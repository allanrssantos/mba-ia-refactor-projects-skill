"""Exceções de domínio mapeadas para HTTP pelo error handler central."""


class AppError(Exception):
    status = 400

    def __init__(self, message, status=None, extra=None):
        super().__init__(message)
        self.message = message
        self.status = status or self.status
        self.extra = extra or {}


class ValidationError(AppError):
    status = 400


class NotFoundError(AppError):
    status = 404


class AuthenticationError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403
