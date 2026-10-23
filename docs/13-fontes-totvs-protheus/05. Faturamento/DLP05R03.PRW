
#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"
#DEFINE POS_FILIAL      01
#DEFINE POS_COD_TAB     02  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A NUMERO DA NOTA
#DEFINE POS_DESC_TAB    03  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A SERIE  DA NOTA
#DEFINE POS_ID_FORM     04
#DEFINE POS_CLIENTE     05
#DEFINE POS_DSC_CLI     06
#DEFINE POS_NF          07
#DEFINE POS_SER_NF      08
#DEFINE POS_EMISSAO     09  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A DATA DE DIGITAÇÃO
#DEFINE POS_PRODUTO     10  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A DATA DE EMISSÃO
#DEFINE POS_DESC_PROD   11  // [QUANTIDADE],
#DEFINE POS_QTD         12  //[PRC_VENDA_NF_SAIDA],
#DEFINE POS_PRC_VND_NF  13  //[PRC_UNIT_NF_SAIDA],
#DEFINE POS_PRC_UNIT_NF 14  // [PRC_TABELA_VENDA],
#DEFINE POS_PRC_TABELA  15  //CUSTO_NF_SAIDA
#DEFINE POS_CUSTO_NF    16  //CUSTO_MP_FORMACAO_PLANILHA_VENDA
#DEFINE POS_CUST_FORM   17
/*#DEFINE POS_     12 //EMISSAO
#DEFINE POS_     13
#DEFINE POS_     14
#DEFINE POS_     15
#DEFINE POS_     16
#DEFINE POS_     17
#DEFINE POS_     18
#DEFINE POS_     19

#DEFINE  POS_NFE_FILIAL        01
#DEFINE  POS_NFE_FORNECE       02
#DEFINE  POS_NFE_LOJA          03
#DEFINE  POS_NFE_NM_FORNECE    04
#DEFINE  POS_NFE_DOC           05
#DEFINE  POS_NFE_SERIE         06
#DEFINE  POS_NFE_DIGIT         07
#DEFINE  POS_NFE_EMISSAO       08
#DEFINE  POS_NFE_PRODUTO       09
#DEFINE  POS_NFE_DESCRICAO     10
#DEFINE  POS_NFE_QUANT         11
#DEFINE  POS_NFE_V_UNIT        12
#DEFINE  POS_NFE_TOTAL         13
#DEFINE  POS_NFE_PRC_TAB       14
#DEFINE  POS_NFE_VLR_ULT_COMP  15
#DEFINE  POS_NFE_INF_ULT_COMP  16*/

/*/{Protheus.doc} DLP02R01
    Relatorio solicitado pela Joici em 06/2023 com o objetivo de otimizar as analises gerenciais de fechamento mensal;.
    retorna uma planilha com duas abas

    Aba CTE => Lista todos os CTE'S  e as Respectivas notas de Origem
    Aba Compras => Lista as Entradas de notas Comparando o Preco de tabela e o Ultimo preço de compra


    @type  Function
    @author Gabriel Araujo
    @since 10/06/2023
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
User Function DLP05R03()

    local   aButtons    := {}
    Local   dDataGer    := Date()
    Local   cHoraGer    := Time()
    Local   cTit        := "FATURAMENTO_"+dToS(dDataGer) + "_" + StrTran(cHoraGer, ':', '-')
    Local   cArquivo    := GetTempPath()+cTit+".rel"
    Local   cPerg       := "DLP05R03"
    Local   cArq2       := GetTempPath()+cTit+".xlsx"
    Private aSelFil     := {}
    Private cEol        := CHR(10)
    Private aOPCCTD     := {}
    Private aOPCBanco   := {}
    Private aSCANBCO    := {}
    Private aSCANCTD    := {}
    Private aRetBCO     := {}
    Private aRetCTD     := {}
    Private cStrRetBCO  := ""
    Private cStrRetCTD  := ""
    Private nSldBUIni   := 0.00
    Private aParBox     := {}
    Private oFileW      := FwFileWriter():New(cArquivo)
    Private oPrtXlsx    := FwPrinterXlsx():New()
    Private aBUPos      := {}
    Private cFormatVlr  := "R$ #,##0.00000;[Red]-R$ #,##0.00000"
    Private cFormatQtd  := "#,##0.00000000;[Red]-#,##0.00000000"
    Private cFormQtd2  :=  "#,##0.0000;[Red]-#,##0.0000" //"0,0000%;[Red]-0,0000%"
    Private cFormatDt :="dd/mm/yyyy"
    //Private cFormatPer  := "% #,##0.00;[Red]-% #,##0.00"

    Private oCellHorAlign  := FwXlsxCellAlignment():Horizontal()
    Private oCellVertAlign := FwXlsxCellAlignment():Vertical()
    Private cHorAlignment  := oCellHorAlign:Center()
    Private cHorAlignLeft  := oCellHorAlign:Left()
    Private cVertAlignment := oCellVertAlign:Center()
    Private cStyleBord     := FwXlsxBorderStyle():Thin() // estilo da borda fino
    Private cCLRWhite      := "ffffff" // branco
    Private cCLRGray       := "C0C0C0" // cinza
    Private cCLRGray1      := "d1d1d1" // cinza
    Private cCLRDelpi      := "003867" // azul
    Private cCLRBlk        := "0d0c0c" //preto
    /*Variaveis Privadas para ser atribuidas aos parametros informados pelo usuario*/
    Private cPPrdDe        :=  SPACE(GETSX3CACHE("B1_COD","X3_TAMANHO"))
    Private cPIdFrmDe      :=  SPACE(GETSX3CACHE("Z9_IDZ8","X3_TAMANHO"))
    Private cPTabDe        :=  SPACE(GETSX3CACHE("DA0_CODTAB","X3_TAMANHO"))
    Private cPDtEmiDe      :=  FirstDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O PRIMEIRO DIA DO MES ANTERIOR
    Private cPPrdAte       :=  REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO"))
    Private cPIdFrmAte     :=  REPLICATE("Z",GETSX3CACHE("Z9_IDZ8","X3_TAMANHO"))
    Private cPTabAte       :=  REPLICATE("Z",GETSX3CACHE("DA0_CODTAB","X3_TAMANHO"))
    Private cPDtEmiAte     :=  LastDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O ULTIMO DIA DO MES ANTERIOR

    PRIVATE lWrapText      := .f.
    PRIVATE lGerFinCte     := nil
    PRIVATE lGerFinNfe     := nil
    PRIVATE nRotation      := 0
    aPergs := {}
    /*Construção de parametros de perguntas. Para nao utilizar o Grupo de Perguntas*/
    aAdd(aPergs, {1, "Produto De"       , cPPrdDe   , "@!", ".T.", "SB1", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Produto Ate"      , cPPrdAte  , "@!", ".T.", "SB1", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Id Form Prd De"   , cPIdFrmDe , "@!", ".T.", "SZ9", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Id Form Prd Ate"  , cPIdFrmAte, "@!", ".T.", "SZ9", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Tabela De"        , cPTabDe    , "@!", ".T.", "DA0", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Tabela Ate"       , cPTabAte  , "@!", ".T.", "DA0", ".T." , 80,  .F.})

    aAdd(aPergs, {1, "Emissão De"   ,   cPDtEmiDe   , "", ".T.", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Emissão Até"  ,   cPDtEmiAte , "", ".T.", "", ".T.", 80,  .T.})

    IF !ParamBox(aPergs, "Informe os parâmetros",/*03*/,/*04*/,/*05*/,/*06*/,/*07*/,/*08*/,/*09*/,cPerg/*10*/,.T.,.T.)
        FWAlertError("Cancelado pelo usuario","Delpi")
        Return .F.
    ENDIF

    cPPrdDe    := MV_PAR01
    cPPrdAte   := MV_PAR02
    cPIdFrmDe  := MV_PAR03
    cPIdFrmAte := MV_PAR04
    cPTabDe    := MV_PAR05
    cPTabAte   := MV_PAR06
    cPDtEmiDe    := MV_PAR07
    cPDtEmiAte   := MV_PAR08
    lRet := oPrtXlsx:Activate(cArquivo, oFileW)
    cTmp1Ini := time()
    FWMsgRun(, {|| fProcTab1() }, "Delpi","1-Aguarde Gerando Relatorio | Analise Gerencial - Faturamento" )
    //FWMsgRun(, {|| fProcCmp1() }, "Delpi","2-Aguarde Gerando Relatorio | Analise Gerencial - Compras" )
    cTmp1Fim := time()
    cTmpTot :=ELAPTIME(cTmp1Ini,cTmp1Fim)

    conout("Processamento Inicio : "+cTmp1Ini)
    conout("Processamento Fim : "+cTmp1Fim)
    conout("Processamento total : "+cTmpTot)
    oPrtXlsx:toXlsx()
    //Abrindo o excel e abrindo o arquivo xml
    oExcel := MsExcel():New()             //Abre uma nova conexão com Excel
    oExcel:WorkBooks:Open(cArq2)     //Abre uma planilha
    oExcel:SetVisible(.T.)                 //Visualiza a planilha
    oExcel:Destroy()
RETURN


static function fProcTab1()



    Local nRow    := 1 // Linha Atual
    Local nColMax := 17 //Quantidade de Colunas
    //parametros da planilha
    cFont       := FwPrinterFont():Calibri()
    nSize       := 12
    lItalic     := .t.
    lBold       := .T.
    lUnderlined := .f.
    /*Adiciona Aba no Excel*/
    oPrtXlsx:AddSheet("Faturamento")
    //seta a fonte da planilha
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)


    /*Ajusta tamanho das Colunas*/
    // Geral 20
    nWidth := 10
    oPrtXlsx:SetColumnsWidth(1, nColMax, nWidth)

    /*Ajusta tamanho das Colunas*/
    nWidth := 15

    oPrtXlsx:SetColumnsWidth(POS_EMISSAO, POS_EMISSAO, nWidth)
    oPrtXlsx:SetColumnsWidth( POS_ID_FORM  , POS_EMISSAO, nWidth)

    nWidth := 40
    oPrtXlsx:SetColumnsWidth(POS_DESC_TAB, POS_DESC_TAB, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_DSC_CLI, POS_DSC_CLI, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_DESC_PROD  , POS_DESC_PROD  , nWidth)
    nWidth := 20
    oPrtXlsx:SetColumnsWidth(POS_QTD, POS_QTD, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_PRC_UNIT_NF, POS_PRC_UNIT_NF, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_PRC_VND_NF, POS_PRC_VND_NF, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_PRC_TABELA, POS_PRC_TABELA, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_CUSTO_NF, POS_CUSTO_NF, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_CUST_FORM, POS_CUST_FORM, nWidth)
    /* busca query para while  */
    cQryTAB := fGetQrytab()

    If Select('TMPQRY') <> 0
        TMPQRY->(dbCloseArea())
    Endif
    TCQuery cQryTAB Alias TMPQRY New
    if  TMPQRY->(!eof())
        /* inicia preenchimento da aba *\
        |  1 - titulo                   |
        \* 2 - cabeçakho               */


        //lRet := oPrtXlsx:MergeCells( nRow/*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, 5/*nColTo*/)
        oPrtXlsx:MergeCells( nRow/*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, nColMax/*nColTo*/)
        // Comando 'Formato de Célula' com cor de texto e fundo personalizada
        oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, .t. /*lWrapText*/, nRotation, cCLRDelpi /*Cor do Texto*/,cCLRGray/*Cor de Fundo*/, "" )
        // define a borda da celula
        oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .t./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk)
        oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/, "Analise Faturamento")

        nRow++ // pula linha
        //setar o nome das colunas
        oPrtXlsx:SetText(nRow /*Linha*/, POS_FILIAL         /*Coluna*/, "Filial")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_COD_TAB        /*Coluna*/, "Cod Tab Vnd")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_DESC_TAB       /*Coluna*/, "Desc Tab")
        oPrtXlsx:SetText(nRow /*Linha*/,  POS_ID_FORM         /*Coluna*/, "ID Calc Form")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CLIENTE        /*Coluna*/, "Cod Cliente")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_DSC_CLI        /*Coluna*/, "Desc Cliente")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NF             /*Coluna*/, "Nota Fiscal")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_SER_NF         /*Coluna*/, "Serie")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_EMISSAO        /*Coluna*/, "Emissao")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PRODUTO        /*Coluna*/, "Cod Prd")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_DESC_PROD      /*Coluna*/, "Desc Prd")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_QTD            /*Coluna*/, "Qtd Vend")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PRC_VND_NF     /*Coluna*/, "Prc Vend NF")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PRC_UNIT_NF    /*Coluna*/, "Prc Unit NF")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PRC_TABELA     /*Coluna*/, "Prc Tab Vend")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CUSTO_NF       /*Coluna*/, "Custo NF")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CUST_FORM      /*Coluna*/, "Custo Form Prc")

        nRow++ // pula linha

        cTmpWlIni := Time()
        WHILE  TMPQRY->(!eof())

            lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)
            // define a borda da celula  1- Primeira coluna
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )
            oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetText(nRow /*Linha*/, POS_FILIAL/*Coluna*/,  TMPQRY->D2_FILIAL)
            oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_COD_TAB/*Coluna*/     , TMPQRY->DA1_CODTAB )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_DESC_TAB/*Coluna*/     , TMPQRY->DA0_DESCRI )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_CLIENTE/*Coluna*/     , TMPQRY->D2_CLIENTE+" - "+TMPQRY->D2_LOJA )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_DSC_CLI  /*Coluna*/     , TMPQRY->A1_NOME )
            oPrtXlsx:SetText(nRow /*Linha*/,   POS_ID_FORM    /*Coluna*/     , TMPQRY->DA1_IDSZ8 )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_NF/*Coluna*/     , TMPQRY->D2_DOC)
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_SER_NF/*Coluna*/     , TMPQRY->D2_SERIE)


            oPrtXlsx:SetText(nRow /*Linha*/, POS_PRODUTO/*Coluna*/     , TMPQRY->DA1_CODPRO)
            oPrtXlsx:SetText(nRow /*Linha*/, POS_DESC_PROD/*Coluna*/     , TMPQRY->B1_DESC)
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatDt/*formato*/ )
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_EMISSAO/*Coluna*/   , stod(TMPQRY->D2_EMISSAO))

            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatQtd /*formato*/ )

            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_QTD     /*Coluna*/  , TMPQRY->D2_QUANT )

            // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )

            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_PRC_VND_NF     /*Coluna*/  , TMPQRY->D2_PRCVEN )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_PRC_UNIT_NF     /*Coluna*/  , TMPQRY->D2_PRUNIT )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_PRC_TABELA     /*Coluna*/  , TMPQRY->DA1_PRCVEN )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CUSTO_NF     /*Coluna*/  , TMPQRY->CUSTONF)


            // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            //  oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )
            oPrtXlsx:SetBorder(.F./*lLeft*/, .t./*lTop*/, .T./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CUST_FORM     /*Coluna*/  , TMPQRY->Z9_PRCLIQ)
            nRow++
            TMPQRY->(dbSkip())
        EndDo
        cTmpWlFim := Time()

        cTmpTot :=ELAPTIME(cTmpWlIni,cTmpWlFim)

        conout("WHILE Inicio : "+cTmpWlIni)
        conout("WHILE Fim : "+cTmpWlFim)
        conout("WHILE total : "+cTmpTot)
        lRet := oPrtXlsx:ApplyAutoFilter(2/*nRowFrom*/,1 /*nColFrom*/,nRow-1/*nRowTo*/,nColMax/*nColTo*/)
    EndIf
Return


/*/{Protheus.doc} fGetQryFrt1
    Objetivo: Gerar em Formatada a query  para retornar os CTEscoforme os parametros do pergunte

/*/

Static Function fGetQrytab()
    Local cRetQry := ""


    cRetQry := "SELECT DA1_CODTAB ," + cEol
    cRetQry += " DA1_IDSZ8 ," + cEol
    cRetQry += " DA1_CODPRO," + cEol
    cRetQry += " B1_DESC,"    + cEol
    cRetQry += " D2_FILIAL,"  + cEol
    cRetQry += " D2_QUANT , " + cEol // QUANTIDADE
    cRetQry += " D2_PRCVEN ," + cEol//PRC_VENDA_NF_SAIDA
    cRetQry += " D2_PRUNIT ," + cEol//PRC_UNIT_NF_SAIDA
    cRetQry += " DA1_PRCVEN ," + cEol
    cRetQry += " CASE WHEN D2_CUSTO1 > 0 " + cEol
    cRetQry += "         THEN D2_CUSTO1 / D2_QUANT " + cEol
    cRetQry += "      ELSE D2_CUSTO1" + cEol
    cRetQry += " END CUSTONF," + cEol // CUSTO_NF_SAIDA
    cRetQry += " isnull(Z9_PRCLIQ,0.00)Z9_PRCLIQ ," + cEol//CUSTO_MP_FORMACAO_PLANILHA_VENDA
    cRetQry += " D2_EMISSAO,     " + cEol
    cRetQry += " D2_DOC,      " + cEol
    cRetQry += " D2_SERIE,        " + cEol
    cRetQry += " D2_CLIENTE,      " + cEol
    cRetQry += " D2_LOJA,         " + cEol
    cRetQry += " A1_NOME,      " + cEol
    cRetQry += " DA0_DESCRI      " + cEol
    cRetQry += "FROM    dbo."+ RetSqlName("DA1") + " (NOLOCK) DA1" + cEol
    cRetQry += "join  dbo."+ RetSqlName("SB1") + " SB1  (NOLOCK) ON SB1.D_E_L_E_T_ = '' " + cEol
    cRetQry += "    AND B1_COD = DA1_CODPRO " + cEol
    cRetQry += "JOIN    dbo."+ RetSqlName("SD2") + " SD2 (NOLOCK)" + cEol
    cRetQry += "  ON SD2.D_E_L_E_T_ = '' " + cEol
    cRetQry += "      AND D2_COD = DA1_CODPRO " + cEol
    cRetQry += "      AND D2_EMISSAO >= DA1_DATVIG " + cEol
    cRetQry += "JOIN    dbo."+ RetSqlName("SF4") + " SF4 (NOLOCK) " + cEol
    cRetQry += "  ON SF4.D_E_L_E_T_ = '' " + cEol
    cRetQry += "      AND F4_FILIAL = '' " + cEol
    cRetQry += "      AND F4_CODIGO = D2_TES " + cEol
    cRetQry += "      AND F4_DUPLIC = 'S' " + cEol
    cRetQry += "JOIN   dbo."+ RetSqlName("SC5") + " SC5 " + cEol
    cRetQry += "  ON SC5.D_E_L_E_T_ = '' " + cEol
    cRetQry += "      AND C5_FILIAL = D2_FILIAL " + cEol
    cRetQry += "      AND D2_CLIENTE = C5_CLIENTE" + cEol
    cRetQry += "      AND D2_LOJA = C5_LOJACLI" + cEol
    cRetQry += "      AND C5_NUM = D2_PEDIDO " + cEol
    cRetQry += "      AND C5_TABELA = DA1_CODTAB " + cEol
    cRetQry += "join  dbo."+ RetSqlName("SA1") + " SA1 (NOLOCK) ON SA1.D_E_L_E_T_ = ''
    cRetQry += "      AND A1_FILIAL ='' " + cEol
    cRetQry += "      AND A1_COD = D2_CLIENTE " + cEol
    cRetQry += "      AND A1_LOJA = D2_LOJA " + cEol
    cRetQry += "join  dbo."+ RetSqlName("DA0") + " DA0 (NOLOCK) ON DA0.D_E_L_E_T_ = ''
    cRetQry += "      AND DA0_FILIAL =DA1_FILIAL  " + cEol
    cRetQry += "       AND DA1.DA1_CODTAB = DA0.DA0_CODTAB  " + cEol
    cRetQry += "LEFT JOIN   dbo."+ RetSqlName("SZ9") + " SZ9 (NOLOCK)" + cEol
    cRetQry += "  ON SZ9.D_E_L_E_T_ = ''" + cEol
    cRetQry += "      AND Z9_IDZ8 = DA1_IDSZ8   " + cEol
    cRetQry += "      AND Z9_IDFLD = '1PRD01'   " + cEol
    cRetQry += "      AND Z9_FILIAL = D2_FILIAL " + cEol
    cRetQry += "      AND Z9_CDPROD = '000001'  " + cEol
    cRetQry += "WHERE  DA1.D_E_L_E_T_ = '' " + cEol
    cRetQry += "    AND DA1_CODTAB  BETWEEN "+valtosql(cPTabDe)+" AND " +valtosql(cPTabAte)+ cEol
    cRetQry += "    AND DA1_CODPRO  BETWEEN "+valtosql(    cPPrdDe)+" AND " +valtosql(cPPrdAte)+ cEol
    cRetQry += "    AND DA1_IDSZ8  BETWEEN  "+valtosql(cPIdFrmDe)+" AND " +valtosql(cPIdFrmAte)+ cEol
    cRetQry += "    AND D2_EMISSAO  BETWEEN "+valtosql(cPDtEmiDe)+" AND " +valtosql(cPDtEmiAte)+ cEol
    cRetQry += "ORDER BY 1,2,3 "

Return  cRetQry


