/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DEL100    ºAutor  ³SERGIO ALEXANDRE    º Data ³  21/09/07   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³PROGRAMA PARA FECHAR ESTOQUE E CUSTO MEDIO                  º±±
±±º          ³                                                            º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
#Include "rwmake.ch"
#Include "topconn.ch"

User Function DEL100()
Local oPerg, cPerg := "DEL100"
oPerg := TPergunta():New(cPerg)
oPerg:AddGet  ("Data Fechamento ?", "D", 08, 0, Nil,               "",    "", "")
oPerg:AddGet  ("De Produto ?",          "C", 15, 0, "               ", "SB1", "", "")
oPerg:AddGet  ("Ate Produto ?",         "C", 15, 0, "ZZZZZZZZZZZZZZZ", "SB1", "", "")
oPerg:AddGet  ("De Local ?",            "C", 02, 0, "01",              "",    "", "")
oPerg:AddGet  ("Ate Local ?",           "C", 02, 0, "99",              "",    "", "")
oPerg:AddCombo("Modo Execucao ?", { "Alteracao", "Somente Log" }, 1)
oPerg:Update()
If oPerg:Execute(.T.)
	Processa({ || fDEL100() }, "Recalculando Fechamentos... Aguarde...")
EndIf
Return

******************************
Static FUNCTION fDEL100()
******************************
Local dDataFim  := Mv_Par01,;
cProdIni  := Mv_Par02,;
cProdFim  := Mv_Par03,;
cLocalIni := Mv_Par04,;
cLocalFim := Mv_Par05,;
lAlterar  := Mv_Par06 == 1
Local nVIni1, nQtde, oLog, cLog := "TRBLOG", dDataIni
oLog := TWorkFile():New(cLog)
oLog:AddField("TR_COD",   "C", 15, 0)
oLog:AddField("TR_LOCAL", "C", 02, 0)
oLog:AddField("TR_OPER",  "C", 01, 0) // 0 SEM INICIO, 1 = INICIO, 2 = FIM, 3 = SEM FIM
oLog:AddField("TR_DATA",  "D", 08, 0)
oLog:AddField("TR_QTD1",  "N", 16, 4)
oLog:AddField("TR_VAL1",  "N", 16, 4)
oLog:AddField("TR_QTD2",  "N", 16, 4)
oLog:AddField("TR_VAL2",  "N", 16, 4)
oLog:Create()
oLog:SortOn("TR_COD+TR_LOCAL+TR_OPER")

dDataIni := ctod("  /  /  ")
DbSelectArea("SB9")
DbSetOrder(2)
DbGoTop()
DbSeek(xFilial("SB9")+DToS(dDataFim),.t.)
iF !xFilial("SB9")+DToS(dDataFim) == SB9->B9_FILIAL+dTos(SB9->B9_DATA)
	Msgbox('Data De Fechamento Invalida!')
	Return
EndIf
DbSkip(-1)
iF xFilial("SB9")+DToS(dDataFim) > SB9->B9_FILIAL+dTos(SB9->B9_DATA)
	dDataIni := SB9->B9_DATA
EndIf

DbSelectArea("SB1")
DbSetOrder(1)
ProcRegua(RecCount())
DbSeek(xFilial("SB1")+cProdIni, .T.)
While !Eof() .And. SB1->B1_FILIAL+SB1->B1_COD <= xFilial("SB1")+cProdFim
	IncProc()
	DbSelectArea("SB2")
	DbSetOrder(1)
	DbSeek(xFilial("SB2")+SB1->B1_COD+cLocalIni, .T.)
	While !Eof() .AND. SB2->B2_FILIAL+SB2->B2_COD+SB2->B2_LOCAL <= xFilial("SB2")+SB1->B1_COD+cLocalFim
		nVIni1 := 0
		nQtde  := 0
		DbSelectArea("SB9")
		DbSetOrder(1)
		DbGoTop()
		If DbSeek(xFilial("SB9")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataIni))
			nVIni1 := SB9->B9_VINI1
			nQtde  := SB9->B9_QINI
			If lAlterar
				oLog:AppendRecord({SB2->B2_COD, SB2->B2_LOCAL, "1", dDataIni, nVIni1, nQtde, 0, 0 })
			EndIf
		EndIf
		DbSelectArea("SD3")
		DbSetOrder(7)
		DbSeek(xFilial("SD3")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataIni+1), .T.)
		While !Eof() .AND. SD3->D3_FILIAL+SD3->D3_COD+SD3->D3_LOCAL+DToS(SD3->D3_EMISSAO) <= xFilial("SD3")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataFim)
			If SD3->D3_ESTORNO != "S"
				If SD3->D3_TM < "500"
					nVIni1    += SD3->D3_CUSTO1
					nQtde     += SD3->D3_QUANT
				Else
					nVIni1    -= SD3->D3_CUSTO1
					nQtde     -= SD3->D3_QUANT
				EndIf
			EndIf
			dbSelectArea("SD3")
			DbSkip()
		EndDo
		DbSelectArea("SD1")
		DbSetOrder(7)
		DbSeek(xFilial("SD1")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataIni+1), .T.)
		While !Eof() .AND. SD1->D1_FILIAL+SD1->D1_COD+SD1->D1_LOCAL+DToS(SD1->D1_DTDIGIT) <= xFilial("SD1")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataFim)
			DbSelectArea ("SF4")
			DbSetOrder(1)
			If (DbSeek(xFilial("SF4")+SD1->D1_TES)) .And. SF4->F4_ESTOQUE == 'S'
				nVIni1    += SD1->D1_CUSTO
				nQtde     += SD1->D1_QUANT
			EndIf
			DbSelectArea("SD1")
			DbSkip()
		EndDo
		DbSelectArea("SD2")
		DbSetOrder(6)
		DbSeek(xFilial("SD2")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataIni+1), .T.)
		While !Eof() .AND. SD2->D2_FILIAL+SD2->D2_COD+SD2->D2_LOCAL+DToS(SD2->D2_EMISSAO) <= xFilial("SD2")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataFim)
			DbSelectArea ("SF4") //TES
			DbSetOrder(1)
			If (DbSeek(xFilial("SF4")+SD2->D2_TES)) .And. SF4->F4_ESTOQUE == "S"
				nVIni1    -= SD2->D2_TOTAL
				nQtde     -= SD2->D2_QUANT
			EndIf
			DbSelectArea("SD2")
			DbSkip()
		EndDo
		DbSelectArea("SB9")
		DbSetOrder(1)
		DbGoTop()
		If DbSeek(xFilial("SB9")+SB2->B2_COD+SB2->B2_LOCAL+DToS(dDataFim))
			If lAlterar .OR. SB9->B9_VINI1 <> nVIni1 .OR. SB9->B9_QINI  <> nQtde
				oLog:AppendRecord({SB2->B2_COD, SB2->B2_LOCAL, "2", dDataFim, SB9->B9_VINI1, SB9->B9_QINI, nVIni1, nQtde })
			EndIf
			If lAlterar .And. (SB9->B9_VINI1 <> nVIni1 .OR. SB9->B9_QINI  <> nQtde)
				RecLock("SB9", .F.)
				SB9->B9_VINI1 := nVIni1
				SB9->B9_QINI  := nQtde
				MsUnlock("SB9")
			EndIf
		Else
			oLog:AppendRecord({SB2->B2_COD, SB2->B2_LOCAL, "3", dDataFim, 0, 0, nVIni1, nQtde })
		EndIf
		DbSelectArea("SB2")
		DbSkip()
	EndDo
	DbSelectArea("SB1")
	DbSkip()
EndDo
If (cLog)->(RecCount()) > 0
	oLog:Display("Log",;
	{{"TR_COD",   "Produto"},;
	{"TR_LOCAL", "Local"},;
	{"TR_OPER",  "Status"},;
	{"TR_DATA",  "Data"},;
	{"TR_QTD1",  "Qtd. SB9"},;
	{"TR_VAL1",  "Val. SB9"},;
	{"TR_QTD2",  "Qtd. Calc."},;
	{"TR_VAL2",  "Val. Calc."}})
Else
	Aviso("DEL100", "Nao Foi Gerado Log do Processo!", { "OK" })
EndIf
Return
