'use strict';

/** Encaminha rejeições de handlers async para o error handler central. */
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
