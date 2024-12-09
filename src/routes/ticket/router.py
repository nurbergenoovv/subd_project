from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.routes.auth import auth
from src.routes.auth.schemas import UserOut
from src.routes.category.models import Category
from src.routes.ticket.models import Ticket
from src.routes.ticket.schemas import TicketCreate, TicketUpdate, TicketOut
from src.routes.ticket.ticket import create_ticket, rate_ticket, update_ticket, delete_ticket, get_tickets, get_ticket
from src.routes.websocket.router import manager
from src.schemas import QueueResponse, CurrentTicketWorker

router = APIRouter(
    prefix="/ticket",
    tags=["ticket"],
)

@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket_endpoint(ticket: TicketCreate, db: AsyncSession = Depends(get_async_session)):
    ticket_data = ticket.dict()
    return await create_ticket(db, ticket_data)

@router.put("/{ticket_id}", response_model=TicketOut)
async def update_ticket_endpoint(ticket_id: int, ticket: TicketUpdate, db: AsyncSession = Depends(get_async_session)):
    return await update_ticket(db, ticket_id, ticket)

@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_endpoint(ticket_id: int, db: AsyncSession = Depends(get_async_session)):
    return await delete_ticket(db, ticket_id)

@router.get("/", response_model=list[TicketOut])
async def get_tickets_endpoint(db: AsyncSession = Depends(get_async_session)):
    return await get_tickets(db)

@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket_endpoint(ticket_id: int, db: AsyncSession = Depends(get_async_session)):
    return await get_ticket(db, ticket_id)

@router.post("/skip", response_model=CurrentTicketWorker)
async def skip_and_get_next_ticket(request: Request, db: AsyncSession = Depends(get_async_session)):
    data = await request.json()
    worker_token = data.get("token")
    if worker_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    worker: UserOut = await auth.get_current_user(db, worker_token)

    current = await db.execute(
        select(Ticket).where(Ticket.worker_id == worker.id, Ticket.status == "invited")
    )
    current = current.scalars().first()
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket_data = TicketUpdate(status="skipped")
    current_ticket = await update_ticket(db, current.id, ticket_data)

    await manager.broadcast({
        "action": "skip_ticket",
        "category_id": current_ticket.category_id,
        "data": TicketOut.from_orm(current_ticket).dict()
    })

    next_ticket_result = await db.execute(
        select(Ticket).where(
            Ticket.category_id == current_ticket.category_id,
            Ticket.status == "wait",
            Ticket.worker_id == None
        ).order_by(Ticket.created_at)
    )
    next_ticket = next_ticket_result.scalars().first()
    if not next_ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No available tickets")
    next_ticket.status = "invited"
    next_ticket.worker_id = worker.id
    db.add(next_ticket)
    await db.commit()
    await db.refresh(next_ticket)

    category = await db.execute(select(Category).where(Category.id == next_ticket.category_id))
    category = category.scalars().first()

    await manager.broadcast({
        "action": "next_ticket",
        "category_id": next_ticket.category_id,
        "data": {"ticket": TicketOut.from_orm(next_ticket).dict(), "window": worker.window}
    })

    return CurrentTicketWorker(
        ticket_data=TicketOut.from_orm(next_ticket),
        ticket_id=next_ticket.id,
        ticket_number=int(next_ticket.number),
        category_name=category.name,
        ticket_created_time=next_ticket.created_at.strftime("%d.%m.%Y %H:%M"),
        ticket_language=next_ticket.language,
        ticket_phone_number=next_ticket.phone_number,  # Изменено с email на phone_number
        ticket_full_name=next_ticket.full_name  # Добавлено поле full_name
    )

@router.get("/{ticket_id}/cancel", response_model=TicketOut)
async def update_ticket_endpoint_cancel(ticket_id: int, db: AsyncSession = Depends(get_async_session)):
    ticket_data = TicketUpdate(status="cancelled")
    return await update_ticket(db, ticket_id, ticket_data)

@router.get("/worker/current", response_model=TicketOut)
async def get_current_ticket(request: Request, db: AsyncSession = Depends(get_async_session)):
    worker_token = request.cookies.get("token")
    if worker_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    worker: UserOut = await auth.get_current_user(db, worker_token)
    current_ticket = await db.execute(
        select(Ticket).where(Ticket.worker_id == worker.id, Ticket.status == "invited")
    )
    current_ticket = current_ticket.scalars().first()
    if current_ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return TicketOut.from_orm(current_ticket)

@router.get("/{ticket_id}/queue", response_model=QueueResponse)
async def get_queue_by_ticket_id(ticket_id: int, db: AsyncSession = Depends(get_async_session)):
    # Retrieve the ticket with the specified ticket_id
    ticket_stmt = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = ticket_stmt.scalars().first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Calculate the queue length
    queue_stmt = await db.execute(
        select(Ticket).where(
            Ticket.category_id == ticket.category_id,
            Ticket.status == "wait",
            Ticket.id < ticket.id
        )
    )
    front_queue = len(queue_stmt.scalars().all())

    return {"queue": front_queue}

@router.get('/worker/{worker_id}/all/', response_model=List[TicketOut])
async def get_all_by_worker_id_all(worker_id: int, db: AsyncSession = Depends(get_async_session)):
    worker: UserOut = await auth.get_user_by_id(db, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    query = select(Ticket).where(Ticket.worker_id == worker_id).order_by(desc(Ticket.created_at))

    result = await db.execute(query)
    tickets = result.scalars().all()

    return tickets

@router.post("/rate/{ticket_id}", response_model=TicketOut)
async def set_rate_ticket(ticket_id: int, request: Request, db: AsyncSession = Depends(get_async_session)):
    return await rate_ticket(ticket_id,request,db)