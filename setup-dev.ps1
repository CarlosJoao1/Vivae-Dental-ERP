# Vivae Dental ERP - Development Setup Script
# Run this script from the project root directory

Write-Host "🦷 Vivae Dental ERP - Development Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (!(Test-Path "backend\app.py") -or !(Test-Path "frontend\package.json")) {
    Write-Host "❌ Error: Please run this script from the project root directory (where README.md is located)" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Current directory: $(Get-Location)" -ForegroundColor Green

# Check Python installation
Write-Host "`n🐍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion) {
        Write-Host "✅ $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Python not found. Please install Python 3.8+ from python.org" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Check Node.js installation
Write-Host "`n📦 Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Node.js not found. Please install Node.js from nodejs.org" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js from nodejs.org" -ForegroundColor Red
    exit 1
}

# Setup backend
Write-Host "`n🔧 Setting up backend..." -ForegroundColor Yellow

# Create virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Install backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
pip install -r backend\requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Backend dependencies installed" -ForegroundColor Green

# Setup backend .env file
if (!(Test-Path "backend\.env")) {
    Write-Host "Creating backend .env file..." -ForegroundColor Cyan
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "✅ Backend .env file created (you may want to customize it)" -ForegroundColor Green
} else {
    Write-Host "✅ Backend .env file already exists" -ForegroundColor Green
}

# Setup frontend  
Write-Host "`n🎨 Setting up frontend..." -ForegroundColor Yellow
Set-Location frontend

# Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
npm ci
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green

# Setup frontend .env file
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "Creating frontend .env file..." -ForegroundColor Cyan
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Frontend .env file created" -ForegroundColor Green
    } else {
        Write-Host "Creating frontend .env file with defaults..." -ForegroundColor Cyan
        "VITE_API_BASE=http://localhost:5000" | Out-File -FilePath ".env" -Encoding utf8
        Write-Host "✅ Frontend .env file created with defaults" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Frontend .env file already exists" -ForegroundColor Green
}

Set-Location ..

# Final instructions
Write-Host "`n🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Start MongoDB (or use Docker: docker run -d -p 27017:27017 mongo:7)" -ForegroundColor White
Write-Host "2. Start the backend:" -ForegroundColor White
Write-Host "   .venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   python backend\app.py" -ForegroundColor Gray
Write-Host "3. In a new terminal, start the frontend:" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host "4. Open http://localhost:5173 in your browser" -ForegroundColor White
Write-Host "5. Login with: admin / admin123" -ForegroundColor White

Write-Host "`n💡 Tip: You can also use Docker Compose:" -ForegroundColor Yellow
Write-Host "   docker compose up --build" -ForegroundColor Gray

Write-Host "`n🔗 Useful URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   Backend API: http://localhost:5000/api" -ForegroundColor White
Write-Host "   Health Check: http://localhost:5000/api/health" -ForegroundColor White