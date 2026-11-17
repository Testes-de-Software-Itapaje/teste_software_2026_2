from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db.produto_schema import ProdutoDB
from db.venda_schema import VendaDB
from entity.venda_model import VendaCreate, VendaHistorico, VendaRead


router = APIRouter(
    prefix="/venda",
    tags=["Vendas"]
)


@router.post("", response_model=VendaRead)
def realizar_venda(
    venda: VendaCreate,
    db: Session = Depends(get_db)
):
    produto = (
        db.query(ProdutoDB)
        .filter(ProdutoDB.id == venda.produto_id)
        .first()
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    if produto.quant_estoque < venda.quantidade:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Estoque insuficiente. "
                f"Disponível: {produto.quant_estoque}; "
                f"solicitado: {venda.quantidade}."
            )
        )

    preco_unitario = produto.preco

    valor_total = round(
        preco_unitario * venda.quantidade,
        2
    )

    produto.quant_estoque -= venda.quantidade

    venda_db = VendaDB(
        produto_id=produto.id,
        quantidade=venda.quantidade,
        preco_unitario=preco_unitario,
        valor_total=valor_total
    )

    try:
        db.add(venda_db)

        db.commit()

        db.refresh(venda_db)
        db.refresh(produto)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Não foi possível registrar a venda."
        )

    return VendaRead(
        id=venda_db.id,
        produto_id=produto.id,
        produto_nome=produto.nome,
        quantidade=venda_db.quantidade,
        preco_unitario=venda_db.preco_unitario,
        valor_total=venda_db.valor_total,
        estoque_restante=produto.quant_estoque,
        data_venda=venda_db.data_venda
    )


@router.get("", response_model=list[VendaHistorico])
def listar_vendas(
    db: Session = Depends(get_db)
):
    return (
        db.query(VendaDB)
        .order_by(VendaDB.id.desc())
        .all()
    )