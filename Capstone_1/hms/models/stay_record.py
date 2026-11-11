"""A single stay of a patient in one ward (Release 2, scenario 2).

Transfers used to be invisible to billing: the bill charged one ward rate for
the whole admission. A :class:`StayRecord` closes the old ward's stay and opens
a new one, so every ward is charged only for the days actually spent in it.
"""

from datetime import date


class StayRecord:
    """One ward stay: ward, bed, from_date and an optional to_date.

    ``to_date`` is ``None`` while the patient is still in that bed. Closing a
    record fixes the number of chargeable days: at least one, even when the
    stay and the transfer happen on the same day.
    """

    def __init__(self, ward, bed_number, from_date=None):
        self.ward = ward
        self.bed_number = bed_number
        self.from_date = from_date or date.today()
        #: ``None`` while the stay is open.
        self.to_date = None

    @property
    def is_open(self):
        """Return ``True`` while the patient still occupies this bed."""
        return self.to_date is None

    @property
    def days(self):
        """Chargeable days in this ward, minimum one."""
        end = self.to_date or date.today()
        return max((end - self.from_date).days, 1)

    @property
    def charge(self):
        """Ward charge for this stay: days x the ward's daily rate."""
        return self.days * self.ward.charge_per_day

    def close(self, on_date=None):
        """Close the stay on ``on_date`` (default: today) and return it."""
        self.to_date = on_date or date.today()
        return self.to_date

    def __str__(self):
        end = f"{self.to_date:%d-%b-%Y}" if self.to_date else "ongoing"
        return (
            f"{self.ward.ward_type} bed {self.bed_number}: "
            f"{self.from_date:%d-%b-%Y} to {end} ({self.days} day(s), "
            f"Rs.{self.charge:,.2f})"
        )

    def __repr__(self):
        return (
            f"StayRecord(ward={self.ward.ward_type!r}, "
            f"bed_number={self.bed_number!r}, from_date={self.from_date!r}, "
            f"to_date={self.to_date!r})"
        )