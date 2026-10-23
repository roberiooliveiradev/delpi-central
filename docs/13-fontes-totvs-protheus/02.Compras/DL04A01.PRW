#include "totvs.ch"
#include "protheus.ch"
#INCLUDE "RWMAKE.CH"
#INCLUDE "TBICONN.CH"
#include 'fileio.ch'
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"

user function DL04A01()

	Private cEOL     := Chr(13)+chr(10)
	Private aHeader  := {}
	Private aCols    := {}
	Private aEdits   :={}
	Private aRegs    := {}
	Private lOk      := .f.
	Private oGetDad1
	Private cNotaFiscal
	Private cNFBar
	Private cFornecedor
	Private dDtDigit

	Private lNf
	Private lVldCpo  := .f.

	FTela()

return


/* +-------------------------------------------------------------------------+
| Funcao     | FTela          | Autor | Gabriel        | Data | 2019/02   |
+-------------------------------------------------------------------------+
| Descricao  | Exibe a tela para informação do RIR.                       |
+-------------------------------------------------------------------------+
| Sintaxe    | FTelaRIR(cVersaoRIR)                                       |
+-------------------------------------------------------------------------+
| Parametros | Nenhum                                                     |
+-------------------------------------------------------------------------+
| Retorno    | Nenhum                                                     |
+-------------------------------------------------------------------------+ */
Static Function FTela()

	Local lRetorno := .T.
	Local oDlg
	Local oRelation
	Local oFWLayer
	Local oMBrowseDown
	Local oMBrowseLeft
	Local oMBrowseRight
	Local oPanelDown
	Local oPanelLeft
	Local oPanelRight
	Local lRetorno    := .T.
	Local aCoors      := FWGetDialogSize(oMainWnd)
	//	LOCAL CNOTAFISCAL := ALLTRIM(SF1->F1_DOC) + ' / ' + ALLTRIM(SF1->F1_SERIE)
	//	LOCAL CFORNECEDOR := POSICIONE("SA2", 1, XFILIAL("SA2") + SF1->F1_FORNECE + SF1->F1_LOJA, "A2_NOME")
	//	LOCAL DDTDIGIT	  := SF1->F1_DTDIGIT
	Local aSizeAut    := MsAdvSize()
	Local nColGrp     := aSizeAut[5]/2
	Local lCheckBox1  := .F.
	Local lCheckBox2  := .F.

	Static oGroup1
	Static oFont1     := TFont():New("Arial",,020,,.T.,,,,,.F.,.F.)


	fHeader(@aHeader, @aEdits) // Declara os Tipos e Labels nos Grids Abaixo.
	lRetorno := FGetColunas(@aCols)
	cNFBar := iif( !lNf,"",ALLTRIM(SF1->F1_DOC)  )
	cNotaFiscal := iif( !lNf,"",ALLTRIM(SF1->F1_DOC) + ' / ' + ALLTRIM(SF1->F1_SERIE) )
	cFornecedor := iif( !lNf,"",Posicione("SA2", 1, xFilial("SA2") + SF1->F1_FORNECE + SF1->F1_LOJA, "A2_NOME") )
	dDtDigit	:= iif( !lNf,DATE(),SF1->F1_DTDIGIT )

	DEFINE MSDIALOG oDlg TITLE "Gerar Etiqueta Almoxarifado" FROM aCoors[1],aCoors[2] TO aCoors[3],aCoors[4] PIXEL

	//-----------------> FWLayer é um componente desenvolvido para facilitar a organização e a divisão das informações na tela por meio de janelas dividas em linhas e colunas.
	oFWLayer := FWLayer():New()
	oFWLayer:Init(oDlg,.F.,.T.)

	//Adicionando coluna à primeira linha
	oFWLayer:AddLine('LIN1',25,.F.)
	oFWLayer:addCollumn('COL1',100, .T. ,'LIN1')
	oFWLayer:AddWindow("COL1","oPanel1","Dados da Nota Fiscal",100,.F.,.T.,,"LIN1",{ || })
	oPanelN := oFWLayer:GetWinPanel("COL1","oPanel1","LIN1")

	//painel
	oPanelN	:= oFWLayer:getColPanel('COL1','LIN1') // Janela de cima - NF
	@ 025, 008 SAY oSay1 PROMPT "Nota Fiscal:"      SIZE 041, 007 OF oPanelN COLORS 32768, 16777215 PIXEL
	@ 022, 043 MSGET oGet1 VAR cNotaFiscal WHEN .F. SIZE 060, 010 OF oPanelN COLORS 32768, 16777215 PIXEL
	@ 040, 008 SAY oSay2 PROMPT "Fornecedor:"       SIZE 031, 007 OF oPanelN COLORS 32768, 16777215 PIXEL
	@ 038, 043 MSGET oGet2 VAR cFornecedor WHEN .F. SIZE 171, 010 OF oPanelN COLORS 32768, 16777215 PIXEL
	@ 055, 008 SAY oSay3 PROMPT "Dt Digitação:"     SIZE 031, 007 OF oPanelN COLORS 32768, 16777215 PIXEL
	@ 053, 043 MSGET oGet3 VAR dDtDigit WHEN .F.    SIZE 060, 010 OF oPanelN COLORS 32768, 16777215 PIXEL
	////	@ 025, 220 SAY oSay5 PROMPT "Versão:" SIZE 031, 007 OF oPanelN COLORS 32768, 16777215 PIXEL
	////	@ 022, 246 MSGET oGet3 VAR cVersao    WHEN .F.  SIZE 060, 010 OF oPanelN COLORS 32768, 16777215 PIXEL
	//
	//Adicionando colunas à segunda linha
	oFWLayer:AddLine('LIN2',75,.F.)
	oFWLayer:addCollumn('COL1',100, .F. ,'LIN2')
	oFWLayer:AddWindow("COL1","oPanel2","Itens",100,.F.,.T.,,"LIN2",{ || })
	oPanelI := oFWLayer:GetWinPanel("COL1","oPanel2","LIN2")

	oGetDad1 := MsNewGetDados():New(001,001,(oPanelI:nHeight/2),(oPanelI:nWidth)/2,GD_UPDATE+GD_DELETE+GD_INSERT,'U_DL04A01L',,,aEdits,0,,,,,oPanelI, aHeader, aCols)

	aColsX           := aCols
	oGetDad1:lActive := .T.
	oDlg:lMaximized  := .T.
	lOk := .F.
	lVldCpo := .t.
	ACTIVATE MSDIALOG oDlg CENTERED ON INIT EnchoiceBar( oDlg, {||If ( U_04A01TOK()  ,oDlg:End(), lOk:= .T.)},{||oDlg:End()})

	//	IF LOK
	//	//	FPROCESSAR(MOBS1, MOBS2, CVERSAO)
	//	ENDIf

Return


/* +-------------------------------------------------------------------------+
| Funcao     | FProcessar     | Autor | Gabriel        | Data | 2019/02  |
+-------------------------------------------------------------------------+
|  Descricao | Gera rir Automático.                                       |
+-------------------------------------------------------------------------+
| Sintaxe    | FGetColunas(aColunas)                                      |
+-------------------------------------------------------------------------+
| Parametros | aColunas : Vetor que será utilizando no msNewGetDados.     |
+-------------------------------------------------------------------------+
| Retorno    | lRetorno.                                                  |
+-------------------------------------------------------------------------+ */

User Function DL04A01L()

	Local lRet := .t.

	//	if oGetDad1:nAt == Len(oGetDad1:aCols)
	//		fSetLine()
	//	endif
	//	//	For i:= 1 to Len(oGetDad1:aCols)
	//	If !GdDeleted(i, oGetDad1:aHeader, oGetDad1:aCols)

Return lRet

/*
+-------------------------------------------------------------------------+
| Funcao     | FProcessar     | Autor | Gabriel        | Data | 2019/02   |
+-------------------------------------------------------------------------+
|  Descricao | Gera rir Automático.                                       |
+-------------------------------------------------------------------------+
| Sintaxe    | FGetColunas(aColunas)                                      |
+-------------------------------------------------------------------------+
| Parametros | aColunas : Vetor que será utilizando no msNewGetDados.     |
+-------------------------------------------------------------------------+
| Retorno    | lRetorno.                                                  |
+-------------------------------------------------------------------------+ */
User Function 04A01TOK()

	Local lRet := .t.
	Local aDados
	Local cMens := "Deseja Imprimir as Etiquetas ?"
	Local cMsgA := ""
	Local nPLote := ascan(aHeader,{|x| Trim(x[2]) == "D1LOTECTL"})
	Local nPTEti := ascan(aHeader,{|x| Trim(x[2]) == "TOTETI"})
	Local nPQEti := ascan(aHeader,{|x| Trim(x[2]) == "QTDETI"})
	Local nPQNF  := ascan(aHeader,{|x| Trim(x[2]) == "D1QUANT"})
	Local nPRest := ascan(aHeader,{|x| Trim(x[2]) == "RESTO"})
	Local nPCod   := ascan(aHeader,{|x| Trim(x[2]) == "D1_COD"})
	Local nPDesc  := ascan(aHeader,{|x| Trim(x[2]) == "B1_DESC"})
	Local nPUn    := ascan(aHeader,{|x| Trim(x[2]) == "B1_UM"})
	Local nPLocal := ascan(aHeader,{|x| Trim(x[2]) == "BZ_MPLOCAL"})
	if MsgYesNo(cMens,"ATENÇÃO","YESNO")
		For i:= 1 to Len(oGetDad1:aCols)

			If !GdDeleted(i, oGetDad1:aHeader, oGetDad1:aCols)

				aDados:={oGetDad1:aCols[i][nPcod]  ,;
					oGetDad1:aCols[i][nPDesc] ,;
					oGetDad1:aCols[i][nPUn]   ,;
					oGetDad1:aCols[i][nPLocal],;
					oGetDad1:aCols[i][nPLote] ,;
					oGetDad1:aCols[i][nPTEti] ,;
					oGetDad1:aCols[i][nPQEti] ,;
					oGetDad1:aCols[i][nPQNF]  ,;
					oGetDad1:aCols[i][nPRest] }
				//				GdFieldGet("TOTETI",i),;
				//				GdFieldGet("QTDETI",i),;
				//				GdFieldGet("D1QUANT",i),;
				//				GdFieldGet("REST",i)}

				cMsgA +="Codigo Produto............:"+ oGetDad1:aCols[i][ nPcod]   + cEol
				cMsgA +="Descricao.................:"+ oGetDad1:aCols[i][ nPDesc]  + cEol
				cMsgA +="Unidade Medida............:"+ oGetDad1:aCols[i][ nPUn]    + cEol
				cMsgA +="Almoxarifado..............:"+ oGetDad1:aCols[i][ nPLocal] + cEol
				cMsgA +="Lote......................:"+ oGetDad1:aCols[i][ nPLote]  + cEol
				cMsgA +="Total Etiqueta............:"+ cValToChar(oGetDad1:aCols[i][ nPTEti]) + cEol
				cMsgA +="Quantidade Por etiqueta...:"+ cValToChar(oGetDad1:aCols[i][ nPQEti]) + cEol
				cMsgA +="Qtd NF....................:"+ cValToChar(oGetDad1:aCols[i][ nPQNF] ) + cEol
				cMsgA +="Resto.....................:"+ oGetDad1:aCols[i][ nPRest]             + cEol


				AVISO("DELPI", cMsgA, { "OK"}, 3)
				//cMsgA:=""
				DL04AIMP(aDados)

			endif
		Next i
	endif
Return lRet

/*
+-------------------------------------------------------------------------+
| Funcao     | fHeader       | Autor | Gabriel        | Data | 2019/02    |
+-------------------------------------------------------------------------+
|  Descricao | Monta as colunas do GRID.                                  |
+-------------------------------------------------------------------------+
| Sintaxe    | fHeader1(aCab, aEdits)                                     |
+-------------------------------------------------------------------------+
| Parametros | aCab   : Cabeçalho do GRID.                                |
|            | aEdits : Campos que estão liberados para editar.           |
+-------------------------------------------------------------------------+
| Retorno    | Nenhum                                                     |
+-------------------------------------------------------------------------+ */
Static Function fHeader(aCab, aEdits)
	Local lRetorno := .T.

	DbSelectArea("SX3")
	DbSetOrder(2)

	dbSeek("D1_COD")
	aAdd(aCab,{"Cod.Produto","D1_COD",x3_picture,x3_tamanho,x3_decimal,"U_DL04A01C('D1_COD')",x3_usado,x3_tipo,   ,x3_context})

	dbSeek("B1_DESC")
	aAdd(aCab,{"Descricao","B1_DESC",x3_picture,x3_tamanho,x3_decimal,,x3_usado,x3_tipo,   ,x3_context})

	dbSeek("B1_UM")
	aAdd(aCab,{"UM","B1_UM",x3_picture,x3_tamanho,x3_decimal,,x3_usado,x3_tipo,   ,x3_context})


	dbSeek("BZ_MPLOCAL")
	aAdd(aCab,{"Endereço","BZ_MPLOCAL",x3_picture,x3_tamanho,x3_decimal,,x3_usado,x3_tipo,   ,x3_context})

	dbSeek("D1_LOTECTL")
	aAdd(aCab,{"Lote","D1LOTECTL",x3_picture,x3_tamanho,x3_decimal,,x3_usado,x3_tipo,   ,x3_context})

	dbSeek("QUG_PRAZO")
	aAdd(aCab,{"Total Etiqueta","TOTETI"   ,x3_picture,x3_tamanho,x3_decimal,"U_DL04A01E('TOTETI')",x3_usado,x3_tipo,     ,x3_context})

	dbSeek("D1_QUANT")
	aAdd(aCab,{"Quantidade Por etiqueta","QTDETI"   ,x3_picture,x3_tamanho,x3_decimal,"U_DL04A01E('QTDETI')",x3_usado,x3_tipo,     ,x3_context})
	aAdd(aCab,{"Qtd NF","D1QUANT"   ,x3_picture,x3_tamanho,x3_decimal,"U_DL04A01E('D1QUANT')",x3_usado,x3_tipo,     ,x3_context})

	dbSeek("B1_UM")
	aAdd(aCab,{"Resto","RESTO",x3_picture,1,0,"U_DL04A01E('RESTO')",x3_usado,x3_tipo,   ,x3_context})


	aEdits := {"D1_COD","BZ_MPLOCAL", "QTDETI", "D1LOTECTL","D1QUANT","TOTETI"}

Return

USER Function DL04A01C(xCampo)
	Local lRet := .t.
	Local cCodProd
	//Local aArea:= getarea()


	If lVldCpo

		cCodProd:=  iif(Empty(GdFieldGet("D1_COD",oGetDad1:nAt,.T.)),M->D1_COD,GdFieldGet("D1_COD",oGetDad1:nAt,.T.))

		If alltrim(xCampo) $ "D1_COD" .OR. ( ( alltrim(xCampo) $ "D1_LOTECTL") .AND. !Empty( GdFieldGet("D1LOTECTL",oGetDad1:nAt,.T.)) )

			iF !(DL04A01D(xCampo)) .AND. lNf

				//Restarea( aArea)
				return .f.

			EndIf

			IF  alltrim(xCampo) $ "D1_COD"

				GDFieldPut("B1_DESC",Posicione("SB1",1,xFilial("SB1")+cCodProd,"B1_DESC"),oGetDad1:nAt)
				GDFieldPut("B1_UM",Posicione("SB1",1,xFilial("SB1")+cCodProd,"B1_UM"),oGetDad1:nAt)
				GDFieldPut("BZ_MPLOCAL",Posicione("SBZ",1,xFilial("SBZ")+cCodProd,"BZ_MPLOCAL"),oGetDad1:nAt)
				GDFieldPut("RESTO","N",oGetDad1:nAt)
				GDFieldPut("TOTETI" ,1,oGetDad1:nAt)
				GDFieldPut("QTDETI" ,1,oGetDad1:nAt)
				GDFieldPut("D1QUANT",1,oGetDad1:nAt)
				oGetdad1:ForceRefresh ()

			ENDIF

		EndIf
	EndIf
	//Restarea( aArea)
Return lRet

//valida se o produto pertece a nota fiscal selecionada
/*
+-------------------------------------------------------------------------+
| Funcao     | FGetColunas    | Autor | Gabriel        | Data | 2019/02   |
+-------------------------------------------------------------------------+
|  Descricao | Popula vetor com os itens da nota selecionada.             |
+-------------------------------------------------------------------------+
| Sintaxe    | FGetColunas(aColunas)                                      |
+-------------------------------------------------------------------------+
| Parametros | aColunas : Vetor que será utilizando no msNewGetDados.     |
+-------------------------------------------------------------------------+
| Retorno    | lRetorno.                                                  |
+-------------------------------------------------------------------------+ */
Static Function DL04A01D(xCampo)
	Local cSql := ""
	Local lRet := .t.

	Local nPLote := ascan(aHeader,{|x| Trim(x[2]) == "D1LOTECTL"})
	Local nPCod:= ascan(aHeader,{|x| Trim(x[2]) == "D1_COD"})

	IF lNf

		cSql+="SELECT      ISNULL(COUNT(*),0 ) QTD,ISNULL(COUNT(distinct B1_COD + D1_LOTECTL ),0 ) QTPRLT" + cEol

		cSql+=" FROM       dbo.SD1010 A (NOLOCK) " + cEol
		cSql+=" LEFT JOIN  dbo.SBZ010 SBZ (NOLOCK) ON SBZ.D_E_L_E_T_ = '' " + cEol
		cSql+="                                       AND A.D1_FILIAL = SBZ.BZ_FILIAL " + cEol
		cSql+="                                       AND A.D1_COD = SBZ.BZ_COD " + cEol
		cSql+=" JOIN       dbo.SB1010 SB1 (NOLOCK) ON SB1.D_E_L_E_T_ = '' " + cEol
		cSql+="                                       AND A.D1_COD = B1_COD " + cEol
		cSql+=" WHERE      A.D_E_L_E_T_ = '' " + cEol
		cSql+="            AND A.D1_FILIAL		= "+ valtosql( iif(lNf,xFilial("SD1")  ,"" )) + cEol
		cSql+="            AND D1_DOC			= "+ valtosql( iif(lNf,SF1->F1_DOC     ,"" )) + cEol
		cSql+="            AND A.D1_SERIE		= "+ valtosql( iif(lNf,SF1->F1_SERIE   ,"" )) + cEol
		cSql+="            AND A.D1_FORNECE		= "+ valtosql( iif(lNf,SF1->F1_FORNECE ,"" )) + cEol
		cSql+="            AND A.D1_LOJA		= "+ valtosql( iif(lNf,SF1->F1_LOJA    ,""))+ cEol
		IF xCampo $ "D1_COD"
			cSql+="            AND A.D1_COD		= "+ valtosql( iif(lNf,&(ReadVar()),"" )) + cEol
		ELSEif xCampo $ "D1_LOTECTL"
			cSql+="            AND A.D1_LOTECTL		= "+ valtosql( iif(lNf,&(ReadVar()),"" )) + cEol
		endif


		If Select("QRY01D") > 1
			QRY01D->(DbCloseArea())
		EndIf

		TcQuery cSQL New Alias "QRY01D"

		if !QRY01D->(Eof()) .and. ( !( QRY01D->QTD > 0) .OR. QRY01D->QTPRLT != 1)

			IF xCampo $ "D1_COD"
				MsgStop( "O Produto não pertence a Nota Selecionada", "DL04A01D" )
			ELSEIF xCampo $ "D1_LOTECTL"
				MsgStop( "O Produto/Lote Digitado não pertence a Nota Selecionada", "DL04A01D" )
			endif

			lRet := .f.

		EndIf
		QRY01D->(DbCloseArea())

	EndIf

	//	if lRet
	//		IF xCampo $ "D1_COD"
	//
	//			aColsX[ oGetDad1:nAt][nPCod]:= &(ReadVar())
	//
	//		ELSEIF xCampo $ "D1_LOTECTL"
	//
	//			aColsX[ oGetDad1:nAt][ nPLote]:= &(ReadVar())
	//
	//		endif
	//
	//	endIf

Return lRet


USER Function DL04A01E(xOpc)

	Local cSql := ""
	Local lRet := .t.
	Local nTotEti :=  GdFieldGet("TOTETI",oGetDad1:nAt,.t.)//Total de Etiquetas a serem impressas
	Local nQtdEti :=  GdFieldGet("QTDETI",oGetDad1:nAt,.t.)//Quantidade de produtos em cada etiqueta
	Local nQtdNF  :=  GdFieldGet("D1QUANT",oGetDad1:nAt,.t.)//Quantidade na 1 UM da Nota Fiscal D1_QUANT

	Local cMsg:=""
	Local cEol := chr(10)
	Local nPTEti:=ascan(aHeader,{|x| Trim(x[2]) == "TOTETI"})
	Local nPQEti:=ascan(aHeader,{|x| Trim(x[2]) == "QTDETI"})
	Local nPQNF :=ascan(aHeader,{|x| Trim(x[2]) == "D1QUANT"})
	Local nPRest :=ascan(aHeader,{|x| Trim(x[2]) == "RESTO"})
	//ascan(aHeader5,{|x| Trim(x[2]) == "MAC_DEPDTN"})

	If lVldCpo


		IF xOpc =="D1QUANT"
			//nQtdNF:=  &(readvar())
			//			oGetDad1:aCols[ oGetDad1:nAt][ nPQNF] := nPQNF
			//aColsX[ oGetDad1:nAt][ nPQNF] := nPQNF
			cMsg += "Deseja realizar o calculo baseado em qual campo ?" + cEoL
			cMsg +="1 - Total Etiqueta" + cEoL
			cMsg +="2 - Quantidade Por etiqueta"
			xOpc:=	iif(AVISO("Delpi - Etiqueta Almoxarifado", cMsg, { "1 - Total Eti", "2 - Qtd Por Eti"}, 1) == 1, xOpc :="TOTETI",xOpc :="QTDETI")

		endif
		if xOpc =="TOTETI"
			//		if("TOTETI" $ readvar()
			//			nTotEti :=  &(readvar())
			//		endif
			nQtdEti := NOROUND(nQtdNF /nTotEti,0)
			If nQtdNF % nQtdEti >0
				nTotEti ++
				GDFieldPut("RESTO","S",oGetDad1:nAt)
				GDFieldPut("TOTETI",nTotEti,oGetDad1:nAt)
			ELSE
				GDFieldPut("RESTO","N",oGetDad1:nAt)
			ENDIF
			GDFieldPut("QTDETI",nQtdEti,oGetDad1:nAt)


			//			oGetDad1:aCols[ oGetDad1:nAt][ nPTEti] := nTotEti
			//			oGetDad1:aCols[ oGetDad1:nAt][ nPQEti] := nQtdEti
			//			oGetDad1:aCols[ oGetDad1:nAt][ nPRest] := "N"
			//
			//			aColsX[ oGetDad1:nAt][ nPTEti] := nTotEti
			//			aColsX[ oGetDad1:nAt][ nPQEti] := nQtdEti
			//			aColsX[ oGetDad1:nAt][ nPRest] := "N"

		elseif xOpc =="QTDETI"

			//			nQtdEti :=  &(readvar())
			//VERIFICO SE A QUANTIDADE A SER IMPRESSA É MAIOR QUE A QUANTIDADE DA NOTA
			if nQtdEti > nQtdNF

				ApMsgAlert('A quantidade de Etiquetas nao pode ser maior que a quantidade da Nota Fiscal !!!')
				RestArea( aArea)
				Return .F.

			Endif

			nTotEti:= NOROUND(nQtdNF /nQtdEti,0)


			//			oGetDad1:aCols[ oGetDad1:nAt][ nPTEti] := nTotEti
			//			oGetDad1:aCols[ oGetDad1:nAt][ nPQEti] := nQtdEti

			//			aColsX[ oGetDad1:nAt][ nPTEti] := nTotEti
			//			aColsX[ oGetDad1:nAt][ nPQEti] := nQtdEti
			//VERIFICO SE POSSUI RESTO DA DIVISÃO
			If nQtdNF % nQtdEti >0
				nTotEti++
				//GDFieldPut( "TOTETI",+1,oGetDad1:nAt)
				GDFieldPut("RESTO","S",oGetDad1:nAt)
				//				oGetDad1:aCols[ oGetDad1:nAt][ nPRest] := "S"
				//				aColsX[ oGetDad1:nAt][ nPRest] := "S"

			else

				GDFieldPut("RESTO","N",oGetDad1:nAt)
				//				aColsX[ oGetDad1:nAt][ nPRest] := "N"
				//				oGetDad1:aCols[ oGetDad1:nAt][ nPRest] := "N"
			ENDIF
			GDFieldPut( "TOTETI",nTotEti,oGetDad1:nAt)
		ENDIF

	ENDIF

	oGetdad1:ForceRefresh ()


Return lRet


/*
+-------------------------------------------------------------------------+
| Funcao     | FGetColunas    | Autor | Gabriel        | Data | 2019/02   |
+-------------------------------------------------------------------------+
|  Descricao | Popula vetor com os itens da nota selecionada.             |
+-------------------------------------------------------------------------+
| Sintaxe    | FGetColunas(aColunas)                                      |
+-------------------------------------------------------------------------+
| Parametros | aColunas : Vetor que será utilizando no msNewGetDados.     |
+-------------------------------------------------------------------------+
| Retorno    | lRetorno.                                                  |
+-------------------------------------------------------------------------+ */
Static Function FGetColunas(aColunas)
	Local cCentroC := ''
	Local lRetorno := .T.

	Local cSql := ""
	lNf := MsgYesNo('Deseja Utilizar os dados da Nota fiscal Selecionada ? ', 'DELPI - ETIQUETA ALMOXARIFADO')

	if lNf
		cSql+="SELECT      A.D1_COD , SB1.B1_DESC,SB1.B1_UM,SBZ.BZ_MPLOCAL,1 QTDETI, A.D1_QUANT D1QUANT, D1_LOTECTL " + cEol
	else

		cSql+="SELECT TOP 1    '' D1_COD , '' B1_DESC,'' B1_UM,'' BZ_MPLOCAL,1 QTDETI, 0.00 D1QUANT, '' D1_LOTECTL " + cEol
	endif
	cSql+=" FROM       dbo.SD1010 A (NOLOCK) " + cEol
	cSql+=" LEFT JOIN  dbo.SBZ010 SBZ (NOLOCK) ON SBZ.D_E_L_E_T_ = '' " + cEol
	cSql+="                                       AND A.D1_FILIAL = SBZ.BZ_FILIAL " + cEol
	cSql+="                                       AND A.D1_COD = SBZ.BZ_COD " + cEol
	cSql+=" JOIN       dbo.SB1010 SB1 (NOLOCK) ON SB1.D_E_L_E_T_ = '' " + cEol
	cSql+="                                       AND A.D1_COD = B1_COD " + cEol
	cSql+=" WHERE      A.D_E_L_E_T_ = '' " + cEol
	cSql+="            AND A.D1_FILIAL		= "+ valtosql( iif(lNf,xFilial("SD1")  ,"" )) + cEol
	cSql+="            AND D1_DOC			= "+ valtosql( iif(lNf,SF1->F1_DOC     ,"" )) + cEol
	cSql+="            AND A.D1_SERIE		= "+ valtosql( iif(lNf,SF1->F1_SERIE   ,"" )) + cEol
	cSql+="            AND A.D1_FORNECE		= "+ valtosql( iif(lNf,SF1->F1_FORNECE ,"" )) + cEol
	cSql+="            AND A.D1_LOJA		= "+ valtosql( iif(lNf,SF1->F1_LOJA    ,""))  + cEol
	cSql+=" ORDER BY D1_ITEM"
	If Select("QRYSD1") > 1
		QRYSD1->(DbCloseArea())
	EndIf

	TcQuery cSQL New Alias "QRYSD1"

	While !QRYSD1->(Eof())
		lRetorno := .F.


		DbSelectArea("QRYSD1")

		aAdd(aColunas,{QRYSD1->D1_COD,QRYSD1->B1_DESC,QRYSD1->B1_UM,QRYSD1->BZ_MPLOCAL,QRYSD1->D1_LOTECTL,QRYSD1->QTDETI,QRYSD1->D1QUANT,QRYSD1->D1QUANT,'N',.f.})

		QRYSD1->(DbSkip())
	EndDo
	QRYSD1->(DbCloseArea())

Return lRetorno

Static Function DL04AIMP(aDados)

	Local cPorta   :="LPT1"
	//Local cCapLpt1 := "C:\TEMP\CAPTURE.BAT"
	//Local cLPT1    := "NET USE LPT1: \\NOTEDELL-MAC\ARGOX /PERSISTENT:YES EXIT"
	Local cLocEti  := AllTrim(SuperGetMv("DP_LOCETI",,""))
	Local cNomEti  := AllTrim(SuperGetMv("DP_NOMETI",,""))
	Local cDirEtq  := "\ETIQUETAS\"
	Local cFileEtq := "ETIQUETA.PRN"
	Local cCmd	   := "TYPE "
	Local nHandle  := 0
	Local lResto := .f.

	If aDados[9] =="S"
		lResto := .t.
		//aDados[6] += 1
	endif
	//	nTotEtiq
	//	nQtdEmb
	//	nQtdPro

	//cLPT1    := "NET USE LPT1: \\"+cLocEti+"\"+cNomEti+" /PERSISTENT:YES EXIT"
	//
	//If (WinExec(cLPT1)) != 0
	//	ApMsgAlert('Erro ao executar comando Net Use para a porta LPT1 !!!')
	//	Return
	//EndIf


	For x=1 to aDados[6]

		if x == aDados[6]	 .and. lResto
			aDados[7] :=  aDados[8] % (aDados[6]-1)
		endif

		MSCBPRINTER("OS 214",cPorta,/*Densidade*/,/*Tamanho 69*/ ,.F.)
		MSCBCHKSTATUS(.F.)
		MSCBINFOETI("Etiquetas Almoxarifado","Protheus")
		MSCBLOADGRF("DELPI.BMP")

		MSCBBEGIN(1,6)

		MSCBGRAFIC(16.5, 56.0, "DELPI")

		//MSCBBOX(1.7,1.7,95.8,67.0) // box principal 96.9 , 66.8
		MSCBBOX(2,1.0,97.3,66.8,2)
		/*
		MSCBLineV
		nX1mm			Numérico			Posição X1 em Milímetros						X
		nY1mm			Numérico			Posição Y1 em Milímetros						X
		nY2mm			Numérico			Posição X2 em Milímetros						X
		nEspessura			Numérico			Numero com a espessura em pixel
		*cCor			Caracter			String com a Cor Branca ou Preta ("W" ou "B")										*/
		MSCBLineV(15	,1.7	,65.9	,2)   // 1 linha vertical
		MSCBLineV(37.1	,54.5	,66.0	,2) // 2 linha vertical

		MSCBLineV(73.1	,54.5	,66.0	,2) // 2 linha vertical

		MSCBLineV(28	,15	,28	,2)      // 3 linha vertical
		MSCBLineV(55	,1.7	,42	,2)      // 3 linha vertical


		MSCBLineH(15,15,97.1,2)   // 1 linha horizontal
		MSCBLineH(15,28.5,97.1,2) // 2 linha horizontal
		MSCBLineH(15,42.2,97.1,2) // 3 linha horizontal
		MSCBLineH(15,54.7,97.1,2) // 4 linha horizontal

		MSCBSAY(10,2.5, "APROVADO ALMOX","B","3","2,1")
		MSCBSAYBAR(40.1,	55.2	, Alltrim( aDados[1]),"N","MB07",9.5,.F.,.F.,.F.,,3,2)

		MSCBSAY(76.1,62, "Material","N","2","0.1")
		MSCBSAY(76.1,55.5, aDados[1], "N","3","1")

		//MSCBSAY(17.1,50.5, "Cliente","N","2","0.1")
		MSCBSAY(17.1,50.5, substr( aDados[2],1,50)	,"N","2","0.1")

		MSCBSAY(17.1,45,substr( aDados[2],51,50),"N","2","0.1")
		//MSCBSAY(17.1,43.5, cDescCli ,"N","3","1")

		MSCBSAY(17.1,37.3, "Nota Fiscal","N","2","0.1")
		MSCBSAY(17.1,29.8, cNotaFiscal, "N","3","1")


		//MSCBSAY(60.1,37.3, "Codigo Cliente","N","2","0.1")
		//MSCBSAY(60.1,29.8, cCodCli, "N","3","1")
		MSCBSAYBAR(60.1,29.8, Alltrim(cNFBar)                ,"N","MB07",9.5,.F.,.T.,.F.,,3,2)


		//MSCBSAY(16.1,42.5, "Peso", "N","3","0.1")
		//MSCBSAY(35,49.5, Transform(nPesoTotal, X3Picture("B1_PESO")), "N","3","1")
		MSCBSAY(17.1,23.6, "Local", "N","2","0.1")
		MSCBSAY(17.1,16.3, aDados[4], "N","3","1")

		MSCBSAY(60.1,23.6, "Lote", "N","2","0.1")
		MSCBSAY(60.1,16.3, aDados[5], "N","3","1")

		MSCBSAY(30.1,23.6, "Unidade", "N","2","0.1")
		MSCBSAY(30.1,16.3, aDados[3], "N","3","1")

		MSCBSAY(17.1,11.1, "Data", "N","2","0.1")
		MSCBSAY(17.1,3.8, Dtoc(dDtDigit), "N","3","1") //TSC: 24/10/2018: Diego Kerstner: Alterada para a data do Apontamento.

		MSCBSAY(60.1,11.1, "Quantidade", "N","2","0.1")
		MSCBSAY(60.1,3.8, Transform(	aDados[7] , X3Picture("B1_EMBDELP")), "N","3","1")

		MSCBEND()

		MSCBCLOSEPRINTER()
	Next
Return
Return


Static Function fSetLine()


	aAdd(aColsx,	{Space(TamSx3('D1_COD')[1])		,;
		Space(TamSx3('B1_DESC')[1])		,;
		Space(TamSx3('B1_UM')[1])		,;
		Space(TamSx3('BZ_MPLOCAL')[1])	,;
		Space(TamSx3('D1_LOTECTL')[1])	,;
		0								,;
		0.00							,;
		0.0								,;
		'N',.f.})

Return
