const API_URL = 'http://127.0.0.1:8000'

export async function listarProdutos() {
  const resposta = await fetch(`${API_URL}/produto`)

  if (!resposta.ok) {
    throw new Error('Erro ao buscar produtos')
  }

  return resposta.json()
}

export async function buscarProduto(id) {
  const resposta = await fetch(`${API_URL}/produto/${id}`)

  if (!resposta.ok) {
    throw new Error('Erro ao buscar produto')
  }

  return resposta.json()
}

export async function criarProduto(produto) {
  const resposta = await fetch(`${API_URL}/produto/criar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(produto)
  })

  if (!resposta.ok) {
    throw new Error('Erro ao criar produto')
  }

  return resposta.json()
}

export async function atualizarProduto(id, produto) {
  const resposta = await fetch(`${API_URL}/produto/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(produto)
  })

  if (!resposta.ok) {
    throw new Error('Erro ao atualizar produto')
  }

  return resposta.json()
}

export async function excluirProduto(id) {
  const resposta = await fetch(`${API_URL}/produto/${id}`, {
    method: 'DELETE'
  })

  if (!resposta.ok) {
    throw new Error('Erro ao excluir produto')
  }

  return resposta.json()
}