'use strict';

const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = function createAdminRoutes({ adminController, adminGuard }) {
  const router = Router();
  router.get('/api/admin/financial-report', adminGuard, asyncHandler(adminController.financialReport));
  return router;
};
