# Análise manual dos 3 projetos

> Insumo da Seção A do `README.md` (RF-01 a RF-03, CA-05). Feita sobre o código original (commit `6d1ce62`) **antes** da escrita da skill; cada linha citada foi conferida no código.
> Severidades conforme a escala do enunciado (SPEC §5.1). A coluna "AP" mapeia cada problema para a entrada do catálogo da skill (`.claude/skills/refactor-arch/anti-patterns-catalog.md`), garantindo a rastreabilidade exigida em RF-03.
> Caminhos relativos à raiz de cada projeto.

## Resumo

| Projeto | Stack | Problemas | CRITICAL | HIGH | MEDIUM | LOW |
|---|---|---|---|---|---|---|
| 1 — `code-smells-project` | Python 3.12 + Flask 3.1.1 + sqlite3 | 14 | 6 | 3 | 3 | 2 |
| 2 — `ecommerce-api-legacy` | Node.js 22 + Express 4 + sqlite3 (memória) | 13 | 5 | 3 | 3 | 2 |
| 3 — `task-manager-api` | Python 3.12 + Flask 3.0.0 + Flask-SQLAlchemy | 14 | 3 | 3 | 5 | 3 |

Os três projetos atendem ao mínimo de RF-01 (≥ 5 problemas, ≥ 1 CRITICAL/HIGH, ≥ 2 MEDIUM, ≥ 2 LOW).

---

## Projeto 1 — code-smells-project (Python/Flask, e-commerce)

Monolito em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`): rotas registradas em `app.py`, "controllers" que são funções soltas com validação e prints, e um `models.py` que concentra SQL e regras dos domínios produtos, usuários, pedidos e relatórios.

| # | Sev. | Problema | Arquivo:linha | AP |
|---|---|---|---|---|
| 1.1 | CRITICAL | SQL Injection em praticamente todas as queries | `models.py:109-111` (login), `models.py:289-297` (busca), `models.py:28`, `47-50`, `58-60`, `68`, `92`, `126-129`, `140`, `148-151`, `157-166`, `174`, `188`, `192`, `279-281` | AP-02 |
| 1.2 | CRITICAL | Endpoints administrativos sem autenticação (reset do banco e SQL arbitrário) | `app.py:47-57`, `app.py:59-78` | AP-05 / AP-02 |
| 1.3 | CRITICAL | Credencial hardcoded (`SECRET_KEY`) | `app.py:7` | AP-01 |
| 1.4 | CRITICAL | Exposição de dados sensíveis (segredo no `/health`, senhas em `/usuarios`) | `controllers.py:286-289`, `models.py:83`, `models.py:99` | AP-04 |
| 1.5 | CRITICAL | Senhas armazenadas e comparadas em texto puro | `database.py:75-83`, `models.py:126-129`, `models.py:109-111` | AP-06 |
| 1.6 | CRITICAL | God Class/God Module: `models.py` com SQL e regras de 4 domínios | `models.py:1-314` | AP-03 |
| 1.7 | HIGH | Estado global mutável: conexão SQLite única compartilhada entre threads | `database.py:4-11` | AP-08 |
| 1.8 | HIGH | Configuração de runtime insegura (`DEBUG=True`, `0.0.0.0`, CORS aberto) | `app.py:8`, `app.py:9`, `app.py:88` | AP-11 |
| 1.9 | HIGH | Criação de pedido sem transação (escritas múltiplas, retornos antecipados, sem rollback) | `models.py:133-169` | AP-10 |
| 1.10 | MEDIUM | Queries N+1 na listagem de pedidos | `models.py:187-193`, `models.py:219-225` | AP-12 |
| 1.11 | MEDIUM | Validação ausente/inconsistente entre criar e atualizar produto; `get_json()` sem checar `None` | `controllers.py:24-62` vs `controllers.py:64-96`; `controllers.py:239-240`, `controllers.py:169-170` | AP-13 |
| 1.12 | MEDIUM | Tratamento de erro genérico que devolve `str(e)` ao cliente, repetido em todos os handlers | `controllers.py:10-12` (padrão em todo o arquivo), `app.py:77-78` | AP-14 |
| 1.13 | LOW | Magic numbers/strings (faixas de desconto, listas de categorias e status inline) | `models.py:256-262`, `controllers.py:52`, `controllers.py:242` | AP-17 |
| 1.14 | LOW | `print` como log, inclusive simulando envio de e-mail/SMS | `controllers.py:8`, `57`, `106`, `161`, `179`, `182`, `208-210`, `248`, `250`; `app.py:56`, `83-86` | AP-20 / AP-09 |

### Detalhamento e justificativa

**1.1 [CRITICAL] SQL Injection** — Todas as funções de `models.py` montam SQL por concatenação (`"SELECT * FROM produtos WHERE id = " + str(id)`). Os casos mais graves recebem texto livre do cliente: o login (`models.py:109-111`) concatena `email` e `senha`, permitindo autenticar como qualquer usuário com `' OR '1'='1`; a busca (`models.py:289-297`) concatena `termo` e `categoria` da query string. *Relevância:* explorável remotamente sem autenticação; permite ler e destruir o banco inteiro e contornar o login.

**1.2 [CRITICAL] Endpoints administrativos desprotegidos** — `POST /admin/reset-db` (`app.py:47-57`) apaga todas as tabelas e `POST /admin/query` (`app.py:59-78`) executa qualquer SQL recebido em `{"sql": ...}`, ambos sem nenhuma checagem de identidade. *Relevância:* qualquer pessoa na rede (o servidor escuta em `0.0.0.0`) apaga ou exfiltra o banco com uma requisição.

**1.3 [CRITICAL] Credencial hardcoded** — `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` (`app.py:7`). *Relevância:* a chave de assinatura de sessão fica no repositório; quem tem acesso ao código pode forjar cookies de sessão. Agravado pelo item 1.4, que a publica via HTTP.

**1.4 [CRITICAL] Exposição de dados sensíveis** — `GET /health` devolve `secret_key`, `db_path`, `debug` e `ambiente` (`controllers.py:286-289`); `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha"` no JSON (`models.py:83`, `models.py:99`), expostos em `GET /usuarios` e `GET /usuarios/<id>`. *Relevância:* qualquer cliente obtém o segredo da aplicação e as senhas (em texto puro, item 1.5) de todos os usuários.

**1.5 [CRITICAL] Senhas em texto puro** — Os seeds gravam `admin123`, `123456`, `senha123` diretamente (`database.py:75-83`); `criar_usuario` insere a senha recebida (`models.py:126-129`); o login compara `senha = '<valor>'` no SQL (`models.py:109-111`). *Relevância:* qualquer vazamento do arquivo `loja.db` (ou o item 1.4) expõe todas as credenciais, que costumam ser reutilizadas em outros serviços.

**1.6 [CRITICAL] God Class / God Module** — `models.py` (314 linhas) contém acesso a dados, serialização, regras de pedido (checagem de estoque, cálculo de total, baixa de estoque) e regras de relatório (faixas de desconto) para produtos, usuários, pedidos e relatórios, todos usando a conexão global. *Relevância:* não há como testar ou alterar um domínio sem tocar os outros; é a raiz que impede a separação MVC.

**1.7 [HIGH] Estado global mutável** — `db_connection` global com inicialização preguiçosa via `global` e `check_same_thread=False` (`database.py:4-11`); a mesma conexão é usada por todas as requisições e threads. *Relevância:* transações de requisições diferentes se misturam (um `commit` de uma requisição confirma escritas pendentes de outra) e o estado não é isolável em testes.

**1.8 [HIGH] Configuração de runtime insegura** — `DEBUG = True` (`app.py:8`), `CORS(app)` sem restrição de origens (`app.py:9`) e `app.run(host="0.0.0.0", ..., debug=True)` (`app.py:88`). *Relevância:* o debugger interativo do Werkzeug exposto na rede permite execução remota de código; tudo fixo no código, sem como desligar por ambiente.

**1.9 [HIGH] Escritas sem transação** — `criar_pedido` (`models.py:133-169`) valida itens, insere o pedido, insere itens e baixa estoque em instruções separadas, com um único `commit` no fim e sem rollback; uma exceção no meio deixa escritas pendentes na conexão global, que serão confirmadas pelo próximo `commit` de qualquer outra requisição. A checagem de estoque e a baixa também não são atômicas. *Relevância:* pedidos sem itens e estoque inconsistente sob falha ou concorrência.

**1.10 [MEDIUM] N+1 queries** — `get_pedidos_usuario` e `get_todos_pedidos` fazem, para cada pedido, uma consulta de itens (`cursor2`) e, para cada item, uma consulta do nome do produto (`cursor3`) (`models.py:187-193`, `models.py:219-225`). *Relevância:* `GET /pedidos` executa 1 + P + P·I consultas; degrada linearmente com o volume.

**1.11 [MEDIUM] Validação ausente/inconsistente** — `criar_produto` valida tamanho do nome e categoria (`controllers.py:47-54`), mas `atualizar_produto` não (`controllers.py:64-96`), permitindo gravar via PUT dados que o POST rejeita. `atualizar_status_pedido` e `login` chamam `dados.get(...)` sem checar se o corpo existe (`controllers.py:239-240`, `controllers.py:169-170`), e tipos não são verificados (`preco < 0` com string). *Relevância:* dados inválidos persistidos e erros 500 para entradas comuns.

**1.12 [MEDIUM] Tratamento de erro genérico** — Todo handler envolve o corpo em `try/except Exception as e: return jsonify({"erro": str(e)}), 500` (padrão iniciado em `controllers.py:10-12`), e `/admin/query` faz o mesmo (`app.py:77-78`); não há error handler central. *Relevância:* mensagens internas (SQL, nomes de tabela) vazam ao cliente, ajudando a explorar o item 1.1; código repetitivo.

**1.13 [LOW] Magic numbers/strings** — Faixas de desconto `10000/5000/1000` e taxas `0.1/0.05/0.02` inline (`models.py:256-262`); lista de categorias válidas (`controllers.py:52`) e de status (`controllers.py:242`) inline. *Relevância:* regras comerciais escondidas no código, difíceis de localizar e manter consistentes.

**1.14 [LOW] `print` como log** — Logs via `print` em controllers e no boot, inclusive "ENVIANDO EMAIL/SMS/PUSH" no meio do fluxo de pedido (`controllers.py:208-210`), o que também caracteriza efeito colateral acoplado ao controller (AP-09). *Relevância:* sem níveis nem destino configurável; integrações simuladas inline impedem trocar por um serviço real.

Outros pontos observados (não contados): imports não usados (`models.py:2` `sqlite3`, `database.py:2` `os`); parâmetro `id` sombreando builtin (`controllers.py:14`, `models.py:24`); serialização de produto duplicada (`models.py:12-21`, `31-40`, `304-313`); `cursor2`/`cursor3` como nomes.

---

## Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

Três arquivos em `src/`: `app.js` (bootstrap), `AppManager.js` (classe que cria o banco em memória, faz seed, registra as 3 rotas e contém toda a lógica) e `utils.js` (config com segredos, cache global e "criptografia" caseira).

| # | Sev. | Problema | Arquivo:linha | AP |
|---|---|---|---|---|
| 2.1 | CRITICAL | Credenciais hardcoded (senha de banco, chave live do gateway) | `src/utils.js:1-7` | AP-01 |
| 2.2 | CRITICAL | God Class `AppManager` (banco, seed, rotas e regras no mesmo lugar) | `src/AppManager.js:4-139` | AP-03 |
| 2.3 | CRITICAL | Número do cartão e chave do gateway escritos no log | `src/AppManager.js:45` | AP-04 |
| 2.4 | CRITICAL | Relatório financeiro administrativo e deleção de usuário sem autenticação | `src/AppManager.js:80-129`, `src/AppManager.js:131-137` | AP-05 |
| 2.5 | CRITICAL | "Hash" de senha caseiro e reversível; seed com senha em texto puro; senha default `123456` | `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:68` | AP-06 |
| 2.6 | HIGH | Checkout em pirâmide de callbacks sem transação; erro de auditoria ignorado | `src/AppManager.js:37-77` (5 níveis), `src/AppManager.js:57-61` | AP-10 |
| 2.7 | HIGH | Deleção de usuário deixa matrículas e pagamentos órfãos e ignora erro | `src/AppManager.js:131-137` | AP-10 |
| 2.8 | HIGH | Estado global mutável (cache sem limite e contador de receita no módulo) | `src/utils.js:9-15` | AP-08 |
| 2.9 | MEDIUM | N+1 no relatório financeiro (consulta por curso, por matrícula, por usuário e por pagamento) | `src/AppManager.js:89-127` | AP-12 |
| 2.10 | MEDIUM | Validação de entrada insuficiente (só truthiness; `card` não-string derruba o processo) | `src/AppManager.js:35`, `src/AppManager.js:46` | AP-13 |
| 2.11 | MEDIUM | Erros de callback ignorados (`err` não lido; `enrollments.length` com `err`) | `src/AppManager.js:92-93`, `104-106`, `133-135` | AP-14 |
| 2.12 | LOW | Nomes ruins (`u`, `e`, `p`, `cid`, `cc`, `badCrypto`) | `src/AppManager.js:29-33`, `src/utils.js:17` | AP-18 |
| 2.13 | LOW | Magic numbers/strings (prefixo `"4"` aprova pagamento, `10000` iterações, corte em 10 chars, status literais) | `src/AppManager.js:46`, `src/utils.js:19`, `src/utils.js:22` | AP-17 |

### Detalhamento e justificativa

**2.1 [CRITICAL] Credenciais hardcoded** — `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser` no objeto `config` (`src/utils.js:1-7`). *Relevância:* a chave "live" do gateway e a senha "prod" ficam no repositório; vazamento permite cobranças e acesso ao banco de produção.

**2.2 [CRITICAL] God Class** — `AppManager` (`src/AppManager.js:4-139`) instancia o banco no construtor, cria schema e seed (`initDb`), registra as rotas (`setupRoutes`) e implementa checkout, pagamento, relatório e deleção dentro dos handlers. *Relevância:* nenhuma parte é testável isoladamente; é exatamente o exemplo de God Class da escala CRITICAL.

**2.3 [CRITICAL] Dados sensíveis em log** — ``console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)`` (`src/AppManager.js:45`). *Relevância:* número completo do cartão e chave do gateway em logs violam PCI-DSS e espalham segredos para qualquer sistema de log.

**2.4 [CRITICAL] Endpoints administrativos/destrutivos sem autenticação** — `GET /api/admin/financial-report` (`src/AppManager.js:80-129`) devolve nomes de alunos e valores pagos a qualquer cliente; `DELETE /api/users/:id` (`src/AppManager.js:131-137`) remove usuários sem checagem. *Relevância:* exposição de PII/financeiro e destruição de dados por qualquer pessoa.

**2.5 [CRITICAL] Armazenamento inseguro de senha** — `badCrypto` (`src/utils.js:17-23`) repete os 2 primeiros caracteres do base64 da senha e trunca em 10 caracteres: é reversível parcialmente e gera colisões triviais (senhas com o mesmo prefixo têm o mesmo "hash"). O seed grava `'123'` em texto puro (`src/AppManager.js:18`) e, sem `pwd`, o checkout cria o usuário com a senha `123456` (`src/AppManager.js:68`). *Relevância:* senhas efetivamente desprotegidas e contas criadas com senha previsível.

**2.6 [HIGH] Pirâmide de callbacks sem transação** — O checkout aninha 5 níveis de callbacks (`src/AppManager.js:37-77`): matrícula, pagamento e auditoria são gravados em instruções independentes; se o pagamento falhar, a matrícula já foi gravada; o erro da auditoria é ignorado (`src/AppManager.js:57-61`). *Relevância:* inconsistência financeira (matrícula sem pagamento) e código ilegível, difícil de evoluir.

**2.7 [HIGH] Deleção que deixa órfãos** — `DELETE /api/users/:id` remove só o usuário; matrículas e pagamentos ficam sem dono, como a própria resposta admite, e o `err` é ignorado (`src/AppManager.js:131-137`). *Relevância:* relatórios passam a mostrar alunos "Unknown" e dados inconsistentes se acumulam.

**2.8 [HIGH] Estado global mutável** — `globalCache` e `totalRevenue` são `let` de módulo; `logAndCache` grava no cache a cada checkout sem limite (`src/utils.js:9-15`). *Relevância:* crescimento de memória ilimitado, estado não isolável e inútil (nada lê o cache).

**2.9 [MEDIUM] N+1 no relatório** — Para cada curso, consulta matrículas; para cada matrícula, consulta usuário e pagamento, com contadores manuais para saber quando responder (`src/AppManager.js:89-127`). *Relevância:* número de consultas cresce com cursos × matrículas; a lógica de contadores é frágil (respostas duplicadas ou ausentes em erro).

**2.10 [MEDIUM] Validação insuficiente** — Só verifica truthiness de `usr`, `eml`, `c_id`, `card` (`src/AppManager.js:35`); se `card` vier como número, `cc.startsWith("4")` (`src/AppManager.js:46`) lança `TypeError` dentro de um callback do sqlite e derruba o processo inteiro. *Relevância:* uma requisição malformada tira a API do ar.

**2.11 [MEDIUM] Erros ignorados** — Callbacks não leem `err` (`src/AppManager.js:104-106`, `133-135`); em `src/AppManager.js:92-93`, se a consulta falhar, `enrollments.length` sobre `undefined` lança exceção e derruba o processo. *Relevância:* falhas silenciosas ou queda total, sem error handler central.

**2.12 [LOW] Nomes ruins** — `let u`, `e`, `p`, `cid`, `cc` (`src/AppManager.js:29-33`) e `badCrypto` (`src/utils.js:17`). *Relevância:* leitura lenta do fluxo mais crítico (checkout); os nomes do contrato (`usr`, `eml`...) devem ser mantidos na borda, mas não internamente.

**2.13 [LOW] Magic numbers/strings** — A regra "cartão começando com `4` é aprovado" (`src/AppManager.js:46`), `10000` iterações e corte em `10` caracteres (`src/utils.js:19`, `22`), status `'PAID'`/`'DENIED'` literais. *Relevância:* regras de negócio implícitas, difíceis de achar e alterar.

Outros pontos observados (não contados): `totalRevenue` importado e nunca usado (`src/AppManager.js:2`, `src/utils.js:10`); `console.log` como log (`src/utils.js:13`, `src/app.js:13`); porta fixa na config literal. APIs deprecated: nenhuma encontrada (`sqlite3.verbose()` e `express.json()` são atuais) — item do checklist "não aplicável" para este projeto.

---

## Projeto 3 — task-manager-api (Python/Flask, Task Manager)

Já possui `models/`, `routes/`, `services/` e `utils/`, mas: não há controllers (as rotas contêm validação, regras, consultas e montagem de resposta), não há módulo de config nem error handler, a aplicação é criada no import de `app.py`, `services/` e `utils/` não são usados, e há problemas de segurança no model de usuário.

| # | Sev. | Problema | Arquivo:linha | AP |
|---|---|---|---|---|
| 3.1 | CRITICAL | Credenciais hardcoded (`SECRET_KEY`, senha SMTP) | `app.py:13`, `services/notification_service.py:7-10` | AP-01 |
| 3.2 | CRITICAL | Hash de senha devolvido nas respostas (`to_dict` inclui `password`) | `models/user.py:16-25` (campo na linha 21); usado em `routes/user_routes.py:33`, `85`, `129`, `209` | AP-04 |
| 3.3 | CRITICAL | Senha com MD5 sem sal | `models/user.py:27-32` | AP-06 |
| 3.4 | HIGH | Regra de negócio e acesso a dados nas rotas (sem camada de controllers) | `routes/task_routes.py:85-154`, `routes/report_routes.py:12-101` | AP-07 |
| 3.5 | HIGH | Aplicação criada no import, sem factory/config, com scripts acoplados ao módulo | `app.py:9-31`, `seed.py:2` | AP-09 |
| 3.6 | HIGH | Configuração de runtime insegura (`debug=True`, `0.0.0.0`, CORS aberto) | `app.py:34`, `app.py:15` | AP-11 |
| 3.7 | MEDIUM | N+1 queries (usuário e categoria por task; tasks por usuário; contagem por categoria) | `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-56`, `routes/report_routes.py:163` | AP-12 |
| 3.8 | MEDIUM | Cálculo de "atrasada" duplicado em 6 lugares apesar de `Task.is_overdue()` | `routes/task_routes.py:30-39`, `71-80`, `283-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:34-36`, `132-135` (vs `models/task.py:50-60`) | AP-15 |
| 3.9 | MEDIUM | APIs deprecated: `Query.get()` (legado no SQLAlchemy 2.x) e `datetime.utcnow()` (deprecated no Python 3.12) | `routes/task_routes.py:42` (+15 ocorrências de `.query.get`); `models/task.py:15-16` (+20 ocorrências de `utcnow`) | AP-16 |
| 3.10 | MEDIUM | `except:` genérico em todas as rotas | `routes/task_routes.py:62-63`, `137`, `204`, `236`; `routes/user_routes.py:130`, `149`; `routes/report_routes.py:186`, `207`, `221` | AP-14 |
| 3.11 | MEDIUM | Validação de tipo ausente gera 500 (`priority` string; corpo ausente no PUT de categoria) | `routes/task_routes.py:113`, `routes/task_routes.py:182`, `routes/report_routes.py:196-197` | AP-13 |
| 3.12 | LOW | Imports não usados e código morto (`NotificationService`, `utils/helpers.py` inteiro) | `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `models/task.py:3`, `services/notification_service.py:4-48`, `utils/helpers.py:1-116` | AP-19 |
| 3.13 | LOW | Magic numbers/strings (status e prioridades inline, apesar das constantes em `utils/helpers.py:110-116`) | `routes/task_routes.py:110`, `113`, `177`, `182`; `routes/report_routes.py:129`, `45` | AP-17 |
| 3.14 | LOW | Nomes ruins (`p1`…`p5`) e `print` como log | `routes/report_routes.py:24-28`; `routes/task_routes.py:149`, `153`, `219`, `234`, `routes/user_routes.py:83`, `89`, `147` | AP-18 / AP-20 |

### Detalhamento e justificativa

**3.1 [CRITICAL] Credenciais hardcoded** — `app.config['SECRET_KEY'] = 'super-secret-key-123'` (`app.py:13`) e `email_user`/`email_password = 'senha123'` com host SMTP fixo (`services/notification_service.py:7-10`). *Relevância:* segredo de assinatura e senha de e-mail no repositório.

**3.2 [CRITICAL] Exposição do hash de senha** — `User.to_dict()` inclui `'password': self.password` (`models/user.py:21`) e é usado em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e no corpo do `POST /login` (`routes/user_routes.py:33`, `85`, `129`, `209`). *Relevância:* qualquer cliente obtém os hashes MD5, quebráveis em segundos (item 3.3).

**3.3 [CRITICAL] MD5 sem sal** — `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()` (`models/user.py:27-32`). *Relevância:* MD5 sem sal é revertido por tabelas rainbow; senhas iguais geram hashes iguais. Combinado com 3.2, as senhas ficam praticamente públicas.

**3.4 [HIGH] Regra de negócio nas rotas** — `create_task` (`routes/task_routes.py:85-154`) faz validação, checagem de FKs, parsing de data, normalização de tags e persistência; `summary_report` (`routes/report_routes.py:12-101`) faz ~15 consultas e todos os cálculos do relatório dentro da view. Não existe camada de controllers nem de serviços usada. *Relevância:* problema arquitetural central do projeto apesar das pastas: regras não reutilizáveis, rotas longas e não testáveis sem HTTP.

**3.5 [HIGH] Acoplamento: app criada no import, sem factory** — `app.py:9-31` cria o `Flask`, configura URI/segredo inline, registra blueprints e executa `db.create_all()` no import; `seed.py:2` importa `app` e `db` desse módulo. *Relevância:* impossível criar a aplicação com outra config (testes, banco em memória); qualquer import de `app` tem efeitos colaterais no banco. A refatoração precisa manter `from app import app, db` funcionando.

**3.6 [HIGH] Configuração de runtime insegura** — `app.run(debug=True, host='0.0.0.0', port=5000)` (`app.py:34`) e `CORS(app)` sem origens (`app.py:15`). *Relevância:* debugger do Werkzeug exposto na rede (execução remota de código).

**3.7 [MEDIUM] N+1 queries** — `GET /tasks` faz `User.query.get` e `Category.query.get` para cada task (`routes/task_routes.py:41-57`); `GET /users` acessa `u.tasks` (lazy) por usuário (`routes/user_routes.py:22`); o relatório consulta tasks por usuário (`routes/report_routes.py:55-56`); `GET /categories` faz `count()` por categoria (`routes/report_routes.py:163`). *Relevância:* número de consultas cresce com o volume de dados.

**3.8 [MEDIUM] Código duplicado** — O bloco "está atrasada" (`due_date < utcnow()` e status diferente de done/cancelled) é reescrito em 6 lugares (`routes/task_routes.py:30-39`, `71-80`, `283-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:34-36`, `132-135`), embora `Task.is_overdue()` exista (`models/task.py:50-60`). A serialização de task também é refeita manualmente em `routes/task_routes.py:17-28` e `routes/user_routes.py:162-169`. *Relevância:* uma mudança de regra precisa ser replicada em 6 pontos; alto risco de divergência.

**3.9 [MEDIUM] APIs deprecated** — `Model.query.get(id)` é API legada no SQLAlchemy 2.x (emite `LegacyAPIWarning`; Flask-SQLAlchemy 3.1 exige SQLAlchemy 2) — 16 ocorrências, primeira em `routes/task_routes.py:42` → `db.session.get(Model, id)`. `datetime.utcnow()` é deprecated no Python 3.12 — 22 ocorrências, primeiras em `models/task.py:15-16` → `datetime.now(timezone.utc)` (o `seed.py` já emite `DeprecationWarning` no boot). *Relevância:* quebrará em atualizações de runtime/biblioteca; o enunciado exige detecção de APIs deprecated.

**3.10 [MEDIUM] Tratamento de erro genérico** — `except:` sem tipo em todas as rotas (ex.: `routes/task_routes.py:62-63` devolve 500 genérico escondendo a causa); sem error handler central. *Relevância:* falhas silenciosas e diagnóstico impossível; capturam até `KeyboardInterrupt`/`SystemExit`.

**3.11 [MEDIUM] Validação de tipo ausente** — `priority < 1` com `priority` string (`routes/task_routes.py:113`, `182`) lança `TypeError` → 500; `update_category` faz `'name' in data` sem checar se o corpo existe (`routes/report_routes.py:196-197`) → 500. Os validadores de `utils/helpers.py` não são usados. *Relevância:* erros 500 para entradas comuns em vez de 400.

**3.12 [LOW] Imports não usados e código morto** — `import os, sys, json` (`app.py:7`); `json, os, sys, time` (`routes/task_routes.py:7`); `hashlib, json` (`routes/user_routes.py:6`); `format_date, calculate_percentage` e `json` importados e nunca usados (`routes/report_routes.py:7-8`); `json` (`models/task.py:3`); `NotificationService` (`services/notification_service.py:4-48`) nunca é importado; `utils/helpers.py` inteiro não é usado. *Relevância:* camadas "de fachada" dão a falsa impressão de organização e confundem a manutenção.

**3.13 [LOW] Magic numbers/strings** — Lista de status e faixa `1..5` inline (`routes/task_routes.py:110`, `113`, `177`, `182`), `priority <= 2` como "alta prioridade" (`routes/report_routes.py:129`), `days=7` (`routes/report_routes.py:45`), enquanto `VALID_STATUSES`/`DEFAULT_PRIORITY` existem sem uso em `utils/helpers.py:110-116`. *Relevância:* regras espalhadas e constantes existentes ignoradas.

**3.14 [LOW] Nomes ruins e `print` como log** — `p1`…`p5` para contagens por prioridade (`routes/report_routes.py:24-28`); `print` para log nas rotas (`routes/task_routes.py:149`, `153`, `219`, `234`; `routes/user_routes.py:83`, `89`, `147`). *Relevância:* legibilidade e observabilidade ruins.

Outros pontos observados (não contados): token de login falso e previsível `'fake-jwt-token-' + str(user.id)` (`routes/user_routes.py:210`); deleção de categoria deixa tasks com `category_id` órfão (`routes/report_routes.py:211-223`); URI do banco fixa (`app.py:11`).

---

## Rastreabilidade problema manual → catálogo (RF-03)

| AP | Nome | P1 | P2 | P3 |
|---|---|---|---|---|
| AP-01 | Hardcoded Credentials | 1.3 | 2.1 | 3.1 |
| AP-02 | SQL Injection | 1.1, 1.2 | — | — |
| AP-03 | God Class / God Method | 1.6 | 2.2 | — |
| AP-04 | Sensitive Data Exposure | 1.4 | 2.3 | 3.2 |
| AP-05 | Unprotected Admin/Destructive Endpoint | 1.2 | 2.4 | — |
| AP-06 | Insecure Password Storage | 1.5 | 2.5 | 3.3 |
| AP-07 | Business Logic in Controller/Route | — | — | 3.4 |
| AP-08 | Global Mutable State | 1.7 | 2.8 | — |
| AP-09 | Tight Coupling / Missing Dependency Injection | 1.14 | — | 3.5 |
| AP-10 | Missing Transaction / Callback Pyramid | 1.9 | 2.6, 2.7 | — |
| AP-11 | Insecure Runtime Configuration | 1.8 | — | 3.6 |
| AP-12 | N+1 Queries | 1.10 | 2.9 | 3.7 |
| AP-13 | Missing or Inconsistent Input Validation | 1.11 | 2.10 | 3.11 |
| AP-14 | Generic Error Handling | 1.12 | 2.11 | 3.10 |
| AP-15 | Duplicated Code | — | — | 3.8 |
| AP-16 | Deprecated API Usage | — | — | 3.9 |
| AP-17 | Magic Numbers / Strings | 1.13 | 2.13 | 3.13 |
| AP-18 | Poor Naming | — | 2.12 | 3.14 |
| AP-19 | Unused Imports / Dead Code | — | — | 3.12 |
| AP-20 | Print/Console Logging | 1.14 | — | 3.14 |

Todos os 41 problemas mapeiam para ao menos uma entrada do catálogo; todas as 20 entradas são exercitadas por pelo menos um projeto.

## Projeto 1 — problemas que a Fase 2 deve reencontrar (CA-06)

Para o critério CA-06 (≥ 5 problemas manuais do projeto 1 no relatório da skill), os candidatos mais objetivos são: 1.1 SQL Injection (`models.py`), 1.2 endpoints admin (`app.py`), 1.3 Hardcoded Credentials (`app.py:7`), 1.4 Sensitive Data Exposure (`controllers.py`/`models.py`), 1.5 Insecure Password Storage, 1.6 God Class (`models.py`), 1.10 N+1 (`models.py`) e 1.13 Magic Numbers (`models.py:256-262`).
