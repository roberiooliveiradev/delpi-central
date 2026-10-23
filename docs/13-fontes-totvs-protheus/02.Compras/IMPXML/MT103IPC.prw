#Include 'Protheus.ch'


user function MT103IPC()

    //Local nPosBicm     := GetPosSD1("D1_BASEICM")
    Local nPosPicm  := GetPosSD1("D1_PICM")     // DT_XALQICM
    Local nPosVicm  := GetPosSD1("D1_VALICM")   //DT_XMLICM
    Local nPosIpi   := GetPosSD1("D1_IPI")      //DT_XALQIPI
    Local nPosVipi  := GetPosSD1("D1_VALIPI")   //DT_XMLIPI
    Local nPosPis   := GetPosSD1("D1_ALQIMP6")  //DT_XALQPIS
    Local nPosVPis  := GetPosSD1("D1_VALIMP6")  //DT_XMLPIS
    Local nPosCof   := GetPosSD1("D1_ALQIMP5")  //DT_XALQCOF
    Local nPosVCof  := GetPosSD1("D1_VALIMP5")  //DT_XMLCOF

    Local nPosFornec	:= GetPosSD1("D1_FORNECE")
    Local nPosLoja		:= GetPosSD1("D1_LOJA")
    Local nPosDoc		:= GetPosSD1("D1_DOC")
    Local nPosSerie		:= GetPosSD1("D1_SERIE")
    Local nPosItem		:= GetPosSD1("D1_ITEM")
    Local nPosCC		:= GetPosSD1("D1_CC")

    //		nPos := aScan(aHeader,{|x| AllTrim(x[2]) == cCampo} )
    //
    //"DT_XMLPIS" 	,"DT_ALIQPIS"	,"DT_XALQPIS"})
    Local xItem := paramixb[1]

    CONOUT("MT103IPC")
    //dbSelectArea("SDT")
    //SDT->(DbSetOrder(8))
    // If SDT->(DbSeek(xFilial("SDT") + CA100FOR + CLOJA+ CNFISCAL +CSERIE + aCols[xItem,nPosItem] ))
    aCols[xItem,nPosCC] := SC7->C7_CC
    //D1_PICM")     // DT_XALQICM
    //  if aCols[nItem,nPosPicm] != SDT->DT_XALQICM
    //      aCols[nItem,nPosPicm] := SDT->DT_XALQICM
    //  ENDIF
    //  //D1_VALICM")   //DT_XMLICM
    //  if aCols[nItem,nPosVicm] != SDT->DT_XMLICM
    //      aCols[nItem,nPosVicm] := SDT->DT_XMLICM
    //  ENDIF
    //  // GetPosSD1("D1_IPI")      //DT_XALQIPI
    //  if aCols[nItem,nPosIpi] != SDT->DT_XALQIPI
    //      aCols[nItem,nPosIpi] := SDT->DT_XALQIPI
    //  ENDIF
    //
    //  ///*      nPosVipi  := GetPosSD1("D1_VALIPI")   //DT_XMLIPI
    //  if aCols[nItem,nPosVipi] != SDT->DT_XMLIPI
    //      aCols[nItem,nPosVipi] := SDT->DT_XMLIPI
    //  ENDIF
    //  //D1_ALQIMP6")  //DT_XALQPIS
    //   if aCols[nItem,nPosPis] != SDT->DT_XALQPIS
    //       aCols[nItem,nPosPis] := SDT->DT_XALQPIS
    //   ENDIF
    //   //  nPosVPis  := GetPosSD1("D1_VALIMP6")  //DT_XMLPIS
    //   if aCols[nItem,nPosVPis] != SDT->DT_XMLPIS
    //       aCols[nItem,nPosVPis] := SDT->DT_XMLPIS
    //   ENDIF
    //   //D1_ALQIMP5")  //DT_XALQCOF
    //   if aCols[nItem,nPosCof] != SDT->DT_XALQCOF
    //       aCols[nItem,nPosCof] := SDT->DT_XALQCOF
    //   ENDIF
    //D1_VALIMP5")  //DT_XMLCOF
    // if aCols[nItem,nPosVCof] != SDT->DT_XMLCOF
    //     aCols[nItem,nPosVCof] := SDT->DT_XMLCOF
    // ENDIF

    // endif
Return Nil
