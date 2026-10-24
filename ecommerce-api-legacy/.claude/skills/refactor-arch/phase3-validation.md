# Phase 3 Validation — baseline, boot real, endpoints e bloco final

> Carregado no início da Fase 3 (depois da resposta afirmativa). A validação é o passo com maior risco de "falso sucesso": siga o procedimento à risca e só marque `✓` com evidência produzida nesta execução.
> Sem novas dependências: use o runtime do próprio projeto (Python `urllib` / Node `fetch`) ou `curl.exe`. Pode instalar as dependências **já declaradas** se faltarem (§4.4).
> Todo artefato de validação (plano, runner, logs, backups) fica num **diretório temporário do sistema**, nunca dentro do projeto.

## 1. Visão geral

```text
[y] → 2. preparar temp + plano → 3. estado limpo do banco → 4. boot ORIGINAL → 5. executar plano = baseline → encerrar
    → refatoração (playbook)
    → 6. estado limpo → boot REFATORADO → mesmo plano (sem token e com token) → 7. comparar
    → falhou? diagnosticar + corrigir (máx. 3 ciclos) → 8. varredura final + limpeza → 9. bloco PHASE 3
```

A baseline é capturada **depois do "y" e antes da primeira edição**: nas Fases 1 e 2 é proibido subir a aplicação (ela cria bancos e caches).

## 2. Diretório temporário e arquivos de apoio

- Crie um diretório temporário fora do projeto: Bash `mktemp -d` (no Git Bash do Windows ele fica sob o temp do usuário); PowerShell `New-Item -ItemType Directory (Join-Path $env:TEMP "refactor-arch-$(Get-Random)")`.
- Nele ficam: `plan.json`, o runner (`runner.py` ou `runner.js`), logs de boot (`boot-before.log`, `boot-after.log`), resultados (`before.txt`, `after-notoken.txt`, `after-token.txt`) e o backup de bancos (`db-backup/`).

## 3. Plano de requisições (`plan.json`)

### 3.1 Montagem

1. Parta do inventário de rotas da Fase 1: **cada combinação método + path aparece ao menos uma vez** com dados válidos.
2. Acrescente ao menos 1 caso de erro por recurso: id inexistente (ex.: `999999`) → 404; corpo inválido ou campo obrigatório ausente → 400/401/422 (conforme o código).
3. IDs existentes: deduza do seed (scripts de seed ou INSERTs no boot; autoincrement começa em 1). Recursos criados pelo plano: capture o id da resposta com `save` e use `${nome}` nos passos seguintes.
4. Corpos: derive dos campos obrigatórios, tipos e valores permitidos lidos nas validações do código; use os nomes de campos **exatamente** como o código lê.
5. Ordem: leituras → criações → atualizações → exclusões (de preferência de registros criados pelo próprio plano) → endpoints administrativos/destrutivos por último (ex.: reset do banco).
6. Marque com `"admin": true` todo endpoint classificado como AP-05 (receberá `X-Admin-Token` quando houver token).
7. Use `http://127.0.0.1:<porta>` em `base_url` (evita resolução de `localhost` para IPv6 quando o servidor escuta só em IPv4).

### 3.2 Formato

```json
{
  "base_url": "http://127.0.0.1:8000",
  "wait_seconds": 30,
  "admin_token": "",
  "requests": [
    { "method": "GET",    "path": "/items" },
    { "method": "GET",    "path": "/items/1" },
    { "method": "GET",    "path": "/items/999999", "label": "not found" },
    { "method": "POST",   "path": "/items", "body": { "name": "Sample", "price": 10.5 },
      "save": { "as": "new_item", "from": "data.id" } },
    { "method": "POST",   "path": "/items", "body": {}, "label": "invalid body" },
    { "method": "PUT",    "path": "/items/${new_item}", "body": { "name": "Sample 2", "price": 11 } },
    { "method": "DELETE", "path": "/items/${new_item}" },
    { "method": "POST",   "path": "/admin/wipe", "admin": true }
  ]
}
```

`save.from` é um caminho com pontos dentro do JSON de resposta (índices numéricos para listas, ex.: `data.0.id`).

## 4. Boot em background

### 4.1 Comando

Use **o mesmo comando de boot detectado na Fase 1** (ex.: `python app.py`, `npm start`), com o interpretador do venv local se existir (`.venv\Scripts\python.exe` no Windows, `.venv/bin/python` em POSIX). Se houver seed obrigatório, rode-o antes, com o mesmo interpretador e a partir da raiz do projeto.

### 4.2 Como iniciar e encerrar

| Ambiente | Iniciar em background (log em arquivo do temp) | Encerrar |
|---|---|---|
| Ferramenta de shell do agente com execução em background | executar o comando de boot a partir da raiz do projeto com saída redirecionada para `<temp>/boot-<rodada>.log` | localizar o PID que escuta na porta e matar a árvore (linhas abaixo) |
| Windows PowerShell | `$p = Start-Process -FilePath <exe> -ArgumentList <args> -WorkingDirectory <raiz> -RedirectStandardOutput <temp>\boot.out -RedirectStandardError <temp>\boot.err -PassThru -WindowStyle Hidden` (para npm use `npm.cmd`) | `taskkill /PID $p.Id /T /F` |
| Windows, PID pela porta | `netstat -ano \| findstr :<porta>` (coluna final = PID, estado LISTENING) | `taskkill /PID <pid> /T /F` (no Git Bash: `taskkill //PID <pid> //T //F`) |
| POSIX | `nohup <comando> > <temp>/boot.log 2>&1 & echo $!` | `kill <pid>`; restos pela porta: `lsof -ti tcp:<porta> \| xargs kill` |

- Modo debug com reloader (ex.: Flask `debug=True`) cria processo pai + filho: mate a **árvore** (`/T`) ou mate o PID da porta e confirme que nenhum processo do projeto ficou.
- Variáveis de ambiente para a rodada com token: PowerShell `$env:ADMIN_TOKEN = '<token>'` antes do `Start-Process`; Bash `ADMIN_TOKEN=<token> <comando>`. Use um token aleatório só desta execução (ex.: `python -c "import secrets; print(secrets.token_hex(16))"`).
- Antes de cada boot, confirme que a porta está livre; depois de encerrar, confirme de novo.

### 4.3 Critério de boot aprovado

- O runner conseguiu conectar na porta dentro de `wait_seconds` (30 s), **e**
- o processo continua vivo depois das requisições, **e**
- o log de boot não contém `Traceback`, `Error:`, `Exception` não tratada, `EADDRINUSE` ou `Cannot find module`.

### 4.4 Dependências ausentes

Se o boot original falhar por dependência declarada não instalada: Python → `<venv>/python -m pip install -r requirements.txt` (crie o venv do projeto se não existir: `python -m venv .venv`); Node → `npm ci` quando houver lockfile (não altera o lockfile), senão `npm install --no-save`. Nunca adicione pacotes ao manifesto.

## 5. Runners HTTP (gravar no temp e executar a partir dele)

### 5.1 Python (stdlib) — `runner.py`

```python
import json, re, socket, sys, time, urllib.error, urllib.parse, urllib.request

plan = json.load(open(sys.argv[1], encoding="utf-8"))
base = plan["base_url"].rstrip("/")
token = plan.get("admin_token") or ""
url = urllib.parse.urlsplit(base)
deadline = time.time() + plan.get("wait_seconds", 30)
while True:
    try:
        socket.create_connection((url.hostname, url.port or 80), timeout=1).close()
        break
    except OSError:
        if time.time() > deadline:
            print("BOOT_TIMEOUT")
            sys.exit(2)
        time.sleep(0.5)

saved = {}

def sub(value):
    if isinstance(value, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: str(saved.get(m.group(1), m.group(0))), value)
    if isinstance(value, list):
        return [sub(v) for v in value]
    if isinstance(value, dict):
        return {k: sub(v) for k, v in value.items()}
    return value

for step in plan["requests"]:
    path = sub(step["path"])
    body = step.get("body")
    data = json.dumps(sub(body)).encode("utf-8") if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=step["method"])
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if step.get("admin") and token:
        request.add_header("X-Admin-Token", token)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read()
    except Exception as err:
        status, raw = "ERR", str(err).encode()
    if "save" in step:
        try:
            value = json.loads(raw)
            for key in step["save"]["from"].split("."):
                value = value[int(key)] if isinstance(value, list) else value[key]
            saved[step["save"]["as"]] = value
        except Exception:
            pass
    label = f'  # {step["label"]}' if step.get("label") else ""
    print(f'{step["method"]:<7}{path} -> {status}{label}')
```

Execução: `<python> <temp>/runner.py <temp>/plan.json > <temp>/before.txt`.

### 5.2 Node.js 18+ (core) — `runner.js`

```js
const fs = require('node:fs');
const net = require('node:net');

const plan = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const base = plan.base_url.replace(/\/$/, '');
const { hostname, port } = new URL(base);
const saved = {};
const sub = (v) => {
  if (typeof v === 'string') return v.replace(/\$\{(\w+)\}/g, (m, k) => (k in saved ? String(saved[k]) : m));
  if (Array.isArray(v)) return v.map(sub);
  if (v && typeof v === 'object') return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, sub(x)]));
  return v;
};
const canConnect = () => new Promise((resolve) => {
  const socket = net.connect({ host: hostname, port: Number(port) || 80 }, () => { socket.destroy(); resolve(true); });
  socket.on('error', () => resolve(false));
});

(async () => {
  const deadline = Date.now() + (plan.wait_seconds || 30) * 1000;
  while (!(await canConnect())) {
    if (Date.now() > deadline) { console.log('BOOT_TIMEOUT'); process.exit(2); }
    await new Promise((r) => setTimeout(r, 500));
  }
  for (const step of plan.requests) {
    const path = sub(step.path);
    const headers = {};
    let body;
    if (step.body !== undefined && step.body !== null) {
      body = JSON.stringify(sub(step.body));
      headers['Content-Type'] = 'application/json';
    }
    if (step.admin && plan.admin_token) headers['X-Admin-Token'] = plan.admin_token;
    let status = 'ERR';
    let text = '';
    try {
      const res = await fetch(base + path, { method: step.method, headers, body });
      status = res.status;
      text = await res.text();
    } catch { /* status permanece ERR */ }
    if (step.save) {
      try {
        let v = JSON.parse(text);
        for (const k of step.save.from.split('.')) v = v[k];
        saved[step.save.as] = v;
      } catch { /* sem valor para salvar */ }
    }
    console.log(`${step.method.padEnd(7)}${path} -> ${status}${step.label ? `  # ${step.label}` : ''}`);
  }
})();
```

Execução: `node <temp>/runner.js <temp>/plan.json > <temp>/before.txt`.

### 5.3 Alternativa: `curl.exe`

Para poucas requisições ou diagnóstico: `curl.exe -s -o NUL -w "%{http_code}" -X POST -H "Content-Type: application/json" --data-binary "@<temp>/body.json" http://127.0.0.1:<porta>/<path>`. No PowerShell 5.1 use sempre `curl.exe` (o alias `curl` é `Invoke-WebRequest`); corpos JSON em arquivo evitam problemas de aspas. Em POSIX troque `NUL` por `/dev/null`.

O test client do framework (ex.: Flask `test_client()`) **não** substitui o boot real; use só para diagnosticar.

## 6. Estado do banco e rodadas

1. **Antes da baseline:** liste bancos gerados em runtime e ignorados pelo Git (`git ls-files --others --ignored --exclude-standard`, filtrando `*.db`, `*.sqlite`, `*.sqlite3`, inclusive em `instance/`). Mova-os para `<temp>/db-backup/` (preservando o caminho relativo).
2. **Antes de cada rodada** (baseline, pós sem token, pós com token): apague os bancos gerados pela rodada anterior e rode o seed, se existir. Banco em memória dispensa reset (reiniciar o processo basta).
3. **Rodadas:**
   - `before.txt` — código original, sem token (o código original ignora o header).
   - `after-notoken.txt` — código refatorado, sem `ADMIN_TOKEN` no ambiente.
   - `after-token.txt` — código refatorado, com `ADMIN_TOKEN` no ambiente do processo e `admin_token` no plano.
4. Se o código original **não subir**, registre `boot failed` como baseline; a meta passa a ser fazer a aplicação subir, e os status esperados são deduzidos do código (sucesso para dados válidos, 4xx para os casos de erro).

## 7. Comparação e ciclos de correção

Compare linha a linha (mesma ordem do plano):

| Situação | Resultado |
|---|---|
| `after-token` igual a `before` | ✓ |
| Endpoint admin: `after-notoken` = 403 **e** `after-token` = status da baseline | ✓ justificado (guard admin) |
| Status diferente previsto em `mvc-guidelines.md` §7 (ex.: entrada inválida que dava 500 agora dá 400) | ✓ justificado, com a razão |
| Qualquer 5xx, `ERR`, `BOOT_TIMEOUT`, 404 em rota que existia, ou divergência não prevista | ✗ |

Para cada ✗: leia o log de boot e o traceback, corrija o código, refaça o estado limpo e rode o **plano inteiro** de novo. Máximo de **3 ciclos** de correção; depois disso, pare e reporte `✗` com o diagnóstico (proibido declarar sucesso sem evidência). Recomenda-se uma revalidação intermediária só de boot depois do esqueleto de camadas (T-01/T-03/T-08).

## 8. Varredura final e limpeza

**Varredura (no código resultante):**
- Rode de novo os padrões de busca do catálogo para AP-01, AP-02, AP-04, AP-05, AP-06, AP-14 e AP-20, e busque os literais de segredos encontrados na Fase 2 — `No hardcoded secrets in source` só é `✓` se não sobrar nenhum fora do `.env.example`.
- Conte os findings residuais (inclusive riscos aceitos, como endpoint de SQL arbitrário protegido por token) e liste-os por ID e arquivo.

**Limpeza (obrigatória, mesmo em caso de falha):**
1. Encerre todos os processos iniciados e confirme que a porta está livre.
2. Apague os bancos gerados pelas rodadas e restaure os de `<temp>/db-backup/` nos caminhos originais.
3. Apague o diretório temporário.
4. Rode `git status --porcelain` no projeto: devem aparecer só as mudanças de código da refatoração e o `.env.example` (nenhum plano, runner, log ou banco).

## 9. Bloco PHASE 3 (formato exato)

```text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<projeto>/
├── <entry point>                 (entry point)
├── .env.example
└── src/
    ├── app.<ext>                 (composition root)
    ├── config/
    │   └── <arquivo>
    ├── models/
    │   └── <arquivos>
    ├── controllers/
    │   └── <arquivos>
    ├── routes/
    │   └── <arquivos>
    └── middlewares/
        └── <arquivos>

## Transformations Applied
  - T-01 Extract Configuration to Environment → <arquivos>
  - <T-xx Nome> → <arquivos>

## Endpoint Check (baseline → after)
  ✓ GET    /recurso                 200 → 200
  ✓ POST   /admin/acao              200 → 403  (justified: admin guard; 200 with X-Admin-Token)
  ✗ PUT    /recurso/<id>            200 → 500  (<diagnóstico>)

## Validation
  ✓|✗ Application boots without errors (<comando de boot> → porta <P>)
  ✓|✗ All endpoints respond correctly (<k>/<N> match baseline, <j> justified changes)
  ✓|✗ No hardcoded secrets in source
  ✓|✗ Residual findings: <n> (<IDs/arquivos ou "none">)
================================
```

Regras:
- A árvore mostra só diretórios e arquivos-fonte relevantes, usando `├──`, `└──`, `│`; anote `(entry point)` e `(composition root)`. Em projetos `partial-layers`, mostre as pastas mantidas e as novas, marcando as novas com `(new)`.
- `Endpoint Check` tem uma linha por requisição do plano (inclusive casos de erro), com o rótulo quando houver.
- As duas primeiras linhas de `## Validation` são literais do enunciado; cada uma recebe `✓` ou `✗` conforme a evidência.
- `Zero anti-patterns remaining` só pode ser escrito se a varredura final não encontrar nada; caso contrário use a linha `Residual findings`.
- Se o comando de boot mudou (não recomendado), informe o novo comando na linha de boot.
- Imprima como texto puro, sem cercas de código.
