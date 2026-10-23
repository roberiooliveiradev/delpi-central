#Include "Protheus.ch"
#Include "RwMake.ch"
#Include "TbiConn.ch"
#Include "totvs.ch"
#INCLUDE "TOPCONN.CH"


USER FUNCTION DLPXFUNA()

    APAR :={}
    AADD(APAR,"MV_IMPXML")
    AADD(APAR,"MV_XMLCFPC")
    AADD(APAR,"MV_XMLCFBN")
    AADD(APAR,"MV_XMLCFDV")
    AADD(APAR,"MV_XMLCFND")
    AADD(APAR,"MV_XMLCFNO")
    AADD(APAR,"MV_CTECLAS")
    AADD(APAR,"MV_XMLPFCT")
    AADD(APAR,"MV_XMLTECT")
    AADD(APAR,"MV_XMLCPCT")
    AADD(APAR,"MV_DIVIZER")
    AADD(APAR,"MV_COMCOL1")
    AADD(APAR,"MV_COMCOL2")
    AADD(APAR,"MV_COMCOL3")
    AADD(APAR,"MV_MSGCOL")
    AADD(APAR,"MV_TCNEW")
    AADD(APAR,"MV_FILREP")
    AADD(APAR,"MV_XMLRATD")
    AADD(APAR,"MV_COLEDI")
    AADD(APAR,"MV_COLTEG")
    AADD(APAR,"MV_COMCOL1")
    AADD(APAR,"MV_COMCOL2")
    AADD(APAR,"MV_ERRCTEG")
    AADD(APAR,"MV_COLVCHV")
    AADD(APAR,"MV_VLRCTE")
    AADD(APAR,"MV_XMLCAUT")
    Local  N1 := 0

    dbSelectArea("SX6")
    SX6->(dbSetOrder(1))

    For N1 := 1 to Len(APAR)
        cChave := space(2) + APAR[n1]
        If SX6->(dbSeek(cChave))
            cTipo := AllTrim(SX6->X6_TIPO)
            cStr := "PARAMETRO | "+ ALLTRIM(SX6->X6_VAR)+" | TIPO "+cTipo+" | "+ Alltrim(X6Conteud())
            CONOUT(cStr)
        else
            cStr:= "NAO ACHOU "+cChave
            CONOUT(cStr)
        endif
    Next N1

RETURN

USER FUNCTION DLPXFUNB()

    Local cLockName As Character
    cLockName := cEmpAnt + ' - FINA717'
    UnLockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ )
    UnLockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ )
    F717Pagar()
    F718Processa()
    cLockName := cEmpAnt + ' - FINA718'
    UnLockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ )
    UnLockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ )
    // cRotSch := "FINA713('" + cEmpAnt + "')"
    // cCodSch := FwSchdByFunction(cRotSch)
    // CONOUT("STOP")

    // Local aArea   := GetArea()
    // Local cCodigo := ''

    // Begin Transaction
    //     //Pegando o último código do cliente conforme a SXE / SXF
    //     cCodigo := GetSXENum('SA2', 'A2_COD')
    //     //cCodigo :=  GetNumSC7(.T.)

    //     //Perguntando se deseja confirmar esse código, para confirmar e atualizar as tabelas SXE / SXF
    //     If MsgYesNo("Deseja confirmar o código "+cCodigo+"?", "Atenção")
    //         ConfirmSX8()

    //         //Senão, volta a numeração onde estava
    //     Else
    //         RollBackSX8()
    //     EndIf
    // End Transaction

    // RestArea(aArea)
Return




USER FUNCTION DLPXFUNC(cCodProd)

    Local aArea   := GetArea()
    Local cCodigo := ''

    // CONOUT("STOPS")
    //nRetQtd := posicione("SB2",1,XFILIAL("SB2")+CELL(cCodProd),"B2_QATU")
    Begin Transaction
        //Pegando o último código do cliente conforme a SXE / SXF
        cCodigo := GetSXENum('SA2', 'A2_COD')
        //  cCodigo :=  GetNumSC7(.T.)

        //Perguntando se deseja confirmar esse código, para confirmar e atualizar as tabelas SXE / SXF
        If MsgYesNo("Deseja confirmar o código "+cCodigo+"?", "Atenção")
            ConfirmSX8()

            //Senão, volta a numeração onde estava
        Else
            RollBackSX8()
        EndIf
    End Transaction

    RestArea(aArea)
Return nRetQtd
