#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/*/{Protheus.doc} DLP02G02
    (long_description)
    @type  Function
    @author user
    @since 11/12/2019
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
user Function DLP02G02()
    Local aArea := getarea()
    Local xRet := ""
    Default cRotina := ALLTRIM(FUNNAME())

    //SA50102 A5_FILIAL, A5_PRODUTO, A5_FORNECE, A5_LOJA, R_E_C_N_O_, D_E_L_E_T_

    sCod    :=  GdFieldGet('D1_COD')

    dbSelectArea("SB1")
    SB1->(dbSetOrder(1))

    dbSelectArea("SA5")
    SA5->(dbSetOrder(2))

    IF   SA5->(dbSeek(xFilial("SA5")+sCod+cA100For+cLoja ))

        xRet :=  SA5->A5_NCMPRF

    ELSE

        SB1->(dbSeek(xFilial("SB1")+sCod))
        xRet := SB1->B1_POSIPI

    END
    RestArea(aArea)
Return xRet
