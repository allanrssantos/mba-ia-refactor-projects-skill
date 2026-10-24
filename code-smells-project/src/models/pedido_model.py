from src.models.constants import (
    FAIXAS_DESCONTO,
    PRODUTO_DESCONHECIDO,
    STATUS_APROVADO,
    STATUS_CANCELADO,
    STATUS_PENDENTE,
)

_SQL_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.id AS item_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
    {where}
    ORDER BY p.id, ip.id
"""


def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0


def _montar_pedidos(linhas):
    """Agrupa o resultado do JOIN em pedidos com lista de itens, preservando a ordem por id."""
    pedidos = {}
    for linha in linhas:
        pedido = pedidos.setdefault(
            linha["id"],
            {
                "id": linha["id"],
                "usuario_id": linha["usuario_id"],
                "status": linha["status"],
                "total": linha["total"],
                "criado_em": linha["criado_em"],
                "itens": [],
            },
        )
        if linha["item_id"] is not None:
            pedido["itens"].append(
                {
                    "produto_id": linha["produto_id"],
                    "produto_nome": linha["produto_nome"] if linha["produto_nome"] is not None else PRODUTO_DESCONHECIDO,
                    "quantidade": linha["quantidade"],
                    "preco_unitario": linha["preco_unitario"],
                }
            )
    return list(pedidos.values())


class PedidoModel:
    def __init__(self, db):
        self.db = db

    def listar_todos(self):
        linhas = self.db.conexao().execute(_SQL_PEDIDOS_COM_ITENS.format(where="")).fetchall()
        return _montar_pedidos(linhas)

    def listar_por_usuario(self, usuario_id):
        linhas = self.db.conexao().execute(
            _SQL_PEDIDOS_COM_ITENS.format(where="WHERE p.usuario_id = ?"), (usuario_id,)
        ).fetchall()
        return _montar_pedidos(linhas)

    def inserir(self, usuario_id, total):
        """Escrita sem commit: deve ser chamada dentro de uma transação aberta pelo chamador."""
        cursor = self.db.conexao().execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        )
        return cursor.lastrowid

    def inserir_item(self, pedido_id, produto_id, quantidade, preco_unitario):
        """Escrita sem commit: deve ser chamada dentro de uma transação aberta pelo chamador."""
        self.db.conexao().execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario),
        )

    def atualizar_status(self, pedido_id, novo_status):
        conexao = self.db.conexao()
        with conexao:
            conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        return True

    def contar(self):
        return self.db.conexao().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def relatorio_vendas(self):
        linha = self.db.conexao().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   SUM(total) AS faturamento,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pendentes,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS aprovados,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()

        total_pedidos = linha["total_pedidos"]
        faturamento = linha["faturamento"] if linha["faturamento"] is not None else 0
        desconto = calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": linha["pendentes"] or 0,
            "pedidos_aprovados": linha["aprovados"] or 0,
            "pedidos_cancelados": linha["cancelados"] or 0,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
