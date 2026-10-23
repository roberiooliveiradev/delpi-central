#INCLUDE 'totvs.ch'
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWPrintSetup.ch"
#Include 'TopConn.ch'
#Include "RPTDef.ch"

/*=========================================================================*\
|| ####################################################################### ||
|| # Sistema:  IMPRESSAO DE ETIQUETA DE EMBALAGEM						 # ||
|| #                                                                     # ||
|| # Objetivo: Programa de impressão de embalagens						 # ||
|| #                                                                     # ||
|| # Autor:    Everton Boing                                      		 # ||
|| # Data:     Fevereiro DE 2018                                         # ||
|| ####################################################################### ||
\*=========================================================================*/

User Function DLP10E04(cNumOP,cDescCli,cCod,cCodCli,nPesoEtiq,cCodBar,nQtdEmb,dDtApo)

    Local aCabec := {}
    Local aItens := {}
    Local aCabA  := {}
    Local aIteA  := {}
    Local aLinha := {}
    Local aLinA  := {}

    Local nTotV := 0
    Local nTotI := 0
    Local nPed  := 0
    Local cMsgHtml := ''
    Local aDir := {}
    Local cArqNovo := ""
    Local aFiles := {}
    Local aSizes := {}
    Local _x

    Local cEol	:= Chr(10)
    Local cLinha := ""
    Local nHdlMod, nHdlNovo
    Local cDir := "C:\Etiqueta\"
    Local cEtiq := "EtiquetaExp.prn"
    Local cPrev14 := ""
    Local cEan132 := ""
    Local cDun14 := ""
    Local aCodBar := {}
    Local l5,l7 := .F.
    Local nContx
    Local cQrcode := ""
    Local cArquivo     := 'dlpetiq'+RetCodUsr()+'_' + dToS(Date()) + '_' + StrTran(Time(), ':', '-') + '.pdf'

    Local cCompName := upper(ComputerName())

    Private oPrintPvt
    Private nPagAtu    := 1
    //Linhas e colunas
    Private nLinAtu   := 0
    Private nLinFin   := 800
    Private nColIni   := 010
    Private nColFin   := 580
    Private nColMeio  := (nColFin-nColIni)/2
    //Colunas
    Private nColQrc   := nColIni
    Private nColDad1  := nColIni + 30
    Private nColDad2  := nColIni + 150 + 150
    Private nColDad3  := nColIni + 150
    Private nColDad4  := nColIni + 150
    Private nColDad5  := nColIni + 150
    Private nColDad6  := nColIni + 150
    Private nColDad7  := nColIni + 150
    Private nColDad8  := nColIni + 150
    Private nColDad9  := nColIni + 150 + 100
    Private nColDad10 := nColIni + 150
    Private nColDad11 := nColIni + 150
    Private nColDad12 := nColIni + 150 + 100
    Private cNmFont := 'Arial'
    Private oFont22	    := nIL //TFontEx():New('Arial',22,22,.F.,.T.,.F.)
    Private oFont22N	:= nIL //TFontEx():New('Arial',22,22,.T.,.T.,.F.)
    Private oFont26	    := nIL //TFontEx():New('Arial',26,26,.F.,.T.,.F.)
    Private oFont26N	:= nIL //TFontEx():New('Arial',26,26,.T.,.T.,.F.)
    Private oFont16N	:= nIL //TFontEx():New('Arial',16,16,.T.,.T.,.F.)
    Private oFont13	    := nIL //TFontEx():New('Arial',13,13,.F.,.T.,.F.)
    Private oFont13N	:= nIL //TFontEx():New('Arial',13,13,.T.,.T.,.F.)
    Private oFont10	    := nIL //TFontEx():New('Arial',10,10,.F.,.T.,.F.)
    Private oFont10N	:= nIL //TFontEx():New('Arial',10,10,.T.,.T.,.F.)
    Private oFont08	    := nIL //TFontEx():New('Arial',08,08,.F.,.T.,.F.)
    Private oFont08N	:= nIL //TFontEx():New('Arial',08,08,.T.,.T.,.F.)
    Private oFont06	    := nIL //TFontEx():New('Arial',06,06,.F.,.T.,.F.)
    Private oFont06N	:= nIL //TFontEx():New('Arial',06,06,.T.,.T.,.F.)

    //Declarando as fontes
    07893316010411
    //nQtdEmb := 1
    // cCodBar := PADL(ALLTRIM(cCod),12,"0") //"(02)"+cCodBar+"(37)"+Transform(StrZero((nQtdEmb*1000),4), "@E 99999999")
    cCodBar :="(01)"+ PADL(ALLTRIM(cCod),14,"0")+"(37)"+StrZero((nQtdEmb*1000),4)

    // PADL(ALLTRIM(cCod),14,"0") //"(02)"+cCodBar+"(37)"+Transform(StrZero((nQtdEmb*1000),4), "@E 99999999")
    cQrcode := ALLTRIM(cCodCli) + " / " + ALLTRIM(cCod) + " / " + ALLTRIM(cNumOp) + " / "
    cQrcode+= ALLTRIM( Transform(StrZero((nQtdEmb*1000),4),"@E 999999")) + " / "+dtoc(dDtApo)

    // aDir(cDir+"*.txt", aFiles, aSizes)

    // Apago os arquivos encontrados.
    ////////////////////////////////////////////////////////////////////////////////////////////
    //For _x := 1 to Len( aFiles )
    //    fErase(cDir+aFiles[_x])
    //Next _x

    // nHdlMod := FT_FUse(cDir+cEtiq)

    // If nHdlMod == -1
    //     MsgAlert("O arquivo de nome "+cDir+cEtiq+" nao pode ser aberto!!!.","Atencao")
    //     Return
    // Endif

    // cArqNovo := Alltrim("etiqueta_")+Alltrim(StrTran(Time(), ":", "_"))+".TXT"
    // nHdlNovo := fCreate(cDir+cArqNovo)

    // If nHdlNovo == -1
    //     MsgAlert("O arquivo de nome "+cDir+cArqNovo+" nao pode ser criado!!!","Atencao")
    //     Return
    // Endif
    cCodOpe := CBRetOpe()
    // FT_FGOTOP()
    cImp :=fGetImp(cCompName)
    lSetup := .t.
    if empty(cImp)
        lSetup := .f.
    endif
    // Criando o objeto de impressao
    //oPrintPvt := FWMSPrinter():New(cArquivo, IMP_PDF, .F., cDir,   .T., ,    @oPrintPvt, ,   ,    , ,.T.)
    oPrintPvt := FWMSPrinter():New(cArquivo, IMP_SPOOL, .F./*lAdjustToLegacy*/, /*cDir cPathInServer */,   lSetup/*lDisabeSetup*/, ,    @oPrintPvt, cImp /*cPrinter*/,  /*lServer*/ ,   /*lPDFAsPNG*/ , /*lRaw*/,/*lViewPDF*/.f.)
    //FWMsPrinter(): New ( < cFilePrintert >, [ nDevice], [ lAdjustToLegacy], [ cPathInServer], [ lDisabeSetup ], [ lTReport], [ @oPrintSetup], [ cPrinter], [ lServer], [ lPDFAsPNG], [ lRaw], [ lViewPDF], [ nQtdCopy]
    // oPrintPvt:cPathPDF := GetTempPath()
    // oPrintPvt:SetResolution(72)
    // oPrintPvt:SetPortrait()
    // oPrintPvt:SetPaperSize(0,080,110)
    // oPrintPvt:SetMargin(2, 2, 2, 2)

    oPrintPvt:StartPage()
    cLogoD	:= GetSrvProfString("Startpath","") + "lgrl"+ cEmpAnt + ".BMP"
    oFont22	    := TFontEx():New(oPrintPvt,'Arial',22,22,.F.,.T.,.F.)
    oFont22N	:= TFontEx():New(oPrintPvt,'Arial',22,22,.T.,.T.,.F.)
    oFont26	    := TFontEx():New(oPrintPvt,'Arial',26,26,.F.,.T.,.F.)
    oFont26N	:= TFontEx():New(oPrintPvt,'Arial',26,26,.T.,.T.,.F.)
    oFont16N	:= TFontEx():New(oPrintPvt,'Arial',16,16,.T.,.T.,.F.)
    oFont13	    := TFontEx():New(oPrintPvt,'Arial',13,13,.F.,.T.,.F.)
    oFont13N	:= TFontEx():New(oPrintPvt,'Arial',13,13,.T.,.T.,.F.)
    oFont10	    := TFontEx():New(oPrintPvt,'Arial',10,10,.F.,.T.,.F.)
    oFont10N	:= TFontEx():New(oPrintPvt,'Arial',10,10,.T.,.T.,.F.)
    oFont08	    := TFontEx():New(oPrintPvt,'Arial',08,08,.F.,.T.,.F.)
    oFont08N	:= TFontEx():New(oPrintPvt,'Arial',08,08,.T.,.T.,.F.)
    oFont06	    := TFontEx():New(oPrintPvt,'Arial',06,06,.F.,.T.,.F.)
    oFont06N	:= TFontEx():New(oPrintPvt,'Arial',06,06,.T.,.T.,.F.)
    //oPrintPvt := FWMSPrinter():New('ETIQUETADLP'+TIME(),6,.F.,,.T.,,,,,.F.)

    // oPrintPvt:Box( 10, 10, nLinAtu + 140, 313)
    // oPrintPvt:Box( 10, 40, nLinAtu + 140, 313)
    // oPrintPvt:Box( nLinAtu + 060, 40, nLinAtu + 080, 190)
    // oPrintPvt:Box( nLinAtu + 080, 40, nLinAtu + 140, 245)
    // oPrintPvt:Box( nLinAtu + 080, 40, nLinAtu + 140, 135)

    nLinAtu += 30
    oPrintPvt:Line (nLinAtu + 040, nColDad1, nLinAtu + 040, 0313) //oPrintPvt:Box( nLinAtu, nColDad1, 110, 0308)
    oPrintPvt:Line (nLinAtu + 060, nColDad1, nLinAtu + 060, 0313) //oPrintPvt:Box( nLinAtu, nColDad1, 110, 0308)
    oPrintPvt:Line (nLinAtu + 080, nColDad1, nLinAtu + 080, 0313) //oPrintPvt:Box( nLinAtu, nColDad1, 110, 0308)
    // oPrintPvt:Line (nLinAtu + 100, nColDad1, nLinAtu + 100, 0245) //oPrintPvt:Box( nLinAtu, nColDad1, 110, 0308)

    oPrintPvt:QRCode(165,210,cQrcode, 065)
    nWidth := 0.015
    nPFWidth := 0.005
    // oPrintPvt:FWMSBAR("CODE128" /*cTypeBar*/,9/*nRow*/ ,12/*nCol*/ ,cCodBar  /*cCode*/,oPrintPvt/*oPrint*/,/*lCheck*/,/*Color*/,/*lHorz*/.T., /*nWidth*/nWidth	,/*nHeigth*/0.450,.T./*lBanner*/,/*cFont*/,/*cMode*/,.F./*lPrint*/,nPFWidth /*nPFWidth*/,1/*nPFHeigth*/,/*lCmtr2Pix*/)
    // oPrintPvt:FWMSBAR("CODE128" /*cTypeBar*/,9/*nRow*/ ,12/*nCol*/ ,cCodBar  /*cCode*/,oPrintPvt/*oPrint*/,/*lCheck*/,/*Color*/,/*lHorz*/.T., /*nWidth*/0.02	,/*nHeigth*/0.8,.T./*lBanner*/,/*cFont*/,/*cMode*/,.F./*lPrint*/,0.001 /*nPFWidth*/,0.001/*nPFHeigth*/,.T./*lCmtr2Pix*/)
    oPrintPvt:SayBitmap(009,42,cLogoD,040,040)
    //oPrintPvt:Say(35/*< nRow>*/, 42/*< nCol>*/,"DELPI" /*< cText>*/, oFont22:oFont/*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(18/*< nRow>*/, 152/*< nCol>*/,"ORDEM DE PRODUÇÃO" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(31/*< nRow>*/, 162/*< nCol>*/,cNumOP /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

    oPrintPvt:Say(48/*< nRow>*/, 42/*< nCol>*/,"CLIENTE" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(58/*< nRow>*/, 42/*< nCol>*/,cDescCli /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

    oPrintPvt:Say(68/*< nRow>*/, 42/*< nCol>*/,"CODIGO DELPI" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(78/*< nRow>*/, 42/*< nCol>*/,cCod /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(68/*< nRow>*/, 196/*< nCol>*/,"CODIGO CLIENTE" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(78/*< nRow>*/, 196/*< nCol>*/,cCodCli /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    // Alltrim(Transform(nQtdEmb, X3Picture("B1_EMBDELP")))
    oPrintPvt:Say(88/*< nRow>*/, 42/*< nCol>*/,"PESO (KG)" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(98/*< nRow>*/, 42/*< nCol>*/,Alltrim(Transform(nPesoEtiq, X3Picture("B1_PESO"))) /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(88/*< nRow>*/, 140/*< nCol>*/,"QUANTIDADE (MIL)" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(98/*< nRow>*/, 140/*< nCol>*/,Alltrim(Transform(nQtdEmb, X3Picture("B1_EMBDELP"))) /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(110/*< nRow>*/, 140/*< nCol>*/,"INSPECIONADO POR" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(120/*< nRow>*/, 140/*< nCol>*/,cCodOpe /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

    oPrintPvt:Say(110/*< nRow>*/, 42/*< nCol>*/,"DATA" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
    oPrintPvt:Say(120/*< nRow>*/, 42/*< nCol>*/,dtoc(dDtApo) /*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

    oPrintPvt:Say(145, 30, "PRODUTO APROVADO", oFont16N:oFont, 250, /*Cor*/, 270)
    nRowCB := 145
    nColCB := 40
    nWidthCB := 75
    nHeigthCB := 18
    conout("stop")
    // oPrintPvt:EAN13(nRowCB/*nRow*/ ,nColCB/*nCol*/ ,cCodBar  /*cCode*/,nWidthCB/*nWidth*/,nHeigthCB/*nHeigth*/)
    oPrintPvt:FwMsBar("CODE128" /*cTypeBar*/, nRowCB /*nRow*/, nColCB /*nCol*/, cCodBar /*cCode*/,;
        NIL/*lCheck*/, /*Color*/, oPrinter /*oPrint*/, .T./*lHorz*/, NIL/*nWidth*/,;
        NIL/*nHeigth*/, .T./*lBanner*/, "Arial"/*cFont*/, NIL/*cMode*/, .F./*lPrint*/,;
        2/*nPFWidth*/, 2/*nPFHeigth*/, .F./*lCmtr2Pix*/)
    ///*oPrint*/,/*lCheck*/,/*Color*/,/*lHorz*/.T., /*nWidth*/0.02	,/*nHeigth*/0.8,.T./*lBanner*/,/*cFont*/,/*cMode*/,.F./*lPrint*/,0.001 /*nPFWidth*/,0.001/*nPFHeigth*/,.T./*lCmtr2Pix*/)


    // oPrintPvt:Say(135, 142, cCodBar, oFntMin, 50, /*Cor*/, )

    oPrintPvt:EndPage()
    oPrintPvt:Print()
    //    oPrintPvt:Preview()

REturn


sTATIC FUNCTION fGetImp(cCompName)

    Local cDscImp:=""
    Local aArea:=GetArea()

    Local cQuery := ""
    Local nRecnoCB1 := NIL


    cQuery := "SELECT TOP 1 CB5_PRINTR , R_E_C_N_O_ RECCB5  FROM "+RetSqlName("CB5")
    cQuery += " WHERE CB5_FILIAL = '"+xFilial("CB5")+"' AND "
    cQuery += " CB5_SERVER = '"+cCompName+"' AND "

    cQuery += " D_E_L_E_T_ = ' '"
    cQuery += " ORDER BY 2 DESC "
    dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),"CB5TOP")

    If CB5TOP->(!EOF())

        cDscImp 	:= alltrim(CB5TOP->CB5_PRINTR)

    EndIf

    CB5TOP->(DbCloseArea())

    restarea(aArea)
Return cDscImp
