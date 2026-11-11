"""Payment policies: who pays how much of a bill (Release 2, scenario 3).

CityCare collects money four different ways. Each payer is its own subclass
of the abstract :class:`PaymentPolicy`, so the bill and the hospital never
branch on the payer's type: they call ``calculate_payable(bill)`` and print
the split. Adding a fifth payer later means one new class and no change to
``Bill`` or ``Hospital`` (open/closed principle).
"""

from abc import ABC, abstractmethod

from ..exceptions import ClaimRejectedError


class PaymentPolicy(ABC):
    """Strategy contract: turn a bill into an insurer/patient split."""

    #: Payer name shown on bills and menus.
    name = "?"

    @abstractmethod
    def calculate_payable(self, bill):
        """Return ``(insurer_pays, patient_pays)`` for this bill."""

    def split(self, bill):
        """Same as :meth:`calculate_payable`, with both halves rounded."""
        insurer, patient = self.calculate_payable(bill)
        insurer = round(insurer, 2)
        return insurer, round(bill.total - insurer, 2)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{type(self).__name__}()"


class SelfPay(PaymentPolicy):
    """The patient pays 100% of the bill."""

    name = "Self-pay"

    def calculate_payable(self, bill):
        return 0.0, bill.total


class GovernmentScheme(PaymentPolicy):
    """Covers up to Rs.50,000, but only for a General ward stay.

    Raises:
        ClaimRejectedError: when any part of the stay was outside the
            General ward.
    """

    name = "Government scheme"
    COVERAGE_LIMIT = 50000.0

    def calculate_payable(self, bill):
        for record in bill.patient.stay_records:
            if record.ward.ward_type != "General":
                raise ClaimRejectedError(
                    f"Government scheme claim rejected: it covers General ward "
                    f"stays only, but {bill.patient.name} stayed in the "
                    f"{record.ward.ward_type} ward."
                )
        insurer = min(bill.total, self.COVERAGE_LIMIT)
        return insurer, bill.total - insurer


class PrivateInsurance(PaymentPolicy):
    """Covers 80% of everything except medicines, up to the policy limit."""

    name = "Private insurance"
    COVERED_RATE = 0.8

    def __init__(self, policy_limit=2000000.0):
        self.policy_limit = float(policy_limit)

    def calculate_payable(self, bill):
        medicines = bill.amount_for("medicines")
        covered_base = max(bill.total - medicines, 0.0)
        insurer = min(covered_base * self.COVERED_RATE, self.policy_limit)
        return insurer, bill.total - insurer

    def __repr__(self):
        return f"PrivateInsurance(policy_limit={self.policy_limit!r})"


class CorporateTieUp(PaymentPolicy):
    """Covers 100% of the consultation and 70% of everything else."""

    name = "Corporate tie-up"

    def calculate_payable(self, bill):
        consultation = bill.amount_for("consultation")
        rest = bill.total - consultation
        insurer = consultation + rest * 0.70
        return insurer, bill.total - insurer


#: Name -> policy class, so menus and seeds only ever pass a string.
PAYMENT_POLICIES = {
    "Self-pay": SelfPay,
    "Government scheme": GovernmentScheme,
    "Private insurance": PrivateInsurance,
    "Corporate tie-up": CorporateTieUp,
}

#: Friendly aliases accepted when registering a patient.
POLICY_ALIASES = {
    "self": "Self-pay",
    "selfpay": "Self-pay",
    "government": "Government scheme",
    "govt": "Government scheme",
    "insurance": "Private insurance",
    "private": "Private insurance",
    "corporate": "Corporate tie-up",
}


def policy_for(name):
    """Return a fresh policy object for a payer name.

    Raises:
        ValueError: when the payer name is not one CityCare knows.
    """
    text = str(name).strip()
    key = POLICY_ALIASES.get(text.lower(), text)
    policy_class = PAYMENT_POLICIES.get(key)
    if policy_class is None:
        raise ValueError(
            f"Unknown payer '{name}'. Payers: "
            f"{', '.join(PAYMENT_POLICIES)}."
        )
    return policy_class()