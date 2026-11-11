"""The :class:`Ambulance` entity: a hospital vehicle, not a person."""

#: Ambulance types in the CityCare fleet.
AMBULANCE_TYPES = ("Basic", "Advanced Life Support (ALS)")


class Ambulance:
    """An ambulance of the CityCare fleet.

    An ambulance is deliberately **not** a
    :class:`~hms.models.person.Person`: it is a vehicle, not a person. It does
    however provide ``get_details()``, which is all that the shared
    :func:`~hms.models.person.print_all` helper needs. A mixed list of people
    and vehicles can therefore be printed without a single ``isinstance``
    check.
    """

    #: Status values used by the dispatch feature of release 3.
    AVAILABLE = "AVAILABLE"
    ON_TRIP = "ON_TRIP"

    def __init__(self, vehicle_number, ambulance_type, driver_name,
                 status=AVAILABLE):
        if ambulance_type not in AMBULANCE_TYPES:
            raise ValueError(
                f"Ambulance type must be one of {', '.join(AMBULANCE_TYPES)}."
            )
        self.vehicle_number = vehicle_number
        self.ambulance_type = ambulance_type
        self.driver_name = driver_name
        self.status = status

    def get_details(self):
        """Return a human readable description, like every printable object."""
        return (
            f"[{self.vehicle_number}] Ambulance ({self.ambulance_type}) | "
            f"driver {self.driver_name} | {self.status}"
        )

    def __str__(self):
        return f"Ambulance {self.vehicle_number} ({self.ambulance_type})"

    def __repr__(self):
        return (
            f"Ambulance(vehicle_number={self.vehicle_number!r}, "
            f"ambulance_type={self.ambulance_type!r}, "
            f"driver_name={self.driver_name!r}, status={self.status!r})"
        )
