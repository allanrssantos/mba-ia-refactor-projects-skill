"""Configuração da aplicação: único módulo que lê variáveis de ambiente."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get('DEBUG', 'false'))
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///tasks.db')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    @property
    def cors_origins(self):
        if self.CORS_ORIGINS.strip() == '*':
            return '*'
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]


settings = Settings()
