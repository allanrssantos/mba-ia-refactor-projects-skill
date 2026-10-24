'use strict';

const { ValidationError } = require('./errors');
const { DEFAULT_PASSWORD } = require('../models/constants');

/**
 * Valida o payload de checkout e o traduz para nomes internos.
 * Contrato externo preservado: usr, eml, pwd (opcional), c_id, card.
 * Mensagem e status idênticos ao original ("Bad Request", 400).
 */
function validateCheckoutInput(body) {
  if (!body || typeof body !== 'object') throw new ValidationError('Bad Request');

  const { usr, eml, pwd, c_id: courseId, card } = body;
  if (!usr || !eml || !courseId || !card) throw new ValidationError('Bad Request');
  // Antes, um cartão numérico lançava TypeError e derrubava o processo.
  if (typeof card !== 'string') throw new ValidationError('Bad Request');

  return {
    userName: usr,
    email: eml,
    password: pwd || DEFAULT_PASSWORD,
    courseId,
    cardNumber: card,
  };
}

module.exports = { validateCheckoutInput };
