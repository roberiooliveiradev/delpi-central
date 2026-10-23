#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 02/05/01
#INCLUDE "TOPCONN.CH"

/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ DLP007   ¦ Autor ¦ MARCIO DA SILVA       ¦ Data ¦ 22/06/07 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ EXPORTACAO DE NOTAS FISCAIS PARA WEG                       ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/
User Function DLP007()        // incluido pelo assistente de conversao do AP5 IDE em 02/05/01


	cPerg := "DLP007"
	Local cMsg :=""
	Local cEol := chr(10)

	iF pergunte(cperg,.T.)
		/*cQuery := "SELECT D2_DOC,D2_SERIE,C5_PEDCLI,C6_ITEMWEG,D2_ALMOX,D2_UM,D2_QUANT FROM "
	cQuery += RetSqlName("SD2") + " SD2, "+RetSqlName("SC6") + " SC6, "+RetSqlName("SC5") + " SC5 "
	cQuery += " WHERE D2_DOC = '"+mv_par01+"' AND D2_SERIE= '"+MV_PAR02+"' "
	cQuery += " AND D2_PEDIDO =C6_NUM  AND D2_ITEMPV = C6_ITEM   AND C5_NUM = C6_NUM "
	cQuery += " ORDER BY D2_DOC,D2_ITEMPV "

		TCQUERY cQuery NEW ALIAS "TRBSD2"*/

		If (Select("TRBSD2") <> 0)
			DbSelectArea("TRBSD2")
			DbCloseArea()
		EndIf

		BeginSql Alias 'TRBSD2
			SELECT
				D2_SERIE,
				D2_DOC,
				D2_ALMOX,
				D2_UM,
				D2_QUANT,
				C6_ITEMWEG,
				C5_PEDCLI
			FROM
				%Table:SF2% F2
			INNER JOIN %Table:SD2% D2
			ON D2.%NotDel%
				AND D2_FILIAL = %xFilial:SD2%
				AND D2_SERIE = F2_SERIE
				AND D2_DOC = F2_DOC
				AND D2_CLIENTE = F2_CLIENTE
				AND D2_LOJA = F2_LOJA
			INNER JOIN %Table:SC6% C6
			ON C6.%NotDel%
				AND C6_FILIAL = %xFilial:SC6%
				AND C6_NUM = D2_PEDIDO
				AND C6_ITEM = D2_ITEMPV
			INNER JOIN %Table:SC5% C5
			ON C5.%NotDel%
				AND C5_FILIAL = %xFilial:SC5%
				AND C5_NUM = C6_NUM
			WHERE
				F2.%NotDel%
				AND F2_FILIAL = %xFilial:SF2%
				AND F2_SERIE = %Exp:MV_PAR03%
				AND F2_DOC BETWEEN %Exp:MV_PAR01% and %Exp:MV_PAR02%
			GROUP BY
				D2_SERIE,
				D2_DOC,
				D2_ALMOX,
				D2_UM,
				D2_QUANT,
				C6_ITEMWEG,
				C5_PEDCLI
			Order by
				1,
				2
		EndSql

		If	TRBSD2->(Eof()) .And. TRBSD2->(Bof())
			Alert("Não foram encontradas informações para Geração do Arquivo para WEG, da Nota/Serie Informada !!!")
			Return
		EndIf

		DbGoTop()
		tAchou := .F.
		sCl     := chr(13) + CHR(10)

		cDocAtu := ""
		nCount :=0
		cMsg :=""
		While !(TRBSD2->(Eof()))
			if cDocAtu != TRBSD2->D2_DOC
				if nCount >0
					cMsg +="NF "+cDocAtu+" Qtd Linhas: "+cValtochar(nCount)+cEol
				endif
				nCount :=0
				sNomeArq:="\WEG-ONLINE\"+alltrim(XFILIAL("SF2"))+'-'+alltrim(TRBSD2->D2_DOC)+".TXT"   //arquivo a gerar texto
				If File(sNomeArq)
					//	if  FWAlertYesNo("Arquivo "+sNomeArq+" já existe, deseja sobrescrever?","Delpi - Arquivo WEG")
					Ferase(sNomeArq)

					//	Endif
				Endif
				sHandle:=MsFCreate(SNomeArq)
				//FWrite(sHandle,sGrava,len(sGrava))
				//sGrava:='H'+TRBSD2->D2_DOC+'-'+Alltrim(TRBSD2->D2_SERIE) + sCl
				sGrava:='H'+alltrim(TRBSD2->D2_DOC)+'-'+cvaltochar(val ( TRBSD2->D2_SERIE)) + sCl
				FWrite(sHandle,sGrava,len(sGrava))
				cDocAtu := TRBSD2->D2_DOC

			Endif
			nCount++
			sGrava:="F"+Repl("0",10-Len(Alltrim(TRBSD2->C5_PEDCLI)))+Left(Alltrim(TRBSD2->C5_PEDCLI),10)
			sGrava+=","+StrZero(Val(TRBSD2->C6_ITEMWEG),5)+","+TRBSD2->D2_ALMOX
			sGrava+=","+iiF(TRBSD2->D2_UM=="MI","MIL",TRBSD2->D2_UM+" ")
			sGrava+=","+StrZero(TRBSD2->D2_QUANT*1000,11)+sCl
			FWrite(sHandle,sGrava,len(sGrava))

			TRBSD2->(dbskip())
			tAchou := .T.
			if cDocAtu != TRBSD2->D2_DOC
				FClose(sHandle)
			endif
		EndDo

		If !tAchou
			MSgbox("Documento Nao Encontrado. Arquivo Nao Gerado!")
			Return
		else
			//    EEcView(cMsgErroPrd, "Itens Com Problemas no Custo")
			EEcView(cMsg, "Geração de Arquivo")
		EndIf
		//MSgbox("Arquivo Gerado Com Sucesso!")
	EndIf

Return
