#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "protheus.ch"

//Static Function DLP10E03(cProd,cNumOp,nQtd,dEmiss,nSeq)
Static Function DLP10E03()
    Local cEol 		:= chr(10)
    Local cFile 	:= ""
    Local cFolder 	:= "C:\TEMP\"
    Local cFldSrv	:= "\ETIQUETAS\"
    Local cFldSrvF	:= "F:\SISTEMAS\Totvs\Totvs_Data_12\etiquetas\"
    Local lRet 		:= .F.
    Local cDirMagic :=  "F:\SISTEMAS\Totvs\ImageMagick\"
    Local cComando  := ""
    Local cFilebmp  := ""
    Local cQrcode  := ""
    Local cDirSrv   := Alltrim(GetSrvProfString("RootPath",""))+"\ETIQUETAS\"
    //convert C:\temp\gda085141_2.pdf -monochrome 085141_04.bmp
    LOCAL AFILES := {}
    LOCAL ASIZES := {}
    Private oPrint 	:= nil

    lAdjustToLegacy := .f.
    lDisableSetup  	:= .T.

    //Material;
    //Lote de fabricação;
    //Quantidade;
    //Data.
    /* cNumOp:=alltrim(cNumOp)
    cFile 		:= alltrim(cNumOp)+STRZERO(nSeq,3)
    cFilename 		:=cFile+".rel"
    cFilePdf 	:= cFile+".pdf"
    cFilebmp	:= cFile+".bmp"
    cFilejpg	:= cFile+".jpg"
    cFilePrint 	:= cFolder+cFilePdf
    cCmd1:=cDirMagic +'magick  mogrify -format jpg "'+cFldSrvF+cFilePdf+'"'
    //cCmd2:=cDirMagic +'convert -monochrome "'+cFldSrvF+cFilejpg+'" -crop -446-692 "'+cFldSrvF+cFilebmp+'" '
    cCmd2:=cDirMagic +'convert -monochrome -crop 210X210+1+1  "'+cFldSrvF+cFilejpg+'"  "'+cFldSrvF+cFilebmp+'" '
    //cCmd2:=cDirMagic +'convert -monochrome -trim "'+cFldSrvF+cFilejpg+'"  "'+cFldSrvF+cFilebmp+'" '
    cQrcode 	+= cProd+cEol
    cQrcode 	+= cNumOp+cEol
    cQrcode 	+= Transform( StrZero ((nQtd * 1000),4), "@E 9999") +cEol
    cQrcode 	+= dtoc(dEmiss)

    ADIR(cFolder +cNumOp+ "*.PDF", AFILES, ASIZES)

    // APAGADAS CHAMADAS DE IMPRESSAO EXISTENTES \\
    FOR _X := 1 TO LEN( AFILES )
        FERASE(cFolder + AFILES[_X])
    NEXT _X*/

    oPrint 			:= FWMSPrinter():New(cFilename,IMP_PDF ,lAdjustToLegacy, cFolder,.T.)
    //	APARS:=fGetLin()
    oPrint:SetPaperSize(0,685,100)
    //oPrint:SetPaperSize(9)
    //oPrint:QRCode(APARS[1],01,cQrcode, APARS[1])
    //oPrint:QRCode(210,02,cQrcode, 210)
    oPrint:SetViewPDF ( .t. )
    File2Printer( cFilePrint, "PDF" )
    oPrint:cPathPDF := cFolder
    oPrint:Preview()


REturn

