@echo off
set dirOri="\\192.168.1.232\d$\Protheus\Apo\CompApp"
set dirDest=\\192.168.1.232\d$\Protheus\Apo\CustomApp
set nmFolder=\20260316_02
set nmFileRPO="custom.rpo"
set dirFull="%dirDest%%nmFolder%"
rem echo %dirOri% %dirFull% %nmFileRPO% 
robocopy %dirOri% %dirFull% %nmFileRPO% /mt:10 /w:0 /r:10 /e
echo abre diretorio
start "" %dirFull%
pause
set PATH=%PATH%;C:\Program Files (x86)\Notepad++ 

start notepad "\\192.168.1.231\d$\Protheus\App\01.01Appserver\appserver0101.ini"
pause
start notepad "\\192.168.1.231\d$\Protheus\App\01.11Appserver\appserver0111.ini"
pause 