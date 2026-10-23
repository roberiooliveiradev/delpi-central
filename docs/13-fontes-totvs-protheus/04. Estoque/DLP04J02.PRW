
#Include 'Protheus.ch'
#Include 'TBICONN.ch'

USER FUNCTION DLP04J02(cEmpJob,cFilJob)

    Local aArea     := getarea()
    Local aAreaSM0	:= SM0->(GetArea())
    //Local nPB1Cod := ascan(aSB1,{|x| Trim(x[2]) == "B1_COD"})
    Local lReclock := Nil
    DEFAULT aSB1 := {}
    PRIVATE lMsErroAuto := .F.
    Private INCLUI := .T.
    Private cRootPath 	:= AllTrim(GetSrvProfString("RootPath",""))
    Private  cLocKey := "DLP04J02"
    Private  lLock   := .f.

    DEFAULT cEmpJob	:= "01"
    DEFAULT cFilJob	:= "01"
    CONOUT("Chamou o Job DLP04J01")
    //-- Evita que se consuma licenca
    RpcSetType( 3 )

    PREPARE ENVIRONMENT EMPRESA cEmpJob FILIAL cFilJob MODULO "EST"
    u_D04J02A()
    CONOUT("EMPRESA " + CEMPANT)
    CONOUT("FILIAL  " + CFILANT)


    RESET ENVIRONMENT
    RESTAREA(aArea)
    RESTAREA(aAreaSM0)

RETURN


/*/{Protheus.doc} D04J02A
Gera chave para travar e poder executar as rotinas e faz a baixa dos demais servicos
@type function
@version
@author Gabriel AraЗjo
@since 24/09/2023
@return variant, return_description
/*/
user Function D04J02A()
    Local  cLocKey := "DLP04J02"
    Local cRootPath 	:= AllTrim(GetSrvProfString("RootPath",""))
    lLock := LockByName(cLocKey,.F.,.F.)
    cSrvpatch := cRootPath+"\jobcm\"
    cArq1 :="01_Parar_Servicos.bat"
    cArq2 :="02_Iniciar_Servicos.bat"
    //verifica se foi possivel travar  via semaforo e pode executar

    conout("cSrvpatch =>"+cSrvpatch)
    conout("cArq1 =>"+cArq1)
    if lLock

        //WaitRunSrv( cRootPath + "Install\RService.bat" , .T. , cRootPath + "Install\" )
        WaitRunSrv( cSrvpatch + cArq1, .T. ,cSrvpatch )

    endif

RETURN




// (lLock := LockByName(cLocKey,.F.,.F.))
//
//  If lLock
//      UnLockByName(cLocKey,.F.,.F.)
//  EndIf
//
//
//  user Function DLP02J01(cEmpJob,cFilJob)
//
//      Local cHoraIni  := ""
//      Local cHoraFim  := ""
//      Local cHoraUlt  := "00:00:01"
//      Local cHora     := cHoraUlt
//      Local cAtivo    := "ON"
//
//      Local nIntervalo:= 0
//
//      DEFAULT cEmpJob	:= "01"
//      DEFAULT cFilJob	:= "01"
//      CONOUT("Chamou o Job DLP02J01")
//      //-- Evita que se consuma licenca
//      RpcSetType( 3 )
//
//      PREPARE ENVIRONMENT EMPRESA cEmpJob FILIAL cFilJob MODULO "FAT"
//
//      CONOUT("EMPRESA " + CEMPANT)
//      CONOUT("FILIAL  " + CFILANT)
//
//      JobMani()
//
//      //GetMDeSinc(2)
//      //зддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддд©
//      //ЁEspera                                                             Ё
//      //юддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддды
//      Sleep(3000)
//
//      //  If KillApp()
//      //      Exit
//      //  EndIf
//
//      //здддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддд©
//      //ЁFinalisando o ambiente para execucao                                    Ё
//      //юдддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддды
//      RESET ENVIRONMENT
