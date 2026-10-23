
#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"
#DEFINE  POS_NFE_FILIAL        01
#DEFINE  POS_NFE_PRODUTO        02
#DEFINE  POS_NFE_DESCRICAO           03
#DEFINE  POS_NFE_CUSTO         04
#DEFINE  POS_NFE_PRC_TAB       05
#DEFINE  POS_NFE_ICMS       06
#DEFINE  POS_NFE_VLR_ULT_COMP  07
#DEFINE  POS_NFE_INF_ULT_COMP  08

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
User Function DLP02R02()



    local   aButtons    := {}
    Local   dDataGer    := Date()
    Local   cHoraGer    := Time()
    Local   cTit        := "ANALISE_"+dToS(dDataGer) + "_" + StrTran(cHoraGer, ':', '-')
    Local   cArquivo    := GetTempPath()+cTit+".rel"
    Local   cPerg       := "DLP02R01"
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
    Private cPCodDe        :=  SPACE(GETSX3CACHE("D1_COD","X3_TAMANHO"))
    Private cPFilDe        :=  SPACE(GETSX3CACHE("D1_FILIAL","X3_TAMANHO"))
    Private cPTranspDe     :=  SPACE(GETSX3CACHE("A4_COD","X3_TAMANHO"))
    Private cPTrpLjDe      :=  SPACE(GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPFornDe       :=  SPACE(GETSX3CACHE("A2_COD","X3_TAMANHO"))
    Private cPLjForDe      :=  SPACE(GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPDtEmiDe      :=  FirstDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O PRIMEIRO DIA DO MES ANTERIOR
    Private cPDtDgtDe      :=  FirstDate(MonthSub(DaySub(DATE(),DAY(Date()+1)),3) )  //RETORNAR O PRIMEIRO DIA DOS 3 MESES
    Private cPCodAte       :=  REPLICATE("Z",GETSX3CACHE("D1_COD","X3_TAMANHO"))
    Private cPFilAte       :=  REPLICATE("Z",GETSX3CACHE("D1_FILIAL","X3_TAMANHO"))
    Private cPtranspAt     :=  REPLICATE("Z",GETSX3CACHE("A4_COD","X3_TAMANHO"))
    Private cPTrpLjAte     :=  REPLICATE("Z",GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPFornAte      :=  REPLICATE("Z",GETSX3CACHE("A2_COD","X3_TAMANHO"))
    Private cPLjForAte     :=  REPLICATE("Z",GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPDtEmiAte     :=  LastDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O ULTIMO DIA DO MES ANTERIOR
    Private cPDtDgtAte     :=  LastDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O ULTIMO DIA DO MES ANTERIOR
    PRIVATE lWrapText      := .f.
    PRIVATE lGerFinCte     := nil
    PRIVATE lGerFinNfe     := nil
    PRIVATE nRotation      := 0
    aPergs := {}
    /*Construção de parametros de perguntas. Para nao utilizar o Grupo de Perguntas*/

    aAdd(aPergs, {1, "Filial De"           , cPFilDe     , "@!", ".T.", "SM0", ".T." , 40,  .F.})
    aAdd(aPergs, {1, "Filial Ate"          , cPFilAte    , "@!", ".T.", "SM0", ".T." , 40,  .F.})
    //aAdd(aPergs, {1, "Transportadora De"   , cPTranspDe  , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    //aAdd(aPergs, {1, "Loja Transp De"      , cPTrpLjDe   , "@!", ".T.", "", ".T."    , 40,  .F.})
    //aAdd(aPergs, {1, "Transportadora Ate"  , cPtranspAt  , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    //aAdd(aPergs, {1, "Loja Transp Ate"     , cPTrpLjAte  , "@!", ".T.", "", ".T."    , 40,  .F.})
    aAdd(aPergs, {1, "Fornecedor De"       , cPFornDe    , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Loja Fornece De"     , cPLjForDe   , "@!", ".T.", "", ".T."    , 40,  .F.})
    aAdd(aPergs, {1, "Fornecedor Ate"      , cPFornAte   , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Loja Fornece Ate"     , cPLjForAte , "@!", ".T.", "", ".T."    , 40,  .F.})
    aAdd(aPergs, {1, "Produto De"           , cPCodDe     , "@!", ".T.", "SB1", ".T." , 40,  .F.})
    aAdd(aPergs, {1, "Produto  Ate"          , cPCodAte    , "@!", ".T.", "SB1", ".T." , 40,  .F.})
    // aAdd( aPergs ,{2,"CT-E Gera Financeiro ",01,{"Sim","Não","Ambos"},50,"",.F.})
    // aAdd( aPergs ,{2,"NF-E Gera Financeiro ",01,{"Sim","Não","Ambos"},50,"",.F.})
    aAdd(aPergs, {1, "Emissão De"   ,   cPDtEmiDe   , "", ".T.", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Emissão Até"  ,   cPDtEmiAte , "", ".T.", "", ".T.", 80,  .T.})
    //  aAdd(aPergs, {1, "Digitacao De"   , cPDtDgtDe  , "", ".T.", "", ".T.", 80,  .F.})
    //  aAdd(aPergs, {1, "Digitacao Até"  , cPDtDgtAte  , "", ".T.", "", ".T.", 80,  .T.})

    IF !ParamBox(aPergs, "Informe os parâmetros",/*03*/,/*04*/,/*05*/,/*06*/,/*07*/,/*08*/,/*09*/,cPerg/*10*/,.T.,.T.)
        FWAlertError("Cancelado pelo usuario","Delpi")
        Return .F.
    ENDIF

    cPFilDe      := MV_PAR01
    cPFilAte     := MV_PAR02
    cPFornDe      := MV_PAR03
    cPLjForDe     := MV_PAR04
    cPFornAte     := MV_PAR05
    cPLjForAte    := MV_PAR06
    cPCodDe := MV_PAR07
    cPCodAte:= MV_PAR08
    cPDtEmiDe   := MV_PAR09
    cPDtEmiAte  := MV_PAR10

    lRet := oPrtXlsx:Activate(cArquivo, oFileW)
    cTmp1Ini := time()
    // FWMsgRun(, {|| fProcFrt1() }, "Delpi","1-Aguarde Gerando Relatorio | Analise Gerencial - Compras" )
    FWMsgRun(, {|| fProcCmp1() }, "Delpi","2-Aguarde Gerando Relatorio | Analise Gerencial - Compras" )
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


static function fProcCmp1()



    Local nRow    := 1 // Linha Atual
    Local nColMax := 7 //Quantidade de Colunas
    //parametros da planilha
    cFont       := FwPrinterFont():Calibri()
    nSize       := 12
    lItalic     := .t.
    lBold       := .T.
    lUnderlined := .f.
    /*Adiciona Aba no Excel*/
    oPrtXlsx:AddSheet("Compras")
    //seta a fonte da planilha
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)


    /*Ajusta tamanho das Colunas*/
    // Geral 20
    nWidth := 10
    oPrtXlsx:SetColumnsWidth(1, nColMax, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_NFE_DESCRICAO, POS_NFE_DESCRICAO, 60)
    oPrtXlsx:SetColumnsWidth(POS_NFE_CUSTO, POS_NFE_CUSTO, 20)
    oPrtXlsx:SetColumnsWidth(POS_NFE_PRC_TAB, POS_NFE_PRC_TAB, 20)
    oPrtXlsx:SetColumnsWidth(POS_NFE_VLR_ULT_COMP, POS_NFE_VLR_ULT_COMP, 20)
    oPrtXlsx:SetColumnsWidth(POS_NFE_ICMS, POS_NFE_ICMS, 20)
    oPrtXlsx:SetColumnsWidth(POS_NFE_INF_ULT_COMP, POS_NFE_INF_ULT_COMP, 80)

    //
    //   /*Ajusta tamanho das Colunas*/
    //   nWidth := 15
    //
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_DIGIT, POS_NFE_DIGIT, nWidth)
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_EMISSAO, POS_NFE_EMISSAO, nWidth)
    //   nWidth := 40
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_NM_FORNECE, POS_NFE_NM_FORNECE, nWidth-10)
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_INF_ULT_COMP, POS_NFE_INF_ULT_COMP, nWidth+25)
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_DESCRICAO, POS_NFE_DESCRICAO, nWidth+25)
    //   nWidth := 20
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_QUANT, POS_NFE_QUANT, nWidth)
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_V_UNIT, POS_NFE_V_UNIT, nWidth)
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_TOTAL, POS_NFE_TOTAL, nWidth)
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_VLR_ULT_COMP, POS_NFE_VLR_ULT_COMP, nWidth)
    //   oPrtXlsx:SetColumnsWidth(POS_NFE_PRC_TAB, POS_NFE_PRC_TAB, nWidth)

    // Geral 20
    //  nWidth := 10
    //  oPrtXlsx:SetColumnsWidth(1, nColMax, nWidth)
    //  //Nome
    //  nWidth := 40
    //  oPrtXlsx:SetColumnsWidth(POS_NFE_NM_FORNECE, POS_NFE_NM_FORNECE, nWidth)
    //  oPrtXlsx:SetColumnsWidth(POS_CTE_NM_FORNECE, POS_CTE_NM_FORNECE, nWidth)
    //  //Valores
    //  nWidth := 20
    //  oPrtXlsx:SetColumnsWidth(POS_CTE_VLR_CTE, POS_CTE_VLR_CTE, nWidth)
    //  oPrtXlsx:SetColumnsWidth(POS_CTE_VLR_TOT_NFE ,POS_CTE_VLR_TOT_NFE , nWidth)
    //  oPrtXlsx:SetColumnsWidth(POS_CTE_CUS_CTE,POS_CTE_CUS_CTE, nWidth)
    //  oPrtXlsx:SetColumnsWidth(POS_CTE_CUS_NFE,POS_CTE_CUS_NFE, nWidth)

    cQryCMP := fGetQryCmp()

    If Select('TMPQRY') <> 0
        TMPQRY->(dbCloseArea())
    Endif
    TCQuery cQryCMP Alias TMPQRY New
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
        oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/, "Analise Compras")

        nRow++ // pula linha

        //setar o nome das colunas


        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_FILIAL             /*Coluna*/, "Filial")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_PRODUTO            /*Coluna*/, "Produto")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_DESCRICAO          /*Coluna*/, "Descrição")

        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_CUSTO              /*Coluna*/, "Vlr Custo Ind")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_PRC_TAB            /*Coluna*/, "Prc tabela")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_ICMS              /*Coluna*/, "% ICMS Ult Comp")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_VLR_ULT_COMP       /*Coluna*/, "Vlr Ultima Compra")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_INF_ULT_COMP       /*Coluna*/, "Inf Ultima Compra")

        nRow++ // pula linha

        cTmpWlIni := Time()
        WHILE  TMPQRY->(!eof())
            //  dbSelectArea("SA2")
            //  SA2->(dbSetOrder(1))
            //  SA2->(dbSeek(xFilial("SA2")+TMPQRY->D1_FORNECE +TMPQRY->D1_LOJA))
            //
            //  dbSelectArea("SB1")
            //  SB1->(dbSetOrder(1))
            //  SB1->(dbSeek(xFilial("SB1")+TMPQRY->D1_COD ))
            //
            //  cNMFornec :=AllTrim(SA2->A2_NREDUZ)
            //  cDescPrd  := AllTrim(SB1->B1_DESC)
            // cNMFornec :=AllTrim( POSICIONE("SA2",1,XFILIAL("SA2")+TMPQRY->D1_FORNECE +TMPQRY->D1_LOJA,"A2_NREDUZ" ))
            // cDescPrd := AllTrim( POSICIONE("SB1",1,XFILIAL("SB1")+TMPQRY->D1_COD,"B1_DESC" ))

            //  aRetCmp :=  fQryUltCmp(TMPQRY->D1_COD,TMPQRY->D1_NUMSEQ,TMPQRY->D1_FILIAL,TMPQRY->D1_DTDIGIT)
            //  aRetCmp := {}
            //  if len(aRetCmp) >0
            //      cUltCmp := aRetCmp[1]+" "+alltrim(aRetCmp[3])+"|"+alltrim(aRetCmp[4])+ dtoc(aRetCmp[8])
            //      nVLrUlt := aRetCmp[6]
            //  else
            //      cUltCmp := ""
            //      nVLrUlt := 0.00
            //  endif
            lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)
            // define a borda da celula  1- Primeira coluna
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

            oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_FILIAL/*Coluna*/,  TMPQRY->D1_FILIAL)
            oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro

            oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_PRODUTO/*Coluna*/     , TMPQRY->D1_COD)
            oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_DESCRICAO/*Coluna*/     , TMPQRY->B1_DESC)


            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormQtd2 /*formato*/ )

            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_NFE_ICMS     /*Coluna*/  , TMPQRY->PICM )
            // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )


            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_NFE_CUSTO     /*Coluna*/  , TMPQRY->BZ_CUSTO )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_NFE_PRC_TAB     /*Coluna*/  , TMPQRY->AIB_PRCCOM )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_NFE_VLR_ULT_COMP     /*Coluna*/  , TMPQRY->VLRULTC)

            // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )
            oPrtXlsx:SetBorder(.F./*lLeft*/, .t./*lTop*/, .T./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetText(nRow /*Linha*/,POS_NFE_INF_ULT_COMP     /*Coluna*/  ,  TMPQRY->ULTCMP)
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

/*/{Protheus.doc} fGetQryCmp
    Objetivo: Gerar em Formatada a query  para retornar as notas de compras coforme os parametros do pergunte

/*/

Static Function fGetQryCmp()
    Local cRetQry := ""

    cRetQry := "SELECT DISTINCT  D1_FILIAL,D1_COD,B1_DESC , BZ_CUSTD BZ_CUSTO,"             + cEol

    cRetQry += "ISNULL(AIB_PRCCOM, 0.00) AIB_PRCCOM	"             + cEol
    cRetQry += ",dbo.fncGetUltComp1(D1_COD,'ZZZZZZ',D1_FILIAL,"+VALTOSQL(cPDtEmiAte)+" ) [ULTCMP],"             + cEol
    cRetQry += "dbo.fncGetUltComp3(D1_COD,'ZZZZZZ',D1_FILIAL,'20231201' ) [PICM],"             + cEol
    cRetQry += "dbo.fncGetUltComp2(D1_COD,'ZZZZZZ',D1_FILIAL,"+VALTOSQL(cPDtEmiAte)+" ) [VLRULTC]"             + cEol
    cRetQry += "     FROM dbo."+ RetSqlName("SD1") + "  (NOLOCK) SD1 "             + cEol
    cRetQry += "    LEFT JOIN dbo."+ RetSqlName("SF4") + "  SF4NFE (NOLOCK) "             + cEol
    cRetQry += "        ON SF4NFE.D_E_L_E_T_ = '' "             + cEol
    cRetQry += "            AND SF4NFE.F4_FILIAL = '' "             + cEol
    cRetQry += "            AND SF4NFE.F4_CODIGO = SD1.D1_TES "             + cEol
    cRetQry += "    LEFT JOIN dbo."+ RetSqlName("SC7") + "  SC7 (NOLOCK) "             + cEol
    cRetQry += "        ON SC7.D_E_L_E_T_ = '' "             + cEol
    cRetQry += "            AND SD1.D1_FILIAL = SC7.C7_FILIAL "             + cEol
    cRetQry += "            AND SD1.D1_PEDIDO = SC7.C7_NUM"             + cEol
    cRetQry += "            AND SD1.D1_ITEMPC = SC7.C7_ITEM"             + cEol
    cRetQry += "            AND SC7.C7_PRODUTO = SD1.D1_COD "             + cEol
    cRetQry += "            AND SD1.D1_FORNECE = SC7.C7_FORNECE"             + cEol
    cRetQry += "            AND SD1.D1_LOJA = SC7.C7_LOJA"             + cEol
    cRetQry += "    LEFT JOIN dbo."+ RetSqlName("AIB") + "  AIB(NOLOCK) ON AIB.D_E_L_E_T_ ='' "             + cEol
    cRetQry += "            AND AIB_FILIAL = C7_FILIAL  "             + cEol
    cRetQry += "            AND AIB_CODFOR = C7_FORNECE "             + cEol
    cRetQry += "            AND AIB_LOJFOR = C7_LOJA"             + cEol
    cRetQry += "            AND AIB_CODTAB = C7_CODTAB "             + cEol
    cRetQry += "            AND AIB_CODPRO = C7_PRODUTO "             + cEol
    cRetQry += "    LEFT JOIN dbo."+ RetSqlName("SB1") + "  SB1 (NOLOCK)  ON SB1.D_E_L_E_T_ ='' "             + cEol
    cRetQry += "             AND B1_FILIAL = '' "             + cEol
    cRetQry += "             AND B1_COD = D1_COD "             + cEol
    cRetQry += "    LEFT JOIN dbo."+ RetSqlName("SBZ") + "  SBZ (NOLOCK)  ON SBZ.D_E_L_E_T_ ='' "             + cEol
    cRetQry += "             AND BZ_FILIAL =D1_FILIAL "             + cEol
    cRetQry += "             AND BZ_COD = D1_COD "             + cEol
    cRetQry += "     LEFT JOIN dbo."+ RetSqlName("SA2") + "  SA2 (NOLOCK)  ON SA2.D_E_L_E_T_ ='' "             + cEol
    cRetQry += "             AND A2_FILIAL = '' "             + cEol
    cRetQry += "             AND A2_COD = D1_FORNECE "             + cEol
    cRetQry += "             AND A2_LOJA = D1_LOJA"             + cEol

    cRetQry += "  WHERE SD1.D_E_L_E_T_ = ''
    cRetQry += "        AND D1_FILIAL           BETWEEN  " + valtosql(cPFilDe   ) + " AND " + VALTOSQL(cPFilAte  ) + cEol
    cRetQry += "        AND D1_COD           BETWEEN  " + valtosql(cPCodDe   ) + " AND " + VALTOSQL(cPCodAte  ) + cEol
    cRetQry += "        AND D1_FORNECE          BETWEEN  " + valtosql(cPFornDe  ) + " AND " + VALTOSQL(cPFornAte ) + cEol
    cRetQry += "        AND D1_LOJA             BETWEEN  " + valtosql(cPLjForDe ) + " AND " + VALTOSQL(cPLjForAte) + cEol

    cRetQry += "        AND SD1.D1_EMISSAO  BETWEEN  " + valtosql(cPDtEmiDe ) + " AND " + VALTOSQL(cPDtEmiAte) + cEol
    //cRetQry += "        AND SD1.D1_DTDIGIT BETWEEN  " + valtosql(cPDtDgtDe ) + " AND " + VALTOSQL(cPDtDgtAte) + cEol
    cRetQry += "        AND D1_TIPO = 'N' "             + cEol
    cRetQry += "  ORDER BY 1,2,3,4,5 "

Return cRetQry
