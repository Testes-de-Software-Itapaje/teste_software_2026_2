# API de Produtos

Este projeto é uma API REST desenvolvida em Python com FastAPI para gerenciar produtos em um banco de dados SQLite.

A estrutura do projeto inclui:

- `main.py`: aplicação principal com os endpoints da API
- `db/`: configuração do banco e modelos de tabela
- `entity/`: modelos de dados usados pela aplicação
- `tests/`: testes automatizados
- `requirements.txt`: dependências do projeto

## Requisitos

Antes de iniciar, verifique se você possui:

- Python 3.10 ou superior
- pip instalado
- Git (opcional, para clonar o repositório)
- Editor ou IDE de sua preferência (VS Code, PyCharm, etc.)

## Clonando o projeto

Para clonar o repositório correto, execute:

```bash
git clone https://github.com/Testes-de-Software-Itapaje/teste_software_2026_2.git
cd novo_testes_por_niveis
```

Se o código já estiver baixado localmente, basta entrar na pasta do projeto:

```bash
cd caminho/para/novo_testes_por_niveis
```

## Instalando as dependências

O arquivo `requirements.txt` contém todas as bibliotecas necessárias para rodar o projeto. Para instalá-las, use:

```bash
pip install -r requirements.txt
```

Isso instalará dependências como:

- fastapi
- uvicorn
- sqlalchemy
- pydantic
- pytest
- starlette
- typing-extensions

Se a instalação falhar por algum motivo, você pode forçar a reinstalação:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Como rodar a aplicação

No diretório raiz do projeto, execute:

```bash
uvicorn main:app --reload
```

### O que acontece?

- O servidor FastAPI será inicializado
- A aplicação estará disponível localmente
- O banco SQLite será criado automaticamente ao iniciar o app

### Endereços locais

Após iniciar a aplicação, acesse:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Redoc: http://127.0.0.1:8000/redoc

## Verificando se a API está funcionando

Você pode testar o endpoint de saúde:

```bash
curl http://127.0.0.1:8000/health
```

Resposta esperada:

```json
[200, "ok"]
```

## Endpoints da API

### 1) Verificar saúde

- Método: `GET`
- Rota: `/health`

Exemplo:

```bash
curl http://127.0.0.1:8000/health
```

### 2) Criar produto

- Método: `POST`
- Rota: `/produto/criar`
- Corpo esperado:

```json
{
  "nome": "Notebook",
  "descricao": "Notebook gamer",
  "preco": 4999.99
}
```

Exemplo com `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/produto/criar" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Notebook",
    "descricao": "Notebook gamer",
    "preco": 4999.99
  }'
```

### 3) Buscar produto por ID

- Método: `GET`
- Rota: `/produto/{produto_id}`

Exemplo:

```bash
curl http://127.0.0.1:8000/produto/1
```

### 4) Listar todos os produtos

- Método: `GET`
- Rota: `/produto`

Exemplo:

```bash
curl http://127.0.0.1:8000/produto
```

### 5) Atualizar produto

- Método: `PUT`
- Rota: `/produto/{produto_id}`
- Corpo esperado:

```json
{
  "nome": "Notebook Atualizado",
  "descricao": "Notebook para desenvolvimento",
  "preco": 4299.90
}
```

Exemplo:

```bash
curl -X PUT "http://127.0.0.1:8000/produto/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Notebook Atualizado",
    "descricao": "Notebook para desenvolvimento",
    "preco": 4299.90
  }'
```

### 6) Deletar produto

- Método: `DELETE`
- Rota: `/produto/{produto_id}`

Exemplo:

```bash
curl -X DELETE http://127.0.0.1:8000/produto/1
```

## Documentação interativa

Depois de iniciar a aplicação, acesse a documentação Swagger em:

```text
http://127.0.0.1:8000/docs
```

Nela você pode testar todos os endpoints diretamente no navegador sem precisar usar o terminal.

## Executando os testes

Para rodar a suíte de testes automatizados:

```bash
pytest
```

Se quiser rodar apenas um arquivo de teste específico:

```bash
pytest tests/test_produto.py
```

Se quiser ver detalhes da execução:

```bash
pytest -v
```

## Estrutura do banco de dados

O projeto usa SQLite e o banco é gerado automaticamente ao iniciar a aplicação. O arquivo local usado é:

```text
produtos.db
```

## Observações importantes

- O banco é criado automaticamente na inicialização da API.
- O ambiente virtual é opcional, mas altamente recomendado.
- A API usa FastAPI, então erros e validações são exibidos automaticamente pela documentação interativa.
- Caso o servidor não suba, verifique se todas as dependências foram instaladas corretamente com `pip install -r requirements.txt`.

## Dicas de troubleshooting

### O comando `uvicorn` não é encontrado

Certifique-se de que o ambiente virtual foi ativado e que as dependências foram instaladas:

```bash
pip install -r requirements.txt
```

### O módulo `fastapi` não existe

Isso geralmente significa que a instalação não foi concluída. Execute novamente:

```bash
pip install -r requirements.txt
```

### O banco de dados não foi criado

Verifique se a aplicação foi iniciada com:

```bash
uvicorn main:app --reload
```

A criação do banco ocorre automaticamente na inicialização do app.

## Resumo rápido

Se você quiser executar tudo em um único fluxo, use:

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Depois disso, abra:

```text
http://127.0.0.1:8000/docs
```

para testar a API.
