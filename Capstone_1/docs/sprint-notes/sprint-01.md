# Sprint 01 - Foundation, core entities and data protection

| | |
|---|---|
| Branch | `manas-dutt/sprint-01-core-entities` |
| Tag | `manas-dutt-sprint-01` |
| Planned end | 2026-10-05 |
| Actual end | 2026-10-03 |

## Goal

Create the folder structure CityCare asked for, then build the shared building
blocks every later module depends on: the core entities and the protected,
validated person data.

## Requirements covered

| Requirement | Where |
|-------------|-------|
| M1 - `Medicine` with name, dosage and days | `hms/models/medicine.py` |
| M1 - `Ward` with type, beds, charge, `available_beds()`, `is_full()` | `hms/models/ward.py` |
| M1 - hospital name stored once and shared | `Hospital.name` (class attribute, added in sprint 03) |
| M2 - `Person` with id, name, age, gender, phone | `hms/models/person.py` |
| M2 - private `__age`, `__phone` with getters and setters | `hms/models/person.py` |
| M2 - age 0-120 and phone exactly 10 digits, `ValueError` otherwise | `hms/models/person.py` |
| M2 - automatic ids `P001`, `D001`, `N001` from class-level counters | `Person._generate_id()` |
| M7 - base `HospitalError` and its subclasses | `hms/exceptions/exceptions.py` |

## What was built

* The required folder layout (`docs/`, `hms/models/`, `hms/services/`,
  `hms/exceptions/`, `hms/data/`, `tests/`) with `README.md` and `.gitignore`.
* `Medicine` and `Ward` as small, self-validating value objects.
* `Person` as an `abc.ABC` with two abstract methods and a validated,
  encapsulated core.
* The exception hierarchy that the sprints 03 and 04 use for every failure.

## Design notes

* `Person` is abstract, so the system can never hold a "person" that is not a
  patient, doctor, nurse or receptionist.
* `age` and `phone` use name mangling (`__age`, `__phone`). The setter is the
  only door into them, which means an invalid value can never reach the object.
* Ids come from a dictionary of counters keyed by the id prefix, held on
  `Person` itself. Keying by prefix (and not by class name) is deliberate: the
  first implementation keyed by `cls.__name__`, which would have restarted the
  `P` series inside `InPatient`; keying by prefix keeps `P001`, `P002`, ...
  unique across `OutPatient` and `InPatient`.
* The ward charges table lives next to `Ward` as `WARD_CHARGES`, so the pricing
  data is not buried inside billing code.

## Commits

| Commit | Purpose |
|--------|---------|
| `chore(project): scaffold capstone folder structure with readme and gitignore` | First commit: structure, README, .gitignore |
| `docs(plan): add release 1 milestones and sprints` | Second commit: the plan itself |
| `feat(exceptions): add HospitalError hierarchy for domain failures` | M7 base types |
| `feat(medicine): add Medicine entity for prescriptions` | M1 |
| `feat(ward): add Ward with bed capacity, charges and occupancy helpers` | M1 |
| `feat(person): add abstract Person with private age and phone validation` | M2 |
| `refactor(person): share one id counter per prefix across patient types` | M2 |
| `chore(hms): add package initialisers and public exports` | Packaging |
| `docs(changelog): start changelog with release 1 and sprint 01 entries` | Changelog |
| `docs(sprint): add sprint 01 notes` | This note |

## Next sprint

Sprint 02 builds the people hierarchy (`Doctor`, `Nurse`, `Receptionist`,
`Patient`, `OutPatient`, `InPatient`, `SeniorDoctor`), the uniform
`get_details()` / `print_all()` behaviour and the OPD / IPD bill formulas.
