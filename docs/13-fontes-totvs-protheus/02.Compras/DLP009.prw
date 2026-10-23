#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
#INCLUDE "TOPCONN.CH"

User Function DLP009()
/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ DLP009   ¦ Autor ¦ Diego Folchini        ¦ Data ¦ 07/03/07 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Relatorio de Pontualidade de Entrega dos Pedidos           ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/

cPerg := "DLP009"
aRegistros := {}
AADD(aRegistros,{cPerg,"01","De  Entrega           ?","","","mv_ch1","D",08,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"02","Ate Entrega           ?","","","mv_ch2","D",08,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})

dbSelectArea("SX1")
dbSeek(cPerg)
If !Found()
	dbSeek(cPerg)
	While SX1->X1_GRUPO==cPerg.and.!Eof()
		Reclock("SX1",.f.)
		dbDelete()
		MsUnlock("SX1")
		dbSkip()
	End
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

aOrd := {}
CbTxt        := ""
cDesc1         := "Este programa tem como objetivo imprimir a    "
cDesc2         := "pontualidade de entrega das Ordens de Producao."
cDesc3         := ""
cPict          := ""
lEnd         := .F.
lAbortPrint  := .F.
cString      :="SC2"
limite       :=132
tamanho      := "M"
nomeprog     := "DLP009" // Coloque aqui o nome do programa para impressao no cabecalho
nTipo        := 18
aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
nLastKey     := 0
cPerg        := "DLP009"
titulo       := "Pontualidade de Entrega das Ordens de Producao"
nLin         := 0
nLIN2		 := 0
nLIN3		 := 0
pergunte(cPerg,.F.)

Cabec1       := "OP           Produto         Descricao                                   Qtd Prod. Dt. Prevista  Dt Entrega    %"
//               99999999999  999999999999999 9999999999999999999999999999999999999999  999,999.99      99/99/99    99/99/99  999
//               0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
//               0         1         2         3         4         5         6         7         8         9         10        11        12
Cabec2       := ""

cbtxt      := Space(10)
cbcont     := 00
CONTFL     := 01
m_pag      := 01
imprime      := .T.
wnrel      := "DLP009" // Coloque aqui o nome do arquivo usado para impressao em disco


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Monta a interface padrao com o usuario...                           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

wnrel := SetPrint(cString,NomeProg,cPerg,@titulo,cDesc1,cDesc2,cDesc3,.F.,aOrd,.T.,Tamanho,,.F.)

If nLastKey == 27
	Return
Endif

SetDefault(aReturn,cString)

If nLastKey == 27
	Return
Endif

nTipo := If(aReturn[4]==1,15,18)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Processamento. RPTSTATUS monta janela com a regua de processamento. ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

RptStatus({|| RunReport(Cabec1,Cabec2,Titulo,nLin) },Titulo)
Return

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºFun‡„o    ³RUNREPORT º Autor ³ AP5 IDE            º Data ³  09/01/01   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescri‡„o ³ Funcao auxiliar chamada pela RPTSTATUS. A funcao RPTSTATUS º±±
±±º          ³ monta a janela com a regua de processamento.               º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Programa principal                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

Static Function RunReport(Cabec1,Cabec2,Titulo,nLin)

dEntIni := mv_par01
dEntFin := mv_par02
Setprc(0,0)
iPag := 0
iLinha := 100

cQuery := "SELECT C2_NUM,C2_ITEM,C2_SEQUEN,B1_COD,B1_DESC,C2_QUANT,C2_DATPRF,C2_DATRF "
cQuery += "FROM " + RetSqlName("SC2") + " SC2, " + RetSqlName("SB1") + " SB1 "
cQuery += "WHERE C2_PRODUTO=B1_COD "
cQuery += "AND C2_DATPRF>='"+DTOS(dEntIni)+"' AND C2_DATPRF <='"+DTOS(dEntFin)+"' "
cQuery += "AND C2_DATRF <> '' AND SC2.D_E_L_E_T_='' AND SB1.D_E_L_E_T_='' "
cQuery += "ORDER BY C2_DATPRF "

If ( Select ( "TRBSC2" ) <> 0 )
	dbSelectArea ( "TRBSC2" )
	dbCloseArea ()
End
TCQuery cQuery NEW ALIAS "TRBSC2"

nPonSim := 0
nPonNao := 0
nTotal  := 0

dbSelectArea("TRBSC2")
DbGoTop()
SetRegua(Reccount())
While !Eof()
	Incregua()
	fCabec2()
Cabec1       := "OP           Produto         Descricao                                   Qtd Prod. Dt. Prevista  Dt Entrega    %"
//               99999999999  999999999999999 9999999999999999999999999999999999999999  999,999.99      99/99/99    99/99/99  999
//               0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
//               0         1         2         3         4         5         6         7         8         9         10        11        12

	@ iLinha, 000 PSAY TRBSC2->C2_NUM+TRBSC2->C2_ITEM+TRBSC2->C2_SEQUEN
	@ iLinha, 013 PSAY TRBSC2->B1_COD
	@ iLinha, 029 PSAY Left(TRBSC2->B1_DESC,40)
	@ iLinha, 071 PSAY TRBSC2->C2_QUANT PICTURE "@E 9999,999.99"
	@ iLinha, 087 PSAY stod(TRBSC2->C2_DATPRF)
	@ iLinha, 099 PSAY stod(TRBSC2->C2_DATRF)
	if (STOD(TRBSC2->C2_DATPRF)>=STOD(TRBSC2->C2_DATRF))
		@ iLinha, 109 PSAY '100%'
		nPonSim += 1
	else
		@ iLinha, 109 PSAY '  0%'
		nPonNao -= 1
	endif
	
	nTotal := nTotal + 1
	DbSelectArea("TRBSC2")
	DbSkip()
EndDo
fCabec2()
@ iLinha, 0 PSAY Repl(' ',132)
fCabec2()
@ iLinha, 0 PSAY Repl('*',132)
fCabec2()
@ iLinha, 0 PSAY "Prazo de entrega atendido:     "+Str(Round((nPonSim*100)/nTotal,2))+"%"
fCabec2()
@ iLinha, 0 PSAY Repl('',132)
fCabec2()
@ iLinha, 0 PSAY "Prazo de entrega não atendido: "+Str(Round((nPonNao*100)/nTotal,2))+"%"
fCabec2()
@ iLinha, 0 PSAY Repl('*',132)
If aReturn[5]==1
	dbCommitAll()
	SET PRINTER TO
	OurSpool(wnrel)
Endif

MS_FLUSH()

Return

// Substituido pelo assistente de conversao do AP5 IDE em 02/05/01 ==> Function Cabec1
Static Function fCabec2()
*************************
iLinha := iLinha + 1
If iLinha > 60
	Cabec(Titulo,Cabec1,Cabec2,WnRel,Tamanho,nTipo)
	iLinha := 8
Endif
Return
