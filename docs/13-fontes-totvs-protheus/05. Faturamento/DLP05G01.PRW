/*/{Protheus.doc} DLP05G01
   Rotina para preencher o campo C5_INCISS
    @type  Function
    @author Gabriel Araujo
    @since 22/04/2021
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"


USER FUNCTION DLP05G01()
    Local aArea := GetArea()
    Local cCodCli := M->C5_CLIENTE
    Local cLojCli := M->C5_LOJACLI
    Local cOldCnt := M->C5_INCISS
    lOCAL cRet := ""
    Local cTpPes := ""
    if !Empty(cCodCli) .and. !Empty(cLojCli )
        cTpPes := posicione("SA1",1,XFILIAL("SA1")+cCodCli+cLojCli,"A1_PESSOA")

        IF cTpPes == "J"
            cRet := "S"
        ELSE
            cRet := "N"
        ENDIF
    else
        cRet :=cOldCnt
    endif

    RESTAREA(aArea)
Return cRet
