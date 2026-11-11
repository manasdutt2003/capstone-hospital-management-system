# CityCare Hospital Management System

A menu-driven Hospital Management System written in **pure Python 3.10+** — standard library only,
no third-party packages, nothing to install.

> Week 1 individual capstone · Perficient Global AI First Academy · Author: **Manas Dutt**

## What it is

A full hospital operations system for a fictional client, CityCare Hospital: patients, doctors,
nurses, wards, appointments, prescriptions, billing and ambulances, modelled as a proper class
hierarchy rather than a script. Delivered as **three tagged releases** planned across milestones
and sprints, the way a client engagement would be run.

| Attribute | Details |
|---|---|
| Client | CityCare Hospital (scenario) |
| Technology | Python 3.10+ (object-oriented), Git |
| Delivery | 3 releases, planned as milestones and sprints |
| Releases | `manas-dutt-v1.0`, `manas-dutt-v2.0`, `manas-dutt-v3.0` |
| Dependencies | **None** — standard library only |

## Quick start

```bash
python --version        # 3.10+ is the only requirement

# run the menu-driven application
cd Capstone_1
python -m hms.main

# run the test suite
python -m unittest discover -s tests -t . -v
```

The menu starts with CityCare's seeded sample data: 4 doctors, 2 nurses, 3 wards, 5 patients.

## What each release contains

**Release 1 — core system (Modules M1–M7)**

| Module | Requirement |
|---|---|
| M1 | Core entities and shared data |
| M2 | Data protection and validation (private `__age`, `__phone`) |
| M3 | People hierarchy, single and multilevel inheritance, `super()` |
| M4 | Uniform behaviour — `get_details()`, `get_role()`, `print_all()` |
| M5 | Contracts and billing rules (`abc.ABC`, `Billable`) |
| M6 | Hospital operations, appointments, prescriptions |
| M7 | Custom exception hierarchy |

**Release 2 — ten advanced scenarios**, including OPD→IPD status by composition, ward transfer with
per-ward charging, insurance and payment strategies, and doctor leave with appointment rescheduling.

**Release 3 — ten further features**, plus the `unittest` suite and seeded sample data.

## Layout

```
Capstone_1/
├── hms/
│   ├── models/        person, patient, staff, ward, medicine, ambulance, prescription
│   ├── services/      hospital, appointment, billing
│   ├── exceptions/    custom exception hierarchy
│   ├── data/          seed_data.py — CityCare sample data
│   └── main.py        menu-driven terminal application
├── tests/             unittest suite
├── docs/              project plan, sprint notes
└── README.md          full module-by-module breakdown
```

`Hospital` is the single object that owns every patient, doctor, nurse, ward, appointment,
prescription and bill.

## Detailed documentation

See [`Capstone_1/README.md`](Capstone_1/README.md) for the complete requirement-to-code mapping,
and [`Capstone_1/docs/project-plan.md`](Capstone_1/docs/project-plan.md) for milestones and sprints.
