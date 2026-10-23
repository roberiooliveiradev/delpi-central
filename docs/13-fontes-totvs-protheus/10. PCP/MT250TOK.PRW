#Include 'Protheus.ch'
#INCLUDE 'TOPCONN.CH'
#INCLUDE "TBICONN.CH"


USER FUNCTION MT250TOK()
    Local lRet := .t.
    Local nB2Qatu := 0
    Local nD3Qnt := 0

    IF (ALTERA .OR. INCLUI) .and. cEmpAnt $"01"
        IF M->D3_EMISSAO != dDatabase
            lRet := .F.

            MSGALERT("Não é possivel apontar OP com Emissao Diferente da Database","Delpi")

        ENDIF
    ENDIF


    //if lRet
    //
    //    nD3Qnt := M->D3_QUANT
    //    //B2_FILIAL, B2_COD, B2_LOCAL, R_E_C_N_O_, D_E_L_E_T_
    //    nB2Qatu := POSICIONE("SB2",1,XfILIAL("SD3")+M->D3_COD+M->D3_LOCAL,"B2_QATU")
    //
    //    IF nD3Qnt > nB2Qatu
    //
    //        MSGALERT("Quantidade da OP superior ao saldo em estoque","Delpi")
    //        lRet := .F.
    //
    //    endif
    //
    //endif

RETURN lRet