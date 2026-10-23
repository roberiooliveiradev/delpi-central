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
user Function MA381BUT()
    Local lRet := .T.

    Local aGroUsr := UsrRetGrp(PswChave(RetCodUsr()),RetCodUsr()) //Retorna um array contendo todos os códigos dos Grupos de Usuário em que o Usuário, passado na função, pertence.
    Local cGRPMnt := supergetmv("MV_DMNTEMP",.F.,"000001") //codigo do grupo de usuario
    Local aBotoes := {}
    Local n1 := 0

    Local aBotBKP := aClone(PARAMIXB[2])  // Array com botões caso exist
    CONOUT("STOP")
    if 	 aScan(aGroUsr,{|x| AllTrim(x) == AllTrim(cGRPMnt)}) == 0 .and. (RetCodUsr() != "000000")
        Set Key VK_F7 To
        For N1 := 1 to Len(aBotBKP)
            IF  ascan(aBotBKP,{|x| Trim(x[1]) == "ESTOMOVI"}) != N1
                AADD(aBotoes,aBotBKP[N1])
            ENDIF

            //"ESTOMOVI"
        Next N1

    ELSE
        aBotoes :=  aBotBKP
    ENDIF


Return( aClone( aBotoes ) )
