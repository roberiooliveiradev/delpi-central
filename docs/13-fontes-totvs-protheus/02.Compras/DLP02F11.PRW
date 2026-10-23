#Include 'fileio.ch'
#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"

#DEFINE  POS_Data       01
#DEFINE  POS_TPDOC      02
#DEFINE  POS_DOCUMENTO  03
#DEFINE  POS_ITEM       07
#DEFINE  POS_INFADIC    08
#DEFINE  POS_ENTREGA    09
#DEFINE  POS_QUANTIDADE 10
#DEFINE  POS_SALDO      11
#DEFINE POS_DSC_PP 07
#DEFINE POS_PP 08
#DEFINE POS_DSC_SEG 05
#DEFINE POS_SEG 06

#DEFINE POS_DSC_PE 07
#DEFINE POS_PE 08

#DEFINE POS_DSC_LM 05
#DEFINE POS_LM 06

#DEFINE POS_DSC_QE 07
#DEFINE POS_QE 08


#DEFINE POS_DSC_LE 05
#DEFINE POS_LE 06
#DEFINE POS_DSC_SLD1 10
#DEFINE POS_SLD1 11

#DEFINE POS_H1_DSC_APS   04
#DEFINE POS_H1_DSC_MOQ  05
#DEFINE POS_H1_DSC_EMB   07
#DEFINE POS_H1_DSC_LT    09
#DEFINE POS_H1_DSC2_LT    11
#DEFINE POS_H1_VLR_MOQ  06
#DEFINE POS_H1_VLR_EMB   08
#DEFINE POS_H1_VLR_LT    10

#DEFINE POS_H2_DSC_FOR  01
#DEFINE POS_H2_DSC_PN   03
#DEFINE POS_H2_DSC_DT   04
#DEFINE POS_H2_DSC_VL   05
#DEFINE POS_H2_DSC_LT   06
#DEFINE POS_H2_DSC_MOQ  07
#DEFINE POS_H2_DSC_EMB  08
#DEFINE POS_H2_DSC_QTD_COMP   09
#DEFINE POS_H2_DSC_DT_REC     10
#DEFINE POS_H2_DSC_VLRTOT     11

#DEFINE POS_H2_VLR_FOR        01
#DEFINE POS_H2_VLR_DSC_FOR    02
#DEFINE POS_H2_VLR_PN         03
#DEFINE POS_H2_VLR_DT         04
#DEFINE POS_H2_VLR_VL          05
#DEFINE POS_H2_VLR_LT        06
#DEFINE POS_H2_VLR_MOQ       07
#DEFINE POS_H2_VLR_EMB       08
#DEFINE POS_H2_VLR_QTD_COMP  09
#DEFINE POS_H2_VLR_DT_REC    10
#DEFINE POS_H2_VLR_VLRTOT   11


uSER FUNCTION DLP02F11(cProdPar)
    Default cProdPar := ""
    local n1:=0
    local n2:=0
    local   aButtons    := {}
    Local   dDataGer    := Date()
    Local   cHoraGer    := Time()
    Local   cTit        :=  "EXTRATO_PRODUTO"+dToS(dDataGer) + "_" + StrTran(cHoraGer, ':', '-')
    Local   cArquivo    := GetTempPath()+cTit+".rel"
    Local cPerg := "DLP02F11"
    Local   cArq2       := GetTempPath()+cTit+".xlsx"
    Private aSelFil     :={}
    Private cEol        := CHR(10)
    Private aOPCCTD     := {}
    Private aOPCBanco   := {}
    Private aSCANBCO    := {}
    Private aSCANCTD    := {}
    Private aRetBCO     := {}
    Private aRetCTD     := {}
    Private cStrRetBCO := ""
    Private cStrRetCTD := ""
    Private nSldBUIni := 0.00
    Private aParBox := {}
    Private oFileW := FwFileWriter():New(cArquivo)
    Private oPrtXlsx := FwPrinterXlsx():New()
    Private aBUPos :={}
    Private cCustomFormat := "[White]R$ #,##0.0000;[Red]-R$ #,##0.0000"
    Private cFormatQtd := "[Color10]#,##0.0000;[Red]-#,##0.0000"
    Private cForQtd2 := "[White]#,##0.0000;[Red]-#,##0.0000"
    static oCellHorAlign := FwXlsxCellAlignment():Horizontal()
    static oCellVertAlign := FwXlsxCellAlignment():Vertical()
    Static cCLRWhite := "ffffff"
    Static cCLRGray := "C0C0C0"
    Static cCLRDlp1 := "023667" // Escuro
    Static cCLRDlp2 := "2c92d5" // Claro
    Static cHorAlignment := oCellHorAlign:Center()
    Static cHorAlignLeft := oCellHorAlign:Left()
    Static cVertAlignment := oCellVertAlign:Center()
    IF IsInCallStack("MATA120") .or. IsInCallStack("MATA110") .and. !Empty(cProdPar)
        //   IF IsInCallStack("MATA110")

        aPergAux := {}
        Pergunte("DLP02F11",.F.,,,,, @aPergAux)

        SetMVValue('DLP02F11' , 'MV_PAR01' ,  cProdPar) //PERCENTUAL MAXIMO ?
        SetMVValue('DLP02F11' , 'MV_PAR02' , "01" ) //SOLIC/PEDIDO DE ?
        SetMVValue('DLP02F11' , 'MV_PAR03' , CTOD("01/01/2000") ) //DATA DE EMISSAO DE ?
        SetMVValue('DLP02F11' , 'MV_PAR04' , CTOD("31/12/2049")    ) //DATA DE EMISSAO ATE ?

        __SaveParam("DLP02F11", aPergAux)
        MV_PAR01:= cProdPar
        MV_PAR02:= "01"  //SOLIC/PEDIDO DE ?
        MV_PAR03:= CTOD("01/01/2000")  //DATA DE EMISSAO DE ?
        MV_PAR04:= CTOD("31/12/2049")     //DATA DE EMISSAO ATE ?


        //    ENDIF

    else
        IF !pergunte(cPerg)
            FWAlertError("Cancelado pelo usuario","Delpi")

            RETURN
        ENDIF
    ENDIF

    lRet := oPrtXlsx:Activate(cArquivo, oFileW)
    cProdPar :=ALLTRIM(MV_PAR01)//"10080407;10380098"
    aProd := StrTokArr(cProdPar, ';')

    For n1 := 1 to Len(aProd)

        cCodPrd :=alltrim(aProd[n1])
        DBSELECTAREA("SB1")
        SB1->(dbSetOrder(1))
        iF !(DbSeek(xFilial("SB1")+cCodPrd))

            loop

        ENDIF

        FWMsgRun(, {|| fProc01(cCodPrd) }, "Delpi","1-Aguarde Gerando Relatorio | Extrato Produto "+cCodPrd )

    Next n1

    oPrtXlsx:toXlsx()
    //Abrindo o excel e abrindo o arquivo xml
    oExcel := MsExcel():New()             //Abre uma nova conexão com Excel
    oExcel:WorkBooks:Open(cArq2)     //Abre uma planilha
    oExcel:SetVisible(.T.)                 //Visualiza a planilha
    oExcel:Destroy()
RETURN



Static Function fProc01(cCodPro)
    lOCAL aForVlr := {}
    Local n2 := 0.00
    Local n2 := 0.00
    cLogoD	:= GetSrvProfString("Startpath","") + "LGDLPMID"+ cEmpAnt + ".png"
    /*header da planilha*/
    lRet := oPrtXlsx:AddSheet(cCodPro)
    cFont := FwPrinterFont():Calibri()
    nSize := 12
    lItalic := .t.
    lBold := .T.
    lUnderlined := .f.
    // Comando 'Fonte' com Calibri 14, itálico, negrito e sublinhado
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)
    lItalic := .f.

    lWrapText := .t.
    nRotation := 0

    // Comando 'Formato de Célula' com cor de texto e fundo personalizadas
    lRet := oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, lWrapText, nRotation, cCLRWhite,cCLRDlp1, "" )
    //lRet := oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, lWrapText, nRotation, "0d0c0c", "C0C0C0", cCustomFormat )
    /*Static cCLRWhite := "ffffff"
    Static cCLRGray := "C0C0C0"
    Static cCLRDlp1 := "023667" // Escuro
    Static cCLRDlp2 := "2c92d5" // Claro


    */

    nColMax := 11
    lTop := .T.
    lBottom := .T.
    lLeft:= .T.
    lRight := .T.
    cStyle := FwXlsxBorderStyle():Thin()
    cColor := "0d0c0c"
    // Borda
    lRet := oPrtXlsx:SetBorder(lLeft, lTop, lRight, lBottom, cStyle, cColor)

    nColFrom := 1
    nColTo   := nColMax
    nWidth   := 15
    lRet     := oPrtXlsx:SetColumnsWidth(nColFrom, nColTo, nWidth)
    nColFrom := 2
    nColTo   := 2
    nWidth   := 25
    lRet     := oPrtXlsx:SetColumnsWidth(nColFrom, nColTo, nWidth)
    nColFrom := 3
    nColTo   := 3
    nWidth   := 45
    lRet     := oPrtXlsx:SetColumnsWidth(nColFrom, nColTo, nWidth)

    lRet := oPrtXlsx:MergeCells( 1 /*nRowFrom*/, 1/*nColFrom*/,1 /*nRowTo*/, nColMax-2/*nColTo*/)
    oPrtXlsx:MergeCells( 1 /*nRowFrom*/, 10/*nColFrom*/,1 /*nRowTo*/, nColMax/*nColTo*/)
    nRow := 1
    nCol := 1
    // Texto em A1
    lRet := oPrtXlsx:SetFont(cFont, 22, .t./*lItalic*/, .t./*lBold*/, lUnderlined)
    lRet := oPrtXlsx:SetRowsHeight(1, 1, 45)

    lRet := oPrtXlsx:SetText(nRow, nCol, "EXTRATO PRODUTO "+ IIF(cFilAnt == "01","MATRIZ","FILIAL"))
    lRet := oPrtXlsx:SetText(nRow, 10, "DATA  "+ DTOC(DATE()) )

    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .f./*lBold*/, lUnderlined)
    // lRet := oPrtXlsx:SetRowsHeight(1, 8, 15)
    oFileRead := FwFileReader():New(cLogoD)
    If oFileRead:Open()
        cConteudo  := oFileRead:FullRead()
    EndIf
    oFileRead:Close()
    nWidthR := 100
    nHeightR := 50
    lRet := oPrtXlsx:AddImageFromBuffer(nRow, 1, "lgrl"+ cEmpAnt, cConteudo,nWidthR,nHeightR)
    lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, "" )
    nRow++

    /*01 INFORMACOES DO PRODUTO*/

    dbSelectArea("SB1")
    DbSetOrder(1)
    DbGoTop()
    iF !(DbSeek(xFilial("SB1")+cCodPro))
        // dbSelectArea("SB2")
        // DbSetOrder(1)
        // PRODUTO NAO ENCONTRADO
        RETURN

    ENDIF

    cDscPE :=""
    dbSelectArea("SBZ")    // Gilson 160313
    SBZ->(dbSetOrder(1))
    If SBZ->(dbSeek(xFilial("SBZ")+SB1->B1_COD))
        nEstSeg := SBZ->BZ_ESTSEG
        nPP := SBZ->BZ_EMIN
        nLe := SBZ->BZ_LE
        nPE := SBZ->BZ_PE
        nQE := SBZ->BZ_QE // Qtd.Embalag.
        nLM := SBZ->BZ_LM // Lote Minimo
        if SBZ->BZ_TIPE == "D"
            cDscPE :="Dias"
        ELSEif SBZ->BZ_TIPE == "S"
            cDscPE :="Semanas"
        ELSEif SBZ->BZ_TIPE == "M"
            cDscPE :="Meses"
        ELSEif SBZ->BZ_TIPE == "A"
            cDscPE :="Anos"
        ENDIF
    Else

        nEstSeg := 0.00
        nPP := 0.00
        nLe := 0.00
        nPE := 0.00
        nQE := 0.00
        nLM := 0.00
        cDscPE :=""
    EndIf
    SBZ->(dbCloseArea())
    /*Cabeçalho 01 Produto*/
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .t./*lBold*/, lUnderlined)
    lRet := oPrtXlsx:SetText(nRow, 1, "Produto")
    lRet := oPrtXlsx:SetText(nRow, POS_H1_DSC_APS   , "APS")
    lRet := oPrtXlsx:SetText(nRow, POS_H1_DSC_MOQ  , "MOQ")
    lRet := oPrtXlsx:SetText(nRow, POS_H1_DSC_EMB   , "Embalagem")
    lRet := oPrtXlsx:SetText(nRow, POS_H1_DSC_LT    , "Lead Time")
    lRet := oPrtXlsx:SetText(nRow, POS_H1_DSC2_LT    , cDscPE)

    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .f./*lBold*/, lUnderlined)
    cProdDesc := alltrim(SB1->B1_COD) + "-" + Alltrim(SB1->B1_DESC)
    lRet := oPrtXlsx:MergeCells( nRow /*nRowFrom*/, 2/*nColFrom*/,nRow /*nRowTo*/, 3/*nColTo*/)
    lRet := oPrtXlsx:SetText(nRow, 2, cProdDesc)
    lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, cForQtd2 )
    oPrtXlsx:SetNumber(nRow, POS_H1_VLR_MOQ,nLe)
    oPrtXlsx:SetNumber(nRow, POS_H1_VLR_EMB,nQE)
    oPrtXlsx:SetNumber(nRow, POS_H1_VLR_LT,nPE)

    /*HEADER 02 Fornecedores*/
    nRow++
    oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, cForQtd2 )
    lRet := oPrtXlsx:MergeCells( nRow/*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, nColMax/*nColTo*/)
    oPrtXlsx:SetFont(cFont, nSize, lItalic, .t./*lBold*/, lUnderlined)
    oPrtXlsx:SetText(nRow, 1, "COMPRAS")

    nRow++
    lRet := oPrtXlsx:MergeCells( nRow/*nRowFrom*/, POS_H2_DSC_FOR/*nColFrom*/,nRow /*nRowTo*/, POS_H2_DSC_FOR+1/*nColTo*/)
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_FOR     , "Fornecedor")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_PN       , "Part Number")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_DT       , "Data Ultima Compra")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_VL       , "Valor")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_LT       , "Lead Time")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_MOQ     , "MOQ")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_EMB     , "Embalagem")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_QTD_COMP , "Qtd a Comprar")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_DT_REC   , "Dt Recebimento")
    lRet := oPrtXlsx:SetText(nRow, POS_H2_DSC_VLRTOT   , "Vlr Total")
    nRow++

    dbSelectArea("SB2")
    DbSetOrder(1)
    nSaldoIni :=0
    If (DbSeek(xFilial("SB2") + SB1->B1_COD + '01'))
        nSaldoIni +=SB2->B2_QATU
    EndIf
    If (DbSeek(xFilial("SB2") + SB1->B1_COD + '99'))
        nSaldoIni +=SB2->B2_QATU
    EndIf
    nSaldoCalc := nSaldoIni
    dbSelectArea("SA5")
    dbSetorder(2)
    nRowPE := nRow
    cSql := " SELECT A5_FORNECE,A5_LOJA,A5_CODPRF,A5_PE,A5_LOTEMIN,A5_LOTEMUL,ISNULL(AIB_PRCCOM,0.00)AIB_PRCCOM,MAX(AIB_DATVIG)AIB_DATVIG "
    cSql += " FROM " + RETSQLNAME("SA5") + " SA5 "+CRLF
    cSql += "  LEFT JOIN " + RETSQLNAME("AIB") + " AIB "+CRLF
    cSql += "ON AIB.D_E_L_E_T_ =''  "+CRLF
    cSql += "AND AIB_FILIAL =  "+ VALTOSQL(XFILIAL("AIB")) +CRLF
    cSql += "AND AIB_CODFOR = A5_FORNECE  "+CRLF
    cSql += "AND AIB_LOJFOR = A5_LOJA  "+CRLF
    cSql += "AND AIB_CODPRO = A5_PRODUTO  "+CRLF
    cSql += "WHERE SA5.D_E_L_E_T_ = '' "+CRLF
    cSql += " AND SA5.A5_PRODUTO = "+VALTOSQL(SB1->B1_COD) +CRLF
    cSql += " AND SA5.A5_FILIAL= "+VALTOSQL( XFILIAL("SA5")) +CRLF
    cSql += "GROUP BY A5_FORNECE,A5_LOJA,A5_CODPRF,A5_PE,A5_LOTEMIN,A5_LOTEMUL,AIB_PRCCOM "  +CRLF
    cSql +=" ORDER BY 1, 2 "
    If Select('TMPSA5') <> 0
        TMPSA5->(dbCloseArea())
    Endif
    TCQuery cSql Alias TMPSA5 New
    if  TMPSA5->(!eof())
        WHILE  TMPSA5->(!eof())
            cDescFor := ALLTRIM(POSICIONE("SA2",1,XFILIAL("SA2")+TMPSA5->A5_FORNECE+TMPSA5->A5_LOJA,"A2_NOME"))
            IF ALLTRIM( TMPSA5->A5_FORNECE) =="000052"
                cDescFor +=" SC"
            ELSEIF  ALLTRIM( TMPSA5->A5_FORNECE) =="000972"
                cDescFor +=" ES"
            ENDIF
            dDtUltCm :=ctod("  /  /  ")
            nVlUltCm :=TMPSA5->AIB_PRCCOM
            cCodFor := TMPSA5->A5_FORNECE+'-'+TMPSA5->A5_LOJA
            cPartNumber :=ALLTRIM( TMPSA5->A5_CODPRF)
            aUltComp    :=  fQueryComp(SB1->B1_COD,TMPSA5->A5_FORNECE,TMPSA5->A5_LOJA)
            nLTSA5  := TMPSA5->A5_PE
            nMOQ    := TMPSA5->A5_LOTEMIN
            nEmb    := TMPSA5->A5_LOTEMUL
            if len(aUltComp) >0

                dDtUltCm := aUltComp[9]
                nVlUltCm := aUltComp[7]

            endif
            lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, "" )


            lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .t./*lBold*/, lUnderlined)
            oPrtXlsx:SetText(nRow,POS_H2_VLR_FOR ,cCodFor)
            oPrtXlsx:SetText(nRow,POS_H2_VLR_DSC_FOR ,cDescFor)
            oPrtXlsx:SetText(nRow, POS_H2_VLR_PN, cPartNumber)

            lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .f./*lBold*/, lUnderlined)
            oPrtXlsx:SetText(nRow,   POS_H2_VLR_DT, DTOC( dDtUltCm) )
            oPrtXlsx:SetText(nRow,   POS_H2_VLR_DT_REC, DTOC(daysum(date(),nLTSA5) ) )
            //QUANTIDADE
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,   cCLRWhite,cCLRDlp2, cForQtd2 )

            oPrtXlsx:SetNumber(nRow, POS_H2_VLR_LT ,nLTSA5)
            oPrtXlsx:SetNumber(nRow,  POS_H2_VLR_MOQ,nMOQ)
            oPrtXlsx:SetNumber(nRow,  POS_H2_VLR_EMB,nEmb)
            oPrtXlsx:SetNumber(nRow,  POS_H2_VLR_QTD_COMP,0)
            //MONETARIO
            lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, cCustomFormat )
            oPrtXlsx:SetNumber(nRow,  POS_H2_VLR_VL , nVlUltCm)
            oPrtXlsx:SetNumber(nRow,    POS_H2_VLR_VLRTOT ,0)

            aadd(aForVlr,{TMPSA5->A5_FORNECE,TMPSA5->A5_LOJA, nRow, nMOQ   ,nEmb ,nVlUltCm  } )
            nRow++
            TMPSA5->(dbSkip())

        EndDo
    Endif

    //nRow++
    //Chama função que analisa a ultima compra
    aUltComp    :=  fQueryComp(SB1->B1_COD)
    IF LEN(aUltComp)>0
        lRet := oPrtXlsx:MergeCells( nRow/*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, nColmax/*nColTo*/)
        lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .t./*lBold*/, lUnderlined)

        lRet := oPrtXlsx:SetText(nRow, 1,"Dados da Ultima Compra: " +alltrim(aUltComp[1])+" | "+alltrim(aUltComp[2]) + " | "+dtoc(aUltComp[9]))
        nRow++
    ENDIF

    //lRet := oPrtXlsx:SetText(nRow, 1,aUltComp[2])
    //nRow++
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .t./*lBold*/, lUnderlined)
    lRet := oPrtXlsx:SetText(nRow, 1, "Ultima Compra")
    lRet := oPrtXlsx:SetText(nRow, 3, "Consumo Medio")
    //lRet := oPrtXlsx:SetText(nRow, POS_DSC_LM, "Lote Minimo")
    lRet := oPrtXlsx:MergeCells( nRow/*nRowFrom*/, POS_DSC_LM/*nColFrom*/,nRow /*nRowTo*/, POS_DSC_LM+4/*nColTo*/)
    lRet := oPrtXlsx:SetText(nRow, POS_DSC_LM, "")
    // lRet := oPrtXlsx:SetText(nRow, POS_LM, "")
    //lRet := oPrtXlsx:SetText(nRow, POS_DSC_QE, "Qtd.Embalag.")
    // lRet := oPrtXlsx:SetText(nRow, 7, "")
    //lRet := oPrtXlsx:MergeCells( nRow /*nRowFrom*/, 5/*nColFrom*/,nRow /*nRowTo*/, 7/*nColTo*/)
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .f./*lBold*/, lUnderlined)

    lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, cCustomFormat )
    IF LEN(aUltComp)>0
        lRet := oPrtXlsx:SetNumber(nRow, 2,aUltComp[7]) // VALOR ULTIMA COMPRA
    else
        lRet := oPrtXlsx:SetNumber(nRow, 2,0.00)
    ENDIF
    lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, cForQtd2 )
    lRet := oPrtXlsx:SetNumber(nRow, 4,POSICIONE("SB3",1,XFILIAL("SB3")+SB1->B1_COD,"B3_MEDIA")) // VALOR ULTIMA COMPRA
    // lRet := oPrtXlsx:SetNumber(nRow, POS_LM, nLM  ) // VALOR ULTIMA COMPRA
    //  lRet := oPrtXlsx:SetNumber(nRow, POS_QE, nQE  ) // VALOR ULTIMA COMPRA
    //nRow++



    lRet := oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2,"" )
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .t./*lBold*/, lUnderlined)
    // lRet := oPrtXlsx:SetText(nRow, 1, "")
    // lRet := oPrtXlsx:SetText(nRow, 2, "")
    // lRet := oPrtXlsx:SetText(nRow, 3, "")
    // lRet := oPrtXlsx:SetText(nRow, 4, "")
    // lRet := oPrtXlsx:MergeCells( nRow /*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, 4/*nColTo*/)
    lRet := oPrtXlsx:SetText(nRow, POS_DSC_SLD1, "Saldo")

    //lRet := oPrtXlsx:SetText(nRow, POS_DSC_LE, "MOQ")
    lRet := oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, lWrapText, nRotation,   cCLRWhite,cCLRDlp2, cForQtd2 )
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .f./*lBold*/, lUnderlined)
    oPrtXlsx:SetNumber(nRow, POS_SLD1 ,nSaldoIni)
    //oPrtXlsx:SetNumber(nRow, POS_LE ,nLe)
    nRow++
    lRet := oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, lWrapText, nRotation,   cCLRWhite,cCLRDlp2, "" )
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .t./*lBold*/, lUnderlined)
    lRet := oPrtXlsx:SetText(nRow, POS_Data, "Emissao")
    lRet := oPrtXlsx:SetText(nRow, POS_TPDOC, "Tipo Documento")
    oPrtXlsx:MergeCells( nRow /*nRowFrom*/, POS_DOCUMENTO/*nColFrom*/,nRow /*nRowTo*/, POS_DOCUMENTO+3/*nColTo*/)
    lRet := oPrtXlsx:SetText(nRow, POS_DOCUMENTO, "Documento")

    lRet := oPrtXlsx:SetText(nRow, POS_QUANTIDADE, "Quantidade")
    lRet := oPrtXlsx:SetText(nRow, POS_ITEM, "Item")
    lRet := oPrtXlsx:SetText(nRow, POS_INFADIC, "SC / Dt Lim Compra")
    lRet := oPrtXlsx:SetText(nRow, POS_ENTREGA, "Entrega")
    //lRet := oPrtXlsx:SetText(nRow, 5, "Pedido")
    lRet := oPrtXlsx:SetText(nRow, POS_SALDO, "Saldo")


    lRet := oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, lWrapText, nRotation, "0d0c0c", cCLRWhite, "" )
    lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, .f./*lBold*/, lUnderlined)
    nRow++
    cSql := fGetQry(xFilial("SD4"),cCodPro,MV_PAR02,MV_PAR03,MV_PAR04)
    If Select('TMPQRY') <> 0
        TMPQRY->(dbCloseArea())
    Endif
    nSldEmp := 0.00
    nSldPC := 0.00
    TCQuery cSql Alias TMPQRY New
    if  TMPQRY->(!eof())
        WHILE  TMPQRY->(!eof())

            if ALLTRIM(TMPQRY->TIPO) =="EMPENHO"
                nSldEmp +=TMPQRY->QUANT
            endif
            if ALLTRIM(TMPQRY->TIPO) =="PEDIDO COMPRA"
                nSldPC +=TMPQRY->QUANT
            endif
            lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, "0d0c0c", cCLRWhite, "" )
            lRet := oPrtXlsx:SetValue(nRow, POS_Data,  dtoc(stod(TMPQRY->D4_DATA)))
            if !empty(TMPQRY->C2_DATPRF)
                lRet := oPrtXlsx:SetText(nRow, POS_ENTREGA, dtoc(stod(TMPQRY->C2_DATPRF)))
            ELSE
                lRet := oPrtXlsx:SetText(nRow, POS_ENTREGA, '')
            endif
            lRet := oPrtXlsx:SetText(nRow, POS_TPDOC,ALLTRIM(TMPQRY->TIPO))
            lRet := oPrtXlsx:SetText(nRow, POS_INFADIC,ALLTRIM(TMPQRY->DLP_OBS))
            oPrtXlsx:MergeCells( nRow /*nRowFrom*/, POS_DOCUMENTO/*nColFrom*/,nRow /*nRowTo*/, POS_DOCUMENTO+3/*nColTo*/)
            lRet := oPrtXlsx:SetText(nRow, POS_DOCUMENTO, ALLTRIM(TMPQRY->DOCUMENTO))

            lRet := oPrtXlsx:SetText(nRow, POS_ITEM, ALLTRIM(TMPQRY->C2_PRODUTO))


            lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation, "0d0c0c", cCLRWhite, cFormatQtd )
            lRet := oPrtXlsx:SetNumber(nRow, POS_QUANTIDADE, TMPQRY->QUANT)
            //   lRet := oPrtXlsx:SetNumber(nRow, 5, 0.00)
            nSaldoCalc +=TMPQRY->QUANT
            lRet := oPrtXlsx:SetNumber(nRow,POS_SALDO, nSaldoCalc)
            nRow++
            TMPQRY->(dbSkip())
        EndDo
        lRet := oPrtXlsx:SetRowsHeight(2,nRow , 15)
    EndIf
    //nSaldoCalc
    //aadd(aForVlr,{TMPSA5->A5_FORNECE,TMPSA5->A5_LOJA, nRow, nMOQ   ,nEmb   } )
    // LoteMinMax( QtdeDigitada, LoteMinimo, LoteMultiplo)
    IF nSaldoIni+nSldPC + nSldEmp  < 0
        For  n2 := 1 to Len( aForVlr)
            // nSld :=
            nQtComp := LoteMinMax( abs(nSaldoCalc), aForVlr[n2][4],aForVlr[n2][5])

            nTot := nQtComp *aForVlr[n2][6]
            oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,   cCLRWhite,cCLRDlp2, cForQtd2 )
            oPrtXlsx:SetNumber(aForVlr[n2][3],  POS_H2_VLR_QTD_COMP,nQtComp)
            lRet := oPrtXlsx:SetCellsFormat(cHorAlignLeft, cVertAlignment, lWrapText, nRotation,  cCLRWhite,cCLRDlp2, cCustomFormat )
            oPrtXlsx:SetNumber(aForVlr[n2][3],  POS_H2_VLR_VLRTOT,nTot)
        Next  n2
    EndIf

rETURN


static function fGetQrY(cCodFl,cCodProd,cLoc,dDtDe,dDtAte)

    Local cQryRet := ""
    Local cEOL    := chr(10)


    cQryRet := "SELECT  'EMPENHO' [TIPO],SC2.C2_DATPRI D4_DATA ,D4_OP[DOCUMENTO], D4_QUANT*-1 QUANT , SC2.C2_DATPRI C2_DATPRF,SC201.C2_PRODUTO C2_PRODUTO , '' [DLP_OBS]" + cEol
    cQryRet += " FROM dbo."+ RetSqlName("SD4") + " SD4 (NOLOCK) "   + cEol
    cQryRet += " LEFT JOIN  dbo."+ RetSqlName("SC2") + " SC2 (NOLOCK) ON " + cEol
    cQryRet += " SC2.D_E_L_E_T_ ='' AND SC2.C2_FILIAL = D4_FILIAL " + cEol
    cQryRet += "  AND SC2.C2_NUM +SC2.C2_ITEM +SC2.C2_SEQUEN = D4_OP  " + cEol
    // cQryRet += " AND C2_ITEM	= '01' AND C2_SEQUEN ='001'  " + cEol
    cQryRet += " LEFT JOIN  dbo."+ RetSqlName("SC2") + " SC201 (NOLOCK) ON " + cEol
    cQryRet += " SC201.D_E_L_E_T_ ='' AND SC201.C2_FILIAL = D4_FILIAL " + cEol
    // cQryRet += "  AND SC201.C2_NUM +SC201.C2_ITEM +SC201.C2_SEQUEN = D4_OP  " + cEol
    cQryRet += "  AND SC201.C2_NUM = SUBSTRING(D4_OP,1,6)  " + cEol
    cQryRet += " AND SC201.C2_ITEM	= '01' AND SC201.C2_SEQUEN ='001'  " + cEol
    cQryRet += "    WHERE  SD4.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND D4_FILIAL        = "+  VALTOSQL(cCodFl) + cEol
    cQryRet += "        AND D4_COD           = "+  VALTOSQL(cCodProd) + cEol
    cQryRet += "        and D4_LOCAL         =   "   + VALTOSQL(cLoc) + cEol
    cQryRet += "        and D4_DATA BETWEEN  " +  VALTOSQL(dDtDe) +" AND " +  VALTOSQL(dDtAte) +   cEol
    cQryRet += "        and D4_QUANT > 0  "+   cEol
    cQryRet += " UNION " + cEol
    cQryRet += "SELECT 'EMPENHO' [TIPO],SC2.C2_EMISSAO D4_DATA ,D4_OP[DOCUMENTO], D4_QUANT*-1 QUANT   , SC2.C2_DATPRI C2_DATPRF,SC201.C2_PRODUTO C2_PRODUTO , '' [DLP_OBS]" +   cEol
    cQryRet += " FROM dbo."+ RetSqlName("SD4") + " SD4 (NOLOCK) "   + cEol
    cQryRet += " LEFT JOIN  dbo."+ RetSqlName("SC2") + " SC2 (NOLOCK) ON " + cEol
    cQryRet += " SC2.D_E_L_E_T_ ='' AND SC2.C2_FILIAL = D4_FILIAL " + cEol
    cQryRet += "  AND SC2.C2_NUM +SC2.C2_ITEM +SC2.C2_SEQUEN = D4_OP  " + cEol
    // cQryRet += "  AND C2_NUM = SUBSTRING(D4_OP,1,6)  " + cEol
    // cQryRet += " AND C2_ITEM	= '01' AND C2_SEQUEN ='001'  " + cEol
    cQryRet += " LEFT JOIN  dbo."+ RetSqlName("SC2") + " SC201 (NOLOCK) ON " + cEol
    cQryRet += " SC201.D_E_L_E_T_ ='' AND SC201.C2_FILIAL = D4_FILIAL " + cEol
    // cQryRet += "  AND SC201.C2_NUM +SC201.C2_ITEM +SC201.C2_SEQUEN = D4_OP  " + cEol
    cQryRet += "  AND SC201.C2_NUM = SUBSTRING(D4_OP,1,6)  " + cEol
    cQryRet += " AND SC201.C2_ITEM	= '01' AND SC201.C2_SEQUEN ='001'  " + cEol
    cQryRet += "    WHERE  SD4.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND D4_FILIAL        = "+  VALTOSQL(cCodFl) + cEol
    cQryRet += "        AND D4_COD           = "+  VALTOSQL(cCodProd) + cEol
    cQryRet += "        and D4_LOCAL         =   "   + VALTOSQL('99') + cEol
    cQryRet += "        and D4_DATA BETWEEN  " +  VALTOSQL(dDtDe) +" AND " +  VALTOSQL(dDtAte) +   cEol
    cQryRet += "        and D4_QUANT > 0  "+   cEol
    cQryRet += " UNION " + cEol
    cQryRet += "SELECT 'PEDIDO COMPRA'  [TIPO],C7_EMISSAO [D4_DATA], C7_ITEM+'-'+C7_NUM + ' '+LTRIM(RTRIM(ISNULL(A2_NOME,'')))  [DOCUMENTO],C7_QUANT-C7_QUJE [QUANT]  , C7_DATPRF C2_DATPRF, '' C2_PRODUTO   ,"
    cQryRet +=" CASE WHEN C7_NUMSC != '' THEN C7_NUMSC + ' - ' + C7_ITEMSC  ELSE '' END [DLP_OBS] "
    cQryRet += " FROM dbo."+ RetSqlName("SC7") + " SC7 (NOLOCK) "   + cEol
    cQryRet += " LEFT JOIN dbo."+ RetSqlName("SA2") + " SA2 (NOLOCK) "   + cEol
    cQryRet += " ON SA2.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND A2_FILIAL        = "+  VALTOSQL(XFILIAL("SA2")) + cEol
    cQryRet += "        AND A2_COD  = C7_FORNECE "+  cEol
    cQryRet += "        AND A2_LOJA = C7_LOJA "  + cEol
    cQryRet += "    WHERE  SC7.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND C7_FILIAL        = "+  VALTOSQL(cCodFl) + cEol
    cQryRet += "        AND C7_PRODUTO           = "+  VALTOSQL(cCodProd) + cEol
    cQryRet += "        and C7_LOCAL         =   "   + VALTOSQL(cLoc) + cEol
    cQryRet += "        and C7_DATPRF BETWEEN  " +  VALTOSQL(dDtDe) +" AND " +  VALTOSQL(dDtAte) +   cEol
    cQryRet += "        and C7_ENCER != 'E'  "+   cEol
    cQryRet += "        and C7_QUANT-C7_QUJE > 0   "+   cEol
    cQryRet += "        and C7_RESIDUO = ''  "+   cEol
    cQryRet += " UNION " + cEol
    cQryRet += "SELECT 'SOLICITACAO COMPRA'[TIPO]  , C1_EMISSAO [D4_DATA],C1_ITEM+'-'+C1_NUM+' ' + LTRIM(RTRIM(C1_SOLICIT))+' ' + LTRIM(RTRIM(C1_OBS))+ ' '+LTRIM(RTRIM(ISNULL(A2_NOME,'')))  [DOCUMENTO]," + cEol
    cQryRet += " C1_QUANT-C1_QUJE[QUANT]  , C1_DATPRF C2_DATPRF, ''   C2_PRODUTO  ,  CONVERT(VARCHAR(10), CONVERT(DATE,C1_DINICOM ), 103) [DLP_OBS]  " + cEol
    cQryRet += "FROM dbo."+ RetSqlName("SC1") + " SC1 (NOLOCK) "   + cEol
    cQryRet += " LEFT JOIN dbo."+ RetSqlName("SA2") + " SA2 (NOLOCK) "   + cEol
    cQryRet += " ON SA2.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND A2_FILIAL        = "+  VALTOSQL(XFILIAL("SA2")) + cEol
    cQryRet += "        AND A2_COD  = C1_FORNECE "+  cEol
    cQryRet += "        AND A2_LOJA = C1_LOJA "  + cEol
    cQryRet += "    WHERE  SC1.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND C1_FILIAL        = "+  VALTOSQL(cCodFl) + cEol
    cQryRet += "        AND C1_PRODUTO          = "+  VALTOSQL(cCodProd) + cEol
    cQryRet += "        and C1_LOCAL         =   "   + VALTOSQL(cLoc) + cEol
    cQryRet += "        and C1_DATPRF BETWEEN  " +  VALTOSQL(dDtDe) +" AND " +  VALTOSQL(dDtAte) +   cEol
    cQryRet += "        and C1_QUANT-C1_QUJE > 0   "+   cEol
    cQryRet += "        and C1_COTACAO IN ( '','XXXXXX') "+   cEol
    cQryRet += "        and C1_RESIDUO = ''  "+   cEol
    cQryRet += " UNION " + cEol
    // cQryRet += "SELECT 'PEDIDO COMPRA'  [TIPO],C7_EMISSAO [D4_DATA], C7_ITEM+'-'+C7_NUM [DOCUMENTO],C7_QUANT-C7_QUJE [QUANT]  , C7_DATPRF C2_DATPRF, '' C2_PRODUTO   , CASE WHEN C7_NUMSC != '' THEN C7_NUMSC + ' - ' + C7_ITEMSC  ELSE '' END [DLP_OBS] "

    cQryRet += "SELECT 'PEDIDO VENDA'[TIPO]  , C5_EMISSAO [D4_DATA],C6_NUM [DOCUMENTO],(C6_QTDVEN-C6_QTDENT )*-1[QUANT] , C6_ENTREG C2_DATPRF, '' C2_PRODUTO, '' [DLP_OBS]      "
    cQryRet += " FROM dbo."+ RetSqlName("SC6") + " SC6 (NOLOCK) "   + cEol
    cQryRet += " JOIN dbo."+ RetSqlName("SC5") + " SC5 (NOLOCK) ON " + cEol
    cQryRet += " SC5.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += " AND C5_FILIAL = C6_FILIAL  "   + cEol
    cQryRet += " AND C5_NUM = C6_NUM  "   + cEol
    cQryRet += " AND C5_CLIENTE=C6_CLI  "   + cEol
    cQryRet += " AND C5_LOJACLI=C6_LOJA "   + cEol
    cQryRet += " AND C5_FILIAL = C6_FILIAL "   + cEol
    cQryRet += "    WHERE  SC6.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND C6_FILIAL        = "+  VALTOSQL(cCodFl) + cEol
    cQryRet += "        AND C6_PRODUTO          = "+  VALTOSQL(cCodProd) + cEol
    cQryRet += "        and C6_LOCAL         =   "   + VALTOSQL(cLoc) + cEol
    cQryRet += "        and C6_ENTREG BETWEEN  " +  VALTOSQL(dDtDe) +" AND " +  VALTOSQL(dDtAte) +   cEol
    cQryRet += "        and C6_QTDVEN-C6_QTDENT >0  "+   cEol
    cQryRet += "        and C6_BLQ = ''  "+   cEol
    cQryRet += " ORDER BY 5 "
    conout(cQryRet)

Return cQryRet


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
Static Function fQueryComp(cCod, cCodFor, cLjFor)
    Default cCodFor := ""
    Default  cLjFor := ""
    Local cQueryComp    :=  ""
    Local aRet          :=  {}

    cQueryComp  :=  "SELECT TOP 1 SD1.*,SD1.R_E_C_N_O_"+CRLF
    cQueryComp  +=  "FROM " + RETSQLNAME("SD1") + " SD1 "+CRLF
    cQueryComp  +=  "   JOIN " + RETSQLNAME("SF4") + " SF4 ON "+CRLF
    cQueryComp  +=  "       SF4.D_E_L_E_T_='' AND F4_CODIGO=D1_TES AND F4_ESTOQUE ='S' AND F4_DUPLIC ='S' "+CRLF
    cQueryComp  +=  "   JOIN " + RETSQLNAME("SF1") + " SF1 ON "+CRLF
    cQueryComp  +=  "       SF1.D_E_L_E_T_='' AND D1_FILIAL = F1_FILIAL AND F1_DOC=D1_DOC AND D1_LOJA = F1_LOJA  AND D1_FORNECE=F1_FORNECE"+CRLF
    cQueryComp  +=  "	    AND D1_EMISSAO=F1_EMISSAO AND D1_SERIE=F1_SERIE AND F1_TIPO='N' AND (F1_ESPECIE='SPED' OR F1_ESPECIE='NFE') "+CRLF
    cQueryComp  +=  "WHERE D1_FILIAL='" + xFilial("SD1") + "' AND D1_COD='" + cCod + "' AND D1_TES <> '   ' AND D1_FORNECE != '000052' "+CRLF

    if !Empty(cCodFor) .and. !Empty(cLjFor)
        cQueryComp  +=  "AND D1_FORNECE = "+VALTOSQL(cCodFor)
        cQueryComp  +=  "AND D1_LOJA = "+VALTOSQL(cLjFor)

    endif
    cQueryComp  +=  "AND SD1.D_E_L_E_T_ ='' "+CRLF
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
        cFornecedor := ALLTRIM(POSICIONE("SA2",1,XFILIAL("SA2") + cAlias2->D1_FORNECE + cAlias2->D1_LOJA, "A2_NOME"))
        SA2 ->(DbClosearea())

        aRet    :=  {;
            /*Fornc.Nome*/cAlias2->D1_FORNECE + cAlias2->D1_LOJA+"/"+ cFornecedor     ,;
            /*Doc      */cAlias2->D1_DOC +"/"+cAlias2->D1_SERIE              ,;
            /*Loja      */cAlias2->D1_LOJA      ,;
            /*NFISCAL   */cAlias2->D1_DOC       ,;
            /*Serie     */cAlias2->D1_SERIE     ,;
            /*Quantidade*/cAlias2->D1_QUANT     ,;
            /*Vlr. Unit */cAlias2->D1_VUNIT     ,;
            /*Total     */cAlias2->D1_TOTAL     ,;
            /*Emissao   */StoD(cAlias2->D1_EMISSAO)    ;
            }
    EndIf

Return aRet


Static Function fSetFormat(xValor,xType)
    Local  cFormMnt := "[White]R$ #,##0.00;[Red]-R$ #,##0.00"
    Local  cFormQtd := "[Color10]#,##0.0000;[Red]-#,##0.0000"
    Local  cFormQtd2 := "[White]#,##0.0000;[Red]-#,##0.0000"
    Local cFormat := cFormMnt

Return cFormat
