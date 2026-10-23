#INCLUDE "FWMVCDEF.CH"
#Include 'PROTHEUS.CH'

User Function FT300BUT()

    Local oView := ParamIXB[01] // Este parâmetro somente estará disponível na versão 12.1.17, cujo programa fonte FATA300.PRX possua a data posterior à 06/novembro/2017
    Local aRet := {}

    aAdd(aRet,{"Cad Produtos"		, "", {|| U_DLP73F02(1) }, "Prod", , {MODEL_OPERATION_VIEW, MODEL_OPERATION_INSERT, MODEL_OPERATION_UPDATE}})
    aAdd(aRet,{"Cad Estruturas"		, "", {|| U_DLP73F02(2) }, "Est" , , {MODEL_OPERATION_VIEW, MODEL_OPERATION_INSERT, MODEL_OPERATION_UPDATE}})
    aAdd(aRet,{"Rot Operações"	  ,   "", {|| U_DLP73F02(3) }, "Oper", , {MODEL_OPERATION_VIEW, MODEL_OPERATION_INSERT, MODEL_OPERATION_UPDATE}})
    aAdd(aRet,{"Formacao de Preco"	  ,   "", {|| U_DLP73F02(4) }, "Form", , {MODEL_OPERATION_VIEW, MODEL_OPERATION_INSERT, MODEL_OPERATION_UPDATE}})

Return aRet