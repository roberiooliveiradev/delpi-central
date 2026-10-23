#Include 'fileio.ch'
#Include 'Protheus.ch'
#Include "totvs.ch"
#Include "rwmake.ch"
#Include 'TOPCONN.CH'

/*=========================================================================*\
|| ####################################################################### ||
|| # Sistema:  IMPRESSAO DE ETIQUETA DE EMBALAGEM						 # ||
|| #                                                                     # ||
|| # Objetivo: Programa de impress�o de embalagens						 # ||
|| #                                                                     # ||
|| # Autor:    Everton Boing                                      		 # ||
|| # Data:     Fevereiro DE 2018                                         # ||
|| ####################################################################### ||
\*=========================================================================*/

User Function DLP10E01(cNumOP,cDescCli,cCod,cCodCli,nPesoEtiq,cCodBar,nQtdEmb,dDtApo)

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

    //  default aPars := {}
    PRIVATE lMsErroAuto := .F.


    aDir(cDir+"*.txt", aFiles, aSizes)

    // Apago os arquivos encontrados.
    ////////////////////////////////////////////////////////////////////////////////////////////
    //For _x := 1 to Len( aFiles )
    //    fErase(cDir+aFiles[_x])
    //Next _x

    nHdlMod := FT_FUse(cDir+cEtiq)

    If nHdlMod == -1
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
        /*
        */
lAltLin := .f.
If "@QRCODEDELPI" $ cLinha
	cQrcode     := alltrim(cCodCli)+" / "
	cQrcode     += alltrim(cCod)+" / "
	cQrcode 	+= alltrim(cNumOp)+" / "
	cQrcode 	+= Transform( StrZero ((nQtdEmb * 1000),4), "@E 999999") +" / "
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
ElseIf "@CODBAR2" $ cLinha
	cLinha := StrTran(cLinha,"@CODBAR2",AllTrim(SubStr(cCodBar,9,4)))
	lAltLin := .t.
ElseIf "@CODBAR" $ cLinha
	cLinha := StrTran(cLinha,"@CODBAR",AllTrim(SubStr(cCodBar,1,8)))
	lAltLin := .t.
ElseIf "@QUANTDLP" $ cLinha
	cLinha := StrTran(cLinha,"@QUANTDLP",Alltrim(Transform(nQtdEmb, X3Picture("B1_EMBDELP"))))
	lAltLin := .t.
ElseIf "@DATADLP" $ cLinha
	cLinha := StrTran(cLinha,"@DATADLP",Alltrim( Dtoc(dDtApo)))
	lAltLin := .t.
ENDIF

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
conout( " /c print "+cArqNovo+" ")
conout(cDir)
ShellExecute( "Open", "C:\Windows\System32\cmd.exe", " /c print "+cArqNovo+" ", cDir, 0 )

Sleep( 500 )

REturn
