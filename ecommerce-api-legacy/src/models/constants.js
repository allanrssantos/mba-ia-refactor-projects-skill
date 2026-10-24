'use strict';

const PAYMENT_STATUS = Object.freeze({
  PAID: 'PAID',
  DENIED: 'DENIED',
});

/** Prefixo de cartão aprovado pelo gateway simulado (regra original: começa com "4"). */
const APPROVED_CARD_PREFIX = '4';

/** Senha aplicada quando o checkout não informa `pwd` (comportamento original). */
const DEFAULT_PASSWORD = '123456';

const UNKNOWN_STUDENT = 'Unknown';

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, DEFAULT_PASSWORD, UNKNOWN_STUDENT };
