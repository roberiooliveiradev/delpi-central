/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DEL021    ºAutor  ³Microsiga           º Data ³  17/05/06   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Alimenta  atraves de ExecBlock o campo Codigo da Tabela    º±±
±±º          ³ de preco a partir do primeiro produto digitado no Ped.Comp º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ MP8                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function DEL021()
**********************
Local aSeg		:= GetArea()
Local aSegAIA	:= AIA->(GetArea())
Local nPosTab	:= ascan(aHeader,{|x| alltrim(x[2]) == "C7_CODTAB"})

If n == 1 .and. Len(aCols) == 1
	
	nCont := 0
	dbSelectArea("AIA")
	dbSetOrder(1)
	dbSeek(xFilial("AIA")+cA120Forn+cA120Loj,.T.)
	While !EOF() .and. AIA->AIA_filial+AIA->AIA_codfor+AIA->AIA_lojfor == xFilial("AIA")+cA120Forn+cA120Loj
		
		If Dtos(dDataBase) >= Dtos(AIA->AIA_datde) .and. Dtos(dDataBase) <= Dtos(AIA->AIA_datate) .and. AIA->AIA_condpg == cCondicao
			cCodTab	:= AIA->AIA_codtab
			nCont++
		EndIf
		
		dbSelectArea("AIA")
		dbSkip()
	EndDo
	
	If nCont == 1 .and. !Empty(cCodTab)
		M->C7_codtab		:= cCodTab
		aCols[n][nPosTab]	:= cCodTab
	EndIf
	
EndIf

RestArea(aSeg)
RestArea(aSegAIA)

Return .T.
