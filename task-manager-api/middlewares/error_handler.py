"""Error handler central: exceções de domínio → status; erro inesperado → 500 genérico com log."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)
ERROR_KEY = 'error'
INTERNAL_ERROR_MESSAGE = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({ERROR_KEY: err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err  # 404 de rota, 405, 415 etc. mantêm o comportamento do framework
        logger.exception('unhandled error')
        return jsonify({ERROR_KEY: INTERNAL_ERROR_MESSAGE}), 500
