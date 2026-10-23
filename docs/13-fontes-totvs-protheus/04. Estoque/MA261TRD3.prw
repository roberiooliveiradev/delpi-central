#Include 'TOTVS.CH'

/*/{Protheus.doc} MA261TRD3
    (Atualiza campos após a gravação da transferência)
    @type user function
    @author Luan Woichechoscki
    @since 13/02/2025
/*/
User Function MA261TRD3()

    //  Local aRecSD3   := PARAMIXB[1]
    //  Local nFor      := 1
    //  Local nPosSNF   := aScan(aHeader,{ |x| x[2] == 'D3_DLPSNF'})
    //  Local nPosNFE   := aScan(aHeader,{ |x| x[2] == 'D3_DLPNFE'})
    //  Local nPosLJF   := aScan(aHeader,{ |x| x[2] == 'D3_DLPLJF'})
    //  Local nPosFor   := aScan(aHeader,{ |x| x[2] == 'D3_DLPFOR'})
    //  Local nPosLtc   := aScan(aHeader,{ |x| x[2] == 'D3_DLPLTC'})
    //
    //  For nFor := 1 To Len(aRecSD3)
    //
    //      //***********************************  Requisicao DE4 ***************************************//
    //      SD3->(DbGoto(aRecSD3[nFor][1]))
    //
    //      IF  nPosSNF > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPSNF := aCols[nFor,nPosSNF]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosNFE > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPNFE := aCols[nFor,nPosNFE]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosLJF > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPLJF := aCols[nFor,nPosLJF]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosFor > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPFOR := aCols[nFor,nPosFor]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosLtc > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPLTC := aCols[nFor,nPosLtc]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      //***********************************  Devolucao DE4 ***************************************//
    //      SD3->(DbGoto(aRecSD3[nFor][2]))
    //
    //      IF nPosSNF > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPSNF := aCols[nFor,nPosSNF]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosNFE > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPNFE := aCols[nFor,nPosNFE]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosLJF > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPLJF := aCols[nFor,nPosLJF]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosFor > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPFOR := aCols[nFor,nPosFor]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      IF nPosLtc > 0
    //          RecLock('SD3', .F.)
    //          SD3->D3_DLPLTC := aCols[nFor,nPosLtc]
    //          SD3->(MsUnlock())
    //      Endif
    //
    //      //***********************************  Validação SD1 para a consulta F7 ***************************************//
    //      IF nPosSNF > 0 .AND. nPosNFE > 0 .AND. nPosFor > 0 .AND. nPosLJF > 0
    //
    //          SD3->(DbGoto(aRecSD3[nFor][1]))
    //          RecLock('SD3', .F.)
    //          SD3->D3_ZSD1DLP := Alltrim(aCols[nFor,nPosNFE]) + Alltrim(aCols[nFor,nPosSNF]) + Alltrim(aCols[nFor,nPosFor]) + Alltrim(aCols[nFor,nPosLJF])
    //          SD3->(MsUnlock())
    //
    //          SD3->(DbGoto(aRecSD3[nFor][2]))
    //          RecLock('SD3', .F.)
    //          SD3->D3_ZSD1DLP := Alltrim(aCols[nFor,nPosNFE]) + Alltrim(aCols[nFor,nPosSNF]) + Alltrim(aCols[nFor,nPosFor]) + Alltrim(aCols[nFor,nPosLJF])
    //          SD3->(MsUnlock())
    //
    //      ENDIF
    //
    //      //***********************************  Savando tabela MovimentaçõesxLoteDelpi  ***************************************//
    //      RecLock('ZA1', .T.)
    //      ZA1->ZA1_FILIAL := SD3->D3_FILIAL
    //      ZA1->ZA1_DOC    := SD3->D3_DOC
    //      ZA1->ZA1_COD    := SD3->D3_COD
    //      ZA1->ZA1_DLPLTC := SD3->D3_DLPLTC
    //      ZA1->ZA1_QUANT  := SD3->D3_QUANT
    //      ZA1->ZA1_SALDO  := SD3->D3_QUANT
    //      ZA1->ZA1_RECSD3 := aRecSD3[nFor][1]
    //      ZA1->ZA1_SD1DLP := Alltrim(aCols[nFor,nPosNFE]) + Alltrim(aCols[nFor,nPosSNF]) + Alltrim(aCols[nFor,nPosFor]) + Alltrim(aCols[nFor,nPosLJF])
    //      ZA1->(MsUnlock())
    //
    //  Next nFor

Return
