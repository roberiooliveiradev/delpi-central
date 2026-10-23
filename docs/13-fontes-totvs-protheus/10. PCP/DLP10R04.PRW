
#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "protheus.ch"

USER FUNCTION DLP10R04(cH6Opera)
    lOCAL aArea := getarea()
    Local cNmUsr :=padr("Operdaor nao encontrado",40)

    cH6Opera := alltrim(cH6Opera)

    PswOrder(1)
    If PswSeek( cH6Opera, .T. )
        cNmUsr := PswRet()[1][4]
    ENDIF
    //
    // if UsrExist(cH6Opera,.f.)
    //
    //     cNmUsr := FwGetUserName(cH6Opera)
    //
    // ENDIF
    restarea(aArea)
Return cNmUsr
