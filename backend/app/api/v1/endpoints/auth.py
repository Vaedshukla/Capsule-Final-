from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token, get_password_hash
from pydantic import BaseModel, EmailStr

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }

@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    db_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return {
        "access_token": create_access_token(db_user.id),
        "token_type": "bearer",
    }
