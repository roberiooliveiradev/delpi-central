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
user Function M380ZEMP()
    Local lRet := .T.

    Local aGroUsr := UsrRetGrp(PswChave(RetCodUsr()),RetCodUsr()) //Retorna um array contendo todos os códigos dos Grupos de Usuário em que o Usuário, passado na função, pertence.
    Local cGRPMnt := supergetmv("MV_DMNTEMP",.F.,"000001") //codigo do grupo de usuario


    CONOUT("STOP")
    if 	 aScan(aGroUsr,{|x| AllTrim(x) == AllTrim(cGRPMnt)}) == 0 .and. (RetCodUsr() != "000000")
        FWAlertError("Sem permissão para excluir empenho de OP", "Ajuste de Empenho")
        lRet := .f.
    ENDIF


Return lRet
