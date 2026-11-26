import { requisitar } from './api'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export function registrarVenda(itens) {
  return requisitar(
    '/venda/lote',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({ itens })
    },
    'Não foi possível registrar a venda.'
  )
}

export function listarVendas() {
  return requisitar('/venda', undefined, 'Não foi possível carregar as vendas.')
}