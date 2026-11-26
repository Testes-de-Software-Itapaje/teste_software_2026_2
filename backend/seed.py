"""Popula o banco com produtos de supermercado.

Uso (rode de dentro da pasta backend/, a mesma de onde sobe o uvicorn):

    python seed.py            # adiciona os produtos que ainda não existem
    python seed.py --limpar   # apaga TODOS os produtos antes de popular

Detalhes:
- É idempotente: rodar duas vezes não duplica nada (a chave é o código de
  barras, que é gerado de forma estável a partir do nome do produto).
- Os códigos de barras são EAN-13 válidos (prefixo 789 = Brasil), mas
  FICTÍCIOS: não correspondem a produtos reais.
- Peso em gramas (1 L de líquido ≈ 1000 g), como no formulário do sistema.
- As validades são calculadas a partir do dia em que o script roda. Parte
  dos perecíveis nasce perto de vencer (ou já vencida) e parte do catálogo
  com estoque baixo ou zerado, para dar o que perguntar ao chat.
"""
import argparse
import hashlib
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import text

from db.database import Base, SessionLocal, engine
from db.produto_schema import ProdutoDB

# Perecível = validade base de até 30 dias.
LIMITE_PERECIVEL_DIAS = 30

# categoria -> [(nome, preço em R$, peso em g, validade base em dias)]
CATALOGO = {
    "Mercearia": [
        ("Arroz Branco Tipo 1 5kg", 27.90, 5000, 540),
        ("Arroz Integral 1kg", 8.90, 1000, 365),
        ("Feijão Carioca 1kg", 8.49, 1000, 365),
        ("Feijão Preto 1kg", 9.29, 1000, 365),
        ("Macarrão Espaguete 500g", 4.79, 500, 540),
        ("Macarrão Parafuso 500g", 4.79, 500, 540),
        ("Açúcar Refinado 1kg", 5.49, 1000, 720),
        ("Açúcar Cristal 5kg", 21.90, 5000, 720),
        ("Sal Refinado 1kg", 3.29, 1000, 1095),
        ("Óleo de Soja 900ml", 7.99, 900, 360),
        ("Azeite de Oliva Extra Virgem 500ml", 39.90, 500, 540),
        ("Farinha de Trigo 1kg", 5.99, 1000, 270),
        ("Farinha de Mandioca 500g", 6.49, 500, 270),
        ("Fubá de Milho 500g", 3.99, 500, 270),
        ("Flocão de Milho para Cuscuz 500g", 3.99, 500, 270),
        ("Café Torrado e Moído 500g", 18.90, 500, 270),
        ("Molho de Tomate 340g", 3.49, 340, 540),
        ("Extrato de Tomate 340g", 4.99, 340, 540),
        ("Milho Verde em Conserva 170g", 3.99, 170, 720),
        ("Ervilha em Conserva 170g", 3.99, 170, 720),
        ("Atum em Óleo 170g", 9.99, 170, 900),
        ("Sardinha em Lata 125g", 6.49, 125, 900),
        ("Vinagre de Álcool 750ml", 3.49, 750, 720),
        ("Maionese 500g", 8.99, 500, 270),
        ("Ketchup 380g", 7.49, 380, 360),
        ("Leite Condensado 395g", 6.99, 395, 360),
        ("Creme de Leite UHT 200g", 3.99, 200, 270),
    ],
    "Biscoitos e Snacks": [
        ("Biscoito Cream Cracker 400g", 5.99, 400, 240),
        ("Biscoito Água e Sal 400g", 5.99, 400, 240),
        ("Biscoito Maisena 200g", 3.99, 200, 240),
        ("Biscoito Recheado de Chocolate 130g", 3.49, 130, 240),
        ("Wafer de Chocolate 100g", 3.29, 100, 200),
        ("Batata Chips Original 90g", 8.99, 90, 150),
        ("Salgadinho de Milho 80g", 6.49, 80, 150),
        ("Amendoim Torrado 200g", 5.49, 200, 180),
        ("Pipoca de Micro-ondas 100g", 3.99, 100, 240),
        ("Barra de Cereal 25g", 1.99, 25, 240),
        ("Chocolate ao Leite 90g", 6.99, 90, 270),
        ("Bala de Goma 100g", 4.49, 100, 300),
        ("Cereal Matinal de Milho 300g", 11.90, 300, 300),
        ("Aveia em Flocos 200g", 4.99, 200, 360),
        ("Granola Tradicional 250g", 12.90, 250, 240),
        ("Achocolatado em Pó 400g", 9.49, 400, 360),
    ],
    "Bebidas": [
        ("Água Mineral sem Gás 1,5L", 2.99, 1500, 540),
        ("Água Mineral com Gás 500ml", 2.49, 500, 540),
        ("Refrigerante Cola 2L", 9.49, 2000, 240),
        ("Refrigerante Guaraná 2L", 8.49, 2000, 240),
        ("Refrigerante Laranja 2L", 8.49, 2000, 240),
        ("Suco de Laranja Integral 1L", 12.90, 1000, 120),
        ("Suco de Uva Integral 1L", 14.90, 1000, 360),
        ("Néctar de Pêssego 1L", 6.99, 1000, 300),
        ("Chá Gelado de Limão 1,5L", 7.49, 1500, 240),
        ("Água de Coco 1L", 11.90, 1000, 180),
        ("Isotônico Laranja 500ml", 5.49, 500, 240),
        ("Energético 269ml", 7.99, 269, 360),
        ("Cerveja Pilsen Lata 350ml", 3.99, 350, 180),
        ("Vinho Tinto Suave 750ml", 29.90, 750, 720),
    ],
    "Laticínios e Ovos": [
        ("Leite Integral UHT 1L", 5.29, 1000, 120),
        ("Leite Desnatado UHT 1L", 5.49, 1000, 120),
        ("Leite em Pó Integral 400g", 19.90, 400, 300),
        ("Iogurte Natural 170g", 2.99, 170, 25),
        ("Iogurte de Morango 170g", 3.29, 170, 25),
        ("Iogurte Grego Tradicional 100g", 4.49, 100, 25),
        ("Queijo Mussarela Fatiado 150g", 9.99, 150, 25),
        ("Queijo Prato Fatiado 150g", 10.49, 150, 25),
        ("Queijo Minas Frescal 500g", 22.90, 500, 15),
        ("Queijo Parmesão Ralado 50g", 5.99, 50, 120),
        ("Requeijão Cremoso 200g", 7.99, 200, 30),
        ("Cream Cheese 150g", 9.49, 150, 30),
        ("Manteiga com Sal 200g", 12.90, 200, 90),
        ("Margarina Cremosa 500g", 7.49, 500, 90),
        ("Ovos Brancos Dúzia", 11.90, 600, 28),
        ("Ovos Caipira Dúzia", 16.90, 600, 28),
    ],
    "Frios e Embutidos": [
        ("Presunto Fatiado 200g", 8.99, 200, 20),
        ("Apresuntado Fatiado 200g", 6.99, 200, 20),
        ("Mortadela Fatiada 200g", 5.99, 200, 20),
        ("Peito de Peru Fatiado 200g", 12.90, 200, 20),
        ("Salame Italiano 100g", 11.90, 100, 30),
        ("Bacon Fatiado 250g", 15.90, 250, 30),
        ("Salsicha Hot Dog 500g", 8.49, 500, 30),
    ],
    "Carnes e Aves": [
        ("Peito de Frango 1kg", 19.90, 1000, 7),
        ("Coxa e Sobrecoxa de Frango 1kg", 13.90, 1000, 7),
        ("Carne Moída Bovina 500g", 21.90, 500, 5),
        ("Contrafilé Bovino 1kg", 49.90, 1000, 6),
        ("Alcatra Bovina 1kg", 44.90, 1000, 6),
        ("Patinho Bovino 1kg", 39.90, 1000, 6),
        ("Costela Bovina 1kg", 29.90, 1000, 6),
        ("Linguiça Toscana 500g", 14.90, 500, 10),
        ("Bisteca Suína 1kg", 18.90, 1000, 7),
        ("Filé de Tilápia 500g", 24.90, 500, 4),
    ],
    "Hortifrúti": [
        ("Banana Prata 1kg", 6.99, 1000, 6),
        ("Maçã Fuji 1kg", 9.99, 1000, 14),
        ("Laranja Pera 1kg", 5.99, 1000, 10),
        ("Mamão Papaia 500g", 5.49, 500, 6),
        ("Limão Tahiti 500g", 4.99, 500, 10),
        ("Tomate 1kg", 8.99, 1000, 7),
        ("Cebola 1kg", 5.99, 1000, 20),
        ("Batata Inglesa 1kg", 6.49, 1000, 15),
        ("Cenoura 1kg", 5.49, 1000, 12),
        ("Alho 200g", 7.99, 200, 30),
        ("Alface Crespa Unidade", 3.49, 300, 5),
        ("Brócolis Maço", 6.99, 400, 5),
        ("Mandioca Descascada 500g", 7.49, 500, 8),
    ],
    "Padaria": [
        ("Pão Francês 500g", 8.50, 500, 2),
        ("Pão de Forma Tradicional 500g", 7.99, 500, 12),
        ("Pão de Forma Integral 400g", 8.99, 400, 12),
        ("Pão de Hambúrguer 8un", 8.49, 300, 10),
        ("Bisnaguinha 300g", 6.49, 300, 12),
        ("Bolo de Cenoura 400g", 12.90, 400, 5),
        ("Torrada Salgada 140g", 4.49, 140, 90),
    ],
    "Congelados": [
        ("Pizza Congelada Mussarela 460g", 15.90, 460, 180),
        ("Lasanha Bolonhesa Congelada 600g", 18.90, 600, 180),
        ("Hambúrguer Bovino 672g", 19.90, 672, 180),
        ("Nuggets de Frango 300g", 12.90, 300, 180),
        ("Batata Palito Congelada 1kg", 14.90, 1000, 180),
        ("Pão de Queijo Congelado 1kg", 24.90, 1000, 120),
        ("Mix de Legumes Congelado 300g", 6.99, 300, 240),
        ("Sorvete de Creme 2L", 22.90, 1000, 360),
    ],
    "Limpeza": [
        ("Detergente Líquido 500ml", 2.49, 500, 720),
        ("Sabão em Pó 1,6kg", 19.90, 1600, 720),
        ("Sabão Líquido para Roupas 3L", 34.90, 3000, 720),
        ("Sabão em Barra 5un", 9.99, 1000, 1095),
        ("Amaciante de Roupas 2L", 14.90, 2000, 720),
        ("Água Sanitária 2L", 6.99, 2000, 540),
        ("Desinfetante Lavanda 2L", 8.49, 2000, 720),
        ("Limpador Multiuso 500ml", 5.49, 500, 720),
        ("Desengordurante 500ml", 8.99, 500, 720),
        ("Esponja Multiuso 3un", 4.99, 60, 1095),
        ("Palha de Aço 8un", 3.49, 60, 1095),
        ("Saco de Lixo 50L 10un", 8.99, 150, 1095),
    ],
    "Higiene e Beleza": [
        ("Papel Higiênico Folha Dupla 12 Rolos", 19.90, 1200, 1460),
        ("Creme Dental 90g", 4.49, 90, 720),
        ("Escova Dental Macia", 7.99, 30, 1460),
        ("Enxaguante Bucal 500ml", 15.90, 500, 720),
        ("Fio Dental 50m", 5.99, 30, 1095),
        ("Sabonete em Barra 85g", 2.49, 85, 1095),
        ("Shampoo 350ml", 14.90, 350, 900),
        ("Condicionador 350ml", 14.90, 350, 900),
        ("Desodorante Aerosol 150ml", 13.90, 150, 900),
        ("Absorvente com Abas 8un", 5.99, 80, 1095),
        ("Algodão em Disco 50g", 5.49, 50, 1460),
        ("Cotonete Haste Flexível 75un", 4.49, 40, 1460),
    ],
    "Pet Shop": [
        ("Ração para Cães Adultos 1kg", 17.90, 1000, 360),
        ("Ração para Gatos Adultos 1kg", 21.90, 1000, 360),
        ("Areia Higiênica para Gatos 4kg", 19.90, 4000, 1095),
    ],
}


def calcular_ean13(base12: str) -> str:
    """Acrescenta o dígito verificador a uma base de 12 dígitos."""
    soma = sum(
        int(digito) * (3 if posicao % 2 else 1)
        for posicao, digito in enumerate(base12)
    )
    return base12 + str((10 - soma % 10) % 10)


def gerar_codigo_barras(nome: str) -> str:
    """EAN-13 fictício e estável: o mesmo nome sempre gera o mesmo código."""
    numero = int(hashlib.sha1(nome.encode("utf-8")).hexdigest(), 16) % 10**9
    return calcular_ean13(f"789{numero:09d}")


def montar_produto(nome, preco, peso, validade_base, categoria, hoje):
    # Seed por nome: resultado estável entre execuções no mesmo dia.
    sorteio = random.Random(nome)
    perecivel = validade_base <= LIMITE_PERECIVEL_DIAS

    if perecivel:
        chance = sorteio.random()
        if chance < 0.04:
            dias = sorteio.randint(-5, -1)    # já vencido
        elif chance < 0.18:
            dias = sorteio.randint(0, 5)      # perto de vencer
        else:
            dias = max(1, round(validade_base * sorteio.uniform(0.4, 1)))
        faixa_estoque = (12, 60)
    else:
        dias = round(validade_base * sorteio.uniform(0.5, 1))
        faixa_estoque = (30, 180)

    if sorteio.random() < 0.10:
        estoque = sorteio.randint(0, 8)       # estoque baixo ou zerado
    else:
        estoque = sorteio.randint(*faixa_estoque)

    return ProdutoDB(
        nome=nome,
        preco=preco,
        quant_estoque=estoque,
        validade=(hoje + timedelta(days=dias)).strftime("%d/%m/%Y"),
        codigo_barras=gerar_codigo_barras(nome),
        categoria=categoria,
        peso=float(peso),
    )


def montar_catalogo(hoje: date) -> list[ProdutoDB]:
    produtos = [
        montar_produto(nome, preco, peso, validade, categoria, hoje)
        for categoria, itens in CATALOGO.items()
        for nome, preco, peso, validade in itens
    ]

    codigos = [produto.codigo_barras for produto in produtos]
    assert len(codigos) == len(set(codigos)), "códigos de barras repetidos"

    return produtos


def limpar_tabela(db) -> int:
    removidos = db.query(ProdutoDB).delete()
    # volta o autoincremento do SQLite para que os IDs recomecem em 1
    db.execute(text("DELETE FROM sqlite_sequence WHERE name = 'produtos'"))
    db.commit()
    return removidos


def main():
    parser = argparse.ArgumentParser(
        description="Popula o banco com produtos de supermercado."
    )
    parser.add_argument(
        "--limpar",
        action="store_true",
        help="apaga todos os produtos existentes antes de popular",
    )
    parser.add_argument(
        "--sim",
        action="store_true",
        help="não pede confirmação ao usar --limpar",
    )
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    banco = Path(engine.url.database).resolve()
    print(f"Banco: {banco}")

    db = SessionLocal()

    try:
        if args.limpar:
            if not args.sim:
                resposta = input(
                    "Isso apaga TODOS os produtos do banco. Continuar? [s/N] "
                )
                if resposta.strip().lower() not in ("s", "sim"):
                    print("Cancelado.")
                    return

            print(f"{limpar_tabela(db)} produto(s) removido(s).")

        existentes = {
            codigo for (codigo,) in db.query(ProdutoDB.codigo_barras).all()
        }
        novos = [
            produto
            for produto in montar_catalogo(date.today())
            if produto.codigo_barras not in existentes
        ]

        db.add_all(novos)
        db.commit()

        total = db.query(ProdutoDB).count()
        tamanho_catalogo = sum(len(itens) for itens in CATALOGO.values())
        print(
            f"{len(novos)} produto(s) adicionado(s), "
            f"{tamanho_catalogo - len(novos)} já existia(m). "
            f"Total no banco: {total}."
        )

        for categoria, quantidade in Counter(
            produto.categoria for produto in novos
        ).items():
            print(f"  {categoria}: {quantidade}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
