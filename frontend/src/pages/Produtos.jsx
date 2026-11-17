import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  MdModeEdit,
  MdDelete,
  MdChat,
  MdReceiptLong,
  MdShoppingCartCheckout
} from 'react-icons/md'

import { listarProdutos, excluirProduto } from '../services/produtoService'
import { registrarVenda } from '../services/vendaService'
import VendaModal from '../components/VendaModal'

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

function Produtos() {
  const [produtos, setProdutos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [busca, setBusca] = useState('')
  const [vendaAtual, setVendaAtual] = useState(null)
  const [aviso, setAviso] = useState('')

  const carregarProdutos = useCallback(async () => {
    setCarregando(true)
    setErro('')
    try {
      const dados = await listarProdutos()
      setProdutos(dados)
    } catch (falha) {
      setErro(falha.message)
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregarProdutos()
  }, [carregarProdutos])

  async function handleExcluir(id) {
    const confirmar = window.confirm('Tem certeza que deseja excluir este produto?')
    if (!confirmar) return

    try {
      await excluirProduto(id)
      setProdutos(atuais => atuais.filter(produto => produto.id !== id))
      setAviso('Produto excluído com sucesso.')
    } catch (falha) {
      setErro(falha.message)
    }
  }

  async function handleConfirmarVenda(produtoId, quantidade) {
    const resultado = await registrarVenda(produtoId, quantidade)
    setVendaAtual(null)
    setAviso(`Venda #${resultado.id} registrada! Restam ${resultado.estoque_restante} unidades de ${resultado.produto_nome}.`)
    await carregarProdutos()
  }

  const termo = busca.trim().toLocaleLowerCase('pt-BR')
  const produtosFiltrados = produtos.filter(produto =>
    produto.nome?.toLocaleLowerCase('pt-BR').includes(termo) ||
    produto.codigo_barras?.toLocaleLowerCase('pt-BR').includes(termo) ||
    produto.categoria?.toLocaleLowerCase('pt-BR').includes(termo)
  )

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
            value={busca}
            onChange={evento => setBusca(evento.target.value)}
          />
        </div>

        {aviso && <p className="aviso-sucesso" role="status">{aviso}</p>}
        {erro && <p className="venda-erro aviso-erro" role="alert">{erro}</p>}

        <section className="card-tabela">
          <div className="tabela-header">
            <span>Total: {produtosFiltrados.length} produtos</span>
          </div>
          {carregando ? (
            <div className="estado">Carregando produtos...</div>
          ) : (
            <>
              <div className="tabela-container">
                <table>
                  <thead>
                    <tr>
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
                    {produtosFiltrados.map(produto => (
                      <tr key={produto.id}>
                        <td>{produto.id}</td>
                        <td><div className="produto-nome">{produto.nome}</div></td>
                        <td>{moeda.format(Number(produto.preco))}</td>
                        <td>
                          <span className={produto.quant_estoque === 0 ? 'estoque-zerado' : 'estoque-disponivel'}>
                            {produto.quant_estoque}
                          </span>
                        </td>
                        <td>{produto.validade}</td>
                        <td>{produto.codigo_barras}</td>
                        <td><span className="categoria">{produto.categoria}</span></td>
                        <td>{produto.peso}</td>
                        <td>
                          <div className="acoes">
                            <button
                              type="button"
                              className="botao-vender"
                              disabled={Number(produto.quant_estoque) < 1}
                              onClick={() => {
                                setAviso('')
                                setVendaAtual(produto)
                              }}
                              title={produto.quant_estoque < 1 ? 'Sem estoque' : `Vender ${produto.nome}`}
                            >
                              <MdShoppingCartCheckout size={18} /> Vender
                            </button>
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
              {produtosFiltrados.length === 0 && (
                <div className="sem-produtos">Nenhum produto encontrado.</div>
              )}
            </>
          )}
        </section>
      </main>
      {vendaAtual && (
        <VendaModal
          produto={vendaAtual}
          onFechar={() => setVendaAtual(null)}
          onConfirmar={handleConfirmarVenda}
        />
      )}
    </div>
  )
}

export default Produtos
