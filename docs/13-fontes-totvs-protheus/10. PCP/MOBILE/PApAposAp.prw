#INCLUDE "TOTVS.CH"

User Function PApAposAp()

    Local aArray     := {}
    Local lRet       := .T.

    Local cRecno     := PARAMIXB[1] //RECNO da SD3
    Local oJson      := PARAMIXB[2] //Objeto do Json
    Local cResponse  := PARAMIXB[3] //String do Json

    //Se o lRet for False o cResponse deve conter a mensagem do problema para ser retornado na API
    //Se o lRet for True o cResponse deve conter a String do Json para ser retornado na API

    AADD(aArray, {lRet, cResponse})
    conout("PApAposAp - gda bateu ")
Return aArray
