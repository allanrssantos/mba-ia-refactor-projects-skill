## Checklist de Validação — Projeto 3 (task-manager-api)

Execução: skill `refactor-arch` (HEAD `a6415bb`), Claude Code 2.1.310, em 2026-10-24, a partir de `task-manager-api/`, via PowerShell 5.1.
- Etapa 1 (Fases 1–2): `claude -p "/refactor-arch" --permission-mode plan` → `stage1.log` (UTF-16 LE, gravado pelo `Tee-Object`).
- Etapa 2 (Fase 3): `claude -p --continue "y" --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep"` → `stage2.log`.
- Tentativa anterior descartada: `stage1-attempt1.log` (+ `stage1-attempt1-git-status.txt`, vazio). O relatório veio correto (34 findings), mas o bloco PHASE 1 não foi impresso em nenhuma mensagem da sessão (conferido no transcript `.jsonl`). A etapa 1 foi repetida uma vez; a sessão abandonada não recebeu "n". O relatório oficial e a Fase 3 são da mesma sessão (a segunda).

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — `Language: Python`.
- [x] Framework detectado corretamente — `Framework: Flask 3.0.0`; `Dependencies: flask-sqlalchemy, flask-cors, marshmallow, requests, python-dotenv`.
- [x] Domínio da aplicação descrito corretamente — `Gerenciamento de tarefas com usuários, categorias e relatórios de produtividade (tasks, users, categories)` (Task Manager); `Architecture: Parcialmente em camadas — models/routes/services/utils existem, mas regras e queries ficam nas rotas; sem controllers, config nem error handler; services/ e utils/ não são usados` (bate com a análise manual); `DB tables: tasks, users, categories (SQLite, arquivo tasks.db em instance/)`.
- [x] Número de arquivos analisados condiz com a realidade — `Source files: 15 files analyzed` (referência CA-01 = 15 `.py` incluindo `__init__.py`); `Endpoints: 22 routes` (SPEC 7.5 = 22).

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência — `reports/audit-project-3.md` (extraído com `scripts/extract-report.ps1`, sem edição).
- [x] Cada finding tem arquivo e linhas exatos — 31/31 com `File:`; conferência por amostragem no original: `models/category.py:11` (`default=datetime.utcnow`), `routes/report_routes.py:105` (`User.query.get`), `models/user.py:21` (`'password': self.password`), `models/user.py:29` (MD5), `services/notification_service.py:10` (`'senha123'`), `app.py:34` (`debug=True, host='0.0.0.0'`), `routes/task_routes.py:113` (comparação de `priority` sem tipo) — todos corretos.
- [x] Findings ordenados por severidade (CRITICAL → LOW) — 5 CRITICAL, 6 HIGH, 13 MEDIUM, 7 LOW, nessa ordem.
- [x] Mínimo de 5 findings identificados — `Total: 31 findings` = 31 blocos `### [`; CRITICAL+HIGH = 11.
- [x] Detecção de APIs deprecated incluída (se aplicável) — 2 findings `[MEDIUM] Deprecated API Usage`: `datetime.utcnow()` (Python 3.12) e `Model.query.get()` (SQLAlchemy 2.x, com `db.session.get` como substituto; cita também `backref` → `back_populates`).
- [x] Skill pausa e pede confirmação antes da Fase 3 — `stage1.log` termina em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`; `stage1-git-status.txt` vazio (0 bytes).

Cobertura da análise manual (`docs/manual-analysis.md`): 14/14 (3.1 `app.py:13` + `services/notification_service.py:10`; 3.2 `models/user.py:21`; 3.3 `models/user.py:29`; 3.4 `routes/task_routes.py:85-154`, `routes/report_routes.py:12-101`; 3.5 `app.py:9-31`; 3.6 `app.py:34`; 3.7 N+1 em `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-56`; 3.8 cálculo de atraso duplicado `routes/report_routes.py:34-36`, `routes/task_routes.py:17-28`; 3.9 deprecated; 3.10 `routes/task_routes.py:62-63`; 3.11 `routes/task_routes.py:113`, `routes/report_routes.py:196-197`; 3.12 `app.py:7` (imports/código morto); 3.13 magic strings; 3.14 `routes/report_routes.py:24-28` e `print` em `routes/task_routes.py:149`).

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — evolução incremental (ADR-09): `models/`, `routes/`, `services/`, `utils/` mantidos na raiz; novos `config/`, `controllers/`, `middlewares/`. Não houve reescrita em `src/`.
- [x] Configuração extraída para módulo de config (sem hardcoded) — `config/settings.py`; `.env.example` (SECRET_KEY, DEBUG, HOST, PORT, DATABASE_URI, CORS_ORIGINS, LOG_LEVEL). `grep -rnE "SECRET_KEY *= *['\"]|super-secret|senha123|password *= *['\"]..."` → sem ocorrências; `services/notification_service.py` (SMTP hardcoded, nunca usado) removido.
- [x] Models criados para abstrair dados — `models/{task,user,category}.py` com queries/agregações (`selectinload`, `GROUP BY`), `PUBLIC_FIELDS` sem `password`, hash werkzeug com aceitação do MD5 legado e rehash transparente (ADR-12).
- [x] Views/Routes separadas para visualização ou roteamento — `routes/*.py` só mapeiam método+path → controller (`routes/__init__.py: register_routes`, mesma ordem); `category_routes.py` e `health_routes.py` extraídos.
- [x] Controllers concentram o fluxo da aplicação — `controllers/{task,user,category,report,health}_controller.py`; regras em `services/{task,user,category,report}_service.py`.
- [x] Error handling centralizado — `middlewares/error_handler.py` (`AppError` → status; `Exception` → 500 `{"error": "Erro interno"}` com log); `database.py` com commit/rollback.
- [x] Entry point claro — `app.py` com `create_app()` (entry point + composition root) e `app = create_app()` no módulo, para `seed.py` continuar importando; boot inalterado: `python seed.py` + `python app.py`.
- [x] Aplicação inicia sem erros — `baseline-after-boot.log`: `Debug mode: off`, `Running on http://127.0.0.1:5000`, nenhum `Traceback`/`Error` (a única linha `WARNING` é o aviso padrão do servidor de desenvolvimento do Werkzeug). Boot pelo `.venv` do projeto. `seed-after.log`: `python -W error::DeprecationWarning seed.py` → exit 0, 3 usuários, 4 categorias, 10 tasks (antes o seed emitia `DeprecationWarning` de `utcnow()`).
- [x] Endpoints originais respondem corretamente — `scripts/smoke-project-3.ps1` → `baseline-after.txt`: **35/35 requisições idênticas** a `baseline-before.txt` (`diff` sem saída). `app.url_map` lista as 22 combinações método+path originais. Inclui `PUT /tasks/11` parcial → 200 (igual à baseline); a validação do PUT continua campo a campo (`utils/validators.py: validate_task_update`, mesmas regras e mensagens do original).

Divergências: nenhuma no plano do smoke. Mudanças fora do plano, relatadas pela skill no `stage2.log` e previstas na ADR-11:
- `GET /tasks/search?priority=x` e `POST /tasks` com `priority` string: 500 → 400 — ADR-11(d).
- `password` removido de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` (`user.password`) — ADR-11(a), status inalterado.
- JSON compacto em vez de indentado (efeito de `DEBUG=false`); mesmas chaves e content-type. HOST padrão `0.0.0.0` → `127.0.0.1`.

Resíduos: nenhum `*.db` no projeto (`instance/` vazio); porta 5000 livre; `__pycache__/` ignorado pelo Git.

### Árvore de diretórios

Antes (arquivos versionados, sem `.claude/`):
```
task-manager-api/
├── README.md
├── app.py
├── database.py
├── requirements.txt
├── seed.py
├── models/    __init__.py, category.py, task.py, user.py
├── routes/    __init__.py, report_routes.py, task_routes.py, user_routes.py
├── services/  __init__.py, notification_service.py
└── utils/     __init__.py, helpers.py
```

Depois:
```
task-manager-api/
├── .env.example                (novo)
├── README.md                   (inalterado)
├── app.py                      (entry point + composition root: create_app)
├── database.py                 (db + commit com rollback)
├── requirements.txt            (inalterado)
├── seed.py                     (mesmo comando)
├── config/       __init__.py, settings.py                                   (novo)
├── controllers/  __init__.py, task_controller.py, user_controller.py,
│                 category_controller.py, report_controller.py,
│                 health_controller.py                                       (novo)
├── middlewares/  __init__.py, error_handler.py                             (novo)
├── models/       __init__.py, category.py, task.py, user.py                (mantido)
├── routes/       __init__.py, task_routes.py, user_routes.py, report_routes.py,
│                 category_routes.py (novo), health_routes.py (novo)
├── services/     __init__.py, task_service.py, user_service.py,
│                 category_service.py, report_service.py   (notification_service.py removido)
└── utils/        __init__.py, constants.py, errors.py, validators.py,
                  numbers.py, time.py                       (helpers.py removido)
```
34 arquivos `.py`, 1331 linhas (antes: 15 arquivos). `git diff --stat` nos arquivos versionados: 12 arquivos, +316/−991.
