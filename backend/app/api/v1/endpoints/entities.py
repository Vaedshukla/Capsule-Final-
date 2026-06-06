"""
Entity exploration endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from app.db.session import get_db
from app.models.memory_capsule import MemoryCapsule

router = APIRouter()

@router.get("/", response_model=List[str], summary="List all distinct entities")
async def list_entities(db: AsyncSession = Depends(get_db)):
    query = select(func.jsonb_array_elements_text(MemoryCapsule.entities)).distinct().where(MemoryCapsule.entities.isnot(None))
    result = await db.execute(query)
    return result.scalars().all()
