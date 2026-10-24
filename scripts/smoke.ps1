<#
.SYNOPSIS
  Smoke test generico: sobe a app com o comando ORIGINAL, chama todos os endpoints da SPEC 7.5,
  grava "METODO path -> status" e derruba o processo. Funciona antes e depois da refatoracao (ADR-06).

.PARAMETER Project
  1 = code-smells-project (Flask, :5000) | 2 = ecommerce-api-legacy (Express, :3000) | 3 = task-manager-api (Flask, :5000)
.PARAMETER Out
  Arquivo de saida. Padrao: docs/evidence/project-N/baseline-before.txt
.PARAMETER AdminToken
  Se informado, exporta ADMIN_TOKEN para a app e envia X-Admin-Token nas rotas admin (ADR-03).
  Sem token: o header nao e enviado; o status obtido (200 no original, 403 no refatorado) e registrado.
.PARAMETER KeepDb
  Nao apaga os *.db ao final (por padrao apaga antes e depois).
#>
param(
  [Parameter(Mandatory = $true)][ValidateSet(1, 2, 3)][int]$Project,
  [string]$Out,
  [string]$AdminToken = $env:ADMIN_TOKEN,
  [int]$BootTimeoutSec = 30,
  [switch]$KeepDb
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Cfg = @{
  1 = @{ Dir = 'code-smells-project';  Port = 5000; Kind = 'py';  Seed = $false }
  2 = @{ Dir = 'ecommerce-api-legacy'; Port = 3000; Kind = 'npm'; Seed = $false }
  3 = @{ Dir = 'task-manager-api';     Port = 5000; Kind = 'py';  Seed = $true }
}[$Project]
$ProjDir = Join-Path $Root $Cfg.Dir
$Base = "http://localhost:$($Cfg.Port)"
if (-not $Out) { $Out = Join-Path $Root "docs/evidence/project-$Project/baseline-before.txt" }
if (-not [IO.Path]::IsPathRooted($Out)) { $Out = Join-Path (Get-Location) $Out }
$Out = [IO.Path]::GetFullPath($Out)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null
$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("smoke-p$Project-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

function Test-PortOpen([int]$Port) {
  $c = New-Object Net.Sockets.TcpClient
  try {
    $iar = $c.BeginConnect('127.0.0.1', $Port, $null, $null)
    return ($iar.AsyncWaitHandle.WaitOne(300) -and $c.Connected)
  } catch { return $false } finally { $c.Close() }
}
function Remove-Dbs {
  Get-ChildItem -Path $ProjDir -Recurse -Include *.db -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\(\.venv|node_modules)\\' } |
    Remove-Item -Force -ErrorAction SilentlyContinue
}
function Stop-Tree([int]$ProcId) { & taskkill.exe /PID $ProcId /T /F 2>&1 | Out-Null }

# Plano: M=metodo, P=path, B=corpo JSON (ou $null), A=rota admin, Cap=nome para capturar o "id" da resposta
function Step($M, $P, $B = $null, [switch]$A, $Cap = $null) { @{ M = $M; P = $P; B = $B; A = [bool]$A; Cap = $Cap } }

switch ($Project) {
  1 { $Plan = @(
      Step GET '/'
      Step GET '/health'
      Step GET '/produtos'
      Step GET '/produtos/1'
      Step GET '/produtos/9999'
      Step GET '/produtos/busca?q=a'
      Step POST '/produtos' '{"nome":"Produto Smoke","descricao":"d","preco":10.5,"estoque":5,"categoria":"geral"}' -Cap prod
      Step POST '/produtos' '{}'
      Step PUT '/produtos/1' '{"nome":"Produto Atualizado","descricao":"d","preco":20.0,"estoque":7,"categoria":"geral"}'
      Step PUT '/produtos/9999' '{"nome":"x","preco":1,"estoque":1}'
      Step GET '/usuarios'
      Step GET '/usuarios/1'
      Step GET '/usuarios/9999'
      Step POST '/usuarios' '{"nome":"Smoke User","email":"smoke@teste.com","senha":"smoke123"}'
      Step POST '/usuarios' '{}'
      Step POST '/login' '{"email":"admin@loja.com","senha":"admin123"}'
      Step POST '/login' '{"email":"admin@loja.com","senha":"errada"}'
      Step POST '/pedidos' '{"usuario_id":1,"itens":[{"produto_id":1,"quantidade":1}]}'
      Step POST '/pedidos' '{"usuario_id":1,"itens":[]}'
      Step GET '/pedidos'
      Step GET '/pedidos/usuario/1'
      Step PUT '/pedidos/1/status' '{"status":"aprovado"}'
      Step PUT '/pedidos/1/status' '{"status":"invalido"}'
      Step GET '/relatorios/vendas'
      Step DELETE '/produtos/{prod}'
      Step DELETE '/produtos/9999'
      Step POST '/admin/query' '{"sql":"SELECT 1 AS x"}' -A
      Step POST '/admin/query' '{}' -A
      Step POST '/admin/reset-db' -A
  ) }
  2 { $Plan = @(
      Step POST '/api/checkout' '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
      Step POST '/api/checkout' '{"usr":"Joao","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
      Step POST '/api/checkout' '{}'
      Step POST '/api/checkout' '{"usr":"X","eml":"x@x.com","pwd":"1","c_id":999,"card":"4111"}'
      Step GET '/api/admin/financial-report' -A
      Step DELETE '/api/users/1'
  ) }
  3 { $Plan = @(
      Step GET '/'
      Step GET '/health'
      Step GET '/tasks'
      Step GET '/tasks/1'
      Step GET '/tasks/9999'
      Step GET '/tasks/search?q=api'
      Step GET '/tasks/stats'
      Step GET '/users'
      Step GET '/users/1'
      Step GET '/users/9999'
      Step GET '/users/1/tasks'
      Step GET '/reports/summary'
      Step GET '/reports/user/1'
      Step GET '/reports/user/9999'
      Step GET '/categories'
      Step POST '/login' '{"email":"joao@email.com","password":"1234"}'
      Step POST '/login' '{"email":"joao@email.com","password":"errada"}'
      Step POST '/users' '{"name":"Smoke User","email":"smoke@teste.com","password":"smoke123","role":"user"}' -Cap user
      Step POST '/users' '{}'
      Step POST '/categories' '{"name":"Smoke Cat","description":"d","color":"#123456"}' -Cap cat
      Step POST '/categories' '{}'
      Step POST '/tasks' '{"title":"Task Smoke","description":"d","status":"pending","priority":3,"user_id":1,"category_id":1}' -Cap task
      Step POST '/tasks' '{}'
      Step PUT '/tasks/{task}' '{"title":"Task Smoke Atualizada","status":"in_progress","priority":2}'
      Step PUT '/tasks/9999' '{"title":"abc"}'
      Step PUT '/users/{user}' '{"name":"Smoke User 2"}'
      Step PUT '/users/9999' '{"name":"abc"}'
      Step PUT '/categories/{cat}' '{"name":"Smoke Cat 2"}'
      Step PUT '/categories/9999' '{"name":"abc"}'
      Step DELETE '/tasks/{task}'
      Step DELETE '/tasks/9999'
      Step DELETE '/users/{user}'
      Step DELETE '/users/9999'
      Step DELETE '/categories/{cat}'
      Step DELETE '/categories/9999'
  ) }
}

# --- pre-condicoes ---
if (Test-PortOpen $Cfg.Port) { throw "Porta $($Cfg.Port) ja esta em uso. Encerre o processo antes (um projeto por vez)." }
if (-not $KeepDb) { Remove-Dbs }

# --- comando de boot ORIGINAL (python app.py / npm start) ---
$env:PYTHONUNBUFFERED = '1'; $env:PYTHONIOENCODING = 'utf-8'
if ($AdminToken) { $env:ADMIN_TOKEN = $AdminToken } else { Remove-Item Env:ADMIN_TOKEN -ErrorAction SilentlyContinue }
if ($Cfg.Kind -eq 'py') {
  $venvPy = Join-Path $ProjDir '.venv\Scripts\python.exe'
  $py = if (Test-Path $venvPy) { $venvPy } else { 'python' }
  if ($Cfg.Seed -and (Test-Path (Join-Path $ProjDir 'seed.py'))) {
    $sp = Start-Process -FilePath $py -ArgumentList @('seed.py') -WorkingDirectory $ProjDir -Wait -PassThru -WindowStyle Hidden `
      -RedirectStandardOutput (Join-Path $Tmp 'seed.out.log') -RedirectStandardError (Join-Path $Tmp 'seed.err.log')
    if ($sp.ExitCode -ne 0) { Write-Warning "seed.py saiu com $($sp.ExitCode)" }
  }
  $exe = $py; $argList = @('app.py')
} else {
  $exe = (Get-Command npm.cmd).Source; $argList = @('start')
}
$outLog = Join-Path $Tmp 'boot.out.log'; $errLog = Join-Path $Tmp 'boot.err.log'
$proc = Start-Process -FilePath $exe -ArgumentList $argList -WorkingDirectory $ProjDir -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput $outLog -RedirectStandardError $errLog

$lines = New-Object System.Collections.Generic.List[string]
$bootOk = $false
try {
  $deadline = (Get-Date).AddSeconds($BootTimeoutSec)
  while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) { break }
    if (Test-PortOpen $Cfg.Port) { $bootOk = $true; break }
    Start-Sleep -Milliseconds 500
  }
  $tok = if ($AdminToken) { 'set' } else { 'unset' }
  $lines.Add("# project-$Project ($($Cfg.Dir)) base=$Base admin_token=$tok")
  if (-not $bootOk) {
    $lines.Add('BOOT FAILED')
    Write-Warning 'Aplicacao nao subiu (ver boot log).'
  } else {
    Start-Sleep -Milliseconds 800
    $captured = @{}
    $n = 0
    foreach ($s in $Plan) {
      $n++
      $path = $s.P
      foreach ($k in @($captured.Keys)) { $path = $path.Replace("{$k}", [string]$captured[$k]) }
      if ($path -match '\{\w+\}') { $path = [regex]::Replace($path, '\{\w+\}', '9998') }  # captura falhou: id inexistente
      $respFile = Join-Path $Tmp "resp$n.txt"
      $curlArgs = @('-s', '-o', $respFile, '-w', '%{http_code}', '--max-time', '20', '-X', $s.M)
      if ($s.B) {
        $bf = Join-Path $Tmp "body$n.json"
        [IO.File]::WriteAllText($bf, $s.B, (New-Object Text.UTF8Encoding($false)))
        $curlArgs += @('-H', 'Content-Type: application/json', '--data-binary', "@$bf")
      } elseif ($s.M -in 'POST', 'PUT') {
        $curlArgs += @('-H', 'Content-Type: application/json', '--data-binary', '{}')
      }
      if ($s.A -and $AdminToken) { $curlArgs += @('-H', "X-Admin-Token: $AdminToken") }
      $curlArgs += "$Base$path"
      $code = (& curl.exe @curlArgs 2>$null)
      if (-not $code) { $code = '000' }
      if ($s.Cap -and (Test-Path $respFile)) {
        $txt = Get-Content -Raw -Path $respFile -ErrorAction SilentlyContinue
        if ($txt -match '"id"\s*:\s*(\d+)') { $captured[$s.Cap] = $Matches[1] }
      }
      $lines.Add(('{0,-6} {1} -> {2}' -f $s.M, $path, $code))
    }
    if ($proc.HasExited) { $lines.Add('WARNING: processo encerrou durante o teste') }
  }
} finally {
  Stop-Tree $proc.Id
  Start-Sleep -Milliseconds 800
  if (Test-PortOpen $Cfg.Port) { Write-Warning "Porta $($Cfg.Port) ainda aberta apos encerrar o processo." }
  $bootLog = ($Out -replace '\.[^.\\/]+$', '') + '-boot.log'
  $b = @('== stdout ==')
  if (Test-Path $outLog) { $b += Get-Content $outLog -Encoding UTF8 -ErrorAction SilentlyContinue }
  $b += '== stderr =='
  if (Test-Path $errLog) { $b += Get-Content $errLog -Encoding UTF8 -ErrorAction SilentlyContinue }
  Set-Content -Path $bootLog -Value $b -Encoding UTF8
  if (-not $KeepDb) { Remove-Dbs }
  Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
  Remove-Item Env:ADMIN_TOKEN -ErrorAction SilentlyContinue
}

Set-Content -Path $Out -Value $lines -Encoding ASCII
$lines | ForEach-Object { Write-Host $_ }
Write-Host "Saida: $Out"
if (-not $bootOk) { exit 1 }
