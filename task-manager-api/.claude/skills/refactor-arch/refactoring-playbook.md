# Refactoring Playbook — transformações da Fase 3

> Carregado na Fase 3, sob demanda: leia as seções `T-xx` citadas nas Recommendations do relatório.
> Exemplos sintéticos (entidades genéricas `items`, `orders`, `accounts`), alternando Python e JavaScript. Adapte nomes, mensagens e formato ao projeto real **sem mudar o contrato** (`mvc-guidelines.md` §7).
> Nenhuma transformação pode adicionar dependências: use a stdlib, o core do runtime ou o que já está declarado no manifesto (e transitivos obrigatórios do framework, como `werkzeug` no Flask).

## Ordem de aplicação recomendada

1. **T-01** config → 2. **T-03 / T-08** esqueleto de camadas + composition root (revalide o boot aqui) → 3. **T-12** error handler → 4. **T-02, T-05, T-06, T-04** segurança → 5. **T-07, T-11, T-09, T-10** regras, validação, transações, N+1 → 6. **T-13** APIs deprecated → 7. **T-14, T-15, T-16** constantes, nomes, logs e código morto → revalidação final.

| ID | Transformação | Resolve |
|---|---|---|
| T-01 | Extract Configuration to Environment | AP-01, AP-11 |
| T-02 | Parameterize Queries | AP-02 |
| T-03 | Split God Class into MVC Layers | AP-03 |
| T-04 | Output Serializer with Field Allow-list | AP-04, AP-15 |
| T-05 | Guard Admin Endpoints by Configuration | AP-05, AP-02 |
| T-06 | Hash Passwords with Standard Library | AP-06 |
| T-07 | Move Business Rules to Model/Service | AP-07, AP-15 |
| T-08 | Inject Dependencies via Composition Root | AP-08, AP-09 |
| T-09 | Wrap Multi-step Writes in Transaction (async/await) | AP-10 |
| T-10 | Replace N+1 with Join/Eager Loading/Aggregation | AP-12 |
| T-11 | Centralize Input Validation | AP-13, AP-15 |
| T-12 | Centralized Error Handler and Domain Exceptions | AP-14 |
| T-13 | Replace Deprecated API | AP-16 |
| T-14 | Extract Named Constants/Enums | AP-17 |
| T-15 | Rename Internals, Keep External Contract | AP-18 |
| T-16 | Structured Logging and Dead Code Removal | AP-19, AP-20, AP-04 |

---

## T-01 — Extract Configuration to Environment

**Resolve:** AP-01, AP-11.

**Passos**
1. Criar o módulo de config (`src/config/settings.py` / `src/config/index.js`, ou `config/` na raiz em projetos `partial-layers`).
2. Mover para ele todo literal de configuração: segredos, debug, host, porta, caminho/URI do banco, origens CORS, chaves de integração, `ADMIN_TOKEN`.
3. Defaults: porta e banco iguais aos originais; debug `false`; segredos gerados em runtime ou vazios (nunca o valor antigo).
4. Substituir os usos pelo objeto de config; nenhum outro módulo lê o ambiente.
5. Criar `.env.example` documentando cada variável.

**Antes (Python)**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "my-very-secret-key"
app.config["DEBUG"] = True
CORS(app)
# ...
app.run(host="0.0.0.0", port=8000, debug=True)
```

**Depois (Python)**
```python
# src/config/settings.py
import os
import secrets

def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("DEBUG", "false"))
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "8000"))          # mesmo default do original
    DB_PATH = os.environ.get("DB_PATH", "store.db")     # mesmo default do original
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

settings = Settings()

# app.py (entry point)
from src.app import create_app
from src.config.settings import settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

**Depois (JavaScript, equivalente)**
```js
// src/config/index.js
const crypto = require('node:crypto');

module.exports = Object.freeze({
  port: Number(process.env.PORT || 8080),
  dbPath: process.env.DB_PATH || ':memory:',
  gatewayKey: process.env.GATEWAY_KEY || '',
  sessionSecret: process.env.SESSION_SECRET || crypto.randomBytes(32).toString('hex'),
  adminToken: process.env.ADMIN_TOKEN || '',
});
```

```text
# .env.example
PORT=8000            # porta HTTP (default de desenvolvimento)
DEBUG=false          # nunca true em produção
SECRET_KEY=          # vazio = gerado a cada boot (sessões não persistem entre reinícios)
ADMIN_TOKEN=         # vazio = rotas administrativas respondem 403
```

**Armadilhas:** não carregar `.env` com biblioteca não declarada; o boot sem `.env` precisa funcionar; manter a mesma porta padrão; não deixar o segredo antigo como default "temporário".

## T-02 — Parameterize Queries

**Resolve:** AP-02.

**Passos**
1. Para cada SQL com concatenação/interpolação, trocar valores por placeholders do driver (`?` no sqlite3, `%s` no psycopg2/pymysql, `$1` no pg).
2. Cláusulas dinâmicas: montar `conditions` e `params` em paralelo.
3. `LIKE`: o `%` vai no parâmetro, não no SQL.
4. Identificadores dinâmicos (coluna de ordenação) só de allow-list.

**Antes (JavaScript)**
```js
app.get('/items/search', (req, res) => {
  let sql = "SELECT * FROM items WHERE 1=1";
  if (req.query.q) sql += " AND name LIKE '%" + req.query.q + "%'";
  if (req.query.category) sql += ` AND category = '${req.query.category}'`;
  db.all(sql, (err, rows) => res.json(rows));
});
```

**Depois (JavaScript)**
```js
// src/models/itemModel.js
async function search({ q, category }) {
  const conditions = [];
  const params = [];
  if (q) {
    conditions.push('(name LIKE ? OR description LIKE ?)');
    params.push(`%${q}%`, `%${q}%`);
  }
  if (category) {
    conditions.push('category = ?');
    params.push(category);
  }
  const where = conditions.length ? ` WHERE ${conditions.join(' AND ')}` : '';
  return db.all(`SELECT * FROM items${where}`, params);
}
```

**Antes (Python)**
```python
cursor.execute("INSERT INTO accounts (name, email) VALUES ('" + name + "', '" + email + "')")
cursor.execute("SELECT * FROM accounts WHERE id = " + str(account_id))
```

**Depois (Python)**
```python
cursor.execute("INSERT INTO accounts (name, email) VALUES (?, ?)", (name, email))
cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
```

**Armadilhas:** preserve a mesma semântica de filtro (ex.: `if preco_min:` ignora `0` — mantenha); `WHERE 1=1` é inofensivo, mas a lista de condições é mais clara; não "parametrize" nomes de tabela com `?` (não funciona) — use allow-list.

## T-03 — Split God Class into MVC Layers

**Resolve:** AP-03 (com T-08 e T-07).

**Passos**
1. Listar responsabilidades da unidade: conexão/schema/seed, uma lista de rotas, regras por domínio.
2. Mover conexão/schema/seed para `models/database`.
3. Para cada domínio: `models/<entidade>` (queries), `controllers/<entidade>` (fluxo), `routes/<domínio>` (mapeamento com os mesmos paths e a mesma ordem).
4. Fluxos multi-entidade vão para `services/`.
5. O composition root instancia tudo e registra as rotas; apagar a classe antiga quando ficar vazia.

**Antes (JavaScript)**
```js
class AppService {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initSchema() { this.db.run('CREATE TABLE items (...)'); /* seed */ }
  mountRoutes(app) {
    app.get('/items', (req, res) => this.db.all('SELECT * FROM items', (e, rows) => res.json(rows)));
    app.post('/orders', (req, res) => { /* valida, calcula, grava 3 tabelas */ });
    app.delete('/accounts/:id', (req, res) => { /* ... */ });
  }
}
module.exports = AppService;
```

**Depois (JavaScript)**
```js
// src/models/itemModel.js
module.exports = (db) => ({
  findAll: () => db.all('SELECT * FROM items'),
});

// src/controllers/itemController.js
module.exports = (itemModel) => ({
  list: async (req, res) => res.json(await itemModel.findAll()),
});

// src/routes/itemRoutes.js
const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
module.exports = (controller) => {
  const router = Router();
  router.get('/items', asyncHandler(controller.list));
  return router;
};

// src/app.js (composition root + entry point)
const express = require('express');
const config = require('./config');
const { openDatabase } = require('./models/database');
const errorHandler = require('./middlewares/errorHandler');

async function createApp() {
  const db = await openDatabase(config.dbPath);          // schema + seed
  const itemController = require('./controllers/itemController')(require('./models/itemModel')(db));
  const app = express();
  app.use(express.json());
  app.use(require('./routes/itemRoutes')(itemController));
  // ... demais domínios, na mesma ordem de registro original
  app.use(errorHandler);
  return app;
}

if (require.main === module) {
  createApp().then((app) => app.listen(config.port, () => console.log(`listening on ${config.port}`)));
}
module.exports = { createApp };
```

**Armadilhas:** manter prefixos e ordem de registro; o seed precisa terminar antes do `listen`; não deixar a classe antiga importada "por garantia".

## T-04 — Output Serializer with Field Allow-list

**Resolve:** AP-04 (e duplicação de serialização, AP-15).

**Passos**
1. Criar um serializador público por entidade (método `to_public_dict()` / função `toPublic()`), com allow-list explícita de campos.
2. Substituir todas as montagens manuais de dicionário da entidade por ele.
3. Remover campos sensíveis (senha, hash, segredos) de todas as respostas; endpoints de health deixam de expor config.

**Antes (Python)**
```python
class Account(db.Model):
    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "password": self.password, "created_at": str(self.created_at)}

@bp.get("/health")
def health():
    return {"status": "ok", "secret_key": app.config["SECRET_KEY"], "db": "store.db"}
```

**Depois (Python)**
```python
class Account(db.Model):
    PUBLIC_FIELDS = ("id", "name", "email", "created_at")

    def to_dict(self):
        data = {field: getattr(self, field) for field in self.PUBLIC_FIELDS}
        data["created_at"] = str(self.created_at)
        return data

def health_controller():
    return {"status": "ok"}, 200   # sem segredos nem caminhos internos
```

**Armadilhas:** manter as demais chaves e seus formatos (ex.: datas serializadas com `str()`); a remoção de campo sensível é mudança permitida e deve ser citada no bloco PHASE 3.

## T-05 — Guard Admin Endpoints by Configuration

**Resolve:** AP-05 (e AP-02 quando o endpoint executa SQL arbitrário).

**Passos**
1. Criar o guard em `middlewares/auth` lendo `ADMIN_TOKEN` da config.
2. Sem `ADMIN_TOKEN` configurado ou header `X-Admin-Token` diferente (comparação em tempo constante) → 403 no estilo de corpo do projeto.
3. Aplicar o guard só às rotas AP-05; manter path, método e comportamento com token válido.
4. Registrar a mudança `200 → 403 (sem token)` no bloco PHASE 3 e validar com e sem token.

**Antes (Python)**
```python
@app.route("/admin/wipe", methods=["POST"])
def wipe():
    db.execute("DELETE FROM orders")
    return jsonify({"message": "wiped"}), 200
```

**Depois (Python)**
```python
# src/middlewares/auth.py
import hmac
from functools import wraps
from flask import jsonify, request
from src.config.settings import settings

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = settings.ADMIN_TOKEN
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided.encode(), expected.encode()):
            return jsonify({"error": "Forbidden"}), 403      # use a chave de erro do projeto
        return view(*args, **kwargs)
    return wrapper

# src/routes/admin_routes.py
admin_bp.add_url_rule("/admin/wipe", view_func=require_admin(admin_controller.wipe), methods=["POST"])
```

**Depois (JavaScript)**
```js
// src/middlewares/adminGuard.js
const crypto = require('node:crypto');
const config = require('../config');

module.exports = function adminGuard(req, res, next) {
  const expected = Buffer.from(config.adminToken || '');
  const provided = Buffer.from(req.get('X-Admin-Token') || '');
  const ok = expected.length > 0 && expected.length === provided.length
    && crypto.timingSafeEqual(expected, provided);
  if (!ok) return res.status(403).send('Forbidden');       // texto, se o projeto responde texto
  return next();
};

// src/routes/adminRoutes.js
router.get('/internal/revenue', adminGuard, asyncHandler(reportController.revenue));
```

**Armadilhas:** não remover a rota; com token válido o status deve ser o da baseline; `timingSafeEqual` exige buffers de mesmo tamanho (cheque antes).

## T-06 — Hash Passwords with Standard Library

**Resolve:** AP-06.

**Passos**
1. Centralizar `hash_password` / `verify_password` no model de usuário (ou `utils/security`).
2. Novas senhas e seeds usam KDF com sal: Python `werkzeug.security` (transitivo do Flask) ou `hashlib.scrypt`/`pbkdf2_hmac`; Node `crypto.scrypt`/`pbkdf2` + `timingSafeEqual`.
3. Login: buscar o usuário pelo identificador (nunca `WHERE password = ?`) e verificar a senha em código.
4. **Compatibilidade:** se o valor armazenado não estiver no formato novo, verificar pelo formato legado que o projeto usava (texto puro, MD5, função caseira) e, se coincidir, regravar com o hash novo (rehash transparente).
5. Nunca devolver o hash nas respostas (T-04).

**Antes (Python)**
```python
def set_password(self, raw):
    self.password = hashlib.md5(raw.encode()).hexdigest()

def check_password(self, raw):
    return self.password == hashlib.md5(raw.encode()).hexdigest()
```

**Depois (Python)**
```python
import hashlib
import hmac
from werkzeug.security import check_password_hash, generate_password_hash

_MODERN_PREFIXES = ("scrypt:", "pbkdf2:")

def set_password(self, raw: str) -> None:
    self.password = generate_password_hash(raw)

def check_password(self, raw: str) -> bool:
    if self.password.startswith(_MODERN_PREFIXES):
        return check_password_hash(self.password, raw)
    legacy = hashlib.md5(raw.encode()).hexdigest()     # somente o formato legado que o projeto usava
    if hmac.compare_digest(self.password, legacy):
        self.set_password(raw)                          # rehash transparente; o chamador faz commit
        return True
    return False
```

**Antes (JavaScript)**
```js
function weakHash(pwd) { return Buffer.from(pwd).toString('base64').slice(0, 12); }
db.run('INSERT INTO accounts (name, email, pass) VALUES (?, ?, ?)', [name, email, weakHash(pwd)]);
```

**Depois (JavaScript)**
```js
// src/models/passwordHasher.js
const crypto = require('node:crypto');
const KEY_LENGTH = 64;
const PREFIX = 'scrypt$';

function hashPassword(raw) {
  const salt = crypto.randomBytes(16).toString('hex');
  return `${PREFIX}${salt}$${crypto.scryptSync(raw, salt, KEY_LENGTH).toString('hex')}`;
}

function verifyPassword(stored, raw, legacyHash) {
  if (stored.startsWith(PREFIX)) {
    const [, salt, hex] = stored.split('$');
    const ok = crypto.timingSafeEqual(crypto.scryptSync(raw, salt, KEY_LENGTH), Buffer.from(hex, 'hex'));
    return { ok, needsRehash: false };
  }
  const ok = legacyHash !== undefined && legacyHash(raw) === stored;
  return { ok, needsRehash: ok };
}

module.exports = { hashPassword, verifyPassword };
```

**Armadilhas:** login com credenciais de seed precisa manter o status da baseline; o comprimento da coluna deve comportar o hash novo (SQLite não limita; outros bancos podem exigir migração); não adicionar `bcrypt`.

## T-07 — Move Business Rules to Model/Service

**Resolve:** AP-07, AP-15.

**Passos**
1. Identificar no handler o que é regra (cálculos, decisões, agregações) e o que é transporte.
2. Regra de uma entidade → método do model; regra que cruza entidades → função de service.
3. Substituir todas as cópias da regra pelo método (inclusive em outros handlers).
4. O controller passa a: extrair entrada → validar → chamar → responder.

**Antes (Python)**
```python
@bp.get("/items/<int:item_id>")
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    data = item.to_dict()
    if item.due_date and item.due_date < datetime.utcnow() and item.status not in ("closed", "archived"):
        data["late"] = True
    else:
        data["late"] = False
    return jsonify(data), 200
```

**Depois (Python)**
```python
# models/item.py
CLOSED_STATUSES = ("closed", "archived")

class Item(db.Model):
    def is_late(self, now=None) -> bool:
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def to_dict_with_late(self) -> dict:
        data = self.to_dict()
        data["late"] = self.is_late()
        return data

# controllers/item_controller.py
def get_item(item_id):
    item = item_service.get_or_404(item_id)
    return jsonify(item.to_dict_with_late()), 200

# routes/item_routes.py
bp.add_url_rule("/items/<int:item_id>", view_func=item_controller.get_item, methods=["GET"])
```

**Armadilhas:** preservar exatamente a semântica (operadores `<` vs `<=`, status considerados); manter a mesma chave e o mesmo tipo no JSON.

## T-08 — Inject Dependencies via Composition Root

**Resolve:** AP-08, AP-09.

**Passos**
1. Remover singletons/caches de módulo e instâncias criadas dentro de construtores/handlers.
2. Criar as dependências (conexão, serviços, clientes externos) na fábrica da aplicação.
3. Passá-las por parâmetro (fábricas de model/controller, construtor) ou via mecanismo do framework (`app.extensions`, `flask.g`).
4. Efeitos colaterais de integração (e-mail, SMS) atrás de um serviço injetável; sem conexão externa no boot.
5. Cache sem leitor → remover; cache necessário → encapsular com limite.

**Antes (JavaScript)**
```js
// utils.js
let requestCache = {};
let revenueCounter = 0;
function remember(key, value) { requestCache[key] = value; }
module.exports = { remember, requestCache, revenueCounter };

// orderService.js
class OrderService {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
}
```

**Depois (JavaScript)**
```js
// src/services/orderService.js
module.exports = function createOrderService({ orderModel, notifier, logger }) {
  return {
    async place(input) {
      const order = await orderModel.create(input);
      notifier.orderPlaced(order);
      logger.info(`order ${order.id} placed`);
      return order;
    },
  };
};

// src/app.js (composition root)
const db = await openDatabase(config.dbPath);
const orderModel = createOrderModel(db);
const orderService = createOrderService({ orderModel, notifier: createNotifier(config), logger });
const orderController = createOrderController(orderService);
```

**Antes (Python, conexão global)**
```python
_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect("store.db", check_same_thread=False)
    return _conn
```

**Depois (Python, conexão por requisição gerenciada pela app)**
```python
# src/models/database.py
import sqlite3
from flask import current_app, g

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        create_schema_and_seed(get_db())
```

**Armadilhas:** banco SQLite **em memória** não pode ter conexão por requisição (cada conexão é um banco novo): mantenha uma conexão única criada no composition root e injetada; schema/seed precisam rodar uma vez, antes do primeiro request.

## T-09 — Wrap Multi-step Writes in Transaction (async/await)

**Resolve:** AP-10.

**Passos**
1. Envolver o driver de callbacks em Promises (`util.promisify` ou wrapper manual para `run`, que expõe `this.lastID`).
2. Reescrever a pirâmide como sequência `await` dentro de `transaction()` com `BEGIN/COMMIT/ROLLBACK`.
3. Em conexão única compartilhada, serializar transações (fila de Promises) para não intercalar requisições.
4. Remoções de pai: remover dependentes na mesma transação (ou cascade declarado).
5. Python `sqlite3`: `with conn:` faz commit/rollback; SQLAlchemy: `try/commit/except: rollback`.

**Antes (JavaScript)**
```js
db.run('INSERT INTO orders (account_id) VALUES (?)', [accountId], function (err) {
  if (err) return res.status(500).send('error');
  const orderId = this.lastID;
  db.run('INSERT INTO payments (order_id, amount) VALUES (?, ?)', [orderId, amount], function (err) {
    if (err) return res.status(500).send('error');
    db.run('INSERT INTO audit (action) VALUES (?)', ['order ' + orderId], () => {
      res.json({ ok: true, order_id: orderId });
    });
  });
});
```

**Depois (JavaScript)**
```js
// src/models/database.js
const { promisify } = require('node:util');

function wrap(db) {
  const run = (sql, params = []) => new Promise((resolve, reject) => {
    db.run(sql, params, function onRun(err) {
      if (err) return reject(err);
      return resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
  const get = promisify(db.get.bind(db));
  const all = promisify(db.all.bind(db));
  let queue = Promise.resolve();
  function transaction(work) {
    const result = queue.then(async () => {
      await run('BEGIN');
      try {
        const value = await work({ run, get, all });
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
  return { run, get, all, transaction };
}

// src/services/orderService.js
async function placeOrder(db, { accountId, amount }) {
  return db.transaction(async (tx) => {
    const { lastID: orderId } = await tx.run('INSERT INTO orders (account_id) VALUES (?)', [accountId]);
    await tx.run('INSERT INTO payments (order_id, amount) VALUES (?, ?)', [orderId, amount]);
    await tx.run("INSERT INTO audit (action, created_at) VALUES (?, datetime('now'))", [`order ${orderId}`]);
    return orderId;
  });
}
```

**Depois (Python)**
```python
def create_order(conn, account_id, lines):
    with conn:   # commit no sucesso, rollback em exceção
        cur = conn.execute("INSERT INTO orders (account_id, total) VALUES (?, ?)", (account_id, total_of(lines)))
        order_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO order_items (order_id, item_id, quantity) VALUES (?, ?, ?)",
            [(order_id, l["item_id"], l["quantity"]) for l in lines],
        )
    return order_id
```

**Armadilhas:** validações que devolvem erro (estoque, recurso inexistente) acontecem **antes** de abrir a transação ou levantam exceção dentro dela; preservar as mesmas mensagens/status de erro de cada etapa.

## T-10 — Replace N+1 with Join/Eager Loading/Aggregation

**Resolve:** AP-12.

**Passos**
1. Identificar o laço que consulta por item.
2. Substituir por uma consulta com `JOIN` (ou `IN (...)` em lote) e montar a estrutura em memória; no ORM, `selectinload`/`joinedload`; contagens por `GROUP BY`.
3. Preservar forma, ordem dos elementos e valores de fallback (ex.: nome "desconhecido" quando o relacionado não existe → `LEFT JOIN`).

**Antes (Python, sqlite3)**
```python
orders = conn.execute("SELECT * FROM orders").fetchall()
result = []
for o in orders:
    lines = conn.execute("SELECT * FROM order_items WHERE order_id = " + str(o["id"])).fetchall()
    items = []
    for line in lines:
        item = conn.execute("SELECT name FROM items WHERE id = " + str(line["item_id"])).fetchone()
        items.append({"item_id": line["item_id"], "item_name": item["name"] if item else "Unknown"})
    result.append({"id": o["id"], "status": o["status"], "items": items})
```

**Depois (Python, sqlite3)**
```python
rows = conn.execute("""
    SELECT o.id, o.status, oi.item_id, it.name AS item_name
    FROM orders o
    LEFT JOIN order_items oi ON oi.order_id = o.id
    LEFT JOIN items it ON it.id = oi.item_id
    ORDER BY o.id, oi.id
""").fetchall()
orders = {}
for r in rows:
    order = orders.setdefault(r["id"], {"id": r["id"], "status": r["status"], "items": []})
    if r["item_id"] is not None:
        order["items"].append({
            "item_id": r["item_id"],
            "item_name": r["item_name"] if r["item_name"] is not None else "Unknown",
        })
result = list(orders.values())
```

**Depois (Python, SQLAlchemy)**
```python
from sqlalchemy.orm import selectinload

items = db.session.execute(
    db.select(Item).options(selectinload(Item.owner), selectinload(Item.category))
).scalars().all()

counts = dict(db.session.execute(
    db.select(Item.category_id, db.func.count(Item.id)).group_by(Item.category_id)
).all())
```

**Depois (JavaScript)**
```js
const rows = await db.all(`
  SELECT c.id AS group_id, c.title, a.name AS account_name, p.amount, p.status
  FROM groups c
  LEFT JOIN memberships m ON m.group_id = c.id
  LEFT JOIN accounts a ON a.id = m.account_id
  LEFT JOIN payments p ON p.membership_id = m.id
  ORDER BY c.id, m.id`);
const byGroup = new Map();
for (const r of rows) {
  if (!byGroup.has(r.group_id)) byGroup.set(r.group_id, { group: r.title, revenue: 0, members: [] });
  const entry = byGroup.get(r.group_id);
  if (r.account_name === null && r.amount === null) continue;   // grupo sem membros
  if (r.status === 'PAID') entry.revenue += r.amount;
  entry.members.push({ member: r.account_name ?? 'Unknown', paid: r.amount ?? 0 });
}
const report = [...byGroup.values()];
```

**Armadilhas:** uma linha "vazia" do `LEFT JOIN` não deve virar elemento; a ordem original (geralmente por id/rowid) deve ser mantida com `ORDER BY` explícito.

## T-11 — Centralize Input Validation

**Resolve:** AP-13, AP-15.

**Passos**
1. Criar um validador por entidade (funções puras; ou schema `marshmallow`/`joi` somente se já declarado).
2. Validar corpo presente e do tipo objeto, campos obrigatórios, tipos e faixas.
3. Aplicar o mesmo validador em create e update (update valida só os campos enviados).
4. Manter **as mesmas mensagens e status** já usados pelo projeto; entradas que antes geravam 500 por tipo inválido passam a 400 (mudança permitida nº 4).

**Antes (JavaScript)**
```js
router.post('/orders', (req, res) => {
  if (!req.body.account || !req.body.code) return res.status(400).send('Bad Request');
  const approved = req.body.code.startsWith('9');   // número → TypeError e queda do processo
  // ...
});
```

**Depois (JavaScript)**
```js
// src/utils/validators.js
class ValidationError extends Error {
  constructor(message) { super(message); this.status = 400; }
}

function validateOrderInput(body) {
  if (!body || typeof body !== 'object') throw new ValidationError('Bad Request');
  const { account, code } = body;
  if (!account || !code) throw new ValidationError('Bad Request');
  if (typeof code !== 'string') throw new ValidationError('Bad Request');
  return { account: String(account), code };
}

module.exports = { ValidationError, validateOrderInput };

// src/controllers/orderController.js
create: async (req, res) => {
  const input = validateOrderInput(req.body);        // erro → error handler → 400 'Bad Request'
  const result = await orderService.place(input);
  res.status(200).json(result);
},
```

**Armadilhas:** não tornar obrigatório um campo que antes era opcional; manter os defaults que o código aplicava; mensagens idênticas.

**Regra para endpoints de update:** validação nova (ex.: alinhar o PUT às regras do POST) não pode mudar o status de entradas que antes eram aceitas (ex.: `200 → 400`) sem registro. Se a mudança for mantida, ela deve aparecer explicitamente no bloco de validação da Fase 3, na linha correspondente de `## Endpoint Check`, como desvio justificado (`(justified: <regra nova> — antes aceito com <status>)`), e ser contada em `<j> justified changes`. Na dúvida, preserve o status antigo e registre a validação faltante como finding residual.

## T-12 — Centralized Error Handler and Domain Exceptions

**Resolve:** AP-14.

**Passos**
1. Definir exceções de domínio com status (`NotFoundError` 404, `ValidationError` 400, `ConflictError` 409, `ForbiddenError` 403) e corpo no formato do projeto.
2. Registrar um handler central; remover `try/except` genéricos repetidos dos controllers.
3. Erro inesperado → 500 genérico, com log no servidor e sem `str(e)` na resposta.
4. Node: handlers `async` via `asyncHandler`; callbacks sempre checam `err`.

**Antes (Python)**
```python
def list_items():
    try:
        return jsonify({"data": item_model.all()}), 200
    except Exception as e:
        print("ERROR: " + str(e))
        return jsonify({"error": str(e)}), 500
```

**Depois (Python)**
```python
# src/middlewares/error_handler.py
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)
ERROR_KEY = "error"   # a mesma chave de erro que o projeto já usa

class AppError(Exception):
    status = 400
    def __init__(self, message, status=None, extra=None):
        super().__init__(message)
        self.message = message
        self.status = status or self.status
        self.extra = extra or {}

class NotFoundError(AppError):
    status = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({ERROR_KEY: err.message, **err.extra}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):   # 404 de rota, 405 etc. mantêm o comportamento do framework
            return err
        logger.exception("unhandled error")
        return jsonify({ERROR_KEY: "Erro interno"}), 500

# src/controllers/item_controller.py
def list_items():
    return jsonify({"data": item_model.all()}), 200
```

**Depois (JavaScript)**
```js
// src/middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// src/middlewares/errorHandler.js
const logger = require('../utils/logger');
module.exports = function errorHandler(err, req, res, next) {   // eslint-disable-line no-unused-vars
  if (err.status && err.status < 500) return res.status(err.status).send(err.message);
  logger.error(err);
  return res.status(500).send('Internal Server Error');
};
```

**Armadilhas:** o handler genérico do Flask para `Exception` também captura `HTTPException` (404 de rota inexistente, 405, 415 de corpo não JSON) — por isso ele a devolve intacta; preservar corpos de erro com chaves extras (ex.: `"success": false`) via `extra`.

## T-13 — Replace Deprecated API

**Resolve:** AP-16 (consulte `deprecated-apis.md`).

**Passos**
1. Para cada finding AP-16, aplicar o substituto da tabela em **todas** as ocorrências.
2. Preservar o formato serializado (ex.: datetimes ingênuos continuam sem sufixo de fuso; comparações entre ingênuos e com fuso geram `TypeError`).
3. Centralizar o substituto num helper quando houver muitas ocorrências.

**Antes (Python)**
```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
item = Item.query.get(item_id)
if item.due_date < datetime.utcnow():
    ...
```

**Depois (Python)**
```python
# utils/time.py
from datetime import datetime, timezone

def utcnow() -> datetime:
    """UTC ingênuo, compatível com os valores já gravados e com str() anterior."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# models/item.py
created_at = db.Column(db.DateTime, default=utcnow)        # callable, sem parênteses

# controllers/item_controller.py
item = db.session.get(Item, item_id)
if item.due_date < utcnow():
    ...
```

**Antes (JavaScript)**
```js
const encoded = new Buffer(raw).toString('base64');
const id = req.param('id');
const { query } = url.parse(req.url, true);
```

**Depois (JavaScript)**
```js
const encoded = Buffer.from(raw).toString('base64');
const { id } = req.params;
const { searchParams } = new URL(req.url, `http://${req.headers.host}`);
```

**Armadilhas:** `db.session.get` devolve `None` como `Query.get` (comportamento igual); `default=utcnow()` (com parênteses) congelaria o valor no import — use a referência à função.

## T-14 — Extract Named Constants/Enums

**Resolve:** AP-17.

**Passos**
1. Reunir literais de regra em `constants` da camada de modelo (ou reutilizar constantes já existentes no projeto).
2. Substituir todos os usos; listas de valores válidos viram tuplas/arrays congelados.
3. Mensagens que exibem a lista (ex.: "válidas: [...]") continuam idênticas.

**Antes (JavaScript)**
```js
if (!['new', 'paid', 'shipped', 'cancelled'].includes(status)) return res.status(400).send('Invalid status');
const fee = total > 5000 ? total * 0.05 : total > 1000 ? total * 0.02 : 0;
const approved = code.startsWith('9');
```

**Depois (JavaScript)**
```js
// src/models/constants.js
const ORDER_STATUSES = Object.freeze(['new', 'paid', 'shipped', 'cancelled']);
const FEE_TIERS = Object.freeze([
  { above: 5000, rate: 0.05 },
  { above: 1000, rate: 0.02 },
]);
const APPROVED_CODE_PREFIX = '9';
module.exports = { ORDER_STATUSES, FEE_TIERS, APPROVED_CODE_PREFIX };

// src/models/orderModel.js
function feeFor(total) {
  const tier = FEE_TIERS.find((t) => total > t.above);
  return tier ? total * tier.rate : 0;
}
```

**Armadilhas:** manter a ordem dos limiares e os operadores (`>` vs `>=`); manter a ordem da lista quando ela aparece em mensagens.

## T-15 — Rename Internals, Keep External Contract

**Resolve:** AP-18.

**Passos**
1. Renomear variáveis, parâmetros e funções internas para nomes de domínio; eliminar sombras de builtins (`id` → `item_id`).
2. Campos de request/response com nomes ruins **não mudam**: mapear na borda (controller) para nomes internos claros.
3. Renomear funções enganosas (ex.: uma "criptografia" que é codificação) junto com a correção de T-06.

**Antes (JavaScript)**
```js
app.post('/orders', (req, res) => {
  let a = req.body.acct;
  let n = req.body.nm;
  let c = req.body.cd;
  // ...
});
```

**Depois (JavaScript)**
```js
// src/controllers/orderController.js — contrato externo preservado: acct, nm, cd
function toOrderInput(body) {
  return { accountEmail: body.acct, customerName: body.nm, paymentCode: body.cd };
}

create: async (req, res) => {
  const input = validateOrderInput(toOrderInput(req.body));
  const result = await orderService.place(input);
  res.status(200).json(result);
},
```

**Armadilhas:** chaves de resposta também são contrato (não renomear); em Flask, renomear parâmetros de view exige renomear o conversor no path (`<int:item_id>`) — o path público continua igual.

## T-16 — Structured Logging and Dead Code Removal

**Resolve:** AP-19, AP-20, AP-04 (logs sensíveis).

**Passos**
1. Substituir `print`/`console.log` por logger com níveis (Python `logging`; Node: módulo `utils/logger.js` encapsulando `console` com nível e timestamp).
2. Remover dados sensíveis das mensagens (cartão, senha, token, chave) ou mascará-los.
3. Remover imports não usados, funções/classes/módulos nunca referenciados e variáveis mortas; se um utilitário morto duplica lógica viva, unificar e manter um só.
4. Scripts de linha de comando (seed) podem manter `print` como saída para o usuário.

**Antes (Python)**
```python
import os, sys, json, time

def create_item(data):
    item_id = item_model.create(data)
    print("Item created: " + str(item_id))
    print("Charging card " + data["card"])
    return item_id
```

**Depois (Python)**
```python
import logging

logger = logging.getLogger(__name__)

def create_item(data):
    item_id = item_model.create(data)
    logger.info("item created id=%s", item_id)
    logger.info("charging card ending %s", str(data["card"])[-4:])
    return item_id

# entry point
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
```

**Armadilhas:** não remover imports com efeito colateral (registro de models para `create_all`); antes de apagar um símbolo, buscar usos no projeto inteiro (incluindo scripts auxiliares).
