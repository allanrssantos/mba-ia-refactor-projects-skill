# MVC Guidelines — arquitetura-alvo da Fase 3

> Carregado na Fase 3. Define as camadas, o que cada uma pode e não pode fazer, a estrutura-alvo por ecossistema, como adaptar ao nível de organização existente e as regras de preservação de contrato.

## 1. Princípios

1. **Separação por responsabilidade:** transporte HTTP (routes/controllers) não conhece SQL; dados (models) não conhecem request/response.
2. **Direção das dependências:** `entry point → composition root → routes → controllers → services/models → database`. Camadas internas nunca importam camadas externas (model não importa controller; controller não importa o entry point).
3. **Dependências injetadas:** conexão, configuração e serviços externos são criados no composition root e passados adiante.
4. **Comportamento externo idêntico:** a refatoração muda a estrutura, não o contrato (§7).
5. **Mudança mínima suficiente:** evolua o que existe quando já é coerente; crie camadas novas só quando faltarem.

## 2. Camadas: responsabilidades e proibições

| Camada | Responsabilidade | Proibido |
|---|---|---|
| **config** | Ler variáveis de ambiente com defaults seguros de desenvolvimento; expor um objeto/módulo de settings (porta, host, debug, URL/caminho do banco, segredos, flags, origens CORS, `ADMIN_TOKEN`) | Regra de negócio; segredo real como default; ler `os.environ`/`process.env` fora deste módulo |
| **models** | Entidades, acesso a dados (SQL parametrizado ou ORM), conexão/sessão/schema/seed inicial, regras intrínsecas da entidade (ex.: "está atrasado?", "total do pedido"), serialização pública (allow-list) | Conhecer request/response, status HTTP ou framework web; imprimir/logar dados sensíveis |
| **services** (opcional, parte da camada Model) | Casos de uso que cruzam várias entidades ou integrações (fluxo transacional de checkout, notificações, relatórios agregados) | Conhecer request/response; ser chamado pelos models |
| **views / routes** | Mapear método + path → função do controller, anexar middlewares/guards por rota, preservar a ordem de registro e os prefixos | SQL, regra de negócio, validação de payload, montagem de resposta |
| **controllers** | Fluxo da requisição: extrair entrada (body/query/params) → validar → chamar model/service → montar resposta e status | SQL direto; regra de negócio pesada; `try/except` genérico que engole erros; acessar conexão global |
| **middlewares** | Error handler centralizado (exceções de domínio → status), guard administrativo, logging de requisição | Regra de negócio |
| **composition root** | Fábrica `create_app()` / `createApp()`: carrega config, cria conexão/extensões, instancia models/serviços, injeta nos controllers, registra rotas e error handler | Ser importado por camadas internas; conter lógica de endpoint |
| **entry point** | Arquivo fino no caminho do comando de boot original: chama o composition root e sobe o servidor com host/porta/debug da config | Qualquer outra lógica |
| **utils** (opcional) | Funções puras sem estado (validadores, constantes, logger) | Acesso a banco, estado global mutável |

Nomenclatura: APIs JSON usam `routes/`; use `views/` só se o projeto renderiza templates ou já usa esse nome.

## 3. Estrutura-alvo por ecossistema

### 3.1 Python / Flask (monolito → criar camadas em `src/`)

```text
<projeto>/
├── app.py                      # entry point fino (mesmo caminho do boot original)
├── <seed/scripts originais>    # continuam funcionando com o mesmo comando
├── requirements.txt            # inalterado
├── .env.example
└── src/
    ├── __init__.py
    ├── app.py                  # composition root: create_app(config=None)
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    ├── models/
    │   ├── __init__.py
    │   ├── database.py         # conexão, schema, seed inicial
    │   └── <entidade>_model.py
    ├── services/               # opcional
    ├── controllers/
    │   ├── __init__.py
    │   └── <entidade>_controller.py
    ├── routes/
    │   ├── __init__.py
    │   └── <entidade>_routes.py   # Blueprints
    ├── middlewares/
    │   ├── __init__.py
    │   ├── error_handler.py
    │   └── auth.py             # guard admin
    └── utils/                  # opcional: validators.py, constants.py, logger.py
```

Notas Flask:
- Entry point: `from src.app import create_app` e `app = create_app()` no nível de módulo (scripts que fazem `from app import app` continuam funcionando); `if __name__ == "__main__": app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)`.
- Todo subdiretório de `src/` é pacote (`__init__.py`); imports absolutos `from src.models...`, que funcionam com `python app.py` executado da raiz.
- Use Blueprints sem alterar paths; se agrupar por prefixo, o path final deve ser idêntico ao original, incluindo conversores (`<int:id>`).
- Flask-SQLAlchemy: `db = SQLAlchemy()` em `models/database.py` e `db.init_app(app)` + `db.create_all()` dentro de `create_app()` sob `app.app_context()`. URIs SQLite relativas são resolvidas na pasta `instance/` derivada do pacote da aplicação: confirme que o arquivo de banco continua no mesmo local após mover a fábrica.
- `sqlite3` da stdlib com arquivo: caminho do banco vem da config com o mesmo default relativo de antes; conexão por requisição (`flask.g` + `teardown_appcontext`) em vez de global.

### 3.2 Node.js / Express (monolito → criar camadas em `src/`)

```text
<projeto>/
├── package.json                # "start" inalterado
├── .env.example
└── src/
    ├── app.js                  # entry point + composition root: createApp(); listen se require.main === module
    ├── config/index.js
    ├── models/
    │   ├── database.js         # conexão, schema, seed, wrapper Promise (util.promisify)
    │   └── <entidade>Model.js
    ├── services/               # opcional: casos de uso multi-entidade/transacionais
    ├── controllers/<entidade>Controller.js
    ├── routes/<dominio>Routes.js   # express.Router() montado com o mesmo prefixo
    ├── middlewares/
    │   ├── errorHandler.js
    │   └── adminGuard.js
    └── utils/                  # opcional: logger.js, constants.js
```

Notas Express:
- O arquivo apontado por `scripts.start`/`main` continua sendo o entry point; se ele já está em `src/`, vira composition root + `listen`.
- `createApp({ db, config })` retorna o `app` sem chamar `listen` (testável); o `listen` fica no bloco `if (require.main === module)` ou no entry point.
- Mantenha `express.json()` e demais middlewares globais na mesma ordem; o error handler `(err, req, res, next)` é o último `app.use`.
- Respostas em texto puro (`res.send("...")`) continuam texto puro; status idênticos.
- Banco em memória: a conexão é única por processo — crie-a no composition root e injete (não por requisição); o seed roda antes de aceitar requisições.

### 3.3 Outras stacks (mapeamento)

| Stack | config | models | routes | controllers | middlewares/erro |
|---|---|---|---|---|---|
| FastAPI | `config.py` (pydantic-settings se já declarado, senão `os.environ`) | `models/`, `repositories/` | `routers/` (`APIRouter`) | funções de rota finas chamando `services/` | `exception_handler` |
| Django | `settings.py` lendo env | `models.py` por app | `urls.py` | views finas + `services.py` | middleware / `handler500` |
| Go (gin/echo) | `internal/config` | `internal/repository` | `internal/http/routes.go` | `internal/http/handlers` | middleware de recover |
| Spring | `application.yml` + env | `repository`/`entity` | anotações no controller | `@RestController` fino + `@Service` | `@ControllerAdvice` |

## 4. Adaptação ao nível de organização (classificação da Fase 1)

| Classificação | Estratégia |
|---|---|
| `monolith` | Criar a estrutura canônica de §3 em `src/`. Distribuir o código por domínio (um model, um controller e um arquivo de rotas por entidade/agrupamento coerente). Os arquivos antigos da raiz são removidos ou viram o entry point fino. |
| `partial-layers` | **Evolução incremental.** Manter no lugar os diretórios de camada que já existem e são coerentes (não mover `models/`/`routes/` para `src/` por estética). Adicionar ao lado deles o que falta: `config/`, `controllers/` (extraindo o fluxo das rotas), `middlewares/` (error handler, guard), composition root (`create_app`) no módulo de entrada. Rotas passam a delegar aos controllers; regra duplicada vai para model/service; utilitários mortos são removidos ou passam a ser usados. |
| `layered` | Apenas transformações pontuais dos findings, sem mover arquivos. |

Regras comuns:
- Scripts auxiliares (seed, migrations) continuam funcionando **com o mesmo comando**. Se importam símbolos do entry point (ex.: `app`, `db`), esses símbolos continuam exportados ali (ou o script é atualizado no mesmo passo).
- Arquivos de banco gerados em runtime continuam no mesmo caminho padrão.
- Não crie camadas vazias "para cumprir tabela": cada diretório criado contém código usado.
- Remover um arquivo antigo só depois que todos os seus usos foram migrados.

## 5. Configuração

- Um único módulo lê o ambiente. Nomes de variáveis em MAIÚSCULAS (`PORT`, `HOST`, `DEBUG`, `DATABASE_URL`/`DB_PATH`, `SECRET_KEY`, `CORS_ORIGINS`, `ADMIN_TOKEN`, chaves de integração).
- Defaults: porta e caminho do banco **iguais aos originais** (o boot sem `.env` precisa funcionar); `DEBUG` padrão `false`; `HOST` padrão `127.0.0.1` (ou o original, se o README documentar acesso externo); segredos sem default real — gere em runtime (`secrets.token_hex(32)` / `crypto.randomBytes(32).toString('hex')`) ou use string vazia quando o valor só for exibido/logado.
- `ADMIN_TOKEN` sem default: ausente → rotas admin respondem 403.
- `CORS_ORIGINS` padrão: o comportamento original (ex.: `*`) lido da config, para não quebrar clientes, mas configurável.
- Carregar `.env` só com biblioteca **já declarada** (ex.: `python-dotenv` presente no manifesto). Sem ela, apenas variáveis de ambiente do processo.
- Criar `.env.example` na raiz do projeto com todas as variáveis, finalidade e default de desenvolvimento (sem valores reais).

## 6. Error handling centralizado

- Python/Flask: exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`, `ForbiddenError`) em `models`/`utils`; `register_error_handlers(app)` em `middlewares/error_handler.py` mapeando cada uma para o **mesmo status e corpo** que o endpoint usava; `Exception` genérica → 500 com mensagem genérica e log no servidor (sem `str(e)` ao cliente).
- Node/Express: classes de erro com `status`; handlers `async` envolvidos por `asyncHandler` (ou `try/catch` que chama `next(err)`); middleware final `(err, req, res, next)` respondendo no formato original (texto ou JSON).
- O formato do corpo de erro de cada endpoint (chave `erro`/`error`/texto puro, mensagem) é preservado.

## 7. Preservação de contrato e mudanças permitidas (lista fechada)

**Deve permanecer idêntico:** paths (com conversores de tipo de parâmetro), métodos, status codes de sucesso e de erro, `Content-Type` (texto continua texto), chaves de topo das respostas, nomes dos campos de request (inclusive nomes ruins na borda — renomeie só internamente), mensagens de erro de validação, ordem de registro das rotas, comando de boot, porta padrão.

**Mudanças permitidas — somente estas, e cada uma deve ser citada no bloco PHASE 3 (`Endpoint Check` com justificativa):**

1. **Remover campos sensíveis das respostas** (senha, hash de senha, segredos, configuração interna). O status não muda.
2. **Guard administrativo (ADR de segurança):** endpoints classificados como AP-05 continuam registrados, mas passam por um guard:
   - Se `ADMIN_TOKEN` não estiver configurado **ou** o header `X-Admin-Token` não coincidir (comparação em tempo constante: `hmac.compare_digest` / `crypto.timingSafeEqual`), responder **403** com corpo no estilo do projeto (JSON com a mesma chave de erro usada nos outros endpoints, ou texto puro se o projeto responde texto).
   - Com token válido, o comportamento original é mantido (mesmo status e corpo da baseline).
   - Nada de remover a rota. Se o endpoint executa SQL arbitrário, ele segue como risco residual mesmo protegido.
3. **500 sem detalhe interno:** respostas de erro inesperado deixam de incluir `str(e)`/stack trace (o status 500 permanece).
4. **Correção de bug que antes gerava 5xx** para uma entrada inválida (ex.: corpo ausente) → passa a responder 400 com mensagem no estilo do projeto.

Qualquer outra diferença de status, path ou formato é regressão e precisa ser corrigida antes de concluir.

## 8. Checklist de conformidade (verificar ao final da Fase 3)

- [ ] Existe módulo de config e nenhum outro módulo lê o ambiente diretamente.
- [ ] Nenhum segredo literal no código (busca por padrões de AP-01 sem resultados fora de `.env.example`).
- [ ] Models concentram todo acesso a dados; controllers e routes não têm SQL/ORM.
- [ ] Routes só mapeiam método + path → controller (e guards).
- [ ] Controllers são finos: entrada → validação → model/service → resposta.
- [ ] Error handler central registrado; nenhum `except:`/`catch {}` genérico em controllers.
- [ ] Composition root único cria e injeta dependências; entry point fino no caminho original.
- [ ] Sem estado global mutável fora do composition root.
- [ ] Scripts auxiliares (seed) funcionam com o mesmo comando.
- [ ] `.env.example` documenta todas as variáveis.
