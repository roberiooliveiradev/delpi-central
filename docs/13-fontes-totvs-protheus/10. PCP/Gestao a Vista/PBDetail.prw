#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'
Static cTipoTemp
/*PBDetail*/
User Function PBDetail()
    Local nCodVisao := PARAMIXB[1] //Código da visão
    Local cCodMon   := PARAMIXB[2] //Código do monitor
    Local nSeqVisao := PARAMIXB[3] //Sequencia do monitor na visão
    Local cReturn   := ""
    Local oJson     := JsonObject():New()
    lOCAL n1        := 0
    lOCAL n2        := 0
    lOCAL nIndice   := 0
    oJson:FromJson(PARAMIXB[4]) //Converte o parâmetro texto para objeto Json
    conout("stop gda")
    conout("cCodMon - "+cCodMon)
    conout("nSeqVisao - "+cvaltochar(nSeqVisao))
    conout("nCodVisao - "+cvaltochar(nCodVisao))


    If ( nCodVisao == 2 .and. cCodMon == "000000000002" .And. nSeqVisao >= 2 .and. nSeqVisao <=25);
            .or. (nCodVisao == 3 .and. cCodMon == "000000000002" .And. nSeqVisao >= 1 .and. nSeqVisao <=4);
            .or. (nCodVisao == 13 .and. cCodMon == "000000000002" .And. nSeqVisao >= 1 .and. nSeqVisao <=24);
            .or. ( cCodMon == "000000000028")
        aColunas := aClone( oJson["columns"])
        nIndice := len( oJson["columns"])

        cCPOX3:="H6_ZEFICI"
        cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
        PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"number",.T.)
        cCPOX3:="H6_OPERADO"
        cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
        PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
        PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'SYS_USR',"Nm Operador","string",.T.)
        cCPOX3:="H6_OBSERVA"
        cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
        PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"number",.T.)
        oJson["columns"] := aClone(aColunas)
        For  n1 := 1 to len( oJson["columns"])

            conout("nCodVisao - "+cvaltochar(nCodVisao))
            nPosHr := 1
            if oJson["columns"][n1]["property"] =="H6_HORAFIN"
                nPosHr := n1
            endif

            if   oJson["columns"][n1]["property"] $"H6_QTDPERD_H6_MOTIVO_CYN_DSSP_H6_DATAINI_H6_DATAFIN"

                oJson["columns"][n1]["visible"] := .F.

            ELSE
                oJson["columns"][n1]["visible"] := .t.
            ENDIF
        Next n1
        conout("stop")
        aItens := aClone(oJson["items"])
        aSort(aItens,,, { |x, y, z| x['H6_HORAFIN'] < y['H6_HORAFIN'] })
        oJson["items"] := aClone( aItens )
        // aSort(aItens,,, { |x, y, z| x[nPosHr] < y[nPosHr] })

        if cCodMon == "000000000028"
            For  n2 := 1 to len( oJson["items"])
                dbSelectArea("SH6")
                SH6->(DbSetOrder(1)) //H6_FILIAL+H6_OP+H6_PRODUTO+H6_OPERAC+H6_SEQ+DTOS(H6_DATAINI)+H6_HORAINI+DTOS(H6_DATAFIN)+H6_HORAFIN
                // cCHVSH6 :=  oJson["items"][n2]["H6_FILIAL"]+ oJson["items"][n2]["H6_OP"]+ oJson["items"][n2]["H6_PRODUTO"]+ oJson["items"][n2]["H6_OPERAC"]
                cCHVSH6 :=  oJson["items"][n2]["RECSH6"]
                SH6->(DbGOTO(cCHVSH6))

                cRoteiro := ""
                dbSelectArea("SC2")
                dbSeek(xFilial("SC2")+SH6->H6_OP)
                If !Empty(SC2->C2_ROTEIRO)
                    cRoteiro:=SC2->C2_ROTEIRO
                Else
                    dbSelectArea("SB1")
                    dbSeek(xFilial("SB1")+SH6->H6_PRODUTO)
                    cRoteiro:=SB1->B1_OPERPAD
                EndIf
                // dbSelectArea("SG2")
                // SG2->(DbSetOrder(1))
                // SG2->(DbSeek(xFilial("SG2")+SH6->H6_PRODUTO+SH6->H6_ROTEIRO))
                // If Empty(cRoteiro)
                //     cRoteiro := StrZero(1, Len(SG2->G2_CODIGO))
                // Endif

                dbSelectArea("SG2")
                a630SeekSG2(1,SH6->H6_PRODUTO,xFilial("SG2")+SH6->H6_PRODUTO+cRoteiro+SH6->H6_OPERAC)

                cHrReal		:=R895Calc()
                cHrPrev		:=TimeH6()
                If cTipoTemp == "C"
                    cHrPrev := Val(StrTran(cHrPrev, ":", "."))
                EndIf

                nVlrEfi := ((cHrReal+ SG2->G2_SETUP) / cHrPrev )
                oJson["items"][n2]["H6_ZEFICI"]  :=round(( (nVlrEfi)*100),2)
                oJson["items"][n2]["H6_OBSERVA"] := SH6->H6_OBSERVA
                oJson["items"][n2]["H6_OPERADO"] := SH6->H6_OPERADO
                if UsrExist(SH6->H6_OPERADO)
                    oJson["items"][n2]["SYS_USR"] := alltrim(UsrFullName(SH6->H6_OPERADO))
                else
                    oJson["items"][n2]["SYS_USR"] := " "
                endif


            Next n2
        endif
    endif

    cReturn := oJson:ToJson() //Converte o objeto Json em texto
Return cReturn




Static Function R895Calc(cAliasSH6)
    Local aTotal  := {}
    Local cTime   := Nil
    Local nLotPad := If(SG2->G2_LOTEPAD==0,1,SG2->G2_LOTEPAD)
    Local nQuant  := 0
    Local nTemPad := If(SG2->G2_TEMPAD ==0,1,SG2->G2_TEMPAD)
    Local nTempo  := Nil

    Default cAliasSH6 := "SH6"

    nQuant  := SH6->(H6_QTDPROD+H6_QTDPERD)

    If cTipoTemp == Nil
        cTipoTemp:=GetMV("MV_TPHR")
    EndIf

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³ Se MV_TPHR for N (Normal) devo converter G2_TEMPAD para            ³
    //³ centesimal para permitir multiplicar pela quantidade produzida     ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    If cTipoTemp == "N"
        nTemPad := Int(nTemPad) + (Mod(nTemPad, 1) / 0.6)
    Endif

    // Calcula Tempo de Dura‡„o baseado no Tipo de Operacao
    If SG2->G2_TPOPER $ " 1"
        nTempo := nQuant * nTemPad / nLotPad
        dbSelectArea("SH1")
        dbSeek(xFilial("SH1")+SH6->H6_RECURSO)
        If Found() .And. SH1->H1_MAOOBRA # 0
            nTempo :=Round( nTempo / H1_MAOOBRA,5)
        EndIf
        dbSelectAreaSH6
    ElseIf SG2->G2_TPOPER == "4"
        nQuantAloc:= nQuant % nLotPad
        nQuantAloc:= Int(nQuant)+If(nQuantAloc>0,nLotPad-nQuantAloc,0)
        nTempo := Round(nQuantAloc * ( nTemPad / nLotPad ),5)
        dbSelectArea("SH1")
        dbSeek(xFilial("SH1")+SH6->H6_RECURSO)
        If Found() .And. SH1->H1_MAOOBRA # 0
            nTempo :=Round( nTempo / H1_MAOOBRA,5)
        EndIf
        dbSelectArea("SH6")
    ElseIf SG2->G2_TPOPER == "2"
        aTotal := FH6Total(SC2->C2_NUM+SC2->C2_ITEM+SC2->C2_SEQUEN,SH6->H6_OPERAC)
        If nQuant == 0
            nTemPad := (nTemPad/(aTotal[3] + aTotal[2])) * aTotal[3]
            nTempo := (nTemPad/aTotal[3])* 1
        else
            nTemPad := (nTemPad/(aTotal[2] + aTotal[3]))*aTotal[2]
            nTempo := (nTemPad/aTotal[1])* nQuant
        EndIf

    ElseIf SG2->G2_TPOPER == "3"
        nTempo := nTemPad
    EndIf

    If cTipoTemp == "N"
        cTime  := StrZero(Int(nTempo), 3) + ":" + StrZero(Mod(nTempo, 1) * 100, 2)
        cTime := A680ConvHora(cTime, "C", "N")
    Endif

Return IF(cTipoTemp=="N",cTime,nTempo)

/*/{Protheus.doc} FH6Total
Retonar as quantidades de apontamentos
@type  Static Function
@author guilherme.bertoldi
@since 18/02/2022
@version 12.1.33
@param 01 cOp, character, numero da OP
@param 02 cOperac, character, Operacao
@return array, array, retorna a quantidade de producao, quantidade de apontamentos e a quantidade apontada sem producao.
/*/
Static Function FH6Total(cOp,cOperac)
    Local nQtdTotal := 0
    Local nQtdApont := 0
    Local nQtdCount := 0

    cAliasSH6 := GetNextAlias()
    //QUANTIDADE TOTAL DE APONTAMENTOS
    BeginSQL alias cAliasSH6
        SELECT
            SUM(SH6.H6_QTDPROD + SH6.H6_QTDPERD) TOTAL,
            COUNT(SH6.H6_QTDPROD + SH6.H6_QTDPERD) COUNTTOTAL
        FROM
            %table:SH6% SH6
        WHERE
            SH6.%notDel%
            AND SH6.H6_FILIAL = %xfilial:SH6%
            AND (
                SH6.H6_QTDPROD != '0'
                OR SH6.H6_QTDPERD != '0'
            )
            AND SH6.H6_OP = %exp:cOp%
            AND SH6.H6_OPERAC = %exp:cOperac%
    EndSQL

    nQtdTotal := (cAliasSH6)->(TOTAL)
    nQtdCount := (cAliasSH6)->(COUNTTOTAL)
    (cAliasSH6)->(dbCloseArea())

    cAliasSH6 := GetNextAlias()
    //QUANTIDADE TOTAL DE APONTAMENTOS
    BeginSQL alias cAliasSH6
        SELECT
            COUNT(SH6.H6_QTDPROD) TOTAL
        FROM
            %table:SH6% SH6
        WHERE
            SH6.%notDel%
            AND SH6.H6_FILIAL = %xfilial:SH6%
            AND SH6.H6_QTDPROD = '0'
            AND SH6.H6_QTDPERD = '0'
            AND SH6.H6_OP = %exp:cOp%
            AND SH6.H6_OPERAC = %exp:cOperac%
    EndSQL

    nQtdApont := (cAliasSH6)->(TOTAL)
    (cAliasSH6)->(dbCloseArea())

Return {nQtdTotal, nQtdCount, nQtdApont}
