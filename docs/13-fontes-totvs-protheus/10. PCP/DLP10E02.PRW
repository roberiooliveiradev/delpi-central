#Include 'fileio.ch'
#Include 'Protheus.ch'
#Include "totvs.ch"
#Include "rwmake.ch"
#Include 'TOPCONN.CH'

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

User Function DLP10E02()

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
    Local cDir := "C:\Etiqueta2\"
    Local cEtiqLogo := "ApenasLogo.prn"
    Local cEtiqMod := "ModSemLogo.txt"
    Local cDirEtLog := "F:\SISTEMAS\Totvs\Totvs_Data_12\Etiqueta\" //caminho completo
    Local cPrev14 := ""
    Local cEan132 := ""
    Local cDun14 := ""
    Local aCodBar := {}
    Local l5,l7 := .F.
    Local nContx

    //  default aPars := {}
    PRIVATE lMsErroAuto := .F.

    //cArqNovo := Alltrim("etiqueta_")+Alltrim(StrTran(Time(), ":", ""))+".TXT"
    cArqNovo := "teste.txt"
    aDir(cDir+"*.txt", aFiles, aSizes)

    // Apago os arquivos encontrados.
    ////////////////////////////////////////////////////////////////////////////////////////////
    // For _x := 1 to Len( aFiles )
    //     fErase(cDir+aFiles[_x])
    // Next _x

    // Copia arquivo do servidor para o client, alterando o nome do arquivo
    //bOk := CpyS2TEx( "c:\protheus\environment\ApData\report.htm", "C:\Dir\index.html" )
    /*pego do servidor e disponiblizo na maquina*/
    bOk := CpyS2TEx( cDirEtLog+cEtiqLogo, cDir+cArqNovo )

    if !bOk
        msgstop("deuerro")
        RETURN
    endif

    // Abre o arquivo modelo
    nHandle1 := fopen(cDir+cArqNovo , FO_READWRITE + FO_SHARED )
    If nHandle1 == -1
        MsgStop('Erro de abertura : FERROR '+str(ferror(),4))
    Else
        FSeek(nHandle1, 0, FS_END)         // nHandle1 Posiciona no fim do arquivo
        nHdlMod := FT_FUse(cDir+cEtiqMod)
        FT_FGoTop()
        While !FT_FEoF()
            CLINHA := FT_FREADLN() + CEOL

            If FWRITE(nHandle1,CLINHA,LEN(CLINHA)) != LEN(CLINHA)
                If !MsgAlert("Ocorreu um erro na gravação do arquivo. Deseja continuar?","ATENÇÃO")
                    //      EXIT
                EndIf
            EndIf
            FT_FSKIP()
        EndDo

        FT_FUse()
        // FWrite(nHandle, "Nova Linha", 10) // Insere texto no arquivo
        FClose(NHDLMOD)
        fclose(nHandle1)                   // nHandle1 Fecha arquivo
        MsgAlert('Processo concluído')
    Endif


    //  nHdlMod := FT_FUse(cDir+cEtiq)

    /*   If nHdlMod == -1
        MsgAlert("O arquivo de nome "+cDir+cEtiq+" nao pode ser aberto!!!.","Atencao")
        Return
    Endif

    cArqNovo := Alltrim("etiqueta_")+Alltrim(StrTran(Time(), ":", "_"))+".TXT"
    nHdlNovo := fCreate(cDir+cArqNovo)

    If nHdlNovo == -1
        MsgAlert("O arquivo de nome "+cDir+cArqNovo+" nao pode ser criado!!!","Atencao")
        Return
    Endif
    FT_FGOTOP()
    nLin := 1
    While !FT_FEOF()

        cLinha := FT_FREADLN()+cEol

        lAltLin := .f.
        If "@QRCODEDELPI" $ cLinha
            cQrcode     := cCod+cEol
            cQrcode 	+= cNumOp+cEol
            cQrcode 	+= Transform( StrZero ((nQtdEmb * 1000),4), "@E 9999") +cEol
            cQrcode 	+= dtoc(dDtApo)
            cLinha      := StrTran(cLinha,"@QRCODEDELPI",Alltrim(cQrcode))
            //  lAltLin := .t.
        ElseIf "@ORDEMDEPROD" $ cLinha
            cLinha := StrTran(cLinha,"@ORDEMDEPROD",Alltrim(cNumOP))
            lAltLin := .t.
        ElseIf "@DESCCLIENTE" $ cLinha
            cLinha := StrTran(cLinha,"@DESCCLIENTE",Alltrim(cDescCli))
            lAltLin := .t.
        ElseIf "@CODDELPI" $ cLinha
            cLinha := StrTran(cLinha,"@CODDELPI",Alltrim(cCod))
            lAltLin := .t.
        ElseIf "@CODCLIENTE" $ cLinha
            cLinha := StrTran(cLinha,"@CODCLIENTE",Alltrim(cCodCli))
            lAltLin := .t.
        ElseIf "@PESODLP" $ cLinha
            cLinha := StrTran(cLinha,"@PESODLP",Alltrim(Transform(nPesoEtiq, X3Picture("B1_PESO"))))
            lAltLin := .t.
        ElseIf "@CODBAR" $ cLinha
            cLinha := StrTran(cLinha,"@CODBAR",Alltrim(cCodBar))
            lAltLin := .t.
        ElseIf "@QUANTDLP" $ cLinha
            cLinha := StrTran(cLinha,"@QUANTDLP",Alltrim(Transform(nQtdEmb, X3Picture("B1_EMBDELP"))))
            lAltLin := .t.
        ElseIf "@DATADLP" $ cLinha
            cLinha := StrTran(cLinha,"@DATADLP",Alltrim( Dtoc(dDtApo)))
            lAltLin := .t.
        ENDIF

        //   if nLin ==14
        //       cLinha := cLin14
        //   endif

        If fWrite(nHdlNovo,cLinha,Len(cLinha)) != Len(cLinha)
            If !MsgAlert("Ocorreu um erro na gravacao do arquivo. Continua?","Atencao!")
                Exit
            Endif
        Endif
        nLin++
        FT_FSKIP()
    Enddo
    // fWrite(nHdlNovo,cLin14,Len(cLinha))
    FT_FUSE()

    FClose(nHdlMod)
    fClose(nHdlNovo)
    ShellExecute( "Open", "C:\Windows\System32\cmd.exe", " /c print "+cArqNovo+" ", cDir, 0 )
    Sleep( 500 ) */

REturn
