from datetime import datetime
from fastapi import Depends, HTTPException, logger, status, APIRouter, Request
import pytz
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_async_session
from src.routes.auth import auth
from src.routes.category.schemas import CategoryCreate, CategoryOutput, CategoryUpdate
from src.routes.category.models import Category
from src.routes.auth.models import User
from src.routes.auth.schemas import UserOut
from src.routes.ticket.models import Ticket
from src.routes.ticket.schemas import TicketOut
from src.routes.ticket.ticket import create_ticket, update_ticket, delete_ticket, get_tickets, get_ticket
from src.routes.websocket.router import manager
from src.schemas import CurrentTicketWorker
from telegram_bot.main import dp


router = APIRouter(
    prefix="/category",
    tags=["category"],
)


@router.post("/", response_model=CategoryOutput, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_async_session)):
    new_category = Category(**category.dict())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category


@router.put("/{category_id}", response_model=CategoryOutput)
async def update_category(category_id: int, category: CategoryUpdate, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalars().first()

    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for key, value in category.dict(exclude_unset=True).items():
        setattr(db_category, key, value)

    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalars().first()

    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await db.delete(db_category)
    await db.commit()
    return {"message": "Category deleted successfully"}


@router.get("/", response_model=list[CategoryOutput])
async def get_categories(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return categories


@router.get("/{category_id}", response_model=CategoryOutput)
async def get_category(category_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().first()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return category


@router.get("/all/users", response_model=list[dict])
async def get_all_users(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()

    response = []
    for category in categories:
        users = await db.execute(select(User).where(User.category_id == category.id))
        users = users.scalars().all()
        response.append({
            "category": CategoryOutput.from_orm(category).dict(),
            "users": [UserOut.from_orm(user).dict() for user in users]
        })

    return response


@router.get("/{category_id}/users", response_model=list[UserOut])
async def get_users_by_id(category_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(User).where(User.category_id == category_id))
    users = result.scalars().all()
    return [UserOut.from_orm(user) for user in users]


@router.get("/{category_id}/tickets", response_model=list[TicketOut])
async def get_tickets_by_id(category_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(Ticket).order_by(Ticket.id).where(Ticket.category_id == category_id, Ticket.status == "wait"))
    tickets = result.scalars().all()
    return [TicketOut.from_orm(ticket) for ticket in tickets]


@router.post("/ticket/next", response_model=CurrentTicketWorker)
async def get_next_ticket(request: Request,
                          db: AsyncSession = Depends(get_async_session)) -> CurrentTicketWorker:
    data = await request.json()  # Получаем JSON данные из запроса
    worker_token = data.get("token")  # Извлекаем токен сотрудника

    tz = pytz.timezone('Asia/Almaty')  # Устанавливаем часовой пояс для Алматы
    # Получаем текущее время и дату и делаем её timezone-naive
    now = datetime.now(tz).replace(tzinfo=None)
    if worker_token is None:  # Проверяем наличие токена
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    # Аутентифицируем пользователя по токену
    worker: UserOut = await auth.get_current_user(db, worker_token)

    current_ticket = await db.execute(
        select(Ticket).where(Ticket.worker_id ==
                             worker.id, Ticket.status == "invited")
    )
    # Получаем текущий билет, назначенный сотруднику
    current_ticket = current_ticket.scalars().first()
    if current_ticket:
        current_ticket.status = "completed"  # Обновляем статус билета на "completed"
        current_ticket.end_time = now  # Устанавливаем время завершения билета
        db.add(current_ticket)
        await db.commit()
        await db.refresh(current_ticket)
        today = now.date()  # Получаем текущую дату

        # completed_tickets_res = await db.execute(
        #   select(Ticket).order_by(Ticket.created_at.asc()).limit(200)
        #   .where(
        #        Ticket.status == 'completed',
        #        Ticket.category_id == ticket.category_id,
        #         func.date(Ticket.created_at) == today
        #        )
        #   )
        

        # completed_tickets = completed_tickets_res.scalars().all()

        average_duration = 0
        # if completed_tickets:
        #     durations = [
        #         (ticket.end_time - ticket.start_time).total_seconds() / 60
        #         for ticket in completed_tickets
        #     ]
        #     average_duration = sum(durations) / len(durations)
   

        # await manager.broadcast({
        #     "action": "average_duration",
        #     "category_id": worker.category_id,
        #     "data": {"average_duration": average_duration}
        # })

    if current_ticket:
        await manager.broadcast({
            "action": "complete_ticket",  # Отправляем информацию о завершенном билете
            "category_id": worker.category_id,
            "data": TicketOut.from_orm(current_ticket).dict()
        })

    next_ticket = await db.execute(
        select(Ticket).where(Ticket.category_id == worker.category_id,
                             Ticket.status == "wait", Ticket.worker_id == None)
        .order_by(Ticket.created_at.asc())  # Ищем следующий билет в очереди
    )
    next_ticket = next_ticket.scalars().first()
    if next_ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No available tickets")  # Если доступных билетов нет, возвращаем ошибку
    if next_ticket.telegram_id:
        try:
            message = ""
            if next_ticket.language == 'English':
                message = f"It’s your turn! Please proceed to window number {worker.window}."
            elif next_ticket.language == 'Қазақ':
                message = f"Кезегіңіз келді! Өтінеміз, {worker.window} терезесіне өтіңіз."
            elif next_ticket.language == 'Русский':
                message = f"Ваше время пришло! Пожалуйста, подойдите к окну номер {worker.window}."
            else:
                message = f"Ваше время пришло! Пожалуйста, подойдите к окну номер {worker.window}."
            await dp.bot.send_message(next_ticket.telegram_id, message)
        except Exception as e:
            print(f"Error: {e}")
    next_ticket.status = "invited"
    next_ticket.worker_id = worker.id

    next_ticket.start_time = now
    db.add(next_ticket)
    await db.commit()
    await db.refresh(next_ticket)
    category = await db.execute(select(Category).where(Category.id == next_ticket.category_id))
    category = category.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found") 

    await manager.broadcast({
        "action": "next_ticket", 
        "category_id": worker.category_id,
        "data": {"ticket": TicketOut.from_orm(next_ticket).dict(), "window": worker.window}
    })
    return CurrentTicketWorker(  # Возвращаем информацию о следующем билете
        ticket_data=TicketOut.from_orm(next_ticket),
        ticket_id=next_ticket.id,
        ticket_number=int(next_ticket.number),
        category_name=category.name,
        ticket_created_time=next_ticket.created_at.strftime("%d.%m.%Y %H:%M"),
        ticket_language=next_ticket.language,
        ticket_full_name=next_ticket.full_name,
        ticket_phone_number=next_ticket.phone_number
    )


@router.get("/{category_id}/average_rating", response_model=float)
async def get_average_rating(category_id: int, db: AsyncSession = Depends(get_async_session)):
    query = select(func.avg(Ticket.rate).label("average_rating")).filter(Ticket.category_id == category_id)
    result = await db.execute(query)
    average_rating = result.fetchone()
    
    if average_rating is None or average_rating[0] is None:
        raise HTTPException(status_code=404, detail="Category not found or no ratings available")

    return round(average_rating[0], 1)
