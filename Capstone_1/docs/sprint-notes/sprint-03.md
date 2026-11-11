# Sprint 03 - Contracts, hospital operations and error handling

| | |
|---|---|
| Branch | `manas-dutt/sprint-03-contracts-operations` |
| Tag | `manas-dutt-sprint-03` |
| Planned end | 2026-10-08 |
| Actual end | 2026-10-04 |

## Goal

Put Module 5's two contracts in place, build Module 6's new entities
(`Appointment`, `Prescription`, `Bill`) and the `Hospital` aggregate that owns
the whole system, and turn every failure into a readable `HospitalError`
instead of a crash.

## Requirements covered

| Requirement | Where |
|-------------|-------|
| M5 - abstract `Billable` with `calculate_bill()`, implemented by both patient types | `hms/services/billing.py`, `hms/models/patient.py` |
| M5 - `Person` stays an `abc.ABC`, so only concrete people can be created | `hms/models/person.py` |
| M6 - `Appointment` holds patient, doctor, slot and a status enum | `hms/services/appointment.py` |
| M6 - state machine: SCHEDULED to COMPLETED or CANCELLED, nothing else | `Appointment.complete()`, `Appointment.cancel()` |
| M6 - `Prescription` holds a doctor, a patient and `Medicine` objects; the patient keeps the list | `hms/models/prescription.py`, `Patient.prescriptions` |
| M6 - `Bill` holds a bill_id, patient, line items and total | `hms/services/billing.py` |
| M6 - `Hospital` owns all patients, doctors, nurses, wards, appointments, prescriptions and bills | `hms/services/hospital.py` |
| M6 - the eight operations CityCare listed | table below |
| M7 - `HospitalError` subclasses raised with a clear message | `hms/exceptions/exceptions.py` |

## The eight operations CityCare asked for

| Operation | Rule it enforces |
|-----------|------------------|
| `register_patient()` | OPD or IPD only; validating the person data is `Person`'s job |
| `book_appointment()` | the doctor must publish that slot and it must still be free |
| `cancel_appointment()` | only a scheduled appointment can be cancelled |
| `admit_patient()` | inpatients only, bed reserved, `WardFullError` when the ward is full |
| `discharge_patient()` | frees the bed, keeps the ward so the bill is still correct |
| `add_prescription()` | doctor + patient + at least one medicine |
| `generate_bill()` | sums the patient's own line items through `Billable` |
| `search_patient()` | by id or by part of a name |

`ward_occupancy()` is an extra read-only view: one row per ward with its total,
occupied and available beds and its daily charge.

## Worked examples (verified by running the code)

Setup used for these runs: 3 wards (General 3 beds, Private 1, ICU 1),
Dr. Meera Rao (Rs.800), Dr. Priya Shah (Rs.500), Ravi Kumar (34, OPD),
Saroj Verma (65, OPD) and Sita Devi (67, IPD).

| Case | Result |
|------|--------|
| OPD, one completed visit at Rs.800 plus Paracetamol 3 days (3 x Rs.50) | Rs.950.00 |
| OPD, one completed visit at Rs.500, patient aged 65 | Rs.450.00 (10% senior discount) |
| IPD, General ward 1 day, one visit at Rs.800, patient aged 67 | 1,000 + 800 + 5% tax (90) - 10% senior discount (189) = Rs.1,701.00 |
| `ward_occupancy()[0]` after one admission | `{'ward': 'General', 'total': 3, 'occupied': 1, 'available': 2, 'charge_per_day': 1000.0}` |
| `bills_sorted()` | `B003 Rs.1,701.00`, `B001 Rs.950.00`, `B002 Rs.450.00` |
| `print_all([patient, doctor, nurse, receptionist, ambulance])` | five lines, no type checks |

## Error paths (verified by running the code)

| Case | Result |
|------|--------|
| `find_patient("P999")` | `PatientNotFoundError: No patient found with id P999.` |
| `book_appointment()` at a time the doctor does not work | `DoctorNotAvailableError: Dr. Arun Nair does not work at 10:00. Available slots: 09:00, 15:00.` |
| `book_appointment()` at a slot another scheduled appointment holds | `DoctorNotAvailableError: Dr. Meera Rao is not available at 11:00.` |
| `discharge_patient()` on an outpatient | `InvalidOperationError: Ravi Kumar is an outpatient, so there is nothing to discharge.` |
| `cancel_appointment()` on a completed appointment | `InvalidOperationError: Appointment A001 is completed, so it cannot be cancelled.` |
| `generate_bill()` for an inpatient who was never admitted | `InvalidOperationError: Neha Menon is not admitted to a ward, so there is no inpatient bill to generate.` |
| `admit_patient()` into a full ward | `WardFullError: Private ward is full (1/1 beds occupied).` |
| `admit_patient()` with an unknown ward type | `ValueError: Unknown ward type 'Deluxe'. Registered wards: General, Private, ICU.` |
| phone that is not 10 digits / age above 120 | `ValueError: Phone number must be exactly 10 digits.` / `ValueError: Age must be between 0 and 120.` |

Every one of them derives from `HospitalError`, so the sprint 04 menu catches
that one base class and prints `Error: <message>` - the application never
crashes on bad input.

## Design notes

* A `Bill` is never built by hand: `Hospital.generate_bill()` asks the patient
  for `bill_line_items()`, so the OPD formula and the IPD formula stay in the
  two patient classes and the billing code never has to ask what type of
  patient it is holding.
* `book_appointment()` assigns the patient's attending doctor, which is why an
  admitted inpatient who has not been seen yet is billed one visit: a doctor is
  already responsible for them.
* Admission is a service rule, not a display rule. The single
  `isinstance(patient, InPatient)` test lives in `Hospital.admit_patient()` and
  `discharge_patient()`; all printing still goes through `get_details()` with no
  type checks anywhere.
* `Ward.occupy_bed()` returns the bed number it took and `Ward.release_bed()`
  returns the patient it freed, so `Hospital` keeps `bed_number` and the medical
  history in step with the ward.
* `normalise_slot()` accepts `9:00`, `09.00` and `0900`, so a receptionist can
  type a slot the way they say it, while the stored slot is always `HH:MM`.
* `ward_occupancy()` returns dictionaries, not `Ward` objects, so callers cannot
  reach into the ward through the view.

## Commits

| Commit | Purpose |
|--------|---------|
| `feat(billing): add the Billable contract and the Bill entity` | M5, M6 |
| `feat(billing): bind the patient types to the Billable contract` | M5 |
| `feat(appointment): add Appointment with a status enum` | M6 |
| `feat(prescription): add Prescription for patient medicine lists` | M6 |
| `chore(services): keep the services package initialiser lightweight` | Packaging |
| `feat(hospital): add the Hospital aggregate with registrations and search` | M6 |
| `feat(hospital): add appointment booking and cancellation` | M6 |
| `feat(hospital): add admission, discharge and ward occupancy` | M6 - this commit also carries the prescription and billing methods, so it is the one commit in this sprint that covers more than one requirement |
| `docs(plan): close release 1 on modules 1-7 and move modules 8-9 to sprint 04` | Plan |
| `docs(changelog): record release 1 (modules 1-7) and the sprint 03 changes` | Changelog |
| `docs(readme): document the release 1 modules and the future menu` | README |
| `docs(sprint): add sprint 03 notes` | This note |

## Release 1

Release 1 (milestone M1) was cut on 2026-10-04 with the tag
`manas-dutt-v1.0` and covers Modules 1-7. Modules 8 (object usability) and 9
(the menu driven terminal application with sample data and the test suite) were
re-planned into Release 2 sprint 04 - see
[project-plan.md](../project-plan.md).
