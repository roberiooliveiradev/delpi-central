#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.CH"
#INCLUDE "rwmake.ch"
#include 'topconn.ch'

/*/{Protheus.doc} FATA600

    Description

    @author  Name
    @example Example
    @param   [Parameter_Name],Parameter_type,Parameter_Description
    @return  Return
    @table   Tables
    @since   04-10-2019
/*/

User Function FATA600()
    Local aParam := PARAMIXB
    Local xRet := .T.
    Local cIdPonto := ""
    Local cUpd := ""
    Local n1

    //1 - MODELPRE | 2 - MODELPOS  3- FORMPRE | 4 - FORMPOS | 5 FORMLINEPRE | 6 FORMLINEPOS Requer um retorno lógico.
    //FORMCANCEL MODELVLDACTIVE Requer um retorno lógico.
    //7 - MODELCOMMITTTS Retorno MODELCOMMITNTTS FORMCOMMITTTSPRE FORMCOMMITTTSPOS Nil
    //BUTTONBAR'

    If aParam <> NIL
        cIdPonto := aParam[2]

        conout("ID do formulário. " + cvaltochar(cIdPonto ))
        If cIdPonto $ "MODELCOMMITTTS_MODELCOMMITNTTS_FORMCOMMITTTSPRE_FORMCOMMITTTSPOS"
            If cIdPonto $ "MODELCOMMITNTTS" .AND. cEmpAnt $"04" .AND. APARAM[1]:NOPERATION == 3

                cUpd := "EXEC dbo.stp_DLPCRM_001 "
                cUpd +=" @OPORTUNIDADE = "+valtosql(ADY->ADY_OPORTU)
                cUpd +=" , @PROPOSTA = "+valtosql(ADY->ADY_PROPOS)
                cUpd +=" , @FILIAL = "+valtosql(xfilial("ADY"))

                conout("cIdPonto - FORMCOMMITTTSPOS")
                CONOUT(cUpd)

                TCSqlExec(cUpd)

            endif
            xRet := Nil
        ElseIf  cIdPonto $ "BUTTONBAR"
            xRet := {}
        EndIf
        If cIdPonto $ "MODELPOSS"
        elseif cIdPonto $ "MODELPRE" .and. trim(cEmpAnt ) == '01'
            oModel		:= FwModelActive()
            oMdlPrd		:= oModel:GetModel("ADZPRODUTO")
            oStrADZPro:= oModel:GetModel("ADZPRODUTO"):GetStruct()
            aAux6 := FwStruTrigger("ADZ_PRODUT" /*cDom*/, "ADZ_PRCTAB" /*cCDom*/,  "U_DLP73G01()" /*cRegra*/,  .F. /*lSeek*/,   Nil /*cAlias*/,    0   /*nOrdem*/,    Nil /*cChave*/,Nil /*cCondic*/,Nil /*cSequen*/)

            lAchou := .f.
            For n1 := 1 to Len(oStrADZPro:ATRIGGERS)
                if "DLP73G01" $ upper(GetCbSource(oStrADZPro:ATRIGGERS[n1][4]))
                    lAchou := .t.
                endif
            Next n1
            if !lAchou
                oStrADZPro:AddTrigger(aAux6[1],aAux6[2],aAux6[3],aAux6[4])
            endif

        elseif cIdPonto $ "FORMPOS"
            if aParam[3]$"CRONOFIN"
                //  fSetCrg(aParam[1])
                conout("gda")
                conout("ID do formulário. " + cvaltochar(aParam[3]) )
            endif

        endif

    endif

Return xRet

