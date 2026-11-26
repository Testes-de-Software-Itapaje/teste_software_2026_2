import { useEffect, useId, useRef, useState } from 'react'
import { MdClose, MdShoppingCartCheckout } from 'react-icons/md'

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

function VendaModal({ produtos, onFechar, onConfirmar }) {
  const [quantidades, setQuantidades] = useState({})
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState('')
  const modalRef = useRef(null)
  const tituloId = useId()

  const itens = produtos.map(produto => {
    const quantidade = quantidades[produto.id] ?? '1'
    const numero = Number(quantidade)
    const valida = Number.isInteger(numero) && numero >= 1 && numero <= produto.quant_estoque
    return { produto, quantidade, numero, valida }
  })
  const vendaValida = itens.length > 0 && itens.every(item => item.valida)
  const total = itens.reduce((soma, { produto, numero }) =>
    soma + Math.round(produto.preco * numero * 100), 0) / 100

  useEffect(() => {
    const modal = modalRef.current
    modal.showModal()
    return () => modal.close()
  }, [])

  async function enviar(evento) {
    evento.preventDefault()
    if (!vendaValida || enviando) return

    setErro('')
    setEnviando(true)
    try {
      await onConfirmar(itens.map(({ produto, numero }) => ({
        produto_id: produto.id,
        quantidade: numero
      })))
    } catch (falha) {
      setErro(falha.message || 'Não foi possível registrar a venda.')
      setEnviando(false)
    }
  }

  return (
    <dialog
      ref={modalRef}
      className="modal-venda"
      aria-labelledby={tituloId}
      onCancel={evento => {
        evento.preventDefault()
        if (!enviando) onFechar()
      }}
      onMouseDown={evento => {
        if (evento.target === evento.currentTarget && !enviando) onFechar()
      }}
    >
      <header className="modal-header">
        <div>
          <h2 id={tituloId}>Registrar venda</h2>
          <p>Confira a quantidade de cada produto selecionado.</p>
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
        {itens.map(({ produto, quantidade, valida }, indice) => {
          const campoId = `${tituloId}-quantidade-${produto.id}`
          return (
            <div key={produto.id} className="venda-produto-resumo">
              <strong id={`${campoId}-nome`}>{produto.nome} (#{produto.id})</strong>
              <span>Preço unitário: {moeda.format(produto.preco)}</span>
              <span>Em estoque: <b>{produto.quant_estoque} unidades</b></span>
              <label id={`${campoId}-rotulo`} htmlFor={campoId}>Quantidade a vender</label>
              <input
                id={campoId}
                aria-labelledby={`${campoId}-rotulo ${campoId}-nome`}
                type="number"
                min="1"
                max={produto.quant_estoque}
                step="1"
                required
                autoFocus={indice === 0}
                value={quantidade}
                disabled={enviando}
                onChange={evento => {
                  const valor = evento.target.value
                  setQuantidades(atuais => ({ ...atuais, [produto.id]: valor }))
                }}
              />
              {quantidade !== '' && !valida && (
                <p className="venda-erro" role="alert">
                  Informe uma quantidade inteira entre 1 e {produto.quant_estoque}.
                </p>
              )}
            </div>
          )
        })}
        {erro && <p className="venda-erro" role="alert">{erro}</p>}

        <div className="venda-total">
          <span>Total estimado</span>
          <strong>{vendaValida ? moeda.format(total) : '—'}</strong>
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
            disabled={!vendaValida || enviando}
          >
            <MdShoppingCartCheckout size={18} />
            {enviando ? 'Registrando...' : 'Confirmar venda'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

export default VendaModal