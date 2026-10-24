from src.models.constants import STATUS_APROVADO, STATUS_CANCELADO
from src.utils.errors import ValidationError


class PedidoService:
    """Casos de uso que cruzam pedidos, produtos e notificações."""

    def __init__(self, db, produto_model, pedido_model, notificacoes):
        self.db = db
        self.produtos = produto_model
        self.pedidos = pedido_model
        self.notificacoes = notificacoes

    def criar(self, usuario_id, itens):
        conexao = self.db.conexao()
        # Uma única transação: validação de estoque, cabeçalho, itens e baixa de estoque.
        with conexao:
            total = 0
            produtos_por_id = {}
            for item in itens:
                produto = self.produtos.buscar_por_id(item["produto_id"])
                if produto is None:
                    raise ValidationError(
                        "Produto " + str(item["produto_id"]) + " não encontrado", extra={"sucesso": False}
                    )
                if produto["estoque"] < item["quantidade"]:
                    raise ValidationError(
                        "Estoque insuficiente para " + produto["nome"], extra={"sucesso": False}
                    )
                total = total + (produto["preco"] * item["quantidade"])
                produtos_por_id[item["produto_id"]] = produto

            pedido_id = self.pedidos.inserir(usuario_id, total)
            for item in itens:
                preco = produtos_por_id[item["produto_id"]]["preco"]
                self.pedidos.inserir_item(pedido_id, item["produto_id"], item["quantidade"], preco)
                self.produtos.baixar_estoque(item["produto_id"], item["quantidade"])

        self.notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, novo_status):
        self.pedidos.atualizar_status(pedido_id, novo_status)
        if novo_status == STATUS_APROVADO:
            self.notificacoes.pedido_aprovado(pedido_id)
        if novo_status == STATUS_CANCELADO:
            self.notificacoes.pedido_cancelado(pedido_id)
        return True
