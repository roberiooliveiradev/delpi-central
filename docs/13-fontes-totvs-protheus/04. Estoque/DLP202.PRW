#Include "rwmake.ch"
#Include "topconn.ch"

User Function DLP202()
	If Aviso("Controle de Estoque", "Deseja Zerar Saldo das Moedas: 2,3,4?", { "Sim", "Nao" }) == 1
		Processa({ || fDLP202() }, "Zerando Moedas... Aguarde...")
	EndIf
Return


*************************
Static Function fDLP202()
***************
Local cQuery

If ( Select ( "TRBSB2" ) <> 0 )
   dbSelectArea ( "TRBSB2" )
   dbCloseArea ()
End
 
BeginSql Alias "TRBSB2"
SELECT
	B2_COD, B2_LOCAL, B2_QATU,
	B2_VATU1, B2_VATU2, B2_VATU3, B2_VATU4, B2_VATU5
FROM SB2010
WHERE
	(B2_VATU2 <> 0 OR B2_VATU3 <> 0 OR B2_VATU4 <> 0 OR B2_VATU5 <> 0) AND B2_LOCAL = '01'
EndSql

DbSelectArea("TRBSB2")
DbGoTop()
While !Eof()

	dbSelectArea("SB1")
	dbSetOrder(1)
	If (DbSeek(xFilial('SB1')+TRBSB2->B2_COD))
		aValor := {{ 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 0, 0, 0, 0 }}
		For I := 2 To 5
			cVatu := "TRBSB2->B2_VATU" + LTrim(Str(I))
			nVatu := &cVatu
			If nVatu < 0
				aValor[1][I] := nVatu
				aValor[1][7] += 1
			ElseIf nVatu > 0
				aValor[2][I] := nVatu
				aValor[2][7] += 1
			EndIf
		Next
		// ENTRADA
		If aValor[1][7] > 0
			lMsErroAuto := .F.
			aVetor := {{"D3_TM", Iif(SB1->B1_APROPRI == 'I', '201', '200'), NIL},;
			{"D3_EMISSAO", dDataBase, NIL},;
			{"D3_COD", TRBSB2->B2_COD, NIL},;
			{"D3_LOCAL", TRBSB2->B2_LOCAL, NIL},;
			{"D3_QUANT", 0, NIL},;
			{"D3_CUSTO1", 0.01, NIL},;
			{"D3_CUSTO2", IIF(aValor[1][2]<0,aValor[1][2]*(-1),0), NIL},;
			{"D3_CUSTO3", IIF(aValor[1][3]<0,aValor[1][3]*(-1),0), NIL},;
			{"D3_CUSTO4", IIF(aValor[1][4]<0,aValor[1][4]*(-1),0), NIL},;
			{"D3_CUSTO5", IIF(aValor[1][5]<0,aValor[1][5]*(-1),0), NIL}}
			MSExecAuto({|x,y| mata240(x,y)}, aVetor, 3)
			If lMsErroAuto
				MostraErro()
			EndIf
		EndIf
		// SAIDA
		If aValor[2][7] > 0   
			lMsErroAuto := .F.
			aVetor := {{"D3_TM", Iif(SB1->B1_APROPRI == 'I', '601', '600'), NIL},;
			{"D3_EMISSAO", dDataBase, NIL},;
			{"D3_COD", TRBSB2->B2_COD, NIL},;
			{"D3_LOCAL", TRBSB2->B2_LOCAL, NIL},;
			{"D3_QUANT", 0, NIL},;
			{"D3_CUSTO1", 0.01, NIL},;
			{"D3_CUSTO2", IIF(aValor[2][2]>0,aValor[2][2],0), NIL},;
			{"D3_CUSTO3", IIF(aValor[2][3]>0,aValor[2][3],0), NIL},;
			{"D3_CUSTO4", IIF(aValor[2][4]>0,aValor[2][4],0), NIL},;
			{"D3_CUSTO5", IIF(aValor[2][5]>0,aValor[2][5],0), NIL}}
			MSExecAuto({|x,y| mata240(x,y)}, aVetor, 3)
			If lMsErroAuto
				MostraErro()
			EndIf
		EndIf
	EndIf
	DbSelectArea("TRBSB2")
	DbSkip()
EndDo
Return()
