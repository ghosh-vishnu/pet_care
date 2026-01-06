@echo off
echo ========================================
echo Dog Breed Model Training
echo ========================================
echo.
echo This will train the breed detection model.
echo Estimated time: 15-22 hours on CPU
echo.
echo Training will run in the background.
echo You can check progress in the log file: training_log.txt
echo.
pause

REM Activate virtual environment if it exists
if exist "dogai_venv\Scripts\activate.bat" (
    call dogai_venv\Scripts\activate.bat
)

REM Run training and save output to log file
echo Starting training at %date% %time% > training_log.txt
echo ======================================== >> training_log.txt
python train_classifier.py >> training_log.txt 2>&1
echo. >> training_log.txt
echo Training completed at %date% %time% >> training_log.txt

echo.
echo Training completed! Check training_log.txt for results.
pause


