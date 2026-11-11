"""Release 3 Feature 8: inpatient diet and visitors.

Diet plans add a daily charge to the IPD bill. Visitor policy: General 4,
Private 2, ICU 0 visitors at a time; violations raise
``VisitorPolicyError``.
"""

#: Daily diet charges.
DIET_CHARGES = {
    "Standard": 300.0,
    "Diabetic": 450.0,
    "High-protein": 550.0,
}

#: Max simultaneous visitors per ward type.
VISITOR_LIMITS = {
    "General": 4,
    "Private": 2,
    "ICU": 0,
}


class DietPlan:
    """A diet assigned to an inpatient."""

    def __init__(self, name, days=1):
        if name not in DIET_CHARGES:
            raise ValueError(f"Diet must be one of {', '.join(DIET_CHARGES)}.")
        if int(days) <= 0:
            raise ValueError("Days must be greater than zero.")
        self.name = name
        self.days = int(days)

    def price(self):
        return round(DIET_CHARGES[self.name] * self.days, 2)

    def to_bill_item(self):
        return (f"Diet: {self.name} x {self.days} day(s)", self.price())

    def get_details(self):
        return (f"[Diet] {self.name} | {self.days} day(s) | "
                f"Rs.{self.price():,.2f}")

    def __repr__(self):
        return f"DietPlan(name={self.name!r}, days={self.days!r})"


class VisitorLog:
    """Visitor check-ins per patient with ward policy enforcement."""

    def __init__(self):
        self.checkins = {}  # patient_id -> [names]

    def check_in(self, patient, visitor_name, ward_type):
        """Register a visitor or raise ``VisitorPolicyError``."""
        from ..exceptions import VisitorPolicyError
        limit = VISITOR_LIMITS.get(ward_type, 0)
        pid = getattr(patient, "person_id", patient)
        current = self.checkins.setdefault(pid, [])
        if len(current) >= limit:
            raise VisitorPolicyError(
                f"{ward_type} ward allows at most {limit} visitor(s).")
        current.append(visitor_name)
        return visitor_name

    def check_out(self, patient, visitor_name):
        pid = getattr(patient, "person_id", patient)
        current = self.checkins.get(pid, [])
        if visitor_name in current:
            current.remove(visitor_name)
        return visitor_name

    def visitors(self, patient):
        pid = getattr(patient, "person_id", patient)
        return list(self.checkins.get(pid, []))
