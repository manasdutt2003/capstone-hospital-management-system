"""Release 3 Feature 6: bed lifecycle and housekeeping.

``Bed`` tracks READY -> OCCUPIED -> NEEDS_CLEANING -> READY. ``WardKeeper``
adapts this onto the existing ``Ward`` bed map (which stores patient or
None) so Release 1 behaviour is untouched; cleaning state lives here.
"""

#: Lifecycle states.
READY = "READY"
OCCUPIED = "OCCUPIED"
NEEDS_CLEANING = "NEEDS_CLEANING"


class Bed:
    """One bed with a cleaning lifecycle."""

    def __init__(self, ward_type, bed_number):
        self.ward_type = ward_type
        self.bed_number = int(bed_number)
        self.state = READY
        self.occupant = None

    def occupy(self, patient):
        from ..exceptions import InvalidOperationError
        if self.state != READY:
            raise InvalidOperationError(
                f"Bed {self.bed_number} in {self.ward_type} is {self.state}.")
        self.state = OCCUPIED
        self.occupant = patient
        return self

    def vacate(self):
        from ..exceptions import InvalidOperationError
        if self.state != OCCUPIED:
            raise InvalidOperationError("Only an occupied bed can be vacated.")
        patient = self.occupant
        self.occupant = None
        self.state = NEEDS_CLEANING
        return patient

    def clean(self):
        from ..exceptions import InvalidOperationError
        if self.state != NEEDS_CLEANING:
            raise InvalidOperationError("Bed does not need cleaning.")
        self.state = READY
        return self

    def get_details(self):
        return (f"[Bed] {self.ward_type}-{self.bed_number} | {self.state}")

    def __repr__(self):
        return (f"Bed(ward_type={self.ward_type!r}, "
                f"bed_number={self.bed_number!r}, state={self.state!r})")


class WardKeeper:
    """Housekeeping view over an existing ``Ward``."""

    def __init__(self, ward):
        self.ward = ward
        self.cleaning = set()  # bed numbers needing cleaning

    def mark_needs_cleaning(self, bed_number):
        self.ward._check_bed_number(bed_number)
        self.cleaning.add(int(bed_number))

    def mark_cleaned(self, bed_number):
        self.cleaning.discard(int(bed_number))

    def ready_beds(self):
        """Free beds that do not need cleaning."""
        return [b for b in self.ward.available_beds() if b not in self.cleaning]

    def is_ready(self, bed_number):
        return (self.ward.bed_available(bed_number)
                and int(bed_number) not in self.cleaning)

    def __len__(self):
        return len(self.ready_beds())
