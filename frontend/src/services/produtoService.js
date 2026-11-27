import { requisitar } from './api'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export function listarProdutos() {
  return requisitar('/produto', undefined, 'Erro ao buscar produtos')
}

export function listarPaginaProdutos(
  pagina,
  busca,
  signal,
  { porPagina = 10, ordenarPor = 'nome', ordem = 'asc' } = {}
) {
  const parametros = new URLSearchParams({
    pagina,
    busca,
    por_pagina: porPagina,
    ordenar_por: ordenarPor,
    ordem
  })

  return requisitar(
    `/produto/pagina?${parametros}`,
    { signal },
    'Erro ao buscar produtos'
  )
}

export function buscarProduto(id) {
  return requisitar(`/produto/${id}`, undefined, 'Erro ao buscar produto')
}

export function criarProduto(produto) {
  return requisitar(
    '/produto/criar',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(produto)
    },
    'Erro ao criar produto'
  )
}

export function atualizarProduto(id, produto) {
  return requisitar(
    `/produto/${id}`,
    {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(produto)
    },
    'Erro ao atualizar produto'
  )
}

export function excluirProduto(id) {
  return requisitar(
    `/produto/${id}`,
    { method: 'DELETE' },
    'Erro ao excluir produto'
  )
}