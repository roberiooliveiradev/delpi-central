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


/*/{Protheus.doc} StatusPedCompras3
Classe para prover os dados do Monitor de Status dos Lotes  a vencer
@type Class
@author douglas.heydt
@since 12/04/2023
@version P12.1.2310
@return Nil
/*/
Class StatusPedCompras3 FROM LongNameClass
	Static Method BuscaDados(oFiltros, cTipo, cSubTipo)
	Static Method BuscaDetalhes(oFiltro,nPagina)
	Static Method CargaMonitor()
	Static Method ValidaPropriedades(oFiltros)
EndClass

/*/{Protheus.doc} CargaMonitor
Realiza a carga do Monitor padrão na base de dados
@type Method
@author douglas.heydt
@since 12/04/2023
@version P12.1.2310
@return lRet, logico, Indica se conseguiu realizar a carga
/*/
Method CargaMonitor() Class StatusPedCompras3
	Local lRet      := .T.
	Local nIndLinha := 0
	Local nIndTag   := 0
	Local oCarga    := PCPMonitorCarga():New()
	Local oExemplo  := JsonObject():New()
	Local oStyle    := JsonObject():New()
	Local oStyleQtd := JsonObject():New()
	Local oPrmAdc   := JsonObject():New()

	If !PCPMonitorCarga():monitorAtualizado("StatusPedCompras3")
		oExemplo["corFundo"]  := COR_VERDE_FORTE
		oExemplo["corTitulo"] := "white"
		oExemplo["tags"]      := {}
		oExemplo["linhas"]    := {}
		oStyle["color"] := "white"

		PCPMonitorUtils():AdicionaTagMonitor(oExemplo["tags"],@nIndTag,"po-icon-calendar","01/01/23 - 15/01/23")
		PCPMonitorUtils():AdicionaTagMonitor(oExemplo["tags"],@nIndTag,"po-icon-bar-code","GUIL01")

		oStyleQtd["font-weight"] := "bold"
		oStyleQtd["font-size"]   := "120px"
		oStyleQtd["line-height"] := "130px"
		oStyleQtd["text-align"]  := "center"
		oStyleQtd["color"]       := oStyle["color"]
		PCPMonitorUtils():AdicionaLinhaInformacao(oExemplo["linhas"],@nIndLinha,"15","po-sm-12",oStyleQtd:ToJson())
		PCPMonitorUtils():AdicionaLinhaInformacao(oExemplo["linhas"],@nIndLinha,"1350 Kg","po-font-title po-text-center po-sm-12 po-pt-1 bold-text",oStyle:ToJson())

		oCarga:setaTitulo("STR0110") //"Lotes a vencer"
		oCarga:setaObjetivo("STR0111") //"Apresentar o número de lotes e a quantidade a vencer de um determinado produto, dentro de um período futuro configurado, utilizando o conceito de semáforo para indicar o nível de atenção ou urgência."
		oCarga:setaAgrupador("STR0112") //"Estoque"
		oCarga:setaFuncaoNegocio("StatusPedCompras3")
		oCarga:setaTiposPermitidos("chart;info")
		oCarga:setaTiposGraficoPermitidos("gauge")
		oCarga:setaTipoPadrao("info")
		oCarga:setaTipoGraficoPadrao("")
		oCarga:setaTipoDetalhe("detalhe")
		oCarga:setaExemploJsonTexto(.F.,oExemplo)

		oPrmAdc["04_TIPOSEMAFORO"]           := JsonObject():New()
		oPrmAdc["04_TIPOSEMAFORO"]["opcoes"] := "STR0182"+":L;"+"STR0183"+":Q" //"Número de Lotes //Quantidade do Produto
		oCarga:setaPropriedadeFilial("02_FILIAL")
		oCarga:setaPropriedadeProduto("02_B8_PRODUTO")
		oCarga:setaPropriedade("03_SEMAFORO", "STR0175", "STR0176",1,30,0,"po-lg-8 po-xl-8 po-md-8 po-sm-12",/*oEstilos*/,/*cIcone*/,/*oPrmAdc*/) //"Atenção;Urgente (Lotes/Quantidade)" //"Semáforo (Lotes/Quantidade)"
		oCarga:setaPropriedade("04_TIPOSEMAFORO","L", "STR0113",4,/*cTamanho*/,/*cDecimal*/,"po-lg-4 po-xl-4 po-md-4 po-sm-12",/*oEstilos*/,/*cIcone*/,oPrmAdc["04_TIPOSEMAFORO"]) //"Lotes/Quantidade"
		oCarga:setaPropriedadePeriodoAtual("05_TIPOPERIODO","D","06_PERIODO")
		If !oCarga:gravaMonitorPropriedades()
			lRet := .F.
		EndIf
		oCarga:Destroy()
	EndIf
	FreeObj(oExemplo)
	FreeObj(oStyle)
	FreeObj(oPrmAdc)
	FreeObj(oStyleQtd)
Return lRet

/*/{Protheus.doc} BuscaDados
Responsável por realizar a busca dos dados que serão exibidos no monitor (gráfico ou texto)

@type Class
@author douglas.heydt
@since 09/02/2023
@version P12.1.2310
@param	oFiltros  , objeto Json, Contém as propriedades do monitor usadas para filtrar a query de busca
@param	cTipo     , caracter   , Tipo chart/info
@param	cSubTipo  , caracter   , Tipo de grafico pie/bar/column
@return cJsonDados, caracter   , Retorna um novo Json em formato texto, pronto para conversão e exibição no front
/*/
Method BuscaDados(oFiltros, cTipo, cSubTipo) Class StatusPedCompras3
	Local aSemaforo  := {C7_DATPRF}//StrTokArr(Replace(oFiltros["03_SEMAFORO"],",","."),";")
	Local cAliasQry  := GetNextAlias()
	Local cJsonDados := ""
	Local cQuery     := ""
	Local nLotes     := 0
	Local nPos       := 0
	Local cTipSem 	 := "L"
	Local oJsonRet   := JsonObject():New()

	oFiltros["02_FILIAL"] := PadR(oFiltros["02_FILIAL"], FWSizeFilial())

	cQuery += " SELECT "
	cQuery += " COUNT(*) AS NUMPED"
	cQuery += " FROM "+RetSqlName("SC7")+" SC7 "
	cQuery += " WHERE "
	cQuery += " SC7.C7_DATPRF BETWEEN '"+PCPMonitorUtils():FormataData(oFiltros["03_DATAINI"], 2)+"' AND  '"+PCPMonitorUtils():FormataData(oFiltros["04_DATAFIM"], 2)+"' "
	cQuery += " AND SC7.C7_FILIAL = '" + xFilial("SC7",oFiltros["02_FILIAL"]) + "' "
	cQuery += " AND SC7.C7_DINICOM > '"+DTOS(date() )+"' "
	cQuery += " AND SC7.C7_DINICOM <= '"+DTOS((DaySum(date(), 8)))+"' "
	cQuery += " AND C7_QUANT-C7_QUJE > 0  "
	cQuery += " AND C7_RESIDUO = '' "
	cQuery += " AND SC7.D_E_L_E_T_  = ' ' "

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasQry,.F.,.F.)
	If (cAliasQry)->(!Eof())

		nLotes     := (cAliasQry)->NUMPED

	End
	(cAliasQry)->(dbCloseArea())

	aadd(aSemaforo,"5")
	aadd(aSemaforo,"5")

	montaInfo(oJsonRet,nLotes,aSemaforo,cTipSem)

	oJsonRet["tags"]     := {}
	// PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-calendar",PCPMonitorUtils():FormataData(oFiltros["03_DATAINI"], 3) + " - " + PCPMonitorUtils():FormataData(oFiltros["04_DATAFIM"], 3))
	// PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-bar-code","cCodProd")
	If cTipo == "info" .And. cTipSem == "Q"
		PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-weight","STR0180" +": ") //"Un. Medida"
	EndIf
	If cTipo == "chart"
		PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-star-filled",IIF(cTipSem == "L",cValToChar(nLotes) + " " ,cValToChar(nLotes) + IIF(nLotes > 1, " "+"STR0178", " "+"STR0177"))) //"Lotes" //"Lote"
	EndIf
	cJsonDados :=  oJsonRet:toJson()

	FwFreeArray(aSemaforo)
	FreeObj(oJsonRet)
Return cJsonDados

/*/{Protheus.doc} ValidaPropriedades
Valida os dados informados nas propriedades do Monitor
@type Method
@author douglas.heydt
@since 12/04/2023
@version P12.1.2310
@param  oFiltros, objeto json, Objeto json com os filtros para a consulta dos dados
@return aRetorno, array      , [1] logico - indica se os dados são válidos [2] caracter - mensagem de erro
/*/
Method ValidaPropriedades(oFiltros) Class StatusPedCompras3
	Local aRetorno  := {.T.,""}
	Local aSemaforo := {}
	// Local nX        := 1

	PCPMonitorUtils():ValidaPropriedadeFilial(oFiltros["02_FILIAL"],aRetorno)

	If aRetorno[1] .And. oFiltros["05_TIPOPERIODO"] == "X"
		If !oFiltros:HasProperty("06_PERIODO") .Or. oFiltros["06_PERIODO"] == Nil .Or. Empty(oFiltros["06_PERIODO"])
			aRetorno[1] := .F.
			aRetorno[2] := "STR0069" //"Deve ser informada a quantidade de dias para o período personalizado."
		EndIf
	EndIf

	FwFreeArray(aSemaforo)
Return aRetorno

/*/{Protheus.doc} BuscaDetalhes
Realiza a busca dos dados para montar os detalhes do Monitor
@type Method
@author douglas.heydt
@since 12/04/2023
@version P12.1.2310
@return Nil
/*/
Method BuscaDetalhes(oFiltro,nPagina) Class StatusPedCompras3
	Local cAlias     := GetNextAlias()
	Local cQuery     := ""
	// Local dDataFim   := PCPMonitorUtils():RetornaPeriodoFinal(AllTrim(oFiltro["05_TIPOPERIODO"]),ddatabase,cValToChar(oFiltro["06_PERIODO"]))
	Local lExpResult := .F.
	// Local nIndTag    := 0
	Local nPos       := 0
	Local nStart     := 1
	Local nTamPagina := 20
	Local oDados     := JsonObject():New()

	Default nPagina := 1

	If nPagina == 0
		lExpResult := .T.
	EndIf

	oFiltro["02_FILIAL"] := PadR(oFiltro["02_FILIAL"], FWSizeFilial())
	oDados["items"]        := {}
	oDados["columns"]      := montaColun(lExpResult)
	oDados["canExportCSV"] := .T.
	oDados["tags"]         := {}

	cQuery := " SELECT "
	cQuery += " C7_NUM ,C7_PRODUTO, C7_DESCRI, C7_QUANT, C7_PRECO, C7_OBS, C7_FORNECE, C7_LOJA, C7_DATPRF, A2_NOME "
	cQuery += " FROM "+RetSqlName("SC7")+" SC7 "
	cQuery += " LEFT JOIN "+RetSqlName("SA2")+" SA2 "
	cQuery += " ON SA2.A2_FILIAL = '" + xFilial("SA2") + "' "
	cQuery += " AND SA2.A2_COD = SC7.C7_FORNECE "
	cQuery += " AND SA2.A2_LOJA = SC7.C7_LOJA "
	cQuery += " AND SA2.D_E_L_E_T_ = ' ' "
	cQuery += " WHERE "
	cQuery += " SC7.C7_DATPRF BETWEEN '"+PCPMonitorUtils():FormataData(oFiltro["03_DATAINI"], 2)+"' AND  '"+PCPMonitorUtils():FormataData(oFiltro["04_DATAFIM"], 2)+"' "
	cQuery += " AND SC7.C7_FILIAL = '" + xFilial("SC7",oFiltro["02_FILIAL"]) + "' "
	cQuery += " AND SC7.C7_DINICOM > '"+DTOS(date() )+"' "
	cQuery += " AND SC7.C7_DINICOM <= '"+DTOS((DaySum(date(), 8)))+"' "
	cQuery += " AND SC7.D_E_L_E_T_  = ' ' "
	cQuery += " AND C7_QUANT-C7_QUJE > 0  "
	cQuery += " AND C7_RESIDUO = '' "
	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAlias,.F.,.F.)

	If nPagina > 1
		nStart := ( (nPagina-1) * nTamPagina )
		If nStart > 0
			(cAlias)->(DbSkip(nStart))
		EndIf
	EndIf

	While (cAlias)->(!Eof())
		aAdd(oDados["items"], JsonObject():New())
		nPos++
		oDados["items"][nPos]["C7_NUM"  ] := (cAlias)->C7_NUM
		oDados["items"][nPos]["C7_PRODUTO" ] := (cAlias)->C7_PRODUTO
		oDados["items"][nPos]["C7_DESCRI" ] := (cAlias)->C7_DESCRI
		oDados["items"][nPos]["C7_QUANT" ] := IIF(!EMPTY(STR((cAlias)->C7_QUANT)),STR((cAlias)->C7_QUANT),"0")
		oDados["items"][nPos]["C7_PRECO"    ] := IIF(!EMPTY(STR((cAlias)->C7_PRECO)),STR((cAlias)->C7_PRECO),"0")
		oDados["items"][nPos]["C7_OBS"  ] := (cAlias)->C7_OBS
		oDados["items"][nPos]["C7_FORNECE"      ] := (cAlias)->C7_FORNECE
		oDados["items"][nPos]["C7_LOJA"   ] := (cAlias)->C7_LOJA
		oDados["items"][nPos]["A2_NOME"   ] := (cAlias)->A2_NOME
		oDados["items"][nPos]["C7_DATPRF" ] := PCPMonitorUtils():FormataData((cAlias)->C7_DATPRF, 3)
		(cAlias)->(dbSkip())
		If !lExpResult .And. nPos >= nTamPagina
			Exit
		EndIf
	End
	oDados["hasNext"] := (cAlias)->(!Eof())
	(cAlias)->(dbCloseArea())
Return oDados:ToJson()

/*/{Protheus.doc} montaColun
Realiza a criação de objeto Json que define as colunas utilizadas na grid de detalhamento do monitor
@type Static Function
@author douglas.heydt
@since 13/04/2023
@version P12.1.2310
@return aColumns, array objetos, Contém as definições das colunas da grid do monitor
/*/
Static Function montaColun(lExpResult)
	Local aColunas := {}
	Local nIndice  := 0

	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_NUM","Num.Pedido","string",.T.) //"Filial"
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_PRODUTO","Produto","string",.T.) //"Lote"
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_DESCRI","Desc.Prod.","string",.T.) //"Sub-Lote"
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_QUANT","Quantidade","string",.T.) //"Produto"
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_PRECO","Preco","string",.T.) //"Desc. Produto"
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_OBS","Observacao","string",.T.) //"Armazém"
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_FORNECE","Fornecedor","string",.T.) //"Validade"
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_LOJA","Loja","string",.T.) //"Quant. Orig."
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"A2_NOME","Nome","string",.T.) //"Quant. Orig."
	PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"C7_DATPRF","Emissao","string",.T.) //"Saldo"

Return aColunas

/*/{Protheus.doc} retCorSmf
Retorna a cor do semáforo de acordo com a quantidade parametrizada
@type Static Function
@author douglas.heydt
@since 13/04/2023
@version P12.1.2310
@param  nQuant    , numerico, Quantidade de lotes ou de unidades
@param  nValSemaf1, numerico, Número do semáforo relacionado a atenção
@param  nValSemaf2, numerico, Número do semáforo relacionado ao urgente
@return cCorSemaf , caracter, String com código RGB da cor
/*/
Static Function retCorSmf(nQuant,nValSemaf1,nValSemaf2)
	If nValSemaf1 == 5
		Return COR_VERDE_FORTE
	ElseIf nValSemaf2 == 3
		Return COR_AMARELO_ESCURO
	EndIf
Return COR_VERMELHO_FORTE

/*/{Protheus.doc} montaGraf
Monta objeto json com os dados para mostrar o gauge
@type Static Function
@author renan.roeder
@since 01/06/2023
@version P12.1.2310
@param  oJsonRet  , objeto json, Objeto json que receberá os dados do gauge
@param  nLotes    , numerico   , Número de lotes retornado da consulta
@param  nSaldo    , numerico   , Saldo dos lotes retornados na consulta
@param  aSemaforo , array      , Array com os números do semáforo
@param  cTipoSemaf, caracter   , L - Quantidade Lotes / Q - Saldo Lotes
@param  cProduto  , caracter   , Codigo do produto
@param  cUnMedida , caracter   , Unidade de medida do produto
@return Nil
/*/
Static Function montaGraf(oJsonRet,nLotes,nSaldo,aSemaforo,cTipoSemaf,cProduto,cUnMedida)
	Local cLabel     := ""
	Local cValorFim  := ""
	Local cValSemaf1 := aSemaforo[1]
	Local cValSemaf2 := aSemaforo[2]
	Local nQuant     := 0
	Local nValorFim  := 0
	Local nValSemaf1 := Val(cValSemaf1)
	Local nValSemaf2 := Val(cValSemaf2)
	Local oGauge     := PCPMonitorGauge():New()

	If cTipoSemaf == "L"
		nQuant  := nLotes
		cLabel  := IIF(nLotes > 1, "STR0178", "STR0177") //"Lotes" //"Lote"
	Else
		nQuant  := nSaldo
		cLabel  := cUnMedida
	EndIf
	If nQuant > nValSemaf2
		nValorFim := nQuant + (nValSemaf2 - nValSemaf1)
	Else
		nValorFim := nValSemaf2 + (nValSemaf2 - nValSemaf1)
	EndIf
	cValorFim := cValToChar(nValorFim)

	oJsonRet["alturaMinimaWidget"] := "350px"
	oJsonRet["alturaMaximaWidget"] := "500px"
	oJsonRet["categorias"] := {}
	oJsonRet["series"]     := {}
	oJsonRet["detalhes"]   := {}
	oGauge:SetMaxValue(nValorFim)
	oGauge:SetValue(nQuant)
	oGauge:SetValueStyle("color",retCorSmf(nQuant,nValSemaf1,nValSemaf2))
	oGauge:SetValueStyle("font-weight","bold")
	oGauge:SetLabel(cLabel)
	oGauge:SetLabelStyle("font-weight","bold")
	oGauge:SetThreshold("0",COR_VERDE_FORTE)
	oGauge:SetThreshold(cValSemaf1,COR_AMARELO_QUEIMADO)
	oGauge:SetThreshold(cValSemaf2,COR_VERMELHO_FORTE)
	If Val(cValSemaf1) > 0
		oGauge:SetMarker("0")
	Endif
	oGauge:SetMarker(cValSemaf1)
	oGauge:SetMarker(cValSemaf2)
	oGauge:SetMarker(cValorFim)
	oJsonRet["gauge"]      := oGauge:GetJsonObject()
	FreeObj(oGauge)
Return

/*/{Protheus.doc} montaInfo
Monta objeto json com os dados para mostrar o gráfico de informações
@type Static Function
@author renan.roeder
@since 01/06/2023
@version P12.1.2310
@param  oJsonRet  , objeto json, Objeto json que receberá os dados do gauge
@param  nLotes    , numerico   , Número de lotes retornado da consulta
@param  nSaldo    , numerico   , Saldo dos lotes retornados na consulta
@param  aSemaforo , array      , Array com os números do semáforo
@param  cTipoSemaf, caracter   , L - Quantidade Lotes / Q - Saldo Lotes
@param  cProduto  , caracter   , Codigo do produto
@param  cUnMedida , caracter   , Unidade de medida do produto
@return Nil
/*/
Static Function montaInfo(oJsonRet,nLotes,aSemaforo,cTipoSemaf)
	Local cTxtPrc    := ""
	Local cTxtSec    := ""
	Local nIndLinha  := 0
	Local nQuant     := 0
	Local nValSemaf1 := Val(aSemaforo[1])
	Local nValSemaf2 := Val(aSemaforo[2])
	Local oStyle     := JsonObject():New()
	Local oStyleQtd  := JsonObject():New()

	oJsonRet["corTitulo"] := "white"
	oStyle["color"] := "white"
	oJsonRet["alturaMinimaWidget"] := "350px"
	oJsonRet["alturaMaximaWidget"] := "500px"
	oJsonRet["linhas"] := {}

	IF aSemaforo[1] == "1"

		cTxtSec := "Atrasado"

	Elseif aSemaforo[1] == "3"

		cTxtSec := "Vence Hoje"

	Else

		cTxtSec := "Próximos Dias"

	Endif

	If cTipoSemaf == "L"
		nQuant  := nLotes
		cTxtPrc := cValToChar(nLotes)

	Else
		nQuant  := nLotes
		cTxtPrc := cValToChar(nLotes)

	EndIf
	If nLotes > 0
		oJSonRet["corFundo"] := retCorSmf(nQuant,nValSemaf1,nValSemaf2)

		If oJSonRet["corFundo"] == COR_AMARELO_ESCURO
			oStyle["color"]       := "white"
			oJsonRet["corTitulo"] := "white"
		EndIf
		oStyleQtd["font-weight"] := "bold"
		oStyleQtd["font-size"]   := "120px"
		oStyleQtd["line-height"] := "130px"
		oStyleQtd["text-align"]  := "center"
		oStyleQtd["color"]       := oStyle["color"]
		oStyleQtd["cursor"]      := "pointer"
		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTxtPrc,"po-sm-12",oStyleQtd:ToJson(),.T.)
		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTxtSec,"po-font-title po-text-center po-sm-12 po-pt-1 bold-text",oStyle:ToJson())
	Else
		oJSonRet["corFundo"] := retCorSmf(nQuant,nValSemaf1,nValSemaf2)

		If oJSonRet["corFundo"] == COR_VERDE_FORTE
			oStyle["color"]       := "white"
			oJsonRet["corTitulo"] := "white"
		EndIf
		oStyleQtd["font-weight"] := "bold"
		oStyleQtd["font-size"]   := "120px"
		oStyleQtd["line-height"] := "130px"
		oStyleQtd["text-align"]  := "center"
		oStyleQtd["color"]       := oStyle["color"]
		oStyleQtd["cursor"]      := "pointer"
		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"0","po-sm-12",oStyleQtd:ToJson(),.T.)
		PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTxtSec,"po-font-title po-text-center po-sm-12 po-pt-1 bold-text",oStyle:ToJson())

	EndIf
Return
