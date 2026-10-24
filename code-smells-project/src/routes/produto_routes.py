from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("produtos", __name__)
    bp.add_url_rule("/produtos", "listar_produtos", controller.listar, methods=["GET"])
    bp.add_url_rule("/produtos/busca", "buscar_produtos", controller.pesquisar, methods=["GET"])
    bp.add_url_rule("/produtos/<int:id>", "buscar_produto", controller.buscar, methods=["GET"])
    bp.add_url_rule("/produtos", "criar_produto", controller.criar, methods=["POST"])
    bp.add_url_rule("/produtos/<int:id>", "atualizar_produto", controller.atualizar, methods=["PUT"])
    bp.add_url_rule("/produtos/<int:id>", "deletar_produto", controller.deletar, methods=["DELETE"])
    return bp
