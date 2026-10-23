#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 20/12/00

User Function DLP003()        // incluido pelo assistente de conversao do AP5 IDE em 20/12/00

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Declaracao de variaveis utilizadas no programa atraves da funcao    ³
//³ SetPrvt, que criara somente as variaveis definidas pelo usuario,    ³
//³ identificando as variaveis publicas do sistema utilizadas no codigo ³
//³ Incluido pelo assistente de conversao do AP5 IDE                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ


cPerg := "DLP003"
aRegistros := {}
AADD(aRegistros,{cPerg,"01","Pedido  Inicial   ?","","","mv_ch1","C",06,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"02","Pedido  Final     ?","","","mv_ch2","C",06,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"03","Periodo Inicial   ?","","","mv_ch3","D",08,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"04","Periodo Final     ?","","","mv_ch4","D",08,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"05","Nro. Vias         ?","","","mv_ch5","N",02,0,0,"G","","mv_par05","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"06","Unidade Medida    ?","","","mv_ch6","N",01,0,0,"C","","mv_par06","Primeira","","","","","Segunda","","","","","","","","","","","","","","","","","","","","","","","",""})

dbSelectArea("SX1")
dbSeek(cPerg)
If !Found()
	dbSeek(cPerg)
	While SX1->X1_GRUPO==cPerg.and.!Eof()
		Reclock("SX1",.f.)
		dbDelete()
		MsUnlock("SX1")
		dbSkip()
	EndDo
	For i:=1 to Len(aRegistros)
		RecLock("SX1",.T.)
		For j:=1 to FCount()
			FieldPut(j,aRegistros[i,j])
		Next
		MsUnlock("SX1")
	Next
Endif

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Declaracao de Variaveis                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

aOrd   := {}
CbTxt        := ""
cDesc1       := "Este programa tem como objetivo imprimir o relatorio "
cDesc2       := "de acordo com os parametros informados pelo usuario."
cDesc3       := "ESPELHO PEDIDO DE COMPRA"
cPict        := ""
lEnd         := .F.
lAbortPrint  := .F.
limite       := 80
tamanho      := "M"
nomeprog     := "COS036"
nTipo        := 18
aReturn      := { "Zebrado", 1, "Administracao", 2, 2, 1, "", 1}
nLastKey     := 0
cPerg        := "DLP003"
titulo       := "ESPELHO DE PEDIDO DE COMPRA"
nLin         := 80
Cabec1       := ""
Cabec2       := ""
cbtxt        := Space(10)
cbcont       := 00
CONTFL       := 01
m_pag        := 01
imprime      := .T.
wnrel        := "DLP003"
li           := 100

cString      := "SC7"

pergunte(cPerg,.F.)


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Variaveis utilizadas para Impressao do Cabecalho e Rodape    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
m_pag    := 1
wnrel:=SetPrint(cString,wnrel,cPerg,Titulo,cDesc1,cDesc2,cDesc3,.T.)

If  nLastKey==27
	Set Filter to
	Return
Endif

SetDefault(aReturn,cString)

//Ú==============================================================¿
//³ Definicao dos cabecalhos                                     ³
//À==============================================================Ù

W_Linha  := 100
W_Pag    := 1

#IFDEF WINDOWS
	RptStatus({|lEnd| FDLP003()},Titulo)// Substituido pelo assistente de conversao do AP5 IDE em 11/01/01 ==>        RptStatus({|lEnd| EXECUTE(FBTC006)},Titulo)
#ELSE
	lEnd := .f.
	B106()
#ENDIF
Return

// Substituido pelo assistente de conversao do AP5 IDE em 11/01/01 ==> Function FBTC006
Static Function FDLP003()
*************
SetPrc(0,0)
DbSelectArea("SC7")
DBSETORDER(5)  //Pedidos de Compra
DbSelectArea("SC1")
DBSETORDER(1)  // NUMERO DA SOLICITACAO DE Compra

//@prow()  ,00 PSAY chr(18)  //Impressao Normal
//@prow()+1,00 PSAY ''


xx      := 1
nCont   :=1
while nCont <= mv_par05
	
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Salva posicoes para movimento da regua de processamento      ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	
	#IFNDEF WINDOWS
		IF LastKey()==286
			@ 00,01 SAY "** CANCELADO PELO OPERADOR **"
			lContinua := .F.
			Exit
		Endif
	#ELSE
		IF lAbortPrint
			@ 00,01 SAY "** CANCELADO PELO OPERADOR **"
			lContinua := .F.
			Exit
		Endif
	#ENDIF
	
	DbSelectArea("SC7")
	dbgotop()
	tregs := RecCount()
	m_mult:=1
	IF tregs>0
		m_mult:=70/tregs
	ENDIF
	p_ant  :=4
	p_atu  :=4
	p_cnt  :=0
	
	DbSelectArea("SC7")
	dbgotop()
	dbseek(xfilial("SC7")+DtoS(mv_par03),.T.)
	While !SC7->(eof()) .and. xfilial("SC7") == sc7->c7_filial ;
		.and. DTOS(SC7->C7_EMISSAO) >= DTOS(MV_PAR03) .And.  DTOS(SC7->C7_EMISSAO) <= DTOS(MV_PAR04)
		If SC7->C7_NUM < MV_PAR01 .Or. SC7->C7_NUM > MV_PAR02
			DbSelectArea("SC7")
			Dbskip()
			Loop
		EndIf
		IF LastKey()==286
			Exit
		Endif
		If !Empty(SC7->C7_APROV)  .And. SC7->C7_CONAPRO<>'L'
			Msgbox(SC7->C7_NUM + ' : Pedido Nao Liberado Por Aprovador de Compras.')
			DbSelectArea("SC7")
			DbSkip()
			Loop
		EndIf
		cPedido:=sc7->c7_num           //Numero do Pedido
		nPri     :=0
		nTotitens:=19                  //Numero total de itens do pedido
		nItens   :=0                   //Numero de itens do pedido
		nTotal   :=0.00                //Valor Total
		nTotmer  :=0.00                //Valor mercadorias
		nTotIPI  :=0.00                //Valor do IPI
		cCond    :=SPACE(03)           //Condicao de Pagamento
		cTrans   :=SPACE(03)           //Transportadora
		cTipo    :=SPACE(01)           //Tipo do Frete
		cLOCENT  :=SPACE(60)           //LOCAL DE ENTREGA
		cTABENT  :=SPACE(02)           //TABELA DO LOCAL DE ENTREGA
		nValfre  :=0.00                //Valor do Frete
		nDesc1   :=0.00                //Desconto 1 do pedido
		nDesc2   :=0.00                //Desconto 2 do pedido
		nDesc3   :=0.00                //Desconto 3 do pedido
		nValdes  :=0.00                //Valor total do desconto
		nIcmret  :=0.00                //Valor do icms substituto
		nIcmret1 :=0.00                //Valor auxiliar
		nBase    :=0.00                //Base para icms retido
		nValicm  :=0.00                //Valor do Icms
		nRettot  :=0.00                //Total do Icms retido para pedido
		nNumItens:=0
		dEmissao := SC7->C7_EMISSAO
		WHILE cPEDIDO == SC7->C7_NUM .AND. !SC7->(EOF())
			p_cnt:=p_cnt + 1
			p_atu:=3 + int(p_cnt*m_mult)
			if p_atu >= p_ant
				p_ant:=p_atu
				//				restscreen(23,0,24,79,m_sav7)
				//				restscreen(23,p_atu,24,p_atu+3,m_sav20)
			endif
			
			DbSelectArea("SC1")
			dbseek(xfilial('SC1')+sc7->c7_numsc+sc7->c7_itemsc)
			
			if nPri==0
				nPri    :=1
				nItens :=0
				nTotal :=0.00                  //Valor Total
				cCond  :=sc7->c7_cond          //Condicao de Pagamento
				cTipo  :=sc7->c7_tpfrete       //Tipo do Frete
				nValfre:=sc7->c7_frete         //Valor do Frete
				nDesc1 :=sc7->c7_desc1         //Desconto 1 do pedido
				nValdes:=0.00                  //Valor total do desconto
				//       cSolic :=sc7->c7_solicit       //Solicitante
				//        cAplic :=sc7->c7_aplic         //Aplicacao
				//        cTransp:=sc7->c7_transp        // observacao
				
				//       SX5->(dBSEEK(xFILIAL("SX5")+"72"+SC7->C7_LOCENT))
				//       cLOCENT := SX5->X5_DESCRI
				
				@ 0,0 PSAY " "+chr(18)
				@prow()+1,000 PSAY "*"
				@prow()  ,001 PSAY repli("-",131)
				@prow()  ,132 PSAY "*"
				@prow()+1,000 PSAY "|"
				@prow()  ,002 PSAY "DELPI COMPONENTES LTDA.               | P E D I D O  D E  C O M P R A S           |  "
				// @prow()  ,089 PSAY chr(18)
				@prow()  ,090 PSAY sc7->c7_num
				// @prow()  ,097 PSAY chr(15)
				@prow()  ,100 PSAY " Emissao: "+DTOC(sc7->c7_emissao)
				@prow()  ,132 PSAY "|"
				@prow()+1,000 PSAY "| R: Manoel Fco. Da Costa, 2020         | "+ Repli("-",90)+"|"
				DbSelectArea("SA2")
				dbseek(xfilial("SA2")+sc7->c7_fornece+sc7->c7_loja)
				@prow()+1,000 PSAY "| CEP:  89257-000 - Jaragua Do Sul - SC |"
				@prow()  ,042 PSAY ALLTRIM(sa2->a2_nome)+"  -  "+sc7->c7_fornece
				@prow()  ,132 PSAY "|"
				@prow()+1,000 PSAY "| TEL: (047)3370-5502   FAX:3370-5502   | "
				@prow()  ,042 PSAY ALLTRIM(sa2->a2_end ) + " - " + ALLTRIM(sa2->a2_mun)
				@prow()  ,132 PSAY "|"
				@prow()+1,000 PSAY "| CGC: 01.379.126/0001-81               | "
				@prow()  ,042 PSAY "CEP: "
				@prow()  ,049 PSAY sa2->a2_cep
				@prow()  ,065 PSAY "CGC: "
				@prow()  ,070 PSAY sa2->a2_cgc PICTURE "@R 99.999.999/9999-99"
				@prow()  ,132 PSAY "|"
				@prow()+1,000 PSAY "| I.E: 253.282.144                      | "
				@prow()  ,042 PSAY "FONE: "+SA2->A2_TEL + "   FAX: " + SA2->A2_FAX
				@prow()  ,132 PSAY "|"
				@prow()+1,000 PSAY "|"
				@prow()  ,001 PSAY repLI("-",131)
				@prow()  ,132 PSAY "|"
				@prow()+1,000 PSAY "|It|Codigo    |Descricao do Material                                         |UM|      Qtd|Valor Unit|IPI|Valor Tot.|Entrega | S. C.|"
				//                   99 00.99.9999 999999999999999999999999999999999999999999999999999999999999   99 99,999.99 9,999.9999 999 999,999,99 99/99/99 090090
				//                  0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012
				//                  0         10        20        30        40        50        60        70        80        90    XX% 100       110       120       130
				@prow()+1,000 PSAY "|"
				@prow()  ,001 PSAY repLI("-",131)
				@prow()  ,132 PSAY "|"
			Endif
			sC7_UM    := ''
			sC7_QUANT := ''
			nC7_PRECO := 0
			iF MV_PAR06 == 1
				sC7_UM    := SC7->C7_UM
				sC7_QUANT := SC7->C7_QUANT
				nC7_PRECO := SC7->C7_PRECO
			Else
				sC7_UM    := SC7->C7_SEGUM
				sC7_QUANT := SC7->C7_QTSEGUM
				nC7_PRECO := SC7->C7_PRUNIT2
			EndIf
			@prow()+1,000 PSAY "|"+StrZero(val(sc7->c7_item),2)+"|"
			@prow()  ,004 PSAY Alltrim(sc7->c7_produto)
			@prow()  ,014 PSAY "|"+Left(sc7->c7_descri+space(60),60)+"  |"+sC7_UM+"|"+transf(sC7_QUANT,"@E 99,999.99")+"|"
			@prow()  ,091 PSAY transf(nC7_PRECO,"@E 999,999.99")+"|"+transf(sc7->c7_IPI,"99")+"%|"+transf(sc7->c7_total,"@E 999,999.99")+"|"
			@prow()  ,117 PSAY DTOC(sc7->c7_DATPRF)+"|"+SC7->C7_NUMSC+"|"
			iF !Empty(SC7->C7_OBS)
				@prow()+1,000 PSAY "|"
				@prow()  ,005 PSAY sc7->c7_obS
				@prow()  ,132 PSAY "|"
				nNumItens  := nNumItens + 1
				
			EndIf
			nTotmer := nTotmer + sc7->c7_total
			nTotIPI := nTotIPI + ((sc7->c7_total * SC7->C7_IPI)/100)
			nNumItens  := nNumItens + 1
			dEmissao := SC7->C7_EMISSAO
			DbSelectArea("SC7")
			DbSkip()
		End
		@prow()+1,000   PSAY "|"
		@prow()  ,001   PSAY repli("-",131)
		@prow()  ,132   PSAY "|"
		
		cCol    := 14
		For i := nNumItens to 20
			@prow() + 1,000     PSAY "|"
			@prow()    ,132     PSAY "|"
			nNumItens  := nNumItens + 1
		Next
		
		
		nTotal := nTotal+ROUND((ntotmer - ((ntotmer * nDesc1) / 100) + nTotIPI),2)
		
		@prow()+1  ,000 PSAY "|"
		@prow()    ,001 PSAY REPLI("-",131)
		@prow()    ,132 PSAY "|"
		
		@prow()+1  ,000 PSAY "|    DESCONTO --> "
		@prow()    ,020 PSAY nDESC1   PICTURE "@E 99.99%"
		@prow()    ,028 PSAY "R$"
		@prow()    ,030 PSAY ROUND((nTotal * nDESC1)/100,2) PICTURE "@E 9,999.99"
		@prow()    ,055 PSAY ">>>Valor das Mercadorias : "
		@prow()    ,095 PSAY ROUND(nTotmer,2) PICTURE "@E 9999,999.99"
		@prow()    ,117 PSAY "IPI: "
		@prow()    ,124 PSAY ROUND(nTotIPI,2) PICTURE "@E 9999.99"
		@prow()    ,132 PSAY "|"
		
		@prow()+1  ,000 PSAY "|"
		@prow()    ,001 PSAY REPLI("-",131)
		@prow()    ,132 PSAY "|"
		
		@prow()+1,000 PSAY "|                                                                                                                                   |"
		
		@prow()+1  ,000 PSAY "|"
		@prow()    ,001 PSAY REPLI("-",131)
		@prow()    ,132 PSAY "|"
		
		cDesCp:=space(15)
		DbSelectArea("SE4")
		if dbseek(xfilial("SE4")+cCond)
			cDesCp:=se4->e4_descri
		endif
		DbSelectArea("SA4")
		//    sa4->(dbseek(xfilial("SA4")+cTransp))
		
		@prow()+1  ,000    PSAY "|"
		@prow()    ,001    PSAY "Condicao de Pagto : " + subs(cDesCp,1,25) + " |   Emissao  : "
		@prow()    ,pCol() PSAY dEmissao
		@prow()    ,132 PSAY "|"
		
		@prow()+1  ,000 PSAY "|"
		@prow()    ,001 PSAY REPLI("-",131)
		@prow()    ,132 PSAY "|"
		
		@prow()+1  ,000 PSAY "|"
		@prow()    ,132 PSAY "|"
		@prow()+1  ,000 PSAY "|"
		@prow()    ,132 PSAY "|"
		
		@prow()+1  ,000 PSAY "|"
		@prow()    ,132 PSAY "|"
		@prow()+1  ,000 PSAY "|"
		@prow()    ,035 PSAY "-------------------------------              DEPTO. DE COMPRAS - CONTATOS"
		@prow()    ,132 PSAY "|"
		@prow()+1  ,000 PSAY "|"
		@prow()    ,035 PSAY "    Liberacao de Compras                     Tel. (047) 3370-5502  - Diomar    "
		@prow()    ,132 PSAY "|"
		@prow()+1  ,000 PSAY "*"
		@prow()    ,001 PSAY REPLI("-",131)
		@prow()    ,132 PSAY "*"
		@prow()+1,000 PSAY "|                                                                                                                                   |"
		@prow()+1,000 PSAY "| ATENCAO: N A   N O T A    F I S C A L   D E V E R A    C O N S T A R   O   N U M E R O    D O    P E D I D O    D E   C O M P R A |"
		@prow()+1,000 PSAY "|                                                                                                                                   |"
		@prow()+1  ,000 PSAY "*"
		@prow()    ,001 PSAY REPLI("-",131)
		@prow()    ,132 PSAY "*"
	END
	nCont := nCont + 1
End
If aReturn[5] == 1
	Set Printer TO
	dbCommitall()
	ourspool(wnrel)
Endif
MS_FLUSH()
Return
