"""Release 3 Feature 9: referrals, follow-ups and feedback."""

from datetime import date


class Referral:
    """A referral of a patient to a specialist/hospital."""

    _counter = 0

    def __init__(self, patient, referred_to, reason, on_date=None):
        Referral._counter += 1
        self.referral_id = f"RF{Referral._counter:03d}"
        self.patient = patient
        self.referred_to = referred_to
        self.reason = reason
        self.on_date = on_date or date.today()
        self.follow_ups = []
        self.feedback = []

    @classmethod
    def reset_counter(cls):
        cls._counter = 0

    def add_follow_up(self, note, on_date=None):
        entry = f"{(on_date or date.today()):%d-%b-%Y}: {note}"
        self.follow_ups.append(entry)
        return entry

    def add_feedback(self, rating, comment=""):
        if not 1 <= int(rating) <= 5:
            raise ValueError("Rating must be 1-5.")
        entry = {"rating": int(rating), "comment": comment}
        self.feedback.append(entry)
        return entry

    def average_rating(self):
        if not self.feedback:
            return 0.0
        return round(sum(f["rating"] for f in self.feedback) / len(self.feedback), 2)

    def get_details(self):
        pname = getattr(self.patient, "name", self.patient)
        return (f"[{self.referral_id}] {pname} -> {self.referred_to} | "
                f"{self.reason} | {len(self.follow_ups)} follow-up(s)")

    def __repr__(self):
        return (f"Referral(referral_id={self.referral_id!r}, "
                f"to={self.referred_to!r})")
