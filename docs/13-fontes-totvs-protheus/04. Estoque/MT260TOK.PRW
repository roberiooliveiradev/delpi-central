#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
* Validação para não permitir que o estoque fique  *
* negativo pois o MV_ESTNEG foi desabilitado       *
* PE Transferencia entre armazens                  *
***************************************************/
User Function  MT260TOK()
	Local lRet := .t.
	Local nD3Qnt , nB2Qatu := 0

	if  cEmpAnt $"01_05"
		nD3Qnt := NQUANT260
		//B2_FILIAL, B2_COD, B2_LOCAL, R_E_C_N_O_, D_E_L_E_T_
		nB2Qatu := POSICIONE("SB2",1,XfILIAL("SD3")+CCODORIG+CLOCORIG,"B2_QATU")

		IF nD3Qnt > nB2Qatu

			MSGALERT("Quantidade da Transferencia superior ao saldo em estoque","Delpi")
			lRet := .F.

		endif
	endif

Return lRet

