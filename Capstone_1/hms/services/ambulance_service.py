"""Release 3 Feature 7: ambulance dispatch.

``AmbulanceService`` picks the first AVAILABLE ambulance of the requested
type, marks it ON_TRIP, computes the trip charge by distance and registers
the patient automatically (emergency admission helper).
"""

#: Base charge per trip.
BASE_CHARGE = 500.0
#: Per-km charge.
PER_KM_CHARGE = 50.0


class AmbulanceService:
    """Fleet dispatcher over ``Ambulance`` objects."""

    def __init__(self, ambulances=None):
        self.ambulances = list(ambulances or [])
        self.trips = []  # (vehicle_number, patient, km, charge)

    def add(self, ambulance):
        self.ambulances.append(ambulance)
        return ambulance

    def available(self, ambulance_type=None):
        """Return AVAILABLE ambulances, optionally filtered by type."""
        from ..models.ambulance import Ambulance
        return [a for a in self.ambulances
                if a.status == Ambulance.AVAILABLE
                and (ambulance_type is None or a.ambulance_type == ambulance_type)]

    def trip_charge(self, km):
        """Charge = base + per-km."""
        return round(BASE_CHARGE + float(km) * PER_KM_CHARGE, 2)

    def dispatch(self, patient, km, ambulance_type=None):
        """Dispatch first available ambulance; raise if fleet is busy."""
        from ..exceptions import InvalidOperationError
        from ..models.ambulance import Ambulance
        free = self.available(ambulance_type)
        if not free:
            raise InvalidOperationError("No ambulance available right now.")
        ambulance = free[0]
        ambulance.status = Ambulance.ON_TRIP
        charge = self.trip_charge(km)
        self.trips.append((ambulance.vehicle_number, patient, float(km), charge))
        return ambulance, charge

    def complete_trip(self, ambulance):
        """Mark the ambulance AVAILABLE again."""
        from ..models.ambulance import Ambulance
        ambulance.status = Ambulance.AVAILABLE
        return ambulance

    def to_bill_item(self, km):
        return (f"Ambulance ({km} km)", self.trip_charge(km))

    def __len__(self):
        return len(self.ambulances)
