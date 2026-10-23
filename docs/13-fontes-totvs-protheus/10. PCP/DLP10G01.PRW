#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "protheus.ch"

USER FUNCTION DLP10G01()

    lOCAL nPRFOP := SuperGetMv("MV_YPRFOP", .F., -2)
    Local nLeadOP := posicione("SBZ",1,XFILIAL("SBZ")+M->C2_PRODUTO,"BZ_YLEADOP")*-1
    CONOUT("FUNNAME DLP10G01")
    CONOUT("FUNNAME DLP10G01 C2NUM"+M->C2_NUM)
    CONOUT("FUNNAME DLP10G01M->C2_DATPRF "+ DTOS(M->C2_DATPRF))

    dDatPri := SomaPrazo(M->C2_DATPRF,nLeadOP )
    if dDatPri < date()
        CONOUT("FUNNAME DLP10G01 < date()")
        dDatPri := date()
    endif

    /*  IF cFilAnt == "01"
        dDatPri := SomaPrazo(M->C2_DATPRF,nPRFOP )
        if dDatPri < date()

            dDatPri := date()
        endif

    else
        dDatPri := SomaPrazo(M->C2_DATPRF,nLeadOP )
        if dDatPri < date()

            dDatPri := date()
        endif

    endif*/
RETURN dDatPri
