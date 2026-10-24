# Relatório de testes (QA) — skill `refactor-arch`

- Data: 2026-10-24
- Commit validado: `38879fe` (HEAD, árvore limpa). Refatorações: `0912915` (P2), `56b46d0` (P1), `38879fe` (P3); skill em `a6415bb`.
- Ambiente: Windows 11, PowerShell 5.1 + Git Bash, Python 3.12.10 (venvs dos projetos), Node 22, `curl.exe`.
- Método: tudo reexecutado pelo QA (nenhum resultado dos outros agentes foi reaproveitado). Saídas intermediárias ficaram em `%TEMP%\qa\` (fora do repositório).
- Comparação com o código original feita contra `git show 6d1ce62:<arquivo>` e contra `git archive 6d1ce62` extraído em pasta temporária.

## Resumo

**Critérios CA-01..CA-18: 15 PASS / 1 FAIL / 2 BLOCKED.** BLOCKED = depende do `README.md` final, ainda não escrito pelo technical-writer (não é falha de código).
Checklist do enunciado: 3 projetos x 19 itens, todos `[x]` (P2 com ressalva de observabilidade, ver O-1).

FAIL: **CA-18** (severidade baixa), ver BUG-QA-01.

## 1. Matriz CA-01..CA-18

| ID | Resultado | Comando / método | Evidência |
|---|---|---|---|
| CA-01 Fase 1 detecta stack | PASS (ressalva O-1 para P2) | `iconv -f UTF-16 -t UTF-8 docs/evidence/project-{1,3}/stage1.log`; `git ls-tree` + `wc -l` em `6d1ce62`; `package-lock.json` | P1: `Language: Python`, `Framework: Flask 3.1.1`, `Source files: 4` (real: 4 `.py`, 780 LOC = `~780` do relatório). P3: `Flask 3.0.0`, `Source files: 15` (real: 15 `.py` incl. `__init__.py`, 1158 LOC = `~1158`), domínio "Gerenciamento de tarefas...". P2: `Express 4.22.1` (= lockfile), `Source files: 3` (real: 3 `.js`, 180 LOC), domínio LMS com checkout; o bloco consta apenas em `stage1-phase1-only.log` (O-1). |
| CA-02 >= 5 findings | PASS | `grep -c '^### \[' reports/audit-project-N.md`; `grep '^Total'` | P1: 33 blocos = `Total: 33 findings`; P2: 21 = 21; P3: 31 = 31. |
| CA-03 >= 1 CRITICAL/HIGH | PASS | `grep -o '^### \[[A-Z]*\]' ... \| sort \| uniq -c` | P1 11C/9H/7M/6L; P2 6C/6H/3M/6L; P3 5C/6H/13M/7L. Summary == blocos reais nos 3. |
| CA-04 App funciona após refatoração | PASS | `scripts/smoke-project-N.ps1` (seção 4) | P1, P2, P3: sem 5xx, sem 404 de rota, boot sem traceback; divergências apenas as aceitas (seção 8). |
| CA-05 Análise manual no README (Seção A) | BLOCKED | Leitura de `README.md` | `README.md` ainda é o enunciado original. Fonte pronta em `docs/manual-analysis.md`: P1 6C/3H/3M/2L (14), P2 5C/3H/3M/2L (13), P3 3C/3H/5M/3L (14); todos cumprem RF-01. Reverificar após a reescrita. |
| CA-06 P1 cobre análise manual | PASS | Cruzamento linha a linha `docs/manual-analysis.md` x `reports/audit-project-1.md` | 14/14 problemas manuais do P1 aparecem (mesmo arquivo + AP). Extra: P2 12/13 (o 2.7, callback do DELETE em `AppManager.js:131-137`, só parcial, coberto por AP-10 em `37-77`); P3 14/14. |
| CA-07 Estrutura da skill | PASS | `head SKILL.md`; `find ... -type f -not -name '*.md'` | Frontmatter `name: refactor-arch` + `description`; 8 arquivos, todos `.md`, sem BOM. |
| CA-08 5 áreas cobertas | PASS | `docs/ARCHITECTURE.md` (tabela de áreas, ~linhas 83-91) + `ls` | análise: `project-analysis.md`; catálogo: `anti-patterns-catalog.md` (+ `deprecated-apis.md`); template: `audit-report-template.md`; guidelines: `mvc-guidelines.md`; playbook: `refactoring-playbook.md` (+ `phase3-validation.md`). Todos existem. |
| CA-09 Catálogo | PASS | `grep -nE '^## AP-'`; `grep 'Severidade:'` | 20 anti-patterns: 6 CRITICAL, 5 HIGH, 5 MEDIUM, 4 LOW. AP-16 Deprecated API Usage com pares obsoleto -> moderno (`utcnow()` -> `datetime.now(timezone.utc)`, `Model.query.get` -> `db.session.get`, `new Buffer` -> `Buffer.from`, ...). |
| CA-10 Playbook | PASS | `awk` contando `**Antes` / `**Depois` por `## T-xx` | 16 transformações (T-01..T-16), todas com >= 1 bloco Antes e >= 1 Depois. |
| CA-11 Cópias idênticas | PASS | `scripts/sync-skill.ps1 -CheckOnly` (rc=0); `diff -r` x2 | "Skill identica nas 3 copias (8 arquivos)"; `diff -r` sem saída para P2 e P3. `git diff a6415bb HEAD -- '*/.claude/*'` vazio (skill intacta durante as refatorações). |
| CA-12 Pausa obrigatória | PASS | `wc -c docs/evidence/project-N/stage1-git-status.txt`; fim de `stage1.log` | Os 3 `stage1-git-status.txt` têm 0 bytes. P1/P3 (UTF-16LE): `stage1.log` termina em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. P2: idem, seguido só do rodapé `<!-- result: subtype=success ... -->` do wrapper. `SKILL.md:85,90` contém a pergunta literal e a regra de parar sem ferramentas. |
| CA-13 Template respeitado | PASS | Script Python (`%TEMP%\qa\chk.py`) sobre os 3 relatórios | Títulos == nomes do catálogo; campos na ordem File/Other occurrences/Description/Impact/Recommendation; ordem CRITICAL->LOW e por AP-id sem violações; 33/21/31 linhas `File: caminho:linha[-fim]` sem exceção; UTF-8 sem BOM, sem CRLF; cabeçalho `ARCHITECTURE AUDIT REPORT` idêntico ao template. |
| CA-14 MVC | PASS (ressalva O-4) | `git ls-files`, greps (seção 5) | Config, models, routes, controllers, error handler e entry point nos 3. Sem `SECRET_KEY = '...'` nem senha literal em código de produção (exceto default de P2, O-4). |
| CA-15 Relatórios | PASS | `git ls-files reports` | Exatamente `audit-project-1.md`, `-2.md`, `-3.md`. |
| CA-16 Commits separados | PASS | `git show --name-only` dos 3 commits | `0912915` toca só `ecommerce-api-legacy/` + `docs/evidence/project-2/` + `reports/audit-project-2.md`; `56b46d0` só P1 + evidências P1 + report 1; `38879fe` só P3 + evidências P3 + report 3. Nenhum cruza projetos. |
| CA-17 README (Seções A-D) | BLOCKED | Leitura de `README.md` | README ainda é o enunciado. Reverificar após o technical-writer. |
| CA-18 Enunciado preservado | **FAIL** | `diff <(git show 6d1ce62:README.md) docs/CHALLENGE.md` | 2 diferenças: linha 428 "já possui alguma **organização**" (original) vs "alguma **separação de camadas**" (CHALLENGE.md), e newline final. Ver BUG-QA-01. |

## 2. Skill estática e restrições

| Verificação | Resultado | Evidência |
|---|---|---|
| Frontmatter `name: refactor-arch` | PASS | `SKILL.md:2` |
| Pergunta literal da Fase 2 + instrução de parar | PASS | `SKILL.md:85` (template) e `SKILL.md:90-91` ("encerre o turno: nenhuma chamada de ferramenta...") |
| Resposta != afirmativa cancela sem escrever | PASS | `SKILL.md` "Qualquer outra resposta ... `Refactoring cancelled. No files were modified.`" |
| Agnosticismo (nomes dos 3 projetos) | PASS | `grep -rniE "code-smells\|ecommerce\|task-manager\|loja\|financial\|AppManager\|produtos\|pedidos\|c_id\|seed.py\|/admin/query"` na skill: 0 ocorrências. Únicos achados: "checkout" como exemplo genérico em `mvc-guidelines.md:19` e "Flask 3.1.1" como exemplo de formato em `project-analysis.md:73` (ilustrativos, aceitáveis). |
| Nome do diretório/arquivo imutáveis, só `.md` | PASS | `.claude/skills/refactor-arch/SKILL.md` nas 3 pastas; 24 `.md`, nenhum outro tipo |
| Dependências não alteradas (ADR-08) | PASS | `git diff 6d1ce62 HEAD -- '*requirements.txt' '*package.json' '*package-lock.json'` vazio |
| Nada escrito nos projetos antes do "y" | PASS | `stage1-git-status.txt` vazio x3. `stage2.log` inicia a Fase 3 (P2: "Confirmação recebida. Iniciando a Fase 3"; P1/P3: bloco `PHASE 3` final). O literal `y` não consta no log; o comando `claude -p --continue "y"` está em `docs/evidence/project-N/checklist.md`. |
| Deprecated API | PASS | P3 tem 2 findings `[MEDIUM] Deprecated API Usage` (`models/category.py:11` `datetime.utcnow`; `routes/report_routes.py:105` `Query.get`). `grep` no ORIGINAL de P1 e P2 por `utcnow\|query.get\|new Buffer\|url.parse\|req.param\|body-parser`: 0 ocorrências, logo a ausência é correta ("se aplicável"). |

## 3. Amostragem de `arquivo:linha` contra o código ORIGINAL (`6d1ce62`)

Todas as 21 amostras conferem (>= 6 por projeto).

| Projeto | Finding do relatório | Linha no original |
|---|---|---|
| P1 | Hardcoded Credentials `app.py:7` | `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` |
| P1 | Insecure Runtime Config `app.py:8` | `app.config["DEBUG"] = True` |
| P1 | Sensitive Data Exposure `controllers.py:289` | `"secret_key": "minha-chave-super-secreta-123"` |
| P1 | SQL Injection `models.py:109-111` | `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` |
| P1 | Insecure Password Storage `database.py:75-83` | seeds `("Admin", "admin@loja.com", "admin123", "admin")` |
| P1 | Sensitive Data Exposure `models.py:83` | `"senha": row["senha"]` |
| P1 | Magic Numbers `models.py:257-262` | `if faturamento > 10000: desconto = faturamento * 0.1` |
| P1 | Print Logging `controllers.py:8` | `print("Listando " + ...)` |
| P2 | Hardcoded Credentials `src/utils.js:3-4` | `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_..."` |
| P2 | Insecure Password Storage `src/utils.js:17-23` | `function badCrypto(pwd)` com base64 |
| P2 | Sensitive Data Exposure `src/AppManager.js:45` | `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` |
| P2 | Insecure Password Storage `src/AppManager.js:68` | `let hash = badCrypto(p \|\| "123456")` |
| P2 | Unprotected Admin `src/AppManager.js:80` | `app.get('/api/admin/financial-report', ...` |
| P2 | Dead Code `src/AppManager.js:2` | `const { config, logAndCache, badCrypto, totalRevenue } = require('./utils')` |
| P3 | Hardcoded `app.py:13` | `app.config['SECRET_KEY'] = 'super-secret-key-123'` |
| P3 | Hardcoded `services/notification_service.py:10` | `self.email_password = 'senha123'` |
| P3 | Sensitive Data `models/user.py:21` | `'password': self.password,` |
| P3 | Password Storage `models/user.py:29` | `hashlib.md5(pwd.encode()).hexdigest()` |
| P3 | Deprecated `models/category.py:11` | `default=datetime.utcnow` |
| P3 | Deprecated `routes/report_routes.py:105` | `User.query.get(user_id)` |
| P3 | Runtime config `app.py:34` | `app.run(debug=True, host='0.0.0.0', port=5000)` |
| P3 | N+1 `routes/user_routes.py:22` | `'task_count': len(u.tasks)` |
| P3 | Print `routes/task_routes.py:149` | `print(f"Task criada: ...")` |

## 4. Fase 3 — execução real (um projeto por vez; portas 3000/5000 livres antes e depois)

Comando de boot (via `scripts/smoke.ps1`, que usa o comando ORIGINAL): P1 `python app.py` (venv); P2 `npm start` (-> `node src/app.js`); P3 `python seed.py` + `python app.py` (venv). Entradas `app.py` / `src/app.js` presentes e finas.

| Projeto | Comando | Resultado vs `baseline-before.txt` | Boot log |
|---|---|---|---|
| P2 sem token | `scripts\smoke-project-2.ps1 -Out ...` | 5 de 6 iguais; `GET /api/admin/financial-report` 200 -> **403** | 0 ocorrências de error/traceback/exception; `INFO LMS rodando na porta 3000...` |
| P2 com token | `... -AdminToken s3cret` | **idêntico** (só o cabeçalho `admin_token=set`) | idem |
| P1 sem token | `scripts\smoke-project-1.ps1 -Out ...` | 26 de 29 iguais; `POST /admin/query` 200 -> 403, `POST /admin/query` 400 -> 403, `POST /admin/reset-db` 200 -> 403 | 0 traceback/error; `Running on http://127.0.0.1:5000` |
| P1 com token | `... -AdminToken s3cret` | **idêntico** (só cabeçalho) | idem |
| P3 | `scripts\smoke-project-3.ps1 -Out ...` | **idêntico** (35 requisições) | 0 traceback/error/exception |
| P3 `seed.py` | `.venv\Scripts\python.exe -W error::DeprecationWarning seed.py` | exit 0: "Seed concluído com sucesso! 3 usuários, 4 categorias, 10 tasks"; senhas gravadas como `scrypt:...`; 0 DeprecationWarning (mesmo com `-W error`) | n/a |

Limpeza: portas 3000/5000 livres (`Get-NetTCPConnection`), sem `*.db`, sem processos de projeto (restam apenas 2 `node.exe` do MCP chrome-devtools, alheios).

### Verificação extra de contrato (corpos), original x refatorado, mesmas requisições
Executada pelo QA com `%TEMP%\qa\shape.py` (chaves e tipos do JSON) contra o original extraído de `6d1ce62` e o código atual.
- P1: diferenças só em `GET /health` (removidos `secret_key`, `db_path`, `debug`, `ambiente`) e `GET /usuarios`, `GET /usuarios/1` (removido `senha`). ADR-11(a), aceitas.
- P3: diferenças só no campo `password` removido de `GET /users/1`, `POST /login` e `POST /users`. ADR-11(a), aceitas. Login com senha legada (`joao@email.com` / `1234`) = 200; senha errada = 401.
- P2: formas idênticas nas 4 chamadas (`checkout` 200/400, `financial-report` 200 com token, `DELETE`).

## 5. Estrutura MVC e anti-patterns residuais (código versionado, excluindo `.claude/`)

| Camada | P1 `code-smells-project` | P2 `ecommerce-api-legacy` | P3 `task-manager-api` |
|---|---|---|---|
| Config (sem segredos) | `src/config/settings.py` (SECRET_KEY de `env` ou `secrets.token_hex`), `.env.example` | `src/config/index.js` (único `process.env`), `.env.example` | `config/settings.py`, `.env.example` |
| Models | `src/models/*` (+ `services/`) | `src/models/*` (+ `services/`) | `models/*` (+ `services/`) |
| Routes | `src/routes/*` (53 linhas) | `src/routes/*` (30) | `routes/*` (66) |
| Controllers | `src/controllers/*` (178) | `src/controllers/*` (32) | `controllers/*` (140) |
| Error handler | `src/middlewares/error_handler.py` (`AppError` + `Exception`) | `src/middlewares/errorHandler.js` | `middlewares/error_handler.py` |
| Entry point | `app.py` (fino) -> `src/app.py` `create_app` | `src/app.js` (`createApp`, composition root + listen) | `app.py` `create_app` |
| SQL/ORM em routes/controllers | 0 ocorrências | 0 | 0 |

Greps no código refatorado:
- Segredos literais (`SECRET_KEY/password/senha/token = '...'`): 0 em P1 e P3; P2 apenas `DEFAULT_PASSWORD = '123456'` (O-4).
- `print(`: 0 em P1 e P2 (`console.*` só em `utils/logger.js`); P3 apenas `seed.py:94-97` (saída de script CLI).
- `except:` nu: 0. `debug=True` / `DEBUG=True`: 0 (DEBUG via env, default `false`). `str(e)` vazado: 0.
- `utcnow(`: P3 usa o helper local `utils/time.py: utcnow()` (= `datetime.now(timezone.utc).replace(tzinfo=None)`); nenhum `datetime.utcnow` nem `.query.get(`.
- md5: P3 `models/user.py:45` só para verificar hash legado + rehash (ADR-12), não para gravar.
- SQL por concatenação: `code-smells-project/src/models/admin_model.py:13` (`"DELETE FROM " + tabela`, nomes de allow-list fixa) e `pedido_model.py:60` (`.format(where="")` com constante). Residuais benignos. `/admin/query` executa SQL arbitrário por design, protegido por `ADMIN_TOKEN` (risco residual documentado no próprio código).
- Boot de P1/P3 mostra `Debug mode: off` (antes `debug=True`): endurecimento, sem efeito no contrato.

## 6. Git

| Verificação | Resultado |
|---|---|
| 1 commit por projeto refatorado | PASS: `0912915` (P2), `56b46d0` (P1), `38879fe` (P3) |
| Sem `.db`, `.venv`, `node_modules`, `instance/`, `__pycache__`, `.pyc`, `.env` versionados | PASS: `git ls-files \| grep -E ...` vazio |
| Árvore limpa no fim da validação | PASS: `git status --short` vazio (antes de gravar este relatório) |

## 7. Checklist do enunciado por projeto

### Projeto 1 — code-smells-project
Fase 1
- [x] Linguagem detectada corretamente (`Language: Python`)
- [x] Framework detectado corretamente (`Flask 3.1.1`)
- [x] Domínio da aplicação descrito corretamente (e-commerce: produtos, usuários, pedidos)
- [x] Número de arquivos analisados condiz com a realidade (4 = 4 `.py`; ~780 LOC conferido)

Fase 2
- [x] Relatório segue o template (CA-13)
- [x] Cada finding tem arquivo e linhas exatos (33/33 com `File:`; 8 amostras conferidas)
- [x] Findings ordenados CRITICAL -> LOW (11/9/7/6)
- [x] Mínimo de 5 findings (33)
- [x] Detecção de APIs deprecated incluída (se aplicável): não aplicável, nenhuma ocorrência no original
- [x] Skill pausa e pede confirmação (`stage1-git-status.txt` vazio; pergunta literal no fim de `stage1.log`)

Fase 3
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados
- [x] Views/Routes separadas
- [x] Controllers concentram o fluxo
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (29/29 sem 5xx/404; com token idêntico à baseline; desvios aceitos na seção 8)

### Projeto 2 — ecommerce-api-legacy
Fase 1
- [x] Linguagem detectada corretamente (`JavaScript (Node.js)`)
- [x] Framework detectado corretamente (`Express 4.22.1`, = lockfile). Ressalva O-1
- [x] Domínio descrito corretamente (LMS com checkout/matrícula)
- [x] Número de arquivos condiz (3 = 3 `.js`; ~180 LOC conferido)

Fase 2
- [x] Template (CA-13)
- [x] Arquivo e linhas exatos (21/21; 6 amostras conferidas)
- [x] Ordenado (6/6/3/6)
- [x] Mínimo de 5 findings (21)
- [x] Deprecated API: não aplicável (0 no original)
- [x] Pausa e confirmação (`stage1-git-status.txt` vazio)

Fase 3
- [x] Estrutura MVC
- [x] Config extraída (`src/config/index.js`; ressalva O-4 sobre `DEFAULT_PASSWORD`)
- [x] Models
- [x] Routes
- [x] Controllers
- [x] Error handling centralizado
- [x] Entry point claro (`src/app.js`)
- [x] Aplicação inicia sem erros (`npm start`)
- [x] Endpoints originais respondem (6/6; com token idêntico à baseline)

### Projeto 3 — task-manager-api
Fase 1
- [x] Linguagem detectada corretamente (`Python`)
- [x] Framework detectado corretamente (`Flask 3.0.0`)
- [x] Domínio descrito corretamente (gerenciamento de tarefas)
- [x] Número de arquivos condiz (15 = 15 `.py`; ~1158 LOC conferido)

Fase 2
- [x] Template (CA-13)
- [x] Arquivo e linhas exatos (31/31; 9 amostras conferidas)
- [x] Ordenado (5/6/13/7)
- [x] Mínimo de 5 findings (31)
- [x] Deprecated API incluída (2 findings: `utcnow`, `Query.get`)
- [x] Pausa e confirmação

Fase 3
- [x] Estrutura MVC (evolução incremental, ADR-09)
- [x] Config extraída
- [x] Models
- [x] Routes
- [x] Controllers
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros (`seed.py` + `python app.py`)
- [x] Endpoints originais respondem (35/35 idêntico à baseline)

## 8. Regressões e desvios

**Regressões: nenhuma encontrada.**

| # | Divergência | Classificação |
|---|---|---|
| D-1 | P1 `POST /admin/query` (200 e 400) e `POST /admin/reset-db` (200): 403 sem `X-Admin-Token`; com token = baseline | Aceita (ADR-03) |
| D-2 | P2 `GET /api/admin/financial-report` 200 -> 403 sem token; com token = baseline | Aceita (ADR-03) |
| D-3 | P1 `GET /health` sem `secret_key/db_path/debug/ambiente`; `GET /usuarios[/id]` sem `senha` | Aceita (ADR-11a) |
| D-4 | P3 `password` removido de `GET /users/<id>`, `POST /login`, `POST /users` | Aceita (ADR-11a) |
| D-5 | P1 `PUT /produtos/1` com `nome` vazio/curto: 200 -> 400 "Nome muito curto"; com `categoria` inválida: 200 -> 400 | Aceita (decisão do orquestrador). **Não é detectada pelo smoke** (as requisições do smoke são válidas); verificada manualmente com `%TEMP%\qa\edge1.py` |
| D-6 | P1 `PUT /produtos/1` com `preco:"abc"`: 500 -> 400 "Preço inválido"; corpo vazio: 500 -> 400 "Dados inválidos" | Aceita (ADR-11d, correção de 5xx) |
| D-7 | P1 erros 500 não vazam mais `str(e)` | Aceita (ADR-11c) |
| D-8 | JSON do P1 agora compacto (o original saía indentado pelo modo debug) | Equivalente semanticamente; sem ação |
| D-9 | P1/P3 sobem com `debug` desligado e `HOST=127.0.0.1` por padrão (antes `debug=True` / `0.0.0.0`) | Aceita (endurecimento, `.env.example`); documentar no README Seção D |

Preservado do original (não é regressão): `POST /pedidos` com `usuario_id` inexistente ainda devolve 201 com total 0.0 (P1). A mensagem do `DELETE /api/users/:id` do P2 continua dizendo "matrículas e pagamentos ficaram sujos" embora o código agora remova os dependentes (mensagem obsoleta, já sinalizada no `stage2.log` do P2).

## 9. Bugs

### BUG-QA-01 — `docs/CHALLENGE.md` não é idêntico ao README original (CA-18). Severidade BAIXA
- Responsável: solution-architect / technical-writer (quem mantém `docs/CHALLENGE.md`)
- Reproduzir: na raiz do repositório, `diff <(git show 6d1ce62:README.md) docs/CHALLENGE.md`
- Esperado: sem diferenças (SPEC §8 chama o arquivo de "enunciado original (imutável)")
- Obtido: linha 428 `...já possui alguma organização...` (original) virou `...já possui alguma separação de camadas...`; o original não termina com newline e o CHALLENGE.md termina.
- Hipótese: edição manual de redação ao copiar. Correção: `git show 6d1ce62:README.md > docs/CHALLENGE.md` antes de reescrever o README.

## 10. Problemas encontrados na skill ou no processo (para iteração; não são FAIL)

- **O-1 (PHASE 1 em modo `-p`)**: `stage1.log` do P1 (linha 2) e do P3 (linha 4) contêm o bloco `PHASE 1: PROJECT ANALYSIS`. O `stage1.log` do **P2 não contém** o bloco (só o relatório da Fase 2); o bloco existe em `stage1-phase1-only.log`, uma execução de calibração separada. O P3 já teve uma tentativa descartada pelo mesmo motivo (`stage1-attempt1.log`). A Fase 1 é impressa antes de chamadas de ferramenta, então o texto some do resultado final do `-p`. Sugestão: exigir na skill que o bloco PHASE 1 seja repetido imediatamente antes do `ARCHITECTURE AUDIT REPORT` na mesma mensagem final, e/ou capturar com `--output-format stream-json`. Para o P2, anexar o PHASE 1 da execução oficial (CA-01 pede o bloco no log da execução).
- **O-2 (encoding das evidências)**: `stage1.log` e `stage2.log` de P1 e P3 estão em UTF-16LE com CRLF (PowerShell `Tee-Object`), enquanto P2 está em UTF-8; `grep` os trata como binários. Sugestão: converter para UTF-8 antes de citá-los no README Seção C.
- **O-3 (Git Bash expande `/refactor-arch`)**: o `stage1.log` do P2 abre com "o caminho `C:/Program Files/Git/refactor-arch` é o Git Bash expandindo `/refactor-arch`". Invocar a skill pelo PowerShell ou com `MSYS_NO_PATHCONV=1`; documentar na Seção D.
- **O-4 (segredo-padrão residual)**: P2 `src/models/constants.js:12` `DEFAULT_PASSWORD = '123456'` (usada em `src/utils/validators.js:22` quando o checkout não envia `pwd`) preserva o comportamento original, mas é uma senha literal no código (gravada com hash). Idem seeds demonstrativos com senha em claro antes do hash (`code-smells-project/src/models/database.py:66-70`, `task-manager-api/seed.py:20-34`). Aceito como dado de seed/comportamento preservado; registrar como risco residual no README ou mover o default para configuração.
- **O-5 (cobertura do smoke)**: o smoke não exercita os caminhos de validação alterados (D-5/D-6) nem confere corpos/campos sensíveis. Sugestão: acrescentar casos inválidos ao plano de `scripts/smoke.ps1` (ex.: `PUT /produtos/1` com nome vazio) para a divergência aparecer na comparação automática.
- **O-6 (inconsistência interna da skill)**: o template resumido em `SKILL.md` (linhas ~60-85) omite a linha opcional `Other occurrences:` presente em `audit-report-template.md`. Sem impacto nos relatórios gerados; vale alinhar.
- **O-7 (README)**: `README.md` e CA-05/CA-17 pendentes. Incluir o desvio D-5 e a mudança de `debug`/host padrão (D-9), exigidos por RNF-02.
- **O-8**: os `docs/evidence/project-N/checklist.md` do executor coincidem com as conclusões do QA (nenhuma discrepância de PASS/FAIL), com a única ressalva O-1 para P2.
