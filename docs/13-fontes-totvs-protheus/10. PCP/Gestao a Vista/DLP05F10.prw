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

/*/{Protheus.doc} DelpiFatDiario
Classe para prover os dados do Monitor de Ordens de Produção atrasadas, de acordo com sua previsão de entrega
@type Class
@author douglas.heydt
@since 30/06/2023
@version P12.1.2310
@return Nil
/*/
Class DelpiFatDiario FROM LongNameClass
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
Method BuscaDados(oFiltros, cTipo, cSubTipo) Class DelpiFatDiario
	Local aSaldos    := {}
	Local aSaldos2   := {}
	Local aPeriodos  := PCPMonitorUtils():RetornaListaPeriodosPassado(oFiltros["03_TIPOPERIODO"],cValToChar(oFiltros["04_PERIODO"]))
	Local aChaves    := {}
	Local aChaves2  := {}
	Local cAliasQry  := GetNextAlias()
	Local cAliasSZC  := GetNextAlias()
	Local cJsonDados := ""
	Local cUnMed     := ""
	Local cQuery     := ""
	Local cEmpAtu	 := ""
	Local dDataAjust := Nil
	Local dDataIni   := dDatabase
	Local dDataFin   := dDatabase
	Local dDiaEspe	 := Date()
	Local nOPsTotal  := 0
	Local nQtPTotal  := 0
	Local nPosTag    := 0
	Local nX         := 0
	Local nDias 		:= 0
	Local cPeriod 	:= 0
	Local nIndSerie := 0
	Local cFilFil   := ""
	Local cSql := ""
	Local cQrySzc := ""
	Local nMeta := ""
	Local oJsonRet   := JsonObject():New()
	Local oPeriods   := JsonObject():New()
	Local oMetas		 := JsonObject():New()

	Local cTpMeta 	 := "1"
	Local cTPData    := ""
	Local cCodFil 	 := cFilAnt
	Local cProdDe 	 := ""
	Local cProdAte 	 := ""
	Local cDtRefDe 	 := DtoS(dDataBase)
	Local cDtRefAte	 := DtoS(dDataBase)
	Local cCliDe	 := ""
	Local cCliAte	 := ""
	Local cLojaDe	 := ""
	Local cLojaAte	 := ""
	Local nPerMeta
	Local nVlrMeta

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

	IF cPeriod == "D"

		nDias := 1

	ELSEIF cPeriod == "M"

		nDias := 30

	ELSE

		nDias := 365

	EndIf

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

	cAnoMes := substr(dtos(ddatabase),1,6)
	if cCodEmp != cEmpAnt
		cEmpAnt := cCodEmp
		cFilAnt := cCodFil
		FWSM0Util():setSM0PositionBycFilAnt()
	endif

	// cCodFil  := cFilAnt
	// cCodFil  := cFilAnt
	cProdDe  := Space(TamSx3('B1_COD')[1])
	cProdAte := REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO"))
	if cTPData == 'M'
		cDtRefDe  := FirstDate(DATE())
		cDtRefAte := LastDate(DATE())
	ELSEif cTPData == "A"
		cDtRefDe  :=  FirstYDate(DATE())
		cDtRefAte :=  LastYDate(DATE())
	ELSEif cTPData == "D"
		cDtRefDe  :=  DATE()
		cDtRefAte :=  DATE()
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

	cSql := "EXEC STP_DELPI_FATURAMENTO_"+cEmpAtu+"_GESTAO"
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALDE VARCHAR(2)
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALATE VARCHAR(2)
	cSql +=  valtosql(cProdDe   ) +" , "//@PRODUTODE VARCHAR(15)
	cSql +=  valtosql(cProdAte  ) +" , "//@PRODUTOATE VARCHAR(15)
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
	cSql +=  valtosql('S') //@DUPLICATA
	CONOUT(cSql)
	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cSql),cAliasQry,.F.,.F.)
	nVlrFat :=  0.00
	nVlrFatT := 0.00
	WHILE  (cAliasQry)->(!Eof())

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
		dLastDm :=   LastDate(	stod((cAliasQry)->EMISSAO)	)  //ultimo dia do mes

		nQtDUtil:= DateWorkDay(dFirstDm,dLastDm,lSaturday,lSunday ,lHoliday ) //DateWorkDay - retorna os dias uteis com base na data

		dDataAjust := Day2Str(stod((cAliasQry)->EMISSAO))//dToC(PCPMonitorUtils():RetornaPeriodoInicial(nQtDUtil,sToD((cAliasQry)->EMISSAO)))
		nVlrFat :=   (cAliasQry)->LIQUIVENDA
		nVlrFat +=   (cAliasQry)->LIQDEV*-1
		nVlrFatT +=nVlrFat
		// nPerMeta := round((nVlrFat /nMeta )*100,2)

		cQuery := "SELECT sum(ZC_ORCFAT) ZC_ORCFAT  " + CRLF
		cQuery += "FROM "+RETSQLNAME('SZC')+"  (NOLOCK) SZC   " + CRLF
		cQuery += "WHERE SZC.D_E_L_E_T_ = ''  " + CRLF
		cQuery += "AND ZC_FILIAL =  ' ' "+ CRLF
		cQuery += "AND ZC_FIL    =  "+VALTOSQL(cCodFil) + CRLF
		cQuery += "AND ZC_EMP    =  "+VALTOSQL(cCodEmp) + CRLF

		if cTpMeta != '0'

			cQuery += "AND ZC_TIPO   =  "+VALTOSQL(cTpMeta) + CRLF
		endif
		if cTPData == 'M'
			cQuery += "AND ZC_ANOMES =  "+VALTOSQL(cAnoMes) + CRLF
		else

			cQuery += "AND substring(ZC_ANOMES,1,4) =  "+VALTOSQL(substr(cAnoMes,1,4)) + CRLF
		endif
		conout(cQuery)
		dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSZC,.F.,.F.)


		if  (cAliasSZC)->(!Eof())
			nVlrMeta :=   (cAliasSZC)->ZC_ORCFAT
		endif

		//IF cTPData == 'D' .AND. !EMPTY(oFiltros["METADIA"])
		//	nVlrMeta := oFiltros["METADIA"]
		//ENDIF

		(cAliasSZC)->(dbCloseArea())
		//if cTPData == 'M' .or. cTPData == 'D'
		//	cEmisDe  := FirstDate(DATE())
		//	cEmisAte := LastDate(DATE())
		//ELSEif  cTPData == 'A'
		//	cEmisDe  :=  FirstYDate(DATE())
		//	cEmisAte :=  LastYDate(DATE())
		//ELSE
		//	cEmisDe  :=  FirstYDate(DATE())
		//	cEmisAte :=  LastYDate(DATE())

		//ENDIF

		// //nValorFim := 25000 //Valor Maximo da Meta
		// nPerMeta := round((nVlrFat /nVlrMeta )*100,2)
		lSaturday  := .F.
		lSunday    := .F.
		lHoliday   := .F.

		nRetMes := DateWorkDay(cDtRefDe,cDtRefAte,lSaturday,lSunday ,lHoliday )
		//nRetAtu := DateWorkDay(cDtRefDe,date(),lSaturday,lSunday ,lHoliday )
		//nVlrPrev :=( (nVlrFat/nRetAtu)*nRetMes)
		nVlrPrev :=round( (nVlrMeta/nRetMes),4)
		conout("nVlrPrev "+cvaltochar(nVlrPrev))
		conout("nVlrFat "+cvaltochar(nVlrFat))
		If oPeriods:HasProperty(dDataAjust)
			//	// oPeriods[dDataAjust] += (cAliasQry)->LIQUIVENDA
			oPeriods[dDataAjust] += nVlrFat//nPerMeta
		Else
			oPeriods[dDataAjust] := nVlrFat//nPerMeta
			/// oPeriods[dDataAjust] := (cAliasQry)->LIQUIVENDA
		EndIf

		//If oMetas:HasProperty(dDataAjust)
		//	oMetas[dDataAjust] += nVlrMeta
		//Else
		oMetas[dDataAjust] := nVlrPrev
		//	EndIf

		// ENDIF

		(cAliasQry)->(dbSkip())

	ENDDO

	(cAliasQry)->(dbCloseArea())

	aChaves := oPeriods:GetNames()

	For nX := 1 To Len(aChaves)
		aAdd(aSaldos, oPeriods[aChaves[nX]])
	Next nX

	aChaves2 := oMetas:GetNames()

	For nX := 1 To Len(aChaves2)
		aAdd(aSaldos2, oMetas[aChaves2[nX]])
	Next nX

	aAdd(oJsonRet["series"], JsonObject():New())
	// oJsonRet["series"][1]["color"]   := COR_AZUL
	// oJsonRet["series"][1]["data"]    := aSaldos
	// oJsonRet["series"][1]["label"]   := "FATURAMENTO(R$)"//cUnMed

	aAdd(oJsonRet["series"], JsonObject():New())

	IF cPeriod == "D"
		cToPer := "Diario"
	ELSEIF cPeriod == "M"
		cToPer := "Mensal"
	ELSEIF cPeriod == "A"
		cToPer := "Anual"
	ELSE
		cToPer := "Personalizado"
	ENDIF
	if cTpMeta=='1'
		cDscMeta := "WEG"
	elseif cTpMeta=='2'
		cDscMeta := "Novos Negocios"
	else
		cDscMeta := "Ambas"
	endif
	oJsonRet["categorias"] := aChaves
	cVlrFat:= Transform(	nVlrFatT , X3Picture("E1_VALOR"))
	cVlrMeta:= Transform(	nVlrPrev , X3Picture("E1_VALOR"))
	PCPMonitorUtils():AdicionaSerieGraficoMonitor(oJsonRet["series"],@nIndSerie,COR_AZUL,aSaldos,"FATURAMENTO(R$) "+cVlrFat) //"Produção"
	PCPMonitorUtils():AdicionaSerieGraficoMonitor(oJsonRet["series"],@nIndSerie,COR_VERMELHO,aSaldos2,"META(R$) "+cVlrMeta) //"Pausa"
	PCPMonitorUtils():AdicionaCategoriasGraficoMonitor(oJsonRet["categorias"], aChaves)


	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"po-icon-calendar",dToC(cDtRefDe) + " - " + dToC(cDtRefAte))
	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"ph-calendar-check",cToPer/*PCPMonitorUtils():RetornaDescricaoTipoPeriodo(oFiltros["03_TIPOPERIODO"])*/)
	PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"po-icon-parameters",cDscMeta)
	// PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"po-icon-star-filled",cValToChar(nOPsTotal) + IIF(nOPsTotal > 1," "+"STR0203"," "+"STR0189") ) //"Ordens"  "Ordem"
	// PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPosTag,"po-icon-star-filled",cValToChar(nQtPTotal) + " " + cUnMed )

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
Method BuscaDetalhes(oFiltros,nPagina) Class DelpiFatDiario
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
	Local cEmpAtu
	Local nStart     := 0
	Local oDados     := JsonObject():New()
	// Local cEol := chr(10)
	Local nStepLog := 0

	Local cTpMeta 	 := "1"
	Local cTPData    := ""
	Local cCodFil 	 := cFilAnt
	Local cProdDe 	 := ""
	Local cProdAte 	 := ""
	Local cDtRefDe 	 := DtoS(dDataBase)
	Local cDtRefAte	 := DtoS(dDataBase)
	Local cCliDe	 := ""
	Local cCliAte	 := ""
	Local cLojaDe	 := ""
	Local cLojaAte	 := ""

	Default nPagina    := 1
	Default nTamPagina := 10
	//FWLogMsg("DEBUG", /*cTransactionId*/, "DlpFaturamento - BuscaDetalhes", ;
	//    /*cCategory*/, /*cStep nStepLog */, /*cMsgId*/, "Inicio", /*nMensure*/, /*nElapseTime*/, /*aMessage*/)
	If nPagina == 0
		lExpResult := .T.
	EndIf

	cEmpAtu := IIF(!EMPTY(oFiltros["EMPRESA"]),oFiltros["EMPRESA"],cEmpAnt)
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

	cAnoMes := substr(dtos(ddatabase),1,6)
	if cCodEmp != cEmpAnt
		cEmpAnt := cCodEmp
		cFilAnt := cCodFil
		FWSM0Util():setSM0PositionBycFilAnt()
	endif

	// cCodFil  := cFilAnt
	// cCodFil  := cFilAnt
	cProdDe  := Space(TamSx3('B1_COD')[1])
	cProdAte := REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO"))
	if cTPData == 'M'
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
		ELSE
			cDtRefDe  :=  REPLACE(oFiltros["DTREFDE"], '-', '')
		ENDIF
		IF VALTYPE(oFiltros["DTREFATE"]) =="A"
			if len(oFiltros["DTREFATE"]) >0
				cDtRefAte  :=  REPLACE(oFiltros["DTREFATE"][1], '-', '')
			endif
		ELSE
			cDtRefAte  :=  REPLACE(oFiltros["DTREFATE"], '-', '')
		ENDIF
	ENDIF
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

	cSql := "EXEC STP_DELPI_FATURAMENTO_"+cEmpAtu+"_GESTAO"
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALDE VARCHAR(2)
	cSql +=  valtosql(cCodFil   ) +" , "//@FILIALATE VARCHAR(2)
	cSql +=  valtosql(cProdDe   ) +" , "//@PRODUTODE VARCHAR(15)
	cSql +=  valtosql(cProdAte  ) +" , "//@PRODUTOATE VARCHAR(15)
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
	cSql +=  valtosql('S') //@DUPLICATA
	// nStepLog++
	// aMessage := {}
	// aAdd(aMessage, {"Query", cSql})
	// FWLogMsg("DEBUG", /*cTransactionId*/, "DlpFaturamento - BuscaDetalhes", ;
	//     /*cCategory*/, nStepLog/*cStep  */, /*cMsgId*/ STRZERO(nStepLog,4) , "Query", /*nMensure*/, /*nElapseTime*/,aMessage /*aMessage*/)
	//conout(cSql)
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

		oDados["items"][nPos]["FILIAL"]  := (cAliasQry)->FILIAL
		oDados["items"][nPos]["CLIENTE"]    := cNMCli
		oDados["items"][nPos]["EMISSAO"]       := PCPMonitorUtils():FormataData((cAliasQry)->EMISSAO, 5)
		// oDados["items"][nPos]["DT_ATE"]      := PCPMonitorUtils():FormataData(dToS(cEmisAte), 5)
		oDados["items"][nPos]["QTDNF"]     :=(cAliasQry)->QTDNF
		oDados["items"][nPos]["QTDPRDVEN"]  :=(cAliasQry)->QTDPRDVEN
		oDados["items"][nPos]["D2_QUANT"]   :=(cAliasQry)->D2_QUANT
		oDados["items"][nPos]["D2_TOTAL"]     := (cAliasQry)->D2_TOTAL
		oDados["items"][nPos]["LIQDEV"]     := (cAliasQry)->LIQDEV *-1
		oDados["items"][nPos]["LIQUIVENDA"]     := (cAliasQry)->LIQUIVENDA // + ((cAliasQry)->LIQDEV *-1)


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
Method ValidaPropriedades(oFiltros) Class DelpiFatDiario
	Local aRetorno  := {.T.,""}

	PCPMonitorUtils():ValidaPropriedadeFilial(oFiltros["FILIAL"],aRetorno)

	// If aRetorno[1] .And. Empty(oFiltros["02_C2_PRODUTO"])
	// 	aRetorno[1] := .F.
	// 	aRetorno[2] := "STR0117" //"O produto deve ser informado."
	// EndIf

	// If aRetorno[1] .And. (!oFiltros:HasProperty("04_PERIODO") .Or. oFiltros["04_PERIODO"] == Nil .Or. Empty(oFiltros["04_PERIODO"]))
	// 	aRetorno[1] := .F.
	// 	aRetorno[2] := "STR0127" //"Deve ser informada a quantidade de períodos."
	// EndIf

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
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'EMISSAO','Emissao de',"date",.T.)
	// PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'DT_ATE','Emissao Ate',"date",.T.)

	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"QTDNF"/*cCPOX3*/,'Total Notas'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"QTDPRDVEN"/*cCPOX3*/,'Total Itens'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"D2_QUANT"/*cCPOX3*/,'Qtd Vendida'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"D2_TOTAL"  /*cCPOX3*/,'Valor Venda'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"LIQDEV"  /*cCPOX3*/,'Valor Devolucao R$'/*cTitX3*/,"number",.T.)
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"LIQUIVENDA"/*cCPOX3*/,'Valor Total R$'/*cTitX3*/,"number",.T.)

Return aColunas
