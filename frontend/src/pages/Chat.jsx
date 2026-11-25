import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  MdArrowBack,
  MdSend,
  MdSmartToy,
  MdDeleteSweep,
  MdAttachFile,
  MdClose
} from 'react-icons/md'

import { enviarMensagem, enviarAnexo } from '../services/chatService'

const EXTENSOES_ACEITAS = '.csv,.xlsx,.pdf,.txt'

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL'
})

const SUGESTOES = [
  
]


function formatarTexto(texto) {
  return texto.split(/\*\*(.+?)\*\*/g).map((parte, indice) =>
    indice % 2 === 1
      ? <strong key={indice}>{parte}</strong>
      : parte
  )
}

function Chat() {
  const [mensagens, setMensagens] = useState([])
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [anexo, setAnexo] = useState(null)

  const proximoId = useRef(1)
  const listaRef = useRef(null)
  const campoRef = useRef(null)
  const arquivoRef = useRef(null)

  useEffect(() => {
    const lista = listaRef.current

    if (lista) {
      lista.scrollTo({ top: lista.scrollHeight, behavior: 'smooth' })
    }
  }, [mensagens, enviando])

  function adicionarMensagem(autor, conteudo, erro = false, extras = {}) {
    const id = proximoId.current++

    setMensagens(atuais => [...atuais, { id, autor, conteudo, erro, ...extras }])
  }

  function handleEscolherArquivo(evento) {
    const arquivo = evento.target.files?.[0]

    if (arquivo) setAnexo(arquivo)

    evento.target.value = ''
  }

  async function importarAnexo() {
    if (!anexo || enviando) return

    const arquivo = anexo

    adicionarMensagem('usuario', `Anexo: ${arquivo.name}`)
    setAnexo(null)
    setEnviando(true)

    try {
      const resultado = await enviarAnexo(arquivo)

      adicionarMensagem('assistente', resultado.resposta, false, {
        criados: resultado.criados,
        ignorados: resultado.ignorados
      })
    } catch (erro) {
      adicionarMensagem('assistente', erro.message, true)
    } finally {
      setEnviando(false)
      campoRef.current?.focus()
    }
  }

  async function enviar(conteudo) {
    const pergunta = conteudo.trim()

    if (!pergunta || enviando) return

    adicionarMensagem('usuario', pergunta)
    setTexto('')
    setEnviando(true)

    if (campoRef.current) {
      campoRef.current.style.height = 'auto'
    }

    try {
      const resposta = await enviarMensagem(pergunta)

      adicionarMensagem('assistente', resposta || 'Sem resposta do modelo.')
    } catch (erro) {
      adicionarMensagem('assistente', erro.message, true)
    } finally {
      setEnviando(false)
      campoRef.current?.focus()
    }
  }

  function handleSubmit(evento) {
    evento.preventDefault()

    if (anexo) {
      importarAnexo()
      return
    }

    enviar(texto)
  }

  function handleTeclado(evento) {
    if (
      evento.key === 'Enter' &&
      !evento.shiftKey &&
      !evento.nativeEvent.isComposing
    ) {
      evento.preventDefault()

      if (anexo) importarAnexo()
      else enviar(texto)
    }
  }

  function handleChange(evento) {
    const campo = evento.target

    setTexto(campo.value)

    campo.style.height = 'auto'
    campo.style.height = `${Math.min(campo.scrollHeight, 120)}px`
  }

  return (
    <div className="sistema">

      <main className="conteudo">

        <header className="topo">

          <div>
            <h1>
              Assistente Virtual
            </h1>

            <p>
              Pergunte sobre produtos, preços, estoque, validade e categorias.
            </p>
          </div>

          <Link to="/produtos" className="botao-voltar">
            <MdArrowBack size={18} />
            Produtos
          </Link>

        </header>

        <section className="card-chat">

          <div className="chat-header">

            <div className="chat-titulo">
              

              <div>
                <strong>Assistente de estoque</strong>
                <span>Responde com base nos produtos cadastrados</span>
              </div>
            </div>

            <button
              type="button"
              className="chat-limpar"
              onClick={() => setMensagens([])}
              disabled={mensagens.length === 0 || enviando}
              title="Limpar conversa"
            >
              <MdDeleteSweep size={18} />
              Limpar
            </button>

          </div>

          <div className="chat-mensagens" ref={listaRef}>

            {mensagens.length === 0 && (
              <div className="chat-vazio">

                <h2>Como posso ajudar?</h2>

                <p>
                  Faça uma pergunta sobre os produtos do sistema ou
                  escolha uma sugestão.
                </p>

                <div className="chat-sugestoes">
                  {SUGESTOES.map(sugestao => (
                    <button
                      key={sugestao}
                      type="button"
                      className="chat-sugestao"
                      onClick={() => enviar(sugestao)}
                      disabled={enviando}
                    >
                      {sugestao}
                    </button>
                  ))}
                </div>

              </div>
            )}

            {mensagens.map(mensagem => (
              <div
                key={mensagem.id}
                className={`chat-linha ${mensagem.autor}`}
              >

                <div
                  className={
                    `chat-balao ${mensagem.autor}` +
                    (mensagem.erro ? ' erro' : '')
                  }
                >
                  {formatarTexto(mensagem.conteudo)}

                  {mensagem.criados?.length > 0 && (
                    <>
                      <span className="chat-importados-titulo">Cadastrados</span>
                      <ul className="chat-importados">
                        {mensagem.criados.map(produto => (
                          <li key={produto.id}>
                            <strong>{produto.nome}</strong>
                            {' - '}{moeda.format(Number(produto.preco))}
                            {' - '}{produto.quant_estoque} un.
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  {mensagem.ignorados?.length > 0 && (
                    <>
                      <span className="chat-importados-titulo">Ignorados</span>
                      <ul className="chat-importados chat-ignorados">
                        {mensagem.ignorados.map(item => (
                          <li key={item.item}>
                            Item {item.item}{item.nome ? ` (${item.nome})` : ''}: {item.motivo}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  {mensagem.criados && (
                    <Link to="/produtos" className="chat-ver-produtos">
                      Ver lista de produtos
                    </Link>
                  )}
                </div>
              </div>
            ))}

            {enviando && (
              <div className="chat-linha assistente">

                <div className="chat-balao assistente chat-digitando">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}

          </div>

          {anexo && (
            <div className="chat-anexo">
              <MdAttachFile size={16} />
              <span>{anexo.name}</span>
              <button
                type="button"
                onClick={() => setAnexo(null)}
                disabled={enviando}
                aria-label="Remover anexo"
                title="Remover anexo"
              >
                <MdClose size={16} />
              </button>
            </div>
          )}

          <form className="chat-form" onSubmit={handleSubmit}>

            <input
              ref={arquivoRef}
              type="file"
              accept={EXTENSOES_ACEITAS}
              onChange={handleEscolherArquivo}
              hidden
            />

            <button
              type="button"
              className="chat-anexar"
              onClick={() => arquivoRef.current?.click()}
              disabled={enviando}
              aria-label="Anexar documento"
              title="Anexar documento (.csv, .xlsx, .pdf, .txt)"
            >
              <MdAttachFile size={20} />
            </button>

            <textarea
              ref={campoRef}
              rows={1}
              placeholder={anexo ? 'Pressione Enviar para importar o documento' : 'Digite sua pergunta...'}
              value={texto}
              disabled={Boolean(anexo)}
              onChange={handleChange}
              onKeyDown={handleTeclado}
              aria-label="Mensagem para o assistente"
              autoFocus
            />

            <button
              type="submit"
              className="chat-enviar"
              disabled={enviando || (!anexo && texto.trim() === '')}
              aria-label="Enviar mensagem"
              title="Enviar"
            >
              <MdSend size={20} />
            </button>

          </form>

        </section>

      </main>

    </div>
  )
}

export default Chat
