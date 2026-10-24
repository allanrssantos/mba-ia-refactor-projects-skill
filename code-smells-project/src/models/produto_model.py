CAMPOS_PUBLICOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def serializar_produto(linha):
    return {campo: linha[campo] for campo in CAMPOS_PUBLICOS}


class ProdutoModel:
    def __init__(self, db):
        self.db = db

    def listar(self):
        linhas = self.db.conexao().execute("SELECT * FROM produtos").fetchall()
        return [serializar_produto(linha) for linha in linhas]

    def buscar_por_id(self, produto_id):
        linha = self.db.conexao().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return serializar_produto(linha) if linha else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        conexao = self.db.conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
            return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conexao = self.db.conexao()
        with conexao:
            conexao.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )
        return True

    def deletar(self, produto_id):
        conexao = self.db.conexao()
        with conexao:
            conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        return True

    def pesquisar(self, termo, categoria=None, preco_min=None, preco_max=None):
        condicoes = []
        parametros = []
        if termo:
            condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
            parametros.extend(["%" + termo + "%", "%" + termo + "%"])
        if categoria:
            condicoes.append("categoria = ?")
            parametros.append(categoria)
        if preco_min:
            condicoes.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max:
            condicoes.append("preco <= ?")
            parametros.append(preco_max)

        sql = "SELECT * FROM produtos"
        if condicoes:
            sql += " WHERE " + " AND ".join(condicoes)
        linhas = self.db.conexao().execute(sql, parametros).fetchall()
        return [serializar_produto(linha) for linha in linhas]

    def baixar_estoque(self, produto_id, quantidade):
        """Escrita sem commit: deve ser chamada dentro de uma transação aberta pelo chamador."""
        self.db.conexao().execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id)
        )

    def contar(self):
        return self.db.conexao().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
