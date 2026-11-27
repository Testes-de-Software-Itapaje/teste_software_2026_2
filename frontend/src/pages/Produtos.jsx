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

const COLUNAS = [
  { campo: 'nome', titulo: 'Nome' },
  { campo: 'preco', titulo: 'Preço' },
  { campo: 'quant_estoque', titulo: 'Estoque' },
  { campo: 'validade', titulo: 'Validade' },
  { campo: 'codigo_barras', titulo: 'Código de Barras' },
  { campo: 'categoria', titulo: 'Categoria' },
  { campo: 'peso', titulo: 'Peso' }
]

const OPCOES_POR_PAGINA = [10, 20, 50, 100]

function Produtos() {
  const [resultado, setResultado] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [busca, setBusca] = useState('')
  const [pagina, setPagina] = useState(1)
  const [porPagina, setPorPagina] = useState(10)
  const [ordenarPor, setOrdenarPor] = useState('nome')
  const [ordem, setOrdem] = useState('asc')
  const [paginaDigitada, setPaginaDigitada] = useState('1')
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
        const dados = await listarPaginaProdutos(pagina, busca.trim(), consulta.signal, {
          porPagina,
          ordenarPor,
          ordem
        })
        if (consulta.signal.aborted) return
        setResultado(dados)
        setPaginaDigitada(String(dados.pagina))
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
  }, [pagina, busca, revisao, porPagina, ordenarPor, ordem])

  function trocarPagina(novaPagina) {
    prepararConsulta()
    setPagina(novaPagina)
  }

  function alternarOrdenacao(campo) {
    prepararConsulta()
    if (campo === ordenarPor) {
      setOrdem(atual => (atual === 'asc' ? 'desc' : 'asc'))
    } else {
      setOrdenarPor(campo)
      setOrdem('asc')
    }
    setPagina(1)
  }

  function trocarPorPagina(valor) {
    prepararConsulta()
    setPorPagina(valor)
    setPagina(1)
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
                <label className="por-pagina">
                  Exibir{' '}
                  <select
                    value={porPagina}
                    onChange={evento => trocarPorPagina(Number(evento.target.value))}
                    aria-label="Produtos por página"
                  >
                    {OPCOES_POR_PAGINA.map(opcao => (
                      <option key={opcao} value={opcao}>{opcao}</option>
                    ))}
                  </select>
                  {' '}por página
                </label>
              </div>
              <div className="tabela-container">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Selecionar</th>
                      <th>ID</th>
                      {COLUNAS.map(coluna => (
                        <th
                          key={coluna.campo}
                          aria-sort={
                            ordenarPor !== coluna.campo
                              ? 'none'
                              : ordem === 'asc' ? 'ascending' : 'descending'
                          }
                        >
                          <button
                            type="button"
                            className="th-ordenar"
                            onClick={() => alternarOrdenacao(coluna.campo)}
                            title={`Ordenar por ${coluna.titulo}`}
                          >
                            {coluna.titulo}
                            <span aria-hidden="true">
                              {ordenarPor === coluna.campo ? (ordem === 'asc' ? ' ▲' : ' ▼') : ' ↕'}
                            </span>
                          </button>
                        </th>
                      ))}
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
                    onClick={() => trocarPagina(1)}
                    aria-label="Primeira página"
                  >
                    « Primeira
                  </button>
                  <button
                    type="button"
                    disabled={resultado.pagina <= 1}
                    onClick={() => trocarPagina(resultado.pagina - 1)}
                  >
                    Anterior
                  </button>
                  <form
                    className="paginacao-ir"
                    onSubmit={evento => {
                      evento.preventDefault()
                      const alvo = Math.min(
                        Math.max(parseInt(paginaDigitada, 10) || 1, 1),
                        resultado.total_paginas
                      )
                      if (alvo !== resultado.pagina) trocarPagina(alvo)
                      else setPaginaDigitada(String(alvo))
                    }}
                  >
                    <label>
                      Página{' '}
                      <input
                        type="number"
                        min={1}
                        max={resultado.total_paginas}
                        value={paginaDigitada}
                        aria-label="Número da página"
                        onChange={evento => setPaginaDigitada(evento.target.value)}
                      />
                    </label>
                    <span>de {resultado.total_paginas}</span>
                    <button type="submit">Ir</button>
                  </form>
                  <button
                    type="button"
                    disabled={resultado.pagina >= resultado.total_paginas}
                    onClick={() => trocarPagina(resultado.pagina + 1)}
                  >
                    Próxima
                  </button>
                  <button
                    type="button"
                    disabled={resultado.pagina >= resultado.total_paginas}
                    onClick={() => trocarPagina(resultado.total_paginas)}
                    aria-label="Última página"
                  >
                    Última »
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