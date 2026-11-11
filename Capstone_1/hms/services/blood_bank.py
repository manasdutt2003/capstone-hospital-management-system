"""Release 3 Feature 5: blood bank.

Units expire 42 days after collection. ``BloodBank.issue()`` serves the
oldest compatible, non-expired unit first and raises
``BloodUnavailableError`` when nothing usable exists.
"""

from datetime import date, timedelta

#: Days a unit stays usable.
EXPIRY_DAYS = 42

#: Who can receive from whom (recipient -> donor groups).
COMPATIBILITY = {
    "O-": ("O-",),
    "O+": ("O-", "O+"),
    "A-": ("O-", "A-"),
    "A+": ("O-", "O+", "A-", "A+"),
    "B-": ("O-", "B-"),
    "B+": ("O-", "O+", "B-", "B+"),
    "AB-": ("O-", "A-", "B-", "AB-"),
    "AB+": ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"),
}


class BloodUnit:
    """One donated unit."""

    _counter = 0

    def __init__(self, blood_group, collected_on=None):
        if blood_group not in COMPATIBILITY:
            raise ValueError(f"Blood group must be one of {', '.join(COMPATIBILITY)}.")
        BloodUnit._counter += 1
        self.unit_id = f"BL{BloodUnit._counter:03d}"
        self.blood_group = blood_group
        self.collected_on = collected_on or date.today()

    @classmethod
    def reset_counter(cls):
        cls._counter = 0

    @property
    def expires_on(self):
        return self.collected_on + timedelta(days=EXPIRY_DAYS)

    def is_expired(self, on_date=None):
        return (on_date or date.today()) > self.expires_on

    def get_details(self):
        return (f"[{self.unit_id}] {self.blood_group} | collected "
                f"{self.collected_on:%d-%b-%Y} | expires {self.expires_on:%d-%b-%Y}")

    def __repr__(self):
        return f"BloodUnit(unit_id={self.unit_id!r}, group={self.blood_group!r})"


class BloodBank:
    """Stock of ``BloodUnit`` objects."""

    def __init__(self):
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)
        return unit

    def usable(self, on_date=None):
        day = on_date or date.today()
        return [u for u in self.units if not u.is_expired(day)]

    def issue(self, recipient_group, on_date=None):
        """Issue oldest compatible unit; raise ``BloodUnavailableError``."""
        from ..exceptions import BloodUnavailableError
        if recipient_group not in COMPATIBILITY:
            raise ValueError("Unknown recipient blood group.")
        allowed = set(COMPATIBILITY[recipient_group])
        day = on_date or date.today()
        candidates = sorted(
            (u for u in self.units
             if u.blood_group in allowed and not u.is_expired(day)),
            key=lambda u: u.collected_on)
        if not candidates:
            raise BloodUnavailableError(
                f"No usable {recipient_group} unit in stock.")
        unit = candidates[0]
        self.units.remove(unit)
        return unit

    def stock_count(self, on_date=None):
        counts = {}
        for unit in self.usable(on_date):
            counts[unit.blood_group] = counts.get(unit.blood_group, 0) + 1
        return counts

    def __len__(self):
        return len(self.units)
