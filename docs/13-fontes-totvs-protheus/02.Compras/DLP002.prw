#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
#INCLUDE "TOPCONN.CH"

User Function DLP002()
	/*
	¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
	¦¦+-----------------------------------------------------------------------+¦¦
	¦¦¦PROGRAMA  ¦ DLP002   ¦ Autor ¦ Diego Folchini        ¦ Data ¦ 07/03/07 ¦¦¦
	¦¦+----------+------------------------------------------------------------¦¦¦
	¦¦¦Descriçào ¦ Relatorio de Pontualidade de Entrega dos Pedidos           ¦¦¦
	¦¦¦          ¦                                                            ¦¦¦
	¦¦+-----------------------------------------------------------------------+¦¦
	¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
	¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
	*/

	cPerg := "DLP002"
	aRegistros := {}
	AADD(aRegistros,{cPerg,"01","De  Cliente           ?","","","mv_ch1","C",06,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","SA1","","","","",""})
	AADD(aRegistros,{cPerg,"02","De  Loja              ?","","","mv_ch2","C",02,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"03","Ate Cliente           ?","","","mv_ch3","C",06,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","SA1","","","","",""})
	AADD(aRegistros,{cPerg,"04","Ate Loja              ?","","","mv_ch4","C",02,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"05","De  Emissao           ?","","","mv_ch5","D",08,0,0,"G","","mv_par05","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"06","Ate Emissao           ?","","","mv_ch6","D",08,0,0,"G","","mv_par06","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"07","De  Prev. Entrega     ?","","","mv_ch7","D",08,0,0,"G","","mv_par07","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"08","Ate Prev. Entrega     ?","","","mv_ch8","D",08,0,0,"G","","mv_par08","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})

	dbSelectArea("SX1")
	dbSeek(cPerg)
	If !Found()
		dbSeek(cPerg)
		While SX1->X1_GRUPO==cPerg.and.!Eof()
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

	aOrd := {}
	CbTxt        := ""
	cDesc1         := "Este programa tem como objetivo imprimir a    "
	cDesc2         := "pontualidade de entrega dos pedidos de venda."
	cDesc3         := ""
	cPict          := ""
	lEnd         := .F.
	lAbortPrint  := .F.
	cString      :="SF2"
	limite       :=132
	tamanho      := "M"
	nomeprog     := "DLP002" // Coloque aqui o nome do programa para impressao no cabecalho
	nTipo        := 18
	aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
	nLastKey     := 0
	cPerg        := "DLP002"
	titulo       := "Pontualidade de Entrega dos Pedidos"
	nLin         := 0
	nLIN2		 := 0
	nLIN3		 := 0
	pergunte(cPerg,.F.)

	Cabec1       := "Pedido Nota Fiscal  Serie Produto  Descrição                                Dt Entrega  Dt Emissao   DF     % "
	//               999999 999999         99  99999999  9999999999999999999999999999999999999999 99/99/9999  99/99/9999  99  999.99
	Cabec2       := ""

	cbtxt      := Space(10)
	cbcont     := 00
	CONTFL     := 01
	m_pag      := 01
	imprime      := .T.
	wnrel      := "DLP002" // Coloque aqui o nome do arquivo usado para impressao em disco


	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Monta a interface padrao com o usuario...                           ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	wnrel := SetPrint(cString,NomeProg,cPerg,@titulo,cDesc1,cDesc2,cDesc3,.F.,aOrd,.T.,Tamanho,,.F.)

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

	sCliIni := mv_par01
	sLojaIn := mv_par02
	sCliFin := mv_par03
	sLojaFi := mv_par04
	dDatIni := mv_par05
	dDatFin := mv_par06
	dEntIni := mv_par07
	dEntFin := mv_par08
	nQuaPon := 0
	nQuanpon:= 0
	nTotal  := 0
	Setprc(0,0)
	iPag := 0
	iLinha := 100

	cQuery := "SELECT D2_PEDIDO,D2_DOC,D2_SERIE,C6_PRODUTO,C6_DESCRI,C6_ENTREG,D2_EMISSAO "
	cQuery += "FROM " + RetSqlName("SD2") + " SD2, " + RetSqlName("SC6") + " SC6 "
	cQuery += "WHERE D2_PEDIDO=C6_NUM AND D2_COD=C6_PRODUTO AND D2_ITEMPV=C6_ITEM AND D2_TES<>'525' "
	cQuery += "AND D2_FILIAL='"+xFilial("SD2")+"' AND C6_FILIAL='"+xFilial("SC6")+"' "
	cQuery += "AND D2_CLIENTE>='"+sCliIni+"' AND D2_CLIENTE<='"+sCliFin+"' "
	cQuery += "AND D2_LOJA>='"+sLojaIn+"' AND D2_LOJA<='"+sLojaFi+"' "
	cQuery += "AND D2_EMISSAO>='"+DTOS(dDatIni)+"' AND D2_EMISSAO <='"+DTOS(dDatFin)+"' "
	cQuery += "AND C6_ENTREG>='"+DTOS(dEntIni)+"' AND C6_ENTREG<='"+DTOS(dEntFin)+"' "
	cQuery += "AND SD2.D_E_L_E_T_='' AND SC6.D_E_L_E_T_='' "
	cQuery += "ORDER BY D2_PEDIDO "

	If ( Select ( "TRBSD2" ) <> 0 )
		dbSelectArea ( "TRBSD2" )
		dbCloseArea ()
	End
	TCQuery cQuery NEW ALIAS "TRBSD2"


	dbSelectArea("TRBSD2")
	DbGoTop()
	SetRegua(Reccount())
	While !Eof()
		Incregua()
		fCabec2()
		@ iLinha, 000 PSAY TRBSD2->D2_PEDIDO
		@ iLinha, 009 PSAY TRBSD2->D2_DOC
		@ iLinha, 022 PSAY TRBSD2->D2_SERIE
		@ iLinha, 026 PSAY TRBSD2->C6_PRODUTO
		@ iLinha, 036 PSAY TRBSD2->C6_DESCRI
		@ iLinha, 077 PSAY STOD(TRBSD2->C6_ENTREG)
		@ iLinha, 089 PSAY STOD(TRBSD2->D2_EMISSAO)
		@ iLinha, 101 PSAY Right(Str(STOD(TRBSD2->D2_EMISSAO)-STOD(TRBSD2->C6_ENTREG)), 3)
		if (STOD(TRBSD2->D2_EMISSAO)-STOD(TRBSD2->C6_ENTREG))<=0
			@ iLinha, 108 PSAY '100%'
			nQuaPon := nQuaPon + 1
		else
			@ iLinha, 108 PSAY '  0%'
			nQuanpon := nQuanpon + 1
		endif

		nTotal := nTotal + 1
		DbSelectArea("TRBSD2")
		DbSkip()
	EndDo
	fCabec2()
	@ iLinha, 0 PSAY Repl(' ',132)
	fCabec2()
	@ iLinha, 0 PSAY Repl('*',132)
	fCabec2()
	@ iLinha, 0 PSAY "Prazo de entrega atendido:     "+Str(Round((nQuaPon*100)/nTotal,2))+"%"
	fCabec2()
	@ iLinha, 0 PSAY Repl('',132)
	fCabec2()
	@ iLinha, 0 PSAY "Prazo de entrega não atendido: "+Str(Round((nQuanpon*100)/nTotal,2))+"%"
	fCabec2()
	@ iLinha, 0 PSAY Repl('*',132)
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
	iLinha := iLinha + 1
	If iLinha > 60
		Cabec(Titulo,Cabec1,Cabec2,WnRel,Tamanho,nTipo)
		iLinha := 8
	Endif
Return