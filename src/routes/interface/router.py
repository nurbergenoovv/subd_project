from datetime import datetime
from datetime import date, datetime, timedelta
from typing import List

from aiosmtplib import status
from fastapi import APIRouter, Depends, HTTPException, Request, logger
import pytz
from sqlalchemy import Date, cast, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.routes.auth import auth

from src.routes.auth.models import User
from src.routes.ticket.models import Ticket
from src.routes.category.models import Category

from src.routes.auth.schemas import UserOut
from src.routes.ticket.schemas import TicketFilter, TicketOut
from src.routes.category.schemas import CategoryOutput, CategoryWithQueue
from src.schemas import ResponseTicket, Dashboard, CurrentTicketWorker, General_data, Personal_data, AdminDashboard, \
    CategoryResponse, AdminRequest, StatisticResponse, Statistic

router = APIRouter(
    prefix="/interface",
    tags=["interface"],
)


@router.get("/client/categories", response_model=list[CategoryWithQueue])
async def get_client_categories(db: AsyncSession = Depends(get_async_session)) -> list[CategoryOutput]:
    stmt = await db.execute(select(Category).order_by(Category.name))
    categories = stmt.scalars().all()

    response: list[CategoryOutput] = []

    for category in categories:
        stmt = await db.execute(
            select(Ticket).where(Ticket.category_id ==
                                 category.id, Ticket.status == 'wait')
        )
        tickets = stmt.scalars().all()
        queue = len(tickets)
        response.append(CategoryWithQueue(
            id=category.id, name=category.name, queue=queue))

    return response


@router.get("/client/ticket/{ticket_id}", response_model=ResponseTicket)
async def get_client_ticket(
        ticket_id: int,
        db: AsyncSession = Depends(get_async_session)
) -> ResponseTicket:
    stmt = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket: TicketOut = stmt.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    queue_stmt = await db.execute(
        select(Ticket).where(
            Ticket.category_id == ticket.category_id,
            Ticket.status == "wait",
            Ticket.id < ticket.id  # Replace with created_at comparison
        ).order_by(Ticket.created_at.asc())  # Order by created_at
    )
    front_queue = len(queue_stmt.scalars().all())


    current_ticket_stmt = await db.execute(
        select(Ticket).where(
            Ticket.category_id == ticket.category_id,
            Ticket.status.in_(["invited"])
        ).order_by(Ticket.created_at)
    )
    current_ticket1 = current_ticket_stmt.scalars().first()
    tz = pytz.timezone('Asia/Almaty')
    now = datetime.now(tz).time()
    today = datetime.now(tz).date()

    # completed_tickets_res = await db.execute(
        #   select(Ticket).order_by(Ticket.created_at.asc()).limit(200)
        #   .where(
            #    Ticket.status == 'completed',
            #    Ticket.category_id == ticket.category_id,
                # func.date(Ticket.created_at) == today
            #    )
        #   )
    


    # completed_tickets = completed_tickets_res.scalars().all()
    # average_duration = 0
    # if completed_tickets:
    #     durations = [
    #         (ticket.end_time - ticket.start_time).total_seconds() / 60
    #         for ticket in completed_tickets
    #     ]
    #     average_duration = sum(durations) / len(durations)
   

    ticket_created_time = ticket.created_at.strftime("%d.%m.%Y %H:%M:%S")

    print({
        "ticket_id": ticket.id,
        "ticket_number": ticket.number,
        "front_queue": front_queue,
        "current_ticket": current_ticket1.number if current_ticket1 else None,
        "ticket_created_time": ticket_created_time,
        "category_id": ticket.category_id,
        "average_duration": 0
    })
    response = ResponseTicket(
        ticket_id=ticket.id,
        ticket_number=ticket.number,
        front_queue=front_queue,
        current_ticket=current_ticket1.number if current_ticket1 else None,
        ticket_created_time=ticket_created_time,
        category_id=ticket.category_id,
        average_duration=0
    )

    return response


@router.post("/worker/dashboard", response_model=Dashboard)
async def get_dashboard(
        request: Request,
        db: AsyncSession = Depends(get_async_session)
) -> Dashboard:
    data = await request.json()
    worker_token = data.get("token")
    if not worker_token:
        raise HTTPException(
            status_code=401,
            detail="Unauthenticated",
        )

    worker: UserOut = await auth.get_current_user(db, worker_token)

    category_stmt = await db.execute(select(Category).where(Category.id == worker.category_id))
    category = category_stmt.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    tz = pytz.timezone('Asia/Almaty')
    today = datetime.now(tz).date()

    print(
        f"Worker ID: {worker.id}, Category ID: {worker.category_id}, Today's Date: {today}")

    accepted_today_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.worker_id == worker.id,
            Ticket.status.in_(["invited", "completed", "skipped"]),
            func.date(Ticket.created_at) == today
        )
    )
    accepted_today = accepted_today_result.scalar()
    print(f"Accepted Today: {accepted_today}")

    skipped_today_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.worker_id == worker.id,
            Ticket.status == "skipped",
            func.date(Ticket.created_at) == today
        )
    )
    skipped_today = skipped_today_result.scalar()
    print(f"Skipped Today: {skipped_today}")

    served_today_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.worker_id == worker.id,
            Ticket.status == "completed",
            func.date(Ticket.created_at) == today
        )
    )
    served_today = served_today_result.scalar()
    print(f"Served Today: {served_today}")

    personal_data = Personal_data(
        user=worker,
        accepted_today=accepted_today,
        skipped_today=skipped_today,
        served_today=served_today
    )

    # General Data
    clients_in_queue_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.category_id == worker.category_id,
            Ticket.status == "wait"
        )
    )
    clients_in_queue = clients_in_queue_result.scalar()
    print(f"Clients in Queue: {clients_in_queue}")

    accepted_today_general_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.category_id == worker.category_id,
            Ticket.status.in_(["invited", "completed", "skipped"]),
            func.date(Ticket.created_at) == today
        )
    )
    accepted_today_general = accepted_today_general_result.scalar()
    print(f"Accepted Today General: {accepted_today_general}")

    served_today_general_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.category_id == worker.category_id,
            Ticket.status == "completed",
            func.date(Ticket.created_at) == today
        )
    )
    served_today_general = served_today_general_result.scalar()
    print(f"Served Today General: {served_today_general}")

    general_data = General_data(
        clients_in_queue=clients_in_queue,
        accepted_today=accepted_today_general,
        served_today=served_today_general
    )

    current_ticket_stmt = await db.execute(
        select(Ticket).where(
            Ticket.worker_id == worker.id,
            Ticket.status == "invited"
        )
    )
    current_ticket: TicketOut = current_ticket_stmt.scalars().first()

    current_ticket_worker = None
    if current_ticket:
        current_ticket_worker = CurrentTicketWorker(
            ticket_data=TicketOut.from_orm(current_ticket),
            ticket_id=current_ticket.id,
            ticket_number=current_ticket.number,
            category_name=category.name,
            ticket_created_time=current_ticket.created_at.strftime(
                "%d.%m.%Y %H:%M"),
            ticket_language=current_ticket.language,
            ticket_phone_number=current_ticket.phone_number,
            ticket_full_name=current_ticket.full_name
        )

    dashboard = Dashboard(
        category_name=category.name,
        personal_data=personal_data,
        general_data=general_data,
        current_ticket=current_ticket_worker
    )

    return dashboard


@router.post('/admin', response_model=AdminDashboard)
async def get_interface_admin(
        request: AdminRequest,
        db: AsyncSession = Depends(get_async_session)
) -> AdminDashboard:

    tz = pytz.timezone('Asia/Almaty')
    today = datetime.now(tz).date()
    try:
        user = await auth.get_current_user(db, request.token)

        if not user:
            raise HTTPException(
                status_code=401, detail="Invalid token or user not found")

        user_out = UserOut.from_orm(user)

        clients_in_queue_result = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.status == "wait",
                func.date(Ticket.created_at) == today
            )
        )
        clients_in_queue = clients_in_queue_result.scalar()

        accepted_result = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.status.in_(["invited", "completed", "skipped"]),
                func.date(Ticket.created_at) == today
            )
        )
        accepted_today = accepted_result.scalar()

        served_today_result = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.status.in_(["completed"]),
                func.date(Ticket.created_at) == today
            )
        )
        served_today = served_today_result.scalar()

        general_data = General_data(
            clients_in_queue=clients_in_queue,
            accepted_today=accepted_today,
            served_today=served_today
        )

        categories_result = await db.execute(select(Category))
        categories = categories_result.scalars().all()

        category_responses = []
        for category in categories:
            users_result = await db.execute(select(User).where(User.category_id == category.id))
            users = users_result.scalars().all()
            user_out_list = [UserOut.from_orm(user) for user in users]
            category_responses.append(CategoryResponse(
                id=category.id, name=category.name, users=user_out_list))

        invalied_users_result = await db.execute(select(User).where(User.category_id == None, User.is_admin == False))
        invalied_users = invalied_users_result.scalars().all()
        category_responses.append(CategoryResponse(
            id=0, name='invalied users', users=invalied_users))
        admin_dashboard = AdminDashboard(
            general_data=general_data,
            user=user_out,
            categories=category_responses
        )

        return admin_dashboard

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/admin/user_information/{user_id}')
async def get_user_information(
        user_id: int,
        db: AsyncSession = Depends(get_async_session)
):
    user = await auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail="Invalid id or user not found")

    query = select(Ticket).where(Ticket.worker_id ==
                                 user_id).order_by(desc(Ticket.created_at))

    result = await db.execute(query)
    tickets = result.scalars().all()

    formatted_tickets = []
    for ticket in tickets:
        formatted_ticket = {
            "id": ticket.id,
            "full_name": ticket.full_name,
            "number": ticket.number,
            "phone_number": ticket.phone_number,
            "rate": ticket.rate,
            "language": ticket.language,
            "status": ticket.status,
            "worker_id": ticket.worker_id,
            "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        formatted_tickets.append(formatted_ticket)

    one_month_ago = date.today() - timedelta(days=30)

    accepted_last_month_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.worker_id == user.id,
            Ticket.status.in_(["invited", "completed", "skipped"]),
            func.date(Ticket.created_at) >= one_month_ago
        )
    )
    accepted_last_month = accepted_last_month_result.scalar()

    skipped_last_month_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.worker_id == user.id,
            Ticket.status == "skipped",
            func.date(Ticket.created_at) >= one_month_ago
        )
    )
    skipped_last_month = skipped_last_month_result.scalar()

    served_last_month_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.worker_id == user.id,
            Ticket.status == "completed",
            func.date(Ticket.created_at) >= one_month_ago
        )
    )
    served_last_month = served_last_month_result.scalar()


    avwrage_result = await db.execute(select(func.avg(Ticket.rate).label("average_rate")).where(
        Ticket.worker_id == user_id,
        Ticket.status == "completed",
        Ticket.rate != None
    ))
    average_rate = avwrage_result.scalar()

    av_rate = round(average_rate, 1) if average_rate is not None else 0.0
    
    return {
        "accepted_last_month": accepted_last_month,
        "skipped_last_month": skipped_last_month,
        "average_rate": av_rate,
        "served_last_month": served_last_month,
        "tickets": formatted_tickets,
    }


@router.get('/admin/statistics', response_model=StatisticResponse)
async def get_interface_statistics(db: AsyncSession = Depends(get_async_session)) -> StatisticResponse:
    tz = pytz.timezone('Asia/Almaty')
    today = datetime.now(tz).date()

    general_query = await db.execute(
        select(
            Ticket.status,
            func.count(Ticket.id).label("count")
        ).where(
            func.date(Ticket.created_at) == today
        ).group_by(Ticket.status)
    )
    general_results = general_query.fetchall()

    stats_mapping = {row.status: row.count for row in general_results}
    accepted_today = sum(
        stats_mapping.get(status, 0) for status in ["invited", "completed", "skipped"]
    )
    cancelled_today = stats_mapping.get("cancelled", 0)
    passed_today = stats_mapping.get("skipped", 0)
    serviced_today = stats_mapping.get("completed", 0)

    all_time_query = await db.execute(
        select(
            Ticket.status,
            func.count(Ticket.id).label("count")
        ).group_by(Ticket.status)
    )
    all_time_results = all_time_query.fetchall()

    all_time_mapping = {row.status: row.count for row in all_time_results}
    serviced_all_time = all_time_mapping.get("completed", 0)
    accepted_all_time = sum(
        all_time_mapping.get(status, 0) for status in ["invited", "completed", "skipped"]
    )

    category_query = await db.execute(
        select(
            Category.id,
            Category.name,
            Ticket.status,
            func.count(Ticket.id).label("count")
        ).join(Ticket, Ticket.category_id == Category.id).where(
            func.date(Ticket.created_at) == today
        ).group_by(Category.id, Ticket.status)
    )
    category_results = category_query.fetchall()

    categories = {}
    for row in category_results:
        category = categories.setdefault(row.id, {"name": row.name, "stats": {}})
        category["stats"][row.status] = row.count

    category_stats = []
    for category_id, data in categories.items():
        stats = data["stats"]
        category_stat = Statistic(
            category_name=data["name"],
            accepted_today=sum(stats.get(status, 0) for status in ["invited", "completed", "skipped"]),
            cancelled_today=stats.get("cancelled", 0),
            passed_today=stats.get("skipped", 0),
            serviced_today=stats.get("completed", 0),
            serviced_all_time=0,
            accepted_all_time=0
        )
        category_stats.append(category_stat)

    general_stat = Statistic(
        category_name="General",
        accepted_today=accepted_today,
        cancelled_today=cancelled_today,
        passed_today=passed_today,
        serviced_today=serviced_today,
        serviced_all_time=serviced_all_time,
        accepted_all_time=accepted_all_time
    )

    response = StatisticResponse(
        general_data=general_stat,
        categories=category_stats,
        today=str(today)
    )

    return response



@router.get('/admin/statistics/{worker_id}/{date_filter}/', response_model=List[TicketOut])
async def get_worker_statistics(
    worker_id: int,
    date_filter: str,
    db: AsyncSession = Depends(get_async_session)
):
    tz = pytz.timezone('Asia/Almaty')
    now = datetime.now(tz)
    
    if not date_filter:
        raise HTTPException(status_code=400, detail="Date filter must be provided")

    if date_filter == "1_day":
        date_threshold = now - timedelta(days=1)
    elif date_filter == "1_week":
        date_threshold = now - timedelta(weeks=1)
    elif date_filter == "1_month":
        date_threshold = now - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid date filter")

    date_threshold = date_threshold.replace(tzinfo=None)

    query = select(Ticket).where(
        Ticket.created_at >= date_threshold,
        Ticket.worker_id == worker_id
    )

    result = await db.execute(query)
    tickets = result.scalars().all()

    if not tickets:
        raise HTTPException(status_code=404, detail="No tickets found for the given worker and date filter")

    return tickets