# VIVAE ERP - Seed Production Data to Render
# Script PowerShell simplificado para Windows

Write-Host "`n🌱 VIVAE ERP - Production Data Seed Helper" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# 1. Verificar se está no diretório correto
$currentDir = Get-Location
if (-not (Test-Path "backend\scripts\seed_production_remote.py")) {
    Write-Host "`n❌ Error: Must run from project root directory" -ForegroundColor Red
    Write-Host "Current: $currentDir" -ForegroundColor Yellow
    Write-Host "Expected: .../Vivae-Dental-ERP/" -ForegroundColor Yellow
    exit 1
}

# 2. Solicitar MongoDB URI
Write-Host "`n📝 Step 1: MongoDB Production URI" -ForegroundColor Green
Write-Host "Get this from Render Dashboard → vivae-backend → Environment → MONGO_URI"
$mongoUri = Read-Host "Enter MONGO_URI_PRODUCTION"

if ([string]::IsNullOrWhiteSpace($mongoUri)) {
    Write-Host "❌ MongoDB URI is required" -ForegroundColor Red
    exit 1
}

# 3. Solicitar Laboratory ID
Write-Host "`n📝 Step 2: Laboratory ID" -ForegroundColor Green
Write-Host "Get this from your database or via API"
Write-Host "Leave blank if you want to be prompted during seed"
$labId = Read-Host "Enter PRODUCTION_LAB_ID (optional)"

# 4. Confirmar dados
Write-Host "`n📋 Configuration:" -ForegroundColor Yellow
Write-Host "  MongoDB URI: $($mongoUri.Substring(0, [Math]::Min(50, $mongoUri.Length)))..."
if (-not [string]::IsNullOrWhiteSpace($labId)) {
    Write-Host "  Laboratory ID: $labId"
} else {
    Write-Host "  Laboratory ID: Will be prompted during seed"
}

# 5. Confirmar execução
Write-Host "`n⚠️  WARNING: This will seed data to PRODUCTION!" -ForegroundColor Red
$confirm = Read-Host "Continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "`n❌ Operation cancelled" -ForegroundColor Yellow
    exit 0
}

# 6. Configurar variáveis de ambiente
$env:MONGO_URI_PRODUCTION = $mongoUri
if (-not [string]::IsNullOrWhiteSpace($labId)) {
    $env:PRODUCTION_LAB_ID = $labId
}

# 7. Verificar se Python está disponível
Write-Host "`n🔍 Checking Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found in PATH" -ForegroundColor Red
    Write-Host "Install Python or add to PATH" -ForegroundColor Yellow
    exit 1
}

# 8. Verificar dependências
Write-Host "`n🔍 Checking dependencies..." -ForegroundColor Cyan
$requirementsExist = Test-Path "backend\requirements.txt"
if ($requirementsExist) {
    Write-Host "✅ requirements.txt found" -ForegroundColor Green
    $installDeps = Read-Host "Install/update dependencies? (yes/no)"
    if ($installDeps -eq "yes") {
        Write-Host "`n📦 Installing dependencies..." -ForegroundColor Cyan
        Set-Location backend
        python -m pip install -r requirements.txt
        Set-Location ..
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    }
}

# 9. Executar seed script
Write-Host "`n🚀 Executing seed script..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

try {
    Set-Location backend\scripts
    python seed_production_remote.py
    $exitCode = $LASTEXITCODE
    Set-Location ..\..
    
    if ($exitCode -eq 0) {
        Write-Host "`n✅ Seed completed successfully!" -ForegroundColor Green
        Write-Host "`n🎯 Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Open https://vivae-frontend.onrender.com"
        Write-Host "  2. Login with your credentials"
        Write-Host "  3. Navigate to Production → Planning"
        Write-Host "  4. Verify demo data is present"
    } else {
        Write-Host "`n❌ Seed failed with exit code: $exitCode" -ForegroundColor Red
    }
} catch {
    Write-Host "`n❌ Error executing seed script: $_" -ForegroundColor Red
    Set-Location ..\..
    exit 1
}

Write-Host "`n" -ForegroundColor White
