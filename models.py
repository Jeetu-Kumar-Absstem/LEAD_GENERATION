
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, text
from sqlalchemy.orm import declarative_base
from database import engine

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String)
    domain = Column(String)
    email = Column(String)
    confidence = Column(Float)
    position = Column(String)
    first_name = Column(String)
    last_name = Column(String)

    batch_id = Column(String, index=True)  # ✅ NEW

    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))