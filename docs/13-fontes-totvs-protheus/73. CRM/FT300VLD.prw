#INCLUDE "FWMVCDEF.CH"
#Include 'PROTHEUS.CH'

User Function FT300VLD()

    Local oModel         := PARAMIXB[1]
    Local oMdlAD1      := oModel:GetModel("AD1MASTER")
    Local oMdlADJ      := oModel:GetModel("ADJDETAIL")
    Local nOper    := oModel:GetOperation()
    Local lRet              := .T.
    lOCAL nVlrPrv := 0.00
    Local nI

    If nOper == MODEL_OPERATION_INSERT .or. nOper == MODEL_OPERATION_UPDATE
        If AD1->(FieldPos("AD1_ZPRVND"))<>0  .AND. ADJ->(FieldPos("ADJ_ZPRVND"))<>0
            For nI := 1 To oMdlADJ:Length()
                oMdlADJ:GOLINE(nI)
                If !oMdlADJ:IsDeleted()

                    nVlrPrv += oMdlADJ:GETVALUE("ADJ_ZPRVND") * oMdlADJ:GETVALUE("ADJ_PRUNIT")

                EndIf
            next nI
            oMdlAD1:SetValue("AD1_ZPRVND",  ROUND(nVlrPrv,2))
        EndIf
    EndIf
Return( lRet )
