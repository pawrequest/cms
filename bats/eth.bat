@echo off
setlocal

:: Check for Administrator privileges
NET SESSION >nul 2>nul
if %errorlevel% neq 0 (
    echo This script requires Administrator privileges.
    echo Restarting with Administrator rights...
    powershell -Command "Start-Process cmd.exe -ArgumentList '/c, %~s0' -Verb RunAs"
    exit
)

set IP_ADDRESS=%~1
set GATEWAY=%~2

set INTERFACE_NAME="Ethernet"
set DNS1=8.8.8.8
set DNS2=8.8.4.4
set SUBNET_MASK=255.255.255.0

netsh interface ip set address name=%INTERFACE_NAME% static %IP_ADDRESS% %SUBNET_MASK% %GATEWAY%
netsh interface ip set dns name=%INTERFACE_NAME% static %DNS1%
netsh interface ip add dns name=%INTERFACE_NAME% %DNS2% index=2

endlocal
