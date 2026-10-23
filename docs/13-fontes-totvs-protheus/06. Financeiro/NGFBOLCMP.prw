#INCLUDE "TOTVS.CH"
#INCLUDE "PROTHEUS.CH"

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 26/06/2024
/*/
User Function NGFBOLCMP()
    Local aCampos As Array

    //Inicialização da variaveis
    aCampos := {}

    //Campos adicionais para os titulos a pagar
    Aadd(aCampos, "EA_YBLQPIX")

Return aCampos
