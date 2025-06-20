from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Responsavel pela sessão do banco de dados para uso em requisições FastAPI.

    Esta função é utilizada como dependência para sessão (Session)
    nas rotas e serviços, garantindo que não fique presa no database.

    :yield: Sessão de banco de dados (SQLAlchemy Session).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
