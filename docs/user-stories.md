# User Stories — Skill `refactor-arch`

> Derivadas de `SPEC.md` (fonte única da verdade) e de `docs/CHALLENGE.md` (enunciado original).
> Personas: **Mantenedor(a)** (opera a skill), **Avaliador(a)** (verifica o entregável), **Agente** (Claude Code executando a skill).
> Rastreabilidade: cada story indica os RF/CA da SPEC que cobre.

---

## Épico 1 — Análise manual

## US-01: Analisar manualmente o code-smells-project
Como Mantenedor(a)
Quero identificar e documentar os problemas do `code-smells-project/`
Para entender quais padrões a skill precisa detectar em um monolito Python/Flask

Cobre: RF-01, RF-02, RF-03, CA-05

### Critérios de aceite
```gherkin
Cenário: Distribuição mínima de severidade
  Dado o código original de code-smells-project (commit f50e265)
  Quando a análise manual for documentada
  Então existem no mínimo 5 problemas
  E no mínimo 1 é CRITICAL ou HIGH
  E no mínimo 2 são MEDIUM
  E no mínimo 2 são LOW

Cenário: Problema completo e rastreável
  Dado um problema documentado
  Então ele contém severidade, título, arquivo:linha, descrição e justificativa de relevância
  E a linha citada corresponde ao trecho descrito no código original
  E ele está mapeado para pelo menos 1 anti-pattern do catálogo da skill
```

## US-02: Analisar manualmente o ecommerce-api-legacy
Como Mantenedor(a)
Quero identificar e documentar os problemas do `ecommerce-api-legacy/`
Para garantir que a skill cubra uma stack Node.js/Express

Cobre: RF-01, RF-02, RF-03, CA-05

### Critérios de aceite
```gherkin
Cenário: Distribuição mínima de severidade
  Dado o código original de ecommerce-api-legacy
  Quando a análise manual for documentada
  Então existem no mínimo 5 problemas, com ≥ 1 CRITICAL/HIGH, ≥ 2 MEDIUM e ≥ 2 LOW
  E cada problema tem arquivo:linha e justificativa
```

## US-03: Analisar manualmente o task-manager-api
Como Mantenedor(a)
Quero identificar e documentar os problemas do `task-manager-api/`
Para provar que um projeto parcialmente organizado também tem problemas arquiteturais e de qualidade

Cobre: RF-01, RF-02, RF-03, CA-05

### Critérios de aceite
```gherkin
Cenário: Distribuição mínima de severidade
  Dado o código original de task-manager-api
  Quando a análise manual for documentada
  Então existem no mínimo 5 problemas, com ≥ 1 CRITICAL/HIGH, ≥ 2 MEDIUM e ≥ 2 LOW
  E ao menos 1 problema é arquitetural (não apenas de estilo), apesar da existência de models/, routes/, services/ e utils/
```

---

## Épico 2 — Construção da skill

## US-04: Criar o esqueleto da skill
Como Mantenedor(a)
Quero um diretório `code-smells-project/.claude/skills/refactor-arch/` com `SKILL.md` válido
Para que o Claude Code reconheça e invoque a skill com `/refactor-arch`

Cobre: RF-04, RF-05, RNF-05, R-01, CA-07

### Critérios de aceite
```gherkin
Cenário: Skill descoberta pelo Claude Code
  Dado o arquivo code-smells-project/.claude/skills/refactor-arch/SKILL.md
  E o frontmatter YAML contém "name: refactor-arch" e um campo "description"
  Quando executo "cd code-smells-project" e "claude \"/refactor-arch\""
  Então a skill é carregada e inicia a Fase 1

Cenário: Orquestração enxuta
  Dado o SKILL.md
  Então ele descreve as 3 fases em ordem (Análise, Auditoria, Refatoração)
  E indica qual arquivo de referência carregar em cada fase
  E todos os outros arquivos do diretório da skill são .md
```

## US-05: Implementar a Fase 1 — Análise
Como Mantenedor(a)
Quero que a skill detecte stack, domínio e arquitetura e imprima um resumo
Para ter uma visão correta do projeto antes da auditoria

Cobre: RF-07, RF-08, RF-09, CA-01

### Critérios de aceite
```gherkin
Cenário: Resumo no formato padrão
  Dado um projeto-alvo com a skill instalada
  Quando a Fase 1 é executada
  Então é impresso o bloco "PHASE 1: PROJECT ANALYSIS"
  E ele contém os campos Language, Framework, Dependencies, Domain, Architecture, Source files e DB tables

Cenário: Fase 1 é somente leitura
  Dado o working tree limpo ("git status" sem alterações no projeto)
  Quando a Fase 1 termina
  Então "git status" continua sem alterações no projeto
```

## US-06: Implementar a Fase 2 — Auditoria com pausa obrigatória
Como Mantenedor(a)
Quero um relatório de auditoria classificado por severidade e uma pausa antes de qualquer modificação
Para revisar os achados e decidir conscientemente se a refatoração deve acontecer

Cobre: RF-10 a RF-16, CA-02, CA-03, CA-12, CA-13, R-04

### Critérios de aceite
```gherkin
Cenário: Relatório completo e ordenado
  Dado que a Fase 1 terminou
  Quando a Fase 2 é executada
  Então é impresso o bloco "ARCHITECTURE AUDIT REPORT" seguindo o template de referência
  E cada finding tem severidade, título, "File: caminho:linha", Description, Impact e Recommendation
  E os findings aparecem na ordem CRITICAL, HIGH, MEDIUM, LOW
  E o Summary traz a contagem por severidade e o "Total" é igual ao número de findings listados

Cenário: Pausa antes de modificar arquivos
  Dado que o relatório foi impresso
  Então a skill exibe literalmente "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"
  E aguarda a resposta
  E "git status" não mostra nenhuma alteração em arquivos do projeto

Cenário: Recusa encerra sem alterações
  Dado que a pergunta de confirmação foi exibida
  Quando o operador responde "n"
  Então a skill encerra
  E nenhum arquivo do projeto é modificado
```

## US-07: Implementar a Fase 3 — Refatoração MVC com validação
Como Mantenedor(a)
Quero que a skill reestruture o projeto em MVC e prove que a aplicação continua funcionando
Para eliminar os problemas sem quebrar os clientes da API

Cobre: RF-17 a RF-22, RNF-01 a RNF-03, CA-04, CA-14

### Critérios de aceite
```gherkin
Cenário: Estrutura MVC criada
  Dado que o operador respondeu "y" à pergunta da Fase 2
  Quando a Fase 3 termina
  Então o projeto tem camadas identificáveis de config, models, views/routes, controllers, error handling centralizado e um entry point único
  E nenhum segredo permanece hardcoded no código

Cenário: Validação de boot e endpoints
  Dado o projeto refatorado
  Quando a skill sobe a aplicação e chama todos os endpoints originais
  Então a aplicação inicia sem exceções
  E todos os endpoints respondem com o status equivalente à baseline (sem 5xx, sem 404 de rota)
  E o bloco "PHASE 3: REFACTORING COMPLETE" lista a nova estrutura e o resultado de cada verificação

Cenário: Falha de validação não é mascarada
  Dado que algum endpoint falha na validação
  Então a skill corrige e revalida, ou reporta a verificação como reprovada
  E não declara sucesso sem evidência

Cenário: Adaptação ao nível de organização
  Dado um projeto já parcialmente organizado em camadas
  Quando a Fase 3 é executada
  Então a skill reorganiza/melhora as camadas existentes em vez de recriar tudo do zero
```

## US-08: Escrever a referência de Análise de projeto
Como Agente
Quero heurísticas de detecção de linguagem, framework, banco e arquitetura
Para executar a Fase 1 corretamente em qualquer stack

Cobre: RF-06 (área 1), RF-23, CA-08

### Critérios de aceite
```gherkin
Cenário: Heurísticas acionáveis e agnósticas
  Dado o arquivo de referência de análise de projeto
  Então ele lista sinais concretos (manifests como requirements.txt/package.json, imports, padrões de registro de rotas, arquivos e drivers de banco)
  E cobre ao menos Python e JavaScript/Node.js sem depender de nomes de arquivos dos 3 projetos
  E define como estimar domínio, arquitetura atual e contagem de arquivos-fonte
```

## US-09: Escrever o Catálogo de anti-patterns
Como Agente
Quero um catálogo com sinais de detecção e severidade
Para classificar findings de forma consistente na Fase 2

Cobre: RF-06 (área 2), RF-13, CA-09

### Critérios de aceite
```gherkin
Cenário: Tamanho e distribuição
  Dado o catálogo de anti-patterns
  Então ele contém no mínimo 8 anti-patterns
  E há pelo menos 1 de cada severidade: CRITICAL, HIGH, MEDIUM, LOW
  E as severidades seguem a escala literal da SPEC (seção 5.1)

Cenário: Sinais de detecção concretos
  Dado um anti-pattern do catálogo
  Então ele tem sinais de detecção específicos (ex.: "query SQL montada por concatenação/f-string com entrada do usuário")
  E não apenas descrições vagas

Cenário: APIs deprecated
  Dado o catálogo
  Então existe ao menos 1 entrada de detecção de APIs deprecated
  E cada exemplo indica a API obsoleta e o equivalente moderno

Cenário: Cobertura da análise manual
  Dado os problemas da análise manual (US-01 a US-03)
  Então cada um mapeia para pelo menos 1 anti-pattern do catálogo
```

## US-10: Escrever o Template de relatório
Como Avaliador(a)
Quero que todos os relatórios sigam um formato padronizado
Para comparar os 3 projetos e verificar os critérios rapidamente

Cobre: RF-06 (área 3), RF-14, RNF-06, CA-13

### Critérios de aceite
```gherkin
Cenário: Template compatível com o enunciado
  Dado o arquivo de template de relatório
  Então ele define cabeçalho (Project, Stack, Files/LOC), Summary por severidade, Findings (severidade, título, File, Description, Impact, Recommendation), Total e a pergunta de confirmação
  E especifica a ordenação CRITICAL → LOW
  E especifica o formato "caminho:linha" ou "caminho:inicio-fim"
```

## US-11: Escrever as Guidelines de arquitetura MVC
Como Agente
Quero regras claras das camadas MVC alvo
Para refatorar qualquer projeto para a mesma arquitetura de referência

Cobre: RF-06 (área 4), RF-18, CA-14

### Critérios de aceite
```gherkin
Cenário: Responsabilidades por camada
  Dado o arquivo de guidelines de arquitetura
  Então ele define responsabilidades e proibições de Models, Views/Routes e Controllers
  E define as camadas de apoio: config, middlewares/error handler e composition root (entry point)
  E apresenta uma estrutura de diretórios alvo aplicável a Python e a Node.js
  E orienta como tratar projetos monolíticos e projetos parcialmente organizados
```

## US-12: Escrever o Playbook de refatoração
Como Agente
Quero padrões concretos de transformação com exemplos de código
Para aplicar correções consistentes na Fase 3

Cobre: RF-06 (área 5), RF-19, CA-10

### Critérios de aceite
```gherkin
Cenário: Tamanho e formato
  Dado o playbook de refatoração
  Então ele contém no mínimo 8 padrões de transformação
  E cada padrão tem um bloco de código "antes" e um bloco "depois"
  E cada padrão referencia o(s) anti-pattern(s) do catálogo que resolve

Cenário: Agnosticismo dos exemplos
  Dado os exemplos do playbook
  Então eles não são cópias de trechos específicos dos 3 projetos tratados como regra
  E cobrem mais de uma stack ou são descritos de forma transferível
```

## US-13: Replicar a skill nos outros projetos
Como Mantenedor(a)
Quero copiar a skill sem alterações para `ecommerce-api-legacy/` e `task-manager-api/`
Para provar que ela é reutilizável e agnóstica

Cobre: RF-24, R-06, CA-11

### Critérios de aceite
```gherkin
Cenário: Cópias idênticas
  Dado a skill em code-smells-project/.claude/skills/refactor-arch/
  Quando ela é copiada para ecommerce-api-legacy/.claude/skills/refactor-arch/ e task-manager-api/.claude/skills/refactor-arch/
  Então "git diff --no-index" entre a original e cada cópia não retorna diferenças

Cenário: Iteração propagada
  Dado que a skill foi ajustada após uma execução
  Então o ajuste é replicado nas 3 cópias antes da próxima execução
```

---

## Épico 3 — Execução nos 3 projetos

## US-14: Executar a skill no Projeto 1 (code-smells-project)
Como Mantenedor(a)
Quero rodar `/refactor-arch` no monolito Python/Flask
Para obter o relatório e o código refatorado em MVC

Cobre: RF-25 a RF-27, CA-01 a CA-04, CA-06, CA-12, CA-16

### Critérios de aceite
```gherkin
Cenário: Fase 1 correta
  Dado "cd code-smells-project" e "claude \"/refactor-arch\""
  Quando a Fase 1 termina
  Então Language é Python, Framework é Flask 3.1.1 e o domínio é E-commerce (produtos, pedidos, usuários)
  E Source files condiz com os 4 arquivos .py originais

Cenário: Fase 2 cobre a análise manual
  Quando a Fase 2 termina
  Então o relatório tem ≥ 5 findings e ≥ 1 CRITICAL ou HIGH
  E ≥ 5 problemas da análise manual do projeto 1 aparecem no relatório
  E a skill pausa com a pergunta de confirmação

Cenário: Fase 3 funcional
  Dado que o operador confirmou com "y"
  Quando a Fase 3 termina
  Então existe estrutura de diretórios MVC
  E "python app.py" (ou comando documentado) sobe em http://localhost:5000 sem erros
  E as 19 rotas do inventário da SPEC (7.5) respondem conforme a baseline
  E endpoints administrativos inseguros seguem a decisão D-03 documentada

Cenário: Artefatos
  Então reports/audit-project-1.md contém a saída da Fase 2
  E existe commit separado contendo apenas a refatoração de code-smells-project
```

## US-15: Executar a skill no Projeto 2 (ecommerce-api-legacy)
Como Mantenedor(a)
Quero rodar `/refactor-arch` no projeto Node.js/Express
Para provar que a skill funciona em outra stack

Cobre: RF-24 a RF-27, CA-01 a CA-04, CA-12, CA-16

### Critérios de aceite
```gherkin
Cenário: Fase 1 correta
  Dado "cd ecommerce-api-legacy" e "claude \"/refactor-arch\""
  Quando a Fase 1 termina
  Então Language é JavaScript/Node.js, Framework é Express 4.x e o domínio é LMS com fluxo de checkout
  E o banco é identificado como SQLite em memória

Cenário: Fase 2 mínima
  Quando a Fase 2 termina
  Então o relatório tem ≥ 5 findings e ≥ 1 CRITICAL ou HIGH
  E a skill pausa com a pergunta de confirmação sem modificar arquivos

Cenário: Fase 3 funcional
  Dado que o operador confirmou com "y"
  Quando a Fase 3 termina
  Então "npm start" (ou comando documentado) sobe em http://localhost:3000 sem erros
  E POST /api/checkout (sucesso e pagamento recusado), GET /api/admin/financial-report e DELETE /api/users/:id respondem conforme a baseline
  E o payload de request do checkout (usr, eml, pwd, c_id, card) continua aceito

Cenário: Artefatos
  Então reports/audit-project-2.md contém a saída da Fase 2
  E existe commit separado contendo apenas a refatoração de ecommerce-api-legacy
```

## US-16: Executar a skill no Projeto 3 (task-manager-api)
Como Mantenedor(a)
Quero rodar `/refactor-arch` em um projeto Flask já parcialmente organizado
Para provar que a skill detecta problemas e melhora a arquitetura sem quebrar a aplicação

Cobre: RF-17, RF-25 a RF-27, CA-01 a CA-04, CA-12, CA-16

### Critérios de aceite
```gherkin
Cenário: Fase 1 correta
  Dado "cd task-manager-api" e "claude \"/refactor-arch\""
  Quando a Fase 1 termina
  Então Language é Python, Framework é Flask 3.0.0 e o domínio é identificado como Task Manager
  E a arquitetura atual é descrita como parcialmente em camadas (models/routes/services/utils)

Cenário: Problemas em projeto organizado
  Quando a Fase 2 termina
  Então o relatório tem ≥ 5 findings e ≥ 1 CRITICAL ou HIGH
  E inclui ao menos 1 finding arquitetural além de problemas de segurança/qualidade
  E inclui findings de APIs deprecated, se aplicável
  E a skill pausa com a pergunta de confirmação

Cenário: Fase 3 sem regressão
  Dado que o operador confirmou com "y"
  E o banco foi populado com "python seed.py"
  Quando a Fase 3 termina
  Então "python app.py" (ou comando documentado) sobe em http://localhost:5000 sem erros
  E as 22 combinações método+path do inventário da SPEC (7.5) respondem conforme a baseline

Cenário: Artefatos
  Então reports/audit-project-3.md contém a saída da Fase 2
  E existe commit separado contendo apenas a refatoração de task-manager-api
```

## US-17: Validar cada projeto com o checklist do enunciado
Como Avaliador(a)
Quero o checklist de validação preenchido para cada projeto
Para verificar rapidamente que todas as exigências foram atendidas

Cobre: SPEC 9.3, CA-04, CA-17

### Critérios de aceite
```gherkin
Cenário: Checklist por projeto
  Dado os 3 projetos refatorados
  Quando o QA executa a validação
  Então existe um checklist (Fase 1, Fase 2, Fase 3) preenchido para cada projeto
  E cada item marcado tem evidência (trecho de relatório, log de boot, resposta de endpoint)
  E itens não atendidos são marcados como não atendidos com justificativa

Cenário: Baseline versus pós-refatoração
  Dado a baseline de status capturada no código original
  Quando os mesmos endpoints são chamados após a refatoração
  Então os status coincidem, exceto mudanças justificadas por correção de segurança documentadas
```

---

## Épico 4 — Relatórios e documentação

## US-18: Salvar os relatórios de auditoria
Como Avaliador(a)
Quero os relatórios da Fase 2 em `reports/`
Para inspecionar os achados de cada projeto sem reexecutar a skill

Cobre: RF-26, R-03, CA-13, CA-15

### Critérios de aceite
```gherkin
Cenário: Arquivos presentes e fiéis
  Dado as 3 execuções concluídas
  Então existem reports/audit-project-1.md, reports/audit-project-2.md e reports/audit-project-3.md
  E cada um é a saída da Fase 2 da última versão da skill, sem sequências ANSI, em UTF-8 sem BOM
  E cada um segue o template de relatório da skill
```

## US-19: Preservar o enunciado original
Como Avaliador(a)
Quero o enunciado original disponível no repositório
Para conferir os requisitos mesmo depois que o README for reescrito

Cobre: O-07, CA-18

### Critérios de aceite
```gherkin
Cenário: Enunciado preservado
  Dado o README.md original do fork
  Então docs/CHALLENGE.md existe com o mesmo conteúdo
```

## US-20: README — Seção A (Análise Manual)
Como Avaliador(a)
Quero ver os problemas encontrados manualmente em cada projeto
Para avaliar a compreensão do problema antes da automação

Cobre: RF-28, CA-05, CA-17

### Critérios de aceite
```gherkin
Cenário: Seção A completa
  Dado o README.md final
  Então a seção "Análise Manual" lista, por projeto, ≥ 5 problemas com severidade e justificativa
  E respeita a distribuição ≥ 1 CRITICAL/HIGH, ≥ 2 MEDIUM, ≥ 2 LOW por projeto
```

## US-21: README — Seção B (Construção da Skill)
Como Avaliador(a)
Quero entender as decisões de design da skill
Para avaliar a qualidade e o agnosticismo da solução

Cobre: RF-28, CA-08, CA-17

### Critérios de aceite
```gherkin
Cenário: Seção B completa
  Dado o README.md final
  Então a seção "Construção da Skill" explica a estrutura do SKILL.md e dos arquivos de referência
  E apresenta a tabela de rastreabilidade das 5 áreas de conhecimento para arquivos
  E lista os anti-patterns do catálogo com o motivo da inclusão
  E explica como o agnosticismo foi garantido
  E descreve desafios encontrados (incluindo iterações) e como foram resolvidos
```

## US-22: README — Seção C (Resultados)
Como Avaliador(a)
Quero um resumo dos resultados com evidências
Para confirmar os critérios de aceite nos 3 projetos

Cobre: RF-28, CA-01 a CA-04, CA-17

### Critérios de aceite
```gherkin
Cenário: Seção C completa
  Dado o README.md final
  Então a seção "Resultados" traz a contagem de findings por severidade de cada projeto
  E a comparação antes/depois da estrutura de diretórios de cada projeto
  E o checklist de validação preenchido para cada projeto
  E logs ou screenshots das 3 aplicações rodando após a refatoração
  E a evidência da pausa/confirmação da Fase 2 (decisão D-01)
  E observações sobre o comportamento da skill em stacks diferentes
```

## US-23: README — Seção D (Como Executar)
Como Avaliador(a)
Quero instruções reproduzíveis
Para rodar a skill e validar a refatoração por conta própria

Cobre: RF-28, RNF-03, RNF-04, CA-17

### Critérios de aceite
```gherkin
Cenário: Seção D reproduzível
  Dado o README.md final
  Então a seção "Como Executar" lista pré-requisitos (Claude Code instalado e configurado, Python 3.12, Node 22)
  E os comandos para executar a skill em cada projeto ("cd <projeto>" + "claude \"/refactor-arch\"")
  E os comandos de instalação e boot de cada projeto refatorado
  E como validar que a refatoração funcionou (chamadas aos endpoints, com exemplos em PowerShell/curl)
```
