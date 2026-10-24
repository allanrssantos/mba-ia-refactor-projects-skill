================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 6 | HIGH: 6 | MEDIUM: 3 | LOW: 6

## Findings

### [CRITICAL] Hardcoded Credentials
File: src/utils.js:3-4
Other occurrences: src/utils.js:2, src/utils.js:5
Description: Objeto `config` literal com `dbPass: "senha_super_secreta_prod_123"` e `paymentGatewayKey: "pk_live_1234567890abcdef"` (prefixo `pk_live_` de chave de produção), além de `dbUser` e `smtpUser` fixos, tudo versionado no repositório.
Impact: Qualquer pessoa com acesso ao repositório obtém a chave do gateway de pagamento e a senha de banco de produção; rotação exige novo deploy.
Recommendation: Mover para módulo de configuração que lê `process.env` com defaults de desenvolvimento não secretos, documentar em `.env.example` e tratar os valores expostos como comprometidos (T-01).

### [CRITICAL] God Class / God Method
File: src/AppManager.js:1-141
Description: A classe `AppManager` abre a conexão SQLite no construtor, cria o schema e os seeds em `initDb()`, registra as 3 rotas em `setupRoutes()` e contém toda a regra de negócio (checkout, pagamento, matrícula, relatório financeiro, exclusão) para 5 tabelas distintas.
Impact: Nenhuma parte pode ser testada isoladamente; qualquer mudança em uma entidade arrisca efeitos colaterais em todas as outras e impede reuso.
Recommendation: Separar por domínio em models (acesso a dados), controllers (fluxo HTTP) e routes (mapeamento), com composition root montando as dependências (T-03, apoiado por T-08 e T-07).

### [CRITICAL] Sensitive Data Exposure
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava no log o número completo do cartão recebido no checkout e a chave do gateway de pagamento.
Impact: Quem lê os logs (stdout, agregadores, CI) obtém números de cartão em texto puro e a chave live do gateway; violação direta de PCI-DSS e LGPD.
Recommendation: Remover o log ou mascarar o cartão (`****4444`) e nunca interpolar segredos de configuração em mensagens de log (T-04, T-16).

### [CRITICAL] Unprotected Admin/Destructive Endpoint
File: src/AppManager.js:80
Description: `app.get('/api/admin/financial-report', ...)` devolve receita por curso e nome dos alunos matriculados sem nenhum middleware de autenticação nem checagem de header/token no handler.
Impact: Qualquer cliente na rede extrai o faturamento da empresa e dados pessoais de todos os alunos com um simples GET.
Recommendation: Manter a rota registrada e protegê-la por guard configurável (`ADMIN_TOKEN` no ambiente + header `X-Admin-Token` comparado em tempo constante; sem token válido → 403) (T-05).

### [CRITICAL] Insecure Password Storage
File: src/AppManager.js:68
Other occurrences: src/AppManager.js:18
Description: No checkout a senha é gravada como `badCrypto(p || "123456")` (hash caseiro reversível) e o seed insere o usuário `Leonan` com `pass` literal `'123'` em texto puro na coluna de senha.
Impact: Um vazamento do banco expõe as senhas imediatamente ou em segundos; reutilização de senha compromete outras contas dos usuários.
Recommendation: Usar KDF com sal do `node:crypto` (`scrypt`/`pbkdf2`) na criação e no seed, com verificação compatível com o formato legado e rehash transparente (T-06).

### [CRITICAL] Insecure Password Storage
File: src/utils.js:17-23
Description: `badCrypto(pwd)` concatena 10000 vezes os 2 primeiros caracteres do base64 da senha e devolve `substring(0, 10)`: não é hash, é uma transformação determinística, sem sal e trivialmente colidível (toda senha com os mesmos 1–2 primeiros bytes gera o mesmo valor).
Impact: Qualquer senha pode ser "quebrada" ou colidida instantaneamente; a função dá uma falsa sensação de segurança.
Recommendation: Substituir por hashing com sal e iterações altas via `node:crypto` (`scrypt` ou `pbkdf2`), mantendo verificação do formato legado para dados existentes (T-06).

### [HIGH] Business Logic in Controller/Route
File: src/AppManager.js:28-78
Other occurrences: src/AppManager.js:80-129, src/AppManager.js:131-137
Description: O handler de `POST /api/checkout` (51 linhas) valida payload, busca curso e usuário, cria usuário, decide aprovação do pagamento (`cc.startsWith("4")`), grava matrícula, pagamento e auditoria e atualiza cache; o handler do relatório financeiro (50 linhas) faz 4 níveis de consultas e agrega receita; o `DELETE` executa SQL direto.
Impact: Regras de checkout e de relatório não são reutilizáveis nem testáveis sem HTTP; qualquer alteração de regra exige tocar a camada de transporte.
Recommendation: Controllers finos (entrada → validação → chamada → resposta) delegando a services/models com as queries e as regras (T-07, com T-11 para validação).

### [HIGH] Global Mutable State
File: src/utils.js:9-10
Other occurrences: src/utils.js:14
Description: `let globalCache = {}` e `let totalRevenue = 0` no escopo do módulo; `logAndCache()` muta `globalCache[key] = data` a cada checkout e o objeto é exportado e compartilhado entre todas as requisições.
Impact: Cache cresce sem limite (vazamento de memória), comportamento difere por processo/worker e testes passam a depender de ordem de execução.
Recommendation: Remover o cache não lido ou encapsulá-lo em um serviço criado no composition root e injetado, com limite de tamanho (T-08).

### [HIGH] Tight Coupling / Missing Dependency Injection
File: src/app.js:5-14
Description: O entry point cria o `express()`, registra middleware, instancia `new AppManager()`, inicializa o banco e chama `app.listen()` em tempo de import, sem função fábrica (`createApp()`), impossibilitando subir a aplicação sem abrir a porta.
Impact: Nenhum teste pode montar a aplicação com dependências substitutas; o boot e a composição ficam indissociáveis.
Recommendation: Extrair `createApp(deps)` como composition root que recebe/instancia banco e serviços, deixando o entry point apenas com o `listen` (T-08).

### [HIGH] Tight Coupling / Missing Dependency Injection
File: src/AppManager.js:7
Other occurrences: src/AppManager.js:45-46
Description: O construtor instancia `new sqlite3.Database(':memory:')` com caminho fixo, e o "gateway de pagamento" é decidido inline por `cc.startsWith("4")` dentro do handler, em vez de um serviço injetável.
Impact: Impossível testar com banco ou gateway falso; trocar a infraestrutura exige editar a regra de negócio.
Recommendation: Receber a conexão e um serviço de pagamento pelo construtor, criados na fábrica da aplicação (T-08).

### [HIGH] Missing Transaction / Callback Pyramid
File: src/AppManager.js:37-77
Other occurrences: src/AppManager.js:131-137
Description: O checkout encadeia `db.get → db.get → db.run(users) → db.run(enrollments) → db.run(payments) → db.run(audit_logs)` em 6 níveis de callbacks sem `BEGIN/COMMIT/ROLLBACK`, com `return` de erro entre as escritas; o `DELETE FROM users WHERE id = ?` não remove matrículas nem pagamentos, e a própria resposta admite que "ficaram sujos no banco".
Impact: Falha parcial deixa matrícula sem pagamento ou usuário criado sem matrícula; exclusões acumulam órfãos em `enrollments` e `payments`; fluxo ilegível e propenso a resposta duplicada/ausente.
Recommendation: Promisificar o driver e agrupar as escritas em transação com rollback via `async/await`; ao excluir usuário, remover dependentes na mesma transação (T-09).

### [HIGH] Insecure Runtime Configuration
File: src/utils.js:6
Description: `port: 3000` fixo no objeto `config`, sem leitura de `process.env.PORT` nem de qualquer variável de ambiente para porta, host ou caminho do banco.
Impact: Impossível alterar porta/ambiente sem editar código; deploy em container ou múltiplas instâncias exige fork do arquivo.
Recommendation: Ler porta e demais parâmetros de `process.env` no módulo de configuração, mantendo `3000` como default (T-01).

### [MEDIUM] N+1 Queries
File: src/AppManager.js:89-106
Description: `courses.forEach` executa `db.all(enrollments WHERE course_id = ?)` por curso e, dentro, `enrollments.forEach` executa `db.get(users)` e `db.get(payments)` por matrícula: 1 + N + 2·N·M consultas para montar o relatório.
Impact: Latência do relatório cresce linearmente com cursos e matrículas; carga desnecessária no banco e risco de timeout conforme a base cresce.
Recommendation: Substituir por uma consulta com `JOIN` entre courses, enrollments, users e payments (ou agregação com `GROUP BY`) e montar o relatório em memória preservando forma e ordem da resposta (T-10).

### [MEDIUM] Missing or Inconsistent Input Validation
File: src/AppManager.js:35
Other occurrences: src/AppManager.js:46, src/AppManager.js:132
Description: A validação checa apenas presença de `usr`, `eml`, `c_id` e `card` (sem tipo, formato ou faixa); `cc.startsWith("4")` em :46 lança `TypeError` se `card` vier como número; `req.params.id` em :132 é usado sem checar se é inteiro.
Impact: Payload com `card` numérico derruba o processo Node (exceção dentro de callback), dados inválidos são persistidos e o comportamento varia entre endpoints.
Recommendation: Validador reutilizável por entidade aplicado no controller, checando corpo, presença, tipo e faixa e devolvendo 400 com as mensagens já usadas (T-11).

### [MEDIUM] Generic Error Handling
File: src/AppManager.js:133-135
Other occurrences: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106
Description: O callback do `DELETE` ignora `err` e responde sucesso sempre; em :38 erro de banco é mascarado como 404; em :57, :92, :104 e :106 `err` não é lido e `enrollments.length` explode se a consulta falhar; não há middleware de erro `(err, req, res, next)` registrado.
Impact: Falhas silenciosas, status incorretos, impossibilidade de diagnosticar problemas e possível queda do processo.
Recommendation: Erros de domínio mapeados por um error handler central do Express; 500 genérico sem detalhes internos com log no servidor; toda operação de banco tratando erro (T-12).

### [LOW] Magic Numbers / Strings
File: src/AppManager.js:46
Other occurrences: src/AppManager.js:48, src/AppManager.js:54, src/AppManager.js:68, src/AppManager.js:108
Description: Regra de aprovação `cc.startsWith("4")`, estados `"PAID"`/`"DENIED"` comparados literalmente em 4 pontos e senha padrão `"123456"` inline.
Impact: Regra de pagamento e estados ficam difíceis de localizar e alterar sem divergência entre cópias.
Recommendation: Extrair para constantes nomeadas (`PAYMENT_STATUS`, prefixo aprovado) em módulo de constantes da camada de modelo (T-14).

### [LOW] Magic Numbers / Strings
File: src/utils.js:19
Other occurrences: src/utils.js:22
Description: Iterações `10000` e truncamento `substring(0, 10)` sem nome dentro de `badCrypto`.
Impact: Parâmetros de segurança opacos; o leitor não sabe o que os números representam.
Recommendation: Constantes nomeadas (ou remoção junto com a função ao adotar KDF padrão) (T-14).

### [LOW] Poor Naming
File: src/AppManager.js:29-33
Other occurrences: src/AppManager.js:4, src/AppManager.js:26, src/AppManager.js:52
Description: Variáveis de 1–3 letras `u`, `e`, `p`, `cid`, `cc` para dados de domínio; `self = this` para contornar `function(err)`; `enrId`; classe genérica `AppManager` que faz tudo; campos de request crípticos `usr`, `eml`, `pwd`, `c_id` (contrato — registrar, não alterar).
Impact: Leitura lenta e risco de confundir variáveis (`e` é e-mail, não erro) em um handler já extenso.
Recommendation: Renomear internamente para nomes de domínio (`userName`, `email`, `password`, `courseId`, `cardNumber`) mantendo as chaves externas do contrato mapeadas no controller (T-15).

### [LOW] Poor Naming
File: src/utils.js:17
Description: Função `badCrypto` com nome pejorativo que admite ser inadequada; módulo `utils` genérico agrupando config, cache e hash sem coesão.
Impact: Nome não comunica intenção e normaliza código inseguro; `utils` vira depósito de responsabilidades distintas.
Recommendation: Substituir por módulo `security/password` com `hashPassword`/`verifyPassword` e separar config em módulo próprio (T-15).

### [LOW] Unused Imports / Dead Code
File: src/AppManager.js:2
Other occurrences: src/utils.js:2, src/utils.js:3, src/utils.js:5, src/utils.js:10, src/utils.js:25
Description: `totalRevenue` importado em `AppManager.js` e nunca usado; em `utils.js` `totalRevenue`, `globalCache` (exportado, nunca importado e nunca lido), `dbUser`, `dbPass` e `smtpUser` não são referenciados em lugar algum (banco em memória sem credenciais, sem SMTP).
Impact: Ruído de leitura e falsa impressão de funcionalidades (cache, SMTP, receita total) que não existem.
Recommendation: Remover imports, exports e chaves de config mortos (T-16).

### [LOW] Print/Console Logging
File: src/AppManager.js:45
Other occurrences: src/app.js:13, src/utils.js:13
Description: `console.log` usado como mecanismo de log no handler de checkout, no boot (`Frankenstein LMS rodando...`) e em `logAndCache` (`[LOG] Salvando no cache`), sem níveis nem destino configurável.
Impact: Logs impossíveis de filtrar ou desligar em produção; o de :45 ainda vaza dados sensíveis (ver Sensitive Data Exposure).
Recommendation: Logger encapsulado em módulo próprio com níveis e sem dados sensíveis (T-16).

================================
Total: 21 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
