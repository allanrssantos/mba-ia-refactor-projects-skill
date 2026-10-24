<#
.SYNOPSIS
  Restaura um projeto ao estado do HEAD (ADR-10): git checkout -- <pasta> + git clean -fd <pasta>,
  preservando .venv, node_modules e .claude (e demais ignorados pelo Git, pois nao usa -x).
.PARAMETER Project  1 = code-smells-project | 2 = ecommerce-api-legacy | 3 = task-manager-api
#>
param([Parameter(Mandatory = $true)][ValidateSet(1, 2, 3)][int]$Project)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Dir = @{ 1 = 'code-smells-project'; 2 = 'ecommerce-api-legacy'; 3 = 'task-manager-api' }[$Project]
Push-Location $Root
try {
  git checkout -- $Dir ":(exclude)$Dir/.claude"
  if ($LASTEXITCODE -ne 0) { throw 'git checkout falhou' }
  # -e: protege .claude mesmo que ele nao esteja ignorado (a skill e versionada); .venv/node_modules ja sao ignorados
  git clean -fd -e .claude -e .venv -e node_modules -- $Dir
  if ($LASTEXITCODE -ne 0) { throw 'git clean falhou' }
  Write-Host "Projeto $Project ($Dir) restaurado para o HEAD."
  git status --short -- $Dir
} finally { Pop-Location }
