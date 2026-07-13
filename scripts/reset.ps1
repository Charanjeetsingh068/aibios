# AI-BOS Complete Reset Script (Windows PowerShell)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Red
Write-Host "   Resetting AI-BOS Enterprise Workspace...              " -ForegroundColor Red
Write-Host "==========================================================" -ForegroundColor Red

# 1. Delete Dependencies & Builds
Write-Host "`n[1/2] Cleaning package and environment folders..." -ForegroundColor Yellow

$cleanTargets = @(
    "backend/.venv",
    "node_modules",
    "frontend/node_modules",
    "frontend/.next",
    "mobile/node_modules"
)

foreach ($target in $cleanTargets) {
    if (Test-Path $target) {
        Write-Host "Deleting $target..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $target -ErrorAction SilentlyContinue
    }
}
Write-Host "Clean completed successfully." -ForegroundColor Green

# 2. Rerun Setup
Write-Host "`n[2/2] Re-executing system setup.ps1..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File ./setup.ps1
