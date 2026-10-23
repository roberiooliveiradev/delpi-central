#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'
Static cTipoTemp
#DEFINE COR_AZUL_ESCURO              'rgb(0,0,84)'
#DEFINE COR_AZUL              'rgb(0,0,165)'
#DEFINE COR_VERMELHO          'rgb(241,143,136)'
#DEFINE COR_AZUL_CLARO        'rgb(0,255,255)'
#DEFINE COR_CINZA             'rgb(128,128,128)'
#DEFINE COR_AMARELO           'rgb(255,255,0)'
#DEFINE COR_VERDE             'rgb(126,226,148)'
#DEFINE COR_ROXO              'rgb(153,0,153)'
#DEFINE COR_ROSA              'rgb(255,51,153)'
#DEFINE COR_BRANCO            'rgb(255,255,255)'
#DEFINE COR_LARANJA           'rgb(255,128,0)'
#DEFINE COR_VERDE_FORTE       'rgb(38,186,65)'
#DEFINE COR_VERMELHO_FORTE    'rgb(245,0,49)'
#DEFINE COR_AMARELO_ESCURO    'rgb(255,207,1)'
#DEFINE COR_AMARELO_CLARO    'rgb(238, 206, 45)'
#DEFINE COR_PRETO             'rgb(0,0,0)'
#DEFINE COR_AMARELO_QUEIMADO  'rgb(238,173,45)'
#DEFINE COR_TURNO_1  'rgb(44,146,213)'
#DEFINE COR_TURNO_2  'rgb(2,54,103)'
#DEFINE COR_TURNO_3  'rgb(15,15,15)'

Class DelpiEficiencia FROM LongNameClass
	Static Method BuscaDados(oFiltros, cTipo, cSubTipo)
	Static Method BuscaDetalhes(oFiltros, nPagina)
	Static Method ValidaPropriedades(oFiltros)
EndClass



/*/{Protheus.doc} BuscaDados
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
Method BuscaDados(oFiltros, cTipo, cSubTipo) Class DelpiEficiencia

	// Local cAliasHZA  := GetNextAlias()
	Local cJsonDados := ""
	Local cQuery     := ""
	Local cTxtPrc    := ""
	Local cTxtSec    := ""
	Local cUnMedida  := ""
	Local cTurno 		 := ""
	Local cTrnName	 := ""
	// Local dFilterDat := PCPMonitorUtils():RetornaPeriodoFinal(oFiltros["05_TIPOPERIODO"],ddatabase,cValtoChar(oFiltros["06_PERIODO"]))
	Local nIndLinha  := 0
	Local nQuant     := 0
	Local nLotes     := 0
	Local nPos       := 0
	Local nSaldo     := 0
	Local nPosHeader := 0
	Local nZeros     := At(":", PesqPict("SH6", "H6_TEMPO")) - 1

	Local oJsonRet   := JsonObject():New()
	Local oGauge     := PCPMonitorGauge():New()
	Local oStylePrc  := JsonObject():New()

	Local cEol := chr(10)
//oGauge["corFundo"]  := "RGB(124,124,124)"
//oGauge["corTitulo"] := "RGB(0,0,0)"

	oJsonRet["corfundo"]  := "RGB(124,124,124)"
	oJsonRet["corTitulo"] := "Black"
	oJsonRet["altura"] := "350"
	oJsonRet["alturaMinimaWidget"] := "350px" //Altura mínima do monitor. Se não for informada, assumirá o valor 350px
	oJsonRet["alturaMaximaWidget"] := "350px" //500 Altura máxima do monitor. Se não for informada, assumirá o valor 350px
	oJsonRet["tags"]               := {}      //Array de objetos json com as tags que serão visualizadas no monitor
	oJsonRet["series"]             := {}      //Array de objetos json com as séries do gráfico. Será apenas inicializado para o gráfico do tipo velocímetro.
	oJsonRet["categorias"]         := {}      //Array de strings com as categorias do gráfico. Será apenas inicializado para o gráfico do tipo velocímetro.
	//oJsonRet["linhas"] :={}

	/*pEGA OS fILTROS PARA ENVIAR A QUERY*/

	// oFiltros["01_B8_FILIAL"] := PadR(oFiltros["01_B8_FILIAL"], FWSizeFilial())

	IF VALTYPE(oFiltros["FILIAL"]) =="A"
		if len(oFiltros["FILIAL"]) >0
			cCodFil := oFiltros["FILIAL"][1]
		endif
	ELSE
		cCodFil := oFiltros["RECURSO"]
	ENDIF
	IF VALTYPE(oFiltros["RECURSO"]) =="A"
		if len(oFiltros["RECURSO"]) >0
			cCodRecur := oFiltros["RECURSO"][1]
		endif
	ELSE
		cCodRecur := oFiltros["RECURSO"]
	ENDIF

	IF VALTYPE(oFiltros["TIPOPERIODO"]) =="A"
		if len(oFiltros["TIPOPERIODO"]) >0
			cDtPer := oFiltros["TIPOPERIODO"][1]
		endif
	ELSE
		cDtPer := oFiltros["TIPOPERIODO"]
	ENDIF

	IF VALTYPE(oFiltros["TURNO"]) =="A"
		if len(oFiltros["TURNO"]) >0
			cTurno := oFiltros["TURNO"][1]
		endif
	ELSE
		cTurno := oFiltros["TURNO"]
	ENDIF

	IF cEmpAnt == '01' .AND. cFilAnt == '02'

		if cTurno =="AT"

			IF SUBSTR(Time(),1,5) >= "04:34" .AND. SUBSTR(Time(),1,5) < "14:18"

				cTurno :="T1"

			ELSEIF SUBSTR(Time(),1,5)  >= "14:18" .AND. SUBSTR(Time(),1,5) < "23:50"

				cTurno :="T2"

			ELSEIF SUBSTR(Time(),1,5)  >= "00:00" .AND. SUBSTR(Time(),1,5) < "04:34"

				cTurno :="T3"

			ENDIF

		ENDIF

	ELSE

		cTurno := "T1"

	ENDIF

	if cTurno == "T1"

		cTrnName := "Turno 1"

	elseif cTurno == "T2"

		cTrnName := "Turno 2"

	elseif cTurno == "T3"

		cTrnName := "Turno 3"

	elseif cTurno == "AT"

		cTrnName := "Turno Atual"

	else

		cTrnName := "Turno Total"

	endif

	if cDtPer == "D"
		cTPFil :=  "Dia Atual"

	elseif  cDtPer == "S"
		cTPFil := "Semana Atual"

	elseif  cDtPer == "M"
		cTPFil := "Mes Atual"

	ENDIF

	cDescRec := ""
	dbSelectArea("SH1")
	SH1->( DbSetOrder(1) )
	if   SH1->(dbSeek( cCodFil+cCodRecur))
		cDescRec := ALLTRIM(SH1->H1_DESCRI)
	ENDIF

	//cTxtHD:= alltrim(cCodRecur)+"<br>"+cDescRec
	cTxtHD:= alltrim(cCodRecur)//+"<br>"+cDescRec
	//oJsonRet["textoTitulo"]               := cTxtHD
	//oStyleHdr["text"]               := cTxtHD
	//PCPMonitorUtils():AdicionaHeaderDetalhe(oJsonRet["headers"],@nPosHeader,cTxtHD,"po-sm-12 po-pb-2",oStyleHdr:ToJson())


	//Query com os filtros para buscar as informações e apresentar no monitor
	cAliasQry:= delpi.custom.pcp.utils.U_RetQueryMonitorEficiencia(oFiltros)


	nHRPrd    :="000:00"
	nHRImpPrd :="000:00"
	nQTDH6 :=0
	nEfiTot := 0.00
	while  (cAliasQry)->(!Eof())

		if (cAliasQry)->H6_TIPO=='I'
			(cAliasQry)->(dbSkip())
			LOOP
		ENDIF
		nQTDH6++
		cCHVSH6 :=  (cAliasQry)->RECSH6
		SH6->(DbGOTO(cCHVSH6))

		cRoteiro := ""
		dbSelectArea("SC2")
		dbSeek(xFilial("SC2")+SH6->H6_OP)
		If !Empty(SC2->C2_ROTEIRO)
			cRoteiro:=SC2->C2_ROTEIRO
		Else
			dbSelectArea("SB1")
			dbSeek(xFilial("SB1")+SH6->H6_PRODUTO)
			cRoteiro:=SB1->B1_OPERPAD
		EndIf


		dbSelectArea("SG2")
		a630SeekSG2(1,SH6->H6_PRODUTO,SH6->H6_FILIAL+SH6->H6_PRODUTO+cRoteiro+SH6->H6_OPERAC)

		cHrReal		:= delpi.custom.pcp.utils.U_R895Calc()
		cHrPrev		:=TimeH6()
		cTipoTemp:=GetMV("MV_TPHR")
		If cTipoTemp == "C"
			cHrPrev := Val(StrTran(cHrPrev, ":", "."))
		EndIf

		nVlrEfi := ((cHrReal+ SG2->G2_SETUP) / cHrPrev )
		nEfiTot += nVlrEfi
		(cAliasQry)->(dbSkip())
	EndDo
	(cAliasQry)->(dbCloseArea())
	nEfiTot := round(( (nEfiTot/nQTDH6)*100),2)

	//nValorFim := 25000 //Valor Maximo da Meta

	cType :="arch" //Especifica o tipo do velocímetro. "semi","arch","full"
	nValSemaf1 :=50
	nValSemaf2 := 75
	nValSemaf3 := 92
	nValorFim := 100
	cValSemaf1 := "50"
	cValSemaf2 := "75"
	cValSemaf3 := "92"
	cValorFim := "100"
	nThick:= 30//Especifica a espessura da barra do velocímetro.
	cClrRed := "rgb(198, 72, 64)"
	cClrLar := "rgb(234, 155, 62)"
	cClrGre := "rgb(0, 178, 142)"
	cHxGre:="#00b28e"
	cHxRed:="#c64940"



	cLabel := "% Atingido"
	cLabel += "<br>"+cTrnName
	//cLabel += "<br>"+" "+"<br>"+" "+"<br>"+cTxtHD
	//  cLabel += "<br>Realizado: R$ "+Transform(nVlrFat,"@E 999,999,999.99")
	//
	//  cLabel1 := '<br>Previsto: R$ '+Transform(nVlrPrev,"@E 999,999,999.99")
	//cLabel2 := 'Previsto: R$ '+Transform(nVlrPrev,"@E 999,999,999.99")
	aCateg :={}
	aadd(aCateg,"Categoria1")
	aadd(aCateg,"Categoria2")
	aadd(aCateg,"Categoria3")
	//cPrepend :="TESTE PREPEND"
	//  oGauge:SetPrepend(cPrepend)
	//  oGauge["corTitulo"]
	oGauge:SetMaxValue(nValorFim)
	oGauge:SetValue(nEfiTot)
	oGauge:SetMargin(5)
	oGauge:SetType(cType)
	oGauge:SetThick(nThick) //Especifica a espessura da barra do velocímetro.
	// oGauge:SetValueStyle("color",IIF(nPerMeta < nValSemaf1,cClrRed,IIF(nPerMeta < nValSemaf2,cClrLar,COR_VERDE_FORTE)))
	if nEfiTot == 0.00
		cCLRValue := COR_VERMELHO_FORTE
		cLabel1 := ""
	ELSEif nEfiTot < nValSemaf1
		cCLRValue := COR_VERMELHO_FORTE
		cLabel1 := "Nivel Critico"
	elseif  nEfiTot < nValSemaf2
		cCLRValue := COR_AMARELO_QUEIMADO
		cLabel1 := "Abaixo da Meta"
	elseif   nEfiTot < nValSemaf3
		cCLRValue := COR_AMARELO_CLARO
		cLabel1 := "Proximo da Meta"
	else
		cCLRValue := COR_VERDE_FORTE
		cLabel1 := "Meta Atingida"
	endif

	oGauge:SetValueStyle("color",cCLRValue)
	oGauge:SetValueStyle("text-align","center")
	oGauge:SetValueStyle("font-weight","bold")
	oGauge:SetValueStyle("font-size","40px")
	//oGauge:SetValueStyle("line-height","0px")
	cNLine := "3.5"
	oGauge:SetLabelStyle("font-weight","bold")
	oGauge:SetLabelStyle("text-align","center")
	oGauge:SetLabelStyle("font-size","20px")
	oGauge:SetLabelStyle("line-height","1")
	oGauge:SetLabel(cLabel+"<br>")
	oGauge:SetAppendStyle("color",cCLRValue)
	oGauge:SetAppendStyle("text-align","center")
	oGauge:SetAppendStyle("font-weight","bold")
	oGauge:SetAppendStyle("font-size","25px")
	oGauge:SetAppendStyle("line-height",cNline)
	oGauge:SetAppend("<br>"+cLabel1)
	//cNLine := "5.5"
	//oGauge:SetPrependStyle("color",cCLRValue)
	//oGauge:SetPrependStyle("text-align","center")
	//oGauge:SetPrependStyle("font-weight","bold")
	//oGauge:SetPrependStyle("font-size","25px")
	//oGauge:SetPrependStyle("line-height",15)
	//oGauge:SetPrepend("<br>2pre "+cTxtHD)
	//oGauge:SetLabelStyle("line-height","1")
	oGauge:SetLabel(cLabel+"<br>")
//Local oEstHeader := JsonObject():New()
	oGauge:SetThreshold("0",COR_VERMELHO_FORTE)
	oGauge:SetThreshold(cValSemaf1,COR_AMARELO_QUEIMADO)
	oGauge:SetThreshold(cValSemaf2,COR_AMARELO_CLARO)
	oGauge:SetThreshold(cValSemaf3,COR_VERDE_FORTE)
	If Val(cValSemaf1) > 0
		oGauge:SetMarker("0")
	Endif
	oGauge:SetMarker(cValSemaf1)
	oGauge:SetMarker(cValSemaf2)
	oGauge:SetMarker(cValSemaf3)
	oGauge:SetMarker(cValorFim)
	oJsonRet["cortitulo"] := "RGB(0,0,0)"
	oJsonRet["titulo"] := "GDA"
	//Atribui o objeto json do velocímetro ao objeto json de retorno do método
	oJsonRet["gauge"]      := oGauge:GetJsonObject()

	cJsonDados :=  oJsonRet:toJson()


	FreeObj(oGauge)
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
Method BuscaDetalhes(oFiltros, nPagina) Class DelpiEficiencia
	//Local cAliasQry  := GetNextAlias()
	Local cJsonDados := ""
	Local cQuery     := ""
	Local cOp        := ""
	Local cStatusOp  := ""
	Local dDataIni   := Date()//dDataBase
	Local dDataFin   := Date()//dDataBase
	Local lExpResult := .F.
	Local nIndice    := 0
	Local nPos       := 0
	Local nPosTag   := 0
	Local cTurno := ""
	Local cOpera := ""
	Local cUltOpe := ""
	Local nStart     := 0
	Local oDados     := JsonObject():New()
	Local cEol := chr(10)
	Default nPagina    := 1
	Default nTamPagina := 10

	If nPagina == 0
		lExpResult := .T.
	EndIf

	IF VALTYPE(oFiltros["FILIAL"]) =="A"
		if len(oFiltros["FILIAL"]) >0
			cCodFil := oFiltros["FILIAL"][1]
		endif
	ELSE
		cCodFil := oFiltros["RECURSO"]
	ENDIF
	IF VALTYPE(oFiltros["RECURSO"]) =="A"
		if len(oFiltros["RECURSO"]) >0
			cCodRecur := oFiltros["RECURSO"][1]
		endif
	ELSE
		cCodRecur := oFiltros["RECURSO"]
	ENDIF

	IF VALTYPE(oFiltros["TIPOPERIODO"]) =="A"
		if len(oFiltros["TIPOPERIODO"]) >0
			cDtPer := oFiltros["TIPOPERIODO"][1]
		endif
	ELSE
		cDtPer := oFiltros["TIPOPERIODO"]
	ENDIF

	if cDtPer == "D"
		cTPFil :=  "Dia Atual"
		//dDtIni := dDataBase
		//dDtFin := dDataBase
	elseif  cDtPer == "S"
		cTPFil := "Semana Atual"
		//aRet := DlpWeek(dDataBase)
		//dDtIni := aRet[2]
		//dDtFin := aRet[3]
	elseif  cDtPer == "M"
		cTPFil := "Mes Atual"
		// dDtIni := FirstDate(dDataBase)
		// dDtFin := LastDate(dDataBase)
	ENDIF
	//VALTYPE(oFiltros["PARAMETROSDETALHE"])

	cAliasQry:= delpi.custom.pcp.utils.U_RetQueryMonitorEficiencia(oFiltros)


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
		cCHVSH6 :=  (cAliasQry)->RECSH6
		SH6->(DbGOTO(cCHVSH6))

		cRoteiro := ""
		dbSelectArea("SC2")
		dbSeek(xFilial("SC2")+SH6->H6_OP)
		If !Empty(SC2->C2_ROTEIRO)
			cRoteiro:=SC2->C2_ROTEIRO
		Else
			dbSelectArea("SB1")
			dbSeek(xFilial("SB1")+SH6->H6_PRODUTO)
			cRoteiro:=SB1->B1_OPERPAD
		EndIf

		dbSelectArea("SG2")
		a630SeekSG2(1,SH6->H6_PRODUTO,SH6->H6_FILIAL+SH6->H6_PRODUTO+cRoteiro+SH6->H6_OPERAC)

		cHrReal		:= delpi.custom.pcp.utils.U_R895Calc()
		cHrPrev		:=TimeH6()
		cTipoTemp:=GetMV("MV_TPHR")
		If cTipoTemp == "C"
			cHrPrev := Val(StrTran(cHrPrev, ":", "."))
		EndIf
		cNmUsr :=""
		PswOrder(1)
		If PswSeek( SH6->H6_OPERADO, .T. )
			cNmUsr := PswRet()[1][4]
		ENDIF

		nVlrEfi := round (( ((cHrReal+ SG2->G2_SETUP) / cHrPrev )*100),2)

		//  IF cOpera != (cAliasQry)->H6_OPERADO

		//      aTurno := DlpFiTrn((cAliasQry)->H6_OPERADO,(cAliasQry)->H6_DATAINI)
		//      cTurno := "{"+aTurno[1]+":"+aTurno[2]+"}"

		//  ENDIF


		// cOpera := (cAliasQry)->H6_OPERADO
		//   {"04:34","14:18"},{"14:18","23:50"},{"00:00","04:34"}

		// ajuste gabriel
		cTurno := "T0"
		if  (cAliasQry)->H6_HORAINI >= "04:34" .and.  (cAliasQry)->H6_HORAINI < "14:18"
			cTurno := "T1"
		elseif  (cAliasQry)->H6_HORAINI >= "14:18" .and.  (cAliasQry)->H6_HORAINI < "23:50"
			cTurno := "T2"
		elseif  (cAliasQry)->H6_HORAINI >= "00:00" .and.  (cAliasQry)->H6_HORAINI < "04:34"
			cTurno := "T3"
		endif

		//IF (cSelTrn != cTurno .AND. cSelTrn != "T4")
		//	(cAliasQry)->(dbSkip())
		//ENDIF

		oDados["items"][nPos]["H6_FILIAL"]    := alltrim((cAliasQry)->H6_FILIAL)
		oDados["items"][nPos]["ZTURNO"]       := alltrim(cTurno)
		oDados["items"][nPos]["H6_OP"]        := alltrim((cAliasQry)->H6_OP)
		oDados["items"][nPos]["H6_PRODUTO"]   := alltrim((cAliasQry)->H6_PRODUTO)
		oDados["items"][nPos]["H6_OPERAC"]    := alltrim((cAliasQry)->H6_OPERAC)
		oDados["items"][nPos]["G2_DESCRI"]    := alltrim(SG2->G2_DESCRI)
		oDados["items"][nPos]["H6_OPERADO"]   := alltrim((cAliasQry)->H6_OPERADO)
		oDados["items"][nPos]["SYS_USR"]      := alltrim(cNmUsr)
		oDados["items"][nPos]["H6_DATAINI"]   := PCPMonitorUtils():FormataData((cAliasQry)->H6_DATAINI, 5)
		oDados["items"][nPos]["H6_HORAINI"]   := alltrim((cAliasQry)->H6_HORAINI)
		oDados["items"][nPos]["H6_DATAFIN"]   := PCPMonitorUtils():FormataData((cAliasQry)->H6_DATAFIN, 5)
		oDados["items"][nPos]["H6_HORAFIN"]   := alltrim((cAliasQry)->H6_HORAFIN)
		oDados["items"][nPos]["H6_QTDPROD"]   := (cAliasQry)->H6_QTDPROD
		oDados["items"][nPos]["H6_QTDPERD"]   := (cAliasQry)->H6_QTDPERD
		oDados["items"][nPos]["H6_PT"]        := (cAliasQry)->H6_PT
		oDados["items"][nPos]["H6_DTAPONT"]   := PCPMonitorUtils():FormataData( (cAliasQry)->H6_DTAPONT, 5)
		oDados["items"][nPos]["H6_TEMPO"]     := (cAliasQry)->H6_TEMPO
		oDados["items"][nPos]["H6_DTPROD"]    := PCPMonitorUtils():FormataData( (cAliasQry)->H6_DTPROD, 5)
		oDados["items"][nPos]["STATUS"]       := (cAliasQry)->H6_TIPO
		oDados["items"][nPos]["RECSH6"]       := (cAliasQry)->RECSH6
		oDados["items"][nPos]["ZEFIC"]        := nVlrEfi
		oDados["items"][nPos]["H6_OBSERVA"]   := alltrim( (cAliasQry)->H6_OBSERVA)

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
	Local aLbl2    := {}
	Local nIndice    := 0
	Local nIndLabels := 0
	Local nIndLbl2 := 0

	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLabels,@nIndLabels,"P","rgb(126,226,148)","Produtiva","rgb(0,0,0)")
	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLabels,@nIndLabels,"I","rgb(241,143,136)","Improdutiva","rgb(0,0,0)")
	/*
		COR_AZUL
		COR_VERMELHO
		COR_AZUL_CLARO
		COR_CINZA
		COR_AMARELO
		COR_VERDE
		COR_ROXO
		COR_ROSA
		COR_BRANCO
		COR_LARANJA
		COR_VERDE_FORTE
		COR_VERMELHO_FORTE
		COR_AMARELO_ESCURO
		COR_AMARELO_CLARO
		COR_PRETO
		COR_AMARELO_QUEIMADO
	*/
	// ajuste gabriel
	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLbl2,@nIndLbl2,"T0",COR_PRETO ,"Turno 0","rgb(0,0,0)")
	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLbl2,@nIndLbl2,"T1",COR_TURNO_1 ,"Turno 1","rgb(0,0,0)")
	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLbl2,@nIndLbl2,"T2",COR_TURNO_2 ,"Turno 2","rgb(255,255,255)")
	PCPMonitorUtils():AdicionaLabelsColunaTabela(aLbl2,@nIndLbl2,"T3",COR_TURNO_3 ,"Turno 3","rgb(255,255,255)")

	// ajuste gabriel
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"STATUS","Status","cellTemplate",.T.,.T.,aLabels)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"ZTURNO","Turno","cellTemplate",.T.,.T.,aLbl2)
	//PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"ZTURNO","TURNO","string",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"H6_OP","OP","string",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"H6_PRODUTO","Produto","string",.T.)
	//  PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"B1_DESC","Desc. Produto","string",lExpResult)

	cCPOX3:="H6_OPERAC"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.F.)

	cCPOX3:="G2_DESCRI"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)

	cCPOX3:="H6_DATAINI"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.F.)
	cCPOX3:="H6_HORAINI"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.t.)
	cCPOX3:="H6_DATAFIN"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.F.)
	cCPOX3:="H6_HORAFIN"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_QTDPROD"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"number",.T.)
	cCPOX3:="H6_QTDPERD"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.f.)
	cCPOX3:="H6_PT"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.F.)
	cCPOX3:="H6_DTAPONT"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.f.)
	cCPOX3:="H6_TEMPO"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_DTPROD"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"date",.f.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"RECSH6","ID SH6","number",.f.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"ZEFIC","EFICIENCIA","number",.T.)

	cCPOX3:="H6_OBSERVA"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
	cCPOX3:="H6_OPERADO"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,"Operador","string",.f.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"SYS_USR","Nm Operador","string",.T.)

Return aColunas

/*/{Protheus.doc} ValidaPropriedades
Valida os dados informados nas propriedades do Monitor
@type Method
@author
@since
@version
@param  oFiltros, objeto json, Objeto json com os filtros para a consulta dos dados
@return aRetorno, array      , [1] logico - indica se os dados são válidos [2] caracter - mensagem de erro
/*/
Method ValidaPropriedades(oFiltros) Class DelpiEficiencia
	Local aRetorno := {.T.,"TESTE VALIDA"}

	//PCPMonitorUtils():ValidaPropriedadeFilial(oFiltros["FILIAL"],aRetorno)

	//If aRetorno[1] .And. oFiltros["TIPOPERIODO"] == "X"
	//    If !oFiltros:HasProperty("PERIODO") .Or. oFiltros["PERIODO"] == Nil .Or. Empty(oFiltros["PERIODO"])
	//        aRetorno[1] := .F.
	//        aRetorno[2] := "Deve ser informada a quantidade de dias para o período personalizado."
	//    EndIf
	//EndIf
Return aRetorno




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
