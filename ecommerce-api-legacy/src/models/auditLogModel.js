'use strict';

module.exports = function createAuditLogModel(db) {
  return {
    record: (action) => db.run(
      "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
      [action],
    ),
  };
};
