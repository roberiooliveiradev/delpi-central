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

    Local nD3Qnt := 0
    Local nB2Qatu := 0
    Local tVolta := .T.
    Local lVldCC  := superGetMv("MV_DVLDCC",.F.,IIF(cEmpAnt $ "01",.T.,.F.))
    Local cDlpPrd  := superGetMv("MV_DLPTPPR",.F.,IIF(cEmpAnt $ "01","MP_PI_PA",""))
    Local cTpProd  :=""
    Local cCCust :=  M->D3_CC
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
		nD3Qnt := M->D3_QUANT
		//B2_FILIAL, B2_COD, B2_LOCAL, R_E_C_N_O_, D_E_L_E_T_
		nB2Qatu := POSICIONE("SB2",1,XfILIAL("SD3")+M->D3_COD+M->D3_LOCAL,"B2_QATU")

        IF nD3Qnt > nB2Qatu

            MSGALERT("Quantidade da OP superior ao saldo em estoque","Delpi - MT240TOK")
            
			tVolta := .F. 
			
        endif
    endif
    
    IF tVolta

    sCod    := M->D3_COD
    cTpProd := ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_TIPO"))

        if lVldCC .AND. !( cTpProd $ cDlpPrd) .and. empty(cCCust) .AND. !GDDeleted()
        ApMsgAlert('Centro de Custo Obrigatorio!')
        lRet := .f.
        endif

    endif
Return(tVolta)