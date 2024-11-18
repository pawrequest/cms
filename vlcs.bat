@echo off
setlocal enabledelayedexpansion

:: Parameters
set user=%1
set pass=%2
set channels=%3
set prog_exe="C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"

:: Kill existing VLC processes
taskkill /IM vlc.exe /F >nul 2>&1

:: Start VLC for each channel
for %%c in (%channels%) do (
    set "chan=%%c"
    set "url=rtsp://192.168.1.10:554/user=%user%&password=%pass%&channel=!chan!&stream=0.sdp?real_stream--rtp-caching=100"
    echo Launching channel !chan!
    start "" %prog_exe% !url!
)

endlocal
exit /b
