<#
.SYNOPSIS
  Copia a skill refactor-arch da fonte (code-smells-project) para os outros 2 projetos e confere
  o hash SHA256 arquivo a arquivo (ADR-13). Falha com mensagem clara se a fonte nao existir.
#>
param([switch]$CheckOnly)   # -CheckOnly: apenas verifica, sem copiar

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Rel = '.claude\skills\refactor-arch'
$Src = Join-Path $Root "code-smells-project\$Rel"
$Dsts = @('ecommerce-api-legacy', 'task-manager-api') | ForEach-Object { Join-Path $Root "$_\$Rel" }

if (-not (Test-Path -LiteralPath $Src -PathType Container)) {
  Write-Error "Fonte da skill nao encontrada: $Src`nCrie a skill em code-smells-project/.claude/skills/refactor-arch/ antes de sincronizar."
  exit 1
}
$srcFiles = Get-ChildItem -LiteralPath $Src -Recurse -File
if (-not $srcFiles) { Write-Error "A pasta da skill esta vazia: $Src"; exit 1 }

function Get-RelHashes($dir) {
  $h = @{}
  Get-ChildItem -LiteralPath $dir -Recurse -File | ForEach-Object {
    $h[$_.FullName.Substring($dir.Length).TrimStart('\')] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
  }
  $h
}

$srcHash = Get-RelHashes $Src
$fail = 0
foreach ($d in $Dsts) {
  if (-not $CheckOnly) {
    if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force }   # evita arquivos orfaos
    New-Item -ItemType Directory -Force -Path $d | Out-Null
    Copy-Item -Path (Join-Path $Src '*') -Destination $d -Recurse -Force
  }
  if (-not (Test-Path -LiteralPath $d)) { Write-Host "FALTA: $d"; $fail++; continue }
  $dh = Get-RelHashes $d
  foreach ($k in $srcHash.Keys) {
    if (-not $dh.ContainsKey($k)) { Write-Host "FALTA   $d :: $k"; $fail++ }
    elseif ($dh[$k] -ne $srcHash[$k]) { Write-Host "DIFERE  $d :: $k"; $fail++ }
    else { Write-Host "OK      $k -> $(Split-Path -Leaf (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $d))))" }
  }
  foreach ($k in $dh.Keys) { if (-not $srcHash.ContainsKey($k)) { Write-Host "EXTRA   $d :: $k"; $fail++ } }
}
if ($fail -gt 0) { Write-Error "$fail divergencia(s) entre as copias da skill."; exit 1 }
Write-Host "Skill identica nas 3 copias ($($srcHash.Count) arquivos)."
