import json
import os
import re

import requests

# Configuráveis por variável de ambiente (ex.: dentro do Docker o Ollama
# do host é acessível em http://host.docker.internal:11434/api/chat).
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODELO = os.getenv("OLLAMA_MODELO", "qwen3:1.7b")


def enviar_mensagem(
    mensagem: str,
    contexto: str | None = None
) -> str:

    mensagens = [
        {
            "role": "system",
            "content": (
                "Você é um assistente virtual de um sistema de gerenciamento "
                "de produtos e estoque. Responda sempre em português, de forma "
                "clara, objetiva e amigável. "
                "Quando a pergunta envolver produtos, preços, estoque, "
                "categorias, validade, peso ou códigos de barras, utilize "
                "somente os dados fornecidos pelo sistema. "
                "Não invente produtos ou informações que não estejam no contexto. "
                "Caso a informação não esteja disponível, informe ao usuário "
                "que não encontrou esse dado no sistema."
            )
        }
    ]

    if contexto:
        mensagens.append(
            {
                "role": "system",
                "content": (
                    "Os dados atuais dos produtos cadastrados no sistema são:\n\n"
                    f"{contexto}"
                )
            }
        )

    mensagens.append(
        {
            "role": "user",
            "content": mensagem
        }
    )

    payload = {
        "model": MODELO,
        "messages": mensagens,
        "stream": False,
        "think": False
    }

    try:
        resposta = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        resposta.raise_for_status()

        dados = resposta.json()

        return dados["message"]["content"]

    except (KeyError, TypeError, ValueError):
        raise RuntimeError(
            "Resposta inesperada do Ollama."
        )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Não foi possível conectar ao Ollama."
        )

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "O Ollama demorou muito para responder."
        )

    except requests.exceptions.RequestException as erro:
        raise RuntimeError(
            f"Erro ao consultar o Ollama: {erro}"
        )


def extrair_produtos_json(texto: str) -> list[dict]:
    mensagens = [
        {
            "role": "system",
            "content": (
                "Você extrai produtos de documentos. Responda somente com um "
                "JSON no formato {\"produtos\": [...]}, sem nenhum texto extra. "
                "Cada produto deve ter exatamente as chaves: nome (texto), "
                "preco (número decimal em reais, ex.: 27.90), quant_estoque "
                "(número inteiro), validade (texto no formato dd/mm/aaaa), "
                "codigo_barras (texto só com dígitos), categoria (texto) e "
                "peso (número em gramas). Use null para informações que não "
                "estiverem no documento. Não invente produtos nem valores."
            )
        },
        {
            "role": "user",
            "content": f"Documento:\n\n{texto}"
        }
    ]

    payload = {
        "model": MODELO,
        "messages": mensagens,
        "stream": False,
        "think": False,
        "format": "json"
    }

    try:
        resposta = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        resposta.raise_for_status()

        conteudo = resposta.json()["message"]["content"]

    except (KeyError, TypeError, ValueError):
        raise RuntimeError(
            "Resposta inesperada do Ollama."
        )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Não foi possível conectar ao Ollama."
        )

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "O Ollama demorou muito para responder."
        )

    except requests.exceptions.RequestException as erro:
        raise RuntimeError(
            f"Erro ao consultar o Ollama: {erro}"
        )

    conteudo = re.sub(r"<think>[\s\S]*?</think>", "", conteudo).strip()

    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError:
        raise RuntimeError(
            "O Ollama não devolveu um JSON válido com os produtos."
        )

    if isinstance(dados, list):
        return dados

    if isinstance(dados, dict):
        produtos = dados.get("produtos")
        if isinstance(produtos, list):
            return produtos
        if "nome" in dados:
            return [dados]

    return []
