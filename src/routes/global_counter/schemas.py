from pydantic import BaseModel


class CounterOut(BaseModel):
    current_counter: int