# Flags do Claude Code (tarefa D1)

Verificado em 2026-10-24 com `claude --version` -> `2.1.310 (Claude Code)`, via `claude --help` e `claude -p --help`
(`-p` imprime o mesmo help global; nao ha help separado para o modo print).

| Flag necessaria (ADR-01) | Existe? | Observacao do help |
|---|---|---|
| `-p, --print` | sim | "Print response and exit". O dialogo de confianca do workspace e ignorado em modo nao interativo: usar somente em diretorios confiaveis. |
| `-c, --continue` | sim | "Continue the most recent conversation in the current directory" (depende do diretorio: rodar as duas etapas no mesmo cwd, sem `--no-session-persistence`). |
| `--permission-mode <mode>` | sim | Valores: `acceptEdits`, `auto`, `bypassPermissions`, `manual`, `dontAsk`, `plan`. |
| `--allowedTools, --allowed-tools <tools...>` | sim | Lista separada por virgula ou espaco; aceita padroes como `"Bash(git *)"`. |

Flags uteis adicionais confirmadas: `--output-format text|json|stream-json`, `--disallowedTools`, `--session-id <uuid>`,
`-r/--resume`, `--max-budget-usd` (so com `-p`), `--no-session-persistence` (NAO usar: impede o `--continue`),
`--permission-prompts host|none` (so com `-p`), `--model`, `--effort`, `--add-dir`, `--debug-file <path>`.

Nao foi possivel validar (a skill ainda nao existe e nada foi executado contra o modelo): se `/refactor-arch` e aceito como
prompt em `-p` e se `--permission-mode plan` nao impede a invocacao da skill. Conforme ADR-01, se `plan` impedir, usar o modo
padrao na etapa 1 e confiar na instrucao da skill + checagem de `git status`.

## Sequencia recomendada (nao interativa, 2 etapas, mesmo diretorio do projeto)

PowerShell, a partir da raiz do repositorio (exemplo: projeto 1; trocar a pasta e N):

```powershell
$Root = (Get-Location).Path
$N = 1; $Proj = 'code-smells-project'
New-Item -ItemType Directory -Force docs\evidence\project-$N | Out-Null
Set-Location $Root\$Proj

# Etapa 1 - Fases 1 e 2 (somente leitura). Deve terminar na pergunta literal
# "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"
claude -p "/refactor-arch" --permission-mode plan 2>&1 |
  Tee-Object -FilePath $Root\docs\evidence\project-$N\stage1.log

# Evidencia da pausa (CA-12): deve ficar vazio
git status --porcelain -- . | Tee-Object -FilePath $Root\docs\evidence\project-$N\stage1-git-status.txt

# (operador) extrair o relatorio para reports\audit-project-$N.md (scripts\extract-report.ps1, ADR-02)

# Etapa 2 - resposta "y" na mesma sessao -> Fase 3 (edicao + shell para boot/validacao)
claude -p --continue "y" --permission-mode acceptEdits `
  --allowedTools "Bash Read Write Edit Glob Grep" 2>&1 |
  Tee-Object -FilePath $Root\docs\evidence\project-$N\stage2.log

Set-Location $Root
```

Calibracao (ADR-10): rodar somente a etapa 1 e, se quiser encerrar sem refatorar, `claude -p --continue "n"`.
Entre tentativas: `scripts\reset-project.ps1 -Project N`.
Alternativa aceita: execucao interativa (`claude` e depois `/refactor-arch`, responder `y`), salvando o transcript.

## Avisos operacionais (aprendidos nas execucoes)

1. **Dispare a etapa 1 pelo PowerShell.** No Git Bash (MSYS), o argumento `/refactor-arch` e convertido em caminho do Windows
   (ex.: `C:/Program Files/Git/refactor-arch`) e a skill nao e invocada. Se precisar usar o Git Bash, desligue a conversao:
   `MSYS_NO_PATHCONV=1 claude -p "/refactor-arch" ...`.
2. **Redirecione o stdin.** Sem stdin, o `claude -p` espera e emite o aviso "no stdin data received". Use `< $null`
   (PowerShell, ex.: `claude -p "/refactor-arch" --permission-mode plan < $null`; se o parser recusar `<`, use `$null | claude -p ...`)
   ou `< /dev/null` (Bash).
3. **Grave os logs em UTF-8.** No PowerShell 5.1 o `Tee-Object` gravou UTF-16LE e a saida nativa e decodificada pela code page
   do console (acentos e `✓`/`├──` corrompidos). Antes de executar:
   ```powershell
   [Console]::OutputEncoding = [Text.Encoding]::UTF8
   $OutputEncoding = [Text.Encoding]::UTF8
   claude -p "/refactor-arch" --permission-mode plan < $null 2>&1 |
     Out-File -FilePath $Root\docs\evidence\project-$N\stage1.log -Encoding utf8
   ```
   (`Out-File -Encoding utf8` no PS 5.1 grava com BOM; o `scripts\extract-report.ps1` le UTF-8 com/sem BOM e UTF-16 e grava o
   relatorio em UTF-8 sem BOM.)
4. **So a ultima mensagem aparece no log do `-p`.** Por isso a skill exige que a mensagem final da Fase 2 traga o bloco PHASE 1,
   o relatorio e a pergunta juntos.
