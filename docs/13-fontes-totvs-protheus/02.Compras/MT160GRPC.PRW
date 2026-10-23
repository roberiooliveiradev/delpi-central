#INCLUDE "PROTHEUS.CH"


/*/{Protheus.doc} User Function MT160GRPC
    Preenche a quantidade de embalagens e a data de entrega na tabela SC7
    @type  Function
    @author Luan Woichechoscki
    @since 29/07/2022
    @version version
    @param
    @return nill
    @example
    (examples)
    @see (links_or_references)
/*/
User Function MT160GRPC()

    conout("PE - MT160GRPC")
    conout("PE - MT160GRPC EMP "+CEMPANT+"/FIL "+CFILANT)
    conout("C7_PRODUTO ->"+SC7->C7_PRODUTO)
    conout("C7_FORNECE ->"+SC7->C7_FORNECE)
    conout("C7_LOJA ->"+SC7->C7_LOJA)


    IF  cEmpAnt $ "01_05"
        SA5->(DbSetOrder(2))
        SA5->(DbSeek(XFILIAL("SA5")+SC7->C7_PRODUTO+SC7->C7_FORNECE+SC7->C7_LOJA))
        CONOUT("ACHOU SA5")
        IF SA5->A5_EMBAL > 0
            CONOUT("A5_EMBAL > 0 ")
            RecLock("SC7",.F.)
            SC7->C7_EMBAL  :=  SC7->C7_QUANT/SA5->A5_EMBAL
            SC7->(MsUnLock())
        ENDIF
        RecLock("SC7",.F.)
        SC7->C7_DATPRF := DaySum(Date(), SA5->A5_LEADT)
        SC7->(MsUnLock())

    ENDIF

Return
