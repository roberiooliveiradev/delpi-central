#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"
#include "Directry.ch"

#define SW_HIDE             0 // Escondido
#define SW_SHOWNORMAL       1 // Normal
#define SW_NORMAL           1 // Normal
#define SW_SHOWMINIMIZED    2 // Minimizada
#define SW_SHOWMAXIMIZED    3 // Maximizada
#define SW_MAXIMIZE         3 // Maximizada
#define SW_SHOWNOACTIVATE   4 // Na Ativação
#define SW_SHOW             5 // Mostra na posição mais recente da janela
#define SW_MINIMIZE         6 // Minimizada
#define SW_SHOWMINNOACTIVE  7 // Minimizada
#define SW_SHOWNA           8 // Esconde a barra de tarefas
#define SW_RESTORE          9 // Restaura a posição anterior
#define SW_SHOWDEFAULT      10// Posição padrão da aplicação
#define SW_FORCEMINIMIZE    11// Força minimização independente da aplicação executada
#define SW_MAX              11// Maximizada

/*/{Protheus.doc} User Function  DLP10F04
    (long_description)
    @type  Function
    @author Gabriel
    @since 08/12/2020
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
User Function  DLP10F04()
    Local aCoors := FWGetDialogSize( oMainWnd )
    Local oPanelUp, oFWLayer, oPanelLeft, oPanelRight, oBrowseUp, oBrowseLeft, oBrowseRight, oRelacZA4, oRelacZA5,oPnlBxLft,oPnlBxRgt
    Local nFat          :=  0.9
    lOCAL aPars         :=  {}
    Local CPERG := "D10F04A"
    //Local cPicTot       :=  STRTRAN(getsx3cache("ZB2_VLRTRA","X3_PICTURE"),"@E","@)") // PICTURE
    Private oDlgPrinc
    Private lMrkUL      := .F.
    Private lMrkUR      := .F.
    Private  oMBrwUL    := Nil
    Private oMBrwUR     := Nil
    Private oBrwRight   := Nil
    Private oBrwLeft   := Nil
    Private oPnlHead    := Nil
    Private aTotHD      := {0 ,0 ,0 ,0,0}
    Private cAliUL      := Nil
    Private cAliUR      := Nil
    Private cAliDW      := Nil
    Private aParsMV     := Nil
    Private aFilF460
    Private cEol        := chr(10)
    Private lAltFil     := nil

    Set Key VK_F12 To MTA650PERG(.T.)

    MTA650PERG(.F.)


    if !Pergunte(cPerg,.t.)
        msginfo("Cancelado pelo Usuario")
        Return
    else
        /*
                MV_PAR01,MV_PAR02, Data Emissao de Ate C2_EMISSAO
                MV_PAR03,MV_PAR04, , Data Emissao de Ate C2_DATPRF
                MV_PAR05,MV_PAR06, OP de Ate C2_NUM
                MV_PAR07,MV_PAR08 pRODUTO DE ATE  C2_PRODUTO
        */
        aParsMV := {MV_PAR01,MV_PAR02,MV_PAR03,MV_PAR04,MV_PAR05,MV_PAR06,MV_PAR07,MV_PAR08}

    endif




    Define MsDialog oDlgPrinc Title 'Delpi - Prioridade OP' From aCoors[1]*nFat, aCoors[2] * nFat To aCoors[3] * nFat, aCoors[4]*nFat Pixel
    // Cria o conteiner onde serão colocados os browses
    oFWLayer := FWLayer():New()
    oFWLayer:Init( oDlgPrinc, .F., .T. )


    // Cria uma "linha" com 50% da tela
    oFWLayer:AddLine( 'HEADER', 15, .F. )
    oFWLayer:AddLine( 'BOX', 85, .F. )
    oFWLayer:AddCollumn( 'BOX_HEADER', 100, .T., 'HEADER' )
    oFWLayer:AddCollumn( 'BOX_LEFT', 50, .T., 'BOX' )
    oFWLayer:AddCollumn( 'BOX_RIGHT', 50, .T., 'BOX' )
    oPnlHead    := oFWLayer:GetColPanel( 'BOX_HEADER', 'HEADER' )
    oPnlBxLft   := oFWLayer:GetColPanel( 'BOX_LEFT' , 'BOX' )
    oPnlBxRgt   := oFWLayer:GetColPanel( 'BOX_RIGHT', 'BOX' )


    aPars       := {}
    aIdxPesqLf  := {}
    aColsBrwLf  := {}
    aStrBrwLf   := {}
    aCpoBLf     := {}
    cAliTLF     := Nil
    cAliLF      := "SLF"

    FWMsgRun(, {||     fSetTmp(1,@aCpoBLf,@aStrBrwLf,@aColsBrwlf,@cAliTLF,@cAliLF,@aIdxPesqLF,aPars) },;
        "Delpi", "Processando a Ordens de Producao...")
    //browse esquerdo
    oBrwLeft:= FWBrowse():New()
    oBrwLeft:leditcell := .t.
    aColsBrwLF[1]:ledit := .t.
    oBrwLeft:SetOwner( oPnlBxLft )
    // Aqui se associa o browse ao componente de tela
    oBrwLeft:SetDescription( "OP - Produto Acabado" )
    oBrwLeft:SetDataTable( .t. )
    //oBrwLeft:SetLineOk(  { || f04Filter(@oBrwRight) }  )
    oBrwLeft:SetAlias(cAliLF )
    oBrwLeft:DisableReport()
    oBrwLeft:SetSeek(, aIdxPesqLF)
    oBrwLeft:SetColumns(aColsBrwlf)
    // Define de onde virao os botoes deste browse
    oBrwLeft:SetProfileID( '1' )
    //    oBrwWin02:SetChange ( {|| fFiltraDestino( (cAliasOri)->CV3_SEQUEN, (cAliasOri)->CT2_RECNO ), oBrwWin03:Refresh( .T. ) } )
    //oBrwLeft:OptionConfig( .T.)
    oBrwLeft:Activate()
    oBrwLeft:Refresh(.T.)
    oBrwLeft:GoTop(.T.)

    aPars := {}
    aIdxPesqRG :={}
    aColsBrwRG :={}
    aStrBrwRG :={}
    aCpoBrwRG :={}
    cAliTRG := Nil
    cAliRG := "SRG"
    FWMsgRun(, {||     fSetTmp(2,@aCpoBrwRG,@aStrBrwRG,@aColsBrwRG,@cAliTRG,@cAliRG,@aIdxPesqRG,aPars)},;
        "Delpi", "Processando a Ordens de Producao Intermediaria...")
    //browse esquerdo

    oBrwRight:= FWBrowse():New()
    oBrwRight:leditcell := .t.
    aColsBrwRG[1]:ledit := .t.
    oBrwRight:SetOwner( oPnlBxRgt )
    // Aqui se associa o browse ao componente de tela
    oBrwRight:SetDescription( "OP - Produto Intermediario" )
    oBrwRight:SetDataTable( .t. )

    oBrwRight:DisableReport()
    oBrwRight:SetSeek(, aIdxPesqRG)
    oBrwRight:SetAlias(cAliRG )
    oBrwRight:SetColumns(aColsBrwRG)
    // Define de onde virao os botoes deste browse
    oBrwRight:SetProfileID( '2' )
    oRelacRg:= FWBrwRelation():New()
    ////oRelacZA4:AddRelation( oBrwRight , oBrwLeft , { { 'ZA4_FILIAL', 'xFilial( "ZA4" )' }, { 'ZA4_ALBUM' , 'ZA3_ALBUM' } } )
    oRelacRg:AddRelation(  oBrwLeft ,oBrwRight , { { 'C2_NUM', 'C2_NUM' } } )
    //
    //oBrwRight:AddBrwRelation( oRelacRg )
    // oBrwRight:OptionConfig( .T.)
    oBrwRight:Activate()
    oBrwRight:Refresh(.T.)
    oBrwRight:GoTop(.T.)
    oRelacRg:Activate()
    //Fontes
    oTFontH1        := TFont():New('Arial',,-16,.T.)
    oTFont2         := TFont():New('Arial',,-13,.T.)
    oTFont3         := TFont():New('Arial',,-16,.T.)
    oTFontH1:bold   := .t.


    //Head
    // Botoes

    aGet := {space(3),space(3)}

    aHeadSay := {}
    aHeadGet := {}
    aParBut  := {}

    aadd(aHeadSay,{10,20})  //  LINHA / COLUNA
    aadd(aHeadSay,{10,510})  //  LINHA / COLUNA

    aadd(aHeadGet,{10,50})  //  LINHA / COLUNA
    aadd(aHeadGet,{10,625})  //  LINHA / COLUNA

    conout("break")


    aadd(aParBut,{05,10})        //  LINHA / COLUNA
    aadd(aParBut,{16,10})        //  LINHA / COLUNA
    aadd(aParBut,{26,10})        //  LINHA / COLUNA

    @ aParBut[1][1], aParBut[1][2] Button 'Processar'       Size 48, 19 Message 'Processando' Pixel Action  FWMsgRun(, {||    D10FPrc( 1,cAliRG,cAliLF) ,oDlgPrinc:End()   },;
        "Delpi - Aguarde", "Processando Registros...") of oPnlHead

    Activate MsDialog oDlgPrinc Center


Return



Static Function fSetTmp(xOpc,aCamposBrw,aStructBrw,aColsBrw,cAlias,cAliBRW,aIdxPesq,aPars)
    Local aCpoTmp   := {}
    Local aIndexTMP := {}
    //   Local aIdxPesq  := {}
    If (Select(cAliBRW) <> 0)

        dbSelectArea(cAliBRW)
        dbCloseArea()

    Endif
    // trato na opcao quais campos retornar
    if xOpc == 1


        aIndexTMP:={"C2_PRIOR","C2_PRODUTO","C2_NUM"}
        cNomIdx := "Prioridade + Produto + OP "
        nTamIdx := 0
        cDescIdx :=""

        For nID := 1 to Len(aIndexTMP)
            if aIndexTMP[nID] == "PRIOR"
                cCpoTMP := "C2_PRIOR"
            ELSE
                cCpoTMP := aIndexTMP[nID]
            ENDIF
            cDescIdx +=aIndexTMP[nID]+iif(nID== Len(aIndexTMP),"","+")
            //     cNomIdx += GetSX3Cache(cCpoTMP, "X3_TITULO")
            nTamIdx += GetSX3Cache(cCpoTMP, "X3_TAMANHO")
        Next nID
        Aadd(aIdxPesq, {cNomIdx, {{"", "C", nTamIdx, 0, cDescIdx, ""}}, 1, .T. })


        aIndexTMP1:={"C2_NUM","C2_PRODUTO","C2_LOCAL"}
        cNomIdx := "Op + Produto + Local "
        nTamIdx := 0
        cDescIdx :=""
        For nID := 1 to Len(aIndexTMP1)
            cDescIdx +=aIndexTMP1[nID]+iif(nID== Len(aIndexTMP1),"","+")
            //     cNomIdx += GetSX3Cache(aIndexTMP1[nID], "X3_TITULO")
            nTamIdx += GetSX3Cache(aIndexTMP1[nID], "X3_TAMANHO")
        Next nID


        Aadd(aIdxPesq, {cNomIdx, {{"", "C", nTamIdx, 0, cDescIdx, ""}}, 2, .T. })

        aIndexTMP2:={"C2_PRODUTO","C2_LOCAL"}
        cNomIdx := "Produto + Local"
        nTamIdx := 0
        cDescIdx :=""
        For nID := 1 to Len(aIndexTMP2)
            cDescIdx +=aIndexTMP2[nID]+iif(nID== Len(aIndexTMP2),"","+")
            //  cNomIdx += GetSX3Cache(aIndexTMP2[nID], "X3_TITULO")
            nTamIdx += GetSX3Cache(aIndexTMP2[nID], "X3_TAMANHO")
        Next nID


        Aadd(aIdxPesq, {cNomIdx, {{"", "C", nTamIdx, 0, cDescIdx, ""}}, 3, .T. })

        aadd(aCpoTmp,"C2_PRIOR"  )
        aadd(aCpoTmp,"C2_NUM"  )
        aadd(aCpoTmp,"C2_ITEM"  )
        aadd(aCpoTmp,"C2_SEQUEN"  )
        aadd(aCpoTmp,"C2_PRODUTO"  )
        aadd(aCpoTmp,"C2_LOCAL"  )
        aadd(aCpoTmp,"C2_QUANT"  )
        aadd(aCpoTmp,"C2_QUJE"  )
        aadd(aCpoTmp,"C2_UM"  )
        aadd(aCpoTmp,"C2_EMISSAO"  )
        aadd(aCpoTmp,"C2_DATPRI"  )
        aadd(aCpoTmp,"C2_DATPRF"  )

    ELSEIF xOpc == 2

        aIndexTMP:={"C2_PRODUTO","C2_NUM"}
        cNomIdx := "Produto + OP "
        nTamIdx := 0
        cDescIdx :=""

        For nID := 1 to Len(aIndexTMP)

            cCpoTMP := aIndexTMP[nID]

            cDescIdx +=aIndexTMP[nID]+iif(nID== Len(aIndexTMP),"","+")
            //    cNomIdx += GetSX3Cache(cCpoTMP, "X3_TITULO")
            nTamIdx += GetSX3Cache(cCpoTMP, "X3_TAMANHO")
        Next nID
        Aadd(aIdxPesq, {cNomIdx, {{"", "C", nTamIdx, 0, cDescIdx, ""}}, 1, .T. })


        aIndexTMP1 := {"C2_NUM","C2_PRODUTO","C2_LOCAL"}
        cNomIdx    := "Op + Produto + Local "
        nTamIdx    := 0
        cDescIdx   := ""
        For nID := 1 to Len(aIndexTMP1)
            cDescIdx +=aIndexTMP1[nID]+iif(nID== Len(aIndexTMP1),"","+")
            //      cNomIdx += GetSX3Cache(aIndexTMP1[nID], "X3_TITULO")
            nTamIdx += GetSX3Cache(aIndexTMP1[nID], "X3_TAMANHO")
        Next nID


        Aadd(aIdxPesq, {cNomIdx, {{"", "C", nTamIdx, 0, cDescIdx, ""}}, 2, .T. })

        aIndexTMP2  := {"C2_PRODUTO","C2_LOCAL"}
        cNomIdx     := "Produto + Local"
        nTamIdx     := 0
        cDescIdx    := ""
        For nID := 1 to Len(aIndexTMP2)
            cDescIdx +=aIndexTMP2[nID]+iif(nID== Len(aIndexTMP2),"","+")
            //    cNomIdx += GetSX3Cache(aIndexTMP2[nID], "X3_TITULO")
            nTamIdx += GetSX3Cache(aIndexTMP2[nID], "X3_TAMANHO")
        Next nID


        Aadd(aIdxPesq, {cNomIdx, {{"", "C", nTamIdx, 0, cDescIdx, ""}}, 3, .T. })

        aadd(aCpoTmp,"PRIOR"  )
        aadd(aCpoTmp,"C2_NUM"  )
        aadd(aCpoTmp,"C2_ITEM"  )
        aadd(aCpoTmp,"C2_SEQUEN"  )
        aadd(aCpoTmp,"C2_PRODUTO"  )
        aadd(aCpoTmp,"C2_LOCAL"  )
        aadd(aCpoTmp,"C2_QUANT"  )
        aadd(aCpoTmp,"C2_QUJE"  )
        aadd(aCpoTmp,"C2_UM"  )
        aadd(aCpoTmp,"C2_EMISSAO"  )
        aadd(aCpoTmp,"C2_DATPRI"  )
        aadd(aCpoTmp,"C2_DATPRF"  )

    endif

    For n1 := 1 to Len(aCpoTmp)

        if alltrim(aCpoTmp[n1]) $ "PRIOR"
            cCpoTMP := "C2_PRIOR"
        ELSE
            cCpoTMP :=  aCpoTmp[n1]
        endif

        cTipoTMP := getsx3cache(cCpoTMP,"X3_TIPO")   // tipo do campo caracter numerico data
        cTamTMP  := getsx3cache(cCpoTMP,"X3_TAMANHO") /// tamanho
        cDecTMP  := getsx3cache(cCpoTMP,"X3_DECIMAL") // decimal
        cTitTMP  := getsx3cache(cCpoTMP,"X3_TITULO") // Titulo

        IF cTipoTMP = 'N'
            cPicTMP := STRTRAN(getsx3cache(cCpoTMP,"X3_PICTURE"),"@E","@)") // PICTURE
        ELSE
            cPicTMP := getsx3cache(cCpoTMP,"X3_PICTURE") // PICTURE
        ENDIF


        aadd(aCamposBrw,aCpoTmp[n1])
        aadd(aStructBrw, {aCpoTmp[n1], cTipoTMP,    cTamTMP, cDecTMP})

        oBrwCol := FWBrwColumn():New()
        oBrwCol:SetType(cTipoTMP)
        oBrwCol:SetData(&("{|| ('"+cAliBRW+"')->"+aCpoTmp[n1]+" }"))
        oBrwCol:SetTitle(ALLTRIM(cTitTMP))
        oBrwCol:SetSize(cTamTMP)
        oBrwCol:SetDecimal(cDecTMP)
        oBrwCol:SetPicture(cPicTMP)
        oBrwCol:SetReadVar(aCpoTmp[n1])
        if  "C2_PRIOR" $ alltrim(aCpoTmp[n1])
            oBrwCol:bvalid := {|| fVldCpo(1)   }
        elseif   "PRIOR" $ alltrim(aCpoTmp[n1])
            oBrwCol:bvalid := {|| fVldCpo(2)   }
        endif

        AAdd(aColsBrw, oBrwCol)

    Next n1

    If Len(GetSrcArray("FWTEMPORARYTABLE.PRW")) > 0 .And. !(InTransaction())
        cAliComp := GetNextAlias()
        oTempTable := FWTemporaryTable():New(cAliBRW)
        oTempTable:SetFields(aStructBrw)
        oTempTable:AddIndex("01",aIndexTMP)
        oTempTable:AddIndex("02",aIndexTMP1)
        oTempTable:AddIndex("03",aIndexTMP2)
        oTempTable:Create()
        cAliComp := oTempTable:GetAlias()
    EndIf


    DbSelectArea(cAliBRW)
    aItem:=fGetItens(xOpc,aCpoTmp,aPars)
    For nX := 1 To Len(aItem)
        (cAliBRW)->(RecLock((cAliBRW), .T.))

        For ni := 1 to Len(aCpoTmp)
            cCMDExec:= "('"+cAliBRW+"')->"+aCpoTmp[ni]
            //(cAliBRW)->&(aCpoTmp[ni]) := aItem[nX][nI]
            conout("gda")
            if alltrim(aCpoTmp[ni]) $ "PRIOR"
                cTipoTMP := getsx3cache("C2_PRIOR","X3_TIPO")   // tipo do campo caracter numerico data

            ELSE
                cTipoTMP := getsx3cache(aCpoTmp[ni],"X3_TIPO")   // tipo do campo caracter numerico data
            endif

            if cTipoTMP $"D"
                &(cCMDExec) :=STOD( aItem[nX][nI])
            ELSE
                &(cCMDExec) := aItem[nX][nI]
            ENDIF
        Next ni
        (cAliBRW)->(MsUnlock())

    Next nX


REturn




Static Function fGetItens(nOpcx,aCpoTmp,aPars)
    Local cSql :=""
    //  Local cEol :=chr(10)
    Local aItens :={}
    // MV_PAR01 ID Repasse De
    // MV_PAR02 ID Repasse Ate
    // MV_PAR03 Cod Marketplace
    // MV_PAR04 Dt Pedido Marketplace De?
    // MV_PAR05 Dt Pedido Marketplace Ate?

    //E1_IDZB2
    // 1 ZB1_FILIAL+ZB1_ZMARKE+ZB1_CODCLI+ZB1_LOJCLI

    // conforme f12 das ordens de producao


    if nOpcx == 1

        // FAZER A TRATATIVA PARA TRAZER CONFORME PARAMETROS
        cSql :=" SELECT C2_PRIOR  ,C2_NUM  ,C2_ITEM,C2_SEQUEN, 				" + cEol
        cSql+=" 	C2_PRODUTO,C2_LOCAL,C2_QUANT,C2_QUJE,C2_UM, 		" + cEol
        cSql+=" 	C2_EMISSAO,C2_DATPRI,C2_DATPRF,R_E_C_N_O_ [RECSC2]	" + cEol
        cSql+=" FROM  dbo."+RetSQLName("SC2")+"  SC2 (NOLOCK) 	" + cEol
        cSql+=" WHERE SC2.D_E_L_E_T_ = '' 	" + cEol
        cSql+=" AND SC2.C2_FILIAL = "+VALTOSQL(XFILIAL("SC2")) + cEol
        //cSql+="       AND C2_NUM in ('191560','191559','191558','191557','191550','191549','191548', '191547','191546') " + cEol
        /*
                MV_PAR01,MV_PAR02, Data Emissao de Ate C2_EMISSAO
                MV_PAR03,MV_PAR04, , Data Emissao de Ate C2_DATPRF
                MV_PAR05,MV_PAR06, OP de Ate C2_NUM
                MV_PAR07,MV_PAR08 pRODUTO DE ATE  C2_PRODUTO
        */
        cSql+=" AND SC2.C2_QUJE <  SC2.C2_QUANT" + cEol
        cSql+="   AND  C2_EMISSAO BETWEEN  " + valtosql(MV_PAR01)  +" AND " + VALTOSQL(MV_PAR02)  + cEol
        cSql+="   AND  C2_DATPRF BETWEEN  " + valtosql(MV_PAR03)  +" AND " + VALTOSQL(MV_PAR04)  + cEol
        cSql+="   AND  C2_NUM BETWEEN  " + valtosql(MV_PAR05)  +" AND " + VALTOSQL(MV_PAR06)  + cEol
        cSql+="   AND  C2_PRODUTO BETWEEN  " + valtosql(MV_PAR07)  +" AND " + VALTOSQL(MV_PAR08)  + cEol
        cSql+=" 	  AND C2_SEQPAI= '' ORDER BY 2,3,4""


    elseif nOpcx == 2

        cSql :=" SELECT C2_PRIOR PRIOR,C2_NUM,C2_ITEM,C2_SEQUEN, 				" + cEol
        cSql+=" 	C2_PRODUTO,C2_LOCAL,C2_QUANT,C2_QUJE,C2_UM, 		" + cEol
        cSql+=" 	C2_EMISSAO,C2_DATPRI,C2_DATPRF,R_E_C_N_O_ [RECSC2]	" + cEol
        cSql+=" FROM  dbo."+RetSQLName("SC2")+"  SC2 (NOLOCK) 	" + cEol
        cSql+=" WHERE SC2.D_E_L_E_T_ = '' 	" + cEol
        //cSql+="       AND C2_NUM in ('191560','191559','191558','191557','191550','191549','191548', '191547','191546') " + cEol
        cSql+="   AND SC2.C2_FILIAL = "+VALTOSQL(XFILIAL("SC2")) + cEol
        cSql+="   AND SC2.C2_SEQPAI != "+VALTOSQL("") + cEol
        cSql+="   AND SC2.C2_QUJE <  SC2.C2_QUANT" + cEol
        cSql+="   AND SC2.C2_EMISSAO BETWEEN  " + valtosql(MV_PAR01)  +" AND " + VALTOSQL(MV_PAR02)  + cEol
        cSql+="   AND SC2.C2_DATPRF BETWEEN  " + valtosql(MV_PAR03)  +" AND " + VALTOSQL(MV_PAR04)  + cEol
        cSql+="   AND SC2.C2_NUM BETWEEN  " + valtosql(MV_PAR05)  +" AND " + VALTOSQL(MV_PAR06)  + cEol
        cSql+="   AND SC2.C2_PRODUTO BETWEEN  " + valtosql(MV_PAR07)  +" AND " + VALTOSQL(MV_PAR08)  + cEol
        cSql+=" 	  ORDER BY 2,3,4"


    endif
    //EEcView(cSql, "query FINA460")

    If (Select("TMP1") <> 0)

        dbSelectArea("TMP1")
        dbCloseArea()

    Endif
    TCQuery cSql NEW ALIAS "TMP1"
    // percorro a query gerando o array conforme os campos de selecao
    While TMP1->(!Eof())
        aITTmp := {}
        For ni := 1 to Len(aCpoTmp)


            aadd(aITTmp,TMP1->&(aCpoTmp[ni]))


        Next ni
        aadd(aItens,aITTmp)
        TMP1->(dbSkip())

    EndDo
Return aItens




/*/{Protheus.doc} D10FPrc

  Relacionado ao Botao "Processar",  faz o Update do Registro  conforme alterado pelo usuario
  Só faz a alteração na SC2 quando necessario evitando travamenos na rotina

    @author  Gabriel
    @since   20-01-2021
/*/

Static FUnction D10FPrc(nOpcx,cAliRG,cAliLF)


    dbSelectArea("SC2")
    SC2->(dbSetOrder(1))
    (cAliRG)->(dbGoTop())
    While (cAliRG)->(!Eof())
        //   C2_FILIAL, C2_NUM, C2_ITEM, C2_SEQUEN, C2_ITEMGRD, R_E_C_N_O_, D_E_L_E_T_
        IF SC2->(dbSeek(xFilial("SC2") + (cAliRG)->C2_NUM+ (cAliRG)->C2_ITEM+ (cAliRG)->C2_SEQUEN    ))
            //   SC2->(DbGoto( (cAliRG)->  ))

            if  (cAliRG)->PRIOR != SC2->C2_PRIOR

                RecLock("SC2", .F.)
                SC2->C2_PRIOR   := (cAliRG)->PRIOR
                SC2->(MsUnlock())


            endif
        endif

        (cAliRG)->(DbSkip())
    EndDo
    dbSelectArea("SC2")
    SC2->(dbSetOrder(1))
    SC2->(dbGoTop())
    (cAliLF)->(dbGoTop())
    While (cAliLF)->(!Eof())
        //   C2_FILIAL, C2_NUM, C2_ITEM, C2_SEQUEN, C2_ITEMGRD, R_E_C_N_O_, D_E_L_E_T_
        IF SC2->(dbSeek(xFilial("SC2") + (cAliLF)->C2_NUM+ (cAliLF)->C2_ITEM+ (cAliLF)->C2_SEQUEN    ))
            //   SC2->(DbGoto( (cAliRG)->  ))

            // if  (cAliLF)->PRIOR != SC2->C2_PRIOR
            if  (cAliLF)->C2_PRIOR != SC2->C2_PRIOR

                RecLock("SC2", .F.)
                SC2->C2_PRIOR   := (cAliLF)->C2_PRIOR
                SC2->(MsUnlock())

            endif
        endif

        (cAliLF)->(DbSkip())
    EndDo

REturn


/*/{Protheus.doc} fVldCpo

  Validacao do campo para que seja alterada a Prioridade e Validar se deve altearar no Browse da Esquerda

    @author  Gabriel
    @since   20-01-2021
/*/
Static FUnction fVldCpo(xOpc)

    Local lRet := .t.

    Local cPriori := &(READVAR())
    Local nTam := getsx3cache("C2_PRIOR","X3_TAMANHO")
    cPriori := val( cPriori)
    cPriori := PADL(cPriori,nTam,"0")

    if cPriori =="000"
        msgstop("Prioridade Invalida","Delpi")
        Return .f.
    endif

    &( 'M->'+READVAR()) := cPriori

    if xOpc == 1 .and. !lAltFil

        // (cAliLF)->PRIOR:= cPriori
        (cAliLF)->C2_PRIOR:= cPriori

    elseif lAltFil .and.  xOpc == 1
        (cAliLF)->C2_PRIOR:= cPriori

        (cAliRG)->(dbGoTop())
        While (cAliRG)->(!Eof())

            IF  (cAliLF)->C2_NUM == (cAliRG)->C2_NUM

                (cAliRG)->(RecLock(cAliRG, .F.))
                (cAliRG)->PRIOR   := cPriori
                (cAliRG)->(MsUnlock())

            endif
            (cAliRG)->(DbSkip())

        EndDo

    elseif   xOpc == 2
        //    (cAliRG)->C2_PRIOR   := cPriori
        (cAliRG)->PRIOR   := cPriori
    endif
    oBrwLeft:Refresh(.T.)
    oBrwRight:Refresh(.T.)

Return lRet




/*/{Protheus.doc} MTA650PERG

    Rotina para validar e o F12 esta ativado coanforme parametro do usuario para alterar as OPs filhas

    @author  Gabriel
    @since   20-01-2021
/*/

Static Function MTA650PERG(lMostra)


    Pergunte("MTA650", lMostra)


    lAltFil     := IIF(MV_PAR05 == 1, .t.,.f.)

RETURN



