#Include 'Protheus.ch'
#INCLUDE 'TOPCONN.CH'
#INCLUDE "TBICONN.CH"

/*/{Protheus.doc} Function


    aadd(aNota,SF1->F1_SERIE)
    aadd(aNota,IIF(Len(SF1->F1_DOC)==6,"000","")+SF1->F1_DOC)
    aadd(aNota,SF1->F1_EMISSAO)
    aadd(aNota,cTipo)
    aadd(aNota,SF1->F1_TIPO)
    aadd(aNota,SF1->F1_HORA)

    aadd(aNota,SF2->F2_SERIE)
    aadd(aNota,IIF(Len(SF2->F2_DOC)==6,"000","")+SF2->F2_DOC)
    aadd(aNota,SF2->F2_EMISSAO)
    aadd(aNota,cTipo)
    aadd(aNota,SF2->F2_TIPO)
    aadd(aNota,Iif(lNfCup,cHoraNota,SF2->F2_HORA))

    aAdd(aInfoItem,{(cAliasSD2)->D2_PEDIDO,(cAliasSD2)->D2_ITEMPV,(cAliasSD2)->D2_TES,(cAliasSD2)->D2_ITEM})

    Description

    @author  Name
    @example Example
    @param   [Parameter_Name],Parameter_type,Parameter_Description
    @return  Return
    @table   Tables
    @since   18-10-2019
/*/

User Function PE01NFESEFAZ()
    Local aArea         := getarea()
    Local aProd			:= PARAMIXB[1]
    Local cMensCli		:= PARAMIXB[2]
    Local cMensFis		:= PARAMIXB[3]
    Local aDest 		:= PARAMIXB[4]
    Local aNota 		:= PARAMIXB[5]
    Local aInfoItem		:= PARAMIXB[6]
    Local aDupl			:= PARAMIXB[7]
    Local aTransp		:= PARAMIXB[8]
    Local aEntrega		:= PARAMIXB[9]
    Local aRetirada		:= PARAMIXB[10]
    Local aVeiculo		:= PARAMIXB[11]
    Local aReboque		:= PARAMIXB[12]
    Local aNfVincRur	:= PARAMIXB[13]
    Local aEspVol     	:= PARAMIXB[14]
    Local aNfVinc		:= PARAMIXB[15]
    Local aDetPag		:= PARAMIXB[16]
    Local aObsCont		:= PARAMIXB[17]
    Local  aProcRef     := aParam[18]
    Local aMed          := aParam[19]
    Local aLote         := aParam[20]
    Local aDI		    := PARAMIXB[21]
    Local aPedCom	    := PARAMIXB[22]
    Local aRetorno      := {}
    Local cMsg          := ""
    Local nVlrSISCO := 0
    Local nVlrAFRMM := 0
    Local aImp
    Local cMSG02 :=""



    /*******************************
    ** 1 - Inicio Customização DI **
    ********************************/
    if alltrim(aDest[9]) $ 'EX' .and. len(aDI[1])>0

        aImp := GetImp({ANOTA[1], ANOTA[2]} )

        For _nX := 1 To Len(aDI)
            cDI		   := aDI[_nX,04,3]
            dDtDI	   := aDI[_nX,05,3]
            nVlrSISCO  += aDI[_nX,18,3]
            //nVlrII     += aAdi[_nX,19,3]
            nVlrAFRMM  += aDI[_nX,37,3]
        Next _nX
        cMensFis := alltrim(cMensFis)
        If	!Empty(cDI)

            cMensFis += ' Nº da DI='+AllTrim(cDI)

        EndIf

        If	!Empty(dDtDI)

            cMensFis += 'Data de Registro da DI '+Dtoc(dDtDI)+' '

        EndIf

        If	!Empty(cDI) .Or. !Empty(dDtDI)

            cMensFis += 'Preco Unitario do(s) Item(ns) com Inclusao do Vlr do Imposto de Importacao '

        EndIf

        /*If	!Empty(nVlrII)

            cMensFis += 'Vlr II=R$'+AllTrim(Transform(nVlrII,PesqPict('CD5','CD5_VLRII')))+ ' '

        EndIf*/

        If	!Empty(aImp[2])

            cMensFis += 'Vlr PIS=R$'+AllTrim(Transform(aImp[2],PesqPict('CD5','CD5_VLPIS')))+ ' '

        EndIf

        If	!Empty(aImp[1])

            cMensFis += 'Vlr COFINS=R$'+AllTrim(Transform(aImp[1],PesqPict('CD5','CD5_VLCOF')))+ ' '

        EndIf

        If	!Empty(nVlrSISCO)

            cMensFis += 'Vlr SISCOMEX=R$'+AllTrim(Transform(nVlrSISCO,PesqPict('CD5','CD5_DSPAD')))+ ' '

        EndIf

        If	!Empty(nVlrAFRMM)

            cMensFis += 'Vlr AFRMM=R$'+AllTrim(Transform(nVlrAFRMM,PesqPict('CD5','CD5_VAFRMM')))+ ' '

        EndIf

    ENDIF

    /*******************************
    ** 1 -  Fim  Customização  DI **
    ********************************/
    /*************************************************
    ** 2 - Saida - Mensagens Pedido de Venda        **
    ** Texto Legal 1 e 2 - Codigo Tamanho 3  - ZZ1  **
    ** Mensagem 1,2 E 3  - Texto Livre - Tamanho 60 **
    ** C5_TEXT1 | C5_TEXT2| Z1_TEXT1 | Z1_TEXT2     **
    *************************************************/

    IF aNota[4] == '1'
        //For nI := 1 to Len(aInfoItem)
        fGetMsgRod(aNota,@cMensFis)
        fGetPedCli(@aProd,@aPedCom,aNota)
        fProc3UM(@aProd,aNota,aDest)
        if cEmpAnt $ "01_05"
            fPutCert(@aProd)
        endif
        /**********************************************
        **            FIM DA CUSTOMIZACAO            **
        ** 2 - Saida - Mensagens Pedido de Venda     **
        ***********************************************/
    endif
    /*01*/ aadd(aRetorno,aProd)
    /*2*/ aadd(aRetorno,cMensCli)
    /*3*/ aadd(aRetorno,cMensFis)
    /*4*/ aadd(aRetorno,aDest)
    /*5*/ aadd(aRetorno,aNota)
    /*6*/ aadd(aRetorno,aInfoItem)
    /*7*/ aadd(aRetorno,aDupl)
    /*8*/ aadd(aRetorno,aTransp)
    /*9*/ aadd(aRetorno,aEntrega)
    /*10*/ aadd(aRetorno,aRetirada)
    /*11*/ aadd(aRetorno,aVeiculo)
    /*12*/ aadd(aRetorno,aReboque)
    /*13*/ aadd(aRetorno,aNfVincRur)
    /*14*/ aadd(aRetorno,aEspVol)
    /*15*/ aadd(aRetorno,aNfVinc)
    /*16*/ aadd(aRetorno,aDetPag)
    /*17*/ aadd(aRetorno,aObsCont)



    /*18*/ aadd(aRetorno,aProcRef)
    /*19*/ aadd(aRetorno,aMed)
    /*20*/ aadd(aRetorno,aLote)

    /*21*/aadd(aRetorno,aDI)
    /*22*/aadd(aRetorno,aPedCom)
    //if len(PARAMIXB) >=19
    //   aadd(aRetorno,aPedCom)
    //endif
    restarea(aArea)
RETURN aRetorno

Static Function fPutCert(aProd)
    Local nX
    For nX := 1 to Len(aProd)
        cCodPrd := aProd[nX][2]
        aProd[nX][3] :=""
        cCertBZ :=ALLTRIM( POSICIONE("SBZ",1,XFILIAL("SBZ")+cCodPrd,"BZ_YCERT"))
        IF !EMPTY(cCertBZ)
            aProd[nX][4] := ALLTRIM(aProd[nX][4] )+" - Certificado: "+cCertBZ
        ENDIF
    next nX
REturn

Static Function GetImp(aPars)
    Local cSql := ""
    Local cEol := chr(10)
    Local aRet := {0,0,0}
    Local cCo

    cSql +="SELECT  SUM( CASE WHEN A.CD2_IMP LIKE 'CF%' THEN CD2_VLTRIB ELSE 0 END) [VL_COFINS]," + cEol
    cSql +="		SUM( CASE WHEN A.CD2_IMP LIKE 'PS%' THEN CD2_VLTRIB ELSE 0 END) [VL_PIS],   " + cEol
    cSql +="		SUM( CASE WHEN A.CD2_IMP LIKE 'ICM%' THEN CD2_VLTRIB ELSE 0 END) [VL_ICMS]  " + cEol
    cSql +="FROM dbo." + retsqlname("CD2") + " A (nolock) "         + cEol
    cSql +="WHERE A.D_E_L_E_T_     = '' 						"   + cEol
    cSql +="	  AND A.CD2_FILIAL = "  + valtosql(SF1->F1_FILIAL)  + cEol
    cSql +="	  AND A.CD2_DOC    = "  + valtosql(aPars[1])        + cEol
    cSql +="	  AND A.CD2_SERIE  = "  + valtosql(aPars[2])        + cEol
    cSql +="	  AND CD2_CODFOR   = "  + valtosql(SF1->F1_FORNECE) + cEol
    cSql +="	  AND CD2_LOJFOR   = "  + valtosql(SF1->F1_LOJA)


    CONOUT(cSql)

    If (Select("TRBCD2") <> 0)

        dbSelectArea("TRBCD2")
        dbCloseArea()

    Endif

    TCQuery cSql NEW ALIAS "TRBCD2"

    if TRBCD2->(!Eof())

        aRet[1] += TRBCD2->VL_COFINS
        aRet[2] += TRBCD2->VL_PIS
        aRet[3] += TRBCD2->VL_ICMS

    EndIF

Return aRet


/*/{Protheus.doc} fGetMsgRod
    VERIFICA AS NOTAS E RETORNA CONFORME A REGRA ABAIXO

    REGRA01  ALMOXARIFADO WEG
    REGRA02 PEDIDO CLIENTE

    @author  Gabriel Araujo
    @param  aNota,cMensFis)
    @since   24-10-2019
/*/

STATIC FUNCTION fGetMsgRod(aNota,cMensFis)
    Local cSql := ""
    Local cEol := chr(10)
    Local aTes := {}
    Local aTxLgl := {}
    Local aSC5Msg := {"","","","","","","","",""}
    if cEmpAnt $ "01_05"
        cSql :="SELECT      DISTINCT SD2.D2_ALMOX, SD2.D2_PEDIDO,SZ2.Z2_DESCR,D2_TES" + cEol
        cSql +="FROM      dbo."+RetSQLTab("SD2")+"  (NOLOCK) " + cEol
        cSql +="LEFT JOIN dbo."+RetSQLTab("SZ2")+"  (NOLOCK) " + cEol
        cSql +="  ON SZ2.D_E_L_E_T_ = '' AND SZ2.Z2_FILIAL = SD2.D2_FILIAL AND SZ2.Z2_CODIGO = SD2.D2_ALMOX " + cEol
        cSql +="WHERE      SD2.D_E_L_E_T_ = '' "               + cEol
        cSql +="			AND SD2.D2_DOC    = " + ValtoSql(aNota[2]) + cEol
        cSql +="			AND SD2.D2_SERIE    = " + ValtoSql(aNota[1]) + cEol
        cSql +="			AND SD2.D2_FILIAL = " + ValtoSql(XFilial("SD2")) + cEol

    else
        cSql :="SELECT      DISTINCT  SD2.D2_PEDIDO,D2_TES " + cEol
        cSql +="FROM      dbo."+RetSQLTab("SD2")+"  (NOLOCK) " + cEol
        cSql +="WHERE      SD2.D_E_L_E_T_ = '' "   + cEol
        cSql +="			AND SD2.D2_DOC    = " + ValtoSql(aNota[2]) + cEol
        cSql +="			AND SD2.D2_SERIE    = " + ValtoSql(aNota[1]) + cEol
        cSql +="			AND SD2.D2_FILIAL = " + ValtoSql(XFilial("SD2")) + cEol

    endif


    CONOUT("QUERY MENSAGEM")
    conout(cSql)
    If (Select("TMPMSG") <> 0)

        dbSelectArea("TMPMSG")
        dbCloseArea()

    Endif

    TCQuery cSql NEW ALIAS "TMPMSG"
    cMsgAlm := ""
    cMsgPed := ""
    cSC5Msg := ""
    cSZ1Msg := ""




    While TMPMSG->(!EOF())

        IF SF4->(DbSeek(xFilial("SF4")+TMPMSG->D2_TES))
            IF   ASCAN(aTxLgl, SF4->F4_ZTXLG1) == 0 .AND. !EMPTY(SF4->F4_ZTXLG1)
                AADD( aTxLgl,SF4->F4_ZTXLG1)
            ENDIF
            IF   ASCAN(aTxLgl, SF4->F4_ZTXLG2) == 0 .AND. !EMPTY(SF4->F4_ZTXLG2)
                AADD( aTxLgl,SF4->F4_ZTXLG2)
            ENDIF
        endif
        //  IF   ASCAN(aTxLgl, TMPMSG->D2_TES) == 0 .AND. !EMPTY(TMPMSG->D2_TES)
        //      AADD( aTxLgl,TMPMSG->D2_TES)
        //  ENDIF

        // IF SF4->(DbSeek(xFilial("SF4")+TMPMSG->D2_TES))
        //     IF   ASCAN(aTxLgl, SF4->F4_ZTXLG1) == 0 .AND. !EMPTY(SF4->F4_ZTXLG1)
        //         AADD( aTxLgl,SF4->F4_ZTXLG1)
        //     ENDIF

        //     IF   ASCAN(aTxLgl, SF4->F4_ZTXLG2) == 0 .AND. !EMPTY(SF4->F4_ZTXLG2)
        //         AADD( aTxLgl,SF4->F4_ZTXLG2)
        //     ENDIF
        // ENDIF


        SC5->(dbSetOrder(1))
        if     SC5->(dbSeek(xFilial("SC5")+ TMPMSG->D2_PEDIDO,.f.))
            If SC5->(FieldPos("C5_TEXT1")) > 0
                IF   ASCAN(aTxLgl, SC5->C5_TEXT1) == 0 .AND. !EMPTY(SC5->C5_TEXT1)
                    AADD( aTxLgl,SC5->C5_TEXT1)
                ENDIF
            ENDIF

            If SC5->(FieldPos("C5_TEXT2")) > 0
                IF   ASCAN(aTxLgl, SC5->C5_TEXT2) == 0 .AND. !EMPTY(SC5->C5_TEXT2)
                    AADD( aTxLgl,SC5->C5_TEXT2)
                ENDIF
            ENDIF

            If SC5->(FieldPos("C5_TEXT3")) > 0
                IF   ASCAN(aTxLgl, SC5->C5_TEXT3) == 0 .AND. !EMPTY(SC5->C5_TEXT3)
                    AADD( aTxLgl,SC5->C5_TEXT3)
                ENDIF
            ENDIF
        ENDIF
        if alltrim(cEmpAnt) $ "01_05"
            IF !EMPTY( TMPMSG->D2_ALMOX )
                cMsgTmpA := Alltrim(TMPMSG->Z2_DESCR)+" - "+Alltrim(TMPMSG->D2_ALMOX)
                if EMPTY(cMsgAlm)

                    cMsgAlm := " Almoxarifado "+ cMsgTmpA

                    //Gabriel Para nao repetir a Mensagem
                elseif !Empty(cMsgAlm) .and. !(cMsgTmpA $ cMsgAlm)
                    //cMsgAlm +=  " / "+ Alltrim(TMPMSG->Z2_DESCR)+" - "+Alltrim(TMPMSG->D2_ALMOX)
                    cMsgAlm +=  " / "+ cMsgTmpA
                endif
            ENDIF
            //C5_FILIAL, C5_NUM, R_E_C_N_O_, D_E_L_E_T_
        ENDIF
        cPedCli := Alltrim(POSICIONE ("SC5",1, XFILIAL("SC5") + TMPMSG->D2_PEDIDO ,"C5_PEDCLI"))

        IF !EMPTY( cPedCli )
            if EMPTY( cMsgPed )
                cMsgPed := " Ped. Cliente: " + cPedCli+ " "
            elseif !(EMPTY( cMsgPed )) .AND. !(cPedCli $ cMsgPED)
                cMsgPed +=  " / " + cPedCli+ " "
            endif
        ENDIF

        IF EMPTY(aSC5Msg[5])
            aSC5Msg[5] := Alltrim(SC5->C5_MSG1)
        ENDIF

        IF EMPTY(aSC5Msg[6])
            aSC5Msg[6] := Alltrim(SC5->C5_MSG2)
        ENDIF

        IF EMPTY(aSC5Msg[7])
            aSC5Msg[7] := Alltrim(SC5->C5_MSG3)
        ENDIF
        TMPMSG->(dbSkip())

    enddo

    For n1 := 1 to Len(aTxLgl)
        if   SZ1->(DbSeek(xFilial("SZ1")+aTxLgl[n1]))
            if    !EMPTY(SZ1->Z1_TEXT1)
                cSZ1Msg += alltrim(SZ1->Z1_TEXT1) + " "
            endif
            if    !EMPTY(SZ1->Z1_TEXT2)
                cSZ1Msg += alltrim(SZ1->Z1_TEXT2) + " "
            endif
        endif
    Next n1

    For nX := 1 to Len(aSC5Msg)

        if !Empty(aSC5Msg[nX])

            cSC5Msg += alltrim(aSC5Msg[nX]) + " "

        endif

    Next nX

    cMensFis := alltrim(alltrim(cMensFis)+" " +cMsgAlm+" "+cMsgPed+" "+alltrim(cSC5Msg)+" "+alltrim(cSZ1Msg)+" ")
Return

/*/{Protheus.doc} fGetPedCli

    REGRA01 PEDIDO CLIENTE POR ITEM E NA TAG DO XML
    REGRA02 AVALIA SE ESTÁ PREENCHIDO O CAMPO B1_REFEREN
    REGRA03 AVALIA SE POSSUI NOTA DE ORIGEM
    @author  Gabriel Araujo
    @param   (aProd,aPedCom,aNota)
    @since   24-10-2019

/*/

Static Function fGetPedCli(aProd,aPedCom,aNota)

    Local cSql := ""
    Local cEol := chr(10)
    aPedCom :={}

    For nX := 1 to Len(aProd)

        if SC6->(FieldPos("C6_ITEMWEG")) <> 0
            cSql :="SELECT      DISTINCT SD2.D2_ITEM,SD2.D2_PEDIDO,             " + cEol
            cSql +="SC5.C5_PEDCLI, SC6.C6_ITEMWEG, SD2.D2_NFORI,SD2.D2_SERIORI , SB1.B1_REFEREN" + cEol
        else
            cSql :="SELECT      DISTINCT SD2.D2_ITEM,C6_NUMPCOM D2_PEDIDO,  " + cEol
            cSql +="SC5.C5_PEDCLI, C6_ITEMPC  C6_ITEMWEG , SD2.D2_NFORI,SD2.D2_SERIORI , SB1.B1_REFEREN " + cEol
        endif

        cSql +="  FROM      dbo."+RetSQLTab("SD2")+"   (NOLOCK)    " + cEol
        cSql +="  LEFT JOIN dbo."+RetSQLTab("SC5")+"  (NOLOCK)     " + cEol
        cSql +="    ON SC5.D_E_L_E_T_ = ''                         " + cEol
        cSql +="   AND SC5.C5_FILIAL  = SD2.D2_FILIAL              " + cEol
        cSql +="   AND SC5.C5_CLIENTE = SD2.D2_CLIENTE             " + cEol
        cSql +="   AND SC5.C5_LOJACLI = SD2.D2_LOJA                " + cEol
        cSql +="   AND SC5.C5_NUM     = SD2.D2_PEDIDO              " + cEol
        cSql +="  LEFT JOIN dbo."+RetSQLTab("SC6")+" (NOLOCK)      " + cEol
        cSql +="    ON SC6.D_E_L_E_T_ = ''                         " + cEol
        cSql +="   AND SC6.C6_FILIAL  = SD2.D2_FILIAL              " + cEol
        cSql +="   AND SC6.C6_NUM     = SD2.D2_PEDIDO              " + cEol
        cSql +="   AND SC6.C6_CLI     = SD2.D2_CLIENTE             " + cEol
        cSql +="   AND SC6.C6_LOJA    = SD2.D2_LOJA                " + cEol
        cSql +="   AND SC6.C6_ITEM    = SD2.D2_ITEMPV              " + cEol
        cSql +="   AND SC6.C6_PRODUTO = SD2.D2_COD                 " + cEol
        cSql +="      LEFT JOIN dbo."+RetSQLTab("SB1")+"  (NOLOCK) " + cEol
        cSql +="  ON SB1.D_E_L_E_T_ = '' AND SB1.B1_FILIAL = ''    " + cEol
        cSql +="  AND B1_COD = SD2.D2_COD                          " + cEol
        cSql +=" WHERE      SD2.D_E_L_E_T_    = ''                 " + cEol
        cSql +="			AND SD2.D2_DOC      = " + ValtoSql(aNota[2]) + cEol
        cSql +="			AND SD2.D2_SERIE    = " + ValtoSql(aNota[1]) + cEol
        cSql +="			AND SD2.D2_FILIAL   = " + ValtoSql(XFilial("SD2"))          + cEol
        cSql +="			AND SD2.D2_COD      = " + ValtoSql(aProd[nX][2]) + cEol
        cSql +="			AND SD2.D2_PEDIDO   = " + ValtoSql(aProd[nX][38]) + cEol
        cSql +="			AND SD2.D2_ITEMPV      = " + ValtoSql(aProd[nX][39]) + cEol
        cSql +="ORDER BY 1 "

        CONOUT("QUERY PEDIDO")
        conout(cSql)

        If (Select("PEDIDO") <> 0)

            dbSelectArea("PEDIDO")
            dbCloseArea()

        Endif

        TCQuery cSql NEW ALIAS "PEDIDO"
        if(PEDIDO->(!Eof()))

            If	!Empty(PEDIDO->B1_REFEREN)
                aProd[NX][4] := ALLTRIM(aProd[NX][4]) + " Referen "+ALLTRIM(PEDIDO->B1_REFEREN)
            EndIf

            if !Empty(PEDIDO->D2_NFORI)
                aProd[NX][4] := ALLTRIM(aProd[NX][4]) + " NF/Serie "+ALLTRIM(PEDIDO->D2_NFORI) + ' - ' + alltrim(PEDIDO->D2_SERIORI)
            EndIf

            /*INICIO AJUSTE DO PEDIDO DE COMPRA DO CLIENTE*/
            If !Empty(PEDIDO->C5_PEDCLI) //.And. !Empty(SC6->C6_ITEMWEG) .And. Right(RTrim(SC6->C6_CF),3) $ '101/102/124'
                If	At(PEDIDO->C5_PEDCLI,'-OP') <> 0 // Situaï¿½ï¿½o para cliente Franklin
                    nPos := At(SC5->C5_PEDCLI,'-')
                    If	nPos <> 0
                        aadd(aPedCom,{Substr(PEDIDO->C5_PEDCLI,1,nPos-1),PEDIDO->C6_ITEMWEG})
                    EndIf
                Else
                    aadd(aPedCom,{PEDIDO->C5_PEDCLI,iif(Empty(PEDIDO->C6_ITEMWEG ),"0001",PEDIDO->C6_ITEMWEG )})
                EndIf
            Else
                aadd(aPedCom,{})
            EndIf
            // PREENCHIMENTO PARA COMPLEMENTAR A DESCRICAO
            // ALIENACAO
            //aProd[nX][2]
            dbSelectArea("SB5")
            SB5->(dbSetOrder(1))
            If SB5->(dbSeek(xFilial("SB5")+aProd[nX][2]))
                IF !EMPTY(SB5->B5_CEME)

                    aProd[NX][4] := ALLTRIM(aProd[NX][4])+" - " + ALLTRIM(SB5->B5_CEME)

                ENDIF
            ENDIF
        ENDIF
    Next nX
Return

/*/{Protheus.doc} fProc3UM
    ROtina para ajustar a Unidade de Medida e Quantidade
    Solicitacao Joici, feita conforme o cadastro da SA7
    @type  Function
    @author Gabriel
    @since 18/12/2020

/*/

Static Function fProc3UM(aProd,aNota,aDest)
    Local cCodCli := ""
    Local cLojCli := ""
    Local cCodProd := ""
    Local nQtd := 0
    Local nQtOri := 0
    conout("gda")
    //DbSelectArea("SA7")
    //SA7->(dbSetOrder(1))
    ////A7_FILIAL, A7_CLIENTE, A7_LOJA, A7_PRODUTO, R_E_C_N_O_, D_E_L_E_T_
    //IF 	SA7->(MsSeek(xFilial("SA7")+SF2->F2_CLIENTE + SF2->F2_LOJA+SD2->D2_COD))
    //endif
    DbSelectArea("SA7")
    SA7->(dbSetOrder(1))
    DbSelectArea("SA1")
    SA1->(dbSetOrder(3))
    IF 	SA1->(MsSeek(xFilial("SA1")+ aDest[1]))
        cCodCli := SA1->A1_COD
        cLojCli := SA1->A1_LOJA
    endif

    nPosUm3 := 11
    nQt3Um3 := 12
    conout("gda")
    For nX := 1 to Len(aProd)
        cCodProd := aProd[nX][2]
        nQtOri := aProd[nX][9]
        //    IF 	SA7->(MsSeek(xFilial("SA7")+ cCodCli+cLojCli+cCodProd))
        IF 	SA7->(MsSeek(xFilial("SA7")+ aNota[7]+aNota[8]+cCodProd))
            if ALLTRIM(SA7->A7_NF3UM) $ "S"

                cUm := SA7->A7_UM3

                IF ALLTRIM(SA7->A7_TPCONV) $ "D"
                    nQtd := nQtOri / SA7->A7_CONV3

                ELSE
                    nQtd := nQtOri * SA7->A7_CONV3
                ENDIF

                if nQtd != 0

                    aProd[nX][8] := cUm
                    aProd[nX][9] := nQtd

                    aProd[nX][nPosUm3] := cUm
                    aProd[nX][nQt3Um3] := nQtd

                endif
            ENDIF
        endif
    next nX

Return
