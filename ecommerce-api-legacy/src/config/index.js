'use strict';

/**
 * Único módulo que lê o ambiente. Defaults iguais aos do código original
 * (porta 3000, banco SQLite em memória); segredos sem valor padrão.
 */
const env = process.env;

module.exports = Object.freeze({
  port: Number(env.PORT || 3000),
  // Sem HOST definido, o servidor escuta em todas as interfaces (comportamento original).
  host: env.HOST || undefined,
  dbPath: env.DB_PATH || ':memory:',
  paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || '',
  adminToken: env.ADMIN_TOKEN || '',
  logLevel: env.LOG_LEVEL || 'info',
});
