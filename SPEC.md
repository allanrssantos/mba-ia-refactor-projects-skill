# SPEC — Skill `refactor-arch`: Refatoração Arquitetural Automatizada

> Fonte única da verdade para a esteira (solution-architect, devops-engineer, python-developer, qa-engineer, technical-writer).
> Enunciado original preservado em `docs/CHALLENGE.md`. Em caso de conflito, o enunciado prevalece sobre esta SPEC, e esta SPEC prevalece sobre qualquer outro documento derivado.
> Histórias e critérios Gherkin: `docs/user-stories.md`.

---

## 1. Visão geral

Entregar uma **Custom Skill do Claude Code** chamada `refactor-arch` que, invocada dentro de um projeto backend legado, executa três fases sequenciais: (1) **análise** da stack e da arquitetura, (2) **auditoria** contra um catálogo de anti-patterns com relatório classificado por severidade e **pausa obrigatória para confirmação humana**, e (3) **refatoração** para o padrão MVC seguida de **validação** (boot + endpoints). A skill deve ser agnóstica de tecnologia e é provada em 3 projetos fornecidos (2 Python/Flask, 1 Node.js/Express). Público: alunos/avaliadores do MBA IA (Full Cycle) e desenvolvedores que herdam código legado.

## 2. Objetivos e não-objetivos

### Objetivos (DEVE ser entregue)
- O-01: Análise manual dos 3 projetos (≥ 5 problemas cada, com distribuição mínima de severidade), documentada no `README.md` (Seção A).
- O-02: Skill `refactor-arch` em `code-smells-project/.claude/skills/refactor-arch/` com `SKILL.md` + arquivos de referência Markdown cobrindo as 5 áreas de conhecimento obrigatórias.
- O-03: Cópias **idênticas** da skill em `ecommerce-api-legacy/.claude/skills/refactor-arch/` e `task-manager-api/.claude/skills/refactor-arch/`.
- O-04: Execução da skill nos 3 projetos, com o código refatorado (resultado da Fase 3) commitado — um commit (ou conjunto de commits) separado por projeto.
- O-05: Relatórios de auditoria (saída da Fase 2) em `reports/audit-project-1.md`, `reports/audit-project-2.md`, `reports/audit-project-3.md`.
- O-06: `README.md` final reescrito com as seções A (Análise Manual), B (Construção da Skill), C (Resultados), D (Como Executar).
- O-07: Enunciado original preservado em `docs/CHALLENGE.md` (já feito por esta etapa).

### Não-objetivos (FORA de escopo)
- NO-01: Suporte/teste em Gemini CLI ou OpenAI Codex (ferramenta escolhida: Claude Code).
- NO-02: Adicionar funcionalidades de negócio novas aos 3 projetos (novos endpoints, novas regras).
- NO-03: Trocar banco de dados (SQLite permanece), framework (Flask/Express permanecem) ou linguagem.
- NO-04: Containerização (Docker/docker-compose), CI/CD, deploy ou publicação.
- NO-05: Frontend/UI.
- NO-06: Suíte de testes automatizados completa como entregável obrigatório (testes/smoke scripts são permitidos como meio de validação, não são exigidos pelo enunciado).
- NO-07: Garantir "zero findings" após a refatoração — o exemplo do enunciado mostra "Zero anti-patterns remaining", mas o critério de aceite obrigatório é a aplicação funcionar; findings residuais devem ser reportados honestamente.
- NO-08: Encontrar todos os problemas dos projetos (o enunciado pede foco nos de maior impacto).

## 3. Personas / Usuários

| Persona | Contexto | Nível técnico |
|---|---|---|
| **Desenvolvedor(a) mantenedor(a)** (operador da skill) | Herdou um projeto legado; roda `claude "/refactor-arch"` na raiz do projeto, lê o relatório e decide se confirma a Fase 3. | Intermediário/avançado; conhece Git e terminal. |
| **Avaliador(a) do MBA** | Clona o fork, lê o `README.md` e os `reports/`, inspeciona a skill e roda os 3 projetos para checar os critérios de aceite. | Avançado; tempo limitado; precisa de evidência observável. |
| **Agente Claude Code** (executor) | Carrega `SKILL.md` e os arquivos de referência sob demanda; precisa de instruções inequívocas e acionáveis. | N/A — consome Markdown como prompt. |

## 4. Requisitos funcionais (RF)

### 4.1 Análise manual (pré-requisito da skill)
- **RF-01:** Para cada um dos 3 projetos, documentar no mínimo **5 problemas**, sendo no mínimo **1 CRITICAL ou HIGH**, **2 MEDIUM** e **2 LOW**.
- **RF-02:** Cada problema manual deve conter: projeto, severidade (escala da seção 5.1), título, arquivo e linha(s), descrição e **justificativa de relevância**.
- **RF-03:** A análise manual deve ser concluída **antes** da escrita da skill e servir de insumo para o catálogo de anti-patterns (rastreabilidade: cada problema manual mapeia para ≥ 1 anti-pattern do catálogo).

### 4.2 Estrutura da skill
- **RF-04:** A skill deve residir em `code-smells-project/.claude/skills/refactor-arch/`, com arquivo de entrada `SKILL.md` (nome do diretório `refactor-arch` e nome do arquivo `SKILL.md` são **imutáveis**).
- **RF-05:** `SKILL.md` deve ter frontmatter YAML válido para Claude Code com, no mínimo, `name: refactor-arch` e `description` (descrevendo quando usar a skill), e corpo descrevendo as 3 fases sequenciais e quando carregar cada arquivo de referência.
- **RF-06:** Os arquivos de referência devem ser Markdown (`.md`) dentro do diretório da skill e cobrir **obrigatoriamente** as 5 áreas:

  | Área | Conteúdo mínimo exigido |
  |---|---|
  | Análise de projeto | Heurísticas de detecção de linguagem, framework, banco de dados e mapeamento de arquitetura (manifests, imports, padrões de rotas, arquivos de DB). |
  | Catálogo de anti-patterns | ≥ 8 anti-patterns, cada um com sinais de detecção concretos e severidade; todas as 4 severidades representadas; inclui detecção de **APIs deprecated** com equivalente moderno. |
  | Template de relatório | Formato padronizado do relatório da Fase 2 (ver seção 7.3). |
  | Guidelines de arquitetura | Regras do MVC alvo: responsabilidades de Models, Views/Routes, Controllers (e camadas de apoio: config, middlewares/error handler, composition root). |
  | Playbook de refatoração | ≥ 8 padrões de transformação, cada um com exemplo de código **antes/depois**, mapeados aos anti-patterns do catálogo. |

  A quantidade e os nomes dos arquivos são livres (decisão do solution-architect); a cobertura das 5 áreas é obrigatória e deve ser rastreável (cada área → arquivo/seção).

### 4.3 Fase 1 — Análise
- **RF-07:** Detectar linguagem, framework (com versão quando declarada em manifest), dependências principais, banco de dados, domínio da aplicação, arquitetura atual, quantidade de arquivos-fonte analisados e tabelas/entidades do banco.
- **RF-08:** Imprimir o resumo no formato da seção 7.2 (bloco `PHASE 1: PROJECT ANALYSIS`).
- **RF-09:** A Fase 1 é somente leitura: nenhum arquivo é criado, alterado ou removido.

### 4.4 Fase 2 — Auditoria
- **RF-10:** Cruzar o código contra o catálogo de anti-patterns e produzir findings, cada um com severidade, título, **arquivo e linha(s) exatos** (`caminho:linha` ou `caminho:inicio-fim`), descrição, impacto e recomendação.
- **RF-11:** Findings ordenados por severidade: CRITICAL → HIGH → MEDIUM → LOW.
- **RF-12:** Incluir sumário com contagem por severidade e total de findings.
- **RF-13:** Incluir findings de APIs deprecated quando aplicável, citando a API obsoleta e o equivalente moderno.
- **RF-14:** O relatório deve seguir exatamente o template definido nos arquivos de referência da skill.
- **RF-15:** Ao final da Fase 2, a skill **deve pausar** e exibir a pergunta de confirmação (`Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`), **sem modificar nenhum arquivo do projeto** antes de receber resposta afirmativa.
- **RF-16:** Resposta negativa (`n` ou qualquer resposta diferente de afirmativa) encerra a skill sem modificações.

### 4.5 Fase 3 — Refatoração e validação
- **RF-17:** Reestruturar o projeto para o padrão MVC definido nas guidelines, adaptando-se ao nível de organização existente (monolito → criação de camadas; projeto parcialmente organizado → reorganização/melhoria das camadas existentes).
- **RF-18:** A estrutura resultante deve contemplar: módulo de configuração (sem segredos/valores hardcoded), Models para abstração de dados, Views/Routes para roteamento, Controllers concentrando o fluxo, error handling centralizado e entry point claro (composition root).
- **RF-19:** Aplicar as transformações do playbook correspondentes aos findings da Fase 2, priorizando CRITICAL e HIGH.
- **RF-20:** Validar o resultado: (a) a aplicação inicia sem erros; (b) **todos os endpoints originais** continuam respondendo (ver inventário na seção 7.5).
- **RF-21:** Imprimir o resumo final no formato da seção 7.4 (bloco `PHASE 3: REFACTORING COMPLETE`), com a nova estrutura de diretórios e o resultado de cada verificação de validação (aprovada/reprovada).
- **RF-22:** Se a validação falhar, a skill deve diagnosticar e corrigir antes de declarar sucesso, ou reportar explicitamente a falha (proibido declarar sucesso sem evidência).

### 4.6 Agnosticismo e reuso
- **RF-23:** Nenhum arquivo da skill pode conter caminhos, nomes de arquivos, tabelas, endpoints ou regras específicas de um dos 3 projetos como instrução obrigatória (exemplos ilustrativos são permitidos se marcados como exemplo e cobrirem mais de uma stack).
- **RF-24:** A mesma skill (byte a byte) deve funcionar nos 3 projetos, apenas copiando o diretório.

### 4.7 Execução nos 3 projetos e artefatos
- **RF-25:** Executar a skill em cada projeto a partir do diretório do projeto (`cd <projeto>` + `claude "/refactor-arch"`).
- **RF-26:** Salvar a saída da Fase 2 de cada projeto em `reports/audit-project-N.md` (N = 1, 2, 3 conforme seção 8), na raiz do repositório.
- **RF-27:** Commitar o código refatorado de cada projeto em commit(s) separado(s) por projeto.
- **RF-28:** Reescrever o `README.md` da raiz com as seções A–D (conteúdo mínimo na seção 7.6).

## 5. Requisitos não-funcionais (RNF)

### 5.1 Escala de severidade (literal do enunciado — obrigatória em análise manual, catálogo e relatórios)
- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### 5.2 Demais RNFs
- **RNF-01 (Segurança):** Após a Fase 3, nenhum segredo (SECRET_KEY, senhas, tokens, credenciais) pode permanecer hardcoded no código; valores devem vir de config/variáveis de ambiente com default seguro para desenvolvimento documentado. Nenhum `.env` real é commitado (`.gitignore` já ignora `.env`).
- **RNF-02 (Compatibilidade de contrato):** A refatoração deve preservar o contrato HTTP dos endpoints originais (método, path, formato básico de request/response e códigos de status de sucesso). Mudanças de contrato só são aceitas quando forem correção de segurança (ex.: não retornar senha na resposta) e devem ser registradas no relatório/README.
- **RNF-03 (Comando de boot):** Recomendado manter o comando de boot original funcional (`python app.py`; `npm start`; `python seed.py` + `python app.py`). Se mudar, o novo comando deve estar no README (Seção D) e no resumo da Fase 3.
- **RNF-04 (Portabilidade):** Todas as validações devem rodar nesta máquina Windows 11 (PowerShell), Python 3.12, Node 22, sem ferramentas externas além das já disponíveis (`curl.exe`, `Invoke-WebRequest`, Python `urllib`/Flask test client, Node `fetch` nativo).
- **RNF-05 (Contexto/tamanho da skill):** `SKILL.md` deve ser enxuto (orquestração das fases) e delegar conhecimento aos arquivos de referência (progressive disclosure), carregados sob demanda por fase.
- **RNF-06 (Determinismo do relatório):** Mesmo projeto + mesma skill ⇒ relatório no mesmo formato (template fixo); variação de conteúdo é aceitável, variação de formato não.
- **RNF-07 (Codificação):** Todos os arquivos Markdown em UTF-8 sem BOM.
- **RNF-08 (Idioma):** Documentação (README, relatórios, análise) em Português (Brasil); cabeçalhos do formato de CLI (ex.: `PHASE 1: PROJECT ANALYSIS`, `ARCHITECTURE AUDIT REPORT`) podem permanecer em inglês, como no enunciado.
- **RNF-09 (Rastreabilidade Git):** Histórico deve permitir distinguir: skill, refatoração do projeto 1, do projeto 2, do projeto 3, relatórios e README.

## 6. Stack obrigatória

- **Ferramenta:** Claude Code (versão local 2.1.310). Gemini CLI e Codex fora de escopo.
- **Recurso:** Custom Skills (`.claude/skills/refactor-arch/`).
- **Formato dos arquivos de referência:** Markdown.
- **Projetos-alvo (fornecidos, stacks não podem ser trocadas):**
  - `code-smells-project/` — Python/Flask 3.1.1, flask-cors 5.0.1, SQLite (`sqlite3` stdlib, arquivo `loja.db`), porta 5000.
  - `ecommerce-api-legacy/` — Node.js/Express ^4.18.2, sqlite3 ^5.1.6 (banco em memória com seed no boot), porta 3000.
  - `task-manager-api/` — Python/Flask 3.0.0, Flask-SQLAlchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0, python-dotenv 1.0.0, SQLite (`tasks.db`, populado por `seed.py`), porta 5000.
- **Ambiente de execução:** Windows 11 Pro, PowerShell, Python 3.12, Node 22.

## 7. Contratos e interfaces

### 7.1 Invocação
```bash
cd <projeto>
claude "/refactor-arch"
```
Pré-condição: `<projeto>/.claude/skills/refactor-arch/SKILL.md` existe.

### 7.2 Saída da Fase 1 (formato mínimo)
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework> <versão>
Dependencies:  <dependências principais>
Domain:        <descrição do domínio>
Architecture:  <descrição da arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <tabelas/entidades>
================================
```

### 7.3 Saída da Fase 2 / relatório (formato mínimo — o template definitivo fica nos arquivos de referência e deve ser compatível com este)
```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Título do anti-pattern>
File: <caminho>:<linha>[-<linha_fim>]
Description: <descrição>
Impact: <impacto>
Recommendation: <recomendação>

(... demais findings, ordenados CRITICAL → LOW ...)

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

### 7.4 Saída da Fase 3 (formato mínimo)
```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  ✓|✗ Application boots without errors
  ✓|✗ All endpoints respond correctly
  <outras verificações, ex.: findings residuais>
================================
```

### 7.5 Inventário de endpoints originais (baseline para validação da Fase 3)

Levantado do código original (commit `f50e265` do fork). A validação considera aprovado quando cada endpoint responde com o **mesmo código de status** da baseline (capturada antes da refatoração) para a mesma requisição, ou com código justificado por correção de segurança documentada. Nenhum endpoint pode responder 5xx ou deixar de existir (404 de rota inexistente) sem justificativa documentada.

**Projeto 1 — code-smells-project (porta 5000) — 19 rotas**
| Método | Path |
|---|---|
| GET | `/` |
| GET | `/health` |
| GET | `/produtos` |
| GET | `/produtos/busca` |
| GET | `/produtos/<id>` |
| POST | `/produtos` |
| PUT | `/produtos/<id>` |
| DELETE | `/produtos/<id>` |
| GET | `/usuarios` |
| GET | `/usuarios/<id>` |
| POST | `/usuarios` |
| POST | `/login` |
| POST | `/pedidos` |
| GET | `/pedidos` |
| GET | `/pedidos/usuario/<usuario_id>` |
| PUT | `/pedidos/<pedido_id>/status` |
| GET | `/relatorios/vendas` |
| POST | `/admin/reset-db` |
| POST | `/admin/query` |

(16 rotas via `add_url_rule` + 3 via `@app.route` em `app.py`; o QA deve reconfirmar a contagem via `app.url_map` antes da refatoração.)

**Projeto 2 — ecommerce-api-legacy (porta 3000) — 3 rotas** (exemplos em `api.http`)
| Método | Path |
|---|---|
| POST | `/api/checkout` (cenários: sucesso e pagamento recusado) |
| GET | `/api/admin/financial-report` |
| DELETE | `/api/users/:id` |

**Projeto 3 — task-manager-api (porta 5000) — 22 combinações método+path** (rodar `python seed.py` antes; reconfirmar via `app.url_map`)
| Método | Path |
|---|---|
| GET | `/` |
| GET | `/health` |
| GET / POST | `/tasks` |
| GET / PUT / DELETE | `/tasks/<task_id>` |
| GET | `/tasks/search` |
| GET | `/tasks/stats` |
| GET / POST | `/users` |
| GET / PUT / DELETE | `/users/<user_id>` |
| GET | `/users/<user_id>/tasks` |
| POST | `/login` |
| GET | `/reports/summary` |
| GET | `/reports/user/<user_id>` |
| GET / POST | `/categories` |
| PUT / DELETE | `/categories/<cat_id>` |

### 7.6 Conteúdo mínimo do `README.md` final
- **A) Análise Manual:** problemas por projeto, severidade, justificativa de relevância.
- **B) Construção da Skill:** decisões de design (estrutura do SKILL.md e referências), anti-patterns do catálogo e por quê, como garantiu agnosticismo, desafios e soluções.
- **C) Resultados:** findings por severidade em cada projeto; comparação antes/depois da estrutura; checklist de validação preenchido por projeto (seção 9.2); screenshots ou logs das aplicações rodando pós-refatoração; observações sobre comportamento em stacks diferentes.
- **D) Como Executar:** pré-requisitos (Claude Code instalado e configurado, Python 3.12, Node 22), comandos para executar a skill em cada projeto, como validar a refatoração.

### 7.7 Variáveis de ambiente
Não há `.env.example` exigido pelo enunciado. Se a Fase 3 extrair configuração para variáveis de ambiente (RF-18/RNF-01), cada projeto refatorado deve documentar as variáveis (nome, finalidade, default de desenvolvimento) — preferencialmente em `<projeto>/.env.example` — e funcionar sem `.env` presente (defaults de desenvolvimento), para não quebrar o boot na validação.

### 7.8 Prompts obrigatórios
O enunciado não define prompts literais além do comando `claude "/refactor-arch"` e da pergunta de confirmação `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, que deve ser reproduzida literalmente.

## 8. Estrutura de arquivos esperada (estado final)

```
mba-ia-refactor-projects-skill/
├── README.md                                  # reescrito (Seções A–D) — technical-writer
├── SPEC.md                                    # esta especificação
├── docs/ARCHITECTURE.md                       # solution-architect (design da skill)
├── docs/
│   ├── CHALLENGE.md                           # enunciado original (imutável)
│   ├── user-stories.md
│   └── manual-analysis.md                     # (sugerido) rascunho da análise manual, insumo da Seção A
├── reports/
│   ├── audit-project-1.md                     # Fase 2 — code-smells-project
│   ├── audit-project-2.md                     # Fase 2 — ecommerce-api-legacy
│   └── audit-project-3.md                     # Fase 2 — task-manager-api
├── code-smells-project/
│   ├── .claude/skills/refactor-arch/
│   │   ├── SKILL.md                           # nome imutável
│   │   └── <arquivos de referência>.md        # cobrindo as 5 áreas (nomes livres)
│   └── <código refatorado em MVC>
├── ecommerce-api-legacy/
│   ├── .claude/skills/refactor-arch/          # cópia idêntica
│   └── <código refatorado em MVC>
└── task-manager-api/
    ├── .claude/skills/refactor-arch/          # cópia idêntica
    └── <código refatorado em MVC>
```

A estrutura MVC interna de cada projeto é definida pelas guidelines de arquitetura da skill (ex. ilustrativo do enunciado: `src/config/`, `src/models/`, `src/views/` ou `routes/`, `src/controllers/`, `src/middlewares/`, `app` como composition root). Arquivos gerados em runtime (`*.db`, `node_modules/`, `__pycache__/`) não são commitados (já cobertos pelo `.gitignore`).

## 9. Critérios de aceite globais

### 9.1 Critérios obrigatórios do enunciado (3/3 projetos), em forma verificável

| ID | Critério | Verificação observável |
|---|---|---|
| CA-01 | Fase 1 detecta stack corretamente | Bloco `PHASE 1` do projeto 1 mostra `Python` + `Flask` (3.1.1); projeto 2 mostra `JavaScript/Node.js` + `Express` (4.x); projeto 3 mostra `Python` + `Flask` (3.0.0) e domínio "Task Manager". `Source files` coerente com a contagem real de arquivos-fonte (ref.: P1 = 4 `.py`; P2 = 3 `.js` em `src/`; P3 = 15 `.py` incluindo `__init__.py` — a skill deve declarar o critério de contagem). |
| CA-02 | Fase 2 encontra ≥ 5 findings | Em `reports/audit-project-N.md`, `Total: X findings` com X ≥ 5, para N = 1, 2, 3; e o número de blocos `### [` é igual a X. |
| CA-03 | Fase 2 inclui ≥ 1 CRITICAL ou HIGH | Em cada relatório, `CRITICAL + HIGH ≥ 1` no Summary e ≥ 1 bloco `### [CRITICAL]` ou `### [HIGH]`. |
| CA-04 | Fase 3: aplicação funciona após refatoração | Para cada projeto, com o código do commit de refatoração: o comando de boot documentado sobe o servidor sem exceção/stack trace, a porta (5000/3000) aceita conexões e **todos** os endpoints do inventário 7.5 respondem com o status da baseline (sem 5xx, sem 404 de rota). |

### 9.2 Critérios adicionais derivados do enunciado

| ID | Critério | Verificação observável |
|---|---|---|
| CA-05 | Análise manual | No `README.md` Seção A, por projeto: ≥ 5 problemas; contagem CRITICAL+HIGH ≥ 1, MEDIUM ≥ 2, LOW ≥ 2; cada item com arquivo:linha e justificativa. |
| CA-06 | Projeto 1 cobre a análise manual | ≥ 5 dos problemas manuais do projeto 1 aparecem (mesmo arquivo e anti-pattern equivalente) em `reports/audit-project-1.md`. |
| CA-07 | Estrutura da skill | Existe `code-smells-project/.claude/skills/refactor-arch/SKILL.md` com frontmatter `name: refactor-arch`; todos os demais arquivos da skill são `.md`. |
| CA-08 | 5 áreas cobertas | Tabela de rastreabilidade (README Seção B ou docs/ARCHITECTURE.md) mapeia cada uma das 5 áreas a arquivo/seção existente. |
| CA-09 | Catálogo | Catálogo lista ≥ 8 anti-patterns, cada um com severidade e sinais de detecção; há ≥ 1 por severidade (CRITICAL, HIGH, MEDIUM, LOW); há ≥ 1 entrada de APIs deprecated com "obsoleto → moderno". |
| CA-10 | Playbook | Playbook lista ≥ 8 transformações, cada uma com bloco de código "antes" e bloco "depois". |
| CA-11 | Cópias idênticas | `git diff --no-index code-smells-project/.claude/skills/refactor-arch ecommerce-api-legacy/.claude/skills/refactor-arch` e idem para `task-manager-api` não retornam diferenças (ou hashes `Get-FileHash` iguais arquivo a arquivo). |
| CA-12 | Pausa obrigatória | Em cada execução: após o relatório aparece literalmente `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, e `git status` do projeto mostra zero alterações em arquivos do projeto nesse momento. |
| CA-13 | Template respeitado | Os 3 relatórios têm as mesmas seções/campos do template de referência; cada finding tem `File: caminho:linha`; ordem CRITICAL → HIGH → MEDIUM → LOW. |
| CA-14 | MVC | Cada projeto refatorado possui camadas identificáveis de config, models, views/routes, controllers, error handling centralizado e um entry point único; nenhum segredo hardcoded (busca por `SECRET_KEY = '`/literal de senha não retorna ocorrências em código). |
| CA-15 | Relatórios | Existem exatamente `reports/audit-project-1.md`, `reports/audit-project-2.md`, `reports/audit-project-3.md`. |
| CA-16 | Commits separados | `git log --stat` mostra commit(s) de refatoração distintos para cada projeto, cada um tocando apenas arquivos do respectivo projeto. |
| CA-17 | README | `README.md` contém as seções A, B, C e D com o conteúdo mínimo de 7.6, incluindo checklist preenchido dos 3 projetos e logs/screenshots. |
| CA-18 | Enunciado preservado | `docs/CHALLENGE.md` existe com o conteúdo do README original. |

### 9.3 Checklist de validação (literal do enunciado) — preencher por projeto

Aplicar a cada um: **Projeto 1 (code-smells-project)**, **Projeto 2 (ecommerce-api-legacy)**, **Projeto 3 (task-manager-api)**.

```markdown
## Checklist de Validação — <Projeto N>

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

Valores esperados por projeto na Fase 1 (referência para o QA):

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Linguagem | Python | JavaScript (Node.js) | Python |
| Framework | Flask 3.1.1 | Express 4.x | Flask 3.0.0 (+ Flask-SQLAlchemy) |
| Banco | SQLite (`loja.db`) | SQLite em memória | SQLite (`tasks.db`) |
| Domínio | E-commerce (produtos, pedidos, usuários) | LMS com fluxo de checkout (cursos, matrículas/pagamentos, usuários) | Task Manager (tasks, usuários, categorias, relatórios) |
| Organização atual | Monolito em 4 arquivos | Monolito (God Class `AppManager`) | Parcialmente em camadas (models/routes/services/utils) |

## 10. Restrições, riscos, premissas e decisões em aberto

### 10.1 Restrições (invioláveis)
- R-01: Nome da skill `refactor-arch` e arquivo `SKILL.md` imutáveis; caminho `.claude/skills/refactor-arch/`.
- R-02: Arquivos de referência exclusivamente em Markdown.
- R-03: Os relatórios em `reports/` devem seguir o template definido na skill (sem reformatar manualmente além de remover ruído do terminal, ex.: códigos ANSI).
- R-04: Nenhum arquivo do projeto-alvo pode ser modificado antes da confirmação da Fase 2 (Fases 1 e 2 são somente leitura no projeto).
- R-05: Código refatorado commitado por projeto, em commits separados (ver CA-16).
- R-06: As 3 cópias da skill devem ser idênticas; ajustes na skill durante iterações devem ser propagados às 3 cópias.
- R-07: Não trocar stacks, não adicionar features (NO-02, NO-03).
- R-08: A ferramenta é exclusivamente Claude Code.

### 10.2 Premissas
- P-01: O repositório `mba-ia-refactor-projects-skill` possui `.git` próprio; o diretório pai (`Documents\MBA`) também é um repositório Git — todos os commits devem ser feitos no repositório `mba-ia-refactor-projects-skill`.
- P-02: Os projetos originais sobem no estado atual (baseline) com os comandos dos seus READMEs; caso algum não suba, isso é registrado como finding/baseline e a Fase 3 deve deixá-lo funcional.
- P-03: `npm install` do `sqlite3` funciona no Windows/Node 22 via binário pré-compilado (sem toolchain C++).
- P-04: Os projetos Flask usam a mesma porta 5000 — validações dos projetos 1 e 3 são executadas sequencialmente.
- P-05: Claude Code 2.1.310 descobre skills de projeto em `<cwd>/.claude/skills/` quando invocado com `cd <projeto>`.

### 10.3 Riscos
| ID | Risco | Mitigação |
|---|---|---|
| RK-01 | Execução não interativa (`claude -p`/agente orquestrador) não permite a pausa humana real; a skill poderia seguir direto para a Fase 3. | Ver D-01. SKILL.md deve instruir parada explícita após a Fase 2 sem tocar arquivos. |
| RK-02 | Endpoints perigosos do projeto 1 (`/admin/query`, `/admin/reset-db`) conflitam entre "corrigir vulnerabilidade" e "endpoints originais continuam respondendo". | Ver D-03. |
| RK-03 | Refatoração altera contrato (nomes de campos, status codes) e quebra clientes (ex.: payload `usr`/`eml`/`pwd`/`c_id` do checkout). | RNF-02: preservar contrato; comparar com baseline de status. |
| RK-04 | Falha de build do `sqlite3` nativo no Windows. | Validar `npm install` na etapa devops; se falhar, registrar e usar versão com prebuild compatível dentro de `^5.1.6`. |
| RK-05 | Conflito de porta 5000 / processos órfãos de servidores em background no Windows. | Encerrar processos após cada validação (`Stop-Process`); validar projetos sequencialmente. |
| RK-06 | Skill acoplada aos projetos (exemplos específicos viram regras). | RF-23; revisão de agnosticismo pelo QA (busca por nomes de tabelas/rotas dos projetos nos arquivos da skill). |
| RK-07 | Relatório com linhas imprecisas (alucinação de `arquivo:linha`). | QA amostra ≥ 5 findings por relatório e confere linha no código original (commit `f50e265`). |
| RK-08 | Banco SQLite de arquivo (`loja.db`, `tasks.db`) gerado no boot fica sujo entre baseline e pós-refatoração, alterando respostas. | Apagar `*.db` antes de cada rodada de validação (e rodar `seed.py` no projeto 3). |
| RK-09 | Saída de terminal com caracteres ANSI/Unicode (`✓`, `├──`) corrompida ao salvar no Windows. | Salvar relatórios em UTF-8 sem BOM; remover sequências ANSI. |
| RK-10 | Necessidade de 2–4 iterações da skill (prevista no enunciado) gera divergência entre cópias e relatórios antigos. | R-06; relatórios finais devem corresponder à última versão da skill; restaurar o projeto para o estado original (`git checkout`) antes de reexecutar. |

### 10.4 Decisões em aberto (a resolver pelo solution-architect, com recomendação do PM)
- **D-01 — Registro da confirmação humana em execução automatizada.** Recomendação: a skill sempre encerra a Fase 2 com a pergunta literal e para. Em modo interativo, o operador digita `y`. Em modo automatizado, a execução é feita em duas etapas: (1) invocação que roda Fases 1–2 e para; (2) após revisão do relatório, nova invocação/mensagem com confirmação explícita (`y`) que executa a Fase 3. Evidência registrada no README (Seção C): trecho de log mostrando a pergunta, a resposta `y` e `git status` limpo entre as etapas.
- **D-02 — Quem grava `reports/audit-project-N.md`.** Recomendação: a skill imprime o relatório (stdout) seguindo o template; o operador/orquestrador salva o conteúdo em `reports/` na raiz do repositório (fora do projeto-alvo, portanto não viola R-04). Alternativa: a skill grava o relatório em um caminho de saída antes da pergunta — aceitável somente se o arquivo ficar fora do código-fonte do projeto e isso estiver documentado no SKILL.md.
- **D-03 — Endpoints intrinsecamente inseguros (ex.: execução de SQL arbitrário, reset de banco sem autenticação).** Recomendação: manter a rota registrada (o endpoint "continua respondendo"), mas protegida/desabilitada por configuração (ex.: responder 403 quando a flag de admin/debug estiver desligada), com a mudança de status documentada como correção de segurança no relatório e no README. Remoção completa só se justificada por escrito.
- **D-04 — Estratégia de validação de endpoints sem ferramentas externas.** Recomendação: (a) capturar baseline de status de todos os endpoints do inventário 7.5 no código original; (b) após a Fase 3, subir a aplicação em background e repetir as mesmas requisições com o cliente HTTP disponível (`curl.exe`, `Invoke-WebRequest`, Python `urllib`, Node `fetch`) ou test client do framework (Flask `test_client`); (c) comparar. A skill deve descrever isso de forma agnóstica (descobrir comando de boot, porta e rotas a partir do código). Scripts de smoke do QA, se criados, ficam fora dos diretórios da skill.
- **D-05 — Critério de contagem de "Source files".** Recomendação: contar arquivos de código-fonte da aplicação (excluindo dependências, `node_modules`, `.claude/`, arquivos vazios como `__init__.py` sem conteúdo podem ser excluídos desde que o critério seja declarado no resumo).
- **D-06 — Comando de boot pós-refatoração.** Recomendação: preservar os comandos originais (RNF-03), mantendo um entry point fino na raiz que delega ao composition root.
- **D-07 — Nomes e quantidade dos arquivos de referência.** Livre; recomendação: um arquivo por área (5 arquivos) para facilitar rastreabilidade (CA-08).

## 11. Roadmap de execução

1. **solution-architect** → `docs/ARCHITECTURE.md`: design da skill (estrutura do SKILL.md, arquivos de referência e mapeamento das 5 áreas, fluxo das 3 fases, mecanismo de pausa), resolução das decisões D-01 a D-07, estrutura MVC alvo genérica e como ela se aplica a monolito vs. projeto parcialmente organizado.
2. **devops-engineer** → preparação do ambiente local: venvs Python 3.12 por projeto, `npm install` no projeto 2, confirmação de boot dos 3 projetos originais, captura da **baseline** de endpoints (inventário 7.5) e utilitários de smoke (fora da skill); sem Docker (NO-04).
3. **python-developer** → (a) análise manual dos 3 projetos (`docs/manual-analysis.md`); (b) escrita da skill em `code-smells-project/.claude/skills/refactor-arch/`; (c) cópia para os outros 2 projetos; (d) execução da skill nos 3 projetos (com pausa/confirmação), salvando `reports/audit-project-{1,2,3}.md`; (e) commits separados por projeto; iterar 2–4 vezes se necessário.
4. **qa-engineer** → verificação dos critérios CA-01 a CA-18, preenchimento do checklist 9.3 por projeto, conferência de `arquivo:linha` por amostragem, comparação baseline × pós-refatoração, coleta de logs/screenshots.
5. **technical-writer** → reescrita do `README.md` com as seções A–D a partir de `docs/manual-analysis.md`, `docs/ARCHITECTURE.md`, `reports/` e evidências do QA.
