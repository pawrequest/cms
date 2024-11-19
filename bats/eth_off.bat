powershell -Command "Start-Process cmd.exe -ArgumentList '/c, %~dp0\eth.bat 192.168.1.127 192.168.1.254' -Verb RunAs -Wait"
