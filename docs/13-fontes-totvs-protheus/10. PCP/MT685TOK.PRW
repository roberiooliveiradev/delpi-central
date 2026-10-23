USER FUNCTION MT685TOK()
    Local aArea := getarea()
    Local lRet := .t.
    Local nVlrInt  := 0 // valor sem arredondamento
    Local nVLrOrig := 0 // Valor original da movimentacao
    Local cProdEx  := supergetmv("MV_DLPPRDPC",.F.,"10080755") /// PRODUTO QUE PERMITIRAO QUEBRA DE PEÇA
    Local cPrdAtu  := ""
    Local cB1UM    := ""//ALLTRIM(POSICIONE("SB1",1,XFILIAL("SB1")+cPrdAtu,"B1_UM"))
    Local nPosCodD  := aScan(aHeader,{|z| AllTrim(z[2])=="BC_CODDEST"})

    conout("GDA MT685TOK")
    conout("GDA MT685TOK BC_OP"+ GdFieldGet("BC_OP",1))

    // For nX := 1 To Len(aCols)
    //     If !GdDeleted(nX, aHeader,aCols)
    //         //cPrdAtu := aCols[nX][nPosCodD]
    //         cPrdAtu := GdFieldGet("BC_CODDEST",nX)
    //         cB1UM    := ALLTRIM(POSICIONE("SB1",1,XFILIAL("SB1")+cPrdAtu,"B1_UM"))

    //         if !( (cPrdAtu) $  (cProdEx)) .AND. cB1UM $ "PC_UN"
    //             nVlrInt  := GdFieldGet("BC_QTDDEST",nX)
    //             nVLrOrig := NOROUND(GdFieldGet("BC_QTDDEST",nX),0)
    //             IF nVLrOrig!=nVlrInt
    //                 MSGSTOP("Atenção, só é permitida movimentação de Peça Inteira.")
    //                 lRet := .f.
    //             ENDIF
    //         endif

    //     endif
    // next nX


    restarea(aArea )
Return lRet
