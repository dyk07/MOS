#!/usr/bin/env bash
# 音频评分工具 一键启动脚本 (Linux / macOS)
# 首次运行会自动创建虚拟环境并安装依赖，之后直接启动。
set -e

cd "$(dirname "$0")"

VENV_DIR=".venv"
PYTHON="${PYTHON:-python3}"

if [ ! -d "$VENV_DIR" ]; then
    echo "==> 首次运行：创建虚拟环境 $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
    echo "==> 安装依赖 ..."
    "$VENV_DIR/bin/python" -m pip install --upgrade pip
    "$VENV_DIR/bin/python" -m pip install -r requirements.txt
fi

echo "==> 启动音频评分工具 ..."
"$VENV_DIR/bin/python" main.py
