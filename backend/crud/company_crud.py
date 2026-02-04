from sqlalchemy.orm import Session
from backend.schemas.sql.company import Company

def get_company_by_id(db: Session, company_id: int):
    return db.query(Company).filter(Company.id == company_id).first()