'use strict';

const sqlite3 = require('sqlite3');
const { hashPassword } = require('./passwordHasher');
const { PAYMENT_STATUS } = require('./constants');

/** Envolve o driver de callbacks em Promises e expõe transações serializadas. */
function wrap(raw) {
  const run = (sql, params = []) => new Promise((resolve, reject) => {
    raw.run(sql, params, function onRun(err) {
      if (err) return reject(err);
      return resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
  const get = (sql, params = []) => new Promise((resolve, reject) => {
    raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });
  const all = (sql, params = []) => new Promise((resolve, reject) => {
    raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });

  // Conexão única (banco em memória): transações entram em fila para não se intercalar.
  let queue = Promise.resolve();
  function transaction(work) {
    const result = queue.then(async () => {
      await run('BEGIN');
      try {
        const value = await work();
        await run('COMMIT');
        return value;
      } catch (err) {
        await run('ROLLBACK');
        throw err;
      }
    });
    queue = result.catch(() => {});
    return result;
  }

  const close = () => new Promise((resolve, reject) => {
    raw.close((err) => (err ? reject(err) : resolve()));
  });

  return { run, get, all, transaction, close };
}

async function createSchema(db) {
  await db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
  await db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
  await db.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
  await db.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
  await db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

/** Seed original, com a senha do usuário de exemplo gravada como hash. */
async function seed(db) {
  const { count } = await db.get('SELECT COUNT(*) AS count FROM users');
  if (count > 0) return;

  await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]);
  await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
    ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]);
  await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
  await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [1, 997.00, PAYMENT_STATUS.PAID]);
}

/** Abre a conexão, cria o schema e aplica o seed antes de devolver o wrapper. */
async function openDatabase(dbPath) {
  const raw = await new Promise((resolve, reject) => {
    const connection = new sqlite3.Database(dbPath, (err) => (err ? reject(err) : resolve(connection)));
  });
  const db = wrap(raw);
  await createSchema(db);
  await seed(db);
  return db;
}

module.exports = { openDatabase };
