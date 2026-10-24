# Wrapper: smoke test do projeto 3. Parametros extras sao repassados (ex.: -Out x.txt -AdminToken abc).
& "$PSScriptRoot\smoke.ps1" -Project 3 @args
exit $LASTEXITCODE
