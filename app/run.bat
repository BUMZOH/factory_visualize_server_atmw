@echo off

REM run.batのフォルダへ移動
cd /d %~dp0

REM 親フォルダの .venv を使用
set PYTHON=..\.venv\Scripts\python.exe

"%PYTHON%" main.py

pause