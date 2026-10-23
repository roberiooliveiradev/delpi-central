#INCLUDE "PROTHEUS.CH"
#INCLUDE "TBICONN.CH"
#INCLUDE "COLORS.CH"
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "danfcom.ch"

static oQry	:= nil

CLASS PrtDanfeCom
	Data oPrinter
	Data cPathPDF
	Data nDevice
	Data cFilePrint
	Data aMessages  AS Array
	Data aItens     AS Array
	Data aTotais    AS Array
	Data nVTotal
	Data nQtd
	Data nVUnit
	Data nCor
	Data cAutoriza
	Data cModalidade
	Data dDataAt
	Data cRetMsg
	Data cCodAutSef

	Data MAXMENLIN      	    // Máximo de caracteres por linha de dados adicionais
	Data MAXMSG        		    // Máximo de dados adicionais por página
	Data MAXONLYMSG  		    // Máximo de dados adicionais por página
	Data nTotItsPag AS Integer  // maximo de itens por pagina

	Data oFont07
	Data oFont08
	Data oFont09
	Data oFont10
	Data oFont11
	Data oFont14
	Data oFont07N
	Data oFont08N
	Data oFont09N
	Data oFont10N
	Data oFont12N
	Data oFont18N
	Data oFont14N

	Method New() Constructor
	Method ConfigurePrinter()           // Método para configurar o Printer
	Method ProcessXML()                 // Método para processar o XML
	Method ValidateXML()                // Método para validar o XML
	Method PrintDetails()               // Método para imprimir
	Method SetPrint()                   // Método para imprimir relatorio
	Method SetHeader()                  // Método para o cabeçalho
	Method SetNFCom()                   // Método para o box da NFCom serie/nota
	Method SetChvAcesso()               // Método para o box da NFCom chave de acesso
	Method SetDest()                    // Método para o box do destinatário
	Method SetAssinante()               // Método para o box do assinante
	Method SetContrib()                 // Método para o box do contribuinte
	Method SetItens()                   // Método para o box dos itens
	Method SetTotal()                   // Método para o box dos totais
	Method SetAnatel()                  // Método para o box da anatel
	Method ProcessItems()               // Método para processar os itens
	Method ProcessImp()                 // Método para processar os impostos
	Method SetInfCPL()                  // Método para o rodapé e informações complementares
	Method GetXML()                     // Método para fazer o parser do xml
	Method impIt()                      // Método para imprimir o conteudo dos itens.
	Method ItemBox()                    // Método para o box dos itens
	Method AddFormattedMessage()        // Método para Tratar as msg que vão no infcpl
	Method AddComplementaryMessages()   // Método para Tratar as msg que vão no infcpl
	Method GetFonts()                   // Método para obter as fontes
	Method Finalize()                   // Método para finalizar
	Method CalculateTotalFolhas()       // Método para calcular o total de folhas
	Method SetMarca()                   // Marca d agua

ENDCLASS

Static Function TSSDANFECOM(aXmlNfcom, oDanfcom, cIdEnt, nVias, cAmbiente)
	Local oDanfe    := Nil
	Local lSuccess  := .F.

	Default cIdEnt	    := ""
	Default aXmlNfcom	:= {}
	Default nVias		:= 1
	Default cAmbiente	:= "2"

	oDanfe := oDanfcom

	// Processar os XMLs e realizar a impress o
	If oDanfe <> Nil
		lSuccess := oDanfe:ProcessXML(aXmlNfcom, nVias, cIdEnt, cAmbiente)
	EndIf

	If lSuccess
		oDanfe:oPrinter:Preview()
	Else
    	Aviso(STR0010,STR0011,{STR0012},3)
	EndIf

	// Finalizar e liberar recursos
	oDanfe:Finalize()

Return lSuccess

Method New(cPathPDF, cFilePrint, nDevice, lBuffer) CLASS PrtDanfeCom
	local cBarDe := "\"
	local cBarPara := "/"

	Default cPathPDF    := "\SPOOL\"
	Default lBuffer     := .T.
	Default cFilePrint  := "danfecom_"+Dtos(MSDate())+StrTran(Time(),":","")
	Default nDevice     := IMP_PDF

	If !issrvunix() //Windows
		cBarDe := "/"
		cBarPara := "\"
	EndIf

	Self:cPathPDF := StrTran(cPathPDF, cBarDe, cBarPara)

	If !Empty(cFilePrint)
		Self:cFilePrint := cFilePrint
	EndIf

	If !Empty(nDevice)
		Self:nDevice    := nDevice
	EndIf

	If !ExistDir(Self:cPathPDF)
		MakeDir(Self:cPathPDF)
	EndIf

	Self:MAXMENLIN  := 80
	Self:MAXMSG     := 20
	Self:MAXONLYMSG := 40
	Self:nTotItsPag := 15

	Self:oPrinter := FWMSPrinter():New(Self:cFilePrint, Self:nDevice /*,.F., Self:cPathPDF, .T.,,,,,,,,,,lBuffer*/)
	Self:ConfigurePrinter()
Return Self

Method ConfigurePrinter() CLASS PrtDanfeCom
	Self:oPrinter:lServer      := .T.
	Self:oPrinter:lPDFAsPNG    := .T.
	Self:oPrinter:SetResolution(78)
	Self:oPrinter:SetPortrait()
	Self:oPrinter:SetPaperSize(DMPAPER_A4)
	Self:oPrinter:SetMargin(60, 60, 60, 60)
	Self:oPrinter:SetViewPDF(.T.)
	//Self:oPrinter:Setup()
Return

Method GetFonts() CLASS PrtDanfeCom
	Self:oFont07    := TFontEx():New(Self:oPrinter,"Times New Roman",06,06,.F.,.T.,.F.)// 3
	Self:oFont08    := TFontEx():New(Self:oPrinter,"Times New Roman",07,07,.F.,.T.,.F.)// 4
	Self:oFont09    := TFontEx():New(Self:oPrinter,"Times New Roman",08,08,.F.,.T.,.F.)// 7
	Self:oFont10    := TFontEx():New(Self:oPrinter,"Times New Roman",09,09,.F.,.T.,.F.)// 8
	Self:oFont11    := TFontEx():New(Self:oPrinter,"Times New Roman",10,10,.F.,.T.,.F.)// 9
	Self:oFont14    := TFontEx():New(Self:oPrinter,"Times New Roman",14,14,.F.,.T.,.F.)// 10
	Self:oFont07N   := TFontEx():New(Self:oPrinter,"Times New Roman",06,06,.T.,.T.,.F.)// 2
	Self:oFont08N   := TFontEx():New(Self:oPrinter,"Times New Roman",08,08,.T.,.T.,.F.)// 5
	Self:oFont09N   := TFontEx():New(Self:oPrinter,"Times New Roman",09,09,.T.,.T.,.F.)// 6
	Self:oFont10N   := TFontEx():New(Self:oPrinter,"Times New Roman",10,10,.T.,.T.,.F.)// 1
	Self:oFont12N   := TFontEx():New(Self:oPrinter,"Times New Roman",12,12,.T.,.T.,.F.)// 11
	Self:oFont18N   := TFontEx():New(Self:oPrinter,"Times New Roman",18,18,.T.,.T.,.F.)// 12
	Self:oFont14N   := TFontEx():New(Self:oPrinter,"Times New Roman",14,14,.T.,.T.,.F.)// 14
Return Self

Method ProcessXML(aXmlNfcom, nVias, cIdEnt, cAmbiente) CLASS PrtDanfeCom
	Local aNfcomObjects := {}
	Local nX            := 0
	Local lImprimiu     := .F.
	Local oXmlData      := Nil

	Default aXmlNfcom   := {}
	Default nVias       := 1
	Default cIdEnt      := ""
	Default cAmbiente   := "2"

	Private cAmb        := cAmbiente

	aNfcomObjects := Self:ValidateXML(aXmlNfcom)

	If Len(aNfcomObjects) > 0
		For nX := 1 To Len(aNfcomObjects)
			oXmlData := aNfcomObjects[nX]
			Self:PrintDetails(oXmlData, nVias, cIdEnt)
			lImprimiu := .T.
		Next nX
	EndIf

	fwfreearray(aNfcomObjects)
	aNfcomObjects := {}

	fwFreeObj(oXmlData)
	oXmlData := Nil

Return lImprimiu

Method ValidateXML(aXmlNfcom) CLASS PrtDanfeCom
	Local aNfcomObjects := {}
	Local aXML          := {}
	Local nX            := 0
	Local cErro         := ""
	Local cAviso        := ""
	Local cMsgError     := ""
	Local oNfcom        := Nil

	Default aXmlNfcom   := {}

	For nX := 1 To Len(aXmlNfcom)

		// Obter o conteúdo do XML
		aXML := Self:GetXML(aXmlNfcom[nX], @cErro)

		// Processar o XML e criar o objeto oNfcom
		cAviso  := ""
		cErro   := ""
		cMsgError   := "NFCom nao Autorizada."
		If !Empty(aXML) .and. !empty(aXML[1]) //protocolo

			oNfcom := XmlParser(EncodeUtf8(aXML[2]), "_", @cAviso, @cErro)

			cMsgError := "Falha de parser: " + cErro + " - " + cAviso
			If oNfcom != Nil
				cMsgError := ""
				Self:cAutoriza      := aXML[1]
				Self:dDataAt        := aXML[7]
				Self:cRetMsg        := aXml[8]
				aAdd(aNfcomObjects, oNfcom)
			EndIf
		EndIf

		if !empty(cMsgError)
			Aviso(STR0010,STR0013+ Self:cFilePrint + STR0014 + cMsgError,{STR0012},3)
		endIf

		aXML := fwfreearray(aXML)

	Next nX

Return aNfcomObjects

Method PrintDetails(oXmlData, nVias, cIdEnt) CLASS PrtDanfeCom
	Private oNF        := oXmlData:_NFCOM
	Private oEmitente  := oNF:_INFNFCOM:_Emit
	Private oIdent     := oNF:_INFNFCOM:_IDE
	Private oDestino   := oNF:_INFNFCOM:_Dest
	Private oTotal     := oNF:_INFNFCOM:_Total
	Private oDet       := oNF:_INFNFCOM:_Det
	Private oAssinante := oNF:_INFNFCOM:_assinante
	Private oFatura    := Nil
	Private oImposto   := Nil

	Default oXmlData    := Nil
	Default nVias       := 1
	Default cIdEnt      := ""

	If Type("oNF:_INFNFCOM:_gFat") <> "U"
		oFatura := oNF:_INFNFCOM:_gFat
	EndIf

	If (ValType(oDet) == "O")
		oDet := {oDet}
	EndIf

	Self:GetFonts()
	Self:AddComplementaryMessages(oIdent, oNF)
	Self:SetPrint(oDestino, oIdent)

Return Self

Method SetTotal(oTotal) CLASS PrtDanfeCom
    local nLiTit    := 2185
    local nLinInfo  := 2205

    Default oTotal := Nil

    Self:aTotais := Array(15)
    AFill(Self:aTotais, 0)

    If Type("oTotal:_ICMSTOT:_vBC") <> "U"
        Self:aTotais[01] := Val(oTotal:_ICMSTOT:_vBC:TEXT)
    EndIf

    If Type("oTotal:_ICMSTOT:_vICMS") <> "U"
        Self:aTotais[02] := Val(oTotal:_ICMSTOT:_vICMS:TEXT)
    EndIf

    If Type("oTotal:_vCOFINS") <> "U"
        Self:aTotais[05] := Val(oTotal:_vCOFINS:TEXT)
    EndIf

    If Type("oTotal:_vPIS") <> "U"
        Self:aTotais[06] := Val(oTotal:_vPIS:TEXT)
    EndIf

    If Type("oTotal:_vFUNTTEL") <> "U"
        Self:aTotais[07] := Val(oTotal:_vFUNTTEL:TEXT)
    EndIf

    If Type("oTotal:_vFUST") <> "U"
        Self:aTotais[08] := Val(oTotal:_vFUST:TEXT)
    EndIf

    If Type("oTotal:_vOutro") <> "U"
        Self:aTotais[14] := Val(oTotal:_vOutro:TEXT)
    EndIf

    If Type("oTotal:_vNF") <> "U"
        Self:aTotais[15] := Val(oTotal:_vNF:TEXT)
    EndIf

 // BOX TRIBUTOS

    Self:oPrinter:Say(2150,010,"INFORMAÇÕES DOS TRIBUTOS/TOTAIS",Self:oFont10N:oFont)

    Self:oPrinter:Box(2160,000,2230,612)
    Self:oPrinter:Say(nLiTit,015,"PIS (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,015,Transform(Self:aTotais[06],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

    Self:oPrinter:Box(2160,611,2230,1212)
    Self:oPrinter:Say(nLiTit,626,"COFINS (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,626,Transform(Self:aTotais[05],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

    Self:oPrinter:Box(2160,1211,2230,1813)
    Self:oPrinter:Say(nLiTit,1226,"FUST (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,1226,Transform(Self:aTotais[08],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

    Self:oPrinter:Box(2160,1812,2230,2450)
    Self:oPrinter:Say(nLiTit,1827,"FUNTTEL (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,1827,Transform(Self:aTotais[07],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

    // BOX TOTAIS

    nLiTit := 2250
    nLinInfo := 2270
    Self:oPrinter:Box(2225,000,2295,490)
    Self:oPrinter:Say(nLiTit,015,"VALOR TOTAL NFF (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,015,Transform(Self:aTotais[15],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

    Self:oPrinter:Box(2225,489,2295,980)
    Self:oPrinter:Say(nLiTit,504,"TOTAL BASE DE CÁLCULO (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,504, Transform(Self:aTotais[01],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

    Self:oPrinter:Box(2225,979,2295,1470)
    Self:oPrinter:Say(nLiTit,994,"VALOR ICMS (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,994,Transform(Self:aTotais[02],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

    Self:oPrinter:Box(2225,1469,2295,1960)
    Self:oPrinter:Say(nLiTit,1484,"VALOR OUTROS (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,1484,Transform(Self:aTotais[14],"@e 9,999,999,999,999.99"),Self:oFont10:oFont)


    Self:oPrinter:Box(2225,1959,2295,2452)
    Self:oPrinter:Say(nLiTit,1974,"VALOR ISENTO (R$)",Self:oFont10N:oFont)
    Self:oPrinter:Say(nLinInfo,1974,Transform(0,"@e 9,999,999,999,999.99"),Self:oFont10:oFont)

Return Self

Method SetHeader(oEmitente) CLASS PrtDanfeCom
	Local cLogo       := FisxLogo("1")

	Default oEmitente := Nil

	Self:oPrinter:StartPage()

	Self:oPrinter:Box(000,000,270,2450)
	Self:oPrinter:SayBitmap(20,40,cLogo,270,220)
	Self:oPrinter:Say(050, 370, "DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA",Self:oFont14N:oFont)	//"Identificação do emitente"
	Self:oPrinter:Say(100, 370, "RAZÃO SOCIAL: " + AllTrim(oEmitente:_xNome:Text),Self:oFont14N:oFont) //Razão social
	Self:oPrinter:Say(150, 370, "ENDEREÇO: " + AllTrim(oEmitente:_EnderEmit:_xLgr:Text)+", "+AllTrim(oEmitente:_EnderEmit:_Nro:Text),Self:oFont14N:oFont) //Endereço
	Self:oPrinter:Say(200, 370, "CNPJ: " + oEmitente:_CNPJ:Text,Self:oFont14N:oFont) //CNPJ
	Self:oPrinter:Say(250, 370, "IE: " + If(Type("oEmitente:_IE") <> "U", oEmitente:_IE:TEXT, ""),Self:oFont14N:oFont) //IE

Return Self

Method SetNFCom(oIdent, oNF, nFolha, nFolhas) CLASS PrtDanfeCom
	Local cQrCode   := ""

	Default oIdent  := Nil
	Default oNF     := Nil
	Default nFolhas := 1
	Default nFolha  := 1

	Self:oPrinter:Box(280,000,600,1200)

	If Type('oNF:_INFNFCOMSUPL:_QRCODNFCOM') <> 'U' .And. !Empty(oNF:_INFNFCOMSUPL:_QRCODNFCOM:TEXT)
		cQrCode := oNF:_INFNFCOMSUPL:_QRCODNFCOM:TEXT
		nPos 	:= At("tpAmb=", cQrCode) + Len("tpAmb=")
		cQrCode := Substr(cQrCode, 1, nPos)
	EndIf

	Self:oPrinter:QRCode(560,040, cQrCode, 070)

	Self:oPrinter:Say(350,370, "NOTA FISCAL FATURA No. " +StrZero(Val(oIdent:_NNf:Text),9),Self:oFont14:oFont)	//"Identificação do emitente"
	Self:oPrinter:Say(390,370, "SÉRIE: " + oIdent:_Serie:Text,Self:oFont14:oFont)	//"Identificação do emitente"
	Self:oPrinter:Say(470,370, "DATA DE EMISSÃO: "+ ConvDate(oIdent:_DHEmi:TEXT),Self:oFont14:oFont)
	Self:oPrinter:Say(550,370, "FOLHA: "+ StrZero(nFolha,2)+"/"+StrZero(nFolhas,2),Self:oFont14:oFont)
Return Self

Method SetChvAcesso(oNF) CLASS PrtDanfeCom
	Default oNF := Nil

	Self:oPrinter:Box(605, 000, 970, 1200)  // Novo box com início abaixo do box anterior
	Self:oPrinter:Say(670, 040, "CONSULTE PELA CHAVE DE ACESSO EM:", Self:oFont14N:oFont)
	Self:oPrinter:Say(710, 040, "http://dfe-portal.svrs.rs.gov.br/nfcom/consulta",Self:oFont14N:oFont)
	Self:oPrinter:Say(800, 040, "CHAVE DE ACESSO:", Self:oFont14N:oFont)
	Self:oPrinter:Say(840, 040, TransForm(SubStr(oNF:_INFNFCOM:_ID:Text, 4), "@r 9999 9999 9999 9999 9999 9999 9999 9999 9999 9999 9999"), Self:oFont14N:oFont)	//"Identificação do emitente"
	Self:oPrinter:Say(940, 040, "Protocolo de Autorização: " + Self:cAutoriza + " - " + Self:dDataAt, Self:oFont14N:oFont)	//"Identificação do emitente"
Return Self

Method SetDest(oDestino, oIdent) CLASS PrtDanfeCom
	Local cCnpj   	:= Space(14)
	Local aDest	  	:= {}
	Local aLinesEnd := {}
	Local nLinhaY 	:= 1090
	Local nI		:= 0

	Default oDestino	:= Nil
	Default oIdent		:= Nil

	aDest := { ;
		oDestino:_EnderDest:_Xlgr:Text + ;
		(If(", SN" $ oDestino:_EnderDest:_Xlgr:Text, "", ", " + oDestino:_EnderDest:_NRO:Text + ;
		If(Type("oDestino:_EnderDest:_xCpl") <> "U", ", " + oDestino:_EnderDest:_xCpl:Text, ""))), ;
			oDestino:_EnderDest:_XBairro:Text, ;
			If(Type("oDestino:_EnderDest:_Cep") == "U", "", Transform(oDestino:_EnderDest:_Cep:Text, "@r 99999-999")), ;
				If(Type("oIdent:_dhEmi") == "U", "", oIdent:_dhEmi:Text), ;
					oDestino:_EnderDest:_XMun:Text, ;
					If(Type("oDestino:_EnderDest:_fone") == "U", "", oDestino:_EnderDest:_fone:Text), ;
						oDestino:_EnderDest:_UF:Text, ;
						If(Type("oDestino:_IE") == "U", "", oDestino:_IE:Text), ;
							"";
							}

						Self:oPrinter:Box(975, 000, 1300, 1200)  // Novo box com início abaixo do box anterior

						cAux := oDestino:_XNome:TEXT
						cAux := SubStr(cAux, 1, 40)

						Self:oPrinter:Say(1050,040, cAux,Self:oFont14N:oFont)

						cAux := aDest[01] + " - " + aDest[02] + ", " + aDest[05] + " - " + aDest[07] + ", CEP: " + aDest[03]
						aLinesEnd := WrapText( cAux, 54)

						For nI := 1 To Min(Len(aLinesEnd), 3)
							Self:oPrinter:Say(nLinhaY, 060, aLinesEnd[nI], Self:oFont14N:oFont)
							nLinhaY += 40
						Next

						Do Case
						Case Type("oDestino:_CNPJ") == "O"
							cCnpj := TransForm(oDestino:_CNPJ:TEXT,"@!R NN.NNN.NNN/NNNN-99")
						Case Type("oDestino:_CPF") == "O"
							cCnpj := TransForm(oDestino:_CPF:TEXT,"@r 999.999.999-99")
						EndCase

						Self:oPrinter:Say(1230, 040, "CNPJ/CPF: " + cCnpj, Self:oFont14N:oFont)
						Self:oPrinter:Say(1270, 040, "IE: " + aDest[08], Self:oFont14N:oFont)
						Return Self

Method SetAssinante(oAssinante, oFatura) CLASS PrtDanfeCom
	Local nFontSize	:= 0
	Local cTexto    := ""
	Local cDataIni  := ""
	Local cDataFim  := ""

	Default oAssinante  := Nil
	Default oFatura     := Nil

	Self:SetTotal(oTotal)

	Self:oPrinter:Box(280, 1210, 335, 2450)

	If Type("oFatura:_CompetFat") <> "U"
		cTexto := oFatura:_CompetFat:TEXT
	EndIf

	Self:oPrinter:Say(320,1250, "REFERÊNCIA: " + cTexto,Self:oFont14N:oFont)

	Self:oPrinter:Box(345, 1210, 400, 2450)

	If Type("oFatura:_dVencFat") <> "U"
		cTexto := ConvDate(oFatura:_dVencFat:TEXT)
	EndIf

	Self:oPrinter:Say(385,1250, "VENCIMENTO: " + cTexto,Self:oFont14N:oFont)

	Self:oPrinter:Box(410, 1210, 465, 2450)
	Self:oPrinter:Say(450,1250, "TOTAL A PAGAR: R$ "+AllTrim(Transform(Self:aTotais[15],"@e 9,999,999,999,999.99")),Self:oFont14N:oFont)

	Self:oPrinter:Box(475, 1210, 530, 2450)

	If Type("oAssinante:_iCodAssinante") <> "U"
		cTexto := oAssinante:_iCodAssinante:TEXT
	EndIf

	Self:oPrinter:Say(515, 1250, "CÓDIGO DO CLIENTE: " + cTexto,Self:oFont14N:oFont)

	Self:oPrinter:Box(540, 1210, 600, 2450)

	If Type("oFatura:_dPerUsoIni") <> "U" .And. Type("oFatura:_dPerUsoFim") <> "U"
		cDataIni := ConvDate(oFatura:_dPerUsoIni:TEXT)
		cDataFim := ConvDate(oFatura:_dPerUsoFim:TEXT)
	EndIf

	Self:oPrinter:Say(580, 1250, "PERÍODO INICIAL: " + AllTrim(cDataIni) + " / " + "PERIODO FINAL: " + AllTrim(cDataFim),Self:oFont14N:oFont)

	Self:oPrinter:Box(610, 1210, 670, 2450)

	If Type("oFatura:_codDebAuto") <> "U"
		cTexto := oFatura:_codDebAuto:TEXT
	EndIf

	Self:oPrinter:Say(650, 1250, "Nº IDENTI. DÉBITO AUTOMÁTICO: " + cTexto,Self:oFont14N:oFont)

	Self:oPrinter:Box(685,1210,835,2450)
	nFontSize := 32
	Self:oPrinter:Code128C(810,1250,SubStr(oNF:_INFNFCOM:_ID:Text,4), nFontSize )

	// box do pix
	Self:oPrinter:Box(845,1210,1300,2450)
	Self:oPrinter:Say(885, 1250, "QRCODE PIX: ",Self:oFont14N:oFont)
	If Type('oFatura:_gPIX') <> 'U' .And. !Empty(oFatura:_gPIX:_urlQRCodePIX:TEXT)
		Self:oPrinter:QRCode(1240,1650, oFatura:_gPIX:_urlQRCodePIX:TEXT, 90)
	Else
		Self:oPrinter:Say(960,1250,"NÃO HÁ DADOS A SEREM IMPRESSOS.",Self:oFont12N:oFont)
	EndIf

Return Self

Method SetContrib(oDestino, oIdent) CLASS PrtDanfeCom
    Default oDestino := Nil
    Default oIdent   := Nil

    Self:oPrinter:Box(1310, 000, 1430, 2450) // Caixa para resumo
    Self:oPrinter:Say(1360, 900, "ÁREA CONTRIBUINTE: ",Self:oFont14N:oFont)

Return Self

Method SetPrint(oDestino, oIdent) CLASS PrtDanfeCom
	Local nItemInicial      := 1
	Local nFolha            := 0
	Local nTotalItens       := Len(oDet)
	local nFolhas           := Self:CalculateTotalFolhas(Len(oDet))

	Default oDestino    := Nil
	Default oIdent      := Nil

	While nItemInicial <= nTotalItens
		nFolha++

		Self:SetHeader(oEmitente)
		Self:SetNFCom(oIdent, oNF, nFolha, nFolhas)
		Self:SetDest(oDestino, oIdent)
		Self:SetChvAcesso(oNF)
		Self:SetAssinante(oAssinante, oFatura)
		Self:SetContrib(oDestino, oIdent)

		nItemInicial := self:SetItens(nItemInicial, nTotalItens) + 1

		Self:SetAnatel()
		Self:SetInfCPL(oIdent, oNF, 2300)
		Self:SetMarca()
		Self:oPrinter:EndPage()
	EndDo

Return Self

Method ItemBox(nPosItem, nPosUni, nPosQuant, nPosUnit, nPosTotal, nPosBcIcm, nPosICMS, nPosAliq, nPosPis) CLASS PrtDanfeCom

	Default nPosItem := 0
	Default nPosUni  := 0
	Default nPosQuant:= 0
	Default nPosUnit := 0
	Default nPosTotal:= 0
	Default nPosBcIcm:= 0
	Default nPosICMS := 0
	Default nPosAliq := 0
	Default nPosPis  := 0

	nTamVert     := 2120
    nPosVertIni  := 1435
	Self:nCor   := RGB(255, 0, 0)

    nPosHorIni      := 0
    nEspacamento    := 700
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni, nPosHorIni, nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni+10,"ITEM DA FATURA",Self:oFont10N:oFont)
    nPosItem := nPosHorIni+10

    nPosHorIni      := nLimiteBox
    nEspacamento    := 150
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni, nPosHorIni, nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni+10,"UN",Self:oFont10N:oFont)
    nPosUni := nPosHorIni+10

    nPosHorIni      := nLimiteBox
    nEspacamento    := 200
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni, nPosHorIni, nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni+10,"QUANT",Self:oFont10N:oFont)
    nPosQuant := nPosHorIni+10
    
    nPosHorIni      := nLimiteBox
    nEspacamento    := 300
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni,nPosHorIni,nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni+10,"PREÇO UNIT (R$)",Self:oFont10N:oFont)
    nPosUnit := nPosHorIni+10

    nPosHorIni      := nLimiteBox
    nEspacamento    := 300
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni,nPosHorIni-10,nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni,"VALOR TOTAL (R$)",Self:oFont10N:oFont)
    nPosTotal := nPosHorIni

    nPosHorIni      := nLimiteBox
    nEspacamento    := 250
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni,nPosHorIni,nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni+10,"PIS/COFINS (R$)",Self:oFont10N:oFont)
    nPosPis := nPosHorIni+10

    nPosHorIni      := nLimiteBox
    nEspacamento    := 200
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni,nPosHorIni,nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni+10,"BC.ICMS (R$)",Self:oFont10N:oFont)
    nPosBcIcm := nPosHorIni+10

    nPosHorIni      := nLimiteBox
    nEspacamento    := 80
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni,nPosHorIni-10,nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni,"ALIQ",Self:oFont10N:oFont)
    nPosAliq := nPosHorIni

    nPosHorIni      := nLimiteBox
    nEspacamento    := 270
    nLimiteBox      := nPosHorIni+nEspacamento
    Self:oPrinter:Box(nPosVertIni,nPosHorIni-5,nTamVert, nLimiteBox)
    Self:oPrinter:Say(1480,nPosHorIni,"VALOR ICMS (R$)",Self:oFont10N:oFont)
    nPosICMS := nPosHorIni

Return Self

Method impIt(aItem, nNroLinhatem, nPosItem, nPosUni, nPosQuant, nPosUnit, nPosTotal, nPosBcIcm, nPosICMS, nPosAliq, nPosPis, aTributos) CLASS PrtDanfeCom
	local cProd := allTrim(aItem:_PROD:_XPROD:TEXT)

	Default aItem        := {}
	Default nNroLinhatem := 0
	Default nPosItem     := 0
	Default nPosUni      := 0
	Default nPosQuant    := 0
	Default nPosUnit     := 0
	Default nPosTotal    := 0
	Default nPosBcIcm    := 0
	Default nPosICMS     := 0
	Default nPosAliq     := 0
	Default nPosPis      := 0
	Default aTributos    := {}

	Self:oPrinter:Say(nNroLinhatem+20,nPosItem,SubStr(cProd, 1, MaxCod(cProd, 500)),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosUni,getUnMed(AllTrim(aItem:_PROD:_UMED:TEXT)),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosQuant,AllTrim(Transform(Val(aItem:_PROD:_qFaturada:TEXT),"@e 99,999,999,999.9999")),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosUnit,AllTrim(Transform(Val(aItem:_PROD:_vItem:TEXT),"@e 9,999,999,999,999.99")),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosTotal,AllTrim(Transform(Val(aItem:_PROD:_vProd:TEXT),"@e 9,999,999,999,999.99")),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosBcIcm,Alltrim(Transform(aTributos[1][1], "@e 9,999,999,999,999.99")),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosICMS,Alltrim(Transform(aTributos[1][2], "@e 9,999,999,999,999.99")),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosAliq,Alltrim(Transform(aTributos[1][3], "@e 999.99")),Self:oFont10:oFont)
	Self:oPrinter:Say(nNroLinhatem+20,nPosPis,AllTrim(Transform(Val(aItem:_PROD:_qFaturada:TEXT),"@e 99,999,999,999.9999")),Self:oFont10:oFont)
return

Method ProcessItems(oDet, oNF) CLASS PrtDanfeCom
	Local nY            := 0
	Local nLenSit       := 0
	Local aTributos     := {}
	local aSitTrib      := {"00","20","40","51","90"}

	Default oDet := {}
	Default oNF  := Nil

	nBaseICM    := 0
	nValICM     := 0
	nPICM       := 0
	nPis        := 0
	nCof        := 0
	oImposto    := oDet

	If Type("oImposto:_Imposto") <> "U"
		nLenSit := Len(aSitTrib)
		For nY := 1 To nLenSit
			Self:ProcessImp(oImposto, aSitTrib[nY], @nBaseICM, @nValICM, @nPICM, @nPis, @nCof)
		Next
	EndIf

	aAdd(aTributos, {nBaseICM, nValICM, nPICM, nPis + nCof})

Return aTributos

Method ProcessImp(oImposto, cTaxCode, nBaseICM, nValICM, nPICM, nPis, nCof) CLASS PrtDanfeCom
	Default oImposto := {}
	Default cTaxCode := ""
	Default nBaseICM := 0
	Default nValICM  := 0
	Default nPICM    := 0
	Default nPis     := 0
	Default nCof     := 0

	If Type("oImposto:_Imposto:_ICMS"+cTaxCode) <> "U"
		If Type("oImposto:_Imposto:_ICMS"+cTaxCode+":_VBC")<>"U"
			nBaseICM := Val(&("oImposto:_Imposto:_ICMS"+cTaxCode+":_VBC:TEXT"))
		EndIf

		If Type("oImposto:_Imposto:_ICMS"+cTaxCode+":_vICMS")<>"U"
			nValICM  := Val(&("oImposto:_Imposto:_ICMS"+cTaxCode+":_vICMS:TEXT"))
		EndIf

		If Type("oImposto:_Imposto:_ICMS"+cTaxCode+":_PICMS")<>"U"
			nPICM    := Val(&("oImposto:_Imposto:_ICMS"+cTaxCode+":_PICMS:TEXT"))
		EndIf
	EndIf

	If Type("oImposto:_Imposto:_PIS") <> "U"
		nPis    := Val(&("oImposto:_Imposto:_PIS:_vPIS:TEXT"))
	EndIf

	If Type("oImposto:_Imposto:_COFINS") <> "U"
		nCof    := Val(&("oImposto:_Imposto:_COFINS:_vCOFINS:TEXT"))
	EndIf
Return

Method SetInfCPL(oIdent, oNF, nLinIni, lOnlyMsg) CLASS PrtDanfeCom
    Local nX            := 1
    Local nLin          := 0
    Local aResFisco     := {}
    Local aMsgRet       := {}
	Local cMsg          := ""
	Local nInicioL	    := 1
	Local nFimL 	    := 68
	Local nLinhasQtd	:= 0

    Default oIdent := Nil
    Default oNF    := Nil
    Default nLinIni := 2300
    Default lOnlyMsg := .F.

    Self:oPrinter:Box(nLinIni,000,2980,1550)
    Self:oPrinter:Say(nLinIni + 20,020,"INFORMAÇÕES COMPLEMENTARES",Self:oFont10N:oFont)

    Self:oPrinter:Box(nLinIni,1550,2980,2452)
    Self:oPrinter:Say(nLinIni + 20,1570,"RESERVADO AO FISCO",Self:oFont10N:oFont)

	//"INFORMAÇÕES COMPLEMENTARES"
    nLin            := nLinIni + 50
	If !Empty(Self:aMessages) .And. Len(Self:aMessages) > 0
		nLinhasQtd := Ceiling(Len(Self:aMessages[1]) / nFimL) //Calcula a quantidade de linhas necessárias para impressao
		While nX <= nLinhasQtd .And. nX <= 32
			cMsg := SubStr(Self:aMessages[1],nInicioL,nFimL)
			Self:oPrinter:Say(nLin,020,cMsg,Self:oFont10:oFont)
			nLin := nLin + 20
			nInicioL += nFimL
			nX ++
		EndDo
	EndIf
	//"RESERVADO AO FISCO"
    If !Empty(Self:cRetMsg)
		aMsgRet := StrTokArr( Self:cRetMsg, "|")
		aEval( aMsgRet, {|x| aadd( aResFisco, alltrim(x) ) } )

		nInicioL	    := 1
		nFimL 	   		:= 38
		nLinhasQtd 		:= Ceiling(Len(aResFisco[1]) / nFimL) //Calcula a quantidade de linhas necessárias para impressao
		nX 				:= 1
		nLin            := nLinIni + 50

		While nX <= nLinhasQtd .And. nX <= 32
			cMsg := SubStr(aResFisco[1],nInicioL,nFimL)
			Self:oPrinter:Say(nLin,1570,cMsg,Self:oFont10:oFont)
			nLin := nLin + 20
			nInicioL += nFimL
			nX ++
		EndDo
    endif

Return

Method SetItens(nItemInicial,nTotalItens) CLASS PrtDanfeCom
	local nPosItem          := 0
	local nPosUni           := 0
	local nPosQuant         := 0
	local nPosUnit          := 0
	local nPosTotal         := 0
	local nPosBcIcm         := 0
	local nPosICMS          := 0
	local nPosAliq          := 0
	local nPosPis           := 0
	local nI                := 0
	Local nItemFinal        := 0
	local nNroLinhatem      := 1500 //Posicionamento vertical
	local nItensPorPagina   := Self:nTotItsPag

	Self:ItemBox(@nPosItem, @nPosUni, @nPosQuant, @nPosUnit, @nPosTotal, @nPosBcIcm, @nPosICMS, @nPosAliq, @nPosPis)

	// // Calcula o limite máximo de itens para a página atual
	nItemFinal := Min(nItemInicial + nItensPorPagina - 1, nTotalItens)

	// // Itera pelos itens na página atual
	For nI := nItemInicial To nItemFinal
		Self:impIt(oDet[nI], nNroLinhatem, nPosItem, nPosUni, nPosQuant, nPosUnit, nPosTotal, nPosBcIcm, nPosICMS, nPosAliq, nPosPis, Self:ProcessItems(oDet[nI], oNF)) //Imprime linha de item
		nNroLinhatem += 25
	Next

Return nItemFinal

Method SetAnatel() CLASS PrtDanfeCom

    Self:oPrinter:Box(3000, 000, 3210, 2452) // Caixa para resumo
    Self:oPrinter:Say(3050,700, "ÁREA CONTRIBUINTE E DETERMINAÇÕES DA ANATEL: ",Self:oFont14N:oFont)
    
Return

Method Finalize() CLASS PrtDanfeCom
	fwFreeObj(Self:oPrinter)
	Self:oPrinter := Nil
Return

Method AddFormattedMessage(cMessage) CLASS PrtDanfeCom
	Local cAux := cMessage

	IF !Empty(cAux)
		aAdd(Self:aMessages, cAux)
	Endif

Return

Method AddComplementaryMessages(oIdent, oNF) CLASS PrtDanfeCom
	Local cInfComp  := ""
	Local aMsgComp := {}
	Local nX		:= 0

	Default oIdent := Nil
	Default oNF    := Nil

	Self:aMessages := {}

	// If !Empty(Self:cAutoriza) .And. oIdent:_tpEmis:TEXT == "2"
	// 	Self:AddFormattedMessage("DANFECOM EMITIDA EM CONTINGÊNCIA")
	// endIf

	If Type("oNF:_INFNFCOM:_INFADIC:_INFCPL") <> "U"

		If ValType(oNF:_INFNFCOM:_INFADIC:_INFCPL) == "A"
			aMsgComp := oNF:_INFNFCOM:_INFADIC:_INFCPL
		Else
			aMsgComp := {oNF:_INFNFCOM:_INFADIC:_INFCPL}
		EndIf

		For nX := 1 To Len(aMsgComp)
			cInfComp    := aMsgComp[nX]:Text
			cInfComp    := STRTRAN(cInfComp, ">", "&gt;")
			cInfComp    := STRTRAN(cInfComp, "<", "&lt;")
			cInfComp    := stripTags(cInfComp,.T.)
			cInfComp    := STRTRAN(cInfComp, "&gt;", ">")
			cInfComp    := STRTRAN(cInfComp, "&lt;", "<")

			Self:AddFormattedMessage(cInfComp)
		Next

	EndIf
Return

Method CalculateTotalFolhas(nTotalItens) CLASS PrtDanfeCom
	Local nItensPorPagina       := Self:nTotItsPag
	Local nMsgPorPagina         := self:MAXMSG
	Local nMsgRestantes         := Len(Self:aMessages)
	Local nTotItfolhas          := 1
	Local nTotMsgFolhas         := 0

	Default nTotalItens := 0

	// Contagem de folhas para os itens
	if nTotalItens > nItensPorPagina
		nTotItfolhas := Int(nTotalItens / nItensPorPagina)
		if mod(nTotalItens, nItensPorPagina) > 0
			nTotItfolhas++
		endif
	endIf

	// Contagem de folhas para as mensagens adicionais
	nMsgRestantes := nMsgRestantes - (nMsgPorPagina * nTotItfolhas) //tira as linhas que ja serao impressas nas folhas dos itens
	if nMsgRestantes > 0
		nTotMsgFolhas :=  Int( nMsgRestantes / self:MAXONLYMSG) //vejo o quanto falta para imprimir
		if mod(nMsgRestantes, self:MAXONLYMSG) > 0 //se sobrou somo +1
			nTotMsgFolhas++
		endIf
	endIf

Return nTotItfolhas + nTotMsgFolhas

Method SetMarca() CLASS PrtDanfeCom
	If AllTrim(cAmb) == "2"
		Self:oPrinter:Say(1200,350,"DANFECOM EMITIDO EM AMBIENTE DE HOMOLOGAÇÃO - SEM VALOR FISCAL",Self:oFont18N:oFont,2000,Self:nCor,030)
	EndIf
Return Self

Method GetXML(aNFe,cErro) CLASS PrtDanfeCom
	Local cRetorno   := ""
	Local cProtocolo := ""
	Local aRetorno   := {}
	Local cDtHrRec   := ""
	Local cDtHrRec1	 := ""
	Local nDtHrRec1  := 0
	Local cAviso	:= ""
	local cXmlDoc	:= ""
	Local cXmlUni	:= ""
    Local dDataAt   := CToD("  /  /   ")
	Local cXmlFisco	:= ""

	Private oDHRecbto
	Private oXmlProt
	Private oXmlFisco

	Default aNFe	:= {}
	Default	cErro	:=	""


	If Len(aNFe) > 0
		cRetorno := aNFe[01]

		if ( !empty(aNFe[02]) )
			cXmlDoc := aNFe[02]
			oXmlProt	:= XmlParser(cXmlDoc,"_",@cErro,@cAviso)
			If ( oXmlProt <> NIL )
				If Type("oXmlProt:_PROTNFCOM:_INFPROT:_NPROT") <> "U"
					cProtocolo := oXmlProt:_PROTNFCOM:_INFPROT:_NPROT:TEXT
				EndIf
			EndIf
			cXmlUni 	:= aNFe[01]
			oXmlFisco	:= XmlParser(cXmlUni,"_",@cErro,@cAviso)
			If Type("oXmlFisco:_NFCOM:_INFNFCOM:_INFADIC:_INFADFISCO:TEXT") <> "U" .And. !Empty(oXmlFisco:_NFCOM:_INFNFCOM:_INFADIC:_INFADFISCO:TEXT)
				cXmlFisco	:= oXmlFisco:_NFCOM:_INFNFCOM:_INFADIC:_INFADFISCO:TEXT
			EndIf
		endif

		//Tratamento para gravar a hora da transmissao da NFe
		If !Empty(cProtocolo)
			cDtHrRec := SubStr(aNFe[02], At("<dhRecbto>", aNFe[02]) + 10)
			cDtHrRec := SubStr(cDtHrRec, 1, At("</dhRecbto>", cDtHrRec) - 1)

			nDtHrRec1   := RAT("T",cDtHrRec)
			dDataAt     := Substr(cDtHrRec,1,10)
			dDataAt	    := SubStr(dDataAt,9,2)+"/"+Substr(dDataAt,6,2)+"/"+Substr(dDataAt,1,4)

			If nDtHrRec1 <> 0
				cDtHrRec1 := SubStr(cDtHrRec,nDtHrRec1+1,8)
			EndIf

		EndIf

		Aadd(aRetorno,cProtocolo)
		Aadd(aRetorno,cRetorno)
		Aadd(aRetorno,"")
		Aadd(aRetorno,"")
		Aadd(aRetorno,cDtHrRec1)
		Aadd(aRetorno,"")
		Aadd(aRetorno,dDataAt)
		Aadd(aRetorno,cXmlFisco)

	EndIf

Return(aRetorno)

Static Function ConvDate(cData)
	Local dData

	Default cData := ""

	cData  := StrTran(cData,"-","")
	dData  := Stod(cData)

Return PadR(StrZero(Day(dData),2)+ "/" + StrZero(Month(dData),2)+ "/" + StrZero(Year(dData),4),15)

static function getUnMed(cUmed)
	local cUnidade := "-"

	Do Case
	Case cUmed == "1"
		cUnidade := "Minuto"
	Case cUmed == "2"
		cUnidade := "MB"
	Case cUmed == "3"
		cUnidade := "GB"
	Case cUmed == "4"
		cUnidade := "UN"
	EndCase

return cUnidade

User Function PrtNfcom(	cIdEnt, cAmb )

	Local lRet		:= .T.
	Local cProg		:= ""

	If existBlock("DANFCOMPrc")
		cProg := "U_DANFCOMPrc"
	Else
		cProg := "DANFCOMPrc"
	EndIf

    RPTStatus( {|lEnd| &cProg.(@lEnd, cIDEnt, cAmb)}, STR0015 )

Return lRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  DANFCOMPrc Autor ³ Antonio Marfil          ³ Data ³18.06.2025³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Rdmake de exemplo para impressão da DANFE no formato Retrato³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpO1: Objeto grafico de impressao                    (OPC) ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³   DATA   ³ Programador   ³Manutencao efetuada                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³               ³                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

User Function DANFCOMPrc( lEnd, cIdEnt, cAmbiente )

    Local aAreaSF3   := {}
    Local aNotas     := {}
    Local aXML       := {}
    Local cAliasSF3  := "SF3"
    Local cIndex	 := ""
    Local lQuery     := .F.
    Local lImpDir	:= GetNewPar("MV_IMPDIR",.F.)
	
    Local cSerie 	:= ""
    Local cSerId 	:= ""
    
    local lPossuiNota	:= .F.
	Local cPathPDF    := SuperGetMV('MV_RELT',,"\SPOOL\")
	Local aPergs	:= {}
	Local cdeNfcom 	:= Space(TamSx3("F3_NFISCAL")[1])
	Local cateNfcom := Space(TamSx3("F3_NFISCAL")[1])
	Local cdaSerie 	:= Space(TamSx3("F3_SERIE")[1])
	Local ctpOP		:= "1"
	Local dDataDe	:= FirstDate(Date())
	Local dDataAte	:= LastDate(Date())

	Default cIdEnt	    := ""
	Default lBuffer	    := .T.
	Default cFilePrint  := "danfecom_"+Dtos(MSDate())+StrTran(Time(),":","")
	Default nDevice		:= IMP_PDF
	Default cAmbiente	:= "2"
	Default nVias		:= 1
    Default lEnd		:= .F.
    Default lIsLoja		:= .F.
    Default nTipo		:= 0

	oDanfcom    := PrtDanfeCom():New(cPathPDF, cFilePrint, nDevice, lBuffer)

	If oDanfcom:oPrinter:NMODALRESULT == 1 // Se o usuário cancelar a impressão
		aAdd(aPergs, {1, STR0001			, cdeNfcom	,  ""							, ".T.", "", ".T.", 80,  .F.})
		aAdd(aPergs, {1, STR0002			, cateNfcom	,  ""							, ".T.", "", ".T.", 80,  .T.})
		aAdd(aPergs, {1, STR0003			, cdaSerie	,  ""							, ".T.", "", ".T.", 80,  .T.})
		aAdd(aPergs, {2, STR0004 			, ctpOP		,  {STR0005,STR0006}, 80   , ".T.", .T.})
		aAdd(aPergs, {1, STR0007			, dDataDe	,  ""							, ".T.", "", ".T.", 80,  .T.})
		aAdd(aPergs, {1, STR0008			, dDataAte	,  ""							, ".T.", "", ".T.", 80,  .T.})

		ParamBox( aPergs, STR0009 )
		
		MV_PAR01 := AllTrim(MV_PAR01)
		MV_PAR02 := AllTrim(MV_PAR02)
		MV_PAR04 := Val(MV_PAR04)

		If !lImpDir .or. MV_PAR04 == 0 // Caso impressão de DANFCOM seja realizada via AutoDistMail 
			dbSelectArea("SF3")
			dbSetOrder(5)
			cSerie := Padr(MV_PAR03,TamSx3("F3_SERIE")[1])

			lQuery    := .T.

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Campos que serao adicionados a query somente se existirem na base³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			
			
			
			
			

			If oQry == nil
				cQry := "SELECT F3_FILIAL,F3_ENTRADA,F3_NFELETR,F3_CFO,F3_FORMUL,F3_NFISCAL,F3_SERIE,F3_CLIEFOR,F3_LOJA,F3_ESPECIE,F3_DTCANC "
				cQry += "FROM " + RetSqlName('SF3') + " "
				cQry += "WHERE F3_FILIAL = ? "
				cQry += "AND F3_SERIE = ? "
				cQry += "AND F3_NFISCAL >= ? " 
				cQry += "AND F3_NFISCAL <= ? "
				
				IF MV_PAR04 == 1 // Saida
					cQry += "AND SubString(F3_CFO,1,1) >= '5' "
				ElseIf MV_PAR04 == 2 // Entrada
					cQry += "AND SubString(F3_CFO,1,1) < '5' AND F3_FORMUL='S' "
				EndIf

				cQry += "AND F3_SERIE = ? "
				cQry += "AND F3_ESPECIE IN ('SPED','NFCE','NFCOM') "

				cQry += "AND F3_EMISSAO >= ? "
				cQry += "AND F3_EMISSAO <= ? "

				cQry += "AND F3_DTCANC = ? "
				cQry += "ORDER BY F3_NFISCAL "
				cQry := ChangeQuery(cQry)
				oQry := FWExecStatement():New(cQry)
			EndIf
			
			oQry:SetString(1, xFilial("SF3"))
			oQry:SetString(2, MV_PAR03)
			oQry:SetString(3, MV_PAR01)
			oQry:SetString(4, MV_PAR02)

			oQry:SetString(5, cSerie)
			oQry:SetString(6, SubStr(DTOS(MV_PAR05),1,4) + SubStr(DTOS(MV_PAR05),5,2) + SubStr(DTOS(MV_PAR05),7,2))
			oQry:SetString(7, SubStr(DTOS(MV_PAR06),1,4) + SubStr(DTOS(MV_PAR06),5,2) + SubStr(DTOS(MV_PAR06),7,2))
			oQry:SetString(8, Space(8))

			oQry:GetFixQuery()
			cAliasSF3 := oQry:OpenAlias()
			
			
			
			
			cSerId := (cAliasSF3)->F3_SERIE
			

			While !Eof() .And. xFilial("SF3") == (cAliasSF3)->F3_FILIAL .And.;
				cSerId == MV_PAR03 .And.;
				(cAliasSF3)->F3_NFISCAL >= MV_PAR01 .And.;
				(cAliasSF3)->F3_NFISCAL <= MV_PAR02

				dbSelectArea(cAliasSF3)

				If  Empty((cAliasSF3)->F3_DTCANC)

					If (SubStr((cAliasSF3)->F3_CFO,1,1)>="5" .Or. (cAliasSF3)->F3_FORMUL=="S") .And. aScan(aNotas,{|x| x[4]+x[5]+x[6]+x[7]==(cAliasSF3)->F3_SERIE+(cAliasSF3)->F3_NFISCAL+(cAliasSF3)->F3_CLIEFOR+(cAliasSF3)->F3_LOJA})==0

						aadd(aNotas,{})
						aadd(Atail(aNotas),.F.)

						If (cAliasSF3)->F3_CFO < "5"
							aadd(Atail(aNotas),"E")
						Else
							aadd(Atail(aNotas),"S")
						Endif

						aadd(Atail(aNotas),(cAliasSF3)->F3_ENTRADA)
						aadd(Atail(aNotas),(cAliasSF3)->F3_SERIE)
						aadd(Atail(aNotas),(cAliasSF3)->F3_NFISCAL)
						aadd(Atail(aNotas),(cAliasSF3)->F3_CLIEFOR)
						aadd(Atail(aNotas),(cAliasSF3)->F3_LOJA)

					EndIf
				EndIf

				dbSelectArea(cAliasSF3)
				dbSkip()

				
				
				
				cSerId := (cAliasSF3)->F3_SERIE
				

				If lEnd
					Exit
				EndIf
				If (cAliasSF3)->(Eof())
					aAreaSF3 := (cAliasSF3)->(GetArea())
					aXml := GetXMLNF(cIdEnt,aNotas,if( valtype(oDanfcom) == "O", oDanfcom:oPrinter:lInJob, nil ) )
					
					if Len(aNotas) > 0
						TSSDANFECOM(aXML,oDanfcom, cIdEnt, nVias, cAmbiente)
					EndIF

					aNotas := {}
					aXml   := {}

					lPossuiNota	:= .T.				   
					RestArea(aAreaSF3)
					DelClassIntF()
				EndIf
			EndDo

			If !lPossuiNota
				Aviso(STR0010,STR0011,{STR0012},3)
			EndIf

		EndIf
		if lQuery
			(cAliasSF3)->(dbCloseArea())
			oQry:Destroy()
			FreeObj(oQry)     
			oQry := nil
		else
			DBClearFilter()
			Ferase(cIndex+OrdBagExt())
		endif
	EndIf
	fwFreeObj(oDanfcom)
	oDanfcom := Nil
Return .T.

//-----------------------------------------------------------------------
/*/{Protheus.doc} executeRetorna
Executa o retorna de notas

@author Antonio Marfil
@since 18/06/2025
@version 1.0

@param  cID ID da nota que sera retornado

@return aRetorno   Array com os dados da nota
/*/
//-----------------------------------------------------------------------
static function executeRetorna( aNfe, cIdEnt, lUsacolab, lJob)

    Local aRetorno		:= {}
    Local aIdNfe		:= {}
    Local aWsErro		:= {}

    Local cAviso		:= ""
    Local cCodRetNFE	:= ""
    Local cDHRecbto		:= ""
    Local cDtHrRec		:= ""
    Local cDtHrRec1		:= ""
    Local cErro			:= ""
    Local cModTrans		:= ""
    Local cProtDPEC		:= ""
    Local cProtocolo	:= ""
    Local cMsgNFE		:= ""
    local cMsgRet		:= ""
    Local cRetDPEC		:= ""
    Local cRetorno		:= ""
    Local cURL			:= PadR(GetNewPar("MV_SPEDURL","http://localhost:8080/sped"),250)
    Local cCodStat		:= ""
    Local dDtRecib		:= CToD("")
    Local nDtHrRec1		:= 0
    Local nX			:= 0
    Local nY			:= 0
    Local nZ			:= 1
    Local nPos			:= 0

    Local oWS

    Private oDHRecbto
    Private oNFeRet
    Private oDoc

    default lUsacolab	:= .F.
    default lJob		:= .F.

    aAdd(aIdNfe,aNfe)

	oWS:= WSNFeSBRA():New()
	oWS:cUSERTOKEN        := "TOTVS"
	oWS:cID_ENT           := cIdEnt
	oWS:nDIASPARAEXCLUSAO := 0
	oWS:_URL 			  := AllTrim(cURL)+"/NFeSBRA.apw"
	oWS:oWSNFEID          := NFESBRA_NFES2():New()
	oWS:oWSNFEID:oWSNotas := NFESBRA_ARRAYOFNFESID2():New()

	aadd(aRetorno,{"","",aIdNfe[nZ][4]+aIdNfe[nZ][5]/*//*,"","","",CToD(""),"","","",""*/})

	aadd(oWS:oWSNFEID:oWSNotas:oWSNFESID2,NFESBRA_NFESID2():New())
	Atail(oWS:oWSNFEID:oWSNotas:oWSNFESID2):cID := aIdNfe[nZ][4]+aIdNfe[nZ][5]

	If oWS:RETORNANOTAS()

		If Len(oWs:oWSRETORNANOTASRESULT:OWSNOTAS:OWSNFES3) > 0
			For nX := 1 To Len(oWs:oWSRETORNANOTASRESULT:OWSNOTAS:OWSNFES3)
				cRetorno        := oWs:oWSRETORNANOTASRESULT:OWSNOTAS:OWSNFES3[nX]:oWSNFE:CXML
				cProtocolo      := oWs:oWSRETORNANOTASRESULT:OWSNOTAS:OWSNFES3[nX]:oWSNFE:CPROTOCOLO
				cDHRecbto  		:= oWs:oWSRETORNANOTASRESULT:OWSNOTAS:OWSNFES3[nX]:oWSNFE:CXMLPROT
				oNFeRet			:= XmlParser(cRetorno,"_",@cAviso,@cErro)
				cModTrans		:= If(!Empty(oNFeRet:_NFCOM:_INFNFCOM:_IDE:_TPEMIS:TEXT),oNFeRet:_NFCOM:_INFNFCOM:_IDE:_TPEMIS:TEXT,"1")
				cCodStat		:= ""
				
				//Tratamento para gravar a hora da transmissao da NFe 
				If !Empty(cProtocolo)
					oDHRecbto		:= XmlParser(cDHRecbto,"","","")

					If ValType("oDHRecbto:_PROTNFCOM:_INFPROT:_DHRECBTO:TEXT") <> "U"
						cDtHrRec := oDHRecbto:_PROTNFCOM:_INFPROT:_DHRECBTO:TEXT
					EndIf

					If ValType("oDHRecbto:_PROTNFCOM:_INFPROT:_XMOTIVO:TEXT") <> "U"
						cMsgRet := oDHRecbto:_PROTNFCOM:_INFPROT:_XMOTIVO:TEXT
					EndIf

					If ValType("oDHRecbto:_PROTNFCOM:_INFPROT:_CSTAT:TEXT") <> "U"
						cCodStat := oDHRecbto:_PROTNFCOM:_INFPROT:_CSTAT:TEXT
					EndIf

					nDtHrRec1		:= RAT("T",cDtHrRec)
					
					If nDtHrRec1 <> 0
						cDtHrRec1   :=	SubStr(cDtHrRec,nDtHrRec1+1)
						dDtRecib	:=	SToD(StrTran(SubStr(cDtHrRec,1,AT("T",cDtHrRec)-1),"-",""))
					EndIf
				EndIf

				nY := aScan(aIdNfe,{|x| x[4] + x[5] == SubStr(oWs:oWSRETORNANOTASRESULT:OWSNOTAS:OWSNFES3[nX]:CID,1,LEN(aIdNfe[nZ][4]+aIdNfe[nZ][5]))})

				oWS:cIdInicial    := aIdNfe[nZ][4]+aIdNfe[nZ][5]
				oWS:cIdFinal      := aIdNfe[nZ][4]+aIdNfe[nZ][5]
				If oWS:MONITORFAIXA()
					nPos    := 0
					aWsErro := {}
					If !Empty(cProtocolo) .AND. !Empty(cCodStat)
						aWsErro := oWS:OWSMONITORFAIXARESULT:OWSMONITORNFE[1]:OWSERRO:OWSLOTENFE
						For nPos := 1 To Len(aWsErro)
							If Alltrim(aWsErro[nPos]:CCODRETNFE) == Alltrim(cCodStat)
								Exit
							Endif
						Next
					Endif
					If nPos > 0 .And. nPos <= Len(aWsErro)
						cCodRetNFE := oWS:oWsMonitorFaixaResult:OWSMONITORNFE[1]:OWSERRO:OWSLOTENFE[nPos]:CCODRETNFE
						cMsgNFE	:= oWS:oWsMonitorFaixaResult:OWSMONITORNFE[1]:OWSERRO:OWSLOTENFE[nPos]:CMSGRETNFE
					Else
						cCodRetNFE := oWS:oWsMonitorFaixaResult:OWSMONITORNFE[1]:OWSERRO:OWSLOTENFE[len(oWS:oWsMonitorFaixaResult:OWSMONITORNFE[1]:OWSERRO:OWSLOTENFE)]:CCODRETNFE
						cMsgNFE	:= oWS:oWsMonitorFaixaResult:OWSMONITORNFE[1]:OWSERRO:OWSLOTENFE[len(oWS:oWsMonitorFaixaResult:OWSMONITORNFE[1]:OWSERRO:OWSLOTENFE)]:CMSGRETNFE
					EndIf
				endif

				If nY > 0
					aRetorno[nY][1] := cRetorno
					aRetorno[nY][2] := cDHRecbto
				EndIf
				cRetDPEC := ""
				cProtDPEC:= ""
			Next nX
		EndIf
	Elseif !lJob
		Aviso("DANFCOM",IIf(Empty(GetWscError(3)),GetWscError(1),GetWscError(3)),{"OK"},3)
	EndIf
    oWS       := Nil
    oDHRecbto := Nil
    oNFeRet   := Nil

   return aRetorno[len(aRetorno)]

Static Function GetXMLNF(cIdEnt,aIdNfse, lJob)

	Local aRetorno		:= {}
	Local aDados		:= {}
	Local nZ			:= 0
	Local nCount		:= 0


	default lJob := .F.

	For nZ := 1 To len(aIdNfse)

		nCount++

		aDados := executeRetorna( aIdNfse[nZ], cIdEnt , , lJob)

		if ( nCount == 10 )
			delClassIntF()
			nCount := 0
		endif

		aAdd(aRetorno,aDados)

	Next nZ

Return(aRetorno)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DANFEIII  ºAutor  ³Microsiga           º Data ³  12/17/10   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Tratamento para o código do item                           º±±
±±º          ³                                                            º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function MaxCod(cString, nTamanho)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Tratamento para saber quantos caracteres irão caber na linha ³
//³ visto que letras ocupam mais espaço do que os números.      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	Local nMax	:= 0
	Local nY   	:= 0
	Default nTamanho := 45

	For nMax := 1 to Len(cString)
		If IsAlpha(SubStr(cString,nMax,1)) .And. SubStr(cString,nMax,1) $ "MOQW"  // Caracteres que ocupam mais espaço em pixels
			nY += 7
		Else
			nY += 5
		EndIf

		If nY > nTamanho   // é o máximo de espaço para uma coluna
			nMax--
			Exit
		EndIf
	Next

	Return nMax

//-----------------------------------------------------------------------
/*/{Protheus.doc} WrapText
Executa o retorna de notas

@author Felipe Duarte Luna
@since 13/12/2025
@version 1.0

@param  cID ID da nota que sera retornado

@return aRetorno   Array com do Endereço quebrado em linhas, quando atinge o limite de caracteres informados
/*/
//-----------------------------------------------------------------------
Static Function WrapText(cText, nLimit)
    Local aLines := {}
    Local cLinha := ""
    Local aPalavras := StrTokArr(AllTrim(cText), " ")
    Local nI

    For nI := 1 To Len(aPalavras)
        If (Len(cLinha) + Len(aPalavras[nI]) + 1) <= nLimit
            If Empty(cLinha)
                cLinha := aPalavras[nI]
            Else
                cLinha := cLinha + " " + aPalavras[nI]
            EndIf
        Else
            AAdd(aLines, cLinha)
            cLinha := aPalavras[nI]
        EndIf
    Next

    If !Empty(cLinha)
        AAdd(aLines, cLinha)
    EndIf

Return aLines
