#include 'protheus.ch'
#include 'parmtype.ch'

User Function M290QSD2()
    Local cQuery := ' '
    cQuery :=  "AND D2_TES NOT IN("+VALTOSQL("627")+" , "+VALTOSQL("638")+" ) " // Adicionar condição do usuário

Return(cQuery)
