from flask import jsonify, request

from src.models.constants import API_VERSION
from src.utils.logger import obter_logger
from src.utils.validators import validar_query_admin

logger = obter_logger(__name__)


class SistemaController:
    """Endpoints de infraestrutura: índice, health e operações administrativas."""

    def __init__(self, produto_model, usuario_model, pedido_model, admin_model):
        self.produtos = produto_model
        self.usuarios = usuario_model
        self.pedidos = pedido_model
        self.admin = admin_model

    def index(self):
        return jsonify(
            {
                "mensagem": "Bem-vindo à API da Loja",
                "versao": API_VERSION,
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                },
            }
        )

    def health(self):
        # Sem segredos nem configuração interna na resposta.
        return jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": {
                    "produtos": self.produtos.contar(),
                    "usuarios": self.usuarios.contar(),
                    "pedidos": self.pedidos.contar(),
                },
                "versao": API_VERSION,
            }
        ), 200

    def resetar_banco(self):
        self.admin.resetar()
        logger.warning("banco de dados resetado por administrador")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        query = validar_query_admin(request.get_json(silent=True))
        resultado = self.admin.executar_sql(query)
        if resultado is not None:
            return jsonify({"dados": resultado, "sucesso": True}), 200
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
