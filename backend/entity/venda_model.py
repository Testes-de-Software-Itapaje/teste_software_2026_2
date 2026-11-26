from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VendaCreate(BaseModel):
    produto_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)


class VendaLoteCreate(BaseModel):
    itens: list[VendaCreate] = Field(min_length=1)

    @field_validator("itens")
    @classmethod
    def validar_produtos_distintos(cls, itens: list[VendaCreate]) -> list[VendaCreate]:
        if len({item.produto_id for item in itens}) != len(itens):
            raise ValueError("Cada produto deve aparecer apenas uma vez na venda.")
        return itens


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