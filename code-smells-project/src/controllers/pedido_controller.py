from flask import jsonify, request

from src.utils.validators import validar_pedido, validar_status_pedido


class PedidoController:
    def __init__(self, pedido_model, pedido_service):
        self.pedidos = pedido_model
        self.servico = pedido_service

    def criar(self):
        entrada = validar_pedido(request.get_json(silent=True))
        resultado = self.servico.criar(entrada["usuario_id"], entrada["itens"])
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    def listar_por_usuario(self, usuario_id):
        return jsonify({"dados": self.pedidos.listar_por_usuario(usuario_id), "sucesso": True}), 200

    def listar_todos(self):
        return jsonify({"dados": self.pedidos.listar_todos(), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        novo_status = validar_status_pedido(request.get_json(silent=True))
        self.servico.atualizar_status(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
