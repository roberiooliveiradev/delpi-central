#INCLUDE "PROTHEUS.CH"


/*/{Protheus.doc} mt380inc

    01 - Solicitacao da Joici para que nao permita movimentacao de "Meia" peça

    @author  Gabriel Araujo
    @since   12-08-2020
/*/


USER FUNCTION MT380INC()
    local aArea    := getarea()
    LOCAL lRet     := .t.
    Local nVlrInt  := 0 // valor sem arredondamento
    Local nVLrOrig := 0 // Valor original da movimentacao
    Local cProdEx  := supergetmv("MV_DLPPRDPC",.F.,"10080755") /// PRODUTO QUE PERMITIRAO QUEBRA DE PEÇA
    Local cPrdAtu  := M->D4_COD
    Local cB1UM    := ALLTRIM(POSICIONE("SB1",1,XFILIAL("SB1")+cPrdAtu,"B1_UM"))

    if !( (cPrdAtu) $  (cProdEx)) .AND. cB1UM $ "PC" .AND. ALLTRIM(UPPER(FUNNAME())) $ "MATA380"

        ///D4_QUANT
        nVLrOrig := M->D4_QUANT
        nVlrInt  := NOROUND(M->D4_QUANT,0)
        IF nVLrOrig!=nVlrInt
            MSGSTOP("Atenção, só é permitida movimentação de Peça Inteira.")
            lRet := .f.
        ENDIF

        nVLrOrig := M->D4_QTDEORI
        nVlrInt  := NOROUND(M->D4_QTDEORI,0)
        IF nVLrOrig!=nVlrInt .AND. lRet
            MSGSTOP("Atenção, só é permitida movimentação de Peça Inteira.")
            lRet := .f.
        ENDIF

    ENDIF

    RESTAREA(aArea)
Return lRet
