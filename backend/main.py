from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db.database import Base, engine, get_db
from entity.produto_model import ProdutoCreate, ProdutoRead
from db.produto_schema import ProdutoDB
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    """Cria as tabelas do banco ao iniciar a aplicação."""
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def main():
    """Retorna uma resposta simples de verificação de saúde."""
    return 200, "ok"

@app.post("/produto/criar", response_model=ProdutoRead)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    """Persisto um novo produto no banco de dados."""
    produto_db = ProdutoDB(**produto.model_dump())
    db.add(produto_db)
    db.commit()
    db.refresh(produto_db)
    return produto_db


@app.get("/produto/{produto_id}", response_model=ProdutoRead)
def buscar_produto(produto_id: int, db: Session = Depends(get_db)):
    """Recupera um produto pelo id no banco de dados."""
    produto = db.query(ProdutoDB).filter(ProdutoDB.id == produto_id).first()
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


@app.get("/produto", response_model=list[ProdutoRead])
def listar_produtos(db: Session = Depends(get_db)):
    """Lista todos os produtos armazenados."""
    return db.query(ProdutoDB).all()


@app.put("/produto/{produto_id}", response_model=ProdutoRead)
def atualizar_produto(produto_id: int, produto: ProdutoCreate, db: Session = Depends(get_db)):
    """Atualiza um produto existente."""
    produto_db = db.query(ProdutoDB).filter(ProdutoDB.id == produto_id).first()
    if produto_db is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for campo, valor in produto.model_dump().items():
        setattr(produto_db, campo, valor)
    db.commit()
    db.refresh(produto_db)
    return produto_db


@app.delete("/produto/{produto_id}")
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    """Remove um produto do banco de dados."""
    produto = db.query(ProdutoDB).filter(ProdutoDB.id == produto_id).first()
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(produto)
    db.commit()
    return {"detail": "Produto removido"}