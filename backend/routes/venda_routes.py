from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.database import get_db
from db.produto_schema import ProdutoDB
from db.venda_schema import VendaDB
from entity.venda_model import VendaCreate, VendaHistorico, VendaLoteCreate, VendaRead


router = APIRouter(
    prefix="/venda",
    tags=["Vendas"]
)


def registrar_vendas(itens: list[VendaCreate], db: Session) -> list[VendaRead]:
    resultados = []

    try:
        with db.begin():
            for item in itens:
                # A atualização e a verificação do estoque acontecem na mesma operação.
                produto = db.execute(
                    update(ProdutoDB)
                    .where(
                        ProdutoDB.id == item.produto_id,
                        ProdutoDB.quant_estoque >= item.quantidade,
                    )
                    .values(quant_estoque=ProdutoDB.quant_estoque - item.quantidade)
                    .returning(ProdutoDB)
                ).scalar_one_or_none()

                if produto is None:
                    produto = db.get(ProdutoDB, item.produto_id)
                    if produto is None:
                        raise HTTPException(404, f"Produto #{item.produto_id} não encontrado.")
                    raise HTTPException(
                        400,
                        f"Estoque insuficiente para {produto.nome}. "
                        f"Disponível: {produto.quant_estoque}. "
                        f"Solicitado: {item.quantidade}."
                    )

                venda = VendaDB(
                    produto_id=produto.id,
                    quantidade=item.quantidade,
                    preco_unitario=produto.preco,
                    valor_total=round(produto.preco * item.quantidade, 2),
                )
                db.add(venda)
                db.flush()

                resultados.append(VendaRead(
                    id=venda.id,
                    produto_id=produto.id,
                    produto_nome=produto.nome,
                    quantidade=venda.quantidade,
                    preco_unitario=venda.preco_unitario,
                    valor_total=venda.valor_total,
                    estoque_restante=produto.quant_estoque,
                    data_venda=venda.data_venda,
                ))
    except SQLAlchemyError as erro:
        raise HTTPException(500, "Não foi possível registrar a venda.") from erro

    return resultados


@router.post("", response_model=VendaRead)
def realizar_venda(venda: VendaCreate, db: Session = Depends(get_db)):
    return registrar_vendas([venda], db)[0]


@router.post("/lote", response_model=list[VendaRead])
def realizar_venda_lote(venda: VendaLoteCreate, db: Session = Depends(get_db)):
    return registrar_vendas(venda.itens, db)


@router.get("", response_model=list[VendaHistorico])
def listar_vendas(
    db: Session = Depends(get_db)
):
    return (
        db.query(VendaDB)
        .order_by(VendaDB.id.desc())
        .all()
    )