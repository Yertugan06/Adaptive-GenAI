from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_sql_db 
from backend.core.security import (
    verify_password, 
    create_access_token, 
    TokenPayload
)
from backend.crud import user_crud, company_crud
from backend.schemas.sql.user import UserCreate
from backend.api.v1.deps import get_current_user
from backend.schemas.sql.user import User
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# Endpoints

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: Session = Depends(get_sql_db)):
    user = user_crud.get_user_by_email(db, data.email)
    
    if not user or not verify_password(data.password, user.hashed_password): # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = TokenPayload(
        sub=str(user.id),
        company_id=user.company_id, # type: ignore
        role=user.role # type: ignore
    )
    token = create_access_token(payload)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "company_id": user.company_id
        }
    }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: Session = Depends(get_sql_db)):
    if not company_crud.get_company_by_id(db, data.company_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {data.company_id} does not exist"
        )

    if user_crud.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User with this email already exists"
        )

    new_user = user_crud.create_user(db, data)

    return {"message": "User created successfully", "user_id": new_user.id}

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out. Please clear your local tokens."}


@router.get("/me")
async def checking_the_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "company_id": current_user.company_id
    }