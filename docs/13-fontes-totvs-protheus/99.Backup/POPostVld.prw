#INCLUDE "TOTVS.CH"

User Function POPostVld()
    Local cJson     := PARAMIXB[1]
    Local oJson     := JsonObject():New()
    Local aRet      := {}

    CONOUT("POPostVld")
    //Converte a string JSON para objeto JSON, para que seja possível manipular os dados.
    oJson:FromJson(cJson)

    // If oJson["FORMCODE"] == "FORMOP"
    //     If oJson["C2_TPPR"] == "I"
    //         aRet := {.T., ""}
    //     Else

    //     EndIf
    // EndIf
    aRet := {.F., "nao permite a inclusao da op DEIVID"}
    //Limpa da memória o objeto Json utilizado.
    FREEOBJ( oJson )

Return aRet
