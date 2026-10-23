#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
//#INCLUDE "TOPCONN.CH"

User Function DLP010()
	/*
	¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
	¦¦+-----------------------------------------------------------------------+¦¦
	¦¦¦PROGRAMA  ¦ DLP010   ¦ Autor ¦ Diego Folchini        ¦ Data ¦ 07/03/07 ¦¦¦
	¦¦+----------+------------------------------------------------------------¦¦¦
	¦¦¦Descriçào ¦ Relatorio de Pontualidade de Entrega dos Pedidos           ¦¦¦
	¦¦¦          ¦                                                            ¦¦¦
	¦¦+-----------------------------------------------------------------------+¦¦
	¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
	¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
	*/

	cPerg := "DLP010"
	/*aRegistros := {}
	AADD(aRegistros,{cPerg,"01","Produto               ?","","","mv_ch1","C",15,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","SB1","","","","",""})
	AADD(aRegistros,{cPerg,"02","Local                 ?","","","mv_ch2","C",02,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"03","De  Periodo           ?","","","mv_ch3","D",08,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
	AADD(aRegistros,{cPerg,"04","Ate Periodo           ?","","","mv_ch4","D",08,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})

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
	Endif*/
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Declaracao de Variaveis                                             ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	aOrd := {}
	CbTxt        := ""
	cDesc1         := "Este programa tem como objetivo imprimir a    "
	cDesc2         := "Extrato de Compra de Produtos."
	cDesc3         := ""
	cPict          := ""
	lEnd         := .F.
	lAbortPrint  := .F.
	cString      :="SB1"
	limite       :=080
	tamanho      := "G"
	nomeprog     := "DLP010" // Coloque aqui o nome do programa para impressao no cabecalho
	nTipo        := 18
	//aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
	nLastKey     := 0
	cPerg        := "DLP010"
	titulo       := "Extrato de Compra de Produtos"
	nLin         := 0
	nLIN2		 := 0
	nLIN3		 := 0

	Private aReturn          := { "Zebrado", 1, "Administracao", 2, 2, 1, "", 1}

	//Private cString := "SB1"
	pergunte(cPerg,.F.)

	Cabec1       := "DATA       TP DOC       DOCUMENTO          EMPENHO          PEDIDO                          SALDO"
	//               99;99;99   9999999999   999999      999.999,999,99  999.999,999.99  9,999,999.99
	//               01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
	//               0         1         2         3         4         5         6         7         8         9         10
	Cabec2       := ""

	cbtxt      := Space(10)
	cbcont     := 00
	CONTFL     := 01
	m_pag      := 01
	imprime    := .T.
	wnrel      := "DLP010" // Coloque aqui o nome do arquivo usado para impressao em disco


	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Monta a interface padrao com o usuario...                           ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	wnrel := SetPrint(cString,NomeProg,cPerg,@titulo,cDesc1,cDesc2,cDesc3,.F.,aOrd,.T.,Tamanho,,.F.)

	If nLastKey == 27
		Return
	Endif

	SetDefault(aReturn,cString,/*uParm3*/,/*lNoAsk*/,/*cSize*/,/*nFormat*/2)

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

	dEntIni := mv_par01
	dEntFin := mv_par02
	Setprc(0,0)
	iPag := 0
	iLinha := 100

	nPonSim := 0
	nPonNao := 0
	nTotal  := 0

	aEstru  := array(6,4)
	aEstru[01] := { "TR_DATA"   ,"D",08,0 }
	aEstru[02] := { "TR_TPDOC"  ,"C",10,0 }
	aEstru[03] := { "TR_DOC"    ,"C",11,0 }
	aEstru[04] := { "TR_QTDEMP" ,"N",14,2 }
	aEstru[05] := { "TR_QTDPED" ,"N",14,2 }
	aEstru[06] := { "TR_NSALDO" ,"N",14,2 }

	If ( Select ( "TRB01" ) <> 0 )
		dbSelectArea ( "TRB01" )
		dbCloseArea ()
	End
	cNomeArq := CriaTrab ( aEstru )
	dbUseArea ( .T.,, cNomeArq, "TRB01", NIL, .F. )
	IndRegua("TRB01",cNomeArq,"DTOS(TR_DATA)",,,"Selecionando registros...")

	dbSelectArea("SB1")
	DbSetOrder(1)
	DbGoTop()
	iF (DbSeek(xFilial("SB1")+MV_PAR01))
		dbSelectArea("SB2")
		DbSetOrder(1)
		nSaldo :=0
		If (DbSeek(xFilial("SB2") + SB1->B1_COD + '01'))
			nSaldo +=SB2->B2_QATU
		EndIf
		If (DbSeek(xFilial("SB2") + SB1->B1_COD + '99'))
			nSaldo +=SB2->B2_QATU
		EndIf
		fCabec2()
		//@ iLinha, 000 PSAY "Produto:"+ Left(SB1->B1_COD,12) + "-" + Left(SB1->B1_DESC,40)
		@ iLinha, 000 PSAY "Produto:"+ Left(SB1->B1_COD,12) + "-" + SB1->B1_DESC
		fCabec2()

		/*+++++++++++++++++++*/
		dbSelectArea("SBZ")    // Gilson 160313
		SBZ->(dbSetOrder(1))
		If SBZ->(dbSeek(xFilial("SBZ")+SB1->B1_COD))
			@ iLinha, 000 PSAY "Segur. :"+ Transform(SBZ->BZ_ESTSEG ,"@E 9,999,999.99 ")     //Gilson 160813
		Else
			@ iLinha, 000 PSAY "Segur. :"+ Transform(0 ,"@E 9,999,999.99 ")     //Gilson 160813
		EndIf
		SBZ->(dbCloseArea())
		/*+++++++++++++++++++*/

		dbSelectArea("SA5")
		dbSetorder(2)
		dbSeek(xFilial("SA5")+SB1->B1_COD,.T.)
		While !eof() .And. xFilial("SA5")+SB1->B1_COD == SA5->A5_FILIAL + SA5->A5_PRODUTO
			sNome := ''
			DbSelectArea("SA2")
			DbSetOrder(1)
			If (DbSeek(xFilial("SA2")+SA5->A5_FORNECE+SA5->A5_LOJA))
				sNome := SA2->A2_NOME
			EndIf
			dbSelectArea("SA5")
			fCabec2()
			@ iLinha, 000 PSAY "Fornec.:"+ SA5->A5_FORNECE+'-'+SA5->A5_LOJA+'  '+sNome +  ' Part Number:'+SA5->A5_CODPRF
			DbSkip()
		EndDo

		dbSelectArea("SD4")
		DbSetOrder(3)
		DbGoTop()
		DbSeek(xFilial("SD4")+SB1->B1_COD+"99"+DTOS(MV_PAR03),.T.)
		While !Eof()  .And. SD4->D4_FILIAL+SD4->D4_COD+SD4->D4_LOCAL+DTOS(SD4->D4_DATA) >=  xFilial("SD4")+SB1->B1_COD+"99"+DTOS(MV_PAR03) .And. ;
				SD4->D4_FILIAL+SD4->D4_COD+SD4->D4_LOCAL+DTOS(SD4->D4_DATA) <=  xFilial("SD4")+SB1->B1_COD+"99"+DTOS(MV_PAR04)
			IF SD4->D4_QUANT> 0
				dbSelectArea("TRB01")
				Reclock("TRB01",.T.)
				TRB01->TR_DATA := SD4->D4_DATA
				TRB01->TR_TPDOC:= "EMPENHO"
				TRB01->TR_DOC  := SD4->D4_OP
				TRB01->TR_QTDEMP  := SD4->D4_QUANT
				TRB01->TR_QTDPED  := 0
				MsUnlock("TRB01")
			EndIf
			dbSelectArea("SD4")
			DbSkip()
		EndDo

		dbSelectArea("SD4")
		DbSetOrder(3)
		DbGoTop()
		DbSeek(xFilial("SD4")+SB1->B1_COD+MV_PAR02+DTOS(MV_PAR03),.T.)
		While !Eof()  .And. SD4->D4_FILIAL+SD4->D4_COD+SD4->D4_LOCAL+DTOS(SD4->D4_DATA) >=  xFilial("SD4")+SB1->B1_COD+MV_PAR02+DTOS(MV_PAR03) .And. ;
				SD4->D4_FILIAL+SD4->D4_COD+SD4->D4_LOCAL+DTOS(SD4->D4_DATA) <=  xFilial("SD4")+SB1->B1_COD+MV_PAR02+DTOS(MV_PAR04)
			IF SD4->D4_QUANT> 0
				dbSelectArea("TRB01")
				Reclock("TRB01",.T.)
				TRB01->TR_DATA := SD4->D4_DATA
				TRB01->TR_TPDOC:= "EMPENHO"
				TRB01->TR_DOC  := SD4->D4_OP
				TRB01->TR_QTDEMP  := SD4->D4_QUANT
				TRB01->TR_QTDPED  := 0
				MsUnlock("TRB01")
			EndIf
			dbSelectArea("SD4")
			DbSkip()
		EndDo
		dbSelectArea("SC6")
		DbSetOrder(2)
		DbGoTop()
		DbSeek(xFilial("SC6")+SB1->B1_COD,.T.)
		While !Eof()
			if  SC6->C6_FILIAL+SC6->C6_PRODUTO+DTOS(SC6->C6_ENTREG) >=  xFilial("SD4")+SB1->B1_COD+DTOS(MV_PAR03) .And. ;
					SC6->C6_FILIAL+SC6->C6_PRODUTO+DTOS(SC6->C6_ENTREG) <=  xFilial("SD4")+SB1->B1_COD+DTOS(MV_PAR04)
				If (SC6->C6_BLQ  == "N"  .OR. Empty(SC6->C6_BLQ )) .AND.  (SC6->C6_QTDVEN - SC6->C6_QTDENT)>0
					dbSelectArea("TRB01")
					Reclock("TRB01",.T.)
					TRB01->TR_DATA := SC6->C6_ENTREG
					TRB01->TR_TPDOC:= "PED VENDA"
					TRB01->TR_DOC  := SC6->C6_NUM
					TRB01->TR_QTDEMP  := 0
					TRB01->TR_QTDPED  := (SC6->C6_QTDVEN - SC6->C6_QTDENT)
					MsUnlock("TRB01")
				EndIf
			EndIf
			dbSelectArea("SC6")
			if  SC6->C6_FILIAL+SC6->C6_PRODUTO+DTOS(SC6->C6_ENTREG)> xFilial("SD4")+SB1->B1_COD+DTOS(MV_PAR04)
				exit
			endif
			DbSkip()
		EndDo

		dbSelectArea("SC7")
		DbSetOrder(7)
		DbGoTop()
		DbSeek(xFilial("SC7")+SB1->B1_COD+DTOS(MV_PAR03),.T.)
		While !Eof()  .And. SC7->C7_FILIAL+SC7->C7_PRODUTO+DTOS(SC7->C7_DATPRF) >=  xFilial("SD4")+SB1->B1_COD+DTOS(MV_PAR03) .And. ;
				SC7->C7_FILIAL+SC7->C7_PRODUTO+DTOS(SC7->C7_DATPRF) <=  xFilial("SD4")+SB1->B1_COD+DTOS(MV_PAR04)
			If SC7->C7_ENCER <> "E"  .And. Empty(SC7->C7_RESIDUO)
				dbSelectArea("TRB01")
				Reclock("TRB01",.T.)
				TRB01->TR_DATA := SC7->C7_DATPRF
				TRB01->TR_TPDOC:= "PEDIDOS"
				TRB01->TR_DOC  := SC7->C7_NUM
				TRB01->TR_QTDEMP  := 0
				TRB01->TR_QTDPED  := (SC7->C7_QUANT - SC7->C7_QUJE)
				MsUnlock("TRB01")
			EndIf
			dbSelectArea("SC7")
			DbSkip()
		EndDo

		dbSelectArea("SC1")
		Dbsetorder(11)
		DbGoTop()
		DbSeek(xFilial("SC1")+MV_PAR02+SB1->B1_COD+DTOS(MV_PAR03),.T.)
		While !Eof()  .And. SC1->C1_FILIAL+SC1->C1_LOCAL+SC1->C1_PRODUTO+DTOS(SC1->C1_DATPRF) >=  xFilial("SC1")+MV_PAR02+SB1->B1_COD+DTOS(MV_PAR03) .And. ;
				SC1->C1_FILIAL+SC1->C1_LOCAL+SC1->C1_PRODUTO+DTOS(SC1->C1_DATPRF) <=  xFilial("SC1")+MV_PAR02+SB1->B1_COD+DTOS(MV_PAR04)
			If Empty(SC1->C1_COTACAO) .And. Empty(SC1->C1_RESIDUO)
				dbSelectArea("TRB01")
				Reclock("TRB01",.T.)
				TRB01->TR_DATA := SC1->C1_DATPRF
				TRB01->TR_TPDOC:= "SOLICIT"
				TRB01->TR_DOC  := SC1->C1_NUM
				TRB01->TR_QTDEMP  := 0
				TRB01->TR_QTDPED  := SC1->C1_QUANT
				MsUnlock("TRB01")
			EndIf
			dbSelectArea("SC1")
			DbSkip()
		EndDo
		fCabec2()
		fCabec2()
		@ iLinha, 080 PSAY "SALDO:"
		@ iLinha, 088 PSAY nsaldo  PICTURE "@E 9,999,999.99"

		dbSelectArea("TRB01")
		DbGoTop()
		While !Eof()
			fCabec2()
			@ iLinha, 000 PSAY TRB01->TR_DATA
			@ iLinha, 011 PSAY TRB01->TR_TPDOC
			/*		@ iLinha, 024 PSAY TRB01->TR_DOC
			@ iLinha, 040 PSAY TRB01->TR_QTDEMP  PICTURE "@E 999,999,999.99"*/
			@ iLinha, 020 PSAY TRB01->TR_DOC
			@ iLinha, 036 PSAY TRB01->TR_QTDEMP  PICTURE "@E 999,999,999.99"
			@ iLinha, 056 PSAY TRB01->TR_QTDPED  PICTURE "@E 999,999,999.99"
			If Alltrim(TRB01->TR_TPDOC) $ "EMPENHO" .or. Alltrim(TRB01->TR_TPDOC) $ 'PED VENDA'
				nSaldo  -= TRB01->TR_QTDPED+TRB01->TR_QTDEMP
			Else
				nSaldo  += TRB01->TR_QTDPED+TRB01->TR_QTDEMP
			EndIf
			@ iLinha, 088 PSAY nSaldo  PICTURE "@E 999,999,999.99"
			dbSelectArea("TRB01")
			DbSkip()
		EndDo
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
	iLinha := iLinha + 1
	If iLinha > 70
		Cabec(Titulo,Cabec1,Cabec2,WnRel,Tamanho,nTipo)
		iLinha := 8
	Endif
Return
