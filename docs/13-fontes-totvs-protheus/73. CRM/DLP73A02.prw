#Include 'TOTVS.ch'
#Include 'FWMVCDef.ch'

/*/{Protheus.doc} DLP73A02
Manipula o Model na operação de Réplica (FT300REP)
Copia dados da filial Origem para a filial Destino (Atual) considerando Header e Grids.
Ref: Especificação MIT044 - Tabelas AD1, AD2, AD3, AD4, AD9, ADJ
/*/
User function DLP73A02(oModel)

	// 1. Cópia do Cabeçalho (AD1)
	fCopyHeader(oModel, cOrigFil, cOrigNum)

	// 2. Cópia das Grids (AD2, AD3, AD4, AD9, ADJ)
	// Conforme IDs definidos no FATA300.PRX
	fCopyGrid(oModel, "AD2", "AD2DETAIL", cOrigFil, cOrigNum) // Time de Vendas
	fCopyGrid(oModel, "AD3", "AD3DETAIL", cOrigFil, cOrigNum) // Concorrentes
	fCopyGrid(oModel, "AD4", "AD4DETAIL", cOrigFil, cOrigNum) // Parceiros
	fCopyGrid(oModel, "AD9", "AD9DETAIL", cOrigFil, cOrigNum) // Contatos
	fCopyGrid(oModel, "ADJ", "ADJDETAIL", cOrigFil, cOrigNum) // Produtos

	oView := FwViewActive()
	oView:Refresh()

Return Nil

/*/{Protheus.doc} fCopyHeader
Realiza a cópia do Cabeçalho (AD1) via SQL e aplica regras de negócio
/*/
Static Function fCopyHeader(oModel, cOrigFil, cOrigNum)
	Local oMdlAD1   := oModel:GetModel("AD1MASTER")
	Local cAliasQry := GetNextAlias()
	Local cQuery    := ""
	Local aStruct   := AD1->(DbStruct())
	Local nX        := 0
	Local cCampo    := ""
	Local xValor    := Nil

	// Busca dados da origem
	cQuery := "SELECT * FROM " + RetSqlName("AD1") + " "
	cQuery += "WHERE AD1_FILIAL = '" + cOrigFil + "' "
	cQuery += "AND AD1_NROPOR = '" + cOrigNum + "' "
	cQuery += "AND AD1_REVISA = '" + cOrigRev + "' "
	cQuery += "AND D_E_L_E_T_ = ' ' "

	MPSysOpenQuery(ChangeQuery(cQuery), cAliasQry)

	If (cAliasQry)->(Eof())
		(cAliasQry)->(DbCloseArea())
		Return .F.
	EndIf

	// Popula campos dinamicamente
	For nX := 1 to Len(aStruct)
		cCampo := aStruct[nX][1]

		// Proteções de campos de sistema e chave primária da NOVA oportunidade
		If cCampo $ "AD1_FILIAL|AD1_NROPOR|R_E_C_N_O_|D_E_L_E_T_"
			Loop
		EndIf

		If (cAliasQry)->(FieldPos(cCampo)) > 0
			xValor := (cAliasQry)->&(cCampo)

			If oMdlAD1:GetStruct():HasField(cCampo)
				oMdlAD1:SetValue(cCampo, xValor)
			EndIf
		EndIf
	Next nX

	(cAliasQry)->(DbCloseArea())

	// --- Regras de Negócio (Especificação Pág 3 e 4)
	oMdlAD1:LoadValue("AD1_ZFLORI", cOrigFil) // Filial Origem
	oMdlAD1:LoadValue("AD1_ZOVORI", cOrigNum) // OV Original
	oMdlAD1:LoadValue("AD1_MEMO", cMemo)    // Memo da OV Original
	oMdlAD1:LoadValue("AD1_DATA", Date())    // Data de Inclusão Atual
	oMdlAD1:LoadValue("AD1_HORA", SubString(Time(), 1, 5)) // Hora de Inclusão
	// Status iniciais padrão, se necessário resetar
	// oMdlAD1:LoadValue("AD1_STATUS", "1")

Return Nil

/*/{Protheus.doc} fCopyGrid
Função Genérica para copiar linhas de tabelas filhas (Grids)
/*/
Static Function fCopyGrid(oModel, cTableName, cGridID, cOrigFil, cOrigNum)
	Local oMdlGrid  := oModel:GetModel(cGridID)
	Local cAliasQry := GetNextAlias()
	Local cQuery    := ""
	Local aStruct   := (cTableName)->(DbStruct())
	Local nX        := 0
	Local cCampo    := ""
	Local xValor    := Nil
	Local cPrefix   := cTableName + "_" // Ex: AD2_
	Local lfirstLine := .T.

	// Valida se o modelo da grid existe (pode estar desabilitado por perfil)
	If oMdlGrid == Nil
		Return .F.
	EndIf

	// Busca dados da origem (Filhos)
	cQuery := "SELECT * FROM " + RetSqlName(cTableName) + " "
	cQuery += "WHERE " + cPrefix + "FILIAL = '" + cOrigFil + "' "
	cQuery += "AND " + cPrefix + "NROPOR = '" + cOrigNum + "' "
	cQuery += "AND " + cPrefix + "REVISA = '" + cOrigRev + "' "
	cQuery += "AND D_E_L_E_T_ = ' ' "

	// Ordenação por tabela:
	// AD2 - AD2_FILIAL+AD2_NROPOR+AD2_REVISA+AD2_VEND
	// AD3 - AD3_FILIAL+AD3_NROPOR+AD3_REVISA+AD3_CODCON
	// AD4 - AD4_FILIAL+AD4_NROPOR+AD4_REVISA+AD4_PARTNE
	// AD9 - AD9_FILIAL+AD9_NROPOR+AD9_REVISA+AD9_CODCON
	// ADJ - ADJ_FILIAL+ADJ_NROPOR+ADJ_REVISA+ADJ_ITEM+ADJ_PROD

	Do Case
	Case cTableName == "AD2"
		cQuery += "ORDER BY AD2_FILIAL, AD2_NROPOR, AD2_REVISA, AD2_VEND"
	Case cTableName == "AD3"
		cQuery += "ORDER BY AD3_FILIAL, AD3_NROPOR, AD3_REVISA, AD3_CODCON"
	Case cTableName == "AD4"
		cQuery += "ORDER BY AD4_FILIAL, AD4_NROPOR, AD4_REVISA, AD4_PARTNE"
	Case cTableName == "AD9"
		cQuery += "ORDER BY AD9_FILIAL, AD9_NROPOR, AD9_REVISA, AD9_CODCON"
	Case cTableName == "ADJ"
		cQuery += "ORDER BY ADJ_FILIAL, ADJ_NROPOR, ADJ_REVISA, ADJ_ITEM, ADJ_PROD"
	End Case

	MPSysOpenQuery(ChangeQuery(cQuery), cAliasQry)

	// Itera sobre os registros da origem
	While (cAliasQry)->(!Eof())

		// Adiciona uma nova linha na Grid de Destino

		If !lfirstLine
			oMdlGrid:AddLine()
		EndIf

		// Itera sobre a estrutura para copiar campos
		For nX := 1 to Len(aStruct)
			cCampo := aStruct[nX][1]

			// Ignora Chaves/Controle: FILIAL, NROPOR, REVISA (geralmente controlada pelo pai), RECNO
			If cCampo $ cPrefix + "FILIAL|" + cPrefix + "NROPOR|" + cPrefix + "REVISA|R_E_C_N_O_|D_E_L_E_T_"
				Loop
			EndIf

			If (cAliasQry)->(FieldPos(cCampo)) > 0
				xValor := (cAliasQry)->&(cCampo)

				// Verifica se o campo existe na estrutura do Model (pode ser campo virtual ou removido via PE)
				If oMdlGrid:GetStruct():HasField(cCampo)
					// LoadValue ignora gatilhos de validação pesada, ideal para carga inicial
					oMdlGrid:SetValue(cCampo, xValor)
				EndIf
			EndIf
		Next nX

		lfirstLine := .F.

		(cAliasQry)->(DbSkip())
	EndDo

	(cAliasQry)->(DbCloseArea())

Return Nil
