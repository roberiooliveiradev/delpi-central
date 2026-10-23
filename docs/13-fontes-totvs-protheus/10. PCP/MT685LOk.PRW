#INCLUDE "PROTHEUS.CH"
//-------------------------------------------------------------------
/*/{Protheus.doc} MT685LOk
Ponto de entrada para Validação da quantidade apontada como perda pelas rotinas de produção
@author  Eduardo Dalitz
@since   28/02/2025
@version 1.0
/*/
//-------------------------------------------------------------------
USER FUNCTION MT685LOk()
    Local nI := 0
    Local nPosProd
    Local nPosQtd
    Local lRet := .T.
    Local nPosCod := 0
    Local nPosQtd := 0
    Local nQtdTot := 0
    Local nPosQtd2 := 0
    Local nPosTotal :=0
    Local nPosDesc := 0
    Local nx := 0
    Local nQtdeSD4 := 0
    LOCAL cRotOrig	 := FunName()
    lOCAL cOprod := ""

    If cRotOrig == "MATA250"
        cOprod := M->D3_OP

    ElseIf cRotOrig $ "MATA680*MATA681"
        cOprod := M->H6_OP
    ElseIf cRotOrig $ "MATA685"
        cOprod :=cOrdEmp
    EndIf

    nPosProd := aScan(aHeader, {|x| AllTrim(Upper(x[2])) == "BC_PRODUTO" })
    nPosQtd:= aScan(aHeader, {|x| AllTrim(Upper(x[2])) == "BC_QUANT" })

    IF SB1->B1_TIPO == "MP"
        IF SB1->B1_UM $ "PC/UN/RL"
            For nI := 1 To Len(aCols)
                IF int(ACOLS[nI][nPosQtd]) - ACOLS[nI][nPosQtd] == 0
                    lRet := .T.
                else
                    FWAlertWarning("A quantidade de perda do produto: "+ACOLS[nI][nPosProd]+"precisa ser um número inteiro", "Atenção")
                    lRet := .F.
                endif
            Next nI
        ENDIF

        For nx:= 1 To Len(aHeader)
            If Trim(Substr(aHeader[nx][2],3)) == "_COD" .Or. Trim(Substr(aHeader[nx][2],3)) == "_PRODUTO"
                nPosCod:=nx
            ElseIf Trim(Substr(aHeader[nx][2],3)) == "_QUANT"
                nPosQtd:=nx
                cVarQtd:="M->"+AllTrim(aHeader[nx][2])
            ElseIf Trim(Substr(aHeader[nx][2],3)) == "_QTSEGUM"
                nPosQtd2:=nx
                cVarQtd2:="M->"+AllTrim(aHeader[nx][2])
            ElseIf Trim(Substr(aHeader[nx][2],3)) == "_TOTAL"
                nPosTotal:=nx
                cVarTotal:="M->"+AllTrim(aHeader[nx][2])
            ElseIf Trim(Substr(aHeader[nx][2],3)) == "_VALDESC"
                nPosDesc:=nx
            EndIf
            // Caso j  achou todos, abandona o Loop
            If nPosCod > 0 .And. nPosQtd > 0 .And. nPosQtd2 > 0 .And. nPosTotal > 0 .And. nPosDesc > 0
                Exit

            ENDIF
        Next nx
        SD4->(dbSetOrder(2))
        SD4->(dbSeek(xFilial("SD4")+cOprod+aCols[n,nPosCod]+aCols[n,nPosLoc]))
        While !SD4->(EOF()) .And. SD4->(D4_FILIAL+D4_OP+D4_COD+D4_LOCAL) == xFilial("SD4")+cOprod+aCols[n,nPosCod]+aCols[n,nPosLoc]
            nQtdeSD4 += SD4->D4_QUANT
            SD4->(dbSkip())
        End
        nQtdTot += If(aCols[N,Len(aCols[N])],0,aCols[N,nPosQtd])
        aAreaSBC:=SBC->(GetArea())
        SBC->(dbSetOrder(1))
        SBC->(dbSeek(xFilial("SBC")+cOprod))
        While !SBC->(Eof()) .And.  SBC->(BC_FILIAL+BC_OP) ==  xFilial("SBC")+cOprod
            If SBC->(BC_PRODUTO+BC_LOCORIG) == aCols[n,nPosCod]+aCols[n,nPosLoc]
                nQtdTot += SBC->BC_QUANT
            EndIF
            SBC->(dbSkip())
        End
        nPercPerd := ((nQtdTot / nQtdeSD4)*100)
        If nPercPerd >50
            FWAlertWarning("Não é permitido realizar perda acima de 50%", "Atenção")
            lRet := .F.
        endif
        RestArea(aAreaSBC)

    ELSE
        FWAlertWarning("Não é permitido apontar perda de produto com tipo diferente de MP", "Atenção")
        lRet := .F.



    ENDIF


    //BC_QUANT

Return lRet
