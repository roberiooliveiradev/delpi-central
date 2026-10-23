#Include "totvs.ch"
#Include "parmtype.ch"

/*/{Protheus.doc} MT170QRY
Ponto de entrada chamado em A170Point para manipulacao da query
de selecao de produtos no MATA170 - Solicitacao por Ponto de Pedido.

Aplica:
  1. Filtro fixo - exclui produtos B1_TIPO 'AI' (regra herdada do
     projeto Delpi).
  2. Filtro condicional - quando MV_PAR23 = 2 (Nao), exclui produtos
     de terceiros (B1_TPMAT='2'). Quando MV_PAR23 = 1 (Sim) ou
     ausente, mantem o comportamento original.

A pergunta MV_PAR23 deve ser cadastrada no SX1 grupo MTA170 ordem 23
via Configurador (SIGACFG):
  - Pergunta : Cons. Prod. Terceiros ?
  - Tipo     : Numerico, tamanho 1
  - Combo    : 1=Sim;2=Nao
  - Default  : 1 (Sim) - preserva comportamento legado

@type   user function (entry point)
@author Johnni C. Moraes
@since  08/05/2026
@param  ParamIXB[1] - cQuery - SQL original montada pelo MATA170
@return cNewQry - SQL ajustada (sem ORDER BY, conforme regra do PE)
/*/
User Function MT170QRY()

	Local cNewQry := ParamIXB[1]
	Local nConsTerc := 1

	If Type("MV_PAR23") == "N"
		nConsTerc := MV_PAR23
	EndIf

	cNewQry += " AND SB1.B1_TIPO NOT IN ('AI') "

	If nConsTerc == 2
		cNewQry += " AND SB1.B1_TPMAT <> '2' "
	EndIf

Return cNewQry
