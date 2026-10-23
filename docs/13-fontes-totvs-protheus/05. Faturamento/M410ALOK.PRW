#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"


USER FUNCTION M410ALOK()
    LOCAL lRet := .t.

    Local lVldCC  := superGetMv("MV_DVLDCC",.F.,IIF(cEmpAnt $ "01",.T.,.F.))
    Local cDlpPrd  := superGetMv("MV_DLPTPPR",.F.,IIF(cEmpAnt $ "01","MP_PI_PA",""))
    Local cTpProd  :=""
    Local cCCust :=  GdFieldGet('C6_CCUSTO')

   /* if !GDDeleted()

        sCod    := GdFieldGet('C6_PRODUTO')
        cTpProd := ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_TIPO"))

    if lVldCC .AND. !( cTpProd $ cDlpPrd) .and. empty(cCCust)
            ApMsgAlert('Centro de Custo Obrigatorio!')
            lRet := .f.
    endif

endif*/
Return lRet