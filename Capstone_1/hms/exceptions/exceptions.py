"""Custom exceptions raised by the Hospital Management System.

Every failure in the domain layer derives from :class:`HospitalError`, so the
terminal application can catch that single base class and print a friendly
``Error: <message>`` line. Adding a new error type later therefore never
requires a change in the menu code.
"""


class HospitalError(Exception):
    """Base class for every error raised by the HMS domain layer."""


class PatientNotFoundError(HospitalError):
    """Raised when a patient cannot be found, for example while searching or
    while generating a bill for an id that does not exist."""


class DoctorNotAvailableError(HospitalError):
    """Raised when a slot is already taken by another appointment, when the
    doctor does not offer that slot at all, or when the doctor is on leave or
    has a break at that time."""


class WardFullError(HospitalError):
    """Raised when a patient is admitted or transferred into a ward that has no
    free bed left."""


class InvalidOperationError(HospitalError):
    """Raised when an operation is not allowed in the object's current state,
    for example discharging a patient who is not admitted or cancelling a
    completed appointment."""


class ResourceConflictError(HospitalError):
    """Raised when a theatre/room booking overlaps an existing one (F3)."""


class BloodUnavailableError(HospitalError):
    """Raised when the blood bank has no usable compatible unit (F5)."""


class VisitorPolicyError(HospitalError):
    """Raised when a visitor check-in breaks the ward limit (F8)."""


class InvalidTransitionError(HospitalError):
    """Raised when a discharge state machine transition is not allowed, for
    example jumping straight from ``ADMITTED`` to ``DISCHARGED``."""


class ClaimRejectedError(HospitalError):
    """Raised when an insurance or scheme claim breaks its own rule, for
    example a Government scheme claim for a non-General ward stay."""


class AllergyAlertError(HospitalError):
    """Raised when a prescribed medicine matches one of the patient's
    recorded allergies."""


class DrugInteractionError(HospitalError):
    """Raised when two medicines known to be a dangerous pair would be taken
    by the same patient, unless the doctor explicitly overrides the check."""


