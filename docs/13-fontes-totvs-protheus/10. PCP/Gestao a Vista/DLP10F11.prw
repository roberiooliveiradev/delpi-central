#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'

Class DelpiOpAtual FROM LongNameClass
	Static Method BuscaDados(oFiltros, cTipo, cSubTipo)
	Static Method BuscaDetalhes(oFiltros, nPagina)
	Static Method ValidaPropriedades(oFiltros)
EndClass



/*/{Protheus.doc} BuscaDados DLP10F11
Responsável por realizar a busca dos dados que serão exibidos no monitor
@type Class
@author
@since
@version
@param  oFiltros  , objeto Json, Contém as propriedades do monitor usadas para filtrar a query de busca
@param  cTipo     , caracter   , Tipo chart/info
@param  cSubTipo  , caracter   , Tipo de grafico pie/bar/column
@return cJsonDados, caracter   , Retorna um novo Json em formato texto, pronto para conversão e exibição no front
/*/
Method BuscaDados(oFiltros, cTipo, cSubTipo) Class DelpiOpAtual
	Local cAliasQry  := GetNextAlias()
	Local cAliasHZA  := GetNextAlias()
	Local cJsonDados := ""
	Local cQuery     := ""
	Local cTxtPrc    := ""
	Local cTxtSec    := ""
	Local cUnMedida  := ""
	// Local dFilterDat := PCPMonitorUtils():RetornaPeriodoFinal(oFiltros["05_TIPOPERIODO"],ddatabase,cValtoChar(oFiltros["06_PERIODO"]))
	Local nIndLinha  := 0
	Local nQuant     := 0
	Local nLotes     := 0
	Local nPos       := 0
	Local nSaldo     := 0
	Local nPosHeader := 0
	Local nZeros     := At(":", PesqPict("SH6", "H6_TEMPO")) - 1
	Local oJsonRet   := JsonObject():New()
	Local oStyle1  := JsonObject():New()
	Local oStyle2  := JsonObject():New()
	Local oStyle3  := JsonObject():New()
	Local oStylePrc  := JsonObject():New()
	Local oStyleHdr  := JsonObject():New()
	Local oStyleSec  := JsonObject():New()
	Local cEol := chr(10)
	//Propriedades que devem ser retornadas para monitores do tipo texto
	// oJsonRet["corTitulo"]          := "white" //Cor do título do monitor. Se não for informada, assumirá o valor #2590aa
	oJsonRet["alturaMinimaWidget"] := "350px" //Altura mínima do monitor. Se não for informada, assumirá o valor 350px
	oJsonRet["alturaMaximaWidget"] := "550px" //Altura máxima do monitor. Se não for informada, assumirá o valor 350px
	oJsonRet["linhas"]             := {}      //Array de objetos json com cada linha de informação do monitor
	oJsonRet["tags"]               := {}      //Array de objetos json com as tags que serão visualizadas no monitor
	oJsonRet["headers"]               := {}      //Array de objetos json com as tags que serão visualizadas no monitor
	//    oJsonRet["Titulo"]               := ""     //Array de objetos json com as tags que serão visualizadas no monitor


    /*pEGA OS fILTROS PARA ENVIAR A QUERY*/

	// oFiltros["01_B8_FILIAL"] := PadR(oFiltros["01_B8_FILIAL"], FWSizeFilial())
	cCodFil   :=  oFiltros["FILIAL"]
	cCodRecur := ""
	IF VALTYPE(oFiltros["RECURSO"]) =="A"
		if len(oFiltros["RECURSO"]) >0
			cCodRecur := oFiltros["RECURSO"][1]
		endif
	ELSE
		cCodRecur := oFiltros["RECURSO"]
	ENDIF
	cDtRef :=   oFiltros["FILTRODATA"]
	cDtPer :=   oFiltros["TIPOPERIODO"]
	if cDtPer == "D"
		cTPFil :=  "Dia Atual"
		dDtIni := dDataBase
		dDtFin := dDataBase
	elseif  cDtPer == "S"
		cTPFil := "Semana Atual"
		aRet := DlpWeek(dDataBase)
		dDtIni := aRet[2]
		dDtFin := aRet[3]
	elseif  cDtPer == "M"
		cTPFil := "Mes Atual"
		dDtIni := FirstDate(dDataBase)
		dDtFin := LastDate(dDataBase)
	ENDIF
	oStyleHdr["color"]       := "rgb(0, 56, 103)"
	oStyleHdr["font-weight"] := "bold"
	oStyleHdr["text-align"]  := "center"
	oStyleHdr["font-size"]   := "24px"
	cDescRec := ""
	dbSelectArea("SH1")
	SH1->( DbSetOrder(1) )
	if   SH1->(dbSeek( cCodFil+cCodRecur))
		cDescRec := ALLTRIM(SH1->H1_DESCRI)
	ENDIF

	cTxtHD:= alltrim(cCodRecur)+ ' - '+cDescRec
	oJsonRet["textoTitulo"]               := cTxtHD
	oStyleHdr["text"]               := cTxtHD
	PCPMonitorUtils():AdicionaHeaderDetalhe(oJsonRet["headers"],@nPosHeader,cTxtHD,"po-sm-12 po-pb-2",oStyleHdr:ToJson())


	//Query com os filtros para buscar as informações e apresentar no monitor
	cQuery := " SELECT  '00:'+SUBSTRING(H6_TEMPO,2,5) H6_TMPDLP,* " + cEol
	cQuery += " FROM dbo."+ RetSqlName("SH6") + " (NOLOCK) SH6 " + cEol
	cQuery += "     WHERE SH6.D_E_L_E_T_ = '' " + cEol
	//cQuery += "     and H6_DTAPONT >= '20240822' " + cEol
	cQuery += "     and H6_DTAPONT BETWEEN "+ VALTOSQL(dDtIni) + " AND "+ VALTOSQL(dDtFin) + cEol
	cQuery += "     and H6_FILIAL =" + valtosql(cCodFil ) + cEol
	cQuery += "     and H6_RECURSO = " + valtosql(cCodRecur ) + cEol

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasQry,.F.,.F.)
	nHRPrd    :="000:00"
	nHRImpPrd :="000:00"
	while  (cAliasQry)->(!Eof())


		nHrTmp :=    (cAliasQry)->H6_TEMPO //(N-Normal/C-Centesimal)
		if (cAliasQry)->H6_TIPO =="P"
			nHRPrd :=  SomaHoras((cAliasQry)->H6_TEMPO,nHRPrd)

		ELSEIF (cAliasQry)->H6_TIPO =="I"

			nHRImpPrd :=  SomaHoras(nHRImpPrd,(cAliasQry)->H6_TEMPO)
		ENDIF
		(cAliasQry)->(dbSkip())
	EndDo
	(cAliasQry)->(dbCloseArea())
	nPos := At(".",CVALTOCHAR(nHRPrd))
	nHRPrdF := STRZERO(val(substr(CVALTOCHAR(nHRPrd),1,nPos-1)),3)+":"+substr(CVALTOCHAR(nHRPrd),nPos+1,2)
	nPos := At(".",CVALTOCHAR(nHRImpPrd))
	nHRImpPF :=STRZERO(val(substr(CVALTOCHAR(nHRImpPrd),1,nPos-1)),3)+":"+substr(CVALTOCHAR(nHRImpPrd),nPos+1,2)
	//cHrDe := "N"
	//cHrPara := "C"
	//nHRPrd    :=  A680ConvHora( CVALTOCHAR(nHRPrd), cHrDe, cHrPara) //(N-Normal/C-Centesimal)
	//nHRImpPrd :=  A680ConvHora( CVALTOCHAR(nHRImpPrd) , cHrDe,cHrPara)

	//oStyle1 - Letra normal

	oStyle1["color"] := "black"
	cStylePO := "po-font-text-large po-text-center po-sm-6 po-pt-2"

	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"Horas Produtivas"  ,cStylePO,oStyle1:ToJson(),.f.)
	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"Horas Improdutivas",cStylePO,oStyle1:ToJson(),.f.)
	oStyle2["background-color"]:= "rgb(126,226,148)"
	oStyle2["border-radius"]:="3px"
	oStyle2["border-color"]:="rgb(126,226,148)"
	oStyle2["border"]:="5px"
	oStyle2["cursor"]:="pointer"
	oStyle3["background-color"]:= "%"
	oStyle3["border-radius"]:="3px"
	oStyle3["border-color"]:="rgb(241,143,136)"
	oStyle3["border"]:="5px"
	oStyle3["cursor"]:="pointer"

	cStylePO :=  "po-font-title po-text-center bold-text po-sm-6 po-pt-2 po-pb-2"
	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,substr(nHRPrdF,2,5),cStylePO,oStyle2:ToJson(),.T.,"SH6.H6_TIPO = 'P'")
	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,substr(nHRImpPF,2,5),cStylePO,oStyle3:ToJson(),.T.,"SH6.H6_TIPO = 'I'")

	cQuery := " SELECT TOP 1 ISNULL('Produto: ' + LTRIM(RTRIM(SC2.C2_PRODUTO)) + ' - ' + LTRIM(RTRIM(SB1.B1_DESC)) + '</br>' +  " + cEol
	cQuery += " 	'Operação: ' + LTRIM(RTRIM(HZA.HZA_OPERAC)) + ' - ' + LTRIM(RTRIM(Isnull(SG2.G2_DESCRI,'Recurso/Roteiro Alternativo'))) ,'')[TXT1] " + cEol
	cQuery += " 	,ISNULL( 'Produto: ' + LTRIM(RTRIM(SC2PAI.C2_PRODUTO)) + ' - ' + LTRIM(RTRIM(SB1PAI.B1_DESC)) + '</br>' +  " + cEol
	cQuery += " 	'Dt Entrega: ' + CONVERT(VARCHAR(12), CAST(SC2PAI.C2_DATPRF AS DATE), 103) ,'') [TXT2], " + cEol
	cQuery += " 	'Dt Entrega: ' + CONVERT(VARCHAR(12), CAST(SC2PAI.C2_DATPRF AS DATE), 103) [TXT3] " + cEol
	cQuery += " 	,  SC2PAI.C2_NUM + SC2PAI.C2_ITEM + SC2PAI.C2_SEQUEN  C2_OPAI " + cEol
	cQuery += " 	, HZA_OP " + cEol
	cQuery += " FROM dbo."+ RetSqlName("HZA") + "(NOLOCK) HZA " + cEol
	cQuery += " LEFT JOIN dbo."+ RetSqlName("SC2") + " SC2PAI " + cEol
	cQuery += " 	ON SC2PAI.D_E_L_E_T_ = '' " + cEol
	cQuery += " 		AND SC2PAI.C2_FILIAL = HZA_FILIAL " + cEol
	cQuery += " 		AND SC2PAI.C2_NUM+SC2PAI.C2_ITEM+SC2PAI.C2_SEQUEN  = SUBSTRING(HZA_OP, 1, 6) + '01001' " + cEol
	cQuery += " LEFT JOIN dbo."+ RetSqlName("SC2") + " SC2 " + cEol
	cQuery += " 	ON SC2.D_E_L_E_T_ = '' " + cEol
	cQuery += " 		AND SC2.C2_FILIAL = HZA_FILIAL " + cEol
	cQuery += " 		AND  SC2.C2_NUM+SC2.C2_ITEM+SC2.C2_SEQUEN = HZA_OP " + cEol
	cQuery += "LEFT JOIN SH6010 SH6 ON SH6.D_E_L_E_T_ = ''  " + cEol
	cQuery += "	AND SH6.H6_FILIAL = HZA_FILIAL  " + cEol
	cQuery += "	AND SH6.H6_OP = HZA_OP  " + cEol
	cQuery += "	AND SH6.H6_OPERAC = HZA_OPERAC  " + cEol
	cQuery += "LEFT JOIN SH8010 SH8 " + cEol
	cQuery += "ON SH8.D_E_L_E_T_ = '' " + cEol
	cQuery += "	AND SH8.H8_FILIAL = HZA_FILIAL " + cEol
	cQuery += "	AND SH8.H8_OP = HZA_OP " + cEol
	cQuery += "	AND SH8.H8_OPER = HZA_OPERAC " + cEol
	cQuery += "	AND SH8.H8_ROTEIRO = SC2.C2_ROTEIRO " + cEol
	cQuery += " LEFT JOIN dbo."+ RetSqlName("SG2") + " SG2 " + cEol
	cQuery += " 	ON SG2.D_E_L_E_T_ = '' " + cEol
	cQuery += " 		AND SG2.G2_FILIAL = HZA_FILIAL " + cEol
	cQuery += " 		AND G2_RECURSO = ISNULL(H8_RECURSO, H6_RECURSO)" + cEol
	cQuery += " 		AND G2_OPERAC = HZA_OPERAC " + cEol
	cQuery += " 		AND G2_CODIGO = H8_ROTEIRO " + cEol
	cQuery += " 		AND SC2.C2_PRODUTO = G2_PRODUTO " + cEol
	cQuery += " LEFT JOIN dbo."+ RetSqlName("SB1") + " SB1PAI " + cEol
	cQuery += " 	ON SB1PAI.D_E_L_E_T_ = '' " + cEol
	cQuery += " 		AND SB1PAI.B1_FILIAL = "+VALTOSQL(XFILIAL("SB1"))  + cEol
	cQuery += " 		AND SB1PAI.B1_COD = SC2PAI.C2_PRODUTO " + cEol
	cQuery += " LEFT JOIN dbo."+ RetSqlName("SB1") + " SB1 " + cEol
	cQuery += " 	ON SB1.D_E_L_E_T_ = '' " + cEol
	cQuery += " 		AND SB1.B1_FILIAL = '' " + cEol
	cQuery += " 		AND SB1.B1_COD = SC2.C2_PRODUTO " + cEol
	cQuery += " WHERE HZA.D_E_L_E_T_ = '' " + cEol
	cQuery += " 	and HZA_STATUS = '1' " + cEol
	cQuery += " 	and HZA_TPTRNS = '1' " + cEol
	cQuery += " 	AND HZA_FILIAL ="+VALTOSQL(cCodFil) + cEol
	cQuery += " 	AND ( ISNULL(H8_RECURSO, H6_RECURSO) ="+VALTOSQL(cCodRecur) + cEol
	cQuery += "     OR  H6_RECURSO = "+VALTOSQL(cCodRecur) + cEol
	cQuery += "     OR  G2_RECURSO = "+VALTOSQL(cCodRecur) + cEol
	cQuery += "     )AND HZA_DTINI >= "+VALTOSQL(dDtIni) + cEol
	cQuery += " ORDER BY HZA.R_E_C_N_O_ DESC " + cEol
	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasHZA,.F.,.F.)
	cTXT1   := " "
	cTXT2   := " "
	cTXT3   := " "
	cOPExec := " "
	cOPPai  := " "
	IF   (cAliasHZA)->(!Eof())
		cOPExec := (cAliasHZA)->HZA_OP
		cOPPai  := (cAliasHZA)->C2_OPAI
		cTXT1   := (cAliasHZA)->TXT1
		cTXT2   := (cAliasHZA)->TXT2
		cTXT3   := (cAliasHZA)->TXT3

	ENDIF
	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"Ord. Produção Em Execução: "+ cOPExec,;
		"po-font-text-large-bold po-text-left po-sm-12 po-pt-1 po-pl-0",oStyle1:ToJson(),.f.)
	IF cOPExec ==   cOPPai
		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTXT1+"</br>"+cTXT3,;
			"po-font-text-small po-text-left po-sm-12 po-pl-0",oStyle1:ToJson(),.f.)
		// IF cOPExec !=   cOPPai
	else
		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTXT1,;
			"po-font-text-small po-text-left po-sm-12 po-pl-0",oStyle1:ToJson(),.f.)
		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"Ordem Producao  Pai: "+cOPPai,;
			"po-font-text-large-bold po-text-left po-sm-12 po-pt-1 po-pl-0",oStyle1:ToJson(),.f.)
		//Adiciona tags ao monitor

		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTXT2,;
			"po-font-text-small po-text-left po-sm-12 po-pl-0",oStyle1:ToJson(),.f.)
	ENDIF
	nPos := 0
	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-calendar",dtoc(dDtIni) + " - " + dtoc(dDtFin))
	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-bar-manufacture",cCodRecur)

	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon po-icon-calendar-settings","Tipo Filtro : "+ cTPFil)
	cJsonDados :=  oJsonRet:toJson()


	FreeObj(oJsonRet)
Return cJsonDados


/*/{Protheus.doc} BuscaDetalhes
Responsável por realizar a busca dos dados que serão exibidos no detalhamento do monitor
@type Class
@author
@since
@version
@param  oFiltros  , objeto Json , Contém as propriedades do monitor usadas para filtrar a query de busca
@param  nPagina   , numerico    , Número da página desejada para busca
@return cJsonDados, caracter    , Retorna um novo Json em formato texto, pronto para conversão e exibição no front
/*/
Method BuscaDetalhes(oFiltros, nPagina) Class DelpiOpAtual
	Local cAliasQry  := GetNextAlias()
	Local cJsonDados := ""
	Local cQuery     := ""
	Local cOp        := ""
	Local cStatusOp  := ""
	Local dDataIni   := dDataBase
	Local dDataFin   := dDataBase
	Local lExpResult := .F.
	Local nIndice    := 0
	Local nPos       := 0
	Local nPosTag   := 0
	Local nStart     := 0
	Local oDados     := JsonObject():New()
	Local cEol := chr(10)
	Default nPagina    := 1
	Default nTamPagina := 10

	If nPagina == 0
		lExpResult := .T.
	EndIf

	cCodFil   :=  oFiltros["FILIAL"]
	cCodRecur :=  oFiltros["RECURSO"][1]
	cDtRef :=   oFiltros["FILTRODATA"]
	cDtPer :=   oFiltros["TIPOPERIODO"]
	if cDtPer == "D"
		cTPFil :=  "Dia Atual"
		dDtIni := dDataBase
		dDtFin := dDataBase
	elseif  cDtPer == "S"
		cTPFil := "Semana Atual"
		aRet := DlpWeek(dDataBase)
		dDtIni := aRet[2]
		dDtFin := aRet[3]
	elseif  cDtPer == "M"
		cTPFil := "Mes Atual"
		dDtIni := FirstDate(dDataBase)
		dDtFin := LastDate(dDataBase)
	ENDIF
	//VALTYPE(oFiltros["PARAMETROSDETALHE"])

	//Query com os filtros para buscar as informações e apresentar no monitor
	cQuery := " SELECT  '00:'+SUBSTRING(H6_TEMPO,2,5) H6_TMPDLP,R_E_C_N_O_ RECSH6,* " + cEol
	cQuery += " FROM dbo."+ RetSqlName("SH6") + " (NOLOCK) SH6 " + cEol
	cQuery += "     WHERE SH6.D_E_L_E_T_ = '' " + cEol
	cQuery += "     and H6_DTAPONT BETWEEN "+ VALTOSQL(dDtIni) + " AND "+ VALTOSQL(dDtFin) + cEol
	cQuery += "     and H6_FILIAL =" + valtosql(cCodFil ) + cEol
	cQuery += "     and H6_RECURSO = " + valtosql(cCodRecur ) + cEol

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasQry,.F.,.F.)

	oDados["items"]   := {}
	oDados["columns"] := montaColun(lExpResult)
	oDados["headers"] := {}
	oDados["tags"] := {}
	oDados["canExportCSV"] := .T.


	If nPagina > 1
		nStart := ( (nPagina-1) * nTamPagina )
		If nStart > 0
			(cAliasQry)->(DbSkip(nStart))
		EndIf
	EndIf

	nPos := 0
	While (cAliasQry)->(!Eof())
		aAdd(oDados["items"], JsonObject():New())
		nPos++
		oDados["items"][nPos]["H6_FILIAL"]    := (cAliasQry)->H6_FILIAL
		oDados["items"][nPos]["H6_OP"]        := (cAliasQry)->H6_OP
		oDados["items"][nPos]["H6_PRODUTO"]   := (cAliasQry)->H6_PRODUTO
		oDados["items"][nPos]["H6_OPERAC"]    := (cAliasQry)->H6_OPERAC
		oDados["items"][nPos]["H6_DATAINI"]   := PCPMonitorUtils():FormataData((cAliasQry)->H6_DATAINI, 5)
		oDados["items"][nPos]["H6_HORAINI"]   := (cAliasQry)->H6_HORAINI
		oDados["items"][nPos]["H6_DATAFIN"]   := PCPMonitorUtils():FormataData((cAliasQry)->H6_DATAFIN, 5)
		oDados["items"][nPos]["H6_HORAFIN"]   := (cAliasQry)->H6_HORAFIN
		oDados["items"][nPos]["H6_QTDPROD"]   := (cAliasQry)->H6_QTDPROD
		oDados["items"][nPos]["H6_QTDPERD"]   := (cAliasQry)->H6_QTDPERD
		oDados["items"][nPos]["H6_PT"]        := (cAliasQry)->H6_PT
		oDados["items"][nPos]["H6_DTAPONT"]   := PCPMonitorUtils():FormataData( (cAliasQry)->H6_DTAPONT, 5)
		oDados["items"][nPos]["H6_TEMPO"]     := (cAliasQry)->H6_TEMPO
		oDados["items"][nPos]["H6_DTPROD"]    := PCPMonitorUtils():FormataData( (cAliasQry)->H6_DTPROD, 5)
		oDados["items"][nPos]["STATUS"]       := (cAliasQry)->H6_TIPO
		oDados["items"][nPos]["RECSH6"]       := (cAliasQry)->RECSH6

		(cAliasQry)->(dbSkip())

		If !lExpResult .And. nPos >= nTamPagina
			Exit
		EndIf
	End
	oDados["hasNext"] := (cAliasQry)->(!Eof())
	(cAliasQry)->(dbCloseArea())
	cJsonDados := oDados:toJson()
	FreeObj(oDados)
Return cJsonDados

/*/{Protheus.doc} montaColun
Realiza a criação de objeto Json que define as colunas utilizadas na grid de detalhamento do monitor
@type Static Function
@author
@since
@version
@param  lExpResult, logico, Indica se trata todas as colunas como visible
@return aColumns, array objetos, Contém as definições das colunas da grid do monitor
/*/
Static Function montaColun(lExpResult)
	Local aColunas   := {}
	Local aLabels    := {}
	Local nIndice    := 0
	Local nIndLabels := 0

	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLabels,@nIndLabels,"P","rgb(126,226,148)","Produtiva","rgb(0,0,0)")
	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLabels,@nIndLabels,"I","rgb(241,143,136)","Improdutiva","rgb(0,0,0)")

	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"STATUS","Status","cellTemplate",.T.,.T.,aLabels)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"H6_OP","OP","string",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"H6_PRODUTO","Produto","string",.T.)
	//  PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"B1_DESC","Desc. Produto","string",lExpResult)

	cCPOX3:="H6_OPERAC"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_DATAINI"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.T.)
	cCPOX3:="H6_HORAINI"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_DATAFIN"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.T.)
	cCPOX3:="H6_HORAFIN"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_QTDPROD"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"number",.T.)
	cCPOX3:="H6_QTDPERD"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_PT"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_DTAPONT"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.T.)
	cCPOX3:="H6_TEMPO"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_DTPROD"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"RECSH6","ID SH6","number",.T.)

	// PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C2_DATPRI","Previsão Início","string",.T.)
	// PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C2_DATPRF","Previsão Entrega","string",.T.)
	// PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C2_QUANT","Quantidade","string",.T.)
	// PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C2_QUJE","Qtd. Prod","string",.T.)
Return aColunas

/*/{Protheus.doc} montaQuery
Realiza a criação de objeto Json que define as colunas utilizadas na grid de detalhamento do monitor
@type Static Function
@author
@since
@version
@param  oFiltros, objeto Json, Contém as propriedades do monitor usadas para filtrar a query de busca
@param  dDataIni, data       , Data inicial do filtro
@param  dDataFin, data       , Data final do filtro
@return cQuery  , caracter   , Query utilizada para busca no banco de dados
/*/
Static Function montaQuery(oFiltros, dDataIni, dDataFin)
	Local cPerDias  := cValtoChar(oFiltros["PERIODO"])
	Local cProdutos := ""
	Local cQuery    := ""
	Local nIndice   := 0

	cQuery := " SELECT "
	cQuery += "     SC2.C2_FILIAL, SC2.C2_NUM, SC2.C2_ITEM, SC2.C2_SEQUEN, SC2.C2_ITEMGRD, SC2.C2_OP, SC2.C2_LOCAL,"
	cQuery += "     SC2.C2_PRODUTO, SB1.B1_DESC, SC2.C2_TPOP, SC2.C2_DATRF, SC2.C2_DATPRF, SC2.C2_QUJE, SC2.C2_QUANT, SC2.C2_DIASOCI, SC2.C2_DATPRI"
	cQuery += " FROM " +RetSqlName("SC2")+ " SC2 "
	cQuery += " LEFT JOIN "+RetSqlName("SB1")+" SB1 ON SB1.B1_FILIAL = '"+xFilial("SB1",oFiltros["FILIAL"])+"' AND SB1.B1_COD = SC2.C2_PRODUTO AND SB1.D_E_L_E_T_ = ' ' "
	cQuery += " WHERE SC2.C2_FILIAL = '"+ xFilial("SC2", oFiltros["FILIAL"])+"' "

	If oFiltros:HasProperty("PRODUTO") .And. ValType(oFiltros["PRODUTO"]) == "A"
		For nIndice := 1 To Len(oFiltros["PRODUTO"])
			If Empty(cProdutos)
				cProdutos := "'" + oFiltros["PRODUTO"][nIndice] + "'"
			Else
				cProdutos +=  ",'" + oFiltros["PRODUTO"][nIndice] + "'"
			EndIf
		Next nIndice
	EndIf
	If !Empty(cProdutos)
		cQuery += " AND SC2.C2_PRODUTO IN ("+cProdutos+") "
	EndIf
	If oFiltros["TIPOPERIODO"] == "X"
		If Val(cPerDias) >= 0
			dDataFin := PCPMonitorUtils():RetornaPeriodoFinal(oFiltros["TIPOPERIODO"],dDataIni,cPerDias)
		Else
			dDataIni := PCPMonitorUtils():RetornaPeriodoInicial(oFiltros["TIPOPERIODO"],dDataFin,cValtoChar(ABS(Val(cPerDias))))
		EndIf
	Else
		dDataIni := PCPMonitorUtils():RetornaPeriodoInicial(oFiltros["TIPOPERIODO"],dDataFin,cPerDias)
		dDataFin := PCPMonitorUtils():RetornaPeriodoFinal(oFiltros["TIPOPERIODO"],dDataIni,cPerDias)
	EndIf
	cQuery += " AND SC2."+oFiltros["FILTRODATA"]+" BETWEEN '"+dToS(dDataIni)+"' AND '"+dToS(dDataFin)+"' "
	cQuery += " AND SC2.D_E_L_E_T_ = ' ' "
Return cQuery

/*/{Protheus.doc} Static Function fStatusOp
Retorna o Status da Ordem de Produção
@type  Static Function
@author
@since
@version
@param  cOP       , caracter, Ordem de Produção
@param  cTpo      , caracter, Tipo da Ordem de Produção / Firme ou Prevista
@param  cDatrf    , caracter, Data de Encerramento
@param  nQuje     , numerico, Quantidade Apontada
@param  nQuant    , numerico, Quantidade Prevista
@param  cFilterFil, caracter, Filial informada no filtro
@return cStatusOp , caracter, Status da OP - 1-Prevista/2-Em aberto/3-Iniciada/4-Ociosa/5-Enc.Parcialmente/6-Enc.Totalmente
/*/
Static Function fStatusOp(cOp, cTpo, cDatrf, nQuje, nQuant, cDatOci, cDTINI, cFilterFil)
	Local cAliasTemp  := ""
	Local cQuery      := ""
	Local dEmissao    := dDatabase
	Local nRegSD3     := 0
	Local nRegSH6     := 0

	Default cOp       := ""
	Default cTpo      := ""
	Default cDatrf    := ""
	Default nQuant    := 0
	Default nQuje     := 0

	cDTINI := STOD(cDTINI)

	If cTpo == "P" //1-Prevista
		Return "1"
	EndIf
	If cTpo == "F" .And. !Empty(cDatrf) .And. (nQuje < nQuant)  //5-Enc.Parcialmente
		Return "5"
	EndIf
	If cTpo == "F" .And. !Empty(cDatrf) .And. (nQuje >= nQuant) //6-Enc.Totalmente
		Return "6"
	EndIf

	cAliasTemp:= "SD3TMP"
	cQuery    := "  SELECT COUNT(*) AS RegSD3, MAX(D3_EMISSAO) AS EMISSAO "
	cQuery    += "   FROM " + RetSqlName("SD3")
	cQuery    += "   WHERE D3_FILIAL   = '" + xFilial( "SC2", cFilterFil ) + "'"
	cQuery    += "     AND D3_OP       = '" + cOp + "'"
	cQuery    += "     AND D3_ESTORNO <> 'S' "
	cQuery    += "     AND D_E_L_E_T_  = ' '"
	cQuery    += "     GROUP BY D3_EMISSAO "
	cQuery    := ChangeQuery(cQuery)
	dbUseArea (.T., "TOPCONN", TCGENQRY(,,cQuery), cAliasTemp, .F., .T.)

	If !SD3TMP->(Eof())
		dEmissao := STOD(SD3TMP->EMISSAO)
		nRegSD3 := SD3TMP->RegSD3
	EndIf

	cAliasTemp:= "SH6TMP"
	cQuery    := "  SELECT COUNT(*) AS REGSH6 "
	cQuery    += "   FROM " + RetSqlName("SH6")
	cQuery    += "   WHERE H6_FILIAL   = '" + xFilial("SH6", cFilterFil) + "'"
	cQuery    += "     AND H6_OP       = '" + cOp + "'"
	cQuery    += "     AND D_E_L_E_T_  = ' '"
	cQuery    := ChangeQuery(cQuery)
	dbUseArea ( .T., "TOPCONN", TCGENQRY(,,cQuery), cAliasTemp, .F., .T.)

	If !SH6TMP->(Eof())
		nRegSH6 := SH6TMP->REGSH6
	EndIf

	SD3TMP->(DbCloseArea())
	SH6TMP->(DbCloseArea())

	If cTpo == "F" .And. Empty(cDatrf)
		If (nRegSD3 < 1 .And. nRegSH6 < 1) .And. (Max(dDataBase - cDTINI,0) < If(cDatOci==0,1,cDatOci)) //2-Em aberto
			Return "2"
		EndIf
		If (nRegSD3 > 0 .Or. nRegSH6 > 0) .And. (Max((ddatabase - dEmissao),0) > If(cDatOci >= 0,-1,cDatOci)) //3-Iniciada
			Return "3"
		EndIf
		If (Max((ddatabase - dEmissao),0) > cDatOci .Or. Max((ddatabase - cDTINI),0) >= cDatOci)  //4-Ociosa
			Return "4"
		EndIf
	EndIf
Return

/*/{Protheus.doc} ValidaPropriedades
Valida os dados informados nas propriedades do Monitor
@type Method
@author
@since
@version
@param  oFiltros, objeto json, Objeto json com os filtros para a consulta dos dados
@return aRetorno, array      , [1] logico - indica se os dados são válidos [2] caracter - mensagem de erro
/*/
Method ValidaPropriedades(oFiltros) Class DelpiOpAtual
	Local aRetorno := {.T.,""}

	PCPMonitorUtils():ValidaPropriedadeFilial(oFiltros["FILIAL"],aRetorno)

	If aRetorno[1] .And. oFiltros["TIPOPERIODO"] == "X"
		If !oFiltros:HasProperty("PERIODO") .Or. oFiltros["PERIODO"] == Nil .Or. Empty(oFiltros["PERIODO"])
			aRetorno[1] := .F.
			aRetorno[2] := "Deve ser informada a quantidade de dias para o período personalizado."
		EndIf
	EndIf
Return aRetorno

/*/{Protheus.doc} buscaSerie
Realiza um "De Para" buscando o texto relativo ao código de status das OPs
@type Static Function
@author
@since
@version
@param  cStatusOp , caracter, Código do status da ordem de produção
@return cDscStatus, caracter, Descrição do status da ordem de produção
/*/
Static Function buscaSerie(cStatusOp)
	Local cDscStatus := ""

	Do Case
	Case cStatusOp == "1"
		cDscStatus :=  "Prevista"
	Case cStatusOp == "2"
		cDscStatus := "Em aberto"
	Case cStatusOp == "3"
		cDscStatus := "Iniciada"
	Case cStatusOp == "4"
		cDscStatus := "Ociosa"
	Case cStatusOp == "5"
		cDscStatus := "Enc. Parcialmente"
	Case cStatusOp == "6"
		cDscStatus := "Enc. Totalmente"
	EndCase
Return cDscStatus



sTATIC function DlpWeek(dDate)
	Local dFWDayCYear 	:= dBIFirstWeekDay(Year(dDate)) //Primeiro dia da primeira semana do ano analisado.
	Local dFWDayLYear 	:= Nil 							//Primeiro dia da primeira semana do ano anterior.
	Local dFDayLastWeek	:= Nil                         	//Primeiro dia da última semana do ano.
	Local dFDayLYear		:= Nil 							//Primeiro dia do ano anterior.
	Local dLDayLYear		:= Nil 							//Último dia do ano anterior.
	Local dFWeekDay 		:= Nil								//Dia que identifica a primeira semana do ano (04/01).
	Local nWeek 			:= 1                           	//Semana do ano.

	//-------------------------------------------------------------------
	// Calcula a semana do ano.
	//-------------------------------------------------------------------
	If ( ( dDate - dFWDayCYear ) > 6)
		nWeek := Int( ( dDate - dFWDayCYear ) / 7 ) + 1
	Else
		//-------------------------------------------------------------------
		// Calcula a semana do ano quando os últimos dias estão no próximo ano.
		//-------------------------------------------------------------------
		If ( ( dDate - dFWDayCYear ) < 0)
			dFDayLYear 	:= CToD("01/01/" + cBIStr( Year(dDate) -1) )
			dLDayLYear 	:= CToD("31/12/" + cBIStr( Year(dDate) -1) )
			dFWDayLYear := dBIFirstWeekDay( Year( dFDayLYear ) )
			nWeek 		:= Int( ( dLDayLYear - dFWDayLYear ) / 7 ) + 1
		Else
			nWeek = 1
		EndIf
	EndIf

	//-------------------------------------------------------------------
	// Verifica se é a última semana do um ano, ou primeira do próximo.
	//-------------------------------------------------------------------
	If ( nWeek == 52 .Or. nWeek == 53 )
		dFWeekDay   	:= CToD( "04/01/" + cBIStr( Year( dDate ) + 1 ) )
		dFDayLastWeek := dBIWeekToDate( nWeek, Year( dDate ) )

		If ( dFWeekDay >= dFDayLastWeek .And. dFWeekDay <= dFDayLastWeek + 6 )
			nWeek := 1
		EndIf
	EndIf
return {nWeek,dFWDayCYear, daySub(dFWDayCYear,7)}

Static Function AjustaHora(cHora,nTam)
	Local nLen := Len(cHora) - nTam
	While nLen > 0
		nLen--
		If SubStr(cHora,1,1)<>"0"
			Exit
		EndIf
		cHora := Substr(cHora,2,Len(cHora))
	EndDo
Return cHora
