# Changelog

All notable changes to the CityCare Hospital Management System are recorded in
this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project is versioned with the sprint and release tags described in
[docs/project-plan.md](docs/project-plan.md).

## [3.0.0] - 2026-10-06 - Release 3 (Features 1-10)

### Added - Sprint 06 clinical (F1-F5)

- `hms/models/lab.py`: `LabTest` + `BloodTest`, `XRay`, `MRI`, `ECG`
  with `price()`, `ABNORMAL` flag and `to_bill_item()`.
- `hms/models/health_package.py`: nested packages with discount and
  the same `price()` as a single test.
- `hms/models/surgery.py`: `Surgery` + `OperationTheatre` with
  `ResourceConflictError` and emergency override.
- `hms/services/payroll.py`: `calculate_salary()` per staff type,
  `Payroll` ledger, 10% tax above Rs.50,000.
- `hms/services/blood_bank.py`: 42-day expiry, compatibility map,
  oldest-first `issue()`, `BloodUnavailableError`.
- `tests/test_release3_part1.py`, `test_release3_part2.py` (F1-F5 cases).

### Added - Sprint 07 services and close (F6-F10)

- `hms/services/housekeeping.py`: `Bed` lifecycle
  READY/OCCUPIED/NEEDS_CLEANING + `WardKeeper` over `Ward`.
- `hms/services/ambulance_service.py`: dispatch, per-km charges.
- `hms/services/diet_visitors.py`: diet charges, `VisitorPolicyError`.
- `hms/models/referral.py`: referrals, follow-ups, feedback ratings.
- `hms/services/search.py`: `search_patients()` filters and
  `patient_timeline()` generator.
- `tests/test_release3_part3.py` (F9-F10 cases).

## [Unreleased]

## [2.0.0] - 2026-10-06 - Release 2 (Scenarios 1-10)

Release 2 adds the advanced business scenarios on top of the Release 1
terminal application: object usability, the menu, sample data and the
unittest suite arrive first (sprint 04), then the ten scenarios (sprints 05
and 08).

### Added - Sprint 04 (object usability, terminal application)

- Magic, class and static methods across `hms/` (`__str__`, `__repr__`,
  `__eq__`, `__len__`, `__contains__`, `__lt__`, `__add__`),
  `Patient.from_string()` and `Hospital.is_valid_phone()`.
- `hms/main.py`: menu driven terminal application; `hms/data/seed_data.py`:
  CityCare sample data (4 doctors, 2 nurses, 3 wards, 5 patients); the
  unittest suite in `tests/`.

### Added - Sprint 05 (scenarios 1-5)

- `hms/models/patient_status.py`: `PatientStatus` by composition - one
  `Patient` switches OPD to IPD without changing class, keeping the same id,
  history, prescriptions and bills (scenario 1).
- `hms/models/stay_record.py`: `StayRecord` with per-ward charging and
  `WardFullError` on transfer (scenario 2).
- `hms/services/payment.py`: `PaymentPolicy` strategy (self-pay, government
  scheme, private insurance, corporate) with `ClaimRejectedError` (scenario 3).
- Doctor leave: rescheduling with `RESCHEDULE_PENDING` and observer
  notifications (scenario 4).
- Booking rules: no double booking, 30-minute slots, breaks and refunds
  (scenario 5).

### Added - Sprint 08 (scenarios 6-10)

- `hms/models/discharge.py`: discharge state machine with
  `InvalidTransitionError` and transitions stored as data (scenario 6).
- `hms/models/emergency.py`: ICU severity queue and shifting suggestion when
  the ICU is full (scenario 7).
- `hms/services/safety.py`: allergy and drug-interaction checks with an
  override reason (scenario 8).
- Nurse coverage rules per ward and shift (scenario 9).
- `hms/services/commands.py`: `Command` undo with an audit log;
  `hms/services/reports.py`: revenue reports with iterators and generators;
  the "One day at CityCare" acceptance test (scenario 10).

Tags: `manas-dutt-sprint-04`, `manas-dutt-sprint-05`, `manas-dutt-sprint-08`,
`manas-dutt-v2.0`.

## [1.0.0] - 2026-10-04 - Release 1 (Modules 1-7)

Release 1 delivers Modules 1 to 7 of the CityCare requirements. Modules 8
(object usability) and 9 (the menu driven terminal application) did not fit the
Release 1 cut and now open Release 2 - see
[docs/project-plan.md](docs/project-plan.md).

### Added - Sprint 01 (core entities, data protection)

- `hms/models/medicine.py`: `Medicine` with `name`, `dosage` and `days`.
- `hms/models/ward.py`: `Ward` with `ward_type`, `total_beds`, `charge_per_day`
  and the methods `available_beds()` and `is_full()`, plus bed allocation
  helpers and the CityCare ward charges (General 1,000 / Private 3,500 / ICU
  8,000 per day).
- `hms/models/person.py`: abstract `Person` storing `age` and `phone` in the
  private attributes `__age` and `__phone`, exposed through validated
  properties (age 0-120, phone exactly 10 digits, `ValueError` on any other
  value) and automatic ids (`P001`, `D001`, `N001`, ...) from shared
  class-level counters.
- `hms/exceptions/`: the `HospitalError` hierarchy with `PatientNotFoundError`,
  `DoctorNotAvailableError`, `WardFullError` and `InvalidOperationError`.
- `hms/__init__.py` and `hms/models/__init__.py`: package initialisers that
  expose the public entities.

### Added - Sprint 02 (people hierarchy, uniform behaviour, pricing rules)

- `hms/models/staff.py`: `Doctor` (specialisation, consultation fee, available
  slots), `Nurse` (shift, assigned ward), `Receptionist` and `SeniorDoctor`,
  all inheriting from `Person` through `super().__init__()`. `SeniorDoctor` is
  the multilevel step and the only class with
  `can_approve_discharge = True`.
- `hms/models/patient.py`: `Patient` (blood group, medical history,
  prescriptions, appointments, bills) plus the concrete `OutPatient` and
  `InPatient` types, each with its own `get_details()` and bill formula:
  OPD = consultation fee + medicines, IPD = (days x ward charge) + doctor
  visits + medicines + 5% service tax; both apply the 10% senior citizen
  discount on the final amount.
- `hms/models/ambulance.py`: `Ambulance`, a vehicle that is not a person but
  still answers `get_details()`.
- `hms/models/person.py`: `print_all()`, which prints any mixed list of people
  and vehicles through `get_details()` alone - no `isinstance` checks.
- `hms/services/billing.py`: the CityCare pricing constants (service tax, senior
  discount and medicine charge per day) in one place.
- `hms/models/__init__.py`: exports the new entities.

### Added - Sprint 03 (contracts, hospital operations, error handling)

- `hms/services/billing.py`: the `Billable` contract (`abc.ABC` with the
  abstract `calculate_bill()`) and the `Bill` entity - id, patient, date, line
  items, total and `__str__`.
- `hms/models/patient.py`: `OutPatient` and `InPatient` now inherit `Patient`
  **and** `Billable`, so a patient object can be billed and a non-billable type
  can never reach the billing code.
- `hms/services/appointment.py`: `Appointment` with the `AppointmentStatus`
  enum (Scheduled, Completed, Cancelled), `complete()`, `cancel()` and
  `__str__`.
- `hms/models/prescription.py`: `Prescription` with its own `RX001` id series,
  the prescribing doctor and the patient's list of medicines.
- `hms/services/hospital.py`: the `Hospital` aggregate - it owns every patient,
  doctor, nurse, receptionist, ward, ambulance, appointment, prescription and
  bill; registrations, lookups (`find_patient()`, `find_doctor()`,
  `find_ward()`, `search_patient()`) and the operations
  `book_appointment()`, `cancel_appointment()`, `admit_patient()`,
  `discharge_patient()`, `ward_occupancy()`, `add_prescription()`,
  `generate_bill()` and `bills_sorted()`.
- Error handling: every failure raises a readable `HospitalError` subclass -
  `PatientNotFoundError`, `DoctorNotAvailableError`, `WardFullError` and
  `InvalidOperationError` - so the terminal menu only has to catch one base
  class and print `Error: <message>`.

### Deferred to Release 2 - Sprint 04

- Module 8 (object usability: `__eq__`, `__len__`/`__contains__`,
  `__lt__`/`__add__`, `Patient.from_string()`, `Hospital.is_valid_phone()`) and
  Module 9 (menu driven `hms/main.py`, CityCare sample data and the automated
  test suite) are the first sprint of Release 2 in
  [docs/project-plan.md](docs/project-plan.md).
