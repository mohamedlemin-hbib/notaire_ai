from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models so Alembic can see them
from app.db.models import User, Document
