@echo off
rem Social Idea Lab by Tarfandhaye.ai - start script for Windows.
rem Installs uv (if missing) and a uv-managed Python 3.12, then runs the skill with it.
rem   start.cmd              opens the dashboard
rem   start.cmd <command>    runs any command (start.cmd help)
setlocal
set "ILAB_DIR=%~dp0"
set "ILAB_PY=3.12"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

rem 1. uv: on PATH, or where its installer puts it (checked once: each lookup costs ~100 ms)
set "UV=uv"
for %%I in (uv.exe) do if not "%%~$PATH:I"=="" goto :have_uv
set "UV=%USERPROFILE%\.local\bin\uv.exe"
if exist "%UV%" goto :have_uv
set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
if exist "%UV%" goto :have_uv
echo [Social Idea Lab] uv is not installed. Installing it from astral.sh ^(one time^)... 1>&2
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" 1>&2
set "UV=%USERPROFILE%\.local\bin\uv.exe"
if exist "%UV%" goto :have_uv
echo [Social Idea Lab] uv could not be installed. Check the internet, or install it from https://docs.astral.sh/uv/ 1>&2
exit /b 1
:have_uv

rem 2. Python, installed and managed by uv (one time, about 30 MB)
set "PY="
for /f "delims=" %%P in ('""%UV%" python find --managed-python %ILAB_PY% 2>nul"') do set "PY=%%P"
if defined PY goto :have_py
echo [Social Idea Lab] Installing Python %ILAB_PY% with uv ^(one time^)... 1>&2
"%UV%" python install --no-bin --compile-bytecode %ILAB_PY% 1>&2
for /f "delims=" %%P in ('""%UV%" python find --managed-python %ILAB_PY% 2>nul"') do set "PY=%%P"
if defined PY goto :have_py
echo [Social Idea Lab] Python could not be installed. Check the internet and run this again. 1>&2
exit /b 1
:have_py

rem 3. run the skill with uv's Python (standard library only: no packages to install)
if "%~1"=="" (
  "%PY%" -I "%ILAB_DIR%scripts\run.py" dashboard --open
) else (
  "%PY%" -I "%ILAB_DIR%scripts\run.py" %*
)
exit /b %errorlevel%
