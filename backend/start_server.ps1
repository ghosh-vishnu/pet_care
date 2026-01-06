Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Dog Health AI Backend Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (Test-Path "dogai_venv\Scripts\activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "dogai_venv\Scripts\activate.ps1"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "WARNING: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it with: python -m venv dogai_venv" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Checking if uvicorn is installed..." -ForegroundColor Yellow
try {
    python -c "import uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "uvicorn not found. Installing..." -ForegroundColor Yellow
        pip install uvicorn[standard]
    }
} catch {
    Write-Host "Installing uvicorn..." -ForegroundColor Yellow
    pip install uvicorn[standard]
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start uvicorn server using python -m to ensure correct environment
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

