from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VendaCreate(BaseModel):
    produto_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)


class VendaRead(BaseModel):
    id: int
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float
    valor_total: float
    estoque_restante: int
    data_venda: datetime


class VendaHistorico(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: float
    valor_total: float
    data_venda: datetime

    model_config = ConfigDict(from_attributes=True)