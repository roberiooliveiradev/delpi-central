#Include "TOTVS.ch"

User Function MTA010MNU()

    Local aFWSM0 :=  FWLoadSM0(.t.,.t.)
    // Local  aUsuarios := AllUsers()
    Local cCodUsr := RetCodUsr()
    Local AllFil := .F.
    // Local  nLinEnc:= aScan(aUsuarios, {|x| x[1][1] == cCodUsr })
    Local nCnt := 0
    lOCAL n1 := 0
    Local cUsrPer01 := SuperGetMV("MV_USR4F03",.f.,"000000_000008_000072_000092")

    For n1 := 1 to Len(aFWSM0)

        if aFWSM0[n1][1] $ cEmpant .and. aFWSM0[n1][11]

            nCnt ++

        endif
    Next n1
    AllFil :=  iif( nCnt >1 ,.t.,.f.)
    // if len(aUsuarios[nLinEnc][2][6]) >0

    //     IF  "@@@@" $ aUsuarios[nLinEnc][2][6]
    //         AllFil := .T.
    //     ELSEIF  len(aUsuarios[nLinEnc][2][6]) >1

    //         For n1 := 1 to Len(aUsuarios[nLinEnc][2][6])
    //             if cEmpAnt $ substr(aUsuarios[nLinEnc][2][6][n1],1,2)
    //                 nCnt ++
    //             endif

    //             if nCnt >1
    //                 AllFil := .T.
    //             endif
    //         Next n1
    //         AllFil := .T.
    //     endif
    // endif

    if AllFil

        conout("teste")
        AAdd(aRotina, {"Consulta Estoque Geral", "U_MT010F6", 0, 2, 0, NIL})
        Set Key VK_F6 TO U_MT010F6()

    endif
    IF cCodUsr $ cUsrPer01
        AAdd(aRotina, {"Copia Prod EMP", "U_DLP04F03", 0, 3, 0, NIL})
    endif
Return (NIL)





USER Function MT010F6()
    Local cFilBkp := cFilAnt
    Set Key VK_F6 TO
    If FWModeAccess("SB1")=="E"
        cFilAnt := SB1->B1_FILIAL
    EndIf
    u_DLP04F01(SB1->B1_COD)
    cFilAnt := cFilBkp
    Set Key VK_F6 TO U_MT010F6()
Return Nil
