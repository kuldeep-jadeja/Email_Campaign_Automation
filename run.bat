@echo off
echo Starting Email Automation System (without Docker)
echo ================================================

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please make sure .env file exists with your configuration.
    pause
    exit /b 1
)

REM Display available commands
echo Available commands:
echo.
echo 1. run-dispatcher        - Run the main dispatcher once
echo 2. run-continuous        - Run dispatcher continuously
echo 3. check-runtime-states  - Check account runtime states
echo 4. fix-runtime-states    - Fix problematic runtime states
echo 5. list-campaigns        - List all campaigns
echo 6. list-leads            - List campaign leads
echo 7. exit                  - Exit
echo.

:menu
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" (
    echo Running dispatcher once...
    python -m app.cli.main run-dispatcher --verbose
    goto menu
)
if "%choice%"=="2" (
    echo Running dispatcher continuously...
    echo Press Ctrl+C to stop
    python -m app.cli.main run-continuous
    goto menu
)
if "%choice%"=="3" (
    echo Checking runtime states...
    python -m app.cli.main check-runtime-states
    goto menu
)
if "%choice%"=="4" (
    echo Fixing runtime states...
    python -m app.cli.main fix-runtime-states
    goto menu
)
if "%choice%"=="5" (
    echo Listing campaigns...
    python -m app.cli.main list-campaigns
    goto menu
)
if "%choice%"=="6" (
    echo Listing leads...
    python -m app.cli.main list-leads
    goto menu
)
if "%choice%"=="7" (
    echo Goodbye!
    exit /b 0
)

echo Invalid choice. Please try again.
goto menu
