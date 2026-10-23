#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"

USER FUNCTION DLP73G01()

    lOCAL nRet    := 0.00
    Local cCodPro := FWFldGet("ADZ_PRODUT")
    Local cOpor   := FWFldGet("ADY_OPORTU")
    Local oView			:= FWViewActive()
    Local oModel		:= FwModelActive()
    Local oMdlPrd		:= oModel:GetModel("ADZPRODUTO")


    dbselectarea("SZ8")
    SZ8->(dbSetOrder(2))
    IF    SZ8->(MsSeek(xFilial("SZ8")+cOpor+cCodPro))
        conout("teste")
        nRet := ROUND(SZ8->Z8_PVSUGER,2)

    endif


    oMdlPrd:GoLine(oMdlPrd:getline())
    oMdlPrd:SetValue("ADZ_PRCVEN", nRet)
    oMdlPrd:SetValue("ADZ_PRCTAB", nRet)
    If !( oMdlPrd:IsEmpty() ) .AND. !IsBlind()
        oView:Refresh('ADZPRODUTO')
        oView:Refresh('ADZACESSOR')
        oView:Refresh('CRONOFIN')
    EndIf

    // "80011855       "
    // "80011856       "
Return nRet
