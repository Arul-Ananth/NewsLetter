from sqlmodel import create_engine, Session, SQLModel
from app.config import settings

# echo=False in production to reduce log noise
engine = create_engine(settings.DATABASE_URL, echo=True)

def get_session():
    """Dependency for injecting DB sessions into routes"""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)