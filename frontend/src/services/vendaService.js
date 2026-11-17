import { requisitar } from './api'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export function registrarVenda(produtoId, quantidade) {
  return requisitar(
    '/venda',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({ produto_id: produtoId, quantidade })
    },
    'Não foi possível registrar a venda.'
  )
}

export function listarVendas() {
  return requisitar('/venda', undefined, 'Não foi possível carregar as vendas.')
}
