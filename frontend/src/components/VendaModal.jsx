import { useEffect, useId, useState } from 'react'
import { MdClose, MdShoppingCartCheckout } from 'react-icons/md'

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

function VendaModal({ produto, onFechar, onConfirmar }) {
  const [quantidade, setQuantidade] = useState('1')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState('')
  const tituloId = useId()
  const estoque = Number(produto.quant_estoque)
  const numero = Number(quantidade)
  const quantidadeValida = Number.isInteger(numero) && numero >= 1 && numero <= estoque

  useEffect(() => {
    function aoPressionarTecla(evento) {
      if (evento.key === 'Escape' && !enviando) onFechar()
    }

    window.addEventListener('keydown', aoPressionarTecla)
    return () => window.removeEventListener('keydown', aoPressionarTecla)
  }, [enviando, onFechar])

  async function enviar(evento) {
    evento.preventDefault()
    if (!quantidadeValida || enviando) return

    setErro('')
    setEnviando(true)

    try {
      await onConfirmar(produto.id, numero)
    } catch (falha) {
      setErro(falha.message || 'Não foi possível registrar a venda.')
      setEnviando(false)
    }
  }

  return (
    <div
      className="modal-overlay"
      onMouseDown={evento => {
        if (evento.target === evento.currentTarget && !enviando) onFechar()
      }}
    >
      <section
        className="modal-venda"
        role="dialog"
        aria-modal="true"
        aria-labelledby={tituloId}
      >
        <header className="modal-header">
          <div>
            <h2 id={tituloId}>Registrar venda</h2>
            <p>Confirme a quantidade antes de registrar.</p>
          </div>
          <button
            className="modal-fechar"
            type="button"
            aria-label="Fechar"
            disabled={enviando}
            onClick={onFechar}
          >
            <MdClose size={20} />
          </button>
        </header>

        <form className="venda-form" onSubmit={enviar}>
          <div className="venda-produto-resumo">
            <strong>{produto.nome}</strong>
            <span>Preço unitário: {moeda.format(Number(produto.preco))}</span>
            <span>Em estoque: <b>{estoque} unidades</b></span>
          </div>

          <label htmlFor="quantidade-venda">Quantidade a vender</label>
          <input
            id="quantidade-venda"
            type="number"
            min="1"
            max={estoque}
            step="1"
            required
            autoFocus
            value={quantidade}
            disabled={enviando}
            onChange={evento => setQuantidade(evento.target.value)}
          />

          {quantidade !== '' && !quantidadeValida && (
            <p className="venda-erro" role="alert">
              Informe uma quantidade inteira entre 1 e {estoque}.
            </p>
          )}
          {erro && <p className="venda-erro" role="alert">{erro}</p>}

          <div className="venda-total">
            <span>Total estimado</span>
            <strong>{moeda.format(quantidadeValida ? numero * Number(produto.preco) : 0)}</strong>
          </div>

          <div className="botoes-form">
            <button
              type="button"
              className="botao-cancelar"
              onClick={onFechar}
              disabled={enviando}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="botao-salvar venda-confirmar"
              disabled={!quantidadeValida || enviando}
            >
              <MdShoppingCartCheckout size={18} />
              {enviando ? 'Registrando...' : 'Confirmar venda'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

export default VendaModal
