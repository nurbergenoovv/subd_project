import json
from typing import Any, Optional

from pydantic import BaseModel

from src.routes.auth.schemas import UserOut
from src.routes.ticket.schemas import TicketOut


class ReturnMessage(BaseModel):
    status: str
    message: str


class SendToWebsocket:
    def __init__(self, command, to, data):
        self.command: str = command
        self.to: int = to
        self.data: Any = data

    def to_json(self):
        message = {
            "command": self.command,
            "to": self.to,
            "data": self.data
        }
        return json.dumps(message)


class WorkerInformation(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    queue: int


class ResponseQueue(BaseModel):
    worker_id: int
    ticket_id: int
    queue: int


class ResponseTicket(BaseModel):
    ticket_id: int
    ticket_number: int
    front_queue: int
    current_ticket: Optional[int]
    ticket_created_time: str
    category_id: int
    average_duration: Optional[float]

class Personal_data(BaseModel):
    user: UserOut
    accepted_today: int
    skipped_today: int
    served_today: int

class General_data(BaseModel):
    clients_in_queue: int
    accepted_today: int
    served_today: int

class CurrentTicketWorker(BaseModel):
    ticket_data: TicketOut
    ticket_id: int
    ticket_number: int
    category_name: str
    ticket_created_time: str
    ticket_language: str
    ticket_full_name: str
    ticket_phone_number: str



class Dashboard(BaseModel):
    category_name: str
    personal_data: Personal_data
    general_data: General_data
    current_ticket: Optional[CurrentTicketWorker]


class QueueResponse(BaseModel):
    queue: int

class CategoryResponse(BaseModel):
    id: int
    name: str
    users: list[UserOut]


class AdminDashboard(BaseModel):
    general_data: General_data
    user: UserOut
    categories: list[CategoryResponse]

class AdminRequest(BaseModel):
    token: str

class Statistic(BaseModel):
    category_name: str
    accepted_today: int
    cancelled_today: int
    passed_today: int
    serviced_today: int
    serviced_all_time: int
    accepted_all_time: int

class StatisticResponse(BaseModel):
    general_data: Statistic # category name maybe null or ''
    categories: list[Statistic]
    today: str