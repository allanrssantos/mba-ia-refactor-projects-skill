# Wrapper: smoke test do projeto 1. Parametros extras sao repassados (ex.: -Out x.txt -AdminToken abc).
& "$PSScriptRoot\smoke.ps1" -Project 1 @args
exit $LASTEXITCODE
