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

User Function DLP1_0E01(cNumOP,cDescCli,cCod,cCodCli,nPesoEtiq,cCodBar,nQtdEmb,dDtApo)

    Local aCabec := {}
    Local aItens := {}
    Local aCabA  := {}
    Local aIteA  := {}
    Local aLinha := {}
    Local aLinA  := {}
    Local cPerg  := "TAF0012"

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

    //  default aPars := {}
    PRIVATE lMsErroAuto := .F.


    // ShellExecute( "Open", "C:\Windows\System32\cmd.exe", " /c print "+cEtiq+" ", cDir, 0 )

    // cEan132  := "1"+Substr(cDes1,1,12)
    // cDun14  := alltrim(cEan132) + alltrim(EAN14(cEan132))
    //
    aDir(cDir+"*.txt", aFiles, aSizes)

    // Apago os arquivos encontrados.
    ////////////////////////////////////////////////////////////////////////////////////////////
    //   For _x := 1 to Len( aFiles )
    //       fErase(cDir+aFiles[_x])
    //   Next _x

    cArqNovo := Alltrim("Etiqueta")+Alltrim(StrTran(Time(), ":", "_"))+".txt"
    If CpyS2TEx( "F:\SISTEMAS\Totvs\Totvs_Data_12\Etiqueta\EtiquetaExp.prn", cDir+cArqNovo )
        Conout( 'Copiado com Sucesso' )
    Endif

    //   nHdlNovo := fopen(cDir+cArqNovo,2)
    //nHdlNovo := FT_FUse(cDir+cArqNovo )
    //   nTamFile := FSeek(nHdlNovo,0,FS_END)
    //  nTamFile := 47//FT_FLastRec()
    //  //nHdlNovo := FT_FUse(cDir+cArqNovo)
    //  //nHandle := fopen('\sigaadv\error.log' , FO_READWRITE + FO_SHARED )
    //  If nHdlNovo == -1
    //      MsgAlert("O arquivo de nome "+cDir+cArqNovo+" nao pode ser criado!!!","Atencao")
    //      Return
    //  Endif
    //  nLin := 1
    //  FT_FGOTOP()
    //  While !FT_FEOF() .and. nLin <=nTamFile

    //      cLinha := FT_FREADLN()
    //      /*
    //      */
    //      lAltLin := .f.
    //      If "@QRCODEDELPI" $ cLinha
    //          cQrcode     := cCod+cEol
    //          cQrcode 	+= cNumOp+cEol
    //          cQrcode 	+= Transform( StrZero ((nQtdEmb * 1000),4), "@E 9999") +cEol
    //          cQrcode 	+= dtoc(dDtApo)
    //          cLinha      := StrTran(cLinha,"@QRCODEDELPI",Alltrim(cQrcode))
    //          //  lAltLin := .t.
    //      ElseIf "@ORDEMDEPROD" $ cLinha
    //          cLinha := StrTran(cLinha,"@ORDEMDEPROD",Alltrim(cNumOP))
    //          lAltLin := .t.
    //      ElseIf "@DESCCLIENTE" $ cLinha
    //          cLinha := StrTran(cLinha,"@DESCCLIENTE",Alltrim(cDescCli))
    //          lAltLin := .t.
    //      ElseIf "@CODDELPI" $ cLinha
    //          cLinha := StrTran(cLinha,"@CODDELPI",Alltrim(cCod))
    //          lAltLin := .t.
    //      ElseIf "@CODCLIENTE" $ cLinha
    //          cLinha := StrTran(cLinha,"@CODCLIENTE",Alltrim(cCodCli))
    //          lAltLin := .t.
    //      ElseIf "@PESODLP" $ cLinha
    //          cLinha := StrTran(cLinha,"@PESODLP",Alltrim(Transform(nPesoEtiq, X3Picture("B1_PESO"))))
    //          lAltLin := .t.
    //      ElseIf "@CODBAR" $ cLinha
    //          cLinha := StrTran(cLinha,"@CODBAR",Alltrim(cCodBar))
    //          lAltLin := .t.
    //      ElseIf "@QUANTDLP" $ cLinha
    //          cLinha := StrTran(cLinha,"@QUANTDLP",Alltrim(Transform(nQtdEmb, X3Picture("B1_EMBDELP"))))
    //          lAltLin := .t.
    //      ElseIf "@DATADLP" $ cLinha
    //          cLinha := StrTran(cLinha,"@DATADLP",Alltrim( Dtoc(dDtApo)))
    //          lAltLin := .t.
    //      ENDIF

    //      if lAltLin
    //          FT_Write(nHdlNovo,cLinha,Len(cLinha)) != Len(cLinha)
    //          //If fWrite(nHdlNovo,cLinha,Len(cLinha)) != Len(cLinha)
    //          //    conout("deu merda")
    //          //    nret := FError()
    //          //    MsgAlert("Ocorreu um erro na gravacao do arquivo. Continua?","Atencao!")
    //          //    // If !MsgAlert("Ocorreu um erro na gravacao do arquivo. Continua?","Atencao!")
    //          //    //     Exit
    //          //    // Endif
    //          //Endif
    //      Endif
    //      FT_FSKIP()
    //      nLin++
    //  Enddo
    //  FT_FUSE()

    //  //  FClose(nHdlMod)
    //  fClose(nHdlNovo)
    //   ShellExecute( "Open", "C:\Windows\System32\cmd.exe", " print "+cDir+cArqNovo, cDir, 0 )
    //  ShellExecute( "Open", "C:\Windows\System32\cmd.exe", " print "+cDir+cArqNovo, "c:\", 0 )
    // WaitRun(" print "+cDir+cArqNovo,0)
    ShellExecute("print",cArqNovo,"",cDir,0)
    Sleep( 500 )

REturn
