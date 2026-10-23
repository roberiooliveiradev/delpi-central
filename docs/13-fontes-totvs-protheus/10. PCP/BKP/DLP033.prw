#include 'protheus.ch'
#include 'parmtype.ch'
//#include "FWPrintSetup.ch"
//#include "RPTDEF.CH"

//--------------------------------------------------------------
/*/{Protheus.doc} MyFunction
Description

@param xParam Parameter Description
@return xRet Return Description
@author Marcos Alberto Schoeffel - marcos0174@gmail.com
@since 27/10/2017
/*/
//--------------------------------------------------------------
User Function DLP033()

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

		//SD3->(dbGoTop())

		SB1->(DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))

		//SA1->(DbSeek(xFilial('SA1')+'00000101'))
		SA1->(DbSeek(xFilial('SA1')+SC2->(C2_CLIDELP+C2_LOJDELP)))

		cNumOP    := SD3->D3_OP
		cCod      := SB1->B1_COD
		cDesc     := SB1->B1_DESC
		cCodCli   := SB1->B1_REFEREN
		cCodCliLj := SA1->A1_COD + SA1->A1_LOJA
		cDescCli  := SA1->A1_NREDUZ
		dDtEmis   := SC2->C2_EMISSAO
		//dDtApo    := SD3->D3_EMISSAO
		dDtApo    := SC2->C2_EMISSAO
		cHora	  := SD3->D3_HORA
		nQuant    := SC2->C2_QUANT
		//nQtdPro   := SD3->D3_QUANT
		nQtdPro   := SC2->C2_QUANT
		nPesoUnit := SB1->B1_PESO
		nPesoTotal:= Round(SB1->B1_PESO * nQtdPro,2)
		nQtdEmb   := SB1->B1_EMBDELP
		nTotEtiq  := IIF((nQtdPro / nQtdEmb) < 1,1,(nQtdPro / nQtdEmb))
		nPesoEtiq := nPesoTotal/nTotEtiq  
		/*
		cNumOP    := ""
		cCod      := ""
		cDesc     := ""
		cCodCli   := ""
		cCodCliLj := ""
		cDescCli  := ""
		dDtEmis   := ""
		dDtApo    := ""
		cHora	  := ""
		nQuant    := 0
		nQtdPro   := 0
		nPesoUnit := 0
		nPesoTotal:= 0
		nQtdEmb   := 0
		nTotEtiq  := 0
		nPesoEtiq := 0 */

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


	DEFINE MSDIALOG oDlg TITLE "Dados Impressão Etiqueta Apontamento Produção" FROM 000, 000  TO 400, 500 COLORS 0, 16777215 PIXEL

	@ 004, 137 BITMAP oDelpi SIZE 103, 036 OF oDlg FILENAME "system\lgrl01.bmp" NOBORDER ADJUST PIXEL
	@ 009, 007 GROUP oGroup1 TO 038, 112 PROMPT "Número da Ordem de Produção" OF oDlg COLOR 0, 16777215 PIXEL
	@ 019, 011 MSGET oNumOP VAR cNumOP F3 "SC2" Valid U_D033OP() SIZE 095, 013 OF oDlg PICTURE "@!" COLORS 255, 16777215 FONT oFont1 When lEdita PIXEL

	@ 044, 008 GROUP oGroup2 TO 111, 241 PROMPT "Informações da Ordem Produção" OF oDlg COLOR 0, 16777215 PIXEL
	@ 055, 013 SAY oSay1 PROMPT "Produto" SIZE 023, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 054, 037 MSGET oCod VAR cCod F3 'SB1' SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 054, 085 MSGET oDesc VAR cDesc SIZE 152, 010 OF oDlg PICTURE "@!" COLORS 0, 16777215 READONLY PIXEL
	@ 069, 013 SAY oSay2 PROMPT "Cliente" SIZE 024, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 068, 037 MSGET oCodCli VAR cCodCliLj F3 'SA1' SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 068, 085 MSGET oDescCli VAR cDescCli SIZE 152, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 082, 013 SAY oSay3 PROMPT "Emissão" SIZE 025, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 081, 037 MSGET oDtEmis VAR dDtEmis SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 082, 085 SAY oSay4 PROMPT "Apontamento" SIZE 034, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 081, 119 MSGET oDtApo VAR dDtApo SIZE 045, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 081, 167 MSGET oHora VAR cHora SIZE 032, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 097, 013 SAY oSay5 PROMPT "Qtd.a Produzir" SIZE 036, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 096, 050 MSGET oQuant VAR nQuant Picture X3Picture("C2_QUANT") SIZE 031, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 097, 085 SAY oSay6 PROMPT "Qtd.Produzida" SIZE 035, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 096, 120 MSGET oQtdPro VAR nQtdPro Picture X3Picture("C2_QUANT") Valid U_D033QPRO() SIZE 045, 010 OF oDlg COLORS 0, 16777215 PIXEL

	@ 120, 007 GROUP oGroup3 TO 172, 241 PROMPT "Dados Etiqueta" OF oDlg COLOR 0, 16777215 PIXEL

	@ 133, 012 SAY oSay7 PROMPT "Peso Unitário" SIZE 039, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 133, 065 MSGET oPesoUnit VAR nPesoUnit Picture X3Picture("B1_PESO") SIZE 042, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 133, 130 SAY oSay8 PROMPT "Peso Total" SIZE 031, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 133, 169 MSGET oPesoTotal VAR nPesoTotal Picture X3Picture("B1_PESO") SIZE 033, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	@ 152, 012 SAY oSay9 PROMPT "Quantidade por Embalagem" SIZE 090, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 151, 079 MSGET oQtdEmb VAR nQtdEmb Valid U_D033QEmb() Picture X3Picture("B1_EMBDELP") SIZE 045, 010 OF oDlg COLORS 0, 16777215 PIXEL
	@ 152, 130 SAY oSay10 PROMPT "Total Etiquetas" SIZE 038, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 151, 169 MSGET oTotEtiq VAR nTotEtiq Picture '@E 9999' SIZE 033, 010 OF oDlg COLORS 0, 16777215 READONLY PIXEL
	//@ 183, 160 BUTTON oButton1 PROMPT "Imprimir" SIZE 037, 012 Action (U_Dlp033Printer(), oDlg:End()) OF oDlg PIXEL
	@ 183, 160 BUTTON oButton1 PROMPT "Imprimir" SIZE 037, 012 Action (U_Dlp033Printer(), oNumOP:SetFocus()) OF oDlg PIXEL
	@ 183, 203 BUTTON oButton2 PROMPT "Cancelar" SIZE 037, 012 Action (oDlg:End()) OF oDlg PIXEL

	ACTIVATE MSDIALOG oDlg CENTERED

Return


User Function D033QPRO()
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

User Function D033QEmb()

	Local lRet := .T.
	Local nCpo := &(ReadVar())

	If	Empty(nCpo)
		ApMsgAlert('É obrigatório o preenchimento da quantidade por embalagem !!!')
		Return (lRet := .F.)
	EndIf

	If	(nCpo > nQtdPro)
		ApMsgAlert('Quantidade por Embalagem não pode ser maior que o Total Produzido !!!')
		Return (lRet := .F.)
	EndIf


	nTotEtiq   := Round(IIF((nQtdPro / nQtdEmb) < 1,1,(nQtdPro / nCpo)),0)
	nPesoTotal := Round( nPesoUnit * nQtdPro,3)
	nPesoEtiq  := Round(nPesoTotal/nTotEtiq,3) 
	oTotEtiq:Refresh()
	oPesoTotal:Refresh()
	oQtdEmb:Refresh()

Return lRet


User Function D033OP()

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
		ApMsgAlert('Número de Ordem Produção não existe !!!')
		Return (lRet := .F.)
	EndIf

	/* TSCB26: Diego Kerstner: 14/11/2018: Comentado por solicitação da Joici.
	If	Empty(SC2->C2_QUJE)
	ApMsgAlert('Esta Ordem de Produção não tem movimentos de Apontamento !!!')
	Return (lRet := .F.)
	EndIf
	*/ 


	SB1->(DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))
	If	SB1->(Found())
		If	SB1->B1_TIPO != 'PA'
			ApMsgAlert('O Produto desta Ordem de Produção não é um Produto Acabado, não poderá ser impresso Etiqueta !!!')
			Return (lRet := .F.)
		EndIf
	EndIf
	//TSC: 31/10/2018: Diego Kerstner: Inicio - Atualizar informações da Tela

	dbSelectArea("SD3")
	SD3->(dbSetOrder(1))
	SD3->(DbSeek(xFilial("SD3")+cCpo+SC2->C2_PRODUTO))

	//SB1->(DbSeek(xFilial('SB1')+SD3->D3_COD))
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
		//cNumOP    := M->D3_OP
		cCod      := SD3->D3_COD
		//cCod      := SC2->C2_PRODUTO
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

	//TSC: 31/10/2018: Diego Kerstner: Fim - Atualizar informações da Tela
Return lRet

User Function Dlp033Printer()

	Local cPorta   :="LPT1"
	//Local cCapLpt1 := "C:\TEMP\CAPTURE.BAT"
	//Local cLPT1    := "NET USE LPT1: \\NOTEDELL-MAC\ARGOX /PERSISTENT:YES EXIT"
	Local cLocEti  := "DESKTOP-VAOQVIM"//AllTrim(SuperGetMv("DP_LOCETI",,""))
	Local cNomEti  := AllTrim(SuperGetMv("DP_NOMETI",,""))
	Local cDirEtq  := "\ETIQUETAS\"
	Local cFileEtq := "ETIQUETA.PRN"
	Local cCmd	   := "TYPE "
	Local nHandle  := 0
	Local lResto := .f.

	If nQtdPro % nQtdEmb >0
		lResto := .t.
		nTotEtiq +=1
	endif
	//	nTotEtiq
	//	nQtdEmb
	//	nQtdPro

//	//cLPT1    := "NET USE LPT1: \\"+cLocEti+"\"+cNomEti+" /PERSISTENT:YES EXIT"
//
//	If (WinExec(cLPT1)) != 0
//		ApMsgAlert('Erro ao executar comando Net Use para a porta LPT1 !!!')
//		Return
//	EndIf


	For x=1 to nTotEtiq	
		
		if x == nTotEtiq .and. lResto
			nQtdEmb := nQtdPro % nQtdEmb
		endif
		
		nPesoEtiq := nQtdEmb * nPesoUnit  
		
		MSCBPRINTER("OS 214",cPorta,/*Densidade*/,/*Tamanho 69*/ ,.F.)
		MSCBCHKSTATUS(.F.)
		MSCBINFOETI("Etiquetas Expedição","Protheus")
		MSCBLOADGRF("DELPI.BMP")

		MSCBBEGIN(1,6)

		MSCBGRAFIC(16.5, 56.0, "DELPI")

		//MSCBBOX(1.7,1.7,95.8,67.0) // box principal 96.9 , 66.8
		MSCBBOX(2,1.0,97.3,66.8,2) 

		MSCBLineV(15,1.7,65.9,2)   // 1 linha vertical

		//MSCBLineV(52.5,1.7,34,2)  // 2 linha vertical
		//MSCBLineV(52.5,54.7,65.9,2) // 2 linha vertical
		MSCBLineV(55.1,54.5,66.0,2) // 2 linha vertical

		//MSCBLineV(55,28.5,65.9,2) // 3 linha vertical
		MSCBLineV(55,1.7,42,2)      // 3 linha vertical

		MSCBLineH(15,15,97.1,2)   // 1 linha horizontal
		MSCBLineH(15,28.5,97.1,2) // 2 linha horizontal
		MSCBLineH(15,42.2,97.1,2) // 3 linha horizontal
		MSCBLineH(15,54.7,97.1,2) // 4 linha horizontal

		MSCBSAY(10,2.5, "PRODUTO APROVADO","B","3","2,1")

		//MSCBSAY(74.4,2.8, "Nr Ordem de Producao","N","3","0.1")
		//MSCBSAY(74,6.4, cNumOP, "N","3","1")
		MSCBSAY(60.1,62, "Ordem de Producao","N","2","0.1")
		MSCBSAY(60.1,55.5, cNumOP, "N","3","1")

		//MSCBSAY(28,28.8, "Cliente","N","3","0.1")
		//MSCBSAY(16.1,23.2, cDescCli ,"N","3","1")
		MSCBSAY(17.1,50.5, "Cliente","N","2","0.1")
		MSCBSAY(17.1,43.5, cDescCli ,"N","3","1")

		MSCBSAY(17.1,37.3, "Codigo Delpi","N","2","0.1")
		MSCBSAY(17.1,29.8, cCod, "N","3","1")

		//MSCBSAY(55.6,28.8, "Codigo Cliente","N","3","0.1")
		//MSCBSAY(76.1,36.3, cCodCli, "N","3","1")
		MSCBSAY(60.1,37.3, "Codigo Cliente","N","2","0.1")
		MSCBSAY(60.1,29.8, cCodCli, "N","3","1")

		//MSCBSAY(16.1,42.5, "Peso", "N","3","0.1")
		//MSCBSAY(35,49.5, Transform(nPesoTotal, X3Picture("B1_PESO")), "N","3","1")
		MSCBSAY(17.1,23.6, "Peso (Kg)", "N","2","0.1")
		MSCBSAY(17.1,16.3, Transform(nPesoEtiq, X3Picture("B1_PESO")), "N","3","1")

		//MSCBSAY(55.6,42.5, "Destino da Entrega", "N","3","0.1")
		//MSCBSAY(68.5,50.2, , "N","3","1")

		//TSCB26: Diego Kerstner: 19/12/2018; Solicitado pela Joici imprimir código de barras contendo código Produto + Quantidade
		//MSCBSAY(60.1,23.6, "Destino da Entrega", "N","2","0.1")
		//MSCBSAY(60.1,16.3, , "N","3","1")


		If Len(Alltrim(cCod)) < 8
			cCodBar := StrZero( Alltrim(cCod), 8)
		else
			cCodBar := Alltrim(cCod)
		endif 

		cCodBar += Transform( StrZero ((nQtdEmb * 1000),4), "@E 9999")


		MSCBSAYBAR(64.1,16.6,cCodBar                ,"N","MB07",9.5,.F.,.T.,.F.,,3,1)
		//MSCBSAYBAR(20  ,22  ,AllTrim(SB1->B1_CODBAR),"N","C",13)

		MSCBSAY(17.1,11.1, "Data", "N","2","0.1")
		//MSCBSAY(17.1,3.8, Dtoc(dDtEmis), "N","3","1")
		MSCBSAY(17.1,3.8, Dtoc(dDtApo), "N","3","1") //TSC: 24/10/2018: Diego Kerstner: Alterada para a data do Apontamento.

		//MSCBSAY(55.6,55, "Quantidade", "N","2","0.1")
		//MSCBSAY(76.1,61.5, Transform(nQtdEmb, X3Picture("B1_EMBDELP")), "N","3","1")
		MSCBSAY(60.1,11.1, "Quantidade (Mil)", "N","2","0.1")
		MSCBSAY(60.1,3.8, Transform(nQtdEmb, X3Picture("B1_EMBDELP")), "N","3","1")

		MSCBEND()

		MSCBCLOSEPRINTER()
	Next
Return