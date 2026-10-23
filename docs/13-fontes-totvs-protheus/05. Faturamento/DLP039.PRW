#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'

/*/{Protheus.doc} DLP039
//Tela para comparativo de custo x venda do produto
@author Diego Kerstner
@since 08/11/2018
@version undefined

@type function
/*/

User function DLP039()

	Local _dDtIniNF := Stod('')
	Local _dDtFimNF := Stod('')
	Local cCliInic  := Space(TamSx3('A1_COD')[1])
	Local cCliFina  := Space(TamSx3('A1_COD')[1])
	Local cLojaInic := Space(TamSx3('A1_LOJA')[1])
	Local cLojaFina := Space(TamSx3('A1_LOJA')[1])
	Local cProdIni  := Space(TamSx3('B1_COD')[1])
	Local cProdFim  := Space(TamSx3('B1_COD')[1])
	Local aIndex	:= {}
	Local aSeek		:= {}
	Local aColumns	:= {}	
	Local cTrab     := ""
	Local _oBrwMar  := nil
	
	//Private aRotina := MenuDef()
	Private _aPerg	:= {}
	Private aRet	:= {}

	
	Public oDlg
	
	DEFINE MSDIALOG oDlg TITLE "Margem de lucro por Produto" FROM 00,00 TO  750, 1024 PIXEL

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Montagem das perguntas                                                  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	aadd(_aPerg,{1,'Emissao Inicial N.F.',_dDtIniNF,"","","",".T.",50,.T.})
	aadd(_aPerg,{1,'Emissao Final N.F.  ',_dDtFimNF,"","","",".T.",50,.T.})
	aadd(_aPerg,{1,'Cliente Inicial  ',cCliInic,"@!","","SA1","",50,.F.})
	aadd(_aPerg,{1,'Loja Cliente Inic',cLojaFina,"@!","","","",30,.F.})
	aadd(_aPerg,{1,'Cliente Final    ',cCliFina,"@!","NaoVazio()","SA1",".T.",50,.T.})
	aadd(_aPerg,{1,'Loja Cliente Fim ',cLojaFina,"@!","NaoVazio()","",".T.",30,.T.})
	aadd(_aPerg,{1,'Produto Inicial  ',cProdIni,"@!","","SB1","",50,.F.})
	aadd(_aPerg,{1,'Produto Final    ',cProdFim,"@!","NaoVazio()","SB1",".T.",50,.T.})

	//-- chamada da funcao parambox()
	lOk := ParamBox(_aPerg,"Filtro para N.F. Saida",@aRet,,,.T.,100,3,,"DLP039",.T.,.T.)

	If	!lOk
		Return
	EndIf

	
	aDados := fCriaArq(@cTrab)
	D039QRY()


	DbSelectArea("TZMAR")
	TZMAR->(dbGoTop())
	
	_oBrwMar := FWMBrowse():New()

	// Setar Menu em Branco
	_oBrwMar:SetMenuDef("")
	
	// Desabilita a utilização das configurações do Browse
	_oBrwMar:DisableConfig()
	
	// Desabilita a utilização do filtro no Browse
	_oBrwMar:DisableFilter(.T.)
	
	// Desabilita a utilização da pesquisa no Browse
	_oBrwMar:DisableSeek()

	// Indicar que neste browse será usado Query 
	_oBrwMar:SetDataQuery(.T.)

	// Setar qual o Alias que será gerado os dados da query
	_oBrwMar:SetAlias("TEMPMAR")

	// Indica quais colunas serão utilizadas como Índice
	//oBrowse:SetQueryIndex(aIndex)

	// Setar qual o conteúdo da query que será executada
	_oBrwMar:SetQuery(aDados[1])

	// Setar campos para pesquisa
	//oBrowse:SetSeek(,aSeek)

	// Titulo da Janela
	_oBrwMar:SetDescription("Consulta Margem de Lucro dos Produtos")

	// Desabilita informações adicionais do browse
	_oBrwMar:DisableDetails()

	//Adiciona colunas
	nX := 0
	For nCpo := 1 to Len(aDados[2])

		AAdd(aColumns,FWBrwColumn():New())
		nX++
		aColumns[nX]:SetData( &("{||"+aDados[2][nCpo][1]+"}") ) 
		aColumns[nX]:SetTitle(aDados[2][nCpo][2]) 
		aColumns[nX]:SetSize(aDados[2][nCpo][3]) 
		aColumns[nX]:SetDecimal(aDados[2][nCpo][4])
		aColumns[nX]:SetPicture(aDados[2][nCpo][5]) 

	Next nCpo

	_oBrwMar:SetColumns(aColumns)	
	
	// ativa o browse
	_oBrwMar:Activate()

	//Activate MsDialog oDlg020 Centered

	//Exclui a tabela do banco
	
	_oBrwMar:DeActivate()
	
	dbCloseArea(cTrab)
	
	If TcCanOpen(cTrab)  
		TcDelFile(cTrab)  
	EndIf
	
return

Static Function D039QRY()

	Local cQuery   := ''
	Local nCustoMO := 0
	Local nCustoPI := 0
	Local nCustoMP := 0


	cQuery := "select D2_COD   		  as PRODUTO, "
	cQuery += "		  B1_DESC         as DESPROD, "
	cQuery += "		  D2_FILIAL       as FILIAL, "
	cQuery += "		  MAX(D2_PRUNIT)  as PRECOUNI,"
	cQuery += "		  MAX(D2_EMISSAO) as EMISSAO  "
	cQuery += "  from "+ RetSqlName("SD2")           
	cQuery += " inner join "+RetSqlName("SB1")+" on B1_COD = D2_COD"                               
 	cQuery += " where B1_TIPO = 'PA' and"
	cQuery += "	   D2_CF in ('5101','5124','6101') and"
	cQuery += "	   D2_EMISSAO = (Select max(B.D2_EMISSAO) from "+RetSqlName("SD2")+" B"
	cQuery += "					  where B.D2_COD = B1_COD and"
	cQuery += "							B1_TIPO = 'PA' and "
	cQuery += "							B.D2_CF in ('5101','5124','6101') and "
	cQuery += "							B.D2_FILIAL = "+ xFilial("SD2") +" and "
	cQuery += "					        (B.D2_EMISSAO between '"+DtoS(aRet[1])+"' and '"+DtoS(aRet[2])+"') and "
	cQuery += "					        (B.D2_CLIENTE between '"+aRet[3]+"' and '"+aRet[5]+"') and "
	cQuery += "					        (B.D2_LOJA between '"+aRet[4]+"' and '"+aRet[6]+"') and "
	cQuery += "					        (B.D2_COD  between '"+aRet[7]+"' and '"+aRet[8]+"') ) "
 	cQuery += "group by D2_COD,B1_DESC,D2_FILIAL	"
 	cQuery += "order by D2_COD"

	If Select("cAliasPA") <> 0
		dbSelectArea("cAliasPA")
		dbCloseArea()
	EndIf
	
	TCQUERY cQuery NEW ALIAS "cAliasPA"
	
	dbselectarea("cAliasPA")
	dbGoTop()
	
	While cAliasPA->(!EOF())	
	
		// Analisa custo de mão de obra do PA
		nCustoMo := D039MO(cAliasPA->PRODUTO)
		nCustoMP := D039MP(cAliasPA->PRODUTO)
		nCustoPI := D039PI(cAliasPA->PRODUTO)
		
		nCustoMP += nCustoPI
		
		TZMAR->(DBAppend( .F. ))
		
		TZMAR->FILIAL	 := cAliasPA->FILIAL
		TZMAR->PRODUTO 	 := AllTrim((TRANSFORM(cAliasPA->PRODUTO, "@!")))
		TZMAR->DESPROD 	 := AllTrim((TRANSFORM(cAliasPA->DESPROD, "@!"))) 
		TZMAR->PRECOUNIT := cAliasPA->PRECOUNI
		//TZMAR->CUSTOMO	 := nCustoMO
		//TZMAR->CUSTOMP	 := nCustoMP
		TZMAR->CUSTOTT	 := nCustoMP + nCustoMO
		TZMAR->MARGEM	 := (((cAliasPA->PRECOUNI - (nCustoMO+nCustoMP))*100)/cAliasPA->PRECOUNI)

		TZMAR->(DBCommit())
		
		cAliasPA->(dbSkip())
		
	EndDo
	
	dbCloseArea("cAliasPA")
	TZMAR->(dbGoTop())
Return


// Função para calcular o custo da Mão de Obra
Static Function D039MO(aProduto)
	Local nCustoMO := 0
	Local cQueryMO := ''

	cQueryMO := "select SUM("
	cQueryMO += "		CASE H1_MAOOBRA"
	cQueryMO += "		     When 0 THEN G2_TEMPAD * BZ_CUSTD"
	cQueryMO += "			 Else (G2_TEMPAD/H1_MAOOBRA) * BZ_CUSTD END )"
	cQueryMO += "			 as Custototal"
	cQueryMO += "  from "+RetSqlName("SG2")
	cQueryMO += " inner join "+RetSqlName("SH1")+" on H1_CODIGO = G2_RECURSO and H1_FILIAL = '" + xFilial("SH1") +"'"
	cQueryMO += " inner join "+RetSqlName("SBZ")+" on BZ_COD = 'MOD'+H1_CCUSTO and BZ_FILIAL = '" + xFilial("SBZ") +"'"
	cQueryMO += " where G2_PRODUTO = '" + aProduto + "'"
	cQueryMO += "   and BZ_FILIAL =  " + xFilial("SBZ")
	cQueryMO += "   and SBZ010.D_E_L_E_T_ <> '*'"
	cQueryMO += "   and SH1010.D_E_L_E_T_ <> '*'"
	cQueryMO += "   and SG2010.D_E_L_E_T_ <> '*'"


	If Select("cAliasMO") <> 0
		dbSelectArea("cAliasMO")
		dbCloseArea()
	EndIf
	
	TCQUERY cQueryMO NEW ALIAS "cAliasMO"
	
	dbselectarea("cAliasMO")
	dbGoTop()
	
	nCustoMO := (cAliasMO->Custototal) 	
    dbCloseArea("cAliasMO")
Return nCustoMO

Static Function D039MP(aProduto)
	Local cQueryMP := ''
	Private nCustoMP := 0

	cQueryMP := "select Sum (G1_QUANT * BZ_CUSTD) as CustoTotMP"
	cQueryMP += "  from SG1010" 
	cQueryMP += " inner join SBZ010 on BZ_COD    = G1_COMP and BZ_FILIAL = '" + xFilial("SBZ") +"'"
	cQueryMP += " inner join SB1010 on B1_COD    = G1_COMP and B1_FILIAL = '" + xFilial("SB1") +"'"
	cQueryMP += " where G1_COD = '" + aProduto + "'"
	cQueryMP += "   and ('"+ DtoS(date())+"' between SG1010.G1_INI and SG1010.G1_FIM)"
	cQueryMP += "   and B1_TIPO = 'MP'"
	cQueryMP += "   and SG1010.D_E_L_E_T_ <> '*'"
	cQueryMP += "   and SBZ010.D_E_L_E_T_ <> '*'"
	cQueryMP += "   and SB1010.D_E_L_E_T_ <> '*'"

	If Select("cAliasMP") <> 0
		dbSelectArea("cAliasMP")
		dbCloseArea()
	EndIf
	
	TCQUERY cQueryMP NEW ALIAS "cAliasMP"
	
	dbselectarea("cAliasMP")
	dbGoTop()
	
	nCustoMP := (cAliasMP->CustoTotMP) 
	dbCloseArea("cAliasMP")
Return nCustoMP


Static Function D039PI(aProduto)
	Local cQueryPI := ''
	Private nCustoPI := 0
	Private nCustoPIMO := 0
	Private nCustoPIMP := 0


	cQueryPI := "select B1_COD, G1_QUANT"
	cQueryPI += "  from SG1010"
	cQueryPI += " inner join SB1010 on B1_COD    = G1_COMP and B1_FILIAL = '"+ xFilial("SB1") +"'"
	cQueryPI += " where G1_COD = '" + aProduto + "'"
	cQueryPI += "   and G1_FILIAL = '" + xFilial("SG1") + "'"
	cQueryPI += "   and ('"+ DtoS(date())+"' between SG1010.G1_INI and SG1010.G1_FIM)"
	cQueryPI += "   and B1_TIPO = 'PI'"
	cQueryPI += "   and SG1010.D_E_L_E_T_ <> '*'"
	cQueryPI += "   and SB1010.D_E_L_E_T_ <> '*'"
	
	If Select("cAliasPI") <> 0
		dbSelectArea("cAliasPI")
		dbCloseArea()
	EndIf
	
	TCQUERY cQueryPI NEW ALIAS "cAliasPI"
	
	dbselectarea("cAliasPI")
	dbGoTop()
	
	While cAliasPI->(!EOF())

		nCustoPIMP := D039MP(cAliasPI->B1_COD)
		nCustoPIMO := D039MO(cAliasPI->B1_COD)
		
		nCustoPIMP := nCustoPIMP * cAliasPI->G1_QUANT
		nCustoPIMO := nCustoPIMO * cAliasPI->G1_QUANT
		nCustoPI := nCustoPIMO + nCustoPIMP  
		cAliasPI->(dbSkip())
	EndDo
	dbCloseArea("cAliasPI")
Return nCustoPI

Static Function fCriaArq(cTrab)
	
	Local aCampos := {}
	Local aHeader := {}
	Local aDados  := {}
	
	aCampos := {}
	aAdd(aCampos,{"FILIAL"   ,"C",   2, 0})
	aAdd(aCampos,{"PRODUTO"  ,"C",  15, 0})
	aAdd(aCampos,{"DESPROD"  ,"C", 120, 0})
	aAdd(aCampos,{"PRECOUNIT","N",  20, 4})
	//aAdd(aCampos,{"CUSTOMO"  ,"N",  20, 4})
	//aAdd(aCampos,{"CUSTOMP"  ,"N",  20, 4})
	aAdd(aCampos,{"CUSTOTT"  ,"N",  20, 4})
	aAdd(aCampos,{"MARGEM"   ,"N",  20, 4})
	
	/*
	TcDelFile("ZMARGEM")
	
	DBCreate("ZMARGEM", aCampos, "TOPCONN") */
	
	cTrab := CriaTrab(aCampos)
	
	DBCreate(cTrab, aCampos, "TOPCONN") 
	
	dbUseArea(.T.,"TOPCONN",cTrab,"TZMAR",.T.,.F.)
	
	//dbUseArea(.T.,"TOPCONN","ZMARGEM","TZMAR",.T.,.F.)
	IndRegua("TZMAR","TZMARA","PRODUTO",,,"Selecionando registros...")
	
	
	//cQuery := "Select FILIAL, PRODUTO, DESPROD, PRECOUNIT, CUSTOMO, CUSTOMP, MARGEM from ZMARGEM"
	//cQuery := "Select FILIAL, PRODUTO, DESPROD, PRECOUNIT, CUSTOTT, MARGEM from ZMARGEM"
	cQuery := "Select FILIAL, PRODUTO, DESPROD, PRECOUNIT, CUSTOTT, MARGEM from "+ cTrab
	aAdd(aDados, ChangeQuery(cQuery))
	
	aCampos := {}
	//aAdd(aCampos, {   "FILIAL",          "Filial",TamSx3("D2_FILIAL")[1],TamSx3("D2_FILIAL")[2],"@E 99"})
	aAdd(aCampos, {  "PRODUTO",         "Produto",   TamSx3("B1_COD")[1],   TamSx3("B1_COD")[2],"@!"})
	aAdd(aCampos, {  "DESPROD",   "Desc. Produto",  TamSx3("B1_DESC")[1],  TamSx3("B1_DESC")[2],"@!"})
	aAdd(aCampos, {"PRECOUNIT",     "Preco Unit.",TamSx3("D2_PRCVEN")[1],TamSx3("D2_PRCVEN")[2],"@E 999,999,999.9999"})
	//aAdd(aCampos, {  "CUSTOMO",  "Custo Mao Obra",                    20,                    0 ,"@E 999,999,999.9999"})
	//aAdd(aCampos, {  "CUSTOMP","Custo Mat. Prima",                    20,                    0 ,"@E 999,999,999.9999"})
	aAdd(aCampos, {  "CUSTOTT",     "Custo Total",                    20,                    0 ,"@E 999,999,999.9999"})
	aAdd(aCampos, {   "MARGEM",          "Margem",                    20,                    0 ,"@E 999,999,999.9999"})
	
	aAdd(aDados,aCampos)


Return(aDados)