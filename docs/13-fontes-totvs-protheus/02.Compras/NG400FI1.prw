************************
User Function NG400FI1() //Ponto de entrada para gerar solcitacao de compra de produto
   *************
   sOrdem := STJ->TJ_ORDEM
   aItem := {}
   nItem := 0
   dbSelectArea("STL")
   dbSetorder(1)
   dbSeek(xFilial("STL")+sOrdem,.T.)
   While xFilial("STL")+sOrdem == STL->TL_FILIAL+STL->TL_ORDEM
      If STL->TL_TIPOREG=='P'
         dbSelectArea("SB1")
         dbSetorder(1)
         dbSeek(xFilial("SB1")+STL->TL_CODIGO,.T.)
         If STL->TL_CODIGO == SB1->B1_COD .And. SB1->B1_LOCPAD >= '02' .And. SB1->B1_ESTSEG > 0 .And. SB1->B1_EMIN>0
            dbSelectArea("SB2")
            DbSetOrder(1)
            DbSeek(xFilial("SB2")+SB1->B1_COD+SB1->B1_LOCPAD,.T.)
            iF xFilial("SB2")+SB1->B1_COD+SB1->B1_LOCPAD==SB2->B2_FILIAL+SB2->B2_COD+SB2->B2_LOCAL .And. SB1->B1_EMIN>SB2->B2_QATU
               nQteSc1 := 0
               dbSelectArea("SC1")
               dbSetorder(5)
               dbSeek(xFilial("SC1")+Space(6)+SB1->B1_COD,.T.)
               While xFilial("SC1")+Space(6)+SB1->B1_COD == SC1->C1_FILIAL + SC1->C1_COTACAO + SC1->C1_PRODUTO .And. !Eof()
                  nQteSc1 := nQteSc1 + SC1->C1_QUANT
                  DbSkip()
               EndDo
               nQteSc8 := 0
               dbSelectArea("SC8")
               dbSetorder(6)
               dbSeek(xFilial("SC8")+Space(6)+SB1->B1_COD,.T.)
               While xFilial("SC8")+Space(6)+SB1->B1_COD == SC8->C8_FILIAL + SC8->C8_NUMPED + SC8->C8_PRODUTO .And. !Eof()
                  nQteSc8 := nQteSc8 + SC8->C8_QUANT
                  DbSkip()
               EndDo
               nQteSc7 := 0
               dbSelectArea("SC7")
               dbSetorder(15)
               dbSeek(xFilial("SC7")+' '+ SB1->B1_COD,.T.)
               While xFilial("SC7")+' '+SB1->B1_COD == SC7->C7_FILIAL + SC7->C7_ENCER + SC7->C7_PRODUTO  .And. !Eof()
                  nQteSc7 := nQteSc7 + SC7->C7_QUANT
                  DbSkip()
               EndDo
               If nQteSc1+nQteSc7+nQteSc8<SB1->B1_ESTSEG
                  nQteDif := SB1->B1_ESTSEG - (nQteSc1+nQteSc7+nQteSc8)
                  nItem := nItem + 1
                  Aadd(aItem, { StrZero(nItem,2),SB1->B1_COD,SB1->B1_UM,nQteDif,dDataBase,SB1->B1_LOCPAD,"Solicitacao Gerada Automaticamente",;
                     SB1->B1_CC,SB1->B1_CONTA ,dDataBase,Left(SB1->B1_DESC,30),Subs(cUsuario,7,15),'N','001','1','000000'})
               EndIf
            EndIf
         EndIf
      EndIf
      dbSelectArea("STL")
      DbSkip()
   EndDo
   For X := 1 To Len(aItem)
      tContinua := .T.
      While tContinua
         sNumSol := GetSxeNum("SC1","C1_NUM")
         confirmsx8()
         dbSelectArea("SC1")
         dbSetorder(1)
         iF !(dbSeek(xFilial("SC1")+sNumSol))
            tContinua := .F.
         EndIf
      EndDo

      dbSelectArea("SC1")
      RecLock("SC1",.T.)
      SC1->C1_FILIAL   := xFilial("SC1")
      SC1->C1_NUM      := sNumSol
      SC1->C1_ITEM     := aItem[X,1]
      SC1->C1_PRODUTO  := aItem[X,2]
      SC1->C1_UM       := aItem[X,3]
      SC1->C1_QUANT    := aItem[X,4]
      SC1->C1_DATPRF   := aItem[X,5]
      SC1->C1_LOCAL    := aItem[X,6]
      SC1->C1_OBS      := aItem[X,7]
      SC1->C1_CC       := aItem[X,8]
      SC1->C1_CONTA    := aItem[X,9]
      SC1->C1_EMISSAO  := aItem[X,10]
      SC1->C1_DESCRI   := aItem[X,11]
      SC1->C1_SOLICIT  := IIF(Empty(Alltrim(aItem[X,12])),"PORTAL INTERNO",Alltrim(aItem[X,12]))
      SC1->C1_IMPORT   := aItem[X,13]
      SC1->C1_CODCOMP  := aItem[X,14]
      SC1->C1_CLASS    := aItem[X,15]
      SC1->C1_USER     := IIF(Empty(Alltrim(aItem[X,16])),"PORTAL INTERNO",Alltrim(aItem[X,16]))
      MsUnlock("SC1")
   Next
Return
