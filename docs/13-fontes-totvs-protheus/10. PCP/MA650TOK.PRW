
uSER FUNCTION MA650TOK
    Local lRet := .t.
    Local cDayOfW := "7_1" //sabado e domingo
    Local cDtOP    := alltrim(cvaltochar(dow( M->C2_DATPRF )))
    Local cDtOPIn  := alltrim(cvaltochar(dow( M->C2_DATPRi )))
    Local cDtEmiss := alltrim(cvaltochar(dow( M->C2_EMISSAO )))
    Local cDATPer  := iif(cEmpAnt == "01" .and. cFilAnt == "02",ALLTRIM(supergetmv("MV_ZDTPRD",.F.,"20240302|20240309|20240316|20240323|20240330")) ,"")//data que permite dias para iniciar ordem de produção no sabado ou dumento
    Local lApsInUse  := SuperGetMv("MV_APS",.F.,"") $ "DRUMMER*TOTVS"
    Local cBzMrp := ""
    Local cTipPrd := ""

    /* Retirado conforme solicitação da Joic
	Alterado - Gabriel Araujo - TOTVS SC
	Data 24/01/2019
	If	cEmpAnt == '01'
		DLP033()lOCAL
    EndIf*/
    conout("procname "+procname())

    conout("funname "+funname())
    conout("IsInCallStack " + cvaltochar(IsInCallStack("WS650PPO") ))
    IF IsInCallStack("WS650PPO")

        RETURN .T.

    ENDIF
    //Validacao
    IF lApsInUse .AND. (INCLUI .OR. ALTERA)

        cBzMrp := POSICIONE("SBZ",1,xFilial("SBZ")+M->C2_PRODUTO,"BZ_MRP")
        cTipPrd := POSICIONE("SB1",1,xFilial("SB1")+M->C2_PRODUTO,"B1_TIPO")

        IF (cTipPrd == "PA" .AND. cBzMrp != "S")

            FWAlertWarning("Não é permitida a inclusão/alteração de Ordem de Produção O Produto: "+ALLTRIM(M->C2_PRODUTO)+" - Deve estar habilitado para integração com o APS","Delpi - PCP - APS")
            lret := .F.

        ENDIF

    ENDIF

    IF( (cDtOP $ cDayOfW .and.!( DTOS( M->C2_DATPRF) $ cDATPer) ) .or. (cDtOPIn $ cDayOfW) .and.!( DTOS( M->C2_DATPRi) $ cDATPer)  ) .AND. (INCLUI .OR. ALTERA)
        if !isBlind()
            Aviso("DELPI","Não é permitido Incluir OP nos Dias de Sabado e Domingo",{"OK"})
        else
            conout("DELPI","Não é permitido Incluir OP nos Dias de Sabado e Domingo")
        endif
        lRet := .F.
    ENDIF

    cDtOP    :=  M->C2_DATPRF
    cDtOPIn  :=  M->C2_DATPRI
    cDtEmiss :=  M->C2_EMISSAO
    //Validação para nao permitir que sejam alteradas ou inseridas datas menores que a emissao da OP
    if cEmpAnt == "01"
        if lRet .and. (cDtOP <  cDtEmiss .OR. cDtOPIn  <  cDtEmiss)
            if !isBlind()
                Aviso("DELPI - Atenção","Não é permitido Previsao Entrega ou Inicio inferior a data de Emissao da OP",{"OK"})
            else
                conout("DELPI - Atenção","Não é permitido Previsao Entrega ou Inicio inferior a data de Emissao da OP")
            endif
            lRet := .F.
        ENDIF
    elseif cEmpAnt == "05"
        if lRet .and. (cDtOP <  cDtEmiss)
            M->C2_DATPRF :=cDtEmiss
            //  Aviso("DELPI - Atenção","Não é permitido Previsao Entrega ou Inicio inferior a data de Emissao da OP",{"OK"})
            //lRet := .F.
        ENDIF
        if lRet .and. (cDtOPIn  <  cDtEmiss)
            CONOUT("DELPI - Atenção","Não é permitido Previsao Entrega ou Inicio inferior a data de Emissao da OP")
            //lRet := .F.
            M->C2_DATPRI :=cDtEmiss
        ENDIF
    ENDIF
rETURN lret
