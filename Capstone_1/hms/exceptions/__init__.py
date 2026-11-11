"""Exception types of the HMS.

The types are re-exported here so that callers can simply write
``from hms.exceptions import WardFullError`` instead of importing from the
``hms.exceptions.exceptions`` module.
"""

from .exceptions import (
    AllergyAlertError,
    BloodUnavailableError,
    ClaimRejectedError,
    DoctorNotAvailableError,
    DrugInteractionError,
    HospitalError,
    InvalidOperationError,
    InvalidTransitionError,
    PatientNotFoundError,
    ResourceConflictError,
    VisitorPolicyError,
    WardFullError,
)

__all__ = [
    "HospitalError",
    "PatientNotFoundError",
    "DoctorNotAvailableError",
    "WardFullError",
    "InvalidOperationError",
    "ResourceConflictError",
    "BloodUnavailableError",
    "VisitorPolicyError",
    "InvalidTransitionError",
    "ClaimRejectedError",
    "AllergyAlertError",
    "DrugInteractionError",
]
