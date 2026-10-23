#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"
#DEFINE  POS_FILIAL      01
#DEFINE  POS_OP_RD       02
#DEFINE  POS_ITEM_OP     03
#DEFINE  POS_SEQ_OP      04
#DEFINE  POS_PROD_PA     05
#DEFINE  POS_DESC_PA     06
#DEFINE  POS_PROD_MP     07
#DEFINE  POS_DESC_MP     08
#DEFINE  POS_QTD_ORI_OP  09
#DEFINE  POS_EMISS_OP    10
#DEFINE  POS_PRV_INI     11
#DEFINE  POS_PRV_FIM     12
#DEFINE  POS_QTD_EST     13
#DEFINE  POS_OP_FULL     14
#DEFINE  POS_QTD_PREV    15
#DEFINE  POS_QTD_PROD    16
#DEFINE  POS_CUSTO_UNIT  17
#DEFINE  POS_DT_PRD      18
#DEFINE  POS_CUSTO_REAL  19
#DEFINE  POS_CUSTO_PREV  20
#DEFINE  POS_TOT_REAL    21
#DEFINE  POS_TOT_PREV    22
#DEFINE  POS_PERC_REF    23
/*/{Protheus.doc} DLP10R02

    @type  Function
    @author Gabriel Araujo
    @since 03/2024
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
User Function DLP10R02()




    local   aButtons    := {}
    Local   dDataGer    := Date()
    Local   cHoraGer    := Time()
    Local   cTit        := "REFUGO_"+dToS(dDataGer) + "_" + StrTran(cHoraGer, ':', '-')
    Local   cArquivo    := GetTempPath()+cTit+".rel"
    Local   cPerg       := "DLP10R01"
    Local   cArq2       := GetTempPath()+cTit+".xlsx"
    Local oSay := Nil
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
    Private cFormatVlr  := "R$ #,##0.00000;[Red]-R$ #,##0.00000;-"
    Private cFormatQtd  := "#,##0.00000000;[Red]-#,##0.00000000;-"
    Private cFormQtd2  :=  "#,##0.0000;[Red]-#,##0.0000;-"
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
    Private cPOPDe        :=  SPACE(GETSX3CACHE("D3_OP","X3_TAMANHO"))
    Private cPFilDe        :=  SPACE(GETSX3CACHE("D1_FILIAL","X3_TAMANHO"))
    Private cPTranspDe     :=  SPACE(GETSX3CACHE("A4_COD","X3_TAMANHO"))
    Private cPTrpLjDe      :=  SPACE(GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPFornDe       :=  SPACE(GETSX3CACHE("A2_COD","X3_TAMANHO"))
    Private cPLjForDe      :=  SPACE(GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPDtEmiDe      :=  FirstDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O PRIMEIRO DIA DO MES ANTERIOR
    Private cPDtMVtDe      :=  FirstDate(MonthSub(DaySub(DATE(),DAY(Date()+1)),3) )  //RETORNAR O PRIMEIRO DIA DOS 3 MESES
    Private cPCodAte       :=  REPLICATE("Z",GETSX3CACHE("D1_COD","X3_TAMANHO"))
    Private cPOPAte       :=  REPLICATE("Z",GETSX3CACHE("D3_COD","X3_TAMANHO"))
    Private cPFilAte       :=  REPLICATE("Z",GETSX3CACHE("D1_FILIAL","X3_TAMANHO"))
    Private cPtranspAt     :=  REPLICATE("Z",GETSX3CACHE("A4_COD","X3_TAMANHO"))
    Private cPTrpLjAte     :=  REPLICATE("Z",GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPFornAte      :=  REPLICATE("Z",GETSX3CACHE("A2_COD","X3_TAMANHO"))
    Private cPLjForAte     :=  REPLICATE("Z",GETSX3CACHE("A2_LOJA","X3_TAMANHO"))
    Private cPDtEmiAte     :=  LastDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O ULTIMO DIA DO MES ANTERIOR
    Private cPDtMvtAte     :=  LastDate(DaySub(DATE(),DAY(Date()+1))) //RETORNAR O ULTIMO DIA DO MES ANTERIOR
    PRIVATE lWrapText      := .f.
    PRIVATE lGerFinCte     := nil
    PRIVATE lGerFinNfe     := nil
    PRIVATE nRotation      := 0
    PRIVATE nRegDe      := 0
    PRIVATE nRegAte      := 0
    aPergs := {}

    /*Construção de parametros de perguntas. Para nao utilizar o Grupo de Perguntas*/

    aAdd(aPergs, {1, "Filial De"            , cPFilDe       , "@!", ".T.", "SM0", ".T." , 40,  .F.})
    aAdd(aPergs, {1, "Filial Ate"           , cPFilAte      , "@!", ".T.", "SM0", ".T." , 40,  .F.})
    aAdd(aPergs, {1, "Emissão OP De"        , cPDtEmiDe     , "", ".T.", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Emissão OP Até"       , cPDtEmiAte    , "", ".T.", "", ".T.", 80,  .T.})
    aAdd(aPergs, {1, "Movimento OP De"      , cPDtMVtDe     , "", ".T.", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Movimento OP Até"     , cPDtEmiAte    , "", ".T.", "", ".T.", 80,  .T.})
    aAdd(aPergs, {1, "PA De"                , cPCodDe       , "@!", ".T.", "SB1", ".T." , 40,  .F.})
    aAdd(aPergs, {1, "PA  Ate"              , cPCodAte      , "@!", ".T.", "SB1", ".T." , 40,  .F.})
    aAdd(aPergs, {1, "Ordem de Prd De"      , cPOPDe        , "@!", ".T.", "SC2", ".T." , 40,  .F.})
    aAdd(aPergs, {1, "Ordem de Prd  Ate"    , cPOPAte       , "@!", ".T.", "SC2", ".T." , 40,  .F.})
    //aAdd(aPergs, {1, "Transportadora De"   , cPTranspDe  , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    //aAdd(aPergs, {1, "Loja Transp De"      , cPTrpLjDe   , "@!", ".T.", "", ".T."    , 40,  .F.})
    //aAdd(aPergs, {1, "Transportadora Ate"  , cPtranspAt  , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    //aAdd(aPergs, {1, "Loja Transp Ate"     , cPTrpLjAte  , "@!", ".T.", "", ".T."    , 40,  .F.})
    // aAdd(aPergs, {1, "Fornecedor De"       , cPFornDe    , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    // aAdd(aPergs, {1, "Loja Fornece De"     , cPLjForDe   , "@!", ".T.", "", ".T."    , 40,  .F.})
    // aAdd(aPergs, {1, "Fornecedor Ate"      , cPFornAte   , "@!", ".T.", "SA4", ".T." , 80,  .F.})
    // aAdd(aPergs, {1, "Loja Fornece Ate"     , cPLjForAte , "@!", ".T.", "", ".T."    , 40,  .F.})
    // aAdd(aPergs, {1, "Produto De"           , cPCodDe     , "@!", ".T.", "SB1", ".T." , 40,  .F.})
    // aAdd(aPergs, {1, "Produto  Ate"          , cPCodAte    , "@!", ".T.", "SB1", ".T." , 40,  .F.})
    // // aAdd( aPergs ,{2,"CT-E Gera Financeiro ",01,{"Sim","Não","Ambos"},50,"",.F.})
    // aAdd( aPergs ,{2,"NF-E Gera Financeiro ",01,{"Sim","Não","Ambos"},50,"",.F.})

    //  aAdd(aPergs, {1, "Digitacao De"   , cPDtDgtDe  , "", ".T.", "", ".T.", 80,  .F.})
    //  aAdd(aPergs, {1, "Digitacao Até"  , cPDtDgtAte  , "", ".T.", "", ".T.", 80,  .T.})

    IF !ParamBox(aPergs, "Informe os parâmetros",/*03*/,/*04*/,/*05*/,/*06*/,/*07*/,/*08*/,/*09*/,cPerg/*10*/,.T.,.T.)
        FWAlertError("Cancelado pelo usuario","Delpi")
        Return .F.
    ENDIF
    cPFilDe     := MV_PAR01
    cPFilAte    := MV_PAR02
    cPDtEmiDe   := MV_PAR03
    cPDtEmiAte  := MV_PAR04
    cPDtMVtDe   := MV_PAR05
    cPDtEmiAte  := MV_PAR06
    cPCodDe     := MV_PAR07
    cPCodAte    := MV_PAR08
    cPOPDe      := MV_PAR09
    cPOPAte     := MV_PAR10


    lRet := oPrtXlsx:Activate(cArquivo, oFileW)

    FWMsgRun(, {|oSay| fProcRel(oSay) }, "Delpi - Refugo - PCP","" )

    oPrtXlsx:toXlsx()
    //Abrindo o excel e abrindo o arquivo xml
    oExcel := MsExcel():New()             //Abre uma nova conexão com Excel
    oExcel:WorkBooks:Open(cArq2)     //Abre uma planilha
    oExcel:SetVisible(.T.)                 //Visualiza a planilha
    oExcel:Destroy()

RETURN




static function fProcRel(oSay)



    Local nRow    := 1 // Linha Atual
    Local nColMax := 23 //Quantidade de Colunas
    //parametros da planilha
    cFont       := FwPrinterFont():Calibri()
    nSize       := 12
    lItalic     := .t.
    lBold       := .T.
    lUnderlined := .f.
    /*Adiciona Aba no Excel*/
    oPrtXlsx:AddSheet("PCP")
    //seta a fonte da planilha
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)


    /*Ajusta tamanho das Colunas*/
    // Geral 20
    nWidth := 15
    oPrtXlsx:SetColumnsWidth(1, nColMax, nWidth)
    oPrtXlsx:SetColumnsWidth(POS_PROD_PA, POS_PROD_PA, 25)
    oPrtXlsx:SetColumnsWidth(POS_PROD_MP, POS_PROD_MP, 25)
    oPrtXlsx:SetColumnsWidth(POS_DESC_PA, POS_DESC_PA, 65)
    oPrtXlsx:SetColumnsWidth(POS_DESC_MP, POS_DESC_MP, 65)
    // oPrtXlsx:SetColumnsWidth(POS_PROD_MP, POS_PROD_MP, 30)
    //oPrtXlsx:SetColumnsWidth(POS_NFE_DESCRICAO, POS_NFE_DESCRICAO, 60)
    //oPrtXlsx:SetColumnsWidth(POS_NFE_CUSTO, POS_NFE_CUSTO, 20)
    //oPrtXlsx:SetColumnsWidth(POS_NFE_PRC_TAB, POS_NFE_PRC_TAB, 20)
    //oPrtXlsx:SetColumnsWidth(POS_NFE_VLR_ULT_COMP, POS_NFE_VLR_ULT_COMP, 20)
    //oPrtXlsx:SetColumnsWidth(POS_NFE_ICMS, POS_NFE_ICMS, 20)
    //oPrtXlsx:SetColumnsWidth(POS_NFE_INF_ULT_COMP, POS_NFE_INF_ULT_COMP, 80)


    cQryCMP := fGetQryCmp()

    If Select('TMPQRY') <> 0
        TMPQRY->(dbCloseArea())
    Endif
    TCQuery cQryCMP Alias TMPQRY New
    // nRegs:=0
    Count To nRegAte
    TMPQRY->(DbGoTop())
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
        oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/, "Refugo PCP")

        nRow++ // pula linha

        //setar o nome das colunas
        oPrtXlsx:SetText(nRow /*Linha*/, POS_FILIAL        /*Coluna*/, "Filial")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_OP_RD         /*Coluna*/, "OP")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_ITEM_OP       /*Coluna*/, "Item OP")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_SEQ_OP        /*Coluna*/, "Seq OP")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PROD_PA       /*Coluna*/, "Cd Prod PA")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_DESC_PA       /*Coluna*/, "Desc PA")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PROD_MP       /*Coluna*/, "Cd Prod")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_DESC_MP       /*Coluna*/, "Desc Prod")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_QTD_ORI_OP    /*Coluna*/, "Qtd Ori OP")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_EMISS_OP      /*Coluna*/, "Dt Emiss OP")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PRV_INI       /*Coluna*/, "Dt Prev Ini")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PRV_FIM       /*Coluna*/, "Dt Prev Fim")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_QTD_EST       /*Coluna*/, "Qtd Estrutura")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_OP_FULL       /*Coluna*/, "Num OP")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_QTD_PREV      /*Coluna*/, "Qtd Prev")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_QTD_PROD      /*Coluna*/, "Qtd Produzida")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CUSTO_UNIT    /*Coluna*/, "Custo Unitario")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_DT_PRD        /*Coluna*/, "Dt Ult Mov")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CUSTO_REAL    /*Coluna*/, "Custo Realizado")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_CUSTO_PREV    /*Coluna*/, "Custo Previsto")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_TOT_REAL      /*Coluna*/, "Total Realizado")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_TOT_PREV      /*Coluna*/, "Total Previso")
        oPrtXlsx:SetText(nRow /*Linha*/, POS_PERC_REF      /*Coluna*/, "% Refugo")

        nRow++ // pula linha

        cTmpWlIni := Time()
        WHILE  TMPQRY->(!eof())
            oSay:cCaption := ("Processando  -  " + cValToChar(nRow) + " - " + cValToChar(nRegAte) ) //Processando registro x de y, aguarde."
            lRet := oPrtXlsx:SetFont(cFont, nSize, .f./*lItalic*/, .f./*lBold*/, lUnderlined)
            /*Campos Texto
            */
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, ""/*formato*/ )

            oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            oPrtXlsx:SetText(nRow /*Linha*/, POS_FILIAL , TMPQRY->C2_FILIAL )
            oPrtXlsx:SetBorder(.f./*lLeft*/, .t./*lTop*/, .f./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro


            oPrtXlsx:SetText(nRow /*Linha*/, POS_OP_RD  , TMPQRY->C2_NUM )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_ITEM_OP, TMPQRY->C2_ITEM )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_SEQ_OP , TMPQRY->C2_SEQUEN )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_PROD_PA, alltrim(TMPQRY->C2_PRODUTO ))
            oPrtXlsx:SetText(nRow /*Linha*/, POS_DESC_PA, alltrim(TMPQRY->DESC_PA) )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_PROD_MP, alltrim(TMPQRY->G1_COMP) )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_DESC_MP, alltrim(TMPQRY->DESC_MP) )
            oPrtXlsx:SetText(nRow /*Linha*/, POS_OP_FULL, TMPQRY->D3_OP )

            oPrtXlsx:SetValue(nRow /*Linha*/, POS_EMISS_OP/*Coluna*/     , dtoc(stod(TMPQRY->C2_EMISSAO)))
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_PRV_INI/*Coluna*/     , dtoc(stod(TMPQRY->C2_DATPRI)))
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_PRV_FIM/*Coluna*/     , dtoc(stod(TMPQRY->C2_DATPRF)))
            oPrtXlsx:SetValue(nRow /*Linha*/, POS_DT_PRD/*Coluna*/      , dtoc(stod(TMPQRY->D3_EMISSAO)))
            //  RANK_DLP,C2_FILIAL,C2_NUM,C2_ITEM,C2_SEQUEN,C2_PRODUTO,DESC_PA,G1_COMP,DESC_MP,C2_QUANT,C2_EMISSAO,C2_DATPRI,
            //C2_DATPRF,G1_QUANT,D3_OP
            //,QTD_PREVISTA,QTD_REALIZADA,
            // CUSTO_UNITARIO,D3_EMISSAO,Custo_REALIZADO,CUSTO_PREVISTO,TOTAL_OP_REALIZADO,TOTAL_OP_PREVISTO,PER_REFUGO
            /*  POS_FILIAL      01 POS_PRV_INI     11 POS_TOT_REAL    21
                POS_OP_RD       02 POS_PRV_FIM     12 POS_TOT_PREV    22
                POS_ITEM_OP     03 POS_QTD_EST     13 POS_PERC_REF    23
                POS_SEQ_OP      04 POS_OP_FULL     14
                POS_PROD_PA     05 POS_QTD_PREV    15
                POS_DESC_PA     06  POS_QTD_PROD   16
                POS_PROD_MP     07 POS_CUSTO_UNIT  17
                POS_DESC_MP     08 POS_DT_PRD      18
                POS_QTD_ORI_OP  09 POS_CUSTO_REAL  19
            POS_EMISS_OP    10 POS_CUSTO_PREV  20            */

            // Campos Valores
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatVlr /*formato*/ )


            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CUSTO_UNIT         /*Coluna*/  , TMPQRY->CUSTO_UNITARIO )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CUSTO_REAL        /*Coluna*/  , TMPQRY->Custo_REALIZADO )
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_CUSTO_PREV     /*Coluna*/  , TMPQRY->CUSTO_PREVISTO)
            // if TMPQRY->TOTAL_OP_PREVISTO>0


            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_TOT_REAL      /*Coluna*/  , TMPQRY->TOTAL_OP_REALIZADO)
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_TOT_PREV     /*Coluna*/  , TMPQRY->TOTAL_OP_PREVISTO)
            //   endif
            // Comando 'Formato de Célula' com cor de texto e fundo personalizada
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormatQtd /*formato*/ )

            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_QTD_EST     /*Coluna*/  ,  TMPQRY->G1_QUANT)

            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_QTD_PREV     /*Coluna*/  ,  TMPQRY->QTD_PREVISTA)
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_QTD_PROD     /*Coluna*/  ,  TMPQRY->QTD_REALIZADA)
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_QTD_ORI_OP     /*Coluna*/  ,  TMPQRY->C2_QUANT)


            /*Campo Percentual*/
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, cCLRBlk /*Cor do Texto*/,cCLRWhite/*Cor de Fundo*/, cFormQtd2 /*formato*/ )
            oPrtXlsx:SetBorder(.F./*lLeft*/, .t./*lTop*/, .T./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk) //Cinza Claro
            //  if TMPQRY->TOTAL_OP_PREVISTO>0
            oPrtXlsx:SetNumber(nRow /*Linha*/,POS_PERC_REF     /*Coluna*/  , TMPQRY->PER_REFUGO )
            //  endif
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


Static Function fGetQryCmp()
    Local cEol := chr(10)

    Local cQuery := "  "

    cQuery := "EXEC dbo.STP_DELPI_REFUGO_01 "
    cQuery += "  @FILIALDE      ="+valtosql(MV_PAR01) +cEol
    cQuery += "  ,@FILIALATE    ="+valtosql(MV_PAR02) +cEol
    cQuery += "  ,@EMISSAOOPDE  ="+valtosql(MV_PAR03) +cEol
    cQuery += "  ,@EMISSAOOPATE ="+valtosql(MV_PAR04) +cEol
    cQuery += "  ,@DTMOVODE     ="+valtosql(MV_PAR05) +cEol
    cQuery += "  ,@DTMOVOPATE   ="+valtosql(MV_PAR06) +cEol
    cQuery += "  ,@PRODUTOPADE  ="+valtosql(MV_PAR07) +cEol
    cQuery += "  ,@PRODUTOPAATE ="+valtosql(MV_PAR08) +cEol
    cQuery += "  ,@OPDE         ="+valtosql(MV_PAR09) +cEol
    cQuery += "  ,@OPATE        ="+valtosql(MV_PAR10)

Return cQuery
