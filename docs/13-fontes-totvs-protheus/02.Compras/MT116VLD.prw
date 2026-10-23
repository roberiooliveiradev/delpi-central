#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "rwmake.ch"
#INCLUDE "topconn.ch"
#INCLUDE "colors.ch"

/*nao compilar*/
User Function MT116VLD()
    Local lRet := .t.

    Local nFormul	  :=PARAMIXB[1]
    Local cNFiscal	  :=PARAMIXB[2]
    Local cSerie	  :=PARAMIXB[3]
    Local cFornecedor :=PARAMIXB[4]
    Local cLoja		  :=PARAMIXB[5]

    Local cUFFor := POSICIONE("SA2",1,XFILIAL("SA2")+cFornecedor+cLoja,"A2_EST")
    IF nFormul ==2 .AND. c116UFOri != cUFFor

        c116UFOri :=  cUFFor

    ENDIF


Return lRet
