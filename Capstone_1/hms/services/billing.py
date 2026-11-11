"""The money rules of CityCare, the ``Billable`` contract and the ``Bill``.

Keeping the rates in one module means no other module hard-codes a number.
Every billable type promises the same thing through :class:`Billable`, and
every bill is a :class:`Bill` built from ``(description, amount)`` line items,
so the arithmetic on a bill is always visible to the billing counter.
"""

from abc import ABC, abstractmethod
from datetime import date

#: Service tax added to inpatient bills.
SERVICE_TAX_RATE = 0.05

#: Discount granted to senior citizens, on the final amount of either bill type.
SENIOR_DISCOUNT_RATE = 0.10

#: Age from which a patient counts as a senior citizen.
SENIOR_AGE = 60

#: Medicine charge: Rs.50 per medicine, per day, on every bill.
MEDICINE_CHARGE_PER_DAY = 50.0


class Billable(ABC):
    """Contract for everything the hospital can raise a bill for.

    ``OutPatient`` and ``InPatient`` both implement this contract, which is how
    the billing counter can total any patient without asking what type of
    patient it is.
    """

    @abstractmethod
    def calculate_bill(self):
        """Return the total amount payable by this patient, in rupees."""


class Bill:
    """A patient bill: an ordered list of ``(description, amount, category)``
    line items.

    The total is always the sum of the line items, and the line items are what
    the billing counter prints, so every rupee on a bill can be traced back to
    a service (consultation, ward days, medicines, tax, discount). The
    ``category`` is what lets Release 2 split a bill for an insurer and build
    the daily revenue report without parsing the descriptions.

    Module 8 usability: bills sort with ``<`` (by total) and add with ``+``
    (combined amount).
    """

    _counter = 0

    def __init__(self, patient, line_items=None, issued_on=None, care_type=None):
        Bill._counter += 1
        self.bill_id = f"B{Bill._counter:03d}"
        self.patient = patient
        self.line_items = []
        for item in line_items or []:
            description, amount = item[0], item[1]
            category = item[2] if len(item) > 2 else "other"
            self.add_item(description, amount, category)
        self.issued_on = issued_on or date.today()
        #: "OPD" or "IPD" when the bill was raised (used by the reports).
        self.care_type = care_type or patient.patient_type
        #: Payer name once a payment policy has split the bill (scenario 3).
        self.payer = None
        self.insurer_share = 0.0
        self.patient_share = self.total
        self.paid_amount = 0.0

    @classmethod
    def reset_counter(cls):
        """Reset the bill numbering (used by tests and by the sample data)."""
        cls._counter = 0

    def add_item(self, description, amount, category="other"):
        """Append one line item to the bill."""
        self.line_items.append((description, float(amount), category))

    @property
    def total(self):
        """Total payable: the sum of every line item."""
        return round(sum(amount for _d, amount, _c in self.line_items), 2)

    def amount_for(self, category):
        """Sum of the line items in one category, for example ``"medicines"``."""
        return round(
            sum(
                amount
                for _description, amount, item_category in self.line_items
                if item_category == category
            ),
            2,
        )

    def apply_policy(self, policy, split):
        """Record the payer and the insurer/patient split of a claim (S3)."""
        self.payer = policy.name
        self.insurer_share = round(split[0], 2)
        self.patient_share = round(split[1], 2)
        return self.insurer_share, self.patient_share

    def pay(self, amount=None):
        """Record a payment against this bill and return the balance left."""
        if amount is None:
            amount = self.balance
        self.paid_amount = round(self.paid_amount + float(amount), 2)
        return self.balance

    @property
    def balance(self):
        """What is still owed on this bill."""
        return round(max(self.total - self.paid_amount, 0.0), 2)

    @property
    def is_paid(self):
        """``True`` once nothing is owed any more."""
        return self.balance <= 0

    def __lt__(self, other):
        """Bills sort by total, cheapest first (Module 8)."""
        if isinstance(other, Bill):
            return self.total < other.total
        return NotImplemented

    def __add__(self, other):
        """``bill1 + bill2`` returns the combined amount (Module 8)."""
        if isinstance(other, Bill):
            return round(self.total + other.total, 2)
        return NotImplemented

    def __str__(self):
        lines = [
            f"Bill {self.bill_id} - {self.patient.name} "
            f"({self.issued_on:%d-%b-%Y})"
        ]
        lines += [
            f"   {description}: Rs.{amount:,.2f}"
            for description, amount, _category in self.line_items
        ]
        lines.append(f"   Total: Rs.{self.total:,.2f}")
        if self.payer and self.payer != "Self-pay":
            lines.append(
                f"   Split ({self.payer}): insurer pays Rs.{self.insurer_share:,.2f}, "
                f"patient pays Rs.{self.patient_share:,.2f}"
            )
        if self.paid_amount:
            lines.append(
                f"   Paid: Rs.{self.paid_amount:,.2f} | Balance: Rs.{self.balance:,.2f}"
            )
        return "\n".join(lines)

    def __repr__(self):
        return (
            f"Bill(bill_id={self.bill_id!r}, patient={self.patient.name!r}, "
            f"total={self.total!r})"
        )

