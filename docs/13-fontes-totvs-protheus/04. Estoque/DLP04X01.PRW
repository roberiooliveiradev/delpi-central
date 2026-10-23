
#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"


/*
DLP04X01A - função para retornar o ultimo SB7
*/
USER FUNCTION DLP04X01A(cFilPrd,cCodProd,cLocArm)

    DEFAULT cFilPrd   = ''
    DEFAULT cCodProd  = ''
    DEFAULT cLocArm   = ''
    Local cDtRet := ctod("")
    Local cEol := chr(10)

    cSql := "SELECT MAX(ISNULL(B7_DATA, '')) B7_DATA " + cEol
    cSql += "   FROM "+ RetSqlName("SB7") + " SB7 (NOLOCK)  " + cEol
    cSql += "   WHERE SB7.D_E_L_E_T_ = ''
    cSql += "        AND B7_FILIAL   = " + valtosql(cFilPrd) + cEol
    cSql += "        AND B7_COD      = " + valtosql(cCodProd) + cEol
    if !empty(cLocArm)
        cSql += "        AND B7_LOCAL    = " + valtosql() + cEol
    endif


    If ( Select ( "TMPSB7" ) <> 0 )
        dbSelectArea ( "TMPSB7" )
        dbCloseArea ()
    ENDIF

    TCQuery cSql NEW ALIAS "TMPSB7"

    IF TMPSB7->(!eof())

        cDtRet := STOD(TMPSB7->B7_DATA)

    ENDIF


rETURN  cDtRet






/*/{Protheus.doc} fQryUltCmp
    (long_description)
    @type  Function
    @author Luan Woichechoscki
    @since 04/08/2022
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
USER Function DLP04X1B(cCod, cFilcmp,dDtDig,nOpc)

    Local cQueryComp    :=  ""
    Local aRet          :=  {}
    xRet := ""

    cQueryComp  :=  "SELECT TOP 1 SD1.*,SD1.R_E_C_N_O_,A5_CODPRF "+CRLF
    cQueryComp  +=  "FROM " + RETSQLNAME("SD1") + " SD1 (nolock) "+CRLF
    cQueryComp  +=  "   JOIN " + RETSQLNAME("SF4") + " SF4 (nolock) ON "+CRLF
    if  cEmpAnt != '05'
        if substr(cCod,1,2) $"41_51"
            cQueryComp  +=  "       SF4.D_E_L_E_T_='' AND F4_CODIGO=D1_TES  AND F4_DUPLIC ='S' "+CRLF
        ELSE
            cQueryComp  +=  "       SF4.D_E_L_E_T_='' AND F4_CODIGO=D1_TES AND F4_ESTOQUE ='S' AND F4_DUPLIC ='S' "+CRLF
        ENDIF
        //  if  cEmpAnt == '05'
    ELSE
        cQueryComp  +=  "       SF4.D_E_L_E_T_='' AND F4_CODIGO=D1_TES  AND F4_ESTOQUE ='S' "+CRLF
    ENDIF
    cQueryComp  +=  " and F4_FILIAL = ''   and F4_TIPO = 'E' AND F4_CODIGO < '500' "+CRLF
    /*A5_FILIAL	A5_FORNECE	A5_LOJA	A5_PRODUTO
    000042	01	10080061*/
    cQueryComp  +=  "   LEFT JOIN " + RETSQLNAME("SA5") + " SA5 ON "+CRLF
    cQueryComp  +=  "       SA5.D_E_L_E_T_='' " +CRLF
    cQueryComp  +=  "       AND SA5.A5_FILIAL = " +  valtosql(XFILIAL("SA5"))
    cQueryComp  +=  "       AND A5_PRODUTO=D1_COD   " +CRLF
    cQueryComp  +=  "        AND A5_LOJA = D1_LOJA   " +CRLF
    cQueryComp  +=  "        AND A5_FORNECE=D1_FORNECE "+CRLF
    //cQueryComp  +=  "	    AND D1_EMISSAO=F1_EMISSAO AND D1_SERIE=F1_SERIE AND F1_TIPO='N' AND (F1_ESPECIE='SPED' OR F1_ESPECIE='NFE') "+CRLF
    cQueryComp  +=  "WHERE D1_FILIAL='" + cFilcmp + "' " + CRLF
    cQueryComp  +=  " AND D1_COD=" +valtosql(cCod) + CRLF
    cQueryComp  +=  " AND D1_DTDIGIT <=" +valtosql(dDtDig) + CRLF
    cQueryComp  +=  " AND D1_QUANT <> 0 " + CRLF
    cQueryComp  +=  " AND D1_TES <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_DOC <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_SERIE <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_FORNECE <> '   ' " + CRLF
    cQueryComp  +=  " AND D1_LOJA <> '   ' " + CRLF
    // cQueryComp  +=  "and D1_NUMSEQ < "+valtosql(cNumSeq)+" AND SD1.D_E_L_E_T_ ='' "+CRLF
    cQueryComp  +=  "ORDER BY D1_NUMSEQ DESC "

    If Select('cAlias2') > 0
        Dbselectarea('cAlias2')
        cAlias2->(DbClosearea())
    EndIf

    TcQuery cQueryComp New Alias cAlias2
    if  cAlias2->(!eof())
        //posicionar no nome do fornecedor
        DbSelectArea("SA2")
        DbSetOrder(1)
        cFornecedor := alltrim(POSICIONE("SA2",1,XFILIAL("SA2") + cAlias2->D1_FORNECE + cAlias2->D1_LOJA, "A2_NOME"))
        SA2 ->(DbClosearea())

        //    Return(  {;
        //        /*Fornc.Nome*/cAlias2->D1_FORNECE + cAlias2->D1_LOJA+" / "+ cFornecedor           ,;
        //        /*Loja      */cAlias2->D1_LOJA      ,;
        //        /*NFISCAL   */cAlias2->D1_DOC       ,;
        //        /*Serie     */cAlias2->D1_SERIE     ,;
        //        /*Quantidade*/cAlias2->D1_QUANT     ,;
        //        /*Vlr. Unit */cAlias2->D1_VUNIT      ,;
        //        /*Total     */cAlias2->D1_TOTAL     ,;
        //        /*Emissao   */StoD(cAlias2->D1_EMISSAO)    ,;
        //        /*COD FOR   */cAlias2->A5_CODPRF   ,;
        //        })
        //    // else
        //    //     aRet    := {}
    endif
    if nOpc == 1
        xRet := cAlias2->A5_CODPRF
    endif

    if nOpc == 2
        xRet := cAlias2->D1_FORNECE + cAlias2->D1_LOJA+" / "+ cFornecedor
    endif
Return xRet




USER Function DLP04X1C(cCodProd,cCodRec)
    default cCodProd := ""
    Default cCodRec := (cAliasSH6)->H6_RECURSO

    lOCAL cEol := CHR(10)
    Local cSql := ""
    lOCAL aRet :={}
    cSql+="SELECT TOP 1 'MOD'+LTRIM(RTRIM(SH1.H1_CCUSTO))[CODPROD],LTRIM(RTRIM(SG2.G2_RECURSO))+' '+LTRIM(RTRIM(SG2.G2_DESCRI)) [DESC],G2_TEMPAD, ISNULL(SBZ.BZ_CUSTD,0.00) BZ_CUSTD ,G2_SETUP, H1_MAOOBRA" + cEol
    cSql+="FROM dbo." + retsqlname("SG2") + " SG2(NOLOCK)" + cEol
    cSql+="     JOIN dbo." + retsqlname("SH1") + " SH1(NOLOCK)ON SH1.D_E_L_E_T_=''" + cEol
    cSql+="                                   AND SG2.G2_FILIAL=SH1.H1_FILIAL" + cEol
    cSql+="                                   AND SG2.G2_RECURSO=SH1.H1_CODIGO" + cEol
    cSql+="    LEFT JOIN dbo." + retsqlname("SBZ") + " SBZ(NOLOCK)ON SBZ.D_E_L_E_T_=''" + cEol
    cSql+="                                   AND SG2.G2_FILIAL=SBZ.BZ_FILIAL" + cEol
    cSql+="                                   AND SBZ.BZ_COD='MOD'+LTRIM(RTRIM(SH1.H1_CCUSTO))" + cEol
    cSql+="WHERE SG2.D_E_L_E_T_='' " + cEol
    //   cSql+=" AND SG2.G2_PRODUTO=" +valtosql(cCodProd) + cEol
    cSql+="AND SG2.G2_FILIAL = " +VALTOSQL(XFILIAL("SG2"))+ cEol
    //cSql+="AND SG2.G2_OPERAC = " +VALTOSQL(cCodOp)+ cEol
    cSql+="AND SG2.G2_RECURSO = " +VALTOSQL(cCodRec)+ cEol
    cSql+="ORDER BY 1  "
    If Select('TMPSG2') <> 0
        TMPSG2->(dbCloseArea())
    Endif

    TCQuery cSql Alias TMPSG2 New
    While TMPSG2->(!eof())

        xRet := TMPSG2->BZ_CUSTD
        //   AADD(aRet,{TMPSG2->CODPROD,TMPSG2->DESC,TMPSG2->G2_TEMPAD,TMPSG2->BZ_CUSTD,TMPSG2->G2_SETUP,H1_MAOOBRA})

        TMPSG2->(dbskip())
    Enddo

    TMPSG2->(dbCloseArea())
Return xRet

USER Function DLP04X1D(cTMP,cCodRec)
    DEFAULT cTMP := ""
    DEFAULT cCodRec := ""
    local nCust := 0.00
    Local xTmp := nil
    conout("stop")

    IF EMPTY(cTMP)
        cTMP := TimeH6(Nil,Nil,cAliasSH6)
    ENDIF
    IF EMPTY(cCodRec)
        cCodRec := (cAliasSH6)->H6_RECURSO
    ENDIF
    nCust :=  u_DLP04X1C(cCodRec,cCodRec)
    xTmp :=  Val(StrTran(A680ConvHora(cTMP, "C", "N"), ":", "."))

    xRet := xTmp*nCust
    conout("stop")

REturn xRet

USER Function DLP04X1E(cTMP,cCodRec)
    DEFAULT cTMP := ""
    DEFAULT cCodRec := ""
    local nCust := 0.00
    Local xTmp := nil
    conout("stop")

    IF EMPTY(cTMP)
        cTMP := TimeH6(Nil,Nil,cAliasSH6)
    ENDIF
    IF EMPTY(cCodRec)
        cCodRec := (cAliasSH6)->H6_RECURSO
    ENDIF
    nCust :=  u_DLP04X1C(cCodRec,cCodRec)
    xTmp :=  (Val(StrTran(A680ConvHora(cTMP, "C","C" ), ":", ".")) )

    xRet := xTmp*nCust
    conout("stop")

REturn xRet
