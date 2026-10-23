#Include 'Protheus.ch' 
#Include 'TOPConn.ch' 
#Include 'COMXCOL.ch'
#Include "FILEIO.CH"
#Include "TbiConn.ch"
#Include 'RwMake.ch'
#Include "FWEVENTVIEWCONSTS.CH"
#INCLUDE 'FWLIBVERSION.CH'
#INCLUDE 'MATA140I.ch'  

//-------------------------------------------------------------------
/*/{Protheus.doc} COMATUTRANS
Atualiza Transmite com documentos gerados

@author	Rodrigo M Pontes
@since 14/05/22
/*/
//------------------------------------------------------------------- 

Function COMATUTRANS(aTransmite,nOpc)

Local oComTransmite := Nil
Local lImpXML       := SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))
Local cTraCID       := SuperGetMv("MV_XMLCID",.F.,"")
Local cTraCSEC      := SuperGetMv("MV_XMLCSEC",.F.,"")

Default nOpc := 1

If lImpXML .And. !Empty(cTraCID) .And. !Empty(cTraCSEC)
    oComTransmite := ComTransmite():New()

    If oComTransmite:TokenTotvsTransmite() 
        //Busca XML no Transmite e grava na CKO
        If nOpc == 1
            oComTransmite:XMLEXPORTED(2,aTransmite) 
        Elseif nOpc == 2 //Atualiza Transmite de 3 para 2 (De SF1/SD1 para apenas CKO)
            oComTransmite:XMLEXPORTED(3,aTransmite) 
        Endif
    Endif
Endif

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} ImpXMLErr
Atualiza Erro durante importação do XML

@author	Rodrigo M Pontes
@since 14/05/22
/*/
//------------------------------------------------------------------- 

Function ImpXMLErr(lJob,cFile,aErros,cMsgJob,cMsgAviso,cMsgSolJob,cCodErr,aErroErp)

Default cCodErr := ""

If lJob
	aAdd(aErros,{cFile,cMsgJob,cMsgSolJob})
Else
	Aviso(STR0082,cMsgAviso,{STR0004},2,"ImpXMLNFsT")
EndIf

If !Empty(cCodErr)
	aAdd(aErroErp,{cFile,cCodErr})
Endif

Return


//-------------------------------------------------------------------
/*/{Protheus.doc} ImpXMLNFsT
Importar NFS para CKO

@author	Rodrigo M Pontes
@since 14/05/22
/*/
//------------------------------------------------------------------- 


Function ImpXMLNFsT(cFile,lJob,aProc,aErros,oFullXML,aErroERP)

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
Local cMsgAviso		:= ""
Local cMsgJob		:= ""
Local cMsgSolJob	:= ""
Local cCodErr		:= ""

Private lMsErroAuto	:= .F.

Default lJob   	 	:= .T.
Default cFile		:= ""
Default aProc		:= {}
Default aErros		:= {}
Default oFullXML	:= NIL

//-- Verifica erro na sintaxe do XML
If Empty(oFullXML) .Or. !Empty(cError)
	//"Erro de sintaxe no arquivo XML: "#"Entre em contato com o emissor do documento e comunique a ocorrência."
	ImpXMLErr(lJob,cFile,@aErros,STR0101+cError,cError,STR0102,"",@aErroERP)
	lProces := .F.
Else
	oFullXML	:= XmlChildEx(oFullXML,"_PROCTRANSMITENFSE")
	cCGCTT  	:= oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_TOMADOR:_CNPJTOM:TEXT
	cCGCTP		:= Iif(XmlChildEx(oFullXML:_TRANSMITE:_RETTRANSMITENFSE,"_CNPJPREST") # NIL,;
							oFullXML:_TRANSMITE:_RETTRANSMITENFSE:_CNPJPREST:TEXT,;
							oFullXML:_TRANSMITE:_RETTRANSMITENFSE:_CPFPREST:TEXT)
EndIf

If lProces
	aDirFilial := DirFilial(cFile,cCGCTT,"",lJob)
	If !aDirFilial[1] 
		If !aDirFilial[2]
			cMsgAviso 	:= Iif(aDirFilial[3],STR0244,Iif(aDirFilial[4],STR0254,STR0085))
			cMsgJob 	:= Iif(aDirFilial[3],"COM042 - " + STR0244,Iif(aDirFilial[4],"COM052 - " + STR0254,"COM002 - " + STR0085))
			cMsgSolJob	:= Iif(aDirFilial[3],STR0245,Iif(aDirFilial[4],STR0255,STR0246))
			cCodErr		:= Iif(aDirFilial[3],"COM042",Iif(aDirFilial[4],"COM052","COM002"))

			ImpXMLErr(lJob,cFile,@aErros,cMsgJob,cMsgAviso,cMsgSolJob,cCodErr,@aErroERP)

			//lJob = F
			//aDirFilial[3] -> "Erro"#""Existe mais de uma Empresa/Filial para este XML." "#"OK"
			//aDirFilial[4] -> "Erro"#""Este XML não pertence a nenhuma empresa/filial e não podera ser processado." "#"OK"
			//"Erro"#""Este XML pertence a outra empresa/filial e não podera ser processado na empresa/filial corrente." "#"OK"

			//lJob = T
			//aDirFilial[3] -> Existe mais de uma Empresa/Filial para este XML. // Selecione a Empresa/Filial deste XML através da rotina Reprocessar no Monitor do TOTVS Colaboração.
			//aDirFilial[4] -> "Este XML não pertence a nenhuma empresa/filial e não podera ser processado." //"Verificar se XML pertence a empresa"
			// Este XML pertence a outra empresa/filial e não poderá ser processado na empresa/filial corrente. // Importe na Empresa/Filial correta.
			lProces:= .F. 
		Else
			// Este XML pertence a outra empresa/filial e não poderá ser processado na empresa/filial corrente. // Importe na Empresa/Filial correta.
			ImpXMLErr(lJob,cFile,@aErros,"COM002 - " + STR0085,"",STR0246,"COM002",@aErroERP)
			lProces  := .F.
		Endif
	Endif
Endif
	
If lProces
	SA2->(dbSetOrder(3))
	If !SA2->(dbSeek(xFilial('SA2')+AllTrim(cCGCTP)))  
		//Verifica se está cadastrado o prestador de servico
		ImpXMLErr(lJob,cFile,@aErros,"COM007 - " + STR0040 + oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_PRESTADOR:_RSOCIALPREST:TEXT  +" [" + Transform(cCGCTP,"@R 99.999.999/9999-99") +"] "+ STR0109,STR0208,STR0110,"COM007",@aErroERP)

		//lJob = F -> "Erro"#""Este XML possui um prestador de serviço que não está cadastrado na empresa/filial corrente." "#"OK"
		//lJob = T -> "Fonecedor"#"inexistente na base."#"Gere cadastro para este fornecedor."
		lProces  := .F.	              
	Else
		cCodigo :=	SA2->A2_COD
		cLoja	:=	SA2->A2_LOJA   
		cNomeFor:=	SA2->A2_NOME
	EndIf      
EndIf

If lProces	
	If ValType(XmlChildEx(oFullXML:_TRANSMITE:_RETTRANSMITENFSE,"_NNFSE")) == "O"
		cDoc	:= StrZero(Val(AllTrim(oFullXML:_TRANSMITE:_RETTRANSMITENFSE:_NNFSE:TEXT)),TamSx3("F1_DOC")[1])
		cSerie	:= Replicate(" ", TamSx3("F1_SERIE")[1])

		If ValType(XmlChildEx(oFullXML:_TRANSMITE:_RETTRANSMITENFSE,"_DTEMISNFSE")) == "O"
			dDtEmis	:= StoD(StrTran(AllTrim(oFullXML:_TRANSMITE:_RETTRANSMITENFSE:_DTEMISNFSE:TEXT),"-",""))
			cHrEmis	:= Substr(oFullXML:_TRANSMITE:_RETTRANSMITENFSE:_DTEMISNFSE:TEXT,12)
		Else
			ImpXMLErr(lJob,cFile,@aErros,"COM034 - " + STR0240,STR0240,STR0241,"COM034",@aErroErp)
			//lJob = F -> Erro#Tag _DTEMISNFSE não encontrada#OK 
			//lJob = T -> Tag _DTEMISNFSE não encontrada#Verificar com quem originou o XML.
			lProces := .F.
		Endif

		If lProces
			If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_TOMADOR,"_UFTOM")) == "O" .And.;
				!Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_TOMADOR:_UFTOM:TEXT)
				cUFTom := oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_TOMADOR:_UFTOM:TEXT
			Else
				ImpXMLErr(lJob,cFile,@aErros,"COM038 - " + STR0243,STR0243,STR0241,"COM038",@aErroErp)
				//lJob = F -> Erro#Tag _UFTOM nao encontrada#OK
				//lJob = T -> Tag _UFTOM nao encontrada#Verificar com quem originou o XML.
				lProces := .F.
			EndIf
		Endif

		If lProces .And. ValType(XmlChildEx(oFullXML:_TRANSMITE:_RETTRANSMITENFSE,"_NRPS")) == "O"
			cRPS := Alltrim(oFullXML:_TRANSMITE:_RETTRANSMITENFSE:_NRPS:TEXT)		
		Endif
		
		If lProces .And. ValType(XmlChildEx(oFullXML:_TRANSMITE:_RETTRANSMITENFSE,"_CVERIFICANFSE")) == "O"
			cCodNFE := Alltrim(oFullXML:_TRANSMITE:_RETTRANSMITENFSE:_cVerificaNFSe:TEXT)
		Endif		 
	Else
		ImpXMLErr(lJob,cFile,@aErros,"COM035 - " + STR0242,STR0242,STR0241,"COM035",@aErroErp)
		//lJob = F -> Erro#Tag _NNFSE não encontrada#OK
		//lJob = T -> Tag _NNFSE não encontrada#Verificar com quem originou o XML.
		lProces	 := .F.
	Endif
Endif

If lProces
	DbSelectArea("SDS")
	SDS->(DbSetOrder(1))
	If (SDS->(DbSeek(xFilial("SDS")+cDoc+cSerie+cCodigo+cLoja)))//Filial + RPS + SERIE RPS + FORNECEDOR + LOJA  
		lProces	 := .F.
	EndIf
Endif
  
If lProces
	If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS,"_ITEM" )) == "A"
		aItens := oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM
		
		If Len(aItens) > 0
			// Codigo de servico
			cCodServ := Iif(ValType(aItens[1]:_CODIGOITEMLISTASERVICO) == "O" .And. !Empty(aItens[1]:_CODIGOITEMLISTASERVICO:TEXT),;
							aItens[1]:_CODIGOITEMLISTASERVICO:TEXT,;
							Iif(ValType(aItens[1]:_CITEMLISTASERVICO) == "O" .And. !Empty(aItens[1]:_CITEMLISTASERVICO:TEXT),;
								aItens[1]:_CITEMLISTASERVICO:TEXT,;
								Iif(ValType(aItens[1]:_CODIGOCFPS) == "O" .And. !Empty(aItens[1]:_CODIGOCFPS:TEXT),;
									aItens[1]:_CODIGOCFPS:TEXT,;
									Iif(ValType(aItens[1]:_CTRIBUTMUN) == "O" .And. !Empty(aItens[1]:_CTRIBUTMUN:TEXT),;
										aItens[1]:_CTRIBUTMUN:TEXT,""))))
			 
			//ISS pela tag ITEM
			If ValType(XmlChildEx(aItens[1],"_ALISS")) == "O" .And. !Empty(aItens[1]:_ALISS:TEXT)
				nAlqISS		:= Val(aItens[1]:_ALISS:TEXT)
			Endif

			If ValType(XmlChildEx(aItens[1],"_VLISS")) == "O" .And. !Empty(aItens[1]:_VLISS:TEXT)
				nVlrISS		:= Val(aItens[1]:_VLISS:TEXT)
			Endif
			
			lISSIt := .T.
		Endif
	Elseif ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS,"_ITEM" )) == "O"
		//Verifica existencia do grupo Itens
        If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_VLUNIT" )) == "O" .And.;
            ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_VLITEM" )) == "O" .And.;
            ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_QTDE" )) == "O"

            aItens := {oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM}
        Endif

        If Len(aItens) > 0
			// Codigo de servico
			cCodServ := Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_CODIGOITEMLISTASERVICO")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CODIGOITEMLISTASERVICO:TEXT),;
							oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CODIGOITEMLISTASERVICO:TEXT ,;
							Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_CITEMLISTASERVICO")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CITEMLISTASERVICO:TEXT),;
								oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CITEMLISTASERVICO:TEXT,;
								Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_CODIGOCFPS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CODIGOCFPS:TEXT),;
									oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CODIGOCFPS:TEXT,;
									Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_CTRIBUTMUN")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CTRIBUTMUN:TEXT),;
										oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_CTRIBUTMUN:TEXT,""))))

            //ISS pela tag ITEM
            If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_ALISS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_ALISS:TEXT)
                nAlqISS		:= Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_ALISS:TEXT)
            Endif
            
            If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM,"_VLISS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_VLISS:TEXT)
                nVlrISS		:= Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_ITEM:_VLISS:TEXT)
            Endif
            
            lISSIt := .T.
        Endif
	EndIf

	// Codigo de servico
	cCodServ := Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_ITEMLISTASERV")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_ITEMLISTASERV:TEXT),;
					oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_ITEMLISTASERV:TEXT,;
					Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_CODIGOCFPS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_CODIGOCFPS:TEXT),;
						oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_CODIGOCFPS:TEXT,;
						Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_CTRIBUTMUN")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_CTRIBUTMUN:TEXT),;
							oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_CTRIBUTMUN:TEXT,"")))

	//ISS pela tag SERVICO
    If !lISSIt
        If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_ALISS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_ALISS:TEXT)
            nAlqISS := Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_ALISS:TEXT)
        Endif
        
        If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_VLISS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLISS:TEXT)
            nVlrISS := Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLISS:TEXT)
        Endif
    Endif

	//PIS pela tag SERVICO
	If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_VLPIS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLPIS:TEXT)
		nVlrPIS := Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLPIS:TEXT)
	Endif 
	
	//COFINS pela tag SERVICO
	If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_VLCOFINS")) == "O" .And. !Empty(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLCOFINS:TEXT)
		nVlrCOF := Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLCOFINS:TEXT)
	Endif
    
    // Descricao do servico
    If ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_DESCRICAO,"_DESRPS")) == "O"
        cDescServ	:= oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_DESCRICAO:_DESRPS:TEXT			
    EndIf
    
    // Municipio do servico
    If ValType(XmlChildEx(oFUllXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO,"_CMUNSERV")) == "O"
        cMunServ	:= Right(oFUllXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_CMUNSERV:TEXT,7)
    EndIf
	
	//Ponto de entrada para manipular o código do serviço
	IF ExistBlock("MT140ISV")
		cMT140ISV 	:= ExecBlock("MT140ISV",.F.,.F.,{cCodServ, cMunServ, cCGCTT, cCGCTP})
		cCodServ	:= Iif(ValType(cMT140ISV) == "C" .And. !Empty(cCodServ),cMT140ISV,cCodServ)
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
		cFiltro := Iif(ValType(cFiltro) <> "C","",cFiltro)
	Endif
		
	cQry	+= " AND (SB1.B1_CODISS = '" + cCodServ + "' OR SBZ.BZ_CODISS = '" + cCodServ + "' " + cFiltro + " )"
	cQry	+= " AND SA2.A2_CGC = '" + cCGCTP + "'"
	cQry	+= " AND SB1.D_E_L_E_T_ = ''"
			
	cQry := ChangeQuery(cQry)
	dbUseArea(.T., "TOPCONN", TCGenQry(,,cQry),"SB1TMP", .T., .T.)                   
        
    If SB1TMP->(Eof()) //Verifica se possui pelo menos uma ocorrencia do codigo de serviço do XML   
		//Nao processa XML de outra empresa/filial
		ImpXMLErr(lJob,cFile,@aErros,"COM018 - " + STR0214+cCodServ+STR0215+SA2->A2_NOME+" ["+cCGCTP+"]. "+STR0217+cDescServ+".",STR0209,STR0216,"COM018",@aErroErp)

		//lJob = F ->"Erro"#"""Este XML possui um codigo de Serviço que não está cadastrado em um produto na empresa/filial corrente."#"OK"
		//lJob = T ->"Código de serviço "+cCodServ+" não cadastrado em um produto, na empresa/filial corrente, e/ou produto não possui amarração com o fornecedor "+SA2->A2_NOME+cCGC. Descrição do serviço:+cDescServ.
		lProces  := .F.
	Else
		cProduto:= SB1TMP->B1_COD
	EndIf  
	SB1TMP->(dbCloseArea())
EndIf

If lProces 	
	// Versao layout
	cNFsVersao := Iif(ValType(XmlChildEx(oFullXML,"_VERSAO")) == "O",;
					  oFullXML:_VERSAO:TEXT,;
					  Iif(ValType(XmlChildEx(oFullXML:_TRANSMITE:_TRANSMITERPS,"_VERSAO")) == "O",;
					  	  oFullXML:_TRANSMITE:_TRANSMITERPS:_VERSAO:TEXT,""))

	//Grava os Dados do Cabecalho - SDS
	DbSelectArea("SDS")
	AADD(aHeadSDS,{{"DS_FILIAL"	    ,xFilial("SDS")																	    },; //Filial
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
				    {"DS_HORAIMP"	,SubStr(Time(),1,5)															   		},; //Hora importacao XML
				   	{"DS_CODNFE" 	,cCodNFE																			},; //Codigo de verificaçao na NFe
					{"DS_NUMRPS"	,cRPS																				},; //Numero do RPS
					{"DS_HORNFE"	,cHrEmis																			}}) //Hora de emissao da NFe

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
							//"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
							lProces := .F.
							ImpXMLErr(lJob,cFile,@aErros,"COM050 - " + STR0253 + cProduto,"",STR0198,"COM050",@aErroErp)
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
		 					{"DT_QUANT"  	,nQtdeIt                									   		},; //Qtde
			 				{"DT_VUNIT"		,nPrcIt                     										},; //Vlor Unitário
			 				{"DT_FORNEC"	,cCodigo															},; //Forncedor
			 				{"DT_LOJA"   	,cLoja																},; //Lja
				 			{"DT_DOC"    	,cDoc																},; //DocmTo
		 					{"DT_SERIE"		,cSerie							   									},; //Serie
		 					{"DT_TOTAL"		,nTotIt                     										}}) //Vlor Total
		 					
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
		nPrcIt	:= Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLSERVICOS:TEXT)
		nTotIt	:= Val(oFullXML:_TRANSMITE:_TRANSMITERPS:_RPS:_SERVICO:_VLSERVICOS:TEXT)
		
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
						//"Não foi possivel converter para 1ª unidade de medida, pois o produto não possui fator de conversão. "
						lProces := .F.
						ImpXMLErr(lJob,cFile,@aErros,"COM050 - " + STR0253 + cProduto,"",STR0198,"COM050",@aErroErp)
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
		 				{"DT_VUNIT"		,nPrcIt																		},; //Vlor Unitário
		 				{"DT_FORNEC"	,cCodigo																	},; //Forncedor
		 				{"DT_LOJA"   	,cLoja																		},; //Lja
			 			{"DT_DOC"    	,cDoc																		},; //DocmTo
	 					{"DT_SERIE"		,cSerie							   											},; //Serie
	 					{"DT_TOTAL"		,nPrcIt																		},; //Vlor Total
	 					{"DT_XALQISS"	,nAlqISS																	},; //Aliquota ISS
	 					{"DT_XMLISS"	,nVlrISS																	},; //Valor ISS
						{"DT_XMLPIS"	,nVlrPIS																	},; //Valor PIS
						{"DT_XMLCOF"	,nVlrCOF			 														}}) //Valor COF 

						If lUnidMed 
							aAdd(aItemSDT[Len(aItemSDT)],{"DT_UM"  		, cUM})
							aAdd(aItemSDT[Len(aItemSDT)],{"DT_SEGUM"  	, cSEGUM})
							aAdd(aItemSDT[Len(aItemSDT)],{"DT_QTSEGUM"  , nQtSEGUM})
						Endif 
	EndIf								 			 						

	//Grava os dados do cabeçalho e itens da nota importada do XML
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
