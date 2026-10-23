#INCLUDE "MATA116.CH" 
#INCLUDE "TBICONN.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.CH"    
      
#DEFINE ROTINA 		01 // Define a Rotina : 1-Inclusao / 2-Exclusao
#DEFINE TIPONF		02 // Considerar Notas : 1 - Compra , 2 - Devolucao
#DEFINE DATAINI		03 // Data Inicial para Filtro das NF Originais
#DEFINE DATAATE		04 // Data Final para Filtro das NF originais
#DEFINE FORNORI		05 // Cod. Fornecedor para Filtro das NF Originais
#DEFINE LOJAORI		06 // Loja Fornecedor para Fltro das NF Originais
#DEFINE FORMUL		07 // Utiliza Formulario proprio ? 1-Sim,2-Nao
#DEFINE NUMNF		08 // Num. da NF de Conhecimento de Frete
#DEFINE SERNF		09 // Serie da NF de COnhecimento de Frete
#DEFINE FORNECE		10 // Codigo do Fornecedor da NF de FRETE
#DEFINE LOJA		11 // Loja do Fornecedor da NF de Frete
#DEFINE TES			12 // Tes utilizada na Classificacao da NF 
#DEFINE VALOR		13 // Valor total do Frete sem Impostos
#DEFINE UFORIGEM	14 // Estado de Origem do Frete
#DEFINE AGLUTINA	15 // Aglutina Produtos : .T. , .F.
#DEFINE BSICMRET	16 // Base do Icms Retido
#DEFINE VLICMRET	17 // Valor do Icms Retido
#DEFINE FILTRONF    18 // Filtra nota com conhecimento frete .F. , .T.
#DEFINE ESPECIE	    19 // Especie da Nota Fiscal

Static cMayUse
Static lLGPD  	:= FindFunction("SuprLGPD") .And. SuprLGPD() 

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ MATA116  ³ Autor ³ Edson Maricate         ³ Data ³14.03.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Programa de Digitacao de Conhecimento de Frete              ³±±
±±³          ³ Utiliza a funcao MATA103 p/ gerar a Nota Fiscal de Entrada  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Generico                                                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ ATUALIZACOES SOFRIDAS DESDE A CONSTRUCAO INICIAL.                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ PROGRAMADOR  ³ DATA   ³ BOPS ³  MOTIVO DA ALTERACAO                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³              ³        ³      ³                                         ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function MATA116(xAutoCab,xAutoItens,lAutoGFE,lPreNota,aRatcc)

Local lInclui := .T.
Local lRet	  := .T.

PRIVATE cFilUF		:= ""
PRIVATE lIntermed	:= A116CPOINTER()

Default lPreNota := .F.
&("M->F1_CHVNFE") := "" 

//Checa a assinatura dos fontes complementares estão corretos.
lRet := A116ChkSig()

If lRet
	While lInclui 
		lRet := Mata116A(xAutoCab,xAutoItens,@lInclui,lAutoGFE,lPreNota,aRatcc)
	EndDo
Endif

Return lRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ MATA116A ³ Autor ³ Edson Maricate         ³ Data ³14.03.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Programa de Digitacao de Conhecimento de Frete              ³±±
±±³          ³ Utiliza a funcao MATA103 p/ gerar a Nota Fiscal de Entrada  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ Generico                                                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ ATUALIZACOES SOFRIDAS DESDE A CONSTRUCAO INICIAL.                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ PROGRAMADOR  ³ DATA   ³ BOPS ³  MOTIVO DA ALTERACAO                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³              ³        ³      ³                                         ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function Mata116A(xAutoCab,xAutoItens,lInclui,lAutoGFE,lPreNota,aRatcc)

LOCAL aIndexSF1 	:= {}
Local aAreaSF1		:= SF1->(GetArea())
LOCAL cFiltraSF1 	:= ""
LOCAL cQrySF1    	:= ""
LOCAL cRetPE 	 	:= ""
LOCAL cNFExc		:= ""
LOCAL cSerieExc  	:= ""
LOCAL cFornExc   	:= ""
LOCAL cLojaExc  	:= ""
LOCAL nPosCH        := aScan(xAutoCab,{|x| x[1] == "F1_CHVNFE" })
LOCAL nPosCte       := aScan(xAutoCab,{|x| x[1] == "F1_TPCTE" })
Local nPosNat       := aScan(xAutoCab,{|x| x[1] == "E2_NATUREZ" })
Local nPosPicm 		:= aScan(xAutoCab,{|x| x[1] == "DT_PICM" })
//Local nPosDesc 		:= aScan(xAutoCab,{|x| x[1] == "F1_DESCONT" })
LOCAL lContinua  	:= .T.  
LOCAL lIntGFE		:= SuperGetMv("MV_INTGFE",.F.,.F.)
LOCAL lMsgGFE     	:= SuperGetMv("MV_INTGFE2",.F.,"2") == "1" .And. SuperGetMv("MV_GFEI10",.F.,"1") == "2"
LOCAL lGFE116Exc	:= SuperGetMv("MV_INTGFE3",.F.,.F.) //Permite execução da execauto mesmo quando o MV_INTGFE = .T.
Local lColab 		:= !Empty(xAutoCab) .And. aScan(xAutoCab, {|x| x[1] == "COLAB" .And. x[2] == "S"}) > 0
Local nx := 0 
Local lMT116QRY   	:= .F.
//Define Array contendo as Rotinas a executar do programa
//----------- Elementos contidos por dimensao ------------
//1. Nome a aparecer no cabecalho
//2. Nome da Rotina associada
//3. Usado pela rotina
//4. Tipo de Transa‡„o a ser efetuada
//   1 - Pesquisa e Posiciona em um Banco de Dados
//   2 - Simplesmente Mostra os Campos
//   3 - Inclui registros no Bancos de Dados
//   4 - Altera o registro corrente
//   5 - Remove o registro corrente do Banco de Dados
Private bFiltraBrw   := {|| Nil}
Private cCadastro    := STR0001 //"Nota Fiscal de Conhecimento de Frete"
Private l116Auto     := (xAutoCab <> nil .And. xAutoItens <> nil)
Private aAutoCab     := aClone(xAutoCab)
Private aAutoItens   := aClone(xAutoItens)
Private aParametros  := {}
Private aRotina      := {}
Private INCLUI       := .F.
Private ALTERA       := .F.
Private aBackSDE     := {}    
Private aNFEDanfe    := {}
Private aDanfeComp   := {}
Private dEmisOld     := ""
Private cCA100ForOld := ""
Private cCondicaoOld := ""
Private cEspecie2	 := ""
Private cChvNFE      := "" //Campo chave Ct-e enviado do GFE, via rotina GFEA065      
Private cTPCTE       := "" //Campo tipo Ct-e enviado do GFE, via rotina GFEA065 
Private aRecMark 	 := {}
Private l116OriDest	 := SF1->(FieldPos("F1_UFORITR")) > 0 .And. SF1->(FieldPos("F1_MUORITR")) > 0 .And. SF1->(FieldPos("F1_UFDESTR")) > 0 .And. SF1->(FieldPos("F1_MUDESTR")) > 0


// Variaveis utilizadas no MATA140
Private nVlrFrt140	:= 0
Private aFrt140		:= {}
Private aCompFutur	:= {}

Private cUfOrig     := "" //Variável criada para ser lida pelo gatilho do campo D1_OPER e quando o MATA103 é executado por essa função, ela estava sendo declarada novamente
Private cUfOri		:= "" //Variável criada para ser lida pelo fonte MATA103x, pois a variável cUFOrig já sofreu alteração até ser lida por esse fonte.
Private aInfAdic	:= {}
Private nInfAdic	:= 0
Private lFormulS	:= .F.

Default lAutoGFE := .F.
Default lPreNota := .F.

aRotina := MenuDef() 

If cPaisLoc <> "BRA"
	lContinua := .F.
	Help(" ",1,"A116TPFRETE",,STR0021,1,0) //"Use a rotina de inclusao de notas de entrada, selecionado o tipo FRETE, para incluir notas fiscais de conhecimento de frete. " //"Rotina fora de uso"
ElseIf lIntGFE .And. !( FWIsInCallStack( "FWUMESSAGE" ) .Or. FWIsInCallStack( "FWFORMEAI" ) .Or. IsInCallStack("GFEA065In") .Or. IsInCallStack("GFEA100In") .Or. IsInCallStack("ImpXML_Cte")) 
	If l116Auto
    	If !lAutoGFE .And. !lMsgGFE .And. !lGFE116Exc
    		lContinua := .F.
			HELP(" ",1,STR0053 + Chr(13))
		EndIf
	ElseIf IIF( lMsgGFE ,.F. ,!MsgYesNo(STR0053 + Chr(13) + STR0054,STR0018) ) //"Com a integração ativa entre o ERP Protheus e o TOTVSGFE, os documentos de Transporte devem ser lançados pelo TOTVSGFE! "/"Confirma o lançamento? ")
		lContinua := .F.
	EndIf
EndIf  

If lContinua
	//Chama a tela de configuracao com os Dados da Nota Fiscal
	If ExistBlock("MT116TEL")
		lContinua := ExecBlock("MT116TEL",.F.,.F.)
		If ValType(lContinua) <> "L"
			lContinua := .T.
		EndIf
	Else
		If !A116Setup(@aParametros)
			lContinua := .F.
		EndIf
	EndIf
EndIf

If lContinua
	If !( l116Auto )
		dDataIni	   := aParametros[DATAINI]
		dDataFim	   := aParametros[DATAATE]
		nRotina        := aParametros[ROTINA]
		cFornOri	   := aParametros[FORNORI]
		cLojaOri	   := aParametros[LOJAORI]
		nTipoOri	   := aParametros[TIPONF]
		lAglutProd     := aParametros[AGLUTINA]
		cUfOrig		   := aParametros[UFORIGEM]
		cUFOrigP	   := aParametros[UFORIGEM]
		lFiltroNF      := aParametros[FILTRONF]
		cEspecie2	   := aParametros[ESPECIE]		
		aRotina := MenuDef()
	Else
		dDataIni	   := aAutoCab[1,2]
		dDataFim	   := aAutoCab[2,2]
		nRotina        := aAutoCab[3,2]
		cFornOri	   := aAutoCab[4,2]
		cLojaOri	   := aAutoCab[5,2]
		nTipoOri	   := aAutoCab[6,2]
		lAglutProd     := If(aAutoCab[7,2]==1,.T.,.F.)
		cUfOrig        := aAutoCab[8,2]
		cUFOrigP	   := aAutoCab[8,2]
		lFiltroNF      := .F.
		aRotina := MenuDef()
		If nPosCH > 0 
		   cChvNFE := aAutoCab[nPosCH][2] //Chave CT-e
		EndIF
		IF nPosCte > 0 
		   cTPCTE := aAutoCab[nPosCte][2] //Tipo chave CT-e
	    EndIf
	EndIf

	cUfOri := cUfOrig //preenchimento para leitura posterior na função NfeCabOk
     
	If nRotina==2
		If ( l116Auto )
			aParametros[VALOR]	  := aAutoCab[09,2]
			aParametros[FORMUL]	  := aAutoCab[10,2]
			aParametros[NUMNF]	  := aAutoCab[11,2]
			aParametros[SERNF]	  := aAutoCab[12,2]
			aParametros[LOJA]	  := aAutoCab[14,2]
			aParametros[TES]	  := aAutoCab[15,2]
			aParametros[FORNECE]  := aAutoCab[13,2]
			aParametros[BSICMRET] := aAutoCab[16,2]
			aParametros[VLICMRET] := aAutoCab[17,2] 
		EndIf
	EndIf
	
	If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. aParametros[FORMUL] == 2 .And. nRotina == 2
		lFormulS := .T.
	Endif
	//Inicializa o filtro
	dbSelectArea("SF1")
	dbSetOrder(1)
	cFiltraSF1	:= 'F1_FILIAL=="'+xFilial("SF1")+'".And.'
	cQrySF1     := "F1_FILIAL='"+xFilial("SF1")+"' AND "
	
	If !Empty(cFornOri) .And. !Empty(cLojaOri) .And. !lColab
		cFiltraSF1	+= ' F1_FORNECE=="'+cFornOri+'".And.F1_LOJA=="'+cLojaOri+'" .And. '
		cQrySF1     += " F1_FORNECE='"+cFornOri+"' AND F1_LOJA = '"+cLojaOri+"' AND "
	Endif	
	
	If !lColab	
		cFiltraSF1 += 'DTOS(F1_DTDIGIT)>="'+DTOS(dDataIni)+'".And.DTOS(F1_DTDIGIT)<="'+DTOS(dDataFim)+'".And.'
		cQrySF1    += "F1_DTDIGIT>='"+DTOS(dDataIni)+"' AND F1_DTDIGIT <= '"+DTOS(dDataFim)+"' AND "
	Endif
	
	If nRotina==1
		cFiltraSF1	+= 'F1_TIPO=="C".And.F1_ORIGLAN=="F "'
		cQrySF1     += "F1_TIPO='C' AND F1_ORIGLAN='F '"
	ElseIf lColab
		cFiltraSF1	+= 'F1_TIPO$"NCDB"'
		cQrySF1 	+= "F1_TIPO IN('N','C','D','B') "
	Else
		cFiltraSF1	+= 'F1_TIPO$"'+If(nTipoOri==1,"NC","BD")+'"'
		If nTipoOri == 1
			cQrySF1 += "F1_TIPO IN ('N','C') " 
		Else
			cQrySF1 += "F1_TIPO IN('B','D') "
		EndIf
		If lFiltroNF
			cFiltraSF1 +='.AND.F1_ORIGLAN<>"F "'
			cQrySF1    +=" AND F1_ORIGLAN <> 'F ' "
		EndIf
	Endif
	
	If ExistBlock("MT116FTR")
		cRetPE := ExecBlock("MT116FTR",.F.,.F.,)
		If ValType(cRetPE) == "C"
			cFiltraSF1 += cRetPE
		EndIf
	EndIf
	
	If ExistBlock("MT116QRY")
		cRetPE := ExecBlock("MT116QRY",.F.,.F.,)
		If ValType(cRetPE) == "C"
			lMT116QRY := .T.
			cQrySF1	+= cRetPE
		EndIf
	EndIf
	
	//Filtro apenas para o MarkBrow
	If nRotina <> 1
		If !Empty(cFiltraSF1) .Or. !Empty(cQrySF1)
			bFiltraBrw 	:= {|x| IIf(x==Nil,FilBrowse("SF1",@aIndexSF1,@cFiltraSF1),cQrySF1)}
			Eval(bFiltraBrw)
		EndIf
	Endif
	
	dbSelectArea("SF1")
	If BOF() .And. EOF()
		If ( l116Auto )
			lInclui := .F.
			lContinua := .F.
		EndIf
		HELP(" ",1,"RECNO", STR0059)
	Else
		If ( l116Auto )
			If nRotina == 1 .And. Len(aAutoCab) > 0		// Se for exclusao, posiciona SF1 para garantir exclusao
				cNFExc		:= PADR(aAutoCab[11,2],TamSX3("F1_DOC")[1])
				cSerieExc	:= PADR(aAutoCab[12,2],SerieNfId("SF1",6,"F1_SERIE"))
				cFornExc	:= PADR(aAutoCab[13,2],TamSX3("F1_FORNECE")[1])
				cLojaExc	:= PADR(aAutoCab[14,2],TamSX3("F1_LOJA")[1])
				SF1->(dbClearFilter())
				SF1->(MsSeek(xFilial("SF1")+cNFExc+cSerieExc+cFornExc+cLojaExc+"C"))
			EndIf
			lContinua := A116Inclui("SF1",,1,,,lPreNota,aRatcc,nPosNat,nPosPicm)				
			lInclui := .F.
		Else
			If nRotina == 1
				mBrowse( 6, 1,22,75,"SF1",,,,,,,,,,,,,,cQrySF1,,,,cFiltraSF1)
			Else
				MarkBrow("SF1","F1_OK","",,,,"a116Mark('A')",,,,"a116Mark()",,IF(lMT116QRY,cQrySF1,nil))
				cMarca := ThisMark()
				dbSelectArea("SF1")
			    For nX:=1 To Len(aRecMark) 
					SF1->( dbGoto( aRecMark[nX] ) )   
					If SimpleLock("SF1",.F.)
				        SF1->F1_OK      := Space(Len(SF1->F1_OK))   
						MsUnLock()
			        EndIf
			    Next nX
				SF1->(dbCommit())
			EndIf
		EndIf
	EndIf
	//Ponto de Entrada apos a escolha das notas
	If ExistBlock('MT115MRK')
		ExecBlock('MT115MRK', .F., .F.) 
	EndIf
	
	If Len(aIndexSF1) > 0
		EndFilBrw("SF1",aIndexSF1) 
		RetIndex("SF1")
		
		SET FILTER TO
	EndIf
Else
	lInclui := .F.
	lContinua := .F.
EndIf

SF1->(dbClearFilter())
RestArea(aAreaSF1)

Return lContinua

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116Setup³ Autor ³ Edson Maricate         ³ Data ³17.11.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Faz a montagem da tela de parametros do MATA116.            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpA1 : [1] Define a Rotina : 1-Inclusao / 2-Exclusao       ³±±
±±³          ³        [2] Considerar Notas : 1 - Compra , 2 - Devolucao   ³±±
±±³          ³        [3] Data Inicial para Filtro das NF Originais       ³±±
±±³          ³        [4] Data Final para Filtro das NF originais         ³±±
±±³          ³        [5] Cod. Fornecedor para Filtro das NF Originais    ³±±
±±³          ³        [6] Loja Fornecedor para Fltro das NF Originais     ³±±
±±³          ³        [7] Utiliza Formulario proprio ? 1-Sim,2-Nao        ³±±
±±³          ³        [8] Num. da NF de Conhecimento de Frete             ³±±
±±³          ³        [9] Serie da NF de COnhecimento de Frete            ³±±
±±³          ³        [10]Codigo do Fornecedor da NF de FRETE             ³±±
±±³          ³        [11]Loja do Fornecedor da NF de Frete               ³±±
±±³          ³        [12]Tes utilizada na Classificacao da NF            ³±±
±±³          ³        [13]Valor total do Frete sem Impostos               ³±±
±±³          ³        [14]Estado de Origem do Frete                       ³±±
±±³          ³        [15]Aglutina Produtos : .T. , .F.                   ³±±
±±³          ³        [16]Base do Icms Retido                             ³±±
±±³          ³        [17]Valor do Icms Retido                            ³±±
±±³          ³        [18]Filtra nota com conhecimento frete 1-Nao , 2-Sim³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116,SIGACOM,SIGAEST                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

Function A116Setup(aParametros)

Local aCombo1	    := {STR0006,STR0007} //"Incluir NF de Conhec. Frete"###"Excluir NF de Conhec. Frete"
Local aCombo2	    := {STR0008+" / "+STR0067,STR0009} //"NF Normal"###"NF Devol./Benef."
Local aCombo3	    := {STR0010,STR0011} //"NÃo"###"Sim"
Local aCombo4	    := {STR0011,STR0010} //"Sim"###"NÃo"
Local aCombo5	    := {STR0010,STR0011} //"NÃo"###"Sim"
Local aCliFor	    := {{STR0012,"FOR"},{STR0013,"SA1"}} //"Fornecedor"###"Cliente"
Local nCombo1	    := 1
Local nCombo2	    := If(l116Auto,aAutoCab[6,2],1)
Local nCombo3	    := If(l116Auto,aAutoCab[10,2],1)
Local nCombo4	    := 1
Local nCombo5	    := 1
Local n116Valor	    := 0
Local n116BsIcmret	:= 0
Local n116VlrIcmRet	:= 0
Local nOpcAuto      := If(l116Auto, If(aAutoCab[3,2]==1 ,2,1),1) //1= Exclusao - 2= Inclusao
Local nX            := 0
Local d116DataDe    := dDataBase - 90
Local d116DataAte   := dDataBase
LocaL lMT116VTP:= .F.

Local c116Combo1    := aCombo1[nCombo1]
Local c116Combo2    := aCombo2[1]
Local c116Combo3    := aCombo3[1]
Local c116Combo4	:= aCombo4[1]
Local c116Combo5    := aCombo5[1]
Local c116FornOri   := If(l116Auto,aAutoCab[4,2],CriaVar("F1_FORNECE",.F.))
Local c116LojaOri   := If(l116Auto,aAutoCab[5,2],CriaVar("F1_LOJA",.F.))
Local c116NumNF	    := If(l116Auto,aAutoCab[11,2],CriaVar("F1_DOC",.F.))
Local c116SerNF	    := If(l116Auto,aAutoCab[12,2],CriaVar(iif(SerieNfId("SF1",3,"F1_SERIE")=='F1_SDOC','F1_SDOC','F1_SERIE'),.F.))
Local c116Fornece   := If(l116Auto,aAutoCab[13,2],CriaVar("F1_FORNECE",.F.))
Local c116Loja	    := If(l116Auto,aAutoCab[14,2],CriaVar("F1_LOJA",.F.))
Local c116Tes	    := If(l116Auto,aAutoCab[15,2],CriaVar("D1_TES",.F.))
Local lRet		    := .F.

Local oDlg
Local oCombo1
Local oCombo2
Local oCombo3
Local oCombo4
Local oCombo5
Local oCliFor
Local oFornOri
Local o116UfOri := NIL

Private c116UFOri	:= CriaVar("A2_EST",.F.)
Private aValidGet	:= {}
Private c116Especie   := If(l116Auto,aAutoCab[18,2],CriaVar("F1_ESPECIE",.F.))

//Tratamento para quando não enviar nada na TES e em vez de gerar
//erro.log é apresentado HELP que tes não foi preenchida.
If ValType(c116Tes) == "U"
	c116Tes := ""
Endif

//Ponto de Entrada para manipular o valor do frete
If (ExistBlock("MT116VAL"))
	n116Valor := ExecBlock("MT116VAL",.F.,.F.,{n116Valor})
	If ValType(n116Valor) <> "N"
		n116Valor := 0
	EndIf
EndIf

//Ponto de Entrada que Permite manipular a Consulta padr]ao que será
//utilizada para F3 FORNECEDOR e CLIENTE   
If (ExistBlock("MT116F3"))
	a116F3 := ExecBlock("MT116F3",.F.,.F.)
	If ValType(a116F3)<>"A" .Or. Len(a116F3) == 0 .Or. Len(a116F3)>2 
	    A116F3:={}  
	Else   
	   For nX = 1 to Len(a116F3)
		   aCliFor[nX][2]=a116F3[nX] 
	   Next Nx
	EndIf   
EndIf

//Ponto de Entrada para manipular o valor padrao da pergunta "Aglutina produtos?"
If (ExistBlock("MT116AGL"))
	c116Combo4 := ExecBlock("MT116AGL", .F., .F., {aCombo4})
	If ValType(c116Combo4) # "C" .Or. !(aScan(aCombo4, c116Combo4) > 0)
		c116Combo4 := aCombo4[1] // padrao = "Sim"
	EndIf
	nCombo4 := aScan(aCombo4, c116Combo4)
EndIf		

If !( l116Auto )
	DEFINE MSDIALOG oDlg FROM 87 ,52  TO 500/*450*/,609 TITLE STR0014+cCadastro Of oMainWnd PIXEL //"Parametros "
	//Parâmetros para Filtro
	@ 22 ,3   TO 68 ,274 LABEL STR0022 OF oDlg PIXEL //"Parametros do Filtro"
	@ 6 ,48  MSCOMBOBOX oCombo1 VAR c116Combo1 ITEMS aCombo1 SIZE 83 ,50 OF oDlg PIXEL VALID (nCombo1:=aScan(aCombo1,c116Combo1))
	@ 7  ,6   SAY STR0024 Of oDlg PIXEL SIZE 43,09 //"Quanto a Nota"
	@ 7  ,140 SAY STR0025 Of oDlg PIXEL SIZE 100 ,9 //"Filtrar notas com conhecimento de frete"
	@ 7  ,245 MSCOMBOBOX oCombo5 VAR c116Combo5 ITEMS aCombo5 SIZE 30 ,50 OF oDlg PIXEL When (nCombo1==1) VALID (nCombo5:=aScan(aCombo5,c116Combo5))
	@ 34 ,12  SAY STR0026 Of oDlg PIXEL SIZE 60 ,9 //"Data Inicial"
	@ 34 ,125 SAY STR0027 Of oDlg PIXEL SIZE 59 ,9 //"Data Final"
	@ 33 ,48  MSGET d116DataDe  Valid !Empty(d116DataDe) OF oDlg PIXEL SIZE 60 ,9
	@ 33 ,165 MSGET d116DataAte Valid !Empty(d116DataAte) OF oDlg PIXEL SIZE 60 ,9
	
	@ 52  ,12 SAY STR0028 Of oDlg PIXEL SIZE 54 ,9 //"Considerar"
	@ 51  ,48 MSCOMBOBOX oCombo2 VAR c116Combo2 ITEMS aCombo2 SIZE 75,50 OF oDlg PIXEL When (nCombo1==1) VALID ((nCombo2:=aScan(aCombo2,c116Combo2)),oCliFor:Refresh(),oFornOri:cF3:=aCliFor[nCombo2][2],c116FornOri:=SPACE(Len(c116FornOri)),c116LojaOri:=SPACE(Len(c116LojaOri)))
	
	@ 52 ,125 SAY oCliFor VAR aCliFor[nCombo2][1] Of oDlg PIXEL SIZE 28 ,9
	@ 51 ,165 MSGET oFornOri VAR c116FornOri Picture PesqPict("SA2","A2_COD") F3 aCliFor[nCombo2][2];
	   		  OF oDlg PIXEL SIZE 80 ,9 VALID Empty(c116FornOri).Or.A116StpVld(nCombo2,c116FornOri,@c116LojaOri,,1)
	   		  
	@ 51 ,245  MSGET c116LojaOri Picture PesqPict("SA2","A2_LOJA") F3 CpoRetF3("A2_LOJA");
		      OF oDlg PIXEL SIZE 19 ,9 VALID A116StpVld(nCombo2,c116FornOri,c116LojaOri,,1)
		
	//Dados para Nf Conhecimento de Frete
	@ 74 ,3   TO 180/*160*/,274 LABEL STR0029 OF oDlg PIXEL //"Dados da NF de Frete"
	@ 86 ,10  SAY STR0030 Of oDlg PIXEL SIZE 39 ,9 COLOR CLR_HBLUE,oDlg:nClrPane //"Form. Proprio"
	@ 85 ,47  MSCOMBOBOX oCombo3 VAR c116Combo3 ITEMS aCombo3 SIZE 35 ,50 OF oDlg PIXEL When (nCombo1==1) VALID ((nCombo3:=aScan(aCombo3,c116Combo3)),c116NumNF:=SPACE(Len(c116NumNF)),c116SerNF:=SPACE(Len(c116SerNF)))
	
	@ 86 ,125 SAY STR0031 Of oDlg PIXEL SIZE 39 ,9 COLOR CLR_HBLUE,oDlg:nClrPane //"Num. Conhec."
	@ 85 ,165 MSGET c116NumNF Picture PesqPict("SF1","F1_DOC") OF oDlg PIXEL SIZE 50 ,9 When (nCombo1==1.And.nCombo3==1) VALID A116NCF(@c116NumNF).And.A116ChkNFE(nCombo3,c116Fornece,c116Loja,c116NumNF,c116SerNF)
	
	@ 86 ,225 SAY STR0047 Of oDlg PIXEL SIZE 15 ,9  //"Serie"
	@ 85 ,242 MSGET c116SerNF Picture PesqPict("SF1","F1_SERIE") OF oDlg PIXEL SIZE 19 ,9  When (nCombo1==1.And.nCombo3==1) VALID A116ChkNFE(nCombo3,c116Fornece,c116Loja,c116NumNF,c116SerNF)

	@ 105,10  SAY STR0012 Of oDlg PIXEL SIZE 47 ,9 COLOR CLR_HBLUE,oDlg:nClrPane //"Fornecedor"
	@ 104,47  MSGET c116Fornece  Picture PesqPict("SF1","F1_FORNECE") F3 aCliFor[1][2] ;
	    	  OF oDlg PIXEL SIZE 80 ,9 When (nCombo1==1) VALID A116StpVld(1,c116Fornece,@c116Loja,@c116UfOri,2).And.A116ChkNFE(nCombo3,c116Fornece,c116Loja,c116NumNF,c116SerNF)

	@ 104,128  MSGET c116Loja Picture PesqPict("SF1","F1_LOJA") F3 CpoRetF3("F1_LOJA");
		      OF oDlg PIXEL SIZE 19 ,9 When (nCombo1==1) VALID A116StpVld(1,c116Fornece,c116Loja,@c116UfOri,2).And.A116ChkNFE(nCombo3,c116Fornece,c116Loja,c116NumNF,c116SerNF).And.A116ChkTra(c116Fornece,c116Loja,c116FornOri,c116LojaOri)

	@ 105,152 SAY STR0032 Of oDlg PIXEL SIZE 32 ,9 COLOR CLR_HBLUE,oDlg:nClrPane //"Cod. TES"
	@ 104,175 MSGET c116TES Picture PesqPict("SD1","D1_TES") F3 CpoRetF3("D1_TES");
		      OF oDlg PIXEL SIZE 25 ,9 When (nCombo1==1) VALID  (Empty(c116Tes) .Or. ExistCpo("SF4",c116Tes)) .And. A116ChkTES(c116TES)

	@ 105,205 SAY STR0046 Of oDlg PIXEL SIZE 33 ,9 COLOR CLR_HBLUE,oDlg:nClrPane //" Valor"
	@ 104,220 MSGET n116Valor Picture PesqPict("SD1","D1_TOTAL") ;
		      OF oDlg PIXEL SIZE 51 ,9 When (nCombo1==1)

	@ 125,10  SAY STR0033 Of oDlg PIXEL SIZE 36 ,9 //"UF Origem"
	@ 124,47  MSGET o116UfOri VAR c116UfOri Picture PesqPict("SA2","A2_EST") F3 CpoRetF3("A2_EST");
		      OF oDlg PIXEL SIZE 25 ,9 	When (nCombo1==1) VALID A116StpVld(1,c116Fornece,@c116Loja,@c116UfOri,2) .And. ExistCPO("SX5","12"+c116UFOri) .Or. Vazio(c116UFOri)
		      If(lLGPD,OfuscaLGPD(o116UfOri,"A2_EST"),.F.) 
		      
	@ 125,120 SAY STR0034 Of oDlg PIXEL SIZE 48 ,9 //"Aglutina Produtos ?"
	@ 125,180 MSCOMBOBOX oCombo4 VAR c116Combo4 ITEMS aCombo4 SIZE 30 ,50 OF oDlg PIXEL When (nCombo1==1) VALID (nCombo4:=aScan(aCombo4,c116Combo4))
	
	@ 146,10  SAY STR0035 Of oDlg PIXEL SIZE 49 ,9 //"Bs Icms Ret."
	@ 144,47  MSGET oGetBs VAR n116BsIcmRet  Picture PesqPict("SD1","D1_BRICMS") F3 CpoRetF3("D1_BRICMS");
		      OF oDlg PIXEL SIZE 70 ,9 When (nCombo1==1) VALID Positivo(n116BsIcmRet)

	@ 144,140 SAY STR0036 Of oDlg PIXEL SIZE 41 ,9 //"Vlr. Icms Ret."
	@ 143,180 MSGET n116VlrIcmRet Picture PesqPict("SD1","D1_ICMSRET") F3 CpoRetF3("D1_ICMSRET");
		      OF oDlg PIXEL SIZE 70 ,9 When (nCombo1==1) VALID Positivo(n116VlrIcmRet)
		      
	@ 166,10  SAY "Especie:" Of oDlg PIXEL SIZE 49 ,9 //"Bs Icms Ret."
	@ 164,47  MSGET oGetBs VAR c116Especie  Picture PesqPict("SF1","F1_ESPECIE") F3 CpoRetF3("F1_ESPECIE");
		      OF oDlg PIXEL SIZE 25 ,9 When (nCombo1==1) VALID CheckSX3("F1_ESPECIE",c116Especie)

	@188,220 BUTTON STR0037 SIZE 35 ,10  FONT oDlg:oFont ACTION If(A116StpOk(c116NumNF,c116Fornece,c116Loja,c116Tes,c116FornOri,c116LojaOri,nCombo1,n116Valor,nCombo3),(lRet:=.T.,oDlg:End()),Nil)  OF oDlg PIXEL //"Confirma >>"
	@188,180 BUTTON STR0038 SIZE 35 ,10  FONT oDlg:oFont ACTION (oDlg:End())  OF oDlg PIXEL //"<< Cancelar"

	ACTIVATE MSDIALOG oDlg CENTERED
Else
	If Type("aParametros") == "A" 
		If nCombo1 == 1
			// criacao da aValidGet
			aValidGet := {}
			Aadd(aValidGet,{"c116FornOri",aAutoCab[ 4,2],"Empty('"+c116FornOri+"') .Or. A116StpVld("+Str(nCombo2,1)+",'"+c116FornOri+"','"+c116LojaOri+"',,1)",.F.})
			Aadd(aValidGet,{"c116LojaOri",aAutoCab[ 5,2],"Empty('"+c116LojaOri+"') .Or. A116StpVld("+Str(nCombo2,1)+",'"+c116FornOri+"','"+c116LojaOri+"',,1)",.F.})
			Aadd(aValidGet,{"c116NumNF"  ,aAutoCab[11,2],"A116ChkNFE("+Str(nOpcAuto,1)+",'"+c116Fornece+"','"+c116Loja+"','"+c116NumNF+"','"+c116SerNF+"')",.F.})
			Aadd(aValidGet,{"c116SerNF"  ,aAutoCab[12,2],"A116ChkNFE("+Str(nOpcAuto,1)+",'"+c116Fornece+"','"+c116Loja+"','"+c116NumNF+"','"+c116SerNF+"')",.F.})
			Aadd(aValidGet,{"c116Fornece",aAutoCab[13,2],"A116StpVld(1,'"+c116Fornece+"','"+c116Loja+"',@c116UfOri,2) .And. A116ChkNFE("+Str(nOpcAuto,1)+",'"+c116Fornece+"','"+c116Loja+"','"+c116NumNF+"','"+c116SerNF+"')",.F.})
			Aadd(aValidGet,{"c116Loja"   ,aAutoCab[14,2],"A116StpVld(1,'"+c116Fornece+"','"+c116Loja+"',@c116UfOri,2) .And. A116ChkNFE("+Str(nOpcAuto,1)+",'"+c116Fornece+"','"+c116Loja+"','"+c116NumNF+"','"+c116SerNF+"')",.F.})
			If nOpcAuto == 1  
				Aadd(aValidGet,{"c116Tes"	  ,aAutoCab[15,2],"!Empty('"+c116Tes+"')",.F.})
			EndIf	
			lRet := SF1->(MsVldGAuto(aValidGet)) // consiste os gets
		Else
			lRet := .T.
		EndIf
	EndIf
EndIf	

nCombo1:= If(nCombo1==1,2,1)

aParametros:= {	nCombo1,; // 1 Define a Rotina : 1-Inclusao / 2-Exclusao
	nCombo2,; 		      // 2 Considerar Notas : 1 - Compra , 2 - Devolucao
	d116DataDe,; 		  // 3 Data Inicial para Filtro das NF Originais
	d116DataAte,;		  // 4 Data Final para Filtro das NF originais
	c116FornOri,;		  // 5 Cod. Fornecedor para Filtro das NF Originais
	c116LojaOri,;		  // 6 Loja Fornecedor para Fltro das NF Originais
	nCombo3,; 			  // 7 Utiliza Formulario proprio ? 1-Sim,2-Nao
	c116NumNF,;  		  // 8 Num. da NF de Conhecimento de Frete
	c116SerNF,;  		  // 9 Serie da NF de COnhecimento de Frete
	c116Fornece,;		  // 10 Codigo do Fornecedor da NF de FRETE
	c116Loja,;   		  // 11 Loja do Fornecedor da NF de Frete
	c116Tes,;    		  // 12 Tes utilizada na Classificacao da NF
	n116Valor,;  		  // 13 Valor total do Frete sem Impostos
	c116UFOri,;  		  // 14 Estado de Origem do Frete
	(nCombo4==1),; 		  // 15 Aglutina Produtos : .T. , .F.
	n116BsIcmRet,;	      // 16 Base do Icms Retido
	n116VlrIcmRet,;		  //17 Valor do Icms Retido
	(nCombo5==2),;  	  //18 Filtra nota com conhecimento frete .F. , .T.
	c116Especie,;		  //19 Especie da Nota Fiscal
	}

//Pontos de Entrada para ponto de entrada de validação da tela de parâmetros
If lRet .And. ExistBlock("MT116VTP")
	lMT116VTP:= ExecBlock("MT116VTP",.F.,.F.,{aParametros} )
	If ValType(lMT116VTP) = "L"
			lRet := lMT116VTP
		EndIf
EndIf

Return lRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116StpVl³ Autor ³ Edson Maricate         ³ Data ³17.11.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Valida o codigo do fornecedor/cliente digitado.             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpN1: Tipo de conhecimento de Frete     	                  ³±±
±±³          ³       1 - Cliente                        	              ³±±
±±³          ³       2 - Fornecedor                                       ³±±
±±³          ³ExpC2: Codigo do cliente/fornecedor                         ³±±
±±³          ³ExpC3: Loja do cliente/fornecedor                           ³±±
±±³          ³ExpC4: Uf de Origem				                          ³±±
±±³          ³ExpC5: Origem.     				                          ³±±
±±³          ³       1 - Cliente/Fornecedor do Filtro	                  ³±±
±±³          ³       2 - Cliente/Fornecedor do Documento de Frete         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL: Validacao do fornecedor/cliente                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function A116StpVld(nTipo,cCodigo,cCodLoja,c116UfOri,cOrigem)

Local aArea		:= GetArea()
Local aAreaSA1	:= SA1->(GetArea()) 
Local aAreaSA2	:= SA2->(GetArea())
Local lRet			:= .T.

If !Empty(cCodigo)
	If nTipo == 2
		dbSelectArea("SA1")
		If !Empty(cCodigo)
			If cCodLoja == Nil .Or. Empty(cCodLoja)
				SA1->(dbSetOrder(1)) 
				SA1->(MsSeek(xFilial("SA1")+cCodigo))
				If SA1->(Found())
					cCodLoja := SA1->A1_LOJA
				Else
					If cOrigem == 2
						lRet := .F.
						HELP("  ",1,"REGNOIS")
					Endif
				EndIf
			Else
				SA1->(dbSetOrder(1))
				SA1->(MsSeek(xFilial("SA1")+cCodigo+cCodLoja))
				If !SA1->(Found())
					If cOrigem == 2
						lRet := .F.
						HELP("  ",1,"REGNOIS")
					Endif
				EndIf
			EndIf
			
			//Verifica se o Registro esta Bloqueado.    
			//Somente irá fazer a crítica de Bloqueio quando for referente ao documento
			//e não ao filtro
			If lRet .And. cOrigem == 2
		       If !RegistroOk("SA1") 
			       lRet := .F.
			   EndIf
			EndIf		
		EndIf
	Else
		If !Empty(cCodigo)
			dbSelectArea("SA2")
			If cCodLoja == Nil .Or. Empty(cCodLoja)
				SA2->(dbSetOrder(1))
				SA2->(MsSeek(xFilial("SA2")+cCodigo))
				While !SA2->(Eof()) .AND. xFilial("SA2")+cCodigo == SA2->A2_FILIAL+SA2->A2_COD .AND. Empty(cCodLoja)
					IF SA2->A2_MSBLQL != "1"
					    If Empty(c116UfOri)
					       c116UfOri := SA2->A2_EST
					    Else
					    	If c116UfOri <> SA2->A2_EST .And. AllTrim(Upper(ReadVar())) <> "C116UFORI"
					    		c116UfOri := SA2->A2_EST
					    	Endif
					    EndIf
						cCodLoja := SA2->A2_LOJA
					Else
						SA2->(DbSkip())	
					EndIf
				Enddo
				
				If SA2->(MsSeek(xFilial("SA2")+cCodigo+cCodLoja))
					If !RegistroOk("SA2")
						cCodLoja := Nil
					EndIf 
				Else
					If cOrigem == 2
						lRet := .F.
						HELP("  ",1,"REGNOIS")
					Endif
				Endif
			Else
				SA2->(dbSetOrder(1))
				SA2->(MsSeek(xFilial("SA2")+cCodigo+cCodLoja))
				If SA2->(Found())
					If RegistroOk("SA2")
					    If Empty(c116UfOri)
					       c116UfOri := SA2->A2_EST
					    Else
					    	If c116UfOri <> SA2->A2_EST .And. AllTrim(Upper(ReadVar())) <> "C116UFORI"
					    		c116UfOri := SA2->A2_EST
					    	Endif
				    	EndIf
				    Else
				    	lRet := .F.
				    EndIf	
				Else
					If cOrigem == 2 .Or. cOrigem == 1
						lRet := .F.
						HELP("  ",1,"REGNOIS")
					Endif
				EndIf
			EndIf
			
			//Verifica se o Registro esta Bloqueado.    
			//Somente irá fazer a crítica de Bloqueio quando for referente ao documento
			//e não ao filtro
			If lRet .And. cOrigem == 2
		       If !RegistroOk("SA2")
			       lRet := .F.
			   Endif
			EndIf		
		EndIf
	EndIf
	
ElseIf l116Auto
	lRet := .F.
	HELP("  ",1,"REGNOIS")
EndIf

RestArea(aAreaSA1)
RestArea(aAreaSA2)
RestArea(aArea)

Return lRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116ChkNFE³ Autor ³ Edson Maricate        ³ Data ³07.01.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Verifica se a NF ja existe ou esta sendo incluida em outra  ³±±
±±³          ³estacao .                                                   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpN1: Informe 1 para consistir o documento de entrada      ³±±
±±³          ³ExpC2: Codigo do fornecedor                                 ³±±
±±³          ³ExpC3: Loja do fornecedor                                   ³±±
±±³          ³ExpC4: Numero do documento de entrada                       ³±±
±±³          ³ExpC5: Serie dodocumento de entrada                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL: Validacao do documento de entrada                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function A116ChkNFE(nFormul,cFornece,cCodLoja,cNFiscal,cSerie)

Local lRet      := .T.
Local lMT116Vld := .T.
 
//Verifica se a NF esta sendo digitada em outra estacao.
If cMayUse == Nil .Or. cMayUse != xFilial("SF1")+cNFiscal+cSerie+cFornece+cCodLoja
	FreeUsedCode()
	cMayUse := xFilial("SF1")+cNFiscal+cSerie+cFornece+cCodLoja
EndIf

If !Empty(cFornece) .And. !Empty(cCodLoja)
	//Consiste duplicidade de digitacao de Nota Fiscal
	If nFormul == 1
		SF1->(dbSetOrder(1))
		If SF1->(MsSeek(xFilial("SF1")+cNFiscal+cSerie+cFornece+cCodLoja,.F.))
			lRet := .F.
			HELP(" ",1,"EXISTNF")
		EndIf
		
		//Verifica se a NF esta sendo digitada em outra estacao.
		If lRet .And. !Empty(cNFiscal) .And. !FreeForUse("NFE",cMayUse)
			lRet := .F.
		EndIf
	EndIf
EndIf

If ExistBlock("MT116VLD") .And. lRet 
	lMT116Vld := ExecBlock("MT116VLD",.F.,.F.,{nFormul,cNFiscal,cSerie,cFornece,cCodLoja})
	If ValType(lMT116Vld)=="L" 
        lRet := lMT116Vld              
    Endif
EndIf

Return (lRet)  

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116NCF   ³ Autor ³ Julio C Guerato       ³ Data ³19.01.2009³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Funcao que aplica ponto de entrada para manipular numero da ³±±
±±³          ³nf de conhecimento                                          ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpC1: Numero do documento de entrada                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL:  Retornar o valor manipulado do Doc.Entrada           ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function A116NCF(c116NumNF)

Local lRet := .T.
Local cPEcNFiscal := ""

If ExistBlock("MT116NCF")
	cPEcNFiscal := ExecBlock("MT116NCF",.F.,.F.,{c116NumNF})
	If ValType(cPEcNFiscal)=="C" .AND. len(trim(cPEcNFiscal))>0
        c116NumNF = cPEcNFiscal              
    Endif
endif

Return (lRet)

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116StpVld³ Autor ³ Edson Maricate        ³ Data ³07.01.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Verifica os dados do formulario de selecao do conhecimento  ³±±
±±³          ³de frete.                                                   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpC1: Documento de Saida                                   ³±±
±±³          ³ExpC2: Codigo do fornecedor                                 ³±±
±±³          ³ExpC3: Loja do fornecedor                                   ³±±
±±³          ³ExpC4: TES                                                  ³±±
±±³          ³ExpC5: Fornecedor de Origem                                 ³±±
±±³          ³ExpC6: Loja do fornecedor de origem                         ³±±
±±³          ³ExpN7: Indica se valida o conhecimento de frete             ³±±
±±³          ³ExpN8: Valor do conhecimento de frete                       ³±±
±±³          ³ExpN9: Indica se valida o numero do conhecimento de frete   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL: Validacao do documento de entrada                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function A116StpOk(cNumNF,cFornece,cLoja,cTes,cFornOri,cLojaOri,nCombo1,nValor,nCombo3)
Local lRet := .T.

If nCombo1 == 1
	If (Empty(cNumNF).And.nCombo3==1) .Or. Empty(cFornece) .Or. Empty(cLoja) .Or. Empty(cTes) .Or. Empty(nValor)
		lRet := .F.
		Help(" ",1,"A116CPOOBRIGAT",,STR0040,1,0) //"Atencao!"###"Existem campos de preenchimento obrigatorio que nao foram informados. Verifique os campos da tela de que contem os dados da nota fiscal."###"Voltar"
	EndIf
EndIf	

If lRet .And. (!Empty(cFornOri).And.Empty(cLojaOri))
	lRet := .F.
	Help(" ",1,"A116FORNLOJ",,STR0042,1,0) //"Atencao!"###"Codigo da loja do fornecedor invalida. Verifique o preenchimento correto da loja do Fornecedor nos parametros para filtragem da nota fiscal."###"Voltar"
EndIf

Return lRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116Inclui³ Autor ³ Edson Maricate        ³ Data ³27/03/2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpC1: Alias de entrada                                     ³±±
±±³          ³ExpC2: Campo com a marca da Markbrowse                      ³±±
±±³          ³ExpC3: Opcao do arotina                                     ³±±
±±³          ³ExpC4: Codigo da marca                                      ³±±
±±³          ³ExpC5: Indicador de inversao de marca                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
FUNCTION A116Inclui(cAlias,cCampo,nOpcX,cMarca,lInverte,lPreNota,aRatcc,nPosNat,nPosPicm)

Local lContinua	 := .T.
Local l116Inclui := .F.
Local l116Exclui := .F.
Local l116Visual := .F.
Local lDigita    := .F.
Local lAglutina  := .F.
Local lGeraLanc  := .F.
Local lQuery     := .F.
Local lSkip      := .F.
Local lAviso     := .T.
Local lM116ACOL  := ExistBlock("M116ACOL")
Local lMt116Cust := ExistBlock("MT116CUST")
Local lSubSerie  := cPaisLoc == "BRA" .And. SF1->(ColumnPos("F1_SUBSERI")) > 0 .And. SuperGetMv("MV_SUBSERI",.F.,.F.)
Local lTrbGen    := IIf(FindFunction("ChkTrbGen"),ChkTrbGen("SD1", "D1_IDTRIB"),.F.) // Verifica se esta preparado para o motor de tributos genericos

Local bCabOk     := {|| .T.}
Local bIPRefresh:= {|| MaFisToCols(aHeader,aCols,,"MT100",.T.),Eval(bRefresh),Eval(bGdRefresh)}	// Carrega os valores da Funcao fiscal e executa o Refresh

Local aCpos2	 := {"D1_VUNIT","D1_TOTAL","D1_PICM","D1_IPI","D1_CONTA","D1_CC","D1_VALICM","D1_CF","D1_TES","D1_BASEICM","D1_BASEIPI","D1_VALIPI","D1_ITEMCTA","D1_CLVL","D1_CLASFIS","D1_BASEINS","D1_ALIQINS","D1_VALINS","D1_OPER","D1_RATEIO","D1_ORDEM","D1_ICMSCOM","D1_ALIQISS"}
Local aInfForn	 := {"","",CTOD("  /  /  "),CTOD("  /  /  "),"","","",""}
Local aValores	 := {0,0,0,0,0,0,0,0,0,0}
Local aTitles	 := {STR0015,; //"Totais"
				  	 STR0016,; //"Inf. Fornecedor/Cliente"
					 STR0017,; //"Descontos/Frete/Despesas"
					 STR0018,; //"Livros Fiscais"
					 STR0019,; //"Impostos"
					 STR0020}  //"Duplicatas"
Local aButtons	 := { {"S4WB013N",{||NfeRatCC(aHeadSDE,aColsSDE,l116Inclui)},STR0043,STR0044} } //"Rateio por Centro de Custo"
Local aFldCBAtu  := Array(Len(aTitles))
Local aSizeAut	 := MsAdvSize(,.F.,400)
Local aAuxRefSD1 := MaFisSXRef("SD1")
Local aAuxRefSF1 := MaFisSXRef("SF1")
Local aHeadSE2   := {}
Local aHeadSEV   := {}
Local aHeadSDE	 := {}
Local aColsSDE   := {}
Local aColsSE2   := {}
Local aColsSEV   := {}
Local aRecSD1	 := {}
Local aRecSE2	 := {}
Local aRecSF3	 := {}
Local aRecSC5	 := {}
Local aRecSF8	 := {}
Local aRecSDE	 := {}
Local aRecSF1Ori := {}
Local aInfo 	 := {}
Local aPosGet	 := {}
Local aPosObj	 := {}
Local aStruSD1   := {}
Local aChave     := Array(5)
Local aM116aCol	 := Array(5)
Local aNotas     := {}
Local aItIcm     := {}
Local aAmarrAFN	 := {}
Local aRetMaFisAjIt	:= {}
Local aInfApurICMS	:= {}	
Local aColTrbGen    := {}
Local aParcTrGen    := {}

Local lAzFrete	 := SuperGetMv("MV_AZFRETE",.F.,.T.) // Indica se no conhecimento de frete, deve zerar a aliquota do item que tiver aliquota zerada na NF de origem
Local lImpfor   := SuperGetMv("MV_M116FOR",.F.,.F.)

Local cItemSDE	 := ""
Local cCadastro	 := STR0001 //"Nota Fiscal de Conhecimento de Frete"
Local cPrefixo 	 := If(Empty(SF1->F1_PREFIXO),&(SuperGetMV("MV_2DUPREF")),SF1->F1_PREFIXO)
Local cItem		 := StrZero(0,Len(SD1->D1_ITEM))
Local cLocCQ	 := SuperGetMv("MV_CQ")
Local cQuery     := ""
Local cQrySF1    := Eval(bFiltraBrw,1)
Local cAliasSF1  := "SF1"
Local cAliasSD1  := "SD1"
Local cRatDesp	 := SuperGetMV("MV_RATDESP")
Local lCusFifo   := SuperGetMv("MV_CUSFIFO",.F.,.F.)
Local cVarFoco   := "     "                
Local cRecIss 	 := "1"

Local oDlg
Local oGetDados
Local oSize
Local oLivro
Local nPosCh     :=  Iif(l116Auto, aScan(aAutoCab,{|x| x[1] == "F1_CHVNFE"}),0 )
Local nPosPedg   :=  Iif(l116Auto, aScan(aAutoCab,{|x| x[1] == "F1_VALPEDG"}),0)
Local nOpc       := 0
Local nUsado	 := 0
Local nTotal	 := 0
Local nDifTotal	 := 0
Local nPosAuto	 := 0
Local nPosProd   := 0
Local nPosNumCQ  := 0
Local nPosConta  := 0
Local nPosItCta  := 0
Local nPosCC     := 0
Local nPosOP     := 0
Local nPosSegUm  := 0 
Local nPesoTotal := 0
Local nPosPeso   := 0
Local nPosClaFis := 0
Local nPosCLVL   := 0
Local nPosNfOri  := 0
Local nPosSeriOri:= 0
Local nPosItemOri:= 0
Local nPosCodLan := 0
Local nPosOper	 := 0
Local nPItem     := 0
Local nPosRat	 := 0
Local nPosCF     := 0
Local nPosOrd    := 0
Local nj		 := 0
Local nX         := 0
Local nY         := 0
Local nW         := 0
Local nA		 := 0
Local nPosicao   := 0
Local nPosVeic   := 0
Local nTpRodape  := 0
Local nRecSF1	 := 0
Local nInfDiv    := 0
Local nTrbGen    := 0
Local nRatFrete  := Val(SubStr(cRatDesp,At("FR=",cRatDesp)+3,1))
Local nMaxItem   := 0
Local nIndexSE2  := 0 
Local nPosGetLoja:= IIF(TamSX3("A2_COD")[1]< 10,(2.5*TamSX3("A2_COD")[1])+(110),(2.8*TamSX3("A2_COD")[1])+(100)) 
Local nColsSE2   := 0

Local cModRetPIS := GetNewPar( "MV_RT10925", "1" )
Local nGeraSemOP := SuperGetMV("MV_GERASOP",.F.,3)
Local lPCCBaixa  := SuperGetMv("MV_BX10925",.T.,"2") == "1"  .and. (!Empty( SE5->( FieldPos( "E5_VRETPIS" ) ) ) .And. !Empty( SE5->( FieldPos( "E5_VRETCOF" ) ) ) .And. ; 
				 !Empty( SE5->( FieldPos( "E5_VRETCSL" ) ) ) .And. !Empty( SE5->( FieldPos( "E5_PRETPIS" ) ) ) .And. ;
				 !Empty( SE5->( FieldPos( "E5_PRETCOF" ) ) ) .And. !Empty( SE5->( FieldPos( "E5_PRETCSL" ) ) ) .And. ;
				 !Empty( SE2->( FieldPos( "E2_SEQBX"   ) ) ) .And. !Empty( SFQ->( FieldPos( "FQ_SEQDES"  ) ) ) )
Local nResto     := 0
Local lMt116SD1  := ExistBlock("MT116SD1")
Local lRet116SD1 := .T.
Local lRet       := .T.
Local aAtuExc	 := {}
Local aValidGet  := {}
Local aCtbInf    := {}	//Array contendo os dados para contabilizacao online:
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

Local nLancAp	:=	0
Local aHeadCDA	:=	{}
Local aColsCDA	:=	{}
Local aHeadCDV	:= {}
Local aColsCDV	:= {}
Local aBtnBack	:=	{}
Local aColsAux	:= {}
Local aDigEnd	:= {}      
      
Local nCombo		:= 2
Local oCombo
Local oCodRet
Local aCodR	        :=	{}
Local cFornIss		:= Space(Len(SE2->E2_FORNECE))
Local cLojaIss		:= Space(Len(SE2->E2_LOJA))
Local dVencISS		:= CtoD("")
Local oRecIss
Local lTemIss			:= .F.
Local cGrpTrib		:= ""
Local cNFs				:= ""

Local lColab := l116Auto .And. aScan(aAutoCab, {|x| x[1] == "COLAB" .And. x[2] == "S"}) > 0

Local aCpos140 	:= {	"D1_COD"	,;
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
						"D1_DESC"	,;
						"D1_VALDESC",;
						"D1_OP"		,;
						"D1_CODGRP"	,;
						"D1_CODITE"	,;
						"D1_VALIPI"	,;
						"D1_VALICM"	,;
						"D1_CF"		,;
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
						"D1_SEGURO"	,;
						"D1_DESPESA",;
						"D1_FORMUL"	,;
						"D1_CLASFIS",;
						"D1_II"		,;
						"D1_ICMSDIF",;		
						"D1_ITEMMED",;
						"D1_NUMCQ",;
						"D1_ORDEM" }
						
Local lMVCAT8309 := SuperGetMv("MV_CAT8309",.F.,.F.)
Local cMVVeiculo := SuperGetMv("MV_VEICULO",.F.,"N")
Local lMT116OK   := ExistBlock("MT116OK")
Local lMT116AGR  := ExistBlock("MT116AGR")
Local lIntMnt    := SuperGetMV("MV_NGMNTES",.F.,"N") == "S" .Or. SuperGetMV("MV_NGMNTCM",.F.,"N") == "S"
Local lGravaOri  := .F.
Local cFilSF4 	 := xFilial("SF4")
Local aItAux     := {}
Local lTESVlZero := .F.
Local nOpcDMS	 := 2
Local aAreaInt	 := {}
Local cPresCom	 := ""
Local cA1UCod	 := ""
Local lVldInter	 := .T.
Local dCtbValiDt := Ctod("")

Private lDKD		:= ChkFile("DKD") //Tabela Complementar SD1
Private lTabAuxD1	:= .F.
Private aHeadDKD	:= {}
Private aColsDKD	:= {}
Private aAltDKD		:= {}
Private oGetDKD		:= Nil

Default lPreNota := .F. 

If lFormulS
	aAreaInt := GetArea()
	If Len(aRecMark) > 0
		SF1->(DbGoto(aRecMark[1]))
		cPresCom := SF1->F1_INDPRES
		cA1UCod  := SF1->F1_CODA1U
		
		For nX := 2 To Len(aRecMark)
			SF1->(DbGoto(aRecMark[nX]))
			If cPresCom <> SF1->F1_INDPRES .Or. cA1UCod <> SF1->F1_CODA1U
				Help(" ",1,"A116PRESA1U",,STR0064 + RetTitle("F1_INDPRES") + STR0065 + RetTitle("F1_CODA1U") + STR0066,1,0) //"Documento possui " //" e/ou " //" diferente, não sendo possivel vincular no mesmo documento"
				lVldInter := .F.
				Exit
			Endif
		Next nX 
	Endif
	RestArea(aAreaInt)
	If !lVldInter
		Return .F.
	Endif
Endif 

If l116Auto
	//Em rotina automatica não deve utilizar a opção 3, pois é apresentada um tela
	//para o usuario decidir se inclui ou não o item de um op cancelada.
	//a oção 2 não ira gerar o item, pois a op esta cancelada.
	If nGeraSemOP == 3
		If SuperGetMv('MV_INTGFE',,.F.)
			nGeraSemOp := 1 //Limpa campo OP
		Else
			nGeraSemOP := 2 //Deleta Item
		Endif
	Endif
Endif

//CAT83 - Permite Manutenção no aCols
If V103CAT83()
    aaDD(aCpos2,"D1_CODLAN")
EndIf

If SD1->(Fieldpos('D1_T_MODAL')) > 0
	aAdd(aCpos2,'D1_T_MODAL')
EndIf

If ExistBlock("MA116BUT")
	aBtnBack := aClone(aButtons)
	aButtons := ExecBlock( "MA116BUT", .F., .F., { nOpcx, aButtons } )
	If ValType( aButtons ) <> "A"
		aButtons := aClone(aBtnBack)
	EndIf
EndIf 

If lPccBaixa
	cModRetPis := "3"
Endif     

aAdd(aTitles,STR0050) //"Lançamentos da Apuração de ICMS"
aAdd(aFldCBAtu,Nil)
nLancAp	:=	Len(aTitles)

If cPaisLoc == "BRA"
	Aadd(aTitles,STR0049) // "Informações DANFE"
	aAdd(aFldCBAtu,Nil)
	nInfDiv := 	Len(aTitles)
	A103CargaDanfe() 
	If Len(aNfeDanfe)>0
		aNfeDanfe[13]:=if(SF1->(FieldPos("F1_CHVNFE"))>0, CriaVar("F1_CHVNFE") ,"")
		If !Empty(cChvNFE)
			aNfeDanfe[13]:= cChvNFE  
		EndIf
		aNfeDanfe[18]:=if(SF1->(FieldPos("F1_TPCTE"))>0, CriaVar("F1_TPCTE") ,"")
		If !Empty(cTPCTE)
			aNfeDanfe[18]:= cTPCTE
		EndIf 
	EndIf
EndIf	

//Verifica o modo de atualizacao da rotina
Do Case
Case aRotina[nOpcx][4] == 6 
	l116Inclui	:= .T.
	l103Visual	:= .F.
	INCLUI      := .T.
	ALTERA      := .F.
	nOpcDMS		:= 3
Case aRotina[nOpcx][4] == 5
	l116Exclui	:= .T.
	cCadastro	 := STR0007 //"Excluir NF de Conhec. Frete"
	l103Visual	:= .T.
	INCLUI      := .F.
	ALTERA      := .F.	
	nRecSF1	 	:= SF1->(RecNo())
	nOpcDMS		:= 5
OtherWise
	l116Visual	:= .T.
	l103Visual	:= .T.
	INCLUI      := .F.
	ALTERA      := .F.	
	nRecSF1	 := SF1->(RecNo())
EndCase

If l116Exclui
	lPreNota	:= Empty(SF1->F1_STATUS)
EndIf

Private cTipo	  := IIf(l116Inclui,"C",SF1->F1_TIPO)
Private cTpCompl  := ""
Private cFormul	  := IIf(l116Inclui,IIf(aParametros[FORMUL]==2,"S","N"),SF1->F1_FORMUL)
Private cNFiscal  := IIf(l116Inclui,aParametros[NUMNF],SF1->F1_DOC)
Private cSerie	  := IIf(l116Inclui,aParametros[SERNF],SF1->F1_SERIE)
Private cSubSerie := ""
Private dDEmissao := IIf(l116Inclui,dDataBase,SF1->F1_EMISSAO)
Private cA100For  := IIf(l116Inclui,aParametros[FORNECE],SF1->F1_FORNECE)
Private cLoja     := IIf(l116Inclui,aParametros[LOJA],SF1->F1_LOJA)
Private cEspecie  := IIf(l116Inclui,CriaVar("F1_ESPECIE"),SF1->F1_ESPECIE)

If (l116Inclui .And. cA100For+cLoja <> SA2->A2_COD+SA2->A2_LOJA)
	SA2->(MsSeek(xFilial("SA2")+cA100For+cLoja))
EndIf

Private cCondicao := IIf(l116Inclui,SA2->A2_COND,SF1->F1_COND)
Private lReajuste  := .F.
Private lAmarra    := .F.
Private lConsLoja  := .F.
Private lPrecoDes  := .F.
Private lDataUCOM  := .F.
Private lAtuAmarra := .F.
Private n          := 1
Private nMoedaCor  := 1
Private aCols	   := {}
Private aHeader    := {}
Private aRatVei    := {}
Private aRatFro    := {}
Private aArraySDG  := {}
Private aRatAFN    := {}
Private bRefresh   := {|nX| NfeFldChg(nX,nY,,aFldCBAtu)}
Private bGDRefresh := {|| IIf(oGetDados<>Nil,(oGetDados:oBrowse:Refresh()),.F.) }		// Efetua o Refresh da GetDados
Private oFoco103
Private lMudouNum  := .F. 	
Private oLancApICMS
Private oLancCDV
Private oFisTrbGen

Private cDirf	   := Space(Len(SE2->E2_DIRF))
Private cCodRet	   := Space(Len(SE2->E2_CODRET))
Private cForAntNFE := ""
Private cLojAntNFE := ""

If cPaisLoc == "BRA" .And. l116OriDest
	Aadd(aTitles,STR0061) // "Informações Adicionais"
	aAdd(aFldCBAtu,Nil)
	nInfAdic := Len(aTitles)
	A103ChkInfAdic(IIF(l116Inclui,1,2))
Endif

If lTrbGen
	Aadd(aTitles,STR0062) // "Tributos Genéricos"
	nTrbGen := Len(aTitles)
	aAdd(aFldCBAtu,Nil) 
EndIf

If SF1->(ColumnPos("F1_TPCOMPL")) > 0
	cTpCompl	:= IIF(l116Inclui,"3",SF1->F1_TPCOMPL)
EndIf

If lSubSerie
	cSubSerie := IIF(l116Inclui,CriaVar("F1_SUBSERI"),SF1->F1_SUBSERI)
EndIf

If ( Type("aNFEDanfe") == "U" )
	PRIVATE aNFEDanfe := {}
EndIf

If ( Type("aDanfeComp") == "U" )
	Private aDanfeComp:= {}
EndIf

If Empty(cEspecie) 
	If !Empty(cEspecie2)
		cEspecie := cEspecie2
	Else
		cEspecie := PadR("CTR",Len(SF1->F1_ESPECIE))
	EndIf
EndIf

//Verificacao do modo de rotina automatica
l116Auto := If (Type("l116Auto")<>"U",l116Auto,.F.)
If l116Auto .And. l116Inclui
	cCondicao := aAutoCab[18,2]
	If Len(aAutoCab) >= 19
		dDEmissao := aAutoCab[19,2]
	EndIf
	If Len(aAutoCab) >= 20
		cEspecie := aAutoCab[20,2]
	EndIf	
EndIf

//Carrega as perguntas utilizadas no mata103
Pergunte("MTA103",.F.)
lDigita     := (mv_par01==1)
lAglutina   := (mv_par02==1) .And. !lColab
lReajuste   := (mv_par04==1)
lAmarra     := (mv_par05==1)
lGeraLanc   := (mv_par06==1)
lConsLoja   := (mv_par07==1)
IsTriangular((mv_par08==1))
nTpRodape   := (mv_par09)
lPrecoDes   := (mv_par10==1)
lDataUcom   := (mv_par11==1)
lAtuAmarra  := (mv_par12==1)

//Verifica se a operacao pode ser feita/ Valida Chave caso
//MV_CHVNFE e MV_DCHVNFE estejam ativos

If l116Inclui
   If l116Auto  .And. (nPosCh > 0 .Or. nPosPedg > 0)
		If nPosCh > 0
			Aadd(aValidGet,{"aNfeDanfe[13]",aAutoCab[nPosCh,2],"Eval({||CheckSX3('F1_CHVNFE',aNfeDanfe[13]),A103ConsNfeSef()})",.F.}) 	 	
			aNfeDanfe[13] := aAutoCab[nPosCh,2]
		EndIf
		If nPosPedg > 0
			Aadd(aValidGet,{"aNfeDanfe[15]",aAutoCab[nPosPedg,2],"Eval({||CheckSX3('F1_VALPEDG',aNfeDanfe[15])})",.F.})
			aNfeDanfe[15] := aAutoCab[nPosPedg,2]
		EndIf
   	EndIf
   	
   	If l116Auto .And. l116OriDest
	   	If ProcH("F1_UFORITR") > 0
			Aadd(aValidGet,{"aInfAdic[10]",aAutoCab[ProcH("F1_UFORITR"),2],"Eval({||CheckSX3('F1_UFORITR',aInfAdic[10])})",.F.})
			aInfAdic[10] := aAutoCab[ProcH("F1_UFORITR"),2]
			MaFisAlt("NF_UFORIGEM",aInfAdic[10]) 
		EndIf
		
		If ProcH("F1_MUORITR") > 0
			Aadd(aValidGet,{"aInfAdic[11]",aAutoCab[ProcH("F1_MUORITR"),2],"Eval({||CheckSX3('F1_MUORITR',aInfAdic[11])})",.F.})
			aInfAdic[11] := aAutoCab[ProcH("F1_MUORITR"),2]
		EndIf
		
		If ProcH("F1_UFDESTR") > 0
			Aadd(aValidGet,{"aInfAdic[12]",aAutoCab[ProcH("F1_UFDESTR"),2],"Eval({||CheckSX3('F1_UFDESTR',aInfAdic[12])})",.F.})
			aInfAdic[12] := aAutoCab[ProcH("F1_UFDESTR"),2]
			MaFisAlt("NF_UFDEST",aInfAdic[12])
		EndIf
		
		If ProcH("F1_MUDESTR") > 0
			Aadd(aValidGet,{"aInfAdic[13]",aAutoCab[ProcH("F1_MUDESTR"),2],"Eval({||CheckSX3('F1_MUDESTR',aInfAdic[13])})",.F.})
			aInfAdic[13] := aAutoCab[ProcH("F1_MUDESTR"),2]
		EndIf
	Endif

	If l116Auto .And. cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed
		If ProcH("F1_INDPRES") > 0
			Aadd(aValidGet,{"aInfAdic[16]",aAutoCab[ProcH("F1_INDPRES"),2],"Eval({|| A103VldPres()})",.F.})
			aInfAdic[16] := aAutoCab[ProcH("F1_INDPRES"),2]
		EndIf 

		If ProcH("F1_CODA1U") > 0
			Aadd(aValidGet,{"aInfAdic[17]",aAutoCab[ProcH("F1_CODA1U"),2],"Eval({|| A103VldA1U()})",.F.})
			aInfAdic[17] := aAutoCab[ProcH("F1_CODA1U"),2]
		EndIf
	Endif
   	
   	If l116Auto .And. Len(aValidGet) > 0
		If !SF1->(MsVldGAuto(aValidGet))
			lContinua := .F.
       EndIf
	Endif
	
	If !NfeVldIni(.F.,lGeraLanc)
		lContinua := .F.
	EndIf
ElseIf l116Exclui .And. !lPreNota
	If !MaCanDelF1(nRecSF1,@aRecSC5,aRecSE2,.T.)
		lContinua := .F.
	EndIf
EndIf	

If lContinua
	//Codigo do ISS de acordo com o cliente/fornecedor
	cRecIss  := Iif(SA2->A2_RECISS$"1S","1","2" )
	
	//Montagem do aHeader
	dbSelectArea("SX3")
	SX3->(dbSetOrder(1))
	SX3->(MsSeek("SD1"))
	While SX3->(!Eof()) .And. (SX3->X3_ARQUIVO == "SD1")
		If X3Uso(SX3->X3_USADO) .And. cNivel >= SX3->X3_NIVEL .And. AllTrim(SX3->X3_CAMPO) <> "D1_GERAPV" .And. ; 
					AllTrim(SX3->X3_CAMPO) <> "D1_ITEMMED"
					
			If lPreNota .And. aScan(aCpos140,Trim(SX3->X3_CAMPO)) == 0 .And. SX3->X3_PROPRI <> "U"
				SX3->(dbSkip())
				Loop
			EndIf
					
			//CAT83 - Nao adiciona campo ao aCols se parametro estiver desligado 
			If Trim(SX3->X3_CAMPO)="D1_CODLAN" .And. !lMVCAT8309		
				SX3->(dbSkip())
				Loop
			EndIF
		
			nUsado++
			aadd(aHeader,{ TRIM(X3Titulo()),;
				SX3->X3_CAMPO,;
				SX3->X3_PICTURE,;
				SX3->X3_TAMANHO,;
				SX3->X3_DECIMAL,;
				SX3->X3_VALID,;
				SX3->X3_USADO,;
				SX3->X3_TIPO,;
				SX3->X3_ARQUIVO,;
				SX3->X3_CONTEXT})
				
			If SX3->X3_PROPRI =="U" .And. SX3->X3_VISUAL != "V"
				aadd(aCpos2,Alltrim(SX3->X3_CAMPO))
			EndIf
			Do Case
			Case SubStr(AllTrim(SX3->X3_CAMPO),3)=="_ITEM"
				nPItem := nUsado		
			Case SubStr(AllTrim(SX3->X3_CAMPO),3)=="_COD"
				nPosProd := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_TOTAL"
				nPosTotal := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_VUNIT"
				nPosUnit  := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_TES"
				nPosTES  := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_UM"
				nPosUM  := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_SEGUM"
				nPosSegum  := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_NUMCQ"
				nPosNumCQ := nUsado			
			Case SubStr(alltrim(x3_campo),3) == "_LOCAL"
				nPosLoc  := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_PESO"
				nPosPeso := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_CONTA"
				nPosConta := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_ITEMCTA"
				nPosItCta := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_CC"
				nPosCC := nUsado
			Case SubStr(alltrim(x3_campo),3) == "_OP"
				nPosOP := nUsado
			Case Subs(alltrim(x3_campo),3) == "_CLASFIS"
		        nPosClaFis := nUsado			
			Case Subs(alltrim(x3_campo),3) == "_CLVL"
		        nPosCLVL := nUsado				        
			Case Subs(alltrim(x3_campo),3) == "_NFORI"
		        nPosNfOri := nUsado				        
			Case Subs(alltrim(x3_campo),3) == "_SERIORI"
		        nPosSeriOri := nUsado				        
			Case Subs(alltrim(x3_campo),3) == "_ITEMORI"
		        nPosItemOri := nUsado				        
	 		Case Subs(alltrim(x3_campo),3) == "_CODLAN"
		        nPosCodLan := nUsado				        
	 		Case Subs(alltrim(x3_campo),3) == "_OPER"
		        nPosOper := nUsado
	        Case Subs(alltrim(x3_campo),3) == "_RATEIO"
		   		nPosRat := nUsado
		   	Case Subs(alltrim(x3_campo),3) == "_CF"
		   		nPosCF := nUsado
		   	Case Subs(alltrim(x3_campo),3) == "_ORDEM"
		   		 nPosOrd := nUsado
			EndCase
		EndIf
		SX3->(dbSkip())
	EndDo
	
	//Adiciona os campos de Alias e Recno ao aHeader para WalkThru
	ADHeadRec("SD1",aHeader)
Endif

If lContinua .And. l116Inclui
	//Tratamento para rotina automatica
	If l116Auto
		cMarca   := GetMark(,"SF1","F1_OK")
		lInverte := .F.
		dbSelectArea("SF1")
		dbSetOrder(1)
		
		Eval(bFiltraBrw)
		If IsInCallStack("GFEA065In") // Limpar Filtro da SF1 Caso o tratamento seja do GFE
			SF1->(dbClearFilter())
		Endif

		For nX := 1 To Len(aAutoItens)
			If SF1->(DbSeek(xFilial("SF1")+aAutoItens[nX,1,2]))
				If Empty(cNFs)
					cNFs := "'" + aAutoItens[nX,1,2] + "'"
				Else
					cNFs += ",'" + aAutoItens[nX,1,2] + "'"
				Endif
				
				RecLock("SF1")
				SF1->F1_OK := cMarca
				MsUnLock()
			EndIf			
		Next nX
	Else
		cMarca   := ThisMark()
		lInverte := ThisInv()
	EndIf		

	dbSelectArea("SF1")

	SF1->(dbCommit())
	lQuery := .T.                      
	cAliasSF1 := "A116INCLUI"
	cAliasSD1 := cAliasSF1
	aStruSD1  := SD1->(dbStruct())

	cQuery := "SELECT SF1.F1_FILIAL, SF1.F1_DOC, SF1.F1_SERIE, SF1.F1_FORNECE, SF1.F1_LOJA, SF1.F1_TIPO,"
	cQuery += "       SF1.R_E_C_N_O_ SF1RECNO,   SF1.F1_OK,SD1.* "
	cQuery += "  FROM "+RetSqlName("SF1")+" SF1, "
	cQuery += RetSqlName("SD1")+" SD1 "
	cQuery += " WHERE "
	
	If !EMPTY(cQrySF1)
		cQuery += cQrySF1 + " AND "
	EndIf
	
	If ( lInverte )
		cQuery    += "SF1.F1_OK<>'"+cMarca+"' AND "
	Else
		cQuery    += "SF1.F1_OK='"+cMarca+"' AND "
	EndIf		
	
	cQuery += "     SF1.D_E_L_E_T_ = ' '"
	cQuery += " AND SD1.D1_FILIAL  = '"+xFilial("SD1")+"'"
	cQuery += " AND SD1.D1_SERIE   = SF1.F1_SERIE   "
	cQuery += " AND SD1.D1_DOC	   = SF1.F1_DOC 	"
	cQuery += " AND SD1.D1_FORNECE = SF1.F1_FORNECE "
	cQuery += " AND SD1.D1_LOJA    = SF1.F1_LOJA    "
	
	If lColab .Or. IsInCallStack("GFEA065In")
		cQuery += " AND SF1.F1_DOC||SF1.F1_SERIE||SF1.F1_FORNECE||SF1.F1_LOJA||SF1.F1_TIPO IN (" + cNFs + ")"
	Endif
	
	cQuery += " AND SD1.D_E_L_E_T_ = ' ' "
	cQuery += "ORDER BY "+SqlOrder(SF1->(IndexKey()))
	cQuery := ChangeQuery(cQuery)

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSF1)

	For nX := 1 To Len(aStruSD1)
		If aStruSD1[nX][2]<>"C"
			TcSetField(cAliasSD1,aStruSD1[nX][1],aStruSD1[nX][2],aStruSD1[nX][3],aStruSD1[nX][4])
		EndIf
	Next nX
	
	dbSelectArea(cAliasSF1)
	If (cAliasSF1)->(EOF())
		If ( l116Auto )
			lInclui := .F.
			lContinua := .F.
		EndIf
		HELP(" ",1,"RECNO", STR0059)
	Endif
	
	While !Eof() .And. xFilial("SF1") == (cAliasSF1)->F1_FILIAL
		lSkip := .F.
		If IsMark("F1_OK",cMarca,lInverte)
			If lQuery
				aadd(aRecSF1Ori,(cAliasSF1)->SF1RECNO)
			Else
				aadd(aRecSF1Ori,(cAliasSF1)->(RecNo()))
			EndIf
			If !lQuery
				dbSelectArea("SD1")
				dbSetOrder(1)
				MsSeek(xFilial("SD1")+(cAliasSF1)->F1_DOC+(cAliasSF1)->F1_SERIE+(cAliasSF1)->F1_FORNECE+(cAliasSF1)->F1_LOJA)
			EndIf
			aChave[1] := (cAliasSF1)->F1_DOC
			aChave[2] := (cAliasSF1)->F1_SERIE
			aChave[3] := (cAliasSF1)->F1_FORNECE
			aChave[4] := (cAliasSF1)->F1_LOJA

			While !Eof() .And. (cAliasSD1)->D1_FILIAL == xFilial("SD1") .And.;
					(cAliasSD1)->D1_DOC == aChave[1] .And.;
					(cAliasSD1)->D1_SERIE == aChave[2] .And.;
					(cAliasSD1)->D1_FORNECE == aChave[3] .And.;
					(cAliasSD1)->D1_LOJA == aChave[4]					

				//-- Auxiliar para verificação de itens com valor zerado
				aAdd(aItAux, GetAdvFVal("SF4", "F4_VLRZERO", cFilSF4 + (cAliasSD1)->D1_TES, 1, "2", .T.) == "1")
				
				If lMt116SD1
					lRet116SD1 := ExecBlock("MT116SD1",.F.,.F.,{(cAliasSD1)})
					If ValType(lRet116SD1) == "L" .And. !lRet116SD1
						dbSelectArea(cAliasSD1)
						dbSkip()					
						Loop
					EndIf
				EndIf

				If (cAliasSD1)->D1_VALISS == 0
					If Len(aCols) > 9999
						lAglutProd := .F.
					EndIf
										
					If (cAliasSD1)->D1_ORIGLAN $"FD|F | D" .And. lAviso .And. !l116auto
						lAviso := .F.
						Help(" ",1,"A116FRTVINC",,STR0045,1,0) //"Entre os itens selecionados ja existe um documento de frete e ou despesa de importacao vinculado."
					EndIf
					
					If lPrenota .and. !lAglutProd
						nX := 0
					Else
						nX	:= aScan(aCols,{|x| x[nPosProd] == (cAliasSD1)->D1_COD .And. x[nPosLoc] == (cAliasSD1)->D1_LOCAL ;
							.And. nPosNumCQ > 0 .and. x[nPosNumCQ] == (cAliasSD1)->D1_NUMCQ })
 					EndIf

 					// Para integracao com SIGAMNT deve preservar OP, OS, NF, Serie e Item da nota origem
					If lIntMnt
						lGravaOri := .F.
						If !Empty((cAliasSD1)->D1_OP) .And. !Empty((cAliasSD1)->D1_ORDEM) .And. ;
							nPosLoc > 0 .And. nPosNumCQ > 0 .And. nPosOP > 0 .And. nPosOrd > 0 .And. nPosNfOri > 0 .And. nPosSeriOri > 0 .And. nPosItemOri > 0
							lGravaOri := .T.
							nX := aScan(aCols,{|x|	x[nPosProd]  == (cAliasSD1)->D1_COD .And. x[nPosLoc] == (cAliasSD1)->D1_LOCAL .And. x[nPosNumCQ] == (cAliasSD1)->D1_NUMCQ .And. ;
													x[nPosOP]    == (cAliasSD1)->D1_OP  .And. x[nPosOrd] == (cAliasSD1)->D1_ORDEM .And. ;
													x[nPosNfOri] == (cAliasSD1)->D1_DOC .And. x[nPosSeriOri] == (cAliasSD1)->D1_SERIE .And. x[nPosItemOri] == (cAliasSD1)->D1_ITEM })
						EndIf
					EndIf

					If !lAglutProd .Or. nX==0
						aadd(aAmarrAFN, {})
						aadd(aCols,	Array(Len(aHeader)+1))
						nX	:= Len(aCols)
						If Empty(aChave[5]) 
							For nY := 1 to Len(aHeader)
								Do Case
									Case IsHeadRec(aHeader[nY][2])      
										aCols[nX][nY] := 0 
									Case IsHeadAlias(aHeader[nY][2])
										aCols[nX][nY] := "SD1"
									Case AllTrim(aHeader[nY][2]) == "D1_ITEM"
										cItem := Soma1(cItem,Len((cAliasSD1)->D1_ITEM))
										aCols[nX][nY] := cItem
									Case aHeader[nY][10] <> "V"
										aCols[nX][nY] := CriaVar(aHeader[nY][2])
									Case aHeader[nY][10] == "V" .And. GetSx3Cache(aHeader[nY][2],'X3_PROPRI') == 'U'
										aCols[nX][nY] := CriaVar(aHeader[nY][2])
								EndCase
	
								If cMVVeiculo == "S" .And. AllTrim(aHeader[nY][2]) $ "D1_CODGRP/D1_CODITE"
									aCols[nX][nY] := CriaVar(aHeader[nY][2])
								EndIf
				
								aCols[nX][Len(aHeader)+1] := .F.
							Next nY
							aChave[5] := aClone(aCols[1])
						Else
							aCols[nX] 		  := aClone(aChave[5])
							aCols[nX][nPItem] := (cAliasSD1)->D1_ITEM //Adiciona o código do item de acordo com o aCols
						EndIf
					EndIf
					
					If nPosOrd > 0
						aCols[nX,nPosOrd] := (cAliasSD1)->D1_ORDEM
					EndIf
					
					//Verifica os itens apontados ao SIGAPMS
					dbSelectArea("AFN")
					dbSetOrder(2)
					MsSeek(xFilial("AFN")+(cAliasSD1)->(D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_ITEM))
					While !Eof() .And. xFilial("AFN")+(cAliasSD1)->(D1_DOC+D1_SERIE+D1_FORNECE+D1_LOJA+D1_ITEM)==;
						AFN_FILIAL+AFN_DOC+AFN_SERIE+AFN_FORNEC+AFN_LOJA+AFN_ITEM
						If AFN->AFN_REVISA==PmsAF8Ver(AFN->AFN_PROJET)
							aAdd(aAmarrAFN[nx],{AFN->AFN_PROJET,AFN->AFN_REVISA,AFN->AFN_TAREFA,(cAliasSD1)->D1_TOTAL*(AFN->AFN_QUANT/(cAliasSD1)->D1_QUANT),(cAliasSD1)->D1_PESO*(AFN->AFN_QUANT/SD1->D1_QUANT),0,0,cItem,(cAliasSD1)->D1_COD, AFN->AFN_ESTOQU })
						EndIf
						dbSelectArea("AFN")
						dbSkip()
					EndDo
					aCols[nX,nPosProd]   := (cAliasSD1)->D1_COD
					aCols[nX,nPosLoc]    := (cAliasSD1)->D1_LOCAL
					If !lPreNota
						aCols[nX,nPosTes]    := aParametros[TES]
						If nPosNumCQ > 0
							aCols[nX,nPosNumCQ]  := (cAliasSD1)->D1_NUMCQ
                        Endif					
						dbSelectArea("SF4")
						dbSetOrder(1)	
						SF4->(DbSeek (xFilial ("SF4")+aCols[nX,nPosTes]))
						
						If nPosCF > 0 
							aCols[nx,nPosCF] := SF4->F4_CF
						EndIf
					EndIf
					aCols[nX,nPosUM]     := (cAliasSD1)->D1_UM
					If (!lAglutProd .And. lCusFifo) .Or. lColab .Or. lGravaOri
						aCols[nX,nPosNfOri]  := (cAliasSD1)->D1_DOC
						aCols[nX,nPosSeriOri]:= (cAliasSD1)->D1_SERIE
						aCols[nX,nPosItemOri]:= (cAliasSD1)->D1_ITEM
					Else
						aCols[nX,nPosNfOri]   :=  (cAliasSD1)->D1_NFORI 
						aCols[nX,nPosSeriOri] :=  (cAliasSD1)->D1_SERIORI
						aCols[nX,nPosItemOri] :=  (cAliasSD1)->D1_ITEMORI
					EndIf		
					SB1->(DbSeek (xFilial ("SB1")+aCols[nX,nPosProd]))
					
					If !Empty( nPosSegUM )
						aCols[nX,nPosSegUM] := (cAliasSD1)->D1_SEGUM
					EndIf
					If nPosClaFis<>0
						aCols[nX, nPosClaFis]:= Iif( GetNewPar("MV_STFRETE",.F.) , "0" , SB1->B1_ORIGEM ) + Iif (SF4->(FieldPos ("F4_SITTRIB"))>0, SF4->F4_SITTRIB, "  ")   // Comforme parecer da Consultoria Tributaria emitido no chamado SCSFW2
					EndIf
					If nPosConta >0
						aCols[nX,nPosConta] := (cAliasSD1)->D1_CONTA
					Endif
					If nPosItCta >0
						aCols[nX,nPosItCta] := (cAliasSD1)->D1_ITEMCTA
					Endif
					If nPosCC >0
						aCols[nX,nPosCC]    := (cAliasSD1)->D1_CC
					Endif
					If nPosCLVL >0
						aCols[nX,nPosCLVL]  := (cAliasSD1)->D1_CLVL
					Endif
					
					If nPosRat > 0 .And. l116Auto
						If ValType(aRatCC) == "A"
							If Len(aRatCC) > 0
								aCols[nX,nPosRat]  := "1"
							Else
								aCols[nX,nPosRat]  := "2"
							Endif
						Else
							aCols[nX,nPosRat]  := "2"
						Endif
					Endif
							
					aCols[nX,nPosTotal] += (cAliasSD1)->D1_TOTAL
					If nPosPeso > 0
						aCols[nX,nPosPeso]  += (cAliasSD1)->D1_PESO
						nPesoTotal += (cAliasSD1)->D1_PESO
					Endif
					If nPosLoc > 0 .And. (cAliasSD1)->D1_LOCAL == cLocCQ
						aCols[nX][nPosLoc] := cLocCQ
					EndIf
					If nPosOP>0
						aCols[nX,nPosOP] := (cAliasSD1)->D1_OP
						If !Empty(aCols[nX,nPosOP])
							If A116VerOP(aCols[nX,nPosOP]) // Verifica se OP do item do documento original esta encerrada
								If l116Auto // Se OP estiver encerrada e for rotina automatica, sempre limpa o campo D1_OP
									aCols[nX,nPosOP] := ""
									
									If nGeraSemOP == 2
										aCols[nX, len(aHeader) + 1] := .T. // exclui linha com a OP encerrada
									Endif 
								Else
									//Dado que existe um item do documento original que possui
									//vinculo com uma OP ja encerrada, pergunta se gera ou nao
									//a nota de conhecimento de frete para este item
									//SIM = inclui item na nota de frete, porem exclui o conteudo
									//do campo D1_OP para que o custo da movimentacao seja gerado
									//sobre o periodo aberto do estoque
									//NAO = nao inclui item na nota de frete (exclui linha do acols)								
										
									//Parametro MV_GERASOP define uma resposta padrao para a pergunta	
									If nGeraSemOP == 1
										aCols[nX,nPosOP] := "" // limpa OP para que nao seja gerado movimento RE5 para OP encerrada
									ElseIf nGeraSemOP == 2
										aCols[nX, len(aHeader) + 1] := .T. // exclui linha com a OP encerrada
									Else
										If A116GerSOP(aCols[nX,nPosOP], (cAliasSD1)->D1_DOC, (cAliasSD1)->D1_ITEM)
											aCols[nX,nPosOP] := "" // limpa OP para que nao seja gerado movimento RE5 para OP encerrada
										Else
											aCols[nX, len(aHeader) + 1] := .T. // exclui linha com a OP encerrada
										EndIf
									EndIf
								EndIf	
							EndIf	
						EndIf
					EndIf
					nTotal += (cAliasSD1)->D1_TOTAL   
					
					//CAT83
					If nPosCodLan >0 
						aCols[nX,nPosCodLan]:=A103CAT83(nX)    
					EndIf
					
					//Tratamento para utilizacao do campo Tipo de Operacao (D1_OPER)
					If nPosOper >0
						aCols[nX,nPosOper] := Space(TamSx3("D1_OPER")[1])
					Endif
                 
                	If l116Auto
						If nPosOper >0
                     	N := nX 
                       	iF NW:= ascan(aAutoCab, {|x| Upper(x[1]) == "D1_OPER" })>0
								NW:= ascan(aAutoCab, {|x| Upper(x[1]) == "D1_OPER" })
								aCols[nX,nPosOper] := aAutoCab[NW,2]
								aCols[nX,nPosTes]   := MaTesInt(1,aCols[nX,nPosOper],cA100For,cLoja,If(cTipo$"DB","C","F"),aCols[nX,nPosProd],"D1_TES")                        
							EndIf
						EndIf
					EndIf

					If lM116ACOL
						aM116aCol[1] := aChave[1]
						aM116aCol[2] := aChave[2]
						aM116aCol[3] := aChave[3]
						aM116aCol[4] := aChave[4]
						aM116aCol[5] := aCols[nX]
						ExecBlock("M116ACOL",.F.,.F.,{cAliasSD1,nX,aM116aCol})						
					EndIf
					
					//Inclui o item do acols que a aliquota eh zero
					If (cAliasSD1)->D1_PICM == 0
						Aadd(aItIcm,{nX,.F.})
					Else
						Aadd(aItIcm,{nX,.T.})
					EndIf
					FillCTBEnt(cAliasSD1,nX)					
				Else
					lTemIss := .T.
				EndIf
				
				If cMVVeiculo == "S" .and. FM_PILHA("VEIVM006")   
					if Type("aRetorn") <> "U"
						nPosVeic := ascan(aRetorn,{ |x| Alltrim(x[8]+"_"+x[1]) == Alltrim(aCols[nX,nPosProd])}) // Posição 1 do Vetor é o CHAINT , posição 8 grupo do item
						if nPosVeic > 0 
							aCols[nX,nPosTes]   := aRetorn[nPosVeic,7]  
							If nPosOper >0
								aCols[nX,nPosOper] := aRetorn[nPosVeic,6]
							Endif							
							If len(aRetorn[nPosVeic]) > 8
								aCols[nX,FG_POSVAR("D1_PICM")] := aRetorn[nPosVeic,9]
							EndIf
						Else
							aDel(aCols,nX)
							aSize( aCols, Len(aCols) - 1 )
							nTotal -= (cAliasSD1)->D1_TOTAL
							nPesoTotal -= (cAliasSD1)->D1_PESO
						Endif	
					Endif	
				Endif                  
				dbSelectArea(cAliasSD1)
				dbSkip()
				lSkip := lQuery
			EndDo
			If lTemIss
				MsgInfo(STR0055) //Há itens que não serão carregados para geração do conhecimento de frete, pois possuem valor de imposto ISS."
			Endif
		EndIf
		If !lSkip
			dbSelectArea(cAliasSF1)
			dbSkip()
		EndIf
	EndDo
	
	If lQuery
		dbSelectArea(cAliasSF1)
		dbCloseArea()
		dbSelectArea("SF1")
	EndIf

	//-- Valida se todos itens são de valor zerado
	For nX := 1 To Len(aItAux)
		If aItAux[nX]
			lTESVlZero := .T.
		Else
			lTESVlZero := .F.
			Exit
		EndIf
	Next nX
	
	//Rateio da do frete nos itens do conhecimento de frete
	For nX := 1 to Len(aCols)
		If (nRatFrete == 2 .Or. lTESVlZero) .And. nPesoTotal > 0  .And. nPosPeso > 0 
			aCols[nX][nPosTotal]	:= NoRound((aCols[nX][nPosPeso]/nPesoTotal)*aParametros[VALOR],2,@nDifTotal)
			If Round(nDifTotal,2) >= 0.01
				aCols[nX][nPosTotal]	+= Round(nDifTotal,2)
				nDifTotal				-= Round(nDifTotal,2)
			EndIf
			aCols[nX][nPosUnit]	:= aCols[nX][nPosTotal]
			
			For nW := 1 to Len(aAmarrAFN[nX])
				nResto := 0
				aAmarrAFN[nX,nW][6] := NoRound((aAmarrAFN[nX,nW][5]/nPesoTotal)*aParametros[VALOR],2,@nResto)
				aAmarrAFN[nX,nW][7]	 := aCols[nX][nPosTotal]
				If Round(nResto,2) >= 0.01
					aAmarrAFN[nX,nW][6] += Round(nResto,2)
				EndIf
			Next nW
		Else
			aCols[nX][nPosTotal]	:= NoRound((aCols[nX][nPosTotal]/nTotal)*aParametros[VALOR],2,@nDifTotal)
			If Round(nDifTotal,2) >= 0.01
				aCols[nX][nPosTotal]	+= Round(nDifTotal,2)
				nDifTotal				-= Round(nDifTotal,2)
			EndIf
			aCols[nX][nPosUnit]	:= aCols[nX][nPosTotal]
			
			For nW := 1 to Len(aAmarrAFN[nX])
				nResto := 0
				aAmarrAFN[nX,nW][6] := NoRound((aAmarrAFN[nX,nW][4]/nTotal)*aParametros[VALOR],2,@nResto)
				aAmarrAFN[nX,nW][7] := aCols[nX][nPosTotal]
				If Round(nResto,2) >= 0.01
					aAmarrAFN[nX,nW][6] += Round(nResto,2)
				EndIf
			Next nW
		EndIf                                          

		If aCols[nX][nPosTotal] == 0 .And. !lColab
			aCols[nX][Len(aHeader)+1] := .T.
		Endif     
		
	Next nX
	
	If !A116ITCOL(aCols) //Sem Itens para inclusão
		lContinua := .F.
		HELP(" ",1,"A116ITCOL",STR0060) //"Não há itens ativos para confirmação do conhecimento."
	Endif		
	
	If lContinua
		//Tratamento da quebra por item de nota
		If cFormul=="S"
			nMaxItem   := a460NumIt(cSerie,.T.)
			nY := 0
			For nX := 1 To Len(aCols)
				If nY==0
					aadd(aNotas,{})
				EndIf
				If !aCols[nX,len(aHeader) + 1]
					aadd(aNotas[Len(aNotas)],aCols[nX])
				EndIf	
				nY++
				If nY == nMaxItem
					nY := 0
				EndIf
			Next nX
		Else
			If len(aCols) > 0 
				// Adiciona no array aNotas apenas os itens do aCols que nao estao deletados
				aColsAux := {}
				For nX := 1 To Len(aCols)
					If !aCols[nX,len(aHeader) + 1]
						aadd(aColsAux,aCols[nX])
					EndIf	
				Next nX
				aadd(aNotas,aColsAux)
			EndIf
		EndIf
	Endif
		
ElseIf lContinua .And. !l116Inclui
	//Abertura da funcao fiscal
	If !lPreNota
		MaFisIni(cA100For,cLoja,"F","C",SA2->A2_TIPO,MaFisRelImp("MT100",{"SD1","SF1"}),"F",.T.,,,,,,,,,,,,,,,,,,,,,,,,,lTrbGen)
	EndIf		
	
	//Altera a origem do conhecimento de Frete
	If !Empty(cUfOrig) .Or. !lPreNota
		MaFisAlt("NF_UFORIGEM",cUfOrig)
	EndIf
	
	//Trava os registros do SF1 - Exclusao
	If l116Exclui
		If !SoftLock("SF1")
			lContinua := .F.
		Endif
	EndIf
	
	If l116Visual .Or. l116Exclui
		//Monta array contendo os registros fiscais SF3
		dbSelectArea("SF3")
		dbSetOrder(4)
		MsSeek(xFilial("SF3")+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_DOC+SF1->F1_SERIE)
		While !Eof().And.lContinua.And. xFilial("SF3")+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_DOC+SF1->F1_SERIE == ;
				F3_FILIAL+F3_CLIEFOR+F3_LOJA+F3_NFISCAL+F3_SERIE
			If Substr(SF3->F3_CFO,1,1) < "5"
				aadd(aRecSF3,RecNo())
				//Trava os registros do SF3 - exclusao
				If l116Exclui
					If !SoftLock("SF3")
						lContinua := .F.
					Endif
				EndIf
			EndIf
			dbSkip()
		End
	EndIf
	
	//Monta o Array contendo as registros do SDE
	If l116Visual .Or. l116Exclui
		dbSelectArea("SDE")
		dbSetOrder(1)
		If MsSeek(xFilial("SDE")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
			If Empty(aBackSDE)
				dbSelectArea("SX3")
				dbSetOrder(1)
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
							SX3->X3_ARQUIVO,;
							SX3->X3_CONTEXT })
					EndIf
					dbSelectArea("SX3")
					dbSkip()
				EndDo
				aHeadSDE  := aBackSDE
				
				//Adiciona os campos de Alias e Recno ao aHeader para WalkThru
				ADHeadRec("SDE",aHeadSDE)
			EndIf
			
			dbSelectArea("SDE")
			
			While !Eof() .And. lContinua .And. xFilial("SDE")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA==;
					SDE->DE_FILIAL+SDE->DE_DOC+SDE->DE_SERIE+SDE->DE_FORNECE+SDE->DE_LOJA
				aadd(aRecSDE,SDE->(RecNo()))
				If cItemSDE != 	SDE->DE_ITEMNF
					cItemSDE	:= SDE->DE_ITEMNF
					aadd(aColsSDE,{cItemSDE,{}})
					nItemSDE	:= Len(aColsSDE)
				EndIf
				aadd(aColsSDE[nItemSDE][2],Array(Len(aHeadSDE)+1))
				For nY := 1 to Len(aHeadSDE)
					If IsHeadRec(aHeadSDE[nY][2])
						aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := SDE->(Recno()) 
					ElseIf IsHeadAlias(aHeadSDE[nY][2])
						aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := "SDE"
					ElseIf ( aHeadSDE[nY][10] != "V")
						aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := FieldGet(FieldPos(aHeadSDE[nY][2]))
					Else
						aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][nY] := CriaVar(aHeadSDE[nY][2])
					EndIf
					aColsSDE[nItemSDE][2][Len(aColsSDE[nItemSDE][2])][Len(aHeadSDE)+1] := .F.
				Next nY
				//Trava os registros do SDE - exclusao
				If l116Exclui
					If !SoftLock("SDE")
						lContinua := .F.
					Endif
				EndIf
				dbSkip()
			End
		EndIf
	EndIf
	If l116Exclui
		aRecSF8	:=	A116GetSF8(@lContinua)
	EndIf
	
	//Monta o Array contendo as duplicatas SE2
	If ( l116Visual .Or. l116Exclui ) .And. Empty(aRecSE2)
		dbSelectArea('SE2')
		dbSetOrder(6)
		If MsSeek(xFilial("SE2")+SF1->F1_FORNECE+SF1->F1_LOJA+cPrefixo+SF1->F1_DOC)
			While !Eof() .And. lContinua .And.xFilial("SE2")+SF1->F1_FORNECE+SF1->F1_LOJA+cPrefixo+SF1->F1_DOC==;
					E2_FILIAL+E2_FORNECE+E2_LOJA+E2_PREFIXO+E2_NUM .And. lContinua
				If !(SE2->E2_VALOR == SE2->E2_SALDO)
					lContinua := .F.
					HELP(" ",1,"A100FINBX")
					Exit
				EndIf
				aadd(aRecSE2,RecNo())
				//Trava os registros do SE2 - exclusao
				If l116Exclui
					If !SoftLock("SE2")
						lContinua := .F.
					Endif
				EndIf
				dbSkip()
			EndDo
		EndIf
	EndIf
	
	//Faz a montagem do aCols com os dados do SD1
	dbSelectArea("SD1")
	dbSetOrder(1)
	MsSeek(xFilial('SD1')+cNFiscal+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
	While !Eof().And.lContinua .And. SD1->D1_FILIAL+SD1->D1_DOC+SD1->D1_SERIE+SD1->D1_FORNECE+SD1->D1_LOJA ==	;
			xFilial('SD1')+cNFiscal+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA

		//Trava os registros na alteracao e  exclusao
		If l116Exclui
			If !SoftLock("SD1")
				lContinua := .F.
			Else
				aadd(aRecSD1,{RecNo(),SD1->D1_ITEM })
			Endif
		EndIf
		aadd(aCols,Array(Len(aHeader)+1))
		For nY := 1 to Len(aHeader)
			If IsHeadRec(aHeader[nY][2])
				aCols[Len(aCols)][nY] := SD1->(Recno())  
			ElseIf IsHeadAlias(aHeader[nY][2])
				aCols[Len(aCols)][nY] := "SD1"
			ElseIf ( aHeader[nY][10] != "V")
				aCols[Len(aCols)][nY] := FieldGet(FieldPos(aHeader[nY][2]))
			Else
				aCols[Len(aCols)][nY] := CriaVar(aHeader[nY][2])
			EndIf
			aCols[Len(aCols)][Len(aHeader)+1] := .F.
		Next nY
		
		//Inicia a Carga do item nas funcoes MATXFIS
		If !lPreNota
			MaFisIniLoad(Len(aCols),,,Iif(lTrbGen,SD1->D1_IDTRIB,""))
			For nX := 1 to Len(aAuxRefSD1)
				//Carrega os valores direto do SD1
				If SD1->(FieldPos(aAuxRefSD1[nX][1])) > 0
					MaFisLoad(aAuxRefSD1[nX][2],&("SD1->"+aAuxRefSD1[nX][1]),Len(aCols))
				Endif
			Next nX
			MaFisEndLoad(Len(aCols),2)
			
			For nX := 1 to Len(aAuxRefSF1)
				//Carrega os valores direto do SF1
				If SF1->(FieldPos(aAuxRefSF1[nX][1])) > 0
					MaFisLoad(aAuxRefSF1[nX][2],&("SF1->"+aAuxRefSF1[nX][1]))
				Endif
			Next nX
		EndIf			
		dbSelectArea("SD1")
		dbSkip()
	EndDo
	//Monta um Array de Notas conforme o numero de itens
	aadd(aNotas,aCols)
EndIf

If lContinua .And. ExistBlock("MT116GRV")
	EXECBLOCK("MT116GRV",.F.,.F.)
Endif

If lContinua .And. Len(aNotas) > 0 .And. Len(aNotas[1]) > 0 
	If cPaisLoc == "BRA" .And. Type("lIntermed") == "L" .And. lIntermed .And. cFormul == "S" .And. Len(aRecSF1Ori) > 0
		aAreaInt	:= GetArea()
		SF1->(DbGoto(aRecSF1Ori[1]))
		aInfAdic[16] := SF1->F1_INDPRES
		aInfAdic[17] := SF1->F1_CODA1U
		RestArea(aAreaInt)
	Endif
	//Verifica o numero maximo de itens da nota fiscal
	For nX := 1 To Len(aNotas)
		If nX >= 2 .And. cFormul == "S"
			cNFiscal := NxtSX5Nota(cSerie)
		EndIf
		If l116Inclui
			dbselectarea("SA2")
				If lImpfor == .T.
				   IF DbSeek(xfilial('SA2')+aParametros[10]+aParametros[11]) //Posiciona no fornecedor do conhecimento de frete para verificar se tem exceção fiscal
					  cGrpTrib := SA2->A2_GRPTRIB
				   Endif					 			
				Else
				   IF DbSeek(xfilial('SA2')+SF1->F1_FORNECE+SF1->F1_LOJA) 
					  cGrpTrib := SA2->A2_GRPTRIB
				   Endif  				
		       Endif	
			//Abertura da funcao fiscal
			If !lPreNota .and. !Empty(cGrpTrib)
				MaFisIni(cA100For,cLoja,"F","C",SA2->A2_TIPO,MaFisRelImp("MT100",{"SD1","SF1"}),"F",.T.,,,,cEspecie,,cGrpTrib,,,,,,,,,,,,,,,,,,,lTrbGen)
			Else 			  
				MaFisIni(cA100For,cLoja,"F","C",SA2->A2_TIPO,MaFisRelImp("MT100",{"SD1","SF1"}),"F",.T.,,,,cEspecie,,,,,,,,,,,,,,,,,,,,,lTrbGen)
			EndIf				
			
			If l116Auto .And. l116Inclui .And. Len(aAutoCab) >= 21 .And. !lPreNota .AND. nPosNat >0 .AND. !Empty(aAutoCab[nPosNat,2]) 
				MaFisAlt("NF_NATUREZA",aAutoCab[nPosNat,2])
			EndIf
				
			//Altera a origem do conhecimento de Frete
			If !Empty(cUfOrig) .Or. !lPreNota
				MaFisAlt("NF_UFORIGEM",cUfOrig)
			EndIf
			
			If l116Auto .And. l116Inclui .And. SF1->(ColumnPos("F1_UFORITR")) > 0 .And. SF1->(ColumnPos("F1_UFDESTR")) > 0
				If ProcH("F1_UFORITR") > 0 .And. !Empty(aAutoCab[ProcH("F1_UFORITR"),2])
					MaFisAlt("NF_UFORIGEM",aAutoCab[ProcH("F1_UFORITR"),2])
					cUfOrig := MaFisRet(,"NF_UFORIGEM")
					cUfOri  := cUfOrig 
				Endif
					
				If ProcH("F1_UFDESTR") > 0 .And. !Empty(aAutoCab[ProcH("F1_UFDESTR"),2])
					MaFisAlt("NF_UFDEST",aAutoCab[ProcH("F1_UFDESTR"),2])
				Endif
			Endif
 
			//Preparacao do acols para o conhecimento de frete
			aCols := aNotas[nX]
			If l116Inclui
				cItem := StrZero(0,Len(SD1->D1_ITEM))
				For nY := 1 To Len(aCols)
					cItem := Soma1(cItem,Len(SD1->D1_ITEM))
					aCols[nY][nPItem]   := cItem
					For nw := 1 to Len(aAmarrAFN[ny])
						aAmarrAFN[ny,nw][8]	 := cItem
					Next nw
				Next nY
			EndIf
			If !lPreNota
				//Carrega os impostos
				MaColsToFis(aHeader,aCols,,"MT100",.T.)
			
				If lAzFrete .and. !lImpfor
		 			For nY := 1 to Len(aItIcm)
		 				If !aItIcm[nY,2]
							MaFisAlt("IT_ALIQICM",0,aItIcm[nY,1])
						Endif
					Next nY
				EndIf
				
				If (nZ:= ascan(aAutoCab, {|x| Upper(x[1]) == "IT_ALIQICM" })) > 0
					If lAzFrete .and. !lImpfor 
						For nY := 1 to Len(aItIcm)
							If !aItIcm[nY,2]
								MaFisAlt("IT_ALIQICM",0,aItIcm[nY,1])
							Else
								MaFisAlt("IT_ALIQICM",aAutoCab[nZ,2],aItIcm[nY,1])
							Endif
						Next nY
					Else
						For nY := 1 to Len(aItIcm)
							MaFisAlt("IT_ALIQICM"  ,aAutoCab[nZ,2],  aItIcm[nY,1])
						Next nY
					Endif
				EndIf

				If aParametros[16]<>0 .And. aParametros[17]<>0
					MaFisAlt("NF_BASESOL",aParametros[16])
					MaFisAlt("NF_VALSOL",aParametros[17])
				EndIf

				If (nY:= ascan(aAutoCab, {|x| Upper(x[1]) == "NF_BASEICM" })) > 0
					MaFisAlt("NF_BASEICM"  ,aAutoCab[nY,2])
				EndIf

				If (nY:= ascan(aAutoCab, {|x| Upper(x[1]) == "NF_VALICM" })) > 0
					MaFisAlt("NF_VALICM" ,aAutoCab[nY,2])	
				EndIf			
						
				MaFisToCols(aHeader,aCols,,"MT100",.T.)			
			EndIf			
		Else
			aCols := aNotas[nX]
		EndIf

		//Inicializa lancamento de integracao com SIGAPCO
		If !lColab
			PcoIniLan("000054")
		EndIf

		If lDKD //Tem DKD, verifica se tem campos adicionais para serem apresentados
			lTabAuxD1 := A103DKD(.F.,l103Visual) //MATA103COM
		Endif
		
		If !( l116Auto )

			aInfo := { aSizeAut[ 1 ], aSizeAut[ 2 ], aSizeAut[ 3 ], aSizeAut[ 4 ], 3, 3 }

			aPosGet := MsObjGetPos(aSizeAut[3]-aSizeAut[1],310,;
				{If(lSubSerie,{8,30,72,92,130,150,180,200,235,250,275,295},{8,35,75,100,140,165,194,220,260,280}),;
				{8,35,75,100,nPosGetLoja,165,194,220,260,280},;
				{5,70,160,205,295},;
				{6,34,200,215},;
				{6,34,75,103,148,164,230,253},;
				{6,34,200,218,280},;
				{11,50,150,190},;
				{273,130,190,293,205},;
				{005,025,065,085,125,145,185,205,250,275},;
				{3,4}})

			DEFINE MSDIALOG oDlg FROM aSizeAut[7],0 TO aSizeAut[6],aSizeAut[5] TITLE cCadastro Of oMainWnd PIXEL

			oSize := FwDefSize():New(.T.,,,oDlg)

			oSize:AddObject('HEADER',100,40,.T.,.F.)
			oSize:AddObject('GRID'  ,100,10,.T.,.T.)
			oSize:AddObject('FOOT'  ,100,90,.T.,.F.)		
			
			oSize:aMargins 	:= { 3, 3, 3, 3 }
			oSize:Process()

			aAdd(aPosObj,{oSize:GetDimension('HEADER', 'LININI'),oSize:GetDimension('HEADER', 'COLINI'),oSize:GetDimension('HEADER', 'LINEND'),oSize:GetDimension('HEADER', 'COLEND')})
			aAdd(aPosObj,{oSize:GetDimension('GRID'  , 'LININI'),oSize:GetDimension('GRID'  , 'COLINI'),oSize:GetDimension('GRID'  , 'LINEND'),oSize:GetDimension('GRID'  , 'COLEND')})
			aAdd(aPosObj,{oSize:GetDimension('FOOT'  , 'LININI'),oSize:GetDimension('FOOT'  , 'COLINI'),oSize:GetDimension('FOOT'  , 'LINEND'),oSize:GetDimension('FOOT'  , 'COLEND')})
			
			//Objeto criado para receber o foco quando pressionado o botao confirma
			//da dialog. Usado para identificar quando foi pressionado o botao
			//confirma, atraves do parametro passado ao lostfocus
			@ 100000,100000 MSGET oFoco103 VAR cVarFoco SIZE 12,09 PIXEL OF oDlg 
			oFoco103:Cargo := {.T.,.T.}
			oFoco103:Disable()

			NfeCabDoc(oDlg,{aPosGet[1],aPosGet[2],aPosObj[1]},@bCabOk,.F..Or.l103Visual,,cUfOrig,,,@nCombo,@oCombo,@cCodRet,@oCodRet,,,@cRecIss,,,,aNfeDanfe)

			If !lDKD .Or. (lDKD .And. !lTabAuxD1)
				oGetDados := MSGetDados():New(aPosObj[2,1],aPosObj[2,2],aPosObj[2,3],aPosObj[2,4],nOpcx,{||A116LinOk(lPreNota)},'A116TudOk(' +If(lPreNota, "'P'", "'N'") + ')',+'D1_ITEM',.T.,aCpos2,,,900,,,,'NfeDelItem')
			Else
				oGetDados := MSGetDados():New(aPosObj[2,1],aPosObj[2,2],aPosObj[2,3]-50,aPosObj[2,4],nOpcx,{||A116LinOk(lPreNota)},'A116TudOk(' +If(lPreNota, "'P'", "'N'") + ')',+'D1_ITEM',.T.,aCpos2,,,900,,,,'NfeDelItem')

				oGetDKD		:= MsNewGetDados():New(aPosObj[2,3]-50,aPosObj[2,2],aPosObj[2,3],aPosObj[2,4],Iif(nOpcx == 2,0,GD_UPDATE+GD_INSERT+GD_DELETE),/*"a103xLOk"*/"",/*"a103xLOk"*/"","+DKD_ITEM",aAltDKD,/*freeze*/,1,/*fieldok*/,/*superdel*/,/*"LancDel("+cVisual+")*/"",oDlg,aHeadDKD,aColsDKD)
				If l103Visual
					A103DKDATU(1) 
				Endif 
			Endif

			oGetDados:oBrowse:bGotFocus	:= bCabOk
			oGetDados:oBrowse:bChange := {|| Iif(lTrbGen, MaFisLinTG(oFisTrbGen,oGetDados:oBrowse:nAt) ,.T.),;
											 Iif(lDKD .And. lTabAuxD1,A103DKDATU(),.T.) }

			oFolder := TFolder():New(aPosObj[3,1],aPosObj[3,2],aTitles,{"AHEADER"},oDlg,,,, .T., .F.,aPosObj[3,4]-aPosObj[3,2],aPosObj[3,3]-aPosObj[3,1],)
			oFolder:bSetOption := {|nDst| NfeFldChg(nDst,oFolder:nOption,oFolder,aFldCBAtu)}
			bRefresh := {|nX| NfeFldChg(nX,oFolder:nOption,oFolder,aFldCBAtu)}

			//Folder dos Totalizadores
			oFolder:aDialogs[1]:oFont := oDlg:oFont
			NfeFldTot(oFolder:aDialogs[1],aValores,aPosGet[3],@aFldCBAtu[1])
			
			//Folder dos Fornecedores
			oFolder:aDialogs[2]:oFont := oDlg:oFont
			NfeFldFor(oFolder:aDialogs[2],aInfForn,{aPosGet[4],aPosGet[5],aPosGet[6]},@aFldCBAtu[2])
			
			//Folder das Despesas acessorias e descontos
			oFolder:aDialogs[3]:oFont := oDlg:oFont
			NfeFldDsp(oFolder:aDialogs[3],aValores,{aPosGet[7],aPosGet[8]},@aFldCBAtu[3])
			
			//Folder dos Livros Fiscais
			oFolder:aDialogs[4]:oFont := oDlg:oFont	
			oLivro := MaFisBrwLivro(oFolder:aDialogs[4],{5,4,( aPosObj[3,4]-aPosObj[3,2] ) - 10,53},.T.,IIf(!.F.,aRecSF3,Nil),.F.) 
			aFldCBAtu[4] := {|| oLivro:Refresh()}
			
			//Folder dos Impostos
			oFolder:aDialogs[5]:oFont := oDlg:oFont	
		    MaFisRodape(nTpRodape,oFolder:aDialogs[5],,{5,4,( aPosObj[3,4]-aPosObj[3,2] )-10,53},@bIPRefresh,l103Visual,@cFornIss,@cLojaIss,aRecSE2,@cDirf,@cCodRet,@oCodRet,@nCombo,@oCombo,@dVencIss,@aCodR,@cRecIss,@oRecIss)
   		    
   		   	//Folder do Financeiro
			oFolder:aDialogs[6]:oFont := oDlg:oFont			
			NfeFldFin(oFolder:aDialogs[6],l103Visual,aRecSE2,( aPosObj[3,4]-aPosObj[3,2] ) - 101,,@aHeadSE2,@aColsSE2,@aHeadSEV,@aColsSEV,@aFldCbAtu[6],.T.,@cModRetPIS,lPccBaixa,,,,@aColTrbGen,@nColsSE2,@aParcTrGen)

			//Folder dos Lancamentos Apuracao ICMS - Sped
			If !lPreNota
				If nLancAp>0
					oFolder:aDialogs[nLancAp]:oFont := oDlg:oFont
					If  FindFunction("a017xLAICMS")
						oLancCDV := a017xLAICMS(oFolder:aDialogs[nLancAp],{5,4,( aPosObj[3,4]-aPosObj[3,2] )-10,53},aHeadCDV,aColsCDV,l116Visual,l116Inclui,"SD1")
					Endif
					oLancApICMS := a103xLAICMS(oFolder:aDialogs[nLancAp],{5,4,( aPosObj[3,4]-aPosObj[3,2] )-10,53},@aHeadCDA,@aColsCDA,l116Visual,l116Inclui,"MATA116")
			    	If Type("oLancApICMS")=="O"  .And. cPaisLoc == "BRA" //grazi
				    	a103AjuICM(0) //Funcao para atualizar o objeto do mata103 (TFOLDER) com as informacoes referentes ao lancamento fiscal. 
					EndIf
				EndIf
			EndIf					

			//Montagem do Folder Informacoes Diversas
			oFolder:aDialogs[nInfDiv]:oFont := oDlg:oFont			
			NfeFldDiv(oFolder:aDialogs[nInfDiv],{aPosGet[9]})

			// -- Folder de Tributos Genericos
			If lTrbGen
				oFolder:aDialogs[nTrbGen]:oFont := oDlg:oFont 
				oFisTrbGen := MaFisBrwTG(oFolder:aDialogs[nTrbGen],{5,4,( aPosObj[3,4]-aPosObj[3,2] ) - 10,65}, l116Visual)
				aFldCBAtu[nTrbGen] := {|| IIf(lTrbGen , MaFisLinTG(oFisTrbGen,oGetDados:oBrowse:nAt) , .T.) }				
			EndIf

			//Transfere o foco para a getdados - nao retirar
			oFoco103:bGotFocus := { || oGetDados:oBrowse:SetFocus() }
			
			If l116OriDest
				oFolder:aDialogs[nInfAdic]:oFont := oDlg:oFont
				NfeFldAdic(oFolder:aDialogs[nInfAdic],{aPosGet[10]},@aInfAdic,,,,.T.)
			Endif		
		
			ACTIVATE MSDIALOG oDlg ON INIT (EnchoiceBar(oDlg,{||Eval(bRefresh,IIf(oFolder:nOption==6,1,6)).And.oFoco103:Enable(),oFoco103:SetFocus(),oFoco103:Disable(),If(oGetDados:TudoOk() .And.  NfeTOkSEV(@aHeadSev, @aColsSev,.F.) .And. a116CDAOk() .And. oFoco103:Cargo[1].And. If(l116Inclui,NfeTotFin(aHeadSE2,aColsSE2,.F.,,nColsSE2,aColTrbGen),.T.) .And. NfeVldSEV(oFoco103:Cargo[2],aHeader,aCols,aHeadSEV,aColsSEV) .And. IIf(l116Inclui,A103ChamaHelp(),.T.) .And. IIf(l116Inclui,A103ConsCTE(aNfeDanfe[18]),.T.) .And. NfeNextDoc(@cNFiscal,@cSerie,l116Inclui),(nOpc:=1,oDlg:End()),Eval({||nOpc:=0,oFoco103:Cargo[1] :=.T.}))},{||nOpc:=0,oDlg:End()},,aButtons),Eval(bRefresh))
			
			SetKey( VK_F4, Nil )
		Else
			//Gerando informacoes dos lanctos da apuracao de ICMS
			If !lPreNota
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
			 	
			//Quando for rotina automatica tera que validar o linhaok e o
			//tudook para isso nao e necessario colocar as funcoes espe-
			//cificas de validacao automatica
			If Len(aCols) > 0
				nOpc := 1
				For nPosicao := 1 To Len(aCols)
					n := nPosicao
					If !A116LinOk(lPreNota,lColab)
						nOpc := 0
						lContinua := .F.
						Exit
					EndIf
				Next		
				cCondicao := aAutoCab[18,2]			
				If nOpc == 0 .Or. !A116TudOk(If(lPreNota,'P','N'),l116Exclui,lColab)
					nOpc := 0
					lContinua := .F.
				Else
					NfeFldFin(,l103Visual,aRecSE2,0,,@aHeadSE2,@aColsSE2,@aHeadSEV,@aColsSEV,@aFldCbAtu[6],,,,,,,@aColTrbGen,@nColsSE2,@aParcTrGen)
					Eval(aFldCbAtu[6])
					Eval(bRefresh,6,6)
				EndIf
			Else
				nOpc := 0
				lContinua := .F.
				HELP(" ",1,"RECNO", STR0059)
			EndIf
		EndIf                                         
		
		If nOpc == 1 .And. (l116Inclui .Or. l116Exclui)  
			//Ponto de entrada para permitir ou nao a exclusao
			If lMT116OK
				lRet := Execblock("MT116OK",.F.,.F.,{l116Exclui})
				If ValType(lRet) <> "L"
					lRet := .T.
				EndIf
			EndIf
			                   
			//Verifica se existe bloqueio contábil
			If lRet
			 
				If l116Exclui
					dCtbValiDt := SF1->F1_DTDIGIT
				Else
					dCtbValiDt := dDataBase
				Endif

				lRet := CtbValiDt(Nil,dCtbValiDt,/*.T.*/ ,Nil ,Nil ,{"COM001"}/*,"Data de apuração bloqueada pelo calendário contábil."*/)
			
			EndIf

			If lRet 
				If cMVVeiculo == "S" .And. FindFunction("VA1800101_ValidarA116Inclui")
					lRet := VA1800101_ValidarA116Inclui( nOpcDMS , nRecSF1 , aRecSF1Ori )
				EndIf
			EndIf
			                   
			If lRet
				//Limpa o Filtro do SF1 para ser executada a gravacao em AS400
				If TcSrvType()=="AS/400"
	  				SF1->(dbClearFilter())
	  			Endif
				
				//Inicializa a gravacao atraves nas funcoes MATXFIS
				If !lPreNota
					MaFisWrite()                    
				EndIf					                    				
				
				//Indregua para o PIS / COFINS / CSLL
				 
				Begin Transaction
					//Ponto de entrada para customizacao do usuario
					If lMt116Cust
						ExecBlock("MT116CUST",.F.,.F.,{l116Inclui,l116Exclui})
					EndIf	
					If lColab
						A116IGrava(aCols, aAutoItens,nPosPicm)
					Else
						If l116Exclui
							aAtuExc := A116CredP(l116Exclui,aRecSF8)
						Endif
							
						a103GrvCDA(l116Exclui,"E",cEspecie,cFormul,cNFiscal,cSerie,cA100For,cLoja,aInfApurICMS)
						If Type("oLancCDV")=="O" 
							a017GrvCDV(l116Exclui,"E",cEspecie,cFormul,cNFiscal,cSerie,cA100For,cLoja,aInfApurICMS)
						Endif

						If !lPrenota
							If l116Auto .And. !Empty(aRatcc)
			  				   	If Empty(aHeadSDE)
							   		dbSelectArea("SX3")
									dbSetOrder(1)
									MsSeek("SDE")
									While ( !EOF() .And. SX3->X3_ARQUIVO == "SDE" )
										If X3USO(SX3->X3_USADO) .AND. cNivel >= SX3->X3_NIVEL .And. !"DE_CUSTO"$SX3->X3_CAMPO
											aadd(aHeadSDE,{ TRIM(X3Titulo()),;
											SX3->X3_CAMPO,;
											SX3->X3_PICTURE,;
											SX3->X3_TAMANHO,;
											SX3->X3_DECIMAL,;
											SX3->X3_VALID,;
											SX3->X3_USADO,;
											SX3->X3_TIPO,;
											SX3->X3_ARQUIVO,;
											SX3->X3_CONTEXT })
										EndIf
										dbSelectArea("SX3") 
										dbSkip()
									EndDo
								   
								   //Adiciona os campos de Alias e Recno ao aHeader
				                 	ADHeadRec("SDE",aHeadSDE)
								EndIf
								For nA := 1 To Len(aCols)
									RatPed2NF(aHeadSDE,@aColsSDE,aCols[nA][GdFieldPos("D1_ITEM",aHeader)],0,aRatcc)
								Next nA
							EndIf
	  				   		a103Grava(l116Exclui,lGeraLanc,	lDigita,lAglutina, aHeadSE2, aColsSE2,aHeadSEV,aColsSEV,@nRecSF1,aRecSD1,aRecSE2,aRecSF3,aRecSC5,aHeadSDE,aColsSDE,aRecSDE,.T.,.F.,@aRecSF1Ori,aRatVei,aRatFro,cFornIss,cLojaIss,Nil,Nil,Nil,Nil,Nil,nIndexSE2,Nil,dVencIss,Nil,Nil,Nil,Nil,Nil,Nil,aCodR,cRecIss,Nil,aCtbInf,aNfeDanfe,Nil,aDigEnd,Nil,Nil,Nil,aInfAdic,,,,,,,aParcTrGen)
	  				    Else	   				   			  				   		
							MA140Grava(l116Exclui,{},{0,0,0,0,0,0,0,0},,,,.T.,@nRecSF1,,Iif(l116Auto,.T.,.F.))	  				   		
	  				   	EndIf
						A116Grava(l116Exclui,nRecSF1,aRecSF1Ori,aRecSF8,aAmarrAFN,aAtuExc)

						If cMVVeiculo == "S" .And. FindFunction("VA1800031_A116Inclui")
							VA1800031_A116Inclui( nOpcDMS , nRecSF1 , aRecSF1Ori )
						EndIf

					EndIf
				End Transaction  
				
				//Executa gravacao da contabilidade
				If !lColab .And. Len(aCtbInf) != 0
					//Cria nova transacao para garantir atualizacao do documento
					Begin Transaction
						cA100Incl(aCtbInf[1],aCtbInf[2],3,aCtbInf[3],aCtbInf[4],aCtbInf[5],,,,aCtbInf[7],,aCtbInf[6])
					End Transaction		
				EndIf
	
				If !lColab .And. lMT116AGR
					ExecBlock("MT116AGR",.F.,.F.)
				EndIf
				
				//Apaga o arquivo da Indregua
				If !InTransact()
					SF1->(dbSetOrder(1))
					Eval(bFiltraBrw)			
				Endif
	    	EndIf
		EndIf

		//Quando for TOTVS Colaboracao nao deve permitir a gravacao apenas do cabecalho da nota sem os itens
		If nOpc == 0 .And. lColab
			lMsErroAuto := .T.
			lContinua := .F.
		EndIf

		//Finaliza a gravacao dos lancamentos do SIGAPCO e apaga lancamentos de bloqueio nao utilizados
		If !lColab
			PcoFinLan("000054")
			PcoFreeBlq("000054")
		EndIf
	
		If !lPreNota
			MaFisEnd()
		EndIf			
	Next nX
ElseIf lContinua .And. lColab
	lContinua := .F.
	HELP(" ",1,"RECNO", STR0059)
EndIf

//Destrava os registros na alteracao e exclusao
If l116Exclui
	MsUnlockAll()
EndIf

If !l116Auto
	CloseBrowse()
EndIf    

SF1->(dbSetOrder(1))
SF1->(dbSeek(xFilial("SF1")))

//Limpa a variavel dMudaEmi
SetVar113(cToD(""))

Return lContinua

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116LinOk ³ Autor ³ Edson Maricate        ³ Data ³08.02.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Critica se a linha digitada esta' Ok                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA116                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A116LINOK(lPreNota,lColab)
Local lRet	:= .T.
Local aArea	:= GetArea()
Local nPosCod,nPosUm,nPosQuant,nPosVUnit,nPosTotal
Local nPosTes,nPosCfo
Local nx := 0

Default lColab := .F.

//Verifica preenchimento dos campos da linha do acols
If CheckCols(n,aCols)

	For nX:= 1 To Len(aHeader)
		cCampo:=AllTrim(aHeader[nX][2])
		Do Case
		Case cCampo == 'D1_COD'
			nPosCod		:= nX
		Case cCampo == 'D1_UM'
			nPosUm		:= nX
		Case cCampo == 'D1_QUANT'
			nPosQuant	:= nX
		Case cCampo == 'D1_VUNIT'
			nPosVunit	:= nX
		Case cCampo == 'D1_TOTAL'
			nPosTotal 	:= nX
		Case cCampo == 'D1_TES'
			nPosTes		:= nX
		Case cCampo == 'D1_CF'
			nPosCFO		:= nX
		Case cCampo == 'D1_LOCAL'
			nPosLoc    := nX
		EndCase
	Next nX
	
	If !aCols[n][Len(aCols[n])] 
		Do Case
		Case Empty(aCols[n][nPosCod]) .Or. ;
				If(lColab,.F.,Empty(aCols[n][nPosVUnit])) .Or. ;
				If(lColab,.F.,Empty(aCols[n][nPosTotal])).Or. ;
				If(lPreNota, .F., Empty(aCols[n][nPosCFO]))  .Or. ;
 				If(lPreNota, .F., !Empty(nPosTES) .And. Empty(aCols[n][nPosTES]))
 			lRet := .F.
			Help("  ",1,"A100VZ")
		Case !lPreNota .And. !Empty(nPosTes) .And. !ExistCpo('SF4',aCols[n][nPostes])
			lRet := .F.
		EndCase
	EndIf
	
	//Verifica a permissao do armazem
	If lRet
		lRet := MaAvalPerm(3,{aCols[n][nPosLoc],aCols[n][nPosCod]})
	EndIf
	
	//Template acionando ponto de entrada
	If lRet .And. (ExistTemplate("MT100LOK"))
		lRet := ExecTemplate("MT100LOK",.F.,.F.,{lRet})
		If ValType(lRet) <> "L"
			lRet := .T.
		EndIf
	EndIf
	
	//Ponto de Entrada Padrao
	If lRet .And. (ExistBlock("MT100LOK"))
		lRet := ExecBlock("MT100LOK",.F.,.F.,{lRet})
		If ValType(lRet) <> "L"
			lRet := .T.
		EndIf
	EndIf
	
	//Valida PCO
	If lRet 
		lRet:=	PcoVldLan("000054","01","MATA103",/*lUsaLote*/,/*lDeleta*/, .T./*lVldLinGrade*/)
	Endif

	RestArea(aArea)
EndIf

Return lRet

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116TudOk ³ Autor ³ Edson Maricate        ³ Data ³08.02.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Critica se as linhas digitadas estao OK.                   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA116                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A116Tudok(cTipo,l116Exclui,lColab)
Local lRet		:= .T.     
Local lVerChv   := SuperGetMv("MV_VCHVNFE",.F.,.F.)
Local cNFForn   := ""
Local nNFNum    := ""
Local nNFSerie	:= ""
Local lPreNota  := .F.
Local cNatValid	  := MaFisRet(,"NF_NATUREZA")

Default cTipo := 'N'
Default l116Exclui := .F.
Default lColab		:= .F.

lPreNota :=  cTipo == 'P'

//Verifica a condicao de pagamento.
If !lPreNota  .And. GDFieldPos("D1_TES") > 0
	If MaFisRet(,"NF_BASEDUP") > 0 .And. Empty(cCondicao)
		lRet := .F.
		HELP("  ",1,"A100COND")
	EndIf
	
	//Verifica a natureza
	If !lPreNota .And. MaFisRet(,"NF_BASEDUP") > 0 .And. Empty(MaFisRet(,"NF_NATUREZA")) .And. cTipo<>"D"
		If SuperGetMV("MV_NFENAT") .And. !SuperGetMV("MV_MULNATP") .And. !l116Exclui
			lRet := .F.
			Help("  ",1,"A103NATURE")
		EndIf
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

//Verifica se o total da NF esta negativo/zerado devido ao valor do desconto
If !lPreNota .And. MaFisRet(,"NF_TOTAL")<=0 .And. !l116Exclui .And. !lColab 
	lRet := .F.
	Help("  ",1,'TOTAL')
EndIf

//Ponto de Entrada Padrao
If lRet .And. (ExistBlock("MT116TOK"))
	lRet := ExecBlock("MT116TOK",.F.,.F.)
	If ValType(lRet) <> "L"
		lRet := .T.
	EndIf
EndIf
        
//Valida se Chave NFE confere com a nota que está sendo digitada
If lRet .And. lVerChv .And. cFormul == "N" .And. cTipo<>"D" .And. !Empty(aNfeDanfe[13])
	cNFForn  := SubStr(aNfeDanfe[13],7,14)			// CNPJ Emitente conforme manual Nota Fiscal Eletrônica
	nNFNum   := Val(SubStr(aNfeDanfe[13],26,9))		// Número da nota conforme manual Nota Fiscal Eletrônica
	nNFSerie := Val(SubStr(aNfeDanfe[13],23,3))		// Série da nota conforme manual Nota Fiscal Eletrônica
	If Posicione("SA2",1,xFilial("SA2")+cA100For+cLoja,"A2_CGC") == cNFForn .And. Val(cNFiscal) == nNFNum .And. Val(cSerie) == nNFSerie
		lRet := .T.
	Else
		lRet := .F.
		Help(" ",1,"A116CHVNFE",,STR0052,1,0)
	EndIf
EndIf

If lRet 
	
	lRet := A103VldObr()
	
EndIf

If lRet .And. lDKD .And. lTabAuxD1 .And. !l116Auto
	//Atualiza aColsDKD
	A103DKDATU() 
Endif

Return lRet


/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116Grava ³ Autor ³ Edson Maricate        ³ Data ³08.02.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Complementa a gravacao da NF de Frete                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA116                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A116Grava(l116Exclui,nRecSF1,aRecSF1Ori,aRecSF8,aAmarrAFN,aAtuExc)

Local aArea	    := GetArea() 
Local aAreaSF1	:= SF1->(GetArea())
Local aAreaSD1	:= SD1->(GetArea())

Local nX        := 0
Local nY        := 0
Local nW        := 0   
Local nA        := 0
Local nDecAFN   := TamSX3("AFN_QUANT")[2]
Local nDecSD1   := TamSX3("D1_CUSTO")[2]
Local nSD1Qtd   := 0
Local nInd      := 0
Local aCusto    := {}
Local aSD1Vlr   := {}
Local cMvEstado := SuperGetMV("MV_ESTADO")
Local nResult   := 0
Local nLimite   := 0 
Local nLimAtu	:= 0
Local nTotal    := 0
Local nTotalCP  := 0
Local nDifTotal := 0
Local aResult   := {}
Local lContinua := .F.
Local aAtuSD1	:= {}
Local cSeFreSDO := ' '
Local cIdFrete 	:= ""
Local lTPCPRES  := SF4->(FieldPos("F4_TPCPRES")) > 0
Local lCRDPRES  := SF4->(FieldPos("F4_CRDPRES")) > 0

Default aAtuExc := {}

If !l116Exclui
	dbSelectArea("SF1")
	MsGoto(nRecSF1)
	cNfFrete := SF1->F1_DOC
	cSeFrete := SF1->F1_SERIE
	cSeFreSDO := If (SerieNfId("SF8",3,"F8_SEDIFRE") == 'F8_SDOCFRE',	SF1->F1_SDOC, '')	
	cForFrete:= SF1->F1_FORNECE
	cLojFrete:= SF1->F1_LOJA
	cIdFrete := SF1->F1_MSIDENT
	
	For nX := 1 to Len(aRecSF1Ori)
		dbSelectArea("SF1")	
		MsGoto(aRecSF1Ori[nX])
		dbSelectArea("SF8")
		RecLock("SF8",.T.)
		SF8->F8_FILIAL	:= xFilial("SF8")
		SF8->F8_DTDIGIT := SF1->F1_DTDIGIT
		SF8->F8_NFDIFRE	:= cNfFrete
		SF8->F8_SEDIFRE	:= cSeFrete
		SF8->F8_TRANSP	:= cForFrete
		SF8->F8_LOJTRAN	:= cLojFrete
		SF8->F8_NFORIG	:= SF1->F1_DOC
		SF8->F8_SERORIG	:= SF1->F1_SERIE
		SF8->F8_FORNECE	:= SF1->F1_FORNECE
		SF8->F8_LOJA	:= SF1->F1_LOJA
		SF8->F8_TIPO	:= "F"
		If SerieNfId("SF8",3,"F8_SEDIFRE") == 'F8_SDOCFRE'				
			SF8->F8_SDOCFRE := cSeFreSDO
		EndIf
		If SerieNfId("SF8",3,"F8_SERORIG") == 'F8_SDOCORI'				
			SF8->F8_SDOCORI := SF1->F1_SDOC
		EndIf	
		MsUnlock()
		dbSelectArea("SF1")
		RecLock("SF1",.F.)
		SF1->F1_ORIGLAN	:= If(SF1->F1_ORIGLAN==" D","FD","F ")
		SF1->F1_OK      := ""
		MsUnlock()

		nSD1Qtd   := 0
		dbSelectArea("SD1")
        dbClearFilter()        
        dbSetOrder(1)
		MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
        While ( !Eof() .And. SD1->D1_FILIAL == xFilial("SD1") .And.;
					            SD1->D1_DOC    == SF1->F1_DOC    .And.;
				 	            SD1->D1_SERIE  == SF1->F1_SERIE  .And.;
					            SD1->D1_FORNECE== SF1->F1_FORNECE.And.;
					            SD1->D1_LOJA   == SF1->F1_LOJA )	
			RecLock("SD1",.F.,.T.)
			SD1->D1_ORIGLAN   := If(SD1->D1_ORIGLAN==" D","FD","F ")
			MsUnlock()
			If SD1->D1_QUANT >0 
				aAdd( aSD1Vlr ,{ cNFFrete,cSeFrete,cForFrete,cLojFrete,SD1->D1_COD,SD1->D1_QUANT } )
			EndIf
			
			//Calculo Crédito Presumido Santa Catarina
			//RICMS - Anexo 02 - Benefícios Fiscais - Capitulo III (Art. 18)
			If cPaisLoc == "BRA" .AND. cMvEstado=="SC" .and. lCRDPRES .AND. lTPCPRES
				dbSelectArea("SF4")
				SF4->(dbClearFilter())
				SF4->(dbSetOrder(1))
				SF4->(dbSeek(xFilial("SF4")+SD1->D1_TES))
	       		If SF4->F4_TPCPRES == "F"  
					dbSelectArea("SFT")
					SFT->(dbClearFilter())
					SFT->(dbSetOrder(1))
					SFT->(dbSeek(xFilial("SFT")+"E"+SD1->D1_SERIE+SD1->D1_DOC+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_ITEM+SD1->D1_COD))
	        	   	// Adiciona ao vetor os itens e seus respectivos limites de credito presumido
	        	   	aAdd(aResult, { SD1->D1_FILIAL,;
	        	   					SD1->D1_DOC,;
	        	   					SD1->D1_SERIE,;
	        	   					SD1->D1_FORNECE,;
	        	   					SD1->D1_LOJA,;
	        	   					SD1->D1_COD ,;
	        	   					SD1->D1_ITEM,;
	        	   					SD1->D1_TOTAL,;
	        	   					NoRound((SFT->FT_VALCONT * SF4->F4_CRDPRES) / 100,2),;
	        	   					SD1->D1_CRPRESC})
					lContinua := .T.
				EndIf
			EndIf
			dbSelectArea("SD1")
			dbSkip()
		EndDo
	Next nX
	
	//Continuacao do Calculo Credito Presumido SC
	If lContinua

		// Atualizar os dados das notas originais
		For nX := 1 to Len(aRecSF1Ori)
			
			nResult  := 0
			nLimite  := 0
			nLimAtu	 := 0
			nTotal   := 0
			nTotalCP := 0
			
			dbSelectArea("SF1")
			MsGoto(aRecSF1Ori[nX])
			
			// obtem o valor total de cada nota original
			For nY := 1 to Len(aResult)
				If (aResult[nY][1] == SF1->F1_FILIAL .And. aResult[nY][2] == SF1->F1_DOC .And. aResult[nY][3] == SF1->F1_SERIE  .And. aResult[nY][4] == SF1->F1_FORNECE .And. aResult[nY][5] == SF1->F1_LOJA)
					nTotal += aResult[nY][8]
				EndIf
			Next nY
			
			// Atualizar os itens da nota original com o valor de crédito presumido
			dbSelectArea("SD1")
	        dbClearFilter()        
	        dbSetOrder(1)
			MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
	        Do While ( !Eof() .And. SD1->D1_FILIAL == xFilial("SD1") .And.;
						            SD1->D1_DOC    == SF1->F1_DOC    .And.;
					 	            SD1->D1_SERIE  == SF1->F1_SERIE  .And.;
						            SD1->D1_FORNECE== SF1->F1_FORNECE.And.;
						            SD1->D1_LOJA   == SF1->F1_LOJA )

				// Localizar o item na NF de origem
				If (nY := aScan( aResult, {|x| x[1] == SD1->D1_FILIAL .and. x[2] == SD1->D1_DOC .and. x[3] == SD1->D1_SERIE .and. x[4] == SD1->D1_FORNECE .and. x[5] == SD1->D1_LOJA .and. x[6] == SD1->D1_COD .and. x[7] == SD1->D1_ITEM .and. x[9] > 0 })) > 0

					// Definir o limite de crédito presumido para o item
					nLimite := NoRound((aResult[nY][8]/nTotal)*aParametros[VALOR],2,@nDifTotal)
					nLimAtu := Iif(Round(nDifTotal,2) >= 0.01,nLimite+=Round(nDifTotal,2),nLimite)
					nLimite += Iif(aResult[nY][10]>0,NoRound(aResult[nY][10],2,@nDifTotal),0)
					If Round(nDifTotal,2) >= 0.01
						nLimite	  += Round(nDifTotal,2)
						nDifTotal -= Round(nDifTotal,2)
					EndIf
					
					// Define qual e o valor do crédito presumido para o item
					nResult := IIf( (aResult[nY][9] > nLimite), aResult[nY][9], nLimite)
					
					// Atualizar os itens da nota original
					If cPaisLoc == "BRA"
						RecLock("SD1",.F.,.T.)
						SD1->D1_CRPRESC := nResult
						MsUnlock()
					EndIf
					//Alimento o array com os valores dos creditos presumidos calculados, para atualizar
					//depois nos itens do conhecimento de frete.
	           		aAdd(aAtuSD1, { cNfFrete,;
	           						cSeFrete,;
	           						cForFrete,;
	           						cLojFrete,;
	           						SD1->D1_COD ,;
	           						SD1->D1_ITEM,;
	           						Iif(nLimite<>nResult,nResult-aResult[nY][10],nLimAtu)})								

					// Atualizar os itens do livro fiscal da nota original
					// com o valor de crédito presumido apurado
					If cPaisLoc == "BRA"
						dbSelectArea("SFT")
				       	SFT->(dbClearFilter())
				       	SFT->(dbSetOrder(1))
						SFT->(dbSeek(xFilial("SFT")+"E"+SD1->D1_SERIE+SD1->D1_DOC+SD1->D1_FORNECE+SD1->D1_LOJA+SD1->D1_ITEM+SD1->D1_COD))
						If SFT->(FieldPos("FT_CRDPRES"))>0
							RecLock("SFT",.F.)
							SFT->FT_CRDPRES := SD1->D1_CRPRESC
							MsUnlock()
						EndIf
					

					// Acumular o valor do crédito presumido
					nTotalCP += SD1->D1_CRPRESC
					EndIf
				EndIf
				dbSelectArea("SD1")
				dbSkip()
			EndDo

			// Atualizar o livro fiscal da nota original 
			// com o valor de crédito presumido apurado
		   	dbSelectArea("SF3")
		   	SF3->(dbClearFilter())
		   	SF3->(dbSetOrder(4))
			SF3->(dbSeek(xFilial("SF3")+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_DOC+SF1->F1_SERIE))
			If cPaisLoc == "BRA"
				If !EOF() .And. SF3->(FieldPos("F3_CRDPRES"))>0
					RecLock("SF3",.F.)
					SF3->F3_CRDPRES := nTotalCP
					MsUnlock()
				EndIf
			EndIf			
		Next nX
	EndIf

	//Atualizo os itens do conhecimento com os valores do cred pres
	For nA := 1 to Len(aAtuSD1)
		SD1->(dbSetOrder(1))
		If SD1->(MsSeek(xFilial("SD1")+aAtuSD1[Na][1]+aAtuSD1[Na][2]+aAtuSD1[Na][3]+aAtuSD1[Na][4]+aAtuSD1[Na][5]+aAtuSD1[Na][6])) .And. cPaisLoc == "BRA"
			If SD1->(FieldPos("D1_CRPRESC"))>0
				RecLock("SD1",.F.)
				SD1->D1_CRPRESC := aAtuSD1[Na][7]
				MsUnlock()
			EndIf		
		Endif		
	Next nA
	
	//Grava a tabela de apontamento do SIGAPMS
	For ny := 1 to Len(aAmarrAFN)
		For nw := 1 to Len(aAmarrAFN[ny])
			If aAmarrAFN[nY][nW][6] > 0
				RecLock("AFN",.T.)
				AFN->AFN_FILIAL := xFilial("AFN")
				AFN->AFN_PROJET := aAmarrAFN[nY][nW][1]
				AFN->AFN_REVISA := aAmarrAFN[nY][nW][2]
				AFN->AFN_TAREFA := aAmarrAFN[nY][nW][3]
				AFN->AFN_QUANT  := aAmarrAFN[nY][nW][6]/aAmarrAFN[nY][nW][7]
				AFN->AFN_DOC    := cNfFrete
				AFN->AFN_SERIE  := cSeFrete
				AFN->AFN_FORNEC := cForFrete
				AFN->AFN_LOJA   := cLojFrete
				AFN->AFN_ITEM   := aAmarrAFN[ny][nw][8]
				AFN->AFN_TIPONF := cTipo
				AFN->AFN_COD    := aAmarrAFN[ny][nw][9]
				If SerieNfId("AFN",3,"AFN_SERIE") == 'AFN_SDOC'				
					AFN->AFN_SDOC := cSeFreSDO
				EndIf
				AFN->AFN_ID 	:= cIdFrete

				If ValType( aAmarrAFN[ny][ nw ][ 10 ] ) == 'C'
					AFN->AFN_ESTOQU := IIf( Empty( aAmarrAFN[ny][ nw ][ 10 ] ), CriaVar( 'AFN_ESTOQU', .t. ), aAmarrAFN[ny][ nw ][ 10 ] )
				Else
					AFN->AFN_ESTOQU := CriaVar( 'AFN_ESTOQU', .t. )
				EndIf
				
				MsUnlock()
				 
				// busca pela nota de entrada q está gerando o frete
				If (nPos := aScan( aSD1Vlr ,{|x| x[1] == cNfFrete .and. x[2] == cSeFrete .and. x[3] == cForFrete .and. x[4] == cLojFrete .and. x[5] == aAmarrAFN[nY][nW][9] }))>0
					// calcula o percentual a ser rateado pro projeto e tarefa					
					nInd := NoRound(aAmarrAFN[nY][nW][6]/aAmarrAFN[nY][nW][7]*100,nDecAFN)/100
				Else
					nInd := 0
				Endif
				
				SD1->(dbSetOrder(1))
				If SD1->(MsSeek(xFilial("SD1")+cNfFrete + cSeFrete + cForFrete + cLojFrete + aAmarrAFN[nY][nW][9] ))
					aCusto := { NoRound( SD1->D1_CUSTO*nInd  ,nDecSD1 ) ;
					           ,NoRound( SD1->D1_CUSTO2*nInd ,nDecSD1 ) ;
					           ,NoRound( SD1->D1_CUSTO3*nInd ,nDecSD1 ) ;
					           ,NoRound( SD1->D1_CUSTO4*nInd ,nDecSD1 ) ;
					           ,NoRound( SD1->D1_CUSTO5*nInd ,nDecSD1 ) }
				EndIf
				PmsAvalAFN("AFN",1,.T.,aCusto)
			EndIf
		Next nw
	Next ny	
Else
	For nX	:= 1 to Len(aRecSF8)
		dbSelectArea("SF8")
		MsGoto(aRecSF8[nX])
        dbSelectArea("SF1")
        dbClearFilter()        
        dbSetOrder(1)
        
        // Guardo as informacoes nota fiscal original    
        If SF1->(dbSeek(xFilial("SF1")+SF8->F8_NFORIG+SF8->F8_SERORIG+SF8->F8_FORNECE+SF8->F8_LOJA+"N")) .Or.;
		   SF1->(dbSeek(xFilial("SF1")+SF8->F8_NFORIG+SF8->F8_SERORIG+SF8->F8_FORNECE+SF8->F8_LOJA+"D")) .Or. ;
		   SF1->(dbSeek(xFilial("SF1")+SF8->F8_NFORIG+SF8->F8_SERORIG+SF8->F8_FORNECE+SF8->F8_LOJA+"B"))

      	  Reclock("SF1",.F.,.T.)
	      SF1->F1_ORIGLAN   := If(SF1->F1_ORIGLAN=="FD"," D","  ")
      	  MsUnlock()
          
		  nLimAtu := 0
		  
		  dbSelectArea("SD1")
	      dbClearFilter()        
	      dbSetOrder(1)
          MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
          While ( !Eof() .And. SD1->D1_FILIAL  == xFilial("SD1")  .And.;
					            SD1->D1_DOC     == SF1->F1_DOC     .And.;
				 	            SD1->D1_SERIE   == SF1->F1_SERIE   .And.;
					            SD1->D1_FORNECE == SF1->F1_FORNECE .And.;
					            SD1->D1_LOJA    == SF1->F1_LOJA )
	
	          RecLock("SD1",.F.,.T.)
	          SD1->D1_ORIGLAN   := IIF(SD1->D1_ORIGLAN=="FD"," D","  ")		
	          If cPaisLoc == "BRA"	
	          If (FieldPos("D1_CRPRESC"))>0 .And. Len(aAtuExc)>0
	          	  If (nY := aScan( aAtuExc, {|x| x[1] == SF8->F8_NFDIFRE .And. x[2] == SF8->F8_SEDIFRE .And. x[3] == SF8->F8_FORNECE .And. x[4] == SF8->F8_LOJA .And. x[5] == SD1->D1_COD .And. x[6] == SD1->D1_ITEM })) > 0
		              SD1->D1_CRPRESC   -= aAtuExc[nY][7] //deduzo o valor do credito presumido do item do conhecimento 			
		      	  	  nLimAtu 			+= aAtuExc[nY][7]		
		      	  Endif
	          EndIf
	          EndIf
	          MsUnlock()		
	
	          dbSelectArea("SD1")
	          dbSkip()
	      EndDo
		  If nLimAtu > 0
			  dbSelectArea("SF3")
			  SF3->(dbClearFilter())
			  SF3->(dbSetOrder(4))
			  MsSeek(xFilial("SF3")+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_DOC+SF1->F1_SERIE)
		  	  While ( !Eof() .And.  SF3->F3_FILIAL  == xFilial("SF3") .And.;
		      			             SF3->F3_NFISCAL == SF1->F1_DOC    .And.;
					 	             SF3->F3_SERIE   == SF1->F1_SERIE  .And.;
						             SF3->F3_CLIEFOR == SF1->F1_FORNECE.And.;
						             SF3->F3_LOJA    == SF1->F1_LOJA )
			If cPaisLoc == "BRA"
				  RecLock("SF3",.F.,.T.)
				  If SF3->(FieldPos("F3_CRDPRES"))>0
				      SF3->F3_CRDPRES -= nLimAtu
				  EndIf
		    	  MsUnlock()
		    EndIf		
	         	  dbSelectArea("SF3")
	         	  dbSkip()
	      	  EndDo

		      dbSelectArea("SFT")
			  SFT->(dbClearFilter())
			  SFT->(dbSetOrder(3))
			  MsSeek(xFilial("SFT")+"E"+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_SERIE+SF1->F1_DOC)
			  While ( !Eof() .And. SFT->FT_FILIAL  == xFilial("SFT") .And.;
						              SFT->FT_NFISCAL == SF1->F1_DOC    .And.;
					 	              SFT->FT_SERIE   == SF1->F1_SERIE  .And.;
						              SFT->FT_CLIEFOR == SF1->F1_FORNECE.And.;
						              SFT->FT_LOJA    == SF1->F1_LOJA )
				
				  RecLock("SFT",.F.,.T.)
				  If SFT->(FieldPos("FT_CRDPRES"))>0
				      SFT->FT_CRDPRES -= nLimAtu
				  EndIf				
	              MsUnlock()		
		          dbSelectArea("SFT")
		          dbSkip()
		      EndDo
	        EndIf
	    Endif
        dbSelectArea("SF8")
		RecLock("SF8",.F.,.T.)
		dbDelete()
		MsUnlock()
	Next
	dbSelectArea("SF1")
EndIf
RestArea(aArea)  
RestArea(aAreaSF1)
RestArea(aAreaSD1)

Return

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116VldExc³ Autor ³ Edson Maricate        ³ Data ³07.01.2000³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Verifica se a NF pode ser excluida.                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function A116VldExc(nRecSF1,aRecSC5)

Local lRet		:= .T.
Local lRetPE	:= .F.
Local l100DelT	:= ExistTemplate('A100DEL') 
Local lIntACD	:= SuperGetMV("MV_INTACD",.F.,"0") == "1"
Local l100Del	:= ExistBlock('A100DEL')
Local dDataFec	:= MVUlmes()

dbSelectArea("SF1")
dbGoto(nRecSF1)

Do Case
	//Nao excluir NF nao classificada
Case Empty(SF1->F1_STATUS)
	lRet := .F.
	HELP(" ",1,"A100NOCLAS")
	//Verificar data do ultimo fechamento em SX6
Case dDataFec>=dDataBase .Or. dDataFec>=SF1->F1_DTDIGIT
	lRet := .F.
	Help( " ", 1, "FECHTO" )
	//Verifica ultima data para operacoes fiscais
Case !FisChkExc(SF1->F1_SERIE,SF1->F1_DOC,SF1->F1_FORNECE,SF1->F1_LOJA)
	lRet := .F.
	//Ponto de entrada para permitir ou nao a exclusao
Case l100DelT .And. ValType(lRetPE := ExecTemplate("A100DEL",.F.,.F.) ) == "L" .And. ! lRetPE
	lRet := .F.
Case l100Del .And. ValType(lRetPE := Execblock("A100DEL",.F.,.F.) ) == "L" .And. ! lRetPE
	lRet := .F.
	//Chamada para integracao com o modulo ACD
Case lIntACD .And. !(CBA100DEL())
	lRet := .F.
EndCase

Return lRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116GetSF8³ Autor ³ Bruno Sobieski        ³ Data ³22.07.2002³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Pega os registros do SF8 referentes a nota fiscal atual     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116,LOCXNF (NAO DEFINIR COMO STATIC!!!)                 ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function A116GetSF8(lContinua)
Local aRet	:=	{}

//Carrega os itens do SF8
dbSelectArea("SF8")
dbSetOrder(1)
MsSeek(xFilial("SF8")+SF1->F1_DOC+SF1->F1_SERIE)		
Do While !Eof() .And. xFilial("SF8")+SF1->F1_DOC+SF1->F1_SERIE == F8_FILIAL+F8_NFDIFRE+F8_SEDIFRE .And. lContinua
	If xFilial("SF8")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA  != F8_FILIAL+F8_NFDIFRE+F8_SEDIFRE+F8_TRANSP+F8_LOJTRAN
		dbSkip()
		Loop
	EndIf
	If !SoftLock("SF8")
		lContinua	:= .F.
	EndIf
	aadd(aRet,RecNo())
	dbSkip()
End

Return aRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116ChkTES³ Autor ³ Nereu Humberto Junior ³ Data ³05.11.2004³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Verifica se o TES digitado e de entrada.                    ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpC1: Codigo do TES                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL: Validacao do Tipo de Entrada/Saida (TES)              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function A116ChkTES(cCodTES)

Local lRet := .T.
If SubStr(cCodTES,1,1) >= "5" .And. cCodTES <> "500"
	lRet := .F.
	HELP("   ",1,"INV_TE")
Endif

Return (lRet)

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116ChkTra³ Autor ³ Mary C. Hergert       ³ Data ³25/07/2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Verifica se o fornecedor da nota fiscal de frete (transpor- ³±±
±±³          ³tadora) e igual ao fornecedor de pesquisa e barra a         ³±±
±±³          ³inclusao atraves de parametro.                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpC1: Codigo do Fornecedor - transportadora                ³±±
±±³          ³ExpC2: Loja do Fornecedor - transportadora                  ³±±
±±³          ³ExpC3: Codigo do Fornecedor - pesquisa                      ³±±
±±³          ³ExpC4: Loja do Fornecedor - pesquisa                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ExpL: Validacao do fornecedor                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function A116ChkTra(c116Fornece,c116Loja,c116FornOri,c116LojaOri)

Local lRet 		:= .T.
Local lCkTrans	:= GetNewPar("MV_CKTRANS",.F.) 

If lCkTrans
	If c116Fornece == c116FornOri .And. c116Loja == c116LojaOri
		lRet := .F.
		HELP("",1,"A116CKTR")
	Endif
Endif

Return (lRet)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116CredP ³ Autor ³ Luciana Pires         ³ Data ³29.04.2009³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Verifica os creditos presumidos na exclusão do conhec. frete³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA116                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A116CredP(l116Exclui,aRecSF8)
Local aArea	    := GetArea()
Local nX        := 0
Local cMvEstado := SuperGetMV("MV_ESTADO")
Local aAtuExc	:= {}

If l116Exclui
	For nX	:= 1 to Len(aRecSF8)
		dbSelectArea("SF8")
		MsGoto(aRecSF8[nX])
        dbSelectArea("SF1")
        dbClearFilter()        
        dbSetOrder(1)
        // Guardo as informacoes credito presumido SC - nota conhecimento de frete
    If cPaisLoc == "BRA"
		If cMvEstado=="SC" .And. SD1->(FieldPos("D1_CRPRESC"))>0 .And. SF4->(FieldPos("F4_CRDPRES"))>0
 			If SF1->(dbSeek(xFilial("SF1")+SF8->F8_NFDIFRE+SF8->F8_SEDIFRE+SF8->F8_TRANSP+SF8->F8_LOJTRAN+"C"))
		
				dbSelectArea("SD1")
		      	dbClearFilter()        
		      	dbSetOrder(1)
	          	MsSeek(xFilial("SD1")+SF1->F1_DOC+SF1->F1_SERIE+SF1->F1_FORNECE+SF1->F1_LOJA)
	          	While ( !SD1->(Eof()) .And. SD1->D1_FILIAL == xFilial("SD1") .And.;
								            SD1->D1_DOC    	== SF1->F1_DOC     .And.;
					 			            SD1->D1_SERIE  	== SF1->F1_SERIE   .And.;
						        		    SD1->D1_FORNECE	== SF1->F1_FORNECE .And.;
						            		SD1->D1_LOJA   	== SF1->F1_LOJA )
		
					//Alimento o array com os valores dos creditos presumidos calculados, para atualizar
					//depois nos itens do conhecimento de frete.
			    	If SD1->D1_CRPRESC > 0
				        AAdd(aAtuExc, {SD1->D1_DOC,;   			//1
				         				SD1->D1_SERIE,; 		//2
				         				SD1->D1_FORNECE,; 		//3
		    		     				SD1->D1_LOJA,;    		//4
		        		 				SD1->D1_COD,;     		//5
		         						SD1->D1_ITEM,;     		//6
		         						SD1->D1_CRPRESC})		//7							
					  	//Depois de guardar para deduzir da nota original, eu zero o valor do credito do item do 
					  	//conhecimento de frete
					  	RecLock("SD1",.F.)
						SD1->D1_CRPRESC   := 0 			
						MsUnlock()
					Endif					        	  	
	        	  	SD1->(dbSkip())
				EndDo	   			
			Endif	
        Endif
     EndIf
	Next
EndIf
RestArea(aArea)

Return(aAtuExc)

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³a116CDAOk ³ Autor ³ Microsiga SA          ³ Data ³31/05/2009³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Funcao para validar a linha do acols de lancamentos         ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³.T. ou .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Nenhum                                                      ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³   DATA   ³ Programador   ³Manutencao efetuada                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³               ³                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function a116CDAOk()
Local	lRet	:=	.T.
Local	nPosLanc:=	0
Local	nPosVlr	:=	0
Local	nNumIte	:=	0
Local   nPosClPr := 0

If Type("oLancApICMS")=="O"
	nPosLanc:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CODLAN"})
	nPosVlr:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_VALOR"})
	nNumIte:=	aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_NUMITE"})
	nPosClPr:=  aScan(oLancApICMS:aHeader,{|aX|aX[2]=="CDA_CALPRO"})

	If oLancApICMS:aCols[oLancApICMS:nAT,nPosClPr] <> "1"
		If !oLancApICMS:aCols[oLancApICMS:nAT,Len(oLancApICMS:aCols[oLancApICMS:nAT])] .And.;
			!Empty(oLancApICMS:aCols[oLancApICMS:nAT,nNumIte])
			
			If nPosLanc>0 .And. Empty(oLancApICMS:aCols[oLancApICMS:nAT,nPosLanc])
				lRet := .F.
				Help(1," ","OBRIGAT",,"CDA_CODLAN"+Space(30),3,0)
			EndIf
		
			If lRet .And. nPosLanc>0 .And. Empty(oLancApICMS:aCols[oLancApICMS:nAT,nPosVlr])
				lRet := .F.
				Help(1," ","OBRIGAT",,"CDA_VALOR"+Space(30),3,0)
			EndIf
		EndIf
	EndIf
EndIf

Return lRet     

//-------------------------------------
/*	Modelo de Dados
@author  	Leandro Paulino
@version 	P10 R1.4
@build		7.00.101202A
@since 		06/10/2011
@return 		oModel Objeto do Modelo*/
//-------------------------------------
Static Function ModelDef()

Local lIntGFE   := SuperGetMv('MV_INTGFE',,.F.)
Local oModel	:= Nil
Local oStruSF1  := FWFormStruct(1,"SF1")
Local oStruSF8  := FWFormStruct(1,"SF8")

Local aParRot   := {'aRotAuto1','aRotAuto2'}
Local aIDStruct := {}
Local bPost		:= Nil
Local aNewField := {}
Local aMsgRet   := {}

Private aPK_SF1   := {"F1_FILIAL", "F1_DOC", "F1_SERIE", "F1_FORNECE", "F1_LOJA" }
Private aSF1xSF8  := {{"F8_FILIAL",'xFilial("SF1")'},{"F8_NFDIFRE","F1_DOC"},{"F8_SEDIFRE","F1_SERIE"},{"F8_FORNECE","F1_FORNECE"},{"F8_LOJA","F1_LOJA"}}
Private cIdxSF8   := "F8_FILIAL+F8_NFDIFRE+F8_SEDIFRE+F8_FORNECE+F8_LOJA"

If lIntGFE
	oStruSF8:aTriggers := {}

	oStruSF1  := FWFormStruct(1,"SF1", {|cCampo| AllTrim(cCampo) $ "F1_DOC|F1_SERIE|F1_FORNECE|F1_LOJA|F1_EMISSAO|F1_BASEICM|F1_VALICM|F1_BASPIS|F1_VALPIS|F1_BASCOFI|F1_VALCOFI|F1_VALBRUT|F1_TIPO|F1_FORMUL|F1_ESPECIE|F1_ISS|" } )
	oStruSF8  := FWFormStruct(1,"SF8", {|cCampo| AllTrim(cCampo) $ "F8_NFDIFRE|F8_SEDIFRE|F8_NFORIG|F8_SERORIG|F8_FORNECE|F8_LOJA|F8_TRANSP|F8_LOJTRAN|" } )

	//Criação dos Campos Virtuais

	//--------------------CRIAÇÃO DO F1_CGCFOR----------------------------------------
	oStruSF1:AddField( ;                      	  // Ord. Tipo Desc.
		"CNPJ"                           , ;      // [01]  C   Titulo do campo
		"CNPJ "                          , ;      // [02]  C   ToolTip do campo
		"F1_CGCFOR"                      , ;      // [03]  C   Id do Field
		'C'                              , ;      // [04]  C   Tipo do campo
		14                               , ;      // [05]  N   Tamanho do campo
		0                                , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		FwBuildFeature( STRUCT_FEATURE_INIPAD,'Posicione("SA2",1,xFilial("SA2")+SF1->F1_FORNECE+SF1->F1_LOJA,"A2_CGC")' ), ; // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual
		
	//--------------------CRIAÇÃO DO F1_MSGRET----------------------------------------

	oStruSF1:AddField( ;                      // Ord. Tipo Desc.
		"Msg Retorno"                    , ;      // [01]  C   Titulo do campo
		"Msg Retorno"                    , ;      // [02]  C   ToolTip do campo
		"F1_MSGRET"                      , ;      // [03]  C   Id do Field
		'C'                              , ;      // [04]  C   Tipo do campo
		250                              , ;      // [05]  N   Tamanho do campo
		0                                , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		{||'Processado'}                 , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual

	//--------------------CRIAÇÃO DO F1_OPER------------------------------------------
	oStruSF1:AddField( ;                      	  // Ord. Tipo Desc.
		"Tp Operacao"                    , ;      // [01]  C   Titulo do campo
		"Tp Operacao"                    , ;      // [02]  C   ToolTip do campo
		"F1_OPER"	                     , ;      // [03]  C   Id do Field
		'C'                              , ;      // [04]  C   Tipo do campo
		TamSx3("D1_OPER")[1]	         , ;      // [05]  N   Tamanho do campo
		0                                , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		NIL                              , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual

	//--------------------CRIAÇÃO DO F1_TES----------------------------------------
	oStruSF1:AddField( ;                      // Ord. Tipo Desc.
		"TES"         	        		 , ;      // [01]  C   Titulo do campo
		"TES"           		         , ;      // [02]  C   ToolTip do campo
		"F1_TES"	                     , ;      // [03]  C   Id do Field
		'C'                              , ;      // [04]  C   Tipo do campo
		TamSx3("D1_TES")[1]	         	 , ;      // [05]  N   Tamanho do campo
		0                                , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		NIL                              , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual
	
	//--------------------CRIAÇÃO DO F1_PICMS----------------------------------------
	oStruSF1:AddField( ;                      // Ord. Tipo Desc.
		"Perc.ICMS"                 	 , ;      // [01]  C   Titulo do campo
		"Perc.ICMS"            		     , ;      // [02]  C   ToolTip do campo
		"F1_PICM"	                     , ;      // [03]  C   Id do Field
		'N'                              , ;      // [04]  C   Tipo do campo
		TamSx3("D1_PICM")[1]          , ;      // [05]  N   Tamanho do campo
		TamSx3("D1_PICM")[2]           , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		NIL                              , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual

	//--------------------CRIAÇÃO DO F1_BASEISS----------------------------------------
	oStruSF1:AddField( ;                      // Ord. Tipo Desc.
		"Base ISS"                 		 , ;      // [01]  C   Titulo do campo
		"Base ISS"            		     , ;      // [02]  C   ToolTip do campo
		"F1_BASEISS"	                 , ;      // [03]  C   Id do Field
		'N'                              , ;      // [04]  C   Tipo do campo
		TamSx3("D1_BASEISS")[1]          , ;      // [05]  N   Tamanho do campo
		TamSx3("D1_BASEISS")[2]          , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		NIL                              , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual

	//--------------------CRIAÇÃO DO F1_ALIQISS----------------------------------------
	oStruSF1:AddField( ;                      // Ord. Tipo Desc.
		"Aliq.ISS"	                 	 , ;      // [01]  C   Titulo do campo
		"Aliq.ISS"            		     , ;      // [02]  C   ToolTip do campo
		"F1_ALIQISS"                     , ;      // [03]  C   Id do Field
		'N'                              , ;      // [04]  C   Tipo do campo
		TamSx3("D1_ALIQISS")[1]          , ;      // [05]  N   Tamanho do campo
		TamSx3("D1_ALIQISS")[2]          , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		NIL                              , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual

	//--------------------CRIAÇÃO DO F1_ALQCOF----------------------------------------
	oStruSF1:AddField( ;                      // Ord. Tipo Desc.
		"Aliq.COFINS"                 	 , ;      // [01]  C   Titulo do campo
		"Aliq.COFINS"          		     , ;      // [02]  C   ToolTip do campo
		"F1_ALQCOF"                      , ;      // [03]  C   Id do Field
		'N'                              , ;      // [04]  C   Tipo do campo
		TamSx3("D1_ALQCOF")[1]          , ;      // [05]  N   Tamanho do campo
		TamSx3("D1_ALQCOF")[2]          , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		NIL                              , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual

	//--------------------CRIAÇÃO DO F1_ALQPIS----------------------------------------
	oStruSF1:AddField( ;                      // Ord. Tipo Desc.
		"Aliq.PIS"          	       	 , ;      // [01]  C   Titulo do campo
		"Aliq.PIS"          		     , ;      // [02]  C   ToolTip do campo
		"F1_ALQPIS"                      , ;      // [03]  C   Id do Field
		'N'                              , ;      // [04]  C   Tipo do campo
		TamSx3("D1_ALQPIS")[1]	         , ;      // [05]  N   Tamanho do campo
		TamSx3("D1_ALQPIS")[2]                                , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		NIL                              , ;      // [11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual

	//--------------------CRIAÇÃO DO F8_TPNFORI----------------------------------------
	oStruSF8:AddField( ; 						// Ord. Tipo Desc.
		"Tp NF Orig"          	       	 , ;      	// [01]  C   Titulo do campo
		"Tp NF Orig" 					 , ; 		// [02] C ToolTip do campo
		"F8_TPNFORI" 					 , ; 		// [03] C Id do Field
		'C' 							 , ;		// [04] C Tipo do campo
		01 								 , ; 		// [05] N Tamanho do campo
		0 								 , ; 		// [06] N Decimal do campo
		NIL 							 , ; 		// [07] B Code-block de validação do campo
		NIL 							 , ; 		// [08] B Code-block de validação When do campo
		NIL 							 , ; 		// [09] A Lista de valores permitido do campo
		NIL 							 , ; 		// [10] L Indica se o campo tem preenchimento obrigatório
		NIL 							 , ; 		// [11] B Code-block de inicializacao do campo
		NIL 							 , ; 		// [12] L Indica se trata-se de um campo chave
		NIL 							 , ; 		// [13] L Indica se o campo pode receber valor em uma operação de update.
		.T. ) 										// [14] L Indica se o campo é virtual

	// ------------- CRIAÇÃO DO F8_CGCFOR ------------------
	oStruSF8:AddField( ;                      // Ord. Tipo Desc.
		"CNPJ"                           , ;      // [01]  C   Titulo do campo
		"CNPJ"                          , ;      // [02]  C   ToolTip do campo
		"F8_CGCFOR"                      , ;      // [03]  C   Id do Field
		'C'                              , ;      // [04]  C   Tipo do campo
		14                               , ;      // [05]  N   Tamanho do campo
		0                                , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		FwBuildFeature( STRUCT_FEATURE_INIPAD,'Posicione("SA2",1,xFilial("SA2")+SF8->(F8_FORNECE+F8_LOJA),"A2_CGC")'), ; //[11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual


	// ------------- CRIAÇÃO DO F8_CGCTRA ------------------
	oStruSF8:AddField( ;                      // Ord. Tipo Desc.
		"CNPJ"                           , ;      // [01]  C   Titulo do campo
		"CNPJ"                          , ;      // [02]  C   ToolTip do campo
		"F8_CGCTRA"                      , ;      // [03]  C   Id do Field
		'C'                              , ;      // [04]  C   Tipo do campo
		14                               , ;      // [05]  N   Tamanho do campo
		0                                , ;      // [06]  N   Decimal do campo
		NIL                              , ;      // [07]  B   Code-block de validação do campo
		NIL                              , ;      // [08]  B   Code-block de validação When do campo
		NIL                              , ;      // [09]  A   Lista de valores permitido do campo
		NIL                              , ;      // [10]  L   Indica se o campo tem preenchimento obrigatório
		FwBuildFeature( STRUCT_FEATURE_INIPAD,'Posicione("SA2",1,xFilial("SA2")+SF8->(F8_TRANSP+F8_LOJTRAN),"A2_CGC")'), ; //[11]  B   Code-block de inicializacao do campo
		NIL                              , ;      // [12]  L   Indica se trata-se de um campo chave
		NIL                              , ;      // [13]  L   Indica se o campo pode receber valor em uma operação de update.
		.T.                              )        // [14]  L   Indica se o campo é virtual


	//--------------------GATILHO NO F1_TES-------------------------------------------
	aAux := FwStruTrigger(;
		"F1_OPER", ;                                                  // [01] Id do campo de origem
		"F1_TES" , ;                                                  // [02] Id do campo de destino
		'Posicione("SFM",1,xFilial("SFM")+M->F1_OPER,"FM_TE")')

	oStruSF1:AddTrigger( ;
		aAux[1], ;                                                      // [01] Id do campo de origem
		aAux[2], ;                                                      // [02] Id do campo de destino
		aAux[3], ;                                                      // [03] Bloco de codigo de validação da execução do gatilho
		aAux[4] )                                                       // [04] Bloco de codigo de execução do gatilho

	
	//------------- Gatilhos para Campos Existentes no X3 e não carregados no XML ------------------  				
	//--------------------GATILHO NO F8_CGCTRA------------------------------------------------------
	aAux := FwStruTrigger(;
		"F8_CGCTRA", ;                                                  // [01] Id do campo de origem
		"F8_TRANSP", ;                                                  // [02] Id do campo de destino
		'Posicione("SA2",3,xFilial("SA2")+FwFldGet("F8_CGCTRA"),"A2_COD")')

	oStruSF8:AddTrigger( ;
		aAux[1], ;                                                      // [01] Id do campo de origem
		aAux[2], ;                                                      // [02] Id do campo de destino
		aAux[3], ;                                                      // [03] Bloco de codigo de validação da execução do gatilho
		aAux[4] )                                                       // [04] Bloco de codigo de execução do gatilho

	//--GATILHO F8_LOJTRAN
	aAux := FwStruTrigger(;
		"F8_CGCTRA", ;                                                     // [01] Id do campo de origem
		"F8_LOJTRAN" , ;                                                   // [02] Id do campo de destino
		'Posicione("SA2",3,xFilial("SA2")+FwFldGet("F8_CGCTRA"),"A2_LOJA")')

	oStruSF8:AddTrigger( ;
		aAux[1], ;                                                      // [01] Id do campo de origem
		aAux[2], ;                                                      // [02] Id do campo de destino
		aAux[3], ;                                                      // [03] Bloco de codigo de validação da execução do gatilho
		aAux[4] )                                                       // [04] Bloco de codigo de execução do gatilho

	//--------------------GATILHO NO F8_CGCFOR-------------------------------------------
	//--GATILHO F8_FORNECE
	aAux := FwStruTrigger(;
		"F8_CGCFOR", ;                                                     // [01] Id do campo de origem
		"F8_FORNECE" , ;                                                   // [02] Id do campo de destino
		'Posicione("SA2",3,xFilial("SA2")+FwFldGet("F8_CGCFOR"),"A2_COD")')
	
	oStruSF8:AddTrigger( ;
		aAux[1], ;                                                      // [01] Id do campo de origem
		aAux[2], ;                                                      // [02] Id do campo de destino
		aAux[3], ;                                                      // [03] Bloco de codigo de validação da execução do gatilho
		aAux[4] )                                                       // [04] Bloco de codigo de execução do gatilho

	//--GATILHO F8_LOJA
	aAux := FwStruTrigger(;
		"F8_CGCFOR", ;                                                  // [01] Id do campo de origem
		"F8_LOJA" , ;                                                   // [02] Id do campo de destino
		'Posicione("SA2",3,xFilial("SA2")+FwFldGet("F8_CGCFOR"),"A2_LOJA")')

	oStruSF8:AddTrigger( ;
		aAux[1], ;                                                      // [01] Id do campo de origem
		aAux[2], ;                                                      // [02] Id do campo de destino
		aAux[3], ;                                                      // [03] Bloco de codigo de validação da execução do gatilho
		aAux[4] )                                                       // [04] Bloco de codigo de execução do gatilho

	aAdd(aIDStruct, "MATA116_SF1")
	aAdd(aIDStruct, "MATA116_SF8")

	aAdd(aMsgRet, {"MATA116_SF1","F1_MSGRET"})
	//Tirar Validação dos campos com SetProperty
	oStruSF1:SetProperty( '*', MODEL_FIELD_OBRIGAT,  .F. )
	oStruSF1:SetProperty( '*', MODEL_FIELD_VALID, FWBuildFeature( STRUCT_FEATURE_VALID, '.T.' ) )
	oStruSF1:SetProperty( '*', MODEL_FIELD_WHEN,  NIL )	

	oStruSF8:SetProperty( '*', MODEL_FIELD_OBRIGAT,  .F. )
	oStruSF8:SetProperty( '*', MODEL_FIELD_VALID, FWBuildFeature( STRUCT_FEATURE_VALID, '.T.' ) )
	oStruSF8:SetProperty( '*', MODEL_FIELD_WHEN,  NIL )
	
	If lLGPD
		oStruSF1:SetProperty( "F1_CGCFOR" , MVC_VIEW_OBFUSCATED , OfuscaLGPD(,"A2_CGC") )
		oStruSF8:SetProperty( "F8_CGCFOR" , MVC_VIEW_OBFUSCATED , OfuscaLGPD(,"A2_CGC") )
		oStruSF8:SetProperty( "F8_CGCTRA" , MVC_VIEW_OBFUSCATED , OfuscaLGPD(,"A2_CGC") )
	Endif

	bPost   := {|oModel,b,c,d,e,f| A116RecEAI(oModel,"MATA116",aIDStruct,aParRot,aNewField,aMsgRet) }

	oModel:= MPFormModel():New("MATA116",  /*bPre*/, bPost /*bPost*/, {|| } /*bCommit*/, /*bCancel*/)
   	oModel:bPost := bPost	
	oModel:AddFields("MATA116_SF1", ,oStruSF1,/*bPre*/,/*bPost*/,/*bLoad*/)
	oModel:SetPrimaryKey(aPK_SF1)

	oModel:AddGrid("MATA116_SF8","MATA116_SF1",oStruSF8,/*bLinePre*/, ,/*bPre*/,/*bPost*/,/*bLoad*/)
	oModel:SetRelation("MATA116_SF8",aSF1xSF8,cIdxSF8)

	oModel:GetModel("MATA116_SF8"):SetDelAllLine(.T.)
	oModel:SetDescription( OemToAnsi(STR0001) )	
EndIf

Return oModel

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³A116RECEAI   ºAutor  ³Leandro Paulino	 º Data ³  19/10/11   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Recebimento do Documento de Frete na Integração com        º±±
±±º          ³ TOTVS GFE                                                  º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Integração OMS x GFE		                                  º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

Function A116RECEAI (oModel, cMainModel, aIDStruct, aParRot, aNewField, aMsgRet)

Local aCab 		:= {}
Local aItens 	:= {}
Local nA			:= 0
Local nB			:= 0
Local nPos		:= 0
Local xValue 	:= Nil
Local oModItem := Nil
Local aErroAuto:= {}
Local cLogErro := ""
Local nI			:= 0
Local cFornNF	:= ""
Local cLojaNF	:= ""
Local cXml     := ""

Private lMsErroAuto    := .F.
Private lAutoErrNoFile := .T.

Default aParRot 		:= {}
Default aNewField 	:= {}
Default aMsgRet		:= {}

Private nOpcx	:= oModel:GetOperation() 

aadd(aCab,{"",dDataBase-90})       	//Data Inicial
aadd(aCab,{"",dDataBase})          	//Data Final
aadd(aCab,{"",IIf(nOpcx == 5,1,2)}) //2-Inclusao;1=Exclusao
aadd(aCab,{"",""})			      	//Fornecedor do documento de Origem
aadd(aCab,{"",""})               	//Loja de origem
aadd(aCab,{"",1})                 	//Tipo da nota de origem: 1=Normal;2=Devol/Benef
aadd(aCab,{"",2})                  	//1=Aglutina;2=Nao aglutina
aadd(aCab,{"F1_EST",""})         	//Estado do Fornecedor Origem
aadd(aCab,{"F1_VALBRUT",0.00})      //Valor do conhecimento
aadd(aCab,{"F1_FORMUL",2})          //Formula
aadd(aCab,{"F1_DOC",""})            //F1_DOC - Numero do CTR
aadd(aCab,{"F1_SERIE",""})          //F1_SERIE - Serie do CTR
aadd(aCab,{"F1_FORNECE",""})        //F1_FORNECEOR - Transportador - Fornecedor CTR
aadd(aCab,{"F1_LOJA",""})           //F1_LOJA 		- Transportador - LOJA       CTR
aadd(aCab,{"F1_TES",""})            //TES
aadd(aCab,{"F1_BRICMS",0.00})    	//BASE ICMS
aadd(aCab,{"F1_ICMSRET",0.00})		//ICMS Ret
aadd(aCab,{"F1_COND",""})	      	//Condição de pagamento


For nA := 1 To Len (aIDStruct) //(oModelStru_SF1)

	cClasse:= oModel:GetModel(aIDStruct[nA]):ClassName()

	If cClasse == 'FWFORMFIELDS'

		aFields:= oModel:GetModel(aIDStruct[nA]):GetStruct():aFields
		For nB := 1 To Len (aFields)
			cIDField := aFields[nB][MODEL_FIELD_IDFIELD]
			xValue   := oModel:GetValue(aIDStruct[nA],cIDField )
			If (npos := Ascan(aCab,{|x| x[1] = cIDField}) ) > 0
				aCab[nPos,2] := IIf (cIDField<>"F1_FORMUL",xValue,Val(xValue))
			EndIf
		Next nB

	ElseIf cClasse == 'FWFORMGRID'

		oModItem := oModel:GetModel(aIDStruct[nA])

		For nB := 1 To oModItem:Length()
			aadd( aItens,{{"PRIMARYKEY",''}} )
			oModItem:GoLine(nB)
			If oModItem:GetValue("F8_TPNFORI") == "D"
				cFornNF := Posicione("SA1",3,xFilial("SA1")+oModItem:GetValue("F8_CGCFOR"),"A1_COD")
				cLojaNF := SA1->A1_LOJA
			Else
				cFornNF := Posicione("SA2",3,xFilial("SA2")+oModItem:GetValue("F8_CGCFOR"),"A2_COD")
				cLojaNF := SA2->A2_LOJA
			EndIf
			If !Empty(cFornNF) .And. !Empty(cLojaNF)
				aItens[nB,1,2] := 	AllTrim(oModItem:GetValue("F8_NFORIG")+;
					oModItem:GetValue("F8_SERORIG")+;
					cFornNF+;
					cLojaNF)
			EndIf
		Next nB

	EndIf

Next nA

MSExecAuto({|x,y| Mata116(x,y)},aCab,aItens)

If lMsErroAuto
	aErroAuto := GetAutoGRLog()
	For nI := 1 To Len(aErroAuto)
		cLogErro += NoAcentoCte(aErroAuto[nI])
	Next nI 
	//-- Forca Help para o Model retornar mensagem de erro para o EAI
	/*@param cIdForm Id do formulário em validação
	@param cIdField Id do campo do formulário em validação
	@param cIdFormErr Id do formulário em que ocorreu o erro
	@param cIdFieldErr Id do campo do formulário em que ocorreu o erro
	@param cId Id da mensagem de help
	@param cMessage Mensagem de erro
	@param cSoluction Mensagem de solução
	@param xValue Valor especificado do campo
	@param xOldValue Valor anterior do campo
	*/ 
	oModel:SetErrorMessage (,,,,,cLogErro)

EndIf

If Len(aMsgRet) > 0
	cXml := oModel:GetXmlData()
	If lMsErroAuto
		For nI:= 1 To Len(aMsgRet)
			cXml:= STRTRAN ( cXml , "<value>Processado</value></"+aMsgRet[nI,2]+">" , "<value>"+SubStr(cLogErro,1,120)+"</value></"+aMsgRet[nI,2]+">"  )
		Next nI
	EndIf
	StartJob("MaEnvEAI",GetEnvServer(),.T.,cEmpAnt,cFilAnt,3,cMainModel,,,,,,cXml)
EndIf

Return !lMsErroAuto

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³A116CpXml ºAutor  ³Leandro Paulino   	 º Data ³  07/12/11   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Complementa o Xml recebido pelo EAI para preenchimento das º±±
±±º          ³ chaves primaria do protheus								  º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Integracao OMS x GFE                                       º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Function A116CpXml(  )

Local cRet    		:= PARAMIXB[1]
Local aArea			:= GetArea()
Local oXml	 		:= Nil
Local lRet        	:= .F.
Local cCGCForSF1	:= ""
Local cCGCForSF8	:= ""
Local cCgcTraSF8	:= ""
Local nTotReg 		:= 0
Local nRegAtu 		:= 1	
Local lIntGFE   	:= SuperGetMv('MV_INTGFE',,.F.)

If lIntGFE

	oXml := tXmlManager():New()

	lRet := oXml:Parse(cRet)

	If lRet
		lRet := oXml:XPathHasNode("//MATA116/MATA116_SF1/F1_CGCFOR/value") // Verifica se a TAG existe
		If lRet
			cCgcForSF1 := AllTrim( oXml:XPathGetNodeValue("//MATA116/MATA116_SF1/F1_CGCFOR", "value") ) //Guarda o Conteudo da TAG
			SA2->(DbSetOrder(3))
			If SA2->(MsSeek(xFilial("SA2") + cCgcForSF1)) 
				While SA2->( !Eof() ) .And. AllTrim( SA2->A2_CGC ) == cCgcForSF1
					If SA2->A2_MSBLQL <>  '1'
						If oXml:XPathAddNode("//MATA116/MATA116_SF1","F1_FORNECE", '') //Adiciona a TAG
							If oXml:XPathAddAtt("//MATA116/MATA116_SF1/F1_FORNECE","order","22")
								If oXml:XPathAddNode("//MATA116/MATA116_SF1","F1_LOJA"   , '')
									If oXml:XPathAddAtt("//MATA116/MATA116_SF1/F1_LOJA","order","23")
										If oXml:XPathAddNode("//MATA116/MATA116_SF1/F1_FORNECE","value", SA2->A2_COD) 	//Adiciona o conteudo na TAG CRIADA
											If oXml:XPathAddNode("//MATA116/MATA116_SF1/F1_LOJA","value", SA2->A2_LOJA)//Adiciona o conteudo na TAG CRIADA
												//Complementa XML com informações dos documentos originais
												If oXml:XPathHasNode("//MATA116/MATA116_SF1/MATA116_SF8/F8_CGCFOR/value") 		// Verifica se a TAG existe
													cCgcForSF8:= AllTrim( oXml:XPathGetNodeValue("//MATA116/MATA116_SF1/MATA116_SF8/F8_CGCFOR/value") )
													If oXml:XPathHasNode("//MATA116/MATA116_SF1/MATA116_SF8/F8_CGCTRA/value") // Verifica se a TAG existe
														cCgcTraSF8:= AllTrim( oXml:XPathGetNodeValue("//MATA116/MATA116_SF1/MATA116_SF8/F8_CGCTRA/value") )
													EndIf
												EndIf
												If !Empty(cCgcTraSF8) .And. !Empty(cCgcForSF8)
													If oXml:xPathHasNode("//MATA116/MATA116_SF1/MATA116_SF8/items")					// Verifica se a TAG existe
														nTotReg := oXml:XPathChildCount("//MATA116/MATA116_SF1/MATA116_SF8/items") //Retorna Quantidade de Itens do Array
														nRegAtu := 1
														While nRegAtu <= nTotReg
															If SA2->(MsSeek(xFilial("SA2") + cCgcForSF8))
																While SA2->( !Eof() ) .And. AllTrim( SA2->A2_CGC )  == cCgcForSF8
																	If SA2->A2_MSBLQL <>  '1'
																		If oXml:XPathAddNode("//MATA116/MATA116_SF1/MATA116_SF8/items/item["+(AllTrim(Str(nRegAtu)))+"]","F8_FORNECE"	,SA2->A2_COD)
																			oXml:XPathAddNode("//MATA116/MATA116_SF1/MATA116_SF8/items/item["+(AllTrim(Str(nRegAtu)))+"]","F8_LOJA"		,SA2->A2_LOJA)
																		EndIf
																		Exit
																	EndIf
																	SA2->( dbSkip() )
																EndDo																
																If SA2->(MsSeek(xFilial("SA2") + cCgcTraSF8))
																	While SA2->( !Eof() ) .And. AllTrim( SA2->A2_CGC ) == cCgcTraSF8
																		If SA2->A2_MSBLQL <>  '1'
																			oXml:XPathAddNode("//MATA116/MATA116_SF1/MATA116_SF8/items/item["+(AllTrim(Str(nRegAtu)))+"]","F8_TRANSP"	,SA2->A2_COD)
																			oXml:XPathAddNode("//MATA116/MATA116_SF1/MATA116_SF8/items/item["+(AllTrim(Str(nRegAtu)))+"]","F8_LOJTRAN"	,SA2->A2_LOJA)
																			Exit
																		EndIf	
																		SA2->( dbSkip() )
																	EndDo																
																EndIf
															EndIf
															nRegAtu++
														EndDo
													EndIf
												EndIf
												cRet := oXml:Save2String()
											EndIf
										EndIf
									EndIf
								EndIf
							EndIf
						EndIf
						Exit
					EndIf
					SA2->( dbSkip() )
				EndDo					
			EndIf
		EndIf
	EndIf
EndIf

RestArea(aArea)
Return cRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³a116Mark  ³ Autor ³ Aline S Damasceno     ³ Data ³26/01/2012³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Funcao para validar as NF marcadas						  ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Function a116Mark(cOpc)     
Local lM116MARK := ExistBlock('M116MARK') 
Local aArea     := GetArea()
Local cMark		:= ThisMark()
Local nPos 		:= aScan(aRecMark,{|x| x == SF1->(Recno())}) 

Default cOpc 	:= "I"

If lM116MARK
	ExecBlock('M116MARK', .F., .F.)
Else
	If cOpc == "I" //Item
		RecLock("SF1",.F.) 
		If IsMark('F1_OK',cMark)
			SF1->F1_OK :=Space(2)
			If nPos > 0 
				ADEL( aRecMark, nPos )
				ASIZE( aRecMark, Len(aRecMark)-1 )
			Endif
		Else
			SF1->F1_OK :=cMark 
			If nPos== 0
				AAdd( aRecMark, SF1->(Recno()) )
			EndIf
		EndIf
		MsUnLock()
	Elseif cOpc == "A" //All
		SF1->(DbGotop())
		While SF1->(!EOF())
			nPos := aScan(aRecMark,{|x| x == SF1->(Recno())}) 

			If Reclock("SF1",.F.)
				If IsMark('F1_OK',cMark)
					SF1->F1_OK := Space(2)
					If nPos > 0 
						ADEL( aRecMark, nPos )
						ASIZE( aRecMark, Len(aRecMark)-1 )
					Endif
				Else
					SF1->F1_OK :=cMark 
					If nPos== 0
						AAdd( aRecMark, SF1->(Recno()) )
					EndIf
				EndIf
				SF1->(MsUnlock())
			Endif
			SF1->(dbSkip())
		EndDo
	Endif
	MarkBRefresh()
EndIf 

If cOpc == "A"
	SF1->(DbGotop())
Endif

RestArea(aArea)

Return 

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A116IGrava³ Autor ³ Rodrigo Toledo Silva  ³ Data ³25.05.2012	³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Faz a inclusao de registros na tabela SDT apos o calculo   	³±±
±±³ 		 ³ do valor de rateio do conhecimento de transporte.		  	³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpA1 -> Array com os elementos dos itens da nf de entrada  	³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA116I - Importacao de arquivos XML Ct-e (TOTVS Colaboracao)³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function A116IGrava(aNFItens, aChvSdt,nPosPicm)

Local aArea	   	:= SDT->(GetArea())
Local nX 	  	:= 0
Local nPos		:= 0
Local cChave	:= ""
Local lUnidMed	:= SDT->(FieldPos("DT_UM")) > 0 .And. SDT->(FieldPos("DT_SEGUM")) > 0 .And. SDT->(FieldPos("DT_QTSEGUM")) > 0
Local lDTNFORI	:= SDT->(FieldPos("DT_NFORI")) > 0 .And. SDT->(FieldPos("DT_SERIORI")) > 0 .And. SDT->(FieldPos("DT_ITEMORI")) > 0
Local lDTPICM	:= SDT->(FieldPos("DT_PICM")) > 0
Local lDTCHVNFO	:= SDT->(FieldPos('DT_CHVNFO')) > 0
Local nPD1ITEM	:= GDFieldPos("D1_ITEM")
Local nPD1COD	:= GDFieldPos("D1_COD")
Local nPD1VUNIT	:= GDFieldPos("D1_VUNIT")
Local nPD1TOTAL	:= GDFieldPos("D1_TOTAL")
Local nPD1Loc	:= GDFieldPos("D1_LOCAL")
Local nPD1NfOri	:= GDFieldPos("D1_NFORI")
Local nPD1SerOr	:= GDFieldPos("D1_SERIORI")
Local nPD1ItOri	:= GDFieldPos("D1_ITEMORI")

SA5->(dbSetOrder(1))
SDT->(dbSetOrder(2))

For nX := 1 To Len(aNFItens) 
	
	RecLock("SDT",.T.)
		
		SDT->DT_FILIAL	:= xFilial("SDT")								// Filial
	 	SDT->DT_ITEM	:= aNFItens[nX,nPD1ITEM]						// Item
		SDT->DT_COD		:= aNFItens[nX,nPD1COD]							// Codigo do produto
	 	SDT->DT_FORNEC	:= SDS->DS_FORNEC								// Fornecedor do conhecimento de frete
	 	SDT->DT_LOJA	:= SDS->DS_LOJA									// Loja do fornecedor do conhecimento
	 	SDT->DT_DOC		:= SDS->DS_DOC	 								// Numero do conhecimento de frete
	 	SDT->DT_SERIE	:= SDS->DS_SERIE								// Serie do conhecimento de frete
	 	SDT->DT_CNPJ	:= SDS->DS_CNPJ									// CNPJ/CPF do fornecedor do conhecimento
	 	SDT->DT_VUNIT	:= aNFItens[nX,nPD1VUNIT]	 					// Valor unitario
	 	SDT->DT_TOTAL	:= aNFItens[nX,nPD1TOTAL]						// Valor total
	 	
	 	If lDTNFORI
		 	SDT->DT_NFORI	:= aNFItens[nX,nPD1NfOri]	 	// Nota fiscal original
		 	SDT->DT_SERIORI	:= aNFItens[nX,nPD1SerOr] 	// Serie da nota fiscal original
		 	SDT->DT_ITEMORI	:= aNFItens[nX,nPD1ItOri] 	// Item da nota fiscal original
		EndIf
		
		If lDTPICM .And. Len(aAutoCab) >= 22 .And. AScan(aAutoCab, {|c| AllTrim(c[1]) == 'DT_PICM' }) > 0 .and. nPosPicm > 0
			SDT->DT_PICM 	:= aAutoCab[nPosPicm,2]
			SDT->DT_XALQICM := aAutoCab[nPosPicm,2]
			SDT->DT_XMLICM	:= (aNFItens[nX,nPD1TOTAL]*aAutoCab[nPosPicm,2])/100
		EndIf
		
		//Local
		SDT->DT_LOCAL := aNFItens[nX,nPD1Loc] 	// Local da nota fiscal original
		
		If lDTCHVNFO // Caso exista na base do cliente, grava informacao no campo.
			If !Empty(SDT->DT_NFORI) // Caso tenha nota original amarrada ao CT-e.
				cChave := SDT->DT_NFORI+SDT->DT_SERIORI
			
				nPos := aScan(aChvSdt,{|x| cChave $ x[1,2]})
				If nPos > 0				
					SF1->(DbSetOrder(1)) // Indice 1 - F1_FILIAL+F1_DOC+F1_SERIE+F1_FORNECE+F1_LOJA+F1_TIPO
					If SF1->(DbSeek(xFilial('SF1')+aChvSdt[nPos][1][2]))
						SDT->DT_CHVNFO := SF1->F1_CHVNFE
					EndIf
				EndIf
			EndIf
		EndIf
		
		If lUnidMed
			SDT->DT_UM		:= GetAdvFVal("SB1","B1_UM",xFilial("SB1")+aNFItens[nX,nPD1COD],1)
			SDT->DT_SEGUM	:= GetAdvFVal("SB1","B1_SEGUM",xFilial("SB1")+aNFItens[nX,nPD1COD],1)
			SDT->DT_QTSEGUM := 0
		Endif
	SDT->(MsUnlock())
Next nX

SDT->(RestArea(aArea))
Return

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³FillCTBEntºAutor  ³ Anieli Rodrigues	 º Data ³ 15/05/13    º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Inicaliza campos das entidades contabeis de acordo com a   º±±
±±º          ³ origem.                                                    º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ MATA116                                                    º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function FillCTBEnt(cOrigem,nItem)
Local aCTBEnt := CTBEntArr()
Local nX	  := 0

For nX := 1 To Len(aCTBEnt)
	If GDFieldPos("D1_EC"+aCTBEnt[nX]+"CR",aHeader) > 0
		aCols[nItem,GDFieldPos("D1_EC"+aCTBEnt[nX]+"CR")] := (cOrigem)->&("D1_EC"+aCTBEnt[nX]+"CR")
	EndIf
	If GDFieldPos("D1_EC"+aCTBEnt[nX]+"DB",aHeader) > 0
		aCols[nItem,GDFieldPos("D1_EC"+aCTBEnt[nX]+"DB")] := (cOrigem)->&("D1_EC"+aCTBEnt[nX]+"DB")
	EndIf
Next nX

Return

/*ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³MenuDef   ³ Autor ³ Materiais       ³ Data ³01/11/2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Utilizacao de menu Funcional                         ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß*/

Static Function MenuDef()

Private aRotina := {}

If !(Type("nRotina") == "U") 
	If nRotina == 1
		aadd(aRotina,{OemtoAnsi(STR0004),"A116Inclui",0,5}) //"Excluir"
		lInclui := .F.
	Else
		aadd(aRotina,{OemtoAnsi(STR0005),"A116Inclui",0,6}) //"Gera Conhec."
	End
Else
	// Inclusao das opcoes para que seja possivel conceder as permissoes a usuarios
	// para geracao e exclusao de conhecimento de frete via Configurador 
	aAdd(aRotina,{OemtoAnsi(STR0004),"A116Inclui",0,5}) //"Excluir"
	aAdd(aRotina,{OemtoAnsi(STR0005),"A116Inclui",0,6}) //"Gera Conhec."
EndIf

aAdd(aRotina,{(STR0003),"A103NFiscal",0,6}) //"Visualizar"

If ExistBlock( "MT116BUT" )
	If ValType( aUsButtons := ExecBlock( "MT116BUT", .F., .F.)) == "A"
		AEval( aUsButtons, { |x| AAdd( aRotina, x ) } )
	EndIf
EndIf

Return(aRotina)

/*ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³A116VerOP ³ Autor ³ Isaias Florencio³ Data ³09.06.2014³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Verifica se Ordem de Producao esta encerrada         ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß*/

Static Function A116VerOP(cOP)
Local lRet := .F.
Local aAreas := { GetArea() , SC2->(GetArea()) }

SC2->(DbSetOrder(1)) // C2_FILIAL + NUM + ITEM + SEQUEN + ITEMGRD
If (SC2->(MsSeek(xFilial("SC2")+cOP)) .And. !Empty(SC2->C2_DATRF))
	lRet := .T.
EndIf

RestArea(aAreas[2])
RestArea(aAreas[1])

Return lRet

/*ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³A116GerSOP³ Autor ³ Isaias Florencio³ Data ³09.06.2014³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Pergunta se emite nota sem gerar movimento RE5 pra OP³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß*/

Static Function A116GerSOP(cOP, cDoc , cItem)

Local cAlerta := ""
Local lRet := .F.

// "A Ordem de Producao informada no documento original "
// "se encontra encerrada e nao e permitida a geracao "
// "do movimento de requisicao direta para producao 'RE5'. "
// "Deseja continuar com a inclusao da nota"
// "de conhecimento de frete para este item sem gerar o movimento"
// "de requisicao para ordem de producao "

cAlerta := STR0056 + AllTrim(cOP) +" ?"

If !l116Auto
	If Aviso((OemToAnsi(STR0039) + STR0057 + AllTrim(cDoc) + STR0058 + AllTrim(cItem)),cAlerta, {STR0011, STR0010},2 ) == 1 // Documento :____ Item: _____
		lRet := .T.
	EndIf
Else
	lRet := .T.
Endif	

Return lRet

Static Function ProcH(cCampo)
Return aScan(aAutoCab,{|x|Trim(x[1])== cCampo })

//-------------------------------------------------------------------
/*/{Protheus.doc} A116ITCOL()
Valida se tem itens ativos no acols para inclusão

@param    aCols116 - Array - Itens do conhecimento
@return   lRet - Logico - Retorna se continua ou não a inclusão

@author Rodrigo M Pontes
@since 04/10/18
@version 11
/*/
//-------------------------------------------------------------------

Static Function A116ITCOL(aCols116) 

Local lRet	:= .T.
Local nX	:= 0
Local nDel	:= 0

If Len(aCols116) == 0
	lRet := .F.
Else
	For nX := 1 To Len(aCols116)
		If aCols116[nX,Len(aCols116[nX])] 
			nDel++
		Endif
	Next nX
	
	If nDel == Len(aCols116)
		lRet := .F.
	Endif
Endif

Return lRet

/*/{Protheus.doc} A116ChkSig
//TODO Checa a assinatura dos fontes complementares estão corretos.

@author rodrigo m pontes
@since 04/04/2020
@version 1.0
/*/

Static Function A116ChkSig()

Local lRet := .F.

lRet := FindFunction("FCalcISS")
If !lRet
	Help(" ",1,"FINXIMP",,STR0063,1,0) // "Por favor, atualize o fonte FINXIMP para uma versão igual ou superior a 29/11/2019" 
EndIf

Return lRet

/*/
{Protheus.doc} A116CPOINTER
Valida existencia dos campos para processo de intermediador
NT2020-006

@author rodrigo.mpontes
@since 10/03/21
@version 1.0
/*/

Function A116CPOINTER() 

Local lRet := .F.

If 	SF1->(FieldPos("F1_INDPRES")) > 0 .And. SF1->(FieldPos("F1_CODA1U")) > 0
	lRet := .T.
Endif

Return lRet
