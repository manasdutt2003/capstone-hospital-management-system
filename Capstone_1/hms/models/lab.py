"""Release 3 Feature 1: laboratory and diagnostics.

``LabTest`` is the base; ``BloodTest``/``XRay``/``MRI``/``ECG`` fix the
default price and reference range. A result outside the range is flagged
``ABNORMAL``. ``to_bill_item()`` gives the ``(description, amount)`` row
used on a patient bill.
"""

from datetime import date


class LabTest:
    """One lab test ordered for a patient."""

    _counter = 0

    def __init__(self, patient, result=None, ordered_on=None, price=0.0,
                 name="Lab test", normal_range=None):
        LabTest._counter += 1
        self.test_id = f"LT{LabTest._counter:03d}"
        self.patient = patient
        self.name = name
        self.price_amount = float(price)
        self.result = result
        self.normal_range = normal_range  # (low, high) or None
        self.ordered_on = ordered_on or date.today()

    @classmethod
    def reset_counter(cls):
        cls._counter = 0

    def price(self):
        """Return the charge for this test."""
        return round(self.price_amount, 2)

    def is_abnormal(self):
        """True when a numeric result falls outside ``normal_range``."""
        if self.result is None or self.normal_range is None:
            return False
        try:
            value = float(self.result)
        except (TypeError, ValueError):
            return False
        low, high = self.normal_range
        return value < low or value > high

    def flag(self):
        """Return ``'ABNORMAL'`` or ``'NORMAL'``."""
        return "ABNORMAL" if self.is_abnormal() else "NORMAL"

    def to_bill_item(self):
        """Return the ``(description, amount)`` row for a bill."""
        return (f"Lab: {self.name} ({self.test_id})", self.price())

    def get_details(self):
        pname = getattr(self.patient, "name", self.patient)
        return (f"[{self.test_id}] {self.name} for {pname} | "
                f"Rs.{self.price():,.2f} | {self.flag()}")

    def __str__(self):
        return f"{self.name} ({self.test_id}): {self.flag()}"

    def __repr__(self):
        return f"{type(self).__name__}(test_id={self.test_id!r}, name={self.name!r})"


class BloodTest(LabTest):
    """Haemoglobin test; normal range 12-17 g/dL."""

    DEFAULT_PRICE = 400.0

    def __init__(self, patient, result=None, ordered_on=None):
        super().__init__(patient, result, ordered_on,
                         price=self.DEFAULT_PRICE,
                         name="Blood test",
                         normal_range=(12.0, 17.0))


class XRay(LabTest):
    """X-ray; no numeric range, abnormal only if result says so."""

    DEFAULT_PRICE = 800.0

    def __init__(self, patient, result=None, ordered_on=None):
        super().__init__(patient, result, ordered_on,
                         price=self.DEFAULT_PRICE, name="X-Ray")

    def is_abnormal(self):
        if isinstance(self.result, str) and "abnormal" in self.result.lower():
            return True
        return False


class MRI(LabTest):
    """MRI scan."""

    DEFAULT_PRICE = 5000.0

    def __init__(self, patient, result=None, ordered_on=None):
        super().__init__(patient, result, ordered_on,
                         price=self.DEFAULT_PRICE, name="MRI")

    def is_abnormal(self):
        if isinstance(self.result, str) and "abnormal" in self.result.lower():
            return True
        return False


class ECG(LabTest):
    """ECG; normal heart rate 60-100 bpm."""

    DEFAULT_PRICE = 600.0

    def __init__(self, patient, result=None, ordered_on=None):
        super().__init__(patient, result, ordered_on,
                         price=self.DEFAULT_PRICE,
                         name="ECG", normal_range=(60.0, 100.0))
