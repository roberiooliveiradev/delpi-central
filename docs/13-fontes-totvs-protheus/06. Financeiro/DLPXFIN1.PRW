#include 'protheus.ch'
#include 'parmtype.ch'


USER FUNCTION DLPXFIN1()
    Local cLockName As Character
    cLockName := cEmpAnt + ' - FINA717 GDA'
    If F717VldUso()
        If LockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ ) // uma execução por vez
            F717Pagar()
            UnLockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ )
        EndIf
    EndIf
RETURN
