#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"


User Function COMXPROC()
    Local lRet := .T.
    Local aDivFis	:= {}
    Local aDivNFPed	:= {}
    Local aDadosPC	:= {}
    Local aCancel	:= {}
    Local cCondPC := ""
    Local cGrTrib:= ""
    Local nVlrToler :=  0.01
    Local nVlTolert :=  0.05
    // Customização de usuário

    dbSelectArea("SA2")
    SA2->(DbSetOrder(1))

    SA2->(DbSeek(xFilial("SA2")+SDS->(DS_FORNEC+DS_LOJA)))
    cGrTrib:= SA2->A2_GRPTRIB
    dbSelectArea("SF4")
    SF4->(DbSetOrder(1))

    //  SA2->(DbSeek(xFilial("SA2")+SDS->(DS_FORNEC+DS_LOJA)))
    SDT->(DbSetOrder(1))

    SDT->(DbSeek(xFilial("SDT")+SDS->(DS_CNPJ+DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
    While !SDT->(Eof()) .And. SDT->(DT_CNPJ+DT_FORNEC+DT_LOJA+DT_DOC+DT_SERIE) == SDS->(DS_CNPJ+DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)

        SF4->(DbSeek(xFilial("SF4")+SDT->(DT_TES)))

        IF ALLTRIM(SF4->F4_CONSUMO) $ "SO"
            lMatConsumo := .T.
        ELSE
            lMatConsumo := .F.
        ENDIF
        If 	!("SN" $ ALLTRIM(UPPER(cGrTrib))  )
            If  Len(aDivFis) == 0 .And. (SDT->DT_TESIPI <> SDT->DT_XMLIPI	.Or.;
                    SDT->DT_TESICM <> SDT->DT_XMLICM	.Or.;
                    SDT->DT_TESISS <> SDT->DT_XMLISS	.Or.;
                    SDT->DT_TESICST <> SDT->DT_XMLICST	.Or.;
                    SDT->DT_ALIQIPI <> SDT->DT_XALQIPI .Or.;
                    SDT->DT_ALIQICM	<> SDT->DT_XALQICM .Or.;
                    SDT->DT_ALIQISS	<> SDT->DT_XALQISS .Or.;
                    IIF( !lMatConsumo, ( SDT->DT_ALIQPIS	<> SDT->DT_XALQPIS .Or.;
                    SDT->DT_ALIQCOF	<> SDT->DT_XALQCOF .Or.;
                    SDT->DT_TESPIS <> SDT->DT_XMLPIS	.Or.;
                    SDT->DT_TESCOF <> SDT->DT_XMLCOF), .F.)	.Or.;
                    SDT->DT_ALIICST <> SDT->DT_XALICST)

                //   If SDT->DT_ALIQICM <> SDT->DT_XALQICM
                //       lVldICMS := (Ascan(aAliqICMS,cValToChar(SDT->DT_XALQICM)) > 0)
                //   EndIf
                aAdd(aDivFis,SDS->(Recno()))
            Endif
        ELSE
            If  Len(aDivFis) == 0 .And. (SDT->DT_TESIPI <> SDT->DT_XMLIPI	.Or.;
                    SDT->DT_TESISS <> SDT->DT_XMLISS	.Or.;
                    SDT->DT_TESICST <> SDT->DT_XMLICST	.Or.;
                    SDT->DT_ALIQIPI <> SDT->DT_XALQIPI .Or.;
                    SDT->DT_ALIQISS	<> SDT->DT_XALQISS .Or.;
                    IIF( !lMatConsumo, (SDT->DT_TESPIS <> SDT->DT_XMLPIS	.Or.;
                    SDT->DT_TESCOF <> SDT->DT_XMLCOF	.Or.;
                    SDT->DT_ALIQPIS	<> SDT->DT_XALQPIS .Or.;
                    SDT->DT_ALIQCOF	<> SDT->DT_XALQCOF),.F.))

                //   If SDT->DT_ALIQICM <> SDT->DT_XALQICM
                //       lVldICMS := (Ascan(aAliqICMS,cValToChar(SDT->DT_XALQICM)) > 0)
                //   EndIf
                aAdd(aDivFis,SDS->(Recno()))
            Endif
        Endif

        If !Empty(SDT->DT_PEDIDO) .And. !Empty(SDT->DT_ITEMPC)
            aDadosPC := GetAdvFval("SC7",{"C7_QUANT","C7_PRECO","C7_MOEDA","C7_TXMOEDA","C7_TOTAL","C7_COND","C7_QUJE","C7_PICM"},xFilial("SC7") + PadR(SDT->DT_PEDIDO,TamSx3("C7_NUM")[1]) + PadR(SDT->DT_ITEMPC,TamSx3("C7_ITEM")[1]),1)

            nQtdPC := aDadosPC[1]-aDadosPC[7]
            If aDadosPC[3] <> 1 //Não é moeda Real
                nPrcPC := xMoeda(aDadosPC[2],aDadosPC[3],1,,2,aDadosPC[4],1)
            Else
                nPrcPC := aDadosPC[2]
                nPrcPCTotal := aDadosPC[5]
            Endif

            /*tratativas Condição de Pagamento*/

            If !empty(aDadosPC[6]) .and. Empty(cCondPC)
                cCondPC :=  aDadosPC[6]
            endif
            nVlrUnit :=   aDadosPC[2]
            If 	!("SN" $ ALLTRIM(UPPER(cGrTrib))  )
                IF  SDT->DT_ALIQICM != aDadosPC[8]//ALIQ ICMS
                    nPos := aScan(aDivNFPed,{|x| x[1]+x[2] == SDT->DT_DOC+SDT->DT_SERIE})
                    If nPos == 0
                        aAdd(aDivNFPed,{SDT->DT_DOC,SDT->DT_SERIE,{SDT->DT_ITEM}})
                    Else
                        aAdd(aDivNFPed[nPos,3],SDT->DT_ITEM)
                    Endif
                ENDIF
            ENDIF
            /*Condições
            1 - Se a quantidade entre o pedido e a nota é diferente e  a quantidade da nota é maior que a do pedido nao prossegue
            2 - Valor unitario Entre o Pedido de Compra é Diferente da Nota
            3 - A diferenca entre (Valor Unitario do Pedido * Quantidade Da Nota) e o Valor Total da Nota é superior a Tolerancia */
            If  (nQtdPC <> SDT->DT_QUANT .and. SDT->DT_QUANT > nQtdPC) .OR.  ABS(nVlrUnit - SDT->DT_VUNIT)>nVlrToler .or. ABS( ROUND((nVlrUnit *SDT->DT_QUANT),6)-SDT->DT_TOTAL) > nVlTolert

                //     nQtdPC <> SDT->DT_QUANT .Or. nPrcPCTotal <> SDT->DT_TOTAL
                nPos := aScan(aDivNFPed,{|x| x[1]+x[2] == SDT->DT_DOC+SDT->DT_SERIE})
                If nPos == 0
                    aAdd(aDivNFPed,{SDT->DT_DOC,SDT->DT_SERIE,{SDT->DT_ITEM}})
                Else
                    aAdd(aDivNFPed[nPos,3],SDT->DT_ITEM)
                Endif
            Endif
            If !IsBlind()
                IF  SDT->DT_VUNIT != nVlrUnit .AND.  MsgYesNo( 'Preco Unitario diferente. Ajustar?', 'Delpi' )
                    RecLock('SDT',.F.)
                    SDT->DT_VUNIT := nVlrUnit

                    SDT->(MsUnLock())
                Endif
            Endif
        Endif
        SDT->(DbSkip())
    EndDo

    oXMLPE :=COMCOLXML(SDS->DS_FILIAL,SDS->DS_DOC,SDS->DS_SERIE,SDS->DS_FORNEC,SDS->DS_LOJA)
    conout("gabriel")
    //XmlChildEx(aItens[N1]:_PROD,"_XPED")<>Nil
    // ValType(XmlChildEx(oXMLPE:_NFEPROC:_NFE:_INFNFE,"_COBR")) == "O"
    IF VALTYPE(oXMLPE)!= "U"
        IF ValType(XmlChildEx(oXMLPE:_NFEPROC:_NFE:_INFNFE,"_COBR")) != "U"
            IF ValType(XmlChildEx(oXMLPE:_NFEPROC:_NFE:_INFNFE:_COBR,"_DUP")) != "U"


                oDupl := oXMLPE:_NFEPROC:_NFE:_INFNFE:_COBR
                If ValType(oDupl:_Dup)=="A"
                    aDuplXML := oDupl:_Dup
                Else
                    aDuplXML := {oDupl:_Dup}
                EndIf
                aDupPC := Condicao(1,cCondPC,dDatabase)
                if len(aDuplXML) != len(aDupPC)
                    If !IsBlind()
                        FWAlertWarning("A NF "+SDS->DS_DOC+SDS->DS_SERIE+" Não será Gerada por Divergencias Na Forma de Pagamento", "Delpi - Imp XML")
                    EndIf
                    lRet := .F.

                EndIf
            EndIf
        EndIf
    EndIf

    if alltrim(SDS->DS_STATUS) $ "B" .AND. ALLTRIM(SDS->DS_TIPO) == "B"

        RecLock("SDS",.F.)
        SDS->DS_STATUS := "  "
        SDS->(MsUnLock())

    ENDIF

    IF LEN(aDivNFPed) > 0  .OR. LEN(aDivFis) > 0 .and. lRet

        lRet := .F.
        If !IsBlind()
            FWAlertWarning("A NF "+SDS->DS_DOC+SDS->DS_SERIE+" Não será Gerada por Divergencias", "Delpi - Imp XML")

        ENDIF
    ENDIF
Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLXML
Busca XML do documento a ser importado

@author	rodrigo.mpontes
@since		18/05/2021
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COMCOLXML(cFilSDS,cDoc,cSerie,cFornece,cLoja)

    Local oXMLCKO	:= Nil
    Local aArea		:= GetArea()
    Local cQry		:= ""
    Local cQXML		:= GetNextAlias()
    Local cXML		:= ""
    Local cXMLEncod	:= ""
    Local cError	:= ""
    Local cWarning	:= ""
    Local nPosPesq	:= 0

    cQry	:= " SELECT DS_ARQUIVO"
    cQry 	+= " FROM " + RetSqlName("SDS") + " SDS"
    cQry	+= " WHERE SDS.DS_FILIAL = '" + cFilSDS + "' "
    cQry	+= " AND SDS.DS_DOC = '" + cDoc + "' "
    cQry	+= " AND SDS.DS_SERIE = '" + cSerie + "' "
    cQry	+= " AND SDS.DS_FORNEC = '" + cFornece + "' "
    cQry	+= " AND SDS.DS_LOJA = '" + cLoja + "' "
    cQry	+= " AND SDS.D_E_L_E_T_ = ' '"

    cQry := ChangeQuery(cQry)

    dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),cQXML,.T.,.T.)

    If (cQXML)->(!EOF())
        cXML := GetAdvFVal("CKO","CKO_XMLRET",Padr((cQXML)->DS_ARQUIVO,TamSX3("CKO_ARQUIV")[1]),1)
        //GetAdvFval("CKO","CKO_XMLRET",(cQXML)->DS_ARQUIVO,1)

        If !Empty(cXML)
            If !Empty(cXML)
                If SubStr(cXML,1,1) != "<"
                    nPosPesq := At("<",cXML)
                    cXML  := SubStr(cXML,nPosPesq,Len(cXML))		// Remove caracteres estranhos antes da abertura da tag inicial do arquivo
                EndIf
            EndIf

            cXMLEncod := EncodeUtf8(cXML)

            If Empty(cXMLEncod)
                cXMLEncod 	:= cXML
                cXML 		:= A140IRemASC(cXMLEncod)
                cXMLEncod 	:= EncodeUtf8(cXML)
            EndIf

            If !Empty(cXMLEncod)
                oXMLCKO := XmlParser(cXMLEncod,"_",@cError,@cWarning)
            EndIf
        Endif
    Endif

    (cQXML)->(DbCloseArea())

    RestArea(aArea)

Return oXMLCKO
