#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 03/10/2024
/*/
User Function MT110TOK()

	IF INCLUI

		EnviaWF()

	ENDIF

Return .T.

Static function EnviaWF()
	Local oProcess := Nil
	Local cQry := ""

	cQry := " SELECT DISTINCT "+CRLF
	cQry += " CR_APROV, USR_CODIGO, "+CRLF
	cQry += " C1_PRECO, A2_NOME, USR_EMAIL, "+CRLF
	cQry += " C1_NUM, C1_SOLICIT, C1_ITEM, "+CRLF
	cQry += " C1_DESCRI, C1_QUANT, C1_TOTAL, "+CRLF
	cQry += " C1_DATPRF, C1_EMISSAO, C1_OBS "+CRLF
	cQry += " FROM "+RetSqlName("SC1")+" SC1 "+CRLF
	cQry += " INNER JOIN "+RetSqlName("SCR")+" SCR ON "+CRLF
	cQry += " SCR.D_E_L_E_T_ = ' ' AND "+CRLF
	cQry += " SCR.CR_USER = SC1.C1_USER AND "+CRLF
	cQry += " SCR.CR_FILIAL = SC1.C1_FILIAL "+CRLF
	cQry += " LEFT JOIN SYS_USR SYS ON "+CRLF
	cQry += " SCR.CR_APROV = SYS.USR_ID AND "+CRLF
	cQry += " SYS.D_E_L_E_T_ = ' ' "+CRLF
	cQry += " LEFT JOIN "+RetSqlName("SA2")+" SA2 ON "+CRLF
	cQry += " SC1.C1_FORNECE = SA2.A2_COD AND "+CRLF
	cQry += " SC1.C1_LOJA = SA2.A2_LOJA AND "+CRLF
	cQry += " SA2.D_E_L_E_T_ = ' ' "+CRLF
	cQry += " WHERE "+CRLF
	cQry += " SC1.D_E_L_E_T_ = ' ' "+CRLF
	cQry += " AND C1_NUM = "+valtosql(SC1->C1_NUM)+" "+CRLF
	cQry += " ORDER BY C1_ITEM "+CRLF
	cQry := ChangeQuery(cQry)
	dbUseArea( .T.,"TOPCONN", TCGENQRY(,,cQry),'TRBSC1', .F., .T.)

	DbSelectArea('TRBSC1')
	DbGoTop()

	IF (TRBSC1)->(!Eof())

		oProcess := TWFProcess():New("DLP02W02","WFDELPICOMPRAS" )

		oProcess:NewTask("DLP02W01","\WF\DelpiSolicitCompras.html")
		oProcess:cSubject := "WF Aprovacao Solicitação de Compra - Filial " + (TRBSC1)->A2_NOME + " Solicitação " + (TRBSC1)->C1_NUM
		oProcess:cTo      := "pedro.silveira@totvs.com.br" // (TRBSC1)->USR_EMAIL
		oProcess:cBCC     := "gabriel.araujo@totvs.com.br"

		oProcess:oHtml:ValByName("cNumSol" ,(TRBSC1)->C1_NUM )
		oProcess:oHtml:ValByName("cFornece",(TRBSC1)->A2_NOME)
		oProcess:oHtml:ValByName("dDtPrev" ,DTOC(STOD((TRBSC1)->C1_DATPRF )))
		oProcess:oHtml:ValByName("dDtEmiss",DTOC(STOD((TRBSC1)->C1_EMISSAO)))

		oProcess:oHtml:ValByName("cSolici",(TRBSC1)->C1_SOLICIT)
		oProcess:oHtml:ValByName("cObs"   ,(TRBSC1)->C1_OBS    )

		WHILE (TRBSC1)->(!Eof())

			oProcess:oHtml:ValByName("cItem"    ,(TRBSC1)->C1_ITEM)
			oProcess:oHtml:ValByName("cProduto" ,(TRBSC1)->C1_DESCRI)
			oProcess:oHtml:ValByName("nValor"   ,Transform((TRBSC1)->C1_PRECO,"@E 999,999,999.9999"))
			oProcess:oHtml:ValByName("nQuant"   ,Transform((TRBSC1)->C1_QUANT,"@E 999,999,999.9999"))
			oProcess:oHtml:ValByName("nTotal"   ,Transform((TRBSC1)->C1_TOTAL,"@E 999,999,999.9999"))

			(TRBSC1)->(DbSkip())

		ENDDO

		(TRBSC1)->(DbCloseArea())

	ENDIF

	oProcess:Start()
	oProcess:Finish()

return
