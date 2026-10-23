#INCLUDE "TOTVS.CH"

User Function PApPosAp()
    Local cTipoApon := PARAMIXB[1] //Tipo do apontamento em execução
    Local aDados    := PARAMIXB[2] //Array de dados que será utilizado pelo MATA250 ou MATA681
    Local oModel    := PARAMIXB[3] //Modelo de dados da rotina de apontamento do chão de fábrica
    Local cTipoSFC  := PARAMIXB[4] //Tipo de operação no chão de fábrica

    Local cFormCode := PARAMIXB[5] //Código do Formulário de Apontamento utilizado para chamar o PE
    conout("PApPosAp - gda bateu "+cFormCode)
    //  conout("PApPosAp - gda bateu "+::ActivityCode            )
    if cTipoApon == "3" // Apontamento MATA681
        custom681(@aDados,cFormCode)

    endif

    if cTipoApon == "4" // Apontamento SFCA314
        customSFC(@oModel, cTipoSFC)

    endif
    //
    //  Do Case
    //     //Case cTipoApon == "1" // Apontamento MATA250
    //     //    If cFormCode = "USINAGEM"
    //     //        cust250USI(@aDados)
    //     //    Else
    //     //        custom250(@aDados)
    //     //    EndIf
    //     //Case cTipoApon == "3" // Apontamento MATA681
    //     //    custom681(@aDados)
    //     //Case cTipoApon == "4" // Apontamento SFCA314
    //     //    customSFC(@oModel, cTipoSFC)
    //  EndCase

Return aDados

Static Function custom681(aDados)
    Local cNumOp := ""
    Local nPos   := 0
    Private aInfos := array(8)

    conout("PApPosAp - GDA H6_OP GDA")


    nPosOper  := aScan(aDados, {|x| x[1] == "H6_OPERAC"})
    nPosSeq   := aScan(aDados, {|x| x[1] == "H6_SEQ"})
    nPosOPr   := aScan(aDados, {|x| x[1] == "H6_OP"})
    nPosQt    := aScan(aDados, {|x| x[1] == "H6_QTDPROD"})
    nPosDes   := aScan(aDados, {|x| x[1] == "H6_DESDOBR"})
    nPsPrd    := aScan(aDados, {|x| x[1] == "H6_PRODUTO"})
    nPsDtIni  := aScan(aDados, {|x| x[1] == "H6_DATAINI"})
    nPsDtFin  := aScan(aDados, {|x| x[1] == "H6_DATAFIN"})
    nPsPend  := aScan(aDados, {|x| x[1] == "PENDENTE"})
    if cEmpAnt $"01_05"
        if cEmpAnt =="01"
            fSetEFIC(@aDados)

            CONOUT("GDA - DELPIUES - nPsPend  " + cvaltochar(nPsPend  ))
            if nPsPend> 0
                CONOUT("GDA - DELPIUES - conteudo   " + cvaltochar(aDados[nPsPend][2]  ))
            endif
            CONOUT("nPosOper  " + cvaltochar(nPosOper  ))
            CONOUT("nPosSeq   " + cvaltochar(nPosSeq   ))
            CONOUT("nPosOPr   " + cvaltochar(nPosOPr   ))
            CONOUT("nPosQt    " + cvaltochar(nPosQt    ))
            CONOUT("nPosDes   " + cvaltochar(nPosDes   ))
            CONOUT("nPsPrd    " + cvaltochar(nPsPrd    ))
            CONOUT("nPsDtIni  " + cvaltochar(nPsDtIni  ))
            CONOUT("nPsDtFin  " + cvaltochar(nPsDtFin  ))


            aInfos[1] /*H6_OPERAC*/ :=  aDados[nPosOper][2]
            if nPosSeq >0
                aInfos[2] /*H6_SEQ*/    :=  aDados[nPosSeq][2]
            else
                aInfos[2] /*H6_SEQ*/    :='  '
            endif
            aInfos[3] /*H6_OP*/     :=  aDados[nPosOPr][2]
            aInfos[4] /*H6_QTDPROD*/:=  aDados[nPosQt][2]
            if nPosDes >0
                aInfos[5] /*H6_DESDOBR*/:=  aDados[nPosDes][2]
            else
                aInfos[5] /*H6_DESDOBR*/:=  "000"
            endif
            aInfos[6] /*H6_PRODUTO*/:=  aDados[nPsPrd][2]
            aInfos[7] /*H6_DATAINI*/:=  aDados[nPsDtIni][2]
            aInfos[8] /*H6_DATAFIN*/:=  aDados[nPsDtFin][2]

            ///*Quantidade */
            nPos := aScan(aDados, {|x| x[1] == "H6_QTDPROD"})
            nPos := aScan(aDados, {|x| x[1] == "H6_QTDPROD"})
            nQtd :=  aDados[nPos][2]

            ///*Busca PA da OP */
            nPos := aScan(aDados, {|x| x[1] == "H6_OP"})
            cOPApont :=   aDados[nPos][2]
        ENDIF
        dbSelectArea("SC2")
        SC2->(dbSetOrder(1))
        If   SC2->(dBSeek(xFilial("SC2")+cOPApont))
            aRet := f680SldOper( .t.,.t.,.t.)//SC2->C2_QUANT - SC2->C2_QUJE

            CONOUT("aRet[1]"+CVALTOCHAR( aRet[1] ))
            CONOUT("aRet[2]"+CVALTOCHAR( aRet[2] ))
            CONOUT("nQtd"+CVALTOCHAR( nQtd ))
            IF nQtd < aRet[1]
                cParTot := "P"
                CONOUT("PARCIAL  | "+cParTot)
            ELSE
                cParTot := "T"
                CONOUT("TOTAL | "+cParTot)
            EndIf
        EndIf

        nPos := aScan(aDados, {|x| x[1] == "H6_PT"})
        aDados[nPos][2] := cParTot

    endif

Return Nil


Static Function customSFC(oModel, cTipo)
    Local aErro   := {}
    Local lRet    := .T.
    Local nQtd    := 0
    Local oMdlCYV := oModel:GetModel("CYVMASTER")
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

    If cTipo == "1" // Apontamento de produção.
        dDtApont    :=  oMdlCYV:GetValue("CYV_DTRP")
        cHrApont    :=  oMdlCYV:GetValue("CYV_HRRP")
        cCDUsr      :=  oMdlCYV:GetValue("CYV_CDUSRP")
        cCDRec      :=  oMdlCYV:GetValue("CYV_CDMQ")
        //Recupera quantidade reportada do apontamento
        nQtd := oMdlCYV:GetValue("CYV_QTATRP")
        cOPApont := oMdlCYV:GetValue("CYV_NRORPO")
        dbSelectArea("SC2")
        SC2->(dbSetOrder(1))
        If   SC2->(dBSeek(xFilial("SC2")+cOPApont))
            cPrdApont := SC2->C2_PRODUTO
            cTpApon     :=  posicione("SB1",1,XFILIAL("SB1")+SC2->C2_PRODUTO,"B1_TIPO" )
            cDescAp     :=  posicione("SB1",1,XFILIAL("SB1")+SC2->C2_PRODUTO,"B1_DESC" )
        endif
        cOpPA := substr( cOPApont,1,6)+"01001"
        If   SC2->(dBSeek(xFilial("SC2")+cOpPA))
            cPrdPA:= SC2->C2_PRODUTO
        endif
        DbSelectArea("SH1")
        SH1->( DbSetOrder(1))
        IF SH1->(DbSeek(xFilial('SH1')+cCDRec))
            sDesRec := SH1->H1_DESCRI
        EndIf

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



        //U_DLP10F09(cPrdPA,cPrdApont,cOPApont,cTpApon,cDescAp,nQtd,cCDRec,sDesRec,cCDUsr,dDtApont,cHrApont)
        //Recupera quantidade reportada do apontamento
        // nQtd := oMdlCYV:GetValue("CYV_QTATRP")

        // //Soma +1 na quantidade reportada do apontamento
        // lRet := oMdlCYV:SetValue("CYV_QTATRP", nQtd + 1)
        // If !lRet
        //     aErro := oModel:GetErrorMessage()
        //     VarInfo("aErro:", aErro)
        // EndIf
        //


        //ElseIf cTipo == "2" // Início de apontamento
        //    //Adiciona uma informação na coluna CYV_CDRE
        //    lRet := oMdlCYV:SetValue("CYV_CDRE", "RF_TESTE")
        //    If !lRet
        //        aErro := oModel:GetErrorMessage()
        //        VarInfo("aErro:", aErro)
        //    EndIf
        //ElseIf cTipo == "3" // Abandono de apontamento
        //    //Adiciona uma informação na coluna CYV_CDRE
        //    lRet := oMdlCYV:SetValue("CYV_CDRE", "RF_TESTE3")
        //    If !lRet
        //        aErro := oModel:GetErrorMessage()
        //        VarInfo("aErro:", aErro)
        //    EndIf
    EndIf

Return Nil



/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡„o    ³ A680SldOper³ Autor ³Marcelo Iuspa          ³ Data ³ 11.10.03 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡„o ³ Calcula quanto posso produzir numa operacao                  ³±±
±±³          ³                                                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MATA680                                                      ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
*/
static Function f680SldOper(lH8Quant,lSomaPerda,lVlOperAnt)
    Local aSavAre   := {SH6->(GetArea()), GetArea()}
    Local cAlias	:= "SH6"
    Local nProd     := 0
    Local nPerda    := 0
    Local aOperAnt  := f680OperAnt()
    Local cOperAnt  := aOperAnt[1]
    Local cSeqAnt   := aOperAnt[2]
    Local nQtdRet   := 0
    Local cOldParctot:="T"
    Local lH6PtAtual
    Local aAreaSH6	:= NIL
    Local nVlAnt    := 0
    Local cStatusAux := ""


    Default lH8Quant   := .F.
    Default lSomaPerda := .F.
    Default lVlOperAnt := .T.

    dbSelectArea("SH6")
    dbSetOrder(1)



    If !lVlOperAnt //Verifica somente o saldo da operacao
        cOperAnt := NIL
        cSeqAnt  := NIL
    EndIf

    If cOperAnt == Nil
        If (SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN+SC2->C2_ITEMGRD) != aInfos[3]
            dbSelectArea("SC2")
            dbSeek(xFilial("SC2")+aInfos[3])
        EndIf
        nProd := SC2->C2_QUANT
    EndIf
    cFilSH6 := XFILIAL("SH6")
    cAlias := GetNextAlias()
    BeginSql Alias cAlias
        SELECT
            H6_FILIAL,
            H6_OP,
            H6_OPERAC,
            H6_SEQ,
            H6_QTDPERD,
            H6_QTDPROD,
            H6_PT,
            H6_DESDOBR
        FROM
            %table:SH6% SH6
        WHERE
            SH6.H6_FILIAL = %Exp:cFilSH6%
            AND SH6.H6_OP = %Exp:aInfos[3]%
            AND SH6.H6_OPERAC <= %Exp:aInfos[1]%
            AND SH6.H6_SEQ <= %Exp:aInfos[2]%
            AND SH6.%NotDel%
        ORDER BY
            %Order:SH6%
    EndSql
    //
    //

    aDados := GetLastQuery()

    //Mostra mensagem com todas as informações capturadas

    conout(aDados[1])
    conout( aDados[2])
    dbSelectArea(cAlias)
    conout("anteswhile "+aInfos[3])
    conout("CALIAS |"+ (cAlias)->H6_FILIAL + (cAlias)->H6_OP+"|" )
    conout("CALIAS |"+ (cAlias)->H6_OPERAC + (cAlias)->H6_SEQ  )
    conout("CVAR |"+ cFilSH6 + aInfos[3]+"|"  )

    IF  (cAlias)->H6_FILIAL + (cAlias)->H6_OP ==cFilSH6 + aInfos[3]
        conout("INFO  000")
    ENDIF
    IF  (cAlias)->H6_OPERAC <=   aInfos[1]
        conout("INFO  001")
    ENDIF
    While ! Eof() .And. ALLTRIM( (cAlias)->H6_FILIAL + (cAlias)->H6_OP) ==ALLTRIM(cFilSH6 + aInfos[3]) .And. ALLTRIM((cAlias)->H6_OPERAC + (cAlias)->H6_SEQ)  <=   aInfos[1]+ aInfos[2]
        conout("entrou 0")
        nProdOper := 0
        If ALLTRIM((cAlias)->H6_OPERAC + (cAlias)->H6_SEQ) < ALLTRIM( aInfos[1]  +   aInfos[2])
            If lSomaPerda
                nProd 		+= (cAlias)->H6_QTDPERD
                cOldParctot	:= (cAlias)->H6_PT
                nProdOper := nProd
            EndIf
        EndIf

        If cOperAnt # Nil .And. (cAlias)->H6_OPERAC + (cAlias)->H6_SEQ == cOperAnt + cSeqAnt .and. mv_par07 != 3
            conout("entrou 1")
            nProd 		+= (cAlias)->H6_QTDPROD
            cOldParctot	:= (cAlias)->H6_PT
            nProdOper := nProd
        ElseIf lH8Quant .And. (cAlias)->H6_OPERAC + (cAlias)->H6_SEQ == aInfos[1]  +   aInfos[2].And. aInfos[5]  == (cAlias)->H6_DESDOBR
            conout("entrou 2")
            nProd 		-= (cAlias)->H6_QTDPROD + (cAlias)->H6_QTDPERD
            cOldParctot	:= (cAlias)->H6_PT

        ElseIf (cAlias)->H6_OPERAC + (cAlias)->H6_SEQ == aInfos[1] + aInfos[2] .And. cOperAnt == Nil .And. ( aInfos[5]  # (cAlias)->H6_DESDOBR .or. l681Auto)
            conout("entrou 3")
            nProd 		-= (cAlias)->H6_QTDPROD + If(lPerdInf,0,(cAlias)->H6_QTDPERD)
            cOldParctot	:= If(QtdComp(nProd -   aInfos[4] ) <= QtdComp(0),"T", (cAlias)->H6_PT)
            nProdOper := nProd
        EndIf


        IF (cAlias)->H6_OPERAC == cOperAnt .AND. (cAlias)->H6_SEQ == cSeqAnt
            nVlAnt 		:=   Max(nProdOper - nPerda, 0)
            cStatusAux 	:= (cAlias)->H6_PT
        EndIF

        (cAlias)->(dbSkip())

    Enddo

    IF (nVlAnt >= aInfos[4] ) .And.	cStatusAux == "P" .And. len(aOperAnt) > 0
        cOldParctot := "P"
    Else
        cOldParctot := "T"
    EndIf

    CONOUT("nVlAnt[1]"+CVALTOCHAR( nVlAnt))
    RestArea(aSavAre[1])
    RestArea(aSavAre[2])

    If lSomaPerda
        nPerda := 0
    EndIf

    nQtdRet := Max(nProd - nPerda, 0)

    If lH8Quant .And. l680
        nQtdRet := Min(nQtdRet, SH8->H8_QUANT)
    EndIf

    (cAlias)->(dbCloseArea())

Return{nQtdRet,cOldParctot}




static Function f680OperAnt()
    Local aSavAre  := {SC2->(GetArea()), SB1->(GetArea()), SG2->(GetArea()), GetArea(), SHY->(GetArea())}
    Local aAreSh8  := Nil
    Local cRoteiro := Space(Len(SC2->C2_ROTEIRO))
    Local cOperAtu := aInfos[1]
    Local cSeqAtu  := aInfos[2]
    Local cOp      := aInfos[3]
    Local cOperAnt := Nil
    Local cSeqAnt  := Nil
    Local lIntSFC	:= FindFunction('IntegraSFC') .And. IntegraSFC() .And. !IsInCallStack("AUTO681")
    Local lProces
    Local l681		:= IsInCallStack("MATA681")
    Local cSeek    := Nil
    Local cSeekSHY
    Local aArray   := {}
    Local nSeek    := 0
    l680 := .f.
    l681 := .t.
    dbSelectArea("SHY")
    SHY->(dbSetOrder(1))
    lProces := SHY->(dbSeek(xFilial("SHY")+cOp))

    //  If l680
    //   // Vou jogar dados no array pois nao tenho o indice que preciso (H8_OP + H8_OPER + H8_SEQROTA)
    //   aAreSh8 := SH8->(GetArea())
    //   dbSelectArea("SH8")
    //   dbSeek(cSeek := xFilial("SH8") + cOp)
    //   do While ! Eof() .And. H8_FILIAL + H8_OP == cSeek
    //       cRoteiro := H8_ROTEIRO
    //       If (nSeek := aScan(aArray, {|z| z[1] + z[2] == H8_OPER + H8_SEQROTA})) == 0
    //           Aadd(aArray, {H8_OPER, H8_SEQROTA})
    //       EndIf
    //       dbSkip()
    //   Enddo
    //   aSort(aArray,,, {|z,w| z[1] + z[2] < w[1] + w[2]})
    //   If (nSeek := aScan(aArray, {|z| z[1] + z[2] == cOperAtu + cSeqAtu})) > 1
    //       cOperAnt := aArray[nSeek - 1, 1]
    //       cSeqAnt  := aArray[nSeek - 1, 2]
    //   EndIf
    //   RestArea(aAreSh8)
    //  EndIf
    If l681 .And. lProces //Verifica se processo foi iniciado pelo modelo 2 e parametro está ativo para validação de operação pela SHY
        If cRoteiro == Nil .Or. Empty(cRoteiro)
            SC2->(dbSetOrder(1))
            SC2->(MsSeek(xFilial("SC2") + cOp))
            If ! Empty(SC2->C2_ROTEIRO)
                cRoteiro := SC2->C2_ROTEIRO
            Else
                SB1->(dbSetOrder(1))
                SB1->(MsSeek(xFilial("SB1") + aInfos[6]))
                If ! Empty(SB1->B1_OPERPAD)
                    cRoteiro := SB1->B1_OPERPAD
                Else
                    cRoteiro := StrZero(1, Len(SG2->G2_CODIGO))
                EndIf
                RestArea(aSavAre[1])
                RestArea(aSavAre[2])
            EndIf
        EndIf
        cSeekSHY	:= "SHY->(HY_FILIAL+HY_OP+HY_ROTEIRO)"
        A650SkHY(1,aInfos[6],xFilial('SHY')+aInfos[3]+cRoteiro,@cSeekSHY)
        SHY->(dbEval({|| cOperAnt := HY_OPERAC},, {|| ! Eof() .And. Eval(&cSeekSHY) .And. SHY->HY_OPERAC < cOperAtu}))

        RestArea(aSavAre[5])
        If cOperAnt # Nil
            cSeqAnt := Space(Len(SH6->H6_SEQ))
        EndIf
    ElseIf ! l680 .Or. cOperAnt == Nil   // Nao consegui achar a operacao anterior pelas operacoes alocadas e vou tentar pelo roteiro de operacoes
        If cRoteiro == Nil .Or. Empty(cRoteiro)
            SC2->(dbSetOrder(1))
            SC2->(MsSeek(xFilial("SC2") + cOp))
            If ! Empty(SC2->C2_ROTEIRO)
                cRoteiro := SC2->C2_ROTEIRO
            Else
                SB1->(dbSetOrder(1))
                SB1->(MsSeek(xFilial("SB1") + aInfos[6]))
                If ! Empty(SB1->B1_OPERPAD)
                    cRoteiro := SB1->B1_OPERPAD
                Else
                    cRoteiro := StrZero(1, Len(SG2->G2_CODIGO))
                EndIf
                RestArea(aSavAre[1])
                RestArea(aSavAre[2])
            EndIf
        EndIf
        cSeek := "SG2->(G2_FILIAL+G2_PRODUTO+G2_CODIGO)"
        a630SeekSG2(1,aInfos[6],xFilial("SG2") + aInfos[6] + cRoteiro,@cSeek)

        //Valida a data de validade da operação.
        While SG2->(!Eof()) .And. Eval(&cSeek) .And. SG2->G2_OPERAC < cOperAtu
            If !Empty(SG2->G2_DTINI)
                If !Empty(aInfos[7]) .And. SG2->G2_DTINI > fConvertDt(aInfos[7])
                    SG2->(dbSkip())
                    Loop
                EndIf
                If !Empty(aInfos[8]) .And. SG2->G2_DTINI > fConvertDt(aInfos[8])
                    SG2->(dbSkip())
                    Loop
                EndIf
            EndIf
            If !Empty(SG2->G2_DTFIM)
                If !Empty(aInfos[7]) .And. SG2->G2_DTFIM < fConvertDt(aInfos[7])
                    SG2->(dbSkip())
                    Loop
                EndIf
                If !Empty(aInfos[8]) .And. SG2->G2_DTFIM < fConvertDt(aInfos[8])
                    SG2->(dbSkip())
                    Loop
                EndIf
            EndIf
            cOperAnt := SG2->G2_OPERAC
            SG2->(dbSkip())
        End

        RestArea(aSavAre[3])
        If cOperAnt # Nil
            cSeqAnt := Space(Len(SH6->H6_SEQ))
        EndIf
    EndIf
    RestArea(aSavAre[4])
Return({cOperAnt,cSeqAnt})



Static function fSetEFIC(aDados)



    LOCAL cQuery:= ""
    LOCAL cQuery1:= ""
    LOCAL NTMPEST :=0
    LOCAL NTMPAD :=0
    LOCAL NEFICI :=0
    LOCAL NROTEIRO:=0




    nPosOper  := aScan(aDados, {|x| x[1] == "H6_OPERAC"})
    nPosSeq   := aScan(aDados, {|x| x[1] == "H6_SEQ"})
    nPosOPr   := aScan(aDados, {|x| x[1] == "H6_OP"})
    nPosQt    := aScan(aDados, {|x| x[1] == "H6_QTDPROD"})
    nPosDes   := aScan(aDados, {|x| x[1] == "H6_DESDOBR"})
    nPsPrd    := aScan(aDados, {|x| x[1] == "H6_PRODUTO"})
    nPsDtIni  := aScan(aDados, {|x| x[1] == "H6_DATAINI"})
    nPsDtFin  := aScan(aDados, {|x| x[1] == "H6_DATAFIN"})
    nPsZEFIC  := aScan(aDados, {|x| x[1] == "H6_ZEFICI"})
    nPini     := aScan(aDados, {|x| x[1] == "H6_HORAINI"})
    nPfin     := aScan(aDados, {|x| x[1] == "H6_HORAFIN"})
    NCINI := HCentini( aDados[nPini][2])
    NCFIN := HCentFim( aDados[nPfin][2])
    NTEMREAL := NCFIN - NCINI


    cOp:= aDados[nPosOPr][2]
    cPrdOP :=  aDados[nPsPrd][2]
    cOperac :=  aDados[nPosOper][2]
    nQtdOP :=  aDados[nPosQt][2]

    cQuery1 +="SELECT C2_NUM, C2_ROTEIRO"
    cQuery1 +=" FROM "+RetSqlName("SC2")+ " SC2"
    cQuery1 +=" WHERE SC2.D_E_L_E_T_<> '*'AND C2_NUM ='"+SUBSTRING(cOp,1,6)+"'"
    cQuery += " AND C2_FILIAL ='"+XFILIAL("SC2")+"'"
    cQuery1 +=" AND C2_ITEM='"+SUBSTRING(cOp,7,2)+"'"
    cQuery1 +=" AND C2_SEQUEN='"+SUBSTRING(cOp,9,3)+"'"

    MPSysOpenQuery( cQuery1, 'SqlQuery1' )

    NROTEIRO := SqlQuery1->C2_ROTEIRO
    cQuery := ""
    cQuery += "SELECT G2_FILIAL, G2_CODIGO,G2_PRODUTO,G2_OPERAC,G2_TEMPAD,G2_SETUP"
    cQuery += " FROM "+RetSqlName("SG2")+" SG2 "
    cQuery += " WHERE SG2.D_E_L_E_T_<> '*' AND G2_FILIAL ='"+XFILIAL("SG2")+"'"
    cQuery += " AND G2_CODIGO= '"+NROTEIRO+"'"
    cQuery += " AND G2_PRODUTO ='"+cPrdOP+"'"
    cQuery += " AND G2_OPERAC ='"+cOperac+"'"
    cQuery += " ORDER BY G2_FILIAL, G2_CODIGO,G2_PRODUTO,G2_OPERAC"

    conout("fSetEFIC")
    MPSysOpenQuery( cQuery, 'SqlQuery' )

    NTMPEST := SqlQuery->G2_TEMPAD *nQtdOP
    NTMPAD:=SqlQuery->G2_SETUP


    NEFICI := ROUND(((NTMPEST + NTMPAD) / NTEMREAL) * 100, 2)

    AADD(aDados, {"H6_ZEFICI", NEFICI, Nil})


    // RECLOCK( "SH6", .F. )
    // M->H6_ZEFICI:=NEFICI
    // SH6->(MSUNLOCK())

    SqlQuery->(DBCLOSEAREA())
    SqlQuery1->(DBCLOSEAREA())

Return



Static Function HCentini(cHora)
    Local NHINI, NMINI, NTINI, NCINI

    NHINI := Val(SubStr(cHora, 1, 3))
    NMINI :=  Val(SubStr(cHora, 4, 2))
    NTINI := NHINI + (NMINI / 60)
    NCINI := NTINI

Return NCINI

Static Function HCentFim(cHora)
    Local NHFIN, NMFIN, NTFIN, NCFIN

    NHFIN :=  Val(SubStr(cHora, 1, 3))
    NMFIN :=   Val(SubStr(cHora, 4, 2))
    NTFIN := NHFIN + (NMFIN / 60)
    NCFIN := NTFIN

Return NCFIN
