"""Shared setup for the unittest suite (standard library only)."""

from hms.data.seed_data import reset_counters
from hms.services.hospital import Hospital


def new_hospital(with_wards=True, with_staff=True):
    """Return a fresh ``Hospital`` with deterministic ids.

    Ids are always the same in every test: D001 (Dr. Meera Rao,
    Cardiology), D002 (Dr. Vikram Sen, Cardiology), D003 (Dr. Sunita
    Reddy, General, senior), N001 (Morning, General), N002 (Night, ICU)
    and R001 (the receptionist, the only billing staff).
    """
    reset_counters()
    hospital = Hospital()
    if with_wards:
        hospital.add_ward("General", 3)
        hospital.add_ward("Private", 2)
        hospital.add_ward("ICU", 4)
    if with_staff:
        hospital.add_doctor(
            "Meera Rao", 45, "Female", "9880011223", "Cardiology", 800.0,
            ["10:00", "11:00", "15:00"],
        )
        hospital.add_doctor(
            "Vikram Sen", 41, "Male", "9880011226", "Cardiology", 750.0,
            ["10:00", "12:00", "16:00"],
        )
        hospital.add_doctor(
            "Sunita Reddy", 52, "Female", "9880011225", "General", 500.0,
            ["09:00", "10:00", "16:00"], senior=True,
        )
        hospital.add_nurse("Kavitha Rao", 29, "Female", "9880022231",
                           "Morning", "General")
        hospital.add_nurse("Deepa Shenoy", 33, "Female", "9880022232",
                           "Night", "ICU")
        hospital.add_receptionist("Ramesh Iyer", 30, "Male", "9880033341")
    return hospital