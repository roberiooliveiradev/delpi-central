#INCLUDE "TOTVS.CH"
/*/{Protheus.doc} User Function MA110BUT
Função para adicionar novos botões na SC.
@type  Function
@author  Eduardo Dalitz
@since 19/02/2025
@version P12
@param param_name, param_type, param_descr
@return return_var, return_type, return_description
/*/
User Function MA110BUT()
Local nOpc:= PARAMIXB[1]
Local aBut:= PARAMIXB[2]//Customização Desejada
 
IF nOpc == 4//ALTERA  
    Aadd(aBut,{'dtNece',{|| dtNece()},"Alt dt Necessidade SC","Dt Necessidade"})
ENDIF

Return aBut

Static Function dtNece()
    Local aParamBox := {}
    Local aRet := {}
    Local dDt := Ctod(Space(8)) 
    Local N1 := 0
    Local cNum := SC1->C1_NUM

    aAdd(aParamBox,{1,"Data Necessidade"  ,Ctod(Space(8)),"","","","",50,.T.}) // Tipo data
    //aAdd(aParamBox,{1,"Data Necessidade"  , dDt,"","" ,"","",50,.t.})// Tipo data

    If ParamBox(aParamBox,"Insira a Nova data de Necessidade",@aRet)
        dDt := aRet[1]

        if dDt < date() 
            FWAlertWarning("A data não pode ser menor que a data atual", "Delpi - Solicitação de Compras")
            return
        else

            For N1 := 1 to Len(aCols) // FAZ UM FOR CONFORME O TAMANHO DA LINHAS / ACOLS
                if !GDDeleted(N1)  // VERIFICA SE A LINHA NAO ESTÁ DELETADA
                    DBSelectArea("SC1")
                    SC1->(DBSetOrder(1))
                    If SC1->(DbSeek(xFilial('SC1')+cNum+acols[N1][1])) //C1_FILIAL + C1_NUM + C1_ITEM + C1_ITEMGRD
                        IF ALTERA .AND. SC1->C1_QUANT > SC1->C1_QUJE .AND. EMPTY(SC1->C1_RESIDUO)
                            GDFieldPut("C1_DATPRF", dDt , N1, aHeader, aCols) // PREENCHE O VALOR DO CAMPO 
                        elseif !ALTERA
                            GDFieldPut("C1_DATPRF", dDt , N1, aHeader, aCols) // PREENCHE O VALOR DO CAMPO 
                        ENDIF  
                    ENDIF  
                endif
            Next N1

            GetDRefresh()
        endif
    Endif

Return
