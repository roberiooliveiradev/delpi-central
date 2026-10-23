
User Function F4LoteHeader()/*cProg, lSLote, aHeaderF4cProg - Programa que chamou a F4LotelSLote - Informa se o produto tem rastro por sublote*/
    Local aHeaderF4 := PARAMIXB[3]
    Local nPosDT:= 7
    aHeaderF4[nPosDT] := "Dt Entrada Lt"
    Aadd(aHeaderF4, 'Nome Fornecedor')
    conout("stop")
Return(aHeaderF4)




