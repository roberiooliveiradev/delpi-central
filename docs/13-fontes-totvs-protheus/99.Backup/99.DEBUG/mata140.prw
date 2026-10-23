#INCLUDE "TBICONN.CH" 
#INCLUDE "MATA140.CH"
#INCLUDE "PROTHEUS.CH"

#DEFINE VALMERC	01	// Valor total do mercadoria
#DEFINE VALDESC	02	// Valor total do desconto
#DEFINE TOTPED	    03	// Total do Pedido
#DEFINE FRETE     	04  // Valor total do Frete
#DEFINE VALDESP   	05	// Valor total da despesa
#DEFINE SEGURO	    07	// Valor total do seguro

Static aPedC      := {} 
Static lPLSMT103  := findFunction("PLSMT103") 
Static lIsRussia := (cPaisLoc == "RUS")  

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³ MATA140  ³ Autor ³ Edson Maricate        ³ Data ³ 24.01.2000 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³ Digitacao das Notas Fiscais de Entrada sem os dados Fiscais  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ Generico                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function MATA140(xAutoCab,xAutoItens,nOpcAuto,lSimulaca,nTelaAuto,xCompDKD)

Local aCores    := {	{ 'Empty(F1_STATUS)','ENABLE' 		},;// NF Nao Classificada
						{ 'F1_STATUS=="B"'	,'BR_LARANJA'	},;// NF Bloqueada
						{ 'F1_STATUS=="C"'	,'BR_VIOLETA'   },;	// NF Bloqueada s/classf.
						{ 'F1_TIPO=="N"'	,'DISABLE'		},;// NF Normal
						{ 'F1_TIPO=="P"'	,'BR_AZUL'		},;// NF de Compl. IPI
						{ 'F1_TIPO=="I"'	,'BR_MARROM'	},;// NF de Compl. ICMS
						{ 'F1_TIPO=="C"'	,'BR_PINK'		},;// NF de Compl. Preco/Frete
						{ 'F1_TIPO=="B"'	,'BR_CINZA'		},;// NF de Beneficiamento
						{ 'F1_TIPO=="D"'	,'BR_AMARELO'	} }// NF de Devolucao
						
Local cFiltraSf1    := ""
Local nX,nAutoPC,nZ	:= 0
Local aCoresUsr     := {}    
Local cTamItem

PRIVATE aRotina 	:= MenuDef()
PRIVATE cCadastro	:= OemToAnsi(STR0007) //"Pre-Documento de Entrada"
PRIVATE l140Auto	:= ( ValType(xAutoCab) == "A"  .And. ValType(xAutoItens) == "A" )
PRIVATE aAutoCab	:= xAutoCab
PRIVATE aAutoItens	:= xAutoItens
PRIVATE aHeadSD1    := {}
PRIVATE l103Auto	:= l140Auto
PRIVATE lOnUpdate	:= .T.
PRIVATE nMostraTela := 0 // 0 - Nao mostra tela 1 - Mostra tela e valida tudo 2 - Mostra tela e valida so cabecalho
PRIVATE a140Total := {0,0,0}
PRIVATE a140Desp  := {0,0,0,0,0,0,0,0}

Private oLbx  
Private _aDivPNF := {}

Private nVlrFrt140	:= 0
Private aFrt140		:= {}
PRIVATE lTOPDRFRM 	:= FindFunction("A120RDFRM") .And. A120RDFRM("A103")
Private axCodRet 	:= {}

Private lIntermed	:= A103CPOINTER()

Private nQtdAnt    	:= 0
Private aAutoDKD	:= {}

DEFAULT nOpcAuto	:= 3
DEFAULT lSimulaca	:= .F.
DEFAULT nTelaAuto   := 0

If MaFisFound("NF")
	MaFisEnd()
EndIf

If l140Auto   
	For nX:= 1 To Len(xAutoItens)
		If (nAutoPC := Ascan(xAutoItens[nx],{|x| x[1]== "D1_PEDIDO"})) > 0
		     If Empty(xAutoItens[nX][nAutoPC][3])
		     	xAutoItens[nX][nAutoPC][3]:= "vazio().or. A103PC()"
			 EndIf
		EndIf
	Next
EndIf      

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Se estiver usando conferencia fisica muda opcoes do mbrowse³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If (SuperGetMV("MV_CONFFIS",.F.,"N") == "S")
	aCores    := {	{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. Empty(F1_STATUS)'	, 'ENABLE' 		},;	// NF Nao Classificada
					{ 'F1_TIPO=="N" .AND. !Empty(F1_STATUS) .AND. (!F1_STATUS$"B;C")'           , 'DISABLE'		},; // NF Normal
					{ 'F1_STATUS=="B"'															, 'BR_LARANJA'	},;	// NF Bloqueada
				    { 'F1_STATUS=="C"'															, 'BR_VIOLETA'	},; // NF Bloqueada s/classf.
					{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="P"'	 	, 'BR_AZUL'		},;	// NF de Compl. IPI
					{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="I"'	 	, 'BR_MARROM'	},;	// NF de Compl. ICMS
					{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="C"'	 	, 'BR_PINK'		},;	// NF de Compl. Preco/Frete
					{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="B"'	 	, 'BR_CINZA'	},;	// NF de Beneficiamento
					{ '((F1_STATCON $ "1|4") .OR. EMPTY(F1_STATCON)) .AND. F1_TIPO=="D"'    	, 'BR_AMARELO'	},;	// NF de Devolucao
					{ '!(F1_STATCON $ "1|4") .AND. !EMPTY(F1_STATCON) .AND. Empty(F1_STATUS)'	, 'BR_PRETO'	}} 	// NF Bloq. para Conferencia
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//| Adiciona rotinas ao aRotina                                  |
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ExistBlock( "MT140FIL" )
    cFiltraSF1 := ExecBlock("MT140FIL",.F.,.F.)
	If ( ValType(cFiltraSF1) <> "C" )
		cFiltraSF1 := ""
	EndIf
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Ponto de entrada para Manipular o Array com as regras e cores da Mbrowse ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ( ExistBlock("MT140COR") )			
	aCoresUsr := ExecBlock("MT140COR",.F.,.F.,{aCores})
	If ( ValType(aCoresUsr) == "A" )
		aCores := aClone(aCoresUsr)
	EndIf
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica a permissao do programa em relacao aos modulos      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If AMIIn(2,4,11,12,14,17,39,41,42,97,17,44,67,69,72,87) 
	Pergunte("MTA140",.F.)
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Ativa tecla F12 para ativar parametros de lancamentos contab.  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If l140Auto
		lOnUpdate  := !lSimulaca
		nMostraTela:= nTelaAuto
		aAutoCab   := xAutoCab
		aAutoItens := xAutoItens
		aAutoDKD   := IIf(xCompDKD<>NIL,xCompDKD,{})	

		If nOpcAuto == 7
			aRotBack 	  := aClone(aRotina)
			aRotina[5][2] := aRotBack[7][2]
			nOpcAuto	  := 5
		EndIf
		
		If	GetMV("MV_INTPMS",,"N") == "S"

			cTamItem := TamSX3("D1_ITEM")[1]    
			For nZ:= 1 To Len(aAutoItens)
				If aScan(aAutoItens[nZ],{|x| Alltrim(x[1]) == "D1_ITEM"}) == 0 
					aAdd(aAutoItens[nZ],{"D1_ITEM",StrZero(nZ,cTamItem),NIL})
				Endif
			Next nZ
			
		Endif
		
		MBrowseAuto( nOpcAuto, AClone( aAutoCab ), "SF1" )
                          
		If nOpcAuto == 5 .And. aRotina[5][2] == "A140EstCla" 
			aRotina:= aClone(aRotBack)
		EndIf

		xAutoCab   := aAutoCab
		xAutoItens := aAutoItens
	Else
		SetKey(VK_F12,{||Pergunte("MTA140",.T.)})
		mBrowse(6,1,22,75,"SF1",,,,,,aCores,,,,,,,,cFiltraSF1) 
		SetKey(VK_F12,Nil)
	EndIf
EndIf
Return
/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³A140NFisca³ Autor ³ Eduardo Riera         ³ Data ³02.10.2002 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³Interface do pre-documento de entrada                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpL1: Alias do arquivo                                      ³±±
±±³          ³ExpN2: Numero do Registro                                    ³±±
±±³          ³ExpN3: Opcao selecionada no arotina                          ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³Nenhum                                                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Esta rotina tem como objetivo controlar a interface de um    ³±±
±±³          ³pre-documento de entrada                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Materiais                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function A140NFiscal(cAlias,nReg,nOpcX)
Local aRecSD1   := {}
Local aObjects  := {}
Local aInfo 	:= {}
Local aPosGet	:= {}
Local aPosObj	:= {}
Local aStruSD1  := {}
Local aListBox  := {}
Local aCamposPE := {}
Local aNoFields := {}
Local aRecOrdSD1:= {}
Local aTitles   := {OemToAnsi(STR0038), STR0008, STR0034} //"Fornecedor/Cliente" ### "Descontos/Frete/Despesas" //"Totais"
Local aFldCBAtu := Array(Len(aTitles))
Local aInfForn	:= {"","",CTOD("  /  /  "),CTOD("  /  /  "),"","","",""}
Local aSizeAut  := {}
Local aButtons	:= {}
Local aListCpo 	:= {	"D1_COD"	,;
						"D1_UM"		,;
						"D1_QUANT"	,;
						"D1_VUNIT"	,;
						"D1_TOTAL"	,;
						"D1_LOCAL"	,;
						"D1_PEDIDO"	,;
						"D1_ITEMPC"	,;
						"D1_SEGUM"	,;
						"D1_QTSEGUM",;
						"D1_CC"		,;
						"D1_CONTA"	,;
						"D1_ITEMCTA",;
						"D1_CLVL"	,;
						"D1_ITEM"	,;
						"D1_LOTECTL",;
						"D1_NUMLOTE",;
						"D1_DTVALID",;
						"D1_LOTEFOR",;
						"D1_DFABRIC",;
						"D1_DESC"	,;
						"D1_VALDESC",;
						"D1_OP"		,;
						"D1_CODGRP"	,;
						"D1_CODITE"	,;
						"D1_VALIPI"	,;
						"D1_VALICM"	,;
						"D1_IPI"	,;
						"D1_PICM"	,;
						"D1_PESO"	,;
						"D1_TP"		,;
						"D1_BASEICM",;
						"D1_BASEIPI",;
						"D1_TEC"	,;
						"D1_CONHEC"	,;
						"D1_TIPO_NF",;
						"D1_NFORI"	,;
						"D1_SERIORI",;
						"D1_ITEMORI",;
						"D1_VALIMP1",;
						"D1_VALIMP2",;
						"D1_VALIMP3",;
						"D1_VALIMP4",;
						"D1_VALIMP5",;
						"D1_VALIMP6",;
						"D1_BASIMP1",;
						"D1_BASIMP2",;
						"D1_BASIMP3",;
						"D1_BASIMP4",;
						"D1_BASIMP5",;
						"D1_BASIMP6",;
						"D1_ALQIMP1",;
						"D1_ALQIMP2",;
						"D1_ALQIMP3",;
						"D1_ALQIMP4",;
						"D1_ALQIMP5",;
						"D1_ALQIMP6",;
						"D1_VALFRE"	,;
						"D1_RATEIO"	,;
						"D1_SEGURO"	,;
						"D1_DESPESA",;
						"D1_FORMUL"	,;
						"D1_II"		,;
						"D1_ICMSDIF",;		
						"D1_ITEMMED",;
						"D1_CODNE",;
						"D1_ITEMNE",;
						"D1_ICMSRET",;
						"D1_ALIQSOL",;
						"D1_POTENCI" } 
					
Local l140Inclui := .F.
Local l140Altera := .F.
Local l140Exclui := .F.
Local l140Visual := .F.
Local lContinua  := .T.
Local lQuery     := .F.
Local lItSD1Ord  := IIF(mv_par03==2,.T.,.F.)
Local lConsMedic := .F.
Local lExistMemo := .F. 
Local lIntACD	 := SuperGetMV("MV_INTACD",.F.,"0") == "1"
Local lSubSerie  := cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_SUBSERI")) > 0 .And. SuperGetMv("MV_SUBSERI",.F.,.F.)
Local lColab 	 := l140Auto .And. !Empty(aAutoCab) .And. aScan(aAutoCab, {|x| x[1] == "COLAB" .And. x[2] == "S"}) > 0
Local lMvNfeDvg  := SuperGetMV("MV_NFEDVG", .F., .T.)
Local cAliasSD1  := "SD1"
Local nX         := 0
Local nPosGetLoja:= IIF(TamSX3("A2_COD")[1]< 10,(2.5*TamSX3("A2_COD")[1])+(110),(2.8*TamSX3("A2_COD")[1])+(100))
Local nOpcA		 := 0
Local nQtdConf   := 0
Local nSaveSX8   := GetSX8Len()
Local bWhileSD1  := {||.T.}
Local bCabOk     := {||.T.}
Local oDlg
Local oFolder
Local oEnable    := LoadBitmap( GetResources(), "ENABLE" )
Local oDisable   := LoadBitmap( GetResources(), "DISABLE" )
Local oStatCon
Local oConf
Local oTimer
Local dDataFec   := MVUlmes()
Local aCTBEnt	 := CTBEntArr()
Local aButVisual := {}
Local nSPed		 := 0
Local nSItPed    := 0  
Local nSMed      := 0
Local nSItem 	 := 0
Local cTipoNf    := SuperGetMv("MV_TPNRNFS")
Local nFldInter	 := 0
Local aPedItAnt  := {}


// Conferencia fisica do SIGAACD
Local lWmsCRD    := SuperGetMV("MV_WMSCRD",.F.,.F.)
Local lEstConfF  := .F. //Se estorna a conferência

// Variável para integração com módulo SIGAPFS
Local lIntPFS := SuperGetMv("MV_JURXFIN",.T., .F.) .And. AliasInDic("OHV")
Local lIntGC := IIf((SuperGetMV("MV_VEICULO",,"N")) == "S",.T.,.F.)

Private oGetDados
Private bGDRefresh	:= {|| IIf(oGetDados<>Nil,(oGetDados:oBrowse:Refresh()),.F.) }		// Efetua o Refresh da GetDados
Private bRefresh    := {|nX,nY,nTotal,nValDesc| Ma140Total(a140Total,a140Desp,nTotal,nValDesc),NfeFldChg(,,oFolder,aFldCBAtu),IIf(oGetDados<>Nil,(oGetDados:oBrowse:Refresh()),.F.)}
Private l103Visual  := .T. //-- Nao permite alterar os campos de despesas/frete.
Private lNfMedic    := .F.
Private lDKD		:= ChkFile("DKD") //Tabela Complementar SD1
Private lTabAuxD1	:= .F.
Private aHeadDKD	:= {}
Private aColsDKD	:= {}
Private aAltDKD		:= {}
Private oGetDKD		:= Nil

If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
	PRIVATE aInfAdic	:= {}
Endif

DEFAULT aPedC	:= {}    

l140Auto := !(Type("l140Auto")=="U" .Or. !l140Auto)

//Adiciona campos D1_CF e D1_CLASFIS quando não for ExecAuto ou recebido no aAutoItens
If !l140Auto
	aAdd( aListCpo, "D1_CF")
	aAdd( aListCpo, "D1_CLASFIS")
ElseIf l140Auto .And. SuperGetMV("MV_EASY",,"N") == "S" .And. !lColab // Adiciona campos D1_CF e D1_CLASFIS quando for SIGAEIC
	aAdd( aListCpo, "D1_CF")
	aAdd( aListCpo, "D1_CLASFIS")
Else
	If SuperGetMv("MV_VLDOBRI",.F.,.F.)
		If Ascan(aAutoItens[1],{|x| x[1]== "D1_CF"}) != 0
			aAdd( aListCpo, "D1_CF")
		EndIf
		If Ascan(aAutoItens[1],{|x| x[1]== "D1_CLASFIS"}) != 0
			aAdd( aListCpo, "D1_CLASFIS")
		EndIf
	EndIf
EndIf

//Adiciona campo ordem de serico quando integrado ao modulo de MNT
If SuperGetMV("MV_NGMNTES",.F.,"N") == "S"
	aAdd( aListCpo, "D1_ORDEM")
EndIf

// Zera os totais para que a chamada de inclusao apos uma gravacao nao traga os valores preenchidos 
a140Total := {0,0,0}
a140Desp  := {0,0,0,0,0,0,0,0}

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inclui os campos referentes as entidades contabeis           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
For nX := 1 To Len(aCTBEnt)
	aAdd(aListCpo,"D1_EC" +aCTBEnt[nX] +"CR")
	aAdd(aListCpo,"D1_EC" +aCTBEnt[nX] +"DB")
Next nX

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inclui os campos referentes ao WMS na Pre-Nota               ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If IntWMS()
	aAdd(aListCpo, 'D1_SERVIC')
	aAdd(aListCpo, 'D1_STSERV')
	aAdd(aListCpo, 'D1_ENDER' )
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inclui os campos referentes ao EIC na Pre-Nota               ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If l140Auto .And. SuperGetMV("MV_EASY",,"N") == "S"
	aAdd(aListCpo, 'D1_DATORI'  )
	aAdd(aListCpo, 'D1_ALQFECP' )
	aAdd(aListCpo, 'D1_VALFECP' )
	aAdd(aListCpo, 'D1_BASFECP' )
	aAdd(aListCpo, 'D1_VOPDIF' )	
EndIf 

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Quando rotina automática e o processo executado e uma transf.³
//³ entre filiais, grava na TES o conteúdo enviado - mv_par15	 ³
//³ MATA310 - array aParam310[15]								 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If l140Auto .and. (IsInCallStack("MATA310") .or. IsInCallStack("MATA311") .Or. IsInCallStack("OFIOM430") .Or. FwIsInCallStack("COMXCOL") .Or. FwIsInCallStack("COMGERJOB") .Or. FwIsInCallStack("PROCDOCS"))
	aAdd(aListCpo, 'D1_TESACLA' )  
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inclusao do campos D1_VALCMAJ para tratamento da Aliquota	 ³
//³ Majorada da COFINS Importacao.								 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aAdd(aListCpo, 'D1_VALCMAJ')

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inclusao do campo D1_VALPMAJ para tratamento da Aliquota	 ³
//³ Majorada do PIS Importacao.									 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aAdd(aListCpo, 'D1_VALPMAJ')

//Inclusão do Campo D1_FCICOD
If SD1->(FieldPos("D1_FCICOD")) > 0
	aAdd(aListCpo, 'D1_FCICOD')
EndIf

//Inclusão do Campo D1_BASNDES
If (SD1->(FieldPos("D1_BASNDES")) > 0)
	aAdd(aListCpo, 'D1_BASNDES')
EndIf

//Inclusão do Campo D1_ICMNDES
If (SD1->(FieldPos("D1_ICMNDES")) > 0)
	aAdd(aListCpo, 'D1_ICMNDES')
EndIf

//Inclusão do Campo D1_ALQNDES
If (SD1->(FieldPos("D1_ALQNDES")) > 0)
	aAdd(aListCpo, 'D1_ALQNDES')
EndIf

If Type("lTOPDRFRM") <> "U" .And. lTOPDRFRM
	aAdd(aListCpo, 'D1_RETENCA')
	aAdd(aListCpo, 'D1_DEDUCAO')
	aAdd(aListCpo, 'D1_FATDIRE')
Endif	

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Chamada do ponto de entrada MT140CPO                         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ExistTemplate("MT140CPO")
	aCamposPE := If(ValType(aCamposPE:=ExecTemplate('MT140CPO',.F.,.F.))=='A',aCamposPE,{})
	If Len(aCamposPE) > 0
		For nX := 1 to Len(aCamposPE)
			If (aScan(aListCpo, aCamposPE[nX])) == 0
				aadd(aListCpo, aCamposPE[nX])
			EndIf
		Next nX
	EndIf
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Chamada do ponto de entrada MT140CPO                         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ExistBlock("MT140CPO")
	aCamposPE := If(ValType(aCamposPE:=ExecBlock('MT140CPO',.F.,.F.))=='A',aCamposPE,{})
	If Len(aCamposPE) > 0
		For nX := 1 to Len(aCamposPE)
			If (aScan(aListCpo, aCamposPE[nX])) == 0
				aadd(aListCpo, aCamposPE[nX])
			EndIf
		Next nX
	EndIf
EndIf                                                           

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Chamada do ponto de entrada MT140DCP 					   ³                                                |
//| Para não exibir os campos customizados no Acols, é necessário incluir o mesmo no aListBox e posteriormente  |
//| carregar o mesmo no array aNolFields para ser descconsiderado na FillGetDados 								|
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aNoFields:= {}
If ExistBlock("MT140DCP")
	aNoFields := If(ValType(aNoFields:=ExecBlock('MT140DCP',.F.,.F.))=='A',aNoFields,{})
	If Len(aNoFields) > 0
		For nX := 1 to Len(aNoFields)
			If (aScan(aListCpo, aNoFields[nX])) == 0
				aadd(aListCpo, aNoFields[nX])
			EndIf
		Next nX
	EndIf
EndIf

If  FindFunction("COMXVLDCPO")
	aListCpo := COMXVLDCPO(aListCpo,1) //retira campos não usdos.
Endif	

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica a operacao a ser realizada                          ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
Do Case
	Case aRotina[nOpcX][4] == 2
		l140Visual := .T.
	Case aRotina[nOpcX][4] == 3
		l140Inclui	:= .T.
	Case aRotina[nOpcX][4] == 4
		l140Altera	:= .T.
	Case aRotina[nOpcX][4] == 5
		l140Exclui	:= .T.
		l140Visual	:= .T.
EndCase

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Analisa data de fechamento somente quando o parametro MV_DATAHOM  |
//| estiver configurado com o conteudo igual a "2"                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If l140Inclui .And. SuperGetMv("MV_DATAHOM",.F.,"1")=="2"
	If dDataFec >= dDataBase
		Help( " ", 1, "FECHTO" )
		lContinua := .F.
    EndIf
EndIf

// Evita reacumulo do saldo em aPedc (ao cancelar alt./realterar/F6) BOPS 90013 07/02/06
If !l140Visual
	aPedC	:= {}	
EndIf

//Criação dos campos no array aInfAdic - Intermediador
If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
	A103ChkInfAdic(Iif(l140Inclui,1,2))
Endif

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inicializa as variaveis da Modelo 2                          ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
Private bPMSDlgNF	:= {||PmsDlgNF(nOpcX,cNFiscal,cSerie,cA100For,cLoja,cTipo)} // Chamada da Dialog de Gerenc. Projetos
Private aRatAFN     := {}
Private aHdrAFN     := {}
Private	cTipo		:= If(l140Inclui,CriaVar("F1_TIPO")		,SF1->F1_TIPO)
Private cTpCompl	:= ""
Private cFormul		:= If(l140Inclui,CriaVar("F1_FORMUL")	,SF1->F1_FORMUL)
Private cNFiscal 	:= If(l140Inclui,CriaVar("F1_DOC")		,SF1->F1_DOC)
Private cSerie		:= If(l140Inclui,SerieNfId("SF1",5,"F1_SERIE")	,SerieNfId("SF1",2,"F1_SERIE"))
Private cSubSerie   := ""
Private dDEmissao	:= If(l140Inclui,CriaVar("F1_EMISSAO")	,SF1->F1_EMISSAO)
Private cA100For	:= If(l140Inclui,CriaVar("F1_FORNECE")	,SF1->F1_FORNECE)
Private cLoja		:= If(l140Inclui,CriaVar("F1_LOJA")		,SF1->F1_LOJA)
Private cEspecie	:= If(l140Inclui,CriaVar("F1_ESPECIE")	,SF1->F1_ESPECIE)
Private cUfOrigP	:= If(l140Inclui,CriaVar("F1_EST")		,SF1->F1_EST)
Private cTpFrete	:= If(l140Inclui,CriaVar("F1_TPFRETE")	,SF1->F1_TPFRETE)
Private n           := 1
Private aCols		:= {}
Private aHeader 	:= {}
Private lReajuste   := IIF(mv_par01==1,.T.,.F.)
Private lConsLoja   := IIF(mv_par02==1,.T.,.F.)
Private cForAntNFE  := ""
Private cLojAntNFE  := ""
Private lMudouNum   := .F.

If SF1->(ColumnPos("F1_TPCOMPL")) > 0
	cTpCompl	:= IIF(l140Inclui,CriaVar("F1_TPCOMPL",.F.),SF1->F1_TPCOMPL)
EndIf

If lSubSerie
	cSubSerie := If(l140Inclui,CriaVar("F1_SUBSERI"),SF1->F1_SUBSERI)
EndIf
nVlrFrt140 := 0
aFrt140	:= {}

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Habilita as HotKeys e botoes da barra de ferramentas         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If (!l140Auto .Or. (nMostraTela <> 0)) .And. (l140Inclui .Or. l140Altera) 
    If !l140Altera
		aButtons	:= {{'PEDIDO',{||A103ForF4(.F.,a140Desp, lNfMedic, lConsMedic),Eval(bRefresh)},STR0009,STR0010},; //"Pedidos de Compras"
						{'SDUPROP',{||A103ItemPC(.F.,aPedC,oGetDados, lNfMedic, lConsMedic,,,a140Desp ),Eval(bRefresh)},STR0011,STR0031} } //"PEDIDO"###"Pedidos de Compras(por item)"
						
		SetKey( VK_F5, { || A103ForF4(.F.,a140Desp, lNfMedic, lConsMedic ),Eval(bRefresh) } )
		SetKey( VK_F6, { || A103ItemPC(.F.,aPedC,oGetDados, lNfMedic, lConsMedic,,,a140Desp ),Eval(bRefresh) } )

    Else                    
		aButtons	:= {{'SDUPROP',{||A103ItemPC(.F.,aPedC,oGetDados, lNfMedic, lConsMedic,,,a140Desp ),Eval(bRefresh)},STR0011,STR0031} } //"PEDIDO"###"Pedidos de Compras(por item)"
		
		SetKey( VK_F6, { || A103ItemPC(.F.,aPedC,oGetDados, lNfMedic, lConsMedic,,,a140Desp ),Eval(bRefresh) } )
    EndIf	
    aAdd(aButtons, {'RECALC',{||A140NFORI()},(STR0070,STR0071)} ) //"Selecionar Documento Original ( Devolucao/Beneficiamento/Complemento )"} )    
EndIf

If (!l140Auto .Or. (nMostraTela <> 0)) .And. IntePms()
	If l140Altera .Or. l140Visual
		aadd(aButVisual, {'PROJETPMS',bPmsDlgNF,STR0012,STR0032}) //"Gerenciamento de Projetos"
	EndIf
	aadd(aButtons, {'PROJETPMS',bPmsDlgNF,STR0012,STR0032}) //"Gerenciamento de Projetos"
	SetKey( VK_F10, { || Eval(bPmsDlgNF)} )
EndIf

lConsMedic := A103GCDisp()

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Habilita o folder de conferencia fisica se necessario        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If cPaisLoc == "BRA"
	If l140Visual
		If UsaConfF(cTipo, cA100For, cLoja)
			aadd(aTitles,STR0013) //"Conferencia Fisica"
		EndIf
	EndIf

	If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
		aadd(aTitles,"Informações adicionais") //"Informações adicionais"
		nFldInter	:= Len(aTitles)
		aAdd(aFldCBAtu,)
	Endif
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Verifica se o usuario tem permissao de exclusao. ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If nOpcX == 5	
	aArea2 := GetArea()
	SD1->(dbSeek(xFilial("SD1")+cNFiscal+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)))
	While !SD1->(Eof()) .And. lContinua .And. SD1->D1_DOC == cNFiscal .And. SD1->D1_SERIE == cSerie
		lContinua := MaAvalPerm(1,{SD1->D1_COD,"MTA140",5})
		SD1->(dbSkip())
	End
	RestArea(aArea2)
	If !lContinua
		Help(,,1,'SEMPERM')
	EndIf	
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica se a NF possui NF de Conhec. e Desp. de Import.     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If l140Exclui .And. lContinua
	SF8->(dbSetOrder(2))
	If SF8->(MsSeek(xFilial("SF8")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA))
		Help(" ", 1, "A103CAGREG")
		lContinua := .F.
	EndIf	
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Notas Fiscais NAO Classificadas geradas pelo SIGAEIC NAO deverao ser visualizadas no MATA140 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If cPaisLoc == "BRA" .And. l140Visual .And. (!Empty(SF1->F1_HAWB) .OR. ALLTRIM(SF1->F1_ORIGEM) == "SIGAEIC")  .And. Empty(SF1->F1_STATUS) .And. (!IsInCallStack("DI154DELET") .And. !IsInCallStack("DI154CapNF") .And. !IsInCallStack("DI554Estorna"))  
	Aviso("A140NOVIEWEIC",STR0065,{"Ok"}) // "Este documento foi gerado pelo SIGAEIC e ainda NÃO foi classificado, para visualizar utilizar a opção classificar ou no Modulo SIGAEIC opção Desembaraço/recebimento de importação/Totais. Apos a classificação o documento pode ser visualizado normalmente nesta opção."
	lContinua := .F.
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Ponto de entrada para validar a alteracao de um pre-documento ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If l140Altera .And. ExistBlock("A140ALT") .And. lContinua
	lContinua := If(ValType(lContinua:=ExecBlock("A140ALT",.F.,.F.))=='L',lContinua,.T.)
EndIf	

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Chamada do banco de conhecimento                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lContinua .And. (l140Visual .Or. l140Altera)
	AAdd(aButVisual,{ "clips", {|| A140Conhec() }, STR0066, STR0067 } ) // "Banco de Conhecimento", "Conhecim."
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica se há integração com módulo WMS
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lContinua .And. (IntWMS() .Or. lWmsCRD) .And. (l140Altera .Or. l140Exclui)
	lContinua := WmsAvalSF1(Iif(l140Altera,"3","4"),"SF1")
EndIf

If !l140Inclui .And. lContinua
	If !(ExistBlock("MT140FRT"))
		//-- Atualiza dados do folder de despesas
		a140Desp[VALDESP]:= SF1->F1_DESPESA
		a140Desp[FRETE]  := SF1->F1_FRETE
		a140Desp[SEGURO] := SF1->F1_SEGURO
	EndIf

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Montagem do aCols                                            ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If !l140Visual
		If !SoftLock("SF1")
			lContinua := .F.
		EndIf
	EndIf
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Alteracao - Verifica Status da conferencia                   ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If lContinua .And. SF1->F1_STATCON == "1" .And. !l140Visual .And. cPaisLoc == "BRA"
		If UsaConfF(cTipo, cA100For, cLoja)
			If IsBlind()
				lEstConfF := .T.
			Else
				lEstConfF := Aviso(OemToAnsi(STR0035),OemToAnsi(STR0054),{STR0026,STR0027})==1 //Atencao##"Documento já conferido. Deseja estornar a conferência?"
			EndIf
			If lEstConfF
				A140AtuCon(,,,,,,,,.T.) //lReconta := .T.
			Else
				lContinua := .F.
			EndIf
		EndIf
	EndIf
	If lContinua
		dbSelectArea("SD1")
		dbSetOrder(1)

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica a existencia de campo MEMO no SD1 para nao executar a Query.³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		SX3->(dbSetOrder(1))
		SX3->(MsSeek("SD1"))
		While !SX3->(Eof()) .And. SX3->X3_ARQUIVO == "SD1"
			If (IIf((!l140Auto .Or. (nMostraTela <> 0)),X3USO(SX3->X3_USADO),.T.) .And.;
			 Ascan(aListCpo,Trim(SX3->X3_CAMPO)) != 0 .And. cNivel >= SX3->X3_NIVEL) .Or.;
			(SX3->X3_PROPRI == "U" .And. cNivel >= SX3->X3_NIVEL)
				If SX3->X3_TIPO == "M"
					lExistMemo := .T. 
					Exit
				EndIf
			EndIf
			SX3->(dbSkip())
		EndDo
		If !InTransact() .And. !lExistMemo
			aStruSD1 := SD1->(dbStruct())
			lQuery   := .T.
			cQuery := "SELECT SD1.R_E_C_N_O_ SD1RECNO,SD1.* "
			cQuery += "FROM "+RetSqlName("SD1")+" SD1 "
			cQuery += "WHERE SD1.D1_FILIAL='"+xFilial("SD1")+"' AND "
			cQuery += "SD1.D1_DOC = '"+SF1->F1_DOC+"' AND "
			cQuery += "SD1.D1_SERIE = '"+SF1->F1_SERIE+"' AND "
			cQuery += "SD1.D1_FORNECE = '"+SF1->F1_FORNECE+"' AND "
			cQuery += "SD1.D1_LOJA = '"+SF1->F1_LOJA+"' AND "
			cQuery += "SD1.D_E_L_E_T_=' ' "
			If lItSD1Ord .Or. ALTERA
				cQuery += "ORDER BY "+SqlOrder( "D1_FILIAL+D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_ITEM+D1_COD" )
			Else
				cQuery += "ORDER BY "+SqlOrder(SD1->(IndexKey()))
			EndIf
			cQuery := ChangeQuery(cQuery)
			SD1->(dbCloseArea())
			dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),"SD1")
			For nX := 1 To Len(aStruSD1)
				If aStruSD1[nX][2]<>"C"
					TcSetField("SD1",aStruSD1[nX][1],aStruSD1[nX][2],aStruSD1[nX][3],aStruSD1[nX][4])
				EndIf
			Next nX
		Else
			MsSeek(xFilial("SD1")+cNFiscal+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
		EndIf

		bWhileSD1 := { || ( !Eof().And. lContinua .And. ;
				(cAliasSD1)->D1_FILIAL== xFilial("SD1") .And. ;
				(cAliasSD1)->D1_DOC == cNFiscal .And. ;
				(cAliasSD1)->D1_SERIE == SF1->F1_SERIE .And. ;
				(cAliasSD1)->D1_FORNECE == SF1->F1_FORNECE .And. ;
				(cAliasSD1)->D1_LOJA == SF1->F1_LOJA ) }

	EndIf
EndIf

If lContinua .And. l140Altera .And. IntePms() .And. FindFunction("A103RATAFN")
	A103RATAFN(cNFiscal,cSerie,cA100For,cLoja,@aRatAFN,@aHdrAFN)
Endif

If lContinua
	aAdd(aListCpo,"D1_LEGENDA")
	aAdd(aNoFields,"D1_LEGENDA")
	if FWSX3Util():GetFieldType( "D1_ITXML" ) == "C"//remove o campo do item do xml, será usado somente no mata103.
		aAdd(aListCpo,"D1_ITXML")
		aAdd(aNoFields,"D1_ITXML")
	endif
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Sintaxe da FillGetDados(nOpcx,cAlias,nOrder,cSeekKey,bSeekWhile,uSeekFor,aNoFields,aYesFields,lOnlyYes,cQuery,bMontCols,lEmpty,aHeaderAux,aColsAux,bAfterCols,bBeforeCols,bAfterHeader,cAliasQry,bCriaVar,lUserFields) |
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	SetKey( VK_F10, Nil ) //desativa tecla F10 ao exibir Alert
	FillGetDados(nOpcX,"SD1",1,/*cSeek*/,/*{|| &cWhile }*/,{||.T.},aNoFields,aListCpo,/*lOnlyYes*/,/*cQuery*/,{|| MaCols140 (cAliasSD1,bWhileSD1,aRecOrdSD1,@aRecSD1,@aPedC,lItSD1Ord,lQuery,l140Inclui,l140Visual,@lContinua,l140Exclui,l140Altera) },l140Inclui,/*aHeaderAux*/,/*aColsAux*/,/*bAfterCols*/,/*bbeforeCols*/,/*bAfterHeader*/,/*cAliasQry*/,/*bCriaVar*/,.T.,aListCpo)

	nSPed    := GetPosSD1("D1_PEDIDO")
    nSItPed	 := GetPosSD1("D1_ITEMPC")
    nSMed	 := GetPosSD1("D1_ITEMMED")
	nSItem	 := GetPosSD1("D1_ITEM")
    
    If nSPed > 0 .And. nSItPed > 0 .And. nSMed > 0 .And. nSItem > 0 
    	For NX := 1 to len(acols)
            If aCols [NX,nSPed] <> Nil .and. aCols [NX,nSItPed] <> Nil
            	SC7->(DbSetOrder(9)) 
            	SC7->(MsSeek(xFilEnt(xFilial("SC7"),"SC7") + cA100For + cLoja + aCols[NX,nSPed] + aCols[NX,nSItPed]))
                Acols[NX,nSMed] := If( !Empty( SC7->C7_CONTRA ) .And. !Empty( SC7->C7_MEDICAO ), "1", "")
            EndIf

			If ALTERA .And.!Empty(aCols[nX,nSPed])
				aAdd(aPedItAnt,{aCols[nX,nSItem],aCols[nX,nSPed],aCols[nX,nSItPed]}) //Guarda numero do pedido e item antes de apresentar a tela da pre nota na alteração
			EndIf 
        Next NX
     EndIf
            	
	SetKey( VK_F10, { || Eval(bPmsDlgNF)} )
	If lQuery
		dbSelectArea("SD1")
		dbCloseArea()
		ChkFile("SD1")
	EndIf
            
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Ponto de entrada que permite o preenchimento automático dos dados do cabeçalho da pre-nota e define se continua a rotina |
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If l140Inclui
		If ExistBlock("MT140CAB")
			If !ExecBlock("MT140CAB",.F.,.F.)
				lContinua := .F.
			EndIf
		EndIf
	EndIf

	If lContinua
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Calculo do total do pre-documento de entrada                 ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		Ma140Total(a140Total,a140Desp)

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Rotina automatica                                            ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If l140Auto
			nOpcA := 1
			If !l140Exclui
				aValidGet := {}
				If l140Inclui
					If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="COLAB"}))<>0 //TOTVS COLABORACAO
						If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_FORNECE"}))<>0
							cA100For := aAutoCab[nX][2]
						EndIf 
						If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_LOJA"}))<>0
							cLoja := aAutoCab[nX][2]
						EndIf
						If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_SERIE"}))<>0
                            cSerie := aAutoCab[nX][2]
                        EndIf
					EndIf 
					
					PRIVATE aBlock := {	{|| NfeTipo(cTipo,@cA100For,@cLoja)},;
						{|| NfeFormul(cFormul,@cNFiscal,@cSerie)},;
						{|| NfeFornece(cTipo,@cA100For,@cLoja).And.CheckSX3("F1_DOC")},;
						{|| NfeFornece(cTipo,@cA100For,@cLoja).And.CheckSX3("F1_SERIE")},;
						{|| CheckSX3("F1_EMISSAO") .And. NfeEmissao(dDEmissao)},;
						{|| A140VerLoj(@cLoja) .And. NfeFornece(cTipo,@cA100For,@cLoja).And.CheckSX3('F1_FORNECE',cA100For)},;
						{|| NfeFornece(cTipo,@cA100For,@cLoja).And.CheckSX3('F1_LOJA',cLoja)},;
						{|| CheckSX3("F1_ESPECIE",cEspecie)},;
						{|| lIsRussia .Or. CheckSX3("F1_EST",cUfOrigP) .And. CheckSX3("F1_EST",cUfOrigP)},;
						{|| NfeFornece(cTipo,@cA100For,@cLoja).And.CheckSX3("F1_SUBSERI")},;
						{|| A103VldPres()},;
						{|| A103VldA1U()}} 
					If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_TIPO"}))<>0
						aadd(aValidGet,{"cTipo",aAutoCab[(nX),2],"Eval(aBlock[1])",.T.})
					Else
						cTipo := "N"
					EndIf
					If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_FORMUL"}))<>0
						If cPaisLoc == "BRA" .AND. aAutoCab[(nX),2] == "N"
							cFormul := ""
						Else						
							aadd(aValidGet,{"cFormul",aAutoCab[(nX),2],"Eval(aBlock[2])",.T.})
							cFormul := aAutoCab[(nX),2] 
						Endif						
					Else
						cFormul := "N"
					EndIf
			
					nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_SERIE"})
					aadd(aValidGet,{"cSerie",aAutoCab[(nX),2],"Eval(aBlock[4])",.T.})
					cSerie := aAutoCab[(nX),2]

					nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_DOC"})
					//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
					//³ Obtem numero do documento quando utilizar ³
					//³ numeracao pelo SD9 (MV_TPNRNFS = 3)       ³
					//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
					If cTipoNf == "3" .AND. cFormul == "S" .AND. cModulo <> "EIC"
						SX3->(DbSetOrder(1))
						If (SX3->(dbSeek("SD9")))
							// Se cNFiscal estiver vazio, busca numeracao no SD9, senao, respeita o novo numero
							// digitado pelo usuario.
							aAutoCab[nX][2]  :=   MA461NumNf(.T.,cSerie,aAutoCab[nX][2])
						EndIf			
					Endif 
					aadd(aValidGet,{"cNFiscal" ,aAutoCab[(nX),2],"Eval(aBlock[3])",.T.})
					nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_EMISSAO"})
					aadd(aValidGet,{"dDEmissao",aAutoCab[(nX),2],"Eval(aBlock[5])",.T.})
					nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_FORNECE"})
					aadd(aValidGet,{"cA100For",aAutoCab[(nX),2],"Eval(aBlock[6])",.T.})
					nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_LOJA"})
					aadd(aValidGet,{"cLoja",aAutoCab[(nX),2],"Eval(aBlock[7])",.T.})
					If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_ESPECIE"}))<>0
						aadd(aValidGet,{"cEspecie",aAutoCab[(nX),2],"Eval(aBlock[8])",.T.})
					Else
						cEspecie := ""
					EndIf
					If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_EST"}))<>0
						aadd(aValidGet,{"cUfOrigP",aAutoCab[(nX),2],"Eval(aBlock[9])",.T.})
					Else
						cUfOrigP := ""
					EndIf
					If lSubSerie
						If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_SUBSERI"}))<>0
							aAdd(aValidGet,{"cSubSerie",aAutoCab[(nX),2],"Eval(aBlock[10])",.T.})
						EndIf
					EndIf

					If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed 
						If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_INDPRES"}))<>0
							Aadd(aValidGet,{"aInfAdic[16]",aAutoCab[(nX),2],"Eval(aVldBlock[11])",.F.})
							aInfAdic[16] := aAutoCab[(nX),2]

							If cFormul == "S" .And. A103EICTRANS(aAutoCab) .And. Empty(aInfAdic[16])
								aInfAdic[16] := "1"
							Endif
						Else
							If cFormul == "S" .And. A103EICTRANS(aAutoCab)
								aInfAdic[16] := "1"
							Endif
						EndIf 

						If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_CODA1U"}))<>0
							Aadd(aValidGet,{"aInfAdic[17]",aAutoCab[(nX),2],"Eval(aVldBlock[12])",.F.})
							aInfAdic[17] := aAutoCab[(nX),2]
						EndIf
					Endif

					If ! SF1->(MsVldGAuto(aValidGet))
						nOpcA := 0
					EndIf

					//Preenche o tipo de complemento
					If SF1->(ColumnPos("F1_TPCOMPL")) > 0 .And. cTipo == "C" .And. (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_TPCOMPL"}))>0 .And. aAutoCab[nX,2] $ "123"
						cTpCompl := aAutoCab[nX,2]
					EndIf

				EndIf
				If nOpcA <> 0 
					If nMostraTela <> 2
				  		If !SD1->(MsGetDAuto(aAutoItens,"Ma140LinOk",{|| Ma140TudOk()},aAutoCab,aRotina[nOpcX][4]))
				  			nOpcA := 0
				  		EndIf
	        		EndIf
				EndIf
				
				If GetMV("MV_INTPMS",,"N") == "S" .And. GetMV("MV_PMSIPC",,2) == 1 //Se utiliza amarracao automatica dos itens da NFE com o Projeto
					For nX := 1 To Len(aAutoItens)
						If (aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_ITEM"}) == 0)
							If nX == 1
								aAdd(aAutoItens[nX],{"D1_ITEM","000"+AllTrim(Str(nX)),NIL})
							Else
								aAdd(aAutoItens[nX],{"D1_ITEM",Soma1(aAutoItens[nX-1][Len(aAutoItens[nX-1])][2]),Nil})
							EndIf
						EndIf
						PMS140IPC(Val(aAutoItens[nX][aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_ITEM"})][2]))					
					Next nX
				EndIf
				
				If nMostraTela <> 0 .And. nOpca <> 0
					l140Auto := .F.
					nOpca    := 0
					HelpInDark(.F.)
				EndIf
			EndIf
		EndIf

		If lDKD //Tem DKD, verifica se tem campos adicionais para serem apresentados
			lTabAuxD1 := A103DKD(,,l140Altera,l140Visual) //MATA103COM
		Endif

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Interface com o Usuario                                      ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If !l140Auto
			aSizeAut := MsAdvSize(,.F.,400)
			aObjects := {}
			aadd( aObjects, { 0,    41, .T., .F. } )
			aadd( aObjects, { 0, 100, .T., .T. } )
			aadd( aObjects, { 0,    90, .T., .F. } )
			aInfo := { aSizeAut[ 1 ], aSizeAut[ 2 ], aSizeAut[ 3 ], aSizeAut[ 4 ], 3, 3 }
			aPosObj := MsObjSize( aInfo, aObjects )
			aPosGet := MsObjGetPos(aSizeAut[3]-aSizeAut[1],310,;
				{If(lSubSerie,{8,30,72,92,130,150,180,200,235,250,275,295},{8,35,75,100,140,165,194,220,260,280}),;
				If( l140Visual .Or. !lConsMedic,{8,35,75,100,nPosGetLoja,194,220,260,280},{8,35,75,108,145,160,190,220,244,265} ),;
				{5,70,160,205,295},;
				{6,34,200,215},;
				{6,34,75,103,148,164,230,253},;
				{6,34,200,218,280},;
				{11,50,150,190},;
				{273,130,190,293,205},;
				{3, 4}})

			DEFINE MSDIALOG oDlg FROM aSizeAut[7],0 TO aSizeAut[6],aSizeAut[5] TITLE cCadastro Of oMainWnd PIXEL

			NfeCabDoc(oDlg,{aPosGet[1],aPosGet[2],aPosObj[1]},@bCabOk,l140Visual .Or. l140Altera,.F.,@cUfOrigP,,.T.,nil,nil,nil,nil,@lNfMedic,,,,l140Altera)

			If !lDKD .Or. (lDKD .And. !lTabAuxD1)
				oGetDados := MSGetDados():New(aPosObj[2,1],aPosObj[2,2],aPosObj[2,3],aPosObj[2,4],nOpcX,"Ma140LinOk","Ma140TudOk","+D1_ITEM",!l140Visual,,,,9999,"A140FldOk",,,"Ma140DelIt")
			Else
				oGetDados := MSGetDados():New(aPosObj[2,1],aPosObj[2,2],aPosObj[2,3]-50,aPosObj[2,4],nOpcX,"Ma140LinOk","Ma140TudOk","+D1_ITEM",!l140Visual,,,,9999,"A140FldOk",,,"Ma140DelIt")

				oGetDKD		:= MsNewGetDados():New(aPosObj[2,3]-50,aPosObj[2,2],aPosObj[2,3],aPosObj[2,4],Iif(nOpcx == 2,0,GD_UPDATE),/*"LinhaOk"*/"",/*TudoOk*/"","+DKD_ITEM",aAltDKD,/*freeze*/,1,/*fieldok*/,/*superdel*/,/*"LancDel("+cVisual+")*/"",oDlg,aHeadDKD,aColsDKD)
				If l140Altera .Or. Len(aAutoDKD) > 0 .Or. l140Visual
					A103DKDATU(1)
				Endif
			Endif
			oGetDados:oBrowse:bGotFocus	:= bCabOk
			oGetDados:oBrowse:bChange := {|| Iif(lDKD .And. lTabAuxD1,A103DKDATU(),.T.) }

			oFolder := TFolder():New(aPosObj[3,1],aPosObj[3,2],aTitles,{"HEADER"},oDlg,,,, .T., .F.,aPosObj[3,4]-aPosObj[3,2],aPosObj[3,3]-aPosObj[3,1],)
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Folder dos Totalizadores                                     ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			oFolder:aDialogs[1]:oFont := oDlg:oFont
			NfeFldTot(oFolder:aDialogs[1],a140Total,aPosGet[3],@aFldCBAtu[1])
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Folder dos Fornecedores                                      ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			oFolder:aDialogs[2]:oFont := oDlg:oFont
			oFolder:bSetOption := {|nDst| NfeFldChg(nDst,oFolder:nOption,oFolder,aFldCBAtu)}
			NfeFldFor(oFolder:aDialogs[2],aInfForn,{aPosGet[4],aPosGet[5],aPosGet[6]},@aFldCBAtu[2])
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Folder das Despesas acessorias e descontos                   ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			oFolder:aDialogs[3]:oFont := oDlg:oFont
			NfeFldDsp(oFolder:aDialogs[3],a140Desp,{aPosGet[7],aPosGet[8]},@aFldCBAtu[3])

			If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
				oFolder:aDialogs[nFldInter]:oFont := oDlg:oFont
				NfeFldAdic(oFolder:aDialogs[nFldInter],{aPosGet[9]},aInfAdic,,,l140Visual,.F.,@aFldCBAtu[4],.T.)
			Endif

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Folder de conferencia para os coletores                      ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If cPaisLoc == "BRA"
			If l140Visual .And. UsaConfF(cTipo, cA100For, cLoja) .And. Len(aTitles) > 3
				oFolder:aDialogs[4]:oFont := oDlg:oFont
				Do Case
				Case SF1->F1_STATCON $ "1 "
					cStatCon := STR0014 //"NF conferida"
				Case SF1->F1_STATCON == "0"
					cStatCon := STR0015 //"NF nao conferida"
				Case SF1->F1_STATCON == "2"
					cStatCon := STR0016 //"NF com divergencia"
				Case SF1->F1_STATCON == "3"
					cStatCon := STR0017 //"NF em conferencia"
				Case SF1->F1_STATCON == "4"
					cStatCon := "NF Clas. C/ Diver." 
				EndCase
				nQtdConf := SF1->F1_QTDCONF
				@ 06 ,aPosGet[6,1] SAY STR0018      OF oFolder:aDialogs[4] PIXEL SIZE 49,09 //"Status"
				@ 05 ,aPosGet[6,2] MSGET oStatCon VAR Upper(cStatCon) COLOR CLR_RED OF oFolder:aDialogs[4] PIXEL SIZE 70,9 When .F.
				@ 25 ,aPosGet[6,1] SAY STR0019 OF oFolder:aDialogs[4] PIXEL SIZE 49,09 //"Conferentes"
				@ 24 ,aPosGet[6,2] MSGET oConf Var nQtdConf OF oFolder:aDialogs[4] PIXEL SIZE 70,09 When .F.
				@ 05 ,aPosGet[5,3] LISTBOX oList Fields HEADER "  ",STR0020,STR0021 SIZE 170, 48 OF oFolder:aDialogs[4] PIXEL //"Codigo"###"Quantidade Conferida"
				oList:BLDblclick := {||A140DetCon(oList,aListBox)}

				DEFINE TIMER oTimer INTERVAL 3000 ACTION (A140AtuCon(oList,aListBox,oEnable,oDisable,oConf,@nQtdConf,oStatCon,@cStatCon,,oTimer)) OF oDlg
				oTimer:Activate()

				@ 30 ,aPosGet[5,3]+180 BUTTON STR0022 SIZE 40 ,11  FONT oDlg:oFont ACTION (A140AtuCon(oList,aListBox,oEnable,oDisable,oConf,@nQtdConf,oStatCon,@cStatCon,.T.,oTimer)) OF oFolder:aDialogs[4] PIXEL When SF1->F1_STATCON == '2' //"Recontagem"
				@ 42 ,aPosGet[5,3]+180 BUTTON STR0023 SIZE 40 ,11  FONT oDlg:oFont ACTION (A140DetCon(oList,aListBox)) OF oFolder:aDialogs[4] PIXEL //"Detalhes"

				A140AtuCon(oList,aListBox,oEnable,oDisable)
			EndIf
		EndIf
			If nMostraTela <> 0 
				Eval(bRefresh)
			EndIf
			ACTIVATE MSDIALOG oDlg ON INIT Ma140Bar(oDlg,{||If(oGetDados:TudoOk().And.NfeNextDoc(@cNFiscal,@cSerie,l140Inclui) .And. A140ATUFRT(1,l140Altera),(nOpcA:=1,oDlg:End()),nOpcA:=0)},{||FreeUsedcode(.T.),oDlg:End()},IIF(l140Visual,aButVisual,aButtons))						
		EndIf 
		
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//  FSW - 05/05/2011 - Rotina Exclui Divergencias
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
        If lMvNfeDvg .And. l140Exclui
           If Empty(SF1->F1_STATUS)
         	  CA040EXC()
           EndIf         
        EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Integracao com o ACD			  				  ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If l140Exclui .And. lIntACD
			nOpcA := IIF(CBA140EXC(),nOpcA,0)
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Template acionando Ponto de Entrada                  ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		ElseIf l140Exclui .And. nOpcA == 1 .And. ExistTemplate("A140EXC")
			nOpcA := IIF(ExecTemplate("A140EXC",.F.,.F.),nOpcA,0)
			If valtype(nOpcA)!= "N" 
			  	nOpcA := 1
			EndIf
		EndIf
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Ponto de entrada para validar a exclusao de um pre-documento ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If l140Exclui .And. nOpcA == 1 .And. ExistBlock("A140EXC")
			nOpcA := IIF(ExecBlock("A140EXC",.F.,.F.),nOpcA,0)
			If valtype(nOpcA)!= "N" 
			  	nOpcA := 1
			EndIf
		EndIf     
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Exclui os registro da CBE (Conferencia)	- ACD     ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If l140Exclui .And. lIntACD .And. FindFunction("EstCBED1")
			EstCBED1(cNFiscal,cSerie,cA100For,cLoja)
		EndIf
		//FSW - Fazer ponto de entrada para validacao da inclusao da pre nota
		If (l140Inclui .OR. l140Altera) .And. nOpcA == 1 .AND. ExistBlock("CM120GR")
		   nOpcA := ExecBlock("CM120GR",.F.,.F.,{nOpcA})
			   If valtype(nOpcA)!= "N" 
			   		nOpcA := 1
			   	EndIf	
		EndIf
		
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Atualizacao do pre-documento de entrada                      ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If nOpcA == 1 .AND. ( l140Inclui .OR. l140Altera .OR. l140Exclui ) .AND. ( Type( "lOnUpDate" ) == "U" .OR. lOnUpdate )
			Ma140Grava( l140Exclui, aRecSD1, a140Desp, nSaveSX8, l140Inclui, l140Altera,,,aPedItAnt)
		ElseIf l140Auto
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_FILIAL" } ) ) > 0
				aAutoCab[nPos][2] := xFilial( "SF1" )
			Else
				AAdd( aAutoCab, { "F1_FILIAL", xFilial( "SF1" ), NIL } )
			Endif

			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_DOC" } ) ) > 0
				aAutoCab[nPos][2] := cNFiscal
			Else
				AAdd( aAutoCab, { "F1_DOC", cNFiscal, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_SERIE" } ) ) > 0
				aAutoCab[nPos][2] := cSerie
			Else
				AAdd( aAutoCab, { "F1_SERIE", cSerie, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_FORNECE" } ) ) > 0
				aAutoCab[nPos][2] := cA100For
			Else
				AAdd( aAutoCab, { "F1_FORNECE", cA100For, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_LOJA" } ) ) > 0
				aAutoCab[nPos][2] := cLoja
			Else
				AAdd( aAutoCab, { "F1_LOJA", cLoja, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_EMISSAO" } ) ) > 0
				aAutoCab[nPos][2] := dDEmissao
			Else
				AAdd( aAutoCab, { "F1_EMISSAO", dDEmissao, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_EST" } ) ) > 0
				aAutoCab[nPos][2] := IIF( cTipo $ "DB", SA1->A1_EST, SA2->A2_EST )
			Else
				AAdd( aAutoCab, { "F1_EST", IIF( cTipo $ "DB", SA1->A1_EST, SA2->A2_EST ), NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_TIPO" } ) ) > 0
				aAutoCab[nPos][2] := cTipo
			Else
				AAdd( aAutoCab, { "F1_TIPO", cTipo, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_DTDIGIT" } ) ) > 0
				aAutoCab[nPos][2] := dDataBase
			Else
				AAdd( aAutoCab, { "F1_DTDIGIT", dDataBase, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_RECBMTO" } ) ) > 0
				aAutoCab[nPos][2] := SF1->F1_DTDIGIT
			Else
				AAdd( aAutoCab, { "F1_RECBMTO", SF1->F1_DTDIGIT	, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_FORMUL" } ) ) > 0
				aAutoCab[nPos][2] := IIF( cFormul == "S", "S", " " )
			Else
				AAdd( aAutoCab, { "F1_FORMUL", IIF( cFormul == "S", "S", " " ), NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_ESPECIE" } ) ) > 0
				aAutoCab[nPos][2] := cEspecie
			Else
				AAdd( aAutoCab, { "F1_ESPECIE", cEspecie, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_DESPESA" } ) ) > 0
				aAutoCab[nPos][2] := a140Desp[VALDESP]
			Else
				AAdd( aAutoCab, { "F1_DESPESA", a140Desp[VALDESP], NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_FRETE" } ) ) > 0
				aAutoCab[nPos][2] := a140Desp[FRETE]
			Else
				AAdd( aAutoCab, { "F1_FRETE", a140Desp[FRETE], NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_SEGURO" } ) ) > 0
				aAutoCab[nPos][2] := a140Desp[SEGURO]
			Else
				AAdd( aAutoCab, { "F1_SEGURO", a140Desp[SEGURO]	, NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_VALMERC" } ) ) > 0
				aAutoCab[nPos][2] := a140Total[VALMERC]
			Else
				AAdd( aAutoCab, { "F1_VALMERC", a140Total[VALMERC], NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_DESCONT" } ) ) > 0
				aAutoCab[nPos][2] := a140Total[VALDESC]
			Else
				AAdd( aAutoCab, { "F1_DESCONT", a140Total[VALDESC], NIL } )
			Endif
	
			If ( nPos := AScan( aAutoCab, { |x| x[1] == "F1_VALBRUT" } ) ) > 0
				aAutoCab[nPos][2] := a140Total[TOTPED]
			Else
				AAdd( aAutoCab, { "F1_VALBRUT", a140Total[TOTPED], NIL } )
			Endif
	
			aAutoItens := MsAuto2Gd( aHeader, aCols )
		EndIf
	EndIf
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Destrava os registros na alteracao e exclusao                ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
MsUnlockAll()
If !l140Auto .And. lContinua
	SetKey( VK_F5, Nil )
	SetKey( VK_F6, Nil )
	SetKey( VK_F10, Nil )
ElseIf !lContinua
	SetKey( VK_F10, Nil )
EndIf
If  Type("_aDivPNF") != "U"
	_aDivPNF := {}
Endif   

If lContinua 
	If lIntGC // Modulos do DMS
		If FindFunction("OA2900031_A140NFiscal_AposOK")
			lContinua := OA2900031_A140NFiscal_AposOK( { aRotina[nOpcX,4] , nOpcA , cNFiscal , cSerie , cA100For , cLoja , cTipo } ) // Apos OK no MATA140
		EndIf
	EndIf
EndIf

If lContinua .And. ExistTemplate( "MT140SAI" )
	ExecTemplate( "MT140SAI", .F., .F., { aRotina[ nOpcx, 4 ], cNFiscal, cSerie, cA100For, cLoja, cTipo, nOpcA } )
EndIf

If lContinua .And. lIntPFS .And. l140Exclui .And. FindFunction("J281ExcDoc")
	J281ExcDoc()
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ O ponto de entrada e disparado apos o RestArea pois pode ser utilizado para posicionar o Browse ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lContinua .And. ExistBlock( "MT140SAI" )
	ExecBlock( "MT140SAI", .F., .F., { aRotina[ nOpcx, 4 ], cNFiscal, cSerie, cA100For, cLoja, cTipo, nOpcA } )
EndIf

Return lContinua

//*------------------------------------------------------------------------//
//Programa:		A140VerLoj 
//Autor:		Ricardo Prandi	         
//Data:			08/05/2017	
//Descricao:	Atualiza o campo Loja quando for rotina automática
//Parametros:	cLoja: Código da Loja, por referência	
//Uso: 			MATA140
//------------------------------------------------------------------------*/
Function A140VerLoj(cLoja)

Local Nx := 1

If (nX := aScan(aAutoCab,{|x| AllTrim(Upper(x[1]))=="F1_LOJA"})) <> 0
	cLoja := aAutoCab[nX][2]
EndIf 

Return .T.

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³Ma140LinOk³ Autor ³ Eduardo Riera         ³ Data ³02.10.2002 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³Validacao da Getdados - LinhaOk                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpO1: Objeto da getdados                                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL1: Indica se a linha digitada eh valida                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Esta rotina tem como objetivo validar um item do pre-documen-³±±
±±³          ³to de entrada                                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Materiais                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function Ma140LinOk()

Local aArea			:= GetArea()
Local lRetorno		:= .T.
Local nPosItemNF	:= GetPosSD1("D1_ITEM")
Local nPosCod		:= GetPosSD1("D1_COD")
Local nPosLocal		:= GetPosSD1("D1_LOCAL")
Local nPosQuant		:= GetPosSD1("D1_QUANT")
Local nPosVUnit		:= GetPosSD1("D1_VUNIT")
Local nPosTotal		:= GetPosSD1("D1_TOTAL")
Local nPosPC		:= GetPosSD1("D1_PEDIDO")
Local nPosItemPC	:= GetPosSD1("D1_ITEMPC")
Local nPosLoteCtl	:= GetPosSD1("D1_LOTECTL")
Local nPosLote   	:= GetPosSD1("D1_NUMLOTE")
Local nPosValDes   	:= GetPosSD1("D1_VALDESC")
Local nPosNFOri		:= GetPosSD1("D1_NFORI")
Local nPosSerOri	:= GetPosSD1("D1_SERIORI")
Local nPosItmOri	:= GetPosSD1("D1_ITEMORI")
Local lPCNFE		:= GetNewPar( "MV_PCNFE", .F. ) //-- Nota Fiscal tem que ser amarrada a um Pedido de Compra ?
Local nPosServic	:= GetPosSD1('D1_SERVIC')
Local lMT140PC
Local nPosOp     	:= GetPosSD1("D1_OP")
Local nA			:= 0
Local lColab 		:= l140Auto .And. !Empty(aAutoCab) .And. aScan(aAutoCab, {|x| x[1] == "COLAB" .And. x[2] == "S"}) > 0
Local lNotaFilha  	:= l140Auto .And. !Empty(aAutoCab) .And. aScan(aAutoCab, {|x| x[1] == "F1_TIPO_NF" .And. x[2] == "6"}) > 0
Local lNotaDespImp	:= l140Auto .And. !Empty(aAutoCab) .And. aScan(aAutoCab, {|x| x[1] == "F1_TIPO_NF" .And. x[2] == "0"}) > 0
Local lGFEA065		:= FwIsInCallStack("GFEA065")
Local lEASY			:= SuperGetMV("MV_EASY",,"N") == "S"
Local lATFA060		:= FwIsInCallStack("ATFA060")
Local nRndLoc		:= SuperGetMV("MV_RNDLOC",.F.,2)
Local lF1TPCompl	:= SF1->(ColumnPos("F1_TPCOMPL")) > 0
Local lIntPMS		:= IntePms()
Local lProcDocs		:= FwIsInCallStack("PROCDOCS")
Local lDifAFN		:= SuperGetMV("MV_DIFAFN",,.T.)
Local lIntWMS		:= IntWMS()
Local dDTULMES 		:= CTOD("") //Data do Ultimo Fechamento do Estoque
Local lNGMNTES		:= SuperGetMV("MV_NGMNTES",.F.,"N") == "S"
Local lNGMNTPC		:= SuperGetMV("MV_NGMNTPC",.F.,"N") == "S"
Local nLinAtv		:= 0 
Local nLinAtu		:= 0
Local lDtNT2006		:= A103DNT2006()
Local lValGat		:= .F.
Local aD1Area       := {}

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica a permissao do armazem. ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
lRetorno := MaAvalPerm(3,{aCols[n][nPosLocal],aCols[n][nPosCod]})

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Ponto de Entrada para o tratamento do parâmetro MV_PCNFE (Nota Fiscal tem que ser amarrada a um Pedido de Compra ?)      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lRetorno .And. (ExistBlock("MT140PC"))  
	lMT140PC  := ExecBlock("MT140PC",.F.,.F.,{lPCNFE})    
	If ( ValType(lMT140PC ) == 'L' )
		lPCNFE := lMT140PC 
	EndIf
EndIf     

If lRetorno .And. IsProdMOD(aCols[n][nPosCod])
	Help("  ",1,"NAOMVMOD")//"Produtos de Mão-de-Obra não podem ser utilizados para esta operação."
	lRetorno := .F.
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica se e rotina automatica do TOTVS Colaboracao      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If l140Auto .And. Type("aAutoCab") == "A"
	nPosColab := aScan(aAutoCab,{|x| AllTrim(x[1])=="COLAB"})
EndIf

If lRetorno
	aD1Area := SD1->(GetArea())
	dbSelectArea("SD1")
       dbSetOrder(1)
       MsSeek(xFilial("SD1")+CNFISCAL+cSerie+cA100For+cLoja+aCols[n][nPosCod]+aCols[n][nPosItemNF])
       If aCols[n][nPosQuant] <> SD1->D1_QUANT  .Or. ;
          aCols[n][nPosVUnit] <> SD1->D1_VUNIT .Or. ;		  
          aCols[n][nPosLocal] <> SD1->D1_LOCAL
		If !ExistCpo("NNR",aCols[n][nPosLocal])
			lRetorno := .F.
		EndIf
	EndIf
	RestArea(aD1Area)
EndIf

If lRetorno .And. cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. cFormul == "S" .And. lDtNT2006
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
		If cTipo <> "N"
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
	Eval(bRefresh)
Endif

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica preenchimento dos campos da linha do acols      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lRetorno .And. CheckCols(n,aCols)
	If !aCols[n][Len(aCols[n])]
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Quando Informado Armazem em branco considerar o B1_LOCPAD   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If Empty(aCols[n][nPosLocal])
			SB1->(dbSetOrder(1))
				If SB1->(MsSeek(xFilial("SB1")+aCols[n][nPosCod])) 
				aCols[n][nPosLocal] := SB1->B1_LOCPAD
				If Type("l140Auto") <> "U" .And. !l140Auto
					Aviso(OemToAnsi(STR0035),OemToAnsi(STR0053),{"Ok"}) //Atencao##O Armazem informado e Invalido, o campo sera ajustando com o armazem padrão do cadastro de produtos
				EndIf	
			EndIf
		EndIf
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica se o produto est  sendo inventariado.      ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		Do Case
		Case Empty(aCols[n][nPosCod]) .Or. ;
				If(lColab,.F.,(Empty(aCols[n][nPosQuant]).And.cTipo$"NDB")).Or. ;
				If(lColab,.F.,Empty(aCols[n][nPosVUnit])) .Or. ;
				If(lColab,.F.,Empty(aCols[n][nPosTotal]))
			Help("  ",1,"A140VZ") 
			lRetorno := .F.			
		Case nPosPC > 0 .And. !Empty(aCols[n][nPosPc]) .And. Empty(aCols[n][nPosItemPC])
			Help("  ",1,"A140PC")
			lRetorno := .F.			
		Case cPaisLoc <> "BRA".AND.cTipo <> "C" .And.;
				Round(aCols[n][nPosVUnit]*aCols[n][nPosQuant],nRndLoc) <> Round(aCols[n][nPosTotal],nRndLoc)
			HELP(" ",1,"A100Valor")
			lRetorno := .F.			
		Case cTipo$'NDB' .And. (aCols[n][nPosTotal]>(aCols[n][nPosVUnit]*aCols[n][nPosQuant]+0.49);
		                   .Or. aCols[n][nPosTotal]<(aCols[n][nPosVUnit]*aCols[n][nPosQuant]-0.49))
			Help("  ",1,'TOTAL') 
			lRetorno := .F.			
		Case !A103Alert(Acols[n][nPosCod],aCols[n][nPosLocal],l140Auto)
			lRetorno := .F.
		Case cTipo = 'N' .And. lPCNFE	 .And. Empty(aCols[n,nPosPC])
			If l140Auto .And. lGFEA065 // Quando originado pela programa GFEA065, não valida o parametro MV_PCNFE
				lRetorno := .T.
			ElseIf l140Auto .And. IsTransFil()   // Quando for Rotina Automatica e Transf.Filiais, ignora parametro pedido de compras 
  		       lRetorno := .T.
  		    ElseIf l140Auto .And. lEASY .And. (lNotaFilha .Or. lNotaDespImp)  // Quando for SIGAEIC não valida o parametro MV_PCNFE quando for nota fiscal de remessa (nota filha) ou nota fiscal de despesa de importação
  		       lRetorno := .T.
  		    ElseIf l140Auto .And. lATFA060  // Quando for transferência DO ATFA060 não valida o parametro MV_PCNFE
  		       lRetorno := .T.			
  		    ElseIf l140auto .And. (nPosCfop := aScan(aAutoItens[n],{|x|AllTrim(x[1])=="CFOP"}))>0
  		    	If AllTrim (aAutoItens[n,nPosCfop,2]) == 'N' 
			   		lRetorno := .F.
  		    	EndIf 
  		    Else 
			   lRetorno := .F.
		    EndIf
			If ! lRetorno
				Aviso(OemToAnsi(STR0035),OemToAnsi(STR0036),{OemToAnsi(STR0037)}, 2 ) //-- "Atencao"###"Informe o No. do Pedido de Compras ou verifique o conteudo do parametro MV_PCNFE"###"Ok"
			EndIf	
		Case nPosCod>0 .And. nPosLoteCtl>0 .And. nPosLote>0 .And. (Rastro(aCols[n][nPosCod],"N")) .And. (!Empty(aCols[n][nPosLoteCtl]) .Or. !Empty(aCols[n][nPosLote]))
			Help(" ",1,"NAORASTRO")
			lRetorno := .F.		
		Case nPosCod > 0 .And. SB1->(MsSeek(xFilial("SB1")+aCols[n][nPosCod])) // Verifica se o produto está bloqueado
			If !RegistroOk("SB1")
				lRetorno := .F.
			EndIf
		OtherWise
			lRetorno := .T.
		EndCase

		//E obrigatorio o preenchimento da quantidade para notas do tipo Complemento de Preco
		If lF1TPCompl .And. cTipo == "C" .And. cTpCompl == "2"
			If Empty(aCols[n][nPosQuant])
				Help(" ",1,"COMPQTD",,STR0080,1,0) // Este texto pode ser retirado a partir do release 12.1.16
				lRetorno := .F.
			EndIf
		EndIf

		//Verifica se o valor do desconto é maior que o valor total do item.
		If lRetorno .And. nPosTotal > 0 .And. nPosValDes > 0 
			If aCols[n][nPosTotal] < aCols[n][nPosValDes]
				Help(" ",1,"A100VALDES")
			    lRetorno := .F.
			EndIf
		EndIf
		
		// Valida qtde com a Integracao PMS
		If lRetorno .And. lIntPMS .And. Len(aRatAFN)>0 .And. !lProcDocs
			If Len(aHdrAFN) == 0
				aHdrAFN := FilHdrAFN()
			Endif
			nPosAFN  := Ascan(aRatAFN,{|x|x[1]==aCols[n][nPosItemNF]})
			nPosQtde := Ascan(aHdrAFN,{|x|Alltrim(x[2])=="AFN_QUANT"})
			nTotAFN	:= 0
			
			nPPed := GetPosSD1("D1_PEDIDO")
			nPItP := GetPosSD1("D1_ITEMPC")

			If (nPosAFN > 0) .And. (nPosQtde > 0)
				For nA := 1 To Len(aRatAfn[nPosAFN][2])
					If !aRatAFN[nPosAFN][2][nA][LEN(aRatAFN[nPosAFN][2][nA])]
						nTotAFN	+= aRatAfn[nPosAFN][2][nA][nPosQtde]
					EndIf
				Next nA
				If nPosQuant>0 
					If !lDifAFN
						If nPPed > 0 .And. nPItP > 0
							If !PMSNFSA(aCols[n][nPPed],aCols[n][nPItP])[1]
								If nTotAFN > 0 .AND. nTotAFN <> aCols[n][nPosQuant]
									Help("   ",1,"DIFAFN")
									lRetorno := .F.
								EndIf
							Endif
						Endif
					Else
						If nPPed > 0 .And. nPItP > 0
							If !PMSNFSA(aCols[n][nPPed],aCols[n][nPItP])[1]
								If	nTotAFN > aCols[n][nPosQuant]
									Help("   ",1,"PMSQTNF")
									lRetorno := .F.
								EndIf
							EndIf
						Endif
					Endif
				Endif					
			Endif
		Endif
		
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Valida o preenchimento dos campos referentes ao WMS             ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If lRetorno .And. lIntWMS .And. nPosServic > 0 .And. !Empty(aCols[n, nPosServic])
			lRetorno := WmsAvalSD1("1","SD1",aCols,n,aHeader,/*lPreNota*/.T.)
		EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica se Produto x Fornecedor foi Bloquedo pela Qualidade.   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If lRetorno
			lRetorno := QieSitFornec(cA100For,cLoja,aCols[n][nPosCod],.T.)
		EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica se Ordem de Produção está encerrada   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If lRetorno
			If !Empty(aCols[n][nPosOp]) .And. (!SC2->(dbSeek(xFilial("SC2")+aCols[n][nPosOp])) .Or. !Empty(SC2->C2_DATRF))
				lRetorno := .F.
			EndIf
			
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Integracao com SIGAMNT - NG Informatica             ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			SC2->(dbSetOrder(1))
			If SC2->(dbSeek(xFilial("SC2")+aCols[n][nPosOp])) .And. !Empty(SC2->C2_DATRF)
				If lNGMNTES .And. lNGMNTPC .And. !Empty(aCols[n][nPosOp])
					lRetorno := .T.
					
					dDTULMES := SuperGetMV("MV_ULMES",.F.,CTOD(""))
					If !Empty(dDTULMES) .and. SC2->C2_DATRF <= dDTULMES
						lRetorno := .F.
					EndIf
				EndIf
			EndIf
			
			If !lRetorno
				Help(" ",1,"A100OPEND")
			EndIf
		EndIf

	Else
		lRetorno := .T.
	EndIf
Else
	lRetorno := .F.
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Refresh do rodape do pre-documento de entrada            ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

If "A140DespGat()" $ GetSx3Cache("D1_VALFRE","X3_VALID") .AND. "A140DespGat()" $ GetSx3Cache("D1_SEGURO","X3_VALID") .AND. "A140DespGat()" $ GetSx3Cache("D1_DESPESA","X3_VALID") .AND. "A140DespGat()" $ GetSx3Cache("D1_VALDESC","X3_VALID")
	lValGat := .T.
endif

If !lValGat 
	Eval(bRefresh)
Endif
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Executa os pontos de entrada da Linha Ok                 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lRetorno .And. ExistTemplate("MT140LOK")
	lRetorno := ExecTemplate("MT140LOK",.F.,.F.,{lRetorno,a140Total,a140Desp})
EndIf

If lRetorno .And. ExistBlock("MT140LOK")
	lRetorno := ExecBlock("MT140LOK",.F.,.F.,{lRetorno,a140Total,a140Desp})
EndIf

RestArea(aArea)
Return lRetorno
/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³Ma140TudOk³ Autor ³ Eduardo Riera         ³ Data ³02.10.2002 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³Validacao da Getdados - TudoOk                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpO1: Objeto da getdados                                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL1: Indica se todos os itens sao validos                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Esta rotina tem como objetivo validar todos os itens do pre- ³±±
±±³          ³-documento de entrada                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Materiais                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function MA140Tudok()

Local lRetorno     := .T.
Local lTudoDel     := .T.
Local nX           := 0   
Local nPosMed      := GetPosSD1( "D1_ITEMMED" ) 
Local nK		   := 0
Local nY		   := 0
Local nI		   := 0
Local lItensMed    := .F. 
Local lItensNaoMed := .F.                
Local aMT140GCT    := {}
Local aDocEmp	   := {}
Local nPos         := 0
Local lDtNT2006	   := A103DNT2006()  
Local nPLocal 	   := GetPosSD1("D1_LOCAL")

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica preenchimento dos campos do cabecalho           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If Empty(ca100For) .Or. Empty(dDEmissao) .Or. Empty(cTipo) .Or. (Empty(cNFiscal).And.cFormul!="S")
	Help(" ",1,"A100FALTA")
	lRetorno := .F.
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica se NF já existe na base					        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ 
If Inclui .AND. lRetorno
	dbSelectArea("SF1")
	dbSetOrder(1)
	If SF1->(dbSeek(xFilial("SF1")+cNFiscal+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja+cTipo))
		Help(" ",1,"A140EXISTE")
		lRetorno := .F.
	EndIf
EndIf

If lRetorno .And. cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. cFormul == "S" .And. lDtNT2006
	lRetorno := A103VldObr(,.T.) 

	If lRetorno
		If SubStr(aInfAdic[16],1,1) $ "0|5" .And. !Empty(aInfAdic[17])
			Help(" ",1,"A140INTA1U",,STR0085 + RetTitle("F1_CODA1U"),1,0)
			lRetorno := .F.
		Endif
	Endif
Endif

If lRetorno
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica se existem itens a serem gravados               ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	For nX :=1 to Len(aCols)
		If !aCols[nX][Len(aCols[nX])]
			lTudoDel := .F.    

			If !ExistCpo("NNR",aCols[nx][nPLocal])
				lRetorno := .F. 		
				Exit
			Endif
	
			If nPosMed > 0 .and. !Empty( aCols[ nX, nPosMed ] ) 		
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Verifica a existencia de itens de medicao junto com itens sem medicao               ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				lItensMed    := lItensMed .Or. aCols[ nX, nPosMed ] == "1" 
				lItensNaoMed := lItensNaoMed .Or. aCols[ nX, nPosMed ] $ " |2"
	
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Ponto de entrada permite incluir itens não-pertinentes ao gct ou não.               ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If (ExistBlock("MT140GCT"))
					aMT140GCT := ExecBlock("MT140GCT",.F.,.F.,{aCols,nX,nPosMed}) 
					
					If ValType(aMT140GCT) == "A" 
						If Len(aMT140GCT) >= 1 .And. ValType(aMT140GCT[1]) == "L"
							lItensMed    := aMT140GCT[1]
						EndIf
						If Len(aMT140GCT) >= 2 .And. ValType(aMT140GCT[2]) == "L" 
							lItensNaoMed := aMT140GCT[2]
						EndIf	 
					EndIf  
				EndIf	  
				
				If lItensMed .And. lItensNaoMed
					Help( " ", 1, "A103MEDIC" ) 
					lRetorno := .F. 		
					Exit
				EndIf 

			EndIf 	
		
		Endif
	Next nX
	If lTudoDel
		Help(" ",1,"A140TUDDEL")
		lRetorno := .F.
	EndIf
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Chamada do Ponto de entrada para validacao da TudoOk     ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If lRetorno .And. ExistBlock("MT140TOK")
		lRetorno := ExecBlock("MT140TOK",.F.,.F.,{lRetorno})
	EndIf

	If lRetorno .And. SuperGetMV("MV_NOTAEMP",.F.,.F.)
 		A103DocEmp(aCols,@aDocEmp,.T.)
 		If Len(aDocEmp) > 0
 			lRetorno := ShowDivNe(aDocEmp,l140Auto)
		EndIf 				
	EndIf

EndIf

//Valida a quantidade informada no item com a quantidade informada no rateio do projeto
If lRetorno
	//Valida se utiliza o parametro MV_INTPMS e se possui integração TOP x PROTHEUS
	If IntePms() .And. IsIntegTop(,.T.)
		For nI := 1 To Len(aCols)
			If !aCols[nI,Len(aHeader)+1]
				nQtdRat := 0
				For nK := 1 To Len(aRatAFN)
					If aRatAFN[nK,1] == aCols[nI,GetPosSD1("D1_ITEM")]
						nPos := nK
						For nY := 1 To Len(aRatAFN[nK,2])
							If !aRatAFN[nK,2,nY,Len(aRatAFN[nK,2,nY])]
								nQtdRat += aRatAFN[nK,2,nY,3]
							Endif
						Next nY
					Endif
				Next nK
				
				//Somente valida se tiver rateio de projeto
				If nPos > 0 .And. Len(aRatAFN[nPos,2]) > 0
					If aCols[nI,GetPosSD1("D1_QUANT")] <> nQtdRat
						lRetorno := .F.
						MsgAlert(STR0072 + AllTrim(aCols[nI,GetPosSD1("D1_ITEM")]) + STR0073 + CRLF +; //"A quantidade informada na item: "--" é diferente da informada no rateio de projeto"
								STR0074 + AllTrim(Str(aCols[nI,GetPosSD1("D1_QUANT")])) + CRLF + ; //"Quantidade no item: "
								STR0075 + AllTrim(Str(nQtdRat))) //"Quantidade no rateio do projeto: "
						Exit
					Endif
				Endif
			Endif
		Next nI
	Endif
Endif

//verificacao SIGAPLS
if lRetorno .and. lPLSMT103
	lRetorno := PLSMT103(1, aHeader, aCols)
endIf

If lRetorno .And. (type("lDKD") == "L" .and. lDKD) .And. (type("lTabAuxD1") == "L" .and. lTabAuxD1)
	//Atualiza aColsDKD
	A103DKDATU() 
Endif

Return lRetorno
/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³Ma140Bar  ³ Prog. ³ Sergio Silveira       ³Data  ³ 23/02/2001³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³ Construcao da EnchoiceBar do pre-documento de entrada       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpO1 = Objeto dialog                                       ³±±
±±³          ³ ExpB2 = Code block de confirma                              ³±±
±±³          ³ ExpB3 = Code block de cancela                               ³±±
±±³          ³ ExpA4 = Array com botoes ja incluidos.                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ Devolve o retorno da enchoicebar                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Esta rotina tem como objetivo criar a barra de botoes denomi-³±±
±±³          ³nada EnchoiceBar                                             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Materiais                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function Ma140Bar(oDlg,bOk,bCancel,aButtonsAtu)

Local aUsButtons := {}
Local lMvNfeDvg := SuperGetMV("MV_NFEDVG", .F., .T.)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//  FSW - 05/05/2011 - Implementa no menu da EnchoiceBar 
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lMvNfeDvg
	aadd(aButtonsAtu,{"BUDGET",{|| _MA140Div1()},STR0068,STR0069})//"Cadastro de Divergências", "Divergências"
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Adiciona botoes do usuario na EnchoiceBar                              ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ExistBlock( "MA140BUT" )
	If ValType( aUsButtons := ExecBlock( "MA140BUT", .F., .F. ) ) == "A"
		AEval( aUsButtons, { |x| aadd( aButtonsAtu, x ) } )
	EndIf
EndIf

Return (EnchoiceBar(oDlg,bOK,bcancel,,aButtonsAtu))

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³Ma140Total³ Prog. ³ Sergio Silveira       ³Data  ³ 23/02/2001³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³ Calculo do total do pre-documento de entrada                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpA1: Array com os totais do pre-documento de entrada      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Esta rotina tem como objetivo calcular os totais do pre-docum³±±
±±³          ³ento de entrada                                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Materiais                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function Ma140Total(aTotal,aDespesa, nTotal, nValDesc)

Local nUsado   := Len(aHeader)
Local nMaxFor  := Len(aCols)
Local lDeleted := .F.
Local nPTotal  := GetPosSD1("D1_TOTAL")
Local nPValDesc:= GetPosSD1("D1_VALDESC")
Local nPValFret:= GetPosSD1("D1_VALFRE")
Local nPValDesp:= GetPosSD1("D1_DESPESA")
Local nPValSegu:= GetPosSD1("D1_SEGURO")

Local nX       := 0

Default nTotal 		:= 0
Default nValDesc 	:= 0

If Len(aCols)> 0
	For nX := 1 To Len(aCols)
		If aCols[nX][Len(aCols[1])]
			lDeleted := .T.
			Exit
		EndIf
	Next nX
EndIf

aTotal := aFill(aTotal,0)
aDespesa[VALDESC] := 0
If nPValFret > 0
	aDespesa[FRETE]	:= 0
Endif

If nPValDesp > 0
	aDespesa[VALDESP] := 0
Endif

If nPValSegu > 0
	aDespesa[SEGURO] := 0
Endif

For nX := 1 To nMaxFor
	If !lDeleted .Or. !aCols[nX][nUsado+1]
		If (n==nX)
			aTotal[VALMERC] 	+= 	Iif (nTotal<>0, nTotal, aCols[nX][nPTotal])
			aTotal[VALDESC] 	+= 	Iif (nValDesc<>0, nValDesc, aCols[nX][nPValDesc])
			
			aTotal[TOTPED ] 	+= 	Iif (nTotal<>0, nTotal, aCols[nX][nPTotal]) - Iif (nValDesc<>0, nValDesc, aCols[nX][nPValDesc])

			aDespesa[VALDESC]	+=	Iif (nValDesc<>0, nValDesc, aCols[nX][nPValDesc])
			
			If nPValFret > 0
				aDespesa[FRETE] += aCols[nX][nPValFret]
			Endif		

			If nPValDesp > 0
				aDespesa[VALDESP] += aCols[nX][nPValDesp]
			Endif
			
			If nPValSegu > 0
				aDespesa[SEGURO] += aCols[nX][nPValSegu]
			Endif

		ElseIf ((nTotal==0) .Or. (n<>nX))
			aTotal[VALMERC] 	+= 	aCols[nX][nPTotal]			
			aTotal[VALDESC] 	+= 	aCols[nX][nPValDesc]
			aTotal[TOTPED ] 	+= 	aCols[nX][nPTotal] - aCols[nX][nPValDesc]
			aDespesa[VALDESC]	+=	aCols[nX][nPValDesc]
			aDespesa[SEGURO]	+=	aCols[nX][nPValSegu]
			If nPValFret > 0
				aDespesa[FRETE] += aCols[nX][nPValFret]
			Endif

			If nPValDesp > 0
				aDespesa[VALDESP] += aCols[nX][nPValDesp]
			Endif

		EndIf
	EndIf
Next nX
aTotal[TOTPED] += aDespesa[FRETE] + aDespesa[VALDESP] + aDespesa[SEGURO]
Return(.T.)
/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³Ma140Grava³ Autor ³ Eduardo Riera         ³ Data ³03.10.2002 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³Rotina de atualizacao do pre-documento de entrada            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpL1: Indica se a operacao eh de exclusao                   ³±±
±±³          ³ExpA1: Array com os recnos do SD1                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL1: Indica se houve atualizacao                           ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Esta rotina tem como objetivo atualizar um pre-documento de  ³±±
±±³          ³entrada e seus anexos                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Materiais                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function Ma140Grava(lExclui,aRecSD1,aDespesa,nSaveSX8,lInclui,lAltera,lNfFrete,nRecSF1,aPedItAnt,l116PreCTAut)

Local nOrderSF1 	:= SF1->(IndexOrd())
Local aPCMail   	:= {}
Local nX        	:= 0
Local nY        	:= 0
Local nMaxFor   	:= Len(aCols)
Local nUsado    	:= Len(aHeader)
Local lTravou   	:= .F.
Local lGrava    	:= .F.
Local cItem     	:= StrZero(0,Len(SD1->D1_ITEM))
Local cGrupo    	:= SuperGetMv("MV_NFAPROV") 
Local lGeraBlq  	:= .F.
Local nI        	:= 0
Local nJ        	:= 0
Local nPosServic	:= GetPosSD1('D1_SERVIC')
Local nPValFret		:= GetPosSD1("D1_VALFRE")
Local nDecimalPC	:= TamSX3("C7_PRECO")[2] 
Local lDescTol		:= SuperGetMV("MV_DESCTOL",.F.,.F.)
Local nVlrItem		:= 0
Local nDescItem 	:= 0
Local nQtdItem  	:= 0
Local nPosCod   	:= GetPosSD1("D1_COD")
Local nPosItNF  	:= GetPosSD1("D1_ITEM")
Local nPosQtd   	:= GetPosSD1("D1_QUANT")
Local nPosVlr   	:= GetPosSD1("D1_VUNIT")
Local nPosDesc  	:= GetPosSD1("D1_VALDESC")
Local nPos			:= 0
Local nPosPdIt 		:= 0
Local lPE140ACD 	:= ExistBlock("MT140ACD")
Local cMVDATAHOM	:= GetMv("MV_DATAHOM",NIL,"1")
Local lTempD1140	:= ExistTemplate("SD1140E")
Local lPED1140  	:= ExistBlock("SD1140E")
Local lSubSerie 	:= cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_SUBSERI")) > 0 .And. SuperGetMv("MV_SUBSERI",.F.,.F.)
Local lLog      	:= GetNewPar("MV_HABLOG",.F.)
Local lNfLimAl		:= SuperGetMV ("MV_NFLIMAL", .F.,.F.)
Local nValorTot
Local cTipoNf    	:= SuperGetMv("MV_TPNRNFS")
Local nRecVinc	 	:= 0
Local nMoedaCor  	:= 1
Local nPosPC	 	:= GetPosSD1("D1_PEDIDO")
Local nPosItemPC 	:= GetPosSD1("D1_ITEMPC")
Local aAreaSC7	 	:= {}
Local cPcAtu	 	:= ""
Local cItNfAtu   	:= ""
Local lSD1140I   	:= ExistBlock("SD1140I")
Local lMvToleNeg 	:= SuperGetMV("MV_TOLENEG",.F., .F.)
Local lForPCNF	 	:= SuperGetMV("MV_FORPCNF",.F., .F.)
Local lMvNfeDvg  	:= SuperGetMV("MV_NFEDVG", .F., .T.)
Local lPcDescTol 	:= SuperGetMV("MV_PCDETOL",.F.,.F.)
Local lSC7Exclsv 	:= FWModeAcces("SC7", 1) + FWModeAcces("SC7", 2) + FWModeAcces("SC7", 3) == "EEE"
Local lCTTExclsv 	:= FWModeAcces("CTT", 3) == "E"
Local lGetRatCC  	:= .T.
Local cFilSDE	 	:= xFilial("SDE")
Local cFilEntC7	 	:= xFilEnt(xFilial("SC7"), "SC7")
Local cFilSD1	 	:= xFilial("SD1")
Local cFilSF1 	 	:= xFilial("SF1")
Local nDescSC7   	:= 0
Local lGrv		 	:= .T. 

Default nSaveSX8 	:= GetSX8Len()
Default lNfFrete 	:= .F.
Default nRecSF1  	:= 0
Default aPedItAnt 	:= {}
Default l116PreCTAut := .F.

l140Auto := !(Type("l140Auto")=="U" .Or. !l140Auto)

If Type("_aDivPNF")=="U"
	_aDivPNF := {}
EndIf

If type('cTpFrete') == 'U'
	cTpFrete := SF1->F1_TPFRETE
EndIf	

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica o grupo de aprovacao do Comprador.                  ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
dbSelectArea("SAL")
dbSetOrder(3)
If MsSeek(xFilial("SAL")+RetCodUsr())
	cGrupo := If(!Empty(SY1->Y1_GRAPROV),SY1->Y1_GRAPROV,cGrupo)
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Ponto de entrada para alterar o Grupo de Aprovacao.          ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ExistBlock("MT140APV")
	cGrupo := ExecBlock("MT140APV",.F.,.F.,{cGrupo})
EndIf
//cGrupo:= If(Empty(SD1->D1_APROV),cGrupo,SD1->D1_APROV)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica se a operacao e de exclusao                         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lExclui
	aEval(aCols,{|x| x[nUsado+1] := .T.})
Else
	aEval(aCols,{|x| lGrava := !x[nUsado+1] .Or. lGrava })
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Posiciona o arquivo de Cliente/Fornecedor                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If cTipo$"DB"
	dbSelectArea("SA1")
	dbSetOrder(1)
	MsSeek(xFilial("SA1")+cA100For+cLoja)
Else
	dbSelectArea("SA2")
	dbSetOrder(1)
	MsSeek(xFilial("SA2")+cA100For+cLoja)
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Atualizacao do pre-documento de entrada                      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
For nX := 1 To nMaxFor
	lTravou := .F.
	Begin Transaction
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Atualizacao do cabecalho do pre-documento de entrada         ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ		
		If nX == 1 .And. lGrava
			dbSelectArea("SF1")
			dbSetOrder(1)
			If MsSeek(cFilSF1+cNFiscal+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja+cTipo)
				RecLock("SF1",.F.)
				MaAvalSF1(2)
			Else
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Obtem numero do documento quando utilizar ³
				//³ numeracao pelo SD9 (MV_TPNRNFS = 3)       ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
				If !l140Auto .and. cTipoNf == "3" .AND. cFormul == "S" .AND. cModulo <> "EIC"
					SX3->(DbSetOrder(1))
					If (SX3->(dbSeek("SD9")))
						// Se cNFiscal estiver vazio, busca numeracao no SD9, senao, respeita o novo numero
						// digitado pelo usuario.
						cNFiscal := MA461NumNf(.T.,cSerie,cNFiscal)
					EndIf			
				Endif 
				RecLock("SF1",.T.)
				//--Atualiza status da nota para em conferencia
				If cPaisLoc == "BRA"
					If UsaConfF(cTipo, cA100For, cLoja)
						SF1->F1_STATCON := "0"
					EndIf
				EndIf
			EndIf
			SF1->F1_FILIAL := cFilSF1
			SF1->F1_DOC    := cNFiscal
			
			SerieNfId("SF1",1,"F1_SERIE",dDEmissao,cEspecie,cSerie)
			
			SF1->F1_FORNECE:= cA100For
			SF1->F1_LOJA   := cLoja
			SF1->F1_EMISSAO:= dDEmissao
			SF1->F1_EST    := IIF(!Empty(cUfOrigP),cUfOrigP,IIf(cTipo$"DB",SA1->A1_EST,SA2->A2_EST))
			SF1->F1_TIPO   := cTipo
			SF1->F1_DTDIGIT:= IIf(cMVDATAHOM == "1" .Or. Empty(SF1->F1_RECBMTO),dDataBase,SF1->F1_RECBMTO)
			SF1->F1_RECBMTO:= SF1->F1_DTDIGIT
			SF1->F1_FORMUL := IIf(cFormul=="S","S"," ")
			SF1->F1_ESPECIE:= cEspecie
			SF1->F1_DESPESA:= aDespesa[VALDESP]
			SF1->F1_FRETE  := aDespesa[FRETE]
			SF1->F1_SEGURO := aDespesa[SEGURO]
			SF1->F1_DESCONT:= aDespesa[VALDESC]
			SF1->F1_TPFRETE:= cTpFrete

			If SF1->(ColumnPos("F1_TPCOMPL")) > 0  .And. cTipo == "C" .And. Type("cTpCompl") == "C"
				SF1->F1_TPCOMPL := cTpCompl
			EndIf

			If lSubSerie .And. Type("cSubSerie") == "C"
				SF1->F1_SUBSERI := cSubSerie
			EndIf

			If lNfFrete						
				SF1->F1_ORIGLAN := 'F'
			EndIf

			If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed 
				SF1->F1_INDPRES := aInfAdic[16]
				SF1->F1_CODA1U := aInfAdic[17]
			Endif		
			
			MaAvalSF1(1)
			If l140Auto .Or. l116PreCTAut
				For nI := 1 To Len(aAutoCab) //ALAN
					If aAutoCab[nI][1] == "F1_FORMUL" .AND. (cPaisLoc == "BRA" .AND.  aAutoCab[nI][2] == "N")
						SF1->(FieldPut(FieldPos(aAutoCab[nI][1]),""))
					Else	
						SF1->(FieldPut(FieldPos(aAutoCab[nI][1]),aAutoCab[nI][2]))
					Endif				
				Next nI
			EndIf
			
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Atualizacao da conferencia fisica                            ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If cPaisLoc == "BRA" 
				If UsaConfF(cTipo, cA100For, cLoja)
					If lPE140ACD
						ExecBlock("MT140ACD",.F.,.F.)
					EndIf
				EndIf
			EndIf

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Tratamento da gravacao do SF1 na Integridade Referencial            ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			SF1->(FkCommit())
			nRecSF1 := SF1->(RecNo())

		EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Atualizacao dos itens do pre-documento de entrada            ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If Len(aRecSD1) == 0 .And. lExclui
			dbSelectArea("SD1")
			SD1->(dbSetOrder(1))
			SD1->(dbSeek(cFilSD1+cNFiscal+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja))
			
			While !SD1->(Eof()) .And. SD1->D1_DOC == cNFiscal .And. SD1->D1_SERIE == cSerie;
										.And. SD1->D1_FORNECE == cA100For .And. SD1->D1_LOJA == cLoja
													
				Aadd(aRecSD1,SD1->(RecNo()))							
				SD1->(dbSkip())
			EndDo
		EndIf
		If nX <= Len(aRecSD1)
			dbSelectArea("SD1")
			MsGoto(aRecSD1[nX])
			RecLock("SD1")
			If cPaisLoc=="BRA"
				MaAvalSD1(2,"SD1")
			ElseIf cPaisLoc == "ARG"
				If SD1->D1_TIPO_NF == "5"	//Factura Fob
					MaAvalSD1(2,"SD1")
				EndIf
			ElseIf cPaisLoc == "CHI"
				If SD1->D1_TIPO_NF == "9"	//Factura Aduana
					MaAvalSD1(2,"SD1")
				EndIf
			Endif
			lTravou := .T.
		Else
			If !aCols[nX][nUsado+1]	
				RecLock("SD1",.T.)
				lTravou := .T.
			EndIf
		EndIf
		If lTravou
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ-Ä¿
			//³ Pontos de Entrada 											 ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ-ÄÄÙ
			If lExclui
				If lTempD1140
					ExecTemplate("SD1140E",.F.,.F.)
				EndIf
				If lPED1140
					ExecBlock("SD1140E",.F.,.F.)
				Endif
			EndIf
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Estorna o Servico do WMS (DCF)                           ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If IntWMS()
				WmsAvalSD1("4","SD1")
			EndIf
			If aCols[nX][nUsado+1]
				If cPaisLoc=="BRA"
					MaAvalSD1(3,"SD1")
				ElseIf cPaisLoc == "ARG"
					If SD1->D1_TIPO_NF == "5"	//Factura Fob
						MaAvalSD1(3,"SD1")
					EndIf
				ElseIf cPaisLoc == "CHI"
					If SD1->D1_TIPO_NF == "9"	//Factura Aduana
						MaAvalSD1(3,"SD1")
					EndIf
				Endif
				//-- Incluido condição para que seja apagado a SDE correspondente.
				aAreaSDE := GetArea("SD1")
				dbSelectArea("SDE")  
				dbSetOrder(1)
				If (SDE->(MsSeek(cFilSDE+SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_ITEM)))
					While SDE->(!EOF()) .And. (SDE->DE_DOC+SDE->DE_SERIE+SDE->DE_FORNECE+SDE->DE_LOJA+SDE->DE_ITEMNF == SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_ITEM)
						RecLock("SDE",.F.)
						SDE->(dbDelete())
						MsUnlock()
						SDE->(dbSkip())
					EndDo
				EndIf
				RestArea(aAreaSDE)

				//Exclusão DKD - Complementos dos itens da NF
				If (type("lDKD") == "L" .and. lDKD) .And. (type("lTabAuxD1") == "L" .and. lTabAuxD1) .And. Type("aColsDKD") == "A" .And. Len(aColsDKD) > 0 .And. (nJ	:= aScan(aColsDKD,{|x| x[1] == SD1->D1_ITEM})) > 0
					A103DKDGRV(aHeadDKD,aColsDKD,nJ,"D")
				Endif

				//Apaga a SD1
				SD1->(dbDelete())
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Projeto CNI ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If lLog
					RSTSCLOG("LPN",2,/*cUser*/)
				EndIf
			Else
				cItem := Soma1(cItem,Len(cItem))
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Atualiza os dados do acols                                   ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				For nY := 1 To nUsado
					If aHeader[nY][10] <> "V"
						SD1->(FieldPut(FieldPos(aHeader[nY][2]),aCols[nX][nY]))
					EndIf
				Next nY
				If l140Auto	
					If StrZero(nX,Len(SD1->D1_ITEM))== SD1->D1_ITEM		
						nPos := aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_QUANT"})
						If nPos != 0 
							SD1->D1_QUANT := aAutoItens[nX,nPos,2]
						EndIf
						nPos := aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_TOTAL"})
						If nPos != 0 	
							SD1->D1_TOTAL := aAutoItens[nX,nPos,2]
						EndIf	
					EndIf				
				EndIf
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Posiciona registros                                          ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				dbSelectArea("SB1")
				dbSetOrder(1)
				MsSeek(xFilial("SB1")+SD1->D1_COD)
				
				If lConsLoja
					SC7->(DbSetOrder(9))
					SC7->(MsSeek(cFilEntC7 + cA100For + cLoja + SD1->D1_PEDIDO + SD1->D1_ITEMPC))
				Else
					SC7->(DbSetOrder(14))
					SC7->(MsSeek(cFilEntC7 + SD1->D1_PEDIDO + SD1->D1_ITEMPC))
					While SC7->(!EOF()) .And. SC7->(C7_FILENT + C7_NUM + C7_ITEM) == cFilEntC7 + SD1->D1_PEDIDO + SD1->D1_ITEMPC
						If SC7->C7_FORNECE == cA100For
							Exit
						EndIf
						SC7->(dbSkip())
					EndDo
				EndIf

				If SC7->C7_FORNECE <> cA100For .And. lForPCNF
					SC7->(DbSetOrder(14))
					SC7->(MsSeek(cFilEntC7 + SD1->D1_PEDIDO + SD1->D1_ITEMPC))				
				EndIf

				dbSelectArea("SD1")
				SD1->D1_FILIAL	:= cFilSD1
				SD1->D1_FORNECE	:= cA100For
				SD1->D1_LOJA	:= cLoja
				SD1->D1_DOC		:= cNFiscal
				
				SerieNfId("SD1",1,"D1_SERIE",dDEmissao,cEspecie,cSerie)
				
				SD1->D1_EMISSAO	:= dDEmissao
				SD1->D1_DTDIGIT	:= dDataBase
				SD1->D1_GRUPO	:= SB1->B1_GRUPO
				SD1->D1_TIPO	:= cTipo
				SD1->D1_RATEIO	:= SC7->C7_RATEIO
				nMoedaCor		:= SC7->C7_MOEDA 
				
				If IntWMS() .And. Empty(SD1->D1_NUMSEQ)
					SD1->D1_NUMSEQ := ProxNum()
				EndIf
				
				SD1->D1_TP			:= SB1->B1_TIPO
				SD1->D1_FORMUL	:= IIf(cFormul=="S","S"," ")
				If Empty(SD1->D1_ITEM)
					SD1->D1_ITEM    := cItem
				EndIf
				SD1->D1_TIPODOC := SF1->F1_TIPODOC
				// Caso o campo exista, significa que tem ACDSTD implantado, sendo necessario iniciar a CONFERENCIA
				SD1->D1_QTDCONF := 0
				
				If l140Auto
					nPos := aScan(aAutoItens[nX],{|x| AllTrim(x[1])=="D1_ORIGLAN"})
					If nPos > 0
						SD1->D1_ORIGLAN := aAutoItens[nX,nPos,2]
					Endif
				Endif
				
				//Atualiza rateio de frete
				If nPValFret > 0
					SD1->D1_VALFRE	:= A140ATUFRT(2,,SD1->D1_COD, SD1->D1_ITEM)
				Endif
				
				If cPaisLoc != "BRA"
					SD1->D1_ESPECIE	:= cEspecie
					SD1->D1_FORMUL  := SF1->F1_FORMUL
					SD1->D1_TES	:= "   " 
				EndIf

				If l140Auto
					For nJ := 1 To Len(aAutoItens[nX])
						If Subs(aAutoItens[nX][nJ][1],4,6) $ "BASIMP|VALIMP|ALQIMP|TESDES"
							SD1->(FieldPut(FieldPos(aAutoItens[nX][nJ][1]),aAutoItens[nX][nJ][2]))
						EndIf
					Next nJ
				EndIf

				//Gravação DKD - Complementos dos itens da NF
				If (type("lDKD") == "L" .and. lDKD) .And. (type("lTabAuxD1") == "L" .and. lTabAuxD1) .And. Type("aColsDKD") == "A" .And. Len(aColsDKD) > 0 .And. (nJ	:= aScan(aColsDKD,{|x| x[1] == SD1->D1_ITEM})) > 0
					A103DKDGRV(aHeadDKD,aColsDKD,nJ)
				Endif 

				//Caio.Santos - 11/01/13 - Req.72
				If lLog
					RSTSCLOG("LPN",1,/*cUser*/)
				EndIf				
				//-- Incluido condição para que seja gravado na SDE o rateio da SCH do pedido que está vinculado a Pré-Nota.
				aAreaSD1 := GetArea("SD1")
				aAreaSC7 := GetArea("SC7")
				If lCTTExclsv .And. lSC7Exclsv
					lGetRatCC := SC7->C7_FILIAL == cFilAnt
				EndIf 
				If lGetRatCC
					SC7->(dbSetOrder(14)) //-- C7_FILENT, C7_NUM, C7_ITEM
					If SC7->(dbSeek(cFilEntC7+aCols[nx,nPosPc]+aCols[nx,nPosItemPC]))
						dbSelectArea("SCH")
						cFilSCH := xFilial("SCH", Iif(lSC7Exclsv, SC7->C7_FILIAL, cFilAnt))  
						dbSetOrder(1) // CH_FILIAL+CH_PEDIDO+CH_FORNECE+CH_LOJA+CH_ITEMPD+CH_ITEM
						If lAltera .Or. Inclui
							If(SCH->(MsSeek(cFilSCH+SC7->( C7_NUM + C7_FORNECE + C7_LOJA + C7_ITEM ))))
								While SCH->(!EOF()) .And. ; 
									SCH->(CH_FILIAL + CH_PEDIDO + CH_FORNECE+ CH_LOJA+ CH_ITEMPD) == SC7->(C7_FILIAL + C7_NUM + C7_FORNECE + C7_LOJA + C7_ITEM  )
									dbSelectArea("SDE")  
									SDE->(dbSetOrder(1)) // DE_FILIAL+DE_DOC+DE_SERIE+DE_FORNECE+DE_LOJA+DE_ITEMNF+DE_ITEM
									lGrv := IIf(SDE->(MsSeek(cFilSDE+SD1->D1_DOC+SD1->D1_SERIE+SCH->CH_FORNECE+SCH->CH_LOJA+SD1->D1_ITEM+SCH->CH_ITEM)),.F.,.T.)

									If Len(aPedItAnt) > 0
										nPosPdIt := aScan(aPedItAnt,{|x| x[1] == aCols[nx,nPosItNF]})
										If nPosPdIt > 0
											If !lGrv .And. aCols[nx,nPosItNF] == aPedItAnt[nPosPdIt,1] .And. (AllTrim(aCols[nx,nPosPc]+aCols[nx,nPosItemPC]) <> AllTrim(aPedItAnt[nPosPdIt,2]+aPedItAnt[nPosPdIt,3])) //Verifica se o pedido de compra (item nf + num ped + item pc) foi alterado, ao salvar alteração da pré nota
												aAreaSDE := GetArea("SD1")
												dbSelectArea("SDE")  
												dbSetOrder(1)
												While SDE->(!EOF()) .And. (SDE->DE_DOC+SDE->DE_SERIE+SDE->DE_FORNECE+SDE->DE_LOJA+SDE->DE_ITEMNF == SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_ITEM)
													RecLock("SDE",.F.)
													SDE->(dbDelete())
													MsUnlock()
													SDE->(dbSkip())
												EndDo

												lGrv := .T. 
												RestArea(aAreaSDE)	
											EndIf
										EndIf 
									EndIf  
										
									RecLock("SDE",lGrv)
									
									For nY := 1 to SDE->(FCount())
										nPos := SCH->(FieldPos("CH"+SubStr(SDE->(FieldName(nY)),3)))
										If nPos > 0 
											FieldPut(nY,SCH->(FieldGet(nPos)))
										EndIf
									Next nY
									
									SDE->DE_FILIAL	:= cFilSDE
									SDE->DE_DOC		:= SD1->D1_DOC
									SDE->DE_SERIE	:= SD1->D1_SERIE
									SDE->DE_FORNECE	:= SD1->D1_FORNECE
									SDE->DE_LOJA	:= SD1->D1_LOJA
									SDE->DE_ITEMNF 	:= SD1->D1_ITEM											
									SDE->(MsUnLock())
									
									SCH->(dbSkip())
								EndDo
							EndIf
						EndIf	
					EndIf	
					RestArea(aAreaSD1)
					RestArea(aAreaSC7)
				EndIf
				
				//so eh necessario q. um item tenha bloqueio, pois o bloqueio eh da NF inteira
				If !lGeraBlq .And. Empty(SD1->D1_TEC) .And. !Empty(SD1->D1_PEDIDO+SD1->D1_ITEMPC) .And. !Empty(cGrupo)
					
					nRecC7 := A103RECC7(xFilial("SC7"),SD1->D1_PEDIDO,SD1->D1_FORNECE,SD1->D1_LOJA,SD1->D1_COD,SD1->D1_ITEMPC)
					SC7->(DbGoTo(nRecC7))
					If !Empty(SD1->D1_PEDIDO + SD1->D1_ITEMPC) .And. nRecC7 > 0
						If lDescTol
							If SD1->D1_QUANT > 0
								nVlrItem := (SD1->D1_VUNIT - (SD1->D1_VALDESC/SD1->D1_QUANT))
							Else
								nVlrItem := (SD1->D1_VUNIT - SD1->D1_VALDESC)
							EndIf
						Else
							nVlrItem := SD1->D1_VUNIT
						EndIf

						//-- Avalia tolerancia a cada novo item de pedido na NF
						If !(AllTrim(SD1->D1_PEDIDO + SD1->D1_ITEMPC) == cPcAtu)
							
							cPcAtu := AllTrim(SD1->D1_PEDIDO + SD1->D1_ITEMPC) //-- Obtem chave do Pedido atual
							
							cItNfAtu := aCols[nX][nPosItNF] //-- Controle do item da NF
							nQtdItem := aCols[nX][nPosQtd] //-- Quantidade do item da NF
							nVlrItem := aCols[nX][nPosVlr] //-- Valor do item da NF
							nDescItem := aCols[nX][nPosDesc] //-- Desconto do item da NF
																//-- Verifica se item do PC foi quebrado em mais de um item na pré-nota e incrementa quantidade e valores
							For nY := 1 To Len(aCols)
								If !(aCols[nY][nPosItNF] == cItNfAtu) .And. aCols[nY][nPosCod] == aCols[nX][nPosCod] .And. aCols[nY][nPosItemPc] == aCols[nX][nPosItemPc] .And. aCols[nY][nPosPc] == aCols[nX][nPosPc]
									nVlrItem	:= (((aCols[nY][nPosVlr] * aCols[nY][nPosQtd]) + (nVlrItem * nQtdItem)) / (nQtdItem + aCols[nY][nPosQtd]))
									nQtdItem	+= (aCols[nY][nPosQtd] - SC7->C7_QTDACLA)
									nDescItem	+= aCols[nY][nPosDesc]
								EndIf
							Next nY

							//-- Aplica o desconto quando no valor do item quando estiver configurado para considerá-lo na tolerancia
							If lDescTol
								nDescItem := nDescItem / nQtdItem
								nVlrItem  := nVlrItem - nDescItem
							EndIf
							nDescSC7	:= 0
							If lPcDescTol
								nDescSC7	:= SC7->C7_VLDESC								 
							Endif
							
							lGeraBlq := MaAvalToler(SD1->D1_FORNECE, SD1->D1_LOJA,SD1->D1_COD,Iif(lMvToleNeg, nQtdItem, nQtdItem+SC7->C7_QUJE+SC7->C7_QTDACLA),SC7->C7_QUANT,nVlrItem,xMoeda(SC7->C7_PRECO-nDescSC7,SC7->C7_MOEDA,,M->dDEmissao,nDecimalPC,SC7->C7_TXMOEDA,))[1]
						
						EndIf
					EndIf
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
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Ponto de Entrada na Inclusao.                                ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If lSD1140I 
					ExecBlock("SD1140I",.F.,.F.,{nx})
				EndIf
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Atualiza array com Pedidos utilizados                        ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If !Empty(SD1->D1_PEDIDO)
					If aScan(aPCMail,SD1->D1_PEDIDO+" - "+SD1->D1_ITEMPC) == 0
						Aadd(aPCMail,SD1->D1_PEDIDO+" - "+SD1->D1_ITEMPC)
					EndIf
				EndIf

				//Gera dados na CBN - partes do produto
				AcdGeraCBN(SD1->D1_COD,SD1->D1_QUANT)

				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Gera os servicos de WMS na inclusao da Pre-Nota              ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				If IntWMS() .And. nPosServic > 0 .And. !Empty(aCols[nX, nPosServic])
					WmsAvalSD1("5","SD1",aCols,nX,aHeader,/*lPreNota*/.T.)
				EndIf
			EndIf
			//--Verifica se já foi gerado bloqueio, pois basta o bloqueio de um item para o bloqueio de toda a nota
			If (lGeraBlq .And. !SF1->F1_STATUS == "B") .Or. (!lGeraBlq .And. SF1->F1_STATUS == "B")
				dbSelectArea("SAL")
				dbSetOrder(2)
				If !Empty(cGrupo) .And. dbSeek(xFilial("SAL")+cGrupo)
					cGrupo:= If(Empty(SF1->F1_APROV),cGrupo,SF1->F1_APROV)
					If ALTERA .Or. lExclui // Estorna as liberacoes
						MaAlcDoc({SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,"NF",SF1->F1_VALBRUT,,,cGrupo,,Iif(SF1->F1_MOEDA == 0, nMoedaCor,SF1->F1_MOEDA ),SF1->F1_TXMOEDA,SF1->F1_EMISSAO},SF1->F1_EMISSAO,3)
					EndIf
					If !lExclui .And. lGeraBlq
						nValorTot := Iif(lNfLimAl, Iif(ValType(A140Total) == "A" .And. ;
										Len(A140Total) >= 3 .And.;
						  				A140Total[TOTPED] > 0,  A140Total[TOTPED], SF1->F1_VALBRUT), 0)
						MaAlcDoc({SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,"NF",nValorTot,,,cGrupo,,Iif(SF1->F1_MOEDA == 0, nMoedaCor,SF1->F1_MOEDA ),SF1->F1_TXMOEDA,SF1->F1_EMISSAO},SF1->F1_EMISSAO,1)
					EndIf					
					dbSelectArea("SF1")
					Reclock("SF1",.F.)
					IF !lExclui .And. lGeraBlq						
						SF1->F1_STATUS := "B"
						SF1->F1_APROV  := cGrupo
					Else
						SF1->F1_STATUS := " "
					EndIf	
					MsUnlock()
			EndIf
		EndIf

		If nX == nMaxFor .And. !lGrava
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Tratamento da gravacao do SD1 na Integridade Referencial            ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			SD1->(FkCommit())

			dbSelectArea("SF1")
			dbSetOrder(1)
			If MsSeek(cFilSF1+cNFiscal+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja+cTipo)   				
				SDS->(DbSetOrder(1))
				If SDS->(MsSeek(xFilial("SDS")+cNFiscal+SerieNfId("SF1",4,"F1_SERIE",dDEmissao,cEspecie,cSerie)+cA100For+cLoja))
					SDS->(RecLock("SDS",.F.))
					Replace SDS->DS_STATUS 	With If(SDS->DS_TIPO == "N"," ",SDS->DS_TIPO)
					Replace SDS->DS_USERPRE With CriaVar("DS_USERPRE")
					Replace SDS->DS_DATAPRE With CriaVar("DS_DATAPRE")
					Replace SDS->DS_HORAPRE With CriaVar("DS_HORAPRE")
					SDS->(MsUnlock())
				EndIf				
				MsDocument("SF1", SF1->( RecNo()),2,,3) // Exclui o Banco de Conhecimentos vinculados a Pre-NF
				RecLock("SF1",.F.)
				MaAvalSF1(2)
				MaAvalSF1(3)
				MaAlcDoc({SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,"NF",SF1->F1_VALBRUT,,,cGrupo,,Iif(SF1->F1_MOEDA == 0, nMoedaCor,SF1->F1_MOEDA ),SF1->F1_TXMOEDA,SF1->F1_EMISSAO},SF1->F1_EMISSAO,3)
				
				SF1->(dbDelete())
			EndIf
		EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Executa os gatilhos e a confirmacao do semaforo              ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If nX == nMaxFor
			EvalTrigger()
			While ( GetSX8Len() > nSaveSX8 )
				ConfirmSx8()
			EndDo
		 EndIf
		EndIf		
	End Transaction
Next nX

If lExclui 
	A103DelSF8(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA)
EndIf

If !lExclui .And. lGrava
	//-- Integrado ao WMS devera disponibilizar as atividades para execução
	If IntWMS()
		WmsAvalSF1("5","SF1")
	EndIf
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica a existencia de e-mails para o evento 005       ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	MEnviaMail("005",{SF1->F1_DOC,SerieNfId("SF1",2,"F1_SERIE"),SF1->F1_FORNECE,SF1->F1_LOJA,If(cTipo$"DB",SA1->A1_NOME,SA2->A2_NOME),aPCMail})
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica a necessidade da impressao de etiquetas         ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If SuperGetMV("MV_INTACD",.F.,"0") == "1"
		If (SA2->A2_IMPIP == "2") .Or. (SA2->A2_IMPIP $ "03 " .And. SuperGetMv("MV_IMPIP",.F.,"3") == "2" ) // MV_IMPIP: ACD
			If (!l140Auto .Or. GetAutoPar("AUTIMPIP",aAutoCab,0) == 1) .And. SF1->F1_STATCON <> "1"
				ACDI10NF(SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA,.T.,l140Auto)
			EndIf
		EndIf
	EndIf
	
    If lMvNfeDvg .And. ( Empty(SF1->F1_STATUS) .Or. SF1->F1_STATUS == "B" .Or. SF1->F1_STATUS == "C" ) .And. (Inclui .or. Altera)
		If Len( _aDivPNF ) > 0
			CA040MAN(@_aDivPNF)
		EndIf
    EndIf
	


	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Template Function apos atualizacao de todos os dados inclusao³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If (ExistTemplate("SF1140I"))
		ExecTemplate("SF1140I",.F.,.F.)
	EndIf

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Ponto de Entrada apos atualizacao de todos os dados inclusao ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If (ExistBlock("SF1140I"))
		ExecBlock("SF1140I",.F.,.F.,{lInclui,lAltera})
	EndIf 

EndIf    

//-- Atualiza documento no TOTVS Colaboração	
If INCLUI .And. FindFunction("COLConVinc") .And. (nRecVinc := COLConVinc(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA)) > 0 
	SDS->(DbGoTo(nRecVinc))
	If SDS->DS_STATUS <> 'P'
		RecLock("SDS",.F.)
		Replace SDS->DS_OK		With ''
		Replace SDS->DS_USERPRE	With cUserName
		Replace SDS->DS_DATAPRE	With dDataBase
		Replace SDS->DS_HORAPRE	With Time()
		Replace SDS->DS_STATUS	With 'P'
		Replace SDS->DS_DOCLOG	With ''
		MsUnlock()
	Endif
Endif

SC7->(dbSetOrder(1))
dbSelecTarea('SF1')
SF1->(dbSetOrder(nOrderSF1))

Return(lGrava)


//-------------------------------------------------------------------
/*/{Protheus.doc} A140DespGat() 
Gatilha o refresh do totalizador das despesas acessorias
@author yuri.porto
@since 24/04/2017
@version P118
/*/
//-------------------------------------------------------------------
Function A140DespGat()

Local nPValFret := 0
Local nPQtdeIt	:= 0
Local nPPedido	:= 0
Local nPItemPc	:= 0
Local nx 		:= 0
Local aArea     := {}
Local lPropFret := SuperGetMV("MV_FRT103E",.F.,.T.)
	
If IsInCallStack("MATA140")
    aArea       := GetArea()
    nPValFret   := GetPosSD1("D1_VALFRE")   //recebe posição da coluna  
    nPValSegu   := GetPosSD1("D1_SEGURO")   //recebe posição da coluna  
    nPValDesp   := GetPosSD1("D1_DESPESA")  //recebe posição da coluna  
    nPValDesc   := GetPosSD1("D1_VALDESC")  //recebe posição da coluna  
    nPQtdeIt    := GetPosSD1("D1_QUANT")    //recebe posição da coluna  Quantidade
    nPPedido    := GetPosSD1("D1_PEDIDO")   //recebe posição da coluna  PC
    nPItemPc    := GetPosSD1("D1_ITEMPC")   //recebe posição da coluna  Item do PC
    nPItem      := GetPosSD1("D1_ITEM")     //recebe posição da coluna  Item da NF

    SC7->(DbSetOrder(14)) //C7_FILENT+C7_NUM+C7_ITEM

    If LEN(aCols) >0.and.Valtype(a140Desp) =="A"
        If lPropFret .And.  nPValFret > 0
            a140Desp[FRETE] := 0
            If Valtype(M->D1_VALFRE) == "N"
                 aCols[n][nPValFret] := M->D1_VALFRE
            EndIf
        Endif
        If nPValSegu>0
            a140Desp[SEGURO] := 0
            If Valtype(M->D1_SEGURO) == "N"
                 aCols[n][nPValSegu] := M->D1_SEGURO
            Endif
        EndIf      
        If nPValDesp>0
            a140Desp[VALDESP] := 0  
            If Valtype(M->D1_DESPESA) == "N"
                aCols[n][nPValDesp] := M->D1_DESPESA
            EndIf      
        Endif
        If nPValDesc>0
            a140Desp[VALDESC] := 0          
            If Valtype(M->D1_VALDESC) == "N"
                aCols[n][nPValDesc] := M->D1_VALDESC
            EndIf
        Endif
        For nX := 1 To LEN(aCols)
            If !empty(aCols[nX][nPPedido])
                If SC7->(dBSeek(xFilial('SC7')+aCols[nX][nPPedido]+aCols[nX][nPItemPc]))
                    If ReadVar() == "M->D1_QUANT" .and. aCols[nX][nPPedido]+aCols[nX][nPItemPc] == BuscaCols("D1_PEDIDO")+BuscaCols("D1_ITEMPC")
                        If M->D1_QUANT<=SC7->C7_QUANT .And. aCols[nX][nPItem] == BuscaCols("D1_ITEM")
                            If lPropFret .And. nPValFret>0
                                aCols[nX][nPValFret] := xMoeda((SC7->C7_VALFRE*M->D1_QUANT)/(SC7->C7_QUANT-SC7->C7_QUJE),SC7->C7_MOEDA,1,dDEmissao,Nil,SC7->C7_TXMOEDA)
								a140Desp[FRETE] += aCols[nX][nPValFret]
                            Endif
                            If nPValSegu>0
                                aCols[nX][nPValSegu] := xMoeda((SC7->C7_SEGURO*M->D1_QUANT)/(SC7->C7_QUANT-SC7->C7_QUJE),SC7->C7_MOEDA,1,dDEmissao,Nil,SC7->C7_TXMOEDA)
								a140Desp[SEGURO] += aCols[nX][nPValSegu]
                            Endif
                            If nPValDesp>0
                                aCols[nX][nPValDesp] := xMoeda((SC7->C7_DESPESA*M->D1_QUANT)/(SC7->C7_QUANT-SC7->C7_QUJE),SC7->C7_MOEDA,1,dDEmissao,Nil,SC7->C7_TXMOEDA)
								a140Desp[VALDESP] += aCols[nX][nPValDesp]      
                            Endif
                            If nPValDesc>0
                                aCols[nX][nPValDesc] := xMoeda((SC7->C7_VLDESC*M->D1_QUANT)/(SC7->C7_QUANT-SC7->C7_QUJE),SC7->C7_MOEDA,1,dDEmissao,Nil,SC7->C7_TXMOEDA)
								a140Desp[VALDESC] += aCols[nX][nPValDesc]
                            Endif
                        EndIf
                    EndIf
                EndIf
            Endif
        Next nX
    EndIf

    RestArea(aArea)
    Eval(bRefresh)

EndIf

Return .T.

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³A140AtuCon³ Prog. ³ Fernando Alves        ³Data  ³15/03/2001³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³ Atualiza folder de conferencia fisica                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A140ConfPr( ExpO1, ExpA1)                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpO1 = Objeto do list box                                 ³±±
±±³          ³ ExpA2 = Array com o contudo da list box                    ³±±
±±³          ³ ExpO3 = Objeto para flag do list box                       ³±±
±±³          ³ ExpO4 = Objeto para flag do list box                       ³±±
±±³          ³ ExpO5 = Objeto com total de conferentes na nota            ³±±
±±³          ³ ExpN6 = Variavel de quantidade de conferentes              ³±±
±±³          ³ ExpN7 = Objeto com o status da nota                        ³±±
±±³          ³ ExpN8 = Variavel com a descricao do status da nota         ³±±
±±³          ³ ExpL9 = Habilita recontagem na conferencia (limpa o que foi³±±
±±³          ³         gravado)                                           ³±±
±±³          ³ ExpO10= Objeto timer                                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function A140AtuCon(oList,aListBox,oEnable,oDisable,oConf,nQtdConf,oStatCon,cStatCon,lReconta,oTimer)

Local aArea     := {}
Local cAliasOld := Alias()
Local lWmsNew   := SuperGetMv("MV_WMSNEW",.F.,.F.) .And. SuperGetMV("MV_INTWMS",.F.,.F.)
Local lMTWmsPai := FindFunction("MTWmsPai")	
Local oProduto  := Nil
Local lConfirm  := .F.

If ValType(oTimer) == "O"
	oTimer:Deactivate()
EndIf
lReconta := If (lReconta == nil,.F.,lReconta)
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Habilita recontagem³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lReconta
	If IsBlind()
		lConfirm := .T.
	Else
		lConfirm := Aviso(STR0024,STR0025,{STR0026,STR0027}) == 1 //"AVISO"###"Voce realmente quer fazer a recontagem?"###"Sim"###"Nao"
	EndIf
EndIf
If lReconta .And. lConfirm
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

MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)

While SD1->(!EOF()) .and. SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE == SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE
	
	If lWmsNew .And. lMTWmsPai
		MTWmsPai(SD1->D1_COD,@oProduto)
	Endif
		
	If lWmsNew .And. IntWMS(SD1->D1_COD) .And. lMTWmsPai .And. oProduto:aProduto[1][1] <> SD1->D1_COD 	
	
		CBN->(MsSeek(xFilial("CBN")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA))
		
		While CBN->(!EOF()) .and. CBN->CBN_DOC+CBN->CBN_SERIE+CBN->CBN_FORNEC+CBN->CBN_LOJA == SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³Se for a opcao RECONTAGEM, zera tudo o que foi conferido³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			If lReconta
				Reclock("CBN",.F.)
				CBN->CBN_QTDCON := 0
				CBN->(MsUnlock())
			EndIf
			aAdd(aListBox,{CBN->CBN_PRODU,CBN->CBN_QTDCON,CBN->CBN_QUANT})
			CBN->(dbSkip())
		End
	Else
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Se for a opcao RECONTAGEM, zera tudo o que foi conferido³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If lReconta
			Reclock("SD1",.F.)
			SD1->D1_QTDCONF := 0
			SD1->(msUnlock())
		EndIf
		aAdd(aListBox,{SD1->D1_COD,SD1->D1_QTDCONF,SD1->D1_QUANT})
	EndIf
	SD1->(dbSkip())
End
If ValType(oList) == "O"
	oList:SetArray(aListBox)
	oList:bLine := { || {If (aListBox[oList:nAT,2] == aListBox[oList:nAT,3],oEnable,oDisable), aListBox[oList:nAT,1], aListBox[oList:nAT,2]} }
	oList:Refresh()
EndIf
RestArea(aArea)
dbSelectArea(cAliasOld)
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Atualiza os Gets³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
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
		cStatCon := STR0014 //"NF conferida"
	Case SF1->F1_STATCON == '0'
		cStatCon := STR0015 //"NF nao conferida"
	Case SF1->F1_STATCON == '2'
		cStatCon := STR0016 //"NF com divergencia"
	Case SF1->F1_STATCON == '3'
		cStatCon := STR0017 //"NF em conferencia"
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
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³A140DetCon³ Prog. ³ Eduardo Motta         ³Data  ³19/04/2001³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³ Monta listbox com dados da conferencia do produto          ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A140DetCon(oList,aListBox)                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpO1 = Objeto do list box                                 ³±±
±±³          ³ ExpA2 = Array com o contudo da list box                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function A140DetCon(oList,aListBox)
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

DEFINE MSDIALOG oDlgDet TITLE OemToAnsi(STR0028+cCodPro+" "+SB1->B1_DESC) From 0, 0 To 25, 67 OF oMainWnd //"Detalhes de Conferencia do Produto "
oListDet := TWBrowse():New( 02, 2, (oDlgDet:nRight/2)-5, (oDlgDet:nBottom/2)-30,,aColunas,, oDlgDet,,,,,,,,,,,, .F.,, .T.,, .F.,,, )

A140AtuDet(cCodPro,oListDet,aListDet,,aCpoCBE)

@ (oDlgDet:nBottom/2)-25, 005 Say STR0029 PIXEL OF oDlgDet //"Ordem "
@ (oDlgDet:nBottom/2)-25, 025 MSCOMBOBOX oIndice    VAR cIndice    ITEMS aIndice    SIZE 180,09 PIXEL OF oDlgDet
oIndice:bChange := {||CBE->(DbSetOrder(aIndOrd[oIndice:nAt])),A140AtuDet(cCodPro,oListDet,aListDet,oTimer,aCpoCBE)}
@  (oDlgDet:nBottom/2)-25, (oDlgDet:nRight/2)-50 BUTTON STR0030 SIZE 40,10 ACTION ( oDlgDet:End() ) Of oDlgDet PIXEL // //"&Retorna"

DEFINE TIMER oTimer INTERVAL 1000 ACTION (A140AtuDet(cCodPro,oListDet,aListDet,oTimer,aCpoCBE)) OF oDlgDet
oTimer:Activate()

ACTIVATE MSDIALOG oDlgDet CENTERED

sRestArea(aArea)
Return .T.

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³A140AtuDet³ Prog. ³ Eduardo Motta         ³Data  ³19/04/2001³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³ Atualiza array para listbox dos detalhes de conferencia    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A140AtuDet(cCodPro,oListDet,aListDet,oTimer)               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ cCodPro  - Codigo do produto a procurar no CBE             ³±±
±±³          ³ oListDet - Objeto listbox a atualizar                      ³±±
±±³          ³ aListDet - Array do listbox                                ³±±
±±³          ³ oTimer   - Objeto timer a desativar para o processo        ³±±
±±³          ³ aCpoCBE  - Campos do LISTBOX                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function A140AtuDet(cCodPro,oListDet,aListDet,oTimer,aCpoCBE)
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
		else
			uConteudo := CriaVar(aCpoCBE[nI,1])
		endif
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
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³RetDetLine³ Prog. ³ Eduardo Motta         ³Data  ³20/04/2001³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³ Funcao para retornar campos para o bLine do listbox        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ RetDetLine(aListDet,nAt)                                   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ aListDet - Array com dados do listbox                      ³±±
±±³          ³ nAt      - Linha do listbox                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ A140AtuDet                                                 ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function RetDetLine( aListDet,nAt)
Local aRet := {}
Local nX:= 0
For nX:= 1 to len(aListDet[nAt])
	aadd(aRet,aListDet[nAt,nx])
Next nX
Return aRet

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³ A140Impri ³ Autor ³Alexandre Inacio Lemes³ Data ³22/03/2004³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³ Efetua a chamada do relatorio padrao ou do usuario         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ ExpX1 := A140Impri( ExpC1, ExpN1, ExpN2 )                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpC1 -> Alias do arquivo                                  ³±±
±±³          ³ ExpN1 -> Recno do registro                                 ³±±
±±³          ³ ExpN2 -> Opcao do Menu                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ ExpX1 -> Retorno do relatorio                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR170                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

Function A140Impri( cAlias, nRecno, nOpc )

Local xRet := a103Impri( cAlias, nRecno, nOpc )

Pergunte("MTA140",.F.)

Return( xRet )
/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³A140EstCla ³ Autor ³Patricia A. Salomao   ³ Data ³01/08/2005³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Estorno da Classificacao da Nota Fiscal.                    ³±±
±±³          ³Executa a funcao de exclusao do MATA103;Porem, nao exclui o ³±±
±±³          ³SD1/SF1;Apenas limpa o conteudo os campos D1_TES e F1_STATUS³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ ExpX1 := A140ExcCla( ExpC1, ExpN1, ExpN2 )                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpC1 -> Alias do arquivo                                  ³±±
±±³          ³ ExpN1 -> Recno do registro                                 ³±±
±±³          ³ ExpN2 -> Opcao Selecionada                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T.                                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß*/
Function A140EstCla( cAlias, nRecno, nOpc )

If SF1->F1_STATUS != "A"
    Help("",1,"A140ESTORN")
ElseIf SF1->F1_TIPO $ "NDB"
	If !Empty(SF1->F1_CHVNFE) .AND. SF1->F1_FORMUL == "S"
		Help("",1,"A140ESFORP")
	Else
		A103NFiscal(cAlias,nRecno,5,,.T.)
	EndIf
Else
	Help("",1,"A140NCLASS")
EndIF

Return .T.

/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³a140Desc   ³ Autor ³Gustavo G. Rueda      ³ Data ³30/03/2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Funcao para atualizar o valor do DESCONTO no rodapeh quando ³±±
±±³          ³ digitamos o campo D1_DESC ou D1_VALDESC.                   ³±±
±±³          ³Para atualizar de acordo com o campo:                       ³±±
±±³          ³ - D1_DESC eh necessario criar o seguinte gatilho junto com ³±±
±±³          ³   padroes do sistema.                                      ³±±
±±³          ³   X7_CAMPO = D1_DESC                                       ³±±
±±³          ³   X7_REGRA = M->D1_VALDESC := IIF(A140DESC(M->D1_VALDESC), ³±±
±±³          ³              M->D1_VALDESC, M-D1_VALDESC)				  ³±±
±±³          ³   X7_CDOMIN = D1_VALDESC                                   ³±±
±±³          ³ - D1_VALDESC eh necessario inserir a seguinte validacao no ³±±
±±³          ³   SX3: A140DESC(M->D1_VALDESC)                             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A140DESC(nValDesc)                                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³nValDesc -> Valor do desconto do item                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T.                                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß*/
Function a140Desc (nValDesc)
	Eval (bRefresh,,,,nValDesc)
Return (.T.)
/*/
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³Ma140DelIt ³ Autor ³Gustavo G. Rueda      ³ Data ³30/03/2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Funcao para atualizar o valor do DESCONTO e do TOTAL no     ³±±
±±³          ³ rodapeh quando marcamos como deletado determinado item.    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ Ma140DelIt ()                                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T.                                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß*/
Function Ma140DelIt ()
Local	aTotal		:=	{0,0,0}
Local	aDespesa	:=	{0,0,0,0,0,0,0,0}
Local 	nPProduto   := GetPosSD1("D1_COD")
Local 	lRet := .T.

Static 	lPermHlp := .F.
	
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Verifica se o usuario tem permissao de exclusao. ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ	
	If IsInCallStack("MATA140")
		If !(lRet := MaAvalPerm(1,{aCols[n][nPProduto],"MTA140",5})) .And. !lPermHlp
			Help(,,1,'SEMPERM')
			lPermHlp := .T.
		Else
			lPermHlp := .F.
		EndIf
	EndIf
	
	If lRet	
		Ma140Total(aTotal,aDespesa)
		Eval (bRefresh)
	EndIf
Return lRet 

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³MenuDef   ³ Autor ³ Fabio Alves Silva     ³ Data ³01/11/2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³ Utilizacao de menu Funcional                               ³±±
±±³          ³                                                            ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³Array com opcoes da rotina.                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Parametros do array a Rotina:                               ³±±
±±³          ³1. Nome a aparecer no cabecalho                             ³±±
±±³          ³2. Nome da Rotina associada                                 ³±±
±±³          ³3. Reservado                                                ³±±
±±³          ³4. Tipo de Transação a ser efetuada:                        ³±±
±±³          ³    1 - Pesquisa e Posiciona em um Banco de Dados           ³±±
±±³          ³    2 - Simplesmente Mostra os Campos                       ³±±
±±³          ³    3 - Inclui registros no Bancos de Dados                 ³±±
±±³          ³    4 - Altera o registro corrente                          ³±±
±±³          ³    5 - Remove o registro corrente do Banco de Dados        ³±±
±±³          ³5. Nivel de acesso                                          ³±±
±±³          ³6. Habilita Menu Funcional                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³   DATA   ³ Programador   ³Manutencao efetuada                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³               ³                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

Static Function MenuDef()     
Local aRotAdic := {}  
PRIVATE aRotina	:= {	{ STR0000	,"AxPesqui"		, 0 , 1, 0, .F.},; //"Pesquisar"
						{ STR0001	,"A140NFiscal"	, 0 , 2, 0, nil},; //"Visualizar"
						{ STR0002	,"A140NFiscal"	, 0 , 3, 0, nil},; //"Incluir"
						{ STR0003	,"A140NFiscal"	, 0 , 4, 0, nil},; //"Alterar"
						{ STR0004	,"A140NFiscal"	, 0 , 5, 0, nil},; //"Excluir"
						{ STR0005	,"A140Impri"  	, 0 , 4, 0, nil},; //"Imprimir"
						{ STR0033	,"A140EstCla" 	, 0 , 5, 0, nil},; //"Estorna Classificacao"
						{ STR0006	,"A103Legenda"	, 0 , 2, 0, .F.},; 	//"Legenda"
						{ STR0067 ,"MsDocument", 0 , 4, 0, nil}}	//"Conhecimento"
                              
AADD(aRotina,{ OemToAnsi(STR0064),"A103Contr" 	, 0 , 2, 0, nil})//"Rastr.Contrato" 

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Ponto de entrada utilizado para inserir novas opcoes no array aRotina  ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ExistBlock("MTA140MNU")
	ExecBlock("MTA140MNU",.F.,.F.)
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//| Adiciona rotinas ao aRotina                                  |
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If ExistBlock( "MT140ROT" )
	aRotAdic := ExecBlock( "MT140ROT",.F.,.F.)
	If ValType( aRotAdic ) == "A"
		AEval( aRotAdic, { |x| aadd( aRotina, x ) } )
	EndIf
EndIf      
Return(aRotina) 

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³MaCols140 ³ Autor ³ Liber De Esteban      ³ Data ³ 10/01/07 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Montagem do aCols para GetDados.                            ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³MaCols140()                                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros|-cAliasSD1 ->Alias do SD1.                                  ³±±
±±³          ³-aRecSD1 -> Array com registros do SD1.                     ³±±
±±³          ³-bWhileSD1 -> Bloco com condicao para While.                ³±±
±±³          ³-nCounterSD1 -> Contador de registros do SD1, para o caso de³±±
±±³          ³nao estar usando query.                                     ³±±
±±³          ³-lQuery -> Flag de identificacao se esta usando query.      ³±±
±±³          ³-l140Inclui -> Flag que identifica se operacao e inclusao.  ³±±
±±³          ³-l140Visual -> Flag que identifica se operacao e inclusao.  ³±±
±±³          ³-lContinua -> Flag que identifica se deve continuar proc.   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

Static Function MaCols140(cAliasSD1,bWhileSD1,aRecOrdSD1,aRecSD1,aPedC,lItSD1Ord,lQuery,l140Inclui,l140Visual,lContinua,l140Exclui,l140Altera)
Local nPosPc	  := 0
Local nY 		  := 0
Local nCountSD1 := 1

If !Empty(aHeadSD1)
	aHeader := aClone(aHeadSD1)
EndIf

If l140Inclui
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Faz a montagem de uma linha em branco no aCols.              ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	aadd(aCols,Array(Len(aHeader)+1))
	For nY := 1 To Len(aHeader)
		If Trim(aHeader[nY][2]) == "D1_ITEM"
			aCols[1][nY] 	:= StrZero(1,Len((cAliasSD1)->D1_ITEM))
		Else
			If AllTrim(aHeader[nY,2]) == "D1_ALI_WT"
				aCOLS[Len(aCols)][nY] := "SD1"
			ElseIf AllTrim(aHeader[nY,2]) == "D1_REC_WT"
				aCOLS[Len(aCols)][nY] := 0
			Else
				aCols[1][nY] := CriaVar(aHeader[nY][2])
			EndIf
		EndIf
		aCols[1][Len(aHeader)+1] := .F.
	Next nY
Else

	While Eval( bWhileSD1 )
	
		If !lQuery .And. (lItSD1Ord .Or. ALTERA)
		
			If nCountSD1 == 1
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Este procedimento eh necessario para fazer a montagem        ³
				//³ do acols na ordem ITEM + COD quando classificacao em CDX     ³
				//³ e o parametro MV_PAR03 estiver para ITEM                     ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				aRecOrdSD1 := {}
				While ( !Eof().And. lContinua .And. ;
						(cAliasSD1)->D1_FILIAL== xFilial("SD1") .And. ;
						(cAliasSD1)->D1_DOC == cNFiscal .And. ;
						(cAliasSD1)->D1_SERIE == SF1->F1_SERIE .And. ;
						(cAliasSD1)->D1_FORNECE == SF1->F1_FORNECE .And. ;
						(cAliasSD1)->D1_LOJA == SF1->F1_LOJA )
	
					AAdd( aRecOrdSD1, { ( cAliasSD1 )->D1_ITEM + ( cAliasSD1 )->D1_COD, ( cAliasSD1 )->( Recno() ) } )
	
					( cAliasSD1 )->( dbSkip() )
	
				EndDo
	
				ASort( aRecOrdSD1, , , { |x,y| y[1] > x[1] } )
	
				bWhileSD1 := { || nCountSD1 <= Len( aRecOrdSD1 ) .And. lContinua  }
			EndIf
			
			If !lQuery .And. (lItSD1Ord .Or. ALTERA)
				SD1->( dbGoto( aRecOrdSD1[ nCountSD1, 2 ] ) )
			EndIf

		EndIf

		If (cAliasSD1)->D1_TIPO == SF1->F1_TIPO
			If Empty((cAliasSD1)->D1_TES)
				//-- Impede a alteracao/exclusao da PreNota com Servico de WMS jah executado
				If IntWMS() .And. (l140Exclui .Or. l140Altera)
					If !WmsAvalSD1(Iif(l140Altera,"6","7"),cAliasSD1,,,,.T.)
						lContinua := .F.
						Exit
					EndIf
				EndIf
					If lQuery
					aadd(aRecSD1,(cAliasSD1)->SD1RECNO)
				Else
					aadd(aRecSD1,RecNo())
				EndIf

				If !l140Visual
					If !Empty((cAliasSD1)->D1_PEDIDO)
						nPosPC := aScan(aPedC,{|y| y[1] == (cAliasSD1)->D1_PEDIDO+(cAliasSD1)->D1_ITEMPC})
						If nPosPc > 0
							aPedC[nPosPc,2] += (cAliasSD1)->D1_QUANT
						Else
							aadd(aPedC,{(cAliasSD1)->D1_PEDIDO+(cAliasSD1)->D1_ITEMPC,(cAliasSD1)->D1_QUANT})
						EndIf
					EndIf
				EndIf
				aadd(aCols,Array(Len(aHeader)+1))
				For nY := 1 to Len(aHeader)
					If ( aHeader[nY][10] != "V")
						aCols[Len(aCols)][nY] := FieldGet(FieldPos(aHeader[nY][2]))
					Else
						If AllTrim(aHeader[nY,2]) == "D1_ALI_WT"
							aCOLS[Len(aCols)][nY] := "SD1"
						ElseIf AllTrim(aHeader[nY,2]) == "D1_REC_WT"
							aCOLS[Len(aCols)][nY] := If(lQuery,(cAliasSD1)->SD1RECNO,(cAliasSD1)->(RecNo()))
						Else
							aCols[Len(aCols)][nY] := CriaVar(aHeader[nY][2])
						EndIf
					EndIf
					aCols[Len(aCols)][Len(aHeader)+1] := .F.
				Next nY
			Else
				SetKey( VK_F6, Nil ) //desativa tecla F6 ao exibir Alert
				Help(" ",1,"A140CLASSI")				
				lContinua := .F.
			EndIf
		EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Efetua skip na area SD1 ( regra geral ) ou incrementa o contador ³
		//³ quando ordem por ITEM + CODIGO DE PRODUTO                        ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If !lQuery .And. (lItSD1Ord .Or. ALTERA)
			nCountSD1++
		Else
			dbSelectArea(cAliasSD1)
			dbSkip()
		EndIf
	EndDo  
EndIf

Return 

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³A140FldOk ³ Autor ³ Allyson B. D. Freitas ³ Data ³09/01/2012³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Valida permissao de usuarios                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MsGetDados do MATA140                                      ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A140FldOk()
Local cFieldSD1 := ReadVar()
Local cFieldEdit:= SubStr(cFieldSD1,4,Len(cFieldSD1))
Local nPProduto := GetPosSD1("D1_COD")
Local lEdita    := .T.

If Altera
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Verifica se o usuario tem permissao de alteracao. ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If cFieldEdit $ "D1_COD"		
		If !(lEdita := MaAvalPerm(1,{cCampo,"MTA140",5}) .And. MaAvalPerm(1,{aCols[n][nPProduto],"MTA140",3}))
			Help(,,1,'SEMPERM')
		EndIf
	Else		
		If !(	lEdita := MaAvalPerm(1,{aCols[n][nPProduto],"MTA140",4}))
			Help(,,1,'SEMPERM')
		EndIf
	EndIf
EndIf
	
Return lEdita   

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Função    ³MA140DIV1 ³ Prog. ³ TOTVS                 ³Data  ³27/04/11  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Selecao de Divergencias da Nota Fiscal Entrada              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MATA140                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
                                                
Static Function _MA140Div1()     
       
Local aArea		:= GetArea()
Local oDlg
Local cTitulo  := STR0084 //-- "Selecao da Natureza das Divergencias"
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

//+-------------------------------------+
//| Carrega o vetor conforme a condicao |
//+-------------------------------------+
IF  (Len( _aDivPNF ) == 0)
	While !Eof() .And. COF_FILIAL == xFilial("COF")
	   aAdd(_aDivPNF, { if(Inclui,	lMark, CA040VER(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,COF->COF_CODIGO)) , ;
	   							COF_DESCRI,;
	   							COF_CODIGO})
	   dbSkip()
	End
ENDIF	                        

//+-----------------------------------------------+
//| Monta a tela para usuario visualizar inclusao |
//+-----------------------------------------------+
If Len( _aDivPNF ) == 0
   Aviso( cTitulo, STR0079, {"Ok"} )
   Return
Endif

DEFINE MSDIALOG oDlg TITLE cTitulo FROM 0,0 TO 240,500 PIXEL
   
@ 10,10 LISTBOX oLbx FIELDS HEADER " ", STR0081 ;
   SIZE 230,095 OF oDlg PIXEL ON dblClick(_aDivPNF[oLbx:nAt,1] := !_aDivPNF[oLbx:nAt,1])

oLbx:SetArray( _aDivPNF )                                       

oLbx:bLine := {|| { Iif(_aDivPNF[oLbx:nAt,1],oOk,oNo),  ;
						 _aDivPNF[oLbx:nAt,2]}}

//+----------------------------------------------------------------
//| ... utilizando a função aEval()
//+----------------------------------------------------------------
@ 110,10 CHECKBOX oChk1 VAR lChk1 PROMPT STR0082 SIZE 70,7 PIXEL OF oDlg ;
         ON CLICK( aEval( _aDivPNF, {|x| x[1] := lChk1 } ),oLbx:Refresh() )

@ 110,95 CHECKBOX oChk2 VAR lChk2 PROMPT STR0083 SIZE 70,7 PIXEL OF oDlg ;
         ON CLICK( aEval( _aDivPNF, {|x| x[1] := !x[1] } ), oLbx:Refresh() )

DEFINE SBUTTON FROM 107,213 TYPE 1 ACTION oDlg:End() ENABLE OF oDlg      

ACTIVATE MSDIALOG oDlg CENTER


RestArea(aArea)
Return()

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³IsTransFilºAutor  ³ Andre Anjos		 º Data ³  05/11/12   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Verifica se a pre-nota incluida e uma transferencia entre  º±±
±±º          ³ filiais através do cadastro do fornecedor.                 º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ MATA140                                                    º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function IsTransFil()
Local lRet     := .F.
Local aAreaSA2 := SA2->(GetArea())
Local aAreaSM0 := SM0->(GetArea())

If IsInCallStack("MATA310")	.or. IsInCallStack("MATA311")//-- Se chamada pela MATA310 - Transf. Filiais
	lRet := .T.
ElseIf IsInCallStack("COMXCOL") .or. IsInCallStack("MATA140I")	//-- Se chamada por TOTVS Colaboracao
	SA2->(dbSetOrder(1))
	SA2->(dbSeek(xFilial("SA2")+cA100For+cLoja))

	//-- Verifica pelo campo A2_FILTRF, que deve ter o codigo da filial
	If UsaFilTrf()	
		lRet := !Empty(SA2->A2_FILTRF)
	//-- Verifica pelo CNPJ no SIGAMAT
	Else
		SM0->(dbGoTop())
		While !SM0->(EOF())
			If AllTrim(SM0->M0_CGC) == AllTrim(SA2->A2_CGC)
				lRet := .T.
				Exit
			EndIf
			SM0->(dbSkip())
		End
		SM0->(RestArea(aAreaSM0))
	EndIf
	
	SA2->(RestArea(aAreaSA2))
EndIf

Return lRet


/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Funcao    ³A140Conhec³ Autor ³Alexandre Gimenez      ³ Data ³29/05/2013³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Chamada da visualizacao do banco de conhecimento            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³A140Conhec()                                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³.T.                                                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³                                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

Static Function A140Conhec()

Local aRotBack := AClone( aRotina )
Local nBack    := N

Private aRotina := {}

Aadd(aRotina,{STR0066,"MsDocument", 0 , 2}) //"Conhecimento"

MsDocument( "SF1", SF1->( Recno() ), 1 )

aRotina := AClone( aRotBack )
N := nBack

Return( .t. )

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Funcao    ³RetOpName³ Autor ³TOTVS                   ³ Data ³14/03/2014³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descrição ³Retorna o nome do Operador da Conferencia de Etiquetas      ³±±
±±³ na tabela CBE - Etiquetas Lidas                                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³RetOpName()                                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³cCodOp - codigo do operador da conferencia de etiquetas     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³cNomeOper - nome do operador                                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³                                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

Function RetOpName(cCodOp)
	
Local aArea := GetArea()
Local cNomeOper := ""
Local cAlias := "CB1"

DbSelectArea(cAlias)
(cAlias)->(DbSetOrder(1))

If (cAlias)->(DbSeek(xFilial("CB1")+cCodOp))
	cNomeOper := CB1->CB1_NOME
Endif
	
RestArea(aArea)
Return cNomeOper


//-------------------------------------------------------------------
/*/{Protheus.doc} A140NFORI() 
Faz a chamada da Tela de Consulta a NF original
@author taniel.silva
@since 16/10/2014
@version P12
/*/
//-------------------------------------------------------------------
Function A140NFORI()
Local nPosCod	:= GetPosSD1('D1_COD')
Local nPLocal	:= GetPosSD1('D1_LOCAL')
Local nPNFORI	:= GetPosSD1('D1_NFORI')
Local lRet    	:= .T.
Local cIndPres	:= ""
Local cCodA1U	:= ""
Local nRecSD2	:= 0
Local nRecSD1	:= 0
Local aArea		:= {}
Local nX		:= 0
Local nLinAtv	:= 0
Local aIndA1U	:= {}

If !cTipo $ 'DC'
	lRet := .F.
	Help('   ',1,'A140NFORI')
EndIf

If lRet 
	If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. cFormul == "S"
		cIndPres := SubStr(aInfAdic[16],1,1)
		cCodA1U	 := aInfAdic[17]

		For nX := 1 To Len(aCols)
			If !aCols[nX,Len(aCols[nX])] .And. !Empty(aCols[nX,nPNFORI])
				nLinAtv++
			Endif
		Next nX
	Endif
Endif

If lRet
	If Empty(Readvar())
		If cTipo == "D"
			F4NFORI(,,"M->D1_NFORI",cA100For,cLoja,aCols[n,nPosCod],"A100",aCols[n,nPLocal],@nRecSD2,,,cIndPres,cCodA1U,nLinAtv)
			If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. nRecSD2 > 0
				aArea := GetArea()
				DbSelectArea("SD2")
				SD2->(DbGoto(nRecSD2))
				aIndA1U			:= GetAdvFVal("SC5",{"C5_INDPRES","C5_CODA1U"},xFilial("SC5") + SD2->D2_CLIENTE + SD2->D2_LOJA + SD2->D2_PEDIDO,3)
				If Len(aIndA1U) > 0
					If !Empty(aIndA1U[1])
						aInfAdic[16] := aIndA1U[1]
					Endif
					If !Empty(aIndA1U[2])
						aInfAdic[17] := aIndA1U[2]
					Endif
				Endif
				Eval(bRefresh)
				RestArea(aArea) 
			Endif 

		ElseIf cTipo == "C" 
			F4COMPL(,,,cA100For,cLoja,aCols[n,nPosCod],"A100",@nRecSD1,"M->D1_NFORI",cIndPres,cCodA1U,nLinAtv) 
			If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. nRecSD1 > 0
				aArea := GetArea()
				DbSelectArea("SD1")
				SD1->(DbGoto(nRecSD1))
				aIndA1U			:= GetAdvFVal("SF1",{"F1_INDPRES","F1_CODA1U"},xFilial("SF1") + SD1->D1_DOC + SD1->D1_SERIE + SD1->D1_FORNECE + SD1->D1_LOJA + SD1->D1_TIPO,1)
				If Len(aIndA1U) > 0
					If !Empty(aIndA1U[1])
						aInfAdic[16] := aIndA1U[1]
					Endif
					If !Empty(aIndA1U[2])
						aInfAdic[17] := aIndA1U[2]
					Endif
				Endif
				Eval(bRefresh)
				RestArea(aArea)
			Endif
		EndIf
	Else
		Help('   ',1,'A103CAB')
	EndIf
EndIf
// Atualiza valores na tela
If Type( "oGetDados" ) == "O" 	
	oGetDados:oBrowse:Refresh()	
EndIf



Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc}A140ATUFRT
Função para atualizar e ratear o frete corretamente entre os itens 
do documento

@author Rodrigo M. Pontes
@since 21/06/16
@version P12.7
@return Nil
/*/
//-------------------------------------------------------------------

Function A140ATUFRT(nOpc,lAlt140,cPrd,cItem)

Local aArea	:= GetArea()
Local nX		:= 0
Local nPrd		:= 0
Local nPFrt	    := GetPosSD1("D1_VALFRE")
Local nI		:= 0

If nOpc == 1 .And. lAlt140 //Pega total de frete
	SD1->(DbGotop())
	SD1->(DbSetOrder(1))
	If SD1->(DbSeek(xFilial("SD1") + Padr(SF1->F1_DOC,TamSx3("F1_DOC")[1]) + Padr(SF1->F1_SERIE,TamSx3("F1_SERIE")[1]) + Padr(SF1->F1_FORNECE,TamSx3("F1_FORNECE")[1]) + Padr(SF1->F1_LOJA,TamSx3("F1_LOJA")[1]))) 
		While SD1->(!EOF()) .And. ;
				Padr(SF1->F1_DOC,TamSx3("F1_DOC")[1]) == Padr(SD1->D1_DOC,TamSx3("D1_DOC")[1]) .And. ;
				Padr(SF1->F1_SERIE,TamSx3("F1_SERIE")[1]) == Padr(SD1->D1_SERIE,TamSx3("D1_SERIE")[1]) .And. ;
				Padr(SF1->F1_FORNECE,TamSx3("F1_FORNECE")[1]) == Padr(SD1->D1_FORNECE,TamSx3("D1_FORNECE")[1]) .And. ;
				Padr(SF1->F1_LOJA,TamSx3("F1_LOJA")[1]) == Padr(SD1->D1_LOJA,TamSx3("D1_LOJA")[1])
				
			nI := aScan(aFrt140,{|x| x[1] == SD1->D1_COD})
			If nI == 0
				aAdd(aFrt140,{SD1->D1_COD,SD1->D1_VALFRE})
			Else
				aFrt140[nI,2] += SD1->D1_VALFRE
			Endif
			
			SD1->(DbSkip())
		Enddo
	Endif
Elseif nOpc == 2 //Ratear
	nVlrFrt140 := 0
	
	For nI := 1 To Len(aCols)
		If !aCols[nI,Len(aHeader)+1]
			If aCols[nI,GetPosSD1("D1_COD")] == cPrd .And. aCols[nI,GetPosSD1("D1_ITEM")] == cItem
				nPrd++
				
				If nPFrt > 0
					nVlrFrt140 += aCols[nI,nPFrt]
				Endif		
			Endif
		Endif
	Next nI
	
	nX := aScan(aFrt140,{|x| x[1] == cPrd})
	If nX > 0
		If nPFrt == 0 
			nVlrFrt140 := aFrt140[nX,2]/nPrd
		Else
			nVlrFrt140 := nVlrFrt140/nPrd
		Endif
	Endif
Endif

RestArea(aArea)

Return Iif(nOpc==1,.T.,nVlrFrt140)

/*/{Protheus.doc} UsaConfF
	Valida se utiliza a conferência física do ACD na pré nota
	@type  Static Function
	@author Gianluca Moreira
	@since 27/10/2022
/*/
Static Function UsaConfF(cTipo, cCliFor, cLoja)
	Local aArea      := GetArea()
	Local aAreaSA1   := SA1->(GetArea())
	Local aAreaSA2   := SA2->(GetArea())
	Local aAreas     := {aAreaSA1, aAreaSA2, aArea}
	Local cMVCONFFIS := SuperGetMV('MV_CONFFIS')
	Local cMVTPCONFF := SuperGetMV('MV_TPCONFF')
	Local lRet       := .F.

	If cMVCONFFIS == "S"
		If cTipo $ "DB"
			//Implementação futura - Após criar o campo A1_CONFFIS
			/*
			If SA1->(FieldPos('A1_CONFFIS')) > 0
				SA1->(DbSetOrder(1)) //A1_FILIAL+A1_COD+A1_LOJA
				If SA1->(MsSeek(FWXFilial('SA1')+cCliFor+cLoja))
					lRet := SA1->A1_CONFFIS <> "3" .And.; // Diferente de '3 - nao utiliza'
						((SA1->A1_CONFFIS == "0" .And. cMVTPCONFF == "1") .Or. SA1->A1_CONFFIS == "1")
				EndIf
			Else
				lRet := cMVTPCONFF == "1"
			EndIf
			*/
			lRet := cMVTPCONFF == "1"
		Else
			SA2->(DbSetOrder(1)) //A2_FILIAL+A2_COD+A2_LOJA
			If SA2->(MsSeek(FWXFilial('SA2')+cCliFor+cLoja))
				lRet := SA2->A2_CONFFIS <> "3" .And.; // Diferente de '3 - nao utiliza'
					((SA2->A2_CONFFIS == "0" .And. cMVTPCONFF == "1") .Or. SA2->A2_CONFFIS == "1")
			EndIf
		EndIf
	EndIf	

	AEval(aAreas, {|x| RestArea(x)})
Return lRet
