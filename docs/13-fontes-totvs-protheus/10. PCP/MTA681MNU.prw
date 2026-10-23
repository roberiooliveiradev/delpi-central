#Include "Protheus.ch"

//--------------------------------------------------------------
/*/{Protheus.doc} MTA681MNU
    Ponto de entrada para adicionar opcoes no menu principal da
    rotina de Apontamento de Producao PCP Mod.2 (MATA681).
    Adiciona opcao "Imprimir Etiqueta" nas Outras Acoes, que
    chama U_DLP033() com a OP do apontamento selecionado.
@author devCMSS
@since 06/05/2026
@version 1.0
/*/
//--------------------------------------------------------------
User Function MTA681MNU()

	aadd(aRotina, {"Imprimir Etiqueta", "U_DLP033()", 0, 7, 0, NIL})

Return
