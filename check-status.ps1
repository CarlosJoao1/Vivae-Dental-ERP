# Vivae Dental ERP - System Status Check
# Checks if the system is running properly

Write-Host "🦷 Vivae Dental ERP - System Status Check" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$backendUrl = "http://localhost:5000"
$frontendUrl = "http://localhost:5173"

# Check backend health
Write-Host "`n🔧 Checking backend status..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$backendUrl/api/health" -Method Get -TimeoutSec 5
    if ($response) {
        Write-Host "✅ Backend is running at $backendUrl" -ForegroundColor Green
        if ($response.ok) {
            Write-Host "   Status: $($response.status)" -ForegroundColor Gray
        }
        if ($response.version) {
            Write-Host "   Version: $($response.version)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "❌ Backend not accessible at $backendUrl" -ForegroundColor Red
    Write-Host "   Make sure to run: python backend\app.py" -ForegroundColor Gray
}

# Check backend info endpoint
Write-Host "`n📊 Checking backend info..." -ForegroundColor Yellow
try {
    $infoResponse = Invoke-RestMethod -Uri "$backendUrl/api/health/info" -Method Get -TimeoutSec 5
    if ($infoResponse) {
        Write-Host "✅ Backend info available" -ForegroundColor Green
        if ($infoResponse.version) {
            Write-Host "   App Version: $($infoResponse.version)" -ForegroundColor Gray
        }
        if ($infoResponse.branch) {
            Write-Host "   Branch: $($infoResponse.branch)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "⚠️  Backend info endpoint not available" -ForegroundColor Yellow
}

# Check frontend
Write-Host "`n🎨 Checking frontend status..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method Get -TimeoutSec 5 -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend is running at $frontendUrl" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend not accessible at $frontendUrl" -ForegroundColor Red
    Write-Host "   Make sure to run: cd frontend && npm run dev" -ForegroundColor Gray
}

# Check MongoDB (if accessible)
Write-Host "`n🗄️  Checking MongoDB connection..." -ForegroundColor Yellow
try {
    $mongoResponse = Invoke-RestMethod -Uri "$backendUrl/api/health/db" -Method Get -TimeoutSec 5
    if ($mongoResponse -and $mongoResponse.db_status) {
        Write-Host "✅ MongoDB connection: $($mongoResponse.db_status)" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  MongoDB status not available (may need /api/health/db endpoint)" -ForegroundColor Yellow
}

Write-Host "`n📋 Quick Commands:" -ForegroundColor Cyan
Write-Host "Start backend:  python backend\app.py" -ForegroundColor Gray
Write-Host "Start frontend: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host "Start MongoDB:  docker run -d -p 27017:27017 mongo:7" -ForegroundColor Gray
Write-Host "Full stack:     docker compose up --build" -ForegroundColor Gray

Write-Host "`n🔗 URLs:" -ForegroundColor Cyan
Write-Host "Frontend: $frontendUrl" -ForegroundColor White
Write-Host "Backend:  $backendUrl/api" -ForegroundColor White
Write-Host "Health:   $backendUrl/api/health" -ForegroundColor White