import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import  get_db, Company, PromoCode, init_db
from utility import hash_password, create_access_token, verify_password, verify_token
from models import CompanyCreate, AuthRequest, PromoCodeCreate
import uvicorn
import os

init_db()
app = FastAPI(root_path="/api")


@app.get("/ping")
def send():
    return {"status": "PROOOOOOOOOOOOOOOOOD"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        ctx = error.get("ctx", {})
        errors.append({
            "type": error["type"],
            "loc": error["loc"],
            "msg": error["msg"],
            "input": error.get("input", None),
            "ctx": {key: str(value) for key, value in ctx.items()}
        })

    return JSONResponse(
        status_code=400,
        content={"detail": errors}
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

@app.post("/business/auth/sign-up")
async def sign_up(data: CompanyCreate, db: Session = Depends(get_db)):
    try:
        logger.info("Получен запрос на регистрацию: %s", data.email)

        existing_user = db.query(Company).filter(Company.email == data.email).first()
        if existing_user:
            logger.warning("Email уже зарегистрирован: %s", data.email)
            raise HTTPException(status_code=409, detail="Такой email уже зарегистрирован")

        hashed_password = hash_password(data.password)
        logger.info("Пароль успешно хэширован для: %s", data.email)

        new_company = Company(
            name=data.name,
            email=data.email,
            password=hashed_password
        )
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        logger.info("Компания успешно зарегистрирована: %s", new_company.id)

        return {"message": "Successfully signed up"}

    except HTTPException as http_exc:
        logger.error("Ошибка HTTP: %s", str(http_exc.detail))
        raise http_exc
    except Exception as e:
        logger.error("Внутренняя ошибка сервера: %s", str(e))
        raise HTTPException(status_code=500, detail="Произошла ошибка на сервере")

@app.post("/business/auth/sign-in", response_model=dict)
def auth_company(auth_request: AuthRequest, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.email == auth_request.email).first()
    if not company or not verify_password(auth_request.password, company.password):
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль"
        )

    access_token = create_access_token({"sub": auth_request.email})

    company.last_login = datetime.now(timezone.utc)
    company.token = access_token
    db.commit()

    return {
        "token": access_token,
        "company_id": str(company.id)
    }


@app.post("/business/promo", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_promo_code(
    promo: PromoCodeCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    print("Полученный токен:", token)

    current_company_email = token.get("sub")
    print("Email компании из токена:", current_company_email)

    current_company = db.query(Company).filter(Company.email == current_company_email).first()
    if not current_company:
        print("Компания не найдена")
        raise HTTPException(status_code=401, detail=f"Компания с email '{current_company_email}' не найдена")

    print("Компания найдена:", current_company)

    new_promo = PromoCode(
        company_id=current_company.id,
        mode=promo.mode,
        promo_common=promo.promo_common,
        promo_unique=promo.promo_unique,
        description=promo.description,
        image_url=promo.image_url,
        target=promo.target,
        max_count=promo.max_count,
        active_from=promo.active_from,
        active_until=promo.active_until,
    )
    db.add(new_promo)
    db.commit()
    db.refresh(new_promo)

    return {"id": str(new_promo.id)}


@app.get("/business/promo", response_model=list, status_code=status.HTTP_200_OK)
def get_promo_codes(
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    current_company_email = token.get("sub")
    if not current_company_email:
        raise HTTPException(status_code=401, detail="Поле 'sub' отсутствует в токене")

    current_company = db.query(Company).filter(Company.email == current_company_email).first()
    if not current_company:
        raise HTTPException(status_code=401, detail=f"Компания с email '{current_company_email}' не найдена")

    promo_codes = (
        db.query(PromoCode)
        .filter(PromoCode.company_id == current_company.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(promo.id),
            "mode": promo.mode,
            "promo_common": promo.promo_common,
            "promo_unique": promo.promo_unique,
            "description": promo.description,
            "image_url": promo.image_url,
            "target": promo.target,
            "max_count": promo.max_count,
            "active_from": promo.active_from,
            "active_until": promo.active_until,
            "created_at": promo.created_at,
            "active": promo.active
        }
        for promo in promo_codes
    ]


@app.get("/business/promo/{id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_promo_by_id(
    id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    current_company_email = token.get("sub")
    if not current_company_email:
        raise HTTPException(status_code=401, detail="Поле 'sub' отсутствует в токене")

    current_company = db.query(Company).filter(Company.email == current_company_email).first()
    if not current_company:
        raise HTTPException(status_code=401, detail=f"Компания с email '{current_company_email}' не найдена")

    promo = db.query(PromoCode).filter(PromoCode.id == id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    if promo.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Промокод не принадлежит этой компании")

    return {
        "promo_id": str(promo.id),
        "company_id": str(promo.company_id),
        "company_name": current_company.email,
        "like_count": promo.like_count,
        "used_count": promo.used_count,
        "active": promo.active,
        "mode": promo.mode,
        "promo_common": promo.promo_common,
        "promo_unique": promo.promo_unique,
        "description": promo.description,
        "image_url": promo.image_url,
        "target": promo.target,
        "max_count": promo.max_count,
        "active_from": promo.active_from,
        "active_until": promo.active_until,
    }

@app.patch("/business/promo/{id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_promo_code(
    id: str,
    promo_data: dict = Body(...),
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    current_company_email = token.get("sub")
    if not current_company_email:
        raise HTTPException(status_code=401, detail="Поле 'sub' отсутствует в токене")

    current_company = db.query(Company).filter(Company.email == current_company_email).first()
    if not current_company:
        raise HTTPException(status_code=401, detail=f"Компания с email '{current_company_email}' не найдена")

    promo = db.query(PromoCode).filter(PromoCode.id == id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    if promo.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Промокод не принадлежит этой компании")

    try:
        for key, value in promo_data.items():
            if hasattr(promo, key):
                setattr(promo, key, value)

        if promo.used_count > promo.max_count:
            raise HTTPException(status_code=400, detail="Текущее количество активаций превышает max_count")

        db.commit()
        db.refresh(promo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "promo_id": str(promo.id),
        "company_id": str(promo.company_id),
        "company_name": current_company.email,
        "like_count": promo.like_count,
        "used_count": promo.used_count,
        "active": promo.active,
        "mode": promo.mode,
        "promo_common": promo.promo_common,
        "promo_unique": promo.promo_unique,
        "description": promo.description,
        "image_url": promo.image_url,
        "target": promo.target,
        "max_count": promo.max_count,
        "active_from": promo.active_from,
        "active_until": promo.active_until,
    }

@app.get("/business/promo/{id}/stat", response_model=dict, status_code=status.HTTP_200_OK)
def get_promo_stats(
    id: str = Path(..., description="Уникальный идентификатор промокода"),
    db: Session = Depends(get_db),
    token: dict = Depends(verify_token)
):
    current_company_email = token.get("sub")
    if not current_company_email:
        raise HTTPException(status_code=401, detail="Поле 'sub' отсутствует в токене")

    current_company = db.query(Company).filter(Company.email == current_company_email).first()
    if not current_company:
        raise HTTPException(status_code=401, detail=f"Компания с email '{current_company_email}' не найдена")

    promo = db.query(PromoCode).filter(PromoCode.id == id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    if promo.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Промокод не принадлежит этой компании")

    stats = promo.target.get("countries", [])
    country_stats = [
        {"country": country, "activations_count": promo.used_count} for country in stats
    ]

    return {
        "activations_count": promo.used_count,
        "countries": country_stats
    }


if __name__ == "__main__":
    server_address = os.getenv("SERVER_ADDRESS", "0.0.0.0:8080")
    host, port = server_address.split(":")
    uvicorn.run(app, host=host, port=int(port))
