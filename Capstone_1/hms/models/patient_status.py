"""Patient care status: OPD and IPD as composed objects (Release 2, scenario 1).

Release 1 modelled the care type with two subclasses, ``OutPatient`` and
``InPatient``. Scenario 1 showed why that breaks down: a patient who walks in
for an OPD consultation and is admitted to ICU the same day cannot change its
class at runtime. CityCare therefore redesigned the patient around a
:class:`PatientStatus` object that can be swapped while the patient - and the
patient's id, history and prescriptions - carries on unchanged.
"""

from abc import ABC, abstractmethod

from ..services.billing import MEDICINE_CHARGE_PER_DAY, SERVICE_TAX_RATE


class PatientStatus(ABC):
    """The care status of a patient: OPD or IPD.

    The status is a small strategy object: it answers "what kind of bill
    lines does this patient produce?" and "which ward rules apply?". Adding a
    future status (for example DayCare) means adding one class here, never
    touching :class:`~hms.models.patient.Patient`.
    """

    #: Status code shown to users, ``"OPD"`` or ``"IPD"``.
    code = "?"

    def is_ipd(self):
        """Return ``True`` for inpatient statuses."""
        return False

    @abstractmethod
    def bill_lines(self, patient):
        """Return the ``(description, amount, category)`` bill rows."""

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"{type(self).__name__}()"


class OPDStatus(PatientStatus):
    """Outpatient care: consultation and medicines, no ward and no tax.

    Bill formula: doctor consultation fee + medicine charges (Rs.50 per
    medicine per day), less the 10% senior citizen discount when the patient
    is 60 or older.
    """

    code = "OPD"

    def bill_lines(self, patient):
        lines = [
            (
                f"Consultation ({patient.doctor_visits} visit(s) x "
                f"Rs.{patient.visit_fee():,.2f})",
                patient.consultation_charges(),
                "consultation",
            ),
            (
                "Medicines "
                f"(Rs.{MEDICINE_CHARGE_PER_DAY:,.0f} per medicine per day)",
                patient.medicine_charges(),
                "medicines",
            ),
        ]
        total = round(sum(amount for _d, amount, _c in lines), 2)
        return lines + patient.senior_discount_items(total)


class IPDStatus(PatientStatus):
    """Inpatient care: ward days, consultation, medicines and service tax.

    Bill formula: ward charges for every stay record + doctor visits +
    medicines + 5% service tax, less the 10% senior citizen discount on the
    final amount. Each stay record charges its own ward's rate for the days
    actually spent there (scenario 2).
    """

    code = "IPD"

    def is_ipd(self):
        return True

    def bill_lines(self, patient):
        lines = list(patient.ward_charge_lines())
        lines.append(
            (
                f"Doctor visits ({patient.doctor_visits} x "
                f"Rs.{patient.visit_fee():,.2f})",
                patient.consultation_charges(),
                "consultation",
            )
        )
        lines.append(
            (
                "Medicines "
                f"(Rs.{MEDICINE_CHARGE_PER_DAY:,.0f} per medicine per day)",
                patient.medicine_charges(),
                "medicines",
            )
        )
        subtotal = round(sum(amount for _d, amount, _c in lines), 2)
        tax = round(subtotal * SERVICE_TAX_RATE, 2)
        lines.append((f"Service tax ({SERVICE_TAX_RATE:.0%})", tax, "tax"))
        return lines + patient.senior_discount_items(round(subtotal + tax, 2))