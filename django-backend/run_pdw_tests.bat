@echo off
REM Run PDW Data Prep tests
REM Usage: run_pdw_tests.bat

echo.
echo ========================================
echo  PDW Data Prep Test Suite
echo ========================================
echo.

REM Check if Mars file exists
if not exist "..\Mars12022025.xlsx" (
    echo ERROR: Mars12022025.xlsx not found in project root
    echo Please place the Mars file at: %CD%\..\Mars12022025.xlsx
    echo.
    exit /b 1
)

echo Running tests...
echo.

python manage.py test pdw --verbosity=2

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  ALL TESTS PASSED!
    echo ========================================
    echo.
) else (
    echo.
    echo ========================================
    echo  TESTS FAILED!
    echo ========================================
    echo.
    exit /b 1
)
