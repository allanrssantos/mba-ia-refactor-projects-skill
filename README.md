# Skill `refactor-arch` — Refatoração Arquitetural Automatizada

Desafio "Criação de Skills" do MBA IA (Full Cycle). Este repositório entrega uma **Custom Skill do Claude Code** chamada `refactor-arch` que, invocada na raiz de um projeto backend legado, executa três fases em sequência: (1) **análise** da stack e da arquitetura, (2) **auditoria** contra um catálogo de 20 anti-patterns, com relatório classificado por severidade e **pausa obrigatória** para confirmação humana, e (3) **refatoração para MVC** seguida de validação (boot real da aplicação e comparação de status de todos os endpoints). A skill foi escrita uma vez, é agnóstica de tecnologia e foi aplicada, sem alterações, em três projetos legados: dois Python/Flask e um Node.js/Express.

**Ferramenta:** Claude Code 2.1.310 (recurso: Custom Skills, em `.claude/skills/refactor-arch/`). Arquivos de referência da skill em Markdown. Enunciado original preservado, sem edição, em [docs/CHALLENGE.md](docs/CHALLENGE.md).

**Navegação:** [A) Análise Manual](#a-análise-manual) · [B) Construção da Skill](#b-construção-da-skill) · [C) Resultados](#c-resultados) · [D) Como Executar](#d-como-executar)

**Estrutura do repositório**

```
.
├── README.md                          # este documento
├── SPEC.md                            # especificação (requisitos, critérios de aceite CA-01..CA-18)
├── docs/
│   ├── CHALLENGE.md                   # enunciado original (imutável)
│   ├── ARCHITECTURE.md                # design da skill e ADRs 01-14
│   ├── manual-analysis.md             # análise manual completa (fonte da Seção A)
│   ├── test-report.md                 # relatório do QA (CA-01..CA-18)
│   ├── ENVIRONMENT.md                 # ambiente local e scripts
│   ├── user-stories.md
│   └── evidence/
│       ├── claude-cli-flags.md        # flags do claude e sequência de execução em 2 etapas
│       └── project-{1,2,3}/           # baselines, logs de boot, logs das etapas, checklists
├── reports/
│   ├── audit-project-1.md             # saída da Fase 2 - code-smells-project
│   ├── audit-project-2.md             # saída da Fase 2 - ecommerce-api-legacy
│   └── audit-project-3.md             # saída da Fase 2 - task-manager-api
├── scripts/                           # utilitários PowerShell (fora dos projetos e da skill)
│   ├── smoke.ps1, smoke-project-{1,2,3}.ps1
│   ├── sync-skill.ps1, extract-report.ps1, reset-project.ps1
├── code-smells-project/               # Projeto 1 - Python/Flask (e-commerce), refatorado
├── ecommerce-api-legacy/              # Projeto 2 - Node.js/Express (LMS com checkout), refatorado
└── task-manager-api/                  # Projeto 3 - Python/Flask (Task Manager), refatorado
    # os três contêm .claude/skills/refactor-arch/ (cópias idênticas da skill)
```

**Documentos de apoio:** [SPEC.md](SPEC.md) (requisitos) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (decisões e ADRs) · [docs/manual-analysis.md](docs/manual-analysis.md) · [docs/test-report.md](docs/test-report.md) · [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) · [docs/evidence/claude-cli-flags.md](docs/evidence/claude-cli-flags.md) · [reports/](reports/).

> Referência de "código original": todos os `arquivo:linha` desta documentação apontam para o código **antes** da refatoração (commit base `6d1ce62`, `origin/main`). Os commits de refatoração são `56b46d0` (Projeto 1), `0912915` (Projeto 2) e `38879fe` (Projeto 3); a skill foi commitada em `a6415bb`.

---

## A) Análise Manual

A análise foi feita lendo o código dos três projetos **antes** de escrever a skill, e serviu de insumo direto para o catálogo de anti-patterns (cada problema abaixo mapeia para uma entrada AP-xx; ver Seção B). Severidades seguem a escala do enunciado (CRITICAL, HIGH, MEDIUM, LOW). A lista completa, com detalhamento, está em [docs/manual-analysis.md](docs/manual-analysis.md); os caminhos são relativos à raiz de cada projeto e as linhas são do código original.

| Projeto | Stack | Problemas documentados | CRITICAL | HIGH | MEDIUM | LOW |
|---|---|---|---|---|---|---|
| 1 - `code-smells-project` | Python + Flask 3.1.1 + sqlite3 | 14 | 6 | 3 | 3 | 2 |
| 2 - `ecommerce-api-legacy` | Node.js + Express 4 + sqlite3 (memória) | 13 | 5 | 3 | 3 | 2 |
| 3 - `task-manager-api` | Python + Flask 3.0.0 + Flask-SQLAlchemy | 14 | 3 | 3 | 5 | 3 |

O mínimo do enunciado (>= 5 problemas, >= 1 CRITICAL/HIGH, >= 2 MEDIUM, >= 2 LOW) é cumprido nos três.

### Projeto 1 - `code-smells-project` (Python/Flask, API de e-commerce)

Monolito em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`): rotas em `app.py`, "controllers" que são funções soltas com validação e `print`, e um `models.py` com SQL e regras de todos os domínios.

| # | Sev. | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 1.1 | CRITICAL | SQL Injection em praticamente todas as queries (login e busca concatenam texto do cliente) | `models.py:109-111`, `models.py:289-297`, `models.py:28`, `47-50`, `126-129` e outras | Explorável sem autenticação: permite ler/destruir o banco e burlar o login com `' OR '1'='1`. |
| 1.2 | CRITICAL | Endpoints administrativos sem autenticação: reset do banco e execução de SQL arbitrário | `app.py:47-57`, `app.py:59-78` | Com o servidor em `0.0.0.0`, qualquer pessoa na rede apaga ou exfiltra o banco com uma requisição. |
| 1.3 | CRITICAL | `SECRET_KEY` hardcoded | `app.py:7` | Chave de assinatura de sessão no repositório; permite forjar cookies (agravado por 1.4, que a publica via HTTP). |
| 1.4 | CRITICAL | Exposição de dados sensíveis: segredo em `/health`, senhas em `/usuarios` | `controllers.py:286-289`, `models.py:83`, `models.py:99` | Qualquer cliente obtém o segredo da aplicação e as senhas de todos os usuários. |
| 1.5 | CRITICAL | Senhas gravadas e comparadas em texto puro | `database.py:75-83`, `models.py:126-129`, `models.py:109-111` | Um vazamento do `loja.db` expõe todas as credenciais, em geral reutilizadas em outros serviços. |
| 1.6 | CRITICAL | God Module: `models.py` com SQL e regras de 4 domínios | `models.py:1-314` | Nenhum domínio é testável ou alterável isoladamente; é a raiz que impede a separação MVC. |
| 1.7 | HIGH | Estado global mutável: conexão SQLite única compartilhada entre threads | `database.py:4-11` | Transações de requisições diferentes se misturam (o `commit` de uma confirma escritas pendentes de outra). |
| 1.8 | HIGH | Configuração de runtime insegura: `DEBUG=True`, bind `0.0.0.0`, CORS aberto | `app.py:8`, `app.py:9`, `app.py:88` | O debugger do Werkzeug exposto na rede permite execução remota de código; nada configurável por ambiente. |
| 1.9 | HIGH | Criação de pedido sem transação (várias escritas, retornos antecipados, sem rollback) | `models.py:133-169` | Falha no meio deixa pedidos sem itens e estoque inconsistente; a checagem de estoque também não é atômica. |
| 1.10 | MEDIUM | Queries N+1 na listagem de pedidos (itens por pedido, produto por item) | `models.py:187-193`, `models.py:219-225` | `GET /pedidos` executa 1 + P + P*I consultas; degrada linearmente com o volume. |
| 1.11 | MEDIUM | Validação inconsistente: o PUT de produto não valida o que o POST valida; `get_json()` sem checar `None` | `controllers.py:24-62` vs `64-96`, `controllers.py:169-170`, `239-240` | Dados que o POST rejeita entram via PUT; entradas comuns viram erro 500. |
| 1.12 | MEDIUM | Erro genérico: `except Exception` devolvendo `str(e)` em todo handler | `controllers.py:10-12` (padrão no arquivo todo), `app.py:77-78` | Mensagens internas (SQL, tabelas) vazam ao cliente e ajudam a explorar 1.1; sem handler central. |
| 1.13 | LOW | Magic numbers/strings: faixas e taxas de desconto, listas de categorias e status inline | `models.py:256-262`, `controllers.py:52`, `controllers.py:242` | Regras comerciais escondidas, difíceis de localizar e manter. |
| 1.14 | LOW | `print` como log, inclusive simulando envio de e-mail/SMS/push no fluxo do pedido | `controllers.py:8`, `57`, `208-210` e outras | Sem níveis nem destino configurável; integração simulada inline impede troca por serviço real. |

### Projeto 2 - `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

Três arquivos em `src/`: `app.js` (bootstrap), `AppManager.js` (cria banco em memória, faz seed, registra as 3 rotas e contém toda a lógica) e `utils.js` (config com segredos, cache global e "criptografia" caseira).

| # | Sev. | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 2.1 | CRITICAL | Credenciais hardcoded: senha de banco, chave "live" do gateway, usuário SMTP | `src/utils.js:1-7` | Vazamento do repositório permite cobranças no gateway e acesso ao banco de produção. |
| 2.2 | CRITICAL | God Class `AppManager`: banco, schema, seed, rotas e regras no mesmo lugar | `src/AppManager.js:4-139` | Nada é testável isoladamente; é o exemplo clássico de God Class da escala CRITICAL. |
| 2.3 | CRITICAL | Número do cartão e chave do gateway escritos no log | `src/AppManager.js:45` | Cartão completo e chave em logs violam PCI-DSS e espalham segredos para qualquer sistema de log. |
| 2.4 | CRITICAL | Relatório financeiro e deleção de usuário sem autenticação | `src/AppManager.js:80-129`, `src/AppManager.js:131-137` | Exposição de PII/financeiro e destruição de dados por qualquer cliente. |
| 2.5 | CRITICAL | "Hash" de senha caseiro e reversível; seed em texto puro; senha padrão `123456` | `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:68` | Senhas efetivamente desprotegidas e contas criadas com senha previsível. |
| 2.6 | HIGH | Checkout em pirâmide de 5 callbacks, sem transação; erro de auditoria ignorado | `src/AppManager.js:37-77`, `57-61` | Matrícula gravada mesmo se o pagamento falhar; inconsistência financeira e código ilegível. |
| 2.7 | HIGH | Deleção de usuário deixa matrículas e pagamentos órfãos e ignora o erro | `src/AppManager.js:131-137` | Relatórios passam a mostrar alunos "Unknown" e dados inconsistentes se acumulam. |
| 2.8 | HIGH | Estado global mutável: cache sem limite e contador de receita no módulo | `src/utils.js:9-15` | Crescimento de memória ilimitado, estado não isolável e inútil (nada lê o cache). |
| 2.9 | MEDIUM | N+1 no relatório financeiro (por curso, matrícula, usuário e pagamento) | `src/AppManager.js:89-127` | Consultas crescem com cursos x matrículas; contadores manuais de resposta são frágeis. |
| 2.10 | MEDIUM | Validação só por truthiness; `card` não-string derruba o processo (`TypeError`) | `src/AppManager.js:35`, `src/AppManager.js:46` | Uma requisição malformada tira a API do ar. |
| 2.11 | MEDIUM | Erros de callback ignorados (`err` não lido; `enrollments.length` sobre `undefined`) | `src/AppManager.js:92-93`, `104-106`, `133-135` | Falhas silenciosas ou queda total, sem error handler central. |
| 2.12 | LOW | Nomes ruins (`u`, `e`, `p`, `cid`, `cc`, `badCrypto`) | `src/AppManager.js:29-33`, `src/utils.js:17` | Leitura lenta do fluxo mais crítico (checkout). |
| 2.13 | LOW | Magic numbers/strings: prefixo `"4"` aprova pagamento, `10000` iterações, corte em 10 caracteres | `src/AppManager.js:46`, `src/utils.js:19`, `src/utils.js:22` | Regras de negócio implícitas, difíceis de achar e alterar. |

APIs deprecated: nenhuma encontrada neste projeto (`sqlite3.verbose()` e `express.json()` são atuais); o item do checklist é "não aplicável".

### Projeto 3 - `task-manager-api` (Python/Flask, Task Manager)

Já tem `models/`, `routes/`, `services/` e `utils/`, mas: não há controllers (as rotas concentram validação, regras e consultas), nem módulo de config nem error handler; a aplicação é criada no import de `app.py`; `services/` e `utils/` não são usados; há falhas de segurança no model de usuário.

| # | Sev. | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 3.1 | CRITICAL | Credenciais hardcoded: `SECRET_KEY` e senha SMTP | `app.py:13`, `services/notification_service.py:7-10` | Segredo de assinatura e senha de e-mail versionados. |
| 3.2 | CRITICAL | `to_dict()` devolve o hash da senha em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` | `models/user.py:21`; usado em `routes/user_routes.py:33`, `85`, `129`, `209` | Qualquer cliente obtém os hashes, quebráveis em segundos (3.3). |
| 3.3 | CRITICAL | Senha com MD5 sem sal | `models/user.py:27-32` | Revertido por rainbow tables; senhas iguais geram hashes iguais. |
| 3.4 | HIGH | Regra de negócio e acesso a dados nas rotas (sem controllers) | `routes/task_routes.py:85-154`, `routes/report_routes.py:12-101` | Problema central apesar das pastas: regras não reutilizáveis e não testáveis sem HTTP. |
| 3.5 | HIGH | Aplicação criada no import, sem factory/config; `seed.py` acoplado ao módulo | `app.py:9-31`, `seed.py:2` | Impossível criar a app com outra config (testes, banco em memória); import tem efeitos colaterais no banco. |
| 3.6 | HIGH | `debug=True`, bind `0.0.0.0`, CORS aberto | `app.py:34`, `app.py:15` | Debugger do Werkzeug exposto na rede (execução remota de código). |
| 3.7 | MEDIUM | N+1: usuário e categoria por task; `u.tasks` lazy por usuário; `count()` por categoria | `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-56`, `163` | Consultas crescem com o volume de dados. |
| 3.8 | MEDIUM | Cálculo de "atrasada" duplicado em 6 lugares apesar de `Task.is_overdue()` existir | `routes/task_routes.py:30-39`, `71-80`, `283-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:34-36`, `132-135` (vs `models/task.py:50-60`) | Mudar a regra exige replicar em 6 pontos; risco alto de divergência. |
| 3.9 | MEDIUM | APIs deprecated: `Model.query.get()` (legado no SQLAlchemy 2.x) e `datetime.utcnow()` (deprecated no Python 3.12) | `routes/task_routes.py:42` (+15 ocorrências), `models/task.py:15-16` (+20 ocorrências) | Quebra em atualizações de runtime/biblioteca; o enunciado exige detecção de APIs deprecated. |
| 3.10 | MEDIUM | `except:` genérico em todas as rotas, sem handler central | `routes/task_routes.py:62-63`, `137`, `204`, `236`; `routes/user_routes.py:130`, `149`; `routes/report_routes.py:186`, `207`, `221` | Esconde a causa das falhas e captura até `KeyboardInterrupt`/`SystemExit`. |
| 3.11 | MEDIUM | Validação de tipo ausente: `priority` string e corpo ausente geram 500 | `routes/task_routes.py:113`, `182`; `routes/report_routes.py:196-197` | 500 para entradas comuns em vez de 400; os validadores de `utils/helpers.py` não são usados. |
| 3.12 | LOW | Imports não usados e código morto (`NotificationService`, `utils/helpers.py` inteiro) | `app.py:7`, `routes/task_routes.py:7`, `services/notification_service.py:4-48`, `utils/helpers.py:1-116` | Camadas "de fachada" dão falsa impressão de organização. |
| 3.13 | LOW | Magic numbers/strings: status e faixa de prioridade inline, apesar das constantes existentes | `routes/task_routes.py:110`, `113`, `177`, `182`; `routes/report_routes.py:45`, `129` (constantes em `utils/helpers.py:110-116`) | Regras espalhadas e constantes ignoradas. |
| 3.14 | LOW | Nomes ruins (`p1`...`p5`) e `print` como log | `routes/report_routes.py:24-28`; `routes/task_routes.py:149`, `153`, `219`, `234` | Legibilidade e observabilidade ruins. |

---

## B) Construção da Skill

A skill vive em `code-smells-project/.claude/skills/refactor-arch/` (fonte) e tem cópias byte a byte em `ecommerce-api-legacy/` e `task-manager-api/`. O design completo e as decisões (ADR-01 a ADR-14) estão em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Estrutura do SKILL.md e progressive disclosure

```
.claude/skills/refactor-arch/
├── SKILL.md                    # orquestrador (~130 linhas)
├── project-analysis.md         # Fase 1
├── anti-patterns-catalog.md    # Fase 2
├── deprecated-apis.md          # Fase 2 (só a seção da stack detectada)
├── audit-report-template.md    # Fase 2
├── mvc-guidelines.md           # Fase 3
├── refactoring-playbook.md     # Fase 3 (só as seções T-xx citadas nos findings)
└── phase3-validation.md        # Fase 3
```

- **`SKILL.md` só orquestra.** Tem frontmatter (`name: refactor-arch` e `description` dizendo quando usar), uma tabela "fase -> o que ler antes de começar", as regras invioláveis, as três fases, o ponto de parada e os blocos de saída exatos. Todo conhecimento de domínio fica nas referências.
- **Progressive disclosure.** Cada fase carrega apenas os arquivos que precisa: a Fase 1 lê só `project-analysis.md`; a Fase 2, catálogo, template e a seção do ecossistema detectado em `deprecated-apis.md`; a Fase 3, guidelines, validação e só as transformações `T-xx` citadas nas Recommendations. Isso mantém o contexto enxuto (SPEC RNF-05).
- **Estrutura plana, tudo `.md`.** Links relativos simples e verificação de identidade por hash arquivo a arquivo; nenhum script ou JSON auxiliar dentro da skill.
- **Regras invioláveis no topo:** Fases 1 e 2 somente leitura; pausa obrigatória; sem novas dependências; contrato HTTP preservado; descobrir (nunca assumir) nomes, rotas, porta e comando de boot; nunca declarar sucesso sem evidência produzida na execução.

### As 3 fases

| Fase | O que faz | Saída | Efeito no disco |
|---|---|---|---|
| 1 - Análise | Detecta linguagem, framework+versão, dependências, banco/tabelas, rotas, entry point, comando de boot, porta, seed; classifica a arquitetura como `monolith`, `partial-layers` ou `layered` | Bloco `PHASE 1: PROJECT ANALYSIS` | Nenhum |
| 2 - Auditoria | Lê todos os arquivos-fonte com numeração, percorre AP-01..AP-20, descarta falsos positivos, reconfere cada `arquivo:linha`, agrupa e ordena CRITICAL -> LOW | Bloco `ARCHITECTURE AUDIT REPORT` + pergunta literal | Nenhum |
| 3 - Refatoração | 3.0 baseline do código original; 3.1 estrutura-alvo conforme a classificação; 3.2 transformações do playbook; 3.3 revalidação (boot + endpoints); 3.4 varredura de resíduos e segredos; 3.5 limpeza | Bloco `PHASE 3: REFACTORING COMPLETE` | Escrita no projeto; temporários só no diretório temporário do SO |

### Pausa obrigatória e como foi garantida no modo `-p`

1. O `SKILL.md` termina a Fase 2 com a pergunta literal `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e manda **encerrar o turno**: nenhuma chamada de ferramenta, nenhum texto adicional. Respostas afirmativas (`y`, `yes`, `s`, `sim`) iniciam a Fase 3; qualquer outra imprime `Refactoring cancelled. No files were modified.` e encerra.
2. Até o "y" é proibido tudo que cria arquivos: Write/Edit, `mkdir`, instalar dependências, executar a aplicação ou seeds (subir a app cria `*.db` e `__pycache__`). Por isso a baseline de endpoints é capturada **no início da Fase 3**, e não antes (ver desafios).
3. No modo não interativo (`claude -p`) a execução é feita em **duas etapas na mesma sessão**: `claude -p "/refactor-arch" --permission-mode plan` (modo plano bloqueia edições, segunda barreira) e, depois da revisão do relatório, `claude -p --continue "y" ...`. Entre as etapas registra-se `git status --porcelain -- .`, que ficou **vazio (0 bytes)** nos três projetos (`docs/evidence/project-N/stage1-git-status.txt`). No Projeto 2, a calibração foi encerrada com `claude -p --continue "n"` e a skill respondeu `Refactoring cancelled. No files were modified.` (`docs/evidence/project-2/stage1-calib-answer-n.log`). Flags verificadas em [docs/evidence/claude-cli-flags.md](docs/evidence/claude-cli-flags.md).

### Rastreabilidade das 5 áreas de conhecimento

| Área obrigatória do enunciado | Arquivo de referência | Conteúdo |
|---|---|---|
| Análise de projeto | `project-analysis.md` | Linguagem por manifesto, framework e versão (lockfile > pin > faixa), banco e tabelas, inventário de rotas, entry point/boot/porta/seed, domínio, classificação da arquitetura, critério de contagem de arquivos/LOC, formato do bloco PHASE 1 |
| Catálogo de anti-patterns | `anti-patterns-catalog.md` | 20 entradas com severidade fixa, sinais de detecção (buscas ripgrep + leitura), "não confundir com", impacto, recomendação e transformação que resolve |
| Template de relatório | `audit-report-template.md` | Template literal do relatório, regras de preenchimento, ordenação, agrupamento determinístico de ocorrências, contagens e exemplo sintético |
| Guidelines de arquitetura | `mvc-guidelines.md` | Responsabilidades e proibições de cada camada, estrutura-alvo por ecossistema, adaptação ao nível de organização, config, error handling, lista fechada de mudanças de contrato permitidas, checklist de conformidade |
| Playbook de refatoração | `refactoring-playbook.md` | 16 transformações (T-01..T-16), cada uma com blocos antes/depois, passos e armadilhas de contrato |
| Extra 1 | `deprecated-apis.md` | Tabela "obsoleto -> moderno" por stack (Python, Flask/Werkzeug, SQLAlchemy, Node, Express, pacotes comuns); complementa AP-16 |
| Extra 2 | `phase3-validation.md` | Procedimento de baseline, boot em background, runners HTTP (Python/Node/`curl.exe`), comparação e ciclos de correção, varredura final e formato do bloco PHASE 3 |

Os dois arquivos extras existem porque a tabela de APIs deprecated cresce por stack e só interessa para a stack detectada, e porque a validação é o passo com maior risco de falso sucesso e só é necessária no fim da Fase 3 (ADR-07).

### Catálogo: os 20 anti-patterns, severidade e por quê

O catálogo nasceu da análise manual (Seção A): cada um dos 41 problemas manuais mapeia para pelo menos uma entrada, e todas as 20 entradas são exercitadas por pelo menos um dos três projetos (tabela de rastreabilidade em [docs/manual-analysis.md](docs/manual-analysis.md)). Distribuição: 6 CRITICAL, 5 HIGH, 5 MEDIUM, 4 LOW. A severidade é **fixa** por entrada (a skill não reclassifica), o que torna os relatórios comparáveis (SPEC RNF-06).

| ID | Anti-pattern | Severidade | Por que entrou (origem na análise manual) |
|---|---|---|---|
| AP-01 | Hardcoded Credentials | CRITICAL | Segredos versionados nos 3 projetos (1.3, 2.1, 3.1) |
| AP-02 | SQL Injection | CRITICAL | Queries concatenadas e endpoint de SQL arbitrário (1.1, 1.2) |
| AP-03 | God Class / God Method | CRITICAL | Arquivo/classe com banco, regras e rotas (1.6, 2.2) |
| AP-04 | Sensitive Data Exposure | CRITICAL | Senha, segredo e cartão em respostas e logs (1.4, 2.3, 3.2) |
| AP-05 | Unprotected Admin/Destructive Endpoint | CRITICAL | Reset, SQL e relatório financeiro abertos (1.2, 2.4) |
| AP-06 | Insecure Password Storage | CRITICAL | Texto puro, "hash" caseiro e MD5 sem sal (1.5, 2.5, 3.3) |
| AP-07 | Business Logic in Controller/Route | HIGH | Regras presas nas rotas do projeto parcialmente organizado (3.4) |
| AP-08 | Global Mutable State | HIGH | Conexão singleton e cache global (1.7, 2.8) |
| AP-09 | Tight Coupling / Missing Dependency Injection | HIGH | App criada no import, efeitos colaterais inline (1.14, 3.5) |
| AP-10 | Missing Transaction / Callback Pyramid | HIGH | Escritas multi-etapa sem rollback, 5 níveis de callback, órfãos (1.9, 2.6, 2.7) |
| AP-11 | Insecure Runtime Configuration | HIGH | `debug=True`, `0.0.0.0`, CORS aberto (1.8, 3.6) |
| AP-12 | N+1 Queries | MEDIUM | Presente nos 3 projetos (1.10, 2.9, 3.7) |
| AP-13 | Missing or Inconsistent Input Validation | MEDIUM | Validação divergente ou ausente, 500 por tipo (1.11, 2.10, 3.11) |
| AP-14 | Generic Error Handling | MEDIUM | `except` genérico, `str(e)` vazado, `err` ignorado (1.12, 2.11, 3.10) |
| AP-15 | Duplicated Code | MEDIUM | "Atrasada" em 6 lugares (3.8) |
| AP-16 | Deprecated API Usage | MEDIUM | Exigido pelo enunciado; `utcnow()` e `Query.get` (3.9) |
| AP-17 | Magic Numbers / Strings | LOW | Faixas, status e prefixos inline (1.13, 2.13, 3.13) |
| AP-18 | Poor Naming | LOW | `u`, `e`, `cc`, `p1..p5` (2.12, 3.14) |
| AP-19 | Unused Imports / Dead Code | LOW | Imports e módulos inteiros sem uso (3.12) |
| AP-20 | Print/Console Logging | LOW | `print` e `console.log` como log (1.14, 3.14) |

O AP-16 (APIs deprecated) traz sinais próprios e pares "obsoleto -> moderno" inline (por exemplo `datetime.utcnow()` -> `datetime.now(timezone.utc)`, `Model.query.get(id)` -> `db.session.get(Model, id)`, `new Buffer()` -> `Buffer.from()`), e consulta `deprecated-apis.md` para a stack detectada. Em projetos sem uso de API obsoleta (Projetos 1 e 2) a skill não força finding: o checklist marca "se aplicável".

O playbook cobre cada anti-pattern com uma transformação: T-01 Extract Configuration to Environment, T-02 Parameterize Queries, T-03 Split God Class into MVC Layers, T-04 Output Serializer with Field Allow-list, T-05 Guard Admin Endpoints by Configuration, T-06 Hash Passwords with Standard Library, T-07 Move Business Rules to Model/Service, T-08 Inject Dependencies via Composition Root, T-09 Wrap Multi-step Writes in Transaction, T-10 Replace N+1 with Join/Eager Loading, T-11 Centralize Input Validation, T-12 Centralized Error Handler and Domain Exceptions, T-13 Replace Deprecated API, T-14 Extract Named Constants, T-15 Rename Internals Keep External Contract, T-16 Structured Logging and Dead Code Removal.

### Como a skill é agnóstica de tecnologia

- **Detecção por manifesto, não por nome de projeto.** `project-analysis.md` deriva a linguagem de `requirements*.txt`/`pyproject.toml` (Python), `package.json` (Node), `go.mod`, `pom.xml`/`build.gradle`, `composer.json`, `Gemfile`, `*.csproj`; o framework vem das dependências declaradas confirmadas pelo import no entry point; a versão, do lockfile, depois do pin, depois da faixa (por isso `Express 4.22.1` no Projeto 2, igual ao `package-lock.json`).
- **Sinais neutros com exemplos por stack.** Cada entrada do catálogo descreve o conceito ("SQL montado por concatenação com valor vindo da requisição") e traz exemplos rotulados em Python e JavaScript, mais referências a outras stacks (Go, JDBC, `application.properties`). Os exemplos são sintéticos (`items`, `orders`, `accounts`).
- **Estrutura-alvo adaptativa.** `mvc-guidelines.md` traz a estrutura canônica para Flask e Express e um mapeamento para outras stacks, e §4 manda adaptar à classificação da Fase 1: `monolith` -> camadas novas em `src/`; `partial-layers` -> evolução incremental, mantendo as camadas coerentes onde estão e criando só o que falta; `layered` -> correções pontuais.
- **Zero menções aos projetos dentro da skill.** O QA buscou nomes de tabelas, rotas e arquivos dos três projetos nos arquivos da skill: 0 ocorrências (os únicos achados são exemplos ilustrativos genéricos, "checkout" e "Flask 3.1.1" como formato). Ver [docs/test-report.md](docs/test-report.md), seção 2.
- **Cópias idênticas por hash.** `scripts/sync-skill.ps1` copia a fonte e confere SHA256 arquivo a arquivo; o resultado foi "Skill identica nas 3 copias (8 arquivos)", e `git diff a6415bb HEAD -- '*/.claude/*'` é vazio (a skill não mudou durante as refatorações).
- **Sem novas dependências** (ADR-08): hash de senha com `werkzeug.security` (Python) e `node:crypto` (Node). `git diff` dos manifestos e lockfiles entre o original e o resultado é vazio.

### Desafios encontrados e soluções

1. **Bloco PHASE 1 ausente do log no modo `-p`.** No modo não interativo só a última mensagem do modelo aparece no log; como a Fase 1 é impressa antes de chamadas de ferramenta, o bloco sumia. Foi visto na calibração do Projeto 1, na primeira tentativa do Projeto 3 (`stage1-attempt1.log`, descartada e repetida) e nas duas execuções do Projeto 2. Iteração feita: a skill passou a exigir uma **mensagem final única** da Fase 2 contendo, nesta ordem, o bloco PHASE 1, o relatório e a pergunta (`SKILL.md`, Fase 2, passo 8). Nos Projetos 1 e 3 o bloco passou a sair no `stage1.log`. No Projeto 2 o modelo ainda omitiu o bloco na etapa 1 oficial (capturada com `--output-format stream-json --verbose`); o bloco foi obtido numa execução separada e somente leitura (`--permission-mode plan --no-session-persistence`, para não afetar o `--continue`), registrada em `docs/evidence/project-2/stage1-phase1-only.log`. A skill não foi editada depois disso (observação O-1 do QA).
2. **Git Bash converte `/refactor-arch` em caminho.** No Git Bash (MSYS) o argumento vira `C:/Program Files/Git/refactor-arch` e a skill não é invocada de forma limpa (visível na primeira linha de `docs/evidence/project-2/stage1.log`). Solução: disparar a etapa 1 pelo PowerShell, ou prefixar `MSYS_NO_PATHCONV=1`.
3. **Logs em UTF-16.** O `Tee-Object` do PowerShell 5.1 gravou `stage1.log` e `stage2.log` dos Projetos 1 e 3 em UTF-16LE com CRLF, e a saída nativa foi decodificada pela code page do console (acentos corrompidos). Solução: definir `[Console]::OutputEncoding` e `$OutputEncoding` como UTF-8 e gravar com `Out-File -Encoding utf8`; o `scripts/extract-report.ps1` detecta UTF-8 e UTF-16 pelo BOM, remove sequências ANSI e grava o relatório em UTF-8 sem BOM.
4. **Responder "y" em modo não interativo.** Foi resolvido com `claude -p --continue "y"` no **mesmo diretório** do projeto, sem `--no-session-persistence` (que impediria o `--continue`). Sem stdin redirecionado o `claude -p` espera 3 s e avisa "no stdin data received"; por isso se passa `$null |` (PowerShell) ou `< /dev/null` (Bash).
5. **Rotas admin inseguras x "endpoints continuam respondendo" (ADR-03).** Corrigir a vulnerabilidade e manter o contrato conflitam em `POST /admin/query`, `POST /admin/reset-db` e `GET /api/admin/financial-report`. Decisão: a rota continua registrada, protegida por um guard configurável. Sem `ADMIN_TOKEN` configurado, ou com o header `X-Admin-Token` diferente (comparação em tempo constante), a resposta é `403`; com token válido, o comportamento original é mantido. Nada foi removido, e o SQL arbitrário com token continua listado como risco residual.
6. **Captura "antes" só após o "y".** Subir a aplicação original para registrar a baseline cria `*.db` e `__pycache__`, o que violaria a regra de Fases 1 e 2 somente leitura. Solução: o passo 3.0 da Fase 3 captura a baseline do código original depois do "y" e antes da primeira edição (`phase3-validation.md`). Em paralelo, uma baseline **externa independente** (`scripts/smoke.ps1`, capturada antes de qualquer execução da skill) serve de critério oficial de aceite.

---

## C) Resultados

### Resumo dos relatórios de auditoria

Relatórios gerados pela skill (Fase 2) e extraídos sem edição com `scripts/extract-report.ps1`: [reports/audit-project-1.md](reports/audit-project-1.md), [reports/audit-project-2.md](reports/audit-project-2.md), [reports/audit-project-3.md](reports/audit-project-3.md). Em cada um, o `Total` é igual ao número de blocos `### [` (conferido pelo QA).

| Projeto | Arquivos / LOC | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| 1 - `code-smells-project` | 4 / ~780 | 11 | 9 | 7 | 6 | **33** |
| 2 - `ecommerce-api-legacy` | 3 / ~180 | 6 | 6 | 3 | 6 | **21** |
| 3 - `task-manager-api` | 15 / ~1158 | 5 | 6 | 13 | 7 | **31** |
| Total | | 22 | 21 | 23 | 19 | **85** |

Cobertura da análise manual: todos os 14 problemas do Projeto 1 e os 14 do Projeto 3 reaparecem nos relatórios (mesmo arquivo e anti-pattern equivalente); no Projeto 2, 12 dos 13 (o 2.7 só parcialmente, coberto por AP-10 em `AppManager.js:37-77`). Os critérios de aceite exigiam >= 5 findings e >= 1 CRITICAL/HIGH em cada projeto, atendidos com folga.

Fase 1 detectada pela skill (blocos `PHASE 1` em `docs/evidence/project-N/stage1.log`; Projeto 2 em `stage1-phase1-only.log`):

| Campo | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Language | Python | JavaScript (Node.js) | Python |
| Framework | Flask 3.1.1 | Express 4.22.1 | Flask 3.0.0 |
| Domain | E-commerce: produtos, usuários, pedidos, itens de pedido | LMS com checkout e matrícula | Gerenciamento de tarefas: tasks, users, categories |
| Architecture | Monolítica | Monolítica (God Class) | Parcialmente em camadas |
| Source files | 4 | 3 | 15 |
| DB tables | produtos, usuarios, pedidos, itens_pedido | users, courses, enrollments, payments, audit_logs | tasks, users, categories |
| Endpoints | 19 | 3 | 22 |

### Comparação antes/depois da estrutura

**Projeto 1 - `code-smells-project`** (monolito -> `src/` completo). Antes: 4 arquivos, ~780 linhas. Depois: 34 arquivos `.py` em `src/`, 1057 linhas.

```
ANTES                              DEPOIS
code-smells-project/               code-smells-project/
├── README.md                      ├── .env.example
├── app.py                         ├── README.md
├── controllers.py                 ├── app.py                  (entry point fino: create_app + app.run)
├── database.py                    ├── requirements.txt        (inalterado)
├── models.py                      └── src/
└── requirements.txt                   ├── app.py              (composition root: create_app)
                                       ├── config/             settings.py
                                       ├── models/             database.py, seguranca.py, constants.py,
                                       │                       produto_model.py, usuario_model.py,
                                       │                       pedido_model.py, admin_model.py
                                       ├── services/           pedido_service.py, notificacao_service.py
                                       ├── controllers/        produto_, usuario_, pedido_,
                                       │                       relatorio_, sistema_controller.py
                                       ├── routes/             produto_, usuario_, pedido_,
                                       │                       relatorio_, sistema_routes.py
                                       ├── middlewares/        error_handler.py, auth.py
                                       └── utils/              errors.py, validators.py, logger.py
```

**Projeto 2 - `ecommerce-api-legacy`** (Express -> `src/` MVC com services e middlewares). Antes: 3 arquivos, 180 linhas. Depois: 26 arquivos `.js`, 560 linhas.

```
ANTES                              DEPOIS
ecommerce-api-legacy/              ecommerce-api-legacy/
├── README.md                      ├── .env.example
├── api.http                       ├── api.http, README.md, package.json, package-lock.json (inalterados)
├── package.json                   └── src/
├── package-lock.json                  ├── app.js              (entry point + composition root: createApp())
└── src/                               ├── config/index.js     (único leitor de process.env)
    ├── app.js          (14 l.)        ├── models/             database.js, constants.js, passwordHasher.js,
    ├── AppManager.js   (141 l.)       │                       userModel, courseModel, enrollmentModel,
    └── utils.js        (25 l.)        │                       paymentModel, auditLogModel, reportModel
                                       ├── services/           checkoutService.js, paymentGateway.js, userService.js
                                       ├── controllers/        checkout-, admin-, userController.js
                                       ├── routes/             checkout-, admin-, userRoutes.js
                                       ├── middlewares/        adminGuard.js, asyncHandler.js, errorHandler.js
                                       └── utils/              errors.js, logger.js, validators.js
```

**Projeto 3 - `task-manager-api`** (Flask parcialmente organizado -> evolução incremental). Antes: 15 arquivos `.py`. Depois: 34 arquivos `.py`, 1331 linhas. As pastas `models/`, `routes/`, `services/`, `utils/` foram mantidas na raiz; foram criadas `config/`, `controllers/` e `middlewares/`.

```
ANTES                              DEPOIS
task-manager-api/                  task-manager-api/
├── README.md                      ├── .env.example                             (novo)
├── app.py                         ├── app.py        (entry point + composition root: create_app)
├── database.py                    ├── database.py   (db + commit com rollback)
├── requirements.txt               ├── requirements.txt, seed.py                (mesmo comando)
├── seed.py                        ├── config/       settings.py                (novo)
├── models/    category, task,     ├── controllers/  task_, user_, category_,
│              user                │                 report_, health_controller (novo)
├── routes/    report_, task_,     ├── middlewares/  error_handler.py           (novo)
│              user_routes         ├── models/       category, task, user       (mantido)
├── services/  notification_       ├── routes/       task_, user_, report_routes (mantidos);
│              service             │                 category_routes, health_routes (novos)
└── utils/     helpers.py          ├── services/     task_, user_, category_, report_service
                                   │                 (notification_service removido)
                                   └── utils/        constants, errors, validators, numbers, time
                                                     (helpers.py removido)
```

Detalhes e listagens completas nos checklists de cada projeto: [project-1](docs/evidence/project-1/checklist.md), [project-2](docs/evidence/project-2/checklist.md), [project-3](docs/evidence/project-3/checklist.md).

### Checklist de validação (enunciado)

Fonte: `docs/evidence/project-N/checklist.md` (executor) e seção 7 de [docs/test-report.md](docs/test-report.md) (QA, que reexecutou tudo e não encontrou discrepâncias).

#### Projeto 1 - code-smells-project

Fase 1 - Análise
- [x] Linguagem detectada corretamente (`Python`)
- [x] Framework detectado corretamente (`Flask 3.1.1`)
- [x] Domínio da aplicação descrito corretamente (e-commerce: produtos, usuários, pedidos)
- [x] Número de arquivos analisados condiz com a realidade (4 = 4 `.py`; ~780 LOC conferido)

Fase 2 - Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos (33/33 com `File:`; amostras conferidas no original)
- [x] Findings ordenados por severidade (11 CRITICAL, 9 HIGH, 7 MEDIUM, 6 LOW)
- [x] Mínimo de 5 findings identificados (33)
- [x] Detecção de APIs deprecated incluída (se aplicável): não aplicável, nenhuma ocorrência no original
- [x] Skill pausa e pede confirmação antes da Fase 3 (`stage1-git-status.txt` vazio; pergunta literal no fim de `stage1.log`)

Fase 3 - Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config, sem hardcoded (`src/config/settings.py`, `.env.example`)
- [x] Models criados para abstrair dados (`src/models/`)
- [x] Views/Routes separadas para visualização ou roteamento (`src/routes/`)
- [x] Controllers concentram o fluxo da aplicação (`src/controllers/`)
- [x] Error handling centralizado (`src/middlewares/error_handler.py`)
- [x] Entry point claro (`app.py` -> `create_app()` em `src/app.py`)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (29/29 sem 5xx/404; com token idêntico à baseline; divergências aceitas na tabela abaixo)

#### Projeto 2 - ecommerce-api-legacy

Fase 1 - Análise
- [x] Linguagem detectada corretamente (`JavaScript (Node.js)`)
- [x] Framework detectado corretamente (`Express 4.22.1`, igual ao `package-lock.json`)
- [x] Domínio da aplicação descrito corretamente (LMS com checkout e matrícula)
- [x] Número de arquivos analisados condiz com a realidade (3 = 3 `.js`; ~180 LOC conferido)
- Ressalva (O-1 do QA): o bloco `PHASE 1` não consta no `stage1.log` oficial deste projeto; ele vem de uma execução separada, somente leitura, em `docs/evidence/project-2/stage1-phase1-only.log` (ver desafio 1 na Seção B). Os valores batem com a realidade e com o relatório (`Stack`, `Files` em `reports/audit-project-2.md`).

Fase 2 - Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos (21/21; amostras conferidas no original)
- [x] Findings ordenados por severidade (6 CRITICAL, 6 HIGH, 3 MEDIUM, 6 LOW)
- [x] Mínimo de 5 findings identificados (21)
- [x] Detecção de APIs deprecated incluída (se aplicável): não aplicável; a skill varreu a tabela Node/Express e declarou que nada foi encontrado
- [x] Skill pausa e pede confirmação antes da Fase 3 (`stage1-git-status.txt` vazio; pergunta literal como última linha do relatório)

Fase 3 - Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config, sem hardcoded (`src/config/index.js`; ressalva O-4: `DEFAULT_PASSWORD` preservada, ver divergências)
- [x] Models criados para abstrair dados (`src/models/`)
- [x] Views/Routes separadas para visualização ou roteamento (`src/routes/`)
- [x] Controllers concentram o fluxo da aplicação (`src/controllers/`, regras em `src/services/`)
- [x] Error handling centralizado (`src/middlewares/errorHandler.js`)
- [x] Entry point claro (`src/app.js`, `npm start` inalterado)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (6/6; com token idêntico à baseline)

#### Projeto 3 - task-manager-api

Fase 1 - Análise
- [x] Linguagem detectada corretamente (`Python`)
- [x] Framework detectado corretamente (`Flask 3.0.0`)
- [x] Domínio da aplicação descrito corretamente (Task Manager: tasks, users, categories, relatórios)
- [x] Número de arquivos analisados condiz com a realidade (15 = 15 `.py` incluindo `__init__.py`; ~1158 LOC conferido)

Fase 2 - Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos (31/31; amostras conferidas no original)
- [x] Findings ordenados por severidade (5 CRITICAL, 6 HIGH, 13 MEDIUM, 7 LOW)
- [x] Mínimo de 5 findings identificados (31)
- [x] Detecção de APIs deprecated incluída (2 findings `[MEDIUM] Deprecated API Usage`: `datetime.utcnow` e `Query.get`)
- [x] Skill pausa e pede confirmação antes da Fase 3 (`stage1-git-status.txt` vazio)

Fase 3 - Refatoração
- [x] Estrutura de diretórios segue padrão MVC (evolução incremental)
- [x] Configuração extraída para módulo de config, sem hardcoded (`config/settings.py`, `.env.example`)
- [x] Models criados para abstrair dados (`models/`)
- [x] Views/Routes separadas para visualização ou roteamento (`routes/`)
- [x] Controllers concentram o fluxo da aplicação (`controllers/`, regras em `services/`)
- [x] Error handling centralizado (`middlewares/error_handler.py`)
- [x] Entry point claro (`app.py` com `create_app()`)
- [x] Aplicação inicia sem erros (`python seed.py` + `python app.py`)
- [x] Endpoints originais respondem corretamente (35/35 idênticos à baseline)

### Aplicações rodando após a refatoração (logs)

Trechos reais dos logs de boot gerados por `scripts/smoke.ps1`, que sobe a aplicação com o **comando de boot original** e chama todos os endpoints.

**Projeto 1** - `docs/evidence/project-1/baseline-after-boot.log` (antes, em `baseline-before-boot.log`, aparecia `Debug mode: on`, `Running on all addresses (0.0.0.0)` e `Debugger PIN`):

```
== stdout ==
 * Serving Flask app 'src.app'
 * Debug mode: off
== stderr ==
 * Running on http://127.0.0.1:5000
2026-10-24 13:37:56,013 INFO werkzeug: 127.0.0.1 - - [24/Oct/2026 13:37:56] "GET /produtos HTTP/1.1" 200 -
2026-10-24 13:38:00,472 INFO werkzeug: 127.0.0.1 - - [24/Oct/2026 13:38:00] "POST /pedidos HTTP/1.1" 201 -
2026-10-24 13:38:02,870 INFO werkzeug: 127.0.0.1 - - [24/Oct/2026 13:38:02] "POST /admin/query HTTP/1.1" 200 -
2026-10-24 13:38:03,406 WARNING src.controllers.sistema_controller: banco de dados resetado por administrador
```

**Projeto 2** - `docs/evidence/project-2/baseline-after-boot.log` (stderr vazio; o cartão aparece mascarado e a chave do gateway não é mais logada):

```
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node src/app.js

2026-10-24T16:33:18.998Z INFO LMS rodando na porta 3000...
2026-10-24T16:33:20.637Z INFO payment PAID amount=497 card=****4444 gateway=not configured
2026-10-24T16:33:20.701Z INFO checkout completed enrollment=2 course=Docker
2026-10-24T16:33:20.744Z INFO payment DENIED amount=997 card=****4444 gateway=not configured
```

**Projeto 3** - `docs/evidence/project-3/baseline-after-boot.log`:

```
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
2026-10-24 14:02:27,059 INFO werkzeug: 127.0.0.1 - - [24/Oct/2026 14:02:27] "GET /tasks HTTP/1.1" 200 -
2026-10-24 14:02:32,942 INFO werkzeug: 127.0.0.1 - - [24/Oct/2026 14:02:32] "POST /tasks HTTP/1.1" 201 -
2026-10-24 14:02:36,677 INFO werkzeug: 127.0.0.1 - - [24/Oct/2026 14:02:36] "DELETE /categories/9999 HTTP/1.1" 404 -
```

O boot de P1 e P3 não tem `Traceback` nem `Error` (a única linha `WARNING` do Projeto 3 e a do Projeto 1 em `stderr` são o aviso padrão do servidor de desenvolvimento do Werkzeug). O `seed.py` do Projeto 3 passa com `python -W error::DeprecationWarning seed.py` (exit 0: 3 usuários, 4 categorias, 10 tasks), o que o original não fazia por causa de `utcnow()` (`docs/evidence/project-3/seed-after.log`).

**Status por endpoint, antes e depois** (`baseline-before.txt` vs `baseline-after.txt` em `docs/evidence/project-N/`; a coluna "depois" é a execução com `-AdminToken`, a "sem token" é a execução sem ele):

Projeto 2 (6 requisições):

| Requisição | Antes | Depois (sem token) | Depois (com token) |
|---|---|---|---|
| `POST /api/checkout` (novo usuário, cartão aprovado) | 200 | 200 | 200 |
| `POST /api/checkout` (cartão recusado) | 400 | 400 | 400 |
| `POST /api/checkout` (corpo vazio) | 400 | 400 | 400 |
| `POST /api/checkout` (curso inexistente) | 404 | 404 | 404 |
| `GET /api/admin/financial-report` | 200 | **403** | 200 |
| `DELETE /api/users/1` | 200 | 200 | 200 |

Projeto 1 (29 requisições): 26 idênticas sem token; as 3 divergentes (`after-notoken.txt`) são as rotas admin; com `-AdminToken`, as 29 linhas são idênticas (`baseline-after.txt`).

| Requisição | Antes | Depois (sem token) | Depois (com token) |
|---|---|---|---|
| `POST /admin/query` (SQL válido) | 200 | **403** | 200 |
| `POST /admin/query` (sem SQL) | 400 | **403** | 400 |
| `POST /admin/reset-db` | 200 | **403** | 200 |

Projeto 3 (35 requisições, sem rotas admin): `baseline-after.txt` é idêntico a `baseline-before.txt` (22 combinações método+path cobertas, incluindo casos de erro como `GET /tasks/9999 -> 404`, `POST /login -> 401`, `POST /users -> 400`).

### Divergências antes/depois e justificativa

A refatoração preserva paths, métodos, status, chaves de resposta e nomes de campos de request. As únicas mudanças permitidas são a lista fechada do ADR-11 (correção de segurança ou de bug que gerava 5xx) e foram todas registradas pela skill no bloco `PHASE 3` e conferidas pelo QA (`docs/test-report.md`, seção 8; nenhuma regressão encontrada).

| Divergência | Projeto | Justificativa |
|---|---|---|
| `POST /admin/query` (200 e 400) e `POST /admin/reset-db` (200) respondem **403** sem `X-Admin-Token`; com token válido, igual ao original | 1 | Guard admin (ADR-03): SQL arbitrário e reset sem autenticação são vulnerabilidades CRITICAL |
| `GET /api/admin/financial-report` responde **403** sem token; com token, status e corpo iguais ao original | 2 | Guard admin (ADR-03): relatório financeiro com PII |
| `PUT /produtos/<id>` agora aplica as regras do POST: nome vazio/curto ou categoria inválida passam de 200 para **400**; `preco:"abc"` ou corpo vazio, de 500 para 400 | 1 | Corrige a validação inconsistente (problema manual 1.11). Fora da lista fechada do ADR-11, mas **decisão aceita** pelo orquestrador. O smoke não exercita esse caminho (as requisições dele são válidas); foi verificado manualmente pelo QA |
| Respostas sem campos sensíveis: `GET /health` sem `secret_key`, `db_path`, `debug`, `ambiente`; `GET /usuarios` e `/usuarios/<id>` sem `senha` | 1 | Correção de segurança (ADR-11a); status inalterado |
| `password` removido de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`; login com a senha legada continua 200 | 3 | Correção de segurança (ADR-11a); o hash legado MD5 é aceito e regravado com hash novo (ADR-12) |
| Entradas inválidas que davam 500 passam a 400 (ex.: busca com `preco_min=abc`, `POST /produtos` com preço string; `priority` string no P3; `card` numérico no P2, que antes derrubava o processo com `TypeError`) | 1, 2, 3 | Correção de bug que gerava 5xx (ADR-11d) |
| Erros 500 não vazam mais `str(e)`; devolvem mensagem genérica | 1 | ADR-11c; o detalhe vai para o log |
| `debug` desligado por padrão e `HOST=127.0.0.1` por padrão (antes `debug=True` e `0.0.0.0`); a porta (5000) é mantida | 1, 3 | Endurecimento (finding AP-11), configurável por `.env.example`. Para expor na rede: `HOST=0.0.0.0`. No Projeto 2 o `HOST` vazio mantém o comportamento original (todas as interfaces) |
| `DELETE /api/users/1` agora remove matrículas e pagamentos do usuário na mesma transação; o relatório financeiro deixa de listar órfãos. O texto da resposta foi mantido por ser contrato e ficou desatualizado ("ficaram sujos") | 2 | Corrige o finding de órfãos (AP-10); chaves, status e content-type iguais |
| JSON compacto em vez de indentado | 1, 3 | Efeito de `DEBUG=false`; mesmas chaves e semântica |

Riscos residuais declarados (não escondidos): `POST /admin/query` com token válido continua executando SQL arbitrário (risco aceito pelo ADR-03); `DEFAULT_PASSWORD = '123456'` em `ecommerce-api-legacy/src/models/constants.js:12` é aplicada quando o checkout não envia `pwd` (comportamento original preservado, mas agora gravada com hash); os seeds de demonstração do P1 e do P3 contêm senhas em claro antes do hash; `POST /pedidos` com `usuario_id` inexistente ainda devolve 201 no P1 (preservado do original).

### Resumo do QA

O QA ([docs/test-report.md](docs/test-report.md)) reexecutou tudo do zero sobre o commit `38879fe` e verificou os critérios CA-01 a CA-18: **15 PASS, 1 FAIL e 2 que dependiam deste README.**

- **FAIL (corrigido):** CA-18, severidade baixa. `docs/CHALLENGE.md` divergia do README original em uma palavra de redação ("separação de camadas" no lugar de "organização") e na quebra de linha final. O arquivo hoje usa "organização", como no original.
- **Dependentes deste README:** CA-05 (Seção A com >= 5 problemas por projeto, >= 1 CRITICAL/HIGH, >= 2 MEDIUM, >= 2 LOW, `arquivo:linha` e justificativa) e CA-17 (Seções A a D, checklist dos 3 projetos e logs), atendidos pelas seções acima.
- **Conferência de linhas:** 21 amostras de `arquivo:linha` contra o código original (>= 6 por projeto), todas corretas.
- **Contrato:** comparação de corpos original x refatorado: diferenças só as listadas em "Divergências".
- **Git:** um commit de refatoração por projeto, cada um tocando só o seu projeto; sem `.db`, `.venv`, `node_modules` ou `.env` versionados.
- **Observações abertas do QA:** O-1 (bloco PHASE 1 do Projeto 2, descrito acima), O-4 (`DEFAULT_PASSWORD` e seeds), O-5 (o smoke não cobre caminhos de validação inválidos) e O-6 (o template resumido no `SKILL.md` omite a linha opcional `Other occurrences:`, sem impacto nos relatórios).

### Como a skill se comportou em cada stack

- **Projeto 1 - monolito Flask:** classificado como `monolith` -> estrutura `src/` completa (config, models, services, controllers, routes, middlewares, utils). O `app.py` da raiz virou entry point fino e o comando `python app.py` ficou igual. O God Module `models.py` foi dividido por domínio, as queries foram parametrizadas e o checkout passou a ser transacional em `src/services/pedido_service.py`. Foi o relatório mais longo (33 findings), porque o mesmo anti-pattern aparece em vários arquivos (agrupamento 1 finding = 1 anti-pattern x 1 arquivo).
- **Projeto 2 - Express:** classificado como `monolith` -> `src/` MVC com services e middlewares. A skill adaptou os mesmos conceitos ao ecossistema Node: wrapper de Promise e transação sobre `sqlite3` com callbacks, `asyncHandler` e `errorHandler` do Express, `node:crypto` (scrypt com sal) para senhas, `createApp()` como composition root com `listen` apenas se `require.main === module`. `npm start` (`node src/app.js`) e `package.json` ficaram intactos. A validação cobriu 9 requisições (inclusive o `card` numérico que derrubava o processo).
- **Projeto 3 - Flask parcialmente organizado:** classificado como `partial-layers` -> **evolução incremental**: manteve `models/`, `routes/`, `services/` e `utils/` onde já estavam e criou `config/`, `controllers/` e `middlewares/`. As rotas passaram a delegar a controllers, a regra de negócio foi para services/models, o cálculo de "atrasada" duplicado passou a usar um único método, `app.py` ganhou `create_app()` com `app = create_app()` no módulo para que `seed.py` continue com `from app import app, db`, e o `notification_service.py` morto foi removido. Os findings de APIs deprecated só apareceram aqui (2), como esperado pela análise manual.
- **Em comum:** a skill descobriu comando de boot, porta, seed e rotas lendo o código, sem nenhuma informação específica dos projetos; nos três a validação final mostrou boot limpo e nenhum endpoint com 5xx ou 404 de rota.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code 2.1.310** instalado e autenticado (`claude --version`). Apenas esta versão foi testada.
- **Python 3.12** (Projetos 1 e 3) e **Node.js 22** com npm (Projeto 2).
- **Windows 11 com PowerShell 5.1** (ambiente em que tudo foi validado) ou equivalente. Os scripts de `scripts/` são PowerShell e usam `taskkill.exe` e `curl.exe`: são Windows-only. Em Linux/macOS os comandos dos projetos (venv, `npm`, `curl`) funcionam igual e as alternativas manuais estão indicadas abaixo.
- Executar os projetos 1 e 3 **um de cada vez**: ambos usam a porta 5000.

### Preparar o ambiente de cada projeto

```powershell
# Projeto 1 - code-smells-project (Flask, porta 5000)
cd code-smells-project
py -3.12 -m venv .venv                      # Linux/Mac: python3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1                # Linux/Mac: source .venv/bin/activate
python -m pip install -r requirements.txt
cd ..

# Projeto 3 - task-manager-api (Flask + SQLAlchemy, porta 5000)
cd task-manager-api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd ..

# Projeto 2 - ecommerce-api-legacy (Express, porta 3000)
cd ecommerce-api-legacy
npm install
cd ..
```

`.venv/`, `node_modules/`, `*.db`, `instance/` e `.env` estão no `.gitignore`. Os scripts `smoke-project-1.ps1` e `smoke-project-3.ps1` sobem a aplicação com o interpretador do `.venv` do projeto, então crie o venv antes de usá-los.

### Executar a skill em cada projeto

A skill já está em `.claude/skills/refactor-arch/` dos três projetos. Para refazer uma execução do zero, restaure o código original do projeto antes (`scripts\reset-project.ps1 -Project N` faz `git checkout` e `git clean` preservando `.claude/`, `.venv` e `node_modules`).

**Forma interativa** (a pausa é humana):

```powershell
cd code-smells-project            # ou ecommerce-api-legacy, ou task-manager-api
claude                            # abre a sessão (aceite o diálogo de confiança do diretório)
```

Dentro da sessão, digite `/refactor-arch`. A skill imprime o bloco `PHASE 1`, o `ARCHITECTURE AUDIT REPORT` e para em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Revise o relatório e responda `y` para iniciar a Fase 3 (qualquer outra resposta cancela sem modificar nada). O formato `claude "/refactor-arch"` do enunciado também funciona; **no Git Bash** use `MSYS_NO_PATHCONV=1 claude "/refactor-arch"` para o `/refactor-arch` não ser convertido em caminho.

**Forma não interativa em 2 etapas** (usada nas execuções deste repositório; detalhes em [docs/evidence/claude-cli-flags.md](docs/evidence/claude-cli-flags.md)). Exemplo para o Projeto 1, em PowerShell a partir da raiz do repositório (troque `$N` e `$Proj` para os outros: `2`/`ecommerce-api-legacy`, `3`/`task-manager-api`):

```powershell
$Root = (Get-Location).Path
$N = 1; $Proj = 'code-smells-project'
[Console]::OutputEncoding = [Text.Encoding]::UTF8      # evita logs corrompidos/UTF-16
$OutputEncoding = [Text.Encoding]::UTF8
New-Item -ItemType Directory -Force docs\evidence\project-$N | Out-Null
Set-Location $Root\$Proj

# Etapa 1 - Fases 1 e 2 (somente leitura); termina na pergunta [y/n]
$null | claude -p "/refactor-arch" --permission-mode plan 2>&1 |
  Out-File -FilePath $Root\docs\evidence\project-$N\stage1.log -Encoding utf8

# Evidência da pausa: deve ficar vazio
git status --porcelain -- . | Tee-Object -FilePath $Root\docs\evidence\project-$N\stage1-git-status.txt

# Salvar o relatório (veja a próxima subseção), revisar e então:

# Etapa 2 - resposta "y" na MESMA sessão/diretório -> Fase 3
$null | claude -p --continue "y" --permission-mode acceptEdits `
  --allowedTools "Bash Read Write Edit Glob Grep" 2>&1 |
  Out-File -FilePath $Root\docs\evidence\project-$N\stage2.log -Encoding utf8
Set-Location $Root
```

Em Bash (Linux/Mac), o equivalente é `claude -p "/refactor-arch" --permission-mode plan < /dev/null | tee stage1.log`, seguido de `claude -p --continue "y" --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep" < /dev/null | tee stage2.log`. Não use `--no-session-persistence` (impede o `--continue`) e use `-p` somente em diretórios confiáveis, pois o diálogo de confiança é ignorado.

### Copiar a skill para outro projeto

Dentro deste repositório, `scripts\sync-skill.ps1` copia a skill-fonte (`code-smells-project`) para `ecommerce-api-legacy` e `task-manager-api`, recriando as cópias do zero e conferindo SHA256 arquivo a arquivo:

```powershell
.\scripts\sync-skill.ps1               # copia e confere
.\scripts\sync-skill.ps1 -CheckOnly    # só confere (esperado: "Skill identica nas 3 copias (8 arquivos).")
```

Para um projeto qualquer fora deste repositório, copie a pasta inteira da skill:

```powershell
Copy-Item -Recurse code-smells-project\.claude\skills\refactor-arch <outro-projeto>\.claude\skills\   # Linux/Mac: cp -r
```

Depois rode `claude` dentro de `<outro-projeto>` e invoque `/refactor-arch`. Para conferir a identidade sem o script: `diff -r code-smells-project/.claude/skills/refactor-arch <outro-projeto>/.claude/skills/refactor-arch` (sem saída = idêntico).

### Salvar o relatório de auditoria

`scripts\extract-report.ps1` recorta do log o trecho do `ARCHITECTURE AUDIT REPORT` até a pergunta final, remove sequências ANSI e grava em UTF-8 sem BOM, conferindo `Total` x número de blocos `### [`:

```powershell
.\scripts\extract-report.ps1 -Log docs\evidence\project-1\stage1.log -Out reports\audit-project-1.md
```

Em uma execução interativa, salve o transcript num arquivo e passe-o em `-Log`.

### Validar que a refatoração funcionou

**1. Subir a aplicação com o comando de boot original** (inalterado pela refatoração):

```powershell
# Projeto 1 (porta 5000) - com o venv ativo
cd code-smells-project;  python app.py
# Projeto 2 (porta 3000)
cd ecommerce-api-legacy; npm start
# Projeto 3 (porta 5000) - popular o banco antes, com o venv ativo
cd task-manager-api;     python seed.py; python app.py
```

Esperado: o log mostra `Running on http://127.0.0.1:5000` e `Debug mode: off` (Flask) ou `INFO LMS rodando na porta 3000...` (Express), sem `Traceback`. Pare com Ctrl+C.

**2. Smoke test completo com o script** (sobe a app, chama todos os endpoints, grava `MÉTODO path -> status`, derruba o processo, apaga `*.db`; em Windows, a partir da raiz do repositório):

```powershell
.\scripts\smoke-project-1.ps1 -Out $env:TEMP\p1-sem-token.txt                          # rotas admin devem dar 403
.\scripts\smoke-project-1.ps1 -AdminToken s3cret -Out $env:TEMP\p1-com-token.txt      # tudo igual à baseline
.\scripts\smoke-project-2.ps1 -Out $env:TEMP\p2-sem-token.txt
.\scripts\smoke-project-2.ps1 -AdminToken s3cret -Out $env:TEMP\p2-com-token.txt
.\scripts\smoke-project-3.ps1 -Out $env:TEMP\p3.txt                                    # P3 não tem rotas admin
```

Com `-AdminToken`, o script exporta `ADMIN_TOKEN` para a aplicação e envia `X-Admin-Token` nas rotas admin. O script também grava `<Out sem extensão>-boot.log` com o stdout/stderr da aplicação.

**3. Comparar com a baseline do código original** (`docs/evidence/project-N/baseline-before.txt`):

```powershell
fc docs\evidence\project-1\baseline-before.txt $env:TEMP\p1-com-token.txt     # Linux/Mac: diff
```

Resultado esperado: com token (P1 e P2) e no P3, **só a linha de cabeçalho pode diferir** (`admin_token=unset` x `admin_token=set`); sem token, as únicas diferenças são as rotas admin com `403` (3 linhas no P1, 1 linha no P2), como na seção de resultados. As saídas de referência já estão no repositório: `baseline-after.txt`, `after-notoken.txt` (P1) e `baseline-after-token.txt` (P2) em `docs/evidence/project-N/`.

**4. Verificação manual de um endpoint admin** (em outro terminal, com a app iniciada com a variável):

```powershell
$env:ADMIN_TOKEN = 's3cret'; cd ecommerce-api-legacy; npm start        # Linux/Mac: ADMIN_TOKEN=s3cret npm start
curl.exe -s -o NUL -w "%{http_code}`n" http://localhost:3000/api/admin/financial-report                             # 403
curl.exe -s -o NUL -w "%{http_code}`n" -H "X-Admin-Token: s3cret" http://localhost:3000/api/admin/financial-report  # 200
```

(Em Bash troque `-o NUL` por `-o /dev/null` e a quebra de linha do `-w` por `\n`.)

**5. Projeto 3 e `seed.py`.** O banco `instance/tasks.db` é populado por `python seed.py`, e os endpoints do smoke e da baseline assumem esses dados (usuários 1-3, categorias 1-4, tasks 1-10). O `seed.py` mantém o mesmo comando e deve terminar com "Seed concluído com sucesso!" (3 usuários, 4 categorias, 10 tasks). Credenciais de demonstração: `joao@email.com` / `1234`.

### Variáveis de ambiente (`.env.example` de cada projeto)

Todas são opcionais: sem `.env` e sem variáveis exportadas, a aplicação sobe com os defaults de desenvolvimento. No Projeto 3 o `.env` é carregado automaticamente via `python-dotenv` (`Copy-Item .env.example .env`); nos Projetos 1 e 2 não há biblioteca de `.env`, então **exporte** as variáveis no ambiente do processo (`$env:NOME='valor'` no PowerShell, `export NOME=valor` no Bash).

**Projeto 1 - `code-smells-project/.env.example`**

| Variável | Descrição | Default | Obrigatória |
|---|---|---|---|
| `PORT` | Porta HTTP | `5000` | Não |
| `HOST` | Interface de escuta (`0.0.0.0` para expor na rede) | `127.0.0.1` | Não |
| `DEBUG` | Modo debug do Flask (nunca `true` em produção) | `false` | Não |
| `DB_PATH` | Arquivo SQLite | `loja.db` | Não |
| `SECRET_KEY` | Chave de sessão; vazio = gerada a cada boot | vazio | Não |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula; `*` mantém o comportamento original | `*` | Não |
| `ADMIN_TOKEN` | Token das rotas `/admin/*`; vazio = respondem 403; enviar em `X-Admin-Token` | vazio | Só para usar as rotas admin |
| `LOG_LEVEL` | Nível do `logging` | `INFO` | Não |

**Projeto 2 - `ecommerce-api-legacy/.env.example`**

| Variável | Descrição | Default | Obrigatória |
|---|---|---|---|
| `PORT` | Porta HTTP | `3000` | Não |
| `HOST` | Interface; vazio = todas as interfaces (comportamento original) | vazio | Não |
| `DB_PATH` | Caminho do SQLite; `:memory:` recria schema e seed a cada boot | `:memory:` | Não |
| `PAYMENT_GATEWAY_KEY` | Chave do gateway de pagamento (nunca versionar o valor real) | vazio | Não |
| `ADMIN_TOKEN` | Token das rotas `/api/admin/*`; vazio = respondem 403; enviar em `X-Admin-Token` | vazio | Só para usar as rotas admin |
| `LOG_LEVEL` | `debug`, `info`, `warn` ou `error` | `info` | Não |

**Projeto 3 - `task-manager-api/.env.example`**

| Variável | Descrição | Default | Obrigatória |
|---|---|---|---|
| `SECRET_KEY` | Chave de sessão do Flask; vazio = gerada a cada boot | vazio | Não |
| `DEBUG` | Modo debug (nunca `true` em produção) | `false` | Não |
| `HOST` | Interface de escuta | `127.0.0.1` | Não |
| `PORT` | Porta HTTP | `5000` | Não |
| `DATABASE_URI` | URI SQLAlchemy; URIs SQLite relativas ficam em `instance/` | `sqlite:///tasks.db` | Não |
| `CORS_ORIGINS` | `*` ou lista separada por vírgula | `*` | Não |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING` ou `ERROR` | `INFO` | Não |

Para mais detalhes de requisitos e decisões, consulte [SPEC.md](SPEC.md) e [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
