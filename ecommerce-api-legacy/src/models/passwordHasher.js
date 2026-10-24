'use strict';

const crypto = require('node:crypto');

const KEY_LENGTH = 64;
const SALT_BYTES = 16;
const PREFIX = 'scrypt$';

/** Hash com sal aleatório via scrypt (node:crypto). Formato: scrypt$<salt hex>$<hash hex>. */
function hashPassword(raw) {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const derived = crypto.scryptSync(String(raw), salt, KEY_LENGTH).toString('hex');
  return `${PREFIX}${salt}$${derived}`;
}

module.exports = { hashPassword };
