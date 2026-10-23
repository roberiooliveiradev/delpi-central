#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
* Validação para não permitir que o estoque fique  *
* negativo pois o MV_ESTNEG foi desabilitado       *
***************************************************/

User Function MT250TOK()        // Verificação de Tipo de Movimentação 501 na Inclução de Produção
	Local aArea :=getarea()
	Local aAreaB2	:= SB2->(GetArea())
	Local nD3Qnt := 0
	Local nB2Qatu := 0
	Local cEol := CHR(10)
	Local cTipo := ""
	lOCAL tVolta := .T.
	Local cMsg :=""
	lOCAL nQtdOri := 0
	/*If M->D3_TM='501' .AND. Empty(M->D3_OP)
		Msgbox("So poderá utilizar tipo de movimentação 501, quando tiver Ordem Produção Cadastrada.")
		tVolta := .F.
	EndIf*/

	IF (ALTERA .OR. INCLUI) .and. cEmpAnt $"01_05"

		IF M->D3_EMISSAO != dDatabase
			tVolta := .F.

			MSGALERT("Não é possivel apontar OP com Emissao Diferente da Database","Delpi")

		ENDIF


		if tVolta .and. (ALTERA .OR. INCLUI) .and. cEmpAnt $"01_05"

			cSql :="SELECT *                                         " + cEol
			cSql +="	FROM dbo." + RETSQLNAME("SD4") + " A (NOLOCK)      " + cEol
			cSql +="WHERE A.D_E_L_E_T_     = ''                      " + cEol
			cSql +="      AND A.D4_FILIAL  = " +VALTOSQL(xFilial("SD4"))+ cEol
			cSql +="      AND A.D4_OP      = " +VALTOSQL(M->D3_OP)  + cEol


			conout(cSql)
			If Select("TRB004") <> 0
				dbSelectArea("TRB004")
				dbCloseArea()
			EndIf

			TCQUERY cSql NEW ALIAS "TRB004"
			nCount := "00"
			While TRB004->(!EOF()) //.and. tVolta

				dbSelectArea("SB2")
				dbSetOrder(1)
				dbSeek( xFilial("SB2") + TRB004->D4_COD+TRB004->D4_LOCAL )

				nB2Qatu := SaldoSB2(.F.,.F.,dDataBase,.t.,.t.) //POSICIONE("SB2",1,XfILIAL("SD3")+TRB004->D4_COD+TRB004->D4_LOCAL,"B2_QATU")
				nB2Qatu2 := SaldoSB2(.F.,.T.,dDataBase,.t.,.t.) //POSICIONE("SB2",1,XfILIAL("SD3")+TRB004->D4_COD+TRB004->D4_LOCAL,"B2_QATU")

				//nB2Qatu := POSICIONE("SB2",1,XfILIAL("SD3")+TRB004->D4_COD+TRB004->D4_LOCAL,"B2_QATU")
				cTipo := posicione("SB1",1,XfILIAL("SB1")+TRB004->D4_COD,"B1_TIPO")

				if M->D3_PARCTOT $ 'P'

					nQtMov  := M->D3_QUANT
					nQtdOri := POSICIONE("SC2",1,XFILIAL("SC2")+ALLTRIM(M->D3_OP),"C2_QUANT")
					nD3Qnt  := ROUND( ( (nQtMov/nQtdOri )* TRB004->D4_QUANT),4)
					//ROUND( (0.010/0.031 )* 279,4)

				ELSE

					nD3Qnt := TRB004->D4_QUANT

				END
				//nD3Qnt := M->D3_QUANT
				//IF nD3Qnt > nB2Qatu .AND. !(cTipo $ "PI")
				IF nD3Qnt > nB2Qatu .AND. !(cTipo $ "PI")

					nCount := soma1(nCOunt)
					//cMsg +="Produto: "+TRB004->D4_COD +" Saldo : "+ cValtoChar(nB2Qatu) + " Qtd Mov " + cValtoChar(nD3Qnt) +cEol
					cMsg +=nCount + " Produto: "+TRB004->D4_COD +" Saldo : "+ cValtoChar(nB2Qatu-nD3Qnt)+cEol
					//	MSGALERT("Quantidade da OP superior ao saldo em estoque."+cEol+"Produto: "+TRB004->D4_COD,"Delpi - MT250TOK")
					//	tVolta := .F.

				endif
				TRB004->(dbSkip())

			enddo

		ENDIF

	ENDIF

	if len(cMsg)>0
		MSGALERT("Quantidade da OP superior ao saldo em estoque."+cEol+cMsg,"Delpi - MT250TOK")
		tVolta := .F.
	endif
	RESTAREA(aArea)
	RESTAREA(aAreaB2)
Return(tVolta)
