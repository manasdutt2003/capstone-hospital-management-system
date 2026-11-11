"""The :class:`Ward` entity: a physical ward holding a fixed number of beds."""

from ..exceptions import WardFullError

#: CityCare ward charges per day, in Indian Rupees.
WARD_CHARGES = {
    "General": 1000.0,
    "Private": 3500.0,
    "ICU": 8000.0,
}

#: Ward types accepted by the hospital.
WARD_TYPES = tuple(WARD_CHARGES)


class Ward:
    """A hospital ward with a fixed number of beds.

    Beds are numbered from ``1`` to ``total_beds``. Each bed holds either
    ``None`` (free) or the inpatient occupying it, which is how the ward knows
    how many beds are available at any moment.
    """

    def __init__(self, ward_type, total_beds):
        if ward_type not in WARD_CHARGES:
            raise ValueError(f"Ward type must be one of {', '.join(WARD_TYPES)}.")
        if int(total_beds) <= 0:
            raise ValueError("A ward must have at least one bed.")
        self.ward_type = ward_type
        self.total_beds = int(total_beds)
        self.charge_per_day = WARD_CHARGES[ward_type]
        self._beds = {number: None for number in range(1, self.total_beds + 1)}

    # ---------------------------------------------------------------- capacity
    @property
    def occupied_count(self):
        """Number of beds that are currently taken."""
        return self.total_beds - len(self.available_beds())

    def available_beds(self):
        """Return the list of bed numbers that are free right now."""
        return [number for number, occupant in self._beds.items() if occupant is None]

    def is_full(self):
        """Return ``True`` when no bed is free."""
        return not self.available_beds()

    # -------------------------------------------------------------------- beds
    def bed_available(self, bed_number):
        """Return ``True`` when the requested bed number is free."""
        self._check_bed_number(bed_number)
        return self._beds[bed_number] is None

    def occupant_of(self, bed_number):
        """Return the patient occupying the bed, or ``None`` when it is free."""
        self._check_bed_number(bed_number)
        return self._beds[bed_number]

    def occupy_bed(self, patient, bed_number=None):
        """Allocate a bed to ``patient`` and return the bed number that was used.

        Raises:
            WardFullError: when every bed in the ward is occupied.
            ValueError: when the requested bed number does not exist or is
                already occupied.
        """
        if self.is_full():
            raise WardFullError(
                f"{self.ward_type} ward is full "
                f"({self.occupied_count}/{self.total_beds} beds occupied)."
            )
        if bed_number is None:
            bed_number = self.available_beds()[0]
        self._check_bed_number(bed_number)
        if self._beds[bed_number] is not None:
            raise ValueError(
                f"Bed {bed_number} in the {self.ward_type} ward is already occupied."
            )
        self._beds[int(bed_number)] = patient
        return int(bed_number)

    def release_bed(self, bed_number):
        """Free a bed and return the patient that was occupying it."""
        self._check_bed_number(bed_number)
        patient = self._beds[int(bed_number)]
        self._beds[int(bed_number)] = None
        return patient

    def _check_bed_number(self, bed_number):
        if bed_number not in self._beds:
            raise ValueError(
                f"The {self.ward_type} ward has beds 1 to {self.total_beds}."
            )

    # -------------------------------------------------------- object usability
    def __len__(self):
        """``len(ward)`` is the number of occupied beds (Module 8)."""
        return self.occupied_count

    def __contains__(self, patient):
        """``patient in ward`` is ``True`` while that patient holds a bed."""
        return patient in self._beds.values()

    def __str__(self):
        return (
            f"{self.ward_type} ward ({self.occupied_count}/{self.total_beds} beds "
            f"occupied at Rs.{self.charge_per_day:,.2f} per day)"
        )

    def __repr__(self):
        return f"Ward(ward_type={self.ward_type!r}, total_beds={self.total_beds!r})"
