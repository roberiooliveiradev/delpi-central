#include "Protheus.ch"
#include "RwMake.ch"

/*
_____________________________________________________________________________
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦Programa  ¦ DLP017  ¦ Autor ¦Marcos A Schoeffel ¦ Data ¦ 12/11/15      ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Chamado pelo MT103FIM N.F.Entrada - IMPORTACAO             ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Uso       ¦ Especifico para Delpi                                      ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦¦          ¦ Trata importacao somente pela entrada em compras           ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
/*/

User Function DLP017()

	Local   aArea1	 		:= GetArea()

	Private	_oDlg1
	Private oGetTrans
	Private nSuperior  		:= C(138)			// Distancia entre a MsNewGetDados e o extremidade superior do objeto que a contem
	Private nEsquerda	  	:= C(005)			// Distancia entre a MsNewGetDados e o extremidade esquerda do objeto que a contem
	Private nInferior  		:= C(210)			// Distancia entre a MsNewGetDados e o extremidade inferior do objeto que a contem
	Private nDireita	   	:= C(235)			// Distancia entre a MsNewGetDados e o extremidade direita  do objeto que a contem
	Private nOpcSF1			:= 3				// 1- Visualizar, 2- Incluir, 3- Alterar, 4-Excluir
	Private cLinhaOk  		:= "AllwaysTrue"	// Funcao executada para validar o contexto da linha atual do aCols
	Private cTudoOk 	   	:= "AllwaysTrue"	// Funcao executada para validar o contexto geral da MsNewGetDados (todo aCols)
	Private cIniCpos   		:= ""				// Nome dos campos do tipo caracter que utilizarao incremento automatico.
	Private aAlter    	 	:= {'CD5_TPIMP','CD5_NADIC','CD5_SQADIC','CD5_DOCIMP','CD5_DTPCOF','CD5_DTPPIS','CD5_DSPAD'} // Campos alteráveis da GetDados
	Private nFreeze	    	:= 000			// Campos estaticos na GetDados.
	Private nMax       		:= 999			// Numero maximo de linhas permitidas. Valor padrao 99
	Private cCampoOk   		:= "AllwaysTrue"	// Funcao executada na validacao do campo
	Private cSuperApagar	:= ""			// Funcao executada quando pressionada as teclas <Ctrl>+<Delete>
	Private cApagaOk   		:= "AllwaysFalse"   // Funcao executada para validar a exclusao de uma linha do aCols
	Private aCampos 		:= {'D1_ITEM','D1_COD','CD5_TPIMP','CD5_NADIC','CD5_SQADIC','CD5_DOCIMP','D1_II','CD5_DSPAD','CD5_BSCOF','CD5_ALCOF','CD5_VLCOF','CD5_DTPCOF','CD5_BSPIS','CD5_ALPIS','CD5_VLPIS','CD5_DTPPIS'}
	Private aLinha			:= {Space(TamSx3('D1_ITEM')[1]), Space(TamSx3('D1_COD')[1]),Space(TamSx3('CD5_TPIMP')[1]),Space(TamSx3('CD5_NADIC')[1]),;
		Space(TamSx3('CD5_SQADIC')[1]),Space(TamSx3('CD5_DOCIMP')[1]), 0.00, 0.00, 0.00, 0.00, 0.00, Stod(''), 0.00, 0.00, 0.00, Stod(''), .F. }
	Private aHeaderSF1		:= MontEstr(1)		// aHeader GetDados
	Private aColsSF1		:= {}			// aCols   GetDados

	// Nota
	Private cDocLoc2 		:= SF1->F1_DOC
	Private cSerieLoc		:= SF1->F1_SERIE

	//Transporte
	Private M->F1_MENSNF1 	:= Space(TamSX3("F1_MENSNF1")[1])
	Private M->F1_MENSNF2  	:= Space(TamSX3("F1_MENSNF2")[1])
	Private M->F1_MENSNF3 	:= Space(TamSX3("F1_MENSNF3")[1])

	//Importação
	Private M->CD5_DTDI 	:= CriaVar("CD5_DTDI")
	Private M->CD5_DTDES 	:= CriaVar("CD5_DTDES")
	Private M->CD5_NDI 	  	:= CriaVar("CD5_NDI")
	Private M->CD5_UFDES 	:= CriaVar("CD5_UFDES")
	Private M->CD5_LOCDES  	:= CriaVar("CD5_LOCDES")
	Private M->CD5_LOCAL	:= CriaVar("CD5_LOCAL")
	Private M->CD5_VTRANS	:= CriaVar("CD5_VTRANS")
	Private M->CD5_VAFRMM	:= CriaVar("CD5_VAFRMM")
	Private M->CD5_INTERM	:= CriaVar("CD5_INTERM")

	If 	SA2->( Dbseek( xFilial( "SA2" ) + SF1->( F1_FORNECE + F1_LOJA ) ) )
		aColsSF1 := MontEstr(2)
	Endif

	@ C(001) , C(001) To C(480) , C(490) Dialog _oDlg1 Title "Dados Complementares"

	@ C(004) ,  C(005) Say OemtoAnsi("Nota:") Size C(039),C(008) PIXEL OF _oDlg1
	@ C(003) ,  C(045) MsGet oEdit1 Var cDocLoc2 WHEN .F. F3 "SF1CUS" Valid ( CrgDadosEnt( cDocLoc2, cSerieLoc ) )  Size C(035),C(006) PIXEL OF _oDlg1 //SF1CUS Consulta padrao que retorna Doc e Serie das notas fiscais de entrada

	@ C(004) ,  C(090) Say OemtoAnsi("Serie:") Size C(039),C(008) PIXEL OF _oDlg1
	@ C(003) ,  C(140) MsGet oEdit1 Var cSerieLoc  Size C(015),C(006) When .F. PIXEL OF _oDlg1

	@ C(015) ,  C(002) To C(060) , C(240) LABEL OemtoAnsi("Mensagem") PIXEL OF _oDlg1
	@ C(065) ,  C(002) To C(215) , C(240) LABEL OemtoAnsi("Dados de Importação") PIXEL OF _oDlg1

	//Mensagem
	@ C(025) , C(005) Say OemtoAnsi("Mensagem 1") PIXEL OF _oDlg1
	@ C(025) , C(045) MsGet oEdit1 Var M->F1_MENSNF1 Picture "@!" Size C(180),C(006) PIXEL OF _oDlg1

	@ C(035) , C(005) Say OemtoAnsi("Mensagem 2") PIXEL OF _oDlg1
	@ C(035) , C(045) MsGet oEdit1 Var M->F1_MENSNF2 Picture "@!" Size C(180),C(006) PIXEL OF _oDlg1

	@ C(045) , C(005) Say OemtoAnsi("Mensagem 3") PIXEL OF _oDlg1
	@ C(045) , C(045) MsGet oEdit1 Var M->F1_MENSNF3  Picture "@!" Size C(180),C(006) PIXEL OF _oDlg1

	// Importação
	@ C(075) , C(005) Say OemtoAnsi("Número DI") PIXEL OF _oDlg1
	@ C(075) , C(045) MsGet oEdit1 Var M->CD5_NDI  Size C(040),C(006) PIXEL OF _oDlg1

	@ C(075) , C(090) Say OemtoAnsi("Emissao DI") PIXEL OF _oDlg1
	@ C(075) , C(140) MsGet oEdit1 Var M->CD5_DTDI Valid ( M->CD5_DTDI <= dDataBase ) Size C(040),C(006) PIXEL OF _oDlg1

	@ C(085) , C(005) Say OemtoAnsi("UF de Desembaraço") PIXEL OF _oDlg1
	@ C(085) , C(045) MsGet oEdit1 Var M->CD5_UFDES F3 "12" VALID ( !Empty( Tabela( "12" , M->CD5_UFDES , .F. ) ) ) Size C(019),C(006) PIXEL OF _oDlg1

	@ C(085) , C(090) Say OemtoAnsi("Dt Desembaraço") PIXEL OF _oDlg1
	@ C(085) , C(140) MsGet oEdit1 Var M->CD5_DTDES  Valid ( M->CD5_DTDES <= dDataBase ) Size C(040),C(006) PIXEL OF _oDlg1

	SX3->(DbSetOrder(2))
	SX3->(DbSeek('CD5_LOCDES'))
	cTitSay1 := SX3->(X3Titulo())
	@ C(095) , C(005) Say OemtoAnsi(cTitSay1) PIXEL OF _oDlg1
	@ C(095) , C(045) MsGet oEdit1 Var M->CD5_LOCDES Size C(180),C(006) PIXEL OF _oDlg1

	SX3->(DbSetOrder(2))
	SX3->(DbSeek('CD5_LOCAL'))
	cTitSay2 := SX3->(X3Titulo())
	aRetBox2 := ComboX3Box("CD5_LOCAL", X3Cbox())
	cValSay2 := IIf(!Empty(SX3->X3_VALID),AllTrim(SX3->X3_VALID),'.T.') + ' .And. ' + IIf(!Empty(SX3->X3_VLDUSER),AllTrim(SX3->X3_VLDUSER),'.T.')
	@ C(105) , C(005) Say OemtoAnsi(cTitSay2) PIXEL OF _oDlg1
	@ C(105) , C(045) MsComboBox oEdit2 Var M->CD5_LOCAL Items aRetBox2 Valid &cValSay2 Size C(180),C(006) PIXEL OF _oDlg1

	SX3->(DbSetOrder(2))
	SX3->(DbSeek('CD5_VTRANS'))
	cTitSay3 := SX3->(X3Titulo())
	aRetBox3 := ComboX3Box("CD5_VTRANS", X3Cbox())
	cValSay3 := IIf(!Empty(SX3->X3_VALID),AllTrim(SX3->X3_VALID),'.T.') + ' .And. ' + IIf(!Empty(SX3->X3_VLDUSER),AllTrim(SX3->X3_VLDUSER),'.T.')
	@ C(115) , C(005) Say OemtoAnsi(cTitSay3) PIXEL OF _oDlg1
	@ C(115) , C(045) MsComboBox oEdit3 Var M->CD5_VTRANS Items aRetBox3 Valid &cValSay3 Size C(050),C(006) PIXEL OF _oDlg1

	SX3->(DbSetOrder(2))
	SX3->(DbSeek('CD5_VAFRMM'))
	cTitSay4 := SX3->(X3Titulo())
	@ C(115) , C(100) Say OemtoAnsi(cTitSay4) PIXEL OF _oDlg1
	@ C(115) , C(150) MsGet oEdit4 Var M->CD5_VAFRMM Picture PesqPict("CD5","CD5_VAFRMM",14) Size C(040),C(006) PIXEL OF _oDlg1

	SX3->(DbSetOrder(2))
	SX3->(DbSeek('CD5_INTERM'))
	cTitSay5 := SX3->(X3Titulo())
	aRetBox5 := ComboX3Box("CD5_INTERM", X3Cbox())
	cValSay5 := IIf(!Empty(SX3->X3_VALID),AllTrim(SX3->X3_VALID),'.T.') + ' .And. ' + IIf(!Empty(SX3->X3_VLDUSER),AllTrim(SX3->X3_VLDUSER),'.T.')
	@ C(125) , C(005) Say OemtoAnsi(cTitSay5) PIXEL OF _oDlg1
	@ C(125) , C(045) MsComboBox oEdit5 Var M->CD5_INTERM Items aRetBox5 Valid &cValSay5 Size C(100),C(006) PIXEL OF _oDlg1

	oGetTrans := MsNewGetDados():New( nSuperior, nEsquerda, nInferior, nDireita,;
		nOpcSF1, cLinhaOk, cTudoOk, cIniCpos, aAlter, nFreeze, Len(aColsSF1) /*nMax*/,;
		cCampoOk, cSuperApagar, cApagaOk, _oDlg1, aHeaderSF1, aColsSF1)

	@ C(220) , C(155) Button OemtoAnsi("Confirmar") Size C(037),C(012) Action(Grava()) PIXEL OF _oDlg1
	@ C(220) , C(195) Button OemtoAnsi("Cancelar") Size C(037),C(012) Action(_oDlg1:END()) PIXEL OF _oDlg1

	Activate Dialog _oDlg1 Centered

	RestArea(aArea1)
Return(.T.)

/*/
_____________________________________________________________________________
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦Programa  ¦ GRAVA    ¦ Autor ¦Marcos A. Schoeffl ¦ Data ¦ 12/11/15     ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Função para gravar os dados digitados pelo usuario         ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Uso       ¦ Especifico para Delpi                                      ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
/*/
Static Function Grava()

	Local aAreaQ	:= GetArea()
	Local nRegAcols	:= Len(oGetTrans:aCols)
	Local nB		:= 0
	Local nRecAcl	:= 5

	DbSelectArea("SF1")
	DbSetOrder(1)
	If cDocLoc2 + cSerieLoc == SF1->( F1_DOC + F1_SERIE )

		Reclock("SF1",.F.)
		//Transporte
		SF1->F1_MENSNF1   := M->F1_MENSNF1
		SF1->F1_MENSNF2   := M->F1_MENSNF2
		SF1->F1_MENSNF3   := M->F1_MENSNF3
		Msunlock()

		//Importação
		DbSelectArea("CD5")
		DbSetOrder(1)
		For nB := 1 to Len(oGetTrans:aCols)
			//DbGoTo( oGetTrans:aCols [ nB, nRecAcl ] )
			RecLock( "CD5", .T. )
			CD5->CD5_FILIAL := xFilial('CD5')
			CD5->CD5_DOC	:= SF1->F1_DOC
			CD5->CD5_SERIE	:= SF1->F1_SERIE
			CD5->CD5_ESPEC	:= SF1->F1_ESPECIE
			CD5->CD5_FORNEC	:= SF1->F1_FORNECE
			CD5->CD5_LOJA	:= SF1->F1_LOJA
			CD5->CD5_CODEXP	:= SF1->F1_FORNECE
			CD5->CD5_LOJEXP	:= SF1->F1_LOJA
			CD5->CD5_CODFAB := SF1->F1_FORNECE
			CD5->CD5_LOJFAB := SF1->F1_LOJA
			CD5->CD5_CNPJAE	:= SM0->M0_CGC

			CD5->CD5_ITEM	:= GdFieldGet('D1_ITEM'   ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_TPIMP	:= GdFieldGet('CD5_TPIMP' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_NADIC	:= GdFieldGet('CD5_NADIC' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_SQADIC	:= GdFieldGet('CD5_SQADIC',nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_DOCIMP := GdFieldGet('CD5_DOCIMP',nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_BSPIS	:= GdFieldGet('CD5_BSPIS' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_ALPIS	:= GdFieldGet('CD5_ALPIS' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_VLPIS	:= GdFieldGet('CD5_VLPIS' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_DTPPIS	:= GdFieldGet('CD5_DTPPIS',nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_BSCOF	:= GdFieldGet('CD5_BSCOF' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_ALCOF	:= GdFieldGet('CD5_ALCOF' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_VLCOF	:= GdFieldGet('CD5_VLCOF' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_DTPCOF	:= GdFieldGet('CD5_DTPCOF',nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_VLRII	:= GdFieldGet('D1_II'     ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)
			CD5->CD5_DSPAD	:= GdFieldGet('CD5_DSPAD' ,nB,.F.,oGetTrans:aHeader,oGetTrans:aCols)

			CD5->CD5_LOCAL	:= M->CD5_LOCAL
			CD5->CD5_NDI	:= M->CD5_NDI
			CD5->CD5_DTDI	:= M->CD5_DTDI
			CD5->CD5_LOCDES := M->CD5_LOCDES
			CD5->CD5_UFDES	:= M->CD5_UFDES
			CD5->CD5_DTDES	:= M->CD5_DTDES
			CD5->CD5_VTRANS	:= M->CD5_VTRANS
			CD5->CD5_VAFRMM	:= M->CD5_VAFRMM
			CD5->CD5_INTERM	:= M->CD5_INTERM

			CD5->(MsUnLock())
		Next nB
		_oDlg1:End()

	Else

		Alert(" Nota não encontrada, verifique os parametros ")

	Endif

	RestArea(aAreaQ)

Return()

/*/
_____________________________________________________________________________
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦Programa  ¦ CrgDadosEnt  ¦ Autor ¦Marcos A Schoeffel¦ Data ¦ 12/11/15  ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Função para trazer na tela os dados já preenchidos         ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Uso       ¦ Especifico para Delpi                                      ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
/*/

Static Function CrgDadosEnt( cDocLoc2 , cSerieLoc )

	Local aArea2	:= GetArea()
	Local lRet 	:= .T.

	If 	(cDocLoc2 + cSerieLoc) == SF1->( F1_DOC + F1_SERIE )
		//Transporte
		M->F1_MENSNF1 	:= Iif( !Empty( SF1->F1_MENSNF1 ), SF1->F1_MENSNF1 , Space( TAMSX3( "F1_MENSNF1" )[1] ) )
		M->F1_MENSNF2	:= Iif( !Empty( SF1->F1_MENSNF2 ), SF1->F1_MENSNF2 , Space( TAMSX3( "F1_MENSNF2" )[1] ) )
		M->F1_MENSNF3	:= Iif( !Empty( SF1->F1_MENSNF3 ), SF1->F1_MENSNF3 , Space( TAMSX3( "F1_MENSNF3" )[1] ) )

		oGetTrans:aCols	:= MontEstr(2)
		_oDlg1:Refresh()
		oGetTrans:Refresh()
	Else
		If !Empty(cDocLoc2 + cSerieLoc)
			Alert(" Nota não encontrada, verifique os parametros ")
			lRet	:= .F.
		Else
			lRet	:= .T.
		Endif
	Endif

	RestArea(aArea2)

Return(lRet)


/*/
_____________________________________________________________________________
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦Programa  ¦ MontEstr     ¦ Autor ¦Marcos A Schoeffel ¦ Data ¦ 12/11/15 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Função para montar a tela                                  ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Uso       ¦ Especifico para Delpi                                      ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
/*/

Static Function MontEstr( nOpcGet )

	Local aArea3	:= GetArea()
	Local aCabDet	:= {}
	Local _nN	:= 0

	If nOpcGet == 1

		DbSelectArea( "SX3" )
		DbSetOrder( 2 )
		Dbgotop()
		For _x:= 1 To Len(aCampos)
			MsSeek(aCampos[_x] )

			If	SX3->(Found())
				AADD( aCabDet, { Alltrim(X3_TITULO), AllTrim(X3_CAMPO), X3_PICTURE, X3_TAMANHO, X3_DECIMAL,"","", X3_TIPO, "", "" } )
			EndIf
		Next _x

	Else

		DbSelectArea( "SD1" )
		DbSetOrder(1)
		If DbSeek( xFilial("SD1") + SF1->( F1_DOC + F1_SERIE + F1_FORNECE + F1_LOJA ) )
			While !SD1->(EOF()) .AND. SF1->( F1_DOC + F1_SERIE + F1_FORNECE + F1_LOJA) == SD1->( D1_DOC + D1_SERIE + D1_FORNECE + D1_LOJA)

				AADD( aCabDet, aClone(aLinha))

				For nJ := 1 To SD1->(FCount())
					If ( nPos := aScan(aCampos, SD1->(FieldName(nJ))) ) > 0
						aCabDet[Len(aCabDet),nPos] := SD1->(FieldGet(nJ))
					ElseIf	AllTrim(SD1->(FieldName(nJ))) == 'D1_BASIMP5'
						aCabDet[Len(aCabDet),aScan(aCampos, 'CD5_BSCOF' )] := SD1->(FieldGet(nJ))
					ElseIf	AllTrim(SD1->(FieldName(nJ))) == 'D1_ALQIMP5'
						aCabDet[Len(aCabDet),aScan(aCampos, 'CD5_ALCOF' )] := SD1->(FieldGet(nJ))
					ElseIf	AllTrim(SD1->(FieldName(nJ))) == 'D1_VALIMP5'
						aCabDet[Len(aCabDet),aScan(aCampos, 'CD5_VLCOF' )] := SD1->(FieldGet(nJ))
					ElseIf	AllTrim(SD1->(FieldName(nJ))) == 'D1_BASIMP6'
						aCabDet[Len(aCabDet),aScan(aCampos, 'CD5_BSPIS' )] := SD1->(FieldGet(nJ))
					ElseIf	AllTrim(SD1->(FieldName(nJ))) == 'D1_ALQIMP6'
						aCabDet[Len(aCabDet),aScan(aCampos, 'CD5_ALPIS' )] := SD1->(FieldGet(nJ))
					ElseIf	AllTrim(SD1->(FieldName(nJ))) == 'D1_VALIMP6'
						aCabDet[Len(aCabDet),aScan(aCampos, 'CD5_VLPIS' )] := SD1->(FieldGet(nJ))
					EndIf
				Next nJ

				aCabDet[Len(aCabDet), aScan(aCampos, 'CD5_DTPPIS')] := MsDate()
				aCabDet[Len(aCabDet), aScan(aCampos, 'CD5_DTPCOF')] := MsDate()

				SD1->(Dbskip())
			Enddo
		Endif

	Endif

	RestArea( aArea3 )

Return( aCabDet )

/*ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa   ³   C()   ³ Autores ³ Norbert/Ernani/Mansano ³ Data ³10/05/2005³±±
*±ÃÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descricao  ³ Funcao responsavel por manter o Layout independente da       ³±±
±±³           ³ resolucao horizontal do Monitor do Usuario.                  ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß*/
Static Function C(nTam)
	Local nHRes	:=	oMainWnd:nClientWidth	// Resolucao horizontal do monitor
	If nHRes == 640	// Resolucao 640x480 (soh o Ocean e o Classic aceitam 640)
		nTam *= 0.8
	ElseIf (nHRes == 798).Or.(nHRes == 800)	// Resolucao 800x600
		nTam *= 1
	Else	// Resolucao 1024x768 e acima
		nTam *= 1.28
	EndIf

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Tratamento para tema "Flat"³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If "11" $ oApp:cVersion
		If (Alltrim(GetTheme()) == "FLAT") .Or. SetMdiChild()
			nTam *= 0.90
		EndIf
	EndIf
Return Int(nTam)
