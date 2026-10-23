


USER FUNCTION DLP05F04(cFil,cNf,cSerie,nOper)

    lRet := .t.
    if nOper == 1
        return .t.
    endif
    dbSelectArea("SD2")
    //MV_PAR04 := 2	//[Operacao] NF de Saida
    SD2->(DbSetOrder(3))
    SD2->(DbSeek( cFil+cNf+cSerie))
    dbSelectArea("CB7")
    CB7->(DbSetOrder(4))
    If  CB7->(DbSeek(xFilial("CB7")+SD2->D2_DOC+SD2->D2_SERIE+SD2->D2_LOCAL+" "))
        if alltrim(CB7->CB7_STATUS) $ "0_1"
            lRet := .f.
        endif
    else
        if SD2->D2_EMISSAO< STOD('20241030')
            lRet := .f.
        endif
    endif
    IF !lRet
        FWAlertError("Não será possivel imprimir a DANFE, a mesma deve seguir o processo de separação","Delpi Faturamento")
    ENDIF
Return lRet
