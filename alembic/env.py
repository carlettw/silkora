import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import Base
from app.models import *  # noqa: F401,F403  -- barcha modellarni metadata'ga ro'yxatdan o'tkazish uchun

config = context.config
# Migratsiyalar uchun DIRECT_URL (session/direct pooler) ishlatiladi - pgbouncer transaction
# rejimidagi DATABASE_URL orqali DDL (CREATE TABLE va h.k.) ishonchli ishlamasligi mumkin.
migration_url = settings.DIRECT_URL or settings.DATABASE_URL
# ConfigParser '%' belgisini interpolatsiya sifatida talqin qiladi (masalan URL-encode qilingan
# parolda %2F bo'lsa xato beradi) - shuning uchun '%' ni '%%' qilib escape qilamiz.
config.set_main_option("sqlalchemy.url", migration_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
