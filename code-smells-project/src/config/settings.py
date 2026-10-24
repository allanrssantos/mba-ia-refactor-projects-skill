"""Configuração da aplicação: único módulo que lê variáveis de ambiente."""
import os
import secrets


def _bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _lista(value):
    """Converte "a,b,c" em lista; "*" permanece como coringa do Flask-CORS."""
    value = value.strip()
    if value == "*":
        return "*"
    return [origem.strip() for origem in value.split(",") if origem.strip()]


class Settings:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        # Segredo sem default real: gerado a cada boot quando não configurado.
        self.SECRET_KEY = env.get("SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = _bool(env.get("DEBUG", "false"))
        self.HOST = env.get("HOST", "127.0.0.1")
        self.PORT = int(env.get("PORT", "5000"))
        self.DB_PATH = env.get("DB_PATH", "loja.db")
        self.CORS_ORIGINS = _lista(env.get("CORS_ORIGINS", "*"))
        # Vazio = rotas administrativas respondem 403.
        self.ADMIN_TOKEN = env.get("ADMIN_TOKEN", "")
        self.LOG_LEVEL = env.get("LOG_LEVEL", "INFO")


settings = Settings()
