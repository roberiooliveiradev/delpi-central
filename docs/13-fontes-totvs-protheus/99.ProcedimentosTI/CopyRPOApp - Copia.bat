@echo off
set dirOri="\\192.168.1.232\d$\Protheus\Apo\CompApp"
set dirDest=\\192.168.1.232\d$\Protheus\Apo\CustomApp
set nmFolder=\20250519_02
set nmFileRPO="custom.rpo"
set dirFull="%dirDest%%nmFolder%"
robocopy %dirOri% %dirFull% %nmFileRPO% /mt:10 /w:0 /r:10 /e /zb
echo abre diretorio
start "" %dirFull%
pause
set PATH=%PATH%;C:\Program Files (x86)\Notepad++ 
rem start notepad++ "\\192.168.1.8\f$\SISTEMAS\Totvs\Totvs12\bin\03.01Appserver\Appserver0301.ini"

start notepad++ "\\192.168.1.231\d$\Protheus\App\01.01Appserver\appserver0101.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.02Appserver\appserver0102.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.03Appserver\appserver0103.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.04Appserver\appserver0104.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.05Appserver\appserver0105.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.06Appserver\appserver0106.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.07Appserver\appserver0107.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.08Appserver\appserver0108.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.09Appserver\appserver0109.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.10Appserver\appserver0110.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\App\01.11Appserver\appserver0111.ini"
pause 