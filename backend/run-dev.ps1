# Script PowerShell para rodar o backend com variáveis de ambiente do Git
$env:GIT_BRANCH = git rev-parse --abbrev-ref HEAD
$env:GIT_COMMIT = git rev-parse HEAD
$env:RENDER_BUILD_TIME = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

Write-Host "Starting backend with:" -ForegroundColor Green
Write-Host "  Branch: $env:GIT_BRANCH" -ForegroundColor Cyan
Write-Host "  Commit: $($env:GIT_COMMIT.Substring(0, 7))" -ForegroundColor Cyan
Write-Host "  Build Time: $env:RENDER_BUILD_TIME" -ForegroundColor Cyan
Write-Host ""

# Ativa o ambiente virtual se existir
if (Test-Path "venv\Scripts\Activate.ps1") {
    & venv\Scripts\Activate.ps1
}

# Inicia o Flask
python app.py
