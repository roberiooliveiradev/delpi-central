

//		ExecBlock("A140IGRV",.F.,.F.,{cDoc,cSerie,cCodigo,cLoja,oXml})


#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"

User Function A140IGRV()
    lOCAL aArea     := getarea()
    lOCAL aAreaSC7 := SC7->(getarea())
    lOCAL aAreaSDS := SDS->(getarea())
    Local cDoc   := ParamIxb[1] // Numero da Nota
    Local cSerie := ParamIxb[2] // Série da Nota
    Local cCod   := ParamIxb[3] // Código do Fornecedor
    Local cLoja   := ParamIxb[4] // Loja do Fornecedor// Customização de usuário.....
    Local oXMLNFEImp   := ParamIxb[5] // Loja do Fornecedor// Customização de usuário.....
    lOCAL N1
    Local lBenef := .f.
    if ALLTRIM(SDS->DS_TIPO) == "B"
        lBenef := .t.
    endif
    aItens := IIF(ValType(oXMLNFEImp:_InfNfe:_Det) == "O",{oXMLNFEImp:_InfNfe:_Det},oXMLNFEImp:_InfNfe:_Det)
    conout("stop Gabriel")
    aRefImpSC7 := MaFisRelImp('MT100',{"SC7"})
    For N1 := 1 to Len(aItens)

        SDT->(dbSetOrder(8))          //8 - DT_FILIAL, DT_FORNEC, DT_LOJA, DT_DOC, DT_SERIE, DT_ITEM, R_E_C_N_O_, D_E_L_E_T_
        If	SDT->( DbSeek(xFilial("SDT")+cCod+cLoja+PADr(alltrim(cDoc),TamSx3("DT_DOC")[1])+PADr(alltrim(cSerie),TamSx3("DT_SERIE")[1])+STRZERo(N1,GETSX3CACHE("DT_ITEM","X3_TAMANHO")) ))

            /*Gravação do cBnef*/
            If XmlChildEx(aItens[N1]:_PROD,"_CBENEF")<>Nil
                cCodAju := PADL(alltrim(aItens[N1]:_Prod:_cBenef:Text),TamSx3("DT_ZCODAJU")[1],'0')
                if !Empty(cCodAju)
                    RecLock("SDT",.F.)
                    SDT->DT_ZCODAJU := cCodAju
                    SDT->(MsUnLock())
                endif
                if lBenef
                    cProd   :=  SDT->DT_COD
                    cCST    :=  RIGHT(SDT->DT_CLASFIS,2)
                    // cCodAju :=  SDT->DT_ZCODAJU
                    cCodReg :=  "000180"
                    cIFComp :=  "CBENEF"
                    cCFOPEnt := ""

                    dbSelectArea("SF4")
                    SF4->(dbSetOrder(1))
                    (SF4->(MsSeek(xFilial("SF4")+"085")))
                    cCFent := SF4->F4_CF
                    cCFRet :=posicione("SF4",1,xFilial("SF4")+F4_TESDV,"F4_CF")
                    dbSelectArea("SA1")
                    SA1->(dbSetOrder(1))
                    SA1->(dBSeek(xFilial("SA1")+SDS->DS_FORNEC+SDS->DS_LOJA))
                    aDadosCfo :={}
                    AAdd( aDadosCfo, { "OPERNF", "E" } )
                    AAdd( aDadosCfo, { "TPCLIFOR", SA1->A1_TIPO } )
                    AAdd( aDadosCfo, { "UFDEST", SA1->A1_EST } )
                    AAdd( aDadosCfo, { "INSCR", SA1->A1_INSCR } )

                    cCFOPEnt := MaFisCfo( NIL, cCFent, aDadosCfo )

                    aDadosCfo :={}
                    AAdd( aDadosCfo, { "OPERNF", "S" } )
                    AAdd( aDadosCfo, { "TPCLIFOR", SA1->A1_TIPO } )
                    AAdd( aDadosCfo, { "UFDEST", SA1->A1_EST } )
                    AAdd( aDadosCfo, { "INSCR", SA1->A1_INSCR } )

                    cCFRet := MaFisCfo( NIL, cCFRet, aDadosCfo )

                    DbSelectArea("F3K")
                    F3K->(DbSetOrder(4)) //F3K_FILIAL'+F3K_PROD+F3K_CFOP+F3K_CODAJU+F3K_CST+F3K_CODREF
                    If !F3K->(DbSeek(xFilial("F3K")+cProd+cCFOPEnt+cCodAju+cCST+cCodReg))

                        If F3K->(DbSeek(xFilial("F3K")+cProd))

                            oModel := FWLoadModel("FISA140")
                            oModel:SetOperation(4)
                            oModel:Activate()
                            //oModel:AddGrid( 'F3KDETAIL','MODEL_F3K', oStruF3K2)

                            //cDesc :=  PADR("GERADO VIA ROTINA AUTOMATICA",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
                            oMDF3KCab := oModel:GetModel("MODEL_F3K")
                            oMDF3KDet := oModel:GetModel("F3KDETAIL")
                            if oMDF3KDet:SeekLine({{"F3K_CFOP",cCFRet},{"F3K_CODAJU",cCodAju};
                                    ,{"F3K_CST",cCST}})
                                oMDF3KDet:SetValue("F3K_CODREF" ,cCodReg)
                            else
                                oMDF3KDet:AddLine()

                                oMDF3KDet:SetValue("F3K_CFOP"   ,cCFRet)
                                oMDF3KDet:SetValue("F3K_CODAJU" ,cCodAju)
                                oMDF3KDet:SetValue("F3K_CST"    ,cCST)
                                oMDF3KDet:SetValue("F3K_CODREF" ,cCodReg)
                                oMDF3KDet:SetValue("F3K_IFCOMP" ,cIFComp)
                            endif

                            if oMDF3KDet:SeekLine({{"F3K_CFOP",cCFOPEnt},{"F3K_CODAJU",cCodAju};
                                    ,{"F3K_CST",cCST}})
                                oMDF3KDet:SetValue("F3K_CODREF" ,cCodReg)
                            else
                                oMDF3KDet:AddLine()

                                oMDF3KDet:SetValue("F3K_CFOP"   ,cCFOPEnt)
                                oMDF3KDet:SetValue("F3K_CODAJU" ,cCodAju)
                                oMDF3KDet:SetValue("F3K_CST"    ,cCST)
                                oMDF3KDet:SetValue("F3K_CODREF" ,cCodReg)
                                oMDF3KDet:SetValue("F3K_IFCOMP" ,cIFComp)
                            endif

                            If oModel:VldData()

                                If oModel:CommitData()

                                EndIf

                            EndIf


                        EndIf

                    Endif
                Endif
            endif


            If XmlChildEx(aItens[N1]:_PROD,"_XPED")<>Nil .and.  XmlChildEx(aItens[N1]:_PROD,"_NITEMPED")<>Nil
                cPedXML := PADL(alltrim(aItens[N1]:_Prod:_xPed:Text),TamSx3("DT_PEDIDO")[1],'0')
                cITPedXML := PADL(alltrim(aItens[N1]:_Prod:_nItemPed:Text),TamSx3("DT_ITEMPC")[1],'0')
                IF EMPTY(SDT->DT_PEDIDO) .AND. !EMPTY(cPedXML)

                    DbSelectArea("SC7")
                    DbSetOrder(1)
                    If MsSeek(xFilial("SC7")+cPedXML+cITPedXML)
                        If	SC7->C7_FORNECE == cCod .And. SC7->C7_LOJA == cLoja .And.;
                                SC7->C7_PRODUTO == SDT->DT_COD .And.;
                                (SC7->C7_QUANT - SC7->C7_QUJE - SC7->C7_QTDACLA) > 0 .And.;
                                SC7->C7_ENCER != "E" .And. SC7->C7_RESIDUO != "S"

                            RecLock("SDT",.F.)

                            SDT->DT_PEDIDO	:= cPedXML
                            SDT->DT_ITEMPC	:= cITPedXML
                            SDT->DT_TES	    := SC7->C7_TES
                            nLoop := VAL(SC7->C7_ITEM)
                            SDT->DT_TESIPI 	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_VALIPI"})][2]) // aScan(aRefImpSC7, {|x| x[3] == "IT_VALIPI"})  //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIPI"})][3]
                            SDT->DT_TESICM 	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_VALICM"})][2]) //MaFisRet(nLoop,"IT_VALICM")  //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALICM"})][3]
                            SDT->DT_TESISS 	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_VALISS"})][2]) //MaFisRet(nLoop,"IT_VALISS")  //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALISS"})][3]
                            SDT->DT_TESPIS 	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_VALPS2"})][2]) //MaFisRet(nLoop,"IT_VALPS2")  //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIMP6"})][3]
                            SDT->DT_TESCOF 	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_VALCF2"})][2]) //MaFisRet(nLoop,"IT_VALCF2")  //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIMP5"})][3]
                            SDT->DT_TESICST	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_VALSOL"})][2]) //MaFisRet(nLoop,"IT_VALSOL")  //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ICMSRET"})][3]
                            SDT->DT_ALIQIPI	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_ALIQIPI"})][2])  // MaFisRet(nLoop,"IT_ALIQIPI") //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_IPI"})][3]
                            SDT->DT_ALIQICM	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_ALIQICM"})][2])  // MaFisRet(nLoop,"IT_ALIQICM") //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_PICM"})][3]
                            SDT->DT_ALIQISS	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_ALIQISS"})][2])  // MaFisRet(nLoop,"IT_ALIQISS") //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALIQISS"})][3]
                            SDT->DT_ALIQPIS	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_ALIQPS2"})][2])  // MaFisRet(nLoop,"IT_ALIQPS2") //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALQIMP6"})][3]
                            SDT->DT_ALIQCOF	:= &("SC7->"+aRefImpSC7[aScan(aRefImpSC7, {|x| x[3] == "IT_ALIQCF2"})][2])  // MaFisRet(nLoop,"IT_ALIQCF2") //aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALQIMP5"})][3]
                            //  SDT->DT_ALIICST	:=//MaFisRet(nLoop,"IT_ALIQSOL") //IIf(SDT->DT_TESICST > 0,aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALIQSOL"})][3],0)
                            //  SDT->DT_TESIPI  := SC7->C7_IPI
                            //  SDT->DT_ALIQIPI	:= SC7->C7_VALIPI

                            SDT->DT_ORIGIN	:= "2"

                            SDT->(MsUnLock())

                            //  ColAtuImp(SDT->DT_TES	,0,.T.,SDT->(RecNo()) )

                        ENDIF
                    ENDIF
                ENDIF
            ENDIF
        ENDIF
    Next N1
    if alltrim(SDS->DS_STATUS) $ "B" .AND. ALLTRIM(SDS->DS_TIPO) == "B"

        RecLock("SDS",.F.)
        SDS->DS_STATUS := "  "
        SDS->(MsUnLock())

    ENDIF

    restarea(aArea    )
    restarea(aAreaSC7 )
    restarea(aAreaSDS )

Return



