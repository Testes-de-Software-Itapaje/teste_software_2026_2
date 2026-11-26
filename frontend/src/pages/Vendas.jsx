import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MdArrowBack, MdReceiptLong } from 'react-icons/md'

import { listarVendas } from '../services/vendaService'
import { listarProdutos } from '../services/produtoService'

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})
const dataHora = new Intl.DateTimeFormat('pt-BR', {
  dateStyle: 'short',
  timeStyle: 'short'
})

function Vendas() {
  const [vendas, setVendas] = useState([])
  const [nomes, setNomes] = useState({})
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')

  useEffect(() => {
    let ativo = true

    async function carregar() {
      try {
        const vendasRecebidas = await listarVendas()
        if (!ativo) return
        setVendas(vendasRecebidas)

        // Nomes são resolvidos separadamente porque GET /venda
        // devolve produto_id, mas não o nome do produto.
        try {
          const produtos = await listarProdutos()
          if (ativo) {
            setNomes(Object.fromEntries(produtos.map(p => [p.id, p.nome])))
          }
        } catch {
          // Histórico continua disponível mesmo sem carregar nomes.
        }
      } catch (falha) {
        if (ativo) setErro(falha.message)
      } finally {
        if (ativo) setCarregando(false)
      }
    }

    carregar()
    return () => { ativo = false }
  }, [])

  const totalFaturado = vendas.reduce((soma, venda) => soma + Number(venda.valor_total), 0)
  const unidadesVendidas = vendas.reduce((soma, venda) => soma + Number(venda.quantidade), 0)

  return (
    <div className="sistema">
      <main className="conteudo">
        <header className="topo">
          <div>
            <h1><MdReceiptLong size={30} /> Histórico de Vendas</h1>
            <p>Consulte as vendas registradas no sistema.</p>
          </div>
          <Link to="/produtos" className="botao-voltar">
            <MdArrowBack size={18} /> Produtos
          </Link>
        </header>

        {erro && <p className="venda-erro aviso-erro" role="alert">{erro}</p>}
        {!carregando && !erro && (
          <div className="resumo-vendas">
            <div><span>Vendas registradas</span><strong>{vendas.length}</strong></div>
            <div><span>Unidades vendidas</span><strong>{unidadesVendidas}</strong></div>
            <div><span>Valor total</span><strong>{moeda.format(totalFaturado)}</strong></div>
          </div>
        )}

        <section className="card-tabela">
          <div className="tabela-header">
            <span>Registros de vendas</span>
          </div>
          {carregando ? (
            <div className="estado">Carregando vendas...</div>
          ) : vendas.length === 0 ? (
            <div className="sem-produtos">
              {erro ? 'Não foi possível carregar o histórico.' : 'Nenhuma venda registrada até agora.'}
            </div>
          ) : (
            <div className="tabela-container">
              <table className="tabela-vendas">
                <thead>
                  <tr>
                    <th>Venda</th>
                    <th>Produto</th>
                    <th>Quantidade</th>
                    <th>Preço unitário</th>
                    <th>Total</th>
                    <th>Data e hora</th>
                  </tr>
                </thead>
                <tbody>
                  {vendas.map(venda => (
                    <tr key={venda.id}>
                      <td>#{venda.id}</td>
                      <td>{nomes[venda.produto_id] || `Produto #${venda.produto_id}`}</td>
                      <td>{venda.quantidade}</td>
                      <td>{moeda.format(Number(venda.preco_unitario))}</td>
                      <td>{moeda.format(Number(venda.valor_total))}</td>
                      <td>{dataHora.format(new Date(venda.data_venda))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default Vendas
