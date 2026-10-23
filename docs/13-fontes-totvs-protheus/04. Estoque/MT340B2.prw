#include "protheus.ch"
User Function MT340B2( )

    conout("MT340B2 stop")


    //Local aArea:= getarea()
    // Local     nTMLocal := getsx3cache("B2_LOCAL","X3_TAMANHO")

    //Local lOpcAuto      := .T.
    //PRIVATE lMsErroAuto := .F.
    //Private lMsHelpAuto	:= .T.
    //Private lAutoErrNoFile  := .T.

    cCodPro := SB2->B2_COD

    //dbSelectArea("SBZ")
    //SBZ->(dbSetOrder(1))
    //SBZ->(dbSeek(xFilial("SBZ")+cCodPro))
    //RecLock('SBZ',.F.)
    //SBZ->BZ_DTINV := DATE()
    //SBZ->BZ_DTPTPD := CToD("")
    //SBZ->(MsUnLock())

    // regra para desbloquear produto do inventario
    SB1->(dbSetOrder(1))
    SB1->(MsSeek(xFilial('SB1')+cCodPro))

    //bloqueio do produto
    Pergunte("MTA271",.F.)
    MV_PAR01 := 2	                        // Quanto ao produto ?
    MV_PAR02 := "01"	        // Do   Armazem ?
    MV_PAR03 := "01"        // Ate  Armazem ?
    MV_PAR04 := SB1->B1_COD	 	        // Do   Produto ?
    MV_PAR05 := SB1->B1_COD	 	        // Ate' Produto ?
    MV_PAR06 := SB1->B1_TIPO	            // Do   Tipo ?
    MV_PAR07 := SB1->B1_TIPO	            // Ate' Tipo ?
    MV_PAR08 := SB1->B1_GRUPO	            // Do   Grupo ?
    MV_PAR09 := SB1->B1_GRUPO	            // Ate' Grupo ?
    MV_PAR10 := "***************"	         // Mascara ?
    MV_PAR11 := CTOD("01/01/2000")            // Da   Data ?
    MV_PAR12 := CTOD("01/01/2049")                      // Ate' Data ?
    MV_PAR13 := 2	                        // Dta do Inventário ?
    MV_PAR14 := date()                      // Data Informada ?
    MV_PAR15 := 2	                        // Seleciona filiais ?
    A271Proces(.F.)

    SB1->(dbSetOrder(1))
    SB1->(MsSeek(xFilial('SB1')+cCodPro))

    //bloqueio do produto
    Pergunte("MTA271",.F.)
    MV_PAR01 := 2	                        // Quanto ao produto ?
    MV_PAR02 := "99"	        // Do   Armazem ?
    MV_PAR03 := "99"        // Ate  Armazem ?
    MV_PAR04 := SB1->B1_COD	 	        // Do   Produto ?
    MV_PAR05 := SB1->B1_COD	 	        // Ate' Produto ?
    MV_PAR06 := SB1->B1_TIPO	            // Do   Tipo ?
    MV_PAR07 := SB1->B1_TIPO	            // Ate' Tipo ?
    MV_PAR08 := SB1->B1_GRUPO	            // Do   Grupo ?
    MV_PAR09 := SB1->B1_GRUPO	            // Ate' Grupo ?
    MV_PAR10 := "***************"	         // Mascara ?
    MV_PAR11 := CTOD("01/01/2000")            // Da   Data ?
    MV_PAR12 := CTOD("01/01/2049")                      // Ate' Data ?
    MV_PAR13 := 2	                        // Dta do Inventário ?
    MV_PAR14 := date()                      // Data Informada ?
    MV_PAR15 := 2	                        // Seleciona filiais ?
    A271Proces(.F.)



    // cGrupo := SB1->B1_GRUPO
    // cTipo := SB1->B1_TIPO
    //
    // conout("MT340D3 - ENTROU NA ROTINA Ç" )
    //
    // aParametros :={}
    //
    // AADD(aParametros, cCodPro)                 //  | mv_par01  || Produto de
    // AADD(aParametros, cCodPro)     //  | mv_par02  || Produto ate
    // AADD(aParametros, cGrupo )    //  | mv_par03  || Grupo de
    // AADD(aParametros, cGrupo)     //  | mv_par04  || Grupo ate
    // AADD(aParametros, cTipo)   //  | mv_par05  || Tipo de
    // AADD(aParametros, cTipo)   //  | mv_par06  || Tipo ate
    // AADD(aParametros, SPACE(nTMLocal))             //  | mv_par07  || Local de
    // AADD(aParametros, REPLICATE("Z",nTMLocal))     //  | mv_par08  || Local ate
    // AADD(aParametros, 1)                           //  | mv_par09  || Considera Necess Bruta 1 sim Pto Pedido
    // AADD(aParametros, 2)                           //  | mv_par10  || Saldo Neg Considera    1 sim Lot.Economico
    // AADD(aParametros, STOD("20491231"))            //  | mv_par11  || Data limite p/ empenhos
    // AADD(aParametros, 2)                           //  | mv_par12  || Cons.Qtd. De 3os.? Sim / Nao
    // AADD(aParametros, 2)                           //  | mv_par13  || Cons.Qtd. Em 3os.? Sim / Nao
    // AADD(aParametros, 1)                           //  | mv_par14  || Ao atingir Estoque Maximo ?  1=Qtde. Original; 2=Ajusta Est. Max
    // AADD(aParametros, 2)                           //  | mv_par15  || Quebra SC por Lote Econmico?
    // AADD(aParametros, 2)                           //  | mv_par16  || Qtd.PV nao Liberado?" Subtr/Ignora
    // AADD(aParametros, SPACE(nTMLocal))             //  | mv_par17  || Considera Saldo Armazem de
    // AADD(aParametros, REPLICATE("Z",nTMLocal))     //  | mv_par18  || Considera Saldo Armazem ate
    // AADD(aParametros, 2)                           //  | mv_par19  || Seleciona Filiais? (Sim/Nao)
    // AADD(aParametros, 2)                           //  | mv_par20  || Gera SC por produto(Sim/Nao)
    // AADD(aParametros, 1)                           //  | mv_par21  || Considera Est. Seguranca ?  (Sim / Nao)
    // AADD(aParametros, 1)                           //  | mv_par22  || Prioriza geração de         (1-Sol.Compra/2-Ped.Compra)
    //
    // lMsErroAuto     := .F.
    //
    // MSExecAuto({|x, y| mata170(x, y)},lOpcAuto, aParametros)
    //
    // If lMsErroAuto
    //     cErro  := ""
    //     //  aLogAuto    := GetAutoGrLog()
    //
    //     //  For nY := 1 To Len(aLogAuto)
    //     //      cErro += aLogAuto[nY] + CRLF
    //     //  Next nY
    //     conout(cErro)
    //
    // Endif
    // //restarea(aArea)

Return

Static Function A271Proces(lBlind)

    LOCAL nX 		  := 0
    LOCAL nForFilial  := 0
    LOCAL cArqTrab    := ""
    LOCAL cQuery	  := ""
    LOCAL cCod		  := ""
    LOCAL cAliasQry	  := GetNextAlias()
    LOCAL aFilsCalc   := {}
    LOCAL lMt271Fil   := ExistBlock("MT271FIL")
    LOCAL cFilBack	  := cFilAnt
    LOCAL lRetPe      := .T.
    LOCAL lViewFilial := .F.
    LOCAL lModoComp   := FWModeAccess("SB1",3)=="C"  // Referente ao X2_MODO
    LOCAL lBloqueia	  := .T.
    LOCAL oTempTable  := NIL
    Local aStru       := {}
    Local aCampos     := {}


    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³ Selecao de Multiplas Filiais                                 ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    If mv_par15==1
        If lModoComp
            aFilsCalc   := MatFilCalc(mv_par15==1)
            lViewFilial := .T.
        Else
            Help(nil,1,'MATR935MODO',nil,"Para utilização de Seleção de Filiais a Tabela de Produtos (SB1) deve estar no modo compartilhado por filial. Para este processo será considera somente a filial corrente [' ; ']!"+cFilAnt+"' ]",3,0)
            aFilsCalc := MatFilCalc(.F.)
        Endif
    Else
        aFilsCalc := MatFilCalc(mv_par15==1)
    EndIf

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³ Cria Arquivo de Trabalho                                     ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    If lViewFilial
        Aadd( aStru,{ "TB_OK"   	, "C",01,0} )
        Aadd( aStru,{ "TB_FILIAL"	, "C",TamSX3("B1_FILIAL")[1],0} )
        Aadd( aStru,{ "TB_PRODUTO"	, "C",TamSX3("B1_COD")[1],0} )
        Aadd( aStru,{ "TB_DESCR"   	, "C",30,0} )
        Aadd( aStru,{ "TB_TIPO"		, "C",02,0} )
        Aadd( aStru,{ "TB_ALMOX"	, "C",TamSX3("B2_LOCAL")[1],0} )
        Aadd( aStru,{ "TB_DIAS" 	, "N",03,0} )
    Else
        Aadd( aStru,{ "TB_OK"   	, "C",01,0} )
        Aadd( aStru,{ "TB_PRODUTO"	, "C",TamSX3("B1_COD")[1],0} )
        Aadd( aStru,{ "TB_DESCR"   	, "C",30,0} )
        Aadd( aStru,{ "TB_TIPO"		, "C",02,0} )
        Aadd( aStru,{ "TB_ALMOX"	, "C",TamSX3("B2_LOCAL")[1],0} )
        Aadd( aStru,{ "TB_DIAS" 	, "N",03,0} )
    EndIf

    oTempTable := FWTemporaryTable():New( "TRB" )
    oTempTable:SetFields( aStru )
    oTempTable:AddIndex("indice1", {"TB_PRODUTO"} )
    oTempTable:Create()

    cArqTrab := oTempTable:GetRealName()

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³ Redefinicao do aCampos para utilizar no MarkBrow             ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    If lViewFilial
        aCampos := {{"TB_OK"	 ,"",""},;
            {"TB_FILIAL","" ,OemToAnsi("Filial")},;
            {"TB_PRODUTO","",OemToAnsi("Produto")},;
            {"TB_DESCR"	 ,"",OemToAnsi("Descricao")},;
            {"TB_TIPO"	 ,"",OemToAnsi("Tipo")},;
            {"TB_ALMOX"	 ,"",OemToAnsi("Local")},;
            {"TB_DIAS" 	 ,"",OemToAnsi("Quantidade de Dias Bloqueados")} }
    Else
        aCampos := {{"TB_OK"	 ,"",""},;
            {"TB_PRODUTO","",OemToAnsi("Produto")},;
            {"TB_DESCR"	 ,"",OemToAnsi("Descricao")},;
            {"TB_TIPO"	 ,"",OemToAnsi("Tipo")},;
            {"TB_ALMOX"	 ,"",OemToAnsi("Local")},;
            {"TB_DIAS" 	 ,"",OemToAnsi("Quantidade de Dias Bloqueados")} }
    EndIf

    For nForFilial := 1 To Len( aFilsCalc )

        If aFilsCalc[nForFilial,1]

            //-- Muda Filial para processamento
            cFilAnt := aFilsCalc[nForFilial,2]

            lBloqueia := mv_par01 == 1

            //De acordo com a função é possível utilizar "*" ou "?" para os caracteres desconhecidos
            cCod	:= mv_par10
            cCod	:= StrTran(cCod,"*","")
            cCod	:= StrTran(cCod,"?","")

            cQuery := " SELECT "
            cQuery += " 	B1_COD, B1_DESC,B1_TIPO,B1_LOCPAD,B5_BLQINVA,B2_DINVENT,B5_BLQINVD,B2_DINVFIM,B2_DTINV,B2_LOCAL "
            cQuery += " FROM " + RetSqlName("SB1") + " SB1 "
            cQuery += " JOIN " + RetSqlName("SB2") + " SB2 "
            cQuery += " ON	 "
            cQuery += " 	B1_COD = B2_COD "
            cQuery += " 	AND SB2.D_E_L_E_T_ = ' ' "
            cQuery += " LEFT JOIN " + RetSqlName("SB5") + " SB5 "
            cQuery += " ON "
            cQuery += " 	B1_COD = B5_COD AND "
            cQuery += " 	SB5.D_E_L_E_T_ = ' ' "
            cQuery += " AND B5_FILIAL = '" + xFilial("SB5") + "' "
            cQuery += " WHERE "
            If !(Empty(cCod))
                cQuery += " 	B1_COD LIKE '" + cCod + "%' AND "
            EndIf
            If lBlind
                cQuery += " B5_BLQINVA = '1' AND "
                cQuery += " B2_DINVENT <= '" + DtoS(dDataBase) + "' AND "
            EndIf
            //if mv_par13 == 2
            //    if lBloqueia
            //        cQuery += " B2_DINVFIM = ' ' AND "
            //    else
            //        cQuery += " B2_DINVFIM <> ' ' AND "
            //    endif
            //ElseIf mv_par13 == 1
            //    if lBloqueia
            //        cQuery += " B2_DTINV = ' ' AND "
            //    else
            //        cQuery += " B2_DTINV <> ' ' AND "
            //    endif
            //endif
            cQuery += " 	B2_LOCAL	BETWEEN '" + mv_par02 + "' AND '" + mv_par03 + "' AND "
            cQuery += " 	B1_COD		BETWEEN '" + mv_par04 + "' AND '" + mv_par05 + "' AND "
            cQuery += " 	B1_TIPO	BETWEEN '" + mv_par06 + "' AND '" + mv_par07 + "' AND "
            cQuery += " 	B1_GRUPO	BETWEEN '" + mv_par08 + "' AND '" + mv_par09 + "' AND "
            cQuery += " 	( "
            cQuery += " 		B2_DINVENT = ' ' OR "
            cQuery += " 		B2_DINVENT BETWEEN '" + DtoS(mv_par11) + "' AND '" + DtoS(mv_par12) + "' "
            cQuery += " 	) AND  "
            cQuery += " 	NOT(B2_STATUS = '2') AND "
            cQuery += " B1_FILIAL = '" + xFilial("SB1") + "' AND "
            cQuery += " 	B2_FILIAL = '" + xFilial("SB2") + "' AND "
            cQuery += " 	SB1.D_E_L_E_T_ = ' ' "

            cQuery := ChangeQuery(cQuery)


            dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasQry,.F.,.T.)
            if (cAliasQry)->((Eof()))
                conout(cQuery)
            endif
            If lMt271Fil
                SB1->(DbSetOrder(1))
                SB2->(DbSetOrder(1))
                SB5->(DbSetOrder(1))
            EndIf

            While (cAliasQry)->(!(Eof()))

                If lBlind .And. (StoD((cAliasQry)->B2_DINVENT) + (cAliasQry)->B5_BLQINVD)  > dDataBase
                    Loop
                EndIf

                If lMt271Fil

                    SB1->(DbSeek(xFilial("SB1") + (cAliasQry)->B1_COD ))
                    SB2->(DbSeek(xFilial("SB2") + (cAliasQry)->B1_COD + (cAliasQry)->B2_LOCAL))
                    SB5->(DbSeek(xFilial("SB5") + (cAliasQry)->B1_COD ))

                    lRetPe := ExecBlock("MT271FIL",.F.,.F.,{mv_par01})
                    If ValType(lRetPe)=="L" .And. lRetPe==.F.
                        (cAliasQry)->(dbSkip())
                        Loop
                    EndIf
                EndIf

                dbSelectArea("TRB")
                RecLock("TRB",.T.)
                If lViewFilial
                    Replace 	TB_FILIAL  With cFilAnt,;
                        TB_PRODUTO With (cAliasQry)->B1_COD,;
                        TB_TIPO    With (cAliasQry)->B1_TIPO,;
                        TB_ALMOX   With (cAliasQry)->B2_LOCAL,;
                        TB_DESCR   With (cAliasQry)->B1_DESC
                Else
                    Replace 	TB_PRODUTO With (cAliasQry)->B1_COD,;
                        TB_TIPO    With (cAliasQry)->B1_TIPO,;
                        TB_ALMOX   With (cAliasQry)->B2_LOCAL,;
                        TB_DESCR   With (cAliasQry)->B1_DESC
                EndIf
                If mv_par01 == 2
                    If (cAliasQry)->B5_BLQINVD > 0
                        nX := (cAliasQry)->B5_BLQINVD
                    ElseIf !Empty((cAliasQry)->B2_DINVFIM) .And. !Empty((cAliasQry)->B2_DTINV) .And. (cAliasQry)->B2_DINVFIM <> (cAliasQry)->B2_DTINV
                        nX := (StoD((cAliasQry)->B2_DINVFIM)-StoD((cAliasQry)->B2_DTINV)) + 1
                    Else
                        nX := 1
                    EndIf
                    Replace TB_DIAS With nX
                EndIf
                If !lBlind
                    Replace TB_OK With "x"
                EndIf
                MsUnLock()

                (cAliasQry)->(dbSkip())

            EndDo

            (cAliasQry)->(DbCloseArea())

        EndIf
    Next nForFilial

    dbSelectArea("TRB")
    dbGoTop()
    If Bof() .and. EOF()
        If !lBlind
            HELP(" ",1,"RECNO")
        EndIf
    Else
        A271Grava(lBlind,lViewFilial)
    EndIf

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³ Restaura para filial de origem.                              ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    If lViewFilial
        cFilAnt := cFilBack
    EndIf

    oTempTable:Delete()

Return Nil

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ A271Grava³ Autor ³ Marcelo Pimentel      ³ Data ³ 19.01.98 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Bloqueia / Desbloqueia itens para Inventario               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ MATA271                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function A271Grava(lBlind,lViewFilial)
    Local nDias		:= 0
    Local cBkpFilial:= cFilAnt
    Local lMt271Grv := ExistBlock("MT271GRV")

    Default lBlind := .F.

    dbSelectArea("TRB")
    dbGoTop()
    While !Eof()
        If Empty(TB_OK)
            dbSkip()
            Loop
        EndIf
        // Posiciona na Filial Selecionada
        If lViewFilial
            cFilAnt := TRB->TB_FILIAL
        EndIf
        nDias := TB_DIAS
        dbSelectArea("SB2")
        dbSetOrder(1)
        If dbSeek(xFilial("SB2")+TRB->TB_PRODUTO+TRB->TB_ALMOX)
            RecLock("SB2",.F.)
            If mv_par01 == 1
                If mv_par13 == 1 .and. !Empty(mv_par14)
                    Replace B2_DTINV With mv_par14
                    Replace B2_DINVFIM With mv_par14 + nDias -1
                Else
                    If lBlind
                        SB5->(dbSetOrder(1))
                        If SB5->(dbSeek(xFilial("SB5")+TRB->TB_PRODUTO)) .And. SB5->B5_BLQINVA == "1"
                            Replace B2_DTINV With If(!Empty(B2_DINVENT),B2_DINVENT+SB5->B5_BLQINVD,dDataBase)  ,;
                                B2_DINVFIM With B2_DTINV
                        EndIf
                    Else
                        SB1->(dbSetOrder(1))
                        If SB1->(dbSeek( xFilial("SB1")+TRB->TB_PRODUTO))
                            Replace B2_DTINV With If(!Empty(B2_DINVENT),B2_DINVENT,dDataBase) + SB1->B1_PERINV ,;
                                B2_DINVFIM With B2_DTINV + nDias
                        EndIf
                    EndIf
                Endif
            Else
                Replace B2_DTINV With Ctod("  /  /  "),;
                    B2_DINVFIM With Ctod("  /  /  ")
            EndIf
            MsUnlock()
        EndIf
        If lMt271Grv
            ExecBlock("MT271GRV",.F.,.F.)
        EndIf
        dbSelectArea("TRB")
        dbSkip()
    EndDo
    // Restaura a filial
    If lViewFilial
        cFilAnt := cBkpFilial
    EndIf
Return Nil
