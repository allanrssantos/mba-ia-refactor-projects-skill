<#
.SYNOPSIS
  Extrai o relatorio da Fase 2 (ARCHITECTURE AUDIT REPORT) de um log de execucao da skill
  refactor-arch e grava o bloco em UTF-8 sem BOM (ADR-02).

.DESCRIPTION
  Recorta do log o trecho que vai da linha "====" imediatamente anterior a primeira linha
  "ARCHITECTURE AUDIT REPORT" ate a linha "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"
  (inclusive). Remove apenas ruido de terminal: sequencias ANSI, CR e linhas que sao so cercas
  de codigo Markdown (```). O conteudo do relatorio nao e alterado (R-03).

  O log pode estar em UTF-8 (com ou sem BOM) ou UTF-16 (ex.: Tee-Object do PowerShell 5.1);
  a codificacao e detectada pelo BOM. Ao capturar a saida do claude no PowerShell 5.1, rode antes
  [Console]::OutputEncoding = [Text.Encoding]::UTF8 para nao corromper acentos e simbolos.

.PARAMETER Log
  Arquivo de log com a saida da execucao (ex.: docs\evidence\project-1\stage1.log).

.PARAMETER Out
  Arquivo de destino (ex.: reports\audit-project-1.md). Diretorios ausentes sao criados.

.EXAMPLE
  .\scripts\extract-report.ps1 -Log docs\evidence\project-1\stage1.log -Out reports\audit-project-1.md
#>
param(
  [Parameter(Mandatory = $true)][string]$Log,
  [Parameter(Mandatory = $true)][string]$Out
)

$ErrorActionPreference = 'Stop'

$logPath = (Resolve-Path -LiteralPath $Log).Path
$text = [IO.File]::ReadAllText($logPath)          # detecta UTF-8/UTF-16 pelo BOM; sem BOM assume UTF-8

$esc = [char]27
$text = [regex]::Replace($text, "$esc\[[0-9;?]*[ -/]*[@-~]", '')     # CSI (cores, cursor)
$text = [regex]::Replace($text, "$esc\][^\a$esc]*(\a|$esc\\)", '')    # OSC (titulo, hyperlinks)
$lines = $text -replace "`r", '' -split "`n"

$headerIdx = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i].Trim() -eq 'ARCHITECTURE AUDIT REPORT') { $headerIdx = $i; break }
}
if ($headerIdx -lt 0) { throw "Linha 'ARCHITECTURE AUDIT REPORT' nao encontrada em $logPath" }

$startIdx = $headerIdx
if ($headerIdx -gt 0 -and $lines[$headerIdx - 1].Trim() -match '^=+$') { $startIdx = $headerIdx - 1 }

$question = 'Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]'
$endIdx = -1
for ($i = $headerIdx + 1; $i -lt $lines.Count; $i++) {
  if ($lines[$i].Trim() -eq $question) { $endIdx = $i; break }
}
if ($endIdx -lt 0) { throw "Linha '$question' nao encontrada apos o cabecalho do relatorio em $logPath" }

$block = $lines[$startIdx..$endIdx] |
  Where-Object { $_ -notmatch '^\s*```[A-Za-z]*\s*$' } |
  ForEach-Object { $_.TrimEnd() }

$outPath = if ([IO.Path]::IsPathRooted($Out)) { [IO.Path]::GetFullPath($Out) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Out)) }
$outDir = Split-Path -Parent $outPath
if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
[IO.File]::WriteAllText($outPath, (($block -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))

# Conferencia rapida do template (CA-02, CA-13): Total x blocos "### [" x Summary
$findings = @($block | Where-Object { $_ -match '^### \[(CRITICAL|HIGH|MEDIUM|LOW)\]' })
$totalLine = $block | Where-Object { $_ -match '^Total:\s*(\d+)\s+findings' } | Select-Object -First 1
$total = if ($totalLine -and $totalLine -match '(\d+)') { [int]$Matches[1] } else { -1 }
$summaryLine = $block | Where-Object { $_ -match '^CRITICAL:\s*\d+' } | Select-Object -First 1

Write-Host "Relatorio gravado: $outPath ($($block.Count) linhas, UTF-8 sem BOM)"
Write-Host "Summary: $summaryLine"
Write-Host "Total declarado: $total | blocos '### [': $($findings.Count)"
if ($total -ne $findings.Count) { Write-Warning "Total declarado difere do numero de findings listados." }
