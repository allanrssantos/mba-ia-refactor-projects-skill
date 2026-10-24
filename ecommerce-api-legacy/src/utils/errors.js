'use strict';

/** Erro de domínio com status HTTP; o error handler devolve `message` como texto puro. */
class AppError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.name = this.constructor.name;
    this.status = status;
  }
}

class ValidationError extends AppError {
  constructor(message = 'Bad Request') {
    super(message, 400);
  }
}

class NotFoundError extends AppError {
  constructor(message = 'Not Found') {
    super(message, 404);
  }
}

class PaymentDeniedError extends AppError {
  constructor(message = 'Pagamento recusado') {
    super(message, 400);
  }
}

class ForbiddenError extends AppError {
  constructor(message = 'Forbidden') {
    super(message, 403);
  }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeniedError, ForbiddenError };
