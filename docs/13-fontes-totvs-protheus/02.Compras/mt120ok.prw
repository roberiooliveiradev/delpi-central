
user function mt120ok()

    lOCAL lRet := .t.
    lOCAL nX
    lOCAL nPosCod
    Local nPosPr	:= Ascan(aHeader, {|x| alltrim(x[2]) == "C7_PRODUTO"})
    Local nPosPrUn	:= Ascan(aHeader, {|x| alltrim(x[2]) == "C7_PRECO"})
    Local nI
    Local aPrUnDiv := {}


    For nX := 1 to Len( aCols )
        cDescriDLP :=""

        //GDFieldGet ( < cCampo>, [ nLine], [ lReadVar], [ aHeaderPastPar], [ aColsPastPar] ) --> xRet
        //GDFieldPut ( < cCampo>, < xConteúdo>, [ nLine], [ aHeaderPastPar], [ aColsPastPar], [ lReadVar] ) --> uLast
        SX3->(DbSetOrder(2))

        SX3->(DbSetOrder(1))
        if !GDDeleted(nX)
            dbSelectArea("SA5")
            SA5->(DbSetOrder(1))

            IF  SA5->(DBSeek(xFilial("SA5")+cA120Forn+cA120Loj+gdfieldget("C7_PRODUTO",nX)))
                IF !eMPTY(  SA5->A5_CODPRCA) .and. !(alltrim(SA5->A5_CODPRCA) $ gdfieldget("C7_DESCRI",nX))
                    cDescriDLP :=  ALLTRIM(SA5->A5_CODPRCA) +" - "+ ALLTRIM(gdfieldget("C7_DESCRI",nX))
                    cDescriDLP := PADR(cDescriDLP,GETSX3CACHE("C7_DESCRI","X3_TAMANHO"))
                    GDFieldPut("C7_DESCRI",cDescriDLP,nX)
                ENDIF
            ENDIF

            //    lAchou := MsSeek(xFilial("SA5")+cA120Forn+cA120Loj+aCols[n][nPosCod])

        ENDIF

    NEXT nX

    For nI := 1 To Len(aCols)

        nPos := aScan(aPrUnDiv,{|x| AllTrim(x[1])==alltrim(acols[nI][nPosPr])})

        if nPos == 0 // caso nao ache o produto ele vai adicionar no array de controle

            aadd(aPrUnDiv, {acols[nI][nPosPr], acols[nI][nPosPrUn]})
        else
            if acols[nI][nPosPrUn] != aPrUnDiv[nPos][2] // Caso ja tenha sido adicionado anteriormente,  comparo o preco da linha atual com o ja adicionado
                FWAlertWarning("O Produto: "+ALLTRIM(aPrUnDiv[nPos][1])+" não pode ter preço unitário diferente.","Atenção" )
                lRet :=.F.
            endif
        endif

    Next nI

Return lRet
