class NomeInvalidoError(Exception):
    """Lançada quando o nome do produto está vazio ou inválido."""

    def __init__(self,msg):
        """Armazena a mensagem de erro."""
        self.msg = msg

    def __str__(self):
        """Retorna a mensagem de erro como texto."""
        return self.msg
