#INCLUDE "PROTHEUS.CH"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³MT010INC  ºAutor  ³Marcos A. Schoeffel º Data ³  09/18/15   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³P.E. Executado depois da gravação da inclusao do produto    º±±
±±º          ³ para a geracao automatica do registro do mesmo na tabela   º±±
±±º          ³ de indicadores SBZ                                         º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function MT010INC()

	Local aFiliais := {'01','02'}
	Local aArea := getarea()
	Local aAreaF3K   := F3K->(GetArea())
	Local _x
	Local n1
	CONOUT("INI MT010INC")
	If	cEmpAnt == '03'
		CONOUT("FIM CEMPANT 03 MT010INC")
		Return
	EndIf
	If	cEmpAnt == '01'
		CriaSB2(SB1->B1_COD,"01","01")
		CriaSB2(SB1->B1_COD,"99","01")
		CriaSB2(SB1->B1_COD,"01","02")
		CriaSB2(SB1->B1_COD,"99","02")
		SBZ->(DbSetOrder(1))
		//For	_x:=1 To Len(aFiliais)
		//	SBZ->(DbSeek(aFiliais[_x]+SB1->B1_COD))
		//	If	!SBZ->(Found())
		//		RecLock('SBZ',.T.)
		//		SBZ->BZ_FILIAL	:= aFiliais[_x]
		//		SBZ->BZ_COD		:= SB1->B1_COD
		//		SBZ->BZ_LOCPAD	:= "01" //SB1->B1_LOCPAD
		//		MsUnlock()
		//	EndIf
		//Next _x
		For	n1:=1 To Len(aFiliais)
			SBZ->(DbSeek(aFiliais[n1]+SB1->B1_COD))
			If	SBZ->(Found())
				if !Empty(SBZ->BZ_MPLOCAL )
					DbSelectArea("SB2")
					SB2->(DbSetOrder(1))
					If	(SB2->(DbSeek(SBZ->BZ_FILIAL+SB1->B1_COD+"01")))
						RecLock('SB2',.F.)
						SB2->B2_MAPA		:= SBZ->BZ_MPLOCAL
						MsUnlock()
					EndIf
				EndIf
			EndIf
		Next n1

		DbSelectArea("F3K")
		If !(Empty(F3K->(IndexKey(2))))	//Verificar se há ordem 2 de F3K cadastrado na SIX
			F3K->(dbSetOrder(2)) // F3K_FILIAL + F3K_PROD + F3K_CFOP + F3K_CST
			lFil := .f.
			IF cFilAnt !="01"
				lFil := .t.
				cFilOld := cFilAnt
				cFilAnt := "01"
				FWSM0Util():setSM0PositionBycFilAnt()
			ENDIF

			If !(F3K->(DbSeek(xFilial("F3K") + PadR(SB1->B1_COD, TamSX3("L2_PRODUTO")[1]))))

				FWMsgRun(, {|| U_DLP09F04(SB1->B1_COD) }, "Delpi", "Cadastro Valores Acessorios")

			EndIf

			IF lFil

				cFilAnt := cFilOld
				FWSM0Util():setSM0PositionBycFilAnt()

			ENDIF
		EndIf

		//CONOUT("FIM CEMPANT 03 MT010INC")
		//	Return
	EndIf

	RESTAREA(aAreaF3K)
	RESTAREA(aArea)
	CONOUT("FIM MT010INC")
Return
