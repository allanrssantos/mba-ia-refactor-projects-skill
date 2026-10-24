# Anti-patterns Catalog — referência da Fase 2

> Carregado na Fase 2 (e consultado na Fase 3). 20 entradas: 6 CRITICAL, 5 HIGH, 5 MEDIUM, 4 LOW.
> Os exemplos são **sintéticos** (entidades genéricas `items`, `orders`, `accounts`) e servem só para ilustrar o sinal; nunca são regras sobre um projeto específico.
> Padrões de busca estão em sintaxe ripgrep (ferramenta Grep). Sempre confirme lendo o trecho: um match de busca não é um finding até ser lido.

## Como usar

1. Para cada entrada, rode os padrões de busca sobre os arquivos-fonte contados na Fase 1 e leia os trechos encontrados.
2. Aplique os sinais de detecção; descarte o que estiver em "Não confundir com".
3. O título do finding é o **nome exato** da entrada (ex.: `SQL Injection`). A severidade é **fixa** (não reclassifique).
4. A Recommendation cita a(s) transformação(ões) `T-xx` indicada(s) em "Resolve com".
5. Agrupamento de ocorrências: regras em `audit-report-template.md` §3. O escopo de cada entrada está indicado em "Escopo".

## Escala de severidade (literal do enunciado)

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

## Índice

| ID | Nome (título do finding) | Severidade | Escopo | Resolve com |
|---|---|---|---|---|
| AP-01 | Hardcoded Credentials | CRITICAL | arquivo | T-01 |
| AP-02 | SQL Injection | CRITICAL | arquivo | T-02, T-05 |
| AP-03 | God Class / God Method | CRITICAL | unidade | T-03 |
| AP-04 | Sensitive Data Exposure | CRITICAL | arquivo | T-04, T-16 |
| AP-05 | Unprotected Admin/Destructive Endpoint | CRITICAL | arquivo | T-05 |
| AP-06 | Insecure Password Storage | CRITICAL | arquivo | T-06 |
| AP-07 | Business Logic in Controller/Route | HIGH | arquivo | T-07 |
| AP-08 | Global Mutable State | HIGH | arquivo | T-08 |
| AP-09 | Tight Coupling / Missing Dependency Injection | HIGH | arquivo | T-08 |
| AP-10 | Missing Transaction / Callback Pyramid | HIGH | arquivo | T-09 |
| AP-11 | Insecure Runtime Configuration | HIGH | arquivo | T-01 |
| AP-12 | N+1 Queries | MEDIUM | arquivo | T-10 |
| AP-13 | Missing or Inconsistent Input Validation | MEDIUM | arquivo | T-11 |
| AP-14 | Generic Error Handling | MEDIUM | projeto | T-12 |
| AP-15 | Duplicated Code | MEDIUM | projeto (por bloco) | T-07, T-11 |
| AP-16 | Deprecated API Usage | MEDIUM | projeto (por API) | T-13 |
| AP-17 | Magic Numbers / Strings | LOW | arquivo | T-14 |
| AP-18 | Poor Naming | LOW | arquivo | T-15 |
| AP-19 | Unused Imports / Dead Code | LOW | projeto | T-16 |
| AP-20 | Print/Console Logging | LOW | projeto | T-16 |

---

## AP-01 — Hardcoded Credentials

- **Severidade:** CRITICAL
- **Descrição:** Segredos (chaves de sessão/assinatura, senhas de banco/SMTP, chaves de API/gateway, tokens) escritos como literais no código-fonte versionado.
- **Sinais de detecção:**
  - Literal de string atribuído a variável, chave de config ou propriedade cujo nome contém `secret`, `password`, `passwd`, `pwd`, `pass`, `token`, `api_key`, `apikey`, `private_key`, `credential`, `auth`, `smtp`.
  - Literais com prefixos conhecidos de credencial: `sk_live_`, `pk_live_`, `sk_test_`, `AKIA`, `ghp_`, `xoxb-`, `-----BEGIN` (chave privada).
  - Connection string com usuário e senha embutidos: `scheme://user:senha@host`.
  - Leitura de variável de ambiente cujo **default** é um segredo real (`os.getenv("SECRET_KEY", "valor-de-producao")`, `process.env.KEY || "sk_live_..."`).
  - Objeto/dicionário de configuração literal com segredos (`const config = { dbPass: "..." }`).
  - Busca: `(?i)(secret|passw|pwd|token|api_?key|private_?key|smtp)\w*["']?\s*[:=]\s*["'][^"']{3,}["']` e `(sk|pk)_(live|test)_|AKIA[0-9A-Z]{12}|-----BEGIN`
  - Exemplo (Python): `app.config["SECRET_KEY"] = "my-very-secret-key"` / `self.smtp_password = "hunter2"`
  - Exemplo (JavaScript): `const settings = { dbPassword: "prod-pass-123", gatewayKey: "sk_live_abc" };`
  - Outras stacks: `application.properties` com `spring.datasource.password=...` versionado; constantes `const APIKey = "..."` em Go.
- **Não confundir com:** leitura de env var sem default secreto (`os.environ["SECRET_KEY"]`); placeholders evidentes em `.env.example` (`change-me`); senhas de **usuários de exemplo** em seeds (isso é AP-06 se forem gravadas em texto puro); hashes de teste.
- **Impacto:** Quem tem acesso ao repositório (ou a um vazamento dele) obtém as credenciais; permite forjar sessões/tokens, acessar banco, SMTP ou gateway de pagamento; rotação exige novo deploy.
- **Recomendação:** Mover para módulo de configuração lendo variáveis de ambiente, com default de desenvolvimento não secreto (ou gerado em runtime) e documentar em `.env.example`; tratar o valor exposto como comprometido.
- **Resolve com:** T-01.

## AP-02 — SQL Injection

- **Severidade:** CRITICAL
- **Descrição:** SQL montado por concatenação ou interpolação de valores vindos da requisição/parâmetros, ou endpoint que executa SQL recebido do cliente.
- **Sinais de detecção:**
  - String SQL (`SELECT|INSERT|UPDATE|DELETE`) construída com `+`, f-string, `%` (formatação de string, não tupla de parâmetros), `.format()` ou template literal `${}` e passada a `execute`, `executemany`, `executescript`, `query`, `run`, `all`, `get`, `exec`, `raw`.
  - Cláusulas dinâmicas montadas por `query += " AND col = '" + valor + "'"`, inclusive `LIKE '%" + termo + "%'`.
  - Endpoint que lê texto SQL do corpo/query e chama `execute(...)` com ele.
  - Buscas: `(?i)["'](SELECT|INSERT|UPDATE|DELETE)[^"']*["']\s*\+`, `(?i)\+\s*["']\s*(AND|OR|WHERE|VALUES|SET)\b`, `(?i)f["'](SELECT|INSERT|UPDATE|DELETE)`, ``(?i)`(SELECT|INSERT|UPDATE|DELETE)[^`]*\$\{``, `(?i)\.format\(.*\)|%\s*\(` próximos de SQL, `execute\(\s*\w+\s*\)` com variável vinda da requisição.
  - Exemplo (Python): `cursor.execute("SELECT * FROM items WHERE id = " + str(item_id))`
  - Exemplo (Python): `cursor.execute(f"UPDATE accounts SET name = '{name}' WHERE id = {account_id}")`
  - Exemplo (JavaScript): ``db.all(`SELECT * FROM items WHERE name LIKE '%${req.query.q}%'`)``
  - Outras stacks: `fmt.Sprintf("... WHERE id = %s", id)` em Go; `"... WHERE id = " + id` em JDBC `Statement`.
- **Não confundir com:** placeholders com parâmetros separados (`?`, `%s` com tupla, `:name`, `$1`); filtros de ORM (`Model.query.filter(Model.col == x)`, `.filter_by(col=x)`); **`Model.col.like(f"%{termo}%")` do SQLAlchemy é parametrizado** (a f-string monta só o valor do bind); query builders com bind (`knex.where('col', valor)`).
- **Impacto:** Leitura/alteração/remoção arbitrária de dados, bypass de login (`' OR '1'='1`), destruição do banco; vulnerabilidade explorável remotamente sem autenticação.
- **Recomendação:** Parametrizar todas as queries; em cláusulas dinâmicas, montar a lista de condições com placeholders e a lista de parâmetros em paralelo; identificadores (nomes de coluna/ordem) só de allow-list. Endpoint que executa SQL arbitrário: proteger por guard admin (T-05) e registrar como risco residual.
- **Resolve com:** T-02 (e T-05 para execução de SQL arbitrário).

## AP-03 — God Class / God Method

- **Severidade:** CRITICAL
- **Descrição:** Uma classe, módulo ou função concentra responsabilidades de várias camadas e domínios: roteamento/HTTP, acesso a dados, regra de negócio, formatação, bootstrap.
- **Sinais de detecção:**
  - Uma mesma unidade (classe ou arquivo) que faz **pelo menos dois** de: (a) registra rotas ou lê request/escreve response; (b) cria conexão/schema ou executa SQL/ORM; (c) aplica regra de negócio (cálculos, decisões, fluxos multi-etapa) — **e** atende 2 ou mais domínios/entidades.
  - Módulo com CRUD de 3 ou mais entidades diferentes (funções prefixadas por entidades distintas) e mais de ~250 linhas.
  - Classe com métodos como `initDb`/`createTables` **e** `setupRoutes`/`registerRoutes`; nomes genéricos `*Manager`, `*Handler`, `App*`, `Main*`, `Utils` concentrando tudo.
  - Função/método com mais de ~80 linhas misturando validação, persistência e resposta.
  - Exemplo (JavaScript): `class AppService { constructor(){ this.db = new Database(...) } initSchema(){...} mountRoutes(app){ app.post('/orders', ...) } }`
  - Exemplo (Python): `store.py` com `get_items`, `create_account`, `create_order`, `sales_report` e SQL de todas as tabelas.
- **Não confundir com:** composition root que apenas instancia e conecta componentes definidos em outros módulos; arquivo de models com várias classes de entidade que só mapeiam dados; arquivo grande de constantes.
- **Escopo:** 1 finding por classe/módulo; `File:` recebe o intervalo da classe ou do arquivo inteiro (`caminho:1-<última linha>`).
- **Impacto:** Impossível testar partes isoladamente; qualquer mudança arrisca efeitos colaterais em todos os domínios; conflitos de merge constantes; impede reuso.
- **Recomendação:** Separar por domínio em model (dados) + controller (fluxo) + routes (mapeamento), com composition root montando as dependências.
- **Resolve com:** T-03 (apoiado por T-08 e T-07).

## AP-04 — Sensitive Data Exposure

- **Severidade:** CRITICAL
- **Descrição:** Dados sensíveis devolvidos em respostas HTTP ou escritos em logs: senhas/hashes, segredos de configuração, números de cartão, chaves de API.
- **Sinais de detecção:**
  - Serializador/dicionário/objeto de resposta que inclui campos `password`, `senha`, `pass`, `pwd`, `hash`, `salt`, `secret`, `token` (ex.: `to_dict()` com a senha; `SELECT *` devolvido direto ao cliente).
  - Endpoints de health/info/debug que devolvem valores de config (`secret_key`, caminho do banco, flags de debug, ambiente).
  - Log/print de cartão, senha, token ou chave: `print`/`console.log`/`logger.*` cuja mensagem interpola `card`, `cc`, `password`, `secret`, `key`, `token`.
  - Buscas: `(?i)["'](password|senha|pass|pwd|hash|secret_?key|token)["']\s*:`, `(?i)(print|console\.log|logger\.\w+|log\.\w+)\(.*(card|cc\b|password|senha|secret|api_?key|token)`
  - Exemplo (Python): `return {"id": u.id, "email": u.email, "password": u.password}`
  - Exemplo (JavaScript): ``console.log(`charging card ${cardNumber} with key ${settings.gatewayKey}`)``
- **Não confundir com:** campos de senha apenas **recebidos** no request (login/cadastro); token de sessão devolvido intencionalmente no login; logs que mascaram o valor (`****1234`).
- **Impacto:** Vazamento de credenciais e PII para qualquer cliente ou para quem lê logs; hashes expostos permitem ataque offline; violação de LGPD/PCI-DSS.
- **Recomendação:** Serializador com allow-list de campos públicos; remover config/segredos das respostas; nunca logar dados sensíveis (mascarar quando necessário).
- **Resolve com:** T-04, T-16.

## AP-05 — Unprotected Admin/Destructive Endpoint

- **Severidade:** CRITICAL
- **Descrição:** Endpoints administrativos, destrutivos ou que expõem dados agregados sensíveis acessíveis sem autenticação/autorização.
- **Sinais de detecção:**
  - Path contendo `admin`, `internal`, `debug`, `reset`, `drop`, `purge`, `seed`, `query`, `exec`, `sql`, `maintenance` **sem** decorator/middleware de auth na rota nem checagem de header/token/sessão no handler.
  - Handler que executa deleção em massa (`DELETE FROM <tabela>` sem `WHERE`, `TRUNCATE`, `drop_all()`), SQL arbitrário ou relatórios financeiros/PII sob prefixo administrativo, sem guard.
  - Buscas: `(?i)(route|get|post|put|delete|add_url_rule)\(\s*["'][^"']*(admin|internal|debug|reset|drop|purge|query|exec|sql)`, `(?i)DELETE FROM \w+["']\s*\)`, `(?i)(TRUNCATE|drop_all\()`
  - Exemplo (Python): `@app.route("/admin/wipe", methods=["POST"])` seguido de `DELETE FROM orders` sem checagem.
  - Exemplo (JavaScript): `app.get('/internal/revenue', (req, res) => db.all('SELECT ...'))` sem middleware.
- **Não confundir com:** rotas com guard existente (decorator `@login_required`/`@require_admin`, middleware `auth` no router); CRUD comum de recurso próprio (DELETE de um registro por id) — se faltar auth em CRUD comum, não é este AP.
- **Impacto:** Qualquer pessoa na rede apaga o banco, executa SQL ou extrai dados financeiros/pessoais; a combinação com bind público torna o ataque trivial.
- **Recomendação:** Manter a rota registrada (contrato), protegida por guard configurável: `ADMIN_TOKEN` no ambiente + header `X-Admin-Token` comparado em tempo constante; sem token válido → 403.
- **Resolve com:** T-05.

## AP-06 — Insecure Password Storage

- **Severidade:** CRITICAL
- **Descrição:** Senhas persistidas em texto puro, com hash rápido sem sal (MD5/SHA-1/SHA-256 simples) ou com "hash" caseiro/reversível.
- **Sinais de detecção:**
  - INSERT/UPDATE da senha exatamente como recebida; seeds com senhas literais gravadas diretamente na coluna de senha.
  - Comparação de senha por igualdade direta: `WHERE email = ? AND password = ?`, `user.password == pwd`.
  - `hashlib.md5(`, `hashlib.sha1(`, `hashlib.sha256(` aplicados à senha; `crypto.createHash('md5'|'sha1'|'sha256')` sobre a senha.
  - Funções próprias de "criptografia": base64, loops de concatenação, truncamento (`substring(0, 10)`), XOR, `reverse()`.
  - Buscas: `(?i)(md5|sha1|sha256)\(`, `(?i)createHash\(\s*["'](md5|sha1|sha256)`, `(?i)(base64|btoa|toString\(\s*["']base64)`, `(?i)(senha|password|pass)\s*=\s*\?`
  - Exemplo (Python): `self.password = hashlib.md5(raw.encode()).hexdigest()`
  - Exemplo (JavaScript): `const digest = Buffer.from(pwd).toString('base64').slice(0, 12);`
- **Não confundir com:** `werkzeug.security.generate_password_hash`, `bcrypt`, `argon2`, `scrypt`, `hashlib.pbkdf2_hmac`/`crypto.pbkdf2` com sal aleatório e iterações altas; hash de valores que não são senha (ETag, checksum).
- **Impacto:** Vazamento do banco expõe senhas imediatamente (texto puro) ou em segundos (MD5 sem sal, tabelas rainbow); reutilização de senha compromete outras contas.
- **Recomendação:** KDF com sal da stdlib/ecossistema já disponível; verificação compatível com o formato legado e rehash transparente no próximo login bem-sucedido.
- **Resolve com:** T-06.

## AP-07 — Business Logic in Controller/Route

- **Severidade:** HIGH
- **Descrição:** Handlers HTTP contendo regras de negócio, cálculos, orquestração e acesso direto a dados, em vez de delegar a model/service.
- **Sinais de detecção:**
  - Função de rota (decorada ou registrada) que faz **dois ou mais** de: cadeia de validação de payload (5+ `if` sobre campos), cálculo/agregação (loops somando, faixas de desconto, estatísticas), acesso direto a dados (SQL ou ORM: `Model.query`, `db.session`, `cursor.execute`, `db.all`), efeitos colaterais (e-mail, notificação), decisão de fluxo de negócio (aprovar pagamento, mudar estado).
  - Handler com mais de ~40 linhas.
  - Em projetos com pasta `routes/` mas sem `controllers/`: rotas importando models e montando consultas/relatórios.
  - Exemplo (Python): rota `/reports/summary` que faz 10 consultas, laços de contagem e monta o relatório inteiro.
  - Exemplo (JavaScript): `router.post('/orders', (req, res) => { /* valida, calcula total, decide aprovação, grava 3 tabelas */ })`
- **Não confundir com:** controller fino que extrai entrada, chama um serviço/model e monta a resposta; validação simples de presença de 1–2 campos.
- **Impacto:** Regras não reutilizáveis nem testáveis sem HTTP; duplicação entre endpoints; mudanças de regra exigem tocar a camada de transporte.
- **Recomendação:** Controller fino (entrada → validação → chamada → resposta); regras em métodos de model ou em service da camada de modelo; queries no model.
- **Resolve com:** T-07 (com T-11 para validação).

## AP-08 — Global Mutable State

- **Severidade:** HIGH
- **Descrição:** Variáveis de módulo mutáveis compartilhadas entre requisições: conexões singleton preguiçosas, caches, contadores, listas acumuladas.
- **Sinais de detecção:**
  - Python: variável de módulo reatribuída dentro de função com `global x`; dicionários/listas de módulo modificados por funções (`cache[key] = ...`, `events.append(...)`).
  - JavaScript: `let` no escopo do módulo reatribuído ou objeto/array de módulo mutado por funções (`globalCache[k] = v`, `total += x`).
  - Conexão única de banco guardada em global e compartilhada entre threads (`check_same_thread=False`).
  - Estado em instância de serviço usada como singleton de módulo (lista que cresce sem limite).
  - Buscas: `^\s*global\s+\w+`, `^(let|var)\s+\w+\s*=`, `^\w+\s*=\s*(\{\}|\[\]|None|0)\s*$`, `check_same_thread\s*=\s*False`
  - Exemplo (Python): `_conn = None` + `def get_conn(): global _conn; if _conn is None: _conn = sqlite3.connect(...)`
  - Exemplo (JavaScript): `let requestCache = {}; function remember(k, v) { requestCache[k] = v; }`
- **Não confundir com:** constantes (MAIÚSCULAS nunca reatribuídas); objetos de framework projetados para nível de módulo (`app = Flask(__name__)`, `db = SQLAlchemy()`, `router = express.Router()`, `logger = logging.getLogger()`); config imutável.
- **Impacto:** Condições de corrida, vazamento de memória, testes dependentes de ordem, comportamento diferente por processo/worker; impossível isolar estado em testes.
- **Recomendação:** Estado criado no composition root e injetado; conexão por requisição ou gerenciada pelo framework; remover caches não usados ou encapsulá-los com limite.
- **Resolve com:** T-08.

## AP-09 — Tight Coupling / Missing Dependency Injection

- **Severidade:** HIGH
- **Descrição:** Componentes instanciam suas próprias dependências concretas (banco, clientes externos, serviços) ou executam efeitos colaterais inline, impedindo substituição e teste; aplicação criada em tempo de import sem fábrica.
- **Sinais de detecção:**
  - `new Database(...)`, `sqlite3.connect(...)`, `smtplib.SMTP(host, port)`, `requests.Session()`, `new SomeClient(...)` dentro de construtor, handler ou método de negócio, com host/caminho fixo.
  - Controllers/handlers chamando diretamente o getter global de conexão (`get_db()`), pulando o model.
  - Efeitos colaterais de integração inline (`print("SENDING EMAIL ...")`, chamadas SMTP/HTTP no meio do handler) em vez de um serviço injetável.
  - Objeto `app` criado e configurado no import do módulo (sem `create_app()`/`createApp()`), com config inline, registrado e iniciado no mesmo arquivo.
  - Buscas: `(?i)new\s+(sqlite3\.)?Database\(`, `(?i)(smtplib\.SMTP|sqlite3\.connect|requests\.Session|new\s+\w+Client)\(`, `(?i)(print|console\.log)\(\s*["'].*(EMAIL|SMS|PUSH|NOTIF)`
  - Exemplo (JavaScript): `class OrderService { constructor() { this.db = new sqlite3.Database(':memory:'); } }`
  - Exemplo (Python): `def create_order(): ...; print("SENDING EMAIL to customer")` dentro do controller.
- **Não confundir com:** composition root/fábrica que instancia e injeta dependências; extensões de framework inicializadas com `init_app(app)`.
- **Impacto:** Impossível testar com banco/serviço falso; troca de infraestrutura exige editar regra de negócio; side effects acoplados ao fluxo HTTP.
- **Recomendação:** Fábrica da aplicação que cria dependências e as passa a models/controllers/serviços; integrações atrás de um serviço com interface simples.
- **Resolve com:** T-08.

## AP-10 — Missing Transaction / Callback Pyramid

- **Severidade:** HIGH
- **Descrição:** Escritas dependentes em várias etapas sem transação/rollback, callbacks aninhados profundamente, ou remoções que deixam registros órfãos.
- **Sinais de detecção:**
  - Sequência de 2+ escritas relacionadas (ex.: cabeçalho + itens + baixa de estoque) sem `BEGIN/COMMIT/ROLLBACK`, `with conn:`, `session.begin()`, `transaction()`; `return` antecipado entre escritas sem rollback.
  - Callbacks aninhados em 3 ou mais níveis (`db.run(..., function(){ db.run(..., function(){ db.run(...`), com erros internos ignorados.
  - DELETE de registro pai sem tratar filhos (sem cascade, sem remoção dos dependentes) — inclusive mensagens que admitem dados "sujos".
  - Verificação seguida de escrita sem atomicidade (checa estoque, depois decrementa em outra instrução).
  - Buscas: `function\s*\(err` aninhado, `\}\);\s*\}\);\s*\}\);`, `(?i)DELETE FROM \w+ WHERE id`, `commit\(\)` isolado após vários `execute`
  - Exemplo (JavaScript): `db.run(insertOrder, [], function () { db.run(insertItem, [], function () { db.run(insertAudit, [], () => res.json(...)) }) })`
  - Exemplo (Python): três `cursor.execute(...)` de escrita e um único `conn.commit()` no fim, com `return` de erro no meio.
- **Não confundir com:** escrita única; ORM com unit-of-work que faz commit/rollback em bloco `try/except` correto; cascade declarado no schema/ORM.
- **Impacto:** Dados inconsistentes em falhas parciais (pedido sem itens, pagamento sem registro correspondente), órfãos acumulando, fluxo ilegível e propenso a respostas duplicadas/ausentes.
- **Recomendação:** Agrupar escritas em transação com rollback; achatar callbacks com Promises/async-await; tratar dependentes ao remover (cascade explícito ou remoção em transação).
- **Resolve com:** T-09.

## AP-11 — Insecure Runtime Configuration

- **Severidade:** HIGH
- **Descrição:** Configuração de execução insegura fixada no código: modo debug ligado, bind em todas as interfaces, CORS irrestrito, valores de ambiente hardcoded.
- **Sinais de detecção:**
  - `debug=True`, `DEBUG = True`, `app.config["DEBUG"] = True`, `app.run(..., debug=True)`; `NODE_ENV` ignorado com stack traces enviados ao cliente.
  - `host="0.0.0.0"` fixo no código (sem config/env).
  - `CORS(app)` ou `app.use(cors())` sem lista de origens configurável.
  - URI do banco, porta e flags fixas no código sem possibilidade de override.
  - Buscas: `(?i)debug\s*=\s*True|["']DEBUG["']\]\s*=\s*True`, `host\s*=\s*["']0\.0\.0\.0`, `CORS\(\s*app\s*\)|cors\(\s*\)`
  - Exemplo (Python): `app.run(host="0.0.0.0", port=8000, debug=True)` (o debugger interativo do Werkzeug permite execução remota de código).
  - Exemplo (JavaScript): `app.use(cors()); app.listen(8080, '0.0.0.0')`
- **Não confundir com:** valores lidos de config/env com default seguro (`debug` padrão `False`).
- **Impacto:** Execução remota de código via debugger, exposição de stack traces e da aplicação na rede, requisições cross-origin de qualquer site.
- **Recomendação:** Ler debug/host/porta/CORS de config com defaults seguros (`debug=False`, host local), mantendo a porta original como default.
- **Resolve com:** T-01.

## AP-12 — N+1 Queries

- **Severidade:** MEDIUM
- **Descrição:** Uma consulta por item de um resultado anterior (consulta dentro de laço), ou acesso preguiçoso a relacionamentos em laço.
- **Sinais de detecção:**
  - `for`/`forEach`/`map` sobre linhas de uma consulta contendo outra chamada de banco (`execute`, `db.get`, `db.all`, `Model.query...`, `session.get`).
  - Acesso a relacionamento lazy dentro de laço (`len(obj.children)`, `item.owner.name`) sem eager loading.
  - `count()` executado por item em laço; vários `count()` sequenciais por status onde um `GROUP BY` bastaria (reporte junto, como variação).
  - Buscas: `for .* in .*:\n(.*\n){0,6}.*(execute|query|\.get\(|filter_by)` (multiline), `forEach\(.*=>\s*\{\s*\n(.*\n){0,4}.*db\.(get|all|run)` (multiline)
  - Exemplo (Python): `for order in orders: cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))`
  - Exemplo (JavaScript): `items.forEach(i => db.get('SELECT name FROM accounts WHERE id = ?', [i.account_id], ...))`
- **Não confundir com:** laço sobre dados já carregados em memória; consultas em lote (`WHERE id IN (...)`); eager loading configurado (`joinedload`, `selectinload`, `include`).
- **Impacto:** Latência cresce linearmente com o volume (1 + N + N·M consultas); carga desnecessária no banco; timeouts em listagens e relatórios.
- **Recomendação:** JOIN/consulta em lote + montagem em memória, eager loading do ORM ou agregação no banco (`GROUP BY`), preservando forma e ordem da resposta.
- **Resolve com:** T-10.

## AP-13 — Missing or Inconsistent Input Validation

- **Severidade:** MEDIUM
- **Descrição:** Entrada do cliente usada sem checar presença, tipo e faixa; regras diferentes entre criação e atualização; falhas de tipo viram 500.
- **Sinais de detecção:**
  - `request.get_json()`/`req.body` usado sem checar `None`/objeto (`data.get(...)` ou `'x' in data` logo após, sem `if not data`).
  - Comparações numéricas ou métodos de string sobre valores não validados (`priority < 1` com string; `value.startsWith(...)` com número) → `TypeError` → 500 (ou queda do processo em callback Node).
  - Conversões `int()`/`float()`/`parseInt` de query string sem tratamento.
  - Regras de criação (tamanho mínimo, categoria válida) ausentes na atualização do mesmo recurso.
  - Validadores utilitários existentes mas não usados.
  - Buscas: `get_json\(\)\s*\n\s*\w+\s*=\s*\w+\.get` (multiline), `req\.body\.\w+`, `(int|float)\(request\.args`
  - Exemplo (Python): `data = request.get_json(); status = data.get("status")` (sem corpo → `AttributeError` → 500)
  - Exemplo (JavaScript): `if (!req.body.code) return res.sendStatus(400); if (req.body.code.startsWith('X'))` (número → exceção)
- **Não confundir com:** validação centralizada por schema (`marshmallow`, `joi`, `pydantic`) aplicada antes do uso.
- **Impacto:** Erros 500 em entradas comuns, dados inválidos persistidos, comportamento diferente entre endpoints do mesmo recurso, possível queda do processo.
- **Recomendação:** Validador reutilizável por entidade aplicado em create e update, checando corpo, presença, tipo e faixa e devolvendo 400 com as mesmas mensagens já usadas.
- **Resolve com:** T-11.

## AP-14 — Generic Error Handling

- **Severidade:** MEDIUM
- **Descrição:** Tratamento de erro genérico e repetido: `except:`/`except Exception` que engole ou devolve `str(e)`, callbacks que ignoram `err`, ausência de handler central.
- **Sinais de detecção:**
  - `except:` sem tipo; `except Exception as e: return {"erro": str(e)}, 500` (vaza detalhes internos); `pass` em `except`.
  - Mesmo `try/except` envolvendo cada handler inteiro, copiado em todas as funções.
  - JavaScript: callback `(err, ...) =>` que não lê `err`; `catch (e) {}` vazio; respostas de sucesso mesmo após erro.
  - Nenhum `@app.errorhandler`/`register_error_handler`/middleware `(err, req, res, next)` registrado.
  - Buscas: `except\s*:`, `except Exception as \w+:\s*\n\s*return.*str\(\w+\)` (multiline), `\(err[^)]*\)\s*=>\s*\{(?![^}]*err)`, `catch\s*\(\w*\)\s*\{\s*\}`
  - Exemplo (Python): `try: ... except Exception as e: return jsonify({"error": str(e)}), 500` em todas as views.
  - Exemplo (JavaScript): `db.run(sql, [id], (err) => { res.send('done'); });`
- **Não confundir com:** captura de exceção específica com tratamento real (`except ValueError: return 400`).
- **Escopo:** projeto (1 finding; `File:` = ocorrência mais representativa; demais em `Other occurrences`).
- **Impacto:** Falhas silenciosas, mensagens internas (SQL, paths) expostas ao cliente, impossibilidade de diagnosticar, status incorretos.
- **Recomendação:** Exceções de domínio + error handler central que mapeia para status; 500 genérico sem detalhes internos, com log no servidor; callbacks/promises sempre tratando erro.
- **Resolve com:** T-12.

## AP-15 — Duplicated Code

- **Severidade:** MEDIUM
- **Descrição:** Blocos idênticos ou quase idênticos repetidos em vários lugares, ou lógica reescrita apesar de já existir helper/método equivalente.
- **Sinais de detecção:**
  - Mesmo bloco de 5+ linhas (serialização de entidade, cálculo de regra, cadeia de validação) em 2+ funções/arquivos.
  - Método de model ou helper existente com a mesma lógica que não é chamado nos lugares duplicados.
  - Mesma lista de valores válidos repetida inline em vários pontos.
  - Procedimento: leia os handlers do mesmo recurso lado a lado; busque uma linha característica do bloco (ex.: a condição) com Grep e conte ocorrências.
  - Exemplo (Python): a mesma condição `if due and due < now and status not in ("closed", "archived")` em 5 rotas, existindo `Item.is_late()` no model.
  - Exemplo (JavaScript): o mesmo objeto `{ id: r.id, name: r.name, price: r.price, ... }` montado em 3 funções.
- **Não confundir com:** repetição trivial de 1–2 linhas (imports, `return jsonify(...)`).
- **Escopo:** 1 finding por bloco duplicado; `File:` = primeira ocorrência; demais em `Other occurrences`.
- **Impacto:** Correções aplicadas em um lugar e esquecidas nos outros; comportamento divergente; mais código para manter.
- **Recomendação:** Extrair para método de model/serializer/validador único e substituir todas as cópias.
- **Resolve com:** T-07, T-11 (serialização: T-04).

## AP-16 — Deprecated API Usage

- **Severidade:** MEDIUM
- **Descrição:** Uso de APIs obsoletas (deprecated, legadas ou removidas em versões recentes) da linguagem, framework ou bibliotecas, com equivalente moderno disponível.
- **Sinais de detecção:**
  - Qualquer padrão da tabela do ecossistema detectado em `deprecated-apis.md` (coluna "Como detectar").
  - Confirme que a versão resolvida na Fase 1 é igual ou posterior à da depreciação; se a versão não puder ser determinada, reporte indicando "a partir de <versão>".
  - Exemplos obsoleto → moderno:
    - Python 3.12+: `datetime.utcnow()` → `datetime.now(timezone.utc)` (busca: `utcnow\(`)
    - SQLAlchemy 2.x / Flask-SQLAlchemy 3.x: `Model.query.get(id)` → `db.session.get(Model, id)` (busca: `\.query\.get\(`)
    - Node.js: `new Buffer(data)` → `Buffer.from(data)` (busca: `new Buffer\(`)
    - Node.js: `url.parse(str)` → `new URL(str)` (busca: `url\.parse\(`)
    - Express 4: `req.param('id')` → `req.params.id` / `req.query.id` / `req.body.id` (busca: `req\.param\(`)
- **Não confundir com:** APIs apenas "não recomendadas" por estilo sem aviso oficial; uso compatível com a versão declarada antes da depreciação.
- **Escopo:** 1 finding por API obsoleta (não por arquivo); `File:` = primeira ocorrência em ordem de caminho; demais em `Other occurrences`. Description cita a API obsoleta, a versão em que foi depreciada e o substituto.
- **Impacto:** Avisos em runtime, quebra ao atualizar dependências/runtime, comportamento sutilmente diferente (ex.: datetimes ingênuos vs. com fuso).
- **Recomendação:** Substituir pelo equivalente moderno da tabela, preservando o formato de saída serializado.
- **Resolve com:** T-13.

## AP-17 — Magic Numbers / Strings

- **Severidade:** LOW
- **Descrição:** Literais com significado de regra de negócio espalhados no código, sem nome.
- **Sinais de detecção:**
  - Números em condições/cálculos de regra: limiares (`> 10000`), percentuais (`* 0.05`), faixas (`1..5`), prazos (`days=7`), limites de tamanho.
  - Listas de valores válidos (status, papéis, categorias) inline, principalmente quando repetidas.
  - Strings de estado comparadas literalmente em vários pontos (`== "approved"`), prefixos mágicos (`startsWith("9")`).
  - Constantes definidas em módulo utilitário mas não usadas, com os literais repetidos no código.
  - Buscas: `(?i)(>|<|>=|<=|==)\s*\d{2,}`, `\*\s*0\.\d+`, `in\s*\[\s*["']\w+["']\s*,`, `startsWith\(\s*["']`
  - Exemplo (Python): `if total > 5000: discount = total * 0.05`
  - Exemplo (JavaScript): `if (!['new', 'paid', 'shipped'].includes(status))`
- **Não confundir com:** `0`, `1`, `-1` como índices/incrementos; códigos HTTP; porta/host no módulo de config; valores em seeds de dados.
- **Impacto:** Regras difíceis de localizar e alterar com segurança; divergência quando uma cópia muda e outra não.
- **Recomendação:** Constantes nomeadas/enums em módulo de constantes da camada de modelo; reutilizar constantes já existentes.
- **Resolve com:** T-14.

## AP-18 — Poor Naming

- **Severidade:** LOW
- **Descrição:** Identificadores que não comunicam intenção: abreviações de 1–3 letras, sufixos numéricos, nomes que sombreiam builtins, nomes enganosos.
- **Sinais de detecção:**
  - Variáveis de 1–3 letras fora de laços curtos/lambdas (`u`, `e`, `p`, `cc`, `cid`).
  - Sufixos numéricos (`p1`…`p5`, `cursor2`, `cursor3`, `data2`).
  - Parâmetros/variáveis que sombreiam builtins: Python `id`, `type`, `list`, `dict`, `input`, `filter`, `format`; JS `name` global em browser, `event`.
  - Nomes enganosos ou pejorativos (`fakeHash`, `doStuff`, `tmp`, `manager` que faz tudo).
  - Campos de request crípticos (`usr`, `eml`) — registrar, mas a correção é só interna (contrato).
  - Buscas: `\b(let|const|var)\s+[a-z]{1,2}\s*=`, `\b\w+[2-9]\s*=`, `def \w+\((id|type|list|input|filter)\b`
  - Exemplo (JavaScript): `let a = req.body.acct; let n = req.body.nm;`
  - Exemplo (Python): `def find(id): ...`, `c1 = ...; c2 = ...; c3 = ...`
- **Não confundir com:** índices de laço (`i`, `j`), `e`/`err` em `catch`, convenções do ecossistema (`db`, `app`, `req`, `res`).
- **Impacto:** Leitura lenta, erros por confusão de variáveis, sombras de builtins causando bugs sutis.
- **Recomendação:** Renomear internamente com nomes de domínio; manter nomes externos do contrato e mapear no controller.
- **Resolve com:** T-15.

## AP-19 — Unused Imports / Dead Code

- **Severidade:** LOW
- **Descrição:** Imports, funções, classes, variáveis ou módulos inteiros nunca referenciados.
- **Sinais de detecção:**
  - Para cada nome importado, busque usos no próprio arquivo; zero usos além do import = não usado.
  - Para cada função/classe/export de nível de módulo, busque o nome no projeto inteiro; só a definição = código morto.
  - Variáveis atribuídas e nunca lidas; serviços/utilitários inteiros que ninguém importa.
  - Procedimento: Grep `^(from .+ )?import .+` / `require\(` por arquivo; depois Grep de cada nome com `-w`.
  - Exemplo (Python): `import os, sys, json` sem uso de `os`, `sys` ou `json`.
  - Exemplo (JavaScript): `const { helperA, helperB } = require('./helpers');` com `helperB` nunca chamado.
- **Não confundir com:** imports com efeito colateral intencional (registro de models, `import models` para criar tabelas); exports públicos de biblioteca; `__init__.py` que reexporta.
- **Escopo:** projeto (1 finding; `File:` = primeira ocorrência; demais em `Other occurrences`).
- **Impacto:** Ruído na leitura, falsa impressão de funcionalidade existente, dependências carregadas à toa.
- **Recomendação:** Remover imports/código morto; se o utilitário for útil, passar a usá-lo e eliminar a duplicata.
- **Resolve com:** T-16.

## AP-20 — Print/Console Logging

- **Severidade:** LOW
- **Descrição:** `print`/`console.log` usados como mecanismo de log em código de aplicação, sem níveis nem destino configurável.
- **Sinais de detecção:**
  - `print(` em módulos da aplicação (rotas, controllers, models, services); `console.log(`/`console.error(` em código de servidor.
  - Buscas: `^\s*print\(`, `console\.(log|error|warn)\(`
  - Exemplo (Python): `print("Order created: " + str(order_id))`
  - Exemplo (JavaScript): ``console.log(`[LOG] saved ${key}`)``
- **Não confundir com:** saída de scripts de linha de comando (resumo de seed/CLI); uso de `logging`/logger estruturado.
- **Escopo:** projeto (1 finding; `File:` = primeira ocorrência; demais em `Other occurrences`). Se o print expõe dado sensível, reporte também AP-04.
- **Impacto:** Logs sem nível/contexto, impossíveis de filtrar ou desligar; risco de vazar dados; poluição de stdout em produção.
- **Recomendação:** Logger da stdlib (`logging` em Python; logger encapsulado em módulo próprio em Node) com níveis, sem dados sensíveis.
- **Resolve com:** T-16.
