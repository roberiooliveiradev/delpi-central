#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
* Validação para não permitir que o estoque fique  *
* negativo pois o MV_ESTNEG foi desabilitado       *
* PE Movimento Interno                             *
***************************************************/
User Function MT241TOK()
    Local aArea := GetArea()
    Local lRet := .t.
    Local cProd := ""
    Local cLocal := ""
    Local nD3Qnt := 0
    Local nB2Qatu := 0
    Local cEol := chr(10)
    Local cUsrper := ALLTRIM(superGetMv("MV_YPERTM",.F.,"000008"))

    if ( cTM == "100" .and. (!FWIsAdmin() .AND. !(RETCODUSR() $ cUsrper )  ))

        lRet := .f.

        msgstop("Sem permissão para utilizar o tipo de movimentação "+ cTM,"Usuario sem permissão")

    endif

    dbselectarea("SF5")
    DBSETORDER(1)
    IF SF5->(MsSeek(xFilial("SF5")+cTM)) .and. lRet
        if SF5->F5_TIPO $ "R"
            For nY := 1 To Len( aCols)
                IF !(GDDeleted(nY,aHeader,aCols)) .and. !("MOD" $ GDFieldGet('D3_COD',nY,,,aCols))
                    cProd := GDFieldGet('D3_COD',nY,,,aCols)
                    cLocal := GDFieldGet('D3_LOCAL',nY,,,aCols)
                    nD3Qnt := GDFieldGet('D3_QUANT',nY,,,aCols)
                    //B2_FILIAL, B2_COD, B2_LOCAL, R_E_C_N_O_, D_E_L_E_T_
                    nB2Qatu := POSICIONE("SB2",1,XfILIAL("SD3")+cProd+cLocal,"B2_QATU")
                    IF nD3Qnt > nB2Qatu
                        conout("MT241TOK Quantidade do Movimento superior ao saldo em estoque"+cEol+"Produto: " + cProd ,"Delpi")

                        MSGALERT("Quantidade do Movimento superior ao saldo em estoque"+cEol+"Produto: " + cProd ,"Delpi")
                        lRet := .F.

                    endif
                endif
            next nY

        endif
    endif


    restarea(aArea)
Return lRet

