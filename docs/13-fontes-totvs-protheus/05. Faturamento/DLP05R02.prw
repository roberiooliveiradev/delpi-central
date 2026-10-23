#INCLUDE "Protheus.ch"
#INCLUDE "TopConn.ch"

/*/{Protheus.doc} User Function DLP05R02
    (long_description)
    @type  Function
    @author Luan Woichechoscki
    @since 04/08/2022
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
User Function DLP05R02()

    Local aPerg         :=  "DLP05R02"
    Local cPath         :=  ""


    If !Pergunte(aPerg,.t.)
        Return
    Endif

    cPath:=cGetFile( 'Arquivo XML|*.xml|'     ,;  //[ cMascara],
        'Selecao da Pasta',;                    //[ cTitulo],
        0,;                                    //[ nMascpadrao],
        ,;                                     //[ cDirinicial],
        .T.,;                                  //[ lSalvar],
        GETF_LOCALHARD + GETF_RETDIRECTORY,;   //[ nOpcoes],
        .T.)



    FWMsgRun(, {|oSay| Report(cPath,oSay) }, "Processando", "Processando dados")


Return

Static Function Report(cPath)

    Local aArea         :=  GetArea()
    Local cWorksheet1   :=  "Plan-FATxMP"
    Local cTable1       :=  "Tabela - FAT x MP"
    Local cQuery        :=  ""
    Local nTotal        :=  0
    Local lOk           :=  .F.
    Local aUltComp      :=  {}
    Local oExcel
    Local oAbreExcel

    //Construtor
    oExcel:=FwMsExcelEx():New()

    //Criando planilha
    oExcel:AddworkSheet(cWorksheet1)
    //Criando tabela
    oExcel:AddTable(cWorksheet1, cTable1,.T. /*lPrintHead*/)
    //Criando colunas
    oExcel:AddColumn(cWorksheet1, cTable1, "FILIAL"     ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "ID"         ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "IDSZ7"      ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "COD"        ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "CDPROD"     ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "TIPO"       ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "ALIQ"       ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "TABPRCC"    ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "FORNECEDOR" ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "LOJA"       ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "NF"       ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "SERIE"       ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "QUANTIDADE" ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "VLR UNIT"   ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "VLR TOTAL"  ,1/*nAlign*/, 1/*nFormat*/,.F. /*lTotal*/)
    oExcel:AddColumn(cWorksheet1, cTable1, "EMISSÃO"    ,1/*nAlign*/, 4/*nFormat*/,.F. /*lTotal*/)

    //Setando as configuracoes da Tabela
    oExcel:SetFont("arial")
    oExcel:SetFontSize(14)
    oExcel:SetItalic(.F.)
    oExcel:SetBold(.F.)
    oExcel:SetUnderline(.F.)

    //Impressao do relatorio
    cQuery  := fQuery1()
    If Select('cAlias1') > 0
        Dbselectarea('cAlias1')
        cAlias1->(DbClosearea())
    EndIf

    TcQuery cQuery New Alias cAlias1
    Count To nTotal
    cAlias1->(DbGoTop())


    IF nTotal>0
        lOk:=.T.
    ELSE
        MsgAlert('Query Vazia', 'ERRO')
        lOk:=.F.
    ENDIF





    IF lOk
        While cAlias1->(! Eof())

            //Chama função que analisa a ultima compra
            aUltComp    :=  fQueryComp(cAlias1->Z9_CDPROD)

            aLinha      :=  {;
                /*FILIAL */ cAlias1->Z8_FILIAL     ,;
                /*ID     */ cAlias1->Z8_ID         ,;
                /*IDSZ7  */ cAlias1->Z8_IDSZ7      ,;
                /*COD    */ cAlias1->Z8_COD        ,;
                /*CDPROD */ cAlias1->Z9_CDPROD     ,;
                /*TIPO   */ cAlias1->B1_TIPO       ,;
                /*ALIQ   */ cAlias1->Z9_ALIQ       ,;
                /*TABPRCC*/ cAlias1->Z9_TABPRCC     ;
                }

            //Adiciona o Array com a media e saldo do estoque ao array que será impresso
            tamanhoAtual = len(aLinha)
            asize(aLinha, tamanhoAtual + len(aUltComp))
            acopy(aUltComp, aLinha, 1, len(aUltComp), tamanhoAtual+1)

            oExcel:AddRow(cWorksheet1, cTable1,aLinha)
            cAlias1->(DbSkip())
        ENDDO

        //Gerando a planilha
        cFileName := cPath+"DLP05R02"+FWTimeStamp(1)+".xml"
        oExcel:Activate()
        oExcel:GetXMLFile(cFileName)


        oAbreExcel := MsExcel():New()             //Abre uma nova conexão com Excel
        oAbreExcel:WorkBooks:Open(cFileName)     //Abre uma planilha
        oAbreExcel:SetVisible(.T.)                 //Visualiza a planilha
        oAbreExcel:Destroy()
    ENDIF
    RestArea(aArea)
Return


/*/{Protheus.doc} fQuery1
    (long_description)
    @type  Function
    @author Luan Woichechoscki
    @since 04/08/2022
    @version version
    @param
    @return cQuery, Character, Query principal
    @example
    (examples)
    @see (links_or_references)
/*/
Static Function fQuery1()

    Local cQuery            :=  ""
    Local FILIAL_DE         :=  MV_PAR01
    Local FILIAL_ATE        :=  MV_PAR02
    Local MP_DE             :=  MV_PAR03
    Local MP_ATE            :=  MV_PAR04
    Local PA_DE             :=  MV_PAR05
    Local PA_ATE            :=  MV_PAR06
    Local FAT_DE            :=  DtoS(MV_PAR07)
    Local FAT_ATE           :=  DtoS(MV_PAR08)
    Local CLIENTE_DE        :=  MV_PAR09
    Local CLILOJA_DE        :=  MV_PAR10
    Local CLIENTE_ATE       :=  MV_PAR11
    Local CLILOJA_ATE       :=  MV_PAR12
    Local FRMPRC_DE         :=  MV_PAR13
    Local FRMPRC_ATE        :=  MV_PAR14
    Local TBPRC_DE          :=  MV_PAR15
    Local TBPRC_ATE         :=  MV_PAR16


    cQuery  :=  "SELECT DISTINCT Z8_FILIAL, Z8_ID, Z8_IDSZ7, Z8_COD, Z9_CDPROD, B1_TIPO, Z9_ALIQ, Z9_TABPRCC"+CRLF
    cQuery  +=  "   FROM " + RETSQLNAME("SZ8") + " TBL1 (nolock)"+CRLF
    cQuery  +=  "   JOIN " + RETSQLNAME("SZ9") + " SZ9 (nolock) ON SZ9.D_E_L_E_T_='' /* AND SZ9.Z9_FILIAL = ''*/ "+CRLF
    //cQuery  +=  "   AND SZ9.Z9_FILMOV=TBL1.Z8_FILIAL AND SZ9.Z9_IDZ8=TBL1.Z8_ID"+CRLF
    cQuery  +=  "   AND SZ9.Z9_FILIAL=TBL1.Z8_FILIAL AND SZ9.Z9_IDZ8=TBL1.Z8_ID"+CRLF
    cQuery  +=  "   JOIN " + RETSQLNAME("SB1") + " SB1 (nolock) ON SB1.D_E_L_E_T_='' AND SB1.B1_FILIAL='' AND B1_COD=Z9_CDPROD"+CRLF
    cQuery  +=  "   WHERE TBL1.D_E_L_E_T_=' ' AND B1_TIPO IN ('MP') AND B1_COD BETWEEN '"+MP_DE+"' AND '"+MP_ATE+"' AND(Z9_ALIQ=0 OR Z9_TABPRCC='')"+CRLF
    cQuery  +=  "       AND Z8_COD IN(SELECT D2_COD"+CRLF
    cQuery  +=  "       FROM " + RETSQLNAME("SD2") + " TBL1(nolock)"+CRLF
    cQuery  +=  "       JOIN " + RETSQLNAME("SF4") + " SF4(nolock) ON SF4.D_E_L_E_T_=' ' AND F4_FILIAL=' ' AND F4_CODIGO=D2_TES"+CRLF
    cQuery  +=  "           AND F4_DUPLIC='S'"+CRLF
    cQuery  +=  "       WHERE TBL1.D_E_L_E_T_=' ' AND D2_COD BETWEEN '"+PA_DE+"' AND '"+PA_ATE+"'"+CRLF
    cQuery  +=  "           AND D2_EMISSAO BETWEEN '"+FAT_DE+"' AND '"+FAT_ATE+"'"+CRLF

    cQuery  +=  "           AND D2_FILIAL BETWEEN '"+ FILIAL_DE +"' AND '"+ FILIAL_ATE +"'"+CRLF
    cQuery  +=  "           AND D2_CLIENTE BETWEEN '"+ CLIENTE_DE +"' AND '"+ CLIENTE_ATE +"'"+CRLF
    cQuery  +=  "           AND D2_LOJA BETWEEN '"+ CLILOJA_DE +"' AND '"+ CLILOJA_ATE +"'"+CRLF
    cQuery  +=  "           AND Z8_IDSZ7 BETWEEN '"+ FRMPRC_DE +"' AND '"+ FRMPRC_ATE +"'"+CRLF
    cQuery  +=  "           AND Z9_TABPRCC BETWEEN '"+ TBPRC_DE +"' AND '"+ TBPRC_ATE +"')"

Return cQuery


/*/{Protheus.doc} fQueryComp
    (long_description)
    @type  Function
    @author Luan Woichechoscki
    @since 04/08/2022
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
Static Function fQueryComp(cCod)

    Local cQueryComp    :=  ""
    Local aRet          :=  {}

    cQueryComp  :=  "SELECT TOP 1 SD1.*,SD1.R_E_C_N_O_"+CRLF
    cQueryComp  +=  "FROM " + RETSQLNAME("SD1") + " SD1 "+CRLF
    cQueryComp  +=  "   JOIN " + RETSQLNAME("SF4") + " SF4 ON "+CRLF
    cQueryComp  +=  "       SF4.D_E_L_E_T_='' AND F4_CODIGO=D1_TES AND F4_ESTOQUE ='S' AND F4_DUPLIC ='S' "+CRLF
    cQueryComp  +=  "   JOIN " + RETSQLNAME("SF1") + " SF1 ON "+CRLF
    cQueryComp  +=  "       SF1.D_E_L_E_T_='' AND F1_DOC=D1_DOC AND D1_LOJA = F1_LOJA  AND D1_FORNECE=F1_FORNECE"+CRLF
    cQueryComp  +=  "	    AND D1_EMISSAO=F1_EMISSAO AND D1_SERIE=F1_SERIE AND F1_TIPO='N' AND (F1_ESPECIE='SPED' OR F1_ESPECIE='NFE') "+CRLF
    cQueryComp  +=  "WHERE D1_FILIAL='" + xFilial("SD1") + "' AND D1_COD='" + cCod + "' AND D1_TES <> '   '  AND SD1.D_E_L_E_T_ ='' "+CRLF
    cQueryComp  +=  "ORDER BY D1_NUMSEQ DESC "

    If Select('cAlias2') > 0
        Dbselectarea('cAlias2')
        cAlias2->(DbClosearea())
    EndIf

    TcQuery cQueryComp New Alias cAlias2

    //posicionar no nome do fornecedor
    DbSelectArea("SA2")
    DbSetOrder(1)
    cFornecedor := POSICIONE("SA2",1,XFILIAL("SA2") + cAlias2->D1_FORNECE + cAlias2->D1_LOJA, "A2_NOME")
    SA2 ->(DbClosearea())

    aRet    :=  {;
        /*Fornc.Nome*/cAlias2->D1_FORNECE + cAlias2->D1_LOJA+"/"+ cFornecedor           ,;
        /*Loja      */cAlias2->D1_LOJA      ,;
        /*NFISCAL   */cAlias2->D1_DOC       ,;
        /*Serie     */cAlias2->D1_SERIE     ,;
        /*Quantidade*/cAlias2->D1_QUANT     ,;
        /*Vlr. Unit */cAlias2->D1_VUNIT     ,;
        /*Total     */cAlias2->D1_TOTAL     ,;
        /*Emissao   */StoD(cAlias2->D1_EMISSAO)    ;
        }


Return aRet
