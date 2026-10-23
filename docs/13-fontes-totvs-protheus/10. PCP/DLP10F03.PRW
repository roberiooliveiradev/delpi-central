USER FUNCTION DLP10F03()



    lOCAL aArea := getarea()
    lOCAL cMsg :=""
    Local cEol := chr(10)
    dbSelectArea("SC7")
    dbSetOrder(8)

    IF SC7-> ( DbSeek( SC2->C2_FILIAL+SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN  ) )


        cMsg +="Filial "+alltrim(SC2->C2_FILIAL)+" OP "+alltrim(SC2->C2_NUM)+" Item "+alltrim(SC2->C2_ITEM)+" Sequencia "+alltrim(SC2->C2_SEQUEN) + cEol+" "+cEol
        cMsg +="Existem Pedidos de Compras Atrelados a esta Ordem de Produção "+cEol
        cMsg +="Pedido " + SC7->C7_NUM + cEol

        RecLock("SC7",.F.)  //Atualizacao do flag de Impressao
        //C7_FILIAL, C7_OP, C7_NUM, C7_ITEM, C7_SEQUEN, R_E_C_N_O_, D_E_L_E_T_
        SC7->C7_OP := ""
        MsUnLock()

        IF !EMPTY (SC7->C7_NUMSC )

            dbSelectArea("SC1")
            dbSetOrder(1)

            IF SC1-> ( DbSeek( SC2->C2_FILIAL+ SC7->C7_NUMSC  + SC7->C7_ITEMSC) )

                //C7_FILIAL, C7_OP, C7_NUM, C7_ITEM, C7_SEQUEN, R_E_C_N_O_, D_E_L_E_T_
                RecLock("SC1",.F.)  //Atualizacao do flag de Impressao
                SC1->C1_OP := ""
                MsUnLock()

            endif
            cMsg +="Solicitacao  " + SC7->C7_NUMSC + cEol

        ENDIF

    endif

    if !EMPTY(cMsg)
        EEcView(cMsg)
    endif

    CONOUT("GABRIEL")
    A650DELETA("SC2",SC2->(Recno()), 5)
    restarea( aArea)

rETURN
