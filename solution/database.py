from os import getenv
from dotenv import load_dotenv
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

load_dotenv()

DATABASE_URL = "postgresql://prod:prod@host.docker.internal:5432/prod"


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    name = Column(String, nullable=False)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    last_login = Column(DateTime, nullable=True)
    token = Column(String, nullable=True)


class PromoCode(Base):
    __tablename__ = "promo_codes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    mode = Column(String, nullable=False)
    promo_common = Column(String, nullable=True)
    promo_unique = Column(JSON, nullable=True)
    description = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    target = Column(JSON, nullable=False)
    max_count = Column(Integer, nullable=False)
    active_from = Column(DateTime, nullable=False)
    active_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    active = Column(Boolean, default=True)
    like_count = Column(Integer, default=0, nullable=True)
    used_count = Column(Integer, default=0, nullable=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
