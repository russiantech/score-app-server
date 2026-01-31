from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_app_config

app_config = get_app_config()

engine = create_engine(app_config.database_config.sql_connection_string, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

