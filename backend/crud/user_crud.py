from sqlalchemy.orm import Session
from backend.schemas.sql.user import User
from backend.core.security import hash_password
from backend.schemas.sql.user import UserCreate

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db : Session, id : int):
    return db.query(User).filter(User.id == id).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_pw = hash_password(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        name=user_in.name,
        company_id=user_in.company_id,
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user