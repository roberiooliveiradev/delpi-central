#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'

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
#DEFINE COR_PRETO             'rgb(0,0,0)'
#DEFINE COR_AMARELO_QUEIMADO  'rgb(238,173,45)'

/*/{Protheus.doc} DelpiSegmento
Classe para prover os dados do faturamento por segmento
@type Class
@author douglas.heydt
@since 30/06/2023
@version P12.1.2310
@return Nil
/*/
Class DelpiSegmento FROM LongNameClass
	Static Method BuscaDados(oFiltros, cTipo, cSubTipo)
	Static Method BuscaDetalhes(oFiltros, nPagina)
	Static Method ValidaPropriedades(oFiltros)
EndClass

/*/{Protheus.doc} CargaMonitor
Realiza a carga do Monitor padrão na base de dados
@type Method
@author douglas.heydt
@since 30/06/2023
@version P12.1.2310
@return lRet, logico, Indica se conseguiu realizar a carga
/*/
/*/{Protheus.doc} BuscaDados
Responsável por realizar a busca dos dados que serão exibidos no monitor (gráfico ou texto)

@type Class
@author douglas.heydt
@since 30/06/2023
@version P12.1.2310
@param	oFiltros  , objeto Json, Contém as propriedades do monitor usadas para filtrar a query de busca
@param	cTipo     , caracter   , Tipo chart/info
@param	cSubTipo  , caracter   , Tipo de grafico pie/bar/column
@return cJsonDados, caracter   , Retorna um novo Json em formato texto, pronto para conversão e exibição no front
/*/
Method BuscaDados(oFiltros, cTipo, cSubTipo) Class DelpiSegmento
	Local aSaldos    := {}
	Local aSaldos2   := {}
	Local aPeriodos  := PCPMonitorUtils():RetornaListaPeriodosPassado(oFiltros["03_TIPOPERIODO"],cValToChar(oFiltros["04_PERIODO"]))
	Local aChaves    := {}
	Local aChaves2  := {}
	Local cAliasQry  := GetNextAlias()
	//Local cAliasSZC  := GetNextAlias()
	Local cJsonDados := ""
	Local cUnMed     := ""
	// Local cQuery     := ""
	Local cEmpAtu	 := ""
	Local dDataAjust := Nil
	Local dDataIni   := dDatabase
	Local dDataFin   := dDatabase
	Local nPosTag    := 0
	Local nX         := 0
	Local cPeriod 	:= 0
	Local nIndSerie := 0
	Local cFilFil   := ""
	Local cSql := ""
	Local oJsonRet   := JsonObject():New()
	Local oPeriods   := JsonObject():New()
	Local oMetas		 := JsonObject():New()

	Local cTpMeta 	 := "1"
	Local cTPData    := ""
	Local cCodFil 	 := cFilAnt
	Local cSegDe 	 := ""
	Local cSegAte 	 := ""
	Local cDtRefDe 	 := DtoS(dDataBase)
	Local cDtRefAte	 := DtoS(dDataBase)
	Local cCliDe	 := ""
	Local cCliAte	 := ""
	Local cLojaDe	 := ""
	Local cLojaAte	 := ""
	// Local nPerMeta := 0.00
	// Local nVlrMeta := 0.00

	oJsonRet["alturaMinimaWidget"] := "350px"
	oJsonRet["alturaMaximaWidget"] := "900px"
	oJsonRet["tags"]               := {}
	oJsonRet["series"]             := {}

	oFiltros["FILIAL"] := PadR(oFiltros["FILIAL"], FWSizeFilial())
	cUnMed  := "KG"//Posicione("SB1",1,xFilial("SB1",oFiltros["FILIAL"])+oFiltros["02_C2_PRODUTO"],"B1_UM")
	dDataIni:= aPeriodos[Len(aPeriodos)][1]
	dDataFin:= aPeriodos[1][2]
	cPeriod := oFiltros["PERIODO"]
	cFilFil := oFiltros["FILIAL"]
	cEmpAtu := IIF(!EMPTY(oFiltros["EMPRESA"]),oFiltros["EMPRESA"],cEmpAnt)

	//Especifica as propriedades do gráfico tipo velocímetro
	IF VALTYPE(oFiltros["TipoMeta"]) =="A"
		if len(oFiltros["TipoMeta"]) >0
			cTpMeta := oFiltros["TipoMeta"][1]
		endif
	ELSE
		cTpMeta := oFiltros["TipoMeta"]
	ENDIF
	//Especifica as propriedades do gráfico tipo velocímetro
	IF VALTYPE(oFiltros["EMPRESA"]) =="A"
		if len(oFiltros["EMPRESA"]) >0
			cCodEmp := oFiltros["EMPRESA"][1]
		endif
	ELSE
		cCodEmp := oFiltros["EMPRESA"]
	ENDIF

	IF VALTYPE(oFiltros["FILIAL"]) =="A"
		if len(oFiltros["FILIAL"]) >0
			cCodFil := oFiltros["FILIAL"][1]
		endif
	ELSE
		cCodFil := oFiltros["FILIAL"]
	ENDIF

	IF VALTYPE(oFiltros["PERIODO"]) =="A"
		if len(oFiltros["PERIODO"]) >0
			cTPData := oFiltros["PERIODO"][1]
		endif
	ELSE
		cTPData := oFiltros["PERIODO"]
	ENDIF


	IF VALTYPE(oFiltros["QTDPERIODO"]) =="A"
		if len(oFiltros["QTDPERIODO"]) >0
			nQtdPer :=val( oFiltros["QTDPERIODO"][1])
		endif
	ELSE
		nQtdPer := val(oFiltros["QTDPERIODO"])
	ENDIF

	cAnoMes := substr(dtos(ddatabase),1,6)


	IF VALTYPE(oFiltros["SEGMENTODE"]) =="A"
		if len(oFiltros["SEGMENTODE"]) >0
			cSegDe  := oFiltros["SEGMENTODE"][1]
		endif
	ELSE
		cSegDe  := ''
	ENDIF

	IF VALTYPE(oFiltros["SEGMENTODE"]) =="A"
		if len(oFiltros["SEGMENTODE"]) >0
			cSegDe := oFiltros["SEGMENTODE"][1]
		endif
	ELSE
		if empty(oFiltros["SEGMENTODE"])
			cSegDe := ' '
		else
			cSegDe :=  oFiltros["SEGMENTODE"]
		ENDIF
	ENDIF

	IF VALTYPE(oFiltros["SEGMENTOATE"]) =="A"
		if len(oFiltros["SEGMENTOATE"]) >0
			cSegAte := oFiltros["SEGMENTOATE"][1]
		endif
	ELSE
		if empty(oFiltros["SEGMENTOATE"])
			cSegAte := 'ZZZZZZZZZ'
		else
			cSegAte :=  oFiltros["SEGMENTOATE"]
		ENDIF
	ENDIF

	if cTPData == 'M'
		IF nQtdPer == 0
			cDtRefDe  :=  FirstDate(MonthSub(DATE(),12))
			cDtRefAte :=  LastYDate(DATE())
		ELSE
			cDtRefDe  :=  FirstDate(MonthSub(DATE(),nQtdPer) )
			cDtRefAte :=  LastYDate(DATE())
		ENDIF
	ELSEif cTPData == "A"

		IF nQtdPer == 0
			cDtRefDe  :=  FirstYDate(YearSub(DATE() , 1))
			cDtRefAte :=  LastYDate(DATE())
		ELSE
			cDtRefDe  :=  FirstYDate(  YearSub(DATE() , nQtdPer) )
			cDtRefAte :=  LastYDate(DATE())
		ENDIF
	ELSEif cTPData == "D"
		IF nQtdPer == 0
			cDtRefDe  := FirstDate(DATE())
			cDtRefAte := LastDate(DATE())
		ELSE
			cDtRefDe  :=  DaySub(DATE() , nQtdPer)
			cDtRefAte :=  LastDate(DATE())
		ENDIF
	else
		IF VALTYPE(oFiltros["DTREFDE"]) =="A"
			if len(oFiltros["DTREFDE"]) >0
				cDtRefDe  :=   stod(REPLACE(oFiltros["DTREFDE"][1], '-', ''))
			endif
		ELSE
			cDtRefDe  := stod( REPLACE(oFiltros["DTREFDE"], '-', ''))
		ENDIF
		IF VALTYPE(oFiltros["DTREFATE"]) =="A"
			if len(oFiltros["DTREFATE"]) >0
				cDtRefAte  :=   stod(REPLACE(oFiltros["DTREFATE"][1], '-', ''))
			endif
		ELSE
			cDtRefAte  :=  stod(REPLACE(oFiltros["DTREFATE"], '-', ''))
		ENDIF
	ENDIF

	// K para milhares, M para milhões
	cCliDe := Space(TamSx3('A1_COD')[1])
	cCliAte := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))

	cLojaDe := Space(TamSx3('A1_LOJA')[1])
	cLojaAte := REPLICATE("Z",GETSX3CACHE("A1_LOJA","X3_TAMANHO"))

	cSql := "EXEC STP_DELPI_FATURAMENTO_"+cEmpAtu+"_SEGMENTOS"
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALDE VARCHAR(2)
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALATE VARCHAR(2)
	cSql +=  valtosql(cSegDe  ) +" , "//@SEGMENTO DE VARCHAR(15)
	cSql +=  valtosql(cSegAte  ) +" , "//@SEGMENTOATE VARCHAR(15)
	cSql +=  valtosql(cDtRefDe   ) +" , "//@EMISSAODE VARCHAR(8)
	cSql +=  valtosql(cDtRefAte  ) +" , "//@EMISSAOATE VARCHAR(8)
	cSql +=  valtosql(cCliDe  	) +" , "//@CLIENTEDE VARCHAR(6)
	cSql +=  valtosql(cCliAte   ) +" , "//@CLIENTEATE VARCHAR(6)
	cSql +=  valtosql(cLojaDe   ) +" , "//@LOJADE VARCHAR(2)
	cSql +=  valtosql(cLojaAte  ) +" , "//@LOJAATE VARCHAR(2)
	IF cCodEmp == '01'
		cSql +=  valtosql('A') +" , " //@ESTOQUE
	ELSE
		cSql +=  valtosql('S') +" , " //@ESTOQUE
	ENDIF
	cSql +=  valtosql('S')+" , "  //@DUPLICATA
	cSql +=  valtosql(cTPData) //@FORMDATE
	CONOUT(cSql)
	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cSql),cAliasQry,.F.,.F.)
	nVlrFat :=  0.00
	nVlrFatT := 0.00

	cSegIni :=""
	cSegFim :=""
	WHILE  (cAliasQry)->(!Eof())
		if empty(cSegIni)
			cSegIni := (cAliasQry)->SEGMENTO


		endif
		cSegFim := (cAliasQry)->SEGMENTO
		//	IF !EMPTY(dDiaEspe) .AND. dDiaEspe == (cAliasQry)->EMISSAO

		// Calculo Meta do Dia => Resumo: Valor orçado dentro do mes divido pela quantidade de dias uteis
		cAnoMes := substr((cAliasQry)->EMISSAO,1,6)

		// Com o AnoMes vc posiciona na SZC Retornando o campo ZC_ORCFAT
		// cQrySzc := "SELECT ZC_ORCFAT AS METADIA FROM SZC010 SCZ WHERE D_E_L_E_T_ = ' ' AND ZC_TIPO = '1' AND ZC_ANOMES = '"+cAnoMes+"' AND ZC_FIL = '"+cFilFil+"' AND ZC_EMP = '"+cEmpAtu+"'"
		// nMeta := MpSysExecScalar(cQrySzc,'METADIA')

		// AADD(aSaldos2,nMeta)

		// Dias úteis Abril 2020 sem considerar fim de semana  e feriados como dia útil.
		lSaturday  := .F.
		lSunday    := .F.
		lHoliday   := .F.
		dFirstDm :=  FirstDate(	stod((cAliasQry)->EMISSAO)	)  //primeiro dia do mes
		dLastDm  :=  LastDate(	stod((cAliasQry)->EMISSAO)	)  //ultimo dia do mes

		nQtDUtil:= DateWorkDay(dFirstDm,dLastDm,lSaturday,lSunday ,lHoliday ) //DateWorkDay - retorna os dias uteis com base na data

		IF cTPData =="D"
			dDataAjust := MesDia(stod((cAliasQry)->EMISSAO))//dToC(PCPMonitorUtils():RetornaPeriodoInicial(nQtDUtil,sToD((cAliasQry)->EMISSAO)))
			dDataAjust := substr(dDataAjust,1,2)+"-"+ substr(dDataAjust,3,2)
		ELSEIF cTPData =="M"
			dDataAjust := AnoMes(stod((cAliasQry)->EMISSAO))
			dDataAjust := substr(dDataAjust,3,2)+"-"+substr(dDataAjust,5,2)
		ELSEIF cTPData =="A"
			dDataAjust := Year2Str(stod((cAliasQry)->EMISSAO))//dToC(PCPMonitorUtils():RetornaPeriodoInicial(nQtDUtil,sToD((cAliasQry)->EMISSAO)))
		ENDIF
		nVlrFat :=   (cAliasQry)->LIQUIVENDA
		nVlrFat +=   (cAliasQry)->LIQDEV*-1
		nVlrFatT +=nVlrFat

		lSaturday  := .F.
		lSunday    := .F.
		lHoliday   := .F.

		conout("nVlrFat "+cvaltochar(nVlrFat))
		If oPeriods:HasProperty(dDataAjust)
			oPeriods[dDataAjust] += nVlrFat//nPerMeta
		Else
			oPeriods[dDataAjust] := nVlrFat//nPerMeta

		EndIf

		(cAliasQry)->(dbSkip())

	ENDDO

	(cAliasQry)->(dbCloseArea())

	aChaves := oPeriods:GetNames()

	For nX := 1 To Len(aChaves)
		aAdd(aSaldos, oPeriods[aChaves[nX]] )
		nVlrOri := aSaldos[nX]
		nVlrCalc := 0.00

		if  cTPData $ 'M_A'
			if nVlrOri >= 1000 .and.  nVlrOri <= 999999   // Milhares K
				nVlrCalc := aSaldos[nX]/1000
				aChaves[nX] := aChaves[nX]+" | R$ "+ alltrim(Transform(nVlrCalc,"@E 999,999,999.99"))+" K"
			elseif   nVlrOri >= 1000000 .and.  nVlrOri <= 999999999   // Milhoes M
				nVlrCalc := aSaldos[nX]/1000000
				aChaves[nX] := aChaves[nX]+" | R$ "+ alltrim(Transform(nVlrCalc,"@E 999,999,999.99"))+" M"
			else
				nVlrCalc := aSaldos[nX]
				aChaves[nX] := aChaves[nX]+" | R$ "+ alltrim(Transform(nVlrCalc,"@E 999,999,999.99"))
			ENDIF

		ENDIF
	Next nX

	IF cPeriod == "D"
		cToPer := "Diario"
	ELSEIF cPeriod == "M"
		cToPer := "Mensal"
	ELSEIF cPeriod == "A"
		cToPer := "Anual"
	ELSE
		cToPer := "Personalizado"
	ENDIF

	oJsonRet["categorias"] := aChaves
	cVlrFat:= Transform(	nVlrFatT , X3Picture("E1_VALOR"))


	dbSelectArea("SX5")
	SX5->(DbSetOrder(1))
	SX5->(MsSeek(xFilial("SX5")+"ZW"+cSegIni))
	cDSegIni := Alltrim(SX5->(X5Descri()))


	dbSelectArea("SX5")
	SX5->(DbSetOrder(1))
	SX5->(MsSeek(xFilial("SX5")+"ZW"+cSegFim))
	cDSegFim := Alltrim(SX5->(X5Descri()))
	PCPMonitorUtils():AdicionaSerieGraficoMonitor(oJsonRet["series"],@nIndSerie,COR_AZUL,aSaldos,"FATURAMENTO(R$) "+cVlrFat) //"Produção"
	PCPMonitorUtils():AdicionaCategoriasGraficoMonitor(oJsonRet["categorias"], aChaves)


	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"po-icon-calendar",dToC(cDtRefDe) + " - " + dToC(cDtRefAte)+" "+cToPer)
	if cDSegIni == cDSegFim
		cDscSeg:= cDSegFim
	else
		cDscSeg:= cDSegIni +"-" +cDSegFim
	endif
	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"po-icon-chart-columns",cDscSeg)
	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"po-icon-manufacture", cCodFil)
	cJsonDados :=  oJsonRet:toJson()

	FwFreeArray(aChaves)
	FwFreeArray(aPeriodos)
	FwFreeArray(aSaldos)
	FreeObj(oPeriods)
	FreeObj(oJsonRet)
Return cJsonDados

/*/{Protheus.doc} BuscaDetalhes
Realiza a busca dos dados para montar os detalhes do Monitor
@type Method
@author douglas.heydt
@since 30/06/2023
@version P12.1.2310
@param	oFiltros  , objeto Json , Contém as propriedades do monitor usadas para filtrar a query de busca
@param	nPagina   , numerico    , Número da página desejada para busca
@return cJsonDados, caracter    , Retorna um novo Json em formato texto, pronto para conversão e exibição no front
@return Nil
/*/
Method BuscaDetalhes(oFiltros,nPagina) Class DelpiSegmento
	Local cAliasQry  := GetNextAlias()
	Local cJsonDados := ""
	//  Local cQuery     := ""
	//  Local cOp        := ""
	//  Local cStatusOp  := ""
	//  Local dDataIni   := dDataBase
	//  Local dDataFin   := dDataBase
	Local lExpResult := .F.
	//  Local nIndice    := 0
	Local nPos       := 0
	//   Local nPosTag   := 0
	Local cEmpAtu
	Local nStart     := 0
	Local oDados     := JsonObject():New()
	Local cTpMeta 	 := "1"
	Local cTPData    := ""
	Local cCodFil 	 := cFilAnt
	Local cSegDe 	 := ""
	Local cSegAte 	 := ""
	Local cDtRefDe 	 := DtoS(dDataBase)
	Local cDtRefAte	 := DtoS(dDataBase)
	Local cCliDe	 := ""
	Local cCliAte	 := ""
	Local cLojaDe	 := ""
	Local cLojaAte	 := "" //Local cCodEmp     := ""

	Default nPagina    := 1
	Default nTamPagina := 10
	//FWLogMsg("DEBUG", /*cTransactionId*/, "DlpFaturamento - BuscaDetalhes", ;
		//    /*cCategory*/, /*cStep nStepLog */, /*cMsgId*/, "Inicio", /*nMensure*/, /*nElapseTime*/, /*aMessage*/)
	If nPagina == 0
		lExpResult := .T.
	EndIf

	cEmpAtu := IIF(!EMPTY(oFiltros["EMPRESA"]),oFiltros["EMPRESA"],cEmpAnt)
	//Especifica as propriedades do gráfico tipo velocímetro
	IF VALTYPE(IIF(!EMPTY(oFiltros["EMPRESA"]),oFiltros["EMPRESA"],cEmpAnt)) =="A"
		if len(oFiltros["EMPRESA"]) >0
			cCodEmp := oFiltros["EMPRESA"][1]
		endif
	ELSE
		cCodEmp := oFiltros["EMPRESA"]
	ENDIF

	IF VALTYPE(oFiltros["FILIAL"]) =="A"
		if len(oFiltros["FILIAL"]) >0
			cCodFil := oFiltros["FILIAL"][1]
		endif
	ELSE
		cCodFil := oFiltros["FILIAL"]
	ENDIF

	IF VALTYPE(oFiltros["PERIODO"]) =="A"
		if len(oFiltros["PERIODO"]) >0
			cTPData := oFiltros["PERIODO"][1]
		endif
	ELSE
		cTPData := oFiltros["PERIODO"]
	ENDIF

	cAnoMes := substr(dtos(ddatabase),1,6)

	if cCodEmp != cEmpAnt
		cEmpAnt := cCodEmp
		cFilAnt := cCodFil
		FWSM0Util():setSM0PositionBycFilAnt()
	endif

	// cCodFil  := cFilAnt
	// cCodFil  := cFilAnt
	IF VALTYPE(oFiltros["SEGMENTODE"]) =="A"
		cSegDe  := oFiltros["SEGMENTODE"]
	ELSE
		if !empty( oFiltros["SEGMENTODE"])
			cSegDe := oFiltros["SEGMENTODE"]
		else
			cSegDe  := ''
		ENDIF
	ENDIF
	IF VALTYPE(oFiltros["SEGMENTOATE"]) =="A"
		cSegAte := oFiltros["SEGMENTOATE"]
	ELSE
		if !empty( oFiltros["SEGMENTOATE"])
			cSegAte := oFiltros["SEGMENTOATE"]
		else
			cSegAte := 'ZZZZZZZZZ'
		ENDIF
	ENDIF

	IF cTPData == "D"
		cDtRefDe  := cToD(substr(oFiltros["CATEGORIA"],4,2) + "/" + substr(oFiltros["CATEGORIA"],1,2) + "/" + cValToChar(YEAR(DATE())))
		cDtRefAte := cToD(substr(oFiltros["CATEGORIA"],4,2) + "/" + substr(oFiltros["CATEGORIA"],1,2) + "/" + cValToChar(YEAR(DATE())))
	ELSEIF cTPData == 'M'
		cDtRefDe  := FirstDate(DATE())
		cDtRefAte := LastDate(DATE())
	ELSEif cTPData == "A"
		cDtRefDe  :=  FirstYDate(DATE())
		cDtRefAte :=  LastYDate(DATE())
	else
		IF VALTYPE(oFiltros["DTREFDE"]) =="A"
			if len(oFiltros["DTREFDE"]) >0
				cDtRefDe  :=  REPLACE(oFiltros["DTREFDE"][1], '-', '')
			endif
		ELSEIF VALTYPE(oFiltros["DTREFDE"]) <> "U"
			cDtRefDe  :=  REPLACE(oFiltros["DTREFDE"], '-', '')
		ENDIF
		IF VALTYPE(oFiltros["DTREFATE"]) =="A"
			if len(oFiltros["DTREFATE"]) >0
				cDtRefAte  :=  REPLACE(oFiltros["DTREFATE"][1], '-', '')
			endif
		ELSEIF VALTYPE(oFiltros["DTREFATE"]) <> "U"
			cDtRefAte  :=  REPLACE(oFiltros["DTREFATE"], '-', '')
		ENDIF
	ENDIF
	// cCliDe := Space(TamSx3('A1_COD')[1])
	// cCliAte := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))

	// cLojaDe := Space(TamSx3('A1_LOJA')[1])
	// cLojaAte := REPLICATE("Z",GETSX3CACHE("A1_LOJA","X3_TAMANHO"))
	IF cTpMeta == '1' //Weg

		cCliDe   := '000001'
		cCliAte  := '000001'

	ELSEIF cTpMeta == '2' //Novos Negocios

		cCliDe   := '000002'
		cCliAte  := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))

	ELSE

		cCliDe  :=  Space(TamSx3('A1_COD')[1])
		cCliAte := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))

	ENDIF

	cLojaDe := Space(TamSx3('A1_LOJA')[1])
	cLojaAte := REPLICATE("Z",GETSX3CACHE("A1_LOJA","X3_TAMANHO"))

	cSql := "EXEC STP_DELPI_FATURAMENTO_PRD_"+cEmpAtu+"_SEGMENTOS"
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALDE VARCHAR(2)
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALATE VARCHAR(2)
	cSql +=  valtosql(cSegDe   ) +" , "//@SEGMENTODE VARCHAR(15)
	cSql +=  valtosql(cSegAte  ) +" , "//@SEGMENTOATE VARCHAR(15)
	cSql +=  valtosql(cDtRefDe   ) +" , "//@EMISSAODE VARCHAR(8)
	cSql +=  valtosql(cDtRefAte  ) +" , "//@EMISSAOATE VARCHAR(8)
	cSql +=  valtosql(cCliDe  	) +" , "//@CLIENTEDE VARCHAR(6)
	cSql +=  valtosql(cCliAte   ) +" , "//@CLIENTEATE VARCHAR(6)
	cSql +=  valtosql(cLojaDe   ) +" , "//@LOJADE VARCHAR(2)
	cSql +=  valtosql(cLojaAte  ) +" , "//@LOJAATE VARCHAR(2)
	// IF cCodEmp == '01'
	// 	cSql +=  valtosql(' ') +" , " //@ESTOQUE
	// ELSE
	cSql +=  valtosql(' ') +" , " //@ESTOQUE
	// ENDIF
	cSql +=  valtosql('S') //@DUPLICATA

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cSql),cAliasQry,.F.,.F.)

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

		cNMCli :=alltrim(posicione("SA1",1, xfilial("SA1")+ (cAliasQry)->CLIENTE+(cAliasQry)->LOJA,"A1_NOME"))
		cNMCli := (cAliasQry)->CLIENTE+"-"+(cAliasQry)->LOJA+cNMCli
		// nStepLog++
		// aMessage := {}
		// aAdd(aMessage, {"Cliente", cNMCli})
		// FWLogMsg("DEBUG", /*cTransactionId*/, "DlpFaturamento - BuscaDetalhes", ;
			//     /*cCategory*/, nStepLog/*cStep  */, /*cMsgId*/ STRZERO(nStepLog,4) , "items", /*nMensure*/, /*nElapseTime*/,aMessage /*aMessage*/)

		oDados["items"][nPos]["FILIAL"]     := (cAliasQry)->FILIAL
		oDados["items"][nPos]["CLIENTE"]    := cNMCli
		oDados["items"][nPos]["EMISSAO"]    := PCPMonitorUtils():FormataData((cAliasQry)->EMISSAO, 5)

		oDados["items"][nPos]["COD"]        := (cAliasQry)->COD
		oDados["items"][nPos]["DESC"]       := (cAliasQry)->B1_DESC

		oDados["items"][nPos]["QTDNF"]      := (cAliasQry)->QTDNF
		oDados["items"][nPos]["QTDPRDVEN"]  := (cAliasQry)->QTDPRDVEN
		oDados["items"][nPos]["D2_QUANT"]   := (cAliasQry)->D2_QUANT
		oDados["items"][nPos]["D2_TOTAL"]   := (cAliasQry)->D2_TOTAL
		oDados["items"][nPos]["LIQDEV"]     := (cAliasQry)->LIQDEV *-1
		oDados["items"][nPos]["LIQUIVENDA"] := (cAliasQry)->LIQUIVENDA // + ((cAliasQry)->LIQDEV *-1)

		(cAliasQry)->(dbSkip())

		If !lExpResult .And. nPos >= nTamPagina
			Exit
		EndIf
	End
	oDados["hasNext"] := (cAliasQry)->(!Eof())
	(cAliasQry)->(dbCloseArea())
	cJsonDados := oDados:toJson()
	FreeObj(oDados)

Return cJsonDados//oDados:ToJson()

/*/{Protheus.doc} ValidaPropriedades
Valida os dados informados nas propriedades do Monitor
@type Method
@author douglas.heydt
@since 30/06/2023
@version P12.1.2310
@param  oFiltros, objeto json, Objeto json com os filtros para a consulta dos dados
@return aRetorno, array      , [1] logico - indica se os dados são válidos [2] caracter - mensagem de erro
/*/
Method ValidaPropriedades(oFiltros) Class DelpiSegmento
	Local aRetorno  := {.T.,""}

	PCPMonitorUtils():ValidaPropriedadeFilial(oFiltros["FILIAL"],aRetorno)


Return aRetorno


/*/{Protheus.doc} montaColun
Realiza a criação de objeto Json que define as colunas utilizadas na grid de detalhamento do monitor
@type Static Function
@author douglas.heydt
@since 30/06/2023
@version P12.1.2310
@param  lExpResult, logico, Indica se trata todas as colunas como visible
@return aColunas, array objetos, Contém as definições das colunas da grid do monitor
/*/
Static Function montaColun(lExpResult)
	Local aColunas   := {}
	Local nIndice    := 0

	cCPOX3:="F2_FILIAL"
	cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"FILIAL","Filial","string",.T.)
	//cCPOX3:="F2_EMISSAO"
	//cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'CLIENTE','Cliente',"string",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'EMISSAO','Emissao de',"string",.T.)

	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'COD','Cod.Produto',"string",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'DESC','Desc.Produto',"string",.T.)

	// PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'DT_ATE','Emissao Ate',"date",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"QTDNF"/*cCPOX3*/,'Total Notas'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"QTDPRDVEN"/*cCPOX3*/,'Total Itens'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"D2_QUANT"/*cCPOX3*/,'Qtd Vendida'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"D2_TOTAL"  /*cCPOX3*/,'Valor Venda'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"LIQDEV"  /*cCPOX3*/,'Valor Devolucao R$'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"LIQUIVENDA"/*cCPOX3*/,'Valor Total R$'/*cTitX3*/,"number",.T.)

Return aColunas
