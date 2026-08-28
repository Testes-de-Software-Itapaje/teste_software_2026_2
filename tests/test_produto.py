from entity.produto import Produto
import pytest
from exceptions.excecoes import NomeInvalidoError

def test_criar_produto_com_sucesso():
    """Garante que o Produto seja criado com dados válidos."""
    cafe = Produto("cafe", 18, 50, 3, 1234567890, "alimenticio", 250)
    assert cafe._nome == "cafe"
    assert cafe._preco == 18 and cafe._quant_estoque == 50 and \
        cafe._validade == 3 and cafe._codigo_barras == 1234567890 and \
        cafe._categoria == "alimenticio" and cafe._peso == 250

def test_criar_produto_sem_nome():
    """Garante que o Produto rejeite um nome vazio."""
    with pytest.raises(NomeInvalidoError):
        Produto("", 18, 50, 3, 1234567890, "alimenticio", 250)
