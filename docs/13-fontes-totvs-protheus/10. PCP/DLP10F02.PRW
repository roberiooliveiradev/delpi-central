#INCLUDE "PROTHEUS.CH"


USER FUNCtion DLP10F02()

    Local nTam := getsx3cache("C2_PRIOR","X3_TAMANHO")
    lOCAL nCont :=  &(readvar())
    nCont := val( nCont)
    M->C2_PRIOR := PADL(nCont,nTam,"0")

    //STRZERO(nCod, 5, 0)

RETURN .t.