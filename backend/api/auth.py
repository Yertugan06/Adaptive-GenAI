from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_sql_db 
from backend.core.security import (
    verify_password, 
    create_access_token, 
    TokenPayload,
    hash_password
)
from backend.schemas.sql.user import User
from pydantic import BaseModel, EmailStr
from backend.schemas.sql.company import Company

router = APIRouter()

#Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_id: int
    role: str = "employee"

#Endpoints    
@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: Session = Depends(get_sql_db)):

    user = db.query(User).filter(User.email == data.email).first()
    
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

    # Generate JWT
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
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {data.company_id} does not exist"
        )

    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User with this email already exists"
        )

    hashed_pw = hash_password(data.password)
    new_user = User(
        email=data.email,
        hashed_password=hashed_pw,
        name=data.name,
        company_id=data.company_id,
        role=data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}