
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, text, LargeBinary, BigInteger
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


class InputFile(Base):
    __tablename__ = "input_files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String)
    file_size = Column(BigInteger)
    file_data = Column(LargeBinary, nullable=False)  # BYTEA in PostgreSQL
    uploaded_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    uploaded_by = Column(String, default="default_user")
    status = Column(String, default="uploaded")


class OutputFile(Base):
    __tablename__ = "output_files"

    id = Column(Integer, primary_key=True, index=True)
    input_file_id = Column(Integer, nullable=True, index=True)  # Reference to input file
    original_filename = Column(String, nullable=False)
    mime_type = Column(String)
    file_size = Column(BigInteger)
    file_data = Column(LargeBinary, nullable=False)  # BYTEA in PostgreSQL
    records_generated = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    status = Column(String, default="generated")