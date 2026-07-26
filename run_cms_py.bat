set THIS_DIR=%~dp0
set CONF=%1
rem if no conf passed we use default
if "%CONF%"=="" set CONF=./default_conf.toml

uv tool run %THIS_DIR% --gui -C %CONF%