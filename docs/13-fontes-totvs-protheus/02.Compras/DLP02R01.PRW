
#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"
#DEFINE POS_CTE_FILIAL        01
#DEFINE POS_CTE_NF_FRETE      02  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A NUMERO DA NOTA
#DEFINE POS_CTE_SER_NF_FRE    03 // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A SERIE  DA NOTA
#DEFINE POS_CTE_DT_DIGIT      04  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A DATA DE DIGITAÇÃO
#DEFINE POS_CTE_DT_EMISSAO    05 // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A DATA DE EMISSÃO
#DEFINE POS_CTE_TRANSP        06
#DEFINE POS_CTE_LJ_TRANSP     07
#DEFINE POS_CTE_NM_TRANSP     08
#DEFINE POS_CTE_NF_ORIG       09
#DEFINE POS_CTE_SET_NF_ORIG   10
#DEFINE POS_CTE_FORNECE       11
#DEFINE POS_CTE_LOJA          12
#DEFINE POS_CTE_NM_FORNECE    13
#DEFINE POS_CTE_VLR_CTE       14
#DEFINE POS_CTE_VLR_TOT_NFE   15
#DEFINE POS_CTE_CUS_CTE       16
#DEFINE POS_CTE_CUS_NFE       17
#DEFINE POS_CTE_PER_FRE       18
#DEFINE POS_CTE_TES_NFE       19

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
#DEFINE  POS_NFE_INF_ULT_COMP  16

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
User Function DLP02R01()



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
    Private cPFilDe        :=  SPACE(GETSX3CACHE("D1_FILIAL","X3_TAMANHO"))
    Private cPTranspDe     :=  SPACE(GETSX3CACHE("A4_COD","X3_TAMANHO"))
    Private cPTrpLjDe      :=  SPACE(GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPFornDe       :=  SPACE(GETSX3CACHE("A2_COD","X3_TAMANHO"))
    Private cPLjForDe      :=  SPACE(GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPDtEmiDe      :=  FirstDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O PRIMEIRO DIA DO MES ANTERIOR
    Private cPDtDgtDe      :=  FirstDate(MonthSub(DaySub(DATE(),DAY(Date()+1)),3) )  //RETORNAR O PRIMEIRO DIA DOS 3 MESES
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
    aAdd(aPergs, {1, "Transportadora De"   , cPTranspDe  , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Loja Transp De"      , cPTrpLjDe   , "@!", ".T.", "", ".T."    , 40,  .F.})
    aAdd(aPergs, {1, "Transportadora Ate"  , cPtranspAt  , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Loja Transp Ate"     , cPTrpLjAte  , "@!", ".T.", "", ".T."    , 40,  .F.})
    aAdd(aPergs, {1, "Fornecedor De"       , cPFornDe    , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Loja Fornece De"     , cPLjForDe   , "@!", ".T.", "", ".T."    , 40,  .F.})
    aAdd(aPergs, {1, "Fornecedor Ate"      , cPFornAte   , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    aAdd(aPergs, {1, "Loja Fornece Ate"     , cPLjForAte , "@!", ".T.", "", ".T."    , 40,  .F.})
    aAdd( aPergs ,{2,"CT-E Gera Financeiro ",01,{"Sim","Não","Ambos"},50,"",.F.})
    aAdd( aPergs ,{2,"NF-E Gera Financeiro ",01,{"Sim","Não","Ambos"},50,"",.F.})
    aAdd(aPergs, {1, "Emissão De"   ,   cPDtEmiDe   , "", ".T.", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Emissão Até"  ,   cPDtEmiAte , "", ".T.", "", ".T.", 80,  .T.})
    aAdd(aPergs, {1, "Digitacao De"   , cPDtDgtDe  , "", ".T.", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Digitacao Até"  , cPDtDgtAte  , "", ".T.", "", ".T.", 80,  .T.})

    IF !ParamBox(aPergs, "Informe os parâmetros",/*03*/,/*04*/,/*05*/,/*06*/,/*07*/,/*08*/,/*09*/,cPerg/*10*/,.T.,.T.)
        FWAlertError("Cancelado pelo usuario","Delpi")
        Return .F.
    ENDIF

    cPFilDe      := MV_PAR01
    cPFilAte     := MV_PAR02
    cPTranspDe   := MV_PAR03
    cPTrpLjDe    := MV_PAR04
    cPtranspAt   := MV_PAR05
    cPTrpLjAte   := MV_PAR06
    cPFornDe     := MV_PAR07
    cPLjForDe    := MV_PAR08
    cPFornAte    := MV_PAR09
    cPLjForAte   := MV_PAR10
    nGerFinCte   := MV_PAR11
    nGerFinNfe   := MV_PAR12
    cPDtEmiDe    := MV_PAR13
    cPDtEmiAte   := MV_PAR14
    cPDtDgtDe    := MV_PAR15
    cPDtDgtAte   := MV_PAR16
    lRet := oPrtXlsx:Activate(cArquivo, oFileW)
    cTmp1Ini := time()
    FWMsgRun(, {|| fProcFrt1() }, "Delpi","1-Aguarde Gerando Relatorio | Analise Gerencial - Compras" )
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
    Local nColMax := 16 //Quantidade de Colunas
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

    /*Ajusta tamanho das Colunas*/
    nWidth := 15

    oPrtXlsx:SetColumnsWidth(POS_NFE_DIGIT, POS_NFE_DIGIT, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_NFE_EMISSAO, POS_NFE_EMISSAO, nWidth)
    nWidth := 40
    oPrtXlsx:SetColumnsWidth(POS_NFE_NM_FORNECE, POS_NFE_NM_FORNECE, nWidth-10)
    oPrtXlsx:SetColumnsWidth(POS_NFE_INF_ULT_COMP, POS_NFE_INF_ULT_COMP, nWidth+25)
    oPrtXlsx:SetColumnsWidth(POS_NFE_DESCRICAO, POS_NFE_DESCRICAO, nWidth+25)
    nWidth := 20
    oPrtXlsx:SetColumnsWidth(POS_NFE_QUANT, POS_NFE_QUANT, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_NFE_V_UNIT, POS_NFE_V_UNIT, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_NFE_TOTAL, POS_NFE_TOTAL, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_NFE_VLR_ULT_COMP, POS_NFE_VLR_ULT_COMP, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_NFE_PRC_TAB, POS_NFE_PRC_TAB, nWidth)

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
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_FORNECE            /*Coluna*/, "Cod Fornece")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_LOJA               /*Coluna*/, "Lj Fornece")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_NM_FORNECE         /*Coluna*/, "Nm Fornece")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_DOC                /*Coluna*/, "N Fiscal")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_SERIE              /*Coluna*/, "Serie")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_DIGIT              /*Coluna*/, "Dt Digit")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_EMISSAO            /*Coluna*/, "Dt Emissão")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_PRODUTO            /*Coluna*/, "Produto")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_DESCRICAO          /*Coluna*/, "Descrição")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_QUANT              /*Coluna*/, "Quantidade")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_V_UNIT             /*Coluna*/, "Vlr Unitario")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_TOTAL              /*Coluna*/, "Vlr Total")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_PRC_TAB            /*Coluna*/, "Prc tabela")
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
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_NFE_DOC/*Coluna*/     , TMPQRY->D1_DOC )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_NFE_SERIE/*Coluna*/     , TMPQRY->D1_SERIE )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_NFE_FORNECE/*Coluna*/     , TMPQRY->D1_FORNECE )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_NFE_LOJA/*Coluna*/     , TMPQRY->D1_LOJA )
            oPrtXlsx:SetText(nRow /*Linha*/,  POS_NFE_NM_FORNECE/*Coluna*/     , TMPQRY->A2_NREDUZ)
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_NFE_DIGIT/*Coluna*/     , dtoc(stod(TMPQRY->D1_DTDIGIT)))
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_NFE_EMISSAO/*Coluna*/   ,  dtoc(stod(TMPQRY->D1_EMISSAO)))

            oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_PRODUTO/*Coluna*/     , TMPQRY->D1_COD)
            oPrtXlsx:SetText(nRow /*Linha*/, POS_NFE_DESCRICAO/*Coluna*/     , TMPQRY->B1_DESC)

            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatQtd /*formato*/ )

            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_NFE_QUANT     /*Coluna*/  , TMPQRY->D1_QUANT )

            // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )


            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_NFE_V_UNIT     /*Coluna*/  , TMPQRY->D1_VUNIT )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_NFE_TOTAL     /*Coluna*/  , TMPQRY->D1_TOTAL )
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


Static Function fProcFrt1()


    Local nRow    := 1 // Linha Atual
    Local nColMax := 18 //Quantidade de Colunas
    //parametros da planilha
    cFont       := FwPrinterFont():Calibri()
    nSize       := 12
    lItalic     := .t.
    lBold       := .T.
    lUnderlined := .f.
    /*Adiciona Aba no Excel*/
    oPrtXlsx:AddSheet("CTE x NF Ori")
    //seta a fonte da planilha
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)


    /*Ajusta tamanho das Colunas*/
    // Geral 20
    nWidth := 10
    oPrtXlsx:SetColumnsWidth(1, nColMax, nWidth)
    //Nome
    nWidth := 40
    oPrtXlsx:SetColumnsWidth(POS_CTE_NM_TRANSP, POS_CTE_NM_TRANSP, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_CTE_NM_FORNECE, POS_CTE_NM_FORNECE, nWidth)
    //Valores
    nWidth := 20
    oPrtXlsx:SetColumnsWidth(POS_CTE_VLR_CTE, POS_CTE_VLR_CTE, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_CTE_VLR_TOT_NFE ,POS_CTE_VLR_TOT_NFE , nWidth)
    oPrtXlsx:SetColumnsWidth(POS_CTE_CUS_CTE,POS_CTE_CUS_CTE, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_CTE_CUS_NFE,POS_CTE_CUS_NFE, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_CTE_PER_FRE,POS_CTE_PER_FRE, nWidth)




    cQryCTE := fGetQryFrt1()

    If Select('TMPQRY') <> 0
        TMPQRY->(dbCloseArea())
    Endif
    TCQuery cQryCTE Alias TMPQRY New
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
        oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/, "CT-e X Nota Fiscal Compra")

        nRow++ // pula linha

        //setar o nome das colunas
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_FILIAL/*Coluna*/, "Filial")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_NF_FRETE/*Coluna*/, "Numero CT-e")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_SER_NF_FRE/*Coluna*/, "Serie CT-e")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_DT_DIGIT/*Coluna*/, "Dt Digitação CT-e")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_DT_EMISSAO/*Coluna*/, "Dt Emissão CT-e")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_TRANSP/*Coluna*/, "Cod Transp")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_LJ_TRANSP/*Coluna*/, "Lj Transp")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_NM_TRANSP/*Coluna*/, "Transportadora")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_FORNECE     /*Coluna*/, "Cod Fornece")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_LOJA        /*Coluna*/, "Lj Fornece")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_NM_FORNECE  /*Coluna*/, "Nm Fornece")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_NF_ORIG  /*Coluna*/, "Nota Fiscal")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_SET_NF_ORIG  /*Coluna*/, "Serie")


        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_VLR_CTE     /*Coluna*/, "Vlr Tot CT-E")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_VLR_TOT_NFE /*Coluna*/, "Vlr Tot NF-e")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_CUS_CTE/*Coluna*/, "Vlr Custo CT-e")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_CUS_NFE/*Coluna*/, "Vlr Custo NF-e")
        oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_PER_FRE/*Coluna*/, "% Frete")
        // oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_TES_CTE     /*Coluna*/, "Gera Fin CT-e")
        // oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_TES_NFE     /*Coluna*/, "Gera Fin NF-e")
        //   oPrtXlsx:SetText(nRow /*Linha*/,/*Coluna*/, "")


        nRow++ // pula linha


        WHILE  TMPQRY->(!eof())

            cNMTransp :=AllTrim( POSICIONE("SA2",1,XFILIAL("SA2")+TMPQRY->F8_TRANSP +TMPQRY->F8_LOJTRAN,"A2_NREDUZ" ))
            cNMFornec :=AllTrim( POSICIONE("SA2",1,XFILIAL("SA2")+TMPQRY->F8_FORNECE +TMPQRY->F8_LOJA,"A2_NREDUZ" ))
            lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)
            // define a borda da celula  1- Primeira coluna
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )
            oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_FILIAL/*Coluna*/,  TMPQRY->F8_FILIAL)
            oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_NF_FRETE/*Coluna*/     , TMPQRY->F8_NFDIFRE )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_SER_NF_FRE/*Coluna*/   , TMPQRY->F8_SEDIFRE )
            // oPrtXlsx:SetValue(nRow, 1,  dtoc(stod(TMPQRY->D4_DATA)))
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_CTE_DT_DIGIT/*Coluna*/     , dtoc(stod(TMPQRY->F8_DTDIGIT)))
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_CTE_DT_EMISSAO/*Coluna*/   ,  dtoc(stod(TMPQRY->CTEF1_EMISSAO)))
            oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_TRANSP/*Coluna*/       , TMPQRY->F8_TRANSP )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_LJ_TRANSP/*Coluna*/    , TMPQRY->F8_LOJTRAN )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_CTE_NM_TRANSP/*Coluna*/    ,cNMTransp)
            oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_FORNECE     /*Coluna*/  , TMPQRY->F8_FORNECE )
            oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_LOJA        /*Coluna*/  , TMPQRY->F8_LOJA )
            oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_NM_FORNECE  /*Coluna*/  , cNMFornec )
            oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_NF_ORIG  /*Coluna*/     , TMPQRY->F8_NFORIG )
            oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_SET_NF_ORIG  /*Coluna*/ , TMPQRY->F8_SERORIG )
            // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CTE_VLR_CTE     /*Coluna*/  , TMPQRY->CTEF1_VALBRUT )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CTE_VLR_TOT_NFE /*Coluna*/  , TMPQRY->NFEF1_VALBRUT )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CTE_CUS_CTE/*Coluna*/  , TMPQRY->CTED1_CUSTO )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CTE_CUS_NFE/*Coluna*/  , TMPQRY->NFED1_CUSTO )
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormQtd2 /*formato*/ )


            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CTE_PER_FRE/*Coluna*/  , TMPQRY->PERFRET )


            //  // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            //  oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )
            //  oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_TES_CTE     /*Coluna*/  , TMPQRY->CTEF4_DUPLIC )
            //  oPrtXlsx:SetBorder(.F./*lLeft*/, .t./*lTop*/, .T./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            //  oPrtXlsx:SetText(nRow /*Linha*/,POS_CTE_TES_NFE     /*Coluna*/  , TMPQRY->NFEF4_DUPLIC )

            nRow++
            TMPQRY->(dbSkip())
        EndDo
        lRet := oPrtXlsx:ApplyAutoFilter(2/*nRowFrom*/,1 /*nColFrom*/,nRow-1/*nRowTo*/,nColMax/*nColTo*/)
    EndIf


Return

/*/{Protheus.doc} fGetQryCmp
    Objetivo: Gerar em Formatada a query  para retornar as notas de compras coforme os parametros do pergunte

/*/

Static Function fGetQryCmp()
    Local cRetQry := ""

    cRetQry := "SELECT D1_FILIAL,D1_FORNECE,D1_LOJA ,D1_DOC,D1_SERIE ,D1_ITEM,D1_COD,"             + cEol
    cRetQry += " D1_QUANT	 ,D1_VUNIT	 ,D1_TOTAL ,D1_EMISSAO	,D1_DTDIGIT,D1_PEDIDO	 ,"             + cEol
    cRetQry += "D1_ITEMPC	 ,C7_CODTAB ,ISNULL(AIB_PRCCOM, 0.00) AIB_PRCCOM, D1_NUMSEQ,A2_NREDUZ,B1_DESC	"             + cEol
    cRetQry += ",dbo.fncGetUltComp1(D1_COD,D1_NUMSEQ,D1_FILIAL,D1_EMISSAO) [ULTCMP],"             + cEol
    cRetQry += "dbo.fncGetUltComp2(D1_COD,D1_NUMSEQ,D1_FILIAL,D1_EMISSAO) [VLRULTC]"             + cEol
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
    cRetQry += "    LEFT JOIN SB1010 SB1 (NOLOCK)  ON SB1.D_E_L_E_T_ ='' "             + cEol
    cRetQry += "             AND B1_FILIAL = '' "             + cEol
    cRetQry += "             AND B1_COD = D1_COD "             + cEol
    cRetQry += "     LEFT JOIN SA2010 SA2 (NOLOCK)  ON SA2.D_E_L_E_T_ ='' "             + cEol
    cRetQry += "             AND A2_FILIAL = '' "             + cEol
    cRetQry += "             AND A2_COD = D1_FORNECE "             + cEol
    cRetQry += "             AND A2_LOJA = D1_LOJA"             + cEol

    cRetQry += "  WHERE SD1.D_E_L_E_T_ = ''
    cRetQry += "        AND D1_FILIAL           BETWEEN  " + valtosql(cPFilDe   ) + " AND " + VALTOSQL(cPFilAte  ) + cEol
    cRetQry += "        AND D1_FORNECE          BETWEEN  " + valtosql(cPFornDe  ) + " AND " + VALTOSQL(cPFornAte ) + cEol
    cRetQry += "        AND D1_LOJA             BETWEEN  " + valtosql(cPLjForDe ) + " AND " + VALTOSQL(cPLjForAte) + cEol

    cRetQry += "        AND SD1.D1_EMISSAO  BETWEEN  " + valtosql(cPDtEmiDe ) + " AND " + VALTOSQL(cPDtEmiAte) + cEol
    cRetQry += "        AND SD1.D1_DTDIGIT BETWEEN  " + valtosql(cPDtDgtDe ) + " AND " + VALTOSQL(cPDtDgtAte) + cEol
    cRetQry += "        AND D1_TIPO = 'N' "             + cEol
    cRetQry += "  ORDER BY 1,2,3,4,5 "

Return cRetQry
/*/{Protheus.doc} fGetQryFrt1
    Objetivo: Gerar em Formatada a query  para retornar os CTEscoforme os parametros do pergunte

/*/

Static Function fGetQryFrt1()
    Local cRetQry := ""

    // cRetQry := "SELECT F8_FILIAL,F8_NFDIFRE,F8_SEDIFRE,F8_DTDIGIT,F8_TRANSP,F8_LOJTRAN,F8_NFORIG,F8_SERORIG,"             + cEol
    // cRetQry += "        F8_FORNECE,F8_LOJA,F8_TIPO,SF1CTE.F1_VALBRUT CTEF1_VALBRUT, SF1CTE.F1_VALMERC CTEF1_VALMERC, "    + cEol
    // cRetQry += "        SF1NFE.F1_VALBRUT NFEF1_VALBRUT, SF1NFE.F1_VALMERC NFEF1_VALMERC, SD1CTE.D1_COD     CTED1_COD,"   + cEol
    // cRetQry += "        SD1CTE.D1_VUNIT   CTED1_VUNIT  , SD1CTE.D1_TOTAL   CTED1_TOTAL  , SD1CTE.D1_TES     CTED1_TES,"   + cEol
    // cRetQry += "        SD1CTE.D1_CUSTO   CTED1_CUSTO  , SD1NFE.D1_COD     NFED1_COD    , SD1NFE.D1_VUNIT   NFED1_VUNIT," + cEol
    // cRetQry += "        SD1NFE.D1_TOTAL   NFED1_TOTAL  , SD1NFE.D1_TES     NFED1_TES    , SD1NFE.D1_CUSTO   NFED1_CUSTO," + cEol
    // cRetQry += "        B1_TIPO,SF4CTE.F4_DUPLIC CTEF4_DUPLIC,SF4NFE.F4_DUPLIC NFEF4_DUPLIC,SF1CTE.F1_EMISSAO CTEF1_EMISSAO"+ cEol
    cRetQry := "SELECT F8_FILIAL,F8_NFDIFRE,F8_SEDIFRE,F8_DTDIGIT,F8_TRANSP,F8_LOJTRAN,F8_NFORIG,F8_SERORIG, "            + cEol
    cRetQry += "        F8_FORNECE,F8_LOJA,F8_TIPO,SF1CTE.F1_VALBRUT CTEF1_VALBRUT, SF1CTE.F1_VALMERC CTEF1_VALMERC, "    + cEol
    cRetQry += "        SF1NFE.F1_VALBRUT NFEF1_VALBRUT, SF1NFE.F1_VALMERC NFEF1_VALMERC, "                               + cEol
    cRetQry += "        SUM( SD1CTE.D1_CUSTO )CTED1_CUSTO, SUM(SD1NFE.D1_CUSTO)   NFED1_CUSTO, "                          + cEol
    cRetQry += "         SF1CTE.F1_EMISSAO CTEF1_EMISSAO , "                                                              + cEol
    cRetQry += "        ROUND((SUM(SD1CTE.D1_CUSTO) / SUM(SD1NFE.D1_CUSTO)) * 100, 2)[PERFRET]"          + cEol
    cRetQry += "FROM dbo."+ RetSqlName("SF8") + "  (NOLOCK) SF8 "                                                         + cEol
    cRetQry += "    LEFT JOIN dbo."+ RetSqlName("SF1") + "  (NOLOCK) SF1CTE "                                             + cEol
    cRetQry += "       ON SF1CTE.D_E_L_E_T_     = '' "                                                                    + cEol
    cRetQry += "          AND SF1CTE.F1_FILIAL  = F8_FILIAL  "                                                            + cEol
    cRetQry += "          AND SF1CTE.F1_DOC     = F8_NFDIFRE "                                                            + cEol
    cRetQry += "          AND SF1CTE.F1_SERIE   = F8_SEDIFRE "                                                            + cEol
    cRetQry += "          AND SF1CTE.F1_FORNECE = F8_TRANSP  "                                                            + cEol
    cRetQry += "          AND SF1CTE.F1_LOJA    = F8_LOJTRAN "                                                            + cEol
    cRetQry += "    LEFT JOIN dbo."+ RetSqlName("SD1") + "  (NOLOCK) SD1CTE "                                             + cEol
    cRetQry += "        ON SD1CTE.D_E_L_E_T_     = '' "                                                                   + cEol
    cRetQry += "           AND SD1CTE.D1_FILIAL  = F8_FILIAL  "                                                           + cEol
    cRetQry += "           AND SD1CTE.D1_DOC     = F8_NFDIFRE "                                                           + cEol
    cRetQry += "           AND SD1CTE.D1_SERIE   = F8_SEDIFRE "                                                           + cEol
    cRetQry += "           AND SD1CTE.D1_FORNECE = F8_TRANSP  "                                                           + cEol
    cRetQry += "           AND SD1CTE.D1_LOJA    = F8_LOJTRAN "                                                           + cEol
    cRetQry += "           AND SD1CTE.D1_NFORI   = F8_NFORIG  "                                                           + cEol
    cRetQry += "           AND SD1CTE.D1_SERIORI = F8_SERORIG "                                                           + cEol
    cRetQry += "               LEFT JOIN dbo."+ RetSqlName("SB1") + "  SB1 (NOLOCK)"                                      + cEol
    cRetQry += "                   ON SB1.D_E_L_E_T_ = ''"                                                                + cEol
    cRetQry += "                      AND B1_FILIAL  = "+VALTOSQL(XFILIAL("SB1"))                                         + cEol
    cRetQry += "                      AND B1_COD     = SD1CTE.D1_COD "                                                    + cEol
    cRetQry += "               LEFT JOIN dbo."+ RetSqlName("SF1") + "  (NOLOCK) SF1NFE "                                  + cEol
    cRetQry += "                   ON SF1NFE.D_E_L_E_T_     = '' "                                                        + cEol
    cRetQry += "                      AND SF1NFE.F1_FILIAL  = F8_FILIAL  "                                                + cEol
    cRetQry += "                      AND SF1NFE.F1_DOC     = F8_NFORIG  "                                                + cEol
    cRetQry += "                      AND SF1NFE.F1_SERIE   = F8_SERORIG "                                                + cEol
    cRetQry += "                      AND SF1NFE.F1_FORNECE = F8_FORNECE "                                                + cEol
    cRetQry += "                      AND SF1NFE.F1_LOJA    = F8_LOJA "                                                   + cEol
    cRetQry += "               LEFT JOIN dbo."+ RetSqlName("SD1") + "  (NOLOCK) SD1NFE "                                  + cEol
    cRetQry += "                   ON SD1NFE.D_E_L_E_T_     = '' "                                                        + cEol
    cRetQry += "                      AND SD1NFE.D1_FILIAL  = F8_FILIAL "                                                 + cEol
    cRetQry += "                      AND SD1NFE.D1_DOC     = F8_NFORIG "                                                 + cEol
    cRetQry += "                      AND SD1NFE.D1_SERIE   = F8_SERORIG "                                                + cEol
    cRetQry += "                      AND SD1NFE.D1_FORNECE = F8_FORNECE "                                                + cEol
    cRetQry += "                      AND SD1NFE.D1_LOJA    = F8_LOJA "                                                   + cEol
    cRetQry += "                      AND SD1CTE.D1_ITEMORI = SD1NFE.D1_ITEM "                                            + cEol
    cRetQry += "               LEFT JOIN dbo."+ RetSqlName("SF4") + "  SF4CTE (NOLOCK)"                                   + cEol
    cRetQry += "                   ON SF4CTE.D_E_L_E_T_    = '' "                                                         + cEol
    cRetQry += "                      AND SF4CTE.F4_FILIAL = "+VALTOSQL(XFILIAL("SF4"))                                   + cEol
    cRetQry += "                      AND SF4CTE.F4_CODIGO = SD1CTE.D1_TES  "                                             + cEol
    cRetQry += "               LEFT JOIN dbo."+ RetSqlName("SF4") + "  SF4NFE (NOLOCK)  "                                 + cEol
    cRetQry += "                   ON SF4NFE.D_E_L_E_T_    = '' "                                                         + cEol
    cRetQry += "                      AND SF4NFE.F4_FILIAL = "+VALTOSQL(XFILIAL("SF4"))                                   + cEol
    cRetQry += "                      AND SF4NFE.F4_CODIGO = SD1NFE.D1_TES"                                               + cEol
    cRetQry += "WHERE SF8.D_E_L_E_T_ = '' "  + cEol
    cRetQry += "        AND F8_FILIAL           BETWEEN  " + valtosql(cPFilDe   ) + " AND " + VALTOSQL(cPFilAte  ) + cEol
    cRetQry += "        AND F8_TRANSP           BETWEEN  " + valtosql(cPTranspDe) + " AND " + VALTOSQL(cPtranspAt) + cEol
    cRetQry += "        AND F8_LOJTRAN          BETWEEN  " + valtosql(cPTrpLjDe ) + " AND " + VALTOSQL(cPTrpLjAte) + cEol
    cRetQry += "        AND F8_FORNECE          BETWEEN  " + valtosql(cPFornDe  ) + " AND " + VALTOSQL(cPFornAte ) + cEol
    cRetQry += "        AND F8_LOJA             BETWEEN  " + valtosql(cPLjForDe ) + " AND " + VALTOSQL(cPLjForAte) + cEol
    cRetQry += "        AND SF1CTE.F1_EMISSAO   BETWEEN  " + valtosql(cPDtEmiDe ) + " AND " + VALTOSQL(cPDtEmiAte) + cEol
    cRetQry += "        AND SF1CTE.F1_DTDIGIT   BETWEEN  " + valtosql(cPDtDgtDe ) + " AND " + VALTOSQL(cPDtDgtAte) + cEol
    if nGerFinCte == 1
        cRetQry += "    AND SF4CTE.F4_DUPLIC  = 'S'  " + cEol
    elseif nGerFinCte == 2
        cRetQry += "    AND SF4CTE.F4_DUPLIC  = 'N'  " + cEol
    endif
    if nGerFinNfe == 1
        cRetQry += "    AND SF4NFE.F4_DUPLIC  = 'S'  " + cEol
    elseif nGerFinNfe == 2
        cRetQry += "    AND SF4NFE.F4_DUPLIC  = 'N'  " + cEol
    endif
    cRetQry += "group by F8_FILIAL,F8_NFDIFRE,F8_SEDIFRE,F8_DTDIGIT,F8_TRANSP,F8_LOJTRAN,F8_NFORIG,F8_SERORIG, " + cEol
    cRetQry += "        F8_FORNECE,F8_LOJA,F8_TIPO,SF1CTE.F1_VALBRUT , SF1CTE.F1_VALMERC ,  " + cEol
    cRetQry += "        SF1NFE.F1_VALBRUT , SF1NFE.F1_VALMERC , SF1CTE.F1_EMISSAO  " + cEol
    cRetQry += "ORDER BY 1 ,4,5 ,2 " + cEol

Return  cRetQry





/*/{Protheus.doc} fQryUltCmp
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
Static Function fQryUltCmp(cCod, cNumSeq,cFilcmp,dDtDig)

    Local cQueryComp    :=  ""
    Local aRet          :=  {}

    cQueryComp  :=  "SELECT TOP 1 SD1.*,SD1.R_E_C_N_O_"+CRLF
    cQueryComp  +=  "FROM " + RETSQLNAME("SD1") + " SD1 (nolock) "+CRLF
    cQueryComp  +=  "   JOIN " + RETSQLNAME("SF4") + " SF4 (nolock) ON "+CRLF

    if substr(cCod,1,2) $"41_51"
        cQueryComp  +=  "       SF4.D_E_L_E_T_='' AND F4_CODIGO=D1_TES  AND F4_DUPLIC ='S' "+CRLF
    ELSE
        cQueryComp  +=  "       SF4.D_E_L_E_T_='' AND F4_CODIGO=D1_TES AND F4_ESTOQUE ='S' AND F4_DUPLIC ='S' "+CRLF
    ENDIF
    cQueryComp  +=  " and F4_FILIAL = ''   and F4_TIPO = 'E' AND F4_CODIGO < '500' "+CRLF
    //cQueryComp  +=  "   JOIN " + RETSQLNAME("SF1") + " SF1 ON "+CRLF
    //cQueryComp  +=  "       SF1.D_E_L_E_T_='' AND F1_DOC=D1_DOC AND D1_LOJA = F1_LOJA  AND D1_FORNECE=F1_FORNECE"+CRLF
    //cQueryComp  +=  "	    AND D1_EMISSAO=F1_EMISSAO AND D1_SERIE=F1_SERIE AND F1_TIPO='N' AND (F1_ESPECIE='SPED' OR F1_ESPECIE='NFE') "+CRLF
    cQueryComp  +=  "WHERE D1_FILIAL='" + cFilcmp + "' " + CRLF
    cQueryComp  +=  " AND D1_COD=" +valtosql(cNumSeq) + CRLF
    cQueryComp  +=  " AND D1_DTDIGIT <=" +valtosql(dDtDig) + CRLF
    cQueryComp  +=  " AND D1_QUANT <> 0 " + CRLF
    cQueryComp  +=  " AND D1_TES <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_DOC <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_SERIE <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_FORNECE <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_LOJA <> '   ' " + CRLF
    cQueryComp  +=  "and D1_NUMSEQ < "+valtosql(cNumSeq)+" AND SD1.D_E_L_E_T_ ='' "+CRLF
    cQueryComp  +=  "ORDER BY D1_NUMSEQ DESC "

    If Select('cAlias2') > 0
        Dbselectarea('cAlias2')
        cAlias2->(DbClosearea())
    EndIf

    TcQuery cQueryComp New Alias cAlias2
    if  cAlias2->(!eof())
        //posicionar no nome do fornecedor
        DbSelectArea("SA2")
        DbSetOrder(1)
        cFornecedor := alltrim(POSICIONE("SA2",1,XFILIAL("SA2") + cAlias2->D1_FORNECE + cAlias2->D1_LOJA, "A2_NOME"))
        SA2 ->(DbClosearea())

        Return(  {;
            /*Fornc.Nome*/cAlias2->D1_FORNECE + cAlias2->D1_LOJA+" / "+ cFornecedor           ,;
            /*Loja      */cAlias2->D1_LOJA      ,;
            /*NFISCAL   */cAlias2->D1_DOC       ,;
            /*Serie     */cAlias2->D1_SERIE     ,;
            /*Quantidade*/cAlias2->D1_QUANT     ,;
            /*Vlr. Unit */cAlias2->D1_VUNIT      ,;
            /*Total     */cAlias2->D1_TOTAL     ,;
            /*Emissao   */StoD(cAlias2->D1_EMISSAO)    ;
            })
        // else
        //     aRet    := {}
    endif

Return aRet
