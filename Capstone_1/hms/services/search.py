"""Release 3 Feature 10: advanced search and patient timeline.

``search_patients`` filters on name substring, blood group, patient type
and admission state. ``patient_timeline`` is a generator yielding dated
events (history, appointments, prescriptions, referrals) in order.
"""


def search_patients(patients, name=None, blood_group=None,
                    patient_type=None, admitted=None):
    """Filter ``patients``; every argument is optional."""
    found = []
    for patient in patients:
        if name and name.lower() not in patient.name.lower():
            continue
        if blood_group and patient.blood_group != blood_group:
            continue
        if patient_type and getattr(patient, "patient_type", None) != patient_type:
            continue
        if admitted is not None:
            is_adm = bool(getattr(patient, "is_admitted", False))
            if callable(getattr(patient, "is_admitted", None)) and not isinstance(
                    getattr(patient, "is_admitted"), bool):
                try:
                    is_adm = bool(patient.is_admitted())
                except TypeError:
                    pass
            if is_adm != bool(admitted):
                continue
        found.append(patient)
    return found


def patient_timeline(patient, referrals=()):
    """Yield ``(date_str, event)`` rows oldest-first as a generator."""
    yield ("history", list(getattr(patient, "medical_history", [])))
    for appt in getattr(patient, "appointments", []):
        yield ("appointment", str(getattr(appt, "get_details", lambda: appt)()))
    for rx in getattr(patient, "prescriptions", []):
        yield ("prescription", str(getattr(rx, "get_details", lambda: rx)()))
    for ref in referrals:
        if getattr(ref, "patient", None) is patient or ref.patient == patient:
            yield ("referral", ref.get_details())
            for note in ref.follow_ups:
                yield ("follow-up", note)
