# Deprecated APIs — complemento de AP-16

> Na Fase 2, leia **apenas** as seções do ecossistema detectado na Fase 1 (ex.: Python → §1, §2, §3 e §7; Node → §4, §5 e §6).
> Cada linha: API obsoleta → substituto moderno, versão de referência e padrão de busca (ripgrep).
> Regras de uso:
> 1. Reporte só o que aparece no código-fonte do projeto (não em dependências).
> 2. Confirme que a versão resolvida do runtime/biblioteca é ≥ à versão da coluna "Desde". Se não for possível determinar, reporte e escreva "a partir de <versão>".
> 3. Um finding por API obsoleta (todas as ocorrências em `Other occurrences`).
> 4. "Legado" = ainda funciona sem aviso, mas está fora da API recomendada: cite como recomendação complementar dentro de um finding existente, não como finding isolado.
> 5. Se nenhuma API da tabela for encontrada, não force o finding (o item do checklist é "se aplicável").
> 6. Nas tabelas, `\|` é apenas o `|` escapado por causa do Markdown: ao buscar, use `|` (alternância de regex).

## 1. Python (stdlib)

| API obsoleta | Desde | Substituto moderno | Como detectar |
|---|---|---|---|
| `datetime.utcnow()` | 3.12 (deprecated) | `datetime.now(timezone.utc)`; para manter datetimes ingênuos já gravados/comparados, use um helper `datetime.now(timezone.utc).replace(tzinfo=None)` | `utcnow\(` |
| `datetime.utcfromtimestamp(ts)` | 3.12 (deprecated) | `datetime.fromtimestamp(ts, tz=timezone.utc)` | `utcfromtimestamp\(` |
| `distutils` | removido em 3.12 | `setuptools`, `packaging`, `shutil`, `sysconfig` | `import distutils\|from distutils` |
| `imp` | removido em 3.12 | `importlib` | `^import imp$\|from imp import` |
| `asynchat`, `asyncore`, `smtpd` | removidos em 3.12 | `asyncio` | `import (asynchat\|asyncore\|smtpd)` |
| `cgi`, `cgitb`, `pipes`, `crypt`, `telnetlib` | deprecated 3.11, removidos em 3.13 | `email.message`/`urllib.parse`, `subprocess`+`shlex.quote`, `hashlib`/KDF, bibliotecas mantidas | `import (cgi\|cgitb\|pipes\|crypt\|telnetlib)` |
| `ssl.wrap_socket()` | removido em 3.12 | `ssl.SSLContext().wrap_socket()` | `ssl\.wrap_socket\(` |
| `smtplib.SMTP.starttls(keyfile=, certfile=)` | removido em 3.12 | `starttls(context=ssl.create_default_context())` | `starttls\(.*(keyfile\|certfile)` |
| `asyncio.get_event_loop()` sem loop ativo | 3.12 (deprecation warning) | `asyncio.run(main())`, `asyncio.get_running_loop()` | `get_event_loop\(` |
| `locale.getdefaultlocale()` | 3.11 | `locale.getlocale()` / `locale.getencoding()` | `getdefaultlocale\(` |
| `unittest.assertEquals`, `assertRegexpMatches`, `makeSuite` | removidos em 3.12/3.13 | `assertEqual`, `assertRegex`, `TestLoader().loadTestsFromTestCase` | `assertEquals\(\|makeSuite\(` |
| `pkg_resources` | deprecated (setuptools) | `importlib.metadata`, `importlib.resources` | `import pkg_resources` |
| `pytz` (para fusos simples) | legado desde 3.9 | `zoneinfo.ZoneInfo` | `import pytz` |

## 2. Flask / Werkzeug

| API obsoleta | Desde | Substituto moderno | Como detectar |
|---|---|---|---|
| `@app.before_first_request` | deprecated 2.2, removido 2.3 | código de inicialização em `create_app()` / `with app.app_context():` | `before_first_request` |
| `app.json_encoder` / `flask.json.JSONEncoder` | deprecated 2.2, removido 2.3 | `app.json = CustomProvider(app)` (`DefaultJSONProvider`) | `json_encoder\|JSONEncoder` |
| Config `JSON_AS_ASCII`, `JSON_SORT_KEYS`, `JSONIFY_PRETTYPRINT_REGULAR` | removidos 2.3 | `app.json.ensure_ascii`, `app.json.sort_keys`, `app.json.compact` | `JSON_(AS_ASCII\|SORT_KEYS)\|JSONIFY_` |
| `app.env` / `FLASK_ENV` | deprecated 2.2, removido 2.3 | `app.debug` / `FLASK_DEBUG` | `app\.env\b\|FLASK_ENV` |
| `from flask import Markup, escape` | deprecated 2.3, removido 3.0 | `from markupsafe import Markup, escape` | `from flask import .*(Markup\|escape)` |
| `flask._app_ctx_stack`, `flask._request_ctx_stack` | deprecated 2.2, removido 3.0 | `flask.g`, `current_app`, `request` | `_(app\|request)_ctx_stack` |
| `send_file(attachment_filename=, cache_timeout=)` | renomeados 2.0, removidos 2.2 | `download_name=`, `max_age=` | `attachment_filename\|cache_timeout` |
| `flask.safe_join` | removido 2.1 | `werkzeug.utils.safe_join` | `from flask import .*safe_join` |
| `flask.__version__` | deprecated 3.0 | `importlib.metadata.version("flask")` | `flask\.__version__` |
| `werkzeug.urls.url_quote`, `url_encode`, `url_parse` | removidos Werkzeug 3.0 | `urllib.parse.quote`, `urlencode`, `urlsplit` | `werkzeug\.urls` |
| `request.get_json(force=True)` para contornar content-type | legado | validar `request.is_json` e responder 400/415 | `get_json\(force=True` |

## 3. SQLAlchemy / Flask-SQLAlchemy / marshmallow

| API obsoleta | Desde | Substituto moderno | Como detectar |
|---|---|---|---|
| `Model.query.get(id)` / `session.query(Model).get(id)` | legado SQLAlchemy 2.0 (`LegacyAPIWarning`); Flask-SQLAlchemy 3.x exige SQLAlchemy 2.x | `db.session.get(Model, id)` | `\.query\.get\(\|query\(\w+\)\.get\(` |
| `Model.query.get_or_404(id)` | Flask-SQLAlchemy 3.0 | `db.get_or_404(Model, id)` | `query\.get_or_404\(` |
| `Model.query.paginate(page, per_page)` posicional | Flask-SQLAlchemy 3.0 (somente keyword) | `db.paginate(db.select(Model), page=, per_page=)` | `\.paginate\(\s*\w+\s*,` |
| `engine.execute(...)`, `connection.execute("SQL string")` | removidos SQLAlchemy 2.0 | `with engine.connect() as c: c.execute(text("..."), params)` | `engine\.execute\(\|\.execute\(\s*["']` (com SQLAlchemy) |
| `from sqlalchemy.ext.declarative import declarative_base` | movido 1.4, deprecated 2.0 | `from sqlalchemy.orm import DeclarativeBase` | `ext\.declarative import` |
| API `Model.query` / `Query` em geral (`filter_by().first()`, `.all()`, `.count()`) | legado (sem aviso) | `db.session.execute(db.select(Model).filter_by(...)).scalars()` | — (recomendação complementar, regra 4) |
| `relationship(backref=...)` | legado (sem aviso) | `back_populates` explícito nos dois lados | — (regra 4) |
| marshmallow `fields.X(missing=..., default=...)` | deprecated 3.13 | `load_default=`, `dump_default=` | `missing=\|default=` em `fields\.` |
| marshmallow `@validates_schema(pass_original=True)` sem `**kwargs` | 3.x | assinatura `(self, data, **kwargs)` | `validates_schema` |

## 4. Node.js (core)

| API obsoleta | Desde | Substituto moderno | Como detectar |
|---|---|---|---|
| `new Buffer(x)` / `Buffer(x)` | DEP0005 (runtime) | `Buffer.from(x)`, `Buffer.alloc(n)` | `new Buffer\(\|[^.]Buffer\(` |
| `url.parse(str)` | DEP0169 (doc) / DEP0116 legado | `new URL(str, base)` | `url\.parse\(` |
| `fs.exists(path, cb)` | DEP0034 | `fs.existsSync()` ou `fs.promises.access()` | `fs\.exists\(` |
| `fs.rmdir(path, { recursive: true })` | DEP0147 | `fs.rm(path, { recursive: true, force: true })` | `rmdir\(.*recursive` |
| `util.isArray`, `util.isDate`, `util.isString`, ... | DEP0044–DEP0058 (removidos no Node 23) | `Array.isArray`, `instanceof Date`, `typeof x === 'string'` | `util\.is[A-Z]\w*\(` |
| `util._extend` | DEP0060 | `Object.assign()` / spread | `util\._extend` |
| `crypto.createCipher` / `createDecipher` | DEP0106, removidos no Node 22 | `crypto.createCipheriv` / `createDecipheriv` com IV | `createCipher\(\|createDecipher\(` |
| `crypto.pbkdf2(..)` sem `digest` | DEP0009 | informar `digest` (`'sha512'`) | `pbkdf2(Sync)?\(` com 4 argumentos |
| `domain` | DEP0032 | `AsyncLocalStorage`, tratamento explícito de erros | `require\(['"]domain['"]\)` |
| `require('punycode')` | DEP0040 | `url.domainToASCII` / pacote `punycode/` | `require\(['"]punycode['"]\)` |
| `querystring` | legado | `URLSearchParams` | `require\(['"]querystring['"]\)` |
| `process.binding()` | DEP0111 | APIs públicas equivalentes | `process\.binding\(` |
| `EventEmitter.listenerCount(emitter, ev)` | DEP0033 | `emitter.listenerCount(ev)` | `EventEmitter\.listenerCount\(` |
| `new SlowBuffer(n)` | DEP0030 | `Buffer.allocUnsafeSlow(n)` | `SlowBuffer` |

## 5. Express

| API obsoleta | Desde | Substituto moderno | Como detectar |
|---|---|---|---|
| `req.param(name)` | deprecated 4.11, removido 5 | `req.params[name]`, `req.query[name]`, `req.body[name]` | `req\.param\(` |
| `res.send(status)` com número / `res.send(body, status)` | deprecated 4 | `res.sendStatus(n)` / `res.status(n).send(body)` | `res\.send\(\s*\d{3}\s*\)\|res\.send\(.*,\s*\d{3}\s*\)` |
| `res.json(obj, status)` / `res.json(status, obj)` | deprecated 4 | `res.status(n).json(obj)` | `res\.json\(\s*\d{3}\s*,\|res\.json\(.*,\s*\d{3}\s*\)` |
| `res.redirect(url, status)` | deprecated 4 | `res.redirect(status, url)` | `res\.redirect\(\s*["'].*,\s*\d{3}` |
| `res.sendfile()` | deprecated 4.8 | `res.sendFile()` (caminho absoluto ou `root`) | `res\.sendfile\(` |
| `app.del()` | deprecated 4, removido 5 | `app.delete()` | `app\.del\(` |
| `req.acceptsCharset`, `acceptsEncoding`, `acceptsLanguage` (singular) | deprecated 4 | formas no plural (`acceptsCharsets`, ...) | `accepts(Charset\|Encoding\|Language)\(` |
| `bodyParser()` (construtor genérico) / `body-parser` só para JSON/urlencoded | 4.16 incorporou | `express.json()`, `express.urlencoded({ extended: false })` | `bodyParser\(\)\|bodyParser\.json\(` |
| `express.createServer()` / `app.configure()` | removidos 4 | `express()` / condicionais por `NODE_ENV` | `createServer\(\)\|app\.configure\(` |

## 6. Pacotes npm comuns

| Pacote/API obsoleto | Situação | Substituto moderno (sem nova dependência quando possível) | Como detectar |
|---|---|---|---|
| `request`, `request-promise` | deprecated (2020) | `fetch` nativo (Node ≥ 18) | `require\(['"]request(-promise)?['"]\)` |
| `node-uuid` | deprecated | `crypto.randomUUID()` | `node-uuid` |
| `crypto` (pacote npm) | deprecated | módulo core `node:crypto` | `"crypto":` em `package.json` |
| `mkdirp`, `rimraf` | substituídos pelo core | `fs.mkdir(p, { recursive: true })`, `fs.rm(p, { recursive: true, force: true })` | `require\(['"](mkdirp\|rimraf)['"]\)` |
| `moment` | modo manutenção | `Intl.DateTimeFormat`, `Date` | `require\(['"]moment['"]\)` |
| `mongoose` com callbacks (`Model.find(q, cb)`) | callbacks removidos no Mongoose 7 | `await Model.find(q)` | `\.(find\|findOne\|save)\(.*function\s*\(err` |
| `sqlite3` / `mysql` com callbacks aninhados | legado (estilo) | wrapper com `util.promisify` / Promises + `async/await` | ver AP-10 (não é AP-16) |

## 7. Pacotes Python comuns

| Pacote/API obsoleto | Situação | Substituto moderno | Como detectar |
|---|---|---|---|
| `flask_script` | abandonado | `flask` CLI (`@app.cli.command`) | `flask_script` |
| `nose` | sem manutenção | `pytest` / `unittest` | `import nose` |
| `requests` com `verify=False` | inseguro (não deprecated) | manter verificação TLS | `verify=False` (reportar como AP-11) |
| `json.loads(..., encoding=)` | removido 3.9 | omitir `encoding` | `json\.loads\(.*encoding=` |
