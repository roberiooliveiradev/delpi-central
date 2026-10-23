#include "protheus.ch" 
#include "tbiconn.ch"
#include "fwlibversion.ch"

Static oQryFltDoc 	:= NIL as object
Static oQryIdTrib 	:= NIL as object


//-----------------------------------------------------------------------
/*/{Protheus.doc} nfseXMLEnv
Função que monta o XML Unico de envio para NFS-e TSS / TOTVS Colaboracao 2.0

@author Marcos Taranta
@since 19.01.2012

@param	cTipo		Tipo do documento.
@param	dDtEmiss	Data de emissão do documento.
@param	cSerie		Serie do documento.
@param	cNota		Numero do documento.
@param	cClieFor	Cliente/Fornecedor do documento.
@param	cLoja		Loja do cliente/fornecedor do documento.
@param	cMotCancela	Motivo do cancelamento do documento.
@param	cCodcanc	Codigo do cancelamento do documento.

@return	cString		Tag montada em forma de string. 
/*/
//-----------------------------------------------------------------------
User function nfseXMLUni( cCodMun, cTipo, dDtEmiss, cSerie, cNota, cClieFor, cLoja, cMotCancela, aAIDF, cCodcanc )

	Local nX		:= 0
	Local nW		:= 0
	Local nZ		:= 0

	Local cString    := ""
	Local cAliasSE1  := "SE1"
	Local cAliasSD2  := "SD2"
	local cCFPS      := ""
	Local cNatOper   := ""
	Local cModFrete  := ""
	Local cScan      := ""
	Local cEspecie   := ""
	Local cMensCli   := ""
	Local cMensFis   := ""
	Local cMV_LJTPNFE:= SuperGetMV("MV_LJTPNFE", ," ")
	lOCAL cMVSUBTRIB := IIf(FindFunction("GETSUBTRIB"), GetSubTrib(), SuperGetMv("MV_SUBTRIB"))
	Local cLJTPNFE   := ""
	Local cWhere     := ""
	Local cMunISS    := ""
	Local cTipoPcc   := "PIS','COF','CSL','CF-','PI-','CS-"
	Local cCodCli    := ""
	Local cLojCli    := ""
	Local cDescMunP  := ""
	local cMunPSIAFI := ""
	local cMunPrest  := ""
	Local cDescrNFSe := ""
	Local cDiscrNFSe := ""
	Local cTpCliente := ""
	Local cF4Agreg   := ""
	Local cNatOP     := "1"
	Local cFieldMsg  := ""
	Local cCamSC5    := SuperGetMV("MV_NFSECOM", .F., "") // Parametro que aponta para o campo do SC5 com a data da competencia

	Local aObra		 := &(SuperGetMV("MV_XMLOBRA", ,"{,,,,,,,,,,,,,,}"))
	Local cLogradOb  := ""
	Local cCompleOb  := "" 
	Local cNumeroOb  := ""
	Local cBairroOb  := ""
	Local cCepOb     := ""
	Local cCodMunob  := ""
	Local cNomMunOb  := ""
	Local cUfOb 	   := ""
	Local cCodPaisOb := ""
	Local cNomPaisOb := ""
	Local cNumArtOb  := ""
	Local cNumCeiOb  := ""
	Local cNumProOb  := ""
	Local cNumMatOb  := ""
	Local cNumEncap  := "" // NumeroEncapsulamento
	Local cNatPCC		:= GetNewPar("MV_1DUPNAT","SA1->A1_NATUREZ") //-- Natureza considerada para retencao de PIS, COF, CSLL 
	Local cCondPag   := "" // Condição de pagamento E4_COND
	Local dDateCom 	:= Date()
	Local nRetPis   := 0
	Local nRetCof   := 0
	Local nRetCsl   := 0
	Local nPosI     := 0
	Local nPosF     := 0
	Local nAliq     := 0
	Local nCont     := 0
	Local nDescon   := 0
	Local nScan     := 0
	Local nRetDesc  := 0
	Local nValTotPrd:= 0
	Local nBasCsl   := 0
	Local nBasCof   := 0
	Local nBasPis   := 0
	Local lQuery    := .F.
	Local lCalSol   := .F.
	Local lEECFAT   := SuperGetMv("MV_EECFAT")
	Local lAglutina := AllTrim(GetNewPar("MV_ITEMAGL","N")) == "S" //-- Aglutinar ITENS do RPS na geracao do XML
	Local lNatOper  := GetNewPar("MV_NFESERV","1") == "1" //-- Descr do servico 1-pedido vendas+SX5 ou 2-somente SX5
	Local lNFeDesc  := GetNewPar("MV_NFEDESC",.F.) //-- Descr do servico = pela tab. 60 e do produto = pedidos de vendas
	Local lNfsePcc  := GetNewPar("MV_NFSEPCC",.F.) //-- Considerar retencao de PIS, COF, CSLL
	Local lCrgTrib  := GetNewPar("MV_CRGTRIB",.F.)
	Local lUsaSF3  	:= GetNewPar("MV_ENVSF3",.F.)
	Local lMvDescInc	:= SuperGetMV("MV_NFSEDIN",,.F. )	// Habilita/Desabilita os Descontos Incondicionados da NFSE
	Local cNatBusc   := ""
	Local cMsgSX5	:= ""
	Local cLibVersion := allTrim( FwLibVersion() )
	local cMVTPABISS	:= GetMv("MV_TPABISS")

	Local aRetSX5	:= {}
	Local aNota     := {}
	Local aDupl     := {}
	Local aDest     := {}
	Local aEntrega  := {}
	Local aProd     := {}
	Local aICMS     := {}
	Local aICMSST   := {}
	Local aIPI      := {}
	Local aPIS      := {}
	Local aCOFINS   := {}
	Local aPISST    := {}
	Local aCOFINSST := {}
	Local aISSQN    := {}
	Local aISS      := {}
	Local aCST      := {}
	Local aRetido   := {}
	Local aTransp   := {}

	Local aVeiculo  := {}
	Local aReboque  := {}
	Local aEspVol   := {}
	Local aNfVinc   := {}
	Local aPedido   := {}
	Local aTotal    := {0,0,"",0,""}
	Local aOldReg   := {}
	Local aOldReg2  := {}
	Local aMed      := {}
	Local aArma     := {}
	Local aveicProd := {}
	Local aIEST     := {}
	Local aDI       := {}
	Local aAdi      := {}
	Local aExp      := {}
	Local aDeducao  := {}

	Local aDeduz    := {}
	Local aConstr   := {}
	Local aInterm	:= {}
	Local aRetISS   := {}
	Local aRetPIS   := {}
	Local aRetCOF   := {}
	Local aRetCSL   := {}
	Local aRetIRR   := {}
	Local aRetINS   := {}
	Local cQuery	 := ""
	
	Local aUF     		:= {}
	Local lVldExc  		:= FindClass("totvs.protheus.backoffice.tss.engine.tributaveis.TSSTCIntegration")
	Local lConfTrib		:= .F.
	Local oISSCfg    	as Json
	Local dNfseIbs  	:= SuperGetMv('MV_RTC56',.f.,stod('20260101'))
	Private oNfTciIntg  :=  NIL as object
	Private aRetSF3	:= {}

	DEFAULT cCodMun     := PARAMIXB[1]
	DEFAULT cTipo       := PARAMIXB[2]
	DEFAULT cSerie      := PARAMIXB[4]
	DEFAULT cNota       := PARAMIXB[5]
	DEFAULT cClieFor    := PARAMIXB[6]
	DEFAULT cLoja       := PARAMIXB[7]
	DEFAULT cMotCancela := PARAMIXB[8]
//	DEFAULT aAIDF       := PARAMIXB[9]
	If type("PARAMIXB[10]") <> "U" 
		DEFAULT cCodCanc	:= IIf ( !Empty(PARAMIXB[10]),PARAMIXB[10], "")
	Else 
		DEFAULT cCodCanc	:= ""
	Endif 

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Preenchimento do Array de UF                                            ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	aadd(aUF,{"RO","11"})
	aadd(aUF,{"AC","12"})
	aadd(aUF,{"AM","13"})
	aadd(aUF,{"RR","14"})
	aadd(aUF,{"PA","15"})
	aadd(aUF,{"AP","16"})
	aadd(aUF,{"TO","17"})
	aadd(aUF,{"MA","21"})
	aadd(aUF,{"PI","22"})
	aadd(aUF,{"CE","23"})
	aadd(aUF,{"RN","24"})
	aadd(aUF,{"PB","25"})
	aadd(aUF,{"PE","26"})
	aadd(aUF,{"AL","27"})
	aadd(aUF,{"MG","31"})
	aadd(aUF,{"ES","32"})
	aadd(aUF,{"RJ","33"})
	aadd(aUF,{"SP","35"})
	aadd(aUF,{"PR","41"})
	aadd(aUF,{"SC","42"})
	aadd(aUF,{"RS","43"})
	aadd(aUF,{"MS","50"})
	aadd(aUF,{"MT","51"})
	aadd(aUF,{"GO","52"})
	aadd(aUF,{"DF","53"})
	aadd(aUF,{"SE","28"})
	aadd(aUF,{"BA","29"})
	aadd(aUF,{"EX","99"})

	//-----------------------------------------------------------------------------------
	// - Verifica a necessidade de atualizacao de LIB para utilizar o comando FWGetSX5
	//-----------------------------------------------------------------------------------
	if( cLibVersion < "20170511" )
		cMsgSX5 := "Para obter as descrições corretas da tabela SX5, por favor, atualize a LIB." + chr( 13 ) + chr( 10 )
		cMsgSX5 += "Versão atual: " + cLibVersion + chr( 13 ) + chr( 10 )
		cMsgSX5 += "Versão mínima necessária: 20170511"
		
		msgAlert( cMsgSX5,"Necessário atualização de LIB" )
		cMsgSX5 := ""
	EndIf
	
	If cTipo == "1" .And. Empty(cMotCancela)
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Posiciona NF                                                            ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		dbSelectArea("SF2")
		dbSetOrder(1) //F2_FILIAL, F2_DOC, F2_SERIE, F2_CLIENTE, F2_LOJA, F2_FORMUL, R_E_C_N_O_, D_E_L_E_T_
		DbGoTop()
		If DbSeek(xFilial("SF2")+cNota+cSerie+cClieFor+cLoja)

			aadd(aNota,IIF(cCodMun == "3526902","RPSL",SF2->F2_SERIE) )
			aadd(aNota,IIF(Len(SF2->F2_DOC)==6,"000","")+SF2->F2_DOC)
			aadd(aNota,SF2->F2_EMISSAO)
			aadd(aNota,cTipo)
			aadd(aNota,SF2->F2_TIPO)
			aadd(aNota,"1")
			aadd(aNota,IIF(Len(SF2->F2_DOC)==6,"000","")+AllTrim(SF2->F2_NFSUBST))
			aadd(aNota,AllTrim(SF2->F2_SERSUBS))
			aadd(aNota,AllTrim(SF2->F2_HORA) + ":" + SUBSTR(Time(), 7, 2))
			dbSelectArea("SE4")
			dbSetOrder(1)			
			If DbSeek(xFilial("SE4")+SF2->F2_COND)
					aadd(aNota,SE4->E4_DESCRI)
					cCondPag := SE4->E4_COND
			EndIf
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Posiciona cliente ou fornecedor                                         ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If !SF2->F2_TIPO $ "DB"
				If IntTMS()
					DT6->(DbSetOrder(1))
					If DT6->(DbSeek(xFilial("DT6")+SF2->(F2_FILIAL+F2_DOC+F2_SERIE)))
						cCodCli := DT6->DT6_CLIDEV
						cLojCli := DT6->DT6_LOJDEV
					Else
						cCodCli := SF2->F2_CLIENTE
						cLojCli := SF2->F2_LOJA
					EndIf
				Else
					cCodCli := SF2->F2_CLIENTE
					cLojCli := SF2->F2_LOJA
				EndIf

				dbSelectArea("SA1")
				dbSetOrder(1) //A1_FILIAL+A1_COD+A1_LOJA
				DbSeek(xFilial("SA1")+cCodCli+cLojCli)
				
				aadd(aDest,AllTrim(SA1->A1_CGC))
				aadd(aDest,SA1->A1_NOME)
				aadd(aDest,myGetEnd(SA1->A1_END,"SA1")[1])
				aadd(aDest,convType(IIF(myGetEnd(SA1->A1_END,"SA1")[2]<>0,myGetEnd(SA1->A1_END,"SA1")[2],"SN")))
				aadd(aDest,IIF(SA1->(FieldPos("A1_COMPLEM")) > 0 .And. !Empty(SA1->A1_COMPLEM),SA1->A1_COMPLEM,myGetEnd(SA1->A1_END,"SA1")[4]))
				aadd(aDest,SA1->A1_BAIRRO)
				If !Upper(SA1->A1_EST) == "EX"
					aadd(aDest,SA1->A1_COD_MUN)
					aadd(aDest,SA1->A1_MUN)
				Else
					aadd(aDest,"9999999")
					aadd(aDest,"EXTERIOR")
				EndIf
				aadd(aDest,Upper(SA1->A1_EST))
				aadd(aDest,SA1->A1_CEP)
				aadd(aDest,IIF(Empty(SA1->A1_PAIS),"1058"  ,Posicione("SYA",1,xFilial("SYA")+SA1->A1_PAIS,"YA_SISEXP")))
				aadd(aDest,IIF(Empty(SA1->A1_PAIS),"BRASIL",Posicione("SYA",1,xFilial("SYA")+SA1->A1_PAIS,"YA_DESCR" )))
				aadd(aDest,SA1->A1_DDD+SA1->A1_TEL)
				aadd(aDest,vldIE(SA1->A1_INSCR,IIF(SA1->(FIELDPOS("A1_CONTRIB"))>0,SA1->A1_CONTRIB<>"2",.T.)))
				aadd(aDest,SA1->A1_SUFRAMA)
				aadd(aDest,SA1->A1_EMAIL)
				aadd(aDest,SA1->A1_INSCRM)
				aadd(aDest,SA1->A1_CODSIAF)
				aadd(aDest,SA1->A1_NATUREZ) //19 - Natureza no cliente
				aadd(aDest,Iif(!Empty(SA1->A1_SIMPNAC),SA1->A1_SIMPNAC,"2"))
				aadd(aDest,Iif(SA1->(FieldPos("A1_INCULT"))> 0 , Iif(!Empty(SA1->A1_INCULT),SA1->A1_INCULT,"2"), "2"))
				aadd(aDest,SA1->A1_TPESSOA)
				aadd(aDest,SF2->F2_DOC)
				aadd(aDest,SF2->F2_SERIE)
				aadd(aDest,Iif(SA1->(FieldPos("A1_OUTRMUN"))> 0 ,SA1->A1_OUTRMUN,""))	//25							
				aadd(aDest,Iif(SA1->(FieldPos("A1_PFISICA"))> 0 ,SA1->A1_PFISICA,""))	//26

				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Posiciona Natureza                                                      ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				cNatBusc := NatPCC ( aDest , cNatPCC )
				DbSelectArea("SED")
				DbSetOrder(1) //ED_FILIAL+ED_CODIGO
				DbSeek(xFilial("SED")+ cNatBusc ) 
				
				If SF2->(FieldPos("F2_CLIENT"))<>0 .And. !Empty(SF2->F2_CLIENT+SF2->F2_LOJENT) .And. SF2->F2_CLIENT+SF2->F2_LOJENT<>SF2->F2_CLIENTE+SF2->F2_LOJA
					dbSelectArea("SA1")
					dbSetOrder(1)
					DbSeek(xFilial("SA1")+SF2->F2_CLIENT+SF2->F2_LOJENT)
					
					aadd(aEntrega,SA1->A1_CGC)
					aadd(aEntrega,myGetEnd(SA1->A1_END,"SA1")[1])
					aadd(aEntrega,convType(IIF(myGetEnd(SA1->A1_END,"SA1")[2]<>0,myGetEnd(SA1->A1_END,"SA1")[2],"SN")))
					aadd(aEntrega,myGetEnd(SA1->A1_END,"SA1")[4])
					aadd(aEntrega,SA1->A1_BAIRRO)
					aadd(aEntrega,SA1->A1_COD_MUN)
					aadd(aEntrega,SA1->A1_MUN)
					aadd(aEntrega,Upper(SA1->A1_EST))

				EndIf

			Else
				dbSelectArea("SA2")
				dbSetOrder(1)
				DbSeek(xFilial("SA2")+SF2->F2_CLIENTE+SF2->F2_LOJA)

				aadd(aDest,AllTrim(SA2->A2_CGC))
				aadd(aDest,SA2->A2_NOME)
				aadd(aDest,myGetEnd(SA2->A2_END,"SA2")[1])
				aadd(aDest,convType(IIF(myGetEnd(SA2->A2_END,"SA2")[2]<>0,myGetEnd(SA2->A2_END,"SA2")[2],"SN")))
				aadd(aDest,IIF(SA2->(FieldPos("A2_COMPLEM")) > 0 .And. !Empty(SA2->A2_COMPLEM),SA2->A2_COMPLEM,myGetEnd(SA2->A2_END,"SA2")[4]))				
				aadd(aDest,SA2->A2_BAIRRO)
				If !Upper(SA2->A2_EST) == "EX"
					aadd(aDest,SA2->A2_COD_MUN)
					aadd(aDest,SA2->A2_MUN)
				Else
					aadd(aDest,"9999999")			
					aadd(aDest,"EXTERIOR")
				EndIf
				aadd(aDest,Upper(SA2->A2_EST))
				aadd(aDest,SA2->A2_CEP)
				aadd(aDest,IIF(Empty(SA2->A2_PAIS),"1058"  ,Posicione("SYA",1,xFilial("SYA")+SA2->A2_PAIS,"YA_SISEXP")))
				aadd(aDest,IIF(Empty(SA2->A2_PAIS),"BRASIL",Posicione("SYA",1,xFilial("SYA")+SA2->A2_PAIS,"YA_DESCR")))
				aadd(aDest,SA2->A2_DDD+SA2->A2_TEL)
				aadd(aDest,vldIE(SA2->A2_INSCR))
				aadd(aDest,"")//SA2->A2_SUFRAMA
				aadd(aDest,SA2->A2_EMAIL)
				aadd(aDest,SA2->A2_INSCRM)
				aadd(aDest,SA2->A2_CODSIAF)
				aadd(aDest,SA2->A2_NATUREZ)
				aadd(aDest,SA2->A2_SIMPNAC)
				aadd(aDest,"")	//Nota para empresa hospitalar utilizar apenas com SF2
				aadd(aDest,"")	//Serie para empresa hospitalar utilizar apenas com SF2
				aadd(aDest,"")//Nota para empresa hospitalar utilizar apenas com SF2
				aadd(aDest,"")//Serie para empresa hospitalar utilizar apenas com SF2
				aadd(aDest,"")//A1_OUTRMUN
				aadd(aDest,Iif(SA2->(FieldPos("A2_PFISICA"))> 0 ,SA2->A2_PFISICA,""))//26

				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Posiciona Natureza                                                      ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				DbSelectArea("SED")
				DbSetOrder(1)
				DbSeek(xFilial("SED")+SA2->A2_NATUREZ)

			EndIf
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Posiciona transportador                                                 ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If !Empty(SF2->F2_TRANSP)
				dbSelectArea("SA4")
				dbSetOrder(1)
				DbSeek(xFilial("SA4")+SF2->F2_TRANSP)
				aadd(aTransp,AllTrim(SA4->A4_CGC))
				aadd(aTransp,SA4->A4_NOME)
				aadd(aTransp,SA4->A4_INSEST)
				aadd(aTransp,SA4->A4_END)
				aadd(aTransp,SA4->A4_MUN)
				aadd(aTransp,Upper(SA4->A4_EST)	)
				If !Empty(SF2->F2_VEICUL1)
					dbSelectArea("DA3")
					dbSetOrder(1)
					DbSeek(xFilial("DA3")+SF2->F2_VEICUL1)
					aadd(aVeiculo,DA3->DA3_PLACA)
					aadd(aVeiculo,DA3->DA3_ESTPLA)
					aadd(aVeiculo,"")//RNTC
					If !Empty(SF2->F2_VEICUL2)
						dbSelectArea("DA3")
						dbSetOrder(1)
						DbSeek(xFilial("DA3")+SF2->F2_VEICUL2)
						aadd(aReboque,DA3->DA3_PLACA)
						aadd(aReboque,DA3->DA3_ESTPLA)
						aadd(aReboque,"") //RNTC
					EndIf
				EndIf
			EndIf
			dbSelectArea("SF2")
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Volumes                                                                 ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			cScan := "1"
			While ( !Empty(cScan) )
				cEspecie := Upper(FieldGet(FieldPos("F2_ESPECI"+cScan)))
				If !Empty(cEspecie)
					nScan := aScan(aEspVol,{|x| x[1] == cEspecie})
					If ( nScan==0 )
						aadd(aEspVol,{ cEspecie, FieldGet(FieldPos("F2_VOLUME"+cScan)) , SF2->F2_PLIQUI , SF2->F2_PBRUTO})
					Else
						aEspVol[nScan][2] += FieldGet(FieldPos("F2_VOLUME"+cScan))
					EndIf
				EndIf
				cScan := Soma1(cScan,1)
				If ( FieldPos("F2_ESPECI"+cScan) == 0 )
					cScan := ""
				EndIf
			EndDo

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Procura duplicatas                                                      ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			
			If !Empty(SF2->F2_DUPL)	
				cLJTPNFE := (StrTran(cMV_LJTPNFE," ,"," ','"))+" "
				cWhere := cLJTPNFE
				dbSelectArea("SE1")
				dbSetOrder(1) //E1_FILIAL+E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO
				#IFDEF TOP
					lQuery  := .T.
					cAliasSE1 := GetNextAlias()
					BeginSql Alias cAliasSE1
						COLUMN E1_VENCORI AS DATE
						SELECT E1_FILIAL,E1_PREFIXO,E1_NUM,E1_PARCELA,E1_TIPO,E1_VENCORI,E1_VALOR,E1_ORIGEM,E1_CSLL,E1_COFINS,E1_PIS,E1_IRRF,E1_INSS,E1_ISS,E1_MOEDA,E1_CLIENTE,E1_LOJA,E1_BASECSL,E1_BASECOF,E1_BASEPIS
						FROM %Table:SE1% SE1
						WHERE
						SE1.E1_FILIAL = %xFilial:SE1% AND
						SE1.E1_PREFIXO = %Exp:SF2->F2_PREFIXO% AND 
						SE1.E1_NUM = %Exp:SF2->F2_DUPL% AND 
						((SE1.E1_TIPO = %Exp:MVNOTAFIS%) OR
						 SE1.E1_TIPO IN (%Exp:cTipoPcc%) OR
						 (SE1.E1_ORIGEM = 'LOJA701' AND SE1.E1_TIPO IN (%Exp:cWhere%))) AND
						SE1.%NotDel%
						ORDER BY %Order:SE1%
					EndSql
					
				#ELSE
					DbSeek(xFilial("SE1")+SF2->F2_PREFIXO+SF2->F2_DOC)
				#ENDIF
				While !Eof() .And. xFilial("SE1") == (cAliasSE1)->E1_FILIAL .And.;
					SF2->F2_PREFIXO == (cAliasSE1)->E1_PREFIXO .And.;
					SF2->F2_DOC == (cAliasSE1)->E1_NUM
					If 	(cAliasSE1)->E1_TIPO = MVNOTAFIS .OR. ((cAliasSE1)->E1_ORIGEM = 'LOJA701' .AND. (cAliasSE1)->E1_TIPO $ cWhere)

						//aadd(aDupl,{/*Neogrid não processa alfanumerico*/ "000"+Alltrim((cAliasSE1)->E1_NUM)+Alltrim((cAliasSE1)->E1_PARCELA),(cAliasSE1)->E1_VENCORI,(cAliasSE1)->E1_VALOR,(cAliasSE1)->E1_PARCELA})
						If cMVTPABISS == "2" .AND. SF2->F2_RECISS == "1"//1-ABATE VALOR LIQ / 2-GERA TITULO ISS
							nValFatura := (cAliasSE1)->(E1_VALOR-(E1_COFINS+E1_PIS+E1_CSLL+E1_IRRF+E1_INSS+E1_ISS))
							aadd(aDupl,{/*Neogrid não processa alfanumerico*/ "000"+(cAliasSE1)->E1_NUM+(cAliasSE1)->E1_PARCELA,(cAliasSE1)->E1_VENCORI,nValFatura,(cAliasSE1)->E1_PARCELA})
						Else
							nValFatura := (cAliasSE1)->(E1_VALOR - (E1_COFINS+E1_PIS+E1_CSLL+E1_IRRF+E1_INSS))
							aadd(aDupl,{/*Neogrid não processa alfanumerico*/ "000"+(cAliasSE1)->E1_NUM+(cAliasSE1)->E1_PARCELA,(cAliasSE1)->E1_VENCORI,nValFatura,(cAliasSE1)->E1_PARCELA})
						EndIf
					EndIf
					//-- Tratamento para saber se existem titulos de retenção de PIS,COFINS e CSLL
					If lNfsePcc
						If Alltrim((cAliasSE1)->E1_TIPO) $ "NF"
							nRetCsl += (cAliasSE1)->E1_CSLL 
							nRetCof += (cAliasSE1)->E1_COFINS
							nRetPis += (cAliasSE1)->E1_PIS
						EndIf
					Else
						If 	(cAliasSE1)->E1_TIPO $ cTipoPcc
							If (cAliasSE1)->E1_TIPO $ "PIS,PI-"
								nRetPis	+= 	(cAliasSE1)->E1_VALOR
							ElseIf (cAliasSE1)->E1_TIPO $ "COF,CF-"
								nRetCof	+= 	(cAliasSE1)->E1_VALOR
							ElseIf (cAliasSE1)->E1_TIPO $ "CSL,CS-"
								nRetCsl	+= 	(cAliasSE1)->E1_VALOR
							EndIf
						EndIf
					EndIf
					If Alltrim((cAliasSE1)->E1_TIPO) $ "NF"
							nBasCsl := (cAliasSE1)->E1_BASECSL
							nBasCof := (cAliasSE1)->E1_BASECOF
							nBasPis := (cAliasSE1)->E1_BASEPIS			
					EndIf
					
					dbSelectArea(cAliasSE1)
					dbSkip()
				EndDo
				If lQuery
					dbSelectArea(cAliasSE1)
					dbCloseArea()
					dbSelectArea("SE1")
				EndIf
			Else
				aDupl := {}
			EndIf

			dbSelectArea("SF3")
			dbSetOrder(4)
			If DbSeek(xFilial("SF3")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_DOC+SF2->F2_SERIE)
					
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Verifica se recolhe ISS Retido ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If SF3->(FieldPos("F3_RECISS"))>0
					If SF3->F3_RECISS $"1S"
						//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
						//³Pega retencao de ISS por item ³
						//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
						SFT->(dbSetOrder(1))
						SFT->(dbSeek(xFilial("SFT")+"S"+SF2->F2_SERIE+SF2->F2_DOC+SF2->F2_CLIENTE+SF2->F2_LOJA))
						While !SFT->(EOF()) .And. SFT->FT_FILIAL+SFT->FT_TIPOMOV+SFT->FT_SERIE+SFT->FT_NFISCAL+SFT->FT_CLIEFOR+SFT->FT_LOJA == xFilial("SFT")+"S"+SF3->F3_SERIE+SF3->F3_NFISCAL+SF3->F3_CLIEFOR+SF3->F3_LOJA
							aAdd(aRetISS,SFT->FT_VALICM)
							SFT->(dbSkip())
						EndDo

						dbSelectArea("SD2")
						dbSetOrder(3)
						dbSeek(xFilial("SD2")+SF3->F3_NFISCAL+SF3->F3_SERIE+SF3->F3_CLIEFOR+SF3->F3_LOJA)

						aadd(aRetido,{"ISS",0,SF3->F3_VALICM,SD2->D2_ALIQISS,val(SF3->F3_RECISS),aRetISS})
					Endif
				EndIf

				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Pega as deduções ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If SF3->(FieldPos("F3_ISSSUB"))>0  .And. SF3->F3_ISSSUB > 0
					If len(aDeducao) > 0
						aDeducao [len(aDeducao)] := SF3->F3_ISSSUB  
					Else
						aadd(aDeducao,{SF3->F3_ISSSUB})
					EndIf
				EndIf

				If SF3->(FieldPos("F3_ISSMAT"))>0 .And. SF3->F3_ISSMAT > 0 
					If len(aDeducao) > 0
						for nW := 1 To len(aDeducao)
							aDeducao[nW][1] += SF3->F3_ISSMAT
							exit
						next nW
					Else
						aadd(aDeducao,{SF3->F3_ISSMAT})
					EndIf
				EndIf
			EndIf

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Analisa os impostos de retencao                                         ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	
			aadd(aRetido,{"PIS",nBasPis,nRetPis,SED->ED_PERCPIS,aRetPIS})
			
			aadd(aRetido,{"COFINS",nBasCof,nRetCof,SED->ED_PERCCOF,aRetCOF})
			
			aadd(aRetido,{"CSLL",nBasCsl,nRetCsl,SED->ED_PERCCSL,aRetCSL})
			
			If SF2->(FieldPos("F2_VALIRRF"))<>0 .and. SF2->F2_VALIRRF>0
				aadd(aRetido,{"IRRF",SF2->F2_BASEIRR,SF2->F2_VALIRRF,SED->ED_PERCIRF,aRetIRR})
			EndIf
			If SF2->(FieldPos("F2_BASEINS"))<>0 .and. SF2->F2_BASEINS>0
				aadd(aRetido,{"INSS",SF2->F2_BASEINS,SF2->F2_VALINSS,SED->ED_PERCINS,aRetINS})
			EndIf
			
			//Verifica tipo do cliente.
			cTpCliente := Alltrim(SF2->F2_TIPOCLI)

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Pesquisa itens de nota                                                  ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			dbSelectArea("SD2")
			dbSetOrder(3) //D2_FILIAL+D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA+D2_COD+D2_ITEM	
			lQuery  := .T.
			If oQryFltDoc == Nil	
				cQuery += "SELECT D2_FILIAL,D2_SERIE,D2_DOC,D2_CLIENTE,D2_LOJA,D2_COD,D2_TES,D2_NFORI,D2_SERIORI,D2_ITEMORI,D2_TIPO,D2_ITEM,D2_CF, "
				cQuery += "D2_QUANT,D2_TOTAL,D2_DESCON,D2_VALFRE,D2_SEGURO,D2_PEDIDO,D2_ITEMPV,D2_DESPESA,D2_VALBRUT,D2_VALISS,D2_PRUNIT, "
				cQuery += "D2_CLASFIS,D2_PRCVEN,D2_CODISS,D2_DESCZFR,D2_PREEMB,D2_BASEISS,D2_VALIMP1,D2_VALIMP2,D2_VALIMP3,D2_VALIMP4,D2_VALIMP5,D2_PROJPMS, "
				cQuery += "D2_DESCICM,D2_TOTIMP,D2_TOTFED, D2_TOTEST, D2_TOTMUN, "
				cQuery += "D2_VALPIS,D2_VALCOF,D2_VALCSL,D2_VALIRRF,D2_VALINS,D2_ORIGLAN,D2_VALICM, D2_IDTRIB  FROM "
				cQuery += RetSqlName('SD2') + " SD2 "
				cQuery += "WHERE SD2.D2_FILIAL= ? AND SD2.D2_SERIE = ? AND SD2.D2_DOC = ? AND SD2.D2_CLIENTE = ? AND SD2.D2_LOJA = ? AND SD2.D_E_L_E_T_ = ? "
				cQuery += "ORDER BY D2_FILIAL, D2_DOC, D2_SERIE, D2_CLIENTE, D2_LOJA, D2_COD, D2_ITEM"

				oQryFltDoc	:= FwExecStatement():New(ChangeQuery(cQuery))
			EndIf	

			oQryFltDoc:SetString(1, xFilial("SD2"))
			oQryFltDoc:SetString(2,SF2->F2_SERIE)
			oQryFltDoc:SetString(3,SF2->F2_DOC)
			oQryFltDoc:SetString(4,SF2->F2_CLIENTE)
			oQryFltDoc:SetString(5,SF2->F2_LOJA)
			oQryFltDoc:SetString(6,Space(1))
			cAliasSD2	:= oQryFltDoc:OpenAlias()
			
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Posiciona na Construção Cilvil                                          ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If !Empty((cAliasSD2)->D2_PROJPMS)
				dbSelectArea("AF8")
				dbSetOrder(1)
				DbSeek(xFilial("AF8")+((cAliasSD2)->D2_PROJPMS))
				If !Empty(AF8->AF8_ART)
					aadd(aConstr,(AF8->AF8_PROJET))
					aadd(aConstr,(AF8->AF8_ART))
					aadd(aConstr,(AF8->AF8_TPPRJ))
				EndIf

			Else
				dbSelectArea("SC5")
				SC5->( dbSetOrder(1) ) //C5_FILIAL+C5_NUM
				If SC5->( MsSeek( xFilial("SC5") + (cAliasSD2)->D2_PEDIDO) )
					If ( SC5->(FieldPos("C5_OBRA")) > 0 .And. !Empty(SC5->C5_OBRA) ) .And. SC5->(FieldPos("C5_ARTOBRA")) > 0
						aadd(aConstr,(SC5->C5_OBRA)) //-- Codigo da Obra
						aadd(aConstr,(SC5->C5_ARTOBRA))
					EndIf
					If SC5->(FieldPos("C5_TIPOBRA")) > 0 .And. !Empty(SC5->C5_TIPOBRA)
						If Len(aConstr) == 0
							aadd(aConstr,"")
							aadd(aConstr,"")
						EndIf
						aadd(aConstr,(SC5->C5_TIPOBRA))
					EndIf
					// Dados do intermediário de serviço
					If SC5->(FieldPos("C5_CLIINT")) > 0 .And. SC5->(FieldPos("C5_CGCINT")) > 0 .And. SC5->(FieldPos("C5_IMINT")) > 0;
					   .And. !Empty(SC5->C5_CLIINT) .And. !Empty(SC5->C5_CGCINT) .And. !Empty(SC5->C5_IMINT)
					   						
						aadd(aInterm,(SC5->C5_CLIINT))
						aadd(aInterm,(SC5->C5_CGCINT))
						aadd(aInterm,(SC5->C5_IMINT))
						
					EndIf
				EndIf
			EndIf
			
			If Len(aConstr) < 3
				For nX := 1 To 3
					If Len(aConstr) < 3 
						aadd(aConstr,"")							
					EndIf
				Next nX
			EndIf

			If Len(aObra) < 15
				For nX := 1 To 15
					If Len(aObra) < 15 
						aadd(aObra,"")							
					EndIf
				Next nX
			EndIf

			If ValType(aObra) <> "U" .And. len (aObra) >= 15
				cLogradOb  := AllTrim(If(!Empty(aObra[01]) .And. SC5->(FieldPos(aObra[01])) > 0 , &(aObra[01]),"")) //Logradouro para Obra
				cCompleOb  := AllTrim(If(!Empty(aObra[02]) .And. SC5->(FieldPos(aObra[02])) > 0 , &(aObra[02]),"")) //Complemento para obra
				cNumeroOb  := AllTrim(If(!Empty(aObra[03]) .And. SC5->(FieldPos(aObra[03])) > 0 , &(aObra[03]),"")) // Numero para Obra
				cBairroOb  := AllTrim(If(!Empty(aObra[04]) .And. SC5->(FieldPos(aObra[04])) > 0 , &(aObra[04]),"")) // Bairro para Obra
				cCepOb     := AllTrim(If(!Empty(aObra[05]) .And. SC5->(FieldPos(aObra[05])) > 0 , &(aObra[05]),"")) // Cep para Obra
				cCodMunob  := AllTrim(If(!Empty(aObra[06]) .And. SC5->(FieldPos(aObra[06])) > 0 , &(aObra[06]),"")) // Cod do Municipio para Obra
				cNomMunOb  := AllTrim(If(!Empty(aObra[07]) .And. SC5->(FieldPos(aObra[07])) > 0 , &(aObra[07]),"")) // Nome do municipio para Obra
				cUfOb 	   := AllTrim(If(!Empty(aObra[08]) .And. SC5->(FieldPos(aObra[08])) > 0 , &(aObra[08]),"")) // UF para Obra
				cCodPaisOb := AllTrim(If(!Empty(aObra[09]) .And. SC5->(FieldPos(aObra[09])) > 0 , &(aObra[09]),"")) // Codigo do Pais para Obra
				cNomPaisOb := AllTrim(If(!Empty(aObra[10]) .And. SC5->(FieldPos(aObra[10])) > 0 , &(aObra[10]),"")) // Nome do Pais para Obra
				cNumArtOb  := AllTrim(If(!Empty(aObra[11]) .And. SC5->(FieldPos(aObra[11])) > 0 , &(aObra[11]),"")) // Numero Art para Obra
				cNumCeiOb  := AllTrim(If(!Empty(aObra[12]) .And. SC5->(FieldPos(aObra[12])) > 0 , &(aObra[12]),"")) // Numero CEI para Obra
				cNumProOb  := AllTrim(If(!Empty(aObra[13]) .And. SC5->(FieldPos(aObra[13])) > 0 , &(aObra[13]),"")) // Numero Projeto para Obra
				cNumMatOb  := AllTrim(If(!Empty(aObra[14]) .And. SC5->(FieldPos(aObra[14])) > 0 , &(aObra[14]),"")) // Numero de Mtricula para Obra
				cNumEncap  := AllTrim(If(!Empty(aObra[15]) .And. SC5->(FieldPos(aObra[15])) > 0 , &(aObra[15]),"")) // NumeroEncapsulamento
			EndIf
			
			If(!Empty(cLogradOb),aadd(aConstr,(cLogradOb)),aadd(aConstr,"") )	//Logradouro para Obra
			If(!Empty(cCompleOb),aadd(aConstr,(cCompleOb)),aadd(aConstr,"") )	//Complemento para obra
			If(!Empty(cNumeroOb),aadd(aConstr,(cNumeroOb)),aadd(aConstr,"") )	// Numero para Obra
			If(!Empty(cBairroOb),aadd(aConstr,(cBairroOb)),aadd(aConstr,"") )	// Bairro para Obra
			If(!Empty(cCepOb),aadd(aConstr,(cCepOb)),aadd(aConstr,"") )			// Cep para Obra
			If(!Empty(cCodMunob),aadd(aConstr,(cCodMunob)),aadd(aConstr,"") )	// Cod do Municipio para Obra
			If(!Empty(cNomMunOb),aadd(aConstr,(cNomMunOb)),aadd(aConstr,"") )	// Nome do municipio para Obra
			If(!Empty(cUfOb),aadd(aConstr,(cUfOb)),aadd(aConstr,"") )			// UF para Obra
			If(!Empty(cCodPaisOb),aadd(aConstr,(cCodPaisOb)),aadd(aConstr,"") ) // Codigo do Pais para Obra
			If(!Empty(cNomPaisOb),aadd(aConstr,(cNomPaisOb)),aadd(aConstr,"") ) // Nome do Pais para Obra
			If(!Empty(cNumArtOb),aadd(aConstr,(cNumArtOb)),aadd(aConstr,"") )	// Numero Art para Obra
			If(!Empty(cNumCeiOb),aadd(aConstr,(cNumCeiOb)),aadd(aConstr,"") )	// Numero CEI para Obra
			If(!Empty(cNumProOb),aadd(aConstr,(cNumProOb)),aadd(aConstr,"") )	// Numero Projeto para Obra
			If(!Empty(cNumMatOb),aadd(aConstr,(cNumMatOb)),aadd(aConstr,"") )	// Numero de Mtricula para Obra
			If(!Empty(cNumEncap),aadd(aConstr,(cNumEncap)),aadd(aConstr,"") )	// NumeroEncapsulamento
			
			SF4->(dbSetOrder(1))
			/*/ Configurador de Tributos
				Função TssTCInteg responsavel pela Integracao TSS com Configurador de Tributos, adequação para atender a
				Reforma Tributária. Classifica o tipo de tributacao do item da nota fiscal, de acordo com a configuracao da Classe TSSTCIIntegration
				@since 28/01/2025
				@version 12.1.2410
			/*///-----------------------------------------------------------------------
			TssTCInteg(cAliasSD2, lVldExc, @oNfTciIntg)
			
			While !(cAliasSD2)->(Eof()) .And. xFilial("SD2") == (cAliasSD2)->D2_FILIAL .And.;
				SF2->F2_SERIE == (cAliasSD2)->D2_SERIE .And.;
				SF2->F2_DOC == (cAliasSD2)->D2_DOC
				
				SF4->(dbSeek(xFilial('SF4')+(cAliasSD2)->D2_TES))
				
				nCont++
				lConfTrib := .F. 
				oISSCfg   := NIL

				If ( !Empty( (cAliasSD2)->D2_IDTRIB ) .And. !oNfTciIntg == Nil )
					lConfTrib := oNfTciIntg:GetNFConfigTributos((cAliasSD2)->D2_IDTRIB)
					oISSCfg   := oNfTciIntg:GetTax( (cAliasSD2)->D2_IDTRIB, "ISS")
				EndIf
				
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Verifica a natureza da operacao                                         ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				dbSelectArea("SC5")
				dbSetOrder(1) //C5_FILIAL+C5_NUM
				If DbSeek(xFilial("SC5")+(cAliasSD2)->D2_PEDIDO)
					lSC5 := .T.
				Else
					lSC5 := .F.
				EndIf

				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Pega retencoes por item ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				aAdd(aRetPIS,Iif(nRetPis > 0, (cAliasSD2)->D2_VALPIS, 0))
				nScan := aScan(aRetido,{|x| x[1] == "PIS"})
				If nScan > 0
					aRetido[nScan][5] := aRetPIS
				EndIf

				aAdd(aRetCOF,Iif(nRetCof > 0, (cAliasSD2)->D2_VALCOF, 0))
				nScan := aScan(aRetido,{|x| x[1] == "COFINS"})
				If nScan > 0
					aRetido[nScan][5] := aRetCOF
				EndIf

				aAdd(aRetCSL,Iif(nRetCsl > 0, (cAliasSD2)->D2_VALCSL, 0))
				nScan := aScan(aRetido,{|x| x[1] == "CSLL"})
				If nScan > 0
					aRetido[nScan][5] := aRetCSL
				EndIf

				aAdd(aRetIRR,Iif(SF2->(FieldPos("F2_VALIRRF")) <> 0 .and. SF2->F2_VALIRRF > 0, (cAliasSD2)->D2_VALIRRF, 0))
				nScan := aScan(aRetido,{|x| x[1] == "IRRF"})
				If nScan > 0
					aRetido[nScan][5] := aRetIRR
				EndIf

				aAdd(aRetINS,Iif(SF2->(FieldPos("F2_BASEINS")) <> 0 .and. SF2->F2_BASEINS > 0, (cAliasSD2)->D2_VALINS, 0))
				nScan := aScan(aRetido,{|x| x[1] == "INSS"})
				If nScan > 0
					aRetido[nScan][5] := aRetINS
				EndIf

				//TRATAMENTO - INTEGRACAO COM TMS-GESTAO DE TRANSPORTES
				If IntTms()
					DT6->(DbSetOrder(1)) //DT6_FILIAL+DT6_FILDOC+DT6_DOC+DT6_SERIE
					If DT6->(DbSeek(xFilial("DT6")+SF2->(F2_FILIAL+F2_DOC+F2_SERIE)))
						cModFrete := DT6->DT6_TIPFRE
						
						SA1->(DbSetOrder(1)) //A1_FILIAL+A1_COD+A1_LOJA
						If SA1->(DbSeek(xFilial("SA1")+DT6->(DT6_CLIDES+DT6_LOJDES)))
							cMunPSIAFI := SA1->A1_CODSIAFI
						EndIf
						
						If DUY->(FieldPos("DUY_CODMUN")) > 0
							DUY->(DbSetOrder(1))
							If DUY->(DbSeek(xFilial("DUY")+DT6->DT6_CDRDES))
								nPosUF:=aScan(aUF,{|X| X[1] == DUY->DUY_EST})
								If nPosUF > 0 
									cMunPrest:=aUF[nPosUF][2]+AllTrim(DUY->DUY_CODMUN)
								Else
									cMunPrest:=DUY->DUY_CODMUN
								EndIf
							EndIf
						Else
							SA1->(DbSetOrder(1))
							If SA1->(DbSeek(xFilial("SA1")+DT6->(DT6_CLIDES+DT6_LOJDES)))
								cMunPrest := SA1->A1_COD_MUN
							EndIf
						EndIf
					Else
						If lSC5 .And. SC5->(FieldPos("C5_MUNPRES")) > 0 .And. !Empty(SC5->C5_MUNPRES)
							//Quando for preenchido os campos C5_ESTPRES e C5_MUNPRES concatena as informacoes
							If ( len(Alltrim(SC5->C5_MUNPRES)) == 5 .AND. !empty(SC5->C5_ESTPRES) )
								
								For nZ := 1 to len(aUf)
									If Alltrim(SC5->C5_ESTPRES) == aUf[nZ][1]
										cMunPrest := Alltrim(aUf[nZ][2] + Alltrim(SC5->C5_MUNPRES))
										exit
									EndIf
								Next
							Else
								cMunPrest := SC5->C5_MUNPRES
							EndIf
							
							cDescMunP := SC5->C5_DESCMUN
							
						Else
							cMunPrest := aDest[07]
							cDescMunP := aDest[08]
						EndIf
					EndIf
				Else
					If lSC5 .And. SC5->(FieldPos("C5_MUNPRES")) > 0 .And. !Empty(SC5->C5_MUNPRES)
						//Quando for preenchido os campos C5_ESTPRES e C5_MUNPRES concatena as informacoes
						If ( len(Alltrim(SC5->C5_MUNPRES)) == 5 .AND. !empty(SC5->C5_ESTPRES) )
							
							For nZ := 1 to len(aUf)
								If Alltrim(SC5->C5_ESTPRES) == aUf[nZ][1]
									cMunPrest := Alltrim(aUf[nZ][2] + Alltrim(SC5->C5_MUNPRES))
									exit
								EndIf
							Next
						Else
							cMunPrest := SC5->C5_MUNPRES
						EndIf
						
						cDescMunP := SC5->C5_DESCMUN
						
					Else
						cMunPrest := aDest[07]
						cDescMunP := aDest[08]
					EndIf
					// Tratamento para notas com data de Competencia
					If ! Empty(cCamSC5)
						If Fieldpos(cCamSC5)>0
							dDateCom := SC5->&(cCamSC5)
						Else
							dDateCom := CToD("")
						Endif
					Endif
				EndIf

				dbSelectArea("SF4")
				dbSetOrder(1) //F4_FILIAL+F4_CODIGO
				DbSeek(xFilial("SF4")+(cAliasSD2)->D2_TES)
				
				cF4Agreg := SF4->F4_AGREG

				If SF4->(FieldPos("F4_NATOPNF")) > 0
					cNatOP := AllTrim(SF4->F4_NATOPNF)
				EndIf

				//Pega descricao do pedido de venda-Parametro MV_NFESERV
				cFieldMsg := GetNewPar("MV_CMPUSR","")
				If !lNFeDesc
					If lNatOper .And. lSC5 .And. nCont == 1 .and. !Empty(cFieldMsg) .and. SC5->(FieldPos(cFieldMsg)) > 0 .and. !Empty(&("SC5->"+cFieldMsg))
						cNatOper := If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(&("SC5->"+cFieldMsg))),&("SC5->"+cFieldMsg))+" "
					ElseIf lNatOper .And. lSC5 .And. !Empty(SC5->C5_MENNOTA).And. nCont == 1
						cNatOper += If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(SC5->C5_MENNOTA)),SC5->C5_MENNOTA)
						// cNatOper += "$$$"
					ElseIf SF2->(FieldPos("F2_MENNOTA")) <> 0 .and. !AllTrim(SF2->F2_MENNOTA) $ cMensCli .and. !Empty(AllTrim(SF2->F2_MENNOTA))
             			cDiscrNFSe +=If(FindFunction('CleanSpecChar'),CleanSpecChar(AllTrim(SF2->F2_MENNOTA)),AllTrim(SF2->F2_MENNOTA))
					EndIf
				Else
					If lSC5 .And. nCont == 1 .and. !Empty(cFieldMsg) .and. SC5->(FieldPos(cFieldMsg)) > 0 .and. !Empty(&("SC5->"+cFieldMsg))
						cDiscrNFSe := If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(&("SC5->"+cFieldMsg))),&("SC5->"+cFieldMsg))+" "
					ElseIf lSC5 .And. !Empty(SC5->C5_MENNOTA).And. nCont == 1
						cDiscrNFSe := If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(SC5->C5_MENNOTA)),SC5->C5_MENNOTA)
						// cDiscrNFSe += "$$$"
					ElseIf !Empty(AllTrim(SF2->F2_MENNOTA)) .And. nCont == 1
             			cDiscrNFSe +=If(FindFunction('CleanSpecChar'),CleanSpecChar(AllTrim(SF2->F2_MENNOTA)),AllTrim(SF2->F2_MENNOTA))
					EndIf
				EndIf

				//---------------------------------------
				// - Posiciona no Cadastro de Produtos
				//---------------------------------------
				dbSelectArea( "SB1" )
				dbSetOrder( 1 )	//B1_FILIAL + B1_COD
				DbSeek( xFilial( "SB1" ) + ( cAliasSD2 )->D2_COD )

				//---------------------------------------------------------------------------------
				// - Obtem a descricao da tabela SX5
				// - Tabela 60 - Conforme Item da Lista de Servico informado no Cad. de Produtos
				//---------------------------------------------------------------------------------
				dbSelectArea( "SX5" )
				dbSetOrder( 1 )
				aRetSX5 := FWGetSX5( '60',RetFldProd( SB1->B1_COD,"B1_CODISS" ) )

				if( !empty( aRetSX5 ) )
					cMsgSX5 := iif( FindFunction( 'CleanSpecChar' ),CleanSpecChar( aRetSX5[ 1 ][ 4 ] ),aRetSX5[ 1 ][ 4 ] )
					cMsgSX5 := allTrim( subStr( cMsgSX5,1,55 ) )
				endIf

				if( nCont == 1 )
					if( !lNFeDesc )
						cNatOper	+= cMsgSX5
					else
						cDescrNFSe	:= cMsgSX5
					endIf
				endIf
    		
				If SF4->(FieldPos("F4_CFPS")) > 0
					cCFPS:=SF4->F4_CFPS
				EndIf
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Verifica as notas vinculadas                                            ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If !Empty((cAliasSD2)->D2_NFORI) 
					If (cAliasSD2)->D2_TIPO $ "DBN"
						dbSelectArea("SD1")
						dbSetOrder(1)
						If DbSeek(xFilial("SD1")+(cAliasSD2)->D2_NFORI+(cAliasSD2)->D2_SERIORI+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_COD+(cAliasSD2)->D2_ITEMORI)
							dbSelectArea("SF1")
							dbSetOrder(1)
							DbSeek(xFilial("SF1")+SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_TIPO)
							If SD1->D1_TIPO $ "DB"
								dbSelectArea("SA1")
								dbSetOrder(1)
								DbSeek(xFilial("SA1")+SD1->D1_FORNECE+SD1->D1_LOJA)
							Else
								dbSelectArea("SA2")
								dbSetOrder(1)
								DbSeek(xFilial("SA2")+SD1->D1_FORNECE+SD1->D1_LOJA)
							EndIf

							aadd(aNfVinc,{SD1->D1_EMISSAO,SD1->D1_SERIE,SD1->D1_DOC,IIF(SD1->D1_TIPO $ "DB",IIF(SD1->D1_FORMUL=="S",SM0->M0_CGC,SA1->A1_CGC),IIF(SD1->D1_FORMUL=="S",SM0->M0_CGC,SA2->A2_CGC)),SM0->M0_ESTCOB,SF1->F1_ESPECIE})
						EndIf
					Else
						aOldReg  := SD2->(GetArea())
						aOldReg2 := SF2->(GetArea())
						dbSelectArea("SD2")
						dbSetOrder(3)
						If DbSeek(xFilial("SD2")+(cAliasSD2)->D2_NFORI+(cAliasSD2)->D2_SERIORI+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_COD+(cAliasSD2)->D2_ITEMORI)
							dbSelectArea("SF2")
							dbSetOrder(1)
							DbSeek(xFilial("SF2")+SD2->D2_DOC+SD2->D2_SERIE+SD2->D2_CLIENTE+SD2->D2_LOJA)
							If !SD2->D2_TIPO $ "DB"
								dbSelectArea("SA1")
								dbSetOrder(1)
								DbSeek(xFilial("SA1")+SD2->D2_CLIENTE+SD2->D2_LOJA)
							Else
								dbSelectArea("SA2")
								dbSetOrder(1)
								DbSeek(xFilial("SA2")+SD2->D2_CLIENTE+SD2->D2_LOJA)
							EndIf

							aadd(aNfVinc,{SF2->F2_EMISSAO,SD2->D2_SERIE,SD2->D2_DOC,SM0->M0_CGC,SM0->M0_ESTCOB,SF2->F2_ESPECIE})
						EndIf
						RestArea(aOldReg)
						RestArea(aOldReg2)
					EndIf
				EndIf
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Obtem os dados do produto                                               ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				dbSelectArea("SB1")
				dbSetOrder(1) //B1_FILIAL+B1_COD
				DbSeek(xFilial("SB1")+(cAliasSD2)->D2_COD)

				dbSelectArea("SB5")
				dbSetOrder(1) //B5_FILIAL+B5_COD
				DbSeek(xFilial("SB5")+(cAliasSD2)->D2_COD)
				//-- Veiculos Novos
				If AliasIndic("CD9")
					dbSelectArea("CD9")
					dbSetOrder(1) //CD9_FILIAL+CD9_TPMOV+CD9_SERIE+CD9_DOC+CD9_CLIFOR+CD9_LOJA+CD9_ITEM+CD9_COD
					DbSeek(xFilial("CD9")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
				EndIf
				//-- Medicamentos
				If AliasIndic("CD7")
					dbSelectArea("CD7")
					dbSetOrder(1) //CD7_FILIAL+CD7_TPMOV+CD7_SERIE+CD7_DOC+CD7_CLIFOR+CD7_LOJA+CD7_ITEM+CD7_COD
					DbSeek(xFilial("CD7")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
				EndIf
				//-- Armas de Fogo
				If AliasIndic("CD8")
					dbSelectArea("CD8")
					dbSetOrder(1) //CD8_FILIAL+CD8_TPMOV+CD8_SERIE+CD8_DOC+CD8_CLIFOR+CD8_LOJA+CD8_ITEM+CD8_COD
					DbSeek(xFilial("CD8")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
				EndIf
				//-- Msg Zona Franca de Manaus / ALC
				dbSelectArea("SF3")
				dbSetOrder(4) //F3_FILIAL+F3_CLIEFOR+F3_LOJA+F3_NFISCAL+F3_SERIE
				If DbSeek(xFilial("SF3")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_DOC+SF2->F2_SERIE)
					If !SF3->F3_DESCZFR == 0
						cMensFis := "Total do desconto Ref. a Zona Franca de Manaus / ALC. R$ "+str(SF3->F3_VALOBSE-SF2->F2_DESCONT,13,2)
					EndIf
				EndIf

				dbSelectArea("SC6")
				dbSetOrder(1) //C6_FILIAL+C6_NUM+C6_ITEM+C6_PRODUTO
				DbSeek(xFilial("SC6")+(cAliasSD2)->D2_PEDIDO+(cAliasSD2)->D2_ITEMPV+(cAliasSD2)->D2_COD)

				cFieldMsg := GetNewPar("MV_CMPUSR","")
				If !Empty(cFieldMsg) .and. SC5->(FieldPos(cFieldMsg)) > 0 .and. !Empty(&("SC5->"+cFieldMsg))
					//Permite ao cliente customizar o conteudo do campo dados adicionais por meio de um campo MEMO proprio.
					cMensCli := If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(&("SC5->"+cFieldMsg))),&("SC5->"+cFieldMsg))+" "
				ElseIf !AllTrim(SC5->C5_MENNOTA) $ cMensCli
					cMensCli +=If(FindFunction('CleanSpecChar'),CleanSpecChar(AllTrim(SC5->C5_MENNOTA)),AllTrim(SC5->C5_MENNOTA))
				EndIf
				If !Empty(SC5->C5_MENPAD) .And. !AllTrim(FORMULA(SC5->C5_MENPAD)) $ cMensFis
					cMensFis += If(FindFunction('CleanSpecChar'),CleanSpecChar(AllTrim(FORMULA(SC5->C5_MENPAD))),AllTrim(FORMULA(SC5->C5_MENPAD)))
				EndIf

				cModFrete := IIF(SC5->C5_TPFRETE=="C","0","1")

				If Empty(aPedido)
					aPedido := {"",AllTrim(SC6->C6_PEDCLI),""}
				EndIf
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Verifica se recolhe ISS Retido ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If SF3->(FieldPos("F3_RECISS"))>0
					If SF3->F3_RECISS $"1S"
						//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
						//³Pega retencao de ISS por item ³
						//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
						SFT->(dbSetOrder(1))
						If SFT->(dbSeek(xFilial("SFT")+"S"+SF2->F2_SERIE+SF2->F2_DOC+SF2->F2_CLIENTE+SF2->F2_LOJA+PadR((cAliasSD2)->D2_ITEM,4)+(cAliasSD2)->D2_COD))
							aAdd(aRetISS,SFT->FT_VALICM)
						EndIf

						dbSelectArea("SD2")
						dbSetOrder(3)
						dbSeek(xFilial("SD2")+SF3->F3_NFISCAL+SF3->F3_SERIE+SF3->F3_CLIEFOR+SF3->F3_LOJA)

						aadd(aRetido,{"ISS",0,SF3->F3_VALICM,SD2->D2_ALIQISS,val(SF3->F3_RECISS),aRetISS})
					Endif
				EndIf
				dbSelectArea("CD2")
				If !(cAliasSD2)->D2_TIPO $ "DB"
					dbSetOrder(1) //CD2_FILIAL+CD2_TPMOV+CD2_SERIE+CD2_DOC+CD2_CODCLI+CD2_LOJCLI+CD2_ITEM+CD2_CODPRO+CD2_IMP
				Else
					dbSetOrder(2)
				EndIf
				If !DbSeek(xFilial("CD2")+"S"+SF2->F2_SERIE+SF2->F2_DOC+SF2->F2_CLIENTE+SF2->F2_LOJA+PadR((cAliasSD2)->D2_ITEM,4)+(cAliasSD2)->D2_COD)

				EndIf
				aadd(aISSQN,{0,0,0,"","",0})
				While !Eof() .And. xFilial("CD2") == CD2->CD2_FILIAL .And.;
					"S" == CD2->CD2_TPMOV .And.;
					SF2->F2_SERIE == CD2->CD2_SERIE .And.;
					SF2->F2_DOC == CD2->CD2_DOC .And.;
					SF2->F2_CLIENTE == IIF(!(cAliasSD2)->D2_TIPO $ "DB",CD2->CD2_CODCLI,CD2->CD2_CODFOR) .And.;
					SF2->F2_LOJA == IIF(!(cAliasSD2)->D2_TIPO $ "DB",CD2->CD2_LOJCLI,CD2->CD2_LOJFOR) .And.;
					(cAliasSD2)->D2_ITEM == SubStr(CD2->CD2_ITEM,1,Len((cAliasSD2)->D2_ITEM)) .And.;
					(cAliasSD2)->D2_COD == CD2->CD2_CODPRO

					Do Case
						Case AllTrim(CD2->CD2_IMP) == "ICM"
							aTail(aICMS) := {CD2->CD2_ORIGEM,CD2->CD2_CST,CD2->CD2_MODBC,CD2->CD2_PREDBC,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,0,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
						Case AllTrim(CD2->CD2_IMP) == "SOL"
							aTail(aICMSST) := {CD2->CD2_ORIGEM,CD2->CD2_CST,CD2->CD2_MODBC,CD2->CD2_PREDBC,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_MVA,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
							lCalSol := .T.
						Case AllTrim(CD2->CD2_IMP) == "IPI"
							aTail(aIPI) := {"","",0,"999",CD2->CD2_CST,CD2->CD2_BC,CD2->CD2_QTRIB,CD2->CD2_PAUTA,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_MODBC,CD2->CD2_PREDBC}
						Case AllTrim(CD2->CD2_IMP) == "PS2"
							If (cAliasSD2)->D2_VALISS==0
								aTail(aPIS) := {CD2->CD2_CST,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
							Else
								If Empty(aISS)
									aISS := {0,0,0,0,0}
								EndIf
								aISS[04]+= CD2->CD2_VLTRIB	
							EndIf
						Case AllTrim(CD2->CD2_IMP) == "CF2"
							If (cAliasSD2)->D2_VALISS==0
								aTail(aCOFINS) := {CD2->CD2_CST,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
							Else
								If Empty(aISS)
									aISS := {0,0,0,0,0}
								EndIf
								aISS[05] += CD2->CD2_VLTRIB	
							EndIf
						Case AllTrim(CD2->CD2_IMP) == "PS3" .And. (cAliasSD2)->D2_VALISS==0
							aTail(aPISST) := {CD2->CD2_CST,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
						Case AllTrim(CD2->CD2_IMP) == "CF3" .And. (cAliasSD2)->D2_VALISS==0
							aTail(aCOFINSST) := {CD2->CD2_CST,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
						Case AllTrim(CD2->CD2_IMP) == "ISS"
							If Empty(aISS)
								aISS := {0,0,0,0,0}
							EndIf
							aISS[01] += (cAliasSD2)->D2_TOTAL+(cAliasSD2)->D2_DESCON
							aISS[02] += CD2->CD2_BC
							aISS[03] += CD2->CD2_VLTRIB
							If !Empty(cMunPrest) .and. (Empty(aDest[01]) .and. Empty(aDest[02]) .and. Empty(aDest[07]) .and. Empty(aDest[09]))
								cMunISS := cMunPrest
							Else
								cMunISS := convType(aUF[aScan(aUF,{|x| x[1] == aDest[09]})][02]+aDest[07])
							EndIf
							If CD2->CD2_ALIQ > 0
								If lAglutina
									aISSQN[1][2] := CD2->CD2_ALIQ
									aISSQN[1][1] += CD2->CD2_BC
									aISSQN[1][3] += CD2->CD2_VLTRIB
									aISSQN[1][6] += iif( lMvDescInc,( cAliasSD2 )->D2_DESCON,0 ) // NFSE - Desconto Incondicionado
								Else
									lAglutina := .F.
									aTail(aISSQN) := {CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,cMunISS,AllTrim((cAliasSD2)->D2_CODISS),iif( lMvDescInc,(cAliasSD2)->D2_DESCON,0 )}
								EndIf
							Else
								aTail(aISSQN) := {CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,cMunISS,AllTrim((cAliasSD2)->D2_CODISS),iif( lMvDescInc,(cAliasSD2)->D2_DESCON,0 )}
								nAliq := CD2->CD2_ALIQ
							EndIf
					EndCase
					dbSelectArea("CD2")
					dbSkip()
				EndDo
				If lAglutina
					If Len(aProd) > 0
						If lUsaSF3	
							If Empty(Alltrim(SFT->FT_TRIBMUN))
								dbselectArea("SFT")
								dbsetOrder(1)//FT_FILIAL+FT_TIPOMOV+FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_ITEM+FT_PRODUTO
								DbSeek(xFilial("SFT")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA)
							EndIf	
							nX := aScan(aRetSF3,{|x| x[5] == alltrim( (cAliasSD2)->D2_CODISS ) .And. x[3] == IIF(SFT->(FieldPos("FT_TRIBMUN"))<>0,SFT->FT_TRIBMUN,"")})
						Else
							nX := aScan(aProd,{|x| x[24] == allTrim( ( cAliasSD2 )->D2_CODISS ) .And. x[23] == IIF(SB1->(FieldPos("B1_TRIBMUN"))<>0,RetFldProd(SB1->B1_COD,"B1_TRIBMUN"),"")})
						EndIf	
						
						If nX > 0
							aProd[nx][13]+= (cAliasSD2)->D2_VALFRE // Valor Frete
							aProd[nx][14]+= (cAliasSD2)->D2_SEGURO // Valor Seguro
							aProd[nx][15]+= ((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR) // Valor Desconto
							aProd[nx][21]+= SF3->F3_ISSSUB
							aProd[nx][22]+= SF3->F3_ISSMAT
							aProd[nx][25]+= (cAliasSD2)->D2_BASEISS
							aProd[nx][26]+= (cAliasSD2)->D2_VALFRE
							aProd[nx][27]+=	IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN,0) * (cAliasSD2)->D2_QUANT // Valor Liquido = I-Compl.ICMS;P-Compl.IPI
							aProd[nx][28]+= IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN,0) * (cAliasSD2)->D2_QUANT+((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR) //Valor Total
							aProd[nx][35]+= IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTIMP"))<>0,(cAliasSD2)->D2_TOTIMP,0),0)
							aProd[nx][10]+= IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN,0)
							//aProd[nx][29]+=	SF3->F3_ISSSUB + SF3->F3_ISSMAT	//Valor Total de deducoes       Comentado para não duplicar o valor na tag ValorDeducoes
						Else
							lAglutina := .F.
						EndIf
					EndIf
				EndIf

				If !lAglutina .Or. lUsaSF3 
					dbselectArea("SFT")
					SFT->(dbSetOrder(1))//FT_FILIAL+FT_TIPOMOV+FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_ITEM+FT_PRODUTO
					If DbSeek(xFilial("SFT")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
					
						aadd(aRetSF3,{Len(aRetSF3)+1,;
									SFT->FT_CNAE,;
									SFT->FT_TRIBMUN,;
									"",; // 4 - Código Beneficio Fiscal - NFS-e RJ IIF(SF4->(FieldPos(cMVBENEFRJ))> 0,SF4->(&(cMVBENEFRJ)),"" ) Manutenção preventiva, tirando o campo de Macro-execução da TES via SX6(Parâmetro).
									Alltrim(SFT->FT_CODISS); // Código de Serviço.
							})
					EndIf		
						   
				EndIf	

				If !lAglutina .Or. Len(aProd) == 0
					If SM0->M0_CODMUN == "4205407" //florianopolis
						nValTotPrd := IIF(!(cAliasSD2)->D2_TIPO$"IP",IIF(SM0->M0_CODMUN == "3550308",(cAliasSD2)->D2_PRCVEN * (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_TOTAL),0)
					Else
						nValTotPrd := IIF(!(cAliasSD2)->D2_TIPO$"IP",IIF(SM0->M0_CODMUN == "3550308",(cAliasSD2)->D2_PRCVEN * (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_TOTAL),0)+((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR)
					EndIf
					aadd(aProd,	{Len(aProd)+1,;
								(cAliasSD2)->D2_COD,;
								IIf(Val(SB1->B1_CODBAR)==0,"",Str(Val(SB1->B1_CODBAR),Len(SB1->B1_CODBAR),0)),;
								IIF(Empty(SC6->C6_DESCRI),SB1->B1_DESC,SC6->C6_DESCRI),;
								SB1->B1_POSIPI,;
								SB1->B1_EX_NCM,;
								(cAliasSD2)->D2_CF,;
								SB1->B1_UM,;
								(cAliasSD2)->D2_QUANT,;
								IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN,0),;
								IIF(Empty(SB5->B5_UMDIPI),SB1->B1_UM,SB5->B5_UMDIPI),;
								IIF(Empty(SB5->B5_CONVDIPI),(cAliasSD2)->D2_QUANT,SB5->B5_CONVDIPI*(cAliasSD2)->D2_QUANT),;
								(cAliasSD2)->D2_VALFRE,;
								(cAliasSD2)->D2_SEGURO,;
								((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR),;
								IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN+(((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR)/(cAliasSD2)->D2_QUANT),0),;
								IIF(SB1->(FieldPos("B1_CODSIMP"))<>0,SB1->B1_CODSIMP,""),; // 17 - codigo ANP do combustivel
								IIF(SB1->(FieldPos("B1_CODIF"))<>0,SB1->B1_CODIF,""),; // 18 - CODIF
								RetFldProd(SB1->B1_COD,"B1_CNAE"),; //19 - Codigo da Atividade CNAE
								SF3->F3_RECISS,;
								SF3->F3_ISSSUB,;
								SF3->F3_ISSMAT,;
								IIF(SB1->(FieldPos("B1_TRIBMUN"))<>0,RetFldProd(SB1->B1_COD,"B1_TRIBMUN"),""),;
								IIF( SC6->(FieldPos("C6_CODISS"))>0,AllTrim(SC6->C6_CODISS),AllTrim(SF3->F3_CODISS)),; //24 - Codigo Servico ISS
								(cAliasSD2)->D2_BASEISS,;
								(cAliasSD2)->D2_VALFRE,;
								IIF(!(cAliasSD2)->D2_TIPO$"IP",IIF(SM0->M0_CODMUN == "3550308",(cAliasSD2)->D2_PRCVEN * (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_TOTAL),0),; // 27 - Valor Liquido
								IIF(!(cAliasSD2)->D2_TIPO$"IP",IIF(SM0->M0_CODMUN == "3550308",(cAliasSD2)->D2_PRCVEN * (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_TOTAL),0)+((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR),; //28 - Valor Total
								SF3->F3_ISSSUB + SF3->F3_ISSMAT,; // 29 - Valor Total de deducoes.
								(cAliasSD2)->D2_VALIMP4,; // 30
								(cAliasSD2)->D2_VALIMP5,; // 31
								RetFldProd(SB1->B1_COD,"B1_TRIBMUN"),; // 32
								IIF(SF4->(FieldPos("F4_CFPS")) > 0,SF4->F4_CFPS,""),;// 33 - Codigo Fiscal de Prestacao de Servico (CFPS)
								"",; // 34 - Código Beneficio Fiscal - NFS-e RJ IIF(SF4->(FieldPos(cMVBENEFRJ))> 0,SF4->(&(cMVBENEFRJ)),"" )
								IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTIMP"))<>0,(cAliasSD2)->D2_TOTIMP,0),0),; // 35 - Lei transparência
								IIF((cAliasSD2)->D2_BASEISS <> nValTotPrd, nValTotPrd - (cAliasSD2)->D2_BASEISS, (cAliasSD2)->D2_BASEISS),;	// 36 - Posicao para verifcar se existe reducao de ISS, será criado um campo na SFT para substituir esse calculo
								IIF( SB1->(FieldPos("B1_MEPLES"))<>0, SB1->B1_MEPLES, "" ),; //37 - campo para NFSe Sao Paulo, identifica se eh Dentro do municipio ou fora.
								IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTFED"))<>0,(cAliasSD2)->D2_TOTFED,0),0),; //38 - Lei transparência
								IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTEST"))<>0,(cAliasSD2)->D2_TOTEST,0),0),; //39 - Lei transparência
								IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTMUN"))<>0,(cAliasSD2)->D2_TOTMUN,0),0),;  //40 - Lei transparência
								IIF(SC6->(FieldPos("C6_DESCRI")) > 0,AllTrim(SC6->C6_DESCRI),"")	;	//41 - Descricao RPS SC6
					})
				EndIf

				If SC6->(FieldPos("C6_TPDEDUZ")) > 0 .And. !Empty(SC6->C6_TPDEDUZ)
					aadd(aDeduz,{	SC6->C6_TPDEDUZ,; //-- Tipo de Deducao = 1-Percentual;2-Valor
									SC6->C6_MOTDED ,;
									SC6->C6_FORDED ,;
									SC6->C6_LOJDED ,;
									SC6->C6_SERDED ,;
									SC6->C6_NFDED  ,;
									SC6->C6_VLNFD  ,;
									SC6->C6_PCDED  ,;
									if (SC6->C6_VLDED > 0, SC6->C6_VLDED, (SC6->C6_ABATISS + SC6->C6_ABATMAT)),;
					})
				EndIf

				aadd(aCST,{IIF(!Empty((cAliasSD2)->D2_CLASFIS),SubStr((cAliasSD2)->D2_CLASFIS,2,2),'50'),;
				           IIF(!Empty((cAliasSD2)->D2_CLASFIS),SubStr((cAliasSD2)->D2_CLASFIS,1,1),'0')})
				aadd(aICMS,{})
				aadd(aIPI,{})
				aadd(aICMSST,{})
				aadd(aPIS,{})
				aadd(aPISST,{})
				aadd(aCOFINS,{})
				aadd(aCOFINSST,{})
				//aadd(aISSQN,{0,0,0,"","",0})
				aadd(aAdi,{})
				aadd(aDi,{})
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Tratamento para TAG Exportação quando existe a integração com a EEC     ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If lEECFAT .And. !Empty((cAliasSD2)->D2_PREEMB)
					aadd(aExp,(GETNFEEXP((cAliasSD2)->D2_PREEMB)))
				Else
					aadd(aExp,{})
				EndIf
				If AliasIndic("CD7")
					aadd(aMed,{CD7->CD7_LOTE,CD7->CD7_QTDLOT,CD7->CD7_FABRIC,CD7->CD7_VALID,CD7->CD7_PRECO})
				Else
					aadd(aMed,{})
				EndIf
				If AliasIndic("CD8")
					aadd(aArma,{CD8->CD8_TPARMA,CD8->CD8_NUMARMA,CD8->CD8_DESCR})
				Else
					aadd(aArma,{})
				EndIf
				If AliasIndic("CD9")
					aadd(aveicProd,{IIF(CD9->CD9_TPOPER$"03",1,IIF(CD9->CD9_TPOPER$"1",2,IIF(CD9->CD9_TPOPER$"2",3,IIF(CD9->CD9_TPOPER$"9",0,"")))),;
									CD9->CD9_CHASSI,CD9->CD9_CODCOR,CD9->CD9_DSCCOR,CD9->CD9_POTENC,CD9->CD9_CM3POT,CD9->CD9_PESOLI,;
					                CD9->CD9_PESOBR,CD9->CD9_SERIAL,CD9->CD9_TPCOMB,CD9->CD9_NMOTOR,CD9->CD9_CMKG,CD9->CD9_DISTEI,CD9->CD9_RENAVA,;
					                CD9->CD9_ANOMOD,CD9->CD9_ANOFAB,CD9->CD9_TPPINT,CD9->CD9_TPVEIC,CD9->CD9_ESPVEI,CD9->CD9_CONVIN,CD9->CD9_CONVEI,;
					                CD9->CD9_CODMOD})
				Else
					aadd(aveicProd,{})
				EndIf

				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Totaliza todas retencoes por item³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				nRetDesc :=	Iif(nRetPis > 0, (cAliasSD2)->D2_VALPIS, 0) + Iif(nRetCof > 0, (cAliasSD2)->D2_VALCOF, 0) + ;
							Iif(nRetCsl > 0, (cAliasSD2)->D2_VALCSL, 0) + Iif(SF2->(FieldPos("F2_VALIRRF")) <> 0 .and. SF2->F2_VALIRRF > 0, (cAliasSD2)->D2_VALIRRF, 0) + ;
							Iif(SF2->(FieldPos("F2_BASEINS")) <> 0 .and. SF2->F2_BASEINS > 0, (cAliasSD2)->D2_VALINS, 0) + Iif(Len(aRetISS) >= nCont, aRetISS[nCont], 0)

				aTotal[01] += (cAliasSD2)->D2_DESPESA
				aTotal[02] += ((cAliasSD2)->D2_TOTAL - nRetDesc)
				If ( lConfTrib .And. oISSCfg <> NIL  .Or. SF4->( FieldPos("F4_ISSST") == 0 ))
					aTotal[03] :=  Alltrim(SF4->F4_NATOPNF)
				Else
					aTotal[03] := SF4->F4_ISSST	
				EndIf
				aTotal[04] += (cAliasSD2)->D2_TOTAL
				/*Adequação: Reforma Tributária, Configurador de Tributos e descontinuação da TES (SF4). Campo F4_TRIBPRD será descontinuado na release 12.1.2510.
					Objetivo: Utilizar o campo F4_NATOPNF para identificar o tipo de tributação da NFSe (tag <tipotrib>). Integração: TOTVS Colaboração x NeoGrid.
					@since 22/07/2025
					@version 12.1.2410*/
				aTotal[05] := IIF(SF4->(ColumnPos('F4_TRIBPRD')),Alltrim(SF4->F4_TRIBPRD),'')
				
				If lCalSol
					dbSelectArea("SF3")
					dbSetOrder(4)
					If DbSeek(xFilial("SF3")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_DOC+SF2->F2_SERIE)
						nPosI	:=	At (SF3->F3_ESTADO, cMVSUBTRIB)+2
						nPosF	:=	At ("/", SubStr (cMVSUBTRIB, nPosI))-1
						nPosF	:=	IIf(nPosF<=0,len(cMVSUBTRIB),nPosF)
						aAdd (aIEST, SubStr (cMVSUBTRIB, nPosI, nPosF))	//01 - IE_ST
					EndIf
				EndIf

				//Tratamento para Calcular o Desconto para  Belo Horizonte
				nDescon += (cAliasSD2)->D2_DESCICM

				dbSelectArea(cAliasSD2)
				dbSkip()
			EndDo
			/*/-----------------------------------------------------------------------
				Destruir os objetos e arrays da classe TSSTCIntegration após o término do loop.
				@since 11/02/2025
				@version 12.1.2410
			/*///-----------------------------------------------------------------------

			If lQuery
				dbSelectArea(cAliasSD2)
				dbCloseArea()
				dbSelectArea("SD2")
			EndIf

		EndIf
		IF ExistBlock("PE02NFSEUNI")		
			aParam := {aProd,cMensCli,cMensFis,aDest,aNota,nil,aDupl,aTransp,aEntrega,nil,aVeiculo,aReboque,cDiscrNFSe,cNatOper}
			
			aParam := ExecBlock("PE02NFSEUNI",.F.,.F.,aParam)
			
			If ( Len(aParam) >= 5 )
				aProd		:= aParam[1]
				cMensCli	:= aParam[2]
				cMensFis	:= aParam[3]
				aDest 		:= aParam[4]
				aNota 		:= aParam[5]
				//aInfoItem	:= aParam[6]
				aDupl		:= aParam[7]
				aTransp		:= aParam[8]
				aEntrega	:= aParam[9]
				//aRetirada	:= aParam[10]
				aVeiculo	:= aParam[11]
				aReboque	:= aParam[12]
				cDiscrNFSe  := aParam[13]
				cNatOper    := aParam[14]
			EndIf
		Endif
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Geracao do arquivo XML                                                  ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If !Empty(aNota)
			cString := '<rps id="rps:' + allTrim( Str( Val( aNota[02] ) ) ) + '" tssversao="2.00">'
			cString += assina( aDeduz, aNota, aProd, aTotal, aDest, aRetSF3 )
			cString += ident( aNota, aProd, aTotal, aDest, aISSQN, aAIDF, dDateCom, cNatOp, cMunPrest, aRetSF3 )
			cString += substit( aNota )
			cString += ativ( aProd, aISSQN, aRetSF3 )
			cString += prest( cMunPSIAFI )
			cString += prestacao( cMunPrest, cDescMunP, aDest, cMunPSIAFI )
			cString += intermediario( aInterm )
			cString += tomador( aDest )
			cString += servicos( aProd, aISSQN, aRetido, cNatOper, lNFeDesc, cDiscrNFSe, aCST, aDest[22], SM0->M0_CODMUN, cF4Agreg ,nDescon, aRetSF3 )
			cString += valores( aISSQN, aRetido, aTotal, aDest, SM0->M0_CODMUN, aDeducao )
			cString += faturas( aDupl, cCondPag )
			cString += pagtos( aDupl )
			cString += deducoes( aISSQN, aDeduz, aDeducao, aConstr )
			cString += infCompl( cMensCli, cMensFis, lNFeDesc, cDescrNFSe, aConstr )
			cString += construcao(aConstr)
			If ( Date() >= dNfseIbs)
				cString	+= IbsCbs( aDest, cCodMun, aNota, cClieFor, cLoja, aEntrega )
			endif
			cString += '</rps>'
		EndIf

		DestroyTCI(@oNfTciIntg)

	ElseIf cTipo == "1" .And. !Empty(cMotCancela)
		cString := u_nfseXMLCan(cNota,cMotCancela, cCodCanc) 
	EndIf
return { cString, cNota }

//-----------------------------------------------------------------------
/*/{Protheus.doc} assina
Função para montar a tag de assinatura do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 07.02.2012

@param	aDeduz	Array contendo as informações de deduções.
@param	aNota	Array contendo as informações de identificação sobre a nota.
@param	aProd	Array contendo as informações dos produtos.
@param	aTotal	Array contendo os valores totais do documento.
@param	aDest	Array contendo as informações de destinatário.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function assina( aDeduz, aNota, aProd, aTotal, aDest, aRetSF3 )
	Local cAssinatura	:= ""
	Local cMVOPTSIMP	:= alltrim( GetMV( "MV_OPTSIMP" ,, "2" )) //-- Contribuinte optante do simples: 1=sim;2=nao
	Local nDeduz		:= 0
	Local nX			:= 0
	Local lUsaSF3  := GetNewPar("MV_ENVSF3",.F.)

	Default aRetSF3 := {}

	For nX := 1 To Len( aDeduz )
		nDeduz += iif( aDeduz[nX][1] == "2", aDeduz[nX][8], 0 )
	Next

	cAssinatura	+= strZero( val( SM0->M0_INSCM ), 11 )
	cAssinatura	+= "NF   "
	cAssinatura	+= strZero( val( aNota[02] ), 12 )
	cAssinatura	+= dToS( aNota[03] )
	do case
		case aTotal[3] $ "2"
			if cMVOPTSIMP == "1" 
				cAssinatura += "H "
			else
				cAssinatura += "E "
			endif
		case aTotal[3] $ "3"
			cAssinatura += "C "
		case aTotal[3] $ "4"
			cAssinatura += "F "
		case aTotal[3] $ "5"
			cAssinatura += "K "
		case aTotal[3] $ "6"
			cAssinatura += "K "
		case aTotal[3] $ "7" .Or. aTotal[3] == "58" .Or. aTotal[3] == "68" .Or. aTotal[3] == "78"
			cAssinatura += "N "
		case aTotal[3] $ "8" .Or. aTotal[3] == "13"
			cAssinatura += "M "
		otherwise
			if cMVOPTSIMP == "1"
				cAssinatura += "H "
			else
				cAssinatura += "T "
			endif
	endcase
	cAssinatura += "N"
	cAssinatura += iif( ( aProd[1][20] ) == '1', "S", "N" )
	cAssinatura += strZero( ( aTotal[2] - nDeduz ) * 100, 15 )
	cAssinatura += strZero( nDeduz * 100, 15 )
	If lUsaSF3  
		cAssinatura += allTrim( strZero( val( aRetSF3[1][2] ), 10 ) )
	Else
		cAssinatura += allTrim( strZero( val( aProd[1][19] ), 10 ) )
	EndIf
	cAssinatura += allTrim( strZero( val( aDest[1] ), 14 ) )
	cAssinatura := allTrim( Lower( sha1( allTrim( cAssinatura ), 2 ) ) )
	cAssinatura := '<assinatura>' + cAssinatura + '</assinatura>'

Return cAssinatura

//-----------------------------------------------------------------------
/*/{Protheus.doc} ident
Função para montar a tag de identificação do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 19.01.2012

@param	aNota	Array com informações sobre a nota.
@param	aProd	Array com informações sobre os serviços da nota.
@param	aTotal	Array com informações sobre os totais da nota.
@param	aDest	Array com informações sobre o tomador da nota.
@param	aAIDF	Array com informações sobre o AIDF.
@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function ident( aNota, aProd, aTotal, aDest, aISSQN, aAIDF, dDateCom, cNatOp, cMunPrest, aRetSF3 )
	Local cMVREGIESP	:= getMV( "MV_REGIESP",, "" )				//-- Informar o Regime especial de tributacao para que seja gerada a TAG <RegimeEspecialTributacao>
	Local cMVINCEFIS	:= AllTrim(GetNewPar("MV_INCEFIS","2"))
	Local cString		:= ""
	Local cMVOPTSIMP	:= allTrim( GetMV( "MV_OPTSIMP",, "2" ) )	//-- Contribuinte optante do simples: 1=sim;2=nao
	Local cMvNFSEINC	:= superGetMV( "MV_NFSEINC",.F.,"" ) 		//-- Parametro que aponta para o campo da SC5 com Código do município de Incidência 
	Local lUsaSF3  		:= GetNewPar("MV_ENVSF3",.F.)

	Default aRetSF3 := {}

	cString	:= "<identificacao>"
	//-- Data e hora de emissao do documento
	cString	+= "<dthremissao>" + subStr( dToS( aNota[3] ), 1, 4 ) + "-" + subStr( dToS( aNota[3] ), 5, 2 ) + "-" + subStr( Dtos( aNota[3] ), 7, 2 ) + 'T' + time() + "</dthremissao>"
	//-- Serie e numero RPS
	If UsaAidfRps(SM0->M0_CODMUN)
		cString += "<serierps>"  + allTrim( aAIDF[2] ) + "</serierps>"
		cString += "<numerorps>" + allTrim( aAIDF[3] ) + "</numerorps>"
	Else
		cString += "<serierps>"  + allTrim( aNota[1] ) + "</serierps>"
		cString += "<numerorps>" + allTrim( str( val( aNota[2] ) ) ) + "</numerorps>"
	EndIf
	//-- Tipo do documento
	cString += "<tipo>1</tipo>" //-- Fixo pois tanto ABRASF como DSFNET, utilizam esta tag como tipo RPS (1) - Obrigat.
	//-- Situacao do RPS
	cString += "<situacaorps>1</situacaorps>" //-- Fixo pois tanto ABRASF como DSFNET, utilizam esta tag como Normal (1) - Obrigat.
	//-- Tipo de recolhimento do documento
	cString += "<tiporecolhe>" + iif( allTrim( aProd[1][20] ) == "1", "2", "1" ) + "</tiporecolhe>" // 1-A receber; 2-Retido na fonte;
	//-- Tipo de operacao do documento - Nao Obrigat.
	do case
		case aNota[4] $ "DB"
			cString += "<tipooper>4</tipooper>"	// 4-Devolucao Simples Remessa;
		case (DivCem(aISSQN[1][2])) <= 0
			cString += "<tipooper>3</tipooper>" // 3-Imune/Isenta de ISSQN;
		otherWise
			cString += "<tipooper>1</tipooper>" // 1-Sem Deducao;
	endcase
	//-- Tipo de tributacao do documento - Natureza do Pagamento Imposto (F4_ISSST) - Obrigat
	//   1-Isenta de ISS
	//   2-Nao incidencia no municipio
	//   3-Imune
	//   4-Exigibilidade Susp. Dec. J.
	//   5-Nao tributavel
	//   6-Tributavel
	//   7-Tributavel fixo
	//   8-Tributavel S.N
	//   9-Cancelado
	//  10-Extraviado
	//  11-Micro Empreendendor Individual (MEI)
	//  12-Exigibilidade Susp. Proc. A.
	do case
		case !Empty(aTotal[05])
			 cString += "<tipotrib>"+aTotal[05]+"</tipotrib>"	//  Campo de usuário com o código da NeoGrid
		case aTotal[3] == "2"
			If  cMVOPTSIMP == "1" 
				cString += "<tipotrib>8</tipotrib>"	//  8- Tributavel S.N.; - Simples Nacional
			Else
				cString += "<tipotrib>2</tipotrib>"	//  2- Nao incidencia no municipio;
			EndIf
		case aTotal[3] == "3"
			cString += "<tipotrib>1</tipotrib>"		//  1- Isenta de ISS;
		case aTotal[3] == "4"
			cString += "<tipotrib>3</tipotrib>"		//  3- Imune;
		case aTotal[3] == "5"
			cString += "<tipotrib>4</tipotrib>"		//  4- Exigibilidade Susp. Dec. J.;
		case aTotal[3] == "6"
			cString += "<tipotrib>12</tipotrib>"		// 12- Exigibilidade Susp. Proc. A.;
		case aTotal[3] $ "7" .Or. aTotal[3] == "58" .Or. aTotal[3] == "68" .Or. aTotal[3] == "78"
			cString += "<tipotrib>5</tipotrib>"		//  5- Nao Tributavel;
		case aTotal[3] $ "8" .Or. aTotal[3] == "13"
			cString += "<tipotrib>11</tipotrib>"		// 11- Micro Empreendedor Individual (MEI);
		case aTotal[3] == "D"
			cString += "<tipotrib>13</tipotrib>"		// 13- Tributação no município PRODAM, SIL TECNOLOGIA, IPM, NOTA CONTROL, CONSIST, ARISS;
		case aTotal[3] == "E"
 			cString += "<tipotrib>14</tipotrib>"		// 14- Tributação fora do município PRODAM, GOVERNA, CONSIST, NOTA CONTROL, SIL TECNOLOGIA, IPM, ARISS, SigISS;
		otherWise
			if cMVOPTSIMP == "1"
				cString += "<tipotrib>8</tipotrib>"
			else
				cString += "<tipotrib>6</tipotrib>"
			EndIf
	endcase
	//-- Regime especial de tributacao do documento - Nao Obrigat.
	If !Empty(cMVREGIESP)
		cString += "<regimeesptrib>" + cMVREGIESP + "</regimeesptrib>"
	EndIf
	//-- Forma da pagamento do documento - Nao Obrigat.
	cString += "<formpagto>" + aNota[9] + "</formpagto>"
	//-- Codigo de Natureza da Operacao - Obrigat.
	//   1-Tributacao no Municipio
	//   2-Tributacao fora do Municipio
	//   3-Isento
	//   4-Imune
	//   5-Exigibilidade suspensa por Decisao Judicial
	//   6-Exigibilidade suspensa por Procedimento
	//   7-Exigivel
	//   8-Nao Incidencia
	//   9-Exportacao
	// 107-Sem deducao
	// 108-Com deducao materiais
	// 109-Devolucao/Simples Remessa
	// 110-Intermediacao
	// 121-ISS fixo (Soc. Profissionais)
	// 201-ISS retido pelo Tomador/Intermediario
	// 301-Operacao Imune,Isenta ou Nao Tributada
	// 541-MEI (Simples Nacional)
	// 551-Escritorio Contabil (Simples Nacional)
	// 601-ISS Retido pelo Tomador/Intermediario (Simples Nacional)
	// 701-Operacao Imune, Isenta ou Nao Tributada
	//  51-Imposto devido no Municipio, com obrigacao de retencao na fonte      (servico prestado no Municipio)
	//  52-Imposto devido no Municipio, sem obrigacao de retencao na fonte      (servico prestado no Municipio)
	//  58-Nao tributavel                                                       (servico prestado no Municipio)
	//  59-Imposto recolhido pelo regime unico de arrecadacao Simples Nacional  (servico prestado no Municipio)
	//  61-Imposto devido no Municipio, com obrigacao de retencao na fonte      (servico prestado fora do Municipio)
	//  62-Imposto devido no Municipio, sem obrigacao de retencao na fonte      (servico prestado fora do Municipio)
	//  63-Imposto devido fora do Municipio, com obrigacao de retencao na fonte (servico prestado fora do Municipio)
	//  64-Imposto devido fora do Municipio, sem obrigacao de retencao na fonte (servico prestado fora do Municipio)
	//  68-Nao tributavel                                                       (servico prestado fora do Municipio)
	//  69-Imposto recolhido pelo regime unico de arrecadacao Simples Nacional  (servico prestado fora do Municipio)
	//  78-Nao tributavel                                                       (servico prestado no exterior)
	//  79-Imposto recolhido pelo regime unico de arrecadacao Simples Nacional  (servico prestado no exterior)
	//  81-Imposto recolhido por guia sem escrituracao
	cString += "<natop>"+cNatOp+"</natop>"
	//-- Data competencia (emissao)
	cString += "<dtcompetencia>" + subStr(dToS(aNota[3]), 1, 4) + "-" + subStr(dToS(aNota[3]), 5, 2) + "-" + subStr(Dtos(aNota[3]), 7, 2) + 'T' + time() + "</dtcompetencia>"
	//-- Identificacao de Sim/Nao
	cString += "<incentfiscal>" + cMVINCEFIS + "</incentfiscal>"
	//-- Recolhimento. Identificacao de Sim/Nao
	cString += "<issret>"+ allTrim( aProd[1][20])+"</issret>"
	If lUsaSF3
		//-- Codigo do Item da Lista de Servico
		cString += "<itemlistaserv>"+ConvType(aRetSF3[1][5],5)+"</itemlistaserv>"
		//-- Codigo da Atividade CNAE
		cString += "<cnae>" + allTrim( aRetSF3[1][2] ) + "</cnae>"
		//-- Codigo de Tributacao do Municipio
		cString += "<ctributmun>" + ConvType(aRetSF3[1][3],20)+"</ctributmun>"
	Else
		//-- Codigo do Item da Lista de Servico
		cString += "<itemlistaserv>"+ConvType(aProd[1][24],5)+"</itemlistaserv>"
		//-- Codigo da Atividade CNAE
		cString += "<cnae>" + allTrim( aProd[1][19] ) + "</cnae>"
		//-- Codigo de Tributacao do Municipio
		cString += "<ctributmun>" + ConvType(aProd[1][23],20)+"</ctributmun>"
	EndIf	
	//-- Codigo Fiscal de Prestacao de Servico (CFPS)
	cString += "<codigocfps>" + allTrim( aProd[1][33] ) + "</codigocfps>"
	//-- Tipo de lancamento de acordo com o servico prestado: N-devido no munic.prestador;P-Prestadores Simples Nac.T-devido no munic.tomador;R-NF recebida dentro ou fora munic.
	cString += "<ctipolancamento>N</ctipolancamento>"
	//-- Exigibilidade de ISS - Mesmo conteudo do campo NatOp - Nao Obrigat.
	If Len(cNatOp) <= 2
		cString += "<cexiss>"+cNatOp+"</cexiss>"
	EndIf
	
	if( !empty( allTrim( cMvNFSEINC ) ) )
		if( SC5->( FieldPos( cMvNFSEINC ) ) > 0 )
			cString	+= "<cMunIncidencia>" + allTrim( SC5-> & ( cMvNFSEINC ) ) + "</cMunIncidencia>"
		endIf
	else
		if( !empty( allTrim( cMunPrest ) ) )
			cString	+= "<cMunIncidencia>" + allTrim( cMunPrest ) + "</cMunIncidencia>"
		endIf
	endIf

	cString += "<cresponsavelretencao>1</cresponsavelretencao>"
	cString	+= "</identificacao>"

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} substit
Função para montar a tag de substituição do XML de envio de NFS-e ao TSS. - Nao Obrigat.

@author Marcos Taranta
@since 19.01.2012

@param	aNota	Array com informações sobre a nota.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function substit( aNota )
	Local cString := ""

	if !empty( allTrim( aNota[8] ) + allTrim( aNota[7] ) )
		
		cString += "<substituicao>"
		cString	+= "<serierps>" + allTrim(aNota[8]) + "</serierps>"
		cString	+= "<numerorps>" + allTrim(str( val(aNota[7]))) + "</numerorps>"
		cString += "<numeronfse>"    + aNota[2] + "</numeronfse>"
		cString	+= "<idnfse>" + aNota[8] + allTrim(aNota[7]) + "</idnfse>"
		cString += "<tipo>1</tipo>"  //-- Tipo do Documento: 1-RPS;2-Nota Fiscal Conjugada (Mista);3-Cupom;
		cString += "<dtEmissaonfse>" + SubStr(dToS(aNota[3]), 1, 4) + "-" + SubStr(dToS(aNota[3]), 5, 2) + "-" + SubStr(Dtos(aNota[3]), 7, 2) + "</dtEmissaonfse>"
		cString += "</substituicao>"

	endif

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} ativ
Função para montar a tag de atividade do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 19.01.2012

@param	aProd	Array contendo as informações sobre os serviços da nota.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function ativ( aProd, aISSQN, aRetSF3 )
	Local cString := ""
	Local lUsaSF3  := GetNewPar("MV_ENVSF3",.F.)

	Default aRetSF3 := {}

	If lUsaSF3
		
		If  !empty( allTrim( aRetSF3[1][2] ))
			cString	+= "<atividade>"
			cString	+= "<codigo>" + allTrim( aRetSF3[1][2] ) + "</codigo>" 
			cString += "<aliquota>" + convType(DivCem(aISSQN[1][2]),7,4) + "</aliquota>"
			cString	+= "</atividade>"
		EndIf
	Else
		If !Empty( allTrim( aProd[1][19] ) )
			cString += "<atividade>"
			cString += "<codigo>"   + allTrim( aProd[1][19] )     + "</codigo>"
			cString += "<aliquota>" + convType(DivCem(aISSQN[1][2]),7,4) + "</aliquota>"
			cString += "</atividade>"
		EndIf
	EndIf
Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} prest
Função para montar a tag de prestador do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 19.01.2012

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function prest( cMunPSIAFI )
	Local aTemp			:= {}
	Local cImPrestador	:= allTrim( SM0->M0_INSCM )
	Local cIEPrestador	:= allTrim( SM0->M0_INSC )
	Local cMVINCECUL	:= allTrim( GetMV( "MV_INCECUL",, "2" ) ) //-- Contribuinte optante do incentivo a cultura: 1=sim;2=nao
	Local cMVOPTSIMP	:= allTrim( GetMV( "MV_OPTSIMP",, "2" ) ) //-- Contribuinte optante do simples: 1=sim;2=nao
	Local cMVNUMPROC	:= allTrim( GetMV( "MV_NUMPROC",, " " ) ) //-- Numero processo judicial ou adm suspensao da exibilidade
	Local cEmail		:= allTrim( GetMV( "MV_EMAILPT",, " " ) ) //-- email prestador
	Local cString		:= ""

	default	cMunPSIAFI	:= ""

	aTemp := fisGetEnd( SM0->M0_ENDCOB )

	cImPrestador := strTran( cImPrestador, "-", "" )
	cImPrestador := strTran( cImPrestador, "/", "" )

	cIEPrestador := strTran( cIEPrestador, "-", "" )
	cIEPrestador := strTran( cIEPrestador, "/", "" )

	cString += "<prestador>"
	cString += "<inscmun>"       + allTrim( cImPrestador )    + "</inscmun>"
	cString += "<cpfcnpj>"       + allTrim( SM0->M0_CGC )     + "</cpfcnpj>"
	cString += "<razao>"         + allTrim( SM0->M0_NOMECOM ) + "</razao>"
	cString += "<fantasia>"      + allTrim( SM0->M0_NOME )    + "</fantasia>"
	cString += "<codmunibge>"    + allTrim( SM0->M0_CODMUN )  + "</codmunibge>"
	cString += "<codmunsiafi>"   + cMunPSIAFI                  + "</codmunsiafi>"
	If !Empty(SM0->M0_CIDCOB)
		cString += "<cidade>"    + allTrim( SM0->M0_CIDCOB )  + "</cidade>"
	EndIf
	cString += "<uf>" + allTrim( SM0->M0_ESTCOB ) + "</uf>"
	if !Empty(cEmail)
		cString += "<email>"     + cEmail + "</email>"
	endif
	//-- DDD do Telefone do Prestador e Telefone do Prestador, Gerando as respectivas Tag's <ddd> e <telefone> - Obrigat.
	cString += getDDDTel(SM0->M0_TEL)
	//-- Optante pelo Simples Nacional - 1-Sim;2-Nao - Obrigat.
	cString += "<simpnac>"       + cMVOPTSIMP + "</simpnac>"
	//-- Incentivador Cultural - 1-Sim;2-Nao - Obrigat.
	cString += "<incentcult>"    + cMVINCECUL + "</incentcult>"
	//-- Numero do processo judicial ou administrativo de suspensao da exigibilidade - Nao Obrigat.
	cString += "<numproc>"       + cMVNUMPROC + "</numproc>"
	cString += "<logradouro>"    + allTrim( aTemp[1] ) + "</logradouro>"
	cString += "<numend>"        + allTrim( aTemp[3] ) + "</numend>"
	if !empty( allTrim( aTemp[4] ) )
		cString	+= "<compleend>" + allTrim( aTemp[4] ) + "</compleend>"
	elseif !Empty(SM0->M0_COMPCOB)
		cString	+= "<compleend>" + allTrim( SM0->M0_COMPCOB ) + "</compleend>"	
	endif
	cString += "<bairro>"        + allTrim( SM0->M0_BAIRCOB ) + "</bairro>"
	cString += "<tplogradouro>2</tplogradouro>" //-- 2-Rua - Nao Obrigat.
	cString += "<tpbairro>1</tpbairro>"         //-- 1-Bairro - Nao Obrigat.
	cString += "<cep>"           + allTrim( SM0->M0_CEPCOB )  + "</cep>"
	cString += "<cie>"           + allTrim( cIEPrestador )    + "</cie>"
	//-- Data de adesão ao Simples Nacional.
	cString += "<dtadesaosn></dtadesaosn>"
	cString += "</prestador>"

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} prestacao
Função para montar a tag de prestação do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 19.01.2012

@param	cMunPrest	Código de município IBGE da prestação do serviço.
@param	cDescMunP	Nome do município da prestação do serviço.
@param	aDest		Array contendo as informações sobre o tomador da nota.
@param	cMunPSIAFI	Código de município SIAFI da prestação do serviço.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function prestacao( cMunPrest, cDescMunP, aDest, cMunPSIAFI )
	Local aTabIBGE		:= {}
	Local cString		:= ""
	Local cMvNFSEINC	:= SuperGetMV("MV_NFSEINC", .F., "") // Parametro que aponta para o campo da SC5 com Código do município de Incidência 
	Local nScan			:= 0
	
	default	cDescMunP	:= ""
	default	cMunPrest	:= ""
	default	cMunPSIAFI	:= ""

	aTabIBGE := spedTabIBGE()

	If Len( cMunPrest ) <= 5
		nScan := aScan( aTabIBGE, { | x | x[1] == aDest[9] } )
		If nScan <= 0
			nScan := aScan( aTabIBGE, { | x | x[4] == aDest[9] } )
			cMunPrest := aTabIBGE[nScan][1] + cMunPrest
		Else
			cMunPrest := aTabIBGE[nScan][4] + cMunPrest
		EndIf
	EndIf

	If Empty( cMunPrest )
		cMunPrest := allTrim( aDest[7] )
	EndIf
	If Empty( cMunPSIAFI )
		cMunPSIAFI := allTrim( aDest[18] )
	EndIf

	cString += "<prestacao>"
	cString += "<serieprest>99</serieprest>"
	If SC5->(FieldPos("C5_ENDPRES")) > 0
		cString += "<logradouro>" +  IIF( !Empty(FisGetEnd(SC5->C5_ENDPRES)[1] ),   FisGetEnd(SC5->C5_ENDPRES)[1], aDest[3] ) + "</logradouro>"
		cString += "<numend>"     + ConvType(IIF(FisGetEnd(SC5->C5_ENDPRES)[2]<> 0, FisGetEnd(SC5->C5_ENDPRES)[2], aDest[4] )) + "</numend>"
	Else
		cString += "<logradouro>" + IIf(!Empty(aDest[3]),allTrim( aDest[3] ),"") + "</logradouro>"
		cString += "<numend>"     + allTrim( aDest[4] ) + "</numend>"
	EndIf
	If !Empty( allTrim( aDest[5] ) )
		cString += "<complend>"  + allTrim( aDest[5] ) + "</complend>"
	EndIf
	If !Empty( allTrim( cMunPrest ) )
		cString += "<codmunibge>" + allTrim( cMunPrest ) + "</codmunibge>"
	EndIf

	If !Empty( allTrim (cMvNFSEINC) ) 
		If( SC5-> ( FieldPos (cMvNFSEINC)  ) > 0 )
			cString	+= "<codmunincidenciaibge>"+ allTrim(SC5-> & (cMvNFSEINC) ) +"</codmunincidenciaibge>"
		Endif		
	Else
		If !empty( allTrim (cMunPrest) )
			cString	+= "<codmunincidenciaibge>"+ allTrim(cMunPrest) +"</codmunincidenciaibge>"  
		endif		
	Endif	
	If !Empty( allTrim( cMunPSIAFI ) )
		cString += "<codmunsiafi>" + allTrim( cMunPSIAFI ) + "</codmunsiafi>"
	endif
	cString += "<municipio>" + allTrim( cDescMunP ) + "</municipio>"
	If SC5->(FieldPos("C5_BAIPRES")) > 0	
		cString += "<bairro>" + IIF ( !Empty(SC5->C5_BAIPRES), SC5->C5_BAIPRES, aDest[6] ) + "</bairro>"
	Else
		cString += "<bairro>" + IIf(!Empty(aDest[6]),allTrim( aDest[6] ),"") + "</bairro>"
	EndIf
	If SC5->(FieldPos("C5_ESTPRES")) > 0
		cString += "<uf>" + IIF ( !Empty(SC5->C5_ESTPRES), SC5->C5_ESTPRES, aDest[9] ) + "</uf>" 
	Else
		cString += "<uf>" + IIf(!Empty(aDest[9]),allTrim( aDest[9] ),"") + "</uf>"
	EndIf
	If SC5->(FieldPos("C5_CEPPRES")) > 0
		cString += "<cep>" + IIF ( !Empty(SC5->C5_CEPPRES), SC5->C5_CEPPRES, aDest[10]) + "</cep>"
	Else
		cString += "<cep>" + IIf(!Empty(aDest[10]),allTrim( aDest[10] ),"" ) + "</cep>"
	EndIf
	cString += "</prestacao>"

Return cString
//-----------------------------------------------------------------------
/*/{Protheus.doc} intermediario
Função para montar a tag de intermediário do XML de envio de NFS-e ao TSS.

@author Karyna Martins
@since 24.04.2015

@param	aInterm	Array com as informações do intermediario da nota.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function intermediario( aInterm )

Local cString	:= "" 

Local lSemInt:= .F.

If len(aInterm) > 0

	If Empty(aInterm[1]) .and. Empty(aInterm[2]) .and. Empty(aInterm[3])
		lSemInt:= .T.
	EndIf
	  
	// Monta a tag de intermediário com as informações do pedido
	If !lSemInt 
	
		cString	+= "<intermediario>"
			cString	+= "<razao>"  + allTrim( aInterm[1])+"</razao>"
			cString	+= "<cpfcnpj>"+ allTrim( aInterm[2])+"</cpfcnpj>"
			cString	+= "<inscmun>"+ alltrim( aInterm[3])+"</inscmun>"	
		cString	+= "</intermediario>"
		
	EndIf

EndIf
	
return cString
//-----------------------------------------------------------------------
/*/{Protheus.doc} tomador
Função para montar a tag de tomador do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 19.01.2012

@param	aDest	Array com as informações do tomador da nota.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function tomador( aDest )
	Local cString   := ""
	Local cCodTom   := ""
	Local lTomador  := .T.
	Local aIntermed := {}

	If Empty(aDest[1]) .And. Empty(aDest[2])
		lTomador:=.F.
	EndIf

	If lTomador
		cString	+= "<tomador>"
		If aDest[17] <> "ISENTO" .And. !Empty( aDest[17] )
			cString += "<inscmun>" + allTrim( aDest[17] ) + "</inscmun>"
		Else
			cString +=  "<inscmun></inscmun>"
		EndIf
		cString += "<cpfcnpj>"    + iif( allTrim( aDest[9] ) == "EX", "99999999999999", allTrim( aDest[1] ) ) + "</cpfcnpj>"
		cString += "<razao>"      + allTrim( aDest[2] ) + "</razao>"
		cString += "<tipologr>" + retTipoLogr( aDest[ 3 ] ) + "</tipologr>"
		cString += "<logradouro>" + allTrim( aDest[3] ) + "</logradouro>"
		cString += "<numend>"     + allTrim( aDest[4] ) + "</numend>"
		If !Empty( aDest[5] )
			cString += "<complend>" + allTrim( aDest[5] ) + "</complend>"
		EndIf
		cString += "<tipobairro>1</tipobairro>" //-- 1-Bairro - Nao Obrigat.
		cString += "<bairro>" + allTrim( aDest[6] ) + "</bairro>"
		cCodTom := aDest[07] // SA1->A1_COD_MUN
		If Len(cCodTom) <= 5 .And. !(cCodTom$'99999')
			cCodTom := UfIBGEUni(aDest[09]) + cCodTom
		EndIf
		If !Empty( aDest[7] )
			cString += "<codmunibge>" + cCodTom + "</codmunibge>"
		EndIf
		If !Empty( aDest[18] )
			cString += "<codmunsiafi>" + allTrim( aDest[18] ) + "</codmunsiafi>"
		EndIf
		cString += "<cidade>" + allTrim( aDest[ 8] ) + "</cidade>"
		cString += "<uf>"     + allTrim( aDest[ 9] ) + "</uf>"
		cString += "<cep>"    + iif( allTrim( aDest[9] ) == "EX", "99999999", allTrim( aDest[10] ) ) + "</cep>"
		If !Empty( aDest[16] )
			cString += "<email>" + allTrim( aDest[16] ) + "</email>"
		EndIf

		//-- DDD do Telefone do Tomador e Telefone do Tomador,Gerando as respectivas Tag's <ddd> e <telefone> - Obrigat.
		cString += getDDDTel(aDest[13])
		//-- Codigo do Pais do Tomador (BACEN) - Obrigat.
		cString += "<codpais>"     + allTrim( aDest[11] ) + "</codpais>"
		//-- Nome do Pais do Tomador - Obrigat.
		cString += "<nomepais>"    + allTrim( aDest[12] ) + "</nomepais>"
		//- Define se o Tomador eh estrangeiro - 1-Sim;2-Nao - Obrigat.
		cString += "<estrangeiro>" + iif( allTrim( aDest[9] ) == "EX", "1", "2" ) + "</estrangeiro>"
		//-- Indicativo para notificar tomador por e-mail - Nao Obrigat.
		If Empty( aDest[16] )
			cString += "<notificatomador>2</notificatomador>" // 2-Nao
		Else
			cString += "<notificatomador>1</notificatomador>" // 1-Sim
		EndIf
		//-- Situacao Especial do Tomador: 0-Outros;1-SUS;2-Orgao Poder Executivo;3-Bancos;4-Comercio/Industria;5-Poder Legislativo/Executivo - Obrigat.
		cString += "<csituacaoesptom>0</csituacaoesptom>" //Obrigat.
		//-- Identificacao de 1-Sim/2-Nao - Nao Obrigat. 
		If allTrim( upper( aDest[ 9 ] ) ) == "EX"
			cString += "<ctomnaoidentificado>1</ctomnaoidentificado>"
		Else
			cString += "<ctomnaoidentificado>2</ctomnaoidentificado>"
		Endif
		//-- tratativa para geração da tag de Inscricao Estadual no XML
		If !empty(aDest[14]) .and. aDest[14] <> 'ISENTO'
		   cString += "<cietom>" + alltrim(aDest[14]) + "</cietom>"
		Else
		   cString += "<cietom></cietom>"
		EndIf
		//-- Ponto de referência do endereço, do estabelecimento ou residência do Tomador do(s) Serviço(s).
		cString += "<pontoreferenciatom></pontoreferenciatom>"
		//--  Inscrição Municipal do Tomador Substituto. 
		cString += "<cimsubstituto></cimsubstituto>"	
		cString	+= "</tomador>"
		
		If SM0->M0_CODMUN == "3550308" .And. Len(aDest) > 21
			If !Empty(aDest[22]) .And. !Empty(aDest[23])
				If FindFunction("HS_NFEINTE")
					aIntermed := HS_NFEINTE(aDest[22],aDest[23])
					If Len(aIntermed) > 0 .And. !Empty(aIntermed[1])
						cString += '<CPFCNPJIntermediario>'+AllTrim(aIntermed[1])+'</CPFCNPJIntermediario>'
						cString += '<InscricaoMunicipalIntermediario>'+(aIntermed[2])+'</InscricaoMunicipalIntermediario>'
						cString += '<ISSRetidoIntermediario>1</ISSRetidoIntermediario>'
					EndIf
					
				EndIf
			EndIf
		EndIf		
					
	EndIf

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} servicos
Função para montar a tag de serviços do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 19.01.2012

@param	aProd		Array contendo as informações dos produtos da nota.
@param	aISSQN		Array contendo as informações sobre o imposto.
@param	aRetido		Array contendo as informações sobre impostos retidos.
@param	cNatOper	String contendo discriminacao do servico
@param	lNFeDesc	Logico contendo conteudo do parametro MV_NFEDESC

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function servicos( aProd, aISSQN, aRetido, cNatOper, lNFeDesc, cDiscrNFSe,aCST, cTpPessoa, cCodMun, cF4Agreg, nDescon, aRetSF3   )	
	Local aCofinsXML	:= { 0, 0, {} }
	Local aCSLLXML		:= { 0, 0, {} }
	Local aINSSXML		:= { 0, 0, {} }
	Local aIRRFXML		:= { 0, 0, {} }
	Local aISSRet		:= { 0, 0, 0, {} }
	Local aPisXML		:= { 0, 0, {} }

	Local cString		:= ""
	Local cCargaTrb		:= ""
	local cFieldMsg		:= GetMV("MV_CMPUSR")
	
	Local nOutRet		:= 0
	Local nScan			:= 0
	Local nValLiq		:= 0
	Local nX			:= 0

	Local lUsaSF3  		:= GetNewPar("MV_ENVSF3",.F.)
	Local lMvDescInc	:= SuperGetMV("MV_NFSEDIN",,.F. )	// Habilita/Desabilita os Descontos Incondicionados da NFSE
	
	Default cTpPessoa	:= ""
	Default cCodMun		:= ""
	Default cF4Agreg	:= ""
	Default nDescon		:= 0
	Default aRetSF3		:= {}
	
	cString += "<servicos>"
	
	For nX := 1 To Len( aProd )
		
		nScan := aScan(aRetido,{|x| x[1] == "ISS"})
		If nScan > 0
			aIssRet[1] += aRetido[nScan][3]
			aIssRet[2] += aRetido[nScan][5]
			aIssRet[3] += aRetido[nScan][4]
			aIssRet[4] := aRetido[nScan][6]
		EndIf
		
		nScan := aScan(aRetido,{|x| x[1] == "PIS"})
		If nScan > 0
			aPisXml[1] := aRetido[nScan][3]
			aPisXml[2] += aRetido[nScan][4]
			aPisXml[3] := aRetido[nScan][5]
		EndIf
		
		nScan := aScan(aRetido,{|x| x[1] == "COFINS"})
		If nScan > 0
			aCofinsXml[1] := aRetido[nScan][3]
			aCofinsXml[2] += aRetido[nScan][4]
			aCofinsXml[3] := aRetido[nScan][5]
		EndIf

		nScan := aScan(aRetido,{|x| x[1] == "IRRF"})
		If nScan > 0
			aIrrfXml[1] := aRetido[nScan][3]
			aIrrfXml[2] += aRetido[nScan][4]
			aIrrfXml[3] := aRetido[nScan][5]
		EndIf

		nScan := aScan(aRetido,{|x| x[1] == "CSLL"})
		If nScan > 0
			aCSLLXml[1] := aRetido[nScan][3]
			aCSLLXml[2] += aRetido[nScan][4]
			aCSLLXml[3] := aRetido[nScan][5]
		EndIf

		nScan := aScan(aRetido,{|x| x[1] == "INSS"})
		If nScan > 0
			aInssXml[1] := aRetido[nScan][3]
			aInssXml[2] += aRetido[nScan][4]
			aInssXml[3] := aRetido[nScan][5]
		EndIf

		//Carga Tributária
		If aProd[Nx][35] > 0
			cCargaTrb := " - Valor aproximado dos tributos: R$ " + ConvType(aProd[Nx][35],15,2) +"."
		EndIf

		//Outras retenções, sera colocado o valor 0 (zero), pois atualmente nao existe valor de Outras retencoes 
		If Len(aRetido) > 0
			nOutRet := 0
		EndIf
		nValLiq := aProd[Nx][27] - aPisXml[3][Nx] - aCofinsXml[3][Nx]  - Iif(Len(aInssXml[3]) > 1 .And. len( aProd ) > 1,aInssXml[3][Nx],aInssXml[1]) - Iif(Len(aIRRFXml[3]) > 1 .And. len( aProd ) > 1,aIRRFXml[3][Nx],aIRRFXml[1]) - aCSLLXml[3][Nx] - Iif(Len(aIssRet[4]) > 1 .And. len( aProd ) > 1,aIssRet[4][Nx],aIssRet[1])
		cString += "<servico>"

		If lUsaSF3	
			cString += "<codigo>" + allTrim( aRetSF3[nX][5] ) + "</codigo>"
			cString += "<aliquota>" + allTrim((iif(!empty( convType( DivCem(aISSQN[1][2]),7,4 ) ), convType( DivCem(aISSQN[1][2]), 7, 4 ), convType(DivCem( aISSRet[3]),7,4) ))) + "</aliquota>"
			cString	+= "<cnae>" + allTrim( aRetSF3[nX][2] ) + "</cnae>" 
			cString	+= "<codtrib>" + allTrim( aRetSF3[nX][3] ) + "</codtrib>"
		Else
			cString += "<codigo>" + allTrim( aProd[nX][24] ) + "</codigo>"
			cString += "<aliquota>" + allTrim((iif(!empty( convType( DivCem(aISSQN[1][2]),7,4 ) ), convType( DivCem(aISSQN[1][2]), 7, 4 ), convType(DivCem( aISSRet[3]),7,4) ))) + "</aliquota>"
			cString += "<cnae>"    + allTrim( aProd[nX][19] ) + "</cnae>"
			cString += "<codtrib>" + allTrim( aProd[nX][32] ) + "</codtrib>"
		EndIf

		If ( SC6->(FieldPos("C6_DESCRI")) > 0 .And. Len(aProd[nX]) > 40 .And. !Empty(aProd[nX][41]) ) .And. (!lNFeDesc .And. !GetNewPar("MV_NFESERV","1") == "1" .And. !Empty(cFieldMsg) )
			cString	+= "<discr>" + AllTrim(aProd[nX][41])+ cCargaTrb + "</discr>"
		ElseIf !lNFeDesc
			cString	+= "<discr>" + AllTrim(cNatOper)+ cCargaTrb + "</discr>"
		Else
			cString	+= "<discr>" + AllTrim(cDiscrNFSe)+ cCargaTrb + "</discr>"
		EndIf
		cString += "<quant>"     + allTrim( convType( aProd[nX][ 9], 15, 2 ) ) + "</quant>"
		cString += "<valunit>"   + allTrim( convType( aProd[nX][10], 15, 2 ) ) + "</valunit>"
		cString += "<valtotal>"  + allTrim( convType( aProd[nX][28], 15, 2 ) ) + "</valtotal>"
		cString += "<basecalc>"  + allTrim( convType( aProd[nX][25], 15, 2 ) ) + "</basecalc>"
		cString += "<issretido>" + iif( !Empty( aISSRet[2] ), "1", "2" )       + "</issretido>"
		cString += "<valdedu>"   + allTrim( convType( aProd[nX][29], 15, 2 ) ) + "</valdedu>"
		cString += "<valpis>"    + allTrim( convType( aPisXml[1],    15, 2 ) ) + "</valpis>"
		cString += "<valcof>"    + allTrim( convType( aCofinsXml[1], 15, 2 ) ) + "</valcof>"
		cString += "<valinss>"   + allTrim( convType( aInssXml[1],   15, 2 ) ) + "</valinss>"
		cString += "<valir>"     + allTrim( convType( aIRRFXml[1],   15, 2 ) ) + "</valir>"
		cString += "<valcsll>"   + allTrim( convType( aCSLLXml[1],   15, 2 ) ) + "</valcsll>"
		cString += "<valiss>"    + allTrim( ConvType( aISSQN[nX][3]  ,15,2 ) ) + "</valiss>"		
		cString += "<valissret>" + alltrim( convType( iif(len(aissret[4]) > 0, aissret[4][nx],0), 15 , 2) ) + "</valissret>"
		cString += "<outrasret>" + allTrim( convType( nOutRet,       15, 2 ) ) + "</outrasret>"
		cString += "<valliq>"    + allTrim( convType( nValLiq,       15, 2 ) ) + "</valliq>"
		cString	+= "<desccond>0.00</desccond>"
			
		If lMvDescInc
			cString += "<descinc>" + allTrim( convType(aISSQN[nX][6],15,2) ) + "</descinc>"
		Else
			cString +="<descinc>0.00</descinc>"
		EndIf	
		cString += "<unidmed>" + Alltrim(aProd[Nx][08]) + "</unidmed>" //-- Nao Obrigat. - campo descontinuado
//		cString += "<tributavel></tributavel>" //Nao Obrigat. - sem uso, existe no grupo valores
		If !Empty( allTrim( aProd[nX][33] ) )
			cString += "<cfps>" + allTrim( aProd[nX][33] ) + "</cfps>" //-- codigo fiscal de prestacao de servico - Nao Obrigat.
		EndIf
		//-- Valor dos impostos municipais.
		cString += "<vltributosmunicpiais></vltributosmunicpiais>"  
		//-- Valor dos impostos federais.
		cString += "<vltributosfederais></vltributosfederais>" 
		
		cString += "</servico>"

	Next nX

	cString += "</servicos>"

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} valores
Função para montar a tag de valores do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 23.01.2012

@param	aISSQN		Array contendo as informações sobre imposto.
@param	aRetido		Array contendo as informações sobre impostos retidos.
@param	aTotal		Array contendo os valores totais da nota.
@param	aDest		Array contendo as informações de destinatário.
@param	cCodMun		string contendo codigo do municipio prestador

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function valores( aISSQN, aRetido, aTotal, aDest, cCodMun , aDeducao )

	Local aCOFINSXML	:= { 0, 0, 0 }
	Local aCSLLXML		:= { 0, 0, 0 }
	Local aINSSXML		:= { 0, 0, 0 }
	Local aIRRFXML		:= { 0, 0, 0 }
	Local aISSRet		:= { 0, 0, 0 }
	Local aPISXML		:= { 0, 0, 0 }
	Local cString		:= ""
	Local nOutRet		:= 0
	Local nScan			:= 0
	Local nY			:= 0
	local nBase			:= 0
	local nValIss		:= 0
	local nValDeduz		:= 0
	local cNbs			:= ""
	
	If Len (aDeducao) > 0
	
		For nY := 1 to Len(aDeducao)
			nValDeduz += aDeducao[nY,1]
		Next nY
	
	EndIf 
	
	// Tratando o abatimento para quando houver mais de um item de serviço
	If len(aISSQN) > 1
		For nY := 1  to len(aISSQN)
			If 	aISSQN[nY][2] > 0
				nBase 		+= aISSQN[nY][1]
				nValIss	+= aISSQN[nY][3]
			EndIf
		Next nY
	Else
		nBase 		:= aISSQN[1][1]
		nValIss	:= aISSQN[1][3]		
	EndIF
	
	nScan := aScan( aRetido, { | x | x[1] == "ISS" } )
	If nScan > 0
		aISSRet[1]	+= aRetido[nScan][3]
		aISSRet[2]	+= aRetido[nScan][5]
		aISSRet[3]	+= aRetido[nScan][4]
	EndIf

	nScan := aScan( aRetido, { | x | x[1] == "PIS" } )
	If nScan > 0
		aPISXML[1] := aRetido[nScan][3]
		aPISXML[2] += aRetido[nScan][4]
		aPISXML[3] += aRetido[nScan][2]
	EndIf

	nScan := aScan( aRetido, { | x | x[1] == "COFINS" } )
	If nScan > 0
		aCOFINSXML[1] := aRetido[nScan][3]
		aCOFINSXML[2] += aRetido[nScan][4]
		aCOFINSXML[3] += aRetido[nScan][2]
	EndIf

	nScan := aScan( aRetido, { | x | x[1] == "INSS" } )
	If nScan > 0
		aINSSXML[1] := aRetido[nScan][3]
		aINSSXML[2] += aRetido[nScan][4]
		aINSSXML[3] += aRetido[nScan][2]
	EndIf

	nScan := aScan( aRetido, { | x | x[1] == "IRRF" } )
	If nScan > 0
		aIRRFXML[1] := aRetido[nScan][3]
		aIRRFXML[2] += aRetido[nScan][4]
		aIRRFXML[3] += aRetido[nScan][2]
	EndIf

	nScan := aScan( aRetido, { | x | x[1] == "CSLL" } )
	If nScan > 0
		aCSLLXML[1] := aRetido[nScan][3]
		aCSLLXML[2] += aRetido[nScan][4]
		aCSLLXML[3] += aRetido[nScan][2]
	EndIf

	If Len( aRetido ) > 0
		nOutRet	:= 0
	EndIf

	If !Empty(SB5->B5_NBS)
		cNbs := SB5->B5_NBS
	EndIf


	cString	+= "<valores>"
	//Para os campos: ValorMulta,ValorJuros,ValorIPI campos ainda sem origem das informações.
	cString += '<ValorMulta>0</ValorMulta>'
	cString += '<ValorJuros>0</ValorJuros>'
	cString += '<ValorIPI>0</ValorIPI>'

	cString += "<iss>"        + allTrim( convType( nValIss,       15, 2 ) ) + "</iss>"
	cString += "<issret>"     + allTrim( convType( aISSRet[1],    15, 2 ) ) + "</issret>"
	cString += "<outrret>"    + allTrim( convType( nOutRet,       15, 2 ) ) + "</outrret>"
	cString += "<pis>"        + allTrim( convType( aPISXML[1],    15, 2 ) ) + "</pis>"
	cString += "<cofins>"     + allTrim( convType( aCOFINSXml[1], 15, 2 ) ) + "</cofins>"
	cString += "<inss>"       + allTrim( convType( aINSSXML[1],   15, 2 ) ) + "</inss>"
	cString += "<ir>"         + allTrim( convType( aIRRFXML[1],   15, 2 ) ) + "</ir>"
	cString += "<csll>"       + allTrim( convType( aCSLLXML[1],   15, 2 ) ) + "</csll>"
	cString += "<aliqiss>"    + allTrim( convType( (DivCem(Iif( !empty( aISSQN[1][02] ), aISSQN[1][02], aISSRet[3] ))), 15, 4 ) ) + "</aliqiss>"
	cString += "<aliqpis>"    + allTrim( convType( DivCem(aPISXML[2])	  	, 15, 4 ) ) + "</aliqpis>"
	cString += "<aliqcof>"    + allTrim( convType( DivCem(aCOFINSXML[2])	, 15, 4 ) ) + "</aliqcof>"
	cString += "<aliqinss>"   + allTrim( convType( DivCem(aINSSXML[2])		, 15, 4 ) ) + "</aliqinss>"
	cString += "<aliqir>"     + allTrim( convType( DivCem(aIRRFXML[2])		, 15, 4 ) ) + "</aliqir>"
	cString += "<aliqcsll>"   + allTrim( convType( DivCem(aCSLLXML[2])		, 15, 4 ) ) + "</aliqcsll>"
	cString += "<valtotdoc>"  + allTrim( convType( aTotal[4],     15, 2 ) ) + "</valtotdoc>"
	cString += "<basecalculo>"+ allTrim( convType( nBase,         15, 2 ) ) + "</basecalculo>"
	cString += "<vliquinfse>" + allTrim( convType( aTotal[2],     15, 2 ) ) + "</vliquinfse>"
	//-- Justificativa para dedução
	cString += "<dJustificaDeducao></dJustificaDeducao>"    
	cString += "<basecalculopis>"   + allTrim( convType( aPISXML[3],   15, 2 ) ) + "</basecalculopis>"
	cString += "<basecalculocofins>"+ allTrim( convType( aCOFINSXML[3],15, 2 ) ) + "</basecalculocofins>"
	cString += "<basecalculocsll>"  + allTrim( convType( aCSLLXML[3],  15, 2 ) ) + "</basecalculocsll>"
	cString += "<basecalculoirrf>"  + allTrim( convType( aIRRFXML[3],  15, 2 ) ) + "</basecalculoirrf>"
	cString += "<basecalculoinss>"  + allTrim( convType( aINSSXML[3],  15, 2 ) ) + "</basecalculoinss>"
	 //-- Alíquota de outro município envolvido na prestação do serviço.
	cString += "<aloutromunicipio></aloutromunicipio> 
	 //-- Alíquota do simples Nacional ou do Contribuinte que tem Isenção Parcial.
	cString += "<alsnip></alsnip>
	//-- Valor de dedução do valor na base de cálculo do INSS.
	cString += "<vldeducaobaseinss></vldeducaobaseinss> 
	//Codigo NBS
	cString	+= "<codigonbs>"+cNbs+"</codigonbs>"
	cString += "</valores>"

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} faturas
Função para montar a tag de faturas do XML de envio de NFS-e ao TSS.

@author Flavio Luiz Vicco
@since 08.08.2014

@param	aDupl		Array contendo informações sobre as faturas.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function faturas( aDupl,cCondPag )
	Local cString	:= ""
	Local nX		:= 0

	Default cCondPag	:= ""

	If Len( aDupl ) > 0
		cString	+= "<faturas>"
		For nX := 1 To Len( aDupl )
			cString += "<fatura>"
			cString += "<numero>" + allTrim( aDupl[nX][1] ) + "</numero>"
			cString += "<valor>"  + allTrim( convType( aDupl[nX][3], 15, 2 ) ) + "</valor>"

			//-- Condição/Forma de Pagamento 
			if ("00" == AllTrim(cCondPag))
				cString += "<condPagamento>1</condPagamento>"
			elseif (AllTrim(cCondPag)>"00" .And. !("," $ AllTrim(cCondPag)))
				cString += "<condPagamento>2</condPagamento>"		
			elseif ("," $ AllTrim(cCondPag)) 
				cString += "<condPagamento>3</condPagamento>"
			elseif ("0" $ AllTrim(cCondPag) .Or. "%" $ AllTrim(cCondPag) )	
				If len( aDupl ) == 1
					cString += "<condPagamento>1</condPagamento>"
				ElseIf len( aDupl ) > 1
					cString += "<condPagamento>3</condPagamento>"
				EndIf	
			endif

			//-- Descricação o tipo de vencimento da fatura.
			cString += "<descFatura></descFatura>"
			//-- URL para impressão da fatura/ boleto
			cString += "<urlFatura></urlFatura>"
			//-- "Indicador de geração do boleto na prefeitura | 1 - Sim 2 - Não"
			cString += "<gerarFatura></gerarFatura>"		
			cString += "</fatura>"
		Next nX
		cString += "</faturas>"
	EndIf

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} pagtos
Função para montar a tag de valores do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 06.02.2012

@param	aDupl		Array contendo informações sobre os pagamentos.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function pagtos( aDupl )
	Local cString	:= ""
	Local cTemp		:= ""
	Local nX		:= 0

	If Len( aDupl ) > 0
		cString	+= "<pagamentos>"
		For nX := 1 To Len( aDupl )
			cTemp := dToS( aDupl[nX][2] )
			cString += "<pagamento>"
			cString += "<parcela>" + iif( !Empty( allTrim( aDupl[nX][4] ) ), allTrim( aDupl[nX][4] ), "1" ) + "</parcela>"
			cString += "<dtvenc>"  + subStr( allTrim( cTemp ), 1, 4 ) + "-" + subStr( allTrim( cTemp ), 5, 2 ) + "-" + subStr( allTrim( cTemp ), 7, 2 ) + "</dtvenc>"
			cString += "<valor>"   + allTrim( convType( aDupl[nX][3], 15, 2 ) ) + "</valor>"
			cString += "</pagamento>"
		Next nX
		cString += "</pagamentos>"
	EndIf

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} deducoes
Função para montar a tag de deduções do XML de envio de NFS-e ao TSS.

@author Marcos Taranta
@since 23.01.2012

@param	aProd	Array contendo as informações sobre os serviços.
@param	aDeduz	Array contendo as informações sobre as deduções.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function deducoes( aISSQN, aDeduz, aDeducao, aConstr )

	Local cCPFCNPJ	:= ""
	Local cString	:= ""
	Local nX		:= 0
	Local nDesInc := 0

	If Len( aDeduz ) <= 0 .And. Len( aDeducao ) <= 0
		Return cString
	EndIf

	cString+= "<deducoes>"
	cString += "<desccond>0</desccond>"
	If  Len( aISSQN ) > 0		
		For nX := 1 To Len( aISSQN )
			nDesInc += aISSQN[nX][6]
		Next nX
		cString += "<descincond>" + allTrim( convType( nDesInc, 15, 2 ) ) + "</descincond>"	
	EndIf
	If  Len( aDeduz ) > 0
		For nX := 1 To Len( aDeduz )
			cCPFCNPJ := allTrim( posicione( "SA2", 1, xFilial( "SA2" ) + aDeduz[nX][3] + aDeduz[nX][4], "A2_CGC" ) )
			cString += "<deducao>"
			cString += "<tipo>"       + iif( empty( allTrim( aDeduz[nX][1] ) ), "1", iif( allTrim( aDeduz[nX][1] ) == "1", "1", "2") ) + "</tipo>"
			cString += "<modal>"      + iif( empty( allTrim( aDeduz[nX][2] ) ), "1", iif( allTrim( aDeduz[nX][2] ) == "1", "1", "2" ) ) + "</modal>"
			If !Empty( aConstr )
				cString += '<codobra>'+ AllTrim(aConstr[01]) + '</codobra>'
				cString += '<codart>' + AllTrim(aConstr[02]) +'</codart>'
			Else
				cString += "<codobra></codobra>"
				cString += "<codart></codart>"
			EndIf
			cString += "<cpfcnpj>"    + iif( empty( cCPFCNPJ ), "00000000000191", cCPFCNPJ ) + "</cpfcnpj>"
			cString += "<numeronf>"   + iif( empty( allTrim( aDeduz[nX][6] ) ), "1", allTrim( aDeduz[nX][6] ) ) + "</numeronf>"
			cString += "<totalnf>"    + allTrim( convType( aDeduz[nX][7], 15, 2 ) ) + "</totalnf>"
			cString += "<percentual>" + iif( aDeduz[nX][1] == "1", allTrim( convType( aDeduz[nX][8], 15, 2 ) ), "0.00" ) + "</percentual>"
			cString += "<valor>"      + iif( aDeduz[nX][1] == "2", allTrim( convType( aDeduz[nX][9], 15, 2 ) ), "0.00" ) + "</valor>"
			//-- Descrição do Material
			cString += "<descricaomaterial></descricaomaterial>"
			//-- Valor Unitário do Material
			cString += "<valorunitariomaterial></valorunitariomaterial>"	
			//-- Quantidade do Material
			cString += "<quantidadematerial></quantidadematerial>	
			cString += "</deducao>"
		Next nX
	Else
		For nX := 1 To Len( aDeducao )
			cString += "<deducao>"
			cString += "<tipo>1</tipo>"
			cString += "<modal>1</modal>"
			If !Empty( aConstr )
				cString += '<codobra>'+ AllTrim(aConstr[01]) + '</codobra>'
				cString += '<codart>' + AllTrim(aConstr[02]) +'</codart>'
			EndIf
			cString += "<cpfcnpj>" + iif( empty( cCPFCNPJ ), "00000000000191", cCPFCNPJ ) + "</cpfcnpj>"
			cString += "<numeronf>1</numeronf>"
			cString += "<totalnf>0.00</totalnf>"
			cString += "<percentual>0.00</percentual>"
			cString += "<valor>" + allTrim( convType( aDeducao[nX][1], 15, 2 ) ) + "</valor>"
			cString += "</deducao>"
		Next nX
	EndIf
	cString	+= "</deducoes>"

Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} infCompl
Função para montar a tag de informações complementares do XML de envio
de NFS-e ao TSS.

@author Marcos Taranta
@since 23.01.2012

@param	cMensCli	Mensagem complementar ao cliente.
@param	cMensFis	Mensagem complementar ao fisco.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function infCompl( cMensCli, cMensFis, lNFeDesc, cDescrNFSe, aConstr )
	Local cString := ""
                
	If Empty(cMensCli + cMensFis)
		cMensCli := "-"
	EndIf
	If Empty(cDescrNFSe)
		cDescrNFSe := "-"
	EndIf
	cString += "<infcompl>"
	//-- Descricao - Tam 2000 - Obrigat.
	If !lNFeDesc
		cString += "<descricao>" + convType(cMensCli,len(cMensCli)) + space( 1 ) + convType(cMensFis,len(cMensFis)) + "</descricao>"
	Else
		cString += "<descricao>" + Alltrim(convType(cDescrNFSe,len(cDescrNFSe))) + "</descricao>"
	EndIf
	//-- Observacao - Tam 255 - Nao Obrigat.
	cString += "<observacao>" + convType(cMensCli,len(cMensCli)) + space( 1 ) + convType(cMensFis,len(cMensFis)) + "</observacao>"
	
	if ( !Empty(aConstr[01]) .Or. !Empty(aConstr[02]) )
		cString += "<constrciv>"

			//-- Nome da obra da construção civil.
			cString += "<nomeobra></nomeobra>"	
			//-- Endereço da construção civil.
			cString += If(Len(aConstr) >= 04 .And. !Empty(aConstr[04]), '<endereco>'+aConstr[04]+'</endereco>' , "" )
			//-- Número do endereço da construção civil.
			cString += If(Len(aConstr) >= 06 .And. !Empty(aConstr[06]), '<numero>'+aConstr[06]+'</numero>' , "" )	
			//-- Complemento do endereço da construção civil.		
			cString += If(Len(aConstr) >= 05 .And. !Empty(aConstr[05]), '<compl>'+aConstr[05]+'</compl>' ,"" )	
			//-- Bairro do endereço da construção civil.			
			cString += If(Len(aConstr) >= 07 .And. !Empty(aConstr[07]), '<bairro>'+aConstr[07]+'</bairro>' , "" )	
			//-- Código do município da construção civil.	
			cString += If(Len(aConstr) >= 09 .And. !Empty(aConstr[09]), '<codmunibge>'+ IIF(Len(aConstr[09])==7,aConstr[09],UfIBGEUni(aConstr[11]+ aConstr[09]))+'</codmunibge>' , "" )
			//-- Unidade federativa do endereço da construção civil	
			cString += If(Len(aConstr) >= 11 .And. !Empty(aConstr[11]), '<uf>'+aConstr[11]+'</uf>' , "" )	
			//-- CEP do endereço da construção civil.
			cString += If(Len(aConstr) >= 08 .And. !Empty(aConstr[08]), '<cep>'+aConstr[08]+'</cep>' , "")
			//-- Descrição do município da Obra.
			cString += If(Len(aConstr) >= 10 .And. !Empty(aConstr[10]), '<dMunObra>'+aConstr[10]+'</dMunObra>' , "" )	
			//-- Código do país da Obra.
			cString += If(Len(aConstr) >= 12 .And. !Empty(aConstr[12]), '<cPais>'+aConstr[12]+'</cPais>' , "" )	
			//-- Descrição país da Obra.			
			cString += If(Len(aConstr) >= 13 .And. !Empty(aConstr[13]), '<dPais>'+aConstr[13]+'</dPais>' , "" )	
			//-- Número do projeto.
			cString += If(Len(aConstr) >= 16 .And. !Empty(aConstr[16]), '<nProjObra>'+aConstr[16]+'</nProjObra>' ,"" )	
			//-- Número da matrícula da Obra.
			cString += If(Len(aConstr) >= 17 .And. !Empty(aConstr[17]), '<nMatriObra>'+aConstr[17]+'</nMatriObra>' , "" )
			//-- Redução Base Cálculo Construção Civil.
			cString += "<vlRedBCConstrucaoCivil></vlRedBCConstrucaoCivil>"	
			//-- Valor das deduções de materiais da construção civil.		
			cString += "<dedmat></dedmat>"	
			//-- Valor das deduções de materiais da construção civil.
			cString += "<dedsubemp></dedsubemp>"
			//--  "Serviço prestado em vias públicas.Identificação de Sim/Não: 1 = Sim 2 = Não"
			cString += If(Len(aConstr) >= 03 .And. !Empty(aConstr[03]), '<servprestviapublica>'+aConstr[03]+'</servprestviapublica>' , "<servprestviapublica>2</servprestviapublica>" )
			//-- "Tipo de empreitada Consulte os valores na tabela 9"	
			cString += If(Len(aConstr) >= 18 .And. !Empty(aConstr[18]), '<tpempreitada>'+aConstr[18]+'</tpempreitada>' , "<tpempreitada>1</tpempreitada>" )						
			
		cString += "</constrciv>"	
	endif	
	cString += "</infcompl>"

Return cString
//-----------------------------------------------------------------------
/*/{Protheus.doc} construcao
Função para montar a tag de construção civil do XML de envio de NFS-e ao TSS.

@author Rafael dos Santos Iaquinto
@since 23.12.2015

@param	aConstr		Array contendo dados da construção civil.

@return cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function construcao( aConstr )
	
	local cString	:= ""
	
	
	If Len( aConstr ) >= 2 .And. ( !Empty(aConstr[01]) .Or. !Empty(aConstr[02]) )   
		cString += "<construcao>"
		
			cString += '<codigoobra>'+AllTrim(aConstr[01])+'</codigoobra>'
			cString += '<art>'+AllTrim(aConstr[02])+'</art>'
			//-- Código do encapsulamento de notas dedutoras.	
			cString += If(Len(aConstr) >= 18 .And. !Empty(aConstr[17]), '<numeroEncapsulamento>'+aConstr[18]+'</numeroEncapsulamento>' , "" )
			// -- Alíquota de Dedução relacionada à Construção Civil			
			cString += '<aldedconstcivil></aldedconstcivil>'				
		
		cString += "</construcao>"
	EndIf 
	
return cString


//-----------------------------------------------------------------------
/*/{Protheus.doc} convType
Função para converter qualquer tipo de informação para string.

@author Marcos Taranta
@since 19.01.2012

@param	xValor	Informação a ser convertida.
@param	nTam	Tamanho final da string a ser retornada.
@param	nDec	Número de casa decimais para informações numéricas.

@return	cNovo	Informação em forma de string a ser retornada.
/*/
//-----------------------------------------------------------------------
static function convType( xValor, nTam, nDec )
	
	local	cNovo	:= ""
	
	default	nDec	:= 0
	
	do case
		case valType( xValor ) == "N"
			if xValor <> 0
				cNovo	:= allTrim( str( xValor, nTam, nDec ) )
				cNovo	:= strTran( cNovo, ",", "." )
			else
				cNovo	:= "0"
			endif
		case valType( xValor ) == "D"
			cNovo	:= fsDateConv( xValor, "YYYYMMDD" )
			cNovo	:= subStr( cNovo, 1, 4 ) + "-" + subStr( cNovo, 5, 2 ) + "-" + subStr( cNovo, 7 )
		case valType( xValor ) == "C"
			if nTam == nil
				xValor	:= allTrim( xValor )
			endif
			default	nTam	:= 60
			cNovo := allTrim( encodeUTF8( NoAcento( subStr( xValor, 1, nTam ) ) ) )
	endcase
	
return cNovo

//-----------------------------------------------------------------------
/*/{Protheus.doc} myGetEnd
Função para pegar partes do endereço de uma única string.

@author Marcos Taranta
@since 24.01.2012

@param	cEndereco	String do endereço único.
@param	cAlias		Alias da base.

@return	aRet		Partes separadas do endereço em um array.
/*/
//-----------------------------------------------------------------------
static function myGetEnd( cEndereco, cAlias )
	
	local aRet		:= { "", 0, "", "" }
	
	local cCmpEndN	:= subStr( cAlias, 2, 2 ) + "_ENDNOT"
	local cCmpEst	:= subStr( cAlias, 2, 2 ) + "_EST"
	
	// Campo ENDNOT indica que endereco participante mao esta no formato <logradouro>, <numero> <complemento>
	// Se tiver com 'S' somente o campo de logradouro sera atualizado (numero sera SN)
	if ( &( cAlias + "->" + cCmpEst ) == "DF" ) .Or. ( ( cAlias )->( FieldPos( cCmpEndN ) ) > 0 .And. &( cAlias + "->" + cCmpEndN ) == "1" )
		aRet[1] := cEndereco
		aRet[3] := "SN"
	else
		aRet := fisGetEnd( cEndereco )
	endIf
	
return aRet 

//-----------------------------------------------------------------------
/*/{Protheus.doc} vldIE
Valida IE.

@author Marcos Taranta
@since 24.01.2012

@param	cInsc	IE.
@param	lContr	Caso .F., retorna "ISENTO".

@return	aRet	Retorna a IE.
/*/
//-----------------------------------------------------------------------
Static Function vldIE( cInsc, lContr )
	
	local cRet		:= ""
	
	local nI		:= 1
	
	default lContr	:= .T.
	
	for nI := 1 to len( cInsc )
		if isDigit( subs( cInsc, nI, 1 ) ) .Or. isAlpha( subs( cInsc, nI, 1 ) )
			cRet += subs( cInsc, nI, 1)
		endif
	next
	
	cRet := allTrim( cRet )
	if "ISENT" $ upper( cRet )
		cRet := ""
	endif
	
	if !( lContr ) .And. !empty( cRet )
		cRet := "ISENTO"
	endif
	
return cRet 


//-----------------------------------------------------------------------
/*/{Protheus.doc} UfIBGEUni
Funcao que retorna o codigo da UF do participante, de acordo com a tabela 
disponibilizada pelo IBGE.

@author Simone Oliveira
@since 02.08.2012

@param	cUf 	Sigla da UF do cliente/fornecedor

@return	cCod	Codigo da UF
/*/
//-----------------------------------------------------------------------

Static Function UfIBGEUni (cUf,lForceUF)
Local nX         := 0
Local cRetorno   := ""
Local aUF        := {}

DEFAULT lForceUF := .T.

aadd(aUF,{"RO","11"})
aadd(aUF,{"AC","12"})
aadd(aUF,{"AM","13"})
aadd(aUF,{"RR","14"})
aadd(aUF,{"PA","15"})
aadd(aUF,{"AP","16"})
aadd(aUF,{"TO","17"})
aadd(aUF,{"MA","21"})
aadd(aUF,{"PI","22"})
aadd(aUF,{"CE","23"})
aadd(aUF,{"RN","24"})
aadd(aUF,{"PB","25"})
aadd(aUF,{"PE","26"})
aadd(aUF,{"AL","27"})
aadd(aUF,{"SE","28"})
aadd(aUF,{"BA","29"})
aadd(aUF,{"MG","31"})
aadd(aUF,{"ES","32"})
aadd(aUF,{"RJ","33"})
aadd(aUF,{"SP","35"})
aadd(aUF,{"PR","41"})
aadd(aUF,{"SC","42"})
aadd(aUF,{"RS","43"})
aadd(aUF,{"MS","50"})
aadd(aUF,{"MT","51"})
aadd(aUF,{"GO","52"})
aadd(aUF,{"DF","53"})
aadd(aUF,{"EX","99"})

If !Empty(cUF)
	nX := aScan(aUF,{|x| x[1] == cUF})
	If nX == 0
		nX := aScan(aUF,{|x| x[2] == cUF})
		If nX <> 0
			cRetorno := aUF[nX][1]
		EndIf
	Else
		cRetorno := aUF[nX][2]
	EndIf
Else
	cRetorno := IIF(lForceUF,"",aUF)
EndIf

Return(cRetorno)

//-----------------------------------------------------------------------
/*/{Protheus.doc} Cancela
Função para montar a tag de cancelamento do XML de envio de NFS-e

@author Flavio Luiz Vicco
@since 15.08.2014

@param	cMotCancela	Motivo do cancelamento do documento.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------

User Function nfseXMLCan( cNota, cMotCancela, cCodCanc )

	Local cString := ""
	Default cCodCanc := ""

	// como só Indaiatuba esta pedindo codigo de cancelamento para o restante nao sera levado esse valor como estava no Legado
	// caso queira informar só colocar o codibge no if 
	If  (allTrim( SM0->M0_CODMUN ) $ "3520509-3552205" )
		If Empty(cCodCanc)
			cCodCanc := "2"
		Endif 
	Else 
		cCodCanc := ""
	Endif 

	cString	+= "<rps>"
	cString	+= "<cancelamento>"
	cString += "<cpfcnpj>"    + allTrim( SM0->M0_CGC ) + "</cpfcnpj>"
	cString += "<numeronfse>" + allTrim( cNota ) + "</numeronfse>"
	cString += "<codmunibge>" + allTrim( SM0->M0_CODMUN ) + "</codmunibge>"
	cString += "<motcanc>"    + convType(cMotCancela) + "</motcanc>"
	//-- Existem municipios que fazem varias inscricoes municipais para mesmo CNPJ para controlar cada ramo de atividade.
	cString += "<codmotcanc>"+ cCodCanc + "</codmotcanc>"
	cString += "<inmunprest>" + allTrim( SM0->M0_INSCM ) + "</inmunprest>"
	cString	+= "</cancelamento>"
	cString	+= "</rps>"
	cString := encodeUTF8( cString )

Return cString
//-----------------------------------------------------------------------
/*/{Protheus.doc} DivCem
Função para montar a tag de Aliquota do XML de envio de NFS-e

@author Cleiton Genuino
@since 14.06.2015

@return nValor		    Valor de retorno  da Tag "aliquota"
/*/
//-----------------------------------------------------------------------

Static Function DivCem ( nVP )

Default nVP := 0
//VP	Valor Percentual	Valor percentual da alíquotano formato: 0.0000
//Ex: 1% = 0.01 ; 25,5% = 0.255 ; 100% = 1.0000 ou 1

If nVP > 0
nVP := NOROUND((nVP /100), 4)
Endif


Return nVP

//-----------------------------------------------------------------------
/*/{Protheus.doc} NatPCC
Função que verifica os pontos de inclusão da natureza de operação

@author Cleiton Genuino
@since 31.12.2015

@return aNatPCC	array com ponteiro e Valor da Natureza para compor calculo PCC
/*/
//-----------------------------------------------------------------------

Static Function  NatPCC ( aDest , cNatPCC  )

Local aArea	 := GetArea()
Local aAreaSC5 := SC5->(GetArea())
Local aAreaSD2 := SD2->(GetArea())
Local cNatBusc := ""

Default aDest   := {}
Default cNatPCC := "SA1->A1_NATUREZ"

				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³Posiciona Natureza do pedido                                            ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ				
	dbSelectArea("SC5")
	SC5->( dbSetOrder(1) )

	dbSelectArea("SD2")	
	SD2->( dbSetOrder(3) )
	
	If SD2->( MsSeek( xFilial("SD2") + aDest[23] + aDest[24])) 	 //D2_FILIAL, D2_DOC, D2_SERIE, D2_CLIENTE, D2_LOJA, D2_COD, D2_ITEM,
	          
		If SC5->( MsSeek( xFilial("SC5") + SD2->D2_PEDIDO) )
		
			If SC5->(FieldPos("C5_NATUREZ") > 0 ) .And. !Empty(SC5->C5_NATUREZ)	
				cNatBusc := SC5->C5_NATUREZ
								
			Elseif (len (aDest) > 0 .And. !Empty(aDest[19]) )	
				cNatBusc := SA1->A1_NATUREZ
					
			Elseif !Empty(cNatPCC) .And. cNatPCC $ 'C5_NATUREZ' 
			    If SC5->(FieldPos("C5_NATUREZ") > 0 ) .And. !Empty(SC5->C5_NATUREZ)	
					cNatBusc := SC5->C5_NATUREZ
				Endif
				
			Elseif !Empty(cNatPCC) .And. cNatPCC $ 'A1_NATUREZ'
				cNatBusc:= SA1->A1_NATUREZ
					
		   Endif
		endif
	endif
	
RestArea(aAreaSC5)
RestArea(aAreaSD2)
RestArea(aArea)

return cNatBusc


//-------------------------------------------------------------------
/*/{Protheus.doc} NoAcento
Retira acentos das strings

@author		Cleiton Genuino da Silva
@since		16.12.2016
/*/
//-------------------------------------------------------------------
Static Function NoAcento(cString)
Local cChar  := ""
Local nX     := 0 
Local nY     := 0
Local cVogal := "aeiouAEIOU"
Local cAgudo := "áéíóú"+"ÁÉÍÓÚ"
Local cCircu := "âêîôû"+"ÂÊÎÔÛ"
Local cTrema := "äëïöü"+"ÄËÏÖÜ"
Local cCrase := "àèìòù"+"ÀÈÌÒÙ" 
Local cTio   := "ãõ"
Local cTioMai:= "ÃÕ"
Local cCecid := "çÇ"
Local aCTag := {"&lt;","&gt;",">","<"}

For nX:= 1 To Len(cString)
	cChar:=SubStr(cString, nX, 1)
	IF cChar$cAgudo+cCircu+cTrema+cCecid+cTio+cCrase+cTioMai
		nY:= At(cChar,cAgudo)
		If nY > 0
			cString := StrTran(cString,cChar,SubStr(cVogal,nY,1))
		EndIf
		nY:= At(cChar,cCircu)
		If nY > 0
			cString := StrTran(cString,cChar,SubStr(cVogal,nY,1))
		EndIf
		nY:= At(cChar,cTrema)
		If nY > 0
			cString := StrTran(cString,cChar,SubStr(cVogal,nY,1))
		EndIf
		nY:= At(cChar,cCrase)
		If nY > 0
			cString := StrTran(cString,cChar,SubStr(cVogal,nY,1))
		EndIf		
		nY:= At(cChar,cTio)
		If nY > 0
			cString := StrTran(cString,cChar,SubStr("ao",nY,1))
		EndIf		
		nY:= At(cChar,cTioMai)
		If nY > 0
			cString := StrTran(cString,cChar,SubStr("AO",nY,1))
		EndIf
		
		nY:= At(cChar,cCecid)
		If nY > 0
			cString := StrTran(cString,cChar,SubStr("cC",nY,1))
		EndIf
	Endif
Next

For nX:= 1 To Len (aCTag)
	cString:= strTran( cString, aCTag[nX], "" ) 
Next      

For nX:=1 To Len(cString)
	cChar:=SubStr(cString, nX, 1)
	If Asc(cChar) < 32 .Or. Asc(cChar) > 123 .Or. cChar $ '&'
		cString:=StrTran(cString,cChar,".")
	Endif
Next nX
cString := _NoTags(cString)
Return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} RetTipoLogr
Função que retorna os tipos de logradouro do prestador/tomador

@author Jonatas Almeida
@since 12/06/2019
@version 1.0 

@param	cTexto		Tipo do Logradouro

@return	cTipoLogr	Retorna a descrição do Tipo do Logradouro
/*/
//-----------------------------------------------------------------------
Static Function RetTipoLogr( cTexto )
	local cTipoLogr	:= ""
	local cAbrev	:= ""
	local nX		:= 0
	local nAt		:= 0 
	local aMsg		:= {}

	aadd( aMsg,{ "1", "Av" } )			// Avenida
	aadd( aMsg,{ "2", "Rua" } )			// Rua
	aadd( aMsg,{ "3", "Rod" } )			// Rodovia
	aadd( aMsg,{ "4", "Ruela" } )
	aadd( aMsg,{ "5", "Rio" } )
	aadd( aMsg,{ "6", "Sitio" } )
	aadd( aMsg,{ "7", "Sup Quadra" } )
	aadd( aMsg,{ "8", "Travessa" } )
	aadd( aMsg,{ "9", "Vale" } )
	aadd( aMsg,{ "10","Via" } )			// Via
	aadd( aMsg,{ "11","Vd" } ) 			// Viaduto
	aadd( aMsg,{ "12","Ve" } ) 			// Viela
	aadd( aMsg,{ "13","Vila" } )
	aadd( aMsg,{ "14","Vargem" } )		// Vargem
	aadd( aMsg,{ "15","Al" } )			// Alameda
	aadd( aMsg,{ "16","Pc" } )			// Praça	
	aadd( aMsg,{ "17","Bc" } )			// Beco
	aadd( aMsg,{ "18","Tv" } )			// Travessa
	aadd( aMsg,{ "19","Vel" } )			// Via Elevada
	aadd( aMsg,{ "20","Pq" } )			// Parque
	aadd( aMsg,{ "21","Lg" } )			// Largo
	aadd( aMsg,{ "22","Vep" } )			// Viela Particular
	aadd( aMsg,{ "23","Pa" } )			// Pátio
	aadd( aMsg,{ "24","Ves" } )			// Viela Sanitária
	aadd( aMsg,{ "25","Ld" } )			// Ladeira
	aadd( aMsg,{ "26","Jd" } )			// Jardim
	aadd( aMsg,{ "27","Es" } )			// Estrada
	aadd( aMsg,{ "28","Pte" } )			// Ponte
	aadd( aMsg,{ "29","Rp" } )			// Rua Particular
	aadd( aMsg,{ "30","Praia" } )

	nX := aScan( aMsg,{ | x | UPPER( x[ 2 ] ) $ UPPER( cTexto ) .AND. Len(x[2]) > 3 } )
	
	if( nX == 0 )
		nAt		:= at( " ",UPPER( cTexto ) )
		cAbrev	:= substr( UPPER( cTexto ),1,nAt-1 )
		nX		:= aScan( aMsg,{ | x | UPPER( x[ 2 ] ) == cAbrev } )
	endIf

	if( nX == 0 )
		cTipoLogr := "2"
	else
		cTipoLogr := aMsg[ nX ][ 1 ]
	endIf
return cTipoLogr

//-----------------------------------------------------------------------
/*/{Protheus.doc} getDDDTel
Função para pegar partes do DDD e Telefone de uma única string.

@author Felipe Duarte Luna
@since 24.03.2021

@param	cTelefone	String do Telefone, para extração do DDD e Telefone

@return	cString		Retorna as Tag's DDD + Telefone preenchida respectivamente.
/*/
//-----------------------------------------------------------------------
static function getDDDTel( cTelefone )
	
	Local lVldExc  	  := GetAPOInfo("MATA950.prx")[4] >= Ctod("29/10/2020") 
	Local cString     := ""
	Private aRetGetTel  := {}
		
	Default cTelefone := "" 
	
	aRetGetTel := IIF(lVldExc, fisGetTel( cTelefone,,,.T. ), fisGetTel( cTelefone ) )
	
	// Para obter a correção do 0800, é preciso atualizar o Fonte MATA950.prx que visto que foi realizado a alteração para contemplação a partir do dia 29/10/2020 (ISSUE DSERFIS1-22424)
	If( Type ("aRetGetTel[03]") == "N")
		cString	+= "<ddd>" + allTrim( str( aRetGetTel[2], 3 ) ) + "</ddd>"
		cString	+= "<telefone>" + allTrim( str( aRetGetTel[3], 15 ) ) + "</telefone>"
	ElseIF ( Type("aRetGetTel[03]") == "C" )
		cString += "<ddd>"           + IIF(aRetGetTel[2] == "", '0', substr(aRetGetTel[2], 1, 3)) + "</ddd>"
		cString += "<telefone>"      + IIF(aRetGetTel[3] == "", '0', substr(aRetGetTel[3], 1, 15)) + "</telefone>"
	EndIF
	
return cString 

//-----------------------------------------------------------------------
/*/{Protheus.doc}  Method TssTCInteg

	Função responsável por integrar o TSS com o Configurador de Tributos, classificando
	o tipo de tributação do item da nota fiscal, de acordo com a configuração.

	@param cAliasSD2  Alias da tabela SD2.
	@param lVldExc    Booleano que indica se a classe TSSTCIIntegration existe.
	@param oNfTciIntg Objeto que irá receber a referencia da classe TSSTCIIntegration.
	@return void
	
	@author Felipe Duarte Luna
	@since 11.02.2025
	@version 12.1.2410
/*///-----------------------------------------------------------------------
Static Function TssTCInteg(cAliasSD2, lVldExc, oNfTciIntg)
    Local 	aIdTribs		:= {}
	Local 	recnoSD2		:= 0

	Default oNfTciIntg 		:= nil

    If lVldExc
        recnoSD2 := (cAliasSD2)->(Recno())
        While !(cAliasSD2)->(Eof())
            If !Empty((cAliasSD2)->D2_IDTRIB)
                aAdd(aIdTribs, (cAliasSD2)->D2_IDTRIB)
            EndIf
            (cAliasSD2)->(dbSkip())
        EndDo
        (cAliasSD2)->(DbGoTop())
        (cAliasSD2)->(DbGoTo(recnoSD2))
    EndIf

    If Len(aIdTribs) > 0
        oNfTciIntg := totvs.protheus.backoffice.tss.engine.tributaveis.TSSTCIntegration():New()
        oNfTciIntg:SetInfoNfs(aIdTribs)
    EndIf

Return

//-----------------------------------------------------------------------
/*/{Protheus.doc}  Method DestroyTCI
	Função para destruir o objeto TSSTCIIntegration.

	@author Felipe Duarte Luna
	@since 11.02.2025
	@version 12.1.2410
	@return void
/*///-----------------------------------------------------------------------
Static Function DestroyTCI(oNfTciIntg)
    If ValType(oNfTciIntg) == 'O'
        oNfTciIntg:Destroy()
        oNfTciIntg := Nil
    EndIf
Return

static function IbsCbs( aDest, cCodMun, aNota, cClieFor, cLoja, aEntrega )
    Local cString	    	:= ""
    Local cErro         	:= ""
    Local cAviso        	:= ""
    local cXmlIBSCBS    	:= ""
    Local aArea         	:= GetArea()
	Local cDocumentItemId 	:= ""
	Local lUsaSF3  := GetNewPar("MV_ENVSF3",.F.)

    Default cCodMun	    := ""
    Default cClieFor    := ""
    Default cLoja       := ""
    Default aNota       := {}
    Default aDest	    := {}
    Default aEntrega    := {}

    Private oXmlRefTri := Nil
    Private oXmlIBSCBS := Nil
    
    cDocumentItemId := GetTribID( SF2->F2_DOC, SF2->F2_SERIE, SF2->F2_CLIENTE, SF2->F2_LOJA)
    DbSelectArea("SD2")
    DbSetOrder(3)
    If !Empty(cDocumentItemId) .And. findClass('totvs.protheus.backoffice.tss.engine.xml.taxinformation') .And. DbSeek(xFilial("SD2")+aNota[2]+aNota[1]+cClieFor+cLoja)
        if oNfTciIntg <> Nil
            oXmlRefTri 	:= totvs.protheus.backoffice.tss.engine.xml.taxinformation():New("56")
            cXmlIBSCBS 	:= oXmlRefTri:getXmlIBSCBS(AllTrim(cDocumentItemId), oNfTciIntg)
            oXmlRefTri := FwFreeObj(oXmlRefTri)
            if !empty(cXmlIBSCBS)
                oXmlIBSCBS  := XmlParser("<IBSCBS>"+cXmlIBSCBS+"</IBSCBS>", "_", @cErro, @cAviso)
            endIf
        EndIf
        If type("oXmlIBSCBS") <> "U"
            cString += "<IBSCBS>"
                //Indicador da finalidade da emissão de NFS-e
                cString += "<finNFSe>0</finNFSe>"

                //Indicador da finalidade da emissão de NFS-e:
                //0 - NFS-e regular;
                If type("aDest[27]")<>"U" .and. aDest[27] == "F"
                    cString += "<indFinal>1</indFinal>"
                Else
                    cString += "<indFinal>0</indFinal>"
                EndIf

                //Código indicador da operação de fornecimento, conforme tabela "código indicador de operação"
                IF TYPE("oXmlIBSCBS:_IBSCBS:_CINDOP")<>"U" .AND. !EMPTY(oXmlIBSCBS:_IBSCBS:_CINDOP:TEXT)
                    cString += "<cIndOp>"+oXmlIBSCBS:_IBSCBS:_CINDOP:TEXT+"</cIndOp>"
                ENDIF
                
                //"Código do tipo de Operação (tpOper) não pode ser informado quando não se tratar de uma compra governamental
                // ou um dos serviços da LC 116/2003 listados: 25.05; 15.09; 17.12; 10.05."
                If lUsaSF3 .and. type("aRetSF3[1][3]") <>"U" .and. (SubStr(allTrim(aRetSF3[1][3]),1,4) $ "2505-1509-1712-1005" .OR. ADEST[22] == 'EP')
                    cString += "<tpOper>1</tpOper>" // De onde buscar ? campo opcional
                Elseif !lUsaSF3 .and.  type("aProd[1][32]") <> "U" .and. (SubStr(allTrim(aProd[1][32]),1,4) $ "2505-1509-1712-1005" .OR. ADEST[22] == 'EP')
                    cString += "<tpOper>1</tpOper>" // De onde buscar ? campo opcional
                Endif

                // De onde buscar se NFSE hoje não tem processo de referenciação campo opcional.
                //cString   += '<gRefNFSe>'
                    //cString   += '<refNFSe>'+  +"</refNFSe>"
                //cString   += '</gRefNFSe>'

                //Tipo de ente governamental Para administração pública direta e suas autarquias e fundações: 1 - União; 2 - Estado; 3 - Distrito Federal; 4 - Município;
                IF ADEST[22] == "EP"
                    cString += "<tpEnteGov>1</tpEnteGov>" //Nao existe no Protheus
                ENDIF 

                //A respeito do Destinatário dos serviços: 0 – o destinatário é o próprio tomador/adquirente identificado na NFS-e (tomador = adquirente = destinatário);
                // 1 – o destinatário não é o próprio adquirente, podendo ser outra pessoa, física ou jurídica (ou equiparada), ou um estabelecimento diferente do indicado como tomador (tomador = adquirente ? destinatário)
                If !Empty(aEntrega) .and. aEntrega[1] <> aDest[1]
                    cString += "<indDest>1</indDest>"
                Else
                    cString += "<indDest>0</indDest>"
                EndIf
                
                // <dest> O destinatário só deve ser identificado quando indDest for 1.	
                If !Empty(aEntrega) .and. aEntrega[1] <> aDest[1]
                    cString += IbsCbsDest(aDest, cCodMun)
                EndIf
                
                // bloco Valores
                if type("oXmlIBSCBS") <> "U"
                    cString += IbsCbsValo(oXmlIBSCBS)
                Endif 
            cString += "</IBSCBS>"
            
            oXmlIBSCBS := FwFreeObj(oXmlIBSCBS)
        Endif
    EndIf

    RestArea(aArea)
    aArea := aSize(aArea,0)
	oXmlIBSCBS := Nil
	oXmlRefTri := Nil
	FwFreeObj(oXmlIBSCBS)
    FwFreeObj(oXmlRefTri)

return cString

Static Function IbsCbsDest(aDest, cCodMun)
	Local cString       := ""
    Local cMunIbsDest   := ""
    Local cPaisIso      := ""

    Default aDest   := {}
    Default cCodMun := ""

    If Len(aDest) > 0
        cMunIbsDest   := UfIBGEUni(aDest[09]) + allTrim( aDest[07] )
        cPaisIso      := Tsspais(allTrim(aDest[11]))

        cString += "<dest>"

            If Len(AllTrim(aDest[1])) == 14
                cString += "<CNPJ>" + AllTrim(aDest[1]) + "</CNPJ>"
            ElseIf Len(AllTrim(aDest[1])) == 11
                cString += "<CPF>" + AllTrim(aDest[1]) + "</CPF>"
            ElseIf AllTrim(aDest[9]) == "EX" .And. !Empty(AllTrim(aDest[26]))
                cString += "<NIF>" + AllTrim(aDest[26]) + "</NIF>"
            ElseIf AllTrim(aDest[9]) == "EX"
                cString += "<cNaoNIF>0</cNaoNIF>"  //0 - Não informado na nota de origem; 1 - Dispensado do NIF; 2 - Não exigência do NIF;
            EndIf
            
            cString += "<xNome>" + AllTrim(aDest[2]) + "</xNome>"

            If !Empty(aDest[10])
                cString += "<end>"
                    If (allTrim(aDest[9]) == "EX")
                        cString += "<endExt>"
                            cString += "<cPais>" + AllTrim(cPaisIso) + "</cPais>"
                            cString += "<cEndPost>" + AllTrim(aDest[10]) + "</cEndPost>"
                            cString += "<xCidade>" + AllTrim(aDest[8]) + "</xCidade>"
                            cString += "<xEstProvReg>" + AllTrim(aDest[12]) + "</xEstProvReg>"
                        cString += "</endExt>"
                    Else
                        cString += "<endNac>"
                            If cCodMun $ "5208707" .And. !empty(allTrim(aDest[25]))
                                cMunIbsDest := UfIBGEUni(aDest[09]) + allTrim(aDest[25])
                            EndIf

                            cString += "<cMun>" + AllTrim(cMunIbsDest) + "</cMun>"
                            cString += "<CEP>" + AllTrim(aDest[10]) + "</CEP>"
                        cString += "</endNac>"
                    EndIf

                    cString += "<xLgr>" + AllTrim(ClearTLogr(aDest[3])) + "</xLgr>"
                    cString += "<nro>" + AllTrim(aDest[4]) + "</nro>"

                    If !Empty(aDest[5])
                        cString += "<xCpl>" + AllTrim(aDest[5]) + "</xCpl>"
                    EndIf

                    cString += "<xBairro>" + AllTrim(aDest[6]) + "</xBairro>"
                cString += "</end>"
            EndIf

            If !Empty(allTrim(aDest[13]))
                cString += "<fone>" + AllTrim(aDest[13]) + "</fone>"
            EndIf

            If !Empty(allTrim(aDest[16]))
                cString += "<email>" + AllTrim(aDest[16]) + "</email>"
            EndIf

        cString += "</dest>"
    EndIf

Return cString

Static Function IbsCbsValo(oXmlIBSCBS)
    Local cString   := ""

    Default oXml    := Nil

    cString := "<valores>"
        cString += "<trib>"
            cString += "<gIBSCBS>"
                iF TYPE("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CST")<>"U" .AND. TYPE("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CCLASSTRIB") <> "U"
                    cString += '<CST>'+oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CST:TEXT+'</CST>'
                    cString += '<cClassTrib>'+oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CCLASSTRIB:TEXT+'</cClassTrib>'
                Endif
                If Type("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CCREDPRES") <> "U"
                    cString += '<cCredPres>'+oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CCREDPRES:TEXT+'</cCredPres>'
                EndIf

                If Type("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GTRIBREGULAR") <> "U"
                    cString += "<gTribRegular>"
                        cString += '<CSTReg>'+oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GTRIBREGULAR:_CSTREG:TEXT+'</CSTReg>'
                        cString += '<cClassTribReg>'+oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GTRIBREGULAR:_CCLASSTRIBREG:TEXT+'</cClassTribReg>'
                    cString += "</gTribRegular>"
                EndIf

                //***********************************************************************************************************************************************
                // O conceito de "pagamento adiado" ou diferimento do Imposto sobre Bens e Serviços (IBS) e da Contribuição Social sobre Bens e Serviços (CBS) 
                // está associado a códigos específicos na Tabela de Código de Classificação Tributária do IBS e da CBS (cClassTrib).
                // O código que indica essa situação é o CST-IBS/CBS 500 CST de 500 A 599(Diferimento).
                //***********************************************************************************************************************************************
                If (TYPE("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CST")<>"U" .and.Substr(oXmlIBSCBS:_IBSCBS:_TRIBUTO:_CST:TEXT,1,1)=="5" ) .and. Type("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GCBS:_GDIF:_PDIF") <> "U" .and. Type("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GIBSMUN:_GDIF:_PDIF") <> "U" .and. Type("oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GIBSUF:_GDIF:_PDIF") <> "U" 
                    cString += "<gDif>"
                        cString += "<pDifUF>"+ConvType(val(oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GIBSUF:_GDIF:_PDIF:TEXT),15,2)+"</pDifUF>"
                        cString += "<pDifMun>"+ConvType(val(oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GIBSMUN:_GDIF:_PDIF:TEXT),15,2)+"</pDifMun>"
                        cString += '<pDifCBS>'+ConvType(val(oXmlIBSCBS:_IBSCBS:_TRIBUTO:_GIBSCBS:_GCBS:_GDIF:_PDIF:TEXT),15,2)+'</pDifCBS>'
                    cString += "</gDif>"
                EndIf

            cString += "</gIBSCBS>"
        cString += "</trib>"
    cString += "</valores>"

Return cString


Static Function GetTribID( cDoc, cSerie, cCliente, cLoja )
Local cQuery	 := ""
Local cAliasSD2  := "SD2"
Local cIdTrib    := ""

Default cDoc	:= ""
Default cSerie	:= ""
Default cCliente:= ""
Default cLoja	:= ""

If oQryIdTrib == Nil
    cQuery += "SELECT D2_FILIAL,D2_SERIE,D2_DOC,D2_CLIENTE,D2_LOJA,D2_COD,D2_TES,D2_TIPO,D2_ITEM,D2_CF, "
    cQuery += "D2_IDTRIB  FROM " + RetSqlName('SD2') + " SD2 "
    cQuery += "WHERE SD2.D2_FILIAL= ? AND SD2.D2_DOC = ? AND SD2.D2_SERIE = ? AND SD2.D2_CLIENTE = ? AND SD2.D2_LOJA = ? AND SD2.D_E_L_E_T_ = ? "
    cQuery += "ORDER BY D2_FILIAL, D2_DOC, D2_SERIE, D2_CLIENTE, D2_LOJA, D2_COD, D2_ITEM"

    oQryIdTrib	:= FwExecStatement():New(ChangeQuery(cQuery))
EndIf

oQryIdTrib:SetString(1, xFilial("SD2") )
oQryIdTrib:SetString(2, cDoc)
oQryIdTrib:SetString(3, cSerie)
oQryIdTrib:SetString(4, cCliente)
oQryIdTrib:SetString(5, cLoja)
oQryIdTrib:SetString(6,Space(1))
cAliasSD2 := oQryIdTrib:OpenAlias()
cQuery    := oQryIdTrib:getFixQuery()

While (cAliasSD2)->(!eof())
    If !Empty((cAliasSD2)->D2_IDTRIB)
        cIdTrib := (cAliasSD2)->D2_IDTRIB
        Exit
    EndIf
    (cAliasSD2)->(DbSkip())
Enddo

(cAliasSD2)->( DbCloseArea() ) 

Return cIdTrib

static Function Tsspais(cCodBacen)


Local cRetorno	:= ""

Local nPosBacen	:= 0

Local aBacen		:= {} 

Default cCodMun	:= ""
Default cCodBacen	:= ""


aadd(aBacen,{"00132","AFEGANISTAO","AF"})
aadd(aBacen,{"00175","ALBANIA","AL"})
aadd(aBacen,{"00230","ALEMANHA","DE"})
aadd(aBacen,{"00310","BURKINA FASO","BF"})
aadd(aBacen,{"00370","ANDORRA","AD"})
aadd(aBacen,{"00400","ANGOLA","AO"})
aadd(aBacen,{"00418","ANGUILLA","AI"})
aadd(aBacen,{"00434","ANTIGUA E BARBUDA","AG"})
aadd(aBacen,{"00477","ANTILHAS HOLANDESAS","NA"})
aadd(aBacen,{"00531","ARABIA SAUDITA","AS "})
aadd(aBacen,{"00590","ARGELIA","DZ"})
aadd(aBacen,{"00639","ARGENTINA","AR"})
aadd(aBacen,{"00647","ARMENIA","AM"})
aadd(aBacen,{"00655","ARUBA","AW"})
aadd(aBacen,{"00698","AUSTRALIA","AU"})	
aadd(aBacen,{"00728","AUSTRIA","AT"})
aadd(aBacen,{"00736","AZERBAIJAO","AZ"})		
aadd(aBacen,{"00779","BAHAMAS","BS"})
aadd(aBacen,{"00809","BAHREIN","BH"})
aadd(aBacen,{"00817","BANGLADESH","BD"})
aadd(aBacen,{"00833","BARBADOS","BB"})
aadd(aBacen,{"00850","BELARUS","BY"})
aadd(aBacen,{"00876","BELGICA","BE"})
aadd(aBacen,{"00884","BELIZE","BZ"})
aadd(aBacen,{"00906","BERMUDAS","BM"})
aadd(aBacen,{"00930","MIANMAR",""})
aadd(aBacen,{"00973","BOLIVIA","BO"})
aadd(aBacen,{"00981","BOSNIA HERZEGOVINA","BA "})	
aadd(aBacen,{"01015","BOTSUANA","BW"}) 
aadd(aBacen,{"01058","BRASIL","BR"})
aadd(aBacen,{"01082","BRUNEI","BN"})
aadd(aBacen,{"01112","BULGARIA","BG"})
aadd(aBacen,{"01155","BURUNDI","BI"})
aadd(aBacen,{"01198","BUTAO","BT"})
aadd(aBacen,{"01279","CABO VERDE","CV"}) 	 
aadd(aBacen,{"01376","CAYMAN","KY"})
aadd(aBacen,{"01414","CAMBOJA","KH"})
aadd(aBacen,{"01457","CAMAROES","CM"})	
aadd(aBacen,{"01490","CANADA","CA"}) 
aadd(aBacen,{"01504","GUERNSEY",""})
aadd(aBacen,{"01508","JERSEY",""})
aadd(aBacen,{"01511","CANARIAS",""})	 
aadd(aBacen,{"01538","CAZAQUISTAO","KZ"})
aadd(aBacen,{"01546","CATAR","QA"})
aadd(aBacen,{"01589","CHILE","CL"})
aadd(aBacen,{"01600","CHINA","CN"})
aadd(aBacen,{"01619","FORMOSA","TW"})
aadd(aBacen,{"01635","CHIPRE","CY"})
aadd(aBacen,{"01651","COCOS","CC"})
aadd(aBacen,{"01694","COLOMBIA","CO"})
aadd(aBacen,{"01732","COMORES","KM"})
aadd(aBacen,{"01775","CONGO","CG"})
aadd(aBacen,{"01830","COOK","CK"})
aadd(aBacen,{"01872","COREIA","KP"})
aadd(aBacen,{"01902","COREIA DO SUL","KR"})
aadd(aBacen,{"01937","COSTA DO MARFIM","CI"})		
aadd(aBacen,{"01953","CROACIA","HR"})
aadd(aBacen,{"01961","COSTA RICA","CR"})
aadd(aBacen,{"01988","COVEITE",""})
aadd(aBacen,{"01996","CUBA","CU"})
aadd(aBacen,{"02291","BENIN","BJ"})
aadd(aBacen,{"02321","DINAMARCA","DK"})
aadd(aBacen,{"02356","DOMINICA","DM"})
aadd(aBacen,{"02399","EQUADOR","EC"})
aadd(aBacen,{"02402","EGITO","EG"})
aadd(aBacen,{"02437","ERITREIA","ER"})
aadd(aBacen,{"02445","EMIRADOS ARABES UNIDOS","AE"})	
aadd(aBacen,{"02453","ESPANHA","ES"})
aadd(aBacen,{"02461","ESLOVENIA","SI"})
aadd(aBacen,{"02470","ESLOVAQUIA","SK"})
aadd(aBacen,{"02496","ESTADOS UNIDOS","US"})
aadd(aBacen,{"02518","ESTONIA","EE"})
aadd(aBacen,{"02534","ETIOPIA","ET"})
aadd(aBacen,{"02550","FALKLAND","FK"})
aadd(aBacen,{"02593","FEROE",""})
aadd(aBacen,{"02674","FILIPINAS","PH"})
aadd(aBacen,{"02712","FINLANDIA","FI"})
aadd(aBacen,{"02755","FRANCA","FR"})
aadd(aBacen,{"02810","GABAO","GA"})
aadd(aBacen,{"02852","GAMBIA","GM"})
aadd(aBacen,{"02895","GANA","GH"})
aadd(aBacen,{"02917","GEORGIA","GE"})
aadd(aBacen,{"02933","GIBRALTAR","GI"})
aadd(aBacen,{"02976","GRANADA",""})
aadd(aBacen,{"03018","GRECIA","GR"})
aadd(aBacen,{"03050","GROENLANDIA","GL"})
aadd(aBacen,{"03093","GUADALUPE","GP"})
aadd(aBacen,{"03131","GUAM","GU"})
aadd(aBacen,{"03174","GUATEMALA","GT"})
aadd(aBacen,{"03255","GUIANA FRANCESA","GF"})
aadd(aBacen,{"03298","GUINE","GN"})
aadd(aBacen,{"03310","GUINE-EQUATORIAL","GQ"})
aadd(aBacen,{"03344","GUINE-BISSAU","GW"})
aadd(aBacen,{"03379","GUIANA","GY"})
aadd(aBacen,{"03417","HAITI","HT"})
aadd(aBacen,{"03450","HONDURAS","HN"})
aadd(aBacen,{"03514","HONG KONG","HK"})
aadd(aBacen,{"03557","HUNGRIA","HU"})
aadd(aBacen,{"03573","IEMEN","YE"})
aadd(aBacen,{"03595","MAN","IM"})
aadd(aBacen,{"03611","INDIA","IN"})
aadd(aBacen,{"03654","INDONESIA","ID"})
aadd(aBacen,{"03697","IRAQUE","IQ"})
aadd(aBacen,{"03727","IRA","IR"})
aadd(aBacen,{"03751","IRLANDA","IE"})
aadd(aBacen,{"03794","ISLANDIA","IS"})
aadd(aBacen,{"03832","ISRAEL","IL"})
aadd(aBacen,{"03867","ITALIA","IT"})
aadd(aBacen,{"03913","JAMAICA","JM"})
aadd(aBacen,{"03964","JOHNSTON",""})
aadd(aBacen,{"03999","JAPAO","JP"})
aadd(aBacen,{"04030","JORDANIA","JO"})
aadd(aBacen,{"04111","KIRIBATI","KI"})
aadd(aBacen,{"04200","LAOS","LA"})
aadd(aBacen,{"04235","LEBUAN",""})
aadd(aBacen,{"04260","LESOTO","LS"})
aadd(aBacen,{"04278","LETONIA","LV"})
aadd(aBacen,{"04316","LIBANO","LB"})
aadd(aBacen,{"04340","LIBERIA","LR"})
aadd(aBacen,{"04383","LIBIA","LY"})
aadd(aBacen,{"04405","LIECHTENSTEIN","LI"})		
aadd(aBacen,{"04421","LITUANIA","LT"})
aadd(aBacen,{"04456","LUXEMBURGO","LU"})
aadd(aBacen,{"04472","MACAU","MO"})
aadd(aBacen,{"04499","MACEDONIA","MK"})
aadd(aBacen,{"04502","MADAGASCAR","MG"})
aadd(aBacen,{"04525","MADEIRA",""})
aadd(aBacen,{"04553","MALASIA","MY"})
aadd(aBacen,{"04588","MALAVI",""})
aadd(aBacen,{"04618","MALDIVAS","MV"})
aadd(aBacen,{"04642","MALI","ML"})
aadd(aBacen,{"04677","MALTA","MT"})
aadd(aBacen,{"04723","MARIANAS DO NORTE","MP"})
aadd(aBacen,{"04740","MARROCOS","MA"})
aadd(aBacen,{"04766","MARSHALL","MH"})
aadd(aBacen,{"04774","MARTINICA","MQ"})	
aadd(aBacen,{"04855","MAURICIO","MU"})
aadd(aBacen,{"04880","MAURITANIA","MR"})
aadd(aBacen,{"04885","MAYOTTE","YT"})		
aadd(aBacen,{"04901","MIDWAY",""})
aadd(aBacen,{"04936","MEXICO","MX"})
aadd(aBacen,{"04944","MOLDAVIA","MD"})
aadd(aBacen,{"04952","MONACO","MC"})
aadd(aBacen,{"04979","MONGOLIA","MN"})
aadd(aBacen,{"04985","MONTENEGRO",""})
aadd(aBacen,{"04995","MICRONESIA","FM"})
aadd(aBacen,{"05010","MONTSERRAT","MS"})
aadd(aBacen,{"05053","MOCAMBIQUE","MZ"})
aadd(aBacen,{"05070","NAMIBIA","NA"})
aadd(aBacen,{"05088","NAURU","NR"})
aadd(aBacen,{"05118","CHRISTMAS","CX"})
aadd(aBacen,{"05177","NEPAL","NP"})
aadd(aBacen,{"05215","NICARAGUA","NI"})
aadd(aBacen,{"05258","NIGER","NE"})
aadd(aBacen,{"05282","NIGERIA","NG"})		 
aadd(aBacen,{"05312","NIUE","NU"})
aadd(aBacen,{"05355","NORFOLK","NF"})
aadd(aBacen,{"05380","NORUEGA","NO"})
aadd(aBacen,{"05428","NOVA CALEDONIA","NC"})
aadd(aBacen,{"05452","PAPUA NOVA GUINE","PG"})
aadd(aBacen,{"05487","NOVA ZELANDIA","NZ"})
aadd(aBacen,{"05517","VANUATU","VU"})
aadd(aBacen,{"05568","OMA","OM"})
aadd(aBacen,{"05665","PACIFICO",""})
aadd(aBacen,{"05738","PAISES BAIXOS",""})
aadd(aBacen,{"05754","PALAU","PW"})
aadd(aBacen,{"05762","PAQUISTAO","PK"})
aadd(aBacen,{"05780","PALESTINA","PS"})
aadd(aBacen,{"05800","PANAMA","PA"})
aadd(aBacen,{"05860","PARAGUAI","PY"})
aadd(aBacen,{"05894","PERU","PE"})
aadd(aBacen,{"05932","PITCAIRN","PN"})
aadd(aBacen,{"05991","POLINESIA FRANCESA","PF"})
aadd(aBacen,{"06033","POLONIA","PL"})
aadd(aBacen,{"06076","PORTUGAL","PT"})
aadd(aBacen,{"06114","PORTO RICO","PR"})
aadd(aBacen,{"06238","QUENIA","KE"})
aadd(aBacen,{"06254","QUIRGUIZ",""})
aadd(aBacen,{"06289","REINO UNIDO","UK"})
aadd(aBacen,{"06408","REPUBLICA CENTRO-AFRICANA","CF"})
aadd(aBacen,{"06475","REPUBLICA DOMINICANA","DO"})
aadd(aBacen,{"06602","REUNIAO","RE"})
aadd(aBacen,{"06653","ZIMBABUE","ZW"})
aadd(aBacen,{"06700","ROMENIA","RO"})	
aadd(aBacen,{"06750","RUANDA","RW"})
aadd(aBacen,{"06769","RUSSIA","RU"})
aadd(aBacen,{"06777","SALOMAO","SB"})
aadd(aBacen,{"06858","SAARA OCIDENTAL","EH"})
aadd(aBacen,{"06874","EL SALVADOR","SV"})
aadd(aBacen,{"06904","SAMOA","WS"})
aadd(aBacen,{"06912","SAMOA AMERICANA","AS"})
aadd(aBacen,{"06955","SAO CRISTOVAO E NEVES","KN"})
aadd(aBacen,{"06971","SAN MARINO","SM"})
aadd(aBacen,{"07005","SAO PEDRO E MIQUELON","PM"})
aadd(aBacen,{"07056","SAO VICENTE E GRANADINAS","VC"})
aadd(aBacen,{"07102","SANTA HELENA","SH"})
aadd(aBacen,{"07153","SANTA LUCIA","LC"})
aadd(aBacen,{"07200","SAO TOME E PRINCIPE","ST"})
aadd(aBacen,{"07285","SENEGAL","SN"})
aadd(aBacen,{"07315","SEYCHELLES","SC"})
aadd(aBacen,{"07358","SERRA LEOA","SL"})
aadd(aBacen,{"07370","SERVIA","RS"})
aadd(aBacen,{"07412","CINGAPURA","SG"})
aadd(aBacen,{"07447","SIRIA","SY"})
aadd(aBacen,{"07480","SOMALIA","SO"})
aadd(aBacen,{"07501","SRI LANKA","LK"})
aadd(aBacen,{"07544","SUAZILANDIA","SZ"})
aadd(aBacen,{"07560","AFRICA DO SUL","ZA"})
aadd(aBacen,{"07595","SUDAO","SD"})
aadd(aBacen,{"07600","SUDAO DO SUL","SD"})
aadd(aBacen,{"07641","SUECIA","SE"})
aadd(aBacen,{"07676","SUICA","CH"})
aadd(aBacen,{"07706","SURINAME","SR"})
aadd(aBacen,{"07722","TADJIQUISTAO",""})	
aadd(aBacen,{"07765","TAILANDIA","TH"})
aadd(aBacen,{"07803","TANZANIA","TZ"})
aadd(aBacen,{"07820","TERRITORIO","IO"})
aadd(aBacen,{"07838","DJIBUTI","DJ"})
aadd(aBacen,{"07889","CHADE","TD"})
aadd(aBacen,{"07919","TCHECA","CZ"})
aadd(aBacen,{"07951","TIMOR LESTE","TP"})
aadd(aBacen,{"08001","TOGO","TG"})
aadd(aBacen,{"08052","TOQUELAU",""})
aadd(aBacen,{"08109","TONGA","TO"})
aadd(aBacen,{"08150","TRINIDAD E TOBAGO","TT"})
aadd(aBacen,{"08206","TUNISIA","TN"})
aadd(aBacen,{"08230","TURCAS E CAICOS","TC"})
aadd(aBacen,{"08249","TURCOMENISTAO","TM"})
aadd(aBacen,{"08273","TURQUIA","TR"})
aadd(aBacen,{"08281","TUVALU",""})
aadd(aBacen,{"08311","UCRANIA","UA"})
aadd(aBacen,{"08338","UGANDA","UG"})
aadd(aBacen,{"08451","URUGUAI","UY"})
aadd(aBacen,{"08478","UZBEQUISTAO","UZ"})
aadd(aBacen,{"08486","VATICANO","VA"})
aadd(aBacen,{"08508","VENEZUELA","VE"})
aadd(aBacen,{"08583","VIETNA","VN"})
aadd(aBacen,{"08630","VIRGENS - BRITANICAS","VG"})
aadd(aBacen,{"08664","VIRGENS - EUA","VI"})
aadd(aBacen,{"08702","FIJI","FJ"})
aadd(aBacen,{"08737","WAKE",""})
aadd(aBacen,{"08885","CONGO","CG"})
aadd(aBacen,{"08907","ZAMBIA","ZM"})
aadd(aBacen,{"08958","ZONA DO CANAL DO PANAMA",""})
aadd(aBacen,{"09903","PROVISAO DE NAVIOS E AERONAVES",""})
aadd(aBacen,{"09946","A DESIGNAR",""})
aadd(aBacen,{"09950","BANCOS CENTRAIS",""})
aadd(aBacen,{"09970","ORGANIZACOES INTERNACIONAIS",""})

If !Empty(cCodBacen)
	
	// Verifica pelo código do País
	If Len (cCodBacen) <= 5
	    cCodBacen := StrZero(Val(cCodBacen),5)
		nPosBacen := aScan(aBacen,{|x| x[1] == cCodBacen})
			If nPosBacen > 0
				cRetorno := aBacen[nPosBacen][3]				
			EndIf			
	Else
		// Verifica pelo nome do País
		nPosBacen := aScan(aBacen,{|x| x[2] == cCodBacen})
		If nPosBacen > 0
			cRetorno := aBacen[nPosBacen][3]				
		EndIf			

	Endif	

	If Empty(cRetorno)
		cRetorno := 'ZZ' // Código para Países não especificados
	EndIf

Endif
Return(cRetorno)

Static Function ClearTLogr(cLogradour)

Local cTipoLogr		:= ""
Local LlimpLog	:= SuperGetMV("MV_TIPLOGR",.F.,.F.) // Parâmetro para determinar se retira o tipo do logradouro do endereço.
                                
if !Empty(cLogradour)
	cTipoLogr:= RetTipoLogr(cLogradour)
endif 

If !Empty(cTipoLogr) .AND.  LlimpLog
	Do Case
		Case cTipoLogr == "1" // Avenida
			cTipoLogr := "Av "
		Case cTipoLogr == "2" // Rua
			cTipoLogr := "Rua "			
		Case cTipoLogr == "3" // Rodovia
			cTipoLogr := "Rod "	
		Case cTipoLogr == "4" // Ruela
			cTipoLogr := "Ruela "		
		Case cTipoLogr == "5" //Rio
			cTipoLogr := "Rio "		
		Case cTipoLogr == "6" //Sitio
			cTipoLogr := "Sitio "	
		Case cTipoLogr == "7" //Sup Quadr
			cTipoLogr := "Sup Quadra "		
		Case cTipoLogr == "8" //Travessa
			cTipoLogr := "Travessa "	
		Case cTipoLogr == "9" //Vale
			cTipoLogr := "Vale "	
		Case cTipoLogr == "10" // Via
			cTipoLogr := "Via "	
		Case cTipoLogr == "11" // Viaduto
			cTipoLogr := "Vd "		
		Case cTipoLogr == "12" // Viela
			cTipoLogr := "Vie "	
		Case cTipoLogr == "13" // Vila
			cTipoLogr := "Vila "	
		Case cTipoLogr == "14" //Vargem
			cTipoLogr := "Vargem "
		Case cTipoLogr == "15" // Alameda
			cTipoLogr := "Al "
		Case cTipoLogr == "16" // Praça
			cTipoLogr := "Pc "
		Case cTipoLogr == "17" // Beco
			cTipoLogr := "Bc "
		Case cTipoLogr == "18" // Travessa
			cTipoLogr := "Tv "
		Case cTipoLogr == "19" // Via Elevada
			cTipoLogr := "Vel "
		Case cTipoLogr == "20" // Parque
			cTipoLogr := "Pq "	
		Case cTipoLogr == "21" // Largo
			cTipoLogr := "Lg "	
		Case cTipoLogr == "22" // Viela Particular
			cTipoLogr := "Vep "	
		Case cTipoLogr == "23" // Pátio
			cTipoLogr := "Pa "
		Case cTipoLogr == "24" // Viela Sanitária
			cTipoLogr := "Ves "
		Case cTipoLogr == "25" // Ladeira
			cTipoLogr := "Ld "
		Case cTipoLogr == "26" // Jardim
			cTipoLogr := "Jd "
		Case cTipoLogr == "27" // Estrada
			cTipoLogr := "Es "
		Case cTipoLogr == "28" // Ponte
			cTipoLogr := "Pte "
		Case cTipoLogr == "29" // Rua Particular
			cTipoLogr := "Rp "
		Case cTipoLogr == "30" // Praia
			cTipoLogr := "Praia "
			
	EndCase

	cLogradour:= StrTran(cLogradour,'.',"")
	cLogradour:= StrTran(cLogradour,cTipoLogr,"")
	cLogradour:= StrTran(cLogradour,Upper(cTipoLogr),"")
	cLogradour:= StrTran(cLogradour,Lower(cTipoLogr),"")
	
endif

return(cLogradour)
