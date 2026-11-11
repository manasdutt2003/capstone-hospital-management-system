"""Services that coordinate the hospital's domain entities.

This package initialiser is intentionally empty. The entity modules import the
pricing rules from ``hms.services.billing``, and an eager import of
``hms.services.hospital`` here would close that circle (hospital -> models ->
services.billing -> services). Import the modules by name instead:

from . import (
    ambulance_service,
    billing,
    blood_bank,
    diet_visitors,
    housekeeping,
    payroll,
    search,
)

__all__ = [
    "billing",
    "payroll",
    "blood_bank",
    "ambulance_service",
    "housekeeping",
    "diet_visitors",
    "search",
]
    from hms.services.hospital import Hospital
"""

