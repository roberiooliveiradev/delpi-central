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

Class DelpiEficienciaTXT FROM LongNameClass
	Static Method BuscaDados(oFiltros, cTipo, cSubTipo)
	Static Method BuscaDetalhes(oFiltros, nPagina)
	Static Method ValidaPropriedades(oFiltros)
EndClass

Method BuscaDados(oFiltros, cTipo, cSubTipo) Class DelpiEficienciaTXT
	// Local aSemaforo  := StrTokArr(Replace(oFiltros["03_SEMAFORO"],",","."),";")
	Local cAliasQry  := GetNextAlias()
	// Local cCodProd   := oFiltros["02_B8_PRODUTO"]
	Local cJsonDados := ""
	Local cQuery     := ""
	Local cTxtPrc    := ""
	Local cTxtSec    := ""
	Local cUnMedida  := ""
	// Local dFilterDat := PCPMonitorUtils():RetornaPeriodoFinal(oFiltros["05_TIPOPERIODO"],ddatabase,cValtoChar(oFiltros["06_PERIODO"]))
	Local nIndLinha  := 0
	Local nQuant     := 0
	//Local nValSemaf1 := Val(aSemaforo[1])
	//Local nValSemaf2 := Val(aSemaforo[2])
	Local nLotes     := 0
	Local nPos       := 0
	Local nSaldo     := 0
	Local oJsonRet   := JsonObject():New()
	Local oStyle1  := JsonObject():New()
	Local oStyle2  := JsonObject():New()
	Local oStyle3  := JsonObject():New()
	// Local oStyleSec  := JsonObject():New()

	//Propriedades que devem ser retornadas para monitores do tipo texto
	oJsonRet["corTitulo"]          := "white" //Cor do título do monitor. Se não for informada, assumirá o valor #2590aa
	oJSonRet["corFundo"] :="white"
	oJsonRet["altura"] := "350"
	oJsonRet["alturaMinimaWidget"] := "350px" //Altura mínima do monitor. Se não for informada, assumirá o valor 350px
	oJsonRet["alturaMaximaWidget"] := "350px" //Altura máxima do monitor. Se não for informada, assumirá o valor 350px
	oJsonRet["linhas"]             := {}      //Array de objetos json com cada linha de informação do monitor
	oJsonRet["tags"]               := {}      //Array de objetos json com as tags que serão visualizadas no monitor


	//Adiciona as linhas de informação no monitor
	// If nLotes > 0
	// 	oStyleSec["color"] := "white"
	// 	oJSonRet["corFundo"] := IIF(nQuant < nValSemaf1,"rgb(38,186,65)",IIF(nQuant < nValSemaf2,"rgb(255,207,1)","rgb(245,0,49)"))
	// 	If oJSonRet["corFundo"] == "rgb(255,207,1)"
	// 		oStyleSec["color"] := "black"
	// 		oJsonRet["corTitulo"] := "black"
	// 	EndIf
	cTxt1:=alltrim(oFiltros["01_TITULO"])
	cTxt2:=alltrim("turno 1")
	oStyle1["font-weight"] := "bold"
	oStyle1["font-size"]   := "50px"
	oStyle1["line-height"] := "65px"
	oStyle1["text-align"]  := "center"
	oStyle1["color"]       := "black"
	oStyle1["cursor"]      := "pointer"
	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTxt1,"po-sm-12",oStyle1:ToJson(),.T.)
	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTxt2,"po-sm-12",oStyle1:ToJson(),.T.)
	//PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,cTxtSec,"po-font-title po-text-center po-sm-12 po-pt-1 bold-text",oStyleSec:ToJson())
	// Else
	// 	oJsonRet["corFundo"] := "rgb(38,186,65)"
	// 	PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"Nenhum lote do produto vencerá no período selecionado.","po-font-text-large-bold po-text-center po-sm-12 po-pt-4",oStyleSec:ToJson())
	// EndIf
	//Adiciona tags ao monitor
	cJsonDados :=  oJsonRet:toJson()

	//FwFreeArray(aSemaforo)
	FreeObj(oJsonRet)
Return cJsonDados



Method BuscaDetalhes(oFiltros, nPagina) Class DelpiEficienciaTXT
	Local cJsonDados := ""
	Local nPosHeader := 0
	Local oDados     := JsonObject():New()
	Local oStyleHdr  := JsonObject():New()

	oDados["items"]        := {}
	oDados["columns"]      := {}
	oDados["headers"]      := {}
	oDados["tags"]         := {}
	oDados["canExportCSV"] := .T.
	oDados["hasNext"]      := .F.

	oStyleHdr["color"]       := "rgba(0,255,255,1)"
	oStyleHdr["font-weight"] := "bold"
	oStyleHdr["text-align"]  := "center"
	oStyleHdr["font-size"]   := "24px"
	PCPMonitorUtils():AdicionaHeaderDetalhe(oDados["headers"],@nPosHeader,"Sem Detalhes a Exibir","po-sm-12 po-pb-2",oStyleHdr:ToJson())

	cJsonDados := oDados:toJson()
	FreeObj(oDados)
	FreeObj(oStyleHdr)
Return cJsonDados




/*/{Protheus.doc} ValidaPropriedades
Valida os dados informados nas propriedades do Monitor
@type Method
@author
@since
@version
@param  oFiltros, objeto json, Objeto json com os filtros para a consulta dos dados
@return aRetorno, array      , [1] logico - indica se os dados são válidos [2] caracter - mensagem de erro
/*/
Method ValidaPropriedades(oFiltros) Class DelpiEficienciaTXT
	Local aRetorno := {.T.,"TESTE VALIDA"}

Return aRetorno

