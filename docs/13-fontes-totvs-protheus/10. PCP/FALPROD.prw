#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 04/12/2024
/*/
User Function FALPROD()

	RpcSetEnv('01')

	Local cAlias := GetNextAlias()
	Local oModel := Nil
	Private lMsErroAuto := .F.

	DBSELECTAREA("SB1")

	If Select(cAlias) <> 0
		(cAlias)->(DbCloseArea())
	EndIf

	BeginSql alias cAlias
  %noparser%
  SELECT DISTINCT
              D3_COD,
              B1_DESC,
              B1_TIPO,
              ISNULL(BZ_COD, 'NÃO EXISTE SBZ') [SBZ],
              BZ_MRP,
              B1_LOCPAD
  FROM dbo.SD3010 (NOLOCK) TBL1
    JOIN SB1010 (NOLOCK)     SB1
        ON SB1.D_E_L_E_T_ = ''
          AND B1_COD = D3_COD
    LEFT JOIN SBZ010 (NOLOCK)     SBZ
        ON SBZ.D_E_L_E_T_ = ''
          AND B1_COD = BZ_COD
          AND BZ_FILIAL = '02'
    WHERE
          TBL1.D_E_L_E_T_ = ''
          AND TBL1.D3_FILIAL = '02'
          AND B1_TIPO = 'PI'
          AND BZ_COD IS NULL
	EndSql

	While (cAlias)->(!EOF())
		//Posiciona
		SB1->(DbSetOrder(1))
		If SB1->(DbSeek(xFilial("SB1")+ALLTRIM((cAlias)->D3_COD)))

			oModel := FwLoadModel("MATA019")
			oModel:SetOperation(4)
			oModel:Activate()
			oModel:SetValue("SBZDETAIL","BZ_FILIAL","02")
			oModel:SetValue("SBZDETAIL","BZ_LOCPAD",(cAlias)->B1_LOCPAD)
			oModel:SetValue("SBZDETAIL","BZ_MRP","S")
			oModel:SetValue("SBZDETAIL","BZ_LE",0.010)

			If oModel:VldData()

				oModel:CommitData()

			Else
				VarInfo("",oModel:GetErrorMessage())
			EndIf

			oModel:DeActivate()

		EndIf

		(cAlias)->(DbSkip())
	EndDo

	(cAlias)->(DbCloseArea())

	RpcClearEnv()

Return
