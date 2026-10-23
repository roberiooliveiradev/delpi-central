#Include 'Protheus.ch'
#Include 'TBICONN.ch'


USER FUNCTION DLP04J04()
    Local PARAMIXB := .t. //-- Caso a rotina seja rodada em batch(.T.), senão (.F.)


    /*   MTA300  01	Do  Armazem ?
    |    MTA300  02	Ate o Armazem ?
    |    MTA300  03	Do Produto ?
    |    MTA300  04	Ate o Produto ?
    |    MTA300  05	Zera o saldo de produtos MOD ?
    |    MTA300  06	Zera o CM de produtos MOD ?
    |    MTA300  07	Travar Registros SB2 ?
    |    MTA300  08	Seleciona Filiais ?    */

    MSExecAuto({|x| mata215(x)},PARAMIXB)


Return




Static Function Scheddef()

    Local aParam  := {}

    aParam := { "P",;           //Tipo R para relatorio P para processo
        "",;      //Pergunte do relatorio, caso nao use passar ParamDef
        ,;              //Alias
        ,;              //Array de ordens
        }               //Titulo

Return aParam
