#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
#INCLUDE "TOPCONN.CH"

User Function DLP004()
	/*
	¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
	¦¦+-----------------------------------------------------------------------+¦¦
	¦¦¦PROGRAMA  ¦ DLP004   ¦ Autor ¦ Sérgio Alexandre      ¦ Data ¦ 11/06/07 ¦¦¦
	¦¦+----------+------------------------------------------------------------¦¦¦
	¦¦¦Descriçào ¦ Relatorio de Empenho de Produção                           ¦¦¦
	¦¦¦Alteracoes¦Roberto Fausto - TSC 243                                    ¦¦¦
	¦¦+-----------------------------------------------------------------------+¦¦
	¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
	¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
	*/

	if cEmpAnt =="05"
		MsgStop("Não é possivel utilizar esse relatorio na empresa 05", "Delpi")
		Return
	Endif

	cPerg := "DLP004"
	aRegistros := {}
	AADD(aRegistros,{cPerg,"01","De  Produto           ?","","","mv_ch1","C",15,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","SB1","","","","",""})
	AADD(aRegistros,{cPerg,"02","Ate Produto           ?","","","mv_ch2","C",15,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","SB1","","","","",""})
	AADD(aRegistros,{cPerg,"03","De  Emissao           ?","","","mv_ch3","D",08,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"04","Ate Emissao           ?","","","mv_ch4","D",08,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"05","Filtro Impressao      ?","","","mv_ch5","N",01,0,3,"C","","mv_par05","Nao Impressos","","","","","Já Impressos","","","","","Ambos","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"06","Marcar Impresso       ?","","","mv_ch6","N",01,0,1,"C","","mv_par06","Sim","","","","","Nao","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"07","Valores               ?","","","mv_ch7","N",01,0,1,"C","","mv_par07","Positivos","","","","","Negativos","","","","","Ambos","","","","","","","","","","","","","","","","","","",""})

	dbSelectArea("SX1")
	dbSeek(cPerg)
	If !Found()
		dbSeek(cPerg)
		While SX1->X1_GRUPO == cPerg .AND. !Eof()
			Reclock("SX1",.f.)
			dbDelete()
			MsUnlock("SX1")
			dbSkip()
		End
		For i:=1 to Len(aRegistros)
			RecLock("SX1",.T.)
			For j:=1 to FCount()
				FieldPut(j,aRegistros[i,j])
			Next
			MsUnlock("SX1")
		Next
	Endif
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Declaracao de Variaveis                                             ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	aOrd         := {"Codigo","Localizacao"}
	CbTxt        := ""
	cDesc1       := "Este programa tem como objetivo imprimir o   "
	cDesc2       := "empenho assignado para as ordens de producao."
	cDesc3       := ""
	cPict        := ""
	lEnd         := .F.
	lAbortPrint  := .F.
	cString      :="SF2"
	limite       :=132
	tamanho      := "M"
	nomeprog     := "DLP004" // Coloque aqui o nome do programa para impressao no cabecalho
	nTipo        := 18
	aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
	nLastKey     := 0
	cPerg        := "DLP004"
	titulo       := "Empenho de Producao"
	nLin         := 9//0
	nLIN2		 := 0
	nLIN3		 := 0
	Pergunte(cPerg,.F.)

	Cabec1       := "Codigo   | Descricao                                      UM | MAPA            |    Empenho | Estoque 99 | A  Liberar |  Estoque 01|"
	Cabec2       := ""
	//Cabec1     := "Codigo   | Descricao                                      UM | MAPA            |    Empenho | Estoque 99 | A  Liberar |      Total |"
	//Cabec2     := ""

	//               ZZZZZZZZ   ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ  ZZ   ZZZZ              999,999.99   999,999.99   999,999.99   999,999.99
	//               123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012
	//                        1         2         3         4         5         6         7         8         9         10        11        12        13

	cbtxt      := Space(10)
	cbcont     := 00
	CONTFL     := 01
	m_pag      := 01
	imprime      := .T.
	wnrel      := "DLP004" // Coloque aqui o nome do arquivo usado para impressao em disco


	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Monta a interface padrao com o usuario...                           ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	wnrel := SetPrint(cString,NomeProg,cPerg,@titulo,cDesc1,cDesc2,cDesc3,.F.,aOrd,.T.,Tamanho)

	If nLastKey == 27
		Return
	Endif

	SetDefault(aReturn,cString)

	If nLastKey == 27
		Return
	Endif

	nTipo := If(aReturn[4]==1,15,18)

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Processamento. RPTSTATUS monta janela com a regua de processamento. ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	RptStatus({|| RunReport(Cabec1,Cabec2,Titulo,nLin) },Titulo)
Return

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºFun‡„o    ³RUNREPORT º Autor ³ AP5 IDE            º Data ³  09/01/01   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescri‡„o ³ Funcao auxiliar chamada pela RPTSTATUS. A funcao RPTSTATUS º±±
±±º          ³ monta a janela com a regua de processamento.               º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Programa principal                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

Static Function RunReport(Cabec1,Cabec2,Titulo,nLin)

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

	cQuery := "SELECT D4_COD, B1_DESC, B1_UM, BZ_MPLOCAL, "
	// Valor dentro da data, e filtrado por impressão
	cQuery += "  SUM(CASE "
	cQuery += "        WHEN D4_DATA >= '" + DToS(dEMISSAO_INI) + "' AND D4_DATA <= '" + DToS(dEMISSAO_FIM) + "' "
	If nFILTRO == 1
		cQuery += "  AND D4_IMPRESS <> 'S' "
	ElseIf nFILTRO == 2
		cQuery += "  AND D4_IMPRESS = 'S' "
	EndIf
	cQuery += "          THEN D4_QUANT "
	cQuery += "        ELSE 0 END) D4_QUANT, "
	// Saldo apenas até a data final (e não saldo completo)
	cQuery += "  SUM(CASE "
	cQuery += "        WHEN D4_DATA <= '" + DToS(dEMISSAO_FIM) + "' "
	cQuery += "          THEN D4_QUANT "
	cQuery += "        ELSE 0 END) D4_TOTAL "
	// fim da query...
	cQuery += "FROM "
	cQuery += "  " + RetSqlName("SD4") + " SD4, "
	cQuery += "  " + RetSqlName("SB1") + " SB1, "
	cQuery += "  " + RetSqlName("SBZ") + " SBZ "
	cQuery += "WHERE "
	cQuery += "  B1_COD = D4_COD AND "
	cQuery += "  SB1.D_E_L_E_T_ = '' AND "
	cQuery += "  B1_FILIAL = '" + xFilial("SB1") + "' AND "
	cQuery += "  SD4.D_E_L_E_T_ = '' AND "
	cQuery += "  D4_FILIAL = '" + xFilial("SD4") + "' AND "
	cQuery += "  D4_COD >= '" + cCOD_INI + "' AND "
	cQuery += "  D4_COD <= '" + cCOD_FIM + "' AND "
	cQuery += "  D4_QUANT > 0 AND "
	cQuery += "  BZ_FILIAL = '" + xFilial("SBZ") + "' AND "
	cQuery += "  SBZ.D_E_L_E_T_ = '' AND "
	cQuery += "  BZ_COD = B1_COD "
	cQuery += "GROUP BY D4_COD, B1_DESC, B1_UM, BZ_MPLOCAL "
	If	aReturn[8] == 1
		cQuery += "ORDER BY D4_COD "
	Else
		cQuery += "ORDER BY BZ_MPLOCAL "
	EndIF
	If ( Select ( "TRBSD4" ) <> 0 )
		dbSelectArea ( "TRBSD4" )
		dbCloseArea ()
	End
	TCQuery cQuery NEW ALIAS "TRBSD4"

	dbSelectArea("TRBSD4")
	DbGoTop()
	SetRegua(Reccount())
	While !Eof()
		Incregua()
		//fCabec2() //ROBERTO TSC 243 - TIRADO EM FUNCAO DE PULAR LINHA EM BRANCO
		nQtd99 := 0
		nQtd01 := 0
		dbSelectArea("SB2")
		DbSetOrder(1)
		If (DbSeek(xFilial("SB2") + TRBSD4->D4_COD + '99'))
			nQtd99 := SB2->B2_QATU
		EndIf
		nALiberar := TRBSD4->D4_TOTAL - nQtd99
		//ROBERTO TSC 243
		If (DbSeek(xFilial("SB2") + TRBSD4->D4_COD + '01'))
			nQtd01 := SB2->B2_QATU
		EndIf
		fCabec2()// FUNCAO FORA DA CONDICAO
		//Cabec1     := "Codigo   | Descricao                                      UM | MAPA            |    Empenho | Estoque 99 | A  Liberar |      Total |"
		//Cabec2     := ""

		//               ZZZZZZZZ   ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ  ZZ   ZZZZ              999,999.99   999,999.99   999,999.99   999,999.99
		//               123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012
		//                        1         2         3         4         5         6         7         8         9         10        11        12        13

		//ROBERTO TSC 243
		IF nALiberar >0 .AND. nTipoVal == 1// .and. nTipoVal == 1nALiberar < 0// .and. nTipoVal == 1
			@ iLinha, 000 PSay AllTrim(TRBSD4->D4_COD)
			@ iLinha, 011 PSay SUBSTR(TRBSD4->B1_DESC,1,46)//ROBERTO TSC 243
			//ROBERTO TSC 243 - POSICAO DO ITEM NO ALMOXARIFADO.
			@ iLinha, 058 PSay TRBSD4->B1_UM
			@ iLinha, 063 PSay TRBSD4->BZ_MPLOCAL
			@ iLinha, 082 PSay Transform(TRBSD4->D4_QUANT, '@E 999,999.99')
			@ iLinha, 095 PSay Transform(nQtd99,           '@E 999,999.99')
			@ iLinha, 108 PSay Transform(nALiberar,        '@E 999,999.99')
			//	@ iLinha, 118 PSay Transform(TRBSD4->D4_TOTAL, '@E 999,999.99')
			@ iLinha, 121 PSay Transform(nQtd01, '@E 999,999.99')
			iLinha := iLinha + 1
			//fCabec2()// INICIALIZADA A FUNCAO FORA DA CONDICAO
		ENDIF
		IF nALiberar < 0 .AND. nTipoVal == 2
			@ iLinha, 000 PSay AllTrim(TRBSD4->D4_COD)
			@ iLinha, 011 PSay SUBSTR(TRBSD4->B1_DESC,1,46)//ROBERTO TSC 243
			@ iLinha, 058 PSay TRBSD4->B1_UM
			@ iLinha, 063 PSay TRBSD4->BZ_MPLOCAL
			@ iLinha, 082 PSay Transform(TRBSD4->D4_QUANT, '@E 999,999.99')
			@ iLinha, 095 PSay Transform(nQtd99,           '@E 999,999.99')
			@ iLinha, 108 PSay Transform(nALiberar,        '@E 999,999.99')
			@ iLinha, 121 PSay Transform(nQtd01, '@E 999,999.99')
			iLinha := iLinha + 1
			//fCabec2()// INICIALIZADA A FUNCAO FORA DA CONDICAO
		ENDIF

		IF nTipoVal == 3
			@ iLinha, 000 PSay AllTrim(TRBSD4->D4_COD)
			@ iLinha, 011 PSay SUBSTR(TRBSD4->B1_DESC,1,45)//ROBERTO TSC 243
			@ iLinha, 058 PSay TRBSD4->B1_UM
			@ iLinha, 063 PSay TRBSD4->BZ_MPLOCAL
			@ iLinha, 082 PSay Transform(TRBSD4->D4_QUANT, '@E 999,999.99')
			@ iLinha, 095 PSay Transform(nQtd99,           '@E 999,999.99')
			@ iLinha, 108 PSay Transform(nALiberar,        '@E 999,999.99')
			@ iLinha, 121 PSay Transform(nQtd01, '@E 999,999.99')
			iLinha := iLinha + 1
			//fCabec2()//INICIALIZADA A FUNCAO FORA DA CONDICAO
		ENDIF

		dbSelectArea("TRBSD4")
		DbSkip()
	EndDo
	fCabec2()
	iLinha := iLinha + 1//VER
	//@ iLinha, 0 PSAY Repl('*',132²)

	If nMARCAR == 1
		cQuery := "UPDATE " + RetSqlName("SD4") + " SET D4_IMPRESS = 'S' WHERE "
		cQuery += "  D_E_L_E_T_ = '' AND "
		cQuery += "  D4_FILIAL = '" + xFilial("SD4") + "' AND "
		cQuery += "  D4_COD >= '" + cCOD_INI + "' AND "
		cQuery += "  D4_COD <= '" + cCOD_FIM + "' AND "
		cQuery += "  D4_DATA >= '" + DToS(dEMISSAO_INI) + "' AND "
		cQuery += "  D4_DATA <= '" + DToS(dEMISSAO_FIM) + "' AND "
		cQuery += "  D4_IMPRESS <> 'S' AND "
		cQuery += "  D4_QUANT > 0 "
		TcSqlExec(cQuery)
	EndIf

	If aReturn[5]==1
		dbCommitAll()
		SET PRINTER TO
		OurSpool(wnrel)
	Endif

	MS_FLUSH()

Return

// Substituido pelo assistente de conversao do AP5 IDE em 02/05/01 ==> Function Cabec1
Static Function fCabec2()
	*************************
	//iLinha := iLinha + 1
	If iLinha > 60
		Cabec(Titulo,Cabec1,Cabec2,WnRel,Tamanho,nTipo)
		iLinha := 8
	Endif
Return
