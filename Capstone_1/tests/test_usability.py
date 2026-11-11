"""Module 8: object usability - magic, class and static methods."""

import unittest

from hms.models.patient import Patient
from hms.models.person import Person
from hms.services.billing import Bill
from hms.services.hospital import Hospital

from .helpers import new_hospital


class PersonUsabilityTests(unittest.TestCase):
    """``__eq__``, ``__str__`` and ``__repr__`` on Person."""

    def test_people_with_the_same_id_are_equal(self):
        first = Patient("Ravi", 34, "Male", "9876543210", "O+")
        second = Patient("Ravi Kumar", 34, "Male", "9876543210", "O+")
        self.assertNotEqual(first.person_id, second.person_id)
        second._person_id = first.person_id  # same id on purpose
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))

    def test_people_with_different_ids_are_not_equal(self):
        first = Patient("Ravi", 34, "Male", "9876543210", "O+")
        second = Patient("Sita", 67, "Female", "9876543211", "A+")
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, "not a person")

    def test_str_is_readable_and_repr_is_developer_friendly(self):
        Person.reset_id_counters()  # ids restart so the repr is predictable
        patient = Patient("Ravi", 34, "Male", "9876543210", "O+")
        self.assertEqual(str(patient), patient.get_details())
        self.assertIn("Patient(person_id='P001'", repr(patient))
        self.assertIn("status='OPD'", repr(patient))

    def test_doctor_repr_names_the_specialisation(self):
        hospital = new_hospital()
        doctor = hospital.doctors["D001"]
        self.assertIn("Doctor(person_id='D001'", repr(doctor))
        self.assertIn("Cardiology", repr(doctor))
        self.assertEqual(str(doctor), doctor.get_details())


class WardUsabilityTests(unittest.TestCase):
    """``__len__`` and ``__contains__`` on Ward."""

    def test_len_is_the_number_of_occupied_beds(self):
        hospital = new_hospital(with_wards=False, with_staff=False)
        ward = hospital.add_ward("General", 3)
        self.assertEqual(len(ward), 0)
        patient = hospital.register_patient(
            "Ravi", 34, "Male", "9876543210", "O+", "IPD"
        )
        hospital.admit_patient(patient.person_id, "General")
        self.assertEqual(len(ward), 1)

    def test_patient_in_ward_reflects_the_bed_map(self):
        hospital = new_hospital(with_wards=False, with_staff=False)
        ward = hospital.add_ward("General", 3)
        first = hospital.register_patient(
            "Ravi", 34, "Male", "9876543210", "O+", "IPD"
        )
        second = hospital.register_patient(
            "Sita", 67, "Female", "9876543211", "A+", "IPD"
        )
        hospital.admit_patient(first.person_id, "General")
        self.assertIn(first, ward)
        self.assertNotIn(second, ward)


class BillUsabilityTests(unittest.TestCase):
    """``__lt__`` and ``__add__`` on Bill."""

    def test_bills_sort_by_total(self):
        hospital = new_hospital()
        small = hospital.register_patient(
            "Small", 30, "Male", "9876543210", "O+"
        )
        big = hospital.register_patient("Big", 30, "Male", "9876543211", "O+")
        low = Bill(small, [("Consultation", 400.0, "consultation")])
        high = Bill(big, [("Consultation", 900.0, "consultation")])
        self.assertTrue(low < high)
        self.assertFalse(high < low)
        self.assertEqual(sorted([high, low]), [low, high])

    def test_adding_bills_returns_the_combined_amount(self):
        hospital = new_hospital()
        patient = hospital.register_patient(
            "Ravi", 34, "Male", "9876543210", "O+"
        )
        first = Bill(patient, [("Consultation", 400.0, "consultation")])
        second = Bill(patient, [("Medicines", 150.0, "medicines")])
        self.assertEqual(first + second, 550.0)


class ClassAndStaticMethodTests(unittest.TestCase):
    """``Patient.from_string`` and ``Hospital.is_valid_phone``."""

    def test_from_string_registers_a_patient_quickly(self):
        Person.reset_id_counters()  # ids restart so the first patient is P001
        patient = Patient.from_string("Ravi,34,M,9876543210,O+")
        self.assertEqual(patient.name, "Ravi")
        self.assertEqual(patient.age, 34)
        self.assertEqual(patient.phone, "9876543210")
        self.assertEqual(patient.blood_group, "O+")
        self.assertEqual(patient.person_id, "P001")

    def test_from_string_rejects_malformed_text(self):
        with self.assertRaises(ValueError):
            Patient.from_string("Ravi,34,M,9876543210")
        with self.assertRaises(ValueError):
            Patient.from_string("Ravi,thirty-four,M,9876543210,O+")

    def test_is_valid_phone(self):
        self.assertTrue(Hospital.is_valid_phone("9876543210"))
        self.assertFalse(Hospital.is_valid_phone("987654321"))
        self.assertFalse(Hospital.is_valid_phone("987654321a"))
        self.assertFalse(Hospital.is_valid_phone(""))

    def test_person_is_abstract(self):
        with self.assertRaises(TypeError):
            Person("Nobody", 30, "Male", "9876543210")


if __name__ == "__main__":
    unittest.main()