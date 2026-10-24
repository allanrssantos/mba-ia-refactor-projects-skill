from flask import Blueprint


def criar_blueprint(controller, require_admin):
    bp = Blueprint("sistema", __name__)
    bp.add_url_rule("/health", "health_check", controller.health, methods=["GET"])
    bp.add_url_rule("/", "index", controller.index, methods=["GET"])
    bp.add_url_rule("/admin/reset-db", "reset_database", require_admin(controller.resetar_banco), methods=["POST"])
    bp.add_url_rule("/admin/query", "executar_query", require_admin(controller.executar_query), methods=["POST"])
    return bp
