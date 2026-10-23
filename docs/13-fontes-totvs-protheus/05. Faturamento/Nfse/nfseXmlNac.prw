#include "protheus.ch" 
#include "tbiconn.ch"
#include "fwlibversion.ch"

Static oQryFltDoc 	:= NIL as object
Static oQryIdTrib 	:= NIL as object

//-----------------------------------------------------------------------
/*/{Protheus.doc} nfseXmlNac
Função que monta o .XML Layout NFS-e Nacional de envio ao TSS.

@param	cCodMun		Código do Município
@param	cTipo		Tipo do documento.
@param	dDtEmiss	Data de emissão do documento.
@param	cSerie		Serie do documento.
@param	cNota		Número do documento.
@param	cTpAmb		Tipo do Ambiente para Transmissão da NFS-e Nacional
@param	cClieFor	Cliente/Fornecedor do documento.
@param	cLoja		Loja do cliente/fornecedor do documento.
@param	cMotCancela	Motivo do cancelamento do documento.

@return	cString		Tag montada em forma de string.

@author Felipe Duarte Luna
@since 23.10.2023
@version 12.12210

/*/
//-----------------------------------------------------------------------
user function nfseXmlNac( cTipo, dDtEmiss, cSerie, cNota, cClieFor, cLoja, cMotCancela,aAIDF,cCodcanc,cAmbiente)

Local cString     := '<?xml version="1.0" encoding="UTF-8"?>'
Local dNfseNacIBS  := SuperGetMv('MV_RTC56',.f.,stod('20260101'))//CTOD("01/01/2026") DSERTSS1-31849

//Private cCondPag  := "" // Condição de pagamento E4_COND
//Private nX        := 0
//Private nW		:= 0
//Private nZ		:= 0
//Private cString    := ""
        
Private cAliasSE1  := "SE1"
Private cAliasSD2  := "SD2"
Private cCFPS      := ""
Private cNatOper   := ""
Private cModFrete  := ""
Private cScan      := ""
Private cEspecie   := ""
Private cMensCli   := ""
Private cMensFis   := ""
Private cNFe       := ""
Private cMV_LJTPNFE:= SuperGetMV("MV_LJTPNFE", ," ")
Private cMVSUBTRIB := IIf(FindFunction("GETSUBTRIB"), GetSubTrib(), SuperGetMv("MV_SUBTRIB"))
Private cLJTPNFE	 := ""
Private cLJPRF	 :=	SuperGetMv("MV_LJPREF", ," ")
Private cWhere	 := ""
Private cMunISS	 := ""
Private cTipoPcc   := "PIS','COF','CSL','CF-','PI-','CS-"
Private cTipoRet   := "IR-"
Private cCodCli 	 := ""
Private cLojCli 	 := "" 
Private cDescMunP	 := ""
Private cMunPSIAFI := ""
Private cMunPrest  := ""
Private cDescrNFSe := ""
Private cDiscrNFSe := ""
Private cField     := "" 
Private cFieldMsg  := ""
Private cTpPessoa	 := ""
Private cUFxIss	 := ""
Private cMunxISS	 := ""
Private lMvNFSEIR	 := SuperGetMV("MV_NFSEIR", .F., .F.) // Pramentro para buscar o IRRF gravado n SD2 e não considerar apenas o acumulado
Private lMvNFSEINSS:= SuperGetMV("MV_NFSEINS", .F., .F.) // Paramentro para buscar o INSS gravado na SD2 e não considerar apenas o acumulado
Private lTssPref	 :=	GetNewPar("MV_TSSPREF",.F. ) // Se definido com .T. faz a busca das Dupl. utilizando Prefixo da SF2 na SE1 SE1.E1_NUM = %Exp:SF2->F2_DUPL% AND -- se nao definido o que vale é a analise feita no parametro MV_LJPREF 

Private aObra		 := &(SuperGetMV("MV_XMLOBRA", ,"{,,,,,,,,,,,,,,}"))
Private cLogradOb  := "" //Logradouro para Obra
Private cCompleOb  := "" //Complemento para obra
Private cNumeroOb  := "" // Numero para Obra
Private cBairroOb  := "" // Bairro para Obra
Private cCepOb     := "" // Cep para Obra
Private cCodMunob  := "" // Cod do Municipio para Obra
Private cNomMunOb	 := "" // Nome do municipio para Obra
Private cUfOb		 := "" // UF para Obra
Private cCodPaisOb := "" // Codigo do Pais para Obra
Private cNomPaisOb := "" // Nome do Pais para Obra
Private cNumArtOb  := "" // Numero Art para Obra
Private cNumCeiOb  := "" // Numero CEI para Obra
Private cNumProOb  := "" // Numero Projeto para Obra
Private cNumMatOb  := "" // Numero de Mtricula para Obra
Private cNumEncap  := "" // NumeroEncapsulamento
Private cInsMunObr := "" // Inscrição Municipal da Obra
Private cCodSerObr := "" // Codigo de Serviço da Obra
Private cNatPCC	 := GetNewPar("MV_1DUPNAT","SA1->A1_NATUREZ") //-- Natureza considerada para retencao de PIS, COF, CSLL 
Private cFntCtrb	 := ""
Private cCondPag   := "" // Condição de pagamento E4_COND
Private cObsDtc	 := "" // Observacao DTC TMS
Private cCST_SFT	 := "" // Codigo CST para ISS (FT_CSTISS)
Private cOrigemSB1 := "" // Codigo Origem do Produto (B1_ORIGEM)
Private cMsgSX5	 := ""
    
Private dDateCom 	:= Date()	
    
Private nRetPis	:= 0
Private nRetCof	:= 0
Private nRetCsl	:= 0
Private nPosI		:= 0
Private nPosF	    := 0
Private nAliq	    := 0
Private nCont		:= 0
Private nDescon	:= 0
Private nScan		:= 0
Private nRetDesc	:= 0
Private nValTotPrd := 0

Private lQuery    := .F.
Private lCalSol	:= .F.
Private lEECFAT	:= SuperGetMv("MV_EECFAT")
Private lNatOper  := GetNewPar("MV_NFESERV","1") == "1"
Private lAglutina := AllTrim(GetNewPar("MV_ITEMAGL","N")) == "S"
Private lNFeDesc  := GetNewPar("MV_NFEDESC",.F.)
Private lNfsePcc  := GetNewPar("MV_NFSEPCC",.F.)	
Private lRecIrrf  := .T.
Private lTitIrrf  := .F.
Private lLJPRF	:= .T.
Private lUsaSF3  := GetNewPar("MV_ENVSF3",.F.)
Private aNota     := {}
Private aDupl     := {}
Private aDest     := {}
Private aEntrega  := {}
Private aProd     := {}
Private aICMS     := {}
Private aICMSST   := {}
Private aIPI      := {}
Private aPIS      := {"  ",0,0,0,0,0} //apuracao pis
Private aCOFINS   := {"  ",0,0,0,0,0} //apuracao cofins
Private aPISST    := {}
Private aCOFINSST := {}
Private aISSQN    := {}
Private aISS      := {}
Private aCST      := {}
Private aRetido   := {}
Private aTransp   := {}
Private aVeiculo  := {}
Private aReboque  := {}
Private aEspVol   := {}
Private aNfVinc   := {}
Private aPedido   := {}
Private aTotal    := {0,0,""}
Private aOldReg   := {}
Private aOldReg2  := {}
Private aMed		:= {}
Private aArma		:= {}
Private aveicProd	:= {}
Private aIEST		:= {}
Private aDI		:= {}
Private aAdi		:= {}
Private aExp		:= {}
Private aDeducao  := {} 
Private aDeduz	:= {}
Private aConstr	:= {}
Private aInterm	:= {}
Private aRetISS	:= {}
Private aRetPIS	:= {}
Private aRetCOF	:= {}
Private aRetCSL	:= {}
Private aRetIRR	:= {}
Private aRetINS	:= {}
Private aLeiTrp	:= {}
Private aRetSX5	:= {}
Private aRetSF3	:= {}
Private aBaspis	:= {} 
Private aBasCof	:= {}
Private aBasCsll	:= {}
Private aBasIRR	:= {}
Private aBasINS	:= {}
Private nCamPrcv  := TamSx3("D2_PRCVEN")[2]	//casa decimal do campo D2_PRCVEN
Private nCamQuan  := TamSx3("D2_QUANT")[2]	//casa decimal do campo D2_QUANT 
Private nCamTot   := TamSx3("D2_TOTAL")[2]	//casa decimal do campo D2_TOTAL
Private lIntegHtl := SuperGetMv("MV_INTHTL",, .F.) //Integracao via Mensagem Unica - Hotelaria
    
//Private aUF     	:= {}         
Private cMvMsgTrib	:= SuperGetMV("MV_MSGTRIB",,"1")
Private lDuplLiq	:= SuperGetMV("MV_DUPLLIQ",,.F.)
Private cMvFntCtrb	:= SuperGetMV("MV_FNTCTRB",," ")
Private cMvFisCTrb	:= SuperGetMV("MV_FISCTRB",,"1")     
Private lCrgTrib 	:= GetNewPar("MV_CRGTRIB",.F.)	
Private lMvEnteTrb	:= SuperGetMV("MV_ENTETRB",,.F.)	// Valor dos tributos por Ente Tributante: Federal, Estadual e Municipal
Private lMvded		:= SuperGetMV("MV_NFSEDED",,.F.)	// Habilita/Desabilita as Deducoes da NFSE
Private lMvred		:= SuperGetMV("MV_NFSERED",,.F.)	// Habilita/Desabilita as Reducoes da NFSE
Private lMvDescInc	:= SuperGetMV("MV_NFSEDIN",,.F. )	// Habilita/Desabilita os Descontos Incondicionados da NFSE
Private cCamSC5		:= SuperGetMV( "MV_NFSECOM",.F.,"" ) // Parametro que aponta para o campo do SC5 com a data da competencia
Private lMvIssxMun	:= SuperGetMV("MV_ISSXMUN",,.F. )	// Habilita/Desabilita Tratamento de ISS por Município, via rotina /FISA052
Private lIntTur		:= SuperGetMV("MV_INTTUR",,.F.)
Private lJescTur	:= SuperGetMV("MV_JESCJUR",, .F.) // Integração com módulo SIGAPFS
Private cNfsTRec	:= superGetMV("MV_NFSTREC",.F.,"" )
Private cCpmUsr		:= GetMV("MV_CMPUSR")
Private cSigamat	:= ""
Private cCidCob		:= ""
Private cIDEnt		:= ""
Private cCgc		:= ""
Private cEstCob		:= ""

Private cTpCliente	:= ""

Private nAbatim 	:= 0
Private nTotalCrg	:= 0
Private nTotFedCrg	:= 0	// Ente Tributante Federal
Private nTotEstCrg	:= 0	// Ente Tributante Estadual
Private nTotMunCrg	:= 0	// Ente Tributante Municipal
private nCountSF3	:= 0
Private lRetPisCof  := .F.
Private cQuery	    := ""
Private lVldExc  	:= FindClass("totvs.protheus.backoffice.tss.engine.tributaveis.TSSTCIntegration")
Private lConfTrib	:= .F.
Private lDescCond   := .F.
Private oNfTciIntg  :=  NIL as object
Private oISSCfg    	as JsonObject
Private lConfTrIss  := .T. // se iss é ou nao do configurador 

Private cIdTribPiSCof	:= ""

DEFAULT cTipo   	:= PARAMIXB[1]
DEFAULT dDtEmiss	:= PARAMIXB[2]
DEFAULT cSerie  	:= PARAMIXB[3]
DEFAULT cNota   	:= PARAMIXB[4]
DEFAULT cClieFor	:= PARAMIXB[5]
DEFAULT cLoja   	:= PARAMIXB[6]
DEFAULT cMotCancela	:= PARAMIXB[7]
DEFAULT aAIDF		:= PARAMIXB[8]
DEFAULT cCodcanc	:= PARAMIXB[7]
DEFAULT cAmbiente   	:= PARAMIXB[10]

//---------------------------------------------
//Posiciona no dados relaciolados a NFS-e (Produto, Cliente, Condição de Pagamento, Títulos Financeiro, Deduções , ...
//---------------------------------------------	
filtrarnf( cNota, cSerie, cClieFor, cLoja)

//---------------------------------------------
//Geracao do arquivo XML
//---------------------------------------------	
if !Empty(aNota)
    if Len(aProd) > 0
        cString += identNac( aNota, cAmbiente, cSigamat)
        //cString	+= substit( aNota )
        cString	+= prestNac()
        //cString	+= prestacao( cMunPrest, cDescMunP, aDest, cMunPSIAFI )
        cString	+= tomadorNac( aDest, if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN ))
        cString	+= intermedNac( aInterm )
        cString	+= servicosNac( aProd, cNatOper, lNFeDesc, cDiscrNFSe,aRetSF3,aDest) 
        cString	+= valoresNac( aISSQN, aRetido, aTotal, aDest, if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN ),aLeiTrp,lRecIrrf,aProd )
        //cString	+= faturas( aDupl )
        //cString	+= pagtos( aDupl,cCondPag )
        //cString	+= deducoes( aProd, aDeduz, aDeducao )
        //cString	+= infCompl( cMensCli, cMensFis, lNFeDesc, cDescrNFSe)
        //cString	+= construcaoNac( aConstr )
        If ( Date() >= dNfseNacIBS) 
            cString	+= IbsCbs( aDest, cCodMun, aNota, cClieFor, cLoja, aEntrega )
        EndIf
        cString += '</infDPS>'
        cString += '</DPS>'
    EndIf
endif	

    /*/-----------------------------------------------------------------------
        Destruir os objetos e arrays da classe TSSTCIntegration após o término do loop e montagem do .XML.
        Não remover, tratamento para cenário que Lote grande com ambientes com Balanciamento de carga.
        @since 06/01/2026
        @author Felipe Duarte Luna
        @version 12.1.2510
    /*///-----------------------------------------------------------------------
    DestroyTCI(@oNfTciIntg)

return { cString, cNfe }

//-----------------------------------------------------------------------
/*/{Protheus.doc}	getUFCode
Funcao que retorna o codigo da UF, de acordo com a tabela 
disponibilizada pelo IBGE. 

@param cEst  	sigla do estado

@return	cCodUF	 Codigo da UF

@author Felipe Duarte Luna
@since 24/10/2023
@version 12.12210
/*/
//-----------------------------------------------------------------------
static function filtrarnf( cNota, cSerie, cClieFor, cLoja)

Local nW		:= 0
Local nX        := 0
Local nZ		:= 0
Local aUF     	:= {} 
Local cTitulo   := ""
Local cTitPFS   := "" // Título da integração do módulo SIGAPFS x Financeiro
Local cNatPFS   := "" // Natureza da integração do módulo SIGAPFS x Financeiro


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Preenchimento do Array de UF                                            ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aAdd(aUF,{"RO","11"})
aAdd(aUF,{"AC","12"})
aAdd(aUF,{"AM","13"})
aAdd(aUF,{"RR","14"})
aAdd(aUF,{"PA","15"})
aAdd(aUF,{"AP","16"})
aAdd(aUF,{"TO","17"})
aAdd(aUF,{"MA","21"})
aAdd(aUF,{"PI","22"})
aAdd(aUF,{"CE","23"})
aAdd(aUF,{"RN","24"})
aAdd(aUF,{"PB","25"})
aAdd(aUF,{"PE","26"})
aAdd(aUF,{"AL","27"})
aAdd(aUF,{"MG","31"})
aAdd(aUF,{"ES","32"})
aAdd(aUF,{"RJ","33"})
aAdd(aUF,{"SP","35"})
aAdd(aUF,{"PR","41"})
aAdd(aUF,{"SC","42"})
aAdd(aUF,{"RS","43"})
aAdd(aUF,{"MS","50"})
aAdd(aUF,{"MT","51"})
aAdd(aUF,{"GO","52"})
aAdd(aUF,{"DF","53"})
aAdd(aUF,{"SE","28"})
aAdd(aUF,{"BA","29"})
aAdd(aUF,{"EX","99"})

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Posiciona NF                                                            ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
dbSelectArea("SF2")
dbSetOrder(1)// F2_FILIAL, F2_DOC, F2_SERIE, F2_CLIENTE, F2_LOJA, F2_FORMUL, R_E_C_N_O_, D_E_L_E_T_
DbGoTop()
If DbSeek(xFilial("SF2")+cNota+cSerie+cClieFor+cLoja)	

    aadd(aNota,SF2->F2_SERIE)
    aadd(aNota,IIF(Len(SF2->F2_DOC)==6,"000","")+SF2->F2_DOC)
    aadd(aNota,SF2->F2_EMISSAO)
    aadd(aNota,cTipo)
    aadd(aNota,SF2->F2_TIPO)
    aadd(aNota,"1")
    If SF2->(FieldPos("F2_NFSUBST"))<>0 
        aadd(aNota,IIF(Len(SF2->F2_DOC)==6 .And. !Empty(SF2->F2_NFSUBST),"000","")+SF2->F2_NFSUBST)
    Endif
    If SF2->(FieldPos("F2_SERSUBS"))<>0
        aadd(aNota,SF2->F2_SERSUBS)
    Endif
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
        dbSetOrder(1)
        DbSeek(xFilial("SA1")+cCodCli+cLojCli)
        
        aadd(aDest,AllTrim(SA1->A1_CGC))
        aadd(aDest,SA1->A1_NOME)
        aadd(aDest,myGetEnd(SA1->A1_END,"SA1")[1])
        aadd(aDest,convType(IIF(myGetEnd(SA1->A1_END,"SA1")[2]<>0,myGetEnd(SA1->A1_END,"SA1")[3],"SN")))
        aadd(aDest,IIF(SA1->(FieldPos("A1_COMPLEM")) > 0 .And. !Empty(SA1->A1_COMPLEM),SA1->A1_COMPLEM,myGetEnd(SA1->A1_END,"SA1")[4]))
        aadd(aDest,SA1->A1_BAIRRO)
        If !Upper(SA1->A1_EST) == "EX"
            aadd(aDest,SA1->A1_COD_MUN)
            aadd(aDest,SA1->A1_MUN)				
        Else
            aadd(aDest,"99999")
            aadd(aDest,"EXTERIOR")
        EndIf
        aadd(aDest,Upper(SA1->A1_EST))
        aadd(aDest,SA1->A1_CEP)
        aadd(aDest,IIF(Empty(SA1->A1_PAIS),"1058"  ,Posicione("SYA",1,xFilial("SYA")+SA1->A1_PAIS,"YA_SISEXP"))) 
        aadd(aDest,IIF(Empty(SA1->A1_PAIS),"BRASIL",Posicione("SYA",1,xFilial("SYA")+SA1->A1_PAIS,"YA_DESCR" )))
        aadd(aDest,Alltrim(SA1->A1_DDD)+Alltrim(StrTran(SA1->A1_TEL,"-","")))
        aadd(aDest,vldIE(SA1->A1_INSCR,IIF(SA1->(FIELDPOS("A1_CONTRIB"))>0,SA1->A1_CONTRIB<>"2",.T.)))
        aadd(aDest,SA1->A1_SUFRAMA)
        aadd(aDest,SA1->A1_EMAIL)          
        aadd(aDest,SA1->A1_INSCRM) 
        aadd(aDest,SA1->A1_CODSIAF)
        aadd(aDest,SA1->A1_NATUREZ)            
        aadd(aDest,Iif(!Empty(SA1->A1_SIMPNAC),SA1->A1_SIMPNAC,"2"))
        aadd(aDest,Iif(SA1->(FieldPos("A1_INCULT"))> 0 , Iif(!Empty(SA1->A1_INCULT),SA1->A1_INCULT,"2"), "2"))
        aadd(aDest,SA1->A1_TPESSOA)
        aadd(aDest,SF2->F2_DOC)
        aadd(aDest,SF2->F2_SERIE)
        aadd(aDest,Iif(SA1->(FieldPos("A1_OUTRMUN"))> 0 ,SA1->A1_OUTRMUN,""))	//25							
        aadd(aDest,Iif(SA1->(FieldPos("A1_PFISICA"))> 0 ,SA1->A1_PFISICA,""))	//26
        aadd(aDest,Iif(SA1->(FieldPos("A1_TIPO"))> 0 ,SA1->A1_TIPO,""))	//27
        aadd(aDest,Iif(SA1->(FieldPos("A1_NIF"))> 0 ,SA1->A1_NIF,""))	//28
                    
        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³Posiciona Natureza                                                      ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
        
        //Para uso no Turismo é necessário verificar se a nota foi gerada por pedido ou pelo módulo de turismo antes de definir a natureza.
        If lIntTur
            aAreaAux := GetArea()
            
            dbSelectArea("SD2")
            dbSetOrder(3)
            dbSeek(xFilial("SD2")+SF2->F2_DOC+SF2->F2_SERIE+SF2->F2_CLIENTE+SF2->F2_LOJA)
            
            dbSelectArea("SC5")
            dbSetOrder(1)
            If !(dbSeek(xFilial("SC5")+(cAliasSD2)->D2_PEDIDO))
                cNatBusc := GetTitNat(cNota, cSerie, cClieFor, cLoja)
            Else
                cNatBusc := NatPCC ( aDest , cNatPCC )
            EndIf
            RestArea(aAreaAux)
        Else
            If lJescTur .And. FindFunction("JurTitPFS") // Integração com módulo SIGAPFS //12.1.2510
                cTitPFS  := JurTitPFS(SF2->F2_DOC, SF2->F2_SERIE, @cNatPFS)
                cTitulo  := cTitPFS
                cNatBusc := cNatPFS
            Else
                cNatBusc := NatPCC ( aDest , cNatPCC )
            EndIf

        EndIf
        DbSelectArea("SED")
        DbSetOrder(1)
        DbSeek(xFilial("SED")+ cNatBusc )  			
        
        If SF2->(FieldPos("F2_CLIENT"))<>0 .And. !Empty(SF2->F2_CLIENT+SF2->F2_LOJENT) .And. SF2->F2_CLIENT+SF2->F2_LOJENT<>SF2->F2_CLIENTE+SF2->F2_LOJA
            dbSelectArea("SA1")
            dbSetOrder(1)
            DbSeek(xFilial("SA1")+SF2->F2_CLIENT+SF2->F2_LOJENT)
            
            aadd(aEntrega,SA1->A1_CGC)
            aadd(aEntrega,myGetEnd(SA1->A1_END,"SA1")[1])
            aadd(aEntrega,convType(IIF(myGetEnd(SA1->A1_END,"SA1")[2]<>0,myGetEnd(SA1->A1_END,"SA1")[3],"SN")))
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
        aadd(aDest,convType(IIF(myGetEnd(SA2->A2_END,"SA2")[2]<>0,myGetEnd(SA2->A2_END,"SA2")[3],"SN")))
        aadd(aDest,IIF(SA2->(FieldPos("A2_COMPLEM")) > 0 .And. !Empty(SA2->A2_COMPLEM),SA2->A2_COMPLEM,myGetEnd(SA2->A2_END,"SA2")[4]))				
        aadd(aDest,SA2->A2_BAIRRO)
        If !Upper(SA2->A2_EST) == "EX"
            aadd(aDest,SA2->A2_COD_MUN)
            aadd(aDest,SA2->A2_MUN)				
        Else
            aadd(aDest,"99999")
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
        aadd(aDest,"")//A1_INCULT
        aadd(aDest,"")//A1_TPESSOA				  
        aadd(aDest,"")//Nota para empresa hospitalar utilizar apenas com SF2
        aadd(aDest,"")//Serie para empresa hospitalar utilizar apenas com SF2
        aadd(aDest,"")//A1_OUTRMUN
        aadd(aDest,Iif(SA2->(FieldPos("A2_PFISICA"))> 0 ,SA2->A2_PFISICA,""))//26
        aadd(aDest,"")	//27
        aadd(aDest,Iif(SA2->(FieldPos("A2_NIFEX"))> 0 ,SA2->A2_NIFEX,""))	//28

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
    //Query específica para registros do Loja, devido a regras de parametrização
    //o prefixo é gravado diferente entre SE1 e SF2 para a mesma venmda assitida
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

    If Empty(cTitPFS)
        cTitulo := SF2->F2_DUPL
    EndIf

    If !Empty(cTitulo)
                    
        cLJTPNFE := (StrTran(cMV_LJTPNFE," ,"," ','"))+" "
        cWhere := cLJTPNFE
        If cLJPRF != "SF2->F2_SERIE"
            lLJPRF := .F.
        EndIf

        dbSelectArea("SE1")
        dbSetOrder(1)	
        #IFDEF TOP
            lQuery  := .T.
            cAliasSE1 := GetNextAlias()
            If lLJPRF .OR. lTssPref //Executa Query com busca pelo Prefixo da SF2 se cLJPRF estiver com conteudo padrao TOTVS ou se parametro MV_TSSPREF estiver preenchido com .T. 
                BeginSql Alias cAliasSE1
                    COLUMN E1_VENCORI AS DATE
                    SELECT E1_FILIAL,E1_PREFIXO,E1_NUM,E1_PARCELA,E1_TIPO,E1_VENCORI,E1_VALOR,E1_ORIGEM,E1_CSLL,E1_COFINS,E1_PIS,E1_PIS,E1_IRRF,E1_INSS,E1_ISS,E1_MOEDA,E1_CLIENTE,E1_LOJA
                    FROM %Table:SE1% SE1
                    WHERE
                    SE1.E1_FILIAL = %xFilial:SE1% AND
                    SE1.E1_PREFIXO = %Exp:SF2->F2_PREFIXO% AND
                    SE1.E1_NUM = %Exp:cTitulo% AND 
                    ((SE1.E1_TIPO = %Exp:MVNOTAFIS%) OR
                    SE1.E1_TIPO IN (%Exp:cTipoPcc%) OR
                    SE1.E1_TIPO IN (%Exp:cTipoRet%) OR
                    (SE1.E1_ORIGEM = 'LOJA701' AND SE1.E1_TIPO IN (%Exp:cWhere%))) AND
                    SE1.%NotDel%
                    ORDER BY %Order:SE1%
                EndSql
            else
                BeginSql Alias cAliasSE1
                    COLUMN E1_VENCORI AS DATE
                    SELECT E1_FILIAL,E1_PREFIXO,E1_NUM,E1_PARCELA,E1_TIPO,E1_VENCORI,E1_VALOR,E1_ORIGEM,E1_CSLL,E1_COFINS,E1_PIS,E1_PIS,E1_IRRF,E1_INSS,E1_ISS,E1_MOEDA,E1_CLIENTE,E1_LOJA
                    FROM %Table:SE1% SE1
                    WHERE
                    SE1.E1_FILIAL = %xFilial:SE1% AND
                    SE1.E1_NUM = %Exp:cTitulo% AND 
                    ((SE1.E1_TIPO = %Exp:MVNOTAFIS%) OR
                    SE1.E1_TIPO IN (%Exp:cTipoPcc%) OR
                    SE1.E1_TIPO IN (%Exp:cTipoRet%) OR
                    (SE1.E1_ORIGEM = 'LOJA701' AND SE1.E1_TIPO IN (%Exp:cWhere%))) AND
                    SE1.%NotDel%
                    ORDER BY %Order:SE1%
                EndSql
            EndIf
        #ELSE
            DbSeek(xFilial("SE1")+SF2->F2_PREFIXO+SF2->F2_DOC)
        #ENDIF
        
        While !Eof() .And. xFilial("SE1") == (cAliasSE1)->E1_FILIAL .And. cTitulo == (cAliasSE1)->E1_NUM .AND.;
            (SF2->F2_PREFIXO == (cAliasSE1)->E1_PREFIXO .Or. !lLJPRF) 
            If 	(cAliasSE1)->E1_TIPO = MVNOTAFIS .OR. ((cAliasSE1)->E1_ORIGEM = 'LOJA701' .AND. (cAliasSE1)->E1_TIPO $ cWhere)
                If lDuplLiq
                    nAbatim := SomaAbat((cAliasSE1)->E1_PREFIXO,(cAliasSE1)->E1_NUM,(cAliasSE1)->E1_PARCELA,"R",(cAliasSE1)->E1_MOEDA,dDataBase,(cAliasSE1)->E1_CLIENTE,(cAliasSE1)->E1_LOJA,(cAliasSE1)->E1_FILIAL,,(cAliasSE1)->E1_TIPO)
                    // Função SomaAbat: Calcula todas as retenções na geração do Titulo
                EndIf
                aadd(aDupl,{(cAliasSE1)->E1_PREFIXO+(cAliasSE1)->E1_NUM+(cAliasSE1)->E1_PARCELA,(cAliasSE1)->E1_VENCORI,(cAliasSE1)->(E1_VALOR)- nAbatim,(cAliasSE1)->E1_PARCELA,(cAliasSE1)->E1_NUM})
            EndIf  

            If Alltrim((cAliasSE1)->E1_TIPO) $ "IR-"
                lTitIrrf := .T.
            EndIf
            //Tratamento para saber se existem titulos de retenção de PIS,COFINS e CSLL
            If lNfsePcc
                If Alltrim((cAliasSE1)->E1_TIPO) $ "NF"
                    nRetCsl += (cAliasSE1)->E1_CSLL 
                    nRetCof	+= (cAliasSE1)->E1_COFINS
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
        If SF3->(FieldPos("F3_RECISS")) > 0
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
            EndIF
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
            
    //Verifica fonte carga tributária
                            
    If cMvMsgTrib $ "1-3"
        If lIntegHtl //Integracao Hotelaria
            cFntCtrb := SF2->F2_LTRAN
        Else
            If cMvFisCTrb =="1"
                If FindFunction("AlqLeiTran")		            		
                    cFntCtrb := AlqLeiTran("SB1","SBZ" )[2]			            		
                EndIf
                If Empty(cFntCtrb) .And. !Empty(cMvFntCtrb).And. !cFntCtrb $ "IBPT"
                    cFntCtrb := cMvFntCtrb
                EndIf 
            Else
                If Empty(cFntCtrb) .And. !Empty(cMvFntCtrb)
                    cFntCtrb := cMvFntCtrb
                EndIf 
            EndIf
        EndIf
    EndIf
    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Analisa os impostos de retencao                                         ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ		

    aadd(aRetido,{"PIS",SF2->F2_BASPIS,nRetPis,SED->ED_PERCPIS,aRetPIS,aBaspis}) 
    
    aadd(aRetido,{"COFINS",SF2->F2_BASCOFI,nRetCof,SED->ED_PERCCOF,aRetCOF,aBasCof})
    
    aadd(aRetido,{"CSLL",SF2->F2_BASCSLL,nRetCsl,SED->ED_PERCCSL,aRetCSL,aBasCsll})
    
    If SF2->(FieldPos("F2_VALIRRF"))<>0 .and. (SF2->F2_VALIRRF>0 .Or. lMvNFSEIR)
        aadd(aRetido,{"IRRF",SF2->F2_BASEIRR,SF2->F2_VALIRRF,SED->ED_PERCIRF,aRetIRR,aBasIRR})
    EndIf
    If SF2->(FieldPos("F2_VALINSS"))<>0 .and. (SF2->F2_VALINSS>0 .Or. lMvNFSEINSS)
        aadd(aRetido,{"INSS",SF2->F2_BASEINS,SF2->F2_VALINSS,SED->ED_PERCINS,aRetINS,aBasINS})
    EndIf      
    
    // Total Carga Tributária 
    If SF2->(FieldPos("F2_TOTIMP"))<>0 .and. SF2->F2_TOTIMP>0
        nTotalCrg := SF2->F2_TOTIMP
    EndIf
    
    If !lTitIrrf 
        lRecIrrf := .F.
    EndIf

    //----------------------------------------------
    // Total Carga Tributária por Ente Tributante
    //----------------------------------------------
    
    // Ente Federal
    If SF2->(FieldPos("F2_TOTFED"))<>0 .and. SF2->F2_TOTFED>0
        nTotFedCrg := SF2->F2_TOTFED
    EndIf

    // Ente Estadual
    If SF2->(FieldPos("F2_TOTEST"))<>0 .and. SF2->F2_TOTEST>0
        nTotEstCrg := SF2->F2_TOTEST
    EndIf
    
    // Ente Municipal
    If SF2->(FieldPos("F2_TOTMUN"))<>0 .and. SF2->F2_TOTMUN>0
        nTotMunCrg := SF2->F2_TOTMUN
    EndIf

    aLeiTrp := {0,0,0}
    aLeiTrp[1] := nTotFedCrg
    aLeiTrp[2] := nTotEstCrg
    aLeiTrp[3] := nTotMunCrg
    
    //Verifica tipo do cliente.
    cTpCliente := Alltrim(SF2->F2_TIPOCLI)
                
    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Pesquisa itens de nota                                                  ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
    
    dbSelectArea("SD2")
    dbSetOrder(3)	
    lQuery  := .T.
    If oQryFltDoc == Nil	
        cQuery += "SELECT D2_FILIAL,D2_SERIE,D2_DOC,D2_CLIENTE,D2_LOJA,D2_COD,D2_TES,D2_NFORI,D2_SERIORI,D2_ITEMORI,D2_TIPO,D2_ITEM,D2_CF, "
        cQuery += "D2_QUANT,D2_TOTAL,D2_DESCON,D2_VALFRE,D2_SEGURO,D2_PEDIDO,D2_ITEMPV,D2_DESPESA,D2_VALBRUT,D2_VALISS,D2_PRUNIT, "
        cQuery += "D2_CLASFIS,D2_PRCVEN,D2_CODISS,D2_DESCZFR,D2_PREEMB,D2_BASEISS,D2_VALIMP1,D2_VALIMP2,D2_VALIMP3,D2_VALIMP4,D2_VALIMP5,D2_PROJPMS, "
        cQuery += "D2_TOTIMP, D2_DESCICM, D2_TOTFED, D2_TOTEST, D2_TOTMUN, "
        cQuery += "D2_VALPIS,D2_VALCOF,D2_VALCSL,D2_VALIRRF,D2_VALINS,D2_ORIGLAN,D2_VALICM,D2_BASECSL,D2_BASEPIS,D2_BASEIRR,D2_BASEINS,D2_BASECOF, D2_IDTRIB, D2_ABATISS, D2_ABATMAT  FROM "
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
        SC5->( dbSetOrder(1) )
        If SC5->( MsSeek( xFilial("SC5") + (cAliasSD2)->D2_PEDIDO) )
            If ( SC5->(FieldPos("C5_OBRA")) > 0 .And. !Empty(SC5->C5_OBRA) ) .And. SC5->(FieldPos("C5_ARTOBRA")) > 0
                aadd(aConstr,(SC5->C5_OBRA))
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
    If Len(aObra) < 17
        For nX := 1 To 17
            If Len(aObra) < 17
                aadd(aObra,"")							
            EndIf
        Next nX
    EndIf
    If ValType(aObra) <> "U"
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

        // Criado para Campinas - SP - 3509502
        cInsMunObr  := AllTrim(If(!Empty(aObra[16]) .And. SC5->(FieldPos(aObra[16])) > 0 , &(aObra[16]),"")) // Inscrição Municipal Obra
        cCodSerObr  := AllTrim(If(!Empty(aObra[17]) .And. SC5->(FieldPos(aObra[17])) > 0 , &(aObra[17]),"")) // Codigo de Serviço da Obra
    EndIf
    If(!Empty(cLogradOb),aadd(aConstr,(cLogradOb)),aadd(aConstr,"") ) //Logradouro para Obra
    If(!Empty(cCompleOb),aadd(aConstr,(cCompleOb)),aadd(aConstr,"") ) //Complemento para obra
    If(!Empty(cNumeroOb),aadd(aConstr,(cNumeroOb)),aadd(aConstr,"") ) // Numero para Obra
    If(!Empty(cBairroOb),aadd(aConstr,(cBairroOb)),aadd(aConstr,"") ) // Bairro para Obra
    If(!Empty(cCepOb),aadd(aConstr,(cCepOb)),aadd(aConstr,"") ) // Cep para Obra
    If(!Empty(cCodMunob),aadd(aConstr,(cCodMunob)),aadd(aConstr,"") ) // Cod do Municipio para Obra
    If(!Empty(cNomMunOb),aadd(aConstr,(cNomMunOb)),aadd(aConstr,"") ) // Nome do municipio para Obra
    If(!Empty(cUfOb),aadd(aConstr,(cUfOb)),aadd(aConstr,"") ) // UF para Obra
    If(!Empty(cCodPaisOb),aadd(aConstr,(cCodPaisOb)),aadd(aConstr,"") ) // Codigo do Pais para Obra
    If(!Empty(cNomPaisOb),aadd(aConstr,(cNomPaisOb)),aadd(aConstr,"") ) // Nome do Pais para Obra
    If(!Empty(cNumArtOb),aadd(aConstr,(cNumArtOb)),aadd(aConstr,"") ) // Numero Art para Obra
    If(!Empty(cNumCeiOb),aadd(aConstr,(cNumCeiOb)),aadd(aConstr,"") ) // Numero CEI para Obra
    If(!Empty(cNumProOb),aadd(aConstr,(cNumProOb)),aadd(aConstr,"") ) // Numero Projeto para Obra
    If(!Empty(cNumMatOb),aadd(aConstr,(cNumMatOb)),aadd(aConstr,"") ) // Numero de Mtricula para Obra
    If(!Empty(cNumEncap),aadd(aConstr,(cNumEncap)),aadd(aConstr,"") ) // NumeroEncapsulamento
    
    If(!Empty(cInsMunObr),aadd(aConstr,(cInsMunObr)),aadd(aConstr,"") ) // Inscrição Municipal Obra
    If(!Empty(cCodSerObr),aadd(aConstr,(cCodSerObr)),aadd(aConstr,"") ) // Codigo de Serviço da Obra
    
    SF4->(dbSetOrder(1))
    
    cSigamat := if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN )
    cCidCob	 := if( type( "oSigamatX" ) == "U",SM0->M0_CIDCOB,oSigamatX:M0_CIDCOB )
    cIDEnt	 := if( type( "oSigamatX" ) == "U",SM0->M0_CIDENT,oSigamatX:M0_CIDENT )

    /*/ Configurador de Tributos
        Função TssTCInteg responsavel pela Integracao TSS com Configurador de Tributos, adequação para atender a
        Reforma Tributária. Classifica o tipo de tributacao do item da nota fiscal, de acordo com a configuracao da Classe TSSTCIIntegration
        @since 17/02/2025
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
            cIdTribPiSCof := (cAliasSD2)->D2_IDTRIB
        EndIf
        
        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³Verifica a natureza da operacao                                         ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
        dbSelectArea("SC5")
        dbSetOrder(1)
        If DbSeek(xFilial("SC5")+(cAliasSD2)->D2_PEDIDO)
            lSC5 := .T.
        Else
            lSC5 := .F.			
        EndIf	
            
        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³Pega retencoes por item ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
        aAdd(aRetPIS,Iif(nRetPis > 0, (cAliasSD2)->D2_VALPIS, 0))
        aAdd(aBasPIS,Iif(nRetPis > 0, (cAliasSD2)->D2_BASEPIS, 0))
        nScan := aScan(aRetido,{|x| x[1] == "PIS"})
        If nScan > 0
            If !oNfTciIntg == Nil
                If oNfTciIntg:GetTax( cIdTribPiSCof, "PISRET") <> NIL .and. valtype(oNfTciIntg:GetTax( cIdTribPiSCof, "PISRET")["regras_aliquota"]) == "J" .and. !empty(oNfTciIntg:GetAliquotaTax( cIdTribPiSCof, "PISRET")['perc_aliquota'])
                    aRetido[nScan][4]  := oNfTciIntg:GetAliquotaTax( cIdTribPiSCof, "PISRET")['perc_aliquota']
                endif
            endif
            aRetido[nScan][5] := aRetPIS
            aRetido[nScan][6] := aBasPIS
        EndIf

        aAdd(aRetCOF,Iif(nRetCof > 0, (cAliasSD2)->D2_VALCOF, 0))
        aAdd(aBasCOF,Iif(nRetCof > 0, (cAliasSD2)->D2_BASECOF, 0))
        nScan := aScan(aRetido,{|x| x[1] == "COFINS"})
        If nScan > 0
            If !oNfTciIntg == Nil
                If oNfTciIntg:GetTax( cIdTribPiSCof, "COFRET") <> NIL .and. valtype(oNfTciIntg:GetTax( cIdTribPiSCof, "COFRET")["regras_aliquota"]) == "J" .and. !empty(oNfTciIntg:GetAliquotaTax( cIdTribPiSCof, "COFRET")['perc_aliquota'])
                    aRetido[nScan][4]  := oNfTciIntg:GetAliquotaTax( cIdTribPiSCof, "COFRET")['perc_aliquota']
                endif
            endif
            aRetido[nScan][5] := aRetCOF
            aRetido[nScan][6] := aBasCof
        EndIf

        aAdd(aRetCSL,Iif(nRetCsl > 0, (cAliasSD2)->D2_VALCSL, 0))
        aAdd(aBasCsll,Iif(nRetCsl > 0, (cAliasSD2)->D2_BASECSL, 0))
        nScan := aScan(aRetido,{|x| x[1] == "CSLL"})
        If nScan > 0
            If !oNfTciIntg == Nil
                If oNfTciIntg:GetTax( cIdTribPiSCof, "CSL") <> NIL .and. valtype(oNfTciIntg:GetTax( cIdTribPiSCof, "CSL")["regras_aliquota"]) == "J" .and. !empty(oNfTciIntg:GetAliquotaTax( cIdTribPiSCof, "CSL")['perc_aliquota'])
                    aRetido[nScan][4]  := oNfTciIntg:GetAliquotaTax( cIdTribPiSCof, "CSL")['perc_aliquota']
                endif
            endif
            aRetido[nScan][5] := aRetCSL
            aRetido[nScan][6] := aBasCsll
        EndIf

        aAdd(aRetIRR,Iif(SF2->(FieldPos("F2_VALIRRF")) <> 0 .and. SF2->F2_VALIRRF > 0, (cAliasSD2)->D2_VALIRRF, 0))
        aAdd(aBasIRR,Iif(SF2->(FieldPos("F2_VALIRRF")) <> 0 .and. SF2->F2_VALIRRF > 0, (cAliasSD2)->D2_BASEIRR, 0))
        nScan := aScan(aRetido,{|x| x[1] == "IRRF"})
        If nScan > 0
            If lMvNFSEIR
                If nCont == 1 .And. aRetido[nScan][2] > 0
                    aRetido[nScan][3] := 0
                EndIf
                aRetido[nScan][3] += (cAliasSD2)->D2_VALIRRF
            EndIf
            aRetido[nScan][5] := aRetIRR
            aRetido[nScan][6] := aBasIRR
        EndIf

        aAdd(aRetINS,Iif(SF2->(FieldPos("F2_VALINSS")) <> 0 .and. SF2->F2_VALINSS > 0, (cAliasSD2)->D2_VALINS, 	0)) 
        aAdd(aBasINS,Iif(SF2->(FieldPos("F2_VALINSS")) <> 0 .and. SF2->F2_VALINSS > 0, (cAliasSD2)->D2_BASEINS, 0)) 

        nScan := aScan(aRetido,{|x| x[1] == "INSS"})
        If nScan > 0
            If lMvNFSEINSS
                If nCont == 1 .And. aRetido[nScan][2] > 0
                    aRetido[nScan][3] := 0
                EndIf
                aRetido[nScan][3] += (cAliasSD2)->D2_VALINS
            EndIf
            aRetido[nScan][5] := aRetINS
            aRetido[nScan][6] := aBasINS
        EndIf

        //TRATAMENTO - INTEGRACAO COM TMS-GESTAO DE TRANSPORTES
        If IntTms()
            DT6->(DbSetOrder(1))
            If DT6->(DbSeek(xFilial("DT6")+SF2->(F2_FILIAL+F2_DOC+F2_SERIE)))
                cModFrete := DT6->DT6_TIPFRE
                
                SA1->(DbSetOrder(1))
                If SA1->(DbSeek(xFilial("SA1")+DT6->(DT6_CLIDES+DT6_LOJDES)))
                    cMunPSIAFI := SA1->A1_CODSIAF
                EndIf
                
                If DUY->(FieldPos("DUY_CODMUN")) > 0
                    DUY->(DbSetOrder(1))
                    If DUY->(DbSeek(xFilial("DUY")+DT6->DT6_CDRCAL))
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
                    If Alltrim(cSigamat) == "5208707" //Goiania
                        cMunPrest := Alltrim(aDest[25])
                        cDescMunP := aDest[08] 
                    Else
                        If ((cAliasSD2)->D2_ORIGLAN $ "LO")
                            cMunPrest := cSigamat
                        Elseif ((cAliasSD2)->D2_ORIGLAN $ "VD")
                            cMunPrest := aDest[07]
                            If Empty(cMunPrest)
                                cMunPrest := cSigamat
                            EndIf
                        Else
                            cMunPrest := aDest[07]
                        Endif
                        cDescMunP := aDest[08]
                    Endif
                EndIf
            EndIf
        ElseIf lIntTur .AND. Empty( (cAliasSD2)->D2_PEDIDO )
            cMunPrest := SM0->M0_CODMUN
            cDescMunP := Alltrim(SM0->M0_CIDCOB)
        ElseIf lJescTur // Integração com módulo SIGAPFS
            If Upper(SF2->F2_ESTPRES) == "EX"
                cMunPrest := "99999"
                cDescMunP := "EXTERIOR"
            Else
                cMunPrest := SF2->F2_MUNPRES
                cDescMunP := Alltrim(Posicione("CC2", 1, xFilial("CC2") + SF2->F2_ESTPRES + cMunPrest, "CC2_MUN"))
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
                
            ElseIf Alltrim(cSigamat) == "3507605" .And. ( SF4->F4_ISSST == '3' .Or. lConfTrib .And. oISSCfg <> NIL .And. SF4->(FieldPos("F4_NATOPNF")) > 0 .And. Alltrim(SF4->F4_NATOPNF) == '3' )	// Bragança Paulista
                cMunPrest := Alltrim(cSigamat)
                cDescMunP := Alltrim(cCidCob)
            Else
                If Alltrim(cSigamat) == "5208707" //Goiania
                    cMunPrest := Alltrim(aDest[25])
                    cDescMunP := aDest[08] 
                Else
                    cDescMunP := aDest[08]
                    If ((cAliasSD2)->D2_ORIGLAN $ "LO")
                        cMunPrest := Alltrim(cSigamat)
                        cDescMunP := Alltrim(cIDEnt)
                    Elseif ((cAliasSD2)->D2_ORIGLAN $ "VD")
                        cMunPrest := aDest[07]
                        If Empty(cMunPrest)
                            cMunPrest := Alltrim(cSigamat)
                            cDescMunP := Alltrim(cIDEnt)
                        EndIf
                    Else
                        cMunPrest := aDest[07]
                    Endif
                    
                Endif
            EndIf
            
            If lSC5 .And. SC5->(FieldPos("C5_MUNPRES")) > 0 .And. Empty(SC5->C5_MUNPRES) .And. cSigamat == "3509502"
            
                SA1->(DbSetOrder(1))
                If SA1->(DbSeek(xFilial("SA1")+SC5->C5_CLIENT+SC5->C5_LOJACLI))
                    cMunPSIAFI := SA1->A1_CODSIAF
                EndIf
            
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
        dbSetOrder(1)
        DbSeek(xFilial("SF4")+(cAliasSD2)->D2_TES)				
        
        //Pega descricao do pedido de venda-Parametro MV_NFESERV
        cFieldMsg := GetNewPar("MV_CMPUSR","")
        If !lNFeDesc
            If lNatOper .And. lSC5 .And. nCont == 1 .and. !Empty(cFieldMsg) .and. SC5->(FieldPos(cFieldMsg)) > 0 .and. !Empty(&("SC5->"+cFieldMsg))
                cNatOper := If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(&("SC5->"+cFieldMsg))),&("SC5->"+cFieldMsg))+" "
            ElseIf lNatOper .And. lSC5 .And. !Empty(SC5->C5_MENNOTA).And. nCont == 1
                cNatOper += If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(SC5->C5_MENNOTA)),SC5->C5_MENNOTA)+" "
            ElseIf SF2->(FieldPos("F2_MENNOTA")) <> 0 .and. !AllTrim(SF2->F2_MENNOTA) $ cMensCli .and. !Empty(AllTrim(SF2->F2_MENNOTA))
                cDiscrNFSe +=If(FindFunction('CleanSpecChar'),CleanSpecChar(AllTrim(SF2->F2_MENNOTA)),AllTrim(SF2->F2_MENNOTA))
            EndIf
        Else 
            If lSC5 .And. nCont == 1 .and. !Empty(cFieldMsg) .and. SC5->(FieldPos(cFieldMsg)) > 0 .and. !Empty(&("SC5->"+cFieldMsg))
                cDiscrNFSe := If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(&("SC5->"+cFieldMsg))),&("SC5->"+cFieldMsg))+" "
            ElseIf lSC5 .And. !Empty(SC5->C5_MENNOTA).And. nCont == 1
                cDiscrNFSe := If(FindFunction('CleanSpecChar'),CleanSpecChar(Alltrim(SC5->C5_MENNOTA)),SC5->C5_MENNOTA)+" "
            ElseIf !Empty(AllTrim(SF2->F2_MENNOTA)) .And. nCont == 1
                cDiscrNFSe +=If(FindFunction('CleanSpecChar'),CleanSpecChar(AllTrim(SF2->F2_MENNOTA)),AllTrim(SF2->F2_MENNOTA))
            EndIf
        EndIf

        If IntTMS() .And. nCont == 1
            DTC->(DbSetOrder(3))
            If DTC->(MsSeek(xFilial('DTC')+SF2->(F2_FILIAL+F2_DOC+F2_SERIE)))
                cObsDtc := StrTran(MsMM(DTC->DTC_CODOBS,80),Chr(13),". ")
                cNatOper += Iif(!Empty(cObsDtc),cObsDtc+" - ",cObsDtc)
            EndIf
        EndIf
        
        //---------------------------------------
        // - Posiciona no Cadastro de Produtos
        //---------------------------------------
        dbSelectArea( "SB1" )
        dbSetOrder( 1 )
        DbSeek( xFilial( "SB1" ) + ( cAliasSD2 )->D2_COD )
        //Define se o PIS/COFINS é retito
        If !lRetPisCof .And. SB1->B1_RETOPER == "1"
            lRetPisCof := .T.
        EndIf
        
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
        cCgc 	:= if( type( "oSigamatX" ) == "U",SM0->M0_CGC,oSigamatX:M0_CGC )
        cEstCob := if( type( "oSigamatX" ) == "U",SM0->M0_ESTCOB,oSigamatX:M0_ESTCOB )

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
                    
                    aadd(aNfVinc,{SD1->D1_EMISSAO,SD1->D1_SERIE,SD1->D1_DOC,IIF(SD1->D1_TIPO $ "DB",If(SD1->D1_FORMUL=="S",cCgc,SA1->A1_CGC),If(SD1->D1_FORMUL=="S",cCgc,SA2->A2_CGC)),cEstCob,SF1->F1_ESPECIE})
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
                    
                    aadd(aNfVinc,{SF2->F2_EMISSAO,SD2->D2_SERIE,SD2->D2_DOC,cCgc,cEstCob,SF2->F2_ESPECIE})
                EndIf
                RestArea(aOldReg)
                RestArea(aOldReg2)
            EndIf
        EndIf
        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³Obtem os dados do produto                                               ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ			
        dbSelectArea("SB1")
        dbSetOrder(1)
        DbSeek(xFilial("SB1")+(cAliasSD2)->D2_COD)
        
        dbSelectArea("SB5")
        dbSetOrder(1)
        DbSeek(xFilial("SB5")+(cAliasSD2)->D2_COD)
        //Veiculos Novos
        If AliasIndic("CD9")			
            dbSelectArea("CD9")
            dbSetOrder(1)
            DbSeek(xFilial("CD9")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
        EndIf			
        //Medicamentos
        If AliasIndic("CD7")			
            dbSelectArea("CD7")
            dbSetOrder(1)
            DbSeek(xFilial("CD7")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
        EndIf
        // Armas de Fogo
        If AliasIndic("CD8")						
            dbSelectArea("CD8")
            dbSetOrder(1) 
            DbSeek(xFilial("CD8")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
        EndIf
        // Msg Zona Franca de Manaus / ALC
        dbSelectArea("SF3")
        If Alltrim(cSigamat) == "4303905"
            dbSetOrder(5)//F3_FILIAL+F3_SERIE+F3_NFISCAL+F3_CLIEFOR+F3_LOJA+F3_IDENTFT
            nItem := PadL((cAliasSD2)->D2_ITEM,6,"0")                                                                                                     
            If DbSeek(xFilial("SF3")+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+nItem)			
                If !SF3->F3_DESCZFR == 0
                    cMensFis := "Total do desconto Ref. a Zona Franca de Manaus / ALC. R$ "+str(SF3->F3_VALOBSE-SF2->F2_DESCONT,13,2)
                EndIf 			
            EndIf
        Else	
            dbSetOrder(4)
            If DbSeek(xFilial("SF3")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_DOC+SF2->F2_SERIE)			
                If !SF3->F3_DESCZFR == 0
                    cMensFis := "Total do desconto Ref. a Zona Franca de Manaus / ALC. R$ "+str(SF3->F3_VALOBSE-SF2->F2_DESCONT,13,2)
                EndIf 			
            EndIf	
        EndIf			
        
        dbSelectArea("SC6")
        dbSetOrder(1)
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

        If AliasIndic("CE1") .And. lMvIssxMun		
            dbSelectArea("CE1")
            dbSetOrder(1) //CE1_FILIAL+CE1_CODISS+CE1_ESTISS+CE1_CMUISS+CE1_PROISS
            If SC5->(ColumnPos("C5_ESTPRES")) > 0 .And. SC5->(ColumnPos("C5_MUNPRES")) > 0
                cUFxIss := IIF( !Empty(SC5->C5_ESTPRES), SC5->C5_ESTPRES, SM0->M0_ESTENT )
                cMunxISS := IIF( !Empty(SC5->C5_MUNPRES),Alltrim(SC5->C5_MUNPRES), Substr(Alltrim(SM0->M0_CODMUN),3,5))
            EndIf
            IF !DbSeek(xFilial("CE1")+SB1->B1_CODISS+cUFxIss+cMunxISS+(cAliasSD2)->D2_COD)
                DbSeek(xFilial("CE1")+SB1->B1_CODISS+cUFxIss+cMunxISS+Space(15))
            Endif
        EndIf
        
        dbSelectArea("CD2")
        If !(cAliasSD2)->D2_TIPO $ "DB"
            dbSetOrder(1)
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
                    If CD2->CD2_VLTRIB > 0 .Or. (CD2->CD2_VLTRIB == 0 .And. CD2->CD2_BC > 0)
                        //aPIS := {CD2->CD2_CST,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
                        aPis[1] := CD2->CD2_CST
                        aPis[2] += CD2->CD2_BC
                        aPis[3] := CD2->CD2_ALIQ
                        aPis[4] += CD2->CD2_VLTRIB
                        aPis[5] += CD2->CD2_QTRIB
                        aPis[6] += CD2->CD2_PAUTA
                    Endif
                    If Empty(aISS)
                        aISS := {0,0,0,0,0}
                    EndIf
                    aISS[04]+= CD2->CD2_VLTRIB	
                
                Case AllTrim(CD2->CD2_IMP) == "CF2"
                    If CD2_VLTRIB > 0 .Or. (CD2->CD2_VLTRIB == 0 .And. CD2->CD2_BC > 0)
                        //aCOFINS :=  {CD2->CD2_CST,CD2->CD2_BC,CD2->CD2_ALIQ,CD2->CD2_VLTRIB,CD2->CD2_QTRIB,CD2->CD2_PAUTA}
                        aCOFINS[1] := CD2->CD2_CST
                        aCOFINS[2] += CD2->CD2_BC
                        aCOFINS[3] := CD2->CD2_ALIQ
                        aCOFINS[4] += CD2->CD2_VLTRIB
                        aCOFINS[5] += CD2->CD2_QTRIB
                        aCOFINS[6] += CD2->CD2_PAUTA
                    EndIf
                    If Empty(aISS)
                        aISS := {0,0,0,0,0}
                    EndIf
                    aISS[05] += CD2->CD2_VLTRIB	
                
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
                    If nAliq > 0
                        If nAliq == CD2->CD2_ALIQ .And. lAglutina
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
        If cSigamat == "4205407" //florianopolis
            nValTotPrd := IIF(!(cAliasSD2)->D2_TIPO$"IP",If(cSigamat == "3550308",(cAliasSD2)->D2_PRCVEN * (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_TOTAL),0)
        Else
            nValTotPrd := IIF(!(cAliasSD2)->D2_TIPO$"IP",If(cSigamat == "3550308",(cAliasSD2)->D2_PRCVEN * (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_TOTAL),0)+((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR)
        EndIf	
        If lAglutina
            If Len(aProd) > 0		
                If lUsaSF3	
                    If Empty(Alltrim(SFT->FT_TRIBMUN))
                        dbselectArea("SFT")
                        dbsetOrder(1)//FT_FILIAL+FT_TIPOMOV+FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_ITEM+FT_PRODUTO
                        DbSeek(xFilial("SFT")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA)
                    EndIf	
                    nX := aScan(aRetSF3,{|x| x[5] == (cAliasSD2)->D2_CODISS .And. x[3] == IIF(SFT->(FieldPos("FT_TRIBMUN"))<>0,SFT->FT_TRIBMUN,"")})
                Else
                    nX := aScan(aProd,{|x| x[24] == (cAliasSD2)->D2_CODISS .And. x[23] == IIF(SB1->(FieldPos("B1_TRIBMUN"))<>0,RetFldProd(SB1->B1_COD,"B1_TRIBMUN"),"")})
                EndIf	
                If nX > 0						
                    aProd[nX][9] := 1							
                    aProd[nx][13]+= (cAliasSD2)->D2_VALFRE // Valor Frete						
                    aProd[nx][14]+= (cAliasSD2)->D2_SEGURO // Valor Seguro
                    aProd[nx][15]+= ((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR) // Valor Desconto
                    aProd[nx][21]+= SF3->F3_ISSSUB                       						
                    aProd[nx][22]+= SF3->F3_ISSMAT
                    aProd[nx][25]+= a410Arred( (cAliasSD2)->D2_BASEISS, "D2_TOTAL" )
                    aProd[nx][26]+= (cAliasSD2)->D2_VALFRE               						

                    If cSigamat == "3550308"
                        aProd[nx][27]+=	a410Arred( IIF(!(cAliasSD2)->D2_TIPO $ "IP",(cAliasSD2)->D2_TOTAL,0), "D2_TOTAL" )
                        aProd[nx][10] := aProd[nx][28]+=	a410Arred( IIF(!(cAliasSD2)->D2_TIPO $ "IP",(cAliasSD2)->D2_TOTAL,0) + ((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR), "D2_TOTAL")	//Valor Total						
                    Else		
                        //----------------------------------------------------------------
                        // Realizado ajuste para considerar o somatorio do D2_TOTAL, 
                        // caso haja 'desconto' a ser somado, sera validado na 
                        // funcao FunValTot, com isso, ficara validacao em um unico lugar.
                        // @autor: Douglas Parreja
                        // @date: 29/03/2018
                        //----------------------------------------------------------------							
                        aProd[nx][27]+=	a410Arred( IIF(!(cAliasSD2)->D2_TIPO $ "IP",(cAliasSD2)->D2_PRCVEN,0) * (cAliasSD2)->D2_QUANT, "D2_TOTAL" ) // Valor Liquido
                        aProd[nx][10] := aProd[nx][28]+= a410Arred( FunValTot((cAliasSD2)->D2_TIPO,(cAliasSD2)->D2_PRCVEN, (cAliasSD2)->D2_QUANT, getValTotal(nValTotPrd,(cAliasSD2)->D2_TOTAL), (cAliasSD2)->D2_DESCON, (cAliasSD2)->D2_DESCZFR, (cAliasSD2)->D2_VALICM, (cAliasSD2)->D2_IDTRIB, (cAliasSD2)->D2_VALBRUT), FuCamArren(nCamPrcv,nCamQuan,nCamTot) ) //Valor Total
                        //aProd[nx][10] := aProd[nx][28]+=	a410Arred( IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN,0) * (cAliasSD2)->D2_QUANT+((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR), "D2_TOTAL" ) //Valor Total
                    EndIf							
                    aProd[nx][29]+=	getValDesc(lMvded, SF2->F2_CLIENTE, SF2->F2_LOJA, SF2->F2_DOC, SF2->F2_SERIE,(cAliasSD2)->D2_CODISS,(cAliasSD2)->D2_DESCON ) 
                    aProd[nx][35]+= IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTIMP"))<>0,(cAliasSD2)->D2_TOTIMP,0),0) //35 - Lei transparência
                    aProd[nx][38]+= IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTFED"))<>0,(cAliasSD2)->D2_TOTFED,0),0) //38 - Lei transparência
                    aProd[nx][39]+= IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTEST"))<>0,(cAliasSD2)->D2_TOTEST,0),0) //39 - Lei transparência
                    aProd[nx][40]+= IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTMUN"))<>0,(cAliasSD2)->D2_TOTMUN,0),0) //40 - Lei transparência
                    aProd[nx][41]+=	"" 						//41 - Descricao RPS SC6 (nao copiado a tratativa abaixo, para nao ter impacto nos processos legados)
                    aProd[nx][42]+= (cAliasSD2)->D2_ITEM 	//42 - Item da Nota
                    aProd[nx][43]+= (cAliasSD2)->D2_ABATISS+(cAliasSD2)->D2_ABATMAT //43 - Abatimento ISSQN
                    
                Else
                    lAglutina := .F.
                EndIF			                                                                                                                        					
            EndIf	
        EndIF

        If !lAglutina .Or. lUsaSF3 
            dbselectArea("SFT")
            SFT->(dbSetOrder(1))//FT_FILIAL+FT_TIPOMOV+FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_ITEM+FT_PRODUTO
            If DbSeek(xFilial("SFT")+"S"+(cAliasSD2)->D2_SERIE+(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_CLIENTE+(cAliasSD2)->D2_LOJA+(cAliasSD2)->D2_ITEM)
            
                aadd(aRetSF3,{Len(aRetSF3)+1,;
                            IIF(lMvIssxMun .AND. !EMPTY(CE1->CE1_CNAE),CE1->CE1_CNAE,SFT->FT_CNAE),;
                            IIF(lMvIssxMun .AND. !EMPTY(CE1->CE1_TRIBMU),CE1->CE1_TRIBMU,SFT->FT_TRIBMUN),;
                            "",; // 4 - Código Beneficio Fiscal - NFS-e RJ IIF(SF4->(FieldPos(cMVBENEFRJ))> 0,SF4->(&(cMVBENEFRJ)),"" ) Manutenção preventiva, tirando o campo de Macro-execução da TES via SX6(Parâmetro).
                            IIF(lMvIssxMun .And. !Empty(CE1->CE1_CPRISS), CE1->CE1_CPRISS,IIF(SFT->(FieldPos("FT_CODISS"))<>0,SFT->FT_CODISS,"")); // Código de Serviço.
                    })
            EndIf		
                    
        EndIf	

        If !lAglutina .Or. Len(aProd) == 0
                                
            aadd(aProd,	{Len(aProd)+1,;
                        (cAliasSD2)->D2_COD,;
                        IIf(Val(SB1->B1_CODBAR)==0,"",Str(Val(SB1->B1_CODBAR),Len(SB1->B1_CODBAR),0)),;
                        IIF(Empty(SC6->C6_DESCRI),SB1->B1_DESC,SC6->C6_DESCRI),;
                        SB1->B1_POSIPI,;
                        SB1->B1_EX_NCM,;
                        (cAliasSD2)->D2_CF,;
                        SB1->B1_UM,;
                        (cAliasSD2)->D2_QUANT,;
                        a410Arred( FunValUnit((cAliasSD2)->D2_TIPO, (cAliasSD2)->D2_PRCVEN, (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_VALICM, (cAliasSD2)->D2_IDTRIB, (cAliasSD2)->D2_VALBRUT), FuCamArren(nCamPrcv,nCamQuan,nCamTot)),; //IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN,0),; // Valor unitário
                        IIF(Empty(SB5->B5_UMDIPI),SB1->B1_UM,SB5->B5_UMDIPI),;
                        IIF(Empty(SB5->B5_CONVDIP),(cAliasSD2)->D2_QUANT,SB5->B5_CONVDIP*(cAliasSD2)->D2_QUANT),;
                        (cAliasSD2)->D2_VALFRE,;
                        (cAliasSD2)->D2_SEGURO,;
                        ((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR),;
                        IIF(!(cAliasSD2)->D2_TIPO$"IP",(cAliasSD2)->D2_PRCVEN+If(cSigamat == "4205407",0,(((cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR)/(cAliasSD2)->D2_QUANT)),0),;								
                        IIF(SB1->(FieldPos("B1_CODSIMP"))<>0,SB1->B1_CODSIMP,""),; //codigo ANP do combustivel
                        IIF(SB1->(FieldPos("B1_CODIF"))<>0,SB1->B1_CODIF,""),; //CODIF
                        RetFldProd(SB1->B1_COD,"B1_CNAE"),;
                        SF3->F3_RECISS,;
                        SF3->F3_ISSSUB,;
                        SF3->F3_ISSMAT,;   
                        IIF(SB1->(FieldPos("B1_TRIBMUN"))<>0,RetFldProd(SB1->B1_COD,"B1_TRIBMUN"),""),;
                        IIF(lMvIssxMun .And. !Empty(CE1->CE1_CPRISS), CE1->CE1_CPRISS,IIF(SB1->(FieldPos("B1_CODISS"))<>0,RetFldProd(SB1->B1_COD,"B1_CODISS"),"")),; // Código de Serviço.
                        (cAliasSD2)->D2_BASEISS,;
                        (cAliasSD2)->D2_VALFRE,;
                        a410Arred( IIF(!(cAliasSD2)->D2_TIPO$"IP",If(cSigamat == "3550308",(cAliasSD2)->D2_PRCVEN * (cAliasSD2)->D2_QUANT,(cAliasSD2)->D2_TOTAL),0), FuCamArren(nCamPrcv,nCamQuan,nCamTot) ),; // Valor Liquido
                        a410Arred( FunValTot((cAliasSD2)->D2_TIPO,(cAliasSD2)->D2_PRCVEN, (cAliasSD2)->D2_QUANT, getValTotal(nValTotPrd,(cAliasSD2)->D2_TOTAL), (cAliasSD2)->D2_DESCON, (cAliasSD2)->D2_DESCZFR, (cAliasSD2)->D2_VALICM, (cAliasSD2)->D2_IDTRIB, (cAliasSD2)->D2_VALBRUT), FuCamArren(nCamPrcv,nCamQuan,nCamTot) ),; //Valor Total
                        getValDesc(lMvded, SF2->F2_CLIENTE, SF2->F2_LOJA, SF2->F2_DOC, SF2->F2_SERIE,(cAliasSD2)->D2_CODISS,(cAliasSD2)->D2_DESCON ),; //Valor Total de deducoes.
                        (cAliasSD2)->D2_VALIMP4,; //30
                        (cAliasSD2)->D2_VALIMP5,; //31
                        RetFldProd(SB1->B1_COD,"B1_TRIBMUN"),; //32
                        IIF(SF4->(FieldPos("F4_CFPS")) > 0,SF4->F4_CFPS,""),;//33 
						"",; // 34 - Código Beneficio Fiscal - NFS-e RJ IIF(SF4->(FieldPos(cMVBENEFRJ))> 0,SF4->(&(cMVBENEFRJ)),"" )
                        IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTIMP"))<>0,(cAliasSD2)->D2_TOTIMP,0),0),; //35 - Lei transparência
                        IIF(lMvred,IIF((cAliasSD2)->D2_BASEISS <> nValTotPrd, nValTotPrd - (cAliasSD2)->D2_BASEISS, (cAliasSD2)->D2_BASEISS),0),;	//Posicao para verifcar se existe reducao de ISS, será criado um campo na SFT para substituir esse calculo
                        IIF( SB1->(FieldPos("B1_MEPLES"))<>0, SB1->B1_MEPLES, "" ),; //37 - campo para NFSe Sao Paulo, identifica se eh Dentro do municipio ou fora.
                        IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTFED"))<>0,(cAliasSD2)->D2_TOTFED,0),0),; //38 - Lei transparência
                        IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTEST"))<>0,(cAliasSD2)->D2_TOTEST,0),0),; //39 - Lei transparência
                        IIF(lCrgTrib .And. cTpCliente == "F",IIF((cAliasSD2)->(FieldPos("D2_TOTMUN"))<>0,(cAliasSD2)->D2_TOTMUN,0),0),;  //40 - Lei transparência
                        IIF(SC6->(FieldPos("C6_DESCRI")) > 0,AllTrim(SC6->C6_DESCRI),""),	;	//41 - Descricao RPS SC6
                        (cAliasSD2)->D2_ITEM, ;//42 - Item da Nota
                        (cAliasSD2)->D2_ABATISS+(cAliasSD2)->D2_ABATMAT  ; //43 - Abatimento ISSQN
            })
        EndIf
        
        If SC6->(FieldPos("C6_TPDEDUZ")) > 0 .And. !Empty(SC6->C6_TPDEDUZ)
            aadd(aDeduz,{SC6->C6_TPDEDUZ,;
                            SC6->C6_MOTDED ,;
                            SC6->C6_FORDED ,;
                            SC6->C6_LOJDED ,;
                            SerieNfId("SC6",2,"C6_SERDED") ,;		            			 		            
                            SC6->C6_NFDED  ,;
                            SC6->C6_VLNFD  ,;
                            SC6->C6_PCDED  ,;
                            if ( SC6->C6_VLDED > 0  , SC6->C6_VLDED , ( SC6->C6_ABATISS + SC6->C6_ABATMAT ) ),;
                })
        endif

        //----------------------------------------------------------------------
        // Tratamento realizado para buscar o CST do ISS no campo do Livro.
        // Este campo FT_CSTISS nada mais eh conforme a configuracao na TES,
        // no campo F4_CSTISS.
        // Manteremos o legado D2_CLASFIS uma vez que estiver informado, mas
        // caso queira que o campo retorne do ISS, o campo FT_CSTISS precisara
        // estar alimentado.
        //
        // @Date: 07/06/2018
        // @Autor: Douglas Parreja				
        //----------------------------------------------------------------------
        If ( lConfTrib .And. oNfTciIntg:GetTax( (cAliasSD2)->D2_IDTRIB, "ISS") <> NIL .and. valtype(oNfTciIntg:GetTax( (cAliasSD2)->D2_IDTRIB, "ISS")["regras_escrituracao"]) == "J")
            cCST_SFT := oNfTciIntg:GetTax( (cAliasSD2)->D2_IDTRIB, "ISS")['dados_escriturados']['cst']
        Else
            dbSelectArea("SFT")				
            if SFT->( fieldPos("FT_CSTISS") ) > 0
                SFT->( dbSetOrder(1) ) //FT_FILIAL+FT_TIPOMOV+FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_ITEM+FT_PRODUTO
                if SFT->( dbSeek( xFilial("SFT") + "S" + (cAliasSD2)->D2_SERIE + (cAliasSD2)->D2_DOC + (cAliasSD2)->D2_CLIENTE + (cAliasSD2)->D2_LOJA) )
                    cCST_SFT 	:= ""
                    cOrigemSB1	:= ""
                    if !empty(SFT->(FT_CSTISS))
                        cCST_SFT := (SFT->(FT_CSTISS))						
                    endif
                endif					
            endif 
        EndIf
        //----------------------------------------------------------------------
        // aCST[] - Caso o B1_ORIGEM ou F4_SITTRIB um deles estejam preenchidos, 
        // o campo D2_CLASFIS ficara (b1_origem) "0  ", com isso, faco a validacao
        // do campo FT_CSTISS/B1_ORIGEM para verificar se esta preenchido.								
        //----------------------------------------------------------------------
        aadd(aCST, { IIF(!Empty((cAliasSD2)->D2_CLASFIS) .and. empty(cCST_SFT)	, SubStr((cAliasSD2)->D2_CLASFIS,2,2), iif(!empty(cCST_SFT)		, cCST_SFT		, '50')) } )				
        aadd(aICMS,{})
        aadd(aIPI,{})
        aadd(aICMSST,{})
        aadd(aPISST,{})
        aadd(aCOFINSST,{})
        //aadd(aISSQN,{0,0,0,"","",0})
        aadd(aAdi,{})
        aadd(aDi,{})				
        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³Tratamento para TAG Exportação quando existe a integração com a EEC     ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
        /*Alterações TQXWO2
        Na chamada da função, foram criados dois novos parâmetros: 
        o 3º referente ao código do produto e o 4º referente ao número da nota fiscal + série (chave).
        GetNfeExp(pProcesso, pPedido, cProduto, cChave)
        No retorno da função serão devolvidas as informações do legado, conforme leiaute anterior à versão 3.10 , 
        e as informações dos grupos “I03 - Produtos e Serviços / Grupo de Exportação” e “ZA - Informações de Comércio Exterior”, conforme estrutura da NT20013.005_v1.21.
        As posições 1 e 2 mantém o retorno das informações ZA02 e ZA03, mantendo o legado para os cliente que utilizam versão 2.00
        Na posição 3 passa a ser enviado o agrupamento do ID I50, tendo como filhos os IDs I51 e I52.
        Na posição 4 passa a ser enviado o agrupamento do ZA01, tendo como filhos os IDs ZA02, ZA03 e ZA04.
        Na posição 5 passa a ser enviado informaçãoes para o grupo "BA02 - Chaves Nfe referenciadas" as chaves de notas fiscais de saída de lote de exportação associadas à nota de saída de exportação.
        O array de retorno será multimensional, trazendo na primeira posição o identificador (ID), 
        na segunda posição a tag (o campo) e na terceira posição o conteúdo retornado do processo, 
        podendo ser um outro array com a mesma estrutura caso o ID possua abaixo de sua estrutura outros IDs. 						 				
        */
        /*Alterações TUSHX4
        Foi incluido o parametro D2_LOTECTL para que a função localize as notas de entrada (produto com lote e endereçamento) amarradas no pedido de exportção e consiga
        retornar o array de exportind de acordo com a quantidade de cada item da SD2, para não ocorrer a rejeição 
        346 Somatório das quantidades informadas na Exportação Indireta não correspondem a quantidade do item.*/

        If lEECFAT .And. !Empty((cAliasSD2)->D2_PREEMB)
            aadd(aExp,(GETNFEEXP((cAliasSD2)->D2_PREEMB,,(cAliasSD2)->D2_COD,(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_SERIE,(cAliasSD2)->D2_PEDIDO,(cAliasSD2)->D2_ITEMPV)))
        Elseif !Empty(SC5->C5_PEDEXP)
            aADD(aExp,(GETNFEEXP(,SC5->C5_PEDEXP,cCodProd,(cAliasSD2)->D2_DOC+(cAliasSD2)->D2_SERIE,(cAliasSD2)->D2_PEDIDO,(cAliasSD2)->D2_ITEMPV)))
        Else
            aadd(aExp,{})
        EndIf
            
        If AliasIndic("CD7")
            aadd(aMed,{CD7->CD7_LOTE,CD7->CD7_QTDLOT,CD7->CD7_FABRIC,CD7->CD7_VALID,CD7->CD7_PRECO})
        Else
            aadd(aMed,{})
        EndIf
        If AliasIndic("CD8")
            aadd(aArma,{CD8->CD8_TPARMA,CD8->CD8_NUMARM,CD8->CD8_DESCR})                       
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
                    Iif(SF2->(FieldPos("F2_VALINSS")) <> 0 .and. SF2->F2_VALINSS > 0, (cAliasSD2)->D2_VALINS, 0) + Iif(Len(aRetISS) >= nCont, aRetISS[nCont], 0)
                    
        aTotal[01] += (cAliasSD2)->D2_DESPESA
        aTotal[02] += getValTotal(nValTotPrd,(cAliasSD2)->D2_TOTAL)
        If ( lConfTrib .And. oISSCfg <> NIL  .Or. SF4->( FieldPos("F4_ISSST") == 0 ))
            aTotal[03] :=  Alltrim(SF4->F4_NATOPNF) //NATUREZA DE OPERACAO DA NFSe
            lConfTrIss := .T. 
        Else
            aTotal[03] := Alltrim(SF4->F4_ISSST)
            lConfTrIss := .F. 
        EndIf

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
        
        If (cAliasSD2)->D2_DESCON > 0
            nDescon += (cAliasSD2)->D2_DESCON
        EndIf	

        If  ( lConfTrib .And. oNfTciIntg:GetTax((cAliasSD2)->D2_IDTRIB, "ISS") <> NIL .and. valtype(oNfTciIntg:GetTax( (cAliasSD2)->D2_IDTRIB, "ISS")["regras_base"]) == "J")
            If ( oNfTciIntg:GetBaseTax((cAliasSD2)->D2_IDTRIB, "ISS")['acao_desconto'] $ "1" .And. (cAliasSD2)->D2_DESCON > 0  .Or. oNfTciIntg:GetBaseTax((cAliasSD2)->D2_IDTRIB, "ISS")['acao_icms_desonerado'] $ "2" ) 
                lDescCond := .T.
            EndIf    
        EndIf
        
        dbSelectArea(cAliasSD2)
        dbSkip()
    EndDo

    /*/-----------------------------------------------------------------------
        Destruir os objetos e arrays da classe TSSTCIntegration após o término do loop.
        @since 11/02/2025
        @version 12.1.2410
    /*///-----------------------------------------------------------------------
    //DestroyTCI(@oNfTciIntg) // Destruir o objeto depois para uso na função valoresNac
 
    If lQuery
        dbSelectArea(cAliasSD2)
        dbCloseArea()
        dbSelectArea("SD2")
    EndIf

EndIf

return 

//-----------------------------------------------------------------------
/*/{Protheus.doc} ident
Função para montar a tag de identificação do XML no Layout NFS-e Nacional ao TSS.

@author Felipe Duarte Luna
@since 25.10.2023

@param	aNota	  Array com informações sobre a nota.
@param	cAmbiente Identificacao do Ambiente : 1 - Producao ou 2 - Homologacao 
@param	cLocEmi	  Código de Município Emissora da NFS-e

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function identNac( aNota, cAmbiente , cLocEmi)

	Local	cString		:= ""
    Local   cNamesPace  := "http://www.sped.fazenda.gov.br/nfse"
    Local   cVersaoNFSe := GetVerParTSS(getCfgEntidade())
    Local   cIdDps      := getIdDps(aNota)
    Local   cverAplic   := "TOTVS-TSS-3.00"
    Local   ctpEmit     := "1" //Emitente da DPS: 1 - Prestador; 2 - Tomador;3 - Intermediário;
    
    Default cLocEmi     := if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN )
    Default cAmbiente   := 2

	cString	:= '<DPS xmlns="'+cNamesPace+'" versao="'+cVersaoNFSe+'">'
    cString	+= '<infDPS xmlns="'+cNamesPace+'" Id="'+cIdDps+'">'
    cString	+= '<tpAmb>'+ cAmbiente +"</tpAmb>"
    cString	+= "<dhEmi>" + subStr( dToS( aNota[3] ), 1, 4 ) + "-" + subStr( dToS( aNota[3] ), 5, 2 ) + "-" + subStr( Dtos( aNota[3] ), 7, 2 ) + 'T' + aNota[9] + '-03:00'+ "</dhEmi>"
    cString	+= '<verAplic>'+ cverAplic +"</verAplic>"
    cString	+= '<serie>'+ AllTrim(aNota[1]) +"</serie>"
    cString	+= '<nDPS>'+ AllTrim(str(val(aNota[2]))) +"</nDPS>"
    cString	+= '<dCompet>'+ subStr( dToS( aNota[3] ), 1, 4 ) + "-" + subStr( dToS( aNota[3] ), 5, 2 ) + "-" + subStr( Dtos( aNota[3] ), 7, 2 ) +"</dCompet>"
    cString	+= '<tpEmit>'+ ctpEmit +"</tpEmit>"
    cString	+= '<cLocEmi>'+ cLocEmi +"</cLocEmi>"	
	
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
			cNovo := allTrim( encodeUTF8( subStr( xValor, 1, nTam ) ) )
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
	
	// Campo ENDNOT indica que endereco participante mao esta no formato <logradouro>, <numero> <complemento>
	// Se tiver com 'S' somente o campo de logradouro sera atualizado (numero sera SN)
	if ( ( cAlias )->( FieldPos( cCmpEndN ) ) > 0 .And. &( cAlias + "->" + cCmpEndN ) == "1" )
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
/*/{Protheus.doc} RetTipoLogr
Função que retorna os tipos de logradouro do prestador/tomador

@author Natalia Sartori
@since 08/01/2013
@version 1.0 

@param	cTexto		Tipo do Logradouro

@return	cTipoLogr	Retorna a descrição do Tipo do Logradouro
/*/
//-----------------------------------------------------------------------
Static Function RetTipoLogr( cTexto )

Local cTipoLogr:= ""
Local cAbrev	 := ""
Local nX       := 0
Local nAt		 := 0 
Local aMsg     := {}

aadd(aMsg,{"1", "Av"})			// Avenida
aadd(aMsg,{"2", "Rua"})			// Rua
aadd(aMsg,{"3", "Rod"})			// Rodovia
aadd(aMsg,{"4", "Ruela"})
aadd(aMsg,{"5", "Rio"})
aadd(aMsg,{"6", "Sitio"})
aadd(aMsg,{"7", "Sup Quadra"})
aadd(aMsg,{"8", "Travessa"})
aadd(aMsg,{"9", "Vale"})
aadd(aMsg,{"10","Via"})			// Via
aadd(aMsg,{"11","Vd"}) 			// Viaduto
aadd(aMsg,{"12","Ve"}) 			// Viela
aadd(aMsg,{"13","Vila"})
aadd(aMsg,{"14","Vargem"})			// Vargem
aadd(aMsg,{"15","Al"})			// Alameda
aadd(aMsg,{"16","Pc"})			// Praça	
aadd(aMsg,{"17","Bc"})			// Beco
aadd(aMsg,{"18","Tv"})			// Travessa
aadd(aMsg,{"19","Vel"})			// Via Elevada
aadd(aMsg,{"20","Pq"})			// Parque
aadd(aMsg,{"21","Lg"})			// Largo
aadd(aMsg,{"22","Vep"})			// Viela Particular
aadd(aMsg,{"23","Pa"})			// Pátio
aadd(aMsg,{"24","Ves"})			// Viela Sanitária
aadd(aMsg,{"25","Ld"})			// Ladeira
aadd(aMsg,{"26","Jd"})			// Jardim
aadd(aMsg,{"27","Es"})			// Estrada
aadd(aMsg,{"28","Pte"})			// Ponte
aadd(aMsg,{"29","Rp"})			// Rua Particular
aadd(aMsg,{"30","Praia"})

nAt := At(" ", UPPER(cTexto))
cAbrev := substr(UPPER(cTexto), 1, nAt-1)

nX := aScan(aMsg,{|x| UPPER(x[2]) $ cAbrev})
If nX == 0
	cTipoLogr := "2"
Else
	cTipoLogr := aMsg[nX][1]
EndIf

Return cTipoLogr

//-----------------------------------------------------------------------
/*/{Protheus.doc} RatValImp
Realiza a proporcionalidade do Valor do imposto aglutinado

@author Rene Julian
@since 17/03/2015
@version 1.0 

@param	cTexto		Tipo do Logradouro

@return	cTipoLogr	Retorna a descrição do Tipo do Logradouro
/*/
//-----------------------------------------------------------------------
Static Function RatValImp(aRetido,nScan,aProd,nProd,aRestImp)
Local nRetorno  := 0
Local nValimp   := 0
Local nValitens := 0
Local nValtot   := 0
Local nDifVal   := 0
Local nX       := 0
Local nPos      := aScan(aRestImp,{|x| x[1] == nScan})


If Len(aRetido[nScan][5]) > 0 
	For nX := 1 To Len(aRetido[nScan][5])
		nValitens += aRetido[nScan][5][nX]
	Next nX
	nDifVal := aRetido[nScan][3] - nValitens 
	For nX := 1 To Len(aProd)
		nValtot += aProd[nX][28]  
	Next nX
	nValimp := (nDifVal / nValtot) * aProd[nProd][28]	
EndIf

If nPos == 0
	AADD(aRestImp,{nScan,nValimp - noRound(nValimp,2)})
	nRetorno := noRound(nValImp)
Else
	nValImp:= nValImp + aRestImp[nPos][2]            
	nRetorno := noRound(nValImp)
	aRestImp[nPos][2] := nValimp - noRound(nValimp,2)
EndIf 
Return(nRetorno)

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

//--------------------------------------------------

/*/{Protheus.doc} FunValUnit
Retorna o valor total

@author Karyna Morato
@since 12/07/2016
@version 1.0 

@param	cTipo		Tipo do item
		nPrcVen 	Valor unitário do item
		

@return nTotal 	Valor total
/*/
//-------------------------------------------------------------------  

Static Function FunValUnit(cTipo, nPrcVen, nQtde,nValIss, cNFIdTrib, nValBrut)

Local nTotal := 0 

/* Conforme alinhado com Renato Panfietti e Felipe Barbieri o TMS sempre trabalha com quantidade "1",
sendo assim, será apenas somado o preco de venda com o valor icms(referente a valor do ISS)
*/
If !cTipo $ "IP"
	If IntTMS() // Soma o valor ISS quando a nota é do TMS
		If ( lConfTrib .And. oNfTciIntg:GetTax( cNFIdTrib, "ISS") <> NIL .and. valtype(oNfTciIntg:GetTax( (cAliasSD2)->D2_IDTRIB, "ISS")["regras_escrituracao"]) == "J" .And. oNfTciIntg:GetEscrituracaoRuleTax(cNFIdTrib, "ISS")['acao_total_nf'] $ "5-6" )
            nTotal := nValBrut //nPrcVen + nValIss
        ElseIf SF4->(FieldPos("F4_AGRISS")) > 0  .And. nQtde == 1 .And. SF4->F4_AGRISS == '1'
			nTotal := nPrcVen + nValIss
        Else
		   nTotal := nPrcVen
		EndIf
	Else
		nTotal := nPrcVen 	 
	EndIf
EndIf

Return nTotal
//--------------------------------------------------

/*/{Protheus.doc} FunValTot
Retorna o valor total

@author Karyna Morato
@since 12/07/2016
@version 1.0 

@param	cTipo		Tipo do item
		nPrcVen 	Valor unitário do item
		nQtde		Quantidade do item
		nTotDoc	Valor total do item
		nDescon	Desconto do item
		nDesczfr	Desconto
		nValIss	Valor do ISS

@return nTotal 	Valor total
/*/
//-------------------------------------------------------------------  

Static Function FunValTot(cTipo,nPrcVen, nQtde, nTotDoc, nDescon, nDesczfr, nValIss, cNFIdTrib, nValBrut)
				  
Local nTotal	:= 0 
Local lMvtot	:= SuperGetMV("MV_NFSETOT",,.F.) // Parâmetro para somar o desconto no valor total


If !cTipo $ "IP"
	
	If if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN ) == "3550308"
		nTotal := nPrcVen * nQtde
	Else
		nTotal := nTotDoc
	EndIf
	
	//----------------------------------------------------------------
	// Realizado ajuste para considerar uma unica vez a soma 
	// no desconto (D2_DESCON + D2_DESCZFR)
	// @autor: Douglas Parreja
	// @date: 29/03/2018
	//----------------------------------------------------------------
	If lMvtot //!SM0->M0_CODMUN $ "4205407-3148103"
		nTotal += nDescon + nDesczfr
	EndIf
	
	// Soma o valor ISS quando a nota é do TMS
	If IntTMS()
        If ( lConfTrib .And. oNfTciIntg:GetTax( cNFIdTrib, "ISS") <> NIL .and. valtype(oNfTciIntg:GetTax( (cAliasSD2)->D2_IDTRIB, "ISS")["regras_escrituracao"]) == "J" .And. oNfTciIntg:GetEscrituracaoRuleTax(cNFIdTrib, "ISS")['acao_total_nf'] $ "5-6" )
            nTotal := nValBrut //nPrcVen + nValIss
        ElseIf ( SF4->(FieldPos("F4_AGRISS")) > 0 .And. SF4->F4_AGRISS == '1' )
            nTotal += nValIss
        EndIf
	EndIf

EndIf

Return nTotal
//--------------------------------------------------

/*/{Protheus.doc} FuCamArren
Retorna o campo correto para a funcao A410Arred 

@author Fernando Bastos 
@since 03/08/2017
@version 1.0 

@param	cCamPrcv	valor do campo D2_PRCVEN
		cCamQuan	valor do campo D2_QUANT
		cCamTot	valor do campo D2_TOTAL

@return cCampo 	Campo para a funcao A410Arred
/*/
//-------------------------------------------------------------------  
Static Function FuCamArren(nCamPrcv,nCamQuan,nCamTot)

//Para entender essa funcao olhar o fonte fatxfun.prx funcao A410Arred  
//Parametro MV_ARREFAT de arredondamento 

Local cCampo 	:= ""

Default nCamPrcv	:= 2 
Default nCamQuan	:= 2
Default nCamTot	:= 2
 	  
If nCamQuan > nCamPrcv .And. nCamQuan > nCamTot 
	cCampo := "D2_QUANT"
ElseIf nCamPrcv > nCamQuan  .And. nCamPrcv > nCamTot
	cCampo := "D2_PRCVEN"
Else
	cCampo := "D2_TOTAL"
EndIf

Return cCampo

//----------------------------------------------------------------------
/*/{Protheus.doc} ClearTLogr
Funcao que define se leva ou não o tipo  do Logradouro do logradouro
@author Valter Silva
@since 23.10.2017
@version 1.0 

@param		cLogradour  	Parâmetro com a informações do Logradouro.
@return	cLogradour     Logradouro com ou sem o tipo de logradouro de acordo com Parâmetro "MV_TIPLOGR".
@obs		
/*/
//------------------------------------------------------------------- 
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
			cLogr := "Vila "	
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

//--------------------------------------------------
/*/{Protheus.doc} GetTitNat
Função utilizada para buscar a natureza do título da nota

@author paulo.barbosa
@since 14/12/2017
@version 1.0 

@param cNota, char, Numero do documento
@param cSerie, char, Série do documento
@param cCliente, char, Codigo do cliente do documento
@param cLoja, char, Codigo da loja do cliente do documento

@return cRet, char, Natureza fiscal do título
/*/
//-------------------------------------------------------------------
Static Function GetTitNat(cNota, cSerie, cCliente, cLoja)
Local cRet       := ""
Local cAliasAux  := GetNextAlias()

BeginSql Alias cAliasAux
	SELECT E1_NATUREZ
	FROM %Table:SE1% SE1
	WHERE E1_FILIAL = %xFilial:SE1%
		AND E1_NUM = %Exp:cNota%
		AND E1_PREFIXO = %Exp:cSerie%
		AND E1_TIPO = %Exp:MVNOTAFIS%
		AND E1_CLIENTE = %Exp:cCliente%
		AND E1_LOJA = %Exp:cLoja%
		AND SE1.%notDel%
EndSql

If ( cAliasAux )->( !EOF() )
	cRet := (cAliasAux)->E1_NATUREZ
EndIf

(cAliasAux)->( dbCloseArea() )

Return cRet

//-----------------------------------------------------------------------
/*/{Protheus.doc} getValTotal
Funcao responsavel por retornar o valor com ou sem desconto.

@param	nValTotPed		Valor total do Pedido.
		nSD2_TOTAL		Valor gravado com abatimento do desconto.

@return	nValor			Valor retornado conforme municipio, caso 
						nao seja informado, mantera o legado.
            
@author Douglas Parreja
@since  16/08/2018
@version 3.0 
/*/
//-----------------------------------------------------------------------
static function getValTotal( nValTotPed, nSD2_TOTAL )

	local lValSemDesc		:= .F.
    local lMvtot	        := SuperGetMV("MV_NFSETOT",,.F.) // Parâmetro para somar o desconto no valor total
	default nValTotPed		:= 0
	default nSD2_TOTAL		:= 0



	//------------------------------------------------------
	// Municipio a ser retornado valor total sem Desconto
	//------------------------------------------------------
	if( (valtype("nValTotPed") <> "U") .and. (valtype("nSD2_TOTAL") <> "U") )
		if( (valtype(nValTotPed) == "N") .and. (valtype(nSD2_TOTAL) == "N") ) 
			if( iif( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN ) $ "2927408" ) .or. (lMvtot  .and. lMvDescInc )
				lValSemDesc := .T.
			endif
		endif	
	endif
		
return iif( lValSemDesc, nValTotPed, nSD2_TOTAL )


//-----------------------------------------------------------------------
/*/{Protheus.doc} getValDesc
Funcao responsavel por retornar a somatoria do Desconto.

@param		lMvded			Parametro Habilita/Desabilita as Deducoes da NFSE.
			cCliente		Codigo do Cliente
			cLoja			Codigo da loja
			cNota			Numero do documento 
			cSerie			Serie do documento
			cCodISS		Codigo do servico
			nSD2Desc		Valor do desconto na tabela SD2.
			
@return	nValor			Valor do documento.

            
@author Douglas Parreja
@since  04/09/2018
@version 3.0 
/*/
//-----------------------------------------------------------------------
static function getValDesc(lMvded, cCliente, cLoja, cNota, cSerie, cCodISS, nSD2Desc )
							
	local nRet			:= 0
	local nValor		:= 0
	local cAliasSF3	:= GetNextAlias()
									
	default lMvded	:= .F.
	default cCliente 	:= ""
	default cloja		:= ""
	default cNota		:= ""
	default cSerie	:= ""
	default cCodISS	:= ""
	default nSD2Desc	:= 0
	
	dbSelectArea("SF3")
	SF3->(dbSetOrder(4))
	if ( dbSeek(xFilial("SF3")+cCliente+cloja+cNota+cSerie) )		
		//---------------------------------------------------------------
		// Hoje o processo existente eh gerar um registro na tabela SF3 
		// para N registros na tabela SD2, principalmente quando houver
		// aglutinacao, considerando Codigo Servico + Aliquota + 
		// Codigo tributacao municipio.
		// Neste cenario, somente retornara o valor da primeira vez.
		//---------------------------------------------------------------		
		if ( nCountSF3 == 0 )		
									
			BeginSql Alias cAliasSF3
			select COUNT(*) NCOUNT
			FROM %Table:SF3% SF3
			WHERE SF3.F3_CLIEFOR= %Exp:cCliente%
					AND SF3.F3_LOJA = %Exp:cLoja%
					AND SF3.F3_NFISCAL = %Exp:cNota%
					AND SF3.F3_SERIE = %Exp:cSerie%
					AND SF3.F3_CODISS = %Exp:cCodISS%
					AND SF3.%notDel%
			EndSql
			//---------------------------------------------------------------		
			// Retorno da quantidade de registros com mesmo cod.servico
			//---------------------------------------------------------------		
			if ( cAliasSF3 )->( !EOF() )
				nRet := (cAliasSF3)->NCOUNT				
			endif															
			(cAliasSF3)->( dbCloseArea() )
		
			//---------------------------------------------------------------
			// Processo para retorno do valor a ser calculado
			//---------------------------------------------------------------				
			if ( valtype(nValor) == "N" )		
				if ( nRet > 0 )	
					if ( nRet == 1  .and. lMvded )																																			
						if ( nSD2Desc > 0 )
							nValor += SF3->F3_ISSSUB + SF3->F3_ISSMAT + nSD2Desc
						else
							nValor += SF3->F3_ISSSUB + SF3->F3_ISSMAT
						endif		
						nCountSF3++		
					//else
						// Funcao para realizar possivel tratamento quando houver mais de 1 registro na SF3.						
					endif
				endif
			endif
		endif							
	endif
	
return ( nValor )

//-----------------------------------------------------------------------
/*/{Protheus.doc} IsRPSLOJA
Verifica se é venda de serviço (RPS) originada do SIGALOJA (Varejo) e retorna as informações 
do local da prestação do serviço.

@author Totvs
@since 19/06/2019
@version 1.0 
@param	aEndPres	Array passado por referência para que seja alimentado com as informações do endereço de prestação do serviço.
@return	lRet		Verifica se é venda de serviço (RPS) originada do SIGALOJA (Varejo)
@obs		
/*/
//-----------------------------------------------------------------------
Static Function IsRPSLOJA(aEndPres)
Local lRet 			:= .F.
Local aFldEndPre	:= {} //Parametro que aponta para os campos da tabela SL1 para pegar as informações do endereço da prestação do serviço
Local nX 			:= 0
Local cField 		:= ""
Local uValue 		:= Nil

/*
Ordem dos campos da tabela SL1 configurados no parâmetro MV_LJENDPS:
01-Endereço Prest. Serviço
02-Núm. End. Prest. Serviço
03-Comp. End. Prest. Serviço
04-Bairro Prestação Serviço
05-UF Prestação Serviço
06-CEP Prestação Serviço
07-Código Mun. Pres. Serviço
08-Descr. Mun. Pres. Serviço
09-País Prestação Serviço
*/

If !Empty(SF2->F2_NUMORC) //Se este campo estiver alimentado significa que é uma venda de RPS originada do SIGALOJA (Varejo)
	
	aFldEndPre	:= &(SuperGetMV("MV_LJENDPS",,"{,,,,,,,,}")) //Parametro que aponta para os campos da tabela SL1 para pegar as informações do endereço da prestação do serviço

	If ValType(aFldEndPre) <> "A"
		aFldEndPre := {}
	EndIf

	//Ajusta o array para que tenha a quantidade certa de 9 posições
	aSize(aFldEndPre, 9)
	For nX:=1 To Len(aFldEndPre)
		If aFldEndPre[nX] == Nil
			aFldEndPre[nX] := ""
		EndIf
	Next nX

	DbSelectArea("SL1")
	SL1->(DbSetOrder(1)) //L1_FILIAL+L1_NUM
	If SL1->(DbSeek(xFilial("SL1")+SF2->F2_NUMORC))
		
		lRet 	 := .T.
		aEndPres := {}

		For nX:=1 To Len(aFldEndPre)
			cField := aFldEndPre[nX]
			uValue := ""
			If !Empty(cField)
				If SL1->(ColumnPos(aFldEndPre[nX])) > 0
					uValue := SL1->&(cField)
				EndIf
			EndIf

			aAdd( aEndPres, uValue )
		Next nX

	EndIf

EndIf

Return lRet

//-----------------------------------------------------------------------
/*/{Protheus.doc} getIdDps
Função para pegar partes do DDD e Telefone de uma única String.

@author Felipe Duarte Luna
@since 25.10.2023

@param	aNota	Array com informações sobre a nota.

@return	cString		Retorna as Tag's DDD + Telefone preenchida respectivamente.
/*/
//-----------------------------------------------------------------------
static function getIdDps( aNota )
	
	Local cString     := ""
    Local cCodMun     := if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN )
    Local ntipoInsc   := if( type( "oSigamatX" ) == "U",SM0->M0_TPINSC,oSigamatX:M0_TPINSC )
    Local cInscFed    := if( type( "oSigamatX" ) == "U",SM0->M0_CGC,oSigamatX:M0_CGC )
    Local cSerieDps   := AllTrim( strZero( val( Alltrim(aNota[1]) ),5 ) )
    Local cNumDps     := AllTrim( strZero( val( Alltrim(aNota[2]) ),15 ) )
    
    If ntipoInsc == 3 //CPF
        cInscFed := AllTrim( strZero( val( cInscFed ),14 ) )
    EndIf

    cString	+='DPS'+cCodMun+cValToChar(ntipoInsc)+cInscFed+cSerieDps+cNumDps
	
return cString 

//-----------------------------------------------------------------------
/*/{Protheus.doc} substit
Função para montar a tag de substituição do XML de envio de NFS-e ao TSS.

@author Felipe Duarte Luna
@since 26.10.2023

@param	aNota	Array com informações sobre a nota.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------

/*
static function substit( aNota )
	
	Local	cString	:= ""
	
	If !empty( allTrim( aNota[8] ) + allTrim( aNota[7] ) )
		
		cString	+= "<subst>"
		cString	+= "<chSubstda>" + allTrim(aNota[8]) + "</chSubstda>"
		cString	+= "<cMotivo>" + allTrim(str( val(aNota[7]))) + "</cMotivo>"
		cString	+= "<xMotivo>" + aNota[8] + allTrim(aNota[7]) + "</xMotivo>"		
		cString	+= "</subst>"		
	Endif
	
return cString
*/

//-----------------------------------------------------------------------
/*/{Protheus.doc} prest
Função para montar a tag de prestador do XML de envio de NFS-e ao TSS.

@author Felipe Duarte Luna
@since 26.10.2023

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function prestNac()
	
	Local	cString			:= ""
    Local	cCpfCnpj		:= if( type( "oSigamatX" ) == "U",SM0->M0_CGC,oSigamatX:M0_CGC )
    Local	cIM		        := IIF( lImNac ,if( type( "oSigamatX" ) == "U",SM0->M0_INSCM,oSigamatX:M0_INSCM ),"" )
    //Local	cNome			:= if( type( "oSigamatX" ) == "U",SM0->M0_NOMECOM,oSigamatX:M0_NOMECOM )
    //Local	cCodMun			:= if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN )
    //Local	cCep			:= if( type( "oSigamatX" ) == "U",SM0->M0_CEPCOB,oSigamatX:M0_CEPCOB )
    //Local	cEndereco		:= if( type( "oSigamatX" ) == "U",SM0->M0_ENDCOB,oSigamatX:M0_ENDCOB )
    //Local	cCompLgr		:= if( type( "oSigamatX" ) == "U",SM0->M0_COMPCOB,oSigamatX:M0_COMPCOB )
    //Local	cBairro			:= if( type( "oSigamatX" ) == "U",SM0->M0_BAIRCOB,oSigamatX:M0_BAIRCOB )
    Local	cfone			:= if( type( "oSigamatX" ) == "U",SM0->M0_TEL,oSigamatX:M0_TEL )
    Local   ntipoInsc       := if( type( "oSigamatX" ) == "U",SM0->M0_TPINSC,oSigamatX:M0_TPINSC )
    //Local	aEndereco		:= fisGetEnd( cEndereco )
    	
	//Local	cMVINCECUL		:= allTrim( getMV( "MV_INCECUL",, "2" ) )
	Local	cMVOPTSIMP		:= allTrim( getMV( "MV_OPTSIMP",, "2" ) )
    Local	cMVREGIESP      := allTrim( getMV( "MV_REGIESP",, " " ) )
	//Local	cMVNUMPROC		:= allTrim( getMV( "MV_NUMPROC",, " " ) )
	Local   cEmail			:= allTrim( getMV( "MV_EMAILPT",, " " ) )
	//Local	cMVDTINISI		:= allTrim( getMV( "MV_DTINISI",, " " ) )
    Local   cMVREGTSN		:= allTrim( getMV( "MV_REGTRSN",, "1" ) )
    
    cEmail := StrTran(cEmail,".T.","")
    
    cString	+= "<prest>"
    cString	+= IIf(ntipoInsc == 3, '<CPF>'+ cCpfCnpj +"</CPF>", '<CNPJ>'+ cCpfCnpj +"</CNPJ>" )
    //cString	+= '<NIF>'+ cAmbiente +"</NIF>"
    //cString	+= '<cNaoNIF>'+ cAmbiente +"</cNaoNIF>"
    //cString	+= '<CAEPF>'+ cAmbiente +"</CAEPF>"
    cString	+= IIF(!empty(AllTrim(cIM)),'<IM>'+ AllTrim(cIM) +"</IM>","")
    //cString	+= '<xNome>'+ AllTrim(cNome) +"</xNome>"
    //cString	+= "<end>"
    //cString	+= "<endNac>"
    //cString	+= '<cMun>'+ cCodMun +"</cMun>
    //cString	+= '<CEP>'+ AllTrim(cCep) +"</CEP>
    //cString += "</endNac>"
    //cString	+= '<xLgr>'+ AllTrim(ClearTLogr(AllTrim(aEndereco[1]))) +"</xLgr>"
    //cString	+= '<nro>'+ AllTrim(aEndereco[3]) +"</nro>"
    //cString	+= IIF( !EMPTY( AllTrim(cCompLgr) ),'<xCpl>'+ AllTrim(cCompLgr) +'</xCpl>',"")
    //cString	+= '<xBairro>'+ AllTrim(cBairro) +"</xBairro>"
    //cString	+= "</end>"
    cString	+= '<fone>'+ AllTrim(cfone) +"</fone>"
    cString	+= IIf(!Empty(cEmail), "<email>" + cEmail + "</email>", "")
    cString	+= "<regTrib>"

    if cMVOPTSIMP == "1" .and. !empty(cMVREGIESP) .and. cMVREGIESP == "6" //Simples nacional e Regime Especial de Tributacao Microempresário e Empresa de Pequeno Porte (ME EPP)
        cString	+= '<opSimpNac>'+ cValToChar(3) +"</opSimpNac>"
    elseif cMVOPTSIMP == "1" .and. !empty(cMVREGIESP) .and. cMVREGIESP == "5" //Simples nacional e Regime Especial de Tributacao Microempresário Individual (MEI)
        cString	+= '<opSimpNac>'+ cValToChar(2) +"</opSimpNac>"
    else
        cString	+= '<opSimpNac>'+ cValToChar(1) +"</opSimpNac>"
    endif

    if cMVOPTSIMP == "1"
        If cMVREGTSN == "1"
            cString += '<regApTribSN>'+ cValToChar(1) +"</regApTribSN>" //Regime de apuração dos tributos federais e municipal pelo SN;
        ElseIf cMVREGTSN == "2"
            cString += '<regApTribSN>'+ cValToChar(2) +"</regApTribSN>" //Regime de apuração dos tributos federais pelo SN e ISSQN por fora do SN conforme respectiva legislação municipal do tributo;
        ElseIf cMVREGTSN == "3"
            cString += '<regApTribSN>'+ cValToChar(3) +"</regApTribSN>" //Regime de apuração dos tributos federais e municipal por fora do SN conforme respectivas legilações federal e municipal de cada tributo.
        endif
    endif
    //Tipos de Regimes Especiais de Tributação NFS-e nacional:0 - Nenhum; 1 - Ato Cooperado (Cooperativa); 2 - Estimativa; 3 - Microempresa Municipal; 4 - Notário ou Registrador; 5 - Profissional Autônomo; 6 - Sociedade de Profissionais; 9 - Outros;
    if !empty(cMVREGIESP) .and. cMVREGIESP == "4"                   //Cooperativa;
        cString	+= '<regEspTrib>'+ cValToChar(1) +"</regEspTrib>"
    elseif !empty(cMVREGIESP) .and. cMVREGIESP == "2"               //Estimativa
        cString	+= '<regEspTrib>'+ cValToChar(2) +"</regEspTrib>"
    elseif !empty(cMVREGIESP) .and. cMVREGIESP == "1"               //Microempresa Municipal
        cString	+= '<regEspTrib>'+ cValToChar(3) +"</regEspTrib>"
    elseif !empty(cMVREGIESP) .and. cMVREGIESP == "7"               //Proficional Autônomo 
        cString	+= '<regEspTrib>'+ cValToChar(5) +"</regEspTrib>"
    elseif !empty(cMVREGIESP) .and. cMVREGIESP == "3"               //Sociedade de Profissionais
        cString	+= '<regEspTrib>'+ cValToChar(6) +"</regEspTrib>"
    elseif !empty(cMVREGIESP) .and. cMVREGIESP == "6"               //ME EPP -- Conforme manual no NFSE Nac, o valor dessa tag deveria ser 3, 
        cString += '<regEspTrib>'+ cValToChar(0) +"</regEspTrib>"   //porém o ambiente de produção está em desacordo com o manual.
    elseif !empty(cMVREGIESP) .and. cMVREGIESP == "14"              // outros, quando se enquadrar em algum dos outros tipos de regimes especiais de tributação previstos no art. 17 da LC 123/2006, ou seja, os códigos de 1 a 6 e 9, conforme o caso.
        cString += '<regEspTrib>'+ cValToChar(9) +"</regEspTrib>"
    else 
        cString	+= '<regEspTrib>'+ cValToChar(0) +"</regEspTrib>"    //Nenhuma - Para atender a gera da tag Obrigatoria
    endif
    // Ja estavam criadas no processos enolvidos Protheus as seguintes conteudos para parametro MV_ REGIESP:Regime especial de tributação do documento.
    /*   Os conteúdos possíveis são:
            0 – Tributação Normal
            1 – Microempresa Municipal (ME);
            2 – Estimativa;
            3 – Sociedade de Profissionais;
            4 – Cooperativa;
            5 – Microempresário Individual (MEI);
            6 – Microempresário e Empresa de Pequeno Porte (ME EPP).
            7 - Movimento Mensal/ISS/Fixo Autônomo;
            8 - Sociedade Limitada/Média Empresa;
            9 - Sociedade Anônima/Grande Empresa;
            11 - Empresa Individual;
            10 - Empresa Individual de Responsabilidade Limitada (EIRELI);
            12 - Empresa de Pequeno Porte (EPP);
            13 - Microempresário;
            14 - Outros/Sem Vínculos;
            50 - Nenhum;
            51 - Nota Avulsa.*/

    cString	+= "</regTrib>"
    cString	+= "</prest>"
    		
return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} tomador
Função para montar a tag de tomador do XML de envio de NFS-e Nacional ao TSS.

@author Renan Botelho  
@since 26.10.2023

@param	aDest	Array com as informações do tomador da nota.

    aDest[1] SA1->A1_CGC
    aDest[2] SA1->A1_NOME
    aDest[3] SA1->A1_END
    aDest[4] NUMERO DO CAMPO SA1->A1_END
    aDest[5] SA1->A1_COMPLEM
    aDest[6] SA1->A1_BAIRRO
    aDest[7] SA1->A1_COD_MUN
    aDest[8] SA1->A1_MUN
    aDest[9] SA1->A1_EST
    aDest[10] SA1->A1_CEP
    aDest[11] SYA->YA_SISEXP - NUMERO
    aDest[12] SYA->YA_DESCR - BRASIL
    aDest[13] SA1->A1_DDD+SA1->A1_TEL
    aDest[14] SA1->A1_INSCR
    aDest[15] SA1->A1_SUFRAMA
    aDest[16] SA1->A1_EMAIL
    aDest[17] SA1->A1_INSCRM
    aDest[18] SA1->A1_CODSIAF
    aDest[19] SA1->A1_NATUREZ
    aDest[20] SA1->A1_SIMPNAC
    aDest[21] SA1->A1_INCULT
    aDest[22] SA1->A1_TPESSOA
    aDest[23] SF2->F2_DOC
    aDest[25] SF2->F2_SERIE
    aDest[25] SA1->A1_OUTRMUN
    aDest[26] SA1->A1_PFISICA
    aDest[27] SA1->A1_TIPO
    aDest[28] SA1->A1_NIF

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function tomadorNac( aDest, cCodMun )
	
    Local cString	:= ""
    Local lSemTomador   := .F.
    Local cPaisIso  := Tsspais(allTrim( aDest[11]) )
	default cCodMun := ""

    If Empty(aDest[1]) .and. Empty(aDest[2])
        lSemTomador:=.T.
    EndIf

    If !lSemTomador

        cString	+= "<toma>"
        
        If Len(AllTrim(aDest[1])) == 14
            cString += "<CNPJ>" + AllTrim(aDest[1]) + "</CNPJ>"
        ElseIf Len(AllTrim(aDest[1])) == 11
            cString += "<CPF>" + AllTrim(aDest[1]) + "</CPF>"
        ElseIf AllTrim(aDest[9]) == "EX" .And. !Empty(AllTrim(aDest[28])) //A1_NIF
            cString += "<NIF>" + AllTrim(aDest[28]) + "</NIF>"
        ElseIf AllTrim(aDest[9]) == "EX" .And. !Empty(AllTrim(aDest[26])) //A1_PFISICA
            cString += "<NIF>" + AllTrim(aDest[26]) + "</NIF>"
        ElseIf AllTrim(aDest[9]) == "EX" // Tag cNaoNIF estamos chumbando como 2, acordado com o Ricardo, mas devemos ver com os outros times para buscar o valor de algum campo.
            cString += "<cNaoNIF>2</cNaoNIF>"  //0 - Não informado na nota de origem; 1 - Dispensado do NIF; 2 - Não exigência do NIF;
        EndIf
        //cString	+= '<CAEPF>'+ cAmbiente +"</CAEPF>"
        cString	+= IIF( !EMPTY( allTrim( aDest[17] ) ), '<IM>'+ allTrim( aDest[17] ) +"</IM>", "" )    
        cString	+= '<xNome>'+ allTrim( aDest[2] ) +"</xNome>"
        cString	+= "<end>"
        if( allTrim( aDest[9] ) == "EX")
   			cString	+= "<endExt>"
			cString	+= "<cPais>"+AllTrim(cPaisIso)+"</cPais>"
			cString	+= "<cEndPost>"+ allTrim( aDest[10] )+"</cEndPost>"
			cString	+= '<xCidade>'+Alltrim(aDest[8])+'</xCidade>'
			cString	+= '<xEstProvReg>'+Alltrim(aDest[12])+'</xEstProvReg>' 
			cString	+= '</endExt>'
        Else
            cString	+= "<endNac>"
            cString	+= '<cMun>'+ IIf(cCodMun $ "5208707" .And. !empty( allTrim( aDest[25] ) ), UfIBGEUni(aDest[09]) + allTrim( aDest[25] ),  UfIBGEUni(aDest[09]) + allTrim( aDest[07] )) +"</cMun>
            cString	+= '<CEP>'+ allTrim( aDest[10] ) +"</CEP>
            cString += "</endNac>"
        Endif 
        cString	+= '<xLgr>'+ allTrim( ClearTLogr( aDest[ 3 ] ) ) +"</xLgr>"
        cString	+= '<nro>'+ allTrim( aDest[4] ) +"</nro>"
        cString	+= IIF( !empty( allTrim( aDest[5] ) ),'<xCpl>'+ allTrim( aDest[5] ) +'</xCpl>',"")
        cString	+= '<xBairro>'+ allTrim( aDest[6] )+"</xBairro>"
        cString	+= "</end>"
        cString	+= IIf(!Empty(allTrim( aDest[13] )), "<fone>"+ allTrim( aDest[13] ) +"</fone>", "")
        If !Empty(allTrim( aDest[16] ))
            if ";" $ AllTrim(aDest[16])
                cString += "<email>" +  allTrim(SUBSTR(aDest[16], 1, At(';', aDest[16])-1)) + "</email>"
            else 
                cString += "<email>" + allTrim(aDest[16]) + "</email>"
            endif 
        EndIf
        cString	+= "</toma>"

	EndIf

return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} intermediario
Função para montar a tag de intermediário do XML de envio de NFS-e ao TSS.

@author renan.botelho
@since 26.10.2023

@param	aInterm	Array com as informações do intermediario da nota.

@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
Static Function intermedNac( aInterm )

Local cString	:= "" 

If len(aInterm) > 0

	If !Empty(aInterm[1]) .and. !Empty(aInterm[2]) .and. !Empty(aInterm[3])

        cString	+= "<interm>"
        cString	+= IIf(len( aInterm[2] ) < 14, '<CPF>'+ allTrim( aInterm[2] ) +"</CPF>", '<CNPJ>'+ allTrim( aInterm[2] ) +"</CNPJ>" )
        //cString	+= '<NIF>'+  +"</NIF>"
        //cString	+= '<cNaoNIF>'+  +"</cNaoNIF>"
        //cString	+= '<CAEPF>'+  +"</CAEPF>"
        cString	+= '<IM>'+ allTrim( aInterm[3] ) +"</IM>"
        cString	+= '<xNome>'+ allTrim( aDest[1] ) +"</xNome>"
        //cString	+= "<end>"
        //cString	+= "<endNac>"
        //cString	+= '<cMun>'+  +"</cMun>
        //cString	+= '<CEP>'+  +"</CEP>
        //cString   += "</endNac>"
        //cString	+= '<xLgr>'+  +"</xLgr>"
        //cString	+= '<nro>'+  +"</nro>"
        //cString	+= '<xCpl>'+  +'</xCpl>',"")
        //cString	+= '<xBairro>'+  +"</xBairro>"
        //cString	+= "</end>"
        //cString	+= '<fone>'+  +"</fone>"
        //cString	+= "<email>" +  + "</email>", )
        cString	+= "</interm>"
		
	EndIf

EndIf
	
return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} servicos
Função para montar a tag de serviços do XML de envio de NFS-e ao TSS.

@author renan.botelho.
@since 26.10.2023

@param	aProd		Array contendo as informações dos produtos da nota.
@param	aISSQN		Array contendo as informações sobre o imposto.
@param	aRetido		Array contendo as informações sobre impostos retidos.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function servicosNac( aProd, cNatOper, lNFeDesc, cDiscrNFSe,aRetSF3,aDest)	
	
	Local cString	    := ""
    Local nValmoeda     := 0  
    Local cTpmoeda      := "220"
    Local cParmoeda     := ""
    Local lUsaSF3       := GetNewPar("MV_ENVSF3",.F.)

	Default aRetSF3	:= {}
    Default aDest   := {} 

    cString += '<serv>'
    cString += '<locPrest>'
    cString += '<cLocPrestacao>'+ prestacaoNac( cMunPrest, cDescMunP, aDest ) +'</cLocPrestacao>'
    //cString += '<cPaisPrestacao>'+ '' +'</cPaisPrestacao>'
    cString += '</locPrest>'
    cString += '<cServ>'
    // issue DSERTSS1-29096 - Conteudo da FT_TRIBMUN pode ser alterado para envio por outros processos se nao é igual B1_TRIBMUN 
    //cString += IIF( !EMPTY( allTrim( aProd[1][32]) ) ,'<cTribNac>'+ SubStr(allTrim( aProd[1][32]),1,6) +'</cTribNac>', "" )
    //cString += IIF( LEN( allTrim( aProd[1][32]) )>6 ,'<cTribMun>'+ SubStr(allTrim( aProd[1][32]),7,3) +'</cTribMun>', "" )
    If lUsaSF3
        cString +='<cTribNac>'+ SubStr(allTrim(aRetSF3[1][3]),1,6) +'</cTribNac>'
        If LEN( allTrim(allTrim(aRetSF3[1][3])) )== 9
            cString +='<cTribMun>'+ SubStr(allTrim(aRetSF3[1][3]),7,3) +'</cTribMun>'
        Endif
    ElseIf !Empty(allTrim(aProd[1][32]) )
        cString +='<cTribNac>'+ SubStr(allTrim(aProd[1][32]),1,6) +'</cTribNac>'
        If LEN( allTrim(aProd[1][32]) )== 9
            cString +='<cTribMun>'+ SubStr(allTrim(aProd[1][32]),7,3) +'</cTribMun>'
        Endif
    Endif
    
    If ( SC6->(FieldPos("C6_DESCRI")) > 0 .And. Len(aProd[1]) > 40 .And. !Empty(aProd[1][41]) ) .And. (!lNFeDesc .And. !GetNewPar("MV_NFESERV","1") == "1" .And. !Empty(cCpmUsr) )
        cString	+= '<xDescServ>'+ allTrim( aProd[1][41]) +'</xDescServ>'
    ElseIf !lNFeDesc
        cString	+= '<xDescServ>'+  AllTrim(cNatOper) +'</xDescServ>'
    Else
        cString	+= '<xDescServ>'+  AllTrim(cDiscrNFSe) +'</xDescServ>'
    EndIf

	//------------------------------------------------------------------------------------------------
    //Codigo NBS
	cString += IIf(!Empty(SB5->B5_NBS), "<cNBS>"+SB5->B5_NBS+"</cNBS>","")


    cString += '</cServ>'

    If type("aDest[9]") <> "U" .and. aDest[9] == "EX" 
        nValmoeda := xMoeda(aTotal[2],1,2) // converte valor do serviço em moeda forte 
        //IIF(Empty(nValmoeda),nValmoeda := aTotal[2],'') // se a conversão para moeda forte der igual a ZERO é destacado o valor do serviço em moeda corrente
        cParmoeda := Alltrim(Upper(SuperGetMV("MV_MOEDA2")))
        IIF(cParmoeda == "DOLAR", cTpmoeda := "220",'' )
        IIF(cParmoeda == "EURO",  cTpmoeda := "978",'' )
        IIF(cParmoeda == "IENE",  cTpmoeda := "470",'' )
        cString	+= '<comExt>'
        //Modo de Prestação: 0 - Desconhecido (tipo não informado na nota de origem); 1 - Transfronteiriço; 2 - Consumo no Brasil; 3 - Presença Comercial no Exterior; 4 - Movimento Temporário de Pessoas Físicas;
        if fPaisprest() == "BR"
            cString	+= '<mdPrestacao>2</mdPrestacao>'
        else
            cString	+= '<mdPrestacao>1</mdPrestacao>'
        endif
        cString	+= '<vincPrest>0</vincPrest>'//Vínculo entre as partes no negócio: 0 - Sem vínculo com o tomador/ Prestador 1 - Controlada; 2 - Controladora; 3 - Coligada; 4 - Matriz; 5 - Filial ou sucursal; 6 - Outro vínculo;
        cString	+= '<tpMoeda>'+cTpmoeda+'</tpMoeda>'//Identifica a moeda da transação comercial
        cString	+= '<vServMoeda>'+convType(nValmoeda,15,2)+'</vServMoeda>'//Valor do serviço prestado expresso em moeda estrangeira especificada em tpmoeda
        cString	+= '<mecAFComexP>01</mecAFComexP>'//Mecanismo de apoio/fomento ao Comércio Exterior utilizado pelo prestador do serviço: 00 - Desconhecido (tipo não informado na nota de origem); 01 - Nenhum; 02 - ACC - Adiantamento sobre Contrato de Câmbio – Redução a Zero do IR e do IOF; 03 - ACE – Adiantamento sobre Cambiais Entregues - Redução a Zero do IR e do IOF; 04 - BNDES-Exim Pós-Embarque – Serviços; 05 - BNDES-Exim Pré-Embarque - Serviços; 06 - FGE - Fundo de Garantia à Exportação; 07 - PROEX - EQUALIZAÇÃO 08 - PROEX - Financiamento;
        cString	+= '<mecAFComexT>01</mecAFComexT>'//Mecanismo de apoio/fomento ao Comércio Exterior utilizado pelo tomador do serviço: 00 - Desconhecido (tipo não informado na nota de origem); 01 - Nenhum; 02 - Adm. Pública e Repr. Internacional; 03 - Alugueis e Arrend. Mercantil de maquinas, equip., embarc. e aeronaves; 04 - Arrendamento Mercantil de aeronave para empresa de transporte aéreo público; 05 - Comissão a agentes externos na exportação; 06 - Despesas de armazenagem, mov. e transporte de carga no exterior; 07 - Eventos FIFA (subsidiária); 08 - Eventos FIFA; 09 - Fretes, arrendamentos de embarcações ou aeronaves e outros; 10 - Material Aeronáutico; 11 - Promoção de Bens no Exterior; 12 - Promoção de Dest. Turísticos Brasileiros; 13 - Promoção do Brasil no Exterior; 14 - Promoção Serviços no Exterior; 15 - RECINE; 16 - RECOPA; 17 - Registro e Manutenção de marcas, patentes e cultivares; 18 - REICOMP; 19 - REIDI; 20 - REPENEC; 21 - REPES; 22 - RETAERO; 23 - RETID; 24 - Royalties, Assistência Técnica, Científica e Assemelhados; 25 - Serviços de avaliação da conformidade vinculados aos Acordos da OMC; 26 - ZPE
        cString	+= '<movTempBens>1</movTempBens>'//Operação está vinculada à Movimentação Temporária de Bens: 0 - Desconhecido (tipo não informado na nota de origem); 1 - Não 2 - Vinculada - Declaração de Importação 3 - Vinculada - Declaração de Exportação
        cString	+= '<mdic>0</mdic>'//Compartilhar as informações da NFS-e gerada a partir desta DPS com a Secretaria de Comércio Exterior: 0 - Não enviar para o MDIC; 1 - Enviar para o MDIC;
        cString	+= '</comExt>'
    Endif 

    IF !EMPTY( aConstr )
        cString += construcaoNac( aConstr )
    ENDIF

    iF !Empty(cMensCli) .or. !Empty(cMensFis)
        cString += '<infoCompl>'
        cString += '<xInfComp>'+ AllTrim(cMensCli + space( 1 ) + cMensFis) +'</xInfComp>'
        cString += '</infoCompl>'
    Endif 

    cString += '</serv>'
	
return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} prestacao
Função para retornar o municipio prestação do XML de envio de NFS-e Nacional.

@author renan.botelho
@since 19.01.2012

@param	cMunPrest	Código de município IBGE da prestação do serviço.
@param	cDescMunP	Nome do município da prestação do serviço.
@param	aDest		Array contendo as informações sobre o tomador da nota.
@param	cMunPSIAFI	Código de município SIAFI da prestação do serviço.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function prestacaoNac( cMunPrest, cDescMunP, aDest, cMunPSIAFI )
	
	Local aTabIBGE		:= {}
	Local cString		:= ""
	Local cMvNFSEINC	:= SuperGetMV("MV_NFSEINC", .F., "") // Parametro que aponta para o campo da SC5 com Código do município de Incidência 
	Local cNFSEINC		:= ""
	Local cUFPres 		:= "" //Estado da prestação
	Local nScan			:= 0
	Local aEndPres		:= {}
	Local lIsRpsLOJA 	:= .F.
		
	default	cDescMunP	:= ""
	default	cMunPrest	:= ""
	default	cMunPSIAFI	:= ""
	
	aTabIBGE	:= spedTabIBGE()
	
	//Verifica se é NFS-e originada do SIGALOJA (Varejo)
	lIsRpsLOJA := IsRPSLOJA(@aEndPres)
	
	If lIsRpsLOJA
		//iIf( !Empty(aEndPres[01]), cLogradPres 	:= aEndPres[01] , Nil ) //01-Logradouro da prestação do serviço
		//iIf( !Empty(aEndPres[02]), cNumEndPres 	:= aEndPres[02] , Nil ) //02-Número do logradouro da prestação do serviço
		//iIf( !Empty(aEndPres[03]), cCompEndPres := aEndPres[03] , Nil ) //03-Complemento do logradouro da prestação do serviço
		//iIf( !Empty(aEndPres[04]), cBairroPres 	:= aEndPres[04] , Nil ) //04-Bairro da prestação do serviço
		iIf( !Empty(aEndPres[05]), cUFPres 		:= aEndPres[05] , Nil ) //05-Estado da prestação do serviço
		//iIf( !Empty(aEndPres[06]), cCepPres 	:= aEndPres[06] , Nil ) //06-CEP da prestação do serviço
		iIf( !Empty(aEndPres[07]), cMunPrest 	:= aEndPres[07] , Nil ) //07-Município da prestação do serviço
		//iIf( !Empty(aEndPres[08]), cDescMunP 	:= aEndPres[08] , Nil ) //08-Descrição do Município da prestação do serviço
		//iIf( !Empty(aEndPres[09]), cPaisPres 	:= aEndPres[09] , Nil ) //09-País da prestação do serviço
	Else

		If lJescTur // Integração com módulo SIGAPFS
			cUFPres := SF2->F2_ESTPRES
		ElseIf SC5->(ColumnPos("C5_ESTPRES")) > 0
			cUFPres := IIF( !Empty(SC5->C5_ESTPRES), SC5->C5_ESTPRES, "" )
		EndIf

	EndIf

	If Len(alltrim(cMunPrest)) <= 5		
		If SuperGetMV("MV_JESCJUR",, .F.) .and. !Empty(cUFPres) //Integração com módulo SIGAPFS
				nScan	:= aScan( aTabIBGE, { | x | x[1] == cUFPres } )
				cMunPrest	:= aTabIBGE[nScan][4] + cMunPrest
			Else
			if lIsRpsLOJA
				nScan	:= aScan( aTabIBGE, { | x | x[1] == cUFPres } )				
			else	
				nScan	:= aScan( aTabIBGE, { | x | x[1] == aDest[9] } )
			EndIf	
			if nScan <= 0			
				nScan		:= aScan( aTabIBGE, { | x | x[4] == aDest[9] } )			
				cMunPrest	:= aTabIBGE[nScan][1] + cMunPrest			
			else			
				cMunPrest	:= aTabIBGE[nScan][4] + cMunPrest			
			endif		
		EndIf
	EndIf
	
	if empty( cMunPrest )
		cMunPrest	:= allTrim(aDest[7])
	endif

	if !Empty( allTrim (cMvNFSEINC) ) .And. !lIsRpsLOJA
		If SC5-> ( FieldPos (cMvNFSEINC)  ) > 0 
			cNFSEINC := allTrim(SC5-> & (cMvNFSEINC) )
			cString	+= allTrim (cNFSEINC) 
		Endif		
	Else
		if !empty( allTrim (cMunPrest) )
			cString	+= allTrim (cMunPrest) 
		endif		
	Endif	
	
return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} valores
Função para montar a tag de valores do XML de envio de NFS-e ao TSS.

@author renan.botelho
@since 27.10.2023

@param	aISSQN		Array contendo as informações sobre o imposto.
@param	aRetido		Array contendo as informações sobre impostos retidos.
@param	aTotal		Array contendo os valores totais da nota.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function valoresNac( aISSQN, aRetido, aTotal, aDest, cCodMun,aLeiTrp,lRecIrrf, aProd )
	
	Local cString		:= ""
    Local cCSTPisCofins := "" 
    Local cTribIssqn    := ""
    Local cQuery        := ""
    Local cAlqISSConv   := ""
    Local cTpRetPisCof  := "0"
    Local cAliasTemp    := GetNextAlias()
    Local cOPTSIMP      := AllTrim( SupergetMV( "MV_OPTSIMP",, "2" ) )
    Local cMvTpImuni    := SuperGetMv("MV_TIMUNAC", ,"") //Tipo de imunidade do ISSQN - NFSe Nacional
    Local cMVREGIESP    := AllTrim( SupergetMV( "MV_REGIESP",, " " ) )
    Local cLocPrest     := AllTrim( prestacaoNac( cMunPrest, cDescMunP, aDest ) )
    Local cLocEmi       := AllTrim( if( type( "oSigamatX" ) == "U",SM0->M0_CODMUN,oSigamatX:M0_CODMUN ) )
    
	Local lAglutina     := AllTrim(GetNewPar("MV_ITEMAGL","N")) == "S" 

    Local oQryCDGCCF    := Nil as object

    Local aAliqISs      := {}
	Local aglISSQN      := {}
	Local aRestImp      := {}
	Local aCSLLXML      := { 0, 0, {}, {} }
	Local aINSSXML      := { 0, 0, {}, {} }
	Local aIRRFXML      := { 0, 0, {}, {} }
	Local aISSRet		:= { 0, 0, 0, {} }
	
	Local nScan         := 0
	Local nX			:= 0
	Local nY			:= 0
	Local nI			:= 0
	Local nAliqISs      := 0
	Local nISSQN		:= 0
	Local nIssRet		:= 0
	Local nInss         := 0
	Local nRatVPis      := 0
	Local nRatVcofins   := 0
	Local nRatVIRRF     := 0
	Local nRatVCsll     := 0
    Local nBsPisCof     := 0
    Local nAliqPis      := 0
    Local nAliqCof      := 0
    Local nValPis       := 0
    Local nValCof       := 0
    Local nTotalRet     := 0
    Local lMVTRIBPORC	:= SuperGetMV( "MV_TRIBPOR",, .F. )

   	Private	aPisXML		:= { 0, 0, {}, {}, 0 }
    Private	aCofinsXML	:= { 0, 0, {}, {}, 0 }

	Default nDescon		:= 0
	Default cFntCtrb	:= ""
	Default aLeiTrp		:= {}
	Default cTpPessoa	:= ""
	Default cCodMun     := ""
	Default aRetSF3		:= {}
	Default lRecIrrf	:= .T.

	// Tratando o abatimento para quando houver mais de um item de serviço
	If len(aISSQN) > 1
		For nY := 1  to len(aISSQN)
			If 	aISSQN[nY][2] > 0 
				If cCodMun $ "4205407" //Florianópolis
					aadd(aAliqISs, aISSQN[nY][2])
					aadd(aglISSQN, aISSQN[nY][3])
				Else
					nAliqISs := aISSQN[nY][2]
				EndIf
				nISSQN	  += aISSQN[nY][3]
			EndIf
		Next nY
	Else
		nAliqISs := aISSQN[1][2]
		nISSQN	 := aISSQN[1][3]		
	EndIF
	
	// Tratamento para gerar aliquota quando houver o abtimento total dos itens
	IF(nAliqISs == 0 .AND. SF3->F3_ISSSUB > 0 .AND. ! EMPTY(SF3->F3_ISSSUB)  )
		nAliqISs := SF3->F3_ALIQICM
	EndIf
	
	for nX := 1 to len( aProd )
		
		nScan := aScan(aRetido,{|x| x[1] == "ISS"})
		If nScan > 0
			aIssRet[1] += aRetido[nScan][3]
			aIssRet[2] += aRetido[nScan][5]
			aIssRet[3] += aRetido[nScan][4]
			aIssRet[4] := aRetido[nScan][6]
		EndIf
		
		//Cálculo de Valor iss retido quando tem aglutinação.
		If lAglutina
			for nY := 1 to len( aIssRet[4] )	
				nIssRet += aIssRet[4][nY]
			next nY	
		EndIf
		nScan := aScan(aRetido,{|x| x[1] == "PIS"})
		If nScan > 0
			aPisXml[1] := aRetido[nScan][3]
			aPisXml[2] := aRetido[nScan][4] //aliquota retido
			aPisXml[3] := aRetido[nScan][5]
			nRatVPis   := RatValImp(aRetido,nScan,aProd,nX,aRestImp)
			aPisXml[4] := aRetido[nScan][6]
            aPisXml[5] := aRetido[nScan][2] // Base de calculo Pis
		EndIf
		
		nScan := aScan(aRetido,{|x| x[1] == "COFINS"})
		If nScan > 0
			aCofinsXml[1] := aRetido[nScan][3]
			aCofinsXml[2] := aRetido[nScan][4]//aliquota retido
			aCofinsXml[3] := aRetido[nScan][5]
			nRatVcofins   := RatValImp(aRetido,nScan,aProd,nX,aRestImp)
			aCofinsXml[4] := aRetido[nScan][6]
            aCofinsXml[5] := aRetido[nScan][2] // Base de calculo Cofins
		EndIf
		                                     
		nScan := aScan(aRetido,{|x| x[1] == "IRRF"})
		If nScan > 0 .and. lRecIrrf
			aIrrfXml[1] := aRetido[nScan][3]
			aIrrfXml[2] += aRetido[nScan][4]
			aIrrfXml[3] := aRetido[nScan][5]
			aIrrfXml[4] := aRetido[nScan][6]
			nRatVIRRF   := RatValImp(aRetido,nScan,aProd,nX,aRestImp)
		EndIf
		                                    
		nScan := aScan(aRetido,{|x| x[1] == "CSLL"})
		If nScan > 0
			aCSLLXml[1] := aRetido[nScan][3]
			aCSLLXml[2] += aRetido[nScan][4]
			aCSLLXml[3] := aRetido[nScan][5]
			nRatVCsll   := RatValImp(aRetido,nScan,aProd,nX,aRestImp) 
			aCSLLXml[4] := aRetido[nScan][6]
		EndIf
		     
		nScan := aScan(aRetido,{|x| x[1] == "INSS"})
		If nScan > 0
			aInssXml[1] := aRetido[nScan][3]
			aInssXml[2] += aRetido[nScan][4]
			aInssXml[3] := aRetido[nScan][5]
			aInssXml[4] := aRetido[nScan][6]
		EndIf 

		If lAglutina .and. len( aInssXml[3] ) >= 1
			for nI := 1 to len( aInssXml[3] )
				nInss += aInssXml[3][nI]
			next nI
		EndIf

    next nX

    //-----------------------------------------------------------------------------------------------------------------------------------//
    // Calculo de impostos federais conforme manual sao somados os Seguintes impostos                                                    //
    // PIS + COFINS + IRRF + CSLL + CP(?)                                                                                                //
    // CONFORME DOCUMENTAÇÃO DO NFSE NACIONAL CP = "A Contribuição Previdenciária (CP)                                                   //
    //      é um tributo federal e é composta pelo Risco Ambiental do Trabalho (RAT)                                                     //
    //      ou Seguro de Acidente do Trabalho (SAT) e pela Contribuição Previdenciária Patronal (CPP).                                   //
    //      Essas contribuições são calculadas pela aplicação de uma alíquota sobre o total das remunerações                             //
    //      pagas ou creditadas, no decorrer do mês, aos segurados empregados e trabalhadores avulsos e são                              //
    //      destinadas ao financiamento da Seguridade Social. As contribuições mencionadas estão regidas pela lei 8.212/1991"            //
    //-----------------------------------------------------------------------------------------------------------------------------------//
     
    cString += '<valores>'
    cString += '<vServPrest>'
    cString += '<vServ>'+ allTrim( convType( aTotal[2], 15, 2 ) ) +'</vServ>'
    cString += '</vServPrest>'
    If (aISSQN[1][6] > 0 .OR. !Empty( nDescon ))//só destaca Desconto incondicionado se parametr deduçao estiver falso
        cString += '<vDescCondIncond>'
        If (lMvDescInc .and. !lDescCond) .Or. (SF4->F4_DESCOND <> '1' .and. !lConfTrIss)
            cString += '<vDescIncond>' + convType(aISSQN[1][6],15,2)+ '</vDescIncond>'
        ElseIf (!lMvDescInc .and. lDescCond) .Or. (SF4->F4_DESCOND == '1' .and. !lConfTrIss)
            cString += '<vDescCond>' + convType(nDescon,15,2) + '</vDescCond>'
        EndIf
        cString += '</vDescCondIncond>'
    EndIf
    if ( lMvded ) 
        If !Empty(adeduz) .and. ADEDUZ[1][9] > 0 //só destaca Dedução se parametr deduçao estiver verdadeiro
            cString += '<vDedRed>'
            cString += '<vDR>'+ allTrim( convType( ADEDUZ[1][9], 15, 2 ) ) +'</vDR>'
            cString += '</vDedRed>'
        elseif Len(aProd[1])>=43 .and. aProd[1][43] > 0 //só destaca Dedução se parametr deduçao estiver verdadeiro
            cString += '<vDedRed>'
            cString += '<vDR>'+ allTrim( convType( aProd[1][43], 15, 2 ) ) +'</vDR>'
            cString += '</vDedRed>'
        endif
    endif

    cString += '<trib>'
    cString += '<tribMun>'

    do case
        case aTotal[3] == "4" // Imune (ERP)
            cTribIssqn := '2' // 2 - Imunidade
        case (aTotal[3] == "7" .and. lConfTrIss  == .F.) .or. (aTotal[3] == "8" .and. lConfTrIss  == .T.) // Não Incidencia (ERP)
            cTribIssqn := '4' // 4 - Não Incidência;
        case (!Empty( aDest[9] ) .AND. aDest[9] $ "EX" .and. aTotal[3] $ "2-3" .and. lConfTrIss  == .F.) .or. (aTotal[3] == "9" .and. lConfTrIss  == .T.) // Exportacao (ERP) dentro ou fora do municipio
            cTribIssqn := '3' // 3 - Exportação de serviço
        otherWise
            cTribIssqn := '1' // 1 - Operação tributável;
    endcase

    cString += '<tribISSQN>' + cTribIssqn + '</tribISSQN>'

    if (!Empty( aDest[9] ) .AND. aDest[9] $ "EX" .and. aTotal[3] $ "2-3" .and. lConfTrIss  == .F.) .or. (aTotal[3] == "9" .and. lConfTrIss  == .T.) // Exportacao (ERP) dentro ou fora do municipio
        cString += '<cPaisResult>' + fPaisprest() + '</cPaisResult>'// Pais de prestação //parra
    endif 

    if cTribIssqn == '2' .and. !empty(cMvTpImuni) // Imunidade
        cString += '<tpImunidade>' + alltrim(cMvTpImuni) + '</tpImunidade>' //Imunidade cadastrada no parametro MV_TPIMNNAC

    endif

    If oQryCDGCCF == Nil
        cQuery += " SELECT "
        cQuery += "   CDG.CDG_PROCES, "
        cQuery += "   CCF.CCF_TPCOMP "
        cQuery += " FROM " + RetSqlName("CDG") + " CDG "
        cQuery += " INNER JOIN " + RetSqlName("CCF") + " CCF "
        cQuery += "   ON CCF.CCF_FILIAL = CDG.CDG_FILIAL "
        cQuery += "   AND CCF.CCF_NUMERO = CDG.CDG_PROCES "
        cQuery += "   AND CCF.CCF_TIPO   = CDG.CDG_TPPROC "
        cQuery += "   AND CCF.D_E_L_E_T_ = ? "
        cQuery += "   AND CCF.CCF_TPCOMP IN (?, ?) "
        cQuery += " WHERE CDG.CDG_FILIAL = ? "
        cQuery += "   AND CDG.CDG_DOC    = ? "
        cQuery += "   AND CDG.CDG_SERIE  = ? "
        cQuery += "   AND CDG.CDG_CLIFOR = ? "
        cQuery += "   AND CDG.CDG_LOJA   = ? "
        cQuery += "   AND CDG.D_E_L_E_T_ = ? "

        oQryCDGCCF := FWExecStatement():New( ChangeQuery(cQuery) )

        oQryCDGCCF:SetString(1, Space(1))        // CCF.D_E_L_E_T_
        oQryCDGCCF:SetString(2, "1")             // CCF_TPCOMP
        oQryCDGCCF:SetString(3, "2")             // CCF_TPCOMP
        oQryCDGCCF:SetString(4, xFilial("CDG"))  // CDG_FILIAL
        oQryCDGCCF:SetString(5, aNota[2])        // CDG_DOC
        oQryCDGCCF:SetString(6, aNota[1])        // CDG_SERIE
        oQryCDGCCF:SetString(7, SF2->F2_CLIENTE) // CDG_CLIFOR
        oQryCDGCCF:SetString(8, SF2->F2_LOJA)    // CDG_LOJA
        oQryCDGCCF:SetString(9, Space(1))       // CDG.D_E_L_E_T_

        cAliasTemp  := oQryCDGCCF:OpenAlias()
        cQuery      := oQryCDGCCF:GetFixQuery()

        If (cAliasTemp)->(!Eof())
            cString += '<exigSusp>'
            cString += '<tpSusp>' + (cAliasTemp)->CCF_TPCOMP + '</tpSusp>'
            cString += '<nProcesso>' + PadL( Alltrim((cAliasTemp)->CDG_PROCES), 30, "0" ) + '</nProcesso>'
            cString += '</exigSusp>'
        EndIf

        (cAliasTemp)->(DbCloseArea())
    EndIf

    /*//------------------------------------------------------------------------------------------------------
        "É obrigatorio o preenchimento do campo pAliq quando ocorrer as condições abaixo simultaneamente:
        1) O prestador de serviço seja optante do Simples Nacional ME/EPP (opSimpNac = 3) 
        na data de competência de emissão da DPS, 
        2) a apuração do ISSQN seja pelo SN (regApTribSN = 1);
        3) Haja retenção do ISSQN (tpRetISSQN = 2 ou 3);
        nesta situção o percentual da alíquota mínima permitida é 1,8%."	
       -------------------------------------------------------------------------------------------------------
        "Não é permitido o preenchimento do campo pAliq quando ocorrer as condições abaixo simultaneamente:
        1) O prestador de serviço seja optante do Simples Nacional ME/EPP (opSimpNac = 3) 
        na data de competência de emissão da DPS, 
        2) a apuração do ISSQN seja pelo SN (regApTribSN = 1);
        3) Não haja retenção do ISSQN (tpRetISSQN = 1);"	
        ------------------------------------------------------------------------------------------------------
        Obs feita durante testes se (opSimpNac = 3) e (tpRetISSQN = 2 ou 3) a tag não é obrigatoria autorizando
        nfse sem aliquota.. porem na nota nao destaca valor do ISS Retido .. 
        Se (opSimpNac = 3) e (tpRetISSQN = 2 ou 3) e coloque a TAG pAliq .. na nota é destacado ISS Retido
        BC ISSQN=R$ 10,00,Alíquota Aplicada=5,00%,Retenção do ISSQN= Retido pelo Tomador,ISSQN Apurado=R$ 0,50
    //---------------------------------------------------------------------------------------------------------*/
    IF !empty( aISSRet[2] )
        cString += '<tpRetISSQN>' + cValToChar(2) + '</tpRetISSQN>'
    else
        cString += '<tpRetISSQN>' + "1" + '</tpRetISSQN>' // opção 3 - protheus não possui endereço nacional do intermediário
    EndIf
    
    If nAliqISs > 0
        cAlqISSConv := AllTrim( ConvType( nAliqISs, 7, 2 ) )
    Else
        cAlqISSConv := AllTrim( ConvType( aISSRet[3], 7, 2 ) )
    EndIf

    IF !empty( aISSRet[2] ) .and. aISSRet[2] == 1 .And. cOPTSIMP == "1" // ISS Retido e Optante Simples Nacional 
        cString += '<pAliq>' +  cAlqISSConv + '</pAliq>'
    ElseIf cLocEmi <>  cLocPrest .AND. cOPTSIMP == "2" .AND. Empty(cMVREGIESP) .AND. !cTribIssqn $ "2|3|4"// Não Optante pelo Simples Nacional
        // Nao e permitido informar aliquota quando o campo referente Ã  tributacao do ISSQN indicar imunidade, exportacao ou nao incidencia.
        // E0619 - É obrigatorio informar aliquota quando o prestador de servico nao e optante do simples nacional (opSimpNac = 1) na data de 
        // competencia informada na DPS, o municipio de incidencia do ISSQN nao esta com situacao "ATIVO" no Sistema Nacional NFS-e e nao haja 
        // algum regime especial de tributacao para o prestador."
        cString += '<pAliq>' +  cAlqISSConv + '</pAliq>'
    Endif

    cString += '</tribMun>'
    cString += '<tribFed>'

    if ( lConfTrib .And. ((oNfTciIntg:GetTax( cIdTribPiSCof, "PIS") <> NIL ) .or. (oNfTciIntg:GetTax( cIdTribPiSCof, "COFINS") <> NIL ))) // Verifica impostos vieram do configurador de tributos
        if !empty(oNfTciIntg:GetEscrituracaoRuleTax( cIdTribPiSCof, "PIS")['cst']) .or. !empty(oNfTciIntg:GetEscrituracaoRuleTax( cIdTribPiSCof, "COFINS")['cst'])
            if !empty(oNfTciIntg:GetEscrituracaoRuleTax( cIdTribPiSCof, "PIS")['cst']) // Estrutura do governo possui tag unica para pis e cofins
                cCSTPisCofins := oNfTciIntg:GetEscrituracaoRuleTax( cIdTribPiSCof, "PIS")['cst']
            else
                cCSTPisCofins := oNfTciIntg:GetEscrituracaoRuleTax( cIdTribPiSCof, "COFINS")['cst']
            endif
        else
            cCSTPisCofins := "01" // Mantido legado tributado integralmente caso CST estiver em branco
        endif
    else
        if !empty(SF4->F4_CSTPIS) .or. !empty(SF4->F4_CSTCOF) // Estrutura do governo possui tag unica para pis e cofins
            if !empty(SF4->F4_CSTPIS)
                cCSTPisCofins := SF4->F4_CSTPIS
            else
                cCSTPisCofins := SF4->F4_CSTCOF
            endif
        else // Mantido legado tributado integralmente caso CST nas TES estiver em branco
            cCSTPisCofins := "01" // Quando o pis/cof é só retido e nao tem CST 
        endif
    endif
   
        /*Código de Situação Tributária do PIS/COFINS (CST):
            00 - Nenhum;      
            01 - Operação Tributável com Alíquota Básica;
            02 - Operação Tributável com Alíquota Diferenciada;
            03 - Operação Tributável com Alíquota por Unidade de Medida de Produto;
            04 - Operação Tributável monofásica - Revenda a Alíquota Zero;
            05 - Operação Tributável por Substituição Tributária;
            06 - Operação Tributável a Alíquota Zero;
            07 - Operação Tributável da Contribuição;
            08 - Operação sem Incidência da Contribuição;
            09 - Operação com Suspensão da Contribuição;*/
    
    
    // defeni valores para as tags de Pis Cofins apuração
    nBsPisCof     := aCOFINS[2]
    nAliqPis      := aPIS[3]
    nAliqCof      := aCOFINS[3]
    nValPis       := aPIS[4]
    nValCof       := aCOFINS[4]
    
    //Retorna o código da tag tpRetPisCofins com base na análise dos valores de Pis e Cofins retido
    cTpRetPisCof  := GetTpRetPisCofins(aPISXML[1], aCOFINSXml[1], aCSLLXml[1])
    
    // Se houver valores de retenções de PIS, de COFINS e/ou de CSLL, eles deverão ser SOMADOS e informados no campo “vRetCSLL” de acordo com o que foi informado no campo “tpRetPisCofins”.
    nTotalRet := aPISXML[1] + aCOFINSXml[1] + aCSLLXml[1] 
   
    cString += '<piscofins>'
    cString += '<CST>' + cCSTPisCofins + '</CST>'
    
    // Se CST for "00 - Nenhum", "08 - Operação sem Incidência da Contribuição", "9 - Operação com Suspensão da Contribuição",
    // tags BC, Aliquota e Valores do Pis/Cofins não devem ser informadas
    if cCSTPisCofins <> "00" .and. cCSTPisCofins <> "08" .and. cCSTPisCofins <> "09"
        cString += '<vBCPisCofins>'+ allTrim( convType( nBsPisCof, 15, 2 ) ) +'</vBCPisCofins>'
        cString += '<pAliqPis>'+ allTrim( convType(nAliqPis, 15, 2 ) ) +'</pAliqPis>' 
        cString += '<pAliqCofins>'+ allTrim( convType(nAliqCof, 15, 2 ) ) +'</pAliqCofins>'
        cString += '<vPis>'+ allTrim( convType( nValPis, 15, 2 ) ) +'</vPis>'
        cString += '<vCofins>' + allTrim( convType( nValCof, 15, 2 ) ) +'</vCofins>'
        
        /*tipo de retenção PIS/COFINS e CSLL:
        0 - PIS/COFINS/CSLL Não Retidos;
        1 - PIS/COFINS Retido;
        2 - PIS/COFINS Não Retido;
        3 - PIS/COFINS/CSLL Retidos;
        4 - PIS/COFINS Retidos, CSLL Não Retido;
        5 - PIS Retido, COFINS/CSLL Não Retido;
        6 - COFINS Retido, PIS/CSLL Não Retido;
        7 - PIS Não Retido, COFINS/CSLL Retidos;
        8 - PIS/COFINS Não Retidos, CSLL Retido;
        9 - COFINS Não Retido, PIS/CSLL Retidos;"*/
        cString += '<tpRetPisCofins>'+cTpRetPisCof+'</tpRetPisCofins>'
    endif

    cString += '</piscofins>'
    If SF2->F2_VALINSS > 0
        cString += '<vRetCP>' + allTrim( convType(SF2->F2_VALINSS, 15, 2)) +'</vRetCP>' 
    EndIf
    If aIrrfXml[1] > 0
        cString += '<vRetIRRF>'+ allTrim( convType( aIrrfXml[1], 15, 2 ) ) +'</vRetIRRF>'
    EndIf
    If nTotalRet > 0
        cString += '<vRetCSLL>'+ allTrim( convType( nTotalRet, 15, 2 ) ) +'</vRetCSLL>'
    EndIf

    cString += '</tribFed>'

    IF lMVTRIBPORC
        cString += gtotTribPrc(SB5->B5_NBS)
    Else
        cString += gtotTribVal(aLeiTrp)
    EndIf

    cString += '</trib>'

    cString += '</valores>'
    

    
return cString

//-----------------------------------------------------------------------
/*/{Protheus.doc} construcao
Função para montar a tag de construção civil do XML de envio de NFS-e ao TSS.

@author renan.botelho
@since 27.10.2023

@param	aConstr		Array contendo dados da construção civil.

@return	cString		Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function construcaoNac( aConstr )
	
	local cString   := ""

    If !Empty(aConstr[1]) .or. !Empty(aConstr[3]) .Or. !Empty(aConstr[4]) .or. !Empty(aConstr[15]) .or. !Empty(aConstr[17]) .or. !Empty(aConstr[19])
        cString += "<obra>"
        Do Case // Esse CASE foi criado, pois a NFSe Nacional aceita apenas uma das informaçoes (<cObra>,<inscImobFisc>,<end>) na montagem do bloco de OBRA
            //---------
            //- cObra
            //---------
            Case (Len(aConstr) > 00 .And. !Empty(aConstr[01]))  .AND. (Len(aConstr) > 01 .And. Empty(aConstr[02]))
                cString += '<cObra>'+AllTrim(aConstr[01])+'</cObra>'
            //-----------
            //- inscImobFisc
            //-----------
            Case (Len(aConstr) > 01 .And. !Empty(aConstr[02]))
                cString += '<inscImobFisc>'+AllTrim(aConstr[02])+'</inscImobFisc>'
            //---------------------------------------
            //- end
            //---------------------------------------
            Case (Len(aConstr) > 03 .And. !Empty(aConstr[04]))
                cString += '<end>'  
                cString += If(Len(aConstr) > 07 .And. !Empty(aConstr[08]), '<CEP>'+aConstr[08]+'</CEP>' , "")
                cString += If(Len(aConstr) > 03 .And. !Empty(aConstr[04]), '<xLgr>'+aConstr[04]+'</xLgr>' , "" )
                cString += If(Len(aConstr) > 05 .And. !Empty(aConstr[06]), '<nro>'+aConstr[06]+'</nro>' , "" )
                cString += If(Len(aConstr) > 04 .And. !Empty(aConstr[05]), '<xCpl>'+aConstr[05]+'</xCpl>' ,"" )
                cString += If(Len(aConstr) > 06 .And. !Empty(aConstr[07]), '<xBairro>'+aConstr[07]+'</xBairro>' , "" )
                cString += '</end>'
        EndCase
        cString += "</obra>"
	EndIf
	
return cString   
//-------------------------------------------------------------------
/*/{Protheus.doc} nfse_
Faz uma comparação do cod pais com o Cod ISO

@param		cCodMun	Codigo do municipio
@param		cCodBacen	Codigo PAIS
 
@return	cRetorno	Sigla do PAIS 
						
						
@author	Fabio M Parra
@since		30/10/2023
/*/
//-------------------------------------------------------------------
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
	iif(Empty(cRetorno),cRetorno := 'ZZ','')
Endif
Return(cRetorno) 

//-----------------------------------------------------------------------
/*/{Protheus.doc}  Method TssTCInteg

	Função responsável por integrar o TSS com o Configurador de Tributos, classificando
	o tipo de tributação do item da nota fiscal, de acordo com a configuração.

	@param cAliasSD2  Alias da tabela SD2.
	@param lVldExc    Booleano que indica se a classe TSSTCIIntegration existe.
	@param oNfTciIntg Objeto que irá receber a referencia da classe TSSTCIIntegration.
	@return void
	
	@author Felipe Duarte Luna
	@since 17.02.2025
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
	@since 17.02.2025
	@version 12.1.2410
	@return void
/*///-----------------------------------------------------------------------
Static Function DestroyTCI(oNfTciIntg)
    If ValType(oNfTciIntg) == 'O'
        oNfTciIntg:Destroy()
        oNfTciIntg := Nil
    EndIf
Return
//-------------------------------------------------------------------
/*/{Protheus.doc} GetVerParTSS
Static Funcao para retornar a versao do Parâmetro MV_NFSEVER

@author		Antonio Marfil
@since		14/07/2025
@version	1.0
/*/
//-------------------------------------------------------------------

Static Function GetVerParTSS(cIdEnt)
	Local    aVersao	:= {}
	Local    cVersao	:= ""
	DEFAULT  cIdEnt		:= getCfgEntidade()
	
	aVersao := GetMvTSS( cIdEnt, {"MV_NFSEVER"} )

	If !Empty(aVersao) .and. Len(aVersao) > 0
		cVersao := aVersao[1][2]
	EndIf
	
Return cVersao

//-----------------------------------------------------------------------
/*/{Protheus.doc}
Função para montar a tag de IBSCBS do XML de envio de NFS-e ao TSS.

@author Antonio Marfil
@since 08.09.2025
@param aDest, array, Informações destinatário.
@param cCodMun, character, Código do municipio.
@param aEntrega, array, Informações destinatário de entrega.
@return	cString	Tag montada em forma de string.
/*/
//-----------------------------------------------------------------------
static function IbsCbs( aDest, cCodMun, aNota, cClieFor, cLoja, aEntrega )
    Local cString	    := ""
    Local cErro         := ""
    Local cAviso        := ""
    local cXmlIBSCBS    := ""
    Local aArea         := GetArea()

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

/*/{Protheus.doc} IbsCbsDest
Monta o grupo DEST dentro de IBSCBS.
@type function
@version P12 V1.2410
@author Gabriel Jesus
@since 08/09/2025
@param aDest, array, Informações destinatário.
@param cCodMun, character, Código do municipio.
/*/
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
            ElseIf AllTrim(aDest[9]) == "EX" .And. !Empty(AllTrim(aDest[28])) //A1_NIF
                cString += "<NIF>" + AllTrim(aDest[28]) + "</NIF>"
            ElseIf AllTrim(aDest[9]) == "EX" .And. !Empty(AllTrim(aDest[26])) //A1_PFISICA
                cString += "<NIF>" + AllTrim(aDest[26]) + "</NIF>"
            ElseIf AllTrim(aDest[9]) == "EX"
                cString += "<cNaoNIF>2</cNaoNIF>"  //0 - Não informado na nota de origem; 1 - Dispensado do NIF; 2 - Não exigência do NIF;
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

/*/{Protheus.doc} IbsCbsValo
Grupo de valores do IBS/CBS
@type function
@version P12 V1.2410
@author Gabriel Jesus
@since 18/09/2025
@param oXml, object, XML parseado com impostos.
/*/
Static Function IbsCbsValo(oXmlIBSCBS)
    Local cString   := ""

    Default oXml    := Nil

    //Existe um grupo anterior as tags abaixo o gReeRepRes porém parece se tratar de referenciamento de nota, como vamos fazer ? campo opcional

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

//-----------------------------------------------------------------------
/*/{Protheus.doc}  GetTribID
    Função responsavel pela busca do primeiro Item da Nota que foi escriturado pelo Configurador de Tributos(FISA170).
    Campo D2_IDTRIB da tabela SD2 preenchido.

    @param cFilial  Character, Filial da Nota Fiscal.
    @param cDoc     Character, Documento da Nota Fiscal.
    @param cSerie   Character, Série da Nota Fiscal.
    @param cClie    Character, Cliente/Fornecedor da Nota Fiscal.
    @param cLoja    Character, Loja do Cliente/Fornecedor da Nota Fiscal.
    
    @return Character, Retorna o ID_TRIB do primeiro item encontrado.

    @author Felipe Duarte Luna
    @since 06.01.2026
    @version 12.1.2510
/*///-----------------------------------------------------------------------
Static Function GetTribID( cDoc, cSerie, cCliente, cLoja )
Local cQuery	 := ""
Local cAliasSD2  := "SD2"
Local cIdTrib    := ""

//Default cFilial	:= ""
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
    //
    If !Empty((cAliasSD2)->D2_IDTRIB)
        cIdTrib := (cAliasSD2)->D2_IDTRIB
        Exit
    EndIf
    (cAliasSD2)->(DbSkip())
Enddo

(cAliasSD2)->( DbCloseArea() ) 

Return cIdTrib


//-----------------------------------------------------------------------
/*/{Protheus.doc}  Method fPaisprest
Função para retornar o código do país da prestação do serviço no formato ISO 3166-1 alpha-2. 
       busca parametro MV_ENDPRES na SC5, se não encontrar, busca o país do tomador.
       se nao definido a tag é preenchida com o país do tomador
@author Fabio M Parra   
@since 06/02/2026
@version 12.1.2510 
/*///-----------------------------------------------------------------------

static function fPaisprest()

Local cPaisPres     := ""   
Local cstring	    := ""   
Private aMvEndPres	:= &(SuperGetMV("MV_ENDPRES",,"{,,,,,}")) //Parametro que aponta para o campo da SC5 para pegar as informações da prestação do serviço
    if Empty(aMvEndPres)
        aMvEndPres := {,,,,,,} //inicializa o array para evitar erro
    endif
    //Busca o campo do país da prestação do serviço na SC5
    If !Empty(aMvEndPres[06]) .and. SC5->(FieldPos(aMvEndPres[06])) > 0
        cPaisPres	:= Alltrim(SC5->&(aMvEndPres[06])) //País da prestação
    EndIf
   	//Se o campo de país não estiver preenchido, a tag é preenchida com o país do tomador
    If Empty(cPaisPres) .and. !Empty(aDest[11]) 
        cPaisPres	:= Alltrim(aDest[11]) //País do endereço Tomador
    EndIf
    // Se estiver preenchido com a consulta padrão da tabela de paises, haverão 3 dígitos, então a função Posicione() pega o código e faz uma busca na tabela SYA retornando o código bacem do país.
	If !Empty(cPaisPres) .and. (len(alltrim(cPaisPres)) < 4) 
			cPaisPres := Posicione("SYA",1,xFilial("SYA")+cPaisPres,"YA_SISEXP")
    EndIf
    //função TSSpais espera o código do país no formato bacen com 5 dígitos
    if len(cPaisPres) < 5
       cPaisPres :=  StrZero( val(cPaisPres), 5 )
    endif 
    //Converte o código do país para o formato ISO 3166-1 alpha-2    
    cString := Tsspais(cPaisPres)

Return cString


//-----------------------------------------------------------------------
/*/{Protheus.doc}  Method fPaisprest
Função  Retorna o código da tag tpRetPisCofins
Parâmetros: valores de retenção de PIS, COFINS e CSLL
@author RICARDO CAVALCANTE PAULINO
@since 12/02/2026
@version 12.1.2510 

tabela de referência para o código de retenção:
PIS	COFINS	CSLL	Código
F	    F	    F	    0
T	    T	    T	    3
T	    T	    F	    4
T	    F	    F	    5
F	    T	    F	    6
F	    T	    T	    7
F	    F	    T	    8
T	    F	    T	    9
/*///-----------------------------------------------------------------------
Static Function GetTpRetPisCofins( nValPis, nValcof, nValcsl )

Local cTpRet    := "0"
Local lPisRet   := .F.
Local lCofRet   := .F.
Local lCslRet   := .F. 

Default nValPis := 0
Default nValcof := 0
Default nValcsl := 0

lPisRet   := (nValpis > 0)
lCofRet   := (nValcof > 0)
lCslRet   := (nValcsl > 0)


// Nenhum retido
If !lPisRet .And. !lCofRet .And. !lCslRet
cTpRet := "0"

// PIS, COFINS e CSLL retidos
ElseIf lPisRet .And. lCofRet .And. lCslRet
cTpRet := "3"

// PIS e COFINS retidos, CSLL não
ElseIf lPisRet .And. lCofRet .And. !lCslRet
cTpRet := "4"

// Só PIS retido
ElseIf lPisRet .And. !lCofRet .And. !lCslRet
cTpRet := "5"
// Só COFINS retido
ElseIf !lPisRet .And. lCofRet .And. !lCslRet
cTpRet := "6"

// COFINS e CSLL retidos, PIS não
ElseIf !lPisRet .And. lCofRet .And. lCslRet
cTpRet := "7"

// Só CSLL retida
ElseIf !lPisRet .And. !lCofRet .And. lCslRet
cTpRet := "8"

// PIS e CSLL retidos, COFINS não
ElseIf lPisRet .And. !lCofRet .And. lCslRet
cTpRet := "9"
EndIf

Return cTpRet
//-----------------------------------------------------------------------
/*/{Protheus.doc} Static Function gtotTribPrc
	Responsável por gerar o grupo totTrib do XML Unico

	@param cMoeda		Código da moeda.
	@return cRetorno	Código da moeda conforme padrão ISO 4217.

	@author Rafael Gama Inacio
	@since 14.01.2026
	@version 12.1.2410
	@return string
/*///--------------------------------------------------------------------
Static Function gtotTribPrc(cNBS)

	Local cString		:= ""
	Local cMVOPTSIMP	:= allTrim( getMV( "MV_OPTSIMP",, "2" ) ) // optante do simples
	Local nTribFed		:= 0
	Local nTribEst		:= 0
	Local nTribMun		:= 0
	Local nTribSN		:= 0

	Default cNBS		:= ""

	if cMVOPTSIMP == "2"
		if !Empty(cNBS)
			DbSelectArea("CLK")
			CLK->(DbSetOrder(1)) //CLK_FILIAL+CLK_CODNBS+CLK_EX+CLK_UF+DTOS(CLK_DTINIV)+DTOS(CLK_DTFIMV)

			if CLK->(DbSeek(xFilial("CLK")+cNBS))
				nTribFed		:= CLK_ALQNAC
				nTribEst		:= CLK_ALQEST
				nTribMun		:= CLK_ALQMUN

			endif

			cString += "<totTrib>"
			
			cString += 		"<pTotTrib>"
			cString += 			"<pTotTribFed>"+ cValtoChar(nTribFed) +"</pTotTribFed>"
			cString += 			"<pTotTribEst>"+ cValtoChar(nTribEst) +"</pTotTribEst>"
			cString += 			"<pTotTribMun>"+ cValtoChar(nTribMun) +"</pTotTribMun>"
			cString += 		"</pTotTrib>"

			cString += "</totTrib>"

			CLK->(DbCloseArea())
		endif

	elseif cMVOPTSIMP == "1"

		cString += 	"<totTrib>"
		cString += 	    "<pTotTribSN>"+ cValtoChar(nTribSN) +"</pTotTribSN>"
		cString += 	"</totTrib>"
		
	endif
	
Return(cString)

//-----------------------------------------------------------------------
/*/{Protheus.doc} Static Function gtotTribVal
	Responsável por gerar o grupo totTrib do XML Unico

	@param aLeiTrp		array com os valores dos tributos federais, estaduais e municipais.
	@return cRetorno	string com o grupo totTrib montado.

	@author valter da silva 
	@since 24.02.2026
	@version 12.1.2510
	@return string
/*///--------------------------------------------------------------------
Static Function gtotTribVal(aLeiTrp)

	Local cString   := ""
	Local nTribFed	:= 0
	Local nTribEst	:= 0
	Local nTribMun	:= 0
    Default aLeiTrp := {0,0,0}

    If Len(aLeiTrp) > 0
        nTribFed += aLeiTrp[1]
        nTribEst += aLeiTrp[2]
        nTribMun += aLeiTrp[3]
    EndIf

	cString += '<totTrib>'
    cString +=  '<vTotTrib>'
    cString +=      '<vTotTribFed>'+  ALLTRIM( STR(nTribFed,15,2) ) +'</vTotTribFed>'
    cString +=      '<vTotTribEst>'+  ALLTRIM( STR(nTribEst,15,2) ) +'</vTotTribEst>'
    cString +=      '<vTotTribMun>'+Alltrim(Str(nTribMun,15,2))+'</vTotTribMun>'
    cString +=  '</vTotTrib>'
    cString += "</totTrib>"

Return(cString)

