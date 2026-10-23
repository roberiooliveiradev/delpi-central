
#INCLUDE "PROTHEUS.CH"
//-------------------------------------------------------------------
/*/{Protheus.doc} CONVUM
Ponto de Entrada para validar a conversão de unidade de medida,
para nao permitir arredondar na segunda unidade de medida
@author  Gabriel
@since   13/02/2025
@version 1.0
/*/
//-------------------------------------------------------------------
USER FUNCTION CONVUM()
    Local nQtd1 := PARAMIXB[1]
    Local nQtd2 := PARAMIXB[2]
    Local nUnid := PARAMIXB[3]
    Local nQtd  := PARAMIXB[4]

    if nUnid == 1 .AND.( IsInCallStack("MATA110") .OR.  IsInCallStack("MATA126"))

        nDif := abs(nQtd1-nQtd)
        if nDif  <1
            nQtd  :=nQtd1
        endif
    endif

rETURN nQtd
