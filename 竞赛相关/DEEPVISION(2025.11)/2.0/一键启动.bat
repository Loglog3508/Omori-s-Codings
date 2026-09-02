@echo off
chcp 65001 >nul
echo 正在启动 DeepVision 本地服务器...

REM 尝试直接使用 python 命令
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python start_server.py
    goto end
)

REM 尝试使用检测到的 E 盘 Python 路径
if exist "E:\python\python.exe" (
    "E:\python\python.exe" start_server.py
    goto end
)

REM 如果都失败了
echo 错误：未找到 Python 环境。
echo 请确保已安装 Python 并将其添加到系统环境变量 PATH 中。
echo 或者修改本脚本中的 Python 路径。

:end
pause