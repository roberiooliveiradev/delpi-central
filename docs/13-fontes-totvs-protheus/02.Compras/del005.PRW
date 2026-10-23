/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DEL005    ºAutor  ³Microsiga           º Data ³  12/01/03   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Alimentar atraves de ExecBlock o campo de Valor Unitario   º±±
±±º          ³ do campo do Item de Pedido de Compras                      º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function DEL005()

nPosPrc			:= ascan(aHeader,{|x| alltrim(x[2]) == "C7_PRECO"})
nPosTab			:= ascan(aHeader,{|x| alltrim(x[2]) == "C7_CODTAB"})

If Empty(aCols[n][nPostab])
	
	dbSelectArea("SD1")
	dbSetOrder(12) // Filial+Produto+Fornecedor+Loja+Data_Emissao
	dbGoTop()
	
	SD1->(dbSeek(xFilial()+aCols[n][2]+M->CA120FORN+M->CA120LOJ,.f.))
	While !Eof() .and. xFilial()+aCols[n][2]+M->CA120FORN+M->CA120LOJ == SD1->D1_FILIAL+SD1->D1_COD+SD1->D1_FORNECE+SD1->D1_LOJA
		
		M->C7_PRECO 		:= SD1->D1_VUNIT
		aCols[n][nPosPrc]	:= SD1->D1_VUNIT
		
		dbSkip()
	End
	
EndIf

Return .t.
