"""Composition root: cria configuração, banco, models, services, controllers e registra rotas."""
from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings, settings as settings_padrao
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.auth import criar_guard_admin
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.database import Database
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.routes import pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.utils.logger import configurar_logging


def create_app(config=None):
    """`config` pode ser um Settings alternativo ou um dict de overrides (útil em testes)."""
    if isinstance(config, Settings):
        cfg = config
    else:
        cfg = settings_padrao
        for chave, valor in (config or {}).items():
            setattr(cfg, chave, valor)

    configurar_logging(cfg.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["DEBUG"] = cfg.DEBUG
    app.config["DB_PATH"] = cfg.DB_PATH
    CORS(app, origins=cfg.CORS_ORIGINS)

    # Infraestrutura
    db = Database(cfg.DB_PATH)
    db.init_app(app)

    # Models
    produto_model = ProdutoModel(db)
    usuario_model = UsuarioModel(db)
    pedido_model = PedidoModel(db)
    admin_model = AdminModel(db)

    # Services
    notificacoes = NotificacaoService()
    pedido_service = PedidoService(db, produto_model, pedido_model, notificacoes)

    # Controllers
    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model)
    pedido_controller = PedidoController(pedido_model, pedido_service)
    relatorio_controller = RelatorioController(pedido_model)
    sistema_controller = SistemaController(produto_model, usuario_model, pedido_model, admin_model)

    # Rotas, na mesma ordem de registro do app original
    require_admin = criar_guard_admin(cfg.ADMIN_TOKEN)
    app.register_blueprint(produto_routes.criar_blueprint(produto_controller))
    app.register_blueprint(usuario_routes.criar_blueprint(usuario_controller))
    app.register_blueprint(pedido_routes.criar_blueprint(pedido_controller))
    app.register_blueprint(relatorio_routes.criar_blueprint(relatorio_controller))
    app.register_blueprint(sistema_routes.criar_blueprint(sistema_controller, require_admin))

    register_error_handlers(app)
    return app
