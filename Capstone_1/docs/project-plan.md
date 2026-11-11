# Capstone 0 - Project plan

Author: **Manas Dutt**
Client: **CityCare Hospital**
Product: Hospital Management System (HMS) - terminal application, pure Python 3.10+

CityCare does not prescribe a sprint plan, so the plan below is my own.
Release 1 is one milestone; Release 2 and Release 3 are planned as the two
milestones that follow it. Each sprint is a branch, a set of commits and a tag.

## Naming conventions

| Item | Pattern | Examples |
|------|---------|----------|
| Branch | `<name>/sprint-<nn>-<slug>` | `manas-dutt/sprint-01-core-entities` |
| Sprint tag | `<name>-sprint-<nn>` | `manas-dutt-sprint-01` |
| Release tag | `<name>-v<major>.<minor>` | `manas-dutt-v1.0` |
| Commit | `type(scope): summary` | `feat(patient): add private age with validation` |
| Commit types | `feat`, `fix`, `refactor`, `docs`, `test`, `chore` | |

## Milestones

| # | Milestone | Scope | Planned end | Actual end | Status |
|---|-----------|-------|-------------|------------|--------|
| M1 | Release 1 - CityCare core HMS | Modules 1-9 of the client requirement document | 2026-10-09 | 2026-10-03 | Delivered |
| M2 | Release 2 - Advanced business scenarios | Scenarios 1-10 (patient status composition, ward transfer, insurance, leave, cancellation policy, discharge state machine, emergency, prescription safety, nurse coverage, reports) | 2026-10-16 | 2026-10-06 | Delivered |
| M3 | Release 3 - Additional features | Features 1-10 (lab, packages, theatre, payroll, blood bank, bed lifecycle, ambulance, diet and visitors, referrals, advanced search) | 2026-10-23 | 2026-10-06 | Delivered |

## Milestone M3 - sprints

| Sprint | Branch | Goal | Requirements covered | Planned end | Actual end |
|--------|--------|------|----------------------|-------------|------------|
| 06 | `manas-dutt/sprint-06-release-3-clinical` | Clinical modules F1-F5 | F1 lab, F2 packages, F3 theatre, F4 payroll, F5 blood bank | 2026-10-23 | 2026-10-06 |
| 07 | `manas-dutt/sprint-07-release-3-services` | Services F6-F10 + close | F6 beds, F7 ambulance, F8 diet/visitors, F9 referrals, F10 search, CHANGELOG + docs | 2026-10-23 | 2026-10-06 |

Result: Release 3 (milestone M3, Features 1-10) was completed on 2026-10-06,
ahead of the planned end date 2026-10-23. Tagged `manas-dutt-v3.0`.

## Milestone M1 - sprints

Release 1 is expected in 5 working days (2026-10-05 to 2026-10-09). The plan
started with four increments inside that window; the fourth one (object
usability and the terminal application) did not fit the Release 1 cut, so the
release was closed on the three sprints below and that increment became the
first sprint of Release 2.

| Sprint | Branch | Goal | Requirements covered | Planned end | Actual end |
|--------|--------|------|----------------------|-------------|------------|
| 01 | `manas-dutt/sprint-01-core-entities` | Foundation, core entities and protected person data | M1: Medicine, Ward, shared hospital name. M2: Person with private `age`/`phone`, validation (0-120, 10 digits), automatic `P001`/`D001`/`N001` ids. Custom exception hierarchy (base for M7) | 2026-10-05 | 2026-10-03 |
| 02 | `manas-dutt/sprint-02-people-hierarchy` | People hierarchy, uniform behaviour and pricing rules | M3: Patient, Doctor, Nurse, Receptionist, `super().__init__()`, OutPatient, InPatient, SeniorDoctor. M4: `get_details()`, `get_role()`, `print_all()` without `isinstance`, Ambulance. M4/M5: OPD and IPD bill formulas, 5% service tax, 10% senior discount | 2026-10-06 | 2026-10-03 |
| 03 | `manas-dutt/sprint-03-contracts-operations` | Contracts, hospital operations and error handling | M5: `abc.ABC` Person contract, `Billable` contract. M6: Appointment (status enum), Prescription, Bill, the `Hospital` aggregate and all eight operations. M7: every `HospitalError` subclass raised and reported as `Error: <message>` | 2026-10-08 | 2026-10-04 |

Result: Release 1 (milestone M1, Modules 1-7) was completed on 2026-10-04, ahead
of the planned end date 2026-10-09. Modules 8 and 9 were re-planned into
milestone M2, where they are sprint 04.

## Milestone M2 - sprints

| Sprint | Branch | Goal | Requirements covered | Planned end | Actual end |
|--------|--------|------|----------------------|-------------|------------|
| 04 | `manas-dutt/sprint-04-usability-cli` | Object usability, terminal application, sample data and tests (the two Release 1 modules left over) | M8: `__str__`/`__repr__`, `__eq__`, `__len__`/`__contains__`, `__lt__`, `__add__`, `Patient.from_string()`, `Hospital.is_valid_phone()`. M9: menu driven `main.py`, seed data (4 doctors, 2 nurses, 3 wards, 5 patients), unittest suite, README module map and CHANGELOG | 2026-10-16 | 2026-10-06 |
| 05 | `manas-dutt/sprint-05-release-2-care-billing` | Patient status, transfers, insurance, leave and booking (scenarios 1-5) | S1: `PatientStatus` by composition, same id across an OPD to IPD switch. S2: `StayRecord` with per-ward charging, `WardFullError` on transfer. S3: `PaymentPolicy` strategy with `ClaimRejectedError`. S4: doctor leave rescheduling (`RESCHEDULE_PENDING`) and notifications. S5: no double booking, 30-minute slots, breaks, refunds | 2026-10-16 | 2026-10-06 |
| 08 | `manas-dutt/sprint-08-release-2-safety-reports` | Discharge state machine, emergency, safety, coverage, undo and reports (scenarios 6-10) | S6: discharge state machine with `InvalidTransitionError`. S7: ICU severity queue and shifting suggestion. S8: `AllergyAlertError` / `DrugInteractionError` with override reason. S9: nurse coverage rules. S10: `Command` undo, audit log, generator reports and the "One day at CityCare" acceptance test | 2026-10-16 | 2026-10-06 |

Result: Release 2 (milestone M2, Scenarios 1-10) was completed on 2026-10-06,
ahead of the planned end date 2026-10-16. Tagged `manas-dutt-v2.0`.

## How every sprint was closed

1. Branch created from an up-to-date `main`:
   `git checkout main && git pull && git checkout -b manas-dutt/sprint-0n-<slug>`
2. At least one commit per requirement, using `type(scope): summary`.
3. Sprint note added in `docs/sprint-notes/sprint-0n.md`, `CHANGELOG.md` updated.
4. Branch merged into `main` through a pull request (the merge is `--no-ff` so the
   sprint keeps its own history) and the merged commit tagged
   `manas-dutt-sprint-0n`.
5. `manas-dutt-v1.0` tagged on the last merged Release 1 commit.

## Requirement to sprint traceability

| Requirement | Sprint | Primary artefact |
|-------------|--------|------------------|
| M1 Core entities | 01 | `hms/models/medicine.py`, `hms/models/ward.py`, `Hospital.name` |
| M2 Data protection and validation | 01 | `hms/models/person.py` |
| M3 People hierarchy | 02 | `hms/models/patient.py`, `hms/models/staff.py` |
| M4 Uniform behaviour | 02 | `get_details()`, `get_role()`, `print_all()`, `hms/models/ambulance.py` |
| M5 Contracts and billing rules | 02, 03 | `hms/services/billing.py`, patient `calculate_bill()` |
| M6 Hospital operations | 03 | `hms/services/hospital.py`, `hms/services/appointment.py`, `hms/models/prescription.py` |
| M7 Error handling | 01, 03 (04 for the menu) | `hms/exceptions/exceptions.py`, `Error: <message>` handling in `hms/main.py` |
| M8 Object usability | Release 2 sprint 04 | magic, class and static methods across `hms/` |
| M9 Terminal application | Release 2 sprint 04 | `hms/main.py`, `hms/data/seed_data.py` |
