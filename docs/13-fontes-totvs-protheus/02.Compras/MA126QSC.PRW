#include 'protheus.ch'
#include 'parmtype.ch'

User Function  MA126QSC()
    Local cKey := PARAMIXB[1] // chave utilizada pelo sistema
    Local cNewKey := 'C1_FILENT+C1_FORNECE+C1_LOJA+C1_PRODUTO+C1_DESCRI+Dtos(C1_DATPRF)+C1_CC+C1_CONTA+C1_ITEMCTA+C1_CLVL+C1_TPOP+C1_USER'
    lConsEntCtb	:= .T.
Return cNewKey

