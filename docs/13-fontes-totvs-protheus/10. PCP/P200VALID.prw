#Include "Totvs.ch"

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 10/01/2025
*/
User Function P200VALID()
	Local oModel := ParamixB[1]  //Modelo Principal (Mestre)
	// Local oDados := ParamixB[2]  //Objeto Json com todas as alterações realizadas na estrutura
	Local lRet   := .T.
/*
    oDados                                     -> Json com as alterações
    oDados["oLinDel"]                          -> Json com as linhas que foram alteradas (indicando se foi excluída)
    oDados["oLinDel"][<Pai+Comp+Trt>]          -> Se estiver como .T., indica que o componente foi removido durante a execução
    oDados["oLines" ]                          -> Json com as linhas que foram alteradas (com os novos valores que serão gravados)
    oDados["oLines" ][<Pai+Comp+Trt>]          -> Array com os valores que serão salvos em cada campo do campo do cadastro (as posições devem ser resgatadas através do oDados["oFields"])
    oDados["oLines" ][<Pai+Comp+Trt>][<Field>] -> Novo valor para o campo (se não foi alterado, retornará o valor atual)
    oDados["oFields"]                          -> Json com os campos do cadastro para buscar seus respectivos índices do array contido em oDados["oLines"]
    oDados["oFields"][<Field>]                 -> Índice do campo (Field) no array das alterações (oDados["oLines"])
*/
  lRet := fVldAps(oModel)

Return lRet

/*/{Protheus.doc} nomeStaticFunction
  (long_description)
  @type  Static Function
  @author Pedro Lindenberg
  @since 10/01/2025
/*/
Static Function fVldAps(oModel)
	Local lRet := .T.
	Local aDataTb := OMODEL:AALLSUBMODELS[3]:ACOLS
	Local cProd2 := ""
	Local x1 := 0
	Local lApsInUse  := SuperGetMv("MV_APS",.F.,"") $ "DRUMMER*TOTVS"
	Local nQtdEst := 0
	Local cBzMrp := ""
	Local cQry := ""

	IF lApsInUse

		for x1 := 1 to len(aDataTb)

			cProd2 := aDataTb[x1][3]

			cQry := " SELECT COUNT(*) AS HAVEEST " + CRLF
			cQry += " FROM  "+RetSqlName("SG1")+" SG1 " + CRLF
			cQry += " WHERE SG1.D_E_L_E_T_ = ' ' " + CRLF
			cQry += " AND SG1.G1_COD = "+VALTOSQL(cProd2)+""
			nQtdEst := MpSysExecScalar(cQry,"HAVEEST")

			IF nQtdEst > 0

				cBzMrp := POSICIONE("SBZ",1,xFilial("SBZ")+cProd2,"BZ_MRP")

				IF cBzMrp != "S"

					FWAlertWarning("Não é permitida a inclusão/alteração da Estrutura do Produto: "+ALLTRIM(cProd2)+" - Deve estar habilitado para integração com o APS","Delpi - PCP - APS")
					lret := .F.
					Exit

				ENDIF

			ENDIF

		next x1

	ENDIF

Return lRet
