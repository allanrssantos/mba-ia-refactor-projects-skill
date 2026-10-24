'use strict';

module.exports = function createUserController({ userService }) {
  return {
    async remove(req, res) {
      await userService.deleteUser(req.params.id);
      res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
    },
  };
};
