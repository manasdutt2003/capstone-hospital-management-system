"""The CityCare terminal menu (Release 2, Module 9).

Run it from the ``Capstone 0 - Git and Python`` folder::

    python -m hms.main

You can also launch the file directly (it bootstraps its own package
context below)::

    python hms/main.py

The menu is a thin shell: every option prompts for input, calls exactly one
:class:`~hms.services.hospital.Hospital` method and prints the result - it
never touches a list directly. Every ``HospitalError`` and bad input is
caught here and printed as ``Error: <message>``, so the program never
crashes on bad input.
"""

if __package__ in (None, ""):
    # Support running this file directly (``python hms/main.py`` from the
    # project root, or ``python main.py`` from inside ``hms/``). Without a
    # package context the relative imports below fail, so put the project root
    # on ``sys.path`` and point ``__package__`` at ``hms`` to resolve them.
    # ``python -m hms.main`` already has that context and skips this block.
    import os
    import sys

    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    __package__ = "hms"

from datetime import datetime

from .data.seed_data import build_hospital
from .exceptions import HospitalError
from .models.discharge import DischargeState
from .models.medicine import Medicine

MENU = """\
===== CityCare Hospital Management System =====
 1. Register patient (OPD / IPD)
 2. Add doctor / nurse
 3. View all doctors
 4. View all patients
 5. Search patient by ID or name
 6. Book appointment
 7. Cancel appointment
 8. Admit patient to ward
 9. Discharge patient
10. Add prescription
11. Generate bill
12. View ward occupancy
13. View all bills (sorted by amount)
14. Transfer patient to another ward
15. Mark doctor on leave
16. Emergency admission
17. Take payment
18. Complete appointment
19. Assign nurse shift
20. Undo last action
21. View audit log
22. Daily revenue report
23. Doctor earnings report
 0. Exit
Enter choice: """


# ------------------------------------------------------------------- helpers
def ask(prompt):
    """Read one line of input."""
    return input(prompt).strip()


def ask_int(prompt):
    """Read an integer, or fail with a readable message."""
    text = ask(prompt)
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"{prompt.strip(': ').title()} must be a number.") from None


def ask_date(prompt):
    """Read a date as ``YYYY-MM-DD``."""
    text = ask(prompt)
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Dates must look like 2026-10-05.") from None


def _print_people(people):
    people = list(people)
    if not people:
        print("Nothing to show yet.")
        return
    for person in people:
        print(person.get_details())


# ----------------------------------------------------------------- handlers
def register_patient(hospital):
    """Option 1: register an OPD or IPD patient with a payer."""
    name = ask("Name: ")
    age = ask_int("Age: ")
    gender = ask("Gender: ")
    phone = ask("Phone: ")
    blood_group = ask("Blood group (A+/A-/B+/B-/AB+/AB-/O+/O-): ")
    patient_type = ask("Patient type (OPD/IPD) [OPD]: ").upper() or "OPD"
    payer = ask(
        "Payer (Self-pay/Government scheme/Private insurance/"
        "Corporate tie-up) [Self-pay]: "
    ) or "Self-pay"
    allergies = ask("Allergies, comma separated (blank for none): ")
    allergy_list = [item.strip() for item in allergies.split(",") if item.strip()]
    patient = hospital.register_patient(
        name, age, gender, phone, blood_group, patient_type,
        allergies=allergy_list, payer=payer,
    )
    print(
        f"Registered {patient.person_id} {patient.name} "
        f"({patient.patient_type}, payer {patient.payment_policy.name})."
    )


def add_doctor_or_nurse(hospital):
    """Option 2: add a doctor (or senior doctor) or a nurse."""
    kind = ask("Add (1) doctor or (2) nurse? ")
    if kind == "1":
        name = ask("Name: ")
        age = ask_int("Age: ")
        gender = ask("Gender: ")
        phone = ask("Phone: ")
        specialisation = ask(
            "Specialisation (Cardiology/Orthopaedics/General/Paediatrics): "
        )
        fee = ask_int("Consultation fee: ")
        slots = ask("Available slots, comma separated (e.g. 10:00, 11:00): ")
        slot_list = [slot.strip() for slot in slots.split(",") if slot.strip()]
        senior = ask("Senior doctor? (y/n) [n]: ").lower() == "y"
        doctor = hospital.add_doctor(
            name, age, gender, phone, specialisation, fee, slot_list, senior
        )
        print(f"Added {doctor.person_id} {doctor.display_name}.")
    elif kind == "2":
        name = ask("Name: ")
        age = ask_int("Age: ")
        gender = ask("Gender: ")
        phone = ask("Phone: ")
        shift = ask("Shift (Morning/Evening/Night): ")
        ward = ask("Assigned ward (General/Private/ICU): ")
        nurse = hospital.add_nurse(name, age, gender, phone, shift, ward)
        print(f"Added {nurse.person_id} {nurse.name}.")
    else:
        print("Enter 1 for a doctor or 2 for a nurse.")


def view_doctors(hospital):
    """Option 3: every doctor, through print_all's protocol."""
    _print_people(hospital.all_doctors())


def view_patients(hospital):
    """Option 4: every patient."""
    _print_people(hospital.all_patients())


def search_patient(hospital):
    """Option 5: search by id or by part of a name."""
    query = ask("Patient ID or name: ")
    _print_people(hospital.search_patient(query))


def book_appointment(hospital):
    """Option 6: book a slot, showing the doctor's free times first."""
    patient_id = ask("Patient ID: ")
    doctor_id = ask("Doctor ID: ")
    doctor = hospital.find_doctor(doctor_id)
    slots = ", ".join(doctor.available_slots) or "no slots published"
    print(f"Available slots for {doctor.display_name} ({doctor.specialisation}): {slots}")
    slot = ask("Choose slot: ")
    on_date = ask("Date (YYYY-MM-DD) [today]: ")
    appointment = hospital.book_appointment(
        patient_id, doctor_id, slot,
        datetime.strptime(on_date, "%Y-%m-%d").date() if on_date else None,
    )
    print(
        f"Appointment {appointment.appointment_id} booked for "
        f"{appointment.patient.name} with {appointment.doctor.display_name} "
        f"at {appointment.slot} on "
        f"{appointment.appointment_date:%d-%b-%Y} "
        f"(advance Rs.{appointment.advance_paid:,.2f} taken)."
    )


def cancel_appointment(hospital):
    """Option 7: cancel with the release 2 refund policy."""
    appointment_id = ask("Appointment ID: ")
    appointment = hospital.cancel_appointment(appointment_id)
    refund = appointment.refund_amount()
    print(
        f"Cancelled {appointment.appointment_id} for "
        f"{appointment.patient.name}; refund Rs.{refund:,.2f}."
    )


def admit_patient(hospital):
    """Option 8: admit a patient to a ward (OPD visits become IPD)."""
    patient_id = ask("Patient ID: ")
    ward_type = ask("Ward type (General/Private/ICU): ")
    severity = None
    if ward_type.strip().upper() == "ICU":
        severity = ask_int("Severity score (1-10): ")
    patient = hospital.admit_patient(
        patient_id, ward_type, severity=severity
    )
    print(
        f"Admitted {patient.name} to the {patient.ward.ward_type} ward, "
        f"bed {patient.bed_number} ({patient.patient_type})."
    )


DISCHARGE_MENU = """\
--- Discharge workflow ---
 1. Request discharge
 2. Approve discharge (senior doctor)
 3. Generate bill (moves to BILLED, billing staff)
 4. Take payment (billing staff)
 5. Finalise discharge
 0. Back
Choose step: """


def discharge_patient(hospital):
    """Option 9: the six-state discharge workflow as a small sub-menu."""
    while True:
        step = ask(DISCHARGE_MENU)
        if step == "0":
            return
        if step not in ("1", "2", "3", "4", "5"):
            print("Invalid choice.")
            continue
        patient_id = ask("Patient ID: ")
        try:
            if step == "1":
                hospital.request_discharge(patient_id)
                print(hospital.find_patient(patient_id).discharge_state.value)
            elif step == "2":
                doctor_id = ask("Senior doctor ID: ")
                hospital.approve_discharge(patient_id, doctor_id)
                print(hospital.find_patient(patient_id).discharge_state.value)
            elif step == "3":
                staff_id = ask("Billing staff ID: ")
                bill = hospital.generate_bill(patient_id, billed_by=staff_id)
                print(bill)
            elif step == "4":
                staff_id = ask("Billing staff ID: ")
                bill = hospital.take_payment(patient_id, paid_by=staff_id)
                print(
                    f"Balance on {bill.bill_id}: Rs.{bill.balance:,.2f}"
                )
            elif step == "5":
                patient = hospital.discharge_patient(patient_id)
                print(
                    f"Discharged {patient.name} from the "
                    f"{patient.ward.ward_type} ward."
                )
        except HospitalError as error:
            print(f"Error: {error}")
        except ValueError as error:
            print(f"Error: {error}")


def add_prescription(hospital):
    """Option 10: prescribe medicines after the safety checks."""
    doctor_id = ask("Doctor ID: ")
    patient_id = ask("Patient ID: ")
    medicines = []
    while True:
        name = ask("Medicine name (blank to finish): ")
        if not name:
            break
        dosage = ask(f"Dosage for {name} (e.g. 500 mg): ")
        days = ask_int(f"Days for {name}: ")
        category = ask(f"Category for {name} [same as name]: ") or None
        medicines.append(Medicine(name, dosage, days, category))
    if not medicines:
        print("No medicines entered.")
        return
    reason = ask("Override reason for interaction warnings (blank = none): ")
    prescription = hospital.add_prescription(
        doctor_id, patient_id, medicines,
        override=bool(reason), override_reason=reason or None,
    )
    print(prescription)


def generate_bill(hospital):
    """Option 11: raise a bill (billing staff only once APPROVED)."""
    patient_id = ask("Patient ID: ")
    billed_by = None
    patient = hospital.find_patient(patient_id)
    if patient.discharge_state is DischargeState.APPROVED:
        billed_by = ask("Billing staff ID: ")
    bill = hospital.generate_bill(patient_id, billed_by=billed_by)
    print(bill)


def view_ward_occupancy(hospital):
    """Option 12: beds per ward."""
    rows = hospital.ward_occupancy()
    if not rows:
        print("No wards registered yet.")
        return
    for row in rows:
        print(
            f"{row['ward']} ward: {row['occupied']}/{row['total']} occupied, "
            f"{row['available']} free, Rs.{row['charge_per_day']:,.2f} per day"
        )


def view_bills(hospital):
    """Option 13: every bill, highest first (uses ``Bill.__lt__``)."""
    bills = hospital.bills_sorted()
    if not bills:
        print("No bills yet.")
        return
    for bill in bills:
        print(
            f"{bill.bill_id} {bill.patient.name} ({bill.care_type}) "
            f"Rs.{bill.total:,.2f}"
        )


def transfer_patient(hospital):
    """Option 14: move a patient between wards (stay records updated)."""
    patient_id = ask("Patient ID: ")
    to_ward = ask("Transfer to ward (General/Private/ICU): ")
    patient = hospital.transfer_patient(patient_id, to_ward)
    print(
        f"Transferred {patient.name} to the {patient.ward.ward_type} ward, "
        f"bed {patient.bed_number}."
    )


def mark_leave(hospital):
    """Option 15: doctor leave with automatic appointment moves (s4)."""
    doctor_id = ask("Doctor ID: ")
    on_date = ask("Leave date (YYYY-MM-DD): ")
    result = hospital.mark_leave(doctor_id, datetime.strptime(on_date, "%Y-%m-%d").date())
    print(
        f"{result['doctor'].display_name} is on leave on "
        f"{result['on_date']:%d-%b-%Y}: {len(result['moved'])} moved, "
        f"{len(result['pending'])} pending."
    )


def emergency_admission(hospital):
    """Option 16: admit, suggest a shift, or queue by severity (s7)."""
    patient_id = ask("Patient ID: ")
    severity = ask_int("Severity score (1-10): ")
    result = hospital.request_emergency_admission(patient_id, severity)
    if result["action"] == "admitted":
        patient = result["patient"]
        print(
            f"Emergency: {patient.name} admitted to the ICU "
            f"(severity {severity})."
        )
    elif result["action"] == "shift_suggested":
        suggestion = result["suggestion"]
        print(
            f"ICU is full. Suggested: shift "
            f"{suggestion['patient'].name} "
            f"(severity {suggestion['severity']}) from ICU to "
            f"{suggestion['to_ward']}."
        )
    else:
        print(
            f"ICU is full and nobody can be shifted. "
            f"{result['case'].patient.name} is on the emergency waiting "
            f"list at position {result['position']}."
        )


def take_payment(hospital):
    """Option 17: record a payment at the billing counter."""
    patient_id = ask("Patient ID: ")
    amount = ask("Amount (blank = full balance): ")
    staff_id = ask("Billing staff ID: ")
    bill = hospital.take_payment(
        patient_id,
        float(amount) if amount else None,
        paid_by=staff_id,
    )
    print(
        f"Paid against {bill.bill_id}; balance Rs.{bill.balance:,.2f}."
    )


def complete_appointment(hospital):
    """Option 18: mark a booking as completed."""
    appointment_id = ask("Appointment ID: ")
    appointment = hospital.complete_appointment(appointment_id)
    print(f"Completed {appointment}.")


def assign_nurse_shift(hospital):
    """Option 19: roster a nurse; never twice a day (scenario 9)."""
    nurse_id = ask("Nurse ID: ")
    shift = ask("Shift (Morning/Evening/Night): ")
    on_date = ask("Date (YYYY-MM-DD) [today]: ")
    entry = hospital.assign_nurse_shift(
        nurse_id, shift,
        datetime.strptime(on_date, "%Y-%m-%d").date() if on_date else None,
    )
    print(f"Assigned {entry[0]:%d-%b-%Y} {entry[1]} shift.")


def undo_last(hospital):
    """Option 20: undo the last action, or the last booking."""
    choice = ask("Undo (1) last action or (2) last booking? [1]: ") or "1"
    if choice == "2":
        appointment = hospital.undo_last_booking()
        print(
            f"Undid booking {appointment.appointment_id} for "
            f"{appointment.patient.name}."
        )
        return
    command = hospital.undo_last()
    print(f"Undid: {command.describe()}")


def view_audit_log(hospital):
    """Option 21: print the audit trail (scenario 10)."""
    lines = hospital.audit_report()
    if not lines:
        print("Audit log is empty.")
        return
    for line in lines:
        print(line)


def daily_revenue_report(hospital):
    """Option 22: the four revenue buckets for today (scenario 11)."""
    for row in hospital.daily_revenue_report():
        print(f"{row['category']}: Rs.{row['amount']:,.2f}")


def doctor_earnings_report(hospital):
    """Option 23: doctor-wise earnings, highest first (scenario 11)."""
    rows = hospital.doctor_earnings_report()
    if not rows:
        print("No completed consultations yet.")
        return
    for row in rows:
        print(
            f"{row['doctor'].display_name}: {row['consultations']} "
            f"consultation(s), Rs.{row['earnings']:,.2f}"
        )


#: Menu choice -> handler. Every option calls one Hospital method.
HANDLERS = {
    "1": register_patient,
    "2": add_doctor_or_nurse,
    "3": view_doctors,
    "4": view_patients,
    "5": search_patient,
    "6": book_appointment,
    "7": cancel_appointment,
    "8": admit_patient,
    "9": discharge_patient,
    "10": add_prescription,
    "11": generate_bill,
    "12": view_ward_occupancy,
    "13": view_bills,
    "14": transfer_patient,
    "15": mark_leave,
    "16": emergency_admission,
    "17": take_payment,
    "18": complete_appointment,
    "19": assign_nurse_shift,
    "20": undo_last,
    "21": view_audit_log,
    "22": daily_revenue_report,
    "23": doctor_earnings_report,
}


def run_menu(hospital):
    """Run the menu loop until the user picks Exit (Module 9)."""
    print(
        f"Welcome to {hospital.name}. Sample data is loaded: "
        f"{len(hospital.doctors)} doctors, {len(hospital.nurses)} nurses, "
        f"{len(hospital.wards)} wards, {len(hospital.patients)} patients."
    )
    while True:
        try:
            choice = ask(MENU)
        except EOFError:
            print()
            return
        if choice == "0":
            print("Goodbye.")
            return
        handler = HANDLERS.get(choice)
        if handler is None:
            print("Invalid choice.")
            continue
        try:
            handler(hospital)
        except HospitalError as error:
            print(f"Error: {error}")
        except ValueError as error:
            print(f"Error: {error}")


def main():
    """Start the CityCare terminal application."""
    try:
        run_menu(build_hospital())
    except KeyboardInterrupt:
        print("\nGoodbye.")


if __name__ == "__main__":
    main()

