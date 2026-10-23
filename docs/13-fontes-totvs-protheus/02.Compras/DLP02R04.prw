#INCLUDE 'TOTVS.CH'
#INCLUDE "topconn.ch"

#DEFINE  IT_CUSTO1           02
#DEFINE  IT_PERCUSTO         03
#DEFINE  IT_CUSTO2       		 04
#DEFINE  IT_PERCUSTO2        05
#DEFINE  IT_DIF  						 06
#DEFINE  IT_DIF2    	 	 		 07
#DEFINE  IT_TOTAL  				   08

/*/{Protheus.doc} nomeFunction
Relatorio Grupo x Produto
@type user function
@author Pedro Lindenberg
@since 04/07/2024
/*/
User Function DLP02R04(cProdCod,aItens,nOpc)
	Local   dDataGer    := Date()
	Local   cHoraGer    := Time()
	Local   cTit        := "ANALISE_"+dToS(dDataGer) + "_" + StrTran(cHoraGer, ':', '-')
	Local   cArquivo    := GetTempPath()+cTit+".rel"
	Local   cArq2       := GetTempPath()+cTit+".xlsx"
	Private cTmpWlIni := ""
	Private cTmpWlFim := ""
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
	Private cFormatVlr 		 := "R$ #,##0.00000;[Red]-R$ #,##0.00000"
	Private cFormatQtd 	 	 := "#,##0.00000000;[Red]-#,##0.00000000"
	Private cFormQtd2 		 :=  "#,##0.0000;[Red]-#,##0.0000" //"0,0000%;[Red]-0,0000%"
	Private cIdItem        :=  SPACE(3)
	Private cId      		   :=  SPACE(GETSX3CACHE("Z8_ID","X3_TAMANHO"))
	Private cCod      		 :=  SPACE(GETSX3CACHE("Z8_COD","X3_TAMANHO"))
	Private cDscPrd      	 :=  SPACE(GETSX3CACHE("Z8_DSCPRD","X3_TAMANHO"))
	Private cPvTab       	 :=  SPACE(GETSX3CACHE("Z8_PVTAB","X3_TAMANHO"))
	Private cPvSuger       :=  SPACE(GETSX3CACHE("Z8_PVSUGER","X3_TAMANHO"))
	Private cPDtEmiDe      :=  FirstDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O PRIMEIRO DIA DO MES ANTERIOR
	Private cPDtDgtDe      :=  FirstDate(MonthSub(DaySub(DATE(),DAY(Date()+1)),3) )  //RETORNAR O PRIMEIRO DIA DOS 3 MESES
	PRIVATE lWrapText      := .f.
	PRIVATE lGerFinCte     := nil
	PRIVATE lGerFinNfe     := nil
	PRIVATE nRotation      := 0
	Default cProdCod := ""
	Default aItens := {}

	lRet := oPrtXlsx:Activate(cArquivo, oFileW)

	cTmp1Ini := time()
	FWMsgRun(, {|| fProcRel1(cProdCod,aItens,nOpc) }, "Delpi","1-Aguarde Gerando Relatorio | Analise Gerencial - Compras" )

	oPrtXlsx:toXlsx()
	//Abrindo o excel e abrindo o arquivo xml
	oExcel := MsExcel():New()             //Abre uma nova conexão com Excel
	oExcel:WorkBooks:Open(cArq2)     //Abre uma planilha

	oExcel:SetVisible(.T.)                 //Visualiza a planilha
	oExcel:Destroy()

Return Nil

/*/{Protheus.doc} nomeStaticFunction
	(long_description)
	@type  Static Function
	@author Pedro Lindenberg
	@since 04/07/2024
	@version version
/*/
Static Function fProcRel1(cProdCod,aItens,nOpc)

	Local nRow    := 1 // Linha Atual
	Local nColMax := 6 //Quantidade de Colunas
	//parametros da planilha
	Local cFont       := FwPrinterFont():Calibri()
	Local nSize       := 12
	Local cCntCol 	  := 0
	Local lItalic     := .t.
	Local lBold       := .T.
	Local lUnderlined := .f.
	Local nTot1 := 0
	Local nTot2 := 0
	Local nTotMod1 := 0
	Local nTotMod2 := 0
	Local aPrdIds:= {}
	Local aTotOne := {}
	Local aTotTwo := {}
	Local aQtd := {}
	Local x := 0
	Local cAlias := GetNextAlias()
	Local cNewAlias := GetNextAlias()
	/*Adiciona Aba no Excel*/
	oPrtXlsx:AddSheet("Compras")
	//seta a fonte da planilha
	lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)

	/*Ajusta tamanho das Colunas*/
	// Geral 20
	nWidth := 10
	oPrtXlsx:SetColumnsWidth(1, nColMax, nWidth)
	oPrtXlsx:SetColumnsWidth(IT_CUSTO1, IT_CUSTO1, 30)
	oPrtXlsx:SetColumnsWidth(IT_PERCUSTO, IT_PERCUSTO, 20)
	oPrtXlsx:SetColumnsWidth(IT_CUSTO2, IT_CUSTO2, 20)
	oPrtXlsx:SetColumnsWidth(IT_DIF, IT_DIF, 20)
	oPrtXlsx:SetColumnsWidth(IT_PERCUSTO2, IT_PERCUSTO2, 20)
	oPrtXlsx:SetColumnsWidth(IT_DIF2, IT_DIF2, 40)

	cQryCMP := fGetQry1(cProdCod,aItens)
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

		nRow++ // pula linha

		lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)

		oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/     , (cAlias)->Z8_COD)
		oPrtXlsx:SetText(nRow /*Linha*/, IT_CUSTO1/*Coluna*/     , (cAlias)->Z8_DSCPRD)

		nRow++ // pula linha

		//setar o nome das colunas
		oPrtXlsx:SetText(nRow /*Linha*/, 1            /*Coluna*/, "Id Item")
		oPrtXlsx:SetText(nRow /*Linha*/, IT_CUSTO1          /*Coluna*/, "Codigo")
		oPrtXlsx:SetText(nRow /*Linha*/, IT_PERCUSTO2 -2              	/*Coluna*/, "Tabela Preço")
		oPrtXlsx:SetText(nRow /*Linha*/, IT_DIF-2     /*Coluna*/, "PV Sugerido")
		oPrtXlsx:SetText(nRow /*Linha*/, IT_DIF2-2    /*Coluna*/, "Custo")

		nRow++ // pula linha
		cTmpWlIni := Time()
		WHILE  (cAlias)->(!eof())

			x++
			AADD(aPrdIds,(cAlias)->Z8_ID)

			lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)
			// define a borda da celula  1- Primeira coluna
			oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

			oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/,  STR(x))

			oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
			oPrtXlsx:SetText(nRow /*Linha*/, IT_CUSTO1/*Coluna*/,  (cAlias)->Z8_ID)
			oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro

			oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

			oPrtXlsx:SetNumber(nRow /*Linha*/,IT_PERCUSTO2-2     /*Coluna*/  ,(cAlias)->Z8_PVTAB )

			oPrtXlsx:SetNumber(nRow /*Linha*/,IT_DIF2-3     /*Coluna*/  ,(cAlias)->Z8_PVSUGER)
			// Comando 'Formato de Célula' com cor de texto e fundo personalizada
			oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

			nRow++
			(cAlias)->(dbSkip())
		EndDo

		(cAlias)->(dbCloseArea())

		nTotMod1 := fSumMod(aPrdIds[1])
		nTotMod2 := fSumMod(aPrdIds[2])

		aQtd := fGetQtd(cProdCod,aItens)

		cQryCMP := fGetQry2(cProdCod,aItens,nOpc)
		DBUseArea(.T., "TOPCONN", TCGENQRY(,, cQryCMP), cNewAlias, .F., .T.)

		(cNewAlias)->(DbGotop())

		While (cNewAlias)->(!EOF())
			AADD(aTotOne,(cNewAlias)->Z9_TOTAL01/aQtd[1])
			AADD(aTotTwo,(cNewAlias)->Z9_TOTAL02/aQtd[2])

			(cNewAlias)->(DbSkip())
		EndDo

		AADD(aTotOne,nTotMod1)
		AADD(aTotTwo,nTotMod2)

		nTot1 := fCalcTot(aTotOne)
		nTot2 := fCalcTot(aTotTwo)

		oPrtXlsx:SetNumber(nRow - 2 /*Linha*/,IT_TOTAL-3     /*Coluna*/  ,nTot1)
		oPrtXlsx:SetNumber(nRow - 1 /*Linha*/,IT_TOTAL-3   /*Coluna*/  ,nTot2)

		(cNewAlias)->(DbGotop())

		While (cNewAlias)->(!EOF())

			IF nOpc == 1

				IF cCntCol == 0

					nRow++

					lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)

					// define a borda da celula  1- Primeira coluna
					oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

					oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
					oPrtXlsx:SetText(nRow /*Linha*/,2 /*Coluna*/,  aPrdIds[1])
					oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro

					oPrtXlsx:SetText(nRow /*Linha*/,  4/*Coluna*/, aPrdIds[2])

					nRow++

					oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, .t. /*lWrapText*/, nRotation, cCLRDelpi /*Cor do Texto*/,cCLRGray/*Cor de Fundo*/, "" )

					oPrtXlsx:SetText(nRow /*Linha*/,  1          /*Coluna*/, "Grupo")
					oPrtXlsx:SetText(nRow /*Linha*/,     IT_CUSTO1           /*Coluna*/, "Custo")
					oPrtXlsx:SetText(nRow /*Linha*/,    IT_PERCUSTO          /*Coluna*/, "%Custo")
					oPrtXlsx:SetText(nRow /*Linha*/,   IT_PERCUSTO2-1     /*Coluna*/, "Custo")
					oPrtXlsx:SetText(nRow /*Linha*/,  IT_DIF-1      /*Coluna*/, "%Custo")
					oPrtXlsx:SetText(nRow /*Linha*/,  IT_DIF      /*Coluna*/, "Diferença")

				ENDIF

				nRow++

				lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)

				// define a borda da celula  1- Primeira coluna
				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

				oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
				oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/,  (cNewAlias)->BM_GRUPO + "-" + (cNewAlias)->BM_DESC) // BM DESCRICAO
				oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr/*formato*/ )

				oPrtXlsx:SetNumber(nRow /*Linha*/,  IT_CUSTO1/*Coluna*/     , (cNewAlias)->Z9_TOTAL01) // Valor total

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

				oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO/*Coluna*/     , SUBSTR(ALLTRIM(STR(fCalcPct(aTotOne,(cNewAlias)->Z9_TOTAL01))),1,5)+"%" ) // Percentual

				oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO+1/*Coluna*/     , " " ) // Percentual

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

				oPrtXlsx:SetNumber(nRow /*Linha*/,  IT_PERCUSTO+1    /*Coluna*/  , (cNewAlias)->Z9_TOTAL02)

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

				oPrtXlsx:SetText(nRow /*Linha*/, IT_PERCUSTO2    /*Coluna*/  , SUBSTR(ALLTRIM(STR(fCalcPct(aTotTwo,(cNewAlias)->Z9_TOTAL02))),1,5)+"%")
				// Comando 'Formato de Célula' com cor de texto e fundo personalizada
				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

				oPrtXlsx:SetText(nRow /*Linha*/, IT_DIF   /*Coluna*/  , STR( ((cNewAlias)->Z9_TOTAL02-(cNewAlias)->Z9_TOTAL01)/100)+"%")

				cCntCol++
				// nRow++
				(cNewAlias)->(DbSkip())

			ELSE

				IF cCntCol == 0

					nRow++

					lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)

					// define a borda da celula  1- Primeira coluna
					oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

					oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
					oPrtXlsx:SetText(nRow /*Linha*/,2 /*Coluna*/,  aPrdIds[1])
					oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro

					oPrtXlsx:SetText(nRow /*Linha*/,  4/*Coluna*/, aPrdIds[2])
					nRow++

					oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, .t. /*lWrapText*/, nRotation, cCLRDelpi /*Cor do Texto*/,cCLRGray/*Cor de Fundo*/, "" )

					oPrtXlsx:SetText(nRow /*Linha*/,  1          		/*Coluna*/, "Produto"  )
					oPrtXlsx:SetText(nRow /*Linha*/,  IT_CUSTO1    	/*Coluna*/, "Custo"    )
					oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO   /*Coluna*/, "%Custo"   )
					oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO2-1/*Coluna*/, "Custo"    )
					oPrtXlsx:SetText(nRow /*Linha*/,  IT_DIF-1      /*Coluna*/, "%Custo"   )
					oPrtXlsx:SetText(nRow /*Linha*/,  IT_DIF      	/*Coluna*/, "Diferença")

				ENDIF

				nRow++

				lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)

				// define a borda da celula  1- Primeira coluna
				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

				oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
				oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/,  (cNewAlias)->Z9_CDPROD) // BM DESCRICAO
				oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr/*formato*/ )

				oPrtXlsx:SetNumber(nRow /*Linha*/,  IT_CUSTO1/*Coluna*/     , (cNewAlias)->Z9_TOTAL01) // Valor total

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

				oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO/*Coluna*/     , SUBSTR(ALLTRIM(STR(fCalcPct(aTotOne,(cNewAlias)->Z9_TOTAL01))),1,5)+"%" ) // Percentual

				oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO+1/*Coluna*/     , " " ) // Percentual

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

				oPrtXlsx:SetNumber(nRow /*Linha*/,  IT_PERCUSTO+1    /*Coluna*/  , (cNewAlias)->Z9_TOTAL02)

				oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, "" /*formato*/ )

				oPrtXlsx:SetText(nRow /*Linha*/, IT_PERCUSTO2    /*Coluna*/  , SUBSTR(ALLTRIM(STR(fCalcPct(aTotTwo,(cNewAlias)->Z9_TOTAL02))),1,5)+"%")
				// Comando 'Formato de Célula' com cor de texto e fundo personalizada
				oPrtXlsx:SetText(nRow /*Linha*/, IT_DIF   /*Coluna*/  , STR( ((cNewAlias)->Z9_TOTAL02-(cNewAlias)->Z9_TOTAL01)/100)+"%")

				cCntCol++
				// nRow++
				(cNewAlias)->(DbSkip())


			ENDIF


		EndDo

		(cNewAlias)->(dbCloseArea())

		// define a borda da celula  1- Primeira coluna
		oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

		oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
		oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/, "MAO DE OBRA") // BM DESCRICAO
		oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro

		oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

		oPrtXlsx:SetNumber(nRow /*Linha*/,  IT_CUSTO1/*Coluna*/     , nTotMod1) // Valor total

		oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, "" /*formato*/ )

		oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO/*Coluna*/     , SUBSTR(ALLTRIM(STR(fCalcPct(aTotOne,nTotMod1))),1,5)+"%" ) // Percentual

		oPrtXlsx:SetText(nRow /*Linha*/,  IT_PERCUSTO+1/*Coluna*/     , " " ) // Percentual

		oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

		oPrtXlsx:SetNumber(nRow /*Linha*/,   IT_CUSTO2 /*Coluna*/  , nTotMod2)

		oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, "" /*formato*/ )

		oPrtXlsx:SetText(nRow /*Linha*/, IT_PERCUSTO2    /*Coluna*/  , SUBSTR(ALLTRIM(STR(fCalcPct(aTotTwo,nTotMod2))),1,5)+"%")
		// Comando 'Formato de Célula' com cor de texto e fundo personalizada
		// oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, "" /*formato*/ )

		oPrtXlsx:SetText(nRow /*Linha*/, IT_TOTAL-2   /*Coluna*/  , STR((nTotMod2-nTotMod1)/100)+"%")

		nRow++

		cTmpWlFim := Time()
		cTmpTot :=ELAPTIME(cTmpWlIni,cTmpWlFim)
		lRet := oPrtXlsx:ApplyAutoFilter(8/*nRowFrom*/,1 /*nColFrom*/,14/*nRowTo*/,nColMax/*nColTo*/)

	ENDIF

Return Nil

/*/{Protheus.doc} nomeStaticFunction
	(long_description)
	@type  Static Function
	@author Pedro Lindenberg
	@since 04/07/2024
	@version version
/*/
Static Function fGetQry1(cProdCod,aItens)

	Local cQry := ""

	cQry += " SELECT "+CRLF
	cQry += " Z8_ID, "+CRLF
	cQry += " Z8_COD, "+CRLF
	cQry += " Z8_DSCPRD, "+CRLF
	cQry += " Z8_PVTAB, "+CRLF
	cQry += " Z8_PVSUGER "+CRLF
	cQry += " FROM SZ8010 SZ8 "+CRLF
	cQry += " WHERE SZ8.D_E_L_E_T_ = ' ' "+CRLF
	cQry += " AND SZ8.Z8_FILIAL = "+valtosql(xFilial("SZ9"))+" "+CRLF
	cQry += " AND SZ8.Z8_ID IN ("+valtosql(aItens[1])+","+valtosql(aItens[2])+") "+CRLF
	cQry += " AND SZ8.Z8_COD = "+valtosql(cProdCod)+" "+CRLF

Return cQry


/*/{Protheus.doc} nomeStaticFunction
	(long_description)
	@type  Static Function
	@author Pedro Lindenberg
	@since 04/07/2024
	@version version
/*/
Static Function fGetQry2(cProdCod,aItens,nOpc)

	Local cQry := ""
	Local cItem1 := aItens[1]
	Local cItem2 := aItens[2]

	IF nOpc == 1

<<<<<<< HEAD
	cQry += " SELECT BM_GRUPO, "+CRLF
	cQry += " BM_DESC, "+CRLF
	cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(aItens[1])+" THEN Z9_TOTAL ELSE 0.00 END ) Z9_TOTAL01, "+CRLF
	cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(aItens[2])+" THEN Z9_TOTAL ELSE 0.00 END ) Z9_TOTAL02 "+CRLF
	cQry += " FROM dbo.SZ9010 (NOLOCK) TBL1 "+CRLF
	cQry += " JOIN SBM010 SBM (NOLOCK) "+CRLF
	cQry += " ON SBM.D_E_L_E_T_ = '' "+CRLF
	cQry += " AND BM_GRUPO = SUBSTRING(Z9_CDPROD, 1, 4) "+CRLF
	cQry += " WHERE TBL1.D_E_L_E_T_ = '' "+CRLF
	cQry += " AND TBL1.Z9_FILIAL = "+valtosql(xFilial("SZ9"))+" "+CRLF
	cQry += " AND TBL1.Z9_IDZ8 IN ( "+valtosql(aItens[1])+" , "+valtosql(aItens[2])+" ) "+CRLF
	cQry += " AND SUBSTRING(Z9_CDPROD, 1, 1) NOT IN ( '8' , '9' , '5' ) "+CRLF
	cQry += " GROUP BY "+CRLF
	cQry += " BM_GRUPO, "+CRLF
	cQry += " BM_DESC "+CRLF
	cQry += " ORDER BY 1 "+CRLF

	ELSE

	cQry += " SELECT DISTINCT Z9_CDPROD, "+CRLF
	cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(cItem1)+" THEN Z9_PRCLIQ ELSE 0.00 END ) Z9_TOTAL01, "+CRLF
	cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(cItem2)+" THEN Z9_PRCLIQ ELSE 0.00 END ) Z9_TOTAL02 "+CRLF
	cQry += " FROM dbo.SZ9010 (NOLOCK) TBL1 "+CRLF
  cQry += " JOIN SBM010 SBM (NOLOCK) "+CRLF
  cQry += " ON SBM.D_E_L_E_T_ = '' "+CRLF
  cQry += " AND BM_GRUPO = SUBSTRING(Z9_CDPROD, 1, 4) "+CRLF
	cQry += " WHERE TBL1.D_E_L_E_T_ = '' "+CRLF
	cQry += " AND TBL1.Z9_FILIAL = "+valtosql(xFilial("SZ9"))+" "+CRLF
	cQry += " AND TBL1.Z9_IDZ8 IN ( "+valtosql(cItem1)+" , "+valtosql(cItem2)+" ) "+CRLF
  cQry += " AND SUBSTRING(Z9_CDPROD, 1, 1) NOT IN ( '8' , '9' , '5' ) "+CRLF
  cQry += " GROUP BY "+CRLF
  cQry += " Z9_CDPROD "+CRLF
	cQry += " ORDER BY 1 "+CRLF
=======
		cQry += " SELECT BM_GRUPO, "+CRLF
		cQry += " BM_DESC, "+CRLF
		cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(aItens[1])+" THEN Z9_TOTAL ELSE 0.00 END ) Z9_TOTAL01, "+CRLF
		cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(aItens[2])+" THEN Z9_TOTAL ELSE 0.00 END ) Z9_TOTAL02 "+CRLF
		cQry += " FROM dbo.SZ9010 (NOLOCK) TBL1 "+CRLF
		cQry += " JOIN SBM010 SBM (NOLOCK) "+CRLF
		cQry += " ON SBM.D_E_L_E_T_ = '' "+CRLF
		cQry += " AND BM_GRUPO = SUBSTRING(Z9_CDPROD, 1, 4) "+CRLF
		cQry += " WHERE TBL1.D_E_L_E_T_ = '' "+CRLF
		cQry += " and Z9_FILIAL = "+
		cQry += " AND TBL1.Z9_IDZ8 IN ( "+valtosql(aItens[1])+" , "+valtosql(aItens[2])+" ) "+CRLF
		cQry += " AND SUBSTRING(Z9_CDPROD, 1, 1) NOT IN ( '8' , '9' , '5' ) "+CRLF
		cQry += " GROUP BY "+CRLF
		cQry += " BM_GRUPO, "+CRLF
		cQry += " BM_DESC "+CRLF
		cQry += " ORDER BY 1 "+CRLF

	ELSE

		cQry += " SELECT DISTINCT Z9_CDPROD, "+CRLF
		cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(cItem1)+" THEN Z9_PRCLIQ ELSE 0.00 END ) Z9_TOTAL01, "+CRLF
		cQry += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(cItem2)+" THEN Z9_PRCLIQ ELSE 0.00 END ) Z9_TOTAL02 "+CRLF
		cQry += " FROM dbo.SZ9010 (NOLOCK) TBL1 "+CRLF
		cQry += " JOIN SBM010 SBM (NOLOCK) "+CRLF
		cQry += " ON SBM.D_E_L_E_T_ = '' "+CRLF
		cQry += " AND BM_GRUPO = SUBSTRING(Z9_CDPROD, 1, 4) "+CRLF
		cQry += " WHERE TBL1.D_E_L_E_T_ = '' "+CRLF
		cQry += " AND TBL1.Z9_IDZ8 IN ( "+valtosql(cItem1)+" , "+valtosql(cItem2)+" ) "+CRLF
		cQry += " AND SUBSTRING(Z9_CDPROD, 1, 1) NOT IN ( '8' , '9' , '5' ) "+CRLF
		cQry += " GROUP BY "+CRLF
		cQry += " Z9_CDPROD "+CRLF
		cQry += " ORDER BY 1 "+CRLF
>>>>>>> 691b22b758663a019968a75741f32b1aae05b7c3

	ENDIF

Return cQry

/*/{Protheus.doc} nomeStaticFunction
	(long_description)
	@type  Static Function
	@author Pedro Lindenberg
	@since 05/07/2024
/*/
Static Function fCalcPct(aValTot,nValAtu)
	Local nValCalc
	Local nSumTot := 0
	Local x

	for x := 1 to Len(aValTot)
		nSumTot += aValTot[x]
	next x

	nValCalc := (nValAtu * 100)/nSumTot

Return nValCalc

/*/{Protheus.doc} nomeStaticFunction
	(long_description)
	@type  Static Function
	@author Pedro Lindenberg
	@since 05/07/2024
/*/
Static Function fCalcTot(aValTot)
	Local nSumTot := 0
	Local x

	for x := 1 to Len(aValTot)
		nSumTot += aValTot[x]
	next x

Return nSumTot

/*/{Protheus.doc} nomeStaticFunction
	(long_description)
	@type  Static Function
	@author Pedro Lindenberg
	@since 05/07/2024
	@version version
/*/
Static Function fSumMod(cCodProd)
	Local cModAlias := GetNextAlias()
	Local cQryCMP := ""
	Local nTotMod := 0

	cQryCMP += " SELECT SUM(Z9_TOTAL) AS TOTAL FROM SZ9010 "+CRLF
<<<<<<< HEAD
  cQryCMP += " WHERE D_E_L_E_T_ = ' ' "+CRLF
  cQryCMP += " AND Z9_IDZ8 = "+valtosql(cCodProd)+" "+CRLF
	 cQryCMP += "AND Z9_FILIAL = "+valtosql(xFilial("SZ9"))+" "+CRLF
  cQryCMP += " AND SUBSTRING(Z9_CDPROD, 1, 3) = 'MOD' "+CRLF
=======
	cQryCMP += " WHERE D_E_L_E_T_ = ' ' "+CRLF
	cQryCMP += " AND Z9_IDZ8 = "+valtosql(cCodProd)+" "+CRLF
	cQryCMP += " AND SUBSTRING(Z9_CDPROD, 1, 3) = 'MOD' "+CRLF
>>>>>>> 691b22b758663a019968a75741f32b1aae05b7c3
	DBUseArea(.T., "TOPCONN", TCGENQRY(,, cQryCMP), cModAlias, .F., .T.)

	if (cModAlias)->(!Eof())
		nTotMod := (cModAlias)->TOTAL
	endif

Return nTotMod


/*/{Protheus.doc} nomeStaticFunction
	Busca quantidade dos produtos
	@type  Static Function
	@author Pedro Lindenberg
	@since 10/07/2024
/*/
Static Function fGetQtd(cProdCod,aItens)
	Local cQtdAlias := GetNextAlias()
	Local cQryCMP := ""
	Local aQtd := {}
	Local cItem1 := aItens[1]
	Local cItem2 := aItens[2]

<<<<<<< HEAD
		/*GABRIEL*/
		cQryCMP += " SELECT BM_GRUPO, Z9_CDPROD, "+CRLF
		cQryCMP += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(cItem1)+" THEN Z9_QUANT ELSE 0.00 END ) Z9_QUANT01, "+CRLF
		cQryCMP += " SUM     (CASE WHEN Z9_IDZ8 = "+valtosql(cItem2)+" THEN Z9_QUANT ELSE 0.00 END )  Z9_QUANT02 "+CRLF
		cQryCMP += " FROM dbo.SZ9010 (NOLOCK) TBL1 "+CRLF
		cQryCMP += " JOIN SBM010 SBM (NOLOCK) "+CRLF
		cQryCMP += " ON SBM.D_E_L_E_T_ = '' "+CRLF
		cQryCMP += " AND BM_GRUPO = SUBSTRING(Z9_CDPROD, 1, 4) "+CRLF
		cQryCMP += " WHERE TBL1.D_E_L_E_T_ = '' "+CRLF
		cQryCMP += " AND TBL1.Z9_IDZ8 IN ("+valtosql(cItem1)+" , "+valtosql(cItem2)+") "+CRLF
		cQryCMP += " AND Z9_FILIAL = "+valtosql(xFilial("SZ9"))+" "+CRLF
		cQryCMP += " AND Z9_ITEM = '001' AND 	Z9_IDFLD ='1PRD01' "+CRLF
		cQryCMP += " GROUP BY  BM_GRUPO, Z9_CDPROD "+CRLF
		cQryCMP += " ORDER BY 2 "+CRLF
		DBUseArea(.T., "TOPCONN", TCGENQRY(,, cQryCMP), cQtdAlias, .F., .T.)
=======
	/*GABRIEL*/
	cQryCMP += " SELECT BM_GRUPO, Z9_CDPROD, "+CRLF
	cQryCMP += " SUM(CASE WHEN Z9_IDZ8 = "+valtosql(cItem1)+" THEN Z9_QUANT ELSE 0.00 END ) Z9_QUANT01, "+CRLF
	cQryCMP += " SUM     (CASE WHEN Z9_IDZ8 = "+valtosql(cItem2)+" THEN Z9_QUANT ELSE 0.00 END )  Z9_QUANT02 "+CRLF
	cQryCMP += " FROM dbo.SZ9010 (NOLOCK) TBL1 "+CRLF
	cQryCMP += " JOIN SBM010 SBM (NOLOCK) "+CRLF
	cQryCMP += " ON SBM.D_E_L_E_T_ = '' "+CRLF
	cQryCMP += " AND BM_GRUPO = SUBSTRING(Z9_CDPROD, 1, 4) "+CRLF
	cQryCMP += " WHERE TBL1.D_E_L_E_T_ = '' "+CRLF
	cQryCMP += " AND TBL1.Z9_IDZ8 IN ("+valtosql(cItem1)+" , "+valtosql(cItem2)+") "+CRLF
	cQryCMP += " AND Z9_ITEM = '001' AND 	Z9_IDFLD ='1PRD01' "+CRLF
	cQryCMP += " GROUP BY  BM_GRUPO, Z9_CDPROD "+CRLF
	cQryCMP += " ORDER BY 2 "+CRLF
	DBUseArea(.T., "TOPCONN", TCGENQRY(,, cQryCMP), cQtdAlias, .F., .T.)
>>>>>>> 691b22b758663a019968a75741f32b1aae05b7c3

	if (cQtdAlias)->(!Eof())
		AADD(aQtd,(cQtdAlias)->Z9_QUANT01)
		AADD(aQtd,(cQtdAlias)->Z9_QUANT02)
	endif

	(cQtdAlias)->(DbCloseArea())

Return aQtd
