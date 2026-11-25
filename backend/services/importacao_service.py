import csv
import io
import re
import unicodedata
from datetime import date, datetime

from pydantic import ValidationError
from sqlalchemy.orm import Session

from db.produto_schema import ProdutoDB
from entity.produto_model import ProdutoCreate
from services.ollama_service import extrair_produtos_json


EXTENSOES_ACEITAS = (".csv", ".xlsx", ".pdf", ".txt")

LIMITE_TEXTO_OLLAMA = 12000

SINONIMOS = {
    "nome": {"nome", "produto", "nomedoproduto", "descricao", "item"},
    "preco": {"preco", "valor", "precounitario", "valorunitario", "precovenda", "precor"},
    "quant_estoque": {"quantidade", "quant", "qtd", "qtde", "quantestoque", "estoque", "quantidadeemestoque"},
    "codigo_barras": {"ean", "ean13", "gtin", "codigodebarras", "codigobarras", "codbarras", "codigo"},
    "validade": {"validade", "datadevalidade", "datavalidade", "vencimento", "datadevencimento"},
    "categoria": {"categoria", "tipo", "grupo", "departamento"},
    "peso": {"peso", "pesog", "pesogramas", "pesoemgramas"},
}

NOMES_CAMPOS = {
    "nome": "nome",
    "preco": "preço",
    "quant_estoque": "quantidade",
    "codigo_barras": "código de barras",
    "validade": "validade",
    "categoria": "categoria",
    "peso": "peso",
}


class ArquivoInvalidoError(Exception):
    pass


def normalizar_cabecalho(texto) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def identificar_campo(cabecalho) -> str | None:
    chave = normalizar_cabecalho(cabecalho)
    for campo, sinonimos in SINONIMOS.items():
        if chave in sinonimos:
            return campo
    return None


def converter_numero(valor):
    if valor is None or isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return valor
    texto = re.sub(r"(?i)r\$|\s", "", str(valor))
    texto = re.sub(r"(?<=\d)g$", "", texto)
    if not texto:
        return None
    if "," in texto and "." in texto and texto.rfind(".") > texto.rfind(","):
        texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return valor


def converter_inteiro(valor):
    numero = converter_numero(valor)
    if isinstance(numero, float) and numero.is_integer():
        return int(numero)
    return numero


def converter_data(valor):
    if valor is None or valor == "":
        return valor
    if isinstance(valor, (datetime, date)):
        return valor.strftime("%d/%m/%Y")
    texto = str(valor).strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return texto


def converter_codigo(valor):
    if valor is None:
        return None
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    texto = str(valor).strip()
    if re.fullmatch(r"\d+\.0+", texto):
        texto = texto.split(".")[0]
    return texto


def converter_texto(valor):
    if valor is None:
        return None
    return str(valor).strip()


CONVERSORES = {
    "nome": converter_texto,
    "preco": converter_numero,
    "quant_estoque": converter_inteiro,
    "codigo_barras": converter_codigo,
    "validade": converter_data,
    "categoria": converter_texto,
    "peso": converter_numero,
}


def normalizar_item(item: dict) -> dict:
    resultado = {}
    for chave, valor in item.items():
        campo = identificar_campo(chave)
        if campo is None or campo in resultado:
            continue
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            resultado[campo] = ""
            continue
        resultado[campo] = CONVERSORES[campo](valor)
    return resultado


def linhas_para_itens(linhas: list[list]) -> list[dict]:
    linhas = [linha for linha in linhas if any(str(c or "").strip() for c in linha)]
    if not linhas:
        return []
    cabecalho = linhas[0]
    if not any(identificar_campo(c) for c in cabecalho):
        raise ArquivoInvalidoError(
            "Não foi possível identificar as colunas do arquivo. "
            "Use cabeçalhos como Nome, Preço, Quantidade, Código de Barras, "
            "Validade, Categoria e Peso."
        )
    return [
        normalizar_item(dict(zip(cabecalho, linha)))
        for linha in linhas[1:]
    ]


def decodificar(conteudo: bytes) -> str:
    for codificacao in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return conteudo.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise ArquivoInvalidoError("Não foi possível ler o texto do arquivo.")


def ler_csv(conteudo: bytes) -> list[dict]:
    texto = decodificar(conteudo)
    amostra = texto[:4096]
    try:
        separador = csv.Sniffer().sniff(amostra, delimiters=";,\t").delimiter
    except csv.Error:
        separador = ";" if amostra.count(";") > amostra.count(",") else ","
    linhas = list(csv.reader(io.StringIO(texto), delimiter=separador))
    return linhas_para_itens(linhas)


def ler_xlsx(conteudo: bytes) -> list[dict]:
    from openpyxl import load_workbook

    try:
        planilha = load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    except Exception:
        raise ArquivoInvalidoError("Não foi possível abrir a planilha .xlsx.")
    try:
        aba = planilha.active
        linhas = [list(linha) for linha in aba.iter_rows(values_only=True)]
    finally:
        planilha.close()
    return linhas_para_itens(linhas)


def ler_pdf(conteudo: bytes) -> str:
    from pypdf import PdfReader

    try:
        leitor = PdfReader(io.BytesIO(conteudo))
        return "\n".join(pagina.extract_text() or "" for pagina in leitor.pages)
    except Exception:
        raise ArquivoInvalidoError("Não foi possível ler o arquivo PDF.")


def extrair_com_ollama(texto: str) -> list[dict]:
    texto = texto.strip()
    if not texto:
        raise ArquivoInvalidoError("O documento não contém texto legível.")
    produtos = extrair_produtos_json(texto[:LIMITE_TEXTO_OLLAMA])
    return [normalizar_item(item) for item in produtos if isinstance(item, dict)]


def ler_documento(nome_arquivo: str, conteudo: bytes) -> list[dict]:
    extensao = "." + nome_arquivo.rsplit(".", 1)[-1].lower() if "." in nome_arquivo else ""
    if extensao not in EXTENSOES_ACEITAS:
        raise ArquivoInvalidoError(
            "Formato não suportado. Envie um arquivo .csv, .xlsx, .pdf ou .txt."
        )
    if not conteudo:
        raise ArquivoInvalidoError("O arquivo enviado está vazio.")
    if extensao == ".csv":
        return ler_csv(conteudo)
    if extensao == ".xlsx":
        return ler_xlsx(conteudo)
    if extensao == ".pdf":
        return extrair_com_ollama(ler_pdf(conteudo))
    return extrair_com_ollama(decodificar(conteudo))


def traduzir_erro(erro: dict) -> str:
    campo = erro["loc"][0] if erro.get("loc") else ""
    nome = NOMES_CAMPOS.get(campo, str(campo))
    tipo = erro.get("type", "")
    if tipo == "missing":
        return f"campo {nome} ausente"
    if tipo == "string_too_short":
        return f"campo {nome} vazio"
    if campo in ("quant_estoque", "validade", "categoria"):
        return f"{nome} inválida"
    return f"{nome} inválido"


def validar_produtos(itens: list[dict], db: Session):
    codigos_existentes = {
        codigo for (codigo,) in db.query(ProdutoDB.codigo_barras).all()
    }
    codigos_no_arquivo = set()
    validos = []
    ignorados = []

    for indice, item in enumerate(itens, start=1):
        nome = item.get("nome") if isinstance(item.get("nome"), str) else None
        try:
            produto = ProdutoCreate.model_validate(item)
        except ValidationError as erro:
            motivos = sorted({traduzir_erro(e) for e in erro.errors()})
            ignorados.append({"item": indice, "nome": nome, "motivo": "; ".join(motivos)})
            continue

        codigo = produto.codigo_barras.strip()
        if codigo and codigo in codigos_existentes:
            ignorados.append({
                "item": indice,
                "nome": produto.nome,
                "motivo": f"código de barras {codigo} já cadastrado",
            })
            continue
        if codigo and codigo in codigos_no_arquivo:
            ignorados.append({
                "item": indice,
                "nome": produto.nome,
                "motivo": f"código de barras {codigo} repetido no arquivo",
            })
            continue

        if codigo:
            codigos_no_arquivo.add(codigo)
        validos.append(produto)

    return validos, ignorados
