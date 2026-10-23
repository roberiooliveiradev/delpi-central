Set DirOri="C:\Users\Gabriel\OneDrive\Protheus\Fontes\Delpi2025\11370-DELPI-PROTHEUS\99.ProcedimentosTI"
Set DirDest="\\192.168.1.232\d$\Protheus\Bin\00.02Appserver_Broker_Webapp"
Set Arquivo=".TOTVS_BROKER_COMMAND"
robocopy %dirOri% %DirDest% %Arquivo% /mt:10 /w:0 /r:10 /e /zb
rem Set DirDest="\\192.168.1.232\d$\Protheus\Bin\00.03Appserver_Broker_Rest"
rem robocopy %dirOri% %DirDest% %Arquivo% /mt:10 /w:0 /r:10 /e /zb
rem Set DirDest="\\192.168.1.232\d$\Protheus\Bin\00.04Appserver_Broker_WS"
rem robocopy %dirOri% %DirDest% %Arquivo% /mt:10 /w:0 /r:10 /e /zb
pause .