#Include "TOTVS.CH"

/*/{Protheus.doc} DLP04P01
@description Rotina de atualização de campo BZ_ESTSEG.
@author Johnni Moraes
@since 07/10/2025
@version 1.0
@return Nil
/*/
User Function DLP04P01()
	Local aArea := FWGetArea()

	Processa({|| ProcessaArquivo()}, "Processando arquivo CSV...")

	FWRestArea(aArea)
Return

/*/{Protheus.doc} ProcessaArquivo
@description Orquestra a leitura, processamento e log da atualização do campo BZ_ESTSEG.
@author Johnni Moraes
@since 07/10/2025
@version 1.0
/*/
Static Function ProcessaArquivo()
	Local aDadosCSV         := {}
	Local aRetCSV           := {}
	Local aLogSucesso       := {}
	Local aLogNaoEncontrado := {}
	Local aLogErro          := {}
	Local nI                := 0
	Local cLogFinal         := ""
	Local cMsgFinal         := ""

	aRetCSV := LerArquivoCSV()
	aDadosCSV := aRetCSV[1]

	If Empty(aDadosCSV)
		If !Empty(aRetCSV[2])
			cLogFinal := "Erros na leitura do arquivo CSV:" + CRLF
			For nI := 1 To Len(aRetCSV[2])
				cLogFinal += aRetCSV[2][nI] + CRLF
			Next
			AutoGrLog(cLogFinal)
			MostraErro()
		Else
			FWAlertInfo("Nenhum dado válido para processar no arquivo selecionado.", "Aviso")
		Endif
		Return
	Endif

	ProcRegua(Len(aDadosCSV))
	For nI := 1 To Len(aDadosCSV)
		IncProc("Processando linha " + CValToChar(nI) + " de " + CValToChar(Len(aDadosCSV)))
		ProcessaLinhaCSV(aDadosCSV[nI], nI + 1, @aLogSucesso, @aLogNaoEncontrado, @aLogErro)
	Next

	cLogFinal := MontaLogFinal(aLogSucesso, aLogNaoEncontrado, aLogErro)
	If !Empty(cLogFinal)
		ShowLog(cLogFinal)
	Endif

	cMsgFinal := "Processamento finalizado!" + CRLF + CRLF
	cMsgFinal += "Produtos atualizados: " + CValToChar(Len(aLogSucesso)) + CRLF
	cMsgFinal += "Produtos não encontrados: " + CValToChar(Len(aLogNaoEncontrado)) + CRLF
	cMsgFinal += "Linhas com erro: " + CValToChar(Len(aLogErro)) + CRLF + CRLF
	cMsgFinal += "Consulte o log para mais detalhes."

	FWAlertInfo(cMsgFinal, "Fim do Processamento")
Return

/*/{Protheus.doc} ProcessaLinhaCSV
@description Valida, busca e atualiza o título de uma linha do CSV.
@author Johnni Moraes
@since 07/10/2025
@version 1.0
/*/
Static Function ProcessaLinhaCSV(aLinha, nLinhaNoArquivo, aLogSucesso, aLogNaoEncontrado, aLogErro)
	Local cProdCod  := ""
	Local cPecaHr    := ""
	Local cQueryInfo  := ""
	Local nStatus    := 0

	// Mapeamento de colunas do CSV
	// 1: BZ_COD | 3: BZ_ESTSEG
	If Len(aLinha) < 3
		AAdd(aLogErro, {"Linha: " + CValToChar(nLinhaNoArquivo), "Estrutura de colunas inválida."})
		Return
	Endif

	cProdCod := AllTrim(aLinha[1])
	cPecaHr  := AllTrim(aLinha[3])
	cQueryInfo := "Produto: " + cProdCod + " | BZ_ESTSEG: " + cPecaHr

	If Empty(cProdCod) .Or. Empty(cPecaHr)
		AAdd(aLogErro, {cQueryInfo, "Dados obrigatórios ausentes na linha " + CValToChar(nLinhaNoArquivo) + "."})
		Return
	Endif

	nStatus := AtuBZEstseg(cProdCod, cPecaHr)
	If nStatus == 0
		AAdd(aLogSucesso, {cQueryInfo, "Campo BZ_ESTSEG atualizado com sucesso."})
	ElseIf nStatus == 1
		AAdd(aLogNaoEncontrado, {cQueryInfo, "Produto não localizado na tabela SBZ."})
	ElseIf nStatus == 2
		AAdd(aLogErro, {cQueryInfo, "Falha ao bloquear (RECLOCK) o registro para atualização."})
	Endif
Return

/*/{Protheus.doc} AtualizaPecaHrSBZ
@description Atualiza o campo BZ_ESTSEG do produto informado na tabela SBZ.
@author Johnni Moraes
@since 10/10/2025
@version 1.1
@param cProdCod, character, Código do produto
@param cPecaHr, character, Valor de peças por hora
@return numeric, Status da operação (0=sucesso, 1=não encontrado, 2=falha de bloqueio)
/*/
Static Function AtuBZEstseg(cProdCod, cPecaHr)
	Local nStatus := 1 // 1=não encontrado, 2=falha de bloqueio, 0=sucesso

	DbSelectArea("SBZ")
	SBZ->(DbSetOrder(1)) // BZ_FILIAL+BZ_COD
	If SBZ->(DbSeek(xFilial("SBZ") + AvKey(cProdCod, "BZ_COD")))
		If RecLock("SBZ", .F.)
			SBZ->BZ_ESTSEG := NoRound(Val(StrTran(StrTran(cPecaHr, ".", ""), ",", ".")), 2)
			SBZ->(MsUnlock())
			nStatus := 0 // sucesso
		Else
			nStatus := 2 // falha de bloqueio
		Endif
	Endif
Return nStatus

/*/{Protheus.doc} LerArquivoCSV
@description Abre um diálogo para seleção de arquivo CSV e lê seu conteúdo.
@author Johnni Moraes
@since 07/10/2025
@version 1.0
/*/
Static Function LerArquivoCSV()
	Local cArquivo  As Character
	Local oFile     As Object
	Local nLin     := 0 As Numeric
	Local cLinAtu   As Character
	Local aLinhas   As Array
	Local aDados    := {} As Array
	Local aErros    := {} As Array

	cArquivo := FileDlg()

	If Empty(cArquivo) .Or. !File(cArquivo)
		Return {aDados, aErros}
	Endif

	oFile := FWFileReader():New(cArquivo)
	If oFile:Open()
		aLinhas := oFile:GetAllLines()
		For nLin := 1 To Len(aLinhas)
			cLinAtu := aLinhas[nLin]
			If nLin > 1 .And. !Empty(cLinAtu) // Pula cabeçalho
				Aadd(aDados, StrTokArr2(cLinAtu, ";"))
			Endif
		Next
		oFile:Close()
	Else
		FWAlertError("Não foi possível abrir o arquivo: " + cArquivo, "Erro de Leitura")
		AAdd(aErros, "Falha ao abrir o arquivo: " + cArquivo)
	Endif
	FreeObj(oFile)

Return {aDados, aErros}

/*/{Protheus.doc} MontaLogFinal
@description Concatena os resultados do processamento em uma string de log.
@author Johnni Moraes
@since 07/10/2025
@version 1.0
/*/
Static Function MontaLogFinal(aLogSucesso, aLogNaoEncontrado, aLogErro)
	Local cLog   := "" As Character
	Local nI     As Numeric

	If !Empty(aLogSucesso)
		cLog += Replicate("=", 50) + CRLF
		cLog += "ATUALIZADOS COM SUCESSO (" + CValToChar(Len(aLogSucesso)) + ")" + CRLF
		cLog += Replicate("=", 50) + CRLF
		For nI := 1 To Len(aLogSucesso)
			cLog += aLogSucesso[nI][1] + " | " + aLogSucesso[nI][2] + CRLF
		Next
	Endif

	If !Empty(aLogNaoEncontrado)
		cLog += CRLF + Replicate("=", 50) + CRLF
		cLog += "NÃO ENCONTRADOS (" + CValToChar(Len(aLogNaoEncontrado)) + ")" + CRLF
		cLog += Replicate("=", 50) + CRLF
		For nI := 1 To Len(aLogNaoEncontrado)
			cLog += aLogNaoEncontrado[nI][1] + " | " + aLogNaoEncontrado[nI][2] + CRLF
		Next
	Endif

	If !Empty(aLogErro)
		cLog += CRLF + Replicate("=", 50) + CRLF
		cLog += "ERROS DE PROCESSAMENTO (" + CValToChar(Len(aLogErro)) + ")" + CRLF
		cLog += Replicate("=", 50) + CRLF
		For nI := 1 To Len(aLogErro)
			cLog += aLogErro[nI][1] + " | " + aLogErro[nI][2] + CRLF
		Next
	Endif
Return cLog

/*/{Protheus.doc} FileDlg
@description Exibe a caixa de diálogo para seleção de arquivo.
@author Johnni Moraes
@since 07/10/2025
@version 1.0
/*/
Static Function FileDlg() As Character
	Local cFileToRead := cGetFile("Arquivos CSV (*.csv)|*.csv", "Selecione o arquivo para importação", 0, "", .F., GETF_LOCALHARD + GETF_NETWORKDRIVE)
Return cFileToRead
