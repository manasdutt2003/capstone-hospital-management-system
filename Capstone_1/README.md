# Capstone 0 - Git and Python

**Hospital Management System (HMS) for CityCare Hospital** - a menu driven
command line application written in pure Python 3.10+ using only the standard
library.

| Attribute | Details |
|-----------|---------|
| Client | CityCare Hospital |
| Product | Hospital Management System (HMS), terminal application |
| Technology | Python 3.10+ (object oriented), Git |
| Delivery | 3 releases, planned as milestones and sprints |
| Author | Manas Dutt |
| Current status | All three releases delivered: `manas-dutt-v1.0`, `manas-dutt-v2.0`, `manas-dutt-v3.0` |

## Quick start

```bash
# Python 3.10+ is the only requirement: standard library only, nothing to install
py -3 --version

# try the hospital from this folder
py -3 -c "from hms.services.hospital import Hospital; h = Hospital(); h.add_ward('General', 3); p = h.register_patient('Ravi Kumar', 34, 'Male', '9876543215', 'O+', 'IPD'); h.admit_patient(p.person_id, 'General'); print(h.ward_occupancy()); print(h.generate_bill(p.person_id))"

# the menu driven application and the unittest suite
python -m hms.main
python -m unittest discover -s tests -t . -v
```

The application is used through `Hospital`, the single object that owns every
patient, doctor, nurse, ward, appointment, prescription, bill and Release 2/3
module. The menu starts with CityCare's sample data (4 doctors, 2 nurses,
3 wards, 5 patients).

## Folder structure

```
Capstone 0 - Git and Python/
├── README.md
├── CHANGELOG.md
├── .gitignore
├── docs/
│   ├── project-plan.md        # milestones and sprints
│   └── sprint-notes/          # sprint-01.md, sprint-02.md, sprint-03.md, ...
├── hms/
│   ├── __init__.py            # package version
│   ├── models/                # person, patient, staff, ward, medicine, ambulance, prescription
│   ├── services/              # hospital, appointment, billing
│   ├── exceptions/            # exceptions.py
│   ├── main.py                # menu driven terminal application (sprint 04)
│   └── data/                  # seed_data.py: CityCare sample data (sprint 04)
└── tests/                     # unittest scripts (sprint 04)
```

## What Release 1 contains

| Module | Requirement | Where it lives |
|--------|-------------|----------------|
| M1 | Core entities and shared data | `hms/models/medicine.py`, `hms/models/ward.py`, `Hospital.name` |
| M2 | Data protection and validation | `hms/models/person.py` (private `__age` and `__phone`) |
| M3 | People hierarchy, single and multilevel inheritance, `super()` | `hms/models/staff.py`, `hms/models/patient.py` |
| M4 | Uniform behaviour (`get_details()`, `get_role()`, `print_all()`) | `hms/models/person.py` and every subclass |
| M5 | Contracts and billing rules (`abc.ABC`, `Billable`) | `hms/services/billing.py`, `calculate_bill()` |
| M6 | Hospital operations | `hms/services/hospital.py`, `hms/services/appointment.py`, `hms/models/prescription.py` |
| M7 | Error handling | `hms/exceptions/exceptions.py` |

Release 1 was delivered in three sprints covering Modules 1-7; Release 2 adds
the ten advanced scenarios; Release 3 adds the ten additional features. The
plan, the requirements covered and the dates are recorded in
[docs/project-plan.md](docs/project-plan.md); the three releases are tagged
`manas-dutt-v1.0`, `manas-dutt-v2.0` and `manas-dutt-v3.0`.

## What Release 2 contains (Scenarios 1-10)

| Scenario | Where it lives |
|----------|----------------|
| 1 OPD becomes IPD (status by composition) | `hms/models/patient_status.py` |
| 2 Ward transfer with per-ward charging | `hms/models/stay_record.py` |
| 3 Insurance / payment strategies | `hms/services/payment.py` |
| 4 Doctor leave and rescheduling | `hms/services/appointment.py` (`RESCHEDULE_PENDING`) |
| 5 Booking conflicts and cancellation policy | `hms/services/hospital.py` |
| 6 Discharge state machine | `hms/models/discharge.py` |
| 7 Emergency with a full ICU | `hms/models/emergency.py` |
| 8 Prescription safety (allergy / interaction) | `hms/services/safety.py` |
| 9 Nurse coverage rules | `hms/services/hospital.py` |
| 10 Undo, audit trail and reports | `hms/services/commands.py`, `hms/services/reports.py` |

## What Release 3 contains (Features 1-10)

| Feature | Where it lives |
|---------|----------------|
| 1 Laboratory and diagnostics | `hms/models/lab.py` |
| 2 Health check-up packages | `hms/models/health_package.py` |
| 3 Operation theatre scheduling | `hms/models/surgery.py` |
| 4 Staff payroll | `hms/services/payroll.py` |
| 5 Blood bank | `hms/services/blood_bank.py` |
| 6 Bed lifecycle and housekeeping | `hms/services/housekeeping.py` |
| 7 Ambulance service | `hms/services/ambulance_service.py` |
| 8 Inpatient diet and visitors | `hms/services/diet_visitors.py` |
| 9 Referrals, follow-ups and feedback | `hms/models/referral.py` |
| 10 Advanced search and patient timeline | `hms/services/search.py` |
