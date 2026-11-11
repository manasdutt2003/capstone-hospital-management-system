"""The :class:`Patient` entity: one class, with a composed care status.

Release 1 split patients into ``OutPatient`` and ``InPatient`` subclasses.
Release 2 scenario 1 proved that design wrong: a patient who is admitted
mid-visit cannot change class. The care type is now a
:class:`~hms.models.patient_status.PatientStatus` object held by the patient,
so the same object - same id, history, prescriptions and bills - simply swaps
``OPDStatus`` for ``IPDStatus`` while staying a ``Patient``.
"""

from datetime import date

from ..exceptions import InvalidOperationError
from ..services.billing import (
    Billable,
    MEDICINE_CHARGE_PER_DAY,
    SENIOR_AGE,
    SENIOR_DISCOUNT_RATE,
)
from .patient_status import IPDStatus, OPDStatus
from .person import Person
from .stay_record import StayRecord

#: Blood groups recorded by CityCare.
BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


class Patient(Person, Billable):
    """A person treated by the hospital.

    The class holds everything that is true for every patient: blood group,
    medical history, allergies, prescriptions, appointments, bills and - when
    admitted - the ward, bed and the list of stay records. What differs
    between OPD and IPD lives in the composed ``status`` object, not in a
    subclass.
    """

    _id_prefix = "P"

    def __init__(self, name, age, gender, phone, blood_group,
                 medical_history=None, status=None, allergies=None):
        super().__init__(name, age, gender, phone)
        if blood_group not in BLOOD_GROUPS:
            raise ValueError(
                f"Blood group must be one of {', '.join(BLOOD_GROUPS)}."
            )
        self.blood_group = blood_group
        self.medical_history = list(medical_history or [])
        #: Composed care status: OPDStatus or IPDStatus (scenario 1).
        self.status = status or OPDStatus()
        #: Allergy categories checked before every prescription (scenario 8).
        self.allergies = list(allergies or [])
        #: Prescriptions written for this patient.
        self.prescriptions = []
        #: Appointments booked for this patient.
        self.appointments = []
        #: Bills generated for this patient.
        self.bills = []
        #: Doctor currently responsible for the patient.
        self.attending_doctor = None
        #: Ward stay details (None until the first admission).
        self.ward = None
        self.bed_number = None
        self.admission_date = None
        self.discharge_date = None
        #: One record per ward stay (scenario 2).
        self.stay_records = []
        #: Current discharge state machine state; set when admitted.
        self.discharge_state = None
        #: ICU severity score 1-10, used by the emergency queue (scenario 7).
        self.severity_score = None
        #: Payment policy object (scenario 3); Hospital assigns the default.
        self.payment_policy = None

    # ------------------------------------------------------------ care status
    @property
    def patient_type(self):
        """``"OPD"`` or ``"IPD"`` - answered by the composed status."""
        return self.status.code

    @property
    def is_ipd(self):
        """Return ``True`` while the patient's status is IPD."""
        return self.status.is_ipd()

    def convert_to_ipd(self):
        """Switch the status to IPD, keeping id, history and prescriptions."""
        if not self.status.is_ipd():
            self.status = IPDStatus()
        return self.status

    def convert_to_opd(self):
        """Switch the status back to OPD (used when the stay ends)."""
        if self.status.is_ipd():
            self.status = OPDStatus()
        return self.status

    def add_history(self, note):
        """Append a dated note to the patient's medical history."""
        self.medical_history.append(f"{date.today():%d-%b-%Y}: {note}")

    def add_allergy(self, category):
        """Record an allergy category (for example ``"Penicillin"``)."""
        if category not in self.allergies:
            self.allergies.append(category)

    def notify(self, message):
        """Observer callback: print a notification about an appointment."""

    # ---------------------------------------------------------- billing inputs
    def is_senior_citizen(self):
        """Return ``True`` for patients of :data:`SENIOR_AGE` years or more."""
        return self.age >= SENIOR_AGE

    def completed_visits(self):
        """Return the appointments of this patient that were completed."""
        return [
            appointment
            for appointment in self.appointments
            if appointment.is_completed()
        ]

    def medicine_charges(self):
        """Total medicine charge: Rs.50 per medicine, per day."""
        return sum(
            medicine.days * MEDICINE_CHARGE_PER_DAY
            for prescription in self.prescriptions
            for medicine in prescription.medicines
        )

    @property
    def doctor_visits(self):
        """Number of doctor consultations that will be charged."""
        visits = len(self.completed_visits())
        if visits == 0 and self.attending_doctor is not None:
            visits = 1
        return visits

    def visit_fee(self):
        """Consultation fee of the doctor who treated this patient."""
        visits = self.completed_visits()
        if visits:
            return float(visits[-1].doctor.consultation_fee)
        if self.attending_doctor is not None:
            return float(self.attending_doctor.consultation_fee)
        return 0.0

    def consultation_charges(self):
        """Total doctor charge: fee per visit multiplied by the visits."""
        return self.doctor_visits * self.visit_fee()

    def senior_discount_items(self, amount):
        """Return the discount rows for a senior citizen, or an empty list.

        The 10% discount is granted on the *final* amount of either bill type,
        so it is always added after the service tax.
        """
        if not self.is_senior_citizen():
            return []
        discount = round(amount * SENIOR_DISCOUNT_RATE, 2)
        return [
            (
                f"Senior citizen discount ({SENIOR_DISCOUNT_RATE:.0%})",
                -discount,
                "discount",
            )
        ]

    # ------------------------------------------------------------------ stays
    @property
    def is_admitted(self):
        """Return ``True`` while the patient is staying in a ward."""
        return self.ward is not None and self.discharge_date is None

    @property
    def days_admitted(self):
        """Days admitted: admission date up to the discharge date or today."""
        if self.admission_date is None:
            return 0
        end = self.discharge_date or date.today()
        return max((end - self.admission_date).days, 1)

    def open_stay(self, ward, bed_number, on_date=None):
        """Open a new stay record and take the bed (scenario 2)."""
        record = StayRecord(ward, bed_number, on_date or date.today())
        self.stay_records.append(record)
        self.ward = ward
        self.bed_number = bed_number
        if self.admission_date is None or not self.is_admitted:
            self.admission_date = record.from_date
        self.discharge_date = None
        return record

    def close_stay(self, on_date=None):
        """Close the open stay record, if there is one (scenario 2)."""
        for record in reversed(self.stay_records):
            if record.is_open:
                return record.close(on_date)
        return None

    def ward_charge_lines(self):
        """Return ``(description, amount, category)`` rows, one per stay.

        Every ward is charged only for the days spent in it (scenario 2). A
        patient admitted before Release 2 (no records) falls back to the
        single-ward Release 1 formula.
        """
        if self.stay_records:
            return [
                (
                    f"Ward charges ({record.days} day(s) x "
                    f"{record.ward.ward_type} Rs.{record.ward.charge_per_day:,.2f})",
                    record.charge,
                    "ward",
                )
                for record in self.stay_records
            ]
        if self.ward is None:
            return []
        return [
            (
                f"Ward charges ({self.days_admitted} day(s) x "
                f"{self.ward.ward_type} Rs.{self.ward.charge_per_day:,.2f})",
                self.days_admitted * self.ward.charge_per_day,
                "ward",
            )
        ]

    def ward_charges(self):
        """Total ward charge across every stay record."""
        return round(sum(amount for _d, amount, _c in self.ward_charge_lines()), 2)

    def mark_discharged(self, on_date=None):
        """Record the discharge date; the Hospital frees the bed itself."""
        self.close_stay(on_date)
        self.discharge_date = on_date or date.today()

    # ---------------------------------------------------------------- billing
    def bill_line_items(self):
        """Return the (description, amount, category) rows of this bill."""
        if self.status.is_ipd() and self.ward is None and not self.stay_records:
            raise InvalidOperationError(
                f"{self.name} is not admitted to a ward, so there is no "
                f"inpatient bill to generate."
            )
        return self.status.bill_lines(self)

    def calculate_bill(self):
        """Return the total this patient has to pay (the ``Billable`` rule)."""
        return round(sum(amount for _d, amount, _c in self.bill_line_items()), 2)

    # ---------------------------------------------------------------- contract
    def get_role(self):
        """OutPatient for OPD status, InPatient for IPD status (M4)."""
        return "OutPatient" if self.patient_type == "OPD" else "InPatient"

    def get_details(self):
        """One readable line: identity, care status and where they are."""
        if self.is_admitted:
            location = f"{self.ward.ward_type} ward, bed {self.bed_number}"
        elif self.ward is not None:
            location = f"discharged from the {self.ward.ward_type} ward"
        else:
            location = "not admitted to a ward"
        doctor = (
            self.attending_doctor.display_name
            if self.attending_doctor is not None
            else "no doctor assigned"
        )
        return (
            f"[{self.person_id}] {self.name} | {self.patient_type} | "
            f"{self.age} y | {self.gender} | blood group {self.blood_group} | "
            f"phone {self.phone} | {location} | {doctor}"
        )

    # -------------------------------------------------------- object usability
    @classmethod
    def from_string(cls, text):
        """Quick registration from ``"Ravi,34,M,9876543210,O+"`` (Module 8).

        The parts are name, age, gender, phone and blood group. Anything that
        does not fit the expected shape raises ``ValueError`` with a clear
        message instead of a traceback.
        """
        parts = [part.strip() for part in str(text).split(",")]
        if len(parts) != 5:
            raise ValueError(
                'Patient text must look like "Ravi,34,M,9876543210,O+".'
            )
        name, age, gender, phone, blood_group = parts
        if not name:
            raise ValueError("A patient needs a name.")
        try:
            age_value = int(age)
        except ValueError:
            raise ValueError(f"Age must be a whole number, not {age!r}.") from None
        return cls(name, age_value, gender, phone, blood_group)

    def __repr__(self):
        return (
            f"Patient(person_id={self.person_id!r}, name={self.name!r}, "
            f"status={self.status.code!r})"
        )


        print(f"Notification for {self.name}: {message}")
