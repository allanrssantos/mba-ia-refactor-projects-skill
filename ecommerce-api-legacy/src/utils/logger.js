'use strict';

const LEVELS = Object.freeze({ debug: 10, info: 20, warn: 30, error: 40 });

/**
 * Logger mínimo com níveis e timestamp sobre o console.
 * Nunca registre dados sensíveis (cartão completo, senha, token, chave).
 */
function createLogger(level = 'info') {
  const threshold = LEVELS[level] !== undefined ? LEVELS[level] : LEVELS.info;

  const write = (name, method) => (message, meta) => {
    if (LEVELS[name] < threshold) return;
    const line = `${new Date().toISOString()} ${name.toUpperCase()} ${message}`;
    if (meta !== undefined) method(line, meta);
    else method(line);
  };

  return {
    debug: write('debug', console.debug),
    info: write('info', console.info),
    warn: write('warn', console.warn),
    error: write('error', console.error),
  };
}

module.exports = { createLogger, LEVELS };
