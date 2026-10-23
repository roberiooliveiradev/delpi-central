#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"


User Function COMCOLSD()
    Local ExpA1 := PARAMIXB[1]
    Local ExpA2 := PARAMIXB[2]
    Local aRet    := {}
    Local lBenef := .f.

    // Customização de usuário
    conout("gda")
    if alltrim(SDS->DS_STATUS) $ "B" .AND. ALLTRIM(SDS->DS_TIPO) == "B"
        lBenef := .t.
    endif
    SDT->(dBSetOrder(1))
    If SDT->(MsSeek(xFilial("SDT")+SDS->DS_CNPJ+SDS->DS_FORNEC+SDS->DS_LOJA+SDS->DS_DOC+SDS->DS_SERIE))
        While SDS->DS_CNPJ == SDT->DT_CNPJ .And. SDS->DS_FORNEC == SDT->DT_FORNEC .And. SDS->DS_LOJA == SDT->DT_LOJA .And. SDS->DS_DOC == SDT->DT_DOC
            // If !Empty(SDT->DT_PEDIDO)

            //       SDT->DT_TESPIS <> SDT->DT_XMLPIS	.Or.;
            //     SDT->DT_TESCOF <> SDT->DT_XMLCOF
            if SDT->DT_TESCOF> 0 .and. SDT->DT_TESCOF !=  SDT->DT_XMLCOF
                RecLock("SDT",.F.)
                SDT->DT_XMLCOF  := SDT->DT_TESCOF
                SDT->DT_XALQCOF := SDT->DT_ALIQCOF
                MsUnLock()
            EndIF

            if SDT->DT_TESPIS> 0 .and. SDT->DT_TESPIS !=  SDT->DT_XMLPIS
                RecLock("SDT",.F.)
                SDT->DT_XMLPIS := SDT->DT_TESPIS
                SDT->DT_XALQPIS := SDT->DT_ALIQPIS
                MsUnLock()
            EndIF


            if SDT->DT_TESICM> 0 .and. abs(SDT->DT_TESICM -  SDT->DT_XMLICM) == 0.01 .and. !EMPTY(SDT->DT_PEDIDO)
                RecLock("SDT",.F.)
                SDT->DT_TESICM := SDT->DT_XMLICM
                //   SDT->DT_XALQPIS := SDT->DT_ALIQPIS
                MsUnLock()


                DbSelectArea("SC7")
                DbSetOrder(1)
                If MsSeek(xFilial("SC7")+SDT->DT_PEDIDO+SDT->DT_ITEMPC)
                    RecLock("SC7",.F.)
                    SC7->C7_VALICM := SDT->DT_XMLICM
                    //   SDT->DT_XALQPIS := SDT->DT_ALIQPIS
                    MsUnLock()
                EndIF
            EndIF


            if SDT->DT_TESIPI> 0 .and. abs(SDT->DT_TESIPI -  SDT->DT_XMLIPI) == 0.01 .and. !EMPTY(SDT->DT_PEDIDO)
                RecLock("SDT",.F.)
                SDT->DT_TESIPI := SDT->DT_XMLIPI
                //   SDT->DT_XALQPIS := SDT->DT_ALIQPIS
                MsUnLock()


                DbSelectArea("SC7")
                DbSetOrder(1)
                If MsSeek(xFilial("SC7")+SDT->DT_PEDIDO+SDT->DT_ITEMPC)
                    RecLock("SC7",.F.)
                    SC7->C7_VALIPI := SDT->DT_XMLIPI
                    //   SDT->DT_XALQPIS := SDT->DT_ALIQPIS
                    MsUnLock()
                EndIF
            EndIF
            // if lBenef
            //     cProd   :=  SDT->DT_COD
            //     cCST    :=  padr(SDT->DT_CLASFIS,2)
            //     cCodAju :=  SDT->DT_ZCODAJU
            //     cCodReg :=  "0000010"
            //     cIFComp :=  "CBENEF"
            //     cCFOPEnt := ""

            //     dbSelectArea("SF4")
            //     SF4->(dbSetOrder(1))
            //     (SF4->(MsSeek(xFilial("SF4")+"085")))

            //     dbSelectArea("SA1")
            //     SA1->(dbSetOrder(1))
            //     SA1->(dBSeek(xFilial("SA1")+SDS->DS_FORNEC+SDS->DS_LOJA))
            //     aDadosCfo :={}
            //     AAdd( aDadosCfo, { "OPERNF", "S" } )
            //     AAdd( aDadosCfo, { "TPCLIFOR", SA1->A1_TIPO } )
            //     AAdd( aDadosCfo, { "UFDEST", SA1->A1_EST } )
            //     AAdd( aDadosCfo, { "INSCR", SA1->A1_INSCR } )

            //     cCFOPEnt := MaFisCfo( NIL, SF4->F4_CF, aDadosCfo )

            //     DbSelectArea("F3K")
            //     F3K->(DbSetOrder(1)) //F3K_FILIAL, F3K_PROD, F3K_CFOP, F3K_CODAJU, F3K_CST, F3K_GRCLAN, F3K_GRPLAN, F3K_GRFLAN, F3K_CODLAN, R_E_C_N_O_, D_E_L_E_T_
            //     If !F3K->(DbSeek(xFilial("F3K")+cProd+cCFOPEnt+cCodAju+cCST))

            //         If F3K->(DbSeek(xFilial("F3K")+cProd))

            //             oModel := FWLoadModel("FISA140")
            //             oModel:SetOperation(4)
            //             oModel:Activate()
            //             //oModel:AddGrid( 'F3KDETAIL','MODEL_F3K', oStruF3K2)

            //             //cDesc :=  PADR("GERADO VIA ROTINA AUTOMATICA",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
            //             oMDF3KCab := oModel:GetModel("MODEL_F3K")
            //             oMDF3KDet := oModel:GetModel("F3KDETAIL")
            //             If !F3K->(DbSeek(xFilial("F3K")+cProd+SDT->DT_CODCFOP+cCodAju+cCST))
            //                 oMDF3KDet:AddLine()

            //                 oMDF3KDet:SetValue("F3K_CFOP"   ,SDT->DT_CODCFOP)
            //                 oMDF3KDet:SetValue("F3K_CODAJU" ,cCodAju)
            //                 oMDF3KDet:SetValue("F3K_CST"    ,cCST)
            //                 oMDF3KDet:SetValue("F3K_CODREF" ,cCodReg)
            //                 oMDF3KDet:SetValue("F3K_IFCOMP" , cIFComp)

            //             EndIf
            //             oMDF3KDet:AddLine()

            //             oMDF3KDet:SetValue("F3K_CFOP"   ,cCFOPEnt)
            //             oMDF3KDet:SetValue("F3K_CODAJU" ,cCodAju)
            //             oMDF3KDet:SetValue("F3K_CST"    ,cCST)
            //             oMDF3KDet:SetValue("F3K_CODREF" ,cCodReg)
            //             oMDF3KDet:SetValue("F3K_IFCOMP" ,cIFComp)


            //             If oModel:VldData()

            //                 If oModel:CommitData()

            //                 EndIf

            //             EndIf


            //         EndIf

            //     Endif
            // Endif

            // if SDT->DT_TESIPI> 0 .and. SDT->DT_TESIPI !=  SDT->DT_XMLIPI .AND. ROUND(ABS(SDT->DT_TESIPI - SDT->DT_XMLIPI	),2) == 0.01
            //     RecLock("SDT",.F.)
            //     SDT->DT_XMLPIS := SDT->DT_TESPIS
            //     SDT->DT_XALQPIS := SDT->DT_ALIQPIS
            //     MsUnLock()
            // EndIF
            //   EndIF
            SDT-> (DbSkip())
        End
    EndIf
    // aColsAux[4][1]:cname := "BR_VERDE"
    // aColsAux[5][1]:cname := "BR_VERDE"
    // aRet := aClone(aColsAux)
    //-- Deleta cabecalho do documento
    if lBenef

        RecLock("SDS",.F.)
        SDS->DS_STATUS := "  "
        SDS->(MsUnLock())

    ENDIF
Return Nil
