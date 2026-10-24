'use strict';

const { hashPassword } = require('./passwordHasher');

module.exports = function createUserModel(db) {
  return {
    findByEmail: (email) => db.get('SELECT id FROM users WHERE email = ?', [email]),

    async create({ name, email, password }) {
      const { lastID } = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, hashPassword(password)],
      );
      return lastID;
    },

    deleteById: (userId) => db.run('DELETE FROM users WHERE id = ?', [userId]),
  };
};
