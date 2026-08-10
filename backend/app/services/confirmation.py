from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FSMConversation, FSMState, Order
from app.services.fsm import initial_state
from app.services.whatsapp import confirmation_payload, send_whatsapp_message


async def start_cod_confirmation(
    session: AsyncSession,
    order: Order,
    phone: str,
    customer_name: str,
) -> dict | None:
    """Create the persistent FSM session and send the first COD prompt."""
    if order.payment_method.lower() != "cod":
        return None
    conversation = await session.scalar(
        select(FSMConversation).where(
            FSMConversation.phone_number == str(phone), FSMConversation.order_id == order.id
        )
    )
    if conversation is None:
        conversation = FSMConversation(
            phone_number=str(phone), order_id=order.id, current_state=initial_state(), session_data={}
        )
        session.add(conversation)
    else:
        conversation.current_state = initial_state()
    await session.flush()
    return await send_whatsapp_message(
        str(phone),
        confirmation_payload(
            order.external_order_number or str(order.id), str(order.amount), customer_name
        ),
    )
