#INCLUDE "rwmake.ch"


User Function DEL003

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DEL003    º Autor ³ Marcos A. Schoeffelº Data ³  21/10/03   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Exportacao do Arquivo de Notas Fiscais para WEG            º±±
±±º          ³                                                            º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ WEG                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Declaracao de Variaveis                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

SetPrvt("lachou")

Private cString
Private oGeraTxt
dCaminho   := "\WEG-ONLINE"
cDiretorio := Space(180)
cArqTxt := Space(12)
cString := "SF2"
dFornec := "201548"
dNFIni  := Space(6)
dNFFim  := Space(6)
dSerie  := "2"
dNFFim 	:= "ZZZZZZ"

@ 0,0 TO 280,450 DIALOG oDlg1 TITLE "Geracao de Arquivo para WEG On-Line"
//@ 0,0 TO 135,230
@ 10,15 SAY "Codigo Fornecedor.: "
@ 10,73 SAY dFornec // GET dFornec size 51,08
@ 30,15 SAY "N. Fiscal Inicial.......: "
@ 30,73 GET dNFIni size 51,08
@ 50,15 SAY "N. Fiscal Final........: "
@ 50,73 GET dNFFim size 51,08
@ 70,15 SAY "Serie da NF...............: "
@ 70,73 GET dSerie size 51,03
@ 90,15 SAY "Informe o diretorio destino: (Caso nao exista sera criado)"
@100,15 GET dCaminho PICTURE "@!" VALID .t. SIZE 180,10

@115,100 BUTTON "_Confirma Geracao" SIZE 50,15 ACTION Geracao()
@115,155 BUTTON "_Sair do Programa" SIZE 50,15 ACTION Close(oDlg1)
ACTIVATE DIALOG oDlg1 CENTER

return

Static Function Geracao()

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Cria o arquivo texto                                                ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

If Empty(dFornec) .or. Empty(dNFFim) .or. Empty(dSerie) .or. Empty(dCaminho)
	MsgStop("Por Favor Preencha todos os campos da Tela"+chr(13)+"           para Geração do Arquivo !!!       ","Atenção")
	Return(nil)
EndIf

cDiretorio := alltrim(dCaminho)
if subs(cDiretorio,len(cDiretorio),1)=="\"
	cDiretorio := Subs(cDiretorio,1,len(cDiretorio)-1)
endif
MakeDir(cDiretorio)

cEOL    := "CHR(13)+CHR(10)"
If Empty(cEOL)
	cEOL := CHR(13)+CHR(10)
Else
	cEOL := Trim(cEOL)
	cEOL := &cEOL
Endif

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inicializa a regua de processamento                                 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

lachou := .f.

Processa({|| RunCont() },"Processando...")

If lachou
	MsgInfo("Geração de Arquivos Concluido !!!","Concluido")
Else
	MsgStop("Notas Fiscais nao encontradas ou ja Processadas "+chr(13)+"              para Arquivo WEG On-Line  !!!        ","Erro")
EndIf

Return

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºFun‡„o    ³ RUNCONT  º Autor ³ AP5 IDE            º Data ³  06/03/01   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescri‡„o ³ Funcao auxiliar chamada pela PROCESSA.  A funcao PROCESSA  º±±
±±º          ³ monta a janela com a regua de processamento.               º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Programa principal                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

Static Function RunCont

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Definicao de Variaveis                                              ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

Local LinHeader  := Space(17)
Local hFornec    := Space(6)
Local hNumNF     := Space(8)
Local hSerNF     := Space(3)

Local LinDetalhe := Space(32)
Local dCodProd   := Space(16)
Local dQtdEnt    := Space(10)
Local dAlmoxDest := Space(3)
Local dUnMed     := Space(3)
LOCAL aTam       := {}
LOCAL aItem		 := {}
LOCAL cQtdPro    := ""
LOCAL cDecPro    := ""
LOCAL lgravou    := .f.
LOCAL lheader	 := .f.

dbSelectArea("SF2")
dbSetOrder(1)
dbGoTop()
ProcRegua(RecCount()) // Numero de registros a processar
DbSeek(xfilial()+dNFIni+dSerie,.t.)
While !Eof() .and. xFilial() == sf2->f2_filial .and.;
	sf2->f2_doc >= dNFini .and. sf2->f2_doc <= dNFfim
	
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Incrementa a regua                                                  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	
	IncProc("Aguarde Gerando Arquivo N.F => "+sf2->f2_doc)
	
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Substitui nas respectivas posicioes na variavel cLin pelo conteudo  ³
	//³ dos campos segundo o Lay-Out. Utiliza a funcao STUFF insere uma     ³
	//³ string dentro de outra string.                                      ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	
	If sf2->f2_serie <> dSerie
		dbSelectArea("SF2")
		DbSkip()
		Loop
	EndIf
	
	If Empty(dNFIni) .and. (dNFFim == "ZZZZZZ")
		If sf2->f2_arqgera == "S"
			dbSelectArea("SF2")
			DbSkip()
			Loop
		EndIf
	EndIf
	
	lgravou := .f.
	dbSelectArea("SD2")
	dbsetOrder(3)
	dbGotop()
	dbSeek(xfilial()+sf2->f2_doc+sf2->f2_serie,.t.)
	While !Eof() .and. xfilial() == sd2->d2_filial .and. ;
		sd2->d2_doc == sf2->f2_doc .and. sd2->d2_serie == sf2->f2_serie
		
		If EMPTY(SD2->D2_ALMOX)
			dbSelectArea("SD2")
			dbSkip()
			Loop
		EndIf
		
		dbSelectArea("SA7")
		dbSetOrder(1)
		dbGotop()
		If !(DbSeek(xFilial("SA7")+SF2->F2_CLIENTE+SF2->F2_LOJA+SD2->D2_COD,.t.))
			dbSelectArea("SF2")
			dbSkip()
			Loop
		EndIf
		
		dCodProd   := sa7->a7_codcli+replicate(" ",16-len(sa7->a7_codcli))
		dAlmoxDest := sd2->d2_almox
		dUnMed     := sd2->d2_um+" "
		
		npos := Ascan(aItem,{|x| (x[1]+x[5]) == dcodProd+dAlmoxDest})
		If 	npos == 0
			aADD(aItem,{dcodProd,",",QtdDetalhe(sd2->d2_quant),",",dAlmoxDest,",",dUnMed,";",sd2->d2_quant})
		Else
			nquant := (aItem[npos][9] + sd2->d2_quant)
			aItem[npos][9] += sd2->d2_quant
			aItem[npos][3] := QtdDetalhe(nquant)
		EndIf
		
		DbSelectArea("SD2")
		DbSkip()
	End
	
	If Len(aItem) > 0
		cArqTxt := cDiretorio+"\"+sf2->f2_doc+".txt"
		if file(cArqTxt)
			ferase(cArqTxt)
		endif
		nHdl := MSFcreate(cArqTXT)
		
		If nHdl == -1
			MsgAlert("O arquivo de nome "+AllTrim(cArqTxt)+" nao pode ser executado! Verifique os parametros.","Atencao!")
			Return
		Endif
		
		nTamLin    := 22
		LinHeader  := Space(nTamLin)+cEOL // Variavel para criacao da linha do registros para gravacao
		
		hFornec    := dFornec // codigo do fornecedor
		hNumNF     := replicate("0",8-len(alltrim(sf2->f2_doc))) + Alltrim(sf2->f2_doc)
		hSerNF     := sf2->f2_serie
		LinHeader  := Stuff(LinHeader,01,17,(hFornec+","+hNumNF+","+hSerNF+";"))
		
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Gravacao registro Header no arquivo texto. 						    ³
		//³ Testa por erros durante a gravacao dalinha montada.                 ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		
		If fWrite(nHdl,LinHeader,Len(LinHeader)) != Len(LinHeader)
			If !MsgAlert("Ocorreu um erro na gravacao do arquivo - "+cArqTXT+chr(13)+"Continua ?","Atencao!")
				Exit
			Endif
		Endif

		for i:=1 to Len(aItem)
			
			nTamLin    := 36
			LinDetalhe := Space(nTamLin)+cEOL // Variavel para criacao da linha do registros para gravacao
			
			linha := ""
			for j:=1 to 8
				linha := linha + aItem[i][j]
			next
			
			LinDetalhe := Stuff(LinDetalhe,01,36,linha)
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Gravacao registro Detalhe no arquivo texto. 					    ³
			//³ Testa por erros durante a gravacao dalinha montada.                 ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			
			If  fWrite(nHdl,LinDetalhe,Len(LinDetalhe)) != Len(LinDetalhe)
				If !MsgAlert("Ocorreu um erro na gravacao do arquivo - "+cArqTXT+chr(13)+"Continua ?","Atencao!")
					Exit
				Endif
			Endif
		Next
		
		fClose(nHdl)
		RecLock("SF2",.f.)
		SF2->F2_ARQGERA := "S"
		MsUnlock("SF2")
		
		aItem := {}
		lachou := .t.
	End

	dbSelectArea("SF2")
	dbSkip()
	
End

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ O arquivo texto deve ser fechado, bem como o dialogo criado na fun- ³
//³ cao anterior.                                                       ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

Return

Static Function QtdDetalhe(nQtdDet)

dbSelectArea("SD2")
aTam:=TamSX3("D2_QUANT")

cQtdPro := strzero( Int(nQtdDet) ,06)
cDecPro := subs ( Alltrim ( str ( ( ( nQtdDet ) - Int ( nQtdDet ) ) ) ) ,3,aTam[2])

If Len(cDecPro) < aTam[2]
	cDecPro := cDecPro + replicate("0",4-len(cDecPro))
EndIf

If Empty(cDecPro) .or. (VAL(cDecPro) == 0)
	cDecPro := "0000"
EndIf

cQtdEnt := cQtdPro + cDecPro

Return cQtdEnt