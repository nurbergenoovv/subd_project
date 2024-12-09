#!/usr/bin/env python3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime as dt

import sys
import os
import uvicorn

sys.path.append(os.path.join(sys.path[0], '../'))
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.routes.setting.models import Settings
from src.routes.interface.router import router as interface_router
from src.routes.setting.router import router as setting_router
from src.routes.ticket.router import router as ticket_router
from src.routes.category.router import router as category_router
from src.routes.websocket.router import router as websocket_router
from src.routes.auth.router import router as auth_router
import logging


logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Queue APP")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(category_router)
app.include_router(ticket_router)
app.include_router(interface_router)
app.include_router(setting_router)

if __name__ == "__main__":
    logging.info("Starting application...")
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True, workers=3)
