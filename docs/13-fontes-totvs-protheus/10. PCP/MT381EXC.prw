#include 'totvs.ch'
#include "rwmake.ch"
#INCLUDE "TOPCONN.CH"
/*/{Protheus.doc} MT381EXC
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
    MT381EXC - Confirmação de exclusão
O ponto de entrada MT381EXC é executado na confirmação da exclusão, utilizado para confirmar a exclusão do Ajuste de Empenho Modelo 2.
    https://tdn.totvs.com/pages/releaseview.action?pageId=6087917
/*/
user Function MT381EXC()
    Local lRet := .f.

    Local aGroUsr := UsrRetGrp(PswChave(RetCodUsr()),RetCodUsr()) //Retorna um array contendo todos os códigos dos Grupos de Usuário em que o Usuário, passado na função, pertence.
    Local cGRPMnt := supergetmv("MV_DMNTEMP",.F.,"000001") //codigo do grupo de usuario
    CONOUT("STOP")

    CONOUT("MT381EXC")
    nPosUsr:=  aScan(aGroUsr,{|x| AllTrim(x) == AllTrim(cGRPMnt)})
    CONOUT("nPosUsr " + cvaltochar(nPosUsr))
    CONOUT("RetCodUsr " + RetCodUsr() )
    CONOUT("cGRPMnt " + alltrim(cGRPMnt) )
    if 	nPosUsr> 0 .or. (RetCodUsr() == "000000")
        lRet := .T.
    endif


    if !lRet

        FWAlertError("Sem permissão para excluir empenho de OP", "Ajuste de Empenho")

    endif

Return lRet
