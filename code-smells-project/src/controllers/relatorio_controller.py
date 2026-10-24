from flask import jsonify


class RelatorioController:
    def __init__(self, pedido_model):
        self.pedidos = pedido_model

    def vendas(self):
        return jsonify({"dados": self.pedidos.relatorio_vendas(), "sucesso": True}), 200
