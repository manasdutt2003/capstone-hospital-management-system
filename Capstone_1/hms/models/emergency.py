"""Emergency admissions when the ICU is full (Release 2, scenario 7).

When every ICU bed is taken the system either suggests shifting the most
stable patient or parks the new arrival on a priority waiting list. The list
entry implements ``__lt__`` so severity and arrival time decide who is served
first - the same objects can therefore be sorted, popped or inserted anywhere
without a separate sorting rule.
"""

from datetime import datetime


class EmergencyCase:
    """One patient waiting for an emergency ICU bed.

    Higher ``severity`` (1 = least urgent, 10 = critical) means higher
    priority; patients who arrived earlier win ties.
    """

    _counter = 0

    def __init__(self, patient, severity, arrived_at=None):
        severity = int(severity)
        if not 1 <= severity <= 10:
            raise ValueError("Severity score must be between 1 and 10.")
        EmergencyCase._counter += 1
        self.case_id = f"E{EmergencyCase._counter:03d}"
        self.patient = patient
        self.severity = severity
        self.arrived_at = arrived_at or datetime.now()

    @classmethod
    def reset_counter(cls):
        """Reset the case numbering (used by tests and sample data)."""
        cls._counter = 0

    @property
    def waiting_minutes(self):
        """Minutes this case has been waiting, for display."""
        elapsed = datetime.now() - self.arrived_at
        return int(elapsed.total_seconds() // 60)

    def __lt__(self, other):
        """Priority order: most severe first, earliest arrival on a tie."""
        if self.severity != other.severity:
            return self.severity > other.severity
        return self.arrived_at < other.arrived_at

    def __str__(self):
        return (
            f"{self.case_id}: {self.patient.name} severity {self.severity}/10 "
            f"(arrived {self.arrived_at:%H:%M:%S})"
        )

    def __repr__(self):
        return (
            f"EmergencyCase(case_id={self.case_id!r}, "
            f"patient={self.patient.person_id!r}, "
            f"severity={self.severity!r})"
        )