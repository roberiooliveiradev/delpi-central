#INCLUDE "RWMAKE.CH"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DEL001    ºAutor  ³Microsiga           º Data ³  20/10/03   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Relatorio de impressao de Nota Fiscal Saida/Entrada.       º±±
±±º          ³                                                            º±±
±±º          ³ Criar Indice no SD2 conforme segue:                        º±±
±±º          ³ SD2 - CHAVE = D2_FILIAL+D2_DOC+D2_SERIE+D2_CF+D2_COD		  º±±
±±º          ³ SD1 - CHAVE = D1_FILIAL+D1_DOC+D1_SERIE+D1_CF+D1_COD		  º±±
±±º          ³ Observacao: A Ordem podera ser qualquer uma, pois o prog.  º±±
±±º          ³ utiliza funcao para verificar qual e a ordem do item.      º±±
±±º          ³                                                            º±±
±±º          ³ Criar tabela SZ1 - texto legal                             º±±
±±º          ³              Z1_TEXTO  C 3                                 º±±
±±º          ³              Z1_DESC1  C 60                                º±±
±±º          ³              Z1_DESC2  C 60                                º±±
±±º NECESSIDADES : EXISTENCIA DA TABELA SF1 CAMPOS: 	 				  º±±
±±º												   SC5->C5_MSG1      C 60 º±±
±±º												   SC5->C5_MSG2      C 60 º±±
±±º												   SC5->C5_MSG3      C 60 º±±
±±º												   SC5->C5_TEXT1     C 3  º±±
±±º												   SC5->C5_TEXT2     C 3  º±±
±±º												   SF1->F1_TRANSP    C 6  º±±
±±º 											   SF1->F1_TPFRETE   C 1  º±±
±±º 											   SF1->F1_TEXT1     C 3  º±±
±±º 											   SF1->F1_TEXT2     C 3  º±±
±±º 											   SF1->F1_VOLUME1   N 5  º±±
±±º 											   SF1->F1_ESPECI1   C 20 º±±
±±º 											   SF1->F1_PESOL    N 7,2 º±±
±±º 											   SF1->F1_PESOB    N 7,2 º±±
±±º 											   SF1->F1_MENSNF1   C 60 º±±
±±º 											   SF1->F1_MENSNF2   C 60 º±±
±±º 											   SF1->F1_MENSNF3   C 60 º±±
±±º 											   SF1->F1_PLACA     C 10 º±±
±±º 											   SF1->F1_MARCA     C 10 º±±
±±º          ³                                                            º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function DEL001()

//Definicao das Variaveis do Corpo da Nota Fiscal.
// Cabecalho
SetPrvt("cDoc,cSerie")
SetPrvt("cNatureza,cCfop,cSubsTrib")
SetPrvt("cSA1Cod,cSA1Razao,cSA1Cnpj,dEmissao")
SetPrvt("cSA1End,cSA1Bairro,cSA1Cep,dSaida")
SetPrvt("cSA1Mun,cSA1Fone,cSA1Uf,cSA1Insc,cHora")

// Duplicatas
SetPrvt("aDuplic")

// Itens Nota Fiscal
SetPrvt("aItem")

// Itens Servico
//SetPrvt("aServico")
//SetPrvt("nSerAliq,nSerBase,nSerVlr,nSerTot")

// Calculos
SetPrvt("nBaseIcms,nVlrIcms,nBaseSubs,nVlrSubs,nVlrPro")
SetPrvt("nVlrFret,nVlrSeg,nVlrOut,nVlrIpi,nVlrFat,nVlrTotNF")

// Transportadora
SetPrvt("cSA4Cod,cSA4Razao,cTpFrete,cPlaca,cUfPlaca,cSA4Cnpj")
SetPrvt("cSA4End,cSA4Mun,cSA4Uf,cSA4Insc")
SetPrvt("nQtdVol,cEspecie,cMarca,cNumero,nPesoBru,nPesoLiq")

// Outras Variaveis Utilizadas
SetPrvt("aCfo,cTexLeg1,cTexLeg2")
SetPrvt("lEnd,lAbortPrint,limite,tamanho,nomeprog,nTipo,aReturn,nLastKey,wnrel,cString")
SetPrvt("cPerg,aRegistros")
SetPrvt("lPrimImp,lPrim,lSegun,cOrig1,cOrig2,cDescSB1,aPed")
SetPrvt("cCobEnd,cCobBair,cCobCep,cCobMun,cCobUf")
SetPrvt("cEntEnd,cEntBair,cEntCep,cEntMun,cEntUf")
SetPrvt("cMsg1,cMsg2,cMsg3")
SetPrvt("aAlmox")
//SetPrvt("aPedidos")
SetPrvt("aNFOriginal")
// Variaveis utilizadas para Classificacao Fiscal.
SetPrvt("cClasFisc,npFisc,aFiscal,aPosIpi")

//aPedidos := {}
aNFOriginal := {}
cPerg := "DEL001"
aRegistros := {}

Aadd(aRegistros,{cPerg,"01","Da Nota     	?","mv_ch1","C",06,0,0,"G","","MV_PAR01","","","","","","","","","","","","","","",""})
Aadd(aRegistros,{cPerg,"02","Ate Nota   	?","mv_ch2","C",06,0,0,"G","","MV_PAR02","","","","","","","","","","","","","","",""})
Aadd(aRegistros,{cPerg,"03","Serie			?","mv_ch3","C",03,0,0,"G","","MV_PAR03","","","","","","","","","","","","","","",""})
Aadd(aRegistros,{cPerg,"04","Tipo da Nota	?","mv_ch4","N",01,0,0,"C","","MV_PAR04","Saida","","","Entrada","","","","","","","","","","",""})

CriaPergunta(cPerg,aRegistros)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Declaracao de Variaveis                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
cDesc1       := "Este programa tem como objetivo imprimir relatorio "
cDesc2       := "de acordo com os parametros informados pelo usuario."
cDesc3       := "Impressao Nota Fiscal Saida/Entrada"
titulo       := "Programa para impressao Nota Fiscal Saida/Entrada - Delpi"
nLin         := 00
Cabec1       := ""
Cabec2       := ""
aOrd         := {}
nTam 			 := 0

lEnd       := .F.
lAbortPrint:= .F.
limite     := 132
tamanho    := "M"
nomeprog   := "DEL001" // Coloque aqui o nome do programa para impressao no cabecalho
nTipo      := 18
aReturn    := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
nLastKey   := 0
wnrel      := "DEL001" // Coloque aqui o nome do arquivo usado para impressao em disco
cString    := "SF2"

pergunte(cPerg,.F.)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Monta a interface padrao com o usuario                              ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
wnrel := SetPrint(cString,NomeProg,cPerg,@titulo,cDesc1,cDesc2,cDesc3,.F.,aOrd,.T.,Tamanho,,.T.)

If nLastKey == 27
	Return
Endif

SetDefault(aReturn,cString)

If nLastKey == 27
	Return
Endif

nTipo := If(aReturn[4]==1,15,18)

GeraDados()

Return

Static Function GeraDados()

cNSU     := ""
cPEDCLI  := ""
cREDESP  := ""


If MV_PAR04 == 1
	lPrimImp	:= .T.	
	DbSelectArea("SF2")
	DbSetOrder(1)
	DbGotop()
	DbSeek(xFilial("SF2")+MV_PAR01,.T.)
	While	!Eof()	.And. SF2->F2_FILIAL == xFilial("SF2");
		.And. SF2->F2_DOC		<= MV_PAR02
		
		If SF2->F2_SERIE <> MV_PAR03
			DbSelectArea("SF2")
			SF2->(DbSkip())
			Loop
		EndIf
		
		IF lAbortPrint
			@ 00,01 PSAY "** CANCELADO PELO OPERADOR **"
			lContinua := .F.
			Exit
		Endif
		
		//Inicializacao das Variaveis do Corpo da Nota Fiscal.
		InicVar()
		
		cChave  := "D2_FILIAL+D2_DOC+D2_SERIE+D2_CF+D2_COD"
		nIndSD2 := 0
		DbSelectarea("SIX")
		DbSeek("SD2")
		While !eof() .and. SIX->INDICE == "SD2"
			nIndSD2 ++
			If alltrim(cChave) == alltrim(SIX->chave)
				Exit
			Endif
			DbSkip()
		End            
		cNSU := ""
		DbSelectArea("SD9")                                 
		DbSetOrder(2)
		If DbSeek(xFilial("SD9")+SF2->F2_SERIE+SF2->F2_DOC)
			cNSU := SD9->D9_NSU + ' Data: ' +dtoc(SD9->D9_DTUSO) +' Hora: '+Left(Alltrim(SD9->D9_HORA),2)+':'+ right(Alltrim(SD9->D9_HORA),2)
		EndIf

		
		DbSelectArea("SD2")
		DbSetOrder(nIndSD2)   // ORDEM FILIAL+DOCUMENTO+SERIE+CFO+PRODUTO
		Dbgotop()
		Dbseek(xFilial("SD2")+SF2->F2_DOC+SF2->F2_SERIE,.T.)
		While !eof() 	.And. SD2->D2_FILIAL		== xFilial("SD2");
			.And. SD2->D2_DOC			== SF2->F2_DOC;
			.And. SD2->D2_SERIE  	== SF2->F2_SERIE
			
			DbSelectArea("SB1")
			DbSetOrder(1)
			DbGotop()
			DbSeek(xFilial("SB1")+SD2->D2_COD)
			cOrig1 	:= Substr(SB1->B1_ORIGEM, 1, 1)
			
			// Montagem da Classificacao Fiscal para impressao no Formulario.
			ClasFisc()
			
			// * Cabecalho do Pedido de Venda
			DbSelectArea("SC5")
			DbSetOrder(1)
			If dbSeek(xFilial("SC5")+SD2->D2_PEDIDO,.T.)
				If ASCAN(aPED,SD2->D2_PEDIDO)==0
					AADD(aPED,SD2->D2_PEDIDO)
					cTpFrete 	:= SC5->C5_TPFRETE	// Tipo de Entrega
					cTexLeg1	:= SC5->C5_TEXT1
					cTexLeg2	:= SC5->C5_TEXT2
					cMsg1		:= SC5->C5_MSG1
					cMsg2		:= SC5->C5_MSG2
					cMsg3		:= SC5->C5_MSG3
					cPEDCLI     := SC5->C5_PEDCLI         // Pedido do Cliente -> Nas observações...
					cREDESP     := SC5->C5_REDESP         // Redespacho...
				Endif
			EndIf
			
			DbSelectArea("SC6")
			DbSetOrder(1)
			DbGotop()
			DbSeek(xFilial("SC6")+SD2->D2_PEDIDO+SD2->D2_ITEMPV+SD2->D2_COD)
			cDescSB1 := Substr(SC6->C6_DESCRI,1,30) + " - " + SD2->D2_ALMOX
			
			lalmox := .f.
			dbSelectArea("SD2")
			If !Empty(SD2->D2_ALMOX)
				DbSelectArea("SZ2")
				DbGotop()
				DbSeek(xFilial("SZ2")+SD2->D2_ALMOX)
				If ASCAN(aAlmox, (Alltrim(SZ2->Z2_DESCR)+" - "+Alltrim(SD2->D2_ALMOX)))==0
					AADD(aAlmox ,(Alltrim(SZ2->Z2_DESCR)+" - "+Alltrim(SD2->D2_ALMOX)))
				EndIf
				lalmox := .t.
			ElseIf !Empty(SC6->C6_ALMOX)
					DbSelectArea("SZ2")
					DbGotop()
					DbSeek(xFilial("SZ2")+SC6->C6_ALMOX)				
					If ASCAN(aAlmox, (Alltrim(SZ2->Z2_DESCR)+" - "+Alltrim(SC6->C6_ALMOX)))==0
						AADD(aAlmox ,(Alltrim(SZ2->Z2_DESCR)+" - "+Alltrim(SC6->C6_ALMOX)))
					EndIf
					lalmox := .t.
			EndIf
			
			If  !(lalmox) 
				If  Empty(SD2->D2_IDENTB6)
					lalmox := .t.
				EndIf
			EndIf
			
			// Se for itens normais utiliza descricao cadastro produto.
			If Empty(SD2->D2_CODISS)
				lCodCli := .T.
				DbSelectArea("SA7")
				DbSetOrder(2)
				DbGotop()
				If (DbSeek(xFilial("SA7")+SD2->D2_COD+SD2->D2_CLIENTE+SD2->D2_LOJA,.T.))
					If !Empty(SA7->A7_CODCLI) // .And. !Empty(SA7->A7_DESCCLI)
						cDescSB1 := Alltrim(SA7->A7_CODCLI) + " " + IIF(!EMPTY(SA7->A7_DESCCLI),Alltrim(Substr(SA7->A7_DESCCLI,1,40)),Alltrim(SB1->B1_DESC))+" - "+SD2->D2_ALMOX
						//					lCodCli := .F.
					EndIf
				EndIf
			EndIf
			
			DbSelectArea("SF4")
			DbSetOrder(1)
			DbGotop()
			Dbseek(xFilial("SF4")+SD2->D2_TES)
			cOrig2 := cOrig1+Substr(SF4->F4_SITTRIB,1,2)
			
			If  Empty(SD2->D2_CODISS)
				lcod := .f.
				If  lalmox
					npos := Ascan(aItem,{|x| (x[1]) == SD2->D2_COD})
				    If 	nPos != 0
				       	aItem[npos][6]  += SD2->D2_QUANT // 6
						aItem[npos][8]  += SD2->D2_TOTAL //8
						aItem[npos][11] += SD2->D2_VALIPI //11
					Else
						lcod := .t.
				    EndIf
				Else
					lcod := .t.
				EndIf
				
				If lcod
					Aadd(aItem,{SD2->D2_COD,;//1
						cDescSB1,;           //2
						cClasFisc,;          //3
						cOrig2,;             //4
						SD2->D2_UM,;         //5
						SD2->D2_QUANT,;      //6
						SD2->D2_PRCVEN,;     //7
						SD2->D2_TOTAL,;      //8
						SD2->D2_IPI,;        //9
						SD2->D2_PICM,;       //10
						SD2->D2_VALIPI,;     //11
						SD2->D2_IDENTB6})    //12
				EndIf
                         
                If SF2->F2_TIPO <> 'I'
				   nVlrTotNF += SD2->D2_TOTAL						
				EndIf
				
				// Por Solicitacao do Cliente, para cada item devera ser impresso o pedido,
				// mesmo que este ja tenha sido impresso anteriormente.
				//If !EMPTY(SC5->C5_PEDCLI)
				//	Aadd(aPedidos,{SC5->C5_PEDCLI,Len(Alltrim(SC5->C5_PEDCLI))})
				//EndIf
				// Incluido por Marcos para guardar as NFs Originais
				If !EMPTY(SD2->D2_NFORI)
					Aadd(aNFOriginal,{SD2->D2_NFORI,Len(Alltrim(SD2->D2_NFORI)),SD2->D2_SERIORI,Len(Alltrim(SD2->D2_SERIORI)),"S",SD2->D2_IDENTB6})
				EndIf
				//					EndIf
				//			Else
				//				Aadd(aServico,{SD2->D2_COD,;			//1
				//				cDescSB1,;           //2
				//				"",; 				      //3
				//				"",;           		//4
				//				"",;			         //5
				//				SD2->D2_QUANT,;      //6
				//				SD2->D2_PRCVEN,;     //7
				//				SD2->D2_TOTAL,;      //8
				//				0,;        				//9
				//				0,;        				//10
				//				0})     					//11
				
			EndIf
			
			// Monta Array com C.F.O.P.
			npos := 0
			npos := Ascan(aCfo,{|x| (x[1]) == SD2->D2_CF})
			If nPos == 0
				DbSelectArea("SF4")
				Dbsetorder(1)
				Dbseek(xFilial("SF4")+SD2->D2_TES,.T.)
				Aadd(aCfo,{SD2->D2_CF,SF4->F4_TEXTO})
				If lPrim
					lPrim := .F.
					/*
					If (SC5->C5_CLIENTE == "000001") .and. (SC5->C5_LOJAENT == "02") ;
					   .and. (SD2->D2_TES == "510")
						Aadd(aCfo,{"5902",""})
					ElseIf  (SC5->C5_CLIENTE == "000001") .and. (SC5->C5_LOJAENT == "03") ;
					   		.and. (SD2->D2_TES == "510")
				       		Aadd(aCfo,{"6902",""})
					EndIf
					*/
					cNatureza := Substr(SF4->F4_TEXTO,1,20)
				ElseIf lSegun
				  		lSegun := .F.
						npos := 0
						npos := Ascan(aCfo,{|x| (x[1]) == "5902"})
						/*
						If npos == 0
							If (SC5->C5_CLIENTE == "000001") .and. (SC5->C5_LOJAENT == "02");
							   .and. (SD2->D2_TES == "510")
				       			Aadd(aCfo,{"5902",""})
							ElseIf (SC5->C5_CLIENTE == "000001") .and. (SC5->C5_LOJAENT == "03");
							   		.and. (SD2->D2_TES == "510")
				       				Aadd(aCfo,{"6902",""})
							EndIf

						EndIf
						*/
						cNatureza := Alltrim(cNatureza)+"/"+Substr(SF4->F4_TEXTO,1,20)
				EndIf
			EndIf
			
			DbSelectArea("SD2")
			SD2->(DbSkip())
		End
		
		// Dados Complementares para os Itens Servico.
		//		If Len(aServico) > 0
		//			nSerAliq := GETMV("MV_ALIQISS")
		//			nSerBase	:= SF2->F2_BASEISS
		//			nSerVlr	:= SF2->F2_VALISS
		//		EndIf
		
		// Monta Descricao da C.F.O.P.
		If len(aCfo) > 1
			cCfop := Alltrim(Transform(aCfo[1,1],"@R 9.999"))+ "/" +;
			Alltrim(Transform(aCfo[2,1],"@R 9.999"))
		ElseIf !Empty(aCfo)
			cCfop	:= Alltrim(Transform(aCfo[1,1],"@R 9.999"))
		EndIf
		
		***************************************************************************************************
		// CORRECAO DE PROBLEMA , NAO IMPRIMIA OS DADOS DO FORNECEDOR
		***************************************************************************************************
		
		IF At(SF2->F2_TIPO,"DB") != 0
			//		IF SF2->F2_TIPO == "D" .OR. SF2->F2_TIPO == "B"
			
			DbSelectArea("SA2")
			DbSetOrder(1)
			DbGotop()
			DbSeek(xFilial("SA2")+SF2->F2_CLIENTE+SF2->F2_LOJA)
			cSA1Cod 	:=SA2->A2_COD             	// Codigo do Cliente
			cSA1Razao	:=SA2->A2_NOME            	// Nome
			cSA1End	 	:=SA2->A2_END             	// Endereco
			cSA1Bairro 	:=SA2->A2_BAIRRO       		// Bairro
			cSA1Cep	 	:=SA2->A2_CEP             	// CEP
			cSA1Mun 	:=SA2->A2_MUN             	// Municipio
			cSA1Uf	 	:=SA2->A2_EST             	// Estado
			cSA1Cnpj 	:=SA2->A2_CGC             	// CGC
			cSA1Insc	:=SA2->A2_INSCR           	// Inscricao estadual
			cSA1Fone 	:=SA2->A2_TEL             	// Telefone
			
			// Endereco de Cobranca
			cCobEnd 	:="" //SA2->A1_ENDCOB      // Endereco
			cCobBair	:="" //SA2->A1_BAIRROC  	// BAIRRO
			cCobCep		:="" //SA2->A1_CEPC		   // CEP
			cCobMun		:="" //SA2->A1_MUNC	  		// MUNICIPIO
			cCobUf		:="" //SA2->A1_ESTC	  		// ESTADO
			
			// Endereco de Entrega
			cEntEnd 	:="" //SA2->A1_ENDENT      // Endereco
			cEntBair	:="" //SA2->A1_BAIRROE  	// BAIRRO
			cEntCep		:="" //SA2->A1_CEPE		   // CEP
			cEntMun		:="" //SA2->A1_MUNE	  		// MUNICIPIO
			cEntUf		:="" //SA2->A1_ESTE	  		// ESTADO
			
		ELSE
			
			DbSelectArea("SA1")
			DbSetOrder(1)
			DbGotop()
			DbSeek(xFilial("SA1")+SF2->F2_CLIENTE+SF2->F2_LOJA)
			cSA1Cod 	:=SA1->A1_COD             	// Codigo do Cliente
			cSA1Razao	:=Alltrim(SA1->A1_NOME)   	// Nome
			cSA1End	 	:=Alltrim(SA1->A1_END)     	// Endereco
			cSA1Bairro 	:=Alltrim(SA1->A1_BAIRRO)	// Bairro
			cSA1Cep	 	:=Alltrim(SA1->A1_CEP)     	// CEP
			cSA1Mun 	:=Alltrim(SA1->A1_MUN)     	// Municipio
			cSA1Uf	 	:=Alltrim(SA1->A1_EST)     	// Estado
			cSA1Cnpj 	:=Alltrim(SA1->A1_CGC)     	// CGC
			cSA1Insc	:=Alltrim(SA1->A1_INSCR)   	// Inscricao estadual
			cSA1Fone 	:=Alltrim(SA1->A1_TEL)     	// Telefone
			
			// Endereco de Cobranca
			cCobEnd 	:=SA1->A1_ENDCOB          	// Endereco
			cCobBair	:=SA1->A1_BAIRROC		  		// BAIRRO
			cCobCep		:=SA1->A1_CEPC		      	// CEP
			cCobMun		:=SA1->A1_MUNC			  		// MUNICIPIO
			cCobUf		:=SA1->A1_ESTC			  		// ESTADO
			cCGCCob     :=SA1->A1_CGCC           // CGC
			
			// Endereco de Entrega
			DbSelectArea("SC5")
			IF !EMPTY(SC5->C5_CLIENT)
				If SA1->(DbSeek(xFilial("SA1")+SC5->C5_CLIENT+SC5->C5_LOJAENT))
					cEntEnd 	:=SA1->A1_END           	// Endereco de Entrega
					cEntBair	:=SA1->A1_BAIRRO		  		// BAIRRO DE Entrega
					cEntCep		:=SA1->A1_CEP		      	// CEP DE ENTREGA
					cEntMun		:=SA1->A1_MUN			  		// MUNICIPIO DE ENTREGA
					cEntUf		:=SA1->A1_EST			  		// ESTADO DE ENTREGA
				EndIF
			ElseIf (SC5->C5_LOJACLI != SC5->C5_LOJAENT)
				If SA1->(DbSeek(xFilial("SA1")+SC5->C5_CLIENTE+SC5->C5_LOJAENT))
					cEntEnd 	:=SA1->A1_END           	// Endereco de Entrega
					cEntBair	:=SA1->A1_BAIRRO		  		// BAIRRO DE Entrega
					cEntCep		:=SA1->A1_CEP		      	// CEP DE ENTREGA
					cEntMun		:=SA1->A1_MUN			  		// MUNICIPIO DE ENTREGA
					cEntUf		:=SA1->A1_EST			  		// ESTADO DE ENTREGA
				EndIf
			ElseIF !EMPTY(SA1->A1_ENDENT)
				cEntEnd 		:=SA1->A1_ENDENT          	// Endereco de Entrega
				cEntBair		:=SA1->A1_BAIRROE		  		// BAIRRO DE Entrega
				cEntCep			:=SA1->A1_CEPE		      	// CEP DE ENTREGA
				cEntMun			:=SA1->A1_MUNE			  		// MUNICIPIO DE ENTREGA
				cEntUf			:=SA1->A1_ESTE			  		// ESTADO DE ENTREGA
			Else
				cEntEnd 		:=""
				cEntBair		:=""
				cEntCep			:=""
				cEntMun			:=""
				cEntUf			:=""
			EndIf
			
		ENDIF
		
		***************************************************************************************************
		// CORRECAO DE PROBLEMA , NAO IMPRIMIA OS DADOS DO FORNECEDOR
		***************************************************************************************************
		
		cDoc			:=	SF2->F2_DOC             // Numero
		cSerie      	:=	SF2->F2_SERIE           // Serie
		dEmissao    	:=	SF2->F2_EMISSAO         // Data de Emissao
		cSA4Cod			:=  SF2->F2_TRANSP				// Codigo Transportadora
		cTranRedes  	:=  SF2->F2_REDESP				// Codigo Transportadora Redespacho
		cHora       	:=  SF2->F2_HORA
		
		// Calculos
		nBaseIcms  		:=	SF2->F2_BASEICM         // Base   do ICMS
		nVlrIcms		:=	SF2->F2_VALICM          // Valor  do ICMS
		nBaseSubs   	:=	SF2->F2_BRICMS		  		// Base do ICMS retido
		nVlrSubs   		:=	SF2->F2_ICMSRET         // Valor  do ICMS Retido
		nVlrPro 		:=	SF2->F2_VALMERC 			// Valor  da Mercadoria
		
		nVlrFret		:= SF2->F2_FRETE           // Valor do Frete
		nVlrOut			:= 0
		nVlrSeg     	:= SF2->F2_SEGURO          // Valor do Seguro
		nVlrIpi			:= SF2->F2_VALIPI          // Valor  do IPI
		nVlrFat    		:= SF2->F2_VALFAT          // Valor Total da Fatura
		If nVlrFat == 0
			nVlrFat := SF2->F2_VALMERC+SF2->F2_VALIPI+SF2->F2_SEGURO+SF2->F2_FRETE
		endif
		
		If !Empty(cSA4Cod)
			DbSelectArea("SA4")
			DbSetOrder(1)
			DbGotop()
			If DbSeek(xFilial("SA4")+cSA4Cod,.T.)
				cSA4Razao	:=	SA4->A4_NOME           // Nome Transportadora
				cSA4End  	:=	SA4->A4_END            // Endereco
				cSA4Mun  	:=	SA4->A4_MUN            // Municipio
				cSA4Uf  	:=	SA4->A4_EST            // Estado
				cSA4Cnpj 	:=	SA4->A4_CGC            // CGC
				cSA4Insc	:=	SA4->A4_INSEST			  // Inscricao Estadual
			Endif
		EndIf
		
		// Informacoes da Transportadora Redespacho
		
		If !Empty(cTranRedes)
			DbSelectArea("SA4")
			DbSetOrder(1)
			DbGotop()
			If DbSeek(xFilial("SA4")+cTranRedes,.T.)
				cNomeRedes  :=	SA4->A4_NOME           // Nome Transportadora Redespacho
				cMunRedes	:=	SA4->A4_MUN            // Municipio
				cUFRedes	:=	SA4->A4_EST            // Estado
				cFoneRedes  := IIF (EMPTY(SA4->A4_DDD), Alltrim(SA4->A4_TEL), "(" + Alltrim(SA4->A4_DDD) + ") " + Alltrim(SA4->A4_TEL)) // DDD + Telefone
			Endif
		EndIf
		
		nQtdVol		:=	SF2->F2_VOLUME1         // Volume 1 no Pedido
		cEspecie	:=	SF2->F2_ESPECI1		  	// Especie 1 da NF
		cMarca	    :=  "DELPI"
		nPesoBru	:=	SF2->F2_PBRUTO          // Peso Bruto
		nPesoLiq	:=	SF2->F2_PLIQUI          // Peso Liquido
		
		GeraDuplic()
		
		Imprime()
		//			RptStatus({|| RunReport(Cabec1,Cabec2,Titulo,nLin) },Titulo)
		
		DbSelectArea("SF2")
		SF2->(DbSkip())
	EndDo
	
ElseIf MV_PAR04 == 2
	lPrimImp	:= .T.
	DbSelectArea("SF1")                //  ENTRADA
	DbSetOrder(1)
	DbGotop()
	DbSeek(xFilial("SF1")+MV_PAR01,.T.)
	While !eof() .And. SF1->F1_FILIAL == xFilial("SF1");
		.And. SF1->F1_DOC    <= MV_PAR02
		
		If SF1->F1_SERIE <> MV_PAR03    // Se a Serie do Arquivo for Diferente
			DbSkip()                    // do Parametro Informado !!!
			Loop
		Endif
		
		IF lAbortPrint
			@ 00,01 PSAY "** CANCELADO PELO OPERADOR **"
			lContinua := .F.
			Exit
		Endif
		
		//Inicializacao das Variaveis do Corpo da Nota Fiscal.
		InicVar()
		
		cChave  := "D1_FILIAL+D1_DOC+D1_SERIE+D1_CF+D1_COD"
		nIndSD1 := 0
		DbSelectarea("SIX")
		DbSeek("SD1")
		While !eof() .and. SIX->INDICE == "SD1"
			nIndSD1 ++
			If alltrim(cChave) == alltrim(SIX->chave)
				Exit
			Endif
			DbSkip()
		End
		
		DbSelectArea("SD1")                // * Itens da Nota Fiscal de Entrada
		DbSetOrder(nIndSD1)
		DbSeek(xFilial("SD1")+SF1->F1_DOC,.T.)
		While !eof() .And. SD1->D1_FILIAL == xFilial("SD1");
			.And. SD1->D1_DOC    == SF1->F1_DOC;
			.And. SD1->D1_SERIE  == SF1->F1_SERIE
			
			DbSelectArea("SB1")
			DbSetOrder(1)
			DbGotop()
			DbSeek(xFilial("SB1")+SD1->D1_COD)
			cOrig1 	:= Substr(SB1->B1_ORIGEM,1,1)
			cDescSB1	:= Substr(SB1->B1_DESC,1,30)
			
			DbSelectArea("SF4")
			DbSetOrder(1)
			DbGotop()
			Dbseek(xFilial("SF4")+SD1->D1_TES)
			cOrig2 := cOrig1+Substr(SF4->F4_SITTRIB,1,2)
			
			npos := 0
			npos := Ascan(aItem,{|x| (x[1]) == SD1->D1_COD})
			If nPos == 0
				Aadd(aItem,{SD1->D1_COD,;			//1
				cDescSB1,;           //2
				cClasFisc,;          //3
				cOrig2,;             //4
				SD1->D1_UM,;         //5
				SD1->D1_QUANT,;      //6
				SD1->D1_VUNIT,;      //7
				SD1->D1_TOTAL,;      //8
				SD1->D1_IPI,;        //9
				SD1->D1_PICM,;       //10
				SD1->D1_VALIPI,;     //11
				SD1->D1_IDENTB6})    //12
			EndIf
			
			npos := 0
			npos := Ascan(aCfo,{|x| (x[1]) == SD1->D1_CF})
			If nPos == 0
				DbSelectArea("SF4")
				Dbsetorder(1)
				Dbseek(xFilial("SF4")+SD1->D1_TES,.T.)
				Aadd(aCfo,{SD1->D1_CF,SF4->F4_TEXTO})
				If lPrim
					lPrim := .F.
					cNatureza := Substr(SF4->F4_TEXTO,1,20)
				ElseIf lSegun
						lSegun := .F.
						cNatureza := Alltrim(cNatureza)+"/"+Substr(SF4->F4_TEXTO,1,20)
				EndIf
			EndIf

			If !EMPTY(SD1->D1_NFORI)
				Aadd(aNFOriginal,{SD1->D1_NFORI,Len(Alltrim(SD1->D1_NFORI)),SD1->D1_SERIORI,Len(Alltrim(SD1->D1_SERIORI)),"E"})
			EndIf
			
			DbSelectArea("SD1")
			SD1->(Dbskip())
		End
		
		// Monta Descricao da C.F.O.P.
		/*
		If len(aCfo) > 1
			cCfop := Alltrim(Transform(aCfo[1,1],"@R 9.999"))+ "/" +;
			Alltrim(Transform(aCfo[2,1],"@R 9.999"))
		Else
			cCfop	:= Alltrim(Transform(aCfo[1,1],"@R 9.999"))
		EndIf
		*/
			cCfop	:= Alltrim(Transform(aCfo[1,1],"@R 9.999"))
		
		dbSelectArea("SB1")                     // * Desc. Generica do Produto
		dbSetOrder(1)
		
		If SF1->F1_TIPO == "D"
			DbSelectArea("SA1")                // * Cadastro de Clientes
			DbSetOrder(1)
			DbSeek(xFilial("SA1")+SF1->F1_FORNECE+SF1->F1_LOJA)
			cSA1Cod 		:=SA1->A1_COD             	// Codigo do Cliente
			cSA1Razao	:=SA1->A1_NOME            	// Nome
			cSA1End	 	:=SA1->A1_END             	// Endereco
			cSA1Bairro 	:=SA1->A1_BAIRRO       		// Bairro
			cSA1Cep	 	:=SA1->A1_CEP             	// CEP
			cSA1Mun 		:=SA1->A1_MUN             	// Municipio
			cSA1Uf	 	:=SA1->A1_EST             	// Estado
			cSA1Cnpj 	:=SA1->A1_CGC             	// CGC
			cSA1Insc		:=SA1->A1_INSCR           	// Inscricao estadual
			cSA1Fone 	:=SA1->A1_TEL             	// Telefone
			
			// Endereco de Cobranca
			cCobEnd 		:=SA1->A1_ENDCOB          	// Endereco
			cCobBair		:=SA1->A1_BAIRROC		  		// Bairro
			cCobCep		:=SA1->A1_CEPC		      	// CEP
			cCobMun		:=SA1->A1_MUNC			  		// MUNICIPIO
			cCobUf		:=SA1->A1_ESTC			  		// ESTADO
			
			// Endereco de Entrega
			cEntEnd 		:=SA1->A1_ENDENT          	// Endereco
			cEntBair		:=SA1->A1_BAIRROE		  		// Bairro
			cEntCep		:=SA1->A1_CEPE		      	// CEP
			cEntMun		:=SA1->A1_MUNE			  		// MUNICIPIO
			cEntUf		:=SA1->A1_ESTE			  		// ESTADO
		Else
			DbSelectArea("SA2")                // * Cadastro de Fornecedores
			DbSetOrder(1)
			DbSeek(xFilial()+SF1->F1_FORNECE+SF1->F1_LOJA)
			cSA1Cod 		:=SA2->A2_COD             	// Codigo do Cliente
			cSA1Razao	:=SA2->A2_NOME            	// Nome
			cSA1End	 	:=SA2->A2_END             	// Endereco
			cSA1Bairro 	:=SA2->A2_BAIRRO       		// Bairro
			cSA1Cep	 	:=SA2->A2_CEP             	// CEP
			cSA1Mun		:=SA2->A2_MUN             	// Municipio
			cSA1Uf	 	:=SA2->A2_EST             	// Estado
			cSA1Cnpj 	:=SA2->A2_CGC             	// CGC
			cSA1Insc	:=SA2->A2_INSCR           	// Inscricao estadual
			cSA1Fone 	:=SA2->A2_TEL             	// Telefone
		EndIf
		
		cDoc     		:=	SF1->F1_DOC             // Numero
		cSerie      	:=	SF1->F1_SERIE           // Serie
		dEmissao    	:=	SF1->F1_EMISSAO         // Data de Emissao
		cSA4Cod			:= SF1->F1_TRANSP
		cTpFrete    	:=	SF1->F1_TPFRETE         // Tipo de Entrega
		cPlaca		 	:= SF1->F1_PLACA
		cTexLeg1		:= SF1->F1_TEXT1
		cTexLeg2		:=	SF1->F1_TEXT2
		cMsg1			:= SF1->F1_MENSNF1
		cMsg2			:= SF1->F1_MENSNF2
		cMsg3			:= SF1->F1_MENSNF3
		
		// Calculos
		nBaseIcms	:= SF1->F1_BASEICM         // Base   do ICMS
		nVlrIcms 	:= SF1->F1_VALICM          // Valor  do ICMS
		nBaseSubs   :=	SF1->F1_BRICMS          // Base do ICMS Retido
		nVlrSubs   	:=	SF1->F1_ICMSRET         // Valor  do ICMS Retido
		nVlrPro 	:=	SF1->F1_VALMERC         // Valor  da Mercadoria
		
		nVlrOut		:= 0
		nVlrFret	:=	0.00                    // Frete
		nVlrSeg		:=	0.00                    // Seguro
		nVlrIpi  	:=	SF1->F1_VALIPI          // Valor  do IPI
		nVlrFat    	:=	SF1->F1_VALBRUT         // Valor Bruto da Compra
		
		If !Empty(cSA4Cod)
			DbSelectArea("SA4")
			DbSetOrder(1)
			DbGotop()
			If DbSeek(xFilial("SA4")+cSA4Cod,.T.)
				cSA4Razao	:=	SA4->A4_NOME           // Nome Transportadora
				cSA4End  	:=	SA4->A4_END            // Endereco
				cSA4Mun  	:=	SA4->A4_MUN            // Municipio
				cSA4Uf 		:=	SA4->A4_EST            // Estado
				cSA4Cnpj 	:=	SA4->A4_CGC            // CGC
				cSA4Insc	:=	SA4->A4_INSEST			  // Inscricao Estadual
			Endif
		EndIf
		
		nQtdVol		:=	SF1->F1_VOLUME1			// Volume 1 no Pedido
		cEspecie	:=	SF1->F1_ESPECI1			// Especie 1 da NF
		cMarca		:=  SF1->F1_MARCA
		nPesoBru	:=	SF1->F1_PESOB          	// Peso Bruto
		nPesoLiq	:=	SF1->F1_PESOL          	// Peso Liquido
		
		GeraDuplic()
		
		Imprime()
		
		DbSelectArea("SF1")
		SF1->(DbSkip())                     // e passa para a proxima Nota Fiscal
	EndDo
	
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Finaliza a execucao do relatorio                                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
SET DEVICE TO SCREEN

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Se impressao em disco, chama o gerenciador de impressao             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If aReturn[5]==1
	dbCommitAll()
	SET PRINTER TO
	OurSpool(wnrel)
Endif
MS_FLUSH()

Return

Static Function ClasFisc()

npFisc := aScan(aFiscal,{|x| (x[1]) == SB1->B1_POSIPI})

If npFisc == 0
	Aadd(aFiscal,{SB1->B1_POSIPI})
EndIf

npFisc := aScan(aFiscal,{|x| (x[1]) == SB1->B1_POSIPI})

Do Case
	Case npFisc == 1
		cClasFisc := "A"
	Case npFisc == 2
		cClasFisc := "B"
	Case npFisc == 3
		cClasFisc := "C"
	Case npFisc == 4
		cClasFisc := "D"
	Case npFisc == 5
		cClasFisc := "E"
	Case npFisc == 6
		cClasFisc := "F"
EndCase

npos := Ascan(aPosIpi,{|x| (x[1]) == SB1->B1_POSIPI })
If  nPos == 0
	Aadd(aPosIpi,{SB1->B1_POSIPI,cClasFisc})
EndIf

Return

Static Function GeraDuplic()

aDuplic  := {}

If MV_PAR04 == 1
	DbSelectArea("SE1")
	DbSetOrder(1)
	DbSeek(xFilial("SE1")+cSerie+cDoc,.T.)
	While !Eof()	.And. SE1->E1_FILIAL	 	==  xFilial("SE1");
		.And. SE1->E1_PREFIXO	==	 cSerie;
		.And. SE1->E1_NUM			==  cDoc
		
		If !("NF" $ SE1->E1_TIPO)
			DbSelectArea("SE1")
			SE1->(DbSkip())
			Loop
		Endif
		
		Aadd(aDuplic,{SE1->E1_NUM,SE1->E1_PARCELA,SE1->E1_VENCTO,SE1->E1_VALOR})
		
		DbSelectArea("SE1")
		SE1->(DbSkip())
	EndDo
Else
	DbSelectArea("SE2")
	DbSetOrder(1)
	DbGotop()
	DbSeek(xFilial("SE2")+cSerie+cDoc,.T.)
	While !Eof()	.And. SE2->E2_FILIAL	 	==  xFilial("SE2");
		.And. SE2->E2_PREFIXO	==	 cSerie;
		.And. SE2->E2_NUM			==  cDoc
		
		If (ALLTRIM(SE2->E2_TIPO) <> "TX")
			DbSelectArea("SE2")
			SE2->(DbSkip())
			Loop
		Endif
		
		Aadd(aDuplic,{SE2->E2_NUM,SE2->E2_PARCELA,SE2->E2_VENCTO,SE2->E2_VALOR})
		
		DbSelectArea("SE2")
		SE2->(DbSkip())
	EndDo
EndIf

Return

//Static Function RunReport()
Static Function Imprime()

// Impressao Cabecalho
ImpCab()

// Impressao das duplicatas.
ImpDuplic()

// Impressao Itens
ImpItem()

// Impressao Itens
//If Len(aServico) > 0
//	ImpServ()
//EndIf

// Impressao Rodape
ImpTotais()

// Impressao Transportadora
Transport()

nLin := 76
// Impressao dos Pedidos de Vendas conforme os Itens das Notas Fiscais.
//If Len(aPedidos) > 0
//	ImpPed()
//EndIf

// Impressao dos Numeros das Notas Fiscais de Devolucao de Terceiros.
If Len(aNFOriginal) > 0
	ImpNFO()
EndIf

// Impressao Textos Legais
Texto()

// Impressao Endereco de Entrega
Entrega()

// Impressao Endereco de Cobranca
Cobranca()

// Impressao de Redespacho
//If !Empty(cTranRedes)
//	@ nLin,000 PSAY "Redespacho: "+Alltrim(cNomeRedes) + " " + Alltrim(cMunRedes)	+ " - " + cUFRedes + " " + cFoneRedes
//	nLin++
//EndIf

// Impressao Classificacao Fiscal
ImpClasFis()

@ 089,140 PSAY cDoc
@ 096,140 PSAY "  "			  // Posiciona na proxima pagina.
Return

Static Function ImpCab()

SetPrc(0,0)
@ 000,000 PSAY CHR(15)  // compactado
@ 000,000 PSAY CHR(27)+CHR(48)  	//1/6"  DIMUNUI O TAMANHO ENTRE AS LINHAS.


If MV_PAR04 == 1
	@ 001,107 PSAY "XX"
Else
	@ 001,122 PSAY "XX"
Endif
@ 001,146 PSAY cDoc
                   

@ 009,000 PSAY Substr(cNatureza,1,40)
@ 009,045 PSAY Substr(cCfop,1,11)
@ 009,059 PSAY Alltrim(cSubsTrib)

@ 012,000 PSAY Substr(cSA1Razao,1,40)
If !Empty(cSA1Cnpj)
	@ 012,100 PSAY Transform(cSA1Cnpj,PesqPict("SA1","A1_CGC"))
EndIf
@ 012,146 PSAY dEmissao

@ 014,000 PSAY Substr(cSA1End,1,40)
@ 014,081 PSAY Substr(cSA1Bairro,1,30)
If !Empty(cSA1Cep)
	@ 014,123 PSAY Transform(cSA1Cep,PesqPict("SA1","A1_CEP"))
EndIf
@ 014,146 PSAY dEmissao

@ 016,000 PSAY Substr(cSA1Mun,1,15)
@ 016,062 PSAY Substr(cSA1Fone,1,15)
@ 016,094 PSAY cSA1Uf
@ 016,105 PSAY cSA1Insc
If !Empty(cHora)
	@ 016,146 PSAY cHora
Else
	@ 016,146 PSAY Space(05)
EndIf

Return

Static Function ImpDuplic()

nLin := 020

For bb := 1 to Len(aDuplic)
	If bb == 1 .Or. bb == 4 .Or. bb == 7
		If bb == 1
			@ nLin, 002 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 020 PSAY aDuplic[bb,3]
			@ nLin, 036 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		ElseIf bb == 4
			nLin := nLin + 1
			@ nLin, 002 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 020 PSAY aDuplic[bb,3]
			@ nLin, 036 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		ElseIf bb == 7
			nLin := nLin + 1
			@ nLin, 002 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 020 PSAY aDuplic[bb,3]
			@ nLin, 036 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		EndIf
	ElseIf bb == 2 .Or. bb == 5 .Or. bb == 8
		If bb == 2
			@ nLin, 057 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 073 PSAY aDuplic[bb,3]
			@ nLin, 091 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		ElseIf bb == 5
			@ nLin, 057 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 073 PSAY aDuplic[bb,3]
			@ nLin, 091 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		ElseIf bb == 8
			@ nLin, 057 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 073 PSAY aDuplic[bb,3]
			@ nLin, 091 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		EndIf
	ElseIf bb == 3 .Or. bb == 6 .Or. bb == 9
		
		If bb == 3
			@ nLin, 113 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 128 PSAY aDuplic[bb,3]
			@ nLin, 143 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		ElseIf bb == 6
			@ nLin, 113 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 128 PSAY aDuplic[bb,3]
			@ nLin, 143 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		ElseIf bb == 9
			@ nLin, 113 PSAY aDuplic[bb,1] + " " + aDuplic[bb,2]
			@ nLin, 128 PSAY aDuplic[bb,3]
			@ nLin, 143 PSAY Transform(aDuplic[bb,4],"@E 9,999,999.99")
		EndIf
		
	EndIf
Next

Return

Static Function ImpItem()
nTamDet 	:= 34
nLin		:= 26

aItem := Asort(aItem,,,{|x,y|x[12]<y[12]}) // Ordem Crescente

lterc := .t.
For i := 1 to Len(aItem)
	If  !Empty(aItem[i,12]) .and. lterc
	    @ nlin, 000 PSAY Replicate(" ",132)
	    nLin++
		lterc := .f.		    
	EndIf

	If i <= nTamDet
		@ nLin, 000  PSAY Alltrim(aItem[i,1])  				// Codigo Produto
		@ nLin, 010  PSAY Alltrim(Substr(aItem[i,2],1,40)) // Descricao Produto
		If Empty(aItem[i,3])
			@ nLin, 060  PSAY " "									// Classificacao Fiscal
		Else
			@ nLin, 060  PSAY aItem[i,3]							// Classificacao Fiscal
		EndIf
		If Empty(aItem[i,4])
			@ nLin, 065  PSAY "   "  // Situacao Tributaria
		Else
			@ nLin, 065  PSAY Alltrim(Substr(aItem[i,4],1,3))  // Situacao Tributaria
		EndIf
		If (substr(cCfop,1,5) != "1.604")
			//@ nLin, 080  PSAY Transform(0,"@E 99999.999")   	// Quantidade
			//@ nLin, 094  PSAY Transform(0,"@E 999999.99999")	// Valor Unitario
			//@ nLin, 114  PSAY Transform(0,"@E 9999,999.99") 	// Valor Total
			//@ nLin, 131  PSAY Transform(0,"@E 99.99")  			// Percentual Icms
			//@ nLin, 137  PSAY Transform(0,"@E 99.99")			// Percentual IPI
			//@ nLin, 146  PSAY Transform(0,"@E 99,999.99")		// Valor do IPI
		//Else
			@ nLin, 074  PSAY aItem[i,5]								// Unidade de Medida
			@ nLin, 080  PSAY Transform(aItem[i,6],"@E 99999.999")   	// quantidade
			@ nLin, 094  PSAY Transform(aItem[i,7],"@E 999999.99999")	// Valor Unitario
			@ nLin, 114  PSAY Transform(aItem[i,8],"@E 9999,999.99") 	// Valor Total
			@ nLin, 131  PSAY Transform(aItem[i,10],"@E 99.99")  		// Percentual Icms
			If !Empty(aItem[i,9])	// Percentual IPI
				@ nLin, 137  PSAY Transform(aItem[i,9],"@E 99.99")
				@ nLin, 146  PSAY Transform(aItem[i,11],"@E 99,999.99")
			EndIf		
		EndIf
	Else
		@ nLin, 000  PSAY "*******  CONTINUA NO PROXIMO FORMULARIO  ********"
		
		@ 063,011  PSAY "**************"
		@ 063,036  PSAY "**************"
		@ 063,075  PSAY "**************"
		@ 063,105  PSAY "**************"
		@ 063,138  PSAY "**************"
		
		@ 065,011  PSAY "**************"
		@ 065,036  PSAY "**************"
		@ 065,075  PSAY "**************"
		@ 065,105  PSAY "**************"
		@ 065,138  PSAY "**************"
		
		@ 089,140 PSAY cDoc
		@ 096,140 PSAY "  "			  // Posiciona na proxima pagina.
		
		ImpCab()
		
		nTamDet := nTamDet + 15
		
		i := i - 1
		nLin := 22
		
	EndIf
	
	nLin :=nLin+1
	
Next i

Return

/*
Static Function ImpServ()
nTamSer 	:= 5
nLin		:= 50

For i := 1 to Len(aServico)
If i <= nTamSer
@ nLin, 004  PSAY aServico[i,2]  											// Descricao Produto
@ nLin, 105  PSAY Transform(aServico[i,6],"@E 999,999.99")   		// quantidade
@ nLin, 120  PSAY Transform(aServico[i,7],"@E 99,999,999.99")		// Valor Unitario
@ nLin, 146  PSAY Transform(aServico[i,8],"@E 999,999,999.99") 	// Valor Total
nSerTot := nSerTot + aServico[i,8]
EndIf
nLin :=nLin+1
Next [i]
@ 055,045 PSAY Transform(nSerAliq,"@E 999,999,999.99")
@ 055,084 PSAY Transform(nSerBase,"@E 999,999,999.99")
@ 055,114 PSAY Transform(nSerVlr ,"@E 999,999,999.99")
@ 055,146 PSAY Transform(nSerTot ,"@E 999,999,999.99")

Return
*/

Static Function ImpTotais()
If !Empty(cNSU)
   @ 060,011 PSAY 'NSU: '+cNSU
EndIf   
cMsg := ""
If !Empty(cPEDCLI)
	cMsg += "Ped. Cliente: " + cPEDCLI + Space(5)
EndIf
If !Empty(cREDESP)
	cMsg += "Redespacho: " + cREDESP + Space(5)
EndIf
If !Empty(cMsg)
   @ 061,011 PSay cMsg
EndIf
 

                      

If (substr(cCfop,1,5) == "1.604")
	@ 063, 011  PSAY Transform(0		,"@E 999,999,999.99")  	// Base do ICMS	
	@ 063, 036  PSAY Transform(aItem[1,7],"@E 999,999,999.99")  	// Valor do ICMS
	@ 063, 075  PSAY Transform(0		,"@E 999,999,999.99")  	// Base ICMS Ret.
	@ 063, 105  PSAY Transform(0 		,"@E 999,999,999.99")  	// Valor  ICMS Ret.
	@ 063, 138  PSAY Transform(0 		,"@E 999,999,999.99")	// Valor Tot. Prod.

	@ 065, 011  PSAY Transform(0 ,"@E 999,999,999.99")  	// Valor do Frete
	@ 065, 036  PSAY Transform(0 ,"@E 999,999,999.99")  	// Valor Seguro
	@ 065, 075  PSAY Transform(0 ,"@E 999,999,999.99")  	// Valor Seguro
	@ 065, 105  PSAY Transform(0 ,"@E 999,999,999.99")  	// Valor do IPI
	@ 065, 138  PSAY Transform(0 ,"@E 999,999,999.99")  	// Valor Total NF soma dos Itens
Else
	@ 063, 011  PSAY Transform(nBaseIcms,"@E 999,999,999.99")  	// Base do ICMS
	@ 063, 036  PSAY Transform(nVlrIcms ,"@E 999,999,999.99")  	// Valor do ICMS
	@ 063, 075  PSAY Transform(nBaseSubs,"@E 999,999,999.99")  	// Base ICMS Ret.
	@ 063, 105  PSAY Transform(nVlrSubs ,"@E 999,999,999.99")  	// Valor  ICMS Ret.
	@ 063, 138  PSAY Transform(nVlrPro  ,"@E 999,999,999.99")	// Valor Tot. Prod.

	@ 065, 011  PSAY Transform(nVlrFret,"@E 999,999,999.99")  	// Valor do Frete
	@ 065, 036  PSAY Transform(nVlrSeg ,"@E 999,999,999.99")  	// Valor Seguro
	@ 065, 075  PSAY Transform(nVlrOut ,"@E 999,999,999.99")  	// Valor Seguro
	@ 065, 105  PSAY Transform(nVlrIpi ,"@E 999,999,999.99")  	// Valor do IPI
	If (nVlrTotNF > nVlrFat)
		@ 065, 138  PSAY Transform(nVlrTotNF ,"@E 999,999,999.99")  	// Valor Total NF soma dos Itens
	Else
		@ 065, 138  PSAY Transform(nVlrFat ,"@E 999,999,999.99")  	// Valor Total NF
	EndIf
EndIf
Return

Static Function Transport()

If !Empty(cSA4Cod)
	
	@ 069,000 PSAY cSA4Razao
	
	If cTpFrete == "C"       // Frete por conta do
		@ 069,090 PSAY "1"    // Emitente (1)
	Else                     //     ou
		@ 069,090 PSAY "2"    // Destinatario (2)
	Endif
	
	@ 069,108 PSAY cPlaca
	@ 069,117 PSAY cUfPlaca
	If !Empty(cSA4Cnpj)
		@ 069,126 PSAY Transform(cSA4Cnpj,PesqPict("SA4","A4_CGC"))
	EndIf
	
	@ 071,000 PSAY cSA4End
	@ 071,086 PSAY cSA4Mun
	@ 071,115 PSAY cSA4Uf
	@ 071,126 PSAY cSA4Insc
	
	@ 073,000 PSAY Transform(nQtdVol,"@E 999,999.99")
	@ 073,021 PSAY cEspecie
	@ 073,078 PSAY cMarca
	@ 073,116 PSAY Transform(nPesoBru,"@E 999,999.99")
	@ 073,140 PSAY Transform(nPesoLiq,"@E 999,999.99")
EndIf

Return

/*
Static Function ImpPed()
If Len(aPedidos) > 0
// Controla a quantidade de pedidos para a nota fiscal.
// O Cliente necessita imprimir todos os pedidos daquela nota fiscal.
cPedLi1	:= ""
cPedLi2	:= ""
cPedidos	:= ""
cBarra	:= ";"
lPrim1 	:= .T.
lPrim2	:= .T.

For aa := 1 to Len(aPedidos)
nCont := (Len(cPedidos) + aPedidos[aa,2] + 1)
Do Case
Case nCont <= 79
If lPrim1
cPedidos := "PEDIDOS:" + AllTrim(aPedidos[aa,1])
cPedLi1	:= "PEDIDOS:" + AllTrim(aPedidos[aa,1])
lPrim1 := .F.
Else
cPedidos := cPedidos + cBarra + AllTrim(aPedidos[aa,1])
cPedLi1	:= cPedLi1	+ cBarra + AllTrim(aPedidos[aa,1])
EndIF
Case nCont > 79 .And. nCont <= 158
If lPrim2
cPedidos := AllTrim(aPedidos[aa,1])
cPedLi2	:= AllTrim(aPedidos[aa,1])
lPrim2 := .F.
Else
cPedidos := cPedidos + cBarra + AllTrim(aPedidos[aa,1])
cPedLi2	:= cPedLi2	+ cBarra + AllTrim(aPedidos[aa,1])
EndIf
EndCAse
Next
EndIf

nLin	:= 70
If !Empty(cPedLi1)
@ nLin,004 PSAY cPedLi1
nLin := nLin + 1
EndIf

If !Empty(cPedLi2)
@ nLin,004 PSAY cPedLi2
nLin := nLin + 1
EndIf
aPedidos := {}
Return
*/

// INCLUIDO POR MARCOS PARA IMPRIMIR AS NFs ORIGINAIS DO CASO DE DEVOLUCAO
// DE PODER DE TERCEIROS/DEVOLUCAO DE MERCADORIAS
Static Function ImpNFO()
cNFOs1	:= ""
cNFOs2	:= ""
cNFOs 	:= ""
cBarra	:= "/"
lPrim1 	:= .T.
lPrim2	:= .T.

aNFOriginal := Asort(aNFOriginal,,,{|x,y|x[6]<y[6]}) // Ordem Crescente

For aa := 1 to Len(aNFOriginal)
	nCont := (Len(cNFOs) + aNFOriginal[aa,2] + 1) + (aNFOriginal[aa,4] + 1)
	//nCont := (Len(cNFOs) + aNFOriginal[aa,2] + 1) + (Len(cNFOs) + aNFOriginal[aa,4] + 1)
	Do Case
		Case nCont <= 79
			If lPrim1                         //19 + 10
				If (aNFOriginal[aa,5] == "S")
					cNFOs := "Retorno suas N.F.s:" + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
					cNFOs1:= "Retorno suas N.F.s:" + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
				Else	
					cNFOs := "Retorno nossa N.Fs:" + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
					cNFOs1:= "Retorno nossa N.Fs:" + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
				EndIf
				lPrim1 := .F.
			Else
				cNFOs := cNFOs  + ", " + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
				cNFOs1:= cNFOs1 + ", " + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
			EndIF
		Case nCont > 79 .And. nCont <= 158
			If lPrim2
				cNFOs := cNFOs := cNFOs  + ", " + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
				cNFOs2:= AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
				lPrim2 := .F.
			Else
				cNFOs := cNFOs  + ", " + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
				cNFOs2:= cNFOs2 + ", " + AllTrim(aNFOriginal[aa,1]) + cBarra + AllTrim(aNFOriginal[aa,3])
			EndIf
	EndCAse
Next

//nLin	:= 70
If !Empty(cNFOs1)
	@ nLin,000 PSAY cNFOs1
	nLin := nLin + 1
EndIf

If !Empty(cNFOs2)
	@ nLin,000 PSAY cNFOs2
	nLin := nLin + 1
EndIf
aNFOriginal := {}
Return

Static Function Texto()

cDText1:=space(40)
cDText2:=space(40)
cDText3:=space(40)
cDText4:=space(40)

If SZ1->(DbSeek(xFilial("SZ1")+cTexLeg1))
	cDText1:=SZ1->Z1_TEXT1
	cDText2:=SZ1->Z1_TEXT2
Endif

If !Empty(cDText1)
	@ nLin,000 PSAY ALLTRIM(cDText1)
	nLin++
EndIf
If !Empty(cDText2)
	@ nLin,000 PSAY ALLTRIM(cDText2)
	nLin++
EndIf

If SZ1->(DbSeek(xFilial("SZ1")+cTexLeg2))
	cDText3:=SZ1->Z1_TEXT1
	cDText4:=SZ1->Z1_TEXT2
Endif

If !Empty(cDText3)
	@ nLin,000 PSAY ALLTRIM(cDText3)
	nLin++
EndIf
If !Empty(cDText4)
	@ nLin,000 PSAY ALLTRIM(cDText4)
	nLin++
EndIf

If Len(aAlmox) > 0
	for i_:= 1 to Len(aAlmox)
		@ nLin,000 PSAY aAlmox[i_]
		nLin++
	next i_
EndIf

If !Empty(cMsg1)
	@ nLin,000 PSAY ALLTRIM(cMsg1)
	nLin++
EndIf

If !Empty(cMsg2)
	@ nLin,000 PSAY ALLTRIM(cMsg2)
	nLin++
EndIf

If !Empty(cMsg3)
	@ nLin,000 PSAY ALLTRIM(cMsg3)
	nLin++
EndIf

Return

// Endereco de Cobranca
Static Function Cobranca()
If !EMPTY(cCobEnd)
	@nLin,000 PSAY "Cobranca: "+Alltrim(cCobEnd)+" - "+ Alltrim(cCobBair)// Endereco de Cobranca
	nLin++
	@nLin,009 PSAY cCobCep+" - "+Alltrim(cCobMun)+" "+cCobUf+" / "
	@nLin,Len(cCobCep+" - "+Alltrim(cCobMun)+" "+cCobUf+" / ") PSAY Transform(cCGCCob,PesqPict("SA1","A1_CGC"))
	nLin++
EndIf
Return

// Endereco de Entrega
Static Function Entrega()
If !EMPTY(cEntEnd)
	@nLin,000 PSAY "Entrega: "+Alltrim(cEntEnd)+" - "+ Alltrim(cEntBair)// Endereco de Cobranca
	nLin++
	@nLin,009 PSAY cEntCep+" - "+Alltrim(cEntMun)+" "+cEntUf+" / "
	nLin++
EndIf
Return

Static Function ImpClasFis()
If Len(aPosIpi) > 0
	nCol := 00
	For m := 1 to len(aPosIpi)
		@ 084,nCol PSAY aPosIpi[m,2] + "-" + aPosIpi[m,1]
		nCol := nCol + 12
	Next
EndIf
Return

Static Function InicVar()
// Cabecalho
cDoc 		:= Space(06)
cSerie		:= Space(03)
cNatureza	:= Space(30)
cCfop		:= Space(10)
cSubsTrib	:= Space(14)
cSA1Razao	:= Space(40)
cSA1Cnpj	:= Space(14)
dEmissao	:= dDataBase
cSA1End		:= Space(40)
cSA1Bairro	:= Space(30)
cSA1Cep		:= Space(08)
dSaida		:= dDataBase
cSA1Mun		:= Space(15)
cSA1Fone	:= Space(15)
cSA1Uf		:= Space(02)
cSA1Insc	:= Space(18)
cHora		:= Space(05)

// Duplicatas
aDuplic		:= {}

// Itens Nota Fiscal
aItem		:= {}

// Itens Servico
aServico	:= {}
nSerAliq	:= 0
nSerBase	:= 0
nSerVlr		:= 0
nSerTot		:= 0

// Calculos
nBaseIcms	:= 0
nVlrIcms	:= 0
nBaseSubs	:= 0
nVlrSubs	:= 0
nVlrPro		:= 0
nVlrFret	:= 0
nVlrSeg		:= 0
nVlrOut		:= 0
nVlrIpi		:= 0
nVlrFat		:= 0
nVlrTotNF	:= 0

// Transportadora
cSA4Cod		:= Space(06)
cSA4Razao	:= Space(40)
cTpFrete	:=	Space(01)
cPlaca		:= Space(08)
cUfPlaca	:=	Space(02)
cSA4Cnpj	:= Space(14)
cSA4End		:= Space(40)
cSA4Mun		:= Space(15)
cSA4Uf		:= Space(02)
cSA4Insc	:= Space(18)
nQtdVol		:= 0
cEspecie	:= Space(10)
cMarca		:= Space(10)
cNumero		:= Space(10)
nPesoBru	:= 0
nPesoLiq	:= 0

// Outras Variaveis Utilizadas
aCfo		:= {}
cTexLeg1	:= Space(03)
cTexLeg2	:= Space(03)
lPrimImp	:= .T.
lPrim		:= .T.
cOrig1		:= Space(01)
cOrig2		:= Space(02)
cDescSB1	:= Space(30)
aPed		:= {}
cMsg1		:= Space(60)
cMsg2		:= Space(60)
cMsg3		:= Space(60)
aAlmox      := {}

// Endereco de Cobranca
cCobEnd 	:= Space(30)	          	// Endereco
cCobBair	:= Space(30)					// BAIRRO
cCobCep		:= Space(08)		      	// CEP
cCobMun		:= Space(15)			  		// MUNICIPIO
cCobUf		:= Space(02)			  		// ESTADO
cCGCCob     := Space(14)					// CGC

// Endereco de Entrega
cEntEnd 	:= Space(30)	          	// Endereco
cEntBair	:= Space(30)			  		// BAIRRO
cEntCep		:= Space(08)		      	// CEP
cEntMun		:= Space(15)			  		// MUNICIPIO
cEntUf		:= Space(02)			  		// ESTADO

cClasFisc	:= Space(01)
npFisc		:= 0
aFiscal		:= {}
aPosIpi		:= {}
aPedidos	:= {}

cTranRedes	:= SPACE(6)               // Codigo da Transportadora Redespacho
cNomeRedes  :=	SPACE(15)              // Nome Transportadora Redespacho
cMunRedes	:=	SPACE(15)              // Municipio
cUFRedes	:=	SPACE(2)               // Estado
cFoneRedes	:=	SPACE(18)              // Telefone

Return

Static Function CriaPergunta(cGrupo,aPer)
LOCAL lRetu := .T., aReg  := {}
LOCAL _l := 1, _m := 1, _k := 1

DbSelectArea("SX1")
If (FCount() == 41)
	For _l := 1 to Len(aPer)
		Aadd(aReg,{cGrupo,aPer[_l,2],aPer[_l,3],"","",aPer[_l,4],aPer[_l,5],;
		aPer[_l,6],aPer[_l,7],aPer[_l,8],aPer[_l,9],aPer[_l,10],;
		aPer[_l,11],aPer[_l,12],"","",aPer[_l,13],aPer[_l,14],;
		aPer[_l,15],"","",aPer[_l,16],aPer[_l,17],aPer[_l,18],"","",;
		aPer[_l,19],aPer[_l,20],aPer[_l,21],"","",aPer[_l,22],;
		aPer[_l,23],aPer[_l,24],"","",aPer[_l,25],aPer[_l,26],"","",""})
	Next _l
Elseif (FCount() == 26)
	aReg := aPer
Endif

dbSelectArea("SX1")
For _l := 1 to Len(aReg)
	If !dbSeek(cGrupo+StrZero(_l,02,00))
		RecLock("SX1",.T.)
		For _m := 1 to FCount()
			FieldPut(_m,aReg[_l,_m])
		Next _m
		MsUnlock("SX1")
	Elseif Alltrim(aReg[_l,3]) <> Alltrim(SX1->X1_PERGUNT)
		RecLock("SX1",.F.)
		For _k := 1 to FCount()
			FieldPut(_k,aReg[_l,_k])
		Next _k
		MsUnlock("SX1")
	Endif
Next _l

Return (lRetu)
