@echo off
rem dirOri = Fixo
rem folderDest => Nome da Pasta do Appserver
rem fileAppserver => Nome do arquivo appserver exe e ini
rem dirDest => Pasta a ser copiada a nova estrutura
rem dirINI => Pasta original para copiar o ini
rem Schd 03.01Appserver
rem  WS 04.01Appserver
rem Rest 02.01Appserver - 3 

set dirOri=C:\Users\Gabriel\OneDrive\TSCActvs\Delpi\2310\Appserver


set folderDest=03.01Appserver
set fileAppserver=Appserver0301
set dirDest=\\192.168.1.231\d$\Protheus\SchdNew2\
set dirINI=\\192.168.1.231\d$\Protheus\Schd\



echo %dirDest%%folderDest%
echo  "%dirINI%%folderDest%.exe"
echo "%dirDest%%folderDest%" 
pause
echo INICIANDO  %folderDest%
rem cria novo diretorio
md  %dirDest%%folderDest%
rem abre pasta
start "" %dirDest%%folderDest%
rem copia
robocopy "%dirOri%"  "%dirDest%%folderDest%"  /mt:50 /w:0 /r:10 /e /np /zb /eta
pause
ren %dirDest%%folderDest%\appserver.exe %fileAppserver%.exe
pause
robocopy "%dirINI%%folderDest%"  "%dirDest%%folderDest%" "%fileAppserver%.ini"  /mt:50 /w:0 /r:10 /e /zb
pause
rmdir "%dirDest%%folderDest%\webapp" /s /q
rmdir "%dirDest%%folderDest%\appmon" /s /q

set folderDest=04.01Appserver
set fileAppserver=Appserver0401
set dirDest=\\192.168.1.231\d$\Protheus\WSNew2\
set dirINI=\\192.168.1.231\d$\Protheus\WS\

echo %dirDest%%folderDest%
echo  "%dirINI%%folderDest%.exe"
echo "%dirDest%%folderDest%" 
pause
echo INICIANDO  %folderDest%
rem cria novo diretorio
md  %dirDest%%folderDest%
rem abre pasta
start "" %dirDest%%folderDest%
rem copia
robocopy "%dirOri%"  "%dirDest%%folderDest%"  /mt:50 /w:0 /r:10 /e /np /zb /eta
pause
ren %dirDest%%folderDest%\appserver.exe %fileAppserver%.exe
pause
robocopy "%dirINI%%folderDest%"  "%dirDest%%folderDest%" "%fileAppserver%.ini"  /mt:50 /w:0 /r:10 /e /zb
pause
rmdir "%dirDest%%folderDest%\webapp" /s /q
rmdir "%dirDest%%folderDest%\appmon" /s /q



set folderDest=04.02Appserver
set fileAppserver=Appserver0402


echo %dirDest%%folderDest%
echo  "%dirINI%%folderDest%.exe"
echo "%dirDest%%folderDest%" 
pause
echo INICIANDO  %folderDest%
rem cria novo diretorio
md  %dirDest%%folderDest%
rem abre pasta
start "" %dirDest%%folderDest%
rem copia
robocopy "%dirOri%"  "%dirDest%%folderDest%"  /mt:50 /w:0 /r:10 /e /np /zb /eta
pause
ren %dirDest%%folderDest%\appserver.exe %fileAppserver%.exe
pause
robocopy "%dirINI%%folderDest%"  "%dirDest%%folderDest%" "%fileAppserver%.ini"  /mt:50 /w:0 /r:10 /e /zb
pause
rmdir "%dirDest%%folderDest%\webapp" /s /q
rmdir "%dirDest%%folderDest%\appmon" /s /q


set folderDest=04.03Appserver
set fileAppserver=Appserver0403


echo %dirDest%%folderDest%
echo  "%dirINI%%folderDest%.exe"
echo "%dirDest%%folderDest%" 
pause
echo INICIANDO  %folderDest%
rem cria novo diretorio
md  %dirDest%%folderDest%
rem abre pasta
start "" %dirDest%%folderDest%
rem copia
robocopy "%dirOri%"  "%dirDest%%folderDest%"  /mt:50 /w:0 /r:10 /e /np /zb /eta
pause
ren %dirDest%%folderDest%\appserver.exe %fileAppserver%.exe
pause
robocopy "%dirINI%%folderDest%"  "%dirDest%%folderDest%" "%fileAppserver%.ini"  /mt:50 /w:0 /r:10 /e /zb
pause
rmdir "%dirDest%%folderDest%\webapp" /s /q
rmdir "%dirDest%%folderDest%\appmon" /s /q


set folderDest=02.01Appserver
set fileAppserver=Appserver0201
set dirDest=\\192.168.1.231\d$\Protheus\RestNew2\
set dirINI=\\192.168.1.231\d$\Protheus\Rest\

echo %dirDest%%folderDest%
echo  "%dirINI%%folderDest%.exe"
echo "%dirDest%%folderDest%" 
pause
echo INICIANDO  %folderDest%
rem cria novo diretorio
md  %dirDest%%folderDest%
rem abre pasta
start "" %dirDest%%folderDest%
rem copia
robocopy "%dirOri%"  "%dirDest%%folderDest%"  /mt:50 /w:0 /r:10 /e /np /zb /eta
pause
ren %dirDest%%folderDest%\appserver.exe %fileAppserver%.exe
pause
robocopy "%dirINI%%folderDest%"  "%dirDest%%folderDest%" "%fileAppserver%.ini"  /mt:50 /w:0 /r:10 /e /zb
pause
rmdir "%dirDest%%folderDest%\webapp" /s /q
rmdir "%dirDest%%folderDest%\appmon" /s /q



set folderDest=02.02Appserver
set fileAppserver=Appserver0202

echo %dirDest%%folderDest%
echo  "%dirINI%%folderDest%.exe"
echo "%dirDest%%folderDest%" 
pause
echo INICIANDO  %folderDest%
rem cria novo diretorio
md  %dirDest%%folderDest%
rem abre pasta
start "" %dirDest%%folderDest%
rem copia
robocopy "%dirOri%"  "%dirDest%%folderDest%"  /mt:50 /w:0 /r:10 /e /np /zb /eta
pause
ren %dirDest%%folderDest%\appserver.exe %fileAppserver%.exe
pause
robocopy "%dirINI%%folderDest%"  "%dirDest%%folderDest%" "%fileAppserver%.ini"  /mt:50 /w:0 /r:10 /e /zb
pause
rmdir "%dirDest%%folderDest%\webapp" /s /q
rmdir "%dirDest%%folderDest%\appmon" /s /q



set folderDest=02.03Appserver
set fileAppserver=Appserver0203

echo %dirDest%%folderDest%
echo  "%dirINI%%folderDest%.exe"
echo "%dirDest%%folderDest%" 
pause
echo INICIANDO  %folderDest%
rem cria novo diretorio
md  %dirDest%%folderDest%
rem abre pasta
start "" %dirDest%%folderDest%
rem copia
robocopy "%dirOri%"  "%dirDest%%folderDest%"  /mt:50 /w:0 /r:10 /e /np /zb /eta
pause
ren %dirDest%%folderDest%\appserver.exe %fileAppserver%.exe
pause
robocopy "%dirINI%%folderDest%"  "%dirDest%%folderDest%" "%fileAppserver%.ini"  /mt:50 /w:0 /r:10 /e /zb
pause
rmdir "%dirDest%%folderDest%\webapp" /s /q
rmdir "%dirDest%%folderDest%\appmon" /s /q
