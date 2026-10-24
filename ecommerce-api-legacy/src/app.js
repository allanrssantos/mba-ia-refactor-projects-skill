'use strict';

const express = require('express');
const config = require('./config');
const { createLogger } = require('./utils/logger');
const { openDatabase } = require('./models/database');
const createUserModel = require('./models/userModel');
const createCourseModel = require('./models/courseModel');
const createEnrollmentModel = require('./models/enrollmentModel');
const createPaymentModel = require('./models/paymentModel');
const createAuditLogModel = require('./models/auditLogModel');
const createReportModel = require('./models/reportModel');
const createPaymentGateway = require('./services/paymentGateway');
const createCheckoutService = require('./services/checkoutService');
const createUserService = require('./services/userService');
const createCheckoutController = require('./controllers/checkoutController');
const createAdminController = require('./controllers/adminController');
const createUserController = require('./controllers/userController');
const createCheckoutRoutes = require('./routes/checkoutRoutes');
const createAdminRoutes = require('./routes/adminRoutes');
const createUserRoutes = require('./routes/userRoutes');
const createAdminGuard = require('./middlewares/adminGuard');
const createErrorHandler = require('./middlewares/errorHandler');

/**
 * Composition root: cria as dependências (config, logger, banco com schema + seed),
 * monta models → services → controllers → routes e devolve o app sem chamar listen.
 */
async function createApp({ settings = config, logger = createLogger(settings.logLevel), db } = {}) {
  const database = db || await openDatabase(settings.dbPath);

  const userModel = createUserModel(database);
  const courseModel = createCourseModel(database);
  const enrollmentModel = createEnrollmentModel(database);
  const paymentModel = createPaymentModel(database);
  const auditLogModel = createAuditLogModel(database);
  const reportModel = createReportModel(database);

  const paymentGateway = createPaymentGateway({ apiKey: settings.paymentGatewayKey, logger });
  const checkoutService = createCheckoutService({
    db: database, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway, logger,
  });
  const userService = createUserService({ db: database, userModel, enrollmentModel, paymentModel });

  const checkoutController = createCheckoutController({ checkoutService });
  const adminController = createAdminController({ reportModel });
  const userController = createUserController({ userService });

  const app = express();
  app.use(express.json());
  // Mesma ordem de registro do código original.
  app.use(createCheckoutRoutes({ checkoutController }));
  app.use(createAdminRoutes({ adminController, adminGuard: createAdminGuard({ adminToken: settings.adminToken }) }));
  app.use(createUserRoutes({ userController }));
  app.use(createErrorHandler({ logger }));

  return app;
}

if (require.main === module) {
  const logger = createLogger(config.logLevel);
  createApp({ logger })
    .then((app) => {
      const onListening = () => logger.info(`LMS rodando na porta ${config.port}...`);
      if (config.host) app.listen(config.port, config.host, onListening);
      else app.listen(config.port, onListening);
    })
    .catch((err) => {
      logger.error(`falha ao iniciar a aplicação: ${err.stack || err}`);
      process.exit(1);
    });
}

module.exports = { createApp };
