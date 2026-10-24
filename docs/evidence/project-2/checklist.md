# Checklist de Validação — Projeto 2 (ecommerce-api-legacy)

Execução da skill `refactor-arch` (versão do commit `a6415bb`), Claude Code 2.1.310, Windows 11, Node v22.20.0.

## Execuções e evidências

| Etapa | Comando (cwd = `ecommerce-api-legacy/`) | Evidência |
|---|---|---|
| Calibração | `claude -p "/refactor-arch" --permission-mode plan` | `stage1-calib.log`, `stage1-calib-git-status.txt` (vazio) |
| Encerramento da calibração | `claude -p --continue "n"` | `stage1-calib-answer-n.log` (`Refactoring cancelled. No files were modified.`) |
| Etapa 1 oficial (Fases 1–2) | `claude -p "/refactor-arch" --permission-mode plan --output-format stream-json --verbose` (sessão `69b5ef03-4b61-4af6-bcca-e48fd5d5ea4a`) | `stage1.log` (textos do assistente renderizados do stream-json), `stage1-git-status.txt` (vazio, 0 bytes) |
| Bloco PHASE 1 (desvio, ver abaixo) | `claude -p "/refactor-arch Execute somente a Fase 1 ..." --permission-mode plan --no-session-persistence` | `stage1-phase1-only.log` |
| Relatório | `scripts/extract-report.ps1 -Log docs/evidence/project-2/stage1.log -Out reports/audit-project-2.md` | `reports/audit-project-2.md` |
| Etapa 2 (Fase 3) | `claude -p --continue "y" --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep"` (mesma sessão `69b5ef03`) | `stage2.log` |
| Smoke independente sem token | `scripts/smoke-project-2.ps1 -Out docs/evidence/project-2/baseline-after.txt` | `baseline-after.txt`, `baseline-after-boot.log` |
| Smoke independente com token | `scripts/smoke-project-2.ps1 -AdminToken s3cret -Out docs/evidence/project-2/baseline-after-token.txt` | `baseline-after-token.txt`, `baseline-after-token-boot.log` |
| Corpo/content-type original x refatorado | script Node ad hoc (scratchpad), mesmo plano nos dois códigos | `body-compare.txt` |

**Desvio registrado:** nas duas execuções de `/refactor-arch` em `-p` (calibração e oficial), o modelo fez o inventário da Fase 1 mas **não imprimiu o bloco PHASE 1**: os textos do assistente no transcript são só uma introdução, uma frase de transição e o relatório. O bloco foi obtido numa execução separada, somente leitura (`--permission-mode plan`), que não persistiu sessão (`--no-session-persistence`), para não afetar o `--continue` da Etapa 2. A skill não foi editada.

## Fase 1 — Análise
- [x] Linguagem detectada corretamente: `Language: JavaScript (Node.js)` (`stage1-phase1-only.log:8`); o relatório também traz `Stack: JavaScript (Node.js) + Express` (`reports/audit-project-2.md:5`)
- [x] Framework detectado corretamente: `Framework: Express 4.22.1` (`stage1-phase1-only.log:9`), igual ao `package-lock.json` (`node_modules/express` → `4.22.1`; manifesto `^4.18.2`)
- [x] Domínio da aplicação descrito corretamente: `LMS com fluxo de checkout e matrícula em cursos (users, courses, enrollments, payments, audit_logs)` (`stage1-phase1-only.log:11`); tabelas `users, courses, enrollments, payments, audit_logs (SQLite, em memória)` (`:14`), 3 rotas (`:15`)
- [x] Número de arquivos analisados condiz com a realidade: `Source files: 3 files analyzed` (`stage1-phase1-only.log:13`) e `Files: 3 analyzed | ~180 lines of code` (`reports/audit-project-2.md:6`); real: `src/app.js`, `src/AppManager.js`, `src/utils.js` = 14 + 141 + 25 = 180 linhas
- Ressalva: o bloco PHASE 1 não saiu na Etapa 1 oficial (ver desvio acima)

## Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência: cabeçalho `ARCHITECTURE AUDIT REPORT`, `Project/Stack/Files`, `## Summary`, `## Findings`, `Total`, pergunta final (`reports/audit-project-2.md:1-156`); `extract-report.ps1` confirmou `Total declarado: 21 | blocos '### [': 21`
- [x] Cada finding tem arquivo e linhas exatos: 21 linhas `File: caminho:linha[-fim]` para 21 findings; amostras conferidas no código original (ex.: `src/AppManager.js:45` = `console.log` com cartão; `src/utils.js:17-23` = `badCrypto`; `src/AppManager.js:80` = rota financial-report)
- [x] Findings ordenados por severidade (CRITICAL → LOW): 6 CRITICAL, 6 HIGH, 3 MEDIUM, 6 LOW, em blocos contíguos nessa ordem
- [x] Mínimo de 5 findings identificados: `Total: 21 findings` (`stage1.log:159`); CRITICAL + HIGH = 12
- [x] Detecção de APIs deprecated incluída (se aplicável): não se aplica a este projeto. A skill varreu e declarou explicitamente "nenhuma API obsoleta da tabela Node/Express encontrada; `sqlite3.verbose()` não consta como deprecated" (`stage1.log:5`), o que bate com `docs/manual-analysis.md` (projeto 2: nenhuma API deprecated)
- [x] Skill pausa e pede confirmação antes da Fase 3: última linha `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` (`stage1.log:162`); `stage1-git-status.txt` vazio; a resposta "n" na calibração cancelou sem alterações (`stage1-calib-answer-n.log`)

## Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC: `src/config`, `src/models`, `src/services`, `src/controllers`, `src/routes`, `src/middlewares`, `src/utils` (árvore abaixo; `stage2.log:9-44`)
- [x] Configuração extraída para módulo de config (sem hardcoded): `src/config/index.js` é o único leitor de `process.env` (linha 7); `.env.example` documenta PORT, HOST, DB_PATH, PAYMENT_GATEWAY_KEY, ADMIN_TOKEN, LOG_LEVEL; busca por `pk_live|senha_super|admin_master|smtpUser|badCrypto|globalCache|console.log` em `src/` não retorna nada
- [x] Models criados para abstrair dados: `src/models/{userModel,courseModel,enrollmentModel,paymentModel,auditLogModel,reportModel}.js` e `database.js` (wrapper Promise + transação)
- [x] Views/Routes separadas para visualização ou roteamento: `src/routes/{checkoutRoutes,adminRoutes,userRoutes}.js` (só mapeamento método+path → controller)
- [x] Controllers concentram o fluxo da aplicação: `src/controllers/{checkoutController,adminController,userController}.js` (entrada → validação → service/model → resposta), com regras em `src/services/`
- [x] Error handling centralizado: `src/middlewares/errorHandler.js` registrado por último (`src/app.js:55`), `asyncHandler.js` e erros de domínio em `src/utils/errors.js`
- [x] Entry point claro: `src/app.js` (`createApp()` composition root na linha 29; `listen` só em `require.main === module`, linha 60); `npm start` → `node src/app.js` inalterado (`package.json` sem diff)
- [x] Aplicação inicia sem erros: `baseline-after-boot.log` e `baseline-after-token-boot.log` com stderr vazio e `INFO LMS rodando na porta 3000...`
- [x] Endpoints originais respondem corretamente: 6/6 requisições com o status da baseline, exceto a divergência justificada do admin sem token (tabela abaixo); com token, 6/6 iguais; corpos e content-type idênticos (`body-compare.txt`)

## Comparação before/after (smoke independente, `scripts/smoke-project-2.ps1`)

| # | Requisição | before | after (sem token) | after (com token) | Situação |
|---|---|---|---|---|---|
| 1 | POST /api/checkout (novo usuário, cartão 4…) | 200 | 200 | 200 | igual |
| 2 | POST /api/checkout (cartão 5…, recusado) | 400 | 400 | 400 | igual |
| 3 | POST /api/checkout `{}` | 400 | 400 | 400 | igual |
| 4 | POST /api/checkout (c_id 999) | 404 | 404 | 404 | igual |
| 5 | GET /api/admin/financial-report | 200 | **403** | 200 | justificada (ADR-03 / ADR-11 b: guard `ADMIN_TOKEN` + `X-Admin-Token`) |
| 6 | DELETE /api/users/1 | 200 | 200 | 200 | igual |

Diferenças observadas fora do status, nenhuma de contrato:
- Depois de `DELETE /api/users/1`, o relatório financeiro deixa de listar as matrículas e pagamentos órfãos do usuário removido (`body-compare.txt`, linha 8 do diff), porque a exclusão agora remove os dependentes na mesma transação (finding HIGH "Missing Transaction / Callback Pyramid", T-09). Chaves, status e content-type continuam iguais. O texto de resposta do DELETE foi mantido de propósito, por ser contrato (a skill o listou como residual).
- Pagamento recusado não cria mais o usuário antes da recusa: o gateway decide antes da transação. O status (400) e o texto ("Pagamento recusado") são iguais.
- `card` numérico: o original derrubava o processo com TypeError; agora responde 400 "Bad Request" (ADR-11 d). Esse caso não está no smoke externo; foi medido pela autovalidação da skill (`stage2.log`, Endpoint Check).
- A mensagem de log de boot passou de `Frankenstein LMS rodando na porta 3000...` para `<timestamp> INFO LMS rodando na porta 3000...` (é log, não contrato).

Limpeza: nenhum `*.db` no projeto, porta 3000 livre e nenhum processo `node src/app.js` remanescente após os testes.

## Árvore de diretórios

Antes (HEAD `a6415bb`, sem `.claude/` e `node_modules/`):

```
ecommerce-api-legacy/
├── README.md
├── api.http
├── package.json
├── package-lock.json
└── src/
    ├── app.js          (14 linhas: express + AppManager + listen)
    ├── AppManager.js   (141 linhas: God Class — banco, schema, seed, rotas e regras)
    └── utils.js        (25 linhas: config com segredos, cache global, badCrypto)
```

Depois (Fase 3):

```
ecommerce-api-legacy/
├── .env.example
├── README.md
├── api.http
├── package.json            (inalterado: "start": "node src/app.js")
├── package-lock.json       (inalterado)
└── src/
    ├── app.js              (entry point + composition root createApp())
    ├── config/
    │   └── index.js
    ├── controllers/
    │   ├── adminController.js
    │   ├── checkoutController.js
    │   └── userController.js
    ├── middlewares/
    │   ├── adminGuard.js
    │   ├── asyncHandler.js
    │   └── errorHandler.js
    ├── models/
    │   ├── auditLogModel.js
    │   ├── constants.js
    │   ├── courseModel.js
    │   ├── database.js
    │   ├── enrollmentModel.js
    │   ├── passwordHasher.js
    │   ├── paymentModel.js
    │   ├── reportModel.js
    │   └── userModel.js
    ├── routes/
    │   ├── adminRoutes.js
    │   ├── checkoutRoutes.js
    │   └── userRoutes.js
    ├── services/
    │   ├── checkoutService.js
    │   ├── paymentGateway.js
    │   └── userService.js
    └── utils/
        ├── errors.js
        ├── logger.js
        └── validators.js
```

26 arquivos `.js` / 560 linhas (antes: 3 arquivos / 180 linhas). `src/AppManager.js` e `src/utils.js` foram removidos; a skill usou `git rm`, então as duas remoções já estão staged.
