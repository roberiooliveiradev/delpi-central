#INCLUDE "PROTHEUS.CH"

/*
Localização: Este Ponto de Entrada está localizado na função A290CalCon (Recálculo do consumo médio do mês)

Em que ponto: É executado DURANTE o cálculo; seu objetivo é que o usuário possa validar itens das NFs de Saída (SD2), que farão parte do recálculo do consumo médio do mês.

Programa fonte: MATA290.PRX

Sintaxe: A290CSD2 - Validação do itens das Nfs de Saída ( [ PARAMIXB ] ) --> lRet

Regra Delpi => Nao considerar
*/
USER FUNCTION A290CSD2()


    Local lRet := .t.
    Local aArea     := getarea()
    Local aAreaSD2 := SD2->(GetArea())

    if alltrim(SD2->D2_CLIENTE) $"000102" .AND.  alltrim(SD2->D2_FILIAL) == "01" .OR.;
            alltrim(SD2->D2_CLIENTE) $"000079" .AND.  alltrim(SD2->D2_FILIAL) == "02"

        lRet := .F.

    endif
    restarea( aArea    )
    restarea( aAreaSD2 )


return lRet
