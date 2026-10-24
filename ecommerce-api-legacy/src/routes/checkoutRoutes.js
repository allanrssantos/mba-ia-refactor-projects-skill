'use strict';

const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = function createCheckoutRoutes({ checkoutController }) {
  const router = Router();
  router.post('/api/checkout', asyncHandler(checkoutController.checkout));
  return router;
};
