#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "rwmake.ch"
#INCLUDE "topconn.ch"
#INCLUDE "colors.ch"

USER FUNCTION WSMT650A()
    Local aArea := getarea()
    Local aRet  := ParamIXB[1]  //Vetor da OP
    Local oProd := ParamIXB[2]  //Objeto da OP//Customização
    lOCAL nPos := 0
    // nPDATPRI:=  aScan(aRet,{|x| AllTrim(x[1]) == "C2_DATPRI"})
    // nPDATPRF:=  aScan(aRet,{|x| AllTrim(x[1]) == "C2_DATPRF"})
    // if nPDATPRI>0
    //     conout("nPDATPRI " + cvaltochar(aRet[nPDATPRI][2]))
    // endif
    // if nPDATPRF>0
    //     conout("nPDATPRF " + cvaltochar(aRet[nPDATPRF][2]))
    // endif
    nPos :=aScan(aRet,{|x| AllTrim(x[1]) == "C2_NUM"})
    if nPos >0

        CONOUT("POID "+alltrim(oProd:POID )+" C2_NUM "+   alltrim(aRet[nPos][2])      )                        // Data Prevista de Início
    endif
    nPos:=aScan(aRet,{|x| AllTrim(x[1]) == "C2_ITEM"})
    if nPos >0
        CONOUT("POItem "+alltrim(oProd:POItem )+" C2_ITEM "+   alltrim(aRet[nPos][2])      )                        // Data Prevista de Início
    endif

    nPos:=aScan(aRet,{|x| AllTrim(x[1]) == "C2_SEQUEN"})

    if nPos >0
        CONOUT("POSequence "+alltrim(oProd:POItem )+" C2_SEQUEN "+   alltrim(aRet[nPos][2])      )                        // Data Prevista de Início
    endif

    if !Empty(oProd:OrderID)
        CONOUT("ORDERID "+alltrim(oProd:OrderID )         )                        // Data Prevista de Início
    endif
    if !Empty(oProd:IDAPS)
        CONOUT("IDAPS "+alltrim(oProd:IDAPS )         )                        // Data Prevista de Início
    endif
    //CONOUT("PRODUCTIONORDERUNIQUEID "+alltrim(oProd:PRODUCTIONORDERUNIQUEID )         )                        // Data Prevista de Início
    restarea(aArea)
Return( aRet )
