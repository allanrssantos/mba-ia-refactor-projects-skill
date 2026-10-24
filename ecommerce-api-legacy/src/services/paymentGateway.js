'use strict';

const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../models/constants');

/**
 * Gateway de pagamento simulado (regra original: cartão iniciado em "4" é aprovado).
 * Injetável, para ser substituído por uma integração real ou por um dublê em testes.
 */
module.exports = function createPaymentGateway({ apiKey, logger }) {
  return {
    charge({ cardNumber, amount }) {
      const status = cardNumber.startsWith(APPROVED_CARD_PREFIX)
        ? PAYMENT_STATUS.PAID
        : PAYMENT_STATUS.DENIED;
      logger.info(`payment ${status} amount=${amount} card=****${cardNumber.slice(-4)} gateway=${apiKey ? 'configured' : 'not configured'}`);
      return { status };
    },
  };
};
