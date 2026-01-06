# Dog Breed Model Training Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dog Breed Model Training" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will train the breed detection model." -ForegroundColor Yellow
Write-Host "Estimated time: 15-22 hours on CPU" -ForegroundColor Yellow
Write-Host ""
Write-Host "Training will run in the background." -ForegroundColor Green
Write-Host "You can check progress in the log file: training_log.txt" -ForegroundColor Green
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path "dogai_venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Blue
    .\dogai_venv\Scripts\Activate.ps1
}

# Get start time
$startTime = Get-Date
Write-Host "Training started at: $startTime" -ForegroundColor Green
Write-Host ""

# Run training and save output to log file
Write-Host "Starting training... Check training_log.txt for progress." -ForegroundColor Blue
$startTimeStr = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"Training started at: $startTimeStr" | Out-File -FilePath "training_log.txt" -Encoding utf8
"=" * 50 | Out-File -FilePath "training_log.txt" -Append -Encoding utf8

# Run training
python train_classifier.py 2>&1 | Tee-Object -FilePath "training_log.txt" -Append

# Get end time
$endTime = Get-Date
$duration = $endTime - $startTime
$endTimeStr = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Training Completed!" -ForegroundColor Green
Write-Host "Total time: $($duration.Hours) hours, $($duration.Minutes) minutes" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check training_log.txt for full results." -ForegroundColor Yellow

"`nTraining completed at: $endTimeStr" | Out-File -FilePath "training_log.txt" -Append -Encoding utf8
"Total duration: $($duration.Hours) hours, $($duration.Minutes) minutes" | Out-File -FilePath "training_log.txt" -Append -Encoding utf8


