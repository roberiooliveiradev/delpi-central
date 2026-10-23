#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'

User function DLP020()

	Local dDtaIniPC := Stod('')
	Local dDtaFimPC := Stod('')
	Local dDtaIniEn := Stod('')
	Local dDtaFimEn := Stod('')
	Local dDtaIniNF := Stod('')
	Local dDtaFimNF := Stod('')
	Local cFornInic := Space(TamSx3('A2_COD')[1])
	Local cFornFina := Space(TamSx3('A2_COD')[1])
	Local cLojaInic := Space(TamSx3('A2_LOJA')[1])
	Local cLojaFina := Space(TamSx3('A2_LOJA')[1])
	Local aIndex	:= {}
	Local aSeek		:= {}
	Local aColumns	:= {}	

	//Private aRotina := MenuDef()
	Private aPerg	:= {}
	Private aRet	:= {}

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Montagem das perguntas                                                  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	aadd(aPerg,{1,'Emissao Inicial P.C.',dDtaIniPC,"","","",".T.",50,.T.})
	aadd(aPerg,{1,'Emissao Final P.C.  ',dDtaFimPC,"","","",".T.",50,.T.})
	aadd(aPerg,{1,'Entrega Inicial P.C.',dDtaIniEn,"","","",".T.",50,.T.})
	aadd(aPerg,{1,'Entrega Final P.C.  ',dDtaFimEn,"","","",".T.",50,.T.})
	aadd(aPerg,{1,'Entrada Inicial N.F.',dDtaIniNF,"","","",".T.",50,.T.})
	aadd(aPerg,{1,'Entrada Final N.F.  ',dDtaFimNF,"","","",".T.",50,.T.})
	aadd(aPerg,{1,'Fornecedor Inicial  ',cFornInic,"@!","","SA2","",50,.F.})
	aadd(aPerg,{1,'Loja Fornecedor Inic',cLojaFina,"@!","","","",30,.F.})
	aadd(aPerg,{1,'Fornecedor Final    ',cFornFina,"@!","NaoVazio()","SA2",".T.",50,.T.})
	aadd(aPerg,{1,'Loja Fornecedor Fim ',cLojaFina,"@!","NaoVazio()","",".T.",30,.T.})

	//-- chamada da funcao parambox()
	lOk := ParamBox(aPerg,"Filtro para P.C. Entregues",@aRet,,,.T.,100,3,,"DLP020",.T.,.T.)

	If	!lOk
		Return
	EndIf

	aDados := D020Query()

	DbSelectArea("SC7")
	DbSetOrder(1)
	DbSeek(xFilial("SC7"))

	/*Aadd( aIndex, "C7_FORNECE" )
	Aadd( aIndex, "D1_PEDIDO" )
	Aadd( aIndex, "D1_COD" )
	Aadd( aIndex, "D1_DTDIGIT" )
	Aadd( aIndex, "C7_EMISSAO" )
	Aadd( aIndex, "C7_DATPRF" )  

	Aadd( aSeek, { 'Fornece'       , {{"","C",TamSx3('A2_COD')[1]    ,0,'Fornece',,}} } )
	Aadd( aSeek, { 'Numero P.C.'   , {{"","C",TamSx3('C7_NUM')[1]    ,0,'Numero P.C.',,}} } )
	Aadd( aSeek, { 'Produto'       , {{"","C",TamSx3('B1_COD')[1]    ,0,'Produto',,}} } )
	Aadd( aSeek, { 'Dta Entrada NF', {{"","D",TamSx3('D1_DTDIGIT')[1],0,'Dta Entrada NF',,}} } )
	Aadd( aSeek, { 'Dta Emissao PC', {{"","D",TamSx3('C7_EMISSAO')[1],0,'Dta Emissao PC',,}} } )
	Aadd( aSeek, { 'Dta Prev.Entr.', {{"","D",TamSx3('C7_DATPRF')[1] ,0,'Dta Prev.Entr.',,}} } )*/

	//Define MsDialog oDlg020 From 100,100 To 300,500 Pixel
		
	oBrowse := FWMBrowse():New()

	// Setar Menu em Branco
	oBrowse:SetMenuDef("")
	
	// Desabilita a utilização das configurações do Browse
	oBrowse:DisableConfig()
	
	// Desabilita a utilização do filtro no Browse
	oBrowse:DisableFilter(.T.)
	
	// Desabilita a utilização da pesquisa no Browse
	oBrowse:DisableSeek()

	// Indicar que neste browse será usado Query 
	oBrowse:SetDataQuery(.T.)

	// Setar qual o Alias que será gerado os dados da query
	oBrowse:SetAlias("TMPPC")

	// Indica quais colunas serão utilizadas como Índice
	//oBrowse:SetQueryIndex(aIndex)

	// Setar qual o conteúdo da query que será executada
	oBrowse:SetQuery(aDados[1])

	// Setar campos para pesquisa
	//oBrowse:SetSeek(,aSeek)

	// Titulo da Janela
	oBrowse:SetDescription("Consulta de Pontualidade de Fornecedores - Pedidos de Compras")

	// Desabilita informações adicionais do browse
	oBrowse:DisableDetails()

	//Adiciona colunas
	nX := 0
	For nCpo := 1 to Len(aDados[2])

		AAdd(aColumns,FWBrwColumn():New())
		nX++
		aColumns[nX]:SetData( &("{||"+aDados[2][nCpo][1]+"}") ) 
		aColumns[nX]:SetTitle(aDados[2][nCpo][2]) 
		aColumns[nX]:SetSize(aDados[2][nCpo][3]) 
		aColumns[nX]:SetDecimal(aDados[2][nCpo][4]) 

	Next nCpo

	oBrowse:SetColumns(aColumns)	
	
	// ativa o browse
	oBrowse:Activate()

	//Activate MsDialog oDlg020 Centered

return

Static Function D020Query()

	Local cQuery  := ''
	//Local aCpos := {'C7_FORNECE','D1_LOJA','D1_DOC','D1_PEDIDO','D1_ITEMPC','D1_COD','D1_QUANT','C7_EMISSAO','C7_DATPRF','D1_DTDIGIT', 'DIAS'}
	Local aCpos := {'C7_FORNECE','D1_LOJA','D1_DOC','D1_PEDIDO','D1_ITEMPC','D1_COD','D1_QUANT','C7_EMISSAO','C7_DATPRF','D1_DTDIGIT','D1_EMISSAO', 'DIAS'}
	Local aCampos := {}
	Local cCampos := ''
	Local aDados  := {}

	DbSelectArea("SX3")
	DbSetOrder(2)
	For	x:=1 To Len(aCpos)

		If	aCpos[x] == 'DIAS'
			AAdd(aCampos,{ aCpos[x], 'Dias', 04, 00 })
		Else
			MsSeek(aCpos[x])
			If	SX3->X3_TIPO == 'D'
				cCampos += "Right("+aCpos[x]+",2) "
				cCampos += " + '/' + " 
				cCampos += "Substring("+aCpos[x]+ ",5,2)"
				cCampos += " + '/' + "
				cCampos += "Left("+aCpos[x]+",4) AS " 
				cCampos += aCpos[x] + ","
			Else
				cCampos += aCpos[x]+","
			EndIf
			If aCpos[x] == "C7_EMISSAO"
				AAdd(aCampos,{aCpos[x], "Dt. Emissao PC", SX3->X3_TAMANHO, SX3->X3_DECIMAL })
			ElseIf aCpos[x] == "D1_EMISSAO"
				AAdd(aCampos,{aCpos[x], "Dt. Emissao NF", SX3->X3_TAMANHO, SX3->X3_DECIMAL })
			Else
				AAdd(aCampos,{ aCpos[x], X3Titulo(), SX3->X3_TAMANHO, SX3->X3_DECIMAL })
			EndIf 	
		EndIf	
		

	Next x

	cCampos := SubStr(cCampos,1,Len(cCampos)-1)

	cQuery := "SELECT " + cCampos 
	//cQuery += ", DATEDIFF(DAY, D1_DTDIGIT, C7_DATPRF) AS DIAS "
	cQuery += ", DATEDIFF(DAY, D1_EMISSAO, C7_DATPRF) AS DIAS "
	cQuery += "FROM "+RetSqlName("SC7")+ " C7 (NOLOCK) "
	cQuery += "INNER JOIN "+RetSqlName("SD1")+" D1 (NOLOCK) ON D1.D_E_L_E_T_ = ' ' AND D1_FILIAL = '"+xFilial("SD1")+"' AND D1_PEDIDO = C7_NUM AND D1_ITEMPC = C7_ITEM AND C7_PRODUTO = D1_COD AND C7_FORNECE = D1_FORNECE AND C7_LOJA = D1_LOJA "
	cQuery += "AND D1_DTDIGIT BETWEEN '"+ DtoS(aRet[5]) +"' AND '"+ DtoS(aRet[6])+"' "
	cQuery += "WHERE C7.D_E_L_E_T_ = ' ' AND C7_FILIAL = '"+xFilial("SC7")+"' AND C7_EMISSAO BETWEEN '"+DtoS(aRet[1])+"' AND '"+DtoS(aRet[2])+"' "
	cQuery += "AND C7_DATPRF BETWEEN '"+DtoS(aRet[3])+"' AND '"+DtoS(aRet[4])+"' "
	cQuery += "AND C7_FORNECE BETWEEN '"+aRet[7]+"' AND  '"+aRet[9]+"' "
	cQuery += "AND C7_LOJA BETWEEN '"+aRet[8]+"' AND '"+aRet[10]+"' "
	cQuery += "ORDER BY C7_FORNECE, C7_LOJA, C7_PRODUTO, C7_NUM, C7_ITEM "

	cQuery := ChangeQuery(cQuery)

	aAdd(aDados,cQuery)
	aAdd(aDados,aCampos)

Return aDados