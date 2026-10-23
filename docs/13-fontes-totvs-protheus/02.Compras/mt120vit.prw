#Include "Protheus.ch"
#Include "RwMake.ch"
#Include "TbiConn.ch"
#Include "totvs.ch"


//user function MT120VIT()
//    Local ExpA1 := ParamIxb[1]
//    Local ExpN2 := ParamIxb[2]    //Customização do usuário para manipulação dos campos do array na seleção da Solicitação de Compras (Item) - F5 no Pedido de Compras.
//
//    IF ExpN2 == 1
//        aadd(ExpA1,"C1_CC")
//    ENDIF
//Return ExpA1
//
//user function  MT120VSC()
//
//
//    Local ExpA1 := ParamIxb[1]
//    Local ExpN2 := ParamIxb[2]    //Customização do usuário para manipulação dos campos do array na seleção da Solicitação de Compras (Item) - F5 no Pedido de Compras.
//    IF ExpN2 == 1
//        aadd(ExpA1,"C1_CC")
//    ENDIF
//Return ExpA1
/*Nao estava compilado*/
USER FUNCTION MT120MAK()

rETURN ({"C1_CC"})

//{"C1_OK","C1_NUM","C1_ITEM","C1_PRO
