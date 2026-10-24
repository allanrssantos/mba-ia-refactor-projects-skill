'use strict';

const { NotFoundError, PaymentDeniedError } = require('../utils/errors');
const { PAYMENT_STATUS } = require('../models/constants');

/** Caso de uso de checkout: curso ativo → cobrança → usuário, matrícula, pagamento e auditoria em transação. */
module.exports = function createCheckoutService({
  db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway, logger,
}) {
  return {
    async checkout({ userName, email, password, courseId, cardNumber }) {
      const course = await courseModel.findActiveById(courseId);
      if (!course) throw new NotFoundError('Curso não encontrado');

      const { status } = paymentGateway.charge({ cardNumber, amount: course.price });
      if (status === PAYMENT_STATUS.DENIED) throw new PaymentDeniedError('Pagamento recusado');

      const enrollmentId = await db.transaction(async () => {
        const existing = await userModel.findByEmail(email);
        const userId = existing ? existing.id : await userModel.create({ name: userName, email, password });
        const newEnrollmentId = await enrollmentModel.create(userId, courseId);
        await paymentModel.create(newEnrollmentId, course.price, status);
        await auditLogModel.record(`Checkout curso ${courseId} por ${userId}`);
        return newEnrollmentId;
      });

      logger.info(`checkout completed enrollment=${enrollmentId} course=${course.title}`);
      return { enrollmentId };
    },
  };
};
