"""Release 3 tests part 1: F1 lab, F2 packages, F3 theatre, F4 payroll."""

import unittest
from datetime import datetime

from hms.exceptions import ResourceConflictError
from hms.models.health_package import HealthPackage
from hms.models.lab import BloodTest, ECG, LabTest
from hms.models.patient import Patient
from hms.models.person import Person
from hms.models.staff import Doctor, Nurse
from hms.models.surgery import OperationTheatre, Surgery
from hms.services.payroll import Payroll, calculate_salary


def make_patient(name="Ravi", age=34, blood="O+"):
    Person.reset_id_counters()
    return Patient(name, age, "M", "9876543210", blood)


class LabTests(unittest.TestCase):
    def test_abnormal_flag(self):
        p = make_patient()
        t = BloodTest(p, result=9.0)
        self.assertEqual(t.flag(), "ABNORMAL")
        self.assertTrue(t.price() > 0)

    def test_normal_flag(self):
        p = make_patient()
        self.assertEqual(BloodTest(p, result=14.0).flag(), "NORMAL")

    def test_bill_item(self):
        p = make_patient()
        desc, amt = BloodTest(p, result=14.0).to_bill_item()
        self.assertIn("Lab", desc)
        self.assertEqual(amt, 400.0)


class PackageTests(unittest.TestCase):
    def test_nested_package_discount(self):
        LabTest.reset_counter()
        p = make_patient()
        inner = HealthPackage("Basic", [BloodTest(p, 14.0), ECG(p, 72.0)])
        outer = HealthPackage("Full", [inner], discount_rate=0.10)
        gross = 400.0 + 600.0
        self.assertEqual(inner.price(), gross)
        self.assertEqual(outer.price(), round(gross * 0.9, 2))
        self.assertEqual(len(outer), 1)


class SurgeryTests(unittest.TestCase):
    def test_overlap_raises(self):
        Surgery.reset_counter()
        p = make_patient()
        ot = OperationTheatre("OT-1")
        s1 = Surgery(p, "OT-1", "Dr. X", datetime(2026, 10, 7, 10, 0),
                     datetime(2026, 10, 7, 12, 0))
        ot.book(s1)
        s2 = Surgery(p, "OT-1", "Dr. Y", datetime(2026, 10, 7, 11, 0),
                     datetime(2026, 10, 7, 13, 0))
        with self.assertRaises(ResourceConflictError):
            ot.book(s2)

    def test_emergency_override(self):
        Surgery.reset_counter()
        p = make_patient()
        ot = OperationTheatre("OT-1")
        s1 = Surgery(p, "OT-1", "Dr. X", datetime(2026, 10, 7, 10, 0),
                     datetime(2026, 10, 7, 12, 0))
        ot.book(s1)
        s2 = Surgery(p, "OT-1", "Dr. Y", datetime(2026, 10, 7, 11, 0),
                     datetime(2026, 10, 7, 13, 0), emergency=True)
        ot.book(s2, emergency_override=True)
        self.assertEqual(len(ot), 2)


class PayrollTests(unittest.TestCase):
    def test_doctor_tax(self):
        Person.reset_id_counters()
        d = Doctor("Meera", 40, "F", "9876543211", "General", 8000.0, ["10:00"])
        net = calculate_salary(d)  # 80000 + 800 - 10pct above 50000
        self.assertEqual(net, round(80800 - 3080.0, 2))

    def test_nurse_night_allowance(self):
        Person.reset_id_counters()
        n = Nurse("Asha", 30, "F", "9876543212", "Night", "General")
        self.assertEqual(calculate_salary(n), 32000.0)
        pr = Payroll()
        pr.pay(n)
        self.assertEqual(pr.total_payout(), 32000.0)


if __name__ == "__main__":
    unittest.main()
