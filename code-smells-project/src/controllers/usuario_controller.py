from flask import jsonify, request

from src.utils.errors import AuthenticationError, NotFoundError
from src.utils.logger import obter_logger
from src.utils.validators import validar_login, validar_usuario

logger = obter_logger(__name__)


class UsuarioController:
    def __init__(self, usuario_model):
        self.usuarios = usuario_model

    def listar(self):
        return jsonify({"dados": self.usuarios.listar(), "sucesso": True}), 200

    def buscar(self, id):
        usuario = self.usuarios.buscar_por_id(id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return jsonify({"dados": usuario, "sucesso": True}), 200

    def criar(self):
        entrada = validar_usuario(request.get_json(silent=True))
        usuario_id = self.usuarios.criar(**entrada)
        logger.info("usuário criado id=%s", usuario_id)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        credenciais = validar_login(request.get_json(silent=True))
        usuario = self.usuarios.autenticar(**credenciais)
        if not usuario:
            logger.info("login falhou para usuário id desconhecido")
            raise AuthenticationError("Email ou senha inválidos", extra={"sucesso": False})
        logger.info("login bem-sucedido id=%s", usuario["id"])
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
