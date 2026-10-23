#include "protheus.ch"
#INCLUDE "TOTVS.CH"
#INCLUDE "FWLIBVERSION.CH"
#INCLUDE "FWEVENTVIEWCONSTS.CH"
/*
O ponto de entrada: MT103ENEG está localizado na função: MaCanDelF1 sendo executado na exclusão do Documento de Entrada,
quandoo parâmetro: MV_ESTNEG estiver configurado como NÃO e o(s) produto(s) do Documento de Entrada não possuirem Lote ou Localização.
Sua finalidade é permitir que o estoque fique negativo mesmo que o parâmetro MV_ESTNEG estiver configurado como NÃO.**
Caso o produto possuir Rastro ou Localização, o ponto de entrada NÃO será executado e prevalecem as validações padrões do sistema.
Programa Fonte
MATA103X.PRX
*/
User function MT103ENEG()
    Local lRet := .T.
    lOCAL cUsrPer := supergetmv("MV_ZEXCNF",.F.,"000000_000008") // codigo dos usuarios que podem excluir com estoque negativo
    Local aArea     :=getarea()
    Local aAreaB2	:= SB2->(GetArea())
    lOCAL cEol := chr(10)

    if !(RetCodUsr() $cUsrPer)

        lRet:= .f.

    endif

    restarea(aArea    )
    restarea(aAreaB2	)
Return lRet
