from pydantic import BaseModel, Field, ConfigDict


class ProdutoBase(BaseModel):
    """Modelo Pydantic base para os dados do Produto."""
    nome: str = Field(..., min_length=1)
    preco: float = Field(...)
    quant_estoque: int = Field(...)
    validade: str
    codigo_barras: str
    categoria: str = Field(..., min_length=1)
    peso: float


class ProdutoCreate(ProdutoBase):
    """Modelo Pydantic usado para receber dados do Produto nas requisições."""
    pass


class ProdutoRead(ProdutoBase):
    """Modelo Pydantic usado para retornar dados do Produto pela API."""
    id: int
    model_config = ConfigDict(from_attributes=True)