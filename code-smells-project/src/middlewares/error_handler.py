from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError
from src.utils.logger import obter_logger

logger = obter_logger(__name__)
CHAVE_ERRO = "erro"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def tratar_erro_dominio(err):
        corpo = {CHAVE_ERRO: err.message}
        corpo.update(err.extra)
        return jsonify(corpo), err.status

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(err):
        if isinstance(err, HTTPException):  # 404 de rota, 405, 415: comportamento do framework
            return err
        logger.exception("erro não tratado")
        return jsonify({CHAVE_ERRO: "Erro interno"}), 500
