#INCLUDE "TOTVS.CH"
#INCLUDE "FWMBROWSE.CH"
#INCLUDE "PARMTYPE.CH"
#INCLUDE "TBICONN.CH"
#INCLUDE "RWMAKE.CH"

User Function MT120FIM()
    Local aArea := getarea()
    Local aSegSA2	:= SA2->(GetArea())
    Local aSegSA5	:= SA5->(GetArea())
    Local nOpcao := PARAMIXB[1]   // Opção Escolhida pelo usuario
    Local cNumPC := PARAMIXB[2]   // Numero do Pedido de Compras
    Local nOpcA  := PARAMIXB[3]   // Indica se a ação foi Cancelada = 0  ou Confirmada = 1.CODIGO DE APLICAÇÃO DO USUARIO.....
    lOCAL n0
    conout("gabriel MT120FIM")
    IF (nOpcao == 4 .OR. nOpcao == 3) .AND. nOpcA == 1
        dbSelectArea("SA2")
        SA2->(dbSetOrder(1))

        SA2->(dbSeek(xFilial("SA2")+CA120FORN+CA120LOJ ))
        IF SA2->(Found()) .and. !EMPTY(SA2->A2_ZTABPRC)
            conout("gabriel MT120FIM - achou fornecedor e A2_ZTABPRC"+SA2->A2_ZTABPRC)
            For n0 := 1 To Len( aCols)

                IF !(GDDeleted(n0))
                    cProd := GDFieldGet('C7_PRODUTO',n0)
                    dbSelectArea("SA5")
                    SA5->(dbSetOrder(1))
                    CONOUT("PRODUTO "+cProd)
                    CONOUT("foRNECEDOR "+CA120FORN+"|"+CA120LOJ)
                    IF   SA5->(dbSeek(xFilial("SA5")+CA120FORN+CA120LOJ+cProd ))
                        CONOUT("ACHOU SA5")
                        RecLock("SA5", .F.)
                        SA5->A5_CODTAB   := SA2->A2_ZTABPRC
                        SA5->(MsUnlock())

                    endif
                endif
            next n0
        endif
    endif
Return

