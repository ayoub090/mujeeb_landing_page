from __future__ import annotations

from dataclasses import dataclass

from app.models import FSMState


class InvalidTransition(ValueError):
    """Raised when a WhatsApp event is not valid for the current state."""


ALLOWED_TRANSITIONS: dict[FSMState, set[FSMState]] = {
    FSMState.order_received: {FSMState.awaiting_confirmation},
    FSMState.awaiting_confirmation: {
        FSMState.awaiting_address_choice,
        FSMState.order_cancelled,
        FSMState.modify_variants,
    },
    FSMState.modify_variants: {FSMState.awaiting_confirmation, FSMState.order_cancelled},
    FSMState.awaiting_address_choice: {
        FSMState.reverse_geo,
        FSMState.llm_parser_strict,
    },
    FSMState.reverse_geo: {FSMState.confirm_address_text, FSMState.order_cancelled},
    FSMState.llm_parser_strict: {FSMState.confirm_address_text, FSMState.awaiting_address_choice, FSMState.order_cancelled},
    FSMState.confirm_address_text: {FSMState.awaiting_address_choice, FSMState.upsell_pitch, FSMState.order_cancelled},
    FSMState.upsell_pitch: {FSMState.final_store_sync, FSMState.order_cancelled},
    FSMState.final_store_sync: {FSMState.order_confirmed},
    FSMState.order_cancelled: {FSMState.final_store_sync},
    FSMState.order_confirmed: {FSMState.tracking_active},
    FSMState.tracking_active: {FSMState.tracking_active},
}


@dataclass(frozen=True)
class Transition:
    source: FSMState
    target: FSMState
    event: str


def transition(source: FSMState, target: FSMState, event: str) -> Transition:
    if target not in ALLOWED_TRANSITIONS.get(source, set()):
        raise InvalidTransition(f"Cannot transition {source.value} -> {target.value} for {event}")
    return Transition(source, target, event)


def initial_state() -> FSMState:
    return FSMState.awaiting_confirmation
