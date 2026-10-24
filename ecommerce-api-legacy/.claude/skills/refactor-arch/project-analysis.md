# Project Analysis — heurísticas da Fase 1

> Carregado na Fase 1. Tudo aqui é **somente leitura**: use Read, Glob, Grep e comandos de shell que apenas leem.
> Objetivo: produzir o bloco `PHASE 1: PROJECT ANALYSIS` e um modelo mental do projeto (§10) reutilizado nas Fases 2 e 3.

## 1. Ordem de trabalho

1. Inventário de arquivos (§2) → 2. Linguagem (§3) → 3. Framework, versão e dependências (§4) → 4. Banco e tabelas (§5) → 5. Rotas (§6) → 6. Entry point, boot, porta, seed (§7) → 7. Domínio (§8) → 8. Classificação da arquitetura (§9) → 9. Contagem (§2.3) → 10. Bloco de saída (§11).

## 2. Inventário de arquivos

### 2.1 Listagem determinística

Prefira a listagem do Git, que respeita o `.gitignore` (exclui venvs, `node_modules`, bancos gerados):

```bash
git ls-files --cached --others --exclude-standard
```

Se o diretório não for repositório Git, use Glob por extensão e **filtre manualmente** os diretórios excluídos (§2.2). Nunca conte o que veio de `node_modules/`, `.venv/` etc. — um Glob `**/*.py` ingênuo inclui milhares de arquivos de dependências.

### 2.2 Sempre excluir

`.claude/`, `.git/`, `node_modules/`, `.venv/`, `venv/`, `env/`, `site-packages/`, `__pycache__/`, `dist/`, `build/`, `target/`, `bin/`, `obj/`, `vendor/`, `coverage/`, `.next/`, `instance/`, arquivos minificados (`*.min.js`), bancos (`*.db`, `*.sqlite*`).

### 2.3 Critério de "Source files" e LOC

- **Conte** todos os arquivos com a extensão da linguagem principal que pertencem à aplicação: entry point, módulos, pacotes, **`__init__.py` vazios inclusive**, e scripts auxiliares (seed, migrations escritas à mão, CLI do projeto).
- **Não conte**: manifestos e lockfiles (`requirements.txt`, `package.json`, `package-lock.json`), `.md`, `.http`, `.json`, `.yml`, `.env*`, arquivos de configuração de ferramentas (`*.config.js`, `.eslintrc.*`, `setup.cfg`), testes de terceiros e tudo de §2.2.
- Extensões por linguagem: Python `.py`; JavaScript `.js`, `.mjs`, `.cjs`, `.jsx`; TypeScript `.ts`, `.tsx`; Go `.go`; Java `.java`; Kotlin `.kt`; PHP `.php`; Ruby `.rb`; C# `.cs`.
- **LOC** = soma das linhas físicas dos arquivos contados (ex.: `wc -l <arquivos>`; ou o número da última linha retornada pelo Read). É apresentado com `~` no relatório.

## 3. Linguagem (por manifesto, em ordem de prioridade)

| Manifesto/arquivo na raiz (ou em subpasta da app) | Linguagem |
|---|---|
| `pyproject.toml`, `requirements*.txt`, `Pipfile`, `setup.py`, `setup.cfg` | Python |
| `package.json` | JavaScript (Node.js); TypeScript se houver `tsconfig.json` ou dependência `typescript` e arquivos `.ts` |
| `go.mod` | Go |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java / Kotlin |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `*.csproj`, `*.sln` | C# |
| nenhum manifesto | extensão dominante entre os arquivos-fonte (declare que foi inferido) |

Confirme pela extensão dominante dos arquivos listados em §2. Em repositórios com mais de uma linguagem, a principal é a do entry point do servidor HTTP.

## 4. Framework, versão e dependências

### 4.1 Framework (dependência declarada + import no entry point)

| Ecossistema | Dependência no manifesto | Import/uso que confirma |
|---|---|---|
| Python | `flask` | `from flask import Flask`, `Flask(__name__)` |
| Python | `fastapi` | `FastAPI()`, `APIRouter` |
| Python | `django` | `manage.py`, `settings.py`, `urls.py` |
| Node | `express` | `require('express')` / `import express`, `express()` |
| Node | `fastify` | `require('fastify')` |
| Node | `koa` | `new Koa()` |
| Node | `@nestjs/core` | `NestFactory.create` |
| Go | `github.com/gin-gonic/gin`, `github.com/labstack/echo` | `gin.Default()`, `echo.New()` |
| Java | `spring-boot-starter-web` | `@SpringBootApplication`, `@RestController` |
| PHP | `laravel/framework`, `slim/slim` | `Route::get`, `$app->get` |
| Ruby | `rails`, `sinatra` | `config/routes.rb`, `get '/' do` |

### 4.2 Resolução da versão (primeira fonte disponível vence)

1. **Lockfile**: `package-lock.json` (chave `"node_modules/<pacote>"` → `"version"`), `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`, `composer.lock`, `Gemfile.lock`, `go.sum`.
2. **Pin exato** no manifesto: `flask==3.1.1` → `3.1.1`.
3. **Faixa declarada**: `^4.18.2` ou `~4.18` → `4.x`; `>=3.0` → `>=3.0`.
4. Nada declarado → omitir a versão e escrever `(versão não declarada)`.

Escreva só a versão resolvida (ex.: `Express 4.22.1`, `Flask 3.1.1`), sem a faixa.

### 4.3 Dependencies

Liste as **demais dependências de runtime** declaradas (sem o framework, sem dependências de desenvolvimento/teste), na ordem do manifesto, separadas por vírgula. Use o nome como declarado (versão opcional). Extensões do framework (ex.: ORM, CORS) entram aqui.

## 5. Banco de dados e tabelas

### 5.1 Engine

| Sinal | Engine |
|---|---|
| `import sqlite3`, `sqlite3` (npm), `better-sqlite3`, URI `sqlite:///arquivo`, arquivos `*.db`/`*.sqlite` | SQLite |
| `psycopg2`, `asyncpg`, `pg` (npm), URI `postgres://`/`postgresql://` | PostgreSQL |
| `pymysql`, `mysqlclient`, `mysql2` (npm), URI `mysql://` | MySQL/MariaDB |
| `pymongo`, `mongoose`, `mongodb` (npm), URI `mongodb://` | MongoDB |
| `sqlalchemy`, `flask_sqlalchemy`, `sequelize`, `typeorm`, `prisma`, `knex` | ORM/query builder — engine pela URI/dialeto configurado |

Distinga **arquivo** (`sqlite:///nome.db`, `connect("nome.db")`) de **memória** (`:memory:`, `sqlite://` sem caminho). Para Flask-SQLAlchemy, URIs SQLite relativas são resolvidas dentro da pasta `instance/` da aplicação.

### 5.2 Tabelas/entidades

Extraia, nesta ordem de confiabilidade:

1. DDL explícito: `CREATE TABLE [IF NOT EXISTS] <nome>`.
2. ORM: `__tablename__ = '<nome>'`; sem `__tablename__`, Flask-SQLAlchemy usa o nome da classe em snake_case; Sequelize `sequelize.define('<nome>')`/`tableName`; TypeORM `@Entity('<nome>')`; Prisma `model <Nome>`; Mongoose `model('<Nome>', schema)`; Django: classes `models.Model` (`<app>_<modelo>`).
3. Migrations versionadas, se existirem.

Liste as tabelas na ordem em que aparecem no schema.

## 6. Rotas (inventário método + path)

| Framework | Padrões de registro | Prefixos a compor |
|---|---|---|
| Flask | `@app.route(path, methods=[...])`, `@<bp>.route(...)`, `@app.get/post/...`, `app.add_url_rule(path, endpoint, view, methods=[...])` | `Blueprint(..., url_prefix=)` e `register_blueprint(bp, url_prefix=)` |
| FastAPI | `@app.get(...)`, `@router.post(...)` | `APIRouter(prefix=)`, `include_router(router, prefix=)` |
| Django | `path()`/`re_path()` em `urls.py` | `include()` |
| Express | `app.get/post/put/patch/delete(path, ...)`, `router.<verbo>(...)`, `app.route(path).get(...)` | `app.use('/prefixo', router)` |
| Fastify/Koa | `fastify.get(...)`, `router.get(...)` (koa-router) | `register(plugin, { prefix })` |
| Spring | `@GetMapping`, `@PostMapping`, `@RequestMapping` | `@RequestMapping` na classe |

Regras:
- Flask sem `methods=` → apenas `GET` (HEAD/OPTIONS automáticos não contam).
- Expanda rotas com vários métodos em **combinações método + path** (é o número que vai em `Endpoints:`).
- Preserve o formato do parâmetro como escrito (`<int:id>`, `:id`), pois a Fase 3 precisa mantê-lo.
- Registre, para cada rota: método, path completo, arquivo:linha do registro e função/handler.
- Registre também a **ordem de registro** (rotas estáticas como `/x/search` antes de `/x/<id>` podem depender dela).

## 7. Entry point, comando de boot, porta, seed e interpretador

| Item | Onde procurar |
|---|---|
| Comando de boot | Seção "Como rodar"/"Run" do README; `package.json` → `scripts.start` (senão `main`); `Procfile`; bloco `if __name__ == "__main__":` com `app.run(...)`; `manage.py runserver`; `uvicorn ...` |
| Entry point | Arquivo chamado pelo comando de boot |
| Porta e host | Argumentos de `app.run(host=, port=)`, `app.listen(<porta>)`, objeto de config, variável `PORT`; default do framework se ausente (Flask 5000, Express sem default — exige valor) |
| Seed | Scripts `seed.*`, `fixtures`, `init_db`, menção no README ("rode antes do primeiro boot"); seed embutido no boot (INSERTs no código de inicialização) |
| Interpretador | Venv local `.venv/` ou `venv/` → Windows `.venv\Scripts\python.exe`, POSIX `.venv/bin/python`; Node → `node` do PATH; dependências instaladas? (`node_modules/` presente) |
| Arquivos de banco gerados | Caminho do banco em arquivo e se está ignorado pelo Git (`git check-ignore -v <arquivo>`) |

## 8. Domínio

Combine, nesta ordem: (1) nomes das tabelas/entidades; (2) prefixos de rota; (3) descrição do README. Escreva 1 frase curta + entidades principais entre parênteses.

- Exemplo genérico: `API de agendamento (clientes, consultas, profissionais)`.
- Exemplo genérico: `Venda de ingressos com fluxo de pagamento (eventos, ingressos, pagamentos, clientes)`.
- **Não deduza o domínio pelo nome do diretório ou do pacote** — ele pode ser enganoso ou genérico. Entidades e rotas prevalecem; em caso de conflito com o README, descreva o que o código faz.

## 9. Classificação da arquitetura

| Classe | Rótulo no bloco | Sinais (basta a maioria) |
|---|---|---|
| `monolith` | `Monolítica` | Poucos arquivos na raiz ou em uma pasta única; um mesmo arquivo/classe registra rotas **e** executa SQL/ORM **e** contém regra de negócio; nenhuma pasta por camada; "controllers" que são só funções soltas chamando SQL |
| `partial-layers` | `Parcialmente em camadas` | Existem algumas pastas por camada (`models/`, `routes/`, `services/`, `utils/`), mas: regra de negócio e queries dentro das rotas; ausência de controllers, de módulo de config ou de error handler central; camadas existentes não usadas (serviços/utilitários mortos) |
| `layered` | `Em camadas` | Config, models, controllers, routes/views e error handling já separados e usados; a Fase 3 atua só sobre findings pontuais |

No detalhe da linha `Architecture:` descreva o porquê em 1 linha, citando as pastas/arquivos reais (ex.: `— tudo em 3 arquivos, sem separação de camadas`; `— models/routes/services/utils, sem controllers nem config`).

## 10. Modelo mental para as próximas fases (guardar, não imprimir)

- Lista dos arquivos contados (caminhos relativos) e LOC total.
- Linguagem, framework + versão, engine do banco, arquivo do banco (ou memória), tabelas.
- Inventário de rotas: método, path, arquivo:linha, handler, ordem de registro; rotas administrativas/destrutivas destacadas.
- Comando de boot exato, entry point, porta, host, seed (comando e ordem), interpretador.
- Classificação (`monolith` / `partial-layers` / `layered`) e quais camadas existem e quais faltam.
- Símbolos importados entre módulos por scripts auxiliares (ex.: seed que importa `app`/`db` do entry point) — a Fase 3 precisa mantê-los.

## 11. Bloco de saída da Fase 1 (formato exato)

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <Python | JavaScript (Node.js) | TypeScript (Node.js) | Go | ...>
Framework:     <Nome> <versão resolvida>
Dependencies:  <deps de runtime separadas por vírgula, sem o framework>
Domain:        <descrição curta> (<entidades principais>)
Architecture:  <Monolítica | Parcialmente em camadas | Em camadas> — <detalhe em 1 linha>
Source files:  <N> files analyzed
DB tables:     <tabela1, tabela2, ...> (<engine>, <arquivo nome.db | em memória>)
Endpoints:     <N> routes
================================
```

Regras de preenchimento:
- Rótulo + `:` + espaços até a coluna 16 (o valor começa sempre na mesma coluna).
- `Source files` segue §2.3; `Endpoints` é o número de combinações método + path de §6.
- Sem banco: `DB tables:     none`.
- Imprima como texto puro, sem cercas de código.

Exemplo sintético (não corresponde a nenhum projeto real):

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     FastAPI 0.110.0
Dependencies:  sqlalchemy, pydantic, uvicorn
Domain:        API de agendamento (clientes, consultas, profissionais)
Architecture:  Monolítica — rotas, SQL e regras em 2 arquivos na raiz
Source files:  5 files analyzed
DB tables:     clients, appointments, professionals (SQLite, arquivo agenda.db)
Endpoints:     12 routes
================================
```
