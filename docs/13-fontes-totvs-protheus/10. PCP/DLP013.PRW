#INCLUDE "MATR820.CH"
#INCLUDE "FIVEWIN.CH"
#Include 'TOPConn.ch'
#Include 'Protheus.ch'
Static cAliasTop

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ MATR820  ³ Autor ³ Felipe Nunes Toledo   ³ Data ³ 26/09/06 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Ordens de Producao                                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ Generico                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±gda
*/
User Function DLP013()
	Local oReport

	// ROBERTO FAUSTO TSC 243
	Private cCabDelp1 := "DATA | QTDE PROD | FORNEC | LOTE/NF | CAD | COD MT PRIMA | COD DEFEITO | QUANTID"
	Private cCabDelp2 := "     |           |        |         |     |              |      |      |        "

	Private cDetDelp1 := "DATA      | QTDE PROD | FORNEC   | LOTE/NF  | CAD    | COD MT PRIMA | COD DEFEITO | QUANTID"
	Private cDetDelp2 := "          |           |          |          |        |              |      |      |        "

	//-- Verifica se o SH8 esta locado para atualizacao por outro processo
	//If !IsLockSH8()
	//
	//	If FindFunction("TRepInUse") .And. TRepInUse()
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Interface de impressao                                                  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oReport:= ReportDef()
	If !oReport:PrintDialog()
		dbSelectArea("SH8")
		dbClearFilter()
		dbCloseArea()
		Return Nil
	EndIf
	//	Else
	//		U_DLP013R3()
	//	EndIf
	//
	//EndIf

Return NIL

/*/
	ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
	±±³Programa  ³ReportDef ³ Autor ³Felipe Nunes Toledo    ³ Data ³27/09/06  ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
	±±³Descri‡…o ³A funcao estatica ReportDef devera ser criada para todos os ³±±
	±±³          ³relatorios que poderao ser agendados pelo usuario.          ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³Parametros³Nenhum                                                      ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³Uso       ³MATR820                                                     ³±±
	±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function ReportDef()
	Local oReport
	Local oSection1, oSection2, Section3 //, oSection6
	Local aOrdem	:= {STR0002,STR0003,STR0004,STR0005}	//"Por Numero"###"Por Produto"###"Por Centro de Custo"###"Por Prazo de Entrega"
	Local cTitle	:= STR0039 //"Ordens de Producao"
	Local lVer116   := (VAL(GetVersao(.F.)) == 11 .And. GetRpoRelease() >= "R6" .Or. VAL(GetVersao(.F.))  > 11)

	#IFDEF TOP
		cAliasTop := GetNextAlias()
	#ELSE
		cAliasTop := "SC2"
	#ENDIF

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Criacao do componente de impressao                                      ³
	//³                                                                        ³
	//³TReport():New                                                           ³
	//³ExpC1 : Nome do relatorio                                               ³
	//³ExpC2 : Titulo                                                          ³
	//³ExpC3 : Pergunte                                                        ³
	//³ExpB4 : Bloco de codigo que sera executado na confirmacao da impressao  ³
	//³ExpC5 : Descricao                                                       ³
	//³                                                                        ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oReport:= TReport():New("DLP013",cTitle,"DLP013", {|oReport| ReportPrint(oReport, cAliasTop)},OemToAnsi(STR0001)) //"Este programa ira imprimir a Rela‡„o das Ordens de Produ‡„o"
	oReport:SetPortrait()     // Define a orientacao de pagina do relatorio como retrato.
	oReport:HideParamPage()   // Desabilita a impressao da pagina de parametros.
	oReport:nFontBody	:= 9  // Define o tamanho da fonte.
	oReport:nLineHeight	:= 50 // Define a altura da linha.
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica as perguntas selecionadas - MTR820                  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Variaveis utilizadas para parametros                         ³
	//³ mv_par01            // Da OP                                 ³
	//³ mv_par02            // Ate a OP                              ³
	//³ mv_par03            // Da data                               ³
	//³ mv_par04            // Ate a data                            ³
	//³ mv_par05            // Imprime roteiro de operacoes          ³
	//³ mv_par06            // Imprime codigo de barras              ³
	//³ mv_par07            // Imprime Nome Cientifico               ³
	//³ mv_par08            // Imprime Op Encerrada                  ³
	//³ mv_par09            // Impr. por Ordem de                    ³
	//³ mv_par10            // Impr. OP's Firmes, Previstas ou Ambas ³
	//³ mv_par11            // Impr. Item Negativo na Estrutura      ³
	//³ mv_par12            // Imprime Lote/Sub-Lote                 ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	AjustaSX1()
	Pergunte(oReport:GetParam(),.F.)
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Criacao da secao utilizada pelo relatorio                               ³
	//³                                                                        ³
	//³TRSection():New                                                         ³
	//³ExpO1 : Objeto TReport que a secao pertence                             ³
	//³ExpC2 : Descricao da secao                                              ³
	//³ExpA3 : Array com as tabelas utilizadas pela secao. A primeira tabela   ³
	//³        sera considerada como principal para a secao.                   ³
	//³ExpA4 : Array com as Ordens do relatorio                                ³
	//³ExpL5 : Carrega campos do SX3 como celulas                              ³
	//³        Default : False                                                 ³
	//³ExpL6 : Carrega ordens do Sindex                                        ³
	//³        Default : False                                                 ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Sessao 1 (oSection1)                                         ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oSection1 := TRSection():New(oReport,STR0050,{"SC2","SB1","SC5","SA1","SBZ"},aOrdem) // "Ordens de Produção"
	oSection1:SetLineStyle() //Define a impressao da secao em linha
	oSection1:SetReadOnly()

	TRCell():New(oSection1,'C2_NUM'		,'SC2',STR0073   ,PesqPict('SC2','C2_NUM')	 ,TamSX3('C2_NUM')[1]	  ,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_PRODUTO'	,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'B1_REFEREN' ,'SB1',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'BZ_YCERT' ,'SBZ',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'B1_DESC' 	,'SB1',/*Titulo*/,/*Picture*/					,TamSX3('B1_DESC')[1]+15 /*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'Emissao'   	,'SC2',STR0040   ,PesqPict("SC2","C2_EMISSAO")	,10						,/*lPixel*/,{|| DTOC(dDataBase) })
	TRCell():New(oSection1,'C5_CLIENTE'	,'SC5',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C5_LOJACLI'	,'SC5',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'A1_NOME'  	,'SA1',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'QtdeProd'	,'SC2',STR0041   ,PesqPict("SC2","C2_QUANT")	,TamSX3("C2_QUANT")[1]	,/*lPixel*/,{|| aSC2Sld(cAliasTop) })
	TRCell():New(oSection1,'C2_QUANT'	,'SC2',STR0042   ,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'OpQuant'  	,'SC2',STR0043   ,PesqPict("SC2","C2_QUANT")	,TamSX3("C2_QUANT")[1]	,/*lPixel*/,{|| (cAliasTop)->C2_QUANT - (cAliasTop)->C2_QUJE })
	TRCell():New(oSection1,'B1_UM'	 	,'SB1',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_CC'		,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_STATUS'	,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_DATPRI'	,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_DATPRF'	,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_DATAJI'	,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_DATAJF'	,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'RealIni'	,'SC2',STR0044   ,'@!'							,8						,/*lPixel*/,{|| "__/__/__" })
	TRCell():New(oSection1,'RealFim'	,'SC2',STR0045   ,'@!'							,8						,/*lPixel*/,{|| "__/__/__" })
	TRCell():New(oSection1,'C2_OBS'		,'SC2',/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection1,'C2_YOBSQUA'		,'SC2',"Observacao Qualidade:"/*Titulo*/,/*Picture*/					,/*Tamanho*/			,/*lPixel*/,/*{|| code-block de impressao }*/)

	oSection1:Cell('B1_DESC'  ):SetCellBreak()
	oSection1:Cell('Emissao'  ):SetCellBreak()
	oSection1:Cell('A1_NOME'  ):SetCellBreak()
	oSection1:Cell('C2_QUANT' ):SetCellBreak()
	oSection1:Cell('OpQuant'  ):SetCellBreak()
	oSection1:Cell('B1_UM'    ):SetCellBreak()
	oSection1:Cell('C2_CC'    ):SetCellBreak()
	oSection1:Cell('C2_STATUS'):SetCellBreak()
	oSection1:Cell('C2_DATPRF'):SetCellBreak()
	oSection1:Cell('C2_DATAJF'):SetCellBreak()
	oSection1:Cell('RealFim'  ):SetCellBreak()
	oSection1:Cell('C2_YOBSQUA'  ):SetCellBreak()

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Sessao 2 (oSection2)                                         ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oSection2 := TRSection():New(oSection1,STR0051,{"SD4","SB1","NNR"},/*Ordem*/) //"Empenhos"
	oSection2:SetHeaderBreak()
	oSection2:SetReadOnly()

	TRCell():New(oSection2,'D4_COD'	 	,'SD4',STR0058   ,PesqPict('SD4','D4_COD')    ,TamSX3('D4_COD')[1]+2    ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,.F./*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	TRCell():New(oSection2,'B1_DESC' 	,'SB1',STR0059   ,PesqPict('SB1','B1_DESC')   ,30 ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	oSection2:Cell("B1_DESC"):SetLineBreak()
	TRCell():New(oSection2,'D4_QUANT' 	,'SD4',STR0043   ,PesqPict('SD4','D4_QUANT')  ,TamSX3('D4_QUANT')[1]  ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	TRCell():New(oSection2,'B1_UM'   	,'SB1',STR0061   ,PesqPict('SB1','B1_UM')     ,TamSX3('B1_UM')[1]     ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	TRCell():New(oSection2,'D4_LOCAL'	,'SD4',STR0072   ,PesqPict('SD4','D4_LOCAL')  ,TamSX3('D4_LOCAL')[1]  ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	If lVer116
		TRCell():New(oSection2,'NNR_DESCRI'	,'NNR',/*Titulo*/,PesqPict('NNR','NNR_DESCRI'),TamSX3('NNR_DESCRI')[1],/*lPixel*/,{||Posicione("NNR",1,xFilial("NNR")+SD4->D4_LOCAL,"NNR_DESCRI")},/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	Else
		TRCell():New(oSection2,'B2_LOCALIZ'	,'SB2',/*Titulo*/,PesqPict('SB2','B2_LOCALIZ'),TamSX3('B2_LOCALIZ')[1],/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	EndIf
	TRCell():New(oSection2,'BZ_MPLOCAL'  	,'SBZ',"Localiz"   ,PesqPict('SBZ','BZ_MPLOCAL')    ,TamSX3('BZ_MPLOCAL')[1]    ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	TRCell():New(oSection2,'D4_TRT'  	,'SD4',STR0064   ,PesqPict('SD4','D4_TRT')    ,TamSX3('D4_TRT')[1]    ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	TRCell():New(oSection2,'D4_LOTECTL'	,'SD4',/*Titulo*/,PesqPict('SD4','D4_LOTECTL'),TamSX3('D4_LOTECTL')[1],/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	TRCell():New(oSection2,'D4_NUMLOTE'	,'SD4',/*Titulo*/,PesqPict('SD4','D4_NUMLOTE'),TamSX3('D4_NUMLOTE')[1],/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	TRCell():New(oSection2,'D4_OP'  	,'SD4',/*Titulo*/,PesqPict('SD4','D4_OP')     ,TamSX3('D4_OP')[1]     ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Sessao 3 (oSection3)                                         ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oSection3 := TRSection():New(oSection1,STR0052,{"SG2","SH8","SH1","SH4"},/*Ordem*/) //"Operações"
	oSection3:SetHeaderBreak()
	oSection3:SetReadOnly()

	TRCell():New(oSection3,'G2_RECURSO','SG2',/*Titulo*/,/*Picture*/,10 		   ,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection3,'H1_DESCRI'	,'SH1',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection3,'G2_FERRAM'	,'SG2',"Ferramenta",/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection3,'H4_DESCRI'	,'SH4',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/)
	TRCell():New(oSection3,'G2_OPERAC'	,'SG2',"Operação",/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/)
	TRCell():New(oSection3,'G2_DESCRI'	,'SG2',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,.T.)
	TRCell():New(oSection3,'G2_CODDESC'	,'SG2',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,.T.)

	oSection3:Cell('H1_DESCRI'):HideHeader()
	oSection3:Cell('H4_DESCRI'):HideHeader()
	oSection3:Cell('G2_DESCRI'):HideHeader()
	oSection3:Cell('G2_CODDESC'):HideHeader()

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Sessao 4 (oSection4)                                         ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oSection4 := TRSection():New(oSection3,STR0053,{"SG2","SH8","SH1","SH4"},/*Ordem*/) //"Tempo Rot. Oper."
	oSection4:SetLineStyle() //Define a impressao da secao em linha
	oSection4:SetReadOnly()

	TRCell():New(oSection4,'H8_DTINI'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection4,'H8_HRINI'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection4,'H8_DTFIM'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection4,'H8_HRFIM'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection4,'IniAloc'	,'SH8',STR0046   ,'@!'  , 24        ,/*lPixel*/,{|| " ____/ ____/____ ___:___" })
	TRCell():New(oSection4,'FimAloc'	,'SH8',STR0047   ,'@!'  , 24        ,/*lPixel*/,{|| " ____/ ____/____ ___:___" })
	TRCell():New(oSection4,'H8_QUANT'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	TRCell():New(oSection4,'QtdeProd'	,'SH8',STR0048   ,/*Picture*/, 12       ,/*lPixel*/,{|| Space(12) })
	TRCell():New(oSection4,'QtdPerda'	,'SH8',STR0049   ,/*Picture*/,/*Tamanho*/,/*lPixel*/,{|| Space(12) })

	oSection4:Cell('H8_HRFIM'):SetCellBreak()
	oSection4:Cell('FimAloc' ):SetCellBreak()


	////ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	////³ Sessao 6 (oSection6)       RECURSO                                  ³
	////ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	//oSection6 := TRSection():New(oSection3,"Recurso",{"SG2","SH8","SH1","SH4","SG1"},/*Ordem*/) //"Tempo Rot. Oper."
	//oSection6:SetLineStyle() //Define a impressao da secao em linha
	//oSection6:SetReadOnly()
	//
	//TRCell():New(oSection6,'G1_COMP'	,'SG1',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection6,'B1_DESC'	,'SB1',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection6,'G1_OBSERV'	,'SG1',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection4,'H8_DTINI'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection4,'H8_HRINI'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection4,'H8_DTFIM'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection4,'H8_HRFIM'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection4,'IniAloc'	,'SH8',STR0046   ,'@!'  , 24        ,/*lPixel*/,{|| " ____/ ____/____ ___:___" })
	//TRCell():New(oSection4,'FimAloc'	,'SH8',STR0047   ,'@!'  , 24        ,/*lPixel*/,{|| " ____/ ____/____ ___:___" })
	//TRCell():New(oSection4,'H8_QUANT'	,'SH8',/*Titulo*/,/*Picture*/,/*Tamanho*/,/*lPixel*/,/*{|| code-block de impressao }*/)
	//TRCell():New(oSection4,'QtdeProd'	,'SH8',STR0048   ,/*Picture*/, 12       ,/*lPixel*/,{|| Space(12) })
	//TRCell():New(oSection4,'QtdPerda'	,'SH8',STR0049   ,/*Picture*/,/*Tamanho*/,/*lPixel*/,{|| Space(12) })
	//
	//oSection6:Cell('G1_COMP'):SetCellBreak()
	//oSection4:Cell('FimAloc' ):SetCellBreak()
	//FIM RECURSO
	oSection1:SetNoFilter({"SA1","SC5"})
	oSection2:SetNoFilter({"SD4","SB1","SB2","SC2"})
	oSection3:SetNoFilter({"SG2","SH8","SH1","SH4"})
	oSection4:SetNoFilter({"SG2","SH8","SH1","SH4"})
	//oSection6:SetNoFilter({"SG2","SH8","SH1","SH4","SG1"})

Return(oReport)

/*/
		ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
		±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
		±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
		±±³Programa  ³ReportPrint ³ Autor ³Felipe Nunes Toledo  ³ Data ³27/09/06  ³±±
		±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
		±±³Descri‡…o ³A funcao estatica ReportPrint devera ser criada para todos  ³±±
		±±³          ³os relatorios que poderao ser agendados pelo usuario.       ³±±
		±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
		±±³Retorno   ³Nenhum                                                      ³±±
		±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
		±±³Parametros³ExpO1: Objeto Report do Relatorio                           ³±±
		±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
		±±³Uso       ³MATR820                                                     ³±±
		±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
		±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
		ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function ReportPrint(oReport, cAliasTop)
	Local oSection1	:= oReport:Section(1)
	Local oSection2	:= oReport:Section(1):Section(1)
	Local oSection3	:= oReport:Section(1):Section(2)
	Local oSection4	:= oReport:Section(1):Section(2):Section(1)
	Local oSection5
	//Local oSection6 := oReport:Section(1):Section(2):Section(2)
	//Local oSection7 := oReport:Section(1):Section(2):Section(3)
	Local nOrdem    := oSection1:GetOrder()
	Local oBreak
	Local cIndex	:= ""
	Local cCondicao	:= ""
	Local cCode    	:= ""
	Local nCntFor   := 0
	Local nLinBar	:= 0
	Local cWhere01, cWhere02, cWhere03
	Local cOrderBy
	Local lVer116   := (VAL(GetVersao(.F.)) == 11 .And. GetRpoRelease() >= "R6" .Or. VAL(GetVersao(.F.))  > 11)
	Local lPlanilha := oReport:nDevice == 4
	Private aArray	 := {}
	Private lItemNeg := GetMv("MV_NEGESTR") .And. mv_par11 == 1

	If !lPlanilha .Or. len(oReport:aXlsTable) == 0
		oSection1:Cell("C2_NUM"):Disable()
	Endif

	// Definindo quebra para secao 2 e ocultando celula utilizada somente para quebra
	oBreak := TRBreak():New(oSection2,oSection2:Cell("D4_OP"),Nil,.F.)
	oSection2:Cell("D4_OP"):Disable()

	If lPlanilha
		oSection5 := TRSection():New(oReport,'',{"SC2"},/*Ordem*/)
		TRCell():New(oSection5,'C2_NUM'  	,'SC2',/*Titulo*/,PesqPict('SC2','C2_NUM')     ,TamSX3('C2_NUM')[1]     ,/*lPixel*/,/*{|| code-block de impressao }*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,/*nColSpace*/,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/)
	Endif

	If mv_par12 == 2
		oSection2:Cell("D4_LOTECTL"):Disable()
		oSection2:Cell("D4_NUMLOTE"):Disable()
	ElseIf !oReport:oPage:IsLandScape()
		oSection2:Cell("B1_DESC"):SetSize(19)
		If lVer116
			oSection2:Cell("NNR_DESCRI"):SetSize(10)
		Else
			oSection2:Cell("B2_LOCALIZ"):SetSize(10)
		EndIf
		oSection2:Cell("D4_NUMLOTE"):SetTitle(STR0057)
	EndIf

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Filtragem do relatorio                                                  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	#IFDEF TOP

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Transforma parametros Range em expressao SQL                            ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		MakeSqlExpr(oReport:GetParam())

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Condicao Where para filtrar OP's                             ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		cWhere01 := "%'"+mv_par01+"'%"
		cWhere02 := "%'"+mv_par02+"'%"

		cWhere03 := "%"
		If mv_par08 == 2
			cWhere03 += "AND SC2.C2_DATRF = ' '"
		Endif
		cWhere03 += "%"

		cOrderBy := "%"
		If nOrdem == 4
			cOrderBy += "SC2.C2_FILIAL, SC2.C2_DATPRF"
		Else
			cOrderBy += SqlOrder(SC2->(IndexKey(nOrdem)))
		EndIf
		cOrderBy += "%"

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Query do relatorio da secao 1                                           ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		oSection1:BeginQuery()
		BeginSql Alias cAliasTop
			SELECT
				SC2.C2_FILIAL,
				SC2.C2_NUM,
				SC2.C2_ITEM,
				SC2.C2_SEQUEN,
				SC2.C2_ITEMGRD,
				SC2.C2_DATPRF,
				SC2.C2_DATRF,
				SC2.C2_PRODUTO,
				SC2.C2_DESTINA,
				SC2.C2_PEDIDO,
				SC2.C2_ROTEIRO,
				SC2.C2_QUJE,
				SC2.C2_PERDA,
				SC2.C2_QUANT,
				SC2.C2_DATPRI,
				SC2.C2_CC,
				SC2.C2_DATAJI,
				SC2.C2_DATAJF,
				SC2.C2_STATUS,
				SC2.C2_OBS,
				SC2.C2_TPOP,
				SC2.R_E_C_N_O_ SC2RECNO
			FROM
				%table:SC2% SC2
			WHERE
				SC2.C2_FILIAL = %xFilial:SC2%
				AND SC2.C2_NUM || SC2.C2_ITEM || SC2.C2_SEQUEN || SC2.C2_ITEMGRD >= %Exp:cWhere01%
				AND SC2.C2_NUM || SC2.C2_ITEM || SC2.C2_SEQUEN || SC2.C2_ITEMGRD <= %Exp:cWhere02%
				AND SC2.C2_DATPRF BETWEEN %Exp:mv_par03% AND %Exp:mv_par04%
				AND SC2.%NotDel% %Exp:cWhere03%
			ORDER BY
				%Exp:cOrderby%
		EndSql
		oSection1:EndQuery()

	#ELSE
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Transforma parametros Range em expressao ADVPL                          ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		MakeAdvplExpr(oReport:GetParam())

		dbSelectArea(cAliasTop)

		If nOrdem == 4
			cIndex := "C2_FILIAL+DTOS(C2_DATPRF)"
		Else
			dbSetOrder(nOrdem)
		EndIf

		cCondicao := "C2_FILIAL=='"+xFilial("SC2")+"'"
		cCondicao += ".And.C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD>='"+mv_par01+"'"
		cCondicao += ".And.C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD<='"+mv_par02+"'"
		cCondicao += ".And.DTOS(C2_DATPRF)>='"+DTOS(mv_par03)+"'"
		cCondicao += ".And.DTOS(C2_DATPRF)<='"+DTOS(mv_par04)+"'"
		If mv_par08 == 2
			cCondicao += ".And.Empty(C2_DATRF)"
		EndIf

		oReport:Section(1):SetFilter(cCondicao,If(nOrdem==4,cIndex,IndexKey()))
	#ENDIF
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Posicionamento das tabelas³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	TRPosition():New(oSection1,"SB1",1,{|| xFilial("SB1")+(cAliasTop)->C2_PRODUTO })
	TRPosition():New(oSection1,"SC5",1,{|| xFilial("SC5")+(cAliasTop)->C2_PEDIDO })
	TRPosition():New(oSection1,"SA1",1,{|| xFilial("SA1")+SC5->C5_CLIENTE+SC5->C5_LOJACLI })

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Inicio da impressao do fluxo do relatorio                               ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oReport:SetMeter(SC2->(LastRec()))
	oSection1:Init()
	oSection2:Init()
	oSection3:Init()
	oSection4:Init()
	If lPlanilha
		oSection5:Init()
	Endif

	dbSelectArea(cAliasTop)
	While !oReport:Cancel() .And. !(cAliasTop)->(Eof())
		//-- Valida se a OP deve ser Impressa ou nao
		If !MtrAValOP(mv_par10,"SC2",cAliasTop)
			dbSkip()
			Loop
		EndIf

		//Definindo a descricao do produto
		MR820Desc(oReport, cAliasTop)

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Desabilitando celulas que nao deverao serem impressas   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If (cAliasTop)->C2_DESTINA <> "P"
			oSection1:Cell('C5_CLIENTE'):Disable()
			oSection1:Cell('C5_LOJACLI'):Disable()
			oSection1:Cell('A1_NOME'   ):Disable()
		EndIf
		If Empty((cAliasTop)->C2_STATUS)
			oSection1:Cell("C2_STATUS"):SetValue("Normal")
		EndIf
		If (cAliasTop)->C2_QUJE + (cAliasTop)->C2_PERDA > 0
			oSection1:Cell('OpQuant'):Disable()
		Else
			oSection1:Cell('QtdeProd'):Disable()
			oSection1:Cell('C2_QUANT'):Disable()
		Endif
		If (Empty((cAliasTop)->C2_OBS))
			oSection1:Cell('C2_OBS'):Disable()
		EndIf

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³Definindo o titulo do Relatorio³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		oReport:SetTitle(STR0010+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)) //"        O R D E M   D E   P R O D U C A O       NRO :"

		If mv_par06 == 1
			nLinBar := 0.95

			oReport:PrintText("")
			For nCntFor := 1 to 5
				oReport:SkipLine()
			Next nCntFor

			cCode := (cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)

			If oReport:lHeaderVisible .And. oReport:nEnvironment == 2
				nLinBar += 1
			EndIf

			If oReport:GetOrientation()== 1
				nLinBar += 0.2
			EndIf
			MSBAR3("CODE128",nLinBar,0.5,Trim(cCode),@oReport:oPrint,Nil,Nil,Nil,Nil ,1.5 ,Nil,Nil,Nil,.F.)
		EndIf

		If lPlanilha
			oReport:SkipLine()
			oSection5:Cell("C2_NUM"):SetValue((cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD))
			oSection5:Cell('C2_NUM'):Enable()
			If len(oReport:aXlsTable) > 0
				oSection1:Cell("C2_NUM"):SetValue((cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD))
				oSection1:Cell('C2_NUM'):Enable()
			Endif
			//Impressao da Section 5
			oSection5:PrintLine()
			oReport:IncMeter()
		Endif

		//Impressao da Section 1
		oSection1:PrintLine()
		oReport:IncMeter()

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ
		//³Habilitando celula
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ
		If (cAliasTop)->C2_DESTINA <> "P"
			oSection1:Cell('C5_CLIENTE'):Enable()
			oSection1:Cell('C5_LOJACLI'):Enable()
			oSection1:Cell('A1_NOME'   ):Enable()
		EndIf
		If (cAliasTop)->C2_QUJE + (cAliasTop)->C2_PERDA > 0
			oSection1:Cell('OpQuant'):Enable()
		Else
			oSection1:Cell('QtdeProd'):Enable()
			oSection1:Cell('C2_QUANT'):Enable()
		Endif
		If (Empty((cAliasTop)->C2_OBS))
			oSection1:Cell('C2_OBS'):Enable()
		EndIf

		//--- Inicio fluxo impressao secao 2
		SB1->(dbSeek(xFilial("SB1")+(cAliasTop)->C2_PRODUTO))

		aArray := {}
		MontStruc((cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD))

		If mv_par09 == 1
			aSort( aArray,1,, { |x, y| (x[1]+x[8]) < (y[1]+y[8]) } )
		Else
			aSort( aArray,1,, { |x, y| (x[8]+x[1]) < (y[8]+y[1]) } )
		ENDIF

		For nCntFor := 1 TO Len(aArray)
			dbSelectArea("SBZ")
			SBZ->(dbSetOrder(1))
			SBZ->(MsSeek(xFilial("SBZ")+aArray[nCntFor][1]))


			SB1->(dbSetOrder(1))
			SB1->(MsSeek(xFilial("SB1")+aArray[nCntFor][1]))

			SD4->(dbSetOrder(2))
			SD4->(MsSeek(xFilial("SD4")+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)+aArray[nCntFor][1]+aArray[nCntFor][6]))

			oSection2:Cell("D4_COD"    ):SetValue(aArray[nCntFor][1])
			oSection2:Cell("B1_DESC"   ):SetValue(aArray[nCntFor][2])
			oSection2:Cell("D4_QUANT"  ):SetValue(aArray[nCntFor][5])
			oSection2:Cell("B1_UM"     ):SetValue(aArray[nCntFor][4])
			oSection2:Cell("D4_LOCAL"  ):SetValue(aArray[nCntFor][6])
			If lVer116
				oSection2:Cell("NNR_DESCRI"):SetValue(aArray[nCntFor][7])
			Else
				oSection2:Cell("B2_LOCALIZ"):SetValue(aArray[nCntFor][7])
			EndIf
			oSection2:Cell("BZ_MPLOCAL"    ):SetValue(SBZ->BZ_MPLOCAL)
			oSection2:Cell("D4_TRT"    ):SetValue(aArray[nCntFor][8])
			oSection2:Cell("D4_OP"     ):SetValue((cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD))
			If mv_par12 == 1
				oSection2:Cell("D4_LOTECTL"):SetValue(aArray[nCntFor][10])
				oSection2:Cell("D4_NUMLOTE"):SetValue(aArray[nCntFor][11])
			EndIf

			//Impressao da Section 2
			oSection2:PrintLine()
		Next nCntFor

		If mv_par05 == 1
			Mr820Ope(oReport, cAliasTop) //Impressao da Section 3 e Section 4
		EndIf

		oReport:EndPage() //-- Salta Pagina
		dbSelectArea(cAliasTop)
		dbSkip()

	EndDo

	If lPlanilha
		oSection5:Finish()
	Endif
	oSection4:Finish()
	oSection3:Finish()
	oSection2:Finish()
	oSection1:Finish()
	(cAliasTop)->(DbCloseArea())
	dbSelectArea("SH8")
	dbClearFilter()
	dbCloseArea()

Return Nil

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³MR820Desc   ³ Autor ³Felipe Nunes Toledo  ³ Data ³28/09/06  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Atribui a descricao do produto conforme opcao selecionada   ³±±
±±³          ³no parametro mv_par07 (Descricao do Produto ?).             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ExpO1: Objeto Report do Relatorio                           ³±±
±±³          ³ExpC1: Alias do arquivo Ordem de Producao                   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³MATR820                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
Static Function MR820Desc(oReport, cAliasTop)
	Local oSection1 := oReport:Section(1)
	Local lSB1Desc 	:= .T.
	Local cProdPA	:= ''

	// Acrescentar o Codigo do produto Acabado da OP Sequencia 001 quando for necessario
	If	(cAliasTop)->C2_SEQUEN > '001'
		SC2->(DbSetOrder(1))
		SC2->(MsSeek(xFilial('SC2')+(cAliasTop)->(C2_NUM+C2_ITEM+'001')))
		If	SC2->(Found())
			cProdPA := AllTrim(SC2->C2_PRODUTO)
			oSection1:Cell("B1_REFEREN"):Disable()
			oSection1:Cell("BZ_YCERT"):Disable()
		EndIf
	Else
		SC2->(DbSetOrder(1))
		SC2->(MsSeek(xFilial('SC2')+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN)))
		If	SC2->(Found())
			SB1->(DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))
			SBZ->(DbSeek(xFilial('SBZ')+SC2->C2_PRODUTO))
		EndIf
		oSection1:Cell("B1_REFEREN"):SetValue(SB1->B1_REFEREN)
		oSection1:Cell("B1_REFEREN"):Enable()
		oSection1:Cell("BZ_YCERT"):SetValue(SBZ->BZ_YCERT)
		oSection1:Cell("BZ_YCERT"):Enable()
	EndIf

	If mv_par07 == 1
		SB5->(dbSetOrder(1))
		If SB5->(dbSeek(xFilial("SB5")+(cAliasTop)->C2_PRODUTO) .And. !Empty(B5_CEME))
			oSection1:Cell("B1_DESC"):GetFieldInfo("B5_CEME")
			cDescSB1 := AllTrim(SB5->B5_CEME) + IIf(!Empty(cProdPA),' / ','') + IIf(!Empty(cProdPA),cProdPA,'')
			oSection1:Cell("B1_DESC"):SetValue(cDescSB1)
			lSB1Desc := .F.
		EndIf
	ElseIf mv_par07 == 3
		If (cAliasTop)->C2_DESTINA == "P"
			SC6->(dbSetOrder(1))
			If SC6->(dbSeek(xFilial("SC6")+(cAliasTop)->C2_PEDIDO+(cAliasTop)->C2_ITEM))
				If !Empty(SC6->C6_DESCRI) .and. SC6->C6_PRODUTO == (cAliasTop)->C2_PRODUTO
					oSection1:Cell("B1_DESC"):GetFieldInfo("C6_DESCRI")
					cDescSB1 := AllTrim(SC6->C6_DESCRI) + IIf(!Empty(cProdPA),' / ','') + IIf(!Empty(cProdPA),cProdPA,'')
					oSection1:Cell("B1_DESC"):SetValue(cDescSB1)
					lSB1Desc := .F.
				EndIf
			EndIf
		EndIf
	EndIf

	If (mv_par07 == 2) .And. lSB1Desc
		SB1->(dbSetOrder(1))
		If SB1->( dbSeek(xFilial("SB1")+(cAliasTop)->C2_PRODUTO) )
			oSection1:Cell("B1_DESC"):GetFieldInfo("B1_DESC")
			cDescSB1 := AllTrim(SB1->B1_DESC) + IIf(!Empty(cProdPA),' / ','') + IIf(!Empty(cProdPA),cProdPA,'')
			oSection1:Cell("B1_DESC"):SetValue(cDescSB1)
		EndIf
	EndIf

Return Nil

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³ Fun‡…o   ³ Mr820Ope ³ Autor ³ Felipe Nunes Toledo   ³ Data ³ 18/07/92 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Descri‡…o³ Imprime Roteiro de Operacoes                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Sintaxe  ³ Mr820Ope()                                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
*/
Static Function Mr820Ope(oReport, cAliasTop)
	Local oSection3 := oReport:Section(1):Section(2)
	Local oSection4	:= oReport:Section(1):Section(2):Section(1)
	//	Local oSection6 := oReport:Section(1):Section(2):Section(2)
	//Local oSection7 := oReport:Section(1):Section(2):Section(3)
	Local oBreak
	Local cRoteiro	:= ""
	Local cSeekWhile:= ""
	Local lSH8 		:= .F.
	Local aArea   	:= GetArea()

	oBreak:= TRBreak():New(oSection3,oSection3:Cell("G2_RECURSO"),Nil,.F.)

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica se imprime ROTEIRO da OP ou PADRAO do produto    ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If !Empty((cAliasTop)->C2_ROTEIRO)
		cRoteiro:=(cAliasTop)->C2_ROTEIRO
	Else
		If !Empty(SB1->B1_OPERPAD)
			cRoteiro:=SB1->B1_OPERPAD
		Else
			If a630SeekSG2(1,(cAliasTop)->C2_PRODUTO,xFilial("SG2")+(cAliasTop)->C2_PRODUTO+"01")
				cRoteiro:="01"
			EndIf
		EndIf
	EndIf

	cSeekWhile := "SG2->(G2_FILIAL+G2_PRODUTO+G2_CODIGO)"
	If a630SeekSG2(1,(cAliasTop)->C2_PRODUTO,xFilial("SG2")+(cAliasTop)->C2_PRODUTO+cRoteiro,@cSeekWhile)

		While SG2->(!Eof()) .And. Eval(&cSeekWhile)
			SH8->(dbSetOrder(1))
			If SH8->(dbSeek(xFilial("SH8")+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)+SG2->G2_OPERAC))
				lSH8 := .T.
			EndIf

			If lSH8
				While SH8->(!Eof()) .And. SH8->(H8_FILIAL+H8_OP+H8_OPER) == xFilial("SH8")+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)+SG2->G2_OPERAC
					SH1->(dbSeek(xFilial("SH1")+SH8->H8_RECURSO))
					SH4->(dbSeek(xFilial("SH4")+SG2->G2_FERRAM))

					oSection3:Cell('G2_RECURSO'):SetValue(SH8->H8_RECURSO)
					oSection3:Cell('H1_DESCRI' ):SetValue(SH1->H1_DESCRI)
					oSection3:Cell('G2_FERRAM' ):SetValue(SG2->G2_FERRAM)
					oSection3:Cell('H4_DESCRI' ):SetValue(SH4->H4_DESCRI)
					oSection3:Cell('G2_OPERAC' ):SetValue(SG2->G2_OPERAC)
					//	oSection3:Cell('G2_DESCRI' ):SetValue(SG2->G2_DESCRI)
					oSection3:Cell('G2_DESCRI' ):SetValue(iif(!Empty(SG2->G2_DESCANT),SG2->G2_DESCANT,SG2->G2_DESCRI))

					If Empty(SH8->H8_DTINI)
						oSection4:Cell('H8_DTINI'):Disable()
						oSection4:Cell('H8_HRINI'):Disable()
						oSection4:Cell('H8_DTFIM'):Disable()
						oSection4:Cell('H8_HRFIM'):Disable()
						//oReport:PrintText('CARGA MAQUINA NAO GERADA!',,10)
						oSection3:PrintLine()
						oSection4:PrintLine()

						oReport:ThinLine()
						oReport:PrintText(cDetDelp1)
						oReport:ThinLine()

						For nI := 1 to MV_PAR13
							oReport:PrintText(cDetDelp2)
							oReport:ThinLine()
						Next nI

						//oReport:PrintText(cDetDelp2)
						//oReport:ThinLine()
					Else
						oSection4:Cell('H8_DTINI'):Enable()
						oSection4:Cell('H8_HRINI'):Enable()
						oSection4:Cell('H8_DTFIM'):Enable()
						oSection4:Cell('H8_HRFIM'):Enable()
						oSection3:PrintLine()
						oSection4:PrintLine()

						oReport:ThinLine()
						oReport:PrintText(cDetDelp1)
						oReport:ThinLine()
						For nI := 1 to MV_PAR13
							oReport:PrintText(cDetDelp2)
							oReport:ThinLine()
						Next nI
						//	oReport:PrintText(cDetDelp2)
						//	oReport:ThinLine()
						//	oReport:PrintText(cDetDelp2)
						//	oReport:ThinLine()
					EndIf

					SH8->(dbSkip())
				EndDo
			Else
				SH1->(dbSeek(xFilial("SH1")+SG2->G2_RECURSO))
				SH4->(dbSeek(xFilial("SH4")+SG2->G2_FERRAM))

				oSection3:Cell('G2_RECURSO'):SetValue(SG2->G2_RECURSO)
				oSection3:Cell('H1_DESCRI' ):SetValue(SH1->H1_DESCRI)
				oSection3:Cell('G2_FERRAM' ):SetValue(SG2->G2_FERRAM)
				oSection3:Cell('H4_DESCRI' ):SetValue(SH4->H4_DESCRI)
				oSection3:Cell('G2_OPERAC' ):SetValue(SG2->G2_OPERAC)
				//oSection3:Cell('G2_DESCRI' ):SetValue(SG2->G2_DESCRI)
				oSection3:Cell('G2_DESCRI' ):SetValue(iif(!Empty(SG2->G2_DESCANT),SG2->G2_DESCANT,SG2->G2_DESCRI))
				oSection3:PrintLine()

				//oReport:PrintText('CARGA MAQUINA NAO GERADA!',,10)
				oSection4:Cell('H8_DTINI'):Disable()
				oSection4:Cell('H8_HRINI'):Disable()
				oSection4:Cell('H8_DTFIM'):Disable()
				oSection4:Cell('H8_HRFIM'):Disable()
				oSection4:Cell('H8_QUANT'):SetValue(aSC2Sld(cAliasTop))

				oSection4:PrintLine()
				oReport:ThinLine()

				oReport:PrintText(cDetDelp1)
				oReport:ThinLine()
				For nI := 1 to MV_PAR13
					oReport:PrintText(cDetDelp2)
					oReport:ThinLine()
				Next nI
				//oReport:PrintText(cDetDelp2)


				oSection4:Cell('H8_DTINI'):Enable()
				oSection4:Cell('H8_HRINI'):Enable()
				oSection4:Cell('H8_DTFIM'):Enable()
				oSection4:Cell('H8_HRFIM'):Enable()
			Endif

			aOBS:=	fGetFerr(cAliasTop)

			For nObs := 1 to Len(aOBS)
				if nObs==1
					oReport:ThinLine()
				Endif
				cLin := aOBS[nObs][1]+" | "+padr(aOBS[nObs][2],40)+" | "+aOBS[nObs][3]
				oReport:PrintText(cLin)
				if len(aOBS)==nObs
					oReport:ThinLine()
				Endif
			Next nObs

			//	oReport:PrintText("TESTE GABRIEL")
			//	oReport:ThinLine()
			SG2->(dbSkip())
		EndDo
	Endif

	RestArea(aArea)
Return Nil
Static Function fGetFerr(cAliasTop)
	Local aRet := {}
	lOCAL cEol := chr(10)

	//StrTran(AllTrim(UPPER(StrTran(aItens[nX]:_Prod:_cProd:Text,"'"))), " ")
	cQuery := "SELECT *  FROM " +RetSqlName("SG1")+" SG1 "+cEol
	cQuery += " WHERE D_E_L_E_T_ = ' '  " +cEol
	cQuery +="AND G1_FILIAL	= "+VALTOSQL(xFilial("SG1")) +cEol
	cQuery +="AND G1_COD	= "+VALTOSQL((cAliasTop)->C2_PRODUTO) +cEol
	cQuery +="AND G1_OBSERV !=''  "


	If Select("TRB") > 0
		TRB->(dbCloseArea())
	EndIf

	TcQuery cQuery new Alias "TRB"

	WHILE !TRB->(EOF())
		cDesc := POSICIONE("SB1",1,XFILIAL("SB1")+TRB->G1_COMP,"B1_DESC")
		//AADD(aRet,{TRB->G1_COMP,cDesc,TRB->G1_OBSERV})
		AADD(aRet,{TRB->G1_COMP,cDesc,padr(TRB->G1_OBSERV,getsx3cache("G1_OBSERV","X3_TAMANHO")) })
		TRB->(dbSkip())
	EndDo

Return aRet
/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ MATR820  ³ Autor ³ Paulo Boschetti       ³ Data ³ 07.07.92 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Ordens de Producao                                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe e ³ MATR820(void)                                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ Generico                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
*/
User Function DLP013R3()
	Local titulo  := STR0039 //"Ordens de Producao"
	Local cString := "SC2"
	Local wnrel   := "DLP013"
	Local cDesc   := STR0001	//"Este programa ira imprimir a Rela‡„o das Ordens de Produ‡„o"
	Local aOrd    := {STR0002,STR0003,STR0004,STR0005}	//"Por Numero"###"Por Produto"###"Por Centro de Custo"###"Por Prazo de Entrega"
	Local tamanho := "P"

	Private aReturn  := {STR0006,1,STR0007, 1, 2, 1, "",1 }	//"Zebrado"###"Administracao"
	Private cPerg    :="DLP013"
	Private nLastKey := 0
	Private lItemNeg := .F.

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica as perguntas selecionadas                           ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	AjustaSX1()
	pergunte("DLP013",.F.)
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Variaveis utilizadas para parametros                         ³
	//³ mv_par01            // Da OP                                 ³
	//³ mv_par02            // Ate a OP                              ³
	//³ mv_par03            // Da data                               ³
	//³ mv_par04            // Ate a data                            ³
	//³ mv_par05            // Imprime roteiro de operacoes          ³
	//³ mv_par06            // Imprime codigo de barras              ³
	//³ mv_par07            // Imprime Nome Cientifico               ³
	//³ mv_par08            // Imprime Op Encerrada                  ³
	//³ mv_par09            // Impr. por Ordem de                    ³
	//³ mv_par10            // Impr. OP's Firmes, Previstas ou Ambas ³
	//³ mv_par11            // Impr. Item Negativo na Estrutura      ³
	//³ mv_par12            // Imprime Lote/Sub-Lote                 ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	//-- Verifica se o SH8 esta locado para atualizacao por outro processo
	If !IsLockSH8()
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Envia controle para a funcao SETPRINT                        ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

		//wnrel:=SetPrint(cString,wnrel,cPerg,@titulo,cDesc,"","",.F.,aOrd,.T.,Tamanho)
		wnrel:=SetPrint(cString,wnrel,cPerg,@titulo,cDesc,"","",.F.,aOrd,,Tamanho)

		lItemNeg := GetMv("MV_NEGESTR") .And. mv_par11 == 1

		If nLastKey == 27
			dbSelectArea("SH8")
			dbClearFilter()
			dbCloseArea()
			dbSelectArea("SC2")
			Return
		Endif

		SetDefault(aReturn,cString)

		If nLastKey == 27
			dbSelectArea("SH8")
			dbClearFilter()
			dbCloseArea()
			dbSelectArea("SC2")
			Return
		Endif

		RptStatus({|lEnd| R820Imp(@lEnd,wnRel,titulo,/*if(mv_par12 == 2,"P","M")*/)},titulo)

	EndIf

Return NIL

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡„o    ³ R820Imp  ³ Autor ³ Waldemiro L. Lustosa  ³ Data ³ 13.11.95 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡„o ³ Chamada do Relat¢rio                                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR820			                                          ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function R820Imp(lEnd,wnRel,titulo,tamanho)

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Define Variaveis                                             ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	Local CbCont,cabec1,cabec2
	Local limite     := 80
	Local nQuant     := 1
	Local nomeprog   := "DLP013"
	Local nPagina	 := 1
	Local nTipo      := 18
	Local cPictQuant := PesqPictQt("D4_QUANT",TamSX3("D4_QUANT")[1])
	Local cProduto   := SPACE(LEN(SC2->C2_PRODUTO))
	Local cQtd,i,nBegin
	Local cIndSC2    := CriaTrab(NIL,.F.), nIndSC2

	#IFDEF TOP
		Local bBlockFiltro := {|| .T.}
	#ENDIF

	Private aArray   := {}
	Private li       := 80

	cAliasTop  := "SC2"

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Variaveis utilizadas para Impressao do Cabecalho e Rodape    ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	cbtxt    := SPACE(10)
	cbcont   := 0
	m_pag    := 1
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Monta os Cabecalhos                                          ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	cabec1 := ""
	cabec2 := ""

	dbSelectArea("SC2")

	#IFDEF TOP
		cAliasTop := GetNextAlias()
		cQuery := "SELECT SC2.C2_FILIAL, SC2.C2_NUM, SC2.C2_ITEM, SC2.C2_SEQUEN, SC2.C2_ITEMGRD, SC2.C2_DATPRF, "
		cQuery += "SC2.C2_DATRF, SC2.C2_PRODUTO, SC2.C2_DESTINA, SC2.C2_PEDIDO, SC2.C2_ROTEIRO, SC2.C2_QUJE, "
		cQuery += "SC2.C2_PERDA, SC2.C2_QUANT, SC2.C2_DATPRI, SC2.C2_CC, SC2.C2_DATAJI, SC2.C2_DATAJF, "
		cQuery += "SC2.C2_STATUS, SC2.C2_OBS, SC2.C2_TPOP, "
		cQuery += "SC2.R_E_C_N_O_  SC2RECNO FROM "+RetSqlName("SC2")+" SC2 WHERE "
		cQuery += "SC2.C2_FILIAL='"+xFilial("SC2")+"' AND SC2.D_E_L_E_T_=' ' "
		If	Upper(TcGetDb()) $ 'ORACLE,DB2,POSTGRES,INFORMIX'
			cQuery += "AND SC2.C2_NUM || SC2.C2_ITEM || SC2.C2_SEQUEN || SC2.C2_ITEMGRD >= '" + mv_par01 + "' "
			cQuery += "AND SC2.C2_NUM || SC2.C2_ITEM || SC2.C2_SEQUEN || SC2.C2_ITEMGRD <= '" + mv_par02 + "' "
		Else
			cQuery += "AND SC2.C2_NUM+SC2.C2_ITEM+SC2.C2_SEQUEN+SC2.C2_ITEMGRD BETWEEN '"+ mv_par01 + "' AND '" + mv_par02 +"' "
		Endif
		cQuery += "AND SC2.C2_DATPRI BETWEEN '" + Dtos(mv_par03) + "' AND '" + Dtos(mv_par04) + "' "
		If mv_par08 == 2
			cQuery += "AND SC2.C2_DATRF = ' '"
		Endif
		If aReturn[8] == 4
			cQuery += "ORDER BY SC2.C2_FILIAL, SC2.C2_DATPRF"
		Else
			cQuery += "ORDER BY " + SqlOrder(SC2->(IndexKey(aReturn[8])))
		EndIf
		cQuery := ChangeQuery(cQuery)
		dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasTop,.T.,.T.)
		aEval(SC2->(dbStruct()), {|x| If(x[2] <> "C" .And. FieldPos(x[1]) > 0, TcSetField(cAliasTop,x[1],x[2],x[3],x[4]),Nil)})
		dbSelectArea(cAliasTop)
	#ELSE
		If aReturn[8] == 4
			Set Filter To
			cTrbSC2  := Criatrab(Nil,.F.)
			cKeySC2 := "C2_FILIAL+C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD+DTOS(C2_DATPRI)"
			cFiltro := "C2_FILIAL == '"+xFilial("SC2")+"' .AND. "
			cFiltro += "C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD >= '"+mv_par01+"' .AND. C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD <= '"+mv_par02+"' .AND. "
			cFiltro += "DTOS(C2_DATPRI) >= '"+dTos(mv_par03)+"' .AND. DTOS(C2_DATPRI) <= '"+dTos(mv_par04)+"' "
			IndRegua("SC2",cIndSC2,"C2_FILIAL+DTOS(C2_DATPRF)",,,STR0008)	//"Selecionando Registros..."
		Else
			dbSetOrder(aReturn[8])
		EndIf
		dbSeek(xFilial("SC2"))
		cAliasTop := 'SC2'
	#ENDIF

	If ! Empty(aReturn[7])
		bBlockFiltro := &("{|| " + aReturn[7] + "}")
	Endif

	SetRegua((cAliasTop)->(LastRec()))

	While !(cAliasTop)->(Eof())

		IF lEnd
			@ Prow()+1,001 PSay STR0009	//"CANCELADO PELO OPERADOR"
			Exit
		EndIF

		IncRegua()

		If (cAliasTop)->(C2_FILIAL+C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD) < xFilial('SC2')+mv_par01 .or. (cAliasTop)->(C2_FILIAL+C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD) > xFilial('SC2')+mv_par02
			(cAliasTop)->(dbSkip())
			Loop
		EndIf

		#IFNDEF TOP
			If  (cAliasTop)->C2_DATPRF < mv_par03 .Or. (cAliasTop)->C2_DATPRF > mv_par04
				(cAliasTop)->(dbSkip())
				Loop
			Endif

			If !(Empty((cAliasTop)->C2_DATRF)) .And. mv_par08 == 2
				(cAliasTop)->(dbSkip())
				Loop
			Endif
		#ENDIF

		If !Empty(aReturn[7])
			#IFDEF TOP
				(cAliasTop)->(dbGoto((cAliasTop)->SC2RECNO))
			#ENDIF

			If !((cAliasTop)->(Eval(bBlockFiltro)))
				(cAliasTop)->(dbSkip())
				Loop
			EndIf
		Endif

		//-- Valida se a OP deve ser Impressa ou n„o
		If !MtrAValOP(mv_par10,"SC2",cAliasTop)
			(cAliasTop)->(dbSkip())
			Loop
		EndIf

		cProduto  := (cAliasTop)->C2_PRODUTO
		nQuant    := aSC2Sld(cAliasTop)

		dbSelectArea("SB1")
		dbSeek(xFilial()+cProduto)

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Adiciona o primeiro elemento da estrutura , ou seja , o Pai  ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		AddAr820(nQuant)

		MontStruc((cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD),nQuant)

		If mv_par09 == 1
			aSort( aArray,2,, { |x, y| (x[1]+x[8]) < (y[1]+y[8]) } )
		Else
			aSort( aArray,2,, { |x, y| (x[8]+x[1]) < (y[8]+y[1]) } )
		ENDIF

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Imprime cabecalho                                       ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		aArea := SB1->(GetArea())
		nPagina := 1
		cabecOp(Tamanho, nPagina)
		RestArea(aArea)

		For I := 2 TO Len(aArray)
			@Li,   0 PSay substr(aArray[I][1],1,tamsx3('B1_COD')[1])
			//@Li,   0 PSay aArray[I][1]    	 				   	// CODIGO PRODUTO
			For nBegin := 1 To Len(Alltrim(aArray[I][2])) Step 31
				@li,017 PSay Substr(aArray[I][2],nBegin,31)

				li++
			Next nBegin
			Li--

			cQtd := Alltrim(Transform(aArray[I][5],cPictQuant))
			@Li , (46+11-Len(cQtd)) PSay cQtd					// QUANTIDADE

			//@Li ,46 PSay substr(aArray[I][5],1,tamsx3("D4_QUANT")[1])

			If mv_par12 == 2
				@Li ,  58 PSay "|"+aArray[I][4]+"|"			  	// UNIDADE DE MEDIDA
				@li ,  62 PSay aArray[I][6]+"|"                  	// ALMOXARIFADO
				@li ,  65 PSay Substr(aArray[I][7],1,12)         	// LOCALIZACAO
				@li ,  75 PSay "  |"+aArray[I][8]                  	// SEQUENCIA
			Else
				@Li ,  59 PSay "| "+aArray[I][4]+" |"			  	// UNIDADE DE MEDIDA
				@li ,  65 PSay aArray[I][6]+"  |"                  	// ALMOXARIFADO
				@li ,  70 PSay Substr(aArray[I][7],1,12)         	// LOCALIZACAO
				@li ,  83 PSay " | "+aArray[I][8]                  	// SEQUENCIA
				@li ,  89 PSay " | "+aArray[I][10]                  	// LOTE
				@li , 102 PSay " | "+aArray[I][11]                  	// SUB-LOTE
			EndIf
			Li++
			@Li ,  00 PSay __PrtThinLine()
			Li++

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Se nao couber, salta para proxima folha                 ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			IF li > 59
				Li := 0
				nPagina++
				m_pag++
				CabecOp(Tamanho, nPagina)		// imprime cabecalho da OP
			EndIF

		Next I

		If mv_par05 == 1
			RotOper()   	// IMPRIME ROTEIRO DAS OPERACOES
		Endif

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Imprimir Relacao de medidas para Cliente == HUNTER DOUGLAS.  ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		dbSelectArea("SX3")
		dbSetOrder(1)
		dbSeek("SMX")
		If Found() .And. (cAliasTop)->C2_DESTINA == "P"
			R820Medidas()
		EndIf

		Li := 0					// linha inicial - ejeta automatico
		aArray:={}

		dbSelectArea(cAliasTop)
		dbSkip()

	EndDO

	dbSelectArea("SH8")
	dbCloseArea()

	dbSelectArea("SC2")
	#IFDEF TOP
		(cAliasTop)->(dbCloseArea())
	#ELSE
		If aReturn[8] == 4
			RetIndex("SC2")
			Ferase(cIndSC2+OrdBagExt())
		EndIf
	#ENDIF
	dbClearFilter()
	dbSetOrder(1)

	If aReturn[5] = 1
		Set Printer TO
		dbCommitall()
		ourspool(wnrel)
	Endif

	MS_FLUSH()

Return NIL

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³ Fun‡…o   ³ AddAr820 ³ Autor ³ Paulo Boschetti       ³ Data ³ 07/07/92 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Descri‡…o³ Adiciona um elemento ao Array                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Sintaxe  ³ AddAr820(ExpN1)                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpN1 = Quantidade da estrutura                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
*/
Static Function AddAr820(nQuantItem)
	Local cDesc   := SB1->B1_DESC
	Local cLocal  := ""
	Local cKey    := ""
	Local cRoteiro:= ""
	Local nQtdEnd
	Local lExiste

	Local lVer116   := (VAL(GetVersao(.F.)) == 11 .And. GetRpoRelease() >= "R6" .Or. VAL(GetVersao(.F.))  > 11)

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica se imprime nome cientifico do produto. Se Sim    ³
	//³ verifica se existe registro no SB5 e se nao esta vazio    ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If mv_par07 == 1
		dbSelectArea("SB5")
		dbSeek(xFilial()+SB1->B1_COD)
		If Found() .and. !Empty(B5_CEME)
			cDesc := B5_CEME
		EndIf
	ElseIf mv_par07 == 2
		cDesc := SB1->B1_DESC
	Else
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica se imprime descricao digitada ped.venda, se sim  ³
		//³ verifica se existe registro no SC6 e se nao esta vazio    ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If (cAliasTop)->C2_DESTINA == "P"
			dbSelectArea("SC6")
			dbSetOrder(1)
			dbSeek(xFilial()+(cAliasTop)->C2_PEDIDO+(cAliasTop)->C2_ITEM)
			If Found() .and. !Empty(C6_DESCRI) .and. C6_PRODUTO==SB1->B1_COD
				cDesc := C6_DESCRI
			ElseIf C6_PRODUTO # SB1->B1_COD
				dbSelectArea("SB5")
				dbSeek(xFilial()+SB1->B1_COD)
				If Found() .and. !Empty(B5_CEME)
					cDesc := B5_CEME
				EndIf
			EndIf
		EndIf
	EndIf

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica se imprime ROTEIRO da OP ou PADRAO do produto    ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If !Empty((cAliasTop)->C2_ROTEIRO)
		cRoteiro:=(cAliasTop)->C2_ROTEIRO
	Else
		If !Empty(SB1->B1_OPERPAD)
			cRoteiro:=SB1->B1_OPERPAD
		Else
			dbSelectArea("SG2")
			If dbSeek(xFilial()+(cAliasTop)->C2_PRODUTO+"01")
				cRoteiro:="01"
			EndIf
		EndIf
	EndIf

	If lVer116
		dbSelectArea("NNR")
		dbSeek(xFilial()+SD4->D4_LOCAL)
	Else
		dbSelectArea("SB2")
		dbSeek(xFilial()+SB1->B1_COD+SD4->D4_LOCAL)
	EndIf

	dbSelectArea("SD4")
	cKey:=SD4->D4_COD+SD4->D4_LOCAL+SD4->D4_OP+SD4->D4_TRT+SD4->D4_LOTECTL+SD4->D4_NUMLOTE
	cLocal:=SB2->B2_LOCALIZ

	lExiste := .F.

	If !lVer116
		DbSelectArea("SDC")
		DbSetOrder(2)
		DbSeek(xFilial("SDC")+cKey)
		//If !Eof() .And. SDC->(DC_PRODUTO+DC_LOCAL+DC_OP+DC_TRT+DC_LOTECTL+DC_NUMLOTE) == cKey
		While !Eof().And. SDC->(DC_PRODUTO+DC_LOCAL+DC_OP+DC_TRT+DC_LOTECTL+DC_NUMLOTE) == cKey
			cLocal  :=DC_LOCALIZ
			nQtdEnd :=DC_QTDORIG

			AADD(aArray, {SB1->B1_COD,cDesc,SB1->B1_TIPO,SB1->B1_UM,nQtdEnd,SD4->D4_LOCAL,cLocal,SD4->D4_TRT,cRoteiro,If(mv_par12 == 1,SD4->D4_LOTECTL,""),If(mv_par12 == 1,SD4->D4_NUMLOTE,"") } )
			lExiste := .T.
			dbSkip()
		end
		//EndIf
	endif

	dbSelectArea("SD4")

	if !lExiste
		If lVer116
			AADD(aArray, {SB1->B1_COD,cDesc,SB1->B1_TIPO,SB1->B1_UM,nQuantItem,SD4->D4_LOCAL,NNR->NNR_DESCRI,SD4->D4_TRT,cRoteiro,If(mv_par12 == 1,SD4->D4_LOTECTL,""),If(mv_par12 == 1,SD4->D4_NUMLOTE,"") } )
		Else
			AADD(aArray, {SB1->B1_COD,cDesc,SB1->B1_TIPO,SB1->B1_UM,nQuantItem,SD4->D4_LOCAL,cLocal,SD4->D4_TRT,cRoteiro,If(mv_par12 == 1,SD4->D4_LOTECTL,""),If(mv_par12 == 1,SD4->D4_NUMLOTE,"") } )
		EndIf
	endif

Return
/*/
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
	±±³ Fun‡…o   ³ MontStruc³ Autor ³ Ary Medeiros          ³ Data ³ 19/10/93 ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
	±±³ Descri‡…o³ Monta um array com a estrutura do produto                  ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³ Sintaxe  ³ MontStruc(ExpC1,ExpN1,ExpN2)                               ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³Parametros³ ExpC1 = Codigo do produto a ser explodido                  ³±±
	±±³          ³ ExpN1 = Quantidade base a ser explodida                    ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³ Uso      ³ MATR820                                                    ³±±
	±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
/*/
Static Function MontStruc(cOp,nQuant)

	dbSelectArea("SD4")
	dbSetOrder(2)
	dbSeek(xFilial()+cOp)

	While !Eof() .And. D4_FILIAL+D4_OP == xFilial()+cOp
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Posiciona no produto desejado                           ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		dbSelectArea("SB1")
		If dbSeek(xFilial()+SD4->D4_COD)
			If SD4->D4_QUANT > 0 .Or. (lItemNeg .And. SD4->D4_QUANT < 0)
				AddAr820(SD4->D4_QUANT)
			EndIf
		Endif
		dbSelectArea("SD4")
		dbSkip()
	Enddo

	dbSetOrder(1)

Return

/*/
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
	±±³ Fun‡…o   ³ CabecOp  ³ Autor ³ Paulo Boschetti       ³ Data ³ 07/07/92 ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
	±±³ Descri‡…o³ Monta o cabecalho da Ordem de Producao                     ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³ Sintaxe  ³ CabecOp()                                                  ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³Parametros³                                                            ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³ Uso      ³ MATR820                                                    ³±±
	±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
/*/
Static Function CabecOp(Tamanho, nPagOp)

	//Local cTitulo := If(mv_par12 == 2,STR0010,STR0054)+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)
	//Local cCabec1 := STR0066+RTrim(SM0->M0_NOME)+" / "+STR0067+Alltrim(SM0->M0_FILIAL)
	//Local cCabec2 := If(mv_par12 == 2,STR0011,STR0055)	//"  C O M P O N E N T E S                                  |  |  |            |   "
	//Local cCabec3 := If(mv_par12 == 2,STR0012,STR0056)	//"CODIGO          DESCRICAO                      QUANTIDADE|UM|AL|LOCALIZACAO |SEQ"
	// 012345678901234567890123456789012345678901234567890123456789012345678901234567890
	//	       1         2         3         4         5         6         7         8

	Local cCabec1 := SM0->M0_NOME+STR0010	//"        O R D E M   D E   P R O D U C A O       NRO :"
	Local cCabec2 := STR0011				//"  C O M P O N E N T E S                                  |  |  |            |   "
	Local cCabec3 := STR0012				//"CODIGO          DESCRICAO                      QUANTIDADE|UM|AL|LOCALIZACAO |SEQ"
	//								           012345678901234567890123456789012345678901234567890123456789012345678901234567890
	//                        			       1         2         3         4         5         6         7         8
	Local cCabec4 := STR0029

	Local nBegin
	Local nLinha   := 0
	Local nomeprog := "DLP013"
	Local cPictQuant := PesqPictQt("C2_QUANT",TamSX3("C2_QUANT")[1])
	Local cProdPA	:= ''
	Local cDescSB1	:= ''

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Verificar se o ambiente é cliente ou servidor.³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	//If SetPrintEnv() == 1
	nLinha := 1.0
	//Else
	//	nLinha := 0.8
	//EndIf

	If li # 5
		li := 0
	Endif

	//Cabec(cTitulo,cCabec1,"",NomeProg,Tamanho,18,,.F.)
	Cabec("","","","",Tamanho,18,{cCabec1+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN)},.F.)

	Li+=2
	IF (mv_par06 == 1) .And. aReturn[5] # 1
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Imprime o codigo de barras do numero da OP              ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		oPr := ReturnPrtObj()
		cCode := (cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)
		MSBAR3("CODE128",nLinha,0.5,Alltrim(cCode),oPr,Nil,Nil,Nil,nil ,1.5 ,Nil,Nil,Nil)
		Li += 5
	ENDIF

	// Acrescentar o Codigo do produto Acabado da OP Sequencia 001 quando for necessario
	If	(cAliasTop)->C2_SEQUEN > '001'
		aAreaSB1 := SB1->(GetArea())
		SC2->(DbSetOrder(1))
		SC2->(MsSeek(xFilial('SC2')+(cAliasTop)->(C2_NUM+C2_ITEM+'001')))
		If	SC2->(Found())
			cProdPA := AllTrim(SC2->C2_PRODUTO)
			SB1->(DbSeek(xFilial('SB1')+(cAliasTop)->C2_PRODUTO))
			If	SB1->(Found()) //.And. !Empty(SB1->B1_REFEREN)
				cDescSB1 := AllTrim(SB1->B1_DESC) + IIf(!Empty(cProdPA),' / ','') + IIf(!Empty(cProdPA),cProdPA,'')
			EndIf
		EndIf
		RestArea(aAreaSB1)
	EndIf

	@Li,00 PSay STR0013+aArray[1][1]+ " " + IIf(!Empty(cDescSB1),cDescSB1,aArray[1][2])	//"Produto: "
	Li++

	If	(cAliasTop)->C2_SEQUEN == '001'
		SC2->(DbSetOrder(1))
		SC2->(MsSeek(xFilial('SC2')+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN)))
		If	SC2->(Found())
			aAreaSB1 := SB1->(GetArea())
			SB1->(DbSeek(xFilial('SB1')+SC2->C2_PRODUTO))
			If	SB1->(Found()) //.And. !Empty(SB1->B1_REFEREN)
				@Li,00 PSay 'Referencia: '+ RTrim(SB1->B1_REFEREN)
				Li++
			EndIf
			RestArea(aAreaSB1)
		EndIf
	EndIf

	@Li,00 PSay STR0014+DTOC(dDatabase)						//"Emissao:"
	@Li,73 PSay STR0015+TRANSFORM(nPagOp,'999')				//"Fol:"
	Li++

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Imprime nome do cliente quando OP for gerada            ³
	//³ por pedidos de venda                                    ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If (cAliasTop)->C2_DESTINA == "P"
		dbSelectArea("SC5")
		dbSetOrder(1)
		If dbSeek(xFilial()+(cAliasTop)->C2_PEDIDO,.F.)
			dbSelectArea("SA1")
			dbSetOrder(1)
			dbSeek(xFilial()+SC5->C5_CLIENTE+SC5->C5_LOJACLI)
			@Li,00 PSay STR0016	//"Cliente :"
			@Li,10 PSay SC5->C5_CLIENTE+"-"+SC5->C5_LOJACLI+" "+A1_NOME
			dbSelectArea("SG1")
			Li++
		EndIf
	EndIf

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Imprime a quantidade original quando a quantidade da    ³
	//³ Op for diferente da quantidade ja entregue              ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If (cAliasTop)->C2_QUJE + (cAliasTop)->C2_PERDA > 0
		@Li,00 PSay STR0017                 //"Qtde Prod.:"
		@Li,11 PSay aSC2Sld(cAliasTop)		PICTURE cPictQuant
		@Li,26 PSay STR0018                 //"Qtde Orig.:"
		@Li,37 PSay (cAliasTop)->C2_QUANT	PICTURE cPictQuant
	Else
		@Li,00 PSay STR0019			//"Quantidade :"
		@Li,15 PSay (cAliasTop)->C2_QUANT - (cAliasTop)->C2_QUJE	PICTURE cPictQuant
	Endif

	@Li,56 PSay STR0020	//"INICIO             F I M"
	Li++
	@Li,00 PSay STR0021+aArray[1][4]			//"Unid. Medida : "
	@Li,42 PSay STR0022+DTOC((cAliasTop)->C2_DATPRI)	//"Prev. : "
	@Li,62 PSay STR0022+DTOC((cAliasTop)->C2_DATPRF)	//"Prev. : "
	Li++
	@Li,00 PSay STR0023+(cAliasTop)->C2_CC				//"C.Custo: "
	@Li,42 PSay STR0024+DTOC((cAliasTop)->C2_DATAJI)	//"Ajuste: "
	@Li,62 PSay STR0024+DTOC((cAliasTop)->C2_DATAJF)	//"Ajuste: "
	Li++
	If (cAliasTop)->C2_STATUS == "S"
		@Li,00 PSay STR0025						//"Status: OP Sacramentada"
	ElseIf (cAliasTop)->C2_STATUS == "U"
		@Li,00 PSay STR0026						//"Status: OP Suspensa"
	ElseIf (cAliasTop)->C2_STATUS $ " N"
		@Li,00 PSay STR0027						//"Status: OP Normal"
	EndIf
	@Li,42 PSay STR0028							//	"Real  :   /  /      Real  :   /  / "
	Li++

	If !(Empty((cAliasTop)->C2_OBS))
		@Li,00 PSay STR0029						//"Observacao: "
		For nBegin := 1 To Len(Alltrim((cAliasTop)->C2_OBS)) Step 65
			@li,012 PSay Substr((cAliasTop)->C2_OBS,nBegin,65)
			li++
		Next nBegin
	EndIf

	@Li,00 PSay __PrtFatLine()
	Li++
	@Li,00 PSay cCabec2
	Li++
	@Li,00 PSay cCabec3
	Li++
	@Li,00 PSay __PrtFatLine()
	Li++

	/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³ Fun‡…o   ³ RotOper  ³ Autor ³ Paulo Boschetti       ³ Data ³ 18/07/92 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Descri‡…o³ Imprime Roteiro de Operacoes                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Sintaxe  ³ RotOper()                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	*/
	Static Function RotOper()

		Local cCabec1 := SM0->M0_NOME+STR0030	//"              ROTEIRO DE OPERACOES              NRO :"
		Local cCabec2 := STR0031					//"RECURSO                       FERRAMENTA               OPERACAO"
		Local nBegin, lSH8
		Local cSeekWhile := "SG2->(G2_FILIAL+G2_PRODUTO+G2_CODIGO)"
		dbSelectArea("SG2")
		If a630SeekSG2(1,aArray[1][1],xFilial("SG2")+aArray[1][1]+aArray[1][9],@cSeekWhile)

			cRotOper()

			While !Eof() .And. Eval(&cSeekWhile)

				dbSelectArea("SH4")
				dbSeek(xFilial()+SG2->G2_FERRAM)

				dbSelectArea("SH8")
				dbSetOrder(1)
				dbSeek(xFilial()+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)+SG2->G2_OPERAC)
				lSH8 := IIf(Found(),.T.,.F.)

				If lSH8
					While !Eof() .And. SH8->H8_FILIAL+SH8->H8_OP+SH8->H8_OPER == xFilial()+(cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)+SG2->G2_OPERAC
						ImpRot(lSH8)
						dbSelectArea("SH8")
						dbSkip()
					End
				Else
					ImpRot(lSH8)
				Endif

				dbSelectArea("SG2")
				dbSkip()

			EndDo

		Endif

	Return Li

	/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³ Fun‡…o   ³ ImpRot   ³ Autor ³ Marcos Bregantim      ³ Data ³ 10/07/95 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Descri‡…o³ Imprime Roteiro de Operacoes                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Sintaxe  ³ ImpRot()                                                   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	*/
	Static Function ImpRot(lSH8)
		Local nBegin

		dbSelectArea("SH1")
		dbSeek(xFilial()+IIf(lSH8,SH8->H8_RECURSO,SG2->G2_RECURSO))

		Verilim()

		@Li,00 PSay IIF(lSH8,SH8->H8_RECURSO,SG2->G2_RECURSO)+" "+SUBS(SH1->H1_DESCRI,1,25)
		@Li,33 PSay SG2->G2_FERRAM+" "+SUBS(SH4->H4_DESCRI,1,20)
		@Li,61 PSay SG2->G2_OPERAC

		For nBegin := 1 To Len(Alltrim(SG2->G2_DESCRI)) Step 16
			@li,064 PSay Substr(SG2->G2_DESCRI,nBegin,16)
			li++

			IF li > 55
				Li := 0
				cRotOper()
			EndIF
		Next nBegin

		dDatIni := ctod('  /  /  ')
		dDatFin := ctod('  /  /  ')
		sHorIni := '  :  '
		sHorFin := '  :  '

		If Empty(dDatIni)
			dDatIni := SH8->H8_DTINI
			sHorIni := SH8->H8_HRINI
		EndIf
		dDatFin := SH8->H8_DTFIM
		sHorFin := SH8->H8_HRFIM
		If Empty(dDatIni)
			li++
			Verilim()
			@Li,10 PSay 'CARGA MAQUINA NAO GERADA!'
		Else
			Li+=1
			@Li,00 PSay STR0032+IIF(lSH8,DTOC(dDatIni),Space(8))+" "+IIF(lSH8,sHorIni,Space(5))+" "+STR0034+IIF(lSH8,DTOC(dDatFin),Space(8))+" "+IIF(lSH8,sHorFin,Space(5))
		EndIf

		/*Li++
	@Li,00 PSay STR0032+IIF(lSH8,DTOC(SH8->H8_DTINI),Space(8))+" "+IIF(lSH8,SH8->H8_HRINI,Space(5))+" "+STR0033+" ____/ ____/____ ___:___"	//"INICIO  ALOC.: "###" INICIO  REAL :"
	Li++
		@Li,00 PSay STR0034+IIF(lSH8,DTOC(SH8->H8_DTFIM),Space(8))+" "+IIF(lSH8,SH8->H8_HRFIM,Space(5))+" "+STR0035+" ____/ ____/____ ___:___"	//"TERMINO ALOC.: "###" TERMINO REAL :"*/
		Li++
		@Li,00 PSay STR0019	//"Quantidade :"
		@Li,13 PSay IIF(lSH8,SH8->H8_QUANT,aSC2Sld(cAliasTop)) PICTURE PesqPictQt("H8_QUANT",14)
		@Li,28 PSay STR0036	//"Quantidade Produzida :               Perdas :"
		Li++
		@Li,00 PSay __PrtThinLine()
		//INICIO ROBERTO FAUSTO TSC 243
		Li++
		@Li,00 PSay cCabDelp1
		Li++
		@Li,00 PSay __PrtThinLine()
		Li++
		@Li,00 PSay cCabDelp2
		Li++
		@Li,00 PSay __PrtThinLine()
		Li++
		@Li,00 PSay cCabDelp2
		Li++
		@Li,00 PSay __PrtThinLine()
		Li++
		@Li,00 PSay cCabDelp2
		Li++
		@Li,00 PSay __PrtThinLine()
		//FIM ROBERTO FAUSTO TSC 243
		Li++

	Return

	/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³ Fun‡…o   ³ RotOper  ³ Autor ³ Paulo Boschetti       ³ Data ³ 18/07/92 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Descri‡…o³ Imprime Roteiro de Operacoes                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Sintaxe  ³ RotOper()                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	*/
	Static Function cRotOper()

		Local cCabec1 := SM0->M0_NOME+STR0030	//"              ROTEIRO DE OPERACOES              NRO :"
		Local cCabec2 := STR0031					//"RECURSO                       FERRAMENTA               OPERACAO"

		Li++
		@Li,00 PSay __PrtFatLine()
		Li++
		@Li,00 PSay cCabec1
		@Li,67 PSay (cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)
		Li++
		@Li,00 PSay __PrtFatLine()
		Li++
		@Li,00 PSay STR0013+aArray[1][1]	//"Produto: "
		ImpDescr(aArray[1][2])

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Imprime a quantidade original quando a quantidade da    ³
		//³ Op for diferente da quantidade ja entregue              ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		If (cAliasTop)->C2_QUJE + (cAliasTop)->C2_PERDA > 0
			@Li,00 PSay STR0017                 //"Qtde Prod.:"
			@Li,11 PSay aSC2Sld(cAliasTop)      PICTURE PesqPictQt("C2_QUANT",TamSX3("C2_QUANT")[1])
			@Li,26 PSay STR0018                 //"Qtde Orig.:"
			@Li,37 PSay (cAliasTop)->C2_QUANT   PICTURE PesqPictQt("C2_QUANT",TamSX3("C2_QUANT")[1])
		Else
			@Li,00 PSay STR0019            //"Quantidade :"
			@Li,15 PSay aSC2Sld(cAliasTop)	PICTURE PesqPictQt("C2_QUANT",TamSX3("C2_QUANT")[1])
		Endif

		/*Li++
		@Li,00 PSay STR0023+(cAliasTop)->C2_CC	//"C.Custo: "*/
		Li++
		@Li,00 PSay STR0023+(cAliasTop)->C2_OBS	//"Observação: "
		Li++
		@Li,00 PSay __PrtFatLine()
		Li++
		@Li,00 PSay cCabec2
		Li++
		@Li,00 PSay __PrtFatLine()
		Li++
	Return Li

	/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³ Fun‡…o   ³ Verilim  ³ Autor ³ Paulo Boschetti       ³ Data ³ 18/07/92 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Descri‡…o³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Sintaxe  ³ Verilim()                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ 			                                          		  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	*/
	Static Function Verilim()

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Verifica a possibilidade de impressao da proxima operacao alocada na ³
		//³ mesma folha.																			 ³
		//³ 7 linhas por operacao => (total da folha) 66 - 7 = 59					 ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		IF Li > 55						// Li > 55
			Li := 0
			cRotOper(0)					// Imprime cabecalho roteiro de operacoes
		Endif
	Return Li

	/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ ImpDescr ³ Autor ³ Marcos Bregantim      ³ Data ³ 31.08.93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Imprimir descricao do Produto.                             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ ImpProd(Void)                                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MatR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
	*/
	Static Function ImpDescr(cDescri)
		Local nBegin

		For nBegin := 1 To Len(Alltrim(cDescri)) Step 50
			@li,025 PSay Substr(cDescri,nBegin,50)
			li++
		Next nBegin

	Return

	/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³R820Medidas³ Autor ³ Jose Lucas           ³ Data ³ 25.01.94 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Imprime o registros referentes as medidas do Pedido Filho. ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ R820Medidas(Void)                                          ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MatR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
	*/
	Static Function R820Medidas()
		Local aArrayPro := {}, lImpItem := .T.
		Local nCntArray := 0,a01 := "",a02 := ""
		Local nX:=0,nI:=0,nL:=0,nY:=0
		Local cNum:="", cItem:="",lImpCab := .T.
		Local nBegin, cProduto:="", cDesc, cDescri, cDescri1, cDescri2

		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Imprime Relacao de Medidas do cliente quando OP for gerada ³
		//³ por pedidos de vendas.                                     ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		dbSelectArea("SC5")
		dbSetOrder(1)
		If dbSeek(xFilial()+(cAliasTop)->C2_PEDIDO,.F.)
			cNum := (cAliasTop)->C2_NUM
			cItem := (cAliasTop)->C2_ITEM
			cProduto := (cAliasTop)->C2_PRODUTO
			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Imprimir somente se houver Observacoes.                      ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			IF !Empty(SC5->C5_OBSERVA)
				IF li > 53
					@ 03,001 PSay "HUNTER DOUGLAS DO BRASIL LTDA"
					@ 05,008 PSay "CONFIRMACAO DE PEDIDOS  -  "+IIF( SC5->C5_VENDA=="01","ASSESSORIA","DISTRIBUICAO")
					@ 05,055 PSay "No. RMP    : "+SC5->C5_NUM+"-"+SC5->C5_VENDA
					@ 06,055 PSay "DATA IMPRES: "+DTOC(dDataBase)
					li := 07
				EndIF
				li++
				@ li,001 PSay "--------------------------------------------------------------------------------"
				li++
				cDescri := SC5->C5_OBSERVA
				@ li,001 PSay " OBSERVACAO: "
				@ li,018 PSay SubStr(cDescri,1,60)
				For nBegin := 61 To Len(Trim(cDescri)) Step 60
					li++
					cDesc:=Substr(cDescri,nBegin,60)
					@ li,018 PSay cDesc
				Next nBegin
				li++
				cDescri1 := SC5->C5_OBSERV1
				@ li,018 PSay SubStr(cDescri1,1,60)
				For nBegin := 61 To Len(Trim(cDescri1)) Step 60
					li++
					cDesc:=Substr(cDescri1,nBegin,60)
					@ li,018 PSay cDesc
				Next nBegin
				Li++
				cDescri2 := SC5->C5_OBSERV2
				@ li,018 PSay SubStr(cDescri2,1,60)
				For nBegin := 61 To Len(Trim(cDescri2)) Step 60
					li++
					cDesc:=Substr(cDescri2,nBegin,60)
					@ li,018 PSay cDesc
				Next nBegin
				li++
				@ li,001 PSay "--------------------------------------------------------------------------------"
				li++
			EndIf

			//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
			//³ Carregar as medidas em array para impressao.                 ³
			//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
			dbSelectArea("SMX")
			dbSetOrder(2)
			dbSeek(xFilial()+cNum+cProduto)
			While !Eof() .And. M6_FILIAL+M6_NRREL+M6_PRODUTO == xFilial()+cNum+cProduto
				IF M6_ITEM == cItem
					AADD(aArrayPro,M6_ITEM+" - "+M6_PRODUTO)
					nCntArray++
					cCnt := StrZero(nCntArray,2)
					aArray&cCnt := {}
					While !Eof() .And. M6_FILIAL+M6_NRREL+M6_PRODUTO == xFilial()+cNum+cProduto
						If M6_ITEM == cItem
							AADD(aArray&cCnt,{ Str(M6_QUANT,9,2)," PECAS COM ",M6_COMPTO})
						EndIf
						dbSkip()
					End
				Else
					dbSkip()
				EndIF
			End
			cCnt := StrZero(nCntArray+1,2)
			aArray&cCnt := {}

			For nX := 1 TO Len(aArrayPro)
				If li > 58
					R820CabMed()
				EndIF
				@ li,009 PSay aArrayPro[nx]
				Li++
				Li++
				dbSelectArea("SMX")
				dbSetOrder(2)
				dbSeek( xFilial()+cNum+Subs(aArrayPro[nX],06,15) )
				While !Eof() .And. M6_FILIAL+M6_NRREL+M6_PRODUTO == xFilial()+cNum+Subs(aArrayPro[nX],06,15)
					If li > 58
						R820CabMed()
					EndIF
					IF M6_ITEM == Subs(aArrayPro[nX],1,2)
						@ li,002 PSay M6_QUANT
						@ li,013 PSay "PECAS COM"
						@ li,023 PSay M6_COMPTO
						@ li,035 PSay M6_OBS
						li ++
					EndIF
					dbSkip()
				End
				li++
			Next nX
			@ li,001 PSay "--------------------------------------------------------------------------------"
		EndIf
	Return Nil

	/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³R820CabMed ³ Autor ³ Jose Lucas           ³ Data ³ 25.01.94 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Imprime o cabecalho referentes as medidas do Pedido Filho. ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ R820CabMed(Void)                                           ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MatR820                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
	*/
	Static Function R820CabMed()
		Local cCabec1 := SM0->M0_NOME+STR0037	//"               RELACAO DE MEDIDAS             NRO :"

		Li := 0

		Li++
		@Li,00 PSay __PrtFatLine()
		Li++
		@Li,00 PSay cCabec1
		@Li,67 PSay (cAliasTop)->(C2_NUM+C2_ITEM+C2_SEQUEN+C2_ITEMGRD)
		Li++
		@Li,00 PSay __PrtFatLine()
		Li++
		Li++
	Return Nil

	/*/
	ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
	±±³Funcao    ³AjustaSX1 ³ Autor ³ Ricardo Berti         ³ Data ³21/02/2008³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
	±±³Descri‡…o ³Cria pergunta para o grupo			                      ³±±
	±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
	±±³ Uso      ³ MATR820                                                    ³±±
	±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
	±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
	ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
	/*/
	Static Function AjustaSX1()

		Local aHelpPor := {	'Opcao para a impressao do produto com  ','rastreabilidade por Lote ou Sub-Lote.  '}
		Local aHelpEng := {	'Option to print the product with       ','trackability by Lot or Sub-lot.        '}
		Local aHelpSpa := {	'Opcion para la impresion del producto  ','con trazabilidad por Lote o Sublote.   '}

		PutSx1("DLP013","12","Imprime Lote/S.Lote ?","¿Imprime Lote/Subl. ?","Print Lot/Sublot ?",;
			"mv_chc","N",1,0,2,"C","","","","","mv_par12","Sim","Si","Yes","" ,"Nao","No","No","","","","","","","","","",;
			aHelpPor,aHelpEng,aHelpSpa)

	Return
