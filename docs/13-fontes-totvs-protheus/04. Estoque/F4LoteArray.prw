
/*
cProg - Identifica o programa usado na chamada do PE.
lSLote - Identifica se o produto'tem rastro por Sub-Lote.
cAlias - Alias original (Ex.: SB8).
cAliasTop - Alias relativo a query quando usado versão Top.
aArray - Array original com os dados.*/

User Function F4LoteArray()/*Deve retornar o array acrescido da coluna ou reordenado na sequencia desejada*/
    Local cProgF4   := PARAMIXB[1] //cProg - Identifica o programa usado na chamada do PE.
    Local lSLoteF4  := PARAMIXB[2] // lSLote - Identifica se o produto'tem rastro por Sub-Lote.
    Local cAliasF4  := PARAMIXB[3] //cAlias - Alias original (Ex.: SB8).
    Local cAliasTF4 := PARAMIXB[4] //cAliasTop - Alias relativo a query quando usado versão Top.
    Local aArrayF4  := PARAMIXB[5]
    Local nPosFor   := 11
    Local nPosLJFor := 12
    Local nMFornece := space(getsx3cache("A2_NOME","X3_TAMANHO"))

    if !Empty(aArrayF4[nPosFor]) .and.  !Empty(aArrayF4[nPosLJFor])
        nMFornece := posicione("SA2",1,XFILIAL("SA2")+aArrayF4[nPosFor]+aArrayF4[nPosLJFor],"A2_NOME")
    endif

    conout("stop")
    Aadd(aArrayF4, nMFornece)
Return(aArrayF4)




