#include 'protheus.ch'
#include 'parmtype.ch'
Static cPathImp		:=	"\xmlsefaz\"
Static cPathXMNfe	:=	cPathImp+"nfe_Emp"+cEmpAnt+"\"
Static cVersaoTSS := IIf( UsaColaboracao("4"), "", StrTran(getVersaoTSS(),".","" ))

//MELHORIAS
//XXX Ler a TAG nDUP para localizar a condição de pagamento
/*/{Protheus.doc} IXMLSEF

Modo de Importação
1) Gerar o documento de entrada
2) Gerar a pré-nota

Mode de Operação
0) Passar como parametro da rotina a importação direta, do arquivo,
sem a necessidade de localizar o arquivo XML ou fazer download.
1) Importar com a chave da nota fiscal, o sistema fará a consulta
do XML no Sefaz, porém, será necessário primeiro fazer o Manifesto do
destinatário na rotina SPEDMANIFE. POde-se configurar a rotina JobMani
no schedule do Protheus para a cada 1 hora (por exemplo) verificar
as notas emitidas contra o CNPJ do cliente, dessa forma basta o usuário
localizar a chave na rotina e fazer a manifesto, após isso fazer a importação.
2) Selecionar o arquivo XML


@author TSC679 - Charles.reitz
@since 28/04/2017
@version undefined

@return return, return_description
@example

Importar Pre-Nota, chamar a rotina dessa forma:
U_IXMLSEF(,'2','1') - Importar pre nota selecionando o arquivo
U_IXMLSEF(,'1','1') - Importar pre nota informando a chave para download


Importar Documento Entrada, chamar a rotina dessa format:
U_IXMLSEF(,'2','2') - Importar pre nota selecionando o arquivo
U_IXMLSEF(,'1','2') - Importar pre nota informando a chave para download

Usando o PE MTA103MNU
Aadd(aRotina,{ "Imp. Nf-e XML Arquivo*", "U_CALA046(,'2','2')", 0 , 2, 0, .F.})
Aadd(aRotina,{ "Imp. Nf-e XML Download*", "U_CALA046(,'1','2')", 0 , 2, 0, .F.})

Usando o PE MTA140MNU
Aadd(aRotina,{ "Imp. Nf-e Xml Arquivo*", "U_CALA046(,'2','1')", 0 , 2, 0, .F.})
Aadd(aRotina,{ "Imp. Nf-e Xml Download*", "U_CALA046(,'1','1')", 0 , 2, 0, .F.})

@see (links_or_references)
/*/
User Function IXMLSEF(cFileXML,cModImp,cOperac,cCHAVFIND)
	Local aParamBox	:=  {}
	Local cTitulo	:=	"Title"
	Local bOk 		:= {|| .T.}
	LOCAL aButtons 	:= {}
	LOCAL lCentered := .T.
	LOCAL nPosx
	Local lRet		:=	.F.
	LOCAL nPosy
	LOCAL cLoad 	:= ProcName()
	LOCAL lCanSave 	:= .F.
	Local lUserSave	:=	.F.
	Local aMVSave		:=	Array(30)
	Local nk
	Local aRetParam		:=	{}
	Local lEnvOk		:=	nil
	Local cXMLRead		:=	""
	Default cModImp		:=	"1" //via chave da nota 1) Por Chave 2) localizar arquivo 3)direto com arquivo
	Default cFileXML	:= ""
	Default cOperac		:=	"1"//1) Pre nota 2) Documento de entrada
	Default cChavFind	:=	""
	Private lMVZerosDoc	:=	SuperGetMv("IX_NFCZERO",.F.,.F.)// GetMv("IX_NFCZERO",.F.) //Define que o numero da nota fiscal vai possui zeros ou apenas numeros
	Private lMVTpFrete	:=  SuperGetMv("IX_TPFRETE",.F.,.F.) //Define se localiza o tipo de freten
	Private lMVSavMemN	:=  SuperGetMv("IX_SAVMEMN",.F.,.F.)  //Define se vai pegar a mensagem fiscal e salvar
	Private cCodPrdFre	:=	Alltrim(SuperGetMv("IX_CODPRFR",.F.,""))  //Define o codigo do produto padrao de frete
	Private cTesPRdFre	:=  Alltrim(SuperGetMv("IX_TESPRDF",.F.,""))  //Define a TES padrao para importacao do CTE
	Private lMVSegUni   :=  SuperGetMv("IX_SEGUNI",.F.,.F.) // Diego Kerstner: Verifica se utiliza segunda unidade de medida
	Private cMsgErro    := ""
	Private cEol := chr(10)
	For nk	:=	1 To Len(aMVSave)
		aMVSave[nk]	:=	&("MV_PAR"+StrZero(nk,2))
	Next

	Begin Sequence

		//	If !ValidEMp()
		//		Break
		//	EndIf


		//Caso foi informado arquivo, nao precisa localizar ou fazer download
		If !Empty(cFileXML)
			cModImp	:= "0" //direto
		EndIf

		While .T.
			If cModImp == "1"

				If Empty(cCHAVFIND)
					aParamBox	:=	{}
					aRetParam	:=	{}
					aAdd(aParamBox, {1,"Chave",CriaVar("F1_CHVNFE",.F.),,".T.",'','.T.', 100, .T.})
					If !ParamBox(aParamBox, cTitulo, @aRetParam, bOk, aButtons, lCentered, nPosx,nPosy,/*oPanel*/ , cLoad, lCanSave, lUserSave)
						Break
					EndIf
				Else
					aRetParam	:=	{cCHAVFIND}
				Endif

				//Cria as patas necessarias
				If !ExistDir(cPathImp)
					MakeDir(cPathImp)
				EndIF

				If !ExistDir(cPathXMNfe)
					MakeDir(cPathXMNfe)
				EndIF

				//If !ExistDir(cPathLogX)
				//	MakeDir(cPathLogX)
				//EndIF

				//Rotina de Download
				//MsgRun("Aguarde Manifestação","Processando",{|| lEnvOk := MontaXmlManif(cCbCpo,aMontXml,@cRetorno,cJustific)})
				dbSelectArea("C00")
				dbSetOrder(1)
				If !dbSeek(xFilial("C00")+aRetParam[1])
					MsgStop("Não foi localizado chave no manifesto do destinatário, faça a sincronização para buscar do SEFAZ (C00)","Atenção - "+ProcName())
					Break
				EndIf
				nRecNOC00	:=	C00->(RecNo())

				//Somente vai manifestar, caso estiver importada mas não manifestada
				If C00->C00_STATUS=='0' .and. alltrim(C00->C00_CODEVE)=='1' .AND. alltrim(C00->C00_SITDOC) = '1'

					//Chama rotina para efetuar a manifestação do destinatário
					//para posterior conseguir efetuar o download da nota fiscal
					cRetorno	:=	""
					cJustific	:=	""
					cCbCpo		:=	"210200" //confirmacao
					cMsgErro += "Manifesto Ini "+time() + ceol
					FWMsgRun( ,{|| lEnvOk := GerXmlManif(cCbCpo,aRetParam[1],@cRetorno,cJustific)},"Efetuando manifesto do destinatário... ")

					IF !lEnvOk
						Break
					EndIf
					cMsgErro += "Manifesto Fim "+time() + ceol
				EndIf

				C00->(dbGoTo(nRecNOC00))

				//Somente faz download quando estiver confirmada o manifesto
				If C00->C00_STATUS=='1' .and. alltrim(C00->C00_CODEVE)=='3' .AND. alltrim(C00->C00_SITDOC) = '1'
					FWMsgRun( ,{|| cFileXML	:=	U_IXMLDown(aRetParam[1],If(C00->(FieldPos("C00_ZXML"))<>0,C00->C00_ZXML,""))},"Efetuando download do XML...")
				Else
					MsgStop("Não foi possível iniciar o download do XML, efetue o monitoramento do Manifesto do Destinatário para verificar autorização do Sefaz","Atenção - "+ProcName())
					Loop
				EndIf

				C00->(dbGoTo(nRecNOC00))

				If C00->(FieldPos("C00_ZXML"))<>0 .AND. !Empty(cFileXML) .AND. Empty(C00->C00_ZXML)
					cXMLRead	:=	""
					FT_fUse(cFileXML)
					While (! FT_fEOF())
						cXMLRead	+=	FT_FREADLN()//memoread(cFileXML)//FT_FREADLN()
						FT_fSkip()
					End
					FT_FUSE()

					C00->(RecLock("C00",.F.))
					C00->C00_ZXML	:=	cXMLRead
					C00->(MsUnlock())

				EndIf

			ElseIf cModImp == "2"
				aParamBox	:=	{}
				aRetParam	:=	{}
				//aAdd(aParamBox, {6, 'Salvar em',"C:\Temp"+space(100),"",'','',60,.T.,'Arquivos .xml |*.xml',,GETF_LOCALHARD+GETF_NETWORKDRIVE+GETF_RETDIRECTORY,.F. })
				aAdd(aParamBox, {6, 'Abrir em',"C:\Temp"+space(100),"",'','',60,.F.,'Arquivos .xml |*.xml',,GETF_LOCALHARD+GETF_NETWORKDRIVE,.F. })
				If !ParamBox(aParamBox, cTitulo, @aRetParam, bOk, aButtons, lCentered, nPosx,nPosy,/*oPanel*/ , cLoad, lCanSave, lUserSave)
					aRetParam	:=	{}
					Break
				EndIf
				If empty(aRetParam)
					Break
				EnDIf
				cFileXML	:= aRetParam[1]

			ElseIf cModImp == "3"
				/*nao manifestado 32211001379126000262550020000070621100314276*/
				/*manifestado 42211007925786000105550020000462661581963050
				210200 – Confirmada a Operação;
					210210 – Ciência da Operação;
					210220 – Desconhecida;
				210240 – Operação não Realizada*/
				conout("trava")
				cChvIni := "35220247454467000175550010001247571116811139"
				cChvFin := "42220203525446000128550010000359881021878487"
				cFileXML	:=	U_IXMLDown(cChvFin,"")
				//cCodEve := "210200"
				conout("trava2")
				//MonitEven(cChvIni,cChvFin,cCodEve,,,.f.)
				Break

			EndIf

			If !File(cFileXML)
				conout("arquivo xml "+cFileXML)
				MsgStop("Arquivo não localizado na pasta informado","Atenção - "+ProcName())
				Loop
			EndIf

			FWMsgRun( ,{|| cFileXML	:=	A046DocEnt(cFileXML,cOperac)},"Efetuando leitura do XML...")

			//Quando for direto, sai da tela.
			If cModImp== "0"
				Exit
			EndIf
		EndDo

		lRet	:=	.T.
	End Sequence

	For nk	:=	1 To Len(aMVSave)
		&("MV_PAR"+StrZero(nk,2))	:=	aMVSave[nk]
	Next


Return lRet


/*/{Protheus.doc} CALA036T

Rotina utilizada para testes, passando o arquivo direto

@author charlesT
@since 03/05/2017
@version undefined

@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
User Function CALA036T()

	//cFileXML	:=	"C:\Temp\xml\42170580110034000178550010000075941036464409-nfe.xml"
	//U_CALA046(cFileXML,nil,"2")
	//CALA046(cFileXML,cModImp,cOperac,cCHAVFIND)
	U_CALA046(,"1","2","35150707562871000148550010000062591586284771")
Return nil



/*/{Protheus.doc} IXMLDown

Efetua o download do XML da nota fiscal

@author charlesT
@since 02/05/2017
@version undefined
@param cChaveFI, characters, descricao
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
user function IXMLDown(cChave,cXMLPronto)
	Local aArea		:= GetArea()
	Local aPerg		:= {}
	Local aChaves	:= {}
	Local aXmlRet	:= {}
	//Local cPaExpXml	:= SM0->M0_CODIGO+SM0->M0_CODFIL+"BxXml"
	Local cWhere	:= ""
	Local cAliasTemp:= GetNextAlias()
	Local cURL		:= PadR(GetNewPar("MV_SPEDURL","http://"),250)
	Local cIdEnt	:= RetIdEnti(.F.)
	Local cAmbiente	:= ""
	Local cAviso	:= ""
	Local cHelp		:= ""
	Local lParamOk	:= .F.
	Local lRet		:= .F.
	Local nX		:= 0
	Local nY		:= 0
	Local nZ		:= 0
	Local nW		:= 0
	Local n1		:= 0
	Local nXAux		:= 0
	Local nQtdChv	:= 0
	Local cFileXML	:=	""
	Default  cChave	:=	""
	Default cXMLPronto	:=	""

	//sleep(30000)

	Begin Sequence

		If File(cPathXMNfe+cChave+"nfe.xml")
			cFileXML	:=	cPathXMNfe+cChave+"nfe.xml"
			Break
		EndIf

		//Caso já possui o XML não precisa consultar
		If !Empty(cXMLPronto)
			cFileXML	:=	cPathXMNfe+cChave+"nfe.xml"
			If !File(cFileXML)
				nHandle  := FCreate(cFileXML)
				If nHandle > 0
					FWrite ( nHandle, cXMLPronto)
					FClose(nHandle)
				EndIf
			EndIf

		Else

			//If !RetRdTSS()
			If !CTIsReady()
				Aviso("Atenção - "+ProcName(),"Execute o módulo de configuração do serviço, antes de utilizar esta opção",{"OK"},3)	//"Execute o módulo de configuração do serviço, antes de utilizar esta opção!!!"
				Break
			EndIf

			BeginSql Alias cAliasTemp
				SELECT
					C00_FILIAL,
					C00_CHVNFE
				FROM
					%Table:C00%
				WHERE
					C00_FILIAL = %xFilial:C00%
					AND C00_CHVNFE = %exp:cChave%
					AND C00_STATUS IN ('1', '4')
					AND %notdel%
			EndSql

			If (cAliasTemp)->(Eof())
				//Aviso("Atenção - "+ProcName(),"Chave da Nota Fiscal não localizada no manifesto. Verifica se a chave existe no manifesto do destinatário e se está confirmada","OK",3)//"As notas selecionadas não foram localizadas. Verifique os parâmetros de busca."
				MsgStop("Chave da Nota Fiscal não localizada no manifesto. Verifica se a chave existe no manifesto do destinatário e se está confirmada","Atenção - "+ProcName())
				Break
			EndIf

			//cChaveXML	:=	(cAliasTemp)->C00_CHVNFE
			While !(cAliasTemp)->(Eof())

				aadd(aChaves,cChave)
				(cAliasTemp)->(dbSkip())
			End
			(cAliasTemp)->(dbCloseArea())
			//RestArea(aArea)

			oWs :=WSMANIFESTACAODESTINATARIO():New()
			oWs:cUserToken   := "TOTVS"
			oWs:cIDENT	     := cIdEnt
			oWs:cAMBIENTE	 := ""
			oWs:cVERSAO      := ""
			oWs:_URL         := AllTrim(cURL)+"/MANIFESTACAODESTINATARIO.apw"
			oWs:CONFIGURARPARAMETROS()

			oWs :=WSMANIFESTACAODESTINATARIO():New()
			oWs:cUserToken   := "TOTVS"
			oWs:cIDENT	     := cIdEnt
			oWs:cAMBIENTE	 := ""
			oWs:cVERSAO      := ""
			oWs:_URL         := AllTrim(cURL)+"/MANIFESTACAODESTINATARIO.apw"
			oWs:CONFIGURARPARAMETROS()

			cAmbiente		 := oWs:OWSCONFIGURARPARAMETROSRESULT:CAMBIENTE

			oWs:cUserToken   := "TOTVS"
			oWs:cIDENT	     := cIdEnt
			oWs:cAMBIENTE	 := cAmbiente

			oWs:_URL         := AllTrim(cURL)+"/MANIFESTACAODESTINATARIO.apw"

			//cAviso := "Arquivos gerados: "+ CRLF + CRLF + "Série  Número" + CRLF

			oWs:oWSDOCUMENTOS:oWSDOCUMENTO  := MANIFESTACAODESTINATARIO_ARRAYOFBAIXARDOCUMENTO():New()
			nQtdChv := 0
			While nQtdChv < Len(aChaves)
				oWs:oWSDOCUMENTOS:oWSDOCUMENTO  := MANIFESTACAODESTINATARIO_ARRAYOFBAIXARDOCUMENTO():New()

				If (Len(aChaves) - nQtdChv) < 5
					nXAux := 1
					For nX:= nQtdChv+1 to Len(aChaves)
						aadd(oWs:oWSDOCUMENTOS:oWSDOCUMENTO:oWSBAIXARDOCUMENTO,MANIFESTACAODESTINATARIO_BAIXARDOCUMENTO():New())
						oWs:oWSDOCUMENTOS:oWSDOCUMENTO:oWSBAIXARDOCUMENTO[nXAux]:CCHAVE := aChaves[nX]
						nXAux++
						nQtdChv++
					Next nX

					If oWs:BAIXARXMLDOCUMENTOS()
						If Type ("oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET") <> "U"
							If Type ("oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET") == "A"
								aXmlRet := oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET
							Else
								aXmlRet := {oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET}
							EndIf
						EndIF

						//	Processa({|| lRet := VerifProces(oRet,aXmlRet,aParam,@cAviso)},"Processando","Aguarde, exportando arquivos",.T.)
						cFileXML	:=	VerifProces(aXmlRet,@cAviso)
						conout("trava ")
					else
						conout("travou download")
						/*	For n1:= 1 to  Len(aChaves)
							dbSelectArea("C00")
							dbSetOrder(1)
							nRecNOC00 := 0
							If dbSeek(xFilial("C00")+aChaves[n1])
								nRecNOC00 := C00->(RecNo())
						endif*/
						MonitoraManif(aChaves, cAmbiente, cIdEnt, alltrim(cURL),.f.)
						//	FWMsgRun( ,{|| lRetOk	:=	ManiMonSl(aChaves[n1],cAmbiente,cIdEnt,cURL,nRecNOC00)},"Aguardando autorização SEFAZ...")
						conout("travalretok")
						//	next n1

					EndIf
				Else
					For nY:= 1 to 5
						aadd(oWs:oWSDOCUMENTOS:oWSDOCUMENTO:oWSBAIXARDOCUMENTO,MANIFESTACAODESTINATARIO_BAIXARDOCUMENTO():New())
						oWs:oWSDOCUMENTOS:oWSDOCUMENTO:oWSBAIXARDOCUMENTO[nY]:CCHAVE := aChaves[nY+nQtdChv]
					Next nY
					nQtdChv := nQtdChv + 5

					If oWs:BAIXARXMLDOCUMENTOS()
						If Type ("oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET") <> "U"
							If Type ("oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET") == "A"
								aXmlRet := oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET
							Else
								aXmlRet := {oWs:OWSBAIXARXMLDOCUMENTOSRESULT:OWSDOCUMENTORET:OWSBAIXARDOCUMENTORET}
							EndIf
						EndIF
						//Processa({|| lRet := VerifProces(oRet,aXmlRet,aParam,@cAviso)},"Processando","Aguarde, exportando arquivos",.T.)
						cFileXML	:=	VerifProces(aXmlRet,@cAviso)
					else
						MonitoraManif(aChaves, cAmbiente, cIdEnt, alltrim(cURL),.f.)
						conout("travou download")
					EndIf
				EndIf
			EndDo

		EndIf


	End Sequence

Return cFileXML


/*/{Protheus.doc} VerifProces
//Função auxiliar para o processamento da exportação do arquivo zip
@author charlesT
@since 03/05/2017
@version undefined
@param oRet, object, descricao
@param aXmlRet, array, descricao
@param cAviso, characters, descricao
@param cFileXML, characters, descricao
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function VerifProces(aXmlRet,cAviso)
	Local nZ 		:= 0
	//Local cDestino 	:= ""
	Local cDrive   	:= ""
	Local cNfeProt  := ""
	Local cNfe		:= ""
	Local cNfeProc	:= ""
	Local cChave	:= ""
	Local cNfeZip	:= ""
	Local cNfeProcZi:= ""
	Local lRet		:= .F.
	Local nHandle	:= 0
	Local oRet
	Local cFileXML	:=	""
	Local CNFEPROTZI	:=	""
	Begin Sequence

		ProcRegua(Len(aXmlRet))
		//SplitPath(cPathXMNfe,@cDrive,@cDestino,"","")
		//cDestino := cDrive+cDestino
		//cFileXML	:=	cDestino

		For nZ:=1 to Len(aXmlRet)
			IncProc()
			oRet := aXmlRet[nZ]

			If oRet:cChvStatus == "137"
				cAviso += "Série: "+SubStr(oRet:CCHAVE,23,3)+ " Documento:"+SubStr(oRet:CCHAVE,26,9)+" - Código:"+oRet:cChvStatus+" Mensagem:"+ oRet:CCHVDESC+CRLF
				Loop
			EndIf

			If !Empty(oRet:CCHAVE)
				cChave	:= oRet:CCHAVE
			EndIf

			If  (!Empty(oRet:CCHVSTATUS) .and. ('138' $ oRet:CCHVSTATUS .or. '140' $ oRet:CCHVSTATUS .or. '656' $ oRet:CCHVSTATUS))   //140: Download disponibilizado - 656:Consumo indevido (tras dos campos da SPED156)
				If !Empty(oRet:CNFEPROTZIP)
					cNfeProtZi	:= oRet:CNFEPROTZIP
				EndIf
				If !Empty(oRet:CNFEZIP)
					cNfeZip	:= oRet:CNFEZIP
				EndIf
				If  !Empty(oRet:CNFEPROCZIP)
					cNfeProcZi	:= oRet:CNFEPROCZIP
				EndIf
			EndIf

			If Empty(cChave)
				cAviso += "Série: "+SubStr(oRet:CCHAVE,23,3)+ " Documento:"+SubStr(oRet:CCHAVE,26,9)+" - Chave em Branco"+CRLF
				Loop
			EndIf

			If ( Left(LTrim(cVersaoTSS),2) <> "12" .And. Val(cVersaoTSS) >= 271 ) .Or. ( Left(LTrim(cVersaoTSS),2) == "12" .And. Val(cVersaoTSS) >= 121016 )

			If !Empty( cNfeProcZi ) .AND. !'<nfeProc' $ cNfeProcZi
				nHandle  := FCreate( cPathXMNfe+cChave+"-procNFe.gz" )
				If nHandle > 0
					FWrite( nHandle, cNfeProcZi )
					FClose( nHandle )
				EndIf
				GzDecomp(cPathXMNfe+cChave+"-procNFe.gz",cPathXMNfe)
				If File(cPathXMNfe+cChave+"-procNFe")
					FRENAME(cPathXMNfe+cChave+"-procNFe", cPathXMNfe+cChave+"-procNFe.xml")
				EndIf
				cFileXML	:=	cPathXMNfe+cChave+"-procNFe.xml"
			EndIf

			Else
			if '<protNFe' $ cNfeProtZi .And. '<NFe' $ cNfeZip
				cFileXML	:=	cPathXMNfe+cChave+"nfe.xml"
				nHandle  := FCreate(cFileXML)
				nAt	:= At(' versao="', cNfeZip )
				cVersao := SubStr(cNfeZip,nAt,14)
				If nHandle > 0
					FWrite ( nHandle, EncodeUtf8('<nfeProc'+cVersao+' xmlns="http://www.portalfiscal.inf.br/nfe">'+cNfeZip+cNfeProtZi+'</nfeProc>'))
					FClose(nHandle)
				EndIf
			endif

			If !Empty(cNfeProcZi)
				cFileUnzip	:=	cPathXMNfe+cChave+"procNFe.zip"
				cNfeProc := EncodeUtf8(Decode64(cNfeProcZi))
				//cNfeProc := EncodeUtf8(Decode64(cNfeProcZi))
				nHandle  := FCreate(cFileUnzip)
				If nHandle > 0
					FWrite ( nHandle, cNfeProc)
					FClose(nHandle)
				EndIf
				FUnzip(cFileUnzip,cPathXMNfe)

			EndIf
			EndIf

			//cAviso += "Série: "+SubStr(oRet:CCHAVE,23,3)+ " Documento:"+SubStr(oRet:CCHAVE,26,9)+" - Código:"+oRet:cChvStatus+" Mensagem:"+ oRet:CCHVDESC+CRLF

		Next

	End Sequence

Return cFileXML


/*/{Protheus.doc} A036DocEnt

Insere o documento de entrada conforme XML

@authr TSC679 - CHARLES REITZ
@since 02/05/2017
@version undefined
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function A046DocEnt(cFileXML,cOperac)
	Local oXml			:= Nil
	Local nXmlStatus
	Local cXml, cAviso, cErro, nHdlMod
	Local aGetAux		:= {}
	Local nUsado 		:= 0
	Local nOpcGet		:= 0
	Local cDoc, cSerie, cCgcFor, dEmissao, _x, _c, cProdFor, cProduto, cPedQry, aTam, _oDlg, _y, cPedido, cItem
	Local nIndAxSA2	:= SA2->(IndexOrd())
	Local aSegSA2		:= SA2->(GetArea())
	Local nPosFil
	Local nPosDoc
	Local nPosCodF
	Local nPosDesF
	Local nPosProd
	Local nPosQtd
	Local nPosVal
	Local nPosTot
	Local nPosPed
	Local nPosProF
	Local aItensNF
	Local nPosProXM
	Local nPosNCM
	Local nPosPedI
	Local cMask       	:= "Arquivos Texto (*.TXT) |*.txt|"
	Local lSaldo 		:= .T.
	Local cTipo       	:= "N"
	Local lRet			:=	.F.
	Local a103Cab		:= {}
	Local nOpc	 	:= 3
	Local aHeader		:= {}
	Local a103Item	:= {}
	Local aIPI		:= {}
	Local aICMS		:= {}
	Local oIpi		:= Nil
	Local oIcms		:= Nil
	Local cCgcFor
	Local lOk       := .T.
	Local aCoors 		:= FWGetDialogSize( oMainWnd )
	Local oIpi		:= nil
	Local oIcms		:= nil
	Local cMsgWarn	:=	""
	Local cOrigDoc	:=	""
	Local cOrigSerie	:=	""
	Local cEspecie
	Local oNF			:=	nil
	Local oTempTable	:= nil
	Local nCarcIt		:=	GetSx3Cache("D1_ITEM","X3_TAMANHO")
	Private aDlpTot := {} /**/
	Private cTexto   	:= ""
	Private aCols	 	:= {}
	Private nOpc
	Private nTotalDoc	:=	0
	Default cOperac		:=	 "" //1-Presta Nota /Documento entrada
	//Crio objeto XML com o conteudo do arquivo
	Procregua(0)

	Begin Sequence
		aTRBInfo	:=	XMLTrb()
		oTempTable	:= aTRBInfo[4]

		// Entao estou lendo o arquivo MODELO das etiquetas.
		nHdlMod := FT_FUse(Alltrim(cFileXML))

		If nHdlMod == -1
			MsgStop("O arquivo de nome " + AllTrim(cFileXML) + " nao pode ser aberto","Atenção - "+ProcName())
			lRet = .F.
		Endif

		// Varro o arquivo Modelo e vou alimentando o novo arquivo.
		cXml := ""

		FT_FGOTOP()

		While !FT_FEOF()
			Incproc("Lendo arquivo XML...")
			cXml += FT_FREADLN()
			FT_FSKIP()
		EndDo

		FT_FUSE()

		cAviso	:= ""
		cErro		:= ""
		oXml		:= XmlParser(cXml,"_",@cAviso,@cErro)

		If !Empty(cAviso)
			MsgStop("Não foi possível ler o arquivo XML.","Atenção - "+ProcName())
			Break

		EndIf

		If !Empty(cErro)
			MsgStop("Não foi possível ler o arquivo XML.","Atenção - "+ProcName())
			Break
		EndIf

		//Verifico 	se foi possivel criar o objeto oXML
		If (oXml == Nil)
			MsgStop("Não foi possível ler o arquivo XML.","Atenção - "+ProcName())
			Break
		Endif

		If XmlChildEx(oXml,"_NFEPROC")<> nil
			oNF := oXml:_NFeProc:_NFe
		ElseIf XmlChildEx(oXml,"_NFE")<> nil
			oNF := oXml:_NFe
		Else
			oNF	:=	nil
		EndIf

		If XmlChildEx(oXml,"_CTEPROC")<> nil
			oCte := oXml:_CTEProc:_CTE
		ElseIf XmlChildEx(oXml,"_CTE")<> nil
			oCte := oXml:_CTE
		Else
			oCte	:=	nil
		EndIf
		//If XmlChildEx(oXml,"_NFEPROC")<> NIL .AND.;
		//	XmlChildEx ( oXml:_NFEPROC,"_NFE")<> NIL .AND.;
		//	XmlChildEx ( oXml:_NFEPROC:_NFE,"_INFNFE")<> NIL
		//	cEspecie	:=	"SPED"

		If oNF == nil
			cEspecie	:=	"CTE"

			//Localiza a chave da nota fiscal
			If XmlChildEx(oXml,"_CTEPROC")<> nil .AND. XmlChildEx(oXml:_CTEPROC,"_PROTCTE")<> nil
				oProtNFE	:=	oXml:_CTEPROC:_PROTCTE
			ElseIF XmlChildEx(oXml,"_CTE")<> nil .AND. XmlChildEx(oXml:_CTE,"_PROTCTE")<> nil
				oProtNFE	:=	oXml:_CTENFE:_PROTCTE
			eLSE
				oProtNFE	:=	nil
			EndIf

			If oProtNFE == nil
				MsgStop("Não foi localizado chave da nota fiscal no XML, falha no arquivo","Atenção - "+ProcName())
				Break
			Else
				If XmlChildEx(oProtNFE,"_INFPROT")<> nil
					cChave	:= oProtNFE:_INFPROT:_CHCTE:TEXT

					If Empty(cChave)
						MsgStop("Não foi localizado chave da nota fiscal no XML","Atenção - "+ProcName())
						Break
					EndIf

				EndIf
			EndIf


			oIdent     	:= oCte:_InfCte:_IDE
			oEmitente  	:= oCte:_InfCte:_Emit
			oDestino   	:= oCte:_InfCte:_Dest

			//carrega dados do cabeçalho
			cCgcFor		:= oEmitente:_CNPJ:TEXT
			cDoc		:= StrZero(Val(oIdent:_nCt:TEXT),9)
			cSerie		:= StrZero(Val(oIdent:_SERIE:TEXT),3)

			aadd(aDlpTot,dEmissao)
			aadd(aDlpTot,cCgcFor)
			aadd(aDlpTot,cDoc)
			aadd(aDlpTot,cSerie)
			aadd(aDlpTot,nBaseIPI)

			//trata as tags conforme a versao do XML
			If XmlChildEx (oIdent,"_DEMI") <> NIL
				dEmissao := Stod(StrTran(oIdent:_DEMI:TEXT,"-",""))
			ElseIf XmlChildEx (oIdent,"_DHEMI") <> NIL
				dEmissao := Stod(StrTran(oIdent:_DHEMI:TEXT,"-",""))
			EndIf

		Else
			cEspecie	:=	"SPED"

			//Localiza a chave da nota fiscal
			If XmlChildEx(oXml,"_NFEPROC")<> nil .AND. XmlChildEx(oXml:_NFEPROC,"_PROTNFE")<> nil
				oProtNFE	:=	oXml:_NFEPROC:_PROTNFE
			ElseIF XmlChildEx(oXml,"_NFE")<> nil .AND. XmlChildEx(oXml:_NFe,"_PROTNFE")<> nil
				oProtNFE	:=	oXml:_NFE:_PROTNFE
			eLSE
				oProtNFE	:=	nil
			EndIf

			If oProtNFE == nil
				MsgStop("Não foi localizado chave da nota fiscal no XML, falha no arquivo","Atenção - "+ProcName())
				Break
			Else
				If XmlChildEx(oProtNFE,"_INFPROT")<> nil
					cChave	:= oProtNFE:_INFPROT:_CHNFE:TEXT

					If Empty(cChave)
						MsgStop("Não foi localizado chave da nota fiscal no XML","Atenção - "+ProcName())
						Break
					EndIf

				EndIf
			EndIf


			oIdent     	:= oNF:_InfNfe:_IDE
			oEmitente  	:= oNF:_InfNfe:_Emit
			oDestino   	:= oNF:_InfNfe:_Dest
			oTotal		:= oNF:_InfNfe:_Total
			oTransp		:= oNF:_InfNfe:_Transp
			oInfoAdic	:= oNF:_InfNfe:_infAdic

			If XmlChildEx(oNF:_InfNfe,"_DET")<> nil
				If ValType(oNF:_InfNfe:_DET) <> "A"
					aItensNF	:=	{oNF:_InfNfe:_DET}
				Else
					aItensNF	:=	oNF:_InfNfe:_DET
				EndIf
			EndIf

			If XmlChildEx(oNF:_InfNfe,"_COBR")<> nil
				oCobr		:= oNF:_InfNfe:_Cobr
			Endif

			//carrega dados do cabeçalho
			cCgcFor		:= oEmitente:_CNPJ:TEXT
			cDoc		:= StrZero(Val(oIdent:_NNF:TEXT),9)
			cSerie		:= StrZero(Val(oIdent:_SERIE:TEXT),3)

			//trata as tags conforme a versao do XML
			If XmlChildEx (oIdent,"_DEMI") <> NIL
				dEmissao := Stod(StrTran(oIdent:_DEMI:TEXT,"-",""))
			ElseIf XmlChildEx (oIdent,"_DHEMI") <> NIL
				dEmissao := Stod(StrTran(oIdent:_DHEMI:TEXT,"-",""))
			EndIf


		EndIf

		// Busco o Fornecedor pelo CNPJ.
		SA2->(dbSetOrder(3))
		If !SA2->(dbSeek(xFilial("SA2")+cCgcFor))
			MsgStop("Fornecedor não localizado pelo CNPJ: " +cCgcFor,"Atenção - "+ProcName())
			Break
		EndIf

		// Verifico se a nota ja existe.
		SF1->(dbSetOrder(1))
		If SF1->(dbSeek(xFilial("SF1")+cDoc+cSerie+SA2->A2_COD+SA2->A2_LOJA+"N"))
			MsgStop("Nota Fiscal já importada. Documento: "+cDoc+" Serie:"+cSerie+" Código:"+SA2->A2_COD+" Loja:"+SA2->A2_LOJA +" Nome: "+SA2->A2_NOME,"Atenção - "+ProcName())
			Break
		EndIf

		//Busca a nota fiscal original em caso de devolução
		//Tratamento para nota fiscal eletronica
		If cEspecie == "SPED"

			If  XmlChildEx(oIdent,"_NFREF")<>NIL .AND. ValType(oIdent:_NFREF) <> "A" .AND. ;
					XmlChildEx(oIdent:_NFREF,"_REFNFE")<>NIL
				cChaveXMLR	:=	oIdent:_NFREF:_REFNFE:TEXT

				BeginSql alias "TRBSF2"
					SELECT
						F2_FILIAL,
						F2_CHVNFE,
						F2_DOC,
						F2_SERIE
					FROM
						%table:SF2% SF2
					WHERE
						SF2.%notdel%
						AND SF2.F2_FILIAl = %xFilial:SF1%
						AND SF2.F2_CHVNFE = %exp:cChaveXMLR%
				EndSql

				If !Empty(TRBSF2->F2_CHVNFE)
					cOrigDoc	:=	TRBSF2->F2_DOC
					cOrigSerie	:=	TRBSF2->F2_SERIE
				Else
					cMsgWarn	+=	"Chave "+cChaveXMLR+" não localizado nas notas de saída"+chr(13)+chr(10)
				EndIf
				TRBSF2->(dbCloseArea())
			EndIf
			nBaseIPI	:= 0

			//Soma a base de IPI
			For _x := 1 To Len(aItensNF)

				If XmlChildEx ( aItensNF[_x]:_IMPOSTO,"_IPI")<>Nil
					oIpi := XmlGetChild(aItensNF[_x]:_IMPOSTO:_IPI,2)
					//Verifica se há IPI
					If(XmlChildEx ( oIpi ,"_VBC")<>Nil)
						nBaseIPI	+= val(oIpi:_VBC:TEXT)
					EndIf
				EndIF

			Next

			For _x := 1 To Len(aItensNF)
				cProduto	:=	""
				cCodProdFor	:=	Alltrim(aItensNF[_x]:_PROD:_CPROD:TEXT)

				(aTRBInfo[1])->(RecLock(aTRBInfo[1],.T.))

				(aTRBInfo[1])->F1_TIPO		:=	"N"
				(aTRBInfo[1])->F1_FORMUL	:=	"N"
				(aTRBInfo[1])->D1_ITEM		:=	StrZero(_x,nCarcIt)
				(aTRBInfo[1])->F1_ESPECIE	:=	cEspecie
				(aTRBInfo[1])->F1_DOC		:=	If(lMVZerosDoc,cDoc,cValtoChar(Val(oIdent:_NNF:TEXT)))
				(aTRBInfo[1])->F1_SERIE		:=	cSerie
				(aTRBInfo[1])->F1_EMISSAO 	:=  dEmissao
				(aTRBInfo[1])->F1_FORNECE	:=	SA2->A2_COD
				(aTRBInfo[1])->F1_LOJA		:=	SA2->A2_LOJA
				(aTRBInfo[1])->A2_NOME		:=	SA2->A2_NOME
				(aTRBInfo[1])->A2_CGC		:=	SA2->A2_CGC
				(aTRBInfo[1])->F1_COND		:=	SA2->A2_COND
				(aTRBInfo[1])->E2_NATUREZ	:=	SA2->A2_NATUREZ
				(aTRBInfo[1])->D1_QUANT		:=	Val(aItensNF[_x]:_PROD:_QCOM:TEXT)
				(aTRBInfo[1])->D1_VUNIT		:=	Val(aItensNF[_x]:_PROD:_VUNCOM:TEXT)
				(aTRBInfo[1])->D1_SEGUM 	:=  Alltrim(aItensNF[_x]:_PROD:_UCOM:TEXT)
				(aTRBInfo[1])->D1_TOTAL		:=	(aTRBInfo[1])->D1_QUANT*(aTRBInfo[1])->D1_VUNIT
				nTotalDoc	+= (aTRBInfo[1])->D1_TOTAL
				(aTRBInfo[1])->A5_CODPRF	:=	cCodProdFor
				//(aTRBInfo[1])->B1_DESC	:=	aItensNF[_x]:_PROD:_XPROD:TEXT
				(aTRBInfo[1])->A5_DESCPRF	:=	aItensNF[_x]:_PROD:_XPROD:TEXT
				(aTRBInfo[1])->B1_POSIPI	:=	aItensNF[_x]:_PROD:_NCM:TEXT
				(aTRBInfo[1])->F1_CHVNFE	:=	cChave//alltrim(oXml:_NFEPROC:_PROTNFE:_INFPROT:_CHNFE:TEXT)
				(aTRBInfo[1])->B1_POSIPI	:=	aItensNF[_x]:_PROD:_NCM:TEXT

				(aTRBInfo[1])->F1_DESCONT	:=	Val(oTotal:_ICMSTot:_vDesc:TEXT)
				(aTRBInfo[1])->F1_DESPESA	:=	Val(oTotal:_ICMSTot:_vOutro:TEXT)
				(aTRBInfo[1])->F1_SEGURO	:=	Val(oTotal:_ICMSTot:_vSeg:TEXT)
				(aTRBInfo[1])->F1_FRETE		:=	Val(oTotal:_ICMSTot:_vFrete:TEXT)
				(aTRBInfo[1])->F1_BASEICM	:= Val(oTotal:_ICMSTot:_vBC:TEXT)
				(aTRBInfo[1])->F1_VALICM	:=	Val(oTotal:_ICMSTot:_vICMS:TEXT)
				(aTRBInfo[1])->F1_BASEIPI	:=	nBaseIPI//Val(oTotal:_ICMSTot:_vIPI:TEXT)
				//(aTRBInfo[1])->F1_VALIPI	:=
				(aTRBInfo[1])->F1_BRICMS	:=	Val(oTotal:_ICMSTot:_vBCST:TEXT)
				(aTRBInfo[1])->F1_ICMSRET	:=	Val(oTotal:_ICMSTot:_vST:TEXT)

				If lMVSavMemN .AND. XmlChildEx(oInfoAdic,"_INFCPL")<>NIL
					(aTRBInfo[1])->F1_MENNOTA	:=	oInfoAdic:_infCpl:TEXT
				EndIf

				If lMVTpFrete
					If Alltrim(oTransp:_modFrete:TEXT)=="0"
						cModFrete := "C"
					ElseIf Alltrim(oTransp:_modFrete:TEXT)=="1"
						cModFrete := "F"
					ElseIf Alltrim(oTransp:_modFrete:TEXT)=="2"
						cModFrete := "T"
					ElseIf Alltrim(oTransp:_modFrete:TEXT)=="9"
						cModFrete := "S"
					Else
						cModFrete	:= ""
					Endif
					(aTRBInfo[1])->F1_TPFRETE	:= cModFrete
				EndIf

				If SF1->(FieldPos("F1_PLACA")) > 0 .And. XmlChildEx(oTransp,"_VEICTRANSP")<>NIL
					(aTRBInfo[1])->F1_PLACA	:=	oTransp:_VEICTRANSP:_PLACA:TEXT
				Endif

				If SF1->(FieldPos("F1_PBRUTO")) > 0 .And.  XmlChildEx(oTransp,"_PESOB")<>NIL
					(aTRBInfo[1])->F1_PBRUTO	:=	Val(oTransp:_VOL:_PESOB:TEXT)
				Endif
				If SF1->(FieldPos("F1_PLIQUI")) > 0 .And.  XmlChildEx(oTransp,"_PESOL")<>NIL
					(aTRBInfo[1])->F1_PLIQUI	:=	Val(oTransp:_VOL:_PESOL:TEXT)
				Endif


				//Verifica se há algum tipo de ICMS
				If (XmlChildEx ( aItensNF[_x]:_IMPOSTO,"_ICMS")<>Nil)
					oIcms := XmlGetChild(aItensNF[_x]:_IMPOSTO:_ICMS,1)
					//Verifica se ICMS
					If(XmlChildEx ( oIcms,"_VICMS")<>Nil)
						(aTRBInfo[1])->D1_VALICM :=	val(oIcms:_VICMS:TEXT)
					EndIf
				EndIf

				//Verifica de há algum tipo de IPI
				If XmlChildEx ( aItensNF[_x]:_IMPOSTO,"_IPI")<>Nil
					oIpi := XmlGetChild(aItensNF[_x]:_IMPOSTO:_IPI,2)
					//Verifica se há IPI
					If(XmlChildEx ( oIpi ,"_VIPI")<>Nil)
						(aTRBInfo[1])->D1_VALIPI :=	val(oIpi:_VIPI:TEXT)
					EndIf
				EndIF

				// Query que verifica se existe o codigo de produto do fornecedor na
				// amarracao padrao do sistema.
				BeginSql alias "TRBSA5"
					SELECT
						A5_FILIAL,
						A5_PRODUTO
					FROM
						%table:SA5%
					WHERE
						A5_FILIAL = %xFilial:SA5%
						AND D_E_L_E_T_ = ' '
						AND A5_CODPRF = %exp:cCodProdFor%
						AND A5_FORNECE = %exp:SA2->A2_COD%
						AND A5_LOJA = %exp:SA2->A2_LOJA%
				EndSQl
				If Empty(TRBSA5->A5_PRODUTO)
					cMsgWarn	+=	"Não localizado amarração Produto X Fornecedor. Produto Fornecedor:"+cCodProdFor+chr(13)+chr(10)
				Else
					cProduto	:=	TRBSA5->A5_PRODUTO
				EndIf
				TRBSA5->(dbCloseArea())

				//Busca dados da nota fiscal original
				//Item da nota original (compara o produto)
				//tes de devolução
				If !Empty(cOrigDoc) .AND. !Empty(cProduto)
					(aTRBInfo[1])->D1_NFORI 	:=	cOrigDoc
					(aTRBInfo[1])->D1_SERIORI 	:=	cOrigSerie

					BeginSql alias "TRBSD2"
						SELECT
							F2_CHVNFE,
							F2_DOC,
							F2_SERIE,
							D2_ITEM,
							F4_TESDV
						FROM
							%table:SF2% SF2
						INNER JOIN %table:SD2% SD2
						ON SD2.%notdel%
							AND SD2.D2_FILIAL = %xFilial:SD2%
							AND SD2.D2_DOC = SF2.F2_DOC
							AND SD2.D2_SERIE = SF2.F2_SERIE
						INNER JOIN %table:SF4% SF4
						ON SF4.%notdel%
							AND SF4.F4_FILIAL = %xFilial:SF4%
							AND SF4.F4_CODIGO = SD2.D2_TES
						WHERE
							SF2.%notdel%
							AND SF2.F2_FILIAL = %xFilial:SF2%
							AND SF2.F2_DOC = %exp:cOrigDoc%
							AND SF2.F2_SERIE = %exp:cOrigSerie%
							AND SD2.D2_COD = %exp:cProduto%
					EndSql

					If TRBSD2->(!Eof())
						(aTRBInfo[1])->D1_ITEMORI 	:=	TRBSD2->D2_ITEM
						(aTRBInfo[1])->D1_TES		:=	TRBSD2->F4_TESDV
					Else
						cMsgWarn	:=	"Não localizado item da nota original."+chr(13)+chr(10)
					EndIf

				EndIf

				//Pedido Original, caso for preenchido a TAG
				If XmlChildEx(aItensNF[_x]:_PROD,"_XPED")<>Nil

					//Verifica se o pedido existe
					BeginSql alias "TRBSC7"
						SELECT
							DISTINCT C7_FILIAL,
							C7_NUM,
							C7_COND
						FROM
							%table:SC7% SC7
						WHERE
							SC7.%notdel%
							AND SC7.C7_FILIAL = %xFilial:SC7%
							AND SC7.C7_NUM = %exp:StrZero(val(aItensNF[_x]:_PROD:_XPED:TEXT),GetSX3Cache("D1_PEDIDO", "X3_TAMANHO"))%
					EndSql

					If !Empty(TRBSC7->C7_NUM)
						(aTRBInfo[1])->D1_PEDIDO	:=	StrZero(val(aItensNF[_x]:_PROD:_XPED:TEXT),GetSX3Cache("D1_PEDIDO","X3_TAMANHO"))
						If Empty((aTRBInfo[1])->F1_COND) .AND. !Empty(TRBSC7->C7_COND)
							(aTRBInfo[1])->F1_COND	:= TRBSC7->C7_COND
						EndIf

						//Localiza o item do pedido de compra
						If XmlChildEx(aItensNF[_x]:_PROD,"_NITEMPED")<>Nil
							(aTRBInfo[1])->D1_ITEMPC	:=	StrZero(val(aItensNF[_x]:_PROD:_NITEMPED:TEXT),TamSX3("D1_ITEMPC")[1])

							//Busca item do pedido original
							BeginSql alias "TRBSC7B"
								SELECT
									C7_PRODUTO
								FROM
									%table:SC7% SC7
								WHERE
									SC7.%notdel%
									AND SC7.C7_FILIAL = %xFilial:SC7%
									AND SC7.C7_NUM = %exp:(aTRBInfo[1])->D1_PEDIDO%
									AND SC7.C7_ITEM = %exp:(aTRBInfo[1])->D1_ITEMPC%
							EndSql

							If Empty(TRBSC7B->C7_PRODUTO)
								cMsgWarn	+=	"Pedido: "+(aTRBInfo[1])->D1_PEDIDO+" Item:"+(aTRBInfo[1])->D1_ITEMPC+" informado no XML porém não localizado no sistema"+chr(13)+chr(10)
							ElseIf cProduto <> SC7->C7_PRODUTO
								cMsgWarn	+=	"Produto do pedido de compra divergente da amarração Prod X Fornecedor "+chr(13)+chr(10)
							EndIf
							TRBSC7B->(dbCloseArea())

							//Caso não foi informado, tenta localizar pelo PEDIDO+PRODUTO
						Else

							//Busca item do pedido original
							BeginSql alias "TRBSC7BI"
								SELECT
									C7_NUM,
									C7_ITEM
								FROM
									%table:SC7% SC7
								WHERE
									SC7.%notdel%
									AND SC7.C7_NUM = %exp:(aTRBInfo[1])->D1_PEDIDO%
									AND SC7.C7_PRODUTO = %exp:cProduto%
							EndSql
							(aTRBInfo[1])->D1_ITEMPC	:= TRBSC7BI->C7_ITEM
							TRBSC7BI->(dbCloseArea())
						EndIf
					Else
						cMsgWarn	+=	"Pedido: "+StrZero(val(aItensNF[_x]:_PROD:_XPED:TEXT),GetSX3Cache("D1_PEDIDO","X3_TAMANHO"))+" não localizado no sistema"+chr(13)+chr(10)
					EndIf
					TRBSC7->(dbCloseArea())

				EndIf

				(aTRBInfo[1])->D1_COD		:=	cProduto
				//(aTRBInfo[1])->(msUnlock())
			Next _x

			//Tratamento para CTE
		Else

			cProduto	:=	""
			//cCodProdFor	:=	Alltrim(aItensNF[_x]:_PROD:_CPROD:TEXT)

			(aTRBInfo[1])->(RecLock(aTRBInfo[1],.T.))

			(aTRBInfo[1])->F1_TIPO		:=	"N"
			(aTRBInfo[1])->F1_FORMUL	:=	"N"
			(aTRBInfo[1])->D1_ITEM		:=	StrZero(1,nCarcIt)
			(aTRBInfo[1])->F1_ESPECIE	:=	cEspecie
			(aTRBInfo[1])->F1_DOC		:=	If(lMVZerosDoc, cDoc ,cValtoChar(Val( oIdent:_nCt:TEXT )))
			(aTRBInfo[1])->F1_SERIE		:=	cSerie
			(aTRBInfo[1])->F1_EMISSAO 	:=  dEmissao
			(aTRBInfo[1])->F1_FORNECE	:=	SA2->A2_COD
			(aTRBInfo[1])->F1_LOJA		:=	SA2->A2_LOJA
			(aTRBInfo[1])->A2_NOME		:=	SA2->A2_NOME
			(aTRBInfo[1])->A2_CGC		:=	SA2->A2_CGC
			(aTRBInfo[1])->F1_COND		:=	SA2->A2_COND
			(aTRBInfo[1])->E2_NATUREZ	:=	SA2->A2_NATUREZ
			(aTRBInfo[1])->D1_QUANT		:=	1
			(aTRBInfo[1])->D1_VUNIT		:=	Val(oCte:_INFCTE:_VPREST:_VTPREST:TEXT)//Val(aItensNF[_x]:_PROD:_VUNCOM:TEXT)
			(aTRBInfo[1])->D1_TOTAL		:=	 Val(oCte:_INFCTE:_VPREST:_VTPREST:TEXT)//(aTRBInfo[1])->D1_QUANT*(aTRBInfo[1])->D1_VUNIT
			nTotalDoc	+= (aTRBInfo[1])->D1_TOTAL
			//cDesProd	:= Posicione("SB1",1,xFilial("SB1")+cCodPrdFre,"B1_DESC")
			(aTRBInfo[1])->A5_CODPRF	:=	cCodPrdFre//cCodProdFor
			//(aTRBInfo[1])->B1_DESC		:=	Posicione("SB1",1,xFilial("SB1")+cCodPrdFre,"B1_DESC")
			//(aTRBInfo[1])->A5_DESCPRF	:=	aItensNF[_x]:_PROD:_XPROD:TEXT
			//(aTRBInfo[1])->B1_POSIPI	:=	aItensNF[_x]:_PROD:_NCM:TEXT
			(aTRBInfo[1])->F1_CHVNFE	:=	cChave//alltrim(oXml:_NFEPROC:_PROTNFE:_INFPROT:_CHNFE:TEXT)
			//(aTRBInfo[1])->B1_POSIPI	:=	aItensNF[_x]:_PROD:_NCM:TEXT

			//(aTRBInfo[1])->F1_DESCONT	:=	Val(oTotal:_ICMSTot:_vDesc:TEXT)
			//(aTRBInfo[1])->F1_DESPESA	:=	Val(oTotal:_ICMSTot:_vOutro:TEXT)
			//(aTRBInfo[1])->F1_SEGURO	:=	Val(oTotal:_ICMSTot:_vSeg:TEXT)
			//(aTRBInfo[1])->F1_FRETE		:=	Val(oTotal:_ICMSTot:_vFrete:TEXT)
			//(aTRBInfo[1])->F1_BASEICM	:= Val(oTotal:_ICMSTot:_vBC:TEXT)
			//(aTRBInfo[1])->F1_VALICM	:=	Val(oTotal:_ICMSTot:_vICMS:TEXT)
			//(aTRBInfo[1])->F1_BASEIPI	:=	nBaseIPI//Val(oTotal:_ICMSTot:_vIPI:TEXT)
			//(aTRBInfo[1])->F1_VALIPI	:=
			//(aTRBInfo[1])->F1_BRICMS	:=	Val(oTotal:_ICMSTot:_vBCST:TEXT)
			//(aTRBInfo[1])->F1_ICMSRET	:=	Val(oTotal:_ICMSTot:_vST:TEXT)
			(aTRBInfo[1])->D1_TES		:=	cTesPRdFre
			//If lMVSavMemN .AND. XmlChildEx(oInfoAdic,"_INFCPL")<>NIL
			//	(aTRBInfo[1])->F1_MENNOTA	:=	oInfoAdic:_infCpl:TEXT
			//EndIf

			If (XmlChildEx ( oCte:_INFCTE:_IMP,"_ICMS")<>Nil)
				oIcms := XmlGetChild(oCte:_INFCTE:_IMP:_ICMS,1)
				If(XmlChildEx ( oIcms,"_VICMS")<>Nil)
					(aTRBInfo[1])->D1_VALICM :=	val(oIcms:_VICMS:TEXT)
				EndIf
			Else
				aAdd(aICMS,	"0")
			EndIf

			//Verifica de há algum tipo de IPI
			If (XmlChildEx ( oCte:_INFCTE:_IMP,"_IPI")<>Nil)
				oIpi := XmlGetChild(oCte:_INFCTE:_IMP:_IPI,2)
				If(XmlChildEx ( oIpi ,"_VIPI")<>Nil)
					(aTRBInfo[1])->D1_VALIPI :=	val(oIpi:_VIPI:TEXT)
				EndIf
			EndIF
			(aTRBInfo[1])->D1_COD		:=	cCodPrdFre

		EndIf

		//
		//Mensagens de aviso
		If !Empty(cMsgWarn)
			Aviso("Atenção - "+Procname()/*cCaption*/,cMsgWarn /*cMensagem*/,{"OK"}/*aBotoes*/,3,/*cCaption2*/,/*nRotAutDefault*/,/*cBitmap*/,.T./*lEdit*/,12200/*nTimer*/,1/*nOpcPadrao*/)
		ENdIf

		Define MsDialog oDlgPrinc Title "Geração documento entrada - "+If(cOperac=="1","Pré-Nota","Documento Entrada")+" - CALA046" From aCoors[1], aCoors[2] To aCoors[3]-2, aCoors[4]-2 Pixel

		oFWLayer := FWLayer():New()
		oFWLayer:Init( oDlgPrinc, .F., .T. )

		oFWLayer:AddLine( 'UP', 13, .F. )                       // Cria uma "linha" com 50% da tela
		oFWLayer:AddCollumn( 'ALL', 100, .T., 'UP' )            // Na "linha" criada eu crio uma coluna com 100% da tamanho dela
		oPanelUp := oFWLayer:GetColPanel( 'ALL', 'UP' )         // Pego o objeto desse pedaÁo do container
		TSay():New(05,05,{|| "Documento: "+(aTRBInfo[1])->F1_DOC +" Serie:"+(aTRBInfo[1])->F1_SERIE +" Data Emissão:"+dtoc((aTRBInfo[1])->F1_EMISSAO)+" Espécie:"+(aTRBInfo[1])->F1_ESPECIE+" Chave:"+(aTRBInfo[1])->F1_CHVNFE},oPanelUp,,/*oFont*/,,,,.T.,,,400,30,,,,,,.T.)
		TSay():New(15,05,{|| "Fornecedor: "+(aTRBInfo[1])->F1_FORNECE +" Loja:"+(aTRBInfo[1])->F1_LOJA +" Nome:"+alltrim((aTRBInfo[1])->A2_NOME)+" CNPJ/CPF:"+(aTRBInfo[1])->A2_CGC},oPanelUp,,/*oFont*/,,,,.T.,,,400,30,,,,,,.T.)
		TSay():New(25,05,{|| "Total Documento: "+alltrim(Transform(nTotalDoc,GetSX3Cache("F1_VALBRUT","X3_PICTURE")))},oPanelUp,,/*oFont*/,,,,.T.,,,400,30,,,,,,.T.)

		oFWLayer:AddLine( 'DOWN', 82, .F. )                     // Cria uma "linha" com 50% da tela
		oFWLayer:AddCollumn( 'ALL', 100, .T., 'DOWN' )          // Na "linha" criada eu crio uma coluna com 100% da tamanho dela
		oPanelDown := oFWLayer:GetColPanel( 'ALL', 'DOWN' )     // Pego o objeto desse pedaÁo do container

		oBrowseNFE := 	FWFormBrowse():New()
		oBrowseNFE:SetOwner(oPanelDown)
		//oBrowseNFE:oBrowseNFE:SetTemporary(.T.)
		//oBrowseNFE:SetDataTable(.T.)
		oBrowseNFE:SetDataQuery(.F.)
		oBrowseNFE:SetDataTable(.T.)
		oBrowseNFE:SetTemporary(.T.)
		oBrowseNFE:SetAlias(aTRBInfo[1])
		oBrowseNFE:SetEditCell(.T.,{||.T.})
		oBrowseNFE:DisableFilter()
		oBrowseNFE:DisableDetails()
		oBrowseNFE:DisableConfig()
		oBrowseNFE:SetInsert(.f.)
		//oBrowseNFE:SetUpdate(.T.)
		oBrowseNFE:DisableReport()
		//oBrowseNFE:SetDBFFilter()
		//oBrowseNFE:SetUseFilter()
		oBrowseNFE:SetColumns(aTRBInfo[3])
		oBrowseNFE:Activate()
		(aTRBInfo[1])->(dbGoTOp())

		//bOK	:=	{|| IF(A046TdOk(cOperac),A046AutoNF(aTRBInfo[1],cOperac),) ,If(nOpc==1,oDlgPrinc:End(),)}
		bOK	:=	{|| IF(A046AutoNF(aTRBInfo[1],cOperac),oDlgPrinc:End(), )}
		bCan	:=	{||If(MsgYesNo("Deseja sair da tela? Os dados serão perdidos."),oDlgPrinc:End(),)}
		Activate MsDialog oDlgPrinc ON INIT EnchoiceBar(oDlgPrinc,bOK,bCan) CENTERED


		lRet	:=	.T.

	End Sequence

	If !lRet .AND. !Empty(cTexto)
		Aviso("Atenção - "+Procname()/*cCaption*/,cTexto /*cMensagem*/,{"OK"}/*aBotoes*/,3,/*cCaption2*/,/*nRotAutDefault*/,/*cBitmap*/,.T./*lEdit*/,12200/*nTimer*/,1/*nOpcPadrao*/)
	EndIf

	If select(aTRBInfo[1])<>0
		(aTRBInfo[1])->(dbCloseArea())
	EndIf

	If type("oTempTable")<> "U"
		oTempTable:Delete()
	EndIF


Return lRet

/*/{Protheus.doc} A046AutoNF

Rotina automatica de documento de entrada MATA103

@author charlesT
@since 02/05/2017
@version undefined
@param aCamposGet, array, descricao
@param aDados, array, descricao
@param aIpi, array, descricao
@param aICMS, array, descricao
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function A046AutoNF(cAliasF,cOperac)
	Local lRet		:= .F.
	Local nI		:= 0
	Local a103Cab	:=	{}
	Local a103Item	:=	{}
	Local a103LItem	:=	{}
	Local lFirstLin	:=	.T.
	Local aSaveArea	:=	GetArea()
	Local aSaveCL	:=	(cAliasF)->(GetArea())

	Begin Sequence

		(cAliasF)->(dbGoTop())
		While (cAliasF)->(!Eof())

			//Primeira linha monta o cabecalho
			If lFirstLin
				lFirstLin	:=	.F.
				// Monto o array do cabecalho da pre-nota.
				a103Cab	:=	{}
				aadd(a103Cab,{	"F1_TIPO"		,(cAliasF)->F1_TIPO			, Nil})
				aadd(a103Cab,{	"F1_FORMUL"		,(cAliasF)->F1_FORMUL			, Nil})
				aadd(a103Cab,{	"F1_DOC"		,(cAliasF)->F1_DOC			, Nil})
				aadd(a103Cab,{	"F1_SERIE"		,(cAliasF)->F1_SERIE		, Nil})
				aadd(a103Cab,{	"F1_FORNECE"	,(cAliasF)->F1_FORNECE		, Nil})
				aadd(a103Cab,{	"F1_LOJA"		,(cAliasF)->F1_LOJA			, Nil})
				aadd(a103Cab,{	"F1_COND"		,(cAliasF)->F1_COND			, Nil})
				aadd(a103Cab,{	"E2_NATUREZ"	,(cAliasF)->E2_NATUREZ			, Nil})
				aadd(a103Cab,{	"F1_CHVNFE"		,(cAliasF)->F1_CHVNFE		, Nil})
				aadd(a103Cab,{	"F1_EMISSAO"	,(cAliasF)->F1_EMISSAO		, Nil})
				aadd(a103Cab,{	"F1_ESPECIE"	,(cAliasF)->F1_ESPECIE, Nil})
				If !Empty((cAliasF)->F1_DESCONT)
					aadd(a103Cab,{	"F1_DESCONT"	,(cAliasF)->F1_DESCONT, Nil})
				EndIf
				If !Empty((cAliasF)->F1_DESPESA)
					aadd(a103Cab,{	"F1_DESPESA"	,(cAliasF)->F1_DESPESA, Nil})
				EndIf
				If !Empty((cAliasF)->F1_SEGURO)
					aadd(a103Cab,{	"F1_SEGURO"	,(cAliasF)->F1_SEGURO, Nil})
				EndIf
				If !Empty((cAliasF)->F1_FRETE)
					aadd(a103Cab,{	"F1_FRETE"	,(cAliasF)->F1_FRETE, Nil})
				EndIf
				If !Empty((cAliasF)->F1_BASEICM)
					aadd(a103Cab,{	"F1_BASEICM"	,(cAliasF)->F1_BASEICM, Nil})
				EndIf
				If !Empty((cAliasF)->F1_VALICM)
					aadd(a103Cab,{	"F1_VALICM"	,(cAliasF)->F1_VALICM, Nil})
				EndIf
				If !Empty((cAliasF)->F1_BASEIPI)
					aadd(a103Cab,{	"F1_BASEIPI"	,(cAliasF)->F1_BASEIPI, Nil})
				EndIf
				If !Empty((cAliasF)->F1_BRICMS)
					aadd(a103Cab,{	"F1_BRICMS"	,(cAliasF)->F1_BRICMS, Nil})
				EndIf
				If !Empty((cAliasF)->F1_PLACA)
					aadd(a103Cab,{	"F1_PLACA"	,(cAliasF)->F1_PLACA, Nil})
				EndIf
				If !Empty((cAliasF)->F1_PBRUTO)
					aadd(a103Cab,{	"F1_PBRUTO"	,(cAliasF)->F1_PBRUTO, Nil})
				EndIf
				If !Empty((cAliasF)->F1_PLIQUI)
					aadd(a103Cab,{	"F1_PLIQUI"	,(cAliasF)->F1_PLIQUI, Nil})
				EndIf
				If !Empty((cAliasF)->F1_TPFRETE)
					aadd(a103Cab,{	"F1_TPFRETE"	,(cAliasF)->F1_TPFRETE, Nil})
				EndIf
				If !Empty((cAliasF)->F1_MENNOTA)
					aadd(a103Cab,{	"F1_MENNOTA"	,(cAliasF)->F1_MENNOTA, Nil})
				EndIf

			EndIF

			a103LItem	:=	{}

			aadd(a103LItem,{	"D1_ITEM"		, (cAliasF)->D1_ITEM, Nil})
			aadd(a103LItem,{	"D1_COD"		, (cAliasF)->D1_COD, Nil})


			// Diego Kerstner: Inicio
			If !lMVSegUni
				aadd(a103LItem,{	"D1_QUANT"		, (cAliasF)->D1_QUANT, Nil})
			Else
				cSeUmPro := AllTrim(Posicione("SB1",1,xFilial("SB1")+(cAliasF)->D1_COD,"B1_SEGUM"))
				IF (aTRBInfo[1])->D1_SEGUM ==cSeUmPro
					cTipConv := AllTrim(Posicione("SB1",1,xFilial("SB1")+(cAliasF)->D1_COD,"B1_TIPCONV"))
					nConv    := Posicione("SB1",1,xFilial("SB1")+(cAliasF)->D1_COD,"B1_CONV")
					If cTipConv = "M"
						aadd(a103LItem,{	"D1_QUANT"		, ((cAliasF)->D1_QUANT) / nConv, Nil})
					Else
						aadd(a103LItem,{	"D1_QUANT"		, ((cAliasF)->D1_QUANT) * nConv, Nil})
					EndIf
				Else
					aadd(a103LItem,{	"D1_QUANT"		, (cAliasF)->D1_QUANT, Nil})
				EndIf
			EndIf
			// Diego Kerstner: Fim

			aadd(a103LItem,{	"D1_VUNIT"		, (cAliasF)->D1_VUNIT, Nil})
			aadd(a103LItem,{	"D1_TOTAL"		, (cAliasF)->D1_TOTAL, Nil})
			aadd(a103LItem,{	"D1_TES"		, (cAliasF)->D1_TES , Nil})

			IF !Empty((cAliasF)->D1_NFORI)
				aadd(a103LItem,{	"D1_NFORI"		, (cAliasF)->D1_NFORI, Nil})
			EndIf
			IF !Empty((cAliasF)->D1_SERIORI)
				aadd(a103LItem,{	"D1_SERIORI"	, (cAliasF)->D1_SERIORI, Nil})
			EndIf
			IF !Empty((cAliasF)->D1_ITEMORI)
				aadd(a103LItem,{	"D1_ITEMORI"	, (cAliasF)->D1_ITEMORI, Nil})
			EndIf

			IF !Empty((cAliasF)->D1_VALIPI)
				aadd(a103LItem,{	"D1_VALIPI"		, (cAliasF)->D1_VALIPI, Nil})
			EndIf

			IF !Empty((cAliasF)->D1_VALICM)
				aadd(a103LItem,{	"D1_VALICM"		, (cAliasF)->D1_VALICM, Nil})
			EndIf

			IF !Empty((cAliasF)->D1_PEDIDO)
				aadd(a103LItem,{	"D1_PEDIDO"		, (cAliasF)->D1_PEDIDO, Nil})
			EndIf
			IF !Empty((cAliasF)->D1_ITEMPC)
				aadd(a103LItem,{	"D1_ITEMPC"		, (cAliasF)->D1_ITEMPC, Nil})
			EndIf
			aadd(a103Item,a103LItem)

			(cAliasF)->(dbSkip())
		EndDo

		lMsErroAuto := .F.
		BeginTran()

		//pre-nota
		If cOperac == "1"
			If IsBlind()
				MsExecAuto({|x,y,z| Mata140(x,y,z)},a103Cab,a103Item,3)
			Else
				//MostraTela := 0 // 0 - Nao mostra tela 1 - Mostra tela e valida tudo 2 - Mostra tela e valida so cabecalho
				FWMsgRun( ,{|| Mata140(a103Cab,a103Item,3,nil,1)},"Processando...")
			EndIF

			//Nota
		ElseIf cOperac == "2"
			If IsBlind()
				MSExecAuto({|x,y| mata103(x,y)},a103Cab,a103Item)
			Else
				FWMsgRun( ,{|| Mata103( a103Cab, a103Item , 3 , .T.)},"Processando...")
			EndIf
		EndIf

		If lMsErroAuto
			DisarmTransaction()
			MostraErro()
			Break
		EndIf

		//(cAliasF)->(dbGoTop())
		//dbSelectArea("SF1")
		//dbSetOrder(1)
		//F1_DOC, F1_SERIE, F1_FORNECE, F1_LOJA, F1_TIPO
		//If !dbSeek(FWXFilial("SF2")+(cAliasF)->F1_DOC+(cAliasF)->F1_SERIE+(cAliasF)->F1_FORNECE+(cAliasF)->F1_LOJA+(cAliasF)->F1_TIPO)
		//	DisarmTransaction()
		//	Break
		//EndIf

		//Atualiza amarracao produto x fornecedor
		(cAliasF)->(dbGoTop())
		While (cAliasF)->(!Eof())

			AtuSA5XSA2((cAliasF)->F1_FORNECE,(cAliasF)->F1_LOJA,(cAliasF)->D1_COD,(cAliasF)->A5_CODPRF,(cAliasF)->A5_DESCPRF)

			(cAliasF)->(dbSkip())
		EndDo

		EndTran()
		cMsgInf	:=	"Nota Importada com Sucesso!"
		Aviso("Atenção - "+Procname()/*cCaption*/, cMsgInf/*cMensagem*/,{"OK"}/*aBotoes*/,3,/*cCaption2*/,/*nRotAutDefault*/,/*cBitmap*/,.T./*lEdit*/,12200/*nTimer*/,1/*nOpcPadrao*/)

		lRet	:=	.T.

	End Sequence

	RestArea(aSaveArea)
	RestArea(aSaveCL)

	//If !lRet .AND. Type("oBrowseNFE")<>"U"
	//	(cAliasF)->(dbGoTop())
	//	oBrowseNFE:Refresh(.T.)
	//EndIf


Return lRet


/*/{Protheus.doc} XMLTrb

Cria arquivo de trabalho

@author charlesT
@since 02/05/2017
@version undefined
@param aCamposGet, array, descricao
@param aDados, array, descricao
@param aIpi, array, descricao
@param aICMS, array, descricao
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function XMLTrb()
	Local aFields 		:= {}
	Local oTempTable
	Local nI
	Local cQuery
	Local aCamposGet	:=	{}
	Local aColunas		:=	{}
	Local cFileTab	:=	GetNextAlias()//CriaTrab(,.F.)
	Local nIX
	//Local cAlias	:=	GetNextAlias()
	//[1] Nome do campo
	//[2] Indica se pode editar
	//[3] Funcao de validação
	//[4] Indica se mostra no browse

	aadd(aCamposGet,{"F1_TIPO",.T.,'fSetTipo()',.T.})
	aadd(aCamposGet,{"F1_FORMUL",.F.,'',.F.})
	aadd(aCamposGet,{"F1_DOC",.F.,'',.F.})
	aadd(aCamposGet,{"F1_SERIE",.F.,'',.F.})
	aadd(aCamposGet,{"F1_EMISSAO",.F.,'',.F.})
	aadd(aCamposGet,{"F1_FORNECE",.F.,'',.F.})
	aadd(aCamposGet,{"F1_LOJA",.F.,'',.F.})
	aadd(aCamposGet,{"A2_NOME",.F.,'',.F.})
	aadd(aCamposGet,{"A2_CGC",.F.,'',.F.})
	aadd(aCamposGet,{"F1_COND",.T.,'',.T.})
	aadd(aCamposGet,{"E2_NATUREZ",.T.,'',.T. })
	aadd(aCamposGet,{"D1_ITEM",.F.,'',.T. })
	aadd(aCamposGet,{"D1_COD",.T.,"ExistCpo('SB1') ",.T. })
	aadd(aCamposGet,{"D1_PEDIDO",.T.,"If(Empty(M->D1_PEDIDO),.T.,ExistCpo('SC7',M->D1_PEDIDO))",.T.})
	aadd(aCamposGet,{"D1_ITEMPC",.T.,'',.T.})
	aadd(aCamposGet,{"A5_CODPRF",.F.,'',.T.})
	aadd(aCamposGet,{"A5_DESCPRF",.F.,'',.T.})
	aadd(aCamposGet,{"D1_TES",.T.,"ExistCpo('SF4')",.T.})
	//aadd(aCamposGet,{"B1_DESC",.F.,'',.T.})
	aadd(aCamposGet,{"D1_QUANT",.F.,'',.T.})
	aadd(aCamposGet,{"D1_VUNIT",.F.,'',.T.})
	aadd(aCamposGet,{"D1_SEGUM",.F.,'',.T.}) // Diego Kerstner
	aadd(aCamposGet,{"D1_TOTAL",.F.,'',.T.})
	aadd(aCamposGet,{"B1_POSIPI",.F.,'',.T.})
	aadd(aCamposGet,{"D1_VALIPI",.F.,'',.T.})
	aadd(aCamposGet,{"D1_VALICM",.F.,'',.T.})
	aadd(aCamposGet,{"F1_CHVNFE",.F.,'',.F.})
	aadd(aCamposGet,{"F1_MENNOTA",.F.,'',.F.})
	aadd(aCamposGet,{"F1_TPFRETE",.T.,'',.T.})
	aadd(aCamposGet,{"F1_PLACA",.F.,'',.T.})
	aadd(aCamposGet,{"F1_PBRUTO",.F.,'',.T.})
	aadd(aCamposGet,{"F1_PLIQUI",.F.,'',.T.})

	aadd(aCamposGet,{"F1_DESCONT",.F.,'',.F.})
	aadd(aCamposGet,{"F1_DESPESA",.F.,'',.F.})
	aadd(aCamposGet,{"F1_SEGURO",.F.,'',.F.})
	aadd(aCamposGet,{"F1_FRETE",.F.,'',.F.})
	aadd(aCamposGet,{"F1_BASEICM",.F.,'',.F.})
	aadd(aCamposGet,{"F1_VALICM",.F.,'',.F.})
	aadd(aCamposGet,{"F1_VALIPI",.F.,'',.F.})
	aadd(aCamposGet,{"F1_BASEIPI",.F.,'',.F.})
	aadd(aCamposGet,{"F1_BRICMS",.F.,'',.F.})
	aadd(aCamposGet,{"F1_ICMSRET",.F.,'',.F.})
	aadd(aCamposGet,{"D1_NFORI",.T.,'',.T.})
	aadd(aCamposGet,{"D1_SERIORI",.T.,'',.T.})
	aadd(aCamposGet,{"D1_ITEMORI",.T.,'',.T.})
	//aadd(aCamposGet,{"D1_CONTA",.T.,{|| .T.}})
	//aadd(aCamposGet,{"D1_CC",.T.,{|| .T.}})
	//aadd(aCamposGet,{"D1_CLVL",.T.,{|| .T.}})
	//aadd(aCamposGet,{"D1_ITEMCTA",.T.,{|| .T.}})
	//aadd(aCamposGet,{"D1_NATUREZ",.T.,{|| .T.}})
	aadd(aCamposGet,{"F1_ESPECIE",.F.,'',.F.})
	aadd(aCamposGet,{"D1_OP",.T.,'',.F.})


	SX3->(dbSetOrder(2))
	For nIX	:=1 to Len(aCamposGet)
		If SX3->(msSeek(aCamposGet[nIX][1]))

			aadd(aFields,{SX3->X3_CAMPO,SX3->X3_TIPO,SX3->X3_TAMANHO,SX3->X3_DECIMAL})
			If aCamposGet[nIX][4]
				oColumn	:=	FWBrwColumn():New()
				oColumn:SetData( &("{||"+cFileTab+"->"+alltrim(SX3->X3_CAMPO)+" }") )
				oColumn:SetType( 	SX3->X3_TIPO)
				oColumn:SetTitle( 	SX3->X3_TITULO)
				oColumn:SetSize(	SX3->X3_TAMANHO)
				oColumn:SetDecimal(	SX3->X3_DECIMAL)
				oColumn:SetPicture( SX3->X3_PICTURE)
				oColumn:SETAUTOSIZE(.T.)
				If aCamposGet[nIX][2]
					oColumn:SetEdit(.T.)
					//oColumn:SetValid({|| alert("oi"),.T.} )
					//oColumn:SetValid( &("{||" +aCamposGet[nIX][3]+"}") )
					If !Empty(aCamposGet[nIX][3])
						oColumn:SetValid( &("{|oObj,oObj2| "+aCamposGet[nIX][3]+".AND.A046VlCell(oObj,oObj2)}")  )
					Else
						oColumn:SetValid( {|oObj,oObj2| A046VlCell(oObj,oObj2)}  )
					EndIf
					oColumn:SetReadVar("M->"+Alltrim(SX3->X3_CAMPO))
					//oColumn:SetReadVar(Alltrim(SX3->X3_CAMPO))
				EndIf
				//oColumn:SetComment("tete")
				If !Empty(SX3->X3_F3)
					oColumn:SetF3(SX3->X3_F3)
				EndIf
				aadd(aColunas,oColumn)
				oColumn	:=	nil
			EndIf
		EndIf
	Next


	//dbCreate(cFileTab,aFields,"SQLITE_MEM")
	//DBUseArea(.T., 'SQLITE_MEM', cFileTab, (cFileTab), .F., .F.)

	oTempTable := FWTemporaryTable():New( cFileTab )
	oTemptable:SetFields( aFields )
	oTempTable:Create()

Return {cFileTab,aCamposGet,aColunas,oTempTable}
//Return {cAlias,aCamposGet,aColunas,oTempTable}


/*/{Protheus.doc} A046VlCell

Valida célula editada e grava no arquivo temporário

@author charlesT
@since 03/05/2017
@version undefined
@param oObj, object, descricao
@param oObj2, object, descricao
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static function A046VlCell(oObj,oObj2)
	Local cField	:=	StrTran(oObj2:GetColumn():cReadVar,"M->","")
	Local aAreaS
	Local cAliasR	:=	oObj2:Alias()
	Local xValor	:=	&(oObj2:GetColumn():cReadVar)

	If "F1_"$Alltrim(cField) .OR. "E2_"$Alltrim(cField)
		aAreaS	:=	GetArea()
		(cAliasR)->(dbGoTop())

		While (cAliasR)->(!Eof())

			(cAliasR)->(RecLock(cAliasR,.F.))
			&((cAliasR)+"->"+cField)	:=	xValor
			(cAliasR)->(msUnlock())
			(cAliasR)->(dbSkip())

		EndDo
		RestARea(aAreaS)
		oBrowseNFE:Refresh(.T.)
	Else
		//_SetOwnerPrvt("M->"+oObj2:GetColumn():cReadVar,&(oObj2:GetColumn():cReadVar))
		(cAliasR)->(RecLock(cAliasR,.F.))
		&((cAliasR)+"->"+cField)	:=	&(oObj2:GetColumn():cReadVar)
		(cAliasR)->(msUnlock())
	EndIf


Return .T.

/*/{Protheus.doc} A046TdOk

Rotina responsavel por validar importação do XML

@author charlesT
@since 02/05/2017
@version undefined

@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function A046TdOk()
	Local lRet	:=	.F.

	Begin Sequence
		//Alert("OK")
		lRet	:=	.T.

	End Sequence

Return lREt


/*/{Protheus.doc} MontaXmlManif

Monta Manifesto

@author charlesT
@since 03/05/2017
@version undefined
@param cCbCpo, characters, descricao
@param aMontXml, array, descricao
@param cRetorno, characters, descricao
@param cJustific, characters, descricao
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function GerXmlManif(cCbCpo,cChaveNFE,cRetorno,cJustific)
	Local aRet			:={}
	Local cAmbiente		:= ""
	Local cXml			:= ""
	Local cTpEvento		:=  SubStr(cCbCpo,1,6)
	Local cIdEnt		:= RetIdEnti()
	Local cURL			:= PadR(GetNewPar("MV_SPEDURL","http://"),250)
	Local cChavesMsg	:= ""
	Local cMsgManif		:= ""
	Local lRetOk		:= .F.
	Local nX 			:= 0
	Local nZ 			:= 0
	Local oWs			:= Nil
	Default cJustific 	:= ""
	Private lUsaColab		:= UsaColaboracao("4")

	Begin Sequence

		If !RetRdTSS()
			Aviso(procname(),"Execute o módulo de configuração do serviço, antes de utilizar esta opção!!!",{"OK"},3) //"Execute o módulo de configuração do serviço, antes de utilizar esta opção!!!"
			Break
		EndIf

		//Atualiza o status na rotina de manifestacao padrao
		dbSelectArea("C00")
		C00->(DbSetOrder(1))
		If C00->(!DBSEEK(xFilial("C00")+Alltrim(cChaveNFE)))
			MsgStop("Falha ao localizar a manifestação (C00)","Atenção - "+ProcName())
			Break
		EndIf
		nRecNOC00	:=	C00->(RecNo())
		oWs :=WSMANIFESTACAODESTINATARIO():New()
		oWs:cUserToken   	:= "TOTVS"
		oWs:cIDENT	     	:= cIdEnt
		oWs:cAMBIENTE	 	:= ""
		oWs:cVERSAO      	:= ""
		oWs:_URL         	:= AllTrim(cURL)+"/MANIFESTACAODESTINATARIO.apw"

		If !oWs:CONFIGURARPARAMETROS()
			MsgStop(IIf(Empty(GetWscError(3)),GetWscError(1),GetWscError(3)),"Atenção - "+ProcName())
			Break
		EndIf
		cAmbiente		 := oWs:OWSCONFIGURARPARAMETROSRESULT:CAMBIENTE

		cXml:=	""
		cXml+='<envEvento>'
		cXml+='<eventos>'
		cXml+='<detEvento>'
		cXml+='<tpEvento>'+cTpEvento+'</tpEvento>'
		cXml+='<chNFe>'+Alltrim(cChaveNFE)+'</chNFe>'
		cXml+='<ambiente>'+cAmbiente+'</ambiente>'
		//If '210240' $ cTpEvento .and. !Empty(cJustific)
		//	cXml+='<xJust>'+Alltrim(cJustific)+'</xJust>'
		//EndIf
		cXml+='</detEvento>'
		cXml+='</eventos>'
		cXml+='</envEvento>'

		oWs:= WsNFeSBra():New()
		oWs:cUserToken	:= "TOTVS"
		oWs:cID_ENT		:= cIdEnt
		oWs:cXML_LOTE	:= cXml
		oWS:_URL		:= AllTrim(cURL)+"/NFeSBRA.apw"

		If !oWs:RemessaEvento()
			MsgStop(IIf(Empty(GetWscError(3)),GetWscError(1),GetWscError(3)),"Atenção - "+ProcName())
			Break
		EndIf

		If Type("oWS:oWsRemessaEventoResult:cString") <> "U"
			If Type("oWS:oWsRemessaEventoResult:cString") <> "A"
				aRetorno:={oWS:oWsRemessaEventoResult:cString}
			Else
				aRetorno:=oWS:oWsRemessaEventoResult:cString
			EndIf
		EndIf

		dbSelectArea("C00")
		C00->(RecLock("C00"),.F.)
		C00->C00_STATUS := "1" //Confirmacao de operacao
		C00->C00_CODEVE := "2"
		C00->(MsUnlock())

		//ENVIADO MANIFESTACAO
		//C00_STATUS = 1
		//C00_SITDOC = 1
		//C00_CODEVE = 2
		//APOS MONITOR
		//C00_CODEVE = 3
		//Monitor altera os campos

		cMsgManif := "Transmissão da Manifestação concluída com sucesso!"+ Chr(10) + Chr(13)//"Transmissão da Manifestação concluída com sucesso!"
		cMsgManif += cCbCpo + Chr(10) + Chr(13)
		cMsgManif += "Chave(s): "+ Chr(10) + Chr(13)
		cMsgManif += cChaveNFE

		//Chama rotina para fazer o omonitoramento e pegar o resultado do sefaz.
		FWMsgRun( ,{|| lRetOk	:=	ManiMonSl(cChaveNFE,cAmbiente,cIdEnt,cURL,nRecNOC00)},"Aguardando autorização SEFAZ...")

		If !lRetOk
			Break
		EndIf

		//sleep(20000) //espera  30 segundos para o sefaz atualizar e liberar o download


		lRetOk	:=	.T.

	End Sequence

Return lRetOk


/*/{Protheus.doc} AtuSA5XSA2

Atualiza SA5 - Amarracao Prod X Fornecedor

@author Administrador
@since 17/05/2017
@version undefined

@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function AtuSA5XSA2(cFornece,cLoja,cProduto,cProdCodF,cProdDesF)
	Local aAreaSa5   	:= SA5->(GetArea())
	Local aAreaSx3    	:= SX3->(GetArea())
	Local lAtuRec		:=	 nil

	dbSelectArea("SA5")
	dbSetOrder(1)
	lAtuRec := !MsSeek(xFilial("SA5")+cFornece+cLoja+cProduto,.F.)


	RecLock("SA5", lAtuRec)

	// Grava os inicializadores padroes dos demais campos.
	SX3->(DbSetOrder(1)) // Indice 1 - X3_ARQUIVO+X3_ORDEM
	If SX3->(DbSeek('SA5'))

		While SX3->(!EOF()) .And. SX3->X3_ARQUIVO == 'SA5'

			If SX3->X3_CONTEXT <> "V" // Retira os campos virtuais.

				SA5->&(SX3->X3_CAMPO) := CriaVar(SX3->X3_CAMPO, .T.)

			EndIf

			SX3->(DbSkip())

		EndDo

	EndIf

	SA5->A5_FILIAL  := fwxFilial("SA5")
	SA5->A5_FORNECE := cFornece
	SA5->A5_LOJA    := cLoja
	SA5->A5_NOMEFOR := Posicione("SA2",1,xFilial("SA2")+cFornece+cLoja,"A2_NOME")
	SA5->A5_PRODUTO := cProduto
	SA5->A5_NOMPROD := Posicione("SB1",1,xFilial("SB1")+cProduto,"B1_DESC")
	SA5->A5_CODPRF 	:= cProdCodF
	SA5->A5_DESCPRF := cProdDesF
	SA5->(MsUnlock())

	RestArea(aAreaSa5)
	RestArea(aAreaSx3)
Return nil

/*/{Protheus.doc} AtuSA5XSA2

Monitora autorizacao do sefaz,
C00 precisa estar posicioanada

@author charlesT
@since 19/05/2017
@version undefined
@param cFornece, characters, description
@param cLoja, characters, description
@param cProduto, characters, description
@param cProdCodF, characters, description
@param cProdDesF, characters, description
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function ManiMonSl(cChaveNFE,cAmbiente,cIdEnt,cURL,nRecNoC00)
	Local lRet		:=	.F.
	Local nTimeWait	:=	2000
	Local nQtdTent	:=	10
	Begin Sequence

		C00->(dbGoTo(nRecNoC00))


		For nIO := 1 To nQtdTent
			Sleep(nTimeWait)
			//MonitoraManif({cChaveNFE}, cAmbiente, cIdEnt, GetNewPar("MV_SPEDURL","http://")+"/MANIFESTACAODESTINATARIO.apw")
			MonitoraManif({cChaveNFE}, cAmbiente, cIdEnt, GetNewPar("MV_SPEDURL","http://")+"/MANIFESTACAODESTINATARIO.apw")
			C00->(dbGoTo(nRecNoC00))
			If C00->C00_STATUS=='1' .and. alltrim(C00->C00_CODEVE)=='3' .AND. alltrim(C00->C00_SITDOC) = '1'
				Sleep(2000)
				Exit
			EndIf

			//Caso chego ao seu limite, sai sem finalizar
			If nIO == nQtdTent
				MsgStop("Não conseguimos recuperar o retorno do sefaz, efetue o processo de monitor do Manifesto do Destinatário e tente novamente.","Atenção - "+Procname())
				Break
			EndIf

		Next

		lRet	:=	.T.
	End Sequence


Return lRet



/*/{Protheus.doc} ValidEMp()
Valida empresas

@author -
@since -
@version 1.00

@Return lRetOk	   - Se autorizado
/*/
Static Function ValidEMp()
	Local aEmpAut	:=	{}
	Local lEmpOK	:= .F.

	//Empresa 99 não precisa validar
	If SM0->M0_CODIGO == "99"
		Return .T.
	EndIf

	//Lista de empresas autorizadas
	aadd(aEmpAut,"04200829000199") //Grupo Weko America Latina               - WEKO AMERICA LATINA EQUIP. INDUSTRIAIS LTDA                 - Indaial
	aadd(aEmpAut,"02255187000108") //TPA TELECOMUNICACAO
	aadd(aEmpAut,"85121820000194") //SELGRON
	aadd(aEmpAut,"85400547000137") //TEXTIL RIO DOS CEDROS
	aadd(aEmpAut,"73954489000104") //ALUMETAF
	aadd(aEmpAut,"78994456000101") //CALWER
	aadd(aEmpAut,"12344954000109") //CALWER
	aadd(aEmpAut,"01379126000181") //DELPI - Solicitado Diego Kerstner - 25/10/2018

	For nI := 1 To Len(aEmpAut)
		If SubString(Alltrim(aEmpAut[nI]),1,8)	== SubString(Alltrim(SM0->M0_CGC),1,8)
			lEmpOK	:=	.T.
			Exit
		EndIf
	Next

	If !lEmpOK
		MsgStop("Rotina customizada, empresa não autorizada para utilizar importação. Entre em contato com a TOTVS SC.","Atenção - "+ProcName())
	EndIf

Return lEmpOK


Static FUnction fSetTipo()

	Local xTipo := &(readvar())
	Local cCGCCli := (aTRBInfo[1])->A2_CGC
	IF xTipo == "B"
		//21,2
		// Busco o Cliente pelo CNPJ.
		dbSelectArea("SA1")
		SA1->(dbSetOrder(3))
		If !SA1->(dbSeek(xFilial("SA2")+cCGCCli))

			MsgStop("Cliente não localizado pelo CNPJ: " +cCgcFor,"Atenção - "+ProcName())

		ELSE
			cArqClifor := "SA1"
			cAchoCli   :=  SA1->A1_COD
			cAchoLoja   :=  SA1->A1_LOJA
			lAchoCli := CliForOrig(cArqClifor, @cAchoCli, @cAchoLoja)

			(aTRBInfo[1])->(RecLock(aTRBInfo[1],.F.))
			(aTRBInfo[1])->F1_FORNECE := cAchoCli
			(aTRBInfo[1])->F1_LOJA := cAchoLoja

			(aTRBInfo[1])->(msUnlock())
		EndIf
	EndIf
RETURN .T.



Static Function fValidNF()
	Local lRet 			:= .t.
	Local aSaveArea		:=	GetArea()
	Local aSaveCL		:=	(cAliasF)->(GetArea())
	Local cAltPrcCtr    := GetMV("MV_ALTPRCC")

	(cAliasF)->(dbGoTop())
	While (cAliasF)->(!Eof())


		IF !Empty((cAliasF)->D1_PEDIDO)
			aadd(a103LItem,{	"D1_PEDIDO"		, (cAliasF)->D1_PEDIDO, Nil})
		EndIf
		IF !Empty((cAliasF)->D1_ITEMPC)
			aadd(a103LItem,{	"D1_ITEMPC"		, (cAliasF)->D1_ITEMPC, Nil})
		EndIf
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica se o preco digitado esta divergente do PC ou da AE.    ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If  !Empty((cAliasF)->D1_PEDIDO) .And.  !Empty((cAliasF)->D1_ITEMPC) .And.  (cAliasF)->D1_VUNIT > 0 .And.;
				lRet .And. cAltPrcCtr <> "0" .And. !Empty(aCols[n][nPosPc]) .And. !Empty(aCols[n][nPosItemPC]) .And. !lVldAfter

			SC7->(DbSetOrder(1))
			If SC7->(MsSeek(xFilial("SC7")+(cAliasF)->D1_PEDIDO+(cAliasF)->D1_ITEMPC))
				nPreco := xMoeda(SC7->C7_PRECO,SC7->C7_MOEDA,1,M->dDEmissao,TamSX3("D1_VUNIT")[2],SC7->C7_TXMOEDA)
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Se a NF for do SIGAEIC, a comparação entre a NF e o Pedido de Compra, não tenha efeito    ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

				If (cAltPrcCtr == "1" .And. SC7->C7_TIPO == 1) .Or.;
						(cAltPrcCtr == "2" .And. SC7->C7_TIPO == 2) .Or.;
						(cAltPrcCtr == "5" .And. SC7->C7_TIPO == 2) .Or.;
						cAltPrcCtr $ "3#6"

					If NoRound((cAliasF)->D1_VUNIT,TamSX3("D1_VUNIT")[2]) <> nPreco

						cTitulo := "Atenção"
						cMsg    := "Preço informado divergente do Pedido de Compras. Verifique o conteúdo do parâmetro MV_ALTPREC"
						aOK     := {"OK"}

						Aviso(cTitulo,cMsg,aOK,2)
						lRet := .F.

					Endif
				Endif

			Endif
		Endif
		(cAliasF)->(dbSkip())
	EndDo

	RestArea(aSaveArea)
	RestArea(aSaveCL)

Return lRet



Static Function MonitEven(cChvIni,cChvFin,cCodEve,cModelo,cChaves,lUsaColab)

	Local aListBox		:= {}

	Local oOk			:= LoadBitMap(GetResources(), "ENABLE")
	Local oNo			:= LoadBitMap(GetResources(), "DISABLE")

	Local cURL   		:= PadR(GetNewPar("MV_SPEDURL","http://"),250)
	Local cOpcUpd		:= ""
	Local cIdEnt		:= RetIdEnti(lUsaColab)

	Local nX			:= 0

	Local lOk      		:= .T.

	Private oXmlCCe
	Private oDados
	Private oWS			:= Nil

	Default cModelo 	:= ""
	Default cChaves	    := ""

	If RetRdTSS()

		// Executa o metodo NfeRetornaEvento()
		oWS:= WSNFeSBRA():New()
		oWS:cUSERTOKEN	:= "TOTVS"
		oWS:cID_ENT		:= cIdEnt
		oWS:_URL			:= AllTrim(cURL)+"/NFeSBRA.apw"
		oWS:cEVENTO		:= cCodEve
		oWS:cCHVINICIAL	:= cChvIni
		oWS:cCHVFINAL		:= cChvFin
		oWS:cCHAVES		:= cChaves
		lOk:=oWS:NFEMONITORLOTEEVENTO()

		If lOk

			// Tratamento do retorno do evento
			If Type("oWS:oWsNfemonitorLoteEventoResult:OWSNfeMonitorEvento") <> "U"

				If Valtype(oWS:oWsNfemonitorLoteEventoResult:OWSNfeMonitorEvento) <> "A"
					aMonitor := {oWS:oWsNfemonitorLoteEventoResult:OWSNfeMonitorEvento}
				Else
					aMonitor := oWS:oWsNfemonitorLoteEventoResult:OWSNfeMonitorEvento
				EndIF

				conout("trava nfe")

				/*	For nX:=1 To Len(aMonitor)
					AADD( aListBox, {	If(aMonitor[nX]:nStatus <> 6 .And. aMonitor[nX]:nStatus <> 7 ,oNo,oOk),;
						If(aMonitor[nX]:nProtocolo <> 0 ,Alltrim(Str(aMonitor[nX]:nProtocolo)),""),;
						aMonitor[nX]:cId_Evento,;
						Alltrim(Str(aMonitor[nX]:nAmbiente)),;
						Alltrim(Str(aMonitor[nX]:nStatus)),;
						If(!Empty(aMonitor[nX]:cCMotEven),Alltrim(aMonitor[nX]:cCMotEven),Alltrim(aMonitor[nX]:cMensagem)),;
						"" }) //XML manter devido ao TOTVS Colaboração.
					//Atualizacao do Status do registro de saida
					cOpcUpd := "3"

					If aListBox[nX][5]	== "3" .Or. aListBox[nX][5] == "5"
						cOpcUpd :=	"4"  //Evento rejeitado +msg rejeiçao
					ElseIf aListBox[nX][5] == "6"
						cOpcUpd := "3"  //Evento vinculado com sucesso
					ElseIf aListBox[nX][5] == "1"
						cOpcUpd := "2"  //Envio de Evento realizado - Aguardando processamento
					EndIF

					cChave:= Substr(aMonitor[nX]:cId_Evento,9,44)

					AtuCodeEve( cChave, cOpcUpd, cCodEve, cModelo, aListBox[nX][4], cIdEnt, cUrl )

				Next*/

			EndIF

		EndIf

	Else
		Aviso("Atenção - "+ProcName(),"Execute o módulo de configuração do serviço, antes de utilizar esta opção",{"OK"},3)	//"Execute o módulo de configuração do serviço, antes de utilizar esta opção!!!"

	EndIf

Return aListBox
