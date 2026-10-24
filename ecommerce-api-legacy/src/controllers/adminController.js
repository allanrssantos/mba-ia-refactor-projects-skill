'use strict';

module.exports = function createAdminController({ reportModel }) {
  return {
    async financialReport(req, res) {
      res.json(await reportModel.financialReport());
    },
  };
};
