#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"


user Function DLP02J01(cEmpJob,cFilJob)

    Local cHoraIni  := ""
    Local cHoraFim  := ""
    Local cHoraUlt  := "00:00:01"
    Local cHora     := cHoraUlt
    Local cAtivo    := "ON"

    Local nIntervalo:= 0

    DEFAULT cEmpJob	:= "01"
    DEFAULT cFilJob	:= "01"
    CONOUT("Chamou o Job DLP02J01")
    //-- Evita que se consuma licenca
    RpcSetType( 3 )

    PREPARE ENVIRONMENT EMPRESA cEmpJob FILIAL cFilJob MODULO "FAT"

    CONOUT("EMPRESA " + CEMPANT)
    CONOUT("FILIAL  " + CFILANT)

    JobMani()

    //GetMDeSinc(2)
    //зддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддд©
    //ЁEspera                                                             Ё
    //юддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддды
    Sleep(3000)

    //  If KillApp()
    //      Exit
    //  EndIf

    //здддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддд©
    //ЁFinalisando o ambiente para execucao                                    Ё
    //юдддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддддды
    RESET ENVIRONMENT

Return
