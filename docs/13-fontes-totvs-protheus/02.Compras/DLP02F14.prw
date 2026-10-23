#INCLUDE "PROTHEUS.CH"
//-------------------------------------------------------------------
/*/{Protheus.doc} DLP02F14
Função colocada como validação no campo C7_QUANT para validar se a quantidade da solcitação é maior ou igual a quantidade do pedido de compra.
@author  Eduardo Dalitz
@since   25/02/2025
@version 1.0
/*/
//-------------------------------------------------------------------

User function DLP02F14()
    Local aArea:= GetArea()
    Local lRet := .T.
    Local nPnumSC := aScan(aHeader,{|x| AllTrim(x[2]) == 'C7_NUMSC'})
    Local nPItem := aScan(aHeader,{|x| AllTrim(x[2]) == 'C7_ITEMSC'})
    Local nPqtdC7 := aScan(aHeader,{|x| AllTrim(x[2]) == 'C7_QUANT'})
    Local cNumSC := ACOLS[1][nPnumSC]
    Local cNumItem := ACOLS[1][nPItem]
    Local cQtdC7 := ACOLS[1][nPqtdC7]

    IF !EMPTY(ACOLS[1][nPnumSC])
        //C1_FILIAL + C1_NUM + C1_ITEM + C1_ITEMGRD
        DbSelectArea("SC1")
        SC1->(dbSetOrder(1))
        IF SC1->(Dbseek(xFilial("SC1")+cNumSC+cNumItem))
            IF cQtdC7 < SC1->C1_QUANT
                lRet := .F.
                FWAlertWarning("A quantidade do pedido não pode ser menor que a quantidade da solicitação", "Atenção")
            ENDIF
            SC1->(msUnlock())
        ENDIF
        SC1->(DBCloseArea())
    ENDIF

    RestArea(aArea)

Return lRet

