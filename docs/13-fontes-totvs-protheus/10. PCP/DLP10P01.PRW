#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'


user function DLP10P01()
    lOCAL lRet := .t.

    Local aGroUsr := UsrRetGrp(PswChave(RetCodUsr()),RetCodUsr()) //Retorna um array contendo todos os códigos dos Grupos de Usuário em que o Usuário, passado na função, pertence.
    Local cGRPMnt := supergetmv("MV_DMNTA5",.F.,"000005") //codigo do grupo de usuario PARA ALTERAR O CAMPO PRODUTO X FORNECEDOR


    CONOUT("STOP")
    if 	 aScan(aGroUsr,{|x| AllTrim(x) == AllTrim(cGRPMnt)}) == 0 //.and. (RetCodUsr() != "000000")
        FWAlertError("Sem permissão para alterar este campo. Procure o setor de Engenharia/Orçamentista", "Produto x Fornecedor")
        lRet := .f.
    ENDIF


Return lRet
