#Include "Protheus.ch"
#Include "RwMake.ch"
#Include "TbiConn.ch"
#Include "totvs.ch"
#INCLUDE "TOPCONN.CH"

user function DLP73F05()

    Local cEstResp := "000001_000002_000004_000005_000006_000007_000010_000011"//Estagio Responsavel
    Local cTo      :=""
    Local cCC      :=""
    Local cBCC     := "gabriel.araujo@totvs.com.br; orcamentos@delpi.com.br; orcamentos4@delpi.com.br"
    Local cTitu    :=  TRIM(AD1->AD1_NROPOR)+" - "+TRIM(AC2->AC2_STAGE) +" - "+TRIM(AC2->AC2_DESCRI)
    lOCAL cEol := CHR(10)
    //:cTo,  :cCC e :cBCC




    dbSelectArea("AO3")
    AO3->(dbSetOrder(1))
    (dbseek(xFilial("AO3")+AD1->AD1_USER))
    if Empty(AO3->AO3_CODEQP)
        if ALLTRIM(AD1->AD1_CODCLI) $ "000001"
            cCodEqui := "000001"
        ELSE
            cCodEqui := "000002"
        ENDIF
    else
        cCodEqui := AO3->AO3_CODEQP
    endif
    dbSelectArea("ACA")
    ACA->(dbSetOrder(1))

    if !( ALLTRIM(AC2->AC2_STAGE) $ cEstResp)

        cCC :=  fGetMail(cCodEqui)

    endif
    //  If ACA->(dbseek(xFilial("ACA")+cCodEqui))

    // cTo:= UsrRetMail(ACA->ACA_USRESP)

    cTo:= IIF(EMPTY(cTo),"",";")+TRIM(UsrRetMail(AD1->AD1_USER))

    CONOUT("TITULO ->"+cTitu)
    CONOUT("cCC ->"+cCC)
    CONOUT("cTo ->"+cTo)
    // CONOUT("TITULO ->"+cTitu)
    oProcess := TWFProcess():New("DLP73F05","WFDELPICRM" )
    oProcess:NewTask("DLP73F05","\WF\DelpiWFCrm.html")
    oProcess:cSubject := cTitu
    oProcess:cTo      := cTo
    if !EMPTY(cCC)
        oProcess:cCC      := cCC
    endif
    oProcess:cBCC := cBCC
    /*  oProcess:oHtml:ValByName("cDescProp"  ,TRIM(AC2->AC2_STAGE) +" - "+TRIM(AC2->AC2_DESCRI) )
    oProcess:oHtml:ValByName("cDescEsta"  , TRIM(AD1->AD1_NROPOR)+" - "+TRIM(AD1->AD1_DESCRI) )  */
    oProcess:oHtml:ValByName("cDescProp"  , TRIM(AD1->AD1_NROPOR)+" - "+TRIM(AD1->AD1_DESCRI) )
    oProcess:oHtml:ValByName("cDescEsta"  , TRIM(AC2->AC2_STAGE) +" - "+TRIM(AC2->AC2_DESCRI) )

    cSql :=" SELECT R_E_C_N_O_ [RECAOB]	  " + cEol

    cSql+=" FROM  dbo."+RetSQLName("AOB")+"  AOB (NOLOCK) 	" + cEol
    cSql+=" WHERE AOB.D_E_L_E_T_ = '' 	" + cEol
    cSql+="   AND AOB.AOB_FILIAL = '' " + cEol
    cSql+="   AND AOB.AOB_ENTIDA = 'AD1' " + cEol
    cSql+="   AND AOB.AOB_CHAVE = " + VALTOSQL(AD1->AD1_FILIAL+AD1->AD1_NROPOR)  + cEol
    cSql+=" ORDER BY 1 "

    If (Select("TMP1") <> 0)

        dbSelectArea("TMP1")
        dbCloseArea()

    Endif
    TCQuery cSql NEW ALIAS "TMP1"
    // percorro a query gerando o array conforme os campos de selecao
    DbSelectArea( "AOB" )
    While TMP1->(!Eof())

        AOB->(Dbgoto( TMP1->RECAOB))

        cOwner := ALLTRIM(AOB->AOB_OWNER)+" - "+ALLTRIM(UsrFullName(AOB->AOB_OWNER))

        AAdd(  oProcess:oHtml:ValByName("TB.cProp" ), cOwner )
        AAdd(  oProcess:oHtml:ValByName("TB.cDTAnot" ), DTOC(AOB->AOB_DTNOTA) )
        AAdd(  oProcess:oHtml:ValByName("TB.cTitAnot" ),   alltrim(AOB->AOB_TITULO) )
        AAdd(  oProcess:oHtml:ValByName("TB.cMemAnot"),  alltrim(AOB->AOB_CONTEU) )

        TMP1->(dbSkip())

    EndDo
    oProcess:Start()
    oProcess:Finish()

    //  ENDIF
RETURN


Static Function fGetMail(cCodEqui)

    Local cRetMail :=""
    Local cSql :=""
    Local cEol := chr(10)

    cSql :="SELECT AO3.AO3_CODUSR " +cEol
    cSql +="    FROM dbo." + RETSQLNAME("AO3")  + " AO3 (NOLOCK) " +cEol
    cSql +="WHERE AO3.D_E_L_E_T_ = ''    " +cEol
    cSql +="      AND AO3.AO3_CODEQP = "+valtosql(cCodEqui)

    cQuery := cSql

    conout(cQuery)



    If ( Select ( "TRBEQUI" ) <> 0 )
        dbSelectArea ( "TRBEQUI" )
        dbCloseArea ()
    Endif
    TCQuery cQuery NEW ALIAS "TRBEQUI"


    While  TRBEQUI->(!Eof())

        cRetMail += IIF(EMPTY(cRetMail),"",";")+TRIM(UsrRetMail(TRBEQUI->AO3_CODUSR))
        TRBEQUI->(DbSkip())
    EndDo
    TRBEQUI->(DbCloseArea())

Return cRetMail
