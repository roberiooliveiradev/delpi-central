#INCLUDE "PROTHEUS.CH"

User Function MACALCICMS( )

    Local cTpOper := paramixb[1]
    Local nItem := paramixb[2]
    Local nBsICM := paramixb[3]
    Local nAliqICM := paramixb[4]
    Local nVlrICM := paramixb[5]
    Local aRet := {}
    Local nPosItem		:=NIl //GetPosSD1("D1_ITEM")
    Local lProcAuto := iif(TYPE("L103GAUTO")!="U",L103GAUTO,.F.)


    IF FwIsInCallStack("COMXCOL") .AND. nVlrICM >0 .and. lProcAuto .and. alltrim(cEmpAnt) $"05_01"
        nPosItem		:=GetPosSD1("D1_ITEM")
        dbSelectArea("SDT")
        SDT->(DbSetOrder(8))
        dbSelectArea("SA2")
        SA2->(DbSetOrder(1))

        SA2->(DbSeek(xFilial("SA2")+ CA100FOR + CLOJA ))
        cGrTrib:= SA2->A2_GRPTRIB


        If SDT->(DbSeek(xFilial("SDT") + CA100FOR + CLOJA+ CNFISCAL +CSERIE + aCols[n,nPosItem] )) .AND. 	!("SN" $ ALLTRIM(UPPER(cGrTrib))  )
            IF  SDT->DT_XMLICM !=  nVlrICM
                CONOUT("STOP")
                nVlrICM := SDT->DT_XMLICM
            ENDIF
        ENDIF
        If SDT->(DbSeek(xFilial("SDT") + CA100FOR + CLOJA+ CNFISCAL +CSERIE + aCols[n,nPosItem] )) .AND. 	("SN" $ ALLTRIM(UPPER(cGrTrib))  )
            aDadosPC := GetAdvFval("SC7",{"C7_QUANT","C7_PRECO","C7_MOEDA","C7_TXMOEDA","C7_TOTAL","C7_COND","C7_PICM","C7_VALICM"},xFilial("SF1") + PadR(SDT->DT_PEDIDO,TamSx3("C7_NUM")[1]) + PadR(SDT->DT_ITEMPC,TamSx3("C7_ITEM")[1]),1)

            IF   aDadosPC[8]!=  nVlrICM
                CONOUT("STOP")
                nVlrICM :=  aDadosPC[8]
            ENDIF
        ENDIF
        aRet := {nBsICM,nAliqICM,nVlrICM}
    ELSE
        aRet := {nBsICM,nAliqICM,nVlrICM}

    ENDIF
Return aRet
