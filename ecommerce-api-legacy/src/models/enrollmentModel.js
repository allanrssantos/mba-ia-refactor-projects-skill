'use strict';

module.exports = function createEnrollmentModel(db) {
  return {
    async create(userId, courseId) {
      const { lastID } = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, courseId],
      );
      return lastID;
    },

    deleteByUserId: (userId) => db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]),
  };
};
