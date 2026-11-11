"""Prescription safety rules (Release 2, scenario 8).

Two checks run before any prescription is written: allergies (never
overridable) and dangerous medicine pairs (overridable by a doctor who
records a reason). The dangerous pairs live in :data:`DRUG_INTERACTIONS`, a
small dictionary kept as data so the pharmacy can extend it without touching
the checking code.
"""

from ..exceptions import AllergyAlertError, DrugInteractionError

#: Dangerous pairs as data: {frozenset({category, category}): reason}.
DRUG_INTERACTIONS = {
    frozenset({"Warfarin", "Aspirin"}): "increased bleeding risk",
    frozenset({"Warfarin", "Ibuprofen"}): "internal bleeding risk",
    frozenset({"Aspirin", "Ibuprofen"}): "stomach irritation and bleeding",
    frozenset({"Penicillin", "Tetracycline"}): "one neutralises the other",
    frozenset({"Metformin", "Furosemide"}): "lactate build-up risk",
}


def check_allergies(patient, medicines):
    """Raise when a medicine matches one of the patient's allergies.

    Raises:
        AllergyAlertError: naming the allergy and the medicine withheld.
    """
    for medicine in medicines:
        if medicine.category in patient.allergies or medicine.name in patient.allergies:
            raise AllergyAlertError(
                f"{patient.name} is allergic to {medicine.category}; "
                f"{medicine.name} was not prescribed."
            )


def find_interaction(medicines):
    """Return ``(first, second, reason)`` for the first dangerous pair found."""
    for index, first in enumerate(medicines):
        for second in medicines[index + 1:]:
            key = frozenset({first.category, second.category})
            if len(key) == 2 and key in DRUG_INTERACTIONS:
                return first, second, DRUG_INTERACTIONS[key]
    return None


def check_interactions(patient, new_medicines, existing_medicines, override,
                       override_reason):
    """Check new medicines against each other and against what is prescribed.

    Returns the override reason when the doctor chose to push on, otherwise
    ``None``.

    Raises:
        DrugInteractionError: a dangerous pair was found and the doctor did
            not pass ``override=True`` with a reason.
    """
    hit = find_interaction(list(new_medicines))
    if hit is None:
        for medicine in new_medicines:
            for existing in existing_medicines:
                key = frozenset({medicine.category, existing.category})
                if len(key) == 2 and key in DRUG_INTERACTIONS:
                    hit = (existing, medicine, DRUG_INTERACTIONS[key])
                    break
            if hit is not None:
                break
    if hit is None:
        return None
    first, second, reason = hit
    if override and str(override_reason).strip():
        return f"{first.name} + {second.name} ({reason}): {override_reason}"
    raise DrugInteractionError(
        f"{first.name} and {second.name} are a dangerous pair for "
        f"{patient.name} ({reason}); pass override=True with a reason to "
        f"prescribe anyway."
    )


def run_safety_checks(patient, new_medicines, existing_medicines,
                      override=False, override_reason=None):
    """Run both checks in order; return the stored override reason or None."""
    check_allergies(patient, new_medicines)
    return check_interactions(
        patient, new_medicines, existing_medicines, override, override_reason
    )