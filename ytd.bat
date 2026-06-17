@echo off
setlocal
set "YTD_PROJECT_DIR=%~dp0"
set "YTD_DEPS_DIR=%~dp0.ytd_env\site-packages"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%YTD_DEPS_DIR%;%PYTHONPATH%"
python "%~dp0ytd.py" %*
set "YTD_EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %YTD_EXIT_CODE%
