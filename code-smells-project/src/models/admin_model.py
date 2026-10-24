class AdminModel:
    """Operações administrativas sobre o banco. Só acessíveis via guard de ADMIN_TOKEN."""

    TABELAS_EM_ORDEM = ("itens_pedido", "pedidos", "produtos", "usuarios")

    def __init__(self, db):
        self.db = db

    def resetar(self):
        conexao = self.db.conexao()
        with conexao:
            for tabela in self.TABELAS_EM_ORDEM:
                conexao.execute("DELETE FROM " + tabela)  # nomes vêm de allow-list fixa

    def executar_sql(self, query):
        """Risco residual assumido: executa SQL arbitrário enviado por um administrador autenticado."""
        conexao = self.db.conexao()
        with conexao:
            cursor = conexao.execute(query)
            if query.strip().upper().startswith("SELECT"):
                return [dict(linha) for linha in cursor.fetchall()]
        return None
