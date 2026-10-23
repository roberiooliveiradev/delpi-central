#include "rwmake.ch"

/////  PROGRAMA PARA INDICAR A MODALIDADE DO PAGAMENTO POS.264-265

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Declaracao de variaveis utilizadas no programa atraves da funcao    ³
//³ SetPrvt, que criara somente as variaveis definidas pelo usuario,    ³
//³ identificando as variaveis publicas do sistema utilizadas no codigo ³
//³ Incluido pelo assistente de conversao do AP5 IDE                    ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

User Function pagmod()

SetPrvt("_AMODEL,")
 
IF SUBSTR(SEA->EA_MODELO,1,2) == "01"
   If SA2->A2_BANCO  =="237"
      aModel := "01"
   Else
      aModel := "03"
   Endif
ElseIf  SUBSTR(SEA->EA_MODELO,1,2) == "30"
   aModel := "31"
Else
   aModel := SUBSTR(SEA->EA_MODELO,1,2)
EndIf

Return(aModel)