"""Hospital staff: doctors (including senior doctors), nurses and receptionists."""

from .person import Person

#: Specialisations offered by CityCare.
SPECIALISATIONS = ("Cardiology", "Orthopaedics", "General", "Paediatrics")

#: Nursing shifts.
SHIFTS = ("Morning", "Evening", "Night")


class Doctor(Person):
    """A doctor: a specialisation, a consultation fee and a list of slots.

    ``available_slots`` holds the times the doctor works, as strings such as
    ``"10:00"``. An appointment may only be booked into one of those slots.
    """

    _id_prefix = "D"

    #: Monthly fixed salary, used by the payroll service.
    base_salary = 80000.0

    #: Only senior doctors may approve discharges.
    can_approve_discharge = False

    #: Doctors never move a patient to the BILLED state; receptionists do.
    can_bill = False

    def __init__(self, name, age, gender, phone, specialisation, consultation_fee,
                 available_slots=None):
        super().__init__(name, age, gender, phone)
        if specialisation not in SPECIALISATIONS:
            raise ValueError(
                f"Specialisation must be one of {', '.join(SPECIALISATIONS)}."
            )
        self.specialisation = specialisation
        self.consultation_fee = float(consultation_fee)
        if self.consultation_fee <= 0:
            raise ValueError("Consultation fee must be greater than zero.")
        self.available_slots = list(available_slots or [])
        #: Dates the doctor is on leave (scenario 4).
        self.leave_dates = set()
        #: Daily break window as (start, end) "HH:MM" strings (scenario 5).
        self.break_window = None

    @property
    def display_name(self):
        """Name as patients know it, for example ``"Dr. Meera Rao"``."""
        return f"Dr. {self.name}"

    def offers_slot(self, slot):
        """Return ``True`` when the doctor works at the given time."""
        return slot in self.available_slots

    # ------------------------------------------------------------ leave rules
    def add_leave(self, on_date):
        """Mark the doctor unavailable for one date (scenario 4)."""
        self.leave_dates.add(on_date)
        return self.leave_dates

    def is_on_leave(self, on_date):
        """Return ``True`` when the doctor is away on ``on_date``."""
        return on_date in self.leave_dates

    # ------------------------------------------------------------ break rules
    @staticmethod
    def slot_minutes(slot):
        """Return ``"HH:MM"`` as minutes after midnight, or ``None``."""
        text = str(slot).strip()
        if ":" not in text:
            return None
        hours, _separator, minutes = text.partition(":")
        if not (hours.isdigit() and minutes.isdigit()):
            return None
        return int(hours) * 60 + int(minutes)

    def set_break(self, start, end):
        """Set the daily break when nothing can be booked (scenario 5)."""
        start_minutes = self.slot_minutes(start)
        end_minutes = self.slot_minutes(end)
        if start_minutes is None or end_minutes is None:
            raise ValueError("Break times must look like '13:00'.")
        if start_minutes >= end_minutes:
            raise ValueError("The break must start before it ends.")
        self.break_window = (f"{start_minutes // 60:02d}:{start_minutes % 60:02d}",
                             f"{end_minutes // 60:02d}:{end_minutes % 60:02d}")
        return self.break_window

    def is_break_time(self, slot):
        """Return ``True`` when ``slot`` falls inside the doctor's break."""
        if self.break_window is None:
            return False
        minutes = self.slot_minutes(slot)
        if minutes is None:
            return False
        start = self.slot_minutes(self.break_window[0])
        end = self.slot_minutes(self.break_window[1])
        return start <= minutes < end

    def get_role(self):
        return "Doctor"

    def get_details(self):
        slots = ", ".join(self.available_slots) or "no slots published"
        leave = (
            f" | on leave: {', '.join(str(d) for d in sorted(self.leave_dates))}"
            if self.leave_dates
            else ""
        )
        return (
            f"[{self.person_id}] {self.display_name} | {self.get_role()} | "
            f"{self.specialisation} | {self.age} y | {self.gender} | "
            f"phone {self.phone} | fee Rs.{self.consultation_fee:,.2f} | "
            f"{slots}{leave}"
        )

    def __repr__(self):
        return (
            f"Doctor(person_id={self.person_id!r}, name={self.name!r}, "
            f"specialisation={self.specialisation!r})"
        )


class SeniorDoctor(Doctor):
    """A doctor who may also approve inpatient discharges.

    This is the multilevel step of the hierarchy: ``SeniorDoctor`` ->
    ``Doctor`` -> ``Person`` -> ``ABC``. ``get_details()`` extends the doctor
    output by calling ``super().get_details()`` instead of repeating it.
    """

    #: Senior doctors are the only staff allowed to approve a discharge.
    can_approve_discharge = True

    def get_role(self):
        return "Senior doctor"

    def get_details(self):
        return f"{super().get_details()} | may approve discharges"


class Nurse(Person):
    """A nurse: a shift and the ward the nurse is assigned to."""

    _id_prefix = "N"

    #: Monthly fixed salary, used by the payroll service.
    base_salary = 30000.0

    #: Nurses never move a patient to the BILLED state.
    can_bill = False

    def __init__(self, name, age, gender, phone, shift, assigned_ward):
        super().__init__(name, age, gender, phone)
        if shift not in SHIFTS:
            raise ValueError(f"Shift must be one of {', '.join(SHIFTS)}.")
        self.shift = shift
        self.assigned_ward = assigned_ward
        #: Roster of (date, shift) entries this nurse is scheduled for
        #: (scenario 9: no nurse may work two shifts on the same day).
        self.roster = set()

    def assign_shift(self, on_date, shift):
        """Add one roster entry for this nurse (scenario 9).

        Raises:
            ValueError: when the nurse already works a shift on that date.
        """
        if shift not in SHIFTS:
            raise ValueError(f"Shift must be one of {', '.join(SHIFTS)}.")
        entry = (on_date, shift)
        if entry in self.roster or any(
            day == on_date for day, _shift in self.roster
        ):
            raise ValueError(
                f"{self.name} is already assigned to a shift on "
                f"{on_date:%d-%b-%Y}."
            )
        self.roster.add(entry)
        return entry

    def get_role(self):
        return "Nurse"

    def get_details(self):
        return (
            f"[{self.person_id}] {self.name} | {self.get_role()} | "
            f"{self.shift} shift | {self.assigned_ward} ward | {self.age} y | "
            f"{self.gender} | phone {self.phone}"
        )


class Receptionist(Person):
    """A receptionist: front desk staff who register, book and bill patients."""

    _id_prefix = "R"

    #: Monthly fixed salary, used by the payroll service.
    base_salary = 22000.0

    #: Only billing staff (receptionists) may move a patient to BILLED.
    can_bill = True

    def __init__(self, name, age, gender, phone, desk="Front desk"):
        super().__init__(name, age, gender, phone)
        self.desk = desk

    def get_role(self):
        return "Receptionist"

    def get_details(self):
        return (
            f"[{self.person_id}] {self.name} | {self.get_role()} | {self.desk} | "
            f"{self.age} y | {self.gender} | phone {self.phone}"
        )

