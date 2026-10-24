## Checklist de Validação — Projeto 1 (code-smells-project)

Execução: skill `refactor-arch` (HEAD `a6415bb`), Claude Code 2.1.310, em 2026-10-24, a partir de `code-smells-project/`.
- Etapa 1 (Fases 1–2): `claude -p "/refactor-arch" --permission-mode plan` via PowerShell 5.1 → `stage1.log` (UTF-16 LE, gravado pelo `Tee-Object`).
- Etapa 2 (Fase 3): `claude -p --continue "y" --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep"` → `stage2.log`.
- Calibração (1 rodada, descartada): `stage1-calib.log` (+ `stage1-calib-git-status.txt`, vazio). Foi disparada pelo Git Bash: a conversão de caminhos do MSYS transformou `/refactor-arch` em caminho do Windows (o modelo carregou a skill mesmo assim), e o bloco PHASE 1 não foi impresso. Por isso a etapa 1 oficial foi refeita pelo PowerShell; a sessão de calibração foi abandonada (sem "n"), e a etapa 2 continuou a sessão oficial.

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — `Language: Python` (`stage1.log`, bloco PHASE 1).
- [x] Framework detectado corretamente — `Framework: Flask 3.1.1` (bate com `requirements.txt`).
- [x] Domínio da aplicação descrito corretamente — `API de e-commerce com catálogo, cadastro/login e pedidos (produtos, usuários, pedidos, itens de pedido)`; `Architecture: Monolítica`; `DB tables: produtos, usuarios, pedidos, itens_pedido (SQLite, arquivo loja.db)`.
- [x] Número de arquivos analisados condiz com a realidade — `Source files: 4 files analyzed` (app.py, controllers.py, database.py, models.py; referência CA-01 = 4) e `Endpoints: 19 routes` (SPEC 7.5 = 19).

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência — `reports/audit-project-1.md` (extraído com `scripts/extract-report.ps1`, sem edição): cabeçalho, `## Summary`, `## Findings`, `Total:` e pergunta final; cada finding com `File/Description/Impact/Recommendation (T-xx)`.
- [x] Cada finding tem arquivo e linhas exatos — 33/33 blocos com `File: caminho:linhas`; conferência por amostragem no código original: `app.py:7` (SECRET_KEY), `app.py:61-69` (`/admin/query` → `cursor.execute(query)`), `database.py:4-10` (conexão global), `controllers.py:285-289` (`/health` com `secret_key`) — todos corretos.
- [x] Findings ordenados por severidade (CRITICAL → LOW) — 11 CRITICAL, 9 HIGH, 7 MEDIUM, 6 LOW, nessa ordem. Observação: dentro de MEDIUM/Duplicated Code, `models.py` aparece antes de `controllers.py` (o desempate por caminho da skill pediria o inverso); não afeta a ordem por severidade.
- [x] Mínimo de 5 findings identificados — `Total: 33 findings` = 33 blocos `### [` (CA-02); CRITICAL+HIGH = 20 (CA-03).
- [x] Detecção de APIs deprecated incluída (se aplicável) — a skill carregou `deprecated-apis.md` (seção Python/Flask) e procurou os padrões; nenhum presente no projeto 1, portanto nenhum finding AP-16 (correto: o código usa só `sqlite3` e APIs atuais do Flask 3.1).
- [x] Skill pausa e pede confirmação antes da Fase 3 — `stage1.log` termina em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`; `stage1-git-status.txt` vazio (0 bytes: `git status --porcelain -- .` sem saída).

Cobertura da análise manual (`docs/manual-analysis.md`, CA-06): 14/14 problemas aparecem no relatório (1.1 SQLi `models.py:109-111`; 1.2 admin `app.py:47-57`; 1.3 `app.py:7`; 1.4 `controllers.py:285-289` e `models.py:83`; 1.5 `database.py:75-83` e `models.py:126-129`; 1.6 `models.py:1-314`; 1.7 `database.py:4-10`; 1.8 `app.py:8`/`:88`; 1.9 `models.py:133-169`; 1.10 `models.py:177-199`; 1.11 `controllers.py:169-171`; 1.12 `controllers.py:10-12`; 1.13 `controllers.py:52`, `models.py:257-262`; 1.14 `controllers.py:8`).

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — `src/{config,models,services,controllers,routes,middlewares,utils}` + `app.py` fino (árvore abaixo).
- [x] Configuração extraída para módulo de config (sem hardcoded) — `src/config/settings.py` é o único leitor de ambiente; `.env.example` documenta PORT, HOST, DEBUG, DB_PATH, SECRET_KEY, CORS_ORIGINS, ADMIN_TOKEN, LOG_LEVEL. `grep -rnE "SECRET_KEY *= *['\"]|minha-chave|senha *= *['\"]..." src app.py` → sem ocorrências.
- [x] Models criados para abstrair dados — `src/models/{produto,usuario,pedido,admin}_model.py`, `database.py` (conexão por requisição via `flask.g`), `seguranca.py` (hash werkzeug + rehash do legado), `constants.py`; todas as queries parametrizadas.
- [x] Views/Routes separadas para visualização ou roteamento — `src/routes/*_routes.py` (Blueprints, mesmos paths/métodos e ordem de registro).
- [x] Controllers concentram o fluxo da aplicação — `src/controllers/*_controller.py` (entrada → validador → model/service → resposta); checkout transacional em `src/services/pedido_service.py`.
- [x] Error handling centralizado — `src/middlewares/error_handler.py` (`AppError` → status; `Exception` → 500 genérico `{"erro": "Erro interno"}` com log); os 17 `except Exception` foram removidos.
- [x] Entry point claro — `app.py` (raiz) → `create_app()` em `src/app.py` (composition root); comando de boot inalterado: `python app.py` (ADR-06).
- [x] Aplicação inicia sem erros — `baseline-after-boot.log` e `after-notoken-boot.log`: `Running on http://127.0.0.1:5000`, `Debug mode: off`, 0 ocorrências de `Traceback`/`Error`. Boot pelo venv do projeto (`.venv\Scripts\python.exe app.py`, `scripts/smoke.ps1` linha 144).
- [x] Endpoints originais respondem corretamente — `scripts/smoke-project-1.ps1`:
  - com `-AdminToken s3cret` → `baseline-after.txt`: 29/29 linhas idênticas a `baseline-before.txt` (só o cabeçalho muda: `admin_token=set`);
  - sem token → `after-notoken.txt`: 26/29 idênticas; 3 divergências, todas previstas na ADR-03/ADR-11(b):

| Requisição | Antes | Depois (sem token) | Depois (com token) | Justificativa |
|---|---|---|---|---|
| `POST /admin/query` (SQL válido) | 200 | 403 | 200 | guard admin (ADR-03) |
| `POST /admin/query` (sem SQL) | 400 | 403 | 400 | guard admin roda antes da validação (ADR-03) |
| `POST /admin/reset-db` | 200 | 403 | 200 | guard admin (ADR-03) |

Mudanças de comportamento fora do plano do smoke (relatadas pela própria skill no `stage2.log`):
- 500 → 400 em entradas inválidas (`/produtos/busca?preco_min=abc`, `POST /produtos` com `preco` string, `POST /login` sem corpo) — ADR-11(d).
- `GET /health` sem `secret_key`, `db_path`, `debug`, `ambiente`; `GET /usuarios[/<id>]` sem `senha` — ADR-11(a), status inalterado.
- `PUT /produtos/<id>` passou a aplicar as mesmas regras do POST (nome com 2–200 caracteres, categoria válida): um PUT que antes gravava categoria inválida agora responde 400. **Não está na lista fechada da ADR-11** (é a correção do problema manual 1.11); não é exercitado pelo smoke. Mantido, mas registrado para decisão do orquestrador.
- HOST padrão `0.0.0.0` → `127.0.0.1` e `DEBUG` padrão `false` (AP-11); porta 5000 mantida.

Resíduos: nenhum `*.db` no projeto após o smoke; porta 5000 livre (`netstat` sem LISTEN); `__pycache__/` (ignorado pelo Git) pode existir.
Findings residuais declarados pela skill: SQL arbitrário em `/admin/query` com token válido (risco aceito pela ADR-03) e `DELETE /produtos/<id>` sem tratar `itens_pedido` históricos.

### Árvore de diretórios

Antes (arquivos versionados, sem `.claude/`):
```
code-smells-project/
├── README.md
├── app.py
├── controllers.py
├── database.py
├── models.py
└── requirements.txt
```

Depois:
```
code-smells-project/
├── .env.example
├── README.md                 (inalterado)
├── app.py                    (entry point fino: create_app + app.run)
├── requirements.txt          (inalterado)
└── src/
    ├── __init__.py
    ├── app.py                (composition root: create_app)
    ├── config/        __init__.py, settings.py
    ├── models/        __init__.py, database.py, seguranca.py, constants.py,
    │                  produto_model.py, usuario_model.py, pedido_model.py, admin_model.py
    ├── services/      __init__.py, pedido_service.py, notificacao_service.py
    ├── controllers/   __init__.py, produto_controller.py, usuario_controller.py,
    │                  pedido_controller.py, relatorio_controller.py, sistema_controller.py
    ├── routes/        __init__.py, produto_routes.py, usuario_routes.py,
    │                  pedido_routes.py, relatorio_routes.py, sistema_routes.py
    ├── middlewares/   __init__.py, error_handler.py, auth.py
    └── utils/         __init__.py, errors.py, validators.py, logger.py
```
Removidos: `controllers.py`, `database.py`, `models.py`. Código em `src/`: 1057 linhas em 34 arquivos `.py`.
