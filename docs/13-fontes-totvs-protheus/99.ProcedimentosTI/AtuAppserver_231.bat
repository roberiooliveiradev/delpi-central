@echo off
rem dirOri = Fixo
rem folderDest => Nome da Pasta do Appserver
rem fileAppserver => Nome do arquivo appserver exe e ini
rem dirDest => Pasta a ser copiada a nova estrutura
rem dirINI => Pasta original para copiar o ini
set dirOri=C:\Users\Gabriel\OneDrive\TSCActvs\Delpi\2310\Appserver
set folderDest=01.01Appserver
set fileAppserver=Appserver0101
set dirDest=\\192.168.1.231\d$\Protheus\AppNew2\
set dirINI=\\192.168.1.231\d$\Protheus\App\

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



set folderDest=01.02Appserver
set fileAppserver=Appserver0102
set dirDest=\\192.168.1.231\d$\Protheus\AppNew2\
set dirINI=\\192.168.1.231\d$\Protheus\App\

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


set folderDest=01.03Appserver
set fileAppserver=Appserver0103
set dirDest=\\192.168.1.231\d$\Protheus\AppNew2\
set dirINI=\\192.168.1.231\d$\Protheus\App\

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


set folderDest=01.04Appserver
set fileAppserver=Appserver0104
set dirDest=\\192.168.1.231\d$\Protheus\AppNew2\
set dirINI=\\192.168.1.231\d$\Protheus\App\

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

set folderDest=01.05Appserver
set fileAppserver=Appserver0105
set dirDest=\\192.168.1.231\d$\Protheus\AppNew2\
set dirINI=\\192.168.1.231\d$\Protheus\App\

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