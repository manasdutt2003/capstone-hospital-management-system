# Sprint 04 - Object usability, terminal application, sample data and tests

| | |
|---|---|
| Branch | `manas-dutt/sprint-04-usability-cli` |
| Tag | `manas-dutt-sprint-04` |
| Planned end | 2026-10-16 |
| Actual end | 2026-10-06 |

## Goal

Deliver the two Release 1 modules that missed the Release 1 cut: object
usability (M8) and the menu driven terminal application with sample data and
tests (M9).

## Requirements covered

| Requirement | Where |
|-------------|-------|
| M8 - `__str__`/`__repr__`, `__eq__`, `__len__`/`__contains__`, `__lt__`, `__add__` | all models, `Bill`, `Ward` |
| M8 - `Patient.from_string()`, `Hospital.is_valid_phone()` | `hms/models/patient.py`, `hms/services/hospital.py` |
| M9 - menu driven `main.py` | `hms/main.py` |
| M9 - seed data (4 doctors, 2 nurses, 3 wards, 5 patients) | `hms/data/seed_data.py` |
| M9 - unittest suite | `tests/` |

## Outcome

Merged with PR #138; the unittest suite runs with
`py -3 -m unittest discover -s tests -t . -v` and the menu with
`python -m hms.main`.
