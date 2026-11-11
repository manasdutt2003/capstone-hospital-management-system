# Sprint 05 - Release 2 scenarios 1-5 (care and billing)

| | |
|---|---|
| Branch | `manas-dutt/sprint-05-release-2-care-billing` |
| Tag | `manas-dutt-sprint-05` |
| Planned end | 2026-10-16 |
| Actual end | 2026-10-06 |

## Goal

Redesign the patient status, support ward transfers and payer rules, and
handle doctor leave and booking rules.

## Requirements covered

| Scenario | Where |
|----------|-------|
| 1 - OPD becomes IPD mid-visit (`PatientStatus` by composition) | `hms/models/patient_status.py`, `hms/models/patient.py` |
| 2 - Ward transfer during a stay (`StayRecord`, per-ward charging, `WardFullError`) | `hms/models/stay_record.py` |
| 3 - Insurance and payment methods (`PaymentPolicy` strategy, `ClaimRejectedError`) | `hms/services/payment.py` |
| 4 - Doctor leave: rescheduling, `RESCHEDULE_PENDING`, notifications | `hms/services/appointment.py` |
| 5 - Booking conflicts and cancellation policy (no double booking, 30-minute slots, breaks, refunds) | `hms/services/hospital.py` |

## Commits

| Commit | Purpose |
|--------|---------|
| `feat(transfer): add StayRecord with per-ward charging` | S2 |
| `feat(insurance): add PaymentPolicy strategy and ClaimRejectedError` | S3 |
| `feat(leave): add rescheduling with RESCHEDULE_PENDING and notify` | S4 |
| `feat(booking): add no-double-book 30min slots breaks refunds` | S5 |

Merged with PR #192 on 2026-10-06.
