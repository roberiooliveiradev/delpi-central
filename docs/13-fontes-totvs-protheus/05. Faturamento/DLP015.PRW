#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 17/07/01
#INCLUDE "TOPCONN.CH"

User Function DLP015()
/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ CTS243   ¦ Autor ¦ Marcio Da Silva       ¦ Data ¦ 13/04/01 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Relatorio de Tabela de Precos Vendedores                   ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/


aOrd := {}
CbTxt        := ""
cDesc1         := "Este programa tem como objetivo imprimir o Pedido   "
cDesc2         := "de acordo com os parametros informados pelo usuario."
cDesc3         := ""
cPict          := ""
lEnd         := .F.
lAbortPrint  := .F.
cString      :="SF2"
limite       := 80
tamanho      := "P"
nomeprog     := "CTS243" // Coloque aqui o nome do programa para impressao no cabecalho
nTipo        := 18
aReturn      := { "Zebrado", 1, "Administracao", 1, 2, 1, "", 1}
nLastKey     := 0
cPerg        := "CTS243"
titulo       := "Tabela de Precos Por Cliente"
nLin         := 0
nLIN2			   := 0
nLIN3			   := 0

Cabec2       := ""
Cabec1       := ""


cbtxt      := Space(10)
cbcont     := 00
CONTFL     := 01
m_pag      := 01
imprime      := .T.
wnrel      := "CTS243" // Coloque aqui o nome do arquivo usado para impressao em disco


//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Monta a interface padrao com o usuario...                           ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

wnrel := SetPrint(cString,NomeProg,,@titulo,cDesc1,cDesc2,cDesc3,.T.,aOrd,.T.,Tamanho,,.T.)

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



Setprc(0,0)

@ 40,10 PSAY "MARCIO" 
i:=10001

//  oPr := ReturnPrtObj()   
//  MSBAR2("CODE128",1.7 ,0.5 ,STR(i)      ,oPr   ,Nil,Nil,Nil,0.012 ,1.2 ,.T.,,"A",.F.,1.5,)

	oPr := ReturnPrtObj()
  cCode := "101010"
  MSBAR2("CODE128"  ,1.7 ,0.5,Alltrim(cCode),oPr  ,Nil,Nil,Nil,0.012 ,1.2 ,.T.     ,Nil,Nil)

	oPr := ReturnPrtObj()
  cCode := "202020"
  MSBAR2("CODE128"  ,4.7 ,0.5,Alltrim(cCode),oPr  ,Nil,Nil,Nil,0.012 ,1.2 ,.T.     ,Nil,Nil)


  
/*  

Sintaxe
MSBAR(cTypeBar,nRow,nCol,cCode,oPrint,lCheck,Color,lHorz,nWidth,nHeigth,lBanner,cFont,cMode,
lPrint,nPFWidth,nPFHeigth)

Parâmetros
[01] nTypeBar - String com o tipo do codigo de barras 
"EAN13","EAN8","UPCA" ,"SUP5" ,"CODE128"
"INT25","MAT25,"IND25","CODABAR","CODE3_9"
[02] nRow - Numero da Linha em centimentros
[03] nCol - Numero da coluna em centimentros
[04] cCode - String com o conteudo do codigo
[05] oPrint - Obejcto Printer
[06] lcheck - Se calcula o digito de controle
[07] color - Numero da Cor, utilize a "common.ch"
[08] lHort - Se imprime na Horizontal                                         
[09] nWidth - Numero do Tamanho da barra em centímetros
[10] nHeigth - Numero da Altura da barra em milímetros
[11] lBanner - Se imprime o linha em baixo do codigo
[12] cFont - String com o tipo de fonte 
[13] cMode - String com o modo do codigo de barras
[14] Onde o 14º lPrint se imprime apenas no server, o default é .F.
15º e 16º passará um índice de ajuste,o default é 1 se passar 0.5 por exemplo
diminuirá.

Segue RDMAKE dos testes:


User Function TMsBar
oprn:=TMSPrinter():New("Teste MSBAR")   
oprn:Setup()

oprn:StartPage()

nLin:= 5

for i:=1 to 3
  MSBAR3("EAN128" ,nLin*i,0.6,STR(i),oprn,.F.,,,0.015, 0.75,.T.,,"A",.F.,1.5,)
Next   
*/


If aReturn[5]==1
	dbCommitAll()
	SET PRINTER TO
	OurSpool(wnrel)
Endif

MS_FLUSH()

Return
