# Wrapper: smoke test do projeto 2. Parametros extras sao repassados (ex.: -Out x.txt -AdminToken abc).
& "$PSScriptRoot\smoke.ps1" -Project 2 @args
exit $LASTEXITCODE
