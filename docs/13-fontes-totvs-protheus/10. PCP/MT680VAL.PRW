#INCLUDE "PROTHEUS.CH"

User Function MT680VAL()
    //Local cLocal:=PARAMIXB[1]
    Local lRet := .T.
    IF cEmpAnt =="01"
        conout("MT680VAL GDA")
        CONOUT("M->H6_HORAINI: " + M->H6_HORAINI)
        If Empty(M->H6_HORAINI)
            conout("entrou no horaini")
            lRet := .F.
            //AutoGrLog ("Hora inicial não informada!!")
            Help(,,"DELPI PCP  : ",,upper("Hora Inicial não informada!!"),1,0, NIL, NIL, NIL, NIL, NIL, {"Texto da Solução"})
            // SetRestFault(400, EncodeUTF8("Hora fim não informada!!"))
            // FWAlertError("Hora Inicio não informada!!", "Delpi PCP")
        ENDIF

        CONOUT("M->H6_HORAFIN: " + M->H6_HORAFIN)
        If Empty (M->H6_HORAFIN) .and. lRet
            lRet := .F.
            conout("entrou no H6_HORAFIN")
            //AutoGrLog ("Hora fim não informada!!")
            //  Help(' ',1,"help",,"Hora fim não informada!!",2,0)
            //  SetRestFault(400, EncodeUTF8("Hora fim não informada!!"))
            //  FWAlertError("Hora fim não informada!!", "Delpi PCP")
            Help(,,"DELPI PCP : ",,upper("Hora Final não informada!!"),1,0, NIL, NIL, NIL, NIL, NIL, {"Texto da Solução"})
        ENDIF
        CONOUT("M->H6_HORAFIN:" + M->H6_HORAFIN)
        If Empty (M->H6_OPERADO) .and. lRet
            lRet := .F.
            conout("entrou no H6_OPERADO")
            //AutoGrLog ("Hora fim não informada!!")
            //  Help(' ',1,"help",,"Hora fim não informada!!",2,0)
            //  SetRestFault(400, EncodeUTF8("Hora fim não informada!!"))
            //  FWAlertError("Hora fim não informada!!", "Delpi PCP")
            Help(,,"DELPI PCP : ",,upper("Operador não informado!!"),1,0, NIL, NIL, NIL, NIL, NIL, {"Texto da Solução"})
        ENDIF

        If lRet
            fImpEti()
        endif
    endif

Return lRet



STATIC FUNCTION fImpEti()
    IF cEmpAnt =="01"
        conout("fImpEti")

        cDsCT1 := ""
        cDsCT2 := ""
        cDsCT3 := ""
        sDesRec := ""
        cCDRec := ""
        cOPApont := ""
        cPrdPA := ""
        cPrdApont := ""
        cTpApon   := ""
        cDescAp   := ""
        cCDUsr := ""
        dDtApont := ctod("")
        cHrApont := ""
        nQtdTOP     := 0.00
        cCDRot      :=""
        /*Busca Codigo do Recurso*/
        // nPos := aScan(aDados, {|x| x[1] == "H6_RECURSO"})
        cCDRec      :=  M->H6_RECURSO//  aDados[nPos][2]

        /*Busca PA da OP */
        // nPos := aScan(aDados, {|x| x[1] == "H6_OP"})
        cOPApont :=    M->H6_OP


        cOpPA := substr( cOPApont,1,6)+"01001"
        dbSelectArea("SC2")
        SC2->(dbSetOrder(1))
        If   SC2->(dBSeek(xFilial("SC2")+cOpPA))
            cPrdPA:= SC2->C2_PRODUTO
        endif

        conout("  M->H6_OP "+M->H6_OP)
        conout(funname())
        /*Op Apontamento*/

        dbSelectArea("SC2")
        SC2->(dbSetOrder(1))
        If   SC2->(dBSeek(xFilial("SC2")+cOPApont))
            cPrdApont := SC2->C2_PRODUTO
            cTpApon     :=  posicione("SB1",1,XFILIAL("SB1")+SC2->C2_PRODUTO,"B1_TIPO" )
            cDescAp     :=  posicione("SB1",1,XFILIAL("SB1")+SC2->C2_PRODUTO,"B1_DESC" )
            nQtdTOP     := SC2->C2_QUANT
            cCDRot      := SC2->C2_ROTEIRO
        endif
        /*Quantidade */
        //nPos := aScan(aDados, {|x| x[1] == "H6_QTDPROD"})
        nQtd := M->H6_QTDPROD *1000

        dbSelectArea("SG2")
        cCHVSG2 := xFilial("SG2")+SC2->C2_PRODUTO+cCDRot+M->H6_OPERAC
        cCHVSG22 := xFilial("SG2")+SC2->C2_PRODUTO+cCDRot
        SG2->( DbSetOrder(1))
        if SG2->( dbSeek(cCHVSG2    ))

            sDesRec :=alltrim(SG2->G2_DESCRI)
            nG2 :=0
            While !SG2->(eof())
                nG2++
                if( SG2->(G2_FILIAL+ G2_PRODUTO+ G2_CODIGO) != cCHVSG22)
                    exit
                endif
                if !empty(cDsCT1)
                    cDsCT1 +=" / "
                endif
                if !empty(cDsCT2)
                    cDsCT2 +=" / "
                endif
                if !empty(cDsCT3)
                    cDsCT3 +=" / "
                endif
                if nG2 <=6
                    cDsCT1 +=  alltrim(SG2->G2_RECURSO)
                elseif nG2 >6 .and. nG2 <=12
                    cDsCT2 +=  alltrim(SG2->G2_RECURSO)
                elseif nG2 >12
                    cDsCT3 +=  alltrim(SG2->G2_RECURSO)
                endif
                SG2->(dbSkip())
            EndDo
        endif

        PswOrder(1)
        If PswSeek( M->H6_OPERADO, .T. )
            cCDUsr  := PswRet()[1][4]
        ENDIF
        //  if UsrExist(M->H6_OPERADO)
        //      // nPos := aScan(aDados, {|x| x[1] == "H6_OPERADO"})
        //      FwGetUserName(M->H6_OPERADO)
        //  endif
        // nPos := aScan(aDados, {|x| x[1] == "H6_DTAPONT"})
        dDtApont   := M->H6_DTAPONT

        // nPos := aScan(aDados, {|x| x[1] == "H6_HORAFIN"})
        cHrApont   := M->H6_HORAFIN
        conout("cPrdPA   ->"      +cPrdPA)
        conout("cPrdApont->"    +cPrdApont)
        conout("cOPApont ->" +cOPApont)
        conout("cTpApon  ->"  +cTpApon)
        conout("cDescAp  ->"  +cDescAp )
        conout("nQtd ->" + cvaltochar(nQtd))
        conout("cCDRec ->"   +cCDRec )
        conout("sDesRec ->"  +sDesRec)
        conout("cCDUsr ->"   +cCDUsr)
        conout("dDtApont ->" +dtoc(dDtApont))
        conout("cHrApont ->"+    cHrApont)
        conout("M->H6_OPERA ->"+    M->H6_OPERAC)
        conout("M->H6_FILIAL ->"+    cFilAnt)
        conout("cEmpAnt "+cEmpAnt)
        if ALLTRIM( M->H6_OPERAC )== '01' .and. alltrim(cFilAnt) $ '02_01' .and. alltrim(cEmpAnt) $ '01'  .and. IsBlind() .AND. nQtdTOP> 0
            conout("VAI IMPRIMIR")
            conout("cEmpAnt "+cEmpAnt)
            //  U_DLP10F09(cPrdPA,cPrdApont,cOPApont,cTpApon,cDescAp,nQtd,cCDRec,sDesRec,cCDUsr,dDtApont,cHrApont,nQtdTOP)

            U_DLP10F09(cPrdPA,cPrdApont,cOPApont,cTpApon,cDescAp,nQtd,cCDRec,sDesRec,cCDUsr,dDtApont,cHrApont,nQtdTOP,;
                cDsCT1 , cDsCT2 , cDsCT3 )

        ENDIF
    ENDIF


Return
