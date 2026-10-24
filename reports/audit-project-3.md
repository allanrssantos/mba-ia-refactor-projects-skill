================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 13 | LOW: 7

## Findings

### [CRITICAL] Hardcoded Credentials
File: app.py:13
Description: `app.config['SECRET_KEY']` definido com o literal `'super-secret-key-123'` no código versionado.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões/cookies assinados; a rotação da chave exige novo deploy.
Recommendation: Mover para um módulo de configuração que leia `SECRET_KEY` do ambiente, com default de desenvolvimento não secreto, e documentar em `.env.example` (T-01).

### [CRITICAL] Hardcoded Credentials
File: services/notification_service.py:10
Other occurrences: services/notification_service.py:7-9
Description: Credenciais SMTP literais no construtor de `NotificationService`: `email_user = 'taskmanager@gmail.com'` e `email_password = 'senha123'`, além de host e porta fixos.
Impact: A conta de e-mail fica exposta a quem lê o repositório; comprometimento permite envio de mensagens em nome da aplicação.
Recommendation: Ler host, porta, usuário e senha SMTP de variáveis de ambiente no módulo de configuração e tratar o valor exposto como comprometido (T-01).

### [CRITICAL] God Class / God Method
File: routes/report_routes.py:1-223
Description: O módulo do blueprint `reports` registra rotas, executa consultas ORM e aplica regras de negócio para dois domínios distintos: relatórios agregados (`summary_report` com ~90 linhas, `user_report`) e o CRUD completo de categorias (`get_categories`, `create_category`, `update_category`, `delete_category`).
Impact: Impossível testar a agregação de relatórios ou o CRUD de categorias isoladamente; mudanças em um domínio arriscam o outro; o blueprint "reports" esconde o recurso `categories`.
Recommendation: Separar em model/service de relatórios + controller de relatórios e em model + controller + routes de categorias, com o composition root montando as dependências (T-03, apoiado por T-07 e T-08).

### [CRITICAL] Sensitive Data Exposure
File: models/user.py:21
Description: `User.to_dict()` inclui a chave `'password'` com o hash armazenado; o método é devolvido ao cliente em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` (routes/user_routes.py:33, 85, 129, 209).
Impact: Qualquer cliente obtém os hashes MD5 de todos os usuários, viabilizando ataque offline imediato; violação de LGPD.
Recommendation: Serializador com allow-list de campos públicos (sem `password`) usado por todas as respostas de usuário (T-04, T-16).

### [CRITICAL] Insecure Password Storage
File: models/user.py:29
Other occurrences: models/user.py:32
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara o MD5 sem sal.
Impact: Vazamento do banco expõe as senhas em segundos via tabelas rainbow; senhas reutilizadas comprometem outras contas.
Recommendation: Usar KDF com sal já disponível na stack (`werkzeug.security.generate_password_hash`/`check_password_hash`), aceitando o formato MD5 legado na verificação com rehash transparente no próximo login (T-06).

### [HIGH] Business Logic in Controller/Route
File: routes/report_routes.py:12-101
Other occurrences: routes/report_routes.py:103-155, routes/report_routes.py:157-223
Description: `summary_report` executa 15+ consultas, percorre todas as tasks calculando atrasos e produtividade por usuário e monta o relatório inteiro; `user_report` repete a agregação por usuário; o CRUD de categorias acessa `db.session` diretamente.
Impact: Regras de relatório não são reutilizáveis nem testáveis sem HTTP; qualquer ajuste de métrica exige editar a camada de transporte.
Recommendation: Mover agregações para um service/model de relatórios e o CRUD para model de categorias, deixando controllers finos (T-07, com T-11 para validação).

### [HIGH] Business Logic in Controller/Route
File: routes/task_routes.py:85-154
Other occurrences: routes/task_routes.py:11-63, routes/task_routes.py:156-223, routes/task_routes.py:240-271, routes/task_routes.py:273-299
Description: `create_task` (70 linhas) encadeia 8+ validações, consulta `User`/`Category`, converte datas e tags e persiste; `get_tasks`, `update_task`, `search_tasks` e `task_stats` montam consultas ORM, serializam e calculam estatísticas inline.
Impact: Regras de task (status, prioridade, atraso) duplicadas entre handlers e impossíveis de testar sem subir o Flask.
Recommendation: Extrair validação para validador de task, consultas e cálculos para o model `Task`/service, controllers só orquestram entrada → chamada → resposta (T-07, T-11).

### [HIGH] Business Logic in Controller/Route
File: routes/user_routes.py:42-90
Other occurrences: routes/user_routes.py:92-132, routes/user_routes.py:134-151, routes/user_routes.py:153-183, routes/user_routes.py:185-211
Description: `create_user` valida 6 campos, checa unicidade de e-mail, hasheia a senha e persiste; `update_user` repete as regras; `delete_user` remove tasks dependentes; `get_user_tasks` recalcula atraso; `login` implementa autenticação inline.
Impact: Fluxo de autenticação e regras de usuário presos à rota, sem reuso nem teste unitário.
Recommendation: Controller fino delegando a validador de usuário e métodos de model/service (criação, autenticação, remoção com dependentes) (T-07, T-11).

### [HIGH] Tight Coupling / Missing Dependency Injection
File: app.py:9-31
Description: `app = Flask(__name__)` é criado e configurado em tempo de import, sem `create_app()`; config inline, `CORS(app)`, `db.init_app(app)`, blueprints e `db.create_all()` executam ao importar o módulo (o `seed.py` depende disso via `from app import app, db`).
Impact: Impossível instanciar a aplicação com outra config (testes, outro banco) sem efeitos colaterais de import; criação de schema ocorre a cada import.
Recommendation: Fábrica `create_app(config)` como composition root, mantendo `app.py` como entry point fino que expõe `app` e `db` para o seed (T-08).

### [HIGH] Tight Coupling / Missing Dependency Injection
File: services/notification_service.py:15
Description: `send_email` instancia `smtplib.SMTP(self.email_host, self.email_port)` dentro do método com host fixo `smtp.gmail.com`, e o serviço instancia a si mesmo sem receber dependências.
Impact: Não é possível substituir o transporte de e-mail em testes nem trocar o provedor sem editar a regra.
Recommendation: Receber cliente SMTP/config pelo construtor a partir do composition root; manter interface simples (T-08).

### [HIGH] Insecure Runtime Configuration
File: app.py:34
Other occurrences: app.py:11, app.py:15
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` fixo no código; `CORS(app)` sem lista de origens; URI do banco `sqlite:///tasks.db` hardcoded sem override.
Impact: Debugger interativo do Werkzeug exposto em todas as interfaces permite execução remota de código; qualquer origem pode fazer requisições cross-origin.
Recommendation: Ler `DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS` e `DATABASE_URI` de config/env com defaults seguros (`debug=False`, host local), mantendo a porta 5000 como default (T-01).

### [MEDIUM] N+1 Queries
File: routes/report_routes.py:55-56
Other occurrences: routes/report_routes.py:161-163, routes/report_routes.py:15-28
Description: `for u in users: Task.query.filter_by(user_id=u.id).all()` executa uma consulta por usuário; `get_categories` faz um `count()` por categoria; `summary_report` dispara 12 `count()` sequenciais por status/prioridade onde um `GROUP BY` bastaria.
Impact: Latência do relatório cresce linearmente com usuários e categorias; carga desnecessária no banco.
Recommendation: Agregar no banco com `GROUP BY` e JOIN/consulta em lote, montando a resposta em memória com a mesma forma (T-10).

### [MEDIUM] N+1 Queries
File: routes/task_routes.py:41-57
Other occurrences: routes/task_routes.py:275-287
Description: `get_tasks` faz `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` para cada task do laço; `task_stats` executa 5 `count()` e depois carrega todas as tasks para contar atrasadas.
Impact: Listagem principal executa 1 + 2N consultas; estatísticas percorrem a tabela inteira em memória.
Recommendation: Eager loading (`joinedload`/`selectinload`) dos relacionamentos `user` e `category` já declarados no model e agregação de status no banco (T-10).

### [MEDIUM] N+1 Queries
File: routes/user_routes.py:22
Description: `'task_count': len(u.tasks)` dentro do laço sobre `User.query.all()` dispara o carregamento lazy do backref `tasks` para cada usuário.
Impact: `GET /users` executa 1 + N consultas.
Recommendation: Contagem agregada por usuário com `GROUP BY` ou `selectinload`, preservando a chave `task_count` (T-10).

### [MEDIUM] Missing or Inconsistent Input Validation
File: routes/report_routes.py:196-197
Other occurrences: routes/report_routes.py:173-180
Description: `update_category` usa `data = request.get_json()` seguido de `'name' in data` sem checar corpo nulo (`TypeError` → 500); `create_category`/`update_category` aceitam `color` sem validar formato apesar de `is_valid_color` existir em `utils/helpers.py:52`.
Impact: Corpo vazio derruba o handler com 500; cores inválidas são persistidas.
Recommendation: Validador de categoria aplicado em create e update, checando corpo, presença e formato (T-11).

### [MEDIUM] Missing or Inconsistent Input Validation
File: routes/task_routes.py:113
Other occurrences: routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/task_routes.py:167-169
Description: `priority < 1 or priority > 5` comparado sem checar tipo (string ou `None` → `TypeError` → 500); `int(priority)`/`int(user_id)` da query string em `search_tasks` sem tratamento (`ValueError` → 500); `len(data['title'])` sem checar tipo; `process_task_data` em `utils/helpers.py:57` existe e não é usado.
Impact: Entradas comuns (`"priority": "alta"`, `?priority=x`) produzem 500 em vez de 400.
Recommendation: Validador reutilizável de task (corpo, presença, tipo, faixa) para create, update e filtros de busca, devolvendo 400 com as mensagens já usadas (T-11).

### [MEDIUM] Missing or Inconsistent Input Validation
File: routes/user_routes.py:102-103
Other occurrences: routes/user_routes.py:115, routes/user_routes.py:124-125, routes/user_routes.py:61, routes/user_routes.py:106
Description: `update_user` aceita `name` vazio e `active` de qualquer tipo sem validar; `len(data['password'])` sem checar tipo; regex de e-mail duplicada inline enquanto `validate_email` em `utils/helpers.py:19` não é usado.
Impact: Dados inválidos persistidos e 500 por `TypeError` em payloads malformados; regras divergem entre criação e atualização.
Recommendation: Validador de usuário único aplicado em create, update e login, reaproveitando os helpers existentes (T-11).

### [MEDIUM] Generic Error Handling
File: routes/task_routes.py:62-63
Other occurrences: routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, routes/task_routes.py:137, routes/task_routes.py:151, routes/task_routes.py:204, routes/task_routes.py:221, routes/task_routes.py:236, routes/user_routes.py:87, routes/user_routes.py:130 (+5 more)
Description: `get_tasks` envolve o handler inteiro em `try/except:` sem tipo devolvendo `'Erro interno'`; 16 blocos `except:`/`except Exception` repetidos nas rotas e helpers; nenhum `@app.errorhandler` registrado em `app.py`.
Impact: Falhas reais (bugs de tipo, erros de banco) viram 500 genéricos sem diagnóstico; status incorretos mascaram problemas de validação.
Recommendation: Exceções de domínio (`NotFound`, `ValidationError`, `Conflict`) + error handler central mapeando para status, 500 genérico com log no servidor (T-12).

### [MEDIUM] Duplicated Code
File: routes/report_routes.py:34-36
Other occurrences: routes/report_routes.py:132-134, routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:284-286, routes/user_routes.py:171-180
Description: O bloco `if t.due_date: if t.due_date < datetime.utcnow(): if t.status != 'done' and t.status != 'cancelled'` aparece em 6 handlers, embora `Task.is_overdue()` em `models/task.py:50-60` implemente exatamente essa regra e nunca seja chamado.
Impact: Mudar a regra de atraso exige editar 6 lugares; divergência garantida.
Recommendation: Usar `Task.is_overdue()` em todos os pontos e remover as cópias (T-07).

### [MEDIUM] Duplicated Code
File: routes/report_routes.py:67
Other occurrences: routes/report_routes.py:151, routes/task_routes.py:296
Description: A expressão `round((x / total) * 100, 2) if total > 0 else 0` é repetida em 3 handlers enquanto `calculate_percentage` em `utils/helpers.py:14` tem a mesma lógica e é importado em `report_routes.py:7` sem uso.
Impact: Arredondamento e tratamento de divisão por zero podem divergir entre endpoints.
Recommendation: Chamar o helper único em todos os cálculos de `completion_rate` (T-07).

### [MEDIUM] Duplicated Code
File: routes/task_routes.py:17-28
Other occurrences: routes/user_routes.py:162-169
Description: Serialização manual de task campo a campo (`task_data['id'] = t.id` ... `tags.split(',')`) replicando `Task.to_dict()` de `models/task.py:23-36`, com subconjuntos diferentes de chaves em `get_tasks` e `get_user_tasks`.
Impact: Novo campo no model exige editar 3 serializações; respostas inconsistentes entre endpoints.
Recommendation: Serializer único de task (com variantes `overdue`, `user_name`, `category_name`) reaproveitado por todos os handlers (T-04, T-07).

### [MEDIUM] Duplicated Code
File: routes/task_routes.py:96-114
Other occurrences: routes/task_routes.py:166-184, routes/user_routes.py:61-72, routes/user_routes.py:106-121
Description: Cadeia de validação de título/status/prioridade copiada entre `create_task` e `update_task`; validação de e-mail/senha/role copiada entre `create_user` e `update_user`; `utils/helpers.py:57-108` (`process_task_data`) e `:19` (`validate_email`) já implementam parte dessas regras sem uso.
Impact: Regras de create e update já divergem (mensagens diferentes, checagens ausentes no update) e tendem a divergir mais.
Recommendation: Validadores por entidade únicos aplicados em create e update (T-11).

### [MEDIUM] Deprecated API Usage
File: models/category.py:11
Other occurrences: models/task.py:15, models/task.py:16, models/task.py:52, models/user.py:14, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:133, routes/task_routes.py:31 (+11 more)
Description: `datetime.utcnow()` (e `default=datetime.utcnow` nas colunas) está deprecated desde o Python 3.12 (o venv do projeto usa 3.12.10); substituto: `datetime.now(timezone.utc)` ou helper `datetime.now(timezone.utc).replace(tzinfo=None)` para manter os datetimes ingênuos já gravados.
Impact: `DeprecationWarning` em runtime e remoção futura; mistura de datetimes com e sem fuso quebra comparações de atraso.
Recommendation: Helper único de "agora" na camada de modelo usado por colunas, comparações e relatórios, preservando o formato serializado (T-13).

### [MEDIUM] Deprecated API Usage
File: routes/report_routes.py:105
Other occurrences: routes/report_routes.py:192, routes/report_routes.py:213, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188 (+5 more)
Description: `Model.query.get(id)` é API legada do SQLAlchemy 2.0 (`LegacyAPIWarning`; o venv tem SQLAlchemy 2.1.6 com Flask-SQLAlchemy 3.1.1); substituto: `db.session.get(Model, id)`. Complementar: `relationship(backref=...)` em `models/task.py:20-21` é legado — preferir `back_populates`.
Impact: Avisos em runtime e quebra em versões futuras do ORM.
Recommendation: Centralizar busca por id nos models com `db.session.get` (T-13).

### [LOW] Magic Numbers / Strings
File: models/task.py:39
Other occurrences: models/task.py:46
Description: Lista `['pending', 'in_progress', 'done', 'cancelled']` e faixa `p >= 1 and p <= 5` inline nos métodos de validação do model, enquanto `VALID_STATUSES` e afins existem em `utils/helpers.py:110-116` sem uso.
Impact: Regras de domínio definidas em dois lugares que não se referenciam.
Recommendation: Módulo de constantes da camada de modelo (status, faixa de prioridade) reutilizado pelo model e validadores (T-14).

### [LOW] Magic Numbers / Strings
File: routes/report_routes.py:45
Other occurrences: routes/report_routes.py:129, routes/report_routes.py:84-88, routes/report_routes.py:180
Description: Janela `timedelta(days=7)`, limiar `t.priority <= 2` como "alta prioridade", mapeamento de rótulos `critical/high/medium/low/minimal` e cor padrão `'#000000'` escritos inline (cor repetida em `models/category.py:10`).
Impact: Parâmetros de relatório difíceis de localizar e alterar com segurança.
Recommendation: Constantes nomeadas (`RECENT_ACTIVITY_DAYS`, `HIGH_PRIORITY_THRESHOLD`, `PRIORITY_LABELS`, `DEFAULT_COLOR`) no módulo de constantes (T-14).

### [LOW] Magic Numbers / Strings
File: routes/task_routes.py:110
Other occurrences: routes/task_routes.py:96, routes/task_routes.py:99, routes/task_routes.py:113, routes/task_routes.py:167, routes/task_routes.py:169, routes/task_routes.py:177, routes/task_routes.py:182
Description: Lista de status válidos, limites de título `3`/`200` e faixa de prioridade `1..5` repetidos inline nos handlers, apesar de `MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH`, `VALID_STATUSES` existirem em `utils/helpers.py:110-116`.
Impact: Alterar um limite exige caçar literais em vários handlers.
Recommendation: Reutilizar as constantes existentes a partir do módulo de constantes (T-14).

### [LOW] Magic Numbers / Strings
File: routes/user_routes.py:71
Other occurrences: routes/user_routes.py:64, routes/user_routes.py:115, routes/user_routes.py:120, routes/user_routes.py:61, routes/user_routes.py:106
Description: Lista de roles `['user', 'admin', 'manager']`, tamanho mínimo de senha `4` e regex de e-mail repetidos inline, com `VALID_ROLES`/`MIN_PASSWORD_LENGTH` já definidos em `utils/helpers.py:111-114`.
Impact: Regras de conta espalhadas e duplicadas.
Recommendation: Constantes nomeadas e regex único no validador de usuário (T-14).

### [LOW] Poor Naming
File: routes/report_routes.py:24-28
Description: Variáveis com sufixo numérico `p1`…`p5` para contagens por prioridade, mapeadas depois para `critical`…`minimal` em `report_routes.py:84-88`.
Impact: Leitura exige correlacionar manualmente número e rótulo; fácil trocar índices.
Recommendation: Nomear pelo significado (`critical_count`, …) ou construir o dicionário diretamente a partir de `PRIORITY_LABELS` (T-15).

### [LOW] Unused Imports / Dead Code
File: app.py:7
Other occurrences: routes/report_routes.py:7-8, routes/task_routes.py:7, routes/user_routes.py:6, models/task.py:3, models/task.py:38-60, models/user.py:34-38, utils/helpers.py:1-116, services/notification_service.py:1-48
Description: `import os, sys, json` sem uso em `app.py`; `json, os, sys, time` em `task_routes`; `hashlib, json` em `user_routes`; `format_date`, `calculate_percentage`, `json` em `report_routes`; `json` em `models/task.py`; métodos `validate_status`/`validate_priority`/`is_overdue`/`is_admin` nunca chamados; `utils/helpers.py` e `services/notification_service.py` nunca importados por nenhum módulo; `marshmallow`, `requests` e `python-dotenv` declarados em `requirements.txt` sem nenhum import.
Impact: Falsa impressão de camadas de serviço/utilitário funcionais; ruído que esconde o código realmente ativo.
Recommendation: Remover imports mortos; passar a usar os helpers/métodos de model úteis (substituindo as duplicatas) e remover o restante; manifestos permanecem intocados (T-16).

### [LOW] Print/Console Logging
File: routes/task_routes.py:149
Other occurrences: routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39, utils/helpers.py:41
Description: `print(f"Task criada: ...")` e similares usados como log em rotas, serviço e helpers (os `print` de `seed.py` são saída legítima de CLI e não foram contados).
Impact: Logs sem nível nem destino configurável, impossíveis de filtrar em produção.
Recommendation: `logging.getLogger(__name__)` com níveis adequados, sem dados sensíveis (T-16).

================================
Total: 31 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
