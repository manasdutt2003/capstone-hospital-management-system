"""Appointments between a patient and a doctor."""

from datetime import date, datetime, time
from enum import Enum

from ..exceptions import InvalidOperationError

#: Advance payment taken when any appointment is booked (scenario 5).
ADVANCE_PAYMENT = 200.0


class AppointmentStatus(Enum):
    """The states an appointment can be in."""

    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    #: The doctor went on leave and no replacement was found yet (scenario 4).
    RESCHEDULE_PENDING = "Reschedule pending"


class Appointment:
    """A booking that links one patient, one doctor and one time slot.

    The status starts as ``SCHEDULED`` and may move to ``COMPLETED``, or to
    ``CANCELLED`` / ``RESCHEDULE_PENDING``. Any other move raises
    :class:`~hms.exceptions.InvalidOperationError`.

    Release 2 additions: an appointment date (so a booking occupies a real
    calendar day), the Rs.200 advance payment with its cancellation refund
    policy, and the observer list that notifies the patient whenever the
    appointment changes (scenario 4).
    """

    _counter = 0

    def __init__(self, patient, doctor, slot, booked_on=None, on_date=None,
                 advance=ADVANCE_PAYMENT):
        Appointment._counter += 1
        self.appointment_id = f"A{Appointment._counter:03d}"
        self.patient = patient
        self.doctor = doctor
        self.slot = str(slot).strip()
        self.status = AppointmentStatus.SCHEDULED
        self.booked_on = booked_on or date.today()
        #: The calendar day the patient actually comes in.
        self.appointment_date = on_date or date.today()
        #: Advance taken at booking; refunded by the cancellation policy.
        self.advance_paid = float(advance)
        #: Observers notified on every status change (scenario 4).
        self._observers = []

    @classmethod
    def reset_counter(cls):
        """Reset the appointment numbering (used by tests and sample data)."""
        cls._counter = 0

    # ------------------------------------------------------------- observers
    def subscribe(self, observer):
        """Register an object with a ``notify(message)`` method (S4)."""
        if observer not in self._observers:
            self._observers.append(observer)
        return observer

    def notify(self, message):
        """Tell every subscribed observer about a change."""
        for observer in self._observers:
            observer.notify(message)

    # ------------------------------------------------------------ predicates
    def is_scheduled(self):
        """Return ``True`` while the appointment is still to come."""
        return self.status is AppointmentStatus.SCHEDULED

    def is_completed(self):
        """Return ``True`` when the patient has been seen."""
        return self.status is AppointmentStatus.COMPLETED

    def is_cancelled(self):
        """Return ``True`` when the appointment was cancelled."""
        return self.status is AppointmentStatus.CANCELLED

    def is_reschedule_pending(self):
        """Return ``True`` when the doctor's leave blocked the booking."""
        return self.status is AppointmentStatus.RESCHEDULE_PENDING

    def holds_slot(self):
        """Return ``True`` while this booking occupies the doctor's slot."""
        return self.status in (
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.RESCHEDULE_PENDING,
        )

    # ------------------------------------------------------- timing and money
    @property
    def scheduled_datetime(self):
        """Date and time the patient is expected (date + slot)."""
        hours, _separator, minutes = self.slot.partition(":")
        try:
            slot_time = time(int(hours), int(minutes))
        except ValueError:
            slot_time = time(0, 0)
        return datetime.combine(self.appointment_date, slot_time)

    def hours_until(self, now=None):
        """Hours between ``now`` and the appointment's date and slot."""
        moment = now or datetime.now()
        delta = self.scheduled_datetime - moment
        return delta.total_seconds() / 3600

    def refund_amount(self, now=None):
        """Refund due on cancellation (scenario 5).

        More than 24 hours before: full advance back. Between 2 and 24
        hours: half. Under 2 hours: nothing.
        """
        hours = self.hours_until(now)
        if hours > 24:
            return self.advance_paid
        if hours >= 2:
            return round(self.advance_paid * 0.5, 2)
        return 0.0

    # ------------------------------------------------------------- behaviour
    def complete(self):
        """Mark the appointment as completed and notify the patient.

        Raises:
            InvalidOperationError: if it was already completed or cancelled.
        """
        if not self.is_scheduled():
            raise InvalidOperationError(
                f"Appointment {self.appointment_id} is "
                f"{self.status.value.lower()}, so it cannot be completed."
            )
        self.status = AppointmentStatus.COMPLETED
        self.notify(
            f"appointment {self.appointment_id} with "
            f"{self.doctor.display_name} at {self.slot} is completed."
        )
        return self.status

    def cancel(self, now=None):
        """Cancel the appointment and notify the patient.

        Raises:
            InvalidOperationError: if it was already completed or cancelled.
        """
        if self.is_completed() or self.is_cancelled():
            raise InvalidOperationError(
                f"Appointment {self.appointment_id} is "
                f"{self.status.value.lower()}, so it cannot be cancelled."
            )
        self.status = AppointmentStatus.CANCELLED
        refund = self.refund_amount(now)
        self.notify(
            f"appointment {self.appointment_id} with "
            f"{self.doctor.display_name} on {self.appointment_date:%d-%b-%Y} "
            f"at {self.slot} is cancelled; refund Rs.{refund:,.2f}."
        )
        return refund

    def reassign(self, doctor, slot):
        """Move the booking to another doctor (doctor leave, scenario 4)."""
        previous = self.doctor.display_name
        self.doctor = doctor
        self.slot = str(slot).strip()
        self.status = AppointmentStatus.SCHEDULED
        self.notify(
            f"appointment {self.appointment_id} moved from {previous} to "
            f"{doctor.display_name} at {self.slot} on "
            f"{self.appointment_date:%d-%b-%Y}."
        )
        return self

    def mark_reschedule_pending(self):
        """Flag the booking when no replacement doctor is free (S4)."""
        self.status = AppointmentStatus.RESCHEDULE_PENDING
        self.notify(
            f"appointment {self.appointment_id} could not be moved while "
            f"{self.doctor.display_name} is on leave; rescheduling pending."
        )
        return self.status

    def __str__(self):
        return (
            f"{self.appointment_id}: {self.patient.name} with "
            f"{self.doctor.display_name} at {self.slot} on "
            f"{self.appointment_date:%d-%b-%Y} ({self.status.value})"
        )

    def __repr__(self):
        return (
            f"Appointment(appointment_id={self.appointment_id!r}, "
            f"patient={self.patient.person_id!r}, "
            f"doctor={self.doctor.person_id!r}, slot={self.slot!r}, "
            f"appointment_date={self.appointment_date!r}, "
            f"status={self.status.name})"
        )
