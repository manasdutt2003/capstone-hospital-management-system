"""Release 3 Feature 3: operation theatre scheduling.

``Surgery`` is the booking; ``OperationTheatre`` owns the schedule and
rejects overlaps with ``ResourceConflictError`` unless the new booking is
an emergency with ``emergency_override=True``.
"""

from datetime import datetime


class Surgery:
    """One surgery booking."""

    _counter = 0
    BASE_CHARGE = 20000.0

    def __init__(self, patient, theatre, surgeon, start, end,
                 emergency=False, charge=None):
        if end <= start:
            raise ValueError("Surgery end must be after start.")
        Surgery._counter += 1
        self.surgery_id = f"S{Surgery._counter:03d}"
        self.patient = patient
        self.theatre = theatre
        self.surgeon = surgeon
        self.start = start
        self.end = end
        self.emergency = bool(emergency)
        self.charge = float(charge) if charge is not None else self.BASE_CHARGE

    @classmethod
    def reset_counter(cls):
        cls._counter = 0

    def price(self):
        return round(self.charge, 2)

    def to_bill_item(self):
        return (f"Surgery {self.surgery_id} ({self.theatre})", self.price())

    def overlaps(self, other):
        return self.theatre == other.theatre and not (
            self.end <= other.start or other.end <= self.start)

    def get_details(self):
        pname = getattr(self.patient, "name", self.patient)
        flag = "EMERGENCY" if self.emergency else "planned"
        return (f"[{self.surgery_id}] {pname} | {self.theatre} | "
                f"{self.start:%d-%b %H:%M}-{self.end:%H:%M} | {flag} | "
                f"Rs.{self.price():,.2f}")

    def __repr__(self):
        return (f"Surgery(surgery_id={self.surgery_id!r}, "
                f"theatre={self.theatre!r})")


class OperationTheatre:
    """A theatre with its own booking list."""

    def __init__(self, name):
        self.name = name
        self.bookings = []

    def book(self, surgery, emergency_override=False):
        """Book ``surgery`` or raise ``ResourceConflictError`` on overlap."""
        from ..exceptions import ResourceConflictError
        if surgery.theatre != self.name:
            raise ValueError(f"Surgery is for {surgery.theatre}, not {self.name}.")
        for existing in self.bookings:
            if surgery.overlaps(existing):
                if surgery.emergency and emergency_override:
                    continue
                raise ResourceConflictError(
                    f"{self.name} is busy {existing.start:%H:%M}-"
                    f"{existing.end:%H:%M} (booking {existing.surgery_id}).")
        self.bookings.append(surgery)
        return surgery

    def __len__(self):
        return len(self.bookings)

    def get_details(self):
        return f"[Theatre] {self.name} | {len(self.bookings)} booking(s)"
