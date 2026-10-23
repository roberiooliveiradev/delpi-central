#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.CH"
#INCLUDE "FWADAPTEREAI.CH"

/*/{Protheus.doc} DLP05F01

    ROTINA PARA ALTERAR O PEDIDO DE VENDA PARA ADICIONAR OS ITENS DE RETORNO

    @since   14-10-2020
/*/


USER FUNCTION DLP05F01()
    if  cFilAnt != '02'
        if MSGYESNO( "Gera Retorno ?", "Delpi" )
            FWMsgRun(, {|| fProc() }, "DELPI", "Processando Pedido "+ alltrim(SC5->C5_NUM) )
        endif
    endif
RETURN

/************************************************\
|| fProc | apenas para rodar o FWMsgRun         ||
\************************************************/

Static Function fProc()

    Local nTmIt     := getsx3cache("C6_ITEM","X3_TAMANHO")
    lOCAL aArea     := getarea()
    Local aCabec    := {}
    Local aItens    := {}
    Local aLinha    := {}
    Local aEstTMP   := {}
    Local aEstru    := {}
    Local aPrdMP := {}
    Private cEol        := chr(10)
    Private lMsErroAuto := .F.
    Private nEstru 	    := 0

    cSql:=" SELECT * FROM  dbo." + retsqlname("SC6") + "  SC6(NOLOCK) " +cEol
    cSql+=" WHERE SC6.D_E_L_E_T_='' " + cEol
    cSql+="     AND SC6.C6_NUM    = "+ valtosql(SC5->C5_NUM) + cEol
    cSql+="     AND SC6.C6_FILIAL = "+ valtosql(SC5->C5_FILIAL) + cEol
    cSql+=" ORDER BY C6_ITEM "

    If Select('TSC6') <> 0
        TSC6->(dbCloseArea())
    Endif

    TCQuery cSql Alias TSC6 New

    While TSC6->(!eof())
        aEstTMP := {}
        nEstru 	:= 0
        aEstTMP := Estrut(TSC6->C6_PRODUTO)

        //aadd(aEstru,aEstTMP)
        For n1 := 1 to Len(aEstTMP)
            cTpPrd := alltrim( posicione("SB1",1,XFILIAL("SB1")+aEstTMP[n1][3],"B1_TIPO"))
            cTpMat := alltrim( posicione("SB1",1,XFILIAL("SB1")+aEstTMP[n1][3],"B1_TPMAT"))
            // conout("***********************************************")
            // conout("**  aEstTMP[n1][3] "+ aEstTMP[n1][3])
            // conout("**  cTpPrd "+ cTpPrd)
            // conout("**  cTpMat "+ cTpMat)
            // conout("***********************************************")
            //  if ! MSGYESNO( "Dar continuidade ?", "Delpi 01 " )
            //      Return
            //  Endif
            if cTPPrd $ "MP" .AND. cTpMat $'2'


                //  conout("***********************************************")
                //  conout("Entrou no IF")
                //  conout("**  aEstTMP[n1][3] "+ aEstTMP[n1][3])
                //  conout("**  aEstTMP[n1][4]*TSC6->C6_QTDVEN "+ cvaltochar(aEstTMP[n1][4]*TSC6->C6_QTDVEN))
                //  conout("**  TSC6->C6_PRODUTO "+ TSC6->C6_PRODUTO)
                //  conout("***********************************************")

                AADD(aPrdMP,{aEstTMP[n1][3],aEstTMP[n1][4]*TSC6->C6_QTDVEN,TSC6->C6_PRODUTO})
            ENDIF
        Next n1
        CONOUT("HD")

        TSC6->(dbskip())

    Enddo
    TSC6->(dbCloseArea())
    //  if ! MSGYESNO( "Dar continuidade ? "+ cvaltochar(len(aPrdMP)), "Delpi 02 " )
    //      Return
    //  Endif
    if len(aPrdMP) > 0
        aItensRet := fGetItRet(aPrdMP)
        if LEN(aItensRet[2]) == 0 .or. LEN(aItensRet) == 0

            MSGALERT( "Não Existem Itens Aptos a Retornar", "Delpi" )
            restarea(aArea)
            RETURN

        endif

        IF aItensRet[1]

            nIt := soma1(REPLICATE("0",nTmIt))

            aadd(aCabec,{"C5_NUM",     SC5->C5_NUM ,Nil})
            aadd(aCabec,{"C5_TIPO",    SC5->C5_TIPO ,Nil})
            aadd(aCabec,{"C5_CLIENTE", SC5->C5_CLIENTE,Nil})
            aadd(aCabec,{"C5_LOJACLI", SC5->C5_LOJACLI,Nil})
            aadd(aCabec, {"C5_LOJAENT", SC5->C5_LOJAENT,   Nil})
            aadd(aCabec, {"C5_CONDPAG",  SC5->C5_CONDPAG, Nil})

            cSql:=" SELECT * FROM  dbo." + retsqlname("SC6") + "  SC6(NOLOCK) " +cEol
            cSql+=" WHERE SC6.D_E_L_E_T_='' " + cEol
            cSql+="     AND SC6.C6_NUM    = "+ valtosql(SC5->C5_NUM) + cEol
            cSql+="     AND SC6.C6_FILIAL = "+ valtosql(SC5->C5_FILIAL) + cEol
            cSql+=" ORDER BY C6_ITEM "

            If Select('TSC6') <> 0
                TSC6->(dbCloseArea())
            Endif

            TCQuery cSql Alias TSC6 New

            While TSC6->(!eof())

                nIt :=TSC6->C6_ITEM

                aLinha:={}

                aadd(aLinha,{"LINPOS","C6_ITEM",TSC6->C6_ITEM})
                aadd(aLinha,{"AUTDELETA","N",Nil})
                aadd(aLinha,{"C6_ITEM"      , TSC6->C6_ITEM     ,Nil})
                aadd(aLinha,{"C6_PRODUTO"   , TSC6->C6_PRODUTO  ,Nil})
                aadd(aLinha,{"C6_LOCAL"     , TSC6->C6_LOCAL    ,Nil})
                aadd(aLinha,{"C6_QTDVEN"    , TSC6->C6_QTDVEN ,Nil})
                aadd(aLinha,{"C6_QTDLIB"  , TSC6->C6_QTDVEN ,Nil})
                aadd(aLinha,{"C6_PRCVEN"    , TSC6->C6_PRCVEN ,Nil})
                aadd(aLinha,{"C6_TES"       , TSC6->C6_TES    ,Nil})
                aadd(aLinha,{"C6_NFORI"     , TSC6->C6_NFORI  ,Nil})
                aadd(aLinha,{"C6_SERIORI"   , TSC6->C6_SERIORI,Nil})
                aadd(aLinha,{"C6_ITEMORI"   , TSC6->C6_ITEMORI,Nil})
                aadd(aLinha,{"C6_IDENTB6"   , TSC6->C6_IDENTB6,Nil})
                aadd(aLinha,{"C6_ITEMWEG"   , TSC6->C6_ITEMWEG,Nil})

                aadd(aItens,aLinha)

                TSC6->(dbskip())

            Enddo
            TSC6->(dbCloseArea())

            For ni := 1 to Len(aItensRet[2])

                aLinha:={}
                nIt := soma1(nIt)
                if alltrim(aItensRet[2][ni][1]) $"10140231"
                    conout("Stop")
                endif
                aadd(aLinha,{"C6_ITEM"    , nIt  ,Nil})
                aadd(aLinha,{"AUTDELETA","N",Nil})
                nQtd   :=  a410Arred( aItensRet[2][ni][3],"C6_QTDVEN")
                nTotal :=  a410Arred(aItensRet[2][ni][4] * nQtd,"C6_VALOR")
                aadd(aLinha,{"C6_PRODUTO" , aItensRet[2][ni][1] ,Nil})
                aadd(aLinha,{"C6_LOCAL"   , aItensRet[2][ni][2] ,Nil})
                aadd(aLinha,{"C6_QTDVEN"  , nQtd ,Nil})
                aadd(aLinha,{"C6_QTDLIB"  , nQtd ,Nil})
                aadd(aLinha,{"C6_PRCVEN"  , aItensRet[2][ni][4] ,Nil})
                aadd(aLinha,{"C6_VALOR"  , nTotal ,Nil})
                aadd(aLinha,{"C6_TES"     , aItensRet[2][ni][5] ,Nil})
                aadd(aLinha,{"C6_NFORI"   , aItensRet[2][ni][6] ,Nil})
                aadd(aLinha,{"C6_SERIORI" , aItensRet[2][ni][7] ,Nil})
                aadd(aLinha,{"C6_ITEMORI" , aItensRet[2][ni][8] ,Nil})
                aadd(aLinha,{"C6_IDENTB6" , aItensRet[2][ni][9] ,Nil})
                aadd(aLinha,{"C6_ITEMWEG" , nIt,Nil})
                aadd(aItens,aLinha)

            Next ni

        ENDIF

        //   conout("aitensret")

        IF LEN(aItens)>0
            MSExecAuto({|x,y,z|mata410(x,y,z)},aCabec,aItens,4,.F.)
            If lMsErroAuto

                Mostraerro()

            EndIf
        EndIf
        if len(aItensRet[3])>0
            cTexto := "Produtos Sem Saldo Para Retornar"+cEol+cEol

            For nX := 1 to Len(aItensRet[3])
                cTexto+=    "Produto Acabado -> "+ alltrim(aItensRet[3][nX][4])+ " | "
                cTexto+=    "Produto Retorno -> "+ alltrim(aItensRet[3][nX][1])+ "  "+cEol
                cTexto+=    "Saldo   "+ cValtochar(aItensRet[3][nX][2])+ " | "
                cTexto+=    "Quantidade Retornar   "+ cValtochar(aItensRet[3][nX][3])+ "  "+cEol
                cTexto+=   alltrim(aItensRet[3][nX][5])+  "  "+cEol
            Next nX
            EEcView(cTexto, "Produtos")
        endif
    endif
    restarea(aArea)
RETURN
/************************************************\
|| fGetItRet | Retorna os itens que devem ser   ||
|| retornados nos pedidos                       ||
\************************************************/
Static function fGetItRet(aItem)
    Local aRet := {}
    Local aSB6Ret := {}

    Local cSql := ""


    /******************************************************************\
    || Query | a) Verifico se o produto possui componente na estrutura ||
    || b) Verifico se possui saldo na SB6                              ||
    || C) tes de devoluçao cadastrado                                  ||
    || d) Nao deixar retornar mais produto do que a conversaão         ||
    ||  quantidade * Qtd Componente                                    ||
    \******************************************************************/

    /*  cSql:=" SELECT DISTINCT SC6.C6_PRODUTO, SG1.G1_COMP, SC6.C6_QTDVEN, SG1.G1_QUANT, SUM(ISNULL(SB6.B6_SALDO,0)) B6_SALDO, SF4.F4_TESDV, SF4.F4_CODIGO, " + cEol
    cSql+=" (SG1.G1_QUANT*SC6.C6_QTDVEN) - ISNULL(SC61.C6_QTDVEN,0) [C6_QT_RET] " + cEol
    cSql+=" FROM dbo." + retsqlname("SC6") + "  SC6(NOLOCK)                                                  " + cEol
    cSql+="   LEFT  JOIN dbo." + retsqlname("SG1") + "  SG1(NOLOCK)ON SG1.D_E_L_E_T_ ='' AND SG1.G1_FILIAL = '' " + cEol
    cSql+="                                   AND SC6.C6_PRODUTO = SG1.G1_COD                               " + cEol
    cSql+="   JOIN dbo." + retsqlname("SB6") + "  SB6 (NOLOCK)ON SB6.D_E_L_E_T_ =''                       " + cEol
    cSql+="                                   AND SB6.B6_FILIAL  = SC6.C6_FILIAL                            " + cEol
    cSql+="                                   AND SB6.B6_PRODUTO = SG1.G1_COMP                              " + cEol
    cSql+="                                   AND SB6.B6_CLIFOR  = SC6.C6_CLI                               " + cEol
    cSql+="                                   AND SB6.B6_LOJA    = SC6.C6_LOJA                              " + cEol
    cSql+="                                   AND SB6.B6_SALDO>0                                            " + cEol
    cSql+="   LEFT  JOIN dbo." + retsqlname("SF4") + "  SF4 (NOLOCK)ON SF4.D_E_L_E_T_='' AND SF4.F4_FILIAL=''   " + cEol
    cSql+="                                   AND SF4.F4_CODIGO=SB6.B6_TES                      " + cEol
    cSql+="    LEFT JOIN dbo." + retsqlname("SC6") + "  SC61(NOLOCK)ON SC61.D_E_L_E_T_=''            " + cEol
    cSql+="                                    AND SC6.C6_FILIAL = SC61.C6_FILIAL               " + cEol
    cSql+="                                    AND SC6.C6_LOJA   = SC61.C6_LOJA                 " + cEol
    cSql+="                                    AND SC6.C6_CLI    = SC61.C6_CLI                  " + cEol
    cSql+="                                    AND SC6.C6_NUM    = SC61.C6_NUM                  " + cEol
    cSql+="                                    AND SG1.G1_COMP   = SC61.C6_PRODUTO              " + cEol
    cSql+=" WHERE SC6.D_E_L_E_T_=''  " + cEol
    cSql+=" AND SC6.C6_NUM    = " + valtosql(SC5->C5_NUM) + cEol
    cSql+=" AND SC6.C6_FILIAL= " + valtosql(SC5->C5_FILIAL) + cEol
    cSql+="      AND SC6.C6_PRODUTO !=SG1.G1_COMP " + cEol
    cSql+=" GROUP BY SC6.C6_PRODUTO, SG1.G1_COMP, SC6.C6_QTDVEN, SG1.G1_QUANT, SF4.F4_TESDV, SF4.F4_CODIGO, SC61.C6_QTDVEN " + cEol

    If Select('TMP1') <> 0
        TMP1->(dbCloseArea())
    Endif
    conout(cSql)
    TCQuery cSql Alias TMP1 New*/

    lContinua := .t.
    aErroSld := {}

    //  While TMP1->(!eof())
    For n2 := 1 to Len(aItem)
        nSldPV := 0
        cSqlC6 := "SELECT ISNULL(SUM(A.C6_QTDVEN - A.C6_QTDENT), 0) [SLDPV] " + cEol
        cSqlC6+=" FROM dbo." + retsqlname("SC6") + "  A (NOLOCK) " + cEol
        cSqlC6+=" WHERE A.D_E_L_E_T_ = '' " + cEol
        cSqlC6+="       AND A.C6_FILIAL  = " + VALTOSQL(XfILIAL("SC6")) + cEol
        cSqlC6+="       AND A.C6_NUM     = " + VALTOSQL(SC5->C5_NUM) + cEol
        cSqlC6+="       AND A.C6_CLI     = " + VALTOSQL(SC5->C5_CLIENTE ) + cEol
        cSqlC6+="       AND A.C6_LOJA    = " + VALTOSQL(SC5->C5_LOJACLI ) + cEol
        cSqlC6+="       AND A.C6_PRODUTO = " + VALTOSQL(aItem[n2][1])

        If Select('TMPC6') <> 0
            TMPC6->(dbCloseArea())
        Endif

        TCQuery cSqlC6 Alias TMPC6 New
        if !TMPC6->(eof())
            nSldPV:=TMPC6->SLDPV
        endif
        //        nSldTmp := TMP1->C6_QT_RET
        nSldTmp := aItem[n2][2] - nSldPV

        cProdMP := aItem[n2][1]
        //while para poder preencher array com as notas de retorno conforme saldo das notas
        while nSldTmp>0 //.and. lContinua
            //   IF  (TMP1->B6_SALDO < TMP1->C6_QT_RET .and. nSldTmp == TMP1->C6_QT_RET )
            //
            //       aadd(aErroSld, {TMP1->G1_COMP,TMP1->B6_SALDO, TMP1->C6_QT_RET,TMP1->C6_PRODUTO})
            //
            //   endif
            cSql1 := " SELECT SB6.B6_SALDO-SUM(ISNULL(SC6.C6_QTDVEN,0)-ISNULL(SC6.C6_QTDENT,0)) B6_SALDO, B6_EMISSAO,B6_FILIAL, B6_CLIFOR, B6_LOJA, B6_PRODUTO, B6_LOCAL, B6_SEGUM, B6_DOC," + cEol
            cSql1 += " B6_SERIE, B6_IDENT,  SB6.B6_PRUNIT,D1_IDENTB6,SD1.D1_TES , D1_ITEM FROM dbo." + retsqlname("SB6") + "  SB6 (NOLOCK) " + cEol
            cSql1 += " JOIN dbo." + retsqlname("SD1") + "  SD1(NOLOCK)ON SD1.D_E_L_E_T_=''" + cEol
            cSql1 += "      AND SD1.D1_FILIAL=SB6.B6_FILIAL " + cEol
            cSql1 += "      AND SD1.D1_COD=SB6.B6_PRODUTO" + cEol
            cSql1 += "      AND SB6.B6_DOC=SD1.D1_DOC" + cEol
            cSql1 += "      AND SB6.B6_SERIE=SD1.D1_SERIE" + cEol
            cSql1 += "      AND SD1.D1_IDENTB6=SB6.B6_IDENT " + cEol
            cSql1 += " LEFT JOIN dbo." + retsqlname("SC6") + "  SC6(NOLOCK)ON SC6.D_E_L_E_T_='' " + cEol
            cSql1 += "      AND SC6.C6_FILIAL=SB6.B6_FILIAL " + cEol
            cSql1 += "      AND SC6.C6_PRODUTO=SB6.B6_PRODUTO " + cEol
            cSql1 += "      AND SB6.B6_LOCAL=SC6.C6_LOCAL " + cEol
            cSql1 += "      AND SC6.C6_IDENTB6=SB6.B6_IDENT " + cEol
            cSql1 += " WHERE SB6.D_E_L_E_T_ = '' " + cEol
            cSql1 += "      AND SB6.B6_SALDO     >  0 " + cEol
            cSql1 += "      AND SB6.B6_FILIAL    = " + valtosql(SC5->C5_FILIAL      ) + cEol
            cSql1 += "      AND SB6.B6_CLIFOR    = " + valtosql(SC5->C5_CLIENTE  ) + cEol
            cSql1 += "      AND SB6.B6_LOJA      = " + valtosql(SC5->C5_LOJACLI  ) + cEol
            cSql1 += "      AND SB6.B6_PRODUTO   = " + valtosql(cProdMP    ) + cEol
            cSql1 += " GROUP BY B6_FILIAL, B6_CLIFOR, B6_LOJA, B6_PRODUTO, B6_LOCAL, B6_SEGUM, B6_DOC," + cEol
            cSql1 += " B6_SERIE, B6_IDENT, B6_SALDO,D1_IDENTB6, B6_EMISSAO, B6_PRUNIT, D1_ITEM,D1_TES" + cEol
            cSql1 += " HAVING SB6.B6_SALDO-SUM(isnull(SC6.C6_QTDVEN,0)-ISNULL(SC6.C6_QTDENT,0)) >0" + cEol
            cSql1 += " ORDER BY B6_EMISSAO;"

            /*INI WHILE TSB6*/
            If Select('TSB6') <> 0
                TSB6->(dbCloseArea())
            Endif

            TCQuery cSql1 Alias TSB6 New
            if TSB6->(eof())
                lContinua := .f.
                nSldTmp := 0
                //    conout("nao possui saldo parcial para devolução")

                aadd(aErroSld, {cProdMP,0,  aItem[n2][2] , aItem[n2][3],""})

            endif

            While (TSB6->(!eof()) ) .AND. nSldTmp > 0
                nqttmp := 0.00
                IF  TSB6->B6_SALDO  > 0

                    if TSB6->B6_SALDO < nSldTmp
                        nqttmp :=  TSB6->B6_SALDO
                    ELSE
                        nqttmp := nSldTmp
                    ENDIF
                    SF4->(DbSetorder(1))
                    SF4->(DbSeek(xFiliaL("SF4")+TSB6->D1_TES))
                    if !Empty(SF4->F4_TESDV)
                        cTesDv := SF4->F4_TESDV
                        AADD(aSB6Ret ,{TSB6->B6_PRODUTO;
                            ,TSB6->B6_LOCAL;
                            ,nqttmp;
                            ,TSB6->B6_PRUNIT;
                            ,cTesDv;
                            ,TSB6->B6_DOC;
                            ,TSB6->B6_SERIE;
                            ,TSB6->D1_ITEM;
                            ,TSB6->D1_IDENTB6;
                            })
                    else
                        aadd(aErroSld, {cProdMP,0,  aItem[n2][2] , aItem[n2][3], "Sem Tes De Devolucao cadastrada"})

                    endif
                endif
                TSB6->(dbskip())

                nSldTmp-= nqttmp // Subtraio a quantidade ja adicionada
            enddo
            TMPC6->(dbskip())
            /*FIM WHILE TSB6*/

            //verifico se ainda ficou saldo  para devolução
            if nSldTmp > 0
                //  lContinua := .f.
                //     conout("possui saldo parcial para devolução")
            endif

        enddo

    Next n2
    /*FIM WHILE  nSldTmp>0 .and. lContinua
        TMP1->(dbskip())

    Enddo
    TMP1->(dbCloseArea())*/

    aRet := {lContinua,aSB6Ret,aErroSld}
Return aRet





Static Function Estrutdlp(cProduto,nQuant,lOneLevel,lPreEstru)
    LOCAL nRegi
    LOCAL nQuantItem:=0
    LOCAL cCodigo,cComponente,cTrt,cGrOpc,cOpc

    DEFAULT lOneLevel := .F.
    DEFAULT lPreEstru := .F.

    nQuant:=IF(nQuant == NIL,1,nQuant)
    nEstru++
    If nEstru == 1
        aEstrutura:={}
    EndIf
    dbSelectArea(If(lPreEstru,"SGG","SG1"))
    dbSetOrder(1)
    dbSeek(xFilial()+cProduto)
    While !Eof() .And. If(lPreEstru,GG_FILIAL+GG_COD,G1_FILIAL+G1_COD) == xFilial()+cProduto
        nRegi:=Recno()
        cCodigo    :=If(lPreEstru,GG_COD,G1_COD)
        cComponente:=If(lPreEstru,GG_COMP,G1_COMP)
        cTrt       :=If(lPreEstru,GG_TRT,G1_TRT)
        cGrOpc     :=If(lPreEstru,GG_GROPC,G1_GROPC)
        cOpc       :=If(lPreEstru,GG_OPC,G1_OPC)
        If cCodigo != cComponente
            nProcura:=aScan(aEstrutura,{|x| x[1] == nEstru .And. x[2] == cCodigo .And. x[3] == cComponente .And. x[5] == cTrt})
            If nProcura  = 0
                nQuantItem:=ExplEstr(nQuant,nil,nil,nil,nil,lPreEstru)

                IF nQuantItem >0
                    AADD(aEstrutura,{nEstru,cCodigo,cComponente,nQuantItem,cTrt,cGrOpc,cOpc,Recno()})
                ENDIF

            EndIf

            If !lOneLevel
                nRecno:=Recno()
                dbSeek(xFilial()+cComponente)
                IF Found()
                    cCodigo:=If(lPreEstru,GG_COD,G1_COD)
                    Estrut(cCodigo,nQuantItem,nil,lPreEstru)
                    nEstru --
                Else
                    MsGoto(nRecno)
                    nProcura:=aScan(aEstrutura,{|x| x[1] == nEstru .And. x[2] == cCodigo .And. x[3] == cComponente .And. x[5] == cTrt})
                    If nProcura  = 0

                        nQuantItem:=ExplEstr(nQuant,nil,nil,nil,nil,lPreEstru)
                        IF nQuantItem >0
                            AADD(aEstrutura,{nEstru,cCodigo,cComponente,nQuantItem,cTrt,cGrOPc,cOpc,Recno()})
                        ENDIF

                    EndIf
                Endif
            EndIf
        EndIf
        MsGoto(nRegi)
        dbSkip()
    Enddo
Return(aEstrutura)
