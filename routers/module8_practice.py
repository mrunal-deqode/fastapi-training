import time
import asyncio

from fastapi import APIRouter

router = APIRouter(prefix="/module8", tags=["Async Operations"])


@router.get("/blocking")
async def demo_operation():
    time.sleep(5)
    return {"message": "Task Completed"}


@router.get("/non-blocking")
async def demo_op():
    await asyncio.sleep(5)
    return {"message": "Non-Blocking task completed"}
