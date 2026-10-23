#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/*/{Protheus.doc}  MT116VTP
    Ponto de Entrada, Para nao aglutinar os Produtos

    Para validar a TES utilizada para entrada do Conhecimento de Transporte X a Tes da Nota fiscal Original
    Ambas tem que ter a configuracao de estoque iguais
05/2021 - Gabriel Araujo
/*/

USER FUNCTION MT116VTP()
	Local aArea :=getarea()
	Local lRet := .t.
	Local cUFFor := POSICIONE("SA2",1,XFILIAL("SA2")+   aParametros[5]+   aParametros[6],"A2_EST")

	IF IsInCallStack("ImpXML_Cte")
		restarea(aArea)
		Return .T.
	ENDIF
	IF  c116UFOri != cUFFor

		c116UFOri :=  cUFFor
		aParametros [14] :=  cUFFor
	ENDIF

	aParametros[15] := .f.

	if Empty(cTPCTE)
		cTPCTE := "N"
	endif

	if alltrim(retcodusr()) $"000000"

		aParametros[18] := .t.

	endif
    /*c116UFOri
     // 5 Cod. Fornecedor para Filtro das NF Originais
    // 6 Loja Fornecedor para Fltro das NF Originais
    14 Estado de Origem do Frete
    */
	restarea(aArea)
Return lRet
