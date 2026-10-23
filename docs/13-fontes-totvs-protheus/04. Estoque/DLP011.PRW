#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
#INCLUDE "TOPCONN.CH"

User Function DLP011()
/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ DLP011   ¦ Autor ¦ Diego Folchini        ¦ Data ¦ 07/03/07 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Relatorio de Estoque X Estoque de Seguranca                ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/

cPerg := "DLP011"
aRegistros := {}
AADD(aRegistros,{cPerg,"01","De  Produto               ?","","","mv_ch1","C",15,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","SB1","","","","",""})
AADD(aRegistros,{cPerg,"02","Ate Produto               ?","","","mv_ch2","C",15,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","SB1","","","","",""})

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
cDesc2         := "Estoque X Estoque de Seguranca"
cDesc3         := ""
cPict          := ""
lEnd         := .F.
lAbortPrint  := .F.
cString      :="SB1"
limite       :=132
tamanho      := "M"
nomeprog     := "DLP011" // Coloque aqui o nome do programa para impressao no cabecalho
nTipo        := 18
aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
nLastKey     := 0
cPerg        := "DLP011"
titulo       := "Extrato de Compra de Produtos"
nLin         := 0
nLIN2		 := 0
nLIN3		 := 0
pergunte(cPerg,.F.)

Cabec1       := "Produto           Descricao                                                             Estoque     Est. De Seg.   Qtde. Faltante"
//               999999999999999   999999999999999999999999999999999999999999999999999999999999   999,999,999.99   999,999,999.99   999,999,999.99
//               01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
//               0         1         2         3         4         5         6         7         8         9         10        11        120       132
Cabec2       := ""

cbtxt      := Space(10)
cbcont     := 00
CONTFL     := 01
m_pag      := 01
imprime      := .T.
wnrel      := "DLP011" // Coloque aqui o nome do arquivo usado para impressao em disco


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

sCodIni := mv_par01
sCodFin := mv_par02
Setprc(0,0)
iPag := 0
iLinha := 100         
                  
cQuery := "SELECT B1_COD,B1_DESC,B1_ESTSEG,B2_QATU "
cQuery += " FROM "
cQuery += " " + RetSqlName("SB2") + " SB2, "
cQuery += " " + RetSqlName("SB1") + " SB1 "
cQuery += "  WHERE B1_COD = B2_COD  AND B2_LOCAL = '01' AND B1_ESTSEG>B2_QATU "
cQuery += "  AND B2_COD >= '"+sCodIni+"'  AND B2_COD <= '"+sCodFin+"'"
cQuery += "  AND SB1.D_E_L_E_T_ = '' AND SB2.D_E_L_E_T_ = ''
cQuery += "ORDER BY B1_DESC "               


If ( Select ( "TRBSB2" ) <> 0 )
   dbSelectArea ( "TRBSB2" )
   dbCloseArea ()
End
TCQuery cQuery NEW ALIAS "TRBSB2"

dbSelectArea("TRBSB2")
DbGoTop()
SetRegua(Reccount())
While !Eof()
	nSalPrd := 0
	dbSelectArea("SB2")
	dbSetOrder(1)
	dbSeek(xFilial("SB2")+TRBSB2->B1_COD,.T.)// 01, Almox. Entrada Estoque
	While xFilial("SB2")+TRBSB2->B1_COD == SB2->B2_FILIAL + SB2->B2_COD  .And. !Eof()
		If SB2->B2_LOCAL == '01' .Or. SB2->B2_LOCAL == '99'
			nSalPrd += SB2->B2_QATU
		EndIf
		DbSkip()
	EndDo
	Incregua()
	fCabec2()
	@ iLinha, 000 PSAY TRBSB2->B1_COD
	@ iLinha, 018 PSAY Left(TRBSB2->B1_DESC,60)
	@ iLinha, 081 PSay nSalPrd                          PICTURE "@E 999,999,999.99"
	@ iLinha, 098 PSay TRBSB2->B1_ESTSEG     			PICTURE "@E 999,999,999.99"
	@ iLinha, 115 PSay (nSalPrd-TRBSB2->B1_ESTSEG)      PICTURE "@E 999,999,999.99"
	dbSelectArea("TRBSB2")
	DbSkip()
	
EndDo
fCabec2()
@ iLinha, 0 PSAY Repl(' ',132)
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
