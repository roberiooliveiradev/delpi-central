

#Include 'Protheus.ch'

User Function COLSTTS()

    Local aArea	:= GetArea()
    Local aAreaSA1:= SA1->(GetArea())
    Local aAreaSF1:= SF1->(GetArea())
    Local lUsaColab := UsaColaboracao("4")

    Local cSFunName := FunName() // Salvar o FUNNAME
    Local nModBKP := nModulo
    // If (CTIsReady(,,.t.,lUsaColab))
    //
    //     nModulo := 2 // Setar Modulo 2 Compras
    //     SetFunName("MATA103") // Setar FUNNAME com MATA103
    //     //
    //     A103Manif("SF1",SF1->(RECNO()),1) // Funcao de Manifestar NFe esta dentro do MATA103
    //     //  A103Manif("SF1",SF1->(RECNO()),2) // Funcao de Manifestar NFe esta dentro do MATA103
    //     //
    //     nModulo := nModBKP // Voltar Modulo 11 Veiculos
    //     SetFunName(cSFunName) // Voltar o FUNNAME
    // else
    //
    //     FWAlertWarning("TSS Nao configurado", "Delpi - Imp XML")
    //
    // endif

    RestArea(aArea)
    RestArea(aAreaSA1)
    RestArea(aAreaSF1)

Return


// Static Function ReadyTSS(cURL,nTipo,lHelp)
//     Local lUsaColab := UsaColaboracao("4")
// Return (CTIsReady(cURL,nTipo,lHelp,lUsaColab))
