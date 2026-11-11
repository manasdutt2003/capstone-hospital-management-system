"""The discharge state machine (Release 2, scenario 6).

Discharge is no longer a single method call: an inpatient moves through six
fixed states, each transition guarded by :func:`transition`. The allowed
moves are stored as **data** in :data:`ALLOWED_TRANSITIONS` instead of a long
``if/elif`` chain, so a reviewer can see the whole machine at a glance and a
new state only ever means one more dictionary entry.
"""

from enum import Enum

from ..exceptions import InvalidTransitionError


class DischargeState(Enum):
    """The fixed states an inpatient moves through before leaving."""

    ADMITTED = "Admitted"
    UNDER_TREATMENT = "Under treatment"
    DISCHARGE_REQUESTED = "Discharge requested"
    APPROVED = "Approved for discharge"
    BILLED = "Billed"
    DISCHARGED = "Discharged"


#: The whole state machine, as data: state -> the states it may move to next.
#: Any other jump (for example ADMITTED -> DISCHARGED) is invalid.
ALLOWED_TRANSITIONS = {
    DischargeState.ADMITTED: {DischargeState.UNDER_TREATMENT},
    DischargeState.UNDER_TREATMENT: {DischargeState.DISCHARGE_REQUESTED},
    DischargeState.DISCHARGE_REQUESTED: {DischargeState.APPROVED},
    DischargeState.APPROVED: {DischargeState.BILLED},
    DischargeState.BILLED: {DischargeState.DISCHARGED},
}


def transition(current, target):
    """Return ``target`` when the move is legal, else raise.

    Raises:
        InvalidTransitionError: when ``target`` is not one of the states
            listed after ``current`` in :data:`ALLOWED_TRANSITIONS`.
    """
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(
            f"Cannot move from {current.value} to {target.value}. "
            f"Allowed from {current.value}: "
            f"{', '.join(state.value for state in sorted(allowed, key=lambda s: s.name)) or 'nothing'}."
        )
    return target