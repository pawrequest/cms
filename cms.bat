@echo off
setlocal enabledelayedexpansion

NET SESSION >nul 2>nul
if %errorlevel% neq 0 (
    echo This script requires Administrator privileges.
    echo Restarting with Administrator rights...
    powershell -Command "Start-Process cmd.exe -ArgumentList '/c, %~s0' -Verb RunAs"
    exit
)

powershell -Command "Start-Process cmd.exe -ArgumentList '/c, E:\DOCS\Desktop\cms\eth.bat 192.168.1.127 192.168.1.254' -Verb RunAs -Wait"


set user=%RTSP_USER%
set pass=%RTSP_PASS%
set prog_exe="C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"

if "%~1"=="" (
    echo No channels provided. Defaulting to doors
    set channels=2 6
) else (
    set channels=%*
)

for %%c in (%channels%) do (
    set "chan=%%c"
    set "url=rtsp://192.168.1.10:554/user=%user%&password=%pass%&channel=!chan!&stream=0.sdp?real_stream--rtp-caching=100"
    echo Launching channel !chan!
    start "" %prog_exe% !url!
)


echo Press 'r' to refresh VLC windows, or any other key to reset eth and close...
set /p userInput=:

if /i "%userInput%"=="r" (
    taskkill /IM vlc.exe /F >nul 2>&1
    echo VLC windows refreshed. Restarting VLC...

    for %%c in (%channels%) do (
        set "chan=%%c"
        set "url=rtsp://192.168.1.10:554/user=%user%&password=%pass%&channel=!chan!&stream=0.sdp?real_stream--rtp-caching=100"
        echo Launching channel !chan!
        start "" %prog_exe% !url!
    )

) else (
    echo Closing VLC and resetting Ethernet...
    taskkill /IM vlc.exe /F >nul 2>&1
    powershell -Command "Start-Process cmd.exe -ArgumentList '/c, E:\DOCS\Desktop\cms\eth.bat 192.168.0.27 192.168.0.254' -Verb RunAs -Wait"
)
