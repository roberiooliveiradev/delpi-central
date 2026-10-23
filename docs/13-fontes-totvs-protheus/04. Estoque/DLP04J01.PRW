
#Include 'Protheus.ch'
#Include 'TBICONN.ch'

USER FUNCTION DLP04J01(aSB1,cEmp)

    Local aArea     := getarea()
    Local aAreaSM0	:= SM0->(GetArea())
    Local nPB1Cod := ascan(aSB1,{|x| Trim(x[2]) == "B1_COD"})
    Local lReclock := Nil
    DEFAULT aSB1 := {}
    PRIVATE lMsErroAuto := .F.
    Private INCLUI := .T.

    PREPARE ENVIRONMENT EMPRESA cEmp FILIAL '01'

    conout("INI DLP04J01")
    conout("EMP LOGADA "+ CEMPANT)
    conout("FIM DLP04J01")

    DbSelectArea("SB1")
    DbSetOrder(1)
    conout("chave")
    If  DbSeek(xFilial("SB1")+ aSB1[nPB1Cod][2]    )

        lReclock := .f.
    else
        lReclock :=.t.
    endif
    // FWAlertInfo("Empresa Logada "+ cEmpAnt, "Teste")

    /*MSExecAuto({|x,y| Mata010(x,y)},aSB1,3)

    If !lMsErroAuto
        ConOut("Produto incluído na empresa 02 ")
    Else
        ConOut("Erro na inclusao!")
        MostraErro()
    EndIf*/

    RESET ENVIRONMENT
    RESTAREA(aArea)
    RESTAREA(aAreaSM0)

RETURN
