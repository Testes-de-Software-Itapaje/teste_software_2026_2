from backend.exceptions.excecoes import NomeInvalidoError

class Produto:
    """Entidade de domínio que valida os atributos do produto."""

    def __init__(self, nome:str, preco:float, quant_estoque:int,validade:str, codigo_barras:str,categoria:str, peso:float):
        """Cria um Produto com validação em cada atributo."""
        self._nome = self.valida_nome(nome)
        self._preco = self.valida_preco(preco)
        self._quant_estoque = self.valida_quant_estoque(quant_estoque)
        self._validade = self.valida_validade(validade)
        self._codigo_barras = self.valida_codigo_barras(codigo_barras)
        self._categoria = self.valida_categoria(categoria)
        self._peso = self.valida_peso(peso)

    def valida_nome(self, nome):
        """Valida o nome do produto."""
        if nome == "" or nome is None:
            raise NomeInvalidoError("Nome não pode ser vazio")
        return nome

    def valida_preco(self, preco):
        """Valida o preço do produto."""
        if preco is None:
            raise ValueError("Preço não pode ser vazio")
        return preco

    def valida_quant_estoque(self, quant_estoque):
        """Valida a quantidade em estoque."""
        if quant_estoque is None:
            raise ValueError("Quantidade em estoque não pode ser vazia")
        return quant_estoque

    def valida_validade(self, validade):
        """Valida o campo de validade do produto."""
        if validade is None:
            raise ValueError("Validade não pode ser vazia")
        return validade

    def valida_codigo_barras(self, codigo_barras):
        """Valida o código de barras."""
        if codigo_barras is None:
            raise ValueError("Código de barras não pode ser vazio")
        return codigo_barras

    def valida_categoria(self, categoria):
        """Valida a categoria do produto."""
        if categoria == "" or categoria is None:
            raise ValueError("Categoria não pode ser vazia")
        return categoria

    def valida_peso(self, peso):
        """Valida o peso do produto."""
        if peso is None:
            raise ValueError("Peso não pode ser vazio")
        return peso

    @property
    def nome(self):
        """Retorna o nome do produto."""
        return self._nome

    @nome.setter
    def nome(self, nome):
        """Atualiza o nome do produto após validação."""
        self._nome = self.valida_nome(nome)

    @property
    def preco(self):
        """Retorna o preço do produto."""
        return self._preco

    @preco.setter
    def preco(self, preco):
        """Atualiza o preço do produto após validação."""
        self._preco = self.valida_preco(preco)

    @property
    def quant_estoque(self):
        """Retorna a quantidade em estoque."""
        return self._quant_estoque

    @quant_estoque.setter
    def quant_estoque(self, quant_estoque):
        """Atualiza a quantidade em estoque após validação."""
        self._quant_estoque = self.valida_quant_estoque(quant_estoque)

    @property
    def validade(self):
        """Retorna o campo de validade do produto."""
        return self._validade

    @validade.setter
    def validade(self, validade):
        """Atualiza o campo de validade do produto após validação."""
        self._validade = self.valida_validade(validade)

    @property
    def codigo_barras(self):
        """Retorna o código de barras."""
        return self._codigo_barras

    @codigo_barras.setter
    def codigo_barras(self, codigo_barras):
        """Atualiza o código de barras após validação."""
        self._codigo_barras = self.valida_codigo_barras(codigo_barras)

    @property
    def categoria(self):
        """Retorna a categoria do produto."""
        return self._categoria

    @categoria.setter
    def categoria(self, categoria):
        """Atualiza a categoria do produto após validação."""
        self._categoria = self.valida_categoria(categoria)

    @property
    def peso(self):
        """Retorna o peso do produto."""
        return self._peso

    @peso.setter
    def peso(self, peso):
        """Atualiza o peso do produto após validação."""
        self._peso = self.valida_peso(peso)
