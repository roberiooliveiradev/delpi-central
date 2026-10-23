#Include 'TOTVS.ch'
#Include 'FWMVCDef.ch'

/*/{Protheus.doc} DLP73A01
Manipula o Model na operação de Cópia (FT300COP)
/*/
User function DLP73A01(oModel, nOperation)
	Local oMdlAD1  := oModel:GetModel("AD1MASTER")

	// Regras Especificas da COPIA
	// A operacao 3 (Inclusao) eh assumida pois o FWExecView de copia inicia um insert
	If nOperation == MODEL_OPERATION_INSERT

		// De-Para: Origem -> Destino
		oMdlAD1:LoadValue("AD1_ZOVORI", cOvOrig)
		oMdlAD1:LoadValue("AD1_PROSPE", cProspe)
		oMdlAD1:LoadValue("AD1_LOJPRO", cLojPro)
		oMdlAD1:LoadValue("AD1_CODCLI", cCodCli)
		oMdlAD1:LoadValue("AD1_LOJCLI", cLojCli)

		// Limpeza de campos conforme especificacao
		oMdlAD1:LoadValue("AD1_PROVEN", "")
		oMdlAD1:LoadValue("AD1_STAGE" , "")
		oMdlAD1:LoadValue("AD1_ZEMBES", "")
		oMdlAD1:LoadValue("AD1_ZDEMBE", "")
		oMdlAD1:LoadValue("AD1_ZCERTI", "")
		oMdlAD1:LoadValue("AD1_ZDCERT", "")
		oMdlAD1:LoadValue("AD1_ZCOMSI", "")
		oMdlAD1:LoadValue("AD1_ZDCOMS", "")
		oMdlAD1:LoadValue("AD1_ZAMOST", "")
		oMdlAD1:LoadValue("AD1_ZENGEN", "")
		oMdlAD1:LoadValue("AD1_MEMO"  , "")
		oMdlAD1:LoadValue("AD1_PRIOR" , "")

		oView := FwViewActive()
		oView:Refresh()

	Endif

Return Nil
