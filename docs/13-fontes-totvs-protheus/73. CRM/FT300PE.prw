#Include 'TOTVS.ch'
#Include 'FWMVCDef.ch'

Static cProVenOld := Nil
Static cEstagioOld := Nil

/*/{Protheus.doc} FATA300PE
P.E da rotina FATA300 - Oportunidade de Vendas
@author  Johnni Moraes
@since   03/12/2025
/*/
User function FATA300

	Local aParam     := PARAMIXB
	Local xRet       := .T.
	Local cIdPonto   := ''
	Local cIdModel   := ''
	Local oModel     := NIL
	Local nOperation := 0

	If aParam <> NIL

		oModel     := aParam[1]
		cIdPonto   := aParam[2]
		cIdModel   := aParam[3]
		lIsGrid    := ( Len( aParam ) > 3 )

		nOperation := oModel:GetOperation()

		If cIdPonto == 'MODELPOS'

			If nOperation == MODEL_OPERATION_UPDATE .Or. nOperation == MODEL_OPERATION_INSERT
				// Dispara eventos de acordo com a alteração do estágio da oportunidade de venda
				u_DLP73P01(oModel, cProVenOld, cEstagioOld)
			EndIf

		EndIf

		If cIdPonto == 'BUTTONBAR'

			If cProVenOld == Nil .Or. cEstagioOld == Nil
				cProVenOld := oModel:GetModel("AD1MASTER"):GetValue("AD1_PROVEN")
				cEstagioOld := oModel:GetModel("AD1MASTER"):GetValue("AD1_STAGE")
			EndIf

			// Trata campos após o modelo estar carregado
			If FWIsInCallStack("U_FT300COP") // Cópia da Oportunidade
				u_DLP73A01(oModel, MODEL_OPERATION_INSERT)
			ElseIf FWIsInCallStack("U_FT300REP")
				u_DLP73A02(oModel) // Réplica da Oportunidade
			EndIf

		EndIf

		If cIdPonto == "MODELCOMMITTTS"
			If nOperation == MODEL_OPERATION_INSERT .And. (FWIsInCallStack("U_FT300REP") .Or. FWIsInCallStack("U_FT300COP"))
				cNumNewOV := oModel:GetModel("AD1MASTER"):GetValue("AD1_NROPOR")
			EndIf
		EndIf

		If cIdPonto == "MODELCOMMITNTTS"

			If nOperation == MODEL_OPERATION_INSERT .And. (FWIsInCallStack("U_FT300REP") .Or. FWIsInCallStack("U_FT300COP"))
				// Indica sucesso na replicação/copia para copia de dados complementares
				lDlp7302OK := .T.

			EndIf

		EndIf

	EndIf

Return xRet

