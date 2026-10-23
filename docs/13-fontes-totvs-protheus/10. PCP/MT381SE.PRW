
#include "protheus.ch"

uSER FUNCTION MT381SE()
    lOCAL nPosCod    := aScan(aHeader,{|aX| AllTrim(aX[2]) == "D4_COD"})
    Local lRet := .t.

    cCodPro := aCols[n,nPosCod]

    dbSelectArea("SBZ")
    SBZ->(dbSetOrder(1))
    SBZ->(dbSeek(xFilial("SBZ")+cCodPro))
    RecLock('SBZ',.F.)
    SBZ->BZ_DTINV := DATE()
    SBZ->BZ_DTPTPD := CToD("")
    SBZ->(MsUnLock())

Return lRet
