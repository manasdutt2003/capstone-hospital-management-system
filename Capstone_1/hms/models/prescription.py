"""A prescription written by a doctor for a patient."""

from datetime import date

from ..services.billing import MEDICINE_CHARGE_PER_DAY


class Prescription:
    """A doctor, a patient and the medicines prescribed.

    The patient keeps its own list of prescriptions (``patient.prescriptions``)
    and the hospital keeps the full list, so both views always agree.
    """

    _counter = 0

    def __init__(self, doctor, patient, medicines, issued_on=None,
                 override_reason=None):
        medicines = list(medicines)
        if not medicines:
            raise ValueError("A prescription needs at least one medicine.")
        Prescription._counter += 1
        self.prescription_id = f"RX{Prescription._counter:03d}"
        self.doctor = doctor
        self.patient = patient
        self.medicines = medicines
        self.issued_on = issued_on or date.today()
        #: Why the doctor overrode an interaction warning (scenario 8).
        self.override_reason = override_reason

    @classmethod
    def reset_counter(cls):
        """Reset the prescription numbering (used by tests and sample data)."""
        cls._counter = 0

    @property
    def medicine_charges(self):
        """Rs.50 per medicine, per day, across this prescription."""
        return sum(
            medicine.days * MEDICINE_CHARGE_PER_DAY for medicine in self.medicines
        )

    def __str__(self):
        medicines = "; ".join(str(medicine) for medicine in self.medicines)
        return (
            f"Prescription {self.prescription_id} "
            f"({self.issued_on:%d-%b-%Y}) by {self.doctor.display_name} for "
            f"{self.patient.name}: {medicines}"
        )

    def __repr__(self):
        return (
            f"Prescription(prescription_id={self.prescription_id!r}, "
            f"patient={self.patient.person_id!r}, "
            f"doctor={self.doctor.person_id!r}, medicines={len(self.medicines)})"
        )
