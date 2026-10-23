#INCLUDE 'Protheus.ch' 
#INCLUDE 'MATA140I.ch'       
#INCLUDE 'TOPConn.ch'
#INCLUDE "FWMVCDEF.CH"         
#INCLUDE "FWCOMMAND.CH"         
#INCLUDE "FILEIO.CH" 
     
/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ImpXML_NFeºAutor  ³Demetrio Fontes 	 º Data ³  14/03/11   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Funcao para leitura de XMLs de NFe no diretorio de downloadº±±
±±º			 ³ e geracao da pre-nota de entrada.						  º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ GENERICO			                                          º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function ImpXML_NFe(cFile,lJob,aProc,aErros,lNFeTransp,oFullXML,lNfeCompl,cXmlOri,aErroERP) 
Local cXML       := ""
Local cError     := ""
Local cWarning   := ""
Local cCGC	     := ""
Local cTipoNF    := ""
Local cTabEmit   := ""
Local cDoc	     := ""
Local cSerie     := ""
Local cCodigo    := ""
Local cLoja	     := ""
Local cNomeFor   := ""
Local cCampo1    := ""
Local cCampo2    := ""
Local cCampo3    := ""
Local cCampo4    := ""
Local cCampo5    := ""
Local cQuery     := ""
Local cTpNfPE 	 := ""
Local cLote		 := ""
Local cPedido	 := Space(TamSx3("DT_PEDIDO")[1])
Local cItemPed	 := Space(TamSx3("DT_ITEMPC")[1])
Local cNFECFAP   := SuperGetMV("MV_XMLCFPC",.F.,"")
Local cNFECFBN   := SuperGetMV("MV_XMLCFBN",.F.,"")
Local cNFECFDV   := SuperGetMV("MV_XMLCFDV",.F.,"")
Local cNFECFND   := SuperGetMV("MV_XMLCFND",.F.,"")
Local cNFECFNO   := SuperGetMV("MV_XMLCFNO",.F.,"")
Local cCFOP      :='N'
Local lA140ICFOP := ExistBlock("A140ICFOP")
Local lFound     := .F.
Local lProces    := .T.
Local nX		 := 0
Local nY		 := 0
Local nI		 := 0
Local nZ         := 0			
Local oAuxXML    := NIL
Local oXML	     := NIL
Local aItens     := {}
Local aHeadSDS   := {}
Local aItemSDT   := {}
Local cProduto	 := ""
Local lMensExib  := .F.
Local nQuant	 := 0
Local nPrecUni	 := 0
Local cCNPJTran  := ""
Local cCodTransp := ""
Local cPlacaTran := ""
Local nPesoLiq   := 0
Local nPesoBruto := 0
Local cTipoFrete := ""
Local aQtdVol	 := {} 
Local aEspVol	 := {} 
Local nFilImp	 := 0
Local cFciCod	 := ""
Local nTamFci	 := TamSx3("DT_FCICOD")[1]
Local dValidLote := StoD("")
Local cCodCFOP	:= ""
Local cMotivo	:= ""
Local cChaveNFe	:= ""
Local ncStat	:= 0
Local aA140IDOC := {}
Local nTotItem  := 0
Local nDescRast := 0
Local nFretRast	:= 0
Local nSeguRast := 0
Local nDespRast := 0

//IMPOSTOS dos itens
Local nIPIItem  := 0 
Local nICMItem  := 0
Local nISSItem  := 0    
Local nPISItem  := 0
Local nCOFItem  := 0
Local nIMCSTIt 	:= 0
Local nAlIPIItem  := 0
Local nAlICMItem  := 0
Local nAlISSItem  := 0    
Local nAlPISItem  := 0
Local nALCOFItem  := 0
Local nALIMCSTIt  := 0

//FCP Ant
Local nBCFCPSTRet := 0
Local nPFCPSTRet  := 0
Local nVFCPSTRet  := 0

//FCP ST
Local nBCFCPST := 0
Local nPFCPST  := 0
Local nVFCPST  := 0

//ICMS ST Ret
Local nVICMSSTRet	:= 0
Local nBICMSSTRet	:= 0
Local nAICMSSTRet	:= 0

//Variáveis SIGATMS
Local cCGCDes	 	 := ""
Local cQueryDUL	 := ""
Local lIncluiDUL	 := .T.
Local cInsc	 	 	 := ""
Local cInsDes	 	 := ""
Local cSeqEnd	 	 := ""
Local cAliasDUL	 := "" 
Local cChvNfe		 := "" 
Local cDetalhe		 := ""
Local nNumDet		 := 0
Local cPulaLinha	 := CHR(13) + CHR(10)
Local aSm0			 := FWLoadSM0()
Local aProdutos	 := {}       
Local cUmNfe		 := ''
Local lAchouForn	:= .F.
Local aDirFilial	:= {}
Local nQCNPJ	:= 0
Local nQINSC	:= 0
Local a140VPed	:= {}
Local a140PedAux	:= {}
Local a140Rastro	:= {}
Local nQtdRastro	:= 0
Local nTotICMDeson	:= 0
Local nTotIPI := 0 //IPI
Local nTotICM := 0 //ICMS
Local nTotISS := 0 //ISS
Local nTotPIS := 0 //PIS
Local nTotCOF := 0 //COFINS
Local nTotCST := 0 //ICMS ST
Local nTotFCPB := 0 //Base FCP
Local nTotFCPV := 0 //Valor FCP
Local nTotBFCPST := 0 //Base FCP ST
Local nTotVFCPST := 0 //Valor FCP ST
Local nTotBICSTRET := 0 //Base ICMS ST Ret
Local nTotVICSTRET := 0 //Valor ICMS ST Ret
Local nQtdVPed	:= 0
Local nPos140Ped	:= 0
Local l140VPed	:= .F.
Local cNFOriComp	:= ""
Local cSerOriComp	:= ""
Local cItOriComp	:= ""
Local cChvNFComp	:= ""
Local lSemCad		:= .F.
Local lValQtd		:= .T.
Local lSemIE		:= .F.
Local cHrEmis		:= ""
Local cCGCTransp	:= ""
Local lFCPAnt		:= SDT->(FieldPos("DT_XBFCPAN")) > 0 .And. SDT->(FieldPos("DT_XAFCPAN")) > 0 .And. SDT->(FieldPos("DT_XVFCPAN")) > 0
Local lFCPST		:= SDT->(FieldPos("DT_XBFCPST")) > 0 .And. SDT->(FieldPos("DT_XAFCPST")) > 0 .And. SDT->(FieldPos("DT_XVFCPST")) > 0
Local lICMSSTRet	:= SDT->(FieldPos("DT_ICMNDES")) > 0 .And. SDT->(FieldPos("DT_BASNDES")) > 0 .And. SDT->(FieldPos("DT_ALQNDES")) > 0
Local lUnidMed		:= SDT->(FieldPos("DT_UM")) > 0 .And. SDT->(FieldPos("DT_SEGUM")) > 0 .And. SDT->(FieldPos("DT_QTSEGUM")) > 0
Local lDTICMDeson	:= SDT->(FieldPos("DT_ICMDES")) > 0 .And. SDT->(FieldPos("DT_ICMDEMT")) > 0
Local nICMDeson		:= 0
Local cICMDesMot	:= ""
Local nQtdeIt		:= 0
Local nQtXML 		:= 0
Local cUmCom		:= ""
Local nPrcIt		:= 0
Local nTotIt		:= 0
Local cUM			:= ""
Local cSEGUM		:= ""
Local nQtSEGUM		:= 0
Local lConvUM		:= .F.
Local dFabLote		:= CtoD("//")
Local lIMPEMIT		:= SuperGetMv( "MV_IMPEMIT", .F., .F. ) //--Parametro para cadastro do Emitente via EDI
Local lA140IPRD		:= ExistBlock("A140IPRD") 
Local lA140IVPED	:= ExistBlock("A140IVPED")
Local lA140IQTD		:= ExistBlock("A140IQTD")  
Local lcgcTrans		:= SuperGetMv( "MV_CGCTRAN", .F., .F. ) //--Parâmetro para ignorar se a TAG <Transporte> da NFe, será validada junto com o CGC da transportadora no cadastro de filiais (SM0).
Local lZeroSDS		:= SuperGetMv( "MV_ZEROSDS", .F., .T. ) //--Parâmetro para completar ou não com zeros a esquerda o campo SDS->D1_DOC (SF1->F1_DOC)
Local cClasFis		:= ""
Local cOrigClas		:= ""
Local cCSTClas		:= ""
Local aClasFis		:= {}
Local nClasFis		:= 0
Local cMVClasFis	:= SuperGetMV("MV_COLCFIS",.F.,"")
Local lDTClasFis	:= SDT->(FieldPos("DT_CLASFIS")) > 0
Local cAliasTmp		:= ""
Local aA140IQTD		:= {}
Local aRefDev		:= {}
Local nA			:= {}
Local lDelRefDev	:= .F.
Local oXMLprotNFe	:= Nil
Local lConsLoja  	:= Nil 	// Considera loja na pesquisa de pedidos
Local cChvNFEIn		:= ""
Local nTotReg		:= 0
Local aRetEstrang   := {}
Local lRetIDEstran	:= FindFunction("RetIDEstrang")
Local cIDEstrang    := ""
Local nVIcmRat      := 0
Local nVIPIRat 		:= 0
Local nVISSRat 		:= 0
Local nVPISRat 		:= 0 
Local nVCOFRat 		:= 0
Local nVCSTRat 		:= 0
Local cCampox       := ""
Local nQuantConv	:= 0
Local lGrava        := .T.
Local lCsdXML 		:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. SDT->(FieldPos("DT_ITXML")) > 0 .and. SDT->(FieldPos("DT_UMXML")) > 0 .and. SDT->(FieldPos("DT_QTDXML")) > 0;
					.and. SDT->(FieldPos("DT_FATOR")) > 0 .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA");
					.and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")


Private lMsErroAuto := .F.
Private lImpXML	  := SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))

Default lJob   	  	:= .T.
Default aProc  	  	:= {}
Default aErros 	  	:= {}
Default lNFeTransp  := .F.
Default oFullXML    := NIL
Default lNfeCompl	:= .F.
Default cXmlOri		:= ""
Default aErroERP 	:= {}

//Posicionar no pergunte correto para validação se consulta loja.
Pergunte("MTA140I",.F.)
lConsLoja := (mv_par12 == 1)

If lProces
	If !Empty(cXMLOri)
		If SubStr(cXMLOri,1,1) != "<"
			nPosPesq := At("<",cXMLOri)
			cXMLOri  := SubStr(cXMLOri,nPosPesq,Len(cXMLOri))	// Remove caracteres estranhos antes da abertura da tag inicial do arquivo
		EndIf
		cXML := DecodeUTF8(cXMLOri)
		
		If Empty(cXML)
			cXML := cXMLOri
		EndIf
		
		cXML := ConvAsc(cXML) //remove acentuação
		cXML := A140IRemASC(cXML)	//remove caracteres especiais não aceitos pelo encode
		
		cXML := EncodeUtf8(cXML)
			
		If Empty(cXML)
			cXML := cXMLOri
		EndIf
	EndIf 

	//-- Nao processa conhecimentos de transporte
	If !("</NFE>" $ Upper(cXML))
		lProces 	:= .F.
	EndIf
Endif

If lProces
	oFullXML := XmlParser(cXML,"_",@cError,@cWarning)
	//-- Erro na sintaxe do XML
	If Empty(oFullXML) .Or. !Empty(cError)
		If lJob
			aAdd(aErros,{cFile,"COM001 - " + STR0101+cError,STR0102}) //"Erro de sintaxe no arquivo XML: "#"Entre em contato com o emissor do documento e comunique a ocorrência."
		Else
			Aviso(STR0082,cError,{STR0004},2,"ImpXML_NFe") //"Erro"#"OK"
		EndIf			
		aAdd(aErroErp,{cFile,"COM001"})		
		lProces := .F.
	Else			
		oXML    := oFullXML
		oAuxXML := oXML			
		//-- Resgata o no inicial da NF-e
		If	lNfeCompl
			oXML := oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE
		Else
			While !lFound
				oAuxXML := XmlChildEx(oAuxXML,"_NFE")
				If !(lFound := oAuxXML # NIL)
					For nX := 1 To XmlChildCount(oXML)
						oAuxXML  := XmlChildEx(XmlGetchild(oXML,nX),"_NFE")
						lFound := oAuxXML:_InfNfe# Nil
						If lFound
							oXML := oAuxXML
							Exit
						EndIf
					Next nX
				EndIf				
				If lFound
					oXML := oAuxXML
					Exit
				EndIf
			EndDo			
		EndIf
		
		oAuxXml := XmlChildEx(oXml,"_INFNFE")

		//Hora emissão da NF-e
		If XmlChildEx(oFullXML, "_NFEPROC") # NIL
			If XmlChildEx(oFullXML:_NFEPROC,"_PROTNFE") # NIL
				oXMLProtNFe := XmlChildEx(oFullXML:_NFEPROC:_PROTNFE,"_INFPROT")
				If XmlChildEx(oXMLProtNFe,"_DHRECBTO") # NIL
					cHrEmis := Substr(oXMLProtNFe:_DhRecbto:Text,12)
				Endif
			Elseif XmlChildEx(oAuxXml, "_IDE") # NIL .And. XmlChildEx(oAuxXml:_IDE,"_DHEMI") # NIL // XML de Devolução/Cancelamento
				cHrEmis := Substr(oAuxXml:_IDE:_DHEMI:Text,12)
				If XmlChildEx(oFullXML:_NFEPROC,"_RETCANCNFE") # NIL .And. ;
				    XmlChildEx(oFullXML:_NFEPROC:_RETCANCNFE,"_INFCANC") # NIL
					oXMLProtNFe := XmlChildEx(oFullXML:_NFEPROC:_RETCANCNFE,"_INFCANC")
				Endif
			Endif
		Endif

		If Empty(cHrEmis) 
			cChvNfe := Right(AllTrim(oXML:_InfNfe:_Id:Text),44)		
			IF !lJob
				Aviso(STR0001, STR0252 + cChvNfe ,{"OK"},2,"ImpXML_NFe") //"Tag _NFEPROC não encontrada no XML da NF-e."
			Endif
			aAdd(aErros,{cFile,"COM049 - " + STR0252 + cChvNfe, ""}) //"Tag _NFEPROC não encontrada no XML da NF-e."
			aAdd(aErroErp,{cFile,"COM049"})

			cMotivo :=  STR0252 //"Tag _NFEPROC não encontrada no XML da NF-e."
			cDetalhe  := STR0252 + cChvNfe + STR0118 + ': ' + cFile
			lProces   := .F. 
		EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Emitente				   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ				
		If XmlChildEx(oAuxXml:_EMIT,"_CNPJ") # NIL
			cCGC := oAuxXml:_EMIT:_CNPJ:TEXT
		Elseif XmlChildEx(oAuxXml:_EMIT,"_CPF") # NIL
			cCGC := oAuxXml:_EMIT:_CPF:TEXT
		EndIf	
		If XmlChildEx(oAuxXml:_EMIT,"_IE") # NIL
			cInsc := oAuxXml:_EMIT:_IE:TEXT
		EndIf
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Destinatario			   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If XmlChildEx(oAuxXml:_DEST,"_CNPJ") # NIL
			cCGCDes := oAuxXml:_DEST:_CNPJ:TEXT
		Elseif XmlChildEx(oAuxXml:_DEST,"_CPF") # NIL
			cCGCDes := oAuxXml:_DEST:_CPF:TEXT
		EndIf
		If XmlChildEx(oAuxXml:_DEST,"_IE") # NIL
			cInsDes := oAuxXml:_DEST:_IE:TEXT					
		EndIf
 		If !lNFeTransp 
			aDirFilial := DirFilial(cFile,cCGCDes,cInsDes,lJob)
			If !aDirFilial[1]
				If !aDirFilial[2]
					//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
					//³ Ponto de entrada para validar se o arquivo deve ser importado    ³
					//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
					If ExistBlock("A140IIMP")
						If !ExecBlock("A140IIMP",.F.,.F.,{oFullXML})
							lProces  := .F.
						EndIf
					Else	
						If !lJob
							If aDirFilial[3]
								Aviso(STR0082,STR0244,{STR0004},2,"ImpXML_NFe")	//"Erro"#""Este XML pertence a outra empresa/filial e não podera ser processado na empresa/filial corrente." "#"OK"
							Elseif aDirFilial[4]
								Aviso(STR0082,STR0254,{STR0004},2,"ImpXML_NFe")	//"Erro"#""Este XML não pertence a nenhuma empresa/filial e não podera ser processado." "#"OK"
							Else
								Aviso(STR0082,STR0085,{STR0004},2,"ImpXML_NFe")	//"Erro"#""Este XML pertence a outra empresa/filial e não podera ser processado na empresa/filial corrente." "#"OK"
							EndIf
						Else
							If aDirFilial[3]
								aAdd(aErros,{cFile,"COM042 - " + STR0244,Iif(lImpXML,STR0248,STR0245)}) // Existe mais de uma Empresa/Filial para este XML. // Selecione a Empresa/Filial deste XML através da rotina Reprocessar no Monitor do TOTVS Colaboração.
								aAdd(aErroErp,{cFile,"COM042"})
							ElseIf aDirFilial[4]
								aAdd(aErros,{cFile,"COM052 - " + STR0254,STR0255}) //"Este XML não pertence a nenhuma empresa/filial e não podera ser processado." //"Verificar se XML pertence a empresa"
								aAdd(aErroErp,{cFile,"COM052"})
							Else
								aAdd(aErros,{cFile,"COM002 - " + STR0085,STR0246}) // Este XML pertence a outra empresa/filial e não poderá ser processado na empresa/filial corrente. // Importe na Empresa/Filial correta.
								aAdd(aErroErp,{cFile,"COM002"})
							EndIf
						EndIf
						lProces:= .F. 
					Endif
				Else 
					aAdd(aErros,{cFile,"COM002 - " + STR0085,STR0246}) // Este XML pertence a outra empresa/filial e não poderá ser processado na empresa/filial corrente. // Importe na Empresa/Filial correta.
					aAdd(aErroErp,{cFile,"COM002"})
					lProces  := .F.
				Endif
			Endif
		Else
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¤[¿
			//³IMPORTACAO VIA TMS										³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¤[Ù
			//Se nao existe a tag TRANSPORTA nao fara a importacao e nao movera o arquivo
			cCGCTransp := ""
			If XmlChildEx(oAuxXml:_TRANSP,"_TRANSPORTA") # NIL 
				If XmlChildEx(oAuxXml:_TRANSP:_Transporta,"_CNPJ") # NIL
					cCGCTransp := oAuxXml:_TRANSP:_Transporta:_CNPJ:TEXT
				ElseIf XmlChildEx(oAuxXml:_TRANSP:_Transporta,"_CPF") # NIL
					cCGCTransp := oAuxXml:_TRANSP:_Transporta:_CPF:TEXT					
				EndIf 	                                      
				//Se o Cnpj do Transportor no XML for diferente da filial atual varremos o SM0 para saber de 
				If AllTrim(SM0->M0_CGC) <> AllTrim(cCGCTransp)
					If (nFilImp := (ASCan(aSm0,{|x| x[SM0_CGC] == cCGCTransp })) )>0
						If cEmpAnt == aSm0[nFilImp,SM0_GRPEMP]						
							cFilAnt := 	aSm0[nFilImp,SM0_CODFIL]
						Else
							If lcgcTrans
								lProces := .T.				
							Else
								lProces := .F.
							EndIf
						EndIf	   						                  
					Else
						If lcgcTrans
							lProces := .T.				
						Else
							lProces := .F.
						EndIf
					EndIf
				EndIf					
			Else
				If lcgcTrans
					lProces := .T.				
				Else
					lProces := .F.
				EndIf
			EndIf						
		Endif
	EndIf
EndIf

//Verifica se XML é Cancelado ou Rejeitado.
IF lProces .And. ValType(oXMLprotNFe) <> "U" .And. Valtype(XmlChildEx(oXMLprotNFe,"_CSTAT")) <> "U" 
	
	ncStat := VAL(AllTrim(oXMLprotNFe:_cStat:Text))
	
	IF ncStat == 101 .Or. ncStat == 151 .Or. ncStat > 200
		//Chave NF-e
		cChaveNFe	:= Right(AllTrim(oXML:_InfNfe:_Id:Text),44)
		lProces	:= .F. 
		
		//Motivo 
		IF Valtype(XmlChildEx(oXMLprotNFe,"_XMOTIVO")) <> "U"
			cMotivo := ConvASC(oXMLprotNFe:_xMotivo:Text)  
		ENDIF
	
		IF ncStat == 101 .Or. ncStat == 151 //Cancelado
			IF !lJob
				Aviso(STR0001,"NF-e cancelada: " + cChaveNFe + " - Motivo: " + cMotivo,{"OK"},2,"ImpXML_NFe")//"Erro"#"NF-e cancelada
			ENDIF
			
			aAdd(aErros,{cFile,"COM040 - NF-e cancelada: " + cChaveNFe + " - Motivo: " + cMotivo,""})
			aAdd(aErroErp,{cFile,"COM040"})				
		ELSE //Rejeitado
			IF !lJob
				Aviso(STR0001,"NF-e rejeitada: " + cChaveNFe + " - Motivo: " + cMotivo,{"OK"},2,"ImpXML_NFe")//"Erro"#"NF-e rejeitada
			ENDIF
			
			aAdd(aErros,{cFile,"COM041 - NF-e rejeitada: " + cChaveNFe + " - Motivo: " + cMotivo,""})
			aAdd(aErroErp,{cFile,"COM041"})
		ENDIF	
	ENDIF
ENDIF

If lProces
	//-- Se tag _InfNfe:_Det valida
	//-- Extrai CGC do fornecedor/cliente
	aItens := IIF(ValType(oXML:_InfNfe:_Det) == "O",{oXML:_InfNfe:_Det},oXML:_InfNfe:_Det)			
	If AllTrim(oXML:_InfNfe:_Ide:_finNFe:Text) == "1"
		cTipoNF := "N"
		
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica se a NF eh compl. de preco ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
		If Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VPROD:Text) == 0  .And.;
			(Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VICMS:Text) > 0 .Or.;
			 Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VIPI:Text)  > 0 .Or.;
			 Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VST:Text)   > 0)
			
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Move arquivo XML de Compl. de Preco ICMS/IPI  ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			aAdd(aErros,{cFile,"COM003 - " + Iif(lImpXML,STR0249,STR0199),STR0200}) //"Documento complemento de preço icms/ipi não é tratado pelo TOTVS Colaboração.#""Gere o documento complementeo de preço icms/ipi de forma manual através da rotina documento de entrada."
			aAdd(aErroErp,{cFile,"COM003"})
			lProces	:= .F.
		EndIf
		
		If lA140ICFOP		// Ponto de entrada para identificar o tipo da nota através do CFOP quando não for possível identificar através dos parâmetros MV_XMLCFPC/MV_XMLCFBN/MV_XMLCFDV
			cTpNfPE := ExecBlock("A140ICFOP",.F.,.F.,{oXML})
			If ValType(cTpNfPE) == "C" .And. cTpNfPE $ "O#B#D"
				cTipoNF := cTpNfPE
			EndIf
		Else
			//-- Valida o tipo da nf
			For nX := 1 To Len(aItens)
				If aItens[nX]:_PROD:_CFOP:TEXT $ cNFECFAP
					cTipoNF := "O"
				ElseIf aItens[nX]:_PROD:_CFOP:TEXT $ cNFECFBN
					cTipoNF := "B"
				ElseIf aItens[nX]:_PROD:_CFOP:TEXT $ cNFECFDV
					cTipoNF := "D"
				EndIf
				If cTipoNF <> "N"
					Exit
				EndIf
			Next nX
		EndIf
	ElseIf AllTrim(oXML:_InfNfe:_Ide:_finNFe:Text) == "2"
		cTipoNF := "C"
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica se a NF eh compl. de preco ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
		If Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VPROD:Text) == 0  .And.;
			(Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VICMS:Text) > 0 .Or.;
			 Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VIPI:Text)  > 0 .Or.;
			 Val(oXML:_InfNFe:_TOTAL:_ICMSTOT:_VST:Text)   > 0)
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Move arquivo XML de Compl. de Preco ICMS/IPI  ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			aAdd(aErros,{cFile,"COM003 - " + Iif(lImpXML,STR0249,STR0199),STR0200}) //"Documento complemento de preço icms/ipi não é tratado pelo TOTVS Colaboração.#""Gere o documento complementeo de preço icms/ipi de forma manual através da rotina documento de entrada."
			aAdd(aErroErp,{cFile,"COM003"})
			lProces := .F.
		EndIf
	ElseIf AllTrim(oXML:_InfNfe:_Ide:_finNFe:Text) == "3"
		aAdd(aErros,{cFile,"COM004 - " + Iif(lImpXML,STR0250,STR0201),STR0202}) //"Tipo NF-e de ajustes não será tratado pelo TOTVS Colaboração."#"Gere o documento de ajustes de forma manual através da rotina documento de entrada."
		aAdd(aErroErp,{cFile,"COM004"})
		lProces := .F.
	ElseIf AllTrim(oXML:_InfNfe:_Ide:_finNFe:Text) == "4"
		If lA140ICFOP		// Ponto de entrada para identificar o tipo da nota através do CFOP quando não for possível identificar através dos parâmetros MV_XMLCFPC/MV_XMLCFBN/MV_XMLCFDV
			cTpNfPE := ExecBlock("A140ICFOP",.F.,.F.,{oXML})
			If ValType(cTpNfPE) == "C" .And. cTpNfPE $ "N#B#D"
				cTipoNF := cTpNfPE
			EndIf
		Else
			For nX := 1 To Len(aItens)
				
				If aItens[nX]:_PROD:_CFOP:TEXT $ cNFECFNO // Tratamento para modificar o tipo da nota para N = Normal, quando TAG FINNFE = 4.
					
					cTipoNF := "N"
					
					Exit
					
				ElseIf aItens[nX]:_PROD:_CFOP:TEXT $ cNFECFBN
					
					cTipoNF := "B"
					
					Exit
					
				EndIf
				
			Next nX
			
			If Empty(cTipoNF)
				cTipoNF := "D"
			Endif
		Endif
	EndIf

	//-- Verifica se este ID ja foi processado	
	If !lNFeTransp
		DbSelectArea("SDS")
		SDS->(DbSetOrder(2))
		lFound := SDS->(DbSeek(xFilial("SDS")+Right(AllTrim(oXML:_InfNfe:_Id:Text),44)))//Filial + Chave de acesso
	Else
		DbSelectArea("DEV")
		DEV->(DbSetOrder(1))
		lFound := DEV->(DbSeek(xFilial("DEV")+Right(AllTrim(oXML:_InfNfe:_Id:Text),44))) .And. DEV->DEV_STATUS == '1'//Filial + Chave de acesso
	EndIf
	If lFound 
		If lJob .And. !lNFeTransp
			If !(cTipoNF $ "DB")		
				aAdd(aErros,{cFile,"COM005 - " + STR0105 +SDS->(DS_DOC+"/"+SerieNfId("SDS",2,"DS_SERIE")); //"ID de NF-e já registrado na NF "
				+STR0106 +Posicione("SA2",1,xFilial("SA2")+SDS->(DS_FORNEC+DS_LOJA),"A2_NOME"); //" do fornecedor "
				+" (" +SDS->(DS_FORNEC +"/" +DS_LOJA)+ ").",STR0107}) //"Exclua o documento registrado na ocorrência."
				aAdd(aErroErp,{cFile,"COM005"})				
			Else
				aAdd(aErros,{cFile,"COM006 - " + STR0105 +SDS->(DS_DOC+"/"+SerieNfId("SDS",2,"DS_SERIE")); //"ID de NF-e já registrado na NF "
				+STR0135 + Posicione("SA1",1,xFilial("SA1")+SDS->(DS_FORNEC+DS_LOJA),"A1_NOME"); //" do cliente "
				+" (" +SDS->(DS_FORNEC +"/" +DS_LOJA)+ ").",STR0107}) //"Exclua o documento registrado na ocorrência."
				aAdd(aErroErp,{cFile,"COM006"})							
			EndIf	
		ElseIf lJob                                                 
			cChvNfe	:= Right(AllTrim(oAuxXml:_ID:TEXT),44)
			cMotivo  := STR0105//--"ID de NF-e já registrado na NF "
			nNumDet  += 1
			cDetalhe += Str(nNumDet,1)+("º " + STR0105 +DEV->(DEV_DOC+"/"+SerieNfId("DEV",2,"DEV_SERIE")) +". CNPJ :" + " (" +DEV->DEV_CGCREM+ ")." )+ cPulaLinha //--"Erro: "//--"O Cliente Emitente não está cadastrado.//-- Favor cadastrá-lo!"
			aAdd(aErros,{cFile,"COM006 - " + STR0105 +DEV->(DEV_DOC+"/"+SerieNfId("DEV",2,"DEV_SERIE")); //"ID de NF-e já registrado na NF "
			+" o CNPJ :" + " (" +DEV->DEV_CGCREM+ ").",STR0107})//"Do Cliente # //"Exclua o documento registrado na ocorrência."			
			aAdd(aErroErp,{cFile,"COM006"})
		Else
			Aviso(STR0082,STR0086 +SDS->(DS_DOC+"/"+SerieNfId("SDS",2,"DS_SERIE"));
			+ STR0087 +SDS->(DS_FORNEC+"/"+DS_LOJA) +".",{STR0004},2,"ImpXML_NFe")
			lMensExib := .T.
		EndIf
		lProces	:= .F.
	EndIf	
	
	if lZeroSDS 
		cDoc     := StrZero(Val(AllTrim(oXML:_InfNfe:_Ide:_nNF:Text)),TamSx3("F1_DOC")[1])
	else
		cDoc     := AllTrim(oXML:_InfNfe:_Ide:_nNF:Text)
	endif

	cSerie   := PadR(oXML:_InfNfe:_Ide:_Serie:Text,SerieNfId("SF1",6,"F1_SERIE"))
	
	If !lNFeTransp .And. lProces
		//-- Se tag CGC valida
		//-- Busca fornecedor/cliente na base
		lAchouForn :=.F.
		cTabEmit := If (Empty(cTabEmit),If(cTipoNF $ "DB","SA1","SA2"),cTabEmit)
		(cTabEmit)->(dbSetOrder(3)) 	
		If (cTabEmit)->(dbSeek(xFilial(cTabEmit)+cCGC))
			While !(cTabEmit)->(EOF()) .And. cCGC $ A140ICAES((cTabEmit)->&(Substr(cTabEmit,2,2)+"_CGC"))
				If (cTabEmit)->&(Substr(cTabEmit,2,2)+"_MSBLQL") <> "1" .And. (A140INSC(cInsc,(cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR")) .Or. Empty(A140ICAES(Alltrim((cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR")))) .Or. "ISENT" $ A140ICAES(Alltrim((cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR"))))
					If A140INSC(cInsc,(cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR"))
						cCodigo 	:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_COD")
						cLoja   	:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_LOJA")
						cNomeFor 	:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_NOME")
						nQCNPJ++
						nQINSC++
						lAchouForn 	:= .T.
						lSemIE 		:= .F.
					ElseIf Empty(A140ICAES(Alltrim((cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR")))) .And. nQINSC = 0
						cCodigo	:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_COD")
						cLoja		:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_LOJA")
						cNomeFor 	:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_NOME")
						nQCNPJ++
						lAchouForn := .T.
						lSemIE 		:= .F.
					ElseIf 'ISENT' $ A140ICAES(Alltrim((cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR"))) .And. nQINSC = 0
						cCodigo	:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_COD")
						cLoja		:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_LOJA")
						cNomeFor 	:= (cTabEmit)->&(Substr(cTabEmit,2,2)+"_NOME")
						nQCNPJ++
						lAchouForn := .T.
						lSemIE 		:= .F.
					ElseIf Empty(A140ICAES(Alltrim((cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR")))) .And. nQINSC <> 0 
						nQCNPJ++
						lAchouForn := .T.
					EndIf
				//Achou CNPJ mas IE esta cadastrado errado
				Elseif (cTabEmit)->&(Substr(cTabEmit,2,2)+"_MSBLQL") <> "1" .And. !Empty(A140ICAES(Alltrim((cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR")))) .And. !A140INSC(cInsc,(cTabEmit)->&(Substr(cTabEmit,2,2)+"_INSCR"))
					If !lAchouForn
						lAchouForn := .T.
						lSemIE := .T.
					Endif
				EndIf
				(cTabEmit)->(dbSkip())
			EndDo
			
			//Ponto de Entrada para informar o fornecedor/cliente correto, 
			//caso não seja possível identificar o fornecedor/cliente através do CNPJ e Inscrição Estadual.	
			If nQCNPJ > 1 .And. nQINSC <> 1 .And. ExistBlock("A140IFOR")
				aFornec := ExecBlock("A140IFOR",.F.,.F.,{cTabEmit, cCGC, cInsc, oXml})
				If ValType(aFornec) == "A" .And. Len(aFornec) >= 3
					cCodigo := aFornec[1]
					cLoja	 := aFornec[2]
					cNomeFor:= aFornec[3]
					(cTabEmit)->(dbSetOrder(1))
					If (cTabEmit)->(dbSeek(xFilial(cTabEmit)+cCodigo+cLoja)) .And. cCGC $ A140ICAES((cTabEmit)->&(Substr(cTabEmit,2,2)+"_CGC"))
						nQCNPJ := 1
						nQINSC := 1
						lAchouForn := .T.
					EndIf
				endIf
			EndIf
			
		Else
			
			lSemCad := .T.
			
		EndIf	
		
		If nQCNPJ > 1 .And. nQINSC <> 1 //CNPJ duplicado
			If lJob
				aAdd(aErros,{cFile,"COM028 - " + STR0227 + Transform(cCGC,"@R 99.999.999/9999-99") + STR0228, STR0229})
			ElseIf !lMensExib
				Aviso(STR0082,STR0227 + Transform(cCGC,"@R 99.999.999/9999-99") + STR0228 ,{STR0004},2,"ImpXML_NFe")
				lMensExib := .T.				
			EndIf
			aAdd(aErroErp,{cFile,"COM028"})
			lProces := .F.
		Elseif lSemCad .Or. (lAchouForn .And. lSemIE) //CPNJ inexistente ou encontrou CNPJ mas não encontrou com a IE correta.
			If lJob
				aAdd(aErros,{cFile,"COM007 - " + IIF(cTipoNF $ "DB", STR0041 +oXML:_INFNFE:_EMIT:_XNOME:Text, STR0040 +oXML:_INFNFE:_EMIT:_XNOME:Text) +" [" + Transform(cCGC,"@R 99.999.999/9999-99") +"] "+ STR0109, IIF(cTipoNF $ "DB",STR0136,STR0110)}) //"Fonecedor/Cliente"#"inexistente na base."#"Gere cadastro para este fornecedor/cliente."
			ElseIf !lMensExib
				Aviso(STR0082,If(cTipoNF $ "DB",STR0041,STR0040) + STR0090 + Transform(cCGC,"@R 99.999.999/9999-99") +STR0091,{STR0004},2,"ImpXML_NFe")
				lMensExib := .T.				
			EndIf
			aAdd(aErroErp,{cFile,"COM007"})
			lProces := .F.
		ElseIf !lAchouForn .And. !lSemCad //Fornecedor bloqueado
			If lJob
				aAdd(aErros,{cFile,"COM030 - " + IIF(cTipoNF $ "DB", STR0233 +oXML:_INFNFE:_EMIT:_XNOME:Text, STR0232 +oXML:_INFNFE:_EMIT:_XNOME:Text) +" [" + Transform(cCGC,"@R 99.999.999/9999-99") +"] "+ STR0234, IIF(cTipoNF $ "DB",STR0236,STR0235)}) //"Cliente"#"Fornecedor"#"bloqueado na base."#"Faça o desbloqueio do cadastro deste cliente."#"Faça o desbloqueio do cadastro deste fornecedor."
			ElseIf !lMensExib
				Aviso(STR0082,If(cTipoNF $ "DB",STR0233,STR0232) + STR0090 + Transform(cCGC,"@R 99.999.999/9999-99") +STR0234,{STR0004},2,"ImpXML_NFe")
				lMensExib := .T.				
			EndIf
			aAdd(aErroErp,{cFile,"COM030"})
			lProces := .F.
		EndIf
	ElseIf lProces
		cChvNfe	:= Right(AllTrim(oAuxXml:_ID:TEXT),44)
		SA1->(dbSetOrder(3))             			
		//--Verifica se o Emitente está cadastrado como Cliente caso não esteja mas o parâmetro (MV_IMPEMIT = .T.),importará emitente
		If lIMPEMIT .And. nModulo == 43 .And. !SA1->(dbSeek(xFilial('SA1')+AllTrim(cCGC)))   //--Módulo SIGATMS S
			lProces := .T.
		Else
		//--Verifica se o Emitente está cadastrado como Cliente caso não esteja a importação não ocorrerá
			If !SA1->(dbSeek(xFilial('SA1')+AllTrim(cCGC)))		
				cMotivo := IIf(Empty(cMotivo), STR0188, STR0210)//--"Cliente Emitente"//--Ocorreram erros na Importacao do XML.
				nNumDet  += 1
				cDetalhe += Str(nNumDet,1)+("º " + STR0189 + STR0190 + STR0191) + cPulaLinha //--"Erro: "//--"O Cliente Emitente não está cadastrado.//-- Favor cadastrá-lo!"
				aAdd(aErros,{cFile,"COM008 - " + STR0190+ ": " + oXML:_INFNFE:_EMIT:_XNOME:Text +" [" + Transform(cCGC,"@R 99.999.999/9999-99") +"] ", STR0192})  //--"O Cliente Emitente não está cadastrado: " //--"Inclua-o Emitente manualmente."
				aAdd(aErroErp,{cFile,"COM008"})
				lProces := .F.
			Else		
				cCodigo 	:= ("SA1")->&(Substr("SA1",2,2)+"_COD")
				cLoja   	:= ("SA1")->&(Substr("SA1",2,2)+"_LOJA")
				cNomeFor := ("SA1")->&(Substr("SA1",2,2)+"_NOME")	
			EndIf
	    EndIf	   	   	   
   		//--Verifica se o Destinatário está cadastrado como Cliente caso não esteja cadastraremos
		If !SA1->(dbSeek(xFilial('SA1')+AllTrim(cCGCDes)))
			If !(TMSAE80Inc(oAuxXml,1,,,@cMotivo,@nNumDet,@cDetalhe))	//Inclui o Cliente - Destinatario
				aAdd(aErros,{cFile,"COM009 - " + STR0193,STR0192}) //"Não foi possível incluir o destinatário." //"#"Inclua-o  manualmente."
				aAdd(aErroErp,{cFile,"COM009"})
				lProces := .F.
			EndIf
		Else
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Destinatario Estrangeiro
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If XmlChildEx(oAuxXml:_DEST,"_IDESTRANGEIRO") # NIL
				cIDEstrang := oAuxXml:_DEST:_IDESTRANGEIRO:TEXT
				If lRetIDEstran 
					aRetEstrang := RetIDEstrang(cIDEstrang)
				EndIf
				If Empty(aRetEstrang)
					If !(TMSAE80Inc(oAuxXml,1,,,@cMotivo,@nNumDet,@cDetalhe,,cIDEstrang))	//Inclui o Cliente - Destinatario
						aAdd(aErros,{cFile,"COM009 - " + STR0193,STR0192}) //"Não foi possível incluir o destinatário." //"#"Inclua-o  manualmente."
						aAdd(aErroErp,{cFile,"COM009"})
						lProces := .F.
					EndIf
				EndIf
			EndIf
		EndIf		
		//Se existir TAG ENTREGA
		If lProces .And. XmlChildEx(oAuxXml,"_ENTREGA") # NIL
			If !(XmlChildEx(oAuxXml:_DEST,"_IDESTRANGEIRO") # NIL) //Se houver a TAG IDESTRANGEIRO e a TAG ENTREGA não deve ser preenchido a DUL, somente o cliente recebedor (DE5_CGCREC) com os dados da TAG ENTREGA
				If !(AllTrim(oAuxXml:_ENTREGA:_XLGR:TEXT) = AllTrim(oAuxXml:_DEST:_ENDERDEST:_XLGR:TEXT))
					DUL->(dbSetOrder(2))
					SA1->(dbSeek(xFilial('SA1')+AllTrim(cCGCDes)))
					If !(DUL->(dbSeek(xFilial("DUL")+SA1->(A1_COD+A1_LOJA))))
						If !(TMSAE80Inc(oAuxXml,2,,,@cMotivo,@nNumDet,@cDetalhe,@cSeqEnd,cIDEstrang))
							aAdd(aErros,{cFile,"COM010 - " + STR0194,STR0192}) //"Não foi possível incluir o local de entrega"#//"Inclua-o  manualmente."
							aAdd(aErroErp,{cFile,"COM010"})
							lProces := .F.					
						EndIf
					Else
						//SE EXISTIR DUL VERIFICAREMOS SE O ENDERECO ESTA ATUALIZADO
						cAliasDUL := GetNextAlias()
						cQueryDUL := "SELECT DUL_END,DUL_BAIRRO, DUL_MUN, DUL_EST, DUL_SEQEND "
						cQueryDUL += " FROM " + RetSqlName("DUL")+ " DUL "
						cQueryDUL += " WHERE "
						cQueryDUL += " DUL_FILIAL = '"+xFilial("DUL")+"' AND "
						cQueryDUL += " DUL_CODCLI = '"+SA1->A1_COD+"' AND "
						cQueryDUL += " DUL_LOJCLI = '"+SA1->A1_LOJA+"' AND "
						cQueryDUL += " DUL.D_E_L_E_T_ = ' ' "
						
						cQueryDUL := ChangeQuery(cQueryDUL)
						DbUseArea(.T., "TOPCONN", TCGenQry(,,cQueryDUL),cAliasDUL, .T., .T.)
		
						(cAliasDUL)->(DbGoTop())
						While (cAliasDUL)->(!Eof()) // (01)//While !cAliasDUL->(EOF())
							If AllTrim(oAuxXml:_ENTREGA:_XLGR:TEXT) $ AllTrim((cAliasDUL)->DUL_END)
								lIncluiDUL := .F.
								Exit
							EndIf
							(cAliasDUL)->(dbSkip())
						End
						//CASO O ENDEREÇO NÃO ESTEJA ATUALIZADO CRIAREMOS UM NOVO DUL
						If lIncluiDUL
							If !(TMSAE80Inc(oAuxXml,2,,,@cMotivo,@nNumDet,@cDetalhe,@cSeqEnd,cIDEstrang))
								aAdd(aErros,{cFile,"COM011 - " + STR0195,STR0196}) //"Não foi possível atualizar o local de entrega"#"Atualize-o manualmente."
								aAdd(aErroErp,{cFile,"COM011"})
								lProces := .F.
							EndIf
						Else
							cSeqEnd := 	(cAliasDUL)->DUL_SEQEND
						EndIf
						(cAliasDUL)->(dbCloseArea())
					EndIf
				EndIf
			EndIf
		EndIf	
   EndIf
	/* ----------------------------------------------------------------------
	SE FOR PARA O EDI TEREMOS QUE AMARRAR COM O CLIENTE  OU COM EMBARCADOR
	------------------------------------------------------------------------*/
	If cTipoNF $ "DB" .Or. lNFeTransp
		cCampo1 := "A7_PRODUTO"
		cCampo2 := "A7_FILIAL"
		cCampo3 := "A7_CLIENTE"
		cCampo4 := "A7_LOJA"
		cCampo5 := "A7_CODCLI"
		If lNFeTransp
			cCampo6 := "DE7_CODPRO"
			cCampo7 := "DE7_FILIAL"
			cCampo8 := "DE7_CODCLI"
			cCampo9 := "DE7_LOJCLI"
			cCampo10:= "DE7_PRDEMB"
		EndIf				
	Else                                        
		//-- Processa cabeçalho e itens
		cCampo1 := "A5_PRODUTO"
		cCampo2 := "A5_FILIAL"
		cCampo3 := "A5_FORNECE"
		cCampo4 := "A5_LOJA"
		cCampo5 := "A5_CODPRF" 
	EndIf	
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Grava o tipo do frete ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
	If lProces
		Do Case 
			Case AllTrim(oXML:_InfNfe:_Transp:_ModFrete:Text) == "0"
				cTipoFrete := "C"
			Case AllTrim(oXML:_InfNfe:_Transp:_ModFrete:Text) == "1"
				cTipoFrete := "F"
			Case AllTrim(oXML:_InfNfe:_Transp:_ModFrete:Text) == "2"
				cTipoFrete := "T"			
			Case AllTrim(oXML:_InfNfe:_Transp:_ModFrete:Text) == "3" .Or. AllTrim(oXML:_InfNfe:_Transp:_ModFrete:Text) == "9" 
				cTipoFrete := "S"
			Case AllTrim(oXML:_InfNfe:_Transp:_ModFrete:Text) == "4" 
				cTipoFrete := "D"
		End Case
		
		// Verifica existência de documento com mesma numeração.
		If ExistBlock("A140IDOC") //Manipula numero e serie do documento
			aA140IDOC := ExecBlock("A140IDOC",.F.,.F.,{cDoc, cSerie, cCodigo, cLoja})			
			If ValType(aA140IDOC) == 'A' .And. Len(aA140IDOC) >= 2
				cDoc   := aA140IDOC[1]
				cSerie := aA140IDOC[2]
			EndIf
		EndIf
		
		dbSelectArea("SDS") 
		dbSetorder(1)
		If msSeek(xFilial("SDS")+cDoc+cSerie+cCodigo+cLoja)
			If lJob
				aAdd(aErros,{cFile,"COM025 - " + STR0223+" "+cDoc+", "+STR0224+" "+cSerie+" , "+STR0225,STR0226}) //Documento cdoc, serie cSerie, já cadastrado. verifique se o documento já foi importado para o ERP. 
			Else
				Aviso(STR0001,STR0223+" "+cDoc+", "+STR0224+""+cSerie+" , "+STR0225+" "+STR0226,2,"ImpXML_NFe")
			EndIf
			aAdd(aErroErp,{cFile,"COM025"})
			lProces := .F.
		EndIf
	EndIf
		
	If !lNFeTransp .And. lProces
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Grava os Dados da DANFE ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		cCNPJTran  := ""
		cCodTransp := ""
		cPlacaTran := ""
		nVolume    := 0
		cEspecie   := ""
		nPesoLiq   := 0
		nPesoBruto := 0
					
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Prepara o Array aEspVol para gravar os campos Vol/Esp ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		aAdd(aEspVol,{"DS_ESPECI1",""})
		aAdd(aEspVol,{"DS_ESPECI2",""})
		aAdd(aEspVol,{"DS_ESPECI3",""})
		aAdd(aEspVol,{"DS_ESPECI4",""})
		aAdd(aEspVol,{"DS_VOLUME1",0})
		aAdd(aEspVol,{"DS_VOLUME2",0})
		aAdd(aEspVol,{"DS_VOLUME3",0})
		aAdd(aEspVol,{"DS_VOLUME4",0})				
		If ValType(XmlChildEx(oXML:_InfNFe,"_TRANSP")) == "O" 			
			If ValType(XmlChildEx(oXML:_InfNFe:_Transp,"_TRANSPORTA")) == "O"
				If ValType(XmlChildEx(oXML:_InfNFe:_Transp:_Transporta,"_CPF")) == "O"
					cCNPJTran := oXML:_InfNfe:_Transp:_Transporta:_CPF:Text	
				ElseIf ValType(XmlChildEx(oXML:_InfNFe:_Transp:_Transporta,"_CNPJ")) == "O"
					cCNPJTran := oXML:_InfNfe:_Transp:_Transporta:_CNPJ:Text
				EndIf
				SA4->(dbSetOrder(3))
				If SA4->(dbSeek(xFilial("SA4")+cCNPJTran))
					cCodTransp := SA4->A4_COD
				EndIf
			EndIf
			If ValType(XmlChildEx(oXML:_InfNFe:_Transp,"_VEICTRANSP")) == "O"
				If ValType(XmlChildEx(oXML:_InfNFe:_Transp:_VeicTransp,"_PLACA")) == "O"
					cPlacaTran := oXML:_InfNFe:_Transp:_VeicTransp:_Placa:Text
				EndIf
			EndIf
			If ValType(XmlChildEx(oXML:_InfNFe:_Transp,"_VOL")) == "O"
				aQtdVol := {oXML:_InfNfe:_Transp:_Vol}
			ElseIf ValType(XmlChildEx(oXML:_InfNFe:_Transp,"_VOL")) == "A"
				aQtdVol := oXML:_InfNfe:_Transp:_Vol
			EndIf
			For nX := 1 To Len(aQtdVol)
				If ValType(XmlChildEx(aQtdVol[nX],"_PESOB")) == "O"
					nPesoBruto += Val(aQtdVol[nX]:_PESOB:TEXT)
				EndIf
				If ValType(XmlChildEx(aQtdVol[nX],"_PESOL")) == "O"
					nPesoLiq += Val(aQtdVol[nX]:_PESOL:TEXT)
				EndIf
				If nX <= 4
					If ValType(XmlChildEx(aQtdVol[nX],"_ESP")) == "O"
						aEspVol[nX][2] := aQtdVol[nX]:_Esp:TEXT
					EndIf
					If ValType(XmlChildEx(aQtdVol[nX],"_QVOL")) == "O"
						aEspVol[nX+4][2] := Val(aQtdVol[nX]:_QVol:TEXT)
					EndIf
				EndIf
			Next nX
		EndIf
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Valida tag da data de emissao      ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If ValType(XmlChildEx(oXML:_InfNfe:_Ide,"_DEMI")) == "O"
			dEmis := StoD(StrTran(AllTrim(oXML:_InfNfe:_Ide:_DEmi:Text),"-",""))
		ElseIf ValType(XmlChildEx(oXML:_InfNfe:_Ide,"_DHEMI")) == "O"
			dEmis := StoD(StrTran(Substr((oXML:_InfNfe:_Ide:_DhEmi:Text),1,10),"-",""))
		EndIf
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Grava os Dados do Cabecalho - SDS  ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		DbSelectArea("SDS")
		 AADD(aHeadSDS,{{"DS_FILIAL"	,xFilial("SDS")																	     	},; //Filial
						    {"DS_CNPJ"		,cCGC																				},; //CGC
						    {"DS_DOC"		,cDoc 																				},; //Numero do Documento
						    {"DS_SERIE"		,cSerie 																			},; //Serie
						    {"DS_FORNEC"	,cCodigo																			},; //Fornecedor
						    {"DS_LOJA"		,cLoja 																				},; //Loja do Fornecedor
						    {"DS_NOMEFOR"	,cNomeFor																			},; //Nome do Fornecedor
						    {"DS_EMISSA"	,dEmis																				},; //Data de Emissão
						    {"DS_EST"		,oXML:_INFNFE:_EMIT:_ENDEREMIT:_UF:TEXT												},; //Estado de emissao da NF
						    {"DS_TIPO"		,cTipoNF													 						},; //Tipo da Nota
						    {"DS_FORMUL"	,"N" 																		 		},; //Formulario proprio
						    {"DS_ESPECI"	,"SPED"																		  		},; //Especie
						    {"DS_ARQUIVO"	,AllTrim(cFile)																   		},; //Arquivo importado
						    {"DS_STATUS"	,If(cTipoNF <> "N",cTipoNF," ")														},; //Status
						    {"DS_CHAVENF"	,Right(AllTrim(oXML:_InfNfe:_Id:Text),44)											},; //Chave de Acesso da NF
						    {"DS_VERSAO"	,oXML:_InfNfe:_versao:text 															},; //Versão
						    {"DS_USERIMP"	,IIf(!lJob,cUserName,Iif(lImpXML,STR0251,STR0137))														},; //Usuario na importacao
						    {"DS_DATAIMP"	,dDataBase																			},; //Data importacao do XML
						    {"DS_HORAIMP"	,SubStr(Time(),1,5)																	},; //Hora importacao XML
						    {"DS_FRETE"		,Val(oXML:_INFNFE:_TOTAL:_ICMSTOT:_vFrete:TEXT)									},; //Valor Frete
						    {"DS_SEGURO"	,Val(oXML:_INFNFE:_TOTAL:_ICMSTOT:_vSeg:TEXT)										},; //Valor Seguro
						    {"DS_DESPESA"	,Val(oXML:_INFNFE:_TOTAL:_ICMSTOT:_vOutro:TEXT)									},; //Valor Desconto
						    {"DS_DESCONTO"	,Val(oXML:_INFNFE:_TOTAL:_ICMSTOT:_vDesc:TEXT)										},; //Valor Desconto
						    {"DS_VALMERC"	,Val(oXML:_INFNFE:_TOTAL:_ICMSTOT:_vProd:TEXT)										},; //Valor Mercadoria
							{"DS_TOTAL"		,Val(oXML:_INFNFE:_TOTAL:_ICMSTOT:_vNF:TEXT)										},; //Valor Total da Nota Fiscal
						    {"DS_TPFRETE"	,cTipoFrete																			},; //Tipo de Frete
						    {"DS_TRANSP"	,cCodTransp																			},; //Codigo da Transportadora
						    {"DS_PLACA"		,cPlacaTran																			},; //Placa
						    {"DS_PLIQUI"	,nPesoLiq																			},; //Peso Liquido
						    {"DS_PBRUTO"	,nPesoBruto																			},; //Peso Bruto
						    {"DS_ESPECI1"	,cValToChar(aEspVol[1][2])															},; //Especie1
							{"DS_VOLUME1"	,aEspVol[5][2]																		},; //Volume1
							{"DS_ESPECI2"	,cValToChar(aEspVol[2][2])															},; //Especie2
							{"DS_VOLUME2"	,aEspVol[6][2]																		},; //Volume2
							{"DS_ESPECI3"	,cValToChar(aEspVol[3][2])															},; //Especie3
							{"DS_VOLUME3"	,aEspVol[7][2]																		},; //Volume3
						   	{"DS_ESPECI4"	,cValToChar(aEspVol[4][2])															},; //Especie4
							{"DS_VOLUME4"	,aEspVol[8][2]																		},; //Volume4
							{"DS_HORNFE"  ,cHrEmis																				}}) //Hora NF-e
			
	EndIf
	If lProces
		IIF(cTipoNF $ "DB",SA7->(DbSetOrder(1)),SA5->(DbSetOrder(1)))
		For nX := 1 To Len(aItens)
			cProduto 	:= ""
			cNFOriComp	:= ""
			cSerOriComp	:= ""
			cItOriComp	:= ""

			//-- Ponto de entrada para cutomizacao da identificacao do produto
			If lA140IPRD
				cProduto := ExecBlock("A140IPRD",.F.,.F.,{cCodigo,cLoja,AllTrim(aItens[nX]:_Prod:_cProd:Text),aItens[nX],IIf(cTipoNF $ "DB","SA7","SA5"),oXML}) 
				SB1->(DbSetOrder(1))
				If ValType(cProduto) # "C" .Or. !SB1->(dbSeek(xFilial("SB1")+cProduto))
					cProduto := ""
				EndIf
			EndIf
			
			If Empty(cProduto)			
					If lNFeTransp //--Se for importacao do SIGATMS verifica primeiro a tabela DE7 (Produto x Embarcador)
						cQuery := "SELECT " +cCampo6 + " FROM " +RetSqlName("DE7")
						cQuery += " WHERE D_E_L_E_T_ = ' ' AND "
						cQuery += cCampo7 +" = '" +xFilial("DE7") +"' AND "
						cQuery += cCampo8 +" = '" +cCodigo +"' AND "
						cQuery += cCampo9+" = '" +cLoja +"' AND "
						cQuery += "Replace(Upper("+cCampo10+"), ' ','') = '"+ StrTran(AllTrim(UPPER(aItens[nX]:_Prod:_cProd:Text)), " ") +"' AND "
						cQuery += cCampo6 +" <> ' '"					
						
						If Select("TRB") > 0
							TRB->(dbCloseArea())
						EndIf        					
						TcQuery cQuery new Alias "TRB"            
					   If !TRB->(EOF())
							cProduto := TRB->(&cCampo6)
						EndIf
					EndIf
					If !lNFeTransp .Or. Empty(cProduto)
						cQuery := "SELECT " +cCampo1 + " FROM " +RetSqlName(If(cTipoNF $ "DB" .Or. lNFeTransp,"SA7","SA5"))
						cQuery += " WHERE D_E_L_E_T_ = ' ' AND "
						cQuery += cCampo2 +" = '" +xFilial(If(cTipoNF $ "DB","SA7","SA5")) +"' AND "
						cQuery += cCampo3 +" = '" +cCodigo +"' AND "
						cQuery += cCampo4 +" = '" +cLoja +"' AND "
						cQuery += "Replace(Upper("+cCampo5+"), ' ','') = '" + StrTran(AllTrim(UPPER(StrTran(aItens[nX]:_Prod:_cProd:Text,"'"))), " ") +"' AND "
						cQuery += cCampo1 +" <> ' '" 
					    					
						If Select("TRB") > 0
							TRB->(dbCloseArea())
						EndIf        
						
						TcQuery cQuery new Alias "TRB"
					             
					   If !TRB->(EOF())
							cProduto := TRB->(&cCampo1)
						ElseIf !lNfeTransp 
							If lJob
								aAdd(aErros,{cFile,IIF(cTipoNF $ "DB","COM027 - ","COM012 - ") + IIF(cTipoNF $ "DB",STR0041,STR0108) + oXML:_INFNFE:_EMIT:_XNOME:Text +" [" + cCodigo + "] [" + cLoja + "] [" +Transform(cCGC,"@R 99.999.999/9999-99")+"]"; //"Fornecedor "
														+IIF(cTipoNF $ "DB",STR0138,STR0111); //" sem cadastro de Produto X Fornecedor"
														+STR0112 +AllTrim(StrTran(aItens[nX]:_Prod:_cProd:Text,"'")) +". " + STR0043 + ": " + AllTrim(aItens[nX]:_Prod:_xProd:Text) + ". " + STR0015 + cDoc + ".",STR0113}) //" para o código "#"Gere cadastro para esta relação."
							Else
								If !lMensExib
									Aviso(STR0082,IIF(cTipoNF $ "DB",STR0041,STR0108) + oXML:_INFNFE:_EMIT:_XNOME:Text +" [" + cCodigo + "] [" + cLoja + "] [" +Transform(cCGC,"@R 99.999.999/9999-99")+"]";//"Erro"#"Fornecedor"
															+IIF(cTipoNF $ "DB",STR0138,STR0111); //" sem cadastro de Produto X Fornecedor"
															+STR0115 +AllTrim(StrTran(aItens[nX]:_Prod:_cProd:Text,"'")) +". " + STR0043 + ": " + AllTrim(aItens[nX]:_Prod:_xProd:Text) + ". " + STR0015 + cDoc + ".",{"OK"},2,"ImpXML_NFe") //" para o código "
									lMensExib := .T.
								EndIf
							EndIf											
							aAdd(aErroErp,{cFile,IIF(cTipoNF $ "DB","COM027","COM012")})										
							lProces := .F.
						EndIf
					EndIf				
				TRB->(dbCloseArea())
			EndIf
			nQuant 		:= Val(aItens[nX]:_Prod:_qCom:Text)
			nPrecUni 	:= Val(aItens[nX]:_Prod:_vUnCom:Text)
			
			If nPrecUni == 0 .And. !(cTipoNF $ "CND")
				If lJob
					aAdd(aErros,{cFile,"COM013 - " + STR0212,STR0213})	// Nota fiscal possui itens com valor zerado./Verifique a nota recebida do fornecedor.
				ElseIf !lMensExib
					Aviso(STR0082,cFile + " " + STR0212,{STR0004},2,"ImpXML_NFe")	// Nota fiscal possui itens com valor zerado.
					lMensExib := .T.
				EndIf
				aAdd(aErroErp,{cFile,"COM013"})
				lProces := .F.
			EndIf
			
			If lProces .And. cTipoNF $ "NC"
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Verifica se existe a Tag para pedido de compra                  ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				l140VPed := .F.
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_XPED")) == "O" 
					cPedido := aItens[nX]:_Prod:_xPed:Text
					If Len(cPedido) > TamSx3("DT_PEDIDO")[1]
						cPedido := RIGHT(cPedido,TamSx3("DT_PEDIDO")[1])
					Else
						cPedido := PADR(cPedido,TamSx3("DT_PEDIDO")[1])
					EndIf
				EndIf 
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_NITEMPED")) == "O"
					cItemPed:= aItens[nX]:_Prod:_nItemPed:Text
					If Len(cItemPed) > TamSx3("DT_ITEMPC")[1]
						cItemPed := RIGHT(cItemPed,TamSx3("DT_ITEMPC")[1])
					Else
						cItemPed := PADL(cItemPed,TamSx3("DT_ITEMPC")[1],"0")
					EndIf
				EndIf
				
				If lA140IVPED
					l140VPed := .F.
					a140VPed := ExecBlock("A140IVPED",.F.,.F.,{cCodigo,cLoja,cProduto,nQuant})
					If ValType(a140VPed) == "A" .And. Len(a140VPed) > 0 .And. Len(a140VPed[1]) >= 3
						
						If Len(a140PedAux) == 0
							For nI := 1 To Len(a140VPed)
								aAdd(a140PedAux,{a140VPed[nI,1],a140VPed[nI,2],a140VPed[nI,3]})
							Next nI
						Else
							For nI := 1 To Len(a140PedAux)
								nPos140Ped := aScan(a140VPed,{|x| AllTrim(x[1]) + AllTrim(x[2]) == AllTrim(a140PedAux[nI,1]) + AllTrim(a140PedAux[nI,2])})
								If nPos140Ped > 0
									aDel(a140VPed,nPos140Ped)
									aSize(a140VPed,Len(a140VPed)-1)
								Endif
							Next nI
						Endif
						
						If Len(a140VPed) == 1
							nQtdVPed := 0
							For nI := 1 To Len(a140VPed)
								nQtdVPed += a140VPed[nI,3]
								
								lValQtd := Iif(Len(a140VPed[nI]) > 3, a140VPed[nI,4], .T.) // Verifica se valida a quantidade do pedido de compra.
							Next nI
							
							If nQtdVPed > nQuant .And. lValQtd
								If lJob
									aAdd(aErros,{cFile,"COM029 - " + STR0231,STR0230}) //"Quantidade nos Pedidos (A140IVPED) é maior que a quantidade do XML"#"Verificar problema"
								ElseIf !lMensExib
									Aviso(STR0082,cFile + " " + STR0231,{STR0004},2,"ImpXML_NFe") //"Quantidade nos Pedidos (A140IVPED) é maior que a quantidade do XML"
									lMensExib := .T.
								EndIf
								aAdd(aErroErp,{cFile,"COM029"})
								lProces := .F.
							Elseif nQtdVPed < nQuant
								aAdd(a140VPed,{"","",nQuant-nQtdVPed})
							Else
								cPedido	:= a140VPed[1,1]
								cItemPed	:= a140VPed[1,2]
							Endif
							l140VPed := .T.
						Elseif Len(a140VPed) > 1
							nQtdVPed := 0
							For nI := 1 To Len(a140VPed)
								nQtdVPed += a140VPed[nI,3]
								
								lValQtd := Iif(Len(a140VPed[nI]) > 3, a140VPed[nI,4], .T.) // Verifica se valida a quantidade do pedido de compra.
							Next nI
							
							If nQtdVPed > nQuant .And. lValQtd
								If lJob
									aAdd(aErros,{cFile,"COM029 - " + STR0231,STR0230}) //"Quantidade nos Pedidos (A140IVPED) é maior que a quantidade do XML"#"Verificar problema"
								ElseIf !lMensExib
									Aviso(STR0082,cFile + " " + STR0231,{STR0004},2,"ImpXML_NFe") //"Quantidade nos Pedidos (A140IVPED) é maior que a quantidade do XML"
									lMensExib := .T.
								EndIf
								aAdd(aErroErp,{cFile,"COM029"})
								lProces := .F.
							Elseif nQtdVPed < nQuant
								aAdd(a140VPed,{"","",nQuant-nQtdVPed})
							Endif
							l140VPed := .T.
						Endif
						
					Endif
				EndIf
				
				If !Empty(cPedido) .And. !Empty(cItemPed)
					DbSelectArea("SC7")
					DbSetOrder(1)
					If MsSeek(xFilial("SC7")+cPedido+cItemPed)
						If	SC7->C7_FORNECE == cCodigo .And. If(lConsLoja,SC7->C7_LOJA == cLoja,.T.) .And.;
							SC7->C7_PRODUTO == cProduto .And.;
							(SC7->C7_QUANT - SC7->C7_QUJE - SC7->C7_QTDACLA) > 0 .And.;
							SC7->C7_ENCER != "E" .And. SC7->C7_RESIDUO != "S"
							lProces := .T.
							l140VPed := .T.

							lConvUM		:= .F.
							nQuantConv	:= 0 //converte ou não para segunda unidade de medida a qtd do PC
						
							If lUnidMed 

								//Busco em qual unidade o produto deve ser tratado na importação.
								lConvUM := If(cTipoNF $ "BD", ;
								GetAdvFVal("SA7","A7_UMNFE",xFilial("SA7")+cCodigo+cLoja+cProduto,1) == "2", ;
								GetAdvFVal("SA5","A5_UMNFE",xFilial("SA5")+cCodigo+cLoja+cProduto,1) == "2")
								
								cUM			:= GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
								cSEGUM		:= GetAdvFVal("SB1","B1_SEGUM",xFilial("SB1")+cProduto,1)
								lFatorConv	:= COLVLSEGUM(cProduto,cSEGUM)

								If !Empty(cSEGUM)
									If lConvUM
										//Produto não possui fator de conversão e não tem como converter para primeira
										//unidade de medida
										If !lFatorConv
											lProces := .F.
											aAdd(aErros,{cFile,"COM050 - " + STR0253 + cProduto ,STR0198}) //"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
											aAdd(aErroErp,{cFile,"COM050"})
										Else
											//Realizo a conversão da 1a unidade do PC para 2a unidade de medida para comparativo
											nQtdVPed := (SC7->C7_QUANT - SC7->C7_QUJE - SC7->C7_QTDACLA)
											nQuantConv := ConvUM(cProduto,nQtdVPed,nQtdVPed,2)
										Endif
									Endif
								Endif
							Endif 

							If !lA140IVPED
								a140VPed := {}

								//Se nQuantConv igual a zero, não foi usada 2a unidade de medida, portanto pega os valores da SC7.
								nQtdVPed := If(nQuantConv == 0, (SC7->C7_QUANT - SC7->C7_QUJE - SC7->C7_QTDACLA), nQuantConv)

								If ((nQuant - nQtdVPed) == 0 .Or. nQuant < nQtdVPed)
									aAdd(a140VPed,{cPedido,cItemPed,nQuant})
								Elseif nQuant > nQtdVPed
									aAdd(a140VPed,{cPedido,cItemPed,nQtdVPed})
									aAdd(a140VPed,{"","",nQuant - nQtdVPed})
								Endif
							Endif
						Else
							cPedido := Space(TamSx3("DT_PEDIDO")[1])
							cItemPed:= Space(TamSx3("DT_ITEMPC")[1])
						EndIf
					Else
						cPedido := Space(TamSx3("DT_PEDIDO")[1])
						cItemPed:= Space(TamSx3("DT_ITEMPC")[1])
					EndIf
				Else
					cPedido := Space(TamSx3("DT_PEDIDO")[1])
					cItemPed:= Space(TamSx3("DT_ITEMPC")[1])
				EndIf
				
				//Verifica NF Origem - NF de Complemento
				If cTipoNF == "C"
					If ValType(XmlChildEx(oXML:_INFNFE,"_IDE")) == "O"
						If ValType(XmlChildEx(oXML:_INFNFE:_IDE,"_NFREF")) == "O"
							If ValType(XmlChildEx(oXML:_INFNFE:_IDE:_NFREF,"_REFNFE")) == "O"
								cChvNFComp := PadR(oXML:_INFNFE:_IDE:_NFREF:_REFNFE:TEXT,TamSX3("F1_CHVNFE")[1])
								
								If !Empty(cChvNFComp)
									cNFOriComp		:= Posicione("SF1",8,xFilial("SF1") + cChvNFComp,"F1_DOC")
									cSerOriComp	:= Posicione("SF1",8,xFilial("SF1") + cChvNFComp,"F1_SERIE")
									cItOriComp		:= Posicione("SD1",1,xFilial("SD1") + cNFOriComp + cSerOriComp + cCodigo + cLoja + cProduto,"D1_ITEM")
								Endif
							Endif
						Endif
					Endif		
				Endif
			EndIf
			
			//Verifica NF Origem - NF de Devolução
			If lProces .And. cTipoNF == "D" 
				lDelRefDev := .F.
				nTamF1Chv  := TamSX3("F1_CHVNFE")[1]
				If ValType(XmlChildEx(oXML:_INFNFE,"_IDE")) == "O"
					If ValType(XmlChildEx(oXML:_INFNFE:_IDE,"_NFREF")) == "O"
						If ValType(XmlChildEx(oXML:_INFNFE:_IDE:_NFREF,"_REFNFE")) == "O"
							aRefDev := {PadR(oXML:_INFNFE:_IDE:_NFREF:_REFNFE:TEXT,nTamF1Chv)}
						Endif
					Elseif ValType(XmlChildEx(oXML:_INFNFE:_IDE,"_NFREF")) == "A"
						If nX == 1
						   For nA := 1 To Len(oXML:_INFNFE:_IDE:_NFREF)
								If ValType(XmlChildEx(oXML:_INFNFE:_IDE:_NFREF[nA],"_REFNFE")) == "O"
									aAdd(aRefDev,PadR(oXML:_INFNFE:_IDE:_NFREF[nA]:_REFNFE:TEXT,nTamF1Chv))
								Endif
							Next nA
						Endif
					Endif
				Endif

				If Len(aRefDev) > 0

					cChvNFEIn := ""
					For nY := 1 To Len(aRefDev)
						cChvNFEIn += Iif(nY > 1,",","")+"'"+aRefDev[nY]+"'"
					Next nY

				
					SF2->(dbClearFilter())
					SF2->(dbSetOrder(1))
					
					cAliasTmp := GetNextAlias()
					
					cQuery := " SELECT F2_DOC, F2_SERIE, D2_ITEM "
					cQuery += " FROM " + RetSqlName("SF2") + " SF2 "
					cQuery += " JOIN " + RetSqlName("SD2") + " SD2 "
					cQuery += " ON D2_FILIAL = F2_FILIAL"
					cQuery += " AND D2_DOC = F2_DOC"
					cQuery += " AND D2_SERIE = F2_SERIE"
					cQuery += " AND D2_CLIENTE = F2_CLIENTE"
					cQuery += " AND D2_LOJA = F2_LOJA"
					cQuery += " AND D2_COD = '" + cProduto + "'"  	
					cQuery += " AND SD2.D_E_L_E_T_ = ' '"
					cQuery += " WHERE SF2.D_E_L_E_T_ = ' ' AND"
					cQuery += " F2_CHVNFE IN ( " + cChvNFEIn + " ) AND"
					cQuery += " F2_FILIAL = '" + xFilial("SF2") + "'"  	
					cQuery := ChangeQuery(cQuery)
					
					dbUseArea(.T., "TOPCONN", TCGenQry(,,cQuery),cAliasTmp, .T., .T.)
					Count to nTotReg
					(cAliasTmp)->(DbGoTop())
					If nTotReg < 2 //Se o produto existir em mais de uma NF, não deverá ser vinculado. O vínculo deverá ser feito manualmente.
						If (cAliasTmp)->(!Eof())
							cNFOriComp	:= (cAliasTmp)->F2_DOC
							cSerOriComp	:= (cAliasTmp)->F2_SERIE
							cItOriComp := (cAliasTmp)->D2_ITEM
						EndIf
					Endif
					(cAliasTmp)->(dbCloseArea())
				Endif
	
			Endif

		    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Verifica se existe a Tag para códido do FCI                 ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			cFciCod := ""
			If lProces .and. ValType(XmlChildEx(aItens[nX]:_Prod,"_NFCI")) == "O"
				cFciCod := aItens[nX]:_Prod:_nFCI:Text
				If Len(cFciCod) > nTamFCI
					cFciCod := RIGHT(cFciCod,nTamFci)
				Else
					cFciCod := PADR(cFciCod,nTamFci)
				EndIf
			EndIf

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Informacoes de Lote e Validade do Lote                          ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If lProces 
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_RASTRO")) == "O"
					cLote		:= aItens[nX]:_Prod:_Rastro:_nLote:Text
					dValidLote	:= StoD(StrTran(AllTrim(aItens[nX]:_Prod:_Rastro:_dVal:Text),"-",""))
					dFabLote	:= StoD(StrTran(AllTrim(aItens[nX]:_Prod:_Rastro:_dFab:Text),"-",""))		
				ElseIf ValType(XmlChildEx(aItens[nX]:_Prod,"_RASTRO")) == "A"
					//a140Rastro
					//01 - Produto
					//02 - Codigo do lote
					//03 - Quantidade do lote
					//04 - Validade do lote
					//05 - Fabricação do lote
					//06 - Frete
					//07 - Despesas
					//08 - Seguro
					//09 - Desconto
					//10 - IPI
					//11 - ICMS
					//12 - ISS
					//13 - PIS
					//14 - COFINS
					//15 - ICMS ST
					//16 - Base FCP
					//17 - Valor FCP
					
					nQtdRastro := 0
					For nZ := 1 To Len(XmlChildEx(aItens[nX]:_Prod,"_RASTRO"))
						//Validar se há lotes iguais, se houver faz aglutinação
						If !lGrava
							nPosRast := aScan(a140Rastro,{|x| x[1][1] + x[2][1] == cProduto + aItens[nX]:_Prod:_Rastro[nZ]:_nLote:Text})
							If nPosRast > 0
								lGrava := .F. 
							Else 
								lGrava := .T. 
							EndIf						
						EndIf

						If lGrava
							aAdd(a140Rastro,{{cProduto                                                                 },; //Codigo do produto
											{aItens[nX]:_Prod:_Rastro[nZ]:_nLote:Text							       },; //Codigo do Lote
											{Val(aItens[nX]:_Prod:_Rastro[nZ]:_qLote:Text)							   },; //Quantidade do Lote
											{StoD(StrTran(AllTrim(aItens[nX]:_Prod:_Rastro[nZ]:_dVal:Text),"-",""))    },; //Validade do Lote
											{StoD(StrTran(AllTrim(aItens[nX]:_Prod:_Rastro[nZ]:_dFab:Text),"-",""))    }}) //Fabricacao do Lote
							nQtdRastro += Val(aItens[nX]:_Prod:_Rastro[nZ]:_qLote:Text)
						Else 
							a140Rastro[nPosRast][3][1] += Val(aItens[nX]:_Prod:_Rastro[nZ]:_qLote:Text)//Soma quantidade do lote 
							nQtdRastro += Val(aItens[nX]:_Prod:_Rastro[nZ]:_qLote:Text)//Atualiza quantidade do rastro
						EndIf
					
						lGrava := .F.
					Next nZ
					
					//Adiciona produto sem lote, pois quantidades informada nos lotes não bate com quantidade recebida.
					If nQtdRastro < nQuant
						aAdd(a140Rastro,{{cProduto              },; //Codigo do produto
										{""						},; //Codigo do Lote
										{nQuant - nQtdRastro	},; //Quantidade do Lote
										{CtoD("//")    			},; //Validade do Lote
										{CtoD("//")    			}}) //Fabricacao do Lote
					Endif
				ElseIf ValType(XmlChildEx(aItens[nX]:_Prod,"_MED")) == "O"
					If ValType(XmlChildEx(aItens[nX]:_Prod:_MED,"_NLOTE")) == "O"
						cLote		:= aItens[nX]:_Prod:_Med:_Nlote:Text
					Endif

					If ValType(XmlChildEx(aItens[nX]:_Prod:_MED,"_DVAL")) == "O"
						dValidLote	:= StoD(StrTran(AllTrim(aItens[nX]:_Prod:_Med:_Dval:Text),"-","")) 
					Endif
				Else
					cLote		:= "" 
					dValidLote	:= CtoD("//")
					dFabLote	:= CtoD("//")
				EndIf
			EndIf

			If !lNFeTransp .And. lProces
				//Verifica se existe a Tag para os valores de frete/seguro/despesa³
				nFretItem  := 0
				nDespItem  := 0
				nSegItem   := 0    
				nDescItem  := 0
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_VFRETE")) == "O"
					nFretItem := Val(aItens[nX]:_Prod:_vFrete:Text)
				EndIf
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_VOUTRO")) == "O"
					nDespItem := Val(aItens[nX]:_Prod:_vOutro:Text)
				EndIf
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_VSEG")) == "O"
					nSegItem := Val(aItens[nX]:_Prod:_vSeg:Text)
				EndIf
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_VDESC")) == "O"
					nDescItem := Val(aItens[nX]:_Prod:_vDesc:Text)
				EndIf
				
				//Proporcionaliza Frete, Despesas, Seguro e Desconto conforme os itens de Lote do Xml
				If Len(a140rastro) > 0
					For nZ := 1 to len(a140rastro)
						nFretRast := nFretItem * a140rastro[nZ,3,1] / nQuant 
							aAdd(a140rastro[Nz],{nFretRast})
			
						nDespRast := nDespItem * a140rastro[nZ,3,1] / nQuant 
							aAdd(a140rastro[Nz],{nDespRast})
				
						nSeguRast := nSegItem * a140rastro[nZ,3,1] / nQuant 
							aAdd(a140rastro[Nz],{nSeguRast})
				
						nDescRast := nDescItem * a140rastro[nZ,3,1] / nQuant 
							aAdd(a140rastro[Nz],{nDescRast})
					Next nZ	  
				EndIf		
						
				cCfop := 'N'
				If aItens[nX]:_PROD:_CFOP:TEXT $ cNFECFND
					cCfop:='S'
				EndIF
			 	cCodCFOP := ""
				If !Empty(aItens[nX]:_PROD:_CFOP:TEXT)
					cCodCFOP := aItens[nX]:_PROD:_CFOP:TEXT
				EndIF
				
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Verifica se existe a Tag para os valores de impostos. ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				nIPIItem  := 0
				nICMItem  := 0
				nISSItem  := 0    
				nPISItem  := 0
				nCOFItem  := 0
				nIMCSTIt  := 0
				
				nAlIPIItem  := 0
				nAlICMItem  := 0
				nAlISSItem  := 0    
				nAlPISItem  := 0
				nALCOFItem  := 0
				nALIMCSTIt  := 0
				
				nBCFCPSTRet := 0
				nPFCPSTRet  := 0
				nVFCPSTRet  := 0
				
				nBCFCPST := 0
				nPFCPST  := 0
				nVFCPST  := 0
				
				nVICMSSTRet	:= 0 //Valor ICMS ST Ret
				nBICMSSTRet	:= 0 //Base ICMS ST Ret
				nAICMSSTRet	:= 0 //Aliquota ICMS ST Ret
				
				//--IPI
				If ValType(XmlChildEx(aItens[nX]:_Imposto,"_IPI")) == "O"
					If ValType(XmlChildEx(aItens[nX]:_Imposto:_IPI,"_IPITRIB")) == "O"
						// Verifica as TAGS do imposto IPI, pois ha XML que vem somente com 1 das TAGS abaixo.
						If ValType(XmlChildEx(aItens[nX]:_Imposto:_IPI:_IPITrib,"_VIPI")) == "O"
							nIPIItem := Val(aItens[nX]:_Imposto:_IPI:_IPITrib:_vIPI:Text)
						EndIf
						
						If ValType(XmlChildEx(aItens[nX]:_Imposto:_IPI:_IPITrib,"_PIPI")) == "O"
							nAlIPIItem := Val(aItens[nX]:_Imposto:_IPI:_IPITrib:_pIPI:Text)
						EndIf
					Endif
				EndIf
				//--ICMS
				If ValType(XmlChildEx(aItens[nX]:_Imposto,"_ICMS")) == "O"
					If ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS00")) == "O"
						nICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS00,"_VICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS00:_vICMS:Text), 0)
						nAlICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS00,"_PICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS00:_pICMS:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS00,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS00:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS00,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS00:_CST:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS10")) == "O"
						nICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_VICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS10:_vICMS:Text), 0)
						nAlICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_PICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS10:_pICMS:Text), 0)
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_VICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS10:_vICMSST:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_PICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS10:_pICMSST:Text), 0)
						nBCFCPST 	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_VBCFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS10:_VBCFCPST:Text), 0)
						nPFCPST  	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_PFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS10:_PFCPST:Text), 0)
						nVFCPST  	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_VFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS10:_VFCPST:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS10:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS10,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS10:_CST:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS20")) == "O"
						nICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS20,"_VICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS20:_vICMS:Text), 0)
						nAlICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS20,"_PICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS20:_pICMS:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS20,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS20:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS20,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS20:_CST:Text,"")
						nICMDeson	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS20,"_VICMSDESON")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS20:_vICMSDeson:Text), 0)
						cICMDesMot	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS20,"_MOTDESICMS")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS20:_motDesICMS:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS30")) == "O"
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_VICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS30:_vICMSST:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_PICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS30:_pICMSST:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS30:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS30:_CST:Text,"")
						nICMDeson	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_VICMSDESON")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS30:_vICMSDeson:Text), 0)
						cICMDesMot	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_MOTDESICMS")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS30:_motDesICMS:Text,"")
						nBCFCPST 	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_VBCFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS30:_VBCFCPST:Text), 0)
						nPFCPST  	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_PFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS30:_PFCPST:Text), 0)
						nVFCPST  	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS30,"_VFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS30:_VFCPST:Text), 0)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS40")) == "O"
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS40,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS40:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS40,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS40:_CST:Text,"")
						nICMDeson	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS40,"_VICMSDESON")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS40:_vICMSDeson:Text), 0)
						cICMDesMot	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS40,"_MOTDESICMS")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS40:_motDesICMS:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS41")) == "O"
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS41,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS41:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS41,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS41:_CST:Text,"")
						nICMDeson	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS41,"_VICMSDESON")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS41:_vICMSDeson:Text), 0)
						cICMDesMot	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS41,"_MOTDESICMS")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS41:_motDesICMS:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS50")) == "O"
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS50,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS50:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS50,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS50:_CST:Text,"")
						nICMDeson	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS50,"_VICMSDESON")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS50:_vICMSDeson:Text), 0)
						cICMDesMot	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS50,"_MOTDESICMS")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS50:_motDesICMS:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS51")) == "O"
						nICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS51,"_VICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS51:_vICMS:Text), 0)
						nAlICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS51,"_PICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS51:_pICMS:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS51,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS51:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS51,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS51:_CST:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS60")) == "O"
						nBCFCPSTRet := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_VBCFCPSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS60:_vBCFCPSTRet:Text), 0)
						nPFCPSTRet  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_PFCPSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS60:_pFCPSTRet:Text), 0)
						nVFCPSTRet  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_VFCPSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS60:_vFCPSTRet:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS60:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS60:_CST:Text,"")
						nVICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_VICMSSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS60:_vICMSSTRet:Text), 0)
						nBICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_VBCSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS60:_vBCSTRet:Text), 0)
						nAICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS60,"_PST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS60:_pST:Text), 0)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS70")) == "O"
						nICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_VICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_vICMS:Text), 0)
						nAlICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_PICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_pICMS:Text), 0)
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_VICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_vICMSST:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_PICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_pICMSST:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS70:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS70:_CST:Text,"")
						nICMDeson	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_VICMSDESON")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_vICMSDeson:Text), 0)
						cICMDesMot	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_MOTDESICMS")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS70:_motDesICMS:Text,"")
						nBCFCPST 	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_VBCFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_VBCFCPST:Text), 0)
						nPFCPST  	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_PFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_PFCPST:Text), 0)
						nVFCPST  	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS70,"_VFCPST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS70:_VFCPST:Text), 0)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMS90")) == "O"
						nICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_VICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS90:_vICMS:Text), 0)
						nAlICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_PICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS90:_pICMS:Text), 0)	
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_VICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS90:_vICMSST:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_PICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS90:_pICMSST:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS90:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS90:_CST:Text,"")
						nICMDeson	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_VICMSDESON")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMS90:_vICMSDeson:Text), 0)
						cICMDesMot	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMS90,"_MOTDESICMS")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMS90:_motDesICMS:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMSPART")) == "O"
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSPART,"_VICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSPART:_vICMSST:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSPART,"_PICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSPART:_pICMSST:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSPART,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMSPART:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSPART,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMSPART:_CST:Text,"")
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMSST")) == "O" 
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSST,"_VICMSSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSST:_vICMSSTRet:Text), 0)
						cOrigClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSST,"_ORIG")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMSST:_Orig:Text,"")
						cCSTClas	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSST,"_CST")) == "O", aItens[nX]:_Imposto:_ICMS:_ICMSST:_CST:Text,"")
						nVICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSST,"_VICMSSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSST:_vICMSSTRet:Text), 0)
						nBICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSST,"_VBCSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSST:_vBCSTRet:Text), 0)
						nAICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSST,"_PST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSST:_pST:Text), 0) 
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMSSN201")) == "O"	
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN201,"_VICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN201:_vICMSST:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN201,"_PICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN201:_pICMSST:Text), 0)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMSSN202")) == "O"
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN202,"_VICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN202:_vICMSST:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN202,"_PICMSST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN202:_pICMSST:Text), 0)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMSSN500")) == "O"	
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN500,"_VICMSSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN500:_vICMSSTRet:Text), 0)
						nBCFCPSTRet := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN500,"_VBCFCPSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN500:_vBCFCPSTRet:Text), 0)
						nPFCPSTRet  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN500,"_PFCPSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN500:_pFCPSTRet:Text), 0)
						nVFCPSTRet  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN500,"_VFCPSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN500:_vFCPSTRet:Text), 0)
						nVICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN500,"_VICMSSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN500:_vICMSSTRet:Text), 0)
						nBICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN500,"_VBCSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN500:_vBCSTRet:Text), 0)
						nAICMSSTRet	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN500,"_PST")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN500:_pST:Text), 0)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS,"_ICMSSN900")) == "O"
						nICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN900,"_VICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN900:_vICMS:Text), 0)
						nAlICMItem	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN900,"_PICMS")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN900:_pICMS:Text), 0)	
						nIMCSTIt	:= If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN900,"_VICMSSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN900:_vICMSSTRet:Text), 0)
						nALIMCSTIt  := If(ValType(XmlChildEx(aItens[nX]:_Imposto:_ICMS:_ICMSSN900,"_PICMSSTRET")) == "O", Val(aItens[nX]:_Imposto:_ICMS:_ICMSSN900:_pICMSSTRet:Text), 0)
					EndIf
				EndIf
				
				If !Empty(cOrigClas) .And. !Empty(cCSTClas)
					If Empty(cMVClasFis)
						cClasFis := cOrigClas+cCSTClas
					Else
						//Conversão a partir do parametro MV_COLCFIS
						aClasFis := Separa(cMVClasFis,"|")
						
						nClasFis := aScan(aClasFis,{|x| SubStr(x,1,1) == cOrigClas})
						If nClasFis > 0
							cClasFis := SubStr(aClasFis[nClasFis],3,1) + cCSTClas 
						Endif
					Endif
				Endif 

				//--PIS
				If ValType(XmlChildEx(aItens[nX]:_Imposto,"_PIS")) == "O"
					If ValType(XmlChildEx(aItens[nX]:_Imposto:_PIS,"_PISALIQ")) == "O"  
						nPISItem := Val(aItens[nX]:_Imposto:_PIS:_PISAliq:_vPIS:Text)
						nAlPISItem := Val(aItens[nX]:_Imposto:_PIS:_PISAliq:_pPIS:Text)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_PIS,"_PISQTDE")) == "O"
						nPISItem := Val(aItens[nX]:_Imposto:_PIS:_PISQtde:_vPIS:Text)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_PIS,"_PISOUTR")) == "O"
						nPISItem := Val(aItens[nX]:_Imposto:_PIS:_PISOutr:_vPIS:Text)
						If ValType(XmlChildEx(aItens[nX]:_Imposto:_PIS:_PISOutr,"_PPIS")) == "O"
							nAlPISItem := Val(aItens[nX]:_Imposto:_PIS:_PISOutr:_pPIS:Text)
						ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_PIS:_PISOutr,"_VALIQPROD")) == "O"
							nAlPISItem := Val(aItens[nX]:_Imposto:_PIS:_PISOutr:_vAliqProd:Text)
						EndIf
					Endif
				EndIf
				
				//--COFINS
				If ValType(XmlChildEx(aItens[nX]:_Imposto,"_COFINS")) == "O"
					If ValType(XmlChildEx(aItens[nX]:_Imposto:_COFINS,"_COFINSALIQ")) == "O"
						nCOFItem := Val(aItens[nX]:_Imposto:_COFINS:_COFINSAliq:_vCOFINS:Text)
						nAlCOFItem := Val(aItens[nX]:_Imposto:_COFINS:_COFINSAliq:_pCOFINS:Text)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_COFINS,"_COFINSQTDE")) == "O"
						nCOFItem := Val(aItens[nX]:_Imposto:_COFINS:_COFINSQtde:_vCOFINS:Text)
					ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_COFINS,"_COFINSOUTR")) == "O"
						nCOFItem := Val(aItens[nX]:_Imposto:_COFINS:_COFINSOutr:_vCOFINS:Text)
						If ValType(XmlChildEx(aItens[nX]:_Imposto:_COFINS:_COFINSOutr,"_PCOFINS")) == "O"
							nAlCOFItem := Val(aItens[nX]:_Imposto:_COFINS:_COFINSOutr:_pCOFINS:Text)
						ElseIf ValType(XmlChildEx(aItens[nX]:_Imposto:_COFINS:_COFINSOutr,"_VALIQPROD")) == "O"
							nAlCOFItem := Val(aItens[nX]:_Imposto:_COFINS:_COFINSOutr:_vAliqProd:Text)
						EndIf
					EndIf
				EndIf
				
				lProces := !COMXIMPVLD({{nAlICMItem,">=100"},{nALIMCSTIt,">=100"},{nAlPISItem,">=100"},{nAlCOFItem,">=100"}})
				
				If !lProces
					aAdd(aErros,{cFile,"COM043 - " + STR0247,STR0241})
					aAdd(aErroErp,{cFile,"COM043"})
				Endif
				
				//Dados dos Itens - SDT
				DbSelectArea("SDT")
				
				//Verifica Tag vProd
				If ValType(XmlChildEx(aItens[nX]:_Prod,"_VPROD")) == "O" 
					nTotItem := Val(aItens[nX]:_Prod:_vProd:Text)
				EndIf
				
				//Proporcionaliza IPI, ICMS, ISS, PIS, COFINS, ICMS ST, Base FCP e Valor FCP conforme os itens de Lote do Xml
				If Len(a140Rastro) > 0
					nTotIPI := nIPIItem //IPI
					nTotICM := nICMItem //ICMS
					nTotISS := nISSItem //ISS
					nTotPIS := nPISItem //PIS
					nTotCOF := nCOFItem //COFINS
					nTotCST := nIMCSTIt //ICMS ST
					
					If lFCPAnt
						nTotFCPB := nBCFCPSTRet //Base FCP
						nTotFCPV := nVFCPSTRet //Valor FCP
					Endif
					
					If lFCPST
						nTotBFCPST := nBCFCPST
						nTotVFCPST := nVFCPST
					Endif
					
					If lICMSSTRet
						nTotBICSTRET := nBICMSSTRet
						nTotVICSTRET := nVICMSSTRet
					Endif

					If lDTICMDeson
						nTotICMDeson := nICMDeson
					Endif
					
					For nI := 1 To Len(a140Rastro)
						nRastPorc := a140Rastro[nI,3,1] * 100 / nQuant
						
						If Len(a140Rastro) == 1 
							aAdd(a140rastro[nI],{nIPIItem})
							aAdd(a140rastro[nI],{nICMItem})
							aAdd(a140rastro[nI],{nISSItem})
							aAdd(a140rastro[nI],{nPISItem})
							aAdd(a140rastro[nI],{nCOFItem})
							aAdd(a140rastro[nI],{nIMCSTIt})
							
							If lFCPAnt
								aAdd(a140rastro[nI],{nBCFCPSTRet})
								aAdd(a140rastro[nI],{nVFCPSTRet})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif
							
							If lFCPST
								aAdd(a140rastro[nI],{nBCFCPST})
								aAdd(a140rastro[nI],{nVFCPST})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif
							
							If lICMSSTRet
								aAdd(a140rastro[nI],{nBICMSSTRet})
								aAdd(a140rastro[nI],{nVICMSSTRet})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif

							If lDTICMDeson
								aAdd(a140rastro[nI],{nICMDeson})
								aAdd(a140rastro[nI],{cICMDesMot})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif
						Else
							//IPI
							nRatImp := nTotIPI * nRastPorc / 100
						
							nIPIItem -= nRatImp
							aAdd(a140rastro[nI],{nRatImp})
							
							//ICMS
							nRatImp := nTotICM * nRastPorc / 100
						
							nICMItem -= nRatImp
							aAdd(a140rastro[nI],{nRatImp})
							
							//ISS
							nRatImp := nTotISS * nRastPorc / 100
						
							nISSItem -= nRatImp
							aAdd(a140rastro[nI],{nRatImp})
							
							//PIS
							nRatImp := nTotPIS * nRastPorc / 100
						
							nPISItem -= nRatImp
							aAdd(a140rastro[nI],{nRatImp})
							
							//COFINS
							nRatImp := nTotCOF * nRastPorc / 100
						
							nCOFItem -= nRatImp
							aAdd(a140rastro[nI],{nRatImp})
							
							//ICMS ST
							nRatImp := nTotCST * nRastPorc / 100
						
							nIMCSTIt -= nRatImp
							aAdd(a140rastro[nI],{nRatImp})
							
							If lFCPAnt
								//Base FCP
								nRatImp := nTotFCPB * nRastPorc / 100
							
								nBCFCPSTRet -= nRatImp
								aAdd(a140rastro[nI],{nRatImp})
								
								//Valor FCP
								nRatImp := nTotFCPV * nRastPorc / 100
							
								nVFCPSTRet -= nRatImp
								aAdd(a140rastro[nI],{nRatImp})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif
							
							If lFCPST
								//Base FCP ST
								nRatImp := nTotBFCPST * nRastPorc / 100
							
								nBCFCPST -= nRatImp
								aAdd(a140rastro[nI],{nRatImp})
								
								//Valor FCP ST
								nRatImp := nTotVFCPST * nRastPorc / 100
							
								nVFCPST -= nRatImp
								aAdd(a140rastro[nI],{nRatImp})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif
							
							If lICMSSTRet
								//Base ICMS ST Ret
								nRatImp := nTotBICSTRET * nRastPorc / 100
							
								nBICMSSTRet -= nRatImp
								aAdd(a140rastro[nI],{nRatImp})
								
								//Valor ICMS ST Ret
								nRatImp := nTotVICSTRET * nRastPorc / 100
							
								nVICMSSTRet -= nRatImp
								aAdd(a140rastro[nI],{nRatImp})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif

							If lDTICMDeson
								nRatImp := nTotICMDeson * nRastPorc / 100
							
								nICMDeson -= nRatImp
								aAdd(a140rastro[nI],{nRatImp})
								aAdd(a140rastro[nI],{cICMDesMot})
							Else
								aAdd(a140rastro[nI],{0})
								aAdd(a140rastro[nI],{0})
							Endif
						Endif						
					Next nI	
				Endif	
				
				//DADOS DO PRODUTO 
				If !Empty(cPedido) .And. !Empty(cItemPed) .And. l140VPed .And. Len(a140Rastro) == 0
					For nI := 1 To Len(a140VPed)
						lConvUM	:= .F.
						nQtdeIt	:= a140VPed[nI,3]
						nPrcIt	:= IIF(cTipoNF == "C",Val(aItens[nX]:_Prod:_vProd:Text),nPrecUni)
						nTotIt	:= IIF(cTipoNF == "C",Val(aItens[nX]:_Prod:_vProd:Text),nQtdeIt * nPrcIt ) 
						
						if lCsdXml .and. cTipoNF == "N"
							nQtXML   := nQtdeIt
							cUmCom   := GetAdvFVal("SA5","A5_UNID",fwxFilial("SA5")+cCodigo+cLoja+cProduto,1)
							cUM		 := GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
							nQtdeIt  := EstConvUM(cProduto,cUmCom,nQtdeIt)
							nPrcIt	 := nTotIt / nQtdeIt
							if nQtdeIt == 0
								lProces := .F.
								//"Não há cadastro de conversão da unidade " # " para o produto " # ". O cadastro é obrigatório quando MV_CSDXML = .T." # "Não há cadastro de conversão para este produto"
								aAdd(aErros,{cFile,"COM053 - " + STR0256 + cUmCom + STR0257 + Alltrim(cProduto) + STR0258,STR0259})
								aAdd(aErroErp,{cFile,"COM053"})
							endif
						
						elseif lUnidMed
							If cTipoNF $ "BD"
								lConvUM := GetAdvFVal("SA7","A7_UMNFE",xFilial("SA7")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
							Else
								lConvUM := GetAdvFVal("SA5","A5_UMNFE",xFilial("SA5")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
							Endif
							
							cUM			:= GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
							cSEGUM		:= GetAdvFVal("SB1","B1_SEGUM",xFilial("SB1")+cProduto,1)
							nQtSEGUM	:= 0
							lFatorConv	:= COLVLSEGUM(cProduto,cSEGUM)

							If !Empty(cSEGUM)
								If lConvUM
									//Produto não possui fator de conversão e não tem como converter para primeira
									//unidade de medida
									If !lFatorConv
										lProces := .F.
										aAdd(aErros,{cFile,"COM050 - " + STR0253 + cProduto ,STR0198}) //"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
										aAdd(aErroErp,{cFile,"COM050"})
									Else
										nQtSEGUM := nQtdeIt
										nQtdeIt	 := ConvUM(cProduto,nQtdeIt,nQtdeIt,1)
										nPrcIt	 := nTotIt / nQtdeIt
									Endif
								Else
									nQtSEGUM := Iif(lFatorConv,ConvUM(cProduto,nQtdeIt,nQtdeIt,2),0)
								Endif
							Endif
						Endif
						
						If lA140IQTD
							aA140IQTD := ExecBlock("A140IQTD",.F.,.F.,{cProduto,cUM,cSEGUM,nQtSEGUM,nQtdeIt,nPrcIt,nTotIt,lConvUM,cCodigo,cLoja,cDoc,cSerie,cTipoNF,Iif(cTipoNF $ "BD",.T.,.F.),oXML})
							If ValType(aA140IQTD) == "A" .And. Len(aA140IQTD) == 4
								nQtdeIt	 := aA140IQTD[1]
								nPrcIt	 := aA140IQTD[2]
								nTotIt	 := aA140IQTD[3]
								nQtSEGUM := aA140IQTD[4]
							EndIf							
						EndIf						
						
						aAdd(aItemSDT,{{"DT_FILIAL" 	,xFilial("SDT")														},; //Filial
										 {"DT_CNPJ"		,cCGC																},; //CGC
					 					 {"DT_COD"		,cProduto															},; //Codigo do produto
					 					 {"DT_PRODFOR"	,aItens[nX]:_PROD:_CPROD:TEXT										},; //Cdgo do pduto do Fornecedor
				 						 {"DT_DESCFOR"	,aItens[nX]:_PROD:_XPROD:TEXT										},; //Dcao do pduto do Fornecedor
				 						 {"DT_ITEM"   	,PadL(Len(aItemSDT)+1,TamSX3("D1_ITEM")[1],"0")						},; //Item
				 						 {"DT_QUANT"  	,nQtdeIt															},; //Qtde
					 					 {"DT_VUNIT"	,nPrcIt																},; //Vlor Unitário
					 					 {"DT_FORNEC"	,cCodigo															},; //Forncedor
		  					 			 {"DT_LOJA"   	,cLoja																},; //Lja
						 				 {"DT_DOC"    	,cDoc																},; //DocmTo
				 					 	 {"DT_SERIE"	,cSerie							   									},; //Serie
				 						 {"DT_TOTAL"	,nTotIt																},; //Valor Total
				 						 {"DT_PEDIDO"	,a140VPed[nI,1]							   							},; //Pedido
				 						 {"DT_ITEMPC"	,a140VPed[nI,2]								  						},; //Item do pedido
				 						 {"DT_CFOP"		,cCFOP										  						},; //CFOP
				 						 {"DT_LOTE"		,cLote										  						},; // Lote
				 						 {"DT_DTVALID"	,dValidLote								  							},; // Validade do Lote
				 						 {"DT_FCICOD"	,cFciCod															}})	//Codigo FCI (alteração)
	 									 
										 If cTipoNF $ "CD" .And. !Empty(cNFOriComp) .And. !Empty(cSerOriComp) .And. !Empty(cItOriComp)
										 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_NFORI"	, cNFOriComp}) // NF Origem
						 					aAdd(aItemSDT[Len(aItemSDT)],{"DT_SERIORI", cSerOriComp}) // Serie Origem
						 					aAdd(aItemSDT[Len(aItemSDT)],{"DT_ITEMORI", cItOriComp}) // Item Origem
						 				 Endif

										 if lCsdXML
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_ITXML"	, STRZERO(VAL(aItens[nX]:_NITEM:TEXT),TamSX3("DKA_ITXML")[1])}) // ITEM DO XML
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_UMXML"	, cUmCom}) // Unidade de medida tributária
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTDXML"	, nQtXML}) // Qtd do XML
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_FATOR"	, GetAdvFVal("D3Q","D3Q_FATOR",fwxFilial("D3Q") + cProduto + cUmCom ,1)}) // Fator de conversão
										endif

										 nVIPIRat 	:= nIPIItem
										 nVIcmRat 	:= nICMItem
										 nVISSRat 	:= nISSItem
										 nVPISRat 	:= nPISItem
										 nVCOFRat 	:= nCOFItem
										 nVCSTRat 	:= nIMCSTIt
										 nFretRast	:= nFretItem
						 				 nDespRast	:= nDespItem
										 nSeguRast	:= nSegItem
										 nDescRast 	:= nDescItem

										 If Len(a140VPed) > 1
										 		//rateio dos impostos 
												nVIPIRat := nIPIItem / nQuant * nQtdeIt
												nVIcmRat := nICMItem / nQuant * nQtdeIt
												nVISSRat := nISSItem / nQuant * nQtdeIt
												nVPISRat := nPISItem / nQuant * nQtdeIt
												nVCOFRat := nCOFItem / nQuant * nQtdeIt
												nVCSTRat := nIMCSTIt / nQuant * nQtdeIt

												//rateio de frete, despesa, seguro e desconto
												nFretRast := nFretItem / nQuant * nQtdeIt
												nDespRast := nDespItem / nQuant * nQtdeIt
												nSeguRast := nSegItem  / nQuant * nQtdeIt
												nDescRast := nDescItem / nQuant * nQtdeIt
										 Endif

										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_VALFRE" 	, nFretRast})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_DESPESA" , nDespRast})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_SEGURO"  , nSeguRast})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_VALDESC" , nDescRast})

	 									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_CODCFOP" , cCodCFOP})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLIPI"  , nVIPIRat})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLICM"  , nVIcmRat})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLISS"  , nVISSRat})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLPIS"  , nVPISRat})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLCOF"  , nVCOFRat})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLICST" , nVCSTRat})
										 
									 	 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQIPI"  , nAlIPIItem})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQICM"  , nAlICMItem})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQISS"  , nAlISSItem})
									  	 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQPIS"  , nAlPISItem})
	  									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQCOF"  , nAlCOFItem})
	  									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALICST"  , nALIMCSTIt})
	  									 
	  									 If SDT->(FieldPos("DT_DFABRIC")) > 0
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_DFABRIC"  , dFabLote})
	  									 Endif
	  									 	
	  									 If lFCPAnt
										 	If Len(a140VPed) > 1 
	  									 		aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPAN"  , nBCFCPSTRet / nQuant * nQtdeIt})
											Else
	  									 		aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPAN"  , nBCFCPSTRet})
											Endif
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XAFCPAN"  , nPFCPSTRet})
											If Len(a140VPed) > 1 
	  											aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPAN"  , nVFCPSTRet / nQuant * nQtdeIt})
											Else
												aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPAN"  , nVFCPSTRet})
											Endif
	  									 Endif
	  									 
	  									 If lFCPST
											If Len(a140VPed) > 1 
	  									 		aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPST"  , nBCFCPST / nQuant * nQtdeIt})
											Else
	  									 		aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPST"  , nBCFCPST})
	  										Endif
		  									aAdd(aItemSDT[Len(aItemSDT)],{"DT_XAFCPST"  , nPFCPST})
	  										If Len(a140VPed) > 1 
											  	aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPST"  , nVFCPST / nQuant * nQtdeIt})
											Else
											  	aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPST"  , nVFCPST})
											Endif
	  									 Endif
	  									 
	  									 If lDTClasFis .And. !Empty(cClasFis)
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_CLASFIS"  , cClasFis})
	  									 Endif
	  									 
	  									 If lICMSSTRet
										   	If Len(a140VPed) > 1
	  									 		aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMNDES"  , nVICMSSTRet / nQuant * nQtdeIt})
	  											aAdd(aItemSDT[Len(aItemSDT)],{"DT_BASNDES"  , nBICMSSTRet / nQuant * nQtdeIt})
											Else
												aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMNDES"  , nVICMSSTRet})
	  											aAdd(aItemSDT[Len(aItemSDT)],{"DT_BASNDES"  , nBICMSSTRet})
											Endif
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_ALQNDES"  , nAICMSSTRet})
	  									 Endif
	  									 
	  									 If lUnidMed
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_UM"  		, cUM})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_SEGUM"  	, cSEGUM})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTSEGUM"  , nQtSEGUM})
	  									 Endif

										 If lDTICMDeson
										 	If Len(a140VPed) > 1 
											 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMDES"  	, nICMDeson / nQuant * nQtdeIt})
											Else
												aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMDES"  	, nICMDeson})
											Endif
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMDEMT"  , cICMDesMot})
	  									 Endif
					Next nI
					
				ElseIf Len(a140Rastro) > 0
								
					For nI := 1 To Len(a140Rastro)
						lConvUM := .F.
						nQtdeIt	:= a140Rastro[nI,3,1]
						nQtXML  := nQtdeIt
						nPrcIt	:= IIF(cTipoNF == "C",Val(aItens[nX]:_Prod:_vProd:Text),nPrecUni)
						nTotIt	:= IIF(cTipoNF == "C",Val(aItens[nX]:_Prod:_vProd:Text), a140Rastro[nI,3,1] * nPrecUni)
						
						if lCsdXml .and. cTipoNF == "N"
							nQtXML  := nQtdeIt
							cUmCom   := GetAdvFVal("SA5","A5_UNID",fwxFilial("SA5")+cCodigo+cLoja+cProduto,1)
							cUM		 := GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
							nQtdeIt  := EstConvUM(cProduto,cUmCom,nQtdeIt)
							nPrcIt	 := nTotIt / nQtdeIt
							if nQtdeIt == 0
								lProces := .F.
								//"Não há cadastro de conversão da unidade " # " para o produto " # ". O cadastro é obrigatório quando MV_CSDXML = .T." # "Não há cadastro de conversão para este produto"
								aAdd(aErros,{cFile,"COM053 - " + STR0256 + cUmCom + STR0257 + Alltrim(cProduto) + STR0258,STR0259})
								aAdd(aErroErp,{cFile,"COM053"})
							endif
						
						elseif lUnidMed
							If cTipoNF $ "BD"
								lConvUM := GetAdvFVal("SA7","A7_UMNFE",xFilial("SA7")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
							Else
								lConvUM := GetAdvFVal("SA5","A5_UMNFE",xFilial("SA5")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
							Endif
							
							cUM			:= GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
							cSEGUM		:= GetAdvFVal("SB1","B1_SEGUM",xFilial("SB1")+cProduto,1)
							nQtSEGUM	:= 0
							lFatorConv	:= COLVLSEGUM(cProduto,cSEGUM)
							
							If !Empty(cSEGUM)
								If lConvUM
									//Produto não possui fator de conversão e não tem como converter para primeira
									//unidade de medida
									If !lFatorConv
										lProces := .F.
										aAdd(aErros,{cFile,"COM050 - " + STR0253 + cProduto ,STR0198}) //"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
										aAdd(aErroErp,{cFile,"COM050"})
									Else
										nQtSEGUM := nQtdeIt
										nQtdeIt	 := ConvUM(cProduto,nQtdeIt,nQtdeIt,1)
										nPrcIt	 := nTotIt / nQtdeIt
									Endif
								Else
									nQtSEGUM := Iif(lFatorConv,ConvUM(cProduto,nQtdeIt,nQtdeIt,2),0)
								Endif
							Endif
						Endif
						
						If lA140IQTD
							aA140IQTD := ExecBlock("A140IQTD",.F.,.F.,{cProduto,cUM,cSEGUM,nQtSEGUM,nQtdeIt,nPrcIt,nTotIt,lConvUM,cCodigo,cLoja,cDoc,cSerie,cTipoNF,Iif(cTipoNF $ "BD",.T.,.F.),oXML})
							If ValType(aA140IQTD) == "A" .And. Len(aA140IQTD) == 4
								nQtdeIt	 := aA140IQTD[1]
								nPrcIt	 := aA140IQTD[2]
								nTotIt	 := aA140IQTD[3]
								nQtSEGUM := aA140IQTD[4]
							EndIf							
						EndIf
												
						aAdd(aItemSDT,{{"DT_FILIAL" 	,xFilial("SDT")														        },; //Filial
										 {"DT_CNPJ"		,cCGC																	    },; //CGC
					 					 {"DT_COD"		,cProduto																	},; //Codigo do produto
					 					 {"DT_PRODFOR"	,aItens[nX]:_PROD:_CPROD:TEXT										        },; //Cdgo do pduto do Fornecedor
				 						 {"DT_DESCFOR"	,aItens[nX]:_PROD:_XPROD:TEXT										        },; //Dcao do pduto do Fornecedor
				 						 {"DT_ITEM"   	,PadL(Len(aItemSDT)+1,TamSX3("D1_ITEM")[1],"0")					            },; //Item
				 						 {"DT_QUANT"  	,nQtdeIt																	},; //Qtde
					 					 {"DT_VUNIT"	,nPrcIt             														},; //Valor Unitário
					 					 {"DT_FORNEC"	,cCodigo																    },; //Forncedor
		  					 			 {"DT_LOJA"   	,cLoja																	    },; //Loja
						 				 {"DT_DOC"    	,cDoc																	    },; //Documento
				 					 	 {"DT_SERIE"	,cSerie							   									        },; //Serie
					 					 {"DT_VALFRE"	,a140Rastro[nI,6,1]															},; //Valor Frete
				 						 {"DT_DESPESA"	,a140Rastro[nI,7,1]						   									},; //Valor Despesa
				 						 {"DT_SEGURO"	,a140Rastro[nI,8,1]								  							},; //Valor Seguro
				 						 {"DT_VALDESC"	,a140Rastro[nI,9,1]															},; //Valor Desconto
				 						 {"DT_TOTAL"	,nTotIt																		},; //Valor Total
				 						 {"DT_CFOP"		,cCFOP										  							    },; //CFOP
				 						 {"DT_LOTE"		,IIF(cTipoNF == "C","",a140Rastro[nI,2,1])									},; // Lote
				 						 {"DT_DTVALID"	,IIF(cTipoNF == "C",CTOD(""),a140Rastro[nI,4,1])							},; // Validade do Lote
				 						 {"DT_FCICOD"	,cFciCod																	}})	//Codigo FCI (alteração)
	 									 
										 If !Empty(cPedido) .And. !Empty(cItemPed)
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_PEDIDO"	,cPedido	}) //Pedido
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_ITEMPC"	,cItemPed	}) //Item do pedido
										 Endif

										 If cTipoNF $ "CD" .And. !Empty(cNFOriComp) .And. !Empty(cSerOriComp) .And. !Empty(cItOriComp)
										 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_NFORI"	, cNFOriComp}) // NF Origem
						 					aAdd(aItemSDT[Len(aItemSDT)],{"DT_SERIORI", cSerOriComp}) // Serie Origem
						 					aAdd(aItemSDT[Len(aItemSDT)],{"DT_ITEMORI", cItOriComp}) // Item Origem
						 				 Endif

										 if lCsdXML
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_ITXML"	, STRZERO(VAL(aItens[nX]:_NITEM:TEXT),TamSX3("DKA_ITXML")[1])}) // ITEM DO XML
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_UMXML"	, cUmCom}) // Unidade tributária
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTDXML"	, nQtXML}) // Quantidade tributária
											aAdd(aItemSDT[Len(aItemSDT)],{"DT_FATOR"	, GetAdvFVal("D3Q","D3Q_FATOR",fwxFilial("D3Q") + cProduto + cUmCom,1)}) // Fator de conversão
										 endif
						 				 
	 									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_CODCFOP"  , cCodCFOP})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLIPI"  , a140Rastro[nI,10,1]})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLICM"  , a140Rastro[nI,11,1]})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLISS"  , a140Rastro[nI,12,1]})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLPIS"  , a140Rastro[nI,13,1]})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLCOF"  , a140Rastro[nI,14,1]})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLICST" , a140Rastro[nI,15,1]})
										 
									 	 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQIPI"  , nAlIPIItem})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQICM"  , nAlICMItem})
										 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQISS"  , nAlISSItem}) 
									  	 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQPIS"  , nAlPISItem})
	  									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQCOF"  , nAlCOFItem})
	  									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALICST"  , nALIMCSTIt})
	  									 
	  									 If SDT->(FieldPos("DT_DFABRIC")) > 0 
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_DFABRIC"  , a140Rastro[nI,5,1]})
	  									 Endif
	  									 	
	  									 If lFCPAnt
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPAN"  , a140Rastro[nI,16,1]})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XAFCPAN"  , nPFCPSTRet})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPAN"  , a140Rastro[nI,17,1]})
	  									 Endif
	  									 
	  									 If lFCPST
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPST"  , a140Rastro[nI,18,1]})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XAFCPST"  , nPFCPST})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPST"  , a140Rastro[nI,19,1]})
	  									 Endif
	  									 
	  									 If lICMSSTRet
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMNDES"  , a140Rastro[nI,21,1]})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_BASNDES"  , a140Rastro[nI,20,1]})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_ALQNDES"  , nAICMSSTRet})
	  									 Endif
	  									 
	  									 If lDTClasFis .And. !Empty(cClasFis)
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_CLASFIS"  , cClasFis})
	  									 Endif
	  									 
	  									 If lUnidMed
	  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_UM"  		, cUM})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_SEGUM"  	, cSEGUM})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTSEGUM"  , nQtSEGUM})
	  									 Endif
										 
										 If lDTICMDeson
										 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMDES"  	, a140Rastro[nI,22,1]})
	  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMDEMT"  , a140Rastro[nI,23,1]})
	  									 Endif				
					Next nI
					
					a140Rastro := {}
					
				ElseIf !l140VPed
					lConvUM := .F.
					nQtdeIt	:= nQuant
					nPrcIt	:= IIF(cTipoNF == "C",Val(aItens[nX]:_Prod:_vProd:Text),nPrecUni)	
					nTotIt	:= IIF(cTipoNF == "C",Val(aItens[nX]:_Prod:_vProd:Text), IIF(nTotItem > 0,nTotItem,(nQuant * nPrecUni)))
					
					if lCsdXml .and. cTipoNF == "N"
						nQtXML  := nQtdeIt
						cUmCom   := GetAdvFVal("SA5","A5_UNID",fwxFilial("SA5")+cCodigo+cLoja+cProduto,1)
						cUM		 := GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
						nQtdeIt  := EstConvUM(cProduto,cUmCom,nQtdeIt)
						nPrcIt	 := nTotIt / nQtdeIt
						if nQtdeIt == 0
							lProces := .F.
							//"Não há cadastro de conversão da unidade " # " para o produto " # ". O cadastro é obrigatório quando MV_CSDXML = .T." # "Não há cadastro de conversão para este produto"
							aAdd(aErros,{cFile,"COM053 - " + STR0256 + cUmCom + STR0257 + Alltrim(cProduto) + STR0258,STR0259})
							aAdd(aErroErp,{cFile,"COM053"})
						endif
					
					elseif lUnidMed
						If cTipoNF $ "BD"
							lConvUM := GetAdvFVal("SA7","A7_UMNFE",xFilial("SA7")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
						Else
							lConvUM := GetAdvFVal("SA5","A5_UMNFE",xFilial("SA5")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
						Endif
						
						cUM			:= GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
						cSEGUM		:= GetAdvFVal("SB1","B1_SEGUM",xFilial("SB1")+cProduto,1)
						nQtSEGUM	:= 0
						lFatorConv	:= COLVLSEGUM(cProduto,cSEGUM)
							
						If !Empty(cSEGUM)
							If lConvUM
								//Produto não possui fator de conversão e não tem como converter para primeira
								//unidade de medida
								If !lFatorConv
									lProces := .F.
									aAdd(aErros,{cFile,"COM050 - " + STR0253 + cProduto ,STR0198}) //"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
									aAdd(aErroErp,{cFile,"COM050"})
								Else
									nQtSEGUM := nQtdeIt
									nQtdeIt	 := ConvUM(cProduto,nQtdeIt,nQtdeIt,1)
									nPrcIt	 := nTotIt / nQtdeIt
								Endif
							Else
								nQtSEGUM := Iif(lFatorConv,ConvUM(cProduto,nQtdeIt,nQtdeIt,2),0)
							Endif
						Endif
					Endif
					
					If lA140IQTD
						aA140IQTD := ExecBlock("A140IQTD",.F.,.F.,{cProduto,cUM,cSEGUM,nQtSEGUM,nQtdeIt,nPrcIt,nTotIt,lConvUM,cCodigo,cLoja,cDoc,cSerie,cTipoNF,Iif(cTipoNF $ "BD",.T.,.F.),oXML})
						If ValType(aA140IQTD) == "A" .And. Len(aA140IQTD) == 4
							nQtdeIt	 := aA140IQTD[1]
							nPrcIt	 := aA140IQTD[2]
							nTotIt	 := aA140IQTD[3]
							nQtSEGUM := aA140IQTD[4]
						EndIf							
					EndIf
						
					aAdd(aItemSDT,{{"DT_FILIAL" 	,xFilial("SDT")											},; //Filial
									 {"DT_CNPJ"		,cCGC													},; //CGC
					 				 {"DT_COD"		,cProduto												},; //Codigo do produto
					 				 {"DT_PRODFOR"	,aItens[nX]:_PROD:_CPROD:TEXT							},; //Cdgo do pduto do Fornecedor
				 					 {"DT_DESCFOR"	,aItens[nX]:_PROD:_XPROD:TEXT							},; //Dcao do pduto do Fornecedor
				 					 {"DT_ITEM"   	,PadL(Len(aItemSDT)+1,TamSX3("D1_ITEM")[1],"0")			},; //Item
				 				 	 {"DT_QUANT"  	,nQtdeIt												},; //Qtde
					 				 {"DT_VUNIT"	,nPrcIt													},; //Vlor Unitário
					 				 {"DT_FORNEC"	,cCodigo												},; //Forncedor
					 				 {"DT_LOJA"   	,cLoja													},; //Lja
						 			 {"DT_DOC"    	,cDoc													},; //DocmTo
				 					 {"DT_SERIE"	,cSerie							   						},; //Serie
				 					 {"DT_VALFRE"	,nFretItem												},; //Valor Frete
	 				 				 {"DT_DESPESA"	,nDespItem							   					},; //Valor Despesa
				 					 {"DT_SEGURO"	,nSegItem								  				},; //Valor Seguro
				 					 {"DT_VALDESC"	,nDescItem												},; //Valor Desconto
				 					 {"DT_TOTAL"	,nTotIt													},; //Valor Total
				 					 {"DT_PEDIDO"	,cPedido							   					},; //Pedido
				 					 {"DT_ITEMPC"	,cItemPed								  				},; //Item do pedido
				 					 {"DT_CFOP"		,cCFOP								  					},; // Confirma CFOP de Retorno de Beneficiamento 'S' ou 'N'
				 					 {"DT_LOTE"		,cLote								  					},; // Lote
				 					 {"DT_DTVALID"	,dValidLote								  				},; // Validade do Lote
				 					 {"DT_FCICOD"	,cFciCod												}})	//Codigo FCI (alteração)

									 If cTipoNF $ "CD" .And. !Empty(cNFOriComp) .And. !Empty(cSerOriComp) .And. !Empty(cItOriComp)
									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_NFORI"	, cNFOriComp}) // NF Origem
					 					aAdd(aItemSDT[Len(aItemSDT)],{"DT_SERIORI", cSerOriComp}) // Serie Origem
					 					aAdd(aItemSDT[Len(aItemSDT)],{"DT_ITEMORI", cItOriComp}) // Item Origem
					 				 Endif

									 if lCsdXML
										aAdd(aItemSDT[Len(aItemSDT)],{"DT_ITXML"	, STRZERO(VAL(aItens[nX]:_NITEM:TEXT),TamSX3("DKA_ITXML")[1])}) // ITEM DO XML
										aAdd(aItemSDT[Len(aItemSDT)],{"DT_UMXML"	, cUmCom}) // Unidade de medida comercial
										aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTDXML"	, nQtXML}) // Qtd xml
										aAdd(aItemSDT[Len(aItemSDT)],{"DT_FATOR"	, GetAdvFVal("D3Q","D3Q_FATOR",fwxFilial("D3Q") + cProduto + cUmCom,1)}) // Fator de conversão
									 endif

									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_CODCFOP"  , cCodCFOP})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLIPI"  , nIPIItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLICM"  , nICMItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLISS"  , nISSItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLPIS"  , nPISItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLCOF"  , nCOFItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLICST" , nIMCSTIt})
									 
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQIPI"  , nAlIPIItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQICM"  , nAlICMItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQISS"  , nAlISSItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQPIS"  , nAlPISItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQCOF"  , nAlCOFItem})
									 aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALICST"  , nALIMCSTIt})
									 
									 If SDT->(FieldPos("DT_DFABRIC")) > 0
  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_DFABRIC"  , dFabLote}) 
  									 Endif
  									 
									 If lFCPAnt
  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPAN"  , nBCFCPSTRet})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XAFCPAN"  , nPFCPSTRet})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPAN"  , nVFCPSTRet})
  									 Endif
  									 
  									 If lFCPST
  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_XBFCPST"  , nBCFCPST})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XAFCPST"  , nPFCPST})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_XVFCPST"  , nVFCPST})
  									 Endif
  									 
  									 If lICMSSTRet
  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMNDES"  , nVICMSSTRet})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_BASNDES"  , nBICMSSTRet})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_ALQNDES"  , nAICMSSTRet})
  									 Endif
  									 
  									 If lDTClasFis .And. !Empty(cClasFis)
  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_CLASFIS"  , cClasFis})
  									 Endif
  									 
  									 If lUnidMed
  									 	aAdd(aItemSDT[Len(aItemSDT)],{"DT_UM"  		, cUM})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_SEGUM"  	, cSEGUM})
  										aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTSEGUM"  , nQtSEGUM})
  									 Endif

									 If lDTICMDeson
										aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMDES"  	, nICMDeson})
										aAdd(aItemSDT[Len(aItemSDT)],{"DT_ICMDEMT"  , cICMDesMot})
									 Endif
				Endif
		
			ElseIf lProces						
				SA7->(DbSetOrder(1))
				DE7->(DbSetOrder(1))
				If SA7->(DbSeek(xFilial("SA7")+cCodigo+cLoja+cProduto))
					cUmNfe := SA7->A7_UMNFE 
					If SA7->A7_UMNFE == "2"
						nQuant := ConvUM(cProduto,Val(aItens[nX]:_Prod:_qCom:Text),Val(aItens[nX]:_Prod:_qCom:Text),1)
					EndIf	
				ElseIf DE7->(DbSeek(xFilial("DE7")+cCodigo+cLoja+cProduto)) .And. DE7->DE7_UMNFE == "2"
					cUmNfe := DE7->DE7_UMNFE 
					If DE7-DE7_UMNFE == "2" 
						nQuant := ConvUM(cProduto,Val(aItens[nX]:_Prod:_qCom:Text),Val(aItens[nX]:_Prod:_qCom:Text),1)
					EndIf	
				EndIf	                                                      				
				AAdd(aProdutos,{cProduto,aItens[nX]:_Prod:_uCom:Text,nQuant,IIf(ValType(oXML:_InfNfe:_Det)=='A',Val(oXML:_InfNfe:_Det[nX]:_PROD:_vPROD:Text),Val(oXML:_INFNFE:_DET:_PROD:_VPROD:TEXT)),cUmNfe})
			EndIf    
		Next nX 
		If lNFeTransp .And. lProces
			If !(TMSAE80Inc(oXml,3,aProdutos,aItens[1]:_PROD:_CFOP:TEXT,@cMotivo,@nNumDet,@cDetalhe,cSeqEnd,cIDEstrang))
				lProces := .F.
				aAdd(aErros,{cFile,"COM015 - " + cDetalhe,STR0198}) //"Verifique as informações da Nf-e."
				aAdd(aErroErp,{cFile,"COM015"})
			EndIf	
		EndIf
		If (TamSx3("DS_PLIQUI")[1] - (TamSx3("DS_PLIQUI")[2]+1) < Len(AllTrim(STR(Int(nPesoLiq)))) .Or. TamSx3("DS_PLIQUI")[2] < Len(AllTrim(Str(nPesoLiq - Int(nPesoLiq))))-2) .And. lProces
			aAdd(aErros,{cFile,"COM016 - " + cDetalhe,"DS_PLIQUI " + STR0211}) //"DS_PLIQUI - O tamanho do campo não suporta o valor fornecido "
			aAdd(aErroErp,{cFile,"COM016"})
			lProces := .F.
		ElseIf (TamSx3("DS_PBRUTO")[1] - (TamSx3("DS_PBRUTO")[2]+1) < Len(AllTrim(STR(Int(nPesoBruto)))) .Or. TamSx3("DS_PBRUTO")[2] < Len(AllTrim(Str(nPesoBruto - Int(nPesoBruto))))-2) .And. lProces
			aAdd(aErros,{cFile,"COM017 - " + cDetalhe,"DS_PBRUTO " + STR0211}) //"DS_PBRUTO - O tamanho do campo não suporta o valor fornecido "
			aAdd(aErroErp,{cFile,"COM017"})
			lProces := .F.			
		EndIf
    EndIf
    
    //Verifica duplicidade da amarração com a nf de origem
    If lProces .And. cTipoNF == "D" 
    	aItemSDT := MT140DUP(aItemSDT)
    Endif
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Grava os dados do cabeçalho e itens da nota importada do XML³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If lProces  .And. !lNFeTransp
		Begin Transaction
		
		aHeadSDS:=aHeadSDS[1]
		//--Grava cabeçalho
		RecLock("SDS",.T.)
		For nX:=1	To Len(aHeadSDS)
			If aHeadSDS[nX][1] == "DS_SERIE"
				SerieNfId("SDS",1,"DS_SERIE",dEmis,"SPED",aHeadSDS[nX][2])
			Elseif aHeadSDS[nX][1] == "DS_TOTAL" .and. SDS->(FieldPos("DS_TOTAL")) > 0
				SDS->&(aHeadSDS[nX][1]):= aHeadSDS[nX][2]
			Else
				SDS->&(aHeadSDS[nX][1]):= aHeadSDS[nX][2]
			Endif
		Next
		dbCommit()
		MsUnlock()
		//--Grava Itens
		For nX:=1 To Len(aItemSDT)
			RecLock("SDT",.T.)
			For nY:=1 To Len(aItemSDT[nX])
				If aItemSDT[nX][nY][1] == "DT_SERIE"
					SerieNfId("SDT",1,"DT_SERIE",dEmis,"SPED",aItemSDT[nX][nY][2])
				Else
					SDT->&(aItemSDT[nX][nY][1]):= aItemSDT[nX][nY][2]
				Endif
			Next
			dbCommit()
			MsUnlock()
		Next	
			aAdd(aProc,{cDoc,cSerie,cNomeFor})

		End Transaction
	ElseIf lProces
		aAdd(aProc,{cDoc,cSerie,Posicione("SA1",1,xFilial("SA1")+cCodigo+cLoja,"A1_NOME")})		
	EndIf

	//-- Ponto de entrada para ajustes apos a inclusao dos dados na tabela SDS e SDT.
	If lProces .And. ExistBlock("A140IGRV")
		ExecBlock("A140IGRV",.F.,.F.,{cDoc,cSerie,cCodigo,cLoja,oXml})
	EndIf   
EndIf	

If lNFeTransp .And. !Empty(cDetalhe)
	TMSAE80GRV(cFile,cChvNfe,cDoc,cSerie,cCGC,cMotivo,cDetalhe)
EndIf

//-------------------------------------------------------//
// Atualiza calculo dos impostos no documento importado. //
//-------------------------------------------------------//
cNextAlias := GetNextAlias()
cQry := " SELECT DT_TES, R_E_C_N_O_ AS RECNO "
cQry += " FROM " + RetSqlName("SDT")
cQry += " WHERE DT_DOC = '" + cDoc + "'"
cQry += " AND DT_SERIE = '" + cSerie + "'"
cQry += " AND DT_FORNEC = '" + cCodigo + "'"
cQry += " AND DT_LOJA = '" + cLoja + "'"
cQry += " AND DT_TES <> ''"
cQry += " AND D_E_L_E_T_ = ' '" 
 
cQry := ChangeQuery(cQry)
dbUseArea(.T., "TOPCONN", TCGenQry(,,cQry),cNextAlias, .T., .T.)

While (cNextAlias)->(!EOF()) 
	ColAtuImp((cNextAlias)->DT_TES,0,.T.,(cNextAlias)->RECNO) 
	(cNextAlias)->(DbSkip())
Enddo

(cNextAlias)->(DbCloseArea()) 

// ------------------------------------------------------------------------------------------ //
// Limpa o Objeto: oFullXMl Conforme orientado pelo Framework, se faz necessário a utilização //
// do DesClassIntf para que o Objeto realmente seje limpo.                                    //
// Caso contrário, em situações onde existir um grande numero de XMLS Parseados, ocorrera a   //
// mensagem: XML dynamic Nodes Overflow                                                       //
// Antes de executar o comando: DesClassIntf, coloque o objeto como NIL                       //
// ------------------------------------------------------------------------------------------ //
oXML	:=Nil
oAuxXml	:=Nil
oFullXML:=Nil
DelClassIntf()

Return lProces

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ImpXML_NFsºAutor  ³Leonardo Quintania  º Data ³  10/08/12   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Funcao para leitura de XMLs de NFs no diretorio de downloadº±±
±±º			 ³ e geracao da nota fiscal					  			  	  º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ COMXCOL			                                          º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function ImpXML_NFs(cFile,lJob,aProc,aErros,oFullXML,aErroERP)

Local cError     	:= ""
Local cCGCTT		:= ""
Local cCGCTP		:= ""
Local cCodigo 		:= ""
Local cLoja			:= ""
Local cNomeFor		:= ""
Local cCodServ		:= ""
Local cMunServ		:= ""
Local cDescServ		:= ""
Local cDoc			:= ""
Local cSerie		:= ""  
Local cRPS			:= ""
Local cCodNFE		:= ""
Local cHrEmis		:= "" 
Local cNFsVersao	:= ""
Local cUFTom		:= ""
Local cQry			:= ""
Local cFiltro		:= ""
Local dDtEmis		:= StoD("")
Local nX			:= 0
Local nY			:= 0
Local lProces    	:= .T.
Local aItens     	:= {}
Local aHeadSDS		:= {}
Local aItemSDT		:= {}
Local aDirFilial	:= {}
Local cMT140ISV		:= ""
Local nAlqISS		:= 0
Local nVlrISS		:= 0
Local nVlrPIS		:= 0
Local nVlrCOF		:= 0
Local lISSIt		:= .F.
Local lUnidMed		:= SDT->(FieldPos("DT_UM")) > 0 .And. SDT->(FieldPos("DT_SEGUM")) > 0 .And. SDT->(FieldPos("DT_QTSEGUM")) > 0
Local lConvUM		:= .F.
Local cUM			:= ""
Local cSEGUM		:= ""
Local nQtSEGUM		:= 0
Local lFatorConv	:= .F.

Private lMsErroAuto	:= .F.

Default lJob   	 	:= .T.
Default cFile		:= ""
Default aProc		:= {}
Default aErros		:= {}
Default oFullXML	:= NIL 

//-- Verifica erro na sintaxe do XML
If Empty(oFullXML) .Or. !Empty(cError)
	If lJob
		aAdd(aErros,{cFile,STR0101+cError,STR0102}) //"Erro de sintaxe no arquivo XML: "#"Entre em contato com o emissor do documento e comunique a ocorrência."
	Else
		Aviso(STR0082,cError,{STR0004},2,"ImpXML_NFs") //"Erro"#"OK"
	EndIf			
	lProces := .F.
Else
	oFullXML	:= XmlChildEx(oFullXML,"_PROCNEOGRIDNFSE")
	cCGCTT  	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_TOMADOR:_CNPJTOM:TEXT
	If XmlChildEx(oFullXML:_NEOGRID:_RETNEOGRIDNFSE,"_CNPJPREST") # NIL 
  		cCGCTP  	:= oFullXML:_NEOGRID:_RETNEOGRIDNFSE:_CNPJPREST:TEXT  
	Else
		cCGCTP  	:= oFullXML:_NEOGRID:_RETNEOGRIDNFSE:_CPFPREST:TEXT
	EndIf 
EndIf

aDirFilial := DirFilial(cFile,cCGCTT,"",lJob)
If !aDirFilial[1] 
	If !aDirFilial[2] 
		If !lJob
			If aDirFilial[3] 
				Aviso(STR0082,STR0244,{STR0004},2,"ImpXML_NFe")	//"Erro"#""Existe mais de uma Empresa/Filial para este XML." "#"OK"
			Elseif aDirFilial[4]
				Aviso(STR0082,STR0254,{STR0004},2,"ImpXML_NFe")	//"Erro"#""Este XML não pertence a nenhuma empresa/filial e não podera ser processado." "#"OK"
			Else
				Aviso(STR0082,STR0085,{STR0004},2,"ImpXML_NFe")	//"Erro"#""Este XML pertence a outra empresa/filial e não podera ser processado na empresa/filial corrente." "#"OK"
			EndIf
		Else
			If aDirFilial[3]
				aAdd(aErros,{cFile,"COM042 - " + STR0244,STR0245}) // Existe mais de uma Empresa/Filial para este XML. // Selecione a Empresa/Filial deste XML através da rotina Reprocessar no Monitor do TOTVS Colaboração.
				aAdd(aErroErp,{cFile,"COM042"})
			ElseIf aDirFilial[4]
				aAdd(aErros,{cFile,"COM052 - " + STR0254,STR0255}) //"Este XML não pertence a nenhuma empresa/filial e não podera ser processado." //"Verificar se XML pertence a empresa"
				aAdd(aErroErp,{cFile,"COM052"})
			Else
				aAdd(aErros,{cFile,"COM002 - " + STR0085,STR0246}) // Este XML pertence a outra empresa/filial e não poderá ser processado na empresa/filial corrente. // Importe na Empresa/Filial correta.
				aAdd(aErroErp,{cFile,"COM002"})
			EndIf
		EndIf
		lProces:= .F. 
 	Else 
	 	aAdd(aErros,{cFile,"COM002 - " + STR0085,STR0246}) // Este XML pertence a outra empresa/filial e não poderá ser processado na empresa/filial corrente. // Importe na Empresa/Filial correta.
		aAdd(aErroErp,{cFile,"COM002"}) 
 		lProces  := .F.
 	Endif
Endif
	
If lProces
	SA2->(dbSetOrder(3))
	If !SA2->(dbSeek(xFilial('SA2')+AllTrim(cCGCTP)))  
		//Verifica se está cadastrado o prestador de servico
		If !lJob
			Aviso(STR0082,STR0208,{STR0004},2,"ImpXML_NFs") //"Erro"#""Este XML possui um prestador de serviço que não está cadastrado na empresa/filial corrente." "#"OK"
		Else
			aAdd(aErros,{cFile,"COM007 - " + STR0040 +oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_PRESTADOR:_RSOCIALPREST:TEXT  +" [" + Transform(cCGCTP,"@R 99.999.999/9999-99") +"] "+ STR0109, STR0110}) //"Fonecedor"#"inexistente na base."#"Gere cadastro para este fornecedor."
		EndIf
	aAdd(aErroErp,{cFile,"COM007"})
		lProces  := .F.	              
	Else
		cCodigo :=	SA2->A2_COD
		cLoja	:=	SA2->A2_LOJA   
		cNomeFor:=	SA2->A2_NOME
	EndIf      
EndIf
		
If lProces  	
	If ValType(XmlChildEx(oFullXML:_NEOGRID:_RETNEOGRIDNFSE,"_NNFSE")) == "O"
		cDoc	:= StrZero(Val(AllTrim(oFullXML:_NEOGRID:_RETNEOGRIDNFSE:_NNFSE:TEXT)),TamSx3("F1_DOC")[1])
		cSerie	:= Replicate(" ", TamSx3("F1_SERIE")[1])

		If ValType(XmlChildEx(oFullXML:_NEOGRID:_RETNEOGRIDNFSE,"_DTEMISNFSE")) == "O"
			dDtEmis	:= StoD(StrTran(AllTrim(oFullXML:_NEOGRID:_RETNEOGRIDNFSE:_DTEMISNFSE:TEXT),"-",""))
			cHrEmis	:= Substr(oFullXML:_NEOGRID:_RETNEOGRIDNFSE:_DTEMISNFSE:TEXT,12)
		Else
			If !lJob
				Aviso(STR0082,STR0240,{STR0004},2,"ImpXML_NFs") //Erro#Tag _DTEMISNFSE não encontrada#OK 
			Else
				aAdd(aErros,{cFile,"COM034 - " + STR0240,STR0241})//Tag _DTEMISNFSE não encontrada#Verificar com quem originou o XML.
			EndIf
			aAdd(aErroErp,{cFile,"COM034"})
			lProces := .F.
		Endif

		If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_TOMADOR,"_UFTOM")) == "O" .And.;
			!Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_TOMADOR:_UFTOM:TEXT)
			cUFTom := oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_TOMADOR:_UFTOM:TEXT
		Else
			If !lJob
				Aviso(STR0082,STR0243,{STR0004},2,"ImpXML_NFs") //Erro#Tag _UFTOM nao encontrada#OK 
			Else
				aAdd(aErros,{cFile,"COM038 - " + STR0243,STR0241})//Tag _UFTOM nao encontrada#Verificar com quem originou o XML.
			EndIf
			aAdd(aErroErp,{cFile,"COM038"})
			lProces := .F.
		EndIf

		If lProces .And. ValType(XmlChildEx(oFullXML:_NEOGRID:_RETNEOGRIDNFSE,"_NRPS")) == "O"
			cRPS := Alltrim(oFullXML:_NEOGRID:_RETNEOGRIDNFSE:_NRPS:TEXT)		
		Endif
		
		If lProces .And. ValType(XmlChildEx(oFullXML:_NEOGRID:_RETNEOGRIDNFSE,"_CVERIFICANFSE")) == "O"
			cCodNFE := Alltrim(oFullXML:_NEOGRID:_RETNEOGRIDNFSE:_cVerificaNFSe:TEXT)
		Endif		 
	Else
		If !lJob
			Aviso(STR0082,STR0242,{STR0004},2,"ImpXML_NFs") //Erro#Tag _NNFSE não encontrada#OK
		Else
			aAdd(aErros,{cFile,"COM035 - " + STR0242,STR0241}) //Tag _NNFSE não encontrada#Verificar com quem originou o XML.
		EndIf
		aAdd(aErroErp,{cFile,"COM035"})
		lProces	 := .F.
	Endif
	
	DbSelectArea("SDS")
	SDS->(DbSetOrder(1))
	If (SDS->(DbSeek(xFilial("SDS")+cDoc+cSerie+cCodigo+cLoja)))//Filial + RPS + SERIE RPS + FORNECEDOR + LOJA  
		lProces	 := .F.
	EndIf
EndIf	    
	
If lProces
	If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS,"_ITEM" )) == "A"
		aItens := oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM
		
		If Len(aItens) > 0
			// Codigo de servico 
			If ValType(aItens[1]:_CODIGOITEMLISTASERVICO) == "O" .And. !Empty(aItens[1]:_CODIGOITEMLISTASERVICO:TEXT)
				cCodServ 	:= aItens[1]:_CODIGOITEMLISTASERVICO:TEXT
			ElseIf ValType(aItens[1]:_CITEMLISTASERVICO) == "O" .And. !Empty(aItens[1]:_CITEMLISTASERVICO:TEXT)
				cCodServ 	:= aItens[1]:_CITEMLISTASERVICO:TEXT
			ElseIf ValType(aItens[1]:_CODIGOCFPS) == "O" .And. !Empty(aItens[1]:_CODIGOCFPS:TEXT)
				cCodServ	:= aItens[1]:_CODIGOCFPS:TEXT
			ElseIf ValType(aItens[1]:_CTRIBUTMUN) == "O" .And. !Empty(aItens[1]:_CTRIBUTMUN:TEXT)
				cCodServ	:= aItens[1]:_CTRIBUTMUN:TEXT
			EndIf
			
			//ISS pela tag ITEM
			If ValType(XmlChildEx(aItens[1],"_ALISS")) == "O" .And. !Empty(aItens[1]:_ALISS:TEXT)
				nAlqISS		:= Val(aItens[1]:_ALISS:TEXT)
			Endif
			
			If ValType(XmlChildEx(aItens[1],"_VLISS")) == "O" .And. !Empty(aItens[1]:_VLISS:TEXT)
				nVlrISS		:= Val(aItens[1]:_VLISS:TEXT)
			Endif
			
			lISSIt := .T.
		Endif
	Elseif ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS,"_ITEM" )) == "O"
		//Verifica existencia do grupo Itens
		If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_VLUNIT" )) == "O" .And.;
			ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_VLITEM" )) == "O" .And.;
			ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_QTDE" )) == "O"

			aItens := {oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM}
		Endif
		
		If Len(aItens) > 0
			// Codigo de servico 
			If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_CODIGOITEMLISTASERVICO")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CODIGOITEMLISTASERVICO:TEXT)
				cCodServ 	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CODIGOITEMLISTASERVICO:TEXT 
			ElseIf ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_CITEMLISTASERVICO")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CITEMLISTASERVICO:TEXT)
				cCodServ 	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CITEMLISTASERVICO:TEXT
			ElseIf ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_CODIGOCFPS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CODIGOCFPS:TEXT)
				cCodServ	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CODIGOCFPS:TEXT
			ElseIf ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_CTRIBUTMUN")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CTRIBUTMUN:TEXT)
				cCodServ	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_CTRIBUTMUN:TEXT
			EndIf
			
			//ISS pela tag ITEM
			If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_ALISS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_ALISS:TEXT)
				nAlqISS		:= Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_ALISS:TEXT)
			Endif
			
			If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM,"_VLISS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_VLISS:TEXT)
				nVlrISS		:= Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_ITEM:_VLISS:TEXT)
			Endif
			
			lISSIt := .T.
		Endif
	EndIf
		  
	// Codigo de servico 
	If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_ITEMLISTASERV")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_ITEMLISTASERV:TEXT)
		cCodServ 	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_ITEMLISTASERV:TEXT 
	ElseIf ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_CODIGOCFPS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_CODIGOCFPS:TEXT)
		cCodServ	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_CODIGOCFPS:TEXT
	ElseIf ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_CTRIBUTMUN")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_CTRIBUTMUN:TEXT)
		cCodServ	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_CTRIBUTMUN:TEXT
	EndIf
	
	//ISS pela tag SERVICO
	If !lISSIt
		If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_ALISS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_ALISS:TEXT)
			nAlqISS := Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_ALISS:TEXT)
		Endif 
		
		If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_VLISS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLISS:TEXT)
			nVlrISS := Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLISS:TEXT)
		Endif
	Endif

	//PIS pela tag SERVICO
	If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_VLPIS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLPIS:TEXT)
		nVlrPIS := Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLPIS:TEXT) 
	Endif
	
	//COFINS pela tag SERVICO 
	If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_VLCOFINS")) == "O" .And. !Empty(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLCOFINS:TEXT)
		nVlrCOF := Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLCOFINS:TEXT)  
	Endif 
	
	// Descricao do servico
	If ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_DESCRICAO,"_DESRPS")) == "O"
		cDescServ	:= oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_DESCRICAO:_DESRPS:TEXT			
	EndIf
	
   	// Municipio do servico
	If ValType(XmlChildEx(oFUllXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO,"_CMUNSERV")) == "O"
		cMunServ	:= Right(oFUllXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_CMUNSERV:TEXT,7)
	EndIf	           

	//Ponto de entrada para manipular o código do serviço
	IF ExistBlock("MT140ISV")
		cMT140ISV := ExecBlock("MT140ISV",.F.,.F.,{cCodServ, cMunServ, cCGCTT, cCGCTP})
		If ValType(cMT140ISV) == "C" .And. !Empty(cCodServ)
			cCodServ := cMT140ISV
		EndIf
	Endif
	                      
	//Pesquisa um produto que possui amarração com fornecedor do XML e possui o codigo de servico correto.                    
	cQry	:= " SELECT SB1.B1_COD, SB1.B1_DESC"
	cQry	+= " FROM " + RetSqlName("SB1") + " SB1"
	cQry	+= " INNER JOIN " + RetSqlName("SA5") + " SA5 ON SA5.A5_PRODUTO = SB1.B1_COD AND SA5.D_E_L_E_T_ = ''"
	cQry	+= " INNER JOIN " + RetSqlName("SA2") + " SA2 ON SA2.A2_COD = SA5.A5_FORNECE AND SA2.D_E_L_E_T_ = ''"
	cQry	+= " LEFT JOIN " + RetSqlName("SBZ") + " SBZ ON SBZ.BZ_COD = SB1.B1_COD AND SBZ.D_E_L_E_T_ = ''"
	cQry	+= " WHERE SB1.B1_FILIAL = '" + xFilial("SB1") + "'"
	
	If ExistBlock("MT140FSV")
		cFiltro := ExecBlock("MT140FSV",.F.,.F.,{cCodServ, cMunServ, cCGCTT, cCGCTP})
		If ValType(cFiltro) <> "C"
			cFiltro := ""
		Endif
	Endif
		
	cQry	+= " AND (SB1.B1_CODISS = '" + cCodServ + "' OR SBZ.BZ_CODISS = '" + cCodServ + "' " + cFiltro + " )"
	cQry	+= " AND SA2.A2_CGC = '" + cCGCTP + "'"
	cQry	+= " AND SB1.D_E_L_E_T_ = ''"
			
	cQry := ChangeQuery(cQry)
	dbUseArea(.T., "TOPCONN", TCGenQry(,,cQry),"SB1TMP", .T., .T.)                   
        
    If SB1TMP->(Eof()) //Verifica se possui pelo menos uma ocorrencia do codigo de serviço do XML   
		//Nao processa XML de outra empresa/filial
		If !lJob
			Aviso(STR0082,STR0209,{STR0004},2,"ImpXML_NFs") //"Erro"#"""Este XML possui um codigo de Serviço que não está cadastrado em um produto na empresa/filial corrente."#"OK"
		Else
			aAdd(aErros,{cFile,"COM018 - " + STR0214+cCodServ+STR0215+SA2->A2_NOME+" ["+cCGCTP+"]. "+STR0217+cDescServ+"." ,STR0216}) //"Código de serviço "+cCodServ+" não cadastrado em um produto, na empresa/filial corrente, e/ou produto não possui amarração com o fornecedor "+SA2->A2_NOME+cCGC. Descrição do serviço:+cDescServ.
		EndIf
	aAdd(aErroErp,{cFile,"COM018"})
		lProces  := .F.
	Else
		cProduto:= SB1TMP->B1_COD
	EndIf  
	SB1TMP->(dbCloseArea())
EndIf

If lProces 	

	// Versao layout
	If ValType(XmlChildEx(oFullXML,"_VERSAO")) == "O"
		cNFsVersao := oFullXML:_VERSAO:TEXT
	ElseIf ValType(XmlChildEx(oFullXML:_NEOGRID:_NEOGRIDRPS,"_VERSAO")) == "O"
		cNFsVersao := oFullXML:_NEOGRID:_NEOGRIDRPS:_VERSAO:TEXT
	EndIf

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Grava os Dados do Cabecalho - SDS  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	DbSelectArea("SDS")
	AADD(aHeadSDS,{{"DS_FILIAL"	,xFilial("SDS")																	     	},; //Filial
				    {"DS_CNPJ"		,cCGCTP																				},; //CGC
				    {"DS_DOC"		,cDoc 																				},; //Numero do Documento
				    {"DS_SERIE"		,cSerie 																			},; //Serie
				    {"DS_FORNEC"	,cCodigo																			},; //Fornecedor
				    {"DS_LOJA"		,cLoja 																				},; //Loja do Fornecedor
				    {"DS_NOMEFOR"	,cNomeFor																			},; //Nome do Fornecedor
				    {"DS_EMISSA"	,dDtEmis										 						   			},; //Data de Emissão
				    {"DS_EST"		,cUFTom																				},; //Estado de emissao da NF
				    {"DS_TIPO"		,"N"																				},; //Tipo da Nota
				    {"DS_FORMUL"	,"N" 																		 		},; //Formulario proprio
				    {"DS_CHAVENF"	,xFilial("SDS")+cDoc+cSerie+cCodigo+cLoja											},; //Chave de Acesso da NF
				    {"DS_ESPECI"	,"NFS"																		  		},; //Especie
				    {"DS_ARQUIVO"	,AllTrim(cFile)																   		},; //Arquivo importado
				    {"DS_STATUS"	,"N"			 																	},; //Status
				    {"DS_VERSAO"	,cNFsVersao																			},; //Versao
				    {"DS_USERIMP"	,IIf(!lJob,cUserName,STR0137)														},; //Usuario na importacao
				    {"DS_DATAIMP"	,dDataBase																			},; //Data importacao do XML
				    {"DS_HORAIMP"	,SubStr(Time(),1,5)															   		},;//Hora importacao XML
				   	{"DS_CODNFE" 	,cCodNFE																				},; //Codigo de verificaçao na NFe
					{"DS_NUMRPS"	,cRPS																					},; //Numero do RPS
					{"DS_HORNFE"	,cHrEmis																				}}) //Hora de emissao da NFe

	//Dados dos Itens - SDT
	If Len(aItens) > 0
		For nX := 1 To Len(aItens)
			nQtdeIt	:= Val(aItens[nX]:_QTDE:TEXT)
			nPrcIt	:= Val(aItens[nX]:_VLUNIT:TEXT)	
			nTotIt	:= Val(aItens[nX]:_VLITEM:TEXT)

			If lUnidMed
				lConvUM 	:= GetAdvFVal("SA5","A5_UMNFE",xFilial("SA5")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
				
				cUM			:= GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
				cSEGUM		:= GetAdvFVal("SB1","B1_SEGUM",xFilial("SB1")+cProduto,1)
				nQtSEGUM	:= 0
				lFatorConv	:= COLVLSEGUM(cProduto,cSEGUM)

				If !Empty(cSEGUM)
					If lConvUM
						//Produto não possui fator de conversão e não tem como converter para primeira
						//unidade de medida
						If !lFatorConv
							lProces := .F.
							aAdd(aErros,{cFile,"COM050 - " + STR0253 + cProduto ,STR0198}) //"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
							aAdd(aErroErp,{cFile,"COM050"})
						Else
							nQtSEGUM := nQtdeIt
							nQtdeIt	 := ConvUM(cProduto,nQtdeIt,nQtdeIt,1)
							nPrcIt	 := nTotIt / nQtdeIt
						Endif
					Else
						nQtSEGUM := Iif(lFatorConv,ConvUM(cProduto,nQtdeIt,nQtdeIt,2),0)
					Endif
				Endif
			Endif

			DbSelectArea("SDT")                                               
			aAdd(aItemSDT,{{"DT_FILIAL" 	,xFilial("SDT")														},; //Filial
							{"DT_CNPJ"		,cCGCTP																},; //CGC Tag Prestador
			 				{"DT_COD"		,cProduto															},; //Codigo do produto
			 				{"DT_PRODFOR"	,cProduto															},; //Cdgo do pduto do Fornecedor
		 					{"DT_DESCFOR"	,aItens[nX]:_DISSERV:TEXT											},; //Dcao do pduto do Fornecedor
		 					{"DT_ITEM"   	,PadL(cValToChar(nX),TamSX3("D1_ITEM")[1],"0")						},; //Item
		 					{"DT_QUANT"  	,Val(aItens[nX]:_QTDE:TEXT)									   		},; //Qtde
			 				{"DT_VUNIT"		,Val(aItens[nX]:_VLUNIT:TEXT)										},; //Vlor Unitário
			 				{"DT_FORNEC"	,cCodigo															},; //Forncedor
			 				{"DT_LOJA"   	,cLoja																},; //Lja
				 			{"DT_DOC"    	,cDoc																},; //DocmTo
		 					{"DT_SERIE"		,cSerie							   									},; //Serie
		 					{"DT_TOTAL"		,Val(aItens[nX]:_VLITEM:TEXT)										}}) //Vlor Total
		 					
						 	If ValType(XmlChildEx(aItens[nX],"_ALISS")) == "O" .And. !Empty(aItens[nX]:_ALISS:TEXT)
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_XALQISS"  , Val(aItens[nX]:_ALISS:TEXT)})
							Endif
							
							If ValType(XmlChildEx(aItens[nX],"_VLISS")) == "O" .And. !Empty(aItens[nX]:_VLISS:TEXT)
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLISS"  , Val(aItens[nX]:_VLISS:TEXT)}) 
							Endif

							If ValType(XmlChildEx(aItens[nX],"_VLPIS")) == "O" .And. !Empty(aItens[nX]:_VLPIS:TEXT)
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLPIS"  , Val(aItens[nX]:_VLPIS:TEXT)})
							Elseif nVlrPIS > 0 .And. Len(aItens) == 1
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLPIS"  , nVlrPIS})
							Endif

							If ValType(XmlChildEx(aItens[nX],"_VLCOFINS")) == "O" .And. !Empty(aItens[nX]:_VLCOFINS:TEXT)
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLCOF"  , Val(aItens[nX]:_VLCOFINS:TEXT)})
							Elseif nVlrCOF > 0 .And. Len(aItens) == 1
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_XMLCOF"  , nVlrCOF})
							Endif

							If lUnidMed
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_UM"  		, cUM})
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_SEGUM"  	, cSEGUM})
								aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTSEGUM"  , nQtSEGUM})
							Endif
		Next nX
	Else
		nQtdeIt	:= 1
		nPrcIt	:= Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLSERVICOS:TEXT)
		nTotIt	:= Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLSERVICOS:TEXT) 

		If lUnidMed
			lConvUM 	:= GetAdvFVal("SA5","A5_UMNFE",xFilial("SA5")+cCodigo+cLoja+cProduto,1) == "2" //Segunda unidade de medida
			
			cUM			:= GetAdvFVal("SB1","B1_UM",xFilial("SB1")+cProduto,1)
			cSEGUM		:= GetAdvFVal("SB1","B1_SEGUM",xFilial("SB1")+cProduto,1)
			nQtSEGUM	:= 0
			lFatorConv	:= COLVLSEGUM(cProduto,cSEGUM)

			If !Empty(cSEGUM)
				If lConvUM
					//Produto não possui fator de conversão e não tem como converter para primeira
					//unidade de medida
					If !lFatorConv 
						lProces := .F.
						aAdd(aErros,{cFile,"COM050 - " + STR0253 + cProduto ,STR0198}) //"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
						aAdd(aErroErp,{cFile,"COM050"})
					Else
						nQtSEGUM := nQtdeIt
						nQtdeIt	 := ConvUM(cProduto,nQtdeIt,nQtdeIt,1)
						nPrcIt	 := nTotIt / nQtdeIt
					Endif
				Else
					nQtSEGUM := Iif(lFatorConv,ConvUM(cProduto,nQtdeIt,nQtdeIt,2),0) 
				Endif
			Endif
		Endif

		DbSelectArea("SDT")                                               
   		aAdd(aItemSDT,{{"DT_FILIAL"		,xFilial("SDT")																},; //Filial
						{"DT_CNPJ"		,cCGCTP																		},; //CGC Tag Prestador
		 				{"DT_COD"		,cProduto																	},; //Codigo do produto
		 				{"DT_PRODFOR"	,cProduto																	},; //Cdgo do pduto do Fornecedor
	 					{"DT_ITEM"		,PadL("1",TamSX3("D1_ITEM")[1],"0")											},; //Item
	 					{"DT_QUANT" 	,1									   										},; //Qtde
		 				{"DT_VUNIT"		,Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLSERVICOS:TEXT)			},; //Vlor Unitário
		 				{"DT_FORNEC"	,cCodigo																	},; //Forncedor
		 				{"DT_LOJA"   	,cLoja																		},; //Lja
			 			{"DT_DOC"    	,cDoc																		},; //DocmTo
	 					{"DT_SERIE"		,cSerie							   											},; //Serie
	 					{"DT_TOTAL"		,Val(oFullXML:_NEOGRID:_NEOGRIDRPS:_RPS:_SERVICO:_VLSERVICOS:TEXT)			},; //Vlor Total
	 					{"DT_XALQISS"	,nAlqISS																	},; //Aliquota ISS
	 					{"DT_XMLISS"	,nVlrISS																	},; //Valor ISS
						{"DT_XMLPIS"	,nVlrPIS																	},; //Valor PIS
						{"DT_XMLCOF"	,nVlrCOF																	}}) //Valor COF 

						If lUnidMed
							aAdd(aItemSDT[Len(aItemSDT)],{"DT_UM"  		, cUM})
							aAdd(aItemSDT[Len(aItemSDT)],{"DT_SEGUM"  	, cSEGUM})
							aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTSEGUM"  , nQtSEGUM})
						Endif 
	EndIf								 			 						

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Grava os dados do cabeçalho e itens da nota importada do XML³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If lProces
		Begin Transaction	
			aHeadSDS:=aHeadSDS[1]
			//--Grava cabeçalho
			RecLock("SDS",.T.)
			For nX:=1	To Len(aHeadSDS)
				SDS->&(aHeadSDS[nX][1]):= aHeadSDS[nX][2]
			Next nX
			SDS->(dbCommit())
			SDS->(MsUnlock())
			//--Grava Itens
			For nX:=1 To Len(aItemSDT)
				RecLock("SDT",.T.)
				For nY:=1 To Len(aItemSDT[nX])
					SDT->&(aItemSDT[nX][nY][1]):= aItemSDT[nX][nY][2]
				Next nY
				SDT->(dbCommit())
				SDT->(MsUnlock())
			Next nX
			aAdd(aProc,{cDoc,cSerie,cNomeFor})					
		End Transaction
	Endif     
EndIf	                                  

// ------------------------------------------------------------------------------------------ //
// Limpa o objeto oFullXMl, conforme orientado pelo Framework, se faz necessário a utilizacao //
// do DelClassIntf para que o objeto realmente seja limpo.                                    //
// Caso contrario, em situacoes onde existir um grande numero de XMLs Parseados, ocorrera a   //
// mensagem: XML dynamic Nodes Overflow                                                       //
// Antes de executar o comando: DesClassIntf, coloque o objeto como NIL                       //
// ------------------------------------------------------------------------------------------ //
oFullXML := Nil
DelClassIntf()

Return lProces

/*ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  | A140IRemASC³Autor ³ Carlos Capeli			   |Data ³ 10/10/12 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡ao | Remove caracteres especiais que nao sao reconhecidos pela		³±±   
±±³          | funcao EncodeUTF8.												³±± 
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±    
±±³Retorno   ³ cXMLOri                                                          ³±±    
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±       
±±³ Uso      ³ AT140IRepr                                                       ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±       
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±      
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ*/

Function A140IRemASC(cStrXML)

Local aPesq		:= {"Ã",CHR(129),CHR(141),CHR(143),CHR(144),CHR(157)}		// Caracteres especiais nao reconhecidos pela funcao EncodeUTF8 - Melhor visualizado com fonte MS LineDraw
Local nX		:= 0
Default cStrXML := ""

// Remove caracteres especiais
If !Empty(cStrXML)
	For nX := 1 To Len(aPesq)
		cStrXML := StrTran(cStrXML, aPesq[nX])
	Next nX
EndIf

Return cStrXML

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡„o    ³ImpXML_Ave³ Autor ³ Alex Egydio           ³ Data ³01.02.2013 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descricao ³Importacao dos dados complementares da NF                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±*/
Function ImpXML_Ave(cFile,lJob,aProc,aErros,oFullXML,cXMLOri,aErroErp)
Local aItens		:= {}
Local cError     	:= ""
Local cWarning   	:= ""
Local cCodigo 		:= ""
Local cLoja			:= ""
Local cNomeFor		:= ""
Local cDoc			:= ""
Local cSerie		:= ""   
Local cNumPed		:= ""
Local cItemPC		:= ""
Local cNfOri		:= ""
Local cSerOri		:= ""
Local cItemOri		:= ""
Local cPrdFor		:= ""
Local lNfOri		:= .F.
Local lNumPed		:= .F.
Local lProces    	:= .T.
Local nCntFor		:= 0
Default lJob   	 	:= .T.
Default cFile		:= ""
Default aProc		:= {}
Default aErros		:= {}
Default oFullXML	:= NIL
If lProces	
	oFullXML := XmlParser(cXMLOri,"_",@cError,@cWarning)		
	//-- Verifica erro na sintaxe do XML
	If Empty(oFullXML) .Or. !Empty(cError)
		If lJob
			aAdd(aErros,{cFile,STR0101+cError,STR0102}) //"Erro de sintaxe no arquivo XML: "#"Entre em contato com o emissor do documento e comunique a ocorrência."
		Else
			Aviso(STR0082,cError,{STR0004},2,"ImpXML_Ave") //"Erro"#"OK"
		EndIf			
		lProces := .F.
	Else
		cChaveNF := RIGHT(oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_Id:Text,TamSx3("DS_CHAVENF")[1])
	EndIf

	If lProces
		SDS->(DbSetOrder(2))
		If	SDS->(!DbSeek(xFilial("SDS")+cChaveNF))
			lProces := ImpXML_NFe(cFile,lJob,@aProc,@aErros,.F.,oFullXml:_INVOIC_NFE_COMPL:_NFE_SEFAZ,.T.,cXmlOri)
		EndIf
	EndIf
	If lProces
		cCodigo := SDS->DS_FORNEC			//-- Codigo do Fornecedor/Cliente
		cLoja	:= SDS->DS_LOJA
		cDoc	:= SDS->DS_DOC
		cSerie	:= SDS->DS_SERIE
		SF2->(DbSetOrder(2))
		SC7->(DbSetOrder(4))
		SDT->(DbSetOrder(2))
		aItens:=Iif(ValType(oFullXML:_INVOIC_NFE_COMPL:_COMPLEMENT_NFE:_NS1_ITENS:_NS1_ITEM) == "O",;
							  {oFullXML:_INVOIC_NFE_COMPL:_COMPLEMENT_NFE:_NS1_ITENS:_NS1_ITEM},oFullXML:_INVOIC_NFE_COMPL:_COMPLEMENT_NFE:_NS1_ITENS:_NS1_ITEM)
		Begin Transaction
					
		For nCntFor := 1 To Len(aItens)
			//-- Pesquisar se o pedido de compra do arquivo XML da nota fiscal complementar esta cadastrado
			cNumPed := ""
			cItemPC	:= ""
			cPrdFor := ""
			cNfOri	:= ""
			cSerOri	:= ""
			cItemOri:= ""
			cNumPed := PadR(aItens[nCntFor]:_NS1_PONUMBER:Text,TamSx3("C7_NUM")[1])
			If	Type("aItens["+Str(nCntFor)+"]:_NS1_NUMITEMREQUEST:Text")<>"U"
				cItemPC := PadR(aItens[nCntFor]:_NS1_NUMITEMREQUEST:Text,TamSx3("C7_ITEM")[1])
			EndIf
			cPrdFor	:= PadR(aItens[nCntFor]:_NS1_PRODCODSUPLLI:Text,TamSx3("DT_PRODFOR")[1])
			//-- Pesquisar se a nota fiscal de origem do arquivo XML da nota fiscal complementar esta cadastrado
			If	Type("aItens["+Str(nCntFor)+"]:_NS1_RETURNINDUSTRIALIZATION:_NS1_INVOICE_REFERENCED:_NS1_INVOICEREFERENCED:_NS1_NUMINVOICEREFERENCED:Text")<>"U"
				cNfOri	:= PadR(aItens[nCntFor]:_NS1_RETURNINDUSTRIALIZATION:_NS1_INVOICE_REFERENCED:_NS1_INVOICEREFERENCED:_NS1_NUMINVOICEREFERENCED:Text,TamSx3("F2_DOC")[1])
			EndIf
			If	Type("aItens["+Str(nCntFor)+"]:_NS1_RETURNINDUSTRIALIZATION:_NS1_INVOICE_REFERENCED:_NS1_INVOICEREFERENCED:_NS1_SERIEINVOICEREFERENCED:Text")<>"U"
				cSerOri	:= PadR(aItens[nCntFor]:_NS1_RETURNINDUSTRIALIZATION:_NS1_INVOICE_REFERENCED:_NS1_INVOICEREFERENCED:_NS1_SERIEINVOICEREFERENCED:Text,SerieNfId("SF2",6,"F2_SERIE"))
			EndIf
			If	Type("aItens["+Str(nCntFor)+"]:_NS1_RETURNINDUSTRIALIZATION:_NS1_INVOICE_REFERENCED:_NS1_INVOICEREFERENCED:_NS1_ITEMINVOICEREFERENCED:Text")<>"U"
				cItemOri:= PadR(aItens[nCntFor]:_NS1_RETURNINDUSTRIALIZATION:_NS1_INVOICE_REFERENCED:_NS1_INVOICEREFERENCED:_NS1_ITEMINVOICEREFERENCED:Text,TamSx3("DT_ITEMORI")[1])
			EndIf
			If	SDT->( DbSeek(xFilial("SDT")+cCodigo+cLoja+cDoc+cSerie+cPrdFor) )
				lNumPed := SC7->(DbSeek(xFilial("SC7")+SDT->DT_COD+cNumPed+cItemPC))
				If	!Empty(cNfOri)
					lNfOri	:= SF2->(DbSeek(xFilial("SF2")+cCodigo+cLoja+cNfOri+cSerOri))
				EndIf	
				RecLock("SDT",.F.)
				If	lNumPed	
					SDT->DT_PEDIDO	:= cNumPed
					SDT->DT_ITEMPC	:= cItemPC
				EndIf
				If	lNfOri	
					SDT->DT_NFORI	:= cNfOri
					SDT->DT_SERIORI	:= cSerOri
					SDT->DT_ITEMORI	:= cItemOri
				EndIf
				MsUnLock()
			EndIf
	   	Next nCntFor
	   	
	   	End Transaction     
		aAdd(aProc,{cDoc,cSerie,cNomeFor})
	EndIf
EndIf

oFullXML := Nil
DelClassIntF()

Return lProces

/*ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  | MATA140I	  ³Autor ³ Rodrigo Toledo Silva		   |Data ³ 09/05/12 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡ao | Busca o nome do cliente quando o tipo da nota for devolucao ou   ³±±   
±±³			 | beneficiamento caso contrario busca o nome do fornecedor.   		³±±   
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±    
±±³Parametros³ cTipoNF = Tipo da Nota fiscal (SDS->DS_TIPO)                     ³±±  
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±    
±±³Retorno   ³ Nome do fornecedor/cliente                                       ³±±    
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±       
±±³ Uso      ³ MATA140	                                                        ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±       
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±      
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ*/

Function A140IBusFC(cTipoNF)
Local aArea	  := GetArea()
Local cNomeFC := ""
                                          
If cTipoNF $ "DB"
	cNomeFC := Posicione("SA1",1,xFilial("SA1",SDS->DS_FILIAL)+SDS->(DS_FORNEC+DS_LOJA),"A1_NOME")
Else
	cNomeFC := Posicione("SA2",1,xFilial("SA2",SDS->DS_FILIAL)+SDS->(DS_FORNEC+DS_LOJA),"A2_NOME")
EndIf

RestArea(aArea)
Return (cNomeFC)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ A140IPictºAutor  ³ Rodrigo Toledo     º Data ³  20/07/11   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Retorna a picture de acordo com o tipo do fornecedor.      º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ MATA140I                                                   º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A140IPict()
Return PicPes(Posicione("SA2",1,xFilial("SA2")+M->(DS_FORNEC+DS_LOJA),"A2_TIPO"))

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ A140ICAESºAutor  ³ Rodrigo Pontes     º Data ³  22/03/16   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Retirar caracteres especiais do CGC e Inscrição Estadual   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ MATA140I                                                   º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A140ICAES(cConteudo)

Local aCaEspec	:= {".","-","/"}
Local nI			:= 0

For nI := 1 To Len(aCaEspec)
	cConteudo := StrTran(cConteudo,aCaEspec[nI],"")
Next nI

Return cConteudo

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ A140INSC ºAutor  ³ Rodrigo Pontes     º Data ³  22/03/16   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Valida Inscrição estadual do XML com Cliente/Fornecedorl   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ MATA140I                                                   º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

Function A140INSC(cINSCXML,cINSCTAB)

Local lRet := .F.

//Elimina espaço em branco e caracteres especiais
cINSCXML := AllTrim(cINSCXML)
cINSCXML := A140ICAES(cINSCXML)

//Elimina espaço em branco e caracteres especiais
cINSCTAB := AllTrim(cINSCTAB)
cINSCTAB := A140ICAES(cINSCTAB)

If (cINSCXML $ cINSCTAB) .Or. (cINSCTAB $ cINSCXML)
	lRet := .T.
Endif

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} MT140DUP
Verifica duplicidade na amarração da nf de origem

@param		aItemSDT	Array com os itens do documento

@author	rodrigo.mpontes
@since		25/06/2019
/*/
//-------------------------------------------------------------------

Static Function MT140DUP(aItemSDT)

Local nNFOri	:= 0
Local nSEOri	:= 0
Local nITOri	:= 0
Local nI		:= 0
Local nY		:= 0
Local cChvDoc	:= ""
Local lNFDup	:= .F.

For nI := 1 To Len(aItemSDT)
	nNFOri	:= aScan(aItemSDT[nI],{|x| x[1] == "DT_NFORI"})
	nSEOri	:= aScan(aItemSDT[nI],{|x| x[1] == "DT_SERIORI"})
	nITOri	:= aScan(aItemSDT[nI],{|x| x[1] == "DT_ITEMORI"})
	
	If nNFOri > 0 .And. nSEOri > 0 .And. nITOri > 0
		cChvDoc := aItemSDT[nI,nNFOri,2] + aItemSDT[nI,nSEOri,2] + aItemSDT[nI,nITOri,2]
		
		For nY := nI + 1 To Len(aItemSDT)
			nNFOri	:= aScan(aItemSDT[nY],{|x| x[1] == "DT_NFORI"})
			nSEOri	:= aScan(aItemSDT[nY],{|x| x[1] == "DT_SERIORI"})
			nITOri	:= aScan(aItemSDT[nY],{|x| x[1] == "DT_ITEMORI"})
			
			If nNFOri > 0 .And. nSEOri > 0 .And. nITOri > 0
				If cChvDoc == aItemSDT[nY,nNFOri,2] + aItemSDT[nY,nSEOri,2] + aItemSDT[nY,nITOri,2]
					lNFDup := .T.
					Exit
				Endif
			Endif
		Next nY
	Endif
Next nI

//Se encontrou duplicidade, é limpo a amarração para que o usuario
//faça a amarração manualmente
If lNFDup
	For nI := 1 To Len(aItemSDT)
		nNFOri	:= aScan(aItemSDT[nI],{|x| x[1] == "DT_NFORI"})
		nSEOri	:= aScan(aItemSDT[nI],{|x| x[1] == "DT_SERIORI"})
		nITOri	:= aScan(aItemSDT[nI],{|x| x[1] == "DT_ITEMORI"})
		
		If nNFOri > 0 .And. nSEOri > 0 .And. nITOri > 0
			aItemSDT[nI,nNFOri,2] := ""
			aItemSDT[nI,nSEOri,2] := ""
			aItemSDT[nI,nITOri,2] := ""
		Endif
	Next nI
Endif

Return aItemSDT
