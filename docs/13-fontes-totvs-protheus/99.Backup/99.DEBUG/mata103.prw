#INCLUDE "MATA103.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "TBICONN.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWMVCDEF.CH"
#INCLUDE "FWADAPTEREAI.CH"
#INCLUDE 'FWLIBVERSION.CH'
#DEFINE FRETE   04	// Valor total do Frete
#DEFINE VALDESP 05	// Valor total da despesa
#DEFINE SEGURO  07	// Valor total do seguro

// DefiniÁıes para indexar os elementos do Array aCount - Rateio de Impostos
#DEFINE idxIRR 1
#DEFINE idxPIS 2
#DEFINE idxCOF 3
#DEFINE idxCSL 4 

Static __aAliasInDic 
Static aBkpHeader 	:= {}
Static aCposSN1 	:= {} 
Static lN1Staus
Static lN1Especie
Static lN1NFItem
Static lN1Prod
Static lN1Orig
Static lN1CstPis
Static lN1AliPis
Static lN1CstCof
Static lN1AliCof
Static cMT103Mot  	:= ""
Static cMT103Hist 	:= ""
Static lIsIssBx   	:= FindFunction("IsIssBx")
Static lPLSMT103  	:= findFunction("PLSMT103")	
Static lHasTplDro 	:= HasTemplate("DRO")
Static nTamX3A2CD	:= 0
Static nTamX3A2LJ	:= 0
Static lIsRussia	:= cPaisLoc == "RUS"
Static lLGPD  		:= FindFunction("SuprLGPD") .And. SuprLGPD()
Static oRatIRF		:= NIL 
Static __lIntPFS  	:= SuperGetMv("MV_JURXFIN",.T., .F.)
Static __lEmpPub	:= NIL
Static oTempTable	:= Nil

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ MATA103  ≥ Autor ≥ Edson Maricate        ≥ Data ≥ 24.01.2000 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Notas Fiscais de Entrada                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ Generico                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function MATA103(xAutoCab,xAutoItens,nOpcAuto,lWhenGet,xAutoImp,xAutoAFN,xParamAuto,xRateioCC,lGravaAuto,xCodRSef,xCodRet,xAposEsp,xNatRend,xAutoPFS,xCompDKD,lGrvGF,xAutoCSD)
Local nPos      	:= 0 
Local bBlock    	:= {|| Nil}
Local nX	   		:= 0
Local nAutoPC		:= 0
Local aCores    	:= {}
Local aCoresUsr   := {}
Local cFiltro     := ""
Local lCtb105Mvc  := FindFunction("CTB105MVC")
Local lIntWMS     := SuperGetMV("MV_INTWMS",.F.,.F.)
Local lCheckVer   := .F.
Local cCONFFIS	  := SuperGetMV("MV_CONFFIS",.F.,"N")

Default lGravaAuto 	:= .T.
Default lGrvGF := .F.

Private l103Auto	:= (xAutoCab<>NIL .And. xAutoItens<>NIL)
Private l103GAuto	:= lGravaAuto
Private l103GGFAut	:= lGrvGF
Private aAutoCab	:= {}
Private aAutoImp    := {}
Private aAutoItens 	:= {}
Private aParamAuto 	:= {}
Private aRateioCC	:= {}
Private aAutoPFS    := {}
Private aRotina 	:= MenuDef() // Foi modificado para o SIGAGSP.
Private cCadastro	:= OemToAnsi(STR0009) //"Documento de Entrada"
Private aBackSD1    := {}
Private aBackSDE    := {}
Private aNFEDanfe   := {}
Private bBlockSev1	:= {|| Nil}
Private bBlockSev2	:= {|| Nil}
Private aAutoAFN	:= {}
Private aDanfeComp  := {}
Private aRegsLock	:={}
Private lImpPedido	:= .F.
Private cCodRSef    := ""
Private aColsOrig   := {}
Private _aDivPNF    := {}	  // Inicializa array do cadastro de divergencias - FW
Private aAposEsp    := {}
Private aNatRend	:= {}
Private aCompFutur  := {}
Private cFornISS    := ""
Private cLojaISS    := ""
Private dVencISS    := CTOD("")
Private lTOPDRFRM   := FindFunction("A120RDFRM") .And. A120RDFRM("A103")
Private cFilUF		:= "" 
Private axCodRet	:=	if(!Empty(xCodRet),xCodRet,{})
Private lIntermed	:= A103CPOINTER()
PRIVATE cQueryC7   	:= ""
Private nQtdAnt    	:= 0
Private nInicio		:= Seconds()
Private nSegsTot	:= 0
Private lAtuDupPC	:= .F.
Private aAutoDKD	:= {}

//Inicializa os parametros DEFAULTS da rotina
DEFAULT lWhenGet := .F.
DEFAULT xCodRSef := ""
DEFAULT xRateioCC:= {}

If SF1->( FieldPos( "F1_GF" ) ) > 0
	aCores	:= {	{'Empty(F1_STATUS).And.F1_GF<>"GF"'	,'ENABLE'			},;	// NF Nao Classificada
					{'Empty(F1_STATUS).And.F1_GF=="GF"'	,'BR_MARRON_OCEAN'	},;	// NF N„o Classificada com Guarda Fiscal
					{'F1_STATUS=="B"'					,'BR_LARANJA'		},;	// NF Bloqueada
					{'F1_STATUS=="C"'					,'BR_VIOLETA'   	},;	// NF Bloqueada s/classf.
					{'F1_STATUS=="D"'					,'BR_BRANCO'	    },;	// Evento desacordo aguardando SEFAZ
					{'F1_STATUS=="E"'					,'BR_AZUL_CLARO'  	},;	// Evento desacordo vinculado
					{'F1_STATUS=="F"'					,'BR_VERDE_ESCURO' 	},;	// Evento desacordo com problemas
					{'F1_TIPO=="N"'						,'DISABLE'   		},;	// NF Normal
					{'F1_TIPO=="P"'						,'BR_AZUL'   		},;	// NF de Compl. IPI
					{'F1_TIPO=="I"'						,'BR_MARROM' 		},;	// NF de Compl. ICMS
					{'F1_TIPO=="C"'						,'BR_PINK'   		},;	// NF de Compl. Preco/Frete
					{'F1_TIPO=="B"'						,'BR_CINZA'  		},;	// NF de Beneficiamento
					{'F1_TIPO=="D"'						,'BR_AMARELO'		} }	// NF de Devolucao
Else
	aCores	:= {	{'Empty(F1_STATUS)'					,'ENABLE'			},;	// NF Nao Classificada
					{'F1_STATUS=="B"'					,'BR_LARANJA'		},;	// NF Bloqueada
					{'F1_STATUS=="C"'					,'BR_VIOLETA'   	},;	// NF Bloqueada s/classf.
					{'F1_STATUS=="D"'					,'BR_BRANCO'	    },;	// Evento desacordo aguardando SEFAZ
					{'F1_STATUS=="E"'					,'BR_AZUL_CLARO'  	},;	// Evento desacordo vinculado
					{'F1_STATUS=="F"'					,'BR_VERDE_ESCURO' 	},;	// Evento desacordo com problemas
					{'F1_TIPO=="N"'						,'DISABLE'   		},;	// NF Normal
					{'F1_TIPO=="P"'						,'BR_AZUL'   		},;	// NF de Compl. IPI
					{'F1_TIPO=="I"'						,'BR_MARROM' 		},;	// NF de Compl. ICMS
					{'F1_TIPO=="C"'						,'BR_PINK'   		},;	// NF de Compl. Preco/Frete
					{'F1_TIPO=="B"'						,'BR_CINZA'  		},;	// NF de Beneficiamento
					{'F1_TIPO=="D"'						,'BR_AMARELO'		} }	// NF de Devolucao
EndIf

nTamX3A2CD	:= Iif(nTamX3A2CD==0,TamSX3("A2_COD")[1],nTamX3A2CD)
nTamX3A2LJ	:= Iif(nTamX3A2LJ==0,TamSX3("A2_LOJA")[1],nTamX3A2LJ)

cFornISS    := Space(nTamX3A2CD)
cLojaISS    := Space(nTamX3A2LJ)

oRatIRF	:= A103CRatIR()

SXV->( DbSetOrder(2) ) //XV_ALIAS + XV_MASHUP
If SXV->( DbSeek("SF1") )
	AddMashupAlias({"SF1"})
EndIf

If lCtb105Mvc .and. IsInCallStack("GFEA065In")
	CTB105MVC(.T.)
EndIf
//-- Forca a criacao do arq. dcf pois o sigamdi nao cria o arq.
If lIntWMS
	DbSelectArea("DCF")
EndIf

If l103Auto
	For nX:= 1 To Len(xAutoItens)
		If (nAutoPC := Ascan(xAutoItens[nx],{|x| x[1]== "D1_PEDIDO"})) > 0
		     If Empty(xAutoItens[nX][nAutoPC][3])
		     	xAutoItens[nX][nAutoPC][3]:= "vazio().or. A103PC()"
			 EndIf
		EndIf
	Next
EndIf

//P.E. Utilizado para adicionar botoes ao Menu Principal
IF ExistBlock("MA103OPC") .And. !l103Auto
	aRotNew := ExecBlock("MA103OPC",.F.,.F.,aRotina)
	For nX := 1 to len(aRotNew)
		aAdd(aRotina,aRotNew[nX])
	Next
Endif

//Aba Danfe
A103CheckDanfe(1)

//Ajusta as cores se utilizar coletor de dados
If cCONFFIS == "S"
	aCores    := {}
	AAdd(aCores,{ 'Empty(F1_STATUS) .And.((F1_STATCON $ "1|4") .Or. Empty(F1_STATCON))','ENABLE'			})	// NF Nao Classificada
	AAdd(aCores,{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="N" .AND. (F1_STATUS<>"B" .AND. F1_STATUS<>"C")', 'DISABLE'		})  // NF Normal
	AAdd(aCores,{ 'F1_STATUS=="B"'															, 'BR_LARANJA'	})  // NF Bloqueada
	AAdd(aCores,{ 'F1_STATUS=="C"'															, 'BR_VIOLETA'	})  // NF Bloqueada s/classf.
	AAdd(aCores,{ 'F1_STATUS=="D"'															,'BR_BRANCO' })	// Evento desacordo aguardando SEFAZ
	AAdd(aCores,{ 'F1_STATUS=="E"'															,'BR_AZUL_CLARO' 	  	})	// Evento desacordo vinculado
	AAdd(aCores,{ 'F1_STATUS=="F"'															,'BR_VERDE_ESCURO' 	  	})	// Evento desacordo com problemas
	AAdd(aCores,{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="P"'	 	, 'BR_AZUL'		})  // NF de Compl. IPI
	AAdd(aCores,{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="I"'		, 'BR_MARROM'	})  // NF de Compl. ICMS
	AAdd(aCores,{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="C"'		, 'BR_PINK'		})  // NF de Compl. Preco/Frete
	AAdd(aCores,{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="B"'		, 'BR_CINZA'	})  // NF de Beneficiamento
	AAdd(aCores,{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="D"'    	, 'BR_AMARELO'	})  // NF de Devolucao
	AAdd(aCores,{ '!(F1_STATCON $ "1|4") .AND. !EMPTY(F1_STATCON)'							, 'BR_PRETO'	})  // NF Bloq. para Conferencia
EndIf

//Checa a assinatura dos fontes complementares da MATA103 est„o corretos.
lCheckVer := A103ChkSig()

//Verifica a permissao do programa em relacao aos modulos
If lCheckVer .AND. AMIIn(2,4,11,12,14,17,39,41,42,43,97,44,67,69,72,87)
	//Salva a pilha fiscal
	MaFisSave()
	MaFisEnd()

	//Verifica o tipo de rotina a ser executada
	aAutoCab   := xAutoCab
	aAutoItens := xAutoItens
	aRateioCC  := xRateioCC
	cCodRSef   := xCodRSef
	aAutoAFN   := Iif(xAutoAFN<>Nil,xAutoAFN,{})
	aAutoImp   := IIf(xAutoImp<>NIL,xAutoImp,{})
	aParamAuto := IIf(xParamAuto<>NIL,xParamAuto,{})
	aAposEsp   := IIf(xAposEsp<>NIL,xAposEsp,{})
	aNatRend   := IIf(xNatRend<>NIL,xNatRend,{})
	aAutoPFS   := IIf(xAutoPFS<>NIL,xAutoPFS,{})
	aAutoDKD   := IIf(xCompDKD<>NIL,xCompDKD,{})
	aAutoCSD   := IIf(xAutoCSD<>NIL,xAutoCSD,{})//Consolidador XML	
	Do Case
	Case lWhenGet .Or. ( !l103Auto .And. nOpcAuto <> Nil )

		Do Case
		Case nOpcAuto == 3
			INCLUI := .T.
			ALTERA := .F.
		Case nOpcAuto == 4
			INCLUI := .F.
			ALTERA := .T.
		OtherWise
			INCLUI := .F.
			ALTERA := .F.
		EndCase

		DbSelectArea('SF1')
		nPos := Ascan(aRotina,{|x| x[4]== nOpcAuto})
		If ( nPos <> 0 )
			bBlock := &( "{ |a,b,c,d,e| " + aRotina[ nPos,2 ] + "(a,b,c,d,e) }" )
			Eval( bBlock, Alias(), (Alias())->(Recno()),nPos,lWhenGet)
		EndIf
	Case l103Auto
		AAdd( aRotina, {OemToAnsi(STR0006), "A103NFiscal", 3, 20 } ) //"Exclusao EIC"
		AAdd( aRotina, {OemToAnsi(STR0006), "A103NFiscal", 3, 21 } ) //"Exclusao TMS"
		DEFAULT nOpcAuto := 3//alteraw
		MBrowseAuto(nOpcAuto,Aclone(aAutoCab),"SF1")
	OtherWise
		//Interface com o usuario via Mbrowse
		Set Key VK_F12 To FAtiva()
		
		//Ponto de entrada para pre-validar os dados a serem exibidos.
		IF ExistBlock("M103BROW")
			ExecBlock("M103BROW",.f.,.f.)
		EndIf
		
		//Ponto de entrada para inclus„o de nova COR da legenda
		If ( ExistBlock("MT103COR") )
			aCoresUsr := ExecBlock("MT103COR",.F.,.F.,{aCores})
			If ( ValType(aCoresUsr) == "A" )
				aCores := aClone(aCoresUsr)
			EndIf
		EndIf

		//Ponto de entrada para verificacao de filtros na Mbrowse
		If  ExistBlock("M103FILB")
			cFiltro := ExecBlock("M103FILB",.F.,.F.)
			If Valtype(cFiltro) <> "C"
				cFiltro := ""
			EndIf
		EndIf

		If Empty(cFiltro)
			SF1->(dbClearFilter())
			SET FILTER TO
		Endif

		mBrowse(6,1,22,75,"SF1",,,,,,aCores,,,,,,,, IF(!Empty(cFiltro),cFiltro, NIL))
		Set Key VK_F12 To
	EndCase
	MaFisRestore()
EndIf

If aBkpHeader <> Nil
	 aBkpHeader:= Nil
Endif

If aCposSN1 <> Nil
	aCposSN1 := Nil
Endif

If !Empty(oRatIRF) 
	oRatIRF:Clean()
	FreeObj(oRatIRF)
EndIf

Return(.T.)

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103NFiscal≥ Autor ≥ Edson Maricate       ≥ Data ≥24.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Programa de Incl/Alter/Excl/Visu.de NF Entrada             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103NFiscal(ExpC1,ExpN1,ExpN2,ExpL1,ExpL2)	              ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpC1 = Alias do arquivo                                   ≥±±
±±≥          ≥ ExpN1 = Numero do registro                                 ≥±±
±±≥          ≥ ExpN2 = Numero da opcao selecionada                        ≥±±
±±≥          ≥ ExpL1 = lWhenGet (default = .F.)                           ≥±±
±±≥          ≥ ExpL2 = Estorno de NF Classificada (chamada MATA140)       ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103NFiscal(cAlias,nReg,nOpcx,lWhenGet,lEstNfClass)

Local lContinua		:= .T.
Local l103Inclui	:= .F.
Local l103Exclui	:= .F.
Local lMT103NFE		:= Existblock("MT103NFE")
Local lTMT103NFE	:= ExistTemplate("MT103NFE")
Local lIntACD		:= SuperGetMV("MV_INTACD",.F.,"0") == "1" 
Local lClaNfCfDv 	:= .F.
Local lDigita		:= .F.
Local lAglutina		:= .F.
Local lQuery		:= .F.
Local lContabiliza  := .F.
Local lGeraLanc		:= .F.
Local lPyme			:= If( Type( "__lPyme" ) <> "U", __lPyme, .F. )
Local lClassOrd		:= ( SuperGetMV( "MV_CLASORD" ) == "1" )  //Indica se na classificacao do documento de entrada os itens devem ser ordenados por ITEM+COD.PRODUTO
Local lNfeOrd		:= ( GetNewPar( "MV_NFEORD" , "2" ) == "1" ) // Indica se na visualizacao do documento de entrada os itens devem ser ordenados por ITEM+COD.PRODUTO
Local lExcViaEIC	:= .F.
Local lExcViaTMS	:= .F.
Local lProcGet		:= .T.
Local lTxNeg        := .F.
Local nTaxaMoeda	:= 0
Local lConsMedic    := .F.
Local lRatLiq       := .T.
Local lRatImp       := .F.
Local lNfGarEst 	:= .F. //Nf de garantia estendida, exibe campo D1_CBASEAF do ATF na grid.
Local lMvAtuComp    := SuperGetMV("MV_ATUCOMP",,.F.)
Local lRet := .T.
Local aArea2 := {}
Local aMT103BCLA	:= {}
Local lMT103BCLA	:= ExistBlock("MT103BCLA")
Local lRetBCla		:= .F.
Local lTColab       := .F.
Local lSubSerie     := cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_SUBSERI")) > 0 .And. SuperGetMv("MV_SUBSERI",.F.,.F.)
Local lDHQInDic     := AliasInDic("DHQ") .And. SF4->(ColumnPos("F4_EFUTUR") > 0)
Local lMt103Com     := FindFunction("A103FutVld")
Local lTrbGen       := IIf(FindFunction("ChkTrbGen"),ChkTrbGen("SD1", "D1_IDTRIB"),.F.) // Verificacao se pode ou nao utilizar tributos genericos
Local nTmpN			:= 0
Local nRecSF1		:= 0
Local nOpc			:= 0
Local nItemSDE		:= 0
Local nTpRodape		:= 1
Local nX			:= 0
Local nY			:= 0
Local nCounterSD1	:= 0
Local nMaxCodes		:= SetMaxCodes( 9999 )
Local nIndexSE2		:= 0
Local nScanBsPis	:= 0
Local nScanVlPis	:= 0
Local nScanAlPis	:= 0
Local nScanBsCof	:= 0
Local nScanVlCof	:= 0
Local nScanAlCof	:= 0
Local nLoop			:= 0
Local nTrbGen       := 0
Local nColsSE2      := 0
Local lPCCBaixa		:= SuperGetMv("MV_BX10925",.T.,"2") == "1"
Local cModRetPIS	:= GetNewPar( "MV_RT10925", "1" )
Local aStruSF3		:= {}
Local aStruSDE		:= {}
Local aStruSE2		:= {}
Local aStruSD1		:= {}
Local aRecSD1		:= {}
Local aRecSE1		:= {}
Local aRecSE2		:= {}
Local aRecSF3		:= {}
Local aRecSC5		:= {}
Local aRecSDE		:= {}
Local aHeadSDE		:= {}
Local aHeadSE2		:= {}
Local aColsSE2		:= {}
Local aHeadSEV		:= {}
Local aColsSEV		:= {}
Local aColsSDE		:= {}
Local aHistor		:= {}
Local aInfo			:= {}
Local aPosGet		:= {}
Local aPosObj		:= {}
Local aPages		:= {"HEADER"}
Local aInfForn		:= {"","",CTOD("  /  /  "),CTOD("  /  /  "),"","","",""}
Local a103Var		:= {0,0,0,0,0,0,0,0,0,0}
Local aButControl	:= {}
Local aTitles		:= {} // foi alterado por causa do SIGAGSP.
Local aSizeAut		:= {}
Local aButVisual	:= {}
Local aButtons		:= {}
Local aMemUser      := {}
Local aRateio		:= {0,0,0}
Local aFldCBAtu	    // foi alterado por causa do SIGAGSP.
Local aRecClasSD1	:= {}
Local aRelImp		:= MaFisRelImp("MT100",{ "SD1" })
Local aMultas       := {}
Local aAreaSD1	:= {}
Local aColTrbGen    := {}
Local aParcTrGen    := {}
Local cIdsTrGen		:= ""//vari·vel que vai guardar os ids de tributos genÈricos.
Local cTituloDlg	:= IIf(Type("cCadastro") == "C" .And. Len(cCadastro) > 0,cCadastro,OemToAnsi(STR0009)) //"Documento de Entrada"
Local cPrefixo		:= IIf(Empty(SF1->F1_PREFIXO),&(SuperGetMV("MV_2DUPREF")),SF1->F1_PREFIXO)
Local cHistor		:= ""
Local cItem			:= ""
Local cItemSDE		:= ""
Local cQuery		:= ""
Local cAliasSF3		:= "SF3"
Local cAliasSDE		:= "SDE"
Local cAliasSE2		:= "SE2"
Local cAliasSD1		:= "SD1"
Local cAliasSB1		:= "SB1"
Local cNumNfGFE		:= ""
Local nHoras 		:= 0
Local nSpedExc 		:= GetNewPar("MV_SPEDEXC",24)
Local dDtDigit 		:= dDataBase
Local dCtbValiDt    := Ctod("")
Local cVarFoco		:= "     "
Local cNatureza		:= ""
Local cCpBasePIS	:= ""
Local cCpValPIS		:= ""
Local cCpAlqPIS		:= ""
Local cCpBaseCOF	:= ""
Local cCpValCOF		:= ""
Local cCpAlqCOF		:= ""
Local nPosRec		:= 0
Local oDlg
Local oHistor
Local oLivro
Local oCombo
Local oCodRet
Local bKeyF12		:= Nil
Local bPMSDlgNF		:= {||PmsDlgNF(nOpcx,cNFiscal,Substr(cSerie,1,3),cA100For,cLoja,cTipo)} // Chamada da Dialog de Gerenc. Projetos
Local bCabOk		:= {|| .T.}
Local bIPRefresh	:= {|| MaFisToCols(aHeader,aCols,,"MT100"),Eval(bRefresh),Eval(bGdRefresh), A103PosFld()}	// Carrega os valores da Funcao fiscal e executa o Refresh
Local bWhileSD1		:= { || .T. }
Local lMT103NAT		:= Existblock("MT103NAT")
Local lGspInUseM	:= If(Type('lGspInUse')=='L', lGspInUse, .F.)
Local aAUTOISS		:= &(GetNewPar("MV_AUTOISS",'{"","","",""}'))
Local aNFEletr		:= {}
Local aNoFields     := {}
Local cDescri		:= Space(Len(SE2->E2_NOMFOR))
Local nNFe			:= 0
Local nConfNF       := 0
Local cDelSDE 	    := ""
Local aCodR	        := {}
Local cRecIss	    :=	"1"
Local oRecIss
Local nLancAp		:= 0
Local nInfDiv       := 0
Local nInfAdic      := 0
Local nDivImp		:= 0
Local nPosGetLoja   := 0
Local aHeadCDA		:= {}
Local aColsCDA		:= {}
Local aHeadCDV		:= {}
Local aColsCDV		:= {}
Local lRatAFN       := .T.
Local aCtbInf       := {} //Array contendo os dados para contabilizacao online:
					    //		[1] - Arquivo (cArquivo)
						//		[2] - Handle (nHdlPrv)
						//		[3] - Lote (cLote)
						//      [4] - Habilita Digitacao (lDigita)
						//      [5] - Habilita Aglutinacao (lAglutina)
						//      [6] - Controle Portugal (aCtbDia)
						//		[7,x] - Campos flags atualizados na CA100INCL
						//		[7,x,1] - Descritivo com o campo a ser atualizado (FLAG)
						//		[7,x,2] - Conteudo a ser gravado na flag
						//		[7,x,3] - Alias a ser atualizado
						//		[7,x,4] - Recno do registro a ser atualizado
Local aMT103CTB  	:= {}
Local lExcCmpAdt 	:= .T.
Local cStatCon   	:= ""
Local nQtdConf   	:= 0
Local oList
Local aListBox   	:= {}
Local oEnable    	:= LoadBitmap( GetResources(), "ENABLE" )
Local oDisable   	:= LoadBitmap( GetResources(), "DISABLE" )
Local lCompAdt	 	:= .F.
Local aPedAdt	 	:= {}
Local aRecGerSE2 	:= {}
Local nPosPC 		:= 0
Local nPosItPC   	:= 0
Local nPosItNF		:= 0
Local nPosRat		:= 0
Local nVlrMetr  	:= 0

//Verifica se a funcionalidade Lista de Presente esta ativa e aplicada
Local a			 := 0
Local aDigEnd	   	:= {}
Local lDistMov		:= SuperGetMV("MV_DISTMOV",.F.,.F.)

//Variaveis utilizadas na integracao NG
Local nG 		:= 0
Local nPORDEM	:= 0

//Tratamendo de ISS por municipio.
Local nInfISS := 0
Local lISSxMun := SuperGetMV("MV_ISSXMUN",.F.,.F.)
Local aInfISS	:= Iif(lISSxMun,{{CriaVar("CC2_CODMUN",.F.),CriaVar("CC2_MUN"),CriaVar("CC2_EST"),CriaVar("CC2_MDEDMA"),CriaVar("CC2_MDEDSR"),;
					CriaVar("CC2_PERMAT"),CriaVar("CC2_PERSER")},;
					{CriaVar("D1_TOTAL"),CriaVar("D1_ABATISS"),CriaVar("D1_ABATMAT"),CriaVar("D1_BASEISS"),CriaVar("D1_VALISS")},;
           	        {CriaVar("D1_TOTAL"),CriaVar("D1_ABATINS"),CriaVar("D1_ABATINS"),CriaVar("D1_BASEINS"),CriaVar("D1_VALINS")}},{})
Local aObjetos := aClone(aInfISS)

Local lIntegGFE := SuperGetMV("MV_INTGFE",.F.,.F.) .And. SuperGetMV("MV_INTGFE2",.F.,"2") $ "1" .And. SuperGetMv("MV_GFEI10",.F.,"2") == "1"
//Verifica se a rotina foi chamada a partir da conferencia de servicos II - Financeiro
Local lFina686 := 	.F. 
Local lMata103 := 	.F.
Local lMata102N := 	.F.
Local lMata101N := 	.F.
Local oSize 	:= nil
Local aRotAux 	:= MenuDef()
Local lCTBC661 	:= IsInCallStack("CTBC661")
Local aRotBkp	:= {}

// Conferencia fisica do SIGAACD
Local cMVTPCONFF := SuperGetMV("MV_TPCONFF",.F.,"1")
Local cMVCONFFIS := SuperGetMV("MV_CONFFIS",.F.,"N")

// Informacoes Adicionais do Documento
Local oDescMun
Local cDescMun := ""

Local aRetInt := {}
Local cMsgRet	:= ""
Local cInfISS 		:= ""
Local lWmsCRD  := SuperGetMV("MV_WMSCRD",.F.,.F.)
Local nFR3_TIPO := TAMSX3("FR3_TIPO")[1]
Local aImpItem	:= {}
Local lIntGC	 := IIf((SuperGetMV("MV_VEICULO",,"N")) == "S",.T.,.F.)
Local lCtbDtBl	 := IIf((SuperGetMV("MV_CTBDTBL",.F.,1)) == 1,.T.,.F.) // 1 = data digitaÁ„o >1 = data base
Local lDclNew 	:= SuperGetMv("MV_DCLNEW",.F.,.F.)
Local aTitImp    := {}
Local nRecSE2    := 0
Local aAreaD1	 := {}
Local nPosNFOri  := 0
Local nPosSerOri := 0
Local nPosForDev := 0
Local nPosLojDev := 0
Local lDevol	 := .F.
Local lUsaGCT    := A103GCDisp()
Local lNgMnTes		:= SuperGetMV("MV_NGMNTES") == "S" 
Local lNgMntCm		:= SuperGetMV("MV_NGMNTCM",.F.,"N") == "S"
Local cFilialC7		:= xFilEnt(xFilial("SC7"),"SC7")
Local cE1Cliente
Local cE1Loja
Local cE1NReduz
Local aRecSE5	 := {}
Local lIntePms	 := IntePms()
Local lIntTms	 := IntTMS()
Local lIntWMS	 := IntWMS()
Local lMT103FIN	 := ExistBlock("MT103FIN")
Local lPropFret  := SuperGetMV("MV_FRT103E",.F.,.T.)
Local aCAMPTPZ   := {}
Local lExiTmpTb  := oTempTable == Nil
Local lMT103RCC	 := ExistBlock( "MT103RCC",,.T. )
Local lCsdXML 	 := SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA") .and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")
Local aRatIRF	 := {}
Local lMvLocBac	 := SuperGetMv("MV_LOCBAC",.F.,.F.) //IntegraÁ„o com MÛdulo de LocaÁıes SIGALOC
Local lFcLOCM008 := FindFunction("LOCM008")

nTamX3A2CD	:= Iif(nTamX3A2CD==0,TamSX3("A2_COD")[1],nTamX3A2CD)
nTamX3A2LJ	:= Iif(nTamX3A2LJ==0,TamSX3("A2_LOJA")[1],nTamX3A2LJ)

nPosGetLoja := IIF(nTamX3A2CD< 10,(2.5*nTamX3A2CD)+(110),(2.8*nTamX3A2CD)+(100))

If Type("cFornIss") == "U"
	cFornIss := Space(nTamX3A2CD)
EndIf
If Type("cLojaIss") == "U"
	cLojaIss := Space(nTamX3A2LJ)
EndIf
If Type("dVencISS") == "U"
	dVencISS := CtoD("")
EndIf
If Type("lIntermed") == "U" 
	lIntermed := A103CPOINTER()
Endif

// foi alterado por causa do SIGAGSP.
aAdd(aTitles, OemToAnsi(STR0010)) //"Totais"
aAdd(aTitles, OemToAnsi(STR0011)) //"Inf. Fornecedor/Cliente"
aAdd(aTitles, OemToAnsi(STR0012)) //"Descontos/Frete/Despesas"
aAdd(aTitles, OemToAnsi(STR0014)) //"Livros Fiscais"
aAdd(aTitles, OemToAnsi(STR0015)) //"Impostos"
aAdd(aTitles, OemToAnsi(STR0013)) //"Duplicatas"

aFldCBAtu	:= Array(Len(aTitles)) // foi alterado por causa do SIGAGSP.

PRIVATE oLancApICMS
PRIVATE oLancCDV
PRIVATE oFisRod
PRIVATE cDirf		:= Space(Len(SE2->E2_DIRF))
PRIVATE cCodRet		:= Space(Len(SE2->E2_CODRET))
PRIVATE l103Visual	:= .F.
PRIVATE lReajuste	:= .F.
PRIVATE lAmarra		:= .F.
PRIVATE lConsLoja	:= .F.
PRIVATE lPrecoDes	:= .F.
PRIVATE lVldAfter	:= .F.
PRIVATE lMt100Tok	:= .T.
PRIVATE cTipo		:= ""
PRIVATE c103Tp		:= ""
PRIVATE cTpCompl	:= ""
PRIVATE cFormul		:= ""
PRIVATE cNFiscal	:= ""
PRIVATE cSerie		:= ""
PRIVATE cSubSerie	:= ""
PRIVATE cA100For	:= ""
PRIVATE cLoja		:= ""
PRIVATE cEspecie	:= ""
PRIVATE cCondicao	:= ""
PRIVATE cForAntNFE	:= ""
PRIVATE cLojAntNFE 	:= ""
PRIVATE dDEmissao	:= dDataBase
PRIVATE n			:= 1
PRIVATE nMoedaCor	:= 1
PRIVATE nTaxa       := 0
PRIVATE nValFat		:= 0
PRIVATE aCols		:= {}
PRIVATE aColsNF		:= {}  //Variavel utilizada pela Funcao NfeRFldFin - MATA103x para alimentar a variavel aColsTit
PRIVATE aHeader		:= {}
PRIVATE aRatVei		:= {}
PRIVATE aRatFro		:= {}
PRIVATE aArraySDG	:= {}
PRIVATE aRatAFN		:= {}	//Variavel utilizada pela Funcao PMSDLGRQ - Gerenc. Projetos
PRIVATE aHdrAFN		:= {}	//Variavel utilizada pela Funcao PMSDLGRQ - Gerenc. Projetos (Cabecalho da aRatAFN)
PRIVATE aMemoSDE    := {}
PRIVATE aOPBenef    := {}
PRIVATE aHeadDHP    := {}
PRIVATE aColsDHP    := {}
PRIVATE aHeadDHR    := {}
PRIVATE aColsDHR    := {}
PRIVATE aHdSusDHR   := {}
PRIVATE aCoSusDHR   := {}
PRIVATE xUserData	:= NIL
PRIVATE oTpFrete
PRIVATE oModelDCL	:= Nil
PRIVATE aSDGGrava	:= {}
PRIVATE bRefresh	:= {|nX| NfeFldChg(nX,nY,,aFldCBAtu)}
PRIVATE bGDRefresh	:= {|| IIf(oGetDados<>Nil,(oGetDados:oBrowse:Refresh()),.F.) }		// Efetua o Refresh da GetDados
PRIVATE oGetDados
PRIVATE oFolder
PRIVATE oFoco103
PRIVATE l240		:=.F.
PRIVATE l241		:=.F.
PRIVATE aBaseDup
PRIVATE aBackColsSDE:={}
PRIVATE l103TolRec  := .F.
PRIVATE l103Class   := .F.
PRIVATE lMudouNum   := .F.
PRIVATE lNfMedic    := .F.
PRIVATE aColsD1		:=	aCols
PRIVATE aHeadD1		:=	aHeader
PRIVATE cCodDiario  := ""
PRIVATE cUfOrig		:= ""
PRIVATE bIRRefresh	:= {|nX| NfeFldChg(nX,oFolder:nOption,oFolder,aFldCBAtu)}
PRIVATE lContDCL   := .T.
Private cAliasTPZ	:= IIf( lExiTmpTb, GetNextAlias(),  oTempTable:GetAlias() ) // Utilizado na funÁ„o NGGARANSD1 que est· no X3_VALID do campo D1_GARANTI
Private aNFMotBloq := {} //Motivo do bloqueio da NF, ser· gravado no CR_NFMOBLQ (Utilizado no MaAvalToler e MaAlcDoc)
Private oModelCSD 	:= nil
Private oMdlCSDGRV	:= nil
Private lGrvCSD 	:= .F.

//Vari·veis para tratamento para aba de Duplicatas
PRIVATE dEmisOld	:= ""
PRIVATE cCA100ForOld:= ""
PRIVATE cCondicaoOld:= ""
PRIVATE lMoedTit	:= (SuperGetMv("MV_MOEDTIT",.F.,"N") == "S")
PRIVATE lBlqTxNeg	:= .T.
PRIVATE dNewVenc	:= CTOD('  /  /  ')
PRIVATE aInfAdic	:= {}
Private oListDvIm
Private nDivCount := 0  
Private oDivCount
Private lDivImp		:= .F.
Private oFisTrbGen
Private	aAuxColSDE	:= aColsSDE
Private aAuxHdSDE	:= aHeadSDE
Private aAdianta	:= ProtCfgAdt()
Private bFilFIE    := Iif(aAdianta[1,4],{|| FIE_FILORI==cFilAnt},{||.T.})
Private lAdtCompart:= aAdianta[1,5] .And. 'C' $ aAdianta[1,1]+aAdianta[1,2]+aAdianta[1,3]
Private cFilFIE := Iif(aAdianta[1,5],cFilAnt,xFilial('FIE'))
Private nCombo		:= 2
Private lDKD		:= ChkFile("DKD") //Tabela Complementar SD1
Private lTabAuxD1	:= .F.
Private aHeadDKD	:= {}
Private aColsDKD	:= {}
Private aAltDKD		:= {}
Private oGetDKD		:= Nil

DEFAULT lEstNfClass	:= .F.

&("M->F1_CHVNFE") := ""

l103GAuto := If(Type("l103GAuto") == "U" ,.T.,l103GAuto)

//Tratamento para rotina automatica
If Type('l103Auto') == 'U'
	PRIVATE l103Auto	:= .F.
EndIf

If l103Auto .and. !Empty(axCodRet)
	aCodR     :=  axCodRet
Endif

If oRatIRF <> Nil
	//alterando a filial que foi atribuida anteriormente no construtor
	aRatIRF := ClassMethArr(oRatIRF,.T.)

	//Verifica se metodo existe
	If aScan(aRatIRF,{|x| AllTrim(Upper(x[1])) == "SETFILIAL"}) > 0
  		oRatIRF:SetFilial()
	Endif	
EndIf

//-- Inserida verificaÁ„o para ver o aRotina, pois quando a funÁ„o È chamada de outra Rotina n„o esta Ok.
//-- Esta validaÁ„o n„o deve ser retirada, pois e usada quando a chamada vem de outra rotina
If lCTBC661	.AND. ValType(aRotAux) == "A"
	aRotBkp := aRotina

	If aRotina <> aRotAux
		aRotina := {}
	 	aRotina := aRotAux
	EndIf
EndIf

if ValType(aRotina[nOpcx][1]) <> "U"
	If STR0006 $ aRotina[nOpcx][1]	// "Excluir"
		dbSelectArea("SD1")
		dbSetOrder(1)
		dbSeek(xFilial("SD1") + SF1->F1_DOC + SF1->F1_SERIE + SF1->F1_FORNECE + SF1->F1_LOJA )
	EndIf
EndIf

dDtdigit 	:= IIf(!Empty(SF1->F1_DTDIGIT),SF1->F1_DTDIGIT,SF1->F1_EMISSAO)

If ( Type("aAutoAFN") == "U" )
	PRIVATE aAutoAFN := {}
EndIf

If ( Type("aRateioCC") == "U" )
	PRIVATE aRateioCC := {}
EndIf

If ( Type("aAutoImp") == "U" )
	PRIVATE aAutoImp := {}
EndIf

If ( Type("aNFEDanfe") == "U" )
	PRIVATE aNFEDanfe := {}
EndIf

If ( Type("aDanfeComp") == "U" )
	Private aDanfeComp:= {}
Else
	aDanfeComp:= {}
EndIf

If ( Type("cCodRSef") == "U" )
	PRIVATE cCodRSef := ""
EndIf

If ( Type("aAposEsp") == "U" )
	PRIVATE aAposEsp := {}
EndIf

If ( Type("aNatRend") == "U" )
	PRIVATE aNatRend := {}
EndIf

If ( Type("aCompFutur") == "U" )
	PRIVATE aCompFutur := {}
EndIf

If ( Type("aAutoPFS") == "U" )
	PRIVATE aAutoPFS := {}
EndIf

If nOpcX == 6
	 lFina686 := 	IsInCallStack("FINA686")
	 lMata103 := 	IsInCallStack("MATA103") //Documento de Entrada
	 lMata102N := 	IsInCallStack("MATA102N") // Remito de Entrada
	 lMata101N := 	IsInCallStack("MATA101N") // Factura de Entrada

	//Nota gerada pela conferencia de servicos do SIGAFIN
	If SF1->F1_ORIGLAN == 'CS' .and. !lFina686
		lRet := .F.
		Help(" ",1,'NOPERMISS',,STR0409+CRLF+;	//'Este documento foi gerado pela conferÍncia de serviÁos do mÛdulo Financeiro.'
							    STR0410,1,0)	//'Portanto, o cancelamento deste documento, somente ser· possÌvel atravÈs da rotina que o originou.'
	Else
		//Verifica se o usuario tem permissao de delecao. ≥
		aArea2 := GetArea()
		SD1->(dbSeek(xFilial("SD1") + SF1->F1_DOC + SF1->F1_SERIE))
		While !SD1->(Eof()) .And. lRet .And. SD1->D1_DOC == SF1->F1_DOC .And. SD1->D1_SERIE ==  SF1->F1_SERIE
			If lMata103 //Documento de Entrada
				lRet := MaAvalPerm(1,{SD1->D1_COD,"MTA103",5})
			ElseIf lMata102N // Remito de Entrada
				lRet := MaAvalPerm(1,{SD1->D1_COD,"MT102N",5})
			ElseIf lMata101N // Factura de Entrada
				lRet := MaAvalPerm(1,{SD1->D1_COD,"MT101N",5})
			EndIf
			SD1->(dbSkip())
		End
		RestArea(aArea2)
		If !lRet
			Help(,,1,'SEMPERM')
		EndIf
	Endif

	If Alltrim(SF1->F1_ORIGEM) == "MSGEAI" .And. !l103Auto
		MsgAlert(STR0417) //"NF gerada por outro sistema, somente podera ser excluida pelo sistema que a originou"
		lRet := .F.
		Return lRet
	Endif
EndIf

If lRet
	//Exec.Block p/Executar Ponto de Entrada de Multiplas Naturezas - MT103MNT
	bBlockSev1	:= {|nX| A103MNat(@aHeadSev, @aColsSev)}
	bBlockSev2  := {|nX| NfeTOkSEV(@aHeadSev, @aColsSev,.F.)}

	If lNgMnTes .or. lNgMntCm
		
		If lExiTmpTb
			// Arquivo temporario utilizado na integracao com SIGAMNT
			AADD( aCAMPTPZ, { "TPZ_ITEM"   , "C", 04, 0 } ) // Numero do item
			AADD( aCAMPTPZ, { "TPZ_CODIGO" , "C", 15, 0 } ) // Codigo do produto
			AADD( aCAMPTPZ, { "TPZ_LOCGAR" , "C", 06, 0 } ) // Localizacao
			AADD( aCAMPTPZ, { "TPZ_ORDEM"  , "C", 06, 0 } ) // Ordem de servico
			AADD( aCAMPTPZ, { "TPZ_QTDGAR" , "N", 09, 0 } ) // Quantidade de garantia
			AADD( aCAMPTPZ, { "TPZ_UNIGAR" , "C", 01, 0 } ) // Unidade de garantia
			AADD( aCAMPTPZ, { "TPZ_CONGAR" , "C", 01, 0 } ) // Tipo do contador da garantia
			AADD( aCAMPTPZ, { "TPZ_QTDCON" , "N", 09, 0 } ) // Quantidade do contador da garantia

			oTempTable:= FWTemporaryTable():New( cAliasTPZ )
			oTempTable:SetFields( aCAMPTPZ ) 
			oTempTable:AddIndex("indice1", {"TPZ_ITEM"} ) 
			oTempTable:Create() 
		Else
			TCSQLEXEC( 'truncate table ' + oTempTable:GetRealName())
		Endif

	EndIf

	cDelSDE := If(lEstNfClass,GetNewPar("MV_DELRATC","1"),"1")

	lDivImp := !l103Inclui .And. ( lTColab := COLConVinc(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA) > 0 ) .And. SuperGetMV("MV_NFDVIMP",.F.,.F.)

	//Preenche automaticamente o fornecedor/loja ISS atraves do par‚metro
	//MV_AUTOISS = {Fornecedor,Loja,Dirf,CodRet}
	//Apenas efetua o processamento se todas as posicoes do parametro estiverem preenchidas
	If aAUTOISS <> NIL .And. Len(aAUTOISS) == 4	//Sempre vai entrar, o default eh todas as posicoes do array vazio, porem quando for
		//	vazio temos de manter a qtd de caracteres definidas na declaracao LOCAL das variaveis cFornIss,
		//	cLojaIss, cDirf e cCodRet, senao nao eh permitido a digitacao no rodape da NF devido ao tamanho
		//	ser ZERO (declaracao LOCAL do aAUTOISS).
		cFornIss := Iif (Empty (aAUTOISS[01]), cFornIss, PadR(aAUTOISS[01], nTamX3A2CD))
		cLojaIss := Iif (Empty (aAUTOISS[02]), cLojaIss, PadR(aAUTOISS[02], nTamX3A2LJ))
		cDirf	 := Iif	(Empty (aAUTOISS[03]), cDirf, aAUTOISS[03])
		cCodRet	 := Iif (Empty (aAUTOISS[04]), cCodRet, aAUTOISS[04])

		If !Empty( cCodRet )
			If aScan( aCodR, {|aX| aX[4]=="IRR"})==0
				aAdd( aCodR, {99, cCodRet, 1, "IRR"} )
			Else 
				aCodR[aScan( aCodR, {|aX| aX[4]=="IRR"})][2]	:=	cCodRet
			EndIf
		EndIf

		// Somente ira preencher se o cadastro no SA2 existir
		If !Empty(cFornIss) .And. !Empty(cLojaIss) .And. SA2->(MsSeek(xFilial("SA2")+cFornIss+cLojaIss))
			cFornIss := SA2->A2_COD
			cLojaIss := SA2->A2_LOJA
		Else
			cFornIss := Space(nTamX3A2CD)
			cLojaIss := Space(nTamX3A2LJ)
		Endif
	Endif

	//Verifica se o tratamento eh pela baixa e disabilita a alteracao do tipo de retencao                                      ≥
	If lPccBaixa
		cModRetPis	:= "3"
	Endif

	aBackSDE	:= If(Type('aBackSDE')=='U',{},aBackSDE)
	aAdd(aButtons, {'PEDIDO',{||Iif(Eval(bCabOk),A103ForF4( NIL, NIL, lNfMedic, lConsMedic, aHeadSDE, @aColsSDE,aHeadSEV, aColsSEV, @lTxNeg, @nTaxaMoeda),Help('   ',1,'A103CAB')),aBackColsSDE:=ACLONE(aColsSDE)},OemToAnsi(STR0024+" - <F5> "),STR0061} ) //"Selecionar Pedido de Compra"
	aAdd(aButtons, {'pedido',{||Iif(Eval(bCabOk),A103ItemPC( NIL,NIL,NIL,lNfMedic,lConsMedic,aHeadSDE,@aColsSDE, ,@lTxNeg, @nTaxaMoeda),Help('   ',1,'A103CAB')),aBackColsSDE:=ACLONE(aColsSDE)},OemToAnsi(STR0025+" - <F6> "),STR0148} ) //"Selecionar Pedido de Compra ( por item )"

	If __lIntPFS .And. FindFunction("JURA281")
		AAdd(aButtons  , {'bmpincluir', {||JURA281(.F., nOpcX)}, "", STR0533})  // "Desdobramento"
		AAdd(aButVisual, {'bmpincluir', {||JURA281(.F., MODEL_OPERATION_VIEW)}, "", STR0533})  // "Desdobramento"
	EndIf
		
	If !lGspInUseM
		aAdd(aButtons, {'RECALC',{||A103NFORI()},OemToAnsi(STR0026+" - <F7> "),STR0062} ) //"Selecionar Documento Original ( Devolucao/Beneficiamento/Complemento )"
		If SuperGetMV("MV_PRNFBEN",.F.,.F.)
			SF5->(dbSetOrder(1))
			If SF5->(dbSeek(xFilial("SF5")+SuperGetMv("MV_TMPAD")))
				aAdd(aButtons, {'RECALC',{||Iif(Eval(bCabOk),ARetBenef(),Help('   ',1,'A103CAB'))},STR0396,STR0397} ) //"Retorno de Beneficiamento#Retorno Ben."
			EndIf
		EndIf
		aAdd(aButtons, {'bmpincluir',{||A103LoteF4()},OemToAnsi(STR0027+" - <F8> "),STR0149} ) //"Selecionar Lotes Disponiveis"
		If ! lPyme
			aAdd(aButVisual,{"budget",{|| a120Posic(cAlias,nReg,nOpcX,"NF")},OemToAnsi(STR0254),OemToAnsi(STR0303)}) //"Consulta Aprovacao"
		EndIf
		If ( aRotina[ nOpcX, 4 ] == 2 .Or. aRotina[ nOpcX, 4 ] == 6 ) .And. !AtIsRotina("A103TRACK")
			AAdd(aButtons  ,{ "bmpord1", {|| A103Track() }, OemToAnsi(STR0150), OemToAnsi(STR0150) } )  // "System Tracker"
			AAdd(aButVisual,{ "bmpord1", {|| A103Track() }, OemToAnsi(STR0150), OemToAnsi(STR0150) } )  // "System Tracker"
		EndIf

		If aRotina[ nOpcX, 4 ] == 2
			AAdd(aButVisual,{ "clips", {|| A103Conhec() }, STR0188, STR0189 } ) // "Banco de Conhecimento", "Conhecim."
		EndIf
	EndIf

	//Permite pesquisar docs de saida de devolucao para vincular
	//com compra - Projeto Oleo e Gas
	If GetNewPar("MV_NFVCORI","2") == "1"
		aAdd(aButtons, {"NOTE",{||NfeVincOri()},OemToAnsi(STR0295),STR0295} )//"Pesquisa Doc Saida - VÌnculo"
	EndIf

	lWhenGet   := IIf(ValType(lWhenGet) <> "L" , .F. , lWhenGet)

	lVldAfter  := lWhenGet
	lMt100Tok  := !lWhenGet
	
	// Demonstrar o help na tela em tempo de execuÁ„o quando for ExecAuto
	If lWhenGet
		lMSHelpAuto  := .F.
	EndIf

	lConsMedic := A103GCDisp()

	//Define a funcao utilizada ( Incl.,Alt.,Visual.,Exclu.)
	Do Case
	Case aRotina[nOpcx][4] == 2
		l103Visual := .T.
		INCLUI := IIf(Type("INCLUI")=="U",.F.,INCLUI)
		ALTERA := IIf(Type("ALTERA")=="U",.F.,ALTERA)
	Case aRotina[nOpcx][4] == 3
		l103Inclui	:= .T.
		INCLUI := IIf(Type("INCLUI")=="U",.F.,INCLUI)
		ALTERA := IIf(Type("ALTERA")=="U",.F.,ALTERA)
	Case aRotina[nOpcx][4] == 4
		l103Class	:= .T.
		l103TolRec  := .T.
		INCLUI := IIf(Type("INCLUI")=="U",.F.,INCLUI)
		ALTERA := IIf(Type("ALTERA")=="U",.F.,ALTERA)
	Case aRotina[nOpcx][4] == 5 .Or. aRotina[nOpcx][4] == 20 .or. aRotina[nOpcx][4] == 21
		l103Exclui	:= .T.
		l103Visual	:= .T.
		INCLUI := IIf(Type("INCLUI")=="U",.F.,INCLUI)
		ALTERA := IIf(Type("ALTERA")=="U",.F.,ALTERA)

		//Indica a chamada de exclusao via SIGAEIC
		If aRotina[ nOpcx, 4 ] == 20
			lExcViaEIC := .T.
			//Encontra o nOpcx referente ao tipo 5 - Exclusao padrao
			If !Empty( nScan := AScan( aRotina, { |x| x[4] == 5 } ) )
				nOpcx := nScan
			EndIf
		EndIf

		//Indica a chamada de exclusao via SIGATMS
		If aRotina[ nOpcx, 4 ] == 21
			lExcViaTMS := .T.
			//Encontra o nOpcx referente ao tipo 5 - Exclusao padrao
			If !Empty( nScan := AScan( aRotina, { |x| x[4] == 5 } ) )
				nOpcx := nScan
			EndIf
		EndIf

	OtherWise
		l103Visual := .T.
		INCLUI := IIf(Type("INCLUI")=="U",.F.,INCLUI)
		ALTERA := IIf(Type("ALTERA")=="U",.F.,ALTERA)
	EndCase

	//Implementado o tratamento  para trazer o codigo de Retencao gravado na tabela
	//SE2 qdo ultilizada o parametro MV_VISDIRF=1
	If SuperGetMv("MV_VISDIRF",.F.,"1") == "1" .And. l103Visual
		dbSelectArea("SE2")
		SE2->(dbSetOrder(6))
		SE2->(dbSeek(xFilial("SE2")+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_PREFIXO+SF1->F1_DOC))
		If !Empty(SE2->E2_DIRF) .And. !Empty(SE2->E2_CODRET)
			cDirf   := SE2->E2_DIRF
			cCodRet := SE2->E2_CODRET

			If !Empty( cCodRet )
				If aScan( aCodR, {|aX| aX[4]=="IRR"})==0
					aAdd( aCodR, {99, cCodRet, 1, "IRR"} )
				Else
					aCodR[aScan( aCodR, {|aX| aX[4]=="IRR"})][2]	:=	cCodRet
				EndIf
			EndIf
		EndIf
	EndIf

	nRecSF1	 := IIF(INCLUI,0,SF1->(RecNo()))

	If l103Class
		//Verifica data da emissao de acordo com a data base
		If dDataBase < SF1->F1_EMISSAO
			lContinua := .F.
			Aviso(OemToAnsi(STR0119),OemToAnsi(STR0292),{"Ok"})//"N„o È possÌvel classificar notas emitidas posteriormente a data corrente do sistema."
		EndIf

		If lContinua
			If !Empty( nScanBsPis := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_BASEPS2"} ) ) .And. ;
					!Empty( nScanVlPis := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_VALPS2"} ) ) .And. ;
					!Empty( nScanAlPis := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_ALIQPS2"} ) )
				cCpBasePIS  := aRelImp[nScanBsPis,2]
				cCpValPIS   := aRelImp[nScanVlPis,2]
				cCpAlqPIS   := aRelImp[nScanAlPis,2]
			EndIf

			If !Empty( nScanBsCof := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_BASECF2"} ) ) .And. ;
					!Empty( nScanVlCof := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_VALCF2"} ) ) .And. ;
					!Empty( nScanAlCof := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_ALIQCF2"} ) )
				cCpBaseCOF  := aRelImp[nScanBsCOF,2]
				cCpValCOF   := aRelImp[nScanVlCOF,2]
				cCpAlqCOF   := aRelImp[nScanAlCOF,2]
			EndIf
		EndIf
	EndIf

	// Verifica se existe bloqueio contabil - Validacao incluida em 03/08/2015 changeset 320011 release 12
	If lContinua .And. ( l103Inclui .Or. l103Exclui .Or. l103Class )
		If l103Exclui .Or. ( l103Class .And. SF1->F1_STATUS <> "C" .AND. lCtbDtBl	)
			dCtbValiDt := SF1->F1_DTDIGIT
		Else
			dCtbValiDt := dDataBase
		EndIf
		lContinua := CtbValiDt(Nil ,dCtbValiDt ,.T. ,Nil ,Nil ,{"COM001"}) // Retorno .F. -> Help CTBBLOQ - Calendario Contabil Bloqueado. Verifique o processo.
	EndIf

	//Define as Hot-keys da rotina
	  If !l103Auto .And. (l103Inclui .Or. l103Class .Or. lWhenGet)
		SetKey( VK_F4 , { || A103F4() } )
		SetKey( VK_F5 , { || A103ForF4( NIL, NIL, lNfMedic, lConsMedic, aHeadSDE, @aColsSDE, aHeadSEV, aColsSEV, @lTxNeg, @nTaxaMoeda ),aBackColsSDE:=ACLONE(aColsSDE) } )
		SetKey( VK_F6 , { || A103ItemPC( NIL,NIL,NIL,lNfMedic,lConsMedic,aHeadSDE,@aColsSDE,,@lTxNeg, @nTaxaMoeda),aBackColsSDE:=ACLONE(aColsSDE) } )
		SetKey( VK_F7 , { || A103NFORI() } )
		SetKey( VK_F8 , { || A103LoteF4() } )
		SetKey( VK_F9 , { |lValidX3| NfeRatCC(aHeadSDE,aColsSDE,l103Inclui.Or.l103Class,lValidX3),aBackColsSDE:=ACLONE(aColsSDE)})
		bKeyF12 := SetKey( VK_F12 , Nil )
		//Integracao com o modulo de Projetos
		If lIntePms		// Integracao PMS
			SetKey( VK_F10, { || Eval(bPmsDlgNF)} )
		EndIf
		//Integracao com o modulo de Transportes
		If lIntTms	// Integracao TMS
			SetKey( VK_F11, { || oGetDados:oBrowse:lDisablePaint:=.T.,A103RatVei(),oGetDados:oBrowse:lDisablePaint:=.F.} )
		EndIf
	ElseIf !l103Auto .Or. lWhenGet
		SetKey( VK_F4 , { || A103F4() } )
		SetKey( VK_F5 , { || A103ForF4( NIL, NIL, lNfMedic, lConsMedic, aHeadSDE, @aColsSDE, aHeadSEV, aColsSEV, @lTxNeg, @nTaxaMoeda ),aBackColsSDE:=ACLONE(aColsSDE) } )
		SetKey( VK_F6 , { || A103ItemPC( NIL,NIL,NIL,lNfMedic,lConsMedic,aHeadSDE,@aColsSDE,,@lTxNeg, @nTaxaMoeda),aBackColsSDE:=ACLONE(aColsSDE) } )
		SetKey( VK_F7 , { || A103NFORI() } )
		bKeyF12 := SetKey( VK_F12 , Nil )
		If nOPCX<>6
			SetKey( VK_F9 , { |lValidX3| oGetDados:oBrowse:lDisablePaint:=.T.,NfeRATCC(aHeadSDE,aColsSDE,l103Inclui.Or.l103Class,lValidX3),oGetDados:oBrowse:lDisablePaint:=.F.,aBackColsSDE:=ACLONE(aColsSDE) } )
		EndIf
	EndIf
	
	//Integracao com o modulo de Projetos
	If lIntePms		// Integracao PMS
		aadd(aButtons	, {'PROJETPMS',{||Eval(bPmsDlgNF)},OemToAnsi(STR0029+" - <F10> "),OemToAnsi(STR0151)}) //"Projetos"
		aadd(aButVisual	, {'PROJETPMS',{||Eval(bPmsDlgNF)},OemToAnsi(STR0029+" - <F10> "),OemToAnsi(STR0151)}) //"Projetos"
	EndIf

	//SEFAZ- AM - Consolidador XML
	If lCsdXML
		aAdd(aButVisual, {"CSDXML",{||oGetDados:oBrowse:lDisablePaint:=.T.,A103CSDXML(4),oGetDados:oBrowse:lDisablePaint:=.F.},"Visu. Consolid. XML","Visu. Consolid. XML"} )
	Endif

	//Integracao com o modulo de Transportes
	If lIntTms		// Integracao TMS
		Aadd(aButtons	, {'CARGA'		,{||oGetDados:oBrowse:lDisablePaint:=.T.,A103RATVEI(),oGetDados:oBrowse:lDisablePaint:=.F. },STR0030+" - <F11>" , STR0152}) //"Rateio por Veiculo/Viagem"
		Aadd(aButVisual	, {'CARGA'		,{||oGetDados:oBrowse:lDisablePaint:=.T.,A103RATVEI(),oGetDados:oBrowse:lDisablePaint:=.F. },STR0030+" - <F11>", STR0152 }) //"Rateio por Veiculo/Viagem"
		Aadd(aButtons	, {'CARGASEQ'	,{||oGetDados:oBrowse:lDisablePaint:=.T.,A103FROTA(),oGetDados:oBrowse:lDisablePaint:=.F. },STR0031,STR0153}) //"Rateio por Frota"
		Aadd(aButVisual	, {'CARGASEQ'	,{||oGetDados:oBrowse:lDisablePaint:=.T.,A103FROTA(),oGetDados:oBrowse:lDisablePaint:=.F. },STR0031,STR0153}) //"Rateio por Frota"
	EndIf
	If !lGSPInUseM
		Aadd(aButtons	, {'S4WB013N' ,{||oGetDados:oBrowse:lDisablePaint:=.T.,NfeRatCC(aHeadSDE,aColsSDE,l103Inclui.Or.l103Class),oGetDados:oBrowse:lDisablePaint:=.F.,aBackColsSDE:=ACLONE(aColsSDE) },OemToAnsi(STR0032+" - <F9> "),STR0154} ) //"Rateio do item por Centro de Custo"
		Aadd(aButVisual	, {'S4WB013N' ,{||oGetDados:oBrowse:lDisablePaint:=.T.,NfeRatCC(aHeadSDE,aColsSDE,l103Inclui.Or.l103Class),oGetDados:oBrowse:lDisablePaint:=.F.,aBackColsSDE:=ACLONE(aColsSDE) },OemToAnsi(STR0032+" - <F9> "),STR0154} ) //"Rateio do item por Centro de Custo"
		aadd(aButVisual	, {"S4WB005N" ,{|| NfeViewPrd() },STR0142,STR0034}) //"Historico de Compras"
	EndIf

	//Itens Complemento DCL
	If lDclNew
		AAdd(aButtons, { "DCLEA013", {|| DCLEA013View(aCols,aHeader,,lConsMedic,aHeadSDE,aColsSDE,aHeadSEV,aColsSEV,lTxNeg,nTaxaMoeda,l103Inclui) }, "Complemento DCL","Complemento DCL" } )  //"Seleciona Multas", "Multas"
		AAdd(aButVisual, { "DCLEA013", {|| DCLEA013View(aCols,aHeader,.T.,lConsMedic,aHeadSDE,aColsSDE,aHeadSEV,aColsSEV,lTxNeg,nTaxaMoeda,l103Inclui) }, "Complemento DCL","Complemento DCL" } )  //"Seleciona Multas", "Multas"
	EndIf

	//Botao para exportar dados para EXCEL
	If RemoteType() == 1
		aAdd(aButtons   , {PmsBExcel()[1],{|| DlgToExcel({ {"CABECALHO",OemToAnsi(STR0009),{RetTitle("F1_TIPO"),RetTitle("F1_FORMUL"),RetTitle("F1_DOC"),RetTitle("F1_SERIE"),RetTitle("F1_EMISSAO"),RetTitle("F1_FORNECE"),RetTitle("F1_LOJA"),RetTitle("F1_ESPECIE"),RetTitle("F1_EST")},{cTipo,cFormul,cNFiscal,Substr(cSerie,1,3),dDEmissao,cA100For,cLoja,cEspecie,cUfOrig}},{"GETDADOS",OemToAnsi(STR0190),aHeader,aCols},{"GETDADOS",OemToAnsi(STR0013),aHeadSE2,aColsSE2}})},PmsBExcel()[2],PmsBExcel()[3]})
		aAdd(aButVisual , {PmsBExcel()[1],{|| DlgToExcel({ {"CABECALHO",OemToAnsi(STR0009),{RetTitle("F1_TIPO"),RetTitle("F1_FORMUL"),RetTitle("F1_DOC"),RetTitle("F1_SERIE"),RetTitle("F1_EMISSAO"),RetTitle("F1_FORNECE"),RetTitle("F1_LOJA"),RetTitle("F1_ESPECIE"),RetTitle("F1_EST")},{cTipo,cFormul,cNFiscal,Substr(cSerie,1,3),dDEmissao,cA100For,cLoja,cEspecie,cUfOrig}},{"GETDADOS",OemToAnsi(STR0190),aHeader,aCols},{"GETDADOS",OemToAnsi(STR0013),aHeadSE2,aColsSE2}})},PmsBExcel()[2],PmsBExcel()[3]})
	EndIf

	//Selecao de multas - SIGAGCT
	If lConsMedic
		AAdd(aButtons, { "checked", {|| A103Multas(dDEmissao,cA100For,cLoja,aMultas) }, STR0249, STR0250 } )  //"Seleciona Multas", "Multas"
	EndIf

	//Aposentadoria Especial - Projeto REINF
	If ChkFile("DHP")
		Aadd(aButtons	, {'APOSESP' ,{||oGetDados:oBrowse:lDisablePaint:=.T.,A103Aposen(aHeadDHP,aColsDHP,l103Inclui,l103Class),oGetDados:oBrowse:lDisablePaint:=.F.},"Aposentadoria Especial","Apos.Especial"} ) //"Aposentadoria Especial"
		Aadd(aButVisual	, {'APOSESP' ,{||oGetDados:oBrowse:lDisablePaint:=.T.,A103Aposen(aHeadDHP,aColsDHP,l103Inclui,l103Class),oGetDados:oBrowse:lDisablePaint:=.F.},"Aposentadoria Especial","Apos.Especial"} ) //"Aposentadoria Especial"
	EndIf
	
	//Natureza de Rendimentos
	If ChkFile("DHR")
		aAdd(aButtons, {"NOTE",{||oGetDados:oBrowse:lDisablePaint:=.T.,A103NATREN(aHeadDHR,aColsDHR,l103Inclui,l103Class),oGetDados:oBrowse:lDisablePaint:=.F.},"Nat. Rendimento","Nat. Rendimento"} )
		aAdd(aButVisual, {"NOTE",{||oGetDados:oBrowse:lDisablePaint:=.T.,A103NATREN(aHeadDHR,aColsDHR,l103Inclui,l103Class),oGetDados:oBrowse:lDisablePaint:=.F.},"Nat. Rendimento","Nat. Rendimento"} )
	Endif

	//Tratamento p/ Nota Fiscal geradas no SIGAEIC
	If !l103Inclui .And. (SF1->F1_IMPORT == "S" .OR. AllTrim(SF1->F1_ORIGEM) == "SIGAEIC" .Or. !Empty( ( cAliasSD1 )->D1_TIPO_NF ) ) .And. lEstNfClass
		lExcViaEIC := .T.
	EndIf

	If !l103Inclui .And. (SF1->F1_IMPORT == "S" .OR. AllTrim(SF1->F1_ORIGEM) == "SIGAEIC")
		If !lExcViaEIC .And. l103Exclui
			Help( "", 1, "A103EXCIMP" )  // "Este documento nao pode ser excluido pois foi criado pelo SIGAEIC. A exclusao devera ser efetuada pelo SIGAEIC."
            lContinua := .F.			
		ElseIf AllTrim(SF1->F1_ORIGEM) != "SIGAEIC"
			A103NFEIC(cAlias,nReg,nOpcx)
			lContinua := .F.
		EndIf		
	EndIf

	//Validacao incluida pela controladoria para  valicaÁ„o da Nota fical de transferencia Rotina ATFA060
	If Alltrim(SF1->F1_ORIGEM) == "ATFA060" .And. !FwIsInCallStack("ATFA060") .And. l103Exclui
		Help(" ",1,'A103NFiscal',,STR0432,1,0)
		lRet := .F.
		Return lRet
	Endif
	//Verifica se o Produto È do tipo armamento.
	If l103Exclui .And. SuperGetMV("MV_GSXNFE",,.F.)

	 		aArea2 	:= GetArea()
	 		aAreaSD1	:= SD1->(GetArea())

	 		If SD1->(dbSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA))

		 		DbSelectArea('SB5')
				SB5->(DbSetOrder(1)) // acordo com o arquivo SIX -> A1_FILIAL+A1_COD+A1_LOJA

				If SB5->(DbSeek(xFilial('SB5')+SD1->D1_COD)) // Filial: 01, CÛdigo: 000001, Loja: 02
					If SB5->B5_TPISERV=='2'
	  					lRetorno := aT720Mov(SD1->D1_DOC,SD1->D1_SERIE)
	  					If !lRetorno
	  						lContinua := lRetorno
	  						Help( "", 1, "At720Mov" )
	  					EndIf
					ElseIf SB5->B5_TPISERV=='1'
	  					lRetorno := aT710Mov(SD1->D1_DOC,SD1->D1_SERIE)
	  					If !lRetorno
	  						lContinua := lRetorno
	  						Help( "", 1, "At710Mov" )
	  					EndIf
	  				ElseIf SB5->B5_TPISERV=='3'
	  					lRetorno := aT730Mov(SD1->D1_DOC,SD1->D1_SERIE)
	  					If !lRetorno
	  						lContinua := lRetorno
	  						Help( "", 1, "At730Mov" )
	  					EndIf
					EndIf

				EndIf

			EndIf

			RestArea(aAreaSD1)
			RestArea(aArea2)
	EndIf

	// Valida de permite excluir NF de compra futura, com saldo consumido
	If l103Exclui .And. lDHQInDic .And. lMt103Com .And. !A103FutVld(.T., aCompFutur)
		lContinua := .F.
	EndIf

	// Inicializa variaveis aba Informacoes Adicionais
	If FindFunction("A103ChkInfAdic")
		A103ChkInfAdic(IIF(l103Inclui,1,2)) 
	EndIf

	//Notas Fiscais NAO Classificadas geradas pelo SIGAEIC NAO deverao ser visualizadas no MATA103
	If l103Visual .And. !Empty(SF1->F1_HAWB) .And. Empty(SF1->F1_STATUS) .and. !l103Exclui
		Aviso("A103NOVIEWEIC",STR0344,{"Ok"}) // "Este documento foi gerado pelo SIGAEIC e ainda N√O foi classificado, para visualizar utilizar a opÁ„o classificar ou no Modulo SIGAEIC opÁ„o DesembaraÁo/recebimento de importaÁ„o/Totais. Apos a classificaÁ„o o documento pode ser visualizado normalmente nesta opÁ„o."
		lContinua := .F.
	EndIf

	//Notas Fiscais excluÌdas, rastreamento cont·bil
	If lContinua .And. l103Visual .And. ( SD1->(Deleted()) .Or. SF1->(Deleted()) ) .And. IsInCallStack("CTBC010ROT")
		Aviso("A103NOVIEWDEL",STR0416,{"Ok"}) //"Este documento encontrasse excluÌdo e n„o È possÌvel visualiza-lo."
		lContinua := .F.
	EndIf

	//Inicializa as variaveis
	cTipo		:= IIf(l103Inclui,CriaVar("F1_TIPO",.F.),SF1->F1_TIPO)
	If cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_TPCOMPL")) > 0
		cTpCompl	:= IIF(l103Inclui,CriaVar("F1_TPCOMPL",.F.),SF1->F1_TPCOMPL)
	EndIf
	cFormul		:= IIf(l103Inclui,CriaVar("F1_FORMUL",.F.),SF1->F1_FORMUL)
	cNFiscal	:= IIf(l103Inclui,CriaVar("F1_DOC"),SF1->F1_DOC)
	cSerie		:= IIf(l103Inclui,SerieNfId("SF1",5,"F1_SERIE") , SerieNfId("SF1",2,"F1_SERIE") )
	If lSubSerie
		cSubSerie	:= IIf(l103Inclui,CriaVar("F1_SUBSERI"),SF1->F1_SUBSERI)
	EndIf
	dDEmissao	:= IIf(l103Inclui,CriaVar("F1_EMISSAO"),SF1->F1_EMISSAO)
	cA100For	:= IIf(l103Inclui,CriaVar("F1_FORNECE",.F.),SF1->F1_FORNECE)
	cLoja		:= IIf(l103Inclui,CriaVar("F1_LOJA",.F.),SF1->F1_LOJA)
	cEspecie	:= IIf(l103Inclui,CriaVar("F1_ESPECIE"),SF1->F1_ESPECIE)
	cCondicao	:= IIf(l103Inclui,CriaVar("F1_COND"),SF1->F1_COND)
	cUfOrig		:= IIf(l103Inclui,CriaVar("F1_EST"),SF1->F1_EST)
	cRecIss		:= IIf(l103Inclui,CriaVar("F1_RECISS"),SF1->F1_RECISS)
	cFornIss	:= Iif(l103Inclui,Iif(Empty(cFornIss),CriaVar("F1_FORNECE"),cFornIss),cFornIss)
	cLojaIss	:= Iif(l103Inclui,Iif(Empty(cLojaIss),CriaVar("F1_LOJA"),cLojaIss),cLojaIss)
	dVencISS	:= IIf(l103Inclui,CtoD(""),dVencISS)
	If lISSxMun .And. cPaisLoc == "BRA"
		aInfISS[1,1] := IIf(l103Inclui,CriaVar("F1_INCISS"),SF1->F1_INCISS)
		aInfISS[1,3] := IIf(l103Inclui,CriaVar("F1_ESTPRES"),SF1->F1_ESTPRES)
		aInfAdic[1]  := aInfISS[1,1]
		cDescMun     := Posicione("CC2",1,xFilial("CC2")+aInfISS[1,3]+aInfISS[1,1],"CC2_MUN")
	Else
		If cPaisLoc == "BRA"
			cInfISS := IIf(l103Inclui,CriaVar("F1_ESTPRES"),SF1->F1_ESTPRES)
		EndIf
		If Len(aInfAdic) > 0
			cDescMun    := Posicione("CC2",1,xFilial("CC2")+cInfISS+aInfAdic[1],"CC2_MUN")
		Endif
	EndIf
	
	//Trata codigo do diario
	If UsaSeqCor()
		cCodDiario := IIf(l103Inclui,CriaVar("F1_DIACTB"),SF1->F1_DIACTB)
	EndIf

	If (!cTipo$"DB" .And. !Empty(cA100For) .And. cA100For+cLoja <> SA2->A2_COD+SA2->A2_LOJA)
		SA2->(DbSetOrder(1))
		SA2->(MsSeek(xFilial("SA2")+cA100For+cLoja))
	EndIf

	If cPaisLoc == "BRA"
		If l103Inclui
			aNFEletr  := {CriaVar("F1_NFELETR"),CriaVar("F1_CODNFE"),CriaVar("F1_EMINFE"),CriaVar("F1_HORNFE"),CriaVar("F1_CREDNFE"),CriaVar("F1_NUMRPS"),;
				    	  CriaVar("F1_MENNOTA"),CriaVar("F1_MENPAD")}
			    A103CheckDanfe(2)
				If l103Auto
					If aScan(aAutoCab,{|x| AllTrim(x[1])=="F1_TPFRETE"})>0
						aNFEDanfe[14]:=aAutoCab[aScan(aAutoCab,{|x| AllTrim(x[1])=="F1_TPFRETE"})][2]
					EndIF

					IF aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_SERIE"}) == 0
						Help(" ",1,"CPOobrigat",,STR0574,1,0)//"obrigatÛrio informar o campo sÈrie para as notas com formul·rio prÛprio = 'S' "
						lContinua := .f.
					Endif	
				EndIf
		Else
			aNFEletr  := {SF1->F1_NFELETR,SF1->F1_CODNFE,SF1->F1_EMINFE,SF1->F1_HORNFE,SF1->F1_CREDNFE,SF1->F1_NUMRPS,;
				    	  SF1->F1_MENNOTA,SF1->F1_MENPAD}
				A103CargaDanfe(l103Class,aNFEletr,aInfAdic)
		Endif
	Endif

	If l103Class .And. Empty(cCondicao) .And. SF1->F1_STATUS <> 'C'
		DbSelectArea("SA2")
		DbSetOrder(1)
		If MsSeek(xFilial("SA2")+cA100For+cLoja)
			cCondicao  := SA2->A2_COND
		EndIf
		DbSelectArea("SF1")
	EndIf

	//Inicializa as variaveis do pergunte
	Pergunte("MTA103",.F.)
	//Carrega as variaveis com os parametros da execauto
	Ma103PerAut()

	lDigita     := (mv_par01==1)
	lAglutina   := (mv_par02==1)
	lReajuste   := (mv_par04==1)
	lAmarra     := (mv_par05==1)
	lGeraLanc   := (mv_par06==1)
	lConsLoja   := (mv_par07==1)
	IsTriangular(mv_par08==1)
	nTpRodape   := (mv_par09)
	lPrecoDes   := (mv_par10==1)
	lDataUcom   := (mv_par11==1)
	lAtuAmarra  := (mv_par12==1)
	lRatLiq     := (mv_par13==2)
	lRatImp     := (mv_par13==2 .And. mv_par14==2)
	lNfGarEst	:= if(valtype(mv_par28) == "N",mv_par28 == 1,.F.)
	
	If lContinua

		//Gera distribuicao de produtos (crossdoking)
		If (l103Inclui .Or. l103Class) .And. SF1->F1_TIPO == "N" .And. SF1->F1_STATUS != "C" .AND. lIntWMS
			WmsAvalSF1("6")
		EndIf

		//Ponto de entrada para adicao de campos memo do usuario
		If ExistBlock( "MT103MEM" )
			If Valtype(	aMemUser := ExecBlock( "MT103MEM", .F., .F. ) ) == "A"
				aEval( aMemUser, { |x| aAdd( aMemoSDE, x ) } )
			EndIf
		EndIf

		//Template acionando ponto de entrada
		If lTMt103NFE
			ExecTemplate("MT103NFE",.F.,.F.,nOpcx)
		EndIf

		//Ponto de entrada no inicio do Documento de Entrada
		If lMt103NFE
			Execblock("MT103NFE",.F.,.F.,nOpcx)
		EndIf
		If l103Inclui .Or. l103Class
			If l103Class
				//Ponto de Entrada na Classificacao da NF
				If ExistBlock("MT100CLA")
					ExecBlock("MT100CLA",.F.,.F.)
				EndIf
			EndIf
			
			//Validacoes para Inclusao/Classificacao de NF de Entrada
			If !NfeVldIni(l103Class,lGeraLanc,@lClaNfCfDv)
				lContinua := .F.
			EndIf
		ElseIf l103Exclui
			
			//As Validacoes para Exclusao de NF de Entrada serao aplicadas
			//somente quando a NFE nao esteja Bloqueada.
			If !SF1->F1_STATUS $ "BC"
				If !MaCanDelF1(nRecSF1,@aRecSC5,aRecSE2,Nil,Nil,Nil,Nil,aRecSE1,lExcViaEIC,lExcViaTMS,l103Exclui)
					lContinua := .F.
				EndIf
			EndIf
			
			//Integracao com o modulo de Armazenagem - SIGAWMS
			If lContinua .And. (lIntWMS .Or. lWmsCRD) .And. SF1->F1_TIPO $ "N|D|B" //-- ValidaÁ„o se pode excluir a nota fiscal pelo WMS
				lContinua := WmsAvalSF1(Iif(lEstNfClass,"2","4"),"SF1")
			EndIf
			
			// quando a nota for de devoluÁ„o, valida se j· houve uma nova movimentaÁao no equipamento
			If lContinua .And. SF1->F1_TIPO == 'D'.And. !At800ExcD1( nRecSF1 )
				lContinua := .F.
			EndIf

			//Integracao com desdobramento - SIGAPFS
			If lContinua .And. __lIntPFS .And. FindFunction("J281VldExc")
				lContinua := J281VldExc(aRecSE2)
			EndIf

		EndIf
	EndIf
	If lContinua
		If !l103Inclui .And. !l103Auto
			//Inicializa as veriaveis utilizadas na exibicao da NF
			If lISSxMun
				NfeCabOk(l103Visual,/*oTipo*/,/*oNota*/,/*oEmissao*/,/*oFornece*/,/*oLoja*/,/*lFiscal*/,cUfOrig,aInfISS[1,1],aInfISS[1,3])
			Else
				NfeCabOk(l103Visual,/*oTipo*/,/*oNota*/,/*oEmissao*/,/*oFornece*/,/*oLoja*/,/*lFiscal*/,cUfOrig)
			EndIf 
		Else
			If !l103Inclui
				MaFisIni(SF1->F1_FORNECE,SF1->F1_LOJA,IIf(cTipo$'DB',"C","F"),cTipo,Nil,MaFisRelImp("MT100",{"SF1","SD1"}),,!l103Visual,,,,,,,,,,,,,,,,,dDEmissao,,,,,,,,lTrbGen)
			EndIf
		EndIf

		//Montagem do aHeader
		If Type("aBackSD1")=="U" .Or. Empty(aBackSD1)
			aBackSD1 := {}
		EndIf

		//Trava os registros do SF1 - Alteracao e Exclusao
		If l103Class .Or. l103Exclui
			If !SoftLock("SF1")
				lContinua := .F.
			EndIf
		EndIf

		//Tratamento da exclus„o da nota fiscal de entrada - NF-e SEFAZ
		If l103Exclui
			If SF1->F1_FORMUL == "S" .And. "SPED"$cEspecie .And. (cAlias)->F1_FIMP$"TS" //verificacao apenas da especie como SPED e notas que foram transmitidas ou impressoo DANFE
				If cPaisLoc == "BRA"
					nHoras := SubtHoras(IIF(!Empty(SF1->F1_DAUTNFE),SF1->F1_DAUTNFE,dDtdigit),IIF(!Empty(SF1->F1_HAUTNFE),SF1->F1_HAUTNFE,SF1->F1_HORA), dDataBase, substr(Time(),1,2)+":"+substr(Time(),4,2) )
				EndIf
				If nHoras > nSpedExc .And. SF1->F1_STATUS<>"C"
					If l103Auto
						Help("  ",1,STR0455 + Alltrim(STR(nSpedExc)) +STR0456)
					Else
						MsgAlert(STR0455 + Alltrim(STR(nSpedExc)) +STR0456)
					EndIf
					lContinua := .F.
				ElseIf SF1->F1_STATUS=="C" .And. l103Exclui
					If l103Auto
						Help("  ",1,STR0328)
					Else
						Aviso(STR0327,STR0328,{"Ok"}) //N„o foi possivel excluir a nota, pois a mesma j· foi transmitida e encotra-se bloqueada. Ser· necess·rio realizar a primeiro a classificaÁ„o da nota e posteriormente a exclus„o!"
					EndIf
					lContinua := .F.
				Else
					lContinua := .T.
			    EndIf
			EndIf
		EndIf

		//Quando existir a NF no Modulo de Veiculos, a exclusao da
		//NF somente pode ser realizada no Modulo de Veiculos
		If lContinua .and. l103Exclui .and. lIntGC
			cAliasAnt := Alias()
			cAliasVVF := "SQLVVF"
			cQuery := "SELECT VVF.R_E_C_N_O_ FROM "+RetSqlName("VVF")+" VVF "
			cQuery += "WHERE VVF.VVF_FILIAL='"+xFilial("VVF")+"' AND "
			cQuery += "VVF.VVF_NUMNFI = '"+SF1->F1_DOC+"' AND VVF.VVF_SERNFI = '"+SF1->F1_SERIE+"' AND VVF.VVF_CODFOR = '"+SF1->F1_FORNECE+"' AND VVF.VVF_LOJA = '"+SF1->F1_LOJA+"' AND "
        	cQuery += "VVF.VVF_SITNFI = '1' AND VVF.D_E_L_E_T_=' '"
			cQuery := ChangeQuery(cQuery)

			dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasVVF,.T.,.T.)

			 If (cAliasVVF)->(!Eof()) .and. !(FM_PILHA("OFI") .or. FM_PILHA("VEI"))
				cMensagem:= STR0412+CHR(10)+CHR(13) // "Nao possivel excluir esse documento pois "
				cMensagem+= STR0413+CHR(10)+CHR(13) // "sua origem ocorreu no Modulo de Veiculos. "
				cMensagem+= STR0414+CHR(10)+CHR(13) // "Portanto seu Cancelamento so sera possivel no modulo de Veiculos."
				Help(" ",1,"NAOEXCNFS","NAOEXCNFS",cMensagem,1,0)
				lContinua := .F.
			Endif

			DbSelectArea(cAliasVVF)
			dbCloseArea()
			DbSelectArea(cAliasAnt)

		Endif
		// Valida exclusao de NF gerada pelo SIGAGFE
		If l103Exclui 
			If !IsInCallStack("GFEA065In") .And. Alltrim(SF1->F1_ORIGEM) $ "GFEA065"				 
				Help(" ",1,"GFEA065",,STR0408,1,0)//"Notas geradas pelo mÛdulo SIGAGFE n„o podem ser excluÌdas atravÈs dessa rotina."
				lContinua := .F.				
			EndIf
		EndIf
		//N„o permite excluir nota que tenha movimentacao de AVP
		If lContinua .And. l103Exclui
			dbSelectArea("SE2")
			SE2->(dbSetOrder(6))
			If SE2->(dbSeek(xFilial("SE2")+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_SERIE+SF1->F1_DOC))
				While SE2->(!EOF()) .And. (SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_SERIE+SF1->F1_DOC == SE2->E2_FORNECE+SE2->E2_LOJA+SE2->E2_PREFIXO+SE2->E2_NUM)
					If !FAVPValTit( "SE2",, SE2->E2_PREFIXO, SE2->E2_NUM, SE2->E2_PARCELA, SE2->E2_TIPO, SE2->E2_FORNECE, SE2->E2_LOJA, " " )
						lContinua := .F.
						Exit
					EndIF
					SE2->(dbSkip())
				Enddo
			EndIf
			SE2->(dbSetOrder(1))
		EndIf

		If lContinua
			If l103Class .Or. l103Visual .Or. l103Exclui
				aadd(aTitles,(STR0034)) //"Historico"
				aAdd(aFldCBAtu,Nil) 

				If Type("aNfeDanfe") == "A" .AND. Len(aNfeDanfe)>=23
					If !Empty(MafisScan("NF_MODAL",.F.)) .And. (Left(aNfeDanfe[23],2) $ "  |01|02|03|04|05|06")
						MaFisRef("NF_MODAL","MT100",Left(aNfeDanfe[23],2))
					EndIf
				EndIf

				If !l103Class .And. !Empty( MaFisScan("NF_RECISS",.F.) )
					MaFisAlt("NF_RECISS",SF1->F1_RECISS)
				EndIf
				cRecIss	:=	MaFisRet(,"NF_RECISS")
				
				//Carrega o Array contendo os Registros Fiscais.(SF3) 
				DbSelectArea("SF3")
				DbSetOrder(4)
				lQuery    := .T.
				cAliasSF3 := "A103NFISCAL"
				aStruSF3  := SF3->(dbStruct())

				cQuery    := "SELECT F3_FILIAL, F3_CLIEFOR, F3_LOJA, F3_NFISCAL, "
				cQuery    += " F3_SERIE, F3_CFO, F3_FORMUL ,SF3.R_E_C_N_O_ SF3RECNO "
				cQuery    += "  FROM "+RetSqlName("SF3")+" SF3 "
				cQuery    += " WHERE SF3.F3_FILIAL     = '"+xFilial("SF3")+"'"
				cQuery    += "   AND SF3.F3_CLIEFOR	   = '"+SF1->F1_FORNECE+"'"
				cQuery    += "   AND SF3.F3_LOJA	   = '"+SF1->F1_LOJA+"'"
				cQuery    += "   AND SF3.F3_NFISCAL	   = '"+SF1->F1_DOC+"'"
				cQuery    += "   AND SF3.F3_SERIE	   = '"+SF1->F1_SERIE+"'"
				cQuery    += "   AND SF3.F3_FORMUL	   = '"+SF1->F1_FORMUL+"'"
				cQuery    += "   AND SF3.D_E_L_E_T_	   = ' ' "
				cQuery    += " ORDER BY "+SqlOrder(SF3->(IndexKey()))

				cQuery := ChangeQuery(cQuery)

				dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSF3,.T.,.T.)
				If (cAliasSF3)->(!Eof())
					(cAliasSF3)->(DbGoTop())
					For nX := 1 To Len(aStruSF3)
						If aStruSF3[nX,2]<>"C"
							TcSetField(cAliasSF3,aStruSF3[nX,1],aStruSF3[nX,2],aStruSF3[nX,3],aStruSF3[nX,4])
						EndIf
					Next nX
					While !Eof() .And. lContinua .And.;
							xFilial("SF3") == (cAliasSF3)->F3_FILIAL .And.;
							SF1->F1_FORNECE == (cAliasSF3)->F3_CLIEFOR .And.;
							SF1->F1_LOJA == (cAliasSF3)->F3_LOJA .And.;
							SF1->F1_DOC == (cAliasSF3)->F3_NFISCAL .And.;
							SF1->F1_SERIE == (cAliasSF3)->F3_SERIE
						If Substr((cAliasSF3)->F3_CFO,1,1) < "5" .And. (cAliasSF3)->F3_FORMUL == SF1->F1_FORMUL
							aadd(aRecSF3,If(lQuery,(cAliasSF3)->SF3RECNO,SF3->(RecNo())))
						EndIf
						DbSelectArea(cAliasSF3)
						dbSkip()
					EndDo
				Endif
				If lQuery
					DbSelectArea(cAliasSF3)
					dbCloseArea()
					DbSelectArea("SF3")
				EndIf
				
				//Monta o Array contendo as registros do SDE
				DbSelectArea("SDE")
				DbSetOrder(1)
				lQuery    := .T.
				aStruSDE  := SDE->(dbStruct())
				cAliasSDE := "A103NFISCAL"
				cQuery    := "SELECT SDE.*,SDE.R_E_C_N_O_ SDERECNO "
				cQuery    += "  FROM "+RetSqlName("SDE")+" SDE "
				cQuery    += " WHERE SDE.DE_FILIAL	 ='"+xFilial("SDE")+"'"
				cQuery    += "   AND SDE.DE_DOC		 ='"+SF1->F1_DOC+"'"
				cQuery    += "   AND SDE.DE_SERIE	 ='"+SF1->F1_SERIE+"'"
				cQuery    += "   AND SDE.DE_FORNECE  ='"+SF1->F1_FORNECE+"'"
				cQuery    += "   AND SDE.DE_LOJA     ='"+SF1->F1_LOJA+"'"
				cQuery    += "   AND SDE.D_E_L_E_T_  =' ' "
				cQuery    += " ORDER BY "+SqlOrder(SDE->(IndexKey()))

				cQuery := ChangeQuery(cQuery)

				dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSDE,.T.,.T.)
				If (cAliasSDE)->(!Eof())
					(cAliasSDE)->(DbGoTop())
					For nX := 1 To Len(aStruSDE)
						If aStruSDE[nX,2]<>"C"
							TcSetField(cAliasSDE,aStruSDE[nX,1],aStruSDE[nX,2],aStruSDE[nX,3],aStruSDE[nX,4])
						EndIf
					Next nX
					While ( !Eof() .And. lContinua .And.;
							xFilial('SDE') == (cAliasSDE)->DE_FILIAL .And.;
							SF1->F1_DOC == (cAliasSDE)->DE_DOC .And.;
							SF1->F1_SERIE == (cAliasSDE)->DE_SERIE .And.;
							SF1->F1_FORNECE == (cAliasSDE)->DE_FORNECE .And.;
							SF1->F1_LOJA == (cAliasSDE)->DE_LOJA )
						If Empty(aBackSDE)
							//Montagem do aHeader
							DbSelectArea("SX3")
							DbSetOrder(1)
							MsSeek("SDE")
							While ( !EOF() .And. SX3->X3_ARQUIVO == "SDE" )
								If X3USO(SX3->X3_USADO) .AND. cNivel >= SX3->X3_NIVEL .And. !"DE_CUSTO"$SX3->X3_CAMPO
									aadd(aBackSDE,{ TRIM(X3Titulo()),;
										SX3->X3_CAMPO,;
										SX3->X3_PICTURE,;
										SX3->X3_TAMANHO,;
										SX3->X3_DECIMAL,;
										SX3->X3_VALID,;
										SX3->X3_USADO,;
										SX3->X3_TIPO,;
										SX3->X3_F3,;
										SX3->X3_CONTEXT })
								EndIf
								DbSelectArea("SX3")
								dbSkip()
							EndDo
						EndIf
						aHeadSDE  := aBackSDE
						
						//Adiciona os campos de Alias e Recno ao aHeader para WalkThru.
						ADHeadRec("SDE",aHeadSDE)

						aadd(aRecSDE,If(lQuery,(cAliasSDE)->SDERECNO,SDE->(RecNo())))
						If cItemSDE <> 	(cAliasSDE)->DE_ITEMNF
							cItemSDE	:= (cAliasSDE)->DE_ITEMNF
							aadd(aColsSDE,{cItemSDE,{}})
							nItemSDE++
						EndIf

						aadd(aColsSDE[nItemSDE][2],Array(Len(aHeadSDE)+1))
						For nY := 1 to Len(aHeadSDE)
							If IsHeadRec(aHeadSDE[nY][2])
								aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := IIf(lQuery , (cAliasSDE)->SDERECNO , SDE->(Recno())  )
							ElseIf IsHeadAlias(aHeadSDE[nY][2])
								aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := "SDE"
							ElseIf ( aHeadSDE[nY][10] <> "V")
								aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := (cAliasSDE)->(FieldGet(FieldPos(aHeadSDE[nY][2])))
							Else
								aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := (cAliasSDE)->(CriaVar(aHeadSDE[nY][2]))
							EndIf
							aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][Len(aHeadSDE)+1] := .F.
						Next nY

						DbSelectArea(cAliasSDE)
						dbSkip()
					EndDo
				Endif
				aBackColsSDE:=ACLONE(aColsSDE)
				If lQuery
					DbSelectArea(cAliasSDE)
					dbCloseArea()
					DbSelectArea("SDE")
				EndIf
				
				//Monta o Array contendo as duplicatas SE2
				If SF1->F1_TIPO$"DB"
					cE1Cliente := SF1->F1_FORNECE // Quando integrado com DMS, o cliente pode ser outro se utilizado condicao de pagamento TIPO A na venda.
					cE1Loja    := SF1->F1_LOJA    // Quando integrado com DMS, o cliente pode ser outro se utilizado condicao de pagamento TIPO A na venda.
					cE1NReduz  := "" 			  // Quando integrado com DMS, o cliente pode ser outro se utilizado condicao de pagamento TIPO A na venda.

					If lIntGC .and. ExistFunc("FMX_NCCCliente")
						FMX_NCCCliente(SF1->F1_DOC, SF1->F1_SERIE, SF1->F1_FORNECE, SF1->F1_LOJA, @cE1Cliente, @cE1Loja, @cE1NReduz)
					EndIf

					cPrefixo := PadR( cPrefixo, Len( SE1->E1_PREFIXO ) )
					DbSelectArea("SE1")
					DbSetOrder(2)
					MsSeek(xFilial("SE1")+cE1Cliente+cE1Loja+cPrefixo+SF1->F1_DOC)
					If Empty(aRecSe1)
						 While !Eof() .And. xFilial("SE1") == SE1->E1_FILIAL .And.;
								cE1Cliente == SE1->E1_CLIENTE .And.;
								cE1Loja == SE1->E1_LOJA .And.;
								cPrefixo == SE1->E1_PREFIXO .And.;
								SF1->F1_DOC == SE1->E1_NUM
							If (SE1->E1_TIPO $ MV_CRNEG)
								aadd(aRecSe1,SE1->(Recno()))
							EndIf
							DbSelectArea("SE1")
							dbSkip()
						EndDo
					EndIf 
				Else
					If Empty(aRecSE2)
						cPrefixo := PadR( cPrefixo, Len( SE2->E2_PREFIXO ) )
						DbSelectArea("SE2")
						DbSetOrder(6)

						lQuery    := .T.
						aStruSE2  := SE2->(dbStruct())
						cAliasSE2 := "A103NFISCAL"
						cQuery    := "SELECT E2_FILIAL, E2_FORNECE, E2_LOJA, E2_PREFIXO, E2_NUM, E2_TIPO, SE2.R_E_C_N_O_ SE2RECNO "
						cQuery    += "  FROM "+RetSqlName("SE2")+" SE2 "
						cQuery    += " WHERE SE2.E2_FILIAL  ='"+xFilial("SE2")+"'"
						cQuery    += "   AND SE2.E2_FORNECE ='"+SF1->F1_FORNECE+"'"
						cQuery    += "   AND SE2.E2_LOJA    ='"+SF1->F1_LOJA+"'"
						cQuery    += "   AND SE2.E2_PREFIXO ='"+cPrefixo+"'"
						cQuery    += "   AND SE2.E2_NUM     ='"+SF1->F1_DUPL+"'"
						cQuery    += "   AND SE2.E2_TIPO    ='"+MVNOTAFIS+"'"
						cQuery    += "   AND SE2.D_E_L_E_T_ =' ' "
						cQuery    += "ORDER BY "+SqlOrder(SE2->(IndexKey()))

						cQuery := ChangeQuery(cQuery)

						dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSE2,.T.,.T.)
						If (cAliasSE2)->(!Eof())
							(cAliasSE2)->(DbGoTop())
							For nX := 1 To Len(aStruSE2)
								If aStruSE2[nX][2]<>"C"
									TcSetField(cAliasSE2,aStruSE2[nX][1],aStruSE2[nX][2],aStruSE2[nX][3],aStruSE2[nX][4])
								EndIf
							Next nX

							While ( !Eof() .And. lContinua .And.;
									xFilial("SE2")    == (cAliasSE2)->E2_FILIAL  		   .And.;
									SF1->F1_FORNECE   == (cAliasSE2)->E2_FORNECE 		   .And.;
									SF1->F1_LOJA      == (cAliasSE2)->E2_LOJA    		   .And.;
									AllTrim(cPrefixo) == AllTrim((cAliasSE2)->E2_PREFIXO) .And.;
									SF1->F1_DUPL      == (cAliasSE2)->E2_NUM )

									If AllTrim((cAliasSE2)->E2_TIPO) == AllTrim(MVNOTAFIS)
										aadd(aRecSE2,If(lQuery,(cAliasSE2)->SE2RECNO,(cAliasSE2)->(RecNo())))
									EndIf
									DbSelectArea(cAliasSE2)
								dbSkip()
							Enddo
						Endif
						If lQuery
							DbSelectArea(cAliasSE2)
							dbCloseArea()
							DbSelectArea("SE2")
						EndIf
					EndIf
				EndIf
			EndIf

			If !l103Inclui
				
				//Faz a montagem do aCols com os dados do SD1
				DbSelectArea("SD1")
				DbSetOrder(1)

					aStruSD1  := SD1->(dbStruct())
						lQuery    := .T.
						cAliasSD1 := "A103NFISCAL"
						cAliasSB1 := "A103NFISCAL"
						cQuery    := "SELECT SD1.*,SD1.R_E_C_N_O_ SD1RECNO, B1_GRUPO,B1_CODITE,B1_TE,B1_COD "
						cQuery    += "  FROM "+RetSqlName("SD1")+" SD1, "
						cQuery    += RetSqlName("SB1")+" SB1 "
						cQuery    += " WHERE SD1.D1_FILIAL	= '"+xFilial("SD1")+"'"
						cQuery    += "   AND SD1.D1_DOC		= '"+SF1->F1_DOC+"'"
						cQuery    += "   AND SD1.D1_SERIE	= '"+SF1->F1_SERIE+"'"
						cQuery    += "   AND SD1.D1_FORNECE	= '"+SF1->F1_FORNECE+"'"
						cQuery    += "   AND SD1.D1_LOJA	= '"+SF1->F1_LOJA+"'"
						cQuery    += "   AND SD1.D1_TIPO	= '"+SF1->F1_TIPO+"'"
						cQuery    += "   AND SD1.D1_FORMUL	= '"+SF1->F1_FORMUL+"'"
						cQuery    += "   AND SD1.D_E_L_E_T_	= ' '"
						cQuery    += "   AND SB1.B1_FILIAL  = '"+xFilial("SB1")+"'"
						cQuery    += "   AND SB1.B1_COD 	= SD1.D1_COD "
						cQuery    += "   AND SB1.D_E_L_E_T_ =' ' "

						If (l103Class .And. lClassOrd) .Or. (l103Visual .And. lClassOrd) .Or. lNfeOrd
							cQuery    += "ORDER BY "+SqlOrder( "D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_ITEM+D1_COD" )
						Else
							cQuery    += "ORDER BY "+SqlOrder(SD1->(IndexKey()))
						EndIf

						cQuery := ChangeQuery(cQuery)

						dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSD1,.T.,.T.)
						For nX := 1 To Len(aStruSD1)
							If aStruSD1[nX][2]<>"C"
								TcSetField(cAliasSD1,aStruSD1[nX][1],aStruSD1[nX][2],aStruSD1[nX][3],aStruSD1[nX][4])
							EndIf
						Next nX

				bWhileSD1 := { || ( !Eof().And. lContinua .And. ; 
					(cAliasSD1)->D1_FILIAL== xFilial("SD1") .And. ;
					(cAliasSD1)->D1_DOC == SF1->F1_DOC .And. ;
					(cAliasSD1)->D1_SERIE == SF1->F1_SERIE .And. ;
					(cAliasSD1)->D1_FORNECE == SF1->F1_FORNECE .And. ;
					(cAliasSD1)->D1_LOJA == SF1->F1_LOJA .And. ;
					(cAliasSD1)->D1_FORMUL == SF1->F1_FORMUL ) }

				If !lQuery .And. ((l103Class .And. lClassOrd) .Or. (l103Visual .And. lClassOrd) .Or. lNfeOrd)
					//Este procedimento eh necessario para fazer a montagem
					//do acols na ordem ITEM + COD quando classificacao em CDX
					//e o parametro MV_CLASORD estiver ativado
					aRecClasSD1 := {}
					While ( !Eof().And. lContinua .And. ;
							(cAliasSD1)->D1_FILIAL== xFilial("SD1") .And. ;
							(cAliasSD1)->D1_DOC == SF1->F1_DOC .And. ;
							(cAliasSD1)->D1_SERIE == SF1->F1_SERIE .And. ;
							(cAliasSD1)->D1_FORNECE == SF1->F1_FORNECE .And. ;
							(cAliasSD1)->D1_LOJA == SF1->F1_LOJA )

						AAdd( aRecClasSD1, { ( cAliasSD1 )->D1_ITEM + ( cAliasSD1 )->D1_COD, ( cAliasSD1 )->( Recno() ) } )

					( cAliasSD1 )->( dbSkip() )
				EndDo

				ASort( aRecClasSD1, , , { |x,y| y[1] > x[1] } )

				nCounterSD1 := 1
				bWhileSD1 := { || nCounterSD1 <= Len( aRecClasSD1 ) .And. lContinua  }
			EndIf
		EndIf

		//Portaria CAT83  - Se o par‚metro n„o estiver ativo, n„o inclui o campo no acols
		If !SuperGetMv("MV_CAT8309",.F.,.F.)
			aAdd(aNoFields,"D1_CODLAN")
		EndIf
		
		aAdd(aNoFields,"D1_TESDES")

		if !lNfGarEst 
			aAdd(aNoFields,"D1_CBASEAF")
		endif

		if !lCsdXML .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C"
			aAdd(aNoFields,"D1_ITXML")
		endif

		If !lDivImp
			aAdd(aNoFields,"D1_LEGENDA")
		Endif
		
		//FILLGETDADOS (Monstagem do aHeader e aCols)
		//FillGetDados( nOpcx, cAlias, nOrder, cSeekKey, bSeekWhile, uSeekFor, aNoFields, aYesFields, lOnlyYes, cQuery, bMountFile, lInclui )
		//nOpcx			- Opcao (inclusao, exclusao, etc).
		//cAlias		- Alias da tabela referente aos itens
		//nOrder		- Ordem do SINDEX
		//cSeekKey		- Chave de pesquisa
		//bSeekWhile	- Loop na tabela cAlias
		//uSeekFor		- Valida cada registro da tabela cAlias (retornar .T. para considerar e .F. para desconsiderar o registro)
		//aNoFields		- Array com nome dos campos que serao excluidos na montagem do aHeader
		//aYesFields	- Array com nome dos campos que serao incluidos na montagem do aHeader
		//lOnlyYes		- Flag indicando se considera somente os campos declarados no aYesFields + campos do usuario
		//cQuery		- Query para filtro da tabela cAlias (se for TOP e cQuery estiver preenchido, desconsidera parametros cSeekKey e bSeekWhiele)
		//bMountFile	- Preenchimento do aCols pelo usuario (aHeader e aCols ja estarao criados)
		//lInclui		- Se inclusao passar .T. para qua aCols seja incializada com 1 linha em branco
		//aHeaderAux	- 
		//aColsAux		- 
		//bAfterCols	- Bloco executado apos inclusao de cada linha no aCols
		//bBeforeCols	- Bloco executado antes da inclusao de cada linha no aCols
		//bAfterHeader 	- 
		//cAliasQry		- Alias para a Query
		If cPaisLoc == "BRA"
			If l103Class .and. SF1->F1_FIMP$'TS' .And. SF1->F1_STATUS='C'//Tratamento para bloqueio de alteracoes na classificacao de uma nota bloqueada e ja transmitida.
				nOpcX:= 2
				FillGetDados(nOpcX,"SD1",1,/*cSeek*/,/*{|| &cWhile }*/,{||.T.},aNoFields,/*aYesFields*/,/*lOnlyYes*/,cQuery,{|| MontaaCols(bWhileSD1,lQuery,l103Class,lClassOrd,lNfeOrd,aRecClasSD1,@nCounterSD1,cAliasSD1,cAliasSB1,@aRecSD1,@aRateio,cCpBasePIS,cCpValPIS,cCpAlqPIS,cCpBaseCOF,cCpValCOF,cCpAlqCOF,@aHeader,@aCols,l103Inclui,aHeadSDE,aColsSDE,@lContinua,,lTColab) },Inclui,/*aHeaderAux*/,/*aColsAux*/,/*bAfterCols*/,/*bbeforeCols*/,/*bAfterHeader*/,/*cAliasQry*/)
			Else
				FillGetDados(nOpcX,"SD1",1,/*cSeek*/,/*{|| &cWhile }*/,{||.T.},aNoFields,/*aYesFields*/,/*lOnlyYes*/,cQuery,{|| MontaaCols(bWhileSD1,lQuery,l103Class,lClassOrd,lNfeOrd,aRecClasSD1,@nCounterSD1,cAliasSD1,cAliasSB1,@aRecSD1,@aRateio,cCpBasePIS,cCpValPIS,cCpAlqPIS,cCpBaseCOF,cCpValCOF,cCpAlqCOF,@aHeader,@aCols,l103Inclui,aHeadSDE,aColsSDE,@lContinua,,lTColab) },Inclui,/*aHeaderAux*/,/*aColsAux*/,/*bAfterCols*/,/*bbeforeCols*/,/*bAfterHeader*/,/*cAliasQry*/)
			EndIf
		Else
			FillGetDados(nOpcX,"SD1",1,/*cSeek*/,/*{|| &cWhile }*/,{||.T.},aNoFields,/*aYesFields*/,/*lOnlyYes*/,cQuery,{|| MontaaCols(bWhileSD1,lQuery,l103Class,lClassOrd,lNfeOrd,aRecClasSD1,@nCounterSD1,cAliasSD1,cAliasSB1,@aRecSD1,@aRateio,cCpBasePIS,cCpValPIS,cCpAlqPIS,cCpBaseCOF,cCpValCOF,cCpAlqCOF,@aHeader,@aCols,l103Inclui,aHeadSDE,aColsSDE,@lContinua) },Inclui,/*aHeaderAux*/,/*aColsAux*/,/*bAfterCols*/,/*bbeforeCols*/,/*bAfterHeader*/,/*cAliasQry*/)
        EndIf

		If lQuery
			DbSelectArea(cAliasSD1)
			dbCloseArea()
			DbSelectArea("SD1")
		EndIf
		If lContinua
			
			//Compatibilizacao da Base X.07 p/ X.08
			If !l103Inclui .And. !l103Class .And. !l103Visual .AND. Empty(SF1->F1_RECBMTO)
				MaFisAlt("NF_VALIRR",SF1->F1_IRRF,)
				MaFisAlt("NF_VALINS",SF1->F1_INSS,)
				MaFisAlt("NF_DESPESA",SF1->F1_DESPESA,)
				MaFisAlt("NF_FRETE",SF1->F1_FRETE,)
				MaFisAlt("NF_SEGURO",SF1->F1_SEGURO,)
			EndIf
			If l103Class .And. SF1->(ColumnPos('F1_UFDESTR'))>0 .And. !Empty(SF1->F1_UFDESTR)
				MaFisRef("NF_UFDEST","MT100",SF1->F1_UFDESTR)
			EndIf
			If l103Visual
				MaFisRef("NF_VALEMB","MT100",SF1->F1_VALEMB)
			EndIf
			If !l103Inclui .And.!l103Class
				MaFisAlt("NF_FUNRURAL",SF1->F1_CONTSOC,)
			EndIf
			If !l103Inclui .And.!l103Visual .And. !l103Class
				MaFisAlt("NF_TOTAL",SF1->F1_VALBRUT,)
			Endif
			
			//Rateio do valores de Frete/Seguro/Despesa do PC
			If !l103Class .Or. (!l103Inclui .And. SF1->F1_IMPORT <> 'S')
				If aRateio[1] <> 0
					MaFisAlt("NF_SEGURO",aRateio[1])
				EndIf
				If aRateio[2] <> 0
					MaFisAlt("NF_DESPESA",aRateio[2])
				EndIf
				If aRateio[3] <> 0
					MaFisAlt("NF_FRETE",aRateio[3])
				EndIf
				If aRateio[1]+aRateio[2]+aRateio[3] <> 0
					MaFisToCols(aHeader,aCols,,"MT100")
				EndIf
			Endif
			
			//Monta o Array contendo os Historico da NF
			If !l103Inclui
				aHistor := A103Histor(SF1->(RecNo()))
			EndIf
		EndIf
	EndIf

	If (l103Inclui .Or. l103Class) .And. !l103Auto
			
		If lContinua .and. lIntGC // Modulos do DMS
			If FindFunction("OA2900011_A103NFiscal_PodeClassificar")
				lContinua := OA2900011_A103NFiscal_PodeClassificar( { cTipo , cNFiscal , INCLUI } ) // Verifica se È possivel classificar a NF pelo MATA103
			EndIf
		EndIf
		
		//PNEUAC - Ponto de Entrada definicao da Operacao
		If lContinua .and. ExistBlock("MT103PN")
			If !Execblock("MT103PN",.F.,.F.,)
				lContinua := .F.
			EndIf
		EndIf
	EndIf
	If lContinua .And. !l103Auto .And. !Len(aCols) > 0
		lContinua := .F.
		Help(" ",1,"RECNO")
	EndIf
	If lContinua

		//Posiciona na SC5 para natureza obrigatÛria p/ DevoluÁ„o
		If Type("l103Devol") == "L"
			lDevol := l103Devol
		EndIf

		If SuperGetMV("MV_NFENAT",.F.,.F.) .And. "C5_NATUREZ" $ SuperGetMV("MV_1DUPNAT",.F.,"") .And. ( l103Class .Or. l103Auto .Or. lDevol)
			cKeySD2 := ""
			aAreaSD2x := SD2->(GetArea())
			SD2->(DbSetOrder(3))
			SD2->(DbGoTop())
			If l103Class .And. !Empty(SD1->D1_NFORI)
				cKeySD2 := xFilial("SD2")+SD1->D1_NFORI+SD1->D1_SERIORI+SD1->D1_FORNECE+SD1->D1_LOJA
			ElseIf lDevol
				cKeySD2 := xFilial("SD2")+SF2->F2_DOC+SF2->F2_SERIE+SF2->F2_CLIENTE+SF2->F2_LOJA
			ElseIf l103Auto
				nPosForDev := aScan(aAutoCab,{|x| AllTrim(x[1]) == "F1_FORNECE"})
				nPosLojDev := aScan(aAutoCab,{|x| AllTrim(x[1]) == "F1_LOJA"})
				nPosNfOri  := aScan(aAutoItens[1],{|x| AllTrim(x[1]) == "D1_NFORI"})
				nPosSerOri := aScan(aAutoItens[1],{|x| AllTrim(x[1]) == "D1_SERIORI"})
				If nPosNfOri > 0 .And. nPosSerOri > 0 .And. nPosForDev > 0 .And. nPosLojDev > 0 .And. !Empty(aAutoItens[1][nPosNfOri][2])
					cKeySD2 := xFilial("SD2")+aAutoItens[1][nPosNfOri][2]+aAutoItens[1][nPosSerOri][2]+aAutoCab[nPosForDev][2]+aAutoCab[nPosLojDev][2]
				EndIf
			EndIf

			If !Empty(cKeySD2) .And. SD2->(DbSeek(cKeySD2))
				DbSelectArea("SC5")
				SC5->(DbSetOrder(3))
				SC5->(DbSeek(xFilial("SC5")+SD2->D2_CLIENTE+SD2->D2_LOJA+SD2->D2_PEDIDO))
			EndIf
			RestArea(aAreaSD2x)
		EndIf

		//********************A T E N C A O ***************************
		//Quando for feita manutencao em alguma VALIDACAO dos GETs,
		//atualize as funcoes que se encontram no array aValidGet
		
		If ( l103Auto )
			aValidGet := {}
			aVldBlock := {}
			aNFeAut	  := aClone(aNFEletr)
			aDanfe    := aClone(aNFEDanfe)
			aIISS	  := aClone(aInfISS)
			aAdd(aVldBlock,{||NFeTipo(cTipo,@cA100For,@cLoja)})
			aAdd(aVldBlock,{||NfeFormul(cFormul,@cNFiscal,@cSerie)})
			aAdd(aVldBlock,{||NfeFornece(cTipo,@cA100For,@cLoja,,@nCombo,@oCombo,@cCodRet,@oCodRet,@aCodR,@cRecIss).And.CheckSX3("F1_DOC")})
			aAdd(aVldBlock,{||NfeFornece(cTipo,@cA100For,@cLoja,,@nCombo,@oCombo,@cCodRet,@oCodRet,@aCodR,@cRecIss).And.CheckSX3("F1_SERIE")})
			aAdd(aVldBlock,{||CheckSX3('F1_EMISSAO') .And. NfeEmissao(dDEmissao)})
			aAdd(aVldBlock,{||NfeFornece(cTipo,@cA100For,@cLoja,@cUfOrig,@nCombo,@oCombo,@cCodRet,@oCodRet,@aCodR,@cRecIss).And.CheckSX3("F1_LOJA",cLoja)})
			aAdd(aVldBlock,{||NfeFornece(cTipo,@cA100For,@cLoja,@cUfOrig,@nCombo,@oCombo,@cCodRet,@oCodRet,@aCodR,@cRecIss).And.CheckSX3("F1_FORNECE",cA100For)})
			aAdd(aVldBlock,{||CheckSX3('F1_ESPECIE',cEspecie)})
			aAdd(aVldBlock,{||CheckSX3('F1_EST',cUfOrig)})
			aAdd(aVldBlock,{||Vazio(cNatureza).Or.(ExistCpo('SED',cNatureza).And.NfeVldRef("NF_NATUREZA",cNatureza)) .And. If(lMt103Nat,ExecBlock("MT103NAT",.F.,.F.,cNatureza),.T.)})
			For nX = 11 to 76
				aAdd(aVldBlock,"")
			Next nX
				
			IF aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_DOC"}) == 0
				aadd(aAutoCab,{"F1_DOC","",nil})
			Endif
			If l103Inclui

				Aadd(aValidGet,{"cTipo"    ,aAutoCab[ProcH("F1_TIPO"),2],"Eval(aVldBlock[1])",.F.})
				Aadd(aValidGet,{"cFormul"  ,aAutoCab[ProcH("F1_FORMUL"),2],"Eval(aVldBlock[2])",.F.})
				Aadd(aValidGet,{"cNFiscal" ,aAutoCab[ProcH("F1_DOC"),2],"Eval(aVldBlock[3])",.F.})
				Aadd(aValidGet,{"cSerie"   ,aAutoCab[ProcH("F1_SERIE"),2],"Eval(aVldBlock[4])",.F.})
				Aadd(aValidGet,{"dDEmissao",aAutoCab[ProcH("F1_EMISSAO"),2],"Eval(aVldBlock[5])",.F.})
				Aadd(aValidGet,{"cLoja"    ,aAutoCab[ProcH("F1_LOJA"),2],"Eval(aVldBlock[6])",.F.})
				Aadd(aValidGet,{"cA100For" ,aAutoCab[ProcH("F1_FORNECE"),2],"Eval(aVldBlock[7])",.F.})
				Aadd(aValidGet,{"cEspecie" ,aAutoCab[ProcH("F1_ESPECIE"),2],"Eval(aVldBlock[8])",.F.})

				If lSubSerie .And. ProcH("F1_SUBSERI") > 0
					aVldBlock[73] := {||NfeFornece(cTipo,@cA100For,@cLoja,,@nCombo,@oCombo,@cCodRet,@oCodRet,@aCodR,@cRecIss).And.CheckSX3("F1_SUBSERI")}
					Aadd(aValidGet,{"cSubSerie",aAutoCab[ProcH("F1_SUBSERI"),2],"Eval(aVldBlock[73])",.F.})
				EndIf

				If ProcH("F1_MOEDA") > 0
					Aadd(aValidGet,{"nMoedaCor" ,aAutoCab[ProcH("F1_MOEDA"),2],"",.F.})
				EndIf

				If ProcH("F1_TXMOEDA") > 0
					Aadd(aValidGet,{"nTaxa"     ,aAutoCab[ProcH("F1_TXMOEDA"),2],"",.F.})
				EndIf

				If ProcH("F1_EST") > 0
					Aadd(aValidGet,{"cUfOrig"  ,aAutoCab[ProcH("F1_EST"),2],"Eval(aVldBlock[9])",.F.})
				EndIf

				If cPaisLoc == "BRA"
				    // NFE
					If ProcH("F1_NFELETR") > 0
						aVldBlock[11] := {||CheckSX3('F1_NFELETR',aNFeAut[01])}
						Aadd(aValidGet,{"aNFeAut[01]",aAutoCab[ProcH("F1_NFELETR"),2],"Eval(aVldBlock[11])",.F.})
						aNFEletr[01] := aAutoCab[ProcH("F1_NFELETR"),2]
					Endif
					If ProcH("F1_CODNFE") > 0
						aVldBlock[12] := {||CheckSX3('F1_CODNFE',aNFeAut[02])}
						Aadd(aValidGet,{"aNFeAut[02]",aAutoCab[ProcH("F1_CODNFE"),2],"Eval(aVldBlock[12])",.F.})
						aNFEletr[02] := aAutoCab[ProcH("F1_CODNFE"),2]
					Endif
					If ProcH("F1_EMINFE") > 0
						aVldBlock[13] := {||A103NFe('EMINFE',aNFeAut) .And. CheckSX3('F1_EMINFE',aNFeAut[03])}
						Aadd(aValidGet,{"aNFeAut[03]",aAutoCab[ProcH("F1_EMINFE"),2],"Eval(aVldBlock[13])",.F.})
						aNFEletr[03] := aAutoCab[ProcH("F1_EMINFE"),2]
					Endif
					If ProcH("F1_HORNFE") > 0
						aVldBlock[14] := {||CheckSX3('F1_HORNFE',aNFeAut[04])}
						Aadd(aValidGet,{"aNFeAut[04]",aAutoCab[ProcH("F1_HORNFE"),2],"Eval(aVldBlock[14])",.F.})
						aNFEletr[04] := aAutoCab[ProcH("F1_HORNFE"),2]
					Endif
					If ProcH("F1_CREDNFE") > 0
						aVldBlock[15] := {||A103NFe('CREDNFE',aNFeAut) .And. CheckSX3('F1_CREDNFE',aNFeAut[05])}
						Aadd(aValidGet,{"aNFeAut[05]",aAutoCab[ProcH("F1_CREDNFE"),2],"Eval(aVldBlock[15])",.F.})
						aNFEletr[05] := aAutoCab[ProcH("F1_CREDNFE"),2]
					Endif
					If ProcH("F1_NUMRPS") > 0
						aVldBlock[16] := {||CheckSX3('F1_NUMRPS',aNFeAut[06])}
						Aadd(aValidGet,{"aNFeAut[06]",aAutoCab[ProcH("F1_NUMRPS"),2],"Eval(aVldBlock[16])",.F.})
						aNFEletr[06] := aAutoCab[ProcH("F1_NUMRPS"),2]
					Endif
					If ProcH("F1_MENNOTA") > 0
						aVldBlock[29] := {||CheckSX3('F1_MENNOTA',aNFeAut[07])}
						Aadd(aValidGet,{"aNFeAut[07]",aAutoCab[ProcH("F1_MENNOTA"),2],"Eval(aVldBlock[29])",.F.})
						aNFEletr[07] := aAutoCab[ProcH("F1_MENNOTA"),2]
					Endif
					If ProcH("F1_MENPAD") > 0
						aVldBlock[64] := {||CheckSX3('F1_MENPAD',aNFeAut[08])}
						Aadd(aValidGet,{"aNFeAut[08]",aAutoCab[ProcH("F1_MENPAD"),2],"Eval(aVldBlock[64])",.F.})
						aNFEletr[08] := aAutoCab[ProcH("F1_MENPAD"),2]
					Endif

					//Danfe
						If ProcH("F1_TRANSP") > 0
		 					aVldBlock[17] := {|| ExistCpo("SA4",aDanfe[01],1,NIL,.T.)}
							Aadd(aValidGet,{"aDanfe[01]",aAutoCab[ProcH("F1_TRANSP"),2],"Eval(aVldBlock[17])",.F.})
							aNfeDanfe[01] := aAutoCab[ProcH("F1_TRANSP"),2]
						Endif

						If ProcH("F1_PLIQUI") > 0
		 					aVldBlock[18] := {||CheckSX3('F1_PLIQUI',aDanfe[02])}
							Aadd(aValidGet,{"aDanfe[02]",aAutoCab[ProcH("F1_PLIQUI"),2],"Eval(aVldBlock[18])",.F.})
							aNfeDanfe[02] := aAutoCab[ProcH("F1_PLIQUI"),2]
						Endif

						If ProcH("F1_PBRUTO") > 0
		 					aVldBlock[19] := {||CheckSX3('F1_PBRUTO',aDanfe[03])}
							Aadd(aValidGet,{"aDanfe[03]",aAutoCab[ProcH("F1_PBRUTO"),2],"Eval(aVldBlock[19])",.F.})
							aNfeDanfe[03] := aAutoCab[ProcH("F1_PBRUTO"),2]
						Endif

						If ProcH("F1_ESPECI1") > 0
	 						aVldBlock[20] := {||CheckSX3('F1_ESPECI1',aDanfe[04])}
							Aadd(aValidGet,{"aDanfe[04]",aAutoCab[ProcH("F1_ESPECI1"),2],"Eval(aVldBlock[20])",.F.})
							aNfeDanfe[04] := aAutoCab[ProcH("F1_ESPECI1"),2]
						Endif

						If ProcH("F1_VOLUME1") > 0
	 						aVldBlock[21] := {||CheckSX3('F1_VOLUME1',aDanfe[05])}
							Aadd(aValidGet,{"aDanfe[05]",aAutoCab[ProcH("F1_VOLUME1"),2],"Eval(aVldBlock[21])",.F.})
							aNfeDanfe[05] := aAutoCab[ProcH("F1_VOLUME1"),2]
						Endif

						If ProcH("F1_ESPECI2") > 0
	 						aVldBlock[22] := {||CheckSX3('F1_ESPECI2',aDanfe[06])}
							Aadd(aValidGet,{"aDanfe[06]",aAutoCab[ProcH("F1_ESPECI2"),2],"Eval(aVldBlock[22])",.F.})
							aNfeDanfe[06] := aAutoCab[ProcH("F1_ESPECI2"),2]
						Endif

						If ProcH("F1_VOLUME2") > 0
	 						aVldBlock[23] := {||CheckSX3('F1_VOLUME2',aDanfe[07])}
							Aadd(aValidGet,{"aDanfe[07]",aAutoCab[ProcH("F1_VOLUME2"),2],"Eval(aVldBlock[23])",.F.})
							aNfeDanfe[07] := aAutoCab[ProcH("F1_VOLUME2"),2]
						Endif

						If ProcH("F1_ESPECI3") > 0
	 						aVldBlock[24] := {||CheckSX3('F1_ESPECI3',aDanfe[08])}
							Aadd(aValidGet,{"aDanfe[08]",aAutoCab[ProcH("F1_ESPECI3"),2],"Eval(aVldBlock[24])",.F.})
							aNfeDanfe[08] := aAutoCab[ProcH("F1_ESPECI3"),2]
						Endif

						If ProcH("F1_VOLUME3") > 0
	 						aVldBlock[25] := {||CheckSX3('F1_VOLUME3',aDanfe[09])}
							Aadd(aValidGet,{"aDanfe[09]",aAutoCab[ProcH("F1_VOLUME3"),2],"Eval(aVldBlock[25])",.F.})
							aNfeDanfe[09] := aAutoCab[ProcH("F1_VOLUME3"),2]
						Endif

						If ProcH("F1_ESPECI4") > 0
	 						aVldBlock[26] := {||CheckSX3('F1_ESPECI4',aDanfe[10])}
							Aadd(aValidGet,{"aDanfe[10]",aAutoCab[ProcH("F1_ESPECI4"),2],"Eval(aVldBlock[26])",.F.})
							aNfeDanfe[10] := aAutoCab[ProcH("F1_ESPECI4"),2]
						Endif

						If ProcH("F1_VOLUME4") > 0
	 						aVldBlock[27] :=  {||CheckSX3('F1_VOLUME4',aDanfe[11])}
							Aadd(aValidGet,{"aDanfe[11]",aAutoCab[ProcH("F1_VOLUME4"),2],"Eval(aVldBlock[27])",.F.})
							aNfeDanfe[11] := aAutoCab[ProcH("F1_VOLUME4"),2]
						Endif

						If ProcH("F1_PLACA") > 0
	 						aVldBlock[28] := {||CheckSX3('F1_PLACA',aDanfe[12])}
							Aadd(aValidGet,{"aDanfe[12]",aAutoCab[ProcH("F1_PLACA"),2],"Eval(aVldBlock[28])",.F.})
							aNfeDanfe[12] := aAutoCab[ProcH("F1_PLACA"),2]
						Endif

						If ProcH("F1_CHVNFE") > 0
							If !l103GAuto	// Nao deve efetuar validacao da chave na importacao do XML ou no vinculo de pedidos de compra do TOTVS Colab (COMXCOL)
								aVldBlock[66] := {||CheckSX3('F1_CHVNFE',aDanfe[13])}
							Else
								aVldBlock[66] := {|| CheckSX3('F1_CHVNFE',aDanfe[13]) .And. A103ChamaHelp(l103Inclui,l103Class) .And. A103ConsNfeSef(,aAutoCab)}
							EndIf
							Aadd(aValidGet,{"aDanfe[13]",aAutoCab[ProcH("F1_CHVNFE"),2],"Eval(aVldBlock[66])",.F.})
							aNfeDanfe[13] := aAutoCab[ProcH("F1_CHVNFE"),2]
						Endif 

						If ProcH("F1_TPFRETE") > 0
		 					aVldBlock[30] := {||CheckSX3('F1_TPFRETE',aDanfe[14])}
							Aadd(aValidGet,{"aDanfe[14]",aAutoCab[ProcH("F1_TPFRETE"),2],"Eval(aVldBlock[30])",.F.})
							aNfeDanfe[14] := aAutoCab[ProcH("F1_TPFRETE"),2]
						Endif

						If ProcH("F1_VALPEDG") > 0
	 						aVldBlock[31] := {||CheckSX3('F1_VALPEDG',aDanfe[15])}
							Aadd(aValidGet,{"aDanfe[15]",aAutoCab[ProcH("F1_VALPEDG"),2],"Eval(aVldBlock[31])",.F.})
							aNfeDanfe[15] := aAutoCab[ProcH("F1_VALPEDG"),2]
						Endif

						If ProcH("F1_FORRET") > 0
	 						aVldBlock[32] := {||CheckSX3('F1_FORRET',aDanfe[16])}
							Aadd(aValidGet,{"aDanfe[16]",aAutoCab[ProcH("F1_FORRET"),2],"Eval(aVldBlock[32])",.F.})
							aNfeDanfe[16] := aAutoCab[ProcH("F1_FORRET"),2]
						Endif

						If ProcH("F1_LOJARET") > 0
	 						aVldBlock[33] := {||CheckSX3('F1_LOJARET',aDanfe[17])}
							Aadd(aValidGet,{"aDanfe[17]",aAutoCab[ProcH("F1_LOJARET"),2],"Eval(aVldBlock[33])",.F.})
							aNfeDanfe[17] := aAutoCab[ProcH("F1_LOJARET"),2]
						Endif

						If ProcH("F1_TPCTE") > 0
		 					aVldBlock[34] := {||CheckSX3('F1_TPCTE',aDanfe[18])}
							Aadd(aValidGet,{"aDanfe[18]",aAutoCab[ProcH("F1_TPCTE"),2],"Eval(aVldBlock[34])",.F.})
							aNfeDanfe[18] := aAutoCab[ProcH("F1_TPCTE"),2]
						Endif

						If ProcH("F1_FORENT") > 0
	 						aVldBlock[35] := {||CheckSX3('F1_FORENT',aDanfe[19])}
							Aadd(aValidGet,{"aDanfe[19]",aAutoCab[ProcH("F1_FORENT"),2],"Eval(aVldBlock[35])",.F.})
							aNfeDanfe[19] := aAutoCab[ProcH("F1_FORENT"),2]
						Endif

						If ProcH("F1_LOJAENT") > 0
	 						aVldBlock[36] := {||CheckSX3('F1_LOJAENT',aDanfe[20])}
							Aadd(aValidGet,{"aDanfe[20]",aAutoCab[ProcH("F1_LOJAENT"),2],"Eval(aVldBlock[36])",.F.})
							aNfeDanfe[20] := aAutoCab[ProcH("F1_LOJAENT"),2]
						Endif

						If ProcH("F1_NUMAIDF") > 0
	 						aVldBlock[37] := {||CheckSX3('F1_NUMAIDF',aDanfe[21])}
							Aadd(aValidGet,{"aDanfe[21]",aAutoCab[ProcH("F1_NUMAIDF"),2],"Eval(aVldBlock[37])",.F.})
							aNfeDanfe[21] := aAutoCab[ProcH("F1_NUMAIDF"),2]
						Endif

						If ProcH("F1_ANOAIDF") > 0
	 						aVldBlock[38] := {||CheckSX3('F1_ANOAIDF',aDanfe[22])}
							Aadd(aValidGet,{"aDanfe[22]",aAutoCab[ProcH("F1_ANOAIDF"),2],"Eval(aVldBlock[38])",.F.})
							aNfeDanfe[22] := aAutoCab[ProcH("F1_ANOAIDF"),2]
						Endif

						If ProcH("F1_MODAL") > 0
							aVldBlock[65] := {||CheckSX3('F1_MODAL',aDanfe[23])}
							Aadd(aValidGet,{"aDanfe[23]",aAutoCab[ProcH("F1_MODAL"),2],"Eval(aVldBlock[65])",.F.})
							aNfeDanfe[23] := aAutoCab[ProcH("F1_MODAL"),2]
						Endif

						If ProcH("F1_DEVMERC") > 0
							aVldBlock[67] := {||CheckSX3('F1_DEVMERC',aDanfe[24])}
							Aadd(aValidGet,{"aDanfe[24]",aAutoCab[ProcH("F1_DEVMERC"),2],"Eval(aVldBlock[67])",.F.})
							If ProcH("F1_TIPO") > 0 .And. aAutoCab[ProcH("F1_TIPO"),2] $ "DBN" .And. ProcH("F1_FORMUL") > 0 .And. aAutoCab[ProcH("F1_FORMUL"),2] == "S"
								aNfeDanfe[24] := aAutoCab[ProcH("F1_DEVMERC"),2]
							Else
								aNfeDanfe[24] := " "
							EndIf
						EndIf
					// Informacoes adicionais
					If ProcH("F1_INCISS") > 0
 						aVldBlock[56] := {||CheckSX3('F1_INCISS',aInfAdic[01])}
						Aadd(aValidGet,{"aInfAdic[01]",aAutoCab[ProcH("F1_INCISS"),2],"Eval(aVldBlock[56])",.F.})
						aInfAdic[01] := aAutoCab[ProcH("F1_INCISS"),2]
					EndIf

					If ProcH("F1_VEICUL1") > 0
 						aVldBlock[57] := {||CheckSX3('F1_VEICUL1',aInfAdic[02])}
						Aadd(aValidGet,{"aInfAdic[02]",aAutoCab[ProcH("F1_VEICUL1"),2],"Eval(aVldBlock[57])",.F.})
						aInfAdic[02] := aAutoCab[ProcH("F1_VEICUL1"),2]
					EndIf

					If ProcH("F1_VEICUL2") > 0
 						aVldBlock[58] := {||CheckSX3('F1_VEICUL2',aInfAdic[03])}
						Aadd(aValidGet,{"aInfAdic[03]",aAutoCab[ProcH("F1_VEICUL2"),2],"Eval(aVldBlock[58])",.F.})
						aInfAdic[03] := aAutoCab[ProcH("F1_VEICUL2"),2]
					EndIf

					If ProcH("F1_VEICUL3") > 0
 						aVldBlock[59] := {||CheckSX3('F1_VEICUL3',aInfAdic[04])}
						Aadd(aValidGet,{"aInfAdic[04]",aAutoCab[ProcH("F1_VEICUL3"),2],"Eval(aVldBlock[59])",.F.})
						aInfAdic[04] := aAutoCab[ProcH("F1_VEICUL3"),2]
					EndIf

					If ProcH("F1_DTCPISS") > 0
						aVldBlock[60] := {||CheckSX3('F1_DTCPISS',aInfAdic[05])}
						Aadd(aValidGet,{"aInfAdic[05]",aAutoCab[ProcH("F1_DTCPISS"),2],"Eval(aVldBlock[60])",.F.})
						aInfAdic[05] := aAutoCab[ProcH("F1_DTCPISS"),2]
					EndIf

					If ProcH("F1_SIMPNAC") > 0
 						aVldBlock[61] := {||CheckSX3('F1_SIMPNAC',aInfAdic[06])}
						Aadd(aValidGet,{"aInfAdic[06]",aAutoCab[ProcH(F1_SIMPNAC),2],"Eval(aVldBlock[61])",.F.})
						aInfAdic[06] := aAutoCab[ProcH("F1_SIMPNAC"),2]
					EndIf

					If ProcH("F1_CLIDEST") > 0
						aVldBlock[62] := {||CheckSX3('F1_CLIDEST',aInfAdic[07])}
						Aadd(aValidGet,{"aInfAdic[07]",aAutoCab[ProcH("F1_CLIDEST"),2],"Eval(aVldBlock[62])",.F.})
						aInfAdic[07] := aAutoCab[ProcH("F1_CLIDEST"),2]
					EndIf

					If ProcH("F1_LOJDEST") > 0
						aVldBlock[63] := {||CheckSX3('F1_LOJDEST',aInfAdic[08])}
						Aadd(aValidGet,{"aInfAdic[08]",aAutoCab[ProcH("F1_LOJDEST"),2],"Eval(aVldBlock[63])",.F.})
						aInfAdic[08] := aAutoCab[ProcH("F1_LOJDEST"),2]
					EndIf

					If ProcH("F1_ESTDES") > 0
						aVldBlock[68] := {||CheckSX3("F1_ESTDES",aInfAdic[09])}
						Aadd(aValidGet,{"aInfAdic[09]",aAutoCab[ProcH("F1_ESTDES"),2],"Eval(aVldBlock[68])",.F.})
						aInfAdic[09] := aAutoCab[ProcH("F1_ESTDES"),2]
					EndIf

					If ProcH("F1_UFORITR") > 0
						aVldBlock[69] := {||CheckSX3('F1_UFORITR',aInfAdic[10])}
						Aadd(aValidGet,{"aInfAdic[10]",aAutoCab[ProcH("F1_UFORITR"),2],"Eval(aVldBlock[69])",.F.})
						aInfAdic[10] := aAutoCab[ProcH("F1_UFORITR"),2]
						MaFisAlt("NF_UFORIGEM",aInfAdic[10])
					EndIf

					If ProcH("F1_MUORITR") > 0
						aVldBlock[70] := {||CheckSX3('F1_MUORITR',aInfAdic[11])}
						Aadd(aValidGet,{"aInfAdic[11]",aAutoCab[ProcH("F1_MUORITR"),2],"Eval(aVldBlock[70])",.F.})
						aInfAdic[11] := aAutoCab[ProcH("F1_MUORITR"),2]
					EndIf

					If ProcH("F1_UFDESTR") > 0
						aVldBlock[71] := {||CheckSX3('F1_UFDESTR',aInfAdic[12])}
						Aadd(aValidGet,{"aInfAdic[12]",aAutoCab[ProcH("F1_UFDESTR"),2],"Eval(aVldBlock[71])",.F.})
						aInfAdic[12] := aAutoCab[ProcH("F1_UFDESTR"),2]
						MaFisAlt("NF_UFDEST",aInfAdic[12])
					EndIf

					If ProcH("F1_MUDESTR") > 0
						aVldBlock[72] := {||CheckSX3('F1_MUDESTR',aInfAdic[13])}
						Aadd(aValidGet,{"aInfAdic[13]",aAutoCab[ProcH("F1_MUDESTR"),2],"Eval(aVldBlock[72])",.F.})
						aInfAdic[13] := aAutoCab[ProcH("F1_MUDESTR"),2]
					EndIf

					If ProcH("F1_CLIPROP") > 0
                        aVldBlock[73] := {||CheckSX3('F1_CLIPROP',aInfAdic[14])}
                        Aadd(aValidGet,{"aInfAdic[14]",aAutoCab[ProcH("F1_CLIPROP"),2],"Eval(aVldBlock[73])",.F.})
                        aInfAdic[14] := aAutoCab[ProcH("F1_CLIPROP"),2]
                    EndIf

                    If ProcH("F1_LJCLIPR") > 0
                        aVldBlock[74] := {||CheckSX3('F1_LJCLIPR',aInfAdic[15])}
                        Aadd(aValidGet,{"aInfAdic[15]",aAutoCab[ProcH("F1_LJCLIPR"),2],"Eval(aVldBlock[74])",.F.})
                        aInfAdic[15] := aAutoCab[ProcH("F1_LJCLIPR"),2]
                    EndIf

					If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
						If ProcH("F1_INDPRES") > 0
							aVldBlock[75] := {|| A103VldPres()}
							Aadd(aValidGet,{"aInfAdic[16]",aAutoCab[ProcH("F1_INDPRES"),2],"Eval(aVldBlock[75])",.F.})
							aInfAdic[16] := aAutoCab[ProcH("F1_INDPRES"),2]

							If aAutoCab[ProcH("F1_FORMUL"),2] == "S" .And. A103EICTRANS(aAutoCab) .And. Empty(aInfAdic[16])
								aInfAdic[16] := "1"
							Endif
						Else
							If aAutoCab[ProcH("F1_FORMUL"),2] == "S" .And. A103EICTRANS(aAutoCab)
								aInfAdic[16] := "1"
							Endif
						EndIf 

						If ProcH("F1_CODA1U") > 0
							aVldBlock[76] := {|| A103VldA1U()}
							Aadd(aValidGet,{"aInfAdic[17]",aAutoCab[ProcH("F1_CODA1U"),2],"Eval(aVldBlock[76])",.F.})
							aInfAdic[17] := aAutoCab[ProcH("F1_CODA1U"),2]
						EndIf
					Endif

					If cPaisLoc = "BRA" .And. lISSxMun .And. Ascan(aAutoCab,{|x| x[1] == 'A2_COD_MUN'}) > 0
						//DADOS DO MUNICIPIO
						aVldBlock[39] := {||CheckSX3('A2_COD_MUN',aIISS[1][1])}
						Aadd(aValidGet,{"aIISS[1][1]",aAutoCab[ProcH("A2_COD_MUN"),2],"Eval(aVldBlock[39])",.F.})
						aInfISS[1][1] := aAutoCab[ProcH("A2_COD_MUN"),2]

						aVldBlock[40] := {||CheckSX3('CC2_MUN',aIISS[1][2])}
						Aadd(aValidGet,{"aIISS[1][2]",aAutoCab[ProcH("CC2_MUN"),2],"Eval(aVldBlock[40])",.F.})
						aInfISS[1][2] := aAutoCab[ProcH("CC2_MUN"),2]

						aVldBlock[41] := {||CheckSX3('CC2_EST',aIISS[1][3])}
						Aadd(aValidGet,{"aIISS[1][3]",aAutoCab[ProcH("CC2_EST"),2],"Eval(aVldBlock[41])",.F.})
						aInfISS[1][3] := aAutoCab[ProcH("CC2_EST"),2]

						aVldBlock[42] := {||CheckSX3('CC2_MDEDMA',aIISS[1][4])}
						Aadd(aValidGet,{"aIISS[1][4]",aAutoCab[ProcH("CC2_MDEDMA"),2],"Eval(aVldBlock[42])",.F.})
						aInfISS[1][4] := aAutoCab[ProcH("CC2_MDEDMA"),2]

						aVldBlock[43] := {||CheckSX3('CC2_MDEDSR',aIISS[1][5])}
						Aadd(aValidGet,{"aIISS[1][5]",aAutoCab[ProcH("CC2_MDEDSR"),2],"Eval(aVldBlock[43])",.F.})
						aInfISS[1][5] := aAutoCab[ProcH("CC2_MDEDSR"),2]

						aVldBlock[44] := {||CheckSX3('CC2_PERMAT',aIISS[1][6])}
						Aadd(aValidGet,{"aIISS[1][6]",aAutoCab[ProcH("CC2_PERMAT"),2],"Eval(aVldBlock[44])",.F.})
						aInfISS[1][6] := aAutoCab[ProcH("CC2_PERMAT"),2]

						aVldBlock[45] := {||CheckSX3('CC2_PERSER',aIISS[1][7])}
						Aadd(aValidGet,{"aIISS[1][7]",aAutoCab[ProcH("CC2_PERSER"),2],"Eval(aVldBlock[45])",.F.})
						aInfISS[1][7] := aAutoCab[ProcH("CC2_PERSER"),2]

						//ISS APURADO
						aVldBlock[46] := {||CheckSX3('D1_TOTAL',aIISS[2][1])}
						Aadd(aValidGet,{"aIISS[2][1]",aAutoCab[ProcH("D1_TOTAL"),2],"Eval(aVldBlock[46])",.F.})
						aInfISS[2][1] := aAutoCab[ProcH("D1_TOTAL"),2]

						aVldBlock[47] := {||CheckSX3('D1_ABATISS',aIISS[2][2])}
						Aadd(aValidGet,{"aIISS[2][2]",aAutoCab[ProcH("D1_ABATISS"),2],"Eval(aVldBlock[47])",.F.})
						aInfISS[2][2] := aAutoCab[ProcH("D1_ABATISS"),2]

						aVldBlock[48] := {||CheckSX3('D1_ABATMAT',aIISS[2][3])}
						Aadd(aValidGet,{"aIISS[2][3]",aAutoCab[ProcH("D1_ABATMAT"),2],"Eval(aVldBlock[48])",.F.})
						aInfISS[2][3] := aAutoCab[ProcH("D1_ABATMAT"),2]

						aVldBlock[49] := {||CheckSX3('D1_BASEISS',aIISS[2][4])}
						Aadd(aValidGet,{"aIISS[2][4]",aAutoCab[ProcH("D1_BASEISS"),2],"Eval(aVldBlock[49])",.F.})
						aInfISS[2][4] := aAutoCab[ProcH("D1_BASEISS"),2]

						aVldBlock[50] := {||CheckSX3('D1_VALISS',aIISS[2][5])}
						Aadd(aValidGet,{"aIISS[2][5]",aAutoCab[ProcH("D1_VALISS"),2],"Eval(aVldBlock[50])",.F.})
						aInfISS[2][5] := aAutoCab[ProcH("D1_VALISS"),2]

						//INSS APURADO
						aVldBlock[51] := {||CheckSX3('D1_TOTAL',aIISS[3][1])}
						Aadd(aValidGet,{"aIISS[3][1]",aAutoCab[ProcH("D1_TOTAL"),2],"Eval(aVldBlock[51])",.F.})
						aInfISS[3][1] := aAutoCab[ProcH("D1_TOTAL"),2]

						aVldBlock[52] := {||CheckSX3('D1_ABATINS',aIISS[3][2])}
						Aadd(aValidGet,{"aIISS[3][2]",aAutoCab[ProcH("D1_ABATINS"),2],"Eval(aVldBlock[52])",.F.})
						aInfISS[3][2] := aAutoCab[ProcH("D1_ABATINS"),2]

						aVldBlock[53] := {||CheckSX3('D1_AVLINSS',aIISS[3][3])}
						Aadd(aValidGet,{"aIISS[3][3]",aAutoCab[ProcH("D1_AVLINSS"),2],"Eval(aVldBlock[53])",.F.})
						aInfISS[3][3] := aAutoCab[ProcH("D1_AVLINSS"),2]

						aVldBlock[54] := {||CheckSX3('D1_BASEINS',aIISS[3][4])}
						Aadd(aValidGet,{"aIISS[3][4]",aAutoCab[ProcH("D1_BASEINS"),2],"Eval(aVldBlock[54])",.F.})
						aInfISS[3][4] := aAutoCab[ProcH("D1_BASEINS"),2]

						aVldBlock[55] := {||CheckSX3('D1_VALINS',aIISS[3][5])}
						Aadd(aValidGet,{"aIISS[3][5]",aAutoCab[ProcH("D1_VALINS"),2],"Eval(aVldBlock[55])",.F.})
						aInfISS[3][5] := aAutoCab[ProcH("D1_VALINS"),2]
					EndIf
				Endif

				If ProcH("F1_COND") > 0
					cCondicao := aAutoCab[ProcH("F1_COND"),2] 
					aVldBlock[74] := {|| NfeCond(cCondicao)}
					Aadd(aValidGet,{"cCondicao",aAutoCab[ProcH("F1_COND"),2],"Eval(aVldBlock[74])",.F.})
				EndIf

				If !lWhenGet
					nOpc := 1
				EndIf
				If !SF1->(MsVldGAuto(aValidGet))
					nOpc := 0
				EndIf
				
				If ProcH("F1_RECISS") > 0
					cRecIss := aAutoCab[ProcH("F1_RECISS"),2]
				EndIf

				If ( nOpc == 1 .Or. lWhenGet ) .And. l103Inclui
					If cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_CLIDEST")) > 0 .And. SF1->(ColumnPos("F1_LOJDEST")) > 0 .AND. ProcH("F1_CLIDEST") > 0 .And. ProcH("F1_LOJDEST") > 0
						MaFisIni(cA100For,cLoja,IIf(cTipo$'DB',"C","F"),cTipo,Nil,MaFisRelImp("MT100",{"SF1","SD1"}),,IIf(lWhenGet,.T.,.F.),,,,,,,,,,,,,,,,,dDEmissao,,,,,,aAutoCab[ProcH("F1_CLIDEST"),2],aAutoCab[ProcH("F1_LOJDEST"),2],lTrbGen)

						//Atualiza UF de Destino apos a inicializacao das rotinas fiscais
						If SF1->(ColumnPos("F1_ESTDES")) > 0
							If ProcH("F1_ESTDES") > 0 .AND. !Empty(aAutoCab[ProcH("F1_ESTDES"),2])
								MaFisAlt("NF_UFCDEST", aAutoCab[ProcH("F1_ESTDES"),2])
							EndIf
						EndIf

						// Se o campo F1_UFDESTR nao for informado, atualiza a UF de destino com o cliente informado nos campos F1_CLIDEST/F1_LOJDEST (mesmo comportamento da inclusao manual da nota)
						If !Empty(aAutoCab[ProcH("F1_CLIDEST"),2]) .And. !Empty(aAutoCab[ProcH("F1_LOJDEST"),2]) .And. ( ProcH("F1_UFDESTR") == 0 .Or. Empty(aAutoCab[ProcH("F1_UFDESTR"),2]) )
							MaFisLoad("NF_UFDEST", Posicione("SA1",1,xFilial("SA1")+aAutoCab[ProcH("F1_CLIDEST"),2]+aAutoCab[ProcH("F1_LOJDEST"),2],"A1_EST"))
						EndIf

					Else
						MaFisIni(cA100For,cLoja,IIf(cTipo$'DB',"C","F"),cTipo,Nil,MaFisRelImp("MT100",{"SF1","SD1"}),,IIf(lWhenGet,.T.,.F.),,,,,,,,,,,,,,,,,dDEmissao,,,,,,,,lTrbGen)
					EndIf
					//Atualiza UF de Origem apos a inicializacao das rotinas fiscais
					MaFisAlt("NF_UFORIGEM",cUfOrig)
				Else
					If cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_CLIDEST")) > 0 .And. SF1->(ColumnPos("F1_LOJDEST")) > 0
						If ProcH("F1_CLIDEST") > 0 .And. ProcH("F1_LOJDEST") > 0;
							.and. !Empty(aAutoCab[ProcH("F1_CLIDEST"),2]) .and. !Empty(aAutoCab[ProcH("F1_LOJDEST"),2])
							MaFisAlt("NF_CLIDEST", aAutoCab[ProcH("F1_CLIDEST"),2])
							MaFisAlt("NF_LOJDEST", aAutoCab[ProcH("F1_LOJDEST"),2])
						EndIf
					EndIf

					//Atualiza UF de Destino apos a inicializacao das rotinas fiscais
					If cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_ESTDES")) > 0
						If ProcH("F1_ESTDES") > 0 .AND. !Empty(aAutoCab[ProcH("F1_ESTDES"),2])
							MaFisAlt("NF_UFCDEST", aAutoCab[ProcH("F1_ESTDES"),2])
						EndIf
					EndIf

					//Atualiza UF de Origem apos a inicializacao das rotinas fiscais
					MaFisAlt("NF_UFORIGEM",cUfOrig)
				EndIf

				//ATEN«√O!! ATEN«√O!! ATEN«√O!! ATEN«√O!! ATEN«√O!! ATEN«√O!!
				//CAMPOS QUE RECRIAM ARRAY DA MAFIS: "NF_CODCLIFOR/NF_LOJA/NF_TIPONF/NF_OPERNF/NF_CLIFOR/NF_NATUREZA/NF_CLIDEST/NF_LOJDEST/NF_TPFRETE"

				If cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_UFORITR")) > 0 .And. SF1->(ColumnPos("F1_UFDESTR")) > 0
					If ProcH("F1_UFORITR") > 0 .And. !Empty(aAutoCab[ProcH("F1_UFORITR"),2])
						MaFisAlt("NF_UFORIGEM",aAutoCab[ProcH("F1_UFORITR"),2])
					Endif

					If ProcH("F1_UFDESTR") > 0 .And. !Empty(aAutoCab[ProcH("F1_UFDESTR"),2])
						MaFisAlt("NF_UFDEST",aAutoCab[ProcH("F1_UFDESTR"),2])
					Endif
				Endif

				//Preenche o tipo de complemento
				If cPaisLoc == "BRA" .And. cTipo == "C" .And. SF1->(ColumnPos("F1_TPCOMPL")) > 0 .And. ProcH("F1_TPCOMPL") > 0 .And. aAutoCab[ProcH("F1_TPCOMPL"),2] $ "123" .And. !Empty(MaFisScan("NF_TPCOMPL",.F.))
					cTpCompl := aAutoCab[ProcH("F1_TPCOMPL"),2]
					MaFisAlt("NF_TPCOMPL", cTpCompl)
				EndIf

				//Atualiza Especie do documento apos a inicializacao das rotinas fiscais
				If(Type("cEspecie")<>"U" .And. cEspecie<>Nil)
					MaFisAlt("NF_ESPECIE",cEspecie)
				EndIf
			Else
				If ALTERA .and. cPaisLoc == "BRA" .and. ProcH("F1_CHVNFE") > 0
 					aVldBlock[66] := {||CheckSX3('F1_CHVNFE',aDanfe[13])}
					Aadd(aValidGet,{"aDanfe[13]",aAutoCab[ProcH("F1_CHVNFE"),2],"Eval(aVldBlock[66])",.F.})
					aNfeDanfe[13] := aAutoCab[ProcH("F1_CHVNFE"),2]
				Endif
				nOpc := 1
			EndIf
			If nOpc == 1 .Or. lWhenGet
				//Verifica o preenchimento do campo D1_ITEM
				cItem := StrZero(1,Len(SD1->D1_ITEM))
				For nX := 1 To Len(aAutoItens)
					nY := aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_ITEM"})
					If nY == 0
						aSize(aAutoItens[nX],Len(aAutoItens[nX])+1)
						For nLoop := Len(aAutoItens[nX]) To 2 STEP -1
							aAutoItens[nX][nLoop]	:=	aAutoItens[nX][nLoop-1]
						Next nLoop
						aAutoItens[nX][1] := {"D1_ITEM", cItem, Nil}
					EndIf
					cItem := Soma1(cItem)

					// Verifica notas de remessa de entrega futura.
					nY := aScan(aAutoItens[nX], {|x| AllTrim(x[1]) == "AUT_ENTFUT"})
					If nY > 0
						aSize(aCompFutur, Len(aAutoItens))
						aCompFutur[nX] := aAutoItens[nX, nY, 2]
					EndIf

				Next nX
				If !Empty( ProcH( "E2_NATUREZ" )) 
					cNatureza := aAutoCab[ProcH("E2_NATUREZ"),2]
					lret := Eval(aVldBlock[10])					
				EndIf
				If l103Class
					If ProcH("F1_COND") > 0
						cCondicao := aAutoCab[ProcH("F1_COND"),2]
					Endif	
					If ProcH("F1_TPFRETE") > 0
						aVldBlock[30] := {||CheckSX3('F1_TPFRETE',aDanfe[14])}
						Aadd(aValidGet,{"aDanfe[14]",aAutoCab[ProcH("F1_TPFRETE"),2],"Eval(aVldBlock[30])",.F.})
						aNfeDanfe[14] := aAutoCab[ProcH("F1_TPFRETE"),2]
					Endif
					If ProcH("F1_TPCTE") > 0
						aVldBlock[34] := {||CheckSX3('F1_TPCTE',aDanfe[18])}
						Aadd(aValidGet,{"aDanfe[18]",aAutoCab[ProcH("F1_TPCTE"),2],"Eval(aVldBlock[34])",.F.})
						aNfeDanfe[18] := aAutoCab[ProcH("F1_TPCTE"),2]
					Endif	
				EndIf
				If SuperGetMv("MV_INTPMS",,"N") == "S"
					If SuperGetMv("MV_PMSIPC",,2) == 1 //Se utiliza amarracao automatica dos itens da NFE com o Projeto
						For nX := 1 To Len(aAutoItens)
							PMS103IPC(Val(aAutoItens[nX][aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_ITEM"})][2]))
						Next nX
					Else
						If Empty(aAutoAFN)
							lRatAFN := .F.
						EndIf
						For nX := 1 To Len(aAutoAFN)
							If lRatAFN
								lRatAFN := !Empty(aAutoAFN[nX])
							EndIf
						Next nX
						If lRatAFN
							For nX := 1 To Len(aAutoItens)
								aRatAFN := aClone(aAutoAFN)
								If !PmsVldAFN(Val(aAutoItens[nX][aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_ITEM"})][2]))//Se as validacoes estiverem ok, continua o processo de amarracao
									aRatAFN := {}
									Exit
								EndIf
							Next nX
						EndIf
					EndIf
				EndIf

				// Tratamento para valores de aposentadoria especial recebidos via rotina automatica
				If ChkFile("DHP") .And. Len(aAposEsp) > 0
					A103Aposen(@aHeadDHP,@aColsDHP,.T.,.T.,aAposEsp)
				EndIf
				
				// Tratamento para valores de natureza de rendimento recebidos via rotina automatica
				If ChkFile("DHR") .And. Len(aNatRend) > 0
					A103NatRen(@aHeadDHR,@aColsDHR,.T.,.T.,aNatRend)
				EndIf

				If l103GAuto
					If !MsGetDAuto(aAutoItens,"A103LinOk",{|| A103TudOk()},aAutoCab,aRotina[nOpcx][4])
						If lWhenGet
							If !IsBlind()
								MostraErro()
							Else
								Aviso(STR0119,STR0157,{STR0148}, 2)
							EndIf
							lProcGet := .F.
						EndIf
						nOpc := 0
					EndIf
				Else	// l103GAuto = .F. -> Chamada via Totvs Colaboracao apenas para atualizar impostos, nao e necessario passar por A103LinOk/A103TudOk
					If !MsGetDAuto(aAutoItens,,,aAutoCab,aRotina[nOpcx][4])
						nOpc := 0
					EndIf
				EndIf
				
				If l103Auto .And. l103Exclui .And. ExistBlock("MT103EXC")
					lVldExc := ExecBlock("MT103EXC",.F.,.F.)
					If ValType(lVldExc) == "L"
						lRet := lVldExc
						If !lVldExc
							nOpc := 0
						Endif
					EndIf
				Endif

				//Se o item estiver amarrado a um PC com rateio, copia rateio
				If l103Auto
					nPosPC		:= GetPosSD1("D1_PEDIDO")
					nPosItPC  	:= GetPosSD1("D1_ITEMPC")
					nPosRat  	:= GetPosSD1("D1_RATEIO")
					nPosItNF	:= GetPosSD1("D1_ITEM")
					If nPosPC > 0 .And. nPosItPc > 0 .And. nPosRat > 0
						If Empty(aHeadSDE)
							dbSelectArea("SX3")
							dbSetOrder(1)
							MsSeek("SDE")
							While !EOF() .And. (SX3->X3_ARQUIVO == "SDE")
								IF X3USO(SX3->X3_USADO) .AND. cNivel >= SX3->X3_NIVEL .And. !"DE_CUSTO"$SX3->X3_CAMPO
									AADD(aHeadSDE,{ TRIM(x3Titulo()),SX3->X3_CAMPO,SX3->X3_PICTURE,SX3->X3_TAMANHO,SX3->X3_DECIMAL,SX3->X3_VALID,SX3->X3_USADO,SX3->X3_TIPO,SX3->X3_F3,SX3->X3_CONTEXT } )
								EndIf
								dbSelectArea("SX3")
								dbSkip()
							EndDo
							ADHeadRec("SDE",aHeadSDE)
						EndIf
						dbSelectArea("SC7") 
						SC7->(dbSetOrder(14))  
						For nX := 1 To Len(aCols)
							If !Empty(aCols[nX][nPosPC]) .And. !Empty(aCols[nX][nPosItPC]) .And. aCols[nX][nPosRat] == "1"
								If SC7->(MsSeek(cFilialC7+aCols[nX][nPosPC]+aCols[nX][nPosItPC]))
									RatPed2NF(aHeadSDE,@aColsSDE,aCols[nX][nPosItNF],SC7->(RecNo()))
								EndIf
							ElseIf !Empty(aRateioCC) .And. aCols[nX][nPosRat] == "1"
								RatPed2NF(aHeadSDE,@aColsSDE,aCols[nX][nPosItNF],0,aRateioCC)
							EndIf
						Next nX
						
						If lMT103RCC
							aColsSDE := ExecBlock( "MT103RCC", .F., .F.,{aHeadSDE,aColsSDE})
						EndIf

					EndIf
				EndIf

				// Verifica se transf. filiais para retornar Base IPI
				For nX := 1 To Len(aAutoItens)
					nY := aScan(aAutoItens[nX], {|x| AllTrim(x[1]) == "D1_TES"})
					If nY == 0
						nY := aScan(aAutoItens[nX], {|x| AllTrim(x[1]) == "D1_TESACLA"})
					EndIf
					If nY > 0
						A103TrfIPI(aAutoItens[nX, nY, 2], nX)
					EndIf
				Next nX

				For nX := 1 to Len(aAutoImp)
					If Len(aAutoImp[nX]) > 2
						MaFisAlt(aAutoImp[nX][1],aAutoImp[nX][2], aAutoImp[nX][3],,,,,Iif(Len(aAutoImp[nX]) >= 4, aAutoImp[nX][4],Nil))
					Else
						MaFisAlt(aAutoImp[nX][1],aAutoImp[nX][2])
					EndIf
				Next nX
				For nX := 1 to Len(aAutoImp)
					If SubStr(aAutoImp[nX][1],1,2) == "LF" .And. MaFisFound("IT",aAutoImp[nX][3])
						MaFisLoad(aAutoImp[nX][1],aAutoImp[nX][2],aAutoImp[nX][3])
					EndIf
				Next nX
				If !cTipo$"PI" .and. ProcH("F1_DESCONT") > 0
					MaFisAlt("NF_DESCONTO",aAutoCab[ProcH("F1_DESCONT"),2])
				EndIf
				If ProcH("F1_DESPESA") > 0
					MaFisAlt("NF_DESPESA",aAutoCab[ProcH("F1_DESPESA"),2])
				EndIf
				If ProcH("F1_SEGURO") > 0
					MaFisAlt("NF_SEGURO",aAutoCab[ProcH("F1_SEGURO"),2])
				EndIf
				If ProcH("F1_FRETE") > 0
					MaFisAlt("NF_FRETE",aAutoCab[ProcH("F1_FRETE"),2])
				EndIf
				If ProcH("F1_BASEICM") > 0
					MaFisAlt("NF_BASEICM",aAutoCab[ProcH("F1_BASEICM"),2])
				EndIf
				If ProcH("F1_VALICM") > 0
					MaFisAlt("NF_VALICM",aAutoCab[ProcH("F1_VALICM"),2])
				EndIf
				If ProcH("F1_BASEIPI") > 0
					MaFisAlt("NF_BASEIPI",aAutoCab[ProcH("F1_BASEIPI"),2])
				EndIf
				If ProcH("F1_VALIPI") > 0
					MaFisAlt("NF_VALIPI",aAutoCab[ProcH("F1_VALIPI"),2])
				EndIf
				If ProcH("F1_BRICMS") > 0
					MaFisAlt("NF_BASESOL",aAutoCab[ProcH("F1_BRICMS"),2])
				EndIf
				If ProcH("F1_ICMSRET") > 0
					MaFisAlt("NF_VALSOL",aAutoCab[ProcH("F1_ICMSRET"),2])
				EndIf
				If ProcH("F1_RECISS") > 0
					MaFisAlt("NF_RECISS",aAutoCab[ProcH("F1_RECISS"),2])
				EndIf
				If !FwIsInCallStack("GFEA065In") .And. ProcH("F1_VALPEDG") > 0  
					MaFisAlt("NF_VALPEDG",aAutoCab[ProcH("F1_VALPEDG"),2])
				EndIf 

				// Tratamento para valores de aposentadoria especial recebidos via rotina automatica
				If nOpc == 1 .And. ChkFile("DHP") .And. Len(aHeadDHP) > 0 .And. Len(aColsDHP) > 0
					A103AtuApos(aHeadDHP,aColsDHP)
				EndIf

				//Ajusta os dados de acordo com a nota fiscal original
				If lWhenGet
					Ascan(aAutoItens,{|X| !Empty( nPosRec := Ascan(  x, { |Y| Alltrim( y[1] ) == "D1RECNO"}))} )
					If nPosRec > 0
						For nX := 1 to Len(aAutoItens)
							nPosRec := Ascan(aAutoItens[nX], { |y| Alltrim( y[1] ) == "D1RECNO"})
							MaFisAlt("IT_RECORI",aAutoItens[nX,nPosRec,2],nX)
							MaFisAlt("NF_UFORIGEM",SF2->F2_EST)
						Next
						MaFisToCols(aHeader,aCols,Len(aCols),'MT100')
					Endif
				Endif

				If nOpc == 1 .Or. lWhenGet
					NfeFldFin(,l103Visual,aRecSE2,0,aRecSE1,@aHeadSE2,@aColsSE2,@aHeadSEV,@aColsSEV,@aFldCbAtu[6],NIL,@cModRetPIS,lPccBaixa,@lTxNeg,@cNatureza,@nTaxaMoeda,@aColTrbGen,@nColsSE2,@aParcTrGen,@cIdsTrGen)
					aColsNF:= aClone(aCols)  
					Eval(aFldCbAtu[6])
					If !l103Auto .Or. lWhenGet
						Eval(bRefresh,6,6)
					Endif

					IF l103Auto .And. lMT103FIN .And. !NfeTotFin(aHeadSE2,aColsSE2,.T.,,nColsSE2,aColTrbGen)
						nOpc := 0	
					Endif
				EndIf
			EndIf
			If lWhenGet
				l103Auto := .F.
			EndIf
		EndIf

		//Inicializa a gravacao dos lancamentos do SIGAPCO
		PcoIniLan("000054")

		If lDKD //Tem DKD, verifica se tem campos adicionais para serem apresentados
			lTabAuxD1 := A103DKD(l103Class,l103Visual) //MATA103COM
		Endif

		//Montagem da Tela da Nota fiscal de entrada
		If (!l103Auto .Or. lWhenGet) .And. lProcGet

			aSizeAut	:= MsAdvSize(,.F.,400)
			aInfo := { aSizeAut[ 1 ], aSizeAut[ 2 ], aSizeAut[ 3 ], aSizeAut[ 4 ], 3, 3 }

			aPosGet := MsObjGetPos(aSizeAut[3]-aSizeAut[1],310,;
				{If(cPaisLoc<>"PTG",If(lSubSerie,{8,30,72,92,130,150,180,200,235,250,275,295},{8,35,75,100,140,165,194,220,260,280}),{8,35,78,100,140,160,200,230,250,270}),;
				If( l103Visual .Or. l103Class .Or. !lConsMedic,{8,35,75,100,nPosGetLoja,194,220,260,280},{8,35,75,108,135,160,190,220,244,265} ) ,;
				{5,70,160,205,295},;
				{6,34,200,215},;
				{6,34,75,103,148,164,230,253},;
				{6,34,200,218,280},;
				{11,50,150,190},;
				{273,130,190,293,205},;
				{005,025,065,085,125,145,185,205,250,275},;
				{11,35,80,110,165,190},;
				{3,35,95,150,205,255,170,230,265,;
				55,115,155,217,185,245,280,167,222,272},;
				{3, 4}}) // 12 - Folder InformaÁıes Adicionais

			DEFINE MSDIALOG oDlg FROM aSizeAut[7],0 TO aSizeAut[6],aSizeAut[5] TITLE cTituloDlg Of oMainWnd PIXEL //"Documento de Entrada"

			oSize := FwDefSize():New(.T.,,,oDlg)

			oSize:AddObject('HEADER',100,40,.T.,.F.)
			oSize:AddObject('GRID'  ,100,10,.T.,.T.)
			oSize:AddObject('FOOT'  ,100,90,.T.,.F.)

			oSize:aMargins 	:= { 3, 3, 3, 3 }
			oSize:Process()

			aAdd(aPosObj,{oSize:GetDimension('HEADER', 'LININI'),oSize:GetDimension('HEADER', 'COLINI'),oSize:GetDimension('HEADER', 'LINEND'),oSize:GetDimension('HEADER', 'COLEND')})
			aAdd(aPosObj,{oSize:GetDimension('GRID'  , 'LININI'),oSize:GetDimension('GRID'  , 'COLINI'),oSize:GetDimension('GRID'  , 'LINEND'),oSize:GetDimension('GRID'  , 'COLEND')})
			aAdd(aPosObj,{oSize:GetDimension('FOOT'  , 'LININI'),oSize:GetDimension('FOOT'  , 'COLINI'),oSize:GetDimension('FOOT'  , 'LINEND'),oSize:GetDimension('FOOT'  , 'COLEND')})

			//Objeto criado para receber o foco quando pressionado o botao confirma da dialog. Usado para identificar quando foi pressionado o botao
			//confirma, atraves do parametro passado ao lostfocus
			@ 100000,100000 MSGET oFoco103 VAR cVarFoco SIZE 12,09 PIXEL OF oDlg
			oFoco103:Cargo := {.T.,.T.}
			oFoco103:Disable()
			If cPaisLoc == "BRA"
				If (SF1->F1_FIMP$'ST'.And. SF1->F1_STATUS='C')
					NfeCabDoc(oDlg,{aPosGet[1],aPosGet[2],aPosObj[1]},@bCabOk,l103Class.Or.l103Visual,NIL,@cUfOrig,.F.,,@nCombo,@oCombo,@cCodRet,@oCodRet,@lNfMedic,@aCodR,@cRecIss,@cNatureza,,aNFEletr,aNfeDanfe,aInfAdic)
				Else
					NfeCabDoc(oDlg,{aPosGet[1],aPosGet[2],aPosObj[1]},@bCabOk,l103Class.Or.l103Visual,NIL,@cUfOrig,l103Class,,@nCombo,@oCombo,@cCodRet,@oCodRet,@lNfMedic,@aCodR,@cRecIss,@cNatureza,,aNFEletr,aNfeDanfe,aInfAdic)
				EndIf
			Else
				NfeCabDoc(oDlg,{aPosGet[1],aPosGet[2],aPosObj[1]},@bCabOk,l103Class.Or.l103Visual,NIL,@cUfOrig,l103Class,,@nCombo,@oCombo,@cCodRet,@oCodRet,@lNfMedic,@aCodR,@cRecIss,@cNatureza,,aNFEletr,aNfeDanfe,aInfAdic)
			EndIf

			//Integracao com SIGAMNT - NG Informatica
			nPORDEM := GetPosSD1("D1_ORDEM")
			If SuperGetMV("MV_NGMNTNO",.F.,"2") == "1" .And. !Empty(nPORDEM)
				STJ->(dbSetOrder(1))
				SC7->(dbSetOrder(19))
				SC1->(dbSetOrder(1))

				For nG := 1 To Len(aCols)
					//Se a Ordem de Servico nao estiver definida e a Ordem de Producao estiver preenchida, recebe a O.S. dela caso seja valida
					If Empty(aCols[nG,nPORDEM]) .And. "OS001" $ aCols[nG,GetPosSD1("D1_OP")]
						If STJ->(dbSeek(xFilial("STJ")+SubStr(aCols[nG,GetPosSD1("D1_OP")],1,TamSX3("TJ_ORDEM")[1])))
							aCols[nG,nPORDEM] := STJ->TJ_ORDEM
						ElseIf 	SC7->(dbSeek(xFilial("SC7")+aCols[nG,GetPosSD1("D1_COD")]+aCols[nG,GetPosSD1("D1_PEDIDO")]+aCols[nG,GetPosSD1("D1_ITEMPC")])) .And. ;
								SC1->(dbSeek(xFilial("SC1")+SC7->C7_NUMSC)) .And. ;
							 	STJ->(dbSeek(xFilial("STJ")+SubStr(SC1->C1_OP,1,At("OS",SC1->C1_OP)-1)))
							aCols[nG,nPORDEM] := SubStr(SC1->C1_OP,1,At("OS",SC1->C1_OP)-1)
						EndIf
					EndIf
				Next nG
			EndIf

			//Ponto de entrada para bloquear os campos do aCols na Classificacao e definir quais poderao ser alterados
			If l103Class .And. lMT103BCLA
				aMT103BCLA := ExecBlock("MT103BCLA",.F.,.F.)
				If ValType(aMT103BCLA) == "A"
					lRetBCla := .T.
				EndIf
			EndIf

			If !lDKD .Or. (lDKD .And. !lTabAuxD1)
				oGetDados := MSGetDados():New(aPosObj[2,1],aPosObj[2,2],aPosObj[2,3],aPosObj[2,4],nOpcx,'A103LinOk','A103TudOk','+D1_ITEM',!l103Visual,If(lRetBCla,aMT103BCLA,),,,IIf(l103Class,Len(aCols), GetNewPar("MV_COMLMAX", 9999)),"A103PosFld",,,IIf(l103Class,'AllwaysFalse()',"NfeDelItem"))
			Else 
				oGetDados := MSGetDados():New(aPosObj[2,1],aPosObj[2,2],aPosObj[2,3]-50,aPosObj[2,4],nOpcx,'A103LinOk','A103TudOk','+D1_ITEM',!l103Visual,If(lRetBCla,aMT103BCLA,),,,IIf(l103Class,Len(aCols), GetNewPar("MV_COMLMAX", 9999)),"A103PosFld",,,IIf(l103Class,'AllwaysFalse()',"NfeDelItem"))

				oGetDKD		:= MsNewGetDados():New(aPosObj[2,3]-50,aPosObj[2,2],aPosObj[2,3],aPosObj[2,4],Iif(nOpcx == 2,0,GD_UPDATE+GD_INSERT+GD_DELETE),/*"a103xLOk"*/"",/*"a103xLOk"*/"","+DKD_ITEM",aAltDKD,/*freeze*/,1,/*fieldok*/,/*superdel*/,/*"LancDel("+cVisual+")*/"",oDlg,aHeadDKD,aColsDKD)
				If l103Class .Or. (Type("aAutoDKD") == "A" .And. Len(aAutoDKD) > 0) .Or. l103Visual
					A103DKDATU(1) 
				Endif 
			Endif 

			oGetDados:oBrowse:bGotFocus	:= bCabOk
			oGetDados:oBrowse:bChange := {|| IIf(lDivImp, A103PosFld(), .T.), IIf(lTrbGen, MaFisLinTG(oFisTrbGen,oGetDados:oBrowse:nAt) ,.T.) , ;
											 Iif(lDKD .And. lTabAuxD1,A103DKDATU(),.T.) }

			//Valida TES de Entrada Padrao do Produto na Classificacao de NF
			If l103Class
				nPosTes := GetPosSD1("D1_TES" )
				If !Empty(aCols[n][nPosTes])
 					SF4->(dbSetOrder(1))
					If SF4->(MsSeek(xFilial("SF4")+RetFldProd(SB1->B1_COD,"B1_TE")))
						If !RegistroOk("SF4",.F.)
							Aviso("A103NTES",STR0391+CHR(10)+STR0392+RetFldProd(SB1->B1_COD,"B1_TE"),{STR0163})
							aCols[n][nPosTes] := ""
			   			Endif
					EndIf
				Endif
				//Valida itens da nota original na classificaÁ„o da nota de devoluÁ„o
				If cTipo $ "D"
					A103VLDITO()
				EndIf
			Endif

			//verificacao SIGAPLS
			if lPLSMT103
				PLSMT103(1, aHeader, aCols)
			endIf

			//Apenas ira montar o folder de Nota Fiscal Eletronica se os campos existirem
			If cPaisLoc == "BRA"
				Aadd(aTitles,STR0255) // "Nota Fiscal EletrÙnica"
				aAdd(aFldCBAtu,Nil)
				nNFe 	:= 	Len(aTitles)
				aAdd(aTitles,STR0280)	//"LanÁamentos da ApuraÁ„o de ICMS"
				aAdd(aFldCBAtu,Nil)
				nLancAp	:=	Len(aTitles)
			EndIf

			//Habilita o folder de conferencia fisica se necessario
			If cPaisLoc == "BRA"
				If l103Visual .AND. !l103Exclui .AND. !Empty(SF1->F1_STATUS) .And. ( ;
				SA2->A2_CONFFIS <> "3" .And. ;// Diferente de '3 - nao utiliza'
				(((SA2->A2_CONFFIS == "0" .And. cMVTPCONFF == "2") .Or. ;
				   SA2->A2_CONFFIS == "2") .And. cMVCONFFIS == "S") .Or.;
				   (cTipo == "B" .And. cMVCONFFIS == "S" .And. cMVTPCONFF == "2"))
					aadd(aTitles,STR0347) // "Conferencia Fisica"
					nConfNF := Len(aTitles)
					aAdd(aFldCBAtu,Nil)
				EndIf
			EndIf
			
			//Apenas ira montar o folder de Informacoes Diversas se os campos existirem
			If cPaisLoc == "BRA"
				Aadd(aTitles,STR0348) // "InformaÁıes DANFE"
				nInfDiv := 	Len(aTitles)
				aAdd(aFldCBAtu,Nil)
			EndIf

			//Apenas ira montar o folder de Informacoes Diversas se os campos existirem
			If cPaisLoc = "BRA" .And. lISSxMun
				Aadd(aTitles,STR0395) // "ApuraÁ„o ISS/INSS"
				aFldCBAtu	:= Array(Len(aTitles))
				nInfISS := 	Len(aTitles)
				aAdd(aFldCBAtu,Nil)
			EndIf

			If Len(aInfAdic) > 0
				aAdd(aTitles, STR0407) //"InformaÁıes Adicionais"
				nInfAdic := 	Len(aTitles)
				aAdd(aFldCBAtu,Nil)
			EndIf

			If lDivImp .And. !l103Inclui
				aAdd(aTitles, STR0497)
				nDivImp	:= Len(aTitles)
				aAdd(aFldCBAtu,Nil)
			Endif

			If lTrbGen
				aAdd(aTitles, STR0517) // "Tributos Genericos - Por Item"
				nTrbGen	:= Len(aTitles)
				Aadd(aFldCBAtu,nil) 
			EndIf

			oFolder := TFolder():New(aPosObj[3,1],aPosObj[3,2],aTitles,aPages,oDlg,,,, .T., .F.,aPosObj[3,4]-aPosObj[3,2],aPosObj[3,3]-aPosObj[3,1],)
			oFolder:bSetOption := {|nDst| NfeFldChg(nDst,oFolder:nOption,oFolder,aFldCBAtu)}
			bRefresh := {|nX| NfeFldChg(nX,oFolder:nOption,oFolder,aFldCBAtu)}
			
			//Folder dos Totalizadores
			oFolder:aDialogs[1]:oFont := oDlg:oFont
			NfeFldTot(oFolder:aDialogs[1],a103Var,aPosGet[3],@aFldCBAtu[1])

			//Folder dos Fornecedores
			oFolder:aDialogs[2]:oFont := oDlg:oFont
			NfeFldFor(oFolder:aDialogs[2],aInfForn,{aPosGet[4],aPosGet[5],aPosGet[6]},@aFldCBAtu[2])

			If !lGspInUseM
				//Folder das Despesas acessorias e descontos
				oFolder:aDialogs[3]:oFont := oDlg:oFont
			 	If cPaisLoc == "BRA"
			 	If (SF1->F1_FIMP$'ST'.And. SF1->F1_STATUS='C' .And. l103Class) //Tratamento para bloqueio de alteracoes na classificacao de uma nota bloqueada e ja transmitida.
			 		l103Visual := .T.
			 		NfeFldDsp(oFolder:aDialogs[3],a103Var,{aPosGet[7],aPosGet[8]},@aFldCBAtu[3])
			 		l103Visual := .F.
			 	Else
					NfeFldDsp(oFolder:aDialogs[3],a103Var,{aPosGet[7],aPosGet[8]},@aFldCBAtu[3])
			 	EndIf
			 	Else
					NfeFldDsp(oFolder:aDialogs[3],a103Var,{aPosGet[7],aPosGet[8]},@aFldCBAtu[3])
			  	EndIf
			  	IF l103Class
			  		aAreaD1 := SD1->(getArea())
			  		dbSelectArea("SD1")
					SD1->(dbSetOrder(1))
					SD1->(dbGoTop())
					SD1->(DbSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA))  //D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_COD+D1_ITEM
					
					nTmpN := n
					n:=0
					nPosTES := GetPosSD1('D1_TES')
					While !Eof() .And. SD1->D1_FILIAL+SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA ==;
									   SF1->F1_FILIAL+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA 
						n++		
						If lPropFret .And. !Empty(aCols[n,nPosTES]) .And. SF4->(MsSeek(xFilial('SF4')+aCols[n,nPosTES])) .And. !(SF4->F4_AGREG $ 'B|C') .And. SF1->F1_STATUS <> "C"
							A103Desp(lClassOrd)
						Endif	
				  		SD1->(dbSkip())
			  		EndDo
			  		restArea(aAreaD1)
			  		n  := nTmpN
			  	Endif	
				
				//Folder dos Livros Fiscais
				oFolder:aDialogs[4]:oFont := oDlg:oFont
				oLivro := MaFisBrwLivro(oFolder:aDialogs[4],{5,4,( aPosObj[3,4]-aPosObj[3,2] ) - 10,53},.T.,IIf(!l103Class,aRecSF3,Nil), IIf(!lWhenGet , IIf( l103Class , .T. , l103Visual ) , .F. ) )
				aFldCBAtu[4] := {|| oLivro:Refresh()}
			Endif

			//Folder dos Impostos
			oFolder:aDialogs[5]:oFont := oDlg:oFont

			//Folder do Financeiro
			oFolder:aDialogs[6]:oFont := oDlg:oFont
			NfeFldFin(oFolder:aDialogs[6],l103Visual,aRecSE2,( aPosObj[3,4]-aPosObj[3,2] ) - 101,aRecSe1,@aHeadSE2,@aColsSE2,@aHeadSEV,@aColsSEV,@aFldCbAtu[6],NIL,@cModRetPIS,lPccBaixa,@lTxNeg,@cNatureza,@nTaxaMoeda,@aColTrbGen,@nColsSE2,@aParcTrGen,@cIdsTrGen)

			If l103Visual .And. Empty(SF1->F1_RECBMTO)
				oFisRod	:=	A103Rodape(oFolder:aDialogs[5])
			ElseIf (cPaisLoc == "BRA" .And. SF1->F1_FIMP$'ST'.And. SF1->F1_STATUS='C' .And. l103Class) 				 //Tratamento para bloqueio de alteracoes na classificacao de uma nota bloqueada e ja transmitida.
				l103Visual := .T.
				oFisRod	:=	MaFisRodape(nTpRodape,oFolder:aDialogs[5],,{5,4,( aPosObj[3,4]-aPosObj[3,2] )-10,53},@bIPRefresh,l103Visual,@cFornIss,@cLojaIss,aRecSE2,@cDirf,@cCodRet,@oCodRet,@nCombo,@oCombo,@dVencIss,@aCodR,@cRecIss,@oRecIss,,@cDescri)
			Else
				oFisRod	:=	MaFisRodape(nTpRodape,oFolder:aDialogs[5],,{5,4,( aPosObj[3,4]-aPosObj[3,2] )-10,53},@bIPRefresh,l103Visual,@cFornIss,@cLojaIss,aRecSE2,@cDirf,@cCodRet,@oCodRet,@nCombo,@oCombo,@dVencIss,@aCodR,@cRecIss,@oRecIss,,@cDescri)
			EndIf
		  		
			//Folder dos historicos do Documento de entrada
			If l103Visual .Or. l103Class
				oFolder:aDialogs[7]:oFont := oDlg:oFont
				@ 05,04 LISTBOX oHistor VAR cHistor ITEMS aHistor PIXEL SIZE ( aPosObj[3,4]-aPosObj[3,2] )-10,53 Of oFolder:aDialogs[7]
				Eval(bRefresh,oFolder:nOption)
			EndIf

			//Ponto de Entrada utilizado na classificaÁ„o da nota para alterar Combobox
			//da aba Impostos que informa se gera DIRF e os cÛdigos de retencao
			If l103Class .And. ExistBlock("MT103DRF")
				aDirfRt := ExecBlock("MT103DRF",.F.,.F.,{nCombo,cCodRet,@oCombo,@oCodRet})
				if len(aDirfRt) > 0
					for a:=1 to len(aDirfRt)
						nCombo  := aDirfRt[a][2]
						cCodRet := ""
						if nCombo = 1
							cCodRet := aDirfRt[a][3]
						endif
					    If !Empty(cCodRet)
							If aScan(aCodR,{|aX| aX[4]==aDirfRt[a][1]})==0
							   aAdd( aCodR,{99, cCodRet,1,aDirfRt[a][1]})
							Else
							   aCodR[aScan(aCodR, {|aX| aX[4]==aDirfRt[a][1]})][2] := cCodRet
							EndIf
						EndIf
					next
				else
					nCombo  := Iif(aDirfRt[1][2] > 2, 2, aDirfRt[1][2])
					cCodRet := aDirfRt[1][3]
					If !Empty( cCodRet )
						If aScan( aCodR, {|aX| aX[4]=="IRR"})==0
							aAdd( aCodR, {99, cCodRet, 1, "IRR"} )
						Else
							aCodR[aScan( aCodR, {|aX| aX[4]=="IRR"})][2] :=	cCodRet
						EndIf
					EndIf
				Endif
				If ValType( oCombo ) == "O"
					oCombo:Refresh()
				Endif
				If ValType( oCodRet ) == "O"
					oCodRet:Refresh()
				Endif
				nCombo  := 2
				cCodRet := "    "

			Endif

			If SED->ED_CALCIRF == "N" .And. !Empty(cA100For)
				If ValType( oCombo ) == "O"
					nCombo  := 2
					oCombo:Refresh()
				Endif
				If ValType( oCodRet ) == "O"
					cCodRet := "    "						
					oCodRet:Refresh()
				Endif										
			EndIf			

			//Folder com os dados da Nota Fiscal Eletronica
			If cPaisLoc == "BRA"
				oFolder:aDialogs[nNFe]:oFont := oDlg:oFont
				NfeFldNfe(oFolder:aDialogs[nNFe],@aNFEletr,{aPosGet[10],aPosGet[8]},@aFldCBAtu[3])

				If nLancAp>0
					oFolder:aDialogs[nLancAp]:oFont := oDlg:oFont
					If  FindFunction("a017xLAICMS")
						oLancCDV := a017xLAICMS(oFolder:aDialogs[nLancAp],{5,4,( aPosObj[3,4]-aPosObj[3,2] )-10,53},aHeadCDV,aColsCDV,l103Visual,(l103Inclui.Or.l103Class),"SD1")
					Endif
					oLancApICMS := a103xLAICMS(oFolder:aDialogs[nLancAp],{5,4,( aPosObj[3,4]-aPosObj[3,2] )-10,53},@aHeadCDA,@aColsCDA,l103Visual,(l103Inclui.Or.l103Class))					
					If lWhenGet
						Eval({||GetLanc()}) 
					EndIf
					If l103Class
						a103AjuICM()						
					EndIf
				EndIf
			EndIf

			//Folder de conferencia para os coletores
				If nConfNF > 0
				oFolder:aDialogs[nConfNF]:oFont := oDlg:oFont
				Do Case
				Case SF1->F1_STATCON $ "1 "
					cStatCon := STR0349 // "NF conferida"
				Case SF1->F1_STATCON == "0"
					cStatCon := STR0350 //"NF nao conferida"
				Case SF1->F1_STATCON == "2"
					cStatCon := STR0351 // "NF com divergencia"
				Case SF1->F1_STATCON == "3"
					cStatCon := STR0352 // "NF em conferencia"
				Case SF1->F1_STATCON == "4"
					cStatCon := "NF Clas. C/ Diver."
				EndCase
				nQtdConf := SF1->F1_QTDCONF
				@ 06 ,aPosGet[6,1] SAY STR0353 OF oFolder:aDialogs[nConfNF] PIXEL SIZE 49,09 // "Status"
				@ 05 ,aPosGet[6,2] MSGET oStatCon VAR Upper(cStatCon) COLOR CLR_RED OF oFolder:aDialogs[nConfNF] PIXEL SIZE 70,9 When .F.
				@ 25 ,aPosGet[6,1] SAY STR0354 OF oFolder:aDialogs[nConfNF] PIXEL SIZE 49,09 // "Conferentes"
				@ 24 ,aPosGet[6,2] MSGET oConf Var nQtdConf OF oFolder:aDialogs[nConfNF] PIXEL SIZE 70,09 When .F.
				@ 05 ,aPosGet[5,3] LISTBOX oList Fields HEADER "  ",STR0355,STR0356 SIZE 170, 48 OF oFolder:aDialogs[nConfNF] PIXEL // "Codigo","Quantidade Conferida"
				oList:BLDblclick := {||A103DetCon(oList,aListBox)}

				DEFINE TIMER oTimer INTERVAL 3000 ACTION (A103AtuCon(oList,aListBox,oEnable,oDisable,oConf,@nQtdConf,oStatCon,@cStatCon,,oTimer)) OF oDlg
				oTimer:Activate()

				@ 30 ,aPosGet[5,3]+180 BUTTON STR0357 SIZE 40 ,11  FONT oDlg:oFont ACTION (A103AtuCon(oList,aListBox,oEnable,oDisable,oConf,@nQtdConf,oStatCon,@cStatCon,.T.,oTimer)) OF oFolder:aDialogs[nConfNF] PIXEL When SF1->F1_STATCON == '2' .And. !lClaNfCfDv // "Recontagem"
				@ 42 ,aPosGet[5,3]+180 BUTTON STR0358 SIZE 40 ,11  FONT oDlg:oFont ACTION (A103DetCon(oList,aListBox)) OF oFolder:aDialogs[nConfNF] PIXEL // "Detalhes"

				A103AtuCon(oList,aListBox,oEnable,oDisable)
			Endif

			//Folder com Informacoes Diversas
			If cPaisLoc == "BRA"
				oFolder:aDialogs[nInfDiv]:oFont := oDlg:oFont
				NfeFldDiv(oFolder:aDialogs[nInfDiv],{aPosGet[9]})
			EndIf

			//Folder com Informacoes ISS
			If cPaisLoc == "BRA" .And. lISSxMun
				oFolder:aDialogs[nInfISS]:oFont := oDlg:oFont
				ISSFldDiv(oFolder:aDialogs[nInfISS],{aPosGet[11]},@aObjetos,@aInfISS,@aFldCBAtu,nInfISS)
				If l103Visual
					Eval(bRefresh)
				EndIf
			EndIf

			//Folder Informacoes Adicionais do Documeno
			If Len(aInfAdic) > 0
				oFolder:aDialogs[nInfAdic]:oFont := oDlg:oFont
				NfeFldAdic(oFolder:aDialogs[nInfAdic],{aPosGet[12]}, @aInfAdic, @oDescMun, @cDescMun, l103Visual,,@aFldCBAtu[10])
			EndIf
			
			IF l103Visual 
				aAreaD1 := SD1->(getArea())
				dbSelectArea("SD1")
				SD1->(dbSetOrder(1))
				SD1->(MsSeek(xFilial("SD1")+cNFiscal+cSerie+cA100For+cLoja))
			EndIf
			
			//-- Folder de DivergÍncias de Impostos
			If  lDivImp .And. !l103Inclui
				oFolder:aDialogs[nDivImp]:oFont := oDlg:oFont

				oListDvIm := COLListDiv(oFolder:aDialogs[nDivImp],{5,4,( aPosObj[3,3]-aPosObj[3,2] ) - 10,53},oGetDados)
			EndIf

			// -- Folder de Tributos Genericos
			If lTrbGen
				oFolder:aDialogs[nTrbGen]:oFont := oDlg:oFont 
				oFisTrbGen := MaFisBrwTG(oFolder:aDialogs[nTrbGen],{5,4,( aPosObj[3,4]-aPosObj[3,2] ) - 10,65}, l103Visual)
				aFldCBAtu[nTrbGen] := {|| Iif(lTrbGen , MaFisLinTG(oFisTrbGen,oGetDados:oBrowse:nAt) , .T.) }				
			EndIf

			If lWhenGet .Or. l103Class
				Eval(bRefresh,oFolder:nOption)
			Endif

			//Transfere o foco para a getdados - nao retirar
			oFoco103:bGotFocus := { || oGetDados:oBrowse:SetFocus() }

			aButControl := {{ |x,y| aColsSEV := aClone( x ), aHeadSEV := aClone( y ) }, aColsSev,aHeadSEV }

			If !l103Inclui .And. FindFunction("gatilhadkd") 
				gatilhadkd()  
			Endif

		    // AtenÁ„o: Conserve a ordem de execuÁ„o dos ExecBlocks abaixo a fim de facilitar a compreenÁ„o
            // e manutenÁıes futuras....!
   			ACTIVATE MSDIALOG oDlg ON INIT (IIf(lWhenGet,oGetDados:oBrowse:Refresh(),Nil),;
				A103Bar(oDlg,{|| oFoco103:Enable(),oFoco103:SetFocus(),oFoco103:Disable(),;
				IIf(((!l103Inclui.And.!l103Class).Or.( Eval(bRefresh,6)          .And. ;
				Iif(l103Inclui .Or. l103Class, A103ConsCTE(aNFeDanfe[18]), .T.) .And.;
				If(l103Inclui.Or.l103Class,NfeTotFin(aHeadSE2,aColsSE2,.T.,,nColsSE2,aColTrbGen),.T.) .And. ;
				oGetDados:TudoOk()))											   .And. ;
				(IIf (l103Class .Or. l103Inclui, NfeCabOk(l103Visual,,,,,,,,,,,.T.),.T.)) .And. ;
				A103VldEXC(l103Exclui,cPrefixo)									   		  .And. ;
				A103CodR(aCodR)													          .And. ;
				A103VldDanfe(aNFEDanfe,aNFEletr)								          .And. ;
				a103xLOk() .And. oFoco103:Cargo[1]    							   		  .And. ;
				NfeVldSEV(oFoco103:Cargo[2],aHeader,aCols,aHeadSEV,aColsSEV)  	   		  .And. ;
			    EVAL(bBlockSev2)												          .And. ;
				    IIf(( l103Inclui .or. l103Class ),A103ChamaHelp(),.T.)	              .And. ;
				A103VldGer( aNFEletr )                                                    .And. ;
				A103VldSusp(aHeader,aCols)										          .And. ;
				NfeNextDoc(@cNFiscal,@cSerie,l103Inclui,@cNumNfGFE) 			          .And. ;
				A103TmsVld(l103Exclui) 					   					   	          .And. ;
				A103MultOk( aMultas, aColsSE2, aHeadSE2 )  					   	          .And. ;
				IIF(ExistFunc("EA013PosValid"),EA013PosValid(oModelDCL,lDclNew),.T.)      .And. ;
				A103VlIGfe( l103Inclui,l103Class, .F., cNumNfGFE )						  .And. ;
				IIF(ExistFunc("MNTLoteDE"),MNTLoteDE(cSerie, l103Inclui, l103Exclui),.T.)      ,;
				(nOpc:=1,oDlg:End()),Eval({||nOpc:=0,oFoco103:Cargo[1] :=.T.}))},;
				{||FreeUsedcode(.T.),nOpc:=0,oDlg:End(),A103GrvCla(l103Class,aColsSE2,cNatureza)},IIf(l103Inclui.Or.l103Class,aButtons,aButVisual),aButControl))
		
		ElseIf EMPTY(cNFiscal)
		
			NfeNextDoc(@cNFiscal,@cSerie,l103Inclui,@cNumNfGFE)

		EndIf

		//Copia aHeader e aCols para uso externo
		If !Type("l103GAuto") == "U"
			If!l103GAuto .And. nOpc == 1
				If aImpVal <> NIL
					For nLoop := 1 to Len( aCols )
						//Conteudo, Campo, ReferÍncia Fiscal/Valor
						aAdd(aImpItem,{"TES"		,"D1_TES"		,aCols[nloop,GetPosSD1("D1_TES")]})
						aAdd(aImpItem,{"IPI"		,"D1_VALIPI"	,MaFisRet(nLoop,"IT_VALIPI")})
						aAdd(aImpItem,{"ICMS"		,"D1_VALICM"	,MaFisRet(nLoop,"IT_VALICM")})
						aAdd(aImpItem,{"ISS"		,"D1_VALISS"	,MaFisRet(nLoop,"IT_VALISS")})
						aAdd(aImpItem,{"PIS"		,"D1_VALIMP6"	,MaFisRet(nLoop,"IT_VALPS2")})
						aAdd(aImpItem,{"COFINS"		,"D1_VALIMP5"	,MaFisRet(nLoop,"IT_VALCF2")})
						aAdd(aImpItem,{"ICMS ST"	,"D1_ICMSRET"	,MaFisRet(nLoop,"IT_VALSOL")})

						aAdd(aImpItem,{"ALIQUOTA IPI"		,"D1_IPI"		,MaFisRet(nLoop,"IT_ALIQIPI")})
						aAdd(aImpItem,{"ALIQUOTA ICMS"		,"D1_PICM"		,MaFisRet(nLoop,"IT_ALIQICM")})
						aAdd(aImpItem,{"ALIQUOTA ISS"		,"D1_ALIQISS"	,MaFisRet(nLoop,"IT_ALIQISS")})
						aAdd(aImpItem,{"ALIQUOTA PIS"		,"D1_ALQIMP6"	,MaFisRet(nLoop,"IT_ALIQPS2")})
						aAdd(aImpItem,{"ALIQUOTA COFINS"	,"D1_ALQIMP5"	,MaFisRet(nLoop,"IT_ALIQCF2")})
						aAdd(aImpItem,{"ALIQUOTA ICMS ST"	,"D1_ALIQSOL"	,MaFisRet(nLoop,"IT_ALIQSOL")})
						aAdd(aImpVal, {aCols[nloop,GetPosSD1("D1_ITEM")],aImpItem})
					Next
				Endif
			EndIf
		EndIf

		If Type("l103GGFAut") == "L"
			If l103GGFAut
				A103GrvCla(l103Class,aColsSE2,cNatureza)
				nOpc := 0
			EndIf
		EndIf

		If nOpc == 1 .And. (l103Inclui.Or.l103Class.Or.l103Exclui)	.And. If(Type("l103GAuto") == "U" ,.T.,l103GAuto)

			If (ExistBlock("MT100AG"))
				ExecBlock("MT100AG",.F.,.F.)
			EndIf
			
			//Inicializa a gravacao atraves nas funcoes MATXFIS
			MaFisWrite(1)

			If A103Trava() .And. IIf(lIntegGFE .And. l103Exclui,ExclDocGFE(),.T.)
					
					// Gera tempor·rias antes da transaÁ„o para o processo de skip-lote
					If lIntWMS
						WmsAvalSF1("8")
					EndIf
					
					If lEstNfClass .And. cDelSDE == "3"  .And. (Len(aRecSDE) > 0)
						cDelSDE:=Str(Aviso(OemToAnsi(STR0236),STR0263,{STR0264,STR0265},2),1,0)
					EndIf

					// Valida retorno valido
					If !(cDelSDE $ "123")
						cDelSDE:="1"
					EndIf
					If !l103Auto
						SetKey(VK_F4,Nil)
						SetKey(VK_F5,Nil)
						SetKey(VK_F6,Nil)
						SetKey(VK_F7,Nil)
						SetKey(VK_F8,Nil)
						SetKey(VK_F9,Nil)
						SetKey(VK_F10,Nil)
						SetKey(VK_F11,Nil)
						SetKey(VK_F12,bKeyF12) 
					EndIf
					SetProxNum()//- carrega os ProxNum fora da transaÁ„o
					Begin Transaction
						If l103Exclui
							SD1->(dbSetOrder(1))
							SD1->(MsSeek(xFilial("SD1")+cNFiscal+cSerie+cA100For+cLoja))
							SDH->(dbSetOrder(1))
							If SDH->(MsSeek(xFilial("SDH")+SD1->D1_NUMSEQ))
								aRetInt := FWIntegDef("MATA103A",,,,"MATA103A")	//-- CoverageDocument

								If Valtype(aRetInt) == "A"
									If Len(aRetInt) == 2 
										If !aRetInt[1]
											If Empty(AllTrim(aRetInt[2]))
												cMsgRet := STR0458
											Else
												cMsgRet := AllTrim(aRetInt[2])
											Endif
											Aviso(STR0459,cMsgRet,{"Ok"},3)
											lRet := .F.
											DisarmTransaction()
										Endif
									Endif
								Endif
							Else
								aRetInt := FWIntegDef("MATA103",,,,"MATA103")	//-- InputDocument
								If Valtype(aRetInt) == "A"
									If Len(aRetInt) == 2
										If !aRetInt[1]
											If Empty(AllTrim(aRetInt[2]))
												cMsgRet := STR0458
											Else
												cMsgRet := AllTrim(aRetInt[2])
											Endif
											Aviso(STR0459,cMsgRet,{"Ok"},3)
											lRet := .F.
											DisarmTransaction()
										Endif
									Endif
								Endif

								aRetInt := FWIntegDef("MATA103B",,,,"MATA103B")	//-- Invoice
								If Valtype(aRetInt) == "A"
									If Len(aRetInt) == 2
										If !aRetInt[1]
											If Empty(AllTrim(aRetInt[2]))
												cMsgRet := STR0458
											Else
												cMsgRet := AllTrim(aRetInt[2])
											Endif
											Aviso(STR0459,cMsgRet,{"Ok"},3)
											lRet := .F.
											DisarmTransaction()
										Endif
									Endif
								Endif
							EndIf

							If lRet .And. SuperGetMV( 'MV_NGMNTES', .F., 'N' ) == 'S' .And. FindFunction( 'MNTINTSD1' ) .And. !MNTINTSD1( 5, 'MATA103' )
								lRet := .F.
								DisarmTransaction()
							EndIf

							If lRet
								cAlFR3 := getNextAlias()
								aRecPA := {}
	
								cQuery := ""
								cQuery += "SELECT	FR3.FR3_FILIAL "								+ CRLF
								cQuery += "		,FR3.FR3_CART"										+ CRLF
								cQuery += "		,FR3.FR3_FORNEC" 									+ CRLF
								cQuery += "		,FR3.FR3_LOJA"										+ CRLF
								cQuery += "		,FR3.FR3_PREFIX"									+ CRLF
								cQuery += "		,FR3.FR3_NUM" 										+ CRLF
								cQuery += "		,FR3.FR3_PARCEL" 									+ CRLF
								cQuery += "		,FR3.FR3_TIPO"										+ CRLF
								cQuery += "		,FR3.FR3_PEDIDO"									+ CRLF
								cQuery += "		,FR3.FR3_VALOR"										+ CRLF
								cQuery += "		,FR3.R_E_C_N_O_ AS RECNO"							+ CRLF
								cQuery += "FROM	" + retSqlname("FR3") + " FR3" 						+ CRLF
								cQuery += "WHERE	FR3.D_E_L_E_T_	= ' ' "							+ CRLF
								cQuery += "AND	FR3.FR3_FILIAL	= '" + xFilial('FR3') + "' "		+ CRLF
								cQuery += "AND	FR3.FR3_CART		= 'P' "							+ CRLF
								cQuery += "AND	FR3.FR3_DOC			= '" + SF1->F1_DOC + "' "			+ CRLF
								cQuery += "AND	FR3.FR3_SERIE		= '" + SF1->F1_SERIE + "' "		+ CRLF
								cQuery += "AND	FR3.FR3_FORNEC		= '" + SF1->F1_FORNECE + "' "   + CRLF
								cQuery += "AND	FR3.FR3_LOJA		= '" + SF1->F1_LOJA + "' "		+ CRLF
								cQuery += "AND	FR3.FR3_TIPO		IN( 'PA','NF') "
								If lAdtCompart
									cQuery += " AND ((FR3_FILORI = '"+cFilant+"') OR (FR3_FILORI = ' '))"
								EndIf
	
								cQuery := changeQuery(cQuery)
	
								If select(cAlFR3) > 0
									(cAlFR3)->(dbCloseArea())
								EndIf
	
								tcQuery cQuery New Alias((cAlFR3))
	
								dbSelectArea((cAlFR3))
								(cAlFR3)->(dbGoTop())
								aAreaE2 := SE2->(getArea())
								SE2->(dbSetOrder(1))
								dbSelectArea("FR3")
								aAreaR3 := FR3->(getArea())
								dbSelectArea("FIE")
								FIE->(dbSetOrder(Iif(lAdtCompart,5,3)))
								FIE->(dbGoTop())
								aAreaIE := FIE->(getArea())
								While((cAlFR3)->(!eof()))
									If SE2->(msSeek(xFilial('SE2') + (cAlFR3)->(FR3_PREFIX + FR3_NUM + FR3_PARCEL + FR3_TIPO + FR3_FORNEC + FR3_LOJA)))
										If((cAlFR3)->FR3_TIPO == PADR('PA',nFR3_TIPO))
											aadd(aRecPA,SE2->(recno()))
										EndIf
									EndIf
									FR3->(dbGoTo((cAlFR3)->RECNO))
									If FIE->(dbSeek(cFilFie + FR3->(FR3_CART+FR3_FORNEC+FR3_LOJA+FR3_PREFIX+FR3_NUM+FR3_PARCEL+FR3_TIPO+FR3_PEDIDO)))
										If(recLock("FIE",.F.))
											FIE->FIE_SALDO += FR3->FR3_VALOR
											FIE->(msUnLock())
										EndIf
									EndIf
									If(recLock("FR3",.F.))
										FR3->(dbDelete())
										FR3->(msUnLock())
									EndIf
									(cAlFR3)->(dbSkip())
								EndDo
							Endif
							
							If lRet
								//Carrega o pergunte da rotina de compensaÁ„o financeira
								Pergunte("AFI340",.F.)
							
								lContabiliza 	:= MV_PAR11 == 1
								lDigita			:= MV_PAR09 == 1
								
								restArea(aAreaE2)
								restArea(aAreaR3)
								restArea(aAreaIE)
								
								If(len(aRecPA) > 0)
									aEstorno := {XGetCP()}
									MaIntBxCP(2,{SE2->(recno())},,aRecPA,,{lContabiliza,lAglutina,lDigita,.F.,.F.,.F.},,aEstorno,,,dDataBase,)
								EndIf
	
								If select(cAlFR3) > 0
									(cAlFR3)->(dbCloseArea())
								EndIf
								Pergunte("MTA103",.F.)
							Endif
						EndIf
						
						If !lRet .Or. (FindFunction("CnNotaDev") .And. lUsaGCT .And. (l103Exclui .And. SF1->F1_TIPO == 'D' .And. !CnNotaDev(1,{SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA})))
							lRet := .F.
							DisarmTransaction()
						Elseif lRet
							a103Grava(	l103Exclui,lGeraLanc ,lDigita    ,lAglutina            ,aHeadSE2   ,;
										aColsSE2  ,aHeadSEV  ,aColsSEV   ,nRecSF1              ,aRecSD1    ,;
										aRecSE2   ,aRecSF3   ,aRecSC5    ,aHeadSDE             ,aColsSDE   ,;
										aRecSDE   ,.F.       ,.F.        ,                     ,aRatVei    ,;
										aRatFro   ,cFornIss  ,cLojaIss   ,A103TemBlq(l103Class), l103Class ,;
										cDirf     ,cCodRet   ,cModRetPIS ,nIndexSE2            ,lEstNfClass,;
										dVencIss  ,lTxNeg    ,aMultas    ,lRatLiq              ,lRatImp    ,;
										aNFEletr  ,cDelSDE   ,aCodR      ,cRecIss              ,cAliasTPZ  ,;
										aCtbInf   ,aNfeDanfe ,@lExcCmpAdt, @aDigEnd            ,@lCompAdt  ,;
										aPedAdt   ,aRecGerSE2,aInfAdic   ,a103Var              ,cCodRSef   ,;
										@aTitImp  , aHeadDHP , aColsDHP  ,aCompFutur           ,aParcTrGen ,;
										aHeadDHR  , aColsDHR , aHdSusDHR , aCoSusDHR		   ,cIdsTrGen )


							If !(l103Exclui .and. !lExcCmpAdt)
								a103GrvCDA(l103Exclui,"E",cEspecie,cFormul,cNFiscal,cSerie,cA100For,cLoja)
								If FindFunction("a017GrvCDV")
									a017GrvCDV(l103Exclui,"E",cEspecie,cFormul,cNFiscal,cSerie,cA100For,cLoja)
								Endif
								//≥ Atualiza dados dos complementos SPED automaticamente ≥
								If lMvAtuComp
									AtuComp(cNFiscal,SF1->F1_SERIE,cEspecie,cA100For,cLoja,"E",cTipo)
								EndIf
							Endif

							If lIntegGFE .And. ( l103Inclui .Or. l103Class ) .And. lProcGet .AND. SF1->F1_ORIGEM != 'GFEA065'
								lRetGFE := A103VlIGfe( l103Inclui,l103Class, .T. )
								If !lRetGFE
									lRet := .F.
									DisarmTransaction()
								Endif
							EndIf

							//Atualiza os dados do movimento na locaÁ„o de equipamentos
							If lRet .And. SF1->F1_TIPO == 'D'
								At800AtNFEnt( l103Exclui )
							EndIf
	
							If lRet .And. l103Inclui .Or. l103Class
								SD1->(dbSetOrder(1))
								SD1->(MsSeek(xFilial("SD1")+cNFiscal+cSerie+cA100For+cLoja))
								SDH->(dbSetOrder(1))
								If SDH->(MsSeek(xFilial("SDH")+SD1->D1_NUMSEQ))
									aRetInt := FWIntegDef("MATA103A",,,,"MATA103A")	//-- CoverageDocument
	
									If Valtype(aRetInt) == "A"
										If Len(aRetInt) == 2
											If !aRetInt[1]
												If Empty(AllTrim(aRetInt[2]))
													cMsgRet := STR0458
												Else
													cMsgRet := AllTrim(aRetInt[2])
												Endif
												Aviso(STR0459,cMsgRet,{"Ok"},3)
												lRet := .F.
												DisarmTransaction()
											Endif
										Endif
									Endif
								Else 
									aRetInt := FWIntegDef("MATA103",,,,"MATA103")	//-- InputDocument
									If Valtype(aRetInt) == "A"
										If Len(aRetInt) == 2
											If !aRetInt[1]
												If Empty(AllTrim(aRetInt[2]))
													cMsgRet := STR0458
												Else
													cMsgRet := AllTrim(aRetInt[2])
												Endif
												Aviso(STR0459,cMsgRet,{"Ok"},3)
												lRet := .F.
												DisarmTransaction()
											Endif
										Endif
									Endif
	
									aRetInt := FWIntegDef("MATA103B",,,,"MATA103B")	//-- Invoice
									If Valtype(aRetInt) == "A"
										If Len(aRetInt) == 2
											If !aRetInt[1]
												If Empty(AllTrim(aRetInt[2]))
													cMsgRet := STR0458
												Else
													cMsgRet := AllTrim(aRetInt[2])
												Endif
												Aviso(STR0459,cMsgRet,{"Ok"},3)
												lRet := .F.
												DisarmTransaction()
											Endif
										Endif
									Endif
								EndIf
								
								If !lRet .Or. (FindFunction("CnNotaDev") .And. lUsaGCT .And. (SF1->F1_TIPO == 'D' .And. !CnNotaDev(0,{SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA})))
									lRet := .F.
									DisarmTransaction()
								EndIf
								
							EndIf

							// Compensacao do Titulo a Pagar quando trata-se de pedido com Adiantamento
							If lRet .And. lCompAdt	
								A103CompAdR(aPedAdt,aRecGerSE2,aRecSE5)
							EndIf

							If __lIntPFS .And. FindFunction("JURA281") .And. !lEstNfClass
								lRet := JURA281(.T., nOpcX, aRecGerSE2, aAutoPFS)
								If lRet
									If l103Exclui .And. FindFunction("J281ExcDoc")
										J281ExcDoc() // IntegraÁ„o com SIGAPFS no momento da exclus„o do documento de entrada
									EndIf
								Else
									DisarmTransaction()
								EndIf
							EndIf

						Endif 
					End Transaction

					//A execuÁ„o das ordens de serviÁo WMS deve ser fora da transaÁ„o
					//para n„o impedir a classificaÁ„o da nota caso ocorra algum problema
					If lRet .And. SF1->F1_TIPO $ "N|D|B" .AND. lIntWMS
						//Desfaz distribuiÁ„o autom·tica quando estorna a classificaÁ„o
						If lEstNfClass .And. SF1->F1_TIPO == "N"
							WmsAvalSF1("7")
						EndIf
						//A execuÁ„o das ordens de serviÁo WMS deve ser fora da transaÁ„o
						//para n„o impedir a classificaÁ„o da nota caso ocorra algum problema
						WmsAvalSF1("5","SF1")
					EndIf

					//Verifica se est· na versao 11.6 e se o endereÁamento na produÁ„o est· ativo.
				    IF lRet .And. lDistMov .And. Len(aDigEnd) > 0
				    	//Chama a rotina de endereÁamento no recebimento / produÁ„o
						A103DigEnd(aDigEnd)
				    endif

					//Executa gravacao da contabilidade
					If lRet .And. !(l103Exclui .and. !lExcCmpAdt)
						If Len(aCtbInf) != 0

							//Ponto de entrada para tratamentos especificos
							If ( ExistBlock("MT103CTB") )
								aMT103CTB := ExecBlock("MT103CTB",.F.,.F.,{aCtbInf,l103Exclui,lExcCmpAdt})
								If ( ValType(aMT103CTB) == "A" )
									aCtbInf := aClone(aMT103CTB)
								EndIf
							EndIf

							//Cria nova transacao para garantir atualizacao do documento
							cA100Incl(aCtbInf[1],aCtbInf[2],3,aCtbInf[3],aCtbInf[4],aCtbInf[5],,,,aCtbInf[7],,aCtbInf[6])

						EndIf
						// ContabilizaÁ„o Compensacao do Titulo a Pagar quando trata-se de pedido com Adiantamento
						If lCompAdt	.And. FindFunction("FxCtbPAdt")
							FxCtbPAdt(aRecSE5)
						EndIf 
					Endif

					// Exibicao do(s) titulo(s) de PIS/COFINS importacao gerados. Retirada da funcao A103GRAVA para que
					// nao seja exibida a interface dentro da transacao.
					If lRet .And. cPaisLoc == "BRA" .And. !l103Auto .And. (l103Inclui .Or. l103Class) .And. Len(aTitImp) > 0 .And. SuperGetMv("MV_TITAPUR",.F.,.F.)
						dbSelectArea("SE2")
						nRecSE2 := SE2->(RecNo())
						Pergunte("FIN050",.F.)
						For nX := 1 To Len(aTitImp)
							If aTitImp[nX][01] <> 0
								SE2->(MsGoto(aTitImp[nX][01]))
								FINA050(,,4,'FA050Alter("SE2",SE2->(RECNO()),2)')
							EndIf
						Next nX
						SE2->(MsGoto(nRecSE2))
						Pergunte("MTA103",.F.)
					Endif

				EndIf

				//Para a localizacao Mexico, sera processada a funcao do ponto de entrada MT100AGR no padrao
				If lRet .And. cPaisLoc == "MEX"
					PgComMex()
				Endif

				//Integracao o modulo ACD - Realiza o enderecamento automatico p/ o CQ na classificacao da nota
				If lRet .And. !(l103Exclui .and. !lExcCmpAdt)

					If lIntACD
						CBMT100AGR()
					
					//Template acionando ponto de entrada
					ElseIf ExistTemplate("MT100AGR")
						ExecTemplate("MT100AGR",.F.,.F.)
					EndIf
					If ExistBlock("MT100AGR",.T.,.T.)
						ExecBlock("MT100AGR",.F.,.F.)
					EndIf
										
					//Agroindustria
					If FindFunction("OGXUtlOrig") //Encontra a funÁ„o
						If OGXUtlOrig()
						   If FindFunction("OGX140")
						      OGX140()
						   EndIf
						EndIf
					Endif
				Endif

                //Trade-Easy
			    //RRC - 18/07/2013 - IntegraÁ„o SIGACOM x SIGAESS: GeraÁ„o autom·tica das invoices e parcelas de c‚mbio a partir do documento de entrada
			    If lRet .And. SF1->F1_TIPO == "N" .And. SuperGetMv("MV_COMSEIC",,.F.) .And. SuperGetMv("MV_ESS0012",,.F.)
			       PS400BuscFat("A","SIGACOM",,SF1->F1_DOC,SF1->F1_SERIE,.T.)
			    EndIf
			Else
				//Libera Lock de Pedidos Bloqueados//
				If Type("aRegsLock")<>"U" 
					If Len(aRegsLock)>0
						A103UnlkPC() 
					EndIf 
				EndIf

				//Desfaz distribuiÁ„o autom·tica
				If l103Class .And. !lEstNfClass .And.  SF1->F1_TIPO == "N" .And. SF1->F1_STATUS != "C" .And. lIntWMS
					WmsAvalSF1("7")
				EndIf

				//Ponto de Entrada para verificar se o usu·rio clicou no bot„o Cancelar no Documento de Entrada
				If (ExistBlock("MT103CAN"))
					ExecBlock("MT103CAN",.F.,.F.)
				EndIf
				
				//Limpa o cache do modelo se o usu·rio clicou no bot„o Cancelar no Documento de Entrada
				If __lIntPFS .And. FindFunction("J281Clear")
					J281Clear()
				EndIf
			EndIf

			//Finaliza a gravacao dos lancamentos do SIGAPCO e apaga lancamentos de bloqueio nao utilizados
			If lRet .And. !(l103Exclui .and. !lExcCmpAdt)
				PcoFinLan("000054")
				PcoFreeBlq("000054")
			Endif
		EndIf
	EndIf
	MaFisEnd()
	//Destrava os registros na alteracao e exclusao
	If l103Class .Or. l103Exclui
		MsUnlockAll()
	EndIf
	If !l103Auto
		SetKey(VK_F4,Nil)
		SetKey(VK_F5,Nil)
		SetKey(VK_F6,Nil)
		SetKey(VK_F7,Nil)
		SetKey(VK_F8,Nil)
		SetKey(VK_F9,Nil)
		SetKey(VK_F10,Nil)
		SetKey(VK_F11,Nil)
		SetKey(VK_F12,bKeyF12)
	EndIf

	//Protecao para evitar ERRORLOG devido ao fato do objeto oLancApICMS nao ser destruido corretamente ao termino da rotina. 
	//Todos os demais objetos sao destruidos corretamente.
	If Type("oLancApICMS") == 'O'
		FreeObj(oLancApICMS)
	EndIf

	If Type("oLancCDV") == 'O'
		FreeObj(oLancCDV)
	EndIf

	If lRet
		If  Type("_aDivPNF") != "U" // Limpa array Divergencias
		   _aDivPNF := {}
		Endif

		If lIntGC // Modulos do DMS
			If FindFunction("OA2900021_A103NFiscal_AposOK")
				lRet := OA2900021_A103NFiscal_AposOK( { aRotina[nOpcX,4] , nOpc , cNFiscal , cSerie , cA100For , cLoja } ) // Apos OK no MATA103
			EndIf
		EndIf
	EndIf

	//Ponto no final da rotina, para o usuario completar algum processo
	If lRet .And. !(l103Exclui .and. !lExcCmpAdt)
		If ExistTemplate("MT103FIM")
			ExecTemplate("MT103FIM",.F.,.F.,{aRotina[nOpcX,4],nOpc})
		EndIf
		If ExistBlock("MT103FIM")
			Execblock("MT103FIM",.F.,.F.,{aRotina[nOpcX,4],nOpc})
		EndIf
		//IntegraÁ„o com MÛdulo de LocaÁıes SIGALOC
		If lMvLocBac .And. lFcLOCM008
			LOCM008(aRotina[nOpcX,4],nOpc)
		EndIf
	Endif

	//Verifica se documento esta excluido ou inserido da SF1
	If l103Auto .And. Type("lTemF1GFE")<>"U" .And. FwIsInCallStack("GFEA065In") 
		lTemF1GFE := !Empty(GetAdvFVal("SF1","F1_DOC",xFilial("SF1") + cNFiscal + cSerie + ca100For + cLoja + cTipo,1))
	Endif 

	//Retorna ao valor original de maxcodes ( utilizado por MayiUseCode()
	SetMaxCodes( nMaxCodes )

EndIf

FwFreeArray(aRecSE5)

cFornIss := ""
dVencISS := CTOD("")

//MÈtricas - Tempo de Inclus„o do documento de entrada
If lRet .And. nOpc <> 0 .And. FwIsInCallStack("MATA103")
	nSegsTot := Round((Seconds() - nInicio), 0)
	nVlrMetr++
	ComMtrTemp("-TempExec",l103Auto,l103Class,cTipo,nVlrMetr,nSegsTot)
	nVlrMetr := 0
EndIf

If lRet .And. nOpc <> 0 .And. FindFunction('JobMultATF') .And. !l103visual .And. SF1->F1_STATUS == 'A'
	JobMultATF(aHeader,aCols,.T.) // .F. Verifica se gera atraves de job / .T. Executa o Job
EndIf

Return lRet

/*/{Protheus.doc} ProcH
Busca campo array cabeÁalho execauto

@param	cCampo: Campo a ser buscado

@author Eduardo Riera
@since 14.03.2006
/*/

Static Function ProcH(cCampo)
Return aScan(aAutoCab,{|x|Trim(x[1])== cCampo })

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ A103NFEic ≥ Autor ≥ Edson Maricate       ≥ Data ≥24.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Programa de Class/Visualizacao/Exclusao de NF SIGAEIC      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103NFEic(ExpC1,ExpN1,ExpN2)                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpC1 = Alias do arquivo                                   ≥±±
±±≥          ≥ ExpN1 = Numero do registro                                 ≥±±
±±≥          ≥ ExpN2 = Numero da opcao selecionada                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103NFEic(cAlias,nReg,nOpcx)

DbSelectArea("SD1")
DbSetOrder(1)
MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)

//Define a funcao utilizada ( Class/Visual/Exclusao)
Do Case
Case aRotina[nOpcx][4] == 2
	MATA100(,,2)
Case aRotina[nOpcx][4] == 4
	MATA100(,,4)
Case aRotina[nOpcx][4] == 5
	MATA100(,,5)
EndCase
Return

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103TudOk ≥ Autor ≥ Edson Maricate        ≥ Data ≥08.02.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Validacao da TudoOk                                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ Nenhum                                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/

Function A103Tudok()

Local aCodFol  	  := {}
Local aPrdBlq     := {}
Local cProdsBlq   := ""
Local cAlerta     := ""
Local cFilSD1	  := ""
Local cSerieNF	  := ""
Local cMRetISS    := GetNewPar("MV_MRETISS","1")
Local cVerbaFol	  := ""
Local cNatValid	  := MaFisRet(,"NF_NATUREZA")
Local lRestNFE	  := SuperGetMV("MV_RESTNFE")=="S"
Local nPValDesc   := GetPosSD1("D1_VALDESC")
Local nPosTotal   := GetPosSD1("D1_TOTAL")
Local nPosIdentB6 := GetPosSD1("D1_IDENTB6")
Local nPosNFOri   := GetPosSD1("D1_NFORI")
Local nPosItmOri  := GetPosSD1("D1_ITEMORI")
Local nPosSerOri  := GetPosSD1("D1_SERIORI")
Local nPosTes     := GetPosSD1("D1_TES")
Local nPosCfo     := GetPosSD1("D1_CF")
Local nPosPc      := GetPosSD1("D1_PEDIDO")
Local nPosItPc    := GetPosSD1("D1_ITEMPC")
Local nPosQtd     := GetPosSD1("D1_QUANT")
Local nPosVlr     := GetPosSD1("D1_VUNIT")
Local nPosOp      := GetPosSD1("D1_OP")
Local nPosCod     := GetPosSD1("D1_COD")
Local nPosItem    := GetPosSD1("D1_ITEM")
Local nPosMed     := GetPosSD1("D1_ITEMMED")
Local nPosQuant   := GetPosSD1("D1_QUANT")
Local nPosItXML	  := GetPosSD1("D1_ITXML")
Local cFilNfOri   := xFilial("SD2")
Local cFilSC7 	  := xFilial('SC7')
Local cFilSF4	  := xFilial('SF4')	
Local nItens      := 0
Local nPosAFN 	  := 0
Local nPosQtde	  := 0
Local nTotAFN	  := 0
Local nA		  := 0
Local nX          := 0
Local nY		  := 0
Local nZ          := 0
Local nR 		  := 0
Local n_SaveLin
Local lGspInUseM  := If(Type('lGspInUse')=='L', lGspInUse, .F.)
Local lContinua	  := .T.
Local lPE		  := .T.
Local lRet        := .T.
Local lItensMed   := .F.
Local lItensNaoMed:= .F.
Local lEECFAT	  := SuperGetMv("MV_EECFAT",.F.,.F.)
Local lEspObg	  := SuperGetMV("MV_ESPOBG",.F.,.F.)
Local lMT103PBLQ  := .F.
Local lUsaAdi	  := .F.
Local lDHQInDic   := AliasInDic("DHQ") .And. SF4->(ColumnPos("F4_EFUTUR") > 0)
Local lMt103Com   := FindFunction("A103FutVld")
Local aAreaSC7    := SC7->(GetArea())
Local aMT103GCT   := {}
Local aItensPC	  := {}
Local nItemPc	  := 0
Local nQtdItPc	  := 0
Local aAreaSX3	  := SX3->(GetArea())
Local lVldItPc	  := SuperGetMv("MV_VLDITPC",.F.,.F.)
Local lVerChv	  := SuperGetMv("MV_VCHVNFE",.F.,.F.)
Local cNFForn	  := ""
Local nNFSerie	  := ""
Local lVtrasef	  := SuperGetMv("MV_VTRASEF",.F.,"N") == "S"
Local aDocEmp		:= {}
Local aAreaSB5	  := {}
Local nTamTipo    := TamSX3("E2_TIPO")[1]
Local lDuplic	:= .F.
Local aAreaSD1	:= {}
Local aAreaSF1	:= {}
Local aAreaTEW	:= {}
Local cMsgTEW		:= ""
Local lHasLocEquip	:= FindFunction("At800AtNFEnt") .And. AliasInDic("TEW")
Local cPrefixo	:= If(SuperGetMV("MV_2DUPREF") == "SF1->F1_SERIE",cSerie,"")
Local cNfDtFin	:= SuperGetMV("MV_NFDTFIN",.F.,"1")
Local nTamCodFol	:= TamSx3("RV_CODFOL")[1]
Local lGrade		:= MaGrade()
Local lVerificou	:= .F. //verificacao de entrada de remedio controlado
Local cCaixaSup		:= Space(25)
Local lAvulsa		:= .F.
Local cDivImp		:= SuperGetMV("MV_NFVLDDI",.F.,"0")
Local lDivImp		:= SuperGetMV("MV_NFDVIMP",.F.,.F.) .And. COLConVinc(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA) > 0 .And. !INCLUI
Local cImpMsg		:= STR0470
Local cImpMsg2		:= CRLF+STR0471
Local cImpMsg3		:= CRLF+STR0472
Local nPosCC		:= 0
Local nPosConta		:= 0
Local nPosItCta		:= 0
Local nPosClVl		:= 0
Local nK			:= 0
Local cVarAuxDB		:= ""
Local cVarAuxCR		:= ""
Local aEntCtb 		:= CtbEntArr()
Local lLjSetSup		:= ExistTemplate( "LjSetSup" )
Local lIntePms		:= IntePms()
Local lMT103GCT		:= ExistBlock("MT103GCT")
Local lDtNT2006		:= A103DNT2006()
Local cNFSerie 		:= ""
Local lDif 			:= .F. 
Local lCsdXML 		:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA") .and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")
Local lRetCSD 		:= .T.
Local lExcCsd		:= .F.
Local nPosAXml 		:= 0
Local aItensDKA		:= {}
Local aAux 			:= {}
Local cExcCFOP  	:= SuperGetMV("MV_EXCCSD",.F.,"1551|1555|1556|1577|2551|2555|2556|2557")
Local nTotItens 	:= 0
Local nItensExc 	:= 0
Local cItemIt   	:= ""

DEFAULT lMT103PBLQ  := .F.

If Type("aAuxColSDE") == "U"
	PRIVATE aAuxColSDE  := {}
EndIf

If Type("aAuxHdSDE") == "U"
	PRIVATE aAuxHdSDE := {}
EndIf

If !Empty(aAuxColSDE) .And. Empty(aAuxHdSDE)
	aAuxHdSDE := COMXHDCO('SDE')	
EndIf

If !Empty(aAuxHdSDE)
	nPosCC		:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_CC"})	
	nPosConta	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_CONTA"})
	nPosItCta	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_ITEMCTA"})
	nPosClVl	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_CLVL"})
	nPEntA05CR	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC05CR"})
	nPEntA05DB	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC05DB"})
	nPEntA06CR	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC06CR"})
	nPEntA06DB	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC06DB"})
	nPEntA07CR	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC07CR"})
	nPEntA07DB	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC07DB"})
	nPEntA08CR	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC08CR"})
	nPEntA08DB	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC08DB"})
	nPEntA09CR	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC09CR"})
	nPEntA09DB	:= Ascan(aAuxHdSDE, {|x| AllTrim(x[2]) == "DE_EC09DB"})
Endif

//ValidaÁ„o para integraÁ„o com GFE via ExecAuto
If l103Auto .And. IsInCallStack("GFEA065In")  .And. INCLUI

	aAreaSF1 := SF1->(GetArea())
	SF1->(DbSetOrder(1))

	//Ajusta campo SÈrie
	If Len(cSerie) <> Len(SD1->D1_SERIE)
	   cSerie := Left(cSerie,Len(SD1->D1_SERIE))
	Endif

	If lContinua .And. ;
	   SF1->(DbSeek(xFilial("SF1")+cnFiscal+SerieNfId("SD1",4,"D1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja+cTipo,.T.))

	   lContinua := .F.

	   nItens := 1 //Para n„o gerar mensagem de erro do item

	Endif

	SF1->(RestArea(aAreaSF1))

	If lContinua

     	//verifica se ja existe na inclus„o itens da Nota

     	aAreaSD1:=SD1->(GetArea())

    	SD1->(DbSetOrder(1))
		cFilSD1  := xFilial("SD1")
		cSerieNF := SerieNfId("SD1",4,"D1_SERIE",dDEmissao,cEspecie,cSerie)
		For nX := 1 to Len(aCols)
			If !aCols[nx][Len(aHeader)+1]
	         If SD1->(DbSeek(cFilSD1+cnFiscal+cSerieNF+cA100For+cLoja+aCols[nX,nPosCod]+aCols[nX,nPosItem],.T.))  //D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_COD+D1_ITEM
				lContinua := .F.
				exit
			  Endif
			EndIf
		Next nX

		SD1->(RestArea(aAreaSD1))

	Endif

	If ! lContinua

       AutoGRLog(STR0420+Space(1)+cnFiscal+Space(1)+STR0037+Space(1)+cSerie+Space(1)+STR0038+Space(1)+STR0028+Space(1)+cA100for) //"Documento Fiscal de Entrada "+cnFiscal+" Serie "+cSerie+" Forn "+cA100for+" j· existente!"

		lRet := .F.

	Endif

Endif

If lRet .And. cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. cFormul == "S" .And. !l103Class .And. lDtNT2006 
	If SubStr(aInfAdic[16],1,1) $ "0|5" .And. !Empty(aInfAdic[17])
		Help(" ",1,"A103INTA1U",,STR0536 + RetTitle("F1_CODA1U"),1,0) //"N„o È necessario informar um "
		lRet := .F.    
	Endif
Endif

If lRet
	For nx:=1 to len(aCols)

		//Verifica o poder de terceiro
		If lRet .And. !aCols[nx][Len(aCols[nx])] .And. nPosNfOri > 0 .And. nPosSerOri > 0 .And. nPosIdentB6 > 0 ;
		                                           .And. nPosQuant > 0 .And. nPosTotal  > 0 .And. nPValDesc   > 0 ;
		                                           .And. nPosCod   > 0 .And. nPosTES    > 0 .And. !lGspInUseM

			/* Com template de Drogaria, eh necessario a verificacao se o
			 remedio eh controlado. Se for , eh obrigatorio a autorizacao
			 do responsavel farmaceutico na entrada do produto */
		    If lHasTplDro .AND. !lVerificou  	        // se for drogaria, verifica se ha itens controlados pelo template
		    	If T_DroVerCont( aCols[nX,nPosCod]) 	// se for remedio controlado
	    			lRet := T_DroVERPerm(3,@cCaixaSup) 			// verifica permissao do primeiro item controlado, 2 parametro indicando que eh entrada de nota
					//Passar· para a vari·vel de referÍncia para DroVldfuncs
					If lLjSetSup
						ExecTemplate("LjSetSup",.F.,.F.,{cCaixaSup})
					EndIf

	    			lVerificou := lRet
		    	EndIf
		    EndIf

			//Verifica se o conteudo do aCols[nX][nPosIdentB6] confere com o do documento original (SD2) em casos onde
			//o usuario altera manualmente o docto orignal ao retornar devolucoes de beneficiamento pela opcao Retornar.
			If Alltrim(SF4->F4_CODIGO) <> Alltrim(aCols[nX][nPosTES])
				SF4->(DbSetOrder(1))
				SF4->(MsSeek(xFilial("SF4") + aCols[nX][nPosTES]))
			Endif

			If SF4->F4_PODER3 == "D"

				//Validacao utilizada para nao permitir que o usuario altere o fornecedor quando utilizado devolucao de poder de terceiros,
				//pois o fornecedor do documento de entrada deve ser o mesmo fornecedor informado no documento original. Somente quando utilizada 
				//operacao triangular sera possivel alterar o fornecedor.
				If lRet .And. !IsTriangular(mv_par08==1)
					SD2->(DbSetOrder(4))
					If SD2->(MsSeek(xFilial("SD2") + aCols[nX][nPosIdentB6])) .And.;
					   SD2->D2_CLIENTE+SD2->D2_LOJA <> cA100for+cLoja
						cAlerta := IIf(cTipo=="B",STR0288,STR0284) + " " + cA100For + "/" + cLoja + " " + STR0285 + " " + chr(13)  //"O conteudo dos campos fornecedor/loja : ###### / ## esta incompativel"
						cAlerta += STR0286 + " " + chr(13) 												 							 //"com a amarraÁ„o dos itens informados referente a devoluÁ„o de poder de terceiros."
						cAlerta += IIf(cTipo=="B",STR0289,STR0287) + chr(13) 													     //"Por favor informe o fornecedor/loja correto."
					   	Aviso("IDENTSB6",cAlerta,{"Ok"})
						lRet := .F.
					EndIf
				EndIf

				If lRet
					lRet := VldLinSB6(nx, nPosNfOri,nPosSerOri,nPosIdentB6,nPosQuant,nPosTotal,nPValDesc,nPosCod,nPosTES,nPosVlr,aCols,cFilNfOri,cA100For,cLoja,cTipo,l103Auto)
				EndIf
			EndIf
		EndIf

		//Valida qtde com a Integracao PMS
		If lRet .And. !aCols[nx][Len(aCols[nx])]
			If lIntePms .And. Len(aRatAFN)>0
				If Len(aHdrAFN) == 0
					aHdrAFN := FilHdrAFN()
				Endif
				nPosAFN  := Ascan(aRatAFN,{|x|x[1]==(aCols[nX,nPosItem])})
				nPosQtde := Ascan(aHdrAFN,{|x|Alltrim(x[2])=="AFN_QUANT"})
				nTotAFN	:= 0

				If nPosAFN>0 .And. nPosQtde>0 .And. nPosQuant>0
					nPPed := GetPosSD1("D1_PEDIDO")
					nPItP := GetPosSD1("D1_ITEMPC")
					For nA := 1 To Len(aRatAfn[nPosAFN][2])
						If !aRatAFN[nPosAFN][2][nA][LEN(aRatAFN[nPosAFN][2][nA])]
							nTotAFN	+= aRatAfn[nPosAFN][2][nA][nPosQtde]
							If !PmsVldTar("AFN", aHdrAFN, aRatAFN[nPosAFN][2]) .AND. PMSHLPAFN()
								Help("   ",1,"PMSUSRNFE")
								lRet := .F.
								Exit
							EndIf
						Endif
					Next nA

					If nPPed > 0 .And. nPItP > 0
						If !PMSNFSA(aCols[nx][nPPed],aCols[nx][nPItP])[1]
							If nTotAFN > aCols[nx][nPosQuant]
								Help("   ",1,"PMSQTNF")
								lRet := .F.
								Exit
							Endif
						Endif
					Endif
				Endif
			Endif
		Endif

		//Verifica o preenchimaneto da TES dos itens devido a importacao do pedido de compras
		If lRet .And. !aCols[nx][Len(aCols[nx])]
			nItens ++
			If nPosCFO>0 .And. nPosTES>0 .And. Empty(aCols[nx][nPosCFO]) .Or. Empty(aCols[nx][nPosTES])
				Help("  ",1,"A100VZ")
				lRet := .F.
				Exit
			Endif

			// Verifica se nao esta consumindo saldo excedente de NF de compra com entrega futura (TudoOK)
			aSize(aCompFutur, Len(aCols))
			For nZ := 1 To Len(aCompFutur)
				If aCompFutur[nZ] == Nil
					aCompFutur[nZ] := {" "," "," ",0," "," "," "}
				EndIf
			Next nZ

			If Alltrim(SF4->F4_CODIGO) <> Alltrim(aCols[nX][nPosTES])
				SF4->(DbSetOrder(1))
				SF4->(MsSeek(xFilial("SF4") + aCols[nX][nPosTES]))
			Endif

			//Verifica se documento gera duplicata (Utilizado na query apÛs o laÁo do Acols)
			If !lDuplic .And. SF4->F4_DUPLIC == "S"
				lDuplic := .T.
			EndIf 

			If lDHQInDic .And. lMt103Com .And. SF4->F4_EFUTUR == "2"
				If !A103FutVld(.F., aCompFutur, nX, .T.)
					lRet := .F.
					Exit
				EndIf
			EndIf

			If nPosCod>0 .And. nPosItem>0 .And. lRet .And. SB1->(MsSeek(xFilial("SB1")+aCols[nx][nPosCod])) .And. !RegistroOk("SB1",.F.)
				Aadd(aPrdBlq,aCols[nx][nPosItem])
			Endif

			If !Empty( nPosMed )
				//Verifica a existencia de itens de medicao junto com itens sem medicao
				lItensMed    := lItensMed .Or. aCols[ nX, nPosMed ] == "1"
				lItensNaoMed := lItensNaoMed .Or. aCols[ nX, nPosMed ] $ " |2"

				//Ponto de entrada permite incluir itens n„o-pertinentes ao gct ou n„o.
				If lMT103GCT
					aMT103GCT := ExecBlock("MT103GCT",.F.,.F.,{aCols,nX,nPosMed})

					If ValType(aMT103GCT) == "A"
						If Len(aMT103GCT) >= 1 .And. ValType(aMT103GCT[1]) == "L"
							lItensMed    := aMT103GCT[1]
						EndIf
						If Len(aMT103GCT) >= 2 .And. ValType(aMT103GCT[2]) == "L"
							lItensNaoMed := aMT103GCT[2]
						EndIf
					EndIf
				EndIf

				If lItensMed .And. lItensNaoMed
					Help( " ", 1, "A103MEDIC" )
					lRet := .F.
					Exit
				EndIf
			EndIf
		EndIf

		If lRet .And. !aCols[nx][Len(aCols[nx])]

			//Verifica se os pedidos amarrados a NFE estao bloqueados "Classificacao"
			If lRet .And. ( l103Class .Or. INCLUI ) .And. lRestNFE
				SC7->(dbSetOrder(14))
				If SC7->(dbSeek(xFilEnt(cFilSC7, "SC7")+aCols[nx,nPosPc]+aCols[nx,nPosItPc]))
					While SC7->C7_FILENT == xFilEnt(cFilSC7, "SC7") .And. SC7->C7_NUM == aCols[nx,nPosPc] .And. SC7->C7_ITEM == aCols[nx,nPosItPc]
						If SC7->C7_FILIAL == cFilSC7 .And. !(SC7->C7_CONAPRO $ 'L ')
							Help( "", 1, "A120BLQ" )
							lRet := .F.
							Exit
						EndIf
						SC7->(dbSkip())
					EndDo
					If !lRet
						Exit
					EndIf
				EndIf
			EndIf

			//Valida se o valor do desconto no item D1_VALDESC e maior ou igual ao valor total do item
			If lRet .And. cPaisLoc == "BRA"
				If aCols[nX,nPValDesc] >= aCols[nX,nPosTotal] .And. aCols[nX,nPValDesc] <> 0
					If SF4->F4_VLRZERO$"2 "
						Aviso("A103VLDESC",STR0315,{"Ok"}) //"Existe algum item onde o valor de desconto È maior ou igual ao valor total do item, verifique o conte˙do do campo ou realize novo rateio do desconto no folder de descontos/Frete/Despesas."
						lRet := .F.
						Exit
					EndIf
				EndIf
	        EndIf

			//Valida a AmarraÁ„o com o Pedido de Compras Centralizado - Referente Central de Compras
			If lRet .And. !A103ValPCC(nX)
		   		lRet := .F.
				Exit
			EndIf

			//Valida se um item de pedido de compras consta mais de uma vez nos itens do documento e ultrapassa a quantidade do PC
			If lRet .And. !lVldItPc .And. !l103Class .And. !aCols[nX][Len(aHeader)+1] .And. !Empty(aCols[nX][nPosPc]) .And. !Empty(aCols[nX][nPosItPc])
				If lGrade
					Aadd(aItensPC,{aCols[nX][nPosPc],aCols[nX][nPosItPc],aCols[nX][nPosQtd],aCols[nX][nPosCod]})
					nItemPc  := 0
					nQtdItPc := 0
					For nY := 1 To Len(aItensPC)
						If aScan(aItensPC,{|x| x[1]==aCols[nX][nPosPc] .And. x[2]==aCols[nX][nPosItPc] .And. x[4]==aCols[nX][nPosCod]},nY,1) > 0
							nItemPc++
							nQtdItPc += aItensPC[nY][3]
						EndIf
						If nItemPc > 1
							SC7->(dbSetOrder(4))
							If SC7->(dbSeek(cFilSC7+aCols[nX][nPosCod]+aCols[nY,nPosPc]+aCols[nX][nPosItPc] ))
								If nQtdItPc > ( SC7->C7_QUANT-SC7->C7_QUJE-SC7->C7_QTDACLA)
									Help(,, "A103ITEXCED",, STR0543, 1, 0,,,,,,{STR0544})
									lRet := .F.
									Exit
								EndIf
							EndIf
						EndIf
					 Next nY
				Else
					Aadd(aItensPC,{aCols[nX][nPosPc],aCols[nX][nPosItPc],aCols[nX][nPosQtd]})
					nItemPc  := 0
					nQtdItPc := 0
					For nY := 1 To Len(aItensPC)
						If aScan(aItensPC,{|x| x[1]==aCols[nX][nPosPc] .And. x[2]==aCols[nX][nPosItPc]},nY,1) > 0
							nItemPc++
							nQtdItPc += aItensPC[nY][3]
						EndIf
						If nItemPc > 1
							SC7->(dbSetOrder(1))
							If SC7->(dbSeek(cFilSC7+aCols[nY,nPosPc]+aCols[nX][nPosItPc] ))
								If nQtdItPc > ( SC7->C7_QUANT-SC7->C7_QUJE-SC7->C7_QTDACLA)
									Help(,, "A103ITEXCED",, STR0543, 1, 0,,,,,,{STR0544})
									lRet := .F.
									Exit
								EndIf
							EndIf
						EndIf
					 Next nY
				Endif
			EndIf

			If lRet
			    lRet := ( Empty(aCols[nX][nPosTES]) .Or. Iif(SF4->F4_MSBLQL == '1',;
				ExistCpo("SF4",Alltrim(aCols[nX][nPosTES]),1),.T.) )
			EndIf

			//Verifica se data do movimento nÑo Ç menor que data limite de movimentacao no financeiro configurada no parametro MV_DATAFIN
			If lRet .And. SF4->F4_DUPLIC == "S"
				If cNfDtFin == "1"
					lRet:= DtMovFin()
				ElseIf cNfDtFin == "2"
					lRet:= DtMovFin(dDEmissao)
				EndIf
			EndIf

			// Validacao do processo de recusa de mercadoria por parte do destinatario (Devolucao) para notas do tipo B e N
			If lRet .And. cTipo $ "BN" .And. "S" $ aNfeDanfe[24] .And. ( Empty(aCols[nX][nPosNfOri]) .Or. Empty(aCols[nX][nPosSerOri]) .Or. Empty(aCols[nX][nPosItmOri]) )
				Aviso(STR0119,STR0453,{STR0163})	// "O campo Merc.nao entregue nas Informacoes DANFE deve ser selecionado exclusivamente para devolucoes de mercadoria. Existem itens na nota sem a informacao da respectiva nota de origem."
				lRet := .F.
				Exit
			EndIf

		EndIf

		//ValidaÁıes - SEFAZ AM
		If lRet .and. lCsdXML .and. ( l103Class .Or. INCLUI ) .and. cTipo == "N" .and. Alltrim(cEspecie) $ "NFE|SPED"
			If !aCols[nX][Len(aCols[nX])]
				nTotItens += 1

				If AllTrim(aCols[nX,nPosCfo]) $ cExcCFOP
                    nItensExc += 1
                Endif

				If Empty(aCols[nX,nPosItXML])
                    cItemIt += "|" + AllTrim(aCols[nX,nPosItem])
                Endif
			Endif
		Endif

		if lRet .and. lCsdXML .and. ( l103Class .Or. INCLUI ) .and. cTipo == "N" .and. Alltrim(cEspecie) $ "NFE|SPED" .And. !(AllTrim(aCols[nX,nPosCfo]) $ cExcCFOP)

			if len(aAutoCSD) > 0
				for nY := 1 to len(aAutoCSD)
					if aScan(aAutoCSD[nY], {|x|AllTrim(x[1])== "DKA_ITXML" }) == 0
						//"H· divergÍncias nos itens da NF - O envio do campo DKA_ITXML È obrigatÛrio quando o par‚metro MV_CSDXML est· ativo."
						Help(,, "A103ITXML",, STR0552 , 1, 0,,,,,,)
						lRet := .F.
						Exit
					endif

					if lRet .and. aScan(aAutoCSD[nY], {|x|AllTrim(x[1])== "DKA_DESCFO" }) == 0 .and. empty(GetAdvFVal("SA5","A5_DESCPRF",fwxFilial("SA5") + ca100for + cLoja + aCols[nX][nPosCod] ,1))
						//"H· divergÍncias nos itens da NF - … obrigatÛrio o envio do campo DKA_DESCFO - DescriÁ„o do fornecedor, quando n„o houver uma descriÁ„o no produto x fornecedor."
						Help(,, "A103ITXML",, STR0553 , 1, 0,,,,,,)
						lRet := .F.
						Exit
					endif

					if lRet
						nPosAXml := aScan(aAutoCSD[nY], {|x|AllTrim(x[1])== "DKA_QTDXML" })
						if nPosAXml == 0
							//"H· divergÍncias nos itens da NF - … obrigatÛrio o envio do campo DKA_QTDXML - Quantidade do XML."
							Help(,, "A103ITXML",, STR0554 , 1, 0,,,,,,)
							lRet := .F.
							Exit
						elseif nPosAXml > 0
							if aAutoCSD[nY][nPosAXml][2] <= 0
								//"H· divergÍncias nos itens da NF - O valor da quantidade do XML deve ser maior que zero."
								Help(,, "A103ITXML",, STR0555 , 1, 0,,,,,,)
								lRet := .F.
								Exit
							endif
						endif
					endif
				next nY
				if lRet .and. aScan(aAutoCSD, {|x|AllTrim(x[1,2])== aCols[nX][nPosItXML] }) == 0
					//"H· divergÍncias nos itens da NF - Foi enviado um item XML(DKA_ITXML) que n„o existe no D1_ITXML dos itens da NF"
					Help(,, "A103ITXML",, STR0556 , 1, 0,,,,,,)
					lRet := .F.
					Exit
				endif
			endif

			if empty(Alltrim(aCols[nX][nPosItXML])) .and. !aCols[nX][Len(aCols[nX])]
				//"H· divergÍncias no item " # "Quando o par‚metro MV_CSDXML estiver ativo, torna-se obrigatÛrio o preenchimento do campo Item XML"
				Help(,, "A103ITXML",, STR0557 + aCols[nX][nPosItem] , 1, 0,,,,,,{STR0558})
				lRet := .F.
				Exit
			else
				//Verifica se o item do XML È composto do mesmo produto e tes.
				nPosAXml := aScan(aItensDKA, {|x|AllTrim(x[1])== Alltrim(StrZero(Val(aCols[nX][nPosItXML]), TamSX3("D1_ITXML")[1])) })
				if nPosAXml == 0

					aAux := {}
					aAux := {;
							StrZero(Val(aCols[nX][nPosItXML]), TamSX3("D1_ITXML")[1]),; 	//[1] - Item XML
							aCols[nX][nPosTes],;	//[2] - TES
							aCols[nX][nPosCod]; 	//[3] - Produto
						}

					aAdd(aItensDKA,aClone(aAux))
				else
					if Alltrim(aItensDKA[nPosAXml][1]+aItensDKA[nPosAXml][2]+aItensDKA[nPosAXml][3]) <> Alltrim(StrZero(Val(aCols[nX][nPosItXML]), TamSX3("D1_ITXML")[1])+aCols[nX][nPosTes]+aCols[nX][nPosCod])
						//"H· divergÍncias no item XML " # "Os produtos e TES devem ser iguais quando s„o parte do mesmo Item do XML"
						Help(,, "A103ITXML",, STR0559 + aCols[nX][nPosItXML] , 1, 0,,,,,,{STR0560})
						lRet := .F.
						Exit
					endif
				endif
			endif
		endif
	Next
EndIf

If lRet .And. Len(aPrdBlq) > 0
	If ExistBlock("MT103PBLQ")
		lMT103PBLQ:=ExecBlock("MT103PBLQ",.F.,.F.,{aPrdBlq})
		lRet:=lMT103PBLQ
	Else
		For nX:= 1 To Len(aPrdBlq)
			If nX == 1
				cProdsBlq := aPrdBlq[nX]
			Else
				cProdsBlq += " / "+aPrdBlq[nX]
			Endif
		Next

		Aviso("REGBLOQ",OemToAnsi(STR0204)+cProdsBlq,{STR0163}, 2) //"Itens Bloqueados: "
		lRet := .F.
	EndIf
Endif

//       Caso a rotina de locaÁ„o de equipamentos do Gest„o de ServiÁos esteja configurada no ambiente do cliente:
// Verifica se na composiÁ„o das notas fiscais de origem (NF de SaÌda)  selecionadas para a criaÁ„o da NF de DevoluÁ„o
// existe algum equipamento de locaÁ„o que possua a cobranÁa do serviÁo prestado atravÈs do controle de  apontamento de
// horimetro.  Caso encontre, verifica se a atualizaÁ„o do valor de sua marcaÁ„o de retorno est· devidamente atualizada
// no sistema. SÛ permitir· que a nota de devoluÁ„o seja gerada para o equipamento cuja atualizaÁ„o do valor de retorno
// do seu horimetro tenha sido realizada.
If lRet .AND. lHasLocEquip
	aAreaTEW	:= TEW->(GetArea())
	cMsgTEW	:= ""
	TEW->(dBSetOrder(5))	//TEW_FILIAL+TEW_NFSAI+TEW_SERSAI+TEW_ITSAI
	For nx := 1 to len(aCols)
		If	TEW->(MsSeek(xFilial("TEW")+aCols[nx][nPosNFOri]+aCols[nx][nPosSerOri]+aCols[nx][nPosItmOri]))
			If !( At970ChkHr(	"RET" /*cFase*/,;
								TEW->TEW_NUMPED /*cNumPV*/,;
								TEW->TEW_ITEMPV /*cItemPV*/,;
								TEW->TEW_ORCSER /*cOrcSer*/,;
								TEW->TEW_CODMV /*cCodMV*/,;
								TEW->TEW_CODEQU /*cCodEqu*/,;
								TEW->TEW_PRODUT /*cProdut*/,;
								TEW->TEW_BAATD /*cBaAtd*/,;
								! l103Auto /*lExibeMsg*/) )
				cMsgTEW	+=	STR0437+" "+TEW->TEW_PRODUT+CRLF+;																//"Produto:"
								STR0438+" "+AllTrim(Posicione("SB1",1,xFilial("SB1")+TEW->TEW_PRODUT,"B1_DESC"))+CRLF+;	//"DescriÁ„o:"
								STR0439+" "+AlLTrim(TEW->TEW_BAATD)+CRLF+CRLF													//"IdentificaÁ„o:"
				lRet := .F.
			EndIf
		EndIf
	Next nx
	If	!lRet .AND. l103Auto
		cMsgTEW	:=	STR0440+CRLF+CRLF+;	//"O valor de retorno do horimetro da(s) base(s) de atendimento abaixo relacionada(s) n„o est· atualizado:"
						cMsgTEW+;
						STR0441+CRLF+;		//"Acesse o cadastro das bases de atendimento do mÛdulo de Gest„o de ServiÁos, localize o(s) equipamento(s) desejado(s), e atualize o valor de retorno do seu horimetro."
						STR0442				//"A preparaÁ„o do documento de entrada desse(s) equipamento(s) somente ser· permitida apÛs a atualizaÁ„o do valor de retorno do seu horimetro."
		Aviso("A103VLDHRM",cMsgTEW,{"Ok"})
	EndIf
	RestArea(aAreaTEW)
EndIf

//Verifica se ha empenho da OP e dispara o Alerta para continuar
If lRet
	For nx:=1 to len(aCols)
		If nPosOp>0 .And. !aCols[nx][Len(aCols[nx])] .And. nX <> n
			If !lGspInUseM .And. lRet .And. !Empty(aCols[nx][nPosOp])
				If ! A103ValSD4(nx)
					lRet := .F. // Corrigido p/ nao alterar o lRet, se .F., novamente p/ .T.
				EndIf
			EndIf
		EndIf
	Next
EndIf

//Impede a inclusao de documentos sem nenhum item ativo
If lRet .And. nItens == 0 
	Help("  ",1,"A100VZ")
	lRet := .F.
EndIf

//Verifica o preenchimento dos campos.
If lRet .And. Empty(ca100For) .Or. Empty(dDEmissao) .Or. Empty(cTipo) .Or. (Empty(cNFiscal).And.cFormul<>"S") .Or. (lEspObg .And. Empty(cEspecie))
	Help(" ",1,"A100FALTA")
	lRet := .F.
EndIf

//Verifica a condicao de pagamento.
If lRet .And. MaFisRet(,"NF_BASEDUP") > 0 .And. Empty(cCondicao) .And. cTipo<>"D"
	Help("  ",1,"A100COND")
	If ( Type("l103Auto") == "U" .Or. !l103Auto )
		oFolder:nOption := 6
	EndIf
	lRet := .F.
EndIf

//Verifica a natureza
If lRet .And. MaFisRet(,"NF_BASEDUP") > 0 .And. Empty(MaFisRet(,"NF_NATUREZA")) .And. cTipo<>"D"
	If SuperGetMV("MV_NFENAT",.F.,.F.) 
		Help("  ",1,"A103NATURE")
		If ( Type("l103Auto") == "U" .Or. !l103Auto )
			oFolder:nOption := 6
		EndIf
		lRet := .F.
	EndIf
EndIf

//Verifica Frete
If lRet .And. !A103ValFrete()
	lRet:=.F.
EndIf

//Verifica se o Produto e do tipo MuniÁ„o e se sua Unidade e Caixa
If lRet .And. SuperGetMV("MV_GSXNFE",,.F.)

	aAreaSB5	:= SB5->(GetArea())

	For nX := 1 To Len(aCols)
		DbSelectArea('SB5')
		SB5->(DbSetOrder(1))
		If SB5->(DbSeek(xFilial('SB5')+aCols[nX][nPosCod])) // Filial: 01, Codigo: 000001, Loja: 02
			If SB5->B5_TPISERV=='3' .AND. !At730Prod(aCols[nX][nPosCod])
				Help("  ",1,"AT730Prod")
				lRet := .F.
			EndIf
		EndIf
	Next nX
	RestArea(aAreaSB5)

EndIf

//Verifica se o total da NF esta negativo devido ao valor do desconto
If lRet .And. cMRetISS == "1"
	If MaFisRet(,"NF_TOTAL")<0  .Or. (MaFisRet(,"NF_BASEDUP")>0 .And. MaFisRet(,"NF_BASEDUP")-MaFisRet(,"NF_VALIRR")-MaFisRet(,"NF_VALINS")-MaFisRet(,"NF_VALISS")<0)
		Help("  ",1,'TOTAL')
		lRet := .F.
	EndIf
Else
	If lRet .And. MaFisRet(,"NF_TOTAL")<0  .Or. (MaFisRet(,"NF_BASEDUP")>0 .And. MaFisRet(,"NF_BASEDUP")-MaFisRet(,"NF_VALIRR")-MaFisRet(,"NF_VALINS")<0)
		Help("  ",1,'TOTAL')
		lRet := .F.
	EndIf
Endif

If lRet .And. lContinua
	//Verifica se ha bloqueio em algum item do pco qdo valida for por grade
	If PcoBlqFim({{"000054","07"},{"000054","05"},{"000054","01"}})
		n_SaveLin := n
		For nx:=1 to len(aCols)
			If !aCols[nx][Len(aCols[nx])]
				n := nX
				If lRet
					Do Case
					Case cTipo == "B"
						lRet	:=	PcoVldLan("000054","07","MATA103",/*lUsaLote*/,/*lDeleta*/, .F./*lVldLinGrade*/)
					Case cTipo == "D"
						lRet	:=	PcoVldLan("000054","05","MATA103",/*lUsaLote*/,/*lDeleta*/, .F./*lVldLinGrade*/)
					OtherWise
						lRet	:=	PcoVldLan("000054","01","MATA103",/*lUsaLote*/,/*lDeleta*/, .F./*lVldLinGrade*/)
					EndCase
				Endif
				If !lRet
					Exit
				EndIf
			EndIf
		Next
		n := n_SaveLin
	EndIf
	If lRet
		Do Case
		Case cTipo == "B"
			lRet	:=	PcoVldLan("000054","20","MATA103",/*lUsaLote*/,/*lDeleta*/, .F./*lVldLinGrade*/)
		Case cTipo == "D"
			lRet	:=	PcoVldLan("000054","19","MATA103",/*lUsaLote*/,/*lDeleta*/, .F./*lVldLinGrade*/)
		OtherWise
			lRet	:=	PcoVldLan("000054","03","MATA103",/*lUsaLote*/,/*lDeleta*/, .F./*lVldLinGrade*/)
		EndCase
	Endif
	
	//Integracao com o PMS
	If lRet .And. lIntePms
		For nX := 1 To Len(aCols)
			If aCols[nX][Len(aCols[nX])] // Item Deletado
				nPosAFN  := Ascan(aRatAFN,{|x|x[1]==(StrZero(nX,4))})
				If nPosAFN >  0
					aDel( aRatAFN, nPosAFN )
					aSize( aRatAFN, Len(aRatAFN)-1)
				Endif
			Endif
		Next nX
	Endif
	
	//Integracao com o EEC
	If ( lRet .And. lEECFAT )
		lRet := EECFAT3("VLD",.F.)
	EndIf
	
	//Pontos de Entrada
	If (ExistTemplate("MT100TOK")) .And. lMt100Tok
		lPE := ExecTemplate("MT100TOK",.F.,.F.,{lRet})
		If ValType(lPE) = "L"
			If ! lPE
				lRet := .F. // Corrigido p/ nao alterar o lRet, se .F., novamente p/ .T.
			EndIf
		EndIf
	EndIf

	If lRet .And. (Inclui .Or. l103Class) .And. !(cTipo$"DB")
		
		//Valida a verba quando pagto de autonomo
		DbSelectArea("SA2")
		DbSetOrder(1)
		If MsSeek(xFilial("SA2")+cA100For+cLoja) .And. !Empty(SA2->A2_NUMRA)
			SF4->(DbSetOrder(1))
			For nx:=1 to len(aCols)
				SF4->(MsSeek(cFilSF4 + aCols[nX][nPosTES]))
				If SF4->F4_DUPLIC == "S"
					dbSelectArea("SRV")
					dbSetOrder(2)
					MsSeek(xFilial("SRV") + StrZero(1,nTamCodFol),.T.)
					If Eof()
						Help("  ",1,"A103VERBAU")
						lRet := .F.
					Else
						//Identifica o funcionario
						DbSelectArea("SRA")
						DbSetOrder(13)
						If MsSeek(SA2->A2_NUMRA) .And. FP_CODFOL(@aCodFol,SRA->RA_FILIAL)
							//Obtem o codigo da verba
							cVerbaFol := aCodFol[218,001] //Pagamento de autonomos
						EndIf
					EndIf
					If lRet .And. Empty(cVerbaFol)
					   Help("  ",1,"A103VERBAU")
					   lRet := .F.
					EndIf
					Exit
				EndIf
			Next
		EndIf
	EndIf

	//Valida se documento de entrada tem condicao de pagamento com adiantamento
	If lRet .and. cPaisLoc $ "BRA|MEX"
		If !cTipo $ "B|D"
			lUsaAdi := A120UsaAdi(cCondicao)
			lRet := A103Adiant(lUsaAdi)
		Endif
	Endif

	//Valida obrigatoriedade de preenchimento do campo F1_CHVNFE
	If lRet .And. alltrim(cEspecie) $ "SPED|CTE|CTEOS"
		DbSelectArea("SX3")
		DbSetOrder(2)
		If MsSeek("F1_CHVNFE")
			If SX3->X3_VISUAL == "A" .And. X3Uso(SX3->X3_USADO) .And. X3Obrigat(SX3->X3_CAMPO) .And. Empty(aNfeDanfe[13])
				Aviso(STR0119,STR0393,{STR0163})
				lRet := .F.
			EndIf
		EndIf

		If lRet .And. lVerChv .And. cFormul == "N" .And. !Empty(aNfeDanfe[13])
			cNFForn := SubStr(aNfeDanfe[13],7,14)			// CNPJ Emitente conforme manual Nota Fiscal EletrÙnica
			nNFNota := Val(SubStr(aNfeDanfe[13],26,9))		// N˙mero da nota conforme manual Nota Fiscal EletrÙnica
			nNFSerie:= Val(SubStr(aNfeDanfe[13],23,3))		// SÈrie da nota conforme manual Nota Fiscal EletrÙnica
			If nNFSerie >= 890 .And. nNFSerie <= 899
				lAvulsa := .T.
			EndIf

			If cTipo == 'B' .Or. cTipo == 'D'
				SA1->(DbSetOrder(1))
				SA1->(MsSeek(xFilial("SA1")+cA100For+cLoja))
				
				If SA1->A1_PESSOA == "J" //Juridico
					cCGC		:= AllTrim(SA1->A1_CGC)
				Else
					cCGC		:= StrZero(Val(SA1->A1_CGC),14)
				Endif
			Else
				If SA2->A2_TIPO == "J" //Juridico
					cCGC		:= AllTrim(SA2->A2_CGC)
				Else
					cCGC		:= StrZero(Val(SA2->A2_CGC),14)
				Endif
			EndIf

			If !Empty(cSerie)

				//Tratamento para verificar se a sÈrie informada È alfanumerica
				For nR := 1 To Len(cSerie)
					If IsAlpha(SubStr(cSerie,nR,1))
						cNFSerie := SubStr(aNfeDanfe[13],23,3) //Carrega a serie da chave NFE para comparar com a serie digitada
						If cSerie != cNFSerie
							lDif := .T. 
						EndIf
						Exit
					EndIf
				Next nR

				If ( cCGC == cNFForn .Or. lAvulsa ) .And. Val(cNFiscal) == nNFNota .And. (Val(cSerie) == nNFSerie) .And. !lDif .Or. Existblock("M103ALTS")
					lRet := .T.
				Elseif (cTipo == 'B' .Or. cTipo == 'D') .And. ( cCGC == cNFForn .Or. lAvulsa ) .And. Val(cNFiscal) == nNFNota .And. (Val(cSerie) == nNFSerie) .And. !lDif // tratamento para beneficiamento e devoluÁ„o
					lRet := .T.
				Else
					Aviso(STR0119,STR0394,{STR0163})
					lRet := .F.
				EndIf
			Else
				Aviso(STR0119,STR0394,{STR0163})
				lRet := .F.
			EndIf
		ElseIf lRet .And. lVerChv .And. cFormul == "S" .And. !Empty(aNfeDanfe[13])
			If Inclui .Or. (l103Class .and. Empty(SF1->F1_DAUTNFE))
    			 Aviso(STR0119,STR0400,{STR0163}) //"Para notas com Form. Prop. = Sim, o campo de Chave NFE deve estar vazio."
     			lRet := .F.
			Endif
		EndIf
	EndIf

	//Valida obrigatoriedade de preenchimento do campo F1_CHVNFE
	If lRet .And. lVtrasef .And. AllTrim(cEspecie) $ "SPED" .And. cFormul == "S"
		lRet := A103CODRSEF(aHeader,aCols)
	EndIf

	If (ExistBlock("MT100TOK")) .And. lMt100Tok
		lPE := ExecBlock("MT100TOK",.F.,.F.,{lRet})
		If ValType(lPE) = "L"
			If ! lPE
				lRet := .F. // Corrigido p/ nao alterar o lRet, se .F., novamente p/ .T.
			EndIf
		EndIf
	EndIf
	lMt100Tok := .T.

	If lRet
		//Bloqueia Pedidos Amarrados ao Processo e checa toler‚ncia
		If ( INCLUI .Or. ALTERA) .And. !l103Class .And. Type("aRegsLock")<>"U"
			lRet := A103LockPC(aHeader,aCols)
		EndIf
	EndIf

	//Verifica se a natureza informada esta bloqueado por ED_MSBLQL ou ED_MSBLQD
	If lRet
		SED->(dbSetOrder(1))
		If !Empty(cNatValid) .And. SED->(MsSeek(xFilial("SED")+cNatValid))
			If !RegistroOk("SED")
				lRet := .F.
			EndIf
    	EndIf
	EndIf
	//Checa se alguma parcela de duplicata gerada pelo documento de entrada j· foi lancado
	//manualmente no modulo de Contas a Pagar. Assim para evitar Error Log por chave dupli-
	//cada o sistema alerta a existencia do pagamaneto e n„o insere o documento de entrada.
	aArea := GetArea()

	If lRet .And. lDuplic .And. !Empty(cPrefixo) .And. TamSX3("F1_SERIE")[1] == 3 .And. (l103Class .Or. INCLUI .Or. ALTERA)
		cQuery := "Select COUNT(E2_NUM) QTDUPLIC From "
		cQuery += RetSqlName("SE2")
		cQuery += " Where E2_FILIAL = '" + xFilial("SE2") + "'"
		cQuery += " And E2_NUM      = '" + cNFiscal + "'"
		cQuery += " And E2_PREFIXO  = '" + cPrefixo + "'"
		cQuery += " And E2_FORNECE  = '" + cA100For + "'"
		cQuery += " And E2_LOJA     = '" + cLoja + "'"
		cQuery += " And E2_TIPO     = '" + Left(MVNOTAFIS,nTamTipo) + "'"
		cQuery += " And D_E_L_E_T_  = ' '"

		cQuery	  := ChangeQuery(cQuery)
		cAliasQry := GetNextAlias()
		dbUseArea( .T., "TOPCONN", TcGenQry( , , cQuery ), cAliasQry, .T., .T. )
		DbSelectArea(cAliasQry)
		(cAliasQry)->(dbGoTop())
		nQtdDupl := (cAliasQry)->QTDUPLIC	//Quantidade de duplicatas lancadas no modulo de Contas a Pagar gerados pela nota.
		dbCloseArea()
		If nQtdDupl > 0
			Help('',1,'A103DVLD')
			lRet := .F.
		EndIf
	EndIf
	RestArea(aArea)

	If lRet
		A103DocEmp(aCols,@aDocEmp)
		If Len(aDocEmp) > 0
			lRet := ShowDivNe(aDocEmp,.F.)
		EndIf
	EndIf

	//ValidaÁıes SIGAPFS
	If lRet .And. __lIntPFS .And. FindFunction("J281VldNat")
		lRet := J281VldNat(cNatValid)
		lRet := lRet .And. J281CondPg(cCondicao, lUsaAdi)
	EndIf
EndIf

//Valida Totvs ColaboraÁ„o
//ClassificaÁ„o de um CT-e onde o valor do frete n„o sera pago.
If lRet
	//Chave CT-e/NF-e
	SDS->(DbSetOrder(2))
	If SDS->(Msseek(xFilial("SDS") + Padr(SF1->F1_CHVNFE,TamSx3("DS_CHAVENF")[1])))
		If SDS->DS_FRETE > 0 .And. SDS->DS_TIPO == "T"
			For nX:=1 To Len(aCols)
				If !aCols[nX,Len(aHeader)+1]
					If !Empty(aCols[nX,GetPosSD1("D1_TES")])
						If Posicione("SF4",1,cFilSF4 + Padr(aCols[nX,GetPosSD1("D1_TES")],TamSx3("F4_CODIGO")[1]),"F4_DUPLIC") <> "N"
							Aviso(STR0459,STR0460,{STR0461})
							lRet := .F.
							Exit
						Endif
					Endif
				EndIf
			Next nX
		Endif
	Endif
Endif

If lRet .And. lDivImp
	If cDivImp <> "0"
		For nX:=1 To Len(aCols)
			If aCols[nX,GetPosSD1("D1_LEGENDA")] == "BR_VERMELHO"
				lRet := .F.
				Exit
			EndIf
		Next nX
		If !lRet
			If cDivImp == "1"
				Aviso(STR0459,cImpMsg+cImpMsg2,{STR0461})
			ElseIf cDivImp == "2"
				lRet := MsgYesNo(cImpMsg+cImpMsg3)
			Endif
		Endif
	Endif
Endif

//Valida RetenÁ„o/DeduÁ„o/Faturamento Direto RM
If lRet .And. Type("lTOPDRFRM") <> "U" .And. lTOPDRFRM
	lRet := A103RDFVLD()
Endif

//verificacao SIGAPLS
if lRet .and. lPLSMT103
	lRet := PLSMT103(1, aHeader, aCols)
endIf

//-- Verifica se existe alguma Entidade Cont·bil bloqueada.
If lRet .And. !Empty(aAuxColSDE) .And. (l103Class .Or. INCLUI) 
	For nY	:=	1 To Len(aAuxColSDE)
		For nX := 1 To Len(aAuxColSDE[nY][2])

			//-- Centro de Custo
			If nPosCC > 0 .And. !Empty(aAuxColSDE[nY][2][nX][nPosCC]) .And. !ValidaBloq(aAuxColSDE[nY][2][nX][nPosCC], dDataBase, "CTT")		
				lRet:= .F.
				Exit
			EndIf

			//-- Conta Cont·bil
			If nPosConta > 0 .And. !Empty(aAuxColSDE[nY][2][nX][nPosConta]) .And. !ValidaBloq(aAuxColSDE[nY][2][nX][nPosConta], dDataBase, "CT1")		
				lRet:= .F.
				Exit
			EndIf 

			//-- Item Cont·bil
			If nPosItCta > 0 .And. !Empty(aAuxColSDE[nY][2][nX][nPosItCta]) .And. !ValidaBloq(aAuxColSDE[nY][2][nX][nPosItCta], dDataBase, "CTD")		
				lRet:= .F.
				Exit
			EndIf 

			//-- Classe de Valor
			If nPosClVl > 0 .And. !Empty(aAuxColSDE[nY][2][nX][nPosClVl]) .And. !ValidaBloq(aAuxColSDE[nY][2][nX][nPosClVl], dDataBase, "CTH")		
				lRet:= .F.
				Exit
			EndIf
			
			For nK := 1 To Len(aEntCtb)

				//-- Entidade Contabil Adicional DB
				cVarAuxDB := "nPEntA" + aEntCtb[nK] + "DB"
				If &(cVarAuxDB) > 0 .And. !Empty(aAuxColSDE[nY][2][nX][&(cVarAuxDB)]) .And. !ValidaBloq(aAuxColSDE[nY][2][nX][&(cVarAuxDB)], dDataBase, "CV0",,, aEntCtb[nK])
					lRet := .F.
					Exit
				EndIf

				//-- Entidade Contabil Adicional CR
				cVarAuxCR := "nPEntA" + aEntCtb[nK] + "CR"
				If &(cVarAuxCR) > 0 .And. !Empty(aAuxColSDE[nY][2][nX][&(cVarAuxCR)]) .And. !ValidaBloq(aAuxColSDE[nY][2][nX][&(cVarAuxCR)], dDataBase, "CV0",,, aEntCtb[nK])
					lRet := .F.
					Exit
				EndIf

			Next nK

			If !lRet
				Exit
			EndIf

		Next nX	
	Next nY	
EndIf

If lRet .And. lCsdXML .And. cTipo == "N" .and. Alltrim(cEspecie) $ "NFE|SPED"
	lExcCsd := .F. //-- Flag de exceÁ„o do consolidador 
	If nItensExc > 0 .And. nTotItens <> nItensExc .And. !Empty(cItemIt)//Nem todos itens s„o exceÁ„o (com isso todos itens precisam ser preenchidos)
		//"H· divergÍncias nos itens " # "Quando o par‚metro MV_CSDXML estiver ativo, torna-se obrigatÛrio o preenchimento do campo Item XML"
		Help(,, "A103ITXMLCFOP",, STR0572 + SubStr(cItemIt,2) , 1, 0,,,,,,{STR0573}) //"H· divergÍncias nos itens " ## "Com o MV_CSDXML ativo, torna-se obrigatÛrio o preenchimento de todos os campos Item XML, caso houver CFOP fora do parametro (MV_EXCCSD) de exceÁ„o."
		lRet := .F.
	Elseif nItensExc > 0 .And. nTotItens == nItensExc//Somente exceÁıes est„o no documento.
		lExcCsd := .T.
	Endif
Endif

if lRet .and. !lExcCsd
	//inÌcio tratativa SEFAZ AM - Consolid. XML
	if lCsdXML .And. cTipo == "N" .and. Alltrim(cEspecie) $ "NFE|SPED"

		if isBlind()
			lRetCSD := A103CSDXML(1, cNFiscal, cSerie, cA100For, cLoja, aCols,aHeader, @oModelCSD)
		else 
			FWMsgRun(, {||  lRetCSD := A103CSDXML(1, cNFiscal, cSerie, cA100For, cLoja, aCols,aHeader, @oModelCSD) }, STR0549, STR0561)//Aguarde...#"Consolidando dados NF x XML"
		endif

		if !lRetCSD//N„o passou no valid do modelo.
			lRet := .F.
		endif
		
		if lRetCSD .and. (INCLUI .or. l103Class) .and. !isBlind()
			//Abre a tela para conferÍncia do usu·rio
			lRetCSD := A103CSDXML(3, cNFiscal, cSerie, cA100For, cLoja, aCols,aHeader,oModelCSD)
			if !lRetCSD
				//Usu·rio n„o confirmou a gravaÁ„o dos dados.
				lRet := .F.
			endif
		endif
		
	endif
endif

RestArea(aAreaSX3)
RestArea(aAreaSC7)
Return(lRet)

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103LinOk  ≥ Autor ≥ Edson Maricate       ≥ Data ≥24.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Rotina de validacao da LinhaOk                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ Nenhum                                                     ≥±±
±±≥          ≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103LinOk()

Local aArea			:= GetArea()
Local aAreaSD2		:= SD2->(GetArea())
Local aAreaSF4		:= SF4->(GetArea())
Local aAreaSB6		:= SB6->(GetArea())
Local aAreaColab	:= GetArea()
Local cRvSB5	    := ""
Local cBlqSG5	    := ""
Local cStatus		:= ""
Local cFilNfOri     := xFilial("SD2")
Local lRet			:= .T.
Local nRet		    := 0
Local nX         	:= 0
Local nPosCod    	:= GetPosSD1("D1_COD")
Local nRevisao  	:= GetPosSD1("D1_REVISAO")
Local nPosLocal  	:= GetPosSD1("D1_LOCAL")
Local nPosATF 		:= GetPosSD1("D1_CBASEAF")
Local nPosPC     	:= GetPosSD1("D1_PEDIDO")
Local nPosQuant  	:= GetPosSD1("D1_QUANT")
Local nPosVUnit  	:= GetPosSD1("D1_VUNIT")
Local nPosTotal  	:= GetPosSD1("D1_TOTAL")
Local nPValDesc  	:= GetPosSD1("D1_VALDESC")
Local nPosTes    	:= GetPosSD1("D1_TES")
Local nPosCfo    	:= GetPosSD1("D1_CF")
Local nPosItemPC 	:= GetPosSD1("D1_ITEMPC")
Local nPosOp     	:= GetPosSD1("D1_OP")
Local nPosIdentB6	:= GetPosSD1("D1_IDENTB6")
Local nPosNFOri  	:= GetPosSD1("D1_NFORI")
Local nPosItmOri 	:= GetPosSD1("D1_ITEMORI")
Local nPosSerOri 	:= GetPosSD1("D1_SERIORI")
Local nPosLote   	:= GetPosSD1("D1_NUMLOTE")
Local nPosLoteCtl	:= GetPosSD1("D1_LOTECTL")
Local nPosDtvalid   := GetPosSD1("D1_DTVALID")
Local nPosConta  	:= GetPosSD1("D1_CONTA")
Local nPosCC     	:= GetPosSD1("D1_CC")
Local nPosCLVL   	:= GetPosSD1("D1_CLVL")
Local nPosItemCTA	:= GetPosSD1("D1_ITEMCTA")
Local nPosItemNF	:= GetPosSD1("D1_ITEM")
Local nPosPCCENTR   := GetPosSD1("D1_PCCENTR")
Local nPosITPCCEN   := GetPosSD1("D1_ITPCCEN")
Local nPosOrdem     := GetPosSD1("D1_ORDEM")
Local nFciCod       := GetPosSD1("D1_FCICOD")
Local nPosEC05DB    := GetPosSD1("D1_EC05DB")
Local nPosEC05CR    := GetPosSD1("D1_EC05CR")
Local nPosEC06DB    := GetPosSD1("D1_EC06DB")
Local nPosEC06CR    := GetPosSD1("D1_EC06CR")
Local nPosEC07DB    := GetPosSD1("D1_EC07DB")
Local nPosEC07CR    := GetPosSD1("D1_EC07CR")
Local nPosEC08DB    := GetPosSD1("D1_EC08DB")
Local nPosEC08CR    := GetPosSD1("D1_EC08CR")
Local nPosEC09DB    := GetPosSD1("D1_EC09DB")
Local nPosEC09CR    := GetPosSD1("D1_EC09CR")
Local nPosDigit     := GetPosSD1("D1_DTDIGIT")
Local nPosFilOri	:= GetPosSD1("D1_FILORI")
Local nItApoEsp     := 0
Local cFilOri		:= xFilial("SD2")
Local nSldQtdDev 	:= 0
Local nSldVlrDev 	:= 0
Local nVlUnitVen	:= 0
Local nVlUnACols 	:= 0 
Local nItensNf		:= 0
Local lPCNFE     	:= GetNewPar( "MV_PCNFE", .F. ) //-- Nota Fiscal tem que ser amarrada a um Pedido de Compra ?
Local dDataBloq     := GetNewPar("MV_ATFBLQM",CTOD("")) //Data de Bloqueio da MovimentaÁ„o - MV_ATFBLQM
Local lRevProd      := SuperGetMv("MV_REVPROD",.F.,.F.)
Local cTesPcNf      := SuperGetMV("MV_TESPCNF") // Tes que nao necessita de pedido de compra amarrado
Local lGspInUseM 	:= If(Type('lGspInUse')=='L', lGspInUse, .F.)
Local nPreco        := 0
Local cAltPrcCtr    := SuperGetMv("MV_ALTPRCC")
Local nPosAFN  	    := 0
Local nPosQtde 	    := 0
Local nTotAFN		:= 0
Local nA			:= 0
Local cRetTes       := ""
Local lVlrZero		:= .F.
Local lTColab		:= .F.
Local i				:= 0
Local lLoteVenc	    := SuperGetMV("MV_LOTVENC") == "S"
Local lDAmarCt		:= SuperGetMV("MV_DAMARCT",.F.,.F.)
Local cVldPDev		:= SuperGetMV("MV_VLDPDEV",.F.,"T")
Local lDCLNew		:= SuperGetMV("MV_DCLNEW",.F.,.F.)
Local lColab 	    := l103Auto .And. aScan(aAutoCab, {|x| x[1] == "COLAB" .And. x[2] == "S"}) > 0
Local aEntid	 	:= {}
Local aEntid2	 	:= {}
Local lIntGC		:= IIf((SuperGetMV("MV_VEICULO",,"N")) == "S",.T.,.F.)
Local lCtb105Mvc	:= FindFunction("CTB105MVC")
Local lDHQInDic     := AliasInDic("DHQ") .And. SF4->(ColumnPos("F4_EFUTUR") > 0)
Local lMt103Com     := FindFunction("A103FutVld")
Local nLinAtv		:= 0
Local cPedC5C7		:= ""
Local aIndCod		:= {}
Local nLinAtu		:= 0
Local lDtNT2006		:= A103DNT2006()
Local lVTESDUP		:= SuperGetMv("MV_VTESDUP", .F., .F.)
Local cEASYFIN		:= SuperGetMv("MV_EASYFIN")
Local c2DUPREF		:= SuperGetMv("MV_2DUPREF")
Local lCsdXML 		:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA") .and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")
Local lMT103SF2		:= ExistBlock('MT103SF2')
Local cExcCFOP  	:= SuperGetMV("MV_EXCCSD",.F.,"1551|1555|1556|1577|2551|2555|2556|2557")
Local lMvLocBac		:= SuperGetMv("MV_LOCBAC",.F.,.F.) //IntegraÁ„o com MÛdulo de LocaÁıes SIGALOC
Local lFcLOCM007	:= FindFunction("LOCM007")
Local lMT103PBLQ	:= .F.

//Quando chamado pelo Modulo de Veiculos, desconsiderar tratamento/validacao do Pedido de Compra na NF Entrada
If lIntGC .and. lPCNFE
	If ExistFunc("FM_PILHA") .and. FM_PILHA("VEIXA")
		lPCNFE := .f.
	Endif
Endif

//Ponto de entrada para alterar as TES que sao permitidas na inclusao de nota avulsa (sem pedido de compra)
If ExistBlock("MT103TPC")
	cRetTes := ExecBlock("MT103TPC",.F.,.F.,{cTesPcNf})
	If ValType( cRetTes ) == "C"
		cTesPcNf := cRetTes
	EndIf
EndIf

//Se a rotina automatica for configurada para exibicao de tela (lWhenGet = .T.) e o parametro MV_PCNFE estiver
//ativo, realiza as validacoes dos campos D1_PEDIDO e D1_ITEMPC apenas apos a confirmacao da inclusao, e
//nao no carregamento da tela.
If l103auto
	lVldAfter   := IIf(Type("lVldAfter") == "L" , lVldAfter, .F. )
	lVldAfter   := lVldAfter .And. lPCNFE
Else
	lVldAfter   := .F. 
EndIf

If !Empty(c103Tp) .And. c103Tp <> cTipo
	cTipo := c103Tp
Endif

If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. cFormul == "S" .And. !l103Class .And. lDtNT2006
	For nA := 1 To Len(aCols)
		If !aCols[nA,Len(aCols[nA])]
			If (cTipo $ "C|D|N" .And. !Empty(aCols[nA,nPosNFOri]))
				nLinAtv++
				If nLinAtu == 0
					nLinAtu := nA
				Endif
			Endif
		Endif
	Next nA

	If nLinAtv == 0 
		If !cTipo $ "N|B|D"
			aInfAdic[16] := ""
			aInfAdic[17] := Space(06)
		Endif
	Elseif nLinAtv > 0 .And. Empty(aInfAdic[16]) .And. Empty(aInfAdic[17])
		If cTipo $ "C|D|N" 
			If !Empty(aCols[nLinAtu,nPosNFOri])
				cPedC5C7 := GetAdvFVal("SD2","D2_PEDIDO",xFilial("SD2") + aCols[nLinAtu,nPosNFOri] + aCols[nLinAtu,nPosSerOri] + ca100For + cLoja + aCols[nLinAtu,nPosCod] + aCols[nLinAtu,nPosItmOri],3)
				If !Empty(cPedC5C7)
					aIndCod := GetAdvFVal("SC5",{"C5_INDPRES","C5_CODA1U"},xFilial("SC5") + ca100For + cLoja + cPedC5C7,3)
					If Len(aIndCod) > 0
						aInfAdic[16] := aIndCod[1]
						aInfAdic[17] := aIndCod[2]
					Endif
				Endif
			Endif
		Endif
	Endif
	Eval(bRefresh,10)
Endif

//Verifica preenchimento dos campos da linha do acols
If CheckCols(n,aCols)
	SF4->(DbSetOrder(1))
	SC2->(DbSetOrder(1))
	If !aCols[n][Len(aCols[n])]
		//Verifica a permissao do armazem
		lRet := MaAvalPerm(3,{aCols[n][nPosLocal],aCols[n][nPosCod]})
		
		//Verifica se o produto e MOD
		If lRet .And. IsProdMOD(aCols[n][nPosCod])
			Help("  ",1,"NAOMVMOD")//"Produtos de M„o-de-Obra n„o podem ser utilizados para esta operaÁ„o."
			lRet := .F.
		EndIf

		if lCsdXML .and. cTipo == "N" .and. Alltrim(cEspecie) $ "NFE|SPED" .And. !(AllTrim(aCols[n,nPosCfo]) $ cExcCFOP)
			if !D3Q->(MsSeek(fwxFilial("D3Q") + aCols[n][nPosCod]))
				lRet := .F.
				Help(" ",1,"CSDCONV",,STR0548,1,0)//"N„o h· cadastro de convers„o para este produto. O cadastro È obrigatÛrio quando MV_CSDXML = .T."
			endif
		endif

		//E obrigatorio o preenchimento da quantidade para notas do tipo Complemento de Preco
		If SF1->(ColumnPos("F1_TPCOMPL")) > 0 .And. cTipo == "C" .And. cTpCompl == "2"
			If Empty(aCols[n][nPosQuant])
				Help(" ",1,"COMPQTD",,STR0457,1,0) // Este texto pode ser retirado a partir do release 12.1.16
				lRet := .F.
			EndIf
		EndIf

		// Valida qtde com a Integracao PMS
		If lRet .And. IntePms() .And. Len(aRatAFN)>0
			If Len(aHdrAFN) == 0
				aHdrAFN := FilHdrAFN()
			Endif
			nPosAFN  := Ascan(aRatAFN,{|x|x[1]==aCols[n][nPosItemNF]})
			nPosQtde := Ascan(aHdrAFN,{|x|Alltrim(x[2])=="AFN_QUANT"})

			If (nPosAFN > 0) .And. (nPosQtde > 0)
				nPPed := GetPosSD1("D1_PEDIDO")
				nPItP := GetPosSD1("D1_ITEMPC")
				nTotAFN	:= 0
				For nA := 1 To Len(aRatAfn[nPosAFN][2])
					If !aRatAFN[nPosAFN][2][nA][LEN(aRatAFN[nPosAFN][2][nA])]
						nTotAFN	+= aRatAfn[nPosAFN][2][nA][nPosQtde]
					EndIf
				Next nA

				If nPosQuant>0
					If !SuperGetMV("MV_DIFAFN",,.T.)
						If nPPed > 0 .And. nPItP > 0
							If !PMSNFSA(aCols[n][nPPed],aCols[n][nPItP])[1]
								If nTotAFN > 0 .AND. nTotAFN <> aCols[n][nPosQuant]
									Help("   ",1,"DIFAFN")
									lRet := .F.
								EndIf
							Endif
						Endif
					Else
						If nPPed > 0 .And. nPItP > 0
							If !PMSNFSA(aCols[n][nPPed],aCols[n][nPItP])[1]
								If nTotAFN > aCols[n][nPosQuant]
									Help("   ",1,"PMSQTNF")
									lRet := .F.
								Endif
							Endif
						Endif
					EndIf
				Endif
			Endif
		Endif

		//Quando Informado Armazem em branco considerar o B1_LOCPAD
		If lRet .And. nPosLocal>0 .And. Empty(aCols[n][nPosLocal])
			SB1->(DbSetOrder(1))
			If nPosCod>0 .And.;
					SB1->(MsSeek(xFilial("SB1")+aCols[n][nPosCod]))

				aCols[n][nPosLocal] := SB1->B1_LOCPAD
				If Valtype(l103Auto) == "L" .And. !l103Auto
					Aviso(OemToAnsi(STR0119),OemToAnsi(STR0225),{STR0461}) //"O Armazem informado e Invalido, o campo sera ajustando com o armazem padr„o do cadastro de produtos"
				EndIf
			EndIf
		EndIf
		If lRet .And. !ExistCpo("NNR",aCols[n][nPosLocal]) 
			lRet := .F.
		EndIf
		
		//Flag que indica se o valor da nota fiscal podera ser zero
		If cPaisLoc == "BRA"
			If lRet .And. SF4->(MsSeek(xFilial("SF4")+aCols[n][nPostes]))
				lVlrZero	:=	Iif(SF4->F4_VLRZERO == "1", .T., .F.)
			Endif
		EndIf

		//Valida ativo digitado em NF de garantia estendida. (Agrega valor no bem)
		if lRet .and. nPosATF > 0 .and. cTipo == "N" .and. (INCLUI .or. l103Class) .and. FindFunction("VldBemCTE")
			if !empty(aCols[n][nPosATF])
				//FunÁ„o de validaÁ„o do ativo fixo.
				// .F. =  Ativo n„o existe ou est· classificado.
				// .T. = Ativo existe e est· pendente de classificaÁ„o, podendo ser alterado.
				lRet := VldBemCTE(left(aCols[n][nPosATF],TamSx3("N1_CBASE")[1]),right(aCols[n][nPosATF],TamSx3("N1_ITEM")[1]))
				if !lRet
					Help(" ",1,"A103VLDATF",,STR0567 + Alltrim(aCols[n][nPosATF]) + STR0568,1,0) //"O ativo " # " n„o existe ou possui status que n„o permite alteraÁ„o."
				endif
			endif
		endif

		//Verifica se valida ou nao o aCols a partir das validacoes do aHeader
		Iif( nPosConta  > 0  , aAdd(aEntid, aCols[n,nPosConta]),  aAdd(aEntid," ") )
		Iif( nPosCC     > 0  , aAdd(aEntid, aCols[n,nPosCC]),     aAdd(aEntid," ") )
		Iif( nPosItemCta> 0  , aAdd(aEntid, aCols[n,nPosItemCta]),aAdd(aEntid," ") )
		Iif( nPosClVl   > 0  , aAdd(aEntid, aCols[n,nPosClVl]),   aAdd(aEntid," ") )
		Iif( nPosEC05DB > 0  , aAdd(aEntid, aCols[n,nPosEC05DB]), aAdd(aEntid," ") )
		Iif( nPosEC06DB > 0  , aAdd(aEntid, aCols[n,nPosEC06DB]), aAdd(aEntid," ") )
		Iif( nPosEC07DB > 0  , aAdd(aEntid, aCols[n,nPosEC07DB]), aAdd(aEntid," ") )
		Iif( nPosEC08DB > 0  , aAdd(aEntid, aCols[n,nPosEC08DB]), aAdd(aEntid," ") )
		Iif( nPosEC09DB > 0  , aAdd(aEntid, aCols[n,nPosEC09DB]), aAdd(aEntid," ") )

		Iif( nPosConta  > 0  , aAdd(aEntid2, aCols[n,nPosConta]),  aAdd(aEntid2," ") )
		Iif( nPosCC     > 0  , aAdd(aEntid2, aCols[n,nPosCC]),     aAdd(aEntid2," ") )
		Iif( nPosItemCta> 0  , aAdd(aEntid2, aCols[n,nPosItemCta]),aAdd(aEntid2," ") )
		Iif( nPosClVl   > 0  , aAdd(aEntid2, aCols[n,nPosClVl]),   aAdd(aEntid2," ") )
		Iif( nPosEC05CR > 0  , aAdd(aEntid2, aCols[n,nPosEC05CR]), aAdd(aEntid2," ") )
		Iif( nPosEC06CR > 0  , aAdd(aEntid2, aCols[n,nPosEC06CR]), aAdd(aEntid2," ") )
		Iif( nPosEC07CR > 0  , aAdd(aEntid2, aCols[n,nPosEC07CR]), aAdd(aEntid2," ") )
		Iif( nPosEC08CR > 0  , aAdd(aEntid2, aCols[n,nPosEC08CR]), aAdd(aEntid2," ") )
		Iif( nPosEC09CR > 0  , aAdd(aEntid2, aCols[n,nPosEC09CR]), aAdd(aEntid2," ") )

		//Verifica se o produto est† sendo inventariado.
		If lRet
			Do Case
			Case nPosCod>0 .And. nPosLocal>0 .And.;
					BlqInvent(aCols[n][nPosCod],aCols[n][nPosLocal])

				Help(" ",1,"BLQINVENT",,aCols[n][nPosCod]+STR0058+aCols[n][nPosLocal],1,11) //" Almox: "
				lRet := .F.
			
			//Analisa se o tipo do armazem permite a movimentacao
			Case  nPosCod>0 .And. nPosLocal>0 .And. nPosTes>0 .And. nPosOP>0  .And. ;
			     AvalBlqLoc(aCols[n][nPosCod],aCols[n][nPosLocal],aCols[n][nPosTES],,,,,,,aCols[n][nPosOp])
				lRet := .F.
				
				//Verifica os campos obrigatorios
			Case (nPosCod>0 .And. Empty(aCols[n][nPosCod])) .Or. ;
					(nPosQuant>0 .And. nPosTes>0 .And. Empty(aCols[n][nPosQuant]).And.cTipo$"NDB".And.!MaTesSel(aCols[n,nPosTes])).Or. ;
					(nPosVUnit>0 .And. Empty(aCols[n][nPosVUnit]) .And. !lVlrZero) .Or. ;
					(nPosQuant>0 .And. nPosVUnit>0 .And. nPosTotal>0 .And. !Empty(aCols[n][nPosQuant]) .And. Empty(aCols[n][nPosTotal]) .And. ;
					 NoRound( aCols[n][nPosQuant] * aCols[n][nPosVUnit],TamSX3("D1_TOTAL")[2] ) <> aCols[n][nPosTotal]) .And. !lVlrZero .Or. ;
					(nPosQuant>0 .And. nPosVUnit>0 .And. nPosTotal>0 .And. Empty(aCols[n][nPosQuant]) .And. ( Empty(aCols[n][nPosVUnit]) .Or. ;
					 (Empty(aCols[n][nPosTotal]))) .And. !lVlrZero ) .Or.;
					(nPosCFO>0 .And. Empty(aCols[n][nPosCFO]))  .Or. ;
					(nPosLocal>0 .And. Empty(aCols[n][nPosLocal])).Or. ;
					(nPosTES>0 .And. Empty(aCols[n][nPosTES]))

				Help("  ",1,"A100VZ")
				lRet := .F.
				//Verifica o codigo da TES
			Case nPosTes>0 .And.;
					aCols[n][nPosTes] > "500"

				Help("   ",1,"A100INVTES")
				lRet := .F.

			Case nPostes>0 .And.;
					!SF4->(MsSeek(xFilial("SF4")+aCols[n][nPostes]))

				Help("   ",1,"D1_TES")
				lRet := .F.

				//Verifica o Pedido de compra
			Case nPosPc>0 .And. nPosItemPC>0 .And.;
					!Empty(aCols[n][nPosPc]) .And. Empty(aCols[n][nPosItemPC]) .And. !lVldAfter

				Help("  ",1,"A100PC")
				lRet := .F.
				
				//Verifica o valor total
			Case cPaisLoc <> "BRA".AND. nPosTes>0 .And. nPosVUnit>0 .And. nPosQuant>0 .And. nPosTotal>0 .And. ;
					cTipo <> "C" .And.!MaTesSel(aCols[n,nPosTes]) .And. ;
					Round(aCols[n][nPosVUnit]*aCols[n][nPosQuant],SuperGetMV("MV_RNDLOC")) <> Round(aCols[n][nPosTotal],SuperGetMV("MV_RNDLOC"))

				Help(" ",1,"A100VALOR")
				lRet := .F.
				
				//Verifica o preenchimento da Nota Original
			Case nPosNFOri>0 .And.;
					!lGspInUseM .And. cTipo == 'D' .And. cPaisLoc <> "ARG" .And. Empty(aCols[n][nPosNFOri]) .And. ;
					!(("|"+AllTrim(StrTran(aCols[n][nPosCfo],".",""))+"|") $ "|1201|1202|1410|1411|5921|6921|")		//De acordo com a legislaÁ„o, n„o È obrigatÛrio o preenchimento do doc. de origem para os CFOPs 1201,1202,1410,1411,5921 e 6921 em NF devoluÁ„o

				Help("  ",1,"A100NFORI")
				lRet := .F.
				
				//Verifica a Ratreabilidade
			Case nPosNFOri>0 .And. nPosLote>0 .And.;
					!lGspInUseM .And. SF4->F4_ESTOQUE == "S" .And. cTipo == 'D' .And. (Rastro(aCols[n][nPosCod],"S")) .And. Empty(aCols[n][nPosLote])

				Help(" ",1,"A100SBLOT",,STR0498,1,0)
				lRet := .F.

			Case nPosCod>0 .And. nPosLoteCtl>0 .And.;
					!lGspInUseM .And. SF4->F4_ESTOQUE == "S" .And. cTipo == 'D' .And. (Rastro(aCols[n][nPosCod],"L")) .And. Empty(aCols[n][nPosLoteCtl])

				Help(" ",1,"A100S/LOT")
				lRet := .F.

			Case nPosOp>0 .And.;
				!lGspInUseM .And. !Empty(aCols[n][nPosOp]) .And. (!SC2->(dbSeek(xFilial("SC2")+aCols[n][nPosOp])) .Or. !Empty(SC2->C2_DATRF))

				lRet := .F.
				//Integracao com SIGAMNT - NG Informatica
				If nPosOrdem > 0
					If SuperGetMV("MV_NGMNTES",.F.,"N") == "S" .and. SuperGetMV("MV_NGMNTPC",.F.,"N") == "S" .and. !Empty(aCols[n][nPosOrdem])
				         If aCols[n][nPosOrdem] == Substr(aCols[n][nPosOp],1,Len(SC2->C2_NUM))
				         	lRet := .T.
							dDTULMES := SuperGetMV("MV_ULMES",.F.,STOD(""))
							If !Empty(dDTULMES) .and. SC2->C2_DATRF <= dDTULMES
								lRet := .F.
							Endif
				         Endif
					Endif
				Endif

				If !lRet
					Help(" ",1,"A100OPEND")
					lRet := .F.
				Endif

			Case  !lColab .and. !lGspInUseM .And. nPosNFOri>0 .And. cTipo $'CPI' .And. !Len(aCompFutur) > 0 .And.;
				  Empty(aCols[n][nPosNFOri]) .And. !A103ExsSF8(cNFiscal,cSerie,cA100For,cLoja)

				Help(" ",1,"A100COMPIP")
				lRet := .F.

			Case nPosPC > 0 .and. nPosItemPC > 0 .and. !Empty(aCols[n][nPosPc]) .And. !Empty(aCols[n][nPosItemPC])

				if(Alltrim(aCols[n][nPosCod]) <> Alltrim(GetAdvFVal("SC7","C7_PRODUTO",xFilEnt(fwxFilial("SC7"),"SC7") + aCols[n][nPosCod] + aCols[n][nPosPc] + aCols[n][nPosItemPC],19)))
					//--N„o È permitido a alteraÁ„o de produto vinculado a pedido de compra. Verifique a linha: # DesfaÁa a alteraÁ„o do produto ou delete a linha alterada.
					Help(,,"A103PCPROD",,STR0575 + aCols[n][nPosItemNF], 1, 0,,,,,,{STR0576})
					lRet := .F.
				ElseIf !CtbAmarra(aCols[n,nPosConta],aCols[n,nPosCC],aCols[n,nPosItemCTA],aCols[n,nPosCLVL],/*lPosiciona*/,/*lHelp*/,/*lValidLinOk*/,aEntid2)
					lRet := .F.
				endif

			Case nPosIdentB6>0 .And.;
					!lGspInUseM .And. SF4->F4_PODER3 == 'D' .And. Empty(aCols[n][nPosIdentB6])

				Help(" ",1,"A103USARF7")
				lRet := .F.

			Case nPosQuant>0 .And.;
					SF4->F4_ATUATF == 'S' .And. SF4->F4_BENSATF == "1" .And. INT(aCols[n][nPosQuant]) <> aCols[n][nPosQuant]

				Help(" ",1,"A103BENATF")
				lRet := .F.

			Case nPosCod>0 .And. nPosLocal>0 .And.;
					SF4->F4_ESTOQUE == 'S' .And. !A103Alert(Acols[n][nPosCod],aCols[n][nPosLocal],( Type('l103Auto') <> 'U' .And. l103Auto ))

				lRet := .F.

			Case nPosTes>0 .And. nPosTotal>0 .And. nPosVUnit>0 .And. nPosQuant>0 .And.;
					cTipo$'NDB' .And. !MaTesSel(aCols[n,nPosTes]) .And. (aCols[n][nPosTotal]>(aCols[n][nPosVUnit]*aCols[n][nPosQuant]+0.49);
					.Or. aCols[n][nPosTotal]<(aCols[n][nPosVUnit]*aCols[n][nPosQuant]-0.49))

				Help("  ",1,'TOTAL')
				lRet := .F.

			Case nPosTes>0 .And. nPosQuant>0 .and.;
					MaTesSel(aCols[n,nPosTes]) .And. aCols[n][nPosQuant] > 0 .And. !IsInCallStack("A103DEVOL")

				Help("  ",1,'A103ZROTES')
				lRet := .F.

			Case nPosConta <> 0 .And. nPosCC>0 .And. nPosItemCta <> 0 .And. nPosClVl <> 0 .And.;
					!lGspInUseM .And. ((!lDAmarCt .And. (!CtbAmarra(aCols[n,nPosConta],aCols[n,nPosCC],aCols[n,nPosItemCTA],aCols[n,nPosCLVL],/*lPosiciona*/,/*lHelp*/,/*lValidLinOk*/,aEntid) .Or.;
					!CtbAmarra(aCols[n,nPosConta],aCols[n,nPosCC],aCols[n,nPosItemCTA],aCols[n,nPosCLVL],/*lPosiciona*/,/*lHelp*/,/*lValidLinOk*/,aEntid2))) .Or.;
					(!Empty(aCols[n,nPosConta]) .And. Iif(lCtb105Mvc,CTB105MVC(.T.),.T.) .And. !Ctb105Cta(aCols[n,nPosConta])) .Or.;
					(!Empty(aCols[n,nPosCC]) .And. Iif(lCtb105Mvc,CTB105MVC(.T.),.T.) .And. !Ctb105CC(aCols[n,nPosCC])) .Or.;
					(!Empty(aCols[n,nPosItemCTA]) .And. Iif(lCtb105Mvc,CTB105MVC(.T.),.T.) .And. !Ctb105Item(aCols[n,nPosItemCTA])) .Or.;
					(!Empty(aCols[n,nPosCLVL]) .And. Iif(lCtb105Mvc,CTB105MVC(.T.),.T.) .And. !Ctb105ClVl(aCols[n,nPosCLVL])))

				lRet := .F.
				
			Case !lGspInUseM .And.nPosPC>0 .And. nPosTes>0 .And. !IsInCallStack("EICDI154") .And.;
				 cTipo == 'N' .And. lPCNFE .And. Empty(aCols[n,nPosPC]) .And. SF4->F4_PODER3=="N" .And. !lVldAfter
				
				If lDHQInDic 
					If SF4->F4_EFUTUR != "2"	
						If Empty(cTesPcNf) .Or. (!Empty(cTesPcNf) .And. !aCols[n][nPosTes] $ cTesPcNf)
							Aviso(STR0119,STR0186,{STR0163}, 2 ) //-- "Atencao"###"Informe o No. do Pedido de Compras ou verifique o conteudo do parametro MV_PCNFE"###"Ok"
							lRet := .F.
						Endif
					EndIf
				Else
					If Empty(cTesPcNf) .Or. (!Empty(cTesPcNf) .And. !aCols[n][nPosTes] $ cTesPcNf)
						Aviso(STR0119,STR0186,{STR0163}, 2 ) //-- "Atencao"###"Informe o No. do Pedido de Compras ou verifique o conteudo do parametro MV_PCNFE"###"Ok"
						lRet := .F.
					EndIf	
				EndIf
			Case nPosCod>0 .And. !lGspInUseM  .And. SB1->(MsSeek(xFilial("SB1")+aCols[n][nPosCod]))
				If !RegistroOk("SB1",.F.)
					If ExistBlock("MT103PBLQ")
						lMT103PBLQ:=ExecBlock("MT103PBLQ",.F.,.F.,{aCols[n][nPosCod]})
						If !lMT103PBLQ 
							lRet := .F.
						Else
							lRet := lMT103PBLQ
						Endif
					Else
						lRet := .F.
					Endif
				Endif
			Case nPosPCCENTR>0 .And. nPosITPCCEN>0 .And. !lGspInUseM
			     If !A103VALPCC(n)
					lRet := .F.
				 EndIf

			OtherWise
				lRet := .T.
			EndCase
		Endif
		
		// Verifica se existe bloqueio pelo parametro MV_ATFBLQM - Validacao incluida em 03/08/2015 changeset 320011 release 12
		If lRet .And. SF4->F4_ATUATF == "S" .And. !Empty(dDataBloq) .And. aCols[n][nPosDigit] <= dDataBloq
			Help(" ",1,"ATFCTBBLQ")	// Processo bloqueado pelo Calendario Contabil ou pelo parametro de bloqueio nesta data ou periodo.
			lRet := .F.
		EndIf

		If lRet .And. cPaisLoc == "BRA" .And. cEASYFIN == "N" .And. "SF1->F1_SERIE" $ c2DUPREF .And. SF4->F4_DUPLIC == "S" .And. lVTESDUP
			lRet := A103F50NUM(cSerie,cNFiscal,cA100For,cLoja)
		EndIf

		// Se nota de remessa de compra com entrega futura
		If lDHQInDic .And. lMt103Com .And. SF4->F4_EFUTUR = "2"
			// Verifica se a quantidade n„o est· acima do saldo a receber (LinOK)
			If !A103FutVld(.F., aCompFutur, N, .F.)
				lRet := .F.
			EndIf
		EndIf

		//Verifica se o documento possui origem
		If nPosNfOri > 0 .And. !Empty(aCols[n][nPosNfOri])
			If nPosFilOri > 0 .And. !Empty(aCols[n][nPosFilOri])
				cFilOri := aCols[n][nPosFilOri]
			Endif
		Endif

		//Verifica a quantidade e o valor devolvido
		If nPosNFOri>0 .And. nPosSerOri>0 .And. nPosCod>0 .And. nPosItmOri>0 .And. nPosQuant>0 .And. nPosTotal>0 .And.;
				lRet .And. !lGspInUseM .And. lRet .And. cTipo=="D" .And. !Empty(aCols[n][nPosNFOri])

			DbSelectArea("SF2")
			DbSetOrder(1)

			If lMT103SF2 //para posicionamento na SF2 pelo cliente
				ExecBlock("MT103SF2",.F.,.F.,{ aCols , nPosNfOri , nPosSerOri, 'MATA103' })
			Else	
				MsSeek(xFilial("SF2") + aCols[n][nPosNfOri] + aCols[n][nPosSerOri] )
			EndIf
			
			//Verifica se a data de devoluÁ„o È maior que a data logada no sistema
			If SF2->F2_EMISSAO > dDatabase
				Help( " ", 1, "A103EMISSAO", , STR0527, 1, 0 ) //"Documento de origem com data superior a data base."
				lRet := .F.
			EndIf

			DbSelectArea("SD2")
			DbSetOrder(3)
			If MsSeek(xFilial("SD2", cFilOri)+aCols[n][nPosNFOri]+aCols[n][nPosSerOri]+SF2->F2_CLIENTE+SF2->F2_LOJA+aCols[n][nPosCod]+aCols[n][nPosItmOri])
				nSldQtdDev := SD2->D2_QUANT-SD2->D2_QTDEDEV
				nSldVlrDev := SD2->D2_TOTAL+SD2->D2_DESCON+SD2->D2_DESCZFR-SD2->D2_VALDEV
				nVlUnitVen := SD2->D2_PRCVEN+((SD2->D2_DESCON+SD2->D2_DESCZFR) / SD2->D2_QUANT)
				nVlUnitVen := a410Arred(nVlUnitVen,"D1_VUNIT")
				For nX := 1 to Len(aCols)
					If !aCols[nX][Len(aCols[nX])] .And.;
							aCols[nX][nPosCod]    == SD2->D2_COD   .And. ;
							aCols[nX][nPosNfOri]  == SD2->D2_DOC   .And. ;
							aCols[nX][nPosSerOri] == SD2->D2_SERIE .And. ;
							Alltrim(aCols[nX][nPosItmOri]) == Alltrim(SD2->D2_ITEM)
						If n <> nX
							nSldQtdDev -= aCols[nX][nPosQuant]
							nSldVlrDev -= aCols[nX][nPosTotal]
						EndIf
					EndIf
				Next nX
				
				//Verifica o valor devolvido
				If cVldPDev == "U" 	//-- Valida pelo preco unitario (devera ser igual)
					nVlUnACols := a410Arred(aCols[n,nPosVUnit],"D1_VUNIT") //Arredonda o valor total de acordo com as casas decimais, ao utilizar a opÁ„o retornar
					If QtdComp(nVlUNaCols) # QtdComp(nVlUnitVen)
						Help(" ",1,"A410UNIDIF")
						lRet := .F.
					EndIf
				Else				//-- Valida pelo preco total (devera ser menor ou igual ao saldo a receber
					If QtdComp(aCols[n][nPosTotal]) > QtdComp(nSldVlrDev)
						Help(" ",1,"A410UNIDIF")
						lRet := .F.
					EndIf
				EndIf
				
				//Verifica a quantidade
				If SD2->D2_QTDEDEV == SD2->D2_QUANT  .And. SD2->D2_QUANT<>0
					lRet := .F.
					Help(" ",1,"A100QDEV")
				Else
					If aCols[n][nPosQuant] > nSldQtdDev
						lRet := .F.
						Help(" ",1,"A100DEVPAR",,Str(nSldQtdDev,18,2),4,1)
					EndIf
				EndIf
				If cPaisLoc == "BRA"
					If nFciCod > 0 .AND. !Empty(SD2->D2_FCICOD)
						aCols[n][nFciCod] := SD2->D2_FCICOD
					EndIf
				EndIf

				//Validacao da NF de Origem Mais NegÛcios
				If lRet .And. FindFunction( "RskIsActive" ) .And. RskIsActive()
					lRet := RskVdLNDev(SD2->D2_FILIAL, SD2->D2_DOC, SD2->D2_SERIE, SD2->D2_CLIENTE, SD2->D2_LOJA)
				EndIf    

			ElseIf MsSeek(xFilial("SD2", cFilOri)+aCols[n][nPosNFOri]+aCols[n][nPosSerOri]+SF2->F2_CLIENTE+SF2->F2_LOJA)
				While SD2->(!Eof()) .And.;										// Encontrou a nota e o item,
					SD2->D2_FILIAL == cFilNfOri .And.;					// porem o codigo do produto esta diferente.
					SD2->D2_DOC == aCols[n][nPosNFOri] .And.;					// Neste caso nao deve permitir a devolucao.
					SD2->D2_SERIE == aCols[n][nPosSerOri] .And.;
					SD2->D2_CLIENTE == SF2->F2_CLIENTE .And.;
					SD2->D2_LOJA == SF2->F2_LOJA
					If SD2->D2_ITEM == AllTrim(aCols[n][nPosItmOri])
						AVISO(STR0119,STR0401,{STR0238})						// Atencao # O codigo do produto para devolucao deve ser igual ao do item da nota original. # Ok
						lRet := .F.
					EndIf  
					SD2->(dbSkip())
				EndDo
			Else
    	    	SX6->(DbSetOrder(1))
    	    	If !SX6->(dbSeek(xFilial("SX6")+"MV_VLDNFO"))
    	    		SX6->(dbSeek(Space(FWGETTAMFILIAL)+"MV_VLDNFO"))
    	    	EndIf
				If !Empty(aCols[n][nPosItmOri]) .And. SX6->(EOF())
					lRet := .F.
					Help(" ",1,"A100ITDEV")
				EndIf
			EndIf
			If lRet .AND. nPosTES>0 .AND. SF4->F4_PODER3 $ 'R'
				lRet := .F.
				Help(" ",1,"A103TESNFD")
			EndIf
		EndIf

		//Verifica se a nota de frete foi gerada pelo TOTVS Colaboracao
		If cTipo $ "C" .And. l103Class
			aAreaColab := GetArea()
			DbSelectArea("SDS")
			DbSetOrder(1)
			If MsSeek(xFilial("SDS")+cNFiscal+SerieNfId("SD1",4,"D1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja)
				lTColab := .T.
				DbSelectArea("SD1")
				DbSetOrder(1)
				MsSeek(xFilial("SD1")+cNFiscal+cSerie+cA100For+cLoja+aCols[n][nPosCod]+aCols[n][nPosItemNf])
				If aCols[n][nPosNfOri] != SD1->D1_NFORI .Or. aCols[n][nPosSerOri] != SD1->D1_SERIORI .Or. aCols[n][nPosItmOri] != SD1->D1_ITEMORI		// Verifica se alterou a nota original manualmente
					lTColab := .F.
				EndIf
			EndIf
			RestArea(aAreaColab)
		EndIf

		//Verifica Notas de Complemento/DevoluÁ„o vinculadas a NFE
		If lRet .And. (Type ( "l103Auto" ) == "U" .Or. !l103Auto) .And. (SuperGetMV("MV_VLDNFO",.F.,.F.) == .T.) .And.;
		((nPosNfOri>0 .Or. nPosItmOri>0 .OR. nPosSerOri>0) .and. !lGspInUseM) .And. !(lDHQInDic .And. lMt103Com .And. SF4->F4_EFUTUR == "2")
			If !lTColab		// Para CTe do TOTVS Colaboracao nao efetua validacao da nota original pois a validacao ja foi feita na importacao do XML
				lRet :=A103VldNFO(n)
			EndIf
		EndIf

		If nPosNfOri>0 .And. nPosSerOri>0 .And. nPosIdentB6>0 .And. nPosQuant>0 .And. nPosTotal>0 .And. nPValDesc>0 .And. nPosCod>0 .And. nPosTES>0 .And.;
		lRet .And. !lGspInUseM .And. SF4->F4_PODER3 == 'D'

			lRet := VldLinSB6(n, nPosNfOri,nPosSerOri,nPosIdentB6,nPosQuant,nPosTotal,nPValDesc,nPosCod,nPosTES,nPosVUnit,aCols,cFilNfOri,cA100For,cLoja,cTipo,l103Auto)

		EndIf

		//Impede que dois identificadores sejam carregados ao mesmo tempo
		If nPosIdentB6>0 .and. lRet .And. !lGspInUseM .And. lRet .And. !GDDeleted()
			If !Empty( aCols[ n, nPosIdentB6 ] )
				lRet := MayIUseCode( "SD1_D1_IDENTB6" + aCols[ n, nPosIdentB6 ] )
			EndIf

			If !lRet
				Help( " ", 1, "A103P3SIM" ) // "O identificador de poder de terceiros utilizado ja esta em uso por outra estacao.Selecione outro item de NF original."
				lRet := .F.
			EndIf
		EndIf

		//Verifica as validacoes do modulo SIGAWMS
		If lRet .And. !lGspInUseM .And. IntWMS() .And. SF4->F4_ESTOQUE == "S" .And. cTipo $ "N|D|B"
			lRet := WmsAvalSD1("1","SD1",aCols,n,aHeader)
		EndIf

		//Verifica se ha empenho da OP
		If nPosOp>0 .And. lRet .And. !lGspInUseM .And. lRet .And. !Empty(aCols[n][nPosOp])
			lRet := A103ValSD4(n)
		EndIf

		//Verifica as validacoes da integracao com o QIE
		If nPosCod>0 .And. lRet .And. Localiza(aCols[n][nPosCod])
			DbSelectArea("SB1")
			DbSetOrder(1)
			If MsSeek(xFilial("SB1")+aCols[n][nPosCod]) .And. RetFldProd(SB1->B1_COD,"B1_TIPOCQ") == 'Q' .And. (!(SuperGetMV('MV_CQ') $ SuperGetMV('MV_DISTAUT')) .And. !Empty(SuperGetMV('MV_DISTAUT')))

				Help(" ",1,"A103CQUALY")
				lRet:=.F.
			EndIf

			If lRet .AND. SB1->B1_TIPOCQ == 'Q'
			     lRet := QIEVDOCENT(aCols) //ATEN«√O: Tentar centralizar todas as validaÁıes do Quality nesta funÁ„o
			EndIf
		Else
			DbSelectArea("SB1")
			DbSetOrder(1)
			If lRet .AND. MsSeek(xFilial("SB1")+aCols[n][nPosCod]) .AND. SB1->B1_TIPOCQ == 'Q'
			     lRet := QIEVDOCENT(aCols) //ATEN«√O: Tentar centralizar todas as validaÁıes do Quality nesta funÁ„o
			EndIf
		EndIf

		//Verifica se Produto x Fornecedor foi Bloquedo pela Qualidade.
		If nPosCod>0 .And. lRet .and. !(cTipo$'DB')
			lRet := QieSitFornec(cA100For,cLoja,aCols[n][nPosCod],.T.)
		EndIf
		
		//Verifica se o preco digitado esta divergente do PC ou da AE.
		If nPosPc>0 .And. nPosItemPC>0 .And. nPosVUnit>0 .And.;
				lRet .And. cAltPrcCtr <> "0" .And. !Empty(aCols[n][nPosPc]) .And. !Empty(aCols[n][nPosItemPC]) .And. !lVldAfter

			SC7->(DbSetOrder(9))
			If SC7->(MsSeek(xFilEnt(xFilial("SC7"),"SC7")+cA100For+cLoja+aCols[n][nPosPc]+aCols[n][nPosItemPC]))
				nPreco := xMoeda(SC7->C7_PRECO,SC7->C7_MOEDA,1,M->dDEmissao,TamSX3("D1_VUNIT")[2],SC7->C7_TXMOEDA)
				
				//Se a NF for do SIGAEIC, a comparaÁ„o entre a NF e o Pedido de Compra, n„o tenha efeito
				If Empty(SC7->C7_SEQUEN)
					If (cAltPrcCtr == "1" .And. SC7->C7_TIPO == 1) .Or.;
						(cAltPrcCtr == "2" .And. SC7->C7_TIPO == 2) .Or.;
						(cAltPrcCtr == "5" .And. SC7->C7_TIPO == 2) .Or.;
						cAltPrcCtr $ "3#6"
				   		If NoRound(aCols[n][nPosVUnit],TamSX3("D1_VUNIT")[2]) <> nPreco
					 		Aviso(STR0119,STR0221+IIF(SC7->C7_TIPO == 1,STR0222,STR0223)+STR0224,{STR0163}, 2 ) //-- "Atencao"###""Pre«o informado divergente "###do Pedido de Compras."###"da AutorizaÁ√o de Entrega."###"Ok"###" Verifique o conte˙do do par‚metro MV_ALTPREC"
							lRet := .F.
						Endif
					Endif
				Endif
			Endif
		Endif
		
		//Verifica se o lote esta com data de validade vencida
		If nPosCod>0 .And. nPosLote>0 .And. nPosOp>0 .And. nPosDtvalid>0 .And.;
				lRet .And. !lGspInUseM .And. SF4->F4_ESTOQUE == "S" .And.;
				(Rastro(aCols[n][nPosCod],"S")) .And. !Empty(aCols[n][nPosLote]) .And.;
				!Empty(aCols[n][nPosOp]) .And. aCols[n][nPosDtvalid] < dDatabase

			Help(" ",1,"LOTEVENC")
			If !lLoteVenc
				lRet := .F.
			EndIf
		Endif
		If nPosCod>0 .And. nPosLoteCtl>0 .And. nPosOp>0 .And. nPosDtvalid>0 .And.;
				lRet .And. !lGspInUseM .And. SF4->F4_ESTOQUE == "S" .And.;
				(Rastro(aCols[n][nPosCod],"L")) .And. !Empty(aCols[n][nPosLoteCtl]) .And.;
				!Empty(aCols[n][nPosOp]) .And. aCols[n][nPosDtvalid] < dDatabase

			Help(" ",1,"LOTEVENC")
			If !lLoteVenc
				lRet := .F.
			EndIf
		Endif
		If nPosCod>0 .And. nPosLoteCtl>0 .And. nPosDtvalid>0 .And. lRet .And. SF4->F4_ESTOQUE == "S" .And.;
			(Rastro(aCols[n][nPosCod],"L")) .And. !Empty(aCols[n][nPosLoteCtl])
			For i:=1 To Len(aCols)
				If aCols[i, nPosCod] == aCols[n, nPosCod] .And. aCols[i,nPosLoteCtl] == aCols[n,nPosLoteCtl] .And. !aCols[n,nPosDtvalid]==aCols[i,nPosDtvalid] .And. (!n = i .Or. n == 1)
					HelpAutoma(" ",1,"A240DTVALI",,,,,,,,,.F.)
					aCols[n,nPosDtvalid] := aCols[i,nPosDtvalid]
				EndIf
			Next i
		EndIf

		//Analisa incompatibilidade entre os modos de compartilhamento entre as tabelas
		If lRet .And. nPosPc>0 .And. nPosItemPC>0 .And. !Empty(aCols[n][nPosPc]) .And. !Empty(aCols[n][nPosItemPC]) .And. !lVldAfter
			If SuperGetMv("MV_PCFILEN") .And. FWModeAccess("SC7")=="E" .And. FWModeAccess("SB2")=="C" //!Empty(SB2->(SC7->(xFilEnt(SC7->C7_FILENT))))  .And. Empty(xFilial("SB2"))
				Aviso(OemToAnsi(STR0119),OemToAnsi(STR0282),{STR0461}) //"Quando o par‚metro MV_PCFILENT estiver configurado para trabalhar com filial de entrega (.T.) a tabela de controle de estoques fÌsicos e financeiros (SB2) necessariamente devem estar em modo exclusivo."
				lRet := .F.
			Endif
		Endif
		
		//Analisa transferencia entre filiais
		If lRet
			lRet:=A103TrFil(GdFieldGet('D1_TES',n),cTipo,ca100For,cLoja,cNFiscal,cSerie,GdFieldGet('D1_COD',n),GdFieldGet('D1_QUANT',n),,GdFieldGet('D1_LOTECTL',n),GdFieldGet('D1_NUMLOTE',n),,aCols[n][nPosItemNf])
		EndIf

		// Valida valor aposentadoria especial - Projeto REINF
		If Len(aColsDHP) > 0 .And. nPosItemNF > 0
			If ( nItApoEsp := aScan(aColsDHP,{|x| x[1] == aCols[N][nPosItemNf]}) ) > 0
				If Len(aColsDHP[nItApoEsp][2]) > 0
					lRet := A103ApoTok(aHeadDHP,aColsDHP[nItApoEsp][2],aCols[N][nPosTotal])
				EndIf
			EndIf
		EndIf
	Else
		lRet := .T.
	EndIf

	//Valida o numero maximo de itens permitido para a nota de formulario proprio = S
	If !(Type('l103Auto') <> 'U' .And. l103Auto)
		If lRet .And. cFormul == "S"
			aEval(aCols,{|x| nItensNf += IIF(x[Len(x)],0,1)})
			If nItensNf > a460NumIt(Substr(cSerie,1,3),.T.)
		   		lRet:= .F.
		   		Help(" ",1,"A100NITENS")
			Endif
		EndIf
	EndIf

	//Verifica se o total da NF esta negativo devido ao valor do desconto
	If lRet .And. MaFisRet(n,"IT_TOTAL")<0
		Help(" ",1,"A100VALDES")
		lRet := .F.
	EndIf

	If lRet .And. lDKD .And. lTabAuxD1
		//Atualiza aColsDKD
		A103DKDATU() 
	Endif

	//Exec.Block para Ponto de Entrada: MT103MNT - Multiplas Naturezas
	Eval(bBlockSev1)

	If lRet .and. lDCLNew
		lRet :=DCLMT100LO()
	Else
		If lRet .And. (ExistTemplate("MT100LOK"))
			lRet := ExecTemplate("MT100LOK",.F.,.F.,{lRet})
		EndIf
	EndIf

	If lRet .And. (ExistBlock("MT100LOK"))
		lRet := ExecBlock("MT100LOK",.F.,.F.,{lRet})
	EndIf

	//Pontos de entrada
	If lRet .And. (ExistBlock("MTA103OK"))
		lRet := ExecBlock("MTA103OK",.F.,.F.,{lRet})
	EndIf

	//IntegraÁ„o com MÛdulo de LocaÁıes SIGALOC
	If lMvLocBac .And. lRet .And. lFcLOCM007
		lRet := LOCM007(lRet)
	EndIf

EndIf

//Validacoes pertinentes a integracao com o Manutencao de Ativos
If SuperGetMV("MV_NGMNTES") == "S"
	If lRet
		lRet := NG103LINOK()
	Endif
EndIf

If lRet 
	Do Case
	Case cTipo == "B"
		lRet	:=	PcoVldLan("000054","07","MATA103",/*lUsaLote*/,aCols[n,Len(aHeader)+1]/*lDeleta*/, .T./*lVldLinGrade*/)
	Case cTipo == "D"
		lRet	:=	PcoVldLan("000054","05","MATA103",/*lUsaLote*/,aCols[n,Len(aHeader)+1]/*lDeleta*/, .T./*lVldLinGrade*/)
	OtherWise
		lRet	:=	PcoVldLan("000054","01","MATA103",/*lUsaLote*/,aCols[n,Len(aHeader)+1]/*lDeleta*/, .T./*lVldLinGrade*/)
	EndCase
Endif

//Verifica se o produto est† em revisao vigente e envia para armazem de CQ para ser validado pela engenharia
If lRet .And. lRevProd
	If nRevisao > 0
		cRvSB5 := Posicione("SB5",1,xFilial("SB5")+aCols[n][nPosCod],"B5_REVPROD")
		cBlqSG5:= Posicione("SG5",1,xFilial("SG5")+aCols[n][nPosCod]+aCols[n][nRevisao],"G5_MSBLQL")
		cStatus:= Posicione("SG5",1,xFilial("SG5")+aCols[n][nPosCod]+aCols[n][nRevisao],"G5_STATUS")
		If cRvSB5="1"
			If Empty(cRvSB5)
				Aviso(STR0178,STR0382,{STR0163})//"N„o foi encontrado registro do produto selecionado na rotina de Complemento de Produto."
				lRet:= .F.
			ElseIf Empty(cBlqSG5)
				Aviso(STR0178,STR0383,{STR0163})//"O produto selecionado n„o possui revis„o em uso. Verifique o cadastro de Revisıes."
				lRet:= .F.
			ElseIf cBlqSG5="1"
				Help(" ",1,"REGBLOQ")
				lRet:= .F.
			ElseIf cStatus=="2" .AND. aCols[n][nPosTes]<= "500"
				Aviso(STR0178,STR0390,{STR0163})//"Esta revis„o n„o pode ser alimentada pois est· inativa."
				lRet:= .F.
			ElseIf aCols[n][nRevisao] <> Posicione("SB5",1,xFilial("SB5")+aCols[n][nPosCod],"B5_VERSAO") .AND. aCols[n][nPosLocal] <> SuperGetMV("MV_CQ",.F.,"98")
				If ExistCpo("SG5",aCols[n][nPosCod]+aCols[n][nRevisao])
					nRet := Aviso(STR0384,STR0385 + AllTrim(aCols[n][nPosCod]) + STR0386 ,{STR0387,STR0388},1,STR0389) //"O Produto xxxxx " foi informado com revis„o diferente da revis„o vigente, este produto ser· enviado para o ArmazÈm de CQ."
					If nRet==1
						aCols[n][nPosLocal]:= SuperGetMV("MV_CQ",.F.,"98")
					Else
						lRet:= .F.
					EndIf
				Else
					lRet:= .F.
				EndIf
			EndIf
		EndIf
	Else
		help( NIL, 1, "RevEstrut", NIL, STR0569, 1 , 0,,,,,, {chr(13) + chr(10) + STR0570 +chr(13) + chr(10) +STR0571}) // "N„o È possivel verificar a revis„o da estrutura." , "- Deixar o campo 'D1_REVISAO' como usado no configurador;" "- Verificar o par‚metro MV_REVPROD."
		lRet:= .F.
	Endif		
EndIf

RestArea(aAreaSF4)
RestArea(aAreaSB6)
RestArea(aAreaSD2)
RestArea(aArea)

Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ A103F4   ≥ Autor ≥ Edson Maricate        ≥ Data ≥26.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Faz a consulta aos pedidos de compra em aberto.            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103F4()                                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103F4()

Local cVariavel	:= ReadVar()
Local bKeyF4	:=  SetKey( VK_F4 )
Local lContinua := .T.

SetKey( VK_F4,Nil )

//Impede de executar a rotina quando a tecla F3 estiver ativa
If Type("InConPad") == "L"
	lContinua := !InConPad
EndIf

If lContinua .And. cVariavel == "M->D1_OP" .And. cTipo $ 'NIPBC'
	A103ShowOp()
Endif

SetKey( VK_F4,bKeyF4 )

Return .T.

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103ForF4 ≥ Autor ≥ Edson Maricate        ≥ Data ≥27.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Tela de importacao de Pedidos de Compra.                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103Pedido()                                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥MATA103                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Function A103ForF4(lUsaFiscal,aGets,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aHeadSEV, aColsSEV, lTxNeg, nTaxaMoeda, aRetPed, oListBox, aRecSC7)

Local nSldPed    := 0
Local nOpc       := 0
Local cAliasSC7  := "SC7"
Local cQueryQPC  := ""
Local lQuery     := .F. 
Local bSavSetKey := SetKey(VK_F4,Nil)
Local bSavKeyF5  := SetKey(VK_F5,Nil)
Local bSavKeyF6  := SetKey(VK_F6,Nil)
Local bSavKeyF7  := SetKey(VK_F7,Nil)
Local bSavKeyF8  := SetKey(VK_F8,Nil)
Local bSavKeyF9  := SetKey(VK_F9,Nil)
Local bSavKeyF10 := SetKey(VK_F10,Nil)
Local bSavKeyF11 := SetKey(VK_F11,Nil)
Local cCbmFor    := ""
Local cCbmLoj    := ""
Local aArea      := GetArea()
Local aAreaSA2   := SA2->(GetArea())
Local aAreaSC7   := SC7->(GetArea())
Local aAreaColab := {}
Local nF4For     := 0
Local aButtons   := { {'PESQUISA',{|| IIf(Len(aRecSC7) > 0, A103VisuPC(aRecSC7[oListBox:nAt]) ,)},OemToAnsi(STR0059),OemToAnsi(STR0061)} } //"Visualiza Pedido"
Local oDlg
Local cNomeFor   := ''
Local aTitCampos := {}
Local aConteudos := {}
Local aUsCont    := {}
Local aUsTitu    := {}
Local bLine      := { || .T. }
Local cLine      := ""
Local cComboFor  := ""
Local cCodLoj    := ""
Local lMa103F4I  := ExistBlock( "MA103F4I" )
Local nLoop      := 0
Local lMt103Vpc  := ExistBlock("MT103VPC")
Local lRet103Vpc := .T.
Local lContinua  := .T.
Local lMT103APC  := ExistBlock("MT103APC")
Local lRetAPC    := .F.
Local lForpcnf   := SuperGetMV("MV_FORPCNF",.F.,.F.)
Local lXmlxped	 := SuperGetMV("MV_XMLXPED",.F.,.F.)
Local lRetPed    := (aRetPed == Nil)
Local oSize
Local nNumCampos := 0
Local cRestNFe	:= SuperGetMV("MV_RESTNFE")
Local lMA103F4L	:= ExistBlock("MA103F4L")
Local lMA103F4H	:= ExistBlock( "MA103F4H" )
Local oNomeFor	:= NIL
Local lIntPMS := SuperGetMv("MV_INTPMS",.F.,"N") == "S"

PRIVATE aF4For     := {}
PRIVATE aRecSC7    := {}
PRIVATE oOk        := LoadBitMap(GetResources(), "LBOK")
PRIVATE oNo        := LoadBitMap(GetResources(), "LBNO")

DEFAULT lUsaFiscal := .T.
DEFAULT aGets      := {}
DEFAULT lNfMedic   := .F.
DEFAULT lConsMedic := .F.
DEFAULT aHeadSDE   := {}
DEFAULT aColsSDE   := {}

nTamX3A2CD	:= Iif(nTamX3A2CD==0,TamSX3("A2_COD")[1],nTamX3A2CD)
nTamX3A2LJ	:= Iif(nTamX3A2LJ==0,TamSX3("A2_LOJA")[1],nTamX3A2LJ)

If VALType("cQueryC7") <> "C"
	PRIVATE cQueryC7   := ""
EndIf

//Impede de executar a rotina quando a tecla F3 estiver ativa
If Type("InConPad") == "L"
	lContinua := !InConPad
EndIf

//Impede de executar a rotina quando algum campo estiver em edicao
If lContinua .And. IsInCallStack("EDITCELL")
	lContinua:=.F.
EndIf

//Informa que houve importaÁ„o de pedido no documento
If lContinua .And. Type("lImpPedido")<>"U"
	lImpPedido := .T.
Endif

//Verifica se a nota foi importada via TOTVS Colaboracao
If lContinua .And. lXmlxped .And. Type("l103Class") == "L" .And. l103Class
	aAreaColab := GetArea()
	DbSelectArea("SDS")
	SDS->(DbSetOrder(1))
	If SDS->(DbSeek(xFilial("SDS")+cNFiscal+cSerie+cA100For+cLoja))
		Aviso(STR0429,STR0430,{STR0163})
		lContinua := .F.
	EndIf
	RestArea(aAreaColab)
EndIf

//Ponto de entrada para validacoes da importacao do Pedido de Compras
If lContinua .And. lMT103APC
	lRetAPC := ExecBlock("MT103APC",.F.,.F.) 
	If ValType(lRetAPC)=="L"
		lContinua:= lRetAPC
	EndIf
EndIf

If lContinua

	If MaFisFound("NF") .Or. !lUsaFiscal
		//Verifica se o aCols esta vazio, se o Tipo da Nota È
		//normal e se a rotina foi disparada pelo campo correto
		If cTipo == "N"
			DbSelectArea("SA2")
			SA2->(DbSetOrder(1))
			SA2->(DbSeek(xFilial("SA2")+cA100For+cLoja))
			cNomeFor	:= SA2->A2_NOME

			DbSelectArea("SC7")
			SC7->(DbSetOrder(9))
			lQuery    := .T.
			cAliasSC7 := "QRYSC7"
			
			cQueryC7 := "SELECT R_E_C_N_O_ RECSC7 FROM "
			cQueryC7 += RetSqlName("SC7") + " SC7 "
			cQueryC7 += "WHERE C7_FILENT = '"+xFilEnt(xFilial("SC7"))+"' AND "

			If HasTemplate( "DRO" ) .AND. FunName() == "MATA103" .AND. MV_PAR15 == 1 .And. ExistTemplate("cA100For")
				cQueryC7 += "C7_FORNECE IN ( " + ExecTemplate("cA100For") + " )  AND "
			Else
				cQueryC7 += "C7_FORNECE = '"+cA100For+"' AND "
			EndIf
			
			cQueryC7 += "(C7_QUANT-C7_QUJE-C7_QTDACLA)>0 AND "
			cQueryC7 += "C7_RESIDUO=' ' AND "
			cQueryC7 += "C7_TPOP<>'P' AND "

			If cRestNFe == "S"
				cQueryC7 += "C7_CONAPRO <> 'B' AND C7_CONAPRO <> 'R' AND "
			EndIf

			If ( lConsLoja )
				cQueryC7 += "C7_LOJA = '"+cLoja+"' AND "
			Endif

			//Filtra os pedidos de compras de acordo com os contratos
			If lConsMedic
				If lNfMedic
					//Traz apenas os pedidos oriundos de medicoes
					cQueryC7 += "C7_CONTRA<>'"  + Space( Len( SC7->C7_CONTRA ) )  + "' AND "
					cQueryC7 += "C7_MEDICAO<>'" + Space( Len( SC7->C7_MEDICAO ) ) + "' AND "
				Else
					//Traz apenas os pedidos que nao possuem medicoes
					cQueryC7 += "C7_CONTRA='"  + Space( Len( SC7->C7_CONTRA ) )  + "' AND "
					cQueryC7 += "C7_MEDICAO='" + Space( Len( SC7->C7_MEDICAO ) ) + "' AND "
				EndIf
			EndIf

			cQueryC7 += "D_E_L_E_T_ = ' '"
			cQueryC7 += "ORDER BY " + SqlOrder(SC7->(IndexKey()))

			If ExistBlock("MT103QPC")
				cQueryQPC := ExecBlock("MT103QPC",.F.,.F.,{cQueryC7,1})
				If (ValType(cQueryQPC) == 'C' )
					cQueryC7 := cQueryQPC
				EndIf
			EndIf
			
			cQueryC7 := ChangeQuery(cQueryC7)

			If !lRetPed .And. Select(cAliasSC7) > 0
				(cAliasSC7)->(dbCloseArea())
			EndIf

			dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQueryC7),cAliasSC7,.T.,.T.)

			Do While (cAliasSC7)->(!Eof())
				SC7->(MsGoto((cAliasSC7)->RECSC7))
				
				If lMt103Vpc
					lRet103Vpc := .T.
					lRet103Vpc := Execblock("MT103VPC",.F.,.F.)
				Endif

				If lRet103Vpc
					If lConsMedic .And. lNfMedic
						nF4For := aScan(aF4For,{|x|x[5]== SC7->C7_LOJA .And. x[6]== SC7->C7_NUM})
					Else
						nF4For := aScan(aF4For,{|x|x[2]== SC7->C7_LOJA .And. x[3]== SC7->C7_NUM})
					EndIf

					If ( nF4For == 0 )
						If lConsMedic .And. lNfMedic
							aConteudos := {.F.,SC7->C7_MEDICAO,SC7->C7_CONTRA,SC7->C7_PLANILH,SC7->C7_LOJA,SC7->C7_NUM,DTOC(SC7->C7_EMISSAO),If(SC7->C7_TIPO==2,'AE','PC') }
						Else
							aConteudos := {.F.,SC7->C7_LOJA,SC7->C7_NUM,DTOC(SC7->C7_EMISSAO),If(SC7->C7_TIPO==2,'AE', 'PC') }
						EndIf

						//Agroindustria
						If FindFunction("OGXUtlOrig") .And. OGXUtlOrig() //Encontra a funÁ„o
							If FindFunction("OGX200") //Encontra a funÁ„o
								If ValType( aUsCont := OGX200() ) == "A"
									AEval( aUsCont, { |x| AAdd( aConteudos, x ) } )
								EndIf
							EndIf
						EndIf

						If lMa103F4I
							If ValType( aUsCont := ExecBlock( "MA103F4I", .F., .F. ) ) == "A"
								AEval( aUsCont, { |x| AAdd( aConteudos, x ) } )
							EndIf
						EndIf

						aAdd(aF4For , aConteudos )
						aAdd(aRecSC7, SC7->(Recno()))
					EndIf
				Endif
				(cAliasSC7)->(dbSkip())
			EndDo

			If lMA103F4L
				ExecBlock("MA103F4L", .F., .F., { aF4For, aRecSC7 } )
			EndIf

			//Exibe os dados na Tela
			If (!Empty(aF4For) .Or. lForPCNF)
				If lConsMedic .And. lNfMedic
					//Exibe os campos de medicao do contrato
					aTitCampos := {" ",RetTitle("C7_MEDICAO"),RetTitle("C7_CONTRA"),RetTitle("C7_PLANILH"),OemToAnsi(STR0060),OemToAnsi(STR0061),OemToAnsi(STR0039),OemToAnsi(STR0062)} //"Medicao"###"Contrato"###"Planilha"###"Loja"###"Pedido"###"Emissao"###"Origem"

					If !Empty(aF4For)
						cLine := "{If(aF4For[oListBox:nAt,1],oOk,oNo),aF4For[oListBox:nAT][2],aF4For[oListBox:nAT][3],aF4For[oListBox:nAT][4],aF4For[oListBox:nAT][5],aF4For[oListBox:nAT][6],aF4For[oListBox:nAT][7],aF4For[oListBox:nAT][8]"
					Else
						cLine := "{If(Empty(aF4For),oNO,oOK)," +Replicate("'',",6) +"''"
					EndIf
				Else
					aTitCampos := {" ",OemToAnsi(STR0060),OemToAnsi(STR0061),OemToAnsi(STR0039),OemToAnsi(STR0062)} //"Loja"###"Pedido"###"Emissao"###"Origem"
					If !Empty(aF4For)
						cLine := "{If(aF4For[oListBox:nAt,1],oOk,oNo),aF4For[oListBox:nAT][2],aF4For[oListBox:nAT][3],aF4For[oListBox:nAT][4],aF4For[oListBox:nAT][5]"
					Else
						cLine := "{If(Empty(aF4For),oNO,oOK)," +Replicate("'',",4) +"''"
					EndIf
				EndIf

				//Agroindustria
				If FindFunction("OGXUtlOrig") .And. OGXUtlOrig() //Encontra a funÁ„o
				   If FindFunction("OGX195") //Encontra a funÁ„o
						If ValType( aUsTitu := OGX195() ) == "A"
						   nNumCampos := Len(aTitCampos)
						   For nLoop := 1 To Len( aUsTitu )
							   AAdd( aTitCampos, aUsTitu[ nLoop ] )
							   cLine += ",aF4For[oListBox:nAT][" + AllTrim( Str( nLoop + nNumCampos ) ) + "]"
						   Next nLoop
						EndIf
					EndIf
				EndIf

				If lMA103F4H .And. !Empty(aF4For)
					If ValType( aUsTitu := ExecBlock( "MA103F4H", .F., .F. ) ) == "A"
						nNumCampos := Len(aTitCampos)
						For nLoop := 1 To Len( aUsTitu )
							AAdd( aTitCampos, aUsTitu[ nLoop ] )
							cLine += ",aF4For[oListBox:nAT][" + AllTrim( Str( nLoop + nNumCampos ) ) + "]"
						Next nLoop
					EndIf
				EndIf

				cLine += " } "

				//Monta dinamicamente o bline do CodeBlock
				bLine := &( "{ || " + cLine + " }" )

				If lRetPed
					DEFINE MSDIALOG oDlg FROM 50,40  TO 285,541 TITLE OemToAnsi(STR0024+" - <F5> ") Of oMainWnd PIXEL //"Selecionar Pedido de Compra"

					//Calcula dimensıes
					oSize := FwDefSize():New(.T.,,,oDlg)
					oSize:AddObject( "CAB"		,  100, 20, .T., .T. ) // Totalmente dimensionavel
					oSize:AddObject( "LISTBOX" 	,  100, 80, .T., .T. ) // Totalmente dimensionavel

					oSize:lProp 	:= .T. // Proporcional
					oSize:aMargins 	:= { 3, 3, 3, 3 } // Espaco ao lado dos objetos 0, entre eles 3

					oSize:Process() 	   // Dispara os calculos

					@ oSize:GetDimension("CAB","LININI")+2  ,oSize:GetDimension("CAB","COLINI")   SAY OemToAnsi(STR0028) Of oDlg PIXEL SIZE 47 ,9 //"Fornecedor"

					If !lForPCNF
						@ oSize:GetDimension("CAB","LININI") ,oSize:GetDimension("CAB","COLINI")+32  MSGET oNomeFor VAR cNomeFor PICTURE PesqPict('SA2','A2_NOME') When .F. Of oDlg PIXEL SIZE 120,9
						If(lLGPD,OfuscaLGPD(oNomeFor,"A2_NOME"),.F.)
					Else
						@ oSize:GetDimension("CAB","LININI") ,oSize:GetDimension("CAB","COLINI")+32  MSCOMBOBOX oComboBox VAR cComboFor ITEMS MTGetForRl(cA100For,cLoja) SIZE 215,9 OF oDlg PIXEL ON CHANGE A103LoadPd(lUsaFiscal,aGets,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aHeadSEV, aColsSEV, lTxNeg, nTaxaMoeda, @oListBox, cComboFor, @aF4For, bLine, @aRecSC7)
					EndIf

					oListBox := TWBrowse():New( oSize:GetDimension("LISTBOX","LININI"),oSize:GetDimension("LISTBOX","COLINI"),;
						 				oSize:GetDimension("LISTBOX","XSIZE")-22,oSize:GetDimension("LISTBOX","YSIZE")+1.4,;
						 				,aTitCampos,,oDlg,,,,,,,,,,,,.F.,,.T.,,.F.,,,)
					oListBox:SetArray(aF4For)
					If (!Empty(aF4For))
						oListBox:bLDblClick := { || A103SELPC(aTitCampos,aF4For,oListBox:nAt,lIntPms)}
					EndIf
					oListBox:bLine := bLine

					ACTIVATE MSDIALOG oDlg CENTERED ON INIT EnchoiceBar(oDlg,{|| (nOpc := 1,nF4For := oListBox:nAt,oDlg:End()) },{||(nOpc := 0,nF4For := oListBox:nAt,oDlg:End())},,aButtons)

					If nOpc == 1
						If (!Empty(aF4For)) .And. lForPCNF
							cCodLoj := SubStr(cComboFor, At(' | ',cComboFor)+3, Len(cComboFor))
							cCodLoj := SubStr(cCodLoj,1, At(' - ',cCodLoj)-1)
						   	cCbmFor := SubStr(cCodLoj, 1, At('/',cCodLoj)-1)
							cCbmLoj := SubStr(cCodLoj, At('/',cCodLoj)+1, Len(cCodLoj))
							cCbmFor := Padr(cCbmFor,nTamX3A2CD)
							cCbmLoj := Padr(cCbmLoj,nTamX3A2LJ)
							Processa({|| a103procPC(aF4For,nOpc,cCbmFor,cCbmLoj,@lRet103Vpc,@lMt103Vpc,@nSldPed,lUsaFiscal,aGets,( lConsMedic .And. lNfMedic ),aHeadSDE,@aColsSDE,aHeadSEV, aColsSEV, @lTxNeg, @nTaxaMoeda)})
						ElseIf (!Empty(aF4For))
							Processa({|| a103procPC(aF4For,nOpc,cA100For,cLoja,@lRet103Vpc,@lMt103Vpc,@nSldPed,lUsaFiscal,aGets,( lConsMedic .And. lNfMedic ),aHeadSDE,@aColsSDE,aHeadSEV, aColsSEV, @lTxNeg, @nTaxaMoeda)})
						Else
							Help(" ",1,"A103F4")
						EndIf
					EndIf

				EndIf
			ElseIf !lRetPed
			Else
				Help(" ",1,"A103F4")
			EndIf
		Else
			Help('   ',1,'A103TIPON')
		EndIf
	Else
		Help('   ',1,'A103CAB')
	EndIf
Endif

//Restaura a Integrida dos dados de Entrada
If lRetPed
	If Select(cAliasSC7) > 0
		(cAliasSC7)->(dbCloseArea())
	Endif
	
	DbSelectArea("SC7")
	
	SetKey(VK_F4,bSavSetKey)
	SetKey(VK_F5,bSavKeyF5)
	SetKey(VK_F6,bSavKeyF6)
	SetKey(VK_F7,bSavKeyF7)
	SetKey(VK_F8,bSavKeyF8)
	SetKey(VK_F9,bSavKeyF9)
	SetKey(VK_F10,bSavKeyF10)
	SetKey(VK_F11,bSavKeyF11)
	RestArea(aAreaSA2)
	RestArea(aAreaSC7)
	RestArea(aArea)
Else
	aRetPed := aClone(aF4For)
	oListBox:bLine := bLine
EndIf
If lDKD .And. lTabAuxD1 .And. FindFunction("gatilhadkd") 
	gatilhadkd()  
Endif
Return(.T.)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103ProcPC| Autor ≥ Alex Lemes            ≥ Data ≥09/06/2003≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Processa o carregamento do pedido de compras para a NFE    ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpA1 = Array com os itens do pedido de compras            ≥±±
±±≥          ≥ ExpN1 = Opcao valida                                       ≥±±
±±≥          ≥ ExpC1 = Fornecedor                                         ≥±±
±±≥          ≥ ExpC2 = loja fornecedor                                    ≥±±
±±≥          ≥ ExpL1 = retorno do ponto de entrada                        ≥±±
±±≥          ≥ ExpL2 = Uso do ponto de entrada                            ≥±±
±±≥          ≥ ExpN2 = Saldo do pedido                                    ≥±±
±±≥          ≥ ExpL3 = Usa funcao fiscal                                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function a103procPC(aF4For,nOpc,cA100For,cLoja,lRet103Vpc,lMt103Vpc,nSldPed,lUsaFiscal,aGets,lNfMedic,aHeadSDE,aColsSDE,aHeadSEV, aColsSEV, lTxNeg, nTaxaMoeda)

Local nx         := 0
Local cItem		 := StrZero(1,Len(SD1->D1_ITEM))
Local lZeraCols  := .T.
Local aRateio    := {0,0,0} 
Local aMT103NPC  := {}
Local aColsBkp   := Aclone(Acols)
Local cPrdNCad   := ""
Local nSavNF  	 := MaFisSave()
Local n103TXPC	 := 0
Local cSeekTXPC	 := ""
Local nPosPc	 := GetPosSD1("D1_PEDIDO")
Local nPosVlr	 := GetPosSD1("D1_VUNIT")
Local aMT103FRE  := {}
Local aCombo		:= {}
Local nPsTpFrt		:= 0
Local lvldFret 		:= SuperGetMV("MV_VALFRET",.F.,.F.)
Local cFilSC7		:= xFilEnt(xFilial("SC7"),"SC7")
Local lMT103NPC		:= ExistBlock("MT103NPC")
Local lMT103TXPC	:= ExistBlock("MT103TXPC")
Local lMT103FRE		:= ExistBlock("MT103FRE")
Local cFilSB1		:= xFilial("SB1")
Local cPCNum		:= ""
Local aEstruSC7		:= SC7->( dbStruct() )
Local nPosC7Qtd		:= aScan(aEstruSC7, {|x| AllTrim(x[1]) == "C7_QUANT"})
Local lPeVldPc		:= .T.
Local lPergBloq 	:= .F.
Local aBkpImport 	:= {}
Local aBkpDKDImport := {}

DEFAULT lUsaFiscal := .T.
DEFAULT aGets      := {}
DEFAULT lNfMedic   := .F.
DEFAULT aHeadSDE   := {}
DEFAULT aColsSDE   := {}
DEFAULT lMT103PBLQ := .F.

If VALType("cQueryC7") <> "C"
	PRIVATE cQueryC7   := ""
EndIf

If ( nOpc == 1 ) 
	
	// PE para validaÁ„o de carregamento do pedido de compras.
	If ExistBlock("M120vlpc") 
		lPeVldPc := ExecBlock("M120vlpc",.F.,.F.,{@aF4For,lNfMedic,lUsaFiscal})
	EndIf
	If lPeVldPc
	
		DbSelectArea("SB1")
		SB1->(DbSetOrder(1))
		
		DbSelectArea("SC7")
		SC7->(DbSetOrder(14))
		
		For nx	:= 1 to Len(aF4For)
			If aF4For[nx][1]
				lPergBloq := .T.
				aBkpImport := aClone(aCols)
				aBkpDKDImport := aClone(aColsDKD)				

		        If lNfMedic
					cPCNum := aF4For[nx,6]
				Else
					cPCNum := aF4For[nx,3]
				Endif	
			
			 	If Select("ITPC") > 0
					ITPC->(DbCloseArea())
			 	Endif

				cQry := StrTran(cQueryC7,"R_E_C_N_O_ RECSC7",	"R_E_C_N_O_ as RECNO, "+;
																"C7_NUM, "+;
																"C7_ITEM, "+;
																"C7_LOTPLS, "+;
																"C7_CODRDA, "+;
																"C7_PLOPELT, "+;
																"C7_PRODUTO, "+;
																"C7_TPFRETE, "+;
																"C7_MOEDA, "+;
																"C7_QUANT - C7_QUJE - C7_QTDACLA AS SLDPC ")
				
				cQry := StrTran(cQry,"WHERE ",	"WHERE C7_NUM = '" + cPCNum + "' AND "+;
												"C7_LOJA = '" + aF4For[nx,Iif(lNfMedic,5,2)] + "' AND ")
				
				
				dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQry),"ITPC",.T.,.T.)
				
				If Len(aEstruSC7) > 0 .And. nPosC7Qtd > 0
					TcSetField( "ITPC", "SLDPC", aEstruSC7[nPosC7Qtd,2], aEstruSC7[nPosC7Qtd,3], aEstruSC7[nPosC7Qtd,4] )
				EndIf
				
				DbSelectArea("ITPC")
				
				While ITPC->(!EOF())
					SC7->(DbGoTo(ITPC->RECNO))
					If lZeraCols
						aCols		:= {}
						aBkpImport  := {}
						aColsDKD	:= {}						
						aBkpDKDImport := {}
						lZeraCols	:= .F.	
						MaFisClear()
						
						If lVldFret .And. !Empty(ITPC->C7_TPFRETE) .And. MaFisFound("NF") .AND. Type("aNFEDanfe") == "A" .AND. Empty(aNfeDanfe[14])
							aCombo			:= CarregaTipoFrete()
							aNfeDanfe[14] := ITPC->C7_TPFRETE
							nPsTpFrt 		:= ascan(aCombo ,{|x| Substr(x,1,1) == Substr(aNFEDanfe[14],1,1)})
							If nPsTpFrt > 0
								oTpFrete:NAT := nPsTpFrt
								oTpFrete:refresh()
		                    EndIf
						ElseIf lVldFret .And. !Empty(ITPC->C7_TPFRETE) .And. !MaFisFound("NF")
							cTpFrete := ITPC->C7_TPFRETE
						EndIf
					EndIf 
	
					If SB1->(DbSeek(cFilSB1 + ITPC->C7_PRODUTO))
						If RegistroOk("SB1",.F.) 
							If lMt103Vpc
								lRet103Vpc := .T.
								lRet103Vpc := Execblock("MT103VPC",.F.,.F.)
							EndIf
									
							If lRet103Vpc
								NfePC2Acol(ITPC->RECNO,,ITPC->SLDPC,cItem,,@aRateio,aHeadSDE,@aColsSDE)
								cItem := SomaIt(cItem)
						   	EndIf
						ElseIf ExistBlock("MT103PBLQ") 
								If !lMT103PBLQ
									lMT103PBLQ := ExecBlock("MT103PBLQ",.F.,.F.,{ITPC->C7_PRODUTO})
								Endif
								If lMT103PBLQ
									NfePC2Acol( ITPC->RECNO, , ITPC->SLDPC, cItem, , @aRateio, aHeadSDE, @aColsSDE )
									cItem := SomaIt( cItem )
								Endif
						ElseIf lPergBloq .And. !MsgYesNo(STR0525 + AllTrim(ITPC->C7_NUM) + STR0526, STR0524) //O pedido de compra XXXX tem produtos bloqueados. Deseja importar apenas os produtos n„o bloqueados desse pedido?
							If Len(aBkpImport) > 0 .And. Empty(aBkpImport[1][2]) //Verifica se a primeira posiÁ„o do aCols est· vazia para n„o gravar linha em branco
								aCols := {}
							Else
								aCols := aBkpImport //Restaura aCols
								aColsDKD := aBkpDKDImport
							EndIf
							Exit	
						Else
							lPergBloq := .F. //Pergunta apenas uma vez por pedido
						EndIf
				   	Else
				   		cPrdNCad += STR0061+": "+ITPC->C7_NUM+"  "+STR0063+": "+ITPC->C7_PRODUTO+CHR(10)
					EndIf
		
					If ITPC->C7_MOEDA != 1
						cSeekTXPC := cFilSC7+cPCNum
					EndIf
	
					ITPC->(dbSkip())
				EndDo
							
				If Select("ITPC") > 0
					ITPC->(DbCloseArea())
				Endif
			EndIf
		Next nX
		
		//Exibe Lista dos Produtos n„o Cadastrados na Filial de Entrega
		If Len(cPrdNCad)>0 .And. !l103Auto
		   Aviso("A103ProcPC",STR0300+CHR(10)+STR0301+CHR(10)+cPrdNCad,{"Ok"})
		EndIf
	
		//Restaura o Acols caso o mesmo estiver vazio
		If Len(Acols) == 0
		    aCols:= aColsBKP
		    MaFisRestore(nSavNF)
		Else
			//Ponto de entrada para manipular o array de multiplas naturezas por titulo no Pedido de Compras
			If lMT103NPC
				aMT103NPC := ExecBlock("MT103NPC",.F.,.F.,{aHeadSEV,aColsSEV})
			 	If (ValType(aMT103NPC) == "A")
			   		aColsSEV := aClone(aMT103NPC)
				EndIf
			EndIf
	
			//Ponto de entrada para alterar a moeda, taxa, e check box de taxa negociada de acordo com o Pedido de Compras
			If lMT103TXPC .And. !Empty(cSeekTXPC)
				If SC7->(DbSeek(cSeekTXPC))
					nPosItPc := aScan(aCols,{|x| AllTrim(x[nPosPc])==AllTrim(SC7->C7_NUM)})
					n103TXPC := ExecBlock("MT103TXPC",.F.,.F.)
					If ValType(n103TXPC) == "N"
						If n103TXPC > 0
							nTaxaMoeda := n103TXPC
						ElseIf nPosItPc > 0
							nTaxaMoeda := NoRound((aCols[nPosItPc][nPosVlr] / SC7->C7_PRECO),TamSx3("F1_TXMOEDA")[2])
						EndIf
						lTxNeg := .T.
						nMoedaCor := SC7->C7_MOEDA
					EndIf
				Endif
			EndIf
	
			//Impede que o item do PC seja deletado pela getdados da NFE na movimentacao das setas.
			If Type( "oGetDados" ) == "O"
				oGetDados:lNewLine:=.F.
				oGetDados:oBrowse:Refresh()
			EndIf
	
			//Ponto de entrada para manipular o array de Frete/Seguro/Despesa do Pedido de Compras
			If lMT103FRE
				aMT103FRE := ExecBlock("MT103FRE",.F.,.F.,aRateio)
				If (ValType(aMT103FRE) == "A")
					aRateio := aClone(aMT103FRE)
				EndIf
			EndIf
		
			//Rateio do valores de Frete/Seguro/Despesa do PC
			If lUsaFiscal
				Eval(bRefresh)
				lAtuDupPC := .T.
				Eval(bRefresh,6)
			Else
				aGets[SEGURO] := aRateio[1]
				aGets[VALDESP]:= aRateio[2]
				aGets[FRETE]  := aRateio[3]
			EndIf
		Endif
	Endif
Endif

Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103ItemPC≥ Autor ≥ Edson Maricate        ≥ Data ≥27.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Tela de importacao de Pedidos de Compra por Item.           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103ItemPC()                                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥MATA103                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103ItemPC(lUsaFiscal,aPedido,oGetDAtu,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aGets, lTxNeg, nTaxaMoeda,aRetPed, aArrSldoAux)

Local cSeek			:= ""
Local nOpca			:= 0
Local aArea			:= GetArea()
Local aAreaSA2		:= SA2->(GetArea())
Local aAreaSC7		:= SC7->(GetArea())
Local aAreaSB1		:= SB1->(GetArea())
Local aAreaColab	:= {}
Local aRateio       := {0,0,0}
Local aNew			:= {}
Local aTamCab		:= {}
Local aSizePed		:= {30,20,270,531}
Local aSizeC7T		:= {}
Local aButtons		:= { {'PESQUISA',{|| IIf(Len(aArrSldo) > 0, A103VisuPC(aArrSldo[oQual:nAt][2]), )},OemToAnsi(STR0059),OemToAnsi(STR0061)},; //"Visualiza Pedido"
						 {'pesquisa',{||A103PesqP(aCab,aCampos,aArrayF4,oQual)},OemToAnsi(STR0001)} } //"Pesquisar"
Local aEstruSC7		:= SC7->( dbStruct() )
Local bSavSetKey	:= SetKey(VK_F4,Nil)
Local bSavKeyF5		:= SetKey(VK_F5,Nil)
Local bSavKeyF6		:= SetKey(VK_F6,Nil)
Local bSavKeyF7		:= SetKey(VK_F7,Nil)
Local bSavKeyF8		:= SetKey(VK_F8,Nil)
Local bSavKeyF9		:= SetKey(VK_F9,Nil)
Local bSavKeyF10	:= SetKey(VK_F10,Nil)
Local bSavKeyF11	:= SetKey(VK_F11,Nil)
Local nFreeQt		:= 0
Local nPosC7Prod 	:= 0
Local nPosC7Ped 	:= 0
Local nPosC7Item 	:= 0
Local nPosPRD		:= GetPosSD1("D1_COD")
Local nPosPDD		:= GetPosSD1("D1_PEDIDO" )
Local nPosITM		:= GetPosSD1("D1_ITEMPC" )
Local nPosQTD		:= GetPosSD1("D1_QUANT" )
Local cVar			:= aCols[n][nPosPrd]
Local cQuery		:= ""
Local aLine 		:= {}
Local cAliasSC7		:= "SC7"
Local cQueryQPC     := ""
Local cCpoObri		:= ""
Local aCpoObri		:= ""
Local cComboFor		:= ''
Local nPed			:= 0
Local nX			:= 0
Local nAuxCNT		:= 0
Local lMt103Vpc		:= ExistBlock("MT103VPC")
Local lMt100C7D		:= ExistBlock("MT100C7D")
Local lMt100C7C		:= ExistBlock("MT100C7C")
Local lMt103C7T		:= ExistBlock("MT103C7T")
Local lMt103Sel		:= ExistBlock("MT103SEL")
Local nMT103Sel     := 0
Local lRet103Vpc	:= .T.
Local lMT103BPC 	:= ExistBlock("MT103BPC")
Local lRetBPC    	:= .F.
Local lContinua		:= .T.
Local lQuery		:= .F.
Local lTColab		:= .F.
Local lForPCNF		:= SuperGetMV("MV_FORPCNF",.F.,.F.)
Local lXmlxped		:= SuperGetMV("MV_XMLXPED",.F.,.F.)
Local lRetPed		:= (aRetPed == Nil)
Local oQual
Local oDlg
Local oSize
Local oComboBox
Local aUsButtons  	:= {}
Local lToler		:= MA103CkAIC(cA100For,cLoja,cVar)
Local nPosPc		:= GetPosSD1("D1_PEDIDO")
Local nPosVlr		:= GetPosSD1("D1_VUNIT")
Local nPosItPc		:= 0
Local n103TXPC		:= 0
Local nScan	    	:= 0
Local nMIten		:= 0
Local aMT103FRE		:= {}
Local nQtdItMark	:= 0
Local nPosItem   	:= GetPosSD1("D1_ITEM")
Local lIntPMS 		:= SuperGetMv("MV_INTPMS",.F.,"N") == "S"
Local nMVOBS		:= SuperGetMV("MV_PCNFOBS",.F.,0)
Local cC7Obs		:= ""
Local cObs			:= ""
Local cObsM			:= ""
Local lVldFret 		:= SuperGetMV("MV_VALFRET",.F.,.F.)
Local aCombo 		:= {}
Local nPsTpFrt      := 0

PRIVATE oOk        := LoadBitMap(GetResources(), "LBOK")
PRIVATE oNo        := LoadBitMap(GetResources(), "LBNO") 
PRIVATE aCab	   := {}
PRIVATE aCampos	   := {}
PRIVATE aArrSldo   := {}
PRIVATE aArrayF4   := {}

DEFAULT lUsaFiscal := .T.
DEFAULT aPedido	   := {}
DEFAULT lNfMedic   := .F.
DEFAULT lConsMedic := .F.
DEFAULT aHeadSDE   := {}
DEFAULT aColsSDE   := {}
DEFAULT aGets      := {}

//Impede de executar a rotina quando a tecla F3 estiver ativa
If Type("InConPad") == "L"
	lContinua := !InConPad
EndIf

//Adiciona botoes do usuario na EnchoiceBar
If ExistBlock( "MTIPCBUT" )
	If ValType( aUsButtons := ExecBlock( "MTIPCBUT", .F., .F. ) ) == "A"
		AEval( aUsButtons, { |x| AAdd( aButtons, x ) } )
	EndIf
EndIf

//Ponto de entrada para validacoes da importacao do Pedido de Compras por item
If lContinua .And. lMT103BPC
	lRetBPC := ExecBlock("MT103BPC",.F.,.F.)
	If ValType(lRetBPC)=="L"
		lContinua:= lRetBPC
	EndIf
EndIf

If lContinua

	If MaFisFound('NF') .Or. !lUsaFiscal
		If cTipo == 'N'

			DbSelectArea("SC7")

			If Empty(cVar)
				DbSetOrder(9)
			Else
				DbSetOrder(6)
			EndIf

			lQuery    := .T.
			cAliasSC7 := "QRYSC7"

			cQuery	  := "SELECT "
			For nAuxCNT := 1 To Len( aEstruSC7 )

				cQuery += aEstruSC7[ nAuxCNT, 1 ]
				cQuery += ", "
			Next
			cQuery += " R_E_C_N_O_ RECSC7 "
			cQuery += " FROM "+RetSqlName("SC7") + " SC7 "
			cQuery += " WHERE "
			cQuery += "C7_FILENT = '"+xFilEnt(xFilial("SC7"))+"' AND "

			If HasTemplate( "DRO" ) .AND. FunName() == "MATA103" .AND. MV_PAR15 == 1 .And. ExistTemplate("cA100For")
				cQuery += "C7_FORNECE IN ( " + ExecTemplate("cA100For") + " )  AND "
			Else
				If Empty(cVar)
					If lConsLoja
						cQuery += " C7_FORNECE = '"+cA100For+"' AND "
						cQuery += " C7_LOJA = '"+cLoja+"' AND "
					Else
						cQuery += " C7_FORNECE = '"+cA100For+"' AND "
					Endif
				Else
					If lConsLoja
						cQuery += " C7_FORNECE = '"+cA100For+"' AND "
						cQuery += " C7_LOJA = '"+cLoja+"' AND "
						cQuery += " C7_PRODUTO = '"+cVar+"' AND "
					Else
						cQuery += " C7_FORNECE = '"+cA100For+"' AND "
						cQuery += " C7_PRODUTO = '"+cVar+"' AND "
					Endif
				Endif
			EndIf

			//Filtra os pedidos de compras de acordo com os contratos
			If lConsMedic
				If lNfMedic
					//Traz apenas os pedidos oriundos de medicoes
					cQuery += "C7_CONTRA<>'"  + Space( Len( SC7->C7_CONTRA ) )  + "' AND "
					cQuery += "C7_MEDICAO<>'" + Space( Len( SC7->C7_MEDICAO ) ) + "' AND "
				Else
					//Traz apenas os pedidos que nao possuem medicoes
					cQuery += "C7_CONTRA='"  + Space( Len( SC7->C7_CONTRA ) )  + "' AND "
					cQuery += "C7_MEDICAO='" + Space( Len( SC7->C7_MEDICAO ) ) + "' AND "
				EndIf
			EndIf
			//Filtra os Pedidos Bloqueados e Previstos
			cQuery += "C7_TPOP <> 'P' AND "
			If SuperGetMV("MV_RESTNFE") == "S"
				cQuery += "(C7_CONAPRO = 'L' OR C7_CONAPRO = ' ') AND "
			EndIf
			If !lToler
				cQuery += " SC7.C7_ENCER='"+Space(Len(SC7->C7_ENCER))+"' AND "
			EndIf
			If lToler
				cQuery += " (SC7.C7_QUJE + SC7.C7_QTDACLA) < SC7.C7_QUANT AND"
			EndIf
			cQuery += " SC7.C7_RESIDUO='"+Space(Len(SC7->C7_RESIDUO))+"' AND "

			cQuery += " SC7.D_E_L_E_T_ = ' ' "
			cQuery += " ORDER BY "+SqlOrder(SC7->(IndexKey()))

			cQuery := ChangeQuery(cQuery)

			//Ponto de Entrada: MT103QPC
			If ExistBlock("MT103QPC")
				cQueryQPC := ExecBlock("MT103QPC",.F.,.F.,{cQuery,2})
				If (ValType(cQueryQPC) == 'C' )
					cQuery := cQueryQPC
					cQuery := ChangeQuery(cQuery)
				EndIf
			EndIf

			If !lRetPed .And. (cAliasSC7)->(Alias()) == "QRYSC7"
				(cAliasSC7)->(dbCloseArea())
			EndIf
			dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSC7,.T.,.T.)

			For nX := 1 To Len(aEstruSC7)
				If aEstruSC7[nX,2]<>"C"
					TcSetField(cAliasSC7,aEstruSC7[nX,1],aEstruSC7[nX,2],aEstruSC7[nX,3],aEstruSC7[nX,4])
				EndIf
			Next nX

			If Empty(cVar)
				cCpoObri := "C7_LOJA|C7_PRODUTO|C7_QUANT|C7_DESCRI|C7_TIPO|C7_LOCAL|C7_OBSM"
			Else
				cCpoObri := "C7_LOJA|C7_PRODUTO|C7_QUANT|C7_PRECO|C7_TOTAL|C7_DESCRI|C7_LOCAL|C7_OBSM"
			Endif
			aCpoObri := Separa(cCpoObri,"|")

			AAdd(aCab," ")
			Aadd(aCampos,{"MARK","L","R",""})
			aadd(aTamCab,6)

			If (cAliasSC7)->(!Eof()) .Or. lForPCNF

				DbSelectArea("SX3")
				DbSetOrder(2)

				If lNfMedic .And. lConsMedic

					MsSeek("C7_MEDICAO")

					AAdd(aCab,x3Titulo())
					Aadd(aCampos,{SX3->X3_CAMPO,SX3->X3_TIPO,SX3->X3_CONTEXT,SX3->X3_PICTURE})
					aadd(aTamCab,CalcFieldSize(SX3->X3_TIPO,SX3->X3_TAMANHO,SX3->X3_DECIMAL,SX3->X3_PICTURE,X3Titulo()))

					MsSeek("C7_CONTRA")

					AAdd(aCab,x3Titulo())
					Aadd(aCampos,{SX3->X3_CAMPO,SX3->X3_TIPO,SX3->X3_CONTEXT,SX3->X3_PICTURE})
					aadd(aTamCab,CalcFieldSize(SX3->X3_TIPO,SX3->X3_TAMANHO,SX3->X3_DECIMAL,SX3->X3_PICTURE,X3Titulo()))

					MsSeek("C7_PLANILH")

					AAdd(aCab,x3Titulo())
					Aadd(aCampos,{SX3->X3_CAMPO,SX3->X3_TIPO,SX3->X3_CONTEXT,SX3->X3_PICTURE})
					aadd(aTamCab,CalcFieldSize(SX3->X3_TIPO,SX3->X3_TAMANHO,SX3->X3_DECIMAL,SX3->X3_PICTURE,X3Titulo()))

				EndIf

				MsSeek("C7_NUM")

				AAdd(aCab,x3Titulo())
				Aadd(aCampos,{SX3->X3_CAMPO,SX3->X3_TIPO,SX3->X3_CONTEXT,SX3->X3_PICTURE})
				aadd(aTamCab,CalcFieldSize(SX3->X3_TIPO,SX3->X3_TAMANHO,SX3->X3_DECIMAL,SX3->X3_PICTURE,X3Titulo()))

				DbSelectArea("SX3")
				DbSetOrder(1)
				MsSeek("SC7")
				While !Eof() .And. SX3->X3_ARQUIVO == "SC7"
					IF ( SX3->X3_BROWSE=="S".And.X3Uso(SX3->X3_USADO).And. AllTrim(SX3->X3_CAMPO)<>"C7_PRODUTO" .And. AllTrim(SX3->X3_CAMPO)<>"C7_NUM" .And. AllTrim(SX3->X3_CAMPO)<>"C7_SEGUM" .And.;
							If( lConsMedic .And. lNfMedic, AllTrim(SX3->X3_CAMPO)<>"C7_MEDICAO" .And. AllTrim(SX3->X3_CAMPO)<>"C7_CONTRA" .And. AllTrim(SX3->X3_CAMPO)<>"C7_PLANILH", .T. )).Or.;
							(aScan(aCpoObri,{|x| AllTrim(x) == AllTrim(SX3->X3_CAMPO)})>0)
						AAdd(aCab,x3Titulo())
						Aadd(aCampos,{SX3->X3_CAMPO,SX3->X3_TIPO,SX3->X3_CONTEXT,SX3->X3_PICTURE})
						aadd(aTamCab,CalcFieldSize(SX3->X3_TIPO,SX3->X3_TAMANHO,SX3->X3_DECIMAL,SX3->X3_PICTURE,X3Titulo()))
					EndIf
					dbSkip()
				Enddo
				
				nPosC7Prod := aScan(aCampos,{|x| x[1] == "C7_PRODUTO"})
				nPosC7Ped  := aScan(aCampos,{|x| Alltrim(x[1]) == "C7_NUM"})
				nPosC7Item := aScan(aCampos,{|x| Alltrim(x[1]) == "C7_ITEM"})
				
				DbSelectArea(cAliasSC7)
				Do While If(lQuery, ;
						(cAliasSC7)->(!Eof()), ;
						(cAliasSC7)->(!Eof()) .And. xFilEnt(cFilial)+cSeek == &(cCond))

					//Filtra os Pedidos Bloqueados, Previstos e Eliminados por residuo
					If !lQuery
						If (SuperGetMV("MV_RESTNFE") == "S" .And. (cAliasSC7)->C7_CONAPRO $ "BR") .Or. ;
								(cAliasSC7)->C7_TPOP == "P" .Or. !Empty((cAliasSC7)->C7_RESIDUO)
							dbSkip()
							Loop
						EndIf
					Endif

					nFreeQT := 0
					nPed    := aScan(aPedido,{|x| x[1] = (cAliasSC7)->C7_NUM+(cAliasSC7)->C7_ITEM})
					nFreeQT -= If(nPed>0,aPedido[nPed,2],0)

					For nAuxCNT := 1 To Len( aCols )
						If (nAuxCNT # n) .And. ;
							(aCols[ nAuxCNT,nPosPRD ] == (cAliasSC7)->C7_PRODUTO) .And. ;
							(aCols[ nAuxCNT,nPosPDD ] == (cAliasSC7)->C7_NUM)     .And. ;
							(aCols[ nAuxCNT,nPosITM ] == (cAliasSC7)->C7_ITEM)    .And. ;
							!ATail( aCols[ nAuxCNT ] )
							nFreeQT += aCols[ nAuxCNT,nPosQTD ]
						EndIf
					Next

					lRet103Vpc := .T.

					If lMt103Vpc
						If lQuery
							('SC7')->(MsGoto((cAliasSC7)->RECSC7))
						EndIf
						lRet103Vpc := Execblock("MT103VPC",.F.,.F.)
					Endif

					If lRet103Vpc
						nFreeQT := (cAliasSC7)->C7_QUANT-(cAliasSC7)->C7_QUJE-(cAliasSC7)->C7_QTDACLA-nFreeQT
						If	lToler .And. nFreeQT < 0
							nFreeQT := 0
						EndIf

						If nFreeQT > 0 .Or. lToler
							Aadd(aArrayF4,Array(Len(aCampos)))

							SB1->(DbSetOrder(1))
							SB1->(MsSeek(xFilial("SB1")+(cAliasSC7)->C7_PRODUTO))
							For nX := 1 to Len(aCampos)

								If aCampos[nX][3] != "V"
									If aCampos[nX][2] == "N"
										If Alltrim(aCampos[nX][1]) == "C7_QUANT"
											aArrayF4[Len(aArrayF4)][nX] :=Transform(nFreeQt,PesqPict("SC7",aCampos[nX][1]))
										ElseIf Alltrim(aCampos[nX][1]) == "C7_QTSEGUM"
											aArrayF4[Len(aArrayF4)][nX] :=Transform(ConvUm(SB1->B1_COD,nFreeQt,nFreeQt,2),PesqPict("SC7",aCampos[nX][1]))
										Else
											aArrayF4[Len(aArrayF4)][nX] := Transform((cAliasSC7)->(FieldGet(FieldPos(aCampos[nX][1]))),PesqPict("SC7",aCampos[nX][1]))
										Endif
									ElseIf aCampos[nX][1] == "MARK"
										aArrayF4[Len(aArrayF4)][nX] := oNo
									Elseif Alltrim(aCampos[nX][1]) == "C7_OBSM"
										If nMVObs == 0 //C7_OBSM
											cC7Obs := GetAdvFVal("SC7","C7_OBSM",xFilial("SC7") + (cAliasSC7)->C7_NUM + (cAliasSC7)->C7_ITEM,14)
										Elseif nMVObs == 1 //C7_OBS
											cC7Obs := GetAdvFVal("SC7","C7_OBS",xFilial("SC7") + (cAliasSC7)->C7_NUM + (cAliasSC7)->C7_ITEM,14)
										Elseif nMVObs == 2 //C7_OBSM + C7_OBS
											cObsM := GetAdvFVal("SC7","C7_OBSM",xFilial("SC7") + (cAliasSC7)->C7_NUM + (cAliasSC7)->C7_ITEM,14)
											cObs  := GetAdvFVal("SC7","C7_OBS",xFilial("SC7") + (cAliasSC7)->C7_NUM + (cAliasSC7)->C7_ITEM,14)

											If !Empty(cObsM) .And. !Empty(cObs)
												cC7Obs := "OBS: " + cObs
												cC7Obs += " |OBSM: " + cObsM
											Elseif !Empty(cObsM)
												cC7Obs := cObsM
											Elseif !Empty(cObs)
												cC7Obs := cObs
											Endif
										Endif
										aArrayF4[Len(aArrayF4)][nX] := cC7Obs
									Else
										aArrayF4[Len(aArrayF4)][nX] := (cAliasSC7)->(FieldGet(FieldPos(aCampos[nX][1])))
									Endif
								Else
									aArrayF4[Len(aArrayF4)][nX] := CriaVar(aCampos[nX][1],.T.)
									If Alltrim(aCampos[nX][1]) == "C7_CODGRP"
										aArrayF4[Len(aArrayF4)][nX] := SB1->B1_GRUPO
									EndIf
									If Alltrim(aCampos[nX][1]) == "C7_CODITE"
										aArrayF4[Len(aArrayF4)][nX] := SB1->B1_CODITE
									EndIf
								Endif

							Next

							aAdd(aArrSldo, {nFreeQT, IIF(lQuery,(cAliasSC7)->RECSC7,(cAliasSC7)->(RecNo()))})

							If lMT100C7D
								If lQuery
									('SC7')->(MsGoto((cAliasSC7)->RECSC7))
								EndIf
								aNew := ExecBlock("MT100C7D", .f., .f., aArrayF4[Len(aArrayF4)])
								If ValType(aNew) = "A"
									aArrayF4[Len(aArrayF4)] := aNew
								EndIf
							EndIf
						EndIf
					Endif
					(cAliasSC7)->(dbSkip())
				EndDo

				If ExistBlock("MT100C7L")
					ExecBlock("MT100C7L", .F., .F., { aArrayF4, aArrSldo })
				EndIf

				If (!Empty(aArrayF4) .Or. lForPCNF) .And. lRetPed

					// Ponto de entrada para redimensionar tela de selecao de pedidos por item
					If lMt103C7T
						aSizeC7T := ExecBlock("MT103C7T",.F.,.F.,{aSizePed})
						If ValType(aSizeC7T) == "A"
							aSizePed := aSizeC7T
						EndIf
					EndIf

					//Monta dinamicamente o bline do CodeBlock
					DEFINE MSDIALOG oDlg FROM aSizePed[1],aSizePed[2] TO aSizePed[3],aSizePed[4] TITLE OemToAnsi(STR0025+" - <F6> ") Of oMainWnd PIXEL //"Selecionar Pedido de Compra ( por item )"

					If lMT100C7C
						aNew := ExecBlock("MT100C7C", .f., .f., aCab)
						If ValType(aNew) == "A"
							aCab := aNew

							DbSelectArea("SX3")
			 				DbSetOrder(2)

							For nX := 1 to Len(aCab)
						    	If aScan(aCampos,{|x| x[1]= aCab[nX]})==0
        						 If SX3->(MsSeek(aCab[nX]))
        						 		Aadd(aCampos,{SX3->X3_CAMPO,SX3->X3_TIPO,SX3->X3_CONTEXT,SX3->X3_PICTURE})
        						 EndIf
   								EndIf
							Next nX
						EndIf
					EndIf

					//Calcula dimensıes
					oSize := FwDefSize():New(.T.,,,oDlg)
					oSize:AddObject( "CAB"		,  100, IIf(lForPCNF,35,20), .T., .T. ) // Totalmente dimensionavel
					oSize:AddObject( "LISTBOX" 	,  100, IIf(lForPCNF,65,80), .T., .T. ) // Totalmente dimensionavel


					oSize:lProp 	:= .T. // Proporcional
					oSize:aMargins 	:= { 3, 3, 3, 3 } // Espaco ao lado dos objetos 0, entre eles 3

					oSize:Process() 	   // Dispara os calculos

					oQual := TWBrowse():New(oSize:GetDimension("LISTBOX","LININI"),oSize:GetDimension("LISTBOX","COLINI"),;
						 				oSize:GetDimension("LISTBOX","XSIZE")-12,oSize:GetDimension("LISTBOX","YSIZE"),;
						 				,aCab,aTamCab,oDlg,,,,,,,,,,,,.F.,,.T.,,.F.,,,)
					

					If (!Empty(aArrayF4))
						oQual:SetArray(aArrayF4)
						oQual:bLDblClick := { || aArrayF4[oQual:nAt,1] := iif(aArrayF4[oQual:nAt,1] == oNo .And. IsProdBloq(aArrayF4[oQual:nAt,nPosC7Prod]) .And. Iif(lIntPms .And. FindFunction("PmsInt"), PmsInt( aArrayF4[oQual:nAt,nPosC7Ped], aArrayF4[oQual:nAt,nPosC7Item] ), .T.), oOk, oNo) }
						oQual:bLine := { || aArrayF4[oQual:nAT] }
					Else
						aLine := array(len(aCab) + 1)
						aLine[1] := oNo //… necess·rio ter a estrutura de LoadBitMap(Imagem) onde h· o checkbox
						for nX := 2 To Len(aLine)
							aLine[nX] := ''
						Next nX						  
						oQual:bLine := { || aLine}	
					EndIf
					
					If !Empty(cVar)
						@ oSize:GetDimension("CAB","LININI")+2 ,oSize:GetDimension("CAB","COLINI")   SAY OemToAnsi(STR0063) Of oDlg PIXEL SIZE 47 ,9 //"Produto"
						@ oSize:GetDimension("CAB","LININI") ,oSize:GetDimension("CAB","COLINI") +27 MSGET cVar PICTURE PesqPict('SB1','B1_COD') When .F. Of oDlg PIXEL SIZE 100,9
					Else
						@ oSize:GetDimension("CAB","LININI")+2 ,oSize:GetDimension("CAB","COLINI")  SAY OemToAnsi(STR0064) Of oDlg PIXEL SIZE 120 ,9 //"Selecione o Pedido de Compra"
					EndIf

					If lForPCNF
						@ oSize:GetDimension("CAB","LININI")+19 ,oSize:GetDimension("CAB","COLINI")   SAY OemToAnsi('Fornecedor:') Of oDlg PIXEL SIZE 120 ,9 //"Fornecedor:"
					   	@ oSize:GetDimension("CAB","LININI")+18 ,oSize:GetDimension("CAB","COLINI")+32 MSCOMBOBOX oComboBox VAR cComboFor ITEMS MTGetForRl(cA100For,cLoja) SIZE 221,10 OF oDlg PIXEL ON CHANGE A103LoadIt(lUsaFiscal,aPedido,oGetDAtu,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aGets, lTxNeg, nTaxaMoeda, @oQual, cComboFor, @aArrSldo, @aArrayF4)
					EndIf

					ACTIVATE MSDIALOG oDlg CENTERED ON INIT EnchoiceBar(oDlg,{|| (nOpca:=1,oDlg:End()) },{||oDlg:End()},,aButtons)

				  	For nX := 1 to Len(aArrayF4)
						If aArrayF4[nX][1] == oOk
						  	If lMt103Sel
						   		nOpca := If(ValType(nMT103Sel:=ExecBlock("MT103SEL",.F.,.F.,{aArrSldo[nX][2]}))=='N',nMT103Sel,nOpca)
						   	Endif
							If nOpca == 1
								nQtdItMark++
								If  (!Empty(aArrayF4))
									DbSelectArea("SC7")
									MsGoto(aArrSldo[nX][2])

			   				        // Verifica se o Produto existe Cadastrado na Filial de Entrada
								    DbSelectArea("SB1")
									DbSetOrder(1)
									MsSeek(xFilial("SB1")+SC7->C7_PRODUTO)
									If !Eof()
										//Verifica se a nota foi importada via TOTVS Colaboracao
										If lXmlxped .And. (( Type("l103Class") == "L" .And. l103Class ) .Or. !lUsaFiscal )		// Verifica se o vinculo esta sendo feito na classificacao da nota (l103Class) ou na pre nota (!lUsaFiscal)
											aAreaColab := GetArea()
											DbSelectArea("SDS")
											DbSetOrder(1)
											If MsSeek(xFilial("SDS")+cNFiscal+cSerie+cA100For+cLoja)
												lTColab := .T.
											EndIf
											RestArea(aAreaColab)
										EndIf

										If nQtdItMark == 1
											cItem := aCols[n][nPosItem]
										ElseIf nQtdItMark == 2
											cItem := acols[1][nPosItem]
											For nMIten := 2 to len(acols) // busca maior item da nota
												If cItem < acols[nMIten][nPosItem]
													cItem := acols[nMIten][nPosItem]
												Endif
											Next
											cItem := SomaIt(cItem)
										Else	
											citem := SomaIt(cItem)
										EndIf

										//-- Carrega o tipo de frete proveniente do pedido de compra.
										If lVldFret .And. !Empty(SC7->C7_TPFRETE) .And. MaFisFound("NF") .AND. Type("aNFEDanfe") == "A" .AND. len(aNfeDanfe) > 14 .and. Empty(aNfeDanfe[14])
											aCombo			:= CarregaTipoFrete()
											aNfeDanfe[14] 	:= SC7->C7_TPFRETE
											nPsTpFrt 		:= ascan(aCombo ,{|x| Substr(x,1,1) == Substr(aNFEDanfe[14],1,1)})
											If nPsTpFrt > 0
												oTpFrete:NAT := nPsTpFrt
												oTpFrete:refresh()
											EndIf
										Endif

										If	!ATail( aCols[ n ] ) .AND. nQtdItMark == 1
											NfePC2Acol(aArrSldo[nX][2],n,aArrSldo[nX][1],cItem,,@aRateio,aHeadSDE,@aColsSDE,,lTColab)
				        				Else
											NfePC2Acol(aArrSldo[nX][2],,aArrSldo[nX][1],cItem,,@aRateio,aHeadSDE,@aColsSDE,,lTColab)
				        				EndIf
										
										//Impede que o item do PC seja deletado pela getdados da NFE na movimentacao das setas
										If ValType( oGetDAtu ) == "O"
											oGetDAtu:lNewLine := .F.
											oGetDAtu:oBrowse:Refresh()
										Else
											If Type( "oGetDados" ) == "O"
												oGetDados:lNewLine:=.F.
												oGetDados:oBrowse:Refresh()
											EndIf
										EndIf
										If ExistBlock("M103PCIT")
											ExecBlock("M103PCIT",.F.,.F.)
										EndIf

										//Ponto de entrada para alterar a moeda, taxa, e check box de taxa negociada de acordo com o Pedido de Compras
										If ExistBlock("MT103TXPC") .And. SC7->C7_MOEDA != 1
											nPosItPc := aScan(aCols,{|x| AllTrim(x[nPosPc])==AllTrim(SC7->C7_NUM)})
											n103TXPC := ExecBlock("MT103TXPC",.F.,.F.)
											If ValType(n103TXPC) == "N"
												If n103TXPC > 0
													nTaxaMoeda := n103TXPC
												ElseIf nPosItPc > 0
													nTaxaMoeda := aCols[nPosItPc][nPosVlr] / SC7->C7_PRECO
												EndIf
												lTxNeg := .T.
												nMoedaCor := SC7->C7_MOEDA
											EndIf
										EndIf
									Else
			  						   Aviso("A103ItemPC",STR0302,{STR0461})
									EndIf
								Else 
									Help(" ",1,"A103F4")
								EndIf
							EndIf

							//Ponto de entrada para manipular o array de Frete/Seguro/Despesa do Pedido de Compras
							If (ExistBlock("MT103FRE"))
								aMT103FRE := ExecBlock("MT103FRE",.F.,.F.,aRateio)
								If (ValType(aMT103FRE) == "A")
										aRateio := aClone(aMT103FRE)
								EndIf
							EndIf

							//Rateio do valores de Frete/Seguro/Despesa do PC
							If lUsaFiscal
								Eval(bRefresh)
								lAtuDupPC := .T.
								Eval(bRefresh,6)
							Else
								nScan:= aScan(aCols,{|x| AllTrim(x[nPosPDD]) == Alltrim(SC7->C7_NUM) .And. Alltrim(x[nPosITM]) == Alltrim(SC7->C7_ITEM)})
								If nScan == n .Or. nScan == 0
									aGets[SEGURO] += aRateio[1]
									aGets[VALDESP]+= aRateio[2]
									//Somente acrescenta frete do pedido, caso n„o tenha no documento
									If aGets[FRETE] == 0
										aGets[FRETE]  += aRateio[3]
									Endif
								EndIf
							EndIf
						EndIf
					Next nX
				ElseIf !lRetPed
				Else
					Help(" ",1,"A103F4")
				EndIf
			Else
				Help(" ",1,"A103F4")
			EndIf
		Else
			Help('   ',1,'A103TIPON')
		EndIf
	Else
		Help('   ',1,'A103CAB')
	EndIf

Endif

If lRetPed
	If lQuery
		DbSelectArea(cAliasSC7)
		dbCloseArea()
		DbSelectArea("SC7")
	Endif

	SetKey(VK_F4,bSavSetKey)
	SetKey(VK_F5,bSavKeyF5)
	SetKey(VK_F6,bSavKeyF6)
	SetKey(VK_F7,bSavKeyF7)
	SetKey(VK_F8,bSavKeyF8)
	SetKey(VK_F9,bSavKeyF9)
	SetKey(VK_F10,bSavKeyF10)
	SetKey(VK_F11,bSavKeyF11)
	RestArea(aAreaSA2)
	RestArea(aAreaSC7)
	RestArea(aAreaSB1)
	RestArea(aArea)
Else
	aRetPed := aArrayF4
	aArrSldoAux := aArrSldo
EndIf
If lDKD .And. lTabAuxD1 .And. FindFunction("gatilhadkd") 
	gatilhadkd()  
Endif
Return

//-------------------------------------------------------------------
/*/{Protheus.doc} A103LoadIt
Carregamento de Itens de pedido de fornecedores diferentes

@author guilherme.pimentel
@since 01/09/2014
@version 1.0
@Return lRet
/*/
//-------------------------------------------------------------------

Function A103LoadIt(lUsaFiscal,aPedido,oGetDAtu,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aGets, lTxNeg, nTaxaMoeda, oQual, cComboFor, aArrSldo, aArrayF4)

Local lRet        := .T.
Local aRetPed     := {}
Local cAntA100For := cA100For
Local cAntLoja    := cLoja
Local cCodLoj     := ""

cCodLoj  := SubStr(cComboFor, At(' | ',cComboFor)+3, Len(cComboFor))
cCodLoj  := SubStr(cCodLoj,1, At(' - ',cCodLoj)-1)

cA100For := SubStr(cCodLoj, 1, At('/',cCodLoj)-1)
cLoja    := SubStr(cCodLoj, At('/',cCodLoj)+1, Len(cCodLoj))

A103ItemPC(lUsaFiscal,aPedido,oGetDAtu,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aGets, lTxNeg, nTaxaMoeda,@aRetPed, @aArrSldo)

aArrayF4 := aClone(aRetPed)

oQual:SetArray(aArrayF4)
oQual:bLDblClick := { || aArrayF4[oQual:nAt,1] := iif(aArrayF4[oQual:nAt,1] == oNo, oOk, oNo) }
oQual:bLine := { || aArrayF4[oQual:nAT] }
oQual:Refresh()

cA100For := cAntA100For
cLoja := cAntLoja

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} A103LoadPd
Carregamento do pedido de fornecedores diferentes

@author taniel.silva
@since 02/09/2014
@version 1.0
@Return lRet
/*/
//-------------------------------------------------------------------

Function A103LoadPd(lUsaFiscal,aGets,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aHeadSEV, aColsSEV, lTxNeg, nTaxaMoeda, oListBox, cComboFor, aF4For, bLine, aRecSC7)

Local lRet        := .T.
Local aRetPed     := {}
Local cAntA100For := cA100For
Local cAntLoja    := cLoja
Local cCodLoj     := ""

cCodLoj  := SubStr(cComboFor, At(' | ',cComboFor)+3, Len(cComboFor))
cCodLoj  := SubStr(cCodLoj,1, At(' - ',cCodLoj)-1)

cA100For := SubStr(cCodLoj, 1, At('/',cCodLoj)-1)
cLoja    := SubStr(cCodLoj, At('/',cCodLoj)+1, Len(cCodLoj))

A103ForF4(lUsaFiscal,aGets,lNfMedic,lConsMedic,aHeadSDE,aColsSDE,aHeadSEV, aColsSEV, lTxNeg, nTaxaMoeda, @aRetPed, oListBox, @aRecSC7)

//AtualizaÁ„o do Array antigo
aF4For := aClone(aRetPed)
bLine	:= oListBox:bLine

oListBox:SetArray(aF4For)
If (!Empty(aF4For))
	oListBox:bLDblClick := { || aF4For[oListBox:nAt,1] := !aF4For[oListBox:nAt,1] }
Else
	oListBox:bLDblClick := {||}
EndIf

oListBox:bLine := bLine

oListBox:Refresh()

cA100For := cAntA100For
cLoja := cAntLoja

Return lRet

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥a103PesqP ≥ Autor ≥ Henry Fila            ≥ Data ≥17.07.2002 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥Seek no browse de itens de pedidos de compra                 ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpA1 : Array das descricoes dos cabecalhos                  ≥±±
±±≥          ≥ExpA2 : Array com os campos                                  ≥±±
±±≥          ≥ExpA3 : Array com os conteudos                               ≥±±
±±≥          ≥ExpO4 : Objeto do listbox                                    ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥Nenhum                                                       ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Esta rotina tem como objetivo abrir uma janela de pesquisa   ≥±±
±±≥          ≥em browses de getdados poisicionando na llinha caso encontre ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Generico                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/

Static Function a103PesqP(aCab,aCampos,aArrayF4,oQual)

Local aCpoBusca	:= {}
Local aCpoPict	:= {}
Local aComboBox	:= { AllTrim( STR0168 ) , AllTrim( STR0169 ) , AllTrim( STR0170 ) } //"Exata"###"Parcial"###"Contem"
Local bAscan	:= { || .F. }
Local cPesq		:= Space(30)
Local cBusca	:= ""
Local cTitulo	:= OemtoAnsi(STR0001)  //"Pesquisar"
Local cOpcAsc	:= aComboBox[1]	//"Exata"
Local cAscan	:= ""
Local nOpca		:= 0
Local nPos		:= 0
Local nx		:= 0
Local nTipo		:= 1
Local nBusca	:= Iif(oQual:nAt == Len(aArrayF4) .Or. oQual:nAt == 1, oQual:nAt, oQual:nAt+1 )
Local oDlg
Local oBusca
Local oPesq1
Local oPesq2
Local oPesq3
Local oPesq4
Local oComboBox

For nX := 1 to Len(aCampos)
	AAdd(aCpoBusca,aCab[nX])
	AAdd(aCpoPict,aCampos[nX][4])
Next

If Len(aCampos) > 0 .And. Len(aArrayF4) > 0

	DEFINE MSDIALOG oDlg TITLE OemtoAnsi(cTitulo)  FROM 00,0 TO 100,490 OF oMainWnd PIXEL

	@ 05,05 MSCOMBOBOX oBusca VAR cBusca ITEMS aCpoBusca SIZE 206, 36 OF oDlg PIXEL ON CHANGE (nTipo := oBusca:nAt,A103ChgPic(nTipo,aCampos,@cPesq,@oPesq1,@oPesq2,@oPesq3,@oPesq4))

	@ 022,005 MSGET oPesq1 VAR cPesq Picture "@!" SIZE 206, 10 Of oDlg PIXEL
	@ 022,005 MSGET oPesq2 VAR cPesq Picture "@!" SIZE 206, 10 Of oDlg PIXEL
	@ 022,005 MSGET oPesq3 VAR cPesq Picture "@!" SIZE 206, 10 Of oDlg PIXEL
	@ 022,005 MSGET oPesq4 VAR cPesq Picture "@!" SIZE 206, 10 Of oDlg PIXEL

	oPesq1:Hide()
	oPesq2:Hide()
	oPesq3:Hide()
	oPesq4:Hide()

	Do Case
		Case aCampos[1][2] == "C"
			DbSelectArea("SX3")
			DbSetOrder(2)
			If MsSeek(aCampos[1][1])
				If !Empty(SX3->X3_F3)
					oPesq2:cF3 := SX3->X3_F3
					oPesq1:Hide()
					oPesq2:Show()
					oPesq3:Hide()
					oPesq4:Hide()
				Else
					oPesq1:Show()
					oPesq2:Hide()
					oPesq3:Hide()
					oPesq4:Hide()
				Endif
			Endif

		Case aCampos[1][2] == "D"
			oPesq1:Hide()
			oPesq2:Hide()
			oPesq3:Show()
			oPesq4:Hide()

		Case aCampos[1][2] == "N"
			oPesq1:Hide()
			oPesq2:Hide()
			oPesq3:Hide()
			oPesq4:Show()
	EndCase

	DEFINE SBUTTON oBut1 FROM 05, 215 TYPE 1 ACTION ( nOpca := 1, oDlg:End() ) ENABLE of oDlg
	DEFINE SBUTTON oBut1 FROM 20, 215 TYPE 2 ACTION ( nOpca := 0, oDlg:End() )  ENABLE of oDlg

	@ 037,005 SAY OemtoAnsi(STR0035) SIZE 050,10 OF oDlg PIXEL //Tipo
	@ 037,030 MSCOMBOBOX oComboBox VAR cOpcAsc ITEMS aComboBox SIZE 050,10 OF oDlg PIXEL

	ACTIVATE MSDIALOG oDlg CENTERED

	If nOpca == 1
		Do Case
			Case aCampos[nTipo][2] == "C"
				IF ( cOpcAsc == aComboBox[1] )	//Exata
					cAscan := Padr( Upper( cPesq ) , TamSx3(aCampos[nTipo][1])[1] )
					bAscan := { |x| cAscan == Upper( x[ nTipo ] ) }
				ElseIF ( cOpcAsc == aComboBox[2] )	//Parcial
					cAscan := Upper( AllTrim( cPesq ) )
					bAscan := { |x| cAscan == Upper( SubStr( Alltrim( x[nTipo] ) , 1 , Len( cAscan ) ) ) }
				ElseIF ( cOpcAsc == aComboBox[3] )	//Contem
					cAscan := Upper( AllTrim( cPesq ) )
					bAscan := { |x| cAscan $ Upper( Alltrim( x[nTipo] ) ) }
				EndIF
				nPos := Ascan( aArrayF4 , bAscan )

			Case aCampos[nTipo][2] == "N"
				nPos := Ascan(aArrayF4,{|x| Transform(cPesq,PesqPict("SC7",aCampos[nTipo][1])) == x[nTipo]},nBusca)

			Case aCampos[nTipo][2] == "D"
				nPos := Ascan(aArrayF4,{|x| Dtos(cPesq) == Dtos(x[nTipo])},nBusca)
		EndCase

		If nPos > 0
			oQual:bLine := { || aArrayF4[oQual:nAT] }
			oQual:nFreeze := 1
			oQual:nAt := nPos
			oQual:Refresh()
			oQual:SetFocus()
		Else
			Help(" ",1,"REGNOIS")
		Endif
	EndIf
Endif

Return

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥a103ChgPic≥ Autor ≥ Henry Fila            ≥ Data ≥17.07.2002 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥Atualiza picture na funcao a103PespP                         ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpN1 : Posicao do campo no Array                            ≥±±
±±≥          ≥ExpA2 : Array com os dados dos campos                        ≥±±
±±≥          ≥ExpX3 : Pesquisa                                             ≥±±
±±≥          ≥ExpO4 : Objeto de pesquisa                                   ≥±±
±±≥          ≥ExpO5 : Objeto de pesquisa                                   ≥±±
±±≥          ≥ExpO6 : Objeto de pesquisa                                   ≥±±
±±≥          ≥ExpO7 : Objeto de pesquisa                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥Nenhum                                                       ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Esta rotina tem como objetivo tratar a picture do campo sele ≥±±
±±≥          ≥cionado na funcao GdSeek                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Generico                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Static Function A103ChgPic(nTipo,aCampos,cPesq,oPesq1,oPesq2,oPesq3,oPesq4)

Local cPict   := ""
Local aArea   := GetArea()
Local aAreaSX3:= SX3->(GetArea())
Local bRefresh

DbSelectArea("SX3")
DbSetOrder(2)
If MsSeek(aCampos[nTipo][1])
	Do case
		Case aCampos[nTipo][2] == "C"
			If !Empty(SX3->X3_F3)
				oPesq2:cF3 := SX3->X3_F3
				oPesq1:Hide()
				oPesq2:Show()
				oPesq3:Hide()
				oPesq4:Hide()
				bRefresh := { || oPesq2:oGet:Picture := cPict,oPesq2:Refresh() }
			Else
				oPesq1:Show()
				oPesq2:Hide()
				oPesq3:Hide()
				oPesq4:Hide()
				bRefresh := { || oPesq1:oGet:Picture := cPict,oPesq1:Refresh() }
			Endif

		Case aCampos[nTipo][2] == "D"
			oPesq1:Hide()
			oPesq2:Hide()
			oPesq3:Show()
			oPesq4:Hide()
			bRefresh := { || oPesq3:oGet:Picture := cPict,oPesq3:Refresh() }

		Case aCampos[nTipo][2] == "N"
			oPesq1:Hide()
			oPesq2:Hide()
			oPesq3:Hide()
			oPesq4:Show()
			bRefresh := { || oPesq4:oGet:Picture := cPict,oPesq4:Refresh() }
	EndCase
Endif

If nTipo > 0
	cPesq := CriaVar(aCampos[nTipo][1],.F.)
	cPict := aCampos[nTipo][4]
EndIf

Eval(bRefresh)

RestArea(aAreaSX3)
RestArea(aArea)

Return

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103GrvAtf≥ Autor ≥ Edson Maricate        ≥ Data ≥ 06.01.98 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Gravacao do Ativo Fixo                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥Nenhum                                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥nOpc    : 1 - Inclusao / 2 - Exclusao                       ≥±±
±±≥          ≥cBase   : Codigo Base do Ativo                              ≥±±
±±≥          ≥cItem   : Item da Nota Fiscal                               ≥±±
±±≥          ≥cCodCiap: Codigo do Ciap Gerado                             ≥±±
±±≥          ≥nVlrCiap: Valor do Ciap Gerado                              ≥±±
±±≥          ≥aRateio	-> Array: Rateio de compras que integrara com o   		≥±±
±±≥          ≥			rateio da ficha de ativo (SNV)					  		≥±±
±±≥          ≥	aRateio[i,1] -> char: Item do Documento de Entrada		  		≥±±
±±≥          ≥	aRateio[i,2] -> array: acols do rateio do item do Doc. Entrada	≥±±
±±≥          ≥		aRateio[i,2,j] -> array: linha do acols 					≥±±
±±≥          ≥		aRateio[i,2,j,1] -> char: item do rateio 					≥±±
±±≥          ≥		aRateio[i,2,j,2] -> Numeric: Percentual 					≥±±
±±≥          ≥		aRateio[i,2,j,3] -> char: Centro de Custo 					≥±±
±±≥          ≥		aRateio[i,2,j,4] -> char: Conta Contabil 					≥±±
±±≥          ≥		aRateio[i,2,j,5] -> char: Item da Conta Contabil			≥±±
±±≥          ≥		aRateio[i,2,j,6] -> char: Classe de valor					≥±±
±±≥          ≥		aRateio[i,2,j,7] -> boolean: 								≥±±
±±≥          ≥cChave  : Chave de busca para excluir ajuste de Nt. Cr/Db.        ≥±±
±±≥          ≥aDIfDec : Array com controle das diferenÁas de decimais a partir  ≥±±
±±≥          ≥          Da terceira casa decimal para o ICMS do bem.            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Observacao≥Este Programa grava um ativo por item de NF, alterando-se o       ≥±±
±±≥          ≥Item do ativo. Nem todos os dados do Ativo serao gravados         ≥±±
±±≥          ≥pois nao ha todas as informacoes na nota fiscal e o classidor     ≥±±
±±≥          ≥da Nota Fiscal nao tem condicoes de faze-lo.                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador         ≥Manutencao Efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥			 ≥					   ≥Incluida a integracao do rateio de compras  ≥±±
±±≥27/04/2011≥Fernando Radu Muscalu≥com o rateio de gastos da depreciacao dos   ≥±±
±±≥          ≥                     ≥bens  									 	≥±±
±±≥ 15/06/11 ≥ Danilo Dias         ≥ GravaÁ„o/Exclus„o de ajuste de Nt. Cr/Db   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103GrvAtf( nOpc, cBase, cItem, cCodCiap, nVlrCiap, aCIAP, aVlrAcAtf,aRateio, cChave,aDIfDec, aRecSF1Ori, cChaveSD1, cBaseDigit, lA12DTHR )

Local aArea				:= GetArea()
Local nUsado			:= 0
Local nVlRatF			:= 0
Local nQtdOri			:= GetQOri(xFilial("SD1"),SD1->D1_NFORI,SD1->D1_SERIORI,SD1->D1_ITEMORI,SD1->D1_COD,SD1->D1_FORNECE,SD1->D1_LOJA)
Local nQtdD1			:= Iif((SD1->D1_TIPO == "C" .Or. SD1->D1_TIPO == "I").And. SD1->D1_ORIGLAN <>"FR",Iif(nQtdOri > 0,nQtdOri,1),Iif((SD1->D1_TIPO == "C" .Or.SD1->D1_TIPO == "I").And. SD1->D1_ORIGLAN =="FR",1,SD1->D1_QUANT))
Local lGravou    		:= .F.
Local lAtuSX6    		:= .F.
Local nMoeda			:= iif(cPaisLoc == "BRA",1,SF1->F1_MOEDA)
Local nAtfQtdIt			:= iif(SF4->F4_BENSATF == "1".And.nQtdD1>=1,nQtdD1,1)
Local bValAtf        	:= { || &( SuperGetMv("MV_VLRATF",.F.,'(SD1->D1_TOTAL-SD1->D1_VALDESC)+If(SF4->F4_CREDIPI=="S",SD1->D1_VALIPI,0)-IIf(SF4->F4_CREDICM=="S",SD1->D1_VALICM,0)'))}
Local aRetAtf			:= {}
Local nVlrMoed			:= 0
Local aTamVOrig			:= {}
Local lF4BensATF		:= iif(SF4->F4_BENSATF == "1".And.nQtdD1>=1,.T.,.F.)
Local lATFDCBA			:= SuperGetMv("MV_ATFDCBA",.F.,"0") == "1" // "0"- Desmembra itens / "1" - Desmembra codigo base
Local aATFPMS			:= {}
Local aParamAFN			:= aClone(aRatAFN)
//Salva ambiente
Local aAreaSF1 			:= SF1->(GetArea())
Local aAreaSD1  		:= SD1->(GetArea())
Local aAreaSN1  		:= SN1->(GetArea())
Local aAreaSN3  		:= SN3->(GetArea())
Local aAreaSN4  		:= SN4->(GetArea())
Local aAreaSB1  		:= SB1->(GetArea())
Local aTmpSN1   		:= {}
Local aTmpSN3			:= {}
Local aTmpSD1   		:= {}
Local aTmpSN4   		:= {}
Local aItens			:= {}
Local aAux				:= {}
Local aCab				:= {}
//Vari·veis locais
Local lAjustaNCD 		:= SuperGetMV( "MV_ATFNCRD", .T., .F. )
Local cRotBaixa  		:= SuperGetMV( "MV_ATFRTBX", .T., "ATFA030")
Local lATFNFIN   		:= SuperGetMV( "MV_ATFNFIN", .T., .T. )
Local lATFVdProp 		:= SuperGetMV( "MV_ATFVDPR", .T., .T. )
Local cDaCiap   		:= GetNewPar("MV_DACIAP",'S') //Utilizado para calc. ICMS no CIAP. Se S= Considera valor de dif. aliquota se N= Nao considera dif. aliquota
Local lRet       		:= .T.
Local nI         		:= 0
Local nJ         		:= 0
Local nX         		:= 0
Local nMoedas    		:= AtfMoedas()
Local cMoeda     		:= ""
Local nVlrOrig   		:= 0
Local nItens    		:= 0
Local cUltItem  		:= ""
Local cUltCBase  		:= ""
Local aVlrTipo01 		:= {}
Local cIdMov     		:= ""
Local lMontaRat  		:= .F.
Local aNewRat    		:= {}
Local aRelImp    		:= MaFisRelImp("MT100",{ "SD1" })
Local nScanPis 	 		:= 0
Local cCpBsPisEn 		:=	 ""
Local nScanCof 	 		:= 0
Local cCpBsCofEn 		:= ""
Local lStrutNCD 		:= !Empty( SN1->( IndexKey(8) ) )
Local cLoopEnt			:= ""
Local cEntConDB	 		:= ""
Local cEntConCR	 		:= ""
Local nQtdEnt 			:= CtbQtdEntd()
Local aParam			:= {}
Local xCab 				:= {}
Local cQryFN7 			:= ""
Local nTamDesc       	:= TamSx3("N1_DESCRIC")[1]
Local aPE 				:= {}
Local lRatAtiv			:= SuperGetMv('MV_RATATIV',,.F.)
Local cFunAtf 			:= "A103GrvAtf"
Local nQtdAtf			:= 0
Local nVlrAdc 			:= 0 //Valor para ser agregado/atualizado nos bens.
Local nQtdAglut			:= 1//Qtd de produtos iguais q foram aglutinados no mata116.
Local cItemPrd			:= ""
Local nVlrRat 			:= 0
Local nVlrIcm 			:= 0
Local cCodProd 			:= ""
Local cBaseSD1 			:= ""
Local cItBsSD1  		:= ""
Local aAuxAtu			:= {}
Local aAuxICM			:= {}
Local aAtuBens			:= {} //Array de atualizaÁ„o de bens.
Local cOpc 				:= "1"//OpÁ„o --> 1 = Atualiza os valores / 2 = Estorno de valores.

Local cAtfMoed	AS CHARACTER
Local cBaseN3	AS CHARACTER
Local cB1FAGrou	AS CHARACTER
Local cB1Desc	AS CHARACTER

STATIC aCrVSN3	 	:= {}
STATIC lCarrega		:= .T.

Default aCIAP		:= {}
Default aVlrAcAtf	:=	{0,0,0,0,0}
Default aRateio		:= {}
Default cChave		:= ""
Default aDIfDec		:= {0,.F.,0}
Default aRecSF1Ori  := {}
Default cChaveSD1   := {}
Default cBaseDigit  := "" //base do ativo digitada manualmente, exemplo: NF de garantia estendida.
Default lA12DTHR	:= .F.

Private lMsErroAuto := .F.
aAdd( aParam, {"MV_PAR01", 2} )
aAdd( aParam, {"MV_PAR02", 1} )
aAdd( aParam, {"MV_PAR05", 2} )

If (ExistBlock ("ATFA006102")) .And. !lA12DTHR
	aRetAtf	:=	ExecBlock ("ATFA006102", .F., .F., {nOpc, cBase, cItem, cCodCiap, nVlrCiap})
	If (aRetAtf[1])
		cBase	:=	aRetAtf[2]
		Return (.T.)
	EndIf
EndIf

If Len(aRateio) == 0 .Or. ValType(aRateio) <> "A"
	aRateio   := {}
	lMontaRat := .T.
EndIf

//Tratamento para arredondamento das casas decimais dos valores a gravar
AADD(aTamVOrig,TamSx3("N3_VORIG1"))
AADD(aTamVOrig,TamSx3("N3_VORIG2"))
AADD(aTamVOrig,TamSx3("N3_VORIG3"))
AADD(aTamVOrig,TamSx3("N3_VORIG4"))
AADD(aTamVOrig,TamSx3("N3_VORIG5"))

//A rotina a seguir e uma protecao devido a falha no dicionario padrao onde a expressao cadastrada no parametro MV_VLRATF foi cadastrada com
//Aspas, isso faz com que a macro do codblock retorne uma string.
nVlRatF := Eval( bValAtf )
If ValType(nVlRatF) <> "N"
	nVlRatF := &(nVlRatF)
EndIf

If nOpc == 1
	Private lMsErroAuto := .F.

	//Calcula o Codigo Base do Ativo
	If ExistBlock("MT103AFN")
		aATFPMS := ExecBlock("MT103AFN",.F.,.F.,{aParamAFN,SF4->F4_ATUATF,SF4->F4_BENSATF,lATFDCBA})
		If ValType(aATFPMS) == "A" .and. ValType(aATFPMS[1]) == "C" .and. ValType(aATFPMS[2]) == "C"
			cBase    := aATFPMS[1]
			cItem    := aATFPMS[2]
		EndIf
	Endif

	If ((Empty(cBase)) .OR. (lF4BensATF .AND. lATFDCBA .AND. !lA12DTHR)) .AND. cPaisLoc != "RUS"
		SuperGetMV("MV_CBASEAF",.F.)
		If ( RecLock("SX6") )
			cBase := &(SuperGetMV("MV_CBASEAF",.F.))
			If ( AllTrim(cBase) $ SuperGetMV("MV_CBASEAF",.F.) )
				lAtuSX6 := .T.
			EndIf
		EndIf
		DbSelectArea("SN1")
		DbSetOrder(1)
		While MsSeek(xFilial("SN1")+cBase)
			cBase := Soma1(cBase,Len(SN1->N1_CBASE))
		EndDo
		If ( lAtuSX6 )
			PutMV("MV_CBASEAF",'"'+Soma1(cBase,Len(SN1->N1_CBASE))+'"')
		EndIf
		SX6->(MsUnLock())
	EndIf
	//Alexandra Menyashina (29/03/18): FI-FA-26-15 Purchase of fixed asset
	If lIsRussia .And. Empty(cBase)
		SB1->(DbSetOrder(1))
		cB1FAGrou	:= ""
		cB1Desc		:= ""
		If SB1->(DBSeek(xFilial("SB1")+SD1->D1_COD))
			cB1FAGrou	:= SB1->B1_FAGROUP
			cB1Desc		:= SB1->B1_DESC
		Else
			Help("",1,"A103GrvAtfEmPr",,STR0509,1,0)	// "Product is not found"
			lRet := .F.
		EndIf
		cAtfMoed := GetNewPar("MV_ATFMOED", "")
		oMdlAF12	:= FWLoadModel("ATFA012")
		oMdlAF12:SetOperation(MODEL_OPERATION_INSERT)
		oMdlAF12:Activate()
		cItem	:= StrZero(1, TamSX3("D1_ITEM")[1])
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_ITEM",cItem)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_GRUPO", cB1FAGrou)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_AQUISIC", SD1->D1_DTDIGIT)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_DESCRIC", SubStr(cB1Desc,1,nTamDesc))
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_QUANTD", nQtdD1 / nAtfQtdIt)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_FORNEC", SD1->D1_FORNECE)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_LOJA", SD1->D1_LOJA)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_NSERIE", SD1->D1_SERIE)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_NFISCAL", SD1->D1_DOC)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_LOJA", SD1->D1_LOJA)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_CHASSIS", SD1->D1_CHASSI)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_PLACA", SD1->D1_PLACA)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_NFESPEC", SF1->F1_ESPECIE)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_NFITEM", SD1->D1_ITEM)
		lRet := lRet .AND. oMdlAF12:GetModel("SN1MASTER"):SetValue("N1_PRODUTO", SD1->D1_COD)
		
		If lRet
			cBase	:= Rtrim(oMdlAF12:GetModel("SN1MASTER"):GetValue("N1_CBASE"))
		EndIf
		For nX := 1 To oMdlAF12:GetModel("SN3DETAIL"):Length()
			oMdlAF12:GetModel("SN3DETAIL"):GoLine(nX)

			lRet := lRet .AND. oMdlAF12:GetModel("SN3DETAIL"):SetValue("N3_CUSTBEM", SD1->D1_CC)
			lRet := lRet .AND. oMdlAF12:GetModel("SN3DETAIL"):SetValue("N3_CCUSTO", SD1->D1_CC)
			lRet := lRet .AND. oMdlAF12:GetModel("SN3DETAIL"):SetValue("N3_SUBCCON", SD1->D1_ITEMCTA)
			lRet := lRet .AND. oMdlAF12:GetModel("SN3DETAIL"):SetValue("N3_CLVLCON", SD1->D1_CLVL)
			lRet := lRet .AND. oMdlAF12:GetModel("SN3DETAIL"):SetValue("N3_VORIG"+cAtfMoed, SD1->D1_CUSTO/SD1->D1_QUANT)
		Next nX
		If ! lRet
			RU01MVCERR(oMdlAF12)
			Help("",1,"A103GrvAtfRusAutoFA",,STR0508,1,0)	// "Error setting values of new balances register"
		EndIf
		cBaseN3	:= ""
		If lRet 
			lRet	:= lRet .And. oMdlAF12:VldData()
			lRet	:= lRet .And. oMdlAF12:CommitData()
			If lRet
				cBaseN3	:= oMdlAF12:GetModel("SN1MASTER"):GetValue("N1_CBASE")
			Else
				RU01MVCERR(oMdlAF12)
			EndIf
		EndIf

		oMdlAF12:DeActivate()	
		//TODO: Alexandra Menyashina(04/04/18) - delit this when FrameTeam fixed bug of SN3
		If ! Empty(cBaseN3)
			RU01FIXBAI(cBaseN3)
		EndIf

		lGravou	:= lRet

	ElseIf ( !Empty(cBase) )

		//Posiciono o campo correto com a aliquota do PIS da tabela SD1
		If !Empty( nScanPis := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_ALIQPS2"} ) )
			cCpBsPisEn := aRelImp[nScanPis,2]
		EndIf

		//Posiciono o campo correto com a aliquota da COFINS da tabela SD1
		If !Empty( nScanCof := aScan(aRelImp,{|x| x[1]=="SD1" .And. x[3]=="IT_ALIQCF2"} ) )
			cCpBsCofEn := aRelImp[nScanCof,2]
		EndIf

		//Posiciona Registros Necessarios
		DbSelectArea("SB1")
		DbSetOrder(1)
		MsSeek(xFilial("SB1")+SD1->D1_COD)
		
		//Preenchimento das Variaveis referentes ao SN1
		aAdd(aCab,{"N1_CBASE" , cBase})
		aAdd(aCab,{"N1_ITEM" , cItem})
		aAdd(aCab,{"N1_AQUISIC" , SD1->D1_DTDIGIT})
		aAdd(aCab,{"N1_DESCRIC" , SubStr(SB1->B1_DESC,1,nTamDesc)})
		aAdd(aCab,{"N1_QUANTD" , nQtdD1 / nAtfQtdIt})
		aAdd(aCab,{"N1_FORNEC" , SD1->D1_FORNECE})
		aAdd(aCab,{"N1_LOJA" , SD1->D1_LOJA})
		aAdd(aCab,{"N1_NSERIE" , SD1->D1_SERIE})
		aAdd(aCab,{"N1_NFISCAL" , SD1->D1_DOC})
		aAdd(aCab,{"N1_CHASSIS" , SD1->D1_CHASSI})
		aAdd(aCab,{"N1_PLACA" , SD1->D1_PLACA})
		aAdd(aCab,{"N1_PATRIM" , "N"})

		If cPaisLoc == "BRA"
			//Acumula valor da diferenca a partir da 3 casa decimal em aDIfDec[1]
			aDIfDec[1]+= (nVlrCiap / nAtfQtdIt) - NoRounD(nVlrCiap / nAtfQtdIt,2)
			//Se aDIfDec[2] == .T. ent„o quer dizer que È o ˙ltimo bem, e neste ser· somado os valores de diferenÁas a partir da 3 casa decimal dos bens anteriores.
			If SF4->F4_CREDICM == 'S'
				If aDIfDec[2] == .T.
					aAdd(aCab,{"N1_ICMSAPR" , NoRound((nVlrCiap / nAtfQtdIt),2) + aDIfDec[1]})
				Else
					aAdd(aCab,{"N1_ICMSAPR" , NoRound((nVlrCiap / nAtfQtdIt),2)})
				EndIF
			Else
				aAdd(aCab,{"N1_ICMSAPR" , 0})	
			EndIf	

			aAdd(aCab,{"N1_CSTPIS"  , SF4->F4_CSTPIS })
			aAdd(aCab,{"N1_CSTCOFI" , SF4->F4_CSTCOF })	
			aAdd(aCab,{"N1_ALIQPIS" , (SD1->&(cCpBsPisEn)-SF4->F4_MALQPIS) })
			aAdd(aCab,{"N1_ALIQCOF" , (SD1->&(cCpBsCofEn)-SF4->F4_MALQCOF) })
			aAdd(aCab,{"N1_CODCIAP" , cCodCiap})
			aAdd(aCab,{"N1_ORIGCRD" , If(Left(SD1->D1_CF,1)=="3","1","0") })
		EndIf

		aAdd(aCab,{"N1_STATUS" , "0"})
		aAdd(aCab,{"N1_NFESPEC" , SF1->F1_ESPECIE })
		aAdd(aCab,{"N1_NFITEM"  , SD1->D1_ITEM })
		aAdd(aCab,{"N1_PRODUTO" , SD1->D1_COD })

		//Preenchimento das Variaveis referentes ao SN3
		If cPaisLoc == "BRA"
			aAdd(aAux,{"N3_TIPO",IIf( SF4->F4_COMPONE == '1', "03","01") })
		Else
			aAdd(aAux,{"N3_TIPO","01" })
		EndIf

		aAdd(aAux,{"N3_CCONTAB", ""  }) //Campo interfere na classificaÁ„o do bem mÛdulo de ativo fixo e n„o deve ser preenchido.
		aAdd(aAux,{"N3_CUSTBEM", SD1->D1_CC  })
		// Nao grava este campo em hipotese alguma pois o controle de classificacao do Ativo
		// eh feito por este campo
		// Wagner Xavier e Eduardo Riera
		aAdd(aAux,{"N3_CCUSTO", SD1->D1_CC  })
		aAdd(aAux,{"N3_SUBCCON", SD1->D1_ITEMCTA  })
		aAdd(aAux,{"N3_CLVLCON", SD1->D1_CLVL  })

		nVlrMoed	:= Round(xMoeda( nVlRatF,nMoeda,1,SD1->D1_DTDIGIT,aTamVOrig[1][2]+1,SF1->F1_TXMOEDA),aTamVOrig[1][2])
		nVlFicha	:= nVlrMoed/nAtfQtdIt

		If cPaisLoc == "BRA"
			//Acumula valor da diferenca a partir da 3 casa decimal em aDIfDec[1] das parcelas 
			aDIfDec[3]+= (nVlrMoed / nAtfQtdIt) - NoRounD(nVlrMoed / nAtfQtdIt,2)
			//Se aDIfDec[2] == .T. ent„o quer dizer que È o ˙ltimo bem, e neste ser· somado os valores de diferenÁas a partir da 3 casa decimal dos bens anteriores.
			If aDIfDec[2] == .T. 
				nVlFicha := nVlFicha + aDIfDec[3]
			Endif
		Endif

		If aVlrAcAtf[1] + nVlFicha > nVlrMoed
			aAdd(aAux,{"N3_VORIG1", NoRound((nVlrMoed - aVlrAcAtf[1]),aTamVOrig[1][2])})
		Else
			aAdd(aAux,{"N3_VORIG1", NoRound(nVlFicha,aTamVOrig[1][2])})
		EndIf

		aVlrAcAtf[1]	+=	NoRound(nVlFicha,aTamVOrig[1][2])
		//
		nVlrMoed	:=	Round(xMoeda( nVlRatF,nMoeda,2,SD1->D1_DTDIGIT,aTamVOrig[2][2]+1,SF1->F1_TXMOEDA),aTamVOrig[2][2])
		nVlFicha	:= nVlrMoed/nAtfQtdIt
		If aVlrAcAtf[2] + nVlFicha > nVlrMoed
			aAdd(aAux,{"N3_VORIG2", NoRound((nVlrMoed - aVlrAcAtf[1]),aTamVOrig[2][2])})
		Else
			aAdd(aAux,{"N3_VORIG2", NoRound(nVlFicha,aTamVOrig[2][2])})
		EndIf
		aVlrAcAtf[2]	+=	NoRound(nVlFicha,aTamVOrig[2][2])
		//
		nVlrMoed	:=	Round(xMoeda( nVlRatF,nMoeda,3,SD1->D1_DTDIGIT,aTamVOrig[3][2]+1,SF1->F1_TXMOEDA),aTamVOrig[3][2])
		nVlFicha	:= nVlrMoed/nAtfQtdIt
		If aVlrAcAtf[3] + nVlFicha > nVlrMoed
			aAdd(aAux,{"N3_VORIG3", NoRound((nVlrMoed - aVlrAcAtf[3]),aTamVOrig[3][2])})
		Else
			aAdd(aAux,{"N3_VORIG3", NoRound(nVlFicha,aTamVOrig[3][2])})
		EndIf
		aVlrAcAtf[3]	+=	NoRound(nVlFicha,aTamVOrig[3][2])
		//
		nVlrMoed	:=	Round(xMoeda( nVlRatF,nMoeda,4,SD1->D1_DTDIGIT,aTamVOrig[4][2]+1,SF1->F1_TXMOEDA),aTamVOrig[4][2])
		nVlFicha	:= nVlrMoed/nAtfQtdIt
		If aVlrAcAtf[4] + nVlFicha > nVlrMoed
			aAdd(aAux,{"N3_VORIG4", NoRound((nVlrMoed - aVlrAcAtf[4]),aTamVOrig[4][2])})
		Else
			aAdd(aAux,{"N3_VORIG4", NoRound(nVlFicha,aTamVOrig[4][2])})
		EndIf
		aVlrAcAtf[4]	+=	NoRound(nVlFicha,aTamVOrig[4][2])
		//
		nVlrMoed	:=	xMoeda( nVlRatF,nMoeda,5,SD1->D1_DTDIGIT,aTamVOrig[5][2]+1,SF1->F1_TXMOEDA)
		nVlFicha	:= nVlrMoed/nAtfQtdIt
		If aVlrAcAtf[5] + nVlFicha > nVlrMoed
			aAdd(aAux,{"N3_VORIG5",  NoRound((nVlrMoed - aVlrAcAtf[5]),aTamVOrig[5][2])})
		Else
			aAdd(aAux,{"N3_VORIG5", NoRound(nVlFicha,aTamVOrig[5][2])})
		EndIf
		aVlrAcAtf[5]	+=	NoRound(nVlFicha,aTamVOrig[5][2])

		//Incluido por Fernando Radu Muscalu em 28/04/2011
		//Monta o Rateio de Despesas de Depreciacao da Ficha do ativo para o cItem (item corrente do Doc Entrada) passado como
		//conteudo do array aRateio e proveniente de aRatCC, que foi adquirido na tela do documento de
		//entrada.
		aNewRat := A103SetRateioBem( aRateio, SD1->D1_ITEM )

		If lRatAtiv .And. len(aNewRat) > 0
			aAdd(aAux,{"N3_RATEIO", "1"  })
			aAdd(aAux,{"N3_CODRAT", aNewRat[1][1] })
		EndIf

		// Tratamento para levar as entidades contabeis para classificacao de compras no ATF
		For nI := 5 to nQtdEnt
			cLoopEnt  := PADL(cValToChar(nI),2,"0")
			cEntConDB := "EC"+cLoopEnt+"DB"
			cEntConCR := "EC"+cLoopEnt+"CR"
			//Manter o filedpos pois as entidades cont·beis s„o criadas pelo usu·rio.
			If SN3->(FieldPos("N3_"+cEntConDB)) > 0 .And. SN3->(FieldPos("N3_"+cEntConCR)) > 0 .AND. ;
				SD1->(FieldPos("D1_"+cEntConDB)) > 0 .AND. SD1->(FieldPos("D1_"+cEntConCR)) > 0
				aAdd(aAux,{"N3_"+cEntConDB, SD1->&("D1_"+cEntConDB)  })
				aAdd(aAux,{"N3_"+cEntConCR, SD1->&("D1_"+cEntConCR)  })
			EndIf
		Next nI

		aAdd(aItens,aAux)

		aAreaSa2 := SA2->(GetArea())

		//P.E. Utilizado para ManipulaÁ„o do aCols e aItens enviado para a Atfa012
		IF ExistBlock("MA103ATF")
			aPE    := ExecBlock("MA103ATF",.F.,.F.,{aCab,aItens})
			aCab   := aPE[1]
			aItens := aPE[2]
		Endif

		Begin Transaction
		DbSelectArea("SN1")
		Pergunte("AFA012",.F.)
		MSExecAuto({|x,y,z,w| Atfa012(x,y,z,w)},aCab,aItens,3,aParam)

		If lMsErroAuto
			lMsErroAuto := .F.
			DisarmTransaction()
			lRet := .F.
			cFileLog := NomeAutoLog()
			cPath := ""
			lGravou := .F.
			If !Empty(cFileLog) .AND. !lRet .And. !IsBlind()
				MostraErro(cPath,cFileLog)
			Endif
		Else
			lRet := .T.
			lGravou := .T.
			RecLock("SD1",.F.)
			SD1->D1_CBASEAF := cBase+cItem
			MsUnLock()
		EndIf
		End Transaction

		RestArea(aAreaSa2)

	EndIf
	Pergunte("MTA103",.F.)
ElseIf nOpc == 100 .And. lAjustaNCD .And. lStrutNCD
	//IntegraÁ„o de Notas de CrÈdito com Ativo para ajuste no valor do bem
	//Ajusta o valor do bem efetuando uma baixa no valor da nota
	
	//Vari·veis private para a funÁ„o de baixa do ativo Af035Grava/Af030Grava e Af035Parcial.
	Private	dBaixa030  := dDataBase
	Private lSN7       := .F.
	Private cMotivo	   := "14"
	Private lQuant	   := .F.
	Private lPrim	   := .T.
	Private cLoteAtf   := LoteCont("ATF")
	Private nPercBaixa := 100
	Private lAuto      := .T.
	Private lUmaVez	   := .T.
	Private cMoedaAtf  := GetMV("MV_ATFMOED")
	Private aVlrAtual  := AtfMultMoe(,,{|x| 0})
	Private aVlResid   := AtfMultMoe(,,{|x| 0})
	Private aValBaixa  := AtfMultMoe(,,{|x| 0})
	Private aValDepr   := AtfMultMoe(,,{|x| 0})
	Private aDepr 	     := AtfMultMoe(,,{|x| 0})

	//Localiza o documento de entrada original (Nota Fiscal ou Remito).
	//O SD2 deve estar aberto e ter sido posicionado no registro do bem a ajustar.
	dbSelectArea("SD1")
	SD1->( dbSetOrder(1) )	//D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_COD+D1_ITEM
	SD1->( dbSeek( xFilial("SD2") + SD2->D2_NFORI + SD2->D2_SERIORI + SD2->D2_CLIENTE + SD2->D2_LOJA + SD2->D2_COD + SD2->D2_ITEMORI ) )

	//Localiza o ativo gerado atravÈs do documento de entrada.
	dbSelectArea("SN1")
	SN1->( dbSetOrder(8) )	//N1_FILIAL+N1_FORNEC+N1_LOJA+N1_NFESPEC+N1_NFISCAL+N1_NSERIE+N1_NFITEM
	If ( SN1->( dbSeek( xFilial("SD1") + SD1->D1_FORNECE + SD1->D1_LOJA + SD1->D1_ESPECIE + SD1->D1_DOC + SD1->D1_SERIE + SD1->D1_ITEM ) ) )

		dbSelectArea("SN3")
		SN3->( dbSetOrder(1) )	//N3_FILIAL+N3_CBASE+N3_ITEM+N3_TIPO+N3_BAIXA+N3_SEQ

		A103QtItem( "SD1", @nItens )	//Verifica quantos itens foram gerados pelo documento de entrada

		//Atualiza todos os bens gerados pelo item do documento de entrada, independente
		//de cÛdigo base, tratando TES configurada para desmembrar o item ou n„o.
		While SN1->(!Eof()) .And.;
				SN1->N1_FORNEC  == SD1->D1_FORNECE .And.;
				SN1->N1_LOJA    == SD1->D1_LOJA    .And.;
				SN1->N1_NFESPEC == SD1->D1_ESPECIE .And.;
				SN1->N1_NFISCAL == SD1->D1_DOC     .And.;
				SN1->N1_NSERIE  == SD1->D1_SERIE   .And.;
				SN1->N1_NFITEM  == SD1->D1_ITEM

   If !Empty(SN1->N1_FORNEC) .And. !Empty(SN1->N1_LOJA) .And. !Empty(SN1->N1_NFESPEC) .And. !Empty(SN1->N1_NFISCAL) .And. !Empty(SN1->N1_NSERIE) .And. !Empty(SN1->N1_NFITEM)				

			SN3->( dbSeek( xFilial("SN1") + SN1->N1_CBASE + SN1->N1_ITEM ) )

			//Atualiza os valores para cada tipo de depreciaÁ„o criada na classificaÁ„o do bem.
			//Trata apenas os tipos "01" e o tipo "10" se o par‚metro MV_ATFNFIN estiver igual a .T.
			While SN3->(!Eof()) .And.;
					SN3->N3_CBASE + SN3->N3_ITEM == SN1->N1_CBASE + SN1->N1_ITEM

				If SN3->N3_TIPO == "01" .And. SN3->N3_BAIXA == "0"	//Trata se for tipo 01 e se n„o È baixa
					For nI := 1 to nMoedas
						cMoeda := Alltrim(Str(nI))
						aVlrAtual[nI]  := Abs( SN3->&( "N3_VORIG" + cMoeda ) )
						IIf ( aVlrAtual[nI] == 0, aValBaixa[nI] := 0, aValBaixa[nI] := ( SD2->D2_TOTAL / nItens ) )
						aAdd( aVlrTipo01, aVlrAtual[nI] )
					Next nI
				ElseIf SN3->N3_TIPO == "10" .And. lATFNFIN .And. SN3->N3_BAIXA == "0"	//Trata se for tipo 10 e par‚metro MV_ATFNFIN for True
					For nI := 1 to nMoedas
						cMoeda := Alltrim(Str(nI))
						nVlrOrig := Abs( SN3->&( "N3_VORIG" + cMoeda ) )

						If aVlrTipo01[nI] != 0
							aValBaixa[nI] := ( SD2->D2_TOTAL * ( nVlrOrig / aVlrTipo01[nI] ) ) / nItens
						Else
							aValBaixa[nI] := 0
						EndIf

						aVlrAtual[nI] := nVlrOrig
					Next nI
				Else	//Se n„o for tipo 01 ou 10 com MV_ATFNFIN=.T. n„o faz nada
					SN3->(dbSkip())
					Loop
				EndIf

				//Salva ambiente antes de gravar
				aTmpSN1 := SN1->(GetArea())
				aTmpSN3 := SN3->(GetArea())
				aTmpSD1 := SD1->(GetArea())

				//Atualiza valor do ativo
				If AllTrim(cRotBaixa) == "ATFA030"
					Af030Calc( "SN3", SN1->N1_NFISCAL, SN1->N1_NSERIE, .F., 0, SN1->N1_QUANTD , .T., @cIdMov )
				Else
					Af035Grava( "SN3", SN1->N1_NFISCAL, SN1->N1_NSERIE, .F., 0, SN1->N1_QUANTD , .T., @cIdMov ) 
				EndIf

				//Restaura ambiente
				RestArea(aTmpSN1)
				RestArea(aTmpSN3)
				RestArea(aTmpSD1)

				//Grava ID do movimento (SN4) no item da nota
				If SN3->N3_TIPO == "01"
					Reclock("SD2")
					Replace SD2->D2_CBASEAF With cIdMov
					MSUnlock()
				EndIf

				SN3->(dbSkip())
			EndDo	//While SN3
   EndIf			

			SN1->(dbSkip())
		EndDo	//While SN1

		lGravou := .T.

	EndIf //If do Seek no SN1

	//Restaura areas usadas
	RestArea(aAreaSN1)
	RestArea(aAreaSD1)

ElseIf nOpc == 101 .And. lAjustaNCD .And. lStrutNCD
	//IntegraÁ„o de Notas de DÈbito com Ativo para ajuste no valor do bem.
	//Incorpora novo item para cada bem gerado pelo documento de entrada.
	
	//Inicializa aHeader do SN3 para gravaÁ„o do ativo
	DbSelectArea("SX3")
	SX3->(DbSetOrder(1))
	SX3->(MsSeek("SN3"))
	While ( !Eof() .And. SX3->X3_ARQUIVO == "SN3" )
		If ( X3Uso(SX3->X3_USADO) .And. cNivel >= SX3->X3_NIVEL ) .Or. "N3_AMPLIA" $ SX3->X3_CAMPO
			Aadd( aHeader, { Trim(X3TITULO()),;
				SX3->X3_CAMPO,;
				SX3->X3_PICTURE,;
				SX3->X3_TAMANHO,;
				SX3->X3_DECIMAL,;
				SX3->X3_VALID,;
				SX3->X3_USADO,;
				SX3->X3_TIPO,;
				SX3->X3_ARQUIVO,;
				SX3->X3_CONTEXT } )
			nUsado++
		EndIf
		SX3->(dbSkip())
	EndDo

	//Reabre SD1 com outro alias para manipular a nota original
	If !ChkFile( "SD1", .F., "SD1ORI" )
		lRet := .F.
		Help( " ", 1, "A103GrvAtf", , STR0375, 1, 0 )	//"Erro ao criar ·rea de trabalho tempor·ria.
	EndIf

	//Localiza o documento de entrada original (Nota Fiscal ou Remito).
	//O SD1 deve estar aberto e ter sido posicionado no registro do bem a incorporar,
	//antes da chamada da funÁ„o.
	If lRet

		//Verifica se rateio foi digitado manualmente, se n„o usa lMontaRat
		//para forÁar verificaÁ„o de rateio do bem origianl
		If aScan( aRateio, { |x| AllTrim(x[1]) == Alltrim(SD1->D1_ITEM) } )	<= 0
			lMontaRat := .T.
		EndIf

		dbSelectArea("SD1ORI")
		SD1ORI->( dbSetOrder(1) )	//D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_COD+D1_ITEM
		If ( SD1ORI->( dbSeek( xFilial("SD1") + SD1->D1_NFORI + SD1->D1_SERIORI + SD1->D1_FORNECE + SD1->D1_LOJA + SD1->D1_COD + SD1->D1_ITEMORI ) ) )

			//Localiza o ativo gerado atravÈs do documento de entrada.
			dbSelectArea("SN1")
			SN1->( dbSetOrder(8) )	//N1_FILIAL+N1_FORNEC+N1_LOJA+N1_NFESPEC+N1_NFISCAL+N1_NSERIE+N1_NFITEM
			If ( SN1->( dbSeek( xFilial("SD1") + SD1ORI->D1_FORNECE + SD1ORI->D1_LOJA + SD1ORI->D1_ESPECIE +;
					SD1ORI->D1_DOC + SD1ORI->D1_SERIE + SD1ORI->D1_ITEM ) ) )

				dbSelectArea("SN3")
				SN3->( dbSetOrder(1) )	//N3_FILIAL+N3_CBASE+N3_ITEM+N3_TIPO+N3_BAIXA+N3_SEQ

				//Atualiza todos os bens gerados pelo item do documento de entrada, independente
				//de cÛdigo base, tratando TES configurada para desmembrar o item ou n„o.
				While SN1->(!Eof()) .And.;
						SN1->N1_FORNEC  == SD1ORI->D1_FORNECE .And.;
						SN1->N1_LOJA    == SD1ORI->D1_LOJA    .And.;
						SN1->N1_NFESPEC == SD1ORI->D1_ESPECIE .And.;
						SN1->N1_NFISCAL == SD1ORI->D1_DOC     .And.;
						SN1->N1_NSERIE  == SD1ORI->D1_SERIE   .And.;
						SN1->N1_NFITEM  == SD1ORI->D1_ITEM

					//Verifica se È o mesmo cÛdigo base do loop anterior,
					//se for, n„o cria um novo item
					If cUltCBase == SN1->N1_CBASE
						cUltCBase := SN1->N1_CBASE
						SN1->(dbSkip())
						Loop
					EndIf

					A103QtItem( "SD1ORI", @nItens, .T. )

					If ( SN3->( dbSeek( xFilial("SN1") + SN1->N1_CBASE + SN1->N1_ITEM ) ) )

						//Preenchimento das Vari·veis referentes ao SN1
						For nI := 1 To SN1->(FCount())
							M->&(SN1->(Field(nI))) := SN1->(FieldGet(nI))
						Next nI

						cUltItem :=  ATFXProxIt(cFilAnt,SN1->N1_CBASE)

						aAdd(aCab,{"N1_ITEM"   , cUltItem})
						aAdd(aCab,{"N1_AQUISIC",SD1->D1_DTDIGIT})
						aAdd(aCab,{"N1_QUANTD", 1})
						aAdd(aCab,{"N1_FORNEC",SD1->D1_FORNECE})
						aAdd(aCab,{"N1_LOJA", SD1->D1_LOJA})
						aAdd(aCab,{"N1_NSERIE",SD1->D1_SERIE})
						aAdd(aCab,{"N1_NFISCAL",SD1->D1_DOC})
						aAdd(aCab,{"N1_CHASSI",SD1->D1_CHASSI})
						aAdd(aCab,{"N1_PLACA",SD1->D1_PLACA})
						aAdd(aCab,{"N1_STATUS", "1"})
						aAdd(aCab,{"N1_NFESPEC",SD1->D1_ESPECIE})
						aAdd(aCab,{"N1_NFITEM" ,SD1->D1_ITEM})
						aAdd(aCab,{"N1_PRODUTO",SD1->D1_COD})
						nJ    := 1
						IIf ( lMontaRat, aNewRat := {}, aNewRat )

						//Varre todos os tipos do ativo para verificar se foram depreciados
						While SN3->(!Eof()) .And.;
								SN3->N3_CBASE + SN3->N3_ITEM == SN1->N1_CBASE + SN1->N1_ITEM

							If SN3->N3_BAIXA == "0"
								//Monta aCols para gravaÁ„o do item
								For nI := 1 to nUsado
									If AllTrim(aHeader[nI][2]) == "N3_VORIG1"
										aAdd(aAux, {"N3_VORIG1" , SD1->D1_TOTAL / nItens })
									ElseIf "N3_VRDACM" $ AllTrim(aHeader[nI][2])
										aAdd(aAux, {"N3_VRDACM" , 0 })
									Else
										aAdd(aAux, {aHeader[nI][2] , &("SN3->" + AllTrim( aHeader[nI][2] ))})
									EndIf
								Next nI

								//Se item n„o possui dados de rateio preenchidos manualmente
								//verifica se item original possui para copiar rateio do bem original
								If lMontaRat
									If SN3->N3_RATEIO == "1" .And. !Empty(SN3->N3_CODRAT)
										AF012LoadR( aNewRat, SN3->N3_CODRAT, nJ )
										aNewRat[nJ,1] := ""
										aNewRat[nJ,2] := ""
									EndIf
								EndIf

								aAdd(aItens, aAux)
								aSize(aAux, 0)
								aAux := Nil
								nJ += 1
							EndIf

							SN3->(dbSkip())
						EndDo

						//Atualiza dados da depreciaÁ„o
						If !lATFVdProp
							A103CalcTx()
						EndIf

						//Formata array de rateio caso tenha sido informado pelo
						//usu·rio manualmente para o item da nota
						If !lMontaRat
							aNewRat := A103SetRateioBem( aRateio, SD1->D1_ITEM )
							aNewRat[1,3] := "3"
						EndIf

						DbSelectArea("SN1")
						Pergunte("AFA012", .F.)
						MSExecAuto({|x,y,z,w| ATFA012(x,y,z,w)},aCab,aItens,3,aParam)
					EndIf	//If do seek no SN3
					cUltCBase := SN1->N1_CBASE
					SN1->(dbSkip())
				EndDo	//While SN1
			EndIf //If do seek no SN1
		Else
			lGravou := .T.
		EndIf	//If do seek no SD1ORI

		//Fecha area tempor·ria
		dbSelectArea("SD1ORI")
		dbCloseArea()

	EndIf	//lRet

	//Restaura areas usadas
	RestArea(aAreaSN1)
	RestArea(aAreaSD1)

ElseIf nOpc == 102 .And.  lAjustaNCD .And. lStrutNCD
	//Deleta os ajustes gerados pela nota de dÈbito.
	If ( !Empty(cChave) )
		dbSelectArea("SN1")
		SN1->(dbSetOrder(8))	//N1_FILIAL+N1_FORNEC+N1_LOJA+N1_NFESPEC+N1_NFISCAL+N1_NSERIE+N1_NFITEM

		If ( SN1->( dbSeek( cChave ) ) )

			While SN1->(!Eof()) .And.;
					cChave == SN1->N1_FILIAL + SN1->N1_FORNEC + SN1->N1_LOJA + SN1->N1_NFESPEC + SN1->N1_NFISCAL + SN1->N1_NSERIE

				Af010DelAtu( "SN3", , , , @aCIAP )
				SN1->(dbSkip())
			EndDo
		EndIf
	EndIf

	RestArea(aAreaSN1)
	
	Elseif nOpc == 104 //Realiza atualizaÁ„o de valor dos bens (Exemplo: Conhecimento de frete agrega valor ao bem)

	nVlrAdc   := Eval( bValAtf )
	nVlrAdc   := IIf(ValType(nVlrAdc) <> "N",(SD1->D1_TOTAL-SD1->D1_VALDESC)+IIf(SF4->F4_CREDIPI=="S",0,SD1->D1_VALIPI)-IIf(SF4->F4_CREDICM=="S",SD1->D1_VALICM,0)-IIf(cDaCiap=="S",SD1->D1_ICMSCOM,0),nVlrAdc)
	nVlrIcm   := SD1->D1_VALICM + IIf(cDaCiap == "S",SD1->D1_ICMSCOM,0)
	cCodProd  := AllTrim(SD1->D1_COD)
	cItemPrd  := AllTrim(SD1->D1_ITEMORI)
	aAreaSF1  := SF1->(GetArea())
	aAreaSD1  := SD1->(GetArea())

	if empty(aRecSF1Ori) .and. FwIsInCallStack("MATA103")
		SF1->(DbSetOrder(1))
		if empty(cBaseDigit) .and. SF1->(MsSeek(cChaveSD1))
			aAdd(aRecSF1Ori,SF1->(Recno()))
		endif

		if !empty(cBaseDigit)
			aAdd(aRecSF1Ori,SF1->(Recno())) //Guardo o recno da propria NF, pois n„o existe origem.

			//Cliente pode enviar somente a base do ativo para atualizar todos os itens.
			//Ou pode enviar a base + item para atualizar valor de um item especÌfico.
			if len(Alltrim(cBaseDigit)) < ( len(SN1->N1_CBASE) + len(SN1->N1_ITEM) )
				cItBsSD1 := getItATF(cBaseDigit)//busca qtd de itens do ativo.
			endif 

			if !empty(cItBsSD1)
				if Reclock("SD1",.F.)
					SD1->D1_CBASEAF := Alltrim(SD1->D1_CBASEAF) + cItBsSD1
					SD1->(MsUnlock())
				endif
			endif
		endif
	endif

	for nX := 1 to len(aRecSF1Ori)

		//cBaseDigit em preenchida = NF de garantia estendida, j· est· posicionado na SF1 correta.
		//cBaseDigit em branco = Inclus„o de CTE, requer posicionamento na SF1 de origem.
		if empty(cBaseDigit)
			SF1->(DbGoTo(aRecSF1Ori[nX]))
			cChaveSD1 := SF1->(F1_FILIAL + F1_DOC + F1_SERIE + F1_FORNECE + F1_LOJA)
		endif

		if FwIsInCallStack("MATA116") .and. type("lAglutProd") == "L" .and. lAglutProd 
			nQtdAglut := getProdIguais(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,cCodProd)
			nVlrAdc := Round(nVlrAdc/nQtdAglut,2)
		endif
		
		SD1->(DbSetOrder(1))//D1_FILIAL, D1_DOC, D1_SERIE, D1_FORNECE, D1_LOJA, D1_COD, D1_ITEM
		if SD1->(MsSeek(cChaveSD1))
			while SD1->(!eof()) .and. SF1->(F1_FILIAL + F1_DOC + F1_SERIE + F1_FORNECE + F1_LOJA) == SD1->(D1_FILIAL + D1_DOC + D1_SERIE + D1_FORNECE + D1_LOJA)
				if !empty(cItemPrd) //Se possuir o D1_ITEMORI, utiliza para posicionar no item correto(D1_ITEMORI È preenchido no MATA116 AglutProd = N„o e Comp Frete via MATA103).
					if cItemPrd + Alltrim(cCodProd) <> SD1->D1_ITEM + Alltrim(SD1->D1_COD)
						SD1->(DbSkip())
						Loop
					endif
				endif
				if !empty(SD1->D1_CBASEAF) .And. cCodProd == AllTrim(SD1->D1_COD)
					aAtuBens := {}
					aAuxAtu  := {}
					aAuxICM  := {}
					cBaseSD1 := left(SD1->D1_CBASEAF,len(SN1->N1_CBASE))
					cItBsSD1 := right(SD1->D1_CBASEAF,len(SN1->N1_ITEM))
					if !empty(cBaseSD1) .and. !empty(cItBsSD1) .and. val(cItBsSD1) > 0

						for nJ := 1 to val(cItBsSD1)
							//Valor do Item							
							nVlrRat := nVlrAdc / val(cItBsSD1)
							aAdd(aAuxAtu, nVlrRat)

							//Valor de ICMS do item
							nVlrRat := nVlrIcm / val(cItBsSD1)
							aAdd(aAuxICM, nVlrRat)
						next nJ

						aAtuBens := { 	cBaseSD1,;
										cItBsSD1,;
										aAuxAtu,;
										aAuxICM;
									}
						
						if !Inclui .and. !Altera 
							cOpc := "2" //Estorna valores
						else 
							cOpc := "1" //Agrega valores
						endif
						aRetAtf := CompCTE(aAtuBens,cOpc)//(FunÁ„o do ativo) -- Envia os dados para o ativo fixo atualizar os bens.
						if !empty(aRetAtf) .and. len(aRetAtf) == 2
							if valtype(aRetAtf[1]) == "L" .and. aRetAtf[1]
								lGravou := .T.
							endif
						endif
					endif
				endif
				SD1->(DbSkip())
			enddo
		endif
	next nX

	RestArea(aAreaSF1)
	RestArea(aAreaSD1)

ElseIf nOpc == 103 .And.  lAjustaNCD .And. lStrutNCD
	//Deleta os ajustes gerados pela nota de crÈdito.
	Private cMoedaAtf := GetMV("MV_ATFMOED")
	Private cMoeda := ""
	Private lPrimlPad := .T.
	Private nTotal    := 0
	Private nHdlPrv   := 0
	Private LUSAMNTAT := .F.
	Private lAuto	  := .T. 

	dbSelectArea("SN3")
	SN3->(dbSetOrder(1))	//N3_FILIAL+N3_CBASE+N3_ITEM+N3_TIPO+N3_BAIXA+N3_SEQ
	dbSelectArea("SN4")
	SN4->(dbSetOrder(6))	//N4_FILIAL+N4_IDMOV+N4_OCORR

	If ( SN4->(dbSeek( xFilial("SF2") + cChave ) ) )	//cChave = ID do SN4 gravado no SD2 durante gravaÁ„o do ajuste

		//Procura todas as baixas realizadas pela nota
		While lRet .And. SN4->N4_IDMOV == cChave

			If ( SN3->(dbSeek( xFilial("SN4") + SN4->N4_CBASE + SN4->N4_ITEM + "01" + "1" + SN4->N4_SEQ ) ) .Or.;
					SN3->(dbSeek( xFilial("SN4") + SN4->N4_CBASE + SN4->N4_ITEM + "10" + "1" + SN4->N4_SEQ ) ) )

				aTmpSN4 := SN4->(GetArea())

		     	cQryFN7 := " SELECT " + CRLF
			cQryFN7 += " FN7.FN7_FILIAL, " + CRLF
			cQryFN7 += " FN7.FN7_CODBX " + CRLF
			cQryFN7 += " FROM " + RetSqlName("FN7") + " FN7 " + CRLF
			cQryFN7 += " WHERE " + CRLF
			cQryFN7 += RetSqlCond("FN7") + CRLF
			cQryFN7 += " AND FN7.FN7_STATUS = '1' "  + CRLF
			cQryFN7 += " AND FN7.FN7_FILORI = '" + FwCodFil() + "' " + CRLF
			cQryFN7 += " AND FN7.FN7_CBASE = '" + SN3->N3_CBASE + "' " + CRLF
			cQryFN7 += " AND FN7.FN7_CITEM = '" +SN3->N3_ITEM + "' " + CRLF
			cQryFN7 += " AND FN7.FN7_TIPO = '" + SN3->N3_TIPO + "' " + CRLF
			cQryFN7 += " AND FN7.FN7_TPSALD = '" + SN3->N3_TPSALDO + "' " + CRLF
			cQryFN7 += " AND FN7.FN7_MOEDA = '01' " + CRLF
			cQryFN7 += " AND FN7.FN7_SEQREA = '" + SN3->N3_SEQREAV + "' " + CRLF
			cQryFN7 += " AND FN7.FN7_SEQ = '" + SN3->N3_SEQ + "' " + CRLF
			cQryFN7 += " AND FN7.FN7_DTBAIX = '" + DTOS(SN3->N3_DTBAIXA) + "' " + CRLF

			If Select("TFN7") > 0
				dbSelectArea("TFN7")
				DbCloseArea()
			EndIf

			//* Cria a Query e da Um Apelido
			dbUseArea(.T.,"TOPCONN",TCGENQRY(,,cQryFN7),"TFN7",.F.,.T.)

			dbSelectArea("TFN7")
			dbGotop()
			Do While TFN7->(!Eof())
				xCab :={ 	{"FN6_FILIAL", TFN7->FN7_FILIAL		,NIL},;
						{"FN6_CODBX"	,TFN7->FN7_CODBX	,NIL} }

				MsExecAuto({|a,b,c|ATFA036(a,b,c)},xCab,,5)
				If lMsErroAuto
					MostraErro()
					lRet:=  .F.
				Endif
				Exit
			EndDo

				RestArea(aTmpSN4)

			EndIf
			SN4->(dbSkip())
		EndDo
	EndIf

	lGravou := lRet

	RestArea(aAreaSN3)
	RestArea(aAreaSN4)

Else
	//Deleta a integracao com o ativo Fixo.
	If ( !Empty(cBase) )
		DbSelectArea("SN1")
		DbSetOrder(1)
		cBase := Alltrim(cBase)
		cBase := PADR(Left(cBase,len(cBase)-len(SN1->N1_ITEM)),len(SN1->N1_CBASE))+Right(cBase,len(SN1->N1_ITEM))
		If ( MsSeek(xFilial("SN1")+cBase))
			//Incluido por Fernando Radu Muscalu em 28/04/2011
			//Monta o Rateio de Despesas de Depreciacao da Ficha do ativo para todos os itens (do Doc. entrada) passado
			//como conteudo do array aRateio que e proveniente de aRatCC, que foi adquirido na tela do documento de
			//entrada.
			aNewRat	:= A103SetRateioBem(aRateio)
			Af010DelAtu("SN3",,,,@aCIAP,aNewRat)
		EndIf
	EndIf
EndIf

//ProteÁ„o para quando o a103grava for chamado por outro fonte.
If Type("l103Class") <> "L"
	l103Class := .F.
Endif
If Type("l103Auto") <> "L"
	l103Auto := .F.
Endif

//Metricas documento de entrada com integraÁ„o com ativo fixo
If lGravou
	nQtdAtf++
	ComMtQtd("-inc",l103Auto,l103Class,cTipo,nQtdAtf,cFunAtf)
	nQtdAtf := 0
EndIf

RestArea(aAreaSB1)
RestArea(aArea)

Return(lGravou)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa   ≥ A103CalcTx ∫Autor  ≥ Danilo Dias      ∫ Data ≥ 17/06/2011  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫DescriÁ„o  ≥ Recalcula a taxa de depreciaÁ„o de acordo com o tempo de   ∫±±
±±∫           ≥ depreciaÁ„o restante do bem original, para bens ajustados  ∫±±
±±∫           ≥ atravÈs de incorporaÁ„o por nota de dÈbito, fazendo com    ∫±±
±±∫           ≥ que o bem incorporado termine de depreciar junto com o     ∫±±
±±∫           ≥ bem original.                                              ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Par‚metros ≥ 												           ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±∫Uso        ≥ A103GRVATF                                                 ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103CalcTx()

Local dUltDepr   := GetMV("MV_ULTDEPR")	//Data do ˙ltimo c·lculo de depreciaÁ„o
Local nPTxDepr   := 0
Local nPDtInDep  := 0
Local nPCritDep  := 0
Local cCritDepr  := ""	//CritÈrio de depreciaÁ„o do bem
Local nTxDepr    := 0	//Taxa de depreciaÁ„o do bem
Local dInicDepr  := StoD("//")	//Data inical de depreciaÁ„o do bem
Local nTempoTot  := 0	//Vida ˙til do bem em meses
Local nTempoRest := 0	//Vida ˙til restante do bem em meses
Local nTempoDepr := 0	//Tempo j· depreciado do bem em meses
Local nI         := 0
Local nMoedas    := AtfMoedas()
Local nY		 := 0

For nI:= 1 To Len(aCols)

	//Carrega dados do bem original
	For nY := 1 to nMoedas
		nPTxDepr  := aScan( aHeader, { |x| AllTrim(x[2]) == IIf( nMoedas > 9,'N3_TXDEP','N3_TXDEPR') + cValToChar(nY) } )
		nTxDepr   := aCols[nI,nPTxDepr]		//Taxa de depreciaÁ„o do bem original
		nPDtInDep := aScan( aHeader, { |x| Alltrim(x[2]) == "N3_DINDEPR" } )
		dInicDepr := aCols[nI,nPDtInDep]	//Data inicial de depreciaÁ„o do bem original
	 		nPCritDep := aScan( aHeader, { |x| AllTrim(x[2]) == "N3_CRIDEPR" } )
	 		cCritDepr := AllTrim(aCols[nI,nPCritDep])	//CritÈrio de depreciaÁ„o do bem original

		nTempoTot  := ( 100 / nTxDepr ) * 12   		//Tempo total de depreciaÁ„o do bem em meses
		nTempoDepr := ( dUltDepr - dInicDepr ) / 30 //Tempo total j· depreciado em meses

		IIf( nTempoDepr < 0, nTempoDepr := 0, nTempoDepr := nTempoDepr )

		nTempoRest := nTempoTot - ( Round( nTempoDepr,0 ) )	//Tempo restante a depreciar do bem em meses

		//Nova taxa de depreciaÁ„o para a incorporaÁ„o
		If nTempoRest > 0
			nTxDepr := ( 100 / nTempoRest ) * 12
			aCols[nI,nPTxDepr] := nTxDepr
		EndIf
    Next nY
	//Se for calend·rio completo, calcula ac˙mulo da depreciaÁ„o
	If cCritDepr = "03"
		AF012VLAEC( nI )
	EndIf

Next nI

Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa   ≥ A103ExAjNC ∫Autor  ≥ Danilo Dias      ∫ Data ≥ 09/06/2011  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫DescriÁ„o  ≥ Exclui o ajuste realizado por notas de crÈdito ou dÈbito,  ∫±±
±±∫           ≥ validando se o ajuste j· foi depreciado, n„o permitindo a  ∫±±
±±∫           ≥ exclus„o se sim.                                           ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Par‚metros ≥ cAlias  = Alias do cabeÁalho da nota. (SF1 ou SF2)         ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±∫Uso        ≥ LOCXNF (LocxDelNF)                                         ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103ExAjNC( cAlias )

Local aArea      := GetArea()			//Salva alias atual
Local aAreaSN1   := SN1->(GetArea())	//Salva alias SN1
Local aAreaSN3   := SN3->(GetArea())	//Salva alias SN3
Local aAreaSD2   := SD2->(GetArea())	//Salva alias SD2
Local lRet       := .T.	//Retorno
Local nI         := 0	//Uso Geral
Local cNota      := ""	//N˙mero da NF
Local cSerie     := "" 	//SÈrie da NF
Local cEspecie   := ""	//EspÈcie da NF
Local cLoja      := ""	//Loja da NF
Local cFornece   := ""	//Fornecedor da NF
Local nRecno     := 0   //Guarda recno para reposicionar ponteiro
Local cChave     := ""  //Dados a serem passado para a A103GRVATF para exclus„o
Local aChave     := {}  //Para m˙ltiplas chaves
Local dDtUltDepr := GetMV("MV_ULTDEPR")	//Data da ˙ltima depreciaÁ„o

If cAlias == "SF1"	//Nota de dÈbito

	//Pega dados da nota
	cNota    := SF1->F1_DOC
	cSerie   := SF1->F1_SERIE
	cEspecie := SF1->F1_ESPECIE
	cLoja    := SF1->F1_LOJA
	cFornece := SF1->F1_FORNECE
	cChave   := xFilial("SF1") + cFornece + cLoja + cEspecie + cNota + cSerie

	dbSelectArea("SN1")
	SN1->(dbSetOrder(8))	//N1_FILIAL+N1_FORNEC+N1_LOJA+N1_NFESPEC+N1_NFISCAL+N1_NSERIE+N1_NFITEM
	dbSelectArea("SN3")
	SN3->(dbSetOrder(1))	//N3_FILIAL+N3_CBASE+N3_ITEM+N3_TIPO+N3_BAIXA+N3_SEQ

	If ( SN1->(dbSeek( cChave ) ) )

	    nRecno := SN1->(recno())

		//Varre todos os bens gerados pela nota
		While SN1->(!Eof()) .And.;
			  cChave == SN1->N1_FILIAL + SN1->N1_FORNEC + SN1->N1_LOJA + SN1->N1_NFESPEC + SN1->N1_NFISCAL + SN1->N1_NSERIE

		  	If ( SN3->(dbSeek( xFilial("SN1") + SN1->N1_CBASE + SN1->N1_ITEM ) ) )

			    //Varre todos os tipos do ativo para verificar se foram depreciados
				While SN3->(!Eof()) .And.;
			      	  SN3->N3_CBASE + SN3->N3_ITEM == SN1->N1_CBASE + SN1->N1_ITEM

					//Se houve depreciaÁ„o, termina e retorna Falso
					If dDtUltDepr > SN3->N3_AQUISIC
						lRet := .F.
						Help( " ", 1, "A103GrvAtf", , STR0377, 1, 0 )	//"N„o È possÌvel excluir essa nota. Os ajustes do ativo fixo causados por ela j· foram depreciados."
						Return lRet
					EndIf
					SN3->(dbSkip())
				EndDo
			EndIf	//End If SN3
			SN1->(dbSkip())
		EndDo

		//Exclui os bens gerados pela nota de dÈbito para fazer o ajuste no ativo fixo.
		A103GrvAtf( 102, , , , , , , , cChave )

	EndIf	//End if SN1

ElseIf cAlias == "SF2"	//Nota de crÈdito

	//Se bem foi depreciado apÛs baixa efetuada pela nota de crÈdito n„o permite exclus„o
	If dDtUltDepr > SF2->F2_EMISSAO
		lRet := .F.
		Help( " ", 1, "A103GrvAtf", , STR0377, 1, 0 )	//"N„o È possÌvel excluir essa nota. Os ajustes do ativo fixo causados por ela j· foram depreciados."
		Return lRet
	EndIf

	dbSelectArea("SD2")
	SD2->(dbSetOrder(3))	//D2_FILIAL+D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA+D2_COD+D2_ITEM

	cChave := xFilial("SF2") + SF2->F2_DOC + SF2->F2_SERIE + SF2->F2_CLIENTE + SF2->F2_LOJA

	//Varre todos os itens da Nota e exclui os ajustes
	If ( SD2->( dbSeek( cChave ) ) )
		While SD2->(!Eof()) .And.;
		      cChave == xFilial("SF2") + SD2->D2_DOC + SD2->D2_SERIE + SD2->D2_CLIENTE + SD2->D2_LOJA

			aAdd( aChave, AllTrim(SD2->D2_CBASEAF) )
			SD2->(dbSkip())
		EndDo

		//Exclui os bens gerados pela nota de dÈbito para fazer o ajuste no ativo fixo.
		For nI := 1 To Len(aChave)
			lRet := A103GrvAtf( 103,,,,,,,, aChave[nI] )
		Next nI
	EndIf
EndIf

RestArea(aAreaSN1)	//Restaura alias SN1
RestArea(aAreaSN3)	//Restaura alias SN3
RestArea(aAreaSD2)	//Restaura alias SD2
RestArea(aArea)		//Restaura ˙ltimo alias ativo

Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa   ≥ A103VlNCD ∫Autor  ≥ Danilo Dias       ∫ Data ≥ 09/06/2011  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫DescriÁ„o  ≥ Valida se o item foi classificado, permitindo a integraÁ„o ∫±±
±±∫           ≥ do ativo fixo com o compras, para notas de CrÈdito ou de   ∫±±
±±∫           ≥ dÈbito e se o usu·rio informou dados da NF original, caso  ∫±±
±±∫           ≥ a TES esteja configurada para atualizar ativo.             ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Par‚metros ≥ cAlias  = Alias da nota fiscal de crÈdito/dÈbito (SD1/SD2) ∫±±
±±∫           ≥ aHeader = CabeÁalho da nota.                               ∫±±
±±∫           ≥ aCols   = Itens da nota.                                   ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±∫Uso        ≥ SIGACOM                                                    ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103VlNCD( cAlias, aHeader, aCols )

Local aArea     := GetArea()
Local aAreaSD1  := SD1->(GetArea())
Local aAreaSN1  := SN1->(GetArea())
Local aAreaSF4  := SF4->(GetArea())
Local nPosTES   := aScan( aHeader, { |x| AllTrim(x) == "D1_TES"})
Local nPosNFOri := aScan( aHeader, { |x| AllTrim(x) == "D1_NFORI"})
Local nPosSeOri := aScan( aHeader, { |x| AllTrim(x) == "D1_SERIORI"})
Local nPosItOri := aScan( aHeader, { |x| AllTrim(x) == "D1_ITEMORI"})
Local lRet      := .T.
Local nItem     := 0
Local nPos      := 0

//Dados da nota
Local cFornece  := ""
Local cLoja	    := ""
Local cNF	    := ""
Local cSerie    := ""
Local cItem	    := ""
Local cProd	    := ""

Default cAlias  := ""
Default aHeader := {}
Default aCols   := {}

//Valida par‚metros recebidos
If ValType(aCols) == "A" .And. ValType(aHeader) == "A" .And. ( cAlias == "SD1" .Or. cAlias == "SD2" )

	//Valida os itens no aCols
	For nItem := 1 To Len(aCols)

	    //Valida se dados do documento de entrada original foram informados, caso o TES gere ativo.
	    If lRet .And. cAlias == "SD1"
			If nPosTES > 0
				dbSelectArea("SF4")
				SF4->(dbSetOrder(1))	//F4_FILIAL+F4_CODIGO
				If SF4->(dbSeek( xFilial("SD1") + aCols[nItem,nPosTES] ) )
					If SF4->F4_ATUATF == "S"
						If AllTrim(aCols[nItem,nPosNFOri]) == "" .Or.;
						   AllTrim(aCols[nItem,nPosSeOri]) == "" .Or.;
						   AllTrim(aCols[nItem,nPosItOri]) == ""
							lRet := .F.
							Help( " ", 1, "A103VLNCDA" )	//"Digite os dados do documento de entrada ou informe um TES que n„o gere Ativo Fixo!"
						EndIf
					EndIf
				EndIf
			EndIf
	    EndIf

	    //Valida se os itens gerados pelo documento original foram classificados
		If lRet
		    //Pega dados do documento de entrada original
			nPos   := aScan( aHeader, { |nPos| AllTrim(nPos) == AllTrim( PrefixoCpo( cAlias ) ) + "_NFORI" } )
			cNF    := aCols[nItem][nPos]
			nPos   := aScan( aHeader, { |nPos| AllTrim(nPos) == AllTrim( PrefixoCpo( cAlias ) ) + "_SERIORI" } )
			cSerie := aCols[nItem][nPos]
			nPos   := aScan( aHeader, { |nPos| AllTrim(nPos) == AllTrim( PrefixoCpo( cAlias ) ) + "_ITEMORI" } )
			cItem  := aCols[nItem][nPos]
			nPos   := aScan( aHeader, { |nPos| AllTrim(nPos) == AllTrim( PrefixoCpo( cAlias ) ) + "_COD" } )
			cProd  := aCols[nItem][nPos]
			nPos   := aScan( aHeader, { |nPos| AllTrim(nPos) == AllTrim( PrefixoCpo( cAlias ) ) + "_LOJA" } )
			cLoja  := aCols[nItem][nPos]

			If cAlias == "SD1"
				nPos     := aScan( aHeader, { |nPos| AllTrim(nPos) == AllTrim( PrefixoCpo( cAlias ) ) + "_FORNECE" } )
				cFornece := aCols[nItem][nPos]
			Else
				nPos     := aScan( aHeader, { |nPos| AllTrim(nPos) == AllTrim( PrefixoCpo( cAlias ) ) + "_CLIENTE" } )
			 	cFornece := aCols[nItem][nPos]
			EndIf

			//Encontra documento de entrada original
			dbSelectArea("SD1")
			SD1->( dbSetOrder(1) )	//D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_COD+D1_ITEM
		   	If ( SD1->( dbSeek( xFilial(cAlias) + cNF + cSerie + cFornece + cLoja + cProd + cItem ) ) )

				//Localiza o ativo gerado atravÈs do documento de entrada.
				dbSelectArea("SN1")
				SN1->( dbSetOrder(8) )	//N1_FILIAL+N1_FORNEC+N1_LOJA+N1_NFESPEC+N1_NFISCAL+N1_NSERIE+N1_NFITEM
				If ( SN1->( dbSeek( xFilial("SD1") + SD1->D1_FORNECE + SD1->D1_LOJA + SD1->D1_ESPECIE +;
				                    SD1->D1_DOC + SD1->D1_SERIE + SD1->D1_ITEM ) ) )

					//Valida os ativos gerados pelo documento de entrada
					While SN1->(!Eof()) .And. lRet .And.;
						  SN1->N1_FORNEC  == SD1->D1_FORNECE .And.;
						  SN1->N1_LOJA    == SD1->D1_LOJA    .And.;
						  SN1->N1_NFESPEC == SD1->D1_ESPECIE .And.;
						  SN1->N1_NFISCAL == SD1->D1_DOC     .And.;
						  SN1->N1_NSERIE  == SD1->D1_SERIE   .And.;
						  SN1->N1_NFITEM  == SD1->D1_ITEM

						//Se item n„o classificado termina validaÁ„o
						If SN1->N1_STATUS == "0"
							lRet := .F.
							Help( " ", 1, "A103VLNCDB" )	//"Existem bens n„o classificados no ativo para o documento de entrada original informado."
						EndIf
						If !lRet
							Loop
						EndIf

						SN1->(dbSkip())
					EndDo	//While SN1
				EndIf	//Seek SN1
		   	EndIf	//Seek SD1
		EndIf	//lRet
	Next nItem

EndIf

//Restaura ambiente
RestArea(aAreaSD1)
RestArea(aAreaSN1)
RestArea(aAreaSF4)
RestArea(aArea)

Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥A103QtItem ∫Autor  ≥ Danilo Dias        ∫ Data ≥ 08/06/2011 ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥ Conta quantos bens do ativo foram gerados pelo documento   ∫±±
±±∫          ≥ de entrada original da nota de crÈdito/dÈbito e qual È o   ∫±±
±±∫          ≥ ˙ltimo item cadastrado para cada bem.                      ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Parametros ≥ cAlias = Alias usado para o SD1 na rotina chamadora.      ∫±±
±±∫           ≥ nItens = Passado por ref., quantidade de itens gerados    ∫±±
±±∫           ≥          pela nota.                                       ∫±±
±±∫           ≥ cUltItem = Passado por ref., ˙ltimo item gerado para o    ∫±±
±±∫           ≥            cÛdigo base.                                   ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±∫Uso       ≥ A103GRVATF                                                 ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103QtItem( cAlias, nQtdItens, lCBase )

Local aArea     := GetArea()
Local cQuery    := ""
Local cCBase    := ""
Local cAliasQry := ""

Default nQtdItens := 0
Default lCBase    := .F.

cCBase := SN1->N1_CBASE

//Verifica tipo de conex„o com banco.
cQuery := "Select COUNT(*) QTDITENS From "
If lCBase
	cQuery += "( Select N1_CBASE From "
EndIf
cQuery += RetSqlName("SN1")
cQuery += " Where N1_FILIAL  = '" + xFilial("SD1") + "'"
cQuery += " And N1_FORNEC = '"    + (cAlias)->D1_FORNECE + "'"
cQuery += " And N1_LOJA = '"      + (cAlias)->D1_LOJA + "'"
cQuery += " And N1_NFISCAL = '"   + (cAlias)->D1_DOC + "'"
cQuery += " And N1_NSERIE = '"    + (cAlias)->D1_SERIE + "'"
cQuery += " And N1_NFESPEC = '"   + (cAlias)->D1_ESPECIE + "'"
cQuery += " And N1_NFITEM = '"    + (cAlias)->D1_ITEM + "'"
cQuery += " And D_E_L_E_T_ = ' '"
If lCBase
	cQuery += " Group By N1_CBASE ) A"
EndIf

cQuery	  := ChangeQuery(cQuery)
cAliasQry := GetNextAlias()
dbUseArea( .T., "TOPCONN", TcGenQry( , , cQuery ), cAliasQry, .T., .T. )
DbSelectArea(cAliasQry)
(cAliasQry)->(dbGoTop())
nQtdItens := (cAliasQry)->qtdItens	//Quantidade de bens gerados pela nota.
dbCloseArea()


RestArea(aArea)

Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103GrvPV ≥ Autor ≥ Edson Maricate        ≥ Data ≥ 19.01.98 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Programa de Gravacao dos Pedidos de Venda                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103GrvPV()                                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function a103GrvPV(nOpc,aPedPV,aRecSC5)

Local aArea     := GetArea()
Local aSavaCols := aClone(aCols)
Local aSavaHead := aClone(aHeader)
Local nMaxFor   := 0
Local nMaxFor1  := 0
Local nPos1     := 0
Local nUsado    := 0
Local nItSC6    := 0
Local nAcols    := 0
Local lContinua := .F.
Local lPedido   := .F.
Local nParcTp9  := SuperGetMV("MV_NUMPARC")
Local nSaveSX8  := GetSX8Len()
Local cCampo    := ""
Local bCampo    := {|x| FieldName(x) }
Local nCntFor1  := 0
Local nCntFor   := 0

If nOpc == 1
	PRIVATE aCols   := {}
	PRIVATE aHeader := {}
	nMaxFor := Len(aPedPV)
	If ( nMaxFor > 0 )
		
		//Monta aHeader do SC6
		DbSelectArea("SX3")
		DbSetOrder(1)
		MsSeek("SC6",.T.)
		While ( !Eof() .And. (SX3->X3_ARQUIVO == "SC6") )
			If (  ((X3Uso(SX3->X3_USADO) .And. ;
					!( Trim(SX3->X3_CAMPO) == "C6_NUM" ) .And.;
					Trim(SX3->X3_CAMPO) <> "C6_QTDEMP"   .And.;
					Trim(SX3->X3_CAMPO) <> "C6_QTDENT")  .And.;
					cNivel >= SX3->X3_NIVEL) )
				Aadd(aHeader,{ Trim(X3TITULO()),;
					SX3->X3_CAMPO,;
					SX3->X3_PICTURE,;
					SX3->X3_TAMANHO,;
					SX3->X3_DECIMAL,;
					SX3->X3_VALID,;
					SX3->X3_USADO,;
					SX3->X3_TIPO,;
					SX3->X3_ARQUIVO,;
					SX3->X3_CONTEXT } )
			EndIf
			DbSelectArea("SX3")
			dbSkip()
		EndDo

		For nCntFor := 1 To nMaxFor
			lContinua := .F.
			//Posiciona Registros
			DbSelectArea("SD2")
			DbSetOrder(3)
			MsSeek(xFilial("SD2")+aPedPV[nCntFor,2]+aPedPV[nCntFor,1]+aPedPV[nCntFor,4],.F.)

			While (!Eof() .And. xFilial("SD2") == SD2->D2_FILIAL     .And.;
					aPedPV[nCntFor,2] == SD2->D2_DOC                  .And.;
					aPedPV[nCntFor,1] == SD2->D2_SERIE                .And.;
					aPedPv[nCntFor,4] == SD2->D2_CLIENTE+SD2->D2_LOJA .And.;
					!lContinua )
				If ( AllTrim(SD2->D2_ITEM) == AllTrim(aPedPv[nCntFor,3]) )
					lContinua := .T.
				Else
					DbSelectArea("SD2")
					dbSkip()
				EndIf
			EndDo
			If ( lContinua )
				DbSelectArea("SC5")
				DbSetOrder(1)
				MsSeek(xFilial("SC5")+SD2->D2_PEDIDO,.F.)
				If ( Found() )
					DbSelectArea("SC6")
					DbSetOrder(1)
					MsSeek(xFilial("SC6")+SD2->D2_PEDIDO+SD2->D2_ITEMPV,.F.)
					If ( !lPedido )
						lPedido := .T.
						DbSelectArea("SC5")
						nMaxFor1 := FCount()
						For nCntFor1 := 1 To nMaxFor1
							M->&(EVAL(bCampo,nCntFor1)) := CriaVar(FieldName(nCntFor1),.T.)
						Next nCntFor1
						M->C5_TIPO    := SC5->C5_TIPO
						M->C5_CLIENTE := SC5->C5_CLIENTE
						M->C5_LOJAENT := SC5->C5_LOJAENT
						M->C5_LOJACLI := SC5->C5_LOJACLI
						M->C5_TIPOCLI := SC5->C5_TIPOCLI
						M->C5_CONDPAG := SC5->C5_CONDPAG
						M->C5_TABELA  := SC5->C5_TABELA
						M->C5_DESC1   := SC5->C5_DESC1
						M->C5_DESC2   := SC5->C5_DESC2
						M->C5_DESC3   := SC5->C5_DESC3
						M->C5_DESC4   := SC5->C5_DESC4
						For nCntFor1 :=  1 To nParcTp9
							cCampo := IIF(nCntFor1<=9,StrZero(nCntFor1,1),Chr(55+nCntFor1))
							cCampo := "C5_PARC"+cCampo
							nPos1 := SC5->(FieldPos(cCampo))
							M->&(cCampo) := SC5->(FieldGet(nPos1))
							cCampo := IIF(nCntFor1<=9,StrZero(nCntFor1,1),Chr(55+nCntFor1))
							cCampo := "C5_DATA"+cCampo
							nPos1 := SC5->(FieldPos(cCampo))
							M->&(cCampo) := SC5->(FieldGet(nPos1))
						Next nCntFor1
					EndIf
					
					//Preenche aCols
					nUsado := Len(aHeader)
					aadd(aCols,Array(nUsado+1))
					nAcols := Len(aCols)
					aCols[nAcols,nUsado+1] := .F.
					For nCntFor1 := 1 To nUsado
						Do Case
							Case ( AllTrim(aHeader[nCntFor1,2]) $ "C6_ITEM" )
								aCols[nAcols,nCntFor1] := StrZero(++nItSC6,Len(SC6->C6_ITEM))
							Case ( AllTrim(aHeader[nCntFor1,2]) $ "C6_QTDVEN" )
								aCols[naCols,nCntFor1] := aPedPv[nCntFor,5]
							Case ( AllTrim(aHeader[nCntFor1,10]) <> "V" )
								aCols[nAcols,nCntFor1] := SC6->(FieldGet(FieldPos(aHeader[nCntFor1,2])))
							Otherwise
								aCols[nAcols,nCntFor1] := CriaVar(aHeader[nCntFor1,2],.T.)
						EndCase
					Next nCntFor1
				EndIf
			EndIf
			//Aqui e'atualizado o numero de pedido gerado no sd1
			If ( lContinua )
				DbSelectArea("SD1")
				MsGoto(aPedPV[nCntFor,6])
				RecLock("SD1",.F.)
				SD1->D1_NUMPV  := M->C5_NUM
				SD1->D1_ITEMPV := StrZero(nItSC6,Len(SC6->C6_ITEM))
			EndIf
		Next nCntFor
		If ( lPedido )
			lGrade   := .F.
			cBloqc6  := ""
			PRIVATE lMTA410TE	:= (ExistTemplate("MTA410"))
			PRIVATE lMTA410		:= (ExistBlock("MTA410"))
			PRIVATE lMTA410I	:= (ExistBlock("MTA410I"))
			PRIVATE lM410ABN	:= (ExistBlock("M410ABN"))
			PRIVATE lMTA410E	:= (ExistBlock("MTA410E"))
			PRIVATE lA410EXC	:= (ExistBlock("A410EXC"))
			PRIVATE lM410LIOKT	:= (ExistTemplate("M410LIOK"))
			PRIVATE lM410LIOK	:= (ExistBlock("M410LIOK"))
			PRIVATE lMta410TTE	:= (ExistTemplate("MTA410T"))
			PRIVATE lMta410T	:= (ExistBlock("MTA410T"))
			PRIVATE l410DEL		:= (ExistBlock("M410DEL"))
			If Type("nAutoAdt") == "U"
				PRIVATE nAutoAdt:= 0
			EndIf
			a410Grava(.F.,.F.)
			While ( GetSX8Len() > nSaveSX8 )
				ConfirmSx8()
			EndDo
			MsgAlert(STR0065+M->C5_NUM) //"Gerada Ped.de Venda N.: "
		EndIf
	EndIf
	aCols   := aSavaCols
	aHeader := aSavaHead
Else
	//Rotina de estorno.
EndIf
RestArea(aArea)
Return(NIL)

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103VisuPC≥ Autor ≥ Edson Maricate       ≥ Data ≥16.02.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Chama a rotina de visualizacao dos Pedidos de Compras      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ Dicionario de Dados - Campo:D1_TOTAL                      ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103VisuPC(nRecSC7)

Local aArea			:= GetArea()
Local aAreaSC7		:= SC7->(GetArea())
Local nSavNF		:= MaFisSave()
Local cSavCadastro	:= cCadastro
Local cFilBak		:= cFilAnt
Local nBack       	:= n

PRIVATE nTipoPed	:= 1
PRIVATE cCadastro	:= OemToAnsi(STR0066) //"Consulta ao Pedido de Compra"
PRIVATE l120Auto	:= .F.
PRIVATE l123Auto	:= .F.
PRIVATE aBackSC7	:= {}  //Sera utilizada na visualizacao do pedido - MATA120

MaFisEnd()

DbSelectArea("SC7")
MsGoto(nRecSC7)

nTipoPed  := SC7->C7_TIPO
cCadastro := iif(nTipoPed==1 ,OemToAnsi(STR0066),OemToAnsi(STR0406)) //"Consulta ao Pedido de Compra"
cFilAnt   := IIf(!Empty(SC7->C7_FILIAL),SC7->C7_FILIAL,cFilAnt)

If SC7->C7_TIPO <> 3
	A120Pedido(Alias(),RecNo(),2)
Else
    nTipoPed := 3
	A123Pedido(Alias(),RecNo(),2)
EndIf

cFilant := cFilBak

n := nBack
cCadastro	:= cSavCadastro
MaFisRestore(nSavNF)
RestArea(aAreaSC7)
RestArea(aArea)

Return .T.

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103NFORI≥ Autor ≥ Edson Maricate        ≥ Data ≥16.02.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Faz a chamada da Tela de Consulta a NF original            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103NFORI()

Local bSavKeyF4 := SetKey(VK_F4,Nil)
Local bSavKeyF5 := SetKey(VK_F5,Nil)
Local bSavKeyF6 := SetKey(VK_F6,Nil)
Local bSavKeyF7 := SetKey(VK_F7,Nil)
Local bSavKeyF8 := SetKey(VK_F8,Nil)
Local bSavKeyF9 := SetKey(VK_F9,Nil)
Local bSavKeyF10:= SetKey(VK_F10,Nil)
Local bSavKeyF11:= SetKey(VK_F11,Nil)
Local nPosCod	:= GetPosSD1('D1_COD')
Local nPosLocal := GetPosSD1('D1_LOCAL')
Local nPosTes	:= GetPosSD1('D1_TES')
Local nPLocal	:= GetPosSD1('D1_LOCAL')
Local nPosOP 	:= GetPosSD1('D1_OP')
Local nPosNFOri	:= GetPosSD1('D1_NFORI')
Local nRecSD1   := 0
Local nRecSD2   := 0
Local lContinua := .T.
Local nTpCtlBN  := A410CtEmpBN()
Local lDHQInDic := AliasInDic("DHQ") .And. SF4->(ColumnPos("F4_EFUTUR") > 0)
Local lMt103Com := FindFunction("A103FutSel")
Local cIndPres	:= ""
Local cCodA1U	:= ""
Local nX		:= 0
Local nLinAtv	:= 0 

If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. cFormul == "S" 
	cIndPres := SubStr(aInfAdic[16],1,1)
	cCodA1U	 := aInfAdic[17]

	For nX := 1 To Len(aCols)
		If !aCols[nX,Len(aCols[nX])] .And. !Empty(aCols[nX,nPosNFOri])
			nLinAtv++
		Endif
	Next nX
Endif

//Impede de executar a rotina quando a tecla F3 estiver ativa
If Type("InConPad") == "L"
	lContinua := !InConPad
EndIf

If lContinua

	DbSelectArea("SF4")
	DbSetOrder(1)
	MsSeek(xFilial("SF4")+aCols[n][nPosTes])

	If MaFisFound("NF") .And. NfeCabOk(l103Visual,,,,,,,cUfOrig)
		Do Case
			Case lDHQInDic .And. lMt103Com .And. cTipo $ "NC" .And. SF4->F4_EFUTUR == "2"  // Se for remessa de compra futura.
				A103FutSel(aCompFutur, cA100For, cLoja, aCols[n][nPosCod])  // Seleciona a NF de origem (compra com entrega futura)
			Case cTipo $ "ND" .And. SF4->F4_PODER3 == "N"
				If F4NFORI(,,"M->D1_NFORI",cA100For,cLoja,aCols[n][nPosCod],"A100",aCols[n][nPLocal],@nRecSD2,,,cIndPres,cCodA1U,nLinAtv) .And. nRecSD2<>0
					NfeNfs2Acols(nRecSD2,n)
					aColsNF := aClone(aCols) 
				EndIf 
			Case cTipo$"CPI"
				If F4COMPL(,,,cA100For,cLoja,aCols[n][nPosCod],"A100",@nRecSD1,"M->D1_NFORI",cIndPres,cCodA1U,nLinAtv) .And. nRecSD1<>0
					NfeNfe2ACols(nRecSD1,n)
				EndIf
			Case cTipo $ "NB" .And. SF4->F4_PODER3=="D"
				If cPaisLoc=="BRA"
					If F4Poder3(aCols[n][nPosCod],aCols[n][nPosLocal],cTipo,"E",cA100For,cLoja,@nRecSD2,SF4->F4_ESTOQUE) .And. nRecSD2<>0
						NfeNfs2Acols(nRecSD2,n)
						If nPosOp > 0 .And. cTipo == "N" .And. (nTpCtlBN != 0)
                    	    If Empty(aCols[n][nPosOp])
								aCols[n][nPosOp] := A103OPBen(nil,nTpCtlBN)
	                        EndIf
						EndIf
					EndIf
				Else
					If A440F4("SB6",aCols[n][nPosCod],aCols[n][nPosLocal],"B6_PRODUTO","E",cA100For,cLoja,.F.,.F.,@nRecSD2,IIF(cTipo=="N","F","C")) > 0
						NfeNfs2Acols(nRecSD2,n)
					EndIf
				EndIf
			OtherWise
				If Empty(aCols[n][nPosCod]) .Or. Empty(aCols[n][nPosTes])
					Help('   ',1,'A103TPNFOR')
				ElseIf cTipo == "D" .And. SF4->F4_PODER3 <> "N"
					Help('   ',1,'A103TESNFD')
				ElseIf cTipo$"B" .And. SF4->F4_PODER3 <> "D"
					Help('   ',1,'A103TESNFB')
				EndIf
		EndCase
	Else
		Help('   ',1,'A103CAB')
	EndIf

	//PNEUAC - Ponto de Entrada,gravar na coluna Lote o numero baseado na nf Original
	If ExistBlock("PNEU002")
		ExecBlock("PNEU002",.F.,.F.)
	EndIf
Endif

// Atualiza valores na tela
If Type( "oGetDados" ) == "O"
	oGetDados:oBrowse:Refresh()
EndIf

SetKey(VK_F4,bSavKeyF4)
SetKey(VK_F5,bSavKeyF5)
SetKey(VK_F6,bSavKeyF6)
SetKey(VK_F7,bSavKeyF7)
SetKey(VK_F8,bSavKeyF8)
SetKey(VK_F9,bSavKeyF9)
SetKey(VK_F10,bSavKeyF10)
SetKey(VK_F11,bSavKeyF11)
// Atualiza valores na tela
Eval(bRefresh)
Return .T.

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103LoteF4≥ Autor ≥ Edson Maricate       ≥ Data ≥16.02.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Faz a chamada da Tela de Consulta a NF original            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103LoteF4()

Local bSavKeyF4 := SetKey(VK_F4,Nil)
Local bSavKeyF5 := SetKey(VK_F5,Nil)
Local bSavKeyF6 := SetKey(VK_F6,Nil)
Local bSavKeyF7 := SetKey(VK_F7,Nil)
Local bSavKeyF8 := SetKey(VK_F8,Nil)
Local bSavKeyF9 := SetKey(VK_F9,Nil)
Local bSavKeyF10:= SetKey(VK_F10,Nil)
Local bSavKeyF11:= SetKey(VK_F11,Nil)
Local lContinua := .T.
Local nPosCod	:= GetPosSD1("D1_COD" )
Local nPosLocal := GetPosSD1("D1_LOCAL" )

PRIVATE nPosLote   := GetPosSD1("D1_NUMLOTE")
PRIVATE nPosLotCTL := GetPosSD1("D1_LOTECTL")
PRIVATE nPosDvalid := GetPosSD1("D1_DTVALID")
PRIVATE nPosPotenc := GetPosSD1("D1_POTENCI")

//Impede de executar a rotina quando a tecla F3 estiver ativa
If Type("InConPad") == "L"
	lContinua := !InConPad
EndIf

If lContinua
	If MaFisFound('NF')
		If cTipo=="D"
			F4Lote(,,,"A103",aCols[n][nPosCod],aCols[n][nPosLocal])
		Else
			Help('  ',1,'A103TIPOD')
		EndIf
	Else
		Help('  ',1,'A103CAB')
	EndIf
Endif

SetKey(VK_F4,bSavKeyF4)
SetKey(VK_F5,bSavKeyF5)
SetKey(VK_F6,bSavKeyF6)
SetKey(VK_F7,bSavKeyF7)
SetKey(VK_F8,bSavKeyF8)
SetKey(VK_F9,bSavKeyF9)
SetKey(VK_F10,bSavKeyF10)
SetKey(VK_F11,bSavKeyF11)

Return .T.

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ FAtiva   ≥ Autor ≥ Edson Maricate        ≥ Data ≥ 18.10.95 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Chama a pergunte do mata103                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function FAtiva()
Pergunte("MTA103",.T.)
If ExistBlock("MT103SX1")
	ExecBlock("MT103SX1",.F.,.F.)
EndIf
Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103EstNCC≥ Autor ≥ Edson Maricate        ≥ Data ≥02.02.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Estorna os titulos de NCC gerados ao Cliente.               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function a103EstNCC()

Local cPref := PadR(&(SuperGetMV("MV_2DUPREF")), Len( SE1->E1_PREFIXO ) )
Local lIntGC	 
Local cE1Cliente
Local cE1Loja   
Local cE1NReduz

If cTipo == "D"
	lIntGC	 := IIf((SuperGetMV("MV_VEICULO",,"N")) == "S",.T.,.F.)
	cE1Cliente := cA100For // Quando integrado com DMS, o cliente pode ser outro se utilizado condicao de pagamento TIPO A na venda.
	cE1Loja    := cLoja    // Quando integrado com DMS, o cliente pode ser outro se utilizado condicao de pagamento TIPO A na venda.
	cE1NReduz  := "" 	   // Quando integrado com DMS, o cliente pode ser outro se utilizado condicao de pagamento TIPO A na venda.

	If lIntGC .and. ExistFunc("FMX_NCCCliente")
		FMX_NCCCliente(cNFiscal, cSerie, cA100For, cLoja, @cE1Cliente, @cE1Loja, @cE1NReduz)
	EndIf

	DbSelectArea("SE1")
	DbSetOrder(2)
	MsSeek(xFilial("SE1")+cE1Cliente+cE1Loja+cPref+cNFiscal)
	While !Eof() .And. xFilial("SE1")+cE1Cliente+cE1Loja+cPref+cNFiscal ==;
			E1_FILIAL+E1_CLIENTE+E1_LOJA+E1_PREFIXO+E1_NUM
		If If(cPaisLoc == "BRA",!(E1_TIPO $ MV_CRNEG),AllTrim(E1_TIPO) <> AllTrim(cEspecie))
			DbSelectArea("SE1")
			dbSkip()
		Else
			DbSelectArea("SA1")
			DbSetOrder(1)
			If MsSeek(xFilial("SA1")+SE1->E1_CLIENTE+SE1->E1_LOJA)
				AtuSalDup("+",SE1->E1_VALOR,SE1->E1_MOEDA,SE1->E1_TIPO,,SE1->E1_EMISSAO)
				AtuSldNat(SE1->E1_NATUREZ,SE1->E1_VENCREA,SE1->E1_MOEDA,"2","R",SE1->E1_VALOR,SE1->E1_VLCRUZ,"+",,FunName(),"SE1",SE1->(Recno()),Iif(INCLUI,3,4))
				DbSelectArea("SE1")
			Endif
			
			//Refaz  os valores da Comissao.
			If ( SuperGetMV("MV_TPCOMIS")=="O" )
				Fa440DeleE("MATA100")
			EndIf
			
			//Chamada da FunÁ„o IntegDef para disparar a rotina de ACCOUNTRECEIVABLEDOCUMENT                         
			If FWHasEAI("FINA040",.T.,, .T.)
   				FwIntegDef("FINA040",,,, "FINA040")
			Endif
			
			RecLock("SE1",.F.,.T.)
			dbDelete()
			MsUnlock()
			dbSkip()
		EndIf
	EndDo
EndIf
Return

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103ToFC030 ≥Autor≥ Edson Maricate        ≥ Data ≥06.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Compatibilizacao de variaveis utilizadas no FINC030/FINC010 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥Nenhum                                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥MATA103                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103TOFC030(cOper)
Local aArea			:= GetArea()
Local nposN			:= n
Local cSavCadastro	:= cCadastro
Local aSavaCols		:= aClone(aCols)
Local aSavaHeader	:= aClone(aHeader)
Local oBSomaItBKP
Local aoSbxBKP
Local oLstFinBKP
Local oLstImpBKP
Local cDocBKP
Local cSerieBKP
Local dEmissBKP

cOper := IIf(cOper == Nil, "E",cOper)

If (cOper=="E".And.cTipo$'DB') .Or. (cOper=="S".And.!(cTipo$'DB'))
	DbSelectArea('SA1')
	If Pergunte("FIC010",.T.)
		Fc010Con('SA1',RecNo(),3)
	EndIf
	Pergunte("MTA103",.F.)
Else
	If Pergunte("FIC030",.T.)
		If cPaisLoc != "BRA"
			oBSomaItBKP	:= oBSomaItens
			aoSbxBKP 	:= aClone(aoSbx)
			oLstFinBKP	:= oLstFin
			oLstImpBKP  := oLstImp
			If Type( "F1_DOC" ) <> "U"
				cDocBKP  	:= F1_DOC       //essas variaveis est„o no get
				cSerieBKP   := F1_SERIE
				dEmissBKP	:= F1_EMISSAO
			Else
				cDocBKP  	:= F2_DOC       //essas variaveis est„o no get
				cSerieBKP   := F2_SERIE
				dEmissBKP	:= F2_EMISSAO
			EndIf	
			
			MaFisSave()
			Finc030("Fc030Con")
			oBSomaItens	:= oBSomaItBKP
			aoSbx 		:= aClone(aoSbxBKP)
			oLstFin		:= oLstFinBKP
			oLstImp 	:= oLstImpBKP
			If Type( "F1_DOC" ) <> "U"
				F1_DOC 		:= cDocBKP
				F1_SERIE 	:= cSerieBKP
				F1_EMISSAO 	:= dEmissBKP
			Else
				F2_DOC 		:= cDocBKP
				F2_SERIE 	:= cSerieBKP
				F2_EMISSAO 	:= dEmissBKP
			EndIf
			
			MaFisRestore()
		Else
			Finc030("Fc030Con")
		EndIf
	EndIf
	Pergunte("MTA103",.F.)
EndIf

cCadastro	:= cSavCadastro
aCols		:= aClone(aSavaCols)
aHeader		:= aClone(aSavaHeader)
n			:= nposN
RestArea(aArea)

Return .T.

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103Histor≥ Prog. ≥Edson Maricate         ≥Data  ≥20.05.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Cria uma array contendo o Historic de Opercoes da NF.       ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103Histor(ExpN1)                                           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpN1 = 01.Registro da NF no SF1                           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ Array contendo os Historicos                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103Histor(nRecSF1)

Local aHistor	:= {}
Local aRet		:= {}
Local aArea		:= GetArea()
Local aAreaSF1	:= SF1->(GetArea())

DbSelectArea('SF1')
MsGoto(nRecSF1)

//Inclui no historico a data de Recebimento da Mercadoria
If !Empty(SF1->F1_RECBMTO)
	aAdd(aHistor,{SF1->F1_RECBMTO,"A",STR0075}) //"  Recebimento do Documento de Entrada."
Else
	aAdd(aHistor,{SF1->F1_RECBMTO,"A",STR0076}) //"  Este Documento de Entrada foi incluido em versıes anteriores do sistema."
EndIf

//Inclui no historico a data de Classificacao da NF
If !Empty(SF1->F1_STATUS) .And. AllTrim(SF1->F1_STATUS) <> "C" //Bloqueado Movimento
	aAdd(aHistor,{SF1->F1_DTDIGIT,"B",STR0077}) //"  Classificacao do Documento de Entrada."
EndIf

//Inclui no historico a data de Contabilizacao da NF
If !Empty(SF1->F1_DTLANC)
	aAdd(aHistor,{SF1->F1_DTLANC,"C",STR0078}) //"  Contabilizacao do Documento de Entrada."
EndIf

DbSelectArea("SD1")
DbSetOrder(1)
MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
While !Eof() .And. SD1->D1_FILIAL+SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA ==;
		xFilial("SD1")+cNFiscal+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA

	//Inclui no historico a data de Contabilizacao da NF
	Do Case
	Case cTipo == 'N'
		If SD1->D1_QTDEDEV <> 0
			DbSelectArea("SD2")
			DbSetOrder(8)
			MsSeek(xFilial("SD2")+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_DOC+SD1->D1_SERIE)
			While !Eof() .And. xFilial("SD2")+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_DOC+SD1->D1_SERIE==;
					SD2->D2_FILIAL+SD2->D2_CLIENTE+SD2->D2_LOJA+SD2->D2_NFORI+SD2->D2_SERIORI
				If aScan(aHistor,{|x| x[1]==SD2->D2_EMISSAO .And. x[3]==STR0079+SD2->D2_DOC+"/"+SerieNfId("SD2",2,D2_SERIE)}) == 0 //"  Devolucao efetuada : "
					aAdd(aHistor,{SD2->D2_EMISSAO,"D",STR0079+SD2->D2_DOC+"/"+SerieNfId("SD2",2,D2_SERIE)}) //"  Devolucao efetuada : "
				EndIf
				dbSkip()
			End
		EndIf
	EndCase
	DbSelectArea("SD1")
	dbSkip()
EndDo

aSort(aHistor,,,{|x,y| x[2]+DTOC(x[1]) < y[2]+DTOC(y[1])})
aEval(aHistor,{|x| aAdd(aRet,DTOC(x[1])+x[3]) })

RestArea(aAreaSF1)
RestArea(aARea)

Return aRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103Rodape≥ Prog. ≥Edson Maricate         ≥Data  ≥20.05.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Cria o Rodape compativel para NF incluidas pelo MATA100     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103Rodape(ExpO1)                                           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpO1 = Janela principal                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ Nenhum                                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103, Compatibilizacao com Notas do MATA100             ≥±±
±±≥          ≥          nas telas de visualizacao e exclusao.             ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103Rodape(oFolderWnd)
Local nValMerc	:= SF1->F1_VALMERC
Local nFrete	:= SF1->F1_FRETE
Local nValDesp	:= SF1->F1_DESPESA
Local nDesconto	:= SF1->F1_DESCONT
Local nAcessori	:= SF1->F1_BASEFD
Local nBsIcms	:= SF1->F1_BASEICM
Local nIPI		:= SF1->F1_VALIPI
Local nIcms		:= SF1->F1_VALICM
Local nBsIcmRet	:= SF1->F1_BRICMS
Local nVIcmRet	:= SF1->F1_ICMSRET
Local nValFun	:= SF1->F1_CONTSOC

@ 5  ,5   SAY STR0080 Of oFolderWnd PIXEL SIZE 32 ,9 //'Mercadorias'
@ 4  ,45  MSGET nValMerc  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

@ 5  ,105 SAY STR0081 Of oFolderWnd PIXEL SIZE 43 ,9 //'Frete'
@ 4  ,130 MSGET nFrete  PICTURE '@E 999,999,999.99' When .F.  OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

@ 5  ,200 SAY STR0082 Of oFolderWnd PIXEL SIZE 35 ,9 //'Despesas'
@ 4  ,230 MSGET nValDesp  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

@ 20 ,6   SAY STR0083 Of oFolderWnd PIXEL SIZE 27 ,9 //'Descontos'
@ 19 ,45  MSGET nDesconto  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

@ 20 ,150 SAY STR0084 Of oFolderWnd PIXEL SIZE 95 ,9 //'Base das Despesas Acessorias'
@ 19 ,230 MSGET nAcessori  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

@ 35 ,6   SAY STR0085 Of oFolderWnd PIXEL SIZE 39 ,9 //'Base de ICMS'
@ 34 ,45  MSGET nBsIcms  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

@ 35 ,105 SAY STR0086 Of oFolderWnd PIXEL SIZE 25 ,9 //'IPI'
@ 34 ,130 MSGET nIpi  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

@ 35 ,205 SAY STR0087 Of oFolderWnd PIXEL SIZE 20 ,9 //'ICMS'
@ 34 ,230 MSGET nICMS  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

If nBsIcmRet+nVIcmRet > 0
	@ 50 ,6   SAY STR0088 Of oFolderWnd PIXEL SIZE 40 ,9 //'Bs. ICMS Ret.'
	@ 49 ,45  MSGET nBsIcmRet  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9

	@ 50 ,100 SAY STR0089 Of oFolderWnd PIXEL SIZE 24 ,9 //'ICMS Ret'
	@ 49 ,130 MSGET nVIcmRet  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9
EndIf

If nValFun > 0
	@ 50 ,194 SAY STR0090 Of oFolderWnd PIXEL SIZE 31 ,9 //'FunRural'
	@ 49 ,230 MSGET nValFun  PICTURE '@E 999,999,999.99' When .F. OF oFolderWnd PIXEL RIGHT SIZE 48 ,9
EndIf

Return Nil

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103Legenda≥ Autor ≥ Edson Maricate       ≥ Data ≥ 01.02.99 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Cria uma janela contendo a legenda da mBrowse              ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103Legenda()

Local aLegenda := {}
Local lGspInUseM := If(Type('lGspInUse')=='L', lGspInUse, .F.)
Local lF1Desa := SF1->(FieldPos("F1_IDDES")) > 0 .And. SF1->(FieldPos("F1_OBSDES")) > 0

aAdd(aLegenda, {"ENABLE"    ,STR0091}) //"Docto. nao Classificado"
aAdd(aLegenda, {"BR_LARANJA",STR0147}) //"Docto. Bloqueado"
aAdd(aLegenda, {"BR_VIOLETA",STR0326}) //"Doc. C/Bloq. de Mov."
aAdd(aLegenda, {"DISABLE"   ,STR0092}) //"Docto. Normal"

If !lGspInUseM
	aAdd(aLegenda, {"BR_AZUL"   ,STR0093}) //"Docto. de Compl. IPI"
	aAdd(aLegenda, {"BR_MARROM" ,STR0094}) //"Docto. de Compl. ICMS"
	aAdd(aLegenda, {"BR_PINK"   ,STR0095}) //"Docto. de Compl. Preco/Frete/Desp. Imp."
	aAdd(aLegenda, {"BR_CINZA"  ,STR0096}) //"Docto. de Beneficiamento"
	aAdd(aLegenda, {"BR_AMARELO",STR0097}) //"Docto. de Devolucao"
Endif

If SuperGetMV("MV_CONFFIS",.F.,"N") == "S"
	aAdd(aLegenda,{"BR_PRETO",STR0098}) //"Docto. em processo de conferencia"
EndIf

If lF1Desa 
	aAdd(aLegenda,{"BR_BRANCO",STR0510}) // Evento desacordo aguardando SEFAZ
	aAdd(aLegenda,{"BR_AZUL_CLARO",STR0511}) // Evento desacordo vinculado 
	aAdd(aLegenda,{"BR_VERDE_ESCURO",STR0512}) // Evento desacordo com problemas
Endif

//Ponto de entrada para inclus„o de novo STATUS da legenda
If ( ExistBlock("MT103LEG") )
	aLegeUsr := ExecBlock("MT103LEG",.F.,.F.,{aLegenda})
	If ( ValType(aLegeUsr) == "A" )
		aLegenda := aClone(aLegeUsr)
	EndIf
EndIf

If SF1->( FieldPos( "F1_GF" ) ) > 0
	aAdd(aLegenda, {"BR_MARRON_OCEAN",STR0562}) //"NF N„o Classificada com GF"
EndIf

BrwLegenda(cCadastro,STR0008 ,aLegenda) //"Legenda"

Return .T.

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥ A103Bar  ≥ Prog. ≥ Sergio Silveira       ≥Data  ≥23/02/2001≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Cria a enchoicebar.                                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103Bar( ExpO1, ExpB1, ExpB2, ExpA1 )                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpO1 = Objeto dialog                                      ≥±±
±±≥          ≥ ExpB1 = Code block de confirma                             ≥±±
±±≥          ≥ ExpB2 = Code block de cancela                              ≥±±
±±≥          ≥ ExpA1 = Array com botoes ja incluidos.                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ Retorna o retorno da enchoicebar                           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103Bar(oDlg,bOk,bCancel,aButtonsAtu, aInfo  )

Local aUsButtons := {}
Local lMvNfeDvg := SuperGetMV("MV_NFEDVG", .F., .T.)

If lMvNfeDvg
	aadd(aButtonsAtu,{"BUDGET", {|| _MA103Div1()}, STR0534, STR0535 }) //#"Cadastro de divergencias" #"Divergencias"
EndIf

//Adiciona botoes do usuario na EnchoiceBar
If ExistTemplate( "MA103BUT" )
	If ValType( aUsButtons := ExecTemplate( "MA103BUT", .F., .F.,{aInfo} ) ) == "A"
		AEval( aUsButtons, { |x| AAdd( aButtonsAtu, x ) } )
	EndIf
EndIf
If ExistBlock( "MA103BUT" )
	If ValType( aUsButtons := ExecBlock( "MA103BUT", .F., .F.,{aInfo} ) ) == "A"
		AEval( aUsButtons, { |x| AAdd( aButtonsAtu, x ) } )
	EndIf
EndIf

Return (EnchoiceBar(oDlg,bOK,bcancel,,aButtonsAtu))

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103Devol≥ Autor ≥ Henry Fila             ≥ Data ≥ 09-02-2001 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Programa de Consulta de Historicos da Revisao.               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpC1 = Alias do arquivo                                     ≥±±
±±≥          ≥ ExpN1 = Numero do registro                                   ≥±±
±±≥          ≥ ExpN2 = Numero da opcao selecionada                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ Generico                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Function A103Devol(cAlias,nReg,nOpcx)
	// o conteudo da funÁ„o A103Devol foi migrada para o fonte MATA103R.PRX com novo nome de funcao SA103Devol 
	SA103Devol(cAlias,nReg,nOpcx)
Return .T.

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥A103ProcDv∫Autor  ≥Henry Fila          ∫ Data ≥  06/29/01   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥ Abre a tela da nota fiscal de entrada de acordo com a nota ∫±±
±±∫          ≥ de saida escolhida no browse                               ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±≥Parametros≥ ExpC1 = Alias do arquivo                                   ≥±±
±±≥          ≥ ExpN1 = Numero do registro                                 ≥±±
±±≥          ≥ ExpN2 = Numero da opcao selecionada                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±∫Uso       ≥ AP6                                                        ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Function A103ProcDv(cAlias,nReg,nOpcx,lCliente,cCliente,cLoja,cDocSF2,lFlagDev)

Local aArea     := GetArea()
Local aAreaSF2  := SF2->(GetArea())
Local aAreaBkp  := nil
Local aCab      := {}
Local aLinha    := {}
Local aItens    := {}
Local cTipoNF   := ""
Local lDevolucao:= .T.
Local lPoder3   := .T.
Local cIndex	:= ""
Local lRestDev	:= .T.
Local nPosNf	:= 0
Local nPosNfSer := 0
Local nPFreteI  := 0
Local nPFreteC  := 0
Local nPSegurI  := 0
Local nPSegurC  := 0
Local nPDespI   := 0
Local nPDespC   := 0
Local nX        := 0
Local cMvNFEAval :=	GetNewPar( "MV_NFEAFSD", "000" )
Local nHpP3     := 0
Local lHelpTES  := .T.
Local cEspecie	:= "NF"
Local cIndPres	:= ""
Local cCodA1U	:= ""

Default lCliente := .F.
Default cCliente := SF2->F2_CLIENTE
Default cLoja    := SF2->F2_LOJA
Default cDocSF2  := ''
Default	cQrDvF2  := ''
Default lFlagDev := .F.

If Type("cTipo") == "U"
	PRIVATE cTipo:= ""
EndIf

If Empty(cQrDvF2)
	cQrDvF2 := "F2_FILIAL == '" + xFilial("SF2") + "' "
	cQrDvF2 += ".AND. F2_TIPO <> 'D' "
Endif

If !SF2->(Eof())

	lDevolucao := M103FilDv(@aLinha,@aItens,cDocSF2,cCliente,cLoja,lCliente,@cTipoNF,@lPoder3,,@nHpP3,@lHelpTES,@cEspecie,@cIndPres,@cCodA1U)

	If lDevolucao .and. Len(aItens)>0
		
		//Montagem do Cabecalho da Nota fiscal de Devolucao/Retorno
		AAdd( aCab, { "F1_DOC"    , CriaVar("F1_DOC",.F.)			, Nil } )	// Numero da NF : Obrigatorio
		AAdd( aCab, { "F1_SERIE"  , CriaVar("F1_SERIE",.F.)		, Nil } )	// Serie da NF  : Obrigatorio

		If !lPoder3
			AAdd( aCab, { "F1_TIPO"   , "D"                  		, Nil } )	// Tipo da NF   : Obrigatorio
		Else
			AAdd( aCab, { "F1_TIPO"   , IIF(cTipoNF=="B","N","B")	, Nil } )	// Tipo da NF   : Obrigatorio
		EndIf

		AAdd( aCab, { "F1_FORNECE", cCliente    				, Nil } )	// Codigo do Fornecedor : Obrigatorio
		AAdd( aCab, { "F1_LOJA"   , cLoja    	   		   	    , Nil } )	// Loja do Fornecedor   : Obrigatorio
		AAdd( aCab, { "F1_EMISSAO", dDataBase           		, Nil } )	// Emissao da NF        : Obrigatorio
		AAdd( aCab, { "F1_FORMUL" , "S"                 		, Nil } )  // Formulario
		AAdd( aCab, { "F1_ESPECIE", If(Empty(CriaVar("F1_ESPECIE",.T.)) .And. !ExistBlock("MT103ESP"),; 
			PadR(cEspecie,Len(SF1->F1_ESPECIE)),CriaVar("F1_ESPECIE",.T.)), Nil } )  // Especie
		AAdd( aCab, { "F1_FRETE",0,Nil})
		AAdd( aCab, { "F1_SEGURO",0,Nil})
		AAdd( aCab, { "F1_DESPESA",0,Nil})

		If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
			AAdd( aCab, { "F1_INDPRES",cIndPres,Nil})
			AAdd( aCab, { "F1_CODA1U",cCodA1U,Nil})
		Endif

    	//Agrega o Frete/Desp/Seguro  referente a NF Retornada de acordo com o parametro MV_NFEAFSD
		nPFreteC := aScan(aCab,{|x| AllTrim(x[1])=="F1_FRETE"})
		nPFreteI := aScan(aItens[1],{|x| AllTrim(x[1])=="D1_VALFRE"})
   		nPSegurC := aScan(aCab,{|x| AllTrim(x[1])=="F1_SEGURO"})
		nPSegurI := aScan(aItens[1],{|x| AllTrim(x[1])=="D1_SEGURO"})
   		nPDespC := aScan(aCab,{|x| AllTrim(x[1])=="F1_DESPESA"})
		nPDespI := aScan(aItens[1],{|x| AllTrim(x[1])=="D1_DESPESA"})

		For nX = 1 to Len(aItens)
		    If len(cMvNFEAval)>=1
		        If Substr(cMvNFEAval,1,1)=="1"
  		   			aCab[nPFreteC][2] := aCab[nPFreteC][2] + aItens[nX][nPFreteI][2]
  		  	    EndIf
  		  	EndIf
  		  	If len(cMvNFEAval)>=2
		        If Substr(cMvNFEAval,2,1)=="1"
  		    		aCab[nPSegurC][2] := aCab[nPSegurC][2] + aItens[nX][nPSegurI][2]
  		  	    EndIf
  		  	EndIf
   		  	If len(cMvNFEAval)=3
		        If Substr(cMvNFEAval,3,1)=="1"
  		    		aCab[nPDespC][2] := aCab[nPDespC][2] + aItens[nX][nPDespI][2]
  		  	    EndIf
  		  	EndIf
		Next nX

		Mata103( aCab, aItens , 3 , .T.)
		//Verifica se nao ha mais saldo para devolucao
		If cPaisLoc == "BRA" .And. lFlagDev
			lRestDev := M103FilDv(@aLinha,@aItens,cDocSF2,cCliente,cLoja,lCliente,@cTipoNF,@lPoder3,.F.)
			If !lRestDev
				aAreaBkp := SF2->(GetArea())
				for nX := 1 to len(aItens)
					nPosNf 	  := aScan(aItens[nX],{|x| AllTrim(x[1])=="D1_NFORI"})
					nPosNfSer := aScan(aItens[nX],{|x| AllTrim(x[1])=="D1_SERIORI"})
					if nPosNf > 0 .and. nPosNfSer > 0
						SF2->(DbSetOrder(1)) //F2_FILIAL+F2_DOC+F2_SERIE+F2_CLIENTE+F2_LOJA
						if SF2->(MsSeek(fwxFilial("SF2") + aItens[nX][nPosNf][2] + aItens[nX][nPosNfSer][2] + cCliente + cLoja))
							if RecLock("SF2",.F.)
								SF2->F2_FLAGDEV := "1"
								SF2->(MsUnlock())
							endif
						endif
					endif
				next nX
				RestArea(aAreaBkp)
			Endif
		Endif
	Else
		
		If lHelpTES .And. !lDevolucao .And. !lPoder3
			Help(" ", 1, "TESPOD3")
		EndIf
		/*
		nHpP3 = Situacao 0 -> Mostra a mensagem
		nHpP3 = Situacao 1 -> Nao mostra a mensagem
		*/
		If (nHpP3 == 0) .And. lPoder3
			Help(" ",1,"NFDGSPTZ")	//Nota Fiscal de DevoluÁ„o j· gerada ou o saldo devedor em poder de terceiro est· zerado.
		EndIf
	EndIf

	MsUnLockAll()

	//Refaz o filtro quando a selecao e por documento, visto que a tela com os documentos que podem ser devolvidos e montada novamente.
	If !lCliente
		DbSelectArea("SF2")
		SF2->(dbSetOrder(1))
		cIndex := CriaTrab(NIL,.F.)
		IndRegua("SF2",cIndex,SF2->(IndexKey()),,cQrDvF2)
	Endif
Endif

//Restaura a entrada da rotina
RestArea(aAreaSF2)
RestArea(aArea)
Return(.T.)

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥M103FilDv ∫Autor  ≥Mary C. Hergert     ∫ Data ≥19/03/2008   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥ Verifica os itens que podem ser devolvidos do documento    ∫±±
±±∫          ≥ selecionado.                                               ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±≥Parametros≥ ExpA1 = Linhas com os itens de devoluvao                   ≥±±
±±≥          ≥ ExpA2 = Itens de devolucao                                 ≥±±
±±≥          ≥ ExpC3 = Documentos do SF2 a serem processados              ≥±±
±±≥          ≥ ExpC4 = Cliente do filtro                                  ≥±±
±±≥          ≥ ExpC5 = Loja do cliente do filtro                          ≥±±
±±≥          ≥ ExpL6 = Se a tela e por cliente/fornecedor                 ≥±±
±±≥          ≥ ExpL7 = Tipo do documento - normal, devolucao, benefic.    ≥±±
±±≥          ≥ ExpL8 = Se tem controle de terceiros no estoque            ≥±±
±±≥          ≥ ExpL9 =                                                    ≥±±
±±≥          ≥ ExpL10 = Ativa mensagem de poder de terceiros              ≥±±
±±≥          ≥ ExpL10                                                     ≥±±
±±≥          ≥ ExpC12 = Especie Padr„o Utilizada no Documento             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±∫Uso       ≥ AP6                                                        ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Function M103FilDv(aLinha,aItens,cDocSF2,cCliente,cLoja,lCliente,cTipoNF,lPoder3,lHelp,nHpP3,lHelpTES,cEspecie,cIndPres,cCodA1U)

Local aAreaAnt  := {}
Local aSaldoTerc:= {}
Local aStruSD2  := {}
Local cFilSX5   := xFilial("SX5")
Local cAliasSF4 := ""
Local cAliasSD2 := ""
Local cCfop     := ""
Local cNFORI  	:= ""
Local cSERIORI	:= ""
Local cITEMORI	:= ""
Local cNewDSF2	:= ""
Local cDSF2Aux	:= ""
Local cQuery    := ""
Local cAliasCpl := ""
Local nTpCtlBN  := A410CtEmpBN()
Local nSldDev   := 0
Local nSldDevAux:= 0
Local nDesc     := 0
Local nTotal	:= 0
Local nVlCompl  := 0
Local nPosDiv	:= 0
Local nX		:= 0
Local lMt103FDV := ExistBlock("MT103FDV")
Local lCompl    := SuperGetMv("MV_RTCOMPL",.F.,"S") == "S"
Local lDevolucao:= .T.
Local lDevCode	:= .F.
Local lTravou	:= .F.
Local lExit		:= .F.

Default lHelp    := .T.
Default lHelpTES := .T.

If !Empty(cDocSF2)												// Selecao foi feita por "Cliente/Fornecedor"

	cNewDSF2 := StrTran(StrTran(cDocSF2,"('",),"')",)			// Retira parÍteses e aspas da string do documento, caso houver

	nPosDiv := At("','",cNewDSF2)								// String ',' identifica que foi selecionada mais de uma nota de saida
	If nPosDiv == 0												// Se foi selecionada apenas uma nota de saida
		DbSelectArea("SF2")
		DbSetOrder(1)
		If MsSeek(xFilial("SF2")+cNewDSF2+cCliente+cLoja)
			lTravou := SoftLock("SF2")							// Tenta reservar o registro para prosseguir com o processo
		Else
			dbGoTop()
		EndIf
	Else														// Se foi selecionada mais de uma nota de saida
		cDSF2Aux := cNewDSF2
		For nX := 1 to Len(cDSF2Aux)
			nPosDiv := At("','",cDSF2Aux)
			If nPosDiv > 0
				cNewDSF2 := SubStr(cDSF2Aux,1,(nPosDiv-1))		// Extrai a primeira nota/serie da string
				cDSF2Aux := SubStr(cDSF2Aux,(nPosDiv+3),Len(cDSF2Aux)) // Grava nova string sem a primeira nota/serie
			Else
				cNewDSF2 := cDSF2Aux
				lExit := .T.
			EndIf
			If !Empty(cNewDSF2)
				DbSelectArea("SF2")
				DbSetOrder(1)
				If MsSeek(xFilial("SF2")+cNewDSF2+cCliente+cLoja)
					lTravou := SoftLock("SF2")					// Tenta reservar todos os registros para prosseguir com o processo
				Else
					dbGoTop()
				EndIf
			EndIf
			If lExit
				Exit
			EndIf
		Next nX
	EndIf
Else
	lTravou := SoftLock("SF2")
EndIf

If lTravou

	If !Empty(SF2->F2_ESPECIE)
		cEspecie := SF2->F2_ESPECIE
	EndIf

	//Montagem dos itens da Nota Fiscal de Devolucao/Retorno
	DbSelectArea("SD2")
	DbSetOrder(3)

	cAliasSD2 := "Oms320Dev"
	cAliasSF4 := "Oms320Dev"
	aStruSD2  := SD2->(dbStruct())
	cQuery    := "SELECT SF4.F4_CODIGO, SF4.F4_CF, SF4.F4_PODER3, SF4.F4_QTDZERO, SF4.F4_ATUATF, SF4.F4_ESTOQUE, SF4.F4_CONTERC, SD2.*, "
	cQuery    += " SD2.R_E_C_N_O_ SD2RECNO "
	cQuery    += " FROM "+RetSqlName("SD2")+" SD2,"
	cQuery    += RetSqlName("SF4")+" SF4 "
	cQuery    += " WHERE SD2.D2_FILIAL='"+xFilial("SD2")+"' AND "
	If !lCliente
		cQuery    += "SD2.D2_DOC   = '"+SF2->F2_DOC+"' AND "
		cQuery    += "SD2.D2_SERIE = '"+SF2->F2_SERIE+"' AND "
	Else
		If !Empty(cDocSF2)
			If UPPER(Alltrim(TCGetDb()))=="POSTGRES"
				cQuery += " Concat(D2_DOC,D2_SERIE) IN "+cDocSF2+" AND "
			Else
				cQuery += " D2_DOC||D2_SERIE IN "+cDocSF2+" AND "
			EndIf
		EndIf
	EndIf
	cQuery    += " SD2.D2_CLIENTE   = '"+cCliente+"' AND "
	cQuery    += " SD2.D2_LOJA      = '"+cLoja+"' AND "
	cQuery    += " ((SD2.D2_QTDEDEV < SD2.D2_QUANT) OR "
	cQuery    += " (SD2.D2_VALDEV  = 0) OR "
	cQuery    += " (SF4.F4_QTDZERO = '1' AND SD2.D2_VALDEV < SD2.D2_TOTAL)) AND "
	cQuery    += " SD2.D_E_L_E_T_  = ' ' AND "
	cQuery    += " SF4.F4_FILIAL   = '"+xFilial("SF4")+"' AND "
	cQuery    += " SF4.F4_CODIGO   = (SELECT F4_TESDV FROM "+RetSqlName("SF4")+" WHERE "
	cQuery    += " F4_FILIAL	   = '"+xFilial("SF4")+"' AND "
	cQuery    += " F4_CODIGO	   = SD2.D2_TES AND "
	cQuery    += " D_E_L_E_T_	   = ' ' ) AND "
	cQuery    += " SF4.D_E_L_E_T_  = ' ' "
	cQuery    += " ORDER BY "+SqlOrder(SD2->(IndexKey()))

	cQuery    := ChangeQuery(cQuery)
	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSD2,.T.,.T.)

	For nX := 1 To Len(aStruSD2)
		If aStruSD2[nX][2]<>"C"
			TcSetField(cAliasSD2,aStruSD2[nX][1],aStruSD2[nX][2],aStruSD2[nX][3],aStruSD2[nX][4])
		EndIf
	Next nX

	If Eof()
		If lHelp
			Help(" ",1,"DSNOTESDT")
			nHpP3 := 1
		EndIf
		lDevolucao := .F.
		lHelpTES   := .F.
	EndIf

	While !Eof() .And. (cAliasSD2)->D2_FILIAL == xFilial("SD2") .And.;
			(cAliasSD2)->D2_CLIENTE 		   == cCliente 		  .And.;
			(cAliasSD2)->D2_LOJA			   == cLoja 		  .And.;
			If(!lCliente,(cAliasSD2)->D2_DOC  == SF2->F2_DOC     .And.;
			(cAliasSD2)->D2_SERIE			   == SF2->F2_SERIE,.T.)

		If ((cAliasSD2)->D2_QTDEDEV < (cAliasSD2)->D2_QUANT) .Or. ((cAliasSD2)->D2_VALDEV == 0) .Or. ((cAliasSD2)->F4_QTDZERO == "1" .And. (cAliasSD2)->D2_VALDEV < (cAliasSD2)->D2_TOTAL)

			If (cAliasSD2)->F4_PODER3<>"D"
				lPoder3 := .F.
			EndIf
			If lPoder3 .And. !cTipo$"B|N"
				cTipo := IIF(cTipoNF=="B","N","B")
			ElseIf !cTipo$"B|N"
				cTipo := "D"
			EndIf			

			If !lMt103FDV .Or. ExecBlock("MT103FDV",.F.,.F.,{cAliasSD2})
				//Destroi o Array, o mesmo È carregado novamente pela CalcTerc
				If Len(aSaldoTerc)>0
					aSize(aSaldoTerc,0)
				EndIf

				//Calcula o Saldo a devolver
				cTipoNF := (cAliasSD2)->D2_TIPO

				Do Case
					Case (cAliasSF4)->F4_PODER3=="D"
						aSaldoTerc := CalcTerc((cAliasSD2)->D2_COD,(cAliasSD2)->D2_CLIENTE,(cAliasSD2)->D2_LOJA,(cAliasSD2)->D2_IDENTB6,(cAliasSD2)->D2_TES,cTipoNF)
						nSldDev :=iif(Len(aSaldoTerc)>0,aSaldoTerc[1],0)
					Case cTipoNF == "N"
						nSldDev := (cAliasSD2)->D2_QUANT-(cAliasSD2)->D2_QTDEDEV
					Case cTipoNF == "B" .And.(cAliasSF4)->F4_PODER3 =="N" .And. A103DevPdr((cAliasSF4)->F4_CODIGO)
						nSldDev := (cAliasSD2)->D2_QUANT-(cAliasSD2)->D2_QTDEDEV
						lPoder3 := .T.
					OtherWise
						nSldDev := 0
				EndCase

				//Efetua a montagem da Linha
				If nSldDev > 0 .Or. (cTipoNF$"CIP" .And. (cAliasSD2)->D2_VALDEV == 0) .Or.;
				   ( (cAliasSD2)->D2_QUANT == 0 .And. (cAliasSD2)->D2_VALDEV == 0 .And. (cAliasSD2)->D2_TOTAL > 0 ) .Or.;
					( (cAliasSD2)->F4_QTDZERO == "1" .And. (cAliasSD2)->D2_VALDEV < (cAliasSD2)->D2_TOTAL )

					lDevCode := .T.

					//Verifica se deve considerar o preco das notas de complemento
					If lCompl
						//Verifica se existe nota de complemento de preco
						aAreaAnt  := GetArea()
						cAliasCpl := GetNextAlias()
						cQuery    := "SELECT SUM(SD2.D2_PRCVEN) AS D2_PRCVEN "
						cQuery    += "  FROM "+RetSqlName("SD2")+" SD2 "
						cQuery    += " WHERE SD2.D2_FILIAL  = '"+xFilial("SD2")+"'"
						cQuery    += "   AND SD2.D2_TIPO    = 'C' "
						cQuery    += "   AND SD2.D2_NFORI   = '"+SF2->F2_DOC+"'"
						cQuery    += "   AND SD2.D2_SERIORI = '"+SF2->F2_SERIE+"'"
						cQuery    += "   AND SD2.D2_ITEMORI = '"+(cAliasSD2)->D2_ITEM +"'"
						cQuery    += "   AND ((SD2.D2_QTDEDEV < SD2.D2_QUANT) OR "
						cQuery    += "       (SD2.D2_VALDEV = 0))"
						cQuery    += "   AND SD2.D2_TES         = '"+(cAliasSD2)->D2_TES+"'"
						cQuery    += "   AND SD2.D_E_L_E_T_     = ' ' "

						cQuery    := ChangeQuery(cQuery)
						dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasCpl,.T.,.T.)

						TcSetField(cAliasCpl,"D2_PRCVEN","N",TamSX3("D2_PRCVEN")[1],TamSX3("D2_PRCVEN")[2])

						If !(cAliasCpl)->(Eof())
							nVlCompl := (cAliasCpl)->D2_PRCVEN
						Else
							nVlCompl := 0
						EndIf

						(cAliasCpl)->(dbCloseArea())
						RestArea(aAreaAnt)
					EndIf

					aLinha := {}
					nDesc  := 0
	  				AAdd( aLinha, { "D1_COD"    , (cAliasSD2)->D2_COD    , Nil } )
					AAdd( aLinha, { "D1_QUANT"  , nSldDev, Nil } )
					If (cAliasSD2)->D2_QUANT==nSldDev
						If Len(aSaldoTerc)=0   // Nf sem Controle Poder Terceiros
							If ((cAliasSD2)->F4_QTDZERO == "1" .And. (cAliasSD2)->D2_VALDEV < (cAliasSD2)->D2_TOTAL)
								AAdd( aLinha, { "D1_VUNIT"  , ((cAliasSD2)->D2_PRCVEN - (cAliasSD2)->D2_VALDEV), Nil })
							ElseIf (cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR == 0
							   	AAdd( aLinha, { "D1_VUNIT"  , (cAliasSD2)->D2_PRCVEN, Nil })
							Else
							    nDesc:=(cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR
								AAdd( aLinha, { "D1_VUNIT"  , ((cAliasSD2)->D2_TOTAL+nDesc)/(cAliasSD2)->D2_QUANT, Nil })
							EndIf
						Else                   // Nf com Controle Poder Terceiros
							If (cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR == 0
								AAdd( aLinha, { "D1_VUNIT"  , NoRound((aSaldoTerc[5]-aSaldoTerc[4])/nSldDev,TamSX3("D2_PRCVEN")[2]), Nil })
							Else
							    nDesc:=(cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR
							    nDesc:=iif(nDesc>0,(nDesc/aSaldoTerc[6])*nSldDev,0)
								AAdd( aLinha, { "D1_VUNIT"  , NoRound(((aSaldoTerc[5]+nDesc)-aSaldoTerc[4])/nSldDev,TamSX3("D2_PRCVEN")[2]), Nil })
							EndIf
						EndIf
						nTotal:= A410Arred(aLinha[2][2]*aLinha[3][2],"D1_TOTAL")
						If nTotal == 0 .And. (cAliasSD2)->D2_QUANT == 0 .And. (cAliasSD2)->D2_PRCVEN == (cAliasSD2)->D2_TOTAL
							If (cAliasSD2)->F4_QTDZERO == "1"
								nTotal := (cAliasSD2)->D2_TOTAL - (cAliasSD2)->D2_VALDEV
							Else
								nTotal := (cAliasSD2)->D2_TOTAL
							EndIf
						EndIf
	 					AAdd( aLinha, { "D1_TOTAL"  , nTotal,Nil } )
						AAdd( aLinha, { "D1_VALDESC", nDesc , Nil } )
						AAdd( aLinha, { "D1_VALFRE", (cAliasSD2)->D2_VALFRE, Nil } )
						AAdd( aLinha, { "D1_SEGURO", (cAliasSD2)->D2_SEGURO, Nil } )
						AAdd( aLinha, { "D1_DESPESA", (cAliasSD2)->D2_DESPESA, Nil } )
					Else
						nSldDevAux:= (cAliasSD2)->D2_QUANT-(cAliasSD2)->D2_QTDEDEV
						If Len(aSaldoTerc)=0	// Nf sem Controle Poder Terceiros
						    nDesc:=(cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR
						    nDesc:=iif(nDesc>0,(nDesc/(cAliasSD2)->D2_QUANT)*IIf(nSldDevAux==0,1,nSldDevAux),0)
						    AAdd( aLinha, { "D1_VUNIT"  ,((((cAliasSD2)->D2_TOTAL+(cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR))-(cAliasSD2)->D2_VALDEV)/IIf(nSldDevAux==0,1,nSldDevAux), Nil })
					    Else  					// Nf com Controle Poder Terceiros
						    nDesc:=(cAliasSD2)->D2_DESCON+(cAliasSD2)->D2_DESCZFR
						    nDesc:=iif(nDesc>0,(nDesc/aSaldoTerc[6])*nSldDev,0)
							AAdd( aLinha, { "D1_VUNIT"  , NoRound(((aSaldoTerc[5]+nDesc)-aSaldoTerc[4])/nSldDev,TamSX3("D2_PRCVEN")[2]), Nil })
					    EndIf

	 					AAdd( aLinha, { "D1_TOTAL"  , A410Arred(aLinha[2][2]*aLinha[3][2],"D1_TOTAL"),Nil } )
						AAdd( aLinha, { "D1_VALDESC", nDesc , Nil } )
						AAdd( aLinha, { "D1_VALFRE" , A410Arred(((cAliasSD2)->D2_VALFRE/(cAliasSD2)->D2_QUANT)*nSldDev,"D1_VALFRE"),Nil } )
						AAdd( aLinha, { "D1_SEGURO" , A410Arred(((cAliasSD2)->D2_SEGURO/(cAliasSD2)->D2_QUANT)*nSldDev,"D1_SEGURO"),Nil } )
						AAdd( aLinha, { "D1_DESPESA" , A410Arred(((cAliasSD2)->D2_DESPESA/(cAliasSD2)->D2_QUANT)*nSldDev,"D1_DESPESA"),Nil } )
					EndIf
					AAdd( aLinha, { "D1_IPI"    , (cAliasSD2)->D2_IPI    , Nil } )
					AAdd( aLinha, { "D1_LOCAL"  , (cAliasSD2)->D2_LOCAL  , Nil } )
					AAdd( aLinha, { "D1_TES" 	, (cAliasSF4)->F4_CODIGO , Nil } )
					
					If ("000"$AllTrim((cAliasSF4)->F4_CF) .Or. "999"$AllTrim((cAliasSF4)->F4_CF))
						cCfop := AllTrim((cAliasSF4)->F4_CF)
					Else
                        cCfop := SubStr("123",At(SubStr((cAliasSD2)->D2_CF,1,1),"567"),1)+SubStr((cAliasSD2)->D2_CF,2)
						//Verifica se existe CFOP equivalente considerando a CFOP do documento de saida
						SX5->( dbSetOrder(1) )
						If !SX5->(MsSeek( cFilSX5 + "13" + cCfop ))
							cCfop := AllTrim((cAliasSF4)->F4_CF)
						EndIf
					EndIf
					AAdd( aLinha, { "D1_CF"		, cCfop, Nil } )
					AAdd( aLinha, { "D1_UM"     , (cAliasSD2)->D2_UM , Nil } )
                    If (nTpCtlBN != 0)
     					AAdd( aLinha, { "D1_OP" 	, A103OPBen(cAliasSD2, nTpCtlBN) , Nil } )
                    EndIf
					If Rastro((cAliasSD2)->D2_COD) .And. ((cAliasSF4)->F4_ESTOQUE == "S" .Or. (FindFunction("ContATer") .And. ContATer(cAliasSF4)))
						AAdd( aLinha, { "D1_LOTECTL", (cAliasSD2)->D2_LOTECTL, ".T." } )
						If (cAliasSD2)->D2_ORIGLAN == "LO"
							If Rastro((cAliasSD2)->D2_COD,"L") .AND. !Empty((cAliasSD2)->D2_NUMLOTE)
								AAdd( aLinha, { "D1_NUMLOTE", Nil , ".T." } )
							Else
								AAdd( aLinha, { "D1_NUMLOTE", (cAliasSD2)->D2_NUMLOTE, ".T." } )
							EndIf
						Else
							AAdd( aLinha, { "D1_NUMLOTE", (cAliasSD2)->D2_NUMLOTE, ".T." } )
						EndIf

						AAdd( aLinha, { "D1_DTVALID", (cAliasSD2)->D2_DTVALID, ".T." } )
						AAdd( aLinha, { "D1_POTENCI", (cAliasSD2)->D2_POTENCI, ".T." } )
						SB8->(dbSetOrder(3)) // FILIAL+PRODUTO+LOCAL+LOTECTL+NUMLOTE+B8_DTVALID
						If 	SB8->(MsSeek(xFilial("SB8")+(cAliasSD2)->D2_COD + (cAliasSD2)->D2_LOCAL + (cAliasSD2)->D2_LOTECTL + (cAliasSD2)->D2_NUMLOTE))
								AAdd( aLinha, { "D1_DFABRIC", SB8->B8_DFABRIC, ".T." } )
						Endif
					EndIf
					cNFORI  := (cAliasSD2)->D2_DOC
					cSERIORI:= (cAliasSD2)->D2_SERIE
					cITEMORI:= (cAliasSD2)->D2_ITEM
					If cTipo == "D"
						SF4->(dbSetOrder(1))
						If SF4->(MsSeek(xFilial("SF4")+(cAliasSD2)->D2_TES)) .And. SF4->F4_PODER3$"D|R"
							If SF4->(MsSeek(xFilial("SF4")+(cAliasSF4)->F4_CODIGO)) .And. SF4->F4_PODER3 == "N"
								cNFORI  := ""
								cSERIORI:= ""
								cITEMORI:= ""
								Help(" ",1,"A100NOTES")
							EndIf
							If SF4->(MsSeek(xFilial("SF4")+(cAliasSF4)->F4_CODIGO)) .And. SF4->F4_PODER3 == "R"
								cNFORI  := ""
								cSERIORI:= ""
								cITEMORI:= ""
							    Help(" ",1,"A103TESNFD")
							EndIf
						EndIf
					EndIf
					AAdd( aLinha, { "D1_NFORI"  , cNFORI   			      , Nil } )
					AAdd( aLinha, { "D1_SERIORI", cSERIORI  		      , Nil } )
					AAdd( aLinha, { "D1_ITEMORI", cITEMORI   			  , Nil } )
					AAdd( aLinha, { "D1_ICMSRET", ((cAliasSD2)->D2_ICMSRET / (cAliasSD2)->D2_QUANT )*nSldDev , Nil })
					If (cAliasSF4)->F4_PODER3=="D"
						AAdd( aLinha, { "D1_IDENTB6", (cAliasSD2)->D2_NUMSEQ, Nil } )
					Endif

					//ObtÈm o valor do Acrescimo Financeiro na Nota de Origem e faz o rateio //
					If (cAliasSD2)->D2_VALACRS >0
						AAdd( aLinha, { "D1_VALACRS", ((cAliasSD2)->D2_VALACRS / (cAliasSD2)->D2_QUANT )*nSldDev , Nil })
					Endif

					If ExistBlock("MT103LDV")
						aLinha := ExecBlock("MT103LDV",.F.,.F.,{aLinha,cAliasSD2})
					EndIf

					If !(Empty((cAliasSD2)->D2_CCUSTO ))
						AAdd( aLinha, { "D1_CC"  , (cAliasSD2)->D2_CCUSTO  , Nil } )
					EndIf

					If !(Empty((cAliasSD2)->D2_CONTA ))
						AAdd( aLinha, { "D1_CONTA"  , (cAliasSD2)->D2_CONTA  , Nil } )
					EndIf 

					If !(Empty((cAliasSD2)->D2_ITEMCC )) 
						AAdd( aLinha, { "D1_ITEMCTA"  , (cAliasSD2)->D2_ITEMCC  , Nil } )
					EndIf

					If !(Empty((cAliasSD2)->D2_CLVL )) 
						AAdd( aLinha, { "D1_CLVL"  , (cAliasSD2)->D2_CLVL  , Nil } )
					EndIf

					If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
						cIndPres	:= GetAdvFVal("SC5","C5_INDPRES",xFilial("SC5") + (cAliasSD2)->D2_CLIENTE + (cAliasSD2)->D2_LOJA + (cAliasSD2)->D2_PEDIDO,3) 
						cCodA1U		:= GetAdvFVal("SC5","C5_CODA1U",xFilial("SC5") + (cAliasSD2)->D2_CLIENTE + (cAliasSD2)->D2_LOJA + (cAliasSD2)->D2_PEDIDO,3) 
					Endif

					AAdd( aLinha, { "D1RECNO", (cAliasSD2)->SD2RECNO, Nil } )

					AAdd( aItens, aLinha)
				EndIf
			Else
				lHelpTes := .F.
			EndIf
		Else
			nHpP3 := 1
		Endif
		DbSelectArea(cAliasSD2)
		dbSkip()
	EndDo

	(cAliasSD2)->(DbCloseArea())

	// Verifica se nenhum item foi processado
	If !lDevCode
		lDevolucao := .F.
	EndIf
	DbSelectArea("SD2")

EndIf

Return lDevolucao

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103ShowOP≥ Autor ≥Alexandre Inacio Lemes≥ Data ≥ 19/07/2001≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Consulta OP em Aberto atraves da tecla F4                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103ShowOP()      				                          ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103ShowOp()

Local oDlg, nOAT
Local nHdl    := GetFocus()
Local nOpt1   := 0
Local aArray  := {}
Local cAlias  := Alias()
Local nOrder  := IndexOrd()
Local nRecno  := Recno()
Local cCampo  := ReadVar()
Local cPicture:= PesqPictQt("C2_QUANT",16)
Local nOrdSC2 := SC2->(IndexOrd())
Local cMascara:= SuperGetMV("MV_MASCGRD")
Local nTamRef := Val(Substr(cMascara,1,2))
Local nPosOp  := GetPosSD1('D1_OP')
Local nPosCod := GetPosSD1('D1_COD')
Local cProdRef:= IIf(MatGrdPrrf(aCols[n][nPosCod]),Alltrim(aCols[n][nPosCod]),aCols[n][nPosCod])
Local bSavKeyF4 := SetKey(VK_F4,Nil)
Local bSavKeyF5 := SetKey(VK_F5,Nil)
Local bSavKeyF6 := SetKey(VK_F6,Nil)
Local bSavKeyF7 := SetKey(VK_F7,Nil)
Local bSavKeyF8 := SetKey(VK_F8,Nil)
Local bSavKeyF9 := SetKey(VK_F9,Nil)
Local bSavKeyF10:= SetKey(VK_F10,Nil)
Local bSavKeyF11:= SetKey(VK_F11,Nil)
Local lContinua	:= .T.

//Verifica se o produto e' referencia (Grade)
If MatGrdPrrf(aCols[n][nPosCod])
	nTamRef	 := Val(Substr(cMascara,1,2))
	cProdRef    := Alltrim(aCols[n][nPosCod])
Else
	nTamRef	 := Len(SC2->C2_PRODUTO)
	cProdRef    := aCols[n][nPosCod]
EndIf

If cCampo <> "M->D1_OP"
	SetKey(VK_F4,bSavKeyF4)
	SetKey(VK_F5,bSavKeyF5)
	SetKey(VK_F6,bSavKeyF6)
	SetKey(VK_F7,bSavKeyF7)
	SetKey(VK_F8,bSavKeyF8)
	SetKey(VK_F9,bSavKeyF9)
	SetKey(VK_F10,bSavKeyF10)
	SetKey(VK_F11,bSavKeyF11)
	lContinua := .F.
EndIf

If lContinua
	DbSelectArea("SC2")
	DbSetOrder(2)
	If MsSeek(xFilial("SC2")+cProdRef)
		While !Eof() .And. C2_FILIAL+Substr(C2_PRODUTO,1, nTamRef) == xFilial("SC2")+cProdRef
			If Empty(C2_DATRF)
				AADD(aArray,{C2_NUM,C2_ITEM,C2_SEQUEN,C2_PRODUTO,DTOC(C2_DATPRI),DTOC(C2_DATPRF),Transform(aSC2Sld(),cPicture),C2_ITEMGRD})
			EndIf
			dbSkip()
		EndDo
	EndIf

	If !Empty(aArray)

		DEFINE MSDIALOG oDlg TITLE OemToAnsi(STR0100) From 03,0 To 17,50 OF oMainWnd //"OPs em Aberto deste Produto"
		@ 0.5,  0 TO 7, 20.0 OF oDlg
		@ 1,.7 LISTBOX oQual VAR cVar Fields HEADER OemToAnsi(STR0101),OemToAnsi(STR0102),OemToAnsi(STR0103),OemToAnsi(STR0063),OemToAnsi(STR0104),OemToAnsi(STR0105),OemToAnsi(STR0106),OemToAnsi(STR0107)  SIZE 150,80 ON DBLCLICK (nOpt1 := 1,oDlg:End()) //"Numero"###"Item"###"Sequencia"###"Produto"###"Dt. Prev. Inicio"###"Dt. Prev. Fim"###"Saldo"###" It. Grade"
		oQual:SetArray(aArray)
		oQual:bLine := { || {aArray[oQual:nAT][1],aArray[oQual:nAT][2],aArray[oQual:nAT][3],aArray[oQual:nAT][4],aArray[oQual:nAT][5],aArray[oQual:nAT][6],aArray[oQual:nAT][7],aArray[oQual:nAT][8]}}
		DEFINE SBUTTON FROM 10  ,166  TYPE 1 ACTION (nOpt1 := 1,oDlg:End()) ENABLE OF oDlg
		DEFINE SBUTTON FROM 22.5,166  TYPE 2 ACTION oDlg:End() ENABLE OF oDlg
		ACTIVATE MSDIALOG oDlg VALID (nOAT := oQual:nAT, .T.)
		If nOpt1 == 1
			M->D1_OP :=aArray[nOAT][1]+aArray[nOAT][2]+aArray[nOAT][3]+aArray[nOAT][8]
			If nPosOp > 0
				aCols[n][nPosOp] := M->D1_OP
			EndIf
		EndIf
		SetFocus(nHdl)
	Else
		Help(" ",1,"A250NAOOP")
	EndIf
	DbSelectArea(cAlias)
	DbSetOrder(nOrder)
	MsGoto(nRecno)
	SC2->(DbSetOrder(nOrdSC2))
	CheckSx3("D1_OP")
	SetKey(VK_F4,bSavKeyF4)
	SetKey(VK_F5,bSavKeyF5)
	SetKey(VK_F6,bSavKeyF6)
	SetKey(VK_F7,bSavKeyF7)
	SetKey(VK_F8,bSavKeyF8)
	SetKey(VK_F9,bSavKeyF9)
	SetKey(VK_F10,bSavKeyF10)
	SetKey(VK_F11,bSavKeyF11)
EndIf
Return Nil

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103AtuSE2≥ Autor ≥ Edson Maricate        ≥ Data ≥11.10.2001 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥Rotina de integracao com o modulo financeiro                 ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpN1: Codigo de operacao                                    ≥±±
±±≥          ≥       [1] Inclusao de Titulos                               ≥±±
±±≥          ≥       [2] Exclusao de Titulos                               ≥±±
±±≥          ≥ExpA2: Array com os recnos dos titulos financeiros. Utilizado≥±±
±±≥          ≥       somente na exclusao                                   ≥±±
±±≥          ≥ExpA3: AHeader dos titulos financeiros                       ≥±±
±±≥          ≥ExpA4: ACols dos titulos financeiro                          ≥±±
±±≥          ≥ExpA5: AHeader das multiplas naturezas                       ≥±±
±±≥          ≥ExpA2: ACols das multiplas naturezas                         ≥±±
±±≥          ≥ExpC6: Fornecedor dos ISS                                    ≥±±
±±≥          ≥ExpC7: Loja do ISS                                           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥Nenhum                                                       ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Esta rotina tem como objetivo efetuar a integracao entre o   ≥±±
±±≥          ≥documento de entrada e os titulos financeiros.               ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/

Function A103AtuSE2(nOpcA,aRecSE2,aHeadSE2,aColsSE2,aHeadSEV,aColsSEV,cFornIss,cLojaIss,cDirf,cCodRet,cModRetPIS,nIndexSE2,aSEZ,dVencIss,cMdRtISS,nTaxa,lTxNeg,aRecGerSE2,cA2FRETISS,cB1FRETISS,aMultas,lRatLiq,lRatImp,aCodR,cRecIss,lPisCofImp,aTitImp,lIssImp,lTemDocs,aDadPLS,aParcTrGen,aRecSEV,cIdsTrGen,cF4FRETISS)

Local aArea     := GetArea()
Local aAreaSA2  := SA2->(GetArea())
Local aAreaSE2  := {}
Local aAreaAt   := {}
Local aRetIrrf  := {}
Local aProp     := {}
Local aCtbRet   := {0,0,0}
Local aCTBEnt   := CTBEntArr()
Local aDadosRet := {0,0,0,0,0,0,0,0,0,0}
Local aTGCalc   := {}
Local aTGRet    := {}
Local aTGCalcRec:= {}
Local aImpCalc  := {}
Local aImpos    := {}
Local cFilSE2	:= xFilial("SE2")
Local cPrefixo  := SF1->F1_PREFIXO
Local cNatureza := MaFisRet(,"NF_NATUREZA")
Local cPrefOri  := ""
Local cNumOri   := ""
Local cParcOri  := ""
Local cTipoOri  := ""
Local cCfOri    := ""
Local cLojaOri  := ""
Local cForLoja	:= ""
Local cAplVlMn  := "1"
Local cNumTitTG := ""
Local cChaveFK7 := ""
Local cHistRec  := ""
Local cPreOr    := ""
Local cNumOr    := ""
Local cParOr    := ""
Local cTipOr    := ""
Local cForOr    := ""
Local cLojOr    := ""
Local nPParcela := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_PARCELA"})
Local nPVencto  := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_VENCTO"})
Local nPValor   := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_VALOR"})
Local nPIRRF    := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_IRRF"})
Local nPISS     := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_ISS"})
Local nPINSS    := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_INSS"})
Local nPPIS     := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_PIS"})
Local nPCOFINS  := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_COFINS"})
Local nPCSLL    := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_CSLL"})
Local nPSEST    := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_SEST"})
Local nPFETHAB  := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_FETHAB"})
Local nPFABOV	:= aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_FABOV"})
Local nPFACS    := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_FACS"})
Local nPIMA     := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_IMA"})
Local nPFAMAD   := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_FAMAD"})
Local nPBTISS   := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_BTRISS"})
Local nSEST		:= 0
Local nBaseDup  := 0
Local nVlCruz   := MaFisRet(,"NF_BASEDUP")
Local nLoop     := 0
Local nX        := 0
Local nY        := 0
Local nZ        := 0
Local nW        := 0
Local nK        := 0
Local nRateio   := 0
Local nRateioSEZ:= 0
Local nMaxFor   := IIF(aColsSE2==Nil,0,Len(aColsSE2))
Local nRetOriPIS := 0
Local nRetOriCOF := 0
Local nRetOriCSLL:= 0
Local nValor    := 0
Local nValTot   := 0
Local nBasePis  := MaFisRet(,"NF_BASEPIS")
Local nBaseCof  := MaFisRet(,"NF_BASECOF")
Local nBaseCsl  := MaFisRet(,"NF_BASECSL")
Local nBaseIrf  := MaFisRet(,"NF_BASEIRR")
Local nBaseIns	:= MaFisRet(,"NF_BASEINS")
Local nSaldoIrf := nBaseIrf
Local nSaldoPis := nBasePis
Local nSaldoCof := nBaseCof
Local nSaldoCsl := nBaseCsl
Local nSaldoIns := nBaseIns
Local nSaldoProp:= 0
Local nProp     := 0
Local nVlRetPIS := 0
Local nVlRetCOF := 0
Local nVlRetCSLL:= 0
Local nVlConvPis:= 0
Local nVlConvCof:= 0
Local nVlConvCsl:= 0
Local nSaldoMult:= 0
Local nSaldoBoni:= 0
Local nBaixaMult:= 0
Local nPosEntAd := 0 
Local nValMinRet:= GetNewPar( "MV_VL10925", 0 )
Local nMinPub := SuperGetMv( "MV_VLMPUB",.F.,0 )
Local nNewMinPcc:= SuperGetMv("MV_VL13137",.F.,0)
Local nContTg   := 0
Local lMulta    := .F.
Local lVisDirf  := SuperGetMv("MV_VISDIRF",.F.,"2") == "1"
Local lRestValImp	:= .F.
Local lRetParc		:= .T.
Local lTrbGen	 	:= Iif(FindFunction("ChkTrbGen"),ChkTrbGen("SD1", "D1_IDTRIB"),.F.) // Verificacao se pode ou nao utilizar tributos genericos
Local lTrbGenFin    := lTrbGen .And. FindFunction("FINCalImp") .AND. FindFunction("FINGRVFK7") .And. FindFunction("FGrvImpFi")
Local lIRBaixa      := IIf(cPaisLoc == "BRA", SA2->A2_CALCIRF == "2", .F.)
Local nBaseIss      := MaFisRet(,"NF_BASEISS")
Local nSaldoIss     := nBaseIss
Local cMRetISS		:= GetNewPar("MV_MRETISS","1")
Local nValFet   	:= MaFisRet(,"NF_VALFET")
Local nValFab   	:= MaFisRet(,"NF_VALFAB")
Local nValFac   	:= MaFisRet(,"NF_VALFAC")
Local nFundesa  	:= MaFisRet(,"NF_VALFUND")
Local nValFase		:= MaFisRet(,"NF_VALFASE")
Local cForMinISS 	:= GetNewPar("MV_FMINISS","1")
Local nValMinISS    := IIF(cForMinISS == '1', SuperGetMv("MV_VRETISS",.F., 0), SuperGetMv("MV_VBASISS",.F., 0) )
Local lMT103ISS     := ExistBlock("MT103ISS")
Local aMT103ISS     := {}
Local nValBTISS     := 0	// ISS bi-tributado pelo CEPOM
Local cCodISS       := MaFisRet(1,"IT_CODISS") // Codigo do ISS
Local lBtrISS       := SE2->(ColumnPos("E2_BTRISS")) > 0 .And. SE2->(ColumnPos("E2_VRETBIS")) > 0 .And. SE2->(ColumnPos("E2_CODSERV")) > 0  .And. nPBTISS > 0
Local nInss := 0
Local aDadosImp	:= Array(3)
Local nVlRetIR 		:= SuperGetMV("MV_VLRETIR")
Local lPCCBaixa		:= SuperGetMv("MV_BX10925") == "1"
Local lISSNat		:= .T.
Local lRatPIS	:= SuperGetMV("MV_RATPIS",.F.,.T.)
Local lRatCOFINS:= SuperGetMV("MV_RATCOF",.F.,.T.)
Local lRatCSLL	:= SuperGetMV("MV_RATCSLL",.F.,.T.)
Local lRatIrf    := SuperGetMV("MV_RATIRRF",.F.,.F.)
Local lRatIss    := SuperGetMV("MV_RATISS",.F.,.F.)
Local lRatInss	:= SuperGetMV("MV_RATINSS",.F.,.F.)
Local lMulNats	:= SuperGetMv( "MV_MULNATS", .F., .F. )
Local aRetPCC	:= {.F.,0,0,0}
Local dRefPCC	:= CTOD("22/06/2015")
Local lGCTRet     := (GetNewPar( "MV_CNRETNF", "N" ) == "S")
Local nGCTRet     := 0
Local nGCTDesc    := 0
Local nGCTMult    := 0
Local nGCTBoni    := 0
Local aContra     := {}
Local nValInss		:= 0
Local lISSTes		:= SuperGetMv("MV_ISSRETD",.F.,.F.)
Local nValIrrf		:= 0
Local lIntALC		:= SuperGetMV("MV_FINCTAL") == "2"
Local cAprov		:= ""
Local lCondTp8 := .F.
Local aTP8 := {}
// V·riaveis para o c·lculo do CIDE
Local nValCIDE		:= MaFisRet(,"NF_VALCIDE")
Local lCIDE			:= nValCIDE > 0 .And. SuperGetMv("MV_FGCIDE",.T.,"2") == "2" // Define o fato gerador do imposto CIDE. 1 = Baixa ou 2 = Emiss„o
Local cForCIDE		:= PadR(SuperGetMV("MV_FORCIDE",.F.,""),Len( SE2->E2_FORNECE ))
Local nVencto	:= SuperGetMv("MV_VCPCCP",.T.,1)
Local dRef		:= dDatabase
Local lCalcIssBx 	:= IIF(lIsIssBx, IsIssBx("P"), SuperGetMv("MV_MRETISS",.F.,"1") == "2" )

//Parametros Titulo de PIS/COF / ISS importacao / FASE-MT
Local cForPisCof := ""
Local cLojaZero	 := ""
Local cPrefPis	 := SuperGetMV("MV_PREFPIS",.F.,"")
Local cPrefCof	 := SuperGetMV("MV_PREFCOF",.F.,"")
Local cNatPis	 := SuperGetMv("MV_PISIMP",.F.,"")
Local cNatCOF	 := SuperGetMv("MV_COFIMP",.F.,"")
Local aTit050	 := {}
Local cPrefISS	 := SuperGetMV("MV_PREFISS",.F.,"")
Local cNatISS	 := SuperGetMv("MV_ISSIMP",.F.,"")
Local cForIss	 := ""
Local lGrossIRRF := .F.
local nTamE2PREF := TamSX3("E2_PREFIXO")[1]
local nTamE2NUM  := TamSX3("E2_NUM")[1]
local nTamE2TIPO := TamSX3("E2_TIPO")[1]
local nTamE2FORN := TamSX3("E2_FORNECE")[1]
local nTamE2LOJA := TamSX3("E2_LOJA")[1]
Local nTamEzPerc := TamSX3("EZ_PERC")[2]
Local aBanco := {}
Local cPreFase	 := SuperGetMV("MV_PREFASE",.F.,"")
Local cNatFase	 := SuperGetMV("MV_FASEIMP",.F.,"")
Local cForFase	 := SuperGetMV("MV_FORFASE",.F.,"")
Local oSX1
Local aPergunte  := {}
Local nInssTot	 := 0
Local lRecalcIns	:= .F.
Local lRateio 		:= .F. 
Local cCdRetIRRt    := SuperGetMv("MV_RETIRRT",.T.,"3208")
Local nIRRateio		:= 0
Local aSobra		:= {}
Local nSobra		:= 0
Local nDecsE2		:= TAMSX3("E2_VALOR")[2]
Local cMVFinAlap	:= SuperGetMV("MV_FINALAP")
Local lPe100IR		:= ExistBlock("MT100IR")
Local lPe100INS  	:= ExistBlock("MT100INS")
Local lPe100PIS 	:= ExistBlock("MT100PIS")
Local lPe100COF 	:= ExistBlock("MT100COF")
Local lPe100CSL 	:= ExistBlock("MT100CSL")
Local lPe100FET 	:= ExistBlock("MT100FET")
Local lAliasCIN		:= AliasIndic("CIN")
Local aAUTOISS		:= &(GetNewPar("MV_AUTOISS",'{"","","",""}'))
Local cRateIcc      := ""
Local cTitPai       := ""
LOCAL aCount        := {0,0,0,0}
Local lHasIRR		:=.F.

//variaveis para retenÁ„o motor de tributos, Configurador de Tributos genÈricos
Local lPccMR		:=.F.
Local lIrfMR		:=.F.
Local lInsMR		:=.F.
Local lIssMR		:=.F.
Local lCidMR		:=.F.
Local lSestMR		:=.F.
Local lFunMR        :=.F.
Local lInsPMR       :=.F.
Local lFamadMR      :=.F.
Local lFethabMR     :=.F.
Local lFacsMR       :=.F.
Local lImaMR        :=.F.
Local lFabovMR      :=.F.
Local lVer640	    := .F.
Local lVer650	    := .F.
Local lVer660	    := .F.
Local lVer642	    := .F.
Local lVer955       := .F.
Local lVer950       := .F.
Local lVer641	    := .F.
Local lVer651	    := .F.
Local lVer65C	    := .F.
Local lVer65D	    := .F.

DEFAULT cModRetPIS	:= "1"
DEFAULT cMdRtISS	:= "1"
DEFAULT nTaxa		:= 0
DEFAULT lTxNeg	    := .F.
DEFAULT cA2FRETISS	:=	""
DEFAULT cB1FRETISS	:=	""
DEFAULT cF4FRETISS	:=  ""
DEFAULT aMultas     := {}
DEFAULT lRatLiq		:= .T.
DEFAULT lRatImp		:= .F.
DEFAULT aCodR		:= {}
DEFAULT cRecIss		:=	"1"
DEFAULT dVencIss	:= CtoD("")
DEFAULT lPisCofImp  := .F.
DEFAULT aTitImp     := {}
DEFAULT lISSImp     := .F.
DEFAULT lTemDocs    := .F.
DEFAULT aParcTrGen  := {}
DEFAULT cIdsTrGen	:= ""

PRIVATE nValFun		:= MaFisRet(,"NF_FUNRURAL")
PRIVATE nValINP         := 0
PRIVATE lMsErroAuto := .F.

nTamX3A2CD	:= Iif(nTamX3A2CD==0,TamSX3("A2_COD")[1],nTamX3A2CD)
nTamX3A2LJ	:= Iif(nTamX3A2LJ==0,TamSX3("A2_LOJA")[1],nTamX3A2LJ)

cForPisCof 	:= PadR(SuperGetMV("MV_UNIAO"),nTamX3A2CD)
cLojaZero	:= PadR("00", nTamX3A2LJ, "0" )
cForIss	 	:= PadR(SuperGetMV("MV_MUNIC"),nTamX3A2CD)

__lEmpPub := IsEmpPub()

//Valor do INSS Patronal
If cPaisLoc == "BRA"
	If SD1->(ColumnPos('D1_VALINP')) > 0 
		nValINP := MaFisRet(,"NF_VALINP")
	EndIf
EndIf

//Verifica se È importaÁ„o de serviÁo, se existe a referÍncia NF_GROSSIR e se est· com alguma opÁ„o de Gross UP do IRRF, se sim o valor do IRRF n„o poder· ser descontado do tÌtulo principal.
lGrossIRRF := lISSImp .AND. !Empty(MaFisScan("NF_GROSSIR",.F.)) .AND. MaFisRet(,"NF_GROSSIR") $ "1/2/3"

//Indica se o tratamento de valor minimo para retencao (R$ 5.000,00) deve ser aplicado:
//Controle pela variavel cAplVlMn, onde :
//1 = Aplica o valor minimo
//2 = Nao aplica o valor minimo
//Quando o tratamento da retencao for pela emissao, sera forcada a retencao em cada
//aquisicao. Quando o tratamento da retencao for pela baixa, o financeiro ira usar o
//campo E2_APLVLMN para identificar se utilizara ou nao o valor minimo para retencao.
If MaFisRet(,"NF_PIS252") > 0 .Or. MaFisRet(,"NF_COF252") > 0
	If cModRetPis <> "3"
		// Forca a retencao sempre - Apenas para retencao na emissao do titulo
		cModRetPis := "2"
	Endif
	cAplVlMn := "2"
Endif

//Verifica se a Taxa da Moeda nao foi negociada
If NMOEDACOR != 1 .And. RecMoeda(M->dDemissao,NMOEDACOR) != nTaxa //se a taxa for diferente da cadastrada na dDataBase a moeda foi negociada
	lTxNeg := .T.                         //para poder gravar e calcular corretamente os titulos financeiros
EndIf

If !lTxNeg
	nTaxa := 0
EndIf

//Verifica o prefixo do titulo a ser gerado
If Empty(cPrefixo)
	cPrefixo := &(SuperGetMV("MV_2DUPREF"))
	cPrefixo += Space(Len(SE2->E2_PREFIXO) - Len(cPrefixo))
EndIf

If nOpcA == 1
	If mv_par06 == 1 
		lVer640 := VerPadrao("640")
		lVer650	:= VerPadrao("650")
		lVer660	:= VerPadrao("660")
		lVer642	:= VerPadrao("642")
		lVer955 := VerPadrao("955")
		lVer950 := VerPadrao("950")
		lVer641	:= VerPadrao("641")
		lVer651	:= VerPadrao("651")
		lVer65C	:= VerPadrao("65C")
		lVer65D	:= VerPadrao("65D")	
	EndIf
	//Calcula o total de multas e / ou bonificacoes de contrato
	AEval( aMultas, { |x| If( x[5] == "1", nSaldoMult += x[3], nSaldoBoni += x[3] ) } )

	lMulta := ( nSaldoMult > nSaldoBoni )

	If lMulta
		nSaldoMult := nSaldoMult - nSaldoBoni
	Else
		nSaldoBoni := nSaldoBoni - nSaldoMult
	EndIf

	CntProcGct(lGCTRet,,,,@nGCTRet,@nGCTDesc,@nGCTMult,@nGCTBoni,aContra)

	If lGCTRet //Calcula valor da retencao, desconto, multa e bonificaÁ„o de contrato pelo total de parcelas
		nGCTRet := nGCTRet/nMaxFor
		nGCTDesc := nGCTDesc/nMaxFor
		nGCTMult := nGCTMult/nMaxFor
		nGCTBoni := nGCTBoni/nMaxFor
	EndIf

	DbSelectArea("SED")
	DbSetOrder(1)
	MsSeek(xFilial("SED")+cNatureza)

	//Verifica se a natureza indica que deva ser calculado/retido o ISS
	lISSNAT := SED->ED_CALCISS <> "N" .Or. lISSTes

	//Calcula o valor total das duplicatas
	For nX := 1 To nMaxFor
		nBaseDup += aColsSE2[nX][nPValor]
		If nPIRRF > 0
			nValIrrf += aColsSE2[nX][nPIRRF]
		Else
			nValIrrf := 0
		EndIf
	Next nX
	
	nBaseDup -= nValFun
	nBaseDup -= nValFet
	nBaseDup -= nValFab
	nBaseDup -= nValFac
	
	//Calcula os percentuais de rateio do SEZ
    cRateIcc   := IIF( Len(aSEZ) > 0, "1", CriaVar("EV_RATEICC", .T.) )   //Identificador de Rateio por Centro de Custo
	nRateioSEZ := 0
	For nZ := 1 To Len(aSEZ)
		nRateioSEZ += aSEZ[nZ][5]
	Next nZ
	
	For nZ := 1 To Len(aSEZ)
		aSEZ[nZ][4] := NoRound(aSEZ[nZ][5]/nRateioSEZ,nTamEzPerc)
	Next nZ
	
	nRateioSEZ := 0
	
	For nZ := 1 To Len(aSEZ)
		nRateioSEZ += aSEZ[nZ][4]
		If nZ == Len(aSEZ)
			aSEZ[nZ][4] += 1-nRateioSEZ
		EndIf
	Next nZ
	
	//Efetua a gravacao dos titulos financeiros a pagar
	nValPis := 0
	nValCof := 0
	nValCsl := 0

	For nX := 1 to nMaxFor
		nValTot += aColsSE2[nX][nPValor]
	Next

	aProp := {}

	nSaldoProp := 1

	/*  lCondTp8 : Flag p/ determinar se os c·lculos foram efetuados com valores percentuais (E4_TIPO = 8).
		Se positivo, devo inverter os c·lculos para que n„o ocorra erro de arredondamento dos valores se forem
		utilizadas condiÁıes de pagamento com casas decimais.

		Ela ser· utilizada para os c·lculos das bases proporcionais de PIS, COFINS, CSLL, IR e INSS.

		O mesmo mecanismo È utilizado no financeiro para a geracao dos valores das duplicatas nestas condicoes.	*/

	If SE4->(MsSeek(xFilial("SE4")+cCondicao)) .And. SE4->E4_TIPO == "8"
		lCondTp8 := .T.
		aTP8 := ArrayTP8(SE4->E4_COND)
	EndIf

	For nX := 1 to nMaxFor
		If nX == nMaxFor
			nProp := nSaldoProp
		Else
			If lCondTp8 .And. Len(aTP8) >= nMaxFor
				nProp := NoRound(aTP8[nX][2], 8)
				nSaldoProp := ((nSaldoProp * 100) - nProp)
			Else
				nProp := Round(aColsSE2[nX][nPValor] / nValTot, 6)
				nSaldoProp -= nProp
			EndIf
		EndIf

		AAdd( aProp, nProp )
	Next nX
	
    // ------------------------------------------------------------------------------
    // Revis„o do Rateio do IRRF/PCC
    // Sistema verifica os par‚metros MV_RATPIS - MV_RATCOF - MV_RATCSLL - MV_RATIRRF
    // PorÈm, o utilizador pode DIGITAR ou acionar o BOT√O RAT.IMP. alterando a regra
    // ------------------------------------------------------------------------------
    IF LEN(aColsSE2) > 1
        AFILL(aCount,0)
        AEVAL(aColsSE2,{|E| aCount[idxIRR] += IF(EMPTY(E[nPIRRF]),0,1),;
                            aCount[idxPIS] += IF(EMPTY(E[nPPIS]),0,1),;
                            aCount[idxCOF] += IF(EMPTY(E[nPCOFINS]),0,1),;
                            aCount[idxCSL] += IF(EMPTY(E[nPCSll]),0,1)})
        lRatIRF    := (aCount[idxIRR] > 1)
        lRatPIS    := (aCount[idxPIS] > 1)
        lRatCOFINS := (aCount[idxCOF] > 1)
        lRatCSLL   := (aCount[idxCSL] > 1)

		//-- Fornecedor tipo "F" n„o carrega os impostos na grid para IR na baixa
		If lIRBaixa .And. SA2->A2_TIPO=="F" .And. aCount[idxIRR]==0
			lRatIRF:= SuperGetMV("MV_RATIRRF",.F.,.F.)//-- Considera conteudo do parametro
		EndIF
    ENDIF
    // ------------------------------------------------------------------------------

	//-- Identifica se ha IR para DIRF
	If aScan( aCodR, {|aX|aX[4]=="IRR"}) > 0 .And. aCodR[aScan( aCodR, {|aX|aX[4]=="IRR"})][3] == 1
		lHasIRR:=.T.
	EndIf

	For nX := 1 To nMaxFor
	    If aColsSE2[nX][nPValor] > 0
		  	RecLock("SE2",.T.)
			If cForMinISS == "1"
				//Atendimento ao DECRETO 5.052, DE 08/01/2004 para o municipio de ARARAS.
				//Mais especificamente o paragrafo unico do Art 2
				If (("2"$cA2FRETISS) .And. ("2"$cB1FRETISS)) .Or.  ("2"$cF4FRETISS)
					SE2->E2_FRETISS	:=	"2"
				Else
					SE2->E2_FRETISS	:=	"1"
				EndIf
			Else
				//Atendimento a Lei 3.968 de 23/12/2003 - Americana / SP
				//para alguns produtos, a retencao deve ocorrer apenas para valores maiores que R$ 3.000,00
				//como um mesmo fornecedor pode prestar mais de um tipo de servico (com minimo e sem minimo
				//de retencao, a configuracao e diferenciada. O default sera reter sempre.
				If (("1"$cA2FRETISS) .And. ("1"$cB1FRETISS)) .Or. ("1"$cF4FRETISS)
					SE2->E2_FRETISS	:=	"1"
				Else
					SE2->E2_FRETISS	:=	"2"
				EndIf
			Endif

			If SE2->E2_FRETISS == '1' // Valida Valor minimo
				If ( cForMinISS == "1" .AND. aColsSE2[nX][nPISS] <= nValMinISS ) .OR. (cForMinISS == "2" .AND. nBaseIss <= nValMinISS)
					aColsSE2[nX][nPISS] := 0
				EndIf
			EndIf

			aBanco := A020GetBnk(SA2->A2_COD,SA2->A2_LOJA)

			If lIntALC
				cAprov := FA050Aprov(nMoedaCor) //verifica se h· aprovador com os par‚metros novos MV_FINAPXX
				If Empty(cAprov)//caso n„o estiver configurado, verifica o par‚metro antigo
					cAprov := cMVFinAlap
				Endif
			Endif

			SE2->E2_FILIAL  := cFilSE2
			SE2->E2_PREFIXO := cPrefixo
			SE2->E2_NUM     := cNFiscal
			SE2->E2_TIPO    := MVNOTAFIS
			SE2->E2_NATUREZ := cNatureza
			SE2->E2_EMISSAO := dDEmissao
			SE2->E2_EMIS1   := SF1->F1_DTDIGIT
			SE2->E2_FORNECE := SA2->A2_COD
			SE2->E2_LOJA    := SA2->A2_LOJA
			SE2->E2_NOMFOR  := SA2->A2_NREDUZ
			SE2->E2_FORBCO  := aBanco[1]
			SE2->E2_FORAGE  := aBanco[2]
			SE2->E2_FAGEDV  := aBanco[3]
			SE2->E2_FORCTA  := aBanco[4]
			SE2->E2_FCTADV  := aBanco[5]
			SE2->E2_MOEDA   := nMoedaCor
			SE2->E2_TXMOEDA := nTaxa
			SE2->E2_LA      := "N"
			If mv_par06 == 1 .And. (lVer640 .Or. lVer650 .Or. lVer660 .Or. lVer642 .Or. lVer955 .Or. lVer950 .Or. lVer641 .Or. lVer651 .Or. lVer65C .Or. lVer65D)
				SE2->E2_LA      := "S"
			EndIf
			SE2->E2_PARCELA := aColsSE2[nX][nPParcela]
			SE2->E2_VENCORI := aColsSE2[nX][nPVencto]
			SE2->E2_VENCTO  := aColsSE2[nX][nPVencto]
			SE2->E2_VENCREA := DataValida(aColsSE2[nX][nPVencto],.T.)
			SE2->E2_CODAPRO := cAprov
			SE2->E2_FORMPAG := SA2->A2_FORMPAG
			SE2->E2_FORBCO  := aBanco[1]
			SE2->E2_FORAGE  := aBanco[2]
			SE2->E2_FAGEDV  := aBanco[3]
			SE2->E2_FORCTA  := aBanco[4]
			SE2->E2_FCTADV  := aBanco[5]

			//verificacao SIGAPLS
			if lPLSMT103
				PLSMT103(2)
			endIf

			//SE FOR INSS Atualiza E2_RETINS
			If Alltrim(cNatureza) == "INSS"
			 	IF ( ALLTRIM(SA2->A2_TIPO)) == "J"
					SE2->E2_RETINS := PADR(SuperGetmv("MV_RETINPJ"),TAMSX3("E2_RETINS")[1])
				else
					SE2->E2_RETINS:= PADR(SuperGetmv("MV_RETINPF"),TAMSX3("E2_RETINS")[1])
				EndIF
			EndIf
			
			//Modo de Retencao de ISS - Municipio de Sao Bernardo do Campo
			//1 = Retencao Normal
			//2 = Retencao por Base
			SE2->E2_MDRTISS := cMdRtISS

			//Implementacao do SEST/SENAT
			If nPSEST > 0
				nSEST := SE2->E2_SEST := aColsSE2[nX][nPSEST]
			Endif

			//Indica se o tratamento de valor minimo para retencao (R$ 5.000,00) deve ser aplicado:
			//1 = Aplica o valor minimo
			//2 = Nao aplica o valor minimo
			SE2->E2_APLVLMN := cAplVlMn

			//Grava a filial de origem quando existir o campo no SE2
			SE2->E2_FILORIG := Iif(Empty(CriaVar("E2_FILORIG",.T.)),cFilAnt,CriaVar("E2_FILORIG",.T.))

			lRetParc := .T.
			If lVisDirf .And. aScan( aCodR, {|aX|aX[4]$"IRR,ISS,CSL,COF,PIS"})>0 .And. (aColsSE2[nX][nPIRRF] > 0 .Or. aColsSE2[nX][nPCSLL] > 0 .Or. aColsSE2[nX][nPCOFINS] > 0 .Or. aColsSE2[nX][nPPIS] > 0)
				IF aScan( aCodR, {|aX|aX[4]=="IRR"}) > 0 .And. aColsSE2[nX][nPIRRF] > 0 .And. aCodR[aScan( aCodR, {|aX|aX[4]=="IRR"})][3] == 1
					cCodRet	:= aCodR[aScan( aCodR, {|aX|aX[4]=="IRR"})][2]
					cDirf	:= "1"
				ELSEIF aScan( aCodR, {|aX|aX[4]=="ISS"}) > 0 .And. aColsSE2[nX][nPISS] > 0 .And. aCodR[aScan( aCodR, {|aX|aX[4]=="ISS"})][3] == 1
					cCodRet	:= aCodR[aScan( aCodR, {|aX|aX[4]=="ISS"})][2]
					cDirf	:= "1"
				ELSEIF aScan( aCodR, {|aX|aX[4]=="CSL"}) > 0 .And. aColsSE2[nX][nPCSLL] > 0 .And. aCodR[aScan( aCodR, {|aX|aX[4]=="CSL"})][3] == 1
					cCodRet	:= aCodR[aScan( aCodR, {|aX|aX[4]=="CSL"})][2]
					cDirf	:= "1"
				ELSEIF aScan( aCodR, {|aX|aX[4]=="COF"}) > 0 .And. aColsSE2[nX][nPCOFINS] > 0 .And. aCodR[aScan( aCodR, {|aX|aX[4]=="COF"})][3] == 1
					cCodRet	:= aCodR[aScan( aCodR, {|aX|aX[4]=="COF"})][2]
					cDirf	:= "1"
				ELSEIF aScan( aCodR, {|aX|aX[4]=="PIS"}) > 0 .And. aColsSE2[nX][nPPIS] > 0 .And. aCodR[aScan( aCodR, {|aX|aX[4]=="PIS"})][3] == 1
					cCodRet	:= aCodR[aScan( aCodR, {|aX|aX[4]=="PIS"})][2]
					cDirf	:= "1"
				ENDIF
			ElseIf l103Auto .And. aScan( aCodR, {|aX|aX[4]=="..."}) > 0						// Tratamento para quando for informado o array de codigos de retencao via rotina automatica com a referencia generica "..."
				cDirf	:=	AllTrim( Str( aCodR[aScan( aCodR, {|aX|aX[4]=="..."})][3] ) )	// seja gravado este codigo de retencao no titulo NF como e feito no padrao, caso contrario nao iria gravar
				cCodRet:=	aCodR[aScan( aCodR, {|aX|aX[4]=="..."})][2]
			EndIf

			//Valida se o codigo de retenÁ„o informado aplica o rateio de IR Aluguel 
			If oRatIRF <> NIL
				If Alltrim(cCodRet) $ cCdRetIRRt
					If !Empty(oRatIRF:aRatIRF) .And. Len(oRatIRF:aRatIRF) > 1
						oRatIRF:SetIRBaixa(lIRBaixa)
						oRatIRF:CalcRatIr()
						//Verifica existencia da propriedade nTitImp
						If AttIsMemberOf(oRatIrf , "nTitImp") 
							nValIrrf := oRatIRF:nTitImp
						Else
							nValIrrgf := 0
							aEval(oRatIRF:aRatIRF,{|x| nValIrrf += x[6]})
						EndIf
						If nX == 1
							aSobra := Array(Len(oRatIRF:aRatIRF))
							For nY := 1 to Len(aSobra)
								aSobra[nY] := oRatIRF:aRatIRF[nY][6]
							Next nY 
						EndIf	
						
						If nX == nMaxFor
							nValIrrf := nValIrrf - nIRRateio
							For nY := 1 to Len(oRatIRF:aRatIRF)
								oRatIRF:aRatIRF[nY][6] := aSobra[nY]
							Next nY	
						Else
							nValIrrf := Round(nValIrrf/nMaxFor,nDecsE2)		
							nIRRateio += nValIrrf
							//ProporcionalizaÁ„o entre as duplicatas
							For nY := 1 to Len(oRatIRF:aRatIRF)
								nSobra := Round(oRatIRF:aRatIRF[nY][6]/nMaxFor,nDecsE2)
								oRatIRF:aRatIRF[nY][6] := nSobra
								aSobra[nY] -= nSobra
							Next nY
						EndIf

						aColsSE2[nX][nPIRRF] := nValIrrf
						lRateio := .T.
					Endif	 
				EndIf    
			EndIf	

			//Verifica os impostos dos titulos financeiros
			If cPaisLoc == "BRA"
				SE2->E2_IRRF    := aColsSE2[nX][nPIRRF]

				//Gravar base IRPF
				//Proporcionalizacao da base do PIS pela duplicata
				If nX == nMaxFor
					SE2->E2_BASEIRF := nSaldoIrf
				Else
					If lCondTp8
						SE2->E2_BASEIRF := ((nBaseIrf / 100) * aProp[nX])
					ElseIf !lRatIrf
						If nX == 1
                     		SE2->E2_BASEIRF := nBaseIrf
                    	EndIf
					Else
						SE2->E2_BASEIRF := nBaseIrf * aProp[nX]
					EndIf

					nSaldoIrf -= SE2->E2_BASEIRF
				EndIf

				If SE2->E2_IRRF >= nVlRetIR .OR. nValIrrf >= nVlRetIR
					RecLock("SF1",.F.)
				    SF1->F1_VALIRF := nValIrrf
					SF1->( MsUnlock() )
				Endif

				If SubStr( cRecIss,1,1 )<>"1" .And. lISSNAT
					SE2->E2_ISS     := aColsSE2[nX][nPISS]
					If cFornIss <> Nil .And. cLojaIss <> Nil .And. aColsSE2[nX][nPISS] > 0
						If lMT103ISS
							aMT103ISS	:=	ExecBlock( "MT103ISS" , .F. , .F. , { cFornIss , cLojaIss , cDirf , cCodRet , dVencIss })
							If Len( aMT103ISS )==5
								cFornIss	:=	aMT103ISS[1]
								cLojaIss	:=	aMT103ISS[2]
								cDirf		:=	aMT103ISS[3]
								cCodRet		:=	aMT103ISS[4]
								dVencIss	:=	aMT103ISS[5]
							EndIf
						EndIf

						SE2->E2_FORNISS := cFornIss
						SE2->E2_LOJAISS := cLojaIss

						If nX == nMaxFor
							SE2->E2_BASEISS := nSaldoIss
						Else
							If lCondTp8
								SE2->E2_BASEISS := ((nBaseIss / 100) * aProp[nX])
							ElseIf !lRatIss
								If nX == 1
									SE2->E2_BASEISS := nBaseIss
								EndIf
							Else
								SE2->E2_BASEISS := nBaseIss * aProp[nX]
							EndIf
							nSaldoIss -= SE2->E2_BASEISS
						Endif

						If dVencIss <> Nil .And. ValType(dVencIss) == "D"
							SE2->E2_VENCISS := dVencIss
						EndIf
					Endif
				EndIf

				If lBtrISS
					SE2->E2_BTRISS  := aColsSE2[nX][nPBTISS] // ISS bi-tributado pelo CEPOM
					SE2->E2_VRETBIS := aColsSE2[nX][nPBTISS] // Como so estamos tratando pela emissao, estou gravando diretamente o que foi calculado
					nValBTISS       := aColsSE2[nX][nPBTISS]
					// Aqui estamos gravando o codigo do ISS pois o Financeiro necessita dele para buscar o fornecedor do ISS
					// No Futuro devemos ter outra forma de configurar essa informacao, por isso hoje so estamos preenchendo na sistuacao da bi-tributacao
					// nas demais situacoes ele continua buscando do MV_MUNIC
					SE2->E2_CODSERV := cCodISS
				EndIf

				//Gravacao dos codigos de receita conforme selecionado na aba impostos
				If aScan( aCodR, {|aX|aX[4]=="PIS"})>0
					SE2->E2_CODRPIS  := aCodR[aScan( aCodR, {|aX|aX[4]=="PIS"})][2]
				EndIf
				If aScan( aCodR, {|aX|aX[4]=="COF"})>0
					SE2->E2_CODRCOF  := aCodR[aScan( aCodR, {|aX|aX[4]=="COF"})][2]
				EndIf
				If aScan( aCodR, {|aX|aX[4]=="CSL"})>0
					SE2->E2_CODRCSL  := aCodR[aScan( aCodR, {|aX|aX[4]=="CSL"})][2]
				EndIf

				// Calculo do INSS
				aAreaAt:= GetArea()
				DbSelectArea("SE2")
				aAreaSE2:= GetArea()

				lRecalcINS	:= aColsSE2[nX][nPINSS] > 0 
				If lRecalcINS
				  	If SA2->A2_TIPO == "F"
				    	nValInss := FCalcInsPF(nBaseIns, aColsSE2[nX][nPINSS], @nInssTot, .T., 0, .T., SE2->E2_EMISSAO, SE2->E2_VENCREA, !Empty(SF1->F1_CONTSOC))
				    Else
				    	nValInss := FCalcInsPJ(nBaseIns, aColsSE2[nX][nPINSS], @nInssTot, .T., 0, .T., SE2->E2_EMISSAO, SE2->E2_VENCREA)
				    EndIf 
				Else
					nValInss := 0
			    EndIf

			   	RestArea(aAreaSE2)
			   	RestArea(aAreaAt)

			   	If lRecalcINS
			   		If nInssTot > 0
			   			SE2->E2_INSS    := nInssTot
			   		Else
			   			SE2->E2_INSS    := 0
			   		EndIf
			   	Else
			   		SE2->E2_INSS    := nValInss
			   	EndIf
				SE2->E2_VRETINS := nValInss
				nValInss := 0
				nInssTot := 0 

				//Ponto de entrada para calculo do IRRF
				If lPe100IR
					aRetIrrf := ExecBlock( "MT100IR",.F.,.F., {SE2->E2_IRRF,aColsSE2[nX][nPValor],nX} )
					Do Case
						Case ValType(aRetIrrf)  == "N"
							SE2->E2_IRRF := aRetIrrf
							If SE2->E2_IRRF >= nVlRetIR
								RecLock("SF1",.F.)
								SF1->F1_VALIRF := SE2->E2_IRRF
								SF1->( MsUnlock() )
							Endif
						Case ValType(aRetIrrf)  == "A"
							SE2->E2_IRRF := aRetIrrf[1]
							SE2->E2_ISS  := Iif(lISSNat,aRetIrrf[2],0)
							If SE2->E2_IRRF >= nVlRetIR
								RecLock("SF1",.F.)
								SF1->F1_VALIRF := SE2->E2_IRRF
								SF1->( MsUnlock() )
							Endif
					EndCase
				EndIf
				
				If nPINSS > 0
					//Ponto de entrada para calculo do INSS
					If SE2->E2_INSS > 0
						If lPe100INS
							SE2->E2_INSS := ExecBlock( "MT100INS",.F.,.F.,{SE2->E2_INSS})
						EndIf
						//Atualiza E2_RETINS
						IF ( ALLTRIM(SA2->A2_TIPO)) == "J"
							SE2->E2_RETINS := SuperGetmv("MV_RETINPJ")
						else
							SE2->E2_RETINS:= SuperGetmv("MV_RETINPF")
						EndIF
					EndIf

					nInss := Iif( SED->ED_DEDINSS=="2",0,SE2->E2_INSS ) 

					If nX == nMaxFor
						SE2->E2_BASEINS := nSaldoIns
					Else
						If lCondTp8
							SE2->E2_BASEINS := ((nBaseIns / 100) * aProp[nX])
						ElseIf !lRatInss
							If nX == 1
		                   		SE2->E2_BASEINS := nBaseIns
		                   	EndIf
						Else
							SE2->E2_BASEINS := nBaseIns * aProp[nX]
						EndIf
						nSaldoIns -= SE2->E2_BASEINS
					Endif
				EndIf

				If nPPIS > 0
					SE2->E2_PIS     := aColsSE2[nX][nPPIS]
					//Ponto de entrada para calculo do PIS
					If lPe100PIS
						SE2->E2_PIS := ExecBlock( "MT100PIS",.F.,.F.,{SE2->E2_PIS})
					EndIf

					//Proporcionalizacao da base do PIS pela duplicata
					If nX == nMaxFor
						SE2->E2_BASEPIS := nSaldoPis
					Else
						If lCondTp8 .And. lRatPIS 
							SE2->E2_BASEPIS := ((nBasePis / 100) * aProp[nX])
						Elseif !lRatPIS
							If nX == 1
								SE2->E2_BASEPIS := nBasePis
							Endif
						Else
							SE2->E2_BASEPIS := nBasePis * aProp[nX]
						EndIf
						nSaldoPis -= SE2->E2_BASEPIS
					Endif
				EndIf

				IF nPCOFINS > 0
					SE2->E2_COFINS  := aColsSE2[nX][nPCOFINS]
					//Ponto de entrada para calculo do COFINS

					If lPe100COF
						SE2->E2_COFINS := ExecBlock( "MT100COF",.F.,.F.,{SE2->E2_COFINS})
					EndIf

					//Proporcionalizacao da base do COFINS pela duplicata
					If nX == nMaxFor
						SE2->E2_BASECOF := nSaldoCof
					Else
						If lCondTp8 .And. lRatCOFINS
							SE2->E2_BASECOF := ((nBaseCof / 100) * aProp[nX])
						Elseif !lRatCOFINS
							If nX == 1
								SE2->E2_BASECOF := nBaseCof
							Endif
						Else
							SE2->E2_BASECOF := nBaseCof * aProp[nX]
						EndIf

						nSaldoCof -= SE2->E2_BASECOF
					Endif
				EndIf

				If nPCSll > 0
					SE2->E2_CSLL    := aColsSE2[nX][nPCSLL]
					//Ponto de entrada para calculo do CSLL

					If lPe100CSL
						SE2->E2_CSLL := ExecBlock( "MT100CSL",.F.,.F.,{SE2->E2_CSLL})
					EndIf

					//Proporcionalizacao da base do CSLL pela duplicata
					If nX == nMaxFor
						SE2->E2_BASECSL := nSaldoCsl
					Else
						If lCondTp8 .And. lRatCSLL
							SE2->E2_BASECSL := ((nBaseCsl / 100) * aProp[nX])
						Elseif !lRatCSLL
							If nX == 1
								SE2->E2_BASECSL := nBaseCsl
							Endif
						Else
							SE2->E2_BASECSL := nBaseCsl * aProp[nX]
						EndIf

						nSaldoCsl -= SE2->E2_BASECSL
					Endif

				EndIf

				If nPFETHAB > 0
					SE2->E2_FETHAB := aColsSE2[nX][nPFETHAB]
					//Ponto de entrada para calculo do FETHAB

					If lPe100FET
						SE2->E2_FETHAB := ExecBlock( "MT100FET",.F.,.F.,{SE2->E2_FETHAB})
					EndIf
				EndIf

				If nPFACS > 0
					SE2->E2_FACS := aColsSE2[nX][nPFACS]
				EndIf

				If nPFABOV > 0
					SE2->E2_FABOV := aColsSE2[nX][nPFABOV]
				EndIf
				
				If nPIMA > 0 .And. SE2->(FieldPos("E2_IMA")) > 0
					SE2->E2_IMA := aColsSE2[nX][nPIMA]
				EndIf
				
				If nPFAMAD > 0 .And. SE2->(FieldPos("E2_FAMAD")) > 0
					SE2->E2_FAMAD := aColsSE2[nX][nPFAMAD]
				EndIf

			   	If lVisDirf
					If !Empty(aAUTOISS[3]) .and. Empty(SE2->E2_CODRPIS) .and. Empty(SE2->E2_CODRCOF) .and. Empty(SE2->E2_CODRCSL)
				   		SE2->E2_DIRF   := IIf(SE2->E2_IRRF > 0 .OR. nValIRRF > 0,cDirf, "2")
					Else
						SE2->E2_DIRF := cDirf
					Endif	

					If  SE2->E2_DIRF == "2"
						SE2->E2_CODRET := ""
					Else
						SE2->E2_CODRET := cCodRet
					EndIf
				Endif
				// Somente deduz o valor do ISS no titulo principal se a forma de retencao do ISS for pela baixa
				If cMRetISS == "1"
					//Converto o valor da duplicata para moeda corrente para subtrair
					//os impostos. Apos subtrair os impostos, converto o valor da
					//duplicata para moeda 2.
					If nMoedaCor <> 1
						If lIRBaixa .And. SE2->E2_IRRF > 0 // IR na baixa
							SE2->E2_VALOR   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun-SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
							SE2->E2_SALDO   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun-SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
						Else
							SE2->E2_VALOR   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun - GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) - SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
							SE2->E2_SALDO   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun - GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) - SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
						EndIf
					Else
						If lIRBaixa .And. SE2->E2_IRRF > 0 // IR na baixa
							SE2->E2_VALOR   := aColsSE2[nX][nPValor]-nValFun-SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS
							SE2->E2_SALDO   := aColsSE2[nX][nPValor]-nValFun-SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS
						Else											// IR na emiss„o
							SE2->E2_VALOR   := aColsSE2[nX][nPValor]-nValFun - GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) - SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS
							SE2->E2_SALDO   := aColsSE2[nX][nPValor]-nValFun - GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) - SE2->E2_ISS-nInss-nSEST-nFundesa-nValBTISS
						EndIf
					Endif
				Else
					//Converto o valor da duplicata para moeda corrente para subtrair
					//os impostos. Apos subtrair os impostos, converto o valor da
					//duplicata para moeda 2
					//Realizado tratamento para valor do titulo, quando pessoa
					//Juridica, opcao 2 no CALCIRF e IRRF maior que 0
					If nMoedaCor <> 1
						If lIRBaixa .AND. SA2->A2_TIPO == "J" .AND. SE2->E2_IRRF > 0
							SE2->E2_VALOR   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun-nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
							SE2->E2_SALDO   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun-nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
						ElseIf lIRBaixa .AND. SA2->A2_TIPO == "F"
							SE2->E2_VALOR   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun-nSEST-nFundesa-nInss-nValBTISS)/SF1->F1_TXMOEDA
							SE2->E2_SALDO   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun-nSEST-nFundesa-nInss-nValBTISS)/SF1->F1_TXMOEDA
						Else
							SE2->E2_VALOR   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun - GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) - nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
							SE2->E2_SALDO   := ((Round(aColsSE2[nX][nPValor]*SF1->F1_TXMOEDA,2))-nValFun - GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) - nInss-nSEST-nFundesa-nValBTISS)/SF1->F1_TXMOEDA
						EndIf
					Else
						If lIRBaixa .AND. SA2->A2_TIPO == "J".AND. SE2->E2_IRRF > 0
							SE2->E2_VALOR   := aColsSE2[nX][nPValor]-nValFun-nInss-nSEST-nFundesa-nValBTISS
							SE2->E2_SALDO   := aColsSE2[nX][nPValor]-nValFun-nInss-nSEST-nFundesa-nValBTISS
						ElseIf lIRBaixa .AND. SA2->A2_TIPO == "F"
							SE2->E2_VALOR   := aColsSE2[nX][nPValor]-nValFun-nSEST-nFundesa-nInss-nValBTISS
							SE2->E2_SALDO   := aColsSE2[nX][nPValor]-nValFun-nSEST-nFundesa-nInss-nValBTISS
						Else
							SE2->E2_VALOR   := aColsSE2[nX][nPValor]-nValFun - GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) -nInss-nSEST-nFundesa-nValBTISS
							SE2->E2_SALDO   := aColsSE2[nX][nPValor]-nValFun  -GrossUpIRRF( SE2->E2_IRRF, lGrossIRRF ) -nInss-nSEST-nFundesa-nValBTISS
						EndIf
					Endif
				Endif

				// Grava a forma de retencao do ISS (1=Emissao / 2=Baixa)
				If SE2->E2_ISS > 0
					SE2->E2_TRETISS := cMRetISS
					If !lCalcIssBx
						SE2->E2_VRETISS := SE2->E2_ISS
					EndIf
				Endif

				lRestValImp := .F.

				//Grava a Marca de "pendente recolhimento" dos demais registros
				If ( !Empty( SE2->E2_PIS ) .Or. !Empty( SE2->E2_COFINS ) .Or. !Empty( SE2->E2_CSLL ) )
					SE2->E2_PRETPIS := "1"
					SE2->E2_PRETCOF := "1"
					SE2->E2_PRETCSL := "1"
				EndIf

				If !lPCCBaixa .And. ((lRatPIS .And. lRatCOFINS .And. lRatCSLL) .Or. cModRetPIS == "2" .Or. cModRetPIS == "3" )
					Do Case
					Case cModRetPIS == "1"

						nVlRetPIS	:= 0
						nVlRetCOF	:= 0
						nVlRetCSLL	:= 0

						If SE2->E2_PIS == 0 .And. SE2->E2_COFINS == 0 .And. SE2->E2_CSLL == 0 .And.;
						   lRatPIS .And. lRatCOFINS .And. lRatCSLL
							AFill( aDadosRet, 0 )
						Else
							If nVencto == 2
								dRef := SE2->E2_VENCREA
							ElseIf nVencto == 1 .OR. EMPTY(nVencto)
								dRef := SE2->E2_EMISSAO
							ElseIf nVencto == 3
								dRef := SE2->E2_EMIS1
							Endif

							If (dDEmissao < dRefPCC .or. __lEmpPub) .And. aScan( aColsSE2 , {|x| x[nPPIS] > 0 .Or. x[nPCOFINS] > 0 .Or. x[nPCSLL] > 0 } ) > 0
								aDadosRet	:= NfeCalcRet( dRef, nIndexSE2 , @aDadosImp )
							Else
								SE2->E2_ORIGEM := "MATA100"
								cForLoja:= SE2->E2_FORNECE + SE2->E2_LOJA

								// C·lculo do PCC(Pis, Cofins, Csll) de acordo com a Lei 13.137 (FINXIMP)
								aRetPCC := newMinPcc(dRef,GetBsPccPg(),cNatureza,"P",SF1->F1_FORNECE+SF1->F1_LOJA,/*nIss*/,/*nIns*/,/*nIrf*/,/*lMin*/,/*lIgnrOrg*/,/*cMotBx*/,/*lChkMin*/,/*nTxMoeda*/, SE2->E2_PIS, SE2->E2_COFINS, SE2->E2_CSLL)

								If ( aRetPCC[2] + aRetPCC[3] + aRetPCC[4] ) > 0
									lRetParc := .T.
								ElseIf Empty(cNatureza) .Or. ( SED->ED_CALCPIS == "N" .And. SED->ED_CALCCOF == "N" .And. SED->ED_CALCCSL == "N" )	// Verifica se o PCC foi informado manualmente para gerar os titulos no Financeiro
									If ( aColsSE2[nX][nPPIS] + aColsSE2[nX][nPCOFINS] + aColsSE2[nX][nPCSLL] ) >= nNewMinPcc
										lRetParc := .T.
									EndIf
								Else
									lRetParc := .F.
								EndIf

								AFill( aDadosRet, 0 )	// Preenche as posicoes do array com 0
                        	EndIf
                    	EndIf

						lRetParc	:= .F.

						If __lEmpPub

							If SA2->A2_MINPUB == "2" .and. aDadosRet[2]+aDadosRet[3]+aDadosRet[4]+aDadosRet[10]< nMinPub  
								If SE2->(E2_PIS+E2_COFINS+E2_CSLL)+aDadosRet[2]+aDadosRet[3]+aDadosRet[4]+aDadosRet[10]+SE2->E2_IRRF < nMinPub
									lRetParc	:= .F.
								Else	
									SE2->E2_PIS    += aDadosRet[2]
									SE2->E2_COFINS += aDadosRet[3]
									SE2->E2_CSLL   += aDadosRet[4]
									lRetParc := .T.
								Endif	
							Else
								lRetParc := .T.
							Endif	

						Else	
							//Verifica se ha residual de retencao para ser somada a retencao do titulo atual
							If aDadosRet[ 6 ] > nValMinRet .And. IIf( lRatPIS , SE2->E2_PIS > 0 , aScan( aColsSE2 , {|x| x[nPPIS] > 0 } ) > 0 )  // PIS
								lRetParc	:= .T.
								nVlRetPis += aDadosImp[1]
							EndIf

							If aDadosRet[ 7 ] > nValMinRet .And. IIf( lRatCOFINS , SE2->E2_COFINS > 0 , aScan( aColsSE2 , {|x| x[nPCOFINS] > 0 } ) > 0 )  // COFINS
								lRetParc	:= .T.
								nVlRetCof += aDadosImp[2]
							EndIf

							If aDadosRet[ 8 ] > nValMinRet .And. IIf( lRatCSLL , SE2->E2_CSLL > 0 , aScan( aColsSE2 , {|x| x[nPCSLL] > 0 } ) > 0 )  // CSLL
								lRetParc	:= .T.
								nVlRetCSLL += aDadosImp[3]
							EndIf
						EndIf 

						If lRetParc .and. !__lEmpPub
							nTotARet	:= nVlRetPIS + nVlRetCOF + nVlRetCSLL

							nSobra		:= SE2->E2_VALOR - nTotARet
							If nSobra < 0
								nSavRec		:= SE2->( Recno() )

								nFatorRed	:= 1 - ( Abs( nSobra ) / nTotARet )
								nVlRetPIS	:= NoRound( nVlRetPIS * nFatorRed, 2 )
								nVlRetCOF	:= NoRound( nVlRetCOF * nFatorRed, 2 )
								nVlRetCSLL	:= SE2->E2_VALOR - ( nVlRetPIS + nVlRetCOF ) - 0.01

								//Grava o valor de NDF caso a retencao seja maior que o valor do titulo
								ADupCredRt(Abs(nSobra),"501",SE2->E2_MOEDA)

								//Restaura o registro do titulo original
								SE2->( MsGoto( nSavRec ) )
								Reclock( "SE2", .F. )
							EndIf

							lRestValImp := .T.

							//Guarda os valores originais
							nRetOriPIS  := SE2->E2_PIS
							nRetOriCOF  := SE2->E2_COFINS
							nRetOriCSLL := SE2->E2_CSLL

							//Grava os novos valores de retencao para este registro
							SE2->E2_PIS    := nVlRetPIS
							SE2->E2_COFINS := nVlRetCOF
							SE2->E2_CSLL   := nVlRetCSLL

							nSavRec := SE2->( Recno() )

							//Exclui a Marca de "pendente recolhimento" dos demais registros
							aRecnos := aClone( aDadosRet[ 5 ] )

							cPrefOri  := SE2->E2_PREFIXO
							cNumOri   := SE2->E2_NUM
							cParcOri  := SE2->E2_PARCELA
							cTipoOri  := SE2->E2_TIPO
							cCfOri    := SE2->E2_FORNECE
							cLojaOri  := SE2->E2_LOJA
							cEmiOri   := SE2->E2_EMISSAO

							For nLoop := 1 to Len( aRecnos )
								SE2->( dbGoto( aRecnos[ nLoop ] ) )

								RecLock( "SE2", .F. )

								If !Empty( nVlRetPIS )
									SE2->E2_PRETPIS := "2"
								EndIf

								If !Empty( nVlRetCOF )
									SE2->E2_PRETCOF := "2"
								EndIf

								If !Empty( nVlRetCSLL )
									SE2->E2_PRETCSL := "2"
								EndIf

								SE2->( MsUnlock() )

									If nSavRec <> aRecnos[ nLoop ]
										DbSelectArea("SFQ")
										RecLock("SFQ",.T.)
										SFQ->FQ_FILIAL  := xFilial("SFQ")
										SFQ->FQ_ENTORI  := "SE2"
										SFQ->FQ_PREFORI := cPrefOri
										SFQ->FQ_NUMORI  := cNumOri
										SFQ->FQ_PARCORI := cParcOri
										SFQ->FQ_TIPOORI := cTipoOri
										SFQ->FQ_CFORI   := cCfOri
										SFQ->FQ_LOJAORI := cLojaOri
										SFQ->FQ_ENTDES  := "SE2"
										SFQ->FQ_PREFDES := SE2->E2_PREFIXO
										SFQ->FQ_NUMDES  := SE2->E2_NUM
										SFQ->FQ_PARCDES := SE2->E2_PARCELA
										SFQ->FQ_TIPODES := SE2->E2_TIPO
										SFQ->FQ_CFDES   := SE2->E2_FORNECE
										SFQ->FQ_LOJADES := SE2->E2_LOJA

										//Grava a filial de destino caso o campo exista
										SFQ->FQ_FILDES := SE2->E2_FILIAL
										MsUnlock()
									Endif

							Next nLoop

							//Retorna do ponteiro do SE1 para a parcela
							SE2->( MsGoto( nSavRec ) )
							Reclock( "SE2", .F. )

						ElseIf dDEmissao >= dRefPCC .and. !__lEmpPub		// Validacao do PCC (Pis, Cofins, Csll) de acordo com a Lei 13.137 - Variavel lRetParc determina geracao dos titulos no Financeiro
							If ( aRetPCC[2] + aRetPCC[3] + aRetPCC[4] ) > 0
								lRetParc := .T.
							Else	// Verifica se o PCC foi informado manualmente para gerar os titulos no Financeiro
								If Empty(cNatureza) .Or. ( SED->ED_CALCPIS == "N" .And. SED->ED_CALCCOF == "N" .And. SED->ED_CALCCSL == "N" )
									If ( aColsSE2[nX][nPPIS] + aColsSE2[nX][nPCOFINS] + aColsSE2[nX][nPCSLL] ) >= nNewMinPcc
										lRetParc := .T.
									EndIf
								EndIf

							EndIf

							//Grava os novos valores de retencao para este registro
							SE2->E2_PIS    := aRetPCC[2]
							SE2->E2_COFINS := aRetPCC[3]
							SE2->E2_CSLL   := aRetPCC[4]
						EndIf

					Case cModRetPIS == "2"
						//Efetua a retencao
						lRetParc := .T.
					Case cModRetPIS == "3"
						//Nao efetua a retencao
						lRetParc := .F.
					EndCase
				Else
					If nVencto == 2
						dRef := SE2->E2_VENCREA
					ElseIf nVencto == 1 .OR. EMPTY(nVencto)
						dRef := SE2->E2_EMISSAO
					ElseIf nVencto == 3
						dRef := SE2->E2_EMIS1
					Endif
					
					aRetPCC	:= { .F., 0, 0, 0 }
					If !__lEmpPub
						If !EMPTY(SE2->E2_PIS + SE2->E2_COFINS + SE2->E2_CSLL)
							// C·lculo do PCC(Pis, Cofins, Csll) de acordo com a Lei 13.137 (FINXIMP)
							aRetPCC := newMinPcc( dRef,GetBsPccPg() ,cNatureza ,"P" , SF1->F1_FORNECE+SF1->F1_LOJA,/*nIss*/,/*nIns*/,/*nIrf*/,/*lMin*/,/*lIgnrOrg*/,/*cMotBx*/,/*lVerMin*/,/*nTxMoeda*/,SE2->E2_PIS, SE2->E2_COFINS, SE2->E2_CSLL)
						EndIf

						If ((aRetPCC[2] + aRetPCC[3] + aRetPCC[4]) > 0)
							lRetParc := .T.
							//Grava os novos valores de retencao para este registro
							SE2->E2_PIS    := aRetPCC[2]
							SE2->E2_COFINS := aRetPCC[3]
							SE2->E2_CSLL   := aRetPCC[4]
						ElseIf Empty(cNatureza) .Or. ( SED->ED_CALCPIS == "N" .And. SED->ED_CALCCOF == "N" .And. SED->ED_CALCCSL == "N" )	// Verifica se o PCC foi informado manualmente para gerar os titulos no Financeiro
							If ( aColsSE2[nX][nPPIS] + aColsSE2[nX][nPCOFINS] + aColsSE2[nX][nPCSLL] ) >= nNewMinPcc
								lRetParc := .T.  
							EndIf
						Else
							//Grava os novos valores de retencao para este registro
							lRetParc		:= .F.
						EndIf
					EndIf
				EndIf

				If !lPccBaixa
					// Tratamento para converter o valor do PCC para a moeda informada na nota
					// para que o abatimento do titulo NF seja feito na mesma moeda
					If SE2->E2_MOEDA <> 1
						nVlConvPis := NoRound(xMoeda(SE2->E2_PIS,1,SE2->E2_MOEDA,dDEmissao),2)
						nVlConvCof := NoRound(xMoeda(SE2->E2_COFINS,1,SE2->E2_MOEDA,dDEmissao),2)
						nVlConvCsl := NoRound(xMoeda(SE2->E2_CSLL,1,SE2->E2_MOEDA,dDEmissao),2)
					Else
						nVlConvPis := SE2->E2_PIS
						nVlConvCof := SE2->E2_COFINS
						nVlConvCsl := SE2->E2_CSLL
					EndIf

					SE2->E2_VALOR	-= nVlConvPis
					SE2->E2_SALDO	-= nVlConvPis
					nVlCruz			-= SE2->E2_PIS

					SE2->E2_VALOR	-= nVlConvCof
					SE2->E2_SALDO	-= nVlConvCof
					nVlCruz			-= SE2->E2_COFINS

					SE2->E2_VALOR	-= nVlConvCsl
					SE2->E2_SALDO	-= nVlConvCsl
					nVlCruz			-= SE2->E2_CSLL
				Endif

				SE2->E2_VALOR   -= SE2->E2_FETHAB
				SE2->E2_SALDO   -= SE2->E2_FETHAB
				nVlCruz         -= SE2->E2_FETHAB

				SE2->E2_VALOR   -= SE2->E2_FABOV
				SE2->E2_SALDO   -= SE2->E2_FABOV
				nVlCruz         -= SE2->E2_FABOV

				SE2->E2_VALOR   -= SE2->E2_FACS
				SE2->E2_SALDO   -= SE2->E2_FACS
				nVlCruz         -= SE2->E2_FACS
				
				If SE2->(FieldPos("E2_IMA")) > 0
					SE2->E2_VALOR   -= SE2->E2_IMA
					SE2->E2_SALDO   -= SE2->E2_IMA
					nVlCruz         -= SE2->E2_IMA
				Endif
				
				If SE2->(FieldPos("E2_FAMAD")) > 0
					SE2->E2_VALOR   -= SE2->E2_FAMAD
					SE2->E2_SALDO   -= SE2->E2_FAMAD
					nVlCruz         -= SE2->E2_FAMAD
				Endif

				//Gravacao do imposto CIDE no titulo principal
				//Caso seja utilizada cond. pagto. parcelada, grava o valor total somente na primeira parcela
				If lCIDE .And. nX == 1
					SE2->E2_CIDE := nValCIDE
				EndIf
			Else
				SE2->E2_VALOR   := aColsSE2[nX][nPValor]
				SE2->E2_SALDO   := aColsSE2[nX][nPValor]
			EndIf

            //Busca o valor da chave FK7
            cChaveFK7 := FinGrvFK7("SE2",†xFilial("SE2",SE2->E2_FILORIG) +"|"+ SE2->E2_PREFIXO +"|"+ SE2->E2_NUM +"|"+ SE2->E2_PARCELA +"|"+ SE2->E2_TIPO +"|"+ SE2->E2_FORNECE +"|"+ SE2->E2_LOJA)

			// Verifica se o sistema esta preparado para utilizar o motor de tributos genericos
			If lTrbGenFin .And. Len(aParcTrGen) > 0

				// Limpa variaveis pois devem ser montadas para cada parcela
				aImpCalc  := {}
				aImpos    := {}

				// Adiciona array com informacoes basicas que sera complementado posteriormente atraves da FinCalImp()
				For nK := 1 To Len(aParcTrGen[nX])

					If aParcTrGen[nX][nK][3] > 0
						aAdd(aImpCalc,{aParcTrGen[nX][nK][1],;	// Cod. Regra Financeira FKK
									   aParcTrGen[nX][nK][2],;	// Base de calculo
									   aParcTrGen[nX][nK][3],;	// Valor calculado
									   aParcTrGen[nX][nK][4],;	// ID da regra fiscal F2B
									   cChaveFK7,;              // Chave da FK7
									   ,;
									   ,;
									   ,;
									   ,;
									   aParcTrGen[nX][nK][6],;  // Codigo da URF
									   aParcTrGen[nX][nK][7]})  // Percentual aplicavel da URF
					EndIf

				Next nK

				// Chama a funcao FinCalImp() abaixo para que o array aImpCalc seja complementado com informacoes do motor. A partir deste momento esta apto ao enviar para A050DUPPAG (chamada na FaAvalSE2).
				If Len(aImpCalc) > 0
					aImpos := FinCalImp("1", SE2->E2_NATUREZ, SE2->E2_FORNECE, SE2->E2_LOJA, cFilAnt, Nil, Nil ,Nil, Nil, SE2->E2_TIPO, Nil, Nil, aImpCalc)
				EndIf

				// Subtrai ou soma valor do tributo no titulo principal de acordo com o campo FKK_VLNOTA
				If Len(aImpos) > 0

					For nK := 1 To Len(aImpos)

						If aImpos[nK][13] == "1"

							SE2->E2_VALOR -= aImpos[nK][3]
							SE2->E2_SALDO -= aImpos[nK][3]
							nVlCruz       -= aImpos[nK][3]

						ElseIf aImpos[nK][13] == "2"

							SE2->E2_VALOR += aImpos[nK][3]
							SE2->E2_SALDO += aImpos[nK][3]
							nVlCruz       += aImpos[nK][3]

						EndIf

					Next nK

				EndIf

			EndIf

			//Verifica se ha necessidade da gravacao das multiplas naturezas
			nRateio := 0
			If lRatLiq .And. !lPccBaixa 
				nValor := SE2->E2_VALOR
				// Verifico se o IRRF atingiu o minimo e se n„o È Groos IRRF e se o IRRF est· na Emiss„o
				If !lIRBaixa .AND. SE2->E2_IRRF > 0 .AND. SE2->E2_IRRF <= nVlRetIR .AND. !lGrossIRRF
					nValor += SE2->E2_IRRF
				EndIf

				If !lRetParc
					nValor   += SE2->E2_PIS
					nVlCruz	 += SE2->E2_PIS
				EndIf
				If !lRetParc
					nValor  += SE2->E2_COFINS
					nVlCruz	 += SE2->E2_COFINS
				EndIf
				If !lRetParc
					nValor   += SE2->E2_CSLL
					nVlCruz	 += SE2->E2_CSLL
				EndIf
			Else
				nValor   := aColsSE2[nX][nPValor]
			EndIf
			
			For nY := 1 To Len(aColsSEV)
				If (!aColsSEV[nY][Len(aColsSEV[1])] .And. !Empty(aColsSEV[nY][1])) .OR. (lMulNats .And. !Empty(SE2->E2_NATUREZ))
					SE2->E2_MULTNAT := "1"
					RecLock("SEV", .T. )
					For nZ := 1 To Len(aHeadSEV)
						If aHeadSEV[nZ][10]<>"V"
							SEV->(FieldPut(FieldPos(aHeadSEV[nZ][2]),aColsSEV[nY][nZ]))
						EndIf
					Next nZ

					//Habilita a geracao dos rateios financeiros para integracao com NFE
					//mesmo com natureza simples mas com rateios de c.custo por itens no
					//documento de entrada. Vinculado ao MV_MULNATP e MV_MULNATS.
					nPercSEV 		 := SEV->EV_PERC
					If Empty(aColsSEV[nY][1])
						nPercSEV		:= 100
						SEV->EV_NATUREZ	:= SE2->E2_NATUREZ
					EndIf

					SEV->EV_FILIAL   := xFilial("SEV")
					SEV->EV_PREFIXO  := SE2->E2_PREFIXO
					SEV->EV_NUM      := SE2->E2_NUM
					SEV->EV_PARCELA  := SE2->E2_PARCELA
					SEV->EV_CLIFOR   := SE2->E2_FORNECE
					SEV->EV_LOJA     := SE2->E2_LOJA
					SEV->EV_TIPO     := SE2->E2_TIPO
					SEV->EV_VALOR    := If( nY == Len(aColsSEV), nValor - nRateio, Round(nValor * nPercSEV/100, 2) )
					SEV->EV_PERC     := nPercSEV / 100
					SEV->EV_RECPAG   := "P"
					SEV->EV_LA       := ""
					SEV->EV_IDENT    := "1"
                    SEV->EV_RATEICC  := cRateIcc
                    SEV->EV_IDDOC    := cChaveFK7

                    SEV->( MsUnLock() )

					nRateio += SEV->EV_VALOR
					nRateioSEZ := 0
					AtuSldNat(SEV->EV_NATUREZ, SE2->E2_VENCREA, SE2->E2_MOEDA, If(SE2->E2_TIPO $ MVPAGANT+"/"+MV_CPNEG,"3","2"), "P", SEV->EV_VALOR, SE2->E2_VLCRUZ*SEV->EV_PERC, If(SE2->E2_TIPO $ MVABATIM, "-", "+"),,FunName(),"SEV", SEV->(Recno()),nOpca)

					For nZ := 1 To Len(aSEZ)

						RecLock("SEZ",.T.)
						SEZ->EZ_FILIAL := xFilial("SEZ")
						SEZ->EZ_PREFIXO:= SEV->EV_PREFIXO
						SEZ->EZ_NUM    := SEV->EV_NUM
						SEZ->EZ_PARCELA:= SEV->EV_PARCELA
						SEZ->EZ_CLIFOR := SEV->EV_CLIFOR
						SEZ->EZ_LOJA   := SEV->EV_LOJA
						SEZ->EZ_TIPO   := SEV->EV_TIPO
						SEZ->EZ_PERC   := aSEZ[nZ][4]
						SEZ->EZ_VALOR  := IIf(nZ==Len(aSEZ),SEV->EV_VALOR-nRateioSEZ,Round(SEV->EV_VALOR*SEZ->EZ_PERC,2))
						SEZ->EZ_NATUREZ:= SEV->EV_NATUREZ
						SEZ->EZ_CCUSTO := aSEZ[nZ][1]
						SEZ->EZ_ITEMCTA:= aSEZ[nZ][2]
						SEZ->EZ_CLVL   := aSEZ[nZ][3]
						SEZ->EZ_CONTA   := aSEZ[nZ][6]

						SEZ->EZ_RECPAG := SEV->EV_RECPAG
						SEZ->EZ_LA     := ""
						SEZ->EZ_IDENT  := SEV->EV_IDENT
						SEZ->EZ_SEQ    := SEV->EV_SEQ
						SEZ->EZ_SITUACA:= SEV->EV_SITUACA
						SEZ->EZ_IDDOC  := cChaveFK7
						nRateioSEZ += SEZ->EZ_VALOR
						// Tratamento para entidades contabeis adicionais
						nPosEntAd := 6
						For nW := 1 To Len(aCTBEnt)
							nPosEntAd++
							SEZ->&("EZ_EC"+aCTBEnt[nW]+"DB") := aSEZ[nZ][nPosEntAd]
							nPosEntAd++
							SEZ->&("EZ_EC"+aCTBEnt[nW]+"CR") := aSEZ[nZ][nPosEntAd]
						Next nW

						SEZ->( MsUnLock() )
					Next nZ
				EndIf
				AADD(aRecSEV,SEV->(Recno()))
			Next nY

            //Processa alteracoes da NF com base no contrato - SIGAGCT
            If !Empty(aContra)
                CNTAvalGCT(nGCTRet,nGCTDesc,nGCTMult,nGCTBoni,@nVlCruz,aContra)
            EndIf

			//funÁ„o para verificar os ids de impostos do configurador de tributos para barrar a geraÁ„o do tÌtulo pelo padr„o.
			If FindFunction("A103IdGen")
				A103IdGen(cIdsTrGen,@lPccMR,@lIrfMR,@lInsMR,@lIssMR,@lCidMR,@lSestMR,@lFunMR,@lInsPMR,@lFamadMR,@lFethabMR,@lFacsMR,@lImaMR,@lFabovMR)
			Endif

            FaAvalSE2(1, "MATA100",(nX==1),MaFisRet(,"NF_VALIRR"),MaFisRet(,"NF_VALINS"),lRetParc,MaFisRet(,"NF_VALISS"),MaFisRet(,"NF_BASEISS"),lRatImp,cRecIss,,aCodR,;
			aImpos,lPccMR,lIrfMR,lInsMR,lIssMR,lCidMR,lSestMR,,If(lRateio,oRatIRF:aRatIRF,NIL),,lFunMR,lInsPMR,lFamadMR,lFethabMR,lFacsMR,lImaMR,lFabovMR) 
            
			If cPaisLoc == "BRA"
                If !lRetParc .and. !lPccBaixa
                    SE2->E2_VALOR	+= SE2->E2_PIS
                    SE2->E2_SALDO	+= SE2->E2_PIS
                    If !lRatLiq // Se estiver .T. a recomposiÁ„o do VlCruz j· ocorreu
                        nVlCruz		+= SE2->E2_PIS
                    EndIf					
                EndIf
                If !lRetParc .and. !lPccBaixa
                    SE2->E2_VALOR	+= SE2->E2_COFINS
                    SE2->E2_SALDO	+= SE2->E2_COFINS
                    If !lRatLiq // Se estiver .T. a recomposiÁ„o do VlCruz j· ocorreu
                        nVlCruz		+= SE2->E2_COFINS
                    EndIf
                EndIf
                If !lRetParc .and. !lPccBaixa
                    SE2->E2_VALOR	+= SE2->E2_CSLL
                    SE2->E2_SALDO	+= SE2->E2_CSLL
                    If !lRatLiq // Se estiver .T. a recomposiÁ„o do VlCruz j· ocorreu
                        nVlCruz	    += SE2->E2_CSLL
                    EndIf
                EndIf
				
				If lVisDirf
					If lHasIRR .And. cDirf=="1" .And. SE2->E2_BASEIRF>0//-- Se houve retenÁ„o do IR em alguma parcela, mantem o cÛdigo dele.
						SE2->E2_CODRET := aCodR[aScan( aCodR, {|aX|aX[4]=="IRR"})][2]
					ElseIf SE2->(E2_BASEIRF+E2_BASECOF+E2_BASEPIS+E2_BASECSL+E2_BASEISS)<=0
						SE2->E2_CODRET :=""
					EndIF
					//-- N„o atualiza antes pois FaAvalSE2/A050DupPag olha o DIRF='1' para gerar o registro TX 
					SE2->E2_DIRF := "2"
				EndIF
            EndIf
			
			If lRetParc
				aCtbRet[1] += SE2->E2_VRETPIS
				aCtbRet[2] += SE2->E2_VRETCOF
				aCtbRet[3] += SE2->E2_VRETCSL
			EndIf

			If lRestValImp
				//Restaura os valores originais de PIS / COFINS / CSLL
				SE2->E2_PIS    := nRetOriPIS
				SE2->E2_COFINS := nRetOriCOF
				SE2->E2_CSLL   := nRetOriCSLL
			EndIf

			nInss			:=	Iif( SED->ED_DEDINSS=="2",0,SE2->E2_INSS )
			SE2->E2_VLCRUZ 	:= 	xMoeda(SE2->E2_VALOR,SE2->E2_MOEDA,1,SE2->E2_EMISSAO,NIL,SF1->F1_TXMOEDA)

			If lIRBaixa // IR na baixa nao deve descontar do E2_VLCRUZ
				nVlCruz -= (SE2->E2_VLCRUZ + nValFun + IIf(cMRetISS == "1", SE2->E2_ISS, 0) + nInss + nSEST + nFundesa)
			Else
				nVlCruz -= (SE2->E2_VLCRUZ + nValFun + IIf(cMRetISS == "1", SE2->E2_ISS, 0) + nInss + nSEST + nFundesa + GrossUpIRRF(SE2->E2_IRRF, lGrossIRRF))
			EndIf

			If nX == nMaxFor
				SE2->E2_VLCRUZ += nVlCruz
			EndIf

			If lMulta
				//Grava as multas de contrato ( SIGAGCT ) na parcela
				nBaixaMult := Min( nSaldoMult, SE2->E2_SALDO )
				SE2->E2_DECRESC := nBaixaMult
				SE2->E2_SDDECRE := nBaixaMult

				//Baixa o saldo a gravar
				nSaldoMult -= nBaixaMult
			Else
				//Grava o valor da bonificacao ( SIGAGCT ) na parcela
				If !Empty( nSaldoBoni )
					SE2->E2_ACRESC  := nSaldoBoni
					SE2->E2_SDACRES := nSaldoBoni
					//Zera o saldo a gravar
					nSaldoBoni := 0
				EndIf
			EndIf

			// Gravacao do campo E2_FLUXO para que os saldos da natureza sejam atualizados na funcao AtuSldNat
			// quando o titulo for alterado no Financeiro
			SE2->E2_FLUXO := "S"

			If lTemDocs
				SE2->E2_TEMDOCS := "1"
			EndIf

			If SE2->E2_MULTNAT <> "1"
				AtuSldNat(SE2->E2_NATUREZ, SE2->E2_VENCREA, SE2->E2_MOEDA, If(SE2->E2_TIPO $ MVPAGANT+"/"+MV_CPNEG,"3","2"), "P", SE2->E2_VALOR, SE2->E2_VLCRUZ, If(SE2->E2_TIPO $ MVABATIM, "-", "+"),,FunName(),"SE2", SE2->(Recno()),nOpca)
            Else

                //Atualiza E2_MULTNAT dos titulos rateados
                cTitPai  := RTrim( SE2->E2_PREFIXO + SE2->E2_NUM + SE2->E2_PARCELA + SE2->E2_TIPO + SE2->E2_FORNECE + SE2->E2_LOJA )
				aAreaSE2 := SE2->( GetArea() )

                SE2->( DbSetOrder(17) )     //E2_FILIAL + E2_TITPAI
                If SE2->( DbSeek( xFilial("SE2") + cTitPai) )

                    While !SE2->( Eof() ) .And. Alltrim(xFilial("SE2") + cTitPai) == Alltrim(SE2->E2_FILIAL + SE2->E2_TITPAI)

                        RecLock("SE2", .F.)
                            SE2->E2_MULTNAT := IIF(lRatImp, "1", "2")
                        SE2->( MsUnLock() )

                        SE2->( DbSkip() )
                    EndDo
                EndIf

                RestArea(aAreaSE2)
			Endif
			
			//Template acionando ponto de entrada
			If ExistTemplate("MT100GE2")
				ExecTemplate("MT100GE2",.F.,.F.)
			EndIf

			//Ponto de entrada apos a gravacao do titulo a pagar
			If Existblock("MT100GE2")
				ExecBlock("MT100GE2",.F.,.F.,{aColsSE2[nX],nOpcA,aHeadSE2,nX,aColsSE2})
			EndIf

			//Agroindustria
			If FindFunction("OGXUtlOrig") //Encontra a funÁ„o
				If OGXUtlOrig() //Verifica se existe
				   If FindFunction("OGX140") //Encontra a funÁ„o
					   OGX140AtuE2() // Executa a funÁ„o
				   EndIf
				EndIf
			EndIf

			//O funrural somente deve ser gerado para a primeira parcela
			nValFun	:= 0
			
			//A FETHAB somente deve ser gerada para a primeira parcela
			nValFet	:= 0
			nValFab	:= 0
			nValFac	:= 0
			
			//Armazena o recno dos titulos gerados
			If ValType( aRecGerSE2 ) == "A"
				AAdd( aRecGerSE2, SE2->( Recno() ) )
			EndIf

			// Zera variavel do INSS Patronal para nao gerar o titulo em duplicidade
			// A variavel nValINP e utilizada na funcao A050DUPPAG (FINXFIN)
			nValINP := 0
		EndIf
	Next nX

	//verificacao SIGAPLS
	if lPLSMT103 
		PLSMT103(3) 
	endIf

	//Variaveis para gravaÁ„o do campo E2_TITPAI
	cPreOr    := SE2->E2_PREFIXO
	cNumOr    := SE2->E2_NUM
	cParOr    := SE2->E2_PARCELA
	cTipOr    := SE2->E2_TIPO
	cForOr    := SE2->E2_FORNECE
	cLojOr    := SE2->E2_LOJA

	//Titulo de PIS COFINS ImportaÁ„o
	IF MV_PAR23 == 1 .And. !Empty(cNatPis) .And. !Empty(cNatCof) .And. lPisCofImp

		dbSelectArea("SA2")
		SA2->(dbSetOrder(1))

		dbSelectArea("SED")
		SED->(dbSetOrder(1))

		If SA2->(!MsSeek(xFilial("SA2")+cForPisCof+cLojaZero))
			Reclock("SA2",.T.)
			SA2->A2_FILIAL	:=	xFilial("SA2")
			SA2->A2_COD 	:=	cForPisCof
			SA2->A2_LOJA	:=	cLojaZero
			SA2->A2_NOME	:=	"UNIAO"
			SA2->A2_NREDUZ	:=	"UNIAO"
			SA2->A2_MUN 	:=	"."
			SA2->A2_EST 	:=	SuperGetMV("MV_ESTADO")
			SA2->A2_BAIRRO	:=	"."
			SA2->A2_END 	:=	"."
			MsUnlock()
		EndIf

		If SF1->F1_VALIMP6 > 0

			/*Natureza do PIS*/
			If !SED->(MsSeek(xFilial("SED") + Padr(cNatPis, TamSX3("ED_CODIGO")[1])))
				RecLock("SED",.T.)
				SED->ED_FILIAL  := xFilial("SED")
				SED->ED_CODIGO  := cNatPis
				SED->ED_CALCIRF := "N"
				SED->ED_CALCISS := "N"
				SED->ED_CALCINSS:= "N"
				SED->ED_DESCRIC := "PIS"
				MsUnlock()
			EndIf

			// Tratamento realizado para caso o titulo ja tenha sido gerado para o mesmo documento, dever· ser incrementado o prefixo.
			cPrefPis := GetNxtPrfImp( Padr( cPrefPis, nTamE2PREF ) , Padr( SF1->F1_DOC, nTamE2NUM ) , , Padr( "PIS", nTamE2TIPO ) , Padr( cForPisCof, nTamE2FORN ) , Padr( cLojaZero, nTamE2LOJA ) )
			aTit050 := {{"E2_FILIAL", xFilial("SE2"), NIL},;
							{"E2_PREFIXO", cPrefPis, NIL},;
							{"E2_NUM", SF1->F1_DOC, NIL},;
							{"E2_TIPO", "PIS", NIL},;
							{"E2_NATUREZ", cNatPis, NIL},;
							{"E2_FORNECE", cForPisCof, NIL},;
							{"E2_LOJA", cLojaZero, NIL},;
							{"E2_EMISSAO", SF1->F1_EMISSAO, NIL},;
							{"E2_VENCTO", SF1->F1_EMISSAO, NIL},;
							{"E2_VENCREA", SF1->F1_EMISSAO, NIL},;
							{"E2_VALOR", SF1->F1_VALIMP6, NIL},;
							{"E2_TITPAI", cPreOr + cNumOr + cParOr + cTipOr + cForOr + cLojOr, NIL},;
							{"E2_ORIGEM", "MATA103", NIL}}
							//Adicionado E2_TITPAI, para que n„o se perca o vinculo com o titulo pai (nota de entrada). 


			If aScan(aCodR, {|aX| aX[4] == "PS2"}) > 0
				aAdd(aTit050, {"E2_DIRF", AllTrim( Str( aCodR[aScan( aCodR, {|aX|aX[4]=="PS2"})][3] ) ), NIL})
				aAdd(aTit050, {"E2_CODRET", aCodR[aScan( aCodR, {|aX|aX[4] == "PS2"})][2], NIL})
			EndIf

			MsExecAuto({|x,y,z| FINA050(x,y,z)},aTit050,,3)

			If lMsErroAuto
				If !l103Auto
					MostraErro()
				EndIf
			Else
				aAdd(aTitImp,{SE2->(RecNo()),""})
			EndIf

			aTit050 := {}
		EndIf

		If SF1->F1_VALIMP5 > 0

			If !SED->(MsSeek(xFilial("SED") + Padr(cNatCof, TamSX3("ED_CODIGO")[1])))
				RecLock("SED",.T.)
				SED->ED_FILIAL  := xFilial("SED")
				SED->ED_CODIGO  := cNatCof
				SED->ED_CALCIRF := "N"
				SED->ED_CALCISS := "N"
				SED->ED_CALCINSS:= "N"
				SED->ED_DESCRIC := "COFINS"
				MsUnlock()
			EndIf

			// Tratamento realizado para caso o titulo ja tenha sido gerado para o mesmo documento, dever· ser incrementado o prefixo.
			cPrefCof := GetNxtPrfImp( Padr( cPrefCof, nTamE2PREF ) , Padr( SF1->F1_DOC, nTamE2NUM ) , , Padr( "COF", nTamE2TIPO ) , Padr( cForPisCof, nTamE2FORN ) , Padr( cLojaZero, nTamE2LOJA ) )
			aTit050 := {{"E2_FILIAL", xFilial("SE2"), NIL},;
							{"E2_PREFIXO", cPrefCof, NIL},;
							{"E2_NUM", SF1->F1_DOC, NIL},;
							{"E2_TIPO", "COF", NIL},;
							{"E2_NATUREZ", cNatCof, NIL},;
							{"E2_FORNECE", cForPisCof, NIL},;
							{"E2_LOJA", cLojaZero, NIL},;
							{"E2_EMISSAO", SF1->F1_EMISSAO, NIL},;
							{"E2_VENCTO", SF1->F1_EMISSAO, NIL},;
							{"E2_VENCREA", SF1->F1_EMISSAO, NIL},;
							{"E2_VALOR", SF1->F1_VALIMP5, NIL},;
							{"E2_TITPAI", cPreOr + cNumOr + cParOr + cTipOr + cForOr + cLojOr, NIL},;
							{"E2_ORIGEM", "MATA103", NIL}}
							//Adicionado E2_TITPAI, para que n„o se perca o vinculo com o titulo pai (nota de entrada)


			If aScan(aCodR, {|aX| aX[4] == "CF2"}) > 0
				aAdd(aTit050, {"E2_DIRF", AllTrim( Str( aCodR[aScan( aCodR, {|aX| aX[4] == "CF2"})][3] ) ), NIL})
				aAdd(aTit050, {"E2_CODRET", aCodR[aScan( aCodR, {|aX|aX[4] == "CF2"})][2], NIL})
			EndIf

			MsExecAuto({|x,y,z| FINA050(x,y,z)},aTit050,,3)

			If lMsErroAuto
				If !l103Auto
					MostraErro()
				EndIf
			Else
				aAdd(aTitImp,{SE2->(RecNo()),""})
			EndIf

			aTit050 := {}

		EndIf

	EndIf

	//Titulo de ISS ImportaÁ„o
	If MV_PAR24 == 1 .And. !Empty(cPrefISS) .And. !Empty(cNatIss) .And. lISSImp

		dbSelectArea("SA2")
		SA2->(dbSetOrder(1))

		dbSelectArea("SED")
		SED->(dbSetOrder(1))

		/*Fornecedor do ISS*/
		If SA2->(!MsSeek(xFilial("SA2")+PadR(cForISS, nTamX3A2CD)+cLojaZero))
			Reclock("SA2",.T.)
			SA2->A2_FILIAL	:=	xFilial("SA2")
			SA2->A2_COD 	:=	cForISS
			SA2->A2_LOJA	:=	cLojaZero
			SA2->A2_NOME	:=	"MUNIC"
			SA2->A2_NREDUZ	:=	"MUNICIPIO"
			SA2->A2_MUN 	:=	"."
			SA2->A2_EST 	:=	"."
			SA2->A2_BAIRRO	:=	"."
			SA2->A2_END 	:=	"."
			MsUnlock()
		EndIf

		/*Natureza do ISS*/
	 	If SED->(!MsSeek(xFilial("SED")+PadR(cNatIss, TamSX3("ED_CODIGO")[1])))
			RecLock("SED",.T.)
			SED->ED_FILIAL  := xFilial("SED")
			SED->ED_CODIGO  := cNatIss
			SED->ED_CALCIRF := "N"
			SED->ED_CALCISS := "S"
			SED->ED_CALCINSS:= "N"
			SED->ED_DESCRIC := "ISS"
			MsUnlock()
		EndIf

		/*Titulo Referente ao ISS*/
		If SF1->F1_ISS > 0

			// Tratamento realizado para caso o titulo ja tenha sido gerado para o mesmo documento, dever· ser incrementado o prefixo.
			cPrefISS := GetNxtPrfImp( Padr( cPrefISS, nTamE2PREF ) , Padr( SF1->F1_DOC, nTamE2NUM ) , , Padr( "ISS", nTamE2TIPO ) , Padr( cForISS, nTamE2FORN ) , Padr( cLojaZero, nTamE2LOJA ) )
			aTit050 := {{"E2_FILIAL", xFilial("SE2"), NIL},;
							{"E2_PREFIXO", cPrefISS, NIL},;
							{"E2_NUM", SF1->F1_DOC, NIL},;
							{"E2_TIPO", "ISS", NIL},;
							{"E2_NATUREZ", cNatIss, NIL},;
							{"E2_FORNECE", cForISS, NIL},;
							{"E2_LOJA", cLojaZero, NIL},;
							{"E2_EMISSAO", SF1->F1_EMISSAO, NIL},;
							{"E2_VENCTO", SF1->F1_EMISSAO, NIL},;
							{"E2_VENCREA", SF1->F1_EMISSAO, NIL},;
							{"E2_VALOR", SF1->F1_ISS, NIL},;
							{"E2_TITPAI", cPreOr + cNumOr + cParOr + cTipOr + cForOr + cLojOr, NIL},;
							{"E2_ORIGEM", "MATA103", NIL}}
							//Adicionado E2_TITPAI, para que n„o se perca o vinculo com o titulo pai (nota de entrada)


			MsExecAuto({|x,y,z| FINA050(x,y,z)},aTit050,,3)

			If lMsErroAuto
				If !l103Auto
					MostraErro()
				EndIf
			Else
				aAdd(aTitImp,{SE2->(RecNo()),""})
			EndIf

			aTit050 := {}

		EndIf

	EndIf

	If SE2->E2_IRRF >= nVlRetIR  
		RecLock("SF1",.F.)
	    SF1->F1_VALIRF := SE2->E2_IRRF
		SF1->( MsUnlock() )
	EndIf

    oSX1 := FWSX1Util():New()
    oSX1:AddGroup("MTA103")
    oSX1:SearchGroup()
	aPergunte := oSX1:GetGroup("MTA103")

	If Len(aPergunte[2]) >= 27
		//Titulo do FASE-MT
		If MV_PAR27 == 1 .And. !Empty(cPreFase) .And. !Empty(cNatFase) .And. !Empty(cForFase)

			dbSelectArea("SA2")
			SA2->(dbSetOrder(1))

			dbSelectArea("SED")
			SED->(dbSetOrder(1))

			/*Fornecedor do FASE*/
			If SA2->(!MsSeek(xFilial("SA2")+PadR(cForFase, nTamX3A2CD)+cLojaZero)) 
				Reclock("SA2",.T.)
				SA2->A2_FILIAL	:=	xFilial("SA2")
				SA2->A2_COD 	:=	cForFase 
				SA2->A2_LOJA	:=	cLojaZero
				SA2->A2_NOME	:=	"MUNIC"
				SA2->A2_NREDUZ	:=	"MUNICIPIO"
				SA2->A2_MUN 	:=	"."
				SA2->A2_EST 	:=	"."
				SA2->A2_BAIRRO	:=	"."
				SA2->A2_END 	:=	"."
				MsUnlock()
			EndIf

			/*Natureza do FASE*/
			If SED->(!MsSeek(xFilial("SED")+PadR(cNatFase, TamSX3("ED_CODIGO")[1]))) 
				RecLock("SED",.T.)
				SED->ED_FILIAL  := xFilial("SED")
				SED->ED_CODIGO  := cNatFase
				SED->ED_CALCIRF := "N"
				SED->ED_CALCISS := "N"
				SED->ED_CALCINSS:= "N"
				SED->ED_DESCRIC := "FASE"
				MsUnlock()
			EndIf

			/*Titulo Referente ao FASE*/
			If SF1->F1_VALFASE > 0 //

				// Tratamento realizado para caso o titulo ja tenha sido gerado para o mesmo documento, dever· ser incrementado o prefixo.
				cPreFase := GetNxtPrfImp( Padr( cPreFase, nTamE2PREF ) , Padr( SF1->F1_DOC, nTamE2NUM ) , , Padr( "TX", nTamE2TIPO ) , Padr( cForFase, nTamE2FORN ) , Padr( cLojaZero, nTamE2LOJA ) )
				aTit050 := {{"E2_FILIAL", xFilial("SE2"), NIL},;
								{"E2_PREFIXO", cPreFase, NIL},;
								{"E2_NUM", SF1->F1_DOC, NIL},;
								{"E2_TIPO", "TX", NIL},; //
								{"E2_NATUREZ", cNatFase, NIL},; //
								{"E2_FORNECE", cForFase, NIL},; //
								{"E2_LOJA", cLojaZero, NIL},;
								{"E2_EMISSAO", SF1->F1_EMISSAO, NIL},;
								{"E2_VENCTO", SF1->F1_EMISSAO, NIL},;
								{"E2_VENCREA", SF1->F1_EMISSAO, NIL},;
								{"E2_VALOR", nValFase, NIL},;
								{"E2_TITPAI", cPreOr + cNumOr + cParOr + cTipOr + cForOr + cLojOr, NIL},;  
								{"E2_ORIGEM", "MATA103", NIL}}
								//Adicionado E2_TITPAI, para que n„o se perca o vinculo com o titulo pai (nota de entrada)


				MsExecAuto({|x,y,z| FINA050(x,y,z)},aTit050,,3)

				If lMsErroAuto
					If !l103Auto
						MostraErro()
					EndIf
				Else
					aAdd(aTitImp,{SE2->(RecNo()),""})
				EndIf

				aTit050 := {}

			EndIf

		EndIf
	EndIf

	//Grava o valor de retencao do PIS/COFINS/CSLL para contabilizacao
	If GetNewPar("MV_CTRETNF","1")=="2"
		RecLock("SF1")
	If cPaisLoc == "BRA"
		SF1->F1_VALPIS := aCtbRet[1]
		SF1->F1_VALCOFI := aCtbRet[2]
	EndIf
		SF1->F1_VALCSLL := aCtbRet[3]
	EndIf

	//GeraÁ„o dos recolhimentos dos tributos genÈricos calculados pelo motor de tributos Fiscal
	If lTrbGen

		If FindFunction("FisRetGen").And. lAliasCIN			
			//ObtÈm todos os tributos genÈricos calculados pelo motor Fiscal
			//ObtÈm todos os tributos genÈricos passÌveis de retenÁ„o
			//Percorre todos tributos genÈricos verificando se ele È passÌvel de retenÁ„o
			//Populo os arrays aTGCalcRet quando retenÁ„o e o aTGCalc para taxas
			FisRetGen(aTGCalc,aTGRet,.F.,{},aTGCalcRec,SF1->F1_EMISSAO, SF1->F1_DOC, SF1->F1_SERIE)
			
		Else

			//ObtÈm todos os tributos genÈricos calculados pelo motor Fiscal
			aTGCalc := MaFisRet(,"NF_TRIBGEN")

			//ObtÈm todos os tributos genÈricos passÌveis de retenÁ„o
			aTGRet	:= xFisRetTG(SF1->F1_EMISSAO)

			//Percorre todos tributos genÈricos verificando se ele È passÌvel de retenÁ„o
			For nContTg := 1 to Len(aTGCalc)
				//procuro pelo tributo genÈrico calculado na lista dos tributos passÌveis de retenÁ„o			
				//Se n„o encontrar tributo na lista dos passiveis de retenÁ„o, trata-se de um recolhimento e os valores ser„o adicionados no aTGCalcRec.
				If AScan(aTGRet, { |x| Alltrim(x[1]) == Alltrim(aTGCalc[nContTg][1])}) == 0 .AND. !Empty(aTGCalc[nContTg][4])
					// Se o tributo n„o È uma retenÁ„o, ou seja, È um recolhimento, adiciono no array aTGCalcRec para que os tÌtulos
					// sejam gerados posteriormente.
					cNumTitTG := xFisTitTG()
					cHistRec := AllTrim(aTGCalc[nContTg][1]) + " - NF: " + AllTrim(SF1->F1_DOC) + " / " + AllTrim(SF1->F1_SERIE)

					aAdd(aTGCalcRec, {aTGCalc[nContTg][4],; // CÛdigo da Regra FKK
										aTGCalc[nContTg][3],; // Valor do tributo
										cNumTitTG,; // N˙mero do tÌtulo a ser gerado
										'',; // ID FK7 do tÌtulo gerado -> SÛ usar como retorno.
										aTGCalc[nContTg][5],; //ID da regra Fiscal da tabela F2B
										cHistRec}) // HistÛrico para gravar no tÌtulo

				EndIf

			Next nContTg

		EndIf

		// Faz a chamda da FGrvImpFi para gerar os recolhimentos no financeiro e da xFisF2F p/
		// gravar a tabela TÌtulo x NF do Fiscal (F2F).
		If lTrbGenFin .And. Len(aTGCalcRec) > 0 .And. SF1->(FieldPos('F1_IDNF')) > 0
			FGrvImpFi(@aTGCalcRec, "MATA100", dDatabase)
			xFisF2F("I", SF1->F1_IDNF, "SF1", aTGCalcRec)
		EndIf

		//Aqui chamo a funÁ„o para fazer tratamento da geraÁ„o das Guias.
		If cPaisLoc == "BRA" .AND. FindFunction("xFisAddGNRE") .And. lAliasCIN
			xFisAddGNRE(SF2->(RECNO()), "SF2",aTGCalcRec)
		EndIF

	EndIf
	
	//GravaÁ„o Tabela Intermediaria NF x Natureza Rendimento x Impostos
	If Len(aRecGerSE2) > 0 .And. ChkFile("FKW") .And. FindFunction("A103FKW") .And. ChkFile("DHR")
		A103FKW("I",aCols,aRecGerSE2)
	Endif
Else
	//Estorno dos titulos a pagar
	DEFAULT aRecSE2 := {}

	//Busca titulo CIDE e inclui seu Recno no array aRecSE2 para ser excluido junto com os demais titulos
	If lCide .And. Len(aRecSE2) > 0 .And. cPaisLoc == "BRA"
		DbSelectArea("SE2")
		MsGoto(aRecSE2[1])
		DbSetOrder(1)
		If (MsSeek(xFilial("SE2")+SE2->E2_PREFIXO+SE2->E2_NUM+SE2->E2_PARCCID+"CID"+cForCIDE))
			AADD(aRecSE2,SE2->(Recno()))
		EndIf
	EndIf
	
	//Exclus„o Tabela Intermediaria NF x Natureza Rendimento x Impostos
	If Len(aRecSE2) > 0 .And. ChkFile("FKW") .And. FindFunction("A103FKW") .And. ChkFile("DHR")
		A103FKW("E",,aRecSE2)
	Endif

	If __lIntPFS .And. FindFunction("JURA281")
		JURA281(.T., 5, aRecSE2)
	EndIf
	
	For nX := 1 To Len(aRecSE2)
		//Estorno dos titulos financeiros
		DbSelectArea("SE2")
		MsGoto(aRecSE2[nX])

		//Gravacao de registros do SE5 na exclusao C.Pagar
		MT103GrvSE5()
		
		//realiza a exclusao da tabela complementar de titulos (FKF)
		If cPaisLoc == "BRA" .and. AliasInDic("FKF") .And. FindFunction("Fa986Excl")
			Fa986Excl("SE2")
		EndIf
		
		//Template acionando ponto de entrada
		If ExistTemplate("M103DSE2")
			ExecTemplate("M103DSE2",.F.,.F.)
		EndIf

		If (Existblock("M103DSE2"))
			ExecBlock("M103DSE2",.F.,.F.)
		EndIf
		
		If SE2->E2_MULTNAT <> "1"
			AtuSldNat(SE2->E2_NATUREZ, SE2->E2_VENCREA, SE2->E2_MOEDA, If(SE2->E2_TIPO $ MVPAGANT+"/"+MV_CPNEG,"3","2"), "P", SE2->E2_VALOR, SE2->E2_VLCRUZ, If(SE2->E2_TIPO $ MVABATIM, "+", "-"),,FunName(),"SE2", SE2->(Recno()),nOpca)
		Endif

		If __lIntPFS .And. FindFunction("J281DelImp")
			J281DelImp(SE2->(Recno()))
		EndIf
		
		MsDocument( "SE2", SE2->( RecNo() ), 2, , 3 )
		RecLock("SE2",.F.)
		FinGrvEx("P")
		dbDelete()
		
		FaAvalSE2(2, "MATA100")
		FaAvalSE2(3, "MATA100")
	Next nX

	//verificacao SIGAPLS
	if lPLSMT103 
		PLSMT103(4) 
	endIf

EndIf

RestArea(aAreaSA2)
RestArea(aArea)

Return(.T.)

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103RatVEI≥ Autor ≥Patricia A. Salomao     ≥ Data ≥19.11.2001≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Monta a tela rateios por Veiculo/Viagem                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103 / MATA240 / MATA241                                 ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ0ﬂﬂﬂﬂﬂﬂ
*/
Function a103RatVei()

Local bSavKeyF4   := SetKey(VK_F4,Nil)
Local bSavKeyF5   := SetKey(VK_F5,Nil)
Local bSavKeyF6   := SetKey(VK_F6,Nil)
Local bSavKeyF7   := SetKey(VK_F7,Nil)
Local bSavKeyF8   := SetKey(VK_F8,Nil)
Local bSavKeyF9   := SetKey(VK_F9,Nil)
Local bSavKeyF10  := SetKey(VK_F10,Nil)
Local bSavKeyF11  := SetKey(VK_F11,Nil)
Local aSavaRotina := aClone(aRotina)
Local nOpc		  := 0
Local nY,nT,nX
Local oDlg, oGetDados
Local nPosItem
Local nPosRat
Local nPosRatFro
Local nItem
Local nOpcx
Local cCposSDG		:= ""
Local aCposSDG		:= {}
Local lRet			:= .T.
Local lMA103SDG		:= ExistBlock("MA103SDG")
Local nCont			:= 0
Local nPosGRV		:= 0

Private aSavCols	:= {}
Private aSavHeader	:= {}
Private nSavN		:= 0
Private nTotValor	:= 0
Private M->DG_CODDES := CriaVar("DG_CODDES")  //-- Esta variavel e' utilizada pelo programa TMSA070

If Type("aSDGGrava") == "U"
	Private	aSDGGrava := {}
EndIf

If l240 .Or. l241
	nPosItem	  := If(l241,StrZero(n,Len(SDG->DG_ITEM)),StrZero(1,Len(SDG->DG_ITEM)) )
	nPosRat	      := aScan(aRatVei,{|x| x[1] == nPosItem })
	nPosRatFro    := aScan(aRatFro,{|x| x[1] == nPosItem })
	nItem         := nPosItem
Else
	nPosItem	  := GetPosSD1("D1_ITEM" )
	nPosRat	      := aScan(aRatVei,{|x| x[1] == aCols[n][nPosItem] })
	nPosRatFro    := aScan(aRatFro,{|x| x[1] == aCols[n][nPosItem] })
	nItem         := aCols[n][nPosItem]
EndIf

If !l240
	aSavCols 	  := aClone(aCols)
	aSavHeader	  := aClone(aHeader)
	nSavN	  	  := n
EndIf

If nPosRatFro > 0
	For nY := 1 To Len(aRatFro)
		If aRatFro[nY][1] == nItem
			For nT := 1 to Len(aRatFro[nY][2])
				If !aRatFro[nY][2][nT] [Len(aRatFro[nY][2][nT])] //Verifica se nao esta deletado
					Help(" ",1,"A103RATFRO") // "Foi Informado Rateio por Frota"
					lRet := .F.
					Exit
				EndIf
			Next nT
		EndIf
		If !lRet
			Exit
		EndIf
	Next
EndIf

If lRet
	n        := 1
	aCols	   := {}
	aHeader	:= {}

	If FwIsInCallStack("MATA116")
		aRotina[1][4]	:= 3
		aRotina[2][4]	:= 2
	Elseif FwIsInCallStack("A150Digita") .Or. FwIsInCallStack("PCOA050")
        aRotina[1][4]   := 2 
	Else
		aRotina[2][4]	:= 2
		aRotina[3][4]	:= 3
	Endif

	//Montagem do aHeader
	cCposSDG := "DG_ITEM|DG_CODVEI|DG_FILORI|DG_VIAGEM|DG_TOTAL"
	If Inclui .Or. l103Class //-- Estes campos so' deverao ser mostrados na inclusao do Rateio
		cCposSDG += "|DG_COND|DG_NUMPARC|DG_PERVENC"
	EndIf

	If lMA103SDG    //-- Ponto de Entrada para adicionar campos no aHeader do SDG.
		aCposSDG := ExecBlock("MA103SDG",.F.,.F.,cCposSDG)
		If ValType(aCposSDG) == "A"
			For nCont := 1 To Len(aCposSDG)
				cCposSDG += "|" + aCposSDG[nCont]
			Next nCont
		EndIf
	EndIf

	DbSelectArea("SX3")
	DbSetOrder(1)
	MsSeek("SDG")
	While !EOF() .And. (x3_arquivo == "SDG")
		IF X3USO(x3_usado) .And. cNivel >= x3_nivel .And. Alltrim(x3_campo)$ cCposSDG
			AADD(aHeader,{ TRIM(x3titulo()), x3_campo, x3_picture,;
				x3_tamanho, x3_decimal, x3_valid,;
				x3_usado, x3_tipo, x3_arquivo,x3_context } )
		EndIf
		dbSkip()
	EndDo

	//Estrutura do Array aRatVei:
	//aRatVei[n,1] - Item da Nota
	//aRatVei[n,2] - aCols do Rateio de Veiculo/Viagem
	//aRatVei[n,3] - Codigo da Despesa de Transporte
	//aRatVei[n,4] - Valor Total informado no Rateio
	If nPosRat > 0
		aCols	     := aClone(aRatVei[nPosRat][2])
		M->DG_CODDES := aRatVei[nPosRat][3]
	Else
		//Faz a montagem de uma linha em branco no aCols.
		aadd(aCols,Array(Len(aHeader)+1))
		For ny := 1 to Len(aHeader)
			If Trim(aHeader[ny][2]) == "DG_ITEM"
				aCols[1][ny] 	:= "01"
			Else
				aCols[1][ny] := CriaVar(aHeader[ny][2])
			EndIf
			aCols[1][Len(aHeader)+1] := .F.
		Next ny
	EndIf

	If !(Type('l103Auto') <> 'U' .And. l103Auto)

		//Monta Dialog                                                 ≥
		DEFINE MSDIALOG oDlg FROM 000,000 TO 250,735 TITLE STR0120 Of oMainWnd PIXEL //'Rateio por Veiculo/Viagem'

		// Calcula dimensıes                                            ≥
		oSize := FwDefSize():New(.T.,,,oDlg)

		oSize:AddObject( "CABECALHO",  100, 20, .T., .T. ) // Totalmente dimensionavel
		oSize:AddObject( "GETDADOS" ,  100, 80, .T., .T. ) // Totalmente dimensionavel

		oSize:lProp 	:= .T. // Proporcional
		oSize:aMargins 	:= { 3, 3, 3, 3 } // Espaco ao lado dos objetos 0, entre eles 3

		oSize:Process() 	   // Dispara os calculos

		If l240 .Or. l241
			nOpcx := IIf(Inclui,3,2)

			@ oSize:GetDimension("CABECALHO","LININI")+3	,oSize:GetDimension("CABECALHO","COLINI")   	SAY STR0121  Of oDlg PIXEL SIZE 56 ,9 //"Codigo da Despesa : "
			@ oSize:GetDimension("CABECALHO","LININI") 	,oSize:GetDimension("CABECALHO","COLINI")+53 	MSGET M->DG_CODDES  Picture PesqPict("SDG","DG_CODDES") F3 CpoRetF3('DG_CODDES');
												When Inclui Valid CheckSX3('DG_CODDES',M->DG_CODDES,.T.) ;
												OF oDlg PIXEL SIZE 60 ,9
			oGetDados :=   MSGetDados():New(oSize:GetDimension("GETDADOS","LININI"),oSize:GetDimension("GETDADOS","COLINI"),;
	     							   			 oSize:GetDimension("GETDADOS","LINEND"),oSize:GetDimension("GETDADOS","COLEND"),;
												 nOpcx,'A103VeiLOK()','A103VeiTOK()','+DG_ITEM',.T.,,,,100,,,,If(nOpcx==2,"AlwaysFalse",NIL))
		Else
			@ oSize:GetDimension("CABECALHO","LININI")+2	,oSize:GetDimension("CABECALHO","COLINI")+126 SAY OemToAnsi(STR0072) Of oDlg PIXEL SIZE 56 ,9 //"Documento : "
			@ oSize:GetDimension("CABECALHO","LININI")+2 	,oSize:GetDimension("CABECALHO","COLINI")+215 SAY OemToAnsi(STR0073) Of oDlg PIXEL SIZE 20 ,9 //"Item :"
			@ oSize:GetDimension("CABECALHO","LININI")+2 	,oSize:GetDimension("CABECALHO","COLINI")+160 SAY cNFiscal 	Of oDlg PIXEL SIZE 70 ,9
			@ oSize:GetDimension("CABECALHO","LININI")+2 	,oSize:GetDimension("CABECALHO","COLINI")+230 SAY aSavCols[nSavN][nPosItem] Of oDlg PIXEL SIZE 37 ,9
			@ oSize:GetDimension("CABECALHO","LININI")+2 	,oSize:GetDimension("CABECALHO","COLINI")     SAY STR0121 Of oDlg PIXEL SIZE 56 ,9 //"Codigo da Despesa : "
			@ oSize:GetDimension("CABECALHO","LININI") 	    ,oSize:GetDimension("CABECALHO","COLINI")+53 MSGET M->DG_CODDES  Picture PesqPict(STR0122,"DG_CODDES") F3 CpoRetF3('DG_CODDES'); //"SDG"
												When !l103Visual  Valid CheckSX3('DG_CODDES',M->DG_CODDES,.T.) ;
												OF oDlg PIXEL SIZE 60 ,9
			oGetDados := MSGetDados():New(oSize:GetDimension("GETDADOS","LININI"),oSize:GetDimension("GETDADOS","COLINI"),;
	     							   			oSize:GetDimension("GETDADOS","LINEND"),oSize:GetDimension("GETDADOS","COLEND"),;
												IIF(l103Visual,2,3),'A103VeiLOK()','A103VeiTOK()','+DG_ITEM',.T.,,,,100,,,,If(l103Visual,"AlwaysFalse",NIL))
		EndIf

		ACTIVATE MSDIALOG oDlg ON INIT (oGetdados:Refresh(),EnchoiceBar(oDlg,   {||IIF(oGetDados:TudoOk(),(nOpc:=1,oDlg:End()),(nOpc:=0))},{||oDlg:End()}) )

	Else
		nOpc := 1
	EndIf

	If nOpc == 1 .And. IIf(l240 .Or. l241, nOpcx<>2, !l103Visual)
		If nPosRat > 0
			aRatVei[nPosRat][2]	:= aClone(aCols)
			aRatVei[nPosRat][3]	:= 	M->DG_CODDES
		Else
			aADD(aRatVei,{ IIf( l240.Or.l241,nPosItem,aSavCols[nSavN][nPosItem] ) , aClone(aCols), M->DG_CODDES, nTotValor })
		EndIf
	EndIf

	For  nX := 1 to Len(aCposSDG)
		
		nPosGRV	  := GetPosSD1(aCposSDG[nX] )
		
		If nPosGRV > 0
			aadd(aSDGGrava,{aCposSDG[nX],acols[nX][nPosGRV]})
		Endif
	NEXT
	
	aRotina	:= aClone(aSavaRotina)
	aCols	:= aClone(aSavCols)
	aHeader	:= aClone(aSavHeader)
	n		:= nSavN

EndIf
SetKey(VK_F4,bSavKeyF4)
SetKey(VK_F5,bSavKeyF5)
SetKey(VK_F6,bSavKeyF6)
SetKey(VK_F7,bSavKeyF7)
SetKey(VK_F8,bSavKeyF8)
SetKey(VK_F9,bSavKeyF9)
SetKey(VK_F10,bSavKeyF10)
SetKey(VK_F11,bSavKeyF11)

Return(lRet)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103VeiLOk≥ Autor ≥Patricia A. Salomao     ≥ Data ≥18.06.2002≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Valida a Linha Digitada                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103 / MATA240 / MATA241                                 ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103VeiLOk()
Local lRet := .T.
Local cSeek:= ""
Local lIdent := nModulo<>43

If !GdDeleted(n)

	//-- Analisa se ha itens duplicados na GetDados.
	If Inclui
		If lIdent
			lRet := GDCheckKey( { "DG_CODVEI","DG_IDENT" }, 4 )
		Else
			lRet := GDCheckKey( { "DG_CODVEI","DG_FILORI","DG_VIAGEM" }, 4 )
		EndIf
	EndIf

	If lRet
		If (Empty(GdFieldGet('DG_CODVEI',n)) .And. Iif(lIdent, Empty( GdFieldGet('DG_IDENT',n)) ,Empty(GdFieldGet('DG_VIAGEM',n)))) .Or. ;
				Empty(GdFieldGet('DG_TOTAL',n) )
			Help('',1,'OBRIGAT2',,RetTitle('DG_CODVEI')+' '+Iif(lIdent,RetTitle('DG_IDENT'),RetTitle('DG_VIAGEM'))+' '+RetTitle('DG_TOTAL'),04,01) //Um ou alguns campos obrigatorios nao foram preenchidos no Browse
			lRet := .F.
		EndIf
		//Valida se o veiculo informado esta amarrado na viagem, caso a mesma seja informada
		If lRet .And. !Empty(GdFieldGet('DG_CODVEI',n)) .And. Iif(lIdent,!Empty(GdFieldGet('DG_IDENT',n)),!Empty(GdFieldGet('DG_VIAGEM',n)))
			If lIdent
				cSeek :=  GDFieldGet( 'DG_IDENT', n ) + GdFieldGet('DG_CODVEI',n)
			Else
				cSeek :=  GDFieldGet( 'DG_FILORI', n ) +  GDFieldGet( 'DG_VIAGEM', n ) + GdFieldGet('DG_CODVEI',n)
			EndIf
			DTR->(DbSetOrder(3))
			If DTR->(!MsSeek(xFilial("DTR")+cSeek))
				Help(" ",1,"TMSA07013") //-- O veiculo nao existe no complemento da viagem.
				lRet:= .F.
			EndIf
		EndIf
	EndIf

	If lRet .And. !Empty(GdFieldGet('DG_FILORI',n)) .And. !Empty(GdFieldGet('DG_VIAGEM',n))
		lRet := TMSChkViag(GdFieldGet('DG_FILORI',n),GdFieldGet('DG_VIAGEM',n),.F.,.F.,.F.,.T.,.F.,.F.,.F.,.F.,.F.,,.F.,.F.,.F.,.F.,.F.,.F.)
	EndIf

EndIf

Return(lRet)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103VeiTOk≥ Autor ≥Patricia A. Salomao     ≥ Data ≥19.11.2001≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥TudOk da GetDados da Tela de rateios por Veiculo/Viagem      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103 / MATA240 / MATA241                                 ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103VeiTOk()
Local nx:=0
Local nPosValor  := GdFieldPos("DG_TOTAL" )
Local nPosCodVei := GdFieldPos("DG_CODVEI")
Local nPosViagem := GdFieldPos("DG_VIAGEM")
Local nPosIdent  := GdFieldPos("DG_IDENT")
Local lRet       := .T.
Local nPosValRat := 0
Local lIdent	 := nModulo<>43

nTotValor := 0
For nx := 1 to Len(aCols)
	If !GdDeleted(nx)
		nTotValor += aCols[nx][nPosValor]
	EndIf
Next

If !l240 .And. !l241
	nPosValRat  := Ascan(aSavHeader,{|x| AllTrim(x[2]) == "D1_TOTAL"} )
	If nPosValRat > 0 .And. nTotValor > 0 .And. nTotValor <> aSavCols[nSavN][nPosValRat]
		Help(' ', 1, 'A103TOTRAT') // Valor a ser rateado nao confere com o total.
		lRet := .F.
	EndIf
EndIf

If lRet .And. !GdDeleted(n) .And. Empty(aCols[n][nPosCodVei]) .And. Iif(lIdent,Empty(aCols[n][nPosIdent]),Empty(aCols[n][nPosViagem]))
	Help(' ', 1, 'A103VEVIVA') // Os Campos de Veiculo e Viagem estao Vazios.
	lRet := .F.
EndIf

Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103Frota ≥ Autor ≥Patricia A. Salomao     ≥ Data ≥20.11.2001≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Monta a tela de rateio por Frota                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103 / MATA240 / MATA241                                 ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function a103Frota()
Local oDlg		:= NIL
Local nY			:= 0
Local nT			:= 0
Local aRet		:= {}
Local nOpc		:= 0
Local nPosItem	:= 0
Local nPosValor	:= 0
Local nPosRat		:= 0
Local nPosRatVei	:= 0
Local nItem		:= 0
Local lRet		:= .T.
Local oSize		:= NIL

Private M->DG_CODDES:= CriaVar("DG_CODDES") //-- Esta variavel e' utilizada pelo programa TMSA070

If l240 .Or. l241
	nPosItem	 := If(l241,StrZero(n,Len(SDG->DG_ITEM)),StrZero(1,Len(SDG->DG_ITEM)) )
	nPosRat	     := aScan(aRatFro,{|x| x[1] == nPosItem })
	nPosRatVei   := aScan(aRatVei,{|x| x[1] == nPosItem })
	nItem        := nPosItem
	nPosValor    := 100
Else
	nPosItem	 := GetPosSD1("D1_ITEM" )
	nPosRat	     := aScan(aRatFro,{|x| x[1] == aCols[n][nPosItem] })
	nPosRatVei   := aScan(aRatVei,{|x| x[1] == aCols[n][nPosItem]})
	nItem        := aCols[n][nPosItem]
	nPosValor    := GetPosSD1("D1_TOTAL")
EndIf

If nPosRatVei > 0
	For nY := 1 To Len(aRatVei)
		If aRatVei[nY][1] == nItem
			For nT := 1 to Len(aRatVei[nY][2])
				If !aRatVei[nY][2][nT] [Len(aRatVei[nY][2][nT])] //Verifica se nao esta deletado
					Help("",1,"A103RATVEI") // "Foi Informado Rateio por Veiculo/Viagem"
					lRet := .F.
					Exit
				EndIf
			Next nT
		EndIf
		If !lRet
			Exit
		EndIf
	Next
EndIf

If lRet
	//Estrutura do Array aRatFro:
	//aRatFro[n,1] - Item da Nota
	//aRatFro[n,2] - aCols do Rateio de Frota
	//aRatFro[n,3] - Codigo da Despesa de Transporte
	If nPosRat > 0
		aRet	 := aClone(aRatFro[nPosRat][2])
		M->DG_CODDES := aRatFro[nPosRat][3]
	Else
		//Faz a montagem de uma linha em branco no aCols.
		AAdd(aRet,{"01",IIf(l240 .Or.  l241, nPosValor,aCols[n][nPosValor]),.F.})
	EndIf

	If !(Type('l103Auto') <> 'U' .And. l103Auto)

		DEFINE MSDIALOG oDlg TITLE STR0123 Of oMainWnd PIXEL FROM 94 ,20 TO 250,670 //'Rateio por Frota'

		oSize := FWDefSize():New(.T.,,,oDlg) //passa para FWDefSize a dialog usada para calcular corretamente as proporÁıes dos objetos
		oSize:AddObject( "Panel", 100, 100, .T., .T. ) //Panel 1 em 50% da tela
		oSize:lProp := .T. //permite redimencionar as telas de acordo com a proporÁ„o do AddObject
		oSize:Process() //executa os calculos

		If l240 .Or. l241
			@ oSize:GetDimension("Panel","LININI")+10,oSize:GetDimension("Panel","COLINI")  SAY STR0121  Of oDlg PIXEL SIZE 56 ,9 //"Codigo da Despesa : "
			@ oSize:GetDimension("Panel","LININI")+10,oSize:GetDimension("Panel","COLINI")+60 MSGET M->DG_CODDES  Picture PesqPict("SDG","DG_CODDES") F3 CpoRetF3('DG_CODDES');
				When Inclui Valid CheckSX3('DG_CODDES',M->DG_CODDES) ;
				OF oDlg PIXEL SIZE 60 ,9
		Else
			@ oSize:GetDimension("Panel","LININI")+18,oSize:GetDimension("Panel","COLINI")+3   SAY OemToAnsi(STR0072) Of oDlg PIXEL SIZE 56 ,9 //"Documento : "
			@ oSize:GetDimension("Panel","LININI")+18,oSize:GetDimension("Panel","COLINI")+96  SAY OemToAnsi(STR0073) Of oDlg PIXEL SIZE 20 ,9 //"Item :"
			@ oSize:GetDimension("Panel","LININI")+18,oSize:GetDimension("Panel","COLINI")+36  SAY Substr(cSerie,1,3)+" "+cNFiscal Of oDlg PIXEL SIZE 70 ,9
			@ oSize:GetDimension("Panel","LININI")+18,oSize:GetDimension("Panel","COLINI")+115 SAY aCols[n][nPosItem] Of oDlg PIXEL SIZE 37 ,9
			@ oSize:GetDimension("Panel","LININI")+30,oSize:GetDimension("Panel","COLINI")+3   SAY STR0121  Of oDlg PIXEL SIZE 56 ,9 //"Codigo da Despesa : "
			@ oSize:GetDimension("Panel","LININI")+30,oSize:GetDimension("Panel","COLINI")+60  MSGET M->DG_CODDES  Picture PesqPict("SDG","DG_CODDES") F3 CpoRetF3('DG_CODDES');
				When !l103Visual  Valid CheckSX3('DG_CODDES',M->DG_CODDES) ;
				OF oDlg PIXEL SIZE 60 ,9
		EndIf

		ACTIVATE MSDIALOG oDlg ON INIT EnchoiceBar(oDlg,{||(nOpc:=1,oDlg:End())},{||oDlg:End()} )
	Else
		nOpc := 1
	EndIf
	If nOpc == 1
		If nPosRat > 0
			aRatFro[nPosRat][2]	:= aClone(aRet)
			aRatFro[nPosRat][3]	:= M->DG_CODDES
		Else
			AAdd(aRatFro,{ IIf( l240.Or.l241,nPosItem,aCols[n][nPosItem] ) , aClone(aRet), M->DG_CODDES })
		EndIf
	EndIf
EndIf
Return (lRet)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103GrvSDG≥ Autor ≥Patricia A. Salomao     ≥ Data ≥20.11.2001≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Grava no SDG o Rateio por Veiculo/Viagem e o Rateio por Frota≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpC1- Alias do Arquivo                                      ≥±±
±±≥          ≥ExpA1- Array contendo os Rateios informados na Tela de Rateio≥±±
±±≥          ≥ExpC2- Tipo do Rateio (V=Veiculo/Viagem ; F=Frota)           ≥±±
±±≥          ≥ExpC3- Item do SD1 ou SD3 que esta sendo gravado             ≥±±
±±≥          ≥ExpL1- Lancamento Contabil OnLine (mv_par06)                 ≥±±
±±≥          ≥ExpN1- Cabecalho do Lancamento Contabil                      ≥±±
±±≥          ≥ExpN2- Total do Lancamento Contabil (@)                      ≥±±
±±≥          ≥ExpC4- Lote para Lancamento Contabil                         ≥±±
±±≥          ≥ExpC5- Programa que esta executando a funcao                 ≥±±
±±≥          ≥ExpD1- Data de emissao inicial                 			      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103 / MATA240 / MATA241                                 ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103GrvSDG(cAlias,aArraySDG,cTpRateio,cItem,lCtbOnLine,nHdlPrv,nTotalLcto,cLote,cProg,dDataEmi)

Local nValRat    := 0
Local aCustoVei  := {}
Local aRecSDGBai := {}
Local aRecSDGEmi := {}
Local nW,nT,cCodDesp,cDoc
Local aParcelas  := {}
Local nParcela   := 0
Local nPerVenc   := 0
Local dDataVenc  := dDataBase
Local nCnt       := 0
Local cCond      := ""
Local cCodVei    := ""
Local cFilOri    := ""
Local cViagem    := ""
Local cIdent	 := ""
Local lBaixa     := .F.
Local lMovim     := .F.
Local nValCob    := 0
Local nTotValCob := 0
Local nSbCusto1  := 0
Local nValTotRat := 0
Local nPerc      := 0
Local nTotPerc   := 0
Local nSbCusto2  := 0
Local nSbCusto3  := 0
Local nSbCusto4  := 0
Local nSbCusto5  := 0
Local nCntFor    := 0
Local nCntCpo	 := 0
Local nDecCusto1 := TamSx3("DG_CUSTO1")[2]
Local nDecCusto2 := TamSx3("DG_CUSTO2")[2]
Local nDecCusto3 := TamSx3("DG_CUSTO3")[2]
Local nDecCusto4 := TamSx3("DG_CUSTO4")[2]
Local nDecCusto5 := TamSx3("DG_CUSTO5")[2]
Local nDecValCob := TamSx3("DG_VALCOB")[2]
Local nDecPerc   := TamSx3("DG_PERC")[2]

DEFAULT aArraySDG  := {}
DEFAULT cTpRateio  := ""
DEFAULT nTotalLcto := 0
DEFAULT lCtbOnLine := .F.
DEFAULT nHdlPrv    := 0
DEFAULT cLote      := ""
DEFAULT cProg      := "MATA103"
DEFAULT dDataEmi   := dDataBase

dDataVenc := dDataEmi

If Type("aSDGGrava") == "U"
	aSDGGrava := {}
EndIf

For nW := 1 to Len(aArraySDG)
	cCodDesp := aArraySDG[nW][3] //-- Despesa
	cDoc     := NextNumero("SDG",1,"DG_DOC",.T.)
	If cTpRateio=="V"
		nValTotRat := aArraySDG[nW][4] //-- Valor Total do Rateio
	Else
		nValTotRat := IIf(cAlias=="SD1", SD1->D1_TOTAL, SD3->D3_CUSTO1)
	EndIf
	For  nT:=1 to Len(aArraySDG[nW][2])
		If aArraySDG[nW][1] == cItem .And. !(aArraySDG[nW][2][nT] [Len(aArraySDG[nW][2][nT])]) // Verifica se esta deletado
			aCustoVei  := Array(6)
			If cTpRateio=="V"
				cCodVei  := aArraySDG[nW][2][nT][2] //-- Codigo Veiculo
				cFilOri  := aArraySDG[nW][2][nT][3] //-- Filial Origem
				cViagem  := aArraySDG[nW][2][nT][4] //-- Viagem
				cCond    := aArraySDG[nW][2][nT][6] //-- Condicao
				nParcela := aArraySDG[nW][2][nT][7] //-- Numero Parcelas
				nPerVenc := aArraySDG[nW][2][nT][8] //-- Periodo Vencimento
				If nModulo==39
					cIdent	 := aArraySDG[nW][2][nT][10]//-- Identificador Viagem/Carga
				EndIf
			EndIf
			If cAlias == 'SD1'
				nValRat := If(cTpRateio=="V",aArraySDG[nW][2][nT][5], SD1->D1_TOTAL ) //-- Valor do Rateio
				lMovim  := .F.
			ElseIf cAlias == 'SD3'
				nValRat := If(cTpRateio=="V",aArraySDG[nW][2][nT][5], SD3->D3_CUSTO1 ) //-- Valor do Rateio
				lMovim  := .T.
			EndIf
			
			//Atualiza o arquivo SDG - Movim. de Custo de Transporte (Integracao TMS)
			//Retorna a quantidade de parcelas
			aParcelas := {}
			If cTpRateio == "V"
				If !Empty(cCond)
					aParcelas:= Condicao(nValRat,cCond,,dDataEmi)
				Else
					nParcela  := Iif(nParcela==0,1,nParcela) //-- Inicializa o numero de parcelas
					nDataVenc := dDataBase
					For nCnt := 1 To nParcela
						dDataVenc := dDataVenc + nPerVenc
						Aadd( aParcelas, { dDataVenc, nValRat / nParcela } )
					Next nCnt
				EndIf
			Else
				Aadd( aParcelas, { dDataBase, nValRat } )
			EndIf

			nPerc        := Round( (nValRat / nValTotRat) * 100, nDecPerc )    //-- Percentual Total do Item
			aCustoVei[6] := Round( nPerc / Len(aParcelas ) , nDecPerc ) //-- Percentual de cada Parcela do item

			If cAlias == 'SD1'
				//-- Armazena o Total do custo
				nSbCusto1 := ( ( SD1->D1_CUSTO  * nPerc ) / 100 )
				nSbCusto3 := ( ( SD1->D1_CUSTO2 * nPerc ) / 100 )
				nSbCusto4 := ( ( SD1->D1_CUSTO3 * nPerc ) / 100 )
				nSbCusto5 := ( ( SD1->D1_CUSTO4 * nPerc ) / 100 )
				nSbCusto5 := ( ( SD1->D1_CUSTO5 * nPerc ) / 100 )

				//-- Rateio das parcelas
				aCustoVei[1] := Round( ( (SD1->D1_CUSTO  * nPerc) / 100 ) / Len(aParcelas), nDecCusto1 )
				aCustoVei[2] := Round( ( (SD1->D1_CUSTO2 * nPerc) / 100 ) / Len(aParcelas), nDecCusto2 )
				aCustoVei[3] := Round( ( (SD1->D1_CUSTO3 * nPerc) / 100 ) / Len(aParcelas), nDecCusto3 )
				aCustoVei[4] := Round( ( (SD1->D1_CUSTO4 * nPerc) / 100 ) / Len(aParcelas), nDecCusto4 )
				aCustoVei[5] := Round( ( (SD1->D1_CUSTO5 * nPerc) / 100 ) / Len(aParcelas), nDecCusto5 )
			Else
				//-- Armazena o Total do custo
				nSbCusto1 := ( ( SD3->D3_CUSTO1 * nPerc ) / 100 )
				nSbCusto2 := ( ( SD3->D3_CUSTO2 * nPerc ) / 100 )
				nSbCusto3 := ( ( SD3->D3_CUSTO3 * nPerc ) / 100 )
				nSbCusto4 := ( ( SD3->D3_CUSTO4 * nPerc ) / 100 )
				nSbCusto5 := ( ( SD3->D3_CUSTO5 * nPerc ) / 100 )

				//-- Rateio das parcelas
				aCustoVei[1] := Round( ( (SD3->D3_CUSTO1 * nPerc)  / 100 ) / Len(aParcelas), nDecCusto1 )
				aCustoVei[2] := Round( ( (SD3->D3_CUSTO2 * nPerc)  / 100 ) / Len(aParcelas), nDecCusto2 )
				aCustoVei[3] := Round( ( (SD3->D3_CUSTO3 * nPerc)  / 100 ) / Len(aParcelas), nDecCusto3 )
				aCustoVei[4] := Round( ( (SD3->D3_CUSTO4 * nPerc)  / 100 ) / Len(aParcelas), nDecCusto4 )
				aCustoVei[5] := Round( ( (SD3->D3_CUSTO5 * nPerc)  / 100 ) / Len(aParcelas), nDecCusto5 )
			EndIf

			nTotValCob   := nValRat  //-- Valor Total do Item
			nValCob      := Round(nValRat / Len(aParcelas), nDecValCob ) //-- Valor de cada parcela

			//-- E' necessario controlar a diferenca de arrendondamento no calculo do Percentual dos itens informados na Tela de Rateio
			//-- ( a soma do percentual dos itens deve ser igual a 100%) e controlar a diferenca de arrendondamento no calculo do percentual
			//-- das parcelas de cada Item (a soma dos percentuais das parcelas tem que ser igual ao percentual Total do item)

			//-- Gravacao das parcelas
			For nCnt := 1 To Len(aParcelas)
				lBaixa := .F.
				//-- Atualiza os itens
				If Val(cNewItSDG) == 0
					cNewItSDG := aArraySDG[nW][2][nT][1] //-- Item
				Else
					cNewItSDG := Soma1(cNewItSDG)
					aArraySDG[nW][2][nT][1] := cNewItSDG
				EndIf

				//-- Para evitar diferenca de arrendamento, armazena a sobra do rateio na ultima parcela
				If nCnt == Len(aParcelas)
					aCustoVei[1]	:= nSbCusto1
					aCustoVei[2]	:= nSbCusto2
					aCustoVei[3]	:= nSbCusto3
					aCustoVei[4]	:= nSbCusto4
					aCustoVei[5]	:= nSbCusto5
					//-- Se for a Ultima Parcela do Ultimo Item
					If Len(aArraySDG[nW][2]) > 1 .And. nT == Len(aArraySDG[nW][2])
						nPerc     := 100 - nTotPerc
					Else
						nTotPerc  += Round( nPerc, nDecPerc ) //-- Acumula os Percentuais calculados de todos os itens
					EndIf
					aCustoVei[6]	:= nPerc
					nValCob			:= nTotValCob
				Else
					nSbCusto1	-= aCustoVei[1]
					nSbCusto2	-= aCustoVei[2]
					nSbCusto3	-= aCustoVei[3]
					nSbCusto4	-= aCustoVei[4]
					nSbCusto5	-= aCustoVei[5]
					nPerc		-= aCustoVei[6]
					nTotValCob	-= nValCob
					nTotPerc	+= Round( aCustoVei[6], nDecPerc ) //-- Acumula os Percentuais calculados de todos os itens
				EndIf

				//-- Grava o movimento de custo
				GravaSDG(cAlias,cTpRateio,aArraySDG[nW][2][nT],aCustoVei,cDoc,cCodDesp,lMovim,ProxNum(),aParcelas[nCnt,1],nValCob)
				
				// grava campos enviados pelo ponto de entrada MA103SDG 
					SDG->(DbSetOrder(1)) //DG_FILIAL, DG_DOC, DG_CODDES, DG_ITEM
					SDG->(dbSeek(xFilial("SDG")+cDoc+cCodDesp+aArraySDG[nW][2][nT][1]))
				For nCntCpo := 1 To Len(aSDGGrava)
					RecLock('SDG',.F.)
						SDG->&(aSDGGrava[nCntCpo][1]) := aSDGGrava[nCntCpo][2] 
					MsUnLock()
				Next

				If cTpRateio == "V"
					//-- Caso a viagem seja informada baixa o movimento de custo
					If (!Empty(cFilOri) .And. !Empty(cViagem)) .Or.  (!Empty(cIdent) .And. nModulo==39)
						lBaixa := .T.
					Else
						//-- Caso a veiculo seja proprio baixa o movimento de custo
						DA3->(DbSetOrder(1))
						If DA3->(MsSeek(xFilial("DA3")+cCodVei))
							If DA3->DA3_FROVEI == "1"
								lBaixa := .T.
							EndIf
						EndIf
					EndIf
				Else
					lBaixa := .T.
				EndIf
				//-- Baixa o movimento de custo de transporte
				If lBaixa
					If nModulo==39
						TMSA070Bx("1",SDG->DG_NUMSEQ,SDG->DG_FILORI,SDG->DG_VIAGEM,SDG->DG_CODVEI,,,SDG->DG_VALCOB,,SDG->DG_IDENT)
					Else
						TMSA070Bx("1",SDG->DG_NUMSEQ,SDG->DG_FILORI,SDG->DG_VIAGEM,SDG->DG_CODVEI,,,SDG->DG_VALCOB,,"")
					EndIf
					If lCtbOnLine .And. SDG->DG_STATUS == StrZero(3,Len(SDG->DG_STATUS)) .And. Empty(SDG->DG_DTLANC)
						nTotalLcto += DetProva(nHdlPrv,"901",cProg,cLote)
						AAdd(aRecSDGBai, SDG->(Recno()) )
					EndIf
				EndIf
				If lCtbOnLine
					nTotalLcto	+= DetProva(nHdlPrv,"903",cProg,cLote)
					AAdd(aRecSDGEmi, SDG->(Recno()) )
				EndIf
			Next nCnt
		EndIf
	Next nT
Next nW

For nCntFor := 1 To Len(aRecSDGBai)
	SDG->(dbGoTo(aRecSDGBai[nCntFor]))
	RecLock('SDG',.F.)
	SDG->DG_DTLANC  := dDataBase  //-- Data de lancamento contabil a partir da Baixa da Despesa
	MsUnLock()
Next

For nCntFor := 1 To Len(aRecSDGEmi)
	SDG->(dbGoTo(aRecSDGEmi[nCntFor]))
	RecLock('SDG',.F.)
	SDG->DG_DTLAEMI := dDataBase  //-- Data de lancamento contabil a partir da Inclusao da Despesa
	MsUnLock()
Next
	
Return

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ A103Impri ≥ Autor ≥Alexandre Inacio Lemes≥ Data ≥10/06/2002≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Efetua a chamada do relatorio padrao ou do usuario         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ ExpX1 := A103Impri( ExpC1, ExpN1, ExpN2 )                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpC1 -> Alias do arquivo                                  ≥±±
±±≥          ≥ ExpN1 -> Recno do registro                                 ≥±±
±±≥          ≥ ExpN2 -> Opcao do Menu                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ ExpX1 -> Retorno do relatorio                              ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA170                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Function A103Impri( cAlias, nRecno, nOpc )

Local aArea    := GetArea()
Local cPrinter := SuperGetMv("MV_PIMPNFE")
Local xRet     := .T.

If !Empty( cPrinter ) .And. Existblock( cPrinter )
	//Faz a chamada do relatorio de usuario
	ExecBlock( cPrinter, .F., .F., { cAlias, nRecno, nOpc } )
Else
	//Faz a chamada do relatorio padrao
	xRet := MATR170( cAlias, nRecno, nOpc )
EndIf

RestArea( aArea )
Return( xRet )

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ A103Grava ≥ Autor ≥ Edson Maricate       ≥ Data ≥27.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Gravacao da Nota Fiscal de Entrada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103Grava(ExpC1,ExpN2,ExpA3)                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ nExpC1 : Controle de Gravacao  1,                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function a103Grava(lDeleta,lCtbOnLine,lDigita,lAglutina,aHeadSE2,aColsSE2,aHeadSEV,aColsSEV,nRecSF1,aRecSD1,aRecSE2,aRecSF3,aRecSC5,aHeadSDE,aColsSDE,aRecSDE,lConFrete,lConImp,aRecSF1Ori,aRatVei,aRatFro,cFornIss,cLojaIss,lBloqueio,l103Class,cDirf,cCodRet,cModRetPIS,nIndexSE2,lEstNfClass,dVencIss,lTxNeg,aMultas,lRatLiq,lRatImp,aNFEletr,cDelSDE,aCodR,cRecIss,cAliasTPZ,aCtbInf,aNfeDanfe,lExcCmpAdt, aDigEnd,lCompAdt,aPedAdt,aRecGerSE2,aInfAdic,aTotais,cCodRSef,aTitImp,aHeadDHP,aColsDHP,aCompFutur,aParcTrGen,aHeadDHR,aColsDHR,aHdSusDHR,aCoSusDHR,cIdsTrGen)
Local aPedPV	:= {}
Local aCustoEnt := {}
Local aCustoSDE := {}
Local aSEZ      := {}
Local aRecSEV	:= {}
Local aContratos:= {}
Local aAreaAnt  := {}
Local aDataGuia := {}
Local aDadosSF1 := {}
Local aNotaEmp  := {}
Local aDIfDec   := {0,.F.,0}
Local aCTBEnt   := CTBEntArr()
Local aFlagCtb  := {}
Local lGeraGuia := .T.
Local cArquivo  := ""
Local cLote     := ""
Local cAux      := ""
Local cBaseAtf	:= ""
Local cItemAtf	:= ""
Local nPosMemo  := ""
Local cB1FRETISS:= ""
Local cA2FRETISS:= ""
Local cF4FRETISS:= ""
Local cMes      := ""
Local cQuery    := ""
Local cMT103APV := ""
Local cMdRtISS	:= "1"
Local cAliasSE1 := "SE1"
Local cLcPadICMS:= Substr(GetMv("MV_LPADICM"),1,3)
Local cParcela  := SuperGetMV("MV_1DUP",.F.,"A")
Local lNotaEmp	:= SuperGetMV("MV_NOTAEMP",.F.,.F.)
Local lBloq103	:= SuperGetMV("MV_BLOQ103",.F.,.F.)
Local cDistAut	:= SuperGetMV('MV_DISTAUT',.F.," ")
Local cPrfx     := ""
Local cAliasSE2 := ""
Local cCtaRec	:= ""
Local cCodCIAPD1:= ""
Local nPosQtd   := GetPosSD1("D1_QUANT")
Local lFuncAgreg := FindFunction("AgregaOri")
Local lAgregaOri := .F.
Local aItensOri := {}
Local lDelCX2	  := .T.
Local lIncNotaEmp := .F.
Local lTemDocs    := .F.
Local nHdlPrv   := 0
Local nTotalLcto:= 0
Local nV        := 0
Local nX        := 0
Local nY        := 0
Local nZ        := 0
Local nW        := 0
Local nM        := 0
Local nJ        := 0
Local nC        := 0
Local nOper     := 0
Local nTaxaNCC  := 0
Local cSql      := ""
Local nItRat    := 0
Local nTotalDev := 0
Local nRecSD1SDE:= 0
Local nValIcmAnt:= 0
Local nDedICM   := 0
Local nSTTrans	:= 0
Local nTamParc  := TamSx3("E2_PARCELA")[1]
Local nTamLoc	:= TamSX3("D1_LOCAL")[1]
Local lVer640	:= .F.
Local lVer641	:= .F.
Local lVer650	:= .F.
Local lVer651	:= .F.
Local lVer656	:= .F.
Local lVer660	:= .F.
Local lVer642	:= .F.
Local lVer655	:= .F.
Local lVer665	:= .F.
Local lVer955   := .F.
Local lVer950   := .F.
Local lVer65C	:= .F.
Local lVer65D	:= .F.
Local lGeraPV   := .F.
Local lQuery    := .F.
Local lAchou    := .F.
Local lRetGrv   := .T.
Local lContinua := .T.
Local lGeraSD9  := .T.	// Valida se gera numero SD9
Local lIcmsTit  := .F.
Local lIcmsGuia := .F.
Local lCAT83    := .F.
Local lConfFor  := .F.
Local lConfBen  := .F.
Local lAuto116  := Iif(Type("l116Auto")== "L",l116Auto,.F.)
Local lAuto103  := Iif(Type("l103Auto")== "L",l103Auto,.F.)
Local lD1CtaRec := SD1->(ColumnPos("D1_CTAREC")) > 0
Local lRefCtaRec:= !Empty(MaFisScan("IT_CTAREC",.F.))
Local lSubSerie := cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_SUBSERI")) > 0 .And. SuperGetMv("MV_SUBSERI",.F.,.F.)
Local lTrbGen   := IIf(FindFunction("ChkTrbGen"),ChkTrbGen("SD1", "D1_IDTRIB"),.F.) // Verificacao se pode ou nao utilizar tributos genericos
Local lIntMnt   := SuperGetMV("MV_NGMNTES",.F.,"N") == "S" .Or. SuperGetMV("MV_NGMNTCM",.F.,"N") == "S"
Local nUsadoSDE    := Len(aHeadSDE)
Local lUsaGCT      := A103GCDisp()
Local lIntGH       := SuperGetMv("MV_INTGH",.F.,.F.)  //Verifica Integracao com GH
Local lCompensa    := SuperGetMv("MV_CMPDEVV",.F.,.F.)
Local lFlagDev	   := GetNewPar("MV_FLAGDEV",.F.)
Local lDISTMOV	   := SuperGetMV("MV_DISTMOV",.F.,.F.)
Local lUsaNewKey   := TamSX3("F1_SERIE")[1] == 14
Local lMulNats	   := SuperGetMv( "MV_MULNATS", .F., .F. )
Local lLog 		   := GetNewPar("MV_HABLOG",.F.)
Local aRecSe1      := {}
Local aRecNCC      := {}
Local aStruSE1     := {}
Local aDetalheMail := {}
Local aCtbDia 	   := {}
Local aCIAP		   := {}
Local aMT103RTE    := {}
Local aDadosMail   := ARRAY(7) // Doc,Serie,Fornecedor,Loja,Nome,Opcao,Natureza
Local cGrupo       := SuperGetMv("MV_NFAPROV")
Local cTipoNf      := SuperGetMv("MV_TPNRNFS")
Local lIntACD	   := SuperGetMV("MV_INTACD",.F.,"0") == "1"
Local nPParcela    := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_PARCELA"})
Local nPVencto     := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_VENCTO"})
Local nPValor      := aScan(aHeadSE2,{|x| AllTrim(x[2])=="E2_VALOR"})
Local nPosCod      := GetPosSD1('D1_COD')
Local nPosVUnit    := GetPosSD1("D1_VUNIT")
Local nPosNfOri    := GetPosSD1("D1_NFORI")
Local nPosSerOri   := GetPosSD1("D1_SERIORI")
Local nPosItem	   := GetPosSD1("D1_ITEM")
Local nPosFilOri   := GetPosSD1("D1_FILORI")
Local nPosNumPC    := GetPosSD1("D1_PEDIDO")
Local nPosItPC     := GetPosSD1("D1_ITEMPC")
Local nPosOP       := GetPosSD1("D1_OP")
Local nPosIDB6     := GetPosSD1("D1_IDENTB6")
Local nPosClaFis   := GetPosSD1("D1_CLASFIS")
Local nPosTes      := 0
Local nPosAC	   := 0
Local nQTDDev      := 0
Local nXCDanfe     := 0
Local lPCxNF   	   := .F.
Local lSCxPCxNF	   := .F.
Local lConfere     := .F.
Local lImpRel	   := Existblock("QIEIMPRL")
Local lMT103RTC    := ExistBlock('MT103RTC')
Local lMT103RTE    := ExistBlock('MT103RTE')
Local lMsDOC       := ExistBlock('MT103MSD')
Local lMT103BXCR   := ExistBlock("MT103BXCR")
Local lRetMT103BXCR:= .F.
Local lExcMSDoc    := .T.
Local cLocCQ       := SuperGetMv('MV_CQ')
Local lATFDCBA     := SuperGetMv("MV_ATFDCBA",.F.,"0") == "1" // "0"- Desmembra itens / "1" - Desmembra codigo base
Local aVlrAcAtf	   := {0,0,0,0,0}
Local aGNRE        := {}
Local lChkDup	   := .F.
Local nCntAdt      := 0
Local nPosAdt      := 0
//Verifica se a funcionalidade Lista de Presente esta ativa e aplicada
Local lUsaLstPre   := SuperGetMV("MV_LJLSPRE",,.F.) // .And. LjUpd78Ok()
Local cNumero	   := ""
Local nPosDeIt	   := 0
Local oModelMov
Local oSubFKA
Local cLog 		:= ""
Local lRet 		:= .T.
Local nRegSF1 	:= 0

// IntegraÁ„o GFE
Local aFieldValue  := {}
Local aStruModel   := {}
Local lIntGFE	   := SuperGetMv("MV_INTGFE",,.F.)
Local cUpDate	   := ""
Local nF1docs	   := 0
Local aAreaSF1	   := {}
Local cAliasAnt    := ""
Local cAno         := Right(Str(Year(dDataBase)),2)
Local cMvfsnciap   := SuperGetMV("MV_FSNCIAP")
Local nRec         := 0
Local nDespesa	   := 0
Local nDesconto	   := 0
Local nValParc	   := 0
Local lNfLimAl	   := SuperGetMV("MV_NFLIMAL", .F.,.F.)
Local nValorTot    := If(lNfLimAl,IIF(MaFisFound(),MaFisRet(,"NF_TOTAL"),0),0)
// Conferencia fisica do SIGAACD
Local lConfACD   := SA2->(FieldPos('A2_CONFFIS')) > 0 .And. SF1->(FieldPos("F1_STATCON")) > 0
Local cMVCONFFIS := SuperGetMV("MV_CONFFIS",.F.,"N")
Local cMVTPCONFF := SuperGetMV("MV_TPCONFF",.F.,"1")
Local lAntParcBA := .F.
Local aAreaSB5		:= {}
Local cDaCiap   	   := GetNewPar("MV_DACIAP",'S') //Utilizado para calc. ICMS no CIAP. Se S= Considera valor de dif. aliquota se N= Nao considera dif. aliquota
Local nVlrICMS	:= 0
Local nValFecp	:= 0
Local cProxNum	:= ""
Local cHoraRMT	:= SuperGetMv("MV_HORARMT",.F.,"2")
Local aHorario	:= {}
Local cFilE2	:=""
Local nPosDtDigit		:= Iif(Type("l103Auto") == "L" .And. l103Auto,aScan(aAutoCab,{|x| AllTrim(x[1])=="F1_DTDIGIT"}),0)
Local nValIcmSt := 0
Local lBkpInclui:= INCLUI
Local lBkpAltera:= ALTERA
Local nRecVinc		:= 0
Local lDclNew 	:= SuperGetMv("MV_DCLNEW",.F.,.F.)
Local lUfVazio	:= .F.
Local lPisCofImp := .F.
Local lISSImp	 := .F.
Local aTitCDA := {}
Local cMTFileCtb 	:= ""
Local nMTHandle 	:= 0
Local lAlcRet		:= .T. 	//Recebe retorno da funÁ„o MaAlcDoc
Local lCs116		:= FwIsInCallStack("MATA116") //Verifica se est· na pilha a rotina 116 para validar junto a rotina autom·tica
Local cPrefBAL    	:= Alltrim(GetNewPar("MV_PREFBAL","BAL"))
Local cPrefOFI    	:= Alltrim(GetNewPar("MV_PREFOFI","OFI"))
Local lIntGC      	:= IIf((SuperGetMV("MV_VEICULO",,"N")) == "S",.T.,.F.) // MÛdulos Concession·rias
Local lCteOriDest	:= SF1->(ColumnPos("F1_UFORITR")) > 0 .And. SF1->(ColumnPos("F1_MUORITR")) > 0 .And. SF1->(ColumnPos("F1_UFDESTR")) > 0 .And. SF1->(ColumnPos("F1_MUDESTR")) > 0
Local aNfColab		:= {}
Local nTamSF6       := TamSX3('F6_TIPODOC')[1]
Local lD1_FILORI	:= SD1->(ColumnPos("D1_FILORI")) > 0
Local l103ATURM		:= Type("lTOPDRFRM") <> "U" .And. lTOPDRFRM
Local cFunName		:= FunName()
Local laMemoSDE		:= Type("aMemoSDE") == "A"
Local lTSDE100I		:= ExistTemplate("SDE100I")
Local lSDE100I		:= ExistBlock("SDE100I")
Local lChkDHP		:= ChkFile("DHP")
Local lChkDHR		:= ChkFile("DHR")
Local lIntTMS		:= IntTMS()
Local lTSD1100I		:= ExistTemplate("SD1100I")
Local lSD1100I		:= ExistBlock("SD1100I")
Local lA103PROCDV	:= !IsInCallStack("A103PROCDV")
Local cMV_GSXNFE	:= SuperGetMV("MV_GSXNFE",,.F.)
Local nTamN1CBas 	:= TamSX3("N1_CBASE")[1]
Local lIntWMS		:= IntWMS()
Local lTSD1100E		:= ExistTemplate("SD1100E")
Local lSD1100E		:= ExistBlock("SD1100E")
Local cFilSD1 		:= xFilial("SD1")
Local cFilSDE		:= xFilial("SDE")
Local cFilSC7		:= xFilial("SC7")
Local lChkCOG		:= ChkFile("COG")
Local lSC1DtFi		:= SC1->(FieldPos("C1_XDTFIM")) > 0
Local lSC1HrFi		:= SC1->(FieldPos("C1_XHRFIM")) > 0
Local lMvNfeDvg		:= SuperGetMV("MV_NFEDVG", .F., .T.)
Local nItemMetric	:= 0
Local cFunc 		:= "a103atuse2"
Local nQtdTit		:= 0
Local lPRNFBEN 		:= SuperGetMV("MV_PRNFBEN", .F., .F.)
Local cFunImp		:= "MaFisAtuSF3"
Local nQtdImp		:= 0
Local cSevTemp		:= ""
Local cTMSERP 		:= SuperGetMV("MV_TMSERP",," ")	//-- CondiÁ„o de integraÁ„o com ERP (0 - Protheus, 1 - Datasul)
Local nPos		    := 0
Local cChaveSD1     := ""
Local lAgVlrATF 	:= SuperGetMV("MV_AGVLATF", .F., .T.) .AND. FindFunction("CompCTE") //Agrega valor do CTE ao ativo fixo.
Local lCsdXML 		:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA") .and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")
Local aD1Area		:= {}
Local lOrigem		:= .F.
Local nValIcmcom 	:= 0
Local lDifTit		:= .F.
Local lCompDifal 	:= .F.

Private aDupl      := {} 
Private cNewItSDG  := ""
Private oModelDCL  := NIL

DEFAULT lCtbOnLine:= .F.
DEFAULT lDeleta   := .F.
DEFAULT aHeadSE2  := {}
DEFAULT aColsSE2  := {}
DEFAULT aHeadSEV  := {}
DEFAULT aColsSEV  := {}
DEFAULT aHeadSDE  := {}
DEFAULT aColsSDE  := {}
DEFAULT nRecSF1   := 0
DEFAULT aRecSD1   := {}
DEFAULT aRecSE2   := {}
DEFAULT aRecSF3   := {}
DEFAULT aRecSC5   := {}
DEFAULT aRecSDE   := {}
DEFAULT lConFrete := .F.
DEFAULT lConImp   := .F.
DEFAULT aRecSF1Ori:= {}
DEFAULT aRatVei   := {}
DEFAULT aRatFro   := {}
DEFAULT lBloqueio := .F.
DEFAULT l103Class := .F.
DEFAULT lTxNeg	  := .F.
DEFAULT lRatLiq   := .T.
DEFAULT lRatImp   := .F.
DEFAULT aNFEletr  := {}
DEFAULT lEstNfClass := .F. //-- Estorno de Nota Fiscal Classificada (MATA140)
DEFAULT aMultas     := {}
DEFAULT cDelSDE     := "1"
DEFAULT cAliasTPZ   := "TRBTPZ"//Alias de integracao com o SIGAMNT
DEFAULT aCtbInf     := {}
DEFAULT aNfeDanfe   := {}
DEFAULT aInfAdic    := {}
DEFAULT aNotaEmp	:= {}
DEFAULT cCodRSef    := ""
DEFAULT aCodR       := {}
DEFAULT aDigEnd     := {}
DEFAULT aPedAdt     := {}
DEFAULT aRecGerSE2  := {}
DEFAULT aTotais     := {}
DEFAULT aTitImp		:= {}
DEFAULT aHeadDHP	:= {}
DEFAULT aColsDHP	:= {}
DEFAULT aHeadDHR	:= {}
DEFAULT aColsDHR	:= {}
DEFAULT aHdSusDHR	:= {}
DEFAULT aCoSusDHR	:= {}
DEFAULT aCompFutur	:= {}
DEFAULT aParcTrGen  := {}
DEFAULT cIdsTrGen	:= ""

If ( Type("cCodDiario") == "U" )
	Private cCodDiario := IIf(UsaSeqCor(), Iif(INCLUI, CriaVar("F1_DIACTB"), SF1->F1_DIACTB), "")
EndIf

//Portaria CAT83
If V103CAT83()
	lCAT83:= .T.
EndIf

If ExistBlock("A1031DUP")
	lChkDup:= ExecBlock("A1031DUP",.F.,.F.)
	If ValType(lChkDup) <> "L"
		lChkDup:= .F.
	EndIf
EndIf

//Reserva titulos vinculados ao documento
If lDeleta .And. !TravaSE2(aRecSE2)
	lContinua := .F.
	Help( ,1,'A103RTIT')
EndIf

//VerificaÁ„o das parcelas de titulo financeiro quando utilizado
If Type("lChkDup") == "L" .And. lChkDup
	//Consiste tamanho do campo de parcelas e parametro MV_1DUP
	If MaFisRet(,"NF_BASEDUP")>0 .And. ( Len(aColsSE2) > 1 ) .And. ( nTamParc <> Len(cParcela) )
		Help('',1,'A1031DUP')
		lContinua:= .F.
	EndIf
	
	//Consiste numero de parcelas da condicao e o maximo suportado pelo tamanho do campo
	If lContinua .And. ( Len(aColsSE2) > ( IIF ( STRZERO(0,nTamParc) == cParcela .Or. Val(cParcela) > 0,35,25) ** nTamParc ) )
		Help('',1,'A103PARC',,STR0342+Alltrim(STR(( IIF ( STRZERO(0,nTamParc) == cParcela .Or.; //##Numero maximo de parcelas:
		Val(cParcela) > 0,35,25) ** nTamParc )) )+Chr(10)+Chr(13)+STR0343+Alltrim(STR(Len(aColsSE2))),5,1)//##Parcelas da condicao de pagamento
		lContinua:= .F.
	EndIf
	If !lContinua
		Final()
	EndIf
EndIf

//Informa que houve importaÁ„o de pedido no documento
If Type("lImpPedido")<>"L"
	lImpPedido := .F.
Endif

//Verifica se o Produto È do tipo armamento.
If lDeleta .And. cMV_GSXNFE

	aAreaSB5 := SB5->(GetArea())

	For nX := 1 to Len(aRecSD1)
		DbSelectArea("SD1")
		MsGoto(aRecSD1[nx,1])

		If lContinua

			DbSelectArea('SB5')
			SB5->(DbSetOrder(1)) // acordo com o arquivo SIX -> A1_FILIAL+A1_COD+A1_LOJA

			//Verifico se algum dos itens foram movimentados ou alguns deles n„o podem ser excluidos
			//de acordo com a vontade do usuario, se alguma das respostas for Negativa a nota n„o ser· Excluida
			If SB5->(DbSeek(xFilial('SB5')+SD1->D1_COD)) // Filial: 01, CÛdigo: 000001, Loja: 02
				If SB5->B5_TPISERV=='2'
					lRetorno := aT720Exc(SD1->D1_DOC,SD1->D1_SERIE,.F.)
		       		If !lRetorno
		       			lContinua := lRetorno
		       		EndIf
				ElseIf SB5->B5_TPISERV=='1'
					lRetorno := aT710Exc(SD1->D1_DOC,SD1->D1_SERIE,.F.)
		       		If !lRetorno
		       			lContinua := lRetorno
		       		EndIf
				ElseIf SB5->B5_TPISERV=='3'
					lRetorno := aT730Exc(SD1->D1_DOC,SD1->D1_SERIE,.T.,SD1->D1_ITEM)
		       		If !lRetorno
		       			lContinua := lRetorno
		       		EndIf
				EndIf
			EndIf
		EndIf
	Next nX
	
	RestArea(aAreaSB5)
EndIf

//Template acionando ponto de entrada
If ExistTemplate("MT100GRV") .AND. lContinua
	lRetGrv := ExecTemplate("MT100GRV",.F.,.F.,{lDeleta})
	If ValType( lRetGrv ) == "L"
		lContinua := lRetGrv
	EndIf
EndIf

//Agroindustria
If FindFunction("OGXUtlOrig") //Encontra a funÁ„o
	If OGXUtlOrig() //Verifica se existe
	   If FindFunction("OGX145") //Encontra a funÁ„o
			OGX145(lDeleta)
			If ValType( lRetGrv ) == "L"
				lContinua := lRetGrv
			EndIf
	   EndIf
	EndIf
EndIf

//Ponto de entrada anterior a gravacao do Documento de Entrada
If (ExistBlock("MT100GRV")) .AND. lContinua
	lRetGrv := ExecBlock("MT100GRV",.F.,.F.,{lDeleta})
	If ValType( lRetGrv ) == "L"
		lContinua := lRetGrv
	EndIf
EndIf

//Ponto de Entrada para validacao dos codigos de retencao - DIRF
If lContinua .And. !lDeleta .And. ExistBlock("MT103DIRF")
	lRetGrv := ExecBlock("MT103DIRF",.F.,.F.,{acodR})
	If ValType( lRetGrv ) == "L"
		lContinua := lRetGrv
	EndIf
EndIf

//Estorna o PR0 quando o apontamento for gerado atraves do documento de entrada
If lContinua .And. lDeleta
	lContinua := MTEstornPR(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA)
Endif

//Atualiza das etiquetas (CB0) quando geradas no pedido de compra
If lContinua .And. UsaCB0("01")
	CBAtuItNFE()
EndIf

If lContinua
	//Verifica se ha rotina automatica
	l103Auto := If(Type("L103AUTO")=="U",.F.,l103Auto)
	l103Auto := If(Type("L116AUTO")=="U",l103Auto,.F.)
	
	//Verifica se ha contabilizacao
	If lCtbOnLine .Or. ( lDeleta .And. !Empty(SF1->F1_DTLANC))
		lCtbOnLine := .T.
		DbSelectArea("SX5")
		DbSetOrder(1)
		MsSeek(xFilial("SX5")+"09COM")
		cLote := IIf(Found(),Trim(X5DESCRI()),"COM ")
		
		//Executa um execblock
		If At(UPPER("EXEC"),X5Descri()) > 0
			cLote := &(X5Descri())
		EndIf
		nHdlPrv := HeadProva(cLote,"MATA103",Subs(cUsuario,7,6),@cArquivo)
		If nHdlPrv <= 0
			lCtbOnLine := .F.
		EndIf
	EndIf
	
	//Verifica quais os lancamentos que estao habilitados
	If lCtbOnLine
		lVer640	:= VerPadrao("640") // Entrada de NF Devolucao/Beneficiamento ( Cliente ) - Itens
		lVer650	:= VerPadrao("650") // Entrada de NF Normal ( Fornecedor ) - Itens
		lVer660	:= VerPadrao("660") // Entrada de NF Normal ( Fornecedor ) - Total
		lVer642	:= VerPadrao("642") // Entrada de NF Devol.Vendas - Total (SF1)
		lVer655	:= VerPadrao("655") // Exclusao de NF ( Fornecedor ) - Itens
		lVer665	:= VerPadrao("665") // Exclusao de NF ( Fornecedor ) - Total
		lVer955 := VerPadrao("955") // Do SIGAEIC - Importacao
		lVer950 := VerPadrao("950") // Do SIGAEIC - Importacao
		lVer641	:= VerPadrao("641")	// Entrada de NF Devolucao/Beneficiamento ( Cliente ) - Itens do Rateio
		lVer651	:= VerPadrao("651")	// Entrada de NF Normal ( Fornecedor ) - Itens do Rateio
		lVer656	:= VerPadrao("656")	// Exclusao de NF ( Fornecedor ) - Itens do Rateio
		lVer65C	:= VerPadrao("65C")	// Documento de Entrada - Rateio Multiplas Naturezas
		lVer65D	:= VerPadrao("65D")	// Documento de Entrada - Cancelamento Rateio Multiplas Naturezas
	EndIf
	
	//Posiciona registros
	If cTipo$"DB"
		DbSelectArea("SA1")
		DbSetOrder(1)
		MsSeek(xFilial("SA1")+cA100For+cLoja)
	Else
		DbSelectArea("SA2")
		DbSetOrder(1)
		MsSeek(xFilial("SA2")+cA100For+cLoja)
	EndIf
	
	//Verifica a operacao a ser realizada (Inclusao ou Exclusao )
	If !lDeleta
		//Grava SF8 (NF Complemente Frete x Nota Original)
		If cTipo == "C" .And. !lCs116 .And. !lIntMnt
			If Type("cTpCompl") == "C" .And. cTpCompl == "3"
				A103GRVSF8()
			Endif
		Endif 

		//Atualizacao do cabecalho do documento de entrada
		DbSelectArea("SF1") 
		DbSetOrder(1)
		If nRecSF1 <> 0
			MsGoto(nRecSF1)
			RecLock("SF1",.F.)

			If lUsaNewKey
				cPrfx := SF1->F1_PREFIXO
			EndIf

			nOper := 2
			If lBloqueio .And. mv_par17==2
				MaAlcDoc({SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,"NF",SF1->F1_VALBRUT,,,SF1->F1_APROV,,SF1->F1_MOEDA,SF1->F1_TXMOEDA,SF1->F1_EMISSAO},SF1->F1_EMISSAO,3)
			EndIf
		Else
			//Obtem numero do documento quando utilizar
			//numeracao pelo SD9 (MV_TPNRNFS = 3)
			//Se a chamada for do SIGALOJA nao pode
			//gerar outro numero no SD9.
			If ( cFunName $ "LOJA720|FATA720|LOJA701|FATA701" .or. IsInCallStack("LJ601DEVSD2") .Or. ( cFormul == "S" .And. IsInCallStack("MATI103")) )
		    	If !Empty( cNFiscal )
					lGeraSD9	:= .F.
				Endif
			Endif

			If cTipoNf == "3" .AND. cFormul == "S" .AND. lGeraSD9
				SX3->(DbSetOrder(1))
				If (SX3->(dbSeek("SD9")))
					// Se cNFiscal estiver vazio, busca numeraÁ„o no SD9, senao, respeita o novo numero
					// digitado pelo usuario.
					cNFiscal := MA461NumNf(.T.,cSerie,cNFiscal,,SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie) )
				EndIf
			Endif

			If lUsaNewKey
                SE2->(dbSetOrder(1))
				cAliasSE2 := GetNextAlias()
				cQuery := " SELECT MAX(E2_PREFIXO) E2PRFXMAX FROM " + RetSqlName("SE2")
				cQuery += " WHERE E2_FILIAL = '" + xFilial("SE2") + "'"
				cQuery += " AND E2_NUM      = '" + cNFiscal + "'"
				cQuery += " AND E2_FORNECE  = '" + cA100For + "'"
				cQuery += " AND E2_LOJA     = '" + cLoja + "'"
				cQuery += " AND D_E_L_E_T_  = ''"
				cQuery	  := ChangeQuery(cQuery)
				dbUseArea( .T., "TOPCONN", TcGenQry( , , cQuery ), cAliasSE2, .T., .T. )
				cFilE2	  := xFilial("SE2")
				DbSelectArea(cAliasSE2)
				If !Empty( (cAliasSE2)->E2PRFXMAX )
 					cPrfx := Soma1( (cAliasSE2)->E2PRFXMAX , TamSX3("E2_PREFIXO")[1] )
 					/*Devido ao projeto CHAVE ⁄NICA, a consistÍncia abaixo È necess·ria para
					garantir que o novo tÌtulo a ser gerado n„o ir· colidir com um tÌtulo
					da base histÛrica do cliente criada antes do projeto chave ˙nica.*/
			  		While .T.
			   			If (SE2->(dbSeek(cFilE2+cPrfx+cNFiscal)))
			    			cPrfx:= Soma1(cPrfx, TamSX3("E2_PREFIXO")[1])
			   			Else
			    			EXIT
			   			EndIf
			  		EndDo
			 	Else
			  		cPrfx:=subStr(&(SuperGetMv("MV_2DUPREF")),1,TamSX3("E2_PREFIXO")[1])
			 	EndIf

				(cAliasSE2)->(DbCloseArea())
				DbSelectArea("SF1")
				DbSetOrder(1)
            EndIf

			RecLock("SF1",.T.)
			nOper := 1
		EndIf

        If l103Auto
			For nX := 1 To Len(aAutoCab)
				SF1->(FieldPut(FieldPos(aAutoCab[nX][1]),aAutoCab[nX][2]))
			Next nX
		EndIf
		
		//--Atualiza status da nota para 'em conferencia'
		If cPaisLoc == "BRA"
			If (cTipo == "N" .And. cMVCONFFIS == "S") .And. ((SA2->A2_CONFFIS == "0" .And. cMVTPCONFF == "2") .Or. SA2->A2_CONFFIS == "2")
				lConfFor := .T.
			EndIf
		EndIf
		
		If !lConfFor .And. cTipo == "D" .And. cMVCONFFIS == "S" .And. cMVTPCONFF == "2"
			lConfFor := .T.
		EndIf
		
		If (cTipo == "B" .And. cMVCONFFIS == "S" .And. cMVTPCONFF == "2")
			lConfBen := .T.
		Endif
		
		//Gera conferencia havendo 1 TES com controle de estoque
		If lConfFor .Or. lConfBen
			lConfere := .F.
			nPosTes  := GetPosSD1("D1_TES")
		
			//--Verifica se o documento possui bloqueio de movimentos, pois se nao ha atualizacao de estoque nao deve haver conferencia fisica
			If MV_PAR17 == 2
				If nPosTes > 0
					SF4->(DbSelectArea("SF4"))
					SF4->(DbSetOrder(1))
					For nX := 1 to Len(aCols)
						If !aCols[nx][Len(aHeader)+1]
							If !Empty(aCols[nX][nPosTes])
								SF4->(MsSeek(xFilial("SF4")+aCols[nX][nPosTes]))
								If SF4->F4_ESTOQUE == "S"
			                        lConfere := .T.
			                        Exit
		    	                EndIf
	    	                EndIf
	                    EndIf
					Next
				EndIf
			EndIf
			SF1->F1_STATCON := IIF(lConfere .And. Empty(SF1->F1_STATCON),"0",SF1->F1_STATCON)
		EndIf
		
		//Atendimento ao DECRETO 5.052, DE 08/01/2004 para o municipio de ARARAS
		//Mais especificamente o paragrafo unico do Art 2
		cA2FRETISS		:=	SA2->(FieldGet (FieldPos ("A2_FRETISS")))
		SF1->F1_FILIAL  := xFilial("SF1")
		SF1->F1_DOC     := cNFiscal
		SF1->F1_STATUS  := "A"
		SerieNfId("SF1",1,"F1_SERIE",dDEmissao,cEspecie,cSerie)
		SF1->F1_FORNECE := cA100For
		SF1->F1_LOJA    := cLoja
		SF1->F1_COND    := cCondicao

		If Empty(SA2->A2_NUMRA)
			SF1->F1_DUPL    := IIf(MaFisRet(,"NF_BASEDUP")>0,cNFiscal,"")
		Else
			SF1->F1_NUMRA   := SA2->A2_NUMRA
		EndIf

		SF1->F1_TXMOEDA := MaFisRet(,"NF_TXMOEDA")
		SF1->F1_EMISSAO := dDEmissao
		SF1->F1_EST     := IIF(cTipo$"DB",SA1->A1_EST,SA2->A2_EST)
		SF1->F1_TIPO    := cTipo

		If cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_TPCOMPL")) > 0 .And. cTipo == "C" .And. Type("cTpCompl") == "C"
			SF1->F1_TPCOMPL := cTpCompl
		EndIf

		If lSubSerie .And. Type("cSubSerie") == "C"
			SF1->F1_SUBSERI := cSubSerie
		EndIf

		If Empty( SF1->F1_RECBMTO )
			SF1->F1_RECBMTO := dDataBase
		Endif

		SF1->F1_DTDIGIT := IIf( (SuperGetMv("MV_DATAHOM",NIL,"1") == "1") .and. !lIntGFE, dDataBase, SF1->F1_RECBMTO )

		SF1->F1_FORMUL  := IIF(cFormul=="S","S"," ")
		SF1->F1_ESPECIE := cEspecie

		If lUsaNewKey .And. !Empty(cPrfx)
			SF1->F1_PREFIXO := cPrfx
        Else
			SF1->F1_PREFIXO := IIf(MaFisRet(,"NF_BASEDUP")>0,&(SuperGetMV("MV_2DUPREF")),"")
		EndIf

		SF1->F1_ORIGLAN := IIf(lConFrete,"F"+SubStr(SF1->F1_ORIGLAN,2),SF1->F1_ORIGLAN)
		SF1->F1_ORIGLAN := IIf(lConImp,SubStr(SF1->F1_ORIGLAN,1,1)+"D",SF1->F1_ORIGLAN)

		SF1->F1_MOTRET  := MT103GetRet()[1]
		SF1->F1_HISTRET := MT103GetRet()[2]

	    If SuperGetMv("MV_HORANFE",.F.,.F.) .And. Empty(SF1->F1_HORA)
			//Parametro MV_HORARMT habilitado pega a hora do smartclient, caso contrario a hora do servidor
			If cHoraRMT == '1' //Horario do SmartClient
				SF1->F1_HORA := GetRmtTime()
			ElseIf cHoraRMT == '2' //Horario do servidor
				SF1->F1_HORA := Time()
			ElseIf cHoraRMT =='3' //Horario de acordo com o estado da filial corrente
				aHorario := A103HORA()
				If !Empty(aHorario[2])
					SF1->F1_HORA := aHorario[2]
				EndIf
			Endif
		EndIf

		If cHoraRMT == '3' .And. LEN(aHorario) > 0
			If (IsInCallStack("MATI103") .Or. IsInCallStack("MATI103A") .Or. IsInCallStack("MATI103B")) .And. l103Auto .And. (nPosDtDigit > 0)
				SF1->F1_DTDIGIT := aAutoCab[nPosDtDigit,2]
			Elseif SuperGetMv("MV_DATAHOM",NIL,"1") == "1" .AND. !Empty(aHorario[1])
				SF1->F1_DTDIGIT := aHorario[1]
			Else
				SF1->F1_DTDIGIT := SF1->F1_RECBMTO
			Endif
		Else
			If (IsInCallStack("MATI103") .Or. IsInCallStack("MATI103A") .Or. IsInCallStack("MATI103B")) .And. l103Auto .And. (nPosDtDigit > 0)
				SF1->F1_DTDIGIT := aAutoCab[nPosDtDigit,2]
			Elseif SuperGetMv("MV_DATAHOM",NIL,"1") == "1"
				SF1->F1_DTDIGIT := dDataBase
			Else
				SF1->F1_DTDIGIT := SF1->F1_RECBMTO
			Endif
		EndIf

		If SF1->F1_STATCON == "2" .And. SuperGetMv("MV_CLACFDV",.F.,.F.)
			SF1->F1_STATCON	:= "4" // Atualiza status da conferencia do ACD para "NF classificada com divergencia"
		EndIf

		If lBloqueio .Or. (mv_par17==1 .And. ( cFormul=="S" .Or. lBloq103 ) .And. ( cFunName$"MATA103|FATA720" .Or. l103Auto ))
			//Ponto de entrada para alterar o Grupo de Aprovacao
			If ExistBlock("MT103APV")
				cMT103APV := ExecBlock("MT103APV",.F.,.F.)
				If ValType(cMT103APV) == "C"
					cGrupo := cMT103APV
				EndIf
			EndIf

			cGrupo:= If(Empty(SF1->F1_APROV),cGrupo,SF1->F1_APROV)
			If !Empty(cGrupo) .And. mv_par17==2 .Or. (mv_par17==1 .And. cFormul=="N" .And. !lBloq103 .And. cFunName$"MATA103|FATA720")
				lAlcRet := MaAlcDoc({SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,"NF",Iif(nValorTot>0,nValorTot,MaFisRet(,"NF_TOTAL")),,,cGrupo,,Iif (SF1->F1_MOEDA == 0, nMoedaCor,SF1->F1_MOEDA ),SF1->F1_TXMOEDA,SF1->F1_EMISSAO},SF1->F1_EMISSAO,1,SF1->F1_DOC+SF1->F1_SERIE)
				if lAlcRet
					DbSelectArea("SF1")
					SF1->F1_STATUS := "B"
					SF1->F1_APROV  := cGrupo
				EndIf
			ElseIf mv_par17==1 .And. ( cFormul=="S" .Or. lBloq103 ) .And. ( cFunName$"MATA103|FATA720" .Or. l103Auto )
				DbSelectArea("SF1")
				SF1->F1_STATUS := "C"
			Else
				lBloqueio := .F.
			EndIf
		EndIf

		// InformaÁıes Adicionais
		If Len(aInfAdic) > 0
			If cPaisLoc == "BRA" .And. SF1->(FieldPos("F1_INCISS")) > 0
				SF1->F1_INCISS  := aInfAdic[01]
			EndIf
			If SF1->(FieldPos("F1_VEICUL1")) > 0
				SF1->F1_VEICUL1 := aInfAdic[02]
			EndIf
			If SF1->(FieldPos("F1_VEICUL2")) > 0
				SF1->F1_VEICUL2 := aInfAdic[03]
			EndIf
			If SF1->(FieldPos("F1_VEICUL3")) > 0
				SF1->F1_VEICUL3 := aInfAdic[04]
			EndIf
			If SF1->(ColumnPos("F1_DTCPISS")) > 0
				SF1->F1_DTCPISS := aInfAdic[05]
			EndIf
			If SF1->(ColumnPos("F1_SIMPNAC")) > 0
				SF1->F1_SIMPNAC := Iif(aInfAdic[06]$'12',aInfAdic[06], IiF(cTipo$"DB",SA1->A1_SIMPNAC,SA2->A2_SIMPNAC))
			EndIf
			If SF1->(ColumnPos("F1_CLIDEST")) > 0
				SF1->F1_CLIDEST := aInfAdic[07]
			EndIf
			If SF1->(ColumnPos("F1_LOJDEST")) > 0
				SF1->F1_LOJDEST := aInfAdic[08]
			EndIf
			If SF1->(ColumnPos("F1_ESTDES")) > 0
				SF1->F1_ESTDES := aInfAdic[09]
			EndIf
			If lCteOriDest
				If SF1->(ColumnPos("F1_UFORITR")) > 0
					SF1->F1_UFORITR := aInfAdic[10]
					If Empty(aInfAdic[10])
						lUfVazio := .T.
					Endif
				EndIf
				If SF1->(ColumnPos("F1_MUORITR")) > 0
					SF1->F1_MUORITR := aInfAdic[11]
				EndIf
				If SF1->(ColumnPos("F1_UFDESTR")) > 0
					SF1->F1_UFDESTR := aInfAdic[12]
					If Empty(aInfAdic[12])
						lUfVazio := .T.
					Endif
				EndIf
				If SF1->(ColumnPos("F1_MUDESTR")) > 0
					SF1->F1_MUDESTR := aInfAdic[13]
				EndIf
			EndIf
			If SF1->(ColumnPos("F1_CLIPROP")) > 0
				SF1->F1_CLIPROP := aInfAdic[14]
			EndIf

			If SF1->(ColumnPos("F1_LJCLIPR")) > 0
				SF1->F1_LJCLIPR := aInfAdic[15]
			EndIf

			If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
				SF1->F1_INDPRES := aInfAdic[16]
				SF1->F1_CODA1U := aInfAdic[17]
			Endif
		EndIf		

		If cPaisLoc == "BRA" .And. SuperGetMV("MV_ISSXMUN",.F.,.F.) .And. (Len(aInfAdic)== 0 .Or. Empty(aInfAdic[1]))
			SF1->F1_INCISS := MaFisRet(,"NF_CODMUN")
			SF1->F1_ESTPRES:= MaFisRet(,"NF_UFPREISS")
		EndIf
		
		//Campos da Nota Fiscal Eletronica
		If cPaisLoc == "BRA"
			If Len(aNFEletr) > 0
				SF1->F1_NFELETR	:= aNFEletr[01]
				SF1->F1_CODNFE	:= aNFEletr[02]
				SF1->F1_EMINFE	:= aNFEletr[03]
				SF1->F1_HORNFE 	:= aNFEletr[04]
				SF1->F1_CREDNFE	:= aNFEletr[05]
				SF1->F1_NUMRPS	:= aNFEletr[06]
				SF1->F1_MENNOTA	:= aNFEletr[07]
				SF1->F1_MENPAD	:= aNFEletr[08]
			Endif
			
			//Campos DANFE-NF
			If Len(aNfeDanfe) > 0
				SF1->F1_TRANSP	:= aNfeDanfe[01]
				SF1->F1_PLIQUI	:= aNfeDanfe[02]
				SF1->F1_PBRUTO 	:= aNfeDanfe[03]
				SF1->F1_ESPECI1	:= aNfeDanfe[04]
				SF1->F1_VOLUME1	:= aNfeDanfe[05]
				SF1->F1_ESPECI2	:= aNfeDanfe[06]
				SF1->F1_VOLUME2	:= aNfeDanfe[07]
				SF1->F1_ESPECI3	:= aNfeDanfe[08]
				SF1->F1_VOLUME3	:= aNfeDanfe[09]
				SF1->F1_ESPECI4	:= aNfeDanfe[10]
				SF1->F1_VOLUME4	:= aNfeDanfe[11]
				SF1->F1_PLACA  	:= aNfeDanfe[12]
				SF1->F1_CHVNFE 	:= aNfeDanfe[13]
				SF1->F1_TPFRETE := aNfeDanfe[14]
				SF1->F1_VALPEDG := aNfeDanfe[15]
				SF1->F1_FORRET  := aNfeDanfe[16]
				SF1->F1_LOJARET := aNfeDanfe[17]
				SF1->F1_TPCTE  	:= aNfeDanfe[18]
				SF1->F1_FORENT  := aNfeDanfe[19]
				SF1->F1_LOJAENT := aNfeDanfe[20]
				SF1->F1_NUMAIDF := aNfeDanfe[21]
				SF1->F1_ANOAIDF := aNfeDanfe[22]
				SF1->F1_MODAL  	:= aNfeDanfe[23]
				SF1->F1_DEVMERC := aNfeDanfe[24]
			EndIf
			
			//Executa a gravaÁ„o do Array ADanfeComp retornado pelo ponto de entrada MT103DCF
			If ExistBlock("MT103DCF") .And. Type("aDanfeComp") == "A"
				If Len(aDanfeComp)>0
			    	For nXCDanfe:=1 to Len(aDanfeComp)
			    		SF1->(FieldPut(FieldPos(aDanfeComp[nXCDanfe][1]),aDanfeComp[nXCDanfe][2]))
					Next nXCDanfe
					aDanfeComp := {}
				EndIf
			EndIf
			//Campo de controle para identificacao do titulo gerado referente a tributos
			If !(cTipo$"DB")
				SF1->F1_NUMTRIB := "N"
			EndIf
		Endif
		//Variavel tipo private aCpoEsp para armazenar campos especificos
		//do cabecalho (SF1) na rotina automatica
		//           Usada pelo sistema de importaÁ„o - TSF
		If Type("aCpoEsp") == "A"
			For nX := 1 to len(aCpoEsp)
				FieldPut(FieldPos(aCpoEsp[nX][1]),aCpoEsp[nX][2])
			Next nY
		Endif
		
		//Campos F1_DESPESA e F1_DESCONT da nota de conhecimento de frete
		//passados atraves da rotina automatica (MATA116)
		If (lAuto116 .Or. lAuto103) .And. Len(aAutoCab) > 0 .And. lCs116
			nPosAC := aScan(aAutoCab,{|x| x[1] == "F1_ORIGEM" })
			If nPosAC > 0
				SF1->F1_ORIGEM := aAutoCab[nPosAC][2]
			EndIf
        	nPosAC := aScan(aAutoCab,{|x| x[1] == "F1_DESPESA" })
            If nPosAC > 0
				SF1->F1_DESPESA := aAutoCab[nPosAC][2]
				MaFisAlt("NF_DESPESA",aAutoCab[nPosAC][2])
				nDespesa := aAutoCab[nPosAC][2]
		 	EndIf
		 	nPosAC := aScan(aAutoCab,{|x| x[1] == "F1_DESCONT" })
		    If nPosAC > 0
				SF1->F1_DESCONT := aAutoCab[nPosAC][2]
				MaFisAlt("NF_DESCONTO",aAutoCab[nPosAC][2])
				nDesconto := aAutoCab[nPosAC][2]
		 	EndIf
			msUnlock()
			nValParc := (nDespesa - nDesconto) / Len(aColsSE2)
			For nX := 1 To Len(aColsSE2)
				If (aColsSE2[nX][nPValor] > 0)
					aColsSE2[nX][nPValor] += nValParc
				EndIf
			Next nX
		EndIf

		// Gravacao do campo F1_IDNF
		If SF1->(FieldPos('F1_IDNF')) > 0
			SF1->F1_IDNF := FWUUID("SF1")
		EndIf

		//Tratamento da gravacao do SF1 na Integridade Referencial
		SF1->(FkCommit())
		
		//Dados para envio de email do messenger
		aDadosMail[1]:=SF1->F1_DOC
		aDadosMail[2]:=SerieNfId("SF1",2,"F1_SERIE")
		aDadosMail[3]:=SF1->F1_FORNECE
		aDadosMail[4]:=SF1->F1_LOJA
		aDadosMail[5]:=If(cTipo$"DB",SA1->A1_NOME,SA2->A2_NOME)
		aDadosMail[6]:=If(lDeleta,5,If(l103Class,4,3))
		aDadosMail[7]:=MaFisRet(,"NF_NATUREZA")
		
		//Atualizacao dos impostos calculados no cabecalho do documento
		SF4->(MaFisWrite(2,"SF1",Nil))
		SF1->F1_MODAL  := aNfeDanfe[23]
		
		//Limpa os campos F1_UFORITR/F1_UFDESTR caso n„o tenham sido utilizados, pois
		//por possuirem referencia ao NF_UFORIGEM e NF_UFDEST eles s„o gravados indevidamente.
		If lCteOriDest
			If SF1->(ColumnPos("F1_UFORITR")) > 0 .And. (lUfVazio .Or. SF1->F1_UFORITR != IIF(Len(aInfAdic) > 0,aInfAdic[10],""))
				SF1->F1_UFORITR := IIF(Len(aInfAdic) > 0,aInfAdic[10],"")
			EndIf
			
			If SF1->(ColumnPos("F1_UFDESTR")) > 0 .And. (lUfVazio .Or. SF1->F1_UFDESTR != IIF(Len(aInfAdic) > 0,aInfAdic[12],""))
			    SF1->F1_UFDESTR := IIF(Len(aInfAdic) > 0,aInfAdic[12],"")
			EndIf
		EndIf

		//Ponto de entrada para atualizaÁıes na SF1 apÛs finalizaÁ„o da gravaÁ„o da SF1
		If (ExistBlock("SF1TTS")) 
			ExecBlock("SF1TTS",.f.,.f.)
		EndIf
		
		//Montagem do array aDupl
		For nX := 1 To Len(aColsSE2)
			aadd(aDupl,Substr(cSerie,1,3)+"≥"+cNFiscal+"≥ "+aColsSE2[nX][nPParcela]+" ≥"+DTOC(aColsSE2[nX][nPVencto])+"≥ "+Transform(aColsSE2[nX][nPValor],PesqPict("SE2","E2_VALOR")))
		Next nX

		//Atualizacao dos itens do documento de entrada
		For nX := 1 to Len(aCols)
			//Atualiza a regua de processamento
			If !aCols[nx][Len(aHeader)+1]

				If INCLUI .Or. l103Class
					nItemMetric++
				Endif

				DbSelectArea("SD1")
				If (nRec := aScan(aRecSD1,{|x| x[2] == acols[nx][nPosItem]})) > 0
					SD1->(MsGoto(aRecSD1[nRec][1]))
					RecLock("SD1",.F.)
					//Estorna os acumulados da Pre-Nota
					MaAvalSD1(2)
				Else
					RecLock("SD1",.T.)
				EndIf
				lGeraPV := .F.
				For nY := 1 To Len(aHeader)
					If aHeader[nY][10] # "V"
						SD1->(FieldPut(FieldPos(aHeader[nY][2]),IIF(aHeader[nY][8] == "M" .and. Empty(aCols[nX][nY]), " ", aCols[nX][nY])))
					EndIf
					If AllTrim(aHeader[ny,2]) == "D1_GERAPV"
						lGeraPV := If(aCols[nX,nY]=="S",.T.,.F.)
					Endif
					If AllTrim(aHeader[ny,2]) == "D1_SLDEXP"
						If l103class
							SD1->D1_SLDEXP := aCols[nX][nPosQTD]
						EndIf
					Endif
					
				Next nY

				// Grava array aOPBenef na ClassificaÁ„o apÛs Bloqueio por Tolerancia
				If l103Class .And. lPRNFBEN .And. Type("aOPBenef") == "A" 	.And. ;
					nPosOP > 0 		.And. !Empty(aCols[nX][nPosOP]) 		.And. ;
					nPosNfOri > 0 	.And. !Empty(aCols[nX][nPosNfOri]) 		.And. ;
					nPosSerOri > 0 	.And. !Empty(aCols[nX][nPosSerOri]) 	.And. ;
					nPosIDB6 > 0 	.And. !Empty(aCols[nX][nPosIDB6])		.And. ;
					l103TolRec		.And. ; // Verifica se passou por bloqueio de recebimento
					SCR->(MsSeek(xFilial("SCR")+"NF"+Padr(SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,Len(SCR->CR_NUM))))
					If (nPos := aScan(aOPBenef,{|x| x[1]+x[3]+x[4] == aCols[nX][nPosOP]+aCols[nX][nPosCod]+aCols[nX][nPosItem]})) == 0
						aAdd(aOPBenef,{aCols[nX][nPosOP],aCols[nX][nPosQtd],aCols[nX][nPosCod],aCols[nX][nPosItem]})
					Else
						aOPBenef[nPos,2] := aCols[nX][nPosQtd]
					EndIf					
				EndIf 

				//-- Avaliar a existencia de ao menos um vÌnculo de SC x PC x NF 
				If !lSCxPCxNF
					lPCxNF := !Empty(aCols[nX][nPosNumPC]) .And. !Empty(aCols[nX][nPosItPC])
					If lPCxNF .And. !lSCxPCxNF
						lSCxPCxNF := !Empty(GetAdvFVal("SC7", "C7_NUMSC", cFilSC7 + aCols[nX][nPosNumPC] + aCols[nX][nPosItPC], 1, "", .T.))
					EndIf
				EndIf

				//Atualiza os dados padroes e dados fiscais
				//Atendimento ao DECRETO 5.052, DE 08/01/2004 para o municipio de ARARAS
				//Mais especificamente o paragrafo unico do Art 2
				If cB1FRETISS <> "2"
					cB1FRETISS	:=	SB1->B1_FRETISS
				EndIf
				SD1->D1_FILIAL  := cFilSD1
				SD1->D1_FORNECE := cA100For
				SD1->D1_LOJA    := cLoja
				SD1->D1_DOC     := cNFiscal
				SerieNfId("SD1",1,"D1_SERIE",dDEmissao,cEspecie,cSerie)
				SD1->D1_EMISSAO := dDEmissao
				SD1->D1_DTDIGIT := SF1->F1_DTDIGIT
				SD1->D1_TIPO    := cTipo
				SD1->D1_FORMUL  := IIF(cFormul=="S","S"," ")

				//- verifica se o proxnum esta nula, fazendo uso do processo 
				//- antigo, pois vem pela rotina de conhecimento de frete
				If _oProxNum == nil 
					cProxNum := ProxNum()
				Else 
					cProxNum := _oProxNum[cValToChar(nX)] //ProxNum()
				EndIf 
				If Empty(cProxNum)
					lMsErroAuto := .T.
					lAutoErrNoFile := .T.
				    If Intransact()
						DisarmTransaction()
					EndIf
					Break
				EndIf
				SD1->D1_NUMSEQ  := cProxNum
				If l103Auto
					nPos := aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_ORIGLAN"})
					If nPos > 0
						SD1->D1_ORIGLAN := aAutoItens[nX,nPos,2]
					Endif
				Else
					If lConFrete
						SD1->D1_ORIGLAN := "FR"
					Elseif lConImp
						SD1->D1_ORIGLAN := "DP"
					Else
						SD1->D1_ORIGLAN := SD1->D1_ORIGLAN
					Endif
				Endif
				SD1->D1_TIPODOC := SF1->F1_TIPODOC
				SD1->D1_CODLAN  := A103CAT83(nX)

				If lD1_FILORI
					If cTipo == "D" .And. (nPosNfOri > 0 .And. !Empty(aCols[nX][nPosNfOri]))
						If nPosFilOri > 0 .And. !Empty(aCols[nX][nPosFilOri])
							SD1->D1_FILORI := aCols[nX][nPosFilOri]
						Else
							SD1->D1_FILORI := xFilial("SD2")
						Endif
					Endif
				Endif

				If l103ATURM //Atualiza saldo no PC (RetenÁ„o/DeduÁ„o/Faturamento Direto)
					A103ATURM("+","RET",SD1->D1_RETENCA,SD1->D1_PEDIDO,SD1->D1_ITEMPC)
					A103ATURM("+","DED",SD1->D1_DEDUCAO,SD1->D1_PEDIDO,SD1->D1_ITEMPC)
					A103ATURM("+","FAT",SD1->D1_FATDIRE,SD1->D1_PEDIDO,SD1->D1_ITEMPC)
				Endif

				//Verifica se NF foi originada no ColaboraÁ„o / Importador
				//Grava clasfis do monitor
				aNfColab := A103CLASFIS(cNFiscal,cSerie,cA100For,cLoja,aCols[nX,nPosItem],aCols[nX,nPosClaFis])
				If aNfColab[1] 
					If aCols[nX,nPosClaFis] <> aNfColab[2]
						MaFisLoad("IT_CLASFIS",aNfColab[2],nX)
						MaFisLoad("LF_CLASFIS",aNfColab[2],nX)
						MaFisToCols(aHeader,aCols,nX,"MT100") 
					Endif
				Endif

				//Atualiza as informacoes relativas aos impostos
				SF4->(MaFisWrite(2,"SD1",nX))
				
				//Posiciona a TES conforme codigo usado no item
				SF4->(DbSetOrder(1))
				SF4->(dbSeek(xFilial("SF4")+SD1->D1_TES))
				
				If cF4FRETISS <> "2" //Verifica se a TES usa o valor MÌnimo
					cF4FRETISS	:=	SF4->F4_FRETISS
				EndIf
								
				//Desconta o Valor do ICMS DESONERADO do valor do Item D1_VUNIT
				If SF4->F4_AGREG$"R"
					nDedICM += MaFisRet(nX,"IT_DEDICM")
					SD1->D1_TOTAL -= MaFisRet(nX,"IT_DEDICM")
					SD1->D1_VUNIT := A410Arred(SD1->D1_TOTAL/IIf(SD1->D1_QUANT==0,1,SD1->D1_QUANT),"D1_VUNIT")
    			EndIf
				
				//Soma o ICMS Antecipado para geracao Titulo/Guia Recolhimento.
				If cPaisLoc == "BRA"
					IF (SF4->F4_VARATAC$"12") .And. (SD1->D1_ICMSRET > 0 .And. SF4->F4_ANTICMS$"1")
						If !SuperGetMV("MV_ANTICMS",.F.,.F.) .And. Iif(mv_par26 == Nil .Or. Empty(mv_par26), .F., mv_par26 == 1)
							nValIcmAnt += SD1->D1_ICMSRET
							nValIcmSt += 0
						Else
							nValIcmAnt += SD1->D1_ICMSRET - SD1->D1_VALANTI
							nValIcmSt += SD1->D1_VALANTI
						EndIf
					Else
						nValIcmAnt += SD1->D1_VALANTI
					Endif
				Endif
				If Alltrim(SF1->F1_ESPECIE)$"CTR/CTE/NFST/CTEOS" .And. SD1->D1_ICMSRET>0 .And. Alltrim(SF4->F4_CREDST)=="4"
					nSTTrans += SD1->D1_ICMSRET
				EndIf
				// Verifica se houve calculo de PIS/COFINS ou ISS Importacao.
				// O primeiro item que atender as condicoes ja eh suficiente para disparar a geracao do titulo.
				If !lPisCofImp .And. SF1->F1_EST == 'EX' .And. Substr(SD1->D1_CF,1,1) == "3" .And. SD1->(D1_VALIMP5 + D1_VALIMP6) > 0 .And. SF4->F4_DUPLIC == 'S' .And. SF4->F4_INTBSIC <> "0"
					lPisCofImp := .T.
				EndIf
				If !lISSImp .And. SF1->F1_EST == 'EX' .And. Substr(SD1->D1_CF,1,1) == "3" .And. SD1->D1_VALISS > 0 .And. SF4->F4_DUPLIC == 'S'
					lISSImp := .T.
				EndIf
				//Analisa se o documento deve ser bloqueado
				If lBloqueio .Or. (mv_par17==1 .And. ( cFormul=="S" .Or. lBloq103 ) .And. cFunName$"MATA103|FATA720")
					SD1->D1_TESACLA := SD1->D1_TES
					SD1->D1_TES := ""
				EndIf
				//Caio.Santos - 11/01/13 - Req.72
				If lLog
					RSTSCLOG("CLS",1,/*cUser*/)
				EndIf
				//Grava CAT83
				If lCAT83
					GravaCAT83("SD1",{SD1->D1_FILIAL,SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD,SD1->D1_ITEM},"I",1,SD1->D1_CODLAN)
				EndIf

				// Faz chamada para gravacao dos tributos genericos na tabela F2D, bem como o ID do tributo na SD1.
				If lTrbGen
					SD1->D1_IDTRIB	:= MaFisTG(1,"SD1",nX)
				EndIf

				//Posiciona registros
				DbSelectArea("SB1")
				DbSetOrder(1)
				MsSeek(xFilial("SB1")+SD1->D1_COD)

				DbSelectArea("SF4")
				DbSetOrder(1)
				MsSeek(xFilial("SF4")+SD1->D1_TES)

				If SF4->F4_TEMDOCS == "1"
					lTemDocs := .T.
				EndIf

				//Retencao de ISS - Municipio de SBC/SP
				If cPaisLoc == "BRA"
					If SF4->F4_RETISS == "N"
						cMdRtISS := "2"		//Retencao por Base
					Else
						cMdRtISS := "1"		//Retencao Normal
					Endif
				EndIf

				//Atualizacao dos arquivos vinculados ao item do documento
				SD1->D1_TP     := SB1->B1_TIPO
				SD1->D1_GRUPO  := SB1->B1_GRUPO

				//Calculo do custo de entrada
				aCustoEnt := SB1->(A103Custo(nX,aHeadSE2,aColsSE2,,IIF(Len(aCompFutur)>0,aCompFutur[nX],Nil)))
				SD1->D1_CUSTO	:= aCustoEnt[1]
				SD1->D1_CUSTO2	:= aCustoEnt[2]
				SD1->D1_CUSTO3	:= aCustoEnt[3]
				SD1->D1_CUSTO4	:= aCustoEnt[4]
				SD1->D1_CUSTO5	:= aCustoEnt[5]
				
				//GravaÁ„o do campo D1_DATORI
				If  nPosNfOri >0 .And. nPosSerOri>0
					If cTipo$"DB"
						DbSelectArea("SF2")
						DbSetOrder(2)
						MsSeek(xFilial("SF2")+SF1->F1_FORNECE+SF1->F1_LOJA+aCols[nX][nPosNfOri] + aCols[nX][nPosSerOri])
						If !EOF()
						    SD1->D1_DATORI = SF2->F2_EMISSAO
						EndIf
					EndIf
				EndIf

				If lFuncAgreg
					lAgregaOri := AgregaOri(@aItensOri, xFilial("SB8", SD1->D1_FILIAL), SD1->D1_COD, SD1->D1_LOCAL, SD1->D1_DTVALID, SD1->D1_LOTECTL, SD1->D1_NUMLOTE)
				EndIf
				
				//Atualizacao dos acumulados do SD1
				MaAvalSD1(If(SF1->F1_STATUS=="A",4,1),"SD1",lAmarra,lDataUcom,lPrecoDes,lAtuAmarra,aRecSF1Ori,@aContratos,MV_PAR15==2,,,IIF(Len(aCompFutur)>0,aCompFutur[nX],Nil),lAgregaOri)

				If SF1->F1_STATUS$"ABC" //Classificada: Sem bloqueio (NORMAL) / Com Bloqueio
					//Atualizacao do rateio dos itens do documento de entrada
					aCustoSDE := aClone(aCustoEnt)
					AFill(aCustoSDE,0)
					
					//Ponto de Entrada para visualizacao do rateio por centro de custo customizado
					If lMT103RTC
						aMt103RTC := ExecBlock( "MT103RTC", .F., .F.,{aHeadSDE,aColsSDE})
						If ( ValType(aMt103RTC) == 'A' )
							aColsSDE := aMt103RTC
						EndIf
					EndIf
					
					//Ponto de Entrada para visualizacao do rateio por centro de custo customizado
					//com esse ponto pode-se manipular aHeadSDE,aColsSDE
					If lMT103RTE
						aMT103RTE := ExecBlock( "MT103RTE", .F., .F.,{aHeadSDE,aColsSDE,nX})
						If ( ValType(aMT103RTE) == 'A' )
							aHeadSDE := aClone(aMT103RTE[1])
							aColsSDE := aClone(aMT103RTE[2])
						EndIf
					EndIf
					nUsadoSDE := Len(aHeadSDE)

					If SD1->D1_RATEIO == "1" .And. (nY	:= aScan(aColsSDE,{|x| x[1] == SD1->D1_ITEM})) > 0
						For nZ := 1 To Len(aColsSDE[nY][2])
							If !aColsSDE[nY][2][nZ][nUsadoSDE+1]
								SDE->(DbSetOrder(1))
								lAchou:=SDE->(MsSeek(cFilSDE+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_ITEM+GdFieldGet("DE_ITEM",nz,NIL,aHeadSDE,ACLONE(aColsSDE[NY,2]))))
								RecLock("SDE",!lAchou)
								For nW := 1 To nUsadoSDE
									If aHeadSDE[nW][10]<>"V" .And. aColsSDE[nY][2][nZ][nW]<>Nil
										SDE->(FieldPut(FieldPos(aHeadSDE[nW][2]),aColsSDE[nY][2][nZ][nW]))
									EndIf
								Next nW
								SDE->DE_FILIAL	:= cFilSDE
								SDE->DE_DOC		:= SD1->D1_DOC
								SerieNfId("SDE",1,"DE_SERIE",,,, SD1->D1_SERIE )
								SDE->DE_FORNECE	:= SD1->D1_FORNECE
								SDE->DE_LOJA	:= SD1->D1_LOJA
								SDE->DE_ITEMNF	:= SD1->D1_ITEM
								For nW:= 1 To Len(aCustoEnt)
									SDE->(FieldPut(FieldPos("DE_CUSTO"+Alltrim(str(nW))),aCustoEnt[nW]*(SDE->DE_PERC/100)))
									aCustoSDE[nW] += SDE->(FieldGet(FieldPos("DE_CUSTO"+Alltrim(str(nW)))))
								Next nW
								If SF4->F4_DUPLIC=="S"
									nW := aScan(aSEZ,{|x| x[1] == SDE->DE_CC .And. x[2] == SDE->DE_ITEMCTA .And. x[3] == SDE->DE_CLVL })
									If nW == 0
										aadd(aSEZ,{SDE->DE_CC,SDE->DE_ITEMCTA,SDE->DE_CLVL,0,0,SDE->DE_CONTA})
										nW := Len(aSEZ)
										// Tratamento para entidades contabeis adicionais
										For nJ := 1 To Len(aCTBEnt)
											If aScan(aHeadSDE,{|x| AllTrim(x[2]) == "DE_EC"+aCTBEnt[nJ]+"DB"}) > 0
												aAdd(aSEZ[nW],SDE->&("DE_EC"+aCTBEnt[nJ]+"DB"))
											EndIf
											If aScan(aHeadSDE,{|x| AllTrim(x[2]) == "DE_EC"+aCTBEnt[nJ]+"CR"}) > 0
												aAdd(aSEZ[nW],SDE->&("DE_EC"+aCTBEnt[nJ]+"CR"))
											EndIf
										Next nJ
									EndIf
									If nZ <> Len(aColsSDE[nY][2])
										aSEZ[nW][5] += SDE->DE_CUSTO1
									EndIf
								EndIf
								//Grava os campos Memos Virtuais da Tabela SDE
								If laMemoSDE
									For nM := 1 to Len(aMemoSDE)
										nPosMemo := aScan(aHeadSDE,{|x| AllTrim(x[2])== aMemoSDE[nM][2] })
										If nPosMemo <> 0 .And. !Empty(aColsSDE[nY][2][nZ][nPosMemo])
											MSMM(aMemoSDE[nM][1],,,aColsSDE[nY][2][nZ][nPosMemo],1,,,"SDE",aMemoSDE[nM][1])
										EndIf
									Next nM
								EndIf
							EndIf
							If nZ == Len(aColsSDE[nY][2])
								For nW := 1 To Len(aCustoEnt)
									SDE->(FieldPut(FieldPos("DE_CUSTO"+Alltrim(str(nW))),FieldGet(FieldPos("DE_CUSTO"+Alltrim(str(nW))))+aCustoEnt[nW]-aCustoSDE[nW]))
								Next nW
								nW := aScan(aSEZ,{|x| x[1] == SDE->DE_CC .And. x[2] == SDE->DE_ITEMCTA .And. x[3] == SDE->DE_CLVL })
								If nW <> 0
									aSEZ[nW][5] += SDE->DE_CUSTO1
								EndIf
							EndIf
							
							//Ponto de Entrada para o Template
							If lTSDE100I
								ExecTemplate("SDE100I",.F.,.F.,{lConFrete,lConImp,nOper,Len(aColsSDE[nY][2])})
							EndIf
							If lSDE100I
								ExecBlock("SDE100I",.F.,.F.,{lConFrete,lConImp,nOper,Len(aColsSDE[nY][2])})
							Endif

							//Gera Lancamento contabil 641- Devolucao / Beneficiamento
							If SF1->F1_STATUS == "A"
								If lCtbOnLine
									If cTipo $ "BD"
										If lVer641
											nTotalLcto	+= DetProva(nHdlPrv,"641","MATA103",cLote)
										EndIf
									Else
										If lVer651
											nTotalLcto	+= DetProva(nHdlPrv,"651","MATA103",cLote)
										EndIf
									EndIf
								EndIf
								//Grava os lancamentos nas contas orcamentarias SIGAPCO
								Do Case
									Case cTipo == "B"
										PcoDetLan("000054","11","MATA103")
									Case cTipo == "D"
										PcoDetLan("000054","10","MATA103")
									OtherWise
										PcoDetLan("000054","09","MATA103")
								EndCase
							EndIf
						Next nZ
						//Elimina Registros na SDE que n„o existem mais no Acols
						//Esta situacao podera ocorrer quando a SDE ja estiver gravada seja atravÈs de
						//Pre-Nota ou bloqueio de Tolerancia e em seguida no momento da classificacao o
						//Array ser manipulado
						nPosDeIt := aScan(aHeadSDE,{|x| Alltrim(x[2])=='DE_ITEM'})
						DbSelectArea("SDE")
						DbSetOrder(1)
						MsSeek(cFilSDE+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_ITEM)
						While !Eof() .And. DE_FILIAL == cFilSDE .And. DE_DOC == SF1->F1_DOC .And. DE_SERIE == SF1->F1_SERIE .And.;
						              DE_FORNECE == SF1->F1_FORNECE .And. DE_LOJA == SF1->F1_LOJA .And. DE_ITEMNF == SD1->D1_ITEM
							nW:=0
							For nZ:=1 to Len(aColsSDE[nY][2])
								If aColsSDE[nY][2][nZ][nPosDeIt]==DE_ITEM
									nW:=nW+1
									exit
								EndIf
							Next nZ  
							If nW==0
								RecLock("SDE",.F.)
								dbDelete()
							EndIf
							DbSkip()
						EndDo
					EndIf
					//Tratamento da gravacao do SDE na Integridade Referencial
					SDE->(FkCommit())
				EndIf

				// Gravacao DHP - Aposentadoria Especial
				If lChkDHP .And. Len(aColsDHP) > 0 .And. (nY	:= aScan(aColsDHP,{|x| x[1] == SD1->D1_ITEM})) > 0
					If !Empty(aColsDHP[nY][2])
						DHP->(DbSetOrder(1))
						If !aColsDHP[nY][2][1][Len(aHeadDHP)+1]
							lAchou := DHP->(MsSeek(xFilial("DHP")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_ITEM))
							RecLock("DHP",!lAchou)
							For nZ := 1 To Len(aHeadDHP)
								If aHeadDHP[nZ][10] <> "V" .And. aColsDHP[nY][2][1][nZ] <> Nil
									DHP->(FieldPut(FieldPos(aHeadDHP[nZ][2]),aColsDHP[nY][2][1][nZ]))
								EndIf
							Next nZ
							DHP->DHP_FILIAL := xFilial("DHP")
							DHP->DHP_DOC    := SD1->D1_DOC
							DHP->DHP_SERIE  := SD1->D1_SERIE
							DHP->DHP_FORNEC := SD1->D1_FORNECE
							DHP->DHP_LOJA   := SD1->D1_LOJA
							DHP->DHP_ITEMNF := SD1->D1_ITEM
							DHP->(MsUnlock())
						Else // Deleta DHP caso item tenha sido excluido pela interface
							If DHP->(MsSeek(xFilial("DHP")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_ITEM))
								RecLock("DHP",.F.)
								DHP->(dbDelete())
								DHP->(MsUnlock())
							EndIf
						EndIf
					EndIf
					// Tratamento da gravacao do DHP na Integridade Referencial
					DHP->(FkCommit())
				EndIf
				
				// Gravacao DHR - Natureza de Rendimento
				If lChkDHR .And. Len(aCoSusDHR) == 0 .And. Len(aColsDHR) > 0 .And. (nY	:= aScan(aColsDHR,{|x| x[1] == SD1->D1_ITEM})) > 0
					A103INCDHR(aHeadDHR,aColsDHR,nY,.F.)
				Endif	
				
				// Gravacao DHR - Natureza de Rendimento - SUSPENS√O
				If lChkDHR .And. Len(aCoSusDHR) > 0 .And. (nY	:= aScan(aCoSusDHR,{|x| x[1] == SD1->D1_ITEM})) > 0
					A103INCDHR(aHdSusDHR,aCoSusDHR,nY,.T.)
				EndIf

				//GravaÁ„o DKD - Complementos dos itens da NF
				If (type("lDKD") == "L" .and. lDKD) .And. (type("lTabAuxD1") == "L" .and. lTabAuxD1) .And. Type("aColsDKD") == "A" .And. Len(aColsDKD) > 0 .And. (nY	:= aScan(aColsDKD,{|x| x[1] == SD1->D1_ITEM})) > 0
					A103DKDGRV(aHeadDKD,aColsDKD,nY)
				Endif

				If SF1->F1_STATUS == "A" //Classificada sem bloqueio (NORMAL)
					//Integracao com Gestao Hospitalar, valorizacao pela Ultima Compra
					If lIntGH
						cSql := " UPDATE "+ RetSqlName("GCB")
						cSql += "    SET GCB_PRCVEN =  " + Alltrim(Str(aCols[nX][nPosVUnit])) + ",GCB_PRCVUC = " + Alltrim(Str(aCols[nX][nPosVUnit]))
						cSql += "  WHERE GCB_PRODUT = '" + aCols[nX][nPosCod] + "' AND GCB_ATIVO = '1' AND D_E_L_E_T_ = ' ' "
						cSql += "    AND GCB_VALUC = '1'  "

						If TcSqlExec(cSql)  < 0
							Hs_MsgInf(TcSqlError(),STR0119,STR0334)
							Return(nil) 
						EndIf
						cSql := " UPDATE "+ RetSqlName("GCB")
						cSql += "    SET GCB_PRCVEN =  (GCB_PRCVUC + " + AllTrim(Str(aCols[nX][nPosVUnit])) + " ) / 2 ,GCB_PRCVUC = (GCB_PRCVUC + " + Alltrim(Str(aCols[nX][nPosVUnit])) + " ) / 2 "
						cSql += "  WHERE GCB_PRODUT = '" + Alltrim(aCols[nX][nPosCod]) + "' AND GCB_ATIVO = '1' AND D_E_L_E_T_ = ' ' "
						cSql += "    AND GCB_VALUC = '2'  "

						If TcSqlExec(cSql)  < 0
							Hs_MsgInf(TcSqlError(),STR0119,STR0334)
							Return(nil)
						EndIf
					EndIf

					//Efetua a Gravacao do Ativo Imobilizado
					If ( SF4->F4_ATUATF=="S" ) .And. !(SF1->F1_TIPO $ "I|P")
						INCLUI     := .T.
						ALTERA     := .F.
						cBaseAtf   := ""
						cCodCIAPD1 := ""
						if ( ( (Alltrim(cEspecie) == "CTE" .and. lAgVlrATF) .OR. ( !empty(SD1->D1_CBASEAF) .and. cTipo == "N") ) ) .and. ( FwIsInCallStack("MATA103") .OR. FwIsInCallStack("MATA116") )
							cChaveSD1 := if(Alltrim(cEspecie) == "CTE",SD1->(D1_FILIAL+D1_NFORI+D1_SERIORI+D1_FORNECE+D1_LOJA),SD1->(D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA))
							if empty(aRecSF1Ori) .and. AllTrim(SF1->F1_ORIGEM) == 'COMXCOL'
							//Resgato o recno da NF de origem para achar a nota de origem
								nRegSF1 := getNfOri(SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA,1)
								if nRegSF1 > 0
									aAdd(aRecSF1Ori, nRegSF1)
								endif
							EndIf
							lContinua := a103GrvAtf(104,,,,,,,,,,aRecSF1Ori,cChaveSD1,SD1->D1_CBASEAF)//AtualizaÁ„o de valor dos bens.
						else
							If ( SF4->F4_BENSATF == "1" .And. At(SF1->F1_TIPO,"CIP")==0 ) .And. SD1->D1_QUANT >= 1
								If (SD1->D1_TIPO == "C") .Or. (SD1->D1_TIPO == "I")
									nQtdD1 := GetQOri(cFilSD1,SD1->D1_NFORI,SD1->D1_SERIORI,SD1->D1_ITEMORI,;
										SD1->D1_COD,SD1->D1_FORNECE,SD1->D1_LOJA)
								Else
									nQtdD1 := Int(SD1->D1_QUANT)
								Endif
								aDIfDec	:= {0,.F.,0}
								aVlrAcAtf	:=	{0,0,0,0,0}
								//inicia cAux zerado, de acordo com o tamanho do campo item (Ex. '0000')
								cAux := Replicate("0", Len(SN1->N1_ITEM))
								If isBlind()
									lContinua := A103MultATF(nQtdD1,lATFDCBA,SF4->F4_CIAP,cMvfsnciap,aDIfDec,cAno)
								Else
									If !FindFunction('JobMultATF') .Or. (FindFunction('JobMultATF') .And. !JobMultATF(,,.F.)) // .F. Verifica se gera atraves de job / .T. Executa o Job
										MsgRun(STR0415,"",{|| lContinua := A103MultATF(nQtdD1,lATFDCBA,SF4->F4_CIAP,cMvfsnciap,aDIfDec,cAno)})//"Gerando Fichas de Ativo Imobilizado"
									EndIf
								EndIf
							Else
								cItemAtf := StrZero(1,Len(SN1->N1_ITEM))
								aVlrAcAtf:=	{0,0,0,0,0}
								If SF4->F4_CIAP=="S" .AND. SF4->F4_CREDICM=="S"
									If SD1->D1_VALICM  > 0 //N„o preencher o campo  N1_ICMSAPR quando n„o houver c·lculo CIAP  
									nVlrICMS := SD1->D1_VALICM
								EndIf 	  						
								If AllTrim(cDACiap) == "S"
									nVlrICMS += SD1->D1_ICMSCOM
								EndIf
								cCodCIAPD1 := SD1->D1_CODCIAP
								EndIf
								lContinua := a103GrvAtf(1,@cBaseAtf,cItemAtf,cCodCIAPD1,nVlrICMS,,@aVlrAcAtf)
							EndIf
						Endif
						If !lContinua
							Help(" ",1,STR0178,,STR0436,1,0)	//'Este documento n„o sera gravado devido a inconsistencias na gravaÁ„o do ativo fixo"
							Return .F.
						EndIf
					EndIf

					//Integracao TMS
					If lIntTMS .And. (Len(aRatVei)>0  .Or. Len(aRatFro)>0)
						//Verifica se o Item da NF foi rateado por Veiculo/Viagem ou por Frota
						nItRat := aScan(aRatVei,{|x| x[1] == SD1->D1_ITEM})
						If nItRat > 0
							A103GrvSDG('SD1',aRatVei,"V",SD1->D1_ITEM,lCtbOnLine,nHdlPrv,@nTotalLcto,cLote,"MATA103")
						Else
							nItRat := aScan(aRatFro,{|x| x[1] == SD1->D1_ITEM})
							If nItRat > 0
								A103GrvSDG('SD1',aRatFro,"F",SD1->D1_ITEM,lCtbOnLine,nHdlPrv,@nTotalLcto,cLote,"MATA103")
							EndIf
						EndIf
					EndIf
					
					//IntegraÁ„o com o WMS
					If SF4->F4_ESTOQUE=="S" .AND. IntWMS(SD1->D1_COD) .And. cTipo $ "N|D|B"  
						If !WmsAvalSD1("5","SD1")
							DisarmTransaction()
							Return
						EndIf 
					Endif
					
					//Ponto de entrada apos a gravacao do SD1 e todas atualizacoes
					If lIntMnt
						If FindFunction("NGSD1STL")
							NGSD1STL(cAliasTPZ, SD1->D1_FILIAL, SD1->D1_DOC, SD1->D1_SERIE, SD1->D1_FORNECE, SD1->D1_LOJA, SD1->D1_COD, SD1->D1_ITEM, .T.)
						Else
							NGSD1100I(cAliasTPZ)
						EndIf
					EndIf
					
					//Ponto de Entrada para o Template
					If lDclNew
						DCLSD1100I()
					ElseIf lTSD1100I
						ExecTemplate("SD1100I",.F.,.F.,{lConFrete,lConImp,nOper})
					EndIf

					If lSD1100I
						ExecBlock("SD1100I",.F.,.F.,{lConFrete,lConImp,nOper})
					Endif

					//Executa a Baixa da NFE X Tabela de Quantidade Prevista
					A103AtuPrev(lDeleta)

					//Contabilizacao do item do documento de entrada
					If lCtbOnline
						If cTipo $ "BD" .And. lVer640
							nTotalLcto	+= DetProva(nHdlPrv,"640","MATA103",cLote)
						Else
							If lVer650

								cCtaRec := "" // Limpa a variavel devido processamento em laco

								nTotalLcto	+= DetProva(nHdlPrv,"650","MATA103",cLote,,,,,,,,,,,,,,,@cCtaRec)

								// Adequacao para Gravar a Conta de Receita do Item da Nota, para uso no EFD-ContribuiÁıes
								If lD1CtaRec .And. !Empty(cCtaRec)
									Aadd(aFlagCTB,{"D1_CTAREC",cCtaRec,"SD1",SD1->(Recno()),0,0,0})
									If lRefCtaRec
										MaFisLoad("IT_CTAREC",cCtaRec,nX)
									EndIf
								EndIf

							EndIf
						EndIf
					EndIf

					//Grava os lancamentos nas contas orcamentarias SIGAPCO
					Do Case
						Case cTipo == "B"
							PcoDetLan("000054","07","MATA103")
						Case cTipo == "D"
							PcoDetLan("000054","05","MATA103")
						OtherWise
							PcoDetLan("000054","01","MATA103")
					EndCase
				EndIf
				
				//Grava Pedido de Venda
				If ( lGeraPV )
					aadd(aPedPV,{SD1->D1_SERIORI,;
								 SD1->D1_NFORI ,;
								 SD1->D1_ITEMORI,;
								 SD1->D1_FORNECE+SD1->D1_LOJA,;
								 SD1->D1_QUANT ,;
								 SD1->(Recno()) })
				EndIf

				//Atualiza saldo no Armazem de Poder de Terceiros
				TrfSldPoder3(SD1->D1_TES,"SD1",SD1->D1_COD)

				//Atualiza Consumo Medio SB3 somente para os casos abaixo:
				// TES que atualiza estoque
				// Devolucao de Vendas
				// Devolucao de produtos em Poder de Terceiros
				If (SD1->D1_TIPO == "D" .Or. SF4->F4_PODER3 == "D") .And. SF4->F4_ESTOQUE == "S"
					aAreaAnt := GetArea()
					cMes := "B3_Q"+StrZero(Month(SD1->D1_DTDIGIT),2)
					SB3->(dbSeek(xFilial("SB3")+SD1->D1_COD))
					If SB3->(Eof())
						RecLock("SB3",.T.)
						Replace B3_FILIAL With xFilial("SB3"), B3_COD With SD1->D1_COD
					Else
						RecLock("SB3",.F.)
					EndIf
					Replace &(cMes) With &(cMes) - SD1->D1_QUANT
					MsUnlock()
					RestArea(aAreaAnt)
				EndIf
				//Atualiza saldo no Armazem de Transito - MV_LOCTRAN				
				A103TrfSld(lDeleta,1)				

				//Atualiza o Indicador F2_FLAGDEV quando devoluÁ„o for Manual
				If lFlagDev .And. SD1->D1_TIPO$"DB" .And. lA103PROCDV
				    //Verifica se todos os itens referente a nota indicada foram devolvidos
				    nQTDDEV :=0
					DbSelectArea("SD2")
					DbSetOrder(3)
					MsSeek(xFilial("SD2")+SD1->D1_NFORI+SD1->D1_SERIORI+SF1->F1_FORNECE+SF1->F1_LOJA)
					While !Eof() .And. D2_FILIAL  == xFilial("SD2");
					              .And. D2_DOC     == SD1->D1_NFORI;
					              .And. D2_SERIE   == SD1->D1_SERIORI;
		   						  .And. D2_CLIENTE == SF1->F1_FORNECE;
		   						  .And. D2_LOJA    == SF1->F1_LOJA

		   				//Verifica se possui Tes de DevoluÁ„o amarrada
		   				DbSelectArea("SF4")
						DbSetOrder(1)
						If MsSeek(xFilial("SF4")+SD2->D2_TES)
							If !Empty(SF4->F4_TESDV)
							    MsSeek(xFilial("SF4")+SF4->F4_TESDV)
							    IF SF4->F4_PODER3<>"D"  //Quando for Tes DevoluÁ„o, n„o considera pois poder· ter Controle de Terceiros
							        nQTDDEV:=nQTDDEV + SD2->D2_QUANT-SD2->D2_QTDEDEV
							    EndIf
							EndIf
						EndIf
						//Verifica se Possui Controle em Terceiros
						If SD2->D2_QTDEDEV == 0 .And. !Empty(SD2->D2_IDENTB6)
							DbSelectArea("SB6")
							DbSetOrder(3)
							If MsSeek(xFilial("SB6")+SD2->D2_IDENTB6+SD2->D2_COD+"R")
								nQTDDEV:=nQTDDEV+SB6->B6_SALDO
							EndIf
						EndIf
						DbSelectArea("SD2")
						dbSkip()
					EndDo

					//Grava indicador de devolucao se a nota j· estiver totalmente devolvida
					if nQTDDEV == 0
						DbSelectArea("SF2")
						DbSetOrder(2)
						MsSeek(xFilial("SF2")+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_NFORI+SD1->D1_SERIORI)
						If !EOF() .And. cPaisLoc == "BRA"
							RecLock("SF2",.F.)
							SF2->F2_FLAGDEV := "1"
							MsUnLock()
						EndIf
					Endif
				Endif

				If lIntGC
					DbSelectArea("SF2")
					DbSetOrder(2)
					MsSeek(xFilial("SF2")+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_NFORI+SD1->D1_SERIORI)
					lOrigem := SF2->F2_PREFORI $ cPrefBAL .Or.  SF2->F2_PREFORI $ cPrefOFI
				EndIf	

				//Dados para envio de email do messenger
				AADD(aDetalheMail,{SD1->D1_ITEM,SD1->D1_COD,SD1->D1_QUANT,SD1->D1_TOTAL})

				If lDistMov .and. Localiza(SD1->D1_COD) .And. SF4->F4_ESTOQUE == 'S' 
					If !(SD1->D1_LOCAL == Alltrim(cLocCQ) .And. (Alltrim(cLocCQ) $ left(Alltrim(cDistAut),nTamLoc))) 
						aADD(aDigEnd,{;
										SD1->D1_ITEM,;
										SD1->D1_COD,;
										SD1->D1_LOCAL,;
										SD1->D1_LOTECTL,;
										SD1->D1_NUMLOTE,;
										SD1->D1_DTVALID,;
										SD1->D1_QUANT,;
										SD1->D1_NUMSEQ,;
										SD1->D1_DOC,;
										SD1->D1_SERIE,;
										SD1->D1_FORNECE,;
										SD1->D1_LOJA,;
										.F.;
									 })
					EndIf
				EndIf
			Else
				If  nX <= Len(aRecSD1)
					SD1->(MsGoto(aRecSD1[nx,1]))
					RecLock("SD1",.F.)
					//Estorna os acumulados da Pre-Nota
					MaAvalSD1(2) 

					//GravaÁ„o DKD - Complementos dos itens da NF
					If (type("lDKD") == "L" .and. lDKD) .And. (type("lTabAuxD1") == "L" .and. lTabAuxD1) .And. Type("aColsDKD") == "A" .And. Len(aColsDKD) > 0 .And. (nY	:= aScan(aColsDKD,{|x| x[1] == SD1->D1_ITEM})) > 0
						A103DKDGRV(aHeadDKD,aColsDKD,nY,"D")
					Endif 

					SD1->(dbDelete())
					SD1->(MsUnLock())
					//Caio.Santos - 11/01/13 - Req.72
					If lLog
						RSTSCLOG("CLS",2,/*cUser*/)
					EndIf
				EndIf
			EndIf
			
		 	//SÛ ir· incluir o Armamento quando a integraÁ„o estiver ativada
		 	If cMV_GSXNFE
		 		aAreaSB5 := SB5->(GetArea())
		 		DbSelectArea('SB5')
				SB5->(DbSetOrder(1)) // acordo com o arquivo SIX -> A1_FILIAL+A1_COD+A1_LOJA
				If SB5->(DbSeek(xFilial('SB5')+SD1->D1_COD)) // Filial: 01, CÛdigo: 000001, Loja: 02
			       	Do Case
			       		Case SB5->B5_TPISERV=='1'
					       		aT710Imp()
	       				Case SB5->B5_TPISERV=='2'
			       				aT720Imp()
						Case SB5->B5_TPISERV=='3'
			       				aT730Imp(SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD,SD1->D1_ITEM)
					EndCase
				EndIf
				RestArea(aAreaSB5)
			EndIf

		Next nX

		//Acerta gravaÁ„o da tabela SD1 apÛs importaÁ„o de pedido com itens diferentes da Pre Nota
		If l103Class .And. (nX <= Len(aRecSD1) .Or. lImpPedido)  // Verifica se houve importaÁ„o de pedidos ou itens deletados
			For nZ := 1 to Len(aRecSD1)
				If (nRec := aScan(aCols,{|x| x[nPosItem] == aRecSD1[nZ,2]})) = 0
					SD1->(MsGoto(aRecSD1[nZ,1]))

					// Faz chamada para exclusao dos tributos genericos
					If lTrbGen .AND. !Empty(SD1->D1_IDTRIB)
						MaFisTG(2,,,SD1->D1_IDTRIB)
					EndIf

					RecLock("SD1",.F.)
					
					//Estorna os acumulados da Pre-Nota
					MaAvalSD1(2)
					SD1->(dbDelete())
					SD1->(MsUnLock())
					//Caio.Santos - 11/01/13 - Req.72
					If lLog
						RSTSCLOG("CLS",2,/*cUser*/)
					EndIf
				Endif
			Next nZ
		EndIf
		
		//Atualiza os acumulados do Cabecalho do documento
		MaAvalSF1(4)
		
		If Type("lContDCL") <> "U" .And. lContDCL
			a103GrvCDA(lDeleta,"E",cEspecie,cFormul,cNFiscal,SF1->F1_SERIE,cA100For,cLoja )
			If FindFunction("a017GrvCDV") 
				a017GrvCDV(lDeleta,"E",cEspecie,cFormul,cNFiscal,SF1->F1_SERIE,cA100For,cLoja )
			Endif
			// Nova funcao de geracao de titulos/guias a partir da CDA.
			If cPaisLoc == "BRA" .And. FindFunction("FisTitCDA")
				aTitCDA := FisTitCDA("MATA103", "E", SF1->(RecNo()))
			EndIf
		Endif

		//Gera os titulos no Contas a Pagar SE2
		If SF1->F1_STATUS == "A" //Classificada sem bloqueio
			If !(cTipo$"DB")
				//Ponto de Entrada para definir se ir· gerar lanÁamento futuro(SRK) ou tÌtulo no financeiro (SE2)
				If (ExistBlock("M103GERT"))
					ExecBlock("M103GERT",.F.,.F.,{1,aRecSE2,aHeadSE2,aColsSE2,aHeadSEV,aColsSEV,cFornIss,cLojaIss,cDirf,cCodRet,cModRetPIS,nIndexSE2,aSEZ,dVencIss,cMdRtISS,SF1->F1_TXMOEDA,lTxNeg,aRecGerSE2,cA2FRETISS,cB1FRETISS,aMultas,lRatLiq,lRatImp,aCodR,cRecIss})
				Else
					If Empty(SF1->F1_NUMRA)
						If lCtbOnLine
							//Guarda cFileCtb e nHandle da MATA103
							cMTFileCtb 	:= GetHFile()
							nMTHandle 	:= GetHProva()

							//Metricas - Quantidade de documento de entrada que gerou titulos
							If aColsSE2[1][nPValor] > 0
								nQtdTit++
								ComMtQtd("-inc",l103Auto,l103Class,cTipo,nQtdTit,cFunc)
							EndIf

							//Rotina de integracao com o modulo financeiro
							A103AtuSE2(1,aRecSE2,aHeadSE2,aColsSE2,aHeadSEV,aColsSEV,cFornIss,cLojaIss,cDirf,cCodRet,cModRetPIS,nIndexSE2,aSEZ,dVencIss,cMdRtISS,SF1->F1_TXMOEDA,lTxNeg,aRecGerSE2,cA2FRETISS,cB1FRETISS,aMultas,lRatLiq,lRatImp,aCodR,cRecIss,lPisCofImp,aTitImp,lIssImp,lTemDocs,,aParcTrGen,aRecSEV,cIdsTrGen,cF4FRETISS)

							//Guarda cFileCtb e nHandle da FINA050
							//cFIFileCtb 	:= GetHFile()	 //N„o utilizado, mantido em cÛdigo para facilitar implantaÁ„o futura
							//nFIHandle 	:= GetHProva()	 //N„o utilizado, mantido em cÛdigo para facilitar implantaÁ„o futura

							//Restaura cFileCtb e nHandle da MATA103 para apresentar tela de contabilizaÁ„o on-line na chamada da cA100Incl.
							PutHFile(cMTFileCtb,nMTHandle)
						Else
							//Rotina de integracao com o modulo financeiro
							A103AtuSE2(1,aRecSE2,aHeadSE2,aColsSE2,aHeadSEV,aColsSEV,cFornIss,cLojaIss,cDirf,cCodRet,cModRetPIS,nIndexSE2,aSEZ,dVencIss,cMdRtISS,SF1->F1_TXMOEDA,lTxNeg,aRecGerSE2,cA2FRETISS,cB1FRETISS,aMultas,lRatLiq,lRatImp,aCodR,cRecIss,lPisCofImp,aTitImp,lIssImp,lTemDocs,,aParcTrGen,aRecSEV,cIdsTrGen,cF4FRETISS)
							//Metricas - Quantidade de documento de entrada que gerou titulos
							If aColsSE2[1][nPValor] > 0
								nQtdTit++
								ComMtQtd("-inc",l103Auto,l103Class,cTipo,nQtdTit,cFunc)
							EndIf
						EndIf

						If cPaisLoc $ "BRA|MEX"
							If A120UsaAdi(cCondicao) .and. MaFisRet(,"NF_BASEDUP") > 0
								aAreaAnt := GetArea()
								For nCntAdt := 1 to Len(aCols)
									If !Empty(gdFieldGet("D1_PEDIDO",nCntAdt)) .and. !Empty(gdFieldGet("D1_ITEMPC",nCntAdt)) .and. !gdDeleted(nCntAdt)
										If AvalTes(gdFieldGet("D1_TES",nCntAdt),,"S")
											If Len(aPedAdt) > 0
												nPosAdt := aScan(aPedAdt,{|x| x[1] == gdFieldGet("D1_PEDIDO",nCntAdt)})
											Endif
											If nPosAdt <= 0
												aAdd(aPedAdt,{gdFieldGet("D1_PEDIDO",nCntAdt),IIf(MaFisFound("IT",nCntAdt),MaFisRet(nCntAdt,"IT_TOTAL"),gdFieldGet("D1_QUANT",nCntAdt)*gdFieldGet("D1_VUNIT",nCntAdt))})
											Else
												aPedAdt[nPosAdt][2] += IIf(MaFisFound("IT",nCntAdt),MaFisRet(nCntAdt,"IT_TOTAL"),gdFieldGet("D1_QUANT",nCntAdt)*gdFieldGet("D1_VUNIT",nCntAdt))
											Endif
										EndIf
									Endif
								Next nCntAdt
								lCompAdt := .T.
								RestArea(aAreaAnt)
							EndIf
						Endif
					Else
						aRet := A103AtuSRK(1,aHeadSE2,aColsSE2)
						If !aRet[1]
							Help( ,,"ATUSRK",,aRet[2], 1, 0 )
							DisarmTransaction()
							Return .F.
						Endif
					EndIf
				EndIf

				//Contabilizacao Rateio Centro de Custo Multipla Natureza
				If lCtbOnLine
					If lVer65C .And. lMulNats .And. Len(aRecSEV) > 0
						For nX := 1 To Len(aRecSEV)
							SEV->(MsGoto(aRecSEV[nX]))
							nTotalLcto	+= DetProva(nHdlPrv,"65C","MATA103",cLote)
							SEV->(RecLock("SEV",.F.))
							SEV->EV_LA := "S"
							MsUnlock()
						Next nX
					EndIf
				EndIf
				//Desconta o Valor do ICMS DESONERADO do valor do Item D2_PRCVEN
				If nDedICM > 0
					SF1->F1_VALMERC -= nDedICM
				EndIf
				
				//Gera Guia de Recolhimento ou Titulo ICMS no Contas a pagar quando houver no documento de
				//entrada ICMS por Antecipacao Tributaria.
				If  nValIcmAnt > 0 .And. cPaisLoc=="BRA" .And. ( cFunName$"MATA103|MATA116" .Or. (IsBlind() .And. IsInCallStack("MATA103")) )

					lIcmsTit  := Iif(mv_par18==Nil,.F.,(mv_par18==1))
					lIcmsGuia := Iif(mv_par19==Nil,.F.,(mv_par19==1))
					lAntParcBA := Iif(mv_par25==Nil,.F.,(mv_par25==1))
					lGeraGuia := .T.
					If lIcmsTit .Or. lIcmsGuia
						If ExistBlock("MT103GUIA")
							lGeraGuia := ExecBlock("MT103GUIA",.F.,.F.,{"SF1","SA2",xFilial("SA2"),SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_ESPECIE})
						Endif
						if lGeraGuia
							aDataGuia := DetDatas(Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),3,1)
							//Armazenamento dos dados para ser utilizado na Guia de Recolhimento
							aadd(aDadosSF1,{SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_TIPO,"1",SuperGetMV("MV_ESTADO"),SF1->F1_ESPECIE,.T.}) // Adicionei posiÁ„o 8 para trazer a especie na geraÁ„o da guia na entrada e a posiÁ„o 9 para confirmar operaÁ„o com AntecipaÁ„o
							nValFecp := MaFisRet(,"NF_VALFECP") + MaFisRet(,"NF_VFECPST")
							If SuperGetMV("MV_TITSEP",, .F.) .And. nValFecp > 0
								GravaTit(lIcmsTit,(nValIcmAnt-nValFecp),"ICMS","IC",cLcPadICMS,aDataGuia[1],aDataGuia[2],DataValida(aDataGuia[2]+1,.T.),1,lIcmsGuia,Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),0,(nValIcmAnt-nValFecp),"MATA103",lCtbOnLine,cNFiscal,@aGNRE,,,,,,,,,,0,aDadosSF1,,,,,,,,,,,,,,,lAntParcBA)
								GravaTit(lIcmsTit,nValFecp,             "ICMS","IC",cLcPadICMS,aDataGuia[1],aDataGuia[2],DataValida(aDataGuia[2]+1,.T.),1,lIcmsGuia,Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),0,(nValFecp),           "MATA103",lCtbOnLine,cNFiscal,@aGNRE,,,,,.T.,,,,,0,aDadosSF1)
							Else
								GravaTit(lIcmsTit,nValIcmAnt,"ICMS","IC",cLcPadICMS,aDataGuia[1]/*Dt inic*/,aDataGuia[2]/*Dt Fim*/,DataValida(aDataGuia[2]+1,.T.) /*Dt Venc*/,1,lIcmsGuia,Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),0,nValIcmAnt,"MATA103",lCtbOnLine,cNFiscal,@aGNRE,,,,,,,,,,0,aDadosSF1,,,,,,,,,,,,,,,lAntParcBA)
							EndIf
							If nValIcmSt > 0 .And. Iif(mv_par26 == Nil .Or. Empty(mv_par26), .F., mv_par26 == 1)
								//Armazenamento dos dados para ser utilizado na Guia de Recolhimento
								aadd(aDadosSF1,{SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_TIPO,"1",SuperGetMV("MV_ESTADO")})
								GravaTit(lIcmsTit,nValIcmSt,"ICMS","IC",cLcPadICMS,aDataGuia[1],aDataGuia[2],DataValida(aDataGuia[2]+1,.T.),1,lIcmsGuia,Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),0,nValIcmSt,"MATA103",lCtbOnLine,cNFiscal,@aGNRE,,,,,,,,,,0,aDadosSF1,,,,,,,,,,,,,,,lAntParcBA)
							EndIf
						Endif
					Endif
				Endif

				nValIcmcom := MaFisRet(,"NF_VALCMP")

				//Gera Guia de Recolhimento e/ou Titulo ICMS no Contas a pagar quando houver no documento de
				//entrada com ICMS Complementar /DIFAl
				If  nValIcmCom > 0 .And. cPaisLoc=="BRA" .And. ( cFunName$"MATA103|MATA116" .Or. (IsBlind() .And. IsInCallStack("MATA103")) )

					lDifTit	:= Iif(VALTYPE(mv_par29)<>"N",.F.,(mv_par29==1)) //gera titulo de ICMS complenetar/difal?
					lCompDifal := Iif(VALTYPE(mv_par30)<>"N",.F.,(mv_par30==1)) //gera guia de recolhimento de ICMS complementar/DIFAL ?
					lGeraGuia := .T.
					
					If ExistBlock("MT103GUIA")
						lGeraGuia := ExecBlock("MT103GUIA",.F.,.F.,{"SF1","SA2",xFilial("SA2"),SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_ESPECIE})
					Endif
					If lGeraGuia
						aDataGuia := DetDatas(Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),3,1)
						//Armazenamento dos dados para ser utilizado na Guia de Recolhimento
						aadd(aDadosSF1,{SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_TIPO,"1",SuperGetMV("MV_ESTADO"),SF1->F1_ESPECIE,.T.}) // Adicionei posiÁ„o 8 para trazer a especie na geraÁ„o da guia na entrada e a posiÁ„o 9 para confirmar operaÁ„o com AntecipaÁ„o
						nValFecp := MaFisRet(,"NF_VALFECP") + MaFisRet(,"NF_VFECPST")
						GravaTit(lDifTit,nValIcmCom,"ICMS","IC",cLcPadICMS,aDataGuia[1]/*Dt inic*/,aDataGuia[2]/*Dt Fim*/,DataValida(aDataGuia[2]+1,.T.) /*Dt Venc*/,1,lCompDifal,Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),0,nValIcmCom,"MATA103",lCtbOnLine,cNFiscal,@aGNRE,,,,,,.T./*lDifAlq*/,,,,0,aDadosSF1,,,,,,,,,,,,,,.T./*lDifal*/,,,,,,,,,,,)
					Endif
				Endif
								
				// Aproveitar o ponto de E    
				If  nSTTrans > 0 .And. nValIcmAnt == 0 .And. nValIcmCom == 0 .And. cPaisLoc=="BRA" .And. ( cFunName$"MATA103|MATA116" .Or. (IsBlind() .And. IsInCallStack("MATA103")) )
					lIcmsTit  := Iif(mv_par20==Nil,.F.,(mv_par20==1))
					lIcmsGuia := Iif(mv_par21==Nil,.F.,(mv_par21==1))
					lGeraGuia := .T.
					If lIcmsTit .Or. lIcmsGuia
				       If ExistBlock("MT103GUIA")
				          	lGeraGuia := ExecBlock("MT103GUIA",.F.,.F.,{"SF1","SA2",xFilial("SA2"),SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_ESPECIE})
  					   	Endif
  					   	If lGeraGuia
						  	aDataGuia := DetDatas(Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),3,1)
						  	//Armazenamento dos dados para ser utilizado na Guia de Recolhimento
						  	aadd(aDadosSF1,{SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_TIPO,"1", SuperGetMV("MV_ESTADO") })
				    	  	GravaTit(lIcmsTit,nSTTrans,"ICMS","IC",cLcPadICMS,aDataGuia[1]/*Dt inic*/,aDataGuia[2]/*Dt Fim*/,DataValida(aDataGuia[2]+1,.T.) /*Dt Venc*/,1,lIcmsGuia,Month(SF1->F1_DTDIGIT),Year(SF1->F1_DTDIGIT),0,nSTTrans,"MATA103",lCtbOnLine,cNFiscal,@aGNRE,,,,,,,,,,0,aDadosSF1)
				    	EndIf
					Endif
				Endif
			EndIf

			//-- 17/Mai/2019 [DLOGTMS02-6360 ] Se o mÛdulo for TMS, sÛ cria o NCC se encontrar tÌtulo na saÌda (no TMS, pode ainda n„o ter sido gerado SE1)
			//Gera titulo de NCC ao cliente
			If cTipo == "D" .And. MaFisRet(,"NF_BASEDUP") > 0 .And. (!lIntTMS .Or. !ExistFunc("TMSA500NCC") .Or. TMSA500NCC())
				//Considera a taxa informada para geracao da NCC
				If SuperGetMv( "MV_TXMOENC" ) == "2" .Or. lMoedTit
					nTaxaNCC := MaFisRet(,"NF_TXMOEDA")
				Else
					nTaxaNCC := 0
				EndIf

				Aadd(aRecNCC,ADupCred(xmoeda(MaFisRet(,"NF_BASEDUP"),1,nMoedaCor,NIL,NIL,NIL,nTaxaNCC),"001",nMoedaCor,MaFisRet(,"NF_NATUREZA"),nTaxaNCC,aColsSE2[1][2]))

				DbSelectArea("SE1")
				DbSetOrder(2)
				lQuery    := .T.
				aStruSE1  := SE1->(dbStruct())
				cAliasSE1 := "A103DEV"
				cQuery    := "SELECT SE1.E1_CLIENTE, SE1.E1_LOJA, SE1.E1_NUM, SE1.E1_SERIE, SE1.E1_TIPO, SE1.E1_SITUACA, SE1.E1_VLCRUZ, SE1.E1_VALOR, SE1.E1_NATUREZ, SE1.E1_VENCREA, SE1.E1_MOEDA, SE1.E1_FILIAL,SE1.R_E_C_N_O_ SE1RECNO "
				cQuery    += "  FROM "+RetSqlName("SE1")+" SE1 "
				cQuery    += " WHERE SE1.E1_FILIAL  = '"+xFilial("SE1")+"'"
				cQuery    += "   AND SE1.E1_CLIENTE = '"+SF1->F1_FORNECE+"'"
				cQuery    += "   AND SE1.E1_LOJA    = '"+SF1->F1_LOJA+"'"
				cQuery    += "   AND SE1.E1_SERIE   = '"+SD1->D1_SERIORI+"'"
				cQuery    += "   AND SE1.E1_NUM     = '"+SD1->D1_NFORI+"'"
				If lIntGC .And. lOrigem// MÛdulos de Concession·rias tambÈm considera Tipo de Titulo DP
					cQuery    += "   AND SE1.E1_TIPO    IN ('NF ','DP ') AND SE1.E1_PREFORI IN ('"+cPrefBAL+"','"+cPrefOFI+"')"
				Else
					cQuery    += "   AND SE1.E1_TIPO    = 'NF '"
				Endif
				cQuery    += "   AND SE1.D_E_L_E_T_ = ' ' "
				cQuery    += " ORDER BY "+SqlOrder(SE1->(IndexKey()))
				cQuery := ChangeQuery(cQuery)
				dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSE1,.T.,.T.)

				For nX := 1 To Len(aStruSE1)
					If aStruSE1[nX][2]<>"C"
						TcSetField(cAliasSE1,aStruSE1[nX][1],aStruSE1[nX][2],aStruSE1[nX][3],aStruSE1[nX][4])
					EndIf
				Next nX

				While !Eof() .And. xFilial("SE1") == (cAliasSE1)->E1_FILIAL .And.;
						SF1->F1_FORNECE  == (cAliasSE1)->E1_CLIENTE .And.;
						SF1->F1_LOJA     == (cAliasSE1)->E1_LOJA    .And.;
						SD1->D1_SERIORI  == (cAliasSE1)->E1_SERIE   .And.;
						SD1->D1_NFORI    == (cAliasSE1)->E1_NUM

					If lCompensa
						If iIf(lIntGC,(cAliasSE1)->E1_TIPO $ "NF |DP ",(cAliasSE1)->E1_TIPO == "NF ") .And. (cAliasSE1)->E1_SITUACA == "0"
							If !SuperGetMv("MV_CHECKNF",.F.,.F.)
								aadd(aRecSE1,If(lQuery,(cAliasSE1)->SE1RECNO,(cAliasSE1)->(RecNo())))
								If lMoedTit
									nTotalDev += (cAliasSE1)->E1_VLCRUZ
								Else
									nTotalDev += (cAliasSE1)->E1_VALOR
								EndIf
							Endif
						Endif
					Endif
					AtuSldNat((cAliasSE1)->E1_NATUREZ,(cAliasSE1)->E1_VENCREA,(cAliasSE1)->E1_MOEDA,"2","R",(cAliasSE1)->E1_VALOR,(cAliasSE1)->E1_VLCRUZ, "-",,cFunName,"SE1",If(lQuery,(cAliasSE1)->SE1RECNO,(cAliasSE1)->(RecNo())),Iif(INCLUI,3,4))
					DbSelectArea(cAliasSE1)
					dbSkip()
				EndDo

				If lCompensa .And. lMT103BXCR
					lRetMT103BXCR := ExecBlock("MT103BXCR",.F.,.F.,{nTotalDev,aRecSe1,aRecNcc})
					If ValType(lRetMT103BXCR) <> "L"
						lRetMT103BXCR := .F. 
					EndIf

					lCompensa := lRetMT103BXCR 
				Endif

				//Estorna os valores da Comissao
				If ( SuperGetMV("MV_TPCOMIS",.F.,"O")=="O" )
					If lCompensa
						Fa440CalcE("MATA100",,,"-")
					Else
						Fa440CalcE("MATA100")
					Endif
				EndIf

				If lCompensa
					If nTotalDev > 0
						If lCtbOnLine
							//Guarda cFileCtb e nHandle da MATA103
							cMTFileCtb 	:= GetHFile()
							nMTHandle 	:= GetHProva()

							Pergunte("FIN330",.F.)
							//Compensacao automatica do titulo, respeitando parametro MV_CHECKNF
							MaIntBxCR(3,aRecSe1,,aRecNcc,,{lCtbOnLine,.F.,.F.,.F.,.F.,.T.},,,,,,,,,,, MV_PAR08 == 1 )
							Pergunte("MTA103",.F.)

							//Restaura cFileCtb e nHandle da MATA103 para apresentar tela de contabilizaÁ„o on-line na chamada da cA100Incl.
							PutHFile(cMTFileCtb,nMTHandle)
						Else
							Pergunte("FIN330",.F.)
							//Compensacao automatica do titulo, respeitando parametro MV_CHECKNF
							MaIntBxCR(3,aRecSe1,,aRecNcc,,{lCtbOnLine,.F.,.F.,.F.,.F.,.T.},,,,,,,,,,, MV_PAR08 == 1 )
							Pergunte("MTA103",.F.)
						EndIf
					EndIf
				Endif

				If lQuery
					DbSelectArea(cAliasSE1)
					dbCloseArea()
					DbSelectArea("SE1")
				EndIf
			EndIf

			If cFormul == "S" .And. cTipoNf == "2"
				While ( __lSX8 )
					ConfirmSX8()
				EndDo
			EndIf

			If lMvNfeDvg .And. lSC1DtFi .And. lSC1HrFi 
				If SF1->F1_TIPO == "N" .And. lSCxPCxNF
					cUpDate := " UPDATE "+RetSqlName("SC1")
					cUpDate += " SET C1_XDTFIM = '"+Dtos(dDataBase)+"',C1_XHRFIM = '"+SubStr(Time(),1,5)+"' "
					cUpDate += " WHERE R_E_C_N_O_ IN(SELECT SC1.R_E_C_N_O_ REGSC1 FROM "
					cUpDate += RetSqlName("SD1")+" SD1 "
					cUpDate += " LEFT OUTER JOIN "
					cUpDate += RetSqlName("SC7")+" SC7 ON "
					cUpDate += " 	C7_FILIAL = '"+xFilial("SC7")+"' "
					cUpDate += " 	AND C7_NUM = D1_PEDIDO "
					cUpDate += " 	AND C7_ITEM = D1_ITEMPC "
					cUpDate += " 	AND SC7.D_E_L_E_T_ = ' ' "
					cUpDate += " LEFT OUTER JOIN "
					cUpDate += RetSqlName("SC1")+" SC1 ON "
					cUpDate += " 	C1_FILIAL = '"+xFilial("SC1")+"' "
					cUpDate += " 	AND C1_NUM = C7_NUMSC "
					cUpDate += " 	AND C1_ITEM = C7_ITEMSC "
					cUpDate += " 	AND SC1.D_E_L_E_T_ = ' ' "
					cUpDate += " WHERE D1_FILIAL = '"+xFilial("SD1")+"' "
					cUpDate += " AND D1_DOC = '"+SF1->F1_DOC+"' "
					cUpDate += " AND D1_SERIE = '"+SF1->F1_SERIE+"' "
					cUpDate += " AND D1_FORNECE = '"+SF1->F1_FORNECE+"' "
					cUpDate += " AND D1_LOJA = '"+SF1->F1_LOJA+"' "
					cUpDate += " AND SD1.D_E_L_E_T_ = ' ') "					
					TCSQLExec(cUpDate)
				EndIf
				
				//FSW - 05/05/2011 - Rotina implementa a inclusao e alteracao das Divergencias
				IF  (Inclui .or. Altera)
					IF Type("_aDivPNF") <> "U" .and. Len( _aDivPNF ) > 0
							CA040MAN(@_aDivPNF)
					EndIf
				Endif
			EndIf
			
			//Verificacao da Lista de Presentes - Vendas CRM
			If lUsaLstPre .And. cTipo == "D"
				If !M103LstPre()
					//DisarmTransaction()
				EndIf
			EndIf
			//Pontos de Entrada apÛs gravacao do SF1
			If (ExistTemplate("SF1100I"))
				ExecTemplate("SF1100I",.f.,.f.)
			EndIf
			If (ExistBlock("SF1100I"))
				ExecBlock("SF1100I",.f.,.f.)
			EndIf
			//Grava Pedido de Venda qdo solicitado pelo campo D1_GERAPV
			a103GrvPV(1,aPedPV)
			
			//Grava o arquivo de Livros  (SF3)
			MaFisAtuSF3(1,"E",0,"SF1",,,,,cCodRSef)
			
			//Metricas - Documento de entrada que geraram imposto
			If !Empty(SF3->F3_ALIQICM) .And. !Empty(SF3->F3_VALICM)
				nQtdImp++
				ComMtQtd("-inc",l103Auto,l103Class,cTipo,nQtdImp,cFunImp)
				nQtdImp := 0
			EndIf

			If nRecSf1 == 0
				nRecSF1	:= SF1->(RecNo())
			EndIf

			//-- Executa integraÁ„o do Datasul se MV_TMSERP == 1
			If cTMSERP == "1"
				TMSAE76()
			Endif

			//Contabilizacao do documento de entrada
			If lCtbOnLine
				If lVer660 .And. !(cTipo $"DB")
					DbSelectArea("SF1")
					MsGoto(nRecSF1)
					nTotalLcto	+= DetProva(nHdlPrv,"660","MATA103",cLote)
				EndIf
				If lVer642 .And. cTipo $"DB"
					DbSelectArea("SF1")
					MsGoto(nRecSF1)
					nTotalLcto	+= DetProva(nHdlPrv,"642","MATA103",cLote)
				EndIf
				If lVer950 .And. !Empty(SD1->D1_TEC)
					nTotalLcto +=DetProva(nHdlPrv,"950","MATA103",cLote)
				Endif
			EndIf
			
			//Grava os lancamentos nas contas orcamentarias SIGAPCO
			Do Case
				Case SF1->F1_TIPO == "B"
					PcoDetLan("000054","20","MATA103")
				Case cTipo == "D"
					PcoDetLan("000054","19","MATA103")
				OtherWise
					PcoDetLan("000054","03","MATA103")
			EndCase

			If lUsaGCT
				//Grava as multas no historico do contrato
				A103HistMul( 1, aMultas, cNFiscal, cSerie, cA100For, cLoja )
				
				//Atualiza os movimentos de caucao do contratos - SIGAGCT
				A103AtuCauc( 1, aContratos, aRecGerSE2, cA100For, cLoja, cNFiscal, cSerie, dDEmissao, SF1->F1_VALBRUT, SF1->F1_SERIE )
			EndIf

		ElseIf SF1->F1_STATUS == "C" //Nota com Bloqueio de Movimentaıutilizo esta funÁ„o para gravaÁ„o do CD2.
			//Pontos de Entrada apÛs gravacao do SF1
			If (ExistTemplate("SF1100I"))
				ExecTemplate("SF1100I",.f.,.f.)
			EndIf
			If (ExistBlock("SF1100I"))
				ExecBlock("SF1100I",.f.,.f.)
			EndIf
			If cFormul == "S" .And. cTipoNf == "2"
				While ( __lSX8 )
					ConfirmSX8()
				EndDo
			EndIf
			MaFisAtuSF3(1,"E",0,"SF1","","","",1,cCodRSef)
		
		Else
			//Pontos de Entrada apÛs gravacao do SF1
			If (ExistTemplate("SF1100I"))
				ExecTemplate("SF1100I",.f.,.f.)
			EndIf
			If (ExistBlock("SF1100I"))
				ExecBlock("SF1100I",.f.,.f.)
			EndIf
		EndIf

		If lIntGC // Modulos do DMS 
			If FindFunction("OA2900045_a103Grava_AposGravacao")
				OA2900045_a103Grava_AposGravacao( { SF1->F1_DOC, SF1->F1_SERIE, SF1->F1_FORNECE, SF1->F1_LOJA } )
			EndIf
		EndIf

		//Chamada dos execblocks no termino do documento de entrada
		If (ExistTemplate("GQREENTR"))
			ExecTemplate("GQREENTR",.F.,.F.)
		EndIf

		If (ExistBlock("GQREENTR"))
			ExecBlock("GQREENTR",.F.,.F.)
		EndIf

		//faz a chamada da funcao abaixo para gravar os apontamentos da OP
		If !lBloqueio .And. Type("aOPBenef") == "A" .And. !Empty(aOPBenef)
			lContinua := MTIncluiPR(aOPBenef)
		EndIf
		
		//Depois da gravaÁ„o da NF
		If SuperGetMV('MV_AGRUBS',.F.,.F.) .And. FindFunction("AGRA840NFE")
			AGRA840NFE()
		EndIf
	Else
		//Se for processo de adiantamento e o titulo estiver baixado exclui a compensacao
		If cPaisLoc $ "BRA|MEX"
			If Len(aRecSE2) > 0
				If A120UsaAdi(SF1->F1_COND)
					SE2->(MsGoto(aRecSE2[1]))
					If SE2->(Recno()) = aRecSE2[1]
						If !Empty(SE2->E2_BAIXA) .and. SE2->E2_VALOR != SE2->E2_SALDO
							If !A103CCompAd(aRecSE2)
								lExcCmpAdt := .F.
								Aviso(STR0119,STR0338 + CRLF + STR0339,{STR0461}) //"AtenÁ„o"#"N„o foi possÌvel excluir a compensaÁ„o associada ao tÌtulo deste Documento de Entrada."#"N„o ser· possÌvel excluir o Documento de Entrada."
								DisarmTransaction()
								Return()
							Endif
						Endif
					Endif
				Endif
			Endif
		Endif
		If lConfACD .And. cPaisLoc == "BRA"
			If (lIntACD .And. lEstNfClass .And. cMVCONFFIS == "S") .And. SA2->A2_CONFFIS <> "3" .And.;
				((SA2->A2_CONFFIS == "0" .And. cMVTPCONFF == "2") .Or. SA2->A2_CONFFIS == "2")
				If SF1->F1_STATCON == "0"
					SF1->F1_STATCON := " "
				EndIf
			EndIf
		EndIf
		If lUsaGCT
			//Obtem os contratos desta NF - SIGAGCT
			A103GetContr( aRecSD1, @aContratos )

			//Atualiza os movimentos de caucao do contratos - SIGAGCT
			A103AtuCauc( 2, aContratos, aRecSE2, cA100For, cLoja, cNFiscal, cSerie,,,SF1->F1_SERIE )

			//Apaga as multas do historico do contrato
			A103HistMul( 2, NIL, cNFiscal, cSerie, cA100For, cLoja )
		EndIf

		A103DelSF8(cNFiscal,cSerie,cA100For,cLoja)
		A103DelCD5(cNFiscal,cSerie,cA100For,cLoja)

		//Grava os lancamentos nas contas orcamentarias SIGAPCO
		Do Case
			Case SF1->F1_TIPO == "B"
				PcoDetLan("000054","20","MATA103",.T.)
			Case cTipo == "D"
				PcoDetLan("000054","19","MATA103",.T.)
			OtherWise
				PcoDetLan("000054","03","MATA103",.T.)
		EndCase
			
		//Ponto de Entrada M103L665
		If (ExistBlock("M103L665"))   
			ExecBlock("M103L665",.F.,.F.,{cLote,nHdlPrv,cArquivo,lDigita,lAglutina})  
			aCtbInf	:= {}   // Zera o Array para que n„o ocorra duplicaÁ„o apÛs retornar do PE
		Else
			//Gera Lancamento contabil 665- Exclusao - Total
			If lVer665.And.!Empty(SF1->F1_DTLANC)
				nTotalLcto	+= DetProva(nHdlPrv,"665","MATA103",cLote)
			EndIf
		EndIf
		
		//Exclui o Titulo a Pager de ICMS Antecipado SE2 se Houver e a Guia de Recolhimento ICMS SF6
    	If cPaisLoc=="BRA"
			If Empty(SF1->F1_NUMTRIB)
				cNumero := SF1->F1_DOC
			Else
				cNumero := SF1->F1_NUMTRIB
			EndIf
			SE2->(DbsetOrder(1))
			If SE2->(dbSeek(xFilial("SE2") + "ICM" + SF1->F1_NUMTRIB))
				// Verifica se existe mais de uma nota com o mesmo numero. Se existir mantem SE2 para nao excluir o registro errado pois nao e possivel posicionar no titulo ICM por fornecedor, sendo necessario excluir manualmente.
				cAliasAnt := Alias()
				aAreaSF1 := SF1->(GetArea())
				SF1->(dbSetOrder(1))
				SF1->(dbSeek(xFilial("SF1")+cNFiscal+ SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie) ))
				While !SF1->(Eof()) .And. SF1->F1_DOC == cNFiscal .And. SF1->F1_SERIE == SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)
					nF1docs++
					SF1->(dbSkip())
				End
				RestArea(aAreaSF1)
				DbSelectArea(cAliasAnt)
				If !(nF1docs > 1) .Or. SE2->E2_NUM = SF1->F1_NUMTRIB
					Do While SE2->(!Eof()).And. SE2->E2_PREFIXO+SE2->E2_NUM == "ICM" + SF1->F1_NUMTRIB
						If ALLTRIM(SE2->E2_TIPO)== Alltrim(MVTAXA) .And. ALLTRIM(SE2->E2_ORIGEM) == "MATA103"
							RecLock("SE2")
							SE2->(dbDelete())
							SE2->(MsUnLock())
						Endif
						SE2->(DbSkip())
					EndDo
				EndIf
			Endif

			If SE2->( DbSeek( xFilial( "SE2" ) + "ICM" + SF1->F1_DOC ) )
				Do While SE2->( !Eof() ) .And. SE2->E2_PREFIXO + SE2->E2_NUM == "ICM" + SF1->F1_DOC
					If ALLTRIM( SE2->E2_TIPO ) == Alltrim( MVTAXA ) .And. ALLTRIM( SE2->E2_ORIGEM ) == "MATA103" .And. SE2->E2_FILORIG == cFilAnt
						RecLock( "SE2" )
							SE2->( dbDelete() )
						SE2->( MsUnLock() )
					Endif
					SE2->( DbSkip() )
				EndDo
			Endif

			//Verifica se a NFE gerou Guia ICMS Antecipado e Exclui o SF6
			SF6->(DbsetOrder(3))
			If SF6->(dbSeek(xFilial("SF6")+"1"+Padr(SF1->F1_TIPO,nTamSF6)+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA))
				While SF6->( !EOF() ) .AND. xFilial( "SF6" ) == SF6->F6_FILIAL .AND. "1" == SF6->F6_OPERNF .AND.;
					Padr(SF1->F1_TIPO,nTamSF6) == SF6->F6_TIPODOC .AND. SF1->F1_DOC == SF6->F6_DOC .AND.;
					SF1->F1_SERIE == SF6->F6_SERIE .AND. SF1->F1_FORNECE == SF6->F6_CLIFOR .AND. SF1->F1_LOJA == SF6->F6_LOJA

					//Verifica se a NFE gerou Complemento da Guia
					If ChkFile("CDC")
						DbSelectArea("CDC")
						CDC->(dbSetOrder(1))
						If CDC->(dbSeek(xFilial("CDC")+"S"+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA+SF6->F6_NUMERO+SF6->F6_EST))
							RecLock("CDC")
								CDC->(dbDelete())
							CDC->(MsUnLock())
						Endif
					Endif

					RecLock("SF6")
						SF6->(dbDelete())
					SF6->(MsUnLock())

					SF6->( DbSkip() )
				EndDo
			Endif
		Endif

		//Apaga o pedido de vendas quando gerado pelo D1_GERAPV
		a103GrvPV(2,,aRecSC5)
		
		//Apaga o arquivo de Livros Fiscais (SF3)
		MaFisAtuSF3(2,"E",SF1->(RecNo()))

		// Exclusao dos titulos de recolhimento gerados pelo motor de tributos
		If cPaisLoc == "BRA" .And. AliasInDic("F2F") .And. AliasInDic("FK7") .And. FindFunction("xFisDelTit") .And. ;
		   FindFunction("xFisF2F") .And. SF1->(FieldPos("F1_IDNF")) > 0
		
			xFisDelTit(SF1->F1_IDNF, "SF1", "MATA100", 2)
			// Exclusao da tabela de amarracao NF x Titulo
			xFisF2F("E", SF1->F1_IDNF, "SF1")
		EndIf

		//Apaga o Flag DevoluÁ„o quando possuir Nota SaÌda relacionada
		DbSelectArea("SD1")
		DbSetOrder(1)
		DbClearFilter()
		MsSeek(cFilSD1+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
		While !Eof() .And. D1_FILIAL  == cFilSD1;
			.And. D1_DOC     == SF1->F1_DOC;
			.And. D1_SERIE   == SF1->F1_SERIE;
			.And. D1_FORNECE == SF1->F1_FORNECE;
			.And. D1_LOJA    == SF1->F1_LOJA

			DbSelectArea("SF2")
			DbSetOrder(2)
			DbClearFilter()
			MsSeek(xFilial("SF2")+SF1->F1_FORNECE+SF1->F1_LOJA+SD1->D1_NFORI+SD1->D1_SERIORI)
			If !EOF() .And. cPaisLoc == "BRA"
				RecLock("SF2",.F.)
				SF2->F2_FLAGDEV := ""
				MsUnLock()
			EndIf
			DbSelectArea("SD1")
			DbSkip()
		EndDo

		//ContabilizaÁ„o da LP 65D - Cancelamento de rateio de multipla natureza.
		If lVer65D .And. !Empty(SF1->F1_DTLANC)

			DbSelectArea("SE2")
			SE2->(DbSetOrder(6))//E2_FILIAL+E2_FORNECE+E2_LOJA+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO
			If SE2->(DbSeek(fwxFilial("SE2") + SF1->F1_FORNECE + SF1->F1_LOJA + SF1->F1_SERIE + SF1->F1_DOC)) 

				cSevTemp := GetNextAlias()	
				
				BeginSql Alias cSevTemp
				SELECT SEV.R_E_C_N_O_ AS RECNOSEV
				FROM	%Table:SEV% SEV
				WHERE SEV.EV_FILIAL = %xFilial:SEV%
					AND SEV.EV_NUM = %Exp:SF1->F1_DOC%
					AND SEV.EV_CLIFOR = %Exp:SF1->F1_FORNECE%'
					AND SEV.EV_LOJA = %Exp:SF1->F1_LOJA%
					AND SEV.EV_LA = "S"
					AND SEV.%NotDel%
				EndSql

				If (cSevTemp)->(!Eof())
					DbSelectArea("SEV")
					While ( (cSevTemp)->(!Eof()) )		
						SEV->(MsGoto((cSevTemp)->RECNOSEV))
						nTotalLcto	+= DetProva(nHdlPrv,"65D","MATA103",cLote)
						(cSevTemp)->(dbSkip())
					Enddo
				Endif

				(cSevTemp)->(DbCloseArea())
			Endif

		EndIf				
		
		//Gera os titulos no Contas a Pagar SE2
		If !(SF1->F1_TIPO$"DB")
			//Ponto de Entrada para definir se ir· gerar lanÁamento futuro(SRK) ou tÌtulo no financeiro (SE2)
			If (ExistBlock("M103GERT"))
				ExecBlock("M103GERT",.F.,.F.,{2,aRecSE2})
			Else
				If Empty(SF1->F1_NUMRA)
					A103AtuSE2(2,aRecSE2)
					A103AtuSE2(2,aRecSE2)
				Else
					aRet := A103AtuSRK(2)
					If !aRet[1]
						Help( ,,"ATUSRK",,aRet[2], 1, 0 )
						DisarmTransaction()
						Return .F.
					Endif
				EndIf
			EndIf
		EndIf
		
		//Atualiza os acumulados do Cabecalho do documento
		MaAvalSF1(5)
		
		//Estorna os titulos de NCC ao cliente
		If SF1->F1_TIPO == "D"
			A103EstNCC()
		Endif

		//Exclusao do rateio dos itens do documento de entrada
		For nX := 1 To Len(aRecSDE)
			//Posiciona registro na tabela SDE
			DbSelectArea("SDE")
			SDE->(MsGoto(aRecSDE[nX]))
			//Posiciona registro na tabela SD1
			nRecSD1SDE := ASCAN(aRecSD1,{|x| x[2] == SDE->DE_ITEMNF})
			If nRecSD1SDE > 0
				SD1->(MsGoto(aRecSD1[nRecSD1SDE,1]))
			EndIf
			//Exclui campos Memos Virtuais da tabela SYP vinculado aos memos SDE
			If laMemoSDE
				If Len(aMemoSDE) > 0
					MSMM(&(aMemoSDE[1][1]),,,,2)
				EndIf
			EndIf
			DbSelectArea("SF4")
			DbSetOrder(1)
			MsSeek(xFilial("SF4")+SD1->D1_TES)

			DbSelectArea("SB1")
			DbSetOrder(1)
			MsSeek(xFilial("SB1")+SD1->D1_COD)
			//Grava os lancamentos nas contas orcamentarias SIGAPCO
			Do Case
				Case cTipo == "B"
					PcoDetLan("000054","11","MATA103",.T.)
				Case cTipo == "D"
					PcoDetLan("000054","10","MATA103",.T.)
				OtherWise
					PcoDetLan("000054","09","MATA103",.T.)
			EndCase
			//Gera Lancamento contabil 656- Exclusao - Itens de Rateio
			If lVer656.And.!Empty(SF1->F1_DTLANC)
				nTotalLcto	+= DetProva(nHdlPrv,"656","MATA103",cLote)
			EndIf
			If !lEstNfClass	.Or. (lEstNfClass .And. cDelSDE == "1")
				RecLock("SDE")
				dbDelete()
				MsUnLock()
			EndIf
		Next nX

		//Exclusao da rotina para tratar a eliminacao do rateio por item na tabela de rateio
		nSpace		:= TamSx3("CH_PEDIDO")[1]
		cPedido		:= SC7->C7_NUM+Space(nSpace-Len(SC7->C7_NUM))
		dbSelectArea("SDE")
		dbSetOrder(1) // DE_FILIAL+DE_DOC+DE_SERIE+DE_FORNECE+DE_LOJA+DE_ITEMNF+DE_ITEM
		If dbSeek(cFilSDE+cPedido+SF1->F1_SERIE+SC7->C7_FORNECE+SC7->C7_LOJA)
			While !Eof() .And. SDE->DE_FILIAL+SDE->DE_DOC+SDE->DE_SERIE +SDE->DE_FORNECE+SDE->DE_LOJA ==;
								cFilSDE+cPedido   +SF1->F1_SERIE +SC7->C7_FORNECE+SC7->C7_LOJA
				RecLock("SDE",.F.)
				dbDelete()
				MsUnlock()
				dbSelectArea("SDE")
				dbSkip()
			EndDo
		EndIf
		//Tratamento da gravacao do SDE na Integridade Referencial
		SDE->(FkCommit())

		// Exclusao aposentadoria especial
		If lChkDHP
			dbSelectArea("DHP")
			dbSetOrder(1)
			If MsSeek(xFilial("DHP")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
				While DHP->(!Eof()) .And. xFilial("DHP") == DHP->DHP_FILIAL .And. ;
						DHP->DHP_DOC == SF1->F1_DOC .And. ;
						DHP->DHP_SERIE == SF1->F1_SERIE .And. ;
						DHP->DHP_FORNEC == SF1->F1_FORNECE .And. ;
						DHP->DHP_LOJA == SF1->F1_LOJA

					RecLock("DHP",.F.)
					dbDelete()
					MsUnlock()
					dbSelectArea("DHP")

					DHP->(DbSkip())
				End
				// Tratamento da gravacao do SDE na Integridade Referencial
				DHP->(FkCommit())
			EndIf
		EndIf
		
		// Exclusao natureza de rendimento
		If lChkDHR
			A103EXCDHR()
		EndIf

		For nX := 1 to Len(aRecSD1)
			DbSelectArea("SD1")
			MsGoto(aRecSD1[nx,1])
			//Gera Lancamento contabil 955- Exclusao - Total EIC
			If nX == 1 .And. lVer955 .And.!Empty(SD1->D1_TEC) .And. !Empty(SF1->F1_DTLANC)
				nTotalLcto +=DetProva(nHdlPrv,"955","MATA103",cLote)
			Endif
			DbSelectArea("SF4")
			DbSetOrder(1)
			MsSeek(xFilial("SF4")+SD1->D1_TES)

			DbSelectArea("SB1")
			DbSetOrder(1)
			MsSeek(xFilial("SB1")+SD1->D1_COD)

			//Efetua o Estorno do Ativo Imobilizado
			cAux := Replicate("0", TAMSX3("N1_ITEM")[1])
			
			If ( SF4->F4_BENSATF == "1" ) .And. SD1->D1_QUANT >= 1 .And. !(SF1->F1_TIPO $ "I|P")
				If !lATFDCBA .And. SF4->F4_BENSATF <> '1'
					For nV := 1 TO Int(SD1->D1_QUANT)
						cAux		:= Soma1( cAux,,, .F. )
						cItemAtf	:= PadL( cAux, Len( SN1->N1_ITEM ), "0" )
						cCodATVF := SubsTR(Trim(SD1->D1_CBASEAF),1,Len(Trim(SD1->D1_CBASEAF))-Len(cItemAtf))
						cCodATVF := cCodATVF+Space(nTamN1CBas-Len(cCodATVF))
						a103GrvAtf(2,cCodATVF+cItemAtf,,,,@aCIAP)
					Next nV
				Else
					// Localiza o ativo gerado atraves do documento de entrada
					SN1->(dbSetOrder(8))	//N1_FILIAL+N1_FORNEC+N1_LOJA+N1_NFESPEC+N1_NFISCAL+N1_NSERIE+N1_NFITEM
					If SN1->(MsSeek(xFilial("SN1") + SD1->D1_FORNECE + SD1->D1_LOJA + SF1->F1_ESPECIE + SD1->D1_DOC + SD1->D1_SERIE + SD1->D1_ITEM))
						While	SN1->(!Eof()) .And.;
								SN1->N1_FORNEC  == SD1->D1_FORNECE .And.;
								SN1->N1_LOJA    == SD1->D1_LOJA    .And.;
								SN1->N1_NFESPEC == SF1->F1_ESPECIE .And.;
								SN1->N1_NFISCAL == SD1->D1_DOC     .And.;
								SN1->N1_NSERIE  == SD1->D1_SERIE   .And.;
								SN1->N1_NFITEM  == SD1->D1_ITEM

							cCodATVF := SN1->N1_CBASE+SN1->N1_ITEM
							a103GrvAtf(2,cCodATVF,,,,@aCIAP)

							If lEstNfClass .And. AllTrim(SD1->D1_CBASEAF) == AllTrim(cCodATVF)
								aD1Area := SD1->(GetArea())
								If RecLock("SD1",.F.,.T.)
									SD1->D1_CBASEAF := ""
									SD1->(MsUnlock())
								Endif
								RestArea(aD1Area)
							Endif

							SN1->(dbSkip())
						EndDo
					elseif !empty(SD1->D1_CBASEAF) .and. cTipo == "N" .and. isNfGatEst(SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA)
						cChaveSD1 := if(Alltrim(cEspecie) == "CTE",SD1->(D1_FILIAL+D1_NFORI+D1_SERIORI+D1_FORNECE+D1_LOJA),SD1->(D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA))
						a103GrvAtf(104,,,,,,,,,,aRecSF1Ori,cChaveSD1,SD1->D1_CBASEAF)//estorna atualizaÁ„o de valor dos bens.
					EndIf
				EndIf
			ElseIf !(SF1->F1_TIPO $ "I|P")
				if ( ( ( Alltrim(cEspecie) == "CTE" .and. lAgVlrATF ) .OR. ( !empty(SD1->D1_CBASEAF) .and. cTipo == "N" .and. isNfGatEst(SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA)) ) ) .and. ( FwIsInCallStack("MATA103") .OR. FwIsInCallStack("MATA116") )
					if empty(aRecSF1Ori) .and. FwIsInCallStack("MATA116")
						//Resgato o recno da NF de origem para achar o ativo a ser estornado os valores.
						nRegSF1 := getNfOri(SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA)
						if nRegSF1 > 0
							aAdd(aRecSF1Ori, nRegSF1)
						endif
					endif
					cChaveSD1 := if(Alltrim(cEspecie) == "CTE",SD1->(D1_FILIAL+D1_NFORI+D1_SERIORI+D1_FORNECE+D1_LOJA),SD1->(D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA))
					a103GrvAtf(104,,,,,,,,,,aRecSF1Ori,cChaveSD1,SD1->D1_CBASEAF)//estorna atualizaÁ„o de valor dos bens.
				else
					a103GrvAtf(2,Trim(SD1->D1_CBASEAF),,,,@aCIAP)

					If lEstNfClass
						aD1Area := SD1->(GetArea())
						If RecLock("SD1",.F.,.T.)
							SD1->D1_CBASEAF := ""
							SD1->(MsUnlock())
						Endif
						RestArea(aD1Area)
					Endif
				endif
			EndIf
			//Grava os lancamentos nas contas orcamentarias SIGAPCO
			Do Case
				Case SD1->D1_TIPO == "B"
					PcoDetLan("000054","07","MATA103",.T.)
				Case SD1->D1_TIPO == "D"
					PcoDetLan("000054","05","MATA103",.T.)
				OtherWise
					PcoDetLan("000054","01","MATA103",.T.)
			EndCase

			//Gera Lancamento contabil 655- Exclusao - Itens
			If lVer655.And.!Empty(SF1->F1_DTLANC)
				nTotalLcto	+= DetProva(nHdlPrv,"655","MATA103",cLote)
			EndIf

			//Estorna o Servico do WMS (DCF)
			If lIntWMS .And. cTipo $ "N|D|B"
				WmsAvalSD1("4","SD1")
			EndIf

			//Estorna o Movimento de Custo de Transporte - Integracao TMS
			If lIntTMS  .And. (Len(aRatVei)>0 .Or. Len(aRatFro)>0)
				EstornaSDG("SD1",SD1->D1_NUMSEQ,lCtbOnLine,nHdlPrv,@nTotalLcto,cLote,"MATA103")
			EndIf

			//Atualiza Consumo Medio SB3 somente para os casos abaixo:
			//- TES que atualiza estoque
			//- Devolucao de Vendas
			//- Devolucao de produtos em Poder de Terceiros
			If (SD1->D1_TIPO == "D" .Or. SF4->F4_PODER3 == "D") .And. SF4->F4_ESTOQUE == "S"
				aAreaAnt := GetArea()
				cMes := "B3_Q"+StrZero(Month(SD1->D1_DTDIGIT),2)
				SB3->(dbSeek(xFilial("SB3")+SD1->D1_COD))
				If SB3->(Eof())
					RecLock("SB3",.T.)
					Replace B3_FILIAL With xFilial("SB3"), B3_COD With SD1->D1_COD
				Else
					RecLock("SB3",.F.)
				EndIf
				Replace &(cMes) With &(cMes) + SD1->D1_QUANT
				MsUnlock()
				RestArea(aAreaAnt)
			EndIf

			//Estorna o Saldo do Armazem de Transito - MV_LOCTRAN
			A103TrfSld(lDeleta,1)

			//Atualizacao dos acumulados do SD1
			MaAvalSD1(If(SF1->F1_STATUS=="A",5,2),"SD1",lAmarra,lDataUcom,lPrecoDes, NIL, NIL, @aContratos,MV_PAR15==2,@aCIAP,lEstNfClass)
			MaAvalSD1(If(SF1->F1_STATUS=="A",6,3),"SD1",lAmarra,lDataUcom,lPrecoDes, , ,,MV_PAR15==2)

			//Exclui o item da CBE quando utilizado ACD
			If lIntACD .And. lDeleta	.And. !lEstNfClass
				EstCBED1(SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD)
			EndIf

			//Exclui o item da NF SD1
			If lIntMnt
				If FindFunction("NGSD1STL")
					NGSD1STL(cAliasTPZ, SD1->D1_FILIAL, SD1->D1_DOC, SD1->D1_SERIE, SD1->D1_FORNECE, SD1->D1_LOJA, SD1->D1_COD, SD1->D1_ITEM, .F.)
				Else
					NGSD1100E()
				EndIf
			EndIf

			//Depois da gravaÁ„o da exclus„o da NFE
			If SuperGetMV('MV_AGRUBS',.F.,.F.) .And. FindFunction("AGRADELENP9")
				AGRADELENP9()
			EndIf

			//Atualiza saldo no armazem de poder de terceiros
			TrfSldPoder3(SD1->D1_TES,"SD1",SD1->D1_COD,.T.)

			//Executa a Baixa da NFE X Tabela de Quantidade Prevista
			A103AtuPrev(lDeleta) 

			//Exclus„o DKD 
			If !lEstNfClass .And. (type("lDKD") == "L" .and. lDKD) .And. (type("lTabAuxD1") == "L" .and. lTabAuxD1) .And. Type("aColsDKD") == "A" .And. Len(aColsDKD) > 0 .And. (nJ	:= aScan(aColsDKD,{|x| x[1] == SD1->D1_ITEM})) > 0
				A103DKDGRV(aHeadDKD,aColsDKD,nJ,"D") 
			Endif 

			//Pontos de Entrada
			If lDclNew 
				DCLSD1100E()
			ElseIf lTSD1100E
				ExecTemplate("SD1100E",.F.,.F.,{lConFrete,lConImp})
			Endif
			If lSD1100E
				ExecBlock("SD1100E",.F.,.F.,{lConFrete,lConImp})
			Endif

			//Dados para envio de email do messenger
			AADD(aDetalheMail,{SD1->D1_ITEM,SD1->D1_COD,SD1->D1_QUANT,SD1->D1_TOTAL})

			If !lEstNfClass //-- Se nao for estorno de Nota Fiscal Classificada (MATA140)
				//Volta o Status da NFe.
				SDS->(DbSetOrder(1))
				If SDS->(MsSeek(xFilial("SDS")+cNFiscal+SD1->D1_SERIE+cA100For+cLoja))
					SDS->(RecLock("SDS",.F.))
					Replace SDS->DS_STATUS 	With If(SDS->DS_TIPO == "N"," ",SDS->DS_TIPO)
					Replace SDS->DS_USERPRE With CriaVar("DS_USERPRE")
					Replace SDS->DS_DATAPRE With CriaVar("DS_DATAPRE")
					Replace SDS->DS_HORAPRE With CriaVar("DS_HORAPRE")
					SDS->(MsUnlock())
				EndIf

				// Faz chamada para exclusao dos tributos genericos
				If lTrbGen .And. !Empty(SD1->D1_IDTRIB)
					MaFisTG(2,,,SD1->D1_IDTRIB)
				EndIf

				RecLock("SD1",.F.,.T.)

				//Grava CAT83
				If lCAT83
					GravaCAT83("SD1",{SD1->D1_FILIAL,SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD,SD1->D1_ITEM},"E",1,SD1->D1_CODLAN)
				EndIf
				dbDelete()
				MsUnlock()
				//Caio.Santos - 11/01/13 - Req.72
				If lLog
					RSTSCLOG("CLS",2,/*cUser*/)
				EndIf
			Else
				RecLock("SD1",.F.,.T.)
				SD1->D1_TES     := CriaVar('D1_TES',.F.)
				SD1->D1_CODCIAP := CriaVar('D1_CODCIAP',.F.)
				If cDelSDE <> "2"
					SD1->D1_RATEIO := "2"		// volta para "Nao (2) para permitir a reclassificacao
				EndIf
				//Grava CAT83
				If lCAT83
					GravaCAT83("SD1",{SD1->D1_FILIAL,SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD,SD1->D1_ITEM},"E",1,SD1->D1_CODLAN)
				EndIf
				MsUnLock()
				//Caio.Santos - 11/01/13 - Req.72
				If lLog
					RSTSCLOG("CLS",3,/*cUser*/)
				EndIf
				If cPaisLoc=="BRA"
					MaAvalSD1(1,"SD1")
				ElseIf cPaisLoc == "ARG"
					If SD1->D1_TIPO_NF == "5"	//Factura Fob
						MaAvalSD1(1,"SD1")
					EndIf
				ElseIf cPaisLoc == "CHI"
					If SD1->D1_TIPO_NF == "9"	//Factura Aduana
						MaAvalSD1(1,"SD1")
					EndIf
				Endif
			EndIf

			If l103ATURM
				A103ATURM("-","RET",SD1->D1_RETENCA,SD1->D1_PEDIDO,SD1->D1_ITEMPC)
				A103ATURM("-","DED",SD1->D1_DEDUCAO,SD1->D1_PEDIDO,SD1->D1_ITEMPC)
				A103ATURM("-","FAT",SD1->D1_FATDIRE,SD1->D1_PEDIDO,SD1->D1_ITEMPC)
			Endif
		Next nX

		//Tratamento da gravacao do SD1 na Integridade Referencial
		SD1->(FkCommit())

		DbSelectArea("SF1")
		MsGoto(nRecSF1)
		RecLock("SF1",.F.,.T.)
		nOper := 3
		
		If !Empty(SF1->F1_APROV)
			MaAlcDoc({SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,"NF",SF1->F1_VALBRUT,,,SF1->F1_APROV,,SF1->F1_MOEDA,SF1->F1_TXMOEDA,SF1->F1_EMISSAO},SF1->F1_EMISSAO,3,SF1->F1_DOC+SF1->F1_SERIE)
		EndIf
		
		//Integracao com o ACD - Faz ajuste do CB0 apos a exclusao da Nota - Somente Protheus
		If SuperGetMV("MV_INTACD",.F.,"0") == "1" .And. !lEstNfClass
			CBSF1100E()
		
		//Template acionando ponto de entrada
		ElseIf ExistTemplate("SF1100E")
			ExecTemplate("SF1100E",.F.,.F.)
		EndIf
		
		If lMvNfeDvg .And. lChkCOG
			CA040EXC()
		EndIf
		
		If (ExistBlock("SF1100E"))
			ExecBlock("SF1100E",.F.,.F.)
		EndIf
		
		//Dados para envio de email do messenger
		aDadosMail[1]:=SF1->F1_DOC
		aDadosMail[2]:=SerieNfId("SF1",2,"F1_SERIE")
		aDadosMail[3]:=SF1->F1_FORNECE
		aDadosMail[4]:=SF1->F1_LOJA
		aDadosMail[5]:=If(cTipo$"DB",SA1->A1_NOME,SA2->A2_NOME)
		aDadosMail[6]:=If(lDeleta,5,If(l103Class,4,3))
		aDadosMail[7]:=MaFisRet(,"NF_NATUREZA")

		//Exclui a amarracao com os conhecimentos
		If lEstNfClass .And. lMsDOC
			lExcMsDoc:=ExecBlock("MT103MSD",.F.,.F.,{})
			If ValType(lExcMsDoc)<>"L"
				lExcMsDoc:=.F.
			EndIf
		EndIf
		
		//Se a NF for de Devolucao originada do LOJA720
		If SF1->F1_TIPO == "D" .AND. SF1->F1_ORIGLAN == "LO"
			aAreaAnt := GetArea()

            //Exclui titulo CR referente a taxa da administradora financeira, gerado no LOJA720 para compensar a NCC
            If ExistFunc("Lj720ExDev")
                lRet := Lj720ExDev()
            EndIf

            //Se a forma de devolucao for dinheiro, deve-se excluir o Movimento Bancario
			DbSelectArea("SE5")
			DbSetOrder(2)	//E5_FILIAL+E5_TIPODOC+E5_PREFIXO+E5_NUMERO+E5_PARCELA+E5_TIPO+DTOS(E5_DATA)+E5_CLIFOR+E5_LOJA
		    If SE5->( DbSeek(xFilial("SE5") + "LJ" + SF1->F1_PREFIXO + SF1->F1_DOC + PADR( SuperGetMV("MV_1DUP"), TamSX3("E5_PARCELA")[1]) + ;
					PADR( SuperGetMV("MV_SIMB1"), TamSX3("E5_TIPO")[1] )  + DtoS(SF1->F1_EMISSAO) + SF1->F1_FORNECE + SF1->F1_LOJA) ) .Or. ;
		     	SE5->( DbSeek(xFilial("SE5") + "DH" + SF1->F1_PREFIXO + SF1->F1_DOC + PADR( SuperGetMV("MV_1DUP"), TamSX3("E5_PARCELA")[1]) + ;
					PADR( SuperGetMV("MV_SIMB1"), TamSX3("E5_TIPO")[1] )  + DtoS(SF1->F1_EMISSAO) + SF1->F1_FORNECE + SF1->F1_LOJA) )
				oModelMov 	:= FWLoadModel("FINM030")
				oModelMov:SetOperation( MODEL_OPERATION_UPDATE ) //AlteraÁ„o
				oModelMov:Activate()
				oModelMov:SetValue( "MASTER", "E5_GRV", .T. ) //Habilita gravaÁ„o SE5
				//E5_OPERACAO 1 = Altera E5_SITUACA da SE5 para 'C' e gera estorno na FK5
				//E5_OPERACAO 2 = Grava E5 com E5_TIPODOC = 'ES' e gera estorno na FK5
				//E5_OPERACAO 3 = Deleta da SE5 e gera estorno na FK5
				oModelMov:SetValue( "MASTER", "E5_OPERACAO", 3 ) //E5_OPERACAO 3 = Deleta da SE5 e gera estorno na FK5

				//Posiciona a FKA com base no IDORIG da SE5 posicionada
				oSubFKA := oModelMov:GetModel( "FKADETAIL" )
				oSubFKA:SeekLine( { {"FKA_IDORIG", SE5->E5_IDORIG } } )

				If oModelMov:VldData()
					oModelMov:CommitData()
				Else
					lRet := .F.
					cLog := cValToChar(oModelMov:GetErrorMessage()[4]) + ' - '
					cLog += cValToChar(oModelMov:GetErrorMessage()[5]) + ' - '
					cLog += cValToChar(oModelMov:GetErrorMessage()[6])
					Help( ,,"M030VALID",,cLog, 1, 0 )
				Endif
				oModelMov:DeActivate()
			EndIf
			RestArea(aAreaAnt)
		EndIf

		If lExcMsDoc .And. !lEstNfClass
			MsDocument( "SF1", SF1->( RecNo() ), 2, , 3 )
		EndIf

		If !lEstNfClass //-- Se nao for estorno de Nota Fiscal Classificada (MATA140)
			MaAvalSF1(6)

			RecLock("SF1")
			dbDelete()
			MsUnlock()
		Else
			RecLock("SF1",.F.,.T.)
			SF1->F1_STATUS := CriaVar('F1_STATUS',.F.)
			SF1->F1_DTLANC := Ctod("")
			If cPaisLoc == "BRA"
			SF1->F1_VALIRF := 0
			EndIf
			MsUnLock()
		EndIf
		//Integracao NATIVA PROTHEUS x TAF
		//Ao Excluir uma Nota Fiscal de Terceiros no Protheus a TAFInOnLn() exclui
		//esta nota diretamente no TAF caso a mesma tenha sido importada pela intergacao
		If SF1->F1_FORMUL <> "S" .And. FindFunction("TAFExstInt") .And. TAFExstInt() .And. (SFT->(FieldPos("FT_TAFKEY")) > 0 )
			aAreaAnt := GetArea()
			dbUseArea( .T.,"TOPCONN","TAFST1","TAFST1",.T.,.F.)
			If SELECT("TAFST1") > 0
				cQuery := "DELETE FROM TAFST1 WHERE "
				cQuery += "TAFFIL    = '"+ allTrim( cEmpAnt ) + allTrim( cFilAnt ) + "' AND "
				cQuery += "TAFTPREG  = 'T013' AND "
				cQuery += "TAFSTATUS = '1'    AND "
				cQuery += "TAFKEY    = '" + xFilial("SF1")+"E"+SF1->F1_SERIE+SF1->F1_DOC+SF1->F1_FORNECE+SF1->F1_LOJA +"'"
				TcSqlExec(cQuery)
				TAFST1->(dbCloseArea())
			EndIf
			RestArea(aAreaAnt)
			TAFIntOnLn( "T013" , 5 , cFilAnt )
		Endif
		//Tratamento da gravacao do SF1 na Integridade Referencial
		SF1->(FkCommit())
	EndIf
	
	If(ExistFunc("COMTemSXI") .And. COMTemSXI("030"))//Verifica o event viewer		
		cMsgMail := STR0009 + " - "+ STR0038 + ": " + aDadosMail[2] + " "+ STR0037 + ": " + aDadosMail[1] + CHR(13) + CHR(10)		
		cMsgMail += STR0028 + ": " + aDadosMail[3] + "/"+aDadosMail[4] + " - " + aDadosMail[5] + CHR(13) + CHR(10)
		cMsgMail += STR0110 + ": " + aDadosMail[7] + CHR(13) + CHR(10) + UsrFullName()
		
		EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, "030",FW_EV_LEVEL_INFO,"", STR0009, cMsgMail,.T.)
	Else
		//Verifica a existencia de e-mails para o evento 030
		MEnviaMail("030",{aDadosMail[1],aDadosMail[2],aDadosMail[3],aDadosMail[4],aDadosMail[5],aDadosMail[6],aDetalheMail,aDadosMail[7]})
	EndIf	

	//Atualizacao dos dados contabeis
	If lCtbOnLine .And. nTotalLcto > 0
	
		//Verifica se deve mostrar a tela de lanÁamentos contabeis
		Pergunte("MTA103",.F.)
		
		//Carrega as variaveis com os parametros da execauto
		Ma103PerAut()

		lDigita := (mv_par01==1)
		
		RodaProva(nHdlPrv,nTotalLcto)
		If UsaSeqCor()
			aCtbDia := {{"SF1",SF1->(RECNO()),cCodDiario,"F1_NODIA","F1_DIACTB"}}
		Else
			aCtbDia := {}
		EndIF

		//Armazena array com as informacoes para a contabilizacao online
		aAdd(aCtbInf,cArquivo)
		aAdd(aCtbInf,nHdlPrv)
		aAdd(aCtbInf,cLote)
		aAdd(aCtbInf,lDigita)
		aAdd(aCtbInf,lAglutina)
		aAdd(aCtbInf,aCtbDia)
		
		//So passar este campo quando nao for estorno de classificacao da NFE caso contrario a CA100Incl colocara
		//novamente a data no campo F1_DTLANC impedindo que na nova classificacao a contabilizacao OFF-LINE gere um
		//novo lancamento
		If !lEstNfClass //-- Se nao for estorno de Nota Fiscal Classificada (MATA140)
			aAdd(aCtbInf,{{"F1_DTLANC",dDataBase,"SF1",SF1->(Recno()),0,0,0}})
			If Len(aFlagCTB) > 0
				For nC := 1 To Len(aFlagCTB)
					aAdd(aCtbInf[7],aFlagCTB[nC])
				Next nC
			EndIf
		Else
			aAdd(aCtbInf,{{,,,0,0,0,0}})
		EndIf
	EndIf

	If cMV_GSXNFE
		For nX := 1 to Len(aRecSD1)
			DbSelectArea("SD1")
			MsGoto(aRecSD1[nx,1])

			//Verifica se o Produto È do tipo armamento.
			aAreaSB5 := SB5->(GetArea())

			DbSelectArea('SB5')
			SB5->(DbSetOrder(1)) // acordo com o arquivo SIX -> A1_FILIAL+A1_COD+A1_LOJA

			//Realiza a exclus„o dos armamentos
			If SB5->(DbSeek(xFilial('SB5')+SD1->D1_COD)) .And. lDeleta // Filial: 01, CÛdigo: 000001, Loja: 02
				If SB5->B5_TPISERV=='2'
					lRetorno := aT720Exc(SD1->D1_DOC,SD1->D1_SERIE,.T.)
				ElseIf SB5->B5_TPISERV=='1'
					lRetorno := aT710Exc(SD1->D1_DOC,SD1->D1_SERIE,.T.)
				ElseIf SB5->B5_TPISERV=='3'
					lRetorno := aT730Exc(SD1->D1_DOC,SD1->D1_SERIE,.T.,SD1->D1_ITEM)
				EndIf
			EndIf
			RestArea(aAreaSB5)
		Next nX
	EndIf
EndIf

//Deleta Complemento DCL
If lDeleta .And. lDclNew
	DCLA013Del()
EndIf

//Ponto de Entrada Utilizado na integracao com o QIE
If lImpRel
	ExecBlock("QIEIMPRL",.F.,.F.,{nOper})
Endif

//Ponto de Entrada para Consulta de NF
If !lDeleta
	If (ExistBlock("CONAUXNF"))
		ExecBlock("CONAUXNF",.F.,.F.,{"SF1"})
	Endif
Endif

//-- aStruModel
//-- [1] - Alias
//-- [2] - Model da Estrutura
//-- [3] - bSeek
//-- [4] - nOrdem
//-- [5] - bWhile
//-- [6] - aFieldValue
//-- [6,1] Nome do Campo
//-- [6,2] Bloco de execucao para o valor
//--       a ser atribuido ao campo

If lIntGFE
	aFieldValue := { { "F1_CDTPDC", { || AllTrim(Tabela('MQ',AllTrim(SF1->F1_TIPO)+"E",.F.)) } } }
	Aadd(aStruModel, { "SA2", "REMETENTE_SA2"   , {|| xFilial("SA2") + SF1->(F1_FORNECE+F1_LOJA) }, 1, NIL, NIL } )
	Aadd(aStruModel, { "SA1", "REMETENTE_SA1"   , {|| xFilial("SA1") + SF1->(F1_FORNECE+F1_LOJA) }, 1, NIL, NIL } )
	Aadd(aStruModel, { "SA2", "REMETENTE_SM0"   , {|| xFilial("SA2") + SM0->M0_CGC }, 1, NIL, NIL } )
	Aadd(aStruModel, { "SA1", "DESTINATARIO_SA1", {|| xFilial("SA1") + SM0->M0_CGC }, 3, NIL, NIL } )
EndIf

Aadd(aStruModel, { "SF1", "MATA103_SF1"     , NIL, NIL, NIL, aFieldValue } )
Aadd(aStruModel, { "SD1", "MATA103_SD1"     , {|| SF1->(F1_FILIAL+F1_DOC+F1_SERIE+F1_FORNECE+F1_LOJA) }, 1, {|| SD1->(D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA) == SF1->(F1_FILIAL+F1_DOC+F1_SERIE+F1_FORNECE+F1_LOJA) }, NIL } )

If lNotaEmp
	If l103Class .Or. !lDeleta
		lIncNotaEmp := .T.
		lDelCX2 := .F.
	EndIf
	A103HisEmp(@aNotaEmp,lIncNotaEmp)
	If Len(aNotaEmp) > 0
		GCPGrHistNE(aNotaEmp,lDelCX2)
	EndIf
EndIf

INCLUI := lBkpInclui
ALTERA := lBkpAltera

//-- Atualiza documento no TOTVS ColaboraÁ„o
If INCLUI .And. (nRecVinc := COLConVinc(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA)) > 0
	SDS->(DbGoTo(nRecVinc))
	If SDS->DS_STATUS <> 'P'
		RecLock("SDS",.F.)
		SDS->DS_OK		:= ''
		SDS->DS_USERPRE	:= cUserName
		SDS->DS_DATAPRE	:= dDataBase
		SDS->DS_HORAPRE	:= Time()
		SDS->DS_STATUS	:= 'P'
		SDS->DS_DOCLOG	:= ''
		MsUnlock()
	Endif
Endif

//Realiza gravaÁ„o dos dados da consolidaÁ„o da NF x XML
if (INCLUI .Or. l103Class) .and. lCsdXML .and. Type("oMdlCSDGRV") == "O" 

	if(cFormul == "S") //Formul·rio prÛprio, possuo o num do doc sÛ no final do processo.
		oMdlCSDGRV:GetModel("DKAMASTER"):SetValue("DKA_DOC", cNFiscal)
		oMdlCSDGRV:GetModel("DKAMASTER"):SetValue("DKA_SERIE", cSerie)
	endif

	if oMdlCSDGRV:IsActive()
		if oMdlCSDGRV:VldData()
			if type("lGrvCSD") == "L"
				lGrvCSD := .T. //permito realizar o commit.
			endif
			if oMdlCSDGRV:CommitData()
				oMdlCSDGRV:DeActivate()
				oMdlCSDGRV:Destroy()
			endif
		endif
	endif
elseif lCsdXML .and. lDeleta
	if !IsBlind()
		FWMsgRun(, {||  A103CSDXML(2, cNFiscal, cSerie, cA100For, cLoja) }, STR0549, STR0550)//Aguarde....#"Excluindo dados consolidados..."
	else 
		A103CSDXML(2, cNFiscal, cSerie, cA100For, cLoja)
	endif
endif

If (INCLUI .Or. l103Class) .And. nItemMetric > 0
	ComMetric("-inc",l103Auto,l103Class,cTipo,nItemMetric)
Endif

Return
/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103Custo≥ Autor ≥ Edson Maricate         ≥ Data ≥27.01.2000≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Calcula o custo de entrada do Item                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103Custo(nItem)                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpN1 : Item da NF                                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103 , A103Grava()                                      ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103Custo(nItem,aHeadSE2,aColsSE2,lTxNeg,aNFCompra)

Local aCusto     := {}
Local aRet       := {}
Local aSM0       := {}
Local nPos       := 0
Local nValIV     := 0
Local nX         := 0
Local nZ         := 0
Local nFatorPS2  := 1
Local nFatorCF2  := 1
Local nValPS2    := 0
Local nValCF2    := 0
Local nValNCalc  := 0
Local lCustPad   := .T.
Local uRet       := Nil
Local lCredICM   := SuperGetMV("MV_CREDICM", .F., .F.) // Parametro que indica o abatimento do credito de ICMS no custo do item, ao utilizar o campo F4_AGREG = "I"
Local lCredPis   := SuperGetMV("MV_CREDPIS", .F., .F.)
Local lCredCof   := SuperGetMV("MV_CREDCOF", .F., .F.)
Local lDEDICMA   := SuperGetMV("MV_DEDICMA", .F., .F.) // Efetua deducao do ICMS anterior nao calculado pelo sistema
Local lDedIcmAnt := .F.
Local lValCMaj   := !Empty(MaFisScan("IT_VALCMAJ",.F.)) // Verifica se a MATXFIS possui a referentcia IT_VALCMAJ
Local lValPMaj   := !Empty(MaFisScan("IT_VALPMAJ",.F.)) // Verifica se a MATXFIS possui a referentcia IT_VALCMAJ
Local nPosItOri  := GetPosSD1("D1_ITEMORI")
Local cCodFil    := ""
Local cAliasAux  := ""
Local lCustRon   := SuperGetMV("MV_CUSTRON",.F.,.T.)
Local lSimpNac   := MaFisRet(,"NF_SIMPNAC") == "1" .Or. MaFisRet(,"NF_UFORIGEM") == "EX"

Default lTxNeg := .F.

If FindFunction("A103xCusto")
	aRet := A103xCusto(nItem,aHeadSE2,aColsSE2,lTxNeg,aNFCompra)
	Return aRet
EndIf

//Calcula o percentual para credito do PIS / COFINS
If !Empty( SF4->F4_BCRDPIS )
	nFatorPS2 := SF4->F4_BCRDPIS / 100
EndIf

If !Empty( SF4->F4_BCRDCOF )
	nFatorCF2 := SF4->F4_BCRDCOF / 100
EndIf

nValPS2 := MaFisRet(nItem,"IT_VALPS2") * nFatorPS2
nValCF2 := MaFisRet(nItem,"IT_VALCF2") * nFatorCF2

If SF4->(FieldPos("F4_CRDICMA")) > 0 .And. !Empty(SF4->F4_CRDICMA)
	lDedIcmAnt := SF4->F4_CRDICMA == '1'
Else
	lDedIcmAnt := lDEDICMA
EndIf
If lDedIcmAnt
	nValNCalc := MaFisRet(nItem,"IT_ICMNDES")
EndIf

l103Auto := Type("l103Auto") <> "U" .And. l103Auto

If l103Auto .And. (nPos:= aScan(aAutoItens[nItem],{|x|Trim(x[1])== "D1_CUSTO" })) > 0
	aADD(aCusto,{	aAutoItens[nItem,nPos,2],;
					0.00,;
					0.00,;
					SF4->F4_CREDIPI,;
					SF4->F4_CREDICM,;
					MaFisRet(nItem,"IT_NFORI"),;
					MaFisRet(nItem,"IT_SERORI"),;
					SD1->D1_COD,;
					SD1->D1_LOCAL,;
					SD1->D1_QUANT,;
					If(SF4->F4_IPI=="R",MaFisRet(nItem,"IT_VALIPI"),0) ,;
					SF4->F4_CREDST,;
					MaFisRet(nItem,"IT_VALSOL"),;
					MaRetIncIV(nItem,"1"),;
					SF4->F4_PISCOF,;
					SF4->F4_PISCRED,;
					nValPS2 - (IIf(lValPMaj,MaFisRet(nItem,"IT_VALPMAJ"),0)),;
					nValCF2 - (IIf(lValCMaj,MaFisRet(nItem,"IT_VALCMAJ"),0)),;
					IIf(SF4->F4_ESTCRED>0,MaFisRet(nItem,"IT_ESTCRED"),0)   ,;
					IIf(lSimpNac,MaFisRet(nItem, "LF_CRDPRES"),0),;
					MaFisRet(nItem,"IT_VALANTI"),;
					If(nPosItOri > 0, aCols[nItem][nPosItOri], ""),;
					MaFisRet(nItem, "IT_VALFEEF"); // Issue DMANMAT01-21311 - ApropriaÁ„o do imposto FEEF ao custo de entrada
				})
Else
	nValIV	:=	MaRetIncIV(nItem,"2")

	If SD1->D1_COD == Left(SuperGetMV("MV_PRODIMP"), Len(SD1->D1_COD))
		aADD(aCusto,{	MaFisRet(nItem,"IT_TOTAL")-IIF(cTipo=="P".Or.SF4->F4_IPI=="R",0,MaFisRet(nItem,"IT_VALIPI"))+MaFisRet(nItem,"IT_VALICM")+If((SF4->F4_CIAP=="S".And.SF4->F4_CREDICM=="S").Or.SF4->F4_ANTICMS=="1",0,MaFisRet(nItem,"IT_VALCMP"))-If(SF4->F4_INCSOL<>"N",MaFisRet(nItem,"IT_VALSOL"),0)-nValIV+IF(SF4->F4_ICM=="S" .And. SF4->F4_AGREG$'A|C',MaFisRet(nItem,"IT_VALICM"),0)+IF(SF4->F4_AGREG=='D' .And. SF4->F4_BASEICM == 0,MaFisRet(nItem,"IT_DEDICM"),0)-MaFisRet(nItem,"IT_CRPRESC")-MaFisRet(nItem,"IT_CRPREPR")+MaFisRet(nItem,"IT_VLINCMG")+IIf(!lCredPis .And. SF4->F4_AGRPIS=="2" .And. SF4->F4_AGREG$"I|B",nValPS2-(IIf(lValPMaj,MaFisRet(nItem,"IT_VALPMAJ"),0)),0)+IIf(!lCredCof .And. SF4->F4_AGRCOF=="2" .And. SF4->F4_AGREG$"I|B",nValCF2-(IIf(lValCMaj,MaFisRet(nItem,"IT_VALCMAJ"),0)),0) - nValNCalc,;
						MaFisRet(nItem,"IT_VALIPI"),;
						MaFisRet(nItem,"IT_VALICM"),;
						SF4->F4_CREDIPI,;
						SF4->F4_CREDICM,;
						MaFisRet(nItem,"IT_NFORI"),;
						MaFisRet(nItem,"IT_SERORI"),;
						SD1->D1_COD,;
						SD1->D1_LOCAL,;
						SD1->D1_QUANT,;
						If(SF4->F4_IPI=="R",MaFisRet(nItem,"IT_VALIPI"),0) ,;
						SF4->F4_CREDST,;
						MaFisRet(nItem,"IT_VALSOL"),;
						MaRetIncIV(nItem,"1"),;
						SF4->F4_PISCOF,;
						SF4->F4_PISCRED,;
						nValPS2 - (IIf(lValPMaj,MaFisRet(nItem,"IT_VALPMAJ"),0)),;
						nValCF2 - (IIf(lValCMaj,MaFisRet(nItem,"IT_VALCMAJ"),0)),;
						IIf(SF4->F4_ESTCRED>0,MaFisRet(nItem,"IT_ESTCRED"),0)   ,;
						IIf(lSimpNac,MaFisRet(nItem, "LF_CRDPRES"),0),;
						MaFisRet(nItem,"IT_VALANTI"),;
						If(nPosItOri > 0, aCols[nItem][nPosItOri], ""),;
						MaFisRet(nItem, "IT_VALFEEF"); // Issue DMANMAT01-21311 - ApropriaÁ„o do imposto FEEF ao custo de entrada
					})
	Else
		aADD(aCusto,{	MaFisRet(nItem,"IT_TOTAL")-IIf(cTipo=="P".Or.SF4->F4_IPI=="R",0,MaFisRet(nItem,"IT_VALIPI"))+IIf((SF4->F4_CIAP=="S" .And. SF4->F4_CREDICM=="S").Or. SF4->F4_ANTICMS=="1",0,MaFisRet(nItem,"IT_VALCMP"))-IIf(SF4->F4_INCSOL<>"N",MaFisRet(nItem,"IT_VALSOL"),0)-nValIV+IIf(SF4->F4_ICM=="S" .And. SF4->F4_AGREG$'A|C',MaFisRet(nItem,"IT_VALICM"),0)+IIf(SF4->F4_AGREG=='D' .And. SF4->F4_BASEICM == 0,MaFisRet(nItem,"IT_DEDICM"),0)-MaFisRet(nItem,"IT_CRPRESC")-MaFisRet(nItem,"IT_CRPREPR")+MaFisRet(nItem,"IT_VLINCMG")-IIf(lCredICM .And. SF4->F4_AGREG$"I|B",MaFisRet(nItem,"IT_VALICM"),0)-IIf(SF4->F4_AGREG == "B",MaFisRet(nItem,"IT_VALSOL"),0)+IIf(!lCredPis .And.SF4->F4_AGRPIS=="2" .And. SF4->F4_AGREG$"I|B",nValPS2-(IIf(lValPMaj,MaFisRet(nItem,"IT_VALPMAJ"),0)),0)+IIf(!lCredCof .And. SF4->F4_AGRCOF=="2" .And. SF4->F4_AGREG$"I|B",nValCF2-(IIf(lValCMaj,MaFisRet(nItem,"IT_VALCMAJ"),0)),0) - nValNCalc,;
						MaFisRet(nItem,"IT_VALIPI"),;
						MaFisRet(nItem,"IT_VALICM"),;
						SF4->F4_CREDIPI,;
						SF4->F4_CREDICM,;
						MaFisRet(nItem,"IT_NFORI"),;
						MaFisRet(nItem,"IT_SERORI"),;
						SD1->D1_COD,;
						SD1->D1_LOCAL,;
						SD1->D1_QUANT,;
						If(SF4->F4_IPI=="R",MaFisRet(nItem,"IT_VALIPI"),0),;
						SF4->F4_CREDST,;
						MaFisRet(nItem,"IT_VALSOL"),;
						MaRetIncIV(nItem,"1"),;
						SF4->F4_PISCOF,;
						SF4->F4_PISCRED,;
						nValPS2 - (IIf(lValPMaj,MaFisRet(nItem,"IT_VALPMAJ"),0)),;
						nValCF2 - (IIf(lValCMaj,MaFisRet(nItem,"IT_VALCMAJ"),0)),;
						IIf(SF4->F4_ESTCRED > 0,MaFisRet(nItem,"IT_ESTCRED"),0) ,;
						IIf(lSimpNac,MaFisRet(nItem, "LF_CRDPRES"),0),;
						Iif(SF4->F4_CREDST != '2' .And. SF4->F4_ANTICMS == '1',MaFisRet(nItem,"IT_VALANTI"),0),;
						If(nPosItOri > 0, aCols[nItem][nPosItOri], ""),;
						MaFisRet(nItem, "IT_VALFEEF"); // Issue DMANMAT01-21311 - ApropriaÁ„o do imposto FEEF ao custo de entrada
					})
	EndIf
EndIf

//Nao considerar o custo de uma entrada por devolucao ou bonificacao
If (SD1->D1_TIPO == "D" .And. SF4->F4_DEVZERO == "2") .Or. Iif (cPaisLoc == "BRA", (SF4->F4_BONIF == "S" .And. SF4->F4_CREDICM != "S"),.F.)
	aRet := {{0,0,0,0,0}}
ElseIf SF4->F4_TRANFIL == "1" .And. lCustRon .And. SD1->D1_TIPO == "N" //-- Para transferencia entre filiais, obtem o custo da origem
	SA2->(DbSetOrder(1))
	SA2->(MsSeek(xFilial("SA2") + SD1->D1_FORNECE + SD1->D1_LOJA))

	If UsaFilTrf() //-- Procura pelo campo
		cCodFil := SA2->A2_FILTRF
	Else //-- Procura pelo CNPJ
		aSM0 := FwLoadSM0(.T.)
		If Len(aSM0) > 0
			nX := aScan(aSM0,{|x| AllTrim(x[SM0_CGC]) == AllTrim(SA2->A2_CGC)})
			If nX > 0
				cCodFil := aSM0[nX, SM0_CODFIL]
			EndIf
		EndIf
	EndIf

	If !Empty(cCodFil)
		cAliasAux := GetNextAlias()
		BeginSQL Alias cAliasAux
            SELECT
                D2_CUSTO1,
                D2_CUSTO2,
                D2_CUSTO3,
                D2_CUSTO4,
                D2_CUSTO5
            FROM
                %Table:SD2% SD2
            WHERE
                D2_FILIAL = %Exp:xFilial("SD2", cCodFil)%
                AND D2_DOC = %Exp:SD1->D1_DOC%
                AND D2_SERIE = %Exp:SD1->D1_SERIE%
                AND D2_ITEM = %Exp:CodeSoma1(SD1->D1_ITEM, FwTamSX3("D2_ITEM")[1])%
                AND SD2.%NotDel%
		EndSQL

		If !(cAliasAux)->(Eof())
			aRet := {{(cAliasAux)->D2_CUSTO1, (cAliasAux)->D2_CUSTO2, (cAliasAux)->D2_CUSTO3, (cAliasAux)->D2_CUSTO4, (cAliasAux)->D2_CUSTO5}}
			// Permite agregar o valor do ICMS ST (Retido) ao custo de entrada das notas fiscais de entrada,
			// geradas pelo processo de TransferÍncia de Filiais.
			If SF4->F4_TRFICST == '1'
				For nX := 1 to len(aRet[01])
					If aRet[01,nX]>0
						If nX == 1
							aRet[01,nX] := aRet[01,nX]+SD1->D1_ICMSRET
						Else
							aRet[01,nX] := aRet[01,nX]+xMoeda(SD1->D1_ICMSRET,1,nX,SD1->D1_DTDIGIT)
						EndIf
					EndIf
				Next nX
			EndIf
		Else
			aRet := {{0,0,0,0,0}}
		EndIf
		(cAliasAux)->(DbCloseArea())
	Else
		aRet := {{0,0,0,0,0}}
	EndIf
Else
	aRet := RetCusEnt(aDupl,aCusto,cTipo,,,aNFCompra,,,,,lTxNeg)
	If SF4->F4_AGREG == "N"
		For nX := 1 to Len(aRet[1])
			aRet[1][nX] := If(aRet[1][nX]>0,aRet[1][nX],0)
		Next nX
	EndIf
EndIf

//A103CUST - Ponto de entrada utilizado para manipular os valores
//           do custo de entrada nas 5 moedas.
If ExistBlock("A103CUST")
	uRet := ExecBlock("A103CUST",.F.,.F.,{aRet})
	If Valtype(uRet) == "A" .And. Len(uRet) > 0
		For nX := 1 To Len(uRet)
			For nZ:=1 To 5
				If Valtype(uRet[nX,nZ]) != "N"	//Uso o array original se retorno nao for numerico
					lCustPad := .F.
					Exit
				EndIf
			Next nZ
		Next nX
		If lCustPad
			aRet := aClone(uRet)
		EndIf
	EndIf
EndIf

Return aRet[1]

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥Ma103Track≥ Autor ≥ Aline Correa do Vale  ≥ Data ≥05/06/2003≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Faz o tratamento da chamada do System Tracker              ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ .T.                                                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ Nenhum                                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao Efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103Track()

Local aEnt     := {}
Local cKey     := cNFiscal + Substr(cSerie,1,3) + cA100For + cLoja
Local nPosItem := GetPosSD1( "D1_ITEM" )
Local nPosCod  := GetPosSD1( "D1_COD"  )
Local nLoop    := 0
Local aArea    := GetArea()
Local aAreaSF1 := SF1->( GetArea() )

//Inicializa a funcao fiscal
For nLoop := 1 To Len( aCols )
	AAdd( aEnt, { "SD1", cKey + aCols[ nLoop, nPosCod ] + aCols[ nLoop, nPosItem ] } )
Next nLoop

MaFisSave()
MaFisEnd()

MaTrkShow( aEnt )

MaFisRestore()

RestArea(aAreaSF1)
RestArea(aArea)

Return( .T. )

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥AliasInDic≥ Autor ≥ Sergio Silveira       ≥ Data ≥02/01/2004≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Indica se um determinado alias esta presente no dicionario ≥±±
±±≥          ≥ de dados                                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ ExpL1 := AliasInDic( ExpC1, ExpL2 )                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ ExpL1 -> .T. - Tabela presente / .F. - tabela nao presente ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpC1 -> Alias                                             ≥±±
±±≥          ≥ ExpL2 -> Indica se exibe help de tabela inexistente        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Function AliasInDic(cAlias,lHelp)
Return FWAliasInDic(cAlias,lHelp)

/*/{Protheus.doc} NfeCalcRet
	Efetua o calculo do valor de titulos financeiros que
	calcularam a retencao do PIS / COFINS / CSLL e nao  
	criaram os titulos de retencao                      
	@type  Static Function
	@author Sergio Silveira 
	@since 24/03/2021
	@version 1.0
	@param dReferencia, Date, Data de referencia para verificaÁ„o dos titulos
	@param nIndexSE2, Numeric, Indice da tabela SE2
	@param aDadosImp, Array, Array que ira conter as informaÁıes das retenÁıes
	@return aDadosRef, Array , Array que ira conter as informaÁıes das retenÁıes
		aDadosRef -> Array com os seguintes elementos                   
    	1 - Valor dos titulos                                
       	2 - Valor do PIS                                     
       	3 - Valor do COFINS                                  
       	4 - Valor da CSLL                                    
       	5 - Array contendo os recnos dos registos processados
	@example
	(examples)
	@see (links_or_references)
/*/
Static Function NfeCalcRet( dReferencia, nIndexSE2, aDadosImp )

Local aAreaSE2  := SE2->( GetArea() )
Local aDadosRef := Array(8)
Local aRecnos   := {}
Local nAdic     := 0
Local dDataIni  := FirstDay( dReferencia )
Local dDataFim  := LastDay( dReferencia )
Local cModTot   := GetNewPar( "MV_MT10925", "1" )
Local lBaseImp  := ( SuperGetMv("MV_BS10925",.F.,"1") == "1")
Local lIrfMp232 :=	Iif (cPaisLoc == "BRA",SA2->A2_CALCIRF == "2",.F.)

//Chamado SDFPWW
Local cAglutFil := SuperGetMV("MV_PCCAGFL",,"1")
Local aAreaSM0  := {}
Local cCGCSM0   := ""
Local cEmpAtu   := ""
Local aStruct   := {}
Local aCampos   := {}
Local aFil10925 := {}
Local cAliasQry := ""
Local cSepNeg   := If("|"$MV_CPNEG,"|",",")
Local cSepProv  := If("|"$MVPROVIS,"|",",")
Local cSepRec   := If("|"$MVPAGANT,"|",",")
Local cQuery    := ""
Local cQryFil   := ""
Local cVencPub	:= SuperGetMV("MV_VENPUB", .F., "M")
Local nVencto 	:= SuperGetMv("MV_VCPCCP",.T.,1)
Local nLoop     := 0
Local lLojaAtu  := ( GetNewPar( "MV_LJ10925", "1" ) == "1" )

	

Default aDadosImp := Array(3)

If cVencPub == "D"
	dDataIni := dDataFim := dReferencia 
EndIF

If __lEmpPub
	aDadosImp := Array(4)
	aDadosRef := Array(10)
EndIf

AFill( aDadosRef, 0 )
AFill( aDadosImp, 0 )

	aFil10925 := {}
	aAreaSM0  := SM0->(GetArea())
	cEmpAtu   := SM0->M0_CODIGO
	cCGCSM0   := SM0->M0_CGC
	SM0->(DbSetOrder(1))
	SM0->(MsSeek(cEmpAnt))

	//Se parametro "MV_PCCAGFR" existe com conteudo diferente de 1
	If cAglutFil == "2" .Or. cAglutFil == "3"
		Do While !SM0->(Eof()) .And. SM0->M0_CODIGO == cEmpAtu
			//Verifica se a filial tem o mesmo CGC/Raiz de CGC
			If (cAglutFil == "2" .And. cCGCSM0 == SM0->M0_CGC) .Or. (cAglutFil == "3" .And. Left(cCGCSM0,8) == Left(SM0->M0_CGC,8))
			AAdd(aFil10925,FWGETCODFILIAL)
			EndIf
			SM0->(DbSkip())
		EndDo

	ElseIf ExistBlock( "MT103FRT" )
		aFil10925 := ExecBlock( "MT103FRT", .F., .F. )
	Else
		aFil10925 := { cFilAnt }
	EndIf
	SM0->(RestArea(aAreaSM0))

	aCampos := { "E2_VALOR","E2_IRRF","E2_ISS","E2_INSS","E2_PIS","E2_COFINS","E2_CSLL","E2_VRETPIS","E2_VRETCOF","E2_VRETCSL" }
	aStruct := SE2->( dbStruct() )

	SE2->( dbCommit() )

	cAliasQry := GetNextAlias()

	cQuery := "SELECT E2_VALOR,E2_PIS,E2_COFINS,E2_EMISSAO,E2_CSLL,E2_ISS,E2_INSS,E2_IRRF,E2_VRETPIS,E2_VRETCOF,E2_VRETCSL,E2_PRETPIS,E2_PRETCOF,E2_PRETCSL,R_E_C_N_O_ RECNO "
	cQuery += ",E2_BASEPIS,E2_BASECOF,E2_BASECSL,E2_VRETIRF,E2_NATUREZ, E2_PRETIRF ,E2_BASEIRF"
	Aadd(aCampos,"E2_BASEPIS")
	Aadd(aCampos,"E2_BASECOF")
	Aadd(aCampos,"E2_BASECSL")
	Aadd(aCampos,"E2_BASEIRF")
	Aadd(aCampos,"E2_VRETIRF")

	cQuery += "FROM "+RetSqlName( "SE2" ) + " SE2 "
	cQuery += "WHERE "

	//Carrega as filiais do filtro
	cQryFil := "("

	If cAglutFil <> "1" .OR. ExistBlock( "MT103FRT" )
		For nLoop := 1 to Len( aFil10925 )
			cQryFil += "E2_FILIAL='" + aFil10925[ nLoop ] + "' OR "
		Next nLoop

		cQryFil := Left( cQryFil, Len( cQryFil ) - 3 )
	Else
		cQryFil += "E2_FILORIG='" + aFil10925[ 1 ] + "' "
	EndIf

	cQryFil  += ") AND "

	cQuery += cQryFil

	cQuery += " E2_FORNECE='"   + cA100For             + "' AND "
	If lLojaAtu
		cQuery += " E2_LOJA='"  + cLoja                + "' AND "
	Endif
	
	If nVencto == 2
		cQuery += " E2_VENCREA>= '" + DToS( dDataIni )      + "' AND "
		cQuery += " E2_VENCREA<= '" + DToS( dDataFim )      + "' AND "
	ElseIf nVencto == 1 .OR. EMPTY(nVencto)
		cQuery += " E2_EMISSAO>= '" + DToS( dDataIni )      + "' AND "
		cQuery += " E2_EMISSAO<= '" + DToS( dDataFim )      + "' AND "
	ElseIf nVencto == 3
		cQuery += " E2_EMIS1>= '" + DToS( dDataIni )      + "' AND "
		cQuery += " E2_EMIS1<= '" + DToS( dDataFim )      + "' AND "
	Endif

	cQuery += " E2_TIPO NOT IN " + FormatIn(MVABATIM,"|") + " AND "
	cQuery += " E2_TIPO NOT IN " + FormatIn(MV_CPNEG,cSepNeg)  + " AND "
	cQuery += " E2_TIPO NOT IN " + FormatIn(MVPROVIS,cSepProv) + " AND "
	cQuery += " E2_TIPO NOT IN " + FormatIn(MVPAGANT,cSepRec)  + " AND "
	cQuery += " D_E_L_E_T_=' '"

	cQuery := ChangeQuery( cQuery )
	dbUseArea( .T., "TOPCONN", TcGenQry(,,cQuery), cAliasQry, .F., .T. )

	For nLoop := 1 To Len( aStruct )
		If !Empty( AScan( aCampos, AllTrim( aStruct[nLoop,1] ) ) )
			TcSetField( cAliasQry, aStruct[nLoop,1], aStruct[nLoop,2],aStruct[nLoop,3],aStruct[nLoop,4])
		EndIf
	Next nLop

	While !( cAliasQRY )->( Eof())

		//Armazena os valores calculados de PIS/COFINS/CSLL para cada titulo.
		//Este valor sera utilizado para se calcular o residual nao retido (quando o titulo
		//onde a retencao deveria ter sido feita tiver o valor menor que o valor total a ser
		//retido).
		If ( cAliasQRY )->E2_PIS > 0
			aDadosImp[1] += ( cAliasQRY )->E2_PIS
		EndIf

		If ( cAliasQRY )->E2_COFINS > 0
			aDadosImp[2] += ( cAliasQRY )->E2_COFINS
		EndIf

		If ( cAliasQRY )->E2_CSLL > 0
			aDadosImp[3] += ( cAliasQRY )->E2_CSLL
		EndIf

		If __lEmpPub
			If ( cAliasQRY )->E2_IRRF > 0
				aDadosImp[4] += ( cAliasQRY )->E2_IRRF
			EndIf
		EndIf

		nAdic := 0

		nAdic += ( ( cAliasQRY )->E2_VALOR + ( cAliasQRY )->E2_ISS + ( cAliasQRY )->E2_INSS + ( cAliasQRY )->E2_IRRF )

		If Empty( ( cAliasQRY )->E2_PRETPIS )
			nAdic += If( Empty( ( cAliasQRY )->E2_VRETPIS ), ( cAliasQRY )->E2_PIS, ( cAliasQRY )->E2_VRETPIS )
			// Armazena os valores calculados por titulo, retirando os valores retidos
			If ( cAliasQRY )->E2_VRETPIS + ( cAliasQRY )->E2_VRETCOF + ( cAliasQRY )->E2_VRETCSL + IF(lIrfMP232, ( cAliasQRY )->E2_VRETIRF , 0 ) > 0
				aDadosImp[1] -= (cAliasQRY)->E2_VRETPIS
			Endif
		EndIf

		If Empty( ( cAliasQRY )->E2_PRETCOF )
			nAdic += If( Empty( ( cAliasQRY )->E2_VRETCOF ), ( cAliasQRY )->E2_COFINS, ( cAliasQRY )->E2_VRETCOF )
			//Armazena os valores calculados por titulo, retirando os valores retidos
			If ( cAliasQRY )->E2_VRETPIS + ( cAliasQRY )->E2_VRETCOF + ( cAliasQRY )->E2_VRETCSL + IF(lIrfMP232, ( cAliasQRY )->E2_VRETIRF , 0 ) > 0
				aDadosImp[2] -= (cAliasQRY)->E2_VRETCOF
			Endif
		EndIf

		If Empty( ( cAliasQRY )->E2_PRETCSL )
			nAdic += If( Empty( ( cAliasQRY )->E2_VRETCSL ), ( cAliasQRY )->E2_CSLL, ( cAliasQRY )->E2_VRETCSL )
			//Armazena os valores calculados por titulo, retirando os valores retidos
			If ( cAliasQRY )->E2_VRETPIS + ( cAliasQRY )->E2_VRETCOF + ( cAliasQRY )->E2_VRETCSL + IF(lIrfMP232, ( cAliasQRY )->E2_VRETIRF , 0 ) > 0
				aDadosImp[3] -= (cAliasQRY)->E2_VRETCSL
			Endif
		EndIf

		If __lEmpPub .And. Empty( ( cAliasQRY )->E2_PRETIRF)
			nAdic += If( Empty( ( cAliasQRY )->E2_PRETIRF ), ( cAliasQRY )->E2_IRRF, ( cAliasQRY )->E2_VRETIRF )
			// Armazena os valores calculados por titulo, retirando os valores retidos
			If ( cAliasQRY )->E2_VRETPIS + ( cAliasQRY )->E2_VRETCOF + ( cAliasQRY )->E2_VRETCSL + IF(lIrfMP232, ( cAliasQRY )->E2_VRETIRF , 0 ) > 0
				aDadosImp[4] -= (cAliasQRY)->E2_VRETIRF
			Endif
		EndIf

		If cModTot == "1"
			aDadosRef[1] += nAdic

			If  lBaseImp
				If ( cAliasQRY )->E2_BASEPIS > 0 .Or. ( cAliasQRY )->E2_BASECOF > 0 .Or. ( cAliasQRY )->E2_BASECSL > 0
					aDadosRef[6] += ( cAliasQRY )->E2_BASEPIS
					aDadosRef[7] += ( cAliasQRY )->E2_BASECOF
					aDadosRef[8] += ( cAliasQRY )->E2_BASECSL
					If __lEmpPub
						aDadosRef[9] += ( cAliasQRY )->E2_BASEIRF
					EndIf
				Else
					aDadosRef[6] += nAdic
					aDadosRef[7] += nAdic
					aDadosRef[8] += nAdic
				EndIf
			Else
				aDadosRef[6] += nAdic
				aDadosRef[7] += nAdic
				aDadosRef[8] += nAdic
			EndIf
		Endif

		If !__lEmpPub
			If ( !Empty( ( cAliasQRY )->E2_PIS ) .Or. !Empty( ( cAliasQRY )->E2_COFINS ) .Or. !Empty( ( cAliasQRY )->E2_CSLL ) )

				If cModTot == "2"
					aDadosRef[1] += nAdic

					If  lBaseImp
						If ( cAliasQRY )->E2_BASEPIS > 0 .Or. ( cAliasQRY )->E2_BASECOF > 0 .Or. ( cAliasQRY )->E2_BASECSL > 0
							aDadosRef[6] += ( cAliasQRY )->E2_BASEPIS
							aDadosRef[7] += ( cAliasQRY )->E2_BASECOF
							aDadosRef[8] += ( cAliasQRY )->E2_BASECSL
						Else
							aDadosRef[6] += nAdic
							aDadosRef[7] += nAdic
							aDadosRef[8] += nAdic
						EndIf
					Else
						aDadosRef[6] += nAdic
						aDadosRef[7] += nAdic
						aDadosRef[8] += nAdic
					EndIf
				Endif

				If ( Empty( ( cAliasQRY )->E2_VRETPIS ) .Or. Empty( ( cAliasQry )->E2_VRETCOF ) .Or. Empty( ( cAliasQry )->E2_VRETCSL ) ) ;
						.And. ( ( cAliasQRY )->E2_PRETPIS == "1" .Or. ( cAliasQry )->E2_PRETCOF == "1" .Or. ( cAliasQry )->E2_PRETCSL == "1" )

					If Empty( ( cAliasQRY )->E2_VRETPIS ) .And. ( cAliasQRY )->E2_PRETPIS == "1"
						aDadosRef[2] += ( cAliasQRY )->E2_PIS
					EndIf

					If Empty( ( cAliasQRY )->E2_VRETCOF )	.And. ( cAliasQRY )->E2_PRETCOF == "1"
						aDadosRef[3] += ( cAliasQRY )->E2_COFINS
					EndIf

					If Empty( ( cAliasQRY )->E2_VRETCSL ) .And. ( cAliasQRY )->E2_PRETCSL == "1"
						aDadosRef[4] += ( cAliasQRY )->E2_CSLL
					EndIf
					AAdd( aRecnos, ( cAliasQRY )->RECNO )
				Endif		
			Endif
		Else
			If ( cAliasQRY )->RECNO <> SE2->(Recno())
				SED->( dbSetOrder(1) ) //ED_FILIAL+ED_CODIGO
				If SED->( msSeek( xFilial("SED") + ( cAliasQRY )->E2_NATUREZ) ) 
				
					If ( cAliasQRY )->E2_PRETPIS == "1"	.OR. !Empty( ( cAliasQRY )->E2_VRETPIS )
						aDadosRef[2] += ( cAliasQRY )->E2_BASEPIS * SED->ED_PERCPIS / 100
					Endif

					If ( cAliasQRY )->E2_PRETCOF == "1" .OR. !Empty( ( cAliasQRY )->E2_VRETCOF )
						aDadosRef[3] += ( cAliasQRY )->E2_BASEPIS * SED->ED_PERCCOF / 100
					Endif

					If ( cAliasQRY )->E2_PRETCSL == "1" .OR. !Empty( ( cAliasQRY )->E2_VRETCSL )
						aDadosRef[4] += ( cAliasQRY )->E2_BASEPIS * SED->ED_PERCCSL / 100
					Endif

					If ( cAliasQRY )->E2_PRETIRF == "1" .OR. !Empty( ( cAliasQRY )->E2_VRETIRF )
						aDadosRef[10] += ( cAliasQRY )->E2_BASEIRF * SED->ED_PERCIRF / 100
					Endif

				Endif
			Endif					

		Endif

		( cAliasQRY )->( dbSkip())

	EndDo

	// Fecha a area de trabalho da query

	( cAliasQRY )->( dbCloseArea() )
	DbSelectArea( "SE2" )

aDadosRef[ 5 ] := AClone( aRecnos )

SE2->( RestArea( aAreaSE2 ) )

Return( aDadosRef )

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103TmsVld≥ Autor ≥Eduardo de Souza       ≥ Data ≥ 30/08/04 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Valida exclusao do movimentos de custos de transporte.      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ExpL1 := A103TmsVld( ExpL1 )                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpD1 - Verifica se eh exclusao                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥SigaTMS                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Static Function A103TmsVld(l103Exclui)

Local lRet     := .T.
Local nCnt     := 0
Local aAreaSD1 := SD1->(GetArea())

If l103Exclui .And. IntTMS() // Integracao TMS
	SD1->(DbSetOrder(1))
	For nCnt := 1 To Len(aCols)
		If SD1->(MsSeek(xFilial("SD1")+cNFiscal+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja+GDFieldGet("D1_COD",nCnt)+GDFieldGet("D1_ITEM",nCnt)))
			SDG->(DbSetOrder(7))
			If SDG->(MsSeek(xFilial("SDG")+"SD1"+SD1->D1_NUMSEQ))
				While SDG->(!Eof()) .And. SDG->DG_FILIAL + SDG->DG_ORIGEM + SDG->DG_SEQMOV == xFilial("SDG") + "SD1" + SD1->D1_NUMSEQ
					If SDG->DG_STATUS <> StrZero(1,Len(SDG->DG_STATUS)) //-- Em Aberto
						//-- Caso somente a viagem esteja informada ou Frota, estorna o movimento de custo de transporte.
						If !( Empty(SDG->DG_CODVEI) .And. Empty(SDG->DG_FILORI) .And. Empty(SDG->DG_VIAGEM) ) .And. ;
								!( Empty(SDG->DG_CODVEI) .And. !Empty(SDG->DG_FILORI) .And. !Empty(SDG->DG_VIAGEM) )
							//-- Caso a veiculo seja proprio estorna o movimento de custo de transporte.
							If !Empty(SDG->DG_CODVEI) .And. Empty(SDG->DG_FILORI) .And. Empty(SDG->DG_VIAGEM)
								DA3->(DbSetOrder(1))
								If DA3->(MsSeek(xFilial("DA3")+SDG->DG_CODVEI))
									If DA3->DA3_FROVEI <> "1"
										lRet := .F.
										Exit
									EndIf
								EndIf
							Else
							   //-- Origem MATA103, nao h· validaÁ„o na inclus„o pelo TMSA070
								If SDG->DG_ORIGEM <> 'SD1' .And. SDG->DG_ORIGEM <> 'SD3'
									lRet := .F.
									Exit
								EndIf
							EndIf
						EndIf
					EndIf
					SDG->(DbSkip())
				EndDo
			EndIf
		EndIf
	Next nCnt
	RestArea( aAreaSD1 )
EndIf

If !lRet
	Help(" ",1,"A103NODEL") //-- Existe movimento de custo de transporte baixado, nao sera permitida a exclusao.
EndIf

Return lRet

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103TemBlq≥ Autor ≥ Edson Maricate        ≥ Data ≥17.02.2005≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Validacao da TudoOk                                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ Nenhum                                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103TemBlq(l103Class)

Local aArea     := GetArea()
Local aAreaSC7  := SC7->(GetArea())
Local aSldItem	:= {}
Local aAreaAux  := {}
Local cKeySF1	:= (SF1->F1_DOC + SF1->F1_SERIE + SF1->F1_FORNECE + SF1->F1_LOJA)
Local cFilSD1   := xFilial("SD1")
Local cFilEntC7 := xFilEnt(xFilial("SC7"), "SC7")
Local lRet      := .F.
Local lVerifica := .T.
Local lDescTol	:= SuperGetMV("MV_DESCTOL",.F.,.F.)
Local lRestCla  := SuperGetMV("MV_RESTCLA",.F.,"2")=="2"
Local lPcDescTol:= SuperGetMV("MV_PCDETOL",.F.,.F.)
Local lExistSCR1:= .F.
Local lExistSCR2:= .F.
Local lLibSCROk := .F.
Local lMT103NBL := ExistBlock("MT103NBL")
Local nX        := 0
Local nPosPc    := GetPosSD1("D1_PEDIDO")
Local nPosItPc  := GetPosSD1("D1_ITEMPC")
Local nPosQtd   := GetPosSD1("D1_QUANT")
Local nPosVlr   := GetPosSD1("D1_VUNIT")
Local nPosDoc   := GetPosSD1("D1_DOC")
Local nPosSerie := GetPosSD1("D1_SERIE")
Local nPosForn  := GetPosSD1("D1_FORNECE")
Local nPosLjFor := GetPosSD1("D1_LOJA")
Local nPosCod   := GetPosSD1("D1_COD")
Local nPosItem  := GetPosSD1("D1_ITEM")
Local nPosDesc  := GetPosSD1("D1_VALDESC")
Local nUsado    := len(aHeader)
Local nDecimalPC:= TamSX3("C7_PRECO")[2]
Local nQuJE		:= 0
Local nQtde		:= 0
Local nQaCl		:= 0
Local nQtdItem	:= 0
Local nVlrItem	:= 0
Local nDescItem	:= 0
Local nCRTotal  := 0
Local nY		:= 0
Local nF1ValBrut:= 0
Local nQtAux    := 0
Local cItAux    := ""
Local nDescSC7  := 0
Local lNfMotBloq:= SCR->(FIELDPOS("CR_NFMOBLQ")) > 0 //Guarda o motivo de bloqueio da NF
Local lBloqueio := .F.					

//Verifica o preenchimaneto da tes dos itens devido a importacao do pedido de compras
If l103Class 
	DbSelectArea("SD1")
	DbSetOrder(1)
	MsSeek(xFilial("SD1") + cKeySF1)

	//-- Vari·veis de controle para ativar o bloqueio dependendo do cen·rio de classificaÁ„o da NF
	lExistSCR1 := MtExistSCR("NF", cKeySF1, .F.) //-- Controla se existe SCR nao deletada para cen·rios de classificaÁ„o de NF que teve alteraÁıes na Guarda Fiscal
	lExistSCR2 := MtExistSCR("NF", cKeySF1, .T.) //-- Controla se existe SCR deletada para cen·rios de reclassificaÁ„o de NF pÛs estorno
	lLibSCROk  := MtGLastSCR("NF", cKeySF1) //-- Controla se o documento encontra-se totalmente liberado na SCR, para cen·rios da Guarda Fiscal
	nCRTotal   := GetAdvFval("SCR", "CR_TOTAL", xFilial("SCR") + "NF" + cKeySF1, 1, 0, .T.) //-- ObtÈm o total do documento na SCR para comparar com o total da SF1 e validar cen·rios de classificaÁ„o de NF que teve alteraÁıes na Guarda Fiscal
	nF1ValBrut := SF1->F1_VALBRUT //-- ObtÈm total do documento na SF1 para comparar com o total da SCR e validar cen·rios de classificaÁ„o de NF que teve alteraÁıes na Guarda Fiscal
EndIf

If ( l103Class .And. Empty(SD1->D1_TESACLA) .And. Empty(SD1->D1_TEC) );
   .Or. ( lRestCla .And. l103Class .And. SF1->F1_STATUS == "B" .And. (!Empty(SD1->D1_TESACLA) .Or. !Empty(SD1->D1_TEC)));
   .Or. ( lRestCla .And. l103Class .And. SF1->F1_STATUS == "C" .And. (!Empty(SD1->D1_TESACLA) .Or. !Empty(SD1->D1_TEC)) .And. mv_par17 == 2);   
   .Or. !l103Class;
   .Or. ( l103Class .And. AllTrim(SD1->D1_ORIGEM) == "GF");
   .Or. ( l103Class .And. lExistSCR2 )
	For nX :=1 To Len(aCols)
		If !aCols[nx][nUsado+1]
			If !Empty(aCols[nx][nPosPc])
				If l103Class
					lVerifica := .T.
					If lRestCla .And. SF1->F1_STATUS == "B"
						lVerifica:= .F.
						Exit
					EndIf
					DbSelectArea("SD1")
					DbSetOrder(1)
					MsSeek(cFilSD1 + cKeySF1 + aCols[nx][nPosCod]+aCols[nx][nPosItem])
					
					//-- Para cen·rios que n„o sejam da guarda fiscal, deve-se comparar se houve alteraÁ„o de quantidade e/ou valor durante a classificaÁ„o da NF (aCols x SD1)
					If Empty(SF1->F1_STATUS) .And. SD1->D1_QUANT == aCols[nx][nPosQtd] .And. SD1->D1_VUNIT == aCols[nx][nPosVlr] .And. AllTrim(SD1->D1_ORIGEM) <> "GF"
						lVerifica:= .F.
					EndIf
					
					//-- Para cen·rios da guarda fiscal, n„o verificar bloqueio se, e somente se, existir SCR totalmente liberada e o valor da SF1 estiver menor ou igual que o valor liberado na SCR
					If lVerifica .And. AllTrim(SD1->D1_ORIGEM) == "GF" .And. lExistSCR1 .And. lLibSCROk .And. (nF1ValBrut <= nCRTotal .Or. nCRTotal == 0)
						lVerifica := .F.
					EndIf
				EndIf

			    If !lVerifica .And. lMT103NBL
        			lVerifica := ExecBlock("MT103NBL",.F.,.F.,{})
		        EndIf

				If lVerifica
					DbSelectArea("SC7")
					DbSetOrder(19)
					If !Empty(aCols[nx][nPosPc]+aCols[nx][nPosItPc]) .And. MsSeek(cFilEntC7+aCols[nx][nPosCod]+aCols[nx][nPosPc]+aCols[nx][nPosItPc])
						nQuJE := SC7->C7_QUJE
						nQaCl := SC7->C7_QTDACLA
						nQtde := SC7->C7_QUANT

						aSldItem := {}
						GCPSldItem("2",aSldItem)
						If	!Empty(aSldItem)
							nQuJE := aSldItem[1]
							nQaCl := aSldItem[2]
							nQtde := aSldItem[3]
						EndIf

						nQtdItem	:= aCols[nx][nPosQtd]
						nVlrItem	:= aCols[nx][nPosVlr]
						nDescItem	:= aCols[nx][nPosDesc]
						cItAux 	    := aCols[nx][nPosItem]

						//Verifica se item do PC foi quebrado em mais de um item no doc de entrada.
						For nY := 1 To Len(aCols)
							If !(cItAux == aCols[nY][nPosItem]) .And. aCols[nY][nPosCod] == aCols[nx][nPosCod] .And. aCols[nY][nPosItPc] == aCols[nx][nPosItPc] .And. aCols[nY][nPosPc] == aCols[nX][nPosPc]
								nVlrItem	:= (((aCols[nY][nPosVlr]*aCols[nY][nPosQtd])+(nVlrItem*nQtdItem))/(nQtdItem+aCols[nY][nPosQtd]))
								nQtdItem	+= aCols[nY][nPosQtd]
								nDescItem	+= aCols[nY][nPosDesc]
							EndIf
						Next nY

						If lDescTol
							nDescItem 	:= nDescItem/nQtdItem
							nVlrItem	:= nVlrItem - nDescItem
						EndIf
						nDescSC7 := 0
						If lPcDescTol
							nDescSC7	:= SC7->C7_VLDESC								 
						Endif
	
						//-- Avalia quebra de 1 item de PC em N itens do Doc. de Entrada vindo de Guarda Fiscal ou PrÈ-Nota
						nQtAux := 0
						If l103Class
							aAreaAux := SD1->(GetArea())
							SD1->(DbGoTop())
							DbSelectArea("SD1")
							DbSetOrder(1)
							MsSeek(cFilSD1 + cKeySF1)
							While SD1->(!EOF()) .And.;
								  cFilSD1 == SD1->D1_FILIAL .And.;
								  (SD1->D1_DOC + SD1->D1_SERIE + SD1->D1_FORNECE + SD1->D1_LOJA == aCols[nX][nPosDoc] + aCols[nX][nPosSerie] + aCols[nX][nPosForn] + aCols[nX][nPosLjFor])
								//-- Valida cada item
								If SD1->D1_COD == aCols[nX][nPosCod] .And. SD1->D1_PEDIDO == aCols[nX][nPosPc] .And. SD1->D1_ITEMPC == aCols[nX][nPosItPc]
									nQtAux += SD1->D1_QUANT //-- Obtem quantidade que j· estava gravada na SD1 para ser avaliada com a quantidade definida no aCols (nQtdItens)
								EndIf
								SD1->(DbSkip())
							EndDo
							RestArea(aAreaAux)
						EndIf

						lRet := MaAvalToler(SC7->C7_FORNECE,SC7->C7_LOJA,SC7->C7_PRODUTO, (nQtdItem+nQuJE+nQaCl) - nQtAux,nQtde,nVlrItem,xMoeda(SC7->C7_PRECO-nDescSC7,SC7->C7_MOEDA,,M->dDEmissao,nDecimalPC,SC7->C7_TXMOEDA,))[1]

						If lRet
							lBloqueio := .T.

							if !lNfMotBloq//Se o campo na SCR existe, dever· avaliar bloqueio em todos os itens
								Exit
							endif
						EndIf
					EndIf
				EndIf
			EndIf
		EndIf
	Next nX

	if lBloqueio .and. lNfMotBloq
		lRet := lBloqueio
	endif
EndIf

If ExistBlock("A103BLOQ")
	lRet:= ExecBlock("A103BLOQ",.F.,.F.,{lRet})
Endif

RestArea(aAreaSC7)
RestArea(aArea)

FwFreeArray(aAreaSC7)
FwFreeArray(aArea)
FwFreeArray(aAreaAux)
FwFreeArray(aSldItem)

Return ( lRet )

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103ValSD4≥ Autor ≥Alexandre Inacio Lemes ≥ Data ≥07/04/2005≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Verifica a existencia de empenhos                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ Nenhum                                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ/*/
Function A103ValSD4(nItem)

Local aArea		:= GetArea()
Local nPosCod	:= GetPosSD1("D1_COD")
Local nPosQuant	:= GetPosSD1("D1_QUANT")
Local nPosOp	:= GetPosSD1("D1_OP")
Local nPosOrdem	:= GetPosSD1("D1_ORDEM")
Local cAlerta	:= ""
Local cProduto	:= ""
Local lRetorno	:= .F.
Local lValida	:= .T.
Local lPyme		:= If( Type( "__lPyme" ) <> "U", __lPyme, .F. )
Local nQuantD4  := 0
Local l410Remb  := Existblock("M410REMB")

//PARAMETRO MV_NFESD4: (V)isualizar / (S)im / (N)ao
//VV - Sempre mostra janela de confirmacao (Default)
//SV - Quando o produto nao faz parte do empenho da OP
//     confirmar item.
//NV - Quando o produto nao faz parte do empenho da OP
//     nao confirmar item.
//VS - Quando a qtde empenhada e menor que qtde do item
//	   confirmar movimentacao.
//VN - Quando a qtde empenhada e menor que qtde do item
//     nao confirmar movimentacao.
Local cNfeSD4	:= Upper(SuperGetMv("MV_NFESD4",.T.,"VV"))

//Verifica se existe empenho
If !Empty(aCols[nItem][nPosOp])

	DbSelectArea("SD4")
	DbSetOrder(1)
	If !dbSeek(xFilial("SD4")+aCols[nItem][nPosCod]+aCols[nItem][nPosOp])
		//P.E. que permite ativar ou nao a checagem da estrutura do produto.
		If ExistBlock("A103VSG1")
			lValida:=ExecBlock("A103VSG1",.f.,.f.)
			If Valtype(lValida) # "L"
				lValida:=.T.
			EndIf
		EndIf
		If lValida
			DbSelectArea("SC2")
			DbSetOrder(1)
			If dbSeek(xFilial("SC2")+aCols[nItem][nPosOp])
				cProduto:=SC2->C2_PRODUTO
			EndIf
			DbSelectArea("SG1")
			DbSetOrder(2)
			If (!DbSeek(xFilial("SG1")+aCols[nItem][nPosCod]+cProduto)) .And.  (IIF(nPosOrdem >0 .And. !lPyme,Empty(aCols[nItem][nPosOrdem]),.T.) .AND. !("OS001" $ aCols[nItem][nPosOp]))
				If SubsTr(cNfeSD4,1,1) $ " V"
					cAlerta := OemToAnsi(STR0174)+chr(13)		                  //"O produto digitado nÑo faz parte da"
					cAlerta += OemToAnsi(STR0175+cProduto)+chr(13)	              //"Estrutura do Produto "
					cAlerta += OemToAnsi(STR0176+ aCols[nItem][nPosOp] )+chr(13)//"da OP - "
					cAlerta += OemToAnsi(STR0177)+chr(13)		 	              //"Confirma movimentaáÑo ?"
					If MsgYesNo(cAlerta,OemToAnsi(STR0178))			              //"ATENCAO"
						lRetorno :=.T.
					EndIf
				Else
					If SubsTr(cNfeSD4,1,1) == "S"
						lRetorno := .T.
					ElseIf SubsTr(cNfeSD4,1,1) == "N"
						cAlerta := OemToAnsi(STR0174)+chr(13)		        	//"O produto digitado nao faz parte da"
						cAlerta += OemToAnsi(STR0175+cProduto)+chr(13)	    	//"Estrutura do Produto "
						cAlerta += OemToAnsi(STR0176+ aCols[nItem][nPosOp])	//"da OP - "
						Aviso(OemToAnsi(STR0178),cAlerta,{STR0461})
						lRetorno := .F.
					EndIf
				EndIf
			Else
				lRetorno :=.T.
			EndIf
			DbSelectArea("SG1")
			DbSetOrder(1)
		Else
			lRetorno := .T.
		EndIf
	Else
		While !EOF() .And. AllTrim(SD4->(D4_FILIAL+D4_COD+D4_OP)) == AllTrim(xFilial("SD4")+aCols[nItem][nPosCod]+aCols[nItem][nPosOp])
			nQuantD4 += SD4->D4_QUANT

			SD4->(dbSkip())
		End
		If nQuantD4 < aCols[nItem][nPosQuant] .And. Posicione("SB1",1,xFilial("SB1")+aCols[nItem][nPosCod],"B1_TIPO") # "BN"
			If l410Remb .And. dbSeek(xFilial("SD4")+aCols[nItem][nPosCod]+aCols[nItem][nPosOp])
				lRetorno = .T.
			Else 			
				If SubsTr(cNfeSD4,2,1) $ " V"
					cAlerta := OemToAnsi(STR0179+Transform(nQuantD4,PesqPict("SD1","D1_QUANT")))+chr(13) //"A quantidade empenhada"
					cAlerta += OemToAnsi(STR0180)+chr(13)														//"e menor que a quantidade do item"
					cAlerta += OemToAnsi(STR0177)+chr(13)														//"Confirma movimentaáÑo ?"
					If MsgYesNo(cAlerta,OemToAnsi(STR0178))														//"ATENCAO"
						lRetorno :=.T.
					EndIf
				ElseIf SubsTr(cNfeSD4,2,1) == "S"
					lRetorno := .T.
				ElseIf SubsTr(cNfeSD4,2,1) == "N"
					cAlerta := OemToAnsi(STR0179+Transform(nQuantD4,PesqPict("SD1","D1_QUANT")))+chr(13) //"A quantidade empenhada"
					cAlerta += OemToAnsi(STR0180)																//"e menor que a quantidade do item"
					Aviso(OemToAnsi(STR0178),cAlerta,{STR0461})
					lRetorno := .F.
				EndIf
			EndIf	

		Else
			lRetorno := .T.
		EndIf
	EndIf

EndIf

RestArea(aArea)
Return lRetorno

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥ A103Line  ≥ Autor ≥ Eduardo de Souza     ≥ Data ≥ 20/07/05 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Atualizacao da bLine do documento.                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103Line(ExpN1)                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpN1 - Posicao da linha no listbox                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ SIGATMS                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Function A103Line(nAT,aSF2)

Static oNoMarked := LoadBitmap( GetResources(),'LBNO'			)
Static oMarked	  := LoadBitmap( GetResources(),'LBOK'			)
Local abLine     := {}
Local nCnt       := 0

For nCnt := 1 To Len(aSF2[nAT])
	If nCnt == 1
		Aadd( abLine, Iif(aSF2[ nAT, nCnt ] , oMarked, oNoMarked ) )
	Else
		Aadd( abLine, aSF2[ nAT, nCnt ] )
	EndIf
Next nCnt

Return abLine

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103Conhec≥ Autor ≥Sergio Silveira        ≥ Data ≥15/08/2005≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Chamada da visualizacao do banco de conhecimento            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103Conhec()                                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥Nenhum                                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T.                                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥                                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103Conhec() 

Local aRotBack := AClone( aRotina )
Local nBack    := N

Private aRotina := {}

Aadd(aRotina,{STR0187,"MsDocument", 0 , 2}) //"Conhecimento"

MsDocument( "SF1", SF1->( Recno() ), 1 )

aRotina := AClone( aRotBack )
N := nBack

Return( .t. )

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥ FunáÖo    ≥ A103TrFil                                                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Autor     ≥ Rodrigo de Almeida Sartorio              ≥ Data ≥ 08/02/06 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ DescriáÖo ≥ Verifica se o movimento e de transferencia entre filiais   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros ≥cTes       Codigo da tes que esta sendo avaliada            ≥±±
±±≥           ≥cTipo      Tipo da nota que esta sendo avaliada             ≥±±
±±≥           ≥cClifor    Codigo do cliente/fornecedor avaliado            ≥±±
±±≥           ≥cLoja      Loja do cliente/fornecedor avaliado              ≥±±
±±≥           ≥cDoc       Documento avaliado                               ≥±±
±±≥           ≥cSerie     Serie do documento avaliado                      ≥±±
±±≥           ≥cCod       Codigo do produto do documento avaliado          ≥±±
±±≥           ≥nQuant     Quantidade do documento avaliado                 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥  Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103TrFil(cTes,cTipo,cCliFor,cLoja,cDoc,cSerie,cCod,nQuant,aItmSD2,cLote,cSubLote,lTrfil,cItem)

Local lRet       := .T.
Local cArqCliFor := ""
Local cAchoCli   := ""
Local cAchoLoja  := ""
Local cFilBack   := cFilAnt
Local cAliasAux  := ""
Local aArea      := GetArea()
Local aAreaSM0   := SM0->(GetArea())
Local lAchoCli   := .F.
Local lPoder3    := .F.
Local lUsaFilTrf := UsaFilTrf()
Local cCodFil    := ""
Local cCodFilOri := ""
Local cAchoFil   := ""
Local cIndex     := ""
Local cArqIdx    := ""
Local nIndex     := 0
Local lRastro    := ValType(cLote)=="C" .And. Rastro(cCod) .And. SuperGetMV("MV_TFVLDLT",.F.,.F.)
Local cItem2	 := ""

Default aItmSD2  := {}
Default lTrfil	 := .F.

If SF4->(MsSeek(xFilial("SF4")+cTes)) .And. SF4->F4_TRANFIL == "1"
	// Verifica se utiliza poder de terceiros
	lPoder3 := (SF4->F4_PODER3 $ "R|D")

	// Itens de nota fiscal de entrada
	If cTipo $ "DB"
		cArqCliFor:="SA2" // Cliente na nota fiscal de entrada fornecedor na nota de saida
		DbSelectArea("SA1")
		DbSetOrder(1)
		If MsSeek(xFilial("SA1")+cCliFor+cLoja)
			cCodFil := Iif(lUsaFilTrf, SA1->A1_FILTRF, SA1->A1_CGC)
		EndIf
	Else
   		cArqCliFor:="SA1" // Fornecedor na nota fiscal de entrada cliente na nota de saida
		DbSelectArea("SA2")
		DbSetOrder(1)
		If MsSeek(xFilial("SA2")+cCliFor+cLoja)
			cCodFil := Iif(lUsaFilTrf, SA2->A2_FILTRF, SA2->A2_CGC)
		EndIf
	EndIf
	
	// Checa se cliente / fornecedor esta configurado como filial do sistema
   	If !Empty(cCodFil) .And. !lPoder3
		DbSelectArea("SM0")
		dbSeek(cEmpAnt)
		Do While !Eof() .And. SM0->M0_CODIGO == cEmpAnt
			// Verifica codigo da filial caso encontre
			If (!lUsaFilTrf .And. SM0->M0_CGC == cCodFil) .Or. (lUsaFilTrf .And. Trim(SM0->M0_CODFIL) == Trim(cCodFil))
				cAchoFil := FWCodfil()
				Exit
			EndIf
			dbSkip()
		End
		RestArea(aAreaSM0)
		// Obtem filial da nota fiscal de entrada
		If SM0->M0_CODIGO+FWCodfil() == cEmpAnt+cFilAnt
			cCodFilOri := Iif(lUsaFilTrf, FWCodfil(), SM0->M0_CGC)
		Else
			dbSeek(cEmpAnt)
			Do While ! Eof() .And. SM0->M0_CODIGO == cEmpAnt
				// Verifica codigo da filial caso encontre CGC
				If FWCodfil() == cFilAnt
					cCodFilOri := Iif(lUsaFilTrf, FWCodfil(), SM0->M0_CGC)
					Exit
				EndIf
				dbSkip()
			End
			RestArea(aAreaSM0)
		EndIf
		// Caso achou procura documento na filial
		If !Empty(cAchoFil)
			// Muda para filial de saida do documento
			cFilAnt:=cAchoFil

			// Obtem codigo do cliente/fornecedor
			DbSelectArea(cArqCliFor)
			If lUsaFilTrf
				//-- Monta filtro e indice temporario na SA1 ou SA2 pelo campo FILTRF
				If cArqCliFor == "SA1"
					cIndex := "A1_FILIAL+A1_FILTRF"
				Else
					cIndex := "A2_FILIAL+A2_FILTRF"
				EndIf

				cArqIdx := CriaTrab(,.F.)
				IndRegua(cArqCliFor, cArqIdx, cIndex,,,STR0283) //"Selecionando Registros ..."
				nIndex := RetIndex(cArqCliFor)
				dbSetOrder(nIndex+1) // A1_FILIAL+A1_FILTRF ou A2_FILIAL+A2_FILTRF
			Else
				DbSetOrder(3)
			EndIf
			If dbSeek(xFilial(cArqClifor)+IIf(Type("l310PODER3") == "L" .And. l310PODER3, cCodFil, cCodFilOri))
				lAchoCli := CliForOrig(cArqClifor, @cAchoCli, @cAchoLoja, lUsaFilTrf)
				If lAchoCli
					// Pesquisa documento
					cItem2 := CodeSoma1(cItem,TamSX3("D2_ITEM")[1])
					
					cAliasAux := GetNextAlias()
					
					BeginSQL Alias cAliasAux
						SELECT 	SD2.D2_FILIAL,
								SD2.D2_COD,
								SD2.D2_QUANT,
								SD2.D2_PEDIDO,
								SD2.D2_ITEMPV,
								SD2.D2_LOTECTL
						FROM 	%Table:SD2% SD2
						WHERE 	SD2.D2_FILIAL 	 	= %xFilial:SD2% 
								AND SD2.D2_DOC 	 	= %Exp:cDoc% 
								AND SD2.D2_SERIE 	= %Exp:cSerie% 
								AND SD2.D2_ITEM  	= %Exp:cItem2% 
								AND SD2.D2_CLIENTE 	= %Exp:cAchoCli% 
								AND SD2.D2_LOJA 	= %Exp:cAchoLoja%
								AND SD2.%NotDel%
						ORDER 
						BY 		SD2.D2_ITEM, SD2.D2_COD
					EndSQL
					
					If !(cAliasAux)->(Eof()) .And. Iif(FindFunction("A310VldPrd"), A310VldPrd(cAchoFil, (cAliasAux)->D2_COD, cFilBack, cCod), (cAliasAux)->D2_COD == cCod)
						If QtdComp(nQuant) <> QtdComp((cAliasAux)->D2_QUANT)
							lRet := .F.
							//≥ Ponto de entrada para nao validar Qtde divergente SD1 x SD2  ≥
							If ExistBlock("A103VLQT")
								lRet := ExecBlock("A103VLQT",.F.,.F.,{lRet})
								If ValType(lRet) <> "L"
									lRet := .F.
								EndIf
							EndIf
							If !lRet
								Aviso(STR0119,STR0507,{STR0461},1) //"A quantidade do Item est· divergente da informada no Documento de SaÌda"
							EndIf
						Else
							lRet := .F.
							lTrfil := .F.

							While !(cAliasAux)->(Eof())
								If !lRastro .Or. (cAliasAux)->D2_LOTECTL == cLote
									AADD(aItmSD2,{"D2_FILIAL", (cAliasAux)->D2_FILIAL})
									AADD(aItmSD2,{"D2_PEDIDO", (cAliasAux)->D2_PEDIDO})
									AADD(aItmSD2,{"D2_ITEMPV", (cAliasAux)->D2_ITEMPV})
									lRet := .T.
									lTrfil := .T.
									Exit
								EndIf
								(cAliasAux)->(DbSkip())
							End
							If lRet
								//≥ Ponto de entrada para nao validar Qtde divergente SD1 x SD2  ≥
								If ExistBlock("A103VLQT")
									lRet := ExecBlock("A103VLQT",.F.,.F.,{lRet})
									If ValType(lRet) <> "L"
										lRet := .F.
										lTrfil := .F.
									EndIf
								EndIf
								If !lRet
									Aviso(STR0119,STR0199,{STR0461},1)
								EndIf
							Else
								Aviso(STR0119,STR0200,{STR0461},1) //O documento n„o foi encontrado na filial de origem ou a ordem do Item est· divergente da informada no Documento de SaÌda
							EndIf
						EndIf
					Else
						lRet := .F.
						lTrfil := .F.
						Aviso(STR0119,STR0200,{STR0461},1) //O documento n„o foi encontrado na filial de origem ou a ordem do Item est· divergente da informada no Documento de SaÌda
					EndIf
					(cAliasAux)->(DbCloseArea())
				Else
					lRet := .F.
					lTrfil := .F.
					Aviso(STR0119,STR0200,{STR0461},1) //O documento n„o foi encontrado na filial de origem ou a ordem do Item est· divergente da informada no Documento de SaÌda
				EndIf
			Else
				lRet := .F.
				lTrfil := .F.
				Aviso(STR0119,STR0201,{STR0461},1)
			EndIf
			
			If lUsaFilTrf
				dbSelectArea(cArqCliFor)
				RetIndex(cArqCliFor)
				Ferase(cArqIdx + OrdBagExt())
			EndIf				
		Else
			lRet := .F.
			lTrfil := .F.
			Aviso(STR0119,STR0203,{STR0461},1)
		EndIf
	ElseIf !lPoder3
		lRet := .F.
		lTrfil := .F.
		Aviso(STR0119,STR0202,{STR0461},1)
	EndIf
EndIf

RestArea(aArea)

cFilAnt := cFilBack

Return lRet

/*/{Protheus.doc} A103AtuSRK
Rotina de integracao com a folha de pagamento

@param	ExpN1: Codigo da operaÁ„o
				[1] Inclusao de Verba
				[2] Exclusao de Verba
		ExpA2: Header das duplicatas
		ExpA3: aCols das duplicatas
@author Eduardo Riera
@since 14.03.2006
/*/

Function A103AtuSRK(nOpcA,aHeadSE2,aColsse2)
Return A103SRKGPE(nOpcA,aHeadSE2,aColsSE2)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥ FunáÖo    ≥ A103AtuCauc( )                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Autor     ≥ Sergio Silveira                          ≥ Data ≥ 08/02/06 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ DescriáÖo ≥ Atualiza a movimentacao de caucao                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Sintaxe   ≥A103AtuCauc(ExpN1,ExpA2,ExpA3,ExpC4,ExpC5,ExpC6,ExpC7,ExpC8,≥±±
±±≥           ≥ ExpN9 )                                                    ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros ≥ExpN1 -> Codigo da operacao : 1 - Inclusao / 2 - Exclusao   ≥±±
±±≥           ≥ExpA2 -> Contratos do documento fiscal                      ≥±±
±±≥           ≥ExpA3 -> Array com os recnos dos titulos gerados            ≥±±
±±≥           ≥ExpC4 -> Codigo do fornecedor                               ≥±±
±±≥           ≥ExpC5 -> Loja do fornecedor                                 ≥±±
±±≥           ≥ExpC6 -> Numero da NF                                       ≥±±
±±≥           ≥ExpC7 -> Serie Real da NF                                   ≥±±
±±≥           ≥ExpC8 -> Data de emissao                                    ≥±±
±±≥           ≥ExpN9 -> Valor bruto da NF                                  ≥±±
±±≥           ≥ExpC10-> Serie Id de Controle para gravar a CNI herdada SF1 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥  Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Function A103AtuCauc( nOper, aContratos, aRecGerSE2, cFornece, cLoja, cNFiscal, cSerie, dDEmissao, nValBrut,cSerieIdSF1 )

Local aArea	:= GetArea()
Local nLoop := 0

//Efetua o processamento apenas se gerar titulos

If !Empty( aRecGerSE2 )
	//Varre os contratos da NF de entrada
	For nLoop := 1 to Len( aContratos )
		//Gera os abatimentos das caucoes
		CtaAbatCauc( nOper, aContratos[ nLoop ], aRecGerSE2, cFornece, cLoja, cNFiscal, cSerie, dDEmissao, nValBrut, cSerieIdSF1 )
	Next nLoop
EndIf

RestArea(aArea)

Return( Nil )

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥ FunáÖo    ≥ A103GetContr( )                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Autor     ≥ Sergio Silveira                          ≥ Data ≥ 08/02/06 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ DescriáÖo ≥ Obtem os contratos de uma nota ( grupo de SD1 )            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Sintaxe   ≥ A103GetContr( ExpA1, ExpA2 )                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros ≥ExpA1 -> Array contendo os recnos do SD1                    ≥±±
±±≥           ≥ExpA2 -> Array com os codigos dos contratos                 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥  Uso      ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Function A103GetContr( aRecSD1, aContratos )

Local nLoop := 0
Local cFilCTR := ""

For nLoop := 1 To Len( aRecSD1 )

	SD1->( dbGoto( aRecSD1[ nLoop,1 ] ) )
	//Pedido de Compra
	If !Empty(SD1->D1_PEDIDO)
		nRecC7 := A103RECC7(xFilial("SC7"),SD1->D1_PEDIDO,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD,SD1->D1_ITEMPC)
		SC7->(DbGoTo(nRecC7))
		If nRecC7 > 0
			//Armazena os contratos desta NF ( gestao de contratos )
			If Empty( AScan( aContratos, {|x| x[1] == SC7->C7_CONTRA .And. x[2] == SC7->C7_CONTREV } ) )
				cFilCTR := CNTBuscFil(xFilial('CND'), SC7->C7_MEDICAO)
				AAdd( aContratos, { SC7->C7_CONTRA, SC7->C7_CONTREV,{}, cFilCTR } )
			EndIf
		EndIf
	EndIf
Next nLoop

Return( nil )

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103Multas≥ Autor ≥ Sergio Silveira       ≥ Data ≥11/04/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descricao ≥Selecao e aplicacao de multas do modulo SIGAGCT              ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103Multas( ExpD1, ExpC2, ExpC3, ExpA4 )                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpD1 -> Data de emissao                                    ≥±±
±±≥          ≥ ExpC2 -> Codigo do fornecedor                               ≥±±
±±≥          ≥ ExpC3 -> Loja do fornecedor                                 ≥±±
±±≥          ≥ ExpA4 -> Array de multas do documento de entrada            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ .T.                                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103Multas(dDEmissao,cA100For,cLoja,aMultas)

Local aArea      := GetArea()
Local aAreaCN9	 := CN9->(GetArea())
Local aAreaCNA	 := CNA->(GetArea())
Local cTpMulta	 := ""
Local aListBox   := {}
Local aContratos := {}
Local aMedicoes  := {}
Local bSavSetKey := SetKey(VK_F4,Nil)
Local bSavKeyF5  := SetKey(VK_F5,Nil)
Local bSavKeyF6  := SetKey(VK_F6,Nil)
Local bSavKeyF7  := SetKey(VK_F7,Nil)
Local bSavKeyF8  := SetKey(VK_F8,Nil)
Local bSavKeyF9  := SetKey(VK_F9,Nil)
Local bSavKeyF10 := SetKey(VK_F10,Nil)
Local bSavKeyF11 := SetKey(VK_F11,Nil)
Local nOpca      := 0
Local nLoop      := 0
Local nPosPedido := GetPosSD1( "D1_PEDIDO" )
Local nPosItem   := GetPosSD1( "D1_ITEMPC" )
Local oOk        := LoadBitmap( GetResources(), "LBOK" )
Local oNOk       := LoadBitmap( GetResources(), "LBNO" )
Local oDlgMult 
Local oList
Local oBold
Local oBmp
Local oBut2

SC7->( DbSetOrder( 1 ) )
CN9->( dbSetOrder( 1 ) )

For nLoop := 1 to Len( aCols )
	If !ATail( aCols[ nLoop ] )
		If SC7->( MsSeek( xFilial( "SC7" ) + aCols[ nLoop, nPosPedido ] + aCols[ nLoop, nPosItem ] ) )
			//Alimenta o array de medicoes / item desta NF
			If !Empty( SC7->C7_CONTRA ) .And. !Empty( SC7->C7_PLANILH )

				If CN9->( MsSeek( xFilial("CN9") + SC7->C7_CONTRA + SC7->C7_CONTREV ) )
					cTpMulta := CN300RetSt("TPMULT",0,SC7->C7_PLANILH)
					If AllTrim(cTpMulta) == "1" 
						If Empty( AScan( aMedicoes, { |x| x[1] == SC7->C7_CONTRA .And. x[2] == SC7->C7_CONTREV .And. ;
								x[3] == SC7->C7_PLANILH .And. x[4] == SC7->C7_MEDICAO .And. x[5] == SC7->C7_ITEMED } ) )
							AAdd( aMedicoes, { SC7->C7_CONTRA, SC7->C7_CONTREV, SC7->C7_PLANILH, SC7->C7_MEDICAO, SC7->C7_ITEMED } )
						EndIf

						If Empty( AScan( aContratos, SC7->C7_CONTRA ) )
							AAdd( aContratos, SC7->C7_CONTRA )
						EndIf
					Endif
				Endif
			EndIf
		EndIf
	EndIf

Next nLoop

If !Empty( aMedicoes ) .Or. !Empty( aMultas )

	If Empty( aMultas )
		//Processa as multas
		A103ProcMul( aMedicoes, @aListBox )
	Else
		//Carrega as multas do array
		AEval( aMultas, { |x| AAdd( aListBox,  { .T., x[1], x[2], x[3], x[4], x[5] } ) } )
	EndIf

	If Empty( aListBox )
		//Se estiver vazio, preenche uma linha em branco
		AAdd( aListBox, { .F., "", "", 0, 0, "" } )
	EndIf

	DEFINE MSDIALOG oDlgMult TITLE STR0226 FROM 0,0 TO 400, 700 OF oMainWnd PIXEL // "Selecao de multas"

	DEFINE FONT oBold NAME "Arial" SIZE 0, -13 BOLD

	@  0, -25 BITMAP oBmp RESNAME "PROJETOAP" oF oDlgMult SIZE 55, 1000 NOBORDER WHEN .F. PIXEL

	@ 03, 40 SAY STR0227 FONT oBold PIXEL // "Selecao de multas aplicadas ao documento de entrada"

	@ 14, 30 TO 16 ,400 LABEL '' OF oDlgMult PIXEL

	@ 24, 223 BUTTON STR0228   SIZE 35,11 ACTION A103RepMult( oList, @aListBox, aMedicoes ) OF oDlgMult PIXEL //"Reprocessar"
	@ 24, 265 BUTTON STR0251   SIZE 35,11 ACTION A103AltMul( oList, @aListBox, aContratos, aMedicoes ) OF oDlgMult PIXEL // "Alterar"
	@ 24, 307 BUTTON STR0229   SIZE 35,11 ACTION A103AdMult( oList, @aListBox, aContratos, aMedicoes ) OF oDlgMult PIXEL // "Adicionar"

	oList := TWBrowse():New( 43, 40, 303, 125,,{ "", "Tipo", STR0230, STR0231, STR0232,STR0233 },,oDlgMult,,,,,,,,,,,,.F.,,.T.,,.F.,,,) // "Tipo", "Contrato", "Descricao", "Valor","Insercao"

	oList:SetArray(aListBox)
	oList:bLine := { || { If( aListBox[oList:nAT,1], oOk, oNOK ), If( aListBox[oList:nAt,6] == "1", "Multa    ","Bonificacao" ), aListBox[oList:nAT,2], aListBox[oList:nAT,3], Transform( aListBox[oList:nAT,4],"@E 999,999,999.99" ), If( aListBox[oList:nAT,5] == 1,STR0234,If( aListBox[oList:nAT,5] == 2,STR0235,"" ) ) } } // "Automatica",	"Manual"
	oList:bLDblClick := { || aListBox[oList:nAt,1] := If( Empty( aListBox[ oList:nAt,2 ]), aListBox[oList:nAt,1],!aListBox[oList:nAt,1] ) }

	DEFINE SBUTTON oBut2 FROM 178, 280 TYPE 1 ACTION ( nOpca := 1, oDlgMult:End() )  ENABLE of oDlgMult
	DEFINE SBUTTON oBut3 FROM 178, 312 TYPE 2 ACTION ( nOpca := 0, oDlgMult:End() )  ENABLE of oDlgMult

	ACTIVATE MSDIALOG oDlgMult CENTERED

	If nOpca == 1

		//Carrega as multas no array aMultas
		aMultas := {}

		For nLoop := 1 to Len( aListBox )

			If aListBox[ nLoop, 1 ]
				AAdd( aMultas, { aListBox[nLoop,2],aListBox[nLoop,3], aListBox[nLoop,4], aListBox[nLoop,5], aListBox[nLoop,6] } )
			EndIf

		Next nLoop

	EndIf

Else
	Aviso( STR0236, STR0237, { STR0238 }, 2 ) // "Atencao !", "Nao existem contratos vinculados a este documento de entrada.", "Ok"
EndIf

//Restaura a integridade dos dados de entrada
SetKey(VK_F4,bSavSetKey)
SetKey(VK_F5,bSavKeyF5)
SetKey(VK_F6,bSavKeyF6)
SetKey(VK_F7,bSavKeyF7)
SetKey(VK_F8,bSavKeyF8)
SetKey(VK_F9,bSavKeyF9)
SetKey(VK_F10,bSavKeyF10)
SetKey(VK_F11,bSavKeyF11)

RestArea( aAreaCN9 )
RestArea( aAreaCNA )
RestArea( aArea )

Return( .T. )

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103AdMult≥ Autor ≥ Sergio Silveira       ≥ Data ≥11/04/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥ Inclusao de multa avulsa - SIGAGCT                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpO1 -> Objeto listbox                                     ≥±±
±±≥          ≥ ExpA2 -> Array da listbox ( alimentado por referencia )     ≥±±
±±≥          ≥ ExpA3 -> Array de contratos do documento de entrada         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ .T.                                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103AdMult( oList, aListBox, aContr, aMedicoes )

Local cDescri   := Space( 50 )
Local cContrato := ""
Local nValor    := 0
Local nOpca     := 0
Local oBut1
Local oBut2
Local oBmp
Local oBold
Local oDlgMult
Local oTipo
Local oContrato

aTipos := { STR0256, STR0257 } // "Multa", "Bonificacao"

DEFINE MSDIALOG oDlgMult TITLE STR0239 FROM 0,0 TO 340, 550 OF oMainWnd PIXEL // "Inclusao de multas"

DEFINE FONT oBold NAME "Arial" SIZE 0, -13 BOLD

@  0, -25 BITMAP oBmp RESNAME "PROJETOAP" oF oDlgMult SIZE 55, 1000 NOBORDER WHEN .F. PIXEL

@ 03, 40 SAY STR0240 FONT oBold PIXEL // "Inclusao de multas avulsas"

@ 14, 30 TO 16 ,400 LABEL '' OF oDlgMult   PIXEL

@  30, 40 SAY STR0241 OF oDlgMult PIXEL // "Contrato"
@  40, 40 MSCOMBOBOX oContrato VAR cContrato ITEMS aContr SIZE 100, 36 OF oDlgMult PIXEL

@  60, 40 SAY STR0242 OF oDlgMult PIXEL // "Descricao"
@  70, 40 GET cDescri SIZE 200, 11 VALID NaoVazio( cDescri ) PICTURE "@!" OF oDlgMult PIXEL

@  90, 40 SAY STR0243 OF oDlgMult PIXEL // "Valor"
@ 100, 40 GET nValor SIZE 70, 11   VALID NaoVazio( nValor ) .And. Positivo( nValor ) PICTURE "@E 999,999,999.99" OF oDlgMult PIXEL

@  120, 40 SAY STR0258 OF oDlgMult PIXEL // "Tipo"
@  130, 40 MSCOMBOBOX oTipo VAR cTipo ITEMS aTipos SIZE 100, 36 OF oDlgMult PIXEL

DEFINE SBUTTON oBut1 FROM 150, 207 TYPE 1 ACTION ( If( A103VldMult( cDescri,nValor,cContrato, Str(oTipo:nAt,1), aMedicoes ),( nOpca := 1, cTipo := Str(oTipo:nAt,1) , oDlgMult:End()), ) )  ENABLE of oDlgMult
DEFINE SBUTTON oBut2 FROM 150, 239 TYPE 2 ACTION ( nOpca := 0, oDlgMult:End() )  ENABLE of oDlgMult

ACTIVATE MSDIALOG oDlgMult CENTERED

If nOpca == 1
	If Len( aListBox ) == 1 .And. Empty( aListBox[ 1, 2 ] )
		//Se tiver uma linha em branco, apaga
		aListBox := {}
	EndIf
	AAdd( aListBox, { .T., cContrato, cDescri, nValor, 2, cTipo } )

	bLine := oList:bLine
	oList:SetArray(aListBox)
	oList:bLine := bLine
EndIf

Return( .T. )

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103AltMul≥ Autor ≥ Sergio Silveira       ≥ Data ≥05/05/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥ Alterecao de multa - SIGAGCT                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpO1 -> Objeto listbox                                     ≥±±
±±≥          ≥ ExpA2 -> Array da listbox ( alimentado por referencia )     ≥±±
±±≥          ≥ ExpA3 -> Array de contratos do documento de entrada         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ .T.                                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103AltMul( oList, aListBox, aContr, aMedicoes )

Local cDescri   := Space( 50 )
Local cContrato := ""
Local cTipo     := ""
Local nValor    := 0
Local nOpca     := 0
Local oBut1
Local oBut2
Local oBmp
Local oBold
Local oDlgMult
Local oContrato

If !( Len( aListBox ) == 1 .And. Empty( aListBox[ 1, 2 ] ) )

	cContrato := aListBox[ oList:nAt, 2 ]
	cDescri   := aListBox[ oList:nAt, 3 ]
	nValor    := aListBox[ oList:nAt, 4 ]
	cTipo     := aListBox[ oList:nAt, 6 ]

	DEFINE MSDIALOG oDlgMult TITLE STR0252 FROM 0,0 TO 300, 550 OF oMainWnd PIXEL // "Alteracao de multas"

	DEFINE FONT oBold NAME "Arial" SIZE 0, -13 BOLD

	@  0, -25 BITMAP oBmp RESNAME "PROJETOAP" oF oDlgMult SIZE 55, 1000 NOBORDER WHEN .F. PIXEL

	@ 03, 40 SAY STR0252 FONT oBold PIXEL //"Alteracao de multas"

	@ 14, 30 TO 16 ,400 LABEL '' OF oDlgMult   PIXEL

	@  30, 40 SAY STR0241 OF oDlgMult PIXEL // "Contrato"
	@  40, 40 MSCOMBOBOX oContrato VAR cContrato ITEMS aContr SIZE 100, 36 OF oDlgMult PIXEL

	@  60, 40 SAY STR0242 OF oDlgMult PIXEL // "Descricao"
	@  70, 40 GET cDescri SIZE 200, 11 VALID NaoVazio( cDescri ) PICTURE "@!" OF oDlgMult PIXEL

	@  90, 40 SAY STR0243 OF oDlgMult PIXEL // "Valor"
	@ 100, 40 GET nValor SIZE 70, 11   VALID NaoVazio( nValor ) .And. Positivo( nValor ) PICTURE "@E 999,999,999.99" OF oDlgMult PIXEL

	DEFINE SBUTTON oBut1 FROM 130, 207 TYPE 1 ACTION ( If( A103VldMult( cDescri,nValor,cContrato, cTipo, aMedicoes ),( nOpca := 1, oDlgMult:End()), ) )  ENABLE of oDlgMult
	DEFINE SBUTTON oBut2 FROM 130, 239 TYPE 2 ACTION ( nOpca := 0, oDlgMult:End() )  ENABLE of oDlgMult

	ACTIVATE MSDIALOG oDlgMult CENTERED

	If nOpca == 1

		aListBox[ oList:nAt, 2 ] := cContrato
		aListBox[ oList:nAt, 3 ] := cDescri
		aListBox[ oList:nAt, 4 ] := nValor

		bLine := oList:bLine
		oList:SetArray(aListBox)
		oList:bLine := bLine

	EndIf

Else

	Aviso( STR0236, STR0253, { STR0238 } ) // "Atencao", "Este item nao pode ser alterado !", "Ok"

EndIf

Return( .T. )

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103VldMult≥ Autor ≥ Sergio Silveira      ≥ Data ≥11/04/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descricao ≥Validacao dos campos de descricao e valor - Inclusao de multa≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ExpL1 :=  A103VldMult( ExpC2, ExpN3 )                        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpC2 -> Descricao da multa                                 ≥±±
±±≥          ≥ ExpN3 -> Valor da multa                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ ExpL1 -> Validacao                                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103VldMult( cDescri, nValor, cContrato, cTipo, aMedicoes )

Local cMulMan  := ""
Local lRet     := !Empty( cDescri )
Local cRev := ""
Local nPosMed := 0

If lRet
	lRet := !Empty( nValor )
EndIf

If !lRet
	Help( " ", 1, "NVAZIO" )
EndIf

If lRet
	//Verifica se permite a inclusao ou alteracao manual deste movimento
	nPosMed := aScan( aMedicoes, { |x| x[1] == cContrato } )

	//Verifica se permite multas no recebimento
	If nPosMed = 0
		lRet := .F.
		Aviso( STR0236, STR0259, { STR0238 }, 2 ) // "Atencao!", "Nao sao permitidas inclusoes ou alteracoes em multas ou bonificacoes deste contrato no recebimento !","Ok"
	Else
		lRet := .T.
	EndIf

	If lRet
		CN9->( DbSetOrder( 1 ) )
		If CN9->( MsSeek( xFilial( "CN9" ) + cContrato + cRev ) )

			cMulMan := CN300RetSt("MULMAN", 0, aMedicoes[nPosMed][3] )

			// cMulMan := CN1->CN1_MULMAN

				Do Case
				Case cMulMan == "1"
					//Nao permite alteracoes manuais
					lRet := .F.
					Aviso( STR0236, STR0260, { STR0238 }, 2 ) // "Atencao!", "Nao sao permitidas inclusoes ou alteracoes em multas ou bonificacoes deste contrato !","Ok"
				Case cMulMan == "2"
					//Permite apenas multas
					If cTipo == "1"
						lRet := .T.
					Else
						lRet := .F.
						Aviso( STR0236, STR0261, { STR0238 }, 2 ) // "Atencao!", "Nao sao permitidas inclusoes ou alteracoes em bonificacoes deste contrato !", "Ok"
					EndIf

				Case cMulMan == "3"
					//Permite apenas bonificacoes
					
					If cTipo == "2"
						lRet := .T.
					Else
						lRet := .F.
						Aviso( STR0236, STR0262, {STR0238}, 2 ) // "Atencao!", "Nao sao permitidas inclusoes ou alteracoes em multas deste contrato !", "Ok"
					EndIf

				Case cMulMan == "4"
					lRet := .T.
				EndCase
		Endif
	EndIf
EndIf

Return( lRet )

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103RepMult≥ Autor ≥ Sergio Silveira      ≥ Data ≥11/04/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpO1 -> Objeto listbox                                     ≥±±
±±≥          ≥ ExpA2 -> Array de multas do listbox                         ≥±±
±±≥          ≥ ExpA3 -> Array de medicoes                                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥                                                             ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Efetua o reprocessamento de multas das medicoes              ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103RepMult( oList, aListBox, aMedicoes )

If Aviso( STR0236, STR0244, { STR0245, STR0246 }, 2 ) == 1 // "Atencao !", "Os dados informados serao sobrepostos. Confirma o reprocessamento das multas deste documento de entrada ?", "Sim","Nao"

	aListBox := {}
	//Efetua o reprocessamento
	A103ProcMul( aMedicoes, @aListBox )

	If Empty( aListBox )
		//Se estiver vazio, preenche uma linha em branco
		AAdd( aListBox, { .F., "", "", 0, 0, "" } )
	EndIf

	//Reinicializa o listBox
	bLine := oList:bLine
	oList:SetArray(aListBox)
	oList:bLine := bLine

EndIf

Return( Nil )

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103ProcMul≥ Autor ≥ Sergio Silveira      ≥ Data ≥11/04/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descricao ≥ Efetua o processamento de multas                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103ProcMul( ExpA1, ExpA2 )                                 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpA1 -> Array contendo as medicoes                         ≥±±
±±≥          ≥ ExpA2 -> Array do listbox de multas a ser preenchido        ≥±±
±±≥          ≥          ( passado por referencia )                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ Nenhum                                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103ProcMul( aMedicoes, aListBox )

Local cCompet    := ""
Local cCronog    := ""
Local cAliasQry  := ""
Local cQuery     := ""
Local lProcessa  := .T.
Local lFormula   := .F.
Local nLoop      := 0
Local nValor     := 0

//Percorre os itens das medicoes
For nLoop := 1 to Len( aMedicoes )

	//Posiciona no contrato
	CN9->( DbSetOrder( 1 ) )
	CN9->( MsSeek( xFilial( "CN9" ) + aMedicoes[ nLoop, 1 ] + aMedicoes[ nLoop, 2 ] ) )

	lProcessa := .T.

	//Verifica o tipo de contrato
	CN1->( DbSetOrder( 1 ) )
	If CN1->( MsSeek( xFilial( "CN1" ) + CN9->CN9_TPCTO ) )
		//Verifica se permite multas no recebimento
		lProcessa := Iif(AllTrim(CN300RetSt( "TPMULT", 0, aMedicoes[ nLoop, 3 ] ))=="1",.T.,.F.)
	EndIf

	If lProcessa

		//Posiciona no item da medicao
		cAliasQry := GetNextAlias()

		cQuery := ""
		cQuery += "SELECT R_E_C_N_O_ CNERECNO FROM " + RetSqlName( "CNE" ) + " CNE "
		cQuery += "WHERE "
		cQuery += "CNE_FILIAL='" + xFilial( "CNE" )   + "' AND "
		cQuery += "CNE_CONTRA='" + aMedicoes[nLoop,1] + "' AND "
		cQuery += "CNE_REVISA='" + aMedicoes[nLoop,2] + "' AND "
		cQuery += "CNE_NUMERO='" + aMedicoes[nLoop,3] + "' AND "
		cQuery += "CNE_NUMMED='" + aMedicoes[nLoop,4] + "' AND "
		cQuery += "CNE_ITEM='"   + aMedicoes[nLoop,5] + "' AND "
		cQuery += "CNE.D_E_L_E_T_=' '"

		cQuery := ChangeQuery( cQuery )

		dbUseArea( .T., "TOPCONN", TcGenQry( ,, cQuery ), cAliasQry, .F., .T. )

		If !( cAliasQry )->( Eof() )
			CNE->( MsGoto( ( cAliasQry )->CNERECNO ) )
		EndIf

		//Fecha a area de trabalho da query
		( cAliasQRY )->( dbCloseArea() )
		DbSelectArea( "CNE" )

		//Posiciona o cabecalho da medicao
		CND->( DbSetOrder( 1 ) )
		CND->( MsSeek( xFilial( "CND" ) + aMedicoes[nLoop,1] + aMedicoes[nLoop,2] + aMedicoes[nLoop,3] + aMedicoes[nLoop,4] ) )

		cCompet := CND->CND_COMPET

		//Posiciona o cabecalho da planilha
		CNA->( DbSetOrder( 1 ) )
		CNA->( MsSeek( xFilial( "CNA" ) + aMedicoes[nLoop,1] + aMedicoes[nLoop,2] + aMedicoes[nLoop,3] ) )

		cCronog := CNA->CNA_CRONOG

		//Posiciona no cronograma / competencia
		CNF->( DbSetOrder( 2 ) )
		CNF->( MsSeek( xFilial( "CNF" ) + aMedicoes[nLoop,1] + aMedicoes[nLoop,2] + cCronog + cCompet ) )

		//Percorre as multas / bonificacoes deste contrato
		cAliasQry := GetNextAlias()
		cQuery := ""

		cQuery += "SELECT CN4_CODIGO,CN4_DESCRI,CN4_VALID,CN4_FORMUL,"
		cQuery += "	      CN4_TIPO,CNH_NUMERO,CN4_VLDALT,CN4_VLRALT "
		cQuery += " FROM " + RetSqlName( "CNH" ) + " CNH,"
		cQuery += RetSqlName( "CN4" ) + " CN4 "
		cQuery += " WHERE CNH_FILIAL 	  = '"+xFilial("CNH")+"'"
		cQuery += "   AND CNH_NUMERO	  = '"+aMedicoes[nLoop,1]+"'"
		cQuery += "   AND CNH_REVISA	  = '"+ CnGetRevAt(aMedicoes[nLoop,1])+"'" // Revis„o atual
		cQuery += "   AND CNH.D_E_L_E_T_  = ' '"
		cQuery += "   AND CNH_CODIGO	  = CN4_CODIGO"
		cQuery += "   AND CN4_FILIAL	  = '" +xFilial("CN4")+"'"
		cQuery += "   AND CN4.D_E_L_E_T_  = ' ' "
		cQuery += " ORDER BY CNH_NUMERO,CN4_CODIGO"

		cQuery := ChangeQuery( cQuery )
		dbUseArea( .T., "TOPCONN", TcGenQry( ,, cQuery ), cAliasQry, .F., .T. )

		While !( cAliasQry )->( Eof() )
			//Avalia a aplicacao da multa
			If Empty( ( cAliasQry )->CN4_VLDALT )
				lFormula := Formula(( cAliasQry )->CN4_VALID )
			Else
				lFormula := &( ( cAliasQry )->CN4_VLDALT )
			EndIf

			If lFormula
				//Obtem o valor da multa
				If Empty( ( cAliasQry )->CN4_VLRALT )
					nValor := Formula( ( cAliasQry )->CN4_FORMUL )
				Else
					nValor := &( ( cAliasQry )->CN4_VLRALT )
				EndIf

				AAdd( aListBox, { .F., ( cAliasQRY )->CNH_NUMERO, ( cAliasQRY )->CN4_DESCRI, nValor, 1, ( cAliasQRY )->CN4_TIPO } )
			EndIf

			( cAliasQry )->( dbSkip() )

		EndDo

		//Fecha a area de trabalho da query
		( cAliasQRY )->( dbCloseArea() )

		DbSelectArea( "CN4" )

	EndIf

Next nLoop

Return

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103MultOk ≥ Autor ≥ Sergio Silveira      ≥ Data ≥11/04/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descricao ≥ Efetua a validacao das multas de contratos                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ ExpL1 := A103MultOk( ExpA1, ExpA2, ExpA3 )                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpA1 -> Array contendo as multas                           ≥±±
±±≥          ≥ ExpA2 -> Acols do SE2 ( titulos )                           ≥±±
±±≥          ≥ ExpA3 -> aHeader do SE2                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ ExpL1 -> Indica validacao                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103MultOk( aMultas, aColsSE2, aHeadSE2 )

Local aContratos := {}
Local lRet       := .T.
Local nPosPedido := GetPosSD1( "D1_PEDIDO" )
Local nPosItem   := GetPosSD1( "D1_ITEMPC" )
Local nPValor    := GdFieldPos( "E2_VALOR", aHeadSE2 )
Local nLoop      := 0
Local nValDup    := 0
Local nValMult   := 0
Local nValBoni   := 0
Local lUsaNewKey := TamSX3("F1_SERIE")[1] == 14 // Verifica se o novo formato de gravacao do Id nos campos _SERIE esta em uso

If !Empty( aMultas )

	SC7->( DbSetOrder( 1 ) )
	For nLoop := 1 to Len( aCols )

		If !ATail( aCols[ nLoop ] )

			If SC7->( MsSeek( xFilial( "SC7" ) + aCols[ nLoop, nPosPedido ] + aCols[ nLoop, nPosItem ] ) )

				//Alimenta o array de medicoes / item desta NF
				If !Empty( SC7->C7_CONTRA ) .And. !Empty( SC7->C7_PLANILH )

					If Empty( AScan( aContratos, SC7->C7_CONTRA ) )
						AAdd( aContratos, SC7->C7_CONTRA )
					EndIf

				EndIf

			EndIf

		EndIf

	Next nLoop

	//Verifica se existe alguma multa para um contrato que nao esta na NF
	For nLoop := 1 to Len( aMultas )

		If Empty( AScan( aContratos, aMultas[ nLoop, 1 ] ) )
			Aviso( STR0236, STR0247, { STR0238 }, 2 ) // "Atencao !", "Nao e possivel inserir multas para um contrato que nao esta nos itens do documento de entrada.","Ok"
			lRet := .F.
			Exit

		EndIf

	Next nLoop

	//Verifica se eh possivel aplicar as multas para o valor de titulos existente
	If lRet

		//Calcula o total de multas e / ou bonificacoes de contrato
		AEval( aMultas, { |x| If( x[5] == "1", nValMult += x[3], nValBoni += x[3] ) } )

		If nValMult > nValBoni

			//Calcula a diferenca entre multas e bonificacoes
			nValMult := nValMult - nValBoni

			nValDup := 0

			For nLoop := 1 to Len( aColsSE2 )
				nValDup += aColsSE2[ nLoop, nPValor ]
			Next nLoop

			If nValMult > nValDup
				lRet := .F.
				Aviso( STR0236, STR0248, { STR0238 }, 2 ) // "Atencao !", "O valor de multas nao pode ser superior ao valor de duplicatas do documento.", { "Ok" }
			EndIf

		EndIf

	EndIf

EndIf

If lRet .And. INCLUI
	//Valida duplicata ja existente
	If SuperGetMv("MV_EASYFIN") == "N" .And. "SF1->F1_SERIE" $ SuperGetMv("MV_2DUPREF") .And. !lUsaNewKey .And. !SuperGetMv("MV_VTESDUP", .F., .F.)
		lRet := A103F50NUM(cSerie,cNFiscal,cA100For,cLoja)
	EndIf
Endif

Return( lRet )

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103HistMul≥ Autor ≥ Sergio Silveira      ≥ Data ≥11/04/2006 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descricao ≥ Efetua a manutencao do historico das multas no contratos    ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103HistMul( ExpN1,ExpA2,ExpC3,ExpC4,ExpC5,ExpC6)           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpN1 -> Tipo : 1 - Inclusao / 2 - Exclusao                 ≥±±
±±≥          ≥ ExpA2 -> Array de multas                                    ≥±±
±±≥          ≥ ExpC3 -> Documento                                          ≥±±
±±≥          ≥ ExpC4 -> Serie                                              ≥±±
±±≥          ≥ ExpC5 -> Fornecedor                                         ≥±±
±±≥          ≥ ExpC6 -> Loja                                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ .T.                                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Materiais                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function A103HistMul( nTipo, aMultas, cDoc, cSerie, cFornec, cLoja )
Local aArea
Local cHora     := ""
Local cAliasQry := ""
Local cQuery    := ""
Local nLoop     := 0

If nTipo == 1

	cHora := Time()

	For nLoop := 1 to Len( aMultas )

		RecLock( "CNG", .T. )

		CNG->CNG_FILIAL  := xFilial( "CNG" )
		CNG->CNG_CONTRA  := aMultas[ nLoop, 1 ]
		CNG->CNG_DATA    := dDataBase
		CNG->CNG_HORA    := cHora
		CNG->CNG_DESCRI  := aMultas[ nLoop, 2 ]
		CNG->CNG_VALOR   := aMultas[ nLoop, 3 ]
		CNG->CNG_DOC     := cDoc
		SerieNfId("CNG",1,"CNG_SERIE",dDEmissao,cEspecie,cSerie)
		CNG->CNG_FORNEC  := cFornec
		CNG->CNG_LOJA    := cLoja

		CNG->( MsUnlock() )

	Next nLoop

Else

    aArea := GetArea()

	//Exclui o historico desta NF no contrato
	cAliasQry := GetNextAlias()

	cQuery := "SELECT R_E_C_N_O_ CNGRECNO "
	cQuery += "  FROM "+RetSqlName("CNG")
	cQuery += " WHERE CNG_DOC     ='"+cDoc    + "'"
	cQuery += "   AND CNG_SERIE	  ='"+SF1->F1_SERIE+ "'"
	cQuery += "   AND CNG_FORNEC  ='"+cFornec + "'"
	cQuery += "   AND CNG_LOJA    ='"+cLoja   + "'"
	cQuery += "   AND D_E_L_E_T_  =' '"

	cQuery := ChangeQuery( cQuery )
	dbUseArea( .T., "TOPCONN", TcGenQry( ,,cQuery ), cAliasQry, .F., .T. )

	While !( cAliasQry )->( Eof() )

		CNG->( dbGoto( ( cAliasQry )->CNGRECNO ) )

		RecLock( "CNG", .F. )

		CNG->( dbDelete())
		CNG->( MsUnlock())

		( cAliasQry )->( dbSkip() )

	EndDo

	//Exclui a area de trabalho da query
	( cAliasQry )->( dbCloseArea() )

   RestArea(aArea)

EndIf

Return( .t. )

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥MATA103   ∫Autor  ≥Luciana P. Munhoz   ∫ Data ≥ 08/08/2006   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥FunÁ„o GetQOri - Retorna a quantidade da Nota Fiscal Original∫±±
±±∫          ≥caso seja uma Nota Fiscal de Complemento(D1_TIPO=="C" e "I") ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥ Quando os campos F4_BENSATF e F4_ATUATF == "Sim"            ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function GetQOri (cFil, cNFOri, cSerieOri, cItemOri, cCodi, cForn, cLoj)

Local aAreaSD1	:= SD1->(GetArea())
Local nQtdD1	:= 0

SD1->(DbSetOrder(1))
If SD1->(MsSeek(cFil+cNFOri+cSerieOri+cForn+cLoj+cCodi+cItemOri))
	nQtdD1 	:= 	Int(SD1->D1_QUANT)
Else
	nQtdD1 	:= 	0
Endif

RestArea(aAreaSD1)

Return(nQtdD1)

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥MenuDef   ≥ Autor ≥ Fabio Alves Silva     ≥ Data ≥06/11/2006≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Utilizacao de menu Funcional                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥Array com opcoes da rotina.                                 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥Parametros do array a Rotina:                               ≥±±
±±≥          ≥1. Nome a aparecer no cabecalho                             ≥±±
±±≥          ≥2. Nome da Rotina associada                                 ≥±±
±±≥          ≥3. Reservado                                                ≥±±
±±≥          ≥4. Tipo de TransaáÑo a ser efetuada:                        ≥±±
±±≥          ≥    1 - Pesquisa e Posiciona em um Banco de Dados           ≥±±
±±≥          ≥    2 - Simplesmente Mostra os Campos                       ≥±±
±±≥          ≥    3 - Inclui registros no Bancos de Dados                 ≥±±
±±≥          ≥    4 - Altera o registro corrente                          ≥±±
±±≥          ≥    5 - Remove o registro corrente do Banco de Dados        ≥±±
±±≥          ≥5. Nivel de acesso                                          ≥±±
±±≥          ≥6. Habilita Menu Funcional                                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/

Static Function MenuDef()
Local aRotina3  := {	{STR0002,"NfeDocVin",0,2,0,nil},;	//"Visualizar"
						{STR0164,"NfeDocVin",0,4,0,nil},;	//"Alterar"
						{STR0006,"NFeDocVin",0,5,0,nil}}	//"Excluir"

Local aRotina4  := {	{STR0009,"NfeDocCob",0,4,0,nil},;	//"Documento de Entrada"
						{STR0198,"NfsDocCob",0,4,0,nil}}	//"Documento de Saida"

Local aRotina2  := {	{STR0165,aRotina3,0,4,0,nil},;		//"Vincular"
						{STR0166,aRotina4,0,4,0,nil}}		//"Cobertura"

//DSERTSS1-177 - submenu
Local aRotina5  := {	{STR0505,"A103Manif",0,2,0,nil},;		//"210200 - ConfirmaÁ„o da OperaÁ„o"
							{STR0506,"A103Manif",0,2,0,nil}}		//"210210 - CiÍncia da OperaÁ„o"

Local aRotComFut := {{STR0518, "A103XDesfaz", 0, 6, 0, nil}}  // "Desfazimento"

Local lGspInUseM := If(Type('lGspInUse')=='L', lGspInUse, .F.)
Local lPyme      := Iif(Type("__lPyme") <> "U",__lPyme,.F.)

Private aRotina	:= {}
Private aRotDES	:=	{{	"Parametros"		,'A103DESARC(1)',0,17,0,Nil },;
					 {	"Ev. Desacordo"		,'A103DESARC(2)'  ,0,15,0,Nil },;
					 {	"Monitor Desacordo"	,'A103DESARC(3)' ,0,16,0,Nil }} 

//Inicializa aRotina para ERP/CRM ou SIGAGSP
aAdd(aRotina,{OemToAnsi(STR0001), "AxPesqui"   , 0 , 1, 0, .F.}) 		//"Pesquisar"
aAdd(aRotina,{OemToAnsi(STR0002), "A103NFiscal", 0 , 2, 0, nil}) 		//"Visualizar"
aAdd(aRotina,{OemToAnsi(STR0003), "A103NFiscal", 0 , 3, 0, nil}) 		//"Incluir"
aAdd(aRotina,{OemToAnsi(STR0004), "A103NFiscal", 0 , 4, 0, nil}) 		//"Classificar"
aAdd(aRotina,{OemToAnsi(STR0006), "A103NFiscal", 3 , 5, 0, nil})		//"Excluir"

If __lIntPFS .And. FindFunction("JAnxM103")
    aAdd(aRotina,{OemToAnsi('Anexos'), "JAnxM103", 0 , 2, 0, nil})		//"Anexos"
EndIf

If !lGspInUseM
	aAdd(aRotina,{OemToAnsi(STR0007), "A103Impri"  , 0 , 4, 0, nil})	//"Imprimir"
	aAdd(aRotina,{OemToAnsi(STR0005), "A103Devol"  , 0 , 3, 0, .F.})	//"Retornar"
Endif

aAdd(aRotina,{OemToAnsi(STR0411), "CTBC662", 0 , 7, 0, .F.})		//"Tracker Cont·bil"
aAdd(aRotina,{OemToAnsi("Ev. Desacordo"), aRotDES, 0 , 15, 0, .F.})		//"Evento Desacordo"
aAdd(aRotina,{OemToAnsi(STR0008), "A103Legenda", 0 , 2, 0, .F.})		//"Legenda"
Aadd(aRotina,{STR0187,"MsDocument", 0 , 4, 0, nil})	//"Conhecimento"

If !lPyme
	//Inclusao da rotina do documento vinculado
	aadd(aRotina,{STR0167   , aRotina2, 0, 4, 0, nil})		//"Doc.Vinculado"
EndIf

//Retorno do saldo contido no Armazem de Transito
aAdd(aRotina,{OemToAnsi(STR0296), 'A103RetTrf' , 0 , 3, 0, nil})	//"Transito"

//Chamada do Rastreio de Contratos Fornecedores
aAdd(aRotina,{OemToAnsi(STR0374), "A103Contr", 0 , 2, 0, nil})//"Rastr.Contrato"

// Compra com entrega futura.
aAdd(aRotina, {STR0519, aRotComFut, 0, 2, 0, nil})  // "Entrega futura"

//ManifestaÁ„o do Destinatario
If FindFunction("MDeMata103")
	//aAdd(aRotina,{OemToAnsi(STR0431), "A103Manif", 0 , 2, 0, nil})//"Manifestar"
	aAdd(aRotina,{OemToAnsi(STR0431), aRotina5, 0 , 2, 0, nil})//"Manifestar" - //DSERTSS1-177 inclusao de um submenu
Endif

//-- Complementos Fiscais (MATA926)
If FindFunction("MATA926")
	aAdd(aRotina,{OemToAnsi(STR0528), "MATA926(SF1->F1_DOC, SF1->F1_SERIE, SF1->F1_ESPECIE, SF1->F1_FORNECE, SF1->F1_LOJA, 'E', SF1->F1_TIPO)", 0 , 6, 0, Nil}) //"Complementos Fiscais"
Endif

If ExistTemplate("MTA103MNU")
	ExecTemplate("MTA103MNU",.F.,.F.)
EndIf

//Ponto de entrada utilizado para inserir novas opcoes no array aRotina
If ExistBlock("MTA103MNU")
	ExecBlock("MTA103MNU",.F.,.F.)
EndIf

Return(aRotina)

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥A103VldGer≥ Autor ≥ Mary C. Hergert       ≥ Data ≥29/12/2006≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Funcao para implemetacao de validacoes gerais na confirmacao≥±±
±±≥          ≥da nota fiscal de entrada.                                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T. ou .F., confirmando ou nao o documento                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥Array com os campos da Nota Fiscal Eletronica:              ≥±±
±±≥          ≥[01]: Numero da NF-e                                        ≥±±
±±≥          ≥[02]: Codigo de Verificacao                                 ≥±±
±±≥          ≥[03]: Emissao                                               ≥±±
±±≥          ≥[04]: Hora da Emissao                                       ≥±±
±±≥          ≥[05]: Valor do credito                                      ≥±±
±±≥          ≥[06]: Numero do RPS                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103VldGer(aNFEletr)

Local lRetVldGer := .T.

If cPaisLoc == "BRA"
	If ExistBlock("MTCHKNFE")
		lRetVldGer := Execblock("MTCHKNFE",.F.,.F.,{aNFEletr})
	Endif
	If lRetVldGer	
		lRetVldGer := A103VldObr(aNFEletr) 
	Endif
EndIf

Return lRetVldGer

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥MontaaCols≥ Autor ≥ Marco Bianchi         ≥ Data ≥ 10/01/07 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Montagem do aCols para GetDados.                            ≥±±
±±≥          ≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥MontaaCols()                                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametro ≥                                                            ≥±±
±±≥          ≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Function MontaaCols(bWhileSD1,lQuery,l103Class,lClassOrd,lNfeOrd,aRecClasSD1,nCounterSD1,cAliasSD1,cAliasSB1,aRecSD1,aRateio,cCpBasePIS,cCpValPIS,cCpAlqPIS,cCpBaseCOF,cCpValCOF,cCpAlqCOF,aHeader,aCols,l103Inclui,aHeadSDE,aColsSDE,lContinua,lDivImp,lTColab)

Local nUsado     := 0
Local nPosTes    := 0
Local aAuxRefSD1 := MaFisSXRef("SD1")
Local nBasePIS	 := 0
Local nValorPIS	 := 0
Local nAliqPIS	 := 0
Local nBaseCOF	 := 0
Local nValorCOF	 := 0
Local nAliqCOF	 := 0
Local cItemSDG	 := ""
Local nItRatFro	 := 0
Local nItRatVei	 := 0
Local nPos       := 0
Local nX         := 0
Local nY         := 0
Local nTRF 		 := 0
Local cTesPed    := ""
LOCAL lA103CLAS  := ExistBlock("A103CLAS")
Local cSD1Recno  := Iif(lQuery,"SD1RECNO","(Recno())")
Local lTrbGen	 := IIf(FindFunction("ChkTrbGen"),ChkTrbGen("SD1", "D1_IDTRIB"),.F.) // Verificacao se pode ou nao utilizar tributos genericos
Local cFilSF4 	 := xFilial("SF4")
Local cFilSD2    := xFilial("SD2")
Local cTesD2     := ""
Local cTesAux    := ""
Local lIntTms	:= IntTMS()
Local lIntWMS	:= IntWMS()
Local lIntePms	:= IntePms()
Local lPMSIPC   := GetNewPar("MV_PMSIPC",  2) == 1
Local lRATAFN   := FindFunction("A103RATAFN")
Local lCsdXML 	:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA") .and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")

Local l103ClasImp := .F.
Local a103ClasImp := {}

Default lTColab := .F.

If !Empty(aBackSD1)
	aHeader := aBackSD1
EndIf
nUsado := Len(aHeader)


If l103Inclui
	//Faz a montagem de uma linha em branco no aCols.
	aadd(aCols,Array(Len(aHeader)+1))
	For nY := 1 To Len(aHeader)
		If Trim(aHeader[nY][2]) == "D1_ITEM"
			aCols[1][nY] 	:= StrZero(1,Len(SD1->D1_ITEM))
		Else
			If AllTrim(aHeader[nY,2]) == "D1_ALI_WT"
				aCOLS[Len(aCols)][nY] := "SD1"
			ElseIf AllTrim(aHeader[nY,2]) == "D1_REC_WT"
				aCOLS[Len(aCols)][nY] := 0
			Else
				aCols[1][nY] := CriaVar(aHeader[nY][2])
			EndIf
		EndIf
		aCols[1][nUsado+1] := .F.
	Next nY
Else

	While Eval( bWhileSD1 )
	    // -- Compara o Tipo da NF Selecionada SF1 X Tipo da NF SD1 --
   		If !lQuery
		    If !Eof() .And. (CALIASSD1)->D1_TIPO <> SF1->F1_TIPO
				(cAliasSD1)->(dbSkip())
				Loop
			EndIf
		EndIf

		If !lQuery .And. ((l103Class .And. lClassOrd) .Or. (l103Visual .And. lClassOrd) .Or. lNfeOrd)
			SD1->( dbGoto( aRecClasSD1[ nCounterSD1, 2 ] ) )
		EndIf
		//Integracao com o modulo de Armazenagem - SIGAWMS
		If l103Class .And. lIntWMS.And. cTipo $ "N|D|B"
			If !WmsAvalSD1("3",cAliasSD1)
				lContinua := .F.
				Exit
			EndIf
		EndIf

		If !lQuery
			SB1->(MsSeek(xFilial("SB1")+(cAliasSD1)->D1_COD))
		Endif

		aadd(aRecSD1,{(cAliasSD1)->&(cSD1Recno),(cAliasSD1)->D1_ITEM})

		aadd(aCols,Array(nUsado+1))
		cTesPed := ""
		//Inicializa a funcao fiscal
		MaFisIniLoad(Len(aCols),,,IIf(lTrbGen,(cAliasSD1)->D1_IDTRIB,""))

		//Atualiza numero do item de acordo com o acols na classificacao de uma pre-nota
		If l103Class
			MaFisAlt("IT_ITEM",(cAliasSD1)->D1_ITEM,Len(aCols))
		Endif

		SF4->(dbSetOrder(1))
		SF4->(MsSeek(xFilial("SF4")+(cAliasSD1)->D1_TES))

		For nX := 1 To Len(aAuxRefSD1)
	 		//Desconta o Valor do ICMS DESONERADO do valor do Item D1_VUNIT - Ajuste para visualizacao da NFE com desoneracao de ICMS
			If aAuxRefSD1[nX][2] == "IT_VALMERC" .And. SF4->F4_AGREG$"R"
				MaFisLoad(aAuxRefSD1[nX][2],(cAliasSD1)->(FieldGet(FieldPos(aAuxRefSD1[nX][1])))+(cAliasSD1)->D1_DESCICM,Len(aCols))
			ElseIf aAuxRefSD1[nX][2] == "IT_TES" .And. !Empty((cAliasSD1)->D1_TESACLA) .And. !l103Visual
				MaFisLoad(aAuxRefSD1[nX][2],(cAliasSD1)->D1_TESACLA,Len(aCols))
			ElseIf aAuxRefSD1[nX][2] == "IT_TES" .And. Empty((cAliasSD1)->D1_TES) .And. !Empty((cAliasSD1)->D1_TESACLA) .And. l103Visual
				MaFisLoad(aAuxRefSD1[nX][2],(cAliasSD1)->D1_TESACLA,Len(aCols))
			Else
				MaFisLoad(aAuxRefSD1[nX][2],(cAliasSD1)->(FieldGet(FieldPos(aAuxRefSD1[nX][1]))),Len(aCols))
			EndIf
		Next nX

		MaFisEndLoad(Len(aCols),2)

		If l103Class .And. SuperGetMV("MV_EASY") == "S" .And. !Empty((cAliasSD1)->D1_TEC)
			MaFisLoad("IT_POSIPI",(cAliasSD1)->D1_TEC,Len(aCols))
		EndIf

		//Atualiza a condicao de pagamento com base no Pedido de compra
		If ( (Empty(cCondicao) .Or. l103Class) .And. !Empty((cAliasSD1)->D1_PEDIDO) )
			nRecC7 := A103RECC7(xFilial("SC7"),(cAliasSD1)->D1_PEDIDO,(cAliasSD1)->D1_FORNECE,(cAliasSD1)->D1_LOJA,(cAliasSD1)->D1_COD,(cAliasSD1)->D1_ITEMPC)
			SC7->(DbGoTo(nRecC7))
			If nRecC7 > 0
				If !l103Class 
					If !cCondicao == SC7->C7_COND
						cCondicao := SC7->C7_COND
					Endif
				EndIf
			EndIf
		EndIf

		//Atualiza os dados do acols com base no Pedido de compra
		If ( !Empty((cAliasSD1)->D1_PEDIDO) .And. l103Class)
			nRecC7 := A103RECC7(xFilial("SC7"),(cAliasSD1)->D1_PEDIDO,(cAliasSD1)->D1_FORNECE,(cAliasSD1)->D1_LOJA,(cAliasSD1)->D1_COD,(cAliasSD1)->D1_ITEMPC)
			SC7->(DbGoTo(nRecC7))
			If nRecC7 > 0
				cTesPed := SC7->C7_TES 
				If Empty(SC7->C7_SEQUEN) .And. !lTColab .And. ( !(SF1->F1_STATUS $ "B|C") .Or. Empty((cAliasSD1)->D1_TESACLA)) .And. (Empty(SF1->F1_APROV) .Or. Empty((cAliasSD1)->D1_TESACLA)) .And. AllTrim((cAliasSD1)->D1_ORIGEM) != "GF"
					NfePC2Acol(SC7->(RecNo()),Len(aCols),(cAliasSD1)->D1_QUANT,(cAliasSD1)->D1_ITEM,l103Class,@aRateio,aHeadSDE,@aColsSDE,(cAliasSD1)->D1_VUNIT)
					aBackColsSDE:=ACLONE(aColsSDE)
					//-- Atualiza as despesas de acordo com a pre-nota.
					If aRateio[1] == 0 .And. aRateio[2] == 0 .And. aRateio[3] == 0
						aRateio[1] := SF1->F1_SEGURO
						aRateio[2] := SF1->F1_DESPESA
						aRateio[3] := SF1->F1_FRETE
					EndIf
				EndIf
			EndIf
			MaFisAlt("IT_DESPESA",(cAliasSD1)->D1_DESPESA,Len(aCols))
			MaFisAlt("IT_SEGURO",(cAliasSD1)->D1_SEGURO,Len(aCols))
			MaFisAlt("IT_FRETE",(cAliasSD1)->D1_VALFRE,Len(aCols))
		ElseIf l103Visual
			aRateio[1] := SF1->F1_SEGURO
			aRateio[2] := SF1->F1_DESPESA
			aRateio[3] := SF1->F1_FRETE
		EndIf

		// Preenchimento do aCols
		DbSelectArea(cAliasSD1)
		SD1->(DbGoto((cAliasSD1)->&(cSD1Recno))) 
		For nY := 1 To nUsado
			If ( aHeader[nY][10] <> "V")
				aCols[Len(aCols)][nY] := FieldGet(FieldPos(aHeader[nY][2]))
				If (l103Class .Or. l103Visual) .And. Alltrim(aHeader[ny][2]) == "D1_TES" .And. Empty((cAliasSD1)->D1_TES)
					If !Empty((cAliasSD1)->D1_TESACLA) .AND. !l103Visual
						aCols[Len(aCols)][ny] := (cAliasSD1)->D1_TESACLA
						MaFisLoad("IT_TES","",Len(aCols))
						MaFisAlt("IT_TES",(cAliasSD1)->D1_TESACLA,Len(aCols))

						For nX := 1 To Len(aAuxRefSD1)
							Do Case
							Case !("IT_BAS"$aAuxRefSD1[nX][2] .Or. "IT_VAL"$aAuxRefSD1[nX][2] .Or. "IT_ALIQ"$aAuxRefSD1[nX][2])
								
							Case !Empty(SD1->(FieldGet(FieldPos(aAuxRefSD1[nX][1]))))
								MaFisAlt(aAuxRefSD1[nX][2],SD1->(FieldGet(FieldPos(aAuxRefSD1[nX][1]))),Len(aCols))
							EndCase 
						Next nX
					ElseiF  !Empty((cAliasSD1)->D1_TESACLA) .And. Empty((cAliasSD1)->D1_TES)
						aCols[Len(aCols)][ny] := (cAliasSD1)->D1_TESACLA
						MaFisLoad("IT_TES","",Len(aCols))
						MaFisAlt("IT_TES",(cAliasSD1)->D1_TESACLA,Len(aCols))
					ElseIf !Empty(cTesPed)
						aCols[Len(aCols)][ny] := cTesPed
					Else
						//-- Para DevoluÁıes (D) ou Beneficiamento (B) deve-se avaliar a TES de devoluÁ„o (F4_TESDV) vinculada na TES do documento de origem (SD2)
						If cTipo $ "D|B" 
							
							//-- Limpar as vari·veis de controle a cada iteraÁ„o do loop
							cTesD2 := "" 
							cTesAux := "" 
							
							//-- Obtem TES utilizada no documento de origem (SD2)
							cTesD2 := GetAdvFVal("SD2", "D2_TES", cFilSD2 + SD1->D1_NFORI + SD1->D1_SERIORI + SD1->D1_FORNECE + SD1->D1_LOJA + SD1->D1_COD + SD1->D1_ITEMORI, 3, "", .T.)

							//-- Obtem TES de devoluÁ„o vinculada a TES utilizada no documento de origem
							If !Empty(cTesD2)
								cTesAux := GetAdvFVal("SF4", "F4_TESDV", cFilSF4 + cTesD2, 1, "", .T.)
							EndIf
							
							//-- Caso ainda assim n„o encontre, utiliza a do cadastro do produto (SB1)
							If Empty(cTesAux)
								cTesAux := RetFldProd((cAliasSB1)->B1_COD, "B1_TE", cAliasSB1)
							EndIf
						Else 
							cTesAux := RetFldProd((cAliasSB1)->B1_COD,"B1_TE",cAliasSB1)
						EndIf

						aCols[Len(aCols)][ny] := cTesAux 
					EndIf
				EndIf

				If l103Class .And. Alltrim(aHeader[ny][2]) == "D1_RATEIO" .And. Empty((cAliasSD1)->D1_RATEIO)
					aCols[Len(aCols)][ny] := "2" 
				EndIf
			Else
				If AllTrim(aHeader[nY,2]) == "D1_ALI_WT"
					aCOLS[Len(aCols)][nY] := "SD1"
				ElseIf AllTrim(aHeader[nY,2]) == "D1_REC_WT"
					aCOLS[Len(aCols)][nY] := (cAliasSD1)->&(cSD1Recno)
				Else
					aCols[Len(aCols)][nY] := CriaVar(aHeader[nY][2])
				EndIf
				Do Case
				Case Alltrim(aHeader[nY][2]) == "D1_CODITE"
					aCols[Len(aCols)][ny] := (cAliasSB1)->B1_CODITE
				Case Alltrim(aHeader[nY][2]) == "D1_CODGRP"
					aCols[Len(aCols)][ny] := (cAliasSB1)->B1_GRUPO
				EndCase
			EndIf
			If Trim(aHeader[ny][2]) == "D1_TES"
				nPosTes := nY
			EndIf

			If ( aHeader[nY][8] == "M" .And. aHeader[nY][10] == "R")
				aCols[Len(aCols)][nY]:= SD1->&(aHeader[nY][2])
			EndIf

			aCols[Len(aCols)][nUsado+1] := .F.
		Next nY 

		//Se for classificaÁ„o de um documento com integraÁ„o com SIGAPMS ,ir· carregar as Tarefas relacionadas ao produto
		If l103Class
			// 1 - utilizaÁ„o a associaÁ„o autom·tica com o PMS
			// 2 - n„o utiliza a associaÁ„o autom·tica com o PMS
			// default: n„o utilizar a associaÁ„o autom·tica
			
			If lIntWMS .And. lPMSIPC
				PMS103IPC(Len(aCols),l103Class)
			EndIf
  			   
			If Len(aRatAFN) == 0 .And. lIntePms .And. lRATAFN
				A103RATAFN(cNFiscal,cSerie,cA100For,cLoja,@aRatAFN,@aHdrAFN)
			Endif

			// Verifica se transf. filiais para retornar Base IPI
			If !Empty((cAliasSD1)->D1_TES) .Or. !Empty((cAliasSD1)->D1_TESACLA)
				A103TrfIPI(IIf(!Empty((cAliasSD1)->D1_TES),(cAliasSD1)->D1_TES,(cAliasSD1)->D1_TESACLA),nTRF:=(nTRF+1))
			EndIf
		EndIf

		//Ponto de Entrada que permite manipular o item do aCols
		If lA103Clas .And. !l103Visual .And. l103Class
			a103ClasImp := ExecBlock("A103CLAS",.F.,.F.,{cAliasSD1})
			If ValType(a103ClasImp)=="A" .And. Len(a103ClasImp)==4
				l103ClasImp := .T.
			EndIf 	
			MaColsToFis(aHeader,aCols,Len(aCols),"MT100") 
		EndIf

		DbSelectArea(cAliasSD1)
		If l103Class .And. nPosTes > 0 .And. !Empty(aCols[Len(aCols),nPosTes]) .And. !(SF1->F1_STATUS $ "B|C") .And. AllTrim((cAliasSD1)->D1_ORIGEM) != "GF"
			MaFisLoad("IT_TES","",Len(aCols))
			MaFisAlt("IT_TES",aCols[Len(aCols)][nPosTes],Len(aCols))
						
			For nX := 1 To Len(aAuxRefSD1)
				Do Case
				Case !("IT_BAS"$aAuxRefSD1[nX][2] .Or. "IT_VAL"$aAuxRefSD1[nX][2] .Or. "IT_ALIQ"$aAuxRefSD1[nX][2])
					
				Case !Empty(SD1->(FieldGet(FieldPos(aAuxRefSD1[nX][1]))))
					MaFisAlt(aAuxRefSD1[nX][2],SD1->(FieldGet(FieldPos(aAuxRefSD1[nX][1]))),Len(aCols))
				EndCase 
			Next nX

			MaFisToCols(aHeader,aCols,Len(aCols),"MT100")
			If ExistTrigger("D1_TES")
				RunTrigger(2,Len(aCols),,"D1_TES")
			EndIf
		EndIf
		//Tratamento especial para a Average
		If (l103Class .Or. l103Visual) .And. Empty((cAliasSD1)->D1_TES)
			If Empty(aCols[Len(aCols),nPosTes])
				MaFisLoad("IT_TES",(cAliasSD1)->D1_TES,Len(aCols))
			Endif

			If (cAliasSD1)->D1_BASEIPI > 0 .And. (!l103ClasImp .Or. (l103ClasImp .And. !a103ClasImp[1] )) 
				MaFisAlt("IT_BASEIPI",(cAliasSD1)->D1_BASEIPI,Len(aCols))
				MaFisAlt("IT_ALIQIPI",(cAliasSD1)->D1_IPI,Len(aCols))
				MaFisAlt("IT_VALIPI",(cAliasSD1)->D1_VALIPI,Len(aCols))
			EndIf
			If (cAliasSD1)->D1_BASEICM > 0 .And. (!l103ClasImp .Or. (l103ClasImp .And. !a103ClasImp[2] )) 
				MaFisAlt("IT_BASEICM",(cAliasSD1)->D1_BASEICM,Len(aCols))
				MaFisAlt("IT_ALIQICM",(cAliasSD1)->D1_PICM,Len(aCols))
				MaFisAlt("IT_VALICM",(cAliasSD1)->D1_VALICM,Len(aCols))
			EndIf

			If !Empty( cCpBasePIS ) .And. !Empty( cCpValPIS ) .And. !Empty( cCpAlqPIS ) .And. (!l103ClasImp .Or. (l103ClasImp .And. !a103ClasImp[3] )) 
				nBasePIS    := ( cAliasSD1 )->( FieldGet( (  cAliasSD1 )->( FieldPos( cCpBasePIS ) ) ) )
				nValorPIS   := ( cAliasSD1 )->( FieldGet( (  cAliasSD1 )->( FieldPos( cCpValPIS ) ) ) )
				nAliqPIS    := ( cAliasSD1 )->( FieldGet( (  cAliasSD1 )->( FieldPos( cCpAlqPIS ) ) ) )

				If !Empty( nBasePIS )
					MaFisAlt("IT_BASEPS2", nBasePIS ,Len(aCols))
					MaFisAlt("IT_VALPS2" , nValorPIS,Len(aCols))
					MaFisAlt("IT_ALIQPS2" , nAliqPIS,Len(aCols))
				EndIf
			EndIf

			If !Empty( cCpBaseCOF ) .And. !Empty( cCpValCOF ) .And. !Empty( cCpAlqCOF ) .And. (!l103ClasImp .Or. (l103ClasImp .And. !a103ClasImp[4] )) 
				nBaseCOF    := ( cAliasSD1 )->( FieldGet( (  cAliasSD1 )->( FieldPos( cCpBaseCOF ) ) ) )
				nValorCOF   := ( cAliasSD1 )->( FieldGet( (  cAliasSD1 )->( FieldPos( cCpValCOF ) ) ) )
				nAliqCOF    := ( cAliasSD1 )->( FieldGet( (  cAliasSD1 )->( FieldPos( cCpAlqCOF ) ) ) )
				If !Empty( nBaseCOF )
					MaFisAlt("IT_BASECF2", nBaseCOF ,Len(aCols))
					MaFisAlt("IT_VALCF2" , nValorCOF,Len(aCols))
					MaFisAlt("IT_ALIQCF2" , nAliqCOF ,Len(aCols))
				EndIf
			EndIf

			MaFisToCols(aHeader,aCols,Len(aCols),"MT100")
		EndIf
		//Integracao com o modulo de Transportes
		If lIntTms
			DbSelectArea("SDG")
			DbSetOrder(7)
			If MsSeek(xFilial("SDG")+"SD1"+(cAliasSD1)->D1_NUMSEQ)
				If cItemSDG <> (cAliasSD1)->D1_ITEM
					cItemSDG	:= (cAliasSD1)->D1_ITEM
					If Empty(SDG->DG_CODVEI) .And. Empty(SDG->DG_VIAGEM) //Verifica se o Rateio foi por Veiculo/Viagem ou por Frota
						aadd(aRatFro,{cItemSDG,{},SDG->DG_CODDES})
						nItRatFro++
					Else
						If Type("aRatVei")== "U"
							aRatVei := {}
						EndIf	
						aadd(aRatVei,{cItemSDG,{},SDG->DG_CODDES})
						nItRatVei++
					EndIf
				EndIf
				Do While !Eof() .And. xFilial("SDG")+"SD1"+(cAliasSD1)->D1_NUMSEQ == DG_FILIAL+DG_ORIGEM+DG_SEQMOV
					If Empty(SDG->DG_CODVEI) .And. Empty(SDG->DG_VIAGEM) //Verifica se o Rateio foi por Veiculo/Viagem ou por Frota
						aadd(aRatFro[nItRatFro][2],{SDG->DG_ITEM, SDG->DG_TOTAL,.F.})
					Else
						If ( nPos := Ascan(aRatVei[nItRatVei][2], { |x| x[2] == SDG->DG_CODVEI } ) ) == 0
							aadd(aRatVei[nItRatVei][2],{SDG->DG_ITEM,SDG->DG_CODVEI, SDG->DG_FILORI, SDG->DG_VIAGEM, SDG->DG_TOTAL," ",0,0,.F.})
						EndIf
					EndIf
					dbSkip()
				EndDo
			EndIf
		EndIf
		//Integracao com o modulo de Armazenagem - SIGAWMS
		If l103Class .And. lIntWMS .And. SF4->F4_ESTOQUE == "S" .And. cTipo $ "N|D|B"
			//-- Efetua o tratamento dos campos do SIGAWMS do aCols
			WmsAvalSD1("2",cAliasSD1,aCols,Len(aCols),aHeader)
		EndIf

		//Ao Visualizar uma NFE com F4_AGREG=R o valor da base ja esta DESONERADO por isso deve se ajustado no NF_VALMERC
		If l103Visual .And. SF4->F4_AGREG$"R"
			MaFisLoad("NF_VALMERC",SF1->F1_VALMERC)
		EndIf

		//Ajuste no valor total da NF na visualizacao caso o valor do campo F1_VALBRUT seja diferente de NF_TOTAL
		//Exemplo: Convenio 43.080 - MG
		If l103Visual .And. MaFisRet(,"NF_TOTAL") <> SF1->F1_VALBRUT .And. SF1->F1_VALBRUT > 0
			MaFisLoad("NF_TOTAL",SF1->F1_VALBRUT)
		EndIf

		//Efetua skip na area SD1 ( regra geral ) ou incrementa o contador
		//quando ordem por ITEM + CODIGO DE PRODUTO
		If !lQuery .And. ((l103Class .And. lClassOrd) .Or. (l103Visual .And. lClassOrd) .Or. lNfeOrd)
			nCounterSD1++
		Else
			DbSelectArea(cAliasSD1)
			dbSkip()
		EndIf
	EndDo
	If ALTERA .And. l103Class .And. lIntWMS
		aColsOrig := aClone(aCols)
	EndIf

	If lDivImp
		For nX:=1 To Len(aCols)
			aCols[nX,GetPosSD1("D1_LEGENDA")] := A103DivImp(aCols[nX])
		Next nX
	Endif

	//relaciona os itens XML com os itens da NF no campo virtual D1_ITXML
	if lCsdXML .and. ( (type("l103Visual") == "L" .and. l103Visual) .or. ( lTColab .and. l103Class ) )
		For nX :=1 To Len(aCols)
			aCols[nX,GetPosSD1("D1_ITXML")] := A103ItXml(aCols[nX,GetPosSD1("D1_ITEM")],aCols[nX,GetPosSD1("D1_COD")],lTColab)
		Next nX
	endif

EndIf

Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103Toler ≥ Autor ≥Nereu Humberto Junior  ≥ Data ≥26/02/2007≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Valida se nf bloqueada por tolerancia ja foi liberada e nao ≥±±
±±≥          ≥permite que a quantidade/preco seja alterado pelo MATA103.  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103Toler( ) //Funcao no X3_VALID -> D1_QUANT/D1_VUNIT      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T. ou .F.                                                  ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103Toler()

Local aArea    := GetArea()
Local aAreaSC7 := SC7->(GetArea())
Local nPosPc   := GetPosSD1("D1_PEDIDO")
Local nPosItPc := GetPosSD1("D1_ITEMPC")
Local nPosOs   := GetPosSD1("D1_ORDEM")
Local nPosOp   := GetPosSD1("D1_OP")
Local nPosCod  := GetPosSD1("D1_COD")
Local nPosNfOri:= GetPosSD1("D1_NFORI")
Local nPosTes  := GetPosSD1("D1_TES")
Local nPosQtd  := GetPosSD1("D1_QUANT")
Local lRet     := .T.
Local cCampo   := ReadVar()
Local lWmsNew  := SuperGetMv("MV_WMSNEW",.F.,.F.) .And. SuperGetMV("MV_INTWMS",.F.,.F.)
Local nPosAutTes  := 0
Local cTes		 := ""
Local lQtdZero := .F.
Local lVlrZero := .F.
Local nQntPedid	:= 0
Local nQntNota	:= 0
Local nTolera	:= 0
Local nQuantD1	:= 0
Local cPcToSal  := SuperGetMV("MV_PCTOSAL", .F., "N")	
Local nQtdSegUm   := 0
Local cCampoant := cCampo
Local lPropFret := SuperGetMV("MV_FRT103E",.F.,.T.)
 
If cCampo == "M->D1_QTSEGUM"
	nQtdSegUm := &cCampo
	cCampo := "M->D1_QUANT"
Endif

l103TolRec := If(Type('l103TolRec') == 'L',l103TolRec,.F.)

If IsInCallStack("MATA103")

	If l103Auto .And. Type("aAutoCab") <> "U" .And. Type("aAutoItens") <> "U"
		If (nPosAutTes := aScan(aAutoItens[n],{|x| AllTrim(x[1])=="D1_TES"})) > 0
			cTes := aAutoItens[n,nPosAutTes,2]
		Endif
	Else 
		cTes := aCols[n][nPosTes]
	Endif

	If !Empty(cTes)
		lQtdZero := Posicione("SF4",1,xFilial("SF4")+cTes,"F4_QTDZERO") == "1"
		lVlrZero := Posicione("SF4",1,xFilial("SF4")+cTes,"F4_VLRZERO") == "1"

		If cCampo == "M->D1_QUANT"
			lRet := Iif(lQtdZero,.T.,Positivo())
		ElseIf cCampo == "M->D1_VUNIT"
			lRet := Iif(lVlrZero,.T.,NaoVazio() .And. Positivo())
		EndIf
	Else
		If cCampo == "M->D1_QUANT"
			lRet := Positivo()
		Elseif cCampo == "M->D1_VUNIT"
			lRet := NaoVazio() .And. Positivo()
		Endif
	Endif 
	
Endif

If IsInCallStack("MATA140") //Pre-Nota
	If Type("aAutoCab") == "U" .Or. (Type("aAutoCab") == "A" .And. aScan(aAutoCab,{|x| AllTrim(x[1]) == "COLAB"}) == 0)
		If (cTipo == "C" .And. Type("cTpCompl") <> "C") .Or. (cTipo == "C" .And. Type("cTpCompl") == "C" .And. cTpCompl $ "1*3")
			If cCampo == "M->D1_QUANT"
				Help( " ", 1, "CONFRETE" )
				lRet := .F.
			EndIf
		EndIf
	EndIf
EndIf

If (nModulo <> 12)   // Se for SigaLoja, n„o entra
	DbSelectArea("SC7")
	SC7->(dbSetOrder(1))
	If nPosPc > 0 .And. nPosItPc > 0
		If SC7->(MsSeek(xFilial("SC7")+aCols[n][nPosPc]+aCols[n][nPosItPc]))			
			If !Empty(SC7->C7_CODED)
				If (cCampo == "M->D1_QUANT" .And. (SC7->C7_QUANT-SC7->C7_QUJE-SC7->C7_QTDACLA) < &cCampo) .Or.;
					 (cCampo == "M->D1_VUNIT" .And. SC7->C7_PRECO != &cCampo)
					Help("",1,STR0402,,STR0403,4,1) // "EDITAL" ## "Este documento pertence ‡ um Edital e nao poder· ocorrer alteraÁ„o na Quantidade e/ou Valor."
					lRet := .F.
				EndIf
			ElseIf(cCampo == "M->D1_QUANT")
				nTolera := SuperGetMV("MV_PCTOLER", .F., 0)			
				If(ValType(nTolera) == "C")
					nTolera := Val(nTolera)
				ElseIf(ValType(nTolera) != "N")
					nTolera := 0
				EndIf
								
				If(nTolera > 0)
					
					nTolera		:= ( nTolera/100 ) + 1	
										
					If Inclui
						If cPcToSal == "N"
							nQntPedid	:= SC7->C7_QUANT-SC7->C7_QTDACLA-SC7->C7_QUJE 
						Else
							nQntPedid	:= SC7->C7_QUANT-SC7->C7_QTDACLA
						Endif
					Else	
						DbSelectArea("SD1")
						nQuantD1 	:= GetAdvFval("SD1","D1_QUANT",xfilial("SD1") + SF1->F1_DOC + SF1->F1_SERIE + SF1->F1_FORNECE +SF1->F1_LOJA+ACOLS[N][2]+ ACOLS[N][1],1)	
					    nQuantD1 	:= SC7->C7_QTDACLA - nQuantD1 // quantidade a classificar - a quantidade sendo alterada
						If cPcToSal == "N"
							nQntPedid	:= SC7->C7_QUANT-nQuantD1-SC7->C7_QUJE 
						Else
							nQntPedid	:= SC7->C7_QUANT-nQuantD1
						Endif
					Endif
					
					nQntNota	:= &cCampo	
					If cCampoant == 'M->D1_QTSEGUM'		
						nQntNota	:= aCols[n][nPosQtd]
					Endif		

					If cPcToSal == "N"
						If(nQntNota > (nQntPedid * nTolera))
							Help(' ', 1, 'A103PCNSLD')
							lRet := .F.
						Endif
					Else
						If(nQntNota + SC7->C7_QUJE  > (nQntPedid * nTolera))
							Help(' ', 1, 'A103PCNSLD')
							lRet := .F.
						EndIf	
					Endif

					If !lRet .And. cCampoant == 'M->D1_QTSEGUM'	
						If Iif(cPaisLoc<>"BRA",Type("nQtdAnt") == "N",ValType(nQtdAnt) == "N")
							If nQtdAnt > 0 
								aCols[n][nPosQtd] := nQtdAnt
							Endif
						Endif
					Endif
					
				EndIf
			EndIf
		EndIf
	EndIf
EndIf

If lRet .And. SuperGetMV("MV_RESTCLA",.F.,"2")=="1" .And. l103TolRec
	If !Empty(aCols[n][nPosPc]) .And. !Empty(aCols[n][nPosItPc])
		SC7->(dbSetOrder(1))
		If SC7->(MsSeek(xFilial("SC7")+aCols[n][nPosPc]+aCols[n][nPosItPc]))
			SCR->(dbSetOrder(1))
			If SCR->(MsSeek(xFilial("SCR")+"NF"+Padr(SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,Len(SCR->CR_NUM)))) ;
					.And. ( SCR->CR_STATUS $ "03|05" )
				lRet := .F.
				Aviso(OemToAnsi(STR0178),OemToAnsi(STR0271+IIF("QUANT"$cCampo,STR0272,STR0273)+STR0274),{OemToAnsi(STR0238)},2) //"O campo de "##"quantidade"##"preÁo unit·rio"##" sÛ poder· ser alterado atravÈs da prÈ-nota de entrada, pois a Nota Fiscal j· foi liberada do bloqueio de toler‚ncia de recebimento."
			Endif
		Endif
	Endif
Endif

//Se alterada quantidade, recalcula valor das despesas de acordo com o pedido de compras
If (nPosPc > 0 .And. nPosItPc > 0)
	If lPropFret .And. FindFunction("A103Desp") .And. cCampo == "M->D1_QUANT" .And. (!Empty(aCols[n][nPosPc]) .And. !Empty(aCols[n][nPosItPc]))
		A103Desp()
	EndIf
ElseIf nPosNfOri > 0 //DevoluÁ„o de documento de saÌda
	If FindFunction("A103Desp") .And. cCampo == "M->D1_QUANT" .And. !Empty(aCols[n][nPosNfOri])
		A103Desp()
	EndIf
EndIf

If lRet
	lRet:= A103RecAc()
EndIf

If lRet //para os itens que foram distribuidos pelo WMS, n„o permite alterar a quantidade
	If lWmsNew .And. IsInCallStack("MATA103") .AND. l103Class .AND. IntWMS() .AND. n <= Len(aColsOrig)
		lRet := WMSVldD07(2,aColsOrig,n,aHeader)
	EndIf
EndIf

If lRet .And. cCampo == "M->D1_QUANT" 
	//Valida a O.P quando integrado com o mÛdulo de manutenÁ„o de ativos
	If IsInCallStack("MATA103") .And. nPosOp > 0 .And. nPosCod > 0 .And. nPosOs > 0 .And. FindFunction("NGAPAGD1OR")
		If !NGAPAGD1OR(aCols[n,nPosOs],aCols[n,nPosOp],aCols[n,nPosCod],M->D1_QUANT)
			lRet := .F.
		EndIf
	EndIf
EndIf

RestArea(aAreaSC7)
RestArea(aArea)

Return(lRet)


/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103RecAC   ≥ Autor ≥Julio C.Guerato      ≥ Data ≥25/08/2009≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Faz Recalculo do Valor do Acrescimo                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T. ou .F.                                                  ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103RecAC()
Local nPQuant
Local nPValAcRS
Local cCampo     := ReadVar()
Local lRet       := .T.

If "D1_QUANT"$cCampo
	nPQuant    := GetPosSD1("D1_QUANT")
	nPValAcRS  := GetPosSD1("D1_VALACRS")
	If nPQuant>0 .And. nPValAcRs >0
		If !Empty(aCols[n][nPQuant]) .And. !Empty(aCols[n][nPValAcRs])
	    	 If (aCols[n][nPQuant])>0 .And. (aCols[n][nPValAcRs])>0
	    	 	If (M->D1_QUANT-aCols[n][nPQuant])<>0 .And. M->D1_QUANT<>0
	    	 		aCols[n][nPValAcRS]:= (aCols[n][nPValAcRs]/aCols[n][nPQuant])* M->D1_QUANT
	    	 	Else
	    	 	    // Zerou Quantidada, retorna falso para garantir valor do rateio
		    	 	If M->D1_QUANT = 0
		    	 		lRet:= .F.
    	 				Aviso((STR0119),OemToAnsi(STR0317),{STR0461})
		    	 	EndIf
	    	 	EndIf
		     EndIf
		EndIf
	EndIf
EndIf

Return (lRet)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103VldDsc≥ Autor ≥ Ricardo Berti         ≥ Data ≥15/07/2008≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Validacao para habilitar ou nao a edicao dos campos de      ≥±±
±±≥          ≥descontos no item.										  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103VldDsc( ) //Funcao no X3_WHEN -> D1_DESC/D1_VALDESC     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T. ou .F.                                                  ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103VldDsc()

Local lRet     := .T.
Local cCampo   := ReadVar()
If Left(FunName(),7)=="MATA103" .And. cTipo$"PI" .And. (cCampo == "M->D1_DESC" .Or. cCampo == "M->D1_VALDESC")
	lRet := .F.
EndIf
Return(lRet)


/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103PrdGrd≥Autor  ≥Alexandre Inacio Lemes ≥ Data ≥10/08/2007 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descricao ≥ Interface de Grade de Produtos para Pre-Nota e Doc.Entrada  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ Nenhum                                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ .T. se Valido ou .F. se Invalido                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥Getdados do MATA103.PRW disparada pelo X3_VALID do D1_COD    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103PrdGrd()

Local aArea	      := GetArea()
Local cItem       := ""
Local cNewItem    := ""
Local cPrdOrig    := ""
Local cCpoName	  := StrTran(ReadVar(),"M->","")
Local cSaveReadVar:= __READVAR
Local nSaveN      := N
Local nNewItem    := Len(aCols)
Local nPosItem    := GetPosSD1("D1_ITEM")
Local nPosProd    := GetPosSD1("D1_COD")
Local nPosQuant   := GetPosSD1("D1_QUANT")
Local nPosQtSegum := GetPosSD1("D1_QTSEGUM")
Local nPosVUnit   := GetPosSD1("D1_VUNIT")
Local nPosTotal   := GetPosSD1("D1_TOTAL")
Local nPosOp	  := GetPosSD1("D1_OP")
Local nPosOs	  := GetPosSD1("D1_ORDEM")
Local nLinX       := 0
Local nColY       := 0
Local nY          := 0
Local lGrade	  := MaGrade()
Local lReferencia := .F.
Local lAadd       := .F.
Local lRet 		  := .T.
Local lWmsNew := SuperGetMv("MV_WMSNEW",.F.,.F.) .And. SuperGetMV("MV_INTWMS",.F.,.F.)
Local cTailItem	  := ""
Local oDlg

If Inclui
	//Verifica se o usuario tem permissao de inclusao
	If IsInCallStack("MATA140") //Pre-Nota
		lRet := MaAvalPerm(1,{M->D1_COD,"MTA140",3})
	ElseIf IsInCallStack("MATA103") //Documento de Entrada
		lRet := MaAvalPerm(1,{M->D1_COD,"MTA103",3})
	ElseIf IsInCallStack("MATA102N") // Remito de Entrada
		lRet := MaAvalPerm(1,{M->D1_COD,"MT102N",3})
	ElseIf IsInCallStack("MATA101N") // Factura de Entrada
		lRet := MaAvalPerm(1,{M->D1_COD,"MT101N",3})
	EndIf
	If !lRet
		Help(,,1,'SEMPERM')
	EndIf
EndIf

//Verifica se a grade esta ativa e se o produto digitado e uma referencia e Monta o AcolsGrade e o AheadGrade para este item
If lRet .And. !Empty(&(ReadVar())) .And. lGrade

	PRIVATE oGrade	  := MsMatGrade():New('oGrade',,"D1_QUANT",,"A103VldGrd()",,;
	{{"D1_QUANT"  ,.T. , {{"D1_QTSEGUM",{|| ConvUm(AllTrim(oGrade:GetNameProd(,nLinha,nColuna)),aCols[nLinha][nColuna],0,2) } }} },;
	{"D1_VUNIT"  ,NIL ,NIL},;
	{"D1_ITEM"	 ,NIL ,NIL},;
	{"D1_QTSEGUM",NIL , {{"D1_QUANT",{|| ConvUm(AllTrim(oGrade:GetNameProd(,nLinha,nColuna)),0,aCols[nLinha][nColuna],1) }}} };
	})

	cProdRef := &(ReadVar())

	lReferencia := MatGrdPrrf(@cProdRef)

	If lReferencia
		//So aceita a entrada de dados via interface de grade se o usr
		//estiver posicionado na ultima linha da MsGetdados (NewLine)
		If N >= Len(aCols) .And. Empty(aCols[Len(aCols)][nPosProd])

			oGrade:MontaGrade(1,cProdRef,.T.,,lReferencia,.T.)
			oGrade:nPosLinO := 1
			oGrade:cProdRef	:= cProdRef
			oGrade:lShowMsgDiff := .F. // Desliga apresentacao do "A410QTDDIF"

			cItem    := aCols[nSaveN][nPosItem]
			nNewItem := Len(aCols)
			lAadd    := .F.

			DEFINE MSDIALOG oDlg TITLE STR0276 OF oMainWnd PIXEL FROM 000,000 TO 220,520  //"Interface para Grade de Produtos"

			oSize := FwDefSize():New(.T.,,,oDlg)
			oSize:AddObject( "QUANT",  100, 30, .T., .T. ) // Totalmente dimensionavel
			oSize:AddObject( "VLUNI",  100, 30, .T., .T. ) // Totalmente dimensionavel
			oSize:AddObject( "SEGUN",  100, 30, .T., .T. ) // Totalmente dimensionavel

			oSize:lProp 	:= .T. // Proporcional
			oSize:aMargins 	:= { 3, 3, 3, 3 } // Espaco ao lado dos objetos 0, entre eles 3

			oSize:Process() 	   // Dispara os calculos

			@ oSize:GetDimension("QUANT","LININI") ,oSize:GetDimension("QUANT","COLINI")  BUTTON STR0277 SIZE 70,15 FONT oDlg:oFont ACTION ;
			{|| __READVAR:="M->D1_QUANT"  ,M->D1_QUANT  := 0,cCpoName := StrTran(ReadVar(),"M->",""),oGrade:Show(cCpoName) } OF oDlg PIXEL //"Quantidade"
			@ oSize:GetDimension("VLUNI","LININI") ,oSize:GetDimension("VLUNI","COLINI")  BUTTON STR0278 SIZE 70,15 FONT oDlg:oFont ACTION ;
			{|| __READVAR:="M->D1_VUNIT"  ,M->D1_VUNIT  := 0,cCpoName := StrTran(ReadVar(),"M->",""),oGrade:Show(cCpoName) } OF oDlg PIXEL //"Valor Unit·rio"
			@ oSize:GetDimension("SEGUN","LININI") ,oSize:GetDimension("SEGUN","COLINI")  BUTTON STR0279 SIZE 70,15 FONT oDlg:oFont ACTION ;
			{|| __READVAR:="M->D1_QTSEGUM",M->D1_QTSEGUM:= 0,cCpoName := StrTran(ReadVar(),"M->",""),oGrade:Show(cCpoName) } OF oDlg PIXEL //"Segunda Und Medida"

			ACTIVATE MSDIALOG oDlg ON INIT EnchoiceBar(oDlg,{||oDlg:End()},{||oDlg:End()}) CENTERED

			//Somente realiza a carga do item para o aCols se pelo menos uma celula do D1_QUANT contiver valor
			If oGrade:SomaGrade("D1_QUANT",oGrade:nPosLinO,aCols[nSaveN,nPosQuant]) > 0
				nLenD1Item := Len(SD1->D1_ITEM)
				nLenD1Cod  := Len(SD1->D1_COD)
				nLenAheader:= Len(aHeader)
				For nLinX  := 1 To Len(oGrade:aColsGrade[1])
					For nColY := 2 To Len(oGrade:aHeadGrade[1])
						If oGrade:aColsFieldByName("D1_QUANT",1,nLinX,nColY) <> 0
							//Faz a montagem de uma nova linha em branco no aCols para
							//adicionar novos itens vindos das celulas da Grade
							If lAadd
								aadd(aCols,Array(nLenAheader+1))
								nNewItem   := Len(aCols)
								cNewItem   := StrZero(nNewItem,nLenD1Item)
								nTaitens   := val(cTailItem)+1
								nLenaItens := Len(cTailItem)
								
								For nY := 1 to nLenAheader
									If Trim(aHeader[nY][2]) == "D1_ITEM"
												aCols[nNewItem][nY] := strzero(nTaitens,nLenaItens)
												cTailItem := aCols[nNewItem][nY]
									ElseIf IsHeadRec(aHeader[nY][2])
										aCols[nNewItem][nY] := 0
									ElseIf IsHeadAlias(aHeader[nY][2])
										aCols[nNewItem][nY] := "SD1"
									Else
										aCols[nNewItem][nY] := CriaVar(aHeader[nY][2])
									EndIf
									aCols[nNewItem][nLenAheader+1] := .F.
								Next nY
							Else
								aTailGrad := aTail(aCols)
								cTailItem := aTailGrad[1]
							EndIf

							//Efetua a carga dos itens digitados do grid para o aCols e sincroniza 
							//os novos itens carregando a Matxfis.
							N := nNewItem
							aCols[nNewItem][nPosProd]:= PadR(oGrade:GetNameProd(cProdRef,nLinX,nColY),nLenD1Cod)

							M->D1_COD := aCols[nNewItem][nPosProd]
							MaFisRef("IT_PRODUTO","MT100",M->D1_COD)
							A103IniCpo()														

							aCols[nNewItem][nPosQuant]:= oGrade:aColsFieldByName("D1_QUANT",1,nLinX,nColY)
							M->D1_QUANT := oGrade:aColsFieldByName("D1_QUANT",1,nLinX,nColY)
							A100SegUm()
							MaFisRef("IT_QUANT","MT100",M->D1_QUANT)

							aCols[nNewItem][nPosQtSegum]:= oGrade:aColsFieldByName("D1_QTSEGUM",1,nLinX,nColY)
							M->D1_QTSEGUM := oGrade:aColsFieldByName("D1_QTSEGUM",1,nLinX,nColY)
							A100SegUm()

							aCols[nNewItem][nPosVUnit]:= oGrade:aColsFieldByName("D1_VUNIT",1,nLinX,nColY)
							M->D1_VUNIT := oGrade:aColsFieldByName("D1_VUNIT",1,nLinX,nColY)
							MaFisRef("IT_PRCUNI","MT100",M->D1_VUNIT)

							aCols[nNewItem][nPosTotal]:= NoRound(aCols[nNewItem][nPosQuant] * aCols[nNewItem][nPosVUnit],TamSX3("D1_TOTAL")[2])
							M->D1_TOTAL := aCols[nNewItem][nPosTotal]
							A103Total(M->D1_TOTAL)
							MaFisRef("IT_VALMERC","MT100",M->D1_TOTAL)

							If !lAadd
                                cPrdOrig := aCols[nNewItem][nPosProd]
								lAadd := .T.
							Endif

						EndIf
					Next nColY
				Next nLinX

			Else
				lRet := .F.
			EndIf

			//Restaura os valores originais do N da GetDados, e da Public
			//__READVAR que fora manipulada pela interface de grade.
			N := nSaveN
			__READVAR   := cSaveReadVar
            M->D1_COD   := cPrdOrig

			If cPaisLoc <> "BRA"
				//Atualiza o browse de quantidade de produtos
				AtuLoadQt(.T.)
			EndIf

		Else
			//Para incluir um produto com referencia de grade e necessario estar em uma nova linha da NFE.                                      ≥
			Help(" ",1,"A103PRDGRD")
			lRet := .F.
		EndIf
	Else
		//Se o Produto nao for um produto de grade executa a validacao no SB1
		//carrega o item na MATXFIS e inicializa os campos na getdados.
		dbSelectArea("SB1")
		dbSetOrder(1)
		If !dbSeek(xFilial("SB1")+cProdRef,.F.)
			Help("  ",1,"REGNOIS")
			lRet := .F.
		EndIf

		If lRet
			MaFisRef("IT_PRODUTO","MT100",M->D1_COD)	
			A103IniCpo()					
		Endif
	EndIf
ElseIf lRet
	//Se o Produto nao for um produto de grade executa a validacao no SB1
	//carrega o item na MATXFIS e inicializa os campos na getdados.
	If !ExistBlock("MT103PBLQ")
		lRet := ExistCpo("SB1")
	Else
		//O P.E. MT103PBLQ permite validar se produtos que estao bloqueados, podem
		//ou nao ser utilizados na NFE ao realizar um RETORNO de doctos de Saida.
		DbSelectArea("SB1")
	   	DbSetorder(1)
	   	Dbseek(xFilial("SB1")+M->D1_COD)
	   	lRet:=iif(eof(),.f.,.t.)
	EndIf
	If lRet		
		MaFisRef("IT_PRODUTO","MT100",M->D1_COD)
		A103IniCpo()
	Endif
EndIf

If lRet //para os itens que foram distribuidos pelo WMS, n„o permite alterar o codigo
	If lWmsNew .And. IsInCallStack("MATA103") .AND. l103Class .AND. IntWMS() .AND. n <= Len(aColsOrig)
		lRet := WMSVldD07(3,aColsOrig,n,aHeader)
	EndIf
EndIf

If lRet 
	//Valida a O.P quando integrado com o mÛdulo de manutenÁ„o de ativos
	If IsInCallStack("MATA103") .And. nPosOp > 0 .And. nPosQuant > 0 .And. nPosOs > 0 .And. FindFunction("NGAPAGD1OR")
		If !NGAPAGD1OR(aCols[n,nPosOs],aCols[n,nPosOp],M->D1_COD,aCols[n,nPosQuant])
			lRet := .F.
		EndIf
	EndIf
EndIf

If lRet .And. ChkFile("DHR") .And. FwIsInCallStack("MATA103") .And. ; //Vincula natureza rendimento automatica
!(FwIsInCallStack("MATA140") .Or. FwIsInCallStack("MATA116") .Or. FwIsInCallStack("MATA119"))
	A103NatRen(aHeadDHR,aColsDHR,.T.,.F.,,M->D1_COD)
Endif

RestArea(aArea)

Return(lRet)

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103VldGrd≥Autor  ≥Alexandre Inacio Lemes ≥ Data ≥22/08/2007 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descricao ≥ Validacao dos itens do Grid na grade de produtos            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ Nenhum                                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ .T. se Valido e .F. se Invalido                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥Objeto de Grade do MATA103                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103VldGrd()

Local lValido := .F.

//Se Houver necessidade de novas validacoes na entrada de dados nas
//celulas do Grid elas deverao ser inseridas nessa funcao.
If Positivo()
	lValido := .T.
EndIf

Return lValido

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥a103AjuICM≥ Autor ≥ Gustavo G. Rueda      ≥ Data ≥13/12/2007≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Funcao para atualizar o objeto do mata103 (TFOLDER) com as  ≥±±
±±≥          ≥ informacoes referentes ao lancamento fiscal.               ≥±±
±±≥          ≥                                                            ≥±±
±±≥          ≥Chamada: MAFISALT da MATXFIS                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T.                                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥nZ -> Numero do item do documento fiscal.                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function a103AjuICM(nZ)
Local nI			:=	0
Local aGrava		:=	{0,"","","1",0,0,0}
Local nPos			:=	0
Local cSeq			:=	"000"
Local aBkpaCls		:=	{}
Local lApagTudo		:=	.T.
Local nTesI			:=	0
Local nTesF			:=	0
Local aRetMaFisAjIt := {}
Local nJ			:= 0
Local ProcCDV		:= Type("oLancCDV") == 'O'
local lNewCDA 	    := CDA->(FieldPos("CDA_VLOUTR")) > 0 .And. CDA->(FieldPos("CDA_TXTDSC")) > 0 .And. CDA->(FieldPos("CDA_CODCPL")) > 0 .And. CDA->(FieldPos("CDA_CODMSG")) > 0;
						.And. CDA->(FieldPos("CDA_REGCAL")) > 0 .And. CDA->(FieldPos("CDA_OPALIQ")) > 0 .And. CDA->(FieldPos("CDA_OPBASE")) > 0 .And. CDA->(FieldPos("CDA_AGRLAN")) > 0 

Local nPosIt		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_NUMITE" } )
Local nPosSeq		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_SEQ" } )
Local nPosCLan		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_CODLAN" } )
Local nPosCSis		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_CALPRO" } )
Local nPosGuia		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_GUIA" } )
Local nPosBase		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_BASE" } )
Local nPosAliq		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_ALIQ" } )
Local nPosValor		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_VALOR" } )
Local nPosTpLanc	:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_TPLANC" } )
Local nPosVl197		:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_VL197" } )
Local nPosDesLan	:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_CLANC" } )
Local nPosCodRef	:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_CODREF" } )
Local nPosOrigem	:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_ORIGEM" } )
Local nPosIFComp	:= aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_IFCOMP" } )
Local nPosVOut		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_VLOUTR" } ), 0)
Local nPosTxDes		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_TXTDSC" } ), 0)
Local nPosCodCp		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_CODCPL" } ), 0)
Local nPosCodms		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_CODMSG" } ), 0)
Local nRegCalc		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_REGCAL" } ), 0)
Local nOpAliq		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_OPALIQ" } ), 0)
Local nOpBase		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_OPBASE" } ), 0)
Local nAgrLan		:= Iif(lNewCDA, aScan( oLancApICMS:aHeader, {|aX| aX[2] == "CDA_AGRLAN" } ), 0)
Local nTotalCols	:= Len(oLancApICMS:aHeader)

Default	nZ	:=	0	//Por enquanto soh vem ZERO quando se tratar de uma nota fiscal que estah sendo classificada.

nTesI	:=	Iif (nZ==0, 1, nZ)
nTesF	:=	Iif (nZ==0, Len(aCols), nZ)

For nZ := nTesI To nTesF

	aRetMaFisAjIt	:=	MaFisAjIt(nZ)
	aGrava	:=	{}
	
	For nJ := 1 to Len(aRetMaFisAjIt)
		iF Len(aRetMaFisAjIt[nJ]) >= 14 .And. aRetMaFisAjIt[nJ,14] == "4"
			Loop
		Endif
		aAdd(aGrava, aRetMaFisAjIt[nJ])				
	Next nJ	

	If Len(aGrava)>0

		If nPosIt>0 .And. nPosSeq>0 .And. nPosCLan>0 .And. nPosCSis>0
			For nI := Len(oLancApICMS:aCols) To 1 Step -1
				If (!oLancApICMS:aCols[nI,Len(oLancApICMS:aCols[nI])] .And. ( MaFisRet(nZ,"IT_ITEM")==oLancApICMS:aCols[nI,nPosIt] .And. oLancApICMS:aCols[nI,nPosCSis] == '1' ) ) .Or.;
					(Empty(oLancApICMS:aCols[nI,nPosIt]) .And. Len(oLancApICMS:aCols)==1)
					aDel(oLancApICMS:aCols,nI)
					aSize(oLancApICMS:aCols,Len(oLancApICMS:aCols)-1)
				EndIf
			Next nI

			If Len(oLancApICMS:aCols)>0
				aBkpaCls	:=	aClone(oLancApICMS:aCols)
				aSort(aBkpaCls,,,{|aX,aY| aX[nPosSeq]<aY[nPosSeq]})
				cSeq	:=	aBkpaCls[Len(aBkpaCls),nPosSeq]
			EndIf

			For nI := 1 To Len(aGrava)
				cSeq	:=	Soma1(cSeq)
				nPos	:=	aScan(oLancApICMS:aCols,{|aX| aX[nPosIt]==aGrava[nI,1] .And.;
														 aX[nPosCLan]==aGrava[nI,2] .And.;
														 aX[nPosCSis]==aGrava[nI,3] .And.;
														 aX[nPosCSis]==aGrava[nI,7] .And.;
														 aX[nTotalCols + 1]==.F.})
				If nPos>0
					oLancApICMS:aCols[1,nPosBase]	+=	aGrava[nI,4]
					oLancApICMS:aCols[1,nPosAliq]	:=	aGrava[nI,5]
					oLancApICMS:aCols[1,nPosValor]	+=	aGrava[nI,6]
					If nPosVOut > 0 .And. Len(aGrava[nI]) > 17 
						oLancApICMS:aCols[1,nPosVOut]	+=	aGrava[nI,21]
					Endif
				Else
					aAdd(oLancApICMS:aCols,array( nTotalCols + 1 ))
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosTpLanc] := aGrava[nI,9]
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosVl197] := aGrava[nI,10]
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosDesLan] := aGrava[nI,11]							

					If Len(aGrava[nI]) >= 12 .And. nPosCodRef > 0
						oLancApICMS:aCols[len(oLancApICMS:aCols),nPosCodRef]:= aGrava[nI,12]
					EndIf

					If Len(aGrava[nI]) >= 13 .And. nPosGuia > 0
						oLancApICMS:aCols[len(oLancApICMS:aCols),nPosGuia]:= aGrava[nI,13]
					EndIf
					
					If Len(aGrava[nI]) >= 14 .And. nPosOrigem > 0
						oLancApICMS:aCols[len(oLancApICMS:aCols),nPosOrigem]:= aGrava[nI,14]
					EndIf
					oLancApICMS:aCols[len(oLancApICMS:aCols),nTotalCols + 1] := .F.

					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosIt] :=  aGrava[nI,1]
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosSeq] :=  cSeq
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosCLan] :=  aGrava[nI,2]
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosCSis] :=  aGrava[nI,3]
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosBase] :=  aGrava[nI,4]
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosAliq] :=  aGrava[nI,5]
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosValor] :=  Round( aGrava[nI,6], 2 )
					oLancApICMS:aCols[len(oLancApICMS:aCols),nPosIFComp] :=  aGrava[nI,8]
										
					If nPosVOut > 0 .And. nPosTxDes > 0 .And. nPosCodCp > 0 .And. nPosCodms > 0 .And. Len(aGrava[nI]) > 17
						oLancApICMS:aCols[len(oLancApICMS:aCols),nPosVOut]	 :=	Round( aGrava[nI,21], 2 ) 
						oLancApICMS:aCols[len(oLancApICMS:aCols),nPosTxDes]  :=  aGrava[nI,18]
						oLancApICMS:aCols[len(oLancApICMS:aCols),nPosCodCp]	 :=  aGrava[nI,19]
						oLancApICMS:aCols[len(oLancApICMS:aCols),nPosCodms]  :=  aGrava[nI,20]

						oLancApICMS:aCols[len(oLancApICMS:aCols),nRegCalc]  :=  aGrava[nI,22]
						oLancApICMS:aCols[len(oLancApICMS:aCols),nOpAliq]   :=  aGrava[nI,23]
						oLancApICMS:aCols[len(oLancApICMS:aCols),nOpBase]   :=  aGrava[nI,24]
						oLancApICMS:aCols[len(oLancApICMS:aCols),nAgrLan]   :=  aGrava[nI,25]
					Endif
				EndIf
			Next nI
		EndIf
	Else
		If nPosIt>0
			For nI := Len(oLancApICMS:aCols) To 1 Step -1
				If (oLancApICMS:aCols[nI,nPosIt]== MaFisRet(nZ,"IT_ITEM") .And. oLancApICMS:aCols[nI,nPosCSis] == '1')  .Or.;
					(Empty(oLancApICMS:aCols[nI,nPosIt]) .And. Len(oLancApICMS:aCols)==1  )
					aDel(oLancApICMS:aCols,nI)
					aSize(oLancApICMS:aCols,Len(oLancApICMS:aCols)-1)
				Else
					lApagTudo	:=	.F.
				EndIf
			Next nI

			If lApagTudo
				oLancApICMS:aCols:=	{Array( nTotalCols + 1 )}
				oLancApICMS:aCols[1, nTotalCols + 1]:=	.F.

				For nI := 1 To nTotalCols
					If oLancApICMS:aHeader[nI,10]#"V"
						oLancApICMS:aCols[1,nI]	:=	CriaVar(oLancApICMS:aHeader[nI,2])
					EndIf

					If "_SEQ"$oLancApICMS:aHeader[nI,2]
						oLancApICMS:aCols[1,nI]	:=	StrZero(1,oLancApICMS:aHeader[nI,4])
					EndIf
				Next
			EndIf
		EndIf
	EndIf
	
	If ProcCDV
		a017AjuICM(nZ)
	Endif
Next nZ

If ProcCDV
	oLancCDV:Refresh()
Endif
oLancApICMS:Refresh()
Return

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥a103GrvCDA≥ Autor ≥ Gustavo G. Rueda      ≥ Data ≥13/12/2007≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Funcao de gravacao/exclusao das informacoes do documento    ≥±±
±±≥          ≥ fiscal referente ao lancamento fiscal da apuracao de icms. ≥±±
±±≥          ≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T.                                                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥lExclui -> Flag que indica exclusao do registro.            ≥±±
±±≥          ≥cTipMov -> (E)nttrada ou (S)aida                            ≥±±
±±≥          ≥cEspecie -> Especie do documento fiscal para montar a chave.≥±±
±±≥          ≥cFormul -> Indicador de formulario proprio (S)im/(N)ao para ≥±±
±±≥          ≥ montar a chave.                                            ≥±±
±±≥          ≥cNFiscal -> Numero da nota fiscal para montar a chave.      ≥±±
±±≥          ≥cSerie -> Serie do documento fiscal para montar a chave.    ≥±±
±±≥          ≥cForn -> Codigo do fornecedor para montar a chave.          ≥±±
±±≥          ≥cLoja -> Codigo da loja do fornecedor para montar a chave.  ≥±±
±±≥          ≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function a103GrvCDA(lExclui,cTipMov,cEspecie,cFormul,cNFiscal,cSerie,cForn,cLoja,aInfApurICMS)
Local	lRet	:=	.T.
Local	aArea	:=	GetArea()
Local	nI		:=	0
Local	nPosIte	:=	0
Local	nPosSeq	:=	0
Local	nTamCdaNu := TamSx3("CDA_NUMITE")[1]
Local	nTamCdaNt := TamSx3("CDA_NUMERO")[1]
Local	nTamCdaSr := TamSx3("CDA_SERIE")[1]
Local	nTamCdaEs := TamSx3("CDA_ESPECI")[1]
Local	cTPLanc	:=	0
Local	cSerId  := ""
Local 	cVL197  := ""
Local	cCmp0460:= ""
Local 	lCmp0460:=	CDA->(ColumnPos("CDA_CLANC")) > 0
Local	cCodRef := ""
Local	cCodOrig := ""
Local	l920Auto :=  (Type("l920Auto") <> "U" .And. (l920Auto))
Local	lAuto116 :=  (Type("l116Auto") <> "U" .And. (l116Auto))
Local	lAuto103 :=  (Type("l103Auto") <> "U" .And. (l103Auto))
Local	lCodRef	:=	CDA->(ColumnPos("CDA_CODREF")) > 0
Local   lVL197	:=  CDA->(ColumnPos("CDA_VL197")) > 0
Local	lIfcomp :=	CDA->(ColumnPos("CDA_IFCOMP")) > 0
Local	lTplanc :=	CDA->(ColumnPos("CDA_TPLANC")) > 0
Local	lCodOrig :=	CDA->(FieldPos("CDA_ORIGEM")) > 0
Local 	lGuia 	 := CDA->(FieldPos("CDA_GUIA")) > 0
local 	lNewCDA  := CDA->(FieldPos("CDA_VLOUTR")) > 0 .And. CDA->(FieldPos("CDA_TXTDSC")) > 0 .And. CDA->(FieldPos("CDA_CODCPL")) > 0 .And. CDA->(FieldPos("CDA_CODMSG")) > 0;
						.And. CDA->(FieldPos("CDA_REGCAL")) > 0 .And. CDA->(FieldPos("CDA_OPALIQ")) > 0 .And. CDA->(FieldPos("CDA_OPBASE")) > 0 .And. CDA->(FieldPos("CDA_AGRLAN")) > 0 
Local   cGuia := ""
Local   aRetMaFisAjIt
Local   nJ		   
Local   nPosAuto
Local   lCDATPNOTA := .F.
Local 	cCodDes    := ""
Local 	cCodObs    := ""
Local 	cCodOLan   := ""
Local 	nValOut    := 0
Local 	cRegCalc   := ""
Local 	cOpBase    := ""
Local 	cOpAliq    := ""
Local   cAgrLan	   := ""

Default aInfApurICMS := {}

//Ajusta quando numero da nota for menor que tamanho do campo F1_DOC
cNFiscal	:= Padr(cNFiscal,TamSX3("F1_DOC")[1])

If cTipMov == "E"
	cSerId := SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)
Else
	cSerId := SerieNfId("SF2",4,"F2_SERIE",d920Emis,cEspecie,cSerie)
EndIf

cFormul	:=	IIF(cFormul=="S","S"," ")

If lAuto103 .Or. l920Auto
	//Gerando informacoes dos lanctos da apuracao de ICMS
	aRetMaFisAjIt := MaFisAjIt(,2)
	If !Empty(aRetMaFisAjIt)
		For nJ := 1 to Len(aRetMaFisAjIt)
			iF Len(aRetMaFisAjIt[nJ]) >= 14 .And. aRetMaFisAjIt[nJ,14] == "4"
				Loop
			Endif
			aAdd(aInfApurICMS, {})
			nPosAuto :=	Len (aInfApurICMS)
			aAdd (aInfApurICMS[nPosAuto], aRetMaFisAjIt[nJ])
		Next nJ
	EndIf
EndIf

If Type("oLancApICMS")= "O" .Or. lAuto116 .OR. lAuto103 .Or. l920Auto

	dbSelectArea("CDA")
	CDA->(dbSetOrder(1))

	If lExclui
		If CDA->(MsSeek(xFilial("CDA")+cTipMov+cEspecie+cFormul+cNFiscal+cSerId+cForn+cLoja))
			While !CDA->(Eof()) .And.;
				xFilial("CDA")+cTipMov+cEspecie+cFormul+cNFiscal+cSerId+cForn+cLoja==;
				CDA->(CDA_FILIAL+CDA_TPMOVI+CDA_ESPECI+CDA_FORMUL+CDA_NUMERO+CDA_SERIE+CDA_CLIFOR+CDA_LOJA)

				RecLock("CDA",.F.)
				CDA->(dbDelete())
				MsUnLock()
				CDA->(FkCommit())
				CDA->(dbSkip())
			End
		EndIf
	Else
		lCDATPNOTA := CDA->( FieldPos("CDA_TPNOTA") ) > 0

		If lAuto116 .OR. lAuto103 .Or. l920Auto
			If Len(aInfApurICMS) > 0
				For nI := 1 To Len(aInfApurICMS)
					If Empty(aInfApurICMS[nI][1][2])
						Loop
					EndIf

					cNumItem :=	aInfApurICMS[nI][1][1]
					cCodLan	 := aInfApurICMS[nI][1][2]
					cCalPro	 :=	aInfApurICMS[nI][1][3]
					nBase	 :=	aInfApurICMS[nI][1][4]
					nAliq	 :=	aInfApurICMS[nI][1][5]
					nValor	 :=	aInfApurICMS[nI][1][6]
					cNumSeq	 := aInfApurICMS[nI][1][7]
					cIFCOMP	 := aInfApurICMS[nI][1][8]
					cTPLanc	 :=	aInfApurICMS[nI][1][9]
					cVL197   := aInfApurICMS[nI][1][10]
					cCmp0460 := aInfApurICMS[nI][1][11]

					If Len(aInfApurICMS[nI][1]) >= 12
						cCodRef  := aInfApurICMS[nI][1][12]
					Endif

					If Len(aInfApurICMS[nI][1]) >= 13
						cGuia  := aInfApurICMS[nI][1][13]
					Endif

					If Len(aInfApurICMS[nI][1]) >= 14
						cCodOrig  := aInfApurICMS[nI][1][14]
					Endif

					If lNewCDA .And. Len(aInfApurICMS[nI][1]) > 17 						
						cCodDes	 := aInfApurICMS[nI][1][18]
						cCodObs	 := aInfApurICMS[nI][1][19]
						cCodOLan := aInfApurICMS[nI][1][20]
						nValOut	 := aInfApurICMS[nI][1][21]
						cRegCalc := aInfApurICMS[nI][1][22]
						cOpBase  := aInfApurICMS[nI][1][23]
						cOpAliq  := aInfApurICMS[nI][1][24]
						cAgrLan	 := aInfApurICMS[nI][1][25]
					Endif		

					If CDA->(MsSeek(xFilial("CDA")+cTipMov+Padr(cEspecie,5)+cFormul+PadR(cNFiscal,9)+Padr(cSerie,3)+cForn+cLoja+PadR(cNumItem,nTamCdaNu)+cNumSeq))
						RecLock("CDA",.F.)

						If lCDATPNOTA .AND. CDA->CDA_TPNOTA <> cTipo
							CDA->CDA_TPNOTA := cTipo
						EndIf

					Else
						RecLock("CDA",.T.)
						CDA->CDA_FILIAL	:=	xFilial("CDA")
						CDA->CDA_TPMOVI	:=	cTipMov
						CDA->CDA_ESPECI	:=	cEspecie
						CDA->CDA_FORMUL	:=	cFormul
						CDA->CDA_NUMERO	:=	cNFiscal
						SerieNfId("CDA",1,"CDA_SERIE",Iif( cTipMov == "E" , dDEmissao , d920Emis ) ,cEspecie,cSerie)
						CDA->CDA_CLIFOR	:=	cForn
						CDA->CDA_LOJA	:=	cLoja
						CDA->CDA_NUMITE	:=	cNumItem
						CDA->CDA_SEQ	:=	cNumSeq
						If lCDATPNOTA
							CDA->CDA_TPNOTA :=  cTipo
						EndIf
					EndIf

					CDA->CDA_CODLAN	:=	cCodLan
					CDA->CDA_CALPRO	:=	cCalPro
					CDA->CDA_BASE	:=	nBase
					CDA->CDA_ALIQ	:=	nAliq
					CDA->CDA_VALOR	:=	nValor

					If lIfcomp
						CDA->CDA_IFCOMP	:=	cIFCOMP
					EndIf

					If lTplanc
						CDA->CDA_TPLANC	:=	cTPLanc
					EndIf
					If lVL197
						CDA->CDA_VL197	:=	cVL197
					Endif
					If lCmp0460
						CDA->CDA_CLANC :=	cCmp0460
					Endif
					If lCodRef
						CDA->CDA_CODREF :=	cCodRef
					Endif
					If lGuia
						CDA->CDA_GUIA :=	cGuia
					EndIf
					If lCodOrig
						CDA->CDA_ORIGEM :=	cCodOrig
					Endif

					If lNewCDA						
						CDA->CDA_TXTDSC := cCodDes						
						CDA->CDA_CODMSG := cCodObs
						CDA->CDA_CODCPL := cCodOLan
						CDA->CDA_VLOUTR := nValOut						
						CDA->CDA_REGCAL	:= cRegCalc					
						CDA->CDA_OPALIQ	:= cOpBase						
						CDA->CDA_OPBASE	:= cOpAliq
						CDA->CDA_AGRLAN := cAgrLan
					Endif	

					MsUnLock()
					CDA->(FkCommit())
				Next nI
			Endif
		Else
			For nI := 1 To Len(oLancApICMS:aCols)
				If oLancApICMS:aCols[nI,Len(oLancApICMS:aCols[nI])]
					Loop
				EndIf

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CODLAN"})
				cCodLan	:=	oLancApICMS:aCols[nI,nPos]
				If Empty(cCodLan)
					Loop
				EndIf

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_NUMITE"})
				cNumItem:=	oLancApICMS:aCols[nI,nPos]

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_SEQ"})
				cNumSeq	:=	oLancApICMS:aCols[nI,nPos]

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CALPRO"})
				cCalPro	:=	oLancApICMS:aCols[nI,nPos]

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_BASE"})
				nBase	:=	oLancApICMS:aCols[nI,nPos]

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_ALIQ"})
				nAliq	:=	oLancApICMS:aCols[nI,nPos]

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_VALOR"})
				nValor	:=	oLancApICMS:aCols[nI,nPos]

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_IFCOMP"})
				cIFCOMP	:=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_TPLANC"})
				cTPLanc	:=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_VL197"})
				cVL197	:=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

				If lCmp0460
					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CLANC"})
					cCmp0460	:=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])
				Endif
				IF lCodRef
					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CODREF"})
					cCodRef	:=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])
				Endif

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_GUIA"})
				cGuia	:=	Iif(nPos==0,"2",oLancApICMS:aCols[nI,nPos])

				nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_ORIGEM"})
				cCodOrig :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

				If lNewCDA
					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_TXTDSC"})
					cCodDes :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])	

					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CODMSG"})
					cCodObs :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])				

					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CODCPL"})
					cCodOLan :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_VLOUTR"})
					nValOut :=	Iif(nPos==0,0,oLancApICMS:aCols[nI,nPos])

					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_REGCAL"})
					cRegCalc :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_OPALIQ"})
					cOpBase :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_OPBASE"})
					cOpAliq :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

					nPos:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_AGRLAN"})
					cAgrLan :=	Iif(nPos==0,"",oLancApICMS:aCols[nI,nPos])

				Endif

				If CDA->(MsSeek(xFilial("CDA")+cTipMov+Padr(cEspecie,nTamCdaEs)+cFormul+PadR(cNFiscal,nTamCdaNt)+Padr(cSerie,nTamCdaSr)+cForn+cLoja+PadR(cNumItem,nTamCdaNu)+cNumSeq))
					RecLock("CDA",.F.)
					
					If lCDATPNOTA .AND. CDA->CDA_TPNOTA <> cTipo
						CDA->CDA_TPNOTA := cTipo
					EndIf
				Else
					RecLock("CDA",.T.)
					CDA->CDA_FILIAL	:=	xFilial("CDA") 
					CDA->CDA_TPMOVI	:=	cTipMov
					CDA->CDA_ESPECI	:=	cEspecie
					CDA->CDA_FORMUL	:=	cFormul
					CDA->CDA_NUMERO	:=	cNFiscal
					SerieNfId("CDA",1,"CDA_SERIE",Iif( cTipMov == "E" , dDEmissao , d920Emis ) ,cEspecie,cSerie)
					CDA->CDA_CLIFOR	:=	cForn
					CDA->CDA_LOJA	:=	cLoja
					CDA->CDA_NUMITE	:=	cNumItem
					CDA->CDA_SEQ	:=	cNumSeq
					If lCDATPNOTA
						CDA->CDA_TPNOTA :=  cTipo
					EndIf
				EndIf

				CDA->CDA_CODLAN	:=	cCodLan
				CDA->CDA_CALPRO	:=	cCalPro
				CDA->CDA_BASE	:=	nBase
				CDA->CDA_ALIQ	:=	nAliq
				CDA->CDA_VALOR	:=	nValor
				CDA->CDA_IFCOMP	:=	cIFCOMP
				CDA->CDA_TPLANC	:=	cTPLanc
				If cPaisLoc == "BRA"
					CDA->CDA_VL197	:=	cVL197
					CDA->CDA_CLANC	:=	cCmp0460
				Endif
				IF lCodRef
					CDA->CDA_CODREF :=	cCodRef
				Endif
				If lGuia
					CDA->CDA_GUIA := cGuia
				EndIf
				If lCodOrig
					CDA->CDA_ORIGEM :=	cCodOrig
				Endif

				If lNewCDA						
					CDA->CDA_TXTDSC := cCodDes						
					CDA->CDA_CODMSG := cCodObs
					CDA->CDA_CODCPL := cCodOLan
					CDA->CDA_VLOUTR := nValOut						
					CDA->CDA_REGCAL	:= cRegCalc					
					CDA->CDA_OPALIQ	:= cOpBase						
					CDA->CDA_OPBASE	:= cOpAliq
					CDA->CDA_AGRLAN := cAgrLan
				Endif	
				
				MsUnLock()
				CDA->(FkCommit())
			Next nI

			//Tratamento para deletar os registros que nao foram reaproveitados acima no caso de reutilizacao de numeracao de nota
			If CDA->(MsSeek(xFilial("CDA")+cTipMov+cEspecie+cFormul+cNFiscal+cSerId+cForn+cLoja))
				nPosIte:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_NUMITE"})
				nPosSeq:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_SEQ"})
				While !CDA->(Eof()) .And.;
					CDA->(CDA_FILIAL+CDA_TPMOVI+CDA_ESPECI+CDA_FORMUL+CDA_NUMERO+CDA_SERIE+CDA_CLIFOR+CDA_LOJA)==;
					xFilial("CDA")+cTipMov+cEspecie+cFormul+cNFiscal+cSerId+cForn+cLoja

					If aScan(oLancApICMS:aCols,{|aX|PadR(aX[nPosIte],TamSx3("CDA_NUMITE")[1])==CDA->CDA_NUMITE .And. aX[nPosSeq]==CDA->CDA_SEQ})==0
						RecLock("CDA",.F.)
						dbDelete()
						MsUnLock()
						CDA->(FkCommit())
					EndIf

					CDA->(dbSkip())
				End
			EndIf
		Endif
	EndIf
EndIf

RestArea(aArea)
Return lRet

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥GetLanc   ≥ Autor ≥ Gustavo G. Rueda      ≥ Data  ≥13/12/2007≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Quando estiver utilizando o flag de whenget(abre nota fiscal)≥±±
±±≥          ≥ com valores a serem alterados.(funcao retornar) utilizo esta≥±±
±±≥          ≥ funcao para carregar os lancamentos das TES do acols da NFE.≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T.                                                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥Nenhum                                                       ≥±±
±±≥          ≥                                                             ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao efetuada                          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                             ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Static Function GetLanc()
Local	nPosTes		:=	0
Local	nZ			:=	0

If Len(aHeader)>0
	nPosTes	:=	GetPosSD1("D1_TES")
    If Len(aCols)>0 .And. nPosTes>0
    	For nZ := 1 To Len(aCols)
			a103AjuICM(nZ)
		Next nI
    EndIf
EndIf

Return

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥A103TrfSld≥ Autor ≥ Microsiga S/A         ≥ Data ≥23/03/2008≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descriáao ≥Funcao utilizada para transferir o saldo classificado para  ≥±±
±±≥          ≥o Armazem de Transito definido pelo parametro MV_LOCTRAN.   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥lDeleta - .T. = Exclusao NFE                                ≥±±
±±≥          ≥          .F. = Classificao da Pre-Nota                     ≥±±
±±≥          ≥nTipo   - 1 = Transferencia para Armazem de Transito        ≥±±
±±≥          ≥          2 = Retorno do saldo para o armazem orginal       ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Static Function A103TrfSld(lDeleta,nTipo)

Local aAreaAnt   := GetArea()
Local aAreaSF4   := SF4->(GetArea())
Local aAreaSD1   := SD1->(GetArea())
Local aAreaSD3   := SD3->(GetArea())
Local aAreaSB2   := SD3->(GetArea())
Local cLocTran   := SuperGetMV("MV_LOCTRAN",.F.,"95")
Local cLocCQ     := SuperGetMV("MV_CQ",.F.,"98")
Local aArray     := {}
Local aStruSD3   := {}
Local cSeek      := ''
Local cQuery     := ''
Local cAliasSD3  := 'SD3'
Local cChave     := Space(TamSX3("D3_CHAVE")[1])
Local nX         := 0
Local lQuery     := .F.
Local lContinua  := .F.
Local lVldPE  	 := .T.
Local lTransit   := .F.

Default lDeleta     := .F.
Default nTipo       := 1

Private lMsErroAuto := .F.

If FindFunction("A103xETrSl")
	A103xETrSl (lDeleta,nTipo)
	Return NIL
EndIf

//Ponto de Entrada para validar se permite a operacao
If ExistBlock("A103TRFVLD")
	lVldPE:= ExecBlock("A103TRFVLD",.F.,.F.,{nTipo,lDeleta})
	If Valtype (lVldPE) != "L"
		lVldPE:= .T.
	EndIf
EndIf

//Remessa para o Armazem de Transito
If nTipo == 1 .And. lVldPE
		If !Localiza(SD1->D1_COD) .And. Empty(SD1->D1_OP) .And. AllTrim(SD1->D1_LOCAL) # AllTrim(cLocCQ)
			dbSelectArea("SF4")
			dbSetOrder(1)
			//-- Tratamento para Transferencia de Saldos
		If cPaisLoc == "BRA"
			If dbSeek(xFilial("SF4")+SD1->D1_TES) .And. SF4->F4_ESTOQUE == 'S' .And. ;
	           SF4->F4_TRANSIT == 'S' .And. SF4->F4_CODIGO <= '500'
				//Estorno da transferencia para o Armazem de Terceiros
				If lDeleta 
					if !Empty(SD1->D1_TRANSIT)
						lTransit:=.T.
					EndIf
					//-- Retira o Flag que indica produto em transito
					RecLock("SD1",.F.)
					SD1->D1_TRANSIT := " "
					MsUnLock()
					lMsErroAuto := .F.
					cSeek:=xFilial("SD3")+SD1->D1_NUMSEQ+cChave+SD1->D1_COD

						aStruSD3 := SD3->(dbStruct())
						//Selecionar os registros da SD3 pertencentes a movimentacao de transferencia
						//e recebimento do armazem de transito. Pode ser que a nota ja tenha sido recebida
						//atraves do botao "Docto. em transito" e entao o saldo do armazem de transito tambem
						//deve ser estornado. Primeiro as saidas, depois as entradas.
						cQuery := "SELECT D3_FILIAL, D3_COD, D3_LOCAL, D3_NUMSEQ, D3_CF, D3_TM, D3_ESTORNO "
						cQuery +=  " FROM "+RetSQLTab('SD3')
						cQuery += " WHERE D3_FILIAL = '"+xFilial("SD3")+"' "
						cQuery +=   " AND D_E_L_E_T_  = ' ' "
						cQuery +=   " AND D3_ESTORNO <> 'S' "
						cQuery += 	" AND D3_COD      = '"+SD1->D1_COD+"' "
						cQuery += 	" AND D3_NUMSEQ   = '"+SD1->D1_NUMSEQ+"' "
						If !lTransit
							cQuery += 	" AND D3_LOCAL = '"+cLocTran+"' "
						EndIf 
						cQuery += " ORDER BY D3_FILIAL, D3_COD, D3_TM DESC "

						//--Executa a Query
						lQuery    := .T.
						cAliasSD3 := GetNextAlias()
						cQuery    := ChangeQuery( cQuery )
						DbUseArea( .T., 'TOPCONN', TcGenQry(,,cQuery), cAliasSD3, .T., .F. )
						For nX := 1 To Len(aStruSD3)
							If aStruSD3[nX,2]<>"C"
								TcSetField(cAliasSD3,aStruSD3[nX,1],aStruSD3[nX,2],aStruSD3[nX,3],aStruSD3[nX,4])
							EndIf
						Next nX

					Do While !(cAliasSD3)->(Eof()) .And. cSeek == xFilial("SD3")+(cAliasSD3)->D3_NUMSEQ+cChave+(cAliasSD3)->D3_COD
						//-- Nao considerar estornos
						If (cAliasSD3)->D3_ESTORNO == 'S'
							(cAliasSD3)->(dbSkip())
							Loop
						EndIf
						aAdd(aArray,{{"D3_FILIAL"	,(cAliasSD3)->D3_FILIAL , NIL},;
									 {"D3_COD"		,(cAliasSD3)->D3_COD	, NIL},;
								     {"D3_LOCAL"	,(cAliasSD3)->D3_LOCAL	, NIL},;
									 {"D3_NUMSEQ"	,(cAliasSD3)->D3_NUMSEQ , NIL},;
									 {"D3_CF"		,(cAliasSD3)->D3_CF     , NIL},;
									 {"D3_TM"		,(cAliasSD3)->D3_TM     , NIL},;
									 {"INDEX"		,3						, NIL} })

						(cAliasSD3)->(dbSkip())
					EndDo

					// Ordenar o vetor para que as saidas sejam estornadas primeiro
					aSort(aArray,,,{|x,y| x[1,2]+x[2,2]+x[5,2] > y[1,2]+y[2,2]+y[5,2]})

					// Percorre todo o vetor com os registros a estornar
					For nX := 1 to Len(aArray)

						// Se for movimento de entrada e do armazem de transito
						If (aArray[nX][6][2] <= "500") .And. (aArray[nX][3][2] == cLocTran)
							//-- Desbloqueia o armazem de terceiro
							dbSelectArea("SB2")
							dbSetOrder(1)
							If dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
								RecLock("SB2",.F.)
								Replace B2_STATUS With "1"
								MsUnLock()
							EndIf
						EndIf

						MSExecAuto({|x,y| MATA240(x,y)},aArray[nX],5) // Operacao de estorno do movimento interno (SD3)

						//-- Tratamento de erro para rotina automatica
						If lMsErroAuto
							DisarmTransaction()
							MostraErro()
							Break
						EndIf

						// Se for movimento de entrada e do armazem de transito
						If (aArray[nX][6][2] <= "500") .And. (aArray[nX][3][2] == cLocTran)
							//-- Bloqueia o armazem de terceiro
							dbSelectArea("SB2")
							dbSetOrder(1)
							If dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
								RecLock("SB2",.F.)
								Replace B2_STATUS With "2"
								MsUnLock()
							EndIf
						EndIf
					Next nX

					If lQuery
						//--Fecha a area corrente
						dbSelectArea(cAliasSD3)
						dbCloseArea()
						dbSelectArea("SD3")
					EndIf

				//Transferencia para o Armazem de Terceiros
				ElseIf !lDeleta
					//-- Grava Flag que indica produto em transito
					RecLock("SD1",.F.)
					SD1->D1_TRANSIT := "S"
					MsUnLock()
					//-- Requisita o produto do armazem origem (Valorizado)
					dbSelectArea("SB2")
					dbSetOrder(1)
					If dbSeek(xFilial("SB2")+SD1->D1_COD+SD1->D1_LOCAL)
						RecLock("SD3",.T.)
						SD3->D3_FILIAL	:= xFilial("SD3")
						SD3->D3_COD		:= SD1->D1_COD
						SD3->D3_QUANT	:= SD1->D1_QUANT
						SD3->D3_TM		:= "999"
						SD3->D3_OP		:= SD1->D1_OP
						SD3->D3_LOCAL	:= SD1->D1_LOCAL
						SD3->D3_DOC		:= SD1->D1_DOC
						SD3->D3_EMISSAO	:= SD1->D1_DTDIGIT
						SD3->D3_NUMSEQ	:= SD1->D1_NUMSEQ
						SD3->D3_UM		:= SD1->D1_UM
						SD3->D3_GRUPO	:= SD1->D1_GRUPO
						SD3->D3_TIPO	:= SD1->D1_TP
						SD3->D3_SEGUM	:= SD1->D1_SEGUM
						SD3->D3_CONTA	:= SD1->D1_CONTA
						SD3->D3_CF		:= "RE6"
						SD3->D3_QTSEGUM	:= SD1->D1_QTSEGUM
						SD3->D3_USUARIO	:= SubStr(cUsuario,7,15)
						SD3->D3_CUSTO1	:= SD1->D1_CUSTO
						SD3->D3_CUSTO2	:= SD1->D1_CUSTO2
						SD3->D3_CUSTO3	:= SD1->D1_CUSTO3
						SD3->D3_CUSTO4	:= SD1->D1_CUSTO4
						SD3->D3_CUSTO5	:= SD1->D1_CUSTO5
						SD3->D3_NUMLOTE	:= SD1->D1_NUMLOTE
						SD3->D3_LOTECTL	:= SD1->D1_LOTECTL
						SD3->D3_DTVALID	:= SD1->D1_DTVALID
						SD3->D3_POTENCI	:= SD1->D1_POTENCI
						MsUnLock()
						dbSelectArea("SB2")
						B2AtuComD3({SD3->D3_CUSTO1,SD3->D3_CUSTO2,SD3->D3_CUSTO3,SD3->D3_CUSTO4,SD3->D3_CUSTO5})
						lContinua := .T.
					EndIf
					//-- Devolucao do produto para o armazem destino (Valorizado)
					If lContinua
						dbSelectArea("SB2")
						dbSetOrder(1)
						If !dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
							CriaSB2(SD1->D1_COD,cLocTran)
						EndIf
						//-- Desbloqueia o armazem de terceiro
						dbSelectArea("SB2")
						dbSetOrder(1)
						If dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
							RecLock("SB2",.F.)
							Replace B2_STATUS With "1"
							MsUnLock()
						EndIf
						RecLock("SD3",.T.)
						SD3->D3_FILIAL	:= xFilial("SD3")
						SD3->D3_COD		:= SD1->D1_COD
						SD3->D3_QUANT	:= SD1->D1_QUANT
						SD3->D3_TM		:= "499"
						SD3->D3_LOCAL	:= cLocTran
						SD3->D3_DOC		:= SD1->D1_DOC
						SD3->D3_EMISSAO	:= SD1->D1_DTDIGIT
						SD3->D3_NUMSEQ	:= SD1->D1_NUMSEQ
						SD3->D3_UM		:= SD1->D1_UM
						SD3->D3_GRUPO	:= SD1->D1_GRUPO
						SD3->D3_TIPO	:= SD1->D1_TP
						SD3->D3_SEGUM	:= SD1->D1_SEGUM
						SD3->D3_CONTA	:= SD1->D1_CONTA
						SD3->D3_CF		:= "DE6"
						SD3->D3_QTSEGUM	:= SD1->D1_QTSEGUM
						SD3->D3_USUARIO	:= SubStr(cUsuario,7,15)
						SD3->D3_CUSTO1	:= SD1->D1_CUSTO
						SD3->D3_CUSTO2	:= SD1->D1_CUSTO2
						SD3->D3_CUSTO3	:= SD1->D1_CUSTO3
						SD3->D3_CUSTO4	:= SD1->D1_CUSTO4
						SD3->D3_CUSTO5	:= SD1->D1_CUSTO5
						SD3->D3_NUMLOTE	:= SD1->D1_NUMLOTE
						SD3->D3_LOTECTL	:= SD1->D1_LOTECTL
						SD3->D3_DTVALID	:= SD1->D1_DTVALID
						SD3->D3_POTENCI	:= SD1->D1_POTENCI
						MsUnLock()
						dbSelectArea("SB2")
						B2AtuComD3({SD3->D3_CUSTO1,SD3->D3_CUSTO2,SD3->D3_CUSTO3,SD3->D3_CUSTO4,SD3->D3_CUSTO5})
						//-- Bloqueia o armazem de terceiro
						dbSelectArea("SB2")
						dbSetOrder(1)
						If dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
							RecLock("SB2",.F.)
							Replace B2_STATUS With "2"
							MsUnLock()
						EndIf
			    	EndIf
			    EndIf
			EndIf
		EndIf
	EndIf
//Retorno para o Armazem Original
ElseIf nTipo == 2 .And. lVldPE
	//-- Grava Flag que indica produto em transito
	RecLock("SD1",.F.)
	SD1->D1_TRANSIT := " "
	MsUnLock()
	//-- Desbloqueia o armazem de terceiro
	dbSelectArea("SB2")
	dbSetOrder(1)
	If dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
		RecLock("SB2",.F.)
		Replace B2_STATUS With "1"
		MsUnLock()
	EndIf
	//-- Requisita o produto do armazem de transito (Valorizado)
	dbSelectArea("SB2")
	dbSetOrder(1)
	If dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
		RecLock("SD3",.T.)
		SD3->D3_FILIAL	:= xFilial("SD3")
		SD3->D3_COD		:= SD1->D1_COD
		SD3->D3_QUANT	:= SD1->D1_QUANT
		SD3->D3_TM		:= "999"
		SD3->D3_OP		:= SD1->D1_OP
		SD3->D3_LOCAL	:= cLocTran
		SD3->D3_DOC		:= SD1->D1_DOC
		SD3->D3_EMISSAO	:= dDataBase
		SD3->D3_NUMSEQ	:= SD1->D1_NUMSEQ
		SD3->D3_UM		:= SD1->D1_UM
		SD3->D3_GRUPO	:= SD1->D1_GRUPO
		SD3->D3_TIPO	:= SD1->D1_TP
		SD3->D3_SEGUM	:= SD1->D1_SEGUM
		SD3->D3_CONTA	:= SD1->D1_CONTA
		SD3->D3_CF		:= "RE6"
		SD3->D3_QTSEGUM	:= SD1->D1_QTSEGUM
		SD3->D3_USUARIO	:= SubStr(cUsuario,7,15)
		SD3->D3_CUSTO1	:= SD1->D1_CUSTO
		SD3->D3_CUSTO2	:= SD1->D1_CUSTO2
		SD3->D3_CUSTO3	:= SD1->D1_CUSTO3
		SD3->D3_CUSTO4	:= SD1->D1_CUSTO4
		SD3->D3_CUSTO5	:= SD1->D1_CUSTO5
		SD3->D3_NUMLOTE	:= SD1->D1_NUMLOTE
		SD3->D3_LOTECTL	:= SD1->D1_LOTECTL
		SD3->D3_DTVALID	:= SD1->D1_DTVALID
		SD3->D3_POTENCI	:= SD1->D1_POTENCI
		MsUnLock()
		dbSelectArea("SB2")
		B2AtuComD3({SD3->D3_CUSTO1,SD3->D3_CUSTO2,SD3->D3_CUSTO3,SD3->D3_CUSTO4,SD3->D3_CUSTO5})
		MsUnLock()
		//-- Bloqueia o armazem de terceiro
		dbSelectArea("SB2")
		dbSetOrder(1)
		If dbSeek(xFilial("SB2")+SD1->D1_COD+cLocTran)
			RecLock("SB2",.F.)
			Replace B2_STATUS With "2"
			MsUnLock()
		EndIf
		lContinua := .T.
	EndIf
	//-- Devolucao do produto para o armazem destino (Valorizado)
	dbSelectArea("SB2")
	dbSetOrder(1)
	If lContinua .And. dbSeek(xFilial("SB2")+SD1->D1_COD+SD1->D1_LOCAL)
		RecLock("SD3",.T.)
		SD3->D3_FILIAL	:= xFilial("SD3")
		SD3->D3_COD		:= SD1->D1_COD
		SD3->D3_QUANT	:= SD1->D1_QUANT
		SD3->D3_TM		:= "499"
		SD3->D3_LOCAL	:= SD1->D1_LOCAL
		SD3->D3_DOC		:= SD1->D1_DOC
		SD3->D3_EMISSAO	:= dDataBase
		SD3->D3_NUMSEQ	:= SD1->D1_NUMSEQ
		SD3->D3_UM		:= SD1->D1_UM
		SD3->D3_GRUPO	:= SD1->D1_GRUPO
		SD3->D3_TIPO	:= SD1->D1_TP
		SD3->D3_SEGUM	:= SD1->D1_SEGUM
		SD3->D3_CONTA	:= SD1->D1_CONTA
		SD3->D3_CF		:= "DE6"
		SD3->D3_QTSEGUM	:= SD1->D1_QTSEGUM
		SD3->D3_USUARIO	:= SubStr(cUsuario,7,15)
		SD3->D3_CUSTO1	:= SD1->D1_CUSTO
		SD3->D3_CUSTO2	:= SD1->D1_CUSTO2
		SD3->D3_CUSTO3	:= SD1->D1_CUSTO3
		SD3->D3_CUSTO4	:= SD1->D1_CUSTO4
		SD3->D3_CUSTO5	:= SD1->D1_CUSTO5
		SD3->D3_NUMLOTE	:= SD1->D1_NUMLOTE
		SD3->D3_LOTECTL	:= SD1->D1_LOTECTL
		SD3->D3_DTVALID	:= SD1->D1_DTVALID
		SD3->D3_POTENCI	:= SD1->D1_POTENCI
		MsUnLock()
		dbSelectArea("SB2")
		B2AtuComD3({SD3->D3_CUSTO1,SD3->D3_CUSTO2,SD3->D3_CUSTO3,SD3->D3_CUSTO4,SD3->D3_CUSTO5})
		MsUnLock()
	EndIf
EndIf

//Ponto de entrada finalidades diversas na rotina de transferÍncia de Armazem de Tr‚nsito
If ExistBlock("MT103TRF")
	ExecBlock("MT103TRF",.F.,.F.,{nTipo,SD1->D1_FILIAL,SD1->D1_DOC,SD1->D1_SERIE,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD,SD1->D1_ITEM})
EndIf

RestArea(aAreaSB2)
RestArea(aAreaSD1)
RestArea(aAreaSD3)
RestArea(aAreaSF4)
RestArea(aAreaAnt)
Return Nil

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥A103RetTrf≥ Autor ≥ Microsiga S/A         ≥ Data ≥23/03/2008≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Funcao utilizada para retornar o saldo das notas fiscais em ≥±±
±±≥          ≥transito.                                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥                                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Function A103RetTrf()
Local lContinua	:= .T.
Local nOpca     := 0
Local nCnt      := 0
Local nPosDoc   := 0
Local nPosSerie := 0
Local nPosItem  := 0
Local nPosLoja  := 0
Local nPosForn  := 0
Local nPosCod   := 0
Local nPosIdCtrl:= 0
Local aCabSD1   := {}
Local aSD1      := {}
Local aCpoSD1   := {}
Local aAux      := {}
Local aButtons  := {}
Local cDocTran  := CriaVar("D1_DOC",.F.)
Local cSerTran  := SerieNfId("SD1",5,"D1_SERIE")
Local oDlg, oListBox, oPanel, dDataFec
Local lUsaNewKey:= TamSX3("D1_SERIE")[1] == 14
Local oChk1
Local lChk1

//Verificar data do ultimo fechamento
dDataFec := MVUlmes() 
	If dDataFec >= dDataBase
		Help( " ", 1, "FECHTO" )
		lContinua := .F.
    EndIf
	If lContinua
		Aadd( aCabSD1, 'Ok' )
		SX3->(DbSetOrder(1))
		SX3->(DbSeek("SD1"))
		While SX3->(!Eof()) .And. SX3->X3_ARQUIVO == "SD1"
			If AllTrim(SX3->X3_CAMPO) $ "D1_DOC|D1_SERIE|D1_ITEM|D1_COD|D1_LOCAL|D1_QUANT|D1_TRANSIT|D1_FORNECE|D1_LOJA|D1_COD"
				Aadd( aCabSD1, X3Titulo() )
				Aadd( aCpoSD1, SX3->X3_CAMPO )
				If AllTrim(SX3->X3_CAMPO) == "D1_DOC"
					nPosDoc   := 1+Len(aCpoSD1)
				ElseIf AllTrim(SX3->X3_CAMPO) == "D1_SERIE"
					nPosSerie := 1+Len(aCpoSD1)
					If lUsaNewKey
						Aadd( aCabSD1, "Id de Controle" )
						Aadd( aCpoSD1, "IDCONTROLSD1" )
						nPosIdCtrl:= 1+Len(aCpoSD1)
					EndIf
				ElseIf AllTrim(SX3->X3_CAMPO) == "D1_ITEM"
					nPosItem  := 1+Len(aCpoSD1)
				ElseIf AllTrim(SX3->X3_CAMPO) == "D1_FORNECE"
					nPosForn  := 1+Len(aCpoSD1)
				ElseIf AllTrim(SX3->X3_CAMPO) == "D1_LOJA"
					nPosLoja  := 1+Len(aCpoSD1)
				ElseIf AllTrim(SX3->X3_CAMPO) == "D1_COD"
					nPosCod  := 1+Len(aCpoSD1)
				EndIf
			EndIf
			SX3->(DbSkip())
		EndDo
		//-- Carrega Registro em Branco
		aAux := {}
		Aadd( aAux, .F. )
		For nCnt := 1 To Len(aCpoSD1)
			Aadd( aAux, Iif( aCpoSD1[nCnt] == "IDCONTROLSD1" ,"" ,CriaVar(aCpoSD1[nCnt],.F.) ) )
		Next nCnt
		aAdd( aSD1, aClone(aAux) )
		//-- Adiciona botao para exibir os documentos em transito
		Aadd(aButtons, {'RECALC',{||A103FilTRF(@oListBox,@aCpoSD1,@aSD1,cDocTran,cSerTran)},STR0298,STR0298}) //"Visualizar documento em transito"

		//-- Monta Dialog
		DEFINE MSDIALOG oDlg TITLE STR0297 FROM 00,00 TO 400, 700 PIXEL

		@ 12,0 MSPANEL oPanel PROMPT "" SIZE 100,19 OF oDlg CENTERED LOWERED //"Botoes"
		oPanel:Align := CONTROL_ALIGN_TOP

		oListBox:= TWBrowse():New( 012, 000, 300, 140, NIL, aCabSD1, NIL, oDlg, NIL, NIL, NIL,,,,,,,,,, "ARRAY", .T. )
		oListBox:SetArray( aSD1 )
		oListBox:bLDblClick  := { || { aSD1[oListBox:nAT,1] := !aSD1[oListBox:nAT,1] }}
		oListBox:bLine := &('{ || A103Line(oListBox:nAT,aSD1) }')
		oListBox:Align := CONTROL_ALIGN_ALLCLIENT

		@ 6  ,4   SAY SD1->(RetTitle("D1_DOC"))			Of oPanel PIXEL
		@ 4  ,35  MSGET cDocTran PICTURE '@!' When .T.	Of oPanel PIXEL

		@ 6  ,100  SAY SD1->(SerieNfId("SD1",7,"D1_SERIE"))		 Of oPanel PIXEL
		@ 4  ,120  MSGET cSerTran PICTURE '!!!' When .T. Of oPanel PIXEL
		
		@ 6,200 CHECKBOX oChk1 VAR lChk1 PROMPT STR0523 SIZE 70,6 PIXEL OF oPanel ON CLICK TranMarkAll(@oListBox,@aSD1,lChk1) // Cadastrar no CH

		ACTIVATE MSDIALOG oDlg CENTERED ON INIT EnchoiceBar(oDlg,{||(nOpca := 1,,oDlg:End())},{||(nOpca := 0,,oDlg:End())},,aButtons)

		//-- Processando Retorno de saldo em Transito
		For nCnt := 1 to Len(aSD1)		
			dbSelectArea("SD1")
			dbSetOrder(1) //D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_COD+D1_ITEM
			If dbSeek(xFilial("SD1")+aSD1[nCnt,nPosDoc]+Iif( lUsaNewKey, aSD1[nCnt,nPosIdCtrl] , aSD1[nCnt,nPosSerie] )+aSD1[nCnt,nPosForn]+aSD1[nCnt,nPosLoja]+aSD1[nCnt,nPosCod]+aSD1[nCnt,nPosItem])
				If nOpca == 1 .And. aSD1[nCnt,1] 
					Processa({|| A103TrfSld(.F.,2) })
				EndIf
				UnLockByName("Tr"+SD1->(D1_FORNECE+D1_DOC+D1_SERIE+D1_ITEM))
			EndIf	
		Next nCnt
	EndIf
Return .F.

//-------------------------------------------------------------------
/*/{Protheus.doc} TranMarkAll
// Realiza marcaÁ„o de todos os itens de um mesmo documento na tela
// de Documentos em Transito.
@since 31/05/2019
/*/
//-------------------------------------------------------------------
Static Function TranMarkAll(oListBox,aSD1,lChk1)

Local nX
Local cChaveNF := aSD1[oListBox:nAT,8] + aSD1[oListBox:nAT,9] + aSD1[oListBox:nAT,5] + aSD1[oListBox:nAT,6]

For nX := 1 to Len(aSD1)
	If cChaveNF == aSD1[nX,8] + aSD1[nX,9] + aSD1[nX,5] + aSD1[nX,6]
		aSD1[nX,1] := lChk1
	EndIf
Next nX

oListBox:Refresh()

Return

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥A103FilRet≥ Autor ≥ Microsiga S/A         ≥ Data ≥23/03/2008≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Funcao utilizada para carregar a TWBrowse com os documentos ≥±±
±±≥          ≥de entrada em transito.                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ oListBox - Objeto TWBrowse()                               ≥±±
±±≥          ≥ aCpoSD1  - Array com o cabecalho da TWBrowse               ≥±±
±±≥          ≥ aSD1     - Array com os itens da TWBrowse                  ≥±±
±±≥          ≥ cDocTran - Documento selecionado pelo usuario              ≥±±
±±≥          ≥ cSerTran - Serie selecionada pelo usuario                  ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Function A103FilTRF(oListBox,aCpoSD1,aSD1,cDocTran,cSerTran)
Local cQuery    := ''
Local cAliasSD1 := 'SD1'
Local aAux      := {}
Local aStruSD1  := {}
Local nCnt      := 0
Local lUsaNewKey:= TamSX3("F1_SERIE")[1] == 14
Local cDocs 	:= ''

	cAliasSD1 := GetNextAlias()
	aStruSD1  := SD1->( dbStruct() )
	cQuery := " SELECT SD1.*,SD1.R_E_C_N_O_ REGD1 "
	cQuery +=   " FROM " + RetSqlName("SD1") + " SD1 "
	cQuery +=  " WHERE D1_FILIAL  = '" + xFilial("SD1") + "' "
	cQuery +=        " AND D1_TRANSIT = 'S' "
	If !Empty(cDocTran)
		cQuery +=    " AND D1_DOC = '"+cDocTran+"' "
	EndIf
	If !Empty(cSerTran)
		If lUsaNewKey
			cQuery +=    " AND D1_SDOC = '"+cSerTran+"' "
		Else
			cQuery +=    " AND D1_SERIE = '"+cSerTran+"' "
		EndIf
	EndIf
	cQuery +=        " AND D_E_L_E_T_ = ' ' "
	cQuery +=  " ORDER BY D1_FILIAL,D1_DOC,D1_SERIE,D1_ITEM "
	cQuery := ChangeQuery( cQuery )
	dbUseArea( .T., "TOPCONN", TcGenQry( , , cQuery ), cAliasSD1, .F., .T. )
	For nCnt := 1 To Len(aStruSD1)
		If aStruSD1[nCnt,2]<>"C"
			TcSetField(cAliasSD1,aStruSD1[nCnt,1],aStruSD1[nCnt,2],aStruSD1[nCnt,3],aStruSD1[nCnt,4])
		EndIf
	Next nCnt

//-- Limpa array aSD1
For nCnt := 1 To Len(aSD1)
	aDel(aSD1,1)
	aSize(aSD1,Len(aSD1)-1)
Next
//-- Carrega Itens em Transito
Do While (cAliasSD1)->(!Eof())
	SD1->(dbGoTo((cAliasSD1)->REGD1))
	If LockByName("Tr"+SD1->(D1_FORNECE+D1_DOC+D1_SERIE+D1_ITEM))
		aAux := {}
		Aadd( aAux, .F. )
		For nCnt := 1 To Len(aCpoSD1)
			If AllTrim(aCpoSD1[nCnt]) == "D1_SERIE"
				Aadd( aAux, Substr( &(aCpoSD1[nCnt]),1,3)  )
			ElseIf AllTrim(aCpoSD1[nCnt]) == "IDCONTROLSD1"
				Aadd( aAux, &("D1_SERIE") )
			Else
				Aadd( aAux, &(aCpoSD1[nCnt]) )
			EndIf
		Next nCnt
		aAdd( aSD1, aClone(aAux) )
	Else		
		If At((cAliasSD1)->D1_DOC,cDocs) == 0
			cDocs += (cAliasSD1)->D1_DOC+';'
		EndIf	
	EndIf
	(cAliasSD1)->(DbSkip())
EndDo
If !Empty(cDocs)
	Help(NIL, NIL, "DOC. BLOQUEADO", NIL, "O(s) documento(s) " +cDocs+ " n„o foi(foram) carregado(s), pois um ou mais itens encontram-se bloqueados por outro usu·rio, na mesma rotina:", 1, 0, NIL, NIL, NIL, NIL, NIL, {"Escolha outro Documento ou aguarde a liberaÁ„o do mesmo."})
EndIf
//-- Carrega Registro em Branco
aAux := {}
If Len(aSD1) == 0
	Aadd( aAux, .F. )
	For nCnt := 1 To Len(aCpoSD1)
		Aadd( aAux, CriaVar(aCpoSD1[nCnt],.F.) )
	Next nCnt
	aAdd( aSD1, aClone(aAux) )
EndIf
//-- Atualiza TWBrowse()
oListBox:Refresh()
//-- Apaga arquivo temporario
	(cAliasSD1)->(DbCloseArea())
Return .T.

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥ A103OPBen∫Autor  ≥Andre Anjos         ∫ Data ≥  14/04/09   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Descricao ≥ Sugere a ordem de producao de acordo com a remessa.        ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥ MATA103                                                    ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103OPBen(cAliasSD2, nTpCtlBN)
Local aArea       := GetArea()
Local cRet        := Space(TamSX3("D1_OP")[1])

Default cAliasSD2 := 'SD2'
Default nTpCtlBN  := 1 // Para manter o comportamento padrao da funcao

If !Empty((cAliasSD2)->(D2_PEDIDO+D2_ITEMPV))
	If nTpCtlBN == 1 // metodo antigo: um unico envio
		dbSelectArea("SD4")
		dbSetOrder(6)
		If dbSeek(xFilial("SD4")+(cAliasSD2)->(D2_PEDIDO+D2_ITEMPV))
			cRet := SD4->D4_OP
		EndIf
	Else // metodo novo: multiplos envios
		dbSelectArea("SGO")
		dbSetOrder(2) // GO_FILIAL+GO_NUMPV+GO_ITEMPV+GO_OP+GO_COD+GO_LOCAL
		dbSeek(xFilial("SGO")+(cAliasSD2)->(D2_PEDIDO+D2_ITEMPV))
		If !Eof() .And. ( GO_FILIAL+GO_NUMPV+GO_ITEMPV == (cAliasSD2)->(D2_FILIAL+D2_PEDIDO+D2_ITEMPV) )
			cRet := SGO->GO_OP
		EndIf
	EndIf
	// Se nao encontrou referencia na SD4 nem na SGO entao procura na SDC
	If Empty(cRet)
		dbSelectArea("SDC")
		dbSetOrder(1)
		If !Empty((cAliasSD2)->(D2_COD+D2_LOCAL+"SC2"+D2_PEDIDO+D2_ITEMPV)) .And. dbSeek(xFilial("SDC")+(cAliasSD2)->(D2_COD+D2_LOCAL+"SC2"+D2_PEDIDO+D2_ITEMPV))
			cRet := SDC->DC_OP
		EndIf
	EndIf
EndIf

RestArea(aArea)
Return cRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥ A103MNat ∫Autor  ≥Julio C.Guerato     ∫ Data ≥  02/06/09   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Descricao ≥ Funcao para carregar aColsSev quando carregado pelo PE     ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±≥Parametros≥ aHeadSev - Header Multiplas Naturezas                      ≥±±
±±≥          ≥ aColsSev - ACOLS Multiplas Naturezas        		          ≥±±
±±∫Uso       ≥ MATA103                                                    ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103MNat(aHeadSev, aColsSev)
Local aCR := {}

If SuperGetMv("MV_MULNATP") .And. !__lPyme
	If ( ExistBlock("MT103MNT") )
		aCR := ExecBlock("MT103MNT",.F.,.F.,{aHeadSev, aColsSev})
		If ( ValType(aCR) == "A" )
				aColsSev := aClone(aCR)
			Eval(bRefresh,6,6)
		EndIf
	EndIf
EndIf
Return (.T.)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103ATUPREV≥Autor 	   ≥Vitor Raspa       ≥Data  ≥ 20.Jun.08≥±±
±±≥          ≥           ≥PadronizaÁ„o ≥Julio C.Guerato   ≥Data  ≥ 15.Set.09≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descriáao ≥ Atualiza o saldo previsto de entrada na tabela que faz o     ≥±±
±±≥			 ≥ controle de amarraÁ„o entre Filial Centralizadora X Entrega  ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103AtuPrev( lExclusao )

Local cFilCen  := ''
Local aArea    := {}
Local aAreaSDP := {}
Local aAreaSM0 := {}
Local aAreaSA2 := {}
Local nQTPCCEN := 0

	If !Empty( SD1->D1_PCCENTR ) .And. !Empty( SD1->D1_ITPCCEN )
		aArea    := GetArea()
		aAreaSDP := SDP->( GetArea() )
		aAreaSM0 := SM0->( GetArea() )
		aAreaSA2 := SA2->( GetArea() )

		//--Obtem a filial de onde esta vindo o produto
		SA2->( DbSetOrder(1) )
		SA2->( DbSeek( xFilial('SA2') + SD1->(D1_FORNECE + D1_LOJA) ) )

		SM0->( DbSetOrder(1) )
		SM0->( DbSeek( cEmpAnt ) )
		While !SM0->( Eof() ) .And. Empty( cFilCen )
			If AllTrim( SA2->A2_CGC ) == AllTrim( SM0->M0_CGC )
				cFilCen := FWGETCODFILIAL
			EndIf
			SM0->( DbSkip() )
		End

		RestArea( aAreaSM0 )
		RestArea( aAreaSA2 )

		//--Atualiza o saldo da Qtd. Prevista a entrar...
		SDP->( DbSetOrder(2) ) //--DP_FILIAL+DP_FILCEN+DP_FILNEC+DP_PEDCEN+DP_ITPCCN
		If SDP->( DbSeek( xFilial('SDP') + cFilCen + cFilAnt + SD1->(D1_PCCENTR + D1_ITPCCEN) ) )

			RecLock('SDP',.F.)
			If lExclusao
			    If SDP->DP_QTDENT<SD1->D1_QUANT
				    SDP->DP_QTDENT := 0
				Else
					SDP->DP_QTDENT := SDP->DP_QTDENT - SD1->D1_QUANT
				EndIf
		    Else
			    If (SDP->DP_QUANT-DP_QTDENT)<SD1->D1_QUANT
				    If (SDP->DP_QUANT-DP_QTDENT)>0 .And. (SDP->DP_QUANT-DP_QTDENT)<SD1->D1_QUANT
					    nQTPCCEN :=SDP->DP_QUANT-DP_QTDENT
					Else
						nQTPCCEN := 0
					EndIf
				    SDP->DP_QTDENT := SDP->DP_QUANT
				Else
					SDP->DP_QTDENT := SDP->DP_QTDENT + SD1->D1_QUANT
					nQTPCCEN := SD1->D1_QUANT
				EndIf
				RecLock('SD1',.F.)
				   SD1->D1_QTPCCEN := nQTPCCEN
				SD1->( MsUnLock() )
			EndIf
			SDP->( MsUnLock() )
		EndIf
		RestArea( aAreaSDP )
		RestArea( aArea )
	EndIf

Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103VALPCC ≥Autor 	   ≥Julio C.Guerato   ≥Data  ≥ 30.Set.09≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descriáao ≥ Valida amarraÁ„o entre NFE X Pedido de Compras Centralizado  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ nItem = N˙mero do Item no Acols                              ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103ValPCC(nItem)

Local aArea    	   := GetArea()
Local nPosCod
Local nPosQuant
Local nPosPC
Local nPosItemPC
Local nPosPCCENTR
Local nPosITPCCEN
Local nQTPrev      := 0
Local nX           := 0
Local nVPCCNFE
Local lRet     	   := .T.
Local lPyme		   := If(Type("__lPyme") <> "U",__lPyme,.F.)

If cTipo=="N" .And. !lPyme
	nPosCod  	 := GetPosSD1("D1_COD")
	nPosQuant    := GetPosSD1("D1_QUANT")
	nPosPC	     := GetPosSD1("D1_PEDIDO")
	nPosItemPC   := GetPosSD1("D1_ITEMPC")
	nPosPCCENTR  := GetPosSD1("D1_PCCENTR")
	nPosITPCCEN  := GetPosSD1("D1_ITPCCEN")
	If nPosPC>0 .And. nPosItemPc>0 .And. nPosPCCENTR>0 .And. nPosITPCCEN>0 .And. nPosCod>0 .And. nPosQuant>0
	   //Verifica se o Pedido que est· sendo recebido na NFE È o Pedido de Compras da Filial Centralizadora
	   //. Se N√O for fim de arquivo, significa o Pedido Centralizado est· sendo recebido e n„o exige amarraÁ„o
	   //  ou n„o existe pedido de compras vinculado a Nota Fiscal
	   //. Se for fim de arquivo, exige amarraÁ„o com o Pedido Centralizado para baixar o saldo previsto na tabela SDP
   	   DbSelectArea("SDP")
	   DbSetOrder(4)
	   DbSeek(xFilial('SDP')+xFilial('SD1')+aCols[nItem][nPosPC]+aCols[nItem][nPosItemPC])
	   If Eof()
	       //Verifica se o Pedido que est· sendo recebido possui amarraÁ„o com um Pedido de Vendas.
	       //Se N„o for fim de arquivo, possui vinculo com o Pedido de Compras da Filial Centralizadora
	       //Se for fim de arquivo, n„o possui vinculo com o Pedido de Compras da Filial Centralizadora
	       DbSelectArea("SC7")
	       DbSetOrder(14)
		   DbSeek(xFilEnt(xFilial('SC7'))+aCols[nItem][nPosPC]+aCols[nItem][nPosItemPC])
	   	   DbSelectArea("SC6")
	   	   DbSetOrder(10)
	 	   DbSeek(SC7->C7_FILCEN+xFilial('SD1')+aCols[nItem][nPosPC]+aCols[nItem][nPosItemPC])
	 	   If !Eof()
	 	        //Permite vincular o PC a NFe somente se o PV estiver faturado
	 	        If (SC6->C6_QTDVEN-SC6->C6_QTDENT)<>0
	 	           Aviso("A103ValPCC6",STR0329+"  "+STR0323+STRZERO(nItem,TamSX3("D1_ITEM")[1])+"  "+CHR(13)+STR0330+SC6->C6_NUM,{STR0461})
			 	   lRet := .F.
			 	EndIf
			 	//Valida vinculo com o PC centralizado
			 	If lRet
			 		nVPCCNFE     := SuperGetMv("MV_VPCCNFE",.F.,1)
					If Empty(aCols[nItem][nPosPCCENTR]) .Or. Empty(aCols[nItem][nPosITPCCEN])
					   If nVPCCNFE<>0
			   			   Aviso("A103ValPCC1",STR0319+CHR(13)+STR0323+STRZERO(nItem,TamSX3("D1_ITEM")[1]),{STR0461})
				 		   lRet := .F.
					   EndIf
			 		Else
					   DbSelectArea("SDP")
					   DbSetOrder(5)
					   DbSeek(xFilial('SDP')+xFilial('SD1')+aCols[nItem][nPosCod])
					   If !Eof()
					      //Verifica quantidade j· relacionada a NFE referente ao Pedido Centralizado//
			       		  For nX := 1 to Len(aCols)
					       	    If !GdDeleted(nx)
				   			       If nx<>nItem .And. aCols[nX][nPosCod]==Acols[nItem][nPosCod]
				   			          nQTPrev := nQTPrev+Acols[nX][nPosQuant]
				   			       Endif
				   			 	Endif
			   			  Next NX

			   			  //Pedido est· sendo baixado, porÈm o par‚metro MV_VPCCNFE n„o est· configurado com o valor correto //
			   			  If nVPCCNFE=0
				   			  Aviso("A103ValPCC5",STR0325,{STR0461})
					   		  lRet := .F.
					   	  EndIf

			   			  //Saldo DisponÌvel n„o suficiente para NFE e Par‚metro = 1, n„o permite vinculo//
			   			  If nVPCCNFE=1
				   			  If (((SDP->DP_QUANT-SDP->DP_QTDENT) == 0) .Or.;
			   				     ((SDP->DP_QUANT-SDP->DP_QTDENT-nQTPrev)<Acols[nItem][nPosQuant]))
			   				      Aviso("A103ValPCC2",STR0320+CHR(13)+STR0322+Transform((SDP->DP_QUANT-SDP->DP_QTDENT-nQTPrev),PesqPict("SD1","D1_QUANT")),{"Ok"})
				   				  lRet := .F.
				   	          EndIf
				   	      EndIf

			   	      	  //Saldo DisponÌvel n„o suficiente para NFE e Par‚metro = 2, permite vinculo
			   			  If nVPCCNFE=2
					   		 If (SDP->DP_QUANT-SDP->DP_QTDENT-nQTPrev)<=0
					   			 lRet := .T.
					   	      EndIf
					   	  EndIf
					   Else
					      Aviso("A103ValPCC3",STR0321,{STR0461})
				   		  lRet := .T.
			  		   EndIf
			  		EndIf
			  	EndIf
		   EndIf
	  	EndIf
	Else
		nVPCCNFE     := SuperGetMv("MV_VPCCNFE",.F.,1)
		If nVPCCNFE<>0
			Aviso("A103ValPCC4",STR0324,{STR0461})
		    lRet := .F.
		EndIf
	EndIf
EndIf

RestArea(aArea)
Return (lRet)


/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥A103VldDanfe≥ Autor ≥ Julio C.Guerato     ≥ Data ≥09/11/2009≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥FunÁ„o para ValidaÁ„o dos Campos do Folder Danfe			  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T. ou .F., confirmando a ValidaÁ„o		                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥Array com os campos da Folder com campos da Danfe           ≥±±
±±≥          ≥[01]: Cod.Transportadora      	                          ≥±±
±±≥          ≥[02]: Peso Liquido		                                  ≥±±
±±≥          ≥[03]: Peso Bruto                                            ≥±±
±±≥          ≥[04]: Especie 1        		                              ≥±±
±±≥          ≥[05]: Volume  1		                                      ≥±±
±±≥          ≥[06]: Especie 2        		                              ≥±±
±±≥          ≥[07]: Volume  2		                                      ≥±±
±±≥          ≥[08]: Especie 3        		                              ≥±±
±±≥          ≥[09]: Volume  3		                                      ≥±±
±±≥          ≥[10]: Especie 4        		                              ≥±±
±±≥          ≥[11]: Volume  4		                                      ≥±±
±±≥          ≥[12]: Placa 			                                      ≥±±
±±≥          ≥[13]: Chave NFe		                                      ≥±±
±±≥          ≥[14]: Tipo de Frete	                                      ≥±±
±±≥          ≥[15]: Valor Ped·gio	                                      ≥±±
±±≥          ≥[16]: Fornecedor Retirada                                   ≥±±
±±≥          ≥[17]: Loja Retirada	                                      ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103VldDanfe(aNFEDanfe,aNFEletr)

Local lRetDanfe := .T.

If cPaisLoc == "BRA"  .And. !l103Visual
	If l103Class .And. !Empty(aNFEDanfe[13])
		lRetDanfe := A103ConsNfeSef(aNFEDanfe[13])
	EndIf

	If ExistBlock("MT103DNF")
		lRetDanfe := Execblock("MT103DNF",.F.,.F.,{aNFEDanfe,aNFEletr})
	Endif
Endif

Return lRetDanfe

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Programa  ≥A103VLDEXC  ≥ Autor ≥ Julio C.Guerato     ≥ Data ≥04/02/2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥FunÁ„o para Validar se existem vinculos da NFe em outras    ≥±±
±±≥			 ≥tabelas													  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥.T. = N„o existem vinculos   				                  ≥±±
±±≥			 ≥.F. = Existe vinculos 	  				                  ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±≥Parametros≥[01]: Indica se est· em exclus„o 	                          ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103VldEXC(lExclui,cPrefixo)

Local lRet      := .T.
Local lContinua := .T.
Local nx        := 0
Local nPosCod   := GetPosSD1("D1_COD")
Local nItem     := GetPosSD1("D1_ITEM")
Local cDesc     := ""
Local lVldExc	:= .T.
Local lCpRet	:= .F.

Default cPrefixo := ""

If lExclui

	If ExistBlock("A103VLEX")
		lContinua := ExecBlock("A103VLEX",.F.,.F.)
		If ValType(lContinua) != "L"
			lContinua := .T.
		EndIf
	EndIf

	If lContinua

		//Verifica vinculo com Pedidos de Venda //
		For nX = 1 to len(aCols)
		     DbSelectArea("SC6")
		     DbSetOrder(5)
		     MsSeek(xFilial("SC6")+CA100FOR+CLOJA+aCols[nX][nPosCod]+CNFISCAL+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)+aCols[nX][nItem])
		     If !EOF()
		         lRet:=.F.
		         cDesc:= STR0331+CHR(13)+STR0332+CHR(13)+STR0333+C6_FILIAL+" "+C6_NUM+" "+C6_ITEM+" "+C6_PRODUTO
			     AVISO("A103ValExc",cDesc,{STR0461})
		         Exit
		     EndIf
		Next nX

		//Valida se Existe baixa no Contas a Pagar
		If lRet .And. !A120UsaAdi(cCondicao)
			dbSelectArea("SE2")
			SE2->(dbSetOrder(6))
			SE2->(DbGotop())

			MsSeek(xFilial()+cA100For+cLoja+cPrefixo+SF1->F1_DUPL)

			While ( !Eof() .And.;
				xFilial("SE2")  == SE2->E2_FILIAL  .And.;
				cA100For        == SE2->E2_FORNECE .And.;
				cLoja           == SE2->E2_LOJA    .And.;
				cPrefixo	    == SE2->E2_PREFIXO .And.;
				SF1->F1_DUPL	== SE2->E2_NUM )
				If SE2->E2_TIPO == MVNOTAFIS
					If !FaCanDelCP("SE2","MATA100|PLSMPAG")
						lRet := .F.
						Exit
					EndIf
				EndIf

				dbSelectArea("SE2")
		   		dbSkip()
			EndDo
		EndIf

		//... Inserir outros Vinculos daqui para baixo .. //

		//Valida se a nota gerou um titulo com PCC que compos o saldo
		//da cumulatividade de outro titulo que ja foi retido
		If lRet .And. !lIsRussia
			dbSelectArea("SE2")
			SE2->(dbSetOrder(6))

			If MsSeek(xFilial("SE2")+cA100For+cLoja+cPrefixo+SF1->F1_DUPL)
				lCpRet := SLDRMSG(SE2->E2_EMISSAO,SE2->E2_VALOR,SE2->E2_NATUREZ,"P",SE2->E2_FORNECE,SE2->E2_LOJA,SE2->E2_TIPO)
				If lCpRet
					If !MSGNoYes(STR0473)
						lRet := .F.
					Endif
				Endif
			EndIf

		EndIf

		//Verifica se algum produto ja foi distribuido
		If lRet
			If Localiza(SD1->D1_COD)
				dbSelectArea('SDA')
				dbSetOrder(1)
				DbSeek(xFilial()+SD1->D1_COD+SD1->D1_LOCAL+SD1->D1_NUMSEQ+SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA)
				If !(SDA->DA_QTDORI == SDA->DA_SALDO)
					Help(" ",1,"SDAJADISTR")
					lRet := .F.
				EndIf
			EndIf
		EndIf
	EndIf

	//Ponto de entrada para validaÁ„o da exclus„o do documento
	If lRet .And. ExistBlock("MT103EXC")
		lVldExc := ExecBlock("MT103EXC",.F.,.F.)
		If ValType(lVldExc) == "L"
			lRet := lVldExc
		EndIf
	EndIf
EndIf

Return lRet


/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103Adiant  ≥ Autor ≥Totvs                ≥ Data ≥20.05.2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Valida a existencia de pedidos de compra para o documento,  ∫±±
±±≥          ≥caso seja usada condicao de pagto com Adiantamento.         ∫±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ExpL1: Indica se existe Pedido de Compra associado ao Docu- ≥±±
±±≥          ≥mento.                                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpC1: Condicao de Pagamento deste documento de entrada     ≥±±
±±≥          ≥ExpC2: Codigo do fornecedor                                 ≥±±
±±≥          ≥ExpC3: Loja do fornecedor                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Observacao≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao Efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Static Function A103Adiant(lUsaAdi)

	Local aArea	   	:= GetArea()
	Local nCnt 	   	:= 0
	Local nCnt1    	:= 0
	Local lRet 	   	:= .T.
	Local aPedidos 	:= {}
	Local aPedAdt  	:= {}
	Local nValAdt  	:= 0
	Local nSldAdt  	:= 0
	Local nValMov	:= 0
	Local aAreaSE2 	:= SE2->(GetArea())
	Local aAreaSE5 	:= SE5->(GetArea())
	Local aAreaSC7 	:= SC7->(GetArea())
	Local lGeraDup 	:= .F.
	Local lIntGH
	Local cKeySE5	:= ""
	Local lPedXPa  := .F.
	Local lVldAdt	  := SuperGetMv("MV_VLDADT",.F.,.T.)

	Default lUsaAdi := .F.

	For nCnt := 1 to Len(aCols)
		If !gdDeleted(nCnt)
			If !Empty(gdFieldGet("D1_PEDIDO",nCnt)) .and. !Empty(gdFieldGet("D1_ITEMPC",nCnt))
				If AvalTes(gdFieldGet("D1_TES",nCnt),,"S")  // Soh considera este pedido se o TES usada gerar duplicata
					lGeraDup := .T.
					If aScan(aPedAdt,{|x| x == gdFieldGet("D1_PEDIDO",nCnt)}) <= 0
	  		 			aAdd(aPedAdt,gdFieldGet("D1_PEDIDO",nCnt))
		  			Endif
				EndIf
			Else
				If AvalTes(gdFieldGet("D1_TES",nCnt),,"S")  // Soh considera este pedido se o TES usada gerar duplicata
					lGeraDup := .T.
				Endif
			Endif
		Endif
	Next nCnt
	If Len(aPedAdt) > 0
		For nCnt := 1 to Len(aPedAdt)
			If lRet 
				// Carrega array de Adiantamentos relacionados ao pedido
				aPedidos := FPedAdtPed("P", { aPedAdt[nCnt] }, .F. )
				For nCnt1 := 1 To Len(aPedidos)
					SC7->(DbSeek(xFilial("SC7")+aPedidos[nCnt1][1])) //Posiciona no pedido de compra com adiantamento, para validar a data de emiss„o com a data base
					If SC7->C7_EMISSAO > dDataBase
						lRet := .F.
						Exit 
					EndIf 
					// checa se o saldo atual do adiantamento eh igual ou maior que o valor relacionado no pedido
					SE2->(dbGoto(aPedidos[nCnt1][2]))
					If SE2->(Recno()) = aPedidos[nCnt1][2]
						If SE2->E2_SALDO >= SaldoTit(SE2->E2_PREFIXO,SE2->E2_NUM,SE2->E2_PARCELA,SE2->E2_TIPO,SE2->E2_NATUREZ,"P",SE2->E2_FORNECE,SE2->E2_MOEDA,dDataBase,RetDtBxPA(),SE2->E2_LOJA,,0,1)
							nSldAdt += aPedidos[nCnt1][3]
							nValAdt += SE2->E2_VALOR
						EndIf
						If cPaisLoc == "BRA"
							SE5->( DbSetOrder( 7 ) )
							SE5->( DbGoTop() )
							cKeySE5 := xFilial("SE5")+SE2->(E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO+E2_FORNECE+E2_LOJA)
							lTemMov := SE5->( DbSeek( cKeySE5 ) )
							If lTemMov† .And. !(SE5->E5_TIPODOC $ "PA")	// Baixa ou Cheque
								Do While SE5->( !Eof() ) .And.  ( SE5->E5_FILIAL+SE5->E5_PREFIXO+SE5->E5_NUMERO+SE5->E5_PARCELA+SE5->E5_TIPO+SE5->E5_CLIFOR+SE5->E5_LOJA == cKeySE5 )
									If !( TemBxCanc( cKeySE5, .F. ) )
										If (SE5->E5_TIPODOC $ "BA/CH" .And. !Empty(SE5->E5_NUMCHEQ) .And. SubStr(SE5->E5_NUMCHEQ,1,1) <> "*") .Or. SE5->E5_TIPODOC $ "VL"
											nValMov += SE5->E5_VALOR
										EndIf
									EndIf
									If SE5->E5_TIPODOC $ "PA"
										nValMov += SE5->E5_VALOR
									EndIf
								SE5->( DbSkip() )
								EndDo
							ElseIf lTemMov†.And.†(SE5->E5_TIPODOC†$†"PA")
								nValMov += SE5->E5_VALOR
							EndIf
						EndIf
					EndIf
					lPedXPa := .T.
				Next nCnt1
			Else
				Exit
			Endif
		Next nCnt

		If !lRet 
			Help(,,"A103ADIANT",,STR0545, 1, 0,,,,,,{STR0547}) //"Pedido de compra vinculado ao documento de entrada possuÌ adiantamento e para que a compensaÁ„o do tÌtulo no Financeiro seja realizada corretamente, a data base do sistema n„o poder· ser retroagida. Ajuste a data base do sistema e faÁa a inclus„o do Documento de Entrada."
		EndIf

		If lRet .And. nValAdt == 0 .And. lUsaAdi
			Aviso(STR0119,STR0336 + CRLF + STR0337,{STR0461}) // "O Documento n„o poder· ser incluÌdo, pois n„o existe nenhum adiantamento relacionado ao(s) pedido(s) de compra e a condiÁ„o de pagamento est· cadastrada para uso de Adiantamento."#CRLF#"Na rotina de Pedido de Compra, relacione pelo menos um adiantamento ao(s) pedido(s) de compra."
			lRet := .F.
		ElseIf lRet .And. cPaisLoc == "BRA" .And. nValMov < nValAdt .And. lUsaAdi .And. lVldAdt //Se movimentou menos banco do que adiantou, existe adto sem mov (SOMENTE BRASIL)
			Aviso(STR0119, STR0500 + CRLF + STR0501, {STR0461} )
			lRet := .F.
		Else
			If lRet .And. lPedXPa .And. !lUsaAdi .And. !l103Auto .And. !__lIntPFS
				lRet := MsgYesNo(STR0499,STR0119)// "Existem pedidos de compra relacionados a adiantamentos e foi escolhida uma condiÁ„o de pagamento que n„o utiliza adiantamento. Neste caso n„o ocorrer· a compensaÁ„o autom·tica. Deseja prosseguir?"
			Else
				If lRet .And. !lVldAdt .And. !lTemMov //Se o par‚metro MV_VLDADT estiver desativado e n„o possui movimentaÁ„o bancaria
					lRet := MsgYesNo(STR0541,STR0119)
				EndIf
			EndIf
		EndIf
	Else
		If lGeraDup .And. lUsaAdi
			lIntGH   	:= SuperGetMv("MV_INTGH",.F.,.F.)  //Verifica Integracao com GH
			If lIntGH
				Aviso(STR0236,STR0334 + CRLF + STR0335,{STR0461}) // "N„o h· nenhum Pedido de Compra relacionado com este documento de entrada, ou o TES usado para este(s) Pedido(s) de Compra n„o gera(m) duplicata."#CRLF#"Para usar condiÁ„o de pagamento com Adiantamento È necess·rio relacionar um item do documento de entrada, cujo TES gera duplicata, com um Pedido de Compra."
				lRet := .F.
			Else
				Aviso(STR0236,STR0335,{STR0461}) // "N„o h· nenhum Pedido de Compra relacionado com este documento de entrada, ou o TES usado para este(s) Pedido(s) de Compra n„o gera(m) duplicata."#CRLF#"Para usar condiÁ„o de pagamento com Adiantamento È necess·rio relacionar um item do documento de entrada, cujo TES gera duplicata, com um Pedido de Compra."
		   		lRet := .F.
		  	EndIf
		Endif
	EndIf

	RestArea(aAreaSE5)
	RestArea(aAreaSE2)
	RestArea(aAreaSC7)
	RestArea(aArea)

Return(lRet)


/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103NCompAd ≥ Autor ≥Totvs                ≥ Data ≥25.05.2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Realiza a compensacao do Titulo a Pagar quando trata-se da  ≥±±
±±≥          ≥parcela a Vista e o pedido utilizou Adiantamento.           ∫±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ExpL1: Indica se realizou a Compensacao                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpA1: Array com os Pedidos de Compra                       ≥±±
±±≥          ≥ExpA2: Array com o Recno dos titulos gerados                ≥±±
±±≥          ≥ExpL3: Indica se eh compensacao do contas a pagar           ≥±±
±±≥          ≥ExpC4: Numero do Documento de Entrada                       ≥±±
±±≥          ≥ExpC5: Serie do Documento de Entrada                        ≥±±
±±≥          ≥ExpA6: Array com recnos das compensaÁıes para contabilizaÁ„o≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Observacao≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao Efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Static Function A103NCompAd(aPedAdt,aRecGerSE2,lCmp,cDoc,cSerie,aRecSE5)

Local aArea := GetArea()
Local aAreaSE2 := SE2->(GetArea())
Local lContabiliza := .F.
Local lDigita := .F.
Local lAglutina := .F.
Local aCodPedidos	:= {} 	// Recebe o codigo dos Pedidos
Local aRecRet := {}	// Retorno da funcao que carrega os titulos de Adiantamento
Local nI := 0 	// Variavel utilizado em loop
Local nAux := 0 	// Variavel utilizado em loop
Local aRecNo := {}	// Recebe o Recno do Titulo de Adiantamento
Local aRecVlr := {}	// Recebe o valor limite para compensaÁ„o do Titulo de Adiantamento
Local nVlrParc1 := 0	// Valor da primeira parcela da Nota Fiscal
Local aPedidos	:= {}	// Array para ajuste do saldo no relacionamento do Financeiro
Local lRet := .F.
Local lTemPA := .F.
Local aPA := {}
Local nSaldo := 0
Local nContPed := 0
Local cPedFIE  := ""

Default aRecSE5 := {}

//Verifica se h· ao menos 1 parcela nesta venda
If Len(aRecGerSE2) > 0 .and. Len(aPedAdt) > 0

	//Carrega os titulos de Adiantamentos relacionados aos Pedidos da Nota.
	For nI := 1 To Len(aPedAdt)
		aPedidos := {}
		nVlrParc1 := aPedAdt[nI][2]
		nSaldo := 0
		
		// PA's
		aRecRet := FPedAdtPed( "P", { aPedAdt[nI][1] }, .F. )
		For nAux := 1 To Len(aRecRet)
			lTemPA := .F.
			If !Empty(aRecRet[nAux, 3])
				// checa se o saldo atual do adiantamento eh igual ou maior que o valor relacionado no pedido
				SE2->(dbGoto(aRecRet[nAux][2]))
				If SE2->(Recno()) = aRecRet[nAux][2]
					If SE2->E2_SALDO >= SaldoTit(SE2->E2_PREFIXO,SE2->E2_NUM,SE2->E2_PARCELA,SE2->E2_TIPO,SE2->E2_NATUREZ,"P",SE2->E2_FORNECE,SE2->E2_MOEDA,dDataBase,RetDtBxPA(),SE2->E2_LOJA,,0,1)
						If nVlrParc1 >= aRecRet[nAux, 3]
							lTemPA := .T.
							aAdd(aRecVlr,	aRecRet[nAux, 3])
							nVlrParc1 -= aRecRet[nAux, 3]
							nsaldo += aRecRet[nAux, 3]
						ElseIf nVlrParc1 > 0
							lTemPA := .T.
		           	 	aAdd(aRecVlr,	nVlrParc1)
		           		nVlrParc1 := 0
						Endif
						If lTemPA
							aAdd(aRecNo, 	aRecRet[nAux, 2])
							// Array para ajuste do saldo do relacionamento no Financeiro
							aAdd( aPedidos, {aRecRet[nAux, 1], aRecRet[nAux, 2], aRecVlr[Len(aRecVlr)]} )

							// artificio usado para resolver o fato da rotina MaIntBxCP nao ter parametro para compensar o valor informado em um array ( compensacao parcial ),
							// como tem a rotina MaIntBxCR, desta forma, eh passado o parametro recebido como aNDFDados com os valores parciais das compensacoes e a rotina
							// MaIntBxCP irah usar estes valores para realizar a compensacao do PA, ao inves do saldo total do PA.
							SE2->(dbGoto(aRecRet[nAux, 2]))
							If SE2->(Recno()) = aRecRet[nAux, 2]
								aAdd(aPA,{aRecRet[nAux, 2],,FaVlAtuCP("SE2")})
								aPA[Len(aPA)][3][11] := aRecVlr[Len(aRecVlr)]
								aPA[Len(aPA)][3][12] := aRecVlr[Len(aRecVlr)]
							Endif
						Endif
					Endif
				Endif
			Endif
		Next nAux
		aAdd(aCodPedidos, {aPedAdt[nI][1], aClone(aPedidos)} )
	Next nI

	//Carrega o pergunte da rotina de compensaÁ„o financeira
	Pergunte("AFI340",.F.)

	lContabiliza 	:= MV_PAR11 == 1
	lDigita			:= MV_PAR09 == 1

	//Compensa os valores no Financeiro
	For nContPed := 1 To Len(aCodPedidos)
		cPedFIE := aCodPedidos[nContPed][1]
		SE2->(MsGoTo(aRecGerSE2[1]))
		If SE2->(Recno()) = aRecGerSE2[1] .and. Len(aRecNo) > 0 .and. Len(aRecVlr)	> 0
			lRet := MaIntBxCP(2,{aRecGerSE2[1]}, ,aRecNo,,{.F.,lAglutina,lDigita,.F.,.F.,.F.},,,aPA, /*nSaldo*/,,,,aRecSE5,/*lHelp*/,cPedFIE)
		Endif 
	Next nContPed 

	//Retorna o pergunte da MATA103
	Pergunte("MTA103",.F.)

	If lRet .and. Len(aCodPedidos) > 0
		SE2->(MsGoTo(aRecGerSE2[1]))
		If SE2->(Recno()) = aRecGerSE2[1]
			If SE2->E2_VALOR != SE2->E2_SALDO .and. !Empty(SE2->E2_BAIXA) // verifica se o titulo foi baixado
				For nI := 1 To Len(aCodPedidos)

					//Ajuste do saldo do relacionamento no Financeiro
					FPedAdtGrv( "P", 4, aCodPedidos[nI, 1], aCodPedidos[nI, 2], lCmp, cDoc, SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie) )
				Next nI

				// grava registro do titulo principal na tabela FR3
				SE2->(MsGoTo(aRecGerSE2[1]))
				If SE2->(Recno()) = aRecGerSE2[1]
					FaGrvFR3("P",aPedAdt[1][1],SE2->E2_PREFIXO,SE2->E2_NUM,SE2->E2_PARCELA,SE2->E2_TIPO,SE2->E2_FORNECE,SE2->E2_LOJA,SE2->E2_VALOR,cDoc, SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie) )
				Endif
			Else
				lRet := .F.
			Endif
		Endif
	Endif
EndIf

RestArea(aAreaSE2)
RestArea(aArea)

Return(lRet)


/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funcao    ≥A103CCompAd ≥ Autor ≥Totvs                ≥ Data ≥20.05.2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Faz o cancelamento da compensacao do adiantamento           ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥ExpL1: Indica se a Compensacao foi excluida                 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpA1: Array com o Recno dos titulos gerados                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Observacao≥                                                            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥   DATA   ≥ Programador   ≥Manutencao Efetuada                         ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥          ≥               ≥                                            ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Static Function A103CCompAd(aRecSE2)

Local aArea	:= GetArea()
Local aAreaSE2	:= SE2->(GetArea())
Local lContabiliza := .T.
Local lDigita := .T.
Local lAglutina := .F.
Local nCnt := 0 	// Variavel utilizado em loop
Local aRecNoPA := {}	// Recebe o Recno do Titulo de Adiantamento
Local cQ := ""
Local aDocCmp := {}
/* estrutura array aDocCmp
//1 - E5_PREFIXO
//2 - E5_NUMERO
//3 - E5_PARCELA
//4 - E5_TIPO
//5 - E5_CLIFOR
//6 - E5_LOJA
//7 - E5_VALOR
//8 - F1_DOC
//9 - F1_SERIE
//10 - Logico - indica se compensacao foi realizada no momento da geracao do documento de saida
*/
Local nTamPref    := TamSX3("E2_PREFIXO")[1]
Local nTamNum     := TamSX3("E2_NUM")[1]
Local nTamParc    := TamSX3("E2_PARCELA")[1]
Local nTamTipoT   := TamSX3("E2_TIPO")[1]
Local nTamFornece := TamSX3("A2_COD")[1]
Local nTamLoja    := TamSX3("A2_LOJA")[1]
Local nPos 		  := 0
Local aRecnoFR3   := {} // array para guardar o recno dos registros da tabela FR3, referente aos adiantamentos compensados com a nota fiscal, no momento da geracao da nota
Local lRet        := .T.
Local aEstorno    := {} // array para guardar o conteudo do campo E5_DOCUMEN dos registros usados na compensacao
Local aEstornoTmp := {}
Local aDocCmpTmp  := {}
Local cCposSelect :=""

//Verifica se h· ao menos 1 parcela nesta entrada
If Len(aRecSE2) >= 1

	//Carrega array com titulos compensados nesta nota fiscal
	cQ	:= "SELECT E5_DOCUMEN,E5_VALOR,E5_NUMERO,E5_PREFIXO,E5_PARCELA,E5_TIPO,E5_CLIFOR,E5_LOJA,E5_SEQ "
	cQ += "   FROM "+RetSqlName("SE5")+" "
	cQ += "  WHERE E5_FILIAL  = '"+xFilial("SE5")+"' "
	cQ += "    AND E5_RECPAG  = 'P' "
	cQ += "	   AND E5_SITUACA <> 'C' "
	cQ += "	   AND E5_DATA    = '"+dTos(SF1->F1_DTDIGIT)+"'"
	cQ += "	   AND E5_NUMERO  = '"+SF1->F1_DUPL+"'"
	cQ += "	   AND E5_PREFIXO = '"+SF1->F1_PREFIXO+"'"
	cQ += "	   AND E5_CLIFOR  = '"+SF1->F1_FORNECE+"'"
	cQ += "	   AND E5_LOJA    = '"+SF1->F1_LOJA+"'"
	cQ += "	   AND E5_MOTBX   = 'CMP' "
	cQ += "	   AND E5_TIPODOC = 'CP' "
	cQ += "	   AND E5_TIPO    = '"+MVNOTAFIS+"' "
	cQ += "	   AND D_E_L_E_T_ = ' ' "

	cQ := ChangeQuery(cQ)

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQ),"TRBSE5",.T.,.T.)
	TcSetField("TRBSE5","E5_VALOR","N",TamSX3("E5_VALOR")[1],TamSX3("E5_VALOR")[2])

   While !Eof()
		If !TemBxCanc(TRBSE5->(E5_PREFIXO+E5_NUMERO+E5_PARCELA+E5_TIPO+E5_CLIFOR+E5_LOJA+E5_SEQ),.T.)
	   	aAdd(aDocCmpTmp,{Subs(TRBSE5->E5_DOCUMEN,1,nTamPref),Subs(TRBSE5->E5_DOCUMEN,nTamPref+1,nTamNum),Subs(TRBSE5->E5_DOCUMEN,nTamPref+nTamNum+1,nTamParc),;
   		Subs(TRBSE5->E5_DOCUMEN,nTamPref+nTamNum+nTamParc+1,nTamTipoT),Subs(TRBSE5->E5_DOCUMEN,nTamPref+nTamNum+nTamParc+nTamTipoT+1,nTamFornece),;
   		Subs(TRBSE5->E5_DOCUMEN,nTamPref+nTamNum+nTamParc+nTamTipoT+nTamFornece+1,nTamLoja),TRBSE5->E5_VALOR,SF1->F1_DOC,SF1->F1_SERIE,.F.})
   	Endif
   	dbSkip()
   Enddo

   TRBSE5->(dbCloseArea())
   SX3->(DbSetOrder(1))
   SX3->(DbSeek("FR3"))
   While !SX3->(EOF()) .and. SX3->X3_ARQUIVO="FR3"
      cCposSelect+=SX3->X3_CAMPO+","
      SX3->(DbSkip())
   Enddo
	//Carrega array com titulos compensados nesta nota fiscal, da tabela de Documento X Adiantamento
	cQ	:= "SELECT "+cCposSelect+"R_E_C_N_O_ AS FR3_RECNO "
	cQ += "   FROM "+RetSqlName("FR3")+" "
	cQ += "  WHERE FR3_FILIAL = '"+xFilial("FR3")+"' "
	cQ += "    AND FR3_CART   = 'P' "
	cQ += "    AND FR3_TIPO   IN "+FormatIn(MVPAGANT,"/")+" "
	cQ += "	   AND FR3_DOC    = '"+SF1->F1_DOC+"'"
	cQ += "	   AND FR3_SERIE  = '"+SF1->F1_SERIE+"'"
	If lAdtCompart
		cQ += "    AND ((FR3_FILORI = '"+cFilant+"') OR (FR3_FILORI = ' '))"
	EndIf
	cQ += "	   AND D_E_L_E_T_ = ' ' "

	cQ := ChangeQuery(cQ)

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQ),"TRBFR3",.T.,.T.)
	TcSetField("TRBFR3","FR3_VALOR","N",TamSX3("FR3_VALOR")[1],TamSX3("FR3_VALOR")[2])

   While !Eof()
   	nPos := aScan(aDocCmpTmp,{|x| x[1]+x[2]+x[3]+x[4]+Alltrim(Str(x[7]))+x[8]+x[9] == ;
		TRBFR3->(FR3_PREFIX+FR3_NUM+FR3_PARCEL+FR3_TIPO)+Alltrim(Str(TRBFR3->FR3_VALOR))+TRBFR3->(FR3_DOC+FR3_SERIE)})
   	If nPos > 0
	   	aDocCmpTmp[nPos][10] := .T.
	   Endif
	   aAdd(aRecnoFR3,TRBFR3->FR3_RECNO)
   	dbSkip()
   Enddo

   TRBFR3->(dbCloseArea())

	//grava no array aDocCmp soh os adiantamentos que pertencem a compensacao referente a geracao da nota fiscal
	For nCnt:=1 To Len(aDocCmpTmp)
		If aDocCmpTmp[nCnt][10]
			aAdd(aDocCmp,aDocCmpTmp[nCnt])
		Endif
	Next nCnt

   If Len(aDocCmp) > 0
   	//grava array aEstorno com a mesma chave do campo E5_DOCUMEN, para uso na rotina MaIntBxPg
   	For nCnt:=1 To Len(aDocCmp)
	   	aAdd(aEstornoTmp,aDocCmp[nCnt][1]+aDocCmp[nCnt][2]+aDocCmp[nCnt][3]+aDocCmp[nCnt][4]+aDocCmp[nCnt][5]+aDocCmp[nCnt][6]+;
	   	Space(TamSX3("E5_DOCUMEN")[1]-(nTamPref+nTamNum+nTamParc+nTamTipoT+nTamFornece+nTamLoja)))
   	Next nCnt
   	If Len(aEstornoTmp) > 0
   		aAdd(aEstorno,aEstornoTmp)
   	Endif
   	// grava recno dos adiantamentos compensados
   	dbSelectArea("SE2")
   	dbSetOrder(6) // filial+fornece+loja+prefixo+numero+parcela+tipo
   	For nCnt:=1 To Len(aDocCmp)
	   	If dbSeek(xFilial("SE2")+aDocCmp[nCnt][5]+aDocCmp[nCnt][6]+aDocCmp[nCnt][1]+aDocCmp[nCnt][2]+aDocCmp[nCnt][3]+aDocCmp[nCnt][4])
	   		aAdd(aRecnoPA,SE2->(Recno()))
	   	Endif
	   Next nCnt
	   If Len(aRecnoPA) > 0.and. Len(aEstorno) > 0

			//Carrega o pergunte da rotina de compensaÁ„o financeira
			Pergunte("AFI340",.F.)

			lContabiliza 	:= MV_PAR11 == 1
			lDigita			:= MV_PAR09 == 1

			//Excluir Compensacao dos valores no Financeiro
			SE2->(MsGoTo(aRecSE2[1]))
			If SE2->(Recno()) = aRecSE2[1]
				lRet := .F.
				lRet := MaIntBxCP(2,{aRecSE2[1]},,aRecNoPA,,{lContabiliza,lAglutina,lDigita,.F.,.F.,.F.},,aEstorno,,SE2->E2_VALOR)
			Endif

			Pergunte("MTA103",.F.)

			// busca todas as compensacoes referentes a esta nota fiscal e ajusta o valor compensado para cada pedido de compra
			If Len(aRecnoFR3) > 0 .and. lRet
				SE2->(MsGoTo(aRecSE2[1]))
				If SE2->(Recno()) = aRecSE2[1]
					If SE2->E2_VALOR = SE2->E2_SALDO .and. Empty(SE2->E2_BAIXA) // verifica se o titulo esta em aberto
						For nCnt:=1 To Len(aRecnoFR3)
							dbSelectArea("FR3")
							dbGoto(aRecnoFR3[nCnt])
							If Recno() = aRecnoFR3[nCnt]
								SE2->(dbSetOrder(6))
								If SE2->(MsSeek(xFilial("SE2")+FR3->(FR3_FORNEC+FR3_LOJA+FR3_PREFIXO+FR3_NUM+FR3_PARCELA+FR3_TIPO)))

									//Ajuste do saldo do relacionamento no Financeiro
									FPedAdtGrv("P",4,FR3->FR3_PEDIDO,{{FR3->FR3_PEDIDO,SE2->(RecNo()),(FR3->FR3_VALOR*-1)}},.T.,SF1->F1_DOC,SF1->F1_SERIE)
							   Endif
							Endif
						Next nCnt

						//exclui registro do titulo principal da tabela FR3
						SE2->(MsGoTo(aRecSE2[1]))
						If SE2->(Recno()) = aRecSE2[1]
							dbSelectArea("FR3")
							dbSetOrder(3)
							If dbSeek(xFilial("FR3")+"P"+SE2->(E2_FORNECE+E2_LOJA+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO)+SF1->F1_DOC+SF1->F1_SERIE)
								RecLock("FR3",.F.)
								dbDelete()
								MsUnlock()
							Endif
						Endif
					Else
						lRet := .F.
					Endif
				Endif
			Endif
		Endif
	Endif
EndIf

SE2->(RestArea(aAreaSE2))
RestArea(aArea)

Return(lRet)

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥ A103CAT83 ∫Autor   ≥TOTVS 			 ∫ Data ≥  08/09/10   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Descricao ≥ FunÁ„o para Atualizar o Cod.Lanc.CAT83 atravÈs do Produto  ∫±±
±±∫			 ≥ ou da TES												  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±≥Parametros≥ nLinha = Nro da Linha do aCols						  	  ≥±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±≥          |															  ≥±±
±±∫Uso       ≥ MATA103                                                    ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103CAT83(nLinha)
Local cRet  	 := ""
Local cCodLan    := ""
Local aArea	  	 := GetArea()
Local nPosCodLan := GetPosSD1("D1_CODLAN")
Local nPosCodTes := GetPosSD1("D1_TES")
Local nPosCod    := GetPosSD1("D1_COD")

Default nLinha:=N

If SuperGetMv("MV_CAT8309",.F.,.F.) .And. nPosCodLan>0 .And. nPosCodTes>0 .And. nPosCod>0
	cCodLan:= aCols[nLinha][nPosCodLan]
    dbSelectArea("SF4")
    dbSetOrder(1)
	dbSeek(xFilial("SF4")+aCols[nLinha][nPosCodTes])
	if !Eof() .And. cPaisLoc == "BRA"
		cRet:=SF4->F4_CODLAN
	EndIf

	If Len(Trim(cRet)) == 0  //Cod.Lancamento, nao esta preenchido na TES, verifica no Produto
	    dbSelectArea("SB1")
	    dbSetOrder(1)
		dbSeek(xFilial("SB1")+aCols[nLinha][nPosCod])
		If !Eof()
			cRet:=SB1->B1_CODLAN
		EndIf
    EndIf

    //Nao achou o Cod.Lancamento preenchido nos cadastros, porÈm j· foi digitado no aCols, mantÈm o que foi digitado
    //Caso contr·rio, ser· retornado valor obtido na base independente do valor preenchido no aCols
    If Len(Trim(cRet)) == 0 .And. Len(Trim(cCodLan))>0
    	cRet:=cCodLan
  	EndIf
EndIf
//para produtos integrados com WMS, se a TES movimentar estoque carrega o ServiÁo,EndereÁo de Entrada e Tipo de estrutura
If nPosCodTes>0 .And. nPosCod>0 .And. IntWMS(aCols[nLinha][nPosCod])
	SF4->(DbSetOrder(1))
	If SF4->(MsSeek(xFilial("SF4")+aCols[nLinha][nPosCodTes])) .And. SF4->F4_ESTOQUE == "S" .And. cTipo $ "N|D|B"
		WmsAvalSD1("2",,aCols,nLinha,aHeader)
	EndIf
EndIf
RestArea(aArea)
Return (cRet)


/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥ GravaCAT83∫Autor   ≥TOTVS 			 ∫ Data ≥  09/09/10   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Descricao ≥ Gravacao de Dados da CAT83								  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±≥Parametros≥ cOrigem, cChave, cOperacao, nIndice, cCAT83                ≥±±
±±≥          |															  ≥±±
±±∫Uso       ≥ Materiais                                                  ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function GravaCAT83(cOrigem, aChave, cOperacao, nIndice, cCAT83)

Return

/*‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥V103CAT83 ≥ Autor ≥TOTVS 				    ≥ Data ≥16/09/2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥Retorna se a CAT83 esta ativa ou nao                        ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ*/
Function V103CAT83()
Local lRet:=.F.

If SuperGetMv("MV_CAT8309",.F.,.F.)
	lRet:=.T.
EndIf
Return (lRet)
/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103AtuCon≥ Prog. ≥ TOTVS                 ≥Data  ≥01/10/2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Atualiza folder de conferencia fisica                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103ConfPr( ExpO1, ExpA1)                                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpO1 = Objeto do list box                                 ≥±±
±±≥          ≥ ExpA2 = Array com o contudo da list box                    ≥±±
±±≥          ≥ ExpO3 = Objeto para flag do list box                       ≥±±
±±≥          ≥ ExpO4 = Objeto para flag do list box                       ≥±±
±±≥          ≥ ExpO5 = Objeto com total de conferentes na nota            ≥±±
±±≥          ≥ ExpN6 = Variavel de quantidade de conferentes              ≥±±
±±≥          ≥ ExpN7 = Objeto com o status da nota                        ≥±±
±±≥          ≥ ExpN8 = Variavel com a descricao do status da nota         ≥±±
±±≥          ≥ ExpL9 = Habilita recontagem na conferencia (limpa o que foi≥±±
±±≥          ≥         gravado)                                           ≥±±
±±≥          ≥ ExpO10= Objeto timer                                       ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103AtuCon(oList,aListBox,oEnable,oDisable,oConf,nQtdConf,oStatCon,cStatCon,lReconta,oTimer)

Local aArea     := {}
Local cAliasOld := Alias()
Local lWmsNew   := SuperGetMv("MV_WMSNEW",.F.,.F.) .And. SuperGetMV("MV_INTWMS",.F.,.F.)
Local lMTWmsPai := FindFunction("MTWmsPai")
Local oProduto  := Nil

If ValType(oTimer) == "O"
	oTimer:Deactivate()
EndIf
lReconta := If (lReconta == nil,.F.,lReconta)

//Habilita recontagem
If lReconta .And. (Aviso(STR0462,STR0463,{STR0464,STR0465}) == 1)
	If Reclock("SF1",.F.)
		SF1->F1_STATCON := "0"
		SF1->(msUnlock())
	EndIf
	dbSelectArea("CBE")
	dbsetOrder(2)
	MsSeek(xFilial("CBE")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
	While !eof() .and. CBE->CBE_NOTA+CBE->CBE_SERIE == SF1->F1_DOC+SF1->F1_SERIE .and.;
			CBE->CBE_FORNEC+CBE->CBE_LOJA == SF1->F1_FORNECE+SF1->F1_LOJA
		If reclock("CBE",.F.)
			CBE->(dbDelete())
			CBE->(msUnlock())
		EndIf
		dbSelectArea("CBE")
		dbSkip()
	EndDo
Else
	lReconta := .F.
EndIf

aListBox := {}
dbSelectArea("SD1")
aArea := GetArea()

MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE)

While SD1->(!EOF()) .and. SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE == SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE

	If lWmsNew .And. lMTWmsPai
		MTWmsPai(SD1->D1_COD,@oProduto)
	Endif

	If lWmsNew .And. IntWMS(SD1->D1_COD) .And. lMTWmsPai .And. oProduto:aProduto[1][1] <> SD1->D1_COD
		CBN->(MsSeek(xFilial("CBN")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA))

		While CBN->(!EOF()) .and. CBN->CBN_DOC+CBN->CBN_SERIE+CBN->CBN_FORNEC+CBN->CBN_LOJA == SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA
			//Se for a opcao RECONTAGEM, zera tudo o que foi conferido
			If lReconta
				Reclock("CBN",.F.)
				CBN->CBN_QTDCON := 0
				CBN->(MsUnlock())
			EndIf
			aAdd(aListBox,{CBN->CBN_PRODU,CBN->CBN_QTDCON,CBN->CBN_QUANT})
			CBN->(dbSkip())
		End
	Else
		//Se for a opcao RECONTAGEM, zera tudo o que foi conferido
		If lReconta
			Reclock("SD1",.F.)
			SD1->D1_QTDCONF := 0
			SD1->(msUnlock())
		EndIf
		
	EndIf
	aAdd(aListBox,{SD1->D1_COD,SD1->D1_QTDCONF,SD1->D1_QUANT})
	SD1->(DbSkip())
End
If ValType(oList) == "O"
	oList:SetArray(aListBox)
	oList:bLine := { || {If (aListBox[oList:nAT,2] == aListBox[oList:nAT,3],oEnable,oDisable), aListBox[oList:nAT,1], aListBox[oList:nAT,2]} }
	oList:Refresh()
EndIf
RestArea(aArea)
dbSelectArea(cAliasOld)

//Atualiza os Gets
If ValType(oConf) == "O"
	SF1->(dbSkip(-1))
	If !SF1->(BOF())
		SF1->(dbSkip())
	EndIf
	nQtdConf := SF1->F1_QTDCONF
	oConf:Refresh()
EndIf

If ValType(oStatCon) == "O"
	Do Case
	Case SF1->F1_STATCON == '1'
		cStatCon := "NF conferida"
	Case SF1->F1_STATCON == '0'
		cStatCon := "NF nao conferida"
	Case SF1->F1_STATCON == '2'
		cStatCon := "NF com divergencia"
	Case SF1->F1_STATCON == '3'
		cStatCon := "NF em conferencia"
	Case SF1->F1_STATCON == '4'
		cStatCon := "NF Clas. C/ Diver."
	EndCase
	nQtdConf := SF1->F1_QTDCONF
	oStatCon:Refresh()
EndIf
If ValType(oTimer) == "O"
	oTimer:Activate()
EndIf
Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103DetCon≥ Prog. ≥ TOTVS                 ≥Data  ≥01/10/2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Monta listbox com dados da conferencia do produto          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103DetCon(oList,aListBox)                                 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ ExpO1 = Objeto do list box                                 ≥±±
±±≥          ≥ ExpA2 = Array com o contudo da list box                    ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103DetCon(oList,aListBox)
Local cCodPro := aListBox[oList:nAt,1]
Local aListDet := {}
Local oListDet
Local oDlgDet
Local aArea := sGetArea()
Local oTimer
Local bBlock := {|cCampo|(SX3->(MsSeek(cCampo)),X3TITULO())}
Local oIndice
Local aIndice := {}
Local cIndice
Local aIndOrd := {}
Local cKeyCBE  := "CBE_FILIAL+CBE_NOTA+CBE_SERIE+CBE_FORNEC+CBE_LOJA+CBE_CODPRO"
Local aColunas := {}
Local aCpoCBE  := {}
Local nI

sGetArea(aArea,"CBE")
sGetArea(aArea,"SB1")
sGetArea(aArea,"SX3")
sGetArea(aArea,"SIX")

SIX->(DbSetOrder(1))
SIX->(MsSeek("CBE"))
While !SIX->(Eof()) .and. SIX->INDICE == "CBE"
	If SubStr(SIX->CHAVE,1,Len(cKeyCBE)) == cKeyCBE
		aadd(aIndice,SIX->(SixDescricao()))
		If IsDigit(SIX->ORDEM)     // se for numerico o conteudo do ORDEM assume ele mesmo, senao calcula o numero do indice (ex: "A" => 10, "B" => 11, "C" => 12, etc)
			aadd(aIndOrd,Val(SIX->ORDEM))
		Else
			aadd(aIndOrd,Asc(SIX->ORDEM)-55)
		EndIf
	EndIf
	SIX->(DbSkip())
EndDo

dbSelectArea("SX3")
dbSetOrder(1)
MsSeek("CBE")
While !EOF() .And. (x3_arquivo == "CBE")
	If ( x3uso(X3_USADO) .And. cNivel >= X3_NIVEL .and. !(AllTrim(X3_CAMPO) $ cKeyCBE))
		aadd(aCpoCBE,{X3_CAMPO,X3_CONTEXT})
	Endif
	dbSkip()
EndDo

SX3->(DbSetOrder(2))
SB1->(DbSetOrder(1))
SB1->(MsSeek(xFilial("SB1")+cCodPro))

cIndice := aIndice[1]

For nI := 1 to Len(aCpoCBE)
	aadd(aColunas,Eval(bBlock,aCpoCBE[nI,1]))
Next

CBE->(dbsetOrder(2))

DEFINE MSDIALOG oDlgDet TITLE OemToAnsi(STR0493+cCodPro+" "+SB1->B1_DESC) From 0, 0 To 25, 67 OF oMainWnd
oListDet := TWBrowse():New( 02, 2, (oDlgDet:nRight/2)-5, (oDlgDet:nBottom/2)-30,,aColunas,, oDlgDet,,,,,,,,,,,, .F.,, .T.,, .F.,,, )

A103AtuDet(cCodPro,oListDet,aListDet,,aCpoCBE)

@ (oDlgDet:nBottom/2)-25, 005 Say "Ordem " PIXEL OF oDlgDet
@ (oDlgDet:nBottom/2)-25, 025 MSCOMBOBOX oIndice VAR cIndice    ITEMS aIndice    SIZE 180,09 PIXEL OF oDlgDet
oIndice:bChange := {||CBE->(DbSetOrder(aIndOrd[oIndice:nAt])),A103AtuDet(cCodPro,oListDet,aListDet,oTimer,aCpoCBE)}
@  (oDlgDet:nBottom/2)-25, (oDlgDet:nRight/2)-50 BUTTON "&Retorna" SIZE 40,10 ACTION ( oDlgDet:End() ) Of oDlgDet PIXEL

DEFINE TIMER oTimer INTERVAL 1000 ACTION (A103AtuDet(cCodPro,oListDet,aListDet,oTimer,aCpoCBE)) OF oDlgDet
oTimer:Activate()

ACTIVATE MSDIALOG oDlgDet CENTERED

sRestArea(aArea)
Return .T.

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103AtuDet≥ Prog. ≥ TOTVS                 ≥Data  ≥01/10/2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Atualiza array para listbox dos detalhes de conferencia    ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103AtuDet(cCodPro,oListDet,aListDet,oTimer)               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ cCodPro  - Codigo do produto a procurar no CBE             ≥±±
±±≥          ≥ oListDet - Objeto listbox a atualizar                      ≥±±
±±≥          ≥ aListDet - Array do listbox                                ≥±±
±±≥          ≥ oTimer   - Objeto timer a desativar para o processo        ≥±±
±±≥          ≥ aCpoCBE  - Campos do LISTBOX                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ MATA103                                                    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103AtuDet(cCodPro,oListDet,aListDet,oTimer,aCpoCBE)
Local aLine := {},nI
Local uConteudo

If ValType(oTimer) == "O"
	oTimer:Deactivate()
EndIf

aListDet := {}

CBE->(MsSeek(xFilial("CBE")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA+cCodPro))

While !CBE->(eof()) .and. CBE->CBE_NOTA+CBE->CBE_SERIE == SF1->F1_DOC+SF1->F1_SERIE .and.;
		CBE->CBE_FORNEC+CBE->CBE_LOJA == SF1->F1_FORNECE+SF1->F1_LOJA .and. CBE->CBE_CODPRO == cCodPro

	aLine := {}
	For nI := 1 to Len(aCpoCBE)
		If (aCpoCBE[nI,2]) <> 'V'
			uConteudo := CBE->&(aCpoCBE[nI,1])
		Else
			uConteudo := CriaVar(aCpoCBE[nI,1])
		EndIf
		aadd(aLine,uConteudo)
	Next
	aadd(aListDet,aLine)

	CBE->(DbSkip())
EndDo
If Empty(aListDet)
	aLine := {}
	For nI := 1 To Len(aCpoCBE)
		aadd(aLine,CriaVar(aCpoCBE[nI,1],.f.))
	Next
	aadd(aListDet,aLine)
EndIf

oListDet:SetArray( aListDet )
oListDet:bLine := { || RetDetLine(aListDet,oListDet:nAT)  }

oListDet:Refresh()

If ValType(oTimer) == "O"
	oTimer:Activate()
EndIf

Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥RetDetLine≥ Prog. ≥ TOTVS                 ≥Data  ≥01/10/2010≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Funcao para retornar campos para o bLine do listbox        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ RetDetLine(aListDet,nAt)                                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ aListDet - Array com dados do listbox                      ≥±±
±±≥          ≥ nAt      - Linha do listbox                                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ A103AtuDet                                                 ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function RetDetLine( aListDet,nAt)
Local aRet := {}
Local nX:= 0
For nX:= 1 to len(aListDet[nAt])
	aadd(aRet,aListDet[nAt,nx])
Next nX
Return aRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥A103CheckDanfe∫Autor  ≥TOTVS		     ∫ Data ≥  24/05/2011  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥Cria Array com Estrutura dos Campos da Danfe				   ∫±±
±±∫          ≥Embora nem todos os campos possam existir na base, o array   ∫±±
±±∫          ≥ser· criado com todos os elementos, a fim de manter a com-   ∫±±
±±∫          ≥patibilidade com pontos de entrada e com o programa.	       ∫±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ nTipo  1 = Verif.se campos existem na base e emite aviso	   ≥±±
±±≥			 ≥ 		  2 = Verif.se campos existem na base e n„o emite aviso≥±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103CheckDanfe(nTipo)
Local aAreaDanfe	:= GetArea()
Local nI			:= 0
Local aCampos		:= {"F1_TRANSP","F1_PLIQUI","F1_PBRUTO","F1_ESPECI1","F1_VOLUME1","F1_ESPECI2","F1_VOLUME2","F1_ESPECI3","F1_VOLUME3",;
						"F1_ESPECI4","F1_VOLUME4","F1_PLACA","F1_CHVNFE","F1_TPFRETE","F1_VALPEDG","F1_FORRET","F1_LOJARET","F1_TPCTE",;
						"F1_FORENT","F1_LOJAENT","F1_NUMAIDF","F1_ANOAIDF","F1_MODAL","F1_DEVMERC"}

DbSelectArea("SF1")
aNFEDanfe   := {}

For nI := 1 To Len(aCampos)
	If aCampos[nI] == "F1_TPFRETE"
		aaDD(aNFEDanfe, RetTipoFrete(CriaVar(aCampos[nI])))
	Else
		aaDD(aNFEDanfe, CriaVar(aCampos[nI]))
	Endif
Next nI

RestArea(aAreaDanfe)

Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥A103CargaDanfe∫Autor  ≥TOTVS		     ∫ Data ≥  24/05/2011 ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥Carrega Array com os Campos da Danfe				  		  ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103CargaDanfe(l103Class,aNFEletr,aInfAdic)
Local aAreaCargaDanfe:= GetArea()

Default l103Class := .F.
Default aNFEletr  := {}
Default aInfAdic  := {}

DbSelectArea("SF1")
aNFEDanfe   := {}
aaDD(aNFEDanfe, SF1->F1_TRANSP)
aaDD(aNFEDanfe, SF1->F1_PLIQUI)
aaDD(aNFEDanfe, SF1->F1_PBRUTO)
aaDD(aNFEDanfe, SF1->F1_ESPECI1)
aaDD(aNFEDanfe, SF1->F1_VOLUME1)
aaDD(aNFEDanfe, SF1->F1_ESPECI2)
aaDD(aNFEDanfe, SF1->F1_VOLUME2)
aaDD(aNFEDanfe, SF1->F1_ESPECI3)
aaDD(aNFEDanfe, SF1->F1_VOLUME3)
aaDD(aNFEDanfe, SF1->F1_ESPECI4)
aaDD(aNFEDanfe, SF1->F1_VOLUME4)
aaDD(aNFEDanfe, SF1->F1_PLACA)
aaDD(aNFEDanfe, SF1->F1_CHVNFE)
If cPaisLoc == "BRA"
aaDD(aNFEDanfe, iif(FieldPos("F1_TPFRETE")>0, RetTipoFrete(SF1->F1_TPFRETE),""))
EndIf
aaDD(aNFEDanfe, SF1->F1_VALPEDG)
aaDD(aNFEDanfe, SF1->F1_FORRET)
aaDD(aNFEDanfe, SF1->F1_LOJARET)
If cPaisLoc == "BRA"
aaDD(aNFEDanfe, RetTipoCte(SF1->F1_TPCTE))
aaDD(aNFEDanfe, SF1->F1_FORENT)
aaDD(aNFEDanfe, SF1->F1_LOJAENT)
aaDD(aNFEDanfe, SF1->F1_NUMAIDF)
aaDD(aNFEDanfe, SF1->F1_ANOAIDF)
EndIf
aaDD(aNFEDanfe, RetModCte(SF1->F1_MODAL))
aaDD(aNFEDanfe, RetDevMerc(SF1->F1_DEVMERC))

If ExistBlock("M103NFEL") .And. l103Class
	A103NfElet("F1_EST",SF1->F1_EST,aNFEletr,aNFEDanfe,aInfAdic)
EndIf

RestArea(aAreaCargaDanfe)
Return
/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo	 ≥ A103Contr  ≥ Autor ≥ TOTVS       		  ≥ Data ≥ 12/08/10 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Rotina para rastreio de contratos a partir da Nota Fiscal    ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe	 ≥ A103Contr(ExpC1,ExpN1,ExpN2)							        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso		 ≥ SIGACOM													    ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103Contr(cAlias,nReg,nOpc)
LOCAL aAreaCN9   := CN9->(GetArea())
LOCAL aAreaSC7   := SC7->(GetArea())
LOCAL aAreaSD1   := SD1->(GetArea())
LOCAL cAliasSD1  := "SD1"
LOCAL cFilCTR	   := cFilAnt
LOCAL aPedidos   := {}
LOCAL aContratos := {}
LOCAL oDlgCtr
LOCAL oLbxCtr
LOCAL aTitCampos := {" ",OemToAnsi("Contrato"),OemToAnsi("Rev.Contrato"),OemToAnsi("Inicio Contrato"),OemToAnsi("Final Contrato")}
LOCAL oOk        := LoadBitMap(GetResources(), "LBOK")
LOCAL oNo        := LoadBitMap(GetResources(), "LBNO")
LOCAL nOpcCtr    := 1
LOCAL nPos
LOCAL nX
LOCAL cQuery

//Busca Pedidos de Compras relacionados com a Nota de Entrada posicionada:
cAliasSD1 := "SD1TMP"
cQuery	  := "  SELECT * FROM " + RetSqlName('SD1')
cQuery	  += "  WHERE D1_FILIAL   = '" + xFilial('SD1') + "'"
cQuery	  += "    AND D1_DOC      = '" + SF1->F1_DOC + "'"
cQuery	  += "    AND D1_SERIE    = '" + SF1->F1_SERIE + "'"
cQuery	  += "    AND D1_FORNECE  = '" + SF1->F1_FORNECE + "'"
cQuery	  += "    AND D1_LOJA     = '" + SF1->F1_LOJA + "'"
cQuery	  += "    AND D1_PEDIDO  <> ' '"
cQuery	  += "    AND D_E_L_E_T_  = ' '"
cQuery    := ChangeQuery(cQuery)
dbUseArea ( .T., "TOPCONN", TCGENQRY(,,cQuery), cAliasSD1, .F., .T.)

While (cAliasSD1)->(!Eof() .AND. D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA == xFilial('SD1')+SF1->(F1_DOC+F1_SERIE+F1_FORNECE+F1_LOJA))
	If !Empty((cAliasSD1)->D1_PEDIDO)
		nPos := Ascan(aPedidos,{|x| x[01]+x[02] == (cAliasSD1)->(D1_PEDIDO+D1_ITEMPC)})
		If nPos == 0
			aadd(aPedidos,{(cAliasSD1)->D1_PEDIDO,(cAliasSD1)->D1_ITEMPC})
		Endif
	Endif
	(cAliasSD1)->(DbSkip())
EndDo

(cAliasSD1)->(dbCloseArea())

If Empty(aPedidos)
	MsgAlert(STR0474,STR0459)
	RestArea(aAreaSD1)
	RestArea(aAreaSC7)
	RestArea(aAreaCN9)
	Return
Endif

//Busca os contratos relacionados ao Pedido de Compras:
CN9->(DbSetOrder(1))
SC7->(DbSetOrder(1))
For nX:=1 to Len(aPedidos)
	If SC7->(DbSeek(xFilial("SC7")+aPedidos[nX,01]+aPedidos[nX,02])) .AND. !Empty(SC7->C7_CONTRA)
		nPos := Ascan(aContratos,{|x| x[02]+x[03] == SC7->(C7_CONTRA+C7_CONTREV)})
		If nPos == 0
			cFilCTR:= CNTBuscFil(xFilial('CND'),SC7->C7_MEDICAO)
			If CN9->(DbSeek(xFilial("CN9",cFilCTR)+SC7->(C7_CONTRA+C7_CONTREV)))
				aadd(aContratos,{oNo,SC7->C7_CONTRA,SC7->C7_CONTREV,CN9->CN9_DTINIC,CN9->CN9_DTFIM,cFilCTR})
			Endif
		Endif
	Endif
Next

If Empty(aContratos)
	MsgAlert(STR0474,STR0459)
	RestArea(aAreaSD1)
	RestArea(aAreaSC7)
	RestArea(aAreaCN9)
	Return
Endif

If Len(aContratos) > 1
	DEFINE MSDIALOG oDlgCtr FROM 50,40 TO 285,541 TITLE OemToAnsi(STR0475) Of oMainWnd PIXEL

		oLbxCtr := TWBrowse():New( 27,4,243,86,,aTitCampos,,oDlgCtr,,,,,,,,,,,,.F.,,.T.,,.F.,,,)
		oLbxCtr:SetArray(aContratos)
		oLbxCtr:bLDblClick := { || aContratos[oLbxCtr:nAt,1] := If(aContratos[oLbxCtr:nAt,1]:cName=="LBNO", oOk,oNo) }
		oLbxCtr:bLine := { || {aContratos[oLbxCtr:nAT][1],aContratos[oLbxCtr:nAT][2],aContratos[oLbxCtr:nAT][3],aContratos[oLbxCtr:nAT][4],aContratos[oLbxCtr:nAT][5]}}
		oLbxCtr:Align := CONTROL_ALIGN_ALLCLIENT

	ACTIVATE MSDIALOG oDlgCtr CENTERED ON INIT EnchoiceBar(oDlgCtr,{||If(VldSelCtr(oLbxCtr:aArray,aContratos),(nOpcCtr := 1,oDlgCtr:End()),oDlgCtr:End())},{||(nOpcCtr := 0,oDlgCtr:End())})
Endif

If nOpcCtr == 1
	CNTC010( aContratos )
Endif

RestArea(aAreaSD1)
RestArea(aAreaSC7)
RestArea(aAreaCN9)
Return

/*/{Protheus.doc} VldSelCtr

@author Eduardo Riera
@since 14.03.2006
/*/
Static Function VldSelCtr(aLbxCtr,aContratos)
LOCAL nSelOK := 0

aEval(aLbxCtr,{|x| If(x[1]:cName == "LBOK",++nSelOK,0)})

If nSelOK == 0
	MsgAlert(STR0476,STR0459)
	Return .f.
ElseIf nSelOK > 1
	MsgAlert(STR0477,STR0459)
	Return .f.
Endif
aContratos := aClone(aLbxCtr)

Return .t.

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥A103SetRateioBem≥ Rev.  ≥Fernando Radu Muscalu  ≥ Data ≥18.04.2011≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥Transforma o rateio do documento de entrada (SDE) em rateio da  	≥±±
±±≥          ≥ficha de ativo (SNV). 										 	≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥A103SetRateioBem(aRatCC,cItem)	 						      	≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥aRatCC	- Array: Rateio de Compras - Doc. Entrada. 			  	≥±±
±±≥          ≥	aRatCC[i,1] -> char: Item do Documento de Entrada		  		≥±±
±±≥          ≥	aRatCC[i,2] -> array: acols do rateio							≥±±
±±≥          ≥		aRatCC[i,2,j] -> array: linha do acols 						≥±±
±±≥          ≥		aRatCC[i,2,j,1] -> char: item do rateio 					≥±±
±±≥          ≥		aRatCC[i,2,j,2] -> Numeric: Percentual 						≥±±
±±≥          ≥		aRatCC[i,2,j,3] -> char: Centro de Custo 					≥±±
±±≥          ≥		aRatCC[i,2,j,4] -> char: Conta Contabil 					≥±±
±±≥          ≥		aRatCC[i,2,j,5] -> char: Item da Conta Contabil				≥±±
±±≥          ≥		aRatCC[i,2,j,6] -> char: Classe de valor					≥±±
±±≥          ≥		aRatCC[i,2,j,7] -> boolean: 								≥±±
±±≥          ≥cItem		- Char: Item do Documento de Entrada				  	≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Retorno   ≥aRateio	- Array: Rateio de despesas de depreciacao (Grava SNV) 	≥±±
±±≥          ≥	aRateio[i,1] - Char: Codigo do Rateio						  	≥±±
±±≥          ≥	aRateio[i,2] - Char: Revisao do Rateio						  	≥±±
±±≥          ≥	aRateio[i,3] - Char: Status do Rateio						  	≥±±
±±≥          ≥		"2"	- Pendente de classificacao							  	≥±±
±±≥          ≥	aRateio[i,4] - Numeric: Nro da Linha do Grid do Item da		  	≥±±
±±≥          ≥	do Ativo (nAt da GetDados do SN3)							  	≥±±
±±≥          ≥	aRateio[i,5] - Array: Similar ao aCols, com o Rateio		  	≥±±
±±≥          ≥		aRateio[i,5,j] - Array: Linhas do aCols	  				  	≥±±
±±≥          ≥			aRateio[i,5,j,k] - Any: Colunas do aCols			  	≥±±
±±≥          ≥	aRateio[i,6] - Boolean: Demonstra se o item da ficha do Ativo 	≥±±
±±≥          ≥	foi apagado na GetDados do SN3. Se .T. - item apagado 		  	≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥SIGAATF - Localizacao Argentina								  	≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103SetRateioBem( aRatCC, cItem )

Local aRateio	  := {}
Local aAuxRat	  := {}
Local aHeadSNV	  := {}
Local aHeadSDE	  := BuscaSDE()[1]
Local aCloned	  := {}
Local aAreaSN3	  := SN3->(GetArea())
Local nPItem	  := 0
Local nCont		  := 0
Local nI		  := 0
Local nX		  := 0
Local nPos		  := 0
Local lRatAtiv    := SuperGetMv('MV_RATATIV',,.F.)
Local aCodeRateio := {}
Local lRet        := .F.

Default cItem	:= ""

If cPaisLoc != "ARG" .And. !lRatAtiv
	Return(aRateio)
Else
	If Empty(aRatCC) .And. Type("aBackColsSDE") <> "U" .And. !Empty(aBackColsSDE)
		aRatCC := aClone(aBackColsSDE)
	EndIf
Endif

aHeadSNV := AF011HeadSNV()

If Empty(aRatCC)	//Nao e uma inclusao
	If !Empty(SD1->D1_CBASEAF)

		SN3->(DbSetOrder(1))

		If SN3->(DbSeek(xFilial("SN3") + SD1->D1_CBASEAF + "01"))
		    If SN3->N3_RATEIO == "1" .and. !Empty(SN3->N3_CODRAT)
		    	AF012LoadR(aRateio,SN3->N3_CODRAT,1)
		    EndIf
	    Endif

	    RestArea(aAreaSN3)
    Endif
Else

	If !Empty(cItem)
		nPItem := aScan(aRatCC,{|x| alltrim(x[1]) == alltrim(cItem)})
	Endif

	If nPItem > 0

		nCont++

		aCloned := aClone(aRatCC[nPItem,2])

		For nI := 1 to len(aCloned)

			aAdd(aAuxRat, Array( len(aHeadSNV)+ 1 ))

			For nX := 1 to len(aHeadSDE)

				Do Case
				Case alltrim(aHeadSDE[nX,2]) == "DE_ITEM"
					nPos := aScan(aHeadSNV,{|x| alltrim(x[2]) == "NV_SEQUEN" })
				Case alltrim(aHeadSDE[nX,2]) == "DE_PERC"
					nPos := aScan(aHeadSNV,{|x| alltrim(x[2]) == "NV_PERCEN" })
				Case alltrim(aHeadSDE[nX,2]) == "DE_CC"
					nPos := aScan(aHeadSNV,{|x| alltrim(x[2]) == "NV_CC" })
				Case alltrim(aHeadSDE[nX,2]) == "DE_CONTA"
					nPos := aScan(aHeadSNV,{|x| alltrim(x[2]) == "NV_CONTA" })
				Case alltrim(aHeadSDE[nX,2]) == "DE_ITEMCTA"
					nPos := aScan(aHeadSNV,{|x| alltrim(x[2]) == "NV_ITEMCTA" })
				Case alltrim(aHeadSDE[nX,2]) == "DE_CLVL"
					nPos := aScan(aHeadSNV,{|x| alltrim(x[2]) == "NV_CLVL" })
				End Case

				If nPos > 0

					If alltrim(aHeadSDE[nX,2]) == "DE_ITEM"
						aAuxRat[len(aAuxRat),nPos] := Strzero(Val(aCloned[nI,nX]),TamSx3("NV_SEQUEN")[1])
					Else
						aAuxRat[len(aAuxRat),nPos] := aCloned[nI,nX]
					Endif
				Endif

			Next nX

			aAuxRat[len(aAuxRat),len(aHeadSNV)+1] := .f.

			For nX := 1 to len(aHeadSNV)
				If aAuxRat[len(aAuxRat),nX] == nil
					aAuxRat[len(aAuxRat),nX] := CriaVar(aHeadSNV[nX,2])
				Endif
			Next nX

		Next nI

		If lRatAtiv
			aCodeRateio	:= AF011COD()
			SNV->(ConfirmSX8())

			aAdd(aRateio,{aCodeRateio[1],aCodeRateio[2],"3",nCont,aAuxRat,.F.})

			//-- Inclus„o
			lRet := AF011Grv(3,aRateio)
		Else
			aAdd(aRateio,{"",Strzero(0,TamSx3("NV_REVISAO")[1]),"2",nCont,aAuxRat,.F.})
		EndIf
		aAuxRat := {}

	EndIf
Endif

Return(aRateio)
/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥M103LstPre∫Autor  ≥Vendas Cliente      ∫ Data ≥  02/22/11   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥Cria um pedido de venda para uma nova entrega ou fechamento ∫±±
±±∫          ≥do pedido de venda										  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥ LOJA846													  ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/

Static Function M103LstPre()

Local lRet		:= .T.													//Variavel de tratamento para o retorno
Local aArea		:= GetArea()											//Grava a area Atual
Local aAreaSF1	:= SF1->( GetArea() )									//Grava a area Atual
Local aAreaSD1	:= SD1->( GetArea()	)									//Grava a area Atual
Local aAreaSD2	:= SD2->( GetArea()	)									//Grava a area Atual
Local aCab		:= {}													//Array de cabecalho do EXECAUTO
Local aItens	:= {}													//Array dos itens do EXECAUTO
Local aItAux	:= {}													//Array auxiliar para os itens do EXECAUTO
Local cTES		:= ""													//TES usada no item da NF de Remessa
Local cTpOper	:= SuperGetMV("MV_LJLPTIV",,"")							//Tipo da Operacao para o Pedido de Venda (TES Inteligente)
Local cTESPad	:= SuperGetMV("MV_LJLPTSV",,"")							//TES padrao para o Pedido de Venda
Local cLista	:= ""													//Numero da Lista de Presente
Local cNumPV	:= ""													//Numero do pedido de Venda original
Local cNumSC5	:= ""													//Numero do Novo Pedido de Venda
Local cMay		:= ""													//Variavel que trata o novo numero do pedido de venda pelo semaforo
Local cSeqItem	:= Replicate("0",TamSX3("C6_ITEM")[1])					//Sequencia de Item no Pedido de Venda
Local cChaveSF1	:= xFilial("SD1") + SF1->F1_DOC + SF1->F1_SERIE + SF1->F1_FORNECE + SF1->F1_LOJA	//Chave de pesquisa para a tabela SD1
Local aRegCtaC	:= {}													//Array para criar o registro de Credito na tabela de conta corrente
Local aAreaSL1  := SL1->(GetArea())
Local aAreaSL2	:= SL2->(GetArea())
Local aAreaME1  := ME1->(GetArea())
Local nTamItem  := TamSX3("L2_ITEM")[1]
Local cDoc		:= ""

Private lMsErroAuto := .F.												//Variavel usada para o retorno da EXECAUTO

SL1->(DbSetOrder(2)) //Serie + Documento
If SL1->(DbSeek(xFilial("SL1") + SD1->D1_SERIORI + SD1->D1_NFORI))
	SL2->(DbSetOrder(1))
	SL2->(DbSeek(xFilial("SL2") + SL1->L1_NUM + PadR(AllTrim(SD1->D1_ITEMORI) , nTamItem)))
	cLista := SL2->L2_CODLPRE
	cDoc := SL2->L2_DOC
EndIf

//Caso o parametro de Tipo de Operacao e TES estejam em branco e n„o seja item de presente, retorna como falso na funcao
If Empty(cTpOper) .And. Empty(cTESPad) .AND. !Empty(cLista)
	lRet		:= .F.
ElseIf !Empty(cLista)	//Caso o codigo da lista de presentes esteja em branco, retorna para a funcionalidade normal
	DbSelectArea("SC5")
	DbSetOrder(1)	//C5_FILIAL + C5_NUM

	ME1->(DbSetOrder(2)) //Filial Cod Lista
	ME1->(DbSeek(xFilial("ME1") + cLista))

	//Por mais que a lista de presente seja Credito/Etrega È possivel alterar para retirada do item
	//o que muda um pouco a regra.
	If ME1->ME1_TIPO <> "1" .And. Empty(cDoc)

		cNumSC5 := GetSxeNum("SC5","C5_NUM")
		cMay 	:= "SC5" + ALLTRIM( xFilial("SC5") ) + cNumSC5
		While !Eof() .AND. ( DbSeek(xFilial("SC5") + cNumSC5) .OR. !MayIUseCode(cMay) )
			cNumSC5 := Soma1(cNumSC5, TamSX3("C5_NUM")[1] )
			cMay 	:= "SC5" + ALLTRIM( xFilial("SC5") ) + cNumSC5
		End

		DbSeek( xFilial("SC5") + cNumPV )

		Aadd(aCab,{ "C5_FILIAL"	,	xFilial("SC5")		,NIL })
		Aadd(aCab,{ "C5_NUM"	,	cNumSC5				,NIL })
		Aadd(aCab,{ "C5_TIPO"	,	"N"					,NIL })
		Aadd(aCab,{ "C5_CLIENTE",	SF1->F1_FORNECE		,NIL })
		Aadd(aCab,{ "C5_LOJACLI",	SF1->F1_LOJA		,NIL })
		Aadd(aCab,{ "C5_CLIENT"	,	SC5->C5_CLIENT		,NIL })
		Aadd(aCab,{ "C5_LOJAENT",	SC5->C5_LOJAENT		,NIL })
		Aadd(aCab,{ "C5_TRANSP"	,	SC5->C5_TRANSP		,NIL })
		Aadd(aCab,{ "C5_TIPOCLI",	SC5->C5_TIPOCLI		,NIL })
		Aadd(aCab,{ "C5_EMISSAO",	dDataBase			,NIL })
		Aadd(aCab,{ "C5_VEND1"	,	SC5->C5_VEND1		,NIL })
		Aadd(aCab,{ "C5_CONDPAG",	SC5->C5_CONDPAG		,NIL })
		Aadd(aCab,{ "C5_ORCRES"	,	SC5->C5_ORCRES		,NIL })
		Aadd(aCab,{ "C5_FRETE"	,	SC5->C5_FRETE		,NIL })
		Aadd(aCab,{ "C5_SEGURO"	,	SC5->C5_SEGURO		,NIL })
		Aadd(aCab,{ "C5_DESPESA",	SC5->C5_DESPESA		,NIL })
		Aadd(aCab,{ "C5_TPFRETE",	SC5->C5_TPFRETE		,NIL })
		Aadd(aCab,{ "C5_DESC1"	,	SC5->C5_DESC1		,NIL })
	EndIf

	DbSelectArea("SD2")
	DbSetOrder(3)	//D2_FILIAL+D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA+D2_COD+D2_ITEM

	DbSelectArea("SD1")
	DbSetOrder(1)	//D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_COD+D1_ITEM
	DbSeek( cChaveSF1 )
	While !SD1->( Eof() ) .AND. cChaveSF1 == SD1->D1_FILIAL + SD1->D1_DOC + SD1->D1_SERIE + SD1->D1_FORNECE + SD1->D1_LOJA
		aItAux := {}
		If !Empty(cTpOper)
			cTES := MaTESInt(2,cTpOper,ME1->ME1_CODCLI,ME1->ME1_LOJCLI,"C",SD2->D2_COD)
		Else
			cTESPad := cTESPad
		EndIf

		cSeqItem := Soma1(cSeqItem,TamSX3("C6_ITEM")[1])

		//SD2->(DbSetOrder(3))
		//SD2->( DbSeek( xFilial("SD2") + SD1->D1_NFORI + SD1->D1_SERIORI + SD1->D1_FORNECE + SD1->D1_LOJA + SD1->D1_COD + SD1->D1_ITEMORI) )
		SL2->(DbSeek(xFilial("SL2") + SL1->L1_NUM + PadR(AllTrim(SD1->D1_ITEMORI) , nTamItem) ))

		//MsSeek( xFilial("SD2") + PadR(AllTrim(SD1->D1_NFORI), nTamDoc) + PadR(AllTrim(SD1->D1_SERIORI), nTamSerie) + PadR(AllTrim(SD1->D1_FORNECE), nTamCli) + PadR(AllTrim(SD1->D1_LOJA),nTamLoja) + PadR(AllTrim(SD1->D1_COD), nTamCod) + PadR(AllTrim(SD1->D1_ITEMORI), nTamItem) )

		If ME1->ME1_TIPO <> "1" .And. Empty(cDoc)
			aAdd(aItAux,{ "C6_FILIAL"	,xFilial("SC6")	   																			,NIL })
			aAdd(aItAux,{ "C6_ITEM"		,cSeqItem																					,NIL })
			aAdd(aItAux,{ "C6_PRODUTO"	,SD1->D1_COD  																				,NIL })
			aAdd(aItAux,{ "C6_DESCRI"	,PadR(GetAdvFVal("SB1","B1_DESC",xFilial("SB1") + SD1->D1_COD,1,""),TamSX3("C6_DESCRI")[1])	,NIL })
			aAdd(aItAux,{ "C6_UM"		,SD1->D1_UM																					,NIL })
			aAdd(aItAux,{ "C6_QTDVEN"	,SD1->D1_QUANT																				,NIL })
			aAdd(aItAux,{ "C6_PRCVEN"	,Round(SD1->D1_VUNIT,TamSX3("C6_PRCVEN")[2])												,NIL })
			aAdd(aItAux,{ "C6_VALOR"	,Round(SD1->D1_TOTAL,TamSX3("C6_VALOR")[2])													,NIL })
			aAdd(aItAux,{ "C6_TES"		,cTESPad	 																				,NIL })
			aAdd(aItAux,{ "C6_LOCAL"	,SD1->D1_LOCAL																				,NIL })
			aAdd(aItAux,{ "C6_CLI"		,SD1->D1_FORNECE																			,NIL })
			aAdd(aItAux,{ "C6_LOJA"		,SD1->D1_LOJA																	 			,NIL })
			aAdd(aItAux,{ "C6_ENTREG"	,dDataBase																					,NIL })
			aAdd(aItAux,{ "C6_CODLPRE"	,SL2->L2_CODLPRE																			,NIL })
			aAdd(aItAux,{ "C6_ITLPRE"	,SL2->L2_ITLPRE																				,NIL })
			aAdd(aItAux,{ "C6_D1DOC"	,SD1->D1_DOC   																				,NIL })
			aAdd(aItAux,{ "C6_D1ITEM"	,SD1->D1_ITEM  																				,NIL })
			aAdd(aItAux,{ "C6_D1SERIE"	,SD1->D1_SERIE 																				,NIL })
			aAdd(aItens,aItAux)

				//D2_FILIAL+D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA+D2_COD+D2_ITEM

			//Alimenta o array com os itens que serao gravados na tabela de Conta Corrente da Lista de Presentes
			aRegCtaC	:= {}
			aAdd(aRegCtaC,SL2->L2_CODLPRE)		//01 - Codigo da Lista
			aAdd(aRegCtaC,SL2->L2_ITLPRE)		//02 - Item da Lista
			aAdd(aRegCtaC,SD1->D1_COD)			//03 - Codigo do Produto
			aAdd(aRegCtaC,SD1->D1_QUANT)		//04 - Quantidade
			aAdd(aRegCtaC,SD1->D1_TOTAL)		//05 - Valor
			aAdd(aRegCtaC,cEmpAnt)				//06 - Empresa Original
			aAdd(aRegCtaC,cFilAnt)				//07 - Filial Original
			aAdd(aRegCtaC,Nil)					//08 - Numero do Orcamento
			aAdd(aRegCtaC,Nil)					//09 - Item do Orcamento
			aAdd(aRegCtaC,cNumSC5)				//10 - Numero do Pedido de Venda
			aAdd(aRegCtaC,cSeqItem)				//11 - Item do Pedido de Venda
			aAdd(aRegCtaC,SD1->D1_DOC)			//12 - Numero do Documento
			aAdd(aRegCtaC,SD1->D1_SERIE)		//13 - Serie do Documento
			aAdd(aRegCtaC,dDataBase)			//14 - Emissao do documento/titulo
			aAdd(aRegCtaC,NIL)					//15 - Prefixo do Titulo
			aAdd(aRegCtaC,NIL)					//16 - Numero do Titulo
			aAdd(aRegCtaC,NIL)					//17 - Parcela do Titulo
			aAdd(aRegCtaC,NIL)					//18 - Tipo do Titulo
			aAdd(aRegCtaC,SD1->D1_FORNECE)		//19 - Codigo do Cliente
			aAdd(aRegCtaC,SD1->D1_LOJA)			//20 - Loja do Cliente
	    Else

		    //Alimenta o array com os itens que serao gravados na tabela de Conta Corrente da Lista de Presentes
			aRegCtaC	:= {}
			aAdd(aRegCtaC,SL2->L2_CODLPRE)		//01 - Codigo da Lista
			aAdd(aRegCtaC,SL2->L2_ITLPRE)		//02 - Item da Lista
			aAdd(aRegCtaC,SD1->D1_COD)			//03 - Codigo do Produto
			aAdd(aRegCtaC,SD1->D1_QUANT)		//04 - Quantidade
			aAdd(aRegCtaC,SD1->D1_TOTAL)		//05 - Valor
			aAdd(aRegCtaC,cEmpAnt)				//06 - Empresa Original
			aAdd(aRegCtaC,cFilAnt)				//07 - Filial Original
			aAdd(aRegCtaC,SL1->L1_NUM)					//08 - Numero do Orcamento
			aAdd(aRegCtaC,SD1->D1_ITEMORI)					//09 - Item do Orcamento
			aAdd(aRegCtaC,Nil)				//10 - Numero do Pedido de Venda
			aAdd(aRegCtaC,Nil)				//11 - Item do Pedido de Venda
			aAdd(aRegCtaC,SD1->D1_DOC)			//12 - Numero do Documento
			aAdd(aRegCtaC,SD1->D1_SERIE)		//13 - Serie do Documento
			aAdd(aRegCtaC,dDataBase)			//14 - Emissao do documento/titulo
			aAdd(aRegCtaC,NIL)					//15 - Prefixo do Titulo
			aAdd(aRegCtaC,NIL)					//16 - Numero do Titulo
			aAdd(aRegCtaC,NIL)					//17 - Parcela do Titulo
			aAdd(aRegCtaC,NIL)					//18 - Tipo do Titulo
			aAdd(aRegCtaC,SD1->D1_FORNECE)		//19 - Codigo do Cliente
			aAdd(aRegCtaC,SD1->D1_LOJA)			//20 - Loja do Cliente
	    EndIf

		//Chama a rotina que cria o registo de credito na tabela de conta corrente
		If !Lj8GeraCC(aRegCtaC,IIF(ME1->ME1_TIPO <> "1".And.Empty(cDoc),5,6),NIL,.T.)
			lRet := .F.
			RollBackSX8()
			Exit
		EndIf

		SD1->( dbSkip() )
	End

	If lRet .And. Empty(cDoc)
		MSExecAuto({|x,y,z| Mata410(x,y,z)},aCab,aItens,3) //Inclusao

		If lMsErroAuto
			RollBackSX8()
			MostraErro()
			lRet := .F.
		Else
			ConfirmSX8()
		EndIf
	EndIf
EndIf

RestArea(aArea)
RestArea(aAreaSF1)
RestArea(aAreaSD1)
RestArea(aAreaSD2)
RestArea(aAreaSL2)
RestArea(aAreaSL1)
RestArea(aAreaME1)
Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥Ma103PerAut∫Autor  ≥Alvaro Camillo Neto ∫ Data ≥  07/22/11   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥Carrega as variaveis com os parametros da execauto          ∫±±
±±∫          ≥                                                            ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥ AP                                                        ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function Ma103PerAut()
Local nX 		:= 0
Local cVarParam := ""

If Type("aParamAuto")!="U"
	For nX := 1 to Len(aParamAuto)
		cVarParam := Alltrim(Upper(aParamAuto[nX][1]))
		If "MV_PAR" $ cVarParam
			&(cVarParam) := aParamAuto[nX][2]
		EndIf
	Next nX
EndIf
Return

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥RetTipoCte∫Autor  ≥Julio C.Guerato	 ∫ Data ≥  29/12/2011 ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥Retorna o Tipo de CTE								          ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥Mata103                                                     ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function RetTipoCTE(cCTE)
Local aCombo1  :={}
Local aComboCte:={}
Local cTPCTE   := ""
Local nCT      := 0

	aCombo1:=x3CboxToArray("F1_TPCTE")[1]
	aSize(aComboCte,Len(aCombo1)+1)
	For nCT:=1 to Len(aComboCte)
		aComboCte[nCT]:=IIf(nCT==1," ",aCombo1[nCT-1])
	Next nCT
	nCT:=Ascan(aComboCTE, {|x| Substr(x,1,1) == cCTE})
	If nCT>0
		cTPCTE:=aComboCte[nCT]
	EndIf

Return cTPCTE

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥A103CpXml ∫Autor  ≥Jefferson Lima      ∫ Data ≥  25/11/11   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Desc.     ≥ Complementa o Xml recebido pelo EAI para preenchimento das ∫±±
±±∫          ≥ chaves primaria do protheus								  ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥ Integracao OMS x GFE                                       ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103CpXml(  )

Local cRet    		:= PARAMIXB[1]
Local aArea			:= GetArea()
Local oXml	 		:= Nil
Local lRet        := .F.
Local cCGC			:= ""
Local lIntGFE   	:= SuperGetMv('MV_INTGFE',,.F.)

If lIntGFE

	oXml := tXmlManager():New()

	lRet := oXml:Parse(cRet)

	If lRet
		lRet := oXml:XPathHasNode("//MATA103/MATA103_SF1/F1_CGCFOR/value")
		If lRet
			cCgc := AllTrim( oXml:XPathGetNodeValue("//MATA103/MATA103_SF1/F1_CGCFOR", "value") )
			SA2->(DbSetOrder(3))
			If SA2->(MsSeek(xFilial("SA2") + cCgc))
				While SA2->(!Eof()) .And. AllTrim( SA2->A2_CGC ) == cCgc
					If SA2->A2_MSBLQL <> '1'
						If oXml:XPathAddNode("//MATA103/MATA103_SF1","F1_FORNECE", '')
							If oXml:XPathAddAtt("//MATA103/MATA103_SF1/F1_FORNECE","order","98")
								If oXml:XPathAddNode("//MATA103/MATA103_SF1","F1_LOJA"   , '')
									If oXml:XPathAddAtt("//MATA103/MATA103_SF1/F1_LOJA","order","99")
										If oXml:XPathAddNode("//MATA103/MATA103_SF1/F1_FORNECE","value", SA2->A2_COD)
											If oXml:XPathAddNode("//MATA103/MATA103_SF1/F1_LOJA"   ,"value", SA2->A2_LOJA)
												cRet := oXml:Save2String()
											EndIf
										EndIf
									EndIf
								EndIf
							EndIf
						EndIf
						Exit
					EndIf
					SA2->(dbSkip())
				EndDo
			EndIf
		EndIf
	EndIf
EndIf

RestArea(aArea)

Return cRet

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103DigEnd≥ Autor ≥Everton M. Fernandes  ≥ Data ≥ 22/11/11  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Faz o endereÁamento dos itens do DOC de entrada            ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103DigEnd()    	   	                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ Generico                                                   ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103DigEnd(aDigEnd)

	Local nOpca		    := 0
	Local nx            := 0
	Local nOpc		    := 0
	Local nPos		    := 0
	Local aFields   	:= {}
	Local aColsSDB	    := {}
	Local aHeaderSDB	:= {}
	Local aHeaderSD1	:= {}
	Local aAlterFields	:= {}
	Local aDados		:= {}
	Local aButtons	    := {}
	Local oSize		    := Nil
	Local oGetSD1		:= Nil
	Local oGetSDB		:= Nil
	Local oDlgEnd		:= Nil
	Local cTitulo		:= ""
	Local cIniCpos	    := ""
	Local cOldAlias     := Alias(),nOrd:=IndexOrd(),nRecno:=Recno()
	Local lAuto103      := (Type("l103Auto") <> "U" .And. (l103Auto))

	If  !lAuto103  .and. MsgYesNo(OemToAnsi(STR0379), OemToAnsi(STR0380))//"Deseja realizar o endereÁamento dos itens da nota?", "EndereÁar itens"
		//Calcula dimensıes
		oSize := FwDefSize():New()
		oSize:AddObject( "SD1" ,  100, 50, .T., .T. ) // Totalmente dimensionavel
		oSize:AddObject( "SDB" ,  100, 50, .T., .T. ) // Totalmente dimensionavel
		oSize:lProp 	:= .T. // Proporcional
		oSize:aMargins 	:= { 3, 3, 3, 3 } // Espaco ao lado dos objetos 0, entre eles 3
		oSize:Process() 	   // Dispara os calculos

		//Monta a Dialog
		cTitulo:=OemToAnsi(STR0381)  //"CriaáÑo de Lotes na ProduáÑo"
		nOpca := 0
		DEFINE MSDIALOG oDlgEnd TITLE cTitulo FROM oSize:aWindSize[1],oSize:aWindSize[2];
												TO oSize:aWindSize[3],oSize:aWindSize[4] of oMainWnd Pixel

		//Monta o MsGetDados SD1
		aFields := {"D1_ITEM","D1_COD","D1_LOCAL","D1_LOTECTL","D1_NUMLOTE","D1_DTVALID",;
					"D1_QUANT","D1_NUMSEQ","D1_DOC","D1_SERIE","D1_FORNECE","D1_LOJA"}

		DbSelectArea("SX3")
		SX3->(DbSetOrder(2))
		For nX := 1 to Len(aFields)
			If SX3->(DbSeek(aFields[nX]))
				Aadd(aHeaderSD1, {AllTrim(X3Titulo()),;
								SX3->X3_CAMPO,;
								SX3->X3_PICTURE,;
								SX3->X3_TAMANHO,;
								SX3->X3_DECIMAL,;
								SX3->X3_VALID,;
	            			    SX3->X3_USADO,;
	            			    SX3->X3_TIPO,;
	            			    SX3->X3_F3,;
	            			    SX3->X3_CONTEXT})
			Endif
		Next nX
			oGetSD1 := MsNewGetDados():New(oSize:GetDimension("SD1","LININI"),oSize:GetDimension("SD1","COLINI"),;
										oSize:GetDimension("SD1","LINEND"),oSize:GetDimension("SD1","COLEND"),;
										2, "AllwaysTrue", "AllwaysTrue", cIniCpos, aAlterFields,, 999, "AllwaysTrue", "", "AllwaysTrue", oDlgEnd, aHeaderSD1, aDigEnd)

			//Monta o MsGetDados SDB
		aFields := {"DB_ITEM","DB_LOCAL","DB_LOCALIZ","DB_NUMSERI","DB_QUANT","DB_SERVIC","DB_ESTDES"}
		
		//Monta o aHeader
		For nX := 1 to Len(aFields)
			If SX3->(DbSeek(aFields[nX]))
				Aadd(aHeaderSDB, {AllTrim(X3Titulo()),;
								SX3->X3_CAMPO,;
								SX3->X3_PICTURE,;
								SX3->X3_TAMANHO,;
								SX3->X3_DECIMAL,;
								If (aFields[nX]="DB_LOCALIZ","A103VLDCMP('DB_LOCALIZ')", If (aFields[nX]="DB_NUMSERI" ,"A103VLDCMP('DB_NUMSERI')",If (aFields[nX]="DB_QUANT" ,"A103VLDCMP('DB_QUANT')", SX3->X3_VALID))),;
	            			    SX3->X3_USADO,;
	            			    SX3->X3_TIPO,;
	            			    SX3->X3_F3,;
	            			    SX3->X3_CONTEXT})
			Endif
		Next nX
	   	aAlterFields := aClone(aFields)
	   	nPos := aScan(aAlterFields,"DB_LOCAL")
	   	if nPos > 0
	   		aDel(aAlterFields,nPos)
	   		aSize(aAlterFields,len(aAlterFields)-1)
	   	endif

			//Bot„o para geraÁ„o dos n˙meros de sÈrie automaticamente
			AAdd( aButtons ,{STR0494  ,{|| A265GerNS(oGetSDB:aHeader,oGetSD1:aCols[oGetSD1:nAt][GDFieldPos("D1_QUANT",oGetSD1:aHeader)],;
																				oGetSD1:aCols[oGetSD1:nAt][GDFieldPos("D1_QUANT",oGetSD1:aHeader)],;
																				oGetSDB,oGetSD1),oGetSDB:ForceRefresh()} , STR0494 , STR0494 })  //'Gerar n˙meros de SÈrie'
		
			cIniCpos := "DB_ITEM+DB_LOCAL"
			nOpc := GD_INSERT + GD_UPDATE + GD_DELETE
			oGetSDB := MsNewGetDados():New(oSize:GetDimension("SDB","LININI"),oSize:GetDimension("SDB","COLINI"),;
										oSize:GetDimension("SDB","LINEND"),oSize:GetDimension("SDB","COLEND"),;
										nOpc, "AllwaysTrue", "AllwaysTrue", cIniCpos, aAlterFields,, 999, "AllwaysTrue", "", "AllwaysTrue", oDlgEnd, aHeaderSDB, aColsSDB, {||A103CHANGE(oGetSD1,@oGetSDB,"SDB")})

			//FunÁıes para atualizar os grids din‚micamente
			oGetSD1:bChange  := {||A103CHANGE (oGetSD1 ,@oGetSDB ,"SD1"  , @aDados)}
			oGetSD1:bLinhaOK := {||DigEndLOk  (oGetSD1 , oGetSDB ,"SD1"  , @aDados)}
			oGetSDB:bLinhaOK := {||DigEndLOk  (oGetSD1 , oGetSDB ,"SDB"  , @aDados)}
			oGetSDB:bTudoOK  := {||DigEndTdOK (oGetSD1 , oGetSDB ,@aDados)}

			//Ativa a Dialog
			ACTIVATE MSDIALOG oDlgEnd ON INIT EnchoiceBar(oDlgEnd,{||nOpca:=1,if(oGetSDB:TudoOk(),oDlgEnd:End(),nOpca := 0)},{||oDlgEnd:End()},,aButtons)
		
		dbSelectArea(cOldAlias)
		dbSetOrder(nOrd)
		dbGoto(nRecno)
	EndIf

Return NIL

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103CHANGE≥ Autor ≥Everton M. Fernandes  ≥ Data ≥ 22/11/11  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Atualiza o Grid SDB							              ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103CHANGE()    	   	                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ A103DigEnd()                                               ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function  A103CHANGE(oGetSD1, oGetSDB, cTab, aDados)

Local nLen, nLinha
Local nPos	:= 0
Local cItem

LOCAL cOldAlias:=Alias(),nOrd:=IndexOrd(),nRecno:=Recno()

Do Case
Case cTab = "SD1"
	//Carrega o aCols
	oGetSDB:aCols := {}
	cItem := GDFieldGet("D1_ITEM",oGetSD1:nAt,,oGetSD1:aHeader,oGetSD1:aCols)
	nPos := aScan(aDados, {|x| alltrim(x[1]) == cItem})

	If nPos <= 0
		DigEndLine(@oGetSDB, oGetSD1) //Inicia uma linha em branco
	Else
		If Len(aDados[nPos,3]) == 0
			DigEndLine(@oGetSDB, oGetSD1)
		Else
			aColsSDB := aDados[nPos,3]
			oGetSDB:aCols := aClone(aColsSDB)
			oGetSDB:lNewLine := .F.
		EndIf
		oGetSDB:Refresh()
	EndIf
Case cTab = "SDB"
	//Auto incremento do campo DB_ITEM
	nLen := Len(oGetSDB:aCols)
	nLinha := oGetSDB:nAt
	cItem := GDFieldGet("DB_ITEM",nLinha,,oGetSDB:aHeader,oGetSDB:aCols)
	nPos := GDFieldPos("DB_ITEM",oGetSDB:aHeader)
	if nLinha = nLen  .and. CtoN(cItem,10) <> nLen
		oGetSDB:aCols[nLinha][nPos] := STRZERO(nLen,4)
	endif
	//Preenche o campo DB_LOCAL
	nPos := GDFieldPos("DB_LOCAL",oGetSDB:aHeader)
	oGetSDB:aCols[nLinha][nPos] := GDFieldGet("D1_LOCAL",oGetSD1:nAt,,oGetSD1:aHeader,oGetSD1:aCols)
EndCase
oGetSDB:Refresh()

dbSelectArea(cOldAlias)
dbSetOrder(nOrd)
dbGoto(nRecno)

Return

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥A103VLDCMP≥ Autor ≥Everton M. Fernandes  ≥ Data ≥ 22/11/11  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Faz a validaÁ„o dos campos do grid de endereÁamento        ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103VLDCMP(cCampo)  	                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ A103DigEnd()                                               ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103VLDCMP(cCampo)
	Local lRet 			:= .T.
	Local cOldAlias:=Alias(),nOrd:=IndexOrd(),nRecno:=Recno()

	DO CASE
	CASE cCampo = "DB_LOCALIZ"
		lRet := ExistCpo("SBE",GDFieldGet("DB_LOCAL",,,aHeader,aCols)+M->DB_LOCALIZ)
	CASE cCampo = "DB_NUMSERI"
		If allTrim(M->DB_NUMSERI) <> "" .and. M->DB_NUMSERI <> nil
			If GDFieldGet("DB_QUANT") > 1
				lRet := .F.
				Help(" ",1,"A103NSERI")//"Para informar o n∫ de sÈrie a quantidade deve ser igual a 1."
			else
				aCols[N][GDFieldPos("DB_QUANT")]:=1
			endif
		EndIf
	CASE cCampo = "DB_QUANT"
		If M->DB_QUANT <> 1
			If allTrim(GDFieldGet("DB_NUMSERI")) <> ""
				lRet := .F.
				Help(" ",1,"A103QTSERI")//Para este item a quantidade deve ser igual a 1, pois foi informado um n∫ de sÈrie."
			endif
		EndIf
	ENDCASE

	dbSelectArea(cOldAlias)
	dbSetOrder(nOrd)
	dbGoto(nRecno)
Return lRet

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥DigEndLOk ≥ Autor ≥Everton M. Fernandes  ≥ Data ≥ 22/11/11  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Faz a validaÁ„o da linha do grid de endereÁamento          ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ A103LtLinOK(cCampo) 	                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ A103DigEnd()                                               ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function DigEndLOk(oGetSD1, oGetSDB, cTab, aDados, lValida)

Local xCampo		:= Nil
Local xSerie		:= Nil
Local lRet			:= .T.
Local lAchou		:= .F.
Local nLen			:= 0
Local nLenY		:= 0
Local nX			:= 0
Local nY 			:= 0
Local nCont 		:= 0
Local nTotal 		:= GdFieldGet("D1_QUANT",oGetSD1:nAt,,oGetSD1:aHeader,oGetSD1:aCols)
Local nPosNumSer	:= GdFieldPos("DB_NUMSERI"	,oGetSDB:aHeader)
Local nPosLocaliz	:= GdFieldPos("DB_LOCALIZ"	,oGetSDB:aHeader)
Local nPosLocal	:= GdFieldPos("DB_LOCAL"	,oGetSDB:aHeader)
Local nPosQtd		:= GdFieldPos("DB_QUANT"	,oGetSDB:aHeader)
Local cItem 		:= GDFieldGet("D1_ITEM",oGetSD1:nAt,,oGetSD1:aHeader,oGetSD1:aCols)
Local cLocal   	:= GdFieldGet("DB_LOCAL"	,oGetSDB:nAt,,oGetSDB:aHeader,oGetSDB:aCols)
Local cProd		:= GdFieldGet("D1_COD"		,oGetSD1:nAt,,oGetSD1:aHeader,oGetSD1:aCols)
Local cSeek 		:= ""
Local cEnd 		:= ""
Local aColsEx 	:= {}
Local cOldAlias:=Alias(),nOrd:=IndexOrd(),nRecno:=Recno()
Local lMT103END:= .T.

Default lValida := .T.

Do Case
Case cTab = "SD1"
	lRet:=DigEndLOk(oGetSD1,oGetSDB,"SDB",@aDados, !oGetSDB:lNewLine ) //Valida o grid 2 antes de mudar de linha
	If lRet
		//Salva os dados do aCols
		nPos := aScan(aDados, {|x| allTrim(x[1]) == allTrim(cItem)})

		If oGetSDB:lNewLine //Retira linha em branco do aCols
			nLen :=  Len(oGetSDB:aCols)
			aDel(oGetSDB:aCols, nLen)
			aSize(oGetSDB:aCols, nLen - 1)
		EndIf

		If nPos <= 0
			If Len(oGetSDB:aCols) > 0
				aAdd(aDados,{cItem, cProd, oGetSDB:aCols})
			EndIf
		Else
			aDados[nPos,1] := cItem
			aDados[nPos,2] := cProd
			aDados[nPos,3] := aClone(oGetSDB:aCols)
		EndIf
	endif
Case cTab = "SDB"
	If lValida .AND. !oGetSDB:aCols[oGetSDB:nAT,Len(oGetSDB:aCols[oGetSDB:nAT])]
		nLen := len(oGetSDB:aCols)
		//Valida o campo EndereÁo
		xCampo := AllTrim(oGetSDB:aCols[oGetSDB:nAt, nPosLocaliz])
	  	xSerie := AllTrim(oGetSDB:aCols[oGetSDB:nAt, nPosNumSer])

		If lRet .and. ((xCampo = "" .or. xCampo = Nil) .And. ( xSerie = "" .or. xSerie = Nil))
			Help(" ",1,"A103END")
			lRet := .F.
		EndIf

		//Verifica se o endereÁo suporta a qtd a endereÁar
		If lRet
			nCont := 0
			For nX:= 1 To nLen
				cEnd :=  allTrim(oGetSDB:aCols[nX, nPosLocaliz])
				If !oGetSDB:aCols[nX,Len(oGetSDB:aCols[nX])] .And. xCampo=cEnd
					nCont += oGetSDB:aCols[nX, nPosQtd]
				EndIf
	 		next nX
			For nX:= 1 to Len(aDados)
				If aDados[nX,1] != cItem
					aColsEx := aClone(aDados[nX,3])
					nLenY := Len(aColsEx)
					For nY:= 1 to nLenY
						cEnd :=  allTrim(aColsEx[nY, nPosLocaliz])
						If !aColsEx[nY,Len(aColsEx[nY])] .And. xCampo = cEnd
							nCont += aColsEx[nY, nPosQtd]
						EndIf
			 		Next nY
				EndIf
			Next nX
	 		lRet := Capacidade(cLocal,xCampo,nCont,cProd)
		 endif

		//Valida o campo Quantidade
		xCampo := oGetSDB:aCols[oGetSDB:nAt, nPosQtd]

		If lRet .and. xCampo > 0
			//Totaliza os itens do Grid 2
			nCont := 0
			For nX:= 1 to nLen
				If !oGetSDB:aCols[nX][len(oGetSDB:aCols[nX])] //se a linha n„o estiver deletada...
					xCampo := oGetSDB:aCols[nX, nPosQtd]
					nCont += xCampo
				EndIf
			Next nX

			If nCont > nTotal
				Help(" ",1,"A103QTD")//"A quantidade dos itens n„o pode ser maior que a quantidade do produto."
				lRet := .F.
			EndIf
		ElseIf lRet
			Help(" ",1,"A103QTD0")	//"A quantidade do item deve ser maior que 0."
			lRet := .F.
		EndIf

		//Valida o campo Num. Serie
		xCampo := oGetSDB:aCols[oGetSDB:nAt, nPosNumSer]
		//Verifica se ja nao existe um numero de serie p/ este produto neste almoxarifado.
		If lRet .And. !Empty(AllTrim(xCampo))
			dbSelectArea("SBF")
			dbSetOrder(4)
			cSeek 	:= xFilial("SBF")+cProd+xCampo
			nX 		:= 1
			While !lAchou .And. nX <= nLen
				lAchou := nX != oGetSDB:nAt .And. oGetSDB:aCols[nX,nPosNumSer] == xCampo .AND. oGetSDB:aCols[nX,nPosLocal] == cLocal .AND. !oGetSDB:aCols[nX][len(oGetSDB:aCols[nX])]
				nX ++
			EndDo
			nX 		:= 1
			While !lAchou .And. nX <= Len(aDados)
				If aDados[nX,1] != cItem .And. aDados[nX,2] == cProd
					aColsEx := aClone(aDados[nX,3])
					lAchou := ASCAN(aColsEx,{|x| x[nPosNumSer] == xCampo .And. x[nPosLocal] == cLocal}) > 0
				EndIf
			    nX++
			EndDo
			If lAchou .Or. (dbSeek(cSeek) .And. QtdComp(BF_QUANT) > QtdComp(0))
				Help(" ",1,"NUMSERIEEX")
				lRet:=.F.
			EndIf
		EndIf
		//Ponto de entrada para validar o produto/armazem/endereÁo digitados em cada linha
		if lRet .AND. ExistBlock("MT103END")
			lMT103END:=ExecBlock("MT103END",.F.,.F.,{cProd,cLocal,GdFieldGet("DB_LOCALIZ"	,oGetSDB:nAt,,oGetSDB:aHeader,oGetSDB:aCols)})
			If ValType(lMT103END)<>'L'
				lMT103END:= .T.
			EndIf
			lRet:= lMT103END
		EndIf
	endif
EndCase

dbSelectArea(cOldAlias)
dbSetOrder(nOrd)
dbGoto(nRecno)
return lRet

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥DigEndTdOK≥Autor ≥Everton M. Fernandes  ≥ Data ≥ 22/11/11   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Faz a validaÁ„o do grid de endereÁamento                   ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ DigEndTdOK()     	                                      ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ A103DigEnd()                                               ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function DigEndTdOK(oGetSD1, oGetSDB, aDados)
	Local lRet
	Local nX, nY, nLenX, nLenY, nPos
	Local cItem 	:= ""
	Local cProd 	:= ""
	Local cNumSeq	:= ""
	Local cDoc 		:= ""
	Local cSerie 	:= ""
	Local cCliFor	:= ""
	Local cLoja 	:= ""
	Local cLocal 	:= ""
	Local cLote 	:= ""
	Local cSubLote	:= ""
	Local cNumSeri	:= ""
	Local cLocaliz	:= ""
	Local nQuant	:= 0

	lRet := DigEndLOk(oGetSD1, oGetSDB, "SD1", @aDados)
	Begin Transaction
		If lRet
			nLenX := Len(oGetSD1:aCols)
			For nX:=1 to nLenX
				cItem 	:= GDFieldGet("D1_ITEM"		,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Item
				cProd 	:= GDFieldGet("D1_COD"		,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Produto
				cNumSeq	:= GDFieldGet("D1_NUMSEQ"	,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Num Sequencial
				cDoc 	:= GDFieldGet("D1_DOC"		,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Num Documento
				cSerie 	:= GDFieldGet("D1_SERIE"	,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Serie da nota
				cCliFor	:= GDFieldGet("D1_FORNECE"	,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Fornecedor
				cLoja 	:= GDFieldGet("D1_LOJA"		,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Loja
				cLocal 	:= GDFieldGet("D1_LOCAL"	,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Armazem
				cLote 	:= GDFieldGet("D1_LOTECTL"	,nX,,oGetSD1:aHeader,oGetSD1:aCols) //Lote
				cSubLote:= GDFieldGet("D1_NUMLOTE"	,nX,,oGetSD1:aHeader,oGetSD1:aCols) //SubLote
				nPos 	:= Ascan(aDados,{|x| x[1]== cItem})
				nLenY	:= If(nPos > 0, Len(aDados[nPos,3]), 0)
				For nY:= 1 to nLenY
					If !aDados[nPos, 3, nY, Len(aDados[nPos, 3, nY])] //Se a linha n„o estiver deletada...
						cNumSeri 	:= GDFieldGet("DB_NUMSERI"		,nY,,oGetSDB:aHeader,aDados[nPos,3]) //Num Serie
						cLocaliz 	:= GDFieldGet("DB_LOCALIZ"		,nY,,oGetSDB:aHeader,aDados[nPos,3]) //EndereÁo
						nQuant		:= GDFieldGet("DB_QUANT"		,nY,,oGetSDB:aHeader,aDados[nPos,3]) //Quantidade
						lRet := A100Distri( cProd, cLocal, cNumSeq, cDoc, cSerie, cCliFor, cLoja, cLocaliz,	cNumSeri, nQuant,cLote,cSubLote)
					EndIf
				Next nY
			next nX
		endif
	End Transaction
Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funáao    ≥ A103FldOk   ≥ Autor ≥ Allyson Freitas       ≥ Data ≥ 12.01.2012 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Descriáao ≥ Valida permissao de Produto                                     ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ MATA103                                                         ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function A103FldOk()
Local lRet := .T.
Local cFieldSD1 := ReadVar()
Local cFieldEdit:= SubStr(cFieldSD1,4,Len(cFieldSD1))
Local nPProduto := aScan(aHeader,{|x| AllTrim(x[2])== "D1_COD"})

If Altera
	//Verifica se o usuario tem permissao de alteracao.
	If cFieldEdit $ "D1_COD"
		If IsInCallStack("MATA103") //Documento de Entrada
			lRet := MaAvalPerm(1,{cCampo,"MTA103",5}) .And. MaAvalPerm(1,{aCols[n][nPProduto],"MTA103",3})
		ElseIf IsInCallStack("MATA102N") // Remito de Entrada
			lRet := MaAvalPerm(1,{cCampo,"MT102N",5}) .And. MaAvalPerm(1,{aCols[n][nPProduto],"MT102N",3})
		ElseIf IsInCallStack("MATA101N") // Factura de Entrada
			lRet := MaAvalPerm(1,{cCampo,"MT101N",5}) .And. MaAvalPerm(1,{aCols[n][nPProduto],"MT101N",3})
		EndIf
		If !lRet
			Help(,,1,'SEMPERM')
		EndIf
	Else
		If IsInCallStack("MATA103") //Documento de Entrada
			lRet := MaAvalPerm(1,{aCols[n][nPProduto],"MTA103",4})
		ElseIf IsInCallStack("MATA102N") // Remito de Entrada
			lRet := MaAvalPerm(1,{aCols[n][nPProduto],"MT102N",4})
		ElseIf IsInCallStack("MATA101N") // Factura de Entrada
			lRet := MaAvalPerm(1,{aCols[n][nPProduto],"MT101N",4})
		EndIf
		If !lRet
			Help(,,1,'SEMPERM')
		EndIF
	EndIf
EndIf

Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥IntegDef  ∫Autor  ≥ Marcelo C. Coutinho  ∫ Data ≥  29/11/11   ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Descricao ≥ Mensagem ⁄nica												∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥ Mensagem ⁄nica                                            	∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function IntegDef( cXML, nTypeTrans, cTypeMessage, cVersion )
Local aRet := {}

aRet := MATI103(cXml, nTypeTrans, cTypeMessage, cVersion)

Return aRet

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÑo    ≥DigEndLine≥ Autor ≥Everton M. Fernandes  ≥ Data ≥ 18/01/12  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÑo ≥ Inicia uma linha no de distribuiÁ„o 		                  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Sintaxe   ≥ DigEndLine(oGetSDB, oGetSD1)                               ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Uso       ≥ A103DigEnd()                                               ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function DigEndLine(oGetSDB, oGetSD1)
	Local nPos := 0

	oGetSDB:AddLine()
	oGetSDB:aCols[oGetSDB:nAt][1] := STRZERO(Len(oGetSDB:aCols),4)
	nPos := GDFieldPos("DB_LOCAL",oGetSDB:aHeader)
	oGetSDB:aCols[oGetSDB:nAt][nPos] := GDFieldGet("D1_LOCAL",oGetSD1:nAt,,oGetSD1:aHeader,oGetSD1:aCols)
Return

/*/
¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶
¶¶+-------------------------------------------------------------------------------+	¶¶
¶¶¶Programa  ¶ MA103DIV1 ¶ Autor SILVIA MONICA ¶  Data ¶ 05/05/11               	¶¶
¶¶+----------+---------------------------------------------------------------------	¶¶
¶¶¶DescriÁ‡o ¶ Selecao de Divergencias da Nota Fiscal Entrada	        	        ¶¶
¶¶+----------+---------------------------------------------------------------------	¶¶
¶¶¶Uso       ¶ Especifico para CNI                                                 	¶¶
¶¶+------------------------------------------------------------------------------+  ¶¶
¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶
/*/

Static Function  _MA103Div1()

Local aArea		:= GetArea()
Local oDlg
Local cTitulo  := STR0490
Local lMark    := .F.
Local oOk      := LoadBitmap( GetResources(), "CHECKED" )   //CHECKED    //LBOK  //LBTIK
Local oNo      := LoadBitmap( GetResources(), "UNCHECKED" ) //UNCHECKED  //LBNO
Local oChk1
Local oChk2

Private lChk1 := .F.
Private lChk2 := .F.

dbSelectArea("COF")
dbSetOrder(1)
dbSeek(xFilial("COF"))

//Carrega o vetor conforme a condicao
IF  (Len( _aDivPNF ) == 0)
	While !Eof() .And. COF_FILIAL == xFilial("COF")
	   aAdd(_aDivPNF, { if(Inclui,	lMark, CA040VER(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,COF->COF_CODIGO)) , ;
	   							COF_DESCRI,;
	   							COF_CODIGO})
	   dbSkip()
	End
ENDIF

//Monta a tela para usuario visualizar inclusao
If Len( _aDivPNF ) == 0
   Aviso( cTitulo, STR0466, {"Ok"} )
   Return
Endif

DEFINE MSDIALOG oDlg TITLE cTitulo FROM 0,0 TO 240,500 PIXEL

@ 10,10 LISTBOX oLbx FIELDS HEADER " ", STR0467 ;
   SIZE 230,095 OF oDlg PIXEL ON dblClick(_aDivPNF[oLbx:nAt,1] := !_aDivPNF[oLbx:nAt,1])

oLbx:SetArray( _aDivPNF )

oLbx:bLine := {|| { Iif(_aDivPNF[oLbx:nAt,1],oOk,oNo),  ;
						 _aDivPNF[oLbx:nAt,2]}}

//utilizando a funÁ„o aEval()
@ 110,10 CHECKBOX oChk1 VAR lChk1 PROMPT STR0468 SIZE 70,7 PIXEL OF oDlg ;
         ON CLICK( aEval( _aDivPNF, {|x| x[1] := lChk1 } ),oLbx:Refresh() )

@ 110,95 CHECKBOX oChk2 VAR lChk2 PROMPT STR0469 SIZE 70,7 PIXEL OF oDlg ;
         ON CLICK( aEval( _aDivPNF, {|x| x[1] := !x[1] } ), oLbx:Refresh() )

DEFINE SBUTTON FROM 107,213 TYPE 1 ACTION oDlg:End() ENABLE OF oDlg

ACTIVATE MSDIALOG oDlg CENTER

RestArea(aArea)

Return()

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo	 ≥A103CompAdR≥ Autor ≥ Carlos Capeli      ≥ Data ≥ 22/08/2012 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Chamada da funÁ„o de compensacao do Titulo a Pagar quando  ≥±±
±±≥          ≥ trata-se de pedido com Adiantamento						  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥Parametros≥ExpA1: Array com os Pedidos de Compra                       ≥±±
±±≥          ≥ExpA2: Array com o Recno dos titulos gerados                ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function A103CompAdR(aPedAdt,aRecGerSE2,aRecSE5)

Local aAreaAnt := GetArea()
Local aAreaSE2 := SE2->(GetArea())
Local nCntAdt  := 0
Local nValTit	 := 0
Local nX		 := 0
Local nZ		 := 0
Local aBkpPedAdt := {}
Local aRecRet	 := {}
Local nValRetPed := 0
Local lElimRes	 := SuperGetMV("MV_ESLDFIE",.F.,.T.) //Indica se elimina resÌduo na tabela FIE (Zerando o FIE_SALDO quando o PC estiver 100% entregue) respeitando o legado

Default aPedAdt := {}
Default aRecGerSE2 := {}
Default aRecSE5 := {}

If Len(aPedAdt) > 0 .and. Len(aRecGerSE2) > 0
	//Valor utilizado no adiantamento deve ser no maximo igual a primeira parcela do documento.
	SE2->(MsGoTo(aRecGerSE2[1]))
	nValTit := SE2->E2_VALOR

	aBkpPedAdt := aClone(aPedAdt) 
	For nX := 1 To Len(aPedAdt)
		aRecRet := FPedAdtPed( "P", { aPedAdt[nX][1] }, .F. )
		
		If Len(aRecRet) > 0
			nValRetPed := 0
			For nZ := 1 To Len(aRecRet)
				nValRetPed += aRecRet[nZ,3] 
			Next nZ 
		Endif

		If nValTit < aPedAdt[nX][2]
			If nValTit < nValRetPed
				aPedAdt[nX][2] := nValTit
			Else
				aPedAdt[nX][2] := nValRetPed
			EndIf
		EndIf
	Next nX

	If A103NCompAd(aPedAdt,aRecGerSE2,.T.,cNFiscal, SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie), aRecSE5 )
		If lElimRes
			//Elimina o saldo do relacionamento de pedidos finalizados
			For nCntAdt := 1 To Len(aPedAdt)
				cQuery  := ""
				cQuery  += "SELECT COUNT(*) NREG "
				cQuery  += "  FROM "+RetSqlName("SC7")+" "
				cQuery  += " WHERE C7_FILENT  = '"+xFilial("SC7")+"' "
				cQuery  += "   AND C7_NUM     = '"+aPedAdt[nCntAdt][1]+"' "
				cQuery  += "   AND C7_RESIDUO <> 'S' "
				cQuery  += "   AND C7_QUANT   > C7_QUJE "
				cQuery  += "   AND D_E_L_E_T_ = ' ' "

				cQuery := ChangeQuery(cQuery)
				dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),"A103GRAVA",.F.,.T.)

				If NREG = 0
					FPedAdtRsd("P",{aPedAdt[nCntAdt][1]})
				Endif
				A103GRAVA->(dbCloseArea())
			Next nCntAdt
		Endif
	Endif
Endif
RestArea(aAreaSE2)
RestArea(aAreaAnt)
Return


/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒø±±
±±≥Funáao    ≥ MA103CkAIC≥ Autor ≥ TOTVS S.A            ≥ Data ≥ 18/09/12 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Funcao: Os Documentos de entrada vinculados a pedidos de   ≥±±
±±≥			 ≥ compra analisam a regra de tolerancia, caso as entradas    ≥±±
±±≥			 ≥ ultrapassem os percentuais definidos pela regra o documento≥±±
±±≥			 ≥ de entrada sera bloqueado.		    					  ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ EST/PCP/FAT/COM	                                          ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Function MA103CkAIC(cCodFor,cLoja,cProduto)
Local lRet := .F.

//-- Executar a funcao maavaltoler passando o 12o parametro como .T., permite saber se ha tolerancia cadastrada para o Fornecedor/Produto sem
//-- avaliar o bloqueio. O bloqueio sera analisado posteriormente.
lRet := MaAvalToler(cCodFor,cLoja,cProduto,,,,,,,,,.T.)[1]

Return(lRet)

//-----------------------------------------------------
/*/	Integra o Documento de Entrada com o SIGAGFE
@author Felipe Machado de Oliveira
@version P11
@since 22/05/2013
/*/
//------------------------------------------------------
Function A103VlIGfe(lIsIncl,lIsClass, lCommit,cNumNfGFE)
Local lRet := .T.
Local aDados := {}
Local aDadosIten := {}
Local nI := 0
Local cTpFrete := ""
Local nVlrIt	:= 0

Default cNumNfGFE := ""

If Type("aNfeDanfe") == "A"
	If !Empty(aNfeDanfe[14])
		cTpFrete := SubStr(aNFEDanfe[14],1,1)
	Else
		//Se o 'aNfeDanfe[14]' estiver vazio significa que o tipo de frete n„o foi informado (sem frete)
		//ent„o forcei o "S" para que n„o haja integraÁ„o com o GFE
		cTpFrete := "S"
	Endif
Endif

// Tratamento para quando o parametro MV_TPNRNFS = 3 para controlar a numeracao da nota pela SD9
// a variavel cNFiscal estara em branco e o numero da nota estara armazenado em cNumNfGFE
If Empty(cNumNfGFE)
	cNumNfGFE := cNFiscal 
EndIf

//IntegraÁ„o Protheus com SIGAGFE
If (cTpFrete <> "S") .And. SuperGetMV("MV_INTGFE",.F.,.F.) .And. SuperGetMV("MV_INTGFE2",.F.,"2") $ "1" .And. SuperGetMv("MV_GFEI10",.F.,"2") == "1" .And. (lIsIncl .Or. lIsClass) .And. !(AllTrim(cTipo) $ 'I|P')
	aAdd(aDados, AllTrim(cTipo)    + Space( (TamSX3("F1_TIPO")[1])   - (Len( AllTrim(cTipo) )) ) )     	//F1_TIPO
	aAdd(aDados, AllTrim(cFormul)  + Space( (TamSX3("F1_FORMUL")[1]) - (Len( AllTrim(cFormul) )) ) )   	//F1_FORMUL
	aAdd(aDados, AllTrim(cNumNfGFE) + Space( (TamSX3("F1_DOC")[1])    - (Len( AllTrim(cNumNfGFE) )) ) )  	//F1_DOC
	aAdd(aDados, AllTrim(cSerie)   + Space( (TamSX3("F1_SERIE")[1])  - (Len( AllTrim(cSerie) )) ) )    	//F1_SERIE
	aAdd(aDados, dDEmissao )                                                                           		//F1_EMISSAO
	aAdd(aDados, AllTrim(cA100For) )  																		//F1_FORNECE
	aAdd(aDados, AllTrim(cLoja) )    																		//F1_LOJA
	aAdd(aDados, AllTrim(cEspecie) + Space( (TamSX3("F1_ESPECIE")[1]) - (Len( AllTrim(cEspecie) )) ) ) 	//F1_ESPECIE
	aAdd(aDados, "" )                                                                                  		//F1_NFORIG
	aAdd(aDados, aNFEDanfe[1] )                        														//F1_TRANSP
	aAdd(aDados, aNFEDanfe[5] )                        														//F1_VOLUME1
	aAdd(aDados, SubStr(aNFEDanfe[14],1,1) )         														//F1_TPFRETE
	aAdd(aDados, IIF(Empty(SF1->F1_VALICM),0,SF1->F1_VALICM) ) 											//F1_VALICM
	aAdd(aDados, xFilial("SF1") )
	aAdd(aDados, "" )                                  	 													//F1_SERORIG
	aAdd(aDados, aNFEDanfe[13] )                       	 													//F1_CHVNFE

	For nI := 1 to Len(aCols)
		If !aCols[nI][Len(aCols[nI])]

			If Posicione("SF4",1,xFilial("SF4") + GDFieldGet("D1_TES",nI),"F4_INCSOL") == "S"
				nVlrIt := GDFieldGet("D1_TOTAL",nI)+GDFieldGet("D1_ICMSRET",nI)+GDFieldGet("D1_VALIPI",nI)
			Else
				nVlrIt := GDFieldGet("D1_TOTAL",nI)+GDFieldGet("D1_VALIPI",nI)
			Endif

			aAdd(aDadosIten, { 	GDFieldGet("D1_ITEM",nI) ,;
						    GDFieldGet("D1_COD",nI)  ,;
						    GDFieldGet("D1_QUANT",nI),;
						    nVlrIt,;
						    GDFieldGet("D1_TES",nI)  ,;
						    GDFieldGet("D1_PESO",nI)  ,;
						    GDFieldGet("D1_CF",nI) })
		EndIf
	Next nI
	
	If FindFunction( "GFEM011NFE")
		lRet := GFEM011NFE("UNICO",aDados,aDadosIten,,,,lCommit)
	Else
		Help(" ",1,"COMGFE",,STR0542,1,0) //Necessario aplicar expediÁ„o continua do GFE para que n„o haja nenhuma incosistencia na integraÁ„o junto ao documento de entrada.
		lRet := .F.
	EndIf	

EndIf

Return lRet

//-----------------------------------------------------
/*/	Exclui o registro integrado.
@author Felipe Machado de Oliveira
@version P11
@since 22/05/2013
/*/
//------------------------------------------------------
Static Function ExclDocGFE()
Local aAreaGW1 := {}
Local lRet := .T.
Local oModelGFE := FWLoadModel("GFEA044")
Local cF1_CDTPDC := ""
Local cEmisDc
Local cSerie := SF1->F1_SERIE
Local cDoc := SF1->F1_DOC
Local lNumProp := SuperGetMv("MV_EMITMP",.F.,"0") == "1" .And. SuperGetMv("MV_INTGFE2",.F.,"2") == "1"
Local cCod := ""
Local cLoja := ""
Local nForCli := 0

cF1_CDTPDC := Posicione("SX5",1,xFilial("SX5")+"MQ"+SF1->F1_TIPO+"E","X5_DESCRI")

If Empty(cF1_CDTPDC)
	cF1_CDTPDC := Posicione("SX5",1,xFilial("SX5")+"MQ"+SF1->F1_TIPO,"X5_DESCRI")
EndIf

If cPaisLoc == "BRA"
aAreaGW1 := GW1->( GetArea() )
EndIf

If SF1->F1_TIPO $ "DB"
	SA1->( dbSetOrder(1) )
	SA1->( MsSeek(xFilial("SA1")+SF1->F1_FORNECE+SF1->F1_LOJA ) )
	If !SA1->( EOF() ) .And. SA1->A1_FILIAL == xFilial("SA1");
						 .And. AllTrim(SA1->A1_COD) == AllTrim(SF1->F1_FORNECE);
						 .And. AllTrim(SA1->A1_LOJA) == AllTrim(SF1->F1_LOJA)

		If lNumProp
			cCod := SA1->A1_COD
			cLoja := SA1->A1_LOJA
			nForCli := 1
		Else
			If SA1->A1_TIPO == "X"
				cEmisDc := AllTrim(SA1->A1_COD)+AllTrim(SA1->A1_LOJA)
			Else
				cEmisDc := SA1->A1_CGC
			EndIf
		EndIf

	EndIf
Else
	SA2->( dbSetOrder(1) )
	SA2->( MsSeek( xFilial("SA2")+SF1->F1_FORNECE+SF1->F1_LOJA) )
	If !SA2->( EOF() ) .And. SA2->A2_FILIAL == xFilial("SA2");
						 .And. AllTrim(SA2->A2_COD) == AllTrim(SF1->F1_FORNECE);
						 .And. AllTrim(SA2->A2_LOJA) == AllTrim(SF1->F1_LOJA)

		If lNumProp
			cCod := SA2->A2_COD
			cLoja := SA2->A2_LOJA
			nForCli := 2
		Else
			If SA2->A2_TIPO == "X"
				cEmisDc := AllTrim(SA2->A2_COD)+AllTrim(SA2->A2_LOJA)
			Else
				cEmisDc := SA2->A2_CGC
			EndIf
		EndIf
	EndIf
EndIf

cF1_CDTPDC := AllTrim(cF1_CDTPDC) + Space( (TamSX3("GW1_CDTPDC")[1]) - (Len( AllTrim(cF1_CDTPDC) )) )
cSerie := AllTrim(cSerie) + Space( (TamSX3("GW1_SERDC" )[1]) - (Len( AllTrim(cSerie) )) )
cDoc := AllTrim(cDoc) + Space( (TamSX3("GW1_NRDC" )[1]) - (Len( AllTrim(cDoc) )) )

If lNumProp
	If FindFunction( "GFEM011COD")
		cEmisDc := GFEM011COD(cCod,cLoja,nForCli,,)
	EndIf	
EndIf
If cPaisLoc == "BRA"
	GW1->( dbSetOrder(1) )
	GW1->( MsSeek(xFilial("GW1")+cF1_CDTPDC+cEmisDc+cSerie+cDoc) )
	If !GW1->( Eof() ) .And. GW1->GW1_FILIAL == xFilial("GW1");
						.And. AllTrim(GW1->GW1_CDTPDC) == AllTrim(cF1_CDTPDC) ;
						.And. AllTrim(GW1->GW1_EMISDC) == AllTrim(cEmisDc) ;
						.And. AllTrim(GW1->GW1_SERDC) == AllTrim(cSerie) ;
						.And. AllTrim(GW1->GW1_NRDC) == AllTrim(cDoc)

		oModelGFE:SetOperation( MODEL_OPERATION_DELETE )
		oModelGFE:Activate()

		If oModelGFE:VldData()
			oModelGFE:CommitData()
		Else
			Help( ,, STR0119,,STR0404+CRLF+CRLF+oModelGFE:GetErrorMessage()[6], 1, 0,,,,,.T. ) //"AtenÁ„o"##"InconsistÍncia com o Frete Embarcador (SIGAGFE): "##
			lRet := .F.
		EndIf
	EndIf
EndIf
RestArea( aAreaGW1 )

Return lRet
//-------------------------------------------------------------------
/*/{Protheus.doc} A103MultATF
GeraÁ„o de ativos imobilizado, quando a opÁ„o de desmembrar ativo for igual a Sim.
O sistema ent„o ir· criar uma ficha de ativo por quantidade de produto da nota
@author Alvaro Camillo Neto
@since  09/01/2014
@version 12
/*/
//-------------------------------------------------------------------
Function A103MultATF(nQtdD1,lATFDCBA,cSF4Ciap,cMvfsnciap,aDIfDec,cAno)
Local nV			:= 0
Local cAux 		:= Replicate("0", TAMSX3("N1_ITEM")[1])
Local cItemAtf	:= ""
Local nTamSN1		:= TamSX3("N1_ITEM")[1]
Local cSoma1		:= ""
Local cCIAP		:= ""
Local cBaseAtf	:= ""
Local aVlrAcAtf	:=	{0,0,0,0,0}
Local cDaCiap   	:= GetNewPar("MV_DACIAP",'S') //Utilizado para calc. ICMS no CIAP. Se S= Considera valor de dif. aliquota se N= Nao considera dif. aliquota
Local nVlrICMS	:= 0
Local lRet      := .T.

For nV := 1 TO nQtdD1
	If !lATFDCBA .OR. ( lATFDCBA .AND. nV == 1 )
		cAux		:= Soma1( cAux,,, .F. )
		cItemAtf	:= PadL( cAux, nTamSN1 , "0" )
	EndIf
	If cSF4Ciap == "S" .And. (SF4->F4_ICM == "S" .OR. SF4->F4_COMPL = "S") .AND. !Empty(SD1->D1_CODCIAP) //PRIME
		if cMvfsnciap == "2"
			cCIAP	:=  IIF (nV == 1,SD1->D1_CODCIAP, Soma1(substr(cSoma1,1,4))+ cAno )
			cSoma1 := cCIAP
		else
			cCIAP	:=  IIF (nV == 1,SD1->D1_CODCIAP, Soma1(cSoma1))
			cSoma1 := cCIAP
		Endif

	Else
		cCIAP	:= ""
	EndIf

	//Se for o ˙ltimo ent„o indica TRUE para gravar a diferenÁa dos valores das casas decimais.
	IF nV == nQtdD1
		aDIfDec[2] := .T.
	EndIF
	If SF4->F4_CIAP=="S" .And. SD1->D1_VALICM  > 0 //N„o preencher o campo  N1_ICMSAPR quando n„o houver c·lculo CIAP 
		nVlrICMS := SD1->D1_VALICM
	EndIf 		
	If AllTrim(cDACiap) == "S"
		nVlrICMS += SD1->D1_ICMSCOM
	EndIf

	If !a103GrvAtf(1,@cBaseAtf,cItemAtf,cCIAP,nVlrICMS,,@aVlrAcAtf,,,@aDIfDec)
		lRet := .F.
		Exit
	EndIf

Next nV

Return lRet
//-----------------------------------------------------
/*/	Reserva registros da tabela SE2
@author jose.delmondes
@version P12
@since 08/10/2014
/*/
//------------------------------------------------------
Function TravaSE2(aRecno)
Local nX		:= 0
Local nY		:= 0
Local aArea 	:= GetArea()
Local aAreaSE2:= SE2->(GetArea())
Local lRet		:= .T.

dbSelectArea("SE2")

//Reserva registros da tabela SE2
For nX := 1 To Len(aRecno)
	msGoto(aRecno[nX])
	If !SimpleLock()
		lRet := .F.
		Exit
	EndIf
Next

//Caso n„o seja possÌvel reservar todos os registros, libera os que foram reservados.
If !lRet
 For nY :=1 To nX-1
 	msGoto(aRecno[nY])
 	msUnlock()
 Next nY
EndIf

RestArea(aArea)
RestArea(aAreaSE2)
Return lRet

/*
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±…ÕÕÕÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÀÕÕÕÕÕÕ—ÕÕÕÕÕÕÕÕÕÕÕÕÕª±±
±±∫Programa  ≥ A103DevPdr ∫Autor  ≥Isaias Florencio    ∫ Data ≥  09/10/2014 ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕ ÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Descricao ≥ Verifica se existe TES de devolucao e, se existir, verifica  ∫±±
±±∫          ≥ se nao controla poder de terceiros                           ∫±±
±±ÃÕÕÕÕÕÕÕÕÕÕÿÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕπ±±
±±∫Uso       ≥ MATA103                                                      ∫±±
±±»ÕÕÕÕÕÕÕÕÕÕœÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕÕº±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
*/
Static Function A103DevPdr(cTES)
Local aAreaAnt := GetArea()
Local aAreaSF4 := SF4->(GetArea())
Local lRet := .F.

SF4->(DbSetOrder(1)) // FILIAL + CODIGO
SF4->(MsSeek(xFilial("SF4")+cTES))

If !Empty(SF4->F4_TESDV)
	SF4->(MsSeek(xFilial("SF4")+SF4->F4_TESDV))
	lRet := SF4->F4_PODER3 == "N"
Else
	lRet := .T.
EndIf

RestArea(aAreaSF4)
RestArea(aAreaAnt)
Return lRet
//-------------------------------------------------------------------
/*/{Protheus.doc}A103ExsSF8
FunÁ„o que verifica e retorna se uma determinada Nota Fiscal existe na SF8

@author Matheus Lando Raimundo
@since 16/01/2015
@version P11.80
/*/
//-------------------------------------------------------------------
Function A103ExsSF8(cNF,cSerieNF,cFornec,cLojaFor)
Local lRet := .F.

SF8->(dbSetOrder(3))

lRet := SF8->(dbSeek(xFilial("SF8")+cNF+cSerieNF+cFornec+cLojaFor))

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc}A103DocEmp
FunÁ„o que retorna os itens vinculado a nota de empenho.

@author taniel.silva
@since 22/01/2015
@version P12
/*/
//-------------------------------------------------------------------
Function A103DocEmp(aCols,aDocEmp,lMata103)
Local nPosCodNE
Local nPosItemNE
Local nPosTotal
Local nPosItem
Local nPos			:= 0
Local nX			:= 0
Local lNotaEmp	:= SuperGetMV("MV_NOTAEMP",.F.,.F.)

Default lMata103	:= .F.

If lNotaEmp .And. !Empty(aCols)
	nPosCodNE	:= aScan(aHeader ,{|x| AllTrim(x[2])=="D1_CODNE"})
	nPosItemNE	:= aScan(aHeader ,{|x| AllTrim(x[2])=="D1_ITEMNE"})
	nPosCod		:= aScan(aHeader,{|x| AllTrim(x[2])=="D1_COD"})
	nPosTotal	:= aScan(aHeader,{|x| AllTrim(x[2])=="D1_TOTAL"})
	nPosItem	:= aScan(aHeader,{|x| AllTrim(x[2])=="D1_ITEM"})
	For nX := 1 To Len(aCols)
		If  nPosCodNE > 0 .And. nPosItemNE > 0 .and. !Empty(aCols[nX][nPosCodNE]) .And. !GdDeleted(nX) 
			If lMata103
				If !Empty(aDocEmp)
					nPos := aScan(aDocEmp,{|x| AllTrim(x[1]) + AllTrim(x[2]) + AllTrim(x[3]) == AllTrim(aCols[nX][nPosCod]) + AllTrim(aCols[nX][nPosCodNE]) + AllTrim(aCols[nX][nPosItemNE])})
					If nPos > 0
						aDocEmp[nPos][4] += aCols[nX][nPosTotal]
					Else
						Aadd(aDocEmp,{aCols[nX][nPosCod],aCols[nX][nPosCodNE],aCols[nX][nPosItemNE],aCols[nX][nPosTotal]})
					EndIf
				Else
					Aadd(aDocEmp,{aCols[nX][nPosCod],aCols[nX][nPosCodNE],aCols[nX][nPosItemNE],aCols[nX][nPosTotal]})
				EndIf
			Else
				If !Empty(aDocEmp)
					nPos := aScan(aDocEmp,{|x| AllTrim(x[1]) + AllTrim(x[2]) + AllTrim(x[3]) == AllTrim(aCols[nX][nPosCod]) + AllTrim(aCols[nX][nPosCodNE]) + AllTrim(aCols[nX][nPosItemNE])})
					If nPos > 0
						aDocEmp[nPos][4] += MaFisRet(nX,"IT_TOTAL")- MaFisRet(aCols[nX][nPosItem],"NF_DESCONTO")
					Else
						Aadd(aDocEmp,{aCols[nX][nPosCod],aCols[nX][nPosCodNE],aCols[nX][nPosItemNE],MaFisRet(nX,"IT_TOTAL")- MaFisRet(aCols[nX][nPosItem],"NF_DESCONTO")})
					EndIf
				Else
					Aadd(aDocEmp,{aCols[nX][nPosCod],aCols[nX][nPosCodNE],aCols[nX][nPosItemNE],MaFisRet(nX,"IT_TOTAL")- MaFisRet(aCols[nX][nPosItem],"NF_DESCONTO")})
				EndIf
			EndIf
		EndIf
	Next nX
EndIf

Return nil

//-------------------------------------------------------------------
/*/{Protheus.doc}A103DocEmp
FunÁ„o que retorna as informaÁıes para gerar o histÛrico da nota de empenho.

@author taniel.silva
@since 22/01/2015
@version P12
/*/
//-------------------------------------------------------------------
Function A103HisEmp(aNotaEmp,lIncNotaEmp)
Local nPosCodNE  	:= GetPosSD1( "D1_CODNE" )
Local nPosItemNE	:= GetPosSD1( "D1_ITEMNE" )
Local nPosTotal	    := GetPosSD1( "D1_TOTAL" )
Local nX			:= 0
Local nPos			:= 0

If !Empty(aCols) .And. nPosCodNE > 0 .And. nPosItemNE > 0
	For nX := 1 To Len(aCols)
	 	nPos := aScan(aNotaEmp,{|x| AllTrim(x[1])== AllTrim(aCols[nX][nPosCodNE])})
	 	If nPos > 0
			aAdd(aNotaEmp[nPos][6],{aCols[nX][nPosItemNE],aCols[nX][nPosTotal]})
		Else
			If !Empty(aCols[nX][nPosCodNE]) .And. !Empty(aCols[nX][nPosItemNE])
		  	aAdd(aNotaEmp,{})
		  	aAdd(aTail(aNotaEmp),aCols[nX][nPosCodNE])
		  	aAdd(aTail(aNotaEmp),"2")
		  	aAdd(aTail(aNotaEmp),cNFiscal)
		  	aAdd(aTail(aNotaEmp),IIf(lIncNotaEmp,'1','2'))
		  	aAdd(aTail(aNotaEmp),IIf(lIncNotaEmp,'1','2'))
		  	aAdd(aTail(aNotaEmp),{{aCols[nX][nPosItemNE],aCols[nX][nPosTotal]}})
		  	aAdd(aTail(aNotaEmp),IIf(lIncNotaEmp,STR0495,STR0496))
			EndIf
		EndIf
	Next nX
EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc}A103DelSF8
FunÁ„o que deleta os registro da SF8

@author Matheus Lando Raimundo
@since 16/01/2015
@version P11.80
/*/
//-------------------------------------------------------------------
Function A103DelSF8(cNF,cSerieNF,cFornec,cLojaFor)

If A103ExsSF8(cNF,cSerieNF,cFornec,cLojaFor)
	While !SF8->(Eof()) .And. SF8->F8_NFDIFRE == cNF .And. SF8->F8_SEDIFRE == cSerieNF .And.;
		SF8->F8_TRANSP == cFornec .And. SF8->F8_LOJTRAN == cLojaFor
		RecLock("SF8",.F.)
		dbDelete()
	   	MsUnlock()
	   	SF8->(dbSkip())
	EndDo
EndIf

Return

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ MATA103  ≥ Autor ≥ Cleyton F.Alves       ≥ Data ≥ 07.05.2015 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Salva as variaveis estaticas                                 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ Generico                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/
Function MT103SetRet(cMotRet,cHistRet)
cMT103Mot  := cMotRet
cMT103Hist := cHistREt
Return(nil)

/*/
‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹‹
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±⁄ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¬ƒƒƒƒƒƒ¬ƒƒƒƒƒƒƒƒƒƒƒƒø±±
±±≥FunáÖo    ≥ MATA103  ≥ Autor ≥ Cleyton F.Alves       ≥ Data ≥ 07.05.2015 ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥DescriáÖo ≥ Recupera as variaveis estaticas                              ≥±±
±±√ƒƒƒƒƒƒƒƒƒƒ≈ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒ¥±±
±±≥ Uso      ≥ Generico                                                     ≥±±
±±¿ƒƒƒƒƒƒƒƒƒƒ¡ƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒƒŸ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂﬂ
/*/

Function MT103GEtRet()
Return({cMT103Mot,cMT103Hist})

//-------------------------------------------------------------------
/*/{Protheus.doc}A103HORA
Realiza c·lculo do fuso hor·rio

@author Jose.delmondes
@since 27/04/2015
@version P11.80
/*/
//-------------------------------------------------------------------
Function A103HORA()
Local aRet 	:= Array(2)
Local dData := Date()
Local aTimeUF	:= {}
Local aArea	:= GetArea()
Local aAreaSM0:= SM0->(GetArea())
Local dHVeraoI:= SuperGetMV("MV_HVERAOI",.F.,CTOD('  /  /    '))
Local dHVeraoF:= SuperGetMV("MV_HVERAOF",.F.,CTOD('  /  /    '))
Local lHverao	:= .F.
Local lAuto103 :=  (Type("l103Auto") <> "U" .And. (l103Auto))

//Verifica se È hor·rio de ver„o
If !Empty(dHVeraoI) .And. !Empty(dHVeraoF) .And. dDataBase >= dHVeraoI .And. dDataBase <= dHVeraoF
	lHverao := .T. 
EndIf

dbSelectArea("SM0")
dbSetOrder(1)
If dbSeek(cEmpAnt+cFilAnt)
	aTimeUf := FwTimeUF(SM0->M0_ESTENT,,lHVerao,DTOS(dDataBase)) //Retorna o fuso da filial corrente
EndIf

//Ajusta data base de acordo com o retorno da funÁ„o FWTimeUF
If ValType(aTimeUF) == 'A' .And. Len(aTimeUF) >= 2
	aRet[1] := CTOD(substr(aTimeUF[1],7,2) +'/'+ substr(aTimeUF[1],5,2) +'/'+ substr(aTimeUF[1],1,4))
	aRet[2] := aTimeUF[2]

	If lAuto103
		If aRet[1] < dData
	   		aRet[1] := dDataBase 
		EndIf	
	EndIf 
EndIf

RestArea(aAreaSM0)
RestArea(aArea)

Return aRet

//-------------------------------------------------------------------
// Esta funÁ„o teve que ser recolocada por questıes de compatibilidade,
// deve ser retirada futuramente
//-------------------------------------------------------------------
Function A103EstDCF(lEstorna)

	If IntWMS()
		If !FindFunction("WmsAvalSF1") .Or. !FindFunction("WmsAvalSD1")
			Final(STR0426) //"Atualize o SIGAWMS com o chamado TSDZH3"
		EndIf
	EndIf

Return .T.

//-------------------------------------------------------------------
// Esta funÁ„o teve que ser recolocada por questıes de compatibilidade,
// deve ser retirada futuramente
//-------------------------------------------------------------------
Function A103WMSOk(cAcao,cAliasSD1)

	If IntWMS()
		If !FindFunction("WmsAvalSF1") .Or. !FindFunction("WmsAvalSD1")
			Final(STR0426) //"Atualize o SIGAWMS com o chamado TSDZH3"
		EndIf
	EndIf

Return .T.


//-------------------------------------------------------------------
/*/{Protheus.doc}A103ExsCD5
FunÁ„o que verifica e retorna se uma determinada Nota Fiscal existe na CD5

@author Igor Braz
@since 22/06/2015
@version P11.80
/*/
//-------------------------------------------------------------------
Function A103ExsCD5(cNF,cSerieNF,cFornec,cLojaFor)
Local lRet := .F.
If cPaisLoc == "BRA"
CD5->(dbSetOrder(3))

lRet := CD5->(dbSeek(xFilial("CD5")+cNF+cSerieNF+cFornec+cLojaFor))
EndIf
Return lRet


//-------------------------------------------------------------------
/*/{Protheus.doc}A103DelCD5
FunÁ„o que deleta os registro da CD5

@author Igor Braz
@since 22/06/2015
@version P11.80
/*/
//-------------------------------------------------------------------
Function A103DelCD5(cNF,cSerieNF,cFornec,cLojaFor)
If cPaisLoc == "BRA"
	If A103ExsCD5(cNF,cSerieNF,cFornec,cLojaFor)
		While !CD5->(Eof()) .And. CD5->CD5_DOC == cNF .And. CD5->CD5_SERIE == cSerieNF .And.;
			CD5->CD5_FORNEC == cFornec .And. CD5->CD5_LOJA == cLojaFor
			RecLock("CD5",.F.)
			dbDelete()
			MsUnlock()
			CD5->(dbSkip())
		EndDo
	EndIf
EndIf
Return

Static Function XGetCP()

Local aArea		:= GetArea()
Local aRecEst		:= {} //Array que contem o Recno dos Titulos do Tipo "PA"
Local cQuery		:= ""
Local cTab		:= GetNextAlias()
Local cTipodoc	:= ""
Local cTipodc		:= ""

	If SE2->E2_TIPO $ MV_CPNEG .or. Alltrim(SE2->E2_TIPO) $ MVPAGANT
		cTipodoc := "BA"
		cTipodc	:= "CP"
	Else
		cTipodoc := "CP"
		cTipodc	:= "BA"
	Endif
	If Select(cTab) > 0
		(cTab)->(dbCloseArea())
	EndIf
	cQuery := "SELECT SE5.E5_FILIAL, SE5.E5_TIPODOC, SE5.E5_PREFIXO, SE5.E5_NUMERO, SE5.E5_PARCELA, "
	cQuery += "SE5.E5_TIPO, SE5.E5_DATA, SE5.E5_CLIFOR, SE5.E5_LOJA, SE5.E5_SEQ, "
	cQuery += "SE5.E5_DOCUMEN, SE5.E5_FILORIG, SE5.E5_VLMOED2, SE5.E5_FORNADT, SE5.E5_LOJAADT, SE5.R_E_C_N_O_ E5_RECNO, "
	cQuery += "SE2.E2_VALOR, SE2.E2_FORNECE, SE2.E2_LOJA "
	cQuery += "FROM "+RetSqlName("SE5") + " SE5, "
	cQuery += RetSqlName("SE2") + " SE2 "
	cQuery += "WHERE "
	cQuery += "SE5.E5_FILIAL = '"+xFilial("SE5")+"' AND "
	cQuery += "SE2.E2_FILIAL = '"+xFilial("SE2")+"' AND "
	cQuery += "SE5.E5_PREFIXO = SE2.E2_PREFIXO AND "
	cQuery += "SE5.E5_NUMERO = SE2.E2_NUM AND "
	cQuery += "SE5.E5_PARCELA = SE2.E2_PARCELA AND "
	cQuery += "SE5.E5_TIPO = SE2.E2_TIPO AND "
	cQuery += "SE5.E5_TIPODOC = '"+cTipoDoc+"' AND "
	cQuery += "SE5.E5_MOTBX = 'CMP' AND "
	cQuery += "SE5.E5_RECPAG = 'P' AND "
	cQuery += "SE5.E5_PREFIXO ='"+SE2->E2_PREFIXO+"' AND "
	cQuery += "SE5.E5_NUMERO ='"+SE2->E2_NUM+"' AND "
	cQuery += "SE5.E5_PARCELA ='"+SE2->E2_PARCELA+"' AND "
	cQuery += "SE5.E5_TIPO = '"+SE2->E2_TIPO+"' AND "
	cQuery += "SE5.E5_CLIFOR = '"+SE2->E2_FORNECE+"' AND "
	cQuery += "SE5.E5_LOJA = '"+SE2->E2_LOJA+"' AND "
	cQuery += "SE5.D_E_L_E_T_ = ' ' AND "
	cQuery += "SE2.D_E_L_E_T_ = ' ' "
	cQuery += "ORDER BY "
	cQuery += "SE5.E5_FILIAL, SE5.E5_TIPODOC, SE5.E5_PREFIXO, SE5.E5_NUMERO, SE5.E5_PARCELA, "
	cQuery += "SE5.E5_TIPO, SE5.E5_DATA, SE5.E5_SEQ"
	cQuery := ChangeQuery(cQuery)
	dbUseArea(.T., "TOPCONN", TCGenQry(,,cQuery), cTab, .F., .T.)

	(cTab)->(dbGoTop())
	While (cTab)->(!EOF())
		//Verifica se tem baixa cancelada
		If TemBxCanc( (cTab)->(E5_PREFIXO+E5_NUMERO+E5_PARCELA+E5_TIPO+E5_CLIFOR+E5_LOJA+E5_SEQ) , .T.)
			(cTab)->( dbskip())
			loop
		EndIf
		aAdd(aRecEst,(cTab)->E5_DOCUMEN)
		(cTab)->(dbSkip())
	EndDo
	(cTab)->(dbCloseArea())
	RestArea(aArea)
Return aRecEst

//-------------------------------------------------------------------
/*/{Protheus.doc}A103Manif
Funcao que transmite manifestacao 'Ciencia da Operacao' para
NF-e(mod 55) e formulario proprio = NAO

@author Natalia Sartori
@since 30/07/2015
@version P12
@return Nil
/*/
//-------------------------------------------------------------------
Function A103Manif(cAlias,nReg,nOpcx)

Local cCodEve := ""

If SF1->F1_FORMUL <> "S" .and. !Empty(SF1->F1_CHVNFE) .and. Alltrim(SF1->F1_ESPECIE) == "SPED"
If cPaisLoc == "BRA"
	If FindFunction("MDeMata103")

		If nOpcx = 1
         cCodEve := "210200" //"210200 - ConfirmaÁ„o da OperaÁ„o"
		Elseif nOpcx = 2
         cCodEve := "210210" //"210210 - CiÍncia da OperaÁ„o"
       EndIf

		MDeMata103(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_EMISSAO,SF1->F1_VALBRUT,SF1->F1_TIPO,SF1->F1_CHVNFE,SF1->F1_DAUTNFE,cCodEve)
	Else
		Aviso(STR0433,STR0434,{"OK"},3) //"ManifestaÁ„o do Destinat·rio"##"FunÁ„o respons·vel pela manifestaÁ„o n„o encontrada. Atualize a rotina SPEDMANIFE!!"
	EndIf
EndIf
Else
	Aviso(STR0433,STR0435,{"OK"},3)// "ManifestaÁ„o do Destinat·rio"##"Para manifestar È necess·rio que a espÈcie do documento seja 'SPED', formul·rio prÛprio = 'N„o' e a Chave da NF-e preenchida. "
EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc}A103GrvCla
FunÁ„o de salva a classificaÁ„o atÈ o momento para posterior atualizaÁ„o

@author Leonardo Quintania
@since 20/06/2016
@version P11.80
@return Nil
/*/
//-------------------------------------------------------------------
Function A103GrvCla(l103Class,aColsSE2,cNatureza)
Local nX		:= 0
Local nY		:= 0
Local nRec		:= 0
Local lMT103MSG := .T.
Local lRecZero 	:= .F.
Local aArea		:= GetArea()
Local aCamposAd := {}
Local lAtuPC	:= .F.
Local cPCAnt	:= ""
Local cItPCAnt	:= ""
Local nQtdPCAnt	:= 0
Local cPCNew	:= ""
Local cItPCNew	:= ""
Local nQtdPCNew	:= 0
Local cFilEntC7 := xFilEnt(xFilial("SC7"), "SC7")
Local lMT103CLAS:= ExistBlock("MT103CLAS")
Local lF1Gf		:= SF1->( FieldPos( "F1_GF" ) ) > 0
Local lGuardFis := (Type("l103GGFAut") == "L" .And. l103GGFAut)
Local lGFGrvD1	:= .F.
Local aAreaSF1	:= {}
Local lCsdXML 	:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA") .and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")

Default l103Class := .F.
Default aColsSE2  := {}
Default cNatureza := ""

//Ponto de entrada para validar a mensagem se deseja ou n„o salvar as informaÁıes j· inseridas.
If ExistBlock("MT103MSG")
	lMT103MSG:=ExecBlock("MT103MSG",.F.,.F.)
	If ValType(lMT103MSG)<>'L'
		lMT103MSG:=.T.
	EndIf
EndIf

If l103Class .And. lMT103MSG
	If  lGuardFis .Or. MsgYesNo(OemToAnsi(STR0454), OemToAnsi(STR0491))//"Deseja salvar as informaÁıes inseridas atÈ o momento que n„o est„o relacionadas a c·lculo de impostos?", "Salvar Dados"

		aCamposAd := {	{"D1_BASIMP6","IT_BASEPS2"},{"D1_ALQIMP6","IT_ALIQPS2"},{"D1_VALIMP6","IT_VALPS2"},;
						{"D1_BASIMP5","IT_BASECF2"},{"D1_ALQIMP5","IT_ALIQCF2"},{"D1_VALIMP5","IT_VALCF2"},;
						{"D1_BASEPS3","IT_BASEPS3"},{"D1_ALIQPS3","IT_ALIQPS3"},{"D1_VALPS3","IT_VALPS3"}, ;
						{"D1_VALFRE","IT_FRETE"},{"D1_DESPESA","IT_DESPESA"},{"D1_SEGURO","IT_SEGURO"}, ;
						{"D1_BASECF3","IT_BASECF3"},{"D1_ALIQCF3","IT_ALIQCF3"},{"D1_VALCF3","IT_VALCF3"},{"D1_BASEDES","IT_BASEDES"},{"D1_ICMSDIF","IT_ICMSDIF"}} 

		For nX := 1 to Len(aCols) 

			lRecZero	:= .F.
			nRec		:= aCols[nX,Len(aCols[nX])-1]

			If nRec == 0 //Inclus„o via Pedido (Documento)
				nRec := A103RECD1(aCols[nX,GetPosSD1("D1_ITEM")])
				lRecZero := .T. 
			Endif

			lAtuPC := .F.
			
			//Posicionamento no R_E_C_N_O_
			SD1->(MsGoto(nRec)) 

			cPCAnt    := SD1->D1_PEDIDO
			cItPCAnt  := SD1->D1_ITEMPC
			nQtdPCAnt := GetAdvFVal("SC7","C7_QUANT",cFilEntC7 + cPCAnt + cItPCAnt,14)

			For nY := 1 To Len(aHeader)
				If aHeader[nY][10] # "V" .And. !IsHeadRec( aHeader[nY,01] ) .And. !IsHeadAlias( aHeader[nY,01] ) .And. AllTrim(aHeader[nY,02]) # "D1_TESACLA"
					If AllTrim(aHeader[nY,02]) == "D1_PEDIDO"
						cPCNew := aCols[nX][nY] 
					Elseif AllTrim(aHeader[nY,02]) == "D1_ITEMPC"
						cPCItNew := aCols[nX][nY] 
					Elseif AllTrim(aHeader[nY,02]) == "D1_QUANT"
						nQtdPCNew := aCols[nX][nY]
					Endif
				EndIf
			Next nY

			//N„o tinha vinculo e foi vinculado na classificaÁ„o
			If Empty(cPCAnt) .And. !Empty(cPCNew) 
				lAtuPC := .T.
			
			//Ja tinha vinculo, mas mudou o PC
			//Com isso e ajustado o PC antigo para depois atualizar o novo
			Elseif !Empty(cPCAnt) .And. cPCAnt <> cPCNew
				MaAvalSD1(2,"SD1")
				lAtuPC := .T.

			//Ja tinha vinculo, mas mudou o item do PC
			//Com isso e ajustado o PC antigo para depois atualizar o novo
			Elseif !Empty(cPCAnt) .And. cPCAnt == cPCNew .And. cItPCAnt <> cItPCNew
				MaAvalSD1(2,"SD1")
				lAtuPC := .T.

			//Ja tinha vinculo, mas alterou a quantidade
			//PC È atualizado
			Elseif !Empty(cPCAnt) .And. cPCAnt == cPCNew .And. cItPCAnt == cItPCNew .And. nQtdPCAnt <> nQtdPCNew
				lAtuPC := .T.
			Endif

			RecLock("SD1",.F.) 

			For nY := 1 To Len(aHeader)
				If aHeader[nY][10] # "V" .And. !IsHeadRec( aHeader[nY,01] ) .And. !IsHeadAlias( aHeader[nY,01] ) .And. AllTrim(aHeader[nY,02]) # "D1_TESACLA"
					If AllTrim(aHeader[nY,02]) == "D1_TES"
						SD1->(FieldPut(FieldPos("D1_TESACLA"),aCols[nX][nY]))
					Else
						If lRecZero
							If AllTrim(aHeader[nY,02]) == "D1_DOC"
								SD1->(FieldPut(FieldPos(aHeader[nY][2]),cNFiscal))
							ElseIf AllTrim(aHeader[nY,02]) == "D1_SERIE"
								SD1->(FieldPut(FieldPos(aHeader[nY][2]),cSerie))
							ElseIf AllTrim(aHeader[nY,02]) == "D1_FORNECE"
								SD1->(FieldPut(FieldPos(aHeader[nY][2]),cA100For))
							ElseIf AllTrim(aHeader[nY,02]) == "D1_LOJA"
								SD1->(FieldPut(FieldPos(aHeader[nY][2]),cLoja))
							Else
								SD1->(FieldPut(FieldPos(aHeader[nY][2]),aCols[nX][nY]))
							Endif
						Else
							SD1->(FieldPut(FieldPos(aHeader[nY][2]),aCols[nX][nY]))
						Endif
					EndIf
				EndIf
			Next nY		

			If lAtuPC 
				MaAvalSD1(1,"SD1") 
			Endif				
		
			// Salva valores de impostos para campos n„o usados (PIS / COFINS)
			For nY := 1 To Len(aCamposAd)
				SD1->(FieldPut(FieldPos(aCamposAd[nY][1]),MaFisRet(nX,aCamposAd[nY][2])))
			Next nY

			// Controle para processo de Guarda Fiscal (cliente Todimo)
			// Ao classificar novamente a nota, os valores fiscais digitados nao devem ser recalculados na funcao MontaAcols
			SD1->D1_ORIGEM := "GF"
			lGFGrvD1 := .T.

			//PE que permite manipular somente os dados inseridos no momento de classificar o documento.
			If lMT103CLAS
				ExecBlock("MT103CLAS",.F.,.F.,{aColsSE2,cNatureza})
			EndIf
			MsUnlock()
		Next nX
	EndIf
EndIf

If lGFGrvD1 .And. lF1Gf
	aAreaSF1 := SF1->(GetArea())
	SF1->(DbSetOrder(1))
	If SF1->(MsSeek(xFilial("SF1") + cNFiscal + cSerie + cA100For + cLoja))
		If RecLock("SF1",.F.)
			SF1->F1_GF := "GF"
		Endif			
		SF1->(MsUnlock())
	Endif
	RestArea(aAreaSF1)
Endif

If lCsdXML
	A103CSDXML(2, cNFiscal, cSerie, cA100For, cLoja) 
Endif

RestArea(aArea) 

Return .T.

/*/{Protheus.doc}A103RECD1
Recno do item da nf

@author Rodrigo M Pontes
@since 09/09/16
@version P11.80
@return Nil
/*/

Static Function A103RECD1(cItNF)

Local cQry		:= ""
Local nRecno	:= 0

If Select("RECD1") > 0
	RECD1->(DbCloseArea())
Endif

cQry := " SELECT R_E_C_N_O_ AS RECNO"
cQry += " FROM " + RetSqlName("SD1")
cQry += " WHERE D_E_L_E_T_ = ''"
cQry += " AND D1_DOC = '" + cNFiscal + "'"
cQry += " AND D1_SERIE = '" + cSerie + "'"
cQry += " AND D1_FORNECE = '" + cA100For + "'"
cQry += " AND D1_LOJA = '" + cLoja + "'"
cQry += " AND D1_ITEM = '" + cItNF + "'"

cQry := ChangeQuery(cQry)

dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQry),"RECD1",.T.,.T.)

If RECD1->(!EOF())
	nRecno := RECD1->RECNO
Endif

RECD1->(DbCloseArea())

Return nRecno

//-------------------------------------------------------------------
/*/{Protheus.doc} GetNxtPrfImp()
FunÁ„o responsavel por gerar o proximo prefixo para os titulos de COF, PIS ou ISS de importaÁ„o.
Como o tÌtulo È gerado atravÈs da chave E2_FILIAL+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO+E2_FORNECE+E2_LOJA, para n„o ocorrer validaÁ„o de chave ˙nica no financeiro dever·
ser incrementado o prefixo do titulo.

@author Bruno Akyo Kubagawa
@since 01/11/2017
@version 12.1.17
/*/
//-------------------------------------------------------------------
static function GetNxtPrfImp( cPrefixo , cNum, cParc, cTipo, cForn, cLoja )
	local cRet := ""
	local aArea := getArea()

	default cPrefixo := ""
	default cNum	 := ""
	default cParc	 := ""
	default cTipo	 := ""
	default cForn	 := ""
	default cLoja	 := ""

	if empty(cParc)
		cParc := space( len( SE2->E2_PARCELA) )
	endif

	dbSelectArea("SE2")
	SE2->(DbSetOrder(1)) // E2_FILIAL+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO+E2_FORNECE+E2_LOJA

	while .T.
		cRet := cPrefixo
		if !SE2->(DbSeek( xFilial("SE2") + cRet + cNum + cParc + cTipo + cForn + cLoja ))
			exit
		endif
		cPrefixo := soma1(cPrefixo)
	end

	restArea(aArea)

return cRet

//-------------------------------------------------------------------
/*/{Protheus.doc} VldLinSB6()
FunÁ„o respons·vel por validar o poder de/em terceiro. A funcionalidade foi extraÌda da funÁ„o LinOk,
pois a mesma dever· ser chamada tambÈm dentro da TudoOk, j· que È possÌvel apenas classificar a nota
de entrada sem alter·-la. Com a chamada dessa funÁ„o ser„o validados todos os itens da grid.
@author Victor F. dos Santos
@since 05/12/2017
@version 11.80
/*/
//-------------------------------------------------------------------

Static Function VldLinSB6(nPosCols, nPosNfOri,nPosSerOri,nPosIdentB6,nPosQuant,nPosTotal,nPValDesc,nPosCod,nPosTES,nPosVUnit,aCols,cFilNfOri,cA100For,cLoja,cTipo,l103Auto)

Local lRet 		 := .T.
Local nQtdPoder3 := 0
Local nSldPoder3 := 0
Local aSldSB6	 := {}
Local lBloqSb6	 := SuperGetMv("MV_BLOQSB6",.F.,.F.)
Local lLibeSb6	 := SuperGetMv("MV_LIBESB6",.F.,.T.)
Local cHelpPD3   := ""
Local nx		 := 1
Local cAlerta	 := ""
Local cMsg		 := ""
Local nQtdpd3 	 := ""
Local nSldPd3 	 := ""

For nX := 1 to Len(aCols)
	If 	aCols[nX][nPosNfOri]  == aCols[nPosCols, nPosNfOri]  .And. ;
			aCols[nX][nPosSerOri] == aCols[nPosCols, nPosSerOri] .And. ;
			aCols[nX][nPosIdentB6] == aCols[nPosCols, nPosIdentB6]  .And. ;
			!aCols[nX][Len(aCols[nX])]
		nQtdPoder3 += aCols[nX][nPosQuant]
		nSldPoder3 += aCols[nX][nPosTotal]-aCols[nX][nPValDesc]
	EndIf
Next nX

//Verifica se o conteudo do aCols[nX][nPosIdentB6] confere com o do documento original (SD2) em casos onde
//o usuario altera manualmente o docto orignal ao retornar devolucoes de beneficiamento pela opcao Retornar.
SD2->(dbSetOrder(4))
SD2->(MsSeek(cFilNfOri + aCols[nPosCols, nPosIdentB6]))

If aCols[nPosCols][nPosNfOri] + aCols[nPosCols, nPosSerOri] <> SD2->D2_DOC + SD2->D2_SERIE
	cAlerta := STR0266 + chr(13) + chr(10)		//O(s) Campo(s) Documento Original e/ou SÈrie foi(ram) alterados manualmente para:
	If aCols[nPosCols][nPosNfOri] <> SD2->D2_DOC
		cAlerta += STR0267 + aCols[nPosCols][nPosNfOri] + chr(13) + chr(10)	//- Documento:
	EndIf
	If aCols[nPosCols, nPosSerOri] <> SD2->D2_SERIE
		cAlerta += STR0502 + aCols[nPosCols, nPosSerOri] + chr(13) + chr(10) //- SÈrie:
	EndIf
	cAlerta += STR0268 + chr(13)	      //"O sistema necessita que esta operaÁ„o seja realizada atraves"
	cAlerta += STR0269 + chr(13)	      //"do bot„o SELECIONAR DOCUMENTO ORIGINAL - F7 para atualizar a"
	cAlerta += STR0270 + chr(13)	      //"baixa da tabela SB6."
	Aviso("IDENTSB6",cAlerta,{"Ok"})
	lRet := .F.
EndIf

If lRet
	aSldSB6 := CalcTerc(aCols[nPosCols, nPosCod],cA100For,cLoja,aCols[nPosCols, nPosIdentB6],aCols[nPosCols, nPosTES],cTipo)

	nQtdpd3 := QtdComp(nQtdPoder3)
	nSldPd3 := QtdComp(aSldSB6[1])
	If nQtdpd3 > nSldPd3

		cMsg := STR0521   
		cMsg += chr(13)+ chr(13) + STR0277 + ": "+ ALLTRIM(str(nQtdpd3)) 
		cMsg += chr(13) + STR0522 +ALLTRIM(str(nSldPd3))
		 
		Help(" ",1,"A100N/PD3.",,cMsg,1,0)
		lRet := .F.
		
	EndIf
EndIf

/*
aSldSB6[1] := Saldo de Poder Terceiro
aSldSB6[2] := Quantidade Poder Terceiro Liberada(ainda nao faturada)
aSldSB6[3] := Saldo total do poder de terceiro ( Valor Unitario)
aSldSB6[4] := Soma do total de devolucoes do Poder Terceiros
aSldSB6[5] := Valor Total em Poder Terceiros
aSldSB6[6] := Quantidade Total em Poder Terceiro
*/

If lRet
	//Somente se o parametro estiver no SX6 como .T. sera executada a validacao a seguir onde nao e permitido digitar 
	//um valor unitario na devolucao diferente do B6_PRUNIT disparando o Help A100VALOR, caso o parametro nao esteja no SX6
	//ou seu conteudo esteja .F. sera executada a validacao do ELSE que consiste o valor total da remessa de saida com o valor
	//total de todas as devolucoes vinculadas a remessa original permitindo que em cada devolucao seja digitado um valor unitario
	//diferente da remessa, contudo a soma total destas devolucoes tem que bater com o valor da remessa.
	If lBloqSb6
		SB6->(DbSetOrder(3))
		SB6->(dbSeek(xFilial("SB6") + aCols[nPosCols, nPosIdentB6]))
		If (Abs(A410Arred(SB6->B6_PRUNIT, 'D1_TOTAL') - A410Arred(aCols[nPosCols, nPosVUnit], 'D1_TOTAL')) >= 0.01)
			Help(" ",1,"A100VALOR")
			lRet := .F.
		EndIf
	Else
		If A410Arred(nSldPoder3,"D1_TOTAL")	> a410Arred((aSldSB6[5]-aSldSB6[4]),"D1_TOTAL")+0.01 .And. Valtype(l103Auto) == "L" .And. !l103Auto
			//O Valor Total do Item a ser devolvido È maior que o saldo disponÌvel no poder de terceiros de
			//O valor original da remessa È de 999.999,99 E foram encontradas devoluÁıes anteriores totalizando 99999999
			//No saldo disponÌvel em poder de terceiros, j· est· sendo considerada a existÍncia de notas de complemento
			//Para continuar È necessario que o valor total das devoluÁoes deste item n„o ultrapasse o valor original da remessa
			cHelpPD3 := STR0308+Alltrim(Transform((aSldSB6[5]-aSldSB6[4]),PesqPict("SD1","D1_TOTAL")))+CRLF
			cHelpPD3 += STR0309+AllTrim(aCols[nPosCols, nPosNfOri])+" - "+aCols[nPosCols][nPosSerOri]+STR0310+AllTrim(Transform(SD2->D2_TOTAL ,PesqPict("SD1","D1_TOTAL")))+CRLF
			cHelpPD3 += STR0311+AllTrim(Transform(aSldSB6[4],PesqPict("SD1","D1_TOTAL")))+CRLF
			cHelpPD3 += STR0316+" "+CRLF
			cHelpPD3 += STR0312+CRLF

			Aviso("A103VALOR",cHelpPD3,{"Ok"})
			lRet := .F.
		Else
			//Atencao! a variavel l103Auto portege o bloco a seguir para nao ser apresentado quando a devolucao for realizada 
			//pela opcao RETORNAR disparando o LOG da rotina automatica antes da tela de entrada impedindo que o usuario fizesse
			// a devolucao quando ha saldo
			
			//A quantidade informada neste item ira encerrar o saldo da remessa efetuada para terceiros. 
			//Este procedimento ira finalizar o controle de terceiros em quantidade e valor, porem o valor informado e inferior
			//ao saldo de remessa.
			If nQtdPoder3 == aSldSB6[1].And. ;
				A410Arred(nSldPoder3,"D1_TOTAL")+0.01 < a410Arred((aSldSB6[5]-aSldSB6[4]),"D1_TOTAL") .And. Valtype(l103Auto) == "L" .And. !l103Auto
				//O saldo em quantidade do Poder de Terceiros sera finalizado com esta devolucao,
				//Contudo ainda existe um saldo financeiro de 999.999.999,99
				//Este saldo deve ser consumido neste momento para que o valor total das devolucoes
				//corresponda ao valor original da remessa
				//No saldo disponivel em poder de terceiros, ja esta sendo considerada a existencia
				//de notas de complemento
				//MV_LIBESB6 - Parametro utilizado para liberar a inclusao de devolucoes de P3
				If !(lLibeSb6 .And. (AllTrim(cTipo) $ 'B|N'))
					cHelpPD3 := STR0313+AllTrim(Transform(a410Arred((aSldSB6[5]-aSldSB6[4]),"D1_TOTAL") - A410Arred(nSldPoder3,"D1_TOTAL")+0.01 ,PesqPict("SD1","D1_TOTAL")))+" "+CRLF
					cHelpPD3 += STR0314+" "+AllTrim(aCols[nPosCols][nPosNfOri])+" - "+AllTrim(aCols[nPosCols][nPosSerOri])+CRLF
					cHelpPD3 += STR0316+" "+CRLF
					Aviso("A103SLDPD3",cHelpPD3,{"Ok"})
					lRet := .F.
				EndIf
			EndIf
		EndIf
	EndIf
EndIf

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} GrossUpIRRF()
FunÁ„o que verifica se para operaÁ„o foi configurado o Gross Up do IRRF.
Se sim, o valor do IRRF N¬O dever· ser descontado do tÌtulo principal.

@param    nValIrrf - Valor do Imposto de Renda calculado na operaÁ„o
@param    lGrossIRRF  - LÛgico   - Indica se operaÁ„o È importaÁ„o de serviÁo configurado para deduzir o IRRF do tÌtulo principal
@return   nRet 	   - Caso seja hipÛtese de n„o descontar o IRRF do tÌtulo, a funÁ„o retornar· zero. 
                     Caso seja hipÛtese de descontar o IRRF, a funÁ„o retornar· o prÛprio valor de IRRF
@author Erick GonÁalves Dias
@since 17/04/2018
@version 12.1.17
/*/
//-------------------------------------------------------------------

Static Function GrossUpIRRF(nValIrrf, lGrossIRRF)

Local nRet	:= nValIrrf

If lGrossIRRF .AND. nValIrrf > 0
	//Se realizou GrossUP ent„o n„o dever· descontar do tÌtulo principal
	nRet := 0
EndIF

Return nRet

/*/{Protheus.doc} CodeSoma1 
//TODO Converte o valor do campo D1_ITEM para o campo D2_ITEM. 
Devido ao tamanho dos campos serem diferente e ter o uso da funÁ„o SOMA1()
@author reynaldo
@since 08/05/2018
@version 1.0
@return ${return}, ${return_description}
@param cItem, characters, Conteudo do campo D1_ITEM
@param nTamanho, numeric, Tamanho do campo D2_ITEM
@type function
/*/
Static Function CodeSoma1(cItem,nTamanho)
Local cResult
Local nLoop
Local nValor
		
nValor := DecodSoma1(cItem)

cResult := strzero(0,nTamanho)
For nLoop := 1 to nValor
	cResult := Soma1(cResult)
Next nLoop

Return cResult

/*/{Protheus.doc} A103ChkSig
//TODO Checa a assinatura dos fontes complementares da MATA103 est„o corretos.
@author reynaldo
@since 04/06/2018
@version 1.0
@return ${return}, ${return_description}

@type function
/*/
Static Function A103ChkSig()
Local lRet := .F.

	// Foi criado o fonte MATA103R.PRW, onde foi migrado o conteudo da funcao A103Devol com novo nome de SA103Devol
	lRet := FindFunction("SA103Devol")
	If !lRet
		Help(" ",1,"MATA103R",,STR0516,1,0) //"Atualizar MATA103R.PRX !!!"
	EndIf

	If lRet
		lRet := FindFunction("FISCIAP")
		If !lRet
			Help(" ",1,"FISXCIAP",,STR0532,1,0) // "Por favor, atualize o fonte FISXCIAP para uma vers„o igual ou superior a 24/07/2020." 
		EndIf
	EndIf

Return lRet

/*/{Protheus.doc} IsProdBloq
//Verifica se o produto est· bloqueado na importaÁ„o do PC por item.
@author juan.felipe
@since 22/08/2019
@version 1.0
@return lRet, Retorna .F. se protuto estiver bloqueado.
@param cProd, characters, CÛdigo do produto.
@type function
/*/
Static Function IsProdBloq(cProd)
Local aArea := SB1->(GetArea())
Local lRet := .T.
Local lMT103PBLQ := .F.

	SB1->(DbSetorder(1))

	If SB1->(Dbseek(xFilial("SB1")+cProd))
		If !RegistroOk("SB1",.F.)
			If ExistBlock("MT103PBLQ")
				lMT103PBLQ:=ExecBlock("MT103PBLQ",.F.,.F.,{cProd})
				If !lMT103PBLQ 
					lRet := RegistroOk("SB1")
				Else
					lRet := lMT103PBLQ
				Endif
			Else
				lRet := RegistroOk("SB1")
			Endif
		Endif
	EndIf

RestArea(aArea)

Return lRet

Static Function ProtCfgAdt()
Local aRet := {}
If FindFunction('CfgAdianta')
	aRet := CfgAdianta()
Else
	aRet := {;
			{FwModeAccess('FIE',1),;
 			 FwModeAccess('FIE',2),;
			 FwModeAccess('FIE',3),;
			 FWSIXUtil():ExistIndex( 'FIE', '4' ),;
			 FWSIXUtil():ExistIndex( 'FIE', '5' )},;
			{FwModeAccess('FR3',1),;
			 FwModeAccess('FR3',2),;
			 FwModeAccess('FR3',3),;
			 FWSIXUtil():ExistIndex( 'FR3' , '8' ),;
			 FWSIXUtil():ExistIndex( 'FR3' , '9' )},;
			{FwModeAccess('SE1',3),;
			 FwModeAccess('SE2',3)} }
EndIf
Return(aRet)

/*/{Protheus.doc} A103CRatIR
	FunÁ„o responsavel por instanciar o objeto de calculo
	do rateio de IR aluguel
	@type  Function
	@author Vitor Duca
	@since 22/04/2020
	@version 1.0
/*/
Function A103CRatIR() 
Local oRateio
	If cPaisLoc == "BRA" .and. FindFunction("FinXRatIR")
		If oRatIRF == NIL
			oRateio := FinBCRateioIR():New()
		Endif	  
	EndIf	
Return oRateio

/*/{Protheus.doc} A103GRatIr
	Realiza o GET da variavel oRatIrf para outros fontes
	@type  Function
	@author Vitor Duca
	@since 22/04/2020
	@version 1.0
	@return oRatIrf, Objeto, Objeto de calculo para o rateio de IR Aluguel
/*/
Function A103GRatIr()
Return oRatIRF

/*/{Protheus.doc} ComMetric
Media de itens por Documento de Entrada

@Param cOper		inc (Inclus„o)
@Param lAuto		T (Rotina Automatica) / F (Tela Padr„o)
@Param lClas		T (Inclusao via classificaÁ„o) / F (Inclus„o)
@Param cTipo		N (Normal) / C (Complemento) / D (DevoluÁ„o) / B (Beneficiamento)
@Param nItemMetric	Quantidade de itens inseridos na inclusao do PC

@author rodrigo.mpontes
@since 25/05/2021
@return Nil, indefinido
/*/
Static Function ComMetric(cOper,lAuto,lClas,cTipo,nItemMetric)

Local cIdMetric		:= "media-itens-notas-fiscais-entrada"
Local cRotina		:= "mata103"
Local cIncRot		:= Iif(lAuto,"-auto","-tela")
Local cTpIncRot		:= Iif(lClas,"-clas","-inc")
Local cTpDoc		:= "-"+Lower(cTipo)
Local cSubRoutine	:= cRotina+cOper+cIncRot+cTpIncRot+cTpDoc+"-average" 
Local lContinua		:= (FWLibVersion() >= "20210517") .And. FindClass('FWCustomMetrics')

If lContinua
	FWCustomMetrics():setAverageMetric(cSubRoutine, cIdMetric, nItemMetric, /*dDateSend*/, /*nLapTime*/,cRotina)
Endif

Return

/*/{Protheus.doc} RetDtBxPA
Retorna data de ultima baixa do PA

@author rd.santos
@since 29/06/2021
@return dDataBaixa
/*/
Function RetDtBxPA()
Local dDataBaixa := Max(SE2->E2_BAIXA,dDataBase)
Local cAliasSE5	 := GetNextAlias()
Local cQuery	 := ''

cQuery := "SELECT MAX(SE5.E5_DATA) DTBAIXA FROM "+RetSqlName("SE5")+" SE5 "
cQuery += "WHERE SE5.E5_FILIAL='"+xFilial("SE5")+"' AND "
cQuery += "SE5.E5_PREFIXO = '"+SE2->E2_PREFIXO+"' AND "
cQuery += "SE5.E5_NUMERO = '"+SE2->E2_NUM+"' AND "
cQuery += "SE5.E5_PARCELA = '"+SE2->E2_PARCELA+"' AND "
cQuery += "SE5.E5_TIPO = '"+SE2->E2_TIPO+"' AND "
cQuery += "SE5.E5_NATUREZ = '"+SE2->E2_NATUREZ+"' AND "
cQuery += "SE5.E5_CLIFOR = '"+SE2->E2_FORNECE+"' AND "
cQuery += "SE5.E5_LOJA = '"+SE2->E2_LOJA+"' AND "	
cQuery += "SE5.D_E_L_E_T_=' '"

cQuery := ChangeQuery(cQuery)

dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSE5,.T.,.T.)

If (cAliasSE5)->(!Eof())
	dDataBaixa := Max(STOD((cAliasSE5)->DTBAIXA),dDataBaixa)
Endif
	
(cAliasSE5)->(DbCloseArea())

Return dDataBaixa

/*/{Protheus.doc} ComMtQtd
Quantidade de documento de entrada, por funÁ„o (A103AtuSE2, A103GrvAtf,MafisAtuSf3)

@Param cOper		inc (Inclus„o)
@Param lAuto		T (Rotina Automatica) / F (Tela Padr„o)
@Param lClas		T (Inclusao via classificaÁ„o) / F (Inclus„o)
@Param cTipo		N (Normal) / C (Complemento) / D (DevoluÁ„o) / B (Beneficiamento)
@Param nItemMetric	Quantidade de itens inseridos na inclusao do PC

@author fabiano.dantas
@since 26/10/2021
@return Nil, indefinido
/*/
Static Function ComMtQtd(cOper,lAuto,lClas,cTipo,nItemMetric,cFunc)

Local cIdMetric		:= "compras-protheus_total-documento-de-entrada-por-funcao_total"
Local cRotina		:= "mata103"
Local cIncRot		:= Iif(lAuto,"-auto","-tela")
Local cTpIncRot		:= Iif(lClas,"-clas","-inc")
Local cTpDoc		:= "-"+Lower(cTipo)
Local cSubRoutine	:= cRotina+cOper+cIncRot+cTpIncRot+cTpDoc+"-"+cFunc 
Local lContinua		:= (FWLibVersion() >= "20210517") .And. FindClass('FWCustomMetrics')

If lContinua
	FWCustomMetrics():setSumMetric(cSubRoutine, cIdMetric, nItemMetric, /*dDateSend*/, /*nLapTime*/,cRotina)
Endif

Return


/*/{Protheus.doc} ComMtrTemp
Tempo mÈdio de execuÁ„o da inclus„o do documento de entrada

@Param cOper		inc (Inclus„o)
@Param lAuto		T (Rotina Automatica) / F (Tela Padr„o)
@Param lClas		T (Inclusao via classificaÁ„o) / F (Inclus„o)
@Param cTipo		N (Normal) / C (Complemento) / D (DevoluÁ„o) / B (Beneficiamento)
@Param nItemMetric	Quantidade de itens inseridos na inclusao do PC
@Param nSegsTot     Tempo gasto para inclus„o de um documento de entrada

@author Fabiano Dantas
@since 26/10/2021
@return Nil, indefinido
/*/
Static Function ComMtrTemp(cOper,lAuto,lClas,cTipo,nItemMetric,nSegsTot)

Local cIdMetric		:= "compras-protheus_tempo-medio-documento-de-entrada_seconds"
Local cRotina		:= "mata103"
Local cIncRot		:= Iif(lAuto,"-auto","-tela")
Local cTpIncRot		:= Iif(lClas,"-clas","-inc")
Local cTpDoc		:= "-"+Lower(cTipo)
Local cSubRoutine	:= cRotina+cOper+cIncRot+cTpIncRot+cTpDoc+'-average'
Local lContinua		:= (FWLibVersion() >= "20210517") .And. FindClass('FWCustomMetrics')

If lContinua
	FWCustomMetrics():setAverageMetric(cSubRoutine, cIdMetric, nItemMetric, /*dDateSend*/, nSegsTot, cRotina)
Endif

Return

/*/{Protheus.doc} SetProxNum
Efetua a carga do ProxNum para o aCols de entrada


@author Nilton Rodrigues
@since 22/03/2022
@return Nil, indefinido
/*/
Function SetProxNum
	Local nX          as Numeric
	Local nTotaCols   as numeric 
	Local nTotaHeader as numeric 
	Static _oProxNum 
	nTotaCols   := Len(aCols)
	nTotaHeader := Len(aHeader)

	If _oProxNum == NIL
		_oProxNum := JsonObject():New()
	Else 
		//- Reseta o Json
		_oProxNum:fromJson("{}")
	EndIf 

	For nX := 1 to Len(aCols)
		//Atualiza a regua de processamento
		If !aCols[nx][nTotaHeader+1]
			_oProxNum[cValToChar(nX)] := ProxNum()
		else
			_oProxNum[cValToChar(nX)] := Space(Len(SD1->D1_NUMSEQ))
		EndIf 
	Next nX
Return 

/*/{Protheus.doc} getItATF
	Retorna total de itens de uma base de ativo.

	@cItMax = Total de itens desmembrados de um ativo.
@author Leandro Fini
@since 23/08/2022
/*/
Static Function getItATF(cBase)

Local cAliasSN1 := GetNextAlias()
Local cItMax 	:= "" //Maior item (N1_ITEM) que existe de uma base de ativo
Local cQuery    := ""

Default cBase := ""

cQuery := "SELECT MAX(N1_ITEM) AS MAXITEM FROM " + RetSqlName("SN1")
cQuery += " WHERE N1_FILIAL  = '" + fwxFilial("SN1") + "'"
cQuery += " AND N1_CBASE = '" + cBase + "'"
cQuery += " AND D_E_L_E_T_ = ' '"

cQuery := ChangeQuery(cQuery)

dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSN1,.T.,.T.)

If (cAliasSN1)->(!Eof())
	cItMax := (cAliasSN1)->MAXITEM
Endif
	
(cAliasSN1)->(DbCloseArea())

Return cItMax

/*/{Protheus.doc} getNfOri
	Retorna o recno da NF de origem do CTE.

	@nRecSF1 = Recno da NF de origem
@author Leandro Fini
@since 23/08/2022
/*/
Static Function getNfOri(cDoc,cSerie,cFornec,cLoja,nOpc)

Local cAliasSF1 := GetNextAlias()
Local aAreaSF1  := SF1->(GetArea())
Local nRecSF1 	:= 0
Local cChaveSF1 := ""
Local cQuery    := ""

Default cDoc 	:= ""
Default cSerie  := ""
Default cFornec := ""
Default cLoja 	:= ""
Default nOpc 	:= 0

cQuery := "SELECT F8_NFORIG, F8_SERORIG, F8_FORNECE, F8_LOJA FROM " + RetSqlName("SF8")
cQuery += " WHERE F8_FILIAL  = '" + fwxFilial("SF8") + "'"
cQuery += " AND F8_NFDIFRE = '" + cDoc + "'"
cQuery += " AND F8_SEDIFRE = '" + cSerie + "'"
cQuery += " AND F8_TRANSP  = '" + cFornec + "'"
cQuery += " AND F8_LOJTRAN = '" + cLoja + "'"
If nOpc == 0//exclus„o do cte.
												
										   
	cQuery += " AND D_E_L_E_T_ = '*'"
Else 
												
											  
	cQuery += " AND D_E_L_E_T_ = ' '"
Endif
cQuery += " ORDER BY R_E_C_N_O_ DESC"

cQuery := ChangeQuery(cQuery)

dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSF1,.T.,.T.)

if (cAliasSF1)->(!Eof())
	cChaveSF1 := (cAliasSF1)->F8_NFORIG + (cAliasSF1)->F8_SERORIG + (cAliasSF1)->F8_FORNECE + (cAliasSF1)->F8_LOJA
endif

if !empty(cChaveSF1)
	DbSelectArea("SF1")
	SF1->(DbSetOrder(1))//F1_FILIAL+F1_DOC+F1_SERIE+F1_FORNECE+F1_LOJA
	if SF1->(MsSeek(fwxFilial("SF1") + cChaveSF1))
		nRecSF1 := SF1->(Recno())
	endif
endif
	
(cAliasSF1)->(DbCloseArea())
RestArea(aAreaSF1)

Return nRecSF1

/*/{Protheus.doc} isNfGatEst
	Retorna se È NF de garantia estendida de ativo fixo.

	@lRet = .T. -> Nota de garantia estendida
	@lRet = .F. -> Nota que gerou ativo.
@author Leandro Fini
@since 23/08/2022
/*/
Static Function isNfGatEst(cDoc,cSerie,cFornec,cLoja)

Local lRet 		:= .T.
Local cAliasSN1 := GetNextAlias()
Local cQuery    := ""

Default cDoc 	:= ""
Default cSerie  := ""
Default cFornec := ""
Default cLoja 	:= ""

cQuery := "SELECT N1_CBASE FROM " + RetSqlName("SN1")
cQuery += " WHERE N1_FILIAL  = '" + fwxFilial("SN1") + "'"
cQuery += " AND N1_NFISCAL = '" + cDoc + "'"
cQuery += " AND N1_NSERIE = '" + cSerie + "'"
cQuery += " AND N1_FORNEC = '" + cFornec + "'"
cQuery += " AND N1_LOJA = '" + cLoja + "'"
cQuery += " AND D_E_L_E_T_ = ' '"

cQuery := ChangeQuery(cQuery)

dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSN1,.T.,.T.)

If (cAliasSN1)->(!Eof())
	lRet := .F. //a NF gerou ativo de fato. N„o È garantia estendida.
Endif
	
(cAliasSN1)->(DbCloseArea())

Return lRet

/*/{Protheus.doc} getProdIguais
	Retorna a quantidade de produtos iguais na NF de origem
@author Leandro Fini
@since 20/06/2023
/*/
Static Function getProdIguais(cDoc,cSerie,cFornec,cLoja,cProduto)

Local nQtd 		:= 1
Local cAliasSD1 := GetNextAlias()
Local cQuery    := ""

Default cDoc 	:= ""
Default cSerie  := ""
Default cFornec := ""
Default cLoja 	:= ""
Default cProduto := ""

cQuery := "SELECT COUNT(D1_COD) PRODIG FROM " + RetSqlName("SD1")
cQuery += " WHERE D1_FILIAL  = '" + fwxFilial("SD1") + "'"
cQuery += " AND D1_DOC = '" + cDoc + "'"
cQuery += " AND D1_SERIE = '" + cSerie + "'"
cQuery += " AND D1_FORNECE = '" + cFornec + "'"
cQuery += " AND D1_LOJA = '" + cLoja + "'"
cQuery += " AND D1_COD = '" + cProduto + "'"
cQuery += " AND D_E_L_E_T_ = ' '"

cQuery := ChangeQuery(cQuery)

dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSD1,.T.,.T.)

If (cAliasSD1)->(!Eof())
	nQtd := (cAliasSD1)->PRODIG
Endif
	
(cAliasSD1)->(DbCloseArea())

Return nQtd
