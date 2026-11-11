# Sprint 07 - Release 3 services and close (Features 6-10)

| | |
|---|---|
| Branch | `manas-dutt/sprint-07-release-3-services` |
| Tags | `manas-dutt-sprint-07`, `manas-dutt-v3.0` |
| Planned end | 2026-10-23 |
| Actual end | 2026-10-06 |

## Goal

Finish Release 3: beds, ambulance, diet/visitors, referrals, search.

## Requirements covered

| Feature | Where |
|---------|-------|
| F6 - Bed lifecycle + housekeeping (`Bed`, `WardKeeper`) | `hms/services/housekeeping.py` |
| F7 - Ambulance dispatch + charges | `hms/services/ambulance_service.py` |
| F8 - Diet charges + `VisitorPolicyError` | `hms/services/diet_visitors.py` |
| F9 - Referrals, follow-ups, feedback | `hms/models/referral.py` |
| F10 - Advanced search + timeline generator | `hms/services/search.py` |
| Release close | CHANGELOG, README, project-plan M3 |

## Commits

| Commit | Purpose |
|--------|---------|
| `feat(beds): add bed lifecycle and housekeeping` | F6 |
| `feat(ambulance): add dispatch charges and auto registration` | F7 |
| `feat(diet-visitors): add diet charges and VisitorPolicyError` | F8 |
| `feat(referrals): add referrals follow-ups and feedback` | F9 |
| `feat(search): add advanced search and timeline generator` | F10 |
| `docs(release): close Release 3 M3 features 1-10` | close |
