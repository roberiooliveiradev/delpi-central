#include "protheus.ch"
#include "parmtype.ch"



User function DLP10G04(cCodProd,nQtdOri)
    nQtdRet :=nQtdOri
    //dbSelectArea("SZ7")
    //SZ7->(dbSetOrder(2))

    //If   SZ7->(dBSeek(xFilial("SZ7")+cIdSZ7))
    //    lCanAlt := .t.
    //    oModelSZ8:SETVALUE("Z8_FATMP",SZ7->Z7_FATMP)
    //    lCanAlt := .f.
    //ENDIF
    dbSelectArea("SBZ")
    SBZ->(dbSetOrder(1))
    If   SBZ->(dBSeek(xFilial("SBZ")+cCodProd))
        if!EMPTY( SBZ->BZ_YQBOP )
            nQtdRet := SBZ->BZ_YQBOP
        endif
    endif
RETURN nQtdRet
