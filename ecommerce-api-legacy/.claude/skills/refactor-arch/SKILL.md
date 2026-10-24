---
name: refactor-arch
description: "Audita e refatora um projeto backend legado para o padrão MVC em 3 fases sequenciais - (1) análise da stack e da arquitetura, (2) auditoria contra um catálogo de anti-patterns com relatório por severidade e pausa obrigatória para confirmação humana, (3) refatoração para MVC com validação de boot e endpoints. Use quando o usuário pedir para auditar a arquitetura, encontrar code smells, anti-patterns ou falhas de segurança, ou refatorar um projeto para MVC, em qualquer linguagem ou framework (por exemplo Python/Flask ou Node.js/Express)."
---

# refactor-arch — auditoria e refatoração arquitetural para MVC

Você atua como arquiteto de software sênior. Execute as três fases abaixo **em ordem**, sempre na raiz do projeto (diretório de trabalho atual). O conhecimento de domínio está nos arquivos de referência deste diretório: leia cada um **somente na fase indicada**.

| Fase | Leia antes de começar a fase |
|---|---|
| 1 — Análise | [project-analysis.md](project-analysis.md) |
| 2 — Auditoria | [anti-patterns-catalog.md](anti-patterns-catalog.md), [audit-report-template.md](audit-report-template.md) e só a seção do ecossistema detectado em [deprecated-apis.md](deprecated-apis.md) |
| 3 — Refatoração | [mvc-guidelines.md](mvc-guidelines.md), [phase3-validation.md](phase3-validation.md) e as seções `T-xx` de [refactoring-playbook.md](refactoring-playbook.md) citadas nos findings |

## Regras invioláveis

1. **Fases 1 e 2 são somente leitura.** Use apenas Read, Glob, Grep e comandos de shell que só leem (`ls`, `cat`, `wc -l`, `git status`, `git ls-files`, `git log`). Até a confirmação é proibido: criar, editar, mover ou apagar arquivos (Write, Edit, `mkdir`, `>`/`>>`), instalar dependências, executar a aplicação, seeds, testes ou qualquer script do projeto (geram `*.db`, `__pycache__`, logs). Nenhum arquivo temporário dentro do projeto.
2. **Pausa obrigatória** entre a Fase 2 e a Fase 3 (seção "Ponto de parada").
3. Não adicione dependências nem altere manifestos ou lockfiles; não troque linguagem, framework ou banco; não crie funcionalidades.
4. Preserve o contrato HTTP de todos os endpoints (paths, métodos, status, chaves de resposta, nomes de campos de request, content-type). Exceções: somente a lista fechada de `mvc-guidelines.md` §7.
5. Descubra, nunca assuma: nomes de arquivos, tabelas, rotas, porta, comando de boot e seed vêm do código lido nesta execução.
6. Ignore `.claude/`, dependências (`node_modules/`, `.venv/`, `venv/`, `site-packages/`) e artefatos de build: não são código do projeto — não analise, não conte, não modifique.
7. Cada `File:` cita caminho e linhas conferidos no código. Nunca invente finding nem declare sucesso sem evidência produzida nesta execução.
8. Rótulos e cabeçalhos dos blocos de saída ficam em inglês, exatamente como abaixo; textos livres (Domain, Architecture, Description, Impact, Recommendation) em português. Imprima os blocos como texto puro, **sem** cercas de código Markdown.

## Fase 1 — Análise (somente leitura)

1. Leia `project-analysis.md`.
2. Inventarie arquivos-fonte, manifestos, lockfiles e README. Detecte linguagem, framework e versão, dependências, banco e tabelas, domínio, rotas (método + path), entry point, comando de boot, porta, seed e interpretador/venv. Classifique a arquitetura: `monolith`, `partial-layers` ou `layered`.
3. Guarde esses dados (inventário de rotas, boot, porta, seed, classificação, lista de arquivos e LOC) para as Fases 2 e 3.
4. Imprima exatamente este bloco (regras de preenchimento em `project-analysis.md` §11):

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework> <versão>
Dependencies:  <dependências principais, sem o framework>
Domain:        <descrição do domínio> (<entidades principais>)
Architecture:  <Monolítica | Parcialmente em camadas | Em camadas> — <detalhe em 1 linha>
Source files:  <N> files analyzed
DB tables:     <tabela1, tabela2, ...> (<engine>, <arquivo | em memória>)
Endpoints:     <N> routes
================================
```

## Fase 2 — Auditoria (somente leitura)

1. Leia `anti-patterns-catalog.md`, `audit-report-template.md` e, em `deprecated-apis.md`, apenas as seções do ecossistema detectado.
2. Leia **todos** os arquivos-fonte contados na Fase 1, com numeração de linhas.
3. Percorra o catálogo de AP-01 a AP-20: para cada entrada, aplique os sinais de detecção (padrões de busca + leitura) e registre cada ocorrência com caminho e linhas.
4. Descarte falsos positivos usando "Não confundir com" de cada entrada.
5. Agrupe ocorrências conforme as regras do template. A severidade é a do catálogo: não reclassifique.
6. Releia o trecho de cada `File:` (Read com offset) e corrija as linhas antes de imprimir.
7. Ordene CRITICAL → HIGH → MEDIUM → LOW (desempate: ID do catálogo, depois caminho).
8. Imprima o relatório exatamente neste formato (regras completas em `audit-report-template.md`):

```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <Linguagem> + <Framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <Nome do anti-pattern exatamente como no catálogo>
File: <caminho/relativo>:<linha>[-<linha_fim>]
Description: <o que foi encontrado, citando o trecho ou identificador>
Impact: <consequência concreta>
Recommendation: <ação> (<T-xx>)

(... demais findings, ordem CRITICAL → HIGH → MEDIUM → LOW ...)

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Ponto de parada (obrigatório)

- A última linha da resposta da Fase 2 é exatamente `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`.
- Logo após imprimi-la, **encerre o turno**: nenhuma chamada de ferramenta, nenhum arquivo escrito, nenhum texto adicional. Em modo de plano (plan mode), não chame ExitPlanMode nem apresente plano: o relatório é a entrega.
- Na próxima mensagem do usuário:
  - Resposta afirmativa — `y`, `yes`, `s` ou `sim` (sem diferenciar maiúsculas/minúsculas, ignorando espaços e pontuação final) → inicie a Fase 3.
  - Qualquer outra resposta (`n`, `no`, `não`, vazia, pergunta, pedido parcial) → imprima `Refactoring cancelled. No files were modified.` e encerre, sem modificar nada e sem perguntar de novo.

## Fase 3 — Refatoração e validação (escrita liberada)

1. Leia `mvc-guidelines.md`, `phase3-validation.md` e as seções do `refactoring-playbook.md` citadas nas Recommendations.
2. **3.0 Baseline — antes de editar qualquer arquivo:** monte o plano de requisições, prepare o estado do banco, suba a aplicação **original** com o comando de boot original, registre `MÉTODO path -> status` e encerre o processo (`phase3-validation.md` §2–§5).
3. **3.1 Estrutura-alvo** pela classificação da Fase 1 (`mvc-guidelines.md` §4): `monolith` → camadas novas em `src/`; `partial-layers` → evolução incremental, mantendo as camadas coerentes onde estão; `layered` → só correções pontuais.
4. **3.2 Transformações** na ordem recomendada do playbook, priorizando CRITICAL e HIGH. Cada finding é resolvido ou listado como residual. O comando de boot original continua funcionando (entry point fino no mesmo caminho) e variáveis de ambiente novas ficam documentadas em `.env.example`.
5. **3.3 Revalidação:** mesmo plano, mesmo estado inicial, mesmo comando de boot; endpoints admin protegidos testados sem e com token. Divergência não justificada, 5xx ou rota sumida → diagnosticar, corrigir e repetir (máximo 3 ciclos).
6. **3.4 Varredura final:** procure findings residuais e segredos hardcoded no código resultante.
7. **3.5 Limpeza:** encerre todos os processos iniciados, restaure ou remova bancos gerados e apague temporários. No projeto ficam apenas o código refatorado e o `.env.example`.
8. Imprima o bloco final (formato completo em `phase3-validation.md` §9):

```text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante, com o composition root anotado>

## Transformations Applied
  - <T-xx Nome> → <arquivos>

## Endpoint Check (baseline → after)
  ✓|✗ <MÉTODO> <path> <status antes> → <status depois> [(justificativa)]

## Validation
  ✓|✗ Application boots without errors (<comando> → porta <P>)
  ✓|✗ All endpoints respond correctly (<k>/<N> match baseline, <j> justified changes)
  ✓|✗ No hardcoded secrets in source
  ✓|✗ Residual findings: <n> (<lista curta ou "none">)
================================
```

Use `✓` somente com evidência produzida nesta execução; caso contrário `✗` com o motivo. Escreva `Zero anti-patterns remaining` só se a varredura final realmente não encontrar nada.
