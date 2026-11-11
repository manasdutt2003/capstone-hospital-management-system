"""Release 3 tests part 3: F9 referrals, F10 search and timeline."""

import unittest

from hms.models.patient import Patient
from hms.models.person import Person
from hms.models.referral import Referral
from hms.services.search import patient_timeline, search_patients


def make_patient(name="Ravi", age=34, blood="O+"):
    Person.reset_id_counters()
    return Patient(name, age, "M", "9876543210", blood)


class ReferralTests(unittest.TestCase):
    def test_feedback_average(self):
        Referral.reset_counter()
        p = make_patient()
        ref = Referral(p, "Cardiologist", "Chest pain")
        ref.add_follow_up("ECG done")
        ref.add_feedback(5, "Good")
        self.assertEqual(ref.average_rating(), 5.0)


class SearchTests(unittest.TestCase):
    def test_filters(self):
        p1 = make_patient("Ravi Kumar", 34, "O+")
        p2 = make_patient("Sita", 29, "A+")
        self.assertEqual(search_patients([p1, p2], name="ravi"), [p1])
        self.assertEqual(search_patients([p1, p2], blood_group="A+"), [p2])

    def test_timeline_is_generator(self):
        import types
        p1 = make_patient("Ravi Kumar", 34, "O+")
        gen = patient_timeline(p1)
        self.assertIsInstance(gen, types.GeneratorType)
        events = list(gen)
        self.assertTrue(any(k == "history" for k, _ in events))


if __name__ == "__main__":
    unittest.main()
