import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [produtos, setProdutos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [novoProduto, setNovoProduto] = useState({
    nome: '',
    preco: '',
    quant_estoque: '',
    validade: '',
    codigo_barras: '',
    categoria: '',
    peso: ''
  })
  const [produtoEditando, setProdutoEditando] = useState(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/produto')
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error('Erro ao buscar produtos')
        }

        return resposta.json()
      })
      .then((dados) => {
        setProdutos(dados)
      })
      .catch((erro) => {
        setErro(erro.message)
      })
      .finally(() => {
        setCarregando(false)
      })
  }, [])

  function atualizarCampo(evento) {
    const { name, value } = evento.target

    setNovoProduto({
      ...novoProduto,
      [name]: value
    })
  }

  function salvarProduto() {
    const produtoParaEnviar = {
      ...novoProduto,
      preco: Number(novoProduto.preco),
      quant_estoque: Number(novoProduto.quant_estoque),
      peso: Number(novoProduto.peso)
    }

    const url = produtoEditando
      ? `http://127.0.0.1:8000/produto/${produtoEditando}`
      : 'http://127.0.0.1:8000/produto/criar'

    const metodo = produtoEditando ? 'PUT' : 'POST'

    fetch(url, {
      method: metodo,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(produtoParaEnviar)
    })
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error('Erro ao salvar produto')
        }

        return resposta.json()
      })
      .then((produtoSalvo) => {
        if (produtoEditando) {
          setProdutos(
            produtos.map((produto) =>
              produto.id === produtoEditando
                ? produtoSalvo
                : produto
            )
          )
        } else {
          setProdutos([...produtos, produtoSalvo])
        }

        limparFormulario()
      })
      .catch((erro) => {
        alert(erro.message)
      })
  }

  function editarProduto(produto) {
    setProdutoEditando(produto.id)

    setNovoProduto({
      nome: produto.nome,
      preco: produto.preco,
      quant_estoque: produto.quant_estoque,
      validade: produto.validade,
      codigo_barras: produto.codigo_barras,
      categoria: produto.categoria,
      peso: produto.peso
    })

    setMostrarFormulario(true)
  }

  function limparFormulario() {
    setNovoProduto({
      nome: '',
      preco: '',
      quant_estoque: '',
      validade: '',
      codigo_barras: '',
      categoria: '',
      peso: ''
    })

    setProdutoEditando(null)
    setMostrarFormulario(false)
  }

  function excluirProduto(id) {
    const confirmar = window.confirm(
      'Tem certeza que deseja excluir este produto?'
    )

    if (!confirmar) {
      return
    }

    fetch(`http://127.0.0.1:8000/produto/${id}`, {
      method: 'DELETE'
    })
      .then((resposta) => {
        if (!resposta.ok) {
          throw new Error('Erro ao excluir produto')
        }

        setProdutos(
          produtos.filter((produto) => produto.id !== id)
        )
      })
      .catch((erro) => {
        alert(erro.message)
      })
  }

  return (
    <div>
      <h1>Sistema de Produtos</h1>

      <button onClick={() => setMostrarFormulario(true)}>
        Novo Produto
      </button>

      {mostrarFormulario && (
        <div className="formulario">
          <h2>
            {produtoEditando ? 'Editar Produto' : 'Novo Produto'}
          </h2>

          <input
            type="text"
            name="nome"
            placeholder="Nome"
            value={novoProduto.nome}
            onChange={atualizarCampo}
          />

          <input
            type="number"
            name="preco"
            placeholder="Preço"
            step="0.01"
            value={novoProduto.preco}
            onChange={atualizarCampo}
          />

          <input
            type="number"
            name="quant_estoque"
            placeholder="Quantidade em estoque"
            value={novoProduto.quant_estoque}
            onChange={atualizarCampo}
          />

          <input
            type="text"
            name="validade"
            placeholder="Validade"
            value={novoProduto.validade}
            onChange={atualizarCampo}
          />

          <input
            type="text"
            name="codigo_barras"
            placeholder="Código de barras"
            value={novoProduto.codigo_barras}
            onChange={atualizarCampo}
          />

          <input
            type="text"
            name="categoria"
            placeholder="Categoria"
            value={novoProduto.categoria}
            onChange={atualizarCampo}
          />

          <input
            type="number"
            name="peso"
            placeholder="Peso"
            step="0.01"
            value={novoProduto.peso}
            onChange={atualizarCampo}
          />

          <div className="botoes-formulario">
            <button onClick={salvarProduto}>
              {produtoEditando ? 'Atualizar' : 'Salvar'}
            </button>

            <button onClick={limparFormulario}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      <h2>Produtos</h2>

      {carregando && <p>Carregando produtos...</p>}

      {erro && <p>{erro}</p>}

      {!carregando && !erro && (
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
            {produtos.map((produto) => (
              <tr key={produto.id}>
                <td>{produto.id}</td>
                <td>{produto.nome}</td>
                <td>R$ {produto.preco.toFixed(2)}</td>
                <td>{produto.quant_estoque}</td>
                <td>{produto.validade}</td>
                <td>{produto.codigo_barras}</td>
                <td>{produto.categoria}</td>
                <td>{produto.peso}</td>
                <td>
                  <button onClick={() => editarProduto(produto)}>
                    Editar
                  </button>

                  <button onClick={() => excluirProduto(produto.id)}>
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default App