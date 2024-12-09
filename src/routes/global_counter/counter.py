from src.routes.ticket.models import Ticket
from src.database import get_async_session
from src.routes.global_counter.models import Counter
from src.routes.global_counter.schemas import CounterOut
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.future import select
from sqlalchemy import delete


# Function to get the current counter
async def get_current_counter(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Counter))  # Await the query execution
    counter: Counter = result.scalars().first()  # Use scalars().first() to get the result
    return counter.current_counter if counter else None

# Function to increment the counter
async def increment_counter(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Counter))  # Await the query execution
    counter: Counter = result.scalars().first()

    if not counter:
        counter = Counter(id=1)
        db.add(counter)

    counter.current_counter += 1
    await db.commit()
    
    return counter.current_counter

async def nullify_counter(db: AsyncSession = Depends(get_async_session)):
    delete_query = delete(Ticket).where(Ticket.status == 'wait')
    await db.execute(delete_query)
    
    await db.commit()
    
    result = await db.execute(select(Counter))
    counter: Counter = result.scalars().first()

    if not counter:
        counter = Counter(id=1)
        db.add(counter)

    counter.current_counter = 0
    await db.commit()
    
    return True