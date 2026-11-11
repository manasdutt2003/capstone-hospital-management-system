"""CityCare sample data (Release 2, Module 9).

At least 3 doctors, 2 nurses, 3 wards and 5 patients, built the moment the
menu starts so CityCare staff can test the system immediately. Counters are
reset first, so ids always begin at ``P001``, ``D001`` and ``A001``.
"""

from ..models.emergency import EmergencyCase
from ..models.person import Person
from ..models.prescription import Prescription
from ..services.appointment import Appointment
from ..services.billing import Bill
from ..services.hospital import Hospital

__all__ = ["build_hospital", "reset_counters"]


def reset_counters():
    """Reset every id counter (tests and the menu rely on this)."""
    Person.reset_id_counters()
    Appointment.reset_counter()
    Bill.reset_counter()
    Prescription.reset_counter()
    EmergencyCase.reset_counter()


def build_hospital():
    """Return a ``Hospital`` loaded with CityCare's sample records."""
    reset_counters()
    hospital = Hospital()

    # Three wards: General, Private and ICU.
    hospital.add_ward("General", 4)
    hospital.add_ward("Private", 2)
    hospital.add_ward("ICU", 4)

    # Doctors: two cardiologists (so a leave can move bookings), one
    # orthopaedist and one senior doctor who may approve discharges.
    hospital.add_doctor(
        "Meera Rao", 45, "Female", "9880011223", "Cardiology", 800.0,
        ["10:00", "11:00", "15:00"],
    )
    hospital.add_doctor(
        "Arjun Nair", 38, "Male", "9880011224", "Orthopaedics", 600.0,
        ["09:30", "11:30", "14:30"],
    )
    hospital.add_doctor(
        "Sunita Reddy", 52, "Female", "9880011225", "General", 500.0,
        ["09:00", "10:00", "16:00"], senior=True,
    )
    hospital.add_doctor(
        "Vikram Sen", 41, "Male", "9880011226", "Cardiology", 750.0,
        ["10:00", "12:00", "16:00"],
    )

    # Two nurses (coverage warnings are part of the demo - scenario 9).
    hospital.add_nurse("Kavitha Rao", 29, "Female", "9880022231",
                       "Morning", "General")
    hospital.add_nurse("Deepa Shenoy", 33, "Female", "9880022232",
                       "Night", "ICU")

    # The billing desk: only receptionists may move a patient to BILLED.
    hospital.add_receptionist("Ramesh Iyer", 30, "Male", "9880033341")

    # Five patients - one senior, one with a Penicillin allergy and
    # Government insurance (the acceptance test needs that pair), two IPD.
    hospital.register_patient(
        "Ravi Kumar", 34, "Male", "9876543210", "O+", "OPD"
    )
    hospital.register_patient(
        "Sita Devi", 67, "Female", "9876543211", "A+", "OPD"
    )
    hospital.register_patient(
        "Anil Kumar", 45, "Male", "9876543212", "B+", "OPD",
        allergies=["Penicillin"], payer="Government scheme",
    )
    hospital.register_patient(
        "Neha Menon", 29, "Female", "9876543213", "AB+", "IPD"
    )
    hospital.register_patient(
        "Farhan Ali", 58, "Male", "9876543214", "O-", "IPD"
    )

    # Two sample bookings for Dr. Rao so the leave scenario has work to do.
    hospital.book_appointment("P001", "D001", "10:00")
    hospital.book_appointment("P002", "D001", "11:00")

    return hospital


def main():
    """Print a one line summary of the sample data."""
    hospital = build_hospital()
    print(hospital)
    for patient in hospital:
        print(patient.get_details())


if __name__ == "__main__":
    main()