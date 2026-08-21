from excecoes import NomeInvalidoError

class Produto:

    def __init__(self, nome, preco, quant_estoque,validade, codigo_barras,categoria, peso):
        self._nome = self.valida_nome(nome)
        self._preco = preco
        self._quant_estoque = quant_estoque
        self._validade = validade
        self._codigo_barras = codigo_barras
        self._categoria = categoria
        self._peso = peso

    def valida_nome(self, nome):
        if nome == "" or nome is None:
            raise NomeInvalidoError("Nome não pode ser vazio")
        return nome
