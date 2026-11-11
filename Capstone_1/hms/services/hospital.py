"""The ``Hospital`` aggregate: it owns every object and runs every operation.

Release 2 grew the hospital considerably: patients carry a composable care
status, admissions open stay records, insurance splits bills through payment
policies, appointments move when a doctor goes on leave, discharges run
through a state machine, emergencies queue by severity, prescriptions are
safety checked, and every reception-desk action is a Command that can be
undone and is written to the audit log.
"""

from datetime import date, datetime

from ..exceptions import (
    DoctorNotAvailableError,
    InvalidOperationError,
    PatientNotFoundError,
)
from ..models.ambulance import Ambulance
from ..models.discharge import DischargeState, transition
from ..models.emergency import EmergencyCase
from ..models.patient import Patient
from ..models.prescription import Prescription
from ..models.staff import SHIFTS, Doctor, Nurse, Receptionist, SeniorDoctor
from ..models.ward import Ward
from .appointment import Appointment
from .billing import Bill
from .commands import (
    AdmitPatientCommand,
    BookAppointmentCommand,
    CancelAppointmentCommand,
    DischargePatientCommand,
    GenerateBillCommand,
    TakePaymentCommand,
    TransferPatientCommand,
)
from .payment import policy_for
from .reports import Reports
from .safety import run_safety_checks


class Hospital:
    """CityCare Hospital: the one place where all the data lives.

    The hospital owns patients, doctors, nurses, receptionists, wards,
    ambulances, appointments, prescriptions, bills, refunds, the emergency
    queue and the audit log, and it exposes the operations the terminal menu
    calls. The menu never touches a list or a dictionary directly - every
    change goes through a method here.
    """

    #: Stored once, on the class, and shared by every object of the system.
    name = "CityCare Hospital"

    #: ICU staffing ratio: one nurse for every two patients (scenario 9).
    ICU_PATIENTS_PER_NURSE = 2

    #: An ICU patient must have stayed this long before being suggested
    #: for a shift out of the ICU (scenario 7).
    MIN_STAY_TO_SHIFT = 2

    def __init__(self):
        self.patients = {}
        self.doctors = {}
        self.nurses = {}
        self.receptionists = {}
        self.wards = {}
        self.ambulances = []
        self.appointments = []
        self.prescriptions = []
        self.bills = []
        #: Cancellation refunds for the daily revenue report (scenario 11).
        self.refunds = []
        #: Who did what and when (scenario 10).
        self.audit_log = []
        #: Emergency cases waiting for an ICU bed, in priority order (s7).
        self.emergency_queue = []
        self._undo_stack = []
        self.reports = Reports(self)

    # ------------------------------------------------------ audit and undo
    def _audit(self, actor, action):
        """Append one audit entry and return it (scenario 10)."""
        entry = {"when": datetime.now(), "actor": actor, "action": action}
        self.audit_log.append(entry)
        return entry

    def audit_report(self):
        """One printable line per audit entry: when, who, what."""
        return [
            f"{entry['when']:%Y-%m-%d %H:%M:%S} | {entry['actor']} | "
            f"{entry['action']}"
            for entry in self.audit_log
        ]

    def execute(self, command, actor=None):
        """Run a command, keep it on the undo stack and log it (s10)."""
        result = command.execute()
        self._undo_stack.append(command)
        self._audit(actor or command.actor, command.describe())
        return result

    def undo_last(self, actor="Receptionist"):
        """Undo the most recent command (scenario 10).

        Raises:
            InvalidOperationError: when there is nothing to undo, or when
                the last command is a billing step - "Undo after billing is
                not allowed."
        """
        if not self._undo_stack:
            raise InvalidOperationError("There is no action to undo.")
        command = self._undo_stack[-1]
        if not command.undoable:
            raise InvalidOperationError("Undo after billing is not allowed.")
        command.undo()
        self._undo_stack.pop()
        self._audit(actor, f"undid: {command.describe()}")
        return command

    def undo_last_booking(self, actor="Receptionist"):
        """Undo the most recent booked appointment, wherever it sits.

        Billing steps never leave the stack, so the receptionist can still
        undo a booking made earlier in the day.
        """
        for index in range(len(self._undo_stack) - 1, -1, -1):
            command = self._undo_stack[index]
            if not isinstance(command, BookAppointmentCommand):
                continue
            appointment = command.result
            if appointment is None or not appointment.is_scheduled():
                continue
            command.undo()
            self._undo_stack.pop(index)
            self._audit(actor, f"undid: {command.describe()}")
            return appointment
        raise InvalidOperationError("There is no booked appointment to undo.")

    # ---------------------------------------------------------------- setup
    def add_ward(self, ward_type, total_beds):
        """Create a ward and return it.

        Raises:
            ValueError: if the ward type is unknown or the bed count is not
                positive.
        """
        ward = Ward(ward_type, total_beds)
        self.wards[ward.ward_type] = ward
        return ward

    def add_doctor(self, name, age, gender, phone, specialisation,
                   consultation_fee, available_slots=None, senior=False):
        """Register a doctor, or a senior doctor when ``senior`` is true."""
        doctor_class = SeniorDoctor if senior else Doctor
        doctor = doctor_class(name, age, gender, phone, specialisation,
                              consultation_fee, available_slots)
        self.doctors[doctor.person_id] = doctor
        return doctor

    def add_nurse(self, name, age, gender, phone, shift, assigned_ward):
        """Register a nurse and return her."""
        nurse = Nurse(name, age, gender, phone, shift, assigned_ward)
        self.nurses[nurse.person_id] = nurse
        return nurse

    def add_receptionist(self, name, age, gender, phone, desk="Front desk"):
        """Register a receptionist and return him or her."""
        receptionist = Receptionist(name, age, gender, phone, desk)
        self.receptionists[receptionist.person_id] = receptionist
        return receptionist

    def add_ambulance(self, vehicle_number, ambulance_type, driver_name):
        """Add an ambulance to the fleet and return it."""
        ambulance = Ambulance(vehicle_number, ambulance_type, driver_name)
        self.ambulances.append(ambulance)
        return ambulance

    # ---------------------------------------------------------- registration
    def register_patient(self, name, age, gender, phone, blood_group,
                         patient_type="OPD", medical_history=None,
                         allergies=None, payer="Self-pay"):
        """Register a patient as OPD or IPD with a payer policy (s1, s3).

        The patient always becomes a plain ``Patient`` whose composed status
        answers OPD or IPD, so the same object can change status later.
        """
        kind = str(patient_type).strip().upper()
        if kind not in ("OPD", "IPD"):
            raise ValueError("Patient type must be OPD or IPD.")
        patient = Patient(name, age, gender, phone, blood_group,
                          medical_history, allergies=allergies)
        if kind == "IPD":
            patient.convert_to_ipd()
        patient.payment_policy = policy_for(payer)
        self.patients[patient.person_id] = patient
        return patient

    def set_payer(self, patient_id, payer):
        """Attach a payment policy to a patient (scenario 3)."""
        patient = self.find_patient(patient_id)
        patient.payment_policy = policy_for(payer)
        return patient.payment_policy

    def add_allergy(self, patient_id, category):
        """Record an allergy category for a patient (scenario 8)."""
        patient = self.find_patient(patient_id)
        patient.add_allergy(category)
        return list(patient.allergies)

    # ---------------------------------------------------------------- lookups
    def find_patient(self, patient_id):
        """Return a patient by id, whatever the letter case.

        Raises:
            PatientNotFoundError: when the id is unknown.
        """
        key = str(patient_id).strip().upper()
        patient = self.patients.get(key)
        if patient is None:
            raise PatientNotFoundError(f"No patient found with id {key}.")
        return patient

    def find_doctor(self, doctor_id):
        """Return a doctor by id, whatever the letter case.

        Raises:
            DoctorNotAvailableError: when the id is unknown.
        """
        key = str(doctor_id).strip().upper()
        doctor = self.doctors.get(key)
        if doctor is None:
            raise DoctorNotAvailableError(f"No doctor found with id {key}.")
        return doctor

    def find_staff(self, staff_id):
        """Return any staff member (doctor, nurse or receptionist) by id."""
        key = str(staff_id).strip().upper()
        for registry in (self.doctors, self.nurses, self.receptionists):
            if key in registry:
                return registry[key]
        raise InvalidOperationError(f"No staff found with id {key}.")

    def _require_billing_staff(self, staff_id):
        """Return the staff member, but only when they may bill (s6)."""
        if staff_id is None:
            raise InvalidOperationError(
                "Billing staff id is required for this step."
            )
        staff = self.find_staff(staff_id)
        if not getattr(staff, "can_bill", False):
            raise InvalidOperationError(
                f"{staff.name} is not billing staff; only billing staff may "
                f"move a patient to BILLED."
            )
        return staff

    def find_ward(self, ward_type):
        """Return a ward by type, whatever the letter case."""
        wanted = str(ward_type).strip().lower()
        for ward in self.wards.values():
            if ward.ward_type.lower() == wanted:
                return ward
        known = ", ".join(self.wards) or "none registered yet"
        raise ValueError(
            f"Unknown ward type '{ward_type}'. Registered wards: {known}."
        )

    def search_patient(self, query):
        """Return every patient matching an id or a part of a name.

        Raises:
            PatientNotFoundError: when nothing matches the query.
        """
        text = str(query).strip()
        if not text:
            raise PatientNotFoundError("Enter a patient id or part of a name.")
        key = text.upper()
        matches = [
            patient
            for patient in self.patients.values()
            if patient.person_id == key or text.lower() in patient.name.lower()
        ]
        if not matches:
            raise PatientNotFoundError(f"No patient found matching '{text}'.")
        return matches

    @staticmethod
    def is_valid_phone(phone):
        """Module 8: a valid CityCare number is exactly 10 digits."""
        text = str(phone).strip()
        return len(text) == 10 and text.isdigit()

    # ------------------------------------------------------------------ views
    def all_patients(self):
        """Return every registered patient, in registration order."""
        return list(self.patients.values())

    def all_doctors(self):
        """Return every registered doctor, in registration order."""
        return list(self.doctors.values())

    def all_nurses(self):
        """Return every registered nurse, in registration order."""
        return list(self.nurses.values())

    def all_staff(self):
        """Return all staff: doctors, then nurses, then receptionists."""
        return (
            self.all_doctors()
            + self.all_nurses()
            + list(self.receptionists.values())
        )

    def ward_occupancy(self):
        """Return one row per ward with its bed counts and daily charge."""
        return [
            {
                "ward": ward.ward_type,
                "total": ward.total_beds,
                "occupied": ward.occupied_count,
                "available": len(ward.available_beds()),
                "charge_per_day": ward.charge_per_day,
            }
            for ward in self.wards.values()
        ]

    # ------------------------------------------------------------ appointments
    def _book_appointment(self, patient_id, doctor_id, slot, on_date=None):
        """Core booking rule: one doctor, one day, one free slot (s4, s5)."""
        patient = self.find_patient(patient_id)
        doctor = self.find_doctor(doctor_id)
        slot = self.normalise_slot(slot)
        on_date = on_date or date.today()
        if doctor.is_on_leave(on_date):
            raise DoctorNotAvailableError(
                f"{doctor.display_name} is on leave on "
                f"{on_date:%d-%b-%Y}."
            )
        if not doctor.offers_slot(slot):
            published = ", ".join(doctor.available_slots) or "no slots published"
            raise DoctorNotAvailableError(
                f"{doctor.display_name} does not work at {slot}. "
                f"Available slots: {published}."
            )
        if doctor.is_break_time(slot):
            start, end = doctor.break_window
            raise DoctorNotAvailableError(
                f"{slot} falls inside {doctor.display_name}'s break "
                f"({start}-{end})."
            )
        if self.is_slot_taken(doctor, slot, on_date):
            raise DoctorNotAvailableError(
                f"{doctor.display_name} is not available at {slot}."
            )
        if any(
            appointment.holds_slot()
            and appointment.slot == slot
            and appointment.appointment_date == on_date
            for appointment in patient.appointments
        ):
            raise InvalidOperationError(
                f"{patient.name} already holds an appointment at {slot} on "
                f"{on_date:%d-%b-%Y}."
            )
        appointment = Appointment(patient, doctor, slot, on_date=on_date)
        appointment.subscribe(patient)
        self.appointments.append(appointment)
        patient.appointments.append(appointment)
        patient.attending_doctor = doctor
        return appointment

    def book_appointment(self, patient_id, doctor_id, slot, on_date=None,
                         actor="Receptionist"):
        """Book a slot through the command layer (undoable, audited)."""
        command = BookAppointmentCommand(
            self, patient_id, doctor_id, slot, on_date, actor
        )
        return self.execute(command, actor)

    def is_slot_taken(self, doctor, slot, on_date=None):
        """Return ``True`` when a scheduled appointment holds this slot."""
        day = on_date or date.today()
        return any(
            appointment.is_scheduled()
            and appointment.doctor is doctor
            and appointment.slot == slot
            and appointment.appointment_date == day
            for appointment in self.appointments
        )

    @staticmethod
    def normalise_slot(slot):
        """Return a slot as ``HH:MM``; accepts ``9:00``, ``09.00`` or ``0900``."""
        text = str(slot).strip().replace(".", ":")
        if ":" in text:
            hours, _separator, minutes = text.partition(":")
        elif len(text) == 4 and text.isdigit():
            hours, minutes = text[:2], text[2:]
        else:
            return text
        if not (hours.isdigit() and minutes.isdigit()):
            return text
        return f"{int(hours):02d}:{int(minutes):02d}"

    def find_appointment(self, appointment_id):
        """Return an appointment by id, whatever the letter case.

        Raises:
            InvalidOperationError: when the id is unknown.
        """
        key = str(appointment_id).strip().upper()
        for appointment in self.appointments:
            if appointment.appointment_id == key:
                return appointment
        raise InvalidOperationError(f"No appointment found with id {key}.")

    def _cancel_appointment_core(self, appointment_id, now=None):
        """Cancel and work out the refund; returns what undo needs (s5)."""
        appointment = self.find_appointment(appointment_id)
        refund = appointment.cancel(now)
        refund_record = None
        if refund > 0:
            refund_record = {
                "amount": refund,
                "on_date": date.today(),
                "reason": f"Advance refund for {appointment.appointment_id}",
            }
            self.refunds.append(refund_record)
        return appointment, refund, refund_record

    def cancel_appointment(self, appointment_id, now=None, actor="Receptionist"):
        """Cancel a booking through the command layer (undoable, audited)."""
        command = CancelAppointmentCommand(self, appointment_id, now, actor)
        return self.execute(command, actor)

    def complete_appointment(self, appointment_id, actor="Doctor"):
        """Mark a booking as completed (the patient was seen)."""
        appointment = self.find_appointment(appointment_id)
        appointment.complete()
        self._audit(
            actor,
            f"completed {appointment.appointment_id} for "
            f"{appointment.patient.name}",
        )
        return appointment

    # ---------------------------------------------------- doctor leave (s4)
    def mark_leave(self, doctor_id, on_date, actor="Receptionist"):
        """Put a doctor on leave and move that day's appointments.

        Every scheduled appointment of the day is offered to a free doctor of
        the same specialisation (same slot first, then any free slot). When
        nobody is free the booking becomes RESCHEDULE_PENDING and the patient
        is notified through the observer pattern.
        """
        doctor = self.find_doctor(doctor_id)
        doctor.add_leave(on_date)
        moved, pending = [], []
        for appointment in list(self.appointments):
            if not appointment.is_scheduled():
                continue
            if appointment.doctor is not doctor:
                continue
            if appointment.appointment_date != on_date:
                continue
            replacement, free_slot = self._find_replacement(
                doctor, appointment.slot, on_date
            )
            if replacement is not None:
                appointment.reassign(replacement, free_slot)
                moved.append(appointment)
            else:
                appointment.mark_reschedule_pending()
                pending.append(appointment)
        self._audit(
            actor,
            f"marked {doctor.display_name} on leave for {on_date:%d-%b-%Y}: "
            f"{len(moved)} appointment(s) moved, {len(pending)} pending",
        )
        return {"doctor": doctor, "on_date": on_date,
                "moved": moved, "pending": pending}

    def _find_replacement(self, doctor, slot, on_date):
        """Return ``(doctor, slot)`` of a free colleague, or ``(None, None)``."""
        colleagues = [
            candidate
            for candidate in self.all_doctors()
            if candidate is not doctor
            and candidate.specialisation == doctor.specialisation
            and not candidate.is_on_leave(on_date)
        ]
        for candidate in colleagues:
            if (
                candidate.offers_slot(slot)
                and not candidate.is_break_time(slot)
                and not self.is_slot_taken(candidate, slot, on_date)
            ):
                return candidate, slot
        for candidate in colleagues:
            for free_slot in candidate.available_slots:
                if candidate.is_break_time(free_slot):
                    continue
                if self.is_slot_taken(candidate, free_slot, on_date):
                    continue
                return candidate, free_slot
        return None, None

    # -------------------------------------------------------------- admissions
    def _admit_core(self, patient_id, ward_type, bed_number=None,
                    on_date=None, severity=None, _skip_queue=False):
        """Give a patient a bed and open the first stay record (s1, s2, s9)."""
        patient = self.find_patient(patient_id)
        if patient.is_admitted:
            raise InvalidOperationError(
                f"{patient.name} is already admitted in the "
                f"{patient.ward.ward_type} ward, bed {patient.bed_number}."
            )
        ward = self.find_ward(ward_type)
        if ward.ward_type == "ICU" and severity is not None:
            severity = int(severity)
            if not 1 <= severity <= 10:
                raise ValueError("Severity score must be between 1 and 10.")
        if ward.ward_type == "ICU" and not _skip_queue:
            # Emergencies already waiting are served before regular
            # admissions (scenario 7).
            self._serve_emergency_queue()
            ward = self.find_ward(ward_type)
        was_ipd = patient.is_ipd
        # Occupy the bed first: if the ward is full nothing has changed yet.
        bed = ward.occupy_bed(patient, bed_number)
        if not was_ipd:
            patient.convert_to_ipd()
            patient.add_history("OPD visit converted to IPD admission")
        patient.open_stay(ward, bed, on_date)
        patient.discharge_state = DischargeState.ADMITTED
        if ward.ward_type == "ICU":
            patient.severity_score = severity if severity is not None else 5
        patient.add_history(
            f"Admitted to the {ward.ward_type} ward, bed {bed}"
        )
        self._warn_nurse_coverage(ward)
        return patient

    def admit_patient(self, patient_id, ward_type, bed_number=None,
                      on_date=None, severity=None, actor="Receptionist"):
        """Admit through the command layer (undoable, audited)."""
        command = AdmitPatientCommand(
            self, patient_id, ward_type, bed_number, on_date, severity, actor
        )
        return self.execute(command, actor)

    def _transfer_core(self, patient_id, to_ward, bed_number=None,
                       on_date=None):
        """Move a patient between wards, charging each stay separately (s2)."""
        patient = self.find_patient(patient_id)
        if not patient.is_admitted:
            raise InvalidOperationError(
                f"{patient.name} is not currently admitted to a ward."
            )
        target = self.find_ward(to_ward)
        if target is patient.ward:
            raise InvalidOperationError(
                f"{patient.name} is already in the {target.ward_type} ward, "
                f"bed {patient.bed_number}."
            )
        if target.ward_type == "ICU" and self.emergency_queue:
            self._serve_emergency_queue()
        previous_ward = patient.ward
        previous_bed = patient.bed_number
        # Occupy the new bed first: WardFullError here leaves the patient in
        # the original bed - a transfer is never half done.
        new_bed = target.occupy_bed(patient, bed_number)
        previous_ward.release_bed(previous_bed)
        patient.close_stay(on_date)
        patient.open_stay(target, new_bed, on_date)
        patient.add_history(
            f"Transferred from the {previous_ward.ward_type} ward to the "
            f"{target.ward_type} ward, bed {new_bed}"
        )
        self._warn_nurse_coverage(target)
        if previous_ward.ward_type == "ICU":
            self._serve_emergency_queue()
        return patient

    def transfer_patient(self, patient_id, to_ward, bed_number=None,
                         on_date=None, actor="Receptionist"):
        """Transfer through the command layer (undoable, audited)."""
        command = TransferPatientCommand(
            self, patient_id, to_ward, bed_number, on_date, actor
        )
        return self.execute(command, actor)

    # -------------------------------------------------- nurse coverage (s9)
    def coverage_warnings(self, ward_type):
        """Ratio problems for one ward, one warning per shift (scenario 9)."""
        ward = self.find_ward(ward_type)
        if ward.occupied_count == 0:
            return []
        if ward.ward_type == "ICU":
            required = -(-ward.occupied_count // self.ICU_PATIENTS_PER_NURSE)
        else:
            required = 1
        warnings = []
        for shift in SHIFTS:
            assigned = [
                nurse
                for nurse in self.nurses.values()
                if nurse.assigned_ward == ward.ward_type
                and nurse.shift == shift
            ]
            if len(assigned) < required:
                warnings.append(
                    f"Warning: {ward.ward_type} ward needs at least "
                    f"{required} nurse(s) on the {shift} shift, only "
                    f"{len(assigned)} assigned."
                )
        return warnings

    def _warn_nurse_coverage(self, ward):
        """Print every coverage warning for the ward just changed (s9)."""
        for warning in self.coverage_warnings(ward.ward_type):
            print(warning)

    def assign_nurse_shift(self, nurse_id, shift, on_date=None,
                           actor="Receptionist"):
        """Roster a nurse for a shift; never twice on the same day (s9)."""
        nurse_key = str(nurse_id).strip().upper()
        nurse = self.nurses.get(nurse_key)
        if nurse is None:
            raise InvalidOperationError(f"No nurse found with id {nurse_key}.")
        day = on_date or date.today()
        try:
            entry = nurse.assign_shift(day, shift)
        except ValueError as error:
            raise InvalidOperationError(str(error)) from error
        self._audit(
            actor,
            f"assigned {nurse.name} to the {shift} shift on {day:%d-%b-%Y}",
        )
        return entry

    # --------------------------------------------------- emergency queue (s7)
    def _serve_emergency_queue(self):
        """Admit waiting emergencies into free ICU beds, priority first."""
        served = []
        icu = self.wards.get("ICU")
        if icu is None:
            return served
        while self.emergency_queue and not icu.is_full():
            case = self.emergency_queue.pop(0)
            if case.patient.is_admitted:
                continue
            self._admit_core(
                case.patient.person_id, "ICU",
                severity=case.severity, _skip_queue=True,
            )
            self._audit(
                "Emergency",
                f"admitted {case.patient.name} from the emergency queue "
                f"(severity {case.severity})",
            )
            served.append(case)
        return served

    def suggest_icu_shift(self):
        """Who could leave the ICU to make room (scenario 7)?

        The most stable patient (lowest severity score) who has already
        stayed :attr:`MIN_STAY_TO_SHIFT` days, but only when the Private
        ward has a free bed to move them into.
        """
        icu = self.wards.get("ICU")
        private = self.wards.get("Private")
        if (
            icu is None
            or private is None
            or not icu.is_full()
            or private.is_full()
        ):
            return None
        candidates = [
            patient
            for patient in self.patients.values()
            if patient.is_admitted
            and patient.ward is icu
            and patient.days_admitted >= self.MIN_STAY_TO_SHIFT
        ]
        if not candidates:
            return None
        most_stable = min(
            candidates,
            key=lambda patient: (
                patient.severity_score
                if patient.severity_score is not None
                else 5
            ),
        )
        return {
            "patient": most_stable,
            "from_ward": "ICU",
            "to_ward": "Private",
            "severity": most_stable.severity_score,
        }

    def request_emergency_admission(self, patient_id, severity,
                                    actor="Doctor"):
        """Admit, suggest a shift, or queue the patient (scenario 7)."""
        patient = self.find_patient(patient_id)
        severity = int(severity)
        if not 1 <= severity <= 10:
            raise ValueError("Severity score must be between 1 and 10.")
        patient.severity_score = severity
        icu = self.wards.get("ICU")
        if icu is None:
            raise ValueError("The hospital has no ICU ward.")
        self._serve_emergency_queue()
        if not icu.is_full():
            self._admit_core(
                patient_id, "ICU", severity=severity, _skip_queue=True
            )
            self._audit(
                actor,
                f"emergency admission for {patient.name} "
                f"(severity {severity}) into the ICU",
            )
            return {"action": "admitted", "patient": patient}
        suggestion = self.suggest_icu_shift()
        if suggestion is not None:
            self._audit(
                actor,
                f"emergency for {patient.name} (severity {severity}): "
                f"suggested shifting {suggestion['patient'].name} to "
                f"{suggestion['to_ward']}",
            )
            return {"action": "shift_suggested", "suggestion": suggestion}
        case = EmergencyCase(patient, severity)
        self.emergency_queue.append(case)
        self.emergency_queue.sort()
        position = self.emergency_queue.index(case) + 1
        self._audit(
            actor,
            f"emergency for {patient.name} (severity {severity}): no ICU "
            f"bed, queued at position {position}",
        )
        return {"action": "queued", "case": case, "position": position}

    # -------------------------------------------------- discharge workflow (s6)
    def _require_admitted(self, patient_id, action):
        """Return an admitted patient, or explain why the step cannot run."""
        patient = self.find_patient(patient_id)
        if not patient.is_admitted:
            if patient.ward is None and not patient.stay_records:
                raise InvalidOperationError(
                    f"{patient.name} is an outpatient, so {action} is not "
                    f"possible."
                )
            raise InvalidOperationError(
                f"{patient.name} is not currently admitted to a ward, so "
                f"{action} is not possible."
            )
        return patient

    def begin_treatment(self, patient_id, actor="Doctor"):
        """Move ADMITTED to UNDER_TREATMENT (state machine entry)."""
        patient = self._require_admitted(patient_id, "treatment")
        patient.discharge_state = transition(
            patient.discharge_state, DischargeState.UNDER_TREATMENT
        )
        self._audit(actor, f"started treatment for {patient.name}")
        return patient.discharge_state

    def request_discharge(self, patient_id, actor="Doctor"):
        """Ask for a discharge: ADMITTED -> UNDER_TREATMENT -> REQUESTED.

        A patient who is still only ADMITTED is by definition under care by
        the time a discharge is requested, so the machine is advanced through
        UNDER_TREATMENT first - never around a state.
        """
        patient = self._require_admitted(patient_id, "a discharge request")
        state = patient.discharge_state
        if state is DischargeState.ADMITTED:
            state = transition(state, DischargeState.UNDER_TREATMENT)
        patient.discharge_state = transition(
            state, DischargeState.DISCHARGE_REQUESTED
        )
        self._audit(actor, f"requested discharge of {patient.name}")
        return patient.discharge_state

    def approve_discharge(self, patient_id, doctor_id, actor=None):
        """A senior doctor moves DISCHARGE_REQUESTED to APPROVED (s6)."""
        patient = self._require_admitted(patient_id, "discharge approval")
        doctor = self.find_doctor(doctor_id)
        if not doctor.can_approve_discharge:
            raise InvalidOperationError(
                f"{doctor.display_name} cannot approve a discharge; only a "
                f"senior doctor can."
            )
        patient.discharge_state = transition(
            patient.discharge_state, DischargeState.APPROVED
        )
        self._audit(
            actor or doctor.display_name,
            f"approved discharge of {patient.name}",
        )
        return patient.discharge_state

    # ------------------------------------------------------ billing (s3, s6)
    def generate_bill(self, patient_id, billed_by=None, actor="Billing"):
        """Raise a bill through the command layer (never undoable)."""
        command = GenerateBillCommand(self, patient_id, billed_by, actor)
        return self.execute(command, actor)

    def _generate_bill_core(self, patient_id, billed_by=None):
        """Build the bill, apply the payer's policy and print the split."""
        patient = self.find_patient(patient_id)
        state = patient.discharge_state
        if state is DischargeState.APPROVED:
            # Only billing staff may move a patient from APPROVED to BILLED.
            self._require_billing_staff(billed_by)
        bill = Bill(patient, patient.bill_line_items())
        policy = patient.payment_policy or policy_for("Self-pay")
        if policy.name != "Self-pay":
            insurer, own = policy.split(bill)
            bill.apply_policy(policy, (insurer, own))
            print(
                f"Bill {bill.bill_id} split ({policy.name}): insurer pays "
                f"Rs.{insurer:,.2f}, patient pays Rs.{own:,.2f}."
            )
        self.bills.append(bill)
        patient.bills.append(bill)
        if state is DischargeState.APPROVED:
            patient.discharge_state = transition(
                state, DischargeState.BILLED
            )
        return bill

    def take_payment(self, patient_id, amount=None, paid_by=None,
                     actor="Billing"):
        """Record a payment through the command layer (never undoable)."""
        command = TakePaymentCommand(
            self, patient_id, amount, paid_by, actor
        )
        return self.execute(command, actor)

    def _take_payment_core(self, patient_id, amount=None, paid_by=None):
        """Pay the oldest unpaid bill of the patient."""
        patient = self.find_patient(patient_id)
        self._require_billing_staff(paid_by)
        bill = next(
            (bill for bill in reversed(patient.bills) if not bill.is_paid),
            None,
        )
        if bill is None:
            raise InvalidOperationError(
                f"{patient.name} has no unpaid bill to take payment against."
            )
        paid = bill.balance if amount is None else float(amount)
        if paid <= 0:
            raise InvalidOperationError("Payment must be more than zero.")
        bill.pay(paid)
        return bill

    # -------------------------------------------------- final discharge (s6)
    def discharge_patient(self, patient_id, on_date=None,
                          actor="Receptionist"):
        """Finish the discharge through the command layer (not undoable)."""
        command = DischargePatientCommand(
            self, patient_id, on_date, actor
        )
        return self.execute(command, actor)

    def _final_discharge_core(self, patient_id, on_date=None):
        """BILLED -> DISCHARGED: free the bed only when the bill is paid."""
        patient = self.find_patient(patient_id)
        if not patient.is_admitted:
            if patient.ward is None and not patient.stay_records:
                raise InvalidOperationError(
                    f"{patient.name} is an outpatient, so there is nothing "
                    f"to discharge."
                )
            raise InvalidOperationError(
                f"{patient.name} is not currently admitted to a ward."
            )
        # Raises InvalidTransitionError for any jump that skips a state.
        new_state = transition(
            patient.discharge_state, DischargeState.DISCHARGED
        )
        bill = patient.bills[-1] if patient.bills else None
        if bill is not None and not bill.is_paid:
            raise InvalidOperationError(
                f"{patient.name} cannot be discharged while bill "
                f"{bill.bill_id} has an unpaid balance of "
                f"Rs.{bill.balance:,.2f}."
            )
        ward = patient.ward
        bed = patient.bed_number
        ward.release_bed(bed)
        patient.mark_discharged(on_date)
        patient.discharge_state = new_state
        patient.convert_to_opd()
        patient.add_history(
            f"Discharged from the {ward.ward_type} ward, bed {bed}"
        )
        if ward.ward_type == "ICU":
            self._serve_emergency_queue()
        return patient

    # ------------------------------------------------------- prescriptions
    def add_prescription(self, doctor_id, patient_id, medicines,
                         override=False, override_reason=None):
        """Write a prescription after the safety checks (scenario 8).

        Raises:
            DoctorNotAvailableError: unknown doctor id.
            PatientNotFoundError: unknown patient id.
            AllergyAlertError: a medicine matches a recorded allergy.
            DrugInteractionError: a dangerous pair without an override.
            ValueError: no medicines were given.
        """
        doctor = self.find_doctor(doctor_id)
        patient = self.find_patient(patient_id)
        previous = [
            medicine
            for prescription in patient.prescriptions
            for medicine in prescription.medicines
        ]
        stored_reason = run_safety_checks(
            patient, medicines, previous, override, override_reason
        )
        prescription = Prescription(
            doctor, patient, medicines, override_reason=stored_reason
        )
        patient.prescriptions.append(prescription)
        self.prescriptions.append(prescription)
        summary = ", ".join(
            f"{medicine.name} {medicine.dosage} for {medicine.days} day(s)"
            for medicine in prescription.medicines
        )
        patient.add_history(f"Prescribed {summary} by {doctor.display_name}")
        return prescription

    # ------------------------------------------------------------- reporting
    def bills_sorted(self):
        """Return every bill, most expensive first."""
        return sorted(self.bills, key=lambda bill: bill.total, reverse=True)

    def daily_revenue_report(self, on_date=None):
        """Rows for the daily revenue: OPD, IPD, Pharmacy, Refunds (s11)."""
        return self.reports.daily_revenue(on_date)

    def doctor_earnings_report(self):
        """Doctor-wise earnings, highest first (scenario 11)."""
        return self.reports.doctor_earnings()

    def ward_occupancy_report(self):
        """Occupancy percentage per ward (scenario 11)."""
        return self.reports.ward_occupancy()

    def patients_admitted_longer_than(self, days):
        """Generator over patients staying longer than ``days`` (s11)."""
        return self.reports.patients_admitted_longer_than(days)

    def __iter__(self):
        """The hospital itself iterates over its patients (scenario 11)."""
        return iter(self.patients.values())

    def __str__(self):
        return (
            f"{self.name} | {len(self.patients)} patients, "
            f"{len(self.doctors)} doctors, {len(self.nurses)} nurses, "
            f"{len(self.wards)} wards, {len(self.appointments)} appointments, "
            f"{len(self.bills)} bills"
        )
