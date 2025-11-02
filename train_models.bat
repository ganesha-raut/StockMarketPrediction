@echo off
echo ============================================================
echo AI STOCK PREDICTION - MODEL TRAINING
echo ============================================================
echo.
echo This will train ML models for all stocks.
echo Time required: 5-10 minutes
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Starting training...
echo.

.\venv\Scripts\python.exe train_all_models.py

echo.
echo ============================================================
echo Training Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Restart Flask app if it's running
echo 2. Go to admin panel to verify models
echo 3. Try making predictions!
echo.
pause
