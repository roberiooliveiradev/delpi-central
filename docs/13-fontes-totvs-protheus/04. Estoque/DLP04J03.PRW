#INCLUDE "FWEVENTVIEWCONSTS.CH"
#Include 'Protheus.ch'
#Include 'TBICONN.ch'


USER FUNCTION DLP04J03()
    Local PARAMIXB := .t. //-- Caso a rotina seja rodada em batch(.T.), senão (.F.)
    Local cProdDe   := REPLICATE(" ",GETSX3CACHE("B1_COD","X3_TAMANHO"))
    Local cProdAte  := REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO"))
    Pergunte("MTA300",.F.)
    SetMVValue("MTA300","MV_PAR01","  ")
    SetMVValue("MTA300","MV_PAR02","ZZ")
    SetMVValue("MTA300","MV_PAR03",cProdDe)
    SetMVValue("MTA300","MV_PAR04", cProdAte )
    SetMVValue("MTA300","MV_PAR05",3)
    SetMVValue("MTA300","MV_PAR06", 3 )
    SetMVValue("MTA300","MV_PAR07", 2 )
    SetMVValue("MTA300","MV_PAR08", 2 )

    /*  MTA300  01	Do  Armazem ?
        MTA300  02	Ate o Armazem ?
        MTA300  03	Do Produto ?
        MTA300  04	Ate o Produto ?
        MTA300  05	Zera o saldo de produtos MOD ?
        MTA300  06	Zera o CM de produtos MOD ?
        MTA300  07	Travar Registros SB2 ?
    MTA300  08	Seleciona Filiais ?    */
    cTit := "DLP04J03 - mata300 "+cFilAnt
    cMsg:="Gda Ini"
    EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, "Z22",FW_EV_LEVEL_INFO,"",cTit,cMessage,.T.)

    MSExecAuto({|x| mata300(x)},PARAMIXB)

Return




Static Function Scheddef()

    Local aParam  := {}

    aParam := { "P",;           //Tipo R para relatorio P para processo
        "",;      //Pergunte do relatorio, caso nao use passar ParamDef
        ,;              //Alias
        ,;              //Array de ordens
        }               //Titulo

Return aParam
