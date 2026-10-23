#INCLUDE "TBICONN.CH"
#INCLUDE "FWMVCDEF.CH"
#Include 'PROTHEUS.CH'
#Include 'TOTVS.CH'


User function DLP73F02(nOpc)

	Local aRotBkp := aRotina

	if nOpc == 1
		CMODULO := "EST"
		nmodulo := 4

		SetKey( VK_F4, { || D73F02A() } )
		U_MATA010M()
		CMODULO := "CRM"
		nmodulo := 73
	elseif nOpc == 2 //Estruturas
		// CMODULO := "PCP"
		//  MATA200()
		// CMODULO := "CRM"
		CMODULO := "PCP"
		nmodulo := 10
		aRotina := PCPA200Men()
		PCPA200()
		aRotina := aRotBkp
		CMODULO := "CRM"
		nmodulo := 73

	elseif nOpc == 3
		CMODULO := "PCP"
		nmodulo := 10
		U_DLPM632()
		// PCPA129()
		CMODULO := "CRM"
		nmodulo := 73
	elseif nOpc == 4
		nmodulo := 4
		CMODULO := "EST"
		//MATC010()
		//AD1_NROPOR
		//AD1MASTER
		U_DLP02F02(M->AD1_NROPOR)
		CMODULO := "CRM"
		nmodulo := 73
	elseif nOpc == 5
		nmodulo := 2
		CMODULO := "EST"
		u_DMATA061()
		CMODULO := "CRM"
		nmodulo := 73
	ENDIF
RETURN

Static Function fGetOper(cGetOp,nOpc)

	Local aButtons := {}
	Local oComboBo1
	Local nComboBo1 :=  "Incluir"
	Local oGet1
	Local cProd := space(tamsx3("B1_COD")[1])
	Local cDesc := space(tamsx3("B1_DESC")[1])
	Local oSay1
	Local oSay2
	Local cTitMnu := iif(nOpc == 1 ,"Produtos" , "Roteiro Operações")
	Local cOldTitle := CCADASTRO
	Static oDlgPrd
	Static lWhPrd := .F.
	CCADASTRO := "Delpi - CRM"


	DEFINE MSDIALOG oDlgPrd TITLE cTitMnu FROM 000, 000  TO 180, 570 COLORS 0, 16777215 PIXEL

	@ 035, 008 SAY oSay2 PROMPT "Operacao" SIZE 053, 009 OF oDlgPrd COLORS 0, 16777215 PIXEL
	@ 035, 072 MSCOMBOBOX oComboBo1 VAR nComboBo1 ITEMS  iif(nOpc == 1 ,{"Incluir","Alterar","Copiar"},{"Incluir","Alterar"} ) ;
		SIZE 072, 010 OF oDlgPrd VALID fVlOper(@lWhPrd,nComboBo1) COLORS 0, 16777215 PIXEL

	@ 051, 008 SAY oSay1 PROMPT "Produto" SIZE 053, 009 OF oDlgPrd COLORS 0, 16777215           PIXEL
	@ 052, 072 MSGET oGet1 VAR cProd SIZE 060, 010 OF oDlgPrd COLORS 0, 16777215 WHEN lWhPrd F3 iif(nOpc == 1 ,"SB1","SG2") ;
		VALID fVldPrd(cProd,@cDesc)        PIXEL
	@ 067, 008 MSGET oGet2 VAR cDesc SIZE 244, 013 OF oDlgPrd COLORS 0, 16777215 WHEN .f. PIXEL


	bOk := {|| DF02End(@oDlgPrd,nComboBo1,cProd,@cGetOp,nOpc ) } //Botao salvar
	bCancel := {||cGetOp := 0,oDlgPrd:End()} //botao cancelar

	ACTIVATE MSDIALOG oDlgPrd ON INIT EnchoiceBar(oDlgPrd, bOk , bCancel,,,,,,,,,,"Cad Produtos")  CENTERED


	CCADASTRO := cOldTitle

Return
Static Function DF02End(oDlgPrd,nComboBo1,cProd,cGetOp,nOpc)


	IF nComboBo1 $ "Incluir"
		cGetOp :=  IIF(nComboBo1 $ "Incluir",1,2)
		lRetPrd := .t.
		oDlgPrd:End()
		Return

	ELSE

		IF EMPTY(cProd) .OR.  IIF(nOpc == 1,!ExistCpo("SB1",cProd),!ExistCpo("SG2",cProd))
			msginfo("Produto Invalido")
			Return
		ENDIF
		cGetOp := IIF(nComboBo1 $ "Alterar",2,3)
		if nOpc == 1
			DbSelectArea("SB1")
			DbSetOrder(1)
			DbSeek(xFilial("SB1") + cProd)
		else
			DbSelectArea("SG2")
			DbSetOrder(1)
			DbSeek(xFilial("SG2") + cProd)
		endif
		lRetPrd := .t.
		oDlgPrd:End()
	ENDIF
Return
//valida o produto digitado e ajusta a descrição
Static Function fvldPrd(cProd,cDesc)
	Local lRet := .t.

	if !Empty(cProd)

		if  !ExistCpo("SB1",cProd)

			msginfo("Produto Não Existe")
			lRet := .f.

		else

			cDesc := POSICIONE("SB1",1,XFILIAL("SB1")+cProd,"B1_DESC")

		endif

	endif

Return lRet

Static Function fVlOper(lWhPrd,nComboBo1)

	if nComboBo1 == "Incluir"
		lWhPrd := .f.
	else
		lWhPrd:=.t.
	end

RETURN .T.

Static Function fGetFil(cFil)

	Local aButtons := {}

	Local oGet1
	Local cGetFil := CEMPANT //space(tamsx3("B1_FILIAL")[1])

	Local oSay1
	Local oSay2
	Local cOldTitle := CCADASTRO
	Static oDlgPrd
	Static lRet := .F.
	CCADASTRO := "Delpi - Formacao de Preco"


	DEFINE MSDIALOG oDlgPrd TITLE CCADASTRO FROM 000, 000  TO 180, 570 COLORS 0, 16777215 PIXEL

	@ 035, 008 SAY oSay2 PROMPT "Filial" SIZE 053, 009 OF oDlgPrd COLORS 0, 16777215 PIXEL
	@ 035, 072 MSGET oGet1 VAR cGetFil SIZE 060, 010 OF oDlgPrd COLORS 0, 16777215  F3 "SM3" VALID ExistCpo('SM0',cEmpAnt+cGetFil,1)         PIXEL

	bOk := {|| F010End(@oDlgPrd,cGetFil,@cFil,@lRet ) } //Botao salvar
	bCancel := {||oDlgPrd:End()} //botao cancelar

	ACTIVATE MSDIALOG oDlgPrd ON INIT EnchoiceBar(oDlgPrd, bOk , bCancel,,,,,,,,,,"Form Preco")  CENTERED


	CCADASTRO := cOldTitle

Return lRet

sTATIC FUNCTION F010End(oDlgPrd,cGetFil,cFil,lRet)

	if !Empty(cGetFil)
		cFil:=cGetFil
		cGetFil:=.t.
		oDlgPrd:End()
	endif
Return






/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010Consul ³ Autor ³Alexandre Inacio Lemes³ Data ³31/03/2005³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Excuta a chamada da funcao MC050con para consulta do produto³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ Nenhum 	                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA010                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//Function A010Consul()
STATIC Function D73F02A()

	Local aArea    := GetArea()

	SetKey( VK_F12, { || pergunte("MTC050",.T.) } )
	If pergunte("MTC050",.T.)
		MC050Con()
	EndIf

	Set Key VK_F4 TO MT010F4()

	SetKey( VK_F12, { || pergunte("MTA010",.T.) } )
	Pergunte("MTA010",.F.)

	RestArea(aArea)
Return Nil
