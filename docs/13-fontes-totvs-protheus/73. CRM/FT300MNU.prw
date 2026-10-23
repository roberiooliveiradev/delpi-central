#INCLUDE "TOTVS.CH"
#INCLUDE "FWMVCDEF.CH"

User Function FT300MNU()
	Local aNewRot := aClone(ParamIXB[01])

	ADD OPTION aNewRot TITLE "Copiar"   ACTION "U_FT300COP" OPERATION OP_COPIA   ACCESS 0
	ADD OPTION aNewRot TITLE "Replicar" ACTION "U_FT300REP" OPERATION OP_COPIA ACCESS 0
Return aNewRot

/*/{Protheus.doc} FT300COP
Copia a oportunidade de venda
/*/
User Function FT300COP()
	Private lCopia     := .T.
	Private cOvOrig    := AD1->AD1_NROPOR
	Private cProspe    := AD1->AD1_PROSPE
	Private cLojPro    := AD1->AD1_LOJPRO
	Private cCodCli    := AD1->AD1_CODCLI
	Private cLojCli    := AD1->AD1_LOJCLI
	Private lDlp7302OK := .F.

	If FWAlertNoYes("Deseja prosseguir com a cópia da oportunidade " + cOvOrig + "?", "Atenção")
		FWExecView("Copiar Oportunidade de venda" , 'FATA300', OP_COPIA,, { || .T. } )

		If lDlp7302OK
			// Copia anexos diretos da Oportunidade (AD1)
			CYBCOCONH(xFilial("AD1"), cOvOrig, xFilial("AD1"), AD1->AD1_NROPOR, "AD1")

			// Copia Notas (AOB) e seus anexos
			CpyNotes(xFilial("AD1"), cOvOrig, xFilial("AD1"), AD1->AD1_NROPOR)
		EndIf
	EndIf
	lCopia := .F.
Return Nil

/*/{Protheus.doc} FT300REP
Replica a oportunidade de venda para outra filial
/*/
User Function FT300REP()
	Local aArea    := GetArea()
	Local cFilBkp  := cFilAnt

	Private cFilDest := Space(FWSizeFilial())
	Private cOrigFil := AD1->AD1_FILIAL
	Private cOrigNum := AD1->AD1_NROPOR
	Private cOrigRev := AD1->AD1_REVISA
	Private cMemo    := MSMM(AD1->AD1_CODMEM, TamSX3("AD1_MEMO")[1])
	Private lDlp7302OK := .F.
	Private lReplica   := .T.
	Private cNumNewOV := ''

	If FWAlertNoYes("Deseja prosseguir com a replicação da oportunidade " + cOrigNum + "?", "Atenção")
		fGetFilDest()

		If Empty(AllTrim(cFilDest))
			RestArea(aArea)
			Return Nil
		EndIf

		If cFilDest != cFilBkp
			cFilAnt := cFilDest
			FWSM0Util():setSM0PositionBycFilAnt()
		EndIf

		FWExecView("Replicar Oportunidade", "FATA300", 3, /*oDlg*/, {|| .T.})

		If cFilDest != cFilBkp
			cFilAnt := cFilBkp
			FWSM0Util():setSM0PositionBycFilAnt()
		EndIf

		If lDlp7302OK
			// Copia anexos diretos da Oportunidade (AD1)
			CYBCOCONH(cOrigFil, cOrigNum, cFilDest, cNumNewOV, "AD1")

			// Copia Notas (AOB) e seus anexos
			CpyNotes(cOrigFil, cOrigNum, cFilDest, cNumNewOV)

			FWAlertInfo("Oportunidade replicada com sucesso para a filial " + cFilDest + ".", "Sucesso")
		EndIf
	EndIf

	RestArea(aArea)
Return Nil

Static Function fGetFilDest()
	Local oDlg, oGet, oBtnConf, oBtnCan
	DEFINE MSDIALOG oDlg TITLE "Selecione Filial Destino" FROM 000,000 TO 120,300 PIXEL
	@ 010, 010 SAY "Filial Destino:" OF oDlg PIXEL
	@ 010, 050 MSGET oGet VAR cFilDest SIZE 060, 010 OF oDlg F3 "SM0" PIXEL VALID vldFilGet() HASBUTTON
	@ 040, 010 BUTTON oBtnConf PROMPT "Confirmar" SIZE 040, 015 OF oDlg PIXEL ACTION oDlg:End()
	@ 040, 060 BUTTON oBtnCan  PROMPT "Cancelar"  SIZE 040, 015 OF oDlg PIXEL ACTION oDlg:end()
	ACTIVATE MSDIALOG oDlg CENTERED
Return

Static function vldFilGet()
Return ExistCpo("SM0", cEmpAnt + cFilDest)

/*/{Protheus.doc} CpyNotes
Copia notas (AOB) e chama replicação de anexos das notas
/*/
Static Function CpyNotes(cFilOrigem, cNumOrigem, cFilDestino, cNumDestino)
	Local cQuery     := ""
	Local cAliasAOB  := GetNextAlias()
	Local oModel     := Nil
	Local cNewID     := ""
	Local cError     := ""
	Local aError     := {}

	Local oStatement := Nil

	cQuery := "SELECT AOB_IDNOTA, AOB_FILIAL "
	cQuery += "FROM " + RetSqlName("AOB") + " "
	cQuery += "WHERE AOB_FILIAL = ? "
	cQuery += "AND AOB_ENTIDA = ? "
	cQuery += "AND AOB_CHAVE = ? "
	cQuery += "AND D_E_L_E_T_ = ' ' "

	oStatement := FwExecStatement():New(cQuery)
	oStatement:SetString(1, xFilial("AOB"))
	oStatement:SetString(2, 'AD1')
	oStatement:SetString(3, cFilOrigem + cNumOrigem)

	cAliasAOB := oStatement:OpenAlias()

	While !(cAliasAOB)->(Eof())

		// Posiciona no registro físico para garantir leitura correta de MEMO e dados completos
		dbSelectArea("AOB")
		AOB->(dbSetOrder(1)) // AOB_FILIAL + AOB_IDNOTA
		If AOB->(dbSeek((cAliasAOB)->AOB_FILIAL + (cAliasAOB)->AOB_IDNOTA))

			oModel := FwLoadModel('CRMA090')
			oModel:SetOperation(MODEL_OPERATION_INSERT)

			If oModel:Activate()
				oModel:SetValue('AOBMASTER', 'AOB_ENTIDA', 'AD1')
				oModel:SetValue('AOBMASTER', 'AOB_CHAVE',  cFilDestino + cNumDestino)
				oModel:SetValue('AOBMASTER', 'AOB_TITULO', AOB->AOB_TITULO)
				oModel:SetValue('AOBMASTER', 'AOB_CONTEU', AOB->AOB_CONTEU) // Conteudo Memo
				oModel:SetValue('AOBMASTER', 'AOB_MSBLQL', AOB->AOB_MSBLQL)
				oModel:SetValue('AOBMASTER', 'AOB_OWNER',  RetCodUsr()) // Assume usuário atual como novo owner

				If oModel:VldData() .And. oModel:CommitData()
					// Recupera o ID gerado para a nova nota
					cNewID := oModel:GetValue('AOBMASTER', 'AOB_IDNOTA')

					// Copia os anexos vinculados à nota antiga para a nova nota
					// AC9_ENTIDA = 'AOB', AC9_CODENT = ID da Nota
					CYBCOCONH(xFilial("AOB"), (cAliasAOB)->AOB_IDNOTA, xFilial("AOB"), cNewID, "AOB")
				Else
					aError := oModel:GetErrorMessage()
					cError := "Erro ao copiar nota: " + AllTrim(AOB->AOB_TITULO)
					If !Empty(aError)
						cError += " - " + AllTrim(aError[5]) + " / " + AllTrim(aError[6])
					Endif
					FWAlertWarning(cError, "Atenção")
				EndIf

				oModel:DeActivate()
			EndIf
			FreeObj(oModel)
		EndIf

		(cAliasAOB)->(dbSkip())
	EndDo

	(cAliasAOB)->(dbCloseArea())
	FreeObj(oStatement)
Return

/*/{Protheus.doc} CYBCOCONH
Função para copiar banco de conhecimento (Genérica)
@param cEntidade: Entidade do anexo (ex: AD1 ou AOB). Default: AD1
/*/
Static Function CYBCOCONH(cFilOrigem, cEntiOrigem, cFilDestino, cEntiDestino, cEntidade)
	Local aArea       := GetArea()
	Local cObj        := ""
	Local cDescri     := ""
	Local cNewCodObj  := ""
	Local cFilAC9     := xFilial("AC9", cFilDestino)
	Local cFilACB     := xFilial("ACB", cFilDestino) // Considera filial destino para ACB
	Local cAliasQry   := ""
	Local cFilq       := xFilial("AC9", cFilOrigem)
	Local lNewReg     := .T.
	Local cQuery      := ""
	Local oStatement  := Nil
	Local nParamOrder := 1

	Default cEntidade := "AD1"

	cQuery += "SELECT AC9.AC9_FILIAL, AC9.AC9_CODOBJ "
	cQuery += "FROM " + RetSqlName('AC9') + " AC9 "
	cQuery += "WHERE AC9.AC9_FILIAL = ? "
	cQuery +=   "AND AC9.AC9_ENTIDA = ? "
	cQuery +=   "AND AC9.AC9_FILENT = ? "
	cQuery +=   "AND AC9.AC9_CODENT = ? "
	cQuery +=   "AND AC9.D_E_L_E_T_ = ' ' "

	cQuery := ChangeQuery(cQuery)

	oStatement := FwExecStatement():New(cQuery)

	oStatement:SetString(nParamOrder++, cFilq)
	oStatement:SetString(nParamOrder++, cEntidade)
	oStatement:SetString(nParamOrder++, cFilOrigem)
	oStatement:SetString(nParamOrder++, cEntiOrigem)

	cAliasQry := oStatement:OpenAlias()

	While !(cAliasQry)->(Eof())

		dbSelectArea("ACB")
		ACB->(dbSetOrder(1))

		// Busca objeto original
		If ACB->(dbSeek((cAliasQry)->AC9_FILIAL + (cAliasQry)->AC9_CODOBJ))
			cObj    := ACB->ACB_OBJETO
			cDescri := ACB->ACB_DESCRI

			cNewCodObj := GetSXENum("ACB", "ACB_CODOBJ")

			ACB->(DbSetOrder(1))
			If !ACB->(DbSeek(cFilACB + cNewCodObj))
				ConfirmSx8()
			Else
				RollBackSX8()
				While ACB->(DbSeek(cFilACB + cNewCodObj))
					cNewCodObj := Soma1(cNewCodObj)
				EndDo
			EndIf

			If RecLock("ACB", .T.)
				ACB->ACB_FILIAL := cFilACB
				ACB->ACB_CODOBJ := cNewCodObj
				ACB->ACB_OBJETO := cObj
				ACB->ACB_DESCRI := cDescri
				ACB->(msUnlock())

				AC9->(DbSetOrder(1)) // AC9_FILIAL+AC9_CODOBJ+AC9_ENTIDA+AC9_FILENT+AC9_CODENT
				lNewReg := !(AC9->(DbSeek(cFilAC9 + cNewCodObj + cEntidade + cFilDestino + cEntiDestino)))

				If RecLock("AC9", lNewReg)
					AC9->AC9_FILIAL := cFilAC9
					AC9->AC9_FILENT := cFilDestino
					AC9->AC9_ENTIDA := cEntidade
					AC9->AC9_CODENT := cEntiDestino
					AC9->AC9_CODOBJ := cNewCodObj
					AC9->(msUnlock())
				EndIf
			EndIf
		EndIf
		(cAliasQry)->(dbSkip())
	EndDo

	(cAliasQry)->(dbCloseArea())
	FreeObj(oStatement)
	RestArea(aArea)
Return
