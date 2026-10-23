#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "protheus.ch"


/*/{Protheus.doc} DLP10F05
    (long_description)
    @type  Function
    @author Gabriel
    @since 09/07/2021
    @version 1.0
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
user Function DLP10F05()
    Local aAreaSA7   := SA7->(GetArea())
    Local aArea := getarea()
    Local lRet := .t.
    conout("teste")
    cCodProd := M->C2_PRODUTO
    dbSelectArea("SA7")
    SA7->(dbSetOrder(2))
    IF 	dbSeek(xFilial("SA7")+cCodProd)

        M->C2_CLIDELP := SA7->A7_CLIENTE
        M->C2_LOJDELP := SA7->A7_LOJA

    ENDIF

    RESTAREA(aAreaSA7 )
    restarea(aArea)

Return lRet
