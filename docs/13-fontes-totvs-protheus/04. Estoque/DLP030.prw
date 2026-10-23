#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
#INCLUDE "TOPCONN.CH"

User Function DLP030()
/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ DLP030   ¦ Autor ¦ Diego Folchini        ¦ Data ¦ 07/03/07 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Relatorio de Estoque X Estoque de Seguranca                ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/

cPerg := "DLP030"
aRegistros := {}
AADD(aRegistros,{cPerg,"01","De  Centro De Custos      ?","","","mv_ch1","C",15,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","CTT","","","","",""})
AADD(aRegistros,{cPerg,"02","Ate Centro De Custos      ?","","","mv_ch2","C",15,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","CTT","","","","",""})
AADD(aRegistros,{cPerg,"03","De  Data Emissao          ?","","","mv_ch3","D",08,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"04","Ate Data Emissao          ?","","","mv_ch4","D",08,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"05","Tipo                      ?","","","mv_ch5","N",01,0,0,"C","","mv_par05","Sintetico","","","","","Analitico","","","","","","","","","","","","","","","","","","","","","","","",""})

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
cDesc1       := "Este programa tem como objetivo imprimir a    "
cDesc2       := "Entrada X Centro De Custos"
cDesc3       := ""
cPict        := ""
lEnd         := .F.
lAbortPrint  := .F.
cString      :="SB1"
limite       :=132
tamanho      := "M"
nomeprog     := "DLP030" // Coloque aqui o nome do programa para impressao no cabecalho
nTipo        := 18
aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
nLastKey     := 0
cPerg        := "DLP030"
titulo       := "Extrato de Compra de Produtos"
nLin         := 0
nLIN2		 := 0
nLIN3		 := 0
pergunte(cPerg,.F.)

Cabec1       := "Emissao   Produto         Descricao                                          UM Quantidade Valor Unit      Total"
//               99/99/99  999999999999999 99999999999999999999999999999999999999999999999999 99 999,999.99 999,999.99 999,999.99
//               01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
//               0         1         2         3         4         5         6         7         8         9         10        11        120       132
	
Cabec2       := ""

cbtxt      := Space(10)
cbcont     := 00
CONTFL     := 01
m_pag      := 01
imprime      := .T.
wnrel      := "DLP030" // Coloque aqui o nome do arquivo usado para impressao em disco


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

sCCIni  := mv_par01
sCCFin  := mv_par02
dEmiIni := mv_par03
dEmiFin := mv_par04
sTipo   := mv_par05

Setprc(0,0)
iPag := 0
iLinha := 100                    

aEstru  := array(05,4)
aEstru[01] := { "TR_CC"     ,"C",09,0 }
aEstru[02] := { "TR_PRODUTO","C",15,0 }
aEstru[03] := { "TR_QUANT"  ,"N",14,2 }
aEstru[04] := { "TR_VALUNIT","N",14,2 }
aEstru[05] := { "TR_TOTAL"  ,"N",14,2 }

If ( Select ( "TRB" ) <> 0 )
   dbSelectArea ( "TRB" )
   dbCloseArea ()
End
cNomeArq := CriaTrab ( aEstru )
dbUseArea ( .T.,, cNomeArq, "TRB", NIL, .F. )
dbSelectArea("TRB") 
cNomeArq := CriaTrab(NIL,.F.)
IndRegua("TRB",cNomeArq,"TR_CC+TR_PRODUTO",,,"Selecionando registros...")

cQuery := "SELECT D1_COD,D1_EMISSAO,D1_CC,Str(D1_QUANT,10,2) D1_QUANT, Str(D1_VUNIT,10,2) D1_VUNIT "
cQuery += " FROM " + RetSqlName("SD1") + " SD1 "
cQuery += "  WHERE D1_CC >= '"+sCCIni+"'  AND D1_CC <= '"+sCCFin+"' "
cQuery += "  AND   D1_EMISSAO >= '"+dtos(dEmiIni)+"'  AND D1_EMISSAO <= '"+dtos(dEmiFin)+"' "
cQuery += "  AND SD1.D_E_L_E_T_ = '' "
cQuery += "  ORDER BY D1_COD "
If ( Select ( "TRBSD1" ) <> 0 )
	dbSelectArea ( "TRBSD1" )
	dbCloseArea ()
End
TCQuery cQuery NEW ALIAS "TRBSD1"


cQuery := "SELECT D3_COD,D3_EMISSAO,D3_CC,Str(D3_QUANT,10,2) D3_QUANT, Str(D3_VUNIT,10,2) D3_VUNIT "
cQuery += " FROM " + RetSqlName("SD3") + " SD3 "
cQuery += "  WHERE D3_CC >= '"+sCCIni+"'  AND D3_CC <= '"+sCCFin+"' "
cQuery += "  AND   D3_EMISSAO >= '"+dtos(dEmiIni)+"'  AND D3_EMISSAO <= '"+dtos(dEmiFin)+"' "
cQuery += "  AND SD3.D_E_L_E_T_ = '' "
cQuery += "  ORDER BY D3_COD "
If ( Select ( "TRBSD3" ) <> 0 )
	dbSelectArea ( "TRBSD3" )
	dbCloseArea ()
End
TCQuery cQuery NEW ALIAS "TRBSD3"

dbSelectArea("TRBSD1")
DbGoTop()
SetRegua(Reccount())
While !Eof()
	Incregua()       
	GravTRB(TRBSD1->D1_CC,TRBSD1->D1_COD,TRBSD1->D1_QUANT,TRBSD1->D1_VUNIT)
    dbSelectArea("CTT")
    DbSetOrder(1)                                                         
    sCenCus := TRBSD1->D1_CC
    DbSeek(xFilial("CTT")+sCenCus,.T.)
    While !Eof() .And. sCenCus == CTT->CTT_CUSTO  .And. !Empty(CTT->CTT_CCSUP)
	    dbSelectArea("CTT")
    	DbSetOrder(1)
	    iF (DbSeek(xFilial("CTT")+CTT->CTT_CCSUP+space(15)))
			GravTRB(TRBSD1->D1_CC,TRBSD1->D1_COD,TRBSD1->D1_QUANT,TRBSD1->D1_VUNIT)
			sCenCus := CTT->CTT_CUSTO
		Else
		    sCenCus := ''
	    EndIf
    EndDo
//EndDo
	
    dbSelectArea("TRBSD1")
    DbSkip()
EndDo


dbSelectArea("TRBSB2")
DbGoTop()
SetRegua(Reccount())
aCols := {}
nTotal := 0
While !Eof()
	Incregua()
	dData := ctod("  /  /  ")
	nValUDoc := 0
	If sTipo == 'PA'
		dbSelectArea("SD2")
		dbSetOrder(6)
		dbSeek(xFilial("SD2")+TRBSB2->B1_COD+sLocal+'99999999',.T.)// 01, Almox. Entrada Estoque
		DbSkip(-1)
		If xFilial("SD2")+TRBSB2->B1_COD+sLocal == SD2->D2_FILIAL+SD2->D2_COD+SD2->D2_LOCAL
			If dTos(SD2->D2_EMISSAO) >= dTos(dUltEnt) .And. Dtos(SD2->D2_EMISSAO) <= dtos(dUltSai)
				nValUDoc := SD2->D2_PRCVEN
				dbSelectArea("TRB")
				RecLock("TRB",.T.)
				TRB->TR_CODPRO := TRBSB2->B1_COD
				TRB->TR_DESCRI := TRBSB2->B1_DESC
				TRB->TR_UM     := TRBSB2->B1_UM
				TRB->TR_ESTOQUE:= TRBSB2->B2_QATU
				TRB->TR_DTENTR := SD2->D2_EMISSAO
				TRB->TR_VALUNIT:= nValUDoc
				TRB->TR_TOTAL  := (TRBSB2->B2_QATU*nValUDoc)
				TRB->TR_PERC   := 0
				TRB->TR_IND    := 0
				MsUnlock("TRB")
				nTotal += TRB->TR_TOTAL
			EndIf
		EndIf
	ElseIf sTipo == 'MP'
		dbSelectArea("SD1")
		dbSetOrder(7)
		dbSeek(xFilial("SD1")+TRBSB2->B1_COD+sLocal+'99999999',.T.)// 01, Almox. Entrada Estoque
		DbSkip(-1)
		nValUDoc := 0                             
		While xFilial("SD1")+TRBSB2->B1_COD+sLocal == SD1->D1_FILIAL+SD1->D1_COD+SD1->D1_LOCAL .And. nValUDoc == 0
			If dTos(SD1->D1_DTDIGIT) >= dTos(dUltEnt) .And. Dtos(SD1->D1_DTDIGIT) <= dtos(dUltSai) .And. Alltrim(SD1->D1_SERIE) <>'U'
				nValUDoc := SD1->D1_VUNIT
				dbSelectArea("TRB")
				RecLock("TRB",.T.)
				TRB->TR_CODPRO := TRBSB2->B1_COD
				TRB->TR_DESCRI := TRBSB2->B1_DESC
				TRB->TR_UM     := TRBSB2->B1_UM
				TRB->TR_ESTOQUE:= TRBSB2->B2_QATU
				TRB->TR_DTENTR := SD1->D1_DTDIGIT
				TRB->TR_VALUNIT:= nValUDoc
				TRB->TR_TOTAL  := (TRBSB2->B2_QATU*nValUDoc)
				TRB->TR_PERC   := 0
				TRB->TR_IND    := 0
				MsUnlock("TRB")
				nTotal += TRB->TR_TOTAL
			EndIf
		dbSelectArea("SD1")
		DbSkip(-1)
		EndDo
	EndIf
	dbSelectArea("TRBSB2")
	DbSkip()
EndDo

dbSelectArea("TRB")
DbGoTop()
SetRegua(Reccount())
aCols := {}
While !Eof()   
    Incregua()
		RecLock("TRB",.F.)
		TRB->TR_PERC   := (TRB->TR_TOTAL/nTotal)*100
		TRB->TR_IND    := 9999-TRB->TR_PERC
		MsUnlock("TRB")
    DbSkip()
EndDo

dbSelectArea("TRB") 
cNomeArq := CriaTrab(NIL,.F.)
IndRegua("TRB",cNomeArq,"STR(TR_IND)",,,"Selecionando registros...")

DbGoTop()
SetRegua(Reccount())
aCols := {}
While !Eof()   
    Incregua()
	fCabec2()                      
	@ iLinha, 000 PSAY TRB->TR_CODPRO
	@ iLinha, 016 PSAY Left(TRB->TR_DESCRI,58)
	@ iLinha, 067 PSAY TRB->TR_UM
	@ iLinha, 071 PSAY TRB->TR_ESTOQUE                 PICTURE "@E 999,999.999"
	@ iLinha, 083 PSAY TRB->TR_DTENTR 
	@ iLinha, 092 PSay TRB->TR_VALUNIT                 PICTURE "@E 999,999.999999"
	@ iLinha, 107 PSay TRB->TR_TOTAL                   PICTURE "@E 99,999,999.99"
	@ iLinha, 121 PSay TRB->TR_PERC                    PICTURE "@E 999.99"
    DbSkip()
EndDo
fCabec2()
@ iLinha, 0 PSAY Repl('=',132)
fCabec2()
@ iLinha, 0 PSAY "TOTAL"
@ iLinha, 107 PSay nTotal                  PICTURE "@E 99,999,999.99"
fCabec2()
@ iLinha, 0 PSAY Repl('=',132)

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


//relatorio de centro de custo..
//aanalitico sintetico..
//centro de custo pai..
//total por centro de custo

/*CC, produto,descricao , qtde, un, vl unit,total,
SELECT D1_COD,D1_EMISSAO,D1_CC,D1_QUANT,D1_VUNIT,* FROM SD1010
WHERE D1_EMISSAO >= '20080801'  AND D1_CC <> ''


SELECT D3_COD,D3_EMISSAO,D3_CC,D3_QUANT,D3_CUSTO1,* FROM SD3010
WHERE D3_CC <>''  AND D3_EMISSAO >= '20080801' */
                                       
***************************************
Static Function GravTRB(sCC,sCod,nQuant,nVunit)
***************
dbSelectArea("TRB")
iF (DbSeek(sCC+sCod))
	Reclock("TRB",.F.)
Else
	Reclock("TRB",.T.)
EndIf
TRB->TR_CC      := sCC
TRB->TR_PRODUTO := sCod
TRB->TR_QUANT   += nQuant
TRB->TR_VALUNIT := nVunit
TRB->TR_TOTAL   := TRB->TR_QUANT * TRB->TR_VALUNIT
MsUnlock("TRB")
Return()
