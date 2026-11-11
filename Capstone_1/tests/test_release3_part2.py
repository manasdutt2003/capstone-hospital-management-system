"""Release 3 tests part 2: F5 blood, F6 beds, F7 ambulance, F8 diet."""

import unittest
from datetime import date, timedelta

from hms.exceptions import BloodUnavailableError, VisitorPolicyError
from hms.models.ambulance import Ambulance
from hms.models.patient import Patient
from hms.models.person import Person
from hms.models.ward import Ward
from hms.services.ambulance_service import AmbulanceService
from hms.services.blood_bank import BloodBank, BloodUnit
from hms.services.diet_visitors import DietPlan, VisitorLog
from hms.services.housekeeping import READY, Bed, WardKeeper


def make_patient(name="Ravi", age=34, blood="O+"):
    Person.reset_id_counters()
    return Patient(name, age, "M", "9876543210", blood)


class BloodBankTests(unittest.TestCase):
    def test_oldest_first_and_expiry(self):
        BloodUnit.reset_counter()
        bank = BloodBank()
        old = BloodUnit("O+", date.today() - timedelta(days=10))
        new = BloodUnit("O+", date.today())
        expired = BloodUnit("O+", date.today() - timedelta(days=50))
        bank.add_unit(new)
        bank.add_unit(old)
        bank.add_unit(expired)
        self.assertIs(bank.issue("O+"), old)
        self.assertEqual(bank.stock_count()["O+"], 1)

    def test_incompatible_raises(self):
        bank = BloodBank()
        bank.add_unit(BloodUnit("A+", date.today()))
        with self.assertRaises(BloodUnavailableError):
            bank.issue("O-")


class BedTests(unittest.TestCase):
    def test_lifecycle(self):
        bed = Bed("General", 1)
        p = make_patient()
        bed.occupy(p)
        bed.vacate()
        bed.clean()
        self.assertEqual(bed.state, READY)

    def test_keeper_ready(self):
        ward = Ward("General", 2)
        keeper = WardKeeper(ward)
        keeper.mark_needs_cleaning(1)
        self.assertEqual(keeper.ready_beds(), [2])


class AmbulanceTests(unittest.TestCase):
    def test_dispatch_charge(self):
        svc = AmbulanceService([Ambulance("TN01-1", "Basic", "Ravi")])
        p = make_patient()
        amb, charge = svc.dispatch(p, 10)
        self.assertEqual(charge, 1000.0)
        self.assertEqual(amb.status, Ambulance.ON_TRIP)
        svc.complete_trip(amb)
        self.assertEqual(amb.status, Ambulance.AVAILABLE)


class DietVisitorTests(unittest.TestCase):
    def test_diet_price(self):
        self.assertEqual(DietPlan("Diabetic", 2).price(), 900.0)

    def test_icu_blocks_visitors(self):
        log = VisitorLog()
        p = make_patient()
        with self.assertRaises(VisitorPolicyError):
            log.check_in(p, "Guest", "ICU")


if __name__ == "__main__":
    unittest.main()
