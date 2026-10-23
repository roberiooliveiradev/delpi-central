#Include "Protheus.ch"
#Include "Topconn.ch"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³A250ETRAN ºAutor  ³Osmar Schimitberger º Data ³  15/10/2020 º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ PONTO DE ENTRADA EXECUTADO NA ROTINA MATA250 - PRODUCAO    º±±
±±º          ³ DO MODULO PCP APOS O APONTAMENTO SER CONCLUIDO             º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function A250ETRAN()

	Local aArea := GETAREA()
	Local cOp	:= SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN
	Local cCodBar1:= Space(56)
	Local cCodBar2:= Space(56)
	Local cCodBar3:= Space(56)
	Local aSize      := {550,1300}//{150,1300}
	Local nOpc       := 0
	Local oDlg
	//Local cQuery      := ""
	//Local _cNrWeg     := ""
	Local _cDoc       := ""
	Local _cCodProd   := ""
	//Local _cCodWeg    := ""
	Local nItem       := 1
	Local cOper1 := space(10)
	Local cOper2 := space(10)
	Local cOper3 := space(10)
	Local cOper4 := space(10)
	Local cOper5 := space(10)
	Local _cRefef     := ""

	FWMsgRun(, {|| fPrcTerc() } , "Delpi", "Processando a Poder3...")

	DbSelectArea("SD3")
	DbSetOrder(1) //D3_FILIAL+D3_OP+D3_COD+D3_LOCAL
	SD3->(DBSEEK(xFILIAL("SD3")+cOp))
	While SD3->(!EoF()) .and. alltrim(SD3->D3_FILIAL+SD3->D3_OP) == xFilial("SD3")+cOp

		_cDoc:= SD3->D3_DOC
		_cCodProd:= SD3->D3_COD
		_cRefef   := Posicione("SB1",1,xFilial("SB1")+SD3->D3_COD,"B1_REFEREN")
		cCodBar1:= Space(56)
		cCodBar2:= Space(56)
		cCodBar3:= Space(56)
		cOper1 := space(10)
		cOper2 := space(10)
		cOper3 := space(10)
		cOper4 := space(10)
		cOper5 := space(10)

		If Posicione("SB1",1,xFilial("SB1")+SD3->D3_COD,"B1_XLEWEG") == "S" .and. Empty(SD3->D3_XNRWEG)

			DEFINE MSDIALOG oDlg FROM 0,0 TO aSize[1],aSize[2] TITLE "Ler Codigo de Docto do Cliente" PIXEL
			@ 0.5,001 TO 044,1300 LABEL "" OF oDlg PIXEL
			@ 007,001 Say OemToAnsi("Cod.Documento do Cliente "+SD3->D3_COD +" Ref.Cliente "+_cRefef) OF oDlg PIXEL
			@ 022,001 Say OemToAnsi("DOCUMENTO 1") OF oDlg PIXEL
			@ 035,001 GET  cCodBar1 Valid u_xValCB1(cCodBar1) When  .T. OF oDlg PIXEL
			@ 047,001 Say OemToAnsi("DOCUMENTO 2") OF oDlg PIXEL
			@ 060,001 GET  cCodBar2 Valid u_xValCB2(cCodBar2) When  .T. OF oDlg PIXEL
			@ 072,001 Say OemToAnsi("DOCUMENTO 3") OF oDlg PIXEL
			@ 085,001 GET  cCodBar3 Valid u_xValCB3(cCodBar3) When  .T. OF oDlg PIXEL
			If nItem == 1
				@ 100,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
				@ 110,001 MSGET  cOper1 Picture "@!" F3 "SZ3" Valid u_xValOpe1(cOper1) When .T. OF oDlg PIXEL
				@ 130,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
				@ 140,001 MSGET  cOper2 Picture "@!" F3 "SZ3" Valid u_xValOpe2(cOper2) When .T. OF oDlg PIXEL
				@ 160,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
				@ 170,001 MSGET  cOper3 Picture "@!" F3 "SZ3" Valid u_xValOpe3(cOper3) When .T. OF oDlg PIXEL
				@ 190,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
				@ 200,001 MSGET  cOper4 Picture "@!" F3 "SZ3" Valid u_xValOpe4(cOper4) When .T. OF oDlg PIXEL
				@ 220,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
				@ 230,001 MSGET  cOper5 Picture "@!" F3 "SZ3" Valid u_xValOpe5(cOper5) When .T. OF oDlg PIXEL
				nItem:= 0
			Endif
			@ 260,005 BUTTON OemToAnsi("Ok") SIZE 40 ,11  FONT oDlg:oFont ACTION (nOpc:=1,oDlg:End())  OF oDlg PIXEL

			ACTIVATE MSDIALOG oDlg CENTERED

			If Empty(cCodBar1) //.or. Empty(cOper1)

				Msginfo("Preenchimento do Codigo de Docto do Cliente e Operador Obrigatorio - Confimar no OK")

				DEFINE MSDIALOG oDlg FROM 0,0 TO aSize[1],aSize[2] TITLE "Ler Codigo de Docto do Cliente" PIXEL
				@ 0.5,001 TO 044,1300 LABEL "" OF oDlg PIXEL
				@ 007,001 Say OemToAnsi("Cod.Documento do Cliente "+SD3->D3_COD +" Ref.Cliente "+_cRefef) OF oDlg PIXEL
				@ 015,001 Say OemToAnsi("DOCUMENTO 1") OF oDlg PIXEL
				@ 025,001 GET  cCodBar1 Valid u_xValCB1(cCodBar1) When  .T. OF oDlg PIXEL
				@ 035,001 Say OemToAnsi("DOCUMENTO 2") OF oDlg PIXEL
				@ 045,001 GET  cCodBar2 Valid u_xValCB2(cCodBar2) When  .T. OF oDlg PIXEL
				@ 055,001 Say OemToAnsi("DOCUMENTO 3") OF oDlg PIXEL
				@ 065,001 GET  cCodBar3 Valid u_xValCB3(cCodBar3) When  .T. OF oDlg PIXEL
				If nItem == 1
					@ 100,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 110,001 MSGET  cOper1 Picture "@!" F3 "SZ3" Valid u_xValOpe1(cOper1) When .T. OF oDlg PIXEL
					@ 130,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 140,001 MSGET  cOper2 Picture "@!" F3 "SZ3" Valid u_xValOpe2(cOper2) When .T. OF oDlg PIXEL
					@ 160,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 170,001 MSGET  cOper3 Picture "@!" F3 "SZ3" Valid u_xValOpe3(cOper3) When .T. OF oDlg PIXEL
					@ 190,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 200,001 MSGET  cOper4 Picture "@!" F3 "SZ3" Valid u_xValOpe4(cOper4) When .T. OF oDlg PIXEL
					@ 220,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 230,001 MSGET  cOper5 Picture "@!" F3 "SZ3" Valid u_xValOpe5(cOper5) When .T. OF oDlg PIXEL
					nItem:= 0
				Endif
				@ 260,005 BUTTON OemToAnsi("Ok") SIZE 40 ,11  FONT oDlg:oFont ACTION (nOpc:=1,oDlg:End())  OF oDlg PIXEL

				ACTIVATE MSDIALOG oDlg CENTERED

			Endif

			If Empty(cCodBar1) //.or. Empty(cOper1)

				Msginfo("Preenchimento do Codigo de Docto do Cliente e Operador Obrigatorio - Confimar no OK")

				DEFINE MSDIALOG oDlg FROM 0,0 TO aSize[1],aSize[2] TITLE "Ler Codigo de Docto do Cliente" PIXEL
				@ 0.5,001 TO 044,1300 LABEL "" OF oDlg PIXEL
				@ 007,001 Say OemToAnsi("Cod.Documento do Cliente "+SD3->D3_COD +" Ref.Cliente "+_cRefef) OF oDlg PIXEL
				@ 015,001 Say OemToAnsi("DOCUMENTO 1") OF oDlg PIXEL
				@ 025,001 GET  cCodBar1 Valid u_xValCB1(cCodBar1) When  .T. OF oDlg PIXEL
				@ 035,001 Say OemToAnsi("DOCUMENTO 2") OF oDlg PIXEL
				@ 045,001 GET  cCodBar2 Valid u_xValCB2(cCodBar2) When  .T. OF oDlg PIXEL
				@ 055,001 Say OemToAnsi("DOCUMENTO 3") OF oDlg PIXEL
				@ 065,001 GET  cCodBar3 Valid u_xValCB3(cCodBar3) When  .T. OF oDlg PIXEL
				If nItem == 1
					@ 100,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 110,001 MSGET  cOper1 Picture "@!" F3 "SZ3" Valid u_xValOpe1(cOper1) When .T. OF oDlg PIXEL
					@ 130,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 140,001 MSGET  cOper2 Picture "@!" F3 "SZ3" Valid u_xValOpe2(cOper2) When .T. OF oDlg PIXEL
					@ 160,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 170,001 MSGET  cOper3 Picture "@!" F3 "SZ3" Valid u_xValOpe3(cOper3) When .T. OF oDlg PIXEL
					@ 190,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 200,001 MSGET  cOper4 Picture "@!" F3 "SZ3" Valid u_xValOpe4(cOper4) When .T. OF oDlg PIXEL
					@ 220,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 230,001 MSGET  cOper5 Picture "@!" F3 "SZ3" Valid u_xValOpe5(cOper5) When .T. OF oDlg PIXEL
					nItem:= 0
				Endif
				@ 260,005 BUTTON OemToAnsi("Ok") SIZE 40 ,11  FONT oDlg:oFont ACTION (nOpc:=1,oDlg:End())  OF oDlg PIXEL

				ACTIVATE MSDIALOG oDlg CENTERED

			Endif

			If Empty(cCodBar1) //.or. Empty(cOper1)

				Msginfo("Preenchimento do Codigo de Docto do Cliente e Operador Obrigatorio - Confimar no OK")

				DEFINE MSDIALOG oDlg FROM 0,0 TO aSize[1],aSize[2] TITLE "Ler Codigo de Docto do Cliente" PIXEL
				@ 0.5,001 TO 044,1300 LABEL "" OF oDlg PIXEL
				@ 007,001 Say OemToAnsi("Cod.Documento do Cliente "+SD3->D3_COD +" Ref.Cliente "+_cRefef) OF oDlg PIXEL
				@ 015,001 Say OemToAnsi("DOCUMENTO 1") OF oDlg PIXEL
				@ 025,001 GET  cCodBar1 Valid u_xValCB1(cCodBar1) When  .T. OF oDlg PIXEL
				@ 035,001 Say OemToAnsi("DOCUMENTO 2") OF oDlg PIXEL
				@ 045,001 GET  cCodBar2 Valid u_xValCB2(cCodBar2) When  .T. OF oDlg PIXEL
				@ 055,001 Say OemToAnsi("DOCUMENTO 3") OF oDlg PIXEL
				@ 065,001 GET  cCodBar3 Valid u_xValCB3(cCodBar3) When  .T. OF oDlg PIXEL
				If nItem == 1
					@ 100,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 110,001 MSGET  cOper1 Picture "@!" F3 "SZ3" Valid u_xValOpe1(cOper1) When .T. OF oDlg PIXEL
					@ 130,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 140,001 MSGET  cOper2 Picture "@!" F3 "SZ3" Valid u_xValOpe2(cOper2) When .T. OF oDlg PIXEL
					@ 160,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 170,001 MSGET  cOper3 Picture "@!" F3 "SZ3" Valid u_xValOpe3(cOper3) When .T. OF oDlg PIXEL
					@ 190,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 200,001 MSGET  cOper4 Picture "@!" F3 "SZ3" Valid u_xValOpe4(cOper4) When .T. OF oDlg PIXEL
					@ 220,001 Say OemToAnsi("Informar Codigo do Operador ?") OF oDlg PIXEL
					@ 230,001 MSGET  cOper5 Picture "@!" F3 "SZ3" Valid u_xValOpe5(cOper5) When .T. OF oDlg PIXEL
					nItem:= 0
				Endif
				@ 260,005 BUTTON OemToAnsi("Ok") SIZE 40 ,11  FONT oDlg:oFont ACTION (nOpc:=1,oDlg:End())  OF oDlg PIXEL

				ACTIVATE MSDIALOG oDlg CENTERED

			Endif

			//If len(_cCodBarras) == 56
			RecLock("SD3",.F.)
			SD3->D3_XNRWEG  := ALLTRIM(cCodBar1)+";"+ALLTRIM(cCodBar2)+";"+ALLTRIM(cCodBar3)
			SD3->D3_XOPERAD := alltrim(cOper1)+" "+alltrim(cOper2)+" "+alltrim(cOper3)+" "+alltrim(cOper4)+" "+alltrim(cOper5)
			SD3->D3_XNOMEOP:= alltrim(Posicione("SZ3",1,xFilial("SZ3")+cOper1,"Z3_NOME"))+" "+;
				alltrim(Posicione("SZ3",1,xFilial("SZ3")+cOper2,"Z3_NOME"))+" "+;
				alltrim(Posicione("SZ3",1,xFilial("SZ3")+cOper3,"Z3_NOME"))+" "+;
				alltrim(Posicione("SZ3",1,xFilial("SZ3")+cOper4,"Z3_NOME"))+" "+;
				alltrim(Posicione("SZ3",1,xFilial("SZ3")+cOper5,"Z3_NOME"))
			MsUnlock()
			//Endif
			//_cNrWeg:= SD3->D3_XNRWEG

		Endif

		DbSelectArea("SD3")
		DbSkip()

		/*/
    If Select("QRYCOD") <> 0
	    dbSelectArea("QRYCOD")
	    dbCloseArea()
    Endif

    cQuery := " SELECT *FROM "
    cQuery += " "+RetSQLName('SD3')+" "
    cQuery += " WHERE D3_OP = '"+cOp+"' "
	cQuery += " AND D3_XNRWEG <> '' "
	cQuery += " AND D3_XNRWEG = '"+substr(_cCodBarras,1,10)+"' "
	cQuery += " AND D3_DOC = '"+_cDoc+"' "
	///cQuery += " AND D3_COD = '"+_cCodProd+"' "
	cQuery += " AND D_E_L_E_T_ <> '*' "
	cQuery += " ORDER BY D3_OP, D3_COD "

    TCQuery cQuery New Alias "QRYCOD"

	DbSelectArea("QRYCOD")
    DbGoTop()
	While !(QRYCOD->(EoF()))

		_cCodWeg:= QRYCOD->D3_XNRWEG
        nItem:= 0

		While !(QRYCOD->(EoF())) .AND. QRYCOD->D3_XNRWEG == _cCodWeg

		    If nItem == 1

 	  	       Msginfo("Preenchimento do Codigo de Docto do Cliente Duplicado - Fazer a leitura novamente")
   			   DEFINE MSDIALOG oDlg FROM 0,0 TO aSize[1],aSize[2] TITLE "Ler Codigo de Docto do Cliente" PIXEL
       		   @ 0.5,001 TO 044,1300 LABEL "" OF oDlg PIXEL
       		   @ 007,001 Say OemToAnsi("Cod.Documento do Cliente "+SD3->D3_COD) OF oDlg PIXEL
   		  	   @ 015,001 MSGET _cCodBarras Valid u_xValCB(_cCodBarras) When .T. SIZE 3100 ,50 OF oDlg PIXEL
   			   @ 055,005 BUTTON OemToAnsi("Ok") SIZE 40 ,11  FONT oDlg:oFont ACTION (nOpc:=1,oDlg:End())  OF oDlg PIXEL

   		   	   ACTIVATE MSDIALOG oDlg CENTERED

			   //RecLock("SD3",.F.)
   		       //SD3->D3_XNRWEG:= substr(_cCodBarras,1,10)
   	 	       //MsUnlock()

		    Endif

        	QRYCOD->(DbSkip())

            nItem:= 1

	    EndDo

    EndDo
		/*/
	EndDo

	RESTAREA(aArea)

Return

//valida codigo de barras
User Function xValCB1(cCodBar1)

	Local cCB := alltrim(strtran(cCodBar1,chr (9),"")) // TAB

	cCodBar1:= cCB
	//msginfo(_cCodBarras)

Return(.T.)

//valida codigo de barras
User Function xValCB2(cCodBar2)

	Local cCB := alltrim(strtran(cCodBar2,chr (9),"")) // TAB

	cCodBar2:= cCB
	//msginfo(_cCodBarras)

Return(.T.)

//valida codigo de barras
User Function xValCB3(cCodBar3)

	Local cCB := alltrim(strtran(cCodBar3,chr (9),"")) // TAB

	cCodBar3:= cCB
	//msginfo(_cCodBarras)

Return(.T.)

//valida operaoor
User Function xValOPe1(cOper1)

	DbSelectArea("SZ3")
	DbSetOrder(1)
	If !DbSeek(xFilial("SZ3")+cOper1)

		Msginfo("Infromar codigo de operador existente")

		Return(.F.)

	Endif

Return(.T.)

//valida operaoor
User Function xValOPe2(cOper2)

	DbSelectArea("SZ3")
	DbSetOrder(1)
	If !DbSeek(xFilial("SZ3")+cOper2)

		If !Empty(cOper2)

			Msginfo("Infromar codigo de operador existente")
			Return(.F.)

		Endif

	Endif

Return(.T.)

//valida operaoor
User Function xValOPe3(cOper3)

	DbSelectArea("SZ3")
	DbSetOrder(1)
	If !DbSeek(xFilial("SZ3")+cOper3)

		If !Empty(cOper3)

			Msginfo("Infromar codigo de operador existente")
			Return(.F.)

		Endif

	Endif

Return(.T.)


//valida operaoor
User Function xValOPe4(cOper4)

	DbSelectArea("SZ3")
	DbSetOrder(1)
	If !DbSeek(xFilial("SZ3")+cOper4)

		If !Empty(cOper4)

			Msginfo("Infromar codigo de operador existente")
			Return(.F.)

		Endif

	Endif

Return(.T.)


//valida operaoor
User Function xValOPe5(cOper5)

	DbSelectArea("SZ3")
	DbSetOrder(1)
	If !DbSeek(xFilial("SZ3")+cOper5)

		If !Empty(cOper5)

			Msginfo("Infromar codigo de operador existente")
			Return(.F.)

		Endif

	Endif

Return(.T.)

/*Gabriel Araujo - 19/05/2022 - */

Static Function fPrcTerc()

	Local lProc := SuperGetMV("MV_DOPTERC",.F.,IIF(TRIM(cEmpAnt)$"01_05",.t.,.f.))

	if  lProc
		cQuery := "EXEC [dbo].[STP_DELPI_OP_TERCEIRO_"+cEmpAnt+"]  @DATADE = "+valtosql("20211201")
		TCSQLExec(cQuery)

	endif
	//005444
Return (Nil)
