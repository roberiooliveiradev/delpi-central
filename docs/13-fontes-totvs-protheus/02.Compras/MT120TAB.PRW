

user function MT120TAB()


    Local aArea     := GetArea()
    Local aAreaSB1  := SB1->(GetArea())
    Local aAreaSA2  := SA2->(GetArea())
    Local aAreaAIB  := AIB->(GetArea())
    Local nPCodTab  := aScan(aHeader,{|x| AllTrim(x[2])=="C7_CODTAB"})
    Local nPProduto := aScan(aHeader,{|x| AllTrim(x[2])=="C7_PRODUTO"})
    Local nPQuant   := aScan(aHeader,{|x| AllTrim(x[2])=="C7_QUANT"})
    Local nPAVista  := aScan(aHeader,{|x| AllTrim(x[2])=="C7_AVISTA"})
    Local nPPreco   := aScan(aHeader,{|x| AllTrim(x[2])=="C7_PRECO"})
    Local nPTxFor   := aScan(aHeader,{|x| AllTrim(x[2])=="C7_TAXAFOR"})
    Local nPrcCom   := IF(nPPreco > 0 ,aCols[N][nPPreco],0)
    Local nQtde     := If(nPQuant > 0 ,aCols[N][nPQuant],0)
    Local cProduto  := If(nPProduto > 0 ,aCols[N][nPProduto],"")
    Local cCodTab	:= If(nPCodTab > 0,aCols[N][nPCodTab],"")
    Local lIntGC    := IIf((SuperGetMV("MV_VEICULO",,"N")) == "S",.T.,.F.) .and. (nModulo == 11 .or. nModulo == 14 .or. nModulo == 41)
    Local nValFrete := 0

    IF alltrim(cEmpAnt) $ "01_05"
        dbSelectArea("SB1")
        dbSetOrder(1)
        SA2->(dbSetOrder(1))
        If SA2->(MsSeek(xFilial("SA2")+cA120Forn+cA120Loj))
            if !empty(SA2->A2_ZTABPRC)
                cCodTab :=SA2->A2_ZTABPRC
                aCols[n][nPCodTab] := cCodTab
                If MaVldTabCom(cA120Forn,cA120Loj,cCodTab,cCondicao,/*cHelp*/,dA120Emis)
                    dbSelectArea("SB1")
                    dbSetOrder(1)
                    If ( !Empty(cProduto) .And. MsSeek(xFilial("SB1")+cProduto,.F.) )

                        DBSELECTAREA("AIB")
                        IF AIB->( MsSeek(XFILIAL("AIB")+ cA120Forn+ cA120Loj+ cCodTab+ xfilial("SC7")) )

                            nPrcCom := MaTabPrCom(cCodTab,cProduto,nQtde,cA120Forn,cA120Loj,nMoedaPed,dA120Emis,nTxMoeda,@nValFrete)
                            IF nPrcCom >0.00
                                If MaFisFound("IT",N)
                                    MaFisRef("IT_PRCUNI","MT120",nPrcCom)
                                    MaFisRef("IT_FRETE","MT120",nValFrete)
                                    If ExistTrigger("C7_PRECO")
                                        RunTrigger(2,N)
                                    EndIf
                                    If ExistTrigger("C7_FRETE")
                                        RunTrigger(2,N,,"C7_FRETE")
                                    EndIf
                                EndIf
                            EndIf
                        EndIf
                    endif
                EndIf
            EndIf
        EndIf
    EndIf

    RESTAREA(aArea    )
    RESTAREA(aAreaSB1 )
    RESTAREA(aAreaSA2 )
    RESTAREA(aAreaAIB )

Return Nil
