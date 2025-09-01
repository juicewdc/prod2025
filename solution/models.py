from cfg import pwd_context
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

class AuthRequest(BaseModel):
    email: str
    password: str

class CompanyCreate(BaseModel):
    name: str =Field(..., min_length=5, max_length=50)
    email: str =Field(...,min_length=8, max_length=120)
    password: str =Field(..., min_length=8, max_length=60)

    @validator("password")
    def validate_password(cls, value):
        if not any(char.islower() for char in value):
            raise ValueError("Нужен нижний регистр")
        if not any(char.isupper() for char in value):
            raise ValueError("Нужен верхний регистр")
        if not any(char.isdigit() for char in value):
            raise ValueError("Нужна хотя бы одна цифра")
        if not any(char in "@$!%*?&" for char in value):
            raise ValueError("Нужен хотя бы один специальный символ")
        return value

class Token(BaseModel):
    access_token: str
    token_type: str


class PromoCodeCreate(BaseModel):
    mode: str = Field(..., description="Режим промокода: COMMON или UNIQUE")
    promo_common: Optional[str] = Field(None, max_length=30, description="Общий промокод для режима COMMON")
    promo_unique: Optional[list[str]] = Field(None, description="Уникальные промокоды для режима UNIQUE")
    description: str = Field(..., min_length=10, max_length=300, description="Описание промокода")
    image_url: Optional[str] = Field(None, max_length=350, description="Ссылка на изображение")
    target: dict[str, Any] = Field(..., description="Целевая аудитория")
    max_count: int = Field(..., description="Максимальное количество использования")
    active_from: Optional[datetime] = Field(None, description="Дата начала действия")
    active_until: Optional[datetime] = Field(None, description="Дата окончания действия")
    like_count: Optional[int] = Field(0, description="Количество лайков", example=0)
    used_count: Optional[int] = Field(0, description="Количество использований", example=0)

    @validator("active_from", "active_until", pre=True)
    def parse_date(cls, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Дата должна быть в формате YYYY-MM-DD")

    @validator("mode")
    def validate_mode(cls, value):
        if value not in ["COMMON", "UNIQUE"]:
            raise ValueError("Значение поля 'mode' должно быть 'COMMON' или 'UNIQUE'")
        return value

    @validator("promo_common", always=True)
    def validate_promo_common(cls, value, values):
        if values.get("mode") == "COMMON" and not value:
            raise ValueError("Поле 'promo_common' обязательно для режима COMMON")
        return value

    @validator("promo_unique", always=True)
    def validate_promo_unique(cls, value, values):
        if values.get("mode") == "UNIQUE" and not value:
            raise ValueError("Поле 'promo_unique' обязательно для режима UNIQUE")
        return value




def hash_id(name: str) -> str:
    pwd_context.hash(name)








