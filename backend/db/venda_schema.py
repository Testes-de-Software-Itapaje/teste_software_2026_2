from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer

from db.database import Base


class VendaDB(Base):
    """Modelo ORM da tabela de vendas."""

    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)

    produto_id = Column(
        Integer,
        ForeignKey("produtos.id"),
        nullable=False,
        index=True
    )

    quantidade = Column(Integer, nullable=False)

    preco_unitario = Column(Float, nullable=False)

    valor_total = Column(Float, nullable=False)

    data_venda = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )