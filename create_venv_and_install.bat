@echo off
setlocal enabledelayedexpansion

rem Script directory (where this .bat lives)
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

rem Find a python executable
where python >nul 2>&1
if %ERRORLEVEL%==0 (
	set "PY_CMD=python"
) else (
	where py >nul 2>&1
	if %ERRORLEVEL%==0 (
		set "PY_CMD=py -3"
	) else (
		echo Python 3 was not found in PATH. Please install Python and try again.
		exit /b 1
	)
)

rem Prefer .venv, fall back to venv
if exist ".venv\Scripts\activate.bat" (
	set "VENV_DIR=.venv"
) else if exist "venv\Scripts\activate.bat" (
	set "VENV_DIR=venv"
) else (
	set "VENV_DIR=.venv"
)

rem Create venv if it doesn't exist
if not exist "%VENV_DIR%\Scripts\activate.bat" (
	echo Creating virtual environment in "%VENV_DIR%"...
	%PY_CMD% -m venv "%VENV_DIR%" || (
		echo Failed to create virtual environment using %PY_CMD%.
		exit /b 1
	)
)

rem Activate the venv (this runs under cmd semantics)
call "%VENV_DIR%\Scripts\activate.bat"

rem If requirements.txt exists, install or upgrade packages as needed
if exist "%SCRIPT_DIR%requirements.txt" (
	echo Installing from requirements.txt...
	python -m pip install --upgrade pip
	python -m pip install -r "%SCRIPT_DIR%requirements.txt"
) else (
	echo No requirements.txt found in "%SCRIPT_DIR%". Skipping pip install.
)

echo Virtual environment is ready. Launching PowerShell with venv activated...
powershell.exe -NoExit -Command "& '%VENV_DIR%\Scripts\Activate.ps1'; Write-Host 'Virtual environment activated. You can now run Python commands. Type exit to close this shell.'"

endlocal

