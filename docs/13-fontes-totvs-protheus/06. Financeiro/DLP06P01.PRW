#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"



USER FUNCTION DLP06P01(nOpc)

    Local cRet := ""

    if nOpc == 1
        cRet := space(getsx3cache("E2_NUM","X3_TAMANHO"))
        IF IsInCallStack("MATA121")

            cRet := padr(CA120NUM,getsx3cache("E2_NUM","X3_TAMANHO"))
            M->E2_NUM := cRet
        ENDIF
    elseif nOpc == 2
        cRet := space(getsx3cache("E2_TIPO","X3_TAMANHO"))
        IF IsInCallStack("MATA121")

            cRet := padr("PA",getsx3cache("E2_TIPO","X3_TAMANHO"))
            M->E2_TIPO := cRet
            cBancoAdt :="001"
            cAgenciaAdt :="31631"
            cNumCon := "5156X     "
        ENDIF
    elseif nOpc == 3 // NATUREZA
        cRet := space(getsx3cache("E2_NATUREZ","X3_TAMANHO"))
        IF IsInCallStack("MATA121")

            cRet := padr(SA2->A2_NATUREZ,getsx3cache("E2_NATUREZ","X3_TAMANHO"))
            M->E2_NATUREZ := cRet
            FA050Natur()
            FinVldNat( .F., M->E2_NATUREZ, 2 )
        ENDIF
    elseif nOpc == 4 // FORNECE
        cRet := space(getsx3cache("E2_FORNECE","X3_TAMANHO"))
        IF IsInCallStack("MATA121")

            cRet := padr(CA120FORN,getsx3cache("E2_FORNECE","X3_TAMANHO"))
            M->E2_FORNECE := cRet
        ENDIF
    elseif nOpc == 5 // LOJA  FORNECE
        cRet := space(getsx3cache("E2_LOJA","X3_TAMANHO"))
        IF IsInCallStack("MATA121")

            cRet := padr(CA120LOJ,getsx3cache("E2_LOJA","X3_TAMANHO"))
            M->E2_LOJA := cRet
        ENDIF

    elseif nOpc == 6 // emissao
        cRet :=  CTOD("  /  /  ")
        IF IsInCallStack("MATA121")

            cRet :=  DA120EMIS+1
            M->E2_EMISSAO:= cRet
        ENDIF
    elseif nOpc == 7 // vencimento E2_VENCTO
        cRet :=  CTOD("  /  /  ")
        IF IsInCallStack("MATA121")

            cRet :=DA120EMIS+1// padr(,getsx3cache("E2_VENCTO","X3_TAMANHO"))
            M->E2_VENCTO  := cRet
        ENDIF
    elseif nOpc == 8 // total
        cRet := 0.00
        IF IsInCallStack("MATA121")

            cRet := aValores[6]
            M->E2_VALOR   := aValores[6]
            // M->E2_SALDO   := aValores[6]
            // M->E2_VLCRUZ   := aValores[6]
            fa050valor()
            FA050Nat2()


        ENDIF
    elseif nOpc == 9 // vencimento E2_VENCREA
        cRet :=  CTOD("  /  /  ")
        IF IsInCallStack("MATA121")

            cRet := DA120EMIS+1
            M->E2_VENCREA  := cRet
        ENDIF
    elseif nOpc == 10 // E2_SALDO
        cRet := 0.00
        IF IsInCallStack("MATA121")

            cRet := aValores[6]
            //    M->E2_VALOR   := aValores[6]
            M->E2_SALDO   := aValores[6]
            //    M->E2_VLCRUZ   := aValores[6]
            //  fa050valor()
            //  FA050Nat2()


        ENDIF
    elseif nOpc == 11 // E2_VLCRUZ
        cRet := 0.00
        IF IsInCallStack("MATA121")

            cRet := aValores[6]
            //    M->E2_VALOR   := aValores[6]
            // M->E2_SALDO   := aValores[6]
            M->E2_VLCRUZ   := aValores[6]
            //  fa050valor()
            //  FA050Nat2()


        ENDIF
    endif
    CONOUT("STOP")
RETURN cRet
