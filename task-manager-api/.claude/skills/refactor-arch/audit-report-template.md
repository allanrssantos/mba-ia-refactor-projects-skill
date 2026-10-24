# Audit Report Template — formato da Fase 2

> Carregado na Fase 2. O relatório é **impresso** (não gravado em arquivo) e deve seguir este formato byte a byte nos rótulos, para que execuções diferentes produzam relatórios comparáveis.

## 1. Template literal

Imprima como texto puro (sem cercas de código), substituindo apenas os `<...>`:

```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório raiz do projeto>
Stack:   <Linguagem> + <Framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <Nome do anti-pattern exatamente como no catálogo>
File: <caminho/relativo>:<linha>[-<linha_fim>]
Other occurrences: <caminho>:<linha>[-<fim>], <caminho>:<linha>[-<fim>], ...
Description: <o que foi encontrado, citando o trecho ou identificador>
Impact: <consequência concreta>
Recommendation: <ação concreta> (<T-xx>[, <T-yy>])

### [<SEVERITY>] <...próximo finding...>
File: ...
Description: ...
Impact: ...
Recommendation: ...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## 2. Regras de preenchimento

### 2.1 Cabeçalho
- `Project:` nome do diretório de trabalho (raiz do projeto), sem caminho.
- `Stack:` `<Linguagem> + <Framework>` sem versão (ex.: `Python + Flask`, `JavaScript (Node.js) + Express`).
- `Files:` o mesmo `N` de `Source files` da Fase 1; `LOC` = soma das linhas físicas desses arquivos, com prefixo `~`.

### 2.2 Findings
- Cabeçalho do finding: `### [CRITICAL]`, `### [HIGH]`, `### [MEDIUM]` ou `### [LOW]` + espaço + **nome exato** da entrada do catálogo (sem o ID `AP-xx`).
- Campos sempre nesta ordem: `File`, `Other occurrences` (opcional), `Description`, `Impact`, `Recommendation`. Uma linha por campo, sem quebras internas.
- `File:` caminho relativo à raiz do projeto, separador `/`, linhas 1-based exatamente como lidas com numeração. Uma linha → `caminho:42`; intervalo → `caminho:42-57`. Nunca `caminho` sem linha, nunca linhas estimadas.
- `Other occurrences:` só quando houver; mesmo formato de `File`, separados por `, `; no máximo 10 itens — acima disso, liste 10 e acrescente `(+<k> more)`. Omita a linha inteira se não houver outras ocorrências.
- `Description:` o que foi encontrado, citando identificador/trecho curto entre crases (ex.: `` `SECRET_KEY` com literal ``). Para AP-16, cite a API obsoleta, desde qual versão e o substituto.
- `Impact:` consequência concreta para segurança, manutenção, desempenho ou correção — não repita a descrição.
- `Recommendation:` ação concreta + ID(s) da transformação do playbook entre parênteses, ex.: `(T-02)`.
- Textos livres em português; rótulos em inglês.

### 2.3 Ordenação
1. Severidade: CRITICAL → HIGH → MEDIUM → LOW.
2. Mesma severidade: ordem do ID no catálogo (AP-01, AP-02, ...).
3. Mesmo ID: caminho do arquivo em ordem alfabética, depois linha.

### 2.4 Contagens
- `Summary` conta exatamente os blocos `### [` impressos de cada severidade (inclua as quatro, mesmo com `0`).
- `Total` = soma do Summary = número de blocos `### [`.
- Confira as contagens antes de imprimir.

### 2.5 Integridade
- Sem findings inventados: cada um tem evidência lida nesta execução. Se houver menos de 5 findings reais, imprima os que existirem (honestidade acima de meta).
- Antes de imprimir, releia o intervalo de cada `File:` e ajuste as linhas se necessário.
- A pergunta final é a última linha da resposta, literal, precedida de uma linha em branco. Depois dela, encerre o turno (ver `SKILL.md`, "Ponto de parada").

## 3. Agrupamento de ocorrências (determinístico)

| Escopo da entrada (ver catálogo) | Regra | Entradas |
|---|---|---|
| arquivo (padrão) | 1 finding por anti-pattern **por arquivo**. `File:` = ocorrência mais grave ou, em empate, a primeira; demais ocorrências do mesmo arquivo em `Other occurrences`. | AP-01, 02, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 17, 18 |
| unidade | 1 finding por classe/módulo; `File:` cobre o intervalo da classe ou do arquivo inteiro (`caminho:1-<última linha>`). | AP-03 |
| projeto | 1 finding para o projeto inteiro; `File:` = ocorrência mais representativa; as demais (de todos os arquivos) em `Other occurrences`. | AP-14, AP-19, AP-20 |
| projeto, por bloco | 1 finding por bloco de código duplicado distinto. | AP-15 |
| projeto, por API | 1 finding por API obsoleta distinta. | AP-16 |

Uma mesma linha pode aparecer em findings de anti-patterns diferentes (ex.: um `print` que vaza senha é AP-04 e AP-20).

## 4. Exemplo preenchido (sintético — não corresponde a nenhum projeto real)

```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: inventory-service
Stack:   Python + Flask
Files:   3 analyzed | ~410 lines of code

## Summary
CRITICAL: 2 | HIGH: 1 | MEDIUM: 1 | LOW: 1

## Findings

### [CRITICAL] Hardcoded Credentials
File: server.py:9
Other occurrences: server.py:12
Description: `SECRET_KEY` definido com o literal `'inv-secret-2020'` e senha SMTP literal em `MAIL_PASSWORD`.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões e usar a conta de e-mail.
Recommendation: Ler os valores de variáveis de ambiente em um módulo de configuração e documentá-los em `.env.example` (T-01).

### [CRITICAL] SQL Injection
File: store.py:41-43
Other occurrences: store.py:77, store.py:102-108
Description: `cursor.execute("SELECT * FROM items WHERE sku = '" + sku + "'")` concatena valor vindo da query string.
Impact: Permite ler ou apagar qualquer tabela e contornar filtros com payloads como `' OR '1'='1`.
Recommendation: Usar placeholders `?` com tupla de parâmetros em todas as consultas (T-02).

### [HIGH] Business Logic in Controller/Route
File: server.py:55-118
Description: A view `create_order` valida o payload, calcula descontos por faixa, baixa estoque e grava o pedido.
Impact: Regras de preço não são reutilizáveis nem testáveis sem HTTP.
Recommendation: Mover cálculo e persistência para um service/model e deixar o controller fino (T-07).

### [MEDIUM] Deprecated API Usage
File: store.py:15
Other occurrences: store.py:88, server.py:131
Description: `datetime.utcnow()` está deprecated desde o Python 3.12; substituto: `datetime.now(timezone.utc)`.
Impact: Gera DeprecationWarning e quebrará em versões futuras do runtime.
Recommendation: Substituir por um helper baseado em `datetime.now(timezone.utc)` preservando o formato serializado (T-13).

### [LOW] Magic Numbers / Strings
File: store.py:120-124
Description: Faixas de desconto `> 5000` e `* 0.05` escritas inline.
Impact: Regra comercial difícil de localizar e alterar com segurança.
Recommendation: Extrair para constantes nomeadas no módulo de constantes (T-14).

================================
Total: 5 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
