#include 'protheus.ch'
#include 'parmtype.ch'

User Function M290QSD1()
    Local cQuery := ' '
    cQuery :=  "AND D1_TES NOT IN("+VALTOSQL("150")+" , "+VALTOSQL("151")+" ) " // Adicionar condição do usuário

Return(cQuery)
