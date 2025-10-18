# Asset Integration Script for VIVAE ERP
# This script copies assets to the appropriate locations in the project

param(
    [switch]$Force,
    [string]$AssetsPath = "assets"
)

Write-Host "🎨 VIVAE ERP - Asset Integration Script" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

$RootPath = $PSScriptRoot
$AssetsSourcePath = Join-Path $RootPath $AssetsPath
$FrontendPublicPath = Join-Path $RootPath "frontend/public/assets"

# Check if assets directory exists
if (-not (Test-Path $AssetsSourcePath)) {
    Write-Host "❌ Assets directory not found: $AssetsSourcePath" -ForegroundColor Red
    exit 1
}

# Create frontend public assets directory if it doesn't exist
if (-not (Test-Path $FrontendPublicPath)) {
    New-Item -ItemType Directory -Path $FrontendPublicPath -Force | Out-Null
    Write-Host "📁 Created frontend assets directory" -ForegroundColor Green
}

# Copy logos
$LogosSource = Join-Path $AssetsSourcePath "logos"
$LogosTarget = Join-Path $FrontendPublicPath "logos"

if (Test-Path $LogosSource) {
    if (-not (Test-Path $LogosTarget) -or $Force) {
        Copy-Item -Path $LogosSource -Destination $LogosTarget -Recurse -Force
        Write-Host "📸 Copied logos to frontend" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Logos already exist in frontend (use -Force to overwrite)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  No logos directory found in assets" -ForegroundColor Yellow
}

# Copy images
$ImagesSource = Join-Path $AssetsSourcePath "images"
$ImagesTarget = Join-Path $FrontendPublicPath "images"

if (Test-Path $ImagesSource) {
    if (-not (Test-Path $ImagesTarget) -or $Force) {
        Copy-Item -Path $ImagesSource -Destination $ImagesTarget -Recurse -Force
        Write-Host "🖼️  Copied images to frontend" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Images already exist in frontend (use -Force to overwrite)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  No images directory found in assets" -ForegroundColor Yellow
}

# Check for favicon and copy to root of public
$FaviconSource = Join-Path $LogosSource "favicon.ico"
$FaviconTarget = Join-Path $RootPath "frontend/public/favicon.ico"

if (Test-Path $FaviconSource) {
    Copy-Item -Path $FaviconSource -Destination $FaviconTarget -Force
    Write-Host "🌐 Copied favicon to public root" -ForegroundColor Green
} else {
    Write-Host "⚠️  No favicon.ico found in logos directory" -ForegroundColor Yellow
}

# List what assets are available
Write-Host "`n📋 Available Assets:" -ForegroundColor Cyan
Get-ChildItem -Path $AssetsSourcePath -Recurse -File | ForEach-Object {
    $RelativePath = $_.FullName.Replace($AssetsSourcePath + "\", "")
    Write-Host "   $RelativePath" -ForegroundColor Gray
}

Write-Host "`n✅ Asset integration complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Place your generated images in the assets/ directory" -ForegroundColor White
Write-Host "2. Run this script again with -Force to update frontend" -ForegroundColor White
Write-Host "3. Update HTML references in frontend/index.html" -ForegroundColor White
Write-Host "4. Import assets in React components as needed" -ForegroundColor White