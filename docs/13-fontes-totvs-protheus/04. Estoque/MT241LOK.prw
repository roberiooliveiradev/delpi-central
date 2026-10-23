#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"



User Function MT241LOK()
    Local aArea := GetArea()
    Local lRet := .t.
    Local lVldCC  := superGetMv("MV_DVLDCC",.F.,IIF(cEmpAnt $ "01",.T.,.F.))
    Local cDlpPrd  := superGetMv("MV_DLPTPPR",.F.,IIF(cEmpAnt $ "01","MP_PI_PA",""))
    Local cTpProd  :=""
    Local cCCust :=  CCC
    Local lVldMI := .t.

    if !GDDeleted()

        sCod    := GdFieldGet('D3_COD')
        cTpProd := ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_TIPO"))
        lVldMI  := iif( ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_YMI")) =="1",.t.,.f.  )

        IF lVldMI
            If!( !(cTpProd $ cDlpPrd)   )
                IF  empty(cCCust)

                    //if lVldCC .AND. !( cTpProd $ cDlpPrd) .and. empty(cCCust)
                    ApMsgAlert('Centro de Custo Obrigatorio!')
                    lRet := .f.
                endif
            endif
        endif
    endif
    restarea(aArea)
Return lRet
