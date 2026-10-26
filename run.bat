@echo off
rem 音频评分工具 一键启动脚本 (Windows)
rem 首次运行会自动创建虚拟环境并安装依赖，之后直接启动。
setlocal

cd /d "%~dp0"

set VENV_DIR=.venv
set PYTHON=python

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo ==^> 首次运行：创建虚拟环境 %VENV_DIR% ...
    %PYTHON% -m venv "%VENV_DIR%"
    echo ==^> 安装依赖 ...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
)

echo ==^> 启动音频评分工具 ...
"%VENV_DIR%\Scripts\python.exe" main.py

endlocal
