#INCLUDE 'TOTVS.CH'
#INCLUDE "TOPCONN.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"

/*/{Protheus.doc}DEL04P01
    (Schedule para gerar mestre de inventario)
    @type  Function
    @author Luan Woichechoscki
    @since 10/11/2024
/*/
User Function DEL04P01()

    Local cAlias
    Local cCodEmp := '01'
    Local cCodFil := '01'
    Local cFilBkp
    Private lRpc  := .F.
    Private aLog  := {}


    Private __lMobPrd  := .t.

    //Abre tabelas necessarias
    // IF !(Type("oMainWnd")=="O")
    //     lRpc := RpcSetEnv(cCodEmp,cCodFil,,,,GetEnvServer(),)
    // ENDIF
    cFilBkp := cFilAnt


    // cAlias := GetNextAlias()
    // BeginSql Alias cAlias
    //     SELECT
    //         TOP 10 *
    //     FROM
    //         %Table:SD1% (NOLOCK) TBL1
    //     WHERE
    //         TBL1.D_E_L_E_T_ = ''
    //         AND TBL1.D1_FILIAL = '02'
    //         AND TBL1.D1_COD IN ('30193952')
    //         AND EXISTS (
    //             SELECT
    //                 NULL
    //             FROM
    //                 %Table:SF4% (NOLOCK) SF4
    //             WHERE
    //                 SF4.D_E_L_E_T_ = ''
    //                 AND SF4.F4_CODIGO = TBL1.D1_TES
    //                 AND SF4.F4_ESTOQUE = 'S'
    //         )
    //     ORDER BY
    //         R_E_C_N_O_ DESC
    // EndSql
    cSql := "EXEC  [dbo].[STP_DELPI_INVENTARIO_RGN01_"+cFilAnt+"] "

    fPutInv(cSql)

    cSql := "EXEC  [dbo].[STP_DELPI_INVENTARIO_RGN02_"+cFilAnt+"] "
    fPutInv(cSql)

    cSql := "EXEC  [dbo].[STP_DELPI_INVENTARIO_RGN03_"+cFilAnt+"] "

    fPutInv(cSql)
    cSql := "EXEC  [dbo].[STP_DELPI_INVENTARIO_RGN04_"+cFilAnt+"] "

    fPutInv(cSql)

    cSql := "EXEC  [dbo].[STP_DELPI_INVENTARIO_RGN05_"+cFilAnt+"] "

    fPutInv(cSql)

    //  cSql := "EXEC  [dbo].[STP_DELPI_INVENTARIO_RGN06] "
    // fPutInv(cSql)
    cSql := "EXEC  [dbo].[STP_DELPI_INVENTARIO_RGN07_"+cFilAnt+"] "

    fPutInv(cSql)
    cFilAnt := cFilBkp
    IF lRpc
        RpcClearEnv()
    ENDIF

Return

/*/{Protheus.doc} fPutInv
@Description
@Type
@Author 	 TSC - Gabriel Araujo
@Since  	 06/11/2025
/*/
Static Function fPutInv(cSql)

    If (Select("TRBMOD") <> 0)

        dbSelectArea("TRBMOD")
        dbCloseArea()

    Endif
    TCQuery cSql NEW ALIAS "TRBMOD"
    while TRBMOD->(!Eof())

        aLog  := {}
        SB1->(dbSetOrder(1))
        SB1->(MsSeek(xFilial('SB1')+TRBMOD->B1_COD))
        //cFilAnt := (cAlias)->D1_FILIAL

        //Gera Mestre por produto
        Pergunte("AIA032",.F.)
        MV_PAR01 := "01"        // Armazem ?
        MV_PAR02 := SB1->B1_COD	        // Do Produto ?
        MV_PAR03 := SB1->B1_COD	        // Ate o Produto ?
        MV_PAR04 := 1	                        // Numero de contagens ?
        MV_PAR05 := date()                      // Data ?
        MV_PAR06 := 1	                        // Cons. Periodicidade ?
        MV_PAR07 := 2	                        // Classe A ?
        MV_PAR08 := 2	                        // Classe B ?
        MV_PAR09 := 2	                        // Classe C ?
        MV_PAR10 := 1	                        // Inventario Guiado ?
        MV_PAR11 := 2	                        // Rec.Inv Mobile ?

        AI031(SB1->B1_COD	 , "DELPI")

        //bloqueio do produto
        Pergunte("MTA271",.F.)
        MV_PAR01 := 1	                        // Quanto ao produto ?
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

        //Gera Mestre por produto
        Pergunte("AIA032",.F.)
        MV_PAR01 := "99"        // Armazem ?
        MV_PAR02 := SB1->B1_COD	        // Do Produto ?
        MV_PAR03 := SB1->B1_COD	        // Ate o Produto ?
        MV_PAR04 := 1	                        // Numero de contagens ?
        MV_PAR05 := date()                      // Data ?
        MV_PAR06 := 1	                        // Cons. Periodicidade ?
        MV_PAR07 := 2	                        // Classe A ?
        MV_PAR08 := 2	                        // Classe B ?
        MV_PAR09 := 2	                        // Classe C ?
        MV_PAR10 := 1	                        // Inventario Guiado ?
        MV_PAR11 := 1	                        // Rec.Inv Mobile ?

        AI031(SB1->B1_COD	 , "DELPI")

        //bloqueio do produto
        Pergunte("MTA271",.F.)
        MV_PAR01 := 1	                        // Quanto ao produto ?
        MV_PAR02 := "99"	        // Do   Armazem ?
        MV_PAR03 := "99"        // Ate  Armazem ?
        MV_PAR04 := SB1->B1_COD	 	        // Do   Produto ?
        MV_PAR05 := SB1->B1_COD	 	        // Ate' Produto ?
        MV_PAR06 := SB1->B1_TIPO	            // Do   Tipo ?
        MV_PAR07 := SB1->B1_TIPO	            // Ate' Tipo ?
        MV_PAR08 := SB1->B1_GRUPO	            // Do   Grupo ?
        MV_PAR09 := SB1->B1_GRUPO	            // Ate' Grupo ?
        MV_PAR10 := "***************"	        // Mascara ?
        MV_PAR11 := CTOD("01/01/2000")            // Da   Data ?
        MV_PAR12 := CTOD("01/01/2049")           // Ate' Data ?
        MV_PAR13 := 2	                        // Dta do Inventário ?
        MV_PAR14 := date()                      // Data Informada ?
        MV_PAR15 := 2	                        // Seleciona filiais ?
        A271Proces(.F.)

        TRBMOD->( DbSkip())

    EndDo




Return

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³AI031     ºAutor  ³Microsiga           º Data ³  17/04/02   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Geracao do CBA                                             º±±
±±º          ³ Por Prduto                                                 º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ SIGAACD                                                    º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function AI031(cProd, cDoc)

    Local nX          := 0
    Local lOk
    Local lACDA30VP   := ExistBlock("ACDA30VP")
    Local lIntegraWMS := SuperGetMv('MV_WMSNEW',.F.,.F.)
    Local lPrdBloq    := .F.
    // Local aArea       := SGetArea()
    Local oProduto    := Nil
    Local aArea := getarea()
    Local aAreaSB1 := SB1->(GetArea())
    // SGetArea(aArea,"CBA")
    If	MV_PAR04 < 1
        IF !lRpc
            MsgAlert("O numero de contagens nao pode ser igual ou inferior a zero, favor verificar !!!" + CRLF + "Documento: "+cDoc+CRLF+"Produto: "+cProd)
        ELSE
            aADD(aLog,{"O numero de contagens nao pode ser igual ou inferior a zero, favor verificar !!!", cProd, cDoc})
        ENDIF
        Return
    EndIf

    dbSelectArea("SB5")
    SB5->(dbSetOrder(1))
    dbSelectArea("SB1")
    SB1->(dbSetOrder(1))
    SB1->(dbSeek(xFilial("SB1")+MV_PAR02,.T.))
    While !SB1->(Eof()) .and. xFilial("SB1") == SB1->B1_FILIAL .and. SB1->B1_COD <= MV_PAR03

        If lPrdBloq .And. SB1->B1_MSBLQL == "1"
            // IncProc()
            SB1->(DbSkip())
            Loop
        Else
            If !ExistCpo("SB1",SB1->B1_COD)
                lPrdBloq := .T.
                // IncProc()
                SB1->(DbSkip())
                Loop
            EndIf
        EndIf

        CBA->(dbSetOrder(3)) //CBA_FILIAL+CBA_TIPINV+CBA_STATUS+CBA_LOCAL+CBA_PROD+CBA_DATA
        If	CBA->(dbSeek(xFilial("CBA")+"1"+"0"+MV_PAR01+SB1->B1_COD+DTOS(MV_PAR05))) .OR.;
                CBA->(dbSeek(xFilial("CBA")+"1"+"1"+MV_PAR01+SB1->B1_COD+DTOS(MV_PAR05)))
            // IncProc()
            SB1->(DbSkip())
            Loop
        EndIf

        //Gerar mestre de inventario para armazens com saldo
        //esta validacao so ocorre por produto
        SB2->(DbSetorder(1))
        If	RetFldProd(SB1->B1_COD,"B1_LOCPAD") # MV_PAR01 .And. ;
                !SB2->(DbSeek(xFilial("SB2")+SB1->B1_COD+MV_PAR01))
            // IncProc()
            SB1->(DbSkip())
            Loop
        EndIf

        //So analisa um produto para bloqueio se encontrar na tabela de complemento,
        //caso contrario eu crio o mestre
        If	MV_PAR06==1 .and. SB5->(DbSeek(xFilial("SB5")+SB1->B1_COD))
            If	!Empty(SB5->B5_PERIOT) .And. (SB5->(B5_DTINV+B5_PERIOT)>dDataBase)
                // IncProc()
                SB1->(DbSkip())
                Loop
            EndIf
        EndIf

        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³ Ponto de Entrada para Validar o SB1                          ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
        If	lACDA30VP
            lOK := ExecBlock("ACDA30VP",.F.,.F.)
            If (ValType(lOk) == "L")
                If !lOK
                    aadd(aLog,{"AI031","98",NIL,SB1->B1_COD,RetFldProd(SB1->B1_COD,"B1_LOCPAD"),""})
                    // IncProc()
                    SB1->(dbSkip())
                    Loop
                Endif
            EndIf
        Endif


        If lIntegraWMS
            If IntWMS(SB1->B1_COD)
                If FindFunction("WMSVldInve")
                    If !WMSVldInve(MV_PAR01,,SB1->B1_COD,,.F.)
                        aadd(aLog,{"AI031","98",NIL,SB1->B1_COD,RetFldProd(SB1->B1_COD,"B1_LOCPAD"),""})
                        // IncProc()
                        SB1->(dbSkip())
                        Loop
                    EndIf
                EndIf

                //Regra WMS para gerar inventário apenas para os produtos componentes
                If WmsPrdPai(SB1->B1_COD)
                    MTWmsPai(SB1->B1_COD,@oProduto)
                    If aScan(oProduto:aProduto,{|x| x[1] == (oProduto:GetProduto())}) = 0
                        For nX := 1 To Len(oProduto:aProduto)
                            CBA->(dbSetOrder(3))//CBA_FILIAL+CBA_TIPINV+CBA_STATUS+CBA_LOCAL+CBA_PROD+DTOS(CBA_DATA)
                            If CBA->(dbSeek(xFilial("CBA")+"1"+"0"+MV_PAR01+oProduto:aProduto[nX][1]+DTOS(MV_PAR05)))
                                Loop
                            Else
                                a030GrvCBA(oProduto:aProduto[nX][1],aLog)
                            EndIf
                        Next nX
                    Else
                        SB1->(dbSkip())
                        Loop
                    EndIf
                Else
                    a030GrvCBA(SB1->B1_COD,aLog)
                EndIf
            Else
                a030GrvCBA(SB1->B1_COD,aLog)
            EndIF
        Else
            a030GrvCBA(SB1->B1_COD,aLog)
        EndIf
        SB1->(dbSkip())
    EndDo
    // SRestArea(aArea)

    // IF !lRpc
    //     MostraLog("AI031","AIA032",aLog)
    // ENDIF
    RESTAREA(aAreaSB1)
    RESTAREA(aArea)
Return


/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡Æo    ³A271Proces ³ Autor ³ Marcelo Pimentel      ³ Data ³ 02/06/93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡Æo ³ Monta o arquivo de trabalho                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA271                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
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



Static Function Scheddef()

    Local aParam  := {}


    Aadd(aParam, "P"            ) // 01 - Tipo R para relatorio P para processo
    Aadd(aParam,   ""    ) // 02 - Pergunte do relatorio, caso nao use passar ParamDef
    Aadd(aParam,   Nil        ) // 03 - Alias
    Aadd(aParam, Nil           ) // 04 - Array de ordens
    Aadd(aParam, Nil ) // 05 - Titulo
    Aadd(aParam,   Nil   ) // 06 - Nome do relatório (parametro 1 do metodo new da classe TReport)
    Aadd(aParam, .F.      ) // 07 Lógico, indica se permite que o agendamento possa ser cadastrado como sempre ativo. Quando não enviado, o default é .F. (não permite que este agendamento seja cadastrado como sempre ativo)
    Aadd(aParam,  .T.    ) // Lógico, indica que o agendamento pode ser realizado por filiais. Quando não enviado, o default é .F. (não permite o agendamento por filiais, somente por grupo de empresas)

Return aParam

Static Function a030GrvCBA(cProduto,aLog)

	cCodInv := GetSXENum("CBA","CBA_CODINV")
	RecLock("CBA",.T.)
	CBA->CBA_Filial := xFilial("CBA")
	CBA->CBA_CODINV := cCodInv
	CBA->CBA_DATA   := MV_PAR05
	CBA->CBA_CONTS  := MV_PAR04
	CBA->CBA_STATUS := "0"
	CBA->CBA_TIPINV := "1"
	CBA->CBA_PROD   := cProduto
	CBA->CBA_LOCAL  := MV_PAR01  
	CBA->CBA_CLASSA := Str(MV_PAR07,1)
	CBA->CBA_CLASSB := Str(MV_PAR08,1)
	CBA->CBA_CLASSC := Str(MV_PAR09,1)
	//If __lMobPrd
	CBA->CBA_INVGUI := Str(MV_PAR10,1)
	CBA->CBA_RECINV := Str(MV_PAR11,1)
	//EndIf
	MsUnlock()	
	If __lSX8
		ConfirmSx8()
	EndIf
	//Mestres de Inventario gerados
	aadd(aLog,{"AI031","01",CBA_CODINV,cProduto,CBA->CBA_LOCAL})
	
	IncProc()
Return nil

User Function Jobtst()

    RpcSetType( 3 )

    PREPARE ENVIRONMENT EMPRESA "01" FILIAL "02" MODULO "EST"
    u_DEL04P01()
    CONOUT("EMPRESA " + CEMPANT)
    CONOUT("FILIAL  " + CFILANT)


    RESET ENVIRONMENT

Return .T.
