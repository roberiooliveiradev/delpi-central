#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"

User Function A140IPRD()

    Local cFornec   := PARAMIXB[1]
    Local cLoja     := PARAMIXB[2]
    Local cProd     := PARAMIXB[3]
    Local oDetItem  := PARAMIXB[4]
    Local cAli      := PARAMIXB[5]
    Local oXML      := PARAMIXB[6]
    Local cRet      := ""


    If cAli $ "SA7" .AND. cFornec == "000001" //WEG
        If cAli $ "SA7"
            cCampo1 := "A7_PRODUTO"
            cCampo2 := "A7_FILIAL"
            cCampo3 := "A7_CLIENTE"
            cCampo4 := "A7_LOJA"
            cCampo5 := "A7_CODCLI"

        Else
            //-- Processa cabeçalho e itens
            cCampo1 := "A5_PRODUTO"
            cCampo2 := "A5_FILIAL"
            cCampo3 := "A5_FORNECE"
            cCampo4 := "A5_LOJA"
            cCampo5 := "A5_CODPRF"
        EndIf

        cProdQRY := CVALTOCHAR(VAL(cProd))
        //StrTran(AllTrim(UPPER(StrTran(aItens[nX]:_Prod:_cProd:Text,"'"))), " ")
        cQuery := "SELECT " +cCampo1 + " FROM " +RetSqlName(cAli)
        cQuery += " WHERE D_E_L_E_T_ = ' ' AND "
        cQuery += cCampo2 +" = '" +xFilial(cAli) +"' AND "
        cQuery += cCampo3 +" = '" +cFornec +"' AND "
        cQuery += cCampo4 +" = '" +cLoja +"' AND "
        cQuery += "Replace(Upper("+cCampo5+"), ' ','') = '" +cProdQRY +"' AND "
        cQuery += cCampo1 +" <> ' '"

        If Select("TRB") > 0
            TRB->(dbCloseArea())
        EndIf

        TcQuery cQuery new Alias "TRB"

        If !TRB->(EOF())
            cRet := TRB->(&cCampo1)
        EndIf
    EndIf
Return cRet
