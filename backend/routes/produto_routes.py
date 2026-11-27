from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Literal

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from db.database import get_db, normalizar_busca
from entity.produto_model import ProdutoCreate, ProdutoPagina, ProdutoRead
from db.produto_schema import ProdutoDB


router = APIRouter(
    prefix="/produto",
    tags=["Produtos"]
)


@router.post("/criar", response_model=ProdutoRead)
def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db)
):
    """Persiste um novo produto no banco de dados."""

    produto_db = ProdutoDB(**produto.model_dump())

    db.add(produto_db)
    db.commit()
    db.refresh(produto_db)

    return produto_db


def _expressao_ordenacao(campo: str):
    """Expressão SQL usada para ordenar a tabela pelo campo escolhido."""
    if campo == "validade":
        valor = ProdutoDB.validade
        # dd/mm/aaaa vira aaaammdd; textos livres ("3 meses") vão para o fim.
        return case(
            (
                valor.op("GLOB")("[0-3][0-9]/[0-1][0-9]/[0-9][0-9][0-9][0-9]"),
                func.substr(valor, 7, 4) + func.substr(valor, 4, 2) + func.substr(valor, 1, 2),
            ),
            else_="z" + func.normalizar_busca(valor),
        )
    if campo in ("nome", "categoria", "codigo_barras"):
        return func.normalizar_busca(getattr(ProdutoDB, campo))
    return getattr(ProdutoDB, campo)


@router.get("/pagina", response_model=ProdutoPagina)
def listar_pagina_produtos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(10, ge=1, le=100),
    ordenar_por: Literal[
        "nome", "preco", "quant_estoque", "validade",
        "codigo_barras", "categoria", "peso"
    ] = Query("nome"),
    ordem: Literal["asc", "desc"] = Query("asc"),
    busca: str = Query("", max_length=200),
    db: Session = Depends(get_db)
):
    consulta = db.query(ProdutoDB)
    termo = normalizar_busca(busca.strip())
    if termo:
        consulta = consulta.filter(or_(
            func.instr(func.normalizar_busca(ProdutoDB.nome), termo) > 0,
            func.instr(func.normalizar_busca(ProdutoDB.codigo_barras), termo) > 0,
            func.instr(func.normalizar_busca(ProdutoDB.categoria), termo) > 0,
        ))

    total = consulta.count()
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    pagina = min(pagina, total_paginas)
    itens = (
        consulta.order_by(
            _expressao_ordenacao(ordenar_por).asc() if ordem == "asc"
            else _expressao_ordenacao(ordenar_por).desc(),
            ProdutoDB.id,
        )
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )
    return ProdutoPagina(
        itens=itens, pagina=pagina, total_paginas=total_paginas, total=total
    )


@router.get("/{produto_id}", response_model=ProdutoRead)
def buscar_produto(
    produto_id: int,
    db: Session = Depends(get_db)
):
    """Recupera um produto pelo ID."""

    produto = (
        db.query(ProdutoDB)
        .filter(ProdutoDB.id == produto_id)
        .first()
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    return produto


@router.get("", response_model=list[ProdutoRead])
def listar_produtos(
    db: Session = Depends(get_db)
):
    """Lista todos os produtos armazenados."""

    return db.query(ProdutoDB).all()


@router.put("/{produto_id}", response_model=ProdutoRead)
def atualizar_produto(
    produto_id: int,
    produto: ProdutoCreate,
    db: Session = Depends(get_db)
):
    """Atualiza um produto existente."""

    produto_db = (
        db.query(ProdutoDB)
        .filter(ProdutoDB.id == produto_id)
        .first()
    )

    if produto_db is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    for campo, valor in produto.model_dump().items():
        setattr(produto_db, campo, valor)

    db.commit()
    db.refresh(produto_db)

    return produto_db


@router.delete("/{produto_id}")
def deletar_produto(
    produto_id: int,
    db: Session = Depends(get_db)
):
    """Remove um produto do banco de dados."""

    produto = (
        db.query(ProdutoDB)
        .filter(ProdutoDB.id == produto_id)
        .first()
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    db.delete(produto)
    db.commit()

    return {"detail": "Produto removido"}