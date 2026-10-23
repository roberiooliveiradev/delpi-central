
#INCLUDE "PROTHEUS.CH"
/*
nItem,aNfItem[nItem][IT_BASEIPI],aNfItem[nItem][IT_ALIQIPI],aNfItem[nItem][IT_VALIPI]
*/
User Function MaIPIVeic()
    Local nItem      := PARAMIXB[1] //Número do Item
    Local nAliqIPI   := PARAMIXB[3]   // Retorna o percentual de alíquota do IPI.
    Local nBaseIPI   := PARAMIXB[2]   // Retorna a base de cálculo do IPI.
    Local nValIPI    := PARAMIXB[4]   // Retorna o Valor do IPI
    //  Local cProduto   := PARAMIXB[2] //Código do Produto
    //  Local cTes       := PARAMIXB[3] //Código da TES
    //  Local cCliFor    := PARAMIXB[4] //Tipo de Participante (C = Cliente/F = Fornecedor)65425l
    //  Local cCodCliFor := PARAMIXB[5] //Código do Participante
    //  Local cLoja      := PARAMIXB[6] //Código da Loja do Participante
    //  Local cOperNF    := PARAMIXB[7] //Operação da Nota Fiscal (E = Entrada/S = Saída)
    Local aRet     := {}
    //Local cCalcIPI := "" // S=Calcula IPI; N=Não Calcula IPI.
    Local nPosItem		:= Nil// GetPosSD1("D1_ITEM")
    Local lProcAuto := iif(TYPE("L103GAUTO")!="U",L103GAUTO,.F.)

    /*

    Faça seu cálculo aqui: À partir desse ponto de entrada, é possível acessar o aCols e o aHeader do Pedido.

    */

    //XX dbSelectArea("SF4")
    // SF4->(dbSetOrder(1))
    // SF4->(DbSeek(xFilial("SF4")+cTes))
    // cCalcIPI := SF4->F4_CODIGO
    IF  FwIsInCallStack("COMXCOL") .and. nValIPI > 0 .AND. lProcAuto  .and. alltrim(cEmpAnt) $"05_01"
        nPosItem		:=GetPosSD1("D1_ITEM")
        dbSelectArea("SDT")
        SDT->(DbSetOrder(8))
        If SDT->(DbSeek(xFilial("SDT") + CA100FOR + CLOJA+ CNFISCAL +CSERIE + aCols[nItem,nPosItem] ))
            IF  SDT->DT_XMLIPI !=  nValIPI
                CONOUT("STOP")
                nValIPI := SDT->DT_XMLIPI
            ENDIF
        ENDIF
        aAdd(aRet, nBaseIPI )
        aAdd(aRet, nAliqIPI )
        aAdd(aRet, nValIPI )
    ELSE
        aAdd(aRet, nBaseIPI )
        aAdd(aRet, nAliqIPI )
        aAdd(aRet, nValIPI )
    ENDIF
Return aRet
