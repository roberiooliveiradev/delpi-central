user function MT240INC
    Local aArea := getarea()
    Local cRotina := "MATA240"
    conout("gda")

    FWMsgRun( ,{||  U_DLP02F01(cRotina)},"Processando...")

    Pergunte("MTA240",.F.)

    restarea(aArea)
Return
