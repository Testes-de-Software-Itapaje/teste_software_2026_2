from sqlalchemy import Column, Integer, String, Float
from db.database import Base


class ProdutoDB(Base):
    """Modelo ORM do SQLAlchemy mapeado para a tabela produtos."""
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    quant_estoque = Column(Integer, nullable=False)
    validade = Column(String, nullable=False)
    codigo_barras = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    peso = Column(Float, nullable=False)
