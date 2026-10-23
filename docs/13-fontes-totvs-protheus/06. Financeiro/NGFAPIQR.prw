#INCLUDE "TOTVS.CH"
#INCLUDE "PROTHEUS.CH"

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 26/06/2024
*/
User Function NGFAPIQR()
  Local cQuery As Character

  //Inicialização da variaveis
  cQuery := ""

  //Trativa para Meios de pagamento Pix a Fornecedores ou Demais pagamentos.
  cQuery += " ((SEA.EA_TIPOPAG = '20' AND SEA.EA_MODELO = '45' AND SEA.EA_YBLQPIX = 'S' AND EA_SUBCTA  ='003' ) OR "
  cQuery += " (SEA.EA_TIPOPAG != '20' AND SEA.EA_MODELO != '45' AND SEA.EA_YBLQPIX = ' ' AND EA_SUBCTA  !='003')) "
  conout("NGFAPIQR")
Return cQuery
