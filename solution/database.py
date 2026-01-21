import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DATABASE", "prod")
DB_USER = os.getenv("POSTGRES_USERNAME", "prod")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "prod")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    last_login = Column(DateTime, nullable=True)
    token = Column(String, nullable=True)

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, email={self.email})>"


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    mode = Column(String, nullable=False)
    promo_common = Column(String, nullable=True)
    promo_unique = Column(UUID(as_uuid=True), nullable=True)  # Пример использования UUID для уникальных промокодов
    description = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    target = Column(String, nullable=False)  # Можно использовать JSON или String для хранения целей
    max_count = Column(Integer, nullable=False)
    active_from = Column(DateTime, nullable=False)
    active_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    active = Column(Boolean, default=True)
    like_count = Column(Integer, default=0, nullable=True)
    used_count = Column(Integer, default=0, nullable=True)

    def __repr__(self):
        return f"<PromoCode(id={self.id}, company_id={self.company_id}, description={self.description})>"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
