#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "protheus.ch"

USER FUNCTION DLP10G01()

    lOCAL dDatPri := SomaPrazo(M->C2_DATPRF,SuperGetMv("MV_YPRFOP", .F., -2))

    if dDatPri < date()

        dDatPri := date()
    endif
RETURN dDatPri
