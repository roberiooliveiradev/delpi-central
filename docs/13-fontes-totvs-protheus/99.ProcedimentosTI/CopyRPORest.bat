@echo off
set dirOri="\\192.168.1.232\d$\Protheus\Apo\CompRest"
set dirDest=\\192.168.1.232\d$\Protheus\Apo\CustomRest
set nmFolder=\20251216_01
set nmFileRPO="custom.rpo"
set dirFull="%dirDest%%nmFolder%"
robocopy %dirOri% %dirFull% %nmFileRPO% /mt:10 /w:0 /r:10 /e /zb
echo abre diretorio
start "" %dirFull%
pause
set PATH=%PATH%;C:\Program Files (x86)\Notepad++ 
start notepad++ "\\192.168.1.231\d$\Protheus\Rest\02.01Appserver\appserver0201.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\Rest\02.02Appserver\appserver0202.ini"
pause
start notepad++ "\\192.168.1.231\d$\Protheus\Rest\02.03Appserver\appserver0203.ini"
pause

