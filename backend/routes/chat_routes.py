from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session

from db.database import get_db
from db.produto_schema import ProdutoDB
from entity.chat_model import ChatRequest, ChatResponse, AnexoResponse
from services.ollama_service import enviar_mensagem
from services.produto_context_service import gerar_contexto_produtos, responder_do_catalogo
from services.importacao_service import (
    ArquivoInvalidoError,
    ler_documento,
    validar_produtos,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("", response_model=ChatResponse)
def conversar(
    chat: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        resposta = responder_do_catalogo(chat.mensagem, db)
        if resposta is not None:
            return ChatResponse(resposta=resposta)

        contexto = gerar_contexto_produtos(chat.mensagem, db)
        db.rollback()
        return ChatResponse(resposta=enviar_mensagem(chat.mensagem, contexto))

    except RuntimeError as erro:
        raise HTTPException(
            status_code=503,
            detail=str(erro)
        )


def pluralizar(quantidade: int, singular: str, plural: str) -> str:
    return f"{quantidade} {singular if quantidade == 1 else plural}"


@router.post("/anexo", response_model=AnexoResponse)
async def importar_anexo(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    conteudo = await arquivo.read()

    try:
        itens = ler_documento(arquivo.filename or "", conteudo)
    except ArquivoInvalidoError as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro))

    if not itens:
        raise HTTPException(
            status_code=422,
            detail="Nenhum produto foi encontrado no documento."
        )

    validos, ignorados = validar_produtos(itens, db)

    criados = [ProdutoDB(**produto.model_dump()) for produto in validos]

    if criados:
        db.add_all(criados)
        db.commit()
        for produto in criados:
            db.refresh(produto)

    resposta = (
        f"Importação de {arquivo.filename} concluída: "
        f"{pluralizar(len(criados), 'produto cadastrado', 'produtos cadastrados')} e "
        f"{pluralizar(len(ignorados), 'ignorado', 'ignorados')}."
    )

    return AnexoResponse(
        resposta=resposta,
        criados=criados,
        ignorados=ignorados
    )