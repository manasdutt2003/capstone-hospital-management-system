"""The :class:`Medicine` entity used by prescriptions and by billing."""


class Medicine:
    """A medicine prescribed to a patient.

    Attributes:
        name: medicine name, e.g. ``"Paracetamol"``.
        dosage: dosage text, e.g. ``"500 mg"``.
        days: number of days the medicine has to be taken.
    """

    def __init__(self, name, dosage, days, category=None):
        if not str(name).strip():
            raise ValueError("A medicine needs a name.")
        if not str(dosage).strip():
            raise ValueError("A medicine needs a dosage, for example '500 mg'.")
        if int(days) <= 0:
            raise ValueError("Days must be greater than zero.")
        self.name = str(name).strip()
        self.dosage = str(dosage).strip()
        self.days = int(days)
        #: Medicine category used by the allergy and interaction checks of
        #: Release 2 (for example ``"Penicillin"``); defaults to the name.
        self.category = str(category).strip() or self.name

    def __str__(self):
        return f"{self.name} {self.dosage} for {self.days} day(s)"

    def __repr__(self):
        return (
            f"Medicine(name={self.name!r}, dosage={self.dosage!r}, "
            f"days={self.days!r})"
        )
