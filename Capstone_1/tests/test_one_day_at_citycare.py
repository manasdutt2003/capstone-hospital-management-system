"""User acceptance test: "One day at CityCare" (Release 2 deliverable).

Walks patients through a full day: registration, appointment, mid-visit
admission (scenario 1), prescription safety (scenario 8), the discharge
state machine (scenario 6), billing and payment (scenario 3), reports
(scenario 11) and undo (scenario 10).
"""

import unittest

from hms.models.discharge import DischargeState
from hms.models.medicine import Medicine

from .helpers import new_hospital


class OneDayAtCityCareTests(unittest.TestCase):
    def test_one_day_at_citycare(self):
        hospital = new_hospital()

        # Morning: an OPD patient registers and is seen by the doctor.
        patient = hospital.register_patient(
            "Ravi Kumar", 34, "Male", "9876543215", "O+", "OPD"
        )
        appointment = hospital.book_appointment(patient.person_id, "D001", "10:00")
        hospital.complete_appointment(appointment.appointment_id)
        self.assertTrue(appointment.is_completed())

        # Mid-visit the patient is admitted: OPD becomes IPD, same id (S1).
        hospital.admit_patient(patient.person_id, "General")
        self.assertTrue(patient.is_admitted)
        self.assertEqual(patient.patient_type, "IPD")

        # The prescription passes the allergy/interaction checks (S8).
        hospital.add_prescription(
            "D001", patient.person_id, [Medicine("Paracetamol", "500 mg", 3)]
        )
        self.assertEqual(len(patient.prescriptions), 1)

        # Discharge state machine: requested, then approved by a senior (S6).
        hospital.request_discharge(patient.person_id)
        hospital.approve_discharge(patient.person_id, "D003")
        self.assertEqual(patient.discharge_state, DischargeState.APPROVED)

        # Billing staff raise the bill and take the payment (S3).
        bill = hospital.generate_bill(patient.person_id, billed_by="R001")
        self.assertGreater(bill.total, 0.0)
        hospital.take_payment(patient.person_id, paid_by="R001")
        self.assertTrue(bill.is_paid)

        # Only a paid bill frees the bed: final discharge (S6).
        hospital.discharge_patient(patient.person_id)
        self.assertFalse(patient.is_admitted)
        self.assertEqual(patient.discharge_state, DischargeState.DISCHARGED)

        # The day closes with revenue rows and an audit trail (S10/S11).
        self.assertTrue(list(hospital.daily_revenue_report()))
        self.assertTrue(hospital.audit_report())

    def test_undone_booking_frees_the_slot(self):
        hospital = new_hospital()
        patient = hospital.register_patient(
            "Sita", 29, "Female", "9876543216", "A+"
        )
        hospital.book_appointment(patient.person_id, "D002", "12:00")
        self.assertTrue(
            hospital.is_slot_taken(hospital.doctors["D002"], "12:00")
        )
        hospital.undo_last_booking()
        self.assertFalse(
            hospital.is_slot_taken(hospital.doctors["D002"], "12:00")
        )


if __name__ == "__main__":
    unittest.main()
