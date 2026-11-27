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


def _responder_extremo(pergunta: str, db: Session) -> str | None:
    """Responde 'qual produto tem maior/menor estoque, preço ou peso'."""
    if not re.search(r"\bproduto\b", pergunta) or "categoria" in pergunta:
        return None

    maior = re.search(r"\b(?:maior|mais|max\w*)\b", pergunta)
    menor = re.search(r"\b(?:menor|menos|min\w*)\b", pergunta)
    if bool(maior) == bool(menor) and not re.search(r"caro|barato|pesado|leve", pergunta):
        return None

    if re.search(r"estoque|quantidade|unidades", pergunta):
        coluna, rotulo, formato = ProdutoDB.quant_estoque, "Estoque", lambda p: f"{p.quant_estoque} unidades"
        crescente = bool(menor)
    elif re.search(r"caro|barato|preco|valor", pergunta):
        coluna, rotulo, formato = ProdutoDB.preco, "Preço", lambda p: formatar_preco(p.preco)
        crescente = bool(re.search(r"barato|menor|menos", pergunta))
    elif re.search(r"pesad|leve|peso", pergunta):
        coluna, rotulo, formato = ProdutoDB.peso, "Peso", lambda p: f"{p.peso:g}"
        crescente = bool(re.search(r"leve|menor|menos", pergunta))
    else:
        return None

    ordem = coluna.asc() if crescente else coluna.desc()
    primeiro = db.query(ProdutoDB).order_by(ordem, ProdutoDB.id).first()
    if primeiro is None:
        return "Não há produtos cadastrados."
    valor = getattr(primeiro, coluna.key)
    empatados = db.query(ProdutoDB).filter(coluna == valor).order_by(ProdutoDB.nome, ProdutoDB.id).all()
    linhas = [f"**{p.nome}** — {rotulo}: {formato(p)}" for p in empatados[:5]]
    if len(empatados) == 1:
        return linhas[0]
    aviso = f"\n(+ {len(empatados) - 5} outros)" if len(empatados) > 5 else ""
    return f"{len(empatados)} produtos empatados:\n\n" + "\n".join(f"- {l}" for l in linhas) + aviso


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
    pergunta_simples = " ".join(pergunta.split())
    estoque_zero_livre = (
        "produto" in pergunta_simples
        and re.match(r"(?:qual|quais|quantos|liste|listar|mostre|ha|existe|existem|tem|temos|algum)\b", pergunta_simples)
        and re.search(
            r"\b(?:zerad[oa]s?|esgotad[oa]s?|sem estoque|acabou|acabaram|estoque (?:igual a )?(?:0|zero))\b",
            pergunta_simples,
        )
    )
    if consulta_estoque_zero or estoque_zero_livre:
        if consulta_estoque_zero:
            sem_estoque = consulta_estoque_zero.group("sem") is not None
        else:
            sem_estoque = "sem estoque" in pergunta_simples
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

    if re.fullmatch(
        r"(?:quais (?:sao )?(?:as )?|liste (?:as )?|listar (?:as )?|mostre (?:as )?)?"
        r"categorias(?: (?:existem|ha|temos|tem|cadastradas))?" + SUFIXO_CATALOGO,
        " ".join(pergunta.split()),
    ):
        linhas = _contagem_por_categoria(db)
        if not linhas:
            return "Não há produtos cadastrados."
        itens = "\n".join(f"- {nome}: {qtd}" for nome, qtd in linhas)
        return f"Há **{len(linhas)}** categorias:\n\n{itens}"

    por_categoria = re.fullmatch(
        r"(?P<acao>quantos|quais|liste|listar|mostre) produtos "
        r"(?:ha |existem |tem |temos )?(?:na|da|de|em) categoria (?P<cat>.+?)"
        + SUFIXO_CATALOGO,
        " ".join(pergunta.split()),
    )
    if por_categoria:
        alvo = por_categoria["cat"].strip(" «»\"'")
        consulta = db.query(ProdutoDB).filter(func.normalizar_busca(ProdutoDB.categoria) == alvo)
        total = consulta.count()
        if not total:
            return f"Nenhum produto foi encontrado na categoria {alvo}."
        if por_categoria["acao"] == "quantos":
            return f"Há **{total}** produtos na categoria **{alvo}**."
        produtos = consulta.order_by(ProdutoDB.nome, ProdutoDB.id).limit(LIMITE_CONTEXTO)
        nomes = "\n".join(f"- {p.nome} (#{p.id})" for p in produtos)
        aviso = f"\nMostrando os primeiros {LIMITE_CONTEXTO}." if total > LIMITE_CONTEXTO else ""
        return f"Há **{total}** produtos na categoria **{alvo}**.\n\n{nomes}{aviso}"

    ranking = _responder_extremo(pergunta, db)
    if ranking is not None:
        return ranking

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


def _contagem_por_categoria(db: Session) -> list[tuple[str, int]]:
    """Conta produtos por categoria, unindo variações de acento/maiúsculas."""
    contagem: dict[str, list] = {}
    for nome, qtd in db.query(ProdutoDB.categoria, func.count(ProdutoDB.id)).group_by(ProdutoDB.categoria):
        chave = normalizar_busca(nome)
        if chave in contagem:
            contagem[chave][1] += qtd
        else:
            contagem[chave] = [nome, qtd]
    return sorted((tuple(v) for v in contagem.values()), key=lambda x: normalizar_busca(x[0]))


def _extremo_estoque(db: Session, ordem) -> dict | None:
    produto = db.query(ProdutoDB).order_by(ordem, ProdutoDB.id).first()
    return None if produto is None else {"nome": produto.nome, "unidades": produto.quant_estoque}


def gerar_resumo_catalogo(db: Session) -> dict:
    total, estoque, menor, maior, media = db.query(
        func.count(ProdutoDB.id),
        func.coalesce(func.sum(ProdutoDB.quant_estoque), 0),
        func.min(ProdutoDB.preco),
        func.max(ProdutoDB.preco),
        func.avg(ProdutoDB.preco),
    ).one()
    return {
        "total_produtos": total,
        "total_unidades_em_estoque": estoque,
        "produtos_sem_estoque": db.query(func.count(ProdutoDB.id)).filter(ProdutoDB.quant_estoque <= 0).scalar(),
        "menor_preco": formatar_preco(menor) if total else None,
        "maior_preco": formatar_preco(maior) if total else None,
        "preco_medio": formatar_preco(media) if total else None,
        "produto_com_maior_estoque": _extremo_estoque(db, ProdutoDB.quant_estoque.desc()),
        "produto_com_menor_estoque": _extremo_estoque(db, ProdutoDB.quant_estoque.asc()),
        "numero_de_produtos_por_categoria_NAO_E_ESTOQUE": {nome: qtd for nome, qtd in _contagem_por_categoria(db)},
    }


def _variantes(termo: str) -> list[str]:
    """Inclui singular simples para casar plurais (refrigerantes -> refrigerante)."""
    if len(termo) > 4 and termo.endswith("s"):
        return [termo, termo[:-1]]
    return [termo]


def gerar_contexto_produtos(mensagem: str, db: Session) -> str:
    palavras = re.findall(r"[a-z0-9]+", normalizar_busca(mensagem))
    termos = list(dict.fromkeys(
        termo for termo in palavras if len(termo) >= 3 and termo not in TERMOS_COMUNS
    ))[:12]
    termos = list(dict.fromkeys(v for t in termos for v in _variantes(t)))[:16]

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
    return json.dumps(
        {"resumo_do_catalogo": gerar_resumo_catalogo(db), "registros_relacionados": registros},
        ensure_ascii=False,
        separators=(",", ":"),
    )