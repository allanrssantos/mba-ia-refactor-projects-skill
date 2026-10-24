'use strict';

const crypto = require('node:crypto');
const { ForbiddenError } = require('../utils/errors');

/**
 * Guard administrativo: exige ADMIN_TOKEN configurado e header X-Admin-Token
 * igual (comparação em tempo constante). Caso contrário → 403.
 */
module.exports = function createAdminGuard({ adminToken }) {
  return function adminGuard(req, res, next) {
    const expected = Buffer.from(adminToken || '');
    const provided = Buffer.from(req.get('X-Admin-Token') || '');
    const ok = expected.length > 0
      && expected.length === provided.length
      && crypto.timingSafeEqual(expected, provided);
    if (!ok) return next(new ForbiddenError('Forbidden'));
    return next();
  };
};
