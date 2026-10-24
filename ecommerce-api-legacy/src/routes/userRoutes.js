'use strict';

const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = function createUserRoutes({ userController }) {
  const router = Router();
  router.delete('/api/users/:id', asyncHandler(userController.remove));
  return router;
};
