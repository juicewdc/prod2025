import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# 1) Добавляем корень проекта в PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # /app
sys.path.insert(0, BASE_DIR)

# 2) Подхватываем .env (если он лежит в корне /app)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 3) Импортируем Base и модели (чтобы metadata знала таблицы)
from database import Base
import models  # важно, чтобы модели зарегистрировались в Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4) Берём URL из env и подсовываем Alembic'у
def get_url() -> str:
    user = os.getenv("POSTGRES_USERNAME", "prod")
    pwd  = os.getenv("POSTGRES_PASSWORD", "prod")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DATABASE", "prod")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

config.set_main_option("sqlalchemy.url", get_url())

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
