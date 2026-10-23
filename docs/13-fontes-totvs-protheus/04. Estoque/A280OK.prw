// #########################################################################################
// Projeto:
// Modulo :
// Fonte  : A280OK
// ---------+-------------------+-----------------------------------------------------------
// Data     | Autor             | Descricao
// ---------+-------------------+-----------------------------------------------------------
// 19/11/14 | Jaylson Ribeiro   | Validar fechamentos com problema
// ---------+-------------------+-----------------------------------------------------------

#include "protheus.ch"

//------------------------------------------------------------------------------------------
/*/{Protheus.doc} A280OK
nao compilar
Montagem da tela de processamento

@author    TOTVS | Developer Studio - Gerado pelo Assistente de Código
@version   1.xx
@since     19/11/2014
/*/
//------------------------------------------------------------------------------------------
User Function A280OK()

	Local cQProb := "A280OK"
	Local aProblem := {}
	Local _lRet := .T.

	beginSQL Alias cQProb
SELECT SB1.B1_DESC, SB1.B1_FILIAL, SB1.B1_COD, SB2.B2_COD, SB2.B2_FILIAL, SB2.B2_QFIM, SB2.B2_LOCAL, SB2.B2_VFIM1
	FROM
	%Table:SB1% SB1 INNER JOIN %Table:SB2% SB2 ON SB1.B1_COD  = SB2.B2_COD
	WHERE SB1.B1_FILIAL = %XFILIAL:SB1% AND SB2.B2_FILIAL = %XFILIAL:SB2% AND SB1.%NotDel% AND SB2.%NotDel% AND
	((B2_QFIM = 0 AND B2_VFIM1 > 0) OR
	 (B2_QFIM < 0 ) OR
	 (B2_VFIM1 <0 ))
	ORDER BY B2_FILIAL,B2_COD
	endSQL

	dbSelectArea(cQProb)
	(cQProb)->(dbGoTop())
	While !(cQProb)->(Eof())

		aadd(aProblem,{(cQProb)->B2_FILIAL,(cQProb)->B2_COD,(cQProb)->B1_DESC,(cQProb)->B2_COD,(cQProb)->B2_LOCAL,(cQProb)->B2_QFIM,(cQProb)->B2_VFIM1})

		(cQProb)->(dbSkip())
	End

	If len(aProblem) > 0
		MsgStop("Foram encontrados erros nos saldos de fechamento. Será impresso um relatório com os problemas apresentados. O fechamento não ocorrerá enquanto existirem estes problemas. Favor verificar!")
		PrtFalts(aProblem)
		_lRet := .F.
	Endif
	(cQProb)->(dbclosearea())
Return(_lRet)
//--< fim de arquivo >----------------------------------------------------------------------

Static Function PrtFalts(aProblem)


	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Declaracao de Variaveis                                             ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	Local cDesc1         := "Foram encontrados problemas no fechamento. "
	Local cDesc2         := "Favor verificar."
	Local cDesc3         := "Não será feito fechamento se existirem problemas."
	Local cPict          := ""
	Local titulo       := "Problemas no fechamento"
	Local nLin         := 80

	Local Cabec1       := "Fil. Codigo    Descrição                     Local  Quantidade  Valor"
	Local Cabec2       := ""
	Local imprime      := .T.
	Local aOrd := {}
	Private lEnd         := .F.
	Private lAbortPrint  := .F.
	Private CbTxt        := ""
	Private limite           := 80
	Private tamanho          := "P"
	Private nomeprog         := "A280OK" // Coloque aqui o nome do programa para impressao no cabecalho
	Private nTipo            := 18
	Private aReturn          := { "Zebrado", 1, "Administracao", 2, 2, 1, "", 1}
	Private nLastKey        := 0
	Private cbtxt      := Space(10)
	Private cbcont     := 00
	Private CONTFL     := 01
	Private m_pag      := 01
	Private wnrel      := "A280OK" // Coloque aqui o nome do arquivo usado para impressao em disco
	Private aProblem := aProblem

	Private cString := ""

	wnrel := SetPrint(cString,NomeProg,"",@titulo,cDesc1,cDesc2,cDesc3,.T.,aOrd,.T.,Tamanho,,.T.)

	If nLastKey == 27
		Return
	Endif

	SetDefault(aReturn,cString)

	If nLastKey == 27
		Return
	Endif

	nTipo := If(aReturn[4]==1,15,18)

	RptStatus({|| RunReport(Cabec1,Cabec2,Titulo,nLin,aProblem) },Titulo)
Return

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºFun‡„o    ³RUNREPORT º Autor ³ AP6 IDE            º Data ³  19/11/14   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescri‡„o ³ Funcao auxiliar chamada pela RPTSTATUS. A funcao RPTSTATUS º±±
±±º          ³ monta a janela com a regua de processamento.               º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Programa principal                                         º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

Static Function RunReport(Cabec1,Cabec2,Titulo,nLin,aProblem)

	For _x := 1 to len(aProblem)

		If lAbortPrint
			@nLin,00 PSAY "*** CANCELADO PELO OPERADOR ***"
			Exit
		Endif

		If nLin > 55 // Salto de Página. Neste caso o formulario tem 55 linhas...
			Cabec(Titulo,Cabec1,Cabec2,NomeProg,Tamanho,nTipo)
			nLin := 8
		Endif

		@nLin,00 PSAY aProblem[_x][1]
		@nLin,05 PSAY aProblem[_x][2]
		@nLin,18 PSAY Substr(aProblem[_x][3],1,30)
		@nLin,51 PSAY aProblem[_x][5]
		@nLin,54 PSAY Transform(aProblem[_x][6],"@E 999999.999")
		@nLin,67 PSAY Transform(aProblem[_x][7],"@E 999999.999")

		nLin := nLin + 1 // Avanca a linha de impressao

	Next _x

	SET DEVICE TO SCREEN

	If aReturn[5]==1
		dbCommitAll()
		SET PRINTER TO
		OurSpool(wnrel)
	Endif

	MS_FLUSH()

Return
