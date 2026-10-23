#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/*/{Protheus.doc} MT240TOK
Descrição:
LOCALIZAÇÃO   :  Na função A240TudoOK (rotina de validação da inclusão do movimento).
EM QUE PONTO :  Encontra-se no FINAL da função de validação da inclusão e pode ser usado para validar a inclusão do movimento pelo usuário.

Programa Fonte MATA240.PRX
MT240TOK - Valida inclusão do movimento ( ) --> lRet
Retorno lRet(logico)
Caso retorne verdadeiro, prossegue com o movimento.
Caso retorne falso, abandona o movimento.
@type User Function
@author Gabriel
@since 25/09/2019
/*/
USER Function MT240TOK()
    Local aArea := GetArea()
    Local nD3Qnt := 0
    Local nB2Qatu := 0
    Local tVolta := .T.
    Local lVldCC  := superGetMv("MV_DVLDCC",.F.,IIF(cEmpAnt $ "01",.T.,.F.))
    Local cDlpPrd  := superGetMv("MV_DLPTPPR",.F.,IIF(cEmpAnt $ "01","MP_PI_PA",""))
    Local cTpProd  :=""
    Local cCCust :=  M->D3_CC
    Local lVldMI := .t.
    Local cUsrper := ALLTRIM(superGetMv("MV_YPERTM",.F.,"000008"))

    /* COMENTADO POR GABRIEL EM 09/2019
    ALINHADO COM A JOICI POIS ESSA REGRA NAO EXISTE MAIS
    If M->D3_TM='501' .AND. Empty(M->D3_OP)
            Msgbox("So poderá utilizar tipo de movimentação 501, quando tiver Ordem Produção Cadastrada.")
            tVolta := .F.
    EndIf*/
    /***************************************************
	* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
	* Validação para não permitir que o estoque fique  *
	* negativo pois o MV_ESTNEG foi desabilitado       *
    ***************************************************/
    if tVolta .and. cEmpAnt $ "01"
        cTm   := M->D3_TM
        cTipo := ALLTRIM( posicione("SF5",1,XFILIAL("SF5")+cTm,"F5_TIPO" ) )
        IF cTipo $ "R"

            nD3Qnt := M->D3_QUANT
            //B2_FILIAL, B2_COD, B2_LOCAL, R_E_C_N_O_, D_E_L_E_T_
            nB2Qatu := POSICIONE("SB2",1,XfILIAL("SD3")+M->D3_COD+M->D3_LOCAL,"B2_QATU")
            IF nD3Qnt > nB2Qatu

                MSGALERT("Quantidade da OP superior ao saldo em estoque","Delpi - MT240TOK")

                tVolta := .F.

            endif
        endif
    endif

    IF tVolta .and. cEmpAnt $ "01"

        sCod    := M->D3_COD
        cTpProd := ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_TIPO"))
        lVldMI  := iif( ALLTRIM(  posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_YMI") ) == "1",.t.,.f.  )
        //if lVldCC .AND. !( cTpProd $ cDlpPrd) .and. empty(cCCust)
        if lVldMI
            If !(cTpProd $ cDlpPrd)
                IF  empty(cCCust)

                    // If!( (cTpProd $ cDlpPrd) .or. lVldMI ) .and. empty(cCCust)
                    ApMsgAlert('Centro de Custo Obrigatorio!')
                    tVolta := .f.
                endif
            endif
        endif
    endif

    cTm   := M->D3_TM
    if  tVolta .and. cEmpAnt $ "01" .and.( cTM == "100" .and. (!FWIsAdmin() .AND. !(RETCODUSR() $ cUsrper )  ))

        tVolta := .f.

        msgstop("Sem permissão para utilizar o tipo de movimentação "+ cTM,"Usuario sem permissão")

    endif
    //   IF tVolta .AND. cTipo $ "R"
    //
    //       FWMsgRun( ,{||  U_DLF01F01("MATA240")},"Processando...")
    //
    //   endif
    restarea(aArea)
Return(tVolta)
