#Include "protheus.ch"
#include 'totvs.ch'
#Include "TopConn.ch"
 
/*/EnviaEmail
	Faz envio do e-mail
	@author eduardo.dalitz
	@since 05/03/2025
/*/

user function DLP04W01()
	RpcSetEnv('01')

    LOCAL cPara:= SuperGetMV('MV_ZEMINVE', .F., 'eduardo.dalitz@totvs.com.br')
    Local cAssunto := "Emp: "+ cEmpAnt + " /  Fil:" + cFilAnt + "Analisar Inventario " + dtoc(dDataBase)
    Local cCorpo := "Prezado, "+CRLF
    cCorpo += "Foi realizado um inventario na Data " + dtoc(dDataBase) +", e necessita de analise." +CRLF
    cCorpo += "Lembrando que os produtos inventariados está bloqueada até seu processamento." +CRLF

    u_zEnvWF(cPara,cAssunto, cCorpo,  ,  , .T. ,,)
	RpcClearEnv()
return

User Function zEnvWF(cPara,cAssunto, cCorpo, aAnexos , lMostraLog , lUsaTLS , cCC, cLog)
	Local aArea        := GetArea()
	Local nAtual       := 0 																					
	Local lRet         := .T. 																					
	Local oMsg         := Nil 																					
	Local oSrv         := Nil 																					
	Local nRet         := 0 																					
	Local cFrom        := Alltrim(GetMV("MV_RELACNT")) 															
	Local cUser 	   := Alltrim(GetMV("MV_RELACNT"))															
	Local cPass        := Alltrim(GetMV("MV_RELPSW")) 															
	Local cSrvFull     := Alltrim(GetMV("MV_RELSERV")) 															
	Local cServer      := Iif(':' $ cSrvFull, SubStr(cSrvFull, 1, At(':', cSrvFull)-1), cSrvFull) 				
	Local nPort        := Iif(':' $ cSrvFull, Val(SubStr(cSrvFull, At(':', cSrvFull)+1, Len(cSrvFull))), 587) 	
	Local nTimeOut     := GetMV("MV_RELTIME") 																																						
	Default cPara      := ""
	Default cAssunto   := ""
	Default cCorpo     := ""
	Default cCC    	   := ""
	Default aAnexos    := {}
	Default lMostraLog := .F.
	Default lUsaTLS    := .F.
    Default cLog       := ""

	//Se tiver em branco o destinatário, o assunto ou o corpo do email
	If Empty(cPara) .Or. Empty(cAssunto) .Or. Empty(cCorpo)
		cLog += "001 - Destinatario, Assunto ou Corpo do e-Mail vazio(s)!" + CRLF
		lRet := .F.
	EndIf

	If lRet
		//Cria a nova mensagem
		oMsg := TMailMessage():New()
		oMsg:Clear()

		//Define os atributos da mensagem
		oMsg:cFrom    := cFrom
		oMsg:cTo      := cPara
		oMsg:cCC      := cCC
		oMsg:cSubject := cAssunto
		oMsg:cBody    := cCorpo

		//Percorre os anexos
		For nAtual := 1 To Len(aAnexos)
			//Se o arquivo existir
			If File(aAnexos[nAtual])
				//Anexa o arquivo na mensagem de e-Mail
				nRet := oMsg:AttachFile(aAnexos[nAtual])
				If nRet < 0
					cLog += "002 - Nao foi possivel anexar o arquivo '"+aAnexos[nAtual]+"'!" + CRLF
				EndIf
			Else
				cLog += "003 - Arquivo '"+aAnexos[nAtual]+"' nao encontrado!" + CRLF
			EndIf
		Next

		//Cria servidor para disparo do e-Mail
		oSrv := tMailManager():New()

		//Define se irá utilizar o TLS
		If lUsaTLS
			oSrv:SetUseTLS(.T.)
		EndIf

		//Inicializa conexão
		nRet := oSrv:Init("", cServer, cUser, cPass, 0, nPort)
		If nRet != 0
			cLog += "004 - Nao foi possivel inicializar o servidor SMTP: " + oSrv:GetErrorString(nRet) + CRLF
			lRet := .F.
		EndIf

		If lRet
			//Define o time out
			nRet := oSrv:SetSMTPTimeout(nTimeOut)
			If nRet != 0
				cLog += "005 - Nao foi possivel definir o TimeOut '"+cValToChar(nTimeOut)+"'" + CRLF
			EndIf

			//Conecta no servidor
			nRet := oSrv:SMTPConnect()
			If nRet <> 0
				cLog += "006 - Nao foi possivel conectar no servidor SMTP: " + oSrv:GetErrorString(nRet) + CRLF
				lRet := .F.
			EndIf

			If lRet
				//Realiza a autenticação do usuário e senha
				nRet := oSrv:SmtpAuth(cFrom, cPass)
				If nRet <> 0
					cLog += "007 - Nao foi possivel autenticar no servidor SMTP: " + oSrv:GetErrorString(nRet) + CRLF
					lRet := .F.
				EndIf

				If lRet
					//Envia a mensagem
					nRet := oMsg:Send(oSrv)
					If nRet <> 0
						cLog += "008 - Nao foi possivel enviar a mensagem: " + oSrv:GetErrorString(nRet) + CRLF
						lRet := .F.
					EndIf
				EndIf

				//Disconecta do servidor
				nRet := oSrv:SMTPDisconnect()
				If nRet <> 0
					cLog += "009 - Nao foi possivel disconectar do servidor SMTP: " + oSrv:GetErrorString(nRet) + CRLF
				EndIf
			EndIf
		EndIf

		FreeObj(oMsg)
		FreeObj(oSrv)
		oMsg := NIL
		oSrv := NIL
	EndIf

	//Se tiver log de avisos/erros
	If !Empty(cLog)
		cLog := "zEnvMail - "+dToC(Date())+ " " + Time() + CRLF + ;
			"Funcao - " + FunName() + CRLF + CRLF +;
			"Existem mensagens de aviso: "+ CRLF +;
			cLog
		ConOut(cLog)
		LogMsg("EnviaEmail", 0, 6, 1, '', '',cLog+" - "+FWTimeStamp(2))

		//Se for para mostrar o log visualmente e for processo com interface com o usuário, mostra uma mensagem na tela
		If lMostraLog .And. ! IsBlind()
			Aviso("Log", cLog, {"Ok"}, 2)
		EndIf

		lRet := .F.
	EndIf

	RestArea(aArea)

Return lRet
