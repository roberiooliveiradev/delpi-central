#include 'totvs.ch'
#include "rwmake.ch"
#INCLUDE "TOPCONN.CH"
/*/{Protheus.doc} MT381LOK
    (long_description)
    @type  Function
    @author Gabriel
    @since 15/11/2022
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)

/*/
user Function MT380EXC()
    Local lRet := .T.

    Local aGroUsr := UsrRetGrp(PswChave(RetCodUsr()),RetCodUsr()) //Retorna um array contendo todos os códigos dos Grupos de Usuário em que o Usuário, passado na função, pertence.
    Local cGRPMnt := supergetmv("MV_DMNTEMP",.F.,"000001") //codigo do grupo de usuario
    Local aBotoes := {}
    Local n1 := 0

    CONOUT("MT380EXC")
    nPosUsr:=  aScan(aGroUsr,{|x| AllTrim(x) == AllTrim(cGRPMnt)})
    CONOUT("nPosUsr " + cvaltochar(nPosUsr))
    CONOUT("RetCodUsr " + RetCodUsr() )
    CONOUT("cGRPMnt " + alltrim(cGRPMnt) )
    if 	nPosUsr > 0 .or. (RetCodUsr() != "000000")
        FWAlertError("Sem permissão para excluir empenho de OP", "Ajuste de Empenho")
        lRet := .f.
    ENDIF


Return lRet
