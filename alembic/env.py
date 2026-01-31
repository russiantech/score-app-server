
# v3 - Improved Alembic env.py with automatic model loading
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load config.ini
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your metadata automatically
from app.db.base_class import Base
target_metadata = Base.metadata

# 
# Import models to ensure they're registered with Base.metadata
from app.models import import_all_models
import_all_models()

# Optional: Verify models were loaded
print(f"Models loaded. Tables in metadata: {list(Base.metadata.tables.keys())}")
# Load DB URL - try environment first, then config
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    # Import and get config only if needed
    from app.core.config import get_app_config
    app_config = get_app_config()
    DB_URL = app_config.database_config.sql_connection_string

# Still no URL? Then raise error
if not DB_URL:
    raise RuntimeError("DATABASE_URL not found in environment or app config")

config.set_main_option("sqlalchemy.url", DB_URL)

def run_migrations_offline():
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

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
            target_metadata=target_metadata,
            compare_type=True
            )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()