#include "rwmake.ch"

User Function DEL015()
/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DEL015 ºAutor ³Clovis Emmendorfer      º Data ³  06/11/04   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³         REQUISICOES AGLUTINADAS POR PRODUTO                º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ EXCLUSIVO DELPI                                            º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

cPerg := "DEL015"
aRegistros := {}
AADD(aRegistros,{cPerg,"01","OP de           ","","","mv_ch1","C",11,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","SC2","","","",})
AADD(aRegistros,{cPerg,"02","OP ate          ","","","mv_ch2","C",11,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","SC2","","","",})
AADD(aRegistros,{cPerg,"03","Data de         ","","","mv_ch3","D",08,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","","","","",})
AADD(aRegistros,{cPerg,"04","Data ate        ","","","mv_ch4","D",08,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","",})

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

Pergunte(cPerg,.f.)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Define Variaveis                                             ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
cSavCur1:="";cSavRow1:="";cSavCol1:="";cSavCor1:="";cSavScr1:="";CbTxt:=""
CbCont:="";cabec1:="";cabec2:="";cabec3:="";wnrel:=""
nOrdem:=1
tamanho:="P"  //M=132 colunas, P=80 colunas, G=220 colunas
titulo :="RELATORIO DE REQUISICOES"
cDesc1 :="Este relatorio emite relacao dos materiais requisitados pelas OP's"
CDesc2 :=" aglutinado por produto."
cDesc3 :=""
cString:="SD4"
aReturn:={ "Especial", 1,"Administracao", 1, 2, 1, "",1 }
nomeprog:="DEL015"
nLastKey:= 0

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Salva a Integridade dos dados de Saida                       ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

cbText   := space(10)
cbCont   := 0
cabec1   := ""
cabec2   := ""
wnrel    := "DEL015"

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Variaveis utilizadas para Impressao do Cabecalho e Rodape    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
li       := 80
m_pag    := 1
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Verifica as perguntas selecionadas                           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Envia controle para a funcao SETPRINT                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

wnrel:=SetPrint(cString,wnrel,cPerg,Titulo,cDesc1,cDesc2,cDesc3,.F.,"",,tamanho)

If LastKey() == 27 .or. nLastKey == 27
	Return
Endif

SetDefault(aReturn,cString)

If LastKey() == 27 .OR. nLastKey == 27
	Return
Endif

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Geracao Arquivo Trabalho                                     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

RptStatus({|| Impcur() })

Return //User Function

Static Function ImpCur()
************************

cChave := "D4_FILIAL+D4_COD"

dbSelectArea("SD4")
dbGoTop()
cIndex := CriaTrab(Nil,.F.)
cString := dbFilter()
cString := 'D4_FILIAL == "' + xFilial("SD4") + '" .And. '
cString += 'DTOS(D4_DATA) >= "' + DTOS(mv_par03) + '" .and. DTOS(D4_DATA) <= "' + DTOS(mv_par04) + '" .AND. '
cString += 'D4_OP >= "' + mv_par01 + '" .And. D4_OP <= "' + mv_par02 + '" '

IndRegua("SD4",cIndex,cChave,,cString,"Selecionando Registros...")

dbGoTop()
SetRegua(RecCount())

cCod   := SD4->D4_COD                     
nQuant := 0

While !EOF()

	If li > 55
			
		li := 5
		cabec(titulo,cabec1,cabec2,nomeprog,tamanho)
		@li,01 PSAY "________________________________________________________________________________"
		li += 1
		@li,01 PSAY "PRODUTO          DESCRICAO                                  QUANTIDADE      UM"
		li += 1
		@li,01 PSAY "________________________________________________________________________________"
			
		li += 3
			
	Endif

	If SD4->D4_COD == cCOD
	
		nQuant := nQuant + SD4->D4_QUANT
		
	Else                
	
		cDesc := Posicione("SB1",1,xFilial("SB1")+cCOD,"B1_DESC")	
		cUM   := Posicione("SB1",1,xFilial("SB1")+cCOD,"B1_UM")	
		@li,01 PSAY cCOD              
		@li,18 PSAY Substr(cDesc,1,40)
		@li,61 PSAY nQuant PICTURE "@E 99,999,999.999"
		@li,77 PSAY cUM
		
		nQuant := SD4->D4_QUANT
		cCOD   := SD4->D4_COD
		
		li += 1		
	Endif
	
	dbSelectArea("SD4")
	dbSkip()
	
Enddo

DbCloseArea("QC2")
DbCloseArea("QD4")

Set Device To Screen

If aReturn[5] == 1
	Set Printer TO
	dbCommitall()
	ourspool(wnrel)
Endif
MS_FLUSH()

Return