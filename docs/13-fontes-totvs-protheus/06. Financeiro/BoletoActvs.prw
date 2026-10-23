#INCLUDE "RWMAKE.CH"
#INCLUDE "TOPCONN.CH"
#Include "Protheus.ch"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "RPTDEF.CH"
#Include "AP5MAIL.CH"

/*/
=========================================================================================================================================================================================ProgramaBOLETO=========================================================================================AutorACTVS====================================================================================================================================================ATUALIZACAO EM 02/08/16===============================================================
=========================================================================================USO ESPECï¿½FICO PARA CLIENTES==================================================================================================================================================ALTERA#¿½ES: 1) Alteraï¿½ï¿½es realizadas ao imprimir 2)Inclusï¿½es e adequaï¿½ï¿½es nos bancos CEF, Santander, HSBC, Sicoob e BB
================================================================================================================================================
REVISOES REGISTRADAS
07/07/2016 - INCLUSAO BANCO HSBC
07/07/2016 - INCLUSAO BANCO SICOOB
02/02/2017 - INCLUSAO BANCO SICRED
24/04/2017 - INCLUSAO BANCO CECRED
16/06/2017 - AJUSTE LAYOUT CEF
10/07/2018 - AJUSTE DIGITO ITAU NO CABECALHO DO BOLETO
21/09/2018 - QUEBRA POR PAGINA / ALTERACAO NA ORDEM DO BROWSE
19/12/2018 - INCLUSAO BANCO UNICRED
26/02/2019 - CORRECAO NO CALCULO DV BANCO SAFRA
11/06/2019 - INCLUSAO DE PE FA740BRW PARA CHAMADA ATRAVES DA ROTINA DE FUNCOES CONTAS A RECEBER (FINA740)
11/06/2019 - CRIADA OUTRA VERSAO DO FONTE PARA O CLIENTE SARAIVA COM OUTRA USER FUNCTION
24/06/2019 - ALTERADO NOME DO CLIENTE PARA TRAZER DO CAMPO SM0->M0_NOMECOM
06/09/2019 - INCLUIDA OPCAO DE ENVIO POR EMAIL
12/09/2019 - TRATAR CAMPO E4_ZBOL NA CONDICAO DE PAGAMENTO (GERA OU NAO BOLETO)

/*/
/*
@Parametros
aBoletos - Rotina para geração de boletos automatico - Autoexec
oDanfe   - Utilizado somente para imprimir o boleto no Danfe
*/
User Function BOLETOACTVS(aBoletos,oDanfe, lGerBol )

	Local   nOpc 		:= 1
	Local	nX			:= 0
	Local	nJ			:= 0
	Local	aCabec		:= {}
	Local   aMarked 	:= {}
	Local   cDesc 		:= "Este programa imprime os boletos de"+chr(13)+"cobranca bancaria de acordo com"+chr(13)+"os parametros informados"
	Local 	cQuery		:= ""
	Local	_lInverte	:= .F.
	Local	_cMarca		:= GetMark()
	Local 	_oDlg
	Local	oMark
	Local	oBrowse
	Local	oImgMark
	Local	oImgDMark
	Local 	aSize		:= MsAdvSize()		//Tamanhos da tela
	Local 	nI

	Private BB			:= .F.
	Private BRADESCO	:= .F.
	Private SAFRA    	:= .F.
	Private ITAU		:= .F.
	Private SANTANDER   := .F.
	Private CAIXAEF     := .F.
	Private HSBC        := .F. // TSC022 07/07/2016
	Private SICOOB      := .F. // TSC022 07/07/2016
	Private SICREDI     := .F. // WALTER 02/02/2017
	Private BANRISUL    := .F. // TSC 422
	Private UNICRED     := .F. // TSC022 19/12/2018
	Private aTitulos	:= {}
	Private cLocPagto	:= ""
	Private Exec    	:= .F.
	Private lMarcar		:= .T.
	Private cIndexName 	:= ''
	Private cIndexKey  	:= ''
	Private cFilter    	:= ''
	Private cPerg		:= "ACTBOL1"
	Private cAliasSE1
	Private lAutoExec
	Private _MV_PAR01
	Private _MV_PAR02
	Private _MV_PAR03
	Private _MV_PAR04
	Private _MV_PAR05
	Private _MV_PAR06
	Private _MV_PAR07
	Private _MV_PAR08
	Private _MV_PAR09
	Private _MV_PAR10
	Private _MV_PAR11
	Private _MV_PAR12
	Private _MV_PAR13
	Private _MV_PAR14
	Private _MV_PAR15
	Private _MV_PAR16
	Private _MV_PAR17
	Private _MV_PAR18
	Private _MV_PAR19
	Private _MV_PAR20
	Private _MV_PAR21
	Private _MV_PAR22
	Private _MV_PAR23
	Private _MV_PAR24
	Private _MV_PAR25
	Private _MV_PAR26
	Private _MV_PAR27
	//INICIO -TSC959 - THIAGO.ZOPPI - BOLETO NA DANFE
	Private	lDanfe 	  := IsInCallStack("SPEDNFE") .OR. IsInCallStack("U_DANFEPROC") .OR. IsInCallStack("AUTODISTMAIL") .OR. funName() == "RPC"
	Private l460nota  := IsInCallStack("U_M460NOTA")
	Private lGerar    :=  .F.
	Private aParbanco := StrTokArr2(SuperGetMV("MV_ZBRIPAR",.F.,""),';') // Parametros de Banco para ser utilizado pelo PE M460NOTA
	DEFAULT oDanfe 	  := NIL
	DEFAULT lGerBol   := .F.

	lGerar := lGerBol
	//FIM -TSC959 - THIAGO.ZOPPI - BOLETO NA DANFE

	// Se vier do Danfe, troca o Objeto para utilizar o do oDanfe passado em parametros.
	IF lDanfe
		IF oDanfe <> NIL
			Private oprint := oDanfe
		ENDIF
	ENDIF

	aBoletos 	:= IIF(aBoletos==Nil,{},aBoletos)
	lAutoExec 	:= Len(aBoletos) > 0

	dbSelectArea("SE1")

	If FunName() == "FINA740"
		lAutoExec := .f.
	EndIf

	If !lAutoExec

		If !ExistDir( "\boleto\" )
			MakeDir( "\boleto\" )
		EndIf

		If FunName() == "FINA740"
			If SE1->E1_SALDO == 0
				MsgStop("Titulo JÁ Baixado!!! Não é Possível Reimpressao de Boleto.")
				Return
			EndIf
			If Empty(SE1->E1_NUMBCO)
				MsgStop("Não Foi Gerado Boleto Para Esse Título!!! Contate Faturamento.")
				Return
			EndIf
			If Empty(SE1->E1_PARCELA)
				MV_PAR05 := SE1->E1_PARCELA
				MV_PAR06 := SE1->E1_PARCELA
			Else
				If MsgYesNo("ATENÇÃO!!! Foram Encontradas Mais Parcelas Desse Título. Reimprime Todos?")
					MV_PAR05 := "   "
					MV_PAR06 := "ZZZ"
				Else
					MV_PAR05 := SE1->E1_PARCELA
					MV_PAR06 := SE1->E1_PARCELA
				EndIf
			EndIf
			MV_PAR01 := SE1->E1_PREFIXO
			MV_PAR02 := SE1->E1_PREFIXO
			MV_PAR03 := SE1->E1_NUM
			MV_PAR04 := SE1->E1_NUM
			MV_PAR07 := SE1->E1_PORTADO
			MV_PAR08 := SE1->E1_AGEDEP
			MV_PAR09 := SE1->E1_CONTA
			MV_PAR10 := Posicione("SEA",1,xFilial("SEA")+SE1->E1_NUMBOR,"EA_SUBCTA")
			MV_PAR11 := SE1->E1_CLIENTE
			MV_PAR12 := SE1->E1_CLIENTE
			MV_PAR13 := SE1->E1_LOJA
			MV_PAR14 := SE1->E1_LOJA
			MV_PAR15 := CToD("01/01/10")
			MV_PAR16 := CToD("31/12/40")
			MV_PAR17 := CToD("01/01/10")
			MV_PAR18 := CToD("31/12/40")
			MV_PAR19 := SE1->E1_NUMBOR
			MV_PAR20 := SE1->E1_NUMBOR
			MV_PAR21 := 1 // NAO MOSTRA TELA DE SELECAO
			MV_PAR22 := 2 // GERA BORDERO = NAO
			MV_PAR23 := 1
			MV_PAR24 := ""
		Else
			If !Pergunte (cPerg,.T.)
				Return
			EndIf
		EndIf

		//Configura os parametros
		_MV_PAR01 := MV_PAR01 //Do Prefixo:
		_MV_PAR02 := MV_PAR02 //Ate o Prefixo:
		_MV_PAR03 := MV_PAR03 //Do Titulo:
		_MV_PAR04 := MV_PAR04 //Ate o Titulo:
		_MV_PAR05 := MV_PAR05 //Da Parcela:
		_MV_PAR06 := MV_PAR06 //Ate a Parcela:
		_MV_PAR07 := MV_PAR07 //Do Banco:
		_MV_PAR08 := MV_PAR08 //Agencia:
		_MV_PAR09 := MV_PAR09 //Conta:
		_MV_PAR10 := MV_PAR10 //SubConta:
		_MV_PAR11 := MV_PAR11 //Do Cliente:
		_MV_PAR12 := MV_PAR12 //Ate o Cliente:
		_MV_PAR13 := MV_PAR13 //Da Loja:
		_MV_PAR14 := MV_PAR14 //Ate a Loja:
		_MV_PAR15 := MV_PAR15 //Da Data de Vencimento:
		_MV_PAR16 := MV_PAR16 //Ate a Data de Vencimento:
		_MV_PAR17 := MV_PAR17 //Da Data Emissao:
		_MV_PAR18 := MV_PAR18 //Ate a Data de Emissao:
		_MV_PAR19 := MV_PAR19 //Do bordero:
		_MV_PAR20 := MV_PAR20 //Ate o Bordero:
		_MV_PAR21 := MV_PAR21 //Selecionar Titulos:
		_MV_PAR22 := MV_PAR22 //Gerar Bordero
		_MV_PAR23 := MV_PAR23 //Tipo Impressao 1-Padrao/2-PDF/3-EMAIL (ainda em desenv)
		_MV_PAR24 := MV_PAR24 //Diretorio dos arquivos PDF


		//		If Empty(MV_PAR04) .Or. Empty(MV_PAR06) .Or. Empty(MV_PAR12) .Or. Empty(MV_PAR18) .Or. Empty(MV_PAR16) .Or. Empty(MV_PAR14) .Or. Empty(MV_PAR20)
		If Empty(MV_PAR04) .Or. Empty(MV_PAR12) .Or. Empty(MV_PAR18) .Or. Empty(MV_PAR16) .Or. Empty(MV_PAR14) .Or. Empty(MV_PAR20)
			VerParam("Voce deve selecionar um intervalo de valores em todos os parametros!")
			Return
		EndIf

		nOpc := Aviso("Impressao do Boleto Laser",cDesc,{"Ok","Cancelar"})
	Else

		IF l460nota .OR. lGerar

			//Configura os parametros
			_MV_PAR21 := 2 // Nao seleciona titulos
			_MV_PAR22 := 1 //Gerar Bordero

			//Dados do Banco
			_MV_PAR07 := PADR(aParbanco[1],TAMSX3("E1_PORTADO")[1]) // Banco
			_MV_PAR08 := PADR(aParbanco[2],TAMSX3("E1_AGEDEP")[1])  // AG
			_MV_PAR09 := PADR(aParbanco[3],TAMSX3("E1_CONTA")[1])   // Conta
			_MV_PAR10 := PADR(aParbanco[4],TAMSX3("E1_NUMBOR")[1])  // SubConta
			_MV_PAR23 := 2 // PDF
			//Somente Geracao Dos Boletos

		Else
			//ADAPTADO PARA JOB :
			// -- ENVIAR EMAIL BOLETOS JA GERADOS COM 3 DIAS DE VENCIMENTO
			//Configura os parametros
			_MV_PAR21 := 2 // NAO SELECIONA
			_MV_PAR22 := 2 // NAO Gerar Bordero
			_MV_PAR23 := 3 // ENVIAR EMAIL
		ENDIF

	EndIf

	If nOpc == 1

		dbSelectArea("SE1")
		aStruTRB := dbStruct()

		If !lAutoExec

			cQuery := "SELECT  "

			For nI:=1 To Len(aStruTRB)
				cQuery += aStruTRB[nI][1]+","
			Next nI

			cQuery += " SE1.R_E_C_N_O_  AS NREG "
			cQuery += " FROM "+	RetSqlName("SE1") + " SE1 "
			cQuery += " WHERE E1_NUM   >= '" 	+ _MV_PAR03 		+ "' And E1_NUM     <= '" 	+ _MV_PAR04 + "'  "
			cQuery += " AND E1_PARCELA >= '" 	+ _MV_PAR05 		+ "' And E1_PARCELA <= '"	+ _MV_PAR06 + "'  "
			cQuery += " AND E1_PREFIXO >= '" 	+ _MV_PAR01 		+ "' And E1_PREFIXO <= '"	+ _MV_PAR02 + "'  "
			cQuery += " AND E1_CLIENTE >= '" 	+ _MV_PAR11 		+ "' And E1_CLIENTE <= '"	+ _MV_PAR12 + "' "
			cQuery += " AND E1_EMISSAO >= '" 	+ DTOS(_MV_PAR17)	+ "' And E1_EMISSAO <= '"	+ DTOS(_MV_PAR18) + "' "
			cQuery += " AND E1_VENCTO  >= '" 	+ DTOS(_MV_PAR15)	+ "' And E1_VENCTO  <= '" 	+ DTOS(_MV_PAR16) + "' "
			cQuery += " AND E1_LOJA    >= '"	+ _MV_PAR13			+ "' And E1_LOJA    <= '"	+ _MV_PAR14 + "' "
			If _MV_PAR22 == 2 //Nao gera bordero
				cQuery += " AND E1_NUMBOR  >= '"	+ _MV_PAR19			+ "' And E1_NUMBOR  <= '"	+ _MV_PAR20 + "' "
				If !Empty(_MV_PAR07)
					cQuery += " AND E1_PORTADO = '" + _MV_PAR07 + "' "
				Endif
			Else
				cQuery += " AND E1_NUMBCO = '' AND E1_NUMBOR = '' " //Se gera bordero, somente selecionara os titulos sem boleto
			Endif
			cQuery += " AND E1_FILIAL = '"		+ xFilial("SE1")	+ "' And E1_SALDO > 0  "
			cQuery += " AND SUBSTRING(E1_TIPO,3,1) != '-' "
			//RETIRA NCC E RA DA SELECAO
			cQuery += " AND E1_TIPO != 'RA ' "
			cQuery += " AND E1_TIPO != 'NCC' "
			//FIM
			cQuery += " AND (E1_PEDIDO = (SELECT C5_NUM FROM "+	RetSqlName("SC5") + " SC5, "+	RetSqlName("SE4") + " SE4 WHERE C5_NUM = SE1.E1_PEDIDO  AND C5_CONDPAG = E4_CODIGO AND C5_FILIAL = '"+xFilial("SC5")+ "' AND  SE1.E1_FILIAL = '"+xFilial("SE1")+"' AND SE4.D_E_L_E_T_ = ' '  AND SC5.D_E_L_E_T_ = ' ' ) OR E1_PEDIDO = '') "
			cQuery += " AND SE1.D_E_L_E_T_ = ' ' "
			cQuery += " ORDER BY E1_PREFIXO, E1_NUM, E1_PARCELA, E1_EMISSAO, E1_NOMCLI, E1_PORTADO"
			//cQuery += " ORDER BY E1_NOMCLI,E1_PORTADO, E1_CLIENTE, E1_PREFIXO, E1_NUM, E1_PARCELA, E1_EMISSAO "
		EndIf

		If Select("TRB1") <> 0
			dbSelectArea("TRB1")
			dbCloseArea()
		EndIf

		cAliasSE1 := "TRB1"
		cNomeArq:=CriaTrab( aStruTRB, .T. )
		dbUseArea(.T.,__LocalDriver,cNomeArq,cAliasSE1,.T.,.F.)

		If !lAutoExec
			MsAguarde({|| SqlToTrb(cQuery, aStruTRB, cAliasSE1 )},OemToAnsi("Executando Query..."))
		Else
			//Criado no ponto de entrada M460NOTA
			//Ou vindo do JOB
			if l460nota .OR. lGerar
				conout("BoletoActvs - Selecionando Boletos : "+ CVALTOCHAR( Len(aBoletos) )   )
			ENDIF
			For nX:=1 To Len(aBoletos)
				RecLock(cAliasSE1, .T.)
				For nJ:=1 To Len(aBoletos[nX])
					aDados := aBoletos[nX][nJ]
					&(cAliasSE1+"->"+aDados[1]) := aDados[2]
				Next
				MsUnlock()

				//MARCA TODOS
				//JOB
				AADD(aMarked,.T.)

			Next
		EndIf

		DbSelectArea(cAliasSE1)
		DbGoTOp()

		If _mv_par21 == 1

			dbSelectArea(cAliasSe1)
			dbGoTop()

			While !(cAliasSe1)->(EoF())

				aTemp := {}
				AADD(aTemp, !lMarcar)
				AADD(aTemp, (cAliasSe1)->E1_PREFIXO)
				AADD(aTemp, (cAliasSe1)->E1_NUM)
				AADD(aTemp, (cAliasSe1)->E1_PARCELA)
				AADD(aTemp, (cAliasSe1)->E1_TIPO)
				AADD(aTemp, (cAliasSe1)->E1_NOMCLI)
				AADD(aTemp, (cAliasSe1)->E1_EMISSAO)
				AADD(aTemp, (cAliasSe1)->E1_VENCTO)
				AADD(aTemp, Transform((cAliasSe1)->E1_SALDO,x3Picture("E1_SALDO")))

				//Caso seja execucao automatica, deve verificar a condicao de pagamento
				If lAutoExec
					AADD(aTitulos, aTemp)
				Else
					//Nao deve verificar porque no financeiro tem o esquema de agrupamento de NF
					AADD(aTitulos, aTemp)
				EndIf

				(cAliasSe1)->(DbSkip())
			EndDo

			If Len(aTitulos) == 0
				Alert("Nao foram encontrados titulos com os parametros informados!")
				DbSelectArea("SE1")
				RetIndex("SE1")
				FErase(cIndexName+OrdBagExt())
				Return
			EndIf

			AADD(aCabec, "")
			AADD(aCabec, "Prefixo")
			AADD(aCabec, "Documento")
			AADD(aCabec, "Parcela")
			AADD(aCabec, "Tipo")
			AADD(aCabec, "Cliente")
			AADD(aCabec, "Emissao")
			AADD(aCabec, "Vencimento")
			AADD(aCabec, "Valor")

			DEFINE MSDIALOG _oDlg TITLE "Selecao de titulos para geracao de boletos" From aSize[7],0 To aSize[6],aSize[5] OF oMainWnd PIXEL

			oImgMark 	:= LoadBitmap(GetResources(),'LBTIK')
			oImgDMark	:= LoadBitmap(GetResources(),'LBNO')

			oBrowse:= TCBROWSE():New(001,001,350,170,,aCabec,{},_oDlg,,,,,{||},,_oDlg:oFont,,,,,.F.,,.T.,,.F.,,,)

			oBrowse:SetArray(aTitulos)
			oBrowse:lAdjustColSize 	:= .T.
			oBrowse:bLDblClick		:= {|nRow, nCol| aTitulos[oBrowse:nAt,01] := !aTitulos[oBrowse:nAt,01]}
			oBrowse:bChange			:= {||SetFocus(oBrowse:hWnd)}
			oBrowse:bHeaderClick	:= {|nRow, nCol| If(nCol == 1,(lMarcacao(),oBrowse:Refresh()),Nil) }
			oBrowse:nAt				:= 1
			oBrowse:Align			:= CONTROL_ALIGN_ALLCLIENT //Tela inteira
			oBrowse:bLine 			:= {||{ If(	aTitulos[oBrowse:nAt,01],oImgMark,oImgDMark),;
				aTitulos[oBrowse:nAt,02],;
				aTitulos[oBrowse:nAt,03],;
				aTitulos[oBrowse:nAT,04],;
				aTitulos[oBrowse:nAT,05],;
				Padr(aTitulos[oBrowse:nAT,06],50),;
				aTitulos[oBrowse:nAT,07],;
				aTitulos[oBrowse:nAT,08],;
				aTitulos[oBrowse:nAT,09]}}


			ACTIVATE DIALOG _oDlg CENTERED ON INIT EnchoiceBar(_oDlg,{|| Exec := .T.,Close(_oDlg)},{|| Exec := .F.,Close(_oDlg)})
		EndIf
	EndIf

	//Execucao automatica
	If _mv_par21 == 2
		Exec := .T.
	EndIf

	For nX:=1 To Len(aTitulos)
		AADD(aMarked,IIF(_mv_par21 == 2,.T.,aTitulos[nX][1]))
	Next

	If Exec
		Processa({|lEnd| MontaRel(aMarked)})
	Endif

	DbSelectArea("SE1")
	RetIndex("SE1")
	FErase(cIndexName+OrdBagExt())

Return Nil

//------------------------------------------------------------------------------------
// Inverte marcacao
//------------------------------------------------------------------------------------
Static Function lMarcacao()
	Local nX:= 0
	For nX:= 1 To Len(aTitulos)
		aTitulos[nX][1] := lMarcar
	Next
	lMarcar := !lMarcar
Return

//------------------------------------------------------------------------------------
// Impressao dos boletos
//------------------------------------------------------------------------------------

Static Function MontaRel(aMarked)

	//Local oPrint
	Local aDatPagador
	Local aBolText
	Local lMark		:= .F.
	Local CB_RN_NN  	:= {}
	Local i        	:= 1
	Local n 			:= 0
	Local nX        := 0
	Local nRec      := 0
	Local _nVlrAbat 	:= 0
	Local aBitmap   	:= {"" ,"\Bitmaps\Logo_Siga.bmp"}  //Logo da empresa
	Local aBMP		:= aBitMap
	Private aDadosEmp	:= {SM0->M0_NOMECOM                                                    			,; //Nome da Empresa
		AllTrim(SM0->M0_ENDCOB)                                          			,; //Endereco
		AllTrim(SM0->M0_BAIRCOB)+", "+AllTrim(SM0->M0_CIDCOB)+", "+SM0->M0_ESTCOB 	,; //Complemento
		"CEP: "+Subs(SM0->M0_CEPCOB,1,5)+"-"+Subs(SM0->M0_CEPCOB,6,3)             	,; //CEP
		"PABX/FAX: "+SM0->M0_TEL                                              		,; //Telefones
		"CNPJ: "+Subs(SM0->M0_CGC,1,2)+"."+Subs(SM0->M0_CGC,3,3)+"."+           		;
		Subs(SM0->M0_CGC,6,3)+"/"+Subs(SM0->M0_CGC,9,4)+"-"+                    		;
		Subs(SM0->M0_CGC,13,2)                                             			,; //CGC
		"I.E.: "+Subs(SM0->M0_INSC,1,3)+"."+Subs(SM0->M0_INSC,4,3)+"."+      		;
		Subs(SM0->M0_INSC,7,3)+"."+Subs(SM0->M0_INSC,10,3)                      		}  //I.E


	Private aDadosTit
	Private aDadosBanco
	Private nFatorH := 1
	Private nFatorV := 1
	Private nAddSay := 0
	Private nAddLin := 0
	Private nAddBco := 0
	Private aAglutinaBol := {}

	DbSelectArea(cAliasSE1)
	dbGoTop()
	For nX:=1 To Len(aMarked)
		If !lMark
			lMark := aMarked[nX]
		EndIf
	Next
	If !lMark
		Alert("Voce deve marcar ao menos um boleto para impressao!")
		if l460nota .OR. lGerar
			conout("Voce deve marcar ao menos um boleto para impressao!" )
		ENDIF
		Return
	EndIf

	If _MV_PAR23 == 1 //Se for geracao em tela
		oPrint:= TMSPrinter():New( "Boleto Laser" )
		oPrint:setPortrait()
		oPrint:setPaperSize(DMPAPER_A4)
		oPrint:Setup()
		oPrint:SetPortrait() 	// ou SetLandscape()
		oPrint:SetPaperSize(DMPAPER_A4)	// tamanho A4
		oPrint:StartPage()   	// Inicia uma nova pagina
	EndIf

	ProcRegua(nRec)

	Do While !EOF()

		//If i <= len(aMarked)
		If !aMarked[i]
			i++
			dbSkip()
			Loop
		Endif
		//Endif

		//Posiciona o SA6 (Bancos)
		DbSelectArea("SA6")
		DbSetOrder(1)
		If !Empty((caliasSE1)->E1_AGEDEP) .And. _MV_PAR22 == 2
			DbSeek(xFilial("SA6")+(caliasSE1)->E1_PORTADO+(caliasSE1)->E1_AGEDEP+(caliasSE1)->E1_CONTA)
		Else
			DbSeek(xFilial("SA6")+_MV_PAR07+_MV_PAR08+_MV_PAR09)
		Endif

		If Eof()
			MsgBox("Banco/Agencia nao Encontrado")
			if l460nota .OR. lGerar
				conout("Banco/Agencia nao Encontrado" )
			ENDIF

			Return()
		Endif

		SEA->(DbSetOrder(1))
		SEA->(DbSeek(xFilial("SEA")+(caliasSE1)->E1_NUMBOR+(caliasSE1)->E1_PREFIXO+(caliasSE1)->E1_NUM+(caliasSE1)->E1_PARCELA+(caliasSE1)->E1_TIPO))
		//Posiciona o SEE (Parametros banco)
		DbSelectArea("SEE")
		SEE->(DbSetOrder(1))
		If !Empty((caliasSE1)->E1_AGEDEP) .And. _MV_PAR22 == 2
			DbSeek(xFilial("SEE")+(caliasSE1)->(E1_PORTADO+E1_AGEDEP+E1_CONTA)+SEA->EA_SUBCTA)
		Else
			SEE->(DbSeek(xFilial("SEE")+_MV_PAR07+_MV_PAR08+_MV_PAR09))
		Endif

		If Eof()
			MsgBox("Parametros Bancos Nao Encontrado")
			if l460nota .OR. lGerar
				conout("Banco/Agencia nao Encontrado" )
			ENDIF
			Return()
		EndIf

		cA6_COD := SA6->A6_COD
		cA6_AGE := SA6->A6_AGENCIA
		cA6_CON := SA6->A6_NUMCON
		cA6_NOM := SA6->A6_NREDUZ
		cA6_DIG := SA6->A6_DVCTA
		cA6_DAG := SA6->A6_DVAGE
		cA6_POS := SEE->EE_CODPROD // ESPECIFICO SICREDI

		If SEE->(FieldPos("EE_BANCORR")) > 0 .and. SEE->(FieldPos("EE_AGECORR")) > 0 .and. SEE->(FieldPos("EE_CONCORR")) > 0 .and.;
				!Empty(SEE->EE_BANCORR) .and. !Empty(SEE->EE_AGECORR) .and. !Empty(SEE->EE_CONCORR)

			aOldSA6 := SA6->(GetArea())
			DbSelectArea("SA6")
			DbSetOrder(1)
			If DbSeek(xFilial("SA6")+SEE->EE_BANCORR+SEE->EE_AGECORR+SEE->EE_CONCORR)
				cA6_COD := SEE->EE_BANCORR
				cA6_AGE := SEE->EE_AGECORR
				cA6_CON := SEE->EE_CONCORR
				cA6_NOM := SA6->A6_NREDUZ
				cA6_DIG := SA6->A6_DVCTA
				cA6_DAG := SA6->A6_DVAGE
				cA6_POS := SEE->EE_CODPROD // ESPECIFICO SICREDI
			Endif
			RestArea(aOldSA6)
		Endif

		//Posiciona o SA1 (Cliente)
		DbSelectArea("SA1")
		DbSetOrder(1)
		DbSeek(xFilial("SA1")+(caliasSE1)->(E1_CLIENTE+E1_LOJA))

		If Len(Alltrim(SA1->A1_CGC))== 14
			cCpfCnpj:="CNPJ "+Transform(SA1->A1_CGC,"@R 99.999.999/9999-99")
		Else
			cCpfCnpj:="CPF "+Transform(SA1->A1_CGC,"@R 999.999.999-99")
		Endif

		DbSelectArea("SE1")

		aDadosBanco  := {cA6_COD                                       ,;               //Numero do Banco
			cA6_NOM                                       ,;               //Nome do Banco
			Iif(cA6_COD=="479",StrZero(Val(AllTrim(cA6_AGE)),7),SubStr(StrZero(Val(AllTrim(cA6_AGE)),4),1,4)+If(Empty(cA6_DAG),"",Iif(cA6_COD=="422",cA6_DAG,"-"+cA6_DAG))),;   //Agencia
			Iif(cA6_COD=="479",AllTrim(SEE->EE_CODEMP),AllTrim(cA6_CON)),;   //Conta Corrente
			Iif(cA6_COD=="479","",If(Empty(cA6_DIG),"",cA6_DIG))  ,;               //Digito da conta corrente
			AllTrim(SEE->EE_CARTEIR)+Iif(!Empty(AllTrim(SEE->EE_VARIACA)),"-"+SEE->EE_VARIACA,"") }                //Carteira

		aDatPagador   := {AllTrim(SA1->A1_NOME)+" - "+cCpfCnpj             ,;      //Razao Social
			AllTrim(SA1->A1_COD )                            ,;      //Codigo
			If(!Empty(SA1->A1_ENDCOB),AllTrim(SA1->A1_ENDCOB)+" - "+SA1->A1_BAIRROC,AllTrim(SA1->A1_END)+"-"+SA1->A1_BAIRRO) ,;      //Endereco
			If(!Empty(SA1->A1_MUNC), AllTrim(SA1->A1_MUNC ), AllTrim(SA1->A1_MUN )) ,;      //Cidade
			If(!Empty(SA1->A1_ESTC), SA1->A1_ESTC, SA1->A1_EST) ,;      //Estado
			If(!Empty(SA1->A1_CEPC), SA1->A1_CEPC, SA1->A1_CEP)  }       //CEP

		_nSaldo := 0
		_nSaldo := (caliasSE1)->E1_SALDO+(caliasSE1)->E1_SDACRES-(caliasSE1)->E1_SDDECRE
		_nSaldo -= SomaAbat((caliasSE1)->E1_PREFIXO,(caliasSE1)->E1_NUM,(caliasSE1)->E1_PARCELA,"R",1,,(caliasSE1)->E1_CLIENTE,(caliasSE1)->E1_LOJA)

		//Monta o Bordero
		If lAutoExec .Or. _MV_PAR22 == 1

			if l460nota .OR. lGerar
				conout("BoletoActvs - Gerando Bordero"+ (caliasSE1)->E1_NUM + "-" +(caliasSE1)->E1_PREFIXO + "-" +(caliasSE1)->E1_CLIENTE )
			ENDIF

			cAliasTmp 	:= Alias()
			cRecTmp		:= Recno()
			cBordero 	:= If(!Empty((caliasSE1)->E1_NUMBOR),(caliasSE1)->E1_NUMBOR,BuscaBorde())

			If Empty(cBordero)
				cBordero := GetMv("MV_NUMBORR",.F.)
				If Empty(cBordero)
					cBordero := "000001"
				Endif
				PutMv("MV_NUMBORR",Soma1(cBordero))
			Endif

			If Empty( (caliasSE1)->E1_NUMBOR )
				RecLock("SEA",.T.)
				SEA->EA_FILIAL		:= (caliasSE1)->E1_FILIAL
				SEA->EA_PREFIXO 	:= (caliasSE1)->E1_PREFIXO
				SEA->EA_NUM 		:= (caliasSE1)->E1_NUM
				SEA->EA_PARCELA 	:= (caliasSE1)->E1_PARCELA
				SEA->EA_PORTADO 	:= SA6->A6_COD
				SEA->EA_AGEDEP 		:= SA6->A6_AGENCIA
				SEA->EA_SUBCTA 		:= _MV_PAR10
				SEA->EA_DATABOR 	:= (dDataBase)
				SEA->EA_TIPO 		:= (caliasSE1)->E1_TIPO
				SEA->EA_LOJA 		:= (caliasSE1)->E1_LOJA
				SEA->EA_NUMCON 		:= SA6->A6_NUMCON
				SEA->EA_SALDO 		:= (caliasSE1)->E1_SALDO
				SEA->EA_FILORIG 	:= (caliasSE1)->E1_FILORIG
				SEA->EA_CART 		:= "R"
				SEA->EA_NUMBOR 		:= cBordero
				SEA->EA_SITUACA		:= "1"
				SEA->EA_SITUANT     := "0"
				SEA->(MsUnlock())

				DbSelectArea("SE1")
				DbSetOrder(1) //incluido pelo sadiomar em 22/04/2013
				DbSeek(xFilial("SE1")+(cAliasSE1)->(E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO))

				RecLock("SE1",.F.)
				SE1->E1_NUMBOR	:= cBordero
				SE1->E1_MOVIMEN	:= dDataBase
				SE1->E1_DATABOR	:= dDataBase
				If (cAliasSE1)->E1_PORTADO == "341"
					SE1->E1_SITUACA	:= SEE->EE_SITUACA //"1"
				Else
					SE1->E1_SITUACA	:= "1"
				EndIf
				SE1->E1_PORTADO := SA6->A6_COD
				SE1->E1_AGEDEP  := SA6->A6_AGENCIA
				SE1->E1_CONTA   := SA6->A6_NUMCON
				SE1->(MsUnlock())
			Endif

			DbSelectArea("SE1")
			DbSetOrder(1)
			DbSeek(xFilial("SE1")+(cAliasSE1)->(E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO))

			DbCloseArea()

			DbSelectArea(cAliasTmp)
			DbGoTo(cRecTmp)

		EndIf

		//Tamanho do NOSSO NUMERO
		nTam_NN := If( SEE->EE_TAM_NN == 0 , 11 , SEE->EE_TAM_NN )

		//Define NOSSO NUMERO: Se o titulo ja foi impresso, reaproveita, senao, busca do proximo numero gravada na tabela de parametros banco
		cNosso_Num := StrZero( Val( IIf( Empty((caliasSE1)->E1_NUMBCO) , SEE->EE_FAXATU , Substr((caliasSE1)->E1_NUMBCO,1,nTam_NN) ) ) , nTam_NN )

		If Val(cNosso_Num) == 0
			cNosso_Num := StrZero( 1, nTam_NN )
		Endif

		If Empty( (caliasSE1)->E1_NUMBCO) //Titulo ainda nao impresso, calcula o proximo numero para o proximo boleto que sera impresso futuramente
			DbSelectArea("SEE")
			RecLock("SEE",.f.)
			SEE->EE_FAXATU := StrZero( Val(cNosso_Num) + 1, nTam_NN )
			SEE->(MsUnlock())
		Endif

		//montando codigo de barras
		//Caso o titulo ja tenha sido impresso sera pego o nosso numero do campo E1_NUMBCO
		CB_RN_NN    := Ret_cBarra(	Substr(aDadosBanco[1],1,3)+"9",;
			Subs(aDadosBanco[3],1,4),;
			aDadosBanco[4],;
			aDadosBanco[5],;
			SubStr(aDadosBanco[6],1,2),;
			AllTrim((caliasSE1)->E1_NUM)+AllTrim((caliasSE1)->E1_PARCELA),;
			_nSaldo,;
			(caliasSE1)->E1_VENCTO,; //********TSC815 ALTERADO DE E1_VENCREA PARA  E1_VENCTO******************
			SEE->EE_CODEMP,;
			cNosso_Num,;
			SEE->EE_CARTEIR)

		//aDadosTit    :=  {AllTrim((caliasSE1)->E1_NUM)+AllTrim((caliasSE1)->E1_PARCELA)  ,;             //Numero do titulo
		aDadosTit    :=  {AllTrim((caliasSE1)->E1_NUM)  ,;             //Numero do titulo
			(caliasSE1)->E1_EMISSAO      ,;             //Data da emissao do titulo
			MsDate()    ,;             //Data da emissao do boleto
			(caliasSE1)->E1_VENCTO  ,;             //Data do vencimento //********TSC815 ALTERADO DE E1_VENCREA PARA  E1_VENCTO******************
			_nSaldo,;             //Valor do titulo
			SubStr(CB_RN_NN[3],1,Len(CB_RN_NN[3])-1)+"-"+SubStr(CB_RN_NN[3],Len(CB_RN_NN[3]),1) ,; //Nosso numero (Ver formula para calculo)
			AllTrim((caliasSE1)->E1_TIPO)  ,;//TIPO DO TITULO
			AllTrim((caliasSE1)->E1_PARCELA),; //PARCELA DO TITULO
			SEE->EE_CODEMP,;//Cod Empresa
			AllTrim(SEE->EE_CODEMP)+SubStr(CB_RN_NN[3],1,Len(CB_RN_NN[3])-1)+SubStr(CB_RN_NN[3],Len(CB_RN_NN[3]),1) }

		//Mensagens boleto
		aBolText  := 	{}

		//Mensagem de desconto
		If (caliasSE1)->E1_DESCFIN > 0
			nValDesc := ((caliasSE1)->E1_DESCFIN * (caliasSE1)->E1_SALDO) / 100
			cDesconto := "DESCONTO DE R$ "+Alltrim(TransForm(nValDesc,"@E 9999,999,999.99"))+" P/ PAGTO ATE O VENCIMENTO"
			aAdd( aBolText , cDesconto )
		Endif

		//Mensagem para protesto/Negativacao
		If SubStr(SEE->EE_INSTPRI,1,2) == "66"
			cProtesto := "NEGATIVAR NO "+SEE->EE_DIASPRO+"o DIA APOS O VENCIMENTO"
			aAdd( aBolText , cProtesto )
		Else
			If Alltrim(SEE->EE_DIASPRO) <> "00" .And. !Empty(SEE->EE_DIASPRO)
				cProtesto := "PROTESTAR APÓS "+SEE->EE_DIASPRO+" DIA(S) DO VENCIMENTO."
				aAdd( aBolText , cProtesto )
			EndIf
		EndIf

		IF SEE->EE_TXJUROS > 0
			nValJuros := (SEE->EE_TXJUROS /100) * (caliasSE1)->E1_SALDO
			nValJuros := ROUND(nValJuros/30,2)
			cJuros    := "MORA DIA/COM. PERMANÊNCIA....................................R$ "+Alltrim(TransForm(nValJuros,"@E 9999,999,999.99"))
			aAdd( aBolText , cJuros )
		Endif

		/*	IF SEE->EE_MULTA > 0
			nValJuros := (SEE->EE_MULTA /100) * (caliasSE1)->E1_SALDO
			cJuros    := "APÓS "+ DTOC((caliasSE1)->E1_VENCTO) +" MULTA.........................................R$ "+Alltrim(TransForm(nValJuros,"@E 9999,999,999.99"))
			aAdd( aBolText , cJuros )
		Endif*/


		/*
		//Mensagem de juros
		If (caliasSE1)->E1_VALJUR > 0
			cJuros := "JUROS DE MORA POR DIA - R$ "+Alltrim(TransForm((caliasSE1)->E1_VALJUR,"@E 9999,999,999.99"))
			aAdd( aBolText , cJuros )
		ElseIf (caliasSE1)->E1_PORCJUR > 0
			nValJuros := ((caliasSE1)->E1_PORCJUR * (caliasSE1)->E1_SALDO) / 100
			cJuros    := "JUROS DE MORA POR DIA - R$ "+Alltrim(TransForm(nValJuros,"@E 9999,999,999.99"))
			aAdd( aBolText , cJuros )
		Endif */


		//Outras Mensagens de instrucao
		aAdd( aBolText , SEE->EE_MSG1 ) //Instrucao 1
		aAdd( aBolText , SEE->EE_MSG2 ) //Instrucao 2
		aAdd( aBolText , SEE->EE_MSG3 ) //Instrucao 3

		cLocPagto := SEE->EE_LOCPAG //Local para pagamento
		cEspecieD := SEE->EE_ESPDOC //Especie Doc
		cAceite   := SEE->EE_ACEITE //Aceite
		BB		:= Substr(aDadosBanco[1],1,3) == "001"
		BRADESCO	:= Substr(aDadosBanco[1],1,3) == "237"
		ITAU 		:= Substr(aDadosBanco[1],1,3) $ "341/655"
		SAFRA    	:= Substr(aDadosBanco[1],1,3) == "422"
		SANTANDER := Substr(aDadosBanco[1],1,3) == "033"
		CAIXAEF   := Substr(aDadosBanco[1],1,3) == "104"
		BANRISUL  := Substr(aDadosBanco[1],1,3) == "041"
		HSBC      := Substr(aDadosBanco[1],1,3) == "399"
		SICOOB    := Substr(aDadosBanco[1],1,3) == "756"
		SICREDI   := Substr(aDadosBanco[1],1,3) == "748"
		CECRED    := Substr(aDadosBanco[1],1,3) == "085"
		UNICRED   := Substr(aDadosBanco[1],1,3) == "091"
		cValCIP   := SEE->EE_VALCIP

		If Empty(AllTrim((caliasSE1)->E1_NUMBCO)) //AINDA NAO FOI IMPRESSO O TITULO
			SE1->(dbSetOrder(1))
			If SE1->(dbSeek(xFilial("SE1")+(cAliasSE1)->(E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO)))
				RecLock("SE1",.F.)
				SE1->E1_OCORREN	:= "01" //Registro de Titulos
				SE1->E1_INSTR1	:= IIf(Empty(SEE->EE_INSTPRI),"00",SubStr(SEE->EE_INSTPRI,1,2)) //"00" //05-Protestar no 5o. Dia Util (1o. Intrs cod.)
				SE1->E1_INSTR2 	:= "00" //00-Ausencia de Instrucoes (2a. Intr. cod.)
				SE1->E1_NUMBCO 	:= CB_RN_NN[3] //Nosso numero com ou sem digito verificador (depende da configuracao do banco)
				SE1->E1_PORTADO	:= SA6->A6_COD
				SE1->(MsUnlock())
			EndIf
		Endif

		// WALTER - 21/09/2018
		If _MV_PAR23 <> 1 //Se for gerar PDF
			nFatorH := 0.9
			nFatorV := 0.8
			nAddSay := 70
			nAddLin := 50
			nAddBco := 40

			//Define o nome do arquivo a ser gerado em PDF
			SE1->(dbSeek(xFilial("SE1")+(cAliasSE1)->(E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO)))
			If !Empty(SE1->E1_PARCELA)
				cFatura := AllTrim(SE1->E1_NUM)+"_"+AllTrim(SE1->E1_PARCELA)
			Else
				cFatura := AllTrim(SE1->E1_NUM)
			EndIf

			//VERIFICA SE  GERADO VIA JOB

			IF ! lDanfe	.and. (! l460nota .OR. !lGerar )
				IF lAutoExec

					cDirTmpFat :="\boleto\"

					nResol := 72

					Private oPrint := FWMSPrinter():New(cFatura,IMP_PDF,.T.,,.T.,,@oPrint,,.F.,,,.F.) //FWMSPrinter():New(cFatura,IMP_PDF,.T.,cDirTmpFat,.T.,,@oPrint,,.T.,,,.F.)
					oPrint:SetResolution(nResol)
					oPrint:SetPortrait()
					oPrint:SetPaperSize(DMPAPER_A4)
					oPrint:SetMargin(60,60,60,60)
					oPrint:SetViewPDF(.F.)
					oPrint:cPathPDF := cDirTmpFat

				ELSE

					cDirTmpFat := ALLTRIM(GETTEMPPATH()) //"\boleto\"

					nResol := 72

					Private oPrint := FWMSPrinter():New(cFatura,6,.T.,,.T.) //FWMSPrinter():New(cFatura,IMP_PDF,.T.,cDirTmpFat,.T.,,@oPrint,,.T.,,,.F.)
					oPrint:SetResolution(nResol)
					oPrint:SetPortrait()
					oPrint:cPathPDF := cDirTmpFat
					oPrint:SetPaperSize(DMPAPER_A4)
					oPrint:SetMargin(60,60,60,60)
					oPrint:SetViewPDF(.F.)

				ENDIF
			ENDIF

		Endif
		//FIM

		//If i <= len(aMarked)
		If aMarked[i] .and. (! l460nota .OR. !lGerar )
			Impress(oPrint,aBMP,aDadosEmp,aDadosTit,aDadosBanco,aDatPagador,aBolText,CB_RN_NN,cLocPagto,cValCIP,cEspecieD,cAceite)
			n := n + 1
		EndIf
		//Endif

		IF ! lDanfe .and. (! l460nota .OR. !lGerar )
			If _MV_PAR23 <> 1 //Se for gerar PDF
				oPrint:Print()   //Gerar em PDF

				IF !lAutoExec
					//move o PDF para o servidor
					CpyT2S( cDirTmpFat+cFatura+".PDF", "\boleto\" )
				ENDIF

				//move para o diretorio do parametro
				If !Empty(_MV_PAR24)
					CpyS2T("\boleto\"+cFatura+".PDF", AllTrim(_MV_PAR24) )
				EndIF

			Endif


			//Enviar PDF por email
			//AGLUTINA OS TITULOS POR CLIENTE - SOMENTE PARA ENVIO POR E-MAIL
			If _MV_PAR23 == 3

				cCliLoj := SE1->E1_CLIENTE + SE1->E1_LOJA //RETIRADO O ALLTRIM PARA CONSEGUIR POSICIONAR NO CLIENTE POSTERIORMENTE
				nPosCli := AScan(aAglutinaBol, {|x| AllTrim(x[1]) == cCliLoj })
				IF nPosCli == 0 //SE NAO ENCONTROU ADD NOVA LINE
					AADD( aAglutinaBol, {cCliLoj , {  cFatura  } }  )
				ELSE
					AADD( aAglutinaBol[nPosCli][2],  cFatura  )
				ENDIF

			Endif
		ENDIF

		DbSelectArea(cAliasSE1)
		dbSkip()
		IncProc()
		i++
	EndDo

	IF ! lDanfe .and. (! l460nota .OR. !lGerar )
		If _MV_PAR23 == 1 //Se for gera em tela
			oPrint:EndPage() //Finaliza a pagina
			oPrint:Preview() //Visualiza antes de imprimir
		Endif

		// ENVIAR PEDIDOS AGLUTINADOS POR CLIENTE
		If _MV_PAR23 == 3
			EnvEmail()
		Endif
	ENDIF


Return nil

//------------------------------------------------------------------------------------
// Imprime pagina
//------------------------------------------------------------------------------------
Static Function Impress(oPrint,aBitmap,aDadosEmp,aDadosTit,aDadosBanco,aDatPagador,aBolText,CB_RN_NN,cLocPagto,cValCIP,cEspecieD,cAceite)

	Local oFont8,nBol
	Local oFont10
	Local oFont16
	Local oFont16n
	Local oFont20
	Local oFont24
	Local i := 0
	Local aCoords1 := {150,1900,250,2300}   // FICHA DO PAGADOR
	Local aCoords2 := {420,1900,490,2300}   // FICHA DO PAGADOR
	Local aCoords3 := {1270,1900,1370,2300} // FICHA DO CAIXA
	Local aCoords4 := {1540,1900,1610,2300} // FICHA DO CAIXA
	Local aCoords5 := {2390,1900,2490,2300} // FICHA DE COMPENSACAO
	Local aCoords6 := {2660,1900,2730,2300} // FICHA DE COMPENSACAO
	Local oBrush

	//Parametros de TFont.New()
	//1.Nome da Fonte (Windows)
	//3.Tamanho em Pixels
	//5.Bold (T/F)
	oFont8  	:= TFont():New("Arial",9, 8,.T.,.F.,5,.T.,5,.T.,.F.)
	oFont09 	:= TFont():New("Arial",9, 9,.T.,.T.,5,.T.,5,.T.,.F.)
	oFont10 	:= TFont():New("Arial",9,10,.T.,.T.,5,.T.,5,.T.,.F.)
	oFont10n 	:= TFont():New("Arial",9,10,.T.,.F.,5,.T.,5,.T.,.F.)
	oFont14		:= TFont():New("Arial",9,14,.T.,.T.,5,.T.,5,.T.,.F.)
	oFont14n	:= TFont():New("Arial",9,13,.T.,.F.,5,.T.,5,.T.,.F.)
	oFont16 	:= TFont():New("Arial",9,16,.T.,.T.,5,.T.,5,.T.,.F.)
	oFont16n	:= TFont():New("Arial",9,16,.T.,.F.,5,.T.,5,.T.,.F.)
	oFont20		:= TFont():New("Arial",9,20,.T.,.T.,5,.T.,5,.T.,.F.)
	oFont20n	:= TFont():New("Arial",9,20,.T.,.F.,5,.T.,5,.T.,.F.)
	oFont24 	:= TFont():New("Arial",9,24,.T.,.T.,5,.T.,5,.T.,.F.)

	oBrush := TBrush():New("",4)

	oPrint:StartPage()   // Inicia uma nova pagina

	// Quando vier da Danfe, necessario ajustar o objeto
	IF lDanfe
		oPrint:lAdjustToLegacy := .T.
	Endif

	//Ficha do Caixa
	o_Line (150,100,150,2300)
	If File(Alltrim(aDadosBanco[1])+".bmp") //Verifica se existe imagem com o logo do banco -> A6_COD + ".bmp"
		o_SayBitMap(84-50,100,Alltrim(aDadosBanco[1])+".bmp",332,82 )  //imagem
	Else
		o_Say  (84,100,aDadosBanco[2],oFont16 )  //Nome Banco
	Endif
	o_Say  (84,1850,"Comprovante de Entrega",oFont10)
	o_Line (250,100,250,1300 )
	o_Line (350,100,350,1300 )
	o_Line (420,100,420,2300 )
	o_Line (490,100,490,2300 )

	o_Line (350,400,420,400)
	o_Line (420,500,490,500)
	o_Line (350,725,420,725)
	o_Line (350,850,420,850)

	o_Line (150,1300 ,490                                               ,1300 )
	o_Line (150,2300 ,490                                               ,2300 )
	o_Say  (150,1310 ,"MOTIVOS DE NAO ENTREGA (para uso do entregador)" ,oFont8)
	o_Say  (200,1310 ,"|   | Mudou-se"                                  ,oFont8)
	o_Say  (270,1310 ,"|   | Recusado"                                  ,oFont8)
	o_Say  (340,1310 ,"|   | Desconhecido"                              ,oFont8)

	o_Say  (200,1580 ,"|   | Ausente"                                   ,oFont8)
	o_Say  (270,1580 ,"|   | Nao Procurado"                             ,oFont8)
	o_Say  (340,1580 ,"|   | Endereco insuficiente"                     ,oFont8)

	o_Say  (200,1930 ,"|   | Nao existe o Numero"                       ,oFont8)
	o_Say  (270,1930 ,"|   | Falecido"                                  ,oFont8)
	o_Say  (340,1930 ,"|   | Outros(anotar no verso)"                   ,oFont8)

	o_Say  (420 ,1310 ,"Recebi(emos) o bloqueto"                         ,oFont8)
	o_Say  (450 ,1310 ,"com os dados ao lado."                           ,oFont8)
	o_Line (420 ,1700 ,490                                               ,1700)
	o_Say  (420 ,1705 ,"Data"                                            ,oFont8)
	o_Line (420 ,1900 ,490                                               ,1900)
	o_Say  (420 ,1905 ,"Assinatura"                                      ,oFont8)
	o_Say  (150 ,100  ,"Beneficiario"                                    ,oFont8)
	o_Say  (150 ,300  ,aDadosEmp[6]                                      ,oFont10n)
	o_Say  (185 ,100  ,AllTrim(aDadosEmp[1])                             ,oFont10)
	o_Say  (220 ,100  ,aDadosEmp[2]+"                                    , "+aDadosEmp[3] ,oFont8)

	cIndTmp  := At("-",aDatPagador[1])
	cCGCTmp  := SubStr(aDatPagador[1], At("-", aDatPagador[1])+2, Len(aDatPagador[1]))
	cPagador := SubStr(aDatPagador[1],1, At("-", aDatPagador[1])-2)

	o_Say  (250,100 ,"Pagador" ,oFont8)
	o_Say  (250,300 ,cCGCTmp   ,oFont10n)
	o_Say  (290,100 ,cPagador  ,oFont10)

	o_Say  (350,100 ,"Data do Vencimento"     ,oFont8)
	o_Say  (380,100 ,Substr(DTOS(aDadosTit[4]),7,2)+"/"+Substr(DTOS(aDadosTit[4]),5,2)+"/"+Substr(DTOS(aDadosTit[4]),1,4),oFont10)
	o_Say  (350,405 ,"Nro.Documento"           ,oFont8)
	IF EMPTY(aDadosTit[8])
		o_Say  (380,405 ,aDadosTit[1],oFont10)
	ELSE
		o_Say  (380,405 ,aDadosTit[1]+'-'+aDadosTit[8] ,oFont10)
	ENDIF

	o_Say  (350    ,730,"Moeda"           ,oFont8)
	If HSBC
		o_Say  (380,755,"REAL"            ,oFont10)
	Else
		o_Say  (380,755,GetMv("MV_SIMB1") ,oFont10)
	EndIf

	o_Say  (350,855,"Valor/Quantidade",oFont8)
	o_Say  (380,855,AllTrim(Transform(aDadosTit[5],"@E 999,999,999.99")),oFont10)

	o_Say  (420,100 ,"Agencia/Codigo do Beneficiario" ,oFont8)
	If CAIXAEF   //LAIANA
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(Transform(SEE->EE_CODEMP,"@R 999999-9")),oFont10)
	ElseIf SANTANDER //LAIANA
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10)

	ElseIf HSBC //LAIANA
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+" "+aDadosBanco[4]+aDadosBanco[5],oFont10)

	Elseif SICOOB   //LAIANA
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10)

	ElseIf SICREDI
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+"."+Alltrim(SEE->EE_CODPROD)+"."+Alltrim(SEE->EE_CODEMP),oFont10)

	ElseIf ITAU
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+"/"+aDadosBanco[4]+"-"+aDadosBanco[5],oFont10)

	ElseIf UNICRED
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10)

	ElseIf SAFRA
		o_Say  (450,100,Alltrim(SEE->EE_AGENCIA)+Alltrim(SEE->EE_DVAGE)+"/"+Alltrim(SEE->EE_CONTA)+Alltrim(SEE->EE_DVCTA),oFont10)

	Else
		o_Say  (450,100,aDadosBanco[3]+"/"+aDadosBanco[4]+Iif(!Empty(aDadosBanco[5]),"-"+aDadosBanco[5],""),oFont10)

	Endif
	o_Say  (420,505,"Nosso Numero",oFont8)

	If BRADESCO
		o_Say  (450,505,aDadosBanco[6]+"/"+SubStr(aDadosTit[6], Len(aDadosTit[6])-12, 13),oFont10)

	ElseIf BB
		o_Say  (450,505,Alltrim(Substr(aDadosTit[9],1,7))+SUBSTR(aDadosTit[6],1,10),oFont10)  //LAIANA

	ElseIf ITAU
		o_Say  (450,505,aDadosBanco[6]+"/"+substr(aDadosTit[6],1,len(aDadosTit[6])),oFont10)

	ElseIf CAIXAEF
		o_Say  (450,505,"14/0000"+substr(aDadosTit[6],1,13),oFont10) //laiana

	Elseif CECRED
		_cNossoNr := aDadosBanco[4] + aDadosBanco[5] + substr(aDadosTit[6],1,9)
		o_Say  (450,520,AllTrim(_cNossoNr),oFont10)

	Elseif UNICRED
		_cNossoNr := AllTrim(SEE->EE_CODEMP) + aDadosTit[6]
		o_Say  (450,505,_cNossoNr,oFont10)

	Else
		o_Say  (450,505,aDadosTit[6],oFont10)

	EndIf

	For i := 100 to 2300 step 50
		o_Line( 520, i, 520, i+30)
	Next i

	For i := 100 to 2300 step 50
		o_Line( 1080, i, 1080, i+30)
	Next i

	/*
	 Ficha do Pagador
	*/
	o_Line (1270,100,1270,2300)
	o_Line (1270,650,1170,650 )
	o_Line (1270,900,1170,900 )
	If File(Alltrim(aDadosBanco[1])+".bmp") //Verifica se existe imagem com o logo do banco -> A6_COD + ".bmp"
		o_SayBitMap(1204-50,100,Alltrim(aDadosBanco[1])+".bmp",332,82 )  //imagem
	Else
		o_Say  (1204,100,aDadosBanco[2],oFont16 ) //Nome Banco (ou imagem)
	Endif
	If BRADESCO
		o_Say  (1182,680,aDadosBanco[1]+"-2",oFont20 )

	ElseIf ITAU
		o_Say  (1182,680,aDadosBanco[1]+"-7",oFont20 )

	ElseIf SAFRA
		o_Say  (1182,680,aDadosBanco[1]+"-7",oFont20 )

	ElseIf HSBC
		o_Say  (1182,680,aDadosBanco[1]+"-9",oFont20 )

	ElseIf SICOOB
		o_Say  (1182,680,aDadosBanco[1]+"-0",oFont20 )

	ElseIf SICREDI
		o_Say  (1182,680,aDadosBanco[1]+"-X",oFont20 )

	ElseIf UNICRED
		o_Say  (1182,680,aDadosBanco[1]+"-4",oFont20 )

	ElseIf CAIXAEF
		o_Say  (1182,680,aDadosBanco[1]+"-"+Modulo11(aDadosBanco[1],aDadosBanco[1]),oFont20n )

	Else
		o_Say  (1182,680,aDadosBanco[1]+"-"+Modulo11(aDadosBanco[1],aDadosBanco[1]),oFont20 )
	EndIf

	o_Line (1370,100,1370,2300 )
	o_Line (1470,100,1470,2300 )
	o_Line (1540,100,1540,2300 )
	o_Line (1610,100,1610,2300 )

	o_Line (1470,500,1610,500)
	o_Line (1540,750,1610,750)
	o_Line (1470,1000,1610,1000)
	o_Line (1470,1350,1540,1350)
	o_Line (1470,1550,1610,1550)

	o_Say  (1270,100 ,"Local de Pagamento" ,oFont8)
	o_Say  (1310,100 ,cLocPagto            ,oFont10)

	o_Say  (1270,1910,"Vencimento"         ,oFont8)

	//nFieldSize := CalcFieldSize("C",10,0,"@R XX/XX/XXXX","Vencimento",oFont10)
	o_Say  (1310,2090,Substr(DTOS(aDadosTit[4]),7,2)+"/"+Substr(DTOS(aDadosTit[4]),5,2)+"/"+Substr(DTOS(aDadosTit[4]),1,4),oFont10,150,,1)

	o_Say  (1370,100 ,"Beneficiario"                           ,oFont8)
	o_Say  (1405,100 ,AllTrim(aDadosEmp[1])+" - "+aDadosEmp[6] ,oFont10)
	o_Say  (1440,100 ,aDadosEmp[2]+"                           , "+aDadosEmp[3] ,oFont8)
	o_Say  (1370,1910,"Agencia/Codigo do Beneficiario"         ,oFont8)

	If SAFRA
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+Alltrim(SEE->EE_DVAGE)+"/"+Alltrim(SEE->EE_CONTA)+Alltrim(SEE->EE_DVCTA),oFont10)

	Elseif CAIXAEF   //LAIANA
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(Transform(SEE->EE_CODEMP,"@R 999999-9")),oFont10,150,,1)

	Elseif SANTANDER   //LAIANA
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10,150,,1)

	ElseIf HSBC //LAIANA
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+" "+aDadosBanco[4]+aDadosBanco[5],oFont10,150,,1)

	Elseif SICOOB   //LAIANA
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10,150,,1)

	ElseIf SICREDI
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+"."+Alltrim(SEE->EE_CODPROD)+"."+Alltrim(SEE->EE_CODEMP),oFont10,150,,1)

	ElseIf ITAU
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+"/"+aDadosBanco[4]+"-"+aDadosBanco[5],oFont10)

	ElseIf UNICRED
		o_Say  (1410,2050,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10)

	Else
		o_Say  (1410,2050,aDadosBanco[3]+"/"+aDadosBanco[4]+Iif(!Empty(aDadosBanco[5]),"-"+aDadosBanco[5],""),oFont10,150,,1)
	Endif

	o_Say  (1470,100 ,"Data do Documento"                              ,oFont8)
	o_Say  (1500,100 ,Substr(DTOS(aDadosTit[2]),7,2)+"/"+Substr(DTOS(aDadosTit[2]),5,2)+"/"+Substr(DTOS(aDadosTit[2]),1,4),oFont10)

	o_Say  (1470,505 ,"Nro.Documento"               ,oFont8)
	IF EMPTY(aDadosTit[8])
		o_Say  (1500,505 ,aDadosTit[1] ,oFont10)
	ELSE
		o_Say  (1500,505 ,aDadosTit[1]+'-'+aDadosTit[8] ,oFont10)
	ENDIF

	o_Say  (1470,1005,"Especie Doc."                ,oFont8)

	If HSBC
		o_Say  (1500,1155 ,"PD"      ,oFont10)
	ElseIf SICOOB
		o_Say  (1500,1155 ,"DM"      ,oFont10)
	ElseIf CAIXAEF
		o_Say  (1500,1155 ,"DMI"     ,oFont10)
	Else
		o_Say  (1500,1155 ,cEspecieD ,oFont10)
	Endif
	o_Say  (1470    ,1355 ,"Aceite"  ,oFont8)
	If HSBC
		o_Say  (1500,1415 ,"NAO"     ,oFont10)
	ElseIf SICOOB
		o_Say  (1500,1415 ,"N"       ,oFont10)
	Else
		o_Say  (1500,1415 ,cAceite   ,oFont10)
	EndIf

	o_Say  (1470,1555,"Data do Processamento"                          ,oFont8)
	o_Say  (1500,1655,Substr(DTOS(aDadosTit[2]),7,2)+"/"+Substr(DTOS(aDadosTit[2]),5,2)+"/"+Substr(DTOS(aDadosTit[2]),1,4)                               ,oFont10)

	o_Say  (1470,1910,"Nosso Numero"                                   ,oFont8)
	If BRADESCO
		o_Say  (1500,2010,aDadosBanco[6]+"/"+SubStr(aDadosTit[6], Len(aDadosTit[6])-12, 13)       ,oFont10,150,,1)
	ElseIf BB
		o_Say  (1500,2010,Alltrim(Substr(aDadosTit[9],1,7))+SUBSTR(aDadosTit[6],1,10),oFont10,150,,1)  //LAIANA
	ElseIf ITAU
		o_Say  (1500,2010,aDadosBanco[6]+"/"+substr(aDadosTit[6],1,len(aDadosTit[6]))        ,oFont10,150,,1)
	ElseIf CAIXAEF
		o_Say  (1500,1900,"14/0000"+substr(aDadosTit[6],1,13),oFont10,150,,1) //laiana
	ElseIf SICREDI
		o_Say  (1500,2010,SubStr(AllTrim(aDadosTit[6]),1,2)+"/"+SubStr(AllTrim(aDadosTit[6]),3,6)+SubStr(AllTrim(aDadosTit[6]),9,2),oFont10,150,,1)
	Elseif CECRED
		//NOSSO NUMERO = CONTA CORRENTE + DV COOPERADO +  NUMERO DO BOLETO E1_NUMBCO
		o_Say  (1500,1930,ALLTRIM(_cNossoNr),oFont10)
	Else
		o_Say  (1500,2010,aDadosTit[6],oFont10,150,,1)
	EndIf

	o_Say  (1540,100 ,"Uso do Banco"	,oFont8)

	If !Empty(cValCIP)
		o_Line(1540,405,1610,405)
		o_Say(1540,410,"CIP")
		o_Say(1570,435,cValCIP,oFont10)
	EndIf

	o_Say  (1540    ,505 ,"Carteira"     ,oFont8)
	If HSBC
		o_Say  (1570,505 ,"CSB"          ,oFont10)
	ElseIf SICOOB
		o_Say  (1570,505 ,"1"            ,oFont10)
	ElseIf SICREDI
		o_Say  (1570,505 ,"11"           ,oFont10)
	Else
		o_Say  (1570,505 ,aDadosBanco[6] ,oFont10)
	EndIf

	If CAIXAEF //LAIANA
		o_Say  (1540,755 ,"Moeda"                       ,oFont8) //LAIANA
	Else //LAIANA
		o_Say  (1540,755 ,"Especie"                     ,oFont8)
	Endif
	If HSBC
		o_Say  (1570,755 ,"REAL"                        ,oFont10)
	Else
		o_Say  (1570,755 ,GetMv("MV_SIMB1")             ,oFont10)
	EndIf
	o_Say  (1540    ,1005,"Quantidade"                  ,oFont8)
	o_Say  (1540    ,1555,"Valor"                       ,oFont8)

	o_Say  (1540,1910,"( = ) Valor do Documento"                          ,oFont8)
	o_Say  (1570,2170,AllTrim(Transform(aDadosTit[5],"@E 999,999,999.99")),oFont10,150,,1)

	o_Say  (1610,100 ,"Instrucoes (Texto de Responsabilidade do Beneficiario): ",oFont8)
	For nBol := 1 To 6
		If Len(aBolText) >= nBol
			o_Say  (1630+(40*nBol),100 ,aBolText[nBol],oFont09)
		Endif
	Next nBol

	o_Say  (1610     ,1910,"( - ) Desconto/Abatimento" ,oFont8)
	o_Say  (1680     ,1910,"( - ) Outras Deducoes"     ,oFont8)
	o_Say  (1750     ,1910,"( + ) Mora/Multa/Juros "   ,oFont8)
	o_Say  (1820     ,1910,"( + ) Outros Acrescimos"   ,oFont8)
	o_Say  (1890     ,1910,"( = ) Valor Cobrado"       ,oFont8)

	If BB
		o_Say  (1960 ,100 ,"Pagador:"         ,oFont8)
	Else
		o_Say  (1960 ,100 ,"Pagador/Avalista:",oFont8)
	EndIf
	o_Say  (1988  ,210 ,aDatPagador[1]+" ("+aDatPagador[2]+")"                  ,oFont8)
	o_Say  (2030  ,210 ,aDatPagador[3]                                          ,oFont8)
	o_Say  (2070  ,210 ,aDatPagador[6]+"  "+aDatPagador[4]+" - "+aDatPagador[5] ,oFont8)
	o_Say  (2110  ,1500,"Autenticacao Mecanica "                                ,oFont8)

	If CAIXAEF  //LAIANA
		o_Say  (2150,100,"SAC CAIXA: 0800 726 0101 (informacoes, reclamacoes, sugestoes e elogios). Para pessoas com deficiencia auditiva ou de fala: 0800 726 2492."  ,oFont8) //LAIANA
		o_Say  (2190,100,"Ouvidoria: 0800 725 7474 (reclamacoes nao solucionadas e denuncias). www.caixa.gov.br" ,oFont8) //LAIANA
	Endif  // LAIANA
	o_Say  (1204,1850,"Recibo do Pagador"                              ,oFont10)
	o_Line (1270,1900,1960,1900 )
	o_Line (1680,1900,1680,2300 )
	o_Line (1750,1900,1750,2300 )
	o_Line (1820,1900,1820,2300 )
	o_Line (1890,1900,1890,2300 )
	o_Line (1960,100 ,1960,2300 )
	o_Line (2105,100,2105,2300  )

	For i := 100 to 2300 step 50
		o_Line( 2270, i, 2270, i+30)
	Next i

	/*
		Ficha de Compensacao
	*/
	o_Line (2390,100,2390,2300)
	o_Line (2390,650,2290,650 )
	o_Line (2390,900,2290,900 )

	If File(Alltrim(aDadosBanco[1])+".bmp") //Verifica se existe imagem com o logo do banco -> A6_COD + ".bmp"
		o_SayBitMap(2324-50,100,Alltrim(aDadosBanco[1])+".bmp",332,82 )  //imagem
	Else
		o_Say  (2324,100,aDadosBanco[2],oFont16 )  //Nome do Banco
	Endif

	If BRADESCO
		o_Say  (2302,680,aDadosBanco[1]+"-2",oFont20 )
	ElseIf ITAU
		o_Say  (2302,680,aDadosBanco[1]+"-7",oFont20 )
	ElseIf SAFRA
		o_Say  (2302,680,aDadosBanco[1]+"-7",oFont20 )
	ElseIf HSBC
		o_Say  (2302,680,aDadosBanco[1]+"-9",oFont20 )
	ElseIf SICREDI
		o_Say  (2302,680,aDadosBanco[1]+"-X",oFont20 )
	ElseIf UNICRED
		o_Say  (2302,680,aDadosBanco[1]+"-4",oFont20 )
	ElseIf CAIXAEF
		o_Say  (2302,680,aDadosBanco[1]+"-"+Modulo11(aDadosBanco[1],aDadosBanco[1]),oFont20n )
	Else
		o_Say  (2302,680,aDadosBanco[1]+"-"+Modulo11(aDadosBanco[1],aDadosBanco[1]),oFont20 )
	EndIf
	o_Say  (2324,920,CB_RN_NN[2],oFont14n) //linha digitavel

	o_Line (2490,100,2490,2300 )
	o_Line (2590,100,2590,2300 )
	o_Line (2660,100,2660,2300 )
	o_Line (2730,100,2730,2300 )

	o_Line (2590,500,2730,500)
	o_Line (2660,750,2730,750)
	o_Line (2590,1000,2730,1000)
	o_Line (2590,1350,2660,1350)
	o_Line (2590,1550,2730,1550)

	o_Say  (2390,100 ,"Local de Pagamento" ,oFont8)
	o_Say  (2430,100 ,cLocPagto            ,oFont10)

	o_Say  (2390,1910,"Vencimento"         ,oFont8)
	o_Say  (2430,2090,Substr(DTOS(aDadosTit[4]),7,2)+"/"+Substr(DTOS(aDadosTit[4]),5,2)+"/"+Substr(DTOS(aDadosTit[4]),1,4),oFont10,150,,1)

	o_Say  (2490,100 ,"Beneficiario"                           ,oFont8)
	o_Say  (2525,100 ,AllTrim(aDadosEmp[1])+" - "+aDadosEmp[6] ,oFont10)
	o_Say  (2560,100 ,aDadosEmp[2]+", "+aDadosEmp[3] 		   ,oFont8)
	o_Say  (2490,1910,"Agencia/Codigo do Beneficiario"         ,oFont8)
	If SAFRA
		o_Say  (2530,2050,Alltrim(SEE->EE_AGENCIA)+Alltrim(SEE->EE_DVAGE)+"/"+Alltrim(SEE->EE_CONTA)+Alltrim(SEE->EE_DVCTA),oFont10)
		//o_Say  (2530,2050,PadL(aDadosBanco[3],5,"0")+"/"+aDadosBanco[4]+Iif(!Empty(aDadosBanco[5]),"-"+aDadosBanco[5],""),oFont10,150,,1)
	Elseif CAIXAEF   //LAIANA
		o_Say  (2530,2050,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(Transform(SEE->EE_CODEMP,"@R 999999-9")),oFont10,150,,1)
	Elseif SANTANDER   //LAIANA
		o_Say  (2530,2050,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10,150,,1)
	ElseIf HSBC //LAIANA
		o_Say  (2530,2050,Alltrim(SEE->EE_AGENCIA)+" "+aDadosBanco[4]+aDadosBanco[5],oFont10,150,,1)
	Elseif SICOOB   //LAIANA
		o_Say  (2530,2050,Alltrim(SEE->EE_AGENCIA)+"/"+Alltrim(SEE->EE_CODEMP),oFont10,150,,1)
	ElseIf SICREDI
		o_Say  (2530,2050,Alltrim(SEE->EE_AGENCIA)+"."+Alltrim(SEE->EE_CODPROD)+"."+Alltrim(SEE->EE_CODEMP),oFont10,150,,1)
	ElseIf ITAU
		o_Say  (2530,2050,Alltrim(SEE->EE_AGENCIA)+"/"+aDadosBanco[4]+"-"+aDadosBanco[5],oFont10)
	Else
		o_Say  (2530,2050,aDadosBanco[3]+"/"+aDadosBanco[4]+Iif(!Empty(aDadosBanco[5]),"-"+aDadosBanco[5],""),oFont10,150,,1)
	Endif
	o_Say  (2590,100 ,"Data do Documento" ,oFont8)
	o_Say  (2620,100 ,Substr(DTOS(aDadosTit[2]),7,2)+"/"+Substr(DTOS(aDadosTit[2]),5,2)+"/"+Substr(DTOS(aDadosTit[2]),1,4),oFont10,150,,1)

	o_Say  (2590,505 ,"Nro.Documento"               ,oFont8)
	IF EMPTY(aDadosTit[8])
		o_Say  (2620,505 ,aDadosTit[1] ,oFont10)
	ELSE
		o_Say  (2620,505 ,aDadosTit[1]+'-'+aDadosTit[8] ,oFont10)
	ENDIF

	o_Say  (2590,1005,"Especie Doc."                ,oFont8)

	If HSBC
		o_Say  (2620,1155 ,"PD"      ,oFont10)
	ElseIf SICOOB
		o_Say  (2620,1155 ,"DM"      ,oFont10)
	ElseIf CAIXAEF
		o_Say  (2620,1155 ,"DMI"     ,oFont10)
	Else
		o_Say  (2620,1155 ,cEspecieD ,oFont10)
	Endif

	o_Say  (2590,1355 ,"Aceite" 	 ,oFont8)

	If HSBC
		o_Say  (2620,1415 ,"NAO"   ,oFont10)
	ElseIf SICOOB
		o_Say  (2620,1415 ,"N"     ,oFont10)
	Else
		o_Say  (2620,1415 ,cAceite ,oFont10)
	EndIf

	o_Say  (2590,1555,"Data do Processamento"                          ,oFont8)
	o_Say  (2620,1655,Substr(DTOS(aDadosTit[2]),7,2)+"/"+Substr(DTOS(aDadosTit[2]),5,2)+"/"+Substr(DTOS(aDadosTit[2]),1,4)                               ,oFont10)

	o_Say  (2590,1910,"Nosso Numero"                                   ,oFont8)
	If BRADESCO
		o_Say  (2620,2010,aDadosBanco[6]+"/"+SubStr(aDadosTit[6], Len(aDadosTit[6])-12, 13)        ,oFont10,150,,1)
	ElseIf BB
		//o_Say  (2620,1930,Alltrim(Substr(aDadosTit[9],1,7))+aDadosTit[6],oFont10)
		o_Say  (2620,2010,Alltrim(Substr(aDadosTit[9],1,7))+SUBSTR(aDadosTit[6],1,10),oFont10,150,,1)  //LAIANA
	ElseIf ITAU
		o_Say  (2620,2010,aDadosBanco[6]+"/"+substr(aDadosTit[6],1,len(aDadosTit[6]))        ,oFont10,150,,1)
	ElseIf CAIXAEF
		o_Say  (2620,1900,"14/0000"+substr(aDadosTit[6],1,13),oFont10,150,,1) //laiana
	ElseIf SICREDI
		o_Say  (2620,2010,SubStr(AllTrim(aDadosTit[6]),1,2)+"/"+SubStr(AllTrim(aDadosTit[6]),3,6)+SubStr(AllTrim(aDadosTit[6]),9,2),oFont10,150,,1)
	Elseif CECRED
		//NOSSO NUMERO = CONTA CORRENTE + DV COOPERADO +  NUMERO DO BOLETO E1_NUMBCO
		o_Say  (2620,1930,ALLTRIM(_cNossoNr),oFont10)
	Else
		o_Say  (2620,2010,aDadosTit[6],oFont10,150,,1)
	EndIf

	o_Say  (2660,100 ,"Uso do Banco"	,oFont8)

	If !Empty(cValCIP)
		o_Line(2660,405,2730,405)
		o_Say(2660,410,"CIP")
		o_Say(2690,435,cValCIP,oFont10)
	EndIf

	o_Say  (2660    ,505 ,"Carteira"     ,oFont8)
	If HSBC
		o_Say  (2690,505 ,"CSB"          ,oFont10)
	ElseIf SICOOB
		o_Say  (2690,505 ,"1"            ,oFont10)
	ElseIf SICREDI
		o_Say  (2690,505 ,"11"           ,oFont10)
	Else
		o_Say  (2690,505 ,aDadosBanco[6] ,oFont10)
	EndIf

	If CAIXAEF //LAIANA
		o_Say  (2660,755 ,"Moeda"           ,oFont8)    //LAIANA
	Else     //LAIANA
		o_Say  (2660,755 ,"Especie"         ,oFont8)
	Endif
	If HSBC
		o_Say  (2690,755 ,"REAL"            ,oFont10)
	Else
		o_Say  (2690,755 ,GetMv("MV_SIMB1") ,oFont10)
	EndIf

	o_Say  (2660    ,1005,"Quantidade"      ,oFont8)
	o_Say  (2660    ,1555,"Valor"           ,oFont8)

	o_Say  (2660,1910,"( = ) Valor do Documento"                          ,oFont8)
	o_Say  (2690,2170,AllTrim(Transform(aDadosTit[5],"@E 999,999,999.99")),oFont10,150,,1)
	o_Say  (2730,100 ,"Instrucoes (Texto de Responsabilidade do Beneficiario): ",oFont8)

	For nBol := 1 To 6
		If Len(aBolText) >= nBol
			o_Say  (2750+(40*nBol),100 ,aBolText[nBol],oFont09)
		Endif
	Next nBol

	If CAIXAEF   //LAIANA
		o_Say  (2730,1910,"( - ) Desconto"			                         	,oFont8)
	else
		o_Say  (2730,1910,"( - ) Desconto/Abatimento"                         	,oFont8)
	Endif
	If CAIXAEF
		o_Say  (2800,1910,"( - ) Outras Deducoes/Abatimentos"                 	,oFont8)
	else
		o_Say  (2800,1910,"( - ) Outras Deducoes"                             	,oFont8)
	Endif        //LAIANA

	o_Say  (2870,1910,"( + ) Mora/Multa/Juros "                           	,oFont8)
	o_Say  (2940,1910,"( + ) Outros Acrescimos"                           	,oFont8)
	o_Say  (3010,1910,"( = ) Valor Cobrado"                               	,oFont8)

	o_Say  (3080  ,100 ,"Pagador"                                               ,oFont8)
	o_Say  (3108  ,210 ,aDatPagador[1]+" ("+aDatPagador[2]+")"                  ,oFont8)
	o_Say  (3148  ,210 ,aDatPagador[3]                                          ,oFont8)
	o_Say  (3188  ,210 ,aDatPagador[6]+"  "+aDatPagador[4]+" - "+aDatPagador[5] ,oFont8)

	o_Say  (3228  ,100 ,"Pagador/Avalista"                                      ,oFont8)
	//o_Say  (3228,100 ,"Sacador/Avalista"                                      ,oFont8)
	o_Say  (3270  ,1500,"Autenticacao Mecanica"                                 ,oFont8)
	o_Say  (3270  ,1850,"Ficha de Compensacao"                                  ,oFont10)


	o_Line(2390,1900,3080,1900)
	o_Line(2800,1900,2800,2300)
	o_Line(2870,1900,2870,2300)
	o_Line(2940,1900,2940,2300)
	o_Line(3010,1900,3010,2300)
	o_Line(3080,100 ,3080,2300)

	o_Line (3265,100,3265,2300)

	If _MV_PAR23 == 1 //Se for imprimir em tela
		MSBAR("INT25"  ,28.9,1.3,CB_RN_NN[1],oPrint,.F.,,,0.025,1.3,,,,.F.)
	Else
		nPosicao := 3285/1.2 //788
		nColBar  := 150 //30
		nWidth   := 0.80
		nHeigth  := 36
		oPrint:Int25(nPosicao,nColBar,CB_RN_NN[1],nWidth,nHeigth,.F.,.F.)
	Endif



	/*
	Parametros 01 cTypeBar String com o tipo do codigo de barras
	                       "EAN13","EAN8","UPCA" ,"SUP5"   ,"CODE128"
	                       "INT25","MAT25,"IND25","CODABAR" ,"CODE3_9"
	           02 nRow     Numero da Linha em centimentros
	           03 nCol     Numero da coluna em centimentros
	           04 cCode    String com o conteudo do codigo
	           05 oPr      Objeto Printer
	           06 lcheck   Se calcula o digito de controle
	           07 Cor      Numero  da Cor, utilize a "common.ch"
	           08 lHort    Se imprime na Horizontal
	           09 nWidth   Numero do Tamanho da barra em centimetros
	           10 nHeigth  Numero da Altura da barra em milimetros
	           11 lBanner  Se imprime o linha em baixo do codigo
	           12 cFont    String com o tipo de fonte
	           13 cMode    String com o modo do codigo de barras CODE128
	*/

	oPrint:EndPage() // Finaliza a pagina

	// TSC959 - Thiago.Zoppi - Quando vier da Danfe, necessário para ajusta boleto na impressao
	IF lDanfe
		oPrint:lAdjustToLegacy := .F.
	Endif

Return Nil

//------------------------------------------------------------------------------------
// Calcula modulo 10
//------------------------------------------------------------------------------------
Static Function Modulo10(cData)

	Local L,D,P	:= 0
	Local B    	:= .F.

	L := Len(cData)
	B := .T.
	D := 0

	While L > 0
		P := Val(SubStr(cData, L, 1))
		If (B)
			P := P * 2
			If P > 9
				P := P - 9
			End
		End
		D := D + P
		L := L - 1
		B := !B
	End

	D := 10 - (Mod(D,10))

	If D = 10
		D := 0
	End

Return(D)

//------------------------------------------------------------------------------------
// Calcula modulo 11
//------------------------------------------------------------------------------------
Static Function Modulo11(cData,cBanc,cCarteira)

	Local L, D, P, X := 0
	Local aPeso := {}
	Local nCnt  := 0
	Private nBase

	If cBanc == "001" //Banco do Brasil
		L := Len(cdata)
		D  := 0
		DS := 0
		P := 6
		X := 0
		for X=1 to L
			P := P + 1
			if P = 10
				P := 2
			end

			DS := DS + (Val(SubStr(cData, X, 1)) * P)
			//L := L - 1
		next

		D := int( (DS / 11) )
		D := DS - (D * 11)

		If D == 10
			D := "X"
		Else
			D := AllTrim(Str(D))
		End

	ElseIf cBanc == "237" //Bradesco

		nSoma1 := val(subs(cCarteira,01,1))*2
		nSoma2 := val(subs(cCarteira,02,1))*7
		nSoma3 := val(subs(cData,01,1))   *6
		nSoma4 := val(subs(cData,02,1))   *5
		nSoma5 := val(subs(cData,03,1))   *4
		nSoma6 := val(subs(cData,04,1))   *3
		nSoma7 := val(subs(cData,05,1))   *2
		nSoma8 := val(subs(cData,06,1))   *7
		nSoma9 := val(subs(cData,07,1))   *6
		nSomaA := val(subs(cData,08,1))   *5
		nSomaB := val(subs(cData,09,1))   *4
		nSomaC := val(subs(cData,10,1))   *3
		nSomaD := val(subs(cData,11,1))   *2

		cDigito := mod(nSoma1+nSoma2+nSoma3+nSoma4+nSoma5+nSoma6+nSoma7+nSoma8+nSoma9+nSomaA+nSomaB+nSomaC+nSomaD,11)

		D := iif(cDigito == 1, "P", iif(cDigito == 0 , "0", strzero(11-cDigito,1)))

	ElseIf cBanc == "422" //.Or. cBanc == "104" //SAFRA ou CAIXA (CEF) // RETIRADO WALTER TSC022 13/07/2016

		/*
		nCnt	:= 0
		cDigito:= 0
		nSoma	:= 0
		nBase	:= 0
		aPeso	:= {9,8,7,6,5,4,3,2};

		nBase := Len(aPeso)+1

		FOR nCnt := Len(cData) TO 1 STEP -1
		nBase := IF(--nBase = 0,Len(aPeso),nBase)
		nSoma += Val(SUBS(cData,nCnt,01)) * aPeso[nBase]
		NEXT

		nResto	:= (nSoma % 11)

		cDigito := 11 - nResto

		D := cDigito
		*/

		L := Len(cdata)
		D := 0
		//    12345678
		//    26173001
		P := "23456789" // Constante Conforme Manual Safra
		While L > 0
			D := D + (Val(SubStr(cData, L, 1)) * Val(SubStr(P, L, 1)))
			L := L - 1
		End

		D  := Mod(D,11)

		If D == 0
			D := 1
		ElseIf D == 1
			D := 0
		Else
			D  := 11 - D
		EndIf

		D := AllTrim(Str(D))

	ElseIf cBanc == "341" //ITAU
		L := Len(cdata)
		D := 0
		C := 0

		D1 := Space(1)
		D2 := Space(1)
		_X1:= 0

		P := "12121212121212121212" // Constante Conforme Manual Itau
		While L > 0
			C := (Val(SubStr(cData, L, 1)) * Val(SubStr(P, L, 1)))
			If C > 9
				_X1 := StrZero(C,2)
				D1 := SubStr(_X1,1,1)
				D2 := SubStr(_X1,2,1)
				D  := D + (Val(D1) + Val(D2))
			Else
				D := D + (Val(SubStr(cData, L, 1)) * Val(SubStr(P, L, 1)))
			EndIf
			L := L - 1
		End

		D := Mod(D,10)
		D := 10 - D
		If D == 10
			D := 0
		Else
			D := AllTrim(Str(D))
		EndIf

		//ElseIf cBanc == "341" .Or. cBanc == "655" //ITAU ou VOTORANTIM
	ElseIf cBanc == "655" // VOTORANTIM

		nCnt	:= 0
		cDigito:= 0
		nSoma	:= 0
		nBase	:= 0
		aPeso	:= {9,8,7,6,5,4,3,2};

		nBase := Len(aPeso)+1

		FOR nCnt := Len(cData) TO 1 STEP -1
			nBase := IF(--nBase = 0,Len(aPeso),nBase)
			nSoma += Val(SUBS(cData,nCnt,01)) * aPeso[nBase]
		NEXT

		cDigito := 11 - (nSoma % 11)

		DO CASE
			CASE cDigito = 0
				cDigito := "1"
			CASE cDigito > 9
				cDigito := "1"
			OTHERWISE
				cDigito := STR( cDigito, 1, 0 )
		ENDCASE

		D := cDigito

	ElseIf cBanc == "479" // ITAUBANK - NAO EH ITAU
		L := Len(cdata)
		D := 0
		P := 1
		While L > 0
			P := P + 1
			D := D + (Val(SubStr(cData, L, 1)) * P)
			If P = 9
				P := 1
			End
			L := L - 1
		End
		D := Mod(D*10,11)
		If D == 10
			D := 0
		End
		D := AllTrim(Str(D))

	ElseIf cBanc == "399" //HSBC
		L := Len(cdata)
		D := 0
		P := 1
		While L > 0
			P := P + 1
			D := D + (Val(SubStr(cData, L, 1)) * P)
			If P = 7
				P := 1
			End
			L := L - 1
		End
		D := Mod(D,11)
		If D == 0 .Or. D == 1
			D := 0
			D := AllTrim(Str(D))
		Else
			D := 11 - D
			D := AllTrim(Str(D))
		EndIf

	ElseIf cBanc == "104" //CEF WALTER TSC022 13/07/2016
		L := Len(cdata)
		D := 0
		P := 1
		While L > 0
			P := P + 1
			D := D + (Val(SubStr(cData, L, 1)) * P)
			If P = 9
				P := 1
			EndIf
			L := L - 1
		End
		D := Mod(D,11)
		D := 11 - D
		If D > 9
			D := 0
		EndIf
		D := AllTrim(Str(D))

	ElseIf cBanc == "756" //SICOOB
		L := Len(cdata)
		D := 0
		P := "319731973197319731973" // Constante Conforme Manual Sicoob
		While L > 0
			D := D + (Val(SubStr(cData, L, 1)) * Val(SubStr(P, L, 1)))
			L := L - 1
		End
		D  := Mod(D,11)
		If D == 0 .Or. D == 1
			D := 0
		Else
			D := 11 - D
		Endif
		D := AllTrim(Str(D))

	ElseIf cBanc == "748" //SICREDI WALTER 02/02/2017
		L := Len(cdata)
		D := 0
		If Len(cdata) == 24
			P := "987654329876543298765432" // Constante Conforme Manual Sicredi
			While L > 0
				D := D + (Val(SubStr(cData, L, 1)) * Val(SubStr(P, L, 1)))
				L := L - 1
			End
			D  := Mod(D,11)
			If D == 0 .Or. D == 1
				D := 0
			Else
				D := 11 - D
			Endif
			D := AllTrim(Str(D))
		ElseIf Len(cdata) == 19
			P := "4329876543298765432"
			While L > 0
				D := D + (Val(SubStr(cData, L, 1)) * Val(SubStr(P, L, 1)))
				L := L - 1
			End
			D  := Mod(D,11)
			D := 11 - D
			If D == 10 .Or. D == 11
				D := 0
			EndIf
			D := AllTrim(Str(D))
		EndIf

	ElseIf cBanc == "033" // SANTANDER
		L := Len(cdata)
		D := 0
		P := 1
		While L > 0
			P := P + 1
			D := D + (Val(SubStr(cData, L, 1)) * P)
			If P = 9
				P := 1
			End
			L := L - 1
		End
		R := (mod(D,11))
		Do Case
			Case R == 10
				D := 1
			Case R == 0
				D := 0
			Case R == 1
				D := 0
			OtherWise
				D := (11 - R )
		EndCase
		D := AllTrim(Str(D))

	ElseIf cBanc == "041"  // BANRISUL
		nCnt	:= 0
		cDigito := 0
		nSoma	:= 0
		nBase	:= 0
		aPeso	:= {4,3,2,7,6,5,4,3,2}

		nBase := Len(aPeso)+1

		FOR nCnt := Len(cData) TO 1 STEP -1
			nBase := IF(--nBase = 0,Len(aPeso),nBase)
			nSoma += Val(SUBS(cData,nCnt,01)) * aPeso[nBase]
		NEXT

		If nSoma < 11
			cDigito := nSoma
		Else
			cDigito := 11 - (nSoma % 11)  // cDigito = RESTO
		EndIf

		DO CASE
			CASE cDigito = 1 .OR. cDigito >= 10
				cNC01   := Substr(cData, Len(cData-1), 1)
				cNC01   := IIF( Val(cNC01)+1 >= 10, '0',  Str( Val(cNC01)+1, 1, 0 ) )
				cDigito := Modulo11( cData, cNC01 )    // deve processar novamente, acrescentando +1 no 1Â° NC
			OTHERWISE
				cDigito := STR( cDigito, 1, 0 )
		ENDCASE

		D := AllTrim(cDigito)

	ElseIf cBanc == "085" //CECRED  THIAGO - TSC959

		nSoma1	:= val(subs(cData,1,1))	*	4
		nSoma2	:= val(subs(cData,2,1))	*	3
		nSoma3	:= val(subs(cData,3,1))	*	2
		nSoma4	:= val(subs(cData,4,1))	*	9
		nSoma5	:= val(subs(cData,5,1))	*	8
		nSoma6	:= val(subs(cData,6,1))	*	7
		nSoma7	:= val(subs(cData,7,1))	*	6
		nSoma8	:= val(subs(cData,8,1))	*	5
		nSoma9	:= val(subs(cData,9,1))	*	4
		nSoma10	:= val(subs(cData,10,1))*	3
		nSoma11	:= val(subs(cData,11,1))*	2
		nSoma12	:= val(subs(cData,12,1))*	9
		nSoma13	:= val(subs(cData,13,1))*	8
		nSoma14	:= val(subs(cData,14,1))*	7
		nSoma15	:= val(subs(cData,15,1))*	6
		nSoma16	:= val(subs(cData,16,1))*	5
		nSoma17	:= val(subs(cData,17,1))*	4
		nSoma18	:= val(subs(cData,18,1))*	3
		nSoma19	:= val(subs(cData,19,1))*	2
		nSoma20	:= val(subs(cData,20,1))*	9
		nSoma21	:= val(subs(cData,21,1))*	8
		nSoma22	:= val(subs(cData,22,1))*	7
		nSoma23	:= val(subs(cData,23,1))*	6
		nSoma24	:= val(subs(cData,24,1))*	5
		nSoma25	:= val(subs(cData,25,1))*	4
		nSoma26	:= val(subs(cData,26,1))*	3
		nSoma27	:= val(subs(cData,27,1))*	2
		nSoma28	:= val(subs(cData,28,1))*	9
		nSoma29	:= val(subs(cData,29,1))*	8
		nSoma30	:= val(subs(cData,30,1))*	7
		nSoma31	:= val(subs(cData,31,1))*	6
		nSoma32	:= val(subs(cData,32,1))*	5
		nSoma33	:= val(subs(cData,33,1))*	4
		nSoma34	:= val(subs(cData,34,1))*	3
		nSoma35	:= val(subs(cData,35,1))*	2
		nSoma36	:= val(subs(cData,36,1))*	9
		nSoma37	:= val(subs(cData,37,1))*	8
		nSoma38	:= val(subs(cData,38,1))*	7
		nSoma39	:= val(subs(cData,39,1))*	6
		nSoma40	:= val(subs(cData,40,1))*	5
		nSoma41	:= val(subs(cData,41,1))*	4
		nSoma42	:= val(subs(cData,42,1))*	3
		nSoma43	:= val(subs(cData,43,1))*	2

		cDigito := mod(nSoma1+nSoma2+nSoma3+nSoma4+nSoma5+nSoma6+nSoma7+nSoma8+nSoma9+nSoma10+nSoma11+nSoma12+nSoma13+nSoma14+nSoma15+nSoma16+nSoma17+nSoma18+nSoma19+nSoma20+nSoma21+nSoma22+nSoma23+nSoma24+nSoma25+nSoma26+nSoma27+nSoma28+nSoma29+nSoma30+nSoma31+nSoma32+nSoma33+nSoma34+nSoma35+nSoma36+nSoma37+nSoma38+nSoma39+nSoma40+nSoma41+nSoma42+nSoma43,11)

		if cDigito <= 1 .OR.  cDigito >= 10
			D:= 1
		ELSE
			D:= 11 - cDigito
		ENDIF

		D := AllTrim(Str(D))

	ElseIf cBanc == "091" //UNICRED  WALTER 04/01/2019
		L := Len(cdata)
		D := 0
		//    1234567890
		//    1920000003
		P := "3298765432" // Constante Conforme Manual Sicoob
		While L > 0
			D := D + (Val(SubStr(cData, L, 1)) * Val(SubStr(P, L, 1)))
			L := L - 1
		End
		D  := Mod(D,11)
		D  := 11 - D
		D := AllTrim(Str(D))

	Else
		L := Len(cdata)
		D := 0
		P := 1
		While L > 0
			P := P + 1
			D := D + (Val(SubStr(cData, L, 1)) * P)
			If P = 9
				P := 1
			End
			L := L - 1
		End
		D := 11 - (mod(D,11))
		If cBanc == "SANTANDER" //.Or. cBanc == "CAIXA"
			IF (D == 0 .Or. D == 1 .Or. D == 10 .Or. D == 11)
				D := 1
			End
		Else
			If (D == 10 .Or. D == 11)
				D := 1
			End
		Endif
		D := AllTrim(Str(D))
	Endif

Return(D)


//------------------------------------------------------------------------------------
//Retorna os strings para inpressao do Boleto
//CB = String para o cod.barras, RN = String com o numero digitavel
//Cobranca nao identificada, numero do boleto = Titulo + Parcela
//------------------------------------------------------------------------------------
Static Function Ret_cBarra(cBanco,cAgencia,cConta,cDacCC,cCarteira,cNroDoc,nValor,dvencimento,cConvenio,cSequencial,cCarBank)

	Local cCodEmp 		:= IIf(SubStr(cBanco,1,3)=="399",AllTrim(cConvenio),StrZero(Val(SubStr(cConvenio,1,7)),7))
	Local cNumSeq 		:= Strzero(val(cSequencial),nTam_NN)
	Local bldocnufinal 	:= Strzero(val(cNroDoc),9)
	Local blvalorfinal 	:= Strzero(Round(nValor,2)*100,10) //strzero(int(nValor*100),10)
	Local cNNumSDig 	:= cCpoLivre := cCBSemDig := cCodBarra := cNNum := cFatVenc := ''
	Local cDvn          := " "

	//Fator Vencimento - POSICAO DE 06 A 09
	cFatVenc := STRZERO(dvencimento - CtoD("07/10/1997"),4)

	//Prefixo Nosso Numero
	//Nosso Numero
	cNNum := cNumSeq

	//Campo Livre (Definir campo livre com cada banco)
	If Substr(cBanco,1,3) == "001" //BB
		cCodEmp := Str(Val(cCodEmp))
		If Len(AllTrim(cCodEmp)) == 7  // CONVENIO 7 POSICOES
			cCpoLivre := AllTrim(StrZero(0,6)) + AllTrim(cCodEmp) + cNumSeq + PadR(cCarBank,2) //cCarBank -> Carteira
			//               000000 2838749 0000000007 17    0000002838749000000000717
		Else // CONVENIO 6 POSICOES
			cCpoLivre := AllTrim(cCodEmp) + cNumSeq + SubStr(SEE->EE_AGENCIA,1,4) + StrZero(Val(SEE->EE_CONTA),8) + AllTrim(cCarBank)
			//           148393 00007 3711 00004793 17   1483930000737110000479317
		EndIf
		//cDvn := cValToChar(Modulo10(AllTrim(cAgencia)+AllTrim(cConta)+cCarBank+cNumSeq))
		cDvn := cValToChar(Modulo11((AllTrim(cConvenio)+cNumSeq),SubStr(cBanco,1,3),cCarteira) )
		//6 + 7 + 10 + 2 = 25

	ElseIf Substr(cBanco,1,3) == "399" // HSBC
		_NumHSBC := cNumSeq //AllTrim(cCodEmp) + cNumSeq
		cDvn := Modulo11(_NumHSBC,SubStr(cBanco,1,3))
		cCpoLivre := _NumHSBC + cDvn + SubStr(aDadosBanco[3],1,4) + aDadosBanco[4] + aDadosBanco[5] + cCarteira + "1"
		// 			2169300009  1	   AGENCIA                      CONTA            DIG.CONTA

	ElseIf SubStr(cBanco,1,3) == "756" // SICOOB
		_NumSICOOB := AllTrim(cAgencia) + StrZero(Val(AllTrim(cCodEmp)),10) + AllTrim(cNumSeq) // WALTER 08/09/2016
		//cDvn := modulo11(cNumSeq,SubStr(cBanco,1,3),cCarteira) //LAIANA

		_Parc     := IIF(Empty((caliasSE1)->E1_PARCELA),"001",STRZERO(VAL((caliasSE1)->E1_PARCELA),3)) // WALTER 11/04/2018

		cDvn      := modulo11(_NumSICOOB,SubStr(cBanco,1,3)) // WALTER 08/09/2016
		cCpoLivre := cCarteira + AllTrim(cAgencia) + ALLTRIM(SEE->EE_CODCART) + StrZero(Val(AllTrim(cCodEmp)),7) + AllTrim(cNumSeq) + cDvn + _Parc  //LAIANA
		//1 3084 01 0222372

	ElseIf SubStr(cBanco,1,3) == "748" // SICREDI
		_NumSICREDI := AllTrim(cAgencia) + AllTrim(cA6_POS) + AllTrim(cConvenio) + AllTrim(cNumSeq)
		cDvn        := cValToChar(Modulo11(_NumSICREDI,SubStr(cBanco,1,3)))
		cCpoLivreP  := "1" + "1" + AllTrim(cNumSeq) + cDvn + AllTrim(cAgencia) + AllTrim(cA6_POS) + AllTrim(cConvenio) + "1" + "0"
		cDvC        := cValToChar(modulo11(cCpoLivreP,SubStr(cBanco,1,3)))
		cCpoLivre   := cCpoLivreP + cDvC
		//17200001/1
		//cCarteira + AllTrim(cAgencia) + ALLTRIM(SEE->EE_CODCART) + StrZero(Val(AllTrim(cCodEmp)),7) + AllTrim(cNumSeq) + cDvn + STRZERO(VAL((caliasSE1)->E1_PARCELA),3)  //LAIANA

	ElseIf Substr(cBanco,1,3) == "237" //BRADESCO
		cDvn := modulo11(cNumSeq,SubStr(cBanco,1,3),cCarteira)
		cCpoLivre := StrZero(Val(cAgencia),4) + cCarteira + cNumSeq + StrZero(Val(cConta),7) + "0"
		//4 + 2 + 11 + 8 = 25
	ElseIf SubStr(cBanco,1,3) $ "341/655" //ITAU ou VOTORANTIM
		//cDvn := cValToChar(Modulo10(AllTrim(cAgencia)+AllTrim(cConta)+cCarBank+cNumSeq)) // COMENTADO WALTER 30/11/16
		_NumItau := AllTrim(cAgencia)+AllTrim(cConta)+ALLTRIM(SEE->EE_CARTEIR)+AllTrim(cNumSeq)
		cDvn      := cValToChar(Modulo11(_NumItau,SubStr(cBanco,1,3),ALLTRIM(SEE->EE_CARTEIR)))
		//cCpoLivre := ALLTRIM(SEE->EE_CARTEIR) + _NumItau + cDvn + AllTrim(cAgencia) + AllTrim(cConta) + aDadosBanco[5] + "000"
		cDvC := cValToChar(Modulo10(AllTrim(cAgencia)+AllTrim(cConta)))
		cCpoLivre := Alltrim(cCarBank) + cNumSeq + cDvn + strzero(val(cAgencia),4)+AllTrim(cConta)+cDvC+"000"
		//2 + 8 + 1 + 4 + 10 = 25
	ElseIf SubStr(cBanco,1,3) == "422" //SAFRA
		cDvn := modulo11(cNumSeq,SubStr(cBanco,1,3))
		//cCpoLivre := "7" + PadL( Strzero(Val(cAgencia),5)+ PadL(AllTrim(cConta)+cDacCC,9,"0") , 14 ) + cNumSeq + cDvn + "2"
		cCpoLivre := "7" + AllTrim(SEE->EE_AGENCIA)+SEE->EE_DVAGE + PadL(AllTrim(cConta)+cDacCC,9,"0") + cNumSeq + cDvn + "2"
		cCpoLivre := StrTran(cCpoLivre," ","0")
		//1 + 14 + 8 + 2 = 25
	ElseIf SubStr(cBanco,1,3) == "033" //SANTANDER
		_NumSant := "00000"+AllTrim(cNumSeq)
		cDvn := modulo11("0000"+_NumSant,SubStr(cBanco,1,3))
		cCpoLivre := "9" + ALLTRIM(cCodEmp) + _NumSant + cDvn + "0" + cCarBank
		//1 + 7 + 12 + 1 + 1 + 3 = 25
	ElseIf SubStr(cBanco,1,3) == "104" //CAIXA E.F.
		/*
		CONFIGURACAO ANTERIOR
		10 - Nosso Numero sem digito verificador (nosso numero deve comecar sempre com 9 no cad. parametro do banco)
		04 - Agencia
		04 - Operacao
		07 - Codigo Beneficiario
		Total 25

		cCpoLivre := cNumSeq + Strzero(Val(cAgencia),4) + "8700" + cCodEmp
		//MsgInfo(cCpoLivre)
		cDvn := modulo11(cNumSeq,SubStr(cBanco,1,3))
		// FIM CONFIGURACAO ANTERIOR
		*/

		// Configuraï¿½ï¿½o de Acordo com o Manual do Banco
		// WALTER TSC022 13/07/2016

		_NumCEF   := IIf(AllTrim(cCarteira)=="RG","1"," ") + "4" + StrZero(Val(cNumSeq),15) // nosso nï¿½mero
		cDvn      := Modulo11(_NumCEF,SubStr(cBanco,1,3))  // dv do nosso nï¿½mero

		_NumCEF1  := AllTrim(cCodEmp) + substr(_NumCEF,3,3) + substr(_NumCEF,1,1) + substr(_NumCEF,6,3) + substr(_NumCEF,2,1) + substr(_NumCEF,9,9) // campo livre do cod de barras
		cDvn1     := Modulo11(_NumCEF1,SubStr(cBanco,1,3)) //dv do campo livre
		cCpoLivre := _NumCEF1 + cDvn1

	ElseIf SubStr(cBanco,1,3) == "041" //BANRISUL
		/*
		Posicao 20 a 20 Produto:
		"1" Cobranca Normal, Fichario emitido pelo BANRISUL
		"2" Cobranca Direta, Fichario emitido pelo CLIENTE.
		Posicao 21 a 21 Constante "1"
		Posicao 22 a 24 Agencia Beneficiario (tres ultimos digitos) sem Numero de Controle.
		Ex.: Se o cod da Agencia for â€˜0015â€™ suprimindo o zero a esquerda fica â€˜015â€™.
		Posicao 25 a 31	Codigo do Beneficiario sem Numero de Controle.
		Posicao 32 a 39	Nosso Numero sem Numero de Controle.
		Posicao 40 a 42	Constante "041".
		Posicao 43 a 44	Duplo Digito referente Ã s posicoes 20 a 42 (modulos 10 e 11).
		*/
		//            20  21  22                    25                    32       40     43       44
		cCpoLivre := "2"+"1"+StrZero(Val(cAgencia),4)+StrZero(Val(cConta),7)+cNumSeq+"40"
		aDv041 := sfMod041(cCpoLivre)
		cCpoLivre += aDv041[1]+aDv041[2]
		cDvn :=	aDv041[1]+aDv041[2]

	ElseIf SubStr(cBanco,1,3) == "085" //CECRED
		cCpoLivre := alltrim(cConvenio)+SubStr(aDadosBanco[4],1,7) + SubStr(aDadosBanco[5],1,1) +STRZERO(VAL(cNosso_Num),9,0)+SubStr(aDadosBanco[6],1,2)

	ElseIf SubStr(cBanco,1,3) == "091" //UNICRED
		cDvn      := Modulo11(AllTrim(cNosso_Num),SubStr(cBanco,1,3))
		//cCpoLivre := ALLTRIM(cCodEmp)+AllTrim(cNosso_Num)+cDvn
		cCpoLivre := AllTrim(cAgencia)+StrZero(Val(SEE->EE_CODEMP),10)+AllTrim(cNosso_Num)+cDvn

	Else
		cCpoLivre := ""
	Endif

	//Dados para Calcular o Dig Verificador Geral
	cCBSemDig := cBanco + cFatVenc + blvalorfinal + cCpoLivre

	//Codigo de Barras Completo
	if SubStr(cBanco,1,3) == "085"
		cCodBarra := cBanco +  Modulo11(cCBSemDig,'085') + cFatVenc + blvalorfinal + cCpoLivre
	Else
		cCodBarra := cBanco +  Modulo11(cCBSemDig, If(SANTANDER .OR. CAIXAEF,"SANTANDER/CAIXA","SEM_BANCO")) + cFatVenc + blvalorfinal + cCpoLivre
	Endif

	//Dados para Calcular o Dig Verificador Geral
	//cCBSemDig := cBanco + cFatVenc + blvalorfinal + cCpoLivre  //WALTER 24/04/2017

	//Codigo de Barras Completo
	//cCodBarra := cBanco +  Modulo11(cCBSemDig, If(SANTANDER .OR. CAIXAEF,"SANTANDER/CAIXA","SEM_BANCO")) + cFatVenc + blvalorfinal + cCpoLivre
	//cCodBarra := cBanco +  Modulo11(cCBSemDig, If(SANTANDER,"SANTANDER","SEM_BANCO")) + cFatVenc + blvalorfinal + cCpoLivre  //WALTER 24/04/2017
	//

	//4 + 1 + 4 + 10 + 6 + 7 + 10 + 2
	//MsgInfo(cCodBarra)
	//Digito Verificador do Primeiro Campo
	cPrCpo := cBanco + SubStr(cCodBarra,20,5)
	cDvPrCpo := AllTrim(Str(Modulo10(cPrCpo)))

	//Digito Verificador do Segundo Campo
	cSgCpo := SubStr(cCodBarra,25,10)
	cDvSgCpo := AllTrim(Str(Modulo10(cSgCpo)))

	//Digito Verificador do Terceiro Campo
	cTrCpo := SubStr(cCodBarra,35,10)
	cDvTrCpo := AllTrim(Str(Modulo10(cTrCpo)))

	//Digito Verificador Geral
	cDvGeral := SubStr(cCodBarra,5,1)

	//Linha Digitavel
	cLindig := SubStr(cPrCpo,1,5) + "." + SubStr(cPrCpo,6,4) + cDvPrCpo + " "   //primeiro campo
	cLinDig += SubStr(cSgCpo,1,5) + "." + SubStr(cSgCpo,6,5) + cDvSgCpo + " "   //segundo campo
	cLinDig += SubStr(cTrCpo,1,5) + "." + SubStr(cTrCpo,6,5) + cDvTrCpo + " "   //terceiro campo
	cLinDig += " " + cDvGeral              //dig verificador geral
	cLinDig += "  " + SubStr(cCodBarra,6,4)+SubStr(cCodBarra,10,10)  // fator de vencimento e valor nominal do titulo

Return({cCodBarra,cLinDig,cNNum+PadR(cDvn,1)})


//-------------------------------------------------------------------
/*/{Protheus.doc} EnvEmail
EnvEmail  Autor  Denis
@author  author
date: "13/03/15"
/*/
//-------------------------------------------------------------------
Static Function EnvEmail()
	Local cEmail   := ""
	Local cEmailCp := ""
	Local ny
	Conout("qtde de boletos aglutinados:"+strzero(len(aAglutinaBol),6))
	for nX := 1 to len(aAglutinaBol)
		cEmail   := ""
		cEmailCp := ""

		If SA1->(DbSeek(xFilial("SA1") + aAglutinaBol[nX][1] ))
			cEmail := SA1->A1_EMAIL
		EndIf

		If Empty(cEmail)
			Return
		EndIf

		cFrom := SUPERGETMV("MV_RELFROM",.F.,"")

		cTo := cEmail
		cCC := cEmailCp
		cSubject := "Informe de emissao de Boleto"
		cAttach := ""

		//ANEXA TITULOS AGLUTINADOS NO ARRAY
		for nY := 1 to len(aAglutinaBol[nX][2])
			cAttach += "\boleto\"+AllTrim( aAglutinaBol[nX][2][nY] )+".PDF" + "; "
			Conout("Boleto: "+AllTrim( aAglutinaBol[nX][2][nY] ))
		next nY

		cMsg := retHTML()
		U_Brienv(cFrom, cTo, cCC, cSubject, cMsg, cAttach,.T.)

		//deleta do diretorio
		for nZ := 1 to len(aAglutinaBol[nX][2])
			FERASE("\boleto\"+AllTrim( aAglutinaBol[nX][2][nZ] )+".PDF")
			FERASE("\boleto\"+AllTrim( aAglutinaBol[nX][2][nZ] )+".REL")
		next nZ

	next nX

return

Static Function ValidPerg()

	PutSx1(cPerg,"01","Do Prefixo:"				,"","","mv_ch1" ,"C",03,0,0,"G","",""		,"","","mv_par01",""  				,"","","",""   			,"","","","","","","","","","","")
	PutSx1(cPerg,"02","Ate o Prefixo:"			,"","","mv_ch2" ,"C",03,0,0,"G","",""		,"","","mv_par02",""  				,"","","",""   			,"","","","","","","","","","","")
	PutSx1(cPerg,"03","Do Titulo:"				,"","","mv_ch3" ,"C",09,0,0,"G","",""		,"","","mv_par03",""				,"","","",""   			,"","","","","","","","","","","")
	PutSx1(cPerg,"04","Ate o Titulo:"			,"","","mv_ch4" ,"C",09,0,0,"G","",""		,"","","mv_par04",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"05","Da Parcela:"				,"","","mv_ch5" ,"C",02,0,0,"G","",""		,"","","mv_par05",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"06","Ate a Parcela:"			,"","","mv_ch6" ,"C",02,0,0,"G","",""		,"","","mv_par06",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"07","Do Banco:"				,"","","mv_ch7" ,"C",03,0,0,"G","","SA6"	,"","","mv_par07",""   				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"08","Agencia:"				,"","","mv_ch8" ,"C",05,0,0,"G","",""		,"","","mv_par08",""   				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"09","Conta:"					,"","","mv_ch9" ,"C",10,0,0,"G","",""		,"","","mv_par09",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"10","SubConta:" 				,"","","mv_ch10","C",03,0,0,"G","",""		,"","","mv_par10",""  				,"","","","" 			,"","","","","","","","","","","")
	PutSx1(cPerg,"11","Do Cliente:"				,"","","mv_ch11","C",06,0,0,"G","","SA1"	,"","","mv_par11",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"12","Ate o Cliente:"			,"","","mv_ch12","C",06,0,0,"G","","SA1"	,"","","mv_par12",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"13","Da Loja:"				,"","","mv_ch13","C",02,0,0,"G","",""		,"","","mv_par13",""   				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"14","Ate a Loja:"				,"","","mv_ch14","C",02,0,0,"G","",""		,"","","mv_par14",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"15","Da Dt. Venc.:"			,"","","mv_ch15","D",08,0,0,"G","",""		,"","","mv_par15",""  				,"","","",""  			,"","","","","","","","","","","")
	PutSx1(cPerg,"16","Ate a Dt. Venc:"			,"","","mv_ch16","D",08,0,0,"G","",""		,"","","mv_par16",""  				,"","","",""   			,"","","","","","","","","","","")
	PutSx1(cPerg,"17","Da Dt. Emissao:"			,"","","mv_ch17","D",08,0,0,"G","",""		,"","","mv_par17",""   				,"","","",""   			,"","","","","","","","","","","")
	PutSx1(cPerg,"18","Ate a Dt. Emis:"			,"","","mv_ch18","D",08,0,0,"G","",""		,"","","mv_par18",""   				,"","","",""   			,"","","","","","","","","","","")
	PutSx1(cPerg,"19","Do bordero:"				,"","","mv_ch19","C",06,0,0,"G","",""		,"","","mv_par19",""				,"","","",""   			,"","","","","","","","","","","")
	PutSx1(cPerg,"20","Ate o Bordero:"			,"","","mv_ch20","C",06,0,0,"G","",""		,"","","mv_par20",""				,"","","",""			,"","","","","","","","","","","")
	PutSx1(cPerg,"21","Selecionar titulos:"		,"","","mv_ch21","N",01,0,0,"C","",""		,"","","mv_par21","Sim"				,"","","","Nao"			,"","","","","","","","","","","")
	PutSx1(cPerg,"22","Gerar Bordero:"			,"","","mv_ch22","N",01,0,0,"C","",""		,"","","mv_par22","Sim"				,"","","","Nao"			,"","","","","","","","","","","")
Return

Static Function VerParam(mensagem)
	Alert(mensagem)
	U_BOLETOACTVS()
Return

//Busca um bordero com a data atual que nao tenha sido transferido
Static Function BuscaBorde()

	Local cRet	:= ""
	Local cQuery:= ""
	Local Temp
	Local cIniBord := "A00001"

	cQuery += "Select EA_NUMBOR From "	+ RetSqlName("SEA")	+ " As SEA "
	cQuery += "Where SEA.EA_AGEDEP = '"	+ _MV_PAR08 		+ "' "
	cQuery += "And SEA.EA_NUMCON = '" 	+ _MV_PAR09 		+ "' "
	cQuery += "And SEA.EA_PORTADO = '" 	+ _MV_PAR07 		+ "' "
	cQuery += "And SEA.EA_SUBCTA = '" 	+ _MV_PAR10 		+ "' "
	cQuery += "And SEA.EA_FILIAL = '" 	+ xFilial("SEA") 	+ "' "
	cQuery += "And SEA.EA_DATABOR = '" 	+ dToS(dDataBase) 	+ "' "
	cQuery += "And SEA.EA_TRANSF = '' "
	cQuery += "And SEA.EA_CART = 'R' "
	cQuery += "And SEA.EA_NUMBOR <> '' "
	cQuery += "And SEA.D_E_L_E_T_ = '' "

	TCQUERY cQuery NEW ALIAS (Temp:=GetNextAlias())

	While (Temp)->(!EoF())
		cRet := (Temp)->EA_NUMBOR
		(Temp)->(DbSkip())
	EndDo

	(Temp)->(DbCloseArea())

Return cRet



/*--------------------------------------------------------------------------*/
Static Function sfMod041(cNumSeq)
	/*--------------------------------------------------------------------------*/
	Local cNc01 := "", cNc02 := ""

	cNc01 := Str( Modulo10(cNumSeq), 1, 0 )
	cNc02 := Modulo11(cNumSeq,cNc01)

Return ({cNc01,cNc02})

//----------------------------------------------------------------------------
Static Function o_Say(xPar1,xPar2,xPar3,xPar4,xPar5)
	oPrint:Say( nAddSay+(xPar1*nFatorV) , xPar2*nFatorH , xPar3, xPar4, xPar5 )
Return

Static Function o_Line(xPar1,xPar2,xPar3,xPar4)
	oPrint:Line( nAddLin+(xPar1*nFatorV) , xPar2*nFatorH , nAddLin+(xPar3*nFatorV) , xPar4*nFatorH )
Return

Static Function o_SayBitMap(xPar1,xPar2,xPar3,xPar4,xPar5)
	oPrint:SayBitMap( 40+(xPar1*nFatorV) , xPar2*nFatorH , xPar3 , xPar4 , xPar5 )
Return



Static Function retHTML()

	Local nSomaDias := 3

	cHTML :=' <!doctype html>                                                                                                  '
	cHTML +=' <html>                                                                                                           '
	cHTML +='   <head>                                                                                                         '
	cHTML +='     <meta name="viewport" content="width=device-width" />                                                        '
	cHTML +='     <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />                                        '
	cHTML +='     <title>Pedido de Venda</title>                                                                               '
	cHTML +='     <style>                                                                                                      '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           GLOBAL RESETS                                                                                          '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       img {                                                                                                      '
	cHTML +='         border: none;                                                                                            '
	cHTML +='         -ms-interpolation-mode: bicubic;                                                                         '
	cHTML +='         max-width: 100%; }                                                                                       '
	cHTML +='       body {                                                                                                     '
	cHTML +='         background-color: #f6f6f6;                                                                               '
	cHTML +='         font-family: sans-serif;                                                                                 '
	cHTML +='         -webkit-font-smoothing: antialiased;                                                                     '
	cHTML +='         font-size: 14px;                                                                                         '
	cHTML +='         line-height: 1.4;                                                                                        '
	cHTML +='         margin: 0;                                                                                               '
	cHTML +='         padding: 0;                                                                                              '
	cHTML +='         -ms-text-size-adjust: 100%;                                                                              '
	cHTML +='         -webkit-text-size-adjust: 100%; }                                                                        '
	cHTML +='       table {                                                                                                    '
	cHTML +='         border-collapse: separate;                                                                               '
	cHTML +='         mso-table-lspace: 0pt;                                                                                   '
	cHTML +='         mso-table-rspace: 0pt;                                                                                   '
	cHTML +='         width: 100%; }                                                                                           '
	cHTML +='         table td {                                                                                               '
	cHTML +='           font-family: sans-serif;                                                                               '
	cHTML +='           font-size: 14px;                                                                                       '
	cHTML +='           vertical-align: top; }                                                                                 '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           BODY & CONTAINER                                                                                       '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       .body {                                                                                                    '
	cHTML +='         background-color: #f6f6f6;                                                                               '
	cHTML +='         width: 100%; }                                                                                           '
	cHTML +='       /* Set a max-width, and make it display as block so it will automatically stretch  */                      '
	cHTML +='       .container {                                                                                               '
	cHTML +='         display: block;                                                                                          '
	cHTML +='         Margin: 0 auto !important;                                                                               '
	cHTML +='         /* makes it centered */                                                                                  '
	cHTML +='         max-width: 580px;                                                                                        '
	cHTML +='         padding: 10px;                                                                                           '
	cHTML +='         width: 580px; }                                                                                          '
	cHTML +='       /* This should also be a block element, so that it will fill 100% of the .container */                     '
	cHTML +='       .content {                                                                                                 '
	cHTML +='         box-sizing: border-box;                                                                                  '
	cHTML +='         display: block;                                                                                          '
	cHTML +='         Margin: 0 auto;                                                                                          '
	cHTML +='         max-width: 580px;                                                                                        '
	cHTML +='         padding: 10px; }                                                                                         '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           HEADER, FOOTER, MAIN                                                                                   '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       .main {                                                                                                    '
	cHTML +='         background: #ffffff;                                                                                     '
	cHTML +='         border-radius: 3px;                                                                                      '
	cHTML +='         width: 100%; }                                                                                           '
	cHTML +='       .wrapper {                                                                                                 '
	cHTML +='         box-sizing: border-box;                                                                                  '
	cHTML +='         padding: 20px; }                                                                                         '
	cHTML +='       .content-block {                                                                                           '
	cHTML +='         padding-bottom: 10px;                                                                                    '
	cHTML +='         padding-top: 10px;                                                                                       '
	cHTML +='       }                                                                                                          '
	cHTML +='       .footer {                                                                                                  '
	cHTML +='         clear: both;                                                                                             '
	cHTML +='         Margin-top: 10px;                                                                                        '
	cHTML +='         text-align: center;                                                                                      '
	cHTML +='         width: 100%; }                                                                                           '
	cHTML +='         .footer td,                                                                                              '
	cHTML +='         .footer p,                                                                                               '
	cHTML +='         .footer span,                                                                                            '
	cHTML +='         .footer a {                                                                                              '
	cHTML +='           color: #999999;                                                                                        '
	cHTML +='           font-size: 12px;                                                                                       '
	cHTML +='           text-align: center; }                                                                                  '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           TYPOGRAPHY                                                                                             '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       h1,                                                                                                        '
	cHTML +='       h2,                                                                                                        '
	cHTML +='       h3,                                                                                                        '
	cHTML +='       h4 {                                                                                                       '
	cHTML +='         color: #000000;                                                                                          '
	cHTML +='         font-family: sans-serif;                                                                                 '
	cHTML +='         font-weight: 400;                                                                                        '
	cHTML +='         line-height: 1.4;                                                                                        '
	cHTML +='         margin: 0;                                                                                               '
	cHTML +='         Margin-bottom: 30px; }                                                                                   '
	cHTML +='       h1 {                                                                                                       '
	cHTML +='         font-size: 35px;                                                                                         '
	cHTML +='         font-weight: 300;                                                                                        '
	cHTML +='         text-align: center;                                                                                      '
	cHTML +='         text-transform: capitalize; }                                                                            '
	cHTML +='       p,                                                                                                         '
	cHTML +='       ul,                                                                                                        '
	cHTML +='       ol {                                                                                                       '
	cHTML +='         font-family: sans-serif;                                                                                 '
	cHTML +='         font-size: 14px;                                                                                         '
	cHTML +='         font-weight: normal;                                                                                     '
	cHTML +='         margin: 0;                                                                                               '
	cHTML +='         Margin-bottom: 15px; }                                                                                   '
	cHTML +='         p li,                                                                                                    '
	cHTML +='         ul li,                                                                                                   '
	cHTML +='         ol li {                                                                                                  '
	cHTML +='           list-style-position: inside;                                                                           '
	cHTML +='           margin-left: 5px; }                                                                                    '
	cHTML +='       a {                                                                                                        '
	cHTML +='         color: #3498db;                                                                                          '
	cHTML +='         text-decoration: underline; }                                                                            '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           BUTTONS                                                                                                '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       .btn {                                                                                                     '
	cHTML +='         box-sizing: border-box;                                                                                  '
	cHTML +='         width: 100%; }                                                                                           '
	cHTML +='         .btn > tbody > tr > td {                                                                                 '
	cHTML +='           padding-bottom: 15px; }                                                                                '
	cHTML +='         .btn table {                                                                                             '
	cHTML +='           width: auto; }                                                                                         '
	cHTML +='         .btn table td {                                                                                          '
	cHTML +='           background-color: #ffffff;                                                                             '
	cHTML +='           border-radius: 5px;                                                                                    '
	cHTML +='           text-align: center; }                                                                                  '
	cHTML +='         .btn a {                                                                                                 '
	cHTML +='           background-color: #ffffff;                                                                             '
	cHTML +='           border: solid 1px #3498db;                                                                             '
	cHTML +='           border-radius: 5px;                                                                                    '
	cHTML +='           box-sizing: border-box;                                                                                '
	cHTML +='           color: #3498db;                                                                                        '
	cHTML +='           cursor: pointer;                                                                                       '
	cHTML +='           display: inline-block;                                                                                 '
	cHTML +='           font-size: 14px;                                                                                       '
	cHTML +='           font-weight: bold;                                                                                     '
	cHTML +='           margin: 0;                                                                                             '
	cHTML +='           padding: 12px 25px;                                                                                    '
	cHTML +='           text-decoration: none;                                                                                 '
	cHTML +='           text-transform: capitalize; }                                                                          '
	cHTML +='       .btn-primary table td {                                                                                    '
	cHTML +='         background-color: #3498db; }                                                                             '
	cHTML +='       .btn-primary a {                                                                                           '
	cHTML +='         background-color: #3498db;                                                                               '
	cHTML +='         border-color: #3498db;                                                                                   '
	cHTML +='         color: #ffffff; }                                                                                        '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           OTHER STYLES THAT MIGHT BE USEFUL                                                                      '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       .last {                                                                                                    '
	cHTML +='         margin-bottom: 0; }                                                                                      '
	cHTML +='       .first {                                                                                                   '
	cHTML +='         margin-top: 0; }                                                                                         '
	cHTML +='       .align-center {                                                                                            '
	cHTML +='         text-align: center; }                                                                                    '
	cHTML +='       .align-right {                                                                                             '
	cHTML +='         text-align: right; }                                                                                     '
	cHTML +='       .align-left {                                                                                              '
	cHTML +='         text-align: left; }                                                                                      '
	cHTML +='       .clear {                                                                                                   '
	cHTML +='         clear: both; }                                                                                           '
	cHTML +='       .mt0 {                                                                                                     '
	cHTML +='         margin-top: 0; }                                                                                         '
	cHTML +='       .mb0 {                                                                                                     '
	cHTML +='         margin-bottom: 0; }                                                                                      '
	cHTML +='       .preheader {                                                                                               '
	cHTML +='         color: transparent;                                                                                      '
	cHTML +='         display: none;                                                                                           '
	cHTML +='         height: 0;                                                                                               '
	cHTML +='         max-height: 0;                                                                                           '
	cHTML +='         max-width: 0;                                                                                            '
	cHTML +='         opacity: 0;                                                                                              '
	cHTML +='         overflow: hidden;                                                                                        '
	cHTML +='         mso-hide: all;                                                                                           '
	cHTML +='         visibility: hidden;                                                                                      '
	cHTML +='         width: 0; }                                                                                              '
	cHTML +='       .powered-by a {                                                                                            '
	cHTML +='         text-decoration: none; }                                                                                 '
	cHTML +='       hr {                                                                                                       '
	cHTML +='         border: 0;                                                                                               '
	cHTML +='         border-bottom: 1px solid #f6f6f6;                                                                        '
	cHTML +='         Margin: 20px 0; }                                                                                        '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           RESPONSIVE AND MOBILE FRIENDLY STYLES                                                                  '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       @media only screen and (max-width: 620px) {                                                                '
	cHTML +='         table[class=body] h1 {                                                                                   '
	cHTML +='           font-size: 28px !important;                                                                            '
	cHTML +='           margin-bottom: 10px !important; }                                                                      '
	cHTML +='         table[class=body] p,                                                                                     '
	cHTML +='         table[class=body] ul,                                                                                    '
	cHTML +='         table[class=body] ol,                                                                                    '
	cHTML +='         table[class=body] td,                                                                                    '
	cHTML +='         table[class=body] span,                                                                                  '
	cHTML +='         table[class=body] a {                                                                                    '
	cHTML +='           font-size: 16px !important; }                                                                          '
	cHTML +='         table[class=body] .wrapper,                                                                              '
	cHTML +='         table[class=body] .article {                                                                             '
	cHTML +='           padding: 10px !important; }                                                                            '
	cHTML +='         table[class=body] .content {                                                                             '
	cHTML +='           padding: 0 !important; }                                                                               '
	cHTML +='         table[class=body] .container {                                                                           '
	cHTML +='           padding: 0 !important;                                                                                 '
	cHTML +='           width: 100% !important; }                                                                              '
	cHTML +='         table[class=body] .main {                                                                                '
	cHTML +='           border-left-width: 0 !important;                                                                       '
	cHTML +='           border-radius: 0 !important;                                                                           '
	cHTML +='           border-right-width: 0 !important; }                                                                    '
	cHTML +='         table[class=body] .btn table {                                                                           '
	cHTML +='           width: 100% !important; }                                                                              '
	cHTML +='         table[class=body] .btn a {                                                                               '
	cHTML +='           width: 100% !important; }                                                                              '
	cHTML +='         table[class=body] .img-responsive {                                                                      '
	cHTML +='           height: auto !important;                                                                               '
	cHTML +='           max-width: 100% !important;                                                                            '
	cHTML +='           width: auto !important; }}                                                                             '
	cHTML +='       /* -------------------------------------                                                                   '
	cHTML +='           PRESERVE THESE STYLES IN THE HEAD                                                                      '
	cHTML +='       ------------------------------------- */                                                                   '
	cHTML +='       @media all {                                                                                               '
	cHTML +='         .ExternalClass {                                                                                         '
	cHTML +='           width: 100%; }                                                                                         '
	cHTML +='         .ExternalClass,                                                                                          '
	cHTML +='         .ExternalClass p,                                                                                        '
	cHTML +='         .ExternalClass span,                                                                                     '
	cHTML +='         .ExternalClass font,                                                                                     '
	cHTML +='         .ExternalClass td,                                                                                       '
	cHTML +='         .ExternalClass div {                                                                                     '
	cHTML +='           line-height: 100%; }                                                                                   '
	cHTML +='         .apple-link a {                                                                                          '
	cHTML +='           color: inherit !important;                                                                             '
	cHTML +='           font-family: inherit !important;                                                                       '
	cHTML +='           font-size: inherit !important;                                                                         '
	cHTML +='           font-weight: inherit !important;                                                                       '
	cHTML +='           line-height: inherit !important;                                                                       '
	cHTML +='           text-decoration: none !important; }                                                                    '
	cHTML +='         .btn-primary table td:hover {                                                                            '
	cHTML +='           background-color: #34495e !important; }                                                                '
	cHTML +='         .btn-primary a:hover {                                                                                   '
	cHTML +='           background-color: #34495e !important;                                                                  '
	cHTML +='           border-color: #34495e !important; } }                                                                  '
	cHTML +='     </style>                                                                                                     '
	cHTML +='   </head>                                                                                                        '
	cHTML +='   <body class="">                                                                                                '
	cHTML +='     <table border="0" cellpadding="0" cellspacing="0" class="body">                                              '
	cHTML +='       <tr>                                                                                                       '
	cHTML +='         <td>&nbsp;</td>                                                                                          '
	cHTML +='         <td class="container">                                                                                   '
	cHTML +='           <div class="content">                                                                                  '
	cHTML +='                                                                                                                  '
	cHTML +='             <!-- START CENTERED WHITE CONTAINER -->                                                              '
	cHTML +='             <span class="preheader">This is preheader text. Some clients will show this text as a preview.</span>'
	cHTML +='             <table class="main">                                                                                 '
	cHTML +='                                                                                                                  '
	cHTML +='               <!-- START MAIN CONTENT AREA -->                                                                   '
	cHTML +='               <tr>                                                                                               '
	cHTML +='                 <td class="wrapper">                                                                             '
	cHTML +='                   <table border="0" cellpadding="0" cellspacing="0">                                             '
	cHTML +='                     <tr>                                                                                         '
	cHTML +='                       <td>                                                                                       '

	cHTML +='                         <p>Olá ' + Alltrim(SA1->A1_NOME) +  ',  </p>                                               '
	cHTML +='                         <br>                                                                                      '
	IF !lAutoExec
		cHTML +='                         <p>Segue em anexo boleto(s) emitido(s).</p>                                                   '
	ELSE
		//If Dow(Date()) = 2
		//	nSomaDias := 3
		//ElseIf Dow(Date()) = 3
		//	nSomaDias := 3
		//ElseIf Dow(Date()) = 4
		//	nSomaDias := 5
		//ElseIf Dow(Date()) = 5
		//	nSomaDias := 5
		//ElseIf Dow(Date()) = 6
		//	nSomaDias := 5
		//Endif

		cHTML +='                         <p>Segue em anexo boleto(s) que irao vencer a <STRONG>3 dias.</STRONG>  </p>                                                   '
		cHTML +='                         	  <p><STRONG>Data do Vencimento: '+ DTOC( date() + nSomaDias )+'</STRONG> </p>                                                   '
	ENDIF
	cHTML +='                         <br>                                                                                         '
	cHTML +='                         <p></p>                                                                                  '
	cHTML +='                       </td>                                                                                   '
	cHTML +='                     </tr>                                                                                        '
	cHTML +='                   </table>                                                                                       '
	cHTML +='                 </td>                                                                                            '
	cHTML +='               </tr>                                                                                              '
	cHTML +='                                                                                                                  '
	cHTML +='             <!-- END MAIN CONTENT AREA -->                                                                       '
	cHTML +='             </table>                                                                                             '
	cHTML +='                                                                                                                  '
	cHTML +='             <!-- START FOOTER -->                                                                                '
	cHTML +='             <div class="footer">                                                                                 '
	cHTML +='               <table border="0" cellpadding="0" cellspacing="0">                                                 '
	cHTML +='                 <tr>                                                                                             '
	cHTML +='                   <td class="content-block powered-by">                                                          '
	cHTML +='                     Gerado via Workflow Protheus - Envio de Boleto.                                                        '
	cHTML +='                   </td>                                                                                          '
	cHTML +='                 </tr>                                                                                            '
	cHTML +='                 <tr>                                                                                             '
	cHTML +='                   <td class="content-block powered-by">                                                          '
	cHTML +='                     '   +  SM0->M0_NOMECOM  + ' - ' +  cValToChar(YEAR(DATE()))   +  '                                                                   '
	cHTML +='                   </td>                                                                                          '
	cHTML +='                 </tr>                                                                                            '
	cHTML +='               </table>                                                                                           '
	cHTML +='             </div>                                                                                               '
	cHTML +='             <!-- END FOOTER -->                                                                                  '
	cHTML +='                                                                                                                  '
	cHTML +='           <!-- END CENTERED WHITE CONTAINER -->                                                                  '
	cHTML +='           </div>                                                                                                 '
	cHTML +='         </td>                                                                                                    '
	cHTML +='         <td>&nbsp;</td>                                                                                          '
	cHTML +='       </tr>                                                                                                      '
	cHTML +='     </table>                                                                                                     '
	cHTML +='   </body>                                                                                                        '
	cHTML +=' </html>                                                                                                          '
Return cHTML
