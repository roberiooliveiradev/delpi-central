#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"

user function DLP02F13()

    Local aPergAux  := {}
    lOCAL n1 := 0 as numeric
    Local aGroUsr := UsrRetGrp(UsrRetName(RetCodUsr()),RetCodUsr())
    //Private lMsHelpAuto     := .T.
    //Private lAutoErrNoFile  := .T.
    Private lMsErroAuto     := .F.
    IF aScan(aGroUsr,{|x| AllTrim(x) == "000000"}) == 0
        FWLogMsg("WARN", "", "DLP02F13", "", "", "", ;
		"Usuário sem permissão: " + RetCodUsr())
        FWAlertWarning("Usuário sem permissão para executar a rotina.", "Atenção")
        Return
    endif
    aNumSC :=   fGetSC()
    cNumSol := "152347"
    CMODULO := "EIC"
    nModulo := 17
    // Pergunte("MTA235",.F.)
    For  n1 := 1 to Len(aNumSC)
        cNumSol :=aNumSC[n1]
        aPergAux := {}
        Pergunte("MTA235",.F.,,,,, @aPergAux)
        nModOld := nModulo
        //salva os Perguntes do compras para restaurar depois da execução
        // aPergOld := aClone(aPergAux)
        SetMVValue('MTA235' , 'MV_PAR01' ,  100) //PERCENTUAL MAXIMO ?
        SetMVValue('MTA235' , 'MV_PAR02' , CTOD("01/01/2000") ) //DATA DE EMISSAO DE ?
        SetMVValue('MTA235' , 'MV_PAR03' , CTOD("31/12/2200")    ) //DATA DE EMISSAO ATE ?
        SetMVValue('MTA235' , 'MV_PAR04' , cNumSol ) //SOLIC/PEDIDO DE ?
        SetMVValue('MTA235' , 'MV_PAR05' ,  cNumSol) //SOLIC/PEDIDO ATE' ?
        SetMVValue('MTA235' , 'MV_PAR06' ,  space(15)) //PRODUTO DE ?
        SetMVValue('MTA235' , 'MV_PAR07' ,  REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO"))) //PRODUTO ATE' ?
        SetMVValue('MTA235' , 'MV_PAR08' , 5 ) //ELIMINA RESIDUO POR ?
        SetMVValue('MTA235' , 'MV_PAR09' , REPLICATE(" ",GETSX3CACHE("A2_COD","X3_TAMANHO")) ) //FORNECEDOR DE ?
        SetMVValue('MTA235' , 'MV_PAR10' ,  REPLICATE("Z",GETSX3CACHE("A2_COD","X3_TAMANHO")) ) //FORNECEDOR ATE' ?
        SetMVValue('MTA235' , 'MV_PAR11' ,CTOD("01/01/2000") ) //DATA DE ENTREGA DE ?
        SetMVValue('MTA235' , 'MV_PAR12' ,CTOD("31/12/2200")    ) //DATA DE ENTREGA ATE ?
        SetMVValue('MTA235' , 'MV_PAR13' , 1 ) //ELIMINA SC COM OP ?
        SetMVValue('MTA235' , 'MV_PAR14' , space(4) ) //A PARTIR DO ITEM ?
        SetMVValue('MTA235' , 'MV_PAR15' , REPLICATE("Z",4) ) //ATÉ O ITEM ?
        SetMVValue('MTA235' , 'MV_PAR16' ,  2) //CONTABILIZA PEDIDO ?
        SetMVValue('MTA235' , 'MV_PAR17' ,  2) //MOSTRA LANC CONTAB ?

        __SaveParam("MTA235", aPergAux)
        MV_PAR01:=  100//PERCENTUAL MAXIMO ?
        MV_PAR02:= CTOD("01/01/2000")  //DATA DE EMISSAO DE ?
        MV_PAR03:= CTOD("31/12/2200")     //DATA DE EMISSAO ATE ?
        MV_PAR04:= cNumSol  //SOLIC/PEDIDO DE ?
        MV_PAR05:=  cNumSol //SOLIC/PEDIDO ATE' ?
        MV_PAR06:=  space(15) //PRODUTO DE ?
        MV_PAR07:=  REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO")) //PR
        MV_PAR08:= 5  //ELIMINA RESIDUO POR ?
        MV_PAR09:= REPLICATE(" ",GETSX3CACHE("A2_COD","X3_TAMANHO"))  //FO
        MV_PAR10:=  REPLICATE("Z",GETSX3CACHE("A2_COD","X3_TAMANHO"))  //F
        MV_PAR11:=CTOD("01/01/2000") //DATA DE ENTREGA DE ?
        MV_PAR12:=CTOD("31/12/2200")     //DATA DE ENTREGA ATE ?
        MV_PAR13:= 1  //ELIMINA SC COM OP ?
        MV_PAR14:= space(4) //A PARTIR DO ITEM ?
        MV_PAR15:= REPLICATE("Z",4) //ATÉ O ITEM ?
        MV_PAR16:=  2//CONTABILIZA PEDIDO ?
        MV_PAR17:=  2 //MOSTRA LANC CONTAB ?

        lMSErroAuto := .F.
        lReturn := .F.
        MsExecAuto({|x| lReturn := MATA235(x)}, .T. )

        If !lReturn .Or. lMSErroAuto

            Mostraerro()
            //aLog     := GetAutoGrLog()
            //for nx := 1 to len(aLog)
            //    cMsgAuto += Alltrim(aLog[nx]) + ENTER
            //Next
        EndIf
    Next n1
    nModulo := nModOld
    CMODULO := "COM"
Return


STATIC FUNCTION fGetSC()

    ANUMSC := {}
    AADD(ANUMSC,'38388')
    AADD(ANUMSC,'146103')
    AADD(ANUMSC,'147069')
    AADD(ANUMSC,'147232')
    AADD(ANUMSC,'149024')
    AADD(ANUMSC,'149103')
    AADD(ANUMSC,'149504')
    AADD(ANUMSC,'149734')
    AADD(ANUMSC,'149954')
    AADD(ANUMSC,'150385')
    AADD(ANUMSC,'150552')
    AADD(ANUMSC,'151833')
    AADD(ANUMSC,'151871')
    AADD(ANUMSC,'151937')
    AADD(ANUMSC,'152245')
    AADD(ANUMSC,'152245')
    AADD(ANUMSC,'152494')
    AADD(ANUMSC,'152669')
    AADD(ANUMSC,'153280')
    AADD(ANUMSC,'153661')
    AADD(ANUMSC,'153772')
    AADD(ANUMSC,'153955')
    AADD(ANUMSC,'154089')
    AADD(ANUMSC,'154090')
    AADD(ANUMSC,'154833')
    AADD(ANUMSC,'155787')
    AADD(ANUMSC,'156116')
    AADD(ANUMSC,'156763')
    AADD(ANUMSC,'156783')
    AADD(ANUMSC,'156810')
    AADD(ANUMSC,'156844')
    AADD(ANUMSC,'156872')
    AADD(ANUMSC,'156965')
    AADD(ANUMSC,'157191')
    AADD(ANUMSC,'157534')
    AADD(ANUMSC,'157534')
    AADD(ANUMSC,'158507')
    AADD(ANUMSC,'158756')
    AADD(ANUMSC,'158917')
    AADD(ANUMSC,'159043')
    AADD(ANUMSC,'159102')
    AADD(ANUMSC,'159109')
    AADD(ANUMSC,'159152')
    AADD(ANUMSC,'159160')
    AADD(ANUMSC,'159202')
    AADD(ANUMSC,'159234')
    AADD(ANUMSC,'160513')
    AADD(ANUMSC,'159601')


return ANUMSC
