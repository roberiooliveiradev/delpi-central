#INCLUDE "MATR430.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "rwmake.CH"
#INCLUDE "TOPCONN.CH"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ MATR430  ³ Autor ³ Ricardo Berti         ³ Data ³07.07.2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Impressao da Planilha de Formacao de Precos                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ Generico                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
User Function DEL030()

Local oReport

MATR430R3()

Return


/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ MATR430R3³ Autor ³ Eveli Morasco         ³ Data ³ 30/03/93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Impressao da Planilha de Formacao de Precos                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ Generico                                                   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³         ATUALIZACOES SOFRIDAS DESDE A CONSTRU€AO INICIAL.             ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Programador ³ Data   ³ BOPS ³  Motivo da Alteracao                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Marcelo Pim.³25/11/97³ 7515A³ Incluir perg. p/ determinar qual nivel de³±±
±±³            ³        ³ 7515A³ detalhamento da estrutura.(mv_par06).    ³±±
±±³Marcelo Pim.³04/12/97³12092A³ Ajust.p/que a 2.moeda nao imp. se a moeda³±±
±±³            ³        ³12092A³ selecionada for moeda 1.                 ³±±
±±³Marcelo Pim.³05/12/97³ 7514A³ Incluir perg. p/ informar a qtde.Basica. ³±±
±±³Bruno Sobies³23.12.98³melhor³ Aumento do tamanho das colunas de descri-³±±
±±³            ³        ³      ³ cao, valor unit e total, e das casas do %³±±
±±³CesarValadao³30/03/99³XXXXXX³ Manutencao na SetPrint()                 ³±±
±±³Fernando J. ³27/05/99³21327A³ Arredondar o Valor Unit rio com o n£mero ³±±
±±³            ³        ³      ³ de casas decimais do Campo Original.     ³±±
±±³CesarValadao³22/07/99³22152A³ Passar mv_par07 (QtdBas) p/ Mc010Forma().³±±
±±³CesarValadao³30/08/99³21448A³ Fazer a inversao do calculo do Valor     ³±±
±±³            ³        ³      ³ Unitario com o maximo de casas decimais. ³±±
±±³CesarValadao³08/10/99³XXXXXX³ Considerar Pergunte() do MTC010.         ³±±
±±³            ³        ³      ³ mv_par02 - Arredonda ou Trunca.          ³±±
±±³Iuspa       ³24/08/00³  5742³ mv_par08 - Considera componente qtd. neg.³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function MATR430R3()
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Define Variaveis                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
LOCAL Tamanho
LOCAL cDesc1   := STR0001	//"Emite um relatorio com os calculos da planilha selecionada pa-"
LOCAL cDesc2   := STR0002	//"ra cada produto. Os valores calculados sao os mesmos  referen-"
LOCAL cDesc3   := STR0003	//"tes as formulas da planilha."
LOCAL cString  := "SB1"
LOCAL nI       := 0

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Estas variaveis foram deixadas em separado para lembrar que  ³
//³ elas devem ser definidas novamente na funcao MR430Impr()     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
LOCAL titulo   := OemToAnsi(STR0004)	//"Planilha de Formacao de Precos"
LOCAL wnrel := "MATR430"

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Variaveis tipo Private padrao de todos os relatorios         ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
PRIVATE aReturn := { OemToAnsi(STR0005), 1,OemToAnsi(STR0006), 2, 2, 1, "",1 }		//"Zebrado"###"Administracao"
PRIVATE nLastKey := 0 ,cPerg := "MTR430",aPar:=Array(20),aParC010:=Array(20)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica as perguntas selecionadas                           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Variaveis utilizadas para parametros                         ³
//³ mv_par01     // Produto inicial                              ³
//³ mv_par02     // Produto final                                ³
//³ mv_par03     // Nome da planilha utilizada                   ³
//³ mv_par04     // Imprime estrutura : Sim / Nao                ³
//³ mv_par05     // Moeda Secundaria  : 1 2 3 4 5                ³
//³ mv_par06     // Nivel de detalhamento da estrutura           ³
//³ mv_par07     // Qual a Quantidade Basica                     ³
//³ mv_par08     // Considera Qtde Neg na estrutura: Sim/Nao     ³
//³ mv_par09     // Considera Estrutura / Pre Estrutura          ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
AjustaSx1()
pergunte(cPerg,.F.)
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Forca utilizacao da estrutura caso nao tenha SGG               ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If Select("SGG") == 0
	mv_par09:=1
EndIf
//Salvar variaveis existentes
For ni := 1 to 20
	aPar[ni] := &("mv_par"+StrZero(ni,2))
Next ni

Tamanho := IIF(apar[05]==1,"M","G")

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Envia controle para a funcao SETPRINT                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
wnrel:=SetPrint(cString,wnrel,cPerg,@titulo,cDesc1,cDesc2,cDesc3,.F.,"",,Tamanho)

If nLastKey = 27
	Set Filter to
	Return
Endif

SetDefault(aReturn,cString)

If nLastKey = 27
	Set Filter to
	Return
Endif

//Salvar variaveis existentes
For ni := 1 to 20
	aPar[ni] := &("mv_par"+StrZero(ni,2))
Next ni

RptStatus({|lEnd| C430Imp(@lEnd,wnRel,cString,titulo,Tamanho)},titulo)

Return NIL

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ C430IMP  ³ Autor ³ Rodrigo de A. Sartorio³ Data ³ 14.12.95 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Chamada do Relatorio                                       ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR430                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function C430Imp(lEnd,WnRel,cString,titulo,Tamanho)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Variaveis locais exclusivas deste programa                   ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
LOCAL cRodaTxt := ""
LOCAL nCntImpr := 0,nReg
LOCAL aArray   := {} ,cCondFiltr,lRet
LOCAL nI       := 0
LOCAL cProdFim :=""
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Contadores de linha e pagina                                 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
PRIVATE li := 80 ,m_pag := 1,cProg:="R430"

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Variaveis privadas exclusivas deste programa                 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Custo a ser considerado nos calculos                           ³
//³ 1 = STANDARD    2 = MEDIO     3 = MOEDA2     4 = MOEDA3        ³
//³ 5 = MOEDA4      6 = MOEDA5    7 = ULTPRECO   8 = PLANILHA      ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
PRIVATE nQualCusto := 1

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Vetor declarado para inversao do calculo do Valor Unitario   ³
//³ Utilizado no MATC010X -> M010Forma e CalcTot                 ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
PRIVATE aAuxCusto

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Nome do arquivo que contem a memoria de calculo desta planilha ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
PRIVATE cArqMemo := "STANDARD"

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Direcao do calculo .T. para baixo .F. para cima                ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
PRIVATE lDirecao := .T.

PRIVATE lConsNeg := apar[08] = 1     // Esta variavel será usada na função MC010FORMA
sCodIni  := MV_PAR01
sCodFin  := MV_PAR02
dPerIni  := MV_PAR10
dPerFin  := MV_PAR11
sTipoRel := MV_PAR12
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inclui pergunta no SX1                                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
MTC010SX1()
PERGUNTE("MTC010", .F.)
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Forca utilizacao da estrutura caso nao tenha SGG               ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If Select("SGG") == 0
	mv_par09:=1
EndIf
//Salvar variaveis existentes
For ni := 1 to 20
	aParC010[ni] := &("mv_par"+StrZero(ni,2))
Next ni
//Forca mesmo valor do relatorio na pergunta 09
mv_par09     := aPar[09]
aParC010[09] := aPar[09]

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Este procedimento foi necessario para transformar o filtro sele- ³
//³ cionado pelo usuario em uma condicao de IF ,isto porque o filtro ³
//³ age em todo o arquivo e eu preciso dele apenas no While principal³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
cCondFiltr := aReturn[7]
If Empty(cCondFiltr)
	cCondFiltr := ".T."
EndIf

DbSelectArea("SB1")
Set Filter to

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inicializa o nome padrao da planilha com o nome selecionado pelo ³
//³ usuario                                                          ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
cArqMemo := apar[03]

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inicializa os codigos de caracter Comprimido/Normal da impressora ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nTipo  := IIF(aReturn[4]==1,15,18)


dbSelectArea("SB1")
SetRegua(LastRec())

Set SoftSeek On
dbSeek(xFilial()+apar[01])
Set SoftSeek Off
lRet:=MR430Plan(.T.,aPar)
IF !lRet
	SET DEVICE TO SCREEN
	Return Nil
ENDIF
	Tamanho  := "M"
	titulo   := "CUSTO PRODUTO"
	nTipo    := 15
	wnrel    := "MATR430"
	Cabec1       := "Produto           Descricao                                                         Qtd Vendida          Cut. MP         Custo MO"
	//               999999999999999   999999999999999999999999999999999999999999999999999999999999   999,999,999.99   999,999,999.99   999,999,999.99
	//               01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
	//               0         1         2         3         4         5         6         7         8         9         10        11        120       132
	Cabec2       := ""
	Limite   := 132
	
	iPag := 0
	iLinha := 100
	
	cQuery := "SELECT D2_COD,B1_DESC,Str(SUM(D2_QUANT),10,2) D2_QUANT "
	cQuery += "FROM " + RetSqlName("SD2") + " SD2, " + RetSqlName("SB1") + " SB1 "
	cQuery += "WHERE B1_COD = D2_COD "
	cQuery += "AND D2_COD >= '"+Alltrim(sCodIni)+"' AND D2_COD <= '"+Alltrim(sCodFin)+"' "
	cQuery += "AND D2_EMISSAO >= '"+dTos(dPerIni)+"' AND D2_EMISSAO <= '"+dTos(dPerFin)+"' "
	cQuery += "AND SD2.D_E_L_E_T_='' AND SB1.D_E_L_E_T_='' "
	cQuery += "GROUP BY D2_COD,B1_DESC "
	cQuery += "ORDER BY D2_COD,B1_DESC "
	
	
	If ( Select ( "TRBSD2" ) <> 0 )
		dbSelectArea ( "TRBSD2" )
		dbCloseArea ()
	End
	TCQuery cQuery NEW ALIAS "TRBSD2"
	
	dbSelectArea("TRBSD2")
	DbGoTop()
	SetRegua(Reccount())
	While !Eof()
		Incregua()
		DbSelectArea("SB1")
		DbSetOrder(1)
		DbSeek(xFilial("SB1")+TRBSD2->D2_COD)
		
		nReg := Recno()
		//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
		//³ Considera filtro escolhido                                   ³
		//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
		aArray := MC010Forma(cString,nReg,99,apar[07],,.F.)
		aArray := aArray[2]
		fCabec2()          
		iReg := 0 
		For nX := 1 To Len(aArray)           
		    If Alltrim(Left(aArray[nX][03],20)) == "TOTAL DE MAO DE OBRA"
		       iReg := nx
		       nx := 100000
		    EndIF   
        Next Nx

		@ iLinha, 000 PSAY aArray[1][04]
		@ iLinha, 018 PSAY Left(aArray[1][03],60)
		@ iLinha, 081 PSay Val(TRBSD2->D2_QUANT)        PICTURE "@E 999,999,999.99"
		@ iLinha, 098 PSay aArray[iReg][06]             PICTURE "@E 999,999,999.99"
		@ iLinha, 115 PSay (aArray[iReg][06] * Val(TRBSD2->D2_QUANT))    			PICTURE "@E 999,999,999.99"
		dbSelectArea("TRBSD2")
		dbSkip()
	End
	

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Devolve a condicao original do arquivo principal             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
dbSelectArea(cString)
Set Filter To
Set Order To 1

If aReturn[5] = 1
	Set Printer To
	dbCommitAll()
	OurSpool(wnrel)
Endif

MS_FLUSH()
Return


/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³MR430Impr ³ Autor ³ Eveli Morasco         ³ Data ³ 30/03/93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Imprime os dados ja' calculados                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ MR430Impr(ExpC1,ExpA1,ExpN1)                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ ExpC1 = Titulo do custo utilizado                          ³±±
±±³          ³ ExpA1 = Array com os dados ja' calculados                  ³±±
±±³          ³ ExpN1 = Numero do elemento inicial a imprimir              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR430                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function MR430Impr(cCusto,aArray,nPosForm)
LOCAL nX
LOCAL nCotacao,nValUnit,nValUnit2
LOCAL cPicQuant:=PesqPictQt("G1_QUANT",13)
LOCAL cPicUnit :=PesqPict("SB1","B1_CUSTD",18)
LOCAL cPicTot	:=PesqPict("SB1","B1_CUSTD",19)
LOCAL cMoeda1,cMoeda2
Local nDecimal :=0
LOCAL nI       :=0

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Estas variaveis foram deixadas em separado para lembrar que  ³
//³ elas foram definidas no programa principal MATR430 e estao   ³
//³ sendo redefinidas para nao ter que defini-las como PRIVATE.  ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
LOCAL Tamanho  := IIF(apar[05]==1,"M","G")
LOCAL titulo   := STR0004		//"Planilha de Formacao de Precos"
LOCAL nTipo    := 0
LOCAL wnrel := "MATR430"
LOCAL cOldAlias,nOrder,nRecno
LOCAL cabec1,cabec2
LOCAL Limite   := IIF(apar[05]==1,132,220)

cCusto := If(cCusto=Nil,'',AllTrim(Upper(cCusto)))
If cCusto == 'ULT PRECO'
	nDecimal := TamSX3('B1_UPRC')[2]
ElseIf 'MEDIO' $ cCusto
	nDecimal := TamSX3('B2_CM1')[2]
Else
	nDecimal := TamSX3('B1_CUSTD')[2]
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ De acordo com o custo da planilha lida monta a cotacao de    ³
//³ conversao e a variavel cMoeda1 usada no cabecalho.           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If Str(nQualCusto,1) $ "3/4/5/6"
	nCotacao:=ConvMoeda(dDataBase,,1,Str(nQualCusto-1,1))
	cMoeda1:=GetMV("MV_MOEDA"+Str(nQualCusto-1,1,0))
Else
	nCotacao:=1
	cMoeda1:=GetMV("MV_MOEDA1")
EndIf
cMoeda1:=PADC(Alltrim(cMoeda1),35)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ De acordo com o parametro da segunda moeda (mv_par05) monta  ³
//³ a variavel cMoeda2 usada no cabecalho.                       ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
cMoeda2:=PADC(Alltrim(GetMV("MV_MOEDA"+Str(apar[05],1,0))),38)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Monta os Cabecalhos de acordo com a moeda                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
If apar[05] == 1
	Cabec1 := STR0008+cMoeda1+STR0009				//"CEL. NIVEL  CODIGO          DESCRICAO                      UM    QUANTIDADE "###"% PART"
	Cabec2 := STR0011										//"                                                                              VALOR UNITARIO       VALOR TOTAL"
Else
	Cabec1 := STR0008+cMoeda1+cMoeda2+STR0009		//"CEL. NIVEL  CODIGO          DESCRICAO                      UM    QUANTIDADE "###"% PART"
//	Cabec1 := STR0008+cMoeda1+cMoeda2+STR0009		//"CEL. NIVEL  CODIGO          DESCRICAO                      UM    QUANTIDADE "###"% PART"
	Cabec2 := STR0010										//"                                                                              VALOR UNITARIO       VALOR TOTAL   VALOR UNITARIO       VALOR TOTAL"
Endif
Cabec1 := "CEL. NIVEL  CODIGO          DESCRICAO                               ULT. CUSTO UM    QUANTIDADE % PART"
//
//         01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
//         0         1        2          3         4         5         6         7         8         9
Cabec2 := STR0011										//"                                                                              VALOR UNITARIO       VALOR TOTAL"

********                                           9999 999999 123456789012345 123456789012345678901234567890 12 9999999999.99 9.999.999.999,99 99.999.999.999,99 9.999.999.999,99 99.999.999.999,99 999.99
********   														0         1         2         3         4         5         6         7         8         9        10        11        12        13        14        15
********   														01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Inicializa os codigos de caracter Comprimido/Normal da impressora ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
nTipo  := IIF(aReturn[4]==1,15,18)

For nX := 1 To Len(aArray)
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Verifica o nivel da estrutura para ser impresso ou nao  ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	If apar[04] == 1
		If Val(apar[06]) != 0
			If Val(aArray[nX,2]) > Val(apar[06])
				Loop
			Endif
		Endif
	Endif
	
	If If( (Len(aArray[ nX ])==12),aArray[nX,12],.T. )
		If li > 60
			// Restaura variaveis existentes
			For ni := 1 to 20
				&("mv_par"+StrZero(ni,2)) := aPar[ni]
			Next ni
			Cabec(titulo,cabec1,cabec2,wnrel,Tamanho,nTipo)
			// Restaura variaveis existentes
			For ni := 1 to 20
				&("mv_par"+StrZero(ni,2)) := aParc010[ni]
			Next ni
		EndIf
		If nX < nPosForm-1
			If mv_par02 == 1
				nValUnit := Round(aAuxCusto[nX]/aArray[nX][05], nDecimal)
			Else
				nValUnit := NoRound(aAuxCusto[nX]/aArray[nX][05], nDecimal)
			EndIf
			nValUnit2:= Round(ConvMoeda(dDataBase,,nValUnit/nCotacao,Str(apar[05],1)), nDecimal)
		EndIf
		//		FOR X := 1 TO LEN(aArray)
		//7 D1_FILIAL+D1_COD+D1_LOCAL+DTOS(D1_DTDIGIT)+D1_NUMSEQ
		@ li,000 PSay aArray[nX][01] Picture "9999"
		@ li,005 PSay aArray[nX][02]
		@ li,012 PSay aArray[nX][04]
		@ li,028 PSay Left(aArray[nX][03],30)
		If aArray[nX][04] != Replicate("-",15)
			If nX < nPosForm-1
				//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
				//³ Posiciona na UM correta do produto ³
				//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
				cOldAlias:=Alias()
				
				dbSelectArea("SB1")
				nOrder:=IndexOrd()
				nRecno:=Recno()
				dbSetOrder(1)
				dbSeek(xFilial()+aArray[nX][04])
				
				dUltCst := ctod('  /  /  ')
				nUltFrt := 0                    
				nQuantSD1  := 0 
				dbSelectArea("SD1")
				dbSetOrder(7)
				dbSeek(xFilial("SD1")+SB1->B1_COD+SB1->B1_LOCPAD+'20100101',.T.)
				DbSkip(-1)                                     
				dDtDigit := SD1->D1_DTDIGIT                     
				While xFilial("SD1")+SB1->B1_COD+SB1->B1_LOCPAD == SD1->D1_FILIAL+SD1->D1_COD+SD1->D1_LOCAL .And. ;
  					dDtDigit == SD1->D1_DTDIGIT
					If Alltrim(SD1->D1_ORIGLAN) == 'FR' .And. nUltFrt==0
						nUltFrt := SD1->D1_CUSTO
					EndIf
					If Empty(dUltCst)                           
						dUltCst := SD1->D1_DTDIGIT 
					EndIf                                              
					If nQuantSD1 == 0 
						nQuantSD1  := SD1->D1_QUANT
					EndIf	
					DbSkip(-1)
				Enddo                                                             
				@ li,068 PSay dUltCst
				dbSelectArea("SB1")
				@ li,079 PSay SB1->B1_UM
				dbSetOrder(nOrder)
				dbGoTo(nRecno)
				dbSelectArea(cOldAlias)
				@ li,085 PSay  Transform(aArray[nX][05],"@E 9,999.99999")
				nValUnit := nValUnit + (nUltFrt/nQuantSD1)
				@ li,099 PSay nValUnit Picture "@E 999,999.99999"
			EndIf
			@ li,112 PSay aArray[nX][06] Picture "@E 99,999.99999"
			If apar[05] == 1
				@ li,125 PSay aArray[nX][07] Picture "999.999"
			Else
				If nX < nPosForm-1
					@ li,125 PSay nValUnit2 Picture cPicUnit
				EndIf
				@ li,143 PSay ConvMoeda(dDataBase,,(aArray[nX][06]/nCotacao),Str(apar[05],1)) Picture cPictot
				@ li,163 PSay aArray[nX][07] Picture "999.999"
			Endif
		EndIf
		li++
		If nX == 1 .And. apar[04] == 2
			nX += (nPosForm-3)
		EndIf
	EndIf
Next nX
@ li,000 PSay Replicate("-",Limite)
li += 2

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³MR430Plan ³ Autor ³ Eveli Morasco         ³ Data ³ 30/03/93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Verifica se a Planilha escolhida existe                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATR430                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function MR430Plan(lGravado,aPar)
Local cArq := ""
Local lRet := .T.
DEFAULT lGravado:=.F.
cArq:=AllTrim(If(lGravado,apar[03],&(ReadVar())))+".PDV"
If !File(cArq)
	Help(" ",1,"MR430NOPLA")
	lRet := .F.
EndIf
Return (lRet)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ AjustaSX1    ³Autor ³ Ricardo Berti        ³Data³07/07/2006³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Ajusta perguntas do SX1                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function AjustaSX1()

Local aHelpPor	:= {}
Local aHelpEng	:= {}
Local aHelpSpa	:= {}

Aadd( aHelpPor, "Identifica se a montagem da composicao  " )
Aadd( aHelpPor, "do produto deve ser feita pela estrutura" )
Aadd( aHelpPor, " ou pela pre-estrutura.                 " )

Aadd( aHelpEng, "Identifies if the product composition   " )
Aadd( aHelpEng, "preparation must be made by the         " )
Aadd( aHelpEng, "structure or by the pre-structure.      " )

Aadd( aHelpSpa, "Identifica si el montaje de composicion " )
Aadd( aHelpSpa, "del producto debe ser hecha por la      " )
Aadd( aHelpSpa, "estructura o por la pre-estructura.     " )

PutSX1("MTR430","09","Mostra ?","¿Muestra?","Show?","mv_ch9","N",1,0,1,"C","","","","N","mv_par09",;
"Estrutura","Estructura","Structure","","Pre-Estrutura","Estructura Previa","Previous Structure","","","","","","","","","")

PutSX1("MTR430","10","De Periodo ?","","","mv_ch9","D",8,0,1,"G","","","","","mv_par09",;
"","","","","","","","","","","","","","","","")
PutSX1("MTR430","11","Ate Periodo ?","","","mv_ch10","D",8,0,1,"G","","","","","mv_par10",;
"","","","","","","","","","","","","","","","")
PutSX1("MTR430","12","Rel Custo MP. MO ?","","","mv_ch11","N",1,0,1,"C","","","","N","mv_par11",;
"Nao","","","","Sim","","","","","","","","","","","")

PutSX1Help("P.MTR43009.",aHelpPor,aHelpEng,aHelpSpa)

Return


// Substituido pelo assistente de conversao do AP5 IDE em 02/05/01 ==> Function Cabec1
Static Function fCabec2()
*************************
iLinha := iLinha + 1
	Tamanho  := "M"
	titulo   := "CUSTO PRODUTO"
	nTipo    := 15
	wnrel    := "MATR430"
	Cabec1       := "Produto           Descricao                                                         Qtd Vendida          Cut. MP         Custo MO"
	//               999999999999999   999999999999999999999999999999999999999999999999999999999999   999,999,999.99   999,999,999.99   999,999,999.99
	//               01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
	//               0         1         2         3         4         5         6         7         8         9         10        11        120       132
	Cabec2       := ""
	Limite   := 132

If iLinha > 60
   Cabec(Titulo,Cabec1,Cabec2,WnRel,Tamanho,nTipo)
   iLinha := 9
Endif
Return
