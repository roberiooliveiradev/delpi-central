#Include "Protheus.ch"
#Include "Topconn.ch"
#INCLUDE "FWEVENTVIEWCONSTS.CH"

User Function MA330OK()
    Local lRet     := .T.
    Local aArray   := Array(2)
    Local cEol     := chr(10)

    Local cMessage := "Texto personalizado do ponto de entrada que será gravado nos logs de processamento."
    //dInicio
    if cEmpAnt =="01"
        cMessage :=   "Chamou a Procedure que ajusta movimentos de terceiro" +cEol
        cMessage += "Empresa "+  cEmpAnt +cEol
        cMessage += "Dt Inicio  "+  dtoc(dInicio)
        aArray[1] := lRet
        aArray[2] := cMessage
        cQuery := "EXEC [dbo].[STP_DELPI_OP_TERCEIRO_"+cEmpAnt+"]  @DATADE = "+valtosql( dInicio)
        TCSQLExec(cQuery)

        EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, "Z22",FW_EV_LEVEL_INFO,"","MA330OK + STP_DELPI_OP_TERCEIRO_",cMessage,.T.)

        cDtSP := substr(dtos(dInicio),1,6)
        conout(cDtSP)
        cUpd := "EXEC dbo.STP_PROTHEUS_DELPI_AJUSTA_OP "
        cUpd += "   @FILIAL = "+valtosql("01")
        cUpd += "   , @ANOMES = "+valtosql( cDtSP)

        TCSqlExec(cUpd)

        cDtSP := substr(dtos(dInicio),1,6)
        cUpd := "EXEC dbo.STP_PROTHEUS_DELPI_AJUSTA_OP "
        cUpd += "   @FILIAL = "+valtosql("02")
        cUpd += "   , @ANOMES = "+valtosql( cDtSP)

        TCSqlExec(cUpd)
        //-- Validações Adicionais do usuário
    endif
Return aArray
