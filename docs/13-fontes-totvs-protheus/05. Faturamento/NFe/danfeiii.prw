#INCLUDE "PROTHEUS.CH" 
#INCLUDE "TBICONN.CH"
#INCLUDE "COLORS.CH"
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"

#DEFINE IMP_SPOOL 2

#DEFINE VBOX      080
#DEFINE VSPACE    008
#DEFINE HSPACE    010
#DEFINE SAYVSPACE 008
#DEFINE SAYHSPACE 008
#DEFINE HMARGEM   030
#DEFINE VMARGEM   030
#DEFINE MAXITEM   010                                                // Máximo de produtos para a primeira página
#DEFINE MAXITEMP2 022                                                // página 02 em diante com inf. complementar
#DEFINE MAXITEMP2F 042                                               // pagina 2 em diante sem informação complementar
#DEFINE MAXITEMP3 022                                                // Máximo de produtos para a pagina 2 (caso utilize a opção de impressao em verso) - Tratamento implementado para atender a legislacao que determina que a segunda pagina de ocupar 50%.
#DEFINE MAXITEMC  012                                                // Máxima de caracteres por linha de produtos/serviços
#DEFINE MAXMENLIN 088                                                // Máximo de caracteres por linha de dados adicionais
#DEFINE MAXMSG    006                                                // Máximo de dados adicionais na primeira página
#DEFINE MAXMSG2   018                                                // Máximo de dados adicionais na segunda página
#DEFINE MAXBOXH   800                                                // Tamanho maximo do box Horizontal
#DEFINE MAXBOXV   600
#DEFINE INIBOXH   -10
#DEFINE MAXMENL   080                                                // Máximo de caracteres por linha de dados adicionais
#DEFINE MAXVALORC 009                                                // Máximo de caracteres por linha de valores numéricos
#DEFINE MAXCODPRD 040                                                // Máximo de caracteres do codigo de produtos/servicos

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³PrtNfeSef ³ Autor ³ Eduardo Riera         ³ Data ³16.11.2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Rdmake de exemplo para impressão da DANFE no formato Retrato³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³Nenhum                                                      ³±±
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

User Function DANFE_P1(	cIdEnt	, cVal1		, cVal2, oDanfe,;
						oSetup	, lIsLoja	)

Local aArea     	:= GetArea() 
Local lExistNfe 	:= .F.
Local lRet			:= .T.
local lJob			:= .F.
Local lImprime		:= .T.
Local lQuebraImp 	:= .F. // Define se quebra a impressão em Lotes
Local lVerPerg		:= .T.
local cNaoImp		:= ""	//Mensagem para as Notas não impressas do Modelo "65- NFCE" pela Rotina SPEDNFE
local cNfceMens		:= ""	//Mensagem para as Notas não impressas do Modelo "65- NFCE" pela Rotina SPEDNFE
Local cTabela		:= ""
Local cCampos		:= ""
Local cAliasChk		:= ""
Local nQtdDocs		:= 0
Local nLimitImp		:= 500 // Define o limite de DANFES a serem impressos em um lote
Local nQtdTotal		:= 0
Local lContinua		:= .T.

Default lIsLoja	:= .F.	// indica se foi chamado de alguma rotina do SIGALOJA

Private nConsNeg := 0.4 // Constante para concertar o cálculo retornado pelo GetTextWidth para fontes em negrito.
Private nConsTex := 0.38 // Constante para concertar o cálculo retornado pelo GetTextWidth.
private oRetNF

lJob := (oDanfe:lInJob .or. oSetup == nil)

Public  nMaxItem :=  MAXITEM

DefineResolution(oDanfe, oSetup, lJob)

If lIsLoja
	//Se SIGALOJA, define as perguntas que sao feitas no Pergunte NFSIGW
	MV_PAR01 := SF2->F2_DOC 
	MV_PAR02 := SF2->F2_DOC
	MV_PAR03 := SF2->F2_SERIE
	MV_PAR04 := 2	//[Operacao] NF de Saida: 2
	MV_PAR05 := 1	//Frente e Verso - 1:Sim
	MV_PAR06 := 2	//DANFE simplificado - 2:Nao
Else
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ 
	//³                        Agroindustria                          ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If FindFunction("OGXUtlOrig") //Encontra a função
		If OGXUtlOrig() // Retorna se tem integração com Agro/originação modulo 67
			If FindFunction("AGRXPERG")
				lVerPerg := AGRXPERG()
			EndIf
		EndIf
	Endif
	
	If lVerPerg
		if !oDanfe:lInJob
			lContinua := Pergunte("NFSIGW",.T.)  .AND. ( (!Empty(MV_PAR06) .AND. MV_PAR06 == 2) .OR. Empty(MV_PAR06) )
		else
			Pergunte("NFSIGW",.F.)
			lContinua := ( (!Empty(MV_PAR06) .AND. MV_PAR06 == 2) .OR. Empty(MV_PAR06) )
		endif
	EndIf
EndIf

If ( !Empty( MV_PAR06 ) .and. MV_PAR06 == 1 )
	if !oDanfe:lInJob
		Aviso("DANFE","Impressão de DANFE Simplificada, disponível somente em formato retrato.",{"OK"},3)
	endif
Else
	If lContinua
		if MV_PAR04==1
				cTabela	:= 'SF1'
				cCampos := 'COUNT(*) AS TOTAL, MAX(SF1.F1_DOC) AS MAIOR, MIN(SF1.F1_DOC) AS MENOR'

			elseif MV_PAR04==2
				cTabela	:= 'SF2'
				cCampos := 'COUNT(*) AS TOTAL, MAX(SF2.F2_DOC) AS MAIOR, MIN(SF2.F2_DOC) AS MENOR'

			endif

			cAliasChk := setQuery(cTabela, cCampos, .F.)
			(cAliasChk)->(DBGoTop())
			nQtdTotal	:= (cAliasChk)->TOTAL
			MV_PAR01 	:= (cAliasChk)->MENOR
			MV_PAR02 	:= (cAliasChk)->MAIOR
			nQtdDocs 	:=Val(Alltrim(MV_PAR02)) - Val(Alltrim(MV_PAR01))
			(cAliasChk)->(DbCloseArea())

		if lJob	
			if nQtdTotal > nLimitImp .and. lImprime		
				DivLtDanfeImp(oDanfe, nQtdDocs, nLimitImp, cIDEnt, lIsLoja, lJob, oSetup, @lExistNFe, @cNfceMens)
				lQuebraImp := .T.
			else
				DANFEProc(@oDanfe, , cIDEnt, Nil, Nil, @lExistNFe, lIsLoja)
			endif
		else
			if  nQtdTotal >= nLimitImp 
					lImprime := FWAlertYesNo("Foram informadas "+Alltrim(Str(nQtdTotal))+" DANFE para impressão."+(Chr(13)+Chr(10))+;
						(Chr(13)+Chr(10))+(Chr(13)+Chr(10))+;
						"Deseja prosseguir com a impressão desta alta quantidade?" +(Chr(13)+Chr(10))+(Chr(13)+Chr(10))+(Chr(13)+Chr(10))+;
						"OBS.: A impressão será realizada em lotes de até "+Alltrim(Str(nLimitImp))+" DANFE cada.",+;
						"Atenção - Alta quantidade de notas selecionada!")
					lQuebraImp := .T.
			endIf

			if lImprime
				if lQuebraImp
					DivLtDanfeImp(oDanfe, nQtdDocs, nLimitImp, cIDEnt, lIsLoja, lJob, oSetup, @lExistNFe, @cNfceMens)
				else
					RPTStatus( {|lEnd| DANFEProc(@oDanfe, @lEnd, cIDEnt, Nil, Nil, @lExistNFe, lIsLoja, @cNfceMens )}, "Imprimindo DANFE..." )
				endif
			endif
		endif
	EndIf

	If lExistNFe
		if !lQuebraImp
			oDanfe:Preview()	//Visualiza antes de imprimir
		endif
	Else
		If !lIsLoja .and. !lJob .and. !lQuebraImp
			Aviso("DANFE","Nenhuma NF-e a ser impressa nos parametros utilizados.",{"OK"},3)
		EndIf
	EndIf
EndIf

//Se SIGALOJA, o objeto oDANFE é destruido onde foi instanciado
If lIsLoja
	lRet := lExistNFe
//Tratamento para as Notas não impressas do Modelo "65- NFCE" pela Rotina SPEDNFE
Elseif !Empty(cNfceMens)  
	cNaoImp := "A impressão do DANFE referente ao Modelo do Documento NFC-e deve ser impresso pela Modulo SigaLoja." 
	cNaoImp += CRLF
	cNaoImp += CRLF
	cNaoImp += "Segue relação de Documentos não impressos: " +CRLF
	cNaoImp += CRLF
	cNaoImp += cNfceMens
	Aviso( "           			SPED   ", cNaoImp, {"OK"}, 3 )
Else
	FreeObj(oDANFE)
	oDANFE := Nil	
EndIf

RestArea(aArea)
aSize(aArea, 0)
aArea:= nil

Return lRet

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³DANFEProc ³ Autor ³ Eduardo Riera         ³ Data ³16.11.2006³±±
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
Static Function DanfeProc(	oDanfe	, lEnd		, cIdEnt	, cVal1,;
							cVal2	, lExistNfe	, lIsLoja	, cNfceMens	)

Local aArea      := GetArea()
Local aAreaSF3   := {}
Local aNotas     := {}
Local aXML       := {}
Local cNaoAut    := ""

Local cAliasSF3  := "SF3"
Local cWhere     := ""
Local cAviso     := ""
Local cErro      := ""
Local cCodRetSF3 := ""
Local cMsgSF3    := ""
Local cCodRetNFE := ""
Local cAutoriza  := ""
Local cModalidade:= ""
Local cChaveSFT  := ""
Local cAliasSFT  := "SFT"
Local cCondicao	 := ""
Local cIndex	 := ""
Local cChave	 := ""
Local cCampos 	 := ""
Local cTabela	 := ""
Local lSdoc  	 := TamSx3("F3_SERIE")[1] == 14
Local cFrom 	 := ""
Local cSerie 	 := ""

Local lQuery     := .F.

Local nX         := 0
Local nI		 := 0

Local oNfe
Local nLenNotas
Local lImpDir	 :=GetNewPar("MV_IMPDIR",.F.)
Local aGrvSF3    := {}
Local lUsaColab	 :=  UsaColaboracao("1") 
Local lMVGfe	 := GetNewPar( "MV_INTGFE", .F. ) // Se tem integração com o GFE
local lChave	 := .F.
local cChavSF3 	 := ""
local lMnVldAR1  := SuperGetMv("MV_RSKVLDF",.F.,.F.) .And. ExistFunc("RskIsActive") .And. RskIsActive() 
local aAreaAR1   := AR1->(GetArea())

default cNfceMens	:= ""	//Mensagem para as Notas não impressas do Modelo "65- NFCE" pela Rotina SPEDNFE
default lEnd 		:= .F.
default lIsLoja		:= .F.

MV_PAR01 := AllTrim(MV_PAR01)
MV_PAR02 := AllTrim(MV_PAR02)

if valtype(cVal1) <> 'U'
	MV_PAR01 := cVal1
endif

if valtype(cVal2) <> 'U'
	MV_PAR02 := cVal2
endif

If lMnVldAR1
	AR1->(DbSetOrder(2)) // AR1_FILIAL+AR1_FILNF+AR1_DOC+AR1_SERIE+AR1_CLIENT+AR1_LOJA
EndIf

If !lImpDir
	dbSelectArea("SF3")
	dbSetOrder(5)
	#IFDEF TOP
		cTabela := "SF3"
		cCampos := "SF3.F3_FILIAL,SF3.F3_ENTRADA,SF3.F3_NFELETR,SF3.F3_CFO,SF3.F3_FORMUL,SF3.F3_NFISCAL,SF3.F3_SERIE,SF3.F3_CLIEFOR,SF3.F3_LOJA,SF3.F3_ESPECIE,SF3.F3_DTCANC"	
		cAliasSF3 := setQuery(cTabela, cCampos, .T.)
		lQuery    := .T.
		
	#ELSE
		cIndex    		:= CriaTrab(NIL, .F.)
		cChave			:= IndexKey(6)
		cCondicao 		:= 'F3_FILIAL == "' + xFilial("SF3") + '" .And. '
		cCondicao 		+= 'SF3->F3_SERIE =="'+ MV_PAR03+'" .And. '
		cCondicao 		+= 'SF3->F3_NFISCAL >="'+ MV_PAR01+'" .And. '
		cCondicao		+= 'SF3->F3_NFISCAL <="'+ MV_PAR02+'" .And. '
		cCondicao		+= 'SF3->F3_ESPECIE IN ("SPED","NFCE") .And. '
		cCondicao		+= 'Empty(SF3->F3_DTCANC)'
		IndRegua(cAliasSF3, cIndex, cChave, , cCondicao)
		nIndex := RetIndex(cAliasSF3)
				DBSetIndex(cIndex + OrdBagExt())
				DBSetOrder(nIndex + 1)
		DBGoTop()
	#ENDIF
	If MV_PAR04==1
		cWhere := "SubStr(F3_CFO,1,1) < '5' .AND. F3_FORMUL=='S'"
	Elseif MV_PAR04==2
		cWhere := "SubStr(F3_CFO,1,1) >= '5'"
	Else
		cWhere := ".T."
	EndIf
	
	If lSdoc
		cSerId := (cAliasSF3)->F3_SDOC
	Else
		cSerId := (cAliasSF3)->F3_SERIE
	EndIf
	
	While !Eof() .And. xFilial("SF3") == (cAliasSF3)->F3_FILIAL .And.;
		cSerId == MV_PAR03 .And.;
		(cAliasSF3)->F3_NFISCAL >= MV_PAR01 .And.;
		(cAliasSF3)->F3_NFISCAL <= MV_PAR02
		
		dbSelectArea(cAliasSF3)

			//------ Tratamento para não Impressão do Danfe do NFC-e quando chamado pela Rotina SPEDNFE ---//
			if !lIsLoja .and. Alltrim((cAliasSF3)->F3_ESPECIE) =='NFCE'
				cNfceMens += "Doc: " +(cAliasSF3)->F3_NFISCAL + " Serie: "+(cAliasSF3)->F3_SERIE +CRLF
				(cAliasSF3)->(DbSkip())
				loop 
			endif
			//---------------------------------------------------------------------------------------------//
			//------  Tratamento para não Imprimir Danfe do Totvs Mais Negócios quando não Aprovada ----// 
			If lMnVldAR1 .And. AR1->(MsSeek(xFilial("AR1")+(cAliasSF3)->F3_FILIAL+(cAliasSF3)->F3_NFISCAL+(cAliasSF3)->F3_SERIE+(cAliasSF3)->F3_CLIEFOR+(cAliasSF3)->F3_LOJA ) )
				If AR1->AR1_STATUS <> "2"
					cNaoAut += "A impressão do DANFE referente ao Doc/Série " + AllTrim( (cAliasSF3)->F3_NFISCAL ) + "/" + (cAliasSF3)->F3_SERIE + " NÃO FOI REALIZADA pelo motivo abaixo:"
					cNaoAut += CRLF + "[ Nota Fiscal TOTVS Mais Negócios não aprovada! ]" + CRLF
					(cAliasSF3)->(DbSkip())
					Loop
				EndIf
			EndIf
			//------------------------------------------------------------------------------------------//

			If  Empty((cAliasSF3)->F3_DTCANC) .And. &cWhere //.And. AModNot((cAliasSF3)->F3_ESPECIE)=="55"
				
				If (SubStr((cAliasSF3)->F3_CFO,1,1)>="5" .Or. (cAliasSF3)->F3_FORMUL=="S") .And. aScan(aNotas,{|x| x[4]+x[5]+x[6]+x[7]==(cAliasSF3)->F3_SERIE+(cAliasSF3)->F3_NFISCAL+(cAliasSF3)->F3_CLIEFOR+(cAliasSF3)->F3_LOJA})==0
					
					aadd(aNotas,{})
					aadd(Atail(aNotas),.F.)
					aadd(Atail(aNotas),IIF((cAliasSF3)->F3_CFO<"5","E","S"))
					aadd(Atail(aNotas),(cAliasSF3)->F3_ENTRADA)
					aadd(Atail(aNotas),(cAliasSF3)->F3_SERIE)
					aadd(Atail(aNotas),(cAliasSF3)->F3_NFISCAL)
					aadd(Atail(aNotas),(cAliasSF3)->F3_CLIEFOR)
					aadd(Atail(aNotas),(cAliasSF3)->F3_LOJA)
					
				EndIf
			EndIf
			
			dbSelectArea(cAliasSF3)
			dbSkip()

			If lSdoc
				cSerId := (cAliasSF3)->F3_SDOC
			Else
				cSerId := (cAliasSF3)->F3_SERIE
			EndIf

			If lEnd
				Exit
			EndIf
			If Len(aNotas) >= 50 .Or. 	(cAliasSF3)->(Eof())
				aAreaSF3 := (cAliasSF3)->(GetArea())
				if lUsaColab
					//Tratamento do TOTVS Colaboração
					aXml := GetXMLColab(aNotas,@cModalidade,lUsaColab)
				else
					aXml := GetXML(cIdEnt,aNotas,@cModalidade, oDanfe:lInJob)
				endif	

				nLenNotas := Len(aNotas)
				For nX := 1 To nLenNotas
					If !Empty(aXML[nX][2])
						If !Empty(aXml[nX])
							cAutoriza		:= aXML[nX][1]
							cCodAutDPEC	:= aXML[nX][5]
							cCodRetNFE		:= aXML[nX][9]
							cCodRetSF3		:= iif ( Empty (cCodAutDPEC),cCodRetNFE,cCodAutDPEC )
							cMsgSF3		:= iif ( aXML[nX][10]<> Nil ,aXML[nX][10],"")
						Else
							cAutoriza		:= ""
							cCodAutDPEC	:= ""
							cCodRetNFE		:= ""
							cCodRetSF3		:= ""
							cMsgSF3		:= ""
							
						EndIf
						If (!Empty(cAutoriza) .Or. !Empty(cCodAutDPEC) .Or. Alltrim(aXML[nX][8])$"2,5") .And. !cCodRetNFE $ RetCodDene()
							If aNotas[nX][02]=="E"
								DBClearFilter()
								dbSelectArea("SF1")
								dbSetOrder(1)
								If MsSeek(xFilial("SF1")+aNotas[nX][05]+aNotas[nX][04]+aNotas[nX][06]+aNotas[nX][07]) .And. SF1->(FieldPos("F1_FIMP")) <> 0 .And. Alltrim(aXML[nX][8])$"1,3,4,6,7" .or. ( Alltrim(aXML[nX][8]) $ "2,5"  .And. !Empty(cAutoriza) )
									RecLock("SF1")
									If !SF1->F1_FIMP$"D"
										SF1->F1_FIMP := "S"
									EndIf
									If SF1->(FieldPos("F1_CHVNFE"))>0
										SF1->F1_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
									EndIf
									If SF1->(FieldPos("F1_HAUTNFE")) > 0 .and. SF1->(FieldPos("F1_DAUTNFE")) > 0 //grava a data e hora de autorização da NFe
										SF1->F1_HAUTNFE := IIF(!Empty(aXML[nX][6]),SUBSTR(aXML[nX][6],1,5),"")
				   						SF1->F1_DAUTNFE	:= IIF(!Empty(aXML[nX][7]),aXML[nX][7],SToD("  /  /    "))
									EndIf
									MsUnlock()
								EndIf
							Else
								dbSelectArea("SF2")
								dbSetOrder(1)
								If MsSeek(xFilial("SF2")+aNotas[nX][05]+aNotas[nX][04]+aNotas[nX][06]+aNotas[nX][07]) .And. Alltrim(aXML[nX][8])$"1,3,4,6,7".Or. ( Alltrim(aXML[nX][8]) $ "2,5"  .And. !Empty(cAutoriza) )
									RecLock("SF2")
									If !SF2->F2_FIMP$"D"
										SF2->F2_FIMP := "S"
									EndIf
									If SF2->(FieldPos("F2_CHVNFE"))>0
										SF2->F2_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
									EndIf
									If SF2->(FieldPos("F2_HAUTNFE")) > 0 .and. SF2->(FieldPos("F2_DAUTNFE")) > 0 //grava a data e hota de autorização da NFe
										SF2->F2_HAUTNFE := IIF(!Empty(aXML[nX][6]),SUBSTR(aXML[nX][6],1,5),"")
				   						SF2->F2_DAUTNFE	:= IIF(!Empty(aXML[nX][7]),aXML[nX][7],SToD("  /  /    "))
									EndIf
									MsUnlock()
									// Grava quando a nota for Transferencia entre filiais 
									IF SF2->(FieldPos("F2_FILDEST"))> 0 .And. SF2->(FieldPos("F2_FORDES"))> 0 .And.SF2->(FieldPos("F2_LOJADES"))> 0 .And.SF2->(FieldPos("F2_FORMDES"))> 0 .And. !EMPTY (SF2->F2_FORDES)  
										SF1->(dbSetOrder(1))
										If SF1->(MsSeek(SF2->F2_FILDEST+SF2->F2_DOC+SF2->f2_SERIE+SF2->F2_FORDES+SF2->F2_LOJADES+SF2->F2_FORMDES))
											If EMPTY(SF1->F1_CHVNFE)	
												RecLock("SF1",.F.)
													SF1->F1_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
												MsUnlock()
											EndIf	
										Endif					    
									EndiF
								ElseIF MsSeek(xFilial("SF2")+aNotas[nX][05]+aNotas[nX][04]+aNotas[nX][06]+aNotas[nX][07]) .And. Alltrim(aXML[nX][8])$"1,3,4,6".Or. ( Alltrim(aXML[nX][8]) $ "2,5"  .And. cModalidade == "7"  ) //Contingencia FSDA
									RecLock("SF2")
									SF2->F2_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
									MsUnlock()
								EndIf
								
								// Atualização dos campos da Tabela GFE
								if FindFunction("GFECHVNFE") .and. lMVGfe  // Integração com o GFE 
									if  SF2->F2_TIPO $ "D|B"    // Documento com tipo de devolução ou "Utilizar Fornecedor"
										dbSelectArea("SA2")
										dbSetOrder(1)
										If SA2->(MsSeek(xFilial("SA2")+ SF2->F2_CLIENTE + SF2->F2_LOJA,.T.))
											GFECHVNFE(xFilial("SF2"),SF2->F2_SERIE,SF2->F2_DOC,SF2->F2_TIPO,SA2->A2_CGC,SA2->A2_COD,SA2->A2_LOJA,SF2->F2_CHVNFE,SF2->F2_FIMP, "S")
										EndIf
									else
										dbSelectArea("SA1")
										dbSetOrder(1)
										If SA1->(MsSeek(xFilial("SA1")+ SF2->F2_CLIENTE + SF2->F2_LOJA,.T.))
											GFECHVNFE(xFilial("SF2"),SF2->F2_SERIE,SF2->F2_DOC,SF2->F2_TIPO,SA1->A1_CGC,SA1->A1_COD,SA1->A1_LOJA,SF2->F2_CHVNFE,SF2->F2_FIMP, "S")
										Endif
									endif
								endif 

								If ExistFunc("STFMMd5NS") //Função do Controle de Lojas - Legislação PAF-ECF
									STFMMd5NS()
								EndIf
							EndIf
							dbSelectArea("SFT")
							dbSetOrder(1)
							If SFT->(FieldPos("FT_CHVNFE"))>0
								cChaveSFT	:=	(xFilial("SFT")+aNotas[nX][02]+aNotas[nX][04]+aNotas[nX][05]+aNotas[nX][06]+aNotas[nX][07])
								If MsSeek(cChaveSFT)
									Do While !(cAliasSFT)->(Eof ()) .And.;
										cChaveSFT==(cAliasSFT)->FT_FILIAL+(cAliasSFT)->FT_TIPOMOV+(cAliasSFT)->FT_SERIE+(cAliasSFT)->FT_NFISCAL+(cAliasSFT)->FT_CLIEFOR+(cAliasSFT)->FT_LOJA 
										If (cAliasSFT)->FT_TIPOMOV $"S" .Or. ((cAliasSFT)->FT_TIPOMOV $"E" .And. (cAliasSFT)->FT_FORMUL=='S')
											RecLock("SFT")
											SFT->FT_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
											MsUnLock()
											//Array criado para gravar o SF3 no final, pois a tabela SF3 pode estah em processamento quando se trata de DBF ou AS/400.
											If aScan(aGrvSF3,{|aX|aX[1]+aX[2]+aX[3]+aX[4]+aX[5]==(cAliasSFT)->(FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_IDENTF3)})==0
												aAdd(aGrvSF3, {(cAliasSFT)->FT_SERIE,(cAliasSFT)->FT_NFISCAL,(cAliasSFT)->FT_CLIEFOR,(cAliasSFT)->FT_LOJA,(cAliasSFT)->FT_IDENTF3,(cAliasSFT)->FT_CHVNFE,cAutoriza,cCodRetSF3,cMsgSF3})
											EndIf										
										EndiF
										DbSkip()
									EndDo
								EndIf
							EndIf 
							// Grava quando a nota for Transferencia entre filiais  
							IF SF1->(!EOF()) .And. SF2->(FieldPos("F2_FILDEST"))> 0 .And. SF2->(FieldPos("F2_FORDES"))> 0 .And.SF2->(FieldPos("F2_LOJADES"))> 0 .And.SF2->(FieldPos("F2_FORMDES"))> 0 .And. !EMPTY (SF2->F2_FORDES)  
							  	SFT->(dbSetOrder(1))
								cChaveSFT := SF1->F1_FILIAL+"E"+SF1->F1_SERIE+SF1->F1_DOC+SF1->F1_FORNECE+SF1->F1_LOJA
								If SFT->(MsSeek(cChaveSFT))
									Do While cChaveSFT == SFT->FT_FILIAL+"E"+SFT->FT_SERIE+SFT->FT_NFISCAL+SFT->FT_CLIEFOR+SFT->FT_LOJA .And. !SFT->(Eof())
										RecLock("SFT")
										SFT->FT_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
										MsUnLock()
										//Array criado para gravar o SF3 no final, pois a tabela SF3 pode estah em processamento quando se trata de DBF ou AS/400.
										If aScan(aGrvSF3,{|aX|aX[1]+aX[2]+aX[3]+aX[4]+aX[5]==(cAliasSFT)->(FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_IDENTF3)})==0
											aAdd(aGrvSF3, {(cAliasSFT)->FT_SERIE,(cAliasSFT)->FT_NFISCAL,(cAliasSFT)->FT_CLIEFOR,(cAliasSFT)->FT_LOJA,(cAliasSFT)->FT_IDENTF3,(cAliasSFT)->FT_CHVNFE,cAutoriza,cCodRetSF3,cMsgSF3})
										EndIf
										SFT->(dbSkip())
							    	EndDo
								EndIf
							EndIf
							
							cAviso := ""
							cErro  := ""
							//-----------------------------------------------------------------------
							// Validacao para quando for TOTVS Colaboracao, pois o retorno do 
							// xml sera o que vem da Neogrid, e nao o que enviamos.
							// Para que nao fosse alterado totalmente a estrutura do Objeto, 
							// atribui a variavel oRetNF o retorno, e abaixo identifico se possui 
							// o objeto NFEPROC, caso tenha, deixarei na mesma estrutura do legado.					
							// @autor: Douglas Parreja	@since 30/10/2017												
							//-----------------------------------------------------------------------												
							oRetNF := XmlParser(aXML[nX][2],"_",@cAviso,@cErro)				 	
							if ValAtrib("oRetNF:_NFEPROC") <> "U"
								oNfe := WSAdvValue( oRetNF,"_NFEPROC","string",NIL,NIL,NIL,NIL,NIL)				
							else
								oNfe := oRetNF
							endif
							
							oNfeDPEC := XmlParser(aXML[nX][4],"_",@cAviso,@cErro)
							If Empty(cAviso) .And. Empty(cErro)
								ImpDet(@oDanfe,oNFe,cAutoriza,cModalidade,oNfeDPEC,cCodAutDPEC,aXml[nX][6],aXml[nX][7],aNotas[nX],aXml[nX][11])
								lExistNfe := .T.
							EndIf
							oNfe     := nil
							oNfeDPEC := nil

						ElseIf lIsLoja							
							/*	Se o Codigo de Retorno da SEFAZ estiver preenchido e for maior que 200,
								entao houve rejeicao por parte da SEFAZ	*/
							If !Empty(aXML[nX][9]) .AND. Val(aXML[nX][9]) > 200 
								RecLock("SF2",.F.)
								Replace SF2->F2_FIMP with "N"
								SF2->( MsUnlock() )

								cNaoAut := "A impressão do DANFE referente a Nota/Série " + SF2->F2_DOC + "/" + SF2->F2_SERIE + " não será realizada pelo motivo abaixo:"
								cNaoAut += CRLF + "[" + aXML[nX][9] + ' - ' + aXML[nX][10] + "]"
								cNaoAut += CRLF + "Se possível, faça o ajuste e retransmita a NF-e."

								if !oDanfe:lInJob
									Aviso( "SPED", cNaoAut, {"Continuar"}, 3 )
								endif
							EndIf	

						Else
							cNaoAut += aNotas[nX][04]+aNotas[nX][05]+CRLF
						EndIf
					EndIf
					
				Next nX
				aNotas := {}
				
				RestArea(aAreaSF3)
				DelClassIntF()
			EndIf
		EndDo

		if lQuery
			(cAliasSF3)->(dbCloseArea())
		else
			DBClearFilter()
			Ferase(cIndex+OrdBagExt())
		endif

		If !lIsLoja .AND. !Empty(cNaoAut) .and. !oDanfe:lInJob
			Aviso("SPED","As seguintes notas não foram autorizadas: "+CRLF+CRLF+cNaoAut,{"Ok"},3)
		EndIf

	ElseIf  lImpDir
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Tratamento para quando o parametro MV_IMPDIR esteja        ³
		//³Habilitado, neste caso não será feita a impressão conforme ³
		//³Registros no SF3, e sim buscando XML diretamente do        ³
		//³webService, e caso exista será impresso.                   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		if  Val(MV_PAR02) - Val(MV_PAR01) > 0 .or. MV_PAR01 == MV_PAR02
			If MV_PAR04==1			
				cxFilial := xFilial("SF1")
				cTabela := "SF1"
				cCampos += "SF1.F1_FILIAL FILIAL, SF1.F1_DOC DOC, SF1.F1_SERIE SERIE,SF1.F1_FORNECE FORNECE,SF1.F1_LOJA LOJA"

			ElseIf MV_PAR04==2				
				cxFilial := xFilial("SF2")
				cTabela := "SF2"
				cCampos += "SF2.F2_FILIAL FILIAL, SF2.F2_DOC DOC, SF2.F2_SERIE SERIE"

			Endif
			
			cAliasSFX := setQuery(cTabela, cCampos, .T.)

			(cAliasSFX)->(DBGoTop())
			
			While  (cAliasSFX)->(!Eof()) .And. ;
				cxFilial == (cAliasSFX)->FILIAL .And.;
				if(lSdoc,(cAliasSFX)->SDOC, (cAliasSFX)->SERIE) == MV_PAR03 .And.;
				(cAliasSFX)->DOC >= MV_PAR01 .And.;
				(cAliasSFX)->DOC <= MV_PAR02
										
				aNotas := {}
				For nx:=1 To 20
					aadd(aNotas,{})
					aadd(Atail(aNotas),.F.)
					aadd(Atail(aNotas),IIF(MV_PAR04==1,"E","S"))
					aadd(Atail(aNotas),"")
					aadd(Atail(aNotas),(cAliasSFX)->SERIE)
					aadd(Atail(aNotas),(cAliasSFX)->DOC)
					aadd(Atail(aNotas),if( MV_PAR04==1, (cAliasSFX)->FORNECE, ""))
					aadd(Atail(aNotas),if( MV_PAR04==1, (cAliasSFX)->LOJA, ""))
					If ( (cAliasSFX)->(Eof()) )
						exit
					EndIF
					( cAliasSFX )->( DbSkip() )
				Next nX

				aXml:={}
				if lUsaColab
					//Tratamento do TOTVS Colaboração
					aXml := GetXMLColab(aNotas,@cModalidade,lUsaColab)
				else		
					aXml := GetXML(cIdEnt,aNotas,@cModalidade, oDanfe:lInJob)
				endif
				
				nLenNotas := Len(aNotas)
				For nx :=1 To nLenNotas
					dbSelectArea("SFT")
					dbSetOrder(1)
					cChaveSFT	:=	(xFilial("SFT")+aNotas[nX][02]+aNotas[nX][04]+aNotas[nX][05])
					MsSeek(cChaveSFT)

					//------ Tratamento para não Impressão do Danfe do NFC-e quando chamado pela ina SPEDNFE ---//
					if !lIsLoja .and. AllTrim((cAliasSFT)->FT_ESPECIE) =='NFCE'
						cNfceMens += " Doc:  " +(cAliasSFT)->FT_NFISCAL + " Serie: "+(cAliasSFT)->FT_SERIE + CRLF 
						loop 
					endif
					//-----------------------------------------------------------------------------------------//					
					//------  Tratamento para não Imprimir Danfe do Totvs Mais Negócios quando não Aprovada ----// 
					If lMnVldAR1 .And. AR1->(MsSeek(xFilial("AR1")+(cAliasSFT)->FT_FILIAL+(cAliasSFT)->FT_NFISCAL+(cAliasSFT)->FT_SERIE+(cAliasSFT)->FT_CLIEFOR+(cAliasSFT)->FT_LOJA ) )
						If AR1->AR1_STATUS <> "2"
							cNaoAut += "A impressão do DANFE referente ao Doc/Série " + AllTrim( (cAliasSFT)->FT_NFISCAL ) + "/" + (cAliasSFT)->FT_SERIE + " NÃO FOI REALIZADA pelo motivo abaixo:"
							cNaoAut += CRLF + "[ Nota Fiscal TOTVS Mais Negócios não aprovada! ]" + CRLF
							Loop
						EndIf
					EndIf
					//------------------------------------------------------------------------------------------//

					If ( !Empty(aXML[nX][2]) .AND. (AllTrim((cAliasSFT)->FT_ESPECIE)$'SPED,NFCE') .Or. (lImpDir .And. !Empty(aXML[nX][2])) ) .And. Empty((cAliasSFT)->FT_DTCANC) //Realizada tal alteração para que seja verificado antes da impressão se a NF-e está cancelada ou e do modelo sped
						If !Empty(aXml[nX])
							cAutoriza		:= aXML[nX][1]
							cCodAutDPEC	:= aXML[nX][5]
							cCodRetNFE		:= aXML[nX][9]
							cCodRetSF3		:= iif ( Empty (cCodAutDPEC),cCodRetNFE,cCodAutDPEC )
							cMsgSF3		:= iif ( aXML[nX][10]<> Nil ,aXML[nX][10],"")
						Else
							cAutoriza		:= ""
							cCodAutDPEC	:= ""
							cCodRetNFE		:= ""
							cCodRetSF3		:= ""
							cMsgSF3		:= ""
						EndIf
						cAviso := ""
						cErro  := ""
						//-----------------------------------------------------------------------
						// Validacao para quando for TOTVS Colaboracao, pois o retorno do 
						// xml sera o que vem da Neogrid, e nao o que enviamos.
						// Para que nao fosse alterado totalmente a estrutura do Objeto, 
						// atribui a variavel oRetNF o retorno, e abaixo identifico se possui 
						// o objeto NFEPROC, caso tenha, deixarei na mesma estrutura do legado.					
						// @autor: Douglas Parreja	@since 30/10/2017												
						//-----------------------------------------------------------------------												
						oRetNF := XmlParser(aXML[nX][2],"_",@cAviso,@cErro)				 	
						if ValAtrib("oRetNF:_NFEPROC") <> "U"
							oNfe := WSAdvValue( oRetNF,"_NFEPROC","string",NIL,NIL,NIL,NIL,NIL)				
						else
							oNfe := oRetNF
						endif
						
						oNfeDPEC := XmlParser(aXML[nX][4],"_",@cAviso,@cErro)
						//(se possui protocolo ou protocolo dpec ou a modalidade de transmissao for 2 ou 5) E codigo retorno nao esta na lista
						If (!Empty(cAutoriza) .Or. !Empty(cCodAutDPEC) .Or. Alltrim(aXML[nX][8])$"2,5") .And. !cCodRetNFE $ RetCodDene()
							If aNotas[nX][02]=="E" .And. MV_PAR04==1 .And. (oNfe:_NFE:_INFNFE:_IDE:_TPNF:TEXT=="0")
								dbSelectArea("SF1")
								dbSetOrder(1)
								If MsSeek(xFilial("SF1")+aNotas[nX][05]+aNotas[nX][04]) .And. SF1->(FieldPos("F1_FIMP"))<>0 .And. Alltrim(aXML[nX][8])$"1,3,4,6" .or. ( Alltrim(aXML[nX][8]) $ "2,5"  .And. !Empty(cAutoriza) )
									Do While !Eof() .And. SF1->F1_DOC==aNotas[nX][05] .And. SF1->F1_SERIE==aNotas[nX][04]
										If SF1->F1_FORMUL=='S'
											if RecLock("SF1")
												If !SF1->F1_FIMP$"D"
													SF1->F1_FIMP := "S"
												EndIf
												If SF1->(FieldPos("F1_CHVNFE"))>0
													SF1->F1_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
												EndIf
												If SF1->(FieldPos("F1_HAUTNFE")) > 0 .and. SF1->(FieldPos("F1_DAUTNFE")) > 0 //grava a data e hora de autorização da NFe
													SF1->F1_HAUTNFE := IIF(!Empty(aXML[nX][6]),SUBSTR(aXML[nX][6],1,5),"")
													SF1->F1_DAUTNFE	:= IIF(!Empty(aXML[nX][7]),aXML[nX][7],SToD("  /  /    "))
												EndIf
												SF1->(MsUnlock())
											endif

											// Atualização dos campos da Tabela GFE
											if FindFunction("GFECHVNFE") .and. lMVGfe  // Integração com o GFE 
												if  SF1->F1_TIPO $ "D|B"    // Documento com tipo de devolução ou "Utilizar Fornecedor"
													dbSelectArea("SA1")
													dbSetOrder(1)
													If SA1->(DbSeek(xFilial("SA1")+ SF1->F1_FORNECE + SF1->F1_LOJA))
														GFECHVNFE(xFilial("SF1"),SF1->F1_SERIE,SF1->F1_DOC,SF1->F1_TIPO,SA1->A1_CGC,SA1->A1_COD,SA1->A1_LOJA,SF1->F1_CHVNFE,SF1->F1_FIMP, "E")
													Endif
												else
													dbSelectArea("SA2")
													dbSetOrder(1)
													If SA2->(MsSeek(xFilial("SA2")+ SF1->F1_FORNECE + SF1->F1_LOJA,.T.))
														GFECHVNFE(xFilial("SF1"),SF1->F1_SERIE,SF1->F1_DOC,SF1->F1_TIPO,SA2->A2_CGC,SA2->A2_COD,SA2->A2_LOJA,SF1->F1_CHVNFE,SF1->F1_FIMP, "E")
													endif
												endif
											endif
										EndIf

										SF1->(DbSkip())
									EndDo
								EndIf
							ElseIf aNotas[nX][02]=="S" .And. MV_PAR04==2 .And. (oNfe:_NFE:_INFNFE:_IDE:_TPNF:TEXT=="1")
								dbSelectArea("SF2")
								dbSetOrder(1)
								If MsSeek(xFilial("SF2")+PADR(aNotas[nX][05],TAMSX3("F2_DOC")[1])+aNotas[nX][04]) .And. Alltrim(aXML[nX][8])$"1,3,4,6,7" .Or. ( Alltrim(aXML[nX][8]) $ "2,5"  .And. !Empty(cAutoriza) )
									RecLock("SF2")
									If !SF2->F2_FIMP$"D"
										SF2->F2_FIMP := "S"
									EndIf
									If SF2->(FieldPos("F2_CHVNFE"))>0
										SF2->F2_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
									EndIf
									If SF2->(FieldPos("F2_HAUTNFE")) > 0 .and. SF2->(FieldPos("F2_DAUTNFE")) > 0 //grava a data e hota de autorização da NFe
										SF2->F2_HAUTNFE := IIF(!Empty(aXML[nX][6]),SUBSTR(aXML[nX][6],1,5),"")
				   						SF2->F2_DAUTNFE	:= IIF(!Empty(aXML[nX][7]),aXML[nX][7],SToD("  /  /    "))
									EndIf								
									MsUnlock()
									// Grava quando a nota for Transferencia entre filiais 
									IF SF2->(FieldPos("F2_FILDEST"))> 0 .And. SF2->(FieldPos("F2_FORDES"))> 0 .And.SF2->(FieldPos("F2_LOJADES"))> 0 .And.SF2->(FieldPos("F2_FORMDES"))> 0 .And. !EMPTY (SF2->F2_FORDES)  
								       SF1->(dbSetOrder(1))
								    	If SF1->(MsSeek(SF2->F2_FILDEST+SF2->F2_DOC+SF2->f2_SERIE+SF2->F2_FORDES+SF2->F2_LOJADES+SF2->F2_FORMDES))
								    		If EMPTY(SF1->F1_CHVNFE)	
									    		RecLock("SF1",.F.)			
									    		SF1->F1_CHVNFE := SF2->F2_CHVNFE
									    		MsUnlock()
									    	EndIf	
								    	Endif					    
								    EndiF
								EndIf
								
								// Atualização dos campos da Tabela GFE
								if FindFunction("GFECHVNFE") .and. lMVGfe  // Integração com o GFE 										
									if  SF2->F2_TIPO $ "D|B"    // Documento com tipo de devolução ou "Utilizar Fornecedor"
										dbSelectArea("SA2")
										dbSetOrder(1)
										If SA2->(MsSeek(xFilial("SA2")+ SF2->F2_CLIENTE + SF2->F2_LOJA,.T.))
											GFECHVNFE(xFilial("SF2"),SF2->F2_SERIE,SF2->F2_DOC,SF2->F2_TIPO,SA2->A2_CGC,SA2->A2_COD,SA2->A2_LOJA,SF2->F2_CHVNFE,SF2->F2_FIMP, "S")
										EndIf
									else
										dbSelectArea("SA1")
										dbSetOrder(1)
										If SA1->(MsSeek(xFilial("SA1")+ SF2->F2_CLIENTE + SF2->F2_LOJA,.T.))
											GFECHVNFE(xFilial("SF2"),SF2->F2_SERIE,SF2->F2_DOC,SF2->F2_TIPO,SA1->A1_CGC,SA1->A1_COD,SA1->A1_LOJA,SF2->F2_CHVNFE,SF2->F2_FIMP, "S")
										Endif
									endif
								endif
							
								If ExistFunc("STFMMd5NS") //Função do Controle de Lojas - Legislação PAF-ECF
									STFMMd5NS()
								EndIf
							EndIf
							dbSelectArea("SFT")
							dbSetOrder(1)
							If SFT->(FieldPos("FT_CHVNFE"))>0
								cChaveSFT	:=	(xFilial("SFT")+aNotas[nX][02]+aNotas[nX][04]+padr(aNotas[nX][05],TamSx3("FT_NFISCAL")[1],""))
								IF MsSeek(cChaveSFT)
									Do While !(cAliasSFT)->(Eof ()) .And.;
										cChaveSFT==(cAliasSFT)->FT_FILIAL+(cAliasSFT)->FT_TIPOMOV+(cAliasSFT)->FT_SERIE+(cAliasSFT)->FT_NFISCAL
										If (cAliasSFT)->FT_TIPOMOV $"S" .Or. ((cAliasSFT)->FT_TIPOMOV $"E" .And. (cAliasSFT)->FT_FORMUL=='S')
											RecLock("SFT")
											SFT->FT_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
											MsUnLock()
											//Array criado para gravar o SF3 no final, pois a tabela SF3 pode estah em processamento quando se trata de DBF ou AS/400.
											If aScan(aGrvSF3,{|aX|aX[1]+aX[2]+aX[3]+aX[4]+aX[5]==(cAliasSFT)->(FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_IDENTF3)})==0
												aAdd(aGrvSF3, {(cAliasSFT)->FT_SERIE,(cAliasSFT)->FT_NFISCAL,(cAliasSFT)->FT_CLIEFOR,(cAliasSFT)->FT_LOJA,(cAliasSFT)->FT_IDENTF3,(cAliasSFT)->FT_CHVNFE,cAutoriza,cCodRetSF3,cMsgSF3})
											EndIf
										EndIf
										DbSkip()
									EndDo
								Endif
							EndIf
							// Grava quando a nota for Transferencia entre filiais 
							IF SF1->(!EOF()) .And. SF2->(FieldPos("F2_FILDEST"))> 0 .And. SF2->(FieldPos("F2_FORDES"))> 0 .And.SF2->(FieldPos("F2_LOJADES"))> 0 .And.SF2->(FieldPos("F2_FORMDES"))> 0 .And. !EMPTY (SF2->F2_FORDES)  
							  	SFT->(dbSetOrder(1))
								cChave := SF1->F1_FILIAL+"E"+SF1->F1_SERIE+SF1->F1_DOC+SF1->F1_FORNECE+SF1->F1_LOJA
								If SFT->(MsSeek(SF1->F1_FILIAL+"E"+SF1->F1_SERIE+SF1->F1_DOC+SF1->F1_FORNECE+SF1->F1_LOJA,.T.))
									Do While cChave == SFT->FT_FILIAL+"E"+SFT->FT_SERIE+SFT->FT_NFISCAL+SFT->FT_CLIEFOR+SFT->FT_LOJA .And. !SFT->(Eof())
											SFT->FT_CHVNFE := SubStr(NfeIdSPED(aXML[nX][2],"Id"),4)
											MsUnLock()
											//Array criado para gravar o SF3 no final, pois a tabela SF3 pode estah em processamento quando se trata de DBF ou AS/400.
											If aScan(aGrvSF3,{|aX|aX[1]+aX[2]+aX[3]+aX[4]+aX[5]==(cAliasSFT)->(FT_SERIE+FT_NFISCAL+FT_CLIEFOR+FT_LOJA+FT_IDENTF3)})==0
												aAdd(aGrvSF3, {(cAliasSFT)->FT_SERIE,(cAliasSFT)->FT_NFISCAL,(cAliasSFT)->FT_CLIEFOR,(cAliasSFT)->FT_LOJA,(cAliasSFT)->FT_IDENTF3,(cAliasSFT)->FT_CHVNFE,cAutoriza,cCodRetSF3,cMsgSF3})
											EndIf
										MsUnLock()
										SFT->(dbSkip())
							    	EndDo
								EndIf
							EndIf
							//-------------------------------
							If Empty(cAviso) .And. Empty(cErro) .And. MV_PAR04==1 .And. (oNfe:_NFE:_INFNFE:_IDE:_TPNF:TEXT=="0")
								ImpDet(@oDanfe,oNFe,cAutoriza,cModalidade,oNfeDPEC,cCodAutDPEC,aXml[nX][6],aXml[nX][7],aNotas[nX],aXml[nX][11])
								lExistNfe := .T.							
							ElseIf Empty(cAviso) .And. Empty(cErro) .And. MV_PAR04==2 .And. (oNfe:_NFE:_INFNFE:_IDE:_TPNF:TEXT=="1")
								ImpDet(@oDanfe,oNFe,cAutoriza,cModalidade,oNfeDPEC,cCodAutDPEC,aXml[nX][6],aXml[nX][7],aNotas[nX],aXml[nX][11])
								lExistNfe := .T.
							EndIf
	
						ElseIf lIsLoja							
							/*	Se o Codigo de Retorno da SEFAZ estiver preenchido e for maior que 200,
								entao houve rejeicao por parte da SEFAZ	*/
							If !Empty(aXML[nX][9]) .AND. Val(aXML[nX][9]) > 200 
								RecLock("SF2",.F.)
								Replace SF2->F2_FIMP with "N"
								SF2->( MsUnlock() )
	
								cNaoAut := "A impressão do DANFE referente a Nota/Série " + SF2->F2_DOC + "/" + SF2->F2_SERIE + " não será realizada pelo motivo abaixo:"
								cNaoAut += CRLF + "[" + aXML[nX][9] + ' - ' + aXML[nX][10] + "]."
								cNaoAut += CRLF + "Se possível, faça o ajuste e retransmita a NF-e."

								if !oDanfe:lInJob
									Aviso( "SPED", cNaoAut, {"Continuar"}, 3 )
								endif
							EndIf
	
						Else
							cNaoAut += aNotas[nX][04]+aNotas[nX][05]+CRLF
						EndIf
					EndIf
				freeObj(oNfe)
				oNfe     := nil 
				freeObj(oNfe)
				oNfeDPEC := nil
				delClassIntF()					
				Next nx
			EndDo

			(cAliasSFX)->(dbCloseArea())
		endif

		If !lIsLoja .AND. !Empty(cNaoAut) .and. !oDanfe:lInJob
			Aviso("SPED","As seguintes notas não foram autorizadas: "+CRLF+CRLF+cNaoAut,{"Ok"},3)
		EndIf
    EndIf
    
If Len(aGrvSF3)>0 .And. SF3->(FieldPos("F3_CHVNFE"))>0
	SF3->( dbSetOrder( 5 ))
	For nI := 1 To Len(aGrvSF3)
		cChavSF3 :=  xFilial("SF3")+aGrvSF3[nI,1]+aGrvSF3[nI,2]+aGrvSF3[nI,3]+aGrvSF3[nI,4]+aGrvSF3[nI,5]	
		If SF3->(MsSeek(xFilial("SF3")+aGrvSF3[nI,1]+aGrvSF3[nI,2]+aGrvSF3[nI,3]+aGrvSF3[nI,4]+aGrvSF3[nI,5]))
			Do While cChavSF3 == xFilial("SF3")+SF3->F3_SERIE+SF3->F3_NFISCAL+SF3->F3_CLIEFOR+SF3->F3_LOJA+SF3->F3_IDENTFT .And. !SF3->(Eof())
				lChave := iif( lUsacolab, .T., Empty(SF3->F3_CHVNFE) )
				If (Val(SF3->F3_CFO) >= 5000 .Or. SF3->F3_FORMUL=='S') .And. lChave
					RecLock("SF3",.F.)
					SF3->F3_CHVNFE := aGrvSF3[nI,6] // Chave da nota
					SF3->F3_PROTOC := aGrvSF3[nI,7] // Protocolo
					SF3->F3_CODRSEF:= aGrvSF3[nI,8] // Codigo de retorno Sefaz
					SF3->F3_DESCRET:= aGrvSF3[nI,9] // Mensagem de retorno Sefaz
					SF3->F3_CODRET := iif (SF3->(FieldPos("F3_CODRET"))>0,"M",)
					MsUnLock()
				EndIf
				SF3->(dbSkip())
			EndDo
		EndIf
	Next nI
EndIf
RestArea(aAreaAR1)
RestArea(aArea)

aSize(aArea, 0)
aArea:= nil
aSize(aAreaSF3, 0)
aAreaSF3:= nil
aSize(aNotas, 0)
aNotas:= nil
aSize(aXML, 0)
aXML:= nil
aSize(aGrvSF3, 0)
aGrvSF3:= nil
aSize(aAreaAR1, 0)
aAreaAR1:= nil

freeObj(oNfe)
oNfe	:= nil

Return(.T.)

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Program   ³ ImpDet   ³ Autor ³ Eduardo Riera         ³ Data ³16.11.2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Controle de Fluxo do Relatorio.                             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpO1: Objeto grafico de impressao                    (OPC) ³±±
±±³          ³ExpC2: String com o XML da NFe                              ³±±
±±³          ³ExpC3: Codigo de Autorizacao do fiscal                (OPC) ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³   DATA   ³ Programador   ³Manutencao efetuada                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³               ³                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function ImpDet(oDanfe,oNfe,cCodAutSef,cModalidade,oNfeDPEC,cCodAutDPEC,cDtHrRecCab,dDtReceb,aNota,cMsgRet)

Default cMsgRet := ""

PRIVATE oFont10N   := TFontEx():New(oDanfe,"Times New Roman",08,08,.T.,.T.,.F.)// 1
PRIVATE oFont07N   := TFontEx():New(oDanfe,"Times New Roman",07,07,.T.,.T.,.F.)// 2
PRIVATE oFont07    := TFontEx():New(oDanfe,"Times New Roman",07,07,.F.,.T.,.F.)// 3
PRIVATE oFont08    := TFontEx():New(oDanfe,"Times New Roman",07,07,.F.,.T.,.F.)// 4
PRIVATE oFont08N   := TFontEx():New(oDanfe,"Times New Roman",06,06,.T.,.T.,.F.)// 5
PRIVATE oFont09N   := TFontEx():New(oDanfe,"Times New Roman",08,08,.T.,.T.,.F.)// 6
PRIVATE oFont09    := TFontEx():New(oDanfe,"Times New Roman",08,08,.F.,.T.,.F.)// 7
PRIVATE oFont10    := TFontEx():New(oDanfe,"Times New Roman",10,10,.F.,.T.,.F.)// 8
PRIVATE oFont11    := TFontEx():New(oDanfe,"Times New Roman",10,10,.F.,.T.,.F.)// 9
PRIVATE oFont12    := TFontEx():New(oDanfe,"Times New Roman",11,11,.F.,.T.,.F.)// 10
PRIVATE oFont11N   := TFontEx():New(oDanfe,"Times New Roman",10,10,.T.,.T.,.F.)// 11
PRIVATE oFont18N   := TFontEx():New(oDanfe,"Times New Roman",17,17,.T.,.T.,.F.)// 12 
PRIVATE OFONT12N   := TFontEx():New(oDanfe,"Times New Roman",11,11,.T.,.T.,.F.)// 12 
PRIVATE oFont13N   := TFontEx():New(oDanfe,"Times New Roman",08,08,.T.,.T.,.F.)// 13 
PRIVATE lUsaColab	  :=  UsaColaboracao("1")

PrtDanfe(@oDanfe,oNfe,cCodAutSef,cModalidade,oNfeDPEC,cCodAutDPEC,cDtHrRecCab,dDtReceb,aNota,cMsgRet)

freeObj(oFont10N)
oFont10N := nil
freeObj(oFont07N)
oFont07N := nil
freeObj(oFont07)
oFont07 := nil
freeObj(oFont08)
oFont08 := nil
freeObj(oFont08N)
oFont08N := nil
freeObj(oFont09N)
oFont09N := nil
freeObj(oFont09)
oFont09 := nil
freeObj(oFont10)
oFont10 := nil
freeObj(oFont11)
oFont11 := nil
freeObj(oFont12)
oFont12 := nil
freeObj(oFont11N)
oFont11N := nil
freeObj(oFont18N)
oFont18N := nil
freeObj(OFONT12N)
OFONT12N := nil
freeObj(oFont13N)
oFont13N := nil

Return(.T.)


/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³PrtDanfe  ³ Autor ³Eduardo Riera          ³ Data ³16.11.2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Impressao do formulario DANFE grafico conforme laytout no   ³±±
±±³          ³formato retrato                                             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ PrtDanfe()                                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpO1: Objeto grafico de impressao                          ³±±
±±³          ³ExpO2: Objeto da NFe                                        ³±±
±±³          ³ExpC3: Codigo de Autorizacao do fiscal                (OPC) ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³   DATA   ³ Programador   ³Manutencao Efetuada                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³               ³                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function PrtDanfe(oDanfe,oNFE,cCodAutSef,cModalidade,oNfeDPEC,cCodAutDPEC,cDtHrRecCab,dDtReceb,aNota,cMsgRet)


Local aAuxCabec     := {} // Array que conterá as strings de cabeçalho das colunas de produtos/serviços.
Local aTamCol       := {} // Array que conterá o tamanho das colunas dos produtos/serviços.
Local aSimpNac		:= {}  
Local aSitTrib      := {}
Local aSitSN        := {}
Local aTransp       := {}
Local aDest         := {}
Local aHrEnt        := {}
Local aFaturas      := {}
Local aItens        := {}
Local aISSQN        := {}
Local aTotais       := {}
Local aAux          := {}
Local aUF           := {}
Local aMensagem     := {}
Local aEspVol       := {}
Local aEspecie      := {}
Local aIndImp       := {}
Local aIndAux       := {}
Local aCodONU		:= {}
Local aAreaSB5      := {}
Local aAreaDY3 		:= {}
Local aMensONU		:= {}
                           
Local nPosV         := 0
Local nAuxH2        := 0
Local nSnBaseIcm	:= 0
Local nSnValIcm		:= 0
Local nDetImp		:= 0
Local nS			:= 0
Local nX            := 0
Local nY            := 0
Local nL            := 0
Local nFolha        := 1
Local nFolhas       := 0
Local nBaseICM      := 0
Local nValICM       := 0
Local nBaseICMST    := 0
Local nValICMST     := 0
Local nValIPI       := 0
Local nPICM         := 0
Local nPIPI         := 0
Local nFaturas      := 0
Local nVTotal       := 0
Local nDesc         := 0
Local nQtd          := 0
Local nVUnit        := 0
Local nVolume	    := 0
Local nLenVol
Local nLenDet
Local nLenSit
Local nLenItens     := 0
Local nLenMensagens := 0
Local nColuna       := 0
Local nE            := 0
Local nMaxCod       := 10
Local nMaxDes       := MAXITEMC
Local nTamB5Cod		:= 0
Local nMsg			:= 0
local nPosOnu		:= 0

//Local nPerDesc      := 0
Local nVUniLiq      := 0
Local nVTotLiq      := 0
Local nZ            := 0

Local cAux          := ""
Local cSitTrib      := ""
Local cMVCODREG     := Alltrim( SuperGetMV("MV_CODREG", ," ") )
Local cGuarda       := "" 
Local cEsp          := ""
Local cXJust		:= ""
Local cDhCont		:= ""
Local cMensONU		:= ""
Local cCodOnu		:= ""
Local cAuxOnu		:= ""

Local lPreview      := .F.
Local lFlag         := .T.
Local lImpAnfav     := GetNewPar("MV_IMPANF",.F.) 
Local lImpInfAd     := GetNewPar("MV_IMPADIC",.F.)
Local lConverte     := GetNewPar("MV_CONVERT",.F.)
Local lImpSimpN		:= GetNewPar("MV_IMPSIMP",.F.)
Local lMv_ItDesc    := Iif( GetNewPar("MV_ITDESC","N")=="S", .T., .F. )
Local lNFori2       := .T.
Local lEntIpiDev   	:= GetNewPar("MV_EIPIDEV",.F.) /*Apenas para nota de entrada de Devolução de ipi. .T.-Séra destacado no cabeçalho + inf.compl/.F.-Será destacado apenas em inf.compl*/
Local lVerso		:= .F. // Impressão de DANFE no verso?
Local lPontilhado 	:= .F.

Local aAuxCom 		:= {}    	
Local cUnTrib		:= ""
Local nQtdTrib		:= 0
Local nVUnitTrib	:= 0

local aMsgRet 		:= {}

// RCIMS de MG
Local lUf_MG		:= ( SuperGetMv("MV_ESTADO") $ "MG" )	// Criado esta variavel para atender o RICMS de MG para totalizar por CFOP
Local nSequencia	:= 0
Local nSubTotal		:= 0
Local cCfop			:= ""
Local cCfopAnt		:= ""
Local aItensAux     := {}
Local aArray		:= {}
Local aRetirada     := {}
Local aEntrega      := {}

local cMarca		:= ""
local cNumeracao	:= ""
local aMarca		:= {}
local aNumeracao	:= {}

local nMaxUn	:= 4
local cAuxUn	:= ""
local lSpedCodOnu	:= existFunc("SpedCodOnu") .and. allTrim(superGetMv("MV_NONUINF",,"0")) == "1" 
local lInfAdProd	:= .F.
Local lFat853		:= .F.

Default cDtHrRecCab := ""
Default dDtReceb    := CToD("")

Private lNFCE 		:= Substr(oNFe:_NFe:_InfNfe:_ID:Text,24,2) == "65"
Private aInfNf      := {}

Private oDPEC       := oNfeDPEC
Private oNF         := oNFe:_NFe
Private oEmitente   := oNF:_InfNfe:_Emit
Private oIdent      := oNF:_InfNfe:_IDE
Private oDestino    := IIf(Type("oNF:_InfNfe:_Dest")=="U",Nil,oNF:_InfNfe:_Dest)
Private oTotal      := oNF:_InfNfe:_Total
Private oTransp     := oNF:_InfNfe:_Transp
Private oDet        := oNF:_InfNfe:_Det
Private oFatura     := IIf(Type("oNF:_InfNfe:_Cobr")=="U",Nil,oNF:_InfNfe:_Cobr)
Private oImposto
Private oEntrega	:= IIf(Type("oNF:_InfNfe:_Entrega") =="U",Nil,oNF:_InfNfe:_Entrega)
Private oRetirada	:= IIf(Type("oNF:_InfNfe:_Retirada")=="U",Nil,oNF:_InfNfe:_Retirada)

Private nPrivate    := 0
Private nPrivate2   := 0
Private nXAux	    := 0

Private lArt488MG   := .F.
Private lArt274SP   := .F.  

Private nAjustaImp    := 0
Private nAjustaRet    := 0
Private nAjustaEnt    := 0
Private nAjustaFat    := 0
Private nAjustaVt     := 0
Private nAjustaPro    := 0
Private nAjustaDad    := 0
Private nAjustaDest   := 0
Private nAjustaISSQN  := 0
Private nAjustaNat    := 0

oBrush      := TBrush():New( , CLR_BLACK )

IF oFatura<>Nil .AND. type("oNF:_InfNfe:_Cobr:_Dup") <> "U"
	IF ValType(oNF:_InfNfe:_Cobr:_Dup)=="A"
		nFaturas := Len(oNF:_InfNfe:_Cobr:_Dup)
	ELSE
		nFaturas := 1
	ENDIF
ELSEIF oFatura<>Nil .AND. type("oNF:_INFNFE:_PAG:_DETPAG:_INDPAG:TEXT") <> "U" .and. oNF:_INFNFE:_PAG:_DETPAG:_INDPAG:TEXT == '0'
	nFaturas 	:= 1
	lFat853		:= .T.
ENDIF

oDet 		:= IIf(ValType(oDet)=="O",{oDet},oDet)

// Popula as variaveis
if(valType(oEntrega)=="O" ) .And. ( valType(oRetirada)=="O") // Entrega e retirada
	
    nAjustaNat   := 4
    nAjustaEnt   := 81
	nAjustaRet   := 162
	nAjustaFat   := 149
	nAjustaImp   := 148
    nAjustaVt    := 147
	nAjustaISSQN := 20
	nAjustaPro   := 0
    nAjustaDad   := 20
    nAjustaDest  := 10
	nMaxItem     := 0

ElseIF( valType(oEntrega)=="O" ) .And. ( valType(oRetirada)=="U") // Entrega

	nAjustaNat   := 4
    nAjustaEnt   := 81
	nAjustaFat   := 68 
    nAjustaImp   := 67
    nAjustaVt    := 67
    nAjustaISSQN := 13
	nAjustaPro   := 67
	nAjustaDad   := 13
	nAjustaDest  := 10 
	nMAXITEM     := 4

ElseIF( valType(oEntrega)=="U" ) .And. ( valType(oRetirada)=="O") // Retirada

	nAjustaNat   := 4
	nAjustaRet   := 81
	nAjustaFat   := 68 
    nAjustaImp   := 67
    nAjustaVt    := 67
    nAjustaISSQN := 13
	nAjustaPro   := 67
	nAjustaDad   := 13
	nAjustaDest  := 10 
	nMAXITEM     := 4

EndIf

If ( valType(oRetirada)=="O" )
	aRetirada := {IIF(Type("oRetirada:_xNome")=="U","",oRetirada:_xNome:Text),;   
    IIF(Type("oRetirada:_CNPJ")=="U","",oRetirada:_CNPJ:Text),;
    IIF(Type("oRetirada:_CPF")=="U","",oRetirada:_CPF:Text),;
    IIF(Type("oRetirada:_xLgr")=="U","",oRetirada:_xLgr:Text),;
    IIF(Type("oRetirada:_nro")=="U","",oRetirada:_nro:Text),;
    IIF(Type("oRetirada:_xCpl")=="U","",oRetirada:_xCpl:Text),;
    IIF(Type("oRetirada:_xBairro")=="U","",oRetirada:_xBairro:Text),;
    IIF(Type("oRetirada:_xMun")=="U","",oRetirada:_xMun:Text),;
    IIF(Type("oRetirada:_UF")=="U","",oRetirada:_UF:Text),;
	IIF(Type("oRetirada:_IE")=="U","",oRetirada:_IE:Text),;
	IIF(Type("oRetirada:_CEP")=="U","",oRetirada:_CEP:Text),;
	IIF(Type("oRetirada:_FONE")=="U","",oRetirada:_Fone:Text),;
	""}
endIf

If ( valType(oEntrega)=="O" )
	aEntrega := {IIF(Type("oEntrega:_xNome")=="U","",oEntrega:_xNome:Text),;   
    IIF(Type("oEntrega:_CNPJ")=="U","",oEntrega:_CNPJ:Text),;
    IIF(Type("oEntrega:_CPF")=="U","",oEntrega:_CPF:Text),;
    IIF(Type("oEntrega:_xLgr")=="U","",oEntrega:_xLgr:Text),;
    IIF(Type("oEntrega:_nro")=="U","",oEntrega:_nro:Text),;
    IIF(Type("oEntrega:_xCpl")=="U","",oEntrega:_xCpl:Text),;
    IIF(Type("oEntrega:_xBairro")=="U","",oEntrega:_xBairro:Text),;
    IIF(Type("oEntrega:_xMun")=="U","",oEntrega:_xMun:Text),;
    IIF(Type("oEntrega:_UF")=="U","",oEntrega:_UF:Text),;
	IIF(Type("oEntrega:_IE")=="U","",oEntrega:_IE:Text),;
	IIF(Type("oEntrega:_CEP")=="U","",oEntrega:_CEP:Text),;
	IIF(Type("oEntrega:_FONE")=="U","",oEntrega:_Fone:Text),;
	""}
endIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Carrega as variaveis de impressao                                       ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aadd(aSitTrib,"00")
aadd(aSitTrib,"02")
aadd(aSitTrib,"10")
aadd(aSitTrib,"15")
aadd(aSitTrib,"20")
aadd(aSitTrib,"30")
aadd(aSitTrib,"40")
aadd(aSitTrib,"41")
aadd(aSitTrib,"50")
aadd(aSitTrib,"51")
aadd(aSitTrib,"53")
aadd(aSitTrib,"60")
aadd(aSitTrib,"61")
aadd(aSitTrib,"70")
aadd(aSitTrib,"90")
aadd(aSitTrib,"PART")

aadd(aSitSN,"101")
aadd(aSitSN,"102")
aadd(aSitSN,"201")
aadd(aSitSN,"202")
aadd(aSitSN,"500")
aadd(aSitSN,"900")
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro Destinatario                                                     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

//Impressao DANFE A4 no PDV NFC-e
if lNFCE .AND. (oDestino == Nil .or. type("oDestino:_EnderDest") == "U")
	oDestino := MontaNfcDest(oDestino)
endif

aDest := {MontaEnd(oDestino:_EnderDest),;
NoChar(oDestino:_EnderDest:_XBairro:Text,lConverte),;
IIF(Type("oDestino:_EnderDest:_Cep")=="U","",Transform(oDestino:_EnderDest:_Cep:Text,"@r 99999-999")),;
IIF(oNF:_INFNFE:_VERSAO:TEXT >= "3.10",IIF(Type("oIdent:_DHSaiEnt")=="U","",oIdent:_DHSaiEnt:Text),IIF(Type("oIdent:_DSaiEnt")=="U","",oIdent:_DSaiEnt:Text)),;
oDestino:_EnderDest:_XMun:Text,;
IIF(Type("oDestino:_EnderDest:_fone")=="U","",oDestino:_EnderDest:_fone:Text),;
oDestino:_EnderDest:_UF:Text,;
IIF(Type("oDestino:_IE")=="U","",oDestino:_IE:Text),;
""}

If oNF:_INFNFE:_VERSAO:TEXT >= "3.10"
	aadd(aHrEnt,IIF(Type("oIdent:_dhSaiEnt")=="U","",SubStr(oIdent:_dhSaiEnt:TEXT,12,8)))
Else
	If Type("oIdent:_DSaiEnt")<>"U" .And. Type("oIdent:_HSaiEnt:Text")<>"U"
		aAdd(aHrEnt,oIdent:_HSaiEnt:Text)
	Else
		aAdd(aHrEnt,"")
	EndIf	
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Calculo do Imposto                                                      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aTotais := {"","","","","","","","","","",""}
aTotais[01] := Transform(Val(oTotal:_ICMSTOT:_vBC:TEXT),		"@e 9,999,999,999,999.99")
aTotais[02] := Transform(Val(oTotal:_ICMSTOT:_vICMS:TEXT),		"@e 999,999,999,999.99")
aTotais[03] := Transform(Val(oTotal:_ICMSTOT:_vBCST:TEXT),		"@e 9,999,999,999,999.99")
aTotais[04] := Transform(Val(oTotal:_ICMSTOT:_vST:TEXT),		"@e 999,999,999,999.99")
aTotais[05] := Transform(Val(oTotal:_ICMSTOT:_vProd:TEXT),		"@e 9,999,999,999,999.99")
aTotais[06] := Transform(Val(oTotal:_ICMSTOT:_vFrete:TEXT),		"@e 999,999,999,999.99")
aTotais[07] := Transform(Val(oTotal:_ICMSTOT:_vSeg:TEXT), 		"@e 999,999,999,999.99")
aTotais[08] := Transform(Val(oTotal:_ICMSTOT:_vDesc:TEXT),		"@e 999,999,999,999.99")
aTotais[09] := Transform(Val(oTotal:_ICMSTOT:_vOutro:TEXT),		"@e 999,999,999,999.99")

If ( MV_PAR04 == 1 )
	dbSelectArea("SF1")
	dbSetOrder(1)
	If MsSeek(xFilial("SF1")+aNota[5]+aNota[4]+aNota[6]+aNota[7]) .And. SF1->(FieldPos("F1_FIMP"))<>0
		If SF1->F1_TIPO <> "D"
		  	aTotais[10] := 	Transform(Val(oTotal:_ICMSTOT:_vIPI:TEXT),"@e 9,999,999,999,999.99")
		ElseIf SF1->F1_TIPO == "D" .and. lEntIpiDev
			aTotais[10] := 	Transform(Val(oTotal:_ICMSTOT:_vIPI:TEXT),"@e 9,999,999,999,999.99")
		Else	
			aTotais[10] := "0,00"
		EndIf        
		MsUnlock()
		DbSkip()
	EndIf
Else
	aTotais[10] := 	Transform(Val(oTotal:_ICMSTOT:_vIPI:TEXT),"@e 9,999,999,999,999.99")
EndIf

aTotais[11] := 	Transform(Val(oTotal:_ICMSTOT:_vNF:TEXT),		"@e 9,999,999,999,999.99")

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Impressão da Base de Calculo e ICMS nos campo Proprios do ICMS quando optante pelo Simples Nacional    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
 
If lImpSimpN   

	nDetImp := Len(oDet)
	nS := nDetImp 
	aSimpNac := {"",""}

	    if Type("oDet["+Alltrim(Str(nS))+"]:_IMPOSTO:_ICMS:_ICMSSN101:_VCREDICMSSN:TEXT") <> "U"
	    	SF3->(dbSetOrder(5))
	
			if SF3->(MsSeek(xFilial("SF3")+aNota[4]+aNota[5]))
				while SF3->(!eof()) .and. ( SF3->F3_SERIE + SF3->F3_NFISCAL  == aNota[4] + aNota[5] )
					nSnBaseIcm += (SF3->F3_BASEICM)
					nSnValIcm  += (SF3->F3_VALICM)
					SF3->(dbSkip())
				end 
		   	endif
		    		    	
	    elseif Type("oDet["+Alltrim(Str(nS))+"]:_IMPOSTO:_ICMS:_ICMSSN900:_VCREDICMSSN:TEXT") <> "U"
			nS:= 0	    
	    	For nS := 1 To nDetImp 
	    		If ValAtrib("oDet["+Alltrim(Str(nS))+"]:_IMPOSTO:_ICMS:_ICMSSN900:_VBC:TEXT") <> "U"
	 				nSnBaseIcm += Val(oDet[nS]:_IMPOSTO:_ICMS:_ICMSSN900:_VBC:TEXT)
				EndIf			
				If ValAtrib("oDet["+Alltrim(Str(nS))+"]:_IMPOSTO:_ICMS:_ICMSSN900:_VCREDICMSSN:TEXT") <> "U"
					nSnValIcm  += Val(oDet[nS]:_IMPOSTO:_ICMS:_ICMSSN900:_VCREDICMSSN:TEXT)
				EndIf
			Next nS
			
	    endif
    	    
	   	aSimpNac[01] := Transform((nSnBaseIcm),"@e 9,999,999,999,999.99")
		aSimpNac[02] := Transform((nSnValIcm),"@e 9,999,999,999,999.99")
    
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro Faturas                                                          ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If nFaturas > 0
	aFaturas := Fatura(oFatura,nFaturas,lFat853)
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro transportadora                                                   ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aTransp := {"","0","","","","","","","","","","","","","",""}

If Type("oTransp:_ModFrete")<>"U"
	aTransp[02] := IIF(Type("oTransp:_ModFrete:TEXT")<>"U",oTransp:_ModFrete:TEXT,"0")
EndIf
If Type("oTransp:_Transporta")<>"U"
	aTransp[01] := IIf(Type("oTransp:_Transporta:_xNome:TEXT")<>"U",NoChar(oTransp:_Transporta:_xNome:TEXT,lConverte),"")
	//	aTransp[02] := IIF(Type("oTransp:_ModFrete:TEXT")<>"U",oTransp:_ModFrete:TEXT,"0")
	aTransp[03] := IIf(Type("oTransp:_VeicTransp:_RNTC")=="U","",oTransp:_VeicTransp:_RNTC:TEXT)
	aTransp[04] := IIf(Type("oTransp:_VeicTransp:_Placa:TEXT")<>"U",oTransp:_VeicTransp:_Placa:TEXT,"")
	aTransp[05] := IIf(Type("oTransp:_VeicTransp:_UF:TEXT")<>"U",oTransp:_VeicTransp:_UF:TEXT,"")
	If Type("oTransp:_Transporta:_CNPJ:TEXT")<>"U"
		aTransp[06] := Transform(oTransp:_Transporta:_CNPJ:TEXT,"@R! NN.NNN.NNN/NNNN-99")
	ElseIf Type("oTransp:_Transporta:_CPF:TEXT")<>"U"
		aTransp[06] := Transform(oTransp:_Transporta:_CPF:TEXT,"@r 999.999.999-99")
	EndIf
	aTransp[07] := IIf(Type("oTransp:_Transporta:_xEnder:TEXT")<>"U",NoChar(oTransp:_Transporta:_xEnder:TEXT,lConverte),"")
	aTransp[08] := IIf(Type("oTransp:_Transporta:_xMun:TEXT")<>"U",oTransp:_Transporta:_xMun:TEXT,"")
	aTransp[09] := IIf(Type("oTransp:_Transporta:_UF:TEXT")<>"U",oTransp:_Transporta:_UF:TEXT,"")
	aTransp[10] := IIf(Type("oTransp:_Transporta:_IE:TEXT")<>"U",oTransp:_Transporta:_IE:TEXT,"")
ElseIf Type("oTransp:_VEICTRANSP")<>"U"
	aTransp[03] := IIf(Type("oTransp:_VeicTransp:_RNTC")=="U","",oTransp:_VeicTransp:_RNTC:TEXT)
	aTransp[04] := IIf(Type("oTransp:_VeicTransp:_Placa:TEXT")<>"U",oTransp:_VeicTransp:_Placa:TEXT,"")
	aTransp[05] := IIf(Type("oTransp:_VeicTransp:_UF:TEXT")<>"U",oTransp:_VeicTransp:_UF:TEXT,"")
EndIf
If Type("oTransp:_Vol")<>"U"
	If ValType(oTransp:_Vol) == "A"
		nX := nPrivate
		cMarca := ""
		aMarca := {}
		cNumeracao := ""
		aNumeracao := {}
		nLenVol := Len(oTransp:_Vol)
		For nX := 1 to nLenVol
			nXAux := nX
			nVolume += IIF(!ValAtrib("oTransp:_Vol[nXAux]:_QVOL:TEXT")=="U",Val(oTransp:_Vol[nXAux]:_QVOL:TEXT),0)
			if !ValAtrib("oTransp:_Vol[nXAux]:_MARCA:TEXT") == "U" .and. !empty(oTransp:_Vol[nXAux]:_MARCA:TEXT)
				if aScan( aMarca, { |X| X == oTransp:_Vol[nXAux]:_MARCA:TEXT}) == 0 
					aAdd( aMarca, oTransp:_Vol[nXAux]:_MARCA:TEXT )
				endif
			endif
			if !ValAtrib("oTransp:_Vol[nXAux]:_nVOL:TEXT") == "U" .and. !empty(oTransp:_Vol[nXAux]:_nVOL:TEXT)
				if aScan( aNumeracao, { |X| X == oTransp:_Vol[nXAux]:_nVOL:TEXT } ) == 0
					aAdd( aNumeracao, oTransp:_Vol[nXAux]:_nVOL:TEXT )
				endif
			endif
		Next nX

		if len(aMarca) == 1
			cMarca := aMarca[1]
		elseif len(aMarca) > 1
			cMarca := "Diversos"
		endif
		aSize(aMarca,0)
		if len(aNumeracao) == 1
			cNumeracao := aNumeracao[1]
		elseif len(aNumeracao) > 1
			cNumeracao := "Diversos"
		endif
		aSize(aNumeracao,0)

		if Type("oTransp:_Vol:_Marca") == "U" 
			cMarca := NoChar(cMarca,lConverte)
		else
			cMarca := NoChar(oTransp:_Vol:_Marca:TEXT,lConverte)
		endif

		if !Type("oTransp:_Vol:_nVol:TEXT") == "U"
			cNumeracao := oTransp:_Vol:_nVol:TEXT
		endif

		aTransp[11]	:= AllTrim(str(nVolume))
		aTransp[12]	:= IIf(Type("oTransp:_Vol:_Esp")=="U","Diversos","")
		aTransp[13] := cMarca
		aTransp[14] := cNumeracao
		If  Type("oTransp:_Vol[1]:_PesoB") <>"U"
			aTransp[15] := alltrim(oTransp:_Vol[1]:_PesoB:TEXT)
		EndIf
		If Type("oTransp:_Vol[1]:_PesoL") <>"U"
			aTransp[16] := alltrim(oTransp:_Vol[1]:_PesoL:TEXT)
		EndIf
	Else
		aTransp[11] := IIf(Type("oTransp:_Vol:_qVol:TEXT")<>"U",oTransp:_Vol:_qVol:TEXT,"")
		aTransp[12] := IIf(Type("oTransp:_Vol:_Esp")=="U","",oTransp:_Vol:_Esp:TEXT)
		aTransp[13] := IIf(Type("oTransp:_Vol:_Marca")=="U","",NoChar(oTransp:_Vol:_Marca:TEXT,lConverte))
		aTransp[14] := IIf(Type("oTransp:_Vol:_nVol:TEXT")<>"U",oTransp:_Vol:_nVol:TEXT,"")
		aTransp[15] := IIf(Type("oTransp:_Vol:_PesoB:TEXT")<>"U",oTransp:_Vol:_PesoB:TEXT,"")
		aTransp[16] := IIf(Type("oTransp:_Vol:_PesoL:TEXT")<>"U",oTransp:_Vol:_PesoL:TEXT,"")
	EndIf
	aTransp[13] := SubStr( aTransp[13], 1, 20)
	aTransp[14] := SubStr( aTransp[14], 1, 20)
	aTransp[15] := strTRan(aTransp[15],".",",")
	aTransp[16] := strTRan(aTransp[16],".",",")
EndIf


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Volumes / Especie Nota de Saida                                         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ 
If(MV_PAR04==2) .And. Empty(aTransp[12])
	If (SF2->(FieldPos("F2_ESPECI1")) <>0 .And. !Empty( SF2->(FieldGet(FieldPos( "F2_ESPECI1" )))  )) .Or.;
	   (SF2->(FieldPos("F2_ESPECI2")) <>0 .And. !Empty( SF2->(FieldGet(FieldPos( "F2_ESPECI2" )))  )) .Or.;
	   (SF2->(FieldPos("F2_ESPECI3")) <>0 .And. !Empty( SF2->(FieldGet(FieldPos( "F2_ESPECI3" )))  )) .Or.; 
	   (SF2->(FieldPos("F2_ESPECI4")) <>0 .And. !Empty( SF2->(FieldGet(FieldPos( "F2_ESPECI4" )))  ))

	   	aEspecie := {}   
		aadd(aEspecie,SF2->F2_ESPECI1)
		aadd(aEspecie,SF2->F2_ESPECI2)
		aadd(aEspecie,SF2->F2_ESPECI3)
		aadd(aEspecie,SF2->F2_ESPECI4)
        
		cEsp := ""
		nx 	 := 0 
		For nE := 1 To Len(aEspecie)
			If !Empty(aEspecie[nE])
				nx ++   
				cEsp := aEspecie[nE]
			EndIf
		Next 
		
		cGuarda := ""
		If nx > 1
			cGuarda := "Diversos"
		Else
			cGuarda := cEsp
		EndIf
		
		If !Empty(cGuarda)
		  	aadd(aEspVol,{cGuarda,Iif(SF2->F2_PLIQUI>0,str(SF2->F2_PLIQUI),""),Iif(SF2->F2_PBRUTO>0, str(SF2->F2_PBRUTO),"")})
		Else
			/*
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ1
			//³Aqui seguindo a mesma regra da criação da TAG de Volumes no xml  ³
			//³ caso não esteja preenchida nenhuma das especies de Volume não se³
			//³ envia as informações de volume.                   				³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ1
			*/
			aadd(aEspVol,{cGuarda,"",""}) 
		Endif 
	Else
		aadd(aEspVol,{cGuarda,"",""})
	EndIf
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Especie Nota de Entrada                                                 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If(MV_PAR04==1) .And. Empty(aTransp[12])   
	dbSelectArea("SF1")
	dbSetOrder(1)
	If MsSeek(xFilial("SF1")+aNota[5]+aNota[4]+aNota[6]+aNota[7])
     
		If (SF1->(FieldPos("F1_ESPECI1")) <>0 .And. !Empty( SF1->(FieldGet(FieldPos( "F1_ESPECI1" )))  )) .Or.;
			(SF1->(FieldPos("F1_ESPECI2")) <>0 .And. !Empty( SF1->(FieldGet(FieldPos( "F1_ESPECI2" )))  )) .Or.;
			(SF1->(FieldPos("F1_ESPECI3")) <>0 .And. !Empty( SF1->(FieldGet(FieldPos( "F1_ESPECI3" )))  )) .Or.;
			(SF1->(FieldPos("F1_ESPECI4")) <>0 .And. !Empty( SF1->(FieldGet(FieldPos( "F1_ESPECI4" )))  ))
			
			aEspecie := {}
			aadd(aEspecie,SF1->F1_ESPECI1)
			aadd(aEspecie,SF1->F1_ESPECI2)
			aadd(aEspecie,SF1->F1_ESPECI3)
			aadd(aEspecie,SF1->F1_ESPECI4)
			
			cEsp := ""
			nx 	 := 0
			For nE := 1 To Len(aEspecie)
				If !Empty(aEspecie[nE])
					nx ++
					cEsp := aEspecie[nE]
				EndIf
			Next
			
			cGuarda := ""
			If nx > 1
				cGuarda := "Diversos"
			Else
				cGuarda := cEsp
			EndIf
			
			If  !Empty(cGuarda)
				aadd(aEspVol,{cGuarda,Iif(SF1->F1_PLIQUI>0,str(SF1->F1_PLIQUI),""),Iif(SF1->F1_PBRUTO>0, str(SF1->F1_PBRUTO),"")})
			Else
				/*
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ1
				//³Aqui seguindo a mesma regra da criação da TAG de Volumes no xml  ³
				//³ caso não esteja preenchida nenhuma das especies de Volume não se³
				//³ envia as informações de volume.                   				³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ1
				*/
				aadd(aEspVol,{cGuarda,"",""})
			Endif
		Else
			aadd(aEspVol,{cGuarda,"",""})
		EndIf
		
		MsUnlock()
		DbSkip()		
	EndIf
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Tipo do frete³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
dbSelectArea("SD2")
dbSetOrder(3)
MsSeek(xFilial("SD2")+SF2->F2_DOC+SF2->F2_SERIE+SF2->F2_CLIENTE+SF2->F2_LOJA)
dbSelectArea("SC5")
dbSetOrder(1)
MsSeek(xFilial("SC5")+SD2->D2_PEDIDO)
dbSelectArea("SF3")
dbSetOrder(4)
MsSeek(xFilial("SF3")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_DOC+SF2->F2_SERIE)

lArt488MG := Iif(SF4->(FIELDPOS("F4_CRLEIT"))>0,Iif(SF4->F4_CRLEIT == "1",.T.,.F.),.F.)
lArt274SP := Iif(SF4->(FIELDPOS("F4_ART274"))>0,Iif(SF4->F4_ART274 $ "1S",.T.,.F.),.F.) 

If Type("oTransp:_ModFrete") <> "U"
	cModFrete := oTransp:_ModFrete:TEXT
Else
	cModFrete := "1"
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro Dados do Produto / Serviço                                       ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nLenDet := Len(oDet)
If lMv_ItDesc
	For nX := 1 To nLenDet
		Aadd(aIndAux, {nX, SubStr(NoChar(oDet[nX]:_Prod:_xProd:TEXT,lConverte),1,MAXITEMC)})
	Next
	
	aIndAux := aSort(aIndAux,,, { |x, y| x[2] < y[2] })
	
	For nX := 1 To nLenDet
		Aadd(aIndImp, aIndAux[nX][1] )
	Next
EndIf

dbSelectArea("SB5")
aAreaSB5 := SB5->( getArea() )
SB5->( dbSetOrder(1) )
nTamB5Cod := GetSX3Cache( "B5_COD", "X3_TAMANHO" )

dbSelectArea("DY3")
aAreaDY3 := DY3->( getArea() )
DY3->( dbSetOrder(1) )

For nZ := 1 To nLenDet
	If lMv_ItDesc
		nX := aIndImp[nZ]
	Else
		nX := nZ
	EndIf
	nPrivate := nX

    If lArt488MG .And. lUf_MG
        nVTotal  := 0
        nVUnit   := 0 
    Else
	    nVTotal  := Val(oDet[nX]:_Prod:_vProd:TEXT)//-Val(IIF(Type("oDet[nPrivate]:_Prod:_vDesc")=="U","",oDet[nX]:_Prod:_vDesc:TEXT))
	    nVUnit   := Val(oDet[nX]:_Prod:_vUnCom:TEXT)
	EndIf
	nQtd     := Val(oDet[nX]:_Prod:_qCom:TEXT)

	If ValAtrib("oDet[nPrivate]:_Prod:_vDesc:TEXT")<>"U"
		nDesc := Val( oDet[nX]:_Prod:_vDesc:TEXT )
	Else
		nDesc := 0
	EndIf
    
//	nPerDesc	:= ((nDesc*100)/nVTotal)
	nVUniLiq	:= nVUnit-(nDesc/nQtd)
	nVTotLiq	:= nVTotal-nDesc

	nBaseICM	:= 0
	nValICM  	:= 0
	nBaseICMST	:= 0
	nValICMST	:= 0
	nValIPI  	:= 0
	nPICM    	:= 0
	nPIPI    	:= 0
	oImposto 	:= oDet[nX]                
	cSitTrib 	:= ""
	lPontilhado	:= .F.	
	If ValAtrib("oImposto:_Imposto")<>"U"
		If ValAtrib("oImposto:_Imposto:_ICMS")<>"U"
			nLenSit := Len(aSitTrib)
			For nY := 1 To nLenSit
				nPrivate2 := nY
				If ValAtrib("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nPrivate2])<>"U" .OR. ValAtrib("oImposto:_Imposto:_ICMS:_ICMSST")<>"U" 
					If ValAtrib("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nPrivate2]+":_VBC:TEXT")<>"U"
						nBaseICM := Val(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_VBC:TEXT"))
						nValICM  := Val(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_vICMS:TEXT"))
						nPICM    := Val(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_PICMS:TEXT")) 
					ElseIf ValAtrib("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nPrivate2]+":_MOTDESICMS") <> "U" .And. ValAtrib("oImposto:_PROD:_VDESC:TEXT") <> "U"   //SINIEF 25/12, efeitos a partir de 20.12.12 
						If !(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_CST:TEXT") $"40-41")
							If AllTrim(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_motDesICMS:TEXT")) == "7" .And. &("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_CST:TEXT") == "30"
								nValICM  := 0
							Else
								nValICM  := Val(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_vICMSDESON:TEXT"))
							EndIf
					    EndIf
					EndIf
					If ValAtrib("oImposto:_Imposto:_ICMS:_ICMSST")<>"U" // Tratamento para 4.0
						cSitTrib := &("oImposto:_Imposto:_ICMS:_ICMSST:_ORIG:TEXT") 
						cSitTrib += &("oImposto:_Imposto:_ICMS:_ICMSST:_CST:TEXT")					
					Else 
						cSitTrib := &("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_ORIG:TEXT") 
						cSitTrib += &("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_CST:TEXT")
					EndIf
					If ValAtrib("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nPrivate2]+":_VBCST:TEXT")<>"U" .And. ValAtrib("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nPrivate2]+":_vICMSST:TEXT")<>"U"
						nBaseICMST := Val(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_VBCST:TEXT"))
						nValICMST  := Val(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_vICMSST:TEXT"))
					EndIf
				EndIf												
			Next nY			
		
			//Tratamento para o ICMS para optantes pelo Simples Nacional
			If ValAtrib("oEmitente:_CRT") <> "U" .And. oEmitente:_CRT:TEXT == "1"
				nLenSit := Len(aSitSN)
				For nY := 1 To nLenSit
					nPrivate2 := nY
					If ValAtrib("oImposto:_Imposto:_ICMS:_ICMSSN"+aSitSN[nPrivate2])<>"U"
						If ValAtrib("oImposto:_Imposto:_ICMS:_ICMSSN"+aSitSN[nPrivate2]+":_VBC:TEXT")<>"U"
							nBaseICM := Val(&("oImposto:_Imposto:_ICMS:_ICMSSN"+aSitSN[nY]+":_VBC:TEXT"))
							nValICM  := Val(&("oImposto:_Imposto:_ICMS:_ICMSSN"+aSitSN[nY]+":_vICMS:TEXT"))
							nPICM    := Val(&("oImposto:_Imposto:_ICMS:_ICMSSN"+aSitSN[nY]+":_PICMS:TEXT"))                   
						EndIf
						cSitTrib := &("oImposto:_Imposto:_ICMS:_ICMSSN"+aSitSN[nY]+":_ORIG:TEXT")
						cSitTrib += &("oImposto:_Imposto:_ICMS:_ICMSSN"+aSitSN[nY]+":_CSOSN:TEXT")				
					EndIf
				Next nY	
			EndIf
		EndIf
		If ValAtrib("oImposto:_Imposto:_IPI")<>"U"
			If ValAtrib("oImposto:_Imposto:_IPI:_IPITrib:_vIPI:TEXT")<>"U"
				nValIPI := Val(oImposto:_Imposto:_IPI:_IPITrib:_vIPI:TEXT)
			EndIf
			If ValAtrib("oImposto:_Imposto:_IPI:_IPITrib:_pIPI:TEXT")<>"U"
				nPIPI   := Val(oImposto:_Imposto:_IPI:_IPITrib:_pIPI:TEXT)
			EndIf
		EndIf
	EndIf
    
	nMaxCod := MaxCod(oDet[nX]:_Prod:_cProd:TEXT, MAXCODPRD)

	cCodOnu := ""
	if lSpedCodOnu
		if SB5->( DbSeek( xFilial( "SB5" ) + padr( oDet[nX]:_Prod:_cProd:TEXT, nTamB5Cod ) ) )
			cUnidMed 	:= oDet[nX]:_Prod:_uTrib:TEXT
			nPesoBruto	:= posicione("SB1",1,xFilial("SB1")+SB5->B5_COD,"B1_PESBRU")
			cMensONU	:= "" //se deve preencher as informações de rodape do DANFE
			cCodOnu		:= SpedCodOnu(SB5->B5_ONU, SB5->B5_ITEM, nQtd, cUnidMed ,nPesoBruto, @cMensONU)
			if !empty(cMensONU)
				aAdd(aMensONU, noAcento('  ' + cMensONU))
			endIf
		endIf
	
	else
		//modelo antigo apenas para compatibilidade - sem manutenção
		If (nPosOnu := ascan( aCodONU, { |x| x[1] == oDet[nX]:_Prod:_cProd:TEXT } ) ) == 0
			if SB5->( DbSeek( xFilial( "SB5" ) + padr( oDet[nX]:_Prod:_cProd:TEXT, nTamB5Cod ) ) )
				If DY3->( DbSeek(xFilial("DY3")+ SB5->B5_ONU) )
					cCodOnu := 'ONU ' + Alltrim(DY3->DY3_ONU) + ' ' + Alltrim(DY3->DY3_DESCRI)
					If !Empty(DY3->DY3_DESCRI) .and. (DY3->DY3_INFCPL =="S" .OR. DY3->DY3_INFCPL =="1")
						aAdd( aMensONU, noAcento( '  ' + cCodOnu + '   ' ))
					EndIF  		
				EndIF
				Aadd( aCodONU, { oDet[nX]:_Prod:_cProd:TEXT , SB5->B5_ONU, cCodOnu }  )
			endIf
		else
			cCodOnu := aCodONU[nPosOnu,3]
		endIf
	endIf
	cCodOnu := iIf(lImpInfAd,cCodOnu,"")
	cAuxOnu := cCodOnu

	//Tratativa para que COD Onu seja impresso antes de produto.
	lInfAdProd := (ValAtrib("oNf:_infnfe:_det[nPrivate]:_Infadprod:TEXT") <> "U" .Or. ValAtrib("oNf:_infnfe:_det:_Infadprod:TEXT") <> "U") .And. ( lImpAnfav .Or. lImpInfAd )	

	If lInfAdProd
		If nX == 1
			aadd(aItens,{;
				"-",;
				{"-",.F.},;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-"; 
			})
		EndIf
		While !Empty(cCodonu)
			aadd(aItens,{;
				"",;
				{SubStr(cCodOnu,1,nMaxDes), .T.},;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"";
			})
			If lUf_MG
				aadd(aItensAux,{;
					"",;
					{SubStr(cCodOnu,1,nMaxDes), .T.},;
					"",;
					"",;
					oDet[nX]:_Prod:_CFOP:TEXT,;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					StrZero( ++nSequencia, 4 ),;
					0;
				})
			Endif
			cCodOnu := SubStr(cCodOnu,(nMaxDes + 1))
		EndDo
	EndIf

	// Tratamento para quebrar os digitos dos valores
	aAux := {}
	AADD(aAux, AllTrim(TransForm(nQtd,TM(nQtd,15,4))))
	AADD(aAux, AllTrim(TransForm(nVUnit,TM(nVUnit,TamSX3("D2_PRCVEN")[1],TamSX3("D2_PRCVEN")[2]))))
	AADD(aAux, AllTrim(TransForm(nVTotal,TM(nVTotal,TamSX3("D2_TOTAL")[1],TamSX3("D2_TOTAL")[2]))))
	AADD(aAux, AllTrim(TransForm(nDesc,TM(nDesc,TamSX3("D2_DESCON")[1],TamSX3("D2_DESCON")[2]))))
	AADD(aAux, AllTrim(TransForm(nVUniLiq,TM(nVUniLiq,TamSX3("D2_PRCVEN")[1],4))))
	AADD(aAux, AllTrim(TransForm(nVTotLiq,TM(nVTotLiq,TamSX3("D2_TOTAL")[1],TamSX3("D2_TOTAL")[2]))))
	AADD(aAux, AllTrim(TransForm(nBaseICM,TM(nBaseICM,TamSX3("D2_BASEICM")[1],TamSX3("D2_BASEICM")[2]))))
	AADD(aAux, AllTrim(TransForm(nBaseICMST,TM(nBaseICMST,TamSX3("D2_BASEICM")[1],TamSX3("D2_BASEICM")[2]))))
	AADD(aAux, AllTrim(TransForm(nValICM,TM(nValICM,TamSX3("D2_VALICM")[1],TamSX3("D2_VALICM")[2]))))
	AADD(aAux, AllTrim(TransForm(nValICMST,TM(nValICMST,TamSX3("D2_VALICM")[1],TamSX3("D2_VALICM")[2]))))
	AADD(aAux, AllTrim(TransForm(nValIPI,TM(nValIPI,TamSX3("D2_VALIPI")[1],TamSX3("D2_BASEIPI")[2]))))
	
	aadd(aItens,{;
		SubStr(oDet[nX]:_Prod:_cProd:TEXT,1,nMaxCod),;
		{SubStr(NoChar(oDet[nX]:_Prod:_xProd:TEXT,lConverte),1,nMaxDes),.F.},;
		IIF(ValAtrib("oDet[nPrivate]:_Prod:_NCM")=="U","",oDet[nX]:_Prod:_NCM:TEXT),;
		cSitTrib,;
		oDet[nX]:_Prod:_CFOP:TEXT,;
		SubStr(oDet[nX]:_Prod:_uCom:TEXT,1,nMaxUn),;
		SubStr(aAux[1], 1, PosQuebrVal(aAux[1])),;
		SubStr(aAux[2], 1, PosQuebrVal(aAux[2])),;
		SubStr(aAux[3], 1, PosQuebrVal(aAux[3])),;
		SubStr(aAux[4], 1, PosQuebrVal(aAux[4])),;
		SubStr(aAux[5], 1, PosQuebrVal(aAux[5])),;
		SubStr(aAux[6], 1, PosQuebrVal(aAux[6])),;
		SubStr(aAux[7], 1, PosQuebrVal(aAux[7])),;
		SubStr(aAux[8], 1, PosQuebrVal(aAux[8])),;
		SubStr(aAux[9], 1, PosQuebrVal(aAux[9])),;
		SubStr(aAux[10], 1, PosQuebrVal(aAux[10])),;
		SubStr(aAux[11], 1, PosQuebrVal(aAux[11])),;
		AllTrim(TransForm(nPICM,"@r 99.99%")),;
		AllTrim(TransForm(nPIPI,"@r 99.99%"));
	})

	If lUf_MG
		aadd(aItensAux,{;
			SubStr(oDet[nX]:_Prod:_cProd:TEXT,1,nMaxCod),;
			{SubStr(NoChar(oDet[nX]:_Prod:_xProd:TEXT,lConverte),1,nMaxDes),.F.},;
			IIF(ValAtrib("oDet[nPrivate]:_Prod:_NCM")=="U","",oDet[nX]:_Prod:_NCM:TEXT),;
			cSitTrib,;
			oDet[nX]:_Prod:_CFOP:TEXT,;
			SubStr(oDet[nX]:_Prod:_uCom:TEXT,1,nMaxUn),;
			SubStr(aAux[1], 1, PosQuebrVal(aAux[1])),;
			SubStr(aAux[2], 1, PosQuebrVal(aAux[2])),;
			SubStr(aAux[3], 1, PosQuebrVal(aAux[3])),;
			SubStr(aAux[4], 1, PosQuebrVal(aAux[4])),;
			SubStr(aAux[5], 1, PosQuebrVal(aAux[5])),;
			SubStr(aAux[6], 1, PosQuebrVal(aAux[6])),;
			SubStr(aAux[7], 1, PosQuebrVal(aAux[7])),;
			SubStr(aAux[8], 1, PosQuebrVal(aAux[8])),;
			SubStr(aAux[9], 1, PosQuebrVal(aAux[9])),;
			SubStr(aAux[10], 1, PosQuebrVal(aAux[10])),;
			SubStr(aAux[11], 1, PosQuebrVal(aAux[11])),;
			AllTrim(TransForm(nPICM,"@r 99.99%")),;
			AllTrim(TransForm(nPIPI,"@r 99.99%")),;
			StrZero( ++nSequencia, 4 ),;
			nVTotal;
		})
	Endif

	/*------------------------------------------------------------
		Tratativa para caso haja quebra de linha em algum quadro do item atual
		 a impressao finalize na linha seguinte, antes de iniciar a impressao dos próx. itens.
	------------------------------------------------------------*/
	cAuxItem := AllTrim(SubStr(oDet[nX]:_Prod:_cProd:TEXT,nMaxCod+1))
	cAux     := AllTrim(SubStr(NoChar(oDet[nX]:_Prod:_xProd:TEXT,lConverte),(nMaxDes + 1)))	
	cAuxUn	 := AllTrim(SubStr(oDet[nX]:_Prod:_uCom:TEXT,nMaxUn+1))
	aAux[1]  := SubStr(aAux[1], PosQuebrVal(aAux[1]) + 1)
	aAux[2]  := SubStr(aAux[2], PosQuebrVal(aAux[2]) + 1)
	aAux[3]  := SubStr(aAux[3], PosQuebrVal(aAux[3]) + 1)
	aAux[4]  := SubStr(aAux[4], PosQuebrVal(aAux[4]) + 1)
	aAux[5]  := SubStr(aAux[5], PosQuebrVal(aAux[5]) + 1)
	aAux[6]  := SubStr(aAux[6], PosQuebrVal(aAux[6]) + 1)
	aAux[7]  := SubStr(aAux[7], PosQuebrVal(aAux[7]) + 1)
	aAux[8]  := SubStr(aAux[8], PosQuebrVal(aAux[8]) + 1)
	aAux[9]  := SubStr(aAux[9], PosQuebrVal(aAux[9]) + 1)
	aAux[10] := SubStr(aAux[10], PosQuebrVal(aAux[10]) + 1)
	aAux[11] := SubStr(aAux[11], PosQuebrVal(aAux[11]) + 1)
	
	While !Empty(cAux) .Or. !Empty(cAuxItem) .Or. !Empty(aAux[1]) .Or. !Empty(aAux[2]) .Or. !Empty(aAux[3]) .Or. !Empty(aAux[4]);
	       .Or. !Empty(aAux[5]) .Or. !Empty(aAux[6]) .Or. !Empty(aAux[7]) .Or. !Empty(aAux[8]) .Or. !Empty(aAux[9]) .Or. !Empty(aAux[10]);
	       .Or. !Empty(aAux[11]) .or. !empty(cAuxUn)
		nMaxCod := MaxCod(cAuxItem, MAXCODPRD)
		
		aadd(aItens,{;
			SubStr(cAuxItem,1,nMaxCod),;
			{SubStr(cAux,1,nMaxDes),.F.},;
			"",;
			"",;
			"",;
			Substr(cAuxUn,1,nMaxUn),;
			SubStr(aAux[1], 1, PosQuebrVal(aAux[1])),;
			SubStr(aAux[2], 1, PosQuebrVal(aAux[2])),;
			SubStr(aAux[3], 1, PosQuebrVal(aAux[3])),;
			SubStr(aAux[4], 1, PosQuebrVal(aAux[4])),;
			SubStr(aAux[5], 1, PosQuebrVal(aAux[5])),;
			SubStr(aAux[6], 1, PosQuebrVal(aAux[6])),;
			SubStr(aAux[7], 1, PosQuebrVal(aAux[7])),;
			SubStr(aAux[8], 1, PosQuebrVal(aAux[8])),;
			SubStr(aAux[9], 1, PosQuebrVal(aAux[9])),;
			SubStr(aAux[10], 1, PosQuebrVal(aAux[10])),;
			SubStr(aAux[11], 1, PosQuebrVal(aAux[11])),;		
			"",;
			"";
		})

		If lUf_MG
			aadd(aItensAux,{;
				SubStr(cAuxItem,1,nMaxCod),;
				{SubStr(cAux,1,nMaxDes),.F.},;
				"",;
				"",;
				oDet[nX]:_Prod:_CFOP:TEXT,;
				Substr(cAuxUn,1,nMaxUn),;
				SubStr(aAux[1], 1, PosQuebrVal(aAux[1])),;
				SubStr(aAux[2], 1, PosQuebrVal(aAux[2])),;
				SubStr(aAux[3], 1, PosQuebrVal(aAux[3])),;
				SubStr(aAux[4], 1, PosQuebrVal(aAux[4])),;
				SubStr(aAux[5], 1, PosQuebrVal(aAux[5])),;
				SubStr(aAux[6], 1, PosQuebrVal(aAux[6])),;
				SubStr(aAux[7], 1, PosQuebrVal(aAux[7])),;
				SubStr(aAux[8], 1, PosQuebrVal(aAux[8])),;
				SubStr(aAux[9], 1, PosQuebrVal(aAux[9])),;
				SubStr(aAux[10], 1, PosQuebrVal(aAux[10])),;
				SubStr(aAux[11], 1, PosQuebrVal(aAux[11])),;		
				"",;
				"",;
				StrZero( ++nSequencia, 4 ),;
				0;
			})
		Endif
		
		cAux        := SubStr(cAux,(nMaxDes + 1)) 
		cAuxItem    := SubStr(cAuxItem,nMaxCod+1)
		cAuxUn 		:= Alltrim(Substr(cAuxUn,nMaxUn+1))
		aAux[1]     := SubStr(aAux[1], PosQuebrVal(aAux[1]) + 1)
		aAux[2]     := SubStr(aAux[2], PosQuebrVal(aAux[2]) + 1)
		aAux[3]     := SubStr(aAux[3], PosQuebrVal(aAux[3]) + 1)
		aAux[4]     := SubStr(aAux[4], PosQuebrVal(aAux[4]) + 1)
		aAux[5]     := SubStr(aAux[5], PosQuebrVal(aAux[5]) + 1)
		aAux[6]     := SubStr(aAux[6], PosQuebrVal(aAux[6]) + 1)
		aAux[7]     := SubStr(aAux[7], PosQuebrVal(aAux[7]) + 1)
		aAux[8]     := SubStr(aAux[8], PosQuebrVal(aAux[8]) + 1)
		aAux[9]     := SubStr(aAux[9], PosQuebrVal(aAux[9]) + 1)
		aAux[10]    := SubStr(aAux[10], PosQuebrVal(aAux[10]) + 1)
		aAux[11]    := SubStr(aAux[11], PosQuebrVal(aAux[11]) + 1)
	    lPontilhado := .T.	
	    
	EndDo

	// Tramento quando houver diferença entre as unidades uCom e uTrib ( SEFAZ MT )
	If ( oDet[nX]:_Prod:_uTrib:TEXT <> oDet[nX]:_Prod:_uCom:TEXT )

	    lPontilhado := IIf( nLenDet > 1, .T., lPontilhado )
    	
		cUnTrib		:= substr(oDet[nX]:_Prod:_uTrib:TEXT,1,nMaxUn)
		nQtdTrib	:= Val(oDet[nX]:_Prod:_qTrib:TEXT)
	   	nVUnitTrib	:= Val(oDet[nX]:_Prod:_vUnTrib:TEXT)

		aAuxCom := {}
		AADD(aAuxCom, AllTrim(TransForm(nQtdTrib,TM(nQtdTrib,15,4))))
		AADD(aAuxCom, AllTrim(TransForm(nVUnitTrib,TM(nVUnitTrib,TamSX3("D2_PRCVEN")[1],TamSX3("D2_PRCVEN")[2]))))
   	
		If lUf_MG
			aadd(aItensAux,{;
				"",;
				{"",.F.},;
				"",;
				"",;
				oDet[nX]:_Prod:_CFOP:TEXT,;
				cUnTrib,;
				SubStr(aAuxCom[1], 1, PosQuebrVal(aAuxCom[1])),;
				SubStr(aAuxCom[2], 1, PosQuebrVal(aAuxCom[2])),;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				StrZero( ++nSequencia, 4 ),;
				0;
			})			
		Else
			aadd(aItens,{;
				"",;
				{"",.F.},;
				"",;
				"",;
				"",;
				cUnTrib,;
				SubStr(aAuxCom[1], 1, PosQuebrVal(aAuxCom[1])),;
				SubStr(aAuxCom[2], 1, PosQuebrVal(aAuxCom[2])),;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;									
				"",;
				"";
			})
		EndIf
		aAuxCom[1]  := SubStr(aAuxCom[1], PosQuebrVal(aAuxCom[1]) + 1) // Quantidade - D2_QUANT
		aAuxCom[2]  := SubStr(aAuxCom[2], PosQuebrVal(aAuxCom[2]) + 1) // Valor Unitario - D2_PRCVEN
		cAuxUn := AllTrim(SubStr(oDet[nX]:_Prod:_uTrib:TEXT,nMaxUn+1))
		/*------------------------------------------------------------
			Quebra de linha para os quadros "Quant." e "V.unitário" 
				da 2a. unidade de medida
		------------------------------------------------------------*/
		While !Empty(aAuxCom[1]) .or. !Empty(aAuxCom[2]).or. !empty(cAuxUn)
			If lUf_MG
				aadd(aItensAux,{;
					"",;
					{"",.F.},;
					"",;
					"",;
					oDet[nX]:_Prod:_CFOP:TEXT,;
					Substr(cAuxUn,1,nMaxUn),;
					SubStr(aAuxCom[1], 1, PosQuebrVal(aAuxCom[1])),;
					SubStr(aAuxCom[2], 1, PosQuebrVal(aAuxCom[2])),;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					StrZero( ++nSequencia, 4 ),;
					0;
				})
			endif
			aadd(aItens,{;
				"",;
				{"",.F.},;
				"",;
				"",;
				"",;
				Substr(cAuxUn,1,nMaxUn),;
				SubStr(aAuxCom[1], 1, PosQuebrVal(aAuxCom[1])),;
				SubStr(aAuxCom[2], 1, PosQuebrVal(aAuxCom[2])),;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;									
				"",;
				"";
			})
			aAuxCom[1]  := SubStr(aAuxCom[1], PosQuebrVal(aAuxCom[1]) + 1) // Quantidade - D2_QUANT
			aAuxCom[2]  := SubStr(aAuxCom[2], PosQuebrVal(aAuxCom[2]) + 1) // Valor Unitario - D2_PRCVEN
			cAuxUn		:= AllTrim(SubStr(cAuxUn,nMaxUn+1))	
		EndDo
	Endif

	If lInfAdProd
		cCodOnu := cAuxOnu
		If at("<", AllTrim(SubStr(oDet[nX]:_Infadprod:TEXT,1))) <> 0
			cAux := stripTags(AllTrim(SubStr(oDet[nX]:_Infadprod:TEXT,1)), .T.) + " "
			cAux += stripTags(AllTrim(SubStr(oDet[nX]:_Infadprod:TEXT,1)), .F.)
		else
			cAux := stripTags(AllTrim(SubStr(oDet[nX]:_Infadprod:TEXT,1)), .T.)
		endIf
		
		// Retira Cód. Onu de cAux para que nao seja impresso duas vezes
		If AllTrim(cCodOnu) $ cAux
			cAux := StrTran(cAux, AllTrim(cCodOnu), "")
		EndIf

		While !Empty(cAux)
			aadd(aItens,{;
				"",;
				{SubStr(cAux, 1, nMaxDes),.F.},;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"";
			})
			If lUf_MG
				aadd(aItensAux,{;
					"",;
					{SubStr(cAux, 1, nMaxDes),.F.},;
					"",;
					"",;
					oDet[nX]:_Prod:_CFOP:TEXT,;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					StrZero( ++nSequencia, 4 ),;
					0;
				})
			Endif
			cAux 		:= SubStr(cAux,(nMaxDes + 1))
			lPontilhado := .T.	
		EndDo
	EndIf

	If (lPontilhado .Or. !Empty(cAuxOnu)) .and. nZ < nLenDet
		aadd(aItens,{;
			"-",;
			{"-",.F.},;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-",;
			"-"; 
		})
		If lUf_MG
			aadd(aItensAux,{;
				"-",;
				{"-",.F.},;
				"-",;
				"-",;
				oDet[nX]:_Prod:_CFOP:TEXT,;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",;
				"-",; 
				StrZero( ++nSequencia, 4 ),;
				0;
			})		
		Endif
	EndIf

Next nZ

restArea( aAreaSB5 )
restArea( aAreaDY3 )

//----------------------------------------------------------------------------------
// Tratamento somente para o estado de MG, para totalizar por CFOP conforme RICMS-MG
//----------------------------------------------------------------------------------
If lUf_MG  

	If 	Len( aItensAux ) > 0

		aItensAux	:= aSort( aItensAux,,, { |x,y| x[5]+x[20] < y[5]+y[20] } )

		nSubTotal	:= 0

		aItens		:= {}
	  
		cCfop		:= aItensAux[1,5]
		cCfopAnt	:= aItensAux[1,5]			
		
		For nX := 1 To Len( aItensAux )

			aArray		:= ARRAY(19)
			
			aArray[01]	:= aItensAux[nX,01]
			aArray[02]	:= aItensAux[nX,02]
			aArray[03]	:= aItensAux[nX,03]
			aArray[04]	:= aItensAux[nX,04]
			
			If Empty( aItensAux[nX,03] ) .Or. aItensAux[nX,03] == "-"
				aArray[05] := ""
			Else
				aArray[05] := aItensAux[nX,05]
			Endif

			aArray[06]	:= aItensAux[nX,06]
			aArray[07]	:= aItensAux[nX,07]
			aArray[08]	:= aItensAux[nX,08]
			aArray[09]	:= aItensAux[nX,09]
			aArray[10]	:= aItensAux[nX,10]
			aArray[11]	:= aItensAux[nX,11]
			aArray[12]	:= aItensAux[nX,12]
			aArray[13]	:= aItensAux[nX,13]
			aArray[14]	:= aItensAux[nX,14]
			aArray[15]	:= aItensAux[nX,15]
			aArray[16]	:= aItensAux[nX,16]
			aArray[17]	:= aItensAux[nX,17]
			aArray[18]	:= aItensAux[nX,18]
			aArray[19]	:= aItensAux[nX,19]

			If aItensAux[nX,5] == cCfop

				aadd( aItens, {; 
					aArray[01],;
					aArray[02],;
					aArray[03],;
					aArray[04],;
					aArray[05],;
					aArray[06],;
					aArray[07],;
					aArray[08],;
					aArray[09],;
					aArray[10],;
					aArray[11],;
					aArray[12],;
					aArray[13],;
					aArray[14],;
					aArray[15],;
					aArray[16],;
					aArray[17],;
					aArray[18],;
					aArray[19];
				} )

				nSubTotal += aItensAux[nX,21]

			Else
				
				aadd(aItens,{;
					"",;
					{"SUB-TOTAL",.F.},;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					AllTrim(TransForm(nSubTotal,TM(nSubTotal,TamSX3("D2_TOTAL")[1],TamSX3("D2_TOTAL")[2]))),;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"";
				})

				aadd(aItens,{;
					"",;
					{"",.F.},;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"",;
					"";
				})
				
				cCfop 		:= aItensAux[nX,05]
				nSubTotal 	:= aItensAux[nX,21]

				aadd( aItens, {; 
					aArray[01],;
					aArray[02],;
					aArray[03],;
					aArray[04],;
					aArray[05],;
					aArray[06],;
					aArray[07],;
					aArray[08],;
					aArray[09],;
					aArray[10],;
					aArray[11],;
					aArray[12],;
					aArray[13],;
					aArray[14],;
					aArray[15],;
					aArray[16],;
					aArray[17],;
					aArray[18],;
					aArray[19];
				} )

			Endif
			
		Next nX
		
		If cCfopAnt <> cCfop .And. nSubTotal > 0

			aadd(aItens,{;
				"",;
				{"SUB-TOTAL",.F.},;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				AllTrim(TransForm(nSubTotal,TM(nSubTotal,TamSX3("D2_TOTAL")[1],TamSX3("D2_TOTAL")[2]))),;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"",;
				"";
			})		
		
		Endif
		
	Endif
	
Endif

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro ISSQN                                                            ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aISSQN := {"","","",""}
If Type("oEmitente:_IM:TEXT")<>"U"
	aISSQN[1] := oEmitente:_IM:TEXT
EndIf
If Type("oTotal:_ISSQNtot")<>"U"
	aISSQN[2] := Transform(Val(oTotal:_ISSQNtot:_vServ:TEXT),"@e 999,999,999.99")
	aISSQN[3] := Transform(Val(oTotal:_ISSQNtot:_vBC:TEXT),"@e 999,999,999.99")
	If Type("oTotal:_ISSQNtot:_vISS:TEXT") <> "U"
		aISSQN[4] := Transform(Val(oTotal:_ISSQNtot:_vISS:TEXT),"@e 999,999,999.99")
	EndIf
EndIf

If Type("oIdent:_DHCONT:TEXT")<>"U"
	cDhCont:= oIdent:_DHCONT:TEXT
EndIf
If Type("oIdent:_XJUST:TEXT")<>"U"
	cXJust:=oIdent:_XJUST:TEXT
EndIf
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro de informacoes complementares                                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aMensagem := {}
If Type("oIdent:_tpAmb:TEXT")<>"U" .And. oIdent:_tpAmb:TEXT=="2"
	cAux := "DANFE emitida no ambiente de homologação - SEM VALOR FISCAL"
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
EndIf 

If Type("oNF:_InfNfe:_infAdic:_infAdFisco:TEXT")<>"U"
	cAux := oNF:_InfNfe:_infAdic:_infAdFisco:TEXT
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
EndIf

If !Empty(cCodAutSef) .AND. oIdent:_tpEmis:TEXT<>"4"
	cAux := "Protocolo: "+cCodAutSef
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
ElseIf !Empty(cCodAutSef) .AND. oIdent:_tpEmis:TEXT=="4" .AND. cModalidade $ "1"
	cAux := "Protocolo: "+cCodAutSef
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
	cAux := "DANFE emitida anteriormente em contingência DPEC"
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
EndIf

If !Empty(cCodAutDPEC) .And. oIdent:_tpEmis:TEXT=="4"
	cAux := "Número de Registro DPEC: "+cCodAutDPEC
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
EndIf

If (Type("oIdent:_tpEmis:TEXT")<>"U" .And. !oIdent:_tpEmis:TEXT$"1,4")
	cAux := "DANFE emitida em contingência"
	If !Empty(cXJust) .and. !Empty(cDhCont) .and. oIdent:_tpEmis:TEXT$"6,7"// SVC-AN e SVC-RS Deve ser impresso o xjust e dhcont
		cAux += " Motivo da adoção da contingência: "+cXJust+ " Data e hora de início de utilização: "+cDhCont
	EndIf
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
ElseIf (!Empty(cModalidade) .And. !cModalidade $ "1,4,5") .And. Empty(cCodAutSef)
	cAux := "DANFE emitida em contingência devido a problemas técnicos - será necessária a substituição."
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
ElseIf (!Empty(cModalidade) .And. cModalidade $ "5" .And. oIdent:_tpEmis:TEXT=="4")
	cAux := "DANFE impresso em contingência"
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
	cAux := "DPEC regularmento recebido pela Receita Federal do Brasil."
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
ElseIf (Type("oIdent:_tpEmis:TEXT")<>"U" .And. oIdent:_tpEmis:TEXT$"5")
	cAux := "DANFE emitida em contingência FS-DA"
	While !Empty(cAux)
		aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
EndIf

If Type("oNF:_InfNfe:_infAdic:_infCpl:TEXT")<>"U"
	If at("<", oNF:_InfNfe:_infAdic:_InfCpl:TEXT) <> 0
		cAux := stripTags(oNF:_InfNfe:_infAdic:_InfCpl:TEXT, .T.) + " "
		cAux += stripTags(oNF:_InfNfe:_infAdic:_InfCpl:TEXT, .F.)
	else
		cAux := stripTags(oNF:_InfNfe:_infAdic:_InfCpl:TEXT, .T.)
	endIf

	if !Empty(cAux) .and. len( aMensONU ) > 0
		for nMsg := 1 to len(aMensONU)
			cMensONU := alltrim( aMensONU[nMsg] )
			if cMensONU $ cAux
				if lSpedCodOnu
					nPosIni 	:= at(cMensONU,cAux)
					nPosFin 	:= nPosIni + len(cMensONU)
					cAux 		:= allTrim(subStr(cAux,1,nPosIni-1)) + " " + allTrim(subStr(cAux,nPosFin)) //Remove somente a ocorrencia da mensagem
				else
					cAux := strTran(cAux, cMensONU, "")
				endIf
				cMensONU	:= alltrim( cMensONU )
				while !empty(cMensONU)
					aadd(aMensagem, { SubStr(cMensONU,1,IIf(EspacoAt(cMensONU, MAXMENLIN) > 1, EspacoAt(cMensONU, MAXMENLIN) - 1, MAXMENLIN)) , .T. } )
					cMensONU := SubStr(cMensONU,IIf(EspacoAt(cMensONU, MAXMENLIN) > 1, EspacoAt(cMensONU, MAXMENLIN), MAXMENLIN) + 1)
				end
			endIf
		next
		cAux := alltrim( cAux )
	endif

	While !Empty(cAux)
		aadd(aMensagem,{ SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
EndIf
/*
dbSelectArea("SF1")
dbSetOrder(1)
If MsSeek(xFilial("SF1")+aNota[5]+aNota[4]+aNota[6]+aNota[7]) .And. SF1->(FieldPos("F1_FIMP"))<>0
	If SF1->F1_TIPO == "D"
		If Type("oNF:_InfNfe:_Total:_icmsTot:_VIPI:TEXT")<>"U"
			cAux := "Valor do Ipi : " + oNF:_InfNfe:_Total:_icmsTot:_VIPI:TEXT
			While !Empty(cAux)
				aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
				cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
			EndDo
		EndIf      
	EndIf
	MsUnlock()
	DbSkip()
EndIf
*/
                                                           
If MV_PAR04 == 2
	//impressao do valor do desconto calculdo conforme decreto 43.080/02 RICMS-MG
	nRecSF3 := SF3->(Recno())
	SF3->(dbSetOrder(4))
	SF3->(MsSeek(xFilial("SF3")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_DOC+SF2->F2_SERIE))
	While !SF3->(Eof()) .And. SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_DOC+SF2->F2_SERIE == SF3->F3_CLIEFOR+SF3->F3_LOJA+SF3->F3_NFISCAL+SF3->F3_SERIE
	    If SF3->(FieldPos("F3_DS43080"))<>0 .And. SF3->F3_DS43080 > 0
			cAux := "Base de calc.reduzida conf.Art.43, Anexo IV, Parte 1, Item 3 do RICMS-MG. Valor da deducao ICMS R$ " 
			cAux += Alltrim(Transform(SF3->F3_DS43080,"@e 9,999,999,999,999.99")) + " ref.reducao de base de calculo"  
			While !Empty(cAux)
				aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
				cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
			EndDo
	    EndIf
	    SF3->(dbSkip())
	EndDo
	SF3->(dbGoTo(nRecSF3))
ElseIf MV_PAR04 == 1
    //impressao do valor do desconto calculdo conforme decreto 43.080/02 RICMS-MG
	dbSelectArea("SF1")
	dbSetOrder(1)
	IF MsSeek(xFilial("SF1")+aNota[5]+aNota[4]+aNota[6]+aNota[7])
		dbSelectArea("SF3")
		dbSetOrder(4)
		If MsSeek(xFilial("SF3")+SF1->F1_FORNECE+SF1->F1_LOJA+SF1->F1_DOC+SF1->F1_SERIE)	                                                                                                                                      		
			If SF3->(FieldPos("F3_DS43080"))<>0 .And. SF3->F3_DS43080 > 0
				cAux := "Base de calc.reduzida conf.Art.43, Anexo IV, Parte 1, Item 3 do RICMS-MG. Valor da deducao ICMS R$ " 
				cAux += Alltrim(Transform(SF3->F3_DS43080,"@ze 9,999,999,999,999.99")) + " ref.reducao de base de calculo"  
				While !Empty(cAux)
					aadd(aMensagem, { SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
					cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
				EndDo                                                                                                                                                               
		    EndIf                                                                                                                                  	
		EndIf  
	EndIf
EndIF

If Type("oNF:_INFNFE:_IDE:_NFREF")<>"U"
	If Type("oNF:_INFNFE:_IDE:_NFREF") == "A"
		aInfNf := oNF:_INFNFE:_IDE:_NFREF
	Else
		aInfNf := {oNF:_INFNFE:_IDE:_NFREF}
	EndIf
	
	For nX := 1 to Len(aMensagem)
		If "ORIGINAL"$ Upper(aMensagem[nX][1])
			lNFori2 := .F.
		EndIf
	Next Nx
	
	cAux1 := ""
	cAux2 := ""
	For Nx := 1 to Len(aInfNf)
		If ValAtrib("aInfNf["+Str(nX)+"]:_REFNFE:TEXT")<>"U" .And. !AllTrim(aInfNf[nx]:_REFNFE:TEXT)$cAux1
			If !"CHAVE"$Upper(cAux1)
				If "65" $ substr (aInfNf[nx]:_REFNFE:TEXT,21,2)
					cAux1 += "Chave de acesso da NFC-E referenciada: "
				Else
					cAux1 += "Chave de acesso da NF-E referenciada: "
				Endif
			EndIf
			cAux1 += aInfNf[nx]:_REFNFE:TEXT+","
		ElseIf ValAtrib("aInfNf["+Str(nX)+"]:_REFNF:_NNF:TEXT")<>"U" .And. !AllTrim(aInfNf[nx]:_REFNF:_NNF:TEXT)$cAux2 .And. lNFori2 
			If !"ORIGINAL"$Upper(cAux2)
				cAux2 += " Numero da nota original: "
			EndIf
			cAux2 += aInfNf[nx]:_REFNF:_NNF:TEXT+","
		EndIf
	Next
	
	cAux	:=	""
	If !Empty(cAux1)
		cAux1	:=	Left(cAux1,Len(cAux1)-1)
		cAux 	+= cAux1
	EndIf
	If !Empty(cAux2)
		cAux2	:=	Left(cAux2,Len(cAux2)-1)
		cAux 	+= 	Iif(!Empty(cAux),CRLF,"")+cAux2
	EndIf
	
	While !Empty(cAux)
		aadd(aMensagem,{ SubStr(cAux,1,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN) - 1, MAXMENLIN)) , .F. } )
		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENLIN) > 1, EspacoAt(cAux, MAXMENLIN), MAXMENLIN) + 1)
	EndDo
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro "RESERVADO AO FISCO"                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

aResFisco := {}
nBaseIcm  := 0

If GetNewPar("MV_BCREFIS",.F.) .And. SuperGetMv("MV_ESTADO")$"PR"
	If Val(&("oTotal:_ICMSTOT:_VBCST:TEXT")) <> 0
		cAux := "Substituição Tributária: Art. 471, II e §1º do RICMS/PR: "
   		nLenDet := Len(oDet)
   		For nX := 1 To nLenDet
	   		oImposto := oDet[nX]
	   		If ValAtrib("oImposto:_Imposto")<>"U"
		 		If ValAtrib("oImposto:_Imposto:_ICMS")<>"U"
		 			nLenSit := Len(aSitTrib)
		 			For nY := 1 To nLenSit
		 				nPrivate2 := nY
		 				If ValAtrib("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nPrivate2])<>"U"
		 					If ValAtrib("oImposto:_IMPOSTO:_ICMS:_ICMS"+aSitTrib[nPrivate2]+":_VBCST:TEXT")<>"U"
		 		   				nBaseIcm := Val(&("oImposto:_Imposto:_ICMS:_ICMS"+aSitTrib[nY]+":_VBCST:TEXT"))
		 						cAux +=  oDet[nX]:_PROD:_CPROD:TEXT + ": BCICMS-ST R$" + AllTrim(TransForm(nBaseICM,TM(nBaseICM,TamSX3("D2_BASEICM")[1],TamSX3("D2_BASEICM")[2]))) + " / "	
   		 	  				Endif
   		 	 			Endif
   					Next nY
   	   			Endif
   	 		Endif
   	  	Next nX
	Endif
	While !Empty(cAux)   
		aadd(aResFisco,SubStr(cAux,1,64))
  		cAux := SubStr(cAux,IIf(EspacoAt(cAux, MAXMENL) > 1, 63, MAXMENL) +2)
   	EndDo	
Endif  

If !Empty(cMsgRet)
	aMsgRet := StrTokArr( cMsgRet, "|")
	aEval( aMsgRet, {|x| aadd( aResFisco, alltrim(x) ) } )
endif
        
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Calculo do numero de folhas                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nFolhas	  := 1
nLenItens := Len(aItens) - MAXITEM // Todos os produtos/serviços excluindo a primeira página
nMsgCompl := Len(aMensagem) - MAXMSG // Todas as mensagens complementares excluindo a primeira página
lFlag     := .T.

While lFlag
	// Caso existam produtos/serviços e mensagens complementares a serem escritas
	If nLenItens > 0 .And. nMsgCompl > 0
		nFolhas++
		If MV_PAR05 == 1 .And. (nFolhas % 2) == 0
			nLenItens -= MAXITEMP3
		Else // Frente e Verso Impressão até 50% da página
			nLenItens -= MAXITEMP2
			nMsgCompl -= MAXMSG2
		Endif
	// Caso existam apenas mensagens complementares a serem escritas
	ElseIf nLenItens <= 0 .And. nMsgCompl > 0
		nFolhas++
		nMsgCompl -= MAXMSG2
	// Caso existam apenas produtos/serviços a serem escritos
	ElseIf nLenItens > 0 .And. nMsgCompl <= 0
		nFolhas++
		// Se estiver habilitado frente e verso e for uma página impar
		If MV_PAR05 == 1 .And. (nFolhas % 2) == 0
			nLenItens -= MAXITEMP3
		Else
			nLenItens -= MAXITEMP2F
		EndIf
	// Se não tiver mais nada a ser escrito fecha a contagem
	Else
		lFlag := .F.
	EndIf
EndDo

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Inicializacao do objeto grafico                                         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If oDanfe == Nil
	
	lPreview := .T.
	oDanfe 	:= FWMSPrinter():New("DANFE", IMP_SPOOL)
	oDanfe:SetLandscape()
	oDanfe:Setup()
EndIf

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


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Inicializacao da pagina do objeto grafico                               ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
oDanfe:StartPage()
nLine  := -42  
nBaseTxt := 180
nBaseCol := 70
/* Comando Say Utilizados
Say( nRow, nCol, cText, oFont, nWidth, cClrText, nAngle )
*/

DanfeCab(oDanfe,nPosV,oNFe,oIdent,oEmitente,nFolha,nFolhas,cCodAutSef,oNfeDPEC,cCodAutDPEC,cDtHrRecCab,dDtReceb,@nLine,@nBaseCol,@nBaseTxt,aUf)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro destinatário/remetente                                           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
Do Case
	Case Type("oDestino:_CNPJ")=="O"
		cAux := TransForm(oDestino:_CNPJ:TEXT,"@R! NN.NNN.NNN/NNNN-99")
	Case Type("oDestino:_CPF")=="O"
		cAux := TransForm(oDestino:_CPF:TEXT,"@r 999.999.999-99")
	OtherWise
		cAux := Space(14)
EndCase

nLine -= 8
oDanfe:FillRect({nLine+197 - nAjustaDest,nBaseCol,nLine+269-nAjustaDest,nBaseCol+30},oBrush)
oDanfe:Say(nLine+265 - nAjustaDest,nBaseTxt+1,"DESTINATARIO/",oFont08N:oFont, , CLR_WHITE, 270 )
oDanfe:Say(nLine+260 - nAjustaDest,nBaseTxt+11,"REMETENTE"     ,oFont08N:oFont, ,CLR_WHITE , 270 )

nBaseTxt += 30 
oDanfe:Box(nLine+197 - nAjustaDest,nBaseCol+30,nLine+222,542)
oDanfe:Say(nLine+205 - nAjustaDest,nBaseTxt, "NOME/RAZÃO SOCIAL",oFont08N:oFont)
oDanfe:Say(nLine+215 - nAjustaDest,nBaseTxt,NoChar(oDestino:_XNome:TEXT,lConverte),oFont08:oFont)
oDanfe:Box(nLine+197 - nAjustaDest,542,nLine+222 - nAjustaDest,MAXBOXH-40)
oDanfe:Say(nLine+205 - nAjustaDest,552,"CNPJ/CPF",oFont08N:oFont)
oDanfe:Say(nLine+215 - nAjustaDest,552,cAux,oFont08:oFont)

oDanfe:Box(nLine+222 - nAjustaDest,nBaseCol+30,nLine+247 - nAjustaDest,402)
oDanfe:Say(nLine+230 - nAjustaDest,nBaseTxt,"ENDEREÇO",oFont08N:oFont)
oDanfe:Say(nLine+240 - nAjustaDest,nBaseTxt,aDest[01],oFont08:oFont)
oDanfe:Box(nLine+222 - nAjustaDest,402,nLine+247- nAjustaDest,602)
oDanfe:Say(nLine+230 - nAjustaDest,412,"BAIRRO/DISTRITO",oFont08N:oFont)
oDanfe:Say(nLine+240 - nAjustaDest,412,aDest[02],oFont08:oFont)
oDanfe:Box(nLine+222 - nAjustaDest,602,nLine+247,MAXBOXH-40)
oDanfe:Say(nLine+230 - nAjustaDest,612,"CEP",oFont08N:oFont)
oDanfe:Say(nLine+240 - nAjustaDest,612,aDest[03],oFont08:oFont)

oDanfe:Box(nLine+247 - nAjustaDest,nBaseCol+30,nLine+270 - nAjustaDest,302)
oDanfe:Say(nLine+255 - nAjustaDest,nBaseTxt,"MUNICIPIO",oFont08N:oFont)
oDanfe:Say(nLine+265 - nAjustaDest,nBaseTxt,aDest[05],oFont08:oFont)
oDanfe:Box(nLine+247 - nAjustaDest,302,nLine+270 - nAjustaDest,502)
oDanfe:Say(nLine+255 - nAjustaDest,312,"FONE/FAX",oFont08N:oFont)
oDanfe:Say(nLine+265 - nAjustaDest,312,aDest[06],oFont08:oFont)
oDanfe:Box(nLine+247 - nAjustaDest,502,nLine+270 - nAjustaDest,542)
oDanfe:Say(nLine+255 - nAjustaDest,512,"UF",oFont08N:oFont)
oDanfe:Say(nLine+265 - nAjustaDest,512,aDest[07],oFont08:oFont)
oDanfe:Box(nLine+247 - nAjustaDest,542,nLine+270 - nAjustaDest,MAXBOXH-40)
oDanfe:Say(nLine+255 - nAjustaDest,552,"INSCRIÇÃO ESTADUAL",oFont08N:oFont)
oDanfe:Say(nLine+265 - nAjustaDest,552,aDest[08],oFont08:oFont)

//nBaseTxt := 790 

oDanfe:Box(nLine+197 - nAjustaDest,MAXBOXH-40,nLine+222 - nAjustaDest,MAXBOXH+70)
oDanfe:Say(nLine+205 - nAjustaDest,MAXBOXH-30,"DATA DE EMISSÃO",oFont08N:oFont)
oDanfe:Say(nLine+215 - nAjustaDest,MAXBOXH-30,Iif(oNF:_INFNFE:_VERSAO:TEXT >= "3.10",ConvDate(oIdent:_DHEmi:TEXT),ConvDate(oIdent:_DEmi:TEXT)),oFont08:oFont)
oDanfe:Box(nLine+222 - nAjustaDest,MAXBOXH-40,nLine+247 - nAjustaDest,MAXBOXH+70)
oDanfe:Say(nLine+230 - nAjustaDest,MAXBOXH-30,"DATA ENTRADA/SAÍDA",oFont08N:oFont)
oDanfe:Say(nLine+240 - nAjustaDest,MAXBOXH-30,Iif( Empty(aDest[4]),"",ConvDate(aDest[4]) ),oFont08:oFont)
oDanfe:Box(nLine+247 - nAjustaDest,MAXBOXH-40,nLine+272 - nAjustaDest,MAXBOXH+70)
oDanfe:Say(nLine+255 - nAjustaDest,MAXBOXH-30,"HORA ENTRADA/SAÍDA",oFont08N:oFont)
oDanfe:Say(nLine+265 - nAjustaDest,MAXBOXH-30,aHrEnt[01],oFont08:oFont)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro Informações do local de entrega                                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If valType(oEntrega)=="O"
	Do Case
		Case Type("oEntrega:_CNPJ")=="O"
			cAux := TransForm(oEntrega:_CNPJ:TEXT,"@R! NN.NNN.NNN/NNNN-99")
		Case Type("oEntrega:_CPF")=="O"
			cAux := TransForm(oEntrega:_CPF:TEXT,"@r 999.999.999-99")
		OtherWise
			cAux := Space(14)
	EndCase

	nLine -= 8

	oDanfe:FillRect({nLine+188+nAjustaEnt,nBaseCol,nLine+258+nAjustaEnt,nBaseCol+30},oBrush)
	oDanfe:Say(nLine+230+nAjustaEnt,nBaseTxt - 27," LOCAL" ,oFont08N:oFont, , CLR_WHITE, 270)
	oDanfe:Say(nLine+230+nAjustaEnt,nBaseTxt - 21,"ENTREGA",oFont08N:oFont, ,CLR_WHITE , 270 )

	oDanfe:Box(nLine+187+nAjustaEnt,nBaseCol+30,nLine+222+nAjustaEnt,542)
	oDanfe:Say(nLine+195+nAjustaEnt,nBaseTxt, "NOME/RAZÃO SOCIAL",oFont08N:oFont)
	oDanfe:Say(nLine+205+nAjustaEnt,nBaseTxt,NoChar(aEntrega[1],lConverte),oFont08:oFont)
	oDanfe:Box(nLine+187+nAjustaEnt,542,nLine+212+nAjustaEnt,MAXBOXH-40)
	oDanfe:Say(nLine+195+nAjustaEnt,552,"CNPJ/CPF",oFont08N:oFont)
	oDanfe:Say(nLine+210+nAjustaEnt,552,cAux,oFont08:oFont)
	oDanfe:Box(nLine+212+nAjustaEnt,nBaseCol+30,nLine+237+nAjustaEnt,502)
	oDanfe:Say(nLine+220+nAjustaEnt,nBaseTxt,"ENDEREÇO",oFont08N:oFont)
	oDanfe:Say(nLine+230+nAjustaEnt,nBaseTxt,MontaEnd(oEntrega),oFont08:oFont)
	oDanfe:Box(nLine+212+nAjustaEnt,402,nLine+237+nAjustaEnt,802)
	oDanfe:Say(nLine+220+nAjustaEnt,412,"BAIRRO/DISTRITO",oFont08N:oFont)
	oDanfe:Say(nLine+230+nAjustaEnt,412,aEntrega[7],oFont08:oFont)
	oDanfe:Box(nLine+237+nAjustaEnt,nBaseCol+30,nLine+260+nAjustaEnt,730)
	oDanfe:Say(nLine+245+nAjustaEnt,nBaseTxt,"MUNICIPIO",oFont08N:oFont)
	oDanfe:Say(nLine+255+nAjustaEnt,nBaseTxt,aEntrega[8],oFont08:oFont)
	oDanfe:Box(nLine+237+nAjustaEnt,725,nLine+260+nAjustaEnt,MAXBOXH-40)
	oDanfe:Say(nLine+245+nAjustaEnt,735,"UF",oFont08N:oFont)
	oDanfe:Say(nLine+255+nAjustaEnt,735,aEntrega[9],oFont08:oFont)
	oDanfe:Box(nLine+187+nAjustaEnt,MAXBOXH-40,nLine+212+nAjustaEnt,MAXBOXH+70)
	oDanfe:Say(nLine+195+nAjustaEnt,MAXBOXH-30,"INSCRIÇÃO ESTADUAL",oFont08N:oFont)
	oDanfe:Say(nLine+205+nAjustaEnt,MAXBOXH-30,aEntrega[10],oFont08:oFont)
	oDanfe:Box(nLine+212+nAjustaEnt,MAXBOXH-40,nLine+237+nAjustaEnt,MAXBOXH+70)
	oDanfe:Say(nLine+220+nAjustaEnt,MAXBOXH-30,"CEP",oFont08N:oFont)
	oDanfe:Say(nLine+230+nAjustaEnt,MAXBOXH-30,aEntrega[11],oFont08:oFont)
	oDanfe:Box(nLine+237+nAjustaEnt,MAXBOXH-40,nLine+260+nAjustaEnt,MAXBOXH+70)
	oDanfe:Say(nLine+245+nAjustaEnt,MAXBOXH-30,"FONE/FAX entrega",oFont08N:oFont)
	oDanfe:Say(nLine+255+nAjustaEnt,MAXBOXH-30,aEntrega[12],oFont08:oFont)
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro Informações do local de retirada                                      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If valType(oRetirada)=="O"
	Do Case
		Case Type("oRetirada:_CNPJ")=="O"
			cAux := TransForm(oRetirada:_CNPJ:TEXT,"@R! NN.NNN.NNN/NNNN-99")
		Case Type("oRetirada:_CPF")=="O"
			cAux := TransForm(oRetirada:_CPF:TEXT,"@r 999.999.999-99")
		OtherWise
			cAux := Space(14)
	EndCase

	nLine -= 8

	oDanfe:FillRect({nLine+188+nAjustaRet,nBaseCol,nLine+258+nAjustaRet,nBaseCol+30},oBrush)
	oDanfe:Say(nLine+237+nAjustaRet,nBaseTxt - 27," LOCAL",oFont08N:oFont, , CLR_WHITE, 270)
	oDanfe:Say(nLine+237+nAjustaRet,nBaseTxt - 21,"RETIRADA"     ,oFont08N:oFont, ,CLR_WHITE , 270 )

	oDanfe:Box(nLine+187+nAjustaRet,nBaseCol+30,nLine+222+nAjustaRet,542)
	oDanfe:Say(nLine+195+nAjustaRet,nBaseTxt, "NOME/RAZÃO SOCIAL",oFont08N:oFont)
 	oDanfe:Say(nLine+205+nAjustaRet,nBaseTxt,NoChar(aRetirada[1],lConverte),oFont08:oFont)
	oDanfe:Box(nLine+187+nAjustaRet,542,nLine+212+nAjustaRet,MAXBOXH-40)
	oDanfe:Say(nLine+195+nAjustaRet,552,"CNPJ/CPF",oFont08N:oFont)
	oDanfe:Say(nLine+210+nAjustaRet,552,cAux,oFont08:oFont)
	oDanfe:Box(nLine+212+nAjustaRet,nBaseCol+30,nLine+237+nAjustaRet,502)
	oDanfe:Say(nLine+220+nAjustaRet,nBaseTxt,"ENDEREÇO",oFont08N:oFont)
	oDanfe:Say(nLine+230+nAjustaRet,nBaseTxt,MontaEnd(oRetirada),oFont08:oFont)
	oDanfe:Box(nLine+212+nAjustaRet,402,nLine+237+nAjustaRet,802)
	oDanfe:Say(nLine+220+nAjustaRet,412,"BAIRRO/DISTRITO",oFont08N:oFont)
	oDanfe:Say(nLine+230+nAjustaRet,412,aRetirada[7],oFont08:oFont)
	oDanfe:Box(nLine+237+nAjustaRet,nBaseCol+30,nLine+260+nAjustaRet,730)
	oDanfe:Say(nLine+245+nAjustaRet,nBaseTxt,"MUNICIPIO",oFont08N:oFont)
	oDanfe:Say(nLine+255+nAjustaRet,nBaseTxt,aRetirada[8],oFont08:oFont)
	oDanfe:Box(nLine+237+nAjustaRet,725,nLine+260+nAjustaRet,MAXBOXH-40)
	oDanfe:Say(nLine+245+nAjustaRet,735,"UF",oFont08N:oFont)
	oDanfe:Say(nLine+255+nAjustaRet,735,aRetirada[09],oFont08:oFont)
	oDanfe:Box(nLine+187+nAjustaRet,MAXBOXH-40,nLine+212+nAjustaRet,MAXBOXH+70)
	oDanfe:Say(nLine+195+nAjustaRet,MAXBOXH-30,"INSCRIÇÃO ESTADUAL",oFont08N:oFont)
	oDanfe:Say(nLine+205+nAjustaRet,MAXBOXH-30,aRetirada[10],oFont08:oFont)
	oDanfe:Box(nLine+212+nAjustaRet,MAXBOXH-40,nLine+237+nAjustaRet,MAXBOXH+70)
	oDanfe:Say(nLine+220+nAjustaRet,MAXBOXH-30,"CEP",oFont08N:oFont)
	oDanfe:Say(nLine+230+nAjustaRet,MAXBOXH-30,aRetirada[11],oFont08:oFont)
	oDanfe:Box(nLine+237+nAjustaRet,MAXBOXH-40,nLine+260+nAjustaRet,MAXBOXH+70)
	oDanfe:Say(nLine+245+nAjustaRet,MAXBOXH-30,"FONE/FAX retirada",oFont08N:oFont)
	oDanfe:Say(nLine+255+nAjustaRet,MAXBOXH-30,aRetirada[12],oFont08:oFont)
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro fatura                                                           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aAux := {{{},{},{},{},{},{},{},{},{}}}
nY := 0
For nX := 1 To Len(aFaturas)
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][1])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][2])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][3])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][4])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][5])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][6])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][7])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][8])
	nY++
	aadd(Atail(aAux)[nY],aFaturas[nX][9])
	If nY >= 9
		nY := 0
	EndIf
Next nX
              
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Fatura / Duplicata                                                      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
//nLine -= 3
nLine -= 5
nBaseTxt -= 30 
//oDanfe:Box(nLine+275,nBaseCol,nLine+310,nBaseCol+30)
oDanfe:FillRect({nLine+277+nAjustaFat,nBaseCol,nLine+308+nAjustaFat,nBaseCol+30},oBrush)

oDanfe:Say(nLine+305+nAjustaFat,nBaseTxt+7,"FATURA",oFont08N:oFont, ,CLR_WHITE , 270 ) 
nBaseTxt += 30 

nPos1Col := 0
nPos2Col := 0
For Nx := 1 to 8
	oDanfe:Box(nLine+277+nAjustaFat,nBaseCol+30+nPos1Col,nLine+310+nAjustaFat,nBaseCol+115.1+nPos2Col)
	nPos1Col += 84.1
	nPos2Col += 84.1
Next
//Ultimo Box
oDanfe:Box(nLine+277+nAjustaFat,nBaseCol+30+nPos1Col,nLine+310+nAjustaFat,MAXBOXH+70)


nColuna := nBaseCol+36
If Len(aFaturas) > 0
	For nY := 1 To 9
		oDanfe:Say(nLine+287+nAjustaFat,nColuna,aAux[1][ny][1],oFont08:oFont)
		oDanfe:Say(nLine+296+nAjustaFat,nColuna,aAux[1][ny][2],oFont08:oFont)
		if !lFat853
			oDanfe:Say(nLine+305+nAjustaFat,nColuna,aAux[1][ny][3],oFont08:oFont)
		endif
		nColuna:= nColuna+84.1
	Next nY
Endif

//nLine -= 15
nLine -= 18
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Calculo do imposto                                                      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nBaseTxt -= 30 
//oDanfe:Box(nLine+328,nBaseCol,nLine+376,nBaseCol+30)
oDanfe:FillRect({nLine+329+nAjustaImp,nBaseCol,nLine+375+nAjustaImp,nBaseCol+30},oBrush)
oDanfe:Say(nLine+372+nAjustaImp,nBaseTxt,"CALCULO",oFont08N:oFont, ,CLR_WHITE , 270 )
oDanfe:Say(nLine+360+nAjustaImp,nBaseTxt+7,"DO",oFont08N:oFont, , CLR_WHITE, 270 )
oDanfe:Say(nLine+370+nAjustaImp,nBaseTxt+14,"IMPOSTO",oFont08N:oFont, , CLR_WHITE, 270 )
nBaseTxt += 30 

oDanfe:Box(nLine+328+nAjustaImp,nBaseCol+30,nLine+353+nAjustaImp,262)
oDanfe:Say(nLine+336+nAjustaImp,nBaseTxt,"BASE DE CALCULO DO ICMS",oFont08N:oFont)
If cMVCODREG $ "2|3" 
	oDanfe:Say(nLine+346+nAjustaImp,nBaseTxt,aTotais[01],oFont08:oFont)
ElseIf lImpSimpN
	oDanfe:Say(nLine+346+nAjustaImp,nBaseTxt,aSimpNac[01],oFont08:oFont)	
Endif
oDanfe:Box(nLine+328+nAjustaImp,262,nLine+353+nAjustaImp,402)
oDanfe:Say(nLine+336+nAjustaImp,272,"VALOR DO ICMS",oFont08N:oFont)
If cMVCODREG $ "2|3" 
	oDanfe:Say(nLine+346+nAjustaImp,272,aTotais[02],oFont08:oFont)
ElseIf lImpSimpN
	oDanfe:Say(nLine+346+nAjustaImp,272,aSimpNac[02],oFont08:oFont)
Endif
oDanfe:Box(nLine+328+nAjustaImp,402,nLine+353+nAjustaImp,557)
oDanfe:Say(nLine+336+nAjustaImp,412,"BASE DE CALCULO DO ICMS ST",oFont08N:oFont)
oDanfe:Say(nLine+346+nAjustaImp,412,aTotais[03],oFont08:oFont)
oDanfe:Box(nLine+328+nAjustaImp,557,nLine+353+nAjustaImp,697)
oDanfe:Say(nLine+336+nAjustaImp,567,"VALOR DO ICMS SUBSTITUIÇÃO",oFont08N:oFont)
oDanfe:Say(nLine+346+nAjustaImp,567,aTotais[04],oFont08:oFont)
oDanfe:Box(nLine+328+nAjustaImp,697,nLine+353+nAjustaImp,MAXBOXH+70)
oDanfe:Say(nLine+336+nAjustaImp,707,"VALOR TOTAL DOS PRODUTOS",oFont08N:oFont)
oDanfe:Say(nLine+346+nAjustaImp,707,aTotais[05],oFont08:oFont)


oDanfe:Box(nLine+353+nAjustaImp,nBaseCol+30,nLine+378+nAjustaImp,232)
oDanfe:Say(nLine+361+nAjustaImp,nBaseTxt,"VALOR DO FRETE",oFont08N:oFont)
oDanfe:Say(nLine+371+nAjustaImp,nBaseTxt,aTotais[06],oFont08:oFont)
oDanfe:Box(nLine+353+nAjustaImp,232,nLine+378+nAjustaImp,352)
oDanfe:Say(nLine+361+nAjustaImp,242,"VALOR DO SEGURO",oFont08N:oFont)
oDanfe:Say(nLine+371+nAjustaImp,242,aTotais[07],oFont08:oFont)
oDanfe:Box(nLine+353+nAjustaImp,352,nLine+378+nAjustaImp,452)
oDanfe:Say(nLine+361+nAjustaImp,362,"DESCONTO",oFont08N:oFont)
oDanfe:Say(nLine+371+nAjustaImp,362,aTotais[08],oFont08:oFont)
oDanfe:Box(nLine+353+nAjustaImp,452,nLine+378+nAjustaImp,592)
oDanfe:Say(nLine+361+nAjustaImp,462,"OUTRAS DESPESAS ACESSÓRIAS",oFont08N:oFont)
oDanfe:Say(nLine+371+nAjustaImp,462,aTotais[09],oFont08:oFont)
oDanfe:Box(nLine+353+nAjustaImp,592,nLine+378+nAjustaImp,712)
oDanfe:Say(nLine+361+nAjustaImp,602,"VALOR TOTAL DO IPI",oFont08N:oFont)
oDanfe:Say(nLine+371+nAjustaImp,602,aTotais[10],oFont08:oFont)
oDanfe:Box(nLine+353+nAjustaImp,712,nLine+378+nAjustaImp,MAXBOXH+70)
oDanfe:Say(nLine+361+nAjustaImp,722,"VALOR TOTAL DA NOTA",oFont08N:oFont)
oDanfe:Say(nLine+371+nAjustaImp,722,aTotais[11],oFont08:oFont)

nLine -= 3

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Transportador/Volumes transportados                                     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nBaseTxt -= 30 
//oDanfe:Box(nLine+379,nBaseCol,nLine+452,nBaseCol+30)
oDanfe:FillRect({nLine+380+nAjustaVt,nBaseCol,nLine+451+nAjustaVt,nBaseCol+30},oBrush)   //ANALISAR
oDanfe:Say(nLine+446+nAjustaVt,nBaseTxt   ,"TRANSPORTADOR/" ,oFont08N:oFont, , CLR_WHITE, 270 )
oDanfe:Say(nLine+438+nAjustaVt,nBaseTxt+7 ,"VOLUMES"        ,oFont08N:oFont, , CLR_WHITE, 270 )
oDanfe:Say(nLine+448+nAjustaVt,nBaseTxt+14,"TRANSPORTADOS"  ,oFont08N:oFont, , CLR_WHITE, 270 )
nBaseTxt += 30 

oDanfe:Box(nLine+379+nAjustaVt,nBaseCol+30,nLine+404+nAjustaVt,402)
oDanfe:Say(nLine+387+nAjustaVt,nBaseTxt,"RAZÃO SOCIAL",oFont08N:oFont)
oDanfe:Say(nLine+397+nAjustaVt,nBaseTxt,aTransp[01],oFont08:oFont)
oDanfe:Box(nLine+379+nAjustaVt,402,nLine+404+nAjustaVt,482)
oDanfe:Say(nLine+387+nAjustaVt,412,"FRETE POR CONTA",oFont08N:oFont)
If cModFrete =="0"
	oDanfe:Say(nLine+397+nAjustaVt,412,"0-REMETENTE",oFont08:oFont)
ElseIf cModFrete =="1"
	oDanfe:Say(nLine+397+nAjustaVt,412,"1-DESTINATARIO",oFont08:oFont)
ElseIf cModFrete =="2"
	oDanfe:Say(nLine+397+nAjustaVt,412,"2-TERCEIROS",oFont08:oFont)
ElseIf cModFrete =="3"
	oDanfe:Say(nLine+397+nAjustaVt,412,"3-TRANSP PROP/REM",oFont08:oFont)
ElseIf cModFrete =="4"
	oDanfe:Say(nLine+397+nAjustaVt,412,"4-TRANSP PROP/DEST",oFont08:oFont)
ElseIf cModFrete =="9"
	oDanfe:Say(nLine+397+nAjustaVt,412,"9-SEM FRETE",oFont08:oFont)
Else
	oDanfe:Say(nLine+397+nAjustaVt,412,"",oFont08:oFont)
Endif
oDanfe:Box(nLine+379+nAjustaVt,482,nLine+404+nAjustaVt,562)
oDanfe:Say(nLine+387+nAjustaVt,492,"CÓDIGO ANTT",oFont08N:oFont)
oDanfe:Say(nLine+397+nAjustaVt,492,aTransp[03],oFont08:oFont)
oDanfe:Box(nLine+379+nAjustaVt,562,nLine+404+nAjustaVt,652)
oDanfe:Say(nLine+387+nAjustaVt,572,"PLACA DO VEÍCULO",oFont08N:oFont)
oDanfe:Say(nLine+397+nAjustaVt,572,aTransp[04],oFont08:oFont)
oDanfe:Box(nLine+379+nAjustaVt,652,nLine+404+nAjustaVt,702)
oDanfe:Say(nLine+387+nAjustaVt,662,"UF",oFont08N:oFont)
oDanfe:Say(nLine+397+nAjustaVt,662,aTransp[05],oFont08:oFont)

oDanfe:Box(nLine+379+nAjustaVt,702,nLine+404+nAjustaVt,MAXBOXH+70)
oDanfe:Say(nLine+387+nAjustaVt,712,"CNPJ/CPF",oFont08N:oFont)
oDanfe:Say(nLine+397+nAjustaVt,712,aTransp[06],oFont08:oFont)

oDanfe:Box(nLine+404+nAjustaVt,nBaseCol+30,nLine+429+nAjustaVt,402)
oDanfe:Say(nLine+412+nAjustaVt,nBaseTxt,"ENDEREÇO",oFont08N:oFont)
oDanfe:Say(nLine+422+nAjustaVt,nBaseTxt,aTransp[07],oFont08:oFont)
oDanfe:Box(nLine+404+nAjustaVt,402,nLine+429+nAjustaVt,652)
oDanfe:Say(nLine+412+nAjustaVt,412,"MUNICIPIO",oFont08N:oFont)
oDanfe:Say(nLine+422+nAjustaVt,412,aTransp[08],oFont08:oFont)
oDanfe:Box(nLine+404+nAjustaVt,652,nLine+429+nAjustaVt,702)
oDanfe:Say(nLine+412+nAjustaVt,662,"UF",oFont08N:oFont)
oDanfe:Say(nLine+422+nAjustaVt,662,aTransp[09],oFont08:oFont)
oDanfe:Box(nLine+404+nAjustaVt,702,nLine+429+nAjustaVt,MAXBOXH+70)
oDanfe:Say(nLine+412+nAjustaVt,712,"INSCRIÇÃO ESTADUAL",oFont08N:oFont)
oDanfe:Say(nLine+422+nAjustaVt,712,aTransp[10],oFont08:oFont)

oDanfe:Box(nLine+429+nAjustaVt,nBaseCol+30,nLine+454+nAjustaVt,169)
oDanfe:Say(nLine+437+nAjustaVt,nBaseTxt,"QUANTIDADE",oFont08N:oFont)
oDanfe:Say(nLine+447+nAjustaVt,nBaseTxt,aTransp[11],oFont08:oFont)
oDanfe:Box(nLine+429+nAjustaVt,169,nLine+454+nAjustaVt,352)
oDanfe:Say(nLine+437+nAjustaVt,179,"ESPECIE",oFont08N:oFont)
oDanfe:Say(nLine+447+nAjustaVt,179,Iif(!Empty(aTransp[12]),aTransp[12],Iif(Len(aEspVol)>0,aEspVol[1][1],"")),oFont08:oFont)
//oDanfe:Say(nLine+447,242,aEspVol[1][1],oFont08:oFont)
oDanfe:Box(nLine+429+nAjustaVt,352,nLine+454+nAjustaVt,472)
oDanfe:Say(nLine+437+nAjustaVt,362,"MARCA",oFont08N:oFont)
oDanfe:Say(nLine+447+nAjustaVt,362,aTransp[13],oFont08:oFont)
oDanfe:Box(nLine+429+nAjustaVt,472,nLine+454+nAjustaVt,592)
oDanfe:Say(nLine+437+nAjustaVt,482,"NUMERAÇÃO",oFont08N:oFont)
oDanfe:Say(nLine+447+nAjustaVt,482,aTransp[14],oFont08:oFont)
oDanfe:Box(nLine+429+nAjustaVt,592,nLine+454+nAjustaVt,712)
oDanfe:Say(nLine+437+nAjustaVt,602,"PESO BRUTO",oFont08N:oFont)
oDanfe:Say(nLine+447+nAjustaVt,602,Iif(!Empty(aTransp[15]),aTransp[15],Iif(Len(aEspVol)>0 .And. Val(aEspVol[1][3])>0,Transform(Val(aEspVol[1][3]),"@E 999999.9999"),"")),oFont08:oFont)
//oDanfe:Say(nLine+447,602,Iif (!Empty(aEspVol[1][3]),Transform(val(aEspVol[1][3]),"@E 999999.9999"),""),oFont08:oFont)
oDanfe:Box(nLine+429+nAjustaVt,712,nLine+454+nAjustaVt,MAXBOXH+70)
oDanfe:Say(nLine+437+nAjustaVt,722,"PESO LIQUIDO",oFont08N:oFont)
oDanfe:Say(nLine+447+nAjustaVt,722,Iif(!Empty(aTransp[16]),aTransp[16],Iif(Len(aEspVol)>0 .And. Val(aEspVol[1][2])>0,Transform(Val(aEspVol[1][2]),"@E 999999.9999"),"")),oFont08:oFont)
//oDanfe:Say(nLine+447,722,aTransp[16],oFont08:oFont)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Calculo do ISSQN                                                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

nBaseTxt -= 30 
//oDanfe:Box(nLine+573,nBaseCol,nLine+597,nBaseCol+30)
oDanfe:FillRect({nLine+574+nAjustaISSQN,nBaseCol,nLine+596+nAjustaISSQN,nBaseCol+30},oBrush)
//oDanfe:Box(nLine+574,nBaseCol+1,nLine+596,nBaseCol+29)
oDanfe:Say(nLine+596+nAjustaISSQN,nBaseTxt+7,"ISSQN",oFont08N:oFont, , CLR_WHITE, 270 )
nBaseTxt += 30 

oDanfe:Box(nLine+573+nAjustaISSQN,nBaseCol+30,nLine+597+nAjustaISSQN,302)
oDanfe:Say(nLine+581+nAjustaISSQN,nBaseTxt,"INSCRIÇÃO MUNICIPAL",oFont08N:oFont)
oDanfe:Say(nLine+591+nAjustaISSQN,nBaseTxt,aISSQN[1],oFont08:oFont)
oDanfe:Box(nLine+573+nAjustaISSQN,302,nLine+597+nAjustaISSQN,502)
oDanfe:Say(nLine+581+nAjustaISSQN,312,"VALOR TOTAL DOS SERVIÇOS",oFont08N:oFont)
oDanfe:Say(nLine+591+nAjustaISSQN,312,aISSQN[2],oFont08:oFont)
oDanfe:Box(nLine+573+nAjustaISSQN,502,nLine+597+nAjustaISSQN,702)
oDanfe:Say(nLine+581+nAjustaISSQN,512,"BASE DE CÁLCULO DO ISSQN",oFont08N:oFont)
oDanfe:Say(nLine+591+nAjustaISSQN,512,aISSQN[3],oFont08:oFont)
oDanfe:Box(nLine+573+nAjustaISSQN,702,nLine+597+nAjustaISSQN,MAXBOXH+70)
oDanfe:Say(nLine+581+nAjustaISSQN,712,"VALOR DO ISSQN",oFont08N:oFont)
oDanfe:Say(nLine+591+nAjustaISSQN,712,aISSQN[4],oFont08:oFont)


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Dados Adicionais                                                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nPosMsg := 0
DanfeInfC(oDanfe,aMensagem,@nBaseTxt,@nBaseCol,@nLine,@nPosMsg,nFolha)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Dados do produto ou servico                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aAux := {{{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}}}
nY := 0
nLenItens := Len(aItens)

For nX :=1 To nLenItens
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][01])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][02])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][03])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][04])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][05])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][06])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][07])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][08])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][09])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][10])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][11])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][12])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][13])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][14])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][15])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][16])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][17])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][18])
	nY++
	aadd(Atail(aAux)[nY],aItens[nX][19])
	If nY >= 19
		nY := 0
	EndIf
Next nX
For nX := 1 To nLenItens
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")
	nY++
	aadd(Atail(aAux)[nY],"")

	If nY >= 19
		nY := 0
	EndIf
	
Next nX

// Popula o array de cabeçalho das colunas de produtos/serviços.
aAuxCabec := {;
	"COD. PROD",;
	"DESCR PROD",;
	"NCM/SH",;
	IIf( cMVCODREG == "1", "CSOSN","CST" ),;
	"CFOP",;
	"UN",;
	"QUANT.",;
	"V.UNITARIO",;
	"VLR TOTAL",;
	"VLR DESC",;
	"V.UNI LIQ",;
	"TOTAL LIQ",;
	"BC.ICMS",;
	"BC.ICMS ST",;
	"VLR ICMS",;
	"VLR ICMS ST",;
	"VALOR IPI",;
	"ICMS",;
	"IPI";
}

// Retorna o tamanho das colunas baseado em seu conteudo
aTamCol := RetTamCol(aAuxCabec, aAux, oDanfe, oFont08N:oFont, oFont07:oFont)

aColProd := {}
DanfeIT(oDanfe, @nLine, @nBaseCol, @nBaseTxt, nFolha, nFolhas, @aColProd, aMensagem, nPosMsg, aTamCol)

If MV_PAR05=1 .And. nFolhas>1
	oDanfe:Say(615,450,"CONTINUA NO VERSO")
Endif

nFolha++
nLinha	:= nLine+478
nL		:= 0  

lVerso := MV_PAR05 == 1

For nY := 1 To nLenItens

	nL++	
	If nY > nMaxItem
		nAjustaPro := 0
	endif 

	if nL > nMaxItem
		if nPosMsg > 0 .and. nPosMsg <= Len(aMensagem) 
			nMaxItem := MAXITEMP2 // 22 itens
		else 
			nMaxItem := MAXITEMP2F // 44 itens
		endif
		if lVerso // Imprime no verso?
			if (nFolha % 2==0) // Somente folha par
				nMaxItem := MAXITEMP3 // 22 itens
			endif
		endif

			oDanfe:EndPage()
			oDanfe:StartPage()
			nLinha    	:=	181

			DanfeCab(oDanfe,nPosV,oNFe,oIdent,oEmitente,nFolha,nFolhas,cCodAutSef,oNfeDPEC,cCodAutDPEC,cDtHrRecCab,dDtReceb,@nLine,@nBaseCol,@nBaseTxt,aUf)			
			DanfeIT(oDanfe, @nLine, @nBaseCol, @nBaseTxt, nFolha, nFolhas, @aColProd, aMensagem, nPosMsg, aTamCol)
			
			if nPosMsg > 0 .and. (!lVerso .or. (nFolha % 2 !=0) ) // Impressão no verso somente em folha par e sem mensagem complementar.
				DanfeInfC(oDanfe,aMensagem,@nBaseTxt,@nBaseCol,@nLine,@nPosMsg,nFolha)
			EndIf	

			nL := 1
			nLinha := 169
			nFolha++   
	Endif
	/* 
		Impressão dos itens da NFe
	*/
	If aAux[1][1][nY] == "-"
		if oDanfe:nDevice == 2
			oDanfe:Say(nLinha+nAjustaPro, aColProd[1][1] + 2, Replicate("- ", 174), oFont07:oFont)
		else
			oDanfe:Say(nLinha+nAjustaPro, aColProd[1][1] + 2, Replicate("- ", 192), oFont07:oFont)
		endif	
	Else
		oDanfe:Say(nLinha+nAjustaPro, aColProd[1][1] + 2, aAux[1][1][nY], oFont07:oFont)

		If aAux[1][2][nY][2]
			oDanfe:Say(nLinha+nAjustaPro, aColProd[2][1] + 2, NoChar(aAux[1][2][nY][1], lConverte), oFont07N:oFont) // COD ONU DESTACADO EM NEGRITO
		else
			oDanfe:Say(nLinha+nAjustaPro, aColProd[2][1] + 2, NoChar(aAux[1][2][nY][1], lConverte), oFont07:oFont) // DESCRICAO DO PRODUTO
		EndIf

		oDanfe:Say(nLinha+nAjustaPro, aColProd[3][1] + 2, aAux[1][3][nY], oFont07:oFont)
		oDanfe:Say(nLinha+nAjustaPro, aColProd[4][1] + 2, aAux[1][4][nY], oFont07:oFont)
		oDanfe:Say(nLinha+nAjustaPro, aColProd[5][1] + 2, aAux[1][5][nY], oFont07:oFont)
		oDanfe:Say(nLinha+nAjustaPro, aColProd[6][1] + 2, aAux[1][6][nY], oFont07:oFont)

		nAuxH2 :=  len(aAux[1][7][nY]) + (aColProd[7][1] + ((aColProd[7][2] - aColProd[7][1]) - RetTamTex(aAux[1][7][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][7][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][8][nY]) + (aColProd[8][1] + ((aColProd[8][2] - aColProd[8][1]) - RetTamTex(aAux[1][8][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][8][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][9][nY]) + (aColProd[9][1] + ((aColProd[9][2] - aColProd[9][1]) - RetTamTex(aAux[1][9][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][9][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][10][nY]) + (aColProd[10][1] + ((aColProd[10][2] - aColProd[10][1]) - RetTamTex(aAux[1][10][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][10][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][11][nY]) + (aColProd[11][1] + ((aColProd[11][2] - aColProd[11][1]) - RetTamTex(aAux[1][11][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][11][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][12][nY]) + (aColProd[12][1] + ((aColProd[12][2] - aColProd[12][1]) - RetTamTex(aAux[1][12][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][12][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][13][nY]) + (aColProd[13][1] + ((aColProd[13][2] - aColProd[13][1]) - RetTamTex(aAux[1][13][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][13][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][14][nY]) + (aColProd[14][1] + ((aColProd[14][2] - aColProd[14][1]) - RetTamTex(aAux[1][14][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][14][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][15][nY]) + (aColProd[15][1] + ((aColProd[15][2] - aColProd[15][1]) - RetTamTex(aAux[1][15][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][15][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][16][nY]) + (aColProd[16][1] + ((aColProd[16][2] - aColProd[16][1]) - RetTamTex(aAux[1][16][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][16][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][17][nY]) + (aColProd[17][1] + ((aColProd[17][2] - aColProd[17][1]) - RetTamTex(aAux[1][17][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][17][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][18][nY]) + (aColProd[18][1] + ((aColProd[18][2] - aColProd[18][1]) - RetTamTex(aAux[1][18][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][18][nY], oFont07:oFont)
		
		nAuxH2 := len(aAux[1][19][nY]) + (aColProd[19][1] + ((aColProd[19][2] - aColProd[19][1]) - RetTamTex(aAux[1][19][nY], oFont07:oFont, oDanfe)))
		oDanfe:Say(nLinha+nAjustaPro, nAuxH2, aAux[1][19][nY], oFont07:oFont)
	EndIf
	nLinha := nLinha + 10 
Next nY 

/* Impressão de mensagem complementar, caso ainda não tenha finalizado */

nLenMensagens := Len(aMensagem)
While nPosMsg > 0 .and. nPosMsg <= nLenMensagens
	oDanfe:EndPage()
	oDanfe:StartPage()
	nLinha    	:=	181                
	DanfeCab(oDanfe,nPosV,oNFe,oIdent,oEmitente,nFolha,nFolhas,cCodAutSef,oNfeDPEC,cCodAutDPEC,cDtHrRecCab,dDtReceb,@nLine,@nBaseCol,@nBaseTxt,aUf)
	DanfeInfC(oDanfe,aMensagem,@nBaseTxt,@nBaseCol,@nLine,@nPosMsg,nFolha,.T.)
	nFolha++
EndDo

nMaxItem :=  MAXITEM

/* Finaliza a Impressão */

oDanfe:EndPage()

/*------------------------------------------------------------------------------------------------
	Tratamento para nao imprimir DANFEs diferentes na mesma folha, uma na FRENTE e outra no VERSO
		quando MV_PAR05 =1 (frente e verso = sim)
------------------------------------------------------------------------------------------------*/

if lVerso .And. MV_PAR01 <> MV_PAR02 
	If nFolhas %2 <> 0 
		oDanfe:StartPage()
		oDanfe:EndPage()
	EndIf
EndIf

aSize(aAuxCabec, 0)
aAuxCabec:= nil
aSize(aTamCol, 0)
aTamCol:= nil
aSize(aSitTrib, 0)
aSitTrib:= nil
aSize(aSitSN, 0)
aSitSN:= nil
aSize(aTransp, 0)
aTransp:= nil
aSize(aDest, 0)
aDest:= nil
aSize(aRetirada, 0)
aRetirada:= nil
aSize(aEntrega, 0)
aEntrega:= nil
aSize(aHrEnt, 0)
aHrEnt:= nil
aSize(aFaturas, 0)
aFaturas:= nil
aSize(aItens, 0)
aItens:= nil
aSize(aISSQN, 0)
aISSQN:= nil
aSize(aSimpNac, 0)
aSimpNac:= nil
aSize(aTotais, 0)
aTotais:= nil
aSize(aAux, 0)
aAux:= nil
aSize(aUF, 0)
aUF:= nil
aSize(aMensagem, 0)
aMensagem:= nil
aSize(aEspVol, 0)
aEspVol:= nil
aSize(aResFisco, 0)
aResFisco:= nil
aSize(aEspecie, 0)
aEspecie:= nil
aSize(aIndImp, 0)
aIndImp:= nil
aSize(aIndAux, 0)
aIndAux:= nil
aSize(aCodONU, 0)
aCodONU:= nil
aSize(aAreaSB5, 0)
aAreaSB5:= nil
aSize(aAreaDY3, 0)
aAreaDY3:= nil
aSize(aMensONU, 0)
aMensONU:= nil
aSize(aAuxCom, 0)
aAuxCom:= nil
aSize(aItensAux, 0)
aItensAux:= nil
aSize(aArray, 0)
aArray:= nil
aSize(aMsgRet, 0)
aMsgRet:= nil
aSize(aMarca, 0)
aMarca:= nil
aSize(aNumeracao, 0)
aNumeracao:= nil

freeObj(oEmitente)
oEmitente := nil
freeObj(oIdent)
oIdent := nil
freeObj(oDestino)
oDestino := nil
freeObj(oTotal)
oTotal := nil
freeObj(oTransp)
oTransp := nil
freeObj(oDet)
oDet := nil
freeObj(oFatura)
oFatura := nil
freeObj(oImposto)
oImposto := nil
freeObj(oEntrega)
oEntrega := nil
freeObj(oRetirada)
oRetirada := nil
freeObj(oDPEC)
oDPEC := nil
freeObj(oNF)
oNF := nil

Return (.T.)

//-----------------------------------------------------------------------
/*/{Protheus.doc} DanfeCab
Definicao do Cabecalho do documento.
 
@author 	Roberto Souza
@since 		13/08/10
@version 	1.0
/*/
//-----------------------------------------------------------------------                                                    
Static Function DanfeCab(oDanfe,nPosV,oNFe,oIdent,oEmitente,nFolha,nFolhas,cCodAutSef,oNfeDPEC,cCodAutDPEC,cDtHrRecCab,dDtReceb,nLine,nBaseCol,nBaseTxt,aUf)

Local cChaveCont := ""
Local cDataEmi   := ""
Local cTPEmis    := ""
Local cValIcm    := ""
Local cICMSp     := ""
Local cICMSs     := ""
Local cUF		 := ""
Local cCNPJCPF	 := ""
Local cLogo      := FisxLogo("1")
Local lConverte  := GetNewPar("MV_CONVERT",.F.)
Local lMv_Logod	 := If( GetNewPar("MV_LOGOD", "N" ) == "S", .T., .F. )
Local cLogoD	 := ""

Local cDescLogo		:= ""
Local cGrpCompany	:= ""
Local cCodEmpGrp	:= ""
Local cUnitGrp		:= ""
Local cFilGrp		:= ""

Private oDPEC    := oNfeDPEC

Default cCodAutSef := ""
Default cCodAutDPEC:= ""
Default cDtHrRecCab:= ""
Default dDtReceb   := CToD("")

nLine    := -42
nBaseCol := 70

oDanfe:Say(000, INIBOXH+74, Replicate("- ",150), oFont08N:oFont, , , 90 )

oDanfe:Box(nLine+135, INIBOXH+10, MAXBOXV, INIBOXH+35)
If Len(oEmitente:_xNome:Text) >= 50
	oDanfe:Say(MAXBOXV-10, INIBOXH+20, "RECEBEMOS DE "+NoChar(oEmitente:_xNome:Text,lConverte), oFont07:oFont, , , 270 )
	oDanfe:Say(MAXBOXV-10, INIBOXH+30, "OS PRODUTOS CONSTANTES DA NOTA FISCAL INDICADA AO LADO", oFont07:oFont, , , 270 )
Else
	oDanfe:Say(MAXBOXV-10, INIBOXH+20, "RECEBEMOS DE "+NoChar(oEmitente:_xNome:Text,lConverte)+" OS PRODUTOS CONSTANTES DA NOTA FISCAL INDICADA AO LADO", oFont07:oFont, , , 270 )
EndIf
	
oDanfe:Box(nLine+500,INIBOXH+35,MAXBOXV,INIBOXH+70)
oDanfe:Say(MAXBOXV-10, INIBOXH+45, "DATA DE RECEBIMENTO", oFont07N:oFont, , , 270)

oDanfe:Box(nLine+135,INIBOXH+35,nLine+500,INIBOXH+70)
oDanfe:Say(MAXBOXV-150, INIBOXH+45, "IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR", oFont07N:oFont, , , 270)

oDanfe:Box(nLine+042, INIBOXH+10, nLine+135, INIBOXH+70)
oDanfe:Say(MAXBOXV-550, INIBOXH+20, iif(lNFCE,"NFC-e","NF-e"), oFont08N:oFont, , , 270)
oDanfe:Say(MAXBOXV-520, INIBOXH+35, "Nº "+StrZero(Val(oIdent:_NNf:Text),9), oFont08:oFont, , , 270)
oDanfe:Say(MAXBOXV-520, INIBOXH+45, "SÉRIE "+SubStr(oIdent:_Serie:Text,1,3), oFont08:oFont, , , 270)


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro 1 IDENTIFICACAO DO EMITENTE                                      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

nBaseTxt := 180
oDanfe:Box(nLine+042,nBaseCol,nLine+139,450)
oDanfe:Say(nLine+057,nBaseTxt, "Identificação do emitente",oFont12N:oFont)
If len(oEmitente:_xNome:Text)>43
	oDanfe:Say(nLine+070,nBaseTxt,SubStr(NoChar(oEmitente:_xNome:Text,lConverte),1,45), ValidDanfe(oDanfe:nDevice) )
	oDanfe:Say(nLine+080,nBaseTxt,SubStr(NoChar(oEmitente:_xNome:Text,lConverte),46,45), ValidDanfe(oDanfe:nDevice) )
Else
	oDanfe:Say(nLine+070,nBaseTxt, NoChar(oEmitente:_xNome:Text,lConverte),ValidDanfe(oDanfe:nDevice))
Endif
If len(oEmitente:_xNome:Text)>45
	oDanfe:Say(nLine+090,nBaseTxt, NoChar(oEmitente:_EnderEmit:_xLgr:Text,lConverte)+", "+oEmitente:_EnderEmit:_Nro:Text,oFont08N:oFont)
Else
	oDanfe:Say(nLine+080,nBaseTxt, NoChar(oEmitente:_EnderEmit:_xLgr:Text,lConverte)+", "+oEmitente:_EnderEmit:_Nro:Text,oFont08N:oFont)
Endif
If len(oEmitente:_xNome:Text)>45
	If Type("oEmitente:_EnderEmit:_xCpl") <> "U"
		oDanfe:Say(nLine+100,nBaseTxt, "Complemento: " + NoChar(oEmitente:_EnderEmit:_xCpl:TEXT,lConverte),oFont08N:oFont)
		oDanfe:Say(nLine+110,nBaseTxt, NoChar(oEmitente:_EnderEmit:_xBairro:Text,lConverte)+" Cep:"+TransForm(IIF(Type("oEmitente:_EnderEmit:_Cep")=="U","",oEmitente:_EnderEmit:_Cep:Text),"@r 99999-999"),oFont08N:oFont)
		oDanfe:Say(nLine+120,nBaseTxt, oEmitente:_EnderEmit:_xMun:Text+"/"+oEmitente:_EnderEmit:_UF:Text,oFont08N:oFont)
		oDanfe:Say(nLine+130,nBaseTxt, "Fone: "+IIf(Type("oEmitente:_EnderEmit:_Fone")=="U","",oEmitente:_EnderEmit:_Fone:Text),oFont08N:oFont)
	Else
		oDanfe:Say(nLine+100,nBaseTxt, NoChar(oEmitente:_EnderEmit:_xBairro:Text,lConverte)+" Cep:"+TransForm(IIF(Type("oEmitente:_EnderEmit:_Cep")=="U","",oEmitente:_EnderEmit:_Cep:Text),"@r 99999-999"),oFont08N:oFont)
		oDanfe:Say(nLine+110,nBaseTxt, oEmitente:_EnderEmit:_xMun:Text+"/"+oEmitente:_EnderEmit:_UF:Text,oFont08N:oFont)
		oDanfe:Say(nLine+120,nBaseTxt, "Fone: "+IIf(Type("oEmitente:_EnderEmit:_Fone")=="U","",oEmitente:_EnderEmit:_Fone:Text),oFont08N:oFont)
	EndIf
	
Else
	If Type("oEmitente:_EnderEmit:_xCpl") <> "U"
		oDanfe:Say(nLine+090,nBaseTxt, "Complemento: " + NoChar(oEmitente:_EnderEmit:_xCpl:TEXT,lConverte),oFont08N:oFont)
		oDanfe:Say(nLine+100,nBaseTxt, NoChar(oEmitente:_EnderEmit:_xBairro:Text,lConverte)+" Cep:"+TransForm(IIF(Type("oEmitente:_EnderEmit:_Cep")=="U","",oEmitente:_EnderEmit:_Cep:Text),"@r 99999-999"),oFont08N:oFont)
		oDanfe:Say(nLine+110,nBaseTxt, oEmitente:_EnderEmit:_xMun:Text+"/"+oEmitente:_EnderEmit:_UF:Text,oFont08N:oFont)
		oDanfe:Say(nLine+120,nBaseTxt, "Fone: "+IIf(Type("oEmitente:_EnderEmit:_Fone")=="U","",oEmitente:_EnderEmit:_Fone:Text),oFont08N:oFont)
	Else
		oDanfe:Say(nLine+090,nBaseTxt, NoChar(oEmitente:_EnderEmit:_xBairro:Text,lConverte)+" Cep:"+TransForm(IIF(Type("oEmitente:_EnderEmit:_Cep")=="U","",oEmitente:_EnderEmit:_Cep:Text),"@r 99999-999"),oFont08N:oFont)
		oDanfe:Say(nLine+100,nBaseTxt, oEmitente:_EnderEmit:_xMun:Text+"/"+oEmitente:_EnderEmit:_UF:Text,oFont08N:oFont)
		oDanfe:Say(nLine+110,nBaseTxt, "Fone: "+IIf(Type("oEmitente:_EnderEmit:_Fone")=="U","",oEmitente:_EnderEmit:_Fone:Text),oFont08N:oFont)
	EndIf
Endif


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro 2                                                                ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

nBaseTxt := 460
oDanfe:Box(nLine+042,450,nLine+139,602)
	if oDanfe:nDevice == 2
		oDanfe:Say(nLine+055,nBaseTxt+35, "DANFE",oFont12N:oFont)
		oDanfe:Say(nLine+065,nBaseTxt+10, "DOCUMENTO AUXILIAR DA",oFont08:oFont)
	else
		oDanfe:Say(nLine+055,nBaseTxt+35, "DANFE",oFont18N:oFont)
		oDanfe:Say(nLine+065,nBaseTxt+10, "DOCUMENTO AUXILIAR DA",oFont10:oFont)
	endif

if lNFCE
	oDanfe:Say(nLine+075,nBaseTxt+10, "NOTA FISCAL DE CONSUMIDOR",oFont10:oFont)
else
	if oDanfe:nDevice == 2
	 	oDanfe:Say(nLine+075,nBaseTxt+10, "NOTA FISCAL ELETRÔNICA",oFont08:oFont)
	else
		oDanfe:Say(nLine+075,nBaseTxt+10, "NOTA FISCAL ELETRÔNICA",oFont10:oFont)
	endif
endif
if oDanfe:nDevice == 2
	oDanfe:Say(nLine+085,nBaseTxt+15, "0-ENTRADA",oFont08:oFont)
	oDanfe:Say(nLine+095,nBaseTxt+15, "1-SAÍDA"  ,oFont08:oFont)
else
	oDanfe:Say(nLine+085,nBaseTxt+15, "0-ENTRADA",oFont10:oFont)
	oDanfe:Say(nLine+095,nBaseTxt+15, "1-SAÍDA"  ,oFont10:oFont)
endif
oDanfe:Box(nLine+078,nBaseTxt+70,nLine+092,nBaseTxt+85)
oDanfe:Say(nLine+088,nBaseTxt+75, oIdent:_TpNf:Text,oFont10N:oFont)
oDanfe:Say(nLine+110,nBaseTxt,"N. "+StrZero(Val(oIdent:_NNf:Text),9),oFont10N:oFont)
oDanfe:Say(nLine+120,nBaseTxt,"SÉRIE "+SubStr(oIdent:_Serie:Text,1,3),oFont10N:oFont)
oDanfe:Say(nLine+130,nBaseTxt,"FOLHA "+StrZero(nFolha,2)+"/"+StrZero(nFolhas,2),oFont10N:oFont)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Logotipo                                     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If lMv_Logod
	cGrpCompany	:= AllTrim(FWGrpCompany())
	cCodEmpGrp	:= AllTrim(FWCodEmp())
	cUnitGrp	:= AllTrim(FWUnitBusiness())
	cFilGrp		:= AllTrim(FWFilial())

	If !Empty(cUnitGrp)
		cDescLogo	:= cGrpCompany + cCodEmpGrp + cUnitGrp + cFilGrp
	Else
		cDescLogo	:= cEmpAnt + cFilAnt
	EndIf

	cLogoD := GetSrvProfString("Startpath","") + "DANFE" + cDescLogo + ".BMP"
	If !File(cLogoD)
		cLogoD	:= GetSrvProfString("Startpath","") + "DANFE" + cEmpAnt + ".BMP"
		If !File(cLogoD)
			lMv_Logod := .F.
		EndIf
	EndIf	
EndIf

If nfolha>=1
	If lMv_Logod
		oDanfe:SayBitmap(005,075,cLogoD,095,096)
	Else
		oDanfe:SayBitmap(005,075,cLogo,095,096)
	EndIf
Endif

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Codigo de barra                                                         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

nBaseTxt := 612
oDanfe:Box(nLine+042,602,nLine+088,MAXBOXH+70)
oDanfe:Box(nLine+075,602,nLine+077,MAXBOXH+70)
oDanfe:Box(nLine+077,602,nLine+110,MAXBOXH+70)
oDanfe:Box(nLine+105,602,nLine+139,MAXBOXH+70)
oDanfe:Say(nLine+097,nBaseTxt,TransForm(SubStr(oNF:_InfNfe:_ID:Text,4),"@r 9999 9999 9999 9999 9999 9999 9999 9999 9999 9999 9999"),oFont10N:oFont)


If nFolha >= 1
	oDanfe:Say(nLine+087,nBaseTxt,"CHAVE DE ACESSO DA "+iif(lNFCE,"NFC-E","NF-E"),oFont09N:oFont)
	nFontSize := 28
	oDanfe:Code128C(nLine+072,nBaseTxt,SubStr(oNF:_InfNfe:_ID:Text,4), nFontSize )
EndIf

If !Empty(cCodAutDPEC) .And. (oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"4" .And. !lUsaColab
	cDataEmi := Iif(oNF:_INFNFE:_VERSAO:TEXT >= "3.10",Substr(oNFe:_NFE:_INFNFE:_IDE:_DHEMI:Text,9,2),Substr(oNFe:_NFE:_INFNFE:_IDE:_DEMI:Text,9,2))
	cTPEmis  := "4"
	If Type("oDPEC:_ENVDPEC:_INFDPEC:_RESNFE") <> "U"
		cUF      := aUF[aScan(aUF,{|x| x[1] == oDPEC:_ENVDPEC:_INFDPEC:_RESNFE:_UF:Text})][02]
		cValIcm := StrZero(Val(StrTran(oDPEC:_ENVDPEC:_INFDPEC:_RESNFE:_VNF:TEXT,".","")),14)
		cICMSp := iif(Val(oDPEC:_ENVDPEC:_INFDPEC:_RESNFE:_VICMS:TEXT)>0,"1","2")
		cICMSs := iif(Val(oDPEC:_ENVDPEC:_INFDPEC:_RESNFE:_VST:TEXT)>0,"1","2")
	ElseIf type ("oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST") <> "U" //EPEC NFE
		If Type ("oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_UF:TEXT") <> "U"
			cUF := aUF[aScan(aUF,{|x| x[1] == oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_UF:TEXT})][02]			
		EndIf
		If Type ("oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_VNF:TEXT") <> "U"
			cValIcm := StrZero(Val(StrTran(oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_VNF:TEXT,".","")),14)
		EndIf
		If 	Type ("oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_VICMS:TEXT") <> "U"
			cICMSp:= IIf(Val(oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_VICMS:TEXT) > 0,"1","2")
		EndIf
		If 	Type ("oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_VST:TEXT") <> "U"
			cICMSs := IIf(Val(oDPEC:_EVENTO:_INFEVENTO:_DETEVENTO:_DEST:_VST:TEXT )> 0,"1","2")
		EndIf	
	EndIf
ElseIF (oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"25" .Or. ( (oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"4" .And. lUsaColab .And. !Empty(cCodAutDPEC) )
	cUF      := aUF[aScan(aUF,{|x| x[1] == oNFe:_NFE:_INFNFE:_DEST:_ENDERDEST:_UF:Text})][02]
	cDataEmi := Iif(oNF:_INFNFE:_VERSAO:TEXT >= "3.10",Substr(oNFe:_NFE:_INFNFE:_IDE:_DHEMI:Text,9,2),Substr(oNFe:_NFE:_INFNFE:_IDE:_DEMI:Text,9,2))
	cTPEmis  := oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT
	cValIcm  := StrZero(Val(StrTran(oNFe:_NFE:_INFNFE:_TOTAL:_ICMSTOT:_VNF:TEXT,".","")),14)
	cICMSp   := iif(Val(oNFe:_NFE:_INFNFE:_TOTAL:_ICMSTOT:_VICMS:TEXT)>0,"1","2")
	cICMSs   :=iif(Val(oNFe:_NFE:_INFNFE:_TOTAL:_ICMSTOT:_VST:TEXT)>0,"1","2")
EndIf
If !Empty(cUF) .And. !Empty(cDataEmi) .And. !Empty(cTPEmis) .And. !Empty(cValIcm) .And. !Empty(cICMSp) .And. !Empty(cICMSs)
	If Type("oNF:_InfNfe:_DEST:_CNPJ:Text")<>"U"
		cCNPJCPF := oNF:_InfNfe:_DEST:_CNPJ:Text
		If cUf == "99"
			cCNPJCPF := STRZERO(val(cCNPJCPF),14)
		EndIf
	ElseIf Type("oNF:_INFNFE:_DEST:_CPF:Text")<>"U"
		cCNPJCPF := oNF:_INFNFE:_DEST:_CPF:Text
		cCNPJCPF := STRZERO(val(cCNPJCPF),14)
	Else
		cCNPJCPF := ""
	EndIf
	cChaveCont += cUF+cTPEmis+cCNPJCPF+cValIcm+cICMSp+cICMSs+cDataEmi
	cChaveCont := cChaveCont+Modulo11(cChaveCont)
EndIf

If Empty(cChaveCont)
	if oDanfe:nDevice == 2
		oDanfe:Say(nLine+117,nBaseTxt,"Consulta de autenticidade no portal nacional da "+iif(lNFCE,"NFC-e","NF-e"),oFont09N:oFont)
		oDanfe:Say(nLine+127,nBaseTxt,"www.nfe.fazenda.gov.br/portal ou no site da SEFAZ Autorizada",oFont09:oFont)
	else
		oDanfe:Say(nLine+117,nBaseTxt,"Consulta de autenticidade no portal nacional da "+iif(lNFCE,"NFC-e","NF-e"),oFont10:oFont)
		oDanfe:Say(nLine+127,nBaseTxt,"www.nfe.fazenda.gov.br/portal ou no site da SEFAZ Autorizada",oFont10:oFont)
	endif

Endif

If  !Empty(cCodAutDPEC)
	oDanfe:Say(nLine+117,nBaseTxt,"Consulta de autenticidade no portal nacional da "+iif(lNFCE,"NFC-e","NF-e"),oFont10:oFont)
	oDanfe:Say(nLine+127,nBaseTxt,"www.nfe.fazenda.gov.br/portal ou no site da SEFAZ Autorizada",oFont10:oFont)
Endif


// inicio do segundo codigo de barras ref. a transmissao CONTIGENCIA OFF LINE
If !Empty(cChaveCont) .And. Empty(cCodAutDPEC) .And. !(Val(SubStr(oNF:_INFNFE:_IDE:_SERIE:TEXT,1,3)) >= 900)
	If nFolha == 1
		If !Empty(cChaveCont)
			nFontSize := 28
			oDanfe:Code128C(nLine+135,nBaseTxt,cChaveCont, nFontSize )
		EndIf
	Else
		If !Empty(cChaveCont)
			nFontSize := 28
			oDanfe:Code128C(nLine+135,nBaseTxt,cChaveCont, nFontSize )
		EndIf
	EndIf
EndIf



//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro 4   NATUREZA DA OPERACAO /  DADOS NFE / DPEC                     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nBaseTxt := nBaseCol + 10
oDanfe:Box(nLine+139,nBaseCol,nLine+164,602)
oDanfe:Box(nLine+139,602,nLine+164,MAXBOXH+70)

oDanfe:Say(nLine+148,nBaseTxt,"NATUREZA DA OPERAÇÃO",oFont08N:oFont)
oDanfe:Say(nLine+158,nBaseTxt,oIdent:_NATOP:TEXT,oFont08:oFont)
If(!Empty(cCodAutDPEC))
	oDanfe:Say(nLine+148,610,"NÚMERO DE REGISTRO DPEC",oFont08N:oFont)
	
Endif
If(((Val(SubStr(oNF:_INFNFE:_IDE:_SERIE:TEXT,1,3)) >= 900).And.(oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"2") .Or. (oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"1|6|7")
	oDanfe:Say(nLine+148,610,"PROTOCOLO DE AUTORIZAÇÃO DE USO",oFont08N:oFont)
Endif
If((oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"25")
	oDanfe:Say(nLine+148,610,"DADOS DA "+iif(lNFCE,"NFC-E","NF-E"),oFont08N:oFont)
Endif
oDanfe:Say(nLine+158,610,IIF(!Empty(cCodAutDPEC),cCodAutDPEC+" "+AllTrim(IIF(!Empty(dDtReceb),ConvDate(DTOS(dDtReceb)),Iif(oNF:_INFNFE:_VERSAO:TEXT >= "3.10",ConvDate(oNF:_InfNfe:_IDE:_DHEMI:Text),ConvDate(oNF:_InfNfe:_IDE:_DEMI:Text))))+" "+AllTrim(cDtHrRecCab),IIF(!Empty(cCodAutSef) .And. ((Val(SubStr(oNF:_INFNFE:_IDE:_SERIE:TEXT,1,3)) >= 900).And.(oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"2") .Or. (oNFe:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT)$"1|6|7",cCodAutSef+" "+AllTrim(IIF(!Empty(dDtReceb),ConvDate(DTOS(dDtReceb)),Iif(oNF:_INFNFE:_VERSAO:TEXT >= "3.10",ConvDate(oNF:_InfNfe:_IDE:_DHEMI:Text),ConvDate(oNF:_InfNfe:_IDE:_DEMI:Text))))+" "+AllTrim(cDtHrRecCab),TransForm(cChaveCont,"@r 9999 9999 9999 9999 9999 9999 9999 9999 9999"))),oFont08:oFont)
nFolha++

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Quadro 5                                                                ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
oDanfe:Box(nLine+164 - nAjustaNat,nBaseCol,nLine+189 - nAjustaNat,350)
oDanfe:Box(nLine+164 - nAjustaNat,350,nLine+189 - nAjustaNat,602)
oDanfe:Box(nLine+164 - nAjustaNat,602,nLine+189 - nAjustaNat,MAXBOXH+70)
oDanfe:Say(nLine+172 - nAjustaNat,nBaseTxt,"INSCRIÇÃO ESTADUAL",oFont08N:oFont)
oDanfe:Say(nLine+180 - nAjustaNat,nBaseTxt,IIf(Type("oEmitente:_IE:TEXT")<>"U",oEmitente:_IE:TEXT,""),oFont08:oFont)
oDanfe:Say(nLine+172 - nAjustaNat,360,"INSC.ESTADUAL DO SUBST.TRIB.",oFont08N:oFont)
oDanfe:Say(nLine+180 - nAjustaNat,362,IIf(Type("oEmitente:_IEST:TEXT")<>"U",oEmitente:_IEST:TEXT,""),oFont08:oFont)
oDanfe:Say(nLine+172 - nAjustaNat,612,"CNPJ/CPF",oFont08N:oFont)

Do Case
	Case Type("oEmitente:_CNPJ")=="O"
		cAux := TransForm(oEmitente:_CNPJ:TEXT,"@R! NN.NNN.NNN/NNNN-99")
	Case Type("oEmitente:_CPF")=="O"
		cAux := TransForm(oEmitente:_CPF:TEXT,"@r 999.999.999-99")
	OtherWise
		cAux := Space(14)
EndCase
oDanfe:Say(nLine+180 - nAjustaNat,612,cAux,oFont08:oFont)

Return()

Static Function GetXML(cIdEnt,aIdNFe,cModalidade, lJob)  
Local aRetorno		:= {}
Local aDados		:= {}

Local cURL			:= PadR(GetNewPar("MV_SPEDURL","http://localhost:8080/sped"),250)
Local cModel		:= "55"
Local nZ			:= 0
Local nCount		:= 0
Local oWS

default lJob := .F.
If Empty(cModalidade)    

	oWS := WsSpedCfgNFe():New()
	oWS:cUSERTOKEN := "TOTVS"
	oWS:cID_ENT    := cIdEnt
	oWS:nModalidade:= 0
	oWS:_URL       := AllTrim(cURL)+"/SPEDCFGNFe.apw"
	oWS:cModelo    := cModel 
	
	If oWS:CFGModalidade()
		cModalidade    := SubStr(oWS:cCfgModalidadeResult,1,1)
	Else
		cModalidade    := ""
	EndIf  
	
EndIf  

freeObj(oWs)
oWs := nil

For nZ := 1 To len(aIdNfe) 

    nCount++

	aDados := executeRetorna( aIdNfe[nZ], cIdEnt, ,lJob)
	
	if ( nCount == 10 )
		delClassIntF()
		nCount := 0
	endif
	
	aAdd(aRetorno,aDados)
	
Next nZ

Return(aRetorno)


Static Function ConvDate(cData)
Local dData
cData  := StrTran(cData,"-","")
dData  := Stod(cData)
Return PadR(StrZero(Day(dData),2)+ "/" + StrZero(Month(dData),2)+ "/" + StrZero(Year(dData),4),15)
  

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DANFE     ºAutor  ³Marcos Taranta      º Data ³  10/01/09   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³Pega uma posição (nTam) na string cString, e retorna o      º±±
±±º          ³caractere de espaço anterior.                               º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function EspacoAt(cString, nTam)

Local nRetorno := 0
Local nX       := 0

/**
* Caso a posição (nTam) for maior que o tamanho da string, ou for um valor
* inválido, retorna 0.
*/
If nTam > Len(cString) .Or. nTam < 1
	nRetorno := 0
	Return nRetorno
EndIf

/**
* Procura pelo caractere de espaço anterior a posição e retorna a posição
* dele.
*/
nX := nTam
While nX > 1
	If Substr(cString, nX, 1) == " "
		nRetorno := nX
		Return nRetorno
	EndIf
	
	nX--
EndDo

/**
* Caso não encontre nenhum caractere de espaço, é retornado 0.
*/
nRetorno := 0

Return nRetorno

//-----------------------------------------------------------------------
/*/{Protheus.doc} DanfeIT
Definicao do Box de Itens.
 
@author 	Roberto Souza
@since 		13/08/10
@version 	1.0
/*/
//-----------------------------------------------------------------------
Static Function DanfeIT(oDanfe, nLine, nBaseCol, nBaseTxt, nFolha, nFolhas, aColProd, aMensagem, nPosMsg, aTamCol)
	
	Local nAux  	:= 0
	Local nAux2 	:= 0
	Local nX    	:= 0
	Local cMVCODREG	:= Alltrim( SuperGetMV("MV_CODREG", ," ") )
	Local lVerso	:= (MV_PAR05 == 1 .And. (nFolha % 2) == 0)

	oBrush := TBrush():New( , CLR_BLACK )

	If nFolha == 1   

		nLine -= 2

		nBaseTxt -= 30
		If nMAXITEM <> 0
			If ( valType(oEntrega)=="U" ) .and. ( valType(oRetirada)=="U")
				oDanfe:FillRect({nLine+455,nBaseCol,nLine+574,nBaseCol+30},oBrush)
				oDanfe:Say(nLine+568,nBaseTxt+7,"DADOS DO PRODUTO / SERVIÇO",oFont08N:oFont, ,CLR_WHITE , 270 )
			ElseIf ( valType(oEntrega)=="O" ) .or. ( valType(oRetirada)=="O")
				oDanfe:FillRect({nLine+522,nBaseCol,nLine+592,nBaseCol+30},oBrush)
				oDanfe:Say(nLine+587,nBaseTxt+7,"DADOS DO PRODUTO/",oFont08N:oFont, ,CLR_WHITE , 270 )
				oDanfe:Say(nLine+579,nBaseTxt+14,"SERVIÇO",oFont08N:oFont, ,CLR_WHITE , 270 )
			Endif

			nBaseTxt += 30 
			aColProd := {}
			nAux     := nBaseCol + 30
			AADD(aColProd, {nAux, nAux + aTamCol[1]}) //"COD. PROD"
			nAux += aTamCol[1]
			AADD(aColProd, {nAux, nAux + aTamCol[2]}) // "DESCRIÇÃO DO PRODUTOS/SERVIÇOS"
			nAux += aTamCol[2]
			AADD(aColProd, {nAux, nAux + aTamCol[3]}) // "NCM/SH"
			nAux += aTamCol[3]
			AADD(aColProd, {nAux, nAux + aTamCol[4]}) // "CST"
			nAux += aTamCol[4]
			AADD(aColProd, {nAux, nAux + aTamCol[5]}) // "CFOP"
			nAux += aTamCol[5]
			AADD(aColProd, {nAux, nAux + aTamCol[6]}) // "UN"
			nAux += aTamCol[6]
			AADD(aColProd, {nAux, nAux + aTamCol[7]}) // "QUANT."
			nAux += aTamCol[7]
			AADD(aColProd, {nAux, nAux + aTamCol[8]}) // "V.UNITARIO"
			nAux += aTamCol[8]
			AADD(aColProd, {nAux, nAux + aTamCol[9]}) // "VLR TOTAL"
			nAux += aTamCol[9]
			//	AADD(aColProd, {nAux, nAux + aTamCol[10]}) // "PER DESC"
			//	nAux += aTamCol[10]
			AADD(aColProd, {nAux, nAux + aTamCol[10]}) // "VLR DESC"
			nAux += aTamCol[10]
			AADD(aColProd, {nAux, nAux + aTamCol[11]}) // "VLR LIQ"
			nAux += aTamCol[11]
			AADD(aColProd, {nAux, nAux + aTamCol[12]}) // "TOT LIQ"
			nAux += aTamCol[12]
			AADD(aColProd, {nAux, nAux + aTamCol[13]}) // "BC.ICMS"
			nAux += aTamCol[13]
			AADD(aColProd, {nAux, nAux + aTamCol[14]}) // "BC.ICMS ST"
			nAux += aTamCol[14]
			AADD(aColProd, {nAux, nAux + aTamCol[15]}) // "VLR ICMS"
			nAux += aTamCol[15]
			AADD(aColProd, {nAux, nAux + aTamCol[16]}) // "VLR ICMS ST"
			nAux += aTamCol[16]
			AADD(aColProd, {nAux, nAux + aTamCol[17]}) // "VALOR IPI"
			nAux += aTamCol[17]
			AADD(aColProd, {nAux, nAux + aTamCol[18]}) // "ICMS"
			nAux += aTamCol[18]
			AADD(aColProd, {nAux, nAux + aTamCol[19]}) // "IPI"
		

			oDanfe:Box(nLine+454+nAjustaPro,nBaseCol+31,nLine+574,MAXBOXH+70)
			nAux := nBaseCol + 30
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[1])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"COD. PROD", oFont08N:oFont)
			nAux += aTamCol[1]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[2])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"DESCR PROD", oFont08N:oFont)
			nAux += aTamCol[2]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[3])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"NCM/SH", oFont08N:oFont)
			nAux += aTamCol[3]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[4])
			If cMVCODREG == "1"
				oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"CSOSN", oFont08N:oFont)
			Else
				oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"CST", oFont08N:oFont)
			Endif
			nAux += aTamCol[4]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[5])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"CFOP", oFont08N:oFont)
			nAux += aTamCol[5]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[6])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"UN", oFont08N:oFont)
			nAux += aTamCol[6]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[7])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"QUANT.", oFont08N:oFont)
			nAux += aTamCol[7]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[8])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"V.UNITARIO", oFont08N:oFont)
			nAux += aTamCol[8]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[9])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"VLR TOTAL", oFont08N:oFont)
			nAux += aTamCol[9]
			//	oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[10])
			//	oDanfe:Say(nLine+462, nAux + 2,"DESC", oFont08N:oFont)
			//	nAux += aTamCol[10]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[10])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"VLR DESC", oFont08N:oFont)
			nAux += aTamCol[10]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[11])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"V.UNI LIQ", oFont08N:oFont)
			nAux += aTamCol[11]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[12])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"TOTAL LIQ", oFont08N:oFont)
			nAux += aTamCol[12]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[13])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"BC.ICMS", oFont08N:oFont)
			nAux += aTamCol[13]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[14])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"BC.ICMS ST", oFont08N:oFont)
			nAux += aTamCol[14]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[15])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"VLR ICMS", oFont08N:oFont)
			nAux += aTamCol[15]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[16])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"VLR ICMS ST", oFont08N:oFont)
			nAux += aTamCol[16]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[17])
			oDanfe:Say(nLine+462+nAjustaPro, nAux + 2,"VALOR IPI", oFont08N:oFont)
			nAux  += aTamCol[17]
			nAux2 := nAux
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[18])
			oDanfe:Say(nLine+468+nAjustaPro, nAux + 2,"ICMS", oFont08N:oFont)
			nAux += aTamCol[18]
			oDanfe:Box(nLine+454+nAjustaPro, nAux, nLine+469+nAjustaPro, nAux + aTamCol[19])
			oDanfe:Say(nLine+468+nAjustaPro, nAux + 2,"IPI", oFont08N:oFont)
			oDanfe:Box(nLine+454+nAjustaPro, nAux2, nLine+461+nAjustaPro, nAux2 + aTamCol[18] + aTamCol[19])
			oDanfe:Say(nLine+460+nAjustaPro, nAux2 + 2,"ALIQUOTA", oFont08N:oFont)
		
			For Nx :=1 to Len(aColProd)
				If ( valType(oEntrega)=="U" ) .and. ( valType(oRetirada)=="U")
					oDanfe:Box(nLine+469,aColProd[nX][1],nLine+575,aColProd[nX][2])
				ElseIf ( valType(oEntrega)=="O" ) .or. ( valType(oRetirada)=="O")
					oDanfe:Box(nLine+469+nAjustaPro,aColProd[nX][1],nLine+575+13,aColProd[nX][2])		
				Endif
			Next
		EndIf
	Else
									
		If nPosMsg > 0 .Or. lVerso
			nLine -= 265

			oDanfe:FillRect({nLine+455,nBaseCol,397,nBaseCol+30},oBrush)
			oDanfe:Say(360,nBaseTxt+7,"DADOS DO PRODUTO / SERVIÇO",oFont08N:oFont, , CLR_WHITE, 270 )
			nBaseTxt += 30 
			aColProd := {}
			nAux     := nBaseCol + 30
			AADD(aColProd, {nAux, nAux + aTamCol[1]}) //"COD. PROD"
			nAux += aTamCol[1]
			AADD(aColProd, {nAux, nAux + aTamCol[2]}) // "DESCRIÇÃO DO PRODUTOS/SERVIÇOS"
			nAux += aTamCol[2]
			AADD(aColProd, {nAux, nAux + aTamCol[3]}) // "NCM/SH"
			nAux += aTamCol[3]
			AADD(aColProd, {nAux, nAux + aTamCol[4]}) // "CST"
			nAux += aTamCol[4]
			AADD(aColProd, {nAux, nAux + aTamCol[5]}) // "CFOP"
			nAux += aTamCol[5]
			AADD(aColProd, {nAux, nAux + aTamCol[6]}) // "UN"
			nAux += aTamCol[6]
			AADD(aColProd, {nAux, nAux + aTamCol[7]}) // "QUANT."
			nAux += aTamCol[7]
			AADD(aColProd, {nAux, nAux + aTamCol[8]}) // "V.UNITARIO"
			nAux += aTamCol[8]
			AADD(aColProd, {nAux, nAux + aTamCol[9]}) // "VLR TOTAL"
			nAux += aTamCol[9]
			AADD(aColProd, {nAux, nAux + aTamCol[10]}) // "VLR DESC"
			nAux += aTamCol[10]
			AADD(aColProd, {nAux, nAux + aTamCol[11]}) // "VLR LIQ"
			nAux += aTamCol[11]
			AADD(aColProd, {nAux, nAux + aTamCol[12]}) // "TOT LIQ"
			nAux += aTamCol[12]
			AADD(aColProd, {nAux, nAux + aTamCol[13]}) // "BC.ICMS"
			nAux += aTamCol[13]
			AADD(aColProd, {nAux, nAux + aTamCol[14]}) // "BC.ICMS ST"
			nAux += aTamCol[14]
			AADD(aColProd, {nAux, nAux + aTamCol[15]}) // "VLR ICMS"
			nAux += aTamCol[15]
			AADD(aColProd, {nAux, nAux + aTamCol[16]}) // "VLR ICMS ST"
			nAux += aTamCol[16]
			AADD(aColProd, {nAux, nAux + aTamCol[17]}) // "VALOR IPI"
			nAux += aTamCol[17]
			AADD(aColProd, {nAux, nAux + aTamCol[18]}) // "ICMS"
			nAux += aTamCol[18]
			AADD(aColProd, {nAux, nAux + aTamCol[19]}) // "IPI"
		
			oDanfe:Box(nLine+454,nBaseCol+31,398,MAXBOXH+70)
			nAux := nBaseCol + 30
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[1])
			oDanfe:Say(nLine+462, nAux + 2,"COD. PROD", oFont08N:oFont)
			nAux += aTamCol[1]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[2])
			oDanfe:Say(nLine+462, nAux + 2,"DESCR PROD", oFont08N:oFont)
			nAux += aTamCol[2]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[3])
			oDanfe:Say(nLine+462, nAux + 2,"NCM/SH", oFont08N:oFont)
			nAux += aTamCol[3]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[4])

			If cMVCODREG == "1"
				oDanfe:Say(nLine+462, nAux + 2,"CSOSN", oFont08N:oFont)
			Else
				oDanfe:Say(nLine+462, nAux + 2,"CST", oFont08N:oFont)
			Endif
			nAux += aTamCol[4]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[5])
			oDanfe:Say(nLine+462, nAux + 2,"CFOP", oFont08N:oFont)
			nAux += aTamCol[5]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[6])
			oDanfe:Say(nLine+462, nAux + 2,"UN", oFont08N:oFont)
			nAux += aTamCol[6]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[7])
			oDanfe:Say(nLine+462, nAux + 2,"QUANT.", oFont08N:oFont)
			nAux += aTamCol[7]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[8])
			oDanfe:Say(nLine+462, nAux + 2,"V.UNITARIO", oFont08N:oFont)
			nAux += aTamCol[8]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[9])
			oDanfe:Say(nLine+462, nAux + 2,"VLR TOTAL", oFont08N:oFont)
			nAux += aTamCol[9]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[10])
			oDanfe:Say(nLine+462, nAux + 2,"VLR DESC", oFont08N:oFont)
			nAux += aTamCol[10]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[11])
			oDanfe:Say(nLine+462, nAux + 2,"V.UNI LIQ", oFont08N:oFont)
			nAux += aTamCol[11]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[12])
			oDanfe:Say(nLine+462, nAux + 2,"TOTAL LIQ", oFont08N:oFont)
			nAux += aTamCol[12]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[13])
			oDanfe:Say(nLine+462, nAux + 2,"BC.ICMS", oFont08N:oFont)
			nAux += aTamCol[13]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[14])
			oDanfe:Say(nLine+462, nAux + 2,"BC.ICMS ST", oFont08N:oFont)
			nAux += aTamCol[14]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[15])
			oDanfe:Say(nLine+462, nAux + 2,"VLR ICMS", oFont08N:oFont)
			nAux += aTamCol[15]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[16])
			oDanfe:Say(nLine+462, nAux + 2,"VLR ICMS ST", oFont08N:oFont)
			nAux += aTamCol[16]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[17])
			oDanfe:Say(nLine+462, nAux + 2,"VALOR IPI", oFont08N:oFont)
			nAux  += aTamCol[17]
			nAux2 := nAux
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[18])
			oDanfe:Say(nLine+468, nAux + 2,"ICMS", oFont08N:oFont)
			nAux += aTamCol[18]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[19])
			oDanfe:Say(nLine+468, nAux + 2,"IPI", oFont08N:oFont)
			oDanfe:Box(nLine+454, nAux2, nLine+461, nAux2 + aTamCol[18] + aTamCol[19])
			oDanfe:Say(nLine+460, nAux2 + 2,"ALIQUOTA", oFont08N:oFont)
			
			For Nx :=1 to Len(aColProd)
				oDanfe:Box(nLine+469,aColProd[nx][1],398,aColProd[nx][2])	
			Next
			nLine -= 257

		Else
			nLine -= 265
		
			oDanfe:FillRect({nLine+455,nBaseCol,MAXBOXV-1,nBaseCol+30},oBrush)
			oDanfe:Say(nLine+768,nBaseTxt+7,"DADOS DO PRODUTO / SERVIÇO",oFont08N:oFont, , CLR_WHITE, 270 )
			nBaseTxt += 30 
			aColProd := {}
			nAux     := nBaseCol + 30
			AADD(aColProd, {nAux, nAux + aTamCol[1]}) //"COD. PROD"
			nAux += aTamCol[1]
			AADD(aColProd, {nAux, nAux + aTamCol[2]}) // "DESCRIÇÃO DO PRODUTOS/SERVIÇOS"
			nAux += aTamCol[2]
			AADD(aColProd, {nAux, nAux + aTamCol[3]}) // "NCM/SH"
			nAux += aTamCol[3]
			AADD(aColProd, {nAux, nAux + aTamCol[4]}) // "CST"
			nAux += aTamCol[4]
			AADD(aColProd, {nAux, nAux + aTamCol[5]}) // "CFOP"
			nAux += aTamCol[5]
			AADD(aColProd, {nAux, nAux + aTamCol[6]}) // "UN"
			nAux += aTamCol[6]
			AADD(aColProd, {nAux, nAux + aTamCol[7]}) // "QUANT."
			nAux += aTamCol[7]
			AADD(aColProd, {nAux, nAux + aTamCol[8]}) // "V.UNITARIO"
			nAux += aTamCol[8]
			AADD(aColProd, {nAux, nAux + aTamCol[9]}) // "VLR TOTAL"
			nAux += aTamCol[9]
			AADD(aColProd, {nAux, nAux + aTamCol[10]}) // "VLR DESC"
			nAux += aTamCol[10]
			AADD(aColProd, {nAux, nAux + aTamCol[11]}) // "VLR LIQ"
			nAux += aTamCol[11]
			AADD(aColProd, {nAux, nAux + aTamCol[12]}) // "TOT LIQ"
			nAux += aTamCol[12]
			AADD(aColProd, {nAux, nAux + aTamCol[13]}) // "BC.ICMS"
			nAux += aTamCol[13]
			AADD(aColProd, {nAux, nAux + aTamCol[14]}) // "BC.ICMS ST"
			nAux += aTamCol[14]
			AADD(aColProd, {nAux, nAux + aTamCol[15]}) // "VLR ICMS"
			nAux += aTamCol[15]
			AADD(aColProd, {nAux, nAux + aTamCol[16]}) // "VLR ICMS ST"
			nAux += aTamCol[16]
			AADD(aColProd, {nAux, nAux + aTamCol[17]}) // "VALOR IPI"
			nAux += aTamCol[17]
			AADD(aColProd, {nAux, nAux + aTamCol[18]}) // "ICMS"
			nAux += aTamCol[18]
			AADD(aColProd, {nAux, nAux + aTamCol[19]}) // "IPI"
		
			oDanfe:Box(nLine+454,nBaseCol+31,nLine+675,MAXBOXH+70)
		
			nAux := nBaseCol + 30
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[1])
			oDanfe:Say(nLine+462, nAux + 2,"COD. PROD", oFont08N:oFont)
			nAux += aTamCol[1]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[2])
			oDanfe:Say(nLine+462, nAux + 2,"DESCR PROD", oFont08N:oFont)
			nAux += aTamCol[2]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[3])
			oDanfe:Say(nLine+462, nAux + 2,"NCM/SH", oFont08N:oFont)
			nAux += aTamCol[3]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[4])

			If cMVCODREG == "1"
				oDanfe:Say(nLine+462, nAux + 2,"CSOSN", oFont08N:oFont)
			Else
				oDanfe:Say(nLine+462, nAux + 2,"CST", oFont08N:oFont)
			Endif
			nAux += aTamCol[4]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[5])
			oDanfe:Say(nLine+462, nAux + 2,"CFOP", oFont08N:oFont)
			nAux += aTamCol[5]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[6])
			oDanfe:Say(nLine+462, nAux + 2,"UN", oFont08N:oFont)
			nAux += aTamCol[6]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[7])
			oDanfe:Say(nLine+462, nAux + 2,"QUANT.", oFont08N:oFont)
			nAux += aTamCol[7]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[8])
			oDanfe:Say(nLine+462, nAux + 2,"V.UNITARIO", oFont08N:oFont)
			nAux += aTamCol[8]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[9])
			oDanfe:Say(nLine+462, nAux + 2,"VLR TOTAL", oFont08N:oFont)
			nAux += aTamCol[9]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[10])
			oDanfe:Say(nLine+462, nAux + 2,"VLR DESC", oFont08N:oFont)
			nAux += aTamCol[10]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[11])
			oDanfe:Say(nLine+462, nAux + 2,"V.UNI LIQ", oFont08N:oFont)
			nAux += aTamCol[11]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[12])
			oDanfe:Say(nLine+462, nAux + 2,"TOTAL LIQ", oFont08N:oFont)
			nAux += aTamCol[12]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[13])
			oDanfe:Say(nLine+462, nAux + 2,"BC.ICMS", oFont08N:oFont)
			nAux += aTamCol[13]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[14])
			oDanfe:Say(nLine+462, nAux + 2,"BC.ICMS ST", oFont08N:oFont)
			nAux += aTamCol[14]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[15])
			oDanfe:Say(nLine+462, nAux + 2,"VLR ICMS", oFont08N:oFont)
			nAux += aTamCol[15]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[16])
			oDanfe:Say(nLine+462, nAux + 2,"VLR ICMS ST", oFont08N:oFont)
			nAux += aTamCol[16]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[17])
			oDanfe:Say(nLine+462, nAux + 2,"VALOR IPI", oFont08N:oFont)
			nAux  += aTamCol[17]
			nAux2 := nAux
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[18])
			oDanfe:Say(nLine+468, nAux + 2,"ICMS", oFont08N:oFont)
			nAux += aTamCol[18]
			oDanfe:Box(nLine+454, nAux, nLine+469, nAux + aTamCol[19])
			oDanfe:Say(nLine+468, nAux + 2,"IPI", oFont08N:oFont)
			oDanfe:Box(nLine+454, nAux2, nLine+461, nAux2 + aTamCol[18] + aTamCol[19])
			oDanfe:Say(nLine+460, nAux2 + 2,"ALIQUOTA", oFont08N:oFont)
					
			For Nx :=1 to Len(aColProd)
				oDanfe:Box(nLine+469,aColProd[nx][1],MAXBOXV,aColProd[nx][2])	
			Next
			nLine -= 257	
			
		EndIf	

	EndIf

Return

//-----------------------------------------------------------------------
/*/{Protheus.doc} DanfeInfC
Definicao do Box de Informações complementares.
 
@author 	Roberto Souza
@since 		13/08/10
@version 	1.0
/*/
//-----------------------------------------------------------------------
Static Function DanfeInfC(oDanfe,aMensagem,nBaseTxt,nBaseCol,nLine,nPosMsg, nFolha,lComplemento )

	Local cLogoTotvs 		:= "Powered_by_TOTVS.bmp"
	Local cStartPath 		:= GetSrvProfString("Startpath","")
	Local nPosAdicionais	:= 0
	Local nX				:= 0	

	Default lComplemento := .F.

	oBrush := TBrush():New( , CLR_BLACK )

	If nFolha == 1

		nBaseTxt -= 30 
		//oDanfe:Box(nLine+597,nBaseCol,MAXBOXV,nBaseCol+30)
		oDanfe:FillRect({nLine+597+nAjustaDad,nBaseCol,MAXBOXV-1,nBaseCol+30},oBrush)
		oBrush:End()
		
		oDanfe:Say(MAXBOXV-25,nBaseTxt+1,"DADOS",oFont08N:oFont, , CLR_WHITE, 270 )
		oDanfe:Say(MAXBOXV-13,nBaseTxt+11,"ADICIONAIS"    ,oFont08N:oFont, ,CLR_WHITE , 270 )
		nBaseTxt += 30 
		
		oDanfe:Box(nLine+597+nAjustaDad,nBaseCol+30,MAXBOXV,622)
		oDanfe:Say(nLine+606+nAjustaDad,nBaseTxt,"INFORMAÇÕES COMPLEMENTARES",oFont08N:oFont)
		
		
		nLenMensagens:= Len(aMensagem)
		nLin:= nLine+618+nAjustaDad
		
		For nX := 1 To Min(nLenMensagens, MAXMSG)
			if aMensagem[nX][2]
				oDanfe:Say(nLin,nBaseTxt,aMensagem[nX][1],oFont07N:oFont)
			else
				oDanfe:Say(nLin,nBaseTxt,aMensagem[nX][1],oFont07:oFont)
			endIf
			nLin:= nLin+10
		Next nX
		
		If Nx <= nLenMensagens 
			nPosMsg := Nx
		else 
			nPosMsg := 0 
		EndIf 
		
		//oDanfe:Box(nLine+597,622,MAXBOXV,MAXBOXH+70)
		oDanfe:Box(nLine+597+nAjustaDad,622,MAXBOXV,MAXBOXH+70)
		oDanfe:Say(nLine+606+nAjustaDad,632,"RESERVADO AO FISCO",oFont08N:oFont)

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Logotipo Rodape
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ												
		if file(cLogoTotvs) .or. Resource2File ( cLogoTotvs, cStartPath+cLogoTotvs )
			oDanfe:SayBitmap(MAXBOXV+1,752,cLogoTotvs,120,20)
		endif	
		nLenMensagens:= Len(aResFisco)
		nLin:= nLine+618   
		For nX := 1 To Min(nLenMensagens, MAXMSG)
			oDanfe:Say(nLin,632,aResFisco[nX],oFont08:oFont)
			nLin:= nLin+10
		Next

	ElseIf nFolha >= 2

		if lComplemento
			nLine -= 208
			nBaseTxt +=30 
			nPosAdicionais := MAXBOXV-239
		else
			nLine :=  0
			nPosAdicionais := MAXBOXV-25
		endif	
		
		nBaseTxt -= 30 
		oDanfe:Box(nLine+597,nBaseCol,MAXBOXV,nBaseCol+30)
		oDanfe:FillRect({nLine+398,nBaseCol,MAXBOXV-1,nBaseCol+30},oBrush)
		oBrush:End()
		
		oDanfe:Say(nPosAdicionais,nBaseTxt+1,"DADOS",oFont08N:oFont, ,CLR_WHITE,270)
		oDanfe:Say(nPosAdicionais+12,nBaseTxt+11,"ADICIONAIS"    ,oFont08N:oFont, ,CLR_WHITE , 270 )
		nBaseTxt += 30 
		
		oDanfe:Box(nLine+397,nBaseCol+30,MAXBOXV,622)
		if lComplemento
			nBaseTxt += 30
		endif
		oDanfe:Say(nLine+406,nBaseTxt,"INFORMAÇÕES COMPLEMENTARES",oFont08N:oFont)
		
		nLenMensagens:= Len(aMensagem)
		nLin:= nLine+416

		For nX := nPosMsg To Min(nLenMensagens,(nPosMsg-1)+MAXMSG2)
			if aMensagem[nX][2]
				oDanfe:Say(nLin,nBaseTxt,aMensagem[nX][1],oFont07N:oFont)
			else
				oDanfe:Say(nLin,nBaseTxt,aMensagem[nX][1],oFont07:oFont)
			endIf
			nLin:= nLin+10
		Next nX
			
		If Nx <= nLenMensagens 
			nPosMsg := Nx
		else 
			nPosMsg := 0 
		EndIf 
		
		oDanfe:Box(nLine+397,622,MAXBOXV,MAXBOXH+70)
		oDanfe:Say(nLine+406,632,"RESERVADO AO FISCO",oFont08N:oFont)

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Logotipo Rodape
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ												
		if file(cLogoTotvs) .or. Resource2File ( cLogoTotvs, cStartPath+cLogoTotvs )
			oDanfe:SayBitmap(MAXBOXV+1,752,cLogoTotvs,120,20)
		endif	
	EndIf

Return

 /*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DANFE     ºAutor  ³Fabio Santana	     º Data ³  04/10/10   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³Converte caracteres espceiais						          º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
*/

STATIC FUNCTION NoChar(cString,lConverte) 

Default lConverte := .F.

If lConverte
	cString := (StrTran(cString,"&lt;","<"))  
	cString := (StrTran(cString,"&gt;",">"))
	cString := (StrTran(cString,"&amp;","&"))
	cString := (StrTran(cString,"&quot;",'"'))
	cString := (StrTran(cString,"&#39;","'"))
EndIf	
		
Return(cString)	


/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DANFEIII  ºAutor  ³Microsiga           º Data ³  12/17/10   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³                                                            º±±
±±º          ³                                                            º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
STATIC FUNCTION MaxCod(cString,nTamanho)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Tratamento para saber quantos caracteres irão caber na linha ³
//³ visto que letras ocupam mais espaço do que os números.      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

Local nMax	:= 0
Local nY   	:= 0
Default nTamanho := 40

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
/*/{Protheus.doc} RetTamCol
Retorna um array do mesmo tamanho do array de entrada, contendo as
medidas dos maiores textos para cálculo de colunas.

@author Marcos Taranta
@since 24/05/2011
@version 1.0 

@param  aCabec     Array contendo as strings de cabeçalho das colunas
        aValores   Array contendo os valores que serão populados nas
                   colunas.
        oPrinter   Objeto de impressão instanciado para utilizar o método
                   nativo de cálculo de tamanho de texto.
        oFontCabec Objeto da fonte que será utilizada no cabeçalho.
        oFont      Objeto da fonte que será utilizada na impressão.

@return aTamCol  Array contendo os tamanhos das colunas baseados nos
                 valores.
/*/
//-----------------------------------------------------------------------
Static Function RetTamCol(aCabec, aValores, oPrinter, oFontCabec, oFont)
	
	Local aTamCol    := {}
	Local nAux       := 0
	Local nX         := 0

	/* Valores fixados, devido erro de impr. quando S.O está com visualização <> de 100% 
	*/		
		aTamCol := {45,;
					69,;
					39,;
					iif(aCabec[4] == "CSOSN", 22, 19),; // CST/CSON
					23,;
					20,;
					33,;
					49,;
					46,;
					40,;
					41,;
					45,;
					39,;
					iif(aCabec[4] == "CSOSN", 45, 46),; // BC.ICMS ST 
					40,;
					iif(aCabec[4] == "CSOSN", 49, 51),; // VLR ICMS ST
					42,;
					34,;
					30}

	// Workaround para o método FWMSPrinter:GetTextWidth() na coluna UN
	aTamCol[6] += 5
	
	// Checa se os campos completam a página, senão joga o resto na coluna da
	//   descrição de produtos/serviços
	nAux := 0
	For nX := 1 To Len(aTamCol)
		
		nAux += aTamCol[nX]
		
	Next nX
	If nAux < MAXBOXH
		aTamCol[2] += MAXBOXH - 30 - nAux
	EndIf
   	If nAux > MAXBOXH               
		aTamCol[2] -= nAux - MAXBOXH - 30
	EndIf

Return aTamCol

//-----------------------------------------------------------------------
/*/{Protheus.doc} RetTamTex
Retorna o tamanho em pixels de uma string. (Workaround para o GetTextWidth)

@author Marcos Taranta
@since 24/05/2011
@version 1.0 

@param  cTexto   Texto a ser medido.
        oFont    Objeto instanciado da fonte a ser utilizada.
        oPrinter Objeto de impressão instanciado.

@return nTamanho Tamanho em pixels da string.
/*/
//-----------------------------------------------------------------------
Static Function RetTamTex(cTexto, oFont, oPrinter)
	
	Local nTamanho := 0
	//Local oFontSize:= FWFontSize():new()
	Local cAux := ""
		
	Local cValor := "0123456789"
	Local cVirgPonto := ",."
	Local cPerc := "%"	
	Local nX := 0
	
	//nTamanho := oPrinter:GetTextWidth(cTexto, oFont)
	//nTamanho := oFontSize:getTextWidth( cTexto, oFont:Name, oFont:nWidth, oFont:Bold, oFont:Italic )
	/*O calculo abaixo é o mesmo realizado pela oFontSize:getTextWidth
	Retorna 5 para numeros (0123456789), 2 para virgula e ponto (, .) e 7 para percentual (%)
	O ajuste foi realizado para diminuir o tempo na impressão de um danfe com muitos itens*/
	For nX:= 1 to len(cTexto)
		cAux:= Substr(cTexto,nX,1)
		If cAux $ cValor
			nTamanho += 5
		ElseIf cAux $ cVirgPonto
			nTamanho += 2
		ElseIf cAux $ cPerc
			nTamanho += 7
		EndIf		
	Next nX
	
	nTamanho := Round(nTamanho, 0)
	
Return nTamanho

//-----------------------------------------------------------------------
/*/{Protheus.doc} PosQuebrVal
Retorna a posição onde um valor deve ser quebrado

@author Marcos Taranta
@since 27/05/2011
@version 1.0 

@param  cTexto Texto a ser medido.

@return nPos   Posição aonde o valor deve ser quebrado.
/*/
//-----------------------------------------------------------------------
Static Function PosQuebrVal(cTexto)
	
	Local nPos := 0
	
	If Empty(cTexto)
		Return 0
	EndIf
	
	If Len(cTexto) <= MAXVALORC
		Return Len(cTexto)
	EndIf
	
	If SubStr(cTexto, MAXVALORC, 1) $ ",."
		nPos := MAXVALORC - 2
	Else
		nPos := MAXVALORC
	EndIf
	
Return nPos

//-----------------------------------------------------------------------
/*/{Protheus.doc} MontaEnd
Retorna o endereço completo do cliente (Logradouro + Número + Complemento)

@author Renan Franco
@since 11/07/2019
@version 1.0

@param  oMontaEnd	 Objeto que possui _xLgr, _xcpl e _xNRO.

@return cEndereco   Endereço concatenado. Ex.: AV BRAZ LEME, 1000, SÊNECA MALL
/*/
//-----------------------------------------------------------------------
Static Function MontaEnd(oMontaEnd)

	Local lConverte		:= GetNewPar("MV_CONVERT",.F.)
	Local cEndereco		:= ""

	Default oMontaEnd	:= Nil

	Private oEnd		:= oMontaEnd
	
	if  oEnd <> Nil .and. ValType(oEnd)=="O"

		cEndereco := NoChar(oEnd:_Xlgr:Text,lConverte) 
	
		If  " SN" $ (UPPER (oEnd:_Xlgr:Text)) .Or. ",SN" $ (UPPER (oEnd:_Xlgr:Text)) .Or. "S/N" $ (UPPER (oEnd:_Xlgr:Text))
            cEndereco += IIf(type("oEnd:_xcpl") == "O", ", " + NoChar(oEnd:_xcpl:Text,lConverte), " ")
		Else
            cEndereco += ", " + NoChar(oEnd:_NRO:Text,lConverte) + IIf(type("oEnd:_xcpl") == "O", ", " + NoChar(oEnd:_xcpl:Text,lConverte), " ")
		Endif

	Endif	

Return cEndereco

//-----------------------------------------------------------------------
/*/{Protheus.doc} executeRetorna
Executa o retorna de notas

@author Henrique Brugugnoli
@since 17/01/2013
@version 1.0 

@param  cID ID da nota que sera retornado

@return aRetorno   Array com os dados da nota
/*/
//-----------------------------------------------------------------------
static function executeRetorna( aNfe, cIdEnt, lUsacolab, lJob)

Local aRetorno		:= {}
Local aDados		:= {} 
Local aIdNfe		:= {}
Local aWsErro		:= {}

Local cAviso		:= "" 
Local cDHRecbto		:= ""
Local cDtHrRec		:= ""
Local cDtHrRec1		:= ""
Local cErro			:= "" 
Local cModTrans		:= ""
Local cProtDPEC		:= ""
Local cProtocolo	:= ""
Local cRetDPEC		:= ""
Local cRetorno		:= ""
Local cCodRetNFE	:= ""
Local cMsgNFE		:= ""
Local cMsgRet		:= ""
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

if !lUsacolab

	oWS:= WSNFeSBRA():New()
	oWS:cUSERTOKEN        := "TOTVS"
	oWS:cID_ENT           := cIdEnt
	oWS:nDIASPARAEXCLUSAO := 0
	oWS:_URL 			  := AllTrim(cURL)+"/NFeSBRA.apw"
	oWS:oWSNFEID          := NFESBRA_NFES2():New()
	oWS:oWSNFEID:oWSNotas := NFESBRA_ARRAYOFNFESID2():New()  
	
	aadd(aRetorno,{"","",aIdNfe[nZ][4]+aIdNfe[nZ][5],"","","",CToD(""),"","","",""})
	
	aadd(oWS:oWSNFEID:oWSNotas:oWSNFESID2,NFESBRA_NFESID2():New())
	Atail(oWS:oWSNFEID:oWSNotas:oWSNFESID2):cID := aIdNfe[nZ][4]+aIdNfe[nZ][5]
	
	If oWS:RETORNANOTASNX()

		If Len(oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5) > 0
			For nX := 1 To Len(oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5)
				cRetorno        := oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5[nX]:oWSNFE:CXML
				cProtocolo      := oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5[nX]:oWSNFE:CPROTOCOLO								
				cDHRecbto  		:= oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5[nX]:oWSNFE:CXMLPROT
				oNFeRet			:= XmlParser(cRetorno,"_",@cAviso,@cErro)
				cModTrans		:= IIf(ValAtrib("oNFeRet:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT") <> "U",IIf (!Empty("oNFeRet:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT"),oNFeRet:_NFE:_INFNFE:_IDE:_TPEMIS:TEXT,1),1)
				cCodStat		:= ""
				If ValType(oWs:OWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5[nX]:OWSDPEC)=="O"
					cRetDPEC        := oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5[nX]:oWSDPEC:CXML
					cProtDPEC       := oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5[nX]:oWSDPEC:CPROTOCOLO
				EndIf
				
	
				//Tratamento para gravar a hora da transmissao da NFe
				If !Empty(cProtocolo)
					oDHRecbto		:= XmlParser(cDHRecbto,"","","")
					cDtHrRec		:= IIf(ValAtrib("oDHRecbto:_ProtNFE:_INFPROT:_DHRECBTO:TEXT")<>"U",oDHRecbto:_ProtNFE:_INFPROT:_DHRECBTO:TEXT,"")
					nDtHrRec1		:= RAT("T",cDtHrRec)
					cMsgRet 		:= IIf(ValAtrib("oDHRecbto:_ProtNFE:_INFPROT:_XMSG:TEXT")<>"U",oDHRecbto:_ProtNFE:_INFPROT:_XMSG:TEXT,"")
					cCodStat		:= IIf(ValAtrib("oDHRecbto:_ProtNFE:_INFPROT:_CSTAT:TEXT")<>"U",oDHRecbto:_ProtNFE:_INFPROT:_CSTAT:TEXT,"")
					If nDtHrRec1 <> 0
						cDtHrRec1   :=	SubStr(cDtHrRec,nDtHrRec1+1)
						dDtRecib	:=	SToD(StrTran(SubStr(cDtHrRec,1,AT("T",cDtHrRec)-1),"-",""))
					EndIf
					
					AtuSF2Hora(cDtHrRec1,aIdNFe[nZ][5]+aIdNFe[nZ][4]+aIdNFe[nZ][6]+aIdNFe[nZ][7])
					
				EndIf
	
				nY := aScan(aIdNfe,{|x| x[4]+x[5] == SubStr(oWs:oWSRETORNANOTASNXRESULT:OWSNOTAS:OWSNFES5[nX]:CID,1,Len(x[4]+x[5]))})
	
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
					aRetorno[nY][1] := cProtocolo
					aRetorno[nY][2] := cRetorno
					aRetorno[nY][4] := cRetDPEC
					aRetorno[nY][5] := cProtDPEC
					aRetorno[nY][6] := cDtHrRec1
					aRetorno[nY][7] := dDtRecib
					aRetorno[nY][8] := cModTrans
					aRetorno[nY][9] := cCodRetNFE
					aRetorno[nY][10]:= cMsgNFE
					aRetorno[nY][11]:= cMsgRet
					
				EndIf
				cRetDPEC := ""
				cProtDPEC:= ""
				freeObj(oDHRecbto)
				oDHRecbto := Nil
				freeObj(oNFeRet)
				oNFeRet	:= Nil
				delClassIntF()
			Next nX
		EndIf
	Elseif !lJob
		Aviso("DANFE",IIf(Empty(GetWscError(3)),GetWscError(1),GetWscError(3)),{"OK"},3)
	EndIf 
else
	oDoc 			:= ColaboracaoDocumentos():new()		
	oDoc:cModelo	:= "NFE"
	oDoc:cTipoMov	:= "1"									
	oDoc:cIDERP	:= aIdNfe[nZ][4]+aIdNfe[nZ][5]+FwGrpCompany()+FwCodFil()
	
	aadd(aRetorno,{"","",aIdNfe[nZ][4]+aIdNfe[nZ][5],"","","",CToD(""),"","","",""})
	
	if odoc:consultar()
		aDados := ColDadosNf(1)
		
		if !Empty(oDoc:cXMLRet)
			cRetorno	:= oDoc:cXMLRet 
		else
			cRetorno	:= oDoc:cXml
		endif
		
		aDadosXml := ColDadosXMl(cRetorno, aDados, @cErro, @cAviso)
		if '<obsCont xCampo="nRegDPEC">' $ cRetorno
			aDadosXml[9] := SubStr(cRetorno,At('<obsCont xCampo="nRegDPEC"><xTexto>',cRetorno)+35,15)
		endif	
		
		cProtocolo	:= aDadosXml[3]		
		cModTrans	:= IIF(Empty(aDadosXml[5]),aDadosXml[7],aDadosXml[5])
		cCodRetNFE	:= aDadosXml[1]
		cMsgNFE 	:= aDadosXml[2]
		cMsgRet		:= aDadosXml[11]			
		
		//Dados do DEPEC
		If !Empty( aDadosXml[9] )
			cRetDPEC        := cRetorno
			cProtDPEC       := aDadosXml[9] 
		EndIf
		
		//Tratamento para gravar a hora da transmissao da NFe
		If !Empty(cProtocolo)
			cDtHrRec		:= aDadosXml[4]
			nDtHrRec1		:= RAT("T",cDtHrRec)
			
			If nDtHrRec1 <> 0
				cDtHrRec1   :=	SubStr(cDtHrRec,nDtHrRec1+1)
				dDtRecib	:=	SToD(StrTran(SubStr(cDtHrRec,1,AT("T",cDtHrRec)-1),"-",""))
			EndIf
			
			AtuSF2Hora(cDtHrRec1,aIdNFe[nZ][5]+aIdNFe[nZ][4]+aIdNFe[nZ][6]+aIdNFe[nZ][7])
			
		EndIf

		aRetorno[1][1] := cProtocolo
		aRetorno[1][2] := cRetorno
		aRetorno[1][4] := cRetDPEC
		aRetorno[1][5] := cProtDPEC
		aRetorno[1][6] := cDtHrRec1
		aRetorno[1][7] := dDtRecib
		aRetorno[1][8] := cModTrans
		aRetorno[1][9] := cCodRetNFE
		aRetorno[1][10]:= cMsgNFE
		aRetorno[1][11]:= cMsgRet
								
		cRetDPEC := ""
		cProtDPEC:= ""		
				
	endif
endif

freeObj(oWS)
oWS	:= Nil
aSize(aDados, 0)
aDados:= nil
aSize(aIdNfe, 0)
aIdNfe:= nil
aSize(aWsErro, 0)
aWsErro:= nil

return aRetorno[len(aRetorno)]

static function getXMLColab(aIdNFe,cModalidade,lUsaColab)

local nZ			:= 0
local nCount		:= 0

local cIdEnt 		:= "000000"

local aDados		:= {}
local aRetorno	:= {}

If Empty(cModalidade)
	cModalidade := ColGetPar( "MV_MODALID", "1" )	
EndIf  
         

For nZ := 1 To len(aIdNfe) 

	nCount++

	aDados := executeRetorna( aIdNfe[nZ], cIdEnt, lUsaColab )
	
	if ( nCount == 10 )
		delClassIntF()
		nCount := 0
	endif
	
	aAdd(aRetorno,aDados)
	
Next nZ

Return(aRetorno)

static function atuSf2Hora( cDtHrRec,cSeek )

local aArea := GetArea()
 
dbSelectArea("SF2")
dbSetOrder(1)
If MsSeek(xFilial("SF2")+cSeek)
	If SF2->(FieldPos("F2_HORA"))<>0 .And. Empty(SF2->F2_HORA)
		RecLock("SF2")
		SF2->F2_HORA := cDtHrRec
		MsUnlock()
	EndIf
EndIf
dbSelectArea("SF1")
dbSetOrder(1)
If MsSeek(xFilial("SF1")+cSeek)
	If SF1->(FieldPos("F1_HORA"))<>0 .And. Empty(SF1->F1_HORA)
		RecLock("SF1")
		SF1->F1_HORA := cDtHrRec
		MsUnlock()
	EndIf
EndIf

RestArea(aArea)

return nil

//-----------------------------------------------------------------------
/*/{Protheus.doc} ColDadosNf
Devolve os dados com a informação desejada conforme parâmetro nInf.
 
@author 	Rafel Iaquinto
@since 		30/07/2014
@version 	11.9
 
@param	nInf, inteiro, Codigo da informação desejada:<br>1 - Normal<br>2 - Cancelametno<br>3 - Inutilização						

@return aRetorno Array com as posições do XML desejado, sempre deve retornar a mesma quantidade de posições.
/*/
//-----------------------------------------------------------------------
static function ColDadosNf(nInf)

local aDados	:= {}

	do case
		case nInf == 1
			//Informaçoes da NF-e
			aadd(aDados,"NFEPROC|PROTNFE|INFPROT|CSTAT") //1 - Codigo Status documento 
			aadd(aDados,"NFEPROC|PROTNFE|INFPROT|XMOTIVO") //2 - Motivo do status
			aadd(aDados,"NFEPROC|PROTNFE|INFPROT|NPROT")	//3 - Protocolo Autporizacao		
			aadd(aDados,"NFEPROC|PROTNFE|INFPROT|DHRECBTO")	//4 - Data e hora de recebimento					
			aadd(aDados,"NFEPROC|NFE|INFNFE|IDE|TPEMIS") //5 - Tipo de Emissao
			aadd(aDados,"NFEPROC|NFE|INFNFE|IDE|TPAMB") //6 - Ambiente de transmissão		
			aadd(aDados,"NFE|INFNFE|IDE|TPEMIS") //7 - Tipo de Emissao - Caso nao tenha retorno
			aadd(aDados,"NFE|INFNFE|IDE|TPAMB") //8 - Ambiente de transmissão -  Caso nao tenha retorno			
			aadd(aDados,"NFEPROC|RETDEPEC|INFDPECREG|NREGDPEC") //9 - Numero de autorização DPEC
			aadd(aDados,"NFEPROC|PROTNFE|INFPROT|CHNFE") //10 - Chave da autorizacao
			aadd(aDados,"NFEPROC|PROTNFE|INFPROT|XMSG") //11 - Tag <xMsg>
		
		case nInf == 2	
			//Informacoes do cancelamento - evento
			aadd(aDados,"PROCEVENTONFE|RETEVENTO|INFEVENTO|CSTAT") //1 - Codigo Status documento 
			aadd(aDados,"PROCEVENTONFE|RETEVENTO|INFEVENTO|XMOTIVO") //2 - Motivo do status
			aadd(aDados,"PROCEVENTONFE|RETEVENTO|INFEVENTO|NPROT")	//3 - Protocolo Autporizacao		
			aadd(aDados,"PROCEVENTONFE|RETEVENTO|INFEVENTO|DHREGEVENTO")	//4 - Data e hora de recebimento					
			aadd(aDados,"") //5 - Tipo de Emissao
			aadd(aDados,"PROCEVENTONFE|RETEVENTO|INFEVENTO|TPAMB") //6 - Ambiente de transmissão		
			aadd(aDados,"") //7 - Tipo de Emissao - Caso nao tenha retorno
			aadd(aDados,"ENVEVENTO|EVENTO|INFEVENTO|TPAMB") //8 - Ambiente de transmissão -  Caso nao tenha retorno												
			aadd(aDados,"") //9 - Numero de autorização DPEC
			aadd(aDados,"") //10 - Chave da autorizacao
			aadd(aDados,"") //11 - Tag <xMsg>
		
		case nInf == 3	
			//Informações da Inutilização
			aadd(aDados,"PROCINUTNFE|RETINUTNFE|INFINUT|CSTAT") //1 - Codigo Status documento 
			aadd(aDados,"PROCINUTNFE|RETINUTNFE|INFINUT|XMOTIVO") //2 - Motivo do status
			aadd(aDados,"PROCINUTNFE|RETINUTNFE|INFINUT|NPROT")	//3 - Protocolo Autporizacao		
			aadd(aDados,"PROCINUTNFE|RETINUTNFE|INFINUT|DHRECBTO")	//4 - Data e hora de recebimento					
			aadd(aDados,"") //5 - Tipo de Emissao
			aadd(aDados,"PROCINUTNFE|RETINUTNFE|INFINUT|TPAMB") //6 - Ambiente de transmissão		
			aadd(aDados,"") //7 - Tipo de Emissao - Caso nao tenha retorno
			aadd(aDados,"INUTNFE|INFINUT|TPAMB	") //8 - Ambiente de transmissão -  Caso nao tenha retorno												
			aadd(aDados,"") //9 - Numero de autorização DPEC
			aadd(aDados,"") //10 - Chave da autorizacao
			aadd(aDados,"") //11 - Tag <xMsg>
	end
	
return(aDados)

static function UsaColaboracao(cModelo)
Local lUsa := .F.

If FindFunction("ColUsaColab")
	lUsa := ColUsaColab(cModelo)
endif
return (lUsa)


//-----------------------------------------------------------------------
/*/{Protheus.doc} DANFE_VI
Funcao utilizada para verificar a ultima versao do fonte DANFEIII.PRW aplicado no rpo do cliente, assim verificando
a necessidade de uma atualizacao neste fonte.
 
@author 	Eduardo Silva
@since 		25/08/2014
@version 	11.9
 
@param	Retornar a ultima data do RPO que esta no cliente. Pois o cliente não esta utilizando o DANFEII com isto esta 
		sendo informado a mensagem que o RdMake não está compilado. 						

@return nRet
/*/
//-----------------------------------------------------------------------

User Function DANFE_VI

Local nRet := 20140825 // 25 de Abril de 2014 # Eduardo Silva ## Cliente não tem o DANFEII compilado no RPO ajuste para não dar erro

Return nRet


/*/{Protheus.doc} ValAtrib
Função utilizada para substituir o type onde não seja possivél a sua retirada para não haver  
ocorrencia indevida pelo SonarQube.

@author 	valter Silva
@since 		09/01/2018
@version 	12
@return 	Nil
/*/
//-----------------------------------------------------------------------
static Function ValAtrib(atributo)
Return (type(atributo) )

//-----------------------------------------------------------------------
/*/{Protheus.doc} MontaNfcDest
Faz criação tag <dest> quando não vem no XML da NFCe
@author 	anderson.machado
@since 		29/04/2020
@version 	12
@return 	Nil
/*/
//-----------------------------------------------------------------------
Static Function MontaNfcDest(oDestino)
Local oDestRet	:= NIL
Local cAux		:= ""

cAux	:= '<?xml version="1.0" encoding="UTF-8"?>'
cAux	+= '<dest>'
if type("oDestino:_xNome") == "U"
	cAux	+= 		'<xNome>CONSUMIDOR NAO IDENTIFICADO</xNome>'
endif
cAux	+=		'<enderDest>'
cAux	+=   		'<xLgr> </xLgr>'
cAux  += 			'<nro> </nro>'
cAux	+= 			'<xBairro> </xBairro>'
cAux	+=			'<cMun> </cMun>'
cAux	+= 			'<Cep> </Cep>'
cAux	+=			'<xMun> </xMun>'
cAux	+=			'<UF> </UF>'
cAux	+=			'<cPais>105</cPais>'
cAux	+=			'<xPais>BRASIL</xPais>'	
cAux 	+= 		'</enderDest>'
cAux	+= '</dest>'

oDestRet := XmlParser(cAux,"_","","")
oDestRet := oDestRet:_dest

Return oDestRet

/*/{Protheus.doc} ValidDanfe
Valida o estilo de fonte caso for PDF ou SPOOl.
@type function
@version V12 P2210
@author Gabriel Jesus
@since 27/06/2023
@param oDanfe, object, recebe o nDevice para identificar se é pdf ou spool.
/*/
Static Function ValidDanfe(oDanfe)
	Local oEstilo	:= oFont13N:oFont
	Default oDanfe	:= 6

	If oDanfe == 6
		oEstilo := oFont12N:oFont
	EndIf

Return oEstilo


//-----------------------------------------------------------------------
/*/{Protheus.doc} DefineResolution
Define a resolução para divisão da impressão das DANFES em lote
@author 	Rafael Gama Inácio
@since 		19/08/2025
@version 	12
@return 	Nil
/*/
//-----------------------------------------------------------------------

static Function DefineResolution(oDanfe, oSetup, lJob)

	oDanfe:SetResolution(78) // Tamanho estipulado para a Danfe
	oDanfe:SetLandscape()
	oDanfe:SetPaperSize(DMPAPER_A4)
	oDanfe:SetMargin(60,60,60,60)

	if lJob
		oDanfe:lServer := .T.
	else 
		oDanfe:lServer := oSetup:GetProperty(PD_DESTINATION)==AMB_SERVER
	endif

	// ----------------------------------------------
	// Define saida de impressão
	// ---------------------------------------------
	If lJob .or. oSetup:GetProperty(PD_PRINTTYPE) == IMP_PDF
		oDanfe:nDevice := IMP_PDF
		// ----------------------------------------------
		// Define para salvar o PDF
		// ----------------------------------------------
		if lJob
			oDanfe:cPathPDF := SuperGetMV('MV_RELT',,"\SPOOL\")
		else
			oDanfe:cPathPDF :=  oSetup:aOptions[PD_VALUETYPE]
		endif
	elseIf oSetup:GetProperty(PD_PRINTTYPE) == IMP_SPOOL
		oDanfe:nDevice := IMP_SPOOL
		oDanfe:SetParm( "-RFS")
		// ----------------------------------------------
		// Salva impressora selecionada
		// ----------------------------------------------
		fwWriteProfString(GetPrinterSession(),"DEFAULT", oSetup:aOptions[PD_VALUETYPE], .T.)
		oDanfe:cPrinter := oSetup:aOptions[PD_VALUETYPE]
	Endif

	Private PixelX := odanfe:nLogPixelX()
	Private PixelY := odanfe:nLogPixelY()

return

//-----------------------------------------------------------------------
/*/{Protheus.doc} DivLtDanfeImp
Divide a impressão das DANFES em lotes
@author 	Rafael Gama Inácio
@since 		19/08/2025
@version 	12
@return 	Nil
/*/
//-----------------------------------------------------------------------

Static Function DivLtDanfeImp(oDanfe, nQtdDocs, nLimitImp, cIDEnt, lIsLoja, lJob, oSetup, lExistNFe, cNfceMens)
	Local nQtdProc 		:= 0
	Local nContProc 	:= 0
	Local nTamStr		:= 0
	Local cDanfeIni 	:= ""
	Local cDanfeFim 	:= ""
	Local cFilePrint	:= ""
	Local cMsgRange		:= ""
	Local cUltima		:= ""

	cUltima := MV_PAR02
	nTamStr := len(Alltrim(MV_PAR01))
	nQtdProc := Ceiling((nQtdDocs + 1) / nLimitImp)

	For nContProc := 1 To nQtdProc
		If nContProc == 1
			cDanfeIni := MV_PAR01
		Else
			cDanfeIni := StrZero((Val(cDanfeIni) + nLimitImp), nTamStr)
		EndIf

		If nContProc == nQtdProc
			cDanfeFim := cUltima
		Else
			cDanfeFim := StrZero(((Val(cDanfeIni) - 1) + nLimitImp), nTamStr)
		EndIf

		If lJob
			DANFEProc(@oDanfe, , cIDEnt, cDanfeIni, cDanfeFim, @lExistNFe, lIsLoja)
		Else
			RPTStatus( {|lEnd| DANFEProc(@oDanfe, @lEnd, cIDEnt, cDanfeIni, cDanfeFim, @lExistNFe, lIsLoja, @cNfceMens )}, "Imprimindo DANFE..." )
		EndIf

		If lExistNFe
			oDanfe:Preview()
			if nContProc == 1 .And. !lJob
				oSetup:aOptions[6] := oDanfe:cPathPDF
			endif

			If nContProc <> nQtdProc
				lExistNFe := .F.
				freeobj(oDanfe)
				oDanfe :=Nil
				cFilePrint := "DANFE_" + cIDEnt + Dtos(MSDate()) + StrTran(Time(), ":", "")
				oDanfe := FWMSPrinter():New(cFilePrint, IMP_PDF, .F., /*cPathInServer*/, .T.)
				DefineResolution(oDanfe, oSetup, lJob)
			EndIf
		ElseIf !lIsLoja .And. !lJob
			cMsgRange += (Chr(13)+Chr(10)) + "NF " +cDanfeIni + " à NF " + cDanfeFim
		EndIf
	Next nContProc
	
	if !empty(cMsgRange)
		Aviso("DANFE", "Nenhuma NF-e a ser impressa no range: " + cMsgRange, {"OK"}, 3)
	endif

Return

//-----------------------------------------------------------------------
/*/{Protheus.doc} setQuery
Executa as querys utilizando bind
@author 	Rafael Gama Inácio
@since 		19/08/2025
@version 	12
@return 	Nil
/*/
//-----------------------------------------------------------------------

Static Function setQuery(cTabela, cCampos, lOrdena)
	Local cQuery		:= ""
	Local cAliasTmp		:= ""
	Local nCont			:= 1

	Private oQryExec
	
	Default cTabela 	:= 'SF2'
	Default cCampos 	:= ''
	Default lOrdena 	:= .F.
		
	cQuery += "SELECT "
	cQuery += cCampos
	cQuery += "FROM " + RetSqlName(cTabela) + " " + cTabela
	
	if cTabela == 'SF1'
		cQuery += "WHERE SF1.F1_FILIAL = ? "
		cQuery += "AND SF1.F1_SERIE = ? "
		cQuery += "AND SF1.F1_DOC >= ? "
		cQuery += "AND SF1.F1_DOC <= ? "
		cQuery += "AND SF1.F1_ESPECIE = ? "
		cQuery += "AND SF1.F1_FORMUL = ? "
		cQuery += "AND  SF1.D_E_L_E_T_ = ? "

		if !Empty(MV_PAR07)
			cQuery += "AND SF1.F1_EMISSAO >= ? "
		endif

		if !Empty(MV_PAR08)
			cQuery += "AND SF1.F1_EMISSAO <= ? "
		endif

		if lOrdena
			cQuery += "ORDER BY SF1.F1_DOC"
		endif
		
	elseif cTabela == 'SF2'
		cQuery += "WHERE SF2.F2_FILIAL = ? "
		cQuery += "AND SF2.F2_SERIE = ? "
		cQuery += "AND SF2.F2_DOC >= ? "
		cQuery += "AND SF2.F2_DOC <= ? " 
		cQuery += "AND SF2.F2_ESPECIE IN (?) "
		cQuery += "AND SF2.D_E_L_E_T_ =  ? "

		if !Empty(MV_PAR07)
			cQuery += "AND SF2.F2_EMISSAO >= ? "
		endif

		if !Empty(MV_PAR08)
			cQuery += "AND SF2.F2_EMISSAO <= ? "
		endif

		if lOrdena	
			cQuery += "ORDER BY SF2.F2_DOC"
		endif

	elseif cTabela == 'SF3'
		cQuery += "WHERE SF3.F3_FILIAL = ? "
		cQuery += "AND SF3.F3_SERIE = ? "
		cQuery += "AND SF3.F3_NFISCAL >= ? "
		cQuery += "AND SF3.F3_NFISCAL <= ? "
		cQuery += "AND SF3.F3_ESPECIE IN (?) "
		cQuery += "AND SF3.F3_DTCANC = ? "

		If MV_PAR04==1
			cQuery	+= "AND SubString(SF3.F3_CFO,1,1) < ? "
			cQuery	+= "AND SF3.F3_FORMUL= ? "

		ElseIf MV_PAR04==2
			cQuery		+= "AND SubString(SF3.F3_CFO,1,1) >= ? "

		EndIf

		cQuery += "AND SF3.D_E_L_E_T_ = ? "

		if !Empty(MV_PAR07)
			cQuery += "AND SF3.F3_EMISSAO >= ? "
		endif

		if !Empty(MV_PAR08)
			cQuery += "AND SF3.F3_EMISSAO <= ? "
		endif

		if lOrdena
			cQuery += "ORDER BY SF3.F3_NFISCAL"
		endif

	endif

	cQuery := ChangeQuery(cQuery)

	oQryExec := FwExecStatement():New(cQuery)

	if cTabela == 'SF1'
		oQryExec:SetString(nCont++, xFilial(cTabela)) //Filial
		oQryExec:SetString(nCont++, MV_PAR03) // Serie
		oQryExec:SetString(nCont++, MV_PAR01) // NF Inicial
		oQryExec:SetString(nCont++, MV_PAR02) // NF Final
		oQryExec:SetString(nCont++, 'SPED') //ESPECIE
		oQryExec:SetString(nCont++, 'S') //FORMUL
		oQryExec:SetString(nCont++, "") //DELETE

		if !Empty(MV_PAR07)
			oQryExec:SetString(nCont++, DtoS(MV_PAR07)) //DT INICIO
		endif

		if !Empty(MV_PAR08)
			oQryExec:SetString(nCont++, DtoS(MV_PAR08)) //DT FIM
		endif

	elseif cTabela == 'SF2'
		oQryExec:SetString(nCont++, xFilial(cTabela)) //Filial
		oQryExec:SetString(nCont++, MV_PAR03) // Serie
		oQryExec:SetString(nCont++, MV_PAR01) // NF Inicial
		oQryExec:SetString(nCont++, MV_PAR02) // NF Final
		oQryExec:SetIn(nCont++, {'SPED','NFCE'}) //ESPECIE
		oQryExec:SetString(nCont++, "") //DELETE

		if !Empty(MV_PAR07)
			oQryExec:SetString(nCont++, DtoS(MV_PAR07)) //DT INICIO
		endif

		if !Empty(MV_PAR08)
			oQryExec:SetString(nCont++, DtoS(MV_PAR08)) //DT FIM
		endif
		
	elseif cTabela == 'SF3'
		oQryExec:SetString(nCont++, xFilial(cTabela)) //Filial
		oQryExec:SetString(nCont++, MV_PAR03) // Serie
		oQryExec:SetString(nCont++, MV_PAR01) // NF Inicial
		oQryExec:SetString(nCont++, MV_PAR02) // NF Final
		oQryExec:SetIn(nCont++, {'SPED','NFCE'}) //ESPECIE
		oQryExec:SetString(nCont++, Space(8)) //DT CANC

		If MV_PAR04==1
			oQryExec:SetString(nCont++, '5')
			oQryExec:SetString(nCont++, 'S')
		ElseIf MV_PAR04==2
			oQryExec:SetString(nCont++, '5')
		EndIf

		oQryExec:SetString(nCont++, "") //DELETE

		if !Empty(MV_PAR07)
			oQryExec:SetString(nCont++, DtoS(MV_PAR07)) //DT INICIO
		endif

		if !Empty(MV_PAR08)
			oQryExec:SetString(nCont++, DtoS(MV_PAR08)) //DT FIM
		endif
	endif

	cAliasTmp	:= oQryExec:OpenAlias()

	oQryExec:Destroy()
	oQryExec := nil

Return cAliasTmp

//-----------------------------------------------------------------------
/*/{Protheus.doc} Fatura
Monta as informações para apresentar no BOX FATURA/DUPLICATA
@author 	renan.botelho
@since 		08/10/2025
@version 	1
@return 	Nil
/*/
//-----------------------------------------------------------------------
static function Fatura(oFatura,nFaturas,lFat853)
local aAux 			:= {}
local aFaturas		:= {}
local nX			:= 0
local nY			:= 0
default	lFat853		:= .F.
default	nFaturas	:= 0
default	oFatura		:= NIL	

IF lFat853
	if type("oFatura:_FAT") <> "U"
		For nX := 1 To 2
			aAux := {}
			For nY := 1 To Min(9, nFaturas)
				Do Case
					Case nX == 1
						AAdd(aAux, AllTrim(oFatura:_FAT:_NFAT:TEXT))
					Case nX == 2
						AAdd(aAux, AllTrim(oFatura:_FAT:_VLIQ:TEXT))
				EndCase
			Next nY
			If nY <= 9
				For nY := 1 To 9
					AAdd(aAux, Space(20))
				Next nY
			EndIf
			AAdd(aFaturas, aAux)
		Next nX
	endif
ELSE
	IF type("oFatura:_DUP") <> "U"
		For nX := 1 To 3
			aAux := {}
			For nY := 1 To Min(9, nFaturas)
				Do Case
					Case nX == 1
						If nFaturas > 1
							AAdd(aAux, AllTrim(oFatura:_Dup[nY]:_nDup:TEXT))
						Else
							AAdd(aAux, AllTrim(oFatura:_Dup:_nDup:TEXT))
						EndIf
					Case nX == 2
						If nFaturas > 1
							AAdd(aAux, AllTrim(ConvDate(oFatura:_Dup[nY]:_dVenc:TEXT)))
						Else
							AAdd(aAux, AllTrim(ConvDate(oFatura:_Dup:_dVenc:TEXT)))
						EndIf
					Case nX == 3
						If nFaturas > 1
							AAdd(aAux, AllTrim(TransForm(Val(oFatura:_Dup[nY]:_vDup:TEXT), "@E 9,999,999,999,999.99")))
						Else
							AAdd(aAux, AllTrim(TransForm(Val(oFatura:_Dup:_vDup:TEXT), "@E 9,999,999,999,999.99")))
						EndIf
				EndCase
			Next nY
			If nY <= 9
				For nY := 1 To 9
					AAdd(aAux, Space(20))
				Next nY
			EndIf
			AAdd(aFaturas, aAux)
		Next nX
	endif
ENDIF
return aFaturas
