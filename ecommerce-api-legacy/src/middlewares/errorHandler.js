'use strict';

/** Error handler central: erros de domínio → status próprio com texto; demais → 500 genérico com log. */
module.exports = function createErrorHandler({ logger }) {
  // eslint-disable-next-line no-unused-vars
  return function errorHandler(err, req, res, next) {
    if (err && err.status && err.status < 500) {
      return res.status(err.status).send(err.message);
    }
    logger.error(`unhandled error on ${req.method} ${req.originalUrl}: ${err && err.stack ? err.stack : err}`);
    return res.status(500).send('Erro interno');
  };
};
