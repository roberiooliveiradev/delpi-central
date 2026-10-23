#INCLUDE 'totvs.ch'
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWPrintSetup.ch"
#Include 'TopConn.ch'
#Include "RPTDef.ch"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "AP5MAIL.CH"
///CHAVE LOTE D1_ITEM+D1_DOC+D1_FORNECE+D1_LOJA

User Function DLP10E05A()

    Local cForDlp01 :="000052"
    Local cForDlp02 :="000972"
    //Local aParamBox := {}
    Local x1
    Local nEmb
    Private cFil    := SF1->F1_FILIAL
    Private cNF     := SF1->F1_DOC
    Private cSerie := SF1->F1_SERIE
    Private cFornece := SF1->F1_FORNECE
    Private cLoja := SF1->F1_LOJA
    Private oRet
    Private lRet := .T.
    Private aRet := {}
    Private lMsErroAuto := .f.


    // cProd := "10400040       "
    // cLote := "AUTO000045"
    // Rastro(cProd,"L")
    // conout("stop")
    // fPutEmp(cProd,cLote)
    // conout("stop")

    aArea       := fwgetarea()
    aAreaSB1    := SB1->(FwGetArea())
    aAreaSB2    := SB2->(FwGetArea())
    aAreaSB8    := SB8->(FwGetArea())
    aAreaSD4    := SD4->(FwGetArea())
    aAreaSD5    := SD5->(FwGetArea())
    DbSelectArea("SF1")
    SF1->(DbSetOrder(1))

    IF SF1->(DbSeek(cFil+cNF+cSerie+cFornece+cLoja))

        //oRet := zMsNew(cFil, cNF, cSerie, cFornece, cLoja)
        aRet := U_zGTela(cFil, cNF, cSerie, cFornece, cLoja)
        cFilAnt := cFil
        FWSM0Util():setSM0PositionBycFilAnt()
        IF lRet

            DbSelectArea("SA2")
            SA2->(DbSetOrder(1))
            IF !SA2->(DbSeek(xfilial("SA2")+SF1->F1_FORNECE+SF1->F1_LOJA))
                FWAlertError("Fornecedor não localizado", "Erro")
                Return
            Endif

            for x1 := 1 to len(aRet)

                DbSelectArea("SD1")
                SD1->(DbSetOrder(1))
                IF !SD1->(DbSeek(cFil+cNF+cSerie+cFornece+cLoja+aRet[x1][2]))
                    FWAlertError("Itens NF não localizados", "Erro")
                    Return
                endif

                DbSelectArea("SB1")
                SB1->(DbSetOrder(1))
                IF !SB1->(DbSeek(xfilial("SA2")+SD1->D1_COD))
                    FWAlertError("Produto não localizado", "Erro")
                    Return
                endif

                DbSelectArea("SBZ")
                SBZ->(DbSetOrder(1))
                IF !SBZ->(DbSeek(xfilial("SBZ",SF1->F1_FILIAL)+SD1->D1_COD))
                    FWAlertError("Produto sbz não localizado", "Erro")
                    Return
                endif

                DbSelectArea("SA5")
                SA5->(DbSetOrder(1))
                IF !SA5->(DbSeek(xfilial("SA5")+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_COD))
                    FWAlertError("Produto Fornecedor não localizado", "Erro")
                    Return
                endif
                lNew := .f.
                IF !Rastro(SB1->B1_COD,"L")
                    lNew := .t. //saber se é a primeira movimentação do produto sem lote
                    If RecLock('SB1',.F.)
                        SB1->B1_RASTRO :=  "L"
                        SB1->(MsUnlock())
                    EndIf
                EndIf
                // lNew := .t.
                // cLote :=  left(cValtoChar(VAL(SD1->D1_FILIAL)+VAL( SD1->D1_DOC)+VAL(SD1->D1_SERIE)+VAL(SD1->D1_FORNECE)+VAL(SD1->D1_LOJA)+VAL(SD1->D1_ITEM)),6)
                // cLoteNF := MesDia(date())+left(Year2Str(date()),2)+PADL(ALLTRIM(cLote),6,"0")
                // If RecLock('SD1',.F.)
                //     SD1->D1_LTDLP :=  cLoteNF
                //     SD1->(MsUnlock())
                // EndIf

                // Impressão do Primeiro Bloco

                //NextLote(cCod,cTipo,cSubLote)
                if lNew
                    /*LOTE SALDO ARMAZEM 01*/
                    nSld01 := CalcEst(SD1->D1_COD,"01",dDataBase,SD1->D1_FILIAL)[1]
                    nPosQuant := 4

                    nSld01 -= aRet[x1][nPosQuant]

                    cEmbal := aRet[x1][5]

                    nCntEmb := Ceiling(nSld01/cEmbal)
                    if nSld01 > 0
                        For nEmb := 1 To nCntEmb
                            if nEmb == nCntEmb .and. (cQtdEmb % cEmbal!= 0)

                                cEmbal := cQtdEmb % cEmbal

                            endif
                            cLote := NextLote(SD1->D1_COD	     ,"L")
                            aLote:= {}
                            aadd(aLote,{"D5_PRODUTO"	, SD1->D1_COD     , NIL} )
                            aadd(aLote,{"D5_LOCAL"   , SD1->D1_LOCAL	    , NIL} )
                            aadd(aLote,{"D5_DOC"		, SD1->D1_DOC       , Nil} )
                            aadd(aLote,{"D5_SERIE"		, SD1->D1_SERIE     , Nil} )
                            aadd(aLote,{"D5_DATA"    , Ddatabase-1	        , NIL} )
                            aadd(aLote,{"D5_QUANT"   , cEmbal               , NIL} )
                            aadd(aLote,{"D5_LOTECTL"	, cLote	            , NIL} )
                            aadd(aLote,{"D5_DTVALID"	, STOD("20491231")  , NIL} )
                            IF cEmpAnt == '01' .and. cFilAnt =='01'

                                aadd(aLote,{"D5_CLIFOR"	, cForDlp01         , NIL} )
                            elseif cEmpAnt == '01' .and. cFilAnt =='02'
                                aadd(aLote,{"D5_CLIFOR"	, cForDlp02         , NIL} )
                            endif
                            IF cEmpAnt == '01'
                                aadd(aLote,{"D5_LOJA"	, "01"              , NIL} )
                            endif


                            lMsErroAuto := .f.
                            FWMsgRun(, {|| MSExecAuto({|x,y| Mata390(x,y)}, aLote, 3) } ,;
                                "Delpi - Mata390", "Gerando  - "+ alltrim(SD1->D1_COD ))


                            If lMsErroAuto
                                mostraerro()
                            endif
                            DLP10E05("DELPI COMPONENTES ","01", dtoc(dDataBase-1),SB1->B1_CODBAR,SB1->B1_COD, SA5->A5_CODPRF, SB1->B1_UM, cEmbal, aRet[x1][5],;
                                SB1->B1_DESC, aRet[x1][1],cLote ,SBZ->BZ_MPLOCAL,nEmb,nCntEmb)
                        Next nEmb
                    endif


                    if aRet[x1][nPosQuant] > 0

                        cEmbal := aRet[x1][5]

                        nCntEmb := Ceiling(nSld01/cEmbal)
                        For nEmb := 1 To nCntEmb
                            if nEmb == nCntEmb .and. (cQtdEmb % cEmbal!= 0)

                                cEmbal := cQtdEmb % cEmbal

                            endif

                            cLote := NextLote(SD1->D1_COD	     ,"L")
                            aLote:= {}
                            aadd(aLote,{"D5_PRODUTO"	, SD1->D1_COD           , NIL} )
                            aadd(aLote,{"D5_LOCAL"      , SD1->D1_LOCAL	        , NIL} )
                            aadd(aLote,{"D5_DOC"		, SD1->D1_DOC           , Nil} )
                            aadd(aLote,{"D5_SERIE"		, SD1->D1_SERIE         , Nil} )
                            aadd(aLote,{"D5_DATA"       , Ddatabase	            , NIL} )
                            aadd(aLote,{"D5_QUANT"      , cEmbal   , NIL} )
                            //   aadd(aLote,{"D5_QUANT"      , aRet[x1][nPosQuant]   , NIL} )
                            aadd(aLote,{"D5_LOTECTL"	, cLote	            , NIL} )
                            aadd(aLote,{"D5_DTVALID"	, STOD("20491231")  , NIL} )
                            IF cEmpAnt == '01' .and. cFilAnt =='01'

                                aadd(aLote,{"D5_CLIFOR"	, cForDlp01         , NIL} )
                            elseif cEmpAnt == '01' .and. cFilAnt =='02'
                                aadd(aLote,{"D5_CLIFOR"	, cForDlp02         , NIL} )
                            endif
                            IF cEmpAnt == '01'
                                aadd(aLote,{"D5_LOJA"	, "01"              , NIL} )
                            endif


                            lMsErroAuto := .f.
                            FWMsgRun(, {|| MSExecAuto({|x,y| Mata390(x,y)}, aLote, 3) } ,;
                                "Delpi - Mata390", "Gerando  - "+ alltrim(SD1->D1_COD ))


                            If lMsErroAuto
                                mostraerro()
                            endif
                            DLP10E05(SA2->A2_NOME,cNF, dtoc(dDataBase),SB1->B1_CODBAR,SB1->B1_COD, SA5->A5_CODPRF, SB1->B1_UM, cEmbal,  aRet[x1][5], SB1->B1_DESC,;
                                aRet[x1][1],cLote,SBZ->BZ_MPLOCAL,nEmb,nCntEmb)
                        Next nEmb
                    endif

                    /*LOTE SALDO ARMAZEM 99*/
                    aSaldo := CalcEst(SD1->D1_COD,"99",dDataBase,SD1->D1_FILIAL)
                    nSld99 := aSaldo[1]
                    if nSld99 > 0
                        /*INICIO DO fOR*/
                        //  nSld99,aRet[x1][5]
                        cEmbal := aRet[x1][5]

                        nCntEmb := Ceiling(nSld99/cEmbal)
                        cRecSD4:= fDelEmp( SD1->D1_COD,space(getsx3cache('D4_LOTECTL','X3_TAMANHO')))
                        cFunBkp := FunName()
                        SetFunName("MATA220")
                        For nEmb := 1 To nCntEmb

                            if nEmb == nCntEmb .and. (cQtdEmb % cEmbal!= 0)

                                cEmbal := cQtdEmb % cEmbal

                            endif
                            cLote := NextLote(SD1->D1_COD,"L")
                            aLote:= {}
                            aadd(aLote,{"D5_PRODUTO"	, SD1->D1_COD      , NIL} )
                            aadd(aLote,{"D5_LOCAL"      ,"99"	            , NIL} )
                            aadd(aLote,{"D5_DOC"		, SD1->D1_DOC       , Nil} )
                            aadd(aLote,{"D5_SERIE"		, SD1->D1_SERIE     , Nil} )
                            aadd(aLote,{"D5_DATA"       , DDATABASE	-1      , NIL} )
                            aadd(aLote,{"D5_QUANT"      , cEmbal            , NIL} )
                            //   aadd(aLote,{"D5_QUANT"      , nSld99            , NIL} )
                            //    aadd(aLote,   {"D5_QTSEGUM"	, 	, NIL} )
                            aadd(aLote,{"D5_LOTECTL"	, cLote             , NIL} )
                            aadd(aLote,{"D5_DTVALID"	, STOD("20491231")  , NIL} )
                            IF cEmpAnt == '01' .and. cFilAnt =='01'

                                aadd(aLote,{"D5_CLIFOR"	, cForDlp01         , NIL} )
                            elseif cEmpAnt == '01' .and. cFilAnt =='02'
                                aadd(aLote,{"D5_CLIFOR"	, cForDlp02         , NIL} )
                            endif
                            IF cEmpAnt == '01'
                                aadd(aLote,{"D5_LOJA"	, "01"              , NIL} )
                            endif
                            DbSelectArea("SB1")
                            SB1->(DbSetOrder(1))
                            SB1->(DbSeek(xfilial("SA2")+SD1->D1_COD))

                            lMsErroAuto := .f.

                            FWMsgRun(, {|| MSExecAuto({|x,y| Mata390(x,y)}, aLote, 3) } ,;
                                "Delpi - Mata390", "99 - Gerando  - "+ alltrim(SD1->D1_COD ))

                            If lMsErroAuto

                                mostraerro()

                            else

                                FWMsgRun(, {|| DLP10E05("DELPI COMPONENTES ","99", dtoc(dDataBase-1),;
                                    SB1->B1_CODBAR,SD1->D1_COD, SA5->A5_CODPRF, SB1->B1_UM, cEmbal,aRet[x1][5], ;
                                    SB1->B1_DESC, aRet[x1][1],cLote ,SBZ->BZ_MPLOCAL,nEmb,nCntEmb)} ,;
                                    "Delpi - Etiqueta ", "Inserindo Empenho  - "+ alltrim(SD1->D1_COD ))


                            endif
                        Next nEmb
                        SetFunName(cFunBkp)

                    ENDIF

                else
                    DbSelectArea("SD5")
                    SD5->(DbSetOrder(5)) //D5_FILIAL, D5_PRODUTO, D5_LOCAL, D5_DOC, D5_SERIE
                    IF SD5->(DbSeek(xfilial("SD5",SD1->D1_FILIAL)+SB1->B1_COD+"01"+ SD1->D1_DOC+ SD1->D1_SERIE))
                        cLote := alltrim(SD5->D5_LOTECTL)
                        DLP10E05(SA2->A2_NOME,cNF, dtoc(dDataBase),SB1->B1_CODBAR,SB1->B1_COD, SA5->A5_CODPRF, SB1->B1_UM, aRet[x1][nPosQuant],  aRet[x1][5], SB1->B1_DESC, aRet[x1][1],cLote,SBZ->BZ_MPLOCAL)
                    ENDIF
                ENDIF
            next x1
        ENDIF

    endif

    SF1->(DbCloseArea())
    SA2->(DbCloseArea())
    SD1->(DbCloseArea())
    SB1->(DbCloseArea())
    SA5->(DbCloseArea())

    FwRestArea( aArea )
    FwRestArea( aAreaSB1 )
    FwRestArea( aAreaSB2 )
    FwRestArea( aAreaSB8 )
    FwRestArea( aAreaSD4 )
    FwRestArea(  aAreaSD5   )
    //Endif

Return


/*=========================================================================*\
|| ####################################################################### ||
|| # Sistema:  IMPRESSAO DE ETIQUETA            						 # ||
|| #                                                                     # ||
|| # Objetivo: Programa de impressão de etiquetas   					 # ||
|| #                                                                     # ||
|| # Autor:    Eduardo Dalitz                                      		 # ||
|| # Data:     Fevereiro DE 2025                                         # ||
|| ####################################################################### ||
\*=========================================================================*/

Static Function DLP10E05(cNomeFor,cNF,cReceb,cCodBar,cCodProd, cProdFor, cUnidMed, cQtdNf, cEmbal, cDescPr, cSitIns,cLote,cMpLoc,nCntAtu,cEmbTot)

    default nCntAtu := 0.00
    default cEmbTot  := 0.00
    Local cDir := "C:\Etiqueta\"

    Local cArquivo     := 'dlpetiq'+RetCodUsr()+'_' + dToS(Date()) + '_' + StrTran(Time(), ':', '-') + '.pdf'
    Local nX           := 0
    Local nRest        := 0

    // Local cCompName := alltrim(upper(ComputerName()))

    Private oPrintPvt
    Private nPagAtu    := 1
    //Linhas e colunas
    Private nLinAtu   := 0
    Private nLinFin   := 265
    Private nColIni   := 10
    Private nColFin   := 215
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
    Private oFont22	    := nIL
    Private oFont22N	:= nIL
    Private oFont26	    := nIL
    Private oFont26N	:= nIL
    Private oFont16N	:= nIL
    Private oFont13	    := nIL
    Private oFont13N	:= nIL
    Private oFont10	    := nIL
    Private oFont10N	:= nIL
    Private oFont08	    := nIL
    Private oFont08N	:= nIL
    Private oFont06	    := nIL
    Private oFont06N	:= nIL
    Private oFont06T	:= nIL


    //Declarando as fontes

    cCodBar := ALLTRIM(cCodBar)

    cCodOpe := CBRetOpe()


    lSetup := .T.
    lDebug:= .T.

    // Criando o objeto de impressao
    // Para gerar em PDF PARA TESTES INTERNOS
    if lDebug
        oPrintPvt := FWMSPrinter():New(cArquivo, IMP_PDF, .F., cDir,   lSetup, ,    @oPrintPvt, ,   ,    , ,.T.)
        oPrintPvt:cPathPDF := GetTempPath()
        oPrintPvt:SetResolution(72)
        oPrintPvt:SetPortrait()
        oPrintPvt:SetPaperSize(0,80,110)
        oPrintPvt:SetMargin(025,001,001,001)
    else
        oPrintPvt := FWMSPrinter():New(cArquivo, IMP_SPOOL, .F./*lAdjustToLegacy*/, /*cDir cPathInServer */,   lSetup/*lDisabeSetup*/, ,    @oPrintPvt, cImp /*cPrinter*/, .f. /*lServer*/ ,   /*lPDFAsPNG*/ , /*lRaw*/,/*lViewPDF*/.f.)
        CONOUT("STOP")
        oPrintPvt:SetMargin(025,001,001,001)
    endif
    cEmbal := IIF(cEmbal==0, cQtdNf, cEmbal )

    For nX := 1 To Ceiling(cQtdNf/cEmbal)

        //FWMsPrinter(): New ( < cFilePrintert >, [ nDevice], [ lAdjustToLegacy], [ cPathInServer], [ lDisabeSetup ], [ lTReport], [ @oPrintSetup], [ cPrinter], [ lServer], [ lPDFAsPNG], [ lRaw], [ lViewPDF], [ nQtdCopy]
        // oPrintPvt:cPathPDF := GetTempPath()
        // oPrintPvt:SetResolution(72)
        // oPrintPvt:SetPortrait()
        // oPrintPvt:SetPaperSize(0,80,110)
        // oPrintPvt:SetMargin(2, 2, 2, 2)

        oPrintPvt:StartPage()
        //cLogoD	:= GetSrvProfString("Startpath","") + "lgrl"+ cEmpAnt + ".BMP"
        cLogoD :=   GetSrvProfString("Startpath","") + "lgrl"+ cEmpAnt + ".BMP"
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
        oFont06	    := TFontEx():New(oPrintPvt,'Arial',10,10,.T.,.T.,.F.)
        oFont06T	:= TFontEx():New(oPrintPvt,'Arial',15,15,.T.,.T.,.F.)
        oFont06N	:= TFontEx():New(oPrintPvt,'Arial',06,06,.T.,.T.,.F.)



        nLinAtu += 30


        nWidth := 0.015
        nPFWidth := 0.005
        oPrintPvt:SayBitmap(009,20,cLogoD,045,030)

        oPrintPvt:Say(25/*< nRow>*/, nColMeio-15/*< nCol>*/,"ETIQUETA RECEBIMENTO" /*< cText>*/,oFont16N:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(53/*< nRow>*/, nColIni/*< nCol>*/,"Fornecedor: " /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(53/*< nRow>*/, nColIni+50/*< nCol>*/,cNomeFor /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(68/*< nRow>*/, nColIni/*< nCol>*/,"NF: " /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(68/*< nRow>*/, nColIni+20/*< nCol>*/,cNF /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(68/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/,"Recebido: " /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(68/*< nRow>*/, nColMeio+(nColMeio/2)+40/*< nCol>*/,cReceb /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(78/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/,"Mapa Localizacao: " /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(88/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/,cMpLoc/*< cText>*/,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )


        nRow128    := 75
        nWidth128  := 1
        nHeigth128 := 22
        nTWidth128 := 75
        conout("stop")
        oPrintPvt:Code128(nRow128/*nRow*/ ,nColIni/*nCol*/, cLote/*cCode*/,nWidth128/*nWidth*/,nHeigth128/*nHeigth*/,.T./*lSay*/,,nTWidth128)

        oPrintPvt:Say(130/*< nRow>*/, nColIni+10/*< nCol>*/ ,"Produto Fornecedor: " /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(140/*< nRow>*/, nColIni+25/*< nCol>*/ ,cProdFor /*< cText>*/              ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(155/*< nRow>*/, nColIni/*< nCol>*/    ,"Espécie Volume: " /*< cText>*/    ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(155/*< nRow>*/, nColIni+65/*< nCol>*/ , cUnidMed /*< cText>*/             ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(170/*< nRow>*/, nColIni/*< nCol>*/    ,"Quantidade NF: " /*< cText>*/     ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(170/*< nRow>*/, nColIni+63/*< nCol>*/ , cValtoChar(cQtdNf)/*< cText>*/    ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(185/*< nRow>*/, nColIni/*< nCol>*/    ,"Qtd Volume: " /*< cText>*/        ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

        if nX == Ceiling(cQtdNf/cEmbal)

            if cQtdNf % cEmbal == 0

                oPrintPvt:Say(185/*< nRow>*/, nColIni+53/*< nCol>*/, cValtoChar(cEmbal) /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

            else
                //ajustar calculo
                //se for igual a5_embal = 0 considerar d1_quant
                nRest := cQtdNf % cEmbal
                oPrintPvt:Say(185/*< nRow>*/, nColIni+53/*< nCol>*/, cValtoChar(nRest) /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
            endif
        else
            oPrintPvt:Say(185/*< nRow>*/, nColIni+53/*< nCol>*/, cValtoChar(cEmbal) /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        endif

        oPrintPvt:Say(98/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/   ,"Produto:" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(98/*< nRow>*/, nColMeio+(nColMeio/2)+40/*< nCol>*/,cCodProd /*< cText>*/  ,oFont10:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

        oPrintPvt:Say(110/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/, MEMOLINE(cDescPr, 30,  1) /*< cText>*/,oFont08:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(120/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/, MEMOLINE(cDescPr, 30,  2) /*< cText>*/,oFont08:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(130/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/, MEMOLINE(cDescPr, 30,  3) /*< cText>*/,oFont08:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Code128C(;
            170,;           // nRow
            nColMeio+(nColMeio/2),;                // nCol
            Left(cCodBar, 40),;    // cCodeBar
            35;                      // nSizeBar
            )

        oPrintPvt:Say(185/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/      ,"Volume:" /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        oPrintPvt:Say(185/*< nRow>*/, nColMeio+(nColMeio/2)+35/*< nCol>*/   ,  cValtoChar(nX)+"/"+cValtoChar(Ceiling(cQtdNf/cEmbal)) /*< cText>*/,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
        cDscSit := ""
        IF !EMPTY(cSitIns)

            if alltrim(cSitIns) == "1"
                cDscSit := "Aprovado"
            elseif alltrim(cSitIns) == "2"
                cDscSit := "Rejeitado"
            else
                cDscSit := "Lib. Condicional"
            endif

            oPrintPvt:Say(185/*< nRow>*/, nColMeio+(nColMeio/2)/*< nCol>*/      ,"Sit. Inspeção:" /*< cText>*/  ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )
            oPrintPvt:Say(195/*< nRow>*/, nColMeio+(nColMeio/2)+55/*< nCol>*/   ,  cDscSit /*< cText>*/         ,oFont06:oFont /*[ oFnt]*/, 50/*[ nWidth]*/, /*[ nClrText]*/, /*[ nAngle]*/ )

        ENDIF


        conout("stop")

        oPrintPvt:EndPage()

    Next nX
    //imprime pagina em branco

    oPrintPvt:Print()

Return


sTATIC FUNCTION fGetImp(cCompName)

    Local cDscImp:=""
    Local aArea:=GetArea()

    Local cQuery := ""
    //Local nRecnoCB1 := NIL


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

/*/{Protheus.doc} User Function zGTela
Tela Para selecionar itens do documento de entrada.
@author Eduardo Dalitz
@since 20/02/2025
@version 1.0
@type function
/*/
User Function zGTela(cFil, cNF, cSerie, cFornece, cLoja)
    Local aArea := FWGetArea()
    Private aRet := {}

    fMontaTela()

    FWRestArea(aArea)
Return aRet

Static Function fMontaTela()
    Local aArea         := GetArea()
    Local aCampos := {}
    Local oTempTable := Nil
    Local aColunas := {}
    Local cFontPad    := 'Tahoma'
    Local oFontGrid   := TFont():New(cFontPad, /*uPar2*/, -14)
    //Barra de Botões
    Local bBlocoOk     := {|| lOk := .T., oDlgBrow:End()}
    Local bBlocoCan    := {|| lOk := .F., oDlgBrow:End()}
    Local aOutrasAc    := {}
    Local bBlocoIni    := {|| EnchoiceBar(oDlgBrow, bBlocoOk, bBlocoCan, , aOutrasAc)}
    Private lOk        := .F.
    //Janela e componentes
    Private oDlgBrow
    Private oPanGrid
    Private oFWBrowse
    Private cAliasTmp := GetNextAlias()
    Private aRotina   := MenuDef()
    //Tamanho da janela
    Private aTamanho := MsAdvSize()
    Private nJanLarg := 1300//aTamanho[5]
    Private nJanAltu := 500//aTamanho[6]

    //Opções no Outras Ações
    aAdd(aOutrasAc, {'BMP', {|| fMarkTod()}, '* (Des) Marcar todos registros'})

    //Adiciona as colunas que serão criadas na temporária
    aAdd(aCampos, { 'FLAG_OK',    'L'  , 1,                    0}) //Flag para marcação
    aAdd(aCampos, { 'X_SITINS',   'C', 1,  0}) //Produto
    aAdd(aCampos, { 'D1_COD',     'C', TamSX3('D1_COD')[1], 0}) //Tipo
    aAdd(aCampos, { 'B1_DESC',    'C', TamSX3('B1_DESC')[1],   0}) //Unid. Med.
    aAdd(aCampos, { 'D1_QUANT',   'N', TamSX3('D1_QUANT')[1], 0}) //Descrição
    aAdd(aCampos, { 'A5_EMBAL',   'N', TamSX3('A5_EMBAL')[1], 0}) //Descrição
    aAdd(aCampos, { 'xVolume',    'C', 10, 0}) //Descrição
    aAdd(aCampos, { 'RECNUM',     'N', 16,                   0}) //RecNo da SB1

    //Cria a tabela temporária
    oTempTable:= FWTemporaryTable():New(cAliasTmp)
    oTempTable:SetFields( aCampos )
    oTempTable:Create()

    //Popula a tabela temporária
    Processa({|| fPopula()}, 'Processando...')

    //Adiciona as colunas que serão exibidas no browse
    aColunas := fCriaCols()

    //Criando a janela
    oDlgBrow := TDialog():New(0, 0, nJanAltu, nJanLarg, 'Marcar itens do Documento de entrada', , , , , , /*nCorFundo*/, , , .T.)
    //Dados

    oFWBrowse := FWBrowse():New()
    oFWBrowse:DisableFilter()
    oFWBrowse:DisableConfig()
    oFWBrowse:DisableReport()
    oFWBrowse:DisableSeek()
    oFWBrowse:DisableSaveConfig()
    oFWBrowse:SetFontBrowse(oFontGrid)
    oFWBrowse:SetAlias(cAliasTmp)
    oFWBrowse:SetDataTable()
    oFWBrowse:SetEditCell(.T., {|| .T.})
    oFWBrowse:lHeaderClick := .F.
    oFWBrowse:AddMarkColumns(;
        {|| Iif((cAliasTmp)->FLAG_OK, 'LBOK', 'LBNO') },;      //ícones
        {|| (cAliasTmp)->FLAG_OK := ! (cAliasTmp)->FLAG_OK};   //ao dar duplo clique
        )

    //Define as colunas, vincula ao painel e exibe
    oFWBrowse:SetColumns(aColunas)
    oFWBrowse:SetOwner(oDlgBrow)
    oFWBrowse:Activate()

    oDlgBrow:Activate(, , , .T., , , bBlocoIni)

    //Se usuário clicou no botão confirmar
    If lOk
        fConfirmou()
    EndIf

    //Deleta a temporária e desativa a tela de marcação
    oTempTable:Delete()
    oFWBrowse:DeActivate()

    RestArea(aArea)
Return

Static Function MenuDef()
    Local aRotina := {}

    //Criação das opções
    ADD OPTION aRotina TITLE 'Continuar'  ACTION 'fConfirmou()'     OPERATION 2 ACCESS 0
Return aRotina

Static Function fPopula()
    Local cQryDados := ''
    Local nTotal := 0
    Local nAtual := 0

    //Monta a consulta

    //Seleciona dados do documento de entrada
    cQryDados := " SELECT "                                                              + CRLF
    cQryDados += "     D1_COD COD, "                                                     + CRLF
    cQryDados += "     B1_DESC, "                                                        + CRLF
    cQryDados += "     SUM(D1_QUANT)D1_QUANT, MAX(SD1.R_E_C_N_O_ )AS SD1REC "            + CRLF
    cQryDados += " FROM "                                                                + CRLF
    cQryDados += "     " + RetSQLName('SD1') + " SD1 "                                   + CRLF
    cQryDados += "     INNER JOIN  " + RetSQLName('SB1') + "  SB1 ON D1_COD = B1_COD   " + CRLF
    cQryDados += " WHERE "                                                               + CRLF
    cQryDados += "      SD1.D_E_L_E_T_ = ' ' "                                           + CRLF
    cQryDados += "     AND SB1.D_E_L_E_T_ = ' ' "                                        + CRLF
    cQryDados += "     AND SB1.B1_TIPO      = 'MP' "                                     + CRLF
    //cQryDados += "     AND SD1.D1_LTDLP     = ' ' "                                      + CRLF
    cQryDados += "     AND D1_FILIAL        = '" + cFil + "' "                           + CRLF
    cQryDados += "     AND D1_DOC           = '" + cNF + "' "                            + CRLF
    cQryDados += "     AND D1_SERIE         = '" + cSerie + "' "                         + CRLF
    cQryDados += "     AND D1_FORNECE       = '" + cFornece + "' "                       + CRLF
    cQryDados += "     AND D1_LOJA          = '" + cLoja + "' "                          + CRLF
    cQryDados +=" GROUP BY D1_COD,B1_DESC "
    cQryDados += " ORDER BY COD "                                                        + CRLF

    PLSQuery(cQryDados, 'QRYDADTMP')

    //Definindo o tamanho da régua
    DbSelectArea('QRYDADTMP')
    Count to nTotal
    ProcRegua(nTotal)
    QRYDADTMP->(DbGoTop())

    //Enquanto houver registros, adiciona na temporária
    While ! QRYDADTMP->(EoF())
        nAtual++
        IncProc('Analisando registro ' + cValToChar(nAtual) + ' de ' + cValToChar(nTotal) + '...')

        nQtdEmb := QRYDADTMP->D1_QUANT
        DbSelectArea("SBZ")
        SBZ->(DbSetOrder(1))
        if   SBZ->(DbSeek(xFilial('SBZ')+QRYDADTMP->COD))

            nQtdEmb :=SBZ->BZ_QE

        endif

        DbSelectArea("SA5")
        SA5->(DbSetOrder(1))
        IF SA5->(DbSeek(xfilial("SA5")+cFornece+cLoja+QRYDADTMP->COD))

            IF SA5->A5_EMBAL >0
                nQtdEmb :=SA5->A5_EMBAL
            endif
        endif
        //
        RecLock(cAliasTmp, .T.)
        (cAliasTmp)->FLAG_OK := .F.
        (cAliasTmp)->X_SITINS := M->X_SITINS
        (cAliasTmp)->D1_COD := QRYDADTMP->COD
        (cAliasTmp)->B1_DESC := QRYDADTMP->B1_DESC
        (cAliasTmp)->D1_QUANT := QRYDADTMP->D1_QUANT
        (cAliasTmp)->A5_EMBAL := nQtdEmb
        //(cAliasTmp)->xVolume := cValtoChar(QRYDADTMP->D1_QUANT)+"/"+ cValtoChar(SA5->A5_EMBAL)
        (cAliasTmp)->xVolume := cValtoChar(QRYDADTMP->D1_QUANT)+"/"+ cValtoChar(nQtdEmb)
        (cAliasTmp)->RECNUM := QRYDADTMP->SD1REC
        (cAliasTmp)->(MsUnlock())

        QRYDADTMP->(DbSkip())
    EndDo
    QRYDADTMP->(DbCloseArea())
    (cAliasTmp)->(DbGoTop())
Return


Static Function fCriaCols()
    Local nAtual       := 0
    Local aColunas := {}
    Local aEstrut  := {}
    Local oColumn

    //Adicionando campos que serão mostrados na tela
    //[1] - Campo da Temporaria
    //[2] - Titulo
    //[3] - Tipo
    //[4] - Tamanho
    //[5] - Decimais
    //[6] - Máscara
    //[7] - Editável? .T. = sim, .F. = não
    aAdd(aEstrut, { 'X_SITINS',  'Situação Inspeção',    'C', 1,  0, '',     .T., {"1=Aprovado", "2=Rejeitado", "3=Liberado Condicional"}})
    aAdd(aEstrut, { 'D1_COD',    'Código',       'C', TamSX3('D1_COD')[1], 0, '',     .F., Nil})
    aAdd(aEstrut, { 'B1_DESC',   'Descrição Prod', 'C', TamSX3('B1_DESC')[1],   0, '',     .F., Nil})
    aAdd(aEstrut, { 'D1_QUANT',  'Quantidade',  'C', TamSX3('D1_QUANT')[1], 0, '',     .F., Nil})
    aAdd(aEstrut, { 'A5_EMBAL',   'Qtd. Volume', 'C', TamSX3('A5_EMBAL')[1],   0, '',     .F., Nil})
    aAdd(aEstrut, { 'xVolume',   'Volume',  'C', 10, 0, '',     .F., Nil})

    //Percorrendo todos os campos da estrutura
    For nAtual := 1 To Len(aEstrut)
        //Cria a coluna
        oColumn := FWBrwColumn():New()
        oColumn:SetData(&('{|| ' + cAliasTmp + '->' + aEstrut[nAtual][1] +'}'))
        oColumn:SetTitle(aEstrut[nAtual][2])
        oColumn:SetType(aEstrut[nAtual][3])
        oColumn:SetSize(aEstrut[nAtual][4])
        oColumn:SetDecimal(aEstrut[nAtual][5])
        oColumn:SetPicture(aEstrut[nAtual][6])
        nAling := 2
        oColumn:SetAlign(nAling)

        //Se for ser possível ter o duplo clique
        If aEstrut[nAtual][7]
            oColumn:SetEdit(.T.)
            oColumn:SetReadVar(aEstrut[nAtual][1])
            //oColumn:SetValid({|| fSuaValid()})
        EndIf

        If ! Empty(aEstrut[nAtual][8])
            oColumn:SetOptions(aEstrut[nAtual][8])
        EndIf

        //Adiciona a coluna
        aAdd(aColunas, oColumn)
    Next
Return aColunas

Static Function fConfirmou()
    Processa({|| fProcessa()}, 'Processando...')
Return

Static Function fProcessa()
    Local aArea     := FWGetArea()
    Local nAtual    := 0
    Local nTotal    := 0
    Local nTotMarc := 0

    //Define o tamanho da régua
    DbSelectArea(cAliasTmp)
    (cAliasTmp)->(DbGoTop())
    Count To nTotal
    ProcRegua(nTotal)

    //Percorrendo os registros
    (cAliasTmp)->(DbGoTop())
    While ! (cAliasTmp)->(EoF())

        nAtual++
        IncProc('Analisando registro ' + cValToChar(nAtual) + ' de ' + cValToChar(nTotal) + '...')

        //Caso esteja marcado
        If (cAliasTmp)->FLAG_OK

            nTotMarc++
            aadd(aRet, {(cAliasTmp)->X_SITINS, (cAliasTmp)->D1_COD,(cAliasTmp)->B1_DESC, (cAliasTmp)->D1_QUANT, (cAliasTmp)->A5_EMBAL})

        EndIf

        (cAliasTmp)->(DbSkip())

    EndDo

    FWRestArea(aArea)
Return

Static Function fMarkTod()
    //Percorre todos os registros
    DbSelectArea(cAliasTmp)
    (cAliasTmp)->(DbGoTop())
    While ! (cAliasTmp)->(EoF())
        //Atualiza o registro atual
        RecLock(cAliasTmp, .F.)
        (cAliasTmp)->FLAG_OK := ! (cAliasTmp)->FLAG_OK
        (cAliasTmp)->(MsUnlock())

        (cAliasTmp)->(DbSkip())
    EndDo

    //Volta pro topo, e atualiza a tela
    (cAliasTmp)->(DbGoTop())
    oFWBrowse:Refresh()
Return

User Function D10E05()

    // fDelEmp()
    fPutEmp()
RETURN
/*/{Protheus.doc} fDelEmp
@Description Função para realizar o Backup dos empenhos de produtos e excluir ele
@Type
@Author 	 TSC - Gabriel Araujo
@Since  	 09/04/2025
/*/
Static Function fDelEmp(cProd,cLote)

    Default cProd := "10400040       "
    Local nX         := 0
    Local aCab       := {}
    Local aLine      := {}
    Local aItens     := {}
    // Local aLineEnder := {}
    //   Local aEnder     := {}
    Local cEol := chr(10)
    Local cRecSD4 :=""
    PRIVATE lMsErroAuto := .F.
    cSql := "SELECT R_E_C_N_O_ [RECSD4], * FROM "+RetSqlName("SD4")+" SD4 (NOLOCK) "+cEol
    cSql +="WHERE SD4.D_E_L_E_T_ = ''" + cEol
    cSql +="AND SD4.D4_FILIAL   = " + VALTOSQL(xfilial("SD4"))+cEol
    cSql +="AND D4_COD          = " + VALTOSQL(cProd)+cEol
    cSql +="and D4_QUANT        > 0 "
    If Select('TMPSD4') <> 0
        TMPSD4->(DbCloseArea())
    EndIf

    TCQuery cSql Alias  TMPSD4 New

    While TMPSD4->(!EOF())


        //Monta o cabeçalho com o número da OP que será alterada.
        //Necessário utilizar o índice 2 para efetuar a alteração.
        aCab := {{"D4_OP", TMPSD4->D4_OP,NIL},;
            {"INDEX",2,Nil}}
        aItens     := {}
        //Seta o índice da SDC
        SDC->(dbSetOrder(2))

        //Busca os empenhos da SD4 para alterar/excluir.
        SD4->(dbSetOrder(2))
        SD4->(dbSeek(xFilial("SD4")+PadR(  TMPSD4->D4_OP,Len(SD4->D4_OP))))

        While SD4->(!Eof()) .And. SD4->(D4_FILIAL+D4_OP) == xFilial("SD4")+PadR( TMPSD4->D4_OP,Len(SD4->D4_OP))
            //Adiciona as informações do empenho, conforme estão na tabela SD4.
            //Busca os empenhos da SD4 para alterar/excluir.
            //  SD4->(dbSetOrder(2))
            if cProd ==   SD4->D4_COD
                RecLock('ZA1', .T.)
                ZA1->ZA1_FILIAL := SD4->D4_FILIAL
                ZA1->ZA1_STATUS := "0"
                ZA1->ZA1_COD    :=  SD4->D4_COD
                ZA1->ZA1_OP     := SD4->D4_OP
                ZA1->ZA1_QUANT  := SD4->D4_QUANT
                ZA1->ZA1_QTDEOR := SD4->D4_QTDEORI
                ZA1->ZA1_RECSD3 := TMPSD4->RECSD4
                ZA1->ZA1_DATA   := ddatabase
                ZA1->ZA1_CDROT  := SD4->D4_ROTEIRO
                ZA1->ZA1_OPERAC := SD4->D4_OPERAC
                ZA1->(MsUnlock())
            endif
            aLine := {}
            For nX := 1 To SD4->(FCount())
                aAdd(aLine,{SD4->(Field(nX)),SD4->(FieldGet(nX)),Nil})
            Next nX

            //Adiciona o identificador LINPOS para identificar que o registro já existe na SD4
            aAdd(aLine,{"LINPOS","D4_COD+D4_TRT+D4_LOTECTL+D4_NUMLOTE+D4_LOCAL+D4_OPORIG+D4_SEQ",;
                SD4->D4_COD,;
                SD4->D4_TRT,;
                SD4->D4_LOTECTL,;
                SD4->D4_NUMLOTE,;
                SD4->D4_LOCAL,;
                SD4->D4_OPORIG,;
                SD4->D4_SEQ})
            //Marca o empenho do produto "MP" como Excluído.
            if cProd ==   SD4->D4_COD .and.  SD4->D4_QTDEORI == SD4->D4_QUANT
                aAdd(aLine,{"AUTDELETA","S",Nil})
            elseif    cProd ==   SD4->D4_COD .and.  SD4->D4_QTDEORI != SD4->D4_QUANT
                nPosOri := aScan(aLine,{|x| x[1] == "D4_QTDEORI"})
                nPosQtd := aScan(aLine,{|x| x[1] == "D4_QUANT"})

                aLine[nPosOri,2] -= SD4->D4_QUANT
                aLine[nPosQtd,2] := 0.00
            endif
            /*    nX := aScan(aLine,{|x| x[1] == "D4_QTDEORI"})
            If nX > 0
                //Encontrou o valor da quantidade. Faz a alteração do valor.
                aLine[nX,2] := 10
            EndIf

            //Altera também o saldo do empenho
            nX := aScan(aLine,{|x| x[1] == "D4_QUANT"})
            If nX > 0
                //Encontrou o valor da quantidade. Faz a alteração do valor.
                aLine[nX,2] := 10
            EndIf*/

            //Adiciona as informações do empenho no array de itens.
            aAdd(aItens,aLine)

            //Próximo registro da SD4.
            SD4->(dbSkip())
        EndDO

        lMsErroAuto := .F.
        if len(aItens) == 1
            aItensDel :={}
            //Executa o MATA381, com a operação de Exclusão.
            MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItensDel,5)
        else
            //Executa o MATA381, com a operação de Alteração.
            MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,4)
        endif
        If lMsErroAuto
            DBSelectArea("ZA1")
            ZA1->(dbSetOrder(4))
            IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                RecLock('ZA1', .F.)
                ZA1->ZA1_STATUS := "A"
                ZA1->ZA1_DLPLTC := cLote
                ZA1->(MsUnlock())
            ENDIF
            //
            //Se ocorrer erro.
            MostraErro()
            // Else
            //     Alert("Alterado com sucesso.")
        else
            //    ZA1->ZA1_STATUS := "1"
            conout("sdsa")
            DBSelectArea("ZA1")
            ZA1->(dbSetOrder(4))
            IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                RecLock('ZA1', .F.)
                ZA1->ZA1_STATUS := "1"
                ZA1->ZA1_DLPLTC := cLote
                ZA1->(MsUnlock())
            ENDIF

        EndIf
        TMPSD4->(DbSkip())
    EndDo
    TMPSD4->(DbCloseArea())


Return cRecSD4



Static Function fPutEmp(cProd,cLote,cRecSD4)

    Default cProd := "10400040       "
    Default cRecSD4 := ""
    Local nX         := 0
    Local aCab       := {}
    Local aLine      := {}
    Local aItens     := {}
    //Local aLineEnder := {}
    //Local aEnder     := {}
    Local cEol := chr(10)

    PRIVATE lMsErroAuto := .F.
    cSql := "SELECT R_E_C_N_O_ [RECSD4], * FROM "+RetSqlName("SD4")+" SD4 (NOLOCK) "+cEol
    cSql +="WHERE SD4.D_E_L_E_T_ = '*'" + cEol
    cSql +="AND SD4.D4_FILIAL   = " + VALTOSQL(xfilial("SD4"))+cEol
    cSql +="AND D4_COD          = " + VALTOSQL(cProd)+cEol
    cSql +="and D4_QUANT        > 0 "+cEol
    cSql +="and R_E_C_N_O_      in (SELECT ZA1_RECSD3 FROM "+RetSqlName("ZA1")+" (NOLOCK) ZA1 "+cEol
    cSql +="WHERE ZA1.D_E_L_E_T_ = '' AND ZA1.ZA1_COD  = "+VALTOSQL(cProd)+" ) "

    If Select('TMPSD4') <> 0
        TMPSD4->(DbCloseArea())
    EndIf

    TCQuery cSql Alias  TMPSD4 New

    While TMPSD4->(!EOF())


        //Monta o cabeçalho com o número da OP que será alterada.
        //Necessário utilizar o índice 2 para efetuar a alteração.
        aCab := {{"D4_OP", TMPSD4->D4_OP,NIL},;
            {"INDEX",2,Nil}}
        aItens     := {}
        //Seta o índice da SDC
        SDC->(dbSetOrder(2))

        //Busca os empenhos da SD4 para alterar/excluir.
        SD4->(dbSetOrder(2))
        if  SD4->(dbSeek(xFilial("SD4")+PadR(  TMPSD4->D4_OP,Len(SD4->D4_OP))))


            While SD4->(!Eof()) .And. SD4->(D4_FILIAL+D4_OP) == xFilial("SD4")+PadR( TMPSD4->D4_OP,Len(SD4->D4_OP))
                //Adiciona as informações do empenho, conforme estão na tabela SD4.
                aLine := {}
                For nX := 1 To SD4->(FCount())
                    aAdd(aLine,{SD4->(Field(nX)),SD4->(FieldGet(nX)),Nil})
                Next nX

                //Adiciona o identificador LINPOS para identificar que o registro já existe na SD4
                aAdd(aLine,{"LINPOS","D4_COD+D4_TRT+D4_LOTECTL+D4_NUMLOTE+D4_LOCAL+D4_OPORIG+D4_SEQ",;
                    SD4->D4_COD,;
                    SD4->D4_TRT,;
                    SD4->D4_LOTECTL,;
                    SD4->D4_NUMLOTE,;
                    SD4->D4_LOCAL,;
                    SD4->D4_OPORIG,;
                    SD4->D4_SEQ})
                //Marca o empenho do produto "MP" como Excluído.
                if cProd ==   SD4->D4_COD
                    aAdd(aLine,{"AUTDELETA","S",Nil})
                endif


                //Adiciona as informações do empenho no array de itens.
                aAdd(aItens,aLine)

                //Próximo registro da SD4.
                SD4->(dbSkip())
            End

            aLine := {}
            aAdd(aLine,{"D4_OP"     ,TMPSD4->D4_OP     ,NIL})
            aAdd(aLine,{"D4_COD"    ,PADR( ALLTRIM(TMPSD4->D4_COD ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") ) ,NIL})
            aAdd(aLine,{"D4_LOCAL"  ,TMPSD4->D4_LOCAL  ,NIL})
            aAdd(aLine,{"D4_DATA"   ,dDatabase  ,NIL})
            aAdd(aLine,{"D4_QTDEORI",TMPSD4->D4_QTDEORI,NIL})
            aAdd(aLine,{"D4_QUANT"  ,TMPSD4->D4_QUANT  ,NIL})
            if !Empty(cLote)
                aAdd(aLine,{"D4_LOTECTL",PADR( ALLTRIM(cLote) ,GETSX3CACHE("D4_LOTECTL","X3_TAMANHO") ) ,NIL})
                aAdd(aLine,{"D4_DTVALID", STOD("20491231"),NIL})
            endif
            aAdd(aLine,{"D4_TRT"    ,TMPSD4->D4_TRT    ,NIL})
            aAdd(aLine,{"D4_ROTEIRO",TMPSD4->D4_ROTEIRO,NIL})
            aAdd(aLine,{"D4_OPERAC",TMPSD4->D4_OPERAC,NIL})
            aAdd(aItens,aLine)
            cCodPrd := PADR( ALLTRIM(TMPSD4->D4_COD ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") )
            lRastro := rastro(cCodPrd,"L")
            CONOUT("STOP")
            lMsErroAuto := .F.
            if len(aItens) == 1

                //  aItensDel :={}
                //Executa o MATA381, com a operação de Exclusão.
                MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,3)
            else

                //Executa o MATA381, com a operação de Alteração.
                MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,4)
            endif
            If lMsErroAuto
                //Se ocorrer erro.
                MostraErro()
                DBSelectArea("ZA1")
                ZA1->(dbSetOrder(4))
                IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                    RecLock('ZA1', .F.)
                    ZA1->ZA1_STATUS := "B"
                    ZA1->(MsUnlock())
                ENDIF
            else
                DBSelectArea("ZA1")
                ZA1->(dbSetOrder(4))
                IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                    RecLock('ZA1', .F.)
                    ZA1->ZA1_STATUS := "2"
                    ZA1->(MsUnlock())
                ENDIF
            EndIf
        else
            //Adiciona novo empenho com utilização de Lote.
            //A data de validade do lote é preenchida automaticamente pelo programa e não precisa ser enviada no array.
            DBSelectArea("ZA1")
            ZA1->(dbSetOrder(4))
            IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                cCodPrd := PADR( ALLTRIM(ZA1->ZA1_COD   ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") )
                lRastro := rastro(cCodPrd,"L")
                CONOUT("STOP")
                aCab := {{"D4_OP",ZA1->ZA1_OP,NIL}}
                dDatabase := ZA1->ZA1_DATA
                aLine := {}
                aAdd(aLine,{"D4_OP"     ,ZA1->ZA1_OP      ,NIL})
                aAdd(aLine,{"D4_COD"    ,PADR( ALLTRIM(ZA1->ZA1_COD   ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") )    ,NIL})

                aAdd(aLine,{"D4_LOCAL"  ,"99"              ,NIL})
                aAdd(aLine,{"D4_DATA"   , ZA1->ZA1_DATA,NIL})
                aAdd(aLine,{"D4_QTDEORI", ZA1->ZA1_QTDEOR                ,NIL})
                aAdd(aLine,{"D4_QUANT"  , ZA1->ZA1_QUANT                ,NIL})
                aAdd(aLine,{"D4_LOTECTL",PADR( ALLTRIM(cLote  ) ,GETSX3CACHE("D4_LOTECTL","X3_TAMANHO") )               ,NIL})
                aAdd(aLine,{"D4_DTVALID", STOD("20491231"),NIL})

                aAdd(aLine,{"D4_ROTEIRO",ZA1->ZA1_CDROT              ,NIL})
                aAdd(aLine,{"D4_OPERAC",ZA1->ZA1_OPERAC              ,NIL})

                //Adiciona a linha do empenho no array de itens.
                aAdd(aItens,aLine)
                lMsErroAuto := .F.
                MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,3)

                If lMsErroAuto
                    //Se ocorrer erro.
                    //  MostraErro()
                    //  DBSelectArea("ZA1")
                    //  ZA1->(dbSetOrder(4))
                    //  IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                    RecLock('ZA1', .F.)
                    ZA1->ZA1_STATUS := "B"
                    ZA1->(MsUnlock())
                    // ENDIF
                else
                    //DBSelectArea("ZA1")
                    //ZA1->(dbSetOrder(4))
                    //IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                    RecLock('ZA1', .F.)
                    ZA1->ZA1_STATUS := "2"
                    ZA1->(MsUnlock())
                    // ENDIF
                EndIf
            EndIf
        endif

        TMPSD4->(DbSkip())
    EndDo
    TMPSD4->(DbCloseArea())


Return

Static Function fPutEmp2()

    Default cProd := "10400040       "
    Default cRecSD4 := ""
    Local nX         := 0
    Local aCab       := {}
    Local aLine      := {}
    Local aItens     := {}
    lOCAL nAux := 0.00
    Local cArqLog   := "zImpCSV_" + dToS(Date()) + "_" + StrTran(Time(), ':', '-') + ".log"
    //Local aLineEnder := {}
    //Local aEnder     := {}
    Local cEol := chr(10)
    Private lMSHelpAuto     := .T.
    Private lAutoErrNoFile  := .T.
    Private lMsErroAuto     := .F.
    Begin Transaction
        cSql := "SELECT R_E_C_N_O_ [RECSD4], * FROM "+RetSqlName("SD4")+" SD4 (NOLOCK) "+cEol
        cSql +="WHERE SD4.D_E_L_E_T_ = '*'" + cEol
        cSql +="AND SD4.D4_FILIAL   = " + VALTOSQL(xfilial("SD4"))+cEol
        //  cSql +="AND D4_COD          = " + VALTOSQL(cProd)+cEol
        cSql +="and D4_QUANT        > 0 "+cEol
        cSql +="and R_E_C_N_O_      in (SELECT ZA1_RECSD3 FROM "+RetSqlName("ZA1")+" (NOLOCK) ZA1 "+cEol
        cSql +="WHERE ZA1.D_E_L_E_T_ = '' AND ZA1.ZA1_STATUS  = '1' ) "

        If Select('TMPSD4') <> 0
            TMPSD4->(DbCloseArea())
        EndIf

        TCQuery cSql Alias  TMPSD4 New

        While TMPSD4->(!EOF())
            cProd :=TMPSD4->D4_COD
            cLote :=""
            DBSelectArea("ZA1")
            ZA1->(dbSetOrder(4))
            IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                cLote := ZA1->ZA1_DLPLTC
            endif
            //Monta o cabeçalho com o número da OP que será alterada.
            //Necessário utilizar o índice 2 para efetuar a alteração.
            aCab := {{"D4_OP", TMPSD4->D4_OP,NIL},;
                {"INDEX",2,Nil}}
            aItens     := {}
            //Seta o índice da SDC
            //   SDC->(dbSetOrder(2))

            //Busca os empenhos da SD4 para alterar/excluir.
            SD4->(dbSetOrder(2))
            if  SD4->(dbSeek(xFilial("SD4")+PadR(  TMPSD4->D4_OP,Len(SD4->D4_OP))))


                While SD4->(!Eof()) .And. SD4->(D4_FILIAL+D4_OP) == xFilial("SD4")+PadR( TMPSD4->D4_OP,Len(SD4->D4_OP))
                    //Adiciona as informações do empenho, conforme estão na tabela SD4.
                    aLine := {}
                    For nX := 1 To SD4->(FCount())
                        aAdd(aLine,{SD4->(Field(nX)),SD4->(FieldGet(nX)),Nil})
                    Next nX

                    //Adiciona o identificador LINPOS para identificar que o registro já existe na SD4
                    aAdd(aLine,{"LINPOS","D4_COD+D4_TRT+D4_LOTECTL+D4_NUMLOTE+D4_LOCAL+D4_OPORIG+D4_SEQ",;
                        SD4->D4_COD,;
                        SD4->D4_TRT,;
                        SD4->D4_LOTECTL,;
                        SD4->D4_NUMLOTE,;
                        SD4->D4_LOCAL,;
                        SD4->D4_OPORIG,;
                        SD4->D4_SEQ})
                    //Marca o empenho do produto "MP" como Excluído.
                    if cProd ==   SD4->D4_COD
                        aAdd(aLine,{"AUTDELETA","S",Nil})
                    endif


                    //Adiciona as informações do empenho no array de itens.
                    aAdd(aItens,aLine)

                    //Próximo registro da SD4.
                    SD4->(dbSkip())
                End
                cLote := ""
                aLine := {}
                aAdd(aLine,{"D4_OP"     ,TMPSD4->D4_OP     ,NIL})
                aAdd(aLine,{"D4_COD"    ,PADR( ALLTRIM(TMPSD4->D4_COD ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") ) ,NIL})
                aAdd(aLine,{"D4_LOCAL"  ,TMPSD4->D4_LOCAL  ,NIL})
                aAdd(aLine,{"D4_DATA"   ,dDatabase  ,NIL})
                aAdd(aLine,{"D4_QTDEORI",TMPSD4->D4_QTDEORI,NIL})
                aAdd(aLine,{"D4_QUANT"  ,TMPSD4->D4_QUANT  ,NIL})
                if !Empty(cLote)
                    aAdd(aLine,{"D4_LOTECTL",PADR( ALLTRIM(cLote) ,GETSX3CACHE("D4_LOTECTL","X3_TAMANHO") ) ,NIL})
                    aAdd(aLine,{"D4_DTVALID", STOD("20491231"),NIL})
                else

                    aadd(aLine,{"D4_LOTECTL", criavar('D4_LOTECTL'), Nil}) //Lote destino
                    aadd(aLine,{"D4_NUMLOTE", criavar('D4_NUMLOTE'), Nil}) //sublote destino
                    //  aadd(aLine,{"D4_DTVALID", criavar('D4_DTVALID'), Nil}) //validade lote destino
                endif
                aAdd(aLine,{"D4_TRT"    ,TMPSD4->D4_TRT    ,NIL})
                aAdd(aLine,{"D4_ROTEIRO",TMPSD4->D4_ROTEIRO,NIL})
                aAdd(aLine,{"D4_OPERAC",TMPSD4->D4_OPERAC,NIL})
                aAdd(aItens,aLine)
                cCodPrd := PADR( ALLTRIM(TMPSD4->D4_COD ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") )
                lRastro := rastro(cCodPrd,"L")
                CONOUT("STOP")
                lMsErroAuto := .F.
                if len(aItens) == 1

                    //  aItensDel :={}
                    //Executa o MATA381, com a operação de Exclusão.
                    MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,3)
                else

                    //Executa o MATA381, com a operação de Alteração.
                    MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,4)
                endif
                If lMsErroAuto
                    //Se ocorrer erro.
                    aLogAuto := GetAutoGRLog()
                    cDir := "C:\LogDelpi\"
                    cArqLog := "LOG_mata381" + dToS(Date()) + "_" + StrTran(Time(), ':', '-') + ".log"
                    //Percorrendo o Log e incrementando o texto (para usar o CRLF você deve usar a include "Protheus.ch")
                    cLogTxt :=""
                    For nAux := 1 To Len(aLogAuto)
                        cLogTxt += aLogAuto[nAux] + CRLF
                    Next
                    MemoWrite(cDir+cArqLog, cLogTxt)
                    conout(cLogTxt)
                    DBSelectArea("ZA1")
                    ZA1->(dbSetOrder(4))
                    IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                        RecLock('ZA1', .F.)
                        ZA1->ZA1_STATUS := "B"
                        ZA1->(MsUnlock())
                    ENDIF
                    DisarmTransaction()
                    Return
                else
                    DBSelectArea("ZA1")
                    ZA1->(dbSetOrder(4))
                    IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                        RecLock('ZA1', .F.)
                        ZA1->ZA1_STATUS := "2"
                        ZA1->(MsUnlock())
                    ENDIF
                EndIf
            else
                //Adiciona novo empenho com utilização de Lote.
                //A data de validade do lote é preenchida automaticamente pelo programa e não precisa ser enviada no array.
                DBSelectArea("ZA1")
                ZA1->(dbSetOrder(4))
                IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                    cCodPrd := PADR( ALLTRIM(ZA1->ZA1_COD   ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") )
                    lRastro := rastro(cCodPrd,"L")
                    CONOUT("STOP")
                    aCab := {{"D4_OP",ZA1->ZA1_OP,NIL}}
                    dDatabase := ZA1->ZA1_DATA
                    aLine := {}
                    aAdd(aLine,{"D4_OP"     ,ZA1->ZA1_OP      ,NIL})
                    aAdd(aLine,{"D4_COD"    ,PADR( ALLTRIM(ZA1->ZA1_COD   ) ,GETSX3CACHE("D4_COD","X3_TAMANHO") )    ,NIL})

                    aAdd(aLine,{"D4_LOCAL"  ,"99"              ,NIL})
                    aAdd(aLine,{"D4_DATA"   , ZA1->ZA1_DATA,NIL})
                    aAdd(aLine,{"D4_QTDEORI", ZA1->ZA1_QTDEOR                ,NIL})
                    aAdd(aLine,{"D4_QUANT"  , ZA1->ZA1_QUANT                ,NIL})
                    cLote := ""
                    if !Empty(cLote)
                        aAdd(aLine,{"D4_LOTECTL",PADR( ALLTRIM(cLote) ,GETSX3CACHE("D4_LOTECTL","X3_TAMANHO") ) ,NIL})
                        aAdd(aLine,{"D4_DTVALID", STOD("20491231"),NIL})
                    else

                        aadd(aLine,{"D4_LOTECTL", criavar('D4_LOTECTL'), Nil}) //Lote destino
                        aadd(aLine,{"D4_NUMLOTE", criavar('D4_NUMLOTE'), Nil}) //sublote destino
                        //   aadd(aLine,{"D4_DTVALID", criavar('D4_DTVALID'), Nil}) //validade lote destino
                    endif

                    //  aAdd(aLine,{"D4_LOTECTL",PADR( ALLTRIM(cLote  ) ,GETSX3CACHE("D4_LOTECTL","X3_TAMANHO") )               ,NIL})
                    //  aAdd(aLine,{"D4_DTVALID", STOD("20491231"),NIL})

                    aAdd(aLine,{"D4_ROTEIRO",ZA1->ZA1_CDROT              ,NIL})
                    aAdd(aLine,{"D4_OPERAC",ZA1->ZA1_OPERAC              ,NIL})

                    //Adiciona a linha do empenho no array de itens.
                    aAdd(aItens,aLine)
                    lMsErroAuto := .F.
                    MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,3)

                    If lMsErroAuto
                        aLogAuto := GetAutoGRLog()
                        cDir := "C:\LogDelpi\"
                        cArqLog := "LOG_mata381" + dToS(Date()) + "_" + StrTran(Time(), ':', '-') + ".log"
                        //Percorrendo o Log e incrementando o texto (para usar o CRLF você deve usar a include "Protheus.ch")
                        cLogTxt :=""
                        For nAux := 1 To Len(aLogAuto)
                            cLogTxt += aLogAuto[nAux] + CRLF
                        Next
                        conout(cLogTxt)
                        MemoWrite(cDir+cArqLog, cLogTxt)
                        //Se ocorrer erro.
                        //  MostraErro()
                        //  DBSelectArea("ZA1")
                        //  ZA1->(dbSetOrder(4))
                        //  IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                        RecLock('ZA1', .F.)
                        ZA1->ZA1_STATUS := "B"
                        ZA1->(MsUnlock())
                        // ENDIF
                        DisarmTransaction()
                        Return
                    else
                        //DBSelectArea("ZA1")
                        //ZA1->(dbSetOrder(4))
                        //IF ZA1->(dbSeek( xfilial("ZA1")+TMPSD4->D4_COD+TMPSD4->D4_OP ))
                        RecLock('ZA1', .F.)
                        ZA1->ZA1_STATUS := "2"
                        ZA1->(MsUnlock())
                        // ENDIF
                    EndIf
                EndIf
            endif

            TMPSD4->(DbSkip())
        EndDo
        TMPSD4->(DbCloseArea())

    End Transaction
Return

// /*/{Protheus.doc} fPutLote
// @Description
// @Type
// @Author 	 TSC - Gabriel Araujo
// @Since  	 25/04/2025
// /*/
// Static Function fPutLote(cCodProd,nQuant)

//     Local aArea := getarea()
//     Private lMsErroAuto := .f.

//     cLote   := NextLote(,"L")
//     //    cRecSD4 := fDelEmp( cCodProd,cLote,nQuant	)

//     Begin Transaction
//         cLote   := NextLote(cCodProd,"L")
//         cFunBkp := FunName()
//         SetFunName("MATA220")

//         aadd(aLote,{"D5_PRODUTO"	, cCodProd     , NIL} )
//         aadd(aLote,{"D5_LOCAL"      ,dDatabase     , NIL} )
//         aadd(aLote,{"D5_LOCAL"      ,cLocal        , NIL} )
//         aadd(aLote,{"D5_DOC"		,cNF           , Nil} )
//         aadd(aLote,{"D5_SERIE"		, cSerie       , Nil} )
//         aadd(aLote,{"D5_DATA"       , DDATABASE	   , NIL} )
//         aadd(aLote,{"D5_QUANT"      , nQuant            , NIL} )
//         aadd(aLote,{"D5_LOTECTL"	, cLote             , NIL} )
//         aadd(aLote,{"D5_DTVALID"	, STOD("20491231")  , NIL} )
//         aadd(aLote,{"D5_CLIFOR"	    , cForLt         , NIL} )
//         aadd(aLote,{"D5_LOJA"	    , cLojLt         , NIL} )

//         DbSelectArea("SB1")
//         SB1->(DbSetOrder(1))
//         SB1->(DbSeek(xfilial("SA2")+cCodProd))

//         lMsErroAuto := .f.
//         //  MSExecAuto({|x,y| Mata390(x,y)}, aLote, 3)
//         FWMsgRun(, {|| MSExecAuto({|x,y| Mata390(x,y)}, aLote, 3) } ,;
//             "Delpi - Mata390", cLocal + " - Gerando  "+alltrim(cLote)+" - "+ alltrim(cCodProd))
//         If lMsErroAuto
//             mostraerro()
//             SetFunName(cFunBkp)
//             DisarmTransaction()
//             Return .f.
//         endif
//         SetFunName(cFunBkp)
//     End Transaction
// Return .t.


User Function D10E05B()

    cEmpJob	:= "01"
    cFilJob	:= "02"
    CONOUT("Chamou o Job D10E05B")
    //-- Evita que se consuma licenca
    //RpcSetType( 3 )

    If Select("SX6") == 0
        CONOUT("ENTROU NO X6")
        RpcSetType(3)

        RpcSetEnv(cEmpJob,cFilJob)

    EndIf
    CONOUT("Chamou o Job D10E05B cempant "+cempant)
    CONOUT("Chamou o Job D10E05B cfilant "+cfilant)
    fPutEmp2()
rETURN
