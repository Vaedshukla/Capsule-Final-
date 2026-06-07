import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.conversation import Conversation
from app.schemas.schemas import ConversationOut, MessageOut
from pydantic import BaseModel, ConfigDict
import uuid
from typing import List

router = APIRouter()
logger = structlog.get_logger()

class FullConversationOut(ConversationOut):
    messages: List[MessageOut]

@router.get("/{conversation_id}", response_model=FullConversationOut)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Validate UUID
        if conversation_id == "undefined":
            raise ValueError("undefined")
            
        uid = uuid.UUID(conversation_id)
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == uid)
        )
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Sort messages by position
        conversation.messages.sort(key=lambda x: x.position)
        
        return conversation
        
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid conversation ID")
