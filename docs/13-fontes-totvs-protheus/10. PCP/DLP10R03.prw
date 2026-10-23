#INCLUDE 'TOTVS.CH'
#INCLUDE "topconn.ch"

#DEFINE IT_CODIGO   01
#DEFINE IT_DESCRIC  02
#DEFINE IT_UNID     03
#DEFINE IT_MAPA     04
#DEFINE IT_EMPENHO  05
#DEFINE IT_ESTOQ99  06
#DEFINE IT_LIBERAR  07
#DEFINE IT_ESTOQ01  08
#DEFINE IT_FALTA    09

/*/{Protheus.doc} nomeFunction
Relatório de Empenhos de Produtos
@type user function
@author Pedro Lindenberg
@since 18/07/2024
@version version
/*/
User Function DLP10R03()
	Local cPerg 					 := "DLP10R03"
	Local   dDataGer       := Date()
	Local   cHoraGer       := Time()
	Local   cTit           := "EMPENHO_"+dToS(dDataGer) + "_" + StrTran(cHoraGer, ':', '-')
	Local   cArquivo       := GetTempPath()+cTit+".rel"
	Local   cArq2       	 := GetTempPath()+cTit+".xlsx"
	Private cTmpWlIni 		 := ""
	Private cTmpWlFim 		 := ""
	Private oFileW      	 := FwFileWriter():New(cArquivo)
	Private oPrtXlsx    	 := FwPrinterXlsx():New()
	Private oCellHorAlign  := FwXlsxCellAlignment():Horizontal()
	Private oCellVertAlign := FwXlsxCellAlignment():Vertical()
	Private cHorAlignment  := oCellHorAlign:Center()
	Private cHorAlignLeft  := oCellHorAlign:Left()
	Private cVertAlignment := oCellVertAlign:Center()
	Private cStyleBord     := FwXlsxBorderStyle():Thin() // estilo da borda fino
	Private cCLRWhite      := "ffffff" // branco
	Private cCLRGray       := "C0C0C0" // cinza
	Private cCLRGray1      := "d1d1d1" // cinza
	Private cCLRDelpi      := "003867" // azul
	Private cCLRBlk        := "0d0c0c" //preto
	PRIVATE lWrapText      := .f.
	PRIVATE nRotation      := 0

	If !Pergunte(cPerg,.t.)

		return

	Else

		//	if cEmpAnt =="05"
		//		MsgStop("Não é possivel utilizar esse relatorio na empresa 05", "Delpi")
		//		Return
		//	Endif

		lRet := oPrtXlsx:Activate(cArquivo, oFileW)

		cTmp1Ini := time()
		FWMsgRun(, {|| fProcRel1() }, "Delpi","1-Aguarde Gerando Relatorio | Empenho de Producao - PCP" )

		oPrtXlsx:toXlsx()
		//Abrindo o excel e abrindo o arquivo xml
		oExcel := MsExcel():New()             //Abre uma nova conexão com Excel
		oExcel:WorkBooks:Open(cArq2)     //Abre uma planilha

		oExcel:SetVisible(.T.)                 //Visualiza a planilha
		oExcel:Destroy()

	Endif

Return(Nil)

/*/{Protheus.doc} nomeStaticFunction
	Realiza a monagem do Relatório
	@type  Static Function
	@author Pedro Lindenberg
	@since 04/07/2024
	@version version
/*/
Static Function fProcRel1()

	Local nRow    := 1 // Linha Atual
	Local nColMax := 9 //Quantidade de Colunas
	//parametros da planilha
	Local cFont       := FwPrinterFont():Calibri()
	Local nSize       := 12
	Local lItalic     := .t.
	Local lBold       := .T.
	Local lUnderlined := .f.
	Local nALiberar   := 0
	Local nQtd99      := 0
	Local nQtd01      := 0
	Local cAlias      := GetNextAlias()
	Local cSoFalta    := ""

	cSoFalta := mv_par08
	/*Adiciona Aba no Excel*/
	oPrtXlsx:AddSheet("PCP")
	//seta a fonte da planilha
	lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)

	/*Ajusta tamanho das Colunas*/
	// Geral 20
	nWidth := 10
	oPrtXlsx:SetColumnsWidth(1					, nColMax			, nWidth)
	oPrtXlsx:SetColumnsWidth(IT_CODIGO	, IT_DESCRIC	, 30		)
	oPrtXlsx:SetColumnsWidth(IT_UNID		, IT_MAPA			,	30		)
	oPrtXlsx:SetColumnsWidth(IT_EMPENHO	, IT_ESTOQ99	, 30		)
	oPrtXlsx:SetColumnsWidth(IT_LIBERAR	, IT_FALTA	, 20		)

	cQryCMP := fGetQry1()
	DBUseArea(.T., "TOPCONN", TCGENQRY(,, cQryCMP), cAlias, .F., .T.)
	IF (cAlias)->(!eof())
		/* inicia preenchimento da aba *\
		|  1 - titulo                   |
		\* 2 - cabeçakho               */
		oPrtXlsx:MergeCells( nRow/*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, nColMax/*nColTo*/)
		// Comando 'Formato de Célula' com cor de texto e fundo personalizada
		oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, .t. /*lWrapText*/, nRotation, cCLRDelpi /*Cor do Texto*/,cCLRGray/*Cor de Fundo*/, "" )
		// define a borda da celula
		oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .t./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk)

		//nRow++ // pula linha

		lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)

		oPrtXlsx:SetText(nRow /*Linha*/, IT_CODIGO/*Coluna*/     , "Empenho de Producao")

		nRow++ // pula linha

		//setar o nome das colunas
		oPrtXlsx:SetText(nRow /*Linha*/, IT_CODIGO     /*Coluna*/, "Codigo"     )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_DESCRIC    /*Coluna*/, "Descricao"  )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_UNID       /*Coluna*/, "UM"         )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_MAPA       /*Coluna*/, "Mapa"       )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_EMPENHO    /*Coluna*/, "Empenho"    )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_ESTOQ99    /*Coluna*/, "Estoque 99" )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_LIBERAR    /*Coluna*/, "A Liberar"  )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_ESTOQ01    /*Coluna*/, "Estoque 01" )
		oPrtXlsx:SetText(nRow /*Linha*/, IT_FALTA    /*Coluna*/, "Falta" )  //""Estoque 01 - A Liberar" -"Estoque 99"

		nRow++ // pula linha
		cTmpWlIni := Time()

		WHILE  (cAlias)->(!eof())

			nQtd99 := 0
			nQtd01 := 0
			dbSelectArea("SB2")
			DbSetOrder(1)
			If (DbSeek(xFilial("SB2") + (cAlias)->D4_COD + '99'))
				nQtd99 := SB2->B2_QATU
			EndIf
			nALiberar := (cAlias)->D4_TOTAL - nQtd99
			If (DbSeek(xFilial("SB2") + (cAlias)->D4_COD + '01'))
				nQtd01 := SB2->B2_QATU
			EndIf

			IF (cSoFalta == 2) .OR. (cSoFalta == 1 .AND. nQtd01 < nALiberar)

				lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)
				// define a borda da celula  1- Primeira coluna
				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

				oPrtXlsx:SetText(	nRow /*Linha*/,IT_CODIGO    /*Coluna*/   ,(cAlias)->D4_COD     )
				oPrtXlsx:SetText(	nRow /*Linha*/,IT_DESCRIC   /*Coluna*/   ,(cAlias)->B1_DESC    )
				oPrtXlsx:SetText(	nRow /*Linha*/,IT_UNID       /*Coluna*/  ,(cAlias)->B1_UM      )
				oPrtXlsx:SetText(	nRow /*Linha*/,IT_MAPA       /*Coluna*/  ,(cAlias)->BZ_MPLOCAL )

				oPrtXlsx:setNumber(nRow /*Linha*/,IT_EMPENHO    /*Coluna*/  ,(cAlias)->D4_QUANT   )
				oPrtXlsx:setNumber(nRow /*Linha*/,IT_ESTOQ99    /*Coluna*/  ,nQtd99               )
				oPrtXlsx:setNumber(nRow /*Linha*/,IT_LIBERAR    /*Coluna*/  ,nALiberar            )
				oPrtXlsx:setNumber(nRow /*Linha*/,IT_ESTOQ01    /*Coluna*/  ,nQtd01               )
				oPrtXlsx:setNumber(nRow /*Linha*/,IT_FALTA    /*Coluna*/  ,nQtd01  -nALiberar             )

				nRow++

			ENDIF

			(cAlias)->(dbSkip())

		EndDo

		lRet := oPrtXlsx:ApplyAutoFilter(2/*nRowFrom*/,1 /*nColFrom*/,nRow/*nRowTo*/,nColMax/*nColTo*/)
		(cAlias)->(dbCloseArea())

	endif

return

/*/{Protheus.doc} nomeStaticFunction
	Retorna Query para preenchimento das linhas do Relatório
	@type  Static Function
	@author Pedro Lindenberg
	@since 04/07/2024
	@version version
/*/
Static Function fGetQry1()

	Local cQry := ""

	cCOD_INI     := Mv_Par01
	cCOD_FIM     := Mv_Par02
	dEMISSAO_INI := Mv_Par03
	dEMISSAO_FIM := Mv_Par04
	nFILTRO      := Mv_Par05
	nMARCAR      := Mv_Par06
	nTipoVal     := mv_par07

	Setprc(0,0)
	iPag := 0
	iLinha := 100

	cQry := "SELECT D4_COD, B1_DESC, B1_UM, BZ_MPLOCAL, "+CRLF
	// Valor dentro da data, e filtrado por impressão
	cQry += "  SUM(CASE "+CRLF
	cQry += "        WHEN C2_DATPRI >= '" + DToS(dEMISSAO_INI) + "' AND C2_DATPRI <= '" + DToS(dEMISSAO_FIM) + "' "+CRLF
	If nFILTRO == 1
		cQry += "  AND D4_IMPRESS <> 'S' "+CRLF
	ElseIf nFILTRO == 2
		cQry += "  AND D4_IMPRESS = 'S' "+CRLF
	EndIf
	cQry += "          THEN D4_QUANT "+CRLF
	cQry += "        ELSE 0 END) D4_QUANT, "+CRLF
	// Saldo apenas até a data final (e não saldo completo)
	cQry += "  SUM(CASE "+CRLF
	cQry += "        WHEN C2_DATPRI <= '" + DToS(dEMISSAO_FIM) + "' "+CRLF
	cQry += "          THEN D4_QUANT "+CRLF
	cQry += "        ELSE 0 END) D4_TOTAL "+CRLF
	// fim da query...
	cQry += "FROM "+CRLF
	cQry += "  " + RetSqlName("SD4") + " SD4, "+CRLF
	cQry += "  " + RetSqlName("SB1") + " SB1, "+CRLF
	cQry += "  " + RetSqlName("SBZ") + " SBZ , "+CRLF
	cQry += "  " + RetSqlName("SC2") + " SC2 "+CRLF
	// cQry += " LEFT JOIN  dbo."+ RetSqlName("SC2") + " SC2 (NOLOCK) ON " + CRLF

	cQry += "WHERE "+CRLF
	cQry += "  B1_COD = D4_COD AND "+CRLF
	cQry += "  SB1.D_E_L_E_T_ = '' AND "+CRLF
	cQry += "  B1_FILIAL = '" + xFilial("SB1") + "' AND "+CRLF
	cQry += "  SD4.D_E_L_E_T_ = '' AND "+CRLF
	cQry += "  D4_FILIAL = '" + xFilial("SD4") + "' AND "+CRLF
	cQry += "  D4_COD >= '" + cCOD_INI + "' AND "+CRLF
	cQry += "  D4_COD <= '" + cCOD_FIM + "' AND "+CRLF
	cQry += "  D4_QUANT > 0 AND "+CRLF
	cQry += "  BZ_FILIAL = '" + xFilial("SBZ") + "' AND "+CRLF
	cQry += "  SBZ.D_E_L_E_T_ = '' AND "+CRLF
	cQry += "  BZ_COD = B1_COD "+CRLF
	cQry += " and SC2.D_E_L_E_T_ ='' AND C2_FILIAL = D4_FILIAL " + CRLF
	cQry += "  AND C2_NUM = SUBSTRING(D4_OP,1,6)  " + CRLF
	cQry += " AND C2_ITEM	= '01' AND C2_SEQUEN ='001'  " + CRLF
	cQry += "GROUP BY D4_COD, B1_DESC, B1_UM, BZ_MPLOCAL "+CRLF
	cQry += "ORDER BY D4_COD "+CRLF
	conout(cQry)
Return cQry
