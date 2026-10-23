#Include 'Protheus.ch'

User Function MTCOLSE2()

    Local aColsE2   := PARAMIXB[1] //aCols de duplicatas
    Local nOpc      := PARAMIXB[2] //0-Tela de visualização / 1-Inclusão ou Classificação
    Local n1
    IF nOpc == 1 .and. Alltrim(cEspecie) == "SPED"
        oXMLPE :=COMCOLXML(xfilial("SF1"),cNFiscal,cSerie,cA100FOR,cLoja)
        IF VALTYPE(oXMLPE) != "U"
            //SDS->DS_FILIAL,SDS->DS_DOC,SDS->DS_SERIE,SDS->DS_FORNEC,SDS->DS_LOJA)
            IF ValType(XmlChildEx(oXMLPE:_NFEPROC:_NFE:_INFNFE,"_COBR")) != "U"
                IF ValType(XmlChildEx(oXMLPE:_NFEPROC:_NFE:_INFNFE:_COBR,"_DUP")) != "U"


                    oDupl := oXMLPE:_NFEPROC:_NFE:_INFNFE:_COBR
                    If ValType(oDupl:_Dup)=="A"
                        aDuplXML := oDupl:_Dup
                    Else
                        aDuplXML := {oDupl:_Dup}
                    EndIf
                    For n1 := 1 to Len(aDuplXML)
                        IF LEN(aColsE2)>= n1
                            conout("gabriel")
                            aColsE2[n1][2] := ConvDate(aDuplXML[n1]:_dVenc:TEXT)
                            aColsE2[n1][3] :=  VAL(aDuplXML[N1]:_vDup:TEXT)

                            //_vDup
                        ENDIF
                    Next n1
                EndIf
            EndIf
        EndIf
    EndIf
    //dVenc
    conout("gabriel")
    conout("gabriel - chamou no importador")
    //Validações do cliente

Return aColsE2


Static Function ConvDate(cData)

    Local dData
    cData  := StrTran(cData,"-","")
    dData  := Stod(cData)

Return dData

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
