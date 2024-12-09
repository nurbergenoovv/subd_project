import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status, Request

from src.routes.global_counter.counter import get_current_counter, increment_counter
from src.routes.auth import auth
from src.routes.auth.schemas import UserOut
from src.routes.ticket.models import Ticket
from src.routes.category.models import Category
from src.routes.websocket.router import manager
from src.routes.ticket.schemas import TicketOut

async def create_ticket(db: AsyncSession, ticket_data: dict) -> Ticket:
    existing_ticket = await db.execute(
        select(Ticket).where(
            Ticket.full_name == ticket_data['full_name'],
            Ticket.phone_number == ticket_data['phone_number'],
            Ticket.category_id == ticket_data['category_id'],
            Ticket.status == 'wait'
        )
    )
    existing_ticket = existing_ticket.scalars().first()

    if existing_ticket:
        return existing_ticket

    language_mapping = {
        'ru': 'Русский',
        'kz': 'Қазақ',
        'en': 'English'
    }

    ticket_data['language'] = language_mapping.get(
        ticket_data['language'], None)

    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    new_ticket = Ticket(**ticket_data, number="0", token=token)

    try:
        db.add(new_ticket)
        await db.flush()
        current_counter = await increment_counter(db)

        new_ticket.number = f"{current_counter:03d}"

        await db.commit()
        await db.refresh(new_ticket)

        await manager.broadcast({
            "action": "new_ticket",
            "category_id": new_ticket.category_id,
            "data": TicketOut.from_orm(new_ticket).dict()
        })

    except Exception as e:
        await db.rollback()
        raise e

    return new_ticket


async def update_ticket(db: AsyncSession, ticket_id: int, ticket_data):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    db_ticket = result.scalars().first()

    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    for key, value in ticket_data.dict(exclude_unset=True).items():
        setattr(db_ticket, key, value)

    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)

    await manager.broadcast({
        "action": "update_ticket",
        "category_id": db_ticket.category_id,
        "data": TicketOut.from_orm(db_ticket).dict()
    })

    return db_ticket


async def update_ticket_telegram_id(db: AsyncSession, token: str, telegram_id: int):
    result = await db.execute(select(Ticket).where(Ticket.token == token))
    db_ticket = result.scalars().first()

    if not db_ticket:
        return False

    db_ticket.telegram_id = telegram_id

    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)

    return db_ticket


async def delete_ticket(db: AsyncSession, ticket_id: int):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    db_ticket = result.scalars().first()

    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    await db.delete(db_ticket)
    await db.commit()

    # Notify via WebSocket for the category
    await manager.broadcast({
        "action": "delete_ticket",
        "data": {"ticket_id": ticket_id}
    }, db_ticket.category_id)
    # Notify via WebSocket for the general queue
    await update_general_queue(db)

    return {"message": "Ticket deleted successfully"}


async def get_tickets(db: AsyncSession):
    result = await db.execute(select(Ticket))
    tickets = result.scalars().all()
    return tickets


async def get_ticket(db: AsyncSession, ticket_id: int):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    return ticket


async def get_ticket_by_token(db: AsyncSession, token: str):
    result = await db.execute(select(Ticket).where(Ticket.token == token))
    ticket = result.scalars().first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    return ticket


async def get_current_ticket(db: AsyncSession, ticket_id: int):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    return ticket


async def update_general_queue(db: AsyncSession):
    result = await db.execute(select(Ticket).where(Ticket.status == "wait").order_by(Ticket.created_at))
    tickets = result.scalars().all()
    await manager.broadcast({
        "action": "general_queue",
        "data": [TicketOut.from_orm(ticket).dict() for ticket in tickets]
    })

async def get_time_service_for_ticket(db: AsyncSession, ticket_id: int):
    query = select(
        Ticket.start_time,
        Ticket.end_time
    ).filter(
        Ticket.id == ticket_id,
        Ticket.start_time.isnot(None),
        Ticket.end_time.isnot(None)
    )

    result = await db.execute(query)
    ticket = result.fetchone()

    if ticket is None:
        return None

    start_time, end_time = ticket
    duration = end_time - start_time

    return duration



async def rate_ticket(ticket_id: int, request: Request, db: AsyncSession):
    data = await request.json()
    rating = data.get("rating")
    print(f"RATEEEEEE  {rating}")
    if not rating:
        raise HTTPException(status_code=400, detail="Rating is required")
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating should be between 1 and 10")
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    query = Ticket.__table__.update().values(rate=rating).where(Ticket.id == ticket_id)
    await db.execute(query)
    await db.commit()
    
    return ticket

