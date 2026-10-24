# Ambiente local (sem Docker, sem PostgreSQL)

Os 3 projetos legados usam SQLite (arquivo ou memoria); nao ha servicos externos.

## Pre-requisitos (verificados)

| Item | Versao encontrada |
|---|---|
| Windows | 11 Pro (PowerShell 5.1 + Git Bash) |
| Python | 3.12.10 (`py -3.12`; o launcher tambem lista 3.14, nao usar) |
| Node.js / npm | v22.20.0 |
| curl | `curl.exe` nativo |
| Claude Code | 2.1.310 (flags em `docs/evidence/claude-cli-flags.md`) |
| Git | repositorio na branch `main`, commit base `6d1ce62` |

## Projetos, numeracao e portas

Numeracao da SPEC 7.5 (usada em `scripts/` e `docs/evidence/project-N/`):

| N | Pasta | Stack | Comando de boot | Porta | Rotas (requisicoes no smoke) |
|---|---|---|---|---|---|
| 1 | `code-smells-project` | Flask 3.1.1 + sqlite3 (`loja.db`) | `python app.py` | 5000 | 19 (29) |
| 2 | `ecommerce-api-legacy` | Express 4 + sqlite3 em memoria | `npm start` | 3000 | 3 (6) |
| 3 | `task-manager-api` | Flask 3.0 + SQLAlchemy (`instance/tasks.db`) | `python seed.py` e depois `python app.py` | 5000 | 22 (35) |

Projetos 1 e 3 usam a mesma porta 5000: rode um de cada vez.

## Ativar e rodar cada ambiente

Os ambientes ja foram criados e estao ignorados pelo Git (`.venv/`, `node_modules/`).

```powershell
# Projeto 1
cd code-smells-project;  .\.venv\Scripts\Activate.ps1; python app.py
# Projeto 3 (popular o banco antes)
cd task-manager-api;     .\.venv\Scripts\Activate.ps1; python seed.py; python app.py
# Projeto 2
cd ecommerce-api-legacy; npm start
```

Recriar do zero: `py -3.12 -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt` (P1 e P3) e `npm install` (P2).
Encerrar: Ctrl+C. Se sobrar processo (Flask em debug cria um filho): `taskkill /PID <pid> /T /F`.

## Scripts (`scripts/`)

| Script | Uso |
|---|---|
| `smoke.ps1 -Project N [-Out arq] [-AdminToken x] [-KeepDb] [-BootTimeoutSec 30]` | Smoke generico. Apaga `*.db`, (P3) roda `seed.py`, sobe a app com o comando original em background, espera a porta (ate 30 s), chama todos os endpoints, escreve `METODO path -> status`, encerra a arvore de processos (`taskkill /T`), confere a porta livre e apaga `*.db`. Grava tambem `<Out sem extensao>-boot.log` (stdout/stderr). Sai com codigo 1 se a app nao subir. |
| `smoke-project-1.ps1`, `-2`, `-3` | Wrappers de `smoke.ps1` (repassam `-Out`, `-AdminToken` etc.). |
| `sync-skill.ps1 [-CheckOnly]` | Copia `code-smells-project\.claude\skills\refactor-arch\` para os outros 2 projetos e confere SHA256 arquivo a arquivo (copias recriadas do zero, sem orfaos). Falha com mensagem clara se a fonte nao existir (estado atual). |
| `reset-project.ps1 -Project N` | `git checkout -- <pasta>` (excluindo `.claude`) + `git clean -fd -e .claude -e .venv -e node_modules -- <pasta>`. Nao usa `-x`: `.venv`, `node_modules` e `*.db` ignorados nao sao tocados. |

Exemplos:

```powershell
# baseline antes (original)
.\scripts\smoke-project-1.ps1
# apos refatorar: sem token e com token (ADR-03)
.\scripts\smoke-project-1.ps1 -Out docs\evidence\project-1\after-notoken.txt
.\scripts\smoke-project-1.ps1 -AdminToken s3cret -Out docs\evidence\project-1\after-token.txt
fc docs\evidence\project-1\baseline-before.txt docs\evidence\project-1\after-token.txt
```

Com `-AdminToken`, a app recebe `ADMIN_TOKEN` no ambiente e as rotas admin (`/admin/query`, `/admin/reset-db`,
`/api/admin/financial-report`) enviam `X-Admin-Token`. No codigo original o token e ignorado (200 com ou sem ele).
As linhas de saida sao comparaveis por ordem (o mesmo metodo+path aparece mais de uma vez: caso valido e caso de erro).
O plano de requisicoes esta embutido em `smoke.ps1` (ids de recursos criados sao capturados da resposta).

## Evidencias geradas

`docs/evidence/project-N/baseline-before.txt` (+ `baseline-before-boot.log`) e `docs/evidence/claude-cli-flags.md`.

## Problemas encontrados e solucoes

1. `sqlite3` nativo no Node 22/Windows: instalou sem problemas (binario pre-compilado; 191 pacotes). Nenhuma acao necessaria. `npm install` reporta 14 vulnerabilidades (dependencias legadas); nao corrigidas de proposito (nao alterar projeto/lockfile).
2. Python: existem 3.12 e 3.14; os venvs usam `py -3.12` conforme a arquitetura.
3. `app.py` de P1 e P3 roda com `debug=True` (reloader): o processo pai gera um filho. O smoke encerra com `taskkill /PID <pid> /T /F` para matar a arvore inteira.
4. Em PS 5.1, stderr de comando nativo com `$ErrorActionPreference='Stop'` vira excecao (o `seed.py` emite `DeprecationWarning` de `utcnow()`). Solucao: seed e app rodam via `Start-Process` com redirecionamento de saida.
5. Logs UTF-8 lidos como ANSI no PS 5.1 geravam mojibake: leitura com `-Encoding UTF8`. Os `.txt` de resultado sao ASCII puro.
6. `curl` em PS 5.1 e alias de `Invoke-WebRequest`: os scripts usam sempre `curl.exe`, com corpos JSON em arquivo temporario (`--data-binary @arq`) para evitar problemas de aspas.
7. Numeracao: a SPEC numera ecommerce como projeto 2 e task-manager como 3 (a ordem do enunciado desta tarefa listava o inverso); foi adotada a da SPEC.
8. Estado de banco: P1 cria `loja.db` e P3 `instance/tasks.db`; os scripts apagam `*.db` antes e depois. `*.db` e `instance/` ja estao no `.gitignore` raiz. Pastas vazias `instance/` e `__pycache__/` (ignoradas) permanecem.
9. O `.gitignore` raiz ja cobria `.venv/`, `venv/`, `node_modules/`, `*.db`, `__pycache__/`, `*.pyc`, `.env` e `instance/`; nada foi alterado.
