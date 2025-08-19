@echo off
echo ========================================
echo    EduPredict AI - Student Performance
echo         Prediction System
echo ========================================
echo.
echo Starting the application...
echo.
echo Please wait while the system initializes...
echo.
echo Once started, open your browser to:
echo http://localhost:5000
echo.
echo Demo Accounts:
echo - Student: student1 / student123
echo - Teacher: teacher1 / teacher123  
echo - Admin: admin / admin123
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

set PYTHONPATH=%CD%
python scripts/app.py

pause
