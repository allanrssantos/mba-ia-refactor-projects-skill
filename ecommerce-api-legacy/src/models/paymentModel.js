'use strict';

module.exports = function createPaymentModel(db) {
  return {
    create: (enrollmentId, amount, status) => db.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, amount, status],
    ),

    deleteByUserId: (userId) => db.run(
      'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
      [userId],
    ),
  };
};
