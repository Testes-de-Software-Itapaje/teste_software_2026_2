import unicodedata

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "sqlite:///./produtos.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def normalizar_busca(texto: str) -> str:
    return "".join(
        letra for letra in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(letra)
    )


@event.listens_for(engine, "connect")
def configurar_busca_sqlite(conexao, _registro):
    conexao.create_function("normalizar_busca", 1, normalizar_busca, deterministic=True)


def get_db():
    """Fornece uma sessão SQLAlchemy e a fecha após a requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()