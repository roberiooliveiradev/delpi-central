#include 'protheus.ch'
#include 'parmtype.ch'

User Function MTGRDVW()

	Local ExpA1	:= PARAMIXB[1] // aViewB2
	Local ExpO1	:= PARAMIXB[2] // oListBox
	Local ExpO2	:= PARAMIXB[3] // oDlg
	Local x		:= 0
	Local nAtIni:= 1

	//...Customização do cliente

	If	cEmpAnt == '03'
		Return Nil
	EndIf

	SBZ->(DbSeek(xFilial('SBZ')+SB1->B1_COD))
	For	x:=1 to Len(ExpA1)
		aAdd(ExpA1[x],SBZ->BZ_MPLOCAL)
	Next x

	aAdd(ExpO1:aHeaders,RetTitle("BZ_MPLOCAL"))
	aAdd(ExpO1:aColSizes,55)

	nAtIni      := Len(ExpA1)

	ExpO1:SetArray(ExpA1)
	ExpO1:bLine := { || ExpA1[ExpO1:nAT]}
	ExpO1:nAt   := Max(1,nAtIni)
	ExpO1:nAt	:= 1

	ExpO2:Refresh()

Return Nil
