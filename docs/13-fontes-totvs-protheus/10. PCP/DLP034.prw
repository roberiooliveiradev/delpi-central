#include 'protheus.ch'
#include 'parmtype.ch'

//--------------------------------------------------------------
/*/{Protheus.doc} DLP034
Impressao de Etiqueta de Embalagem para Apontamento de Producao
Utiliza classe MSCB para impressora termica Argox em rede Windows.
Substitui DLP033 + DLP10E01 (template .prn + ShellExecute).

@param xParam -
@return xRet  -
@author Marcos Alberto Schoeffel / Everton Boing
@since 27/10/2017
@update 06/05/2026
/*/
//--------------------------------------------------------------
User Function DLP034()

	Local oButton1
	Local oButton2
	Local oFont1 := TFont():New("Arial",,020,,.F.,,,,,.F.,.F.)
	Local oSay1
	Local oSay2
	Local oSay3
	Local oSay4
	Local oSay5
	Local oSay6
	Local oSay7
	Local oSay8
	Local oSay9
	Local oSay10

	Private oCod
	Private cCod := Space(TamSx3('B1_COD')[1])

	Private oCodCli
	Private cCodCli := Space(TamSx3('B1_REFEREN')[1])

	Private oDelpi

	Private oDesc
	Private cDesc := Space(TamSx3('B1_DESC')[1])
	Private oDescCli
	Private cDescCli := Space(TamSx3('A1_NOME')[1])

	Private oDtEmis
	Private dDtEmis := Stod('')
	Private oHora
	Private cHora := ''

	Private oDtApo
	Private dDtApo := Stod('')
	Private oGroup1
	Private oGroup2
	Private oGroup3
	Private oNumOP
	Private cNumOP := Space(TamSx3('D3_OP')[1])
	Private oPesoTotal
	Private nPesoTotal := 0
	Private nPesoEtiq  := 0
	Private oPesoUnit
	Private nPesoUnit := 0
	Private oQuant
	Private nQuant := 0
	Private lEdita := .T.

	Private oQtdPro
	Private nQtdPro := 0
	Private oQtdEmb
	Private nQtdEmb := 0
	Private nTotEtiq := 0
	Private oTotEtiq

	Static oDlg

	If	!IsInCallStack('MATA250')
		SC2->(DbSeek(xFilial('SC2')+'              '))

		SB1->(DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))

		SA1->(DbSeek(xFilial('SA1')+SC2->(C2_CLIDELP+C2_LOJDELP)))

		cNumOP    := SD3->D3_OP
		cCod      := SB1->B1_COD
		cDesc     := SB1->B1_DESC
		cCodCli   := SB1->B1_REFEREN
		cCodCliLj := SA1->A1_COD + SA1->A1_LOJA
		cDescCli  := SA1->A1_NREDUZ
		dDtEmis   := SC2->C2_EMISSAO
		dDtApo    := SC2->C2_EMISSAO
		cHora	  := SD3->D3_HORA
		nQuant    := SC2->C2_QUANT
		nQtdPro   := SC2->C2_QUANT
		nPesoUnit := SB1->B1_PESO
		nPesoTotal:= Round(SB1->B1_PESO * nQtdPro,2)
		nQtdEmb   := SB1->B1_EMBDELP
		nTotEtiq  := IIF((nQtdPro / nQtdEmb) < 1,1,(nQtdPro / nQtdEmb))
		nPesoEtiq := nPesoTotal/nTotEtiq

	Else

		SB1->(DbSeek(xFilial('SB1')+SD3->D3_COD))

		SC2->(DbSeek(xFilial('SC2')+M->D3_OP))

		SA1->(DbSeek(xFilial('SA1')+SC2->(C2_CLIDELP+C2_LOJDELP)))

		cNumOP    := M->D3_OP
		cCod      := M->D3_COD
		cDesc     := SB1->B1_DESC
		cCodCli   := SB1->B1_REFEREN
		cCodCliLj := SA1->A1_COD + SA1->A1_LOJA
		cDescCli  := SA1->A1_NREDUZ
		dDtEmis   := SC2->C2_EMISSAO
		dDtApo    := M->D3_EMISSAO
		cHora	  := M->D3_HORA
		nQuant    := SC2->C2_QUANT
		nQtdPro   := M->D3_QUANT
		nPesoUnit := SB1->B1_PESO
		nPesoTotal:= Round(SB1->B1_PESO * nQtdPro,2)
		nQtdEmb   := SB1->B1_EMBDELP
		nTotEtiq  := IIF((nQtdPro / nQtdEmb) < 1,1,(nQtdPro / nQtdEmb))
		nPesoEtiq := nPesoTotal/nTotEtiq

		lEdita := .F.
	EndIf


	DEFINE MSDIALOG oDlg TITLE "Dados Impressao Etiqueta Apontamento Producao" FROM 000, 000  TO 400, 500 COLORS 0, 16777215 PIXEL

	@ 004, 137 BITMAP oDelpi SIZE 103, 036 OF oDlg FILENAME "system\lgrl01.bmp" NOBORDER ADJUST PIXEL
	@ 009, 007 GROUP oGroup1 TO 038, 112 PROMPT "Numero da Ordem de Producao" OF oDlg COLOR 0, 16777215 PIXEL
	@ 019, 011 MSGET oNumOP VAR cNumOP F3 "SC2" Valid U_D034OP() SIZE 095, 013 OF oDlg PICTURE "@!" COLORS 255, 16777215 FONT oFont1 When lEdita PIXEL

	@ 044, 008 GROUP oGroup2 TO 111, 241 PROMPT "Informacoes da Ordem Producao" OF oDlg COLOR 0, 16777215 PIXEL
	@ 055, 013 SAY oSay1 PROMPT "Produto" SIZE 023, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 054, 037 MSGET oCod VAR cCod F3 'SB1' SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 054, 085 MSGET oDesc VAR cDesc SIZE 152, 010 OF oDlg PICTURE "@!" COLORS 0, 16777215 READONLY PIXEL
	@ 069, 013 SAY oSay2 PROMPT "Cliente" SIZE 024, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 068, 037 MSGET oCodCli VAR cCodCliLj F3 'SA1' SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 068, 085 MSGET oDescCli VAR cDescCli SIZE 152, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 082, 013 SAY oSay3 PROMPT "Emissao" SIZE 025, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 081, 037 MSGET oDtEmis VAR dDtEmis SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 082, 085 SAY oSay4 PROMPT "Apontamento" SIZE 034, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 081, 119 MSGET oDtApo VAR dDtApo SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 081, 167 MSGET oHora VAR cHora SIZE 032, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 097, 013 SAY oSay5 PROMPT "Qtd.a Produzir" SIZE 036, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 096, 050 MSGET oQuant VAR nQuant Picture X3Picture("C2_QUANT") SIZE 031, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 097, 085 SAY oSay6 PROMPT "Qtd.Produzida" SIZE 035, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 096, 120 MSGET oQtdPro VAR nQtdPro Picture X3Picture("C2_QUANT") Valid U_D034QPRO() SIZE 045, 010 OF oDlg COLORS 0, 16777215 PIXEL

	@ 120, 007 GROUP oGroup3 TO 172, 241 PROMPT "Dados Etiqueta" OF oDlg COLOR 0, 16777215 PIXEL

	@ 133, 012 SAY oSay7 PROMPT "Peso Unitario" SIZE 039, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 133, 065 MSGET oPesoUnit VAR nPesoUnit Picture X3Picture("B1_PESO") SIZE 042, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 133, 130 SAY oSay8 PROMPT "Peso Total" SIZE 031, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 133, 169 MSGET oPesoTotal VAR nPesoTotal Picture X3Picture("B1_PESO") SIZE 033, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 152, 012 SAY oSay9 PROMPT "Quantidade por Embalagem" SIZE 090, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 151, 079 MSGET oQtdEmb VAR nQtdEmb Valid U_D034QEmb() Picture X3Picture("B1_EMBDELP") SIZE 045, 010 OF oDlg COLORS 0, 16777215 PIXEL
	@ 152, 130 SAY oSay10 PROMPT "Total Etiquetas" SIZE 038, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 151, 169 MSGET oTotEtiq VAR nTotEtiq Picture '@E 9999' SIZE 033, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 183, 160 BUTTON oButton1 PROMPT "Imprimir" SIZE 037, 012 Action (U_Dlp034Printer(), oNumOP:SetFocus()) OF oDlg PIXEL
	@ 183, 203 BUTTON oButton2 PROMPT "Cancelar" SIZE 037, 012 Action (oDlg:End()) OF oDlg PIXEL

	ACTIVATE MSDIALOG oDlg CENTERED

Return


User Function D034QPRO()
	Local nCpo := &(ReadVar())

	nQtdEmb   := SB1->B1_EMBDELP
	nPesoTotal := Round( nPesoUnit * nQtdPro,3)
	If (nQtdPro / nQtdEmb) < 1
		nQtdEmb := nQtdPro
	EndIf

	nTotEtiq   := Round((nQtdPro / nQtdEmb),0)
	nPesoEtiq  := Round(nPesoTotal/nTotEtiq,3)
	oTotEtiq:Refresh()
	oPesoTotal:Refresh()
	oQtdEmb:Refresh()
Return

User Function D034QEmb()

	Local lRet := .T.
	Local nCpo := &(ReadVar())

	If	Empty(nCpo)
		ApMsgAlert('E obrigatorio o preenchimento da quantidade por embalagem !!!')
		Return (lRet := .F.)
	EndIf

	If	(nCpo > nQtdPro)
		ApMsgAlert('Quantidade por Embalagem nao pode ser maior que o Total Produzido !!!')
		Return (lRet := .F.)
	EndIf

	nTotEtiq   := Round(IIF((nQtdPro / nQtdEmb) < 1,1,(nQtdPro / nCpo)),0)
	nPesoTotal := Round( nPesoUnit * nQtdPro,3)
	nPesoEtiq  := Round(nPesoTotal/nTotEtiq,3)
	oTotEtiq:Refresh()
	oPesoTotal:Refresh()
	oQtdEmb:Refresh()

Return lRet


User Function D034OP()

	Local lRet := .T.
	Local cCpo := &(ReadVar())

	If	Empty(cCpo)
		cCod      := ''
		cDesc     := ''
		cCodCli   := ''
		cDescCli  := ''
		dDtEmis   := Stod('')
		cHora     := ''
		nQuant    := 0
		nQtdPro   := 0
		nPesoUnit := 0
		nPesoTotal:= 0
		nQtdEmb   := 0
		nTotEtiq  := 0
		oDlg:Refresh()
		Return (lRet)
	EndIf

	SC2->(DbSeek(xFilial('SC2')+cCpo))
	If	!SC2->(Found())
		ApMsgAlert('Numero de Ordem Producao nao existe !!!')
		Return (lRet := .F.)
	EndIf

	SB1->(DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))
	If	SB1->(Found())
		If	SB1->B1_TIPO != 'PA'
			ApMsgAlert('O Produto desta Ordem de Producao nao e um Produto Acabado, nao podera ser impresso Etiqueta !!!')
			Return (lRet := .F.)
		EndIf
	EndIf

	dbSelectArea("SD3")
	SD3->(dbSetOrder(1))
	SD3->(DbSeek(xFilial("SD3")+cCpo+SC2->C2_PRODUTO))

	SB1->(DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))

	SA1->(DbSeek(xFilial('SA1')+SC2->(C2_CLIDELP+C2_LOJDELP)))

	If	!IsInCallStack('MATA250')
		cCod      := SC2->C2_PRODUTO
		cDesc     := SB1->B1_DESC
		cCodCli   := SB1->B1_REFEREN
		cCodCliLj := SA1->A1_COD + SA1->A1_LOJA
		cDescCli  := SA1->A1_NREDUZ
		dDtEmis   := SC2->C2_EMISSAO
		dDtApo    := SD3->D3_EMISSAO
		cHora	  := SD3->D3_HORA
		nQuant    := SC2->C2_QUANT
		nQtdPro   := SC2->C2_QUANT
		nPesoUnit := SB1->B1_PESO
		nPesoTotal:= Round(SB1->B1_PESO * nQtdPro,2)
		nQtdEmb   := SB1->B1_EMBDELP
		nTotEtiq  := IIF((nQtdPro / nQtdEmb) < 1,1,(nQtdPro / nQtdEmb))
		nPesoEtiq := nPesoTotal/nTotEtiq
	Else
		cCod      := SD3->D3_COD
		cDesc     := SB1->B1_DESC
		cCodCli   := SB1->B1_REFEREN
		cCodCliLj := SA1->A1_COD + SA1->A1_LOJA
		cDescCli  := SA1->A1_NREDUZ
		dDtEmis   := SC2->C2_EMISSAO
		dDtApo    := SD3->D3_EMISSAO
		cHora	  := SD3->D3_HORA
		nQuant    := SC2->C2_QUANT
		nQtdPro   := SD3->D3_QUANT
		nPesoUnit := SB1->B1_PESO
		nPesoTotal:= Round(SB1->B1_PESO * nQtdPro,2)
		nQtdEmb   := SB1->B1_EMBDELP
		nTotEtiq  := IIF((nQtdPro / nQtdEmb) < 1,1,(nQtdPro / nQtdEmb))
		nPesoEtiq := nPesoTotal/nTotEtiq
	EndIf

	oCod:Refresh()
	oDesc:Refresh()
	oCodCli:Refresh()
	oDescCli:Refresh()
	oDtEmis:Refresh()
	oDtApo:Refresh()
	oHora:Refresh()
	oQuant:Refresh()
	oQtdPro:Refresh()
	oPesoUnit:Refresh()
	oPesoTotal:Refresh()
	oQtdEmb:Refresh()
	oTotEtiq:Refresh()

Return lRet

User Function Dlp034Printer()

	Local cNomEti   := AllTrim(SuperGetMv("DP_NOMETI",,""))
	Local lSrv      := .F.
	Local lDrvWin   := .T.
	Local lResto    := .F.
	Local x         := 0
	Local nTotalEti := 0
	Local nQtdEtiq  := 0
	Local cCodBarL  := ""
	Local cQrcode   := ""
	Local nQrX      := 0
	Local nQrY      := 0
	Local nQrLen    := 0

	// Calcula total de etiquetas corretamente (ceiling)
	nTotalEti := Int(nQtdPro / nQtdEmb)
	If nQtdPro % nQtdEmb > 0
		nTotalEti++
		lResto := .T.
	EndIf

	// Coordenadas PPLA do QR: coluna direita (X=67mm), centro vertical da area abaixo de 42mm
	// 203 DPI = 8 dots/mm; etiqueta = 66.8mm altura; QR ~22mm (moduleSize=6, ~29 modulos)
	nQrX := 536  // 67mm * 8
	nQrY := 278  // (66.8 - 10 - 22) * 8 = 278 dots do topo

	MSCBPrinter("ARGOX", "LPT1",,,lSrv,,,,,,lDrvWin)
	MSCBChkStatus(.F.)

	For x := 1 To nTotalEti

		// Quantidade desta etiqueta
		If x == nTotalEti .And. lResto
			nQtdEtiq := nQtdPro % nQtdEmb
		Else
			nQtdEtiq := nQtdEmb
		EndIf

		nPesoEtiq := nQtdEtiq * nPesoUnit

		If Len(AllTrim(cCod)) < 8
			cCodBarL := StrZero(AllTrim(cCod), 8)
		Else
			cCodBarL := AllTrim(cCod)
		EndIf
		cCodBarL += Transform(StrZero((nQtdEtiq * 1000), 4), "@E 9999")

		cQrcode := AllTrim(cCodCli) + "/" + AllTrim(cCod) + "/" + ;
			AllTrim(cNumOP) + "/" + ;
			AllTrim(Str(Int(nQtdEtiq * 1000))) + "/" + ;
			Dtoc(dDtApo)
		nQrLen := Len(cQrcode)

		MSCBBegin(1, 6)

		MSCBBox(2, 1.0, 97.3, 66.8, 2)

		MSCBLineV(15,   1.7,  65.9, 2)
		MSCBLineV(55.1, 54.5, 66.0, 2)
		MSCBLineV(40,   1.7,  42,   2)
		MSCBLineV(65,   1.7,  42,   2)

		MSCBLineH(15, 15,   65.1, 2)
		MSCBLineH(15, 28.5, 65.1, 2)
		MSCBLineH(15, 42.2, 97.1, 2)
		MSCBLineH(15, 54.7, 97.1, 2)

		MSCBSay(10,   2.5,  "PRODUTO APROVADO",                                 "B", "3", "2,1")
		MSCBSay(17,   62,   "DELPI",                                            "N", "3", "1")
		MSCBSay(60.1, 62,   "Ordem de Producao",                                "N", "2", "0.1")
		MSCBSay(60.1, 55.5, cNumOP,                                             "N", "3", "1")
		MSCBSay(17.1, 50.5, "Cliente",                                          "N", "2", "0.1")
		MSCBSay(17.1, 43.5, cDescCli,                                           "N", "3", "1")
		MSCBSay(17.1, 37.3, "Codigo Delpi",                                     "N", "2", "0.1")
		MSCBSay(17.1, 29.8, cCod,                                               "N", "3", "1")
		MSCBSay(42.1, 38.3, "Codigo Cliente",                                   "N", "2", "0.1")
		MSCBSay(42.1, 31.8, cCodCli,                                            "N", "3", "1")
		MSCBSay(17.1, 23.6, "Peso (Kg)",                                        "N", "2", "0.1")
		MSCBSay(17.1, 16.3, Transform(nPesoEtiq, X3Picture("B1_PESO")),         "N", "3", "1")
		MSCBSay(17.1, 11.1, "Data",                                             "N", "2", "0.1")
		MSCBSay(17.1, 3.8,  Dtoc(dDtApo),                                      "N", "3", "1")
		MSCBSay(42.1, 11.1, "Quantidade (Mil)",                                 "N", "2", "0.1")
		MSCBSay(42.1, 3.8,  Transform(nQtdEtiq, X3Picture("B1_EMBDELP")),      "N", "3", "1")

		MSCBSayBar(42.1, 16.6, cCodBarL, "N", "MB07", 9.5, .F., .T., .F.,, 3, 1)

		// QR Code via PPLA nativo (MSCBSayBar nao suporta QR)
		// Formato: W X,Y,Rotation,QR,ModuleSize,0,ECC,Mask,Data,DataLen;
			// Coordenadas em dots (203 DPI = 8 dots/mm), Y de cima para baixo
		// MSCBWrite("W " + AllTrim(Str(nQrX)) + "," + AllTrim(Str(nQrY)) + ",0,QR,6,0,M,7," + cQrcode + "," + AllTrim(Str(nQrLen)) + ";")

		MSCBEnd()

	Next x

	MSCBClosePrinter()

Return
