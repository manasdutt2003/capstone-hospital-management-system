"""Command objects for the hospital's undoable actions (Release 2, s10).

Every reception-desk action - book, cancel, admit, transfer, discharge - is
an object with ``execute()`` and ``undo()``. The hospital keeps the stack, so
"undo the last action" is one method call instead of a pile of ``if``
branches, and the audit log records ``describe()`` of every command that ran.

Billing commands (bill, payment, final discharge) set ``undoable = False``:
once money has moved, undo is refused with ``Undo after billing is not
allowed.``
"""

from abc import ABC, abstractmethod

from ..exceptions import InvalidOperationError
from .appointment import AppointmentStatus


def snapshot_patient(patient):
    """Capture the stay fields a command may have to put back."""
    return {
        "ward": patient.ward,
        "bed_number": patient.bed_number,
        "admission_date": patient.admission_date,
        "discharge_date": patient.discharge_date,
        "stay_records": list(patient.stay_records),
        "status": patient.status,
        "discharge_state": patient.discharge_state,
        "severity_score": patient.severity_score,
    }


def restore_patient(patient, snapshot):
    """Put back everything :func:`snapshot_patient` captured."""
    patient.ward = snapshot["ward"]
    patient.bed_number = snapshot["bed_number"]
    patient.admission_date = snapshot["admission_date"]
    patient.discharge_date = snapshot["discharge_date"]
    patient.stay_records = list(snapshot["stay_records"])
    patient.status = snapshot["status"]
    patient.discharge_state = snapshot["discharge_state"]
    patient.severity_score = snapshot["severity_score"]


def undo_bed_change(patient, snapshot):
    """Free the bed taken now, give back the bed in the snapshot (if any)."""
    if patient.ward is not None and patient.bed_number is not None:
        patient.ward.release_bed(patient.bed_number)
    if snapshot["ward"] is not None and snapshot["bed_number"] is not None:
        if not snapshot["ward"].bed_available(snapshot["bed_number"]):
            raise InvalidOperationError(
                f"Bed {snapshot['bed_number']} in the "
                f"{snapshot['ward'].ward_type} ward is no longer free, so "
                f"the ward stay cannot be undone."
            )
        snapshot["ward"].occupy_bed(patient, snapshot["bed_number"])


class Command(ABC):
    """One action: run it with :meth:`execute`, reverse it with :meth:`undo`."""

    #: Commands with ``undoable = False`` refuse to be undone.
    undoable = True

    def __init__(self, hospital, actor="Receptionist"):
        self.hospital = hospital
        self.actor = actor
        self.result = None

    @abstractmethod
    def execute(self):
        """Run the action and store whatever :meth:`undo` needs."""

    @abstractmethod
    def undo(self):
        """Reverse the action exactly as :meth:`execute` ran it."""

    def describe(self):
        """One line for the audit log; called after :meth:`execute`."""
        return str(self.result) if self.result is not None else type(self).__name__

    def __str__(self):
        return self.describe()


class BookAppointmentCommand(Command):
    """Book one of a doctor's slots for a patient."""

    def __init__(self, hospital, patient_id, doctor_id, slot, on_date=None,
                 actor="Receptionist"):
        super().__init__(hospital, actor)
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.slot = slot
        self.on_date = on_date

    def execute(self):
        self.result = self.hospital._book_appointment(
            self.patient_id, self.doctor_id, self.slot, self.on_date
        )
        return self.result

    def undo(self):
        """Forget the booking entirely, including its advance."""
        appointment = self.result
        if appointment is None:
            return
        if appointment in self.hospital.appointments:
            self.hospital.appointments.remove(appointment)
        if appointment in appointment.patient.appointments:
            appointment.patient.appointments.remove(appointment)

    def describe(self):
        appointment = self.result
        if appointment is None:
            return f"booked an appointment for {self.patient_id}"
        return (
            f"booked {appointment.appointment_id} for "
            f"{appointment.patient.name} with "
            f"{appointment.doctor.display_name} at {appointment.slot} on "
            f"{appointment.appointment_date:%d-%b-%Y}"
        )


class CancelAppointmentCommand(Command):
    """Cancel a booking and refund the advance by the cancellation policy."""

    def __init__(self, hospital, appointment_id, now=None, actor="Receptionist"):
        super().__init__(hospital, actor)
        self.appointment_id = appointment_id
        self.now = now
        self.refund_record = None
        self.refund = 0.0

    def execute(self):
        self.result, self.refund, self.refund_record = (
            self.hospital._cancel_appointment_core(self.appointment_id, self.now)
        )
        return self.result

    def undo(self):
        """Put the appointment back on the schedule and drop the refund."""
        appointment = self.result
        if appointment is None:
            return
        appointment.status = AppointmentStatus.SCHEDULED
        if self.refund_record in self.hospital.refunds:
            self.hospital.refunds.remove(self.refund_record)
        self.refund_record = None

    def describe(self):
        appointment = self.result
        if appointment is None:
            return f"cancelled appointment {self.appointment_id}"
        return (
            f"cancelled {appointment.appointment_id} for "
            f"{appointment.patient.name} (refund Rs.{self.refund:,.2f})"
        )


class AdmitPatientCommand(Command):
    """Give a patient a bed, converting an OPD visit into an IPD stay."""

    def __init__(self, hospital, patient_id, ward_type, bed_number=None,
                 on_date=None, severity=None, actor="Receptionist"):
        super().__init__(hospital, actor)
        self.patient_id = patient_id
        self.ward_type = ward_type
        self.bed_number = bed_number
        self.on_date = on_date
        self.severity = severity
        self.snapshot = None

    def execute(self):
        patient = self.hospital.find_patient(self.patient_id)
        self.snapshot = snapshot_patient(patient)
        self.result = self.hospital._admit_core(
            self.patient_id, self.ward_type, self.bed_number, self.on_date,
            self.severity,
        )
        return self.result

    def undo(self):
        """Release the bed and put the patient back the way they were."""
        patient = self.hospital.find_patient(self.patient_id)
        undo_bed_change(patient, self.snapshot)
        restore_patient(patient, self.snapshot)

    def describe(self):
        patient = self.result
        if patient is None:
            return f"admitted {self.patient_id} to the {self.ward_type} ward"
        return (
            f"admitted {patient.name} to the {self.ward_type} ward, "
            f"bed {patient.bed_number}"
        )


class TransferPatientCommand(Command):
    """Move an admitted patient from one ward to another."""

    def __init__(self, hospital, patient_id, to_ward, bed_number=None,
                 on_date=None, actor="Receptionist"):
        super().__init__(hospital, actor)
        self.patient_id = patient_id
        self.to_ward = to_ward
        self.bed_number = bed_number
        self.on_date = on_date
        self.snapshot = None

    def execute(self):
        patient = self.hospital.find_patient(self.patient_id)
        self.snapshot = snapshot_patient(patient)
        self.result = self.hospital._transfer_core(
            self.patient_id, self.to_ward, self.bed_number, self.on_date
        )
        return self.result

    def undo(self):
        """Move the patient back to the original bed and reopen the stay."""
        patient = self.hospital.find_patient(self.patient_id)
        undo_bed_change(patient, self.snapshot)
        restore_patient(patient, self.snapshot)

    def describe(self):
        patient = self.result
        if patient is None:
            return f"transferred {self.patient_id} to the {self.to_ward} ward"
        return (
            f"transferred {patient.name} to the {self.to_ward} ward"
        )


class DischargePatientCommand(Command):
    """Final step of the discharge state machine; never undoable."""

    undoable = False

    def __init__(self, hospital, patient_id, on_date=None, actor="Receptionist"):
        super().__init__(hospital, actor)
        self.patient_id = patient_id
        self.on_date = on_date

    def execute(self):
        self.result = self.hospital._final_discharge_core(
            self.patient_id, self.on_date
        )
        return self.result

    def undo(self):
        raise InvalidOperationError("Undo after billing is not allowed.")

    def describe(self):
        patient = self.result
        if patient is None:
            return f"discharged {self.patient_id}"
        return f"discharged {patient.name} from the ward"


class GenerateBillCommand(Command):
    """Raise a bill; billing itself is never undoable."""

    undoable = False

    def __init__(self, hospital, patient_id, billed_by=None, actor="Billing"):
        super().__init__(hospital, actor)
        self.patient_id = patient_id
        self.billed_by = billed_by

    def execute(self):
        self.result = self.hospital._generate_bill_core(
            self.patient_id, self.billed_by
        )
        return self.result

    def undo(self):
        raise InvalidOperationError("Undo after billing is not allowed.")

    def describe(self):
        bill = self.result
        if bill is None:
            return f"generated a bill for {self.patient_id}"
        return (
            f"generated bill {bill.bill_id} for {bill.patient.name} "
            f"(total Rs.{bill.total:,.2f}, payer {bill.payer or 'Self-pay'})"
        )


class TakePaymentCommand(Command):
    """Record a payment against a bill; payments are never undoable."""

    undoable = False

    def __init__(self, hospital, patient_id, amount=None, paid_by=None,
                 actor="Billing"):
        super().__init__(hospital, actor)
        self.patient_id = patient_id
        self.amount = amount
        self.paid_by = paid_by

    def execute(self):
        self.result = self.hospital._take_payment_core(
            self.patient_id, self.amount, self.paid_by
        )
        return self.result

    def undo(self):
        raise InvalidOperationError("Undo after billing is not allowed.")

    def describe(self):
        bill = self.result
        if bill is None:
            return f"took a payment for {self.patient_id}"
        return (
            f"took payment for bill {bill.bill_id}; balance "
            f"Rs.{bill.balance:,.2f}"
        )
