# Sprint 02 - People hierarchy, uniform behaviour and pricing rules

| | |
|---|---|
| Branch | `manas-dutt/sprint-02-people-hierarchy` |
| Tag | `manas-dutt-sprint-02` |
| Planned end | 2026-10-06 |
| Actual end | 2026-10-03 |

## Goal

Turn the single `Person` base class into the real CityCare people tree, make
every type print and bill itself the same way, and put the money rules in one
place.

## Requirements covered

| Requirement | Where |
|-------------|-------|
| M3 - `Patient`, `Doctor`, `Nurse`, `Receptionist` inherit `Person` and call `super().__init__()` | `hms/models/staff.py`, `hms/models/patient.py` |
| M3 - `Doctor` specialisation, consultation fee, available slots | `Doctor` |
| M3 - `Nurse` shift and assigned ward | `Nurse` |
| M3 - `Patient` blood group and medical history | `Patient` |
| M3 - `OutPatient` / `InPatient`, `InPatient` ward, bed, admission date | `hms/models/patient.py` |
| M3 - `SeniorDoctor` with the right to approve discharges | `SeniorDoctor` |
| M4 - every subclass has its own `get_details()` | all models |
| M4 - `print_all(people)` with no `isinstance` checks | `hms/models/person.py` |
| M4 - `calculate_bill()` behaves differently for OPD and IPD | `OutPatient`, `InPatient` |
| M4 - `Ambulance` (not a person) also prints through `print_all()` | `hms/models/ambulance.py` |
| M5 (pricing) - OPD and IPD formulas, 5% tax, 10% senior discount, ward charges | `OutPatient.bill_line_items()`, `InPatient.bill_line_items()` |

## What was built

* `Doctor` -> `SeniorDoctor` (multilevel) and `Person` -> {`Doctor`, `Nurse`,
  `Receptionist`, `Patient`} -> {`OutPatient`, `InPatient`} (single level).
* Every type answers `get_details()` and `get_role()`, so one loop can print
  anything, patients and vehicles included.
* Two different bill formulas that share one set of helpers on `Patient`
  (`medicine_charges()`, `doctor_visits`, `visit_fee()`, `consultation_charges()`,
  `senior_discount_items()`).

## Worked examples (verified by running the code)

| Case | Result |
|------|--------|
| OPD, Dr. Meera Rao (Rs.800), no medicines | Rs.800.00 |
| OPD, same doctor, patient aged 67 | Rs.720.00 (10% senior discount) |
| IPD, General ward, 3 days, one visit at Rs.800 | 3,000 + 800 + 5% tax = Rs.3,990.00 |
| `print_all([patient, doctor, nurse, receptionist, ambulance])` | five lines, no type checks |

## Design notes

* `calculate_bill()` is the sum of `bill_line_items()`. The formula is
  documented on each class and the line items are visible on the bill, so a
  CityCare accountant can check every rupee without reading code.
* The senior discount is applied to the final amount (after the service tax),
  exactly as the requirement describes.
* `display_name` is defined on `Person` and overridden by `Doctor` ("Dr.
  ..."), which is why `OutPatient.get_details()` can show the doctor's name
  without knowing the class.
* `InPatient.ward` is kept after discharge: the bill must still know which ward
  and which daily charge to use, and `is_admitted` is what says whether the
  patient is still in a bed.

## Commits

| Commit | Purpose |
|--------|---------|
| `feat(billing): add CityCare pricing rules and charges` | M5 rates |
| `feat(staff): add Doctor with specialisation, consultation fee and slots` | M3 |
| `feat(staff): add Nurse and Receptionist subclasses` | M3 |
| `feat(staff): add SeniorDoctor for multi level inheritance` | M3 |
| `feat(ambulance): add Ambulance with get_details for print_all` | M4 |
| `feat(models): add print_all to display mixed hospital objects` | M4 |
| `feat(patient): add Patient with blood group and medical history` | M3 |
| `feat(patient): add OutPatient and InPatient with OPD and IPD bill formulas` | M3, M4, M5 |
| `chore(models): export the new people and vehicle entities` | Packaging |
| `docs(changelog): record sprint 02 changes` | Changelog |
| `docs(sprint): add sprint 02 notes` | This note |

## Next sprint

Sprint 03 adds the contracts (`abc.ABC` on `Person`, the `Billable` contract),
the `Appointment` / `Prescription` / `Bill` entities and the `Hospital`
aggregate with its eight operations and error handling.
