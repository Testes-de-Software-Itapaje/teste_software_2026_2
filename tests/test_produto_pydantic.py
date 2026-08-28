import pytest
from pydantic import ValidationError

from entity.produto_model import ProdutoCreate, ProdutoRead


def test_produto_create_com_dados_validos():
    """Garante que o modelo Pydantic aceita um produto válido."""
    produto = ProdutoCreate(
        nome="Notebook",
        preco=4999.99,
        quant_estoque=10,
        validade="2026-12-31",
        codigo_barras="7891234567890",
        categoria="eletronicos",
        peso=2.5,
    )

    assert produto.nome == "Notebook"
    assert produto.preco == 4999.99
    assert produto.quant_estoque == 10
    assert produto.validade == "2026-12-31"
    assert produto.codigo_barras == "7891234567890"
    assert produto.categoria == "eletronicos"
    assert produto.peso == 2.5


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("nome", ""),
        ("categoria", ""),
    ],
)
def test_produto_create_rejeita_campos_vazios(campo, valor):
    """Garante que campos obrigatórios não aceitarem valores vazios."""
    payload = {
        "nome": "Notebook",
        "preco": 4999.99,
        "quant_estoque": 10,
        "validade": "2026-12-31",
        "codigo_barras": "7891234567890",
        "categoria": "eletronicos",
        "peso": 2.5,
    }
    payload[campo] = valor

    with pytest.raises(ValidationError):
        ProdutoCreate(**payload)


def test_produto_read_exige_id():
    """Garante que a leitura do produto exige o identificador."""
    payload = {
        "nome": "Notebook",
        "preco": 4999.99,
        "quant_estoque": 10,
        "validade": "2026-12-31",
        "codigo_barras": "7891234567890",
        "categoria": "eletronicos",
        "peso": 2.5,
    }

    with pytest.raises(ValidationError):
        ProdutoRead(**payload)


def test_produto_read_com_id_valido():
    """Garante que o modelo de leitura aceita um produto completo."""
    produto = ProdutoRead(
        id=1,
        nome="Notebook",
        preco=4999.99,
        quant_estoque=10,
        validade="2026-12-31",
        codigo_barras="7891234567890",
        categoria="eletronicos",
        peso=2.5,
    )

    assert produto.id == 1
    assert produto.codigo_barras == "7891234567890"
