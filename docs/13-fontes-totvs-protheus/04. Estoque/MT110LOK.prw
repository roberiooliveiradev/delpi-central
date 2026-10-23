#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
* Validação para não permitir que o estoque fique  *
* negativo pois o MV_ESTNEG foi desabilitado       *
* Solicitação de Compras                           *
***************************************************/


User Function MT110LOK()

    Local lRet     := .t.
    Local lVldCC   := superGetMv("MV_DVLDCC",.F.,IIF(cEmpAnt $ "01_05",.T.,.F.))
    Local cDlpPrd  := superGetMv("MV_DLPTPPR",.F.,IIF(cEmpAnt $ "01_05","MP_PI_PA",""))
    Local cTpProd  :=""
    Local cCCust   :=  GdFieldGet('C1_CC')
    Local lVldSC   := .t.

    if !GDDeleted()

        sCod    := GdFieldGet('C1_PRODUTO')
        cTpProd := ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_TIPO"))
        lVldSC := iif( ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_YSC")) =="1",.t.,.f.  )
        //  if lVldCC .AND. !( cTpProd $ cDlpPrd) .and. empty(cCCust)
        If( !(cTpProd $ cDlpPrd) .and. lVldSC ) .and. empty(cCCust)
            ApMsgAlert('Centro de Custo Obrigatorio!')
            lRet := .f.
        endif
    endif
Return lRet
