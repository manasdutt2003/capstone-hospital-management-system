# Sprint 06 - Release 3 clinical modules (Features 1-5)

| | |
|---|---|
| Branch | `manas-dutt/sprint-06-release-3-clinical` |
| Tag | `manas-dutt-sprint-06` |
| Planned end | 2026-10-23 |
| Actual end | 2026-10-06 |

## Goal

Add the five clinical/staffing modules of Release 3 without touching
Release 1 billing behaviour.

## Requirements covered

| Feature | Where |
|---------|-------|
| F1 - Lab (`LabTest`, `BloodTest`, `XRay`, `MRI`, `ECG`, ABNORMAL flag, bill rows) | `hms/models/lab.py` |
| F2 - Health packages (nested, discount, same `price()`) | `hms/models/health_package.py` |
| F3 - Theatre (`Surgery`, `ResourceConflictError`, emergency override) | `hms/models/surgery.py` |
| F4 - Payroll (`calculate_salary`, 10% tax above Rs.50,000) | `hms/services/payroll.py` |
| F5 - Blood bank (42-day expiry, compatibility, oldest-first) | `hms/services/blood_bank.py` |

## Commits

| Commit | Purpose |
|--------|---------|
| `feat(lab): add LabTest BloodTest XRay MRI ECG with ABNORMAL flag` | F1 |
| `feat(packages): add health packages with nested discount and price()` | F2 |
| `feat(theatre): add Surgery scheduling with ResourceConflictError` | F3 |
| `feat(payroll): add calculate_salary per staff and Payroll` | F4 |
| `feat(blood-bank): add units 42-day expiry compatibility oldest-first` | F5 |
| `test(release3): cover F1-F5` | tests |
| `docs(sprint): add sprint 06 notes` | This note |
