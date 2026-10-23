#INCLUDE "TBICONN.CH"
#INCLUDE "FWMVCDEF.CH"
#Include 'PROTHEUS.CH'
#Include 'TOTVS.CH'


/*/{Protheus.doc} DLP73F02

    Função que será responsavel por cadastrar os clientes e pedidos de venda em outras filiais

    @author  Name
    @example Example
    @param   [Parameter_Name],Parameter_type,Parameter_Description
    @return  Return
    @table   Tables
    @since   12-02-2020
/*/


user function DLP73F03()



Return Nil




//-------------------------------------------------------------------
/*/{Protheus.doc} MyCRMA980
Função de exemplo para utilização da rotina automática de Clientes.
@param      Nenhum
@return Nenhum
@author     Squad CRM / FAT
@version    12.1.17 / Superior
@since      24/05/2017
/*/
//-------------------------------------------------------------------
User Function fCadCli(aPars,xOper,aEmpFil)


    Local aAI0Auto  := {}
    Local nOpcAuto  := xOper
    Local lRet      := .T.
    Local oModel	:= Nil
    Private axSA1Auto  := {}
    Private lMsErroAuto := .F.
    Private l030Auto   	:= .F. // Variavel usada para saber se é rotina automática

    PREPARE ENVIRONMENT EMPRESA aEmpFil[1] FILIAL aEmpFil[2] MODULO aEmpFil[3] TABLES "SA1"

    CONOUT("ANTES - CEMPANT "+ cEmpAnt)
    CONOUT("ANTES - FILANT "+ cFilAnt)
    RpcSetEnv( aEmpFil[1],aEmpFil[2],,,,,{})
    CONOUT("APOS - CEMPANT "+ cEmpAnt)
    CONOUT("APOS - FILANT "+ cFilAnt)

    If lRet

        //----------------------------------
        // Dados do Cliente
        //----------------------------------

        For nX := 1 To Len( aPars )

            aAdd(axSA1Auto,{aPars[nX][1]     ,aPars[nX][2]              ,Nil})
            //oMBrowse:AddLegend( aCores[nX][1], aCores[nX][2], aCores[nX][3] )

        Next nX

        //---------------------------------------------------------
        // Dados do Complemento do Cliente
        //---------------------------------------------------------
        aAdd(aAI0Auto,{"AI0_SALDO"  ,30                     ,Nil})

        //------------------------------------
        // Chamada para cadastrar o cliente.
        //------------------------------------

        Conout("INI EXECAUTO")

        MSExecAuto({|a,b,c| CRMA980(a,b,c)}, axSA1Auto, nOpcAuto, aAI0Auto)


        If lMsErroAuto

            lRet := lMsErroAuto
            lRetSA1 := .F.
            aAutoErro := GETAUTOGRLOG()
            aObs := TXTERRO(aAutoErro)
            conout(aObs)
            conout("*************** INI ERROR ***************")
            conout(alltrim(cvaltochar(MostraErro())))
            conout("*************** FIM ERROR ***************")
        Else
            Conout("Cliente incluído com sucesso!")
        EndIf

    EndIf
    RpcClearEnv()

    oServer := nil
    RESET ENVIRONMENT
    CONOUT("FIM fCadCli RET" +CVALTOCHAR(lRet))

Return lRet



//-------------------------------------------------------------------------------------------------
/*/{Protheus.doc} fPutPV
Função que executa a rotina automatica (Execauto) do Pedido de Venda
@param      aPar => 1 - CNPJ/CPF | 2 - Num Pedido de Cenda Produto   | 3 - Filial do Pedido Origem
@return 	aRet =>  lRet Variavel de controle de incluiu ou nao o pedido
@author     Squad CRM / FAT
@version    12.1.17 / Superior
@since      08/2019
/*/
//-------------------------------------------------------------------------------------------------
User Function fPutPV(aPars,aEmpFil)
    Local lRet      := .t.
    Local cMVPrdSrv := ""
    Local xCab      := {}
    Local xItens    := {}
    Local xItem     := {}
    Local cCli      := ""
    Local cLj       := ""
    Local aInfPV04  := aPars[7]
    Local cFieldCP  := ""
    Local cFieldCV  := ""
    Local nPar := "0"


    CONOUT("aPars[1][4]" + aPars[4] )
    CONOUT("cMVPrdSrv  " + cMVPrdSrv   )
    CONOUT("aPars[1][3]" + aPars[3] )
    CONOUT("aPars[1][5]" + aPars[5] )


    PREPARE ENVIRONMENT EMPRESA aEmpFil[1] FILIAL aEmpFil[2] MODULO aEmpFil[3] TABLES "SA1,SC5,SC6,SB1,SE4"

    CONOUT("ANTES - CEMPANT "+ cEmpAnt)
    CONOUT("ANTES - FILANT "+ cFilAnt)
    RpcSetEnv( aEmpFil[1],aEmpFil[2],,,,,{})
    CONOUT("APOS - CEMPANT "+ cEmpAnt)
    CONOUT("APOS - FILANT "+ cFilAnt)



    cMVPrdSrv := alltrim(supergetmv("MV_YPRDSRV",.F.,"90020001"))
    // aInfPV04:=fGetItPV({aPars[1][4],cMVPrdSrv,aPars[1][3],aPars[1][5]})
    cCli      := POSICIONE("SA1",3,xFilial("SA1")+aPars[1],"A1_COD" )
    cLj       := POSICIONE("SA1",3,xFilial("SA1")+aPars[1],"A1_LOJA" )

    aadd(xCab,{"C5_TIPO"   ,"N"    ,Nil})
    aadd(xCab,{"C5_CLIENTE",cCli    ,Nil})
    aadd(xCab,{"C5_CLIENT" ,cCli    ,Nil})
    aadd(xCab,{"C5_LOJACLI",cLj     ,Nil})
    aadd(xCab,{"C5_LOJAENT",cLj     ,Nil})

    IF aPars[5] $ '9'
        aadd(xCab,{"C5_CONDPAG","001"   ,Nil})
        For nXI := 1 To Len(aPars[6] )

            aadd(xCab,{aPars[6][nXI][1] , aPars[6][nXI][2],aPars[6][nXI][3]})

        Next nXI
    ELSE
        aadd(xCab,{"C5_CONDPAG","003"   ,Nil})
    endif


    aadd(xItem,{"C6_ITEM"       ,"01"           ,Nil})
    aadd(xItem,{"C6_PRODUTO"    ,aInfPV04[1][1] ,Nil})
    aadd(xItem,{"C6_TES"        ,"503"          ,Nil})
    aadd(xItem,{"C6_QTDVEN"     ,aInfPV04[1][2] ,Nil})
    aadd(xItem,{"C6_PRCVEN"     ,aInfPV04[1][3] ,Nil})
    aadd(xItem,{"C6_PRUNIT"     ,aInfPV04[1][4] ,Nil})
    aadd(xItem,{"C6_VALOR"      ,aInfPV04[1][5] ,Nil})

    aAdd(xItens, xItem)
    lMsErroAuto := .F.

    msExecAuto({|x,y,z|Mata410(x,y,z)},xCab,xItens,3)

    If lMsErroAuto

        lRetPV := .F.

        aAutoErro := GETAUTOGRLOG()
        aObs := TXTERRO(aAutoErro)
        conout(aObs)
        conout("*************** INI ERROR ***************")
        conout(alltrim(cvaltochar(MostraErro())))
        conout("*************** FIM ERROR ***************")
    EndIF

    RpcClearEnv()

    oServer := nil
    RESET ENVIRONMENT
    CONOUT("FIM fCadCli RET" +CVALTOCHAR(lRet))


Return lRet