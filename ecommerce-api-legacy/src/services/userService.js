'use strict';

/** Remove o usuário e seus dependentes (pagamentos e matrículas) na mesma transação. */
module.exports = function createUserService({ db, userModel, enrollmentModel, paymentModel }) {
  return {
    deleteUser(userId) {
      return db.transaction(async () => {
        await paymentModel.deleteByUserId(userId);
        await enrollmentModel.deleteByUserId(userId);
        await userModel.deleteById(userId);
      });
    },
  };
};
