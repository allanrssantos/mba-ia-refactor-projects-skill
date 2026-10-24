================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 11 | HIGH: 9 | MEDIUM: 7 | LOW: 6

## Findings

### [CRITICAL] Hardcoded Credentials
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` define a chave de sessão/assinatura como literal versionado.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões e cookies assinados; a rotação da chave exige novo deploy.
Recommendation: Ler `SECRET_KEY` de variável de ambiente em módulo de configuração, com default de desenvolvimento não secreto, e documentar em `.env.example` (T-01).

### [CRITICAL] Hardcoded Credentials
File: controllers.py:289
Description: O handler `health_check` repete o literal `"secret_key": "minha-chave-super-secreta-123"` dentro do dicionário de resposta.
Impact: O segredo fica duplicado em dois arquivos, de modo que trocar um deles mantém o valor comprometido no outro.
Recommendation: Remover o literal e qualquer referência ao segredo fora do módulo de configuração (T-01).

### [CRITICAL] SQL Injection
File: app.py:61-69
Description: A rota `/admin/query` lê `dados.get("sql", "")` do corpo da requisição e chama `cursor.execute(query)` com o texto recebido.
Impact: Qualquer cliente executa SQL arbitrário sobre o banco (leitura, alteração e destruição de todas as tabelas) sem autenticação.
Recommendation: Proteger a rota por guard administrativo e registrar a execução de SQL arbitrário como risco residual (T-05, T-02).

### [CRITICAL] SQL Injection
File: models.py:109-111
Other occurrences: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-161 (+8 more)
Description: `login_usuario` monta `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`; todas as demais consultas do módulo concatenam valores com `+`, inclusive `LIKE '%" + termo + "%'` em `buscar_produtos`.
Impact: Bypass de login com `' OR '1'='1`, leitura e remoção arbitrária de dados e corrupção do banco, exploráveis remotamente sem autenticação.
Recommendation: Parametrizar todas as consultas com placeholders `?` e tupla de parâmetros; em `buscar_produtos`, montar lista de condições e de parâmetros em paralelo (T-02).

### [CRITICAL] God Class / God Method
File: controllers.py:1-292
Description: Módulo único com handlers de produtos, usuários, login, pedidos, relatório e health; lê request e escreve response, aplica cadeias de validação e regras (categorias, status, notificações) e executa SQL direto em `health_check` (linhas 266-273).
Impact: Nenhuma regra é testável sem HTTP; qualquer mudança em um domínio arrisca os demais no mesmo arquivo.
Recommendation: Separar por domínio em controllers finos por entidade, com regras e queries movidas para a camada de modelo e um composition root montando as dependências (T-03).

### [CRITICAL] God Class / God Method
File: models.py:1-314
Description: Módulo de 314 linhas com CRUD e SQL de 4 tabelas (`produtos`, `usuarios`, `pedidos`, `itens_pedido`) mais regras de negócio: checagem de estoque e cálculo de total em `criar_pedido` (133-169) e faixas de desconto em `relatorio_vendas` (256-262).
Impact: Acesso a dados e regra de negócio inseparáveis; impossível testar o cálculo de pedido ou do relatório sem SQLite real.
Recommendation: Dividir em um model por entidade e um service para orquestração de pedido e relatório, mantendo as assinaturas usadas pelos controllers (T-03).

### [CRITICAL] Sensitive Data Exposure
File: controllers.py:285-289
Description: `health_check` devolve ao cliente `"ambiente"`, `"db_path": "loja.db"`, `"debug": True` e `"secret_key": "minha-chave-super-secreta-123"`.
Impact: Endpoint público entrega a chave de assinatura e a configuração interna a qualquer chamador, viabilizando forja de sessão e reconhecimento do ambiente.
Recommendation: Reduzir a resposta do health a status e conectividade, removendo valores de configuração e segredo (T-04, T-16).

### [CRITICAL] Sensitive Data Exposure
File: models.py:83
Other occurrences: models.py:99
Description: `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha": row["senha"]` no dicionário devolvido por `/usuarios` e `/usuarios/<int:id>`.
Impact: Qualquer cliente lista as senhas de todos os usuários em texto puro, inclusive a do admin.
Recommendation: Serializador de usuário com allow-list de campos públicos (id, nome, email, tipo, criado_em) (T-04).

### [CRITICAL] Unprotected Admin/Destructive Endpoint
File: app.py:47-57
Other occurrences: app.py:59-78
Description: `/admin/reset-db` executa `DELETE FROM itens_pedido`, `pedidos`, `produtos` e `usuarios` sem `WHERE`, e `/admin/query` executa SQL arbitrário; nenhuma das duas rotas tem decorator, middleware ou checagem de token.
Impact: Qualquer pessoa na rede apaga o banco inteiro ou executa SQL livre com uma única requisição POST, agravado pelo bind em `0.0.0.0`.
Recommendation: Manter as rotas registradas e protegê-las por guard com `ADMIN_TOKEN` do ambiente comparado em tempo constante via header `X-Admin-Token`, respondendo 403 sem token válido (T-05).

### [CRITICAL] Insecure Password Storage
File: database.py:75-83
Description: O seed grava `("Admin", "admin@loja.com", "admin123", "admin")` e demais usuários com a senha literal diretamente na coluna `senha`.
Impact: Senhas iniciais ficam legíveis no banco e no repositório; a conta admin é comprometida por qualquer leitura do arquivo `loja.db`.
Recommendation: Gravar o seed com hash gerado por KDF com sal (ex.: `werkzeug.security.generate_password_hash`, já disponível com o Flask) (T-06).

### [CRITICAL] Insecure Password Storage
File: models.py:126-129
Other occurrences: models.py:109-111
Description: `criar_usuario` insere a senha exatamente como recebida e `login_usuario` autentica por igualdade direta `AND senha = '...'` no SQL.
Impact: Vazamento do banco expõe todas as senhas imediatamente e permite reutilização em outros serviços.
Recommendation: Hash com sal no cadastro e verificação com `check_password_hash`, aceitando o formato legado em texto puro com rehash transparente no próximo login (T-06).

### [HIGH] Business Logic in Controller/Route
File: app.py:47-57
Other occurrences: app.py:59-78
Description: As views `reset_database` e `executar_query` obtêm conexão com `get_db()`, executam SQL e fazem `db.commit()` diretamente no entry point.
Impact: Operações de dados ficam presas à camada de transporte e fora de qualquer model, sem possibilidade de teste ou reutilização.
Recommendation: Mover as operações administrativas para a camada de modelo e deixar as rotas apenas delegando (T-07).

### [HIGH] Business Logic in Controller/Route
File: controllers.py:188-220
Other occurrences: controllers.py:24-62, controllers.py:64-96, controllers.py:237-255, controllers.py:264-292
Description: `criar_pedido` valida payload, interpreta o dicionário de erro do model e dispara efeitos colaterais (`ENVIANDO EMAIL/SMS/PUSH`); `criar_produto` tem cadeia de 9 `if` com lista de categorias; `atualizar_status_pedido` decide notificações por status; `health_check` executa 4 consultas SQL.
Impact: Regras de validação, notificação e contagem não são reutilizáveis nem testáveis sem subir o Flask, e divergem entre criação e atualização.
Recommendation: Controllers finos (entrada → validação → chamada → resposta) com regras e queries em models/services e validadores reutilizáveis (T-07, T-11).

### [HIGH] Global Mutable State
File: database.py:4-10
Description: `db_connection = None` em nível de módulo, reatribuído com `global db_connection` dentro de `get_db()`, criando um singleton `sqlite3.connect(db_path, check_same_thread=False)` compartilhado entre todas as threads do servidor.
Impact: Transações de requisições concorrentes se misturam na mesma conexão (um `commit` persiste escritas parciais de outra requisição) e é impossível isolar o banco em testes.
Recommendation: Criar a conexão por requisição (ou por app) no composition root e injetá-la nos models, removendo o global (T-08).

### [HIGH] Tight Coupling / Missing Dependency Injection
File: app.py:6-9
Other occurrences: app.py:49, app.py:66
Description: `app = Flask(__name__)` é criado e configurado no import do módulo, sem `create_app()`; os handlers administrativos chamam `get_db()` diretamente.
Impact: Não há como instanciar a aplicação com configuração ou banco diferentes para teste; importar o módulo já cria o app com config fixa.
Recommendation: Fábrica `create_app()` que cria config, conexão e registra rotas, mantendo o entry point `app.py` fino (T-08).

### [HIGH] Tight Coupling / Missing Dependency Injection
File: controllers.py:208-210
Other occurrences: controllers.py:248-250, controllers.py:266
Description: Notificações simuladas inline (`print("ENVIANDO EMAIL: ...")`, `"ENVIANDO SMS"`, `"ENVIANDO PUSH"`, `"NOTIFICAÇÃO: ..."`) dentro dos handlers e `health_check` chamando `get_db()` pulando o model.
Impact: Integrações não podem ser substituídas por dublês em teste e qualquer troca de canal de notificação exige editar o fluxo HTTP.
Recommendation: Serviço de notificação injetável com interface simples e acesso a dados exclusivamente via model (T-08).

### [HIGH] Tight Coupling / Missing Dependency Injection
File: database.py:5-10
Description: `db_path = "loja.db"` fixo e `sqlite3.connect(db_path, ...)` dentro do getter global, sem possibilidade de receber caminho ou conexão de fora.
Impact: Testes e ambientes distintos sempre apontam para o mesmo arquivo `loja.db` ao lado do código.
Recommendation: Receber o caminho do banco da configuração e expor uma função de conexão injetável pelo composition root (T-08).

### [HIGH] Missing Transaction / Callback Pyramid
File: models.py:133-169
Other occurrences: models.py:65-70
Description: `criar_pedido` checa estoque (144) e só depois decrementa (163-166), faz `INSERT` em `pedidos`, N `INSERT` em `itens_pedido` e N `UPDATE` em `produtos` com um único `db.commit()` ao fim e sem `rollback`; `deletar_produto` apaga o produto sem tratar `itens_pedido` dependentes (o fallback `"Desconhecido"` em 196 admite os órfãos).
Impact: Uma exceção no meio do laço deixa pedido sem itens ou estoque parcialmente baixado, que é persistido pelo próximo `commit` de outra requisição na conexão global; pedidos ficam com itens órfãos.
Recommendation: Envolver as escritas do pedido em transação explícita com rollback em erro, validar e baixar estoque atomicamente, e tratar dependentes ao remover produto (T-09).

### [HIGH] Insecure Runtime Configuration
File: app.py:8
Other occurrences: app.py:9, app.py:88
Description: `app.config["DEBUG"] = True`, `CORS(app)` sem lista de origens e `app.run(host="0.0.0.0", port=5000, debug=True)` fixos no código.
Impact: Debugger interativo do Werkzeug exposto a toda a rede permite execução remota de código; qualquer site pode fazer requisições cross-origin à API.
Recommendation: Ler debug, host, porta e origens CORS de configuração com defaults seguros (`debug=False`, host local, porta 5000 preservada) (T-01).

### [HIGH] Insecure Runtime Configuration
File: database.py:5
Description: Caminho do banco `db_path = "loja.db"` hardcoded, sem override por variável de ambiente.
Impact: Não é possível apontar para outro banco (teste, outro diretório) sem editar código.
Recommendation: Ler `DATABASE_PATH` da configuração com default `loja.db` (T-01).

### [MEDIUM] N+1 Queries
File: models.py:177-199
Other occurrences: models.py:209-231, models.py:139-166, models.py:239-254
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam, para cada pedido, um `SELECT` em `itens_pedido` e, para cada item, um `SELECT nome FROM produtos` (`cursor2`/`cursor3`); `criar_pedido` consulta o produto duas vezes por item; `relatorio_vendas` faz 5 `COUNT`/`SUM` sequenciais onde um `GROUP BY` bastaria.
Impact: Latência de listagem cresce com 1 + N + N·M consultas; relatórios e listagens de pedidos degradam com o volume.
Recommendation: JOIN de pedidos, itens e produtos com montagem em memória preservando forma e ordem da resposta; agregação por status em uma consulta (T-10).

### [MEDIUM] Missing or Inconsistent Input Validation
File: controllers.py:169-171
Other occurrences: controllers.py:239-240, controllers.py:118-121, controllers.py:43-46, controllers.py:87-90, controllers.py:195-201
Description: `login` e `atualizar_status_pedido` chamam `dados.get(...)` sem checar corpo nulo; `buscar_produtos` faz `float(preco_min)` sem tratamento; `preco < 0` e `estoque < 0` comparam valores sem checar tipo; `atualizar_produto` omite as regras de tamanho de nome e categoria válida presentes em `criar_produto`; itens de pedido não têm `produto_id`/`quantidade` validados.
Impact: Requisições sem corpo, com string em campo numérico ou com item malformado viram 500 (`AttributeError`, `TypeError`, `ValueError`, `KeyError`), e atualização aceita dados que a criação rejeita.
Recommendation: Validador reutilizável por entidade aplicado em create e update, checando corpo, presença, tipo e faixa e devolvendo 400 com as mensagens já usadas (T-11).

### [MEDIUM] Generic Error Handling
File: controllers.py:10-12
Other occurrences: controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165, controllers.py:185-186, controllers.py:218-220 (+6 more)
Description: Todos os 16 handlers de `controllers.py` e `executar_query` em `app.py` repetem `except Exception as e: return jsonify({"erro": str(e)}), 500`; não há `@app.errorhandler` registrado.
Impact: Mensagens internas (erros SQL, nomes de tabela) são devolvidas ao cliente e erros de entrada recebem 500 em vez de 400.
Recommendation: Exceções de domínio e error handler central mapeando para status, com 500 genérico sem detalhes e log no servidor (T-12).

### [MEDIUM] Duplicated Code
File: models.py:12-21
Other occurrences: models.py:31-40, models.py:304-313
Description: O mesmo dicionário de serialização de produto (`id`, `nome`, `descricao`, `preco`, `estoque`, `categoria`, `ativo`, `criado_em`) é montado em três funções.
Impact: Mudança de campo precisa ser replicada em três pontos, com risco de divergência entre listagem, busca e detalhe.
Recommendation: Extrair um serializador único de produto na camada de modelo e usá-lo nas três funções (T-04, T-07).

### [MEDIUM] Duplicated Code
File: models.py:79-86
Other occurrences: models.py:95-102
Description: O dicionário de serialização de usuário é duplicado em `get_todos_usuarios` e `get_usuario_por_id`.
Impact: A correção da exposição de senha precisa ser feita em dois lugares.
Recommendation: Serializador único de usuário com allow-list de campos (T-04, T-07).

### [MEDIUM] Duplicated Code
File: models.py:178-200
Other occurrences: models.py:211-232
Description: Montagem de pedido com itens e nome do produto (`cursor2`/`cursor3`) é idêntica em `get_pedidos_usuario` e `get_todos_pedidos`.
Impact: Correção do N+1 ou de formato precisa ser aplicada duas vezes.
Recommendation: Extrair a montagem de pedidos para uma função única recebendo o filtro (T-07).

### [MEDIUM] Duplicated Code
File: controllers.py:28-46
Other occurrences: controllers.py:72-90
Description: A cadeia de validação de produto (corpo, `nome`, `preco`, `estoque`, negativos) é copiada entre `criar_produto` e `atualizar_produto`, já com divergência (tamanho de nome e categoria só na criação).
Impact: As duas rotas já se comportam de forma diferente para o mesmo recurso e qualquer nova regra tende a ser esquecida em uma delas.
Recommendation: Validador único de produto reutilizado nas duas operações (T-11).

### [LOW] Magic Numbers / Strings
File: controllers.py:52
Other occurrences: controllers.py:47-50, controllers.py:242, controllers.py:247-249
Description: Lista `categorias_validas` inline, limites `len(nome) < 2` / `> 200`, lista de status `["pendente", "aprovado", "enviado", "entregue", "cancelado"]` e comparações literais `== "aprovado"` / `== "cancelado"`.
Impact: Regras de catálogo e de estado ficam espalhadas e difíceis de alterar com segurança.
Recommendation: Constantes nomeadas para categorias, status e limites em módulo de constantes da camada de modelo (T-14).

### [LOW] Magic Numbers / Strings
File: models.py:257-262
Other occurrences: models.py:247-253, models.py:150
Description: Faixas de desconto `> 10000` / `* 0.1`, `> 5000` / `* 0.05`, `> 1000` / `* 0.02` e strings de status `'pendente'`, `'aprovado'`, `'cancelado'` embutidas nas consultas e no insert.
Impact: Regra comercial do relatório fica escondida em literais e os status duplicam a lista usada no controller.
Recommendation: Extrair faixas de desconto e status para constantes nomeadas reutilizadas por controllers e models (T-14).

### [LOW] Poor Naming
File: controllers.py:14
Other occurrences: controllers.py:56, controllers.py:64, controllers.py:98, controllers.py:160
Description: Parâmetro `id` em `buscar_produto`, `atualizar_produto`, `deletar_produto` e variável local `id = models.criar_produto(...)` sombreiam o builtin `id`.
Impact: Leitura confusa e risco de bugs sutis ao precisar do builtin no mesmo escopo.
Recommendation: Renomear internamente para `produto_id`/`usuario_id`, mantendo o parâmetro de rota `<int:id>` do contrato (T-15).

### [LOW] Poor Naming
File: models.py:187
Other occurrences: models.py:24, models.py:54, models.py:65, models.py:89, models.py:191, models.py:219, models.py:223
Description: Cursores com sufixo numérico `cursor2`/`cursor3` e parâmetros `id` que sombreiam o builtin em `get_produto_por_id`, `atualizar_produto`, `deletar_produto` e `get_usuario_por_id`.
Impact: Nomes não comunicam intenção e dificultam acompanhar os laços aninhados.
Recommendation: Nomes de domínio (`itens_cursor`, `produto_id`) na refatoração interna (T-15).

### [LOW] Unused Imports / Dead Code
File: database.py:2
Other occurrences: models.py:2
Description: `import os` em `database.py` e `import sqlite3` em `models.py` nunca são usados nos respectivos arquivos.
Impact: Ruído e falsa impressão de uso de ambiente ou de conexão direta no módulo de models.
Recommendation: Remover os imports não usados (T-16).

### [LOW] Print/Console Logging
File: controllers.py:8
Other occurrences: controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208, controllers.py:209, controllers.py:210 (+4 more)
Description: `print(...)` usado como log em todos os fluxos (listagem, criação, erros, login com e-mail, notificações) e em `reset_database` em `app.py:56`.
Impact: Logs sem nível nem destino configurável, impossíveis de filtrar ou desligar em produção.
Recommendation: Substituir por `logging` da stdlib com níveis e sem dados sensíveis (T-16).

================================
Total: 33 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
