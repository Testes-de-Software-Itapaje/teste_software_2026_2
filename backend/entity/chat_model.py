from pydantic import BaseModel, ConfigDict, Field
from entity.produto_model import ProdutoRead


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    mensagem: str = Field(
        min_length=1,
        description="Mensagem enviada pelo usuário"
    )


class ChatResponse(BaseModel):
    resposta: str


class ProdutoIgnorado(BaseModel):
    item: int
    nome: str | None = None
    motivo: str


class AnexoResponse(BaseModel):
    resposta: str
    criados: list[ProdutoRead]
    ignorados: list[ProdutoIgnorado]
