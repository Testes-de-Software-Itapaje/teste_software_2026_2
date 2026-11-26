import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  MdModeEdit,
  MdDelete,
  MdChat,
  MdReceiptLong,
  MdShoppingCartCheckout
} from 'react-icons/md'

import { listarPaginaProdutos, excluirProduto } from '../services/produtoService'
import { registrarVenda } from '../services/vendaService'
import VendaModal from '../components/VendaModal'

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

function Produtos() {
  const [resultado, setResultado] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [busca, setBusca] = useState('')
  const [pagina, setPagina] = useState(1)
  const [revisao, setRevisao] = useState(0)
  const [selecionados, setSelecionados] = useState({})
  const [vendaAberta, setVendaAberta] = useState(false)
  const [aviso, setAviso] = useState('')

  function prepararConsulta() {
    setCarregando(true)
    setErro('')
  }

  useEffect(() => {
    const consulta = new AbortController()

    async function carregarProdutos() {
      try {
        const dados = await listarPaginaProdutos(pagina, busca.trim(), consulta.signal)
        if (consulta.signal.aborted) return
        setResultado(dados)
        setSelecionados(atuais => {
          const atualizados = { ...atuais }
          for (const produto of dados.itens) {
            if (!(produto.id in atualizados)) continue
            if (produto.quant_estoque > 0) atualizados[produto.id] = produto
            else delete atualizados[produto.id]
          }
          return atualizados
        })
      } catch (falha) {
        if (!consulta.signal.aborted) {
          setResultado(null)
          setErro(falha.message)
        }
      } finally {
        if (!consulta.signal.aborted) setCarregando(false)
      }
    }

    carregarProdutos()
    return () => consulta.abort()
  }, [pagina, busca, revisao])

  function trocarPagina(novaPagina) {
    prepararConsulta()
    setPagina(novaPagina)
  }

  function atualizarLista() {
    prepararConsulta()
    setRevisao(atual => atual + 1)
  }

  function alternarSelecao(produto, marcado) {
    setSelecionados(atuais => {
      const proximos = { ...atuais }
      if (marcado) proximos[produto.id] = produto
      else delete proximos[produto.id]
      return proximos
    })
  }

  async function handleExcluir(id) {
    const confirmar = window.confirm('Tem certeza que deseja excluir este produto?')
    if (!confirmar) return

    try {
      await excluirProduto(id)
      alternarSelecao({ id }, false)
      setAviso('Produto excluído com sucesso.')
      atualizarLista()
    } catch (falha) {
      setErro(falha.message)
    }
  }

  async function handleConfirmarVenda(itens) {
    const vendas = await registrarVenda(itens)
    const total = vendas.reduce((soma, venda) => soma + venda.valor_total, 0)
    setVendaAberta(false)
    setSelecionados({})
    setAviso(vendas.length === 1
      ? `Venda #${vendas[0].id} registrada. Estoque restante de ${vendas[0].produto_nome}: ${vendas[0].estoque_restante}.`
      : `Venda registrada com ${vendas.length} produtos. Total: ${moeda.format(total)}.`)
    atualizarLista()
  }

  const produtosSelecionados = Object.values(selecionados)

  return (
    <div className="sistema">
      <main className="conteudo">
        <header className="topo">
          <div>
            <h1>Sistema de Produtos</h1>
            <p>Gerencie seus produtos, o estoque e as vendas.</p>
          </div>
          <div className="topo-links">
            <Link to="/vendas" className="botao-voltar">
              <MdReceiptLong size={19} /> Histórico de vendas
            </Link>
            <Link
              to="/chat"
              className="botao-chat"
              title="Conversar com o assistente"
              aria-label="Abrir o chat com o assistente"
            >
              <MdChat size={24} />
            </Link>
          </div>
        </header>

        <div className="acoes-topo produtos-toolbar">
          <Link to="/produtos/criar" className="botao-novo">
            <span>+</span> Novo Produto
          </Link>
          <input
            type="search"
            className="busca-produtos"
            placeholder="Buscar por nome, categoria ou código..."
            aria-label="Buscar produtos"
            maxLength={200}
            value={busca}
            onChange={evento => {
              prepararConsulta()
              setBusca(evento.target.value)
              setPagina(1)
            }}
          />
          <div className="produtos-venda-acoes">
            {produtosSelecionados.length > 0 && (
              <button type="button" className="botao-limpar-selecao" onClick={() => setSelecionados({})}>
                Limpar seleção
              </button>
            )}
            <button
              type="button"
              className="botao-vender"
              disabled={carregando || produtosSelecionados.length === 0}
              onClick={() => {
                setAviso('')
                setVendaAberta(true)
              }}
            >
              <MdShoppingCartCheckout size={18} /> Vender
              {produtosSelecionados.length > 0 && ` (${produtosSelecionados.length})`}
            </button>
          </div>
        </div>

        {aviso && <p className="aviso-sucesso" role="status">{aviso}</p>}
        {erro && <p className="venda-erro aviso-erro" role="alert">{erro}</p>}

        <section className="card-tabela">
          {carregando ? (
            <div className="estado" role="status">Carregando produtos...</div>
          ) : resultado && (
            <>
              <div className="tabela-header">
                <span>Total: {resultado.total} produtos</span>
              </div>
              <div className="tabela-container">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Selecionar</th>
                      <th>ID</th>
                      <th>Nome</th>
                      <th>Preço</th>
                      <th>Estoque</th>
                      <th>Validade</th>
                      <th>Código de Barras</th>
                      <th>Categoria</th>
                      <th>Peso</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultado.itens.map(produto => (
                      <tr key={produto.id}>
                        <td>
                          <input
                            type="checkbox"
                            className="produto-selecao"
                            aria-label={`Selecionar ${produto.nome} (produto #${produto.id})`}
                            checked={produto.id in selecionados}
                            disabled={produto.quant_estoque < 1}
                            onChange={evento => alternarSelecao(produto, evento.target.checked)}
                          />
                        </td>
                        <td>{produto.id}</td>
                        <td><div className="produto-nome">{produto.nome}</div></td>
                        <td>{moeda.format(Number(produto.preco))}</td>
                        <td>
                          <span className={produto.quant_estoque < 1 ? 'estoque-zerado' : 'estoque-disponivel'}>
                            {produto.quant_estoque}
                          </span>
                        </td>
                        <td>{produto.validade}</td>
                        <td>{produto.codigo_barras}</td>
                        <td><span className="categoria">{produto.categoria}</span></td>
                        <td>{produto.peso}</td>
                        <td>
                          <div className="acoes">
                            <Link
                              to={`/produtos/${produto.id}`}
                              className="botao-editar"
                              title={`Editar ${produto.nome}`}
                              aria-label={`Editar ${produto.nome}`}
                            >
                              <MdModeEdit size={20} />
                            </Link>
                            <button
                              type="button"
                              className="botao-excluir"
                              onClick={() => handleExcluir(produto.id)}
                              title={`Excluir ${produto.nome}`}
                              aria-label={`Excluir ${produto.nome}`}
                            >
                              <MdDelete size={20} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {resultado.total === 0 && (
                <div className="sem-produtos">Nenhum produto encontrado.</div>
              )}
              {resultado.total_paginas > 1 && (
                <nav className="produtos-paginacao" aria-label="Paginação de produtos">
                  <button
                    type="button"
                    disabled={resultado.pagina <= 1}
                    onClick={() => trocarPagina(resultado.pagina - 1)}
                  >
                    Anterior
                  </button>
                  <span>Página {resultado.pagina} de {resultado.total_paginas}</span>
                  <button
                    type="button"
                    disabled={resultado.pagina >= resultado.total_paginas}
                    onClick={() => trocarPagina(resultado.pagina + 1)}
                  >
                    Próxima
                  </button>
                </nav>
              )}
            </>
          )}
        </section>
      </main>
      {vendaAberta && (
        <VendaModal
          produtos={produtosSelecionados}
          onFechar={() => setVendaAberta(false)}
          onConfirmar={handleConfirmarVenda}
        />
      )}
    </div>
  )
}

export default Produtos