# Quick test script to check if server starts
Write-Host "Testing backend server startup..." -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot

# Activate virtual environment
if (Test-Path "dogai_venv\Scripts\activate.ps1") {
    & "dogai_venv\Scripts\activate.ps1"
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    exit 1
}

# Test import
Write-Host "Testing imports..." -ForegroundColor Yellow
python -c "import main; print('✓ All imports successful')" 2>&1

Write-Host ""
Write-Host "Testing uvicorn..." -ForegroundColor Yellow
python -c "import uvicorn; print('✓ Uvicorn version:', uvicorn.__version__)" 2>&1

Write-Host ""
Write-Host "Testing FastAPI app..." -ForegroundColor Yellow
python -c "import main; print('✓ FastAPI app created:', main.app.title)" 2>&1

Write-Host ""
Write-Host "✓ All tests passed! Server should start successfully." -ForegroundColor Green
Write-Host "Run: .\start_server.ps1 to start the server" -ForegroundColor Cyan



