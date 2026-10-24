import hmac
from functools import wraps

from flask import request

from src.utils.errors import ForbiddenError


def criar_guard_admin(admin_token):
    """Decorator que exige o header X-Admin-Token igual ao ADMIN_TOKEN configurado (tempo constante)."""

    def require_admin(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            informado = request.headers.get("X-Admin-Token", "")
            if not admin_token or not hmac.compare_digest(informado.encode("utf-8"), admin_token.encode("utf-8")):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return wrapper

    return require_admin
