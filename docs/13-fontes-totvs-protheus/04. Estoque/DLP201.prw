#Include "rwmake.ch"
#Include "topconn.ch"

User Function DLP201()
	Aviso("Controle de Estoque", " Gentileza avisar a Tamiris sobre o uso da Rotina...", { "Sim", "Nao" })
	/*If Aviso("Controle de Estoque", "Deseja Atualizar os Saldos de Pedidos no Controle de Estoque?", { "Sim", "Nao" }) == 1
		Processa({ || fDLP201() }, "Atualizando Saldo dos Pedidos... Aguarde...")
EndIf*/

Return

Static Function fDLP201()
	Local cQuery 

	cQuery := "UPDATE "+RetSqlName("SB2")+" SET B2_SALPEDI = 0, B2_QPEDVEN=0 "
	TcSqlExec(cQuery)
	//
	cQuery := "SELECT C2_PRODUTO, C2_LOCAL, SUM(C2_QUANT - C2_QUJE) C2_QUANT "
	cQuery += "FROM "+RetSqlName("SC2")+" SC2 "
	cQuery += "WHERE D_E_L_E_T_ <> '*' AND C2_DATRF = '' "
	cQuery += "GROUP BY C2_PRODUTO, C2_LOCAL "
	If Select("TRBSC2") != 0
		TRBSC2->(DbCloseArea())
	EndIf
	DbUseArea(.T., "TOPCONN", TCGenQry(,, cQuery), "TRBSC2", .F., .T.)
	DbSelectArea("TRBSC2")
	DbGoTop()
	While !Eof()
		DbSelectArea("SB2")
		DbSetOrder(1)
		If DbSeek(xFilial("SB2")+TRBSC2->C2_PRODUTO+TRBSC2->C2_LOCAL)
			RecLock("SB2", .F.)
			SB2->B2_SALPEDI := TRBSC2->C2_QUANT
			MsUnlock("SB2")		
		EndIf
		DbSelectArea("TRBSC2")
		DbSkip()
	EndDo
	
	//
	cQuery := "SELECT C6_PRODUTO,C6_LOCAL,SUM( C6_QTDVEN- C6_QTDENT ) C6_QUANT "
	cQuery += "FROM "+RetSqlName("SC6")+" SC6, "+RetSqlName("SC5")+" SC5 "
	cQuery += "WHERE C6_NUM = C5_NUM    AND C5_NOTA = ''  AND C6_QTDVEN > C6_QTDENT AND C6_BLOQUEI = '' "
	cQuery += "AND SC6.D_E_L_E_T_ ='' AND SC5.D_E_L_E_T_ ='' "
	cQuery += "GROUP BY C6_PRODUTO,C6_LOCAL "
	cQuery += "ORDER BY C6_PRODUTO,C6_LOCAL "
	If Select("TRBSC6") != 0
		TRBSC6->(DbCloseArea())
	EndIf
	DbUseArea(.T., "TOPCONN", TCGenQry(,, cQuery), "TRBSC6", .F., .T.)
	DbSelectArea("TRBSC6")
	DbGoTop()
	While !Eof()
		DbSelectArea("SB2")
		DbSetOrder(1)
		If DbSeek(xFilial("SB2")+TRBSC6->C6_PRODUTO+TRBSC6->C6_LOCAL)
			RecLock("SB2", .F.) 
			SB2->B2_QPEDVEN := TRBSC6->C6_QUANT
			MsUnlock("SB2")		
		EndIf
		DbSelectArea("TRBSC6")
		DbSkip()
	EndDo
	
	
	//
	cQuery := "SELECT C7_PRODUTO, C7_LOCAL, SUM(C7_QUANT-C7_QUJE) C7_QUANT "
	cQuery += "FROM "+RetSqlName("SC7")+" SC7 "
	cQuery += "WHERE D_E_L_E_T_ <> '*' AND C7_ENCER = '' AND C7_RESIDUO = '' "
	cQuery += "GROUP BY C7_PRODUTO, C7_LOCAL "
	If Select("TRBSC7") != 0
		TRBSC7->(DbCloseArea())
	EndIf
	DbUseArea(.T., "TOPCONN", TCGenQry(,, cQuery), "TRBSC7", .F., .T.)
	DbSelectArea("TRBSC7")
	DbGoTop()
	While !Eof()
		DbSelectArea("SB2")
		DbSetOrder(1)
		If DbSeek(xFilial("SB2")+TRBSC7->C7_PRODUTO+TRBSC7->C7_LOCAL)
			RecLock("SB2", .F.)
			SB2->B2_SALPEDI += TRBSC7->C7_QUANT
			MsUnlock("SB2")		
		EndIf
		DbSelectArea("TRBSC7")
		DbSkip()
	EndDo

	cQuery := "SELECT C1_PRODUTO, C1_LOCAL, SUM(C1_QUANT-C1_QUJE) C1_QUANT "
	cQuery += "FROM "+RetSqlName("SC1")+" SC1 "
	cQuery += "WHERE D_E_L_E_T_ <> '*' AND  C1_RESIDUO = '' "
	cQuery += "GROUP BY C1_PRODUTO, C1_LOCAL "
	If Select("TRBSC1") != 0
		TRBSC1->(DbCloseArea())
	EndIf
	DbUseArea(.T., "TOPCONN", TCGenQry(,, cQuery), "TRBSC1", .F., .T.)
	DbSelectArea("TRBSC1")
	DbGoTop()
	While !Eof()
		DbSelectArea("SB2")
		DbSetOrder(1)
		If DbSeek(xFilial("SB2")+TRBSC1->C1_PRODUTO+TRBSC1->C1_LOCAL)
			RecLock("SB2", .F.)
			SB2->B2_SALPEDI += TRBSC1->C1_QUANT
			MsUnlock("SB2")		
		EndIf
		DbSelectArea("TRBSC1")
		DbSkip()
	EndDo
Return

*********************************
User Function DLP201A()
*************
	If Aviso("Controle de Estoque", "Deseja Atualizar os Saldos de Solicitacoes?", { "Sim", "Nao" }) == 1
	cQuery := "UPDATE "+RetSqlName("SC1")+" SET C1_QUJE = C1_QUANT,C1_RESIDUO='S'"
	cQuery += "WHERE D_E_L_E_T_ <> '*' AND C1_QUJE <> C1_QUANT  AND C1_PEDIDO <>'' "
	TcSqlExec(cQuery)
	EndIf
Return

