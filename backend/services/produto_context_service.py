import json
import re

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from db.database import normalizar_busca
from db.produto_schema import ProdutoDB


LIMITE_CONTEXTO = 20
SUFIXO_CATALOGO = r"(?: no (?:sistema|catalogo)| do catalogo)?"
ATRIBUTOS = {
    "preco": "Preço",
    "estoque": "Estoque",
    "validade": "Validade",
    "peso": "Peso",
    "categoria": "Categoria",
    "codigo de barras": "Código de barras",
}
TERMOS_COMUNS = {
    "quais", "qual", "qualquer", "quanto", "quantos", "quanta", "quantas",
    "custa", "custam", "existe", "existem", "lista", "liste", "listar",
    "preco", "precos", "produto", "produtos", "estoque", "sistema",
    "catalogo", "total", "valor", "categoria", "categorias", "codigo",
    "barras", "validade", "peso", "sobre", "tem", "dos", "das", "com",
    "uma", "uns", "umas", "esta", "estao", "disponivel", "disponiveis",
}


def formatar_preco(valor: float) -> str:
    numero = format(valor, ",.2f").translate(str.maketrans(",.", ".,"))
    return f"R$ {numero}"


def formatar_atributo(produto: ProdutoDB, atributo: str) -> str:
    valores = {
        "preco": formatar_preco(produto.preco),
        "estoque": f"{produto.quant_estoque} unidades",
        "validade": produto.validade,
        "peso": f"{produto.peso:g}",
        "categoria": produto.categoria,
        "codigo de barras": produto.codigo_barras,
    }
    return f"**{produto.nome}** — {ATRIBUTOS[atributo]}: {valores[atributo]}"


def responder_do_catalogo(mensagem: str, db: Session) -> str | None:
    pergunta = normalizar_busca(mensagem).strip().rstrip("?! .")

    if re.fullmatch(
        r"(?:quantos produtos (?:ha|existem|tem|temos|estao cadastrados)"
        r"|quantos produtos (?:ha |existem |tem |temos )?cadastrados"
        r"|(?:qual e o )?total de produtos(?: cadastrados)?"
        r"|quantos produtos)" + SUFIXO_CATALOGO,
        pergunta,
    ):
        total = db.query(func.count(ProdutoDB.id)).scalar()
        return f"Há **{total}** produtos cadastrados."

    if re.fullmatch(
        r"(?:(?:qual e )?o )?(?:total de unidades|estoque total)(?: em estoque)?"
        r"|quantas unidades (?:ha |existem |temos |tem )?em estoque",
        pergunta,
    ):
        total = db.query(func.coalesce(func.sum(ProdutoDB.quant_estoque), 0)).scalar()
        return f"Há **{total}** unidades em estoque, somando todos os produtos."

    consulta_estoque_zero = re.fullmatch(
        r"(?:(?:ha|havia|existe|existem|tem|temos|quais|quantos|liste|listar|mostre) )?"
        r"(?:(?:algum|alguns|um|os) )?"
        r"(?:produtos?(?: cadastrados?)? )?"
        r"(?:que )?(?:(?:esta|estao|ficou|ficaram|tem) )?"
        r"(?:(?P<sem>sem estoque)|(?:com |o )?(?:"
        r"estoque (?:zerado|(?:igual a |de )?(?:0|zero))"
        r"|(?:0|zero)(?: unidades?)? (?:em|no|de) estoque))"
        + SUFIXO_CATALOGO,
        " ".join(pergunta.split()),
    )
    if consulta_estoque_zero:
        sem_estoque = consulta_estoque_zero.group("sem") is not None
        saldo = ProdutoDB.quant_estoque
        filtro = saldo <= 0 if sem_estoque else saldo == 0
        descricao = "sem estoque" if sem_estoque else "com estoque zerado"

        consulta = db.query(ProdutoDB).filter(filtro)
        total = consulta.count()
        if not total:
            return f"Nenhum produto {descricao} foi encontrado."

        produtos = consulta.order_by(ProdutoDB.nome, ProdutoDB.id).limit(LIMITE_CONTEXTO)
        nomes = "\n".join(f"- {produto.nome} (#{produto.id})" for produto in produtos)
        aviso = f"\nMostrando os primeiros {LIMITE_CONTEXTO}." if total > LIMITE_CONTEXTO else ""
        unidade = "produto" if total == 1 else "produtos"
        return f"Há **{total}** {unidade} {descricao}.\n\n{nomes}{aviso}"

    extremo = re.fullmatch(
        r"(?:(?:qual (?:e )?o|o) )?produto (?:mais )?(barato|caro)" + SUFIXO_CATALOGO,
        pergunta,
    )
    if extremo:
        ordenar = ProdutoDB.preco.asc() if extremo[1] == "barato" else ProdutoDB.preco.desc()
        produto = db.query(ProdutoDB).order_by(ordenar, ProdutoDB.id).first()
        if produto is None:
            return "Não há produtos cadastrados."
        empate = db.query(func.count(ProdutoDB.id)).filter(ProdutoDB.preco == produto.preco).scalar()
        aviso = f" ({empate} produtos com esse preço.)" if empate > 1 else ""
        return formatar_atributo(produto, "preco") + aviso

    atributos = "|".join(ATRIBUTOS)
    detalhe = re.fullmatch(
        rf"(?:qual (?:e )?(?:o |a )?)?({atributos}) (?:de|do|da) (.+)", pergunta
    )
    preco = re.fullmatch(r"(?:quanto custa|qual o valor de) (.+)", pergunta)
    estoque = re.fullmatch(r"quantas unidades (?:de|do|da) (.+?) (?:ha |temos |tem )?em estoque", pergunta)
    if detalhe:
        atributo, nome = detalhe.groups()
    elif preco:
        atributo, nome = "preco", preco[1]
    elif estoque:
        atributo, nome = "estoque", estoque[1]
    else:
        return None

    nome = re.sub(r"^(?:o |a |produto )", "", nome).strip(" «»\"'")
    produtos = (
        db.query(ProdutoDB)
        .filter(or_(func.normalizar_busca(ProdutoDB.nome) == nome, ProdutoDB.codigo_barras == nome))
        .order_by(ProdutoDB.id)
        .limit(LIMITE_CONTEXTO + 1)
        .all()
    )
    if len(produtos) == 1:
        return formatar_atributo(produtos[0], atributo)
    if len(produtos) > 1:
        return "Há mais de um produto com esse nome. Faça a pergunta usando o código de barras do produto."
    return None


def gerar_contexto_produtos(mensagem: str, db: Session) -> str:
    palavras = re.findall(r"[a-z0-9]+", normalizar_busca(mensagem))
    termos = list(dict.fromkeys(
        termo for termo in palavras if len(termo) >= 3 and termo not in TERMOS_COMUNS
    ))[:12]

    consulta = db.query(ProdutoDB)
    if termos:
        nome = func.normalizar_busca(ProdutoDB.nome)
        categoria = func.normalizar_busca(ProdutoDB.categoria)
        criterios = [
            (
                func.instr(nome, termo) > 0,
                func.instr(categoria, termo) > 0,
                ProdutoDB.codigo_barras == termo,
            )
            for termo in termos
        ]
        pontos = sum(
            case((codigo, 5), (nome, 3), (categoria, 1), else_=0)
            for nome, categoria, codigo in criterios
        )
        consulta = consulta.filter(or_(*(c for grupo in criterios for c in grupo)))
        consulta = consulta.order_by(pontos.desc())

    produtos = consulta.order_by(ProdutoDB.id).limit(LIMITE_CONTEXTO).all()
    registros = [{
        "id": produto.id,
        "nome": produto.nome[:200],
        "preco": formatar_preco(produto.preco),
        "estoque": produto.quant_estoque,
        "validade": produto.validade[:30],
        "codigo_barras": produto.codigo_barras[:40],
        "categoria": produto.categoria[:100],
        "peso": produto.peso,
    } for produto in produtos]
    return json.dumps(registros, ensure_ascii=False, separators=(",", ":"))