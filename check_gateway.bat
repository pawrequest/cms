set GATEWAY=%~1

echo Waiting for gateway connection...
:WAIT_FOR_NETWORK
ping -n 1 %GATEWAY% >nul
if %errorlevel% neq 0 (
    echo Gateway not yet connected. Retrying...
    timeout /t 1 >nul
    goto WAIT_FOR_NETWORK
)
echo Gateway connected...