#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
#INCLUDE "TOPCONN.CH"

User Function DLP005()
/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ DLP005   ¦ Autor ¦ Sérgio Alexandre      ¦ Data ¦ 18/06/07 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Relatorio de Pontualidade de Recebimento dos Pedidos       ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/

cPerg := "DLP005"
aRegistros := {}
AADD(aRegistros,{cPerg,"01","De  Fornecedor        ?","","","mv_ch1","C",06,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","SA2","","","","",""})
AADD(aRegistros,{cPerg,"02","De  Loja              ?","","","mv_ch2","C",02,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"03","Ate Fornecedor        ?","","","mv_ch3","C",06,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","SA2","","","","",""})
AADD(aRegistros,{cPerg,"04","Ate Loja              ?","","","mv_ch4","C",02,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"05","De  Entrega PC        ?","","","mv_ch5","D",08,0,0,"G","","mv_par05","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"06","Ate Entrega PC        ?","","","mv_ch6","D",08,0,0,"G","","mv_par06","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"07","De  Digitacao NF      ?","","","mv_ch7","D",08,0,0,"G","","mv_par07","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"08","Ate Digitacao NF      ?","","","mv_ch8","D",08,0,0,"G","","mv_par08","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"09","De  Produto           ?","","","mv_ch9","C",15,0,0,"G","","mv_par09","","","","","","","","","","","","","","","","","","","","","","","","","SA2","","","","",""})
AADD(aRegistros,{cPerg,"10","Ate Produto           ?","","","mv_chA","C",15,0,0,"G","","mv_par10","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})


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
cDesc2         := "pontualidade de recebimento dos pedidos de    "
cDesc3         := "venda."
cPict          := ""
lEnd         := .F.
lAbortPrint  := .F.
cString      :="SF2"
limite       :=132
tamanho      := "M"
nomeprog     := "DLP005" // Coloque aqui o nome do programa para impressao no cabecalho
nTipo        := 18
aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
nLastKey     := 0
cPerg        := "DLP005"
titulo       := "Pontualidade de Entrega Por Fornecedor"
nLin         := 0
nLIN2		 := 0
nLIN3		 := 0
pergunte(cPerg,.F.)

Cabec1       := "Pedido Nota Fiscal  Serie Produto  Descrição                                Dt Entr. PC Dt Dig. NF   DF     % "
//               999999 999999         99  99999999  9999999999999999999999999999999999999999 99/99/9999  99/99/9999  99  999.99
Cabec2       := ""

cbtxt      := Space(10)
cbcont     := 00
CONTFL     := 01
m_pag      := 01
imprime      := .T.
wnrel      := "DLP005" // Coloque aqui o nome do arquivo usado para impressao em disco


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

sCliIni := mv_par01
sLojaIn := mv_par02
sCliFin := mv_par03
sLojaFi := mv_par04
dEntIni := mv_par05
dEntFin := mv_par06
dDigIni := mv_par07
dDigFin := mv_par08
sProIni := mv_par09
sProFin := mv_par10
nQuaPPon := 0
nQuanpon:= 0
nTotal  := 0
Setprc(0,0)
iPag := 0
iLinha := 100         

cQuery := "SELECT "
cQuery += "  C7_DATPRF,A2_NOME,D1_FORNECE, D1_LOJA, "
cQuery += "  D1_PEDIDO, "
cQuery += "  D1_DOC, "
cQuery += "  D1_SERIE, "
cQuery += "  C7_PRODUTO, "
cQuery += "  C7_DESCRI, "
cQuery += "  C7_EMISSAO, "
cQuery += "  D1_DTDIGIT "
cQuery += "FROM "
cQuery += "  " + RetSqlName("SD1") + " SD1, "
cQuery += "  " + RetSqlName("SA2") + " SA2, "
cQuery += "  " + RetSqlName("SC7") + " SC7 "
cQuery += "WHERE "
cQuery += "  D1_FILIAL = '" + xFilial("SD1") + "' AND "
cQuery += "  C7_FILIAL = '" + xFilial("SC7") + "' AND "
cQuery += "  D1_FORNECE=A2_COD AND D1_LOJA=A2_LOJA AND "
cQuery += "  D1_PEDIDO = C7_NUM AND "
cQuery += "  D1_COD = C7_PRODUTO AND "
cQuery += "  D1_ITEMPC = C7_ITEM AND "
cQuery += "  D1_FORNECE >= '" + sCliIni + "' AND "
cQuery += "  D1_FORNECE <= '" + sCliFin + "' AND "
cQuery += "  D1_LOJA >= '" + sLojaIn + "' AND "
cQuery += "  D1_LOJA <= '" + sLojaFi + "' AND "
cQuery += "  D1_DTDIGIT >= '" + DToS(dDigIni) + "' AND "
cQuery += "  D1_DTDIGIT <= '" + DToS(dDigFin) + "' AND "
cQuery += "  C7_DATPRF  >= '" + DToS(dEntIni) + "' AND "
cQuery += "  C7_DATPRF  <= '" + DToS(dEntFin) + "' AND "
cQuery += "  D1_COD     >= '" + sProIni + "' AND "
cQuery += "  D1_COD     <= '" + sProFin + "' AND "
cQuery += "  D1_TES<>'035' AND D1_TES<>'083' AND "//Solictado Dennis
cQuery += "  SD1.D_E_L_E_T_ = '' AND "
cQuery += "  SC7.D_E_L_E_T_ = '' "
cQuery += "ORDER BY D1_FORNECE,D1_PEDIDO "               

/* cQuery := "SELECT D2_PEDIDO,D2_DOC,D2_SERIE,C6_PRODUTO,C6_DESCRI,C6_ENTREG,D2_EMISSAO "
cQuery += "FROM SD2010 SD2, SC6010 SC6 "
cQuery += "WHERE D2_PEDIDO=C6_NUM AND D2_COD=C6_PRODUTO AND D2_ITEM=C6_ITEM  "
cQuery += "AND D2_CLIENTE>='"+sCliIni+"' AND D2_CLIENTE<='"+sCliFin+"' AND D2_LOJA>='"+sLojaIn+"' AND D2_LOJA<='"+sLojaFi+"' "
cQuery += "AND D2_EMISSAO>='"+DTOS(dDatIni)+"' AND D2_EMISSAO <='"+DTOS(dDatFin)+"' AND C6_ENTREG>='"+DTOS(dEntIni)+"' AND C6_ENTREG<='"+DTOS(dEntFin)+"' "
cQuery += "AND SD2.D_E_L_E_T_='' AND SC6.D_E_L_E_T_='' "
cQuery += "ORDER BY D2_PEDIDO " */

If ( Select ( "TRBSD2" ) <> 0 )
   dbSelectArea ( "TRBSD2" )
   dbCloseArea ()
End
TCQuery cQuery NEW ALIAS "TRBSD2"

nTotal := 0 


dbSelectArea("TRBSD2")
DbGoTop()
SetRegua(Reccount())
While !Eof()
	sFornece := TRBSD2->D1_FORNECE+TRBSD2->D1_LOJA
	fCabec2()
	@ iLinha, 000 PSAY "FORNECEDOR :"+TRBSD2->D1_FORNECE+" - "+TRBSD2->D1_LOJA+ " : "+TRBSD2->A2_NOME
	sNomFor  := TRBSD2->A2_NOME
	nTotperc := 0
	nConperc := 0                        
	nTotPFor := 0
	nPercFor := 0
	While !Eof() .And. sFornece == TRBSD2->D1_FORNECE+TRBSD2->D1_LOJA
		Incregua()
		fCabec2()
		@ iLinha, 000 PSAY TRBSD2->D1_PEDIDO
		@ iLinha, 009 PSAY TRBSD2->D1_DOC
		@ iLinha, 022 PSAY TRBSD2->D1_SERIE
		@ iLinha, 026 PSAY TRBSD2->C7_PRODUTO
		@ iLinha, 036 PSAY TRBSD2->C7_DESCRI
		@ iLinha, 077 PSAY STOD(TRBSD2->C7_DATPRF)
		@ iLinha, 089 PSAY STOD(TRBSD2->D1_DTDIGIT)
		@ iLinha, 101 PSAY Transform(STOD(TRBSD2->D1_DTDIGIT)-STOD(TRBSD2->C7_DATPRF), '@E 999')
		if (STOD(TRBSD2->D1_DTDIGIT)-STOD(TRBSD2->C7_DATPRF))<=0
			@ iLinha, 108 PSAY '100.00%'
			nPercFor += 1
			nQuaPPon += 1
			nTotperc += 100
		else
			@ iLinha, 108 PSAY '  0.00%'
			nQuanpon := nQuanpon + 1
		endif
		nTotPFor += 1

		nConperc += 1
		nTotal   += 1
		dbSelectArea("TRBSD2")
		DbSkip()
	EndDo
	fCabec2()
	@ iLinha, 0 PSAY Repl('*',132)
	fCabec2()
	@ iLinha, 0 PSAY " TOTAL POR FORNECEDOR : " + sNomFor
	@ iLinha, 108 PSAY Transform((nPercFor/nTotPFor)*100, '@E 999.99')
	fCabec2()
	@ iLinha, 0 PSAY Repl('*',132)
EndDo

fCabec2()
@ iLinha, 0 PSAY Repl(' ',132)
fCabec2()
@ iLinha, 0 PSAY Repl('*',132)
fCabec2()               
@ iLinha, 0 PSAY "Prazo de recebimento atendido:     "+str(round((nQuaPPon/nTotal)*100,2))+"%"
fCabec2()
@ iLinha, 0 PSAY Repl('',132)
fCabec2()
@ iLinha, 0 PSAY "Prazo de recebimento não atendido: "+str(round((nQuanpon*100)/nTotal,2))+"%"
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