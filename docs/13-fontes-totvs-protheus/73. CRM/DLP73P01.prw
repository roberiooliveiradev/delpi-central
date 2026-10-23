#Include 'TOTVS.ch'
#include "fweventviewconsts.ch"
#Include 'FWMVCDef.ch'

/*/{Protheus.doc} DLP73P01
Dispara eventos de acordo com a alteração do estágio da oportunidade de venda
@param  oModel  - Modelo da oportunidade de venda FATA300
@author  Johnni Moraes
@since   03/12/2025
/*/
User Function DLP73P01(oModel, cProVenOld, cEstagioOld)

	Local oMdlAD1 := Nil
	Local nOperation := 0
	Local cProVen := ""
	Local cEstagio := ""

	nOperation := oModel:GetOperation()

	If nOperation == MODEL_OPERATION_UPDATE .Or. nOperation == MODEL_OPERATION_INSERT

		oMdlAD1 := oModel:GetModel("AD1MASTER")
		cProVen := oMdlAD1:GetValue("AD1_PROVEN")
		cEstagio := oMdlAD1:GetValue("AD1_STAGE")

		If cProVen $ "000002/000003" .And. (AllTrim(cProVen) != AllTrim(cProVenOld) .Or. AllTrim(cEstagio) != AllTrim(cEstagioOld))

			Do Case

			Case cEstagio $ "000001/000005/000006/000010/000011/000013"
				sndEvent("Z05")

			Case cEstagio $ "000002/000004"
				sndEvent("Z06")

			Case cEstagio $ "000003/000008/000012"
				sndEvent("Z07")

			Case cEstagio == "000007"
				sndEvent("Z08")

			Case cEstagio == "000009"
				sndEvent("Z09")

			EndCase
		EndIf

	EndIf

Return Nil

Static Function sndEvent(cEvCode)

	Local cTitulo := "OV " + AD1->AD1_NROPOR + " com estágio alterado."
	Local cMsg := "Realize a análise da OV " + AD1->AD1_NROPOR + " na rotina Oportunidade de Vendas."

	EventInsert( FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEvCode, FW_EV_LEVEL_INFO, "", cTitulo, cMsg, .T.)

Return
