from enum import StrEnum

__all__ = (
    "Event",
    "Reason",
)


class Event(StrEnum):
    # Dispatched after queue owner submits prematch modal successfully
    PREMATCH_MODAL_DONE = "prematch_modal_done"

    # Dispatched after player drafts are completed by team captains
    VC_LISTENER_ADD = "vc_listener_add"

    # Dispatched after report results button is pressed by queue owner
    VC_LISTENER_REMOVE = "vc_listener_remove"
    
    # Dispatched after the reset button was pressed
    RESET_BUTTON_PRESSED = "reset_button_pressed"

    # Dispatched after match has been finalised (win + mvp set for both teams)
    MATCH_FINALISED = "match_finalised"


class Reason(StrEnum):
    TEAM_VC = "Automatically moved into team voice channel."
    VIEW_RESET_STATE = "Reset button was pressed on a match. Moved back to lobby voice channel."
    MATCH_FINALISED_DEL_TEMP = "Match was finalised, temp channel no longer needed."
    MATCH_FINALISED_LOBBY_MOVE = "Match was finalised, moved back to lobby voice channel."