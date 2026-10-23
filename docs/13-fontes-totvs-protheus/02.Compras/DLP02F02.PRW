
/*/{Protheus.doc} DLP02F02

    Formacao de Preco Delpi
SetNoInsertLine
/*/

#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"
//#include "Directry.ch"

user function DLP02F02(cOporCrm)
    Local aArea       := GetArea()
    Local cAliasCab   := "SZ8"
    Local cAliasIte   := "SZ9"

    Local oBrowse := FWMBrowse():New()
    Private aFiles    :={}
    Private cEol      := chr(10)
    PRIVATE lLibField := .f.
    PRIVATE lRetCx    := .f.
    Private cBox1     := "1PRD01"
    Private cBox2     := "2OPE01"
    Private  cBox3    := "3IMP01"
    Private nTmIt     := getsx3cache("Z9_ITEM","X3_TAMANHO")
    Private nTotMP    := 0 // Variavel que totaliza a Materia Prima
    Private nTotMOD   := 0 // Variavel que totaliza a Mao de Obra
    Private nTotBen   := 0 // Variavel que totaliza a Beneficiamento
    Private nTotGG    := 0 // Variavel que totaliza Gastos Gerais
    Private nTotINV   := 0 // Variavel que totaliza Investimento/Ferramental
    Private nQtdBas   := 1 // Variavel Quantidade Basica
    Private nTotUnit  := 0
    Private NTOTESTR  := 0
    Private LucroOper := 0
    Private nPVOper   := 0
    Private nVlFre    := 0
    Private nCoefOper := 0
    Private nCoefImp  := 0
    Private lRecal    := .f.
    Private cTabPV    := space(3)
    //Variaveis da aba impostos
    Private nICMS    :=0  // ICMS
    Private nPisCof  :=0  // PIS E COFINS
    Private nComiss  :=0  // COMISSÃO
    Private nISS     :=0  // ISS
    Private nCoef    :=0  // COEFICIENTE
    Private nPVVenda :=0  // PV VENDA
    Private nIRCSLL  :=0  // IR E CSLL
    Private nCusPrd  :=0 // Custo produto
    Private lCanAlt := .F.
    Private lVldCpos := .f.
    Private aPrdQtBas := {}
    Private aCusLiq := {0,0,0} //icms - pis cof - frete
    Private nQtdEst := 0
    Private idCoefOp := "000007"
    /****************************/
    /****************************/
    // Private lBrowse := .T.
    Private aRotina		:= MenuDef()
    // Private aLogProc := {} // ID |CODIGO PRODUTO | erro
    Private lAuto := .f.

    Default cOporCrm := ""


    oBrowse:SetAlias("SZ8")
    oBrowse:SetDescription("DELPI - Formação de Preço de Venda") //Roteiro de Operações

    oBrowse:SetCanSaveArea(.T.)


    chkfile("SZ8")
    chkfile("SZ7")
    chkfile("SZ9")
    chkfile(cAliasCab)
    chkfile(cAliasIte)

    SetKey( VK_F5, { || U_D02fPDados() } )


    if !Empty(cOporCrm)
        oBrowse:SetFilterDefault( "M->Z8_NROPOR == '"+cOporCrm+"' .And. M->Z8_FILIAL == '"+cFilAnt+"'" )
    endif
    // oBrowse:AddLegend( "Z8_MARGEM <= 0 ", "RED"		, "Margem Inconsistente"	)
    // oBrowse:AddLegend( "Z8_MARGEM > 0 ", "GREEN"		, "Margem OK"	)
    //oBrowse:AddLegend( "ZA6_STATUS == '3'", "GREEN"		         , "XML PROCESSADO"	)
    //oBrowse:AddLegend( "Z8_SITUA =='P' ", "RED"		, "Z8_SITUA Inconsistente"	)
    //oBrowse:AddLegend( "Z8_MARGEM !='P' ", "GREEN"		, "Z8_SITUA OK"	)
    //oBrowse:AddStatusColumns({||fLegMargem()},{|oBrowse| fLegDesc()/*Função de DOUBLECLICK*/})
    oBrowse:AddStatusColumns({||fLegMargem()},{|| fLegDesc(1)/*Função de DOUBLECLICK*/})
    oBrowse:AddStatusColumns({||fLegPrc()},{|| fLegDesc(2)/*Função de DOUBLECLICK*/})
    //oBrowse:AddStatusColumns({||If(.T./*Função de avaliação de status*/,'BR_LARANJA','BR_VERMELHO')},{|oBrowse|/*Função de DOUBLECLICK*/})
    //oBrowse:AddStatusColumns({||If(.T./*Função de avaliação de status*/,'BR_AMARELO','BR_VERMELHO')},{|oBrowse|/*Função de DOUBLECLICK*/})
    DBSELECTAREA("SZ9")
    SZ9->(DBGOTOP())
    SZ9->(dbSetOrder(1))
    oBrowse:Activate()

    RestArea(aArea)

Return

static function fLegPrc()

    Local aArea := getarea()

    IF ALLTRIM(SZ8->Z8_SITUA )=='P'
        cREtLeg := "BR_VERMELHO"
    ELSE
        cREtLeg := "BR_VERDE"
    ENDIF

    restarea(aArea )
    SZ9->(DBGOTOP())
    SZ9->(dbSetOrder(1))
Return cREtLeg
static function fLegDesc(nTp)
    lOCAL aLegenda := {}
    if nTp == 1
        Aadd(aLegenda,{"BR_VERDE"	        , "Margem OK" })	                //-- Integração realizada com sucesso.
        Aadd(aLegenda,{"BR_VERMELHO"        , "Margem Inconsistente" })	                //-- Erro de integração.
        cTit := "Margem Lucro"

    else
        Aadd(aLegenda,{"BR_VERDE"	        , "Sem Pendencia" })	                //-- Integração realizada com sucesso.
        Aadd(aLegenda,{"BR_VERMELHO"        , "Analise Pendente Tabela de Preco" })	                //-- Erro de integração.
        cTit := "Preco Venda"
    endif

    BrwLegenda(cTit , cTit , aLegenda )  //-- Rota Inteligente
    SZ9->(DBGOTOP())
    SZ9->(dbSetOrder(1))
RETURN .t.
static function fLegMargem()

    Local aArea := getarea()
    Local aAreaSZ9	:= SZ9->(GetArea())
    lOCAL cChave := SZ8->Z8_FILIAL+SZ8->Z8_ID + '2OPE01LUCRO                                             '
    DBSELECTAREA("SZ9")
    SZ9->(dbSetOrder(2))
    SZ9->(MsSeek( cChave))
    IF     SZ8->Z8_PVSUGER <=SZ8->Z8_PVTAB

        cREtLeg := "BR_VERDE"

    ELSE
        cREtLeg := "BR_VERMELHO"

    ENDIF
    //Z9_IDFLD
    //2OPE01

    restarea(aArea )
    restarea(aAreaSZ9 )
    SZ9->(DBGOTOP())
    SZ9->(dbSetOrder(1))

Return cREtLeg
/*====================================*\
|| # Func:  MenuDef   MVC		    # ||
\*====================================*/
Static Function MenuDef()
    local aRotina := {}
    //aRotina := FWMVCMenu( 'NSK05F06' )
    //ADD OPTION aRotina TITLE "Importar XML"           ACTION 'U_FIMPXML()' OPERATION 3 ACCESS 0
    // ADD OPTION aRotina TITLE 'Visualizar'   ACTION 'VIEWDEF.DLP02F02' OPERATION 2 ACCESS 0
    // ADD OPTION aRotina TITLE 'Incluir'      ACTION 'VIEWDEF.DLP02F02' OPERATION 3 ACCESS 0

    //   ADD OPTION aRotina TITLE 'Alterar'      ACTION 'VIEWDEF.DLP02F02' OPERATION 4 ACCESS 0
    // ADD OPTION aRotina TITLE 'Excluir'      ACTION 'VIEWDEF.DLP02F02' OPERATION 5 ACCESS 0
    ADD OPTION aRotina TITLE 'Visualizar'   ACTION 'U_DLPD2FOP(2)' OPERATION 2 ACCESS 0
    ADD OPTION aRotina TITLE 'Incluir'      ACTION 'U_DLPD2FOP(3)' OPERATION 3 ACCESS 0
    ADD OPTION aRotina TITLE 'Alterar'      ACTION 'U_DLPD2FOP(4)' OPERATION 4 ACCESS 0
    ADD OPTION aRotina TITLE 'Excluir'      ACTION 'U_DLPD2FOP(5)' OPERATION 5 ACCESS 0

    //  ADD OPTION aRotina TITLE 'Visualizar 2'   ACTION 'VIEWDEF.DLP02F02' OPERATION 2 ACCESS 0
    // ADD OPTION aRotina TITLE 'Incluir'      ACTION 'VIEWDEF.DLP02F02' OPERATION 3 ACCESS 0
    //  ADD OPTION aRotina TITLE 'Alterar 2 '      ACTION 'VIEWDEF.DLP02F02' OPERATION 4 ACCESS 0
    // ADD OPTION aRotina TITLE 'Excluir'      ACTION 'VIEWDEF.DLP02F02' OPERATION 5 ACCESS 0
    ADD OPTION aRotina TITLE 'Forma Proc Auto'      ACTION 'U_DLP02F06()' OPERATION 3 ACCESS 0
    ADD OPTION aRotina TITLE 'Proc Preco'      ACTION 'U_DLP02F07()' OPERATION 3 ACCESS 0
    ADD OPTION aRotina TITLE 'Cópia'      ACTION 'U_zCopyMVC()' OPERATION 3 ACCESS 0
    //ADD OPTION aRotina TITLE '2 Proc XML'    	    ACTION 'U_W97F02A()' 	  OPERATION 4 ACCESS 0
    //ADD OPTION aRotina TITLE '3 Gera Pedido'    	    ACTION 'U_W97F02B()' 	  OPERATION 4 ACCESS 0
    //ADD OPTION aRotina TITLE '2 Check Out'    	    ACTION 'U_N05F06A()' 	  OPERATION 4 ACCESS 0
    //ADD OPTION aRotina TITLE '3 Libera Pedido'    	ACTION 'U_N05F06B()' 	  OPERATION 4 ACCESS 0
    //ADD OPTION aRotina TITLE '4 Fatura Pedido'    	ACTION 'U_N05F06C()' 	  OPERATION 4 ACCESS 0


Return aRotina

USer Function DF02TOK( oModel)

    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local nTZ9CDPRD  := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local cSeek1 := ""
    Local cSeek2 := ""
    Local nPVSuger := 0.0
    Local nPVTab   := 0.0
    Local nMargem := 0.0
    Local lRet := .t.
    Local cMsgErroPrd := ""
    lOCAL nI,n2,n3
    conout("cteste")
    //oModel:GetOperation()
    if (oModel:GetOperation() == 3) .or. (oModel:GetOperation() == 4 )
        IF EMPTY(oModelSZ8:GETVALUE("Z8_DSCPRD"))
            D02F02D()
        ENDIF
        conout("cteste")
        DBSELECTAREA("SB1")
        SB1->(dbSetOrder(1))

        For nI := 1 To oModelSZ91:Length()
            //Z9_VUNIT
            if lRet
                oModelSZ91:GoLine( nI )
                //  IF EMPTY(oModelSZ91:GETVALUE("Z9_FILMOV"))
                //      oModelSZ91:LOADVALUE("Z9_FILMOV",XFILIAL("SZ8"))
                //  ENDIF
                cProd := oModelSZ91:GETVALUE("Z9_CDPROD")
                nVUnit := oModelSZ91:GETVALUE("Z9_VUNIT")

                // Ignora produtos de totalização (códigos iniciados por "000")
                IF SubStr(alltrim(cProd),1,3) != "000"
                    IF    SB1->(MsSeek(xFilial("SB1")+cProd))
                        if SB1->B1_TPMAT == "1" .and. SB1->B1_TIPO == "MP" .and.  nVUnit == 0.00
                            //B1_TPMAT 1=Nao;2=Sim
                            lRet := .f.
                            if !lAuto
                                // MSGINFO("Não é permitido Produtos MP com o Custo Zerado. Gentileza revisar",trim(cProd))
                                cMsgErroPrd += "Produto | "+ alltrim(cProd) + " | "+ alltrim(SB1->B1_DESC) + CHR(10)
                            else
                                //     MSGINFO("Auto Não é permitido Produtos MP com o Custo Zerado. Gentileza revisar",trim(cProd))
                                aTmpLog := {}

                                aadd(aTmpLog,ALLTRIM(oModelSZ8:GETVALUE("Z8_ID")) +" - "+ ALLTRIM(oModelSZ8:GETVALUE("Z8_COD")) )
                                aadd(aTmpLog,Alltrim(cProd)+" - "+alltrim(SB1->B1_DESC))
                                aadd(aTmpLog,"Não é permitido Produtos MP com o Custo Zerado. Gentileza revisar")

                                aadd( aLogProc,aTmpLog)
                                lRet := .t.
                            ENDIF
                        ENDIF
                        if SB1->B1_MSBLQL == '1'
                            cMsgErroPrd += "Produto | "+ alltrim(cProd) + " | "+ alltrim(SB1->B1_DESC)
                            cMsgErroPrd += "Encontra-se bloqueado " + CHR(10)
                        ENDIF
                    ENDIF
                    If   (SubStr(cProd,1,3) $ "MOD" ) .and. nVUnit == 0.00 .and. lRet
                        lRet := .f.
                        cMsgErroPrd += "Produto | "+ alltrim(cProd) + " | Custo Mao de Obra Zerado Gentileza Revisar Roteiro de Operações " + CHR(10)
                    ENDIF
                ENDIF

                // Validação específica para o produto 000002 (mantida conforme original)
                If   (alltrim(cProd) $ alltrim("000002" ) ) .and. oModelSZ91:GETVALUE("Z9_TOTAL") == 0.00 .and. lRet
                    lRet := .f.
                    cMsgErroPrd += "Produto | "+ alltrim(cProd) + " | Custo Mao de Obra Zerado Gentileza Revisar Roteiro de Operações " + CHR(10)
                    // aTmpLog := {}

                    // aadd(aTmpLog,ALLTRIM(oModelSZ8:GETVALUE("Z8_ID")) +" - "+ ALLTRIM(oModelSZ8:GETVALUE("Z8_COD")) )
                    // aadd(aTmpLog,Alltrim(cProd)+" - "+alltrim(SB1->B1_DESC))
                    // aadd(aTmpLog,"Não é permitido Produtos MOD com o Custo Zerado. Gentileza revisar")

                    // aadd( aLogProc,aTmpLog)

                EndIf
            ENDIF
        next nI

        /*   For n2 := 1 To oModelSZ92:Length()
            //Z9_VUNIT
            lCanAlt := .T.
            if lRet .AND.  EMPTY(oModelSZ92:GETVALUE("Z9_FILMOV"))
                oModelSZ92:GoLine( n2 )
                oModelSZ92:LOADVALUE("Z9_FILMOV",XFILIAL("SZ8"))
            ENDIF
            lCanAlt := .f.
        next n2

        For n3 := 1 To oModelSZ93:Length()
            //Z9_VUNIT
            lCanAlt := .T.
            if lRet .AND.  EMPTY(oModelSZ93:GETVALUE("Z9_FILMOV"))
                oModelSZ93:GoLine( n3 )
                oModelSZ93:LOADVALUE("Z9_FILMOV",XFILIAL("SZ8"))


            ENDIF
            lCanAlt := .f.
        next n3*/
        if lRet .and. !EMpty(oModelSZ8:GETVALUE("Z8_NROPOR"))
            // DbSelectArea("ADZ")
            // SBZ->(dbSetOrder(2))

            cSql := " SELECT ADY.R_E_C_N_O_ RECADY, ADZ.R_E_C_N_O_ RECADZ,ADZ_PRCVEN,AD1.R_E_C_N_O_ RECAD1 " + cEol
            cSql += " FROM	dbo." + retsqlname("ADY") + " ADY (NOLOCK) " + cEol
            cSql += " JOIN dbo." + retsqlname("ADZ") + " ADZ (NOLOCK) ON ADZ.D_E_L_E_T_ = '' " + cEol
            cSql += "       AND ADY.ADY_FILIAL = ADZ.ADZ_FILIAL " + cEol
            cSql += "       AND ADY.ADY_PROPOS = ADZ.ADZ_PROPOS " + cEol
            cSql += " JOIN dbo." + retsqlname("AD1") + " AD1 (NOLOCK) ON AD1.D_E_L_E_T_ ='' " + cEol
            cSql += "       AND AD1.AD1_FILIAL=  " + VALTOSQL(xfilial("AD1"))+ cEol
            cSql += "       AND AD1.AD1_NROPOR = ADY.ADY_OPORTU  " + cEol
            cSql += "       AND ADY_REVISA = AD1.AD1_REVISA      " + cEol
            cSql += "       AND ADY_CLIENT = AD1.AD1_CODCLI      " + cEol
            cSql += "       AND ADY_LOJENT = AD1.AD1_LOJCLI      " + cEol
            cSql += " WHERE ADY.D_E_L_E_T_ = '' " + cEol
            cSql += "       AND ADY.ADY_FILIAL = " + VALTOSQL(xfilial("ADY")) + cEol
            cSql += "       AND ADY.ADY_OPORTU = " + valtosql(oModelSZ8:GETVALUE("Z8_NROPOR"))  + cEol
            cSql += "       AND ADZ.ADZ_PRODUT = " + valtosql(oModelSZ8:GETVALUE("Z8_COD"))

            If Select('TMPOPOR') <> 0
                TMPOPOR->(dbCloseArea())
            Endif
            TCQuery cSql Alias TMPOPOR New
            if TMPOPOR->(!eof()) .AND. ROUND( TMPOPOR->ADZ_PRCVEN  ,2)!=  ROUND(oModelSZ8:GETVALUE("Z8_PVSUGER"),2)
                DbSelectArea("ADY")
                ADY->(dbGoTo(TMPOPOR->RECADY))
                DbSelectArea("ADZ")
                ADZ->(dbGoTo(TMPOPOR->RECADZ))
                DbSelectArea("AD1")
                AD1->(dbGoTo(TMPOPOR->RECAD1))

                oModel := FWLoadModel("FATA600")
                oModel:SetOperation(4)
                oModel:Activate()
                oMDADZ := oModel:GetModel("ADZPRODUTO")
                For nI := 1 To oMDADZ:Length()
                    oMDADZ:GOLINE(nI)
                    IF oMDADZ:GETVALUE("ADZ_PRODUT") == oModelSZ8:GETVALUE("Z8_COD")

                        oMDADZ:SetValue("ADZ_PRCVEN",  ROUND(oModelSZ8:GETVALUE("Z8_PVSUGER"),2))
                        oMDADZ:SetValue("ADZ_PRCTAB",  ROUND(oModelSZ8:GETVALUE("Z8_PVSUGER"),2))

                    ENDIF
                next nI
                If oModel:VldData()
                    If oModel:CommitData()
                        lOk := .T.

                        //Se não deu certo, altera a variável para false
                    Else
                        lOk := .F.
                    EndIf

                    //Se não conseguir validar as informações, altera a variável para false
                Else
                    lOk := .F.
                EndIf

                If ! lOk
                    //Busca o Erro do Modelo de Dados
                    aErro := oModel:GetErrorMessage()

                    //Monta o Texto que será mostrado na tela
                    cMessage := "Id do formulário de origem:"  + ' [' + cValToChar(aErro[01]) + '], '
                    cMessage += "Id do campo de origem: "      + ' [' + cValToChar(aErro[02]) + '], '
                    cMessage += "Id do formulário de erro: "   + ' [' + cValToChar(aErro[03]) + '], '
                    cMessage += "Id do campo de erro: "        + ' [' + cValToChar(aErro[04]) + '], '
                    cMessage += "Id do erro: "                 + ' [' + cValToChar(aErro[05]) + '], '
                    cMessage += "Mensagem do erro: "           + ' [' + cValToChar(aErro[06]) + '], '
                    cMessage += "Mensagem da solução: "        + ' [' + cValToChar(aErro[07]) + '], '
                    cMessage += "Valor atribuído: "            + ' [' + cValToChar(aErro[08]) + '], '
                    cMessage += "Valor anterior: "             + ' [' + cValToChar(aErro[09]) + ']'

                    ConOut("Erro: " + cMessage)

                EndIf
                //Desativa o modelo de dados
                oModel:DeActivate()

                TMPOPOR->(dbCloseArea())
            endif
        endif

    ENDIF
    /*valida ajuste na oportunidade*/

    IF LEN(cMsgErroPrd) > 0
        EEcView(cMsgErroPrd, "Itens Com Problemas no Custo")
    ENDIF
Return lRet


/*====================================*\
|| # Func:  ModelDef   MVC		    # ||
\*====================================*/

Static Function ModelDef()
    Local oModel         := Nil
    Local oStSZ8	    := FWFormStruct(1, 'SZ8')
    Local oStSZ91	    := FWFormStruct(1, 'SZ9')
    Local oStSZ92	    := FWFormStruct(1, 'SZ9')
    Local oStSZ93	    := FWFormStruct(1, 'SZ9')
    LOCAL  nPerFrt := SuperGetMv("MV_DLPPFRT",.F.,3.5)
    LOCAL  nPerMOD := SuperGetMv("MV_DLPPMOD",.F.,0.00)
    Local cUserId   := RetCodUsr()
    Local cFiltSZ9  := ""
    //oModel := MPFormModel():New('D02F02',/*bPreValidacao*/,  /*{|oModel| u_validtok(oModel)} /* bTudoOK*/ ,  {|oModel| U_DF02TOK( oModel:GetOperation(), oModel)} )
    oModel := MPFormModel():New('D02F02',,  {|oModel| U_DF02TOK( oModel)} )
    //  oModel := MPFormModel():New('D02F02' )

    oModel:AddFields( "SZ8MASTER", /*cOwner*/, oStSZ8,,,/*bLoad*/ )

    oModel:SetPrimaryKey( {"Z8_FILIAL", "Z8_ID"} )

    oModel:SetDescription("Delpi - Formacao de Preco")

    //oModel:AddGrid('ZA7DETAIL','ZA6MASTER',oStZA7,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    //oModel:SetRelation( "ZA7DETAIL", {	{"ZA7_FILIAL","xFilial('ZA7')"  },{"ZA7_IDZA6","ZA6_ID"}}, ZA7->( IndexKey( 2 ) ) )

    oModel:AddGrid('SZ9DETAIL01','SZ8MASTER',oStSZ91,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    oModel:SetRelation( "SZ9DETAIL01", {	{"Z9_IDZ8","Z8_ID"},{"Z9_IDFLD","'1PRD01'"}}, SZ9->( IndexKey( 1 ) ) )
    oModel:AddGrid('SZ9DETAIL02','SZ8MASTER',oStSZ92,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    oModel:SetRelation( "SZ9DETAIL02", {	{"Z9_IDZ8","Z8_ID"},{"Z9_IDFLD","'3IMP01'"}}, SZ9->( IndexKey( 1 ) ) )
    oModel:AddGrid('SZ9DETAIL03','SZ8MASTER',oStSZ93,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    oModel:SetRelation( "SZ9DETAIL03", {	{"Z9_IDZ8","Z8_ID"},{"Z9_IDFLD","'2OPE01'"}}, SZ9->( IndexKey( 1 ) ) )
    oModel:getModel('SZ9DETAIL01'):SetOptional(.T.)
    oModel:getModel('SZ9DETAIL02'):SetOptional(.T.)
    oModel:getModel('SZ9DETAIL03'):SetOptional(.T.)

    // Inits explicitos para Z9_FILIAL e Z9_FILMOV ja que removi o filtro
    // de Z9_FILIAL do SetRelation (necessario para fallback em legados)
    oStSZ91:SetProperty('Z9_FILIAL', MODEL_FIELD_INIT, {|| xFilial('SZ9') })
    oStSZ92:SetProperty('Z9_FILIAL', MODEL_FIELD_INIT, {|| xFilial('SZ9') })
    oStSZ93:SetProperty('Z9_FILIAL', MODEL_FIELD_INIT, {|| xFilial('SZ9') })
    oStSZ91:SetProperty('Z9_FILMOV', MODEL_FIELD_INIT, {|| xFilial('SZ8') })
    oStSZ92:SetProperty('Z9_FILMOV', MODEL_FIELD_INIT, {|| xFilial('SZ8') })
    oStSZ93:SetProperty('Z9_FILMOV', MODEL_FIELD_INIT, {|| xFilial('SZ8') })

    oStSZ8:SetProperty('Z8_CDTABVN'		,MODEL_FIELD_VALID, {|| D02F02H()	})
    oStSZ8:SetProperty('Z8_IDSZ7'		,MODEL_FIELD_VALID, {|| D02F02A({"Z8_IDSZ7","MODEL_FIELD_VALID"})	})
    oStSZ8:SetProperty('Z8_COD'		    ,MODEL_FIELD_VALID, {|| D02F02A({"Z8_COD","MODEL_FIELD_VALID"})	})

    oStSZ91:AddTrigger('Z9_QUANT',"Z9_TOTAL"    ,{|| .T.}, {|| D02F02C()	} )
    oStSZ91:AddTrigger('Z9_VUNIT',"Z9_TOTAL"    ,{|| .T.}, {|| D02F02C()	} )
    oStSZ91:AddTrigger('Z9_TABPRCC',"Z9_VUNIT"    ,{|| .T.}, {|| D02F02G()	} )
    aFltSZ9   := {}
    //aadd(aFltSZ9, {"Z9_FILMOV","'"+xFilial('SZ8')+"'" })
    aadd(aFltSZ9, {"Z9_FILMOV","'"+xFilial('SZ8')+"'" })

    // oModel:GetModel( 'SZ7DETAIL01' ):SetLoadFilter( , " Z7_FOLDER = '"+cBox1+"'" )

    //oModel:GetModel('SZ9DETAIL01'):SetLoadFilter(," Z9_FILMOV = '"+xFilial('SZ8')+"'" )
    //oModel:GetModel('SZ9DETAIL02'):SetLoadFilter(," Z9_FILMOV = '"+xFilial('SZ8')+"'" )
    //oModel:GetModel('SZ9DETAIL03'):SetLoadFilter(," Z9_FILMOV = '"+xFilial('SZ8')+"'" )
    cFiltSZ9 := fD02FltSZ9(SZ8->Z8_ID, xFilial('SZ8'), SZ8->Z8_COD)
    oModel:GetModel('SZ9DETAIL01'):SetLoadFilter(, cFiltSZ9)
    oModel:GetModel('SZ9DETAIL02'):SetLoadFilter(, cFiltSZ9)
    oModel:GetModel('SZ9DETAIL03'):SetLoadFilter(, cFiltSZ9)
    if cUserId $"000000_000000"
        oStSZ8:SetProperty('Z8_IDSZ7'		    ,MODEL_FIELD_INIT,  {|| "000002"	})
        oStSZ8:SetProperty('Z8_DESC'		    ,MODEL_FIELD_INIT,  {|| "PLANILHA FORMACAO PADRAO DELPI GDA                                                                    	"	})
        oStSZ8:SetProperty('Z8_COD'		    ,MODEL_FIELD_INIT,  {|| "80014984       "	})
        //     oStSZ8:SetProperty('Z8_PERFRT'		    ,MODEL_FIELD_INIT,  {|| 3.00	})
        //     oStSZ8:SetProperty('Z8_FATMOD'		    ,MODEL_FIELD_INIT,  {||0.7	})

    endif

    // oStSZ91:SetProperty('Z9_FILMOV'		    ,MODEL_FIELD_INIT,  {|| xFilial('SZ8')	})
    // oStSZ92:SetProperty('Z9_FILMOV'		    ,MODEL_FIELD_INIT,  {|| xFilial('SZ8')	})
    // oStSZ93:SetProperty('Z9_FILMOV'		    ,MODEL_FIELD_INIT,  {|| xFilial('SZ8')	})

    oStSZ8:SetProperty('Z8_PERFRT'		    ,MODEL_FIELD_INIT,  {|| nPerFrt	})
    oStSZ8:SetProperty('Z8_FATMOD'		    ,MODEL_FIELD_INIT,  {||nPerMOD	})
    oStSZ8:SetProperty('Z8_TMPSET'		    ,MODEL_FIELD_INIT,  {|| "2"	})
    //   oStSZ8:SetProperty('Z8_ID'		    ,MODEL_FIELD_INIT,  {|| D02F02A({"Z8_ID","MODEL_FIELD_INIT"})	})
    oStSZ8:SetProperty('Z8_ID'		    ,MODEL_FIELD_WHEN,  {|| .f.	})
    //  oStSZ8:SetProperty('Z8_DSCPRD'		    ,MODEL_FIELD_WHEN,  {|| lCanAlt})
    oStSZ8:SetProperty('Z8_PVTAB'		    ,MODEL_FIELD_WHEN,  {|| lCanAlt .OR. lAuto})
    oStSZ8:SetProperty('Z8_PVSUGER'		    ,MODEL_FIELD_WHEN,  {|| lCanAlt .OR. lAuto})
    oStSZ8:SetProperty('Z8_MARGEM'		    ,MODEL_FIELD_WHEN,  {|| lCanAlt .OR. lAuto})
    oStSZ8:SetProperty('Z8_DSCPRD'		    ,MODEL_FIELD_WHEN,  {|| lCanAlt .OR. lAuto})
    //oStSZ8:SetProperty('Z8_FATMP'		    ,MODEL_FIELD_WHEN,  {|| lCanAlt .OR. lAuto})

    oStSZ91:SetProperty( 'Z9_CDPROD' , MODEL_FIELD_WHEN , {|| lCanAlt .OR. lAuto} )
    oStSZ92:SetProperty( 'Z9_CDPROD' , MODEL_FIELD_WHEN , {|| lCanAlt .OR. lAuto} )
    oStSZ93:SetProperty( 'Z9_CDPROD' , MODEL_FIELD_WHEN , {|| lCanAlt .OR. lAuto} )
    oStSZ91:SetProperty( 'Z9_DESC' ,   MODEL_FIELD_WHEN , {|| lCanAlt .OR. lAuto} )
    oStSZ92:SetProperty( 'Z9_DESC' ,   MODEL_FIELD_WHEN , {|| lCanAlt .OR. lAuto} )
    oStSZ93:SetProperty( 'Z9_DESC' ,   MODEL_FIELD_WHEN , {|| lCanAlt .OR. lAuto} )

    oStSZ91:SetProperty("Z9_VUNIT",MODEL_FIELD_TITULO,"Unit Bruto")
    oStSZ91:SetProperty("Z9_TOTAL",MODEL_FIELD_TITULO,"Total Bruto")



    oStSZ92:RemoveField( 'Z9_OBS' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_OBS' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_QUANT' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_QUANT' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_VUNIT' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_VUNIT' ) //VIEW E MODEL


Return oModel

/*---------------------------------------------------------------------*
| Func:  D02F02A                                                      |
| VALIDACOES GERAIS DE INICIALIZADOR E TRIGGER                        |
*---------------------------------------------------------------------*/

Static Function D02F02A(aPars)
    Local xRet   := Nil
    Local oModel := FWModelActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")

    lOCAL cIdSZ7 := oModelSZ8:GETVALUE("Z8_IDSZ7")
    //Local nOperation := oModel:GetOperation()
    //Local oModelZA2 := oModel:GetModel( 'ZA2DETAIL' )
    //D02F02A //FUNCAO PARA PREENCHER OS CAMPOS
    if aPars[1] $"Z8_ID" .and. aPars[1] $ "MODEL_FIELD_INIT"

        //    xNum := GetSxeNum("SZ8","Z8_ID")
        //    ConfirmSx8()
        //    bInitDesc	:= FWBuildFeature( STRUCT_FEATURE_INIPAD, 'IIF(!INCLUI,Posicione("FKC",1, xFilial("FKC") + FKD->FKD_CODIGO,"FKC_DESC"),"")')
        //    //    oMdlSZ8:SetValue(  'Z8_ID', xNum )

    elseif  aPars[1] $"Z8_IDSZ7" .and. aPars[2] $ "MODEL_FIELD_VALID"
        xOper := oModel:GetOperation()

        IF xOper == 4  .AND. SZ8->Z8_IDSZ7 != oModelSZ8:GETVALUE("Z8_IDSZ7")
            xRet := .f.
            if lAuto

                aTmpLog := {}

                aadd(aTmpLog,ALLTRIM(oModelSZ8:GETVALUE("Z8_ID")) +" - "+ ALLTRIM(oModelSZ8:GETVALUE("Z8_COD")) )
                aadd(aTmpLog,"VlrAtu " + Alltrim(SZ8->Z8_IDSZ7)+" - Vlr Novo "+alltrim(oModelSZ8:GETVALUE("Z8_IDSZ7")))
                aadd(aTmpLog,"Não é permitido Alterar Planilha de Calculo")

                aadd( aLogProc,aTmpLog)
                //   aadd(aLogProc,{"03",cIdSZ7+" - Planilha Não esta Ativa "})
            else
                FWAlertError("Não é permitido Alterar Planilha de Calculo", "Formação Preco")
            endif
        ELSE
            DBSELECTAREA("SZ7")
            SZ7->(dbSetOrder(1))
            IF    SZ7->(MsSeek(xFilial("SZ7")+cIdSZ7))
                if SZ7->Z7_STACALC == 'I'
                    xRet := .f.

                    aadd(aLogProc,{"01",cIdSZ7+" - Planilha Não esta Ativa "})
                ELSE
                    xRet := .t.
                ENDIF
            else

                xRet := .f.
                aadd(aLogProc,{"02",cIdSZ7+" - Planilha Não Localizada "})

            ENDIF
        ENDIF

        /*2023/01 AJUSTE FATOR MP*/
        IF xRet == .t.
            D02F02I()
        endif
    elseif  aPars[1] $"Z8_COD" .and. aPars[2] $ "MODEL_FIELD_VALID"

        If oModel:isActive()
            oModelSZ91:GoLine(1)
            cProdGrid := oModelSZ91:GETVALUE("Z9_CDPROD")
            cCodZ8 := oModelSZ8:getvalue("Z8_COD")
            xOper := oModel:GetOperation()
            if cProdGrid != cCodZ8 .and. xOper == 4
                xRet := .f.
            else
                D02F02D()
                xRet := .t.
            ENDIF
        ENDIF


    ENDIF

Return xRet
/*---------------------------------------------------------------------*
| Func:  ViewDef                                                      |
*---------------------------------------------------------------------*/

Static Function ViewDef()

    Local oView     := Nil
    Local oModel    := FWLoadModel('DLP02F02')
    Local oStSZ8	:= FWFormStruct(2, 'SZ8')
    Local oStSZ91	:= FWFormStruct(2, 'SZ9')
    Local oStSZ92	:= FWFormStruct(2, 'SZ9')
    Local oStSZ93	:= FWFormStruct(2, 'SZ9')

    //Criando a View
    oView := FWFormView():New()

    oView:SetModel(oModel)

    oView:AddField('Master_SZ8' , oStSZ8,'SZ8MASTER' )
    oView:AddGrid('Detail_SZ91' , oStSZ91,'SZ9DETAIL01')
    oView:AddGrid('Detail_SZ92' , oStSZ92,'SZ9DETAIL02')
    oView:AddGrid('Detail_SZ93' , oStSZ93,'SZ9DETAIL03')


    oView:CreateHorizontalBox( '01CAB', 20) //CABECALHO
    oView:CreateHorizontalBox( 'BOX01', 40)  //PRODUTOS
    oView:CreateHorizontalBox( 'BOX02', 40)  //IMPOSTO / IOPERACIONAL
    // Quebra em 2 "box" vertical para receber algum elemento da view
    oView:CreateVerticalBox( 'BOX02ESQ', 50, 'BOX02' )
    oView:CreateVerticalBox( 'BOX02DIR', 50, 'BOX02' )

    oView:SetOwnerView('Master_SZ8','01CAB')
    oView:SetOwnerView('Detail_SZ91','BOX01')
    oView:SetOwnerView('Detail_SZ92','BOX02ESQ')
    oView:SetOwnerView('Detail_SZ93','BOX02DIR')

    oStSZ8:RemoveField( 'Z8_DTAPROV')
    oStSZ8:RemoveField( 'Z8_IDAPROV')
    oStSZ8:RemoveField( 'Z8_ULTPV')
    oStSZ8:RemoveField( 'Z8_DTULTPV')
    oStSZ8:RemoveField( 'Z8_SITUA')
    oStSZ8:RemoveField( 'Z8_PVTMP')

    // oStSZ91:RemoveField( 'Z9_PERCENT' )  //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_PERCENT' )  //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_PERCENT' )  //VIEW E MODEL

    oStSZ91:RemoveField( 'Z9_FILMOV' )  //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_FILMOV' )  //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_FILMOV' )  //VIEW E MODEL

    oStSZ91:RemoveField( 'Z9_IDZ8' )  //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_IDZ8' )  //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_IDZ8' )  //VIEW E MODEL
    oStSZ91:RemoveField( 'Z9_IDFLD' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_IDFLD' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_IDFLD' ) //VIEW E MODEL
    //   oStSZ91:RemoveField( 'Z9_ALIQ' )  //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_QUANT' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_QUANT' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_VUNIT' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_VUNIT' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_OBS' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_OBS' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_CDPROD' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_CDPROD' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_PRCLIQ' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_PRCLIQ' ) //VIEW E MODEL
    oStSZ92:RemoveField( 'Z9_TABPRCC' ) //VIEW E MODEL
    oStSZ93:RemoveField( 'Z9_TABPRCC' ) //VIEW E MODEL

    oStSZ91:SetProperty("Z9_VUNIT",MVC_VIEW_TITULO,"Unit Bruto")
    oStSZ91:SetProperty("Z9_ALIQ",MVC_VIEW_TITULO,"Aliq")
    oStSZ91:SetProperty("Z9_PERCENT",MVC_VIEW_TITULO,"%")
    oStSZ91:SetProperty("Z9_TABPRCC",MVC_VIEW_TITULO,"Tab Prc")
    oStSZ91:SetProperty("Z9_TOTAL",MVC_VIEW_TITULO,"Total Bruto")
    oStSZ91:SetProperty("Z9_VUNIT",MVC_VIEW_DESCR,"Unit Bruto")
    oStSZ91:SetProperty("Z9_TOTAL",MVC_VIEW_DESCR,"Total Bruto")

    nLarg := 100
    oStSZ91:SetProperty("Z9_TOTAL",MVC_VIEW_WIDTH ,nLarg)
    oStSZ91:SetProperty("Z9_PRCLIQ",MVC_VIEW_WIDTH ,nLarg)
    oStSZ91:SetProperty("Z9_CDPROD",MVC_VIEW_WIDTH ,nLarg)



    nLarg :=70
    oStSZ91:SetProperty("Z9_VUNIT",MVC_VIEW_WIDTH ,nLarg)
    oStSZ91:SetProperty("Z9_ALIQ",MVC_VIEW_WIDTH ,nLarg)
    oStSZ91:SetProperty("Z9_QUANT",MVC_VIEW_WIDTH ,nLarg)
    oStSZ91:SetProperty("Z9_PERCENT",MVC_VIEW_WIDTH ,nLarg)

    nLarg := 60

    oStSZ91:SetProperty("Z9_TABPRCC",MVC_VIEW_WIDTH ,nLarg)
    nLarg := 350


    oStSZ91:SetProperty("Z9_DESC",MVC_VIEW_WIDTH ,nLarg)



    nLarg := 100

    oStSZ92:SetProperty("Z9_DESC",MVC_VIEW_WIDTH ,nLarg)
    oStSZ93:SetProperty("Z9_DESC",MVC_VIEW_WIDTH ,nLarg)

    oView:AddUserButton( 'Preenche dados', 'DADOS', {|oView| U_D02fPDados()} )
    oView:AddUserButton( 'Tabela de Preco', 'DADOS2', {|oView| U_fSetTabPV()} )
    oView:AddUserButton("Imprimir","",{|oView| print(oView)})
    oView:EnableTitleView('Detail_SZ91','Estrutura')
    oView:EnableTitleView('Detail_SZ92','Mark-up Impostos')
    oView:EnableTitleView('Detail_SZ93','Mark-up Operacional')
    oView:AddIncrementField( 'SZ9DETAIL01', 'Z9_ITEM' )
    oView:AddIncrementField( 'SZ9DETAIL02', 'Z9_ITEM' )
    oView:AddIncrementField( 'SZ9DETAIL03', 'Z9_ITEM' )

Return oView

/*Static Function fPrcImp()
    Local cSql := ""
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local nTamPrd   := GetSx3cache("B1_COD","X3_TAMANHO")
    Local nTaMZ9DESC   := GetSx3cache("Z9_DESC","X3_TAMANHO")
    Local lSbz := .f.
    Local lSb1 := .f.
    Local nAliq := 0
    Local nAliqTot := 0
    lOCAL cIdSZ8 := oModelSZ8:GETVALUE("Z8_ID")
    lOCAL cIdSZ7 := oModelSZ8:GETVALUE("Z8_IDSZ7")
    xVAr := Nil

    cCodPro :=padr( oModelSZ8:getvalue("Z8_COD"),nTamPrd)

    cSql :="SELECT * FROM dbo." + retsqlname("SZ7") + " SZ7 " + cEol
    cSql +="WHERE D_E_L_E_T_='' AND Z7_ID="+valtosql(cIdSZ7)+" AND Z7_FOLDER='3IMP01' " + cEol
    cSql +="ORDER BY Z7_ITEM "


    If Select('TMPIMP') <> 0
        TMPIMP->(dbCloseArea())
    Endif

    DBSELECTAREA("SBZ")
    SBZ->(dbSetOrder(1))
    IF    SBZ->(MsSeek(xFilial("SBZ")+cCodPro))
        lSbz := .t.
    ENDIF

    DBSELECTAREA("SB1")
    SB1->(dbSetOrder(1))
    IF    SB1->(MsSeek(xFilial("SB1")+cCodPro))
        lSb1 := .t.
    ENDIF
    TCQuery cSql Alias TMPIMP New
    While TMPIMP->(!eof())
        nAliq := 0
        nTot  := 0

        cCodIte  := padr( TMPIMP->Z7_CAMPO,nTamPrd)
        cDescTmp := padr( TMPIMP->Z7_DESCCMP,nTaMZ9DESC)
        //CALCULO DO CONTEUDO
        IF upper(alltrim(TMPIMP->Z7_CAMPO)) $ alltrim("000005" )
            CONOUT("ENTROU NO coefi")
        ENDIF

        IF SUBSTR(TMPIMP->Z7_FORMULA,1,3) $"SBZ" .AND. lSbz
            nAliq := &(TMPIMP->Z7_FORMULA)

        elseif SUBSTR(TMPIMP->Z7_FORMULA,1,3) $"SB1" .AND. lSb1
            nAliq := &(TMPIMP->Z7_FORMULA)
        elseif upper(alltrim(TMPIMP->Z7_CAMPO)) $ alltrim("000005" ) //para calcular o coeficiente

            //   nAliq := &(TMPIMP->Z7_FORMULA)
            aRet    := &(TMPIMP->Z7_FORMULA)
            nTot    := aRet[2]
            nAliq   := aRet[1]
        elseif upper(alltrim(TMPIMP->Z7_CAMPO)) $ alltrim("000007_000006" ) //para calcular o coeficiente
            nTot    :=&(TMPIMP->Z7_FORMULA)

            if upper(alltrim(TMPIMP->Z7_CAMPO)) $ alltrim("000006" ) .and. !Empty(cTabPV)

                cDescTmp :=  PADR(alltrim(cDescTmp)+' - '+ cTabPV,GETSX3CACHE("Z9_DESC","X3_TAMANHO") )

            endif

        elseif upper(alltrim(TMPIMP->Z7_CAMPO)) $ alltrim("000001" ) //para calcular o ICMS

            aRet    := &(TMPIMP->Z7_FORMULA)
            nTot    := aRet[1]
            nAliq   := 12 //aRet[2]

        elseif upper(alltrim(TMPIMP->Z7_CAMPO)) $ alltrim("000002" ) //para calcular o PIS COFINS
            aRet    := &(TMPIMP->Z7_FORMULA)
            nTot    := aRet[1]
            nAliq   := aRet[2]
        elseif !Empty(TMPIMP->Z7_FORMULA)

            nAliq := &(TMPIMP->Z7_FORMULA)

        endif
        //Atribui o valor calculado as variaveis privadas
        if !Empty(TMPIMP->Z7_LOGINC) .AND. nAliq > 0
            &(TMPIMP->Z7_LOGINC) := nAliq
        ENDIF

        //  trativa para quando retornar valor ao inves de aliquota
        if nAliq > 100

            nTot := nAliq
            nAliq := (nTot / nPVOper)*100
        endif
        nAliqTot+=nAliq
        IF oModelSZ92:NLINE == 1
            oModelSZ92:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ92:SETVALUE("Z9_IDFLD",cBox2)
            //   oModelSZ92:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ92:NLINE,nTmIt))
            oModelSZ92:SETVALUE("Z9_CDPROD",cCodIte)
            oModelSZ92:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ92:SETVALUE("Z9_ALIQ",nAliq)
            oModelSZ92:SETVALUE("Z9_TOTAL",nTot)
            oModelSZ92:AddLine()

        ELSE
            oModelSZ92:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ92:SETVALUE("Z9_IDFLD",cBox2)
            //  oModelSZ92:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ92:NLINE,nTmIt))
            oModelSZ92:SETVALUE("Z9_CDPROD",cCodIte)
            oModelSZ92:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ92:SETVALUE("Z9_ALIQ",nAliq)
            oModelSZ92:SETVALUE("Z9_TOTAL",nTot)
            oModelSZ92:AddLine()

        ENDIF

        TMPIMP->(dbskip())
    Enddo
    oModelSZ92:DeleteLine()
    TMPIMP->(dbCloseArea())

    For nI := 1 To oModelSZ92:Length()
        oModelSZ92:GOLINE(nI)
        if !(alltrim(oModelSZ92:GETVALUE("Z9_CDPROD")) $ alltrim("000002_000001_000006_000008" ) )

            nAliq := oModelSZ92:GETVALUE("Z9_ALIQ")/100
            oModelSZ92:SETVALUE("Z9_TOTAL",nAliq*nPVVenda)

        endif
    next nI
    //   fPrcRecal()

    fProcCusMp()
Return*/

Static Function fPrcImp2()
    Local cSql := ""
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local nTamPrd   := GetSx3cache("B1_COD","X3_TAMANHO")
    Local nTaMZ9DESC   := GetSx3cache("Z9_DESC","X3_TAMANHO")
    Local lSbz := .f.
    Local lSb1 := .f.
    Local nAliq := 0
    Local nAliqTot := 0
    lOCAL cIdSZ8 := oModelSZ8:GETVALUE("Z8_ID")
    lOCAL cIdSZ7 := oModelSZ8:GETVALUE("Z8_IDSZ7")
    xVAr := Nil

    cCodPro :=padr( oModelSZ8:getvalue("Z8_COD"),nTamPrd)

    cSql :="SELECT * FROM dbo." + retsqlname("SZ7") + " SZ7 " + cEol
    cSql +="WHERE D_E_L_E_T_='' AND Z7_ID="+valtosql(cIdSZ7)+" AND Z7_FOLDER='3IMP01' " + cEol
    cSql +="ORDER BY Z7_TIPO,Z7_ITEM "


    If Select('TMPIMP') <> 0
        TMPIMP->(dbCloseArea())
    Endif


    TCQuery cSql Alias TMPIMP New
    //TMPIMP->( RecCount() )
    While TMPIMP->(!eof())

        nAliq := 0
        nTot  := 0

        cCodIte  := padr( TMPIMP->Z7_CAMPO,nTamPrd)
        cDescTmp := padr( TMPIMP->Z7_DESCCMP,nTaMZ9DESC)
        If  TRIM(TMPIMP->Z7_TIPO ) $ "1"

            nAliq := TMPIMP->Z7_VLRINI
            nAliqTot += TMPIMP->Z7_VLRINI

        ELSE
            nAliq := 100-nAliqTot
        EndIf

        //CALCULO DO CONTEUDO

        IF oModelSZ92:NLINE == 1
            oModelSZ92:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ92:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
            oModelSZ92:SETVALUE("Z9_IDFLD",cBox2)

            IF lAuto
                oModelSZ92:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ92:NLINE,nTmIt))
            ENDIF
            oModelSZ92:SETVALUE("Z9_CDPROD",cCodIte)
            oModelSZ92:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ92:SETVALUE("Z9_ALIQ",nAliq)
            //       oModelSZ92:SETVALUE("Z9_TOTAL",nTot)


        ELSE
            oModelSZ92:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
            oModelSZ92:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ92:SETVALUE("Z9_IDFLD",cBox2)
            IF lAuto
                oModelSZ92:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ92:NLINE,nTmIt))
            ENDIF
            oModelSZ92:SETVALUE("Z9_CDPROD",cCodIte)
            oModelSZ92:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ92:SETVALUE("Z9_ALIQ",nAliq)
            //       oModelSZ92:SETVALUE("Z9_TOTAL",nTot)


        ENDIF

        TMPIMP->(dbskip())
        IF TMPIMP->(!eof())
            oModelSZ92:AddLine()
        ENDIF
        CONOUT("TESTE")
    Enddo

    TMPIMP->(dbCloseArea())

Return
/*/{Protheus.doc} fPrcOpe2
  Função Para Calcular os itens da aba Operacional
    @type  Function
    @author Gabriel
    @since 24/05/2021
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
Static Function fPrcOpe2()

    Local cSql          := ""
    Local oModel        := FWMODELACTIVE()
    Local oView         := FWViewActive()
    Local oModelSZ8     := oModel:GetModel("SZ8MASTER")
    Local oModelSZ93    := oModel:GetModel("SZ9DETAIL03")
    Local nTamPrd       := GetSx3cache("B1_COD","X3_TAMANHO")
    Local nTaMZ9DESC    := GetSx3cache("Z9_DESC","X3_TAMANHO")
    Local nAliqOpe      := 0.00
    Local nAliqTot      := 0.00
    lOCAL cIdSZ8        := oModelSZ8:GETVALUE("Z8_ID")
    lOCAL cIdSZ7        := oModelSZ8:GETVALUE("Z8_IDSZ7")

    cSql :="SELECT * FROM dbo." + retsqlname("SZ7") + " SZ7 " + cEol
    cSql +="WHERE D_E_L_E_T_='' AND  Z7_ID = "+valtosql(cIdSZ7)+" AND Z7_FOLDER='2OPE01' " + cEol
    cSql +="ORDER BY Z7_TIPO,Z7_ITEM "


    If Select('TMPOPE') <> 0
        TMPOPE->(dbCloseArea())
    Endif

    TCQuery cSql Alias TMPOPE New
    While TMPOPE->(!eof())

        nTot     := 0.00
        cCodIte  := padr( TMPOPE->Z7_CAMPO,nTamPrd)
        cDescTmp := padr( TMPOPE->Z7_DESCCMP,nTaMZ9DESC)

        If  TRIM(TMPOPE->Z7_TIPO ) $ "1"

            nAliqOpe := TMPOPE->Z7_VLRINI
            nAliqTot += TMPOPE->Z7_VLRINI

        ELSE

            nAliqOpe := 100-nAliqTot

        EndIf

        IF oModelSZ93:NLINE == 1
            oModelSZ93:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
            oModelSZ93:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ93:SETVALUE("Z9_IDFLD",cBox3)

            oModelSZ93:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ93:SETVALUE("Z9_ALIQ",nAliqOpe)
            oModelSZ93:SETVALUE("Z9_TOTAL",nTot)
        ELSE
            oModelSZ93:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
            oModelSZ93:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ93:SETVALUE("Z9_IDFLD",cBox3)

            oModelSZ93:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ93:SETVALUE("Z9_ALIQ",nAliqOpe)
            oModelSZ93:SETVALUE("Z9_TOTAL",nTot)


        ENDIF

        TMPOPE->(dbskip())
        IF TMPOPE->(!eof())
            oModelSZ93:AddLine()
        ENDIF
    Enddo
    TMPOPE->(dbCloseArea())

Return
/*Static Function fPrcOpe()

    Local cSql := ""
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local nTamPrd   := GetSx3cache("B1_COD","X3_TAMANHO")
    Local nTaMZ9DESC   := GetSx3cache("Z9_DESC","X3_TAMANHO")
    Local nAliqOpe := 0
    lOCAL cIdSZ8 := oModelSZ8:GETVALUE("Z8_ID")
    cSql :="SELECT * FROM dbo." + retsqlname("SZ7") + " SZ7 " + cEol
    cSql +="WHERE D_E_L_E_T_='' AND  Z7_ID = "+valtosql(cIdSZ7)+" AND Z7_FOLDER='2OPE01' " + cEol
    cSql +="ORDER BY Z7_TIPO,Z7_ITEM "


    If Select('TMPOPE') <> 0
        TMPOPE->(dbCloseArea())
    Endif

    TCQuery cSql Alias TMPOPE New
    While TMPOPE->(!eof())
        nTot :=0
        nAliqOpe := 0
        cCodIte := padr( TMPOPE->Z7_CAMPO,nTamPrd)
        cDescTmp := padr( TMPOPE->Z7_DESCCMP,nTaMZ9DESC)
        if alltrim(TMPOPE->Z7_CAMPO) $ "000008"
            nAliqOpe := 0
            nTot :=  &(TMPOPE->Z7_FORMULA)
        elseIF !Empty(TMPOPE->Z7_FORMULA)

            nAliqOpe := &(TMPOPE->Z7_FORMULA)

        endif
        if alltrim(TMPOPE->Z7_CAMPO) $ "000001_000002_000003" // custo fixo E FRETE em cima do somatorio
            if alltrim(TMPOPE->Z7_CAMPO) $ "000003"
                nTot :=(nTotMP+nTotINV) *(nAliqOpe/100) // Incluindo Investimento/Ferramental

            else
                nTot :=(nTotMP+nTotMOD+nTotINV) *(nAliqOpe/100) // Incluindo Investimento/Ferramental
            endif
        ELSEIF alltrim(TMPOPE->Z7_CAMPO) $ "000004_000005" // custo fixo em cima do somatorio
            nTot :=(nPVVenda) *(nAliqOpe/100)
        ENDIF

        if !Empty(TMPOPE->Z7_LOGINC) .AND. nAliqOpe > 0
            &(TMPOPE->Z7_LOGINC) := nAliqOpe
        ENDIF

        IF oModelSZ93:NLINE == 1
            oModelSZ93:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ93:SETVALUE("Z9_IDFLD",cBox3)
            //    oModelSZ93:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ93:NLINE,nTmIt))
            //oModelSZ9:SETVALUE("Z9_IDFLD",cBox1)
            oModelSZ93:SETVALUE("Z9_CDPROD",cCodIte)
            oModelSZ93:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ93:SETVALUE("Z9_ALIQ",nAliqOpe)
            oModelSZ93:SETVALUE("Z9_TOTAL",nTot)
            oModelSZ93:AddLine()
        ELSE
            oModelSZ93:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ93:SETVALUE("Z9_IDFLD",cBox3)
            //oModelSZ93:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ93:NLINE,nTmIt))
            //oModelSZ9:SETVALUE("Z9_IDFLD",cBox1)
            oModelSZ93:SETVALUE("Z9_CDPROD",cCodIte)
            oModelSZ93:SETVALUE("Z9_DESC",cDescTmp)
            oModelSZ93:SETVALUE("Z9_ALIQ",nAliqOpe)
            oModelSZ93:SETVALUE("Z9_TOTAL",nTot)
            oModelSZ93:AddLine()

        ENDIF

        TMPOPE->(dbskip())
    Enddo
    oModelSZ93:DeleteLine()
    TMPOPE->(dbCloseArea())

    fProcCusMp()

Return */
//USER  Function fPrcDados()
USER  Function D02fPDados()

    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8  := NIL
    Local oModelSZ91 := NIL
    Local oModelSZ92 := NIL
    Local oModelSZ93 := NIL
    lOCAL cIdSZ7     := NIL
    lOCAL cCodPro    := NIL
    lOCAL lSb1 := .f.
    lOCAL lSX5 := .f.
    Local cProdGrid :=""

    Private aTPPrd   := {}

    IF oModel!= Nil
        oModelSZ8  := oModel:GetModel("SZ8MASTER")
        oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
        oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
        oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
        cIdSZ7     := oModelSZ8:GETVALUE("Z8_IDSZ7")
        cCodPro    := oModelSZ8:getvalue("Z8_COD")

        lVldCpos := .t.
        oModelSZ91:GoLine(1)
        cProdGrid := oModelSZ91:GETVALUE("Z9_CDPROD")
        DBSELECTAREA("SB1")
        SB1->(dbSetOrder(1))
        IF    SB1->(MsSeek(xFilial("SB1")+cCodPro))
            lSb1 := .t.
        ENDIF
        DBSELECTAREA("SZ7")
        SZ7->(dbSetOrder(1))
        IF    SZ7->(MsSeek(xFilial("SZ7")+cIdSZ7))
            lSX5 := .t.
        ENDIF

        if( Empty(cCodPro) .or. Empty(cIdSZ7))
            msgstop("Parametros Invalidos - Dados em Branco")
            Return
        endif

        if !(  lSX5 .or. lSb1)
            msgstop("Parametros Invalidos - Dados Invalidos")
            Return
        endif

        if empty(oModelSZ8:getvalue("Z8_CDTABVN"))
            MsgAlert("Tabela de Preco de Venda em Branco, gentileza revisar e reprocessar o calculo")
        endif
        
        if oModelSZ91:Length() <= 1
            lCanAlt := .T.
            fPrcClear()
            FWMsgRun(, {|| fPrcEst() } , "Delpi", "Processando - Estrutura...")
            FWMsgRun(, {|| fPrcOpe2() } , "Delpi", "Processando - Operacional...")
            FWMsgRun(, {|| fPrcImp2() } , "Delpi", "Processando - Impostos...")
            FWMsgRun(, {|| fRPrc01() }, "Delpi", "Recalculando Coeficiente...")
            FWMsgRun(, {|| fPrcEst2() }, "Delpi", "Coeficiente Estrutura...")
            FWMsgRun(, {|| fPrcEst3() }, "Delpi", "Coeficiente Estrutura...")
            FWMsgRun(, {|| fRPrc02() }, "Delpi", "Recalculando Coeficiente...")
            FWMsgRun(, {|| fPrcRecal() }, "Delpi", "Recalculando Valores...") // ? ADICIONADO!
            FWMsgRun(, {|| fSetPVen() }, "Delpi", "Preco de Venda...")
            FWMsgRun(, {|| fPrcPPart() }, "Delpi", "Processando a Percentual de Participacao...")
            lCanAlt := .f.
            
        ELSEIF !eMPTY(cProdGrid) .AND. cProdGrid != cCodPro
            lCanAlt := .T.
            fPrcClear()
            FWMsgRun(, {|| fPrcEst() }  , "Delpi", "Processando -  Estrutura...")
            FWMsgRun(, {|| fPrcOpe2() } , "Delpi", "Processando - Operacional...")
            FWMsgRun(, {|| fPrcImp2() } , "Delpi", "Processando - Impostos...")
            FWMsgRun(, {|| fRPrc01() }  , "Delpi", "Recalculando Coeficiente...")
            FWMsgRun(, {|| fPrcEst2() } , "Delpi", "Coeficiente Estrutura...")
            FWMsgRun(, {|| fPrcEst3() } , "Delpi", "Coeficiente Estrutura...")
            FWMsgRun(, {|| fRPrc02() }  , "Delpi", "Recalculando Coeficiente...")
            FWMsgRun(, {|| fPrcRecal() }, "Delpi", "Recalculando Valores...") // ? ADICIONADO!
            FWMsgRun(, {|| fSetPVen() } , "Delpi", "Preco de Venda...")
            FWMsgRun(, {|| fPrcPPart() }, "Delpi", "Processando a Percentual de Participacao...")
            lCanAlt := .f.
        else
            lCanAlt := .t.
            lRecal := .t.
            FWMsgRun(, {|| fRPrc01() }, "Delpi", "Recalculando Coeficiente...")
            FWMsgRun(, {|| fPrcEst2() }, "Delpi", "Coeficiente Estrutura...")
            FWMsgRun(, {|| fPrcEst3() }, "Delpi", "Coeficiente Estrutura...")
            FWMsgRun(, {|| fRPrc02() }, "Delpi", "Recalculando Coeficiente...")
            FWMsgRun(, {|| fPrcRecal() }, "Delpi", "Recalculando Valores...") // ? ADICIONADO!
            FWMsgRun(, {|| fSetPVen() } , "Delpi", "Preco de Venda...")
            FWMsgRun(, {|| fPrcPPart() }, "Delpi", "Processando a Percentual de Participacao...")
            lCanAlt := .f.
        endif

        oModelSZ91:GoLine(1)
        oModelSZ92:GoLine(1)
        oModelSZ93:GoLine(1)
        If ValType( oView ) != "U" .AND. !lAUTO
            oView:Refresh("SZ9DETAIL01")
            oView:Refresh("SZ9DETAIL02")
            oView:Refresh("SZ9DETAIL03")
            oView:Refresh("SZ8MASTER")
        endif

    ELSE
        MSGSTOP("Opção não disponivel","Delpi")
    ENDIF
Return
Static Function fPrcEst()

    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8 := oModel:GetModel("SZ8MASTER")
    Local oModelSZ9 := oModel:GetModel("SZ9DETAIL01")
    Local cCodPro   := ""
    Local aEstru    := {}
    Local aSG2 :={}
    Local nTamPrd   := GetSx3cache("B1_COD","X3_TAMANHO")
    Local nTaMZ9DESC   := GetSx3cache("Z9_DESC","X3_TAMANHO")
    Local cTpProd := ""
    Local aPI :={}
    Local nPosPIAtu := 1
    Local nPosPIOld := 1
    lOCAL cIdSZ8 := oModelSZ8:GETVALUE("Z8_ID")
    lOCAL cIdSZ7 := oModelSZ8:GETVALUE("Z8_IDSZ7")
    lOCAL cTmpSet := oModelSZ8:GETVALUE("Z8_TMPSET")
    //Local nTotMP  := 0 // Variavel que totaliza a Materia Prima
    //Local nTotMOD := 0 // Variavel que totaliza a Mao de Obra
    //Local nTotBen := 0 // Variavel que totaliza a Beneficiamento
    //Local nTotGG := 0 // Variavel que totaliza Gastos Gerais
    //   Local nQtdBas := 2 // Variavel Quantidade Basica
    Local nTotUnit  := 0
    Local NTOTESTR  := 0
    Local nG2       := 0
    Local n1        := 0
    lOCAL aTpProd   := {}
    Private nEstru 	:= 0

    aPrdQtBas := {}
    //oModel:GetValue( 'ZA1MASTER', 'ZA1_MUSICA )

    IF  oModelSZ9:Length() > 1

        oModelSZ9:GoLine(1)
        nQtdBas   :=    oModelSZ9:GETVALUE("Z9_QUANT")

    ELSE

        nQtdBas   := 1

    ENDIF


    nTotMP   := 0
    nTotMOD  := 0
    nTotBen  := 0
    nTotGG   := 0
    nTotINV  := 0 // Inicializa total de investimento/ferramental
    nTotUnit := 0
    cCodPro  := padr( oModelSZ8:getvalue("Z8_COD"),nTamPrd)
    cTpProd  := POSICIONE("SB1",1,XFILIAL("SB1")+cCodPro,"B1_TIPO")
    cDescTmp := padr(ALLTRIM(POSICIONE("SB1",1,XFILIAL("SB1")+cCodPro,"B1_DESC")),nTaMZ9DESC)
    aEstru   := Estrut(cCodPro)
    //dbSelectArea("SZ7")
    //SZ7->(dbSetOrder(2))

    //If   SZ7->(dBSeek(xFilial("SZ7")+cIdSZ7))
    //    lCanAlt := .t.
    //    oModelSZ8:SETVALUE("Z8_FATMP",SZ7->Z7_FATMP)
    //    lCanAlt := .f.
    //ENDIF

    conout("gda")
    //preenche dados da primeira linha
    oModelSZ9:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
    oModelSZ9:SETVALUE("Z9_IDZ8",cIdSZ8)
    oModelSZ9:SETVALUE("Z9_IDFLD",cBox3)
    IF lAuto
        oModelSZ9:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ9:NLINE,nTmIt))
    ENDIF
    oModelSZ9:SETVALUE("Z9_CDPROD",cCodPro)
    oModelSZ9:SETVALUE("Z9_DESC",cDescTmp)
    oModelSZ9:SETVALUE("Z9_QUANT",nQtdBas)
    nQtdEst ++



    // Calcula Mao de Obra
    //a Estrutura mao de obra tem que ser depois do item principal
    IF ALLTRIM(cCodPro) $ "50225199"
        conout("stop")
    endif
    aSG2 :=  fGetMOD(cCodPro)
    For nG2 := 1 to Len(aSG2)
        oModelSZ9:AddLine()
        nQtdEst ++
        // Calcula valores Totais e Unitarios conforme quantidade basica
        nTSG2Qtd  :=  aSG2[nG2][3] * nQtdBas
        //     nTSG2VUni :=  aSG2[nG2][4] * nQtdBas

        IF aSG2[nG2][6] <=1
            nTSG2VUni :=  aSG2[nG2][4] * nQtdBas
        ELSE
            nTSG2VUni := ( aSG2[nG2][4] * nQtdBas)/aSG2[nG2][6]
        ENDIF
        if cTmpSet !='1'


            nTSG2Qtd  +=  (aSG2[nG2][5] ) * nQtdBas

            //  nTmp := (  aSG2[nG2][4]*aSG2[nG2][5] )
            //  nTmp := nTmp  * nQtdBas
            //  nTSG2VUni +=  nTmp
        endif
        nTSG2Tot  :=  nTSG2Qtd * nTSG2VUni
        nTotMOD   += nTSG2Tot
        oModelSZ9:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
        oModelSZ9:SETVALUE("Z9_IDZ8",cIdSZ8)
        oModelSZ9:SETVALUE("Z9_IDFLD",cBox1)
        IF lAuto
            oModelSZ9:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ9:NLINE,nTmIt))
        ENDIF
        oModelSZ9:SETVALUE("Z9_CDPROD",aSG2[nG2][1])
        //oModelSZ9:SETVALUE("Z9_DESC",aSG2[nG2][2])
        oModelSZ9:SETVALUE("Z9_DESC",Padr(ALLTRIM( aSG2[nG2][2]),nTaMZ9DESC))
        oModelSZ9:SETVALUE("Z9_QUANT",  nTSG2Qtd )
        oModelSZ9:SETVALUE("Z9_VUNIT",  nTSG2VUni)
        oModelSZ9:SETVALUE("Z9_TOTAL",  nTSG2Tot )
        //  fSetQtbas(aSG2[nG2][1],nTSG2Qtd,nTSG2VUni)
    Next nG2

    nPosQtd:= 4
    conout("antes")

    For n1 := 1 to Len(aEstru)

        cCodTmp   := padr( aEstru[n1][3],nTamPrd)
        cTpProd   := POSICIONE("SB1",1,XFILIAL("SB1")+cCodTmp,"B1_TIPO")
        cDescTmp  := padr(ALLTRIM(POSICIONE("SB1",1,XFILIAL("SB1")+cCodTmp,"B1_DESC")),nTaMZ9DESC)
        nPosPIAtu := n1
        
        // Debug: rastrear todos os produtos processados
        ConOut(">>> PROCESSANDO PRODUTO: " + cCodTmp + " | Tipo: " + cTpProd + " | Desc: " + AllTrim(cDescTmp))

        if cTpProd $"PI" .AND. nPosPIAtu != nPosPIOld
            nPosPIOld := nPosPIAtu
            AADD(aPI,{nPosPIAtu-1,cCodTmp,0} )//Posicao | CodProduto | Valor
        ENDIF
        /*GDA - posiciono na sZ7 para buscar o valor dos campos*/
        dbSelectArea("SZ7")
        SZ7->(dbSetOrder(2))

        If   SZ7->(dBSeek(xFilial("SZ7")+cIdSZ7))
            lCalPCOF := IIF(   SZ7->Z7_PISCFMP == 'N',.F.,.T.)
            lCalICMS := IIF(   SZ7->Z7_ICMSMP == 'N',.F.,.T.)
        else
            lCalPCOF := .f.
            lCalICMS := .f.
        ENDIF

        //  lCalPCOF := .f.
        //  lCalICMS := .f.
        DBSELECTAREA("SBZ")
        SBZ->(dbSetOrder(1))



        IF 	SBZ->(MsSeek(xFilial("SBZ")+cCodTmp)) .and. lCalICMS
            nAliqICM :=SBZ->BZ_PICM
        ELSE
            nAliqICM:=0
        endif
        nTSG2Qtd  :=  aEstru[n1][nPosQtd] * nQtdBas
        aRet:=  fGetPrc(cCodTmp,cTpProd) //nVlrCus
        nTSG2VUni := aRet[1]
        cCodTab := aRet[3]
        cObs := PADR(ALLTRIM(aRet[2]),GETSX3CACHE("Z9_OBS","X3_TAMANHO") )
        nTSG2Tot  :=  nTSG2Qtd * nTSG2VUni
        nQtdEst ++
        oModelSZ9:AddLine()
        oModelSZ9:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
        oModelSZ9:SETVALUE("Z9_IDZ8",cIdSZ8)
        oModelSZ9:SETVALUE("Z9_IDFLD",cBox1)
        IF lAuto
            oModelSZ9:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ9:NLINE,nTmIt))
        endif
        oModelSZ9:SETVALUE("Z9_CDPROD", cCodTmp  )
        oModelSZ9:SETVALUE("Z9_DESC",cDescTmp)
        oModelSZ9:SETVALUE("Z9_QUANT",nTSG2Qtd)
        oModelSZ9:SETVALUE("Z9_VUNIT",nTSG2VUni)
        oModelSZ9:SETVALUE("Z9_ALIQ",nAliqICM)
        oModelSZ9:SETVALUE("Z9_TOTAL",nTSG2Tot)
        oModelSZ9:SETVALUE("Z9_OBS",cObs)
        oModelSZ9:SETVALUE("Z9_TABPRCC",cCodTab)
        fSetQtbas(cCodTmp,nTSG2Qtd,nTSG2VUni)
        nQtBasSG2 := nTSG2Qtd
        if len(aPI)>0
            aPI[len(aPI)][3]+=((nTSG2VUni*aEstru[n1][nPosQtd]) *nQtdBas)
        endif
        
        ConOut(">>> VERIFICACAO TIPO: " + cCodTmp + " | Tipo: " + cTpProd + " | Total: " + cValToChar(nTSG2Tot))

        if cTpProd $ "MP"

            //nTotMP += nVlrCus*aEstru[n1][nPosQtd]

            nTotMP += nTSG2Tot
            ConOut(">>> SOMADO EM MATERIA PRIMA: " + cValToChar(nTotMP))
        ELSEIF cTpProd $ "BN|BE" // Beneficiamento
            nTotBen += nTSG2Tot
            ConOut(">>> SOMADO EM BENEFICIAMENTO: " + cCodTmp + " | Tipo: " + cTpProd + " | Valor: " + cValToChar(nTSG2Tot) + " | Total Acum: " + cValToChar(nTotBen))
        ELSEIF cTpProd $ "GG|MC|II" // Gastos Gerais, Material de Consumo ou tipo II (mini aplicador)
            nTotGG += nTSG2Tot
            ConOut(">>> SOMADO EM GASTOS GERAIS: " + cCodTmp + " | Tipo: " + cTpProd + " | Valor: " + cValToChar(nTSG2Tot) + " | Total Acum: " + cValToChar(nTotGG))
        ELSEIF cTpProd $ "FE|IN" // Ferramental ou Investimento (removido II daqui)
            nTotINV += nTSG2Tot
            ConOut(">>> FERRAMENTAL IDENTIFICADO: " + cCodTmp + " | Tipo: " + cTpProd + " | Valor: " + cValToChar(nTSG2Tot) + " | Total Acum: " + cValToChar(nTotINV))
        ELSE
            ConOut(">>> NAO SOMADO (TIPO NAO RECONHECIDO): " + cCodTmp + " | Tipo: " + cTpProd)
        ENDIF
        IF ALLTRIM(cCodTmp) $ "50225199"
            conout("stop")
        endif
        //a Estrutura mao de obra tem que ser depois do item principal
        aSG2 :=  fGetMOD(cCodTmp)
        nPos  :=  ascan(aPrdQtBas,{|x| Trim(x[1]) $ alltrim(cCodTmp) })
        For nG2 := 1 to Len(aSG2)

            //  nTSG2Qtd  :=  aSG2[nG2][3] * nQtdBas
            //  nTSG2VUni :=  aSG2[nG2][4]// fGetPrc(aSG2[nG2][1],cTpProd)  //aSG2[nG2][4]
            /*11/2023 - Esse trecho é para trata a quantidade Base que era superior a 1 nos produtos do tipo PI*/
            if nPos == 0
                nTSG2Qtd  :=  aSG2[nG2][3] * nQtdBas
            else
                nTSG2Qtd  :=  aSG2[nG2][3] * nQtBasSG2
            endif

            IF aSG2[nG2][6] <=1
                nTSG2VUni :=  aSG2[nG2][4] * nQtdBas
            ELSE
                nTSG2VUni := ( aSG2[nG2][4] * nQtdBas)/aSG2[nG2][6]
            ENDIF
            if cTmpSet !='1'


                nTSG2Qtd  +=  (aSG2[nG2][5] ) * nQtdBas
                //nTmp := (  aSG2[nG2][4]*aSG2[nG2][5] )
                //nTmp := nTmp  * nQtdBas
                //nTSG2VUni +=  nTmp

            endif

            nTSG2Tot  :=  nTSG2Qtd * nTSG2VUni
            nTotMOD   += nTSG2Tot
            nQtdEst ++
            oModelSZ9:AddLine()
            oModelSZ9:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
            oModelSZ9:SETVALUE("Z9_IDZ8",cIdSZ8)
            oModelSZ9:SETVALUE("Z9_IDFLD",cBox1)
            IF lAuto
                oModelSZ9:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ9:NLINE,nTmIt))
            endif
            oModelSZ9:SETVALUE("Z9_CDPROD",aSG2[nG2][1])
            //oModelSZ9:SETVALUE("Z9_DESC",aSG2[nG2][2])
            oModelSZ9:SETVALUE("Z9_DESC",Padr(ALLTRIM( aSG2[nG2][2]),nTaMZ9DESC))
            oModelSZ9:SETVALUE("Z9_QUANT", nTSG2Qtd )
            oModelSZ9:SETVALUE("Z9_VUNIT", nTSG2VUni)
            oModelSZ9:SETVALUE("Z9_TOTAL", nTSG2Tot )
            //aPI[len(aPI)][3]+=((nTSG2VUni*aEstru[n1][nPosQtd]) *nQtdBas)
            if len(aPI)>0
                aPI[len(aPI)][3]+=(nTSG2Tot)
            ENDIF
            fSetQtbas(aSG2[nG2][1],nTSG2Qtd,nTSG2VUni)
            //    aPI[len(aPI)][3]+=(nVlrCus*aEstru[n1][nPosQtd])
        Next nG2
    Next n1

    ConOut(">>> TOTAIS CALCULADOS - MP: " + cValToChar(nTotMP) + " | MOD: " + cValToChar(nTotMOD) + " | BEN: " + cValToChar(nTotBen) + " | GG: " + cValToChar(nTotGG) + " | INV: " + cValToChar(nTotINV))

    cSql :="SELECT * FROM dbo." + retsqlname("SZ7") + " SZ7 " + cEol
    cSql +="WHERE D_E_L_E_T_='' AND Z7_ID = " + VALTOSQL(cIdSZ7) + " AND Z7_FOLDER='1PRD01' " + cEol
    cSql +="ORDER BY Z7_ITEM "


    If Select('TMPEST') <> 0
        TMPEST->(dbCloseArea())
    Endif

    TCQuery cSql Alias TMPEST New
    While TMPEST->(!eof())

        nZ9Tot := 0
        cCodIte := padr( TMPEST->Z7_CAMPO,nTamPrd)
        cDescTmp := padr( TMPEST->Z7_DESCCMP,nTaMZ9DESC)
        
        // Atribui o valor calculado conforme o código da linha
        If AllTrim(TMPEST->Z7_CAMPO) == "000001" // Total de Matéria Prima
            nZ9Tot := nTotMP
            ConOut(">>> LINHA 000001 - TOTAL MP: " + cValToChar(nTotMP))
        ElseIf AllTrim(TMPEST->Z7_CAMPO) == "000002" // Total de Mão de Obra
            nZ9Tot := nTotMOD
            ConOut(">>> LINHA 000002 - TOTAL MOD: " + cValToChar(nTotMOD))
        ElseIf AllTrim(TMPEST->Z7_CAMPO) == "000003" // Total de Beneficiamento
            nZ9Tot := nTotBen
            ConOut(">>> LINHA 000003 - TOTAL BEN: " + cValToChar(nTotBen))
        ElseIf AllTrim(TMPEST->Z7_CAMPO) == "000004" // Total de Gastos Gerais
            nZ9Tot := nTotGG
            ConOut(">>> LINHA 000004 - TOTAL GG: " + cValToChar(nTotGG))
        ElseIf AllTrim(TMPEST->Z7_CAMPO) == "000009" // Total de Investimento/Ferramental
            nZ9Tot := nTotINV
            ConOut(">>> LINHA 000009 - TOTAL INV: " + cValToChar(nTotINV))
        Else
            nZ9Tot := TMPEST->Z7_VLRINI
        EndIf

        /* IF !Empty(TMPEST->Z7_FORMULA)

            nZ9Tot := &(TMPEST->Z7_FORMULA)

        endif
        if !Empty(TMPEST->Z7_LOGINC) .AND. nZ9Tot > 0
            &(TMPEST->Z7_LOGINC) := nZ9Tot
        ENDIF*/
        oModelSZ9:AddLine()
        oModelSZ9:SETVALUE("Z9_FILMOV",XFILIAL("SZ8"))
        oModelSZ9:SETVALUE("Z9_IDZ8",cIdSZ8)
        oModelSZ9:SETVALUE("Z9_IDFLD",cBox1)
        if lAuto
            oModelSZ9:SETVALUE("Z9_ITEM",  STRZERO(oModelSZ9:NLINE,nTmIt))
        endif
        //oModelSZ9:SETVALUE("Z9_IDFLD",cBox1)
        oModelSZ9:SETVALUE("Z9_CDPROD",cCodIte)
        oModelSZ9:SETVALUE("Z9_DESC",cDescTmp)
        oModelSZ9:SETVALUE("Z9_QUANT",1)
        oModelSZ9:SETVALUE("Z9_TOTAL",nZ9Tot)

        TMPEST->(dbskip())

    Enddo

    TMPEST->(dbCloseArea())
    oModelSZ9:GoLine(1)
    //  oModelSZ9:SETVALUE("Z9_TOTAL",nZ9Tot)
    //  oModelSZ9:SETVALUE("Z9_QUANT",nQtdBas)
    //  oModelSZ9:SETVALUE("Z9_VUNIT",nZ9Tot)
    //If Type( 'oView' ) != "U"
    If ValType( oView ) != "U" .and. !lAuto
        oView:Refresh("SZ9DETAIL01")
    endif
Return


/*/{Protheus.doc} fGetMOD

    Função para retornar o custo de mao de obra
    e adicionar no Grid Principal
/*/


Static Function fGetMOD(cCodProd)

    Local cSql := ""
    lOCAL aRet :={}

    cSql+="SELECT 'MOD'+LTRIM(RTRIM(SH1.H1_CCUSTO))[CODPROD],LTRIM(RTRIM(SG2.G2_RECURSO))+' '+LTRIM(RTRIM(SG2.G2_DESCRI)) [DESC],G2_TEMPAD, ISNULL(SBZ.BZ_CUSTD,0.00) BZ_CUSTD ,G2_SETUP, H1_MODFAT H1_MAOOBRA" + cEol
    cSql+="FROM dbo." + retsqlname("SG2") + " SG2(NOLOCK)" + cEol
    cSql+="     JOIN dbo." + retsqlname("SH1") + " SH1(NOLOCK)ON SH1.D_E_L_E_T_=''" + cEol
    cSql+="                                   AND SG2.G2_FILIAL=SH1.H1_FILIAL" + cEol
    cSql+="                                   AND SG2.G2_RECURSO=SH1.H1_CODIGO" + cEol
    cSql+="    LEFT JOIN dbo." + retsqlname("SBZ") + " SBZ(NOLOCK)ON SBZ.D_E_L_E_T_=''" + cEol
    cSql+="                                   AND SG2.G2_FILIAL=SBZ.BZ_FILIAL" + cEol
    cSql+="                                   AND SBZ.BZ_COD='MOD'+LTRIM(RTRIM(SH1.H1_CCUSTO))" + cEol
    cSql+="WHERE SG2.D_E_L_E_T_='' AND SG2.G2_PRODUTO=" +valtosql(cCodProd) + cEol
    cSql+="AND SG2.G2_FILIAL   = " +VALTOSQL(XFILIAL("SG2"))+ cEol
    cSql+="AND SG2.G2_CODIGO   = " +VALTOSQL("01")+ cEol
    cSql+="AND SG2.G2_ZFRMPRC !=  'N' " + cEol

    cSql+="ORDER BY 1  "
    If Select('TMPSG2') <> 0
        TMPSG2->(dbCloseArea())
    Endif

    TCQuery cSql Alias TMPSG2 New
    While TMPSG2->(!eof())
        aRetCD5 := fVldCD5(TMPSG2->CODPROD)
        nVlrCus := 0.00
        if aRetCD5[1]
            nVlrCus :=aRetCD5[2]
        else
            nVlrCus :=TMPSG2->BZ_CUSTD
        endif
        //H1_MODFAT
        AADD(aRet,{TMPSG2->CODPROD,TMPSG2->DESC,TMPSG2->G2_TEMPAD,nVlrCus ;
            ,TMPSG2->G2_SETUP,TMPSG2->H1_MAOOBRA})

        TMPSG2->(dbskip())
    Enddo

    TMPSG2->(dbCloseArea())
Return aRet


Static Function fVldCD5(cPrdCD5)
    Local cSql := ""
    Local lRet := .f.
    lOCAL nRet := 0.00

    /// dbo." + retsqlname("SBZ") + "
    cSql +="SELECT COUNT(*) CD5_VTRANS " + cEol
    cSql +="FROM  dbo." + retsqlname("SD1") + "  (NOLOCK) SD1 " + cEol
    cSql +="     JOIN  dbo." + retsqlname("CD5") + "  CD5 (NOLOCK) " + cEol
    cSql +="        ON CD5.D_E_L_E_T_ = '' " + cEol
    cSql +="           AND CD5_FILIAL = D1_FILIAL " + cEol
    cSql +="           AND CD5_DOC = D1_DOC " + cEol
    cSql +="           AND CD5_SERIE = D1_SERIE " + cEol
    cSql +="           AND CD5_FORNEC = D1_FORNECE " + cEol
    cSql +="           AND CD5_LOJA = D1_LOJA  " + cEol
    cSql +="           AND CD5_ITEM = D1_ITEM " + cEol
    cSql +="           AND CD5_VTRANS = '11' " + cEol
    cSql +="WHERE SD1.D_E_L_E_T_ = '' " + cEol
    cSql +="      AND D1_COD   = "+valtosql(cPrdCD5) + cEol

    If Select('TMPCD5') <> 0
        TMPCD5->(dbCloseArea())
    Endif

    TCQuery cSql Alias TMPCD5 New
    IF TMPCD5->CD5_VTRANS>0
        lRet := .t.
        nRet:=  MTGetVProd(cPrdCD5)

    Endif
Return {lRet,nRet}

/*/{Protheus.doc} fGetPrc

  Retornar o Valor do Produto conforme tabela de Preco de Fornecedor
  Para Produtos do Tipo Mao de Obra - MO, o calculo é feito na funcao  fGetMOD
  Faz um select na AIB conforme produto e retorna o menor Preco, regra definida pela Joici
/*/

Static Function fGetPrc(cCodPro,cTpProd)
    Local nPrc := 0
    lOCAL cSql:=""
    Local cTabCom := "   "
    Local cCodTab := "   "
    CONOUT(cSql)

    /* IF alltrim(cCodPro) $ "10420048"
        msgstop("achou")
    endif*/
    IF cTpProd != "MO"


        // cSql:="SELECT LTRIM(RTRIM(AIB.AIB_CODTAB)) +' '+LTRIM(RTRIM(A2_COD    ))+'/'+LTRIM(RTRIM(A2_LOJA	  ))+' '+LTRIM(RTRIM(A2_NREDUZ )) DESCTAB, " + cEol
        cSql:="SELECT AIB.AIB_CODTAB AIB_CODTAB,LTRIM(RTRIM(A2_COD    ))+'/'+LTRIM(RTRIM(A2_LOJA	  ))+' '+LTRIM(RTRIM(A2_NREDUZ )) DESCTAB, " + cEol
        cSql+=" MIN(AIB_PRCCOM) AIB_PRCCOM,MAX(AIB_DATVIG)AIB_DATVIG " + cEol
        cSql+="FROM dbo." + retsqlname("AIB") + "  AIB(NOLOCK) " + cEol
        cSql+=" JOIN dbo." + retsqlname("AIA") + " AIA (NOLOCK) ON AIA.D_E_L_E_T_= ''
        cSql+="AND AIB.AIB_FILIAL = AIA.AIA_FILIAL " + cEol
        cSql+="AND AIB.AIB_CODTAB = AIA.AIA_CODTAB " + cEol
        cSql+=" AND AIB_CODFOR = AIA_CODFOR " + cEol
        cSql+=" AND AIB_LOJFOR = AIA_LOJFOR " + cEol
        cSql+=" JOIN dbo." + retsqlname("SA2") + " SA2 (NOLOCK)ON SA2.D_E_L_E_T_= '' AND   " + cEol
        cSql+="     SA2.A2_FILIAL= '' AND AIB.AIB_CODFOR = SA2.A2_COD  " + cEol
        cSql+="     AND AIB.AIB_LOJFOR = SA2.A2_LOJA  " + cEol
        cSql+="WHERE AIB.D_E_L_E_T_='' AND AIB.AIB_FILIAL=" +valtosql(xfilial("AIB")) + cEol
        cSql+="      AND AIB_DATVIG != ''  " + cEol
        cSql+="      AND AIB.AIB_CODPRO =" +valtosql(cCodPro) + cEol
        cSql+="      AND RTRIM(CONVERT(VARCHAR(10), GETDATE(), 112)) BETWEEN  AIA_DATDE AND " + cEol
        cSql+="                 CASE WHEN AIA_DATATE ='' THEN '20491231' ELSE AIA_DATATE END " + cEol
        cSql+="GROUP BY AIB_CODTAB,A2_COD,A2_LOJA,A2_NREDUZ"

        CONOUT(cSql)

        If Select('TMPPRC') <> 0
            TMPPRC->(dbCloseArea())
        Endif
        aRetCD5 := fVldCD5(cCodPro)
        TCQuery cSql Alias TMPPRC New
        if  TMPPRC->(!eof())
            IF aRetCD5[1]
                nPrc := aRetCD5[2]
            ELSE
                nPrc := TMPPRC->AIB_PRCCOM
            ENDIF
            cTabCom := TMPPRC->DESCTAB
            cCodTab :=  TMPPRC->AIB_CODTAB
        endif
    ELSE
        nPrc := POSICIONE("SB1",1,XFILIAL("SB1")+cCodPro,"B1_CUSTOD")
    ENDIF
    TMPPRC->(dbCloseArea())
Return {nPrc,cTabCom,cCodTab }
Static Function Estrut(cProduto,nQuant,lOneLevel,lPreEstru)
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
                /*                                                   ,lTipoDec,cAliasSG1,cAliasSB1,lMRP,cProOpc,,lTipoDec,cAliasSG1,cAliasSB1,lMRP,cProOpc,lVldData,lVlOpc,lProBlq,*/
                nQuantItem:=ExplEstr(nQuant,nil,nil,nil,nil,lPreEstru,/*lTipoDec*/,/*cAliasSG1*/,/*cAliasSB1*/,/*lMRP*/,/*cProOpc*/,/*lVldData*/.T.,.F.)

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
                        /*                                                   ,lTipoDec,cAliasSG1,cAliasSB1,lMRP,cProOpc,lVldData,lVlOpc,lProBlq,lVldRev)*/
                        nQuantItem:=ExplEstr(nQuant,nil,nil,nil,nil,lPreEstru,/*lTipoDec*/,/*cAliasSG1*/,/*cAliasSB1*/,/*lMRP*/,/*cProOpc*/,/*lVldData*/.T.,.F.)
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



Static Function GeraEstr(cCodPrd)

    Local aEstru    := {}
    Local aSG1	    := {}
    Local aLeg	    := {}
    Local cSeqLeg   := 'ABCDEFGHIJKLMNOPQRSTU'
    Local cDescRh   := "- ROHS"
    local i := 0
    Private nEstru 	:= 0

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³	Processando a Sessao 1                                       ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    aEstru := Estrut(cCodPrd)

    If 	!Empty(aEstru)

        nItem:= 0
        nLeg := 0
        aComp:= {}
        if Len(aEstru) >0

            SB1->(DbSeek(xFilial('SB1')+aEstru[1,2]))
            If	SB1->(Found())

                cDescCod :=  STRTRAN( SB1->B1_DESC , cDescRh , space(len(cDescRh) ))

            EndIf

            aAdd(aSG1,{'', aEstru[1,2], cDescCod, '', '', '', ''})

        endif

        For i:=1 to Len(aEstru)

            SG1->(DbSeek(xFilial('SG1')+aEstru[i,2]+aEstru[i,3]))
            If	SG1->(Found())
                If	Dtos(SG1->G1_FIM) < Dtos(dDataBase)
                    Loop
                EndIf
            EndIf

            cCodigo  := aEstru[i,2]
            cDescCod := ''
            cTipo    := ''
            SB1->(DbSeek(xFilial('SB1')+aEstru[i,2]))
            If	SB1->(Found())
                cDescCod :=  STRTRAN( SB1->B1_DESC , cDescRh , space(len(cDescRh) ))
                cTipo    := SB1->B1_TIPO
            EndIf

            cCodComp  := aEstru[i,3]
            cDescComp := ''
            SB1->(DbSeek(xFilial('SB1')+aEstru[i,3]))
            If	SB1->(Found())
                cDescComp := STRTRAN(SB1->B1_DESC,cDescRh,space(len(cDescRh)))
            EndIf

            nQuant := aEstru[i,4]
            If	SB1->B1_UM == 'PC'
                nQuant := aEstru[i,4] / 1000
            EndIf

            If	AllTrim(SB1->B1_UM) == 'MT'
                nQuant := aEstru[i,4] / SG1->G1_QUANT
            EndIf

            If	AllTrim(SB1->B1_UM) == 'KG'
                nQuant := 1
            EndIf

            If	cTipo == 'PA' .And. SB1->B1_TIPO == 'PI' .And. aEstru[i,1] == 1
                Loop
            EndIf

            nAt := aScan(aComp, Str(aEstru[i,1])+cCodigo)
            If	nAt == 0
                aAdd(aComp, Str(aEstru[i,1])+cCodigo)
                nItem++
            Else
                cCodigo := ''
                cDescCod:= ''
            EndIf

            nPos := aScan(aLeg,{|x| x[2] == aEstru[i,3]})
            If	nPos == 0
                nLeg++
                aAdd(aLeg, {Substr(cSeqLeg,nLeg,1), aEstru[i,3]} )
                nPos := Len(aLeg)
            EndIf

            aAdd(aSG1,{AllTrim(Str(nItem)), cCodigo, cDescCod, aLeg[nPos,1], nQuant, cCodComp, cDescComp})

        Next i

    Else
        ApMsgAlert('Não foi encontrado estrutura do produto '+mv_par01+'. Verifique !!!')
    EndIf

Return aSG1
//COEFICIENTE OLD
//Calcula Coeficiente do Markup Operacional
Static FUnction fCoefOper()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local nPosCoef := 0
    Local nPosPVOper := 0
    Local nPosLcOper := 0
    local nI := 0

    nCoefOper := 100
    nLucro := 0
    nLnold := oModelSZ93:NLINE
    For nI := 1 To oModelSZ93:Length()

        conout("stop")
        oModelSZ93:GoLine( nI )
        if ALLTRIM(oModelSZ93:GETVALUE("Z9_CDPROD") )$ "000001_000002_000004_000005"
            nCoefOper -=  oModelSZ93:GETVALUE("Z9_ALIQ")
            if ALLTRIM(oModelSZ93:GETVALUE("Z9_CDPROD") )$ "000005"
                nLucro :=  oModelSZ93:GETVALUE("Z9_ALIQ")
            endif
        elseIF ALLTRIM(oModelSZ93:GETVALUE("Z9_CDPROD") )$ "000006"
            nPosCoef:= NI
        elseif ALLTRIM(oModelSZ93:GETVALUE("Z9_CDPROD") )$ "000007"
            nPosPVOper := NI
        elseif    ALLTRIM(oModelSZ93:GETVALUE("Z9_CDPROD")) $ "000008"
            nPosLcOper:= nI
        endif
    Next
    //Coeficiente
    nCoefOper := nCoefOper/1
    oModelSZ93:GoLine( nPosCoef )
    oModelSZ93:SETVALUE("Z9_ALIQ",nCoefOper)
    //000007	PV OPERACIONAL
    // nPVOper:= ((nTotMP + nTotMOD)/(nCoefOper/100))
    oModelSZ93:GoLine( nPosPVOper )
    oModelSZ93:SETVALUE("Z9_ALIQ",1)
    oModelSZ93:SETVALUE("Z9_TOTAL",nPvOper )
    //000008	LUCRO OPERACIONAL
    nLcrOper := nPvOper*(nLucro/100)
    oModelSZ93:GoLine( nLnold )
    oView:Refresh("SZ9DETAIL03")
    LucroOper := nLcrOper
return nLcrOper


//Calcula Coeficiente do Markup iMPOSTOS
Static FUnction fCoefImp()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local nPosCoef   := 0
    Local nSumCoef   := 0
    local nI := 0

    Local nPosLcOper := 0
    nLcrImp          := 0
    nCoefOper        := 100
    nLucro           := 0
    nLnold           := oModelSZ92:NLINE
    nAliqIRClss      :=0
    For nI := 1 To oModelSZ92:Length()

        oModelSZ92:GoLine( nI )
        if ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD") )$  "000001_000002_000003_000004"

            nSumCoef+=oModelSZ92:GETVALUE("Z9_ALIQ")

        elseif ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD") )$ "000005" // coeficiente imp

            if !lRecal
                nCoefImp :=  oModelSZ92:GETVALUE("Z9_ALIQ")
            else
                oModelSZ92:SETVALUE("Z9_ALIQ",100-nSumCoef)
            endif

            // elseif ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD") )$ "000006" // pv venda

            //  nTmp:= nPvOper/ (nCoefImp/100)
            //  oModelSZ92:SETVALUE("Z9_TOTAL",nTmp)

        elseif ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD") )$ "000007" // IR E CSLL

            nAliqIRClss :=(nPvOper/ (nCoefImp/100))*( oModelSZ92:GETVALUE("Z9_ALIQ") /100)
            oModelSZ92:SETVALUE("Z9_TOTAL",nAliqIRClss)

        elseif    ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) $ "000008" .or. empty( ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) )  // pv venda

            nLcrImp := LucroOper-nAliqIRClss

            if lRecal

                oModelSZ92:SETVALUE("Z9_TOTAL",nLcrImp)

            endif
        endif
    Next

    oModelSZ92:GoLine( nLnold )
    oView:Refresh("SZ9DETAIL02")

return nLcrImp


/*--------------------------------------------------------------------*\
| Func:  CLEARGAMBI -  FUNÇÃO PARA REMOVER AS DELETADAS DE UMA GRID MVC|
\*--------------------------------------------------------------------*/

Static Function CLEARGAMBI(cName)

    Local oModel     := FWModelActive()
    Local oModelCL   := oModel:getModel(cName)
    Local nTamAnt    := oModelCL:Length()
    local nI := 0

    FOR nI := 1 TO oModelCL:Length()
        IF nI != oModelCL:Length()
            oModelCL:GoLine(nI)
            IF oModelCL:IsDeleted()
                oModelCL:LineShift(nI+1, nI )
                oModelCL:GoLine(nI+1)
                oModelCL:DeleteLine(.T.,.T.)
                CLEARGAMBI(cName)
            ENDIF
        ENDIF
    Next

    oModelCL:GoLine(1)

Return .T.

Static Function fPrcRecal()

    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02") // IMPOSTOS
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    lOCAL cIdSZ8     := oModelSZ8:GETVALUE("Z8_ID")
    lOCAL cIdSZ7     := oModelSZ8:GETVALUE("Z8_IDSZ7")
    Local nTaMZ9DESC   := GetSx3cache("Z9_DESC","X3_TAMANHO")
    Local lSbz       := .f.
    Local lSb1       := .f.
    Local nAliq := 0
    Local nAliqTot := 0
    Local nPosPIAtu := 1
    Local nPosPIOld := 1
    Local nTamPrd   := GetSx3cache("B1_COD","X3_TAMANHO")
    Local aSZ901 :={}
    Local nICMS := 0
    local n1 := 0
    local n2 := 0
    local n3 := 0
    local n4 := 0

    Local nTotUnit := 0
    Local NTOTESTR := 0
    Local nTamPrd   := GetSx3cache("B1_COD","X3_TAMANHO")
    Local aAliqImpostos := {}
    Local nVlrCoefImp := 0
    Local cDescImp := ""
    Local nAliqLinha := 0
    Local nDivisor := 0

    aPI      := {}
    nPosQtd  := 4
    nTotMP   := 0
    nTotMOD  := 0
    nTotBen  := 0
    nTotGG   := 0
    nTotINV  := 0 // Inicializa total de investimento/ferramental
    nTotUnit := 0
    nQtdTotal := 0 // Quantidade total para linhas de totalização
    
    // ? Variáveis para somar valores LÍQUIDOS separadamente
    nTotMP_Liq   := 0
    nTotMOD_Liq  := 0
    nTotBen_Liq  := 0
    nTotGG_Liq   := 0
    nTotINV_Liq  := 0


    // PRIMEIRA PASSADA: Acumula valores de itens REAIS (não linhas de totalização)
    For n1 := 1 To oModelSZ9:Length()

        oModelSZ9:GoLine(n1)
        If oModelSZ9:IsDeleted()
            ConOut(">>> RECALC - Linha " + cValToChar(n1) + " - DELETADA (ignorada)")
            Loop
        EndIf
        cCodPro  := AllTrim(oModelSZ9:GETVALUE("Z9_CDPROD"))
        
        // Pula linhas de totalização na primeira passada
        If cCodPro $ "000001|000002|000003|000004|000009"
            Loop
        EndIf
        
        AADD(aSZ901,{    oModelSZ9:GETVALUE("Z9_CDPROD"  ),;
            oModelSZ9:GETVALUE("Z9_QUANT"   ),;
            oModelSZ9:GETVALUE("Z9_VUNIT"   ),;
            oModelSZ9:GETVALUE("Z9_TOTAL"   )})

        cCodPro  := padr( oModelSZ9:GETVALUE("Z9_CDPROD"  ),nTamPrd)
        cTpProd  := POSICIONE("SB1",1,XFILIAL("SB1")+cCodPro,"B1_TIPO")

        nTQtdUni := oModelSZ9:GETVALUE("Z9_QUANT"   )
        nTVlrUni := oModelSZ9:GETVALUE("Z9_VUNIT"   )
        nTTot    := nTQtdUni*nTVlrUni                      // Valor BRUTO
        nTLiq    := oModelSZ9:GETVALUE("Z9_PRCLIQ")        // Valor LÍQUIDO
        
        // Acumula quantidade total
        nQtdTotal += nTQtdUni

        if cTpProd $ "MP"
            nTotMP += nTTot
            nTotMP_Liq += nTLiq  // ? Acumula LÍQUIDO
            ConOut(">>> RECALC MP: " + AllTrim(cCodPro) + " | Qtd: " + cValToChar(nTQtdUni) + " | Bruto: " + cValToChar(nTTot) + " | Liq: " + cValToChar(nTLiq))

        elseif cTpProd $ "MO"
            nTotMOD += nTTot
            nTotMOD_Liq += nTLiq  // ? Acumula LÍQUIDO
            ConOut(">>> RECALC MOD: " + AllTrim(cCodPro) + " | Qtd: " + cValToChar(nTQtdUni) + " | Bruto: " + cValToChar(nTTot) + " | Liq: " + cValToChar(nTLiq))

        ELSEIF cTpProd $ "BN|BE" // Beneficiamento
            nTotBen += nTTot
            nTotBen_Liq += nTLiq  // ? Acumula LÍQUIDO
            ConOut(">>> RECALC BEN: " + AllTrim(cCodPro) + " | Qtd: " + cValToChar(nTQtdUni) + " | Bruto: " + cValToChar(nTTot) + " | Liq: " + cValToChar(nTLiq))

        ELSEIF cTpProd $ "GG|MC|II" // Gastos Gerais, Material de Consumo ou tipo II (mini aplicador)
            nTotGG += nTTot
            nTotGG_Liq += nTLiq  // ? Acumula LÍQUIDO
            ConOut(">>> RECALC GASTOS GERAIS/II: " + AllTrim(cCodPro) + " | Qtd: " + cValToChar(nTQtdUni) + " | Tipo: " + cTpProd + " | Bruto: " + cValToChar(nTTot) + " | Liq: " + cValToChar(nTLiq))

        ELSEIF cTpProd $ "FE|IN" // Ferramental ou Investimento (removido II daqui)
            nTotINV += nTTot
            nTotINV_Liq += nTLiq  // ? Acumula LÍQUIDO
            ConOut(">>> RECALC FERRAMENTAL: " + AllTrim(cCodPro) + " | Qtd: " + cValToChar(nTQtdUni) + " | Tipo: " + cTpProd + " | Bruto: " + cValToChar(nTTot) + " | Liq: " + cValToChar(nTLiq))

        ENDIF

        IF  oModelSZ9:GETVALUE("Z9_ALIQ"  ) > 0
            nICMS +=nTTot* (oModelSZ9:GETVALUE("Z9_ALIQ"  ) /100)
        endif

        // Atualiza o valor total do item real
        oModelSZ9:SETVALUE("Z9_TOTAL"  ,nTTot )
    next n1
    
    // LOG dos totais acumulados
    ConOut("=== TOTAIS RECALC ACUMULADOS ===")
    ConOut(">>> Matéria Prima (000001) - Bruto: " + cValToChar(nTotMP) + " | Liq: " + cValToChar(nTotMP_Liq))
    ConOut(">>> Mão de Obra Direta (000002) - Bruto: " + cValToChar(nTotMOD) + " | Liq: " + cValToChar(nTotMOD_Liq))
    ConOut(">>> Beneficiamento (000003) - Bruto: " + cValToChar(nTotBen) + " | Liq: " + cValToChar(nTotBen_Liq))
    ConOut(">>> Gastos Gerais (000004) - Bruto: " + cValToChar(nTotGG) + " | Liq: " + cValToChar(nTotGG_Liq))
    ConOut(">>> Investimento/Ferramental (000009) - Bruto: " + cValToChar(nTotINV) + " | Liq: " + cValToChar(nTotINV_Liq))
    ConOut(">>> Quantidade Total: " + cValToChar(nQtdTotal))
    ConOut("=================================")
    
    // Calcula o total geral para cálculo de percentuais
    nTotalGeral := nTotMP + nTotMOD + nTotBen + nTotGG + nTotINV
    nTotalGeralLiq := nTotMP_Liq + nTotMOD_Liq + nTotBen_Liq + nTotGG_Liq + nTotINV_Liq
    
    // SEGUNDA PASSADA: Preenche linhas de totalização com valores acumulados
    For n1 := 1 To oModelSZ9:Length()
        oModelSZ9:GoLine(n1)
        If oModelSZ9:IsDeleted()
           Loop
        EndIf
        cCodPro := AllTrim(oModelSZ9:GETVALUE("Z9_CDPROD"))
        
        If cCodPro == "000001" // MP
            oModelSZ9:LoadValue("Z9_QUANT", 1.0000)
            //oModelSZ9:LoadValue("Z9_UNTBRT", nTotMP)
            oModelSZ9:LoadValue("Z9_TOTAL", nTotMP)         // BRUTO
            oModelSZ9:LoadValue("Z9_PRCLIQ", nTotMP_Liq)   // LÍQUIDO (diferente do bruto)
            If nTotalGeralLiq > 0
                oModelSZ9:LoadValue("Z9_PERCENT", Round((nTotMP_Liq / nTotalGeralLiq) * 100, 2))
            Else
                oModelSZ9:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> TOTALIZADOR RECALC 000001 (MP) PREENCHIDO: Qtd=1 | Bruto=" + cValToChar(nTotMP) + " | Liq=" + cValToChar(nTotMP_Liq))
            
        ElseIf cCodPro == "000002" // MOD
            oModelSZ9:LoadValue("Z9_QUANT", 1.0000)
            //oModelSZ9:LoadValue("Z9_UNTBRT", nTotMOD)
            oModelSZ9:LoadValue("Z9_TOTAL", nTotMOD)
            oModelSZ9:LoadValue("Z9_PRCLIQ", nTotMOD_Liq)
            If nTotalGeralLiq > 0
                oModelSZ9:LoadValue("Z9_PERCENT", Round((nTotMOD_Liq / nTotalGeralLiq) * 100, 2))
            Else
                oModelSZ9:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> TOTALIZADOR RECALC 000002 (MOD) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotMOD) + " | Total=" + cValToChar(nTotMOD))
            
        ElseIf cCodPro == "000003" // BEN
            oModelSZ9:LoadValue("Z9_QUANT", 1.0000)
            //oModelSZ9:LoadValue("Z9_UNTBRT", nTotBen)
            oModelSZ9:LoadValue("Z9_TOTAL", nTotBen)
            oModelSZ9:LoadValue("Z9_PRCLIQ", nTotBen_Liq)
            If nTotalGeralLiq > 0
                oModelSZ9:LoadValue("Z9_PERCENT", Round((nTotBen_Liq / nTotalGeralLiq) * 100, 2))
            Else
                oModelSZ9:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> TOTALIZADOR RECALC 000003 (BEN) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotBen) + " | Total=" + cValToChar(nTotBen))
            
        ElseIf cCodPro == "000004" // GG
            oModelSZ9:LoadValue("Z9_QUANT", 1.0000)
            //oModelSZ9:LoadValue("Z9_UNTBRT", nTotGG)
            oModelSZ9:LoadValue("Z9_TOTAL", nTotGG)
            oModelSZ9:LoadValue("Z9_PRCLIQ", nTotGG_Liq)
            If nTotalGeralLiq > 0
                oModelSZ9:LoadValue("Z9_PERCENT", Round((nTotGG_Liq / nTotalGeralLiq) * 100, 2))
            Else
                oModelSZ9:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> TOTALIZADOR RECALC 000004 (GG) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotGG) + " | Total=" + cValToChar(nTotGG))
            
        ElseIf cCodPro == "000009" // INV - Investimento/Ferramental
            oModelSZ9:LoadValue("Z9_QUANT", 1.0000)
            //oModelSZ9:LoadValue("Z9_UNTBRT", nTotINV)
            oModelSZ9:LoadValue("Z9_TOTAL", nTotINV)
            oModelSZ9:LoadValue("Z9_PRCLIQ", nTotINV_Liq)
            If nTotalGeralLiq > 0
                oModelSZ9:LoadValue("Z9_PERCENT", Round((nTotINV_Liq / nTotalGeralLiq) * 100, 2))
            Else
                oModelSZ9:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> TOTALIZADOR RECALC 000009 (INV) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotINV) + " | Total=" + cValToChar(nTotINV))
            
        ElseIf cCodPro == "000006" // Custo total do produto
            // Mantém lógica original - não preenche aqui
        EndIf
    next n1
    
    conout("teste")
    
    // ??? ATUALIZA A LINHA 1 COM OS TRÊS CAMPOS ???
    // Total Bruto = Soma dos valores BRUTOS
    // Preço Líquido = Soma dos valores LÍQUIDOS
    oModelSZ9:GoLine(1)
    nTotalBrutoLinha1 := nTotMP + nTotMOD + nTotBen + nTotGG + nTotINV
    nTotalLiqLinha1   := nTotMP_Liq + nTotMOD_Liq + nTotBen_Liq + nTotGG_Liq + nTotINV_Liq

    oModelSZ9:LoadValue("Z9_VUNIT", nTotalBrutoLinha1)   // Unit Bruto = Soma BRUTOS ?
    oModelSZ9:LoadValue("Z9_TOTAL", nTotalBrutoLinha1)   // Total Bruto = Soma BRUTOS ?
    oModelSZ9:LoadValue("Z9_PRCLIQ", nTotalLiqLinha1)    // Preço Líquido = Soma LÍQUIDOS ???

    ConOut(">>> fPrcRecal - LINHA 1 ATUALIZADA:")
    ConOut("    - Z9_VUNIT (Unit Bruto): " + cValToChar(nTotalBrutoLinha1) + " ?")
    ConOut("    - Z9_TOTAL (Total Bruto): " + cValToChar(nTotalBrutoLinha1) + " ?")
    ConOut("    - Z9_PRCLIQ (Preço Líquido): " + cValToChar(nTotalLiqLinha1) + " ???")
    ConOut("    - Incluindo GG Bruto: " + cValToChar(nTotGG) + " | Liq: " + cValToChar(nTotGG_Liq))
    ConOut("    - Incluindo INV Bruto: " + cValToChar(nTotINV) + " | Liq: " + cValToChar(nTotINV_Liq))
    
    fProcCusMp()
    fPrcPPart()
    fCoefOP()

    ConOut("=== fPrcRecal - PROCESSAMENTO DOS MARK-UPS ===")
    ConOut(">>> ORDEM: 1) Mark-up Operacional (n4)  2) Mark-up Impostos (n2)")

    // =====================================================================
    // PASSO A: PROCESSA MARK-UP OPERACIONAL PRIMEIRO (oModelSZ93)
    // O COEFICIENTE do Operacional precisa estar calculado ANTES de calcular
    // o Mark-up Impostos, pois o Impostos usa o Z9_TOTAL do COEFICIENTE do
    // Operacional como base de cálculo.
    // =====================================================================
    nVlrCoefOper := 0  // Variável para armazenar o Z9_TOTAL do COEFICIENTE Operacional

    For n4 := 1 To oModelSZ93:Length()

        oModelSZ93:GoLine(n4)

        If ALLTRIM(oModelSZ93:GETVALUE("Z9_DESC")) $ "IR"
            nAliq   :=  oModelSZ93:GETVALUE("Z9_ALIQ")
            nVlr    :=  nTotalLiqLinha1 / (nAliq/100)
            oModelSZ93:LoadValue("Z9_TOTAL", 0)
            ConOut(">>> Mark-up Operacional - IR: Aliq=" + cValToChar(nAliq) + "% | Total=0")

        ELSEIF ALLTRIM(oModelSZ93:GETVALUE("Z9_DESC")) $ "CUSTO FIXO"
            nAliq   :=  oModelSZ93:GETVALUE("Z9_ALIQ")
            nVlr    :=  nTotalLiqLinha1 / (nAliq/100)
            oModelSZ93:LoadValue("Z9_TOTAL", 0)
            ConOut(">>> Mark-up Operacional - CUSTO FIXO: Aliq=" + cValToChar(nAliq) + "% | Total=0")

        ELSEIF ALLTRIM(oModelSZ93:GETVALUE("Z9_DESC")) $ "LUCRO"
            nAliq   :=  oModelSZ93:GETVALUE("Z9_ALIQ")
            nVlr    :=  nTotalLiqLinha1 / (nAliq/100)
            oModelSZ93:LoadValue("Z9_TOTAL", 0)
            ConOut(">>> Mark-up Operacional - LUCRO: Aliq=" + cValToChar(nAliq) + "% | Total=0")

        ELSEIF ALLTRIM(oModelSZ93:GETVALUE("Z9_DESC")) $ "COMISSAO"
            nAliq   :=  oModelSZ93:GETVALUE("Z9_ALIQ")
            nVlr    :=  nPVVenda * (nAliq/100)
            oModelSZ93:LoadValue("Z9_TOTAL", nVlr)
            ConOut(">>> Mark-up Operacional - COMISSAO: Aliq=" + cValToChar(nAliq) + "% | Total=" + cValToChar(nVlr))

        ELSEIF ALLTRIM(oModelSZ93:GETVALUE("Z9_DESC")) $ "FRETE"
            nAliq   :=  oModelSZ93:GETVALUE("Z9_ALIQ")
            nVlr    :=  nTotalLiqLinha1 / (nAliq/100)
            oModelSZ93:LoadValue("Z9_TOTAL", 0)
            ConOut(">>> Mark-up Operacional - FRETE: Aliq=" + cValToChar(nAliq) + "% | Total=0")

        ELSEIF ALLTRIM(oModelSZ93:GETVALUE("Z9_DESC")) $ "COEFICIENTE"
            nAliq   :=  oModelSZ93:GETVALUE("Z9_ALIQ")
            If nAliq > 0
                nVlr := nTotalLiqLinha1 / (nAliq / 100)
            Else
                nVlr := 0
            EndIf
            oModelSZ93:LoadValue("Z9_TOTAL", nVlr)
            nVlrCoefOper := nVlr  // Armazena para uso no Mark-up Impostos
            ConOut(">>> Mark-up Operacional - COEFICIENTE: " + cValToChar(nTotalLiqLinha1) + " / (" + cValToChar(nAliq) + "/100) = " + cValToChar(nVlr))
            ConOut(">>> *** nVlrCoefOper ARMAZENADO = " + cValToChar(nVlrCoefOper) + " ***")

        ELSEIF ALLTRIM(oModelSZ93:GETVALUE("Z9_DESC")) $ "PV OPERACIONAL"
            // PV OPERACIONAL = mesmo valor do COEFICIENTE
            oModelSZ93:LoadValue("Z9_TOTAL", nVlrCoefOper)
            ConOut(">>> Mark-up Operacional - PV OPERACIONAL: " + cValToChar(nVlrCoefOper))

        endif

    next n4

    // Chama fSetPOper para recalcular/ajustar o Mark-up Operacional via fórmula
    fSetPOper()
    ConOut(">>> fPrcRecal: fSetPOper() chamado após loop Operacional")

    // Relê o Z9_TOTAL do COEFICIENTE do Operacional após fSetPOper (pode ter sido recalculado)
    For n4 := 1 To oModelSZ93:Length()
        oModelSZ93:GoLine(n4)
        If AllTrim(oModelSZ93:GetValue("Z9_DESC")) $ "COEFICIENTE"
            nVlrCoefOper := oModelSZ93:GetValue("Z9_TOTAL")
            ConOut(">>> nVlrCoefOper ATUALIZADO após fSetPOper = " + cValToChar(nVlrCoefOper))
            Exit
        EndIf
    Next n4

    // =====================================================================
    // PASSO B: PROCESSA MARK-UP IMPOSTOS (oModelSZ92)
    // Agora o Z9_TOTAL do COEFICIENTE do Mark-up Operacional já está calculado
    // e pode ser usado como base para o cálculo do Mark-up Impostos.
    //
    // REGRA DE CÁLCULO SEQUENCIAL DO COEFICIENTE:
    // O valor base (Z9_TOTAL do Mark-up Operacional) é dividido sequencialmente
    // por (100% - Alíquota) de CADA linha de imposto (exceto o COEFICIENTE),
    // na ordem em que aparecem na grid. Exemplo:
    //   Base = 146.577,90  (vem do Mark-up Operacional)
    //   Passo 1: 146.577,90 / (100% - 7,00% ICMS) = 146.577,90 / 0,93 = 157.610,65
    //   Passo 2: 157.610,65 / (100% - 9,25% PIS/COFINS) = 157.610,65 / 0,9075 = 173.675,65
    //   O resultado final (173.675,65) é o COEFICIENTE (Z9_TOTAL da linha 003)
    // =====================================================================
    
    // PASSO B.1: Coleta as alíquotas das linhas de impostos (exceto COEFICIENTE) na ordem
    aAliqImpostos := {}
    For n2 := 1 To oModelSZ92:Length()
        oModelSZ92:GoLine(n2)
        cDescImp := AllTrim(oModelSZ92:GetValue("Z9_DESC"))
        
        // Coleta alíquotas de linhas que NÃO são o COEFICIENTE
        If !(cDescImp $ "COEFICIENTE")
            nAliqLinha := oModelSZ92:GetValue("Z9_ALIQ")
            If nAliqLinha > 0
                aAdd(aAliqImpostos, {cDescImp, nAliqLinha, n2})
                ConOut(">>> Mark-up Impostos - Coletada alíquota: " + cDescImp + " = " + cValToChar(nAliqLinha) + "% (linha " + cValToChar(n2) + ")")
            EndIf
        EndIf
    Next n2
    
    // PASSO B.2: Calcula o COEFICIENTE de forma SEQUENCIAL
    nVlrCoefImp := nVlrCoefOper  // Valor base = Z9_TOTAL do COEFICIENTE do Mark-up Operacional
    ConOut(">>> Mark-up Impostos - CÁLCULO SEQUENCIAL - Base inicial (Mark-up Operacional): " + cValToChar(nVlrCoefImp))
    
    If nVlrCoefImp > 0
        For n2 := 1 To Len(aAliqImpostos)
            cDescPasso := aAliqImpostos[n2][1]
            nAliqPasso := aAliqImpostos[n2][2]
            nVlrAntes  := nVlrCoefImp
            
            // Fórmula: Valor / (100% - Alíquota%) = Valor / ((100 - Aliq) / 100)
            nDivisor := (100 - nAliqPasso) / 100
            If nDivisor > 0
                nVlrCoefImp := nVlrCoefImp / nDivisor
                ConOut(">>> Passo " + cValToChar(n2) + ": " + cValToChar(nVlrAntes) + " / (100% - " + cValToChar(nAliqPasso) + "%) = " + cValToChar(nVlrAntes) + " / " + cValToChar(nDivisor) + " = " + cValToChar(nVlrCoefImp) + " [" + cDescPasso + "]")
            Else
                ConOut(">>> Passo " + cValToChar(n2) + ": ERRO - Divisor zero para " + cDescPasso + " (Aliq=" + cValToChar(nAliqPasso) + "%)")
            EndIf
        Next n2
    Else
        ConOut(">>> Mark-up Impostos - CÁLCULO SEQUENCIAL IGNORADO - Base (nVlrCoefOper) = 0")
    EndIf
    
    ConOut(">>> Mark-up Impostos - COEFICIENTE FINAL CALCULADO: " + cValToChar(nVlrCoefImp))
    
    // PASSO B.3: Preenche as linhas do Mark-up Impostos
    nI := 0
    For n2 := 1 To oModelSZ92:Length()

        oModelSZ92:GoLine(n2)
        IF ALLTRIM(oModelSZ92:GETVALUE("Z9_DESC")) $ "ICMS" //ICMS

            aRet :=  fGetIcms(nICMS)
            nVlr :=  aRet[1]
            if nICMS == 0
                nICMS  :=  aRet[2]
            endif
            oModelSZ92:LoadValue("Z9_TOTAL", 0)

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_DESC")) $ "PIS E COFINS" //nPisCof

            nPisCof  :=   oModelSZ92:GETVALUE("Z9_ALIQ")
            nVlr     :=   fGetPCof(nPisCof)[1]
            oModelSZ92:LoadValue("Z9_TOTAL", 0)

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_DESC")) $ "COEFICIENTE" //coeficiente

            // CÁLCULO SEQUENCIAL: O valor já foi calculado no PASSO B.2
            oModelSZ92:LoadValue("Z9_TOTAL", nVlrCoefImp)
            ConOut(">>> Mark-up Impostos - COEFICIENTE Z9_TOTAL ATUALIZADO = " + cValToChar(nVlrCoefImp))

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_DESC")) $ "COMISSAO" //nComiss

            nComiss   :=   oModelSZ92:GETVALUE("Z9_ALIQ")

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) $ "000004" //nISS
            nISS    :=   oModelSZ92:GETVALUE("Z9_ALIQ")

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) $ "000005" //nCoef
            nCoef := fCoefVend()

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) $ "000006" .and. !Empty(cTabPV) //nPVVenda

            oModelSZ9:GoLine(1)

            cCdPro := oModelSZ9:Getvalue("Z9_CDPROD")

            DBSELECTAREA("DA1")
            DA1->(dbSetOrder(1))
            IF    DA1->(MsSeek(xFilial("DA1")+cTabPV+cCdPro))

                oModelSZ92:LoadValue("Z9_DESC", PADR("PV TABELA - "+cTabPV, GETSX3CACHE("Z9_DESC","X3_TAMANHO")))
                oModelSZ92:LoadValue("Z9_TOTAL", DA1->DA1_PRCVEN)

            endif

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) $ "000007" //nIRCSLL
            nIRCSLL := oModelSZ92:GETVALUE("Z9_ALIQ")

        ELSEIF ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) $ "000008" //LUCRO
            nVlr := LucroOper - ((nIRCSLL / 100) * nPVVenda)
            oModelSZ92:LoadValue("Z9_TOTAL", nVlr)

        ENDIF

    next n2

    // Loop n3: Acerta valores de ICMS/ISS após PV Venda estar calculado
    //For n3 := 1 To oModelSZ92:Length()
//
    //    oModelSZ92:GoLine(n3)
//
    //    if ALLTRIM(oModelSZ92:GETVALUE("Z9_CDPROD")) $ "000003_000004" //acerta valor
//
    //        nPVVenda := fGetPV()
    //        nAliq   :=  oModelSZ92:GETVALUE("Z9_ALIQ")
    //        nVlr    :=  nPVVenda * (nAliq/100)
    //        oModelSZ92:LoadValue("Z9_TOTAL", nVlr)
//
    //    endif
//
    //next n3

    // LOG final: verifica o valor do COEFICIENTE que será lido por fSetPVen
    ConOut("=== fPrcRecal - VERIFICAÇÃO FINAL DO COEFICIENTE ===")
    For n2 := 1 To oModelSZ92:Length()
        oModelSZ92:GoLine(n2)
        If AllTrim(oModelSZ92:GetValue("Z9_DESC")) $ "COEFICIENTE"
            ConOut(">>> fPrcRecal - COEFICIENTE FINAL (linha " + cValToChar(n2) + "): Z9_TOTAL = " + cValToChar(oModelSZ92:GetValue("Z9_TOTAL")))
            Exit
        EndIf
    Next n2
    ConOut("=== fPrcRecal - FIM ===")

    oModelSZ9:GoLine(1)
    oModelSZ92:GoLine(1)
    oModelSZ93:GoLine(1)
    oView:Refresh("SZ9DETAIL01")
    oView:Refresh("SZ9DETAIL02")
    oView:Refresh("SZ9DETAIL03")
Return



/*-----------------------------------------------------------------------*
| Func:  fPrcPPart -  Funcao Para calcular o Percentual de Participacao  |
*-----------------------------------------------------------------------*/
Static function fPrcPPart()

    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8 := oModel:GetModel("SZ8MASTER")
    Local oModelSZ9 := oModel:GetModel("SZ9DETAIL01")
    LOCAL aMapPer := {}
    local nI := 0
    local n1 := 0
    // PEGAR O TOTAL DO SOMATORIO
    //no "for" pega da segunda linha, pois a primeira ja é o somatorio e tomo como base do percentual
    oModelSZ9:GoLine( 1 )
    oModelSZ9:SETVALUE("Z9_PERCENT",100)
    nVlrTot :=oModelSZ9:GETVALUE("Z9_PRCLIQ")
    DBSELECTAREA("SB1")
    SB1->(dbSetOrder(1))

    For nI := 1 To oModelSZ9:Length()

        IF nI >= 2
            oModelSZ9:GoLine( nI )
            If oModelSZ9:IsDeleted()
                Loop
            EndIf
            cCodPro :=oModelSZ9:GETVALUE("Z9_CDPROD")

            IF     SB1->(MsSeek(xFilial("SB1")+cCodPro))  .and. oModelSZ9:GETVALUE("Z9_PRCLIQ") > 0

                nPer := round(((oModelSZ9:GETVALUE("Z9_PRCLIQ")/nVlrTot)*100),2)

                oModelSZ9:SETVALUE("Z9_PERCENT",nPer)
                if len(aMapPer) > 0
                    aMapPer[len(aMapPer)][3] += nPer
                endif
                conout("teste")
            elseif   SB1->(MsSeek(xFilial("SB1")+cCodPro))  .and. oModelSZ9:GETVALUE("Z9_PRCLIQ") == 0
                aadd(aMapPer,{cCodPro,nI,0})
                // elseif   !SB1->(MsSeek(xFilial("SB1")+cCodPro))  .and. oModelSZ9:GETVALUE("Z9_PRCLIQ") == 0
                //     aMapMod[len(aMapMod)][3] := nI-1
            endif
        endif
    next nI

    For n1 := 1 to Len(aMapPer)
        oModelSZ9:GoLine( aMapPer[n1][2])
        oModelSZ9:SETVALUE("Z9_PERCENT",aMapPer[n1][3])
    Next n1

Return
Static Function fPrcClear()
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8 := oModel:GetModel("SZ8MASTER")
    Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")

    oModelSZ91:ClearData(.F.,.T.)
    oModelSZ92:ClearData(.F.,.T.)
    oModelSZ93:ClearData(.F.,.T.)
    //  if Type( 'oView' ) != "U"
    If ValType( oView ) != "U" .and. !lAuto
        oView:Refresh("SZ9DETAIL01")
        oView:Refresh("SZ9DETAIL02")
        oView:Refresh("SZ9DETAIL03")
    ENDIF
Return


/* D02F02B
Funcao Para Setar o Valor da Variavel Alterada
*/
static Function D02F02B(cModelVld,cZ7Folder)
    Local lRet := .t.
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelTMP := oModel:GetModel(cModelVld)
    //Local cZ7Folder := oModelTMP:getvalue("Z9_IDFLD")
    lOCAL cIdSZ7 :=  cIdSZ7 := oModelSZ8:GETVALUE("Z8_IDSZ7")
    lOCAL nVlTAl :=0 //oModelTMP:GETVALUE("Z9_ALIQ")
    lOCAL nVlUni :=0 //oModelTMP:GETVALUE("Z9_VUNIT")

    if lVldCpos

        cSql :="SELECT * FROM dbo." + retsqlname("SZ7") + " SZ7 " + cEol
        cSql +="WHERE D_E_L_E_T_='' AND Z7_ID="+valtosql(cIdSZ7)+" AND Z7_FOLDER="+valtosql(cZ7Folder) + cEol

        If Select('TMP') <> 0
            TMP->(dbCloseArea())
        Endif

        TCQuery cSql Alias TMP New
        IF  TMP->(!eof())
            if alltrim(cZ7Folder ) $ "2OPE01_3IMP01"

                &(TMP->Z7_LOGINC) := oModelTMP:GETVALUE("Z9_ALIQ")

            ENDIF
        ENDIF
    endif

Return lRet




Static Function D02F02C(aPars)

    Local lRet := .t.
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()

    Local oModelSZ8 := oModel:GetModel("SZ8MASTER")
    Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
    Local nVUnit := 0
    Local nVTot := 0
    Local nQtd := 0
    nQtd    :=  oModelSZ91:GETVALUE("Z9_QUANT")
    nVUnit   :=  oModelSZ91:GETVALUE("Z9_VUNIT")
    nVTot := nVUnit* nQtd
    //oModelSZ91:SETVALUE("Z9_TOTAL",nVTot)

    //    oView:Refresh("SZ9DETAIL01")
Return nVTot
//D02F02I - Trigger/Gatilho para PREENCHER FATOR MATERIA PRIMA
Static Function D02F02I()

    Local lRet := .t.
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    lOCAL cDscPrd := ""
    Local oModelSZ8 := oModel:GetModel("SZ8MASTER")
    lOCAL cIdSZ7 :=  cIdSZ7 := oModelSZ8:GETVALUE("Z8_IDSZ7")


    dbSelectArea("SZ7")
    SZ7->(dbSetOrder(2))

    If   SZ7->(dBSeek(xFilial("SZ7")+cIdSZ7))
        lCanAlt := .t.
        oModelSZ8:SETVALUE("Z8_FATMP",SZ7->Z7_FATMP)
        lCanAlt := .f.
    ENDIF

Return

//D02F02D - Trigger/Gatilho para REtornar a descricao do Produto
Static Function D02F02D()

    Local lRet := .t.
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    lOCAL cDscPrd := ""
    Local oModelSZ8 := oModel:GetModel("SZ8MASTER")

    cProd    :=  oModelSZ8:GETVALUE("Z8_COD")
    cDscPrd :=  posicione("SB1",1,XFILIAL("SB1")+cProd,"B1_DESC")

    lCanAlt := .T.
    oModelSZ8:SETVALUE("Z8_DSCPRD",cDscPrd)
    lCanAlt := .F.

Return

Static FUnction   fSetQtbas(cCodPro,nQtdBas,nVUni)
    Local nPos := 0
    if alltrim(cCodPro) $ "50225199"
        conout("stop")
    endif
    nPos  :=  ascan(aPrdQtBas,{|x| Trim(x[1]) $ alltrim(cCodPro) })
    if nPos == 0
        aadd(aPrdQtBas,{cCodPro,nQtdBas,nVUni})
    endif
    conout("teste")
Return

/****************************************\
| 04/2021 - Gabriel Araujo               |
| Funcao fGetIcms - Calculo do ICMS      |
| Percorre todos o produtos do tipo MP   |
| e Busca na SBZ                         |
\****************************************/

Static Function fGetIcms(nAliqPar)
    Local aArea := GetArea()
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local nRet := 0
    Local nSumAliq := 0
    Local nCntAliq := 0
    Local nAliqRet :=0
    Local aAliq :={0,0,0,0}
    Local nTZ9CDPRD  := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local oModelSZ9 := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local aOldLine   := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}

    Default nAliqPar := 0
    oModelSZ9:GoLine( 1 )

    /*
        retornar a aliquota do frete
        se nao achar é 3 %
    */
    cSeek1 := padr('000003',nTZ9CDPRD)
    cSeek2 := padr('FRETE CUSTO MP',nTZ9DESC)

    if  oModelSZ93:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        nAliqFre := ( oModelSZ93:getvalue("Z9_ALIQ") / 100 )
    else
        nAliqFre := 0.03
    endif

    // Info -> Percorro o Grid Principal  verificando se o produto tem ICMS
    // Depois realizo o calculo conforme as aliquotas
    nRet := 0
    For nI := 1 To oModelSZ9:Length()
        lSbz := .f.
        IF nI >= 2

            oModelSZ9:GoLine( nI )

            cCodPro  :=oModelSZ9:GETVALUE("Z9_CDPROD")
            nVLrAliq :=oModelSZ9:GETVALUE("Z9_ALIQ")
            nVlrTot  :=oModelSZ9:GETVALUE("Z9_TOTAL")
            nVlrTot  := nVlrTot + (nVlrTot*nAliqFre)

            DBSELECTAREA("SBZ")
            SBZ->(dbSetOrder(1))

            DBSELECTAREA("SB1")
            SB1->(dbSetOrder(1))

            IF    SBZ->(MsSeek(xFilial("SBZ")+cCodPro)) .and.  SB1->(MsSeek(xFilial("SB1")+cCodPro))
                if   ((SBZ->BZ_PICM >0 .AND. ALLTRIM(SB1->B1_TIPO) $ "MP" .and. nVlrTot > 0) .OR.( nVLrAliq >0 ))

                    if nAliqPar == 0
                        nAliqCal := (SBZ->BZ_PICM/100)
                        nAliqRet :=12
                    else
                        nAliqCal := nVLrAliq/100
                        nAliqRet :=nAliqCal
                    endif
                    nRet += nVlrTot * nAliqCal

                    conout("gda")

                    aAliq[1] += nAliqCal
                    aAliq[2] += (nVlrTot *nAliqCal)
                    aAliq[3] += 1
                    aAliq[4] += nVlrTot

                ENDIF
            ENDIF

        endif

    next nI
    conout("calc aliqret")
    //  nAliqRet := iif(len(aAliq) > 1,0,aAliq[1])
    // nAliqRet := (aAliq[1]/aAliq[3])*100
    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])
    RestArea(aArea)
Return {nRet,nAliqRet} //valor / aliquota

/****************************************\
| 04/2021 - Gabriel Araujo               |
| Funcao fGetIcms - Calculo do ICMS      |
| Percorre todos o produtos do tipo MP   |
| e Busca na SBZ                         |
\****************************************/

Static Function fGetPCof(nAliq)
    Local aArea := GetArea()
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local nRet := 0
    Local nSumAliq := 0
    Local nCntAliq := 0
    Local nAliqRet :=0
    Local aAliq :={}

    Local nTZ9CDPRD  := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local oModelSZ9 := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local aOldLine   := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}
    oModelSZ9:GoLine( 1 )

    /*
        retornar a aliquota do frete
        se nao achar é 3 %
    */
    cSeek1 := padr('000003',nTZ9CDPRD)
    cSeek2 := padr('FRETE CUSTO MP',nTZ9DESC)

    if  oModelSZ93:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        nAliqFre := ( oModelSZ93:getvalue("Z9_ALIQ") / 100 )
    else
        nAliqFre := 0.03
    endif
    // Info -> Percorro o Grid Principal  verificando se o produto tem ICMS
    // Depois realizo o calculo conforme as aliquotas

    For nI := 1 To oModelSZ9:Length()
        lSbz := .f.
        IF nI >= 2

            oModelSZ9:GoLine( nI )

            cCodPro :=oModelSZ9:GETVALUE("Z9_CDPROD")
            nVlrTot :=oModelSZ9:GETVALUE("Z9_TOTAL")
            nVlrTot := nVlrTot + (nVlrTot*nAliqFre)
            DBSELECTAREA("SBZ")
            SBZ->(dbSetOrder(1))

            DBSELECTAREA("SB1")
            SB1->(dbSetOrder(1))

            IF     SB1->(MsSeek(xFilial("SB1")+cCodPro)) .and. ALLTRIM(SB1->B1_TIPO) $ "MP"

                nRet += nVlrTot * (nAliq/100)

            ENDIF

        endif
    next nI
    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])
    RestArea(aArea)
Return {nRet,nAliq}

Static Function fProcCusMp()
    Local aArea := GetArea()
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local nVlICMS := 0
    Local nVlPCC := 0
    Local nVlFre := 0
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")

    Local aOldLine := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}

    //busca os valores dos impostos pis cofins icms

    cSeek1 :=  '000001         '
    cSeek2 :=  'ICMS                                              '

    if  oModelSZ92:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        nVlICMS := oModelSZ92:Getvalue("Z9_TOTAL")
    endif

    cSeek1 := '000002         '
    cSeek2 := 'PIS E COFINS                                      '
    if  oModelSZ92:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        nVlPCC := oModelSZ92:Getvalue("Z9_TOTAL")
    endif

    cSeek1 := '000003         '
    cSeek2 :=  'FRETE CUSTO MP                                    '
    if  oModelSZ93:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        nVlFre := oModelSZ93:Getvalue("Z9_TOTAL")
    endif


    cSeek1 := "000006         "
    cSeek2 := "CUSTO TOTAL DO PRODUTO                            "


    if  oModelSZ9:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})

        //    Z9_FATMOD
        // 23/09/2021 - Gabriel Retirado conforme solicitação
        //  nCalc := (nTotMP + nVlFre) -(nVlPCC+nVlICMS) + (nTotMOD/0.7)
        nCalc := (nTotMP + nVlFre) -(nVlPCC+nVlICMS) + (nTotMOD) + nTotGG + nTotINV // Incluindo Gastos Gerais (tipo II) e Investimento/Ferramental

        oModelSZ9:setvalue("Z9_TOTAL",nCalc)

    else
        // 23/09/2021 - Gabriel Retirado conforme solicitação
        //   nCalc := nTotMP + nVlFre -nVlPCC-nVlICMS + (nTotMOD/0.7)
        nCalc := nTotMP + nVlFre -nVlPCC-nVlICMS + (nTotMOD) + nTotGG + nTotINV // Incluindo Gastos Gerais (tipo II) e Investimento/Ferramental
    endif
    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])

    RestArea(aArea)
Return nCalc


Static Function fCoefVend()
    Local aArea := GetArea()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local nCoef := 0
    Local nVlrPrdLiq := 0  // Preço líquido da linha 1
    Local nAliqCoef := 0    // Alíquota do coeficiente
    Local nPosCoef := 0
    Local nTotalCalcImp := 0  // Total calculado Mark-up Impostos

    Local nTZ9CDPRD := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC  := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local aOldLine   := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}
    Local nI := 0
    Local cCodProd := ""
    Local cItem := ""
    Local nVlrBaseOper := 0
    Local aAliqImp := {}
    Local cDescLinha := ""
    Local nAliqLinha := 0
    Local cDescPasso := ""
    Local nAliqPasso := 0
    Local nVlrAntes  := 0
    Local nDivisor   := 0

    ConOut("=== fCoefVend - INICIO ===")

    // ========================================
    // PASSO 1: Busca o Z9_TOTAL da linha 006 (COEFICIENTE) do Mark-up Operacional
    // Este valor será a BASE para o cálculo do Mark-up Impostos
    // ========================================
    nVlrBaseOper := 0
    For nI := 1 To oModelSZ93:Length()
        oModelSZ93:GoLine(nI)
        If AllTrim(oModelSZ93:GetValue("Z9_DESC")) $ "COEFICIENTE"
            nVlrBaseOper := oModelSZ93:GetValue("Z9_TOTAL")
            ConOut(">>> BASE DO MARK-UP IMPOSTOS: Z9_TOTAL da linha " + cValToChar(nI) + " (COEFICIENTE) do Mark-up Operacional = " + cValToChar(nVlrBaseOper))
            Exit
        EndIf
    Next nI
    
    // Fallback: se não encontrou no Mark-up Operacional, usa o preço líquido da linha 1 da Estrutura
    If nVlrBaseOper == 0
        oModelSZ9:GoLine(1)
        nVlrBaseOper := oModelSZ9:GetValue("Z9_PRCLIQ")
        ConOut(">>> FALLBACK: Usando Z9_PRCLIQ da linha 1 da Estrutura = " + cValToChar(nVlrBaseOper))
    EndIf
    
    // Guarda também o preço líquido para referência
    oModelSZ9:GoLine(1)
    nVlrPrdLiq := oModelSZ9:GetValue("Z9_PRCLIQ")
    ConOut(">>> PREÇO LÍQUIDO (Linha 1 - referência): " + cValToChar(nVlrPrdLiq))
    ConOut(">>> BASE PARA CÁLCULO IMPOSTOS: " + cValToChar(nVlrBaseOper))

    // ========================================
    // PASSO 2: CÁLCULO SEQUENCIAL DO COEFICIENTE DO MARK-UP IMPOSTOS
    // O valor base (Mark-up Operacional) é dividido sequencialmente
    // por (100% - Alíquota) de cada linha de imposto (exceto COEFICIENTE),
    // na ordem em que aparecem na grid.
    // Exemplo:
    //   Base = 146.577,90
    //   Passo 1: 146.577,90 / (100% - 7% ICMS)     = 157.610,65
    //   Passo 2: 157.610,65 / (100% - 9,25% PIS)    = 173.675,65
    //   Resultado = 173.675,65 = COEFICIENTE
    // ========================================
    
    // PASSO 2.1: Coleta alíquotas das linhas de impostos (exceto COEFICIENTE) na ordem
    aAliqImp := {}
    For nI := 1 To oModelSZ92:Length()
        oModelSZ92:GoLine(nI)
        If !oModelSZ92:IsDeleted()
            cDescLinha := AllTrim(oModelSZ92:GetValue("Z9_DESC"))
            If !(cDescLinha $ "COEFICIENTE")
                nAliqLinha := oModelSZ92:GetValue("Z9_ALIQ")
                If nAliqLinha > 0
                    aAdd(aAliqImp, {cDescLinha, nAliqLinha, nI})
                    ConOut(">>> fCoefVend - Coletada alíquota: " + cDescLinha + " = " + cValToChar(nAliqLinha) + "% (linha " + cValToChar(nI) + ")")
                EndIf
            EndIf
        EndIf
    Next nI
    
    // PASSO 2.2: Calcula o COEFICIENTE de forma SEQUENCIAL
    nTotalCalcImp := nVlrBaseOper
    ConOut(">>> fCoefVend - CÁLCULO SEQUENCIAL - Base inicial: " + cValToChar(nTotalCalcImp))
    
    If nTotalCalcImp > 0
        For nI := 1 To Len(aAliqImp)
            cDescPasso := aAliqImp[nI][1]
            nAliqPasso := aAliqImp[nI][2]
            nVlrAntes  := nTotalCalcImp
            
            // Fórmula: Valor / (100% - Alíquota%) = Valor / ((100 - Aliq) / 100)
            nDivisor := (100 - nAliqPasso) / 100
            If nDivisor > 0
                nTotalCalcImp := nTotalCalcImp / nDivisor
                ConOut(">>> fCoefVend Passo " + cValToChar(nI) + ": " + cValToChar(nVlrAntes) + " / (100% - " + cValToChar(nAliqPasso) + "%) = " + cValToChar(nTotalCalcImp) + " [" + cDescPasso + "]")
            EndIf
        Next nI
    EndIf
    
    ConOut(">>> fCoefVend - COEFICIENTE FINAL: " + cValToChar(nTotalCalcImp))
    
    // PASSO 2.3: Atualiza a linha do COEFICIENTE com o valor calculado
    nAliqCoef := 0
    For nI := 1 To oModelSZ92:Length()
        oModelSZ92:GoLine(nI)
        cItem := AllTrim(oModelSZ92:GetValue("Z9_ITEM"))
        cCodProd := AllTrim(oModelSZ92:GetValue("Z9_CDPROD"))
        
        If !oModelSZ92:IsDeleted()
            If cItem == "003" .Or. cCodProd == "000003" .Or. AllTrim(oModelSZ92:GetValue("Z9_DESC")) $ "COEFICIENTE"
                nPosCoef := nI
                nAliqCoef := oModelSZ92:GetValue("Z9_ALIQ")
                oModelSZ92:SetValue("Z9_TOTAL", nTotalCalcImp)
                ConOut(">>> fCoefVend - COEFICIENTE (003) Z9_TOTAL Atualizado: " + cValToChar(nTotalCalcImp))
            EndIf
        EndIf
    Next nI

    // Restaura posições originais
    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])

    RestArea(aArea)
    
    ConOut("=== fCoefVend - FIM ===")
    
Return {nAliqCoef, nTotalCalcImp}


Static Function fCoefOP()
    Local aArea := GetArea()
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local nCoef := 0

    Local nTZ9CDPRD := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local oModelSZ9 := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local aOldLine := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}

    ConOut("=== fCoefOP - INICIO ===")

    cSeek1 := padr('000007',nTZ9CDPRD)
    cSeek2 := padr('IR E CSLL',nTZ9DESC)
    if  oModelSZ92:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        nCoef += oModelSZ92:Getvalue("Z9_ALIQ")
        ConOut(">>> IR E CSLL: " + cValToChar(oModelSZ92:Getvalue("Z9_ALIQ")) + "% | Acumulado: " + cValToChar(nCoef) + "%")
    endif

    cSeek1 := padr('000001',nTZ9CDPRD)
    cSeek2 := padr('CUSTO FIXO',nTZ9DESC)
    if  oModelSZ93:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        nCoef += oModelSZ93:Getvalue("Z9_ALIQ")
        ConOut(">>> CUSTO FIXO: " + cValToChar(oModelSZ93:Getvalue("Z9_ALIQ")) + "% | Acumulado: " + cValToChar(nCoef) + "%")
    endif

    cSeek1 := padr('000004',nTZ9CDPRD)
    cSeek2 := padr('COMISSAO',nTZ9DESC)
    if  oModelSZ93:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        nCoef += oModelSZ93:Getvalue("Z9_ALIQ")
        ConOut(">>> COMISSAO: " + cValToChar(oModelSZ93:Getvalue("Z9_ALIQ")) + "% | Acumulado: " + cValToChar(nCoef) + "%")
    endif

    cSeek1 := padr('000005',nTZ9CDPRD)
    cSeek2 := padr('LUCRO',nTZ9DESC)
    if  oModelSZ93:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        nCoef += oModelSZ93:Getvalue("Z9_ALIQ")
        ConOut(">>> LUCRO: " + cValToChar(oModelSZ93:Getvalue("Z9_ALIQ")) + "% | Acumulado: " + cValToChar(nCoef) + "%")
    endif

    cSeek1 := padr('000002',nTZ9CDPRD)
    cSeek2 := padr('FRETE SOBRE VENDAS',nTZ9DESC)
    if  oModelSZ93:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        nCoef += oModelSZ93:Getvalue("Z9_ALIQ")
        ConOut(">>> FRETE SOBRE VENDAS: " + cValToChar(oModelSZ93:Getvalue("Z9_ALIQ")) + "% | Acumulado: " + cValToChar(nCoef) + "%")
    endif

    // Atualiza a alíquota do COEFICIENTE
    cSeek1 := padr('006',nTZ9CDPRD)
    cSeek2 := padr('COEFICIENTE',nTZ9DESC)
    if  oModelSZ93:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        oModelSZ93:Setvalue("Z9_ALIQ",100-nCoef)
        ConOut(">>> COEFICIENTE Alíquota ATUALIZADA para: " + cValToChar(100-nCoef) + "%")
    endif

    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])

    ConOut("=== fCoefOP - FIM (Retorna: " + cValToChar(100-nCoef) + "%) ===")
    RestArea(aArea)
Return 100-nCoef


Static Function fPrcMark()
    Local nRet := 0
    Local aArea := GetArea()
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local nCoef := 0
    Local nTZ9CDPRD := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC  := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local oModelSZ9 := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local aOldLine := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}
    cSeek1 := padr('000005',nTZ9CDPRD)
    cSeek2 := padr('COEFICIENTE',nTZ9DESC)
    if  oModelSZ92:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        nPerCof :=  oModelSZ92:Getvalue("Z9_ALIQ")
    endif

    cSeek1 := padr('000007',nTZ9CDPRD)
    cSeek2 := padr('PV OPERACIONAL',nTZ9DESC)
    if  oModelSZ93:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        nVlrCus :=  oModelSZ93:Getvalue("Z9_TOTAL")
    endif
    nRet := nVlrCus / (nPerCof/100)

    cSeek1 := padr('000005',nTZ9CDPRD)
    cSeek2 := padr('COEFICIENTE',nTZ9DESC)
    if  oModelSZ92:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})
        oModelSZ92:Setvalue("Z9_TOTAL",nRet)
    endif
    nRet:= 0.00
    if empty(cTabPV)
        If MsgYesNo( 'Define tabela de Preço?', 'Delpi' )
            U_fSetTabPV()
        endif
    endif
    IF !Empty(cTabPV)
        oModelSZ9:GoLine(1)

        cCdPro := oModelSZ9:Getvalue("Z9_CDPROD")

        DBSELECTAREA("DA1")
        DA1->(dbSetOrder(1))
        IF    DA1->(MsSeek(xFilial("DA1")+cTabPV+cCdPro))

            nRet:=  DA1->DA1_PRCVEN

        endif

    endif
    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])

Return nRet


Static Function fSetPOper()
    Local nRet       := 0
    Local aArea      := GetArea()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local nCoef      := 0
    Local nTZ9CDPRD  := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local nVlrPrd    := 0
    Local xCoef      := 0
    Local aOldLine   := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}

    ConOut("=== fSetPOper - INICIO ===")

    // PASSO 1: Busca o PREÇO LÍQUIDO da linha 1 da grid Estrutura
    oModelSZ9:GoLine(1)
    nVlrPrd := oModelSZ9:GetValue("Z9_PRCLIQ")
    ConOut(">>> PREÇO LÍQUIDO (Linha 1 - Z9_PRCLIQ): " + cValToChar(nVlrPrd))

    // PASSO 2: Busca a ALÍQUOTA do COEFICIENTE (Z9_CDPROD = '000006') na grid Mark-up Operacional
    cSeek1 := padr('006',nTZ9CDPRD)
    cSeek2 := padr('COEFICIENTE',nTZ9DESC)
    ConOut(">>> Buscando COEFICIENTE com Z9_CDPROD = '" + cSeek1 + "' e Z9_DESC = '" + cSeek2 + "'")
    
    if  oModelSZ93:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        xCoef := oModelSZ93:GetValue("Z9_ALIQ")
        ConOut(">>> ? COEFICIENTE ENCONTRADO! Alíquota: " + cValToChar(xCoef) + "%")
        
        // PASSO 3: Calcula o TOTAL = Preço Líquido ÷ (Alíquota/100)
        // Exemplo: 4085.66 ÷ (70/100) = 4085.66 ÷ 0.70 = 5836.66
        If xCoef > 0
            nTotal := nVlrPrd / (xCoef / 100)
            ConOut(">>> ?? CÁLCULO: " + cValToChar(nVlrPrd) + " ÷ (" + cValToChar(xCoef) + "/100) = " + cValToChar(nTotal))
            
            // PASSO 4: Atualiza o campo Z9_TOTAL da linha COEFICIENTE (000006)
            oModelSZ93:SetValue("Z9_TOTAL", nTotal)
            ConOut(">>> ??? COEFICIENTE (000006) Total Atualizado: " + cValToChar(nTotal) + " ???")
        Else
            nTotal := 0
            ConOut(">>> ? ERRO: Alíquota do COEFICIENTE é ZERO!")
        EndIf
    Else
        nTotal := 0
        ConOut(">>> ? ERRO: Linha COEFICIENTE (000006) não encontrada na grid Mark-up Operacional!")
        ConOut(">>> Verifique se o campo Z9_CDPROD contém '000006' e Z9_DESC contém 'COEFICIENTE'")
    endif

    // PASSO 5: Atualiza também o PV OPERACIONAL (000007) se existir
    cSeek1 := padr('007',nTZ9CDPRD)
    cSeek2 := padr('PV OPERACIONAL',nTZ9DESC)
    ConOut(">>> Buscando PV OPERACIONAL com Z9_CDPROD = '" + cSeek1 + "'")
    
    if  oModelSZ93:SeekLine({{"Z9_ITEM",cSeek1},{"Z9_DESC",cSeek2}})
        oModelSZ93:SetValue("Z9_TOTAL", nTotal)
        ConOut(">>> ? PV OPERACIONAL (000007) Atualizado: " + cValToChar(nTotal))
    else
        ConOut(">>> ?? PV OPERACIONAL (000007) não encontrado")
    endif

    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])

    ConOut("=== fSetPOper - FIM ===")

Return nTotal


/* Static Function fGetPV()
    Local nRet       := 0
    Local aArea      := GetArea()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local nCoef      := 0
    Local nTZ9CDPRD  := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")

    Local nValor      := 0
    Local aOldLine   := {oModelSZ9:NLINE,;
        oModelSZ92:NLINE,;
        oModelSZ93:NLINE}

    cSeek1 := padr('000003',nTZ9CDPRD)
    cSeek2 := padr('COEFICIENTE',nTZ9DESC)

    if  oModelSZ92:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})

        nValor := oModelSZ92:GETvalue("Z9_TOTAL")

    endif

    oModelSZ9:GoLine(aOldLine[1])
    oModelSZ92:GoLine(aOldLine[2])
    oModelSZ93:GoLine(aOldLine[3])

Return nValor */





USER Function fSetTabPV()


    Local oGet1
    Local cFolder := SPACE(200)
    Local oSay1
    Local oSay2
    Local nOpcGet := 0
    LOCAL aPar    := array(8)
    Local bOk     := {|| }
    Local bCancel := {|| }
    Static oDlg
    oTFont  := TFont():New('Arial',,-11,.T.)
    oTFont2 := TFont():New('Arial',,-10,.f.)
    oTFont3 := TFont():New('Arial',,-11,.f.)


    DEFINE MSDIALOG oDlg TITLE "Delpi " FROM 000, 000  TO 200, 500 COLORS 0, 16777215 PIXEL  STYLE DS_MODALFRAME


    //Linha 1 Coluna 1
    aPar[1]:= 035; aPar[2] := 008
    aPar[3]:= 045; aPar[4] := 009
    aPar[5]:= 045

    //Linha 1 Coluna 1
    @aPar[1],aPar[2]  SAY   oSay1 PROMPT 'Selecione a tabela de Preço'	SIZE    150,        020     OF oDlg FONT oTFont PIXEL
    @aPar[3],aPar[4]  MSGET oGet2 VAR cTabPV SIZE     aPar[5], 010     OF oDlg  FONT oTFont2 COLORS 0, 16777215 PIXEL;
        VALID ExistCpo("DA0",cTabPV) F3 "DA0"

    // Cria a Enchoice
    bCancel := { ||  oDlg:End() }
    //bOK     := { || (  FWMsgRun(, {||   fProcXML(cFolder)}, "WCT", cMsgRun) ,oDlg:End() )}
    bOK     := { || (  fVldDA0() ,oDlg:End() )}
    ACTIVATE MSDIALOG oDlg ON INIT EnchoiceBar(oDlg, bOk , bCancel) CENTERED

Return

Static Function fVldDA0()
    Local lRet := .t.

    DBSELECTAREA("DA0")
    DA0->(dbSetOrder(1))
    IF DA0->(MsSeek(xFilial("DA0")+cTabPV))


        if  ( DATE() < DA0->DA0_DATDE  .OR. DA0->DA0_DATATE < DATE()  ) .OR. ALLTRIM(DA0->DA0_ATIVO ) $ "2"
            lRet := .F.
            MSGSTOP("Tabela de Preço Fora de Vigencia ou Inativa","Delpi")
        ENDIF
    ELSE
        lRet := .F.
        MSGSTOP("Tabela de Preço Não Existe","Delpi")
    ENDIF

Return lRet


/*/{Protheus.doc} D02F02E

    Filtro da Consulta Padrao DA1DLP

    @author  Gabriel

    @since   17-05-2021
/*/

USER FUNCTION D02F02E()
    Local lRet       := .t.
    Local aAreaDA0   := DA0->(GetArea())
    Local aAreaDA1   := DA1->(GetArea())
    Local aArea      := GetArea()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local nTamPrd    := GetSx3cache("B1_COD","X3_TAMANHO")
    Local cSQL := ""
    cCodPro :=padr( oModelSZ8:getvalue("Z8_COD"),nTamPrd)


    cSQL :=" SELECT  DISTINCT DA1.DA1_CODTAB ,DA0_ATIVO,DA0_DATATE " + cEol
    cSql +="FROM dbo." + retsqlname("DA0") + " DA0 (NOLOCK) " + cEol
    cSql +="    JOIN dbo." + retsqlname("DA1") + " DA1 (NOLOCK) " + cEol
    cSql +="        ON DA1.D_E_L_E_T_ = '' " + cEol
    cSql +="           AND DA1.DA1_FILIAL = DA0.DA0_FILIAL " + cEol
    cSql +="           AND DA1.DA1_CODTAB = DA0.DA0_CODTAB " + cEol
    cSql +="WHERE DA0.D_E_L_E_T_ = '' " + cEol
    cSql +="      AND  DA0.DA0_CODTAB =  "+valtosql(DA1->DA1_CODTAB) + cEol
    cSql +="      AND DA1.DA1_CODPRO =  "+valtosql(cCodPro) + cEol
    cSql +="	  AND   DA0.DA0_ATIVO != '2'  " + cEol
    cSql +="	  AND  NOT(   DA0.DA0_DATATE < "+valtosql(dDataBase) + cEol
    cSql +="                         AND DA0.DA0_DATATE != '') " + cEol
    cSql +="						 ORDER BY 1 " + cEol

    If Select('TMPDA0') <> 0
        TMPDA0->(dbCloseArea())
    Endif
    TCQuery cSql Alias TMPDA0 New
    IF TMPDA0->(eof())
        lRet       := .F.
    ENDIF
    TMPDA0->(dbCloseArea())


    RESTAREA(aAreaDA0 )
    RESTAREA(aArea    )

Return lREt


/*/{Protheus.doc} D02F02F

    Filtro da Consulta Padrao SZ7DLP

    @author  Gabriel

    @since   17-05-2021
/*/

USER FUNCTION D02F02F()
    Local lRet       := .t.
    Local aAreaDA0   := DA0->(GetArea())
    Local aAreaDA1   := DA1->(GetArea())
    Local aArea      := GetArea()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local nTamPrd    := GetSx3cache("B1_COD","X3_TAMANHO")
    Local cSQL := ""
    cCodPro :=padr( oModelSZ8:getvalue("Z8_COD"),nTamPrd)

    cSQL :=" SELECT DISTINCT  Z7_ID, Z7_DESCPLN " + cEol
    cSql +="    FROM dbo.SZ7010 TBL1 " + cEol
    cSql +="WHERE TBL1.D_E_L_E_T_ = '' " + cEol
    cSql +="ORDER BY 1 "


    If Select('TMPSZ7') <> 0
        TMPSZ7->(dbCloseArea())
    Endif
    TCQuery cSql Alias TMPDA0 New
    IF TMPSZ7->(eof())
        lRet       := .F.
    ENDIF
    TMPDA0->(dbCloseArea())
    //  IF TRIM(DA1->DA1_CODPRO) == TRIM(cCodPro)

    //      dbSelectArea("DA0")
    //      DA0->(dbSetOrder(1))
    //      IF   DA0->(dbSeek(xFilial("DA0")+DA1->DA1_CODTAB))
    //          IF( Dtos( DA0->DA0_DATATE) < Dtos(dDataBase).And. !Empty(Dtos( DA0->DA0_DATATE))) .OR. DA0->DA0_ATIVO =='2'
    //              lRet := .F.
    //          ENDIF
    //      ENDIF

    //  ELSE

    //      lRet := .F.

    //  ENDIF
    RESTAREA(aAreaDA0 )
    RESTAREA(aArea    )

Return lREt


/*/{Protheus.doc} fPrcEst2

    Funï¿½ï¿½o para Calcular o Custo dos produtos com base na estrutura dele
    Vai calcular a Mao de Obra tambem

    Para compor o custo Total do Produto é a seguinte formula

    MOD => Somatorio MOD * 1,7 (Fator)
    MP  => Somatorio MP + Percentual do Frete  - (ICMS + Pis Cofins)

    26/11/2021
    Solicitado criação de campo para cadastro na SZ7 para saber se vai considerar ou nao Icms e/ou Pis Cofins

25/03/2022
Configuração do PIS/Cofins , sempre que for LUCRO REAL (A EMPRESA 05 NAO É E TEM QUE AJUSTAR POSTERIOSMENTE).
A Regra é a seguinte, sempre que for lucro real considerar pis/cofins

-- nVlrFre Vem do Cabeçalho Z8_PERFRT

    @author  Gabriel Araujo
    @since   17-05-2021
/*/

Static Function fPrcEst2()

    Local oModel      := FWMODELACTIVE()
    Local oView       := FWViewActive()
    Local oModelSZ8   := oModel:GetModel("SZ8MASTER")
    Local oModelSZ91  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92  := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93  := oModel:GetModel("SZ9DETAIL03")
    Local nAliq       := 0.00
    Local nVlrFre := oModelSZ8:getvalue("Z8_PERFRT")/100
    Local nFatMOD := oModelSZ8:getvalue("Z8_FATMOD")
    Local nFatMP  := oModelSZ8:getvalue("Z8_FATMP")/100
    Local nTxPis	:= SuperGetMv("MV_TXPIS",.F.)
    Local nTxCof	:= SuperGetMv("MV_TXCOFIN",.F.)
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local cCodCal :=   oModelSZ8:getvalue("Z8_IDSZ7")
    
    // Variáveis de acumulação por tipo
    Local nTotMP_Acum  := 0  // 000001 - Matéria Prima
    Local nTotMOD_Acum := 0  // 000002 - Mão de Obra Direta
    Local nTotBen_Acum := 0  // 000003 - Beneficiamento
    Local nTotGG_Acum  := 0  // 000004 - Gastos Gerais (incluindo tipo II)
    Local nTotINV_Acum := 0  // 000009 - Investimento/Ferramental
    Local nQtdTotal    := 0  // Quantidade total para as linhas de totalização
    
    // Buscar configurações da SZ7
    If   SZ7->(dBSeek(xFilial("SZ7")+cCodCal))
        lCalPCOF := IIF(   SZ7->Z7_PISCFMP == 'N',.F.,.T.)
        lCalICMS := IIF(   SZ7->Z7_ICMSMP == 'N',.F.,.T.)
    ENDIF

    cSeek1 := "PIS E COFINS"

    /*Busco Pela Linha do PIS e cofins na aba Impostos*/
    if  oModelSZ92:SeekLine({{"Z9_DESC",cSeek1}}) .and. lCalPCOF
        nPisCof :=  oModelSZ92:getvalue("Z9_ALIQ")/100
    ELSE
        nPisCof := 0.0
    endif
    
    aTPPrd := {}
    
    ConOut("=== fPrcEst2 - INICIO DO PROCESSAMENTO ===")
    
    // PRIMEIRA PASSADA: Processar apenas itens REAIS (não são linhas de totalização)
    For N1 := 1 To   oModelSZ91:Length()
        oModelSZ91:GOLINE(n1)
        If oModelSZ91:IsDeleted()
            ConOut(">>> fPrcEst2 - Linha " + cValToChar(N1) + " - DELETADA (ignorada)")
            Loop
        EndIf
        cCodProd := AllTrim(oModelSZ91:getvalue("Z9_CDPROD"))
        
        // Pula linhas de totalização na primeira passada
        If cCodProd $ "000001|000002|000003|000004|000009"
            ConOut(">>> fPrcEst2 - Linha " + cValToChar(N1) + " [" + cCodProd + "] - TOTALIZADOR (pulado)")
            Loop
        EndIf
        
        nVlrCal  := 0.00
        cTpPrd := POSICIONE("SB1",1,XFILIAL("SB1")+PadR(cCodProd,15),"B1_TIPO")
        nVlrTot  := oModelSZ91:getvalue("Z9_TOTAL")
        nQtdPrd  := oModelSZ91:getvalue("Z9_QUANT")
        nAliqICM := iif(lCalICMS, oModelSZ91:getvalue("Z9_ALIQ")/100 , 0)

        ConOut(">>> fPrcEst2 - Linha " + cValToChar(N1) + " [" + cCodProd + "] | Tipo: " + cTpPrd + " | QtdPrd: " + cValToChar(nQtdPrd) + " | VlrTot: " + cValToChar(nVlrTot))

        if nVlrTot > 0 .and. !Empty(cTpPrd)
            
            // Acumula quantidade para totalização
            nQtdTotal += nQtdPrd

            if cTpPrd $ "MO"
                if nFatMOD > 0
                    nVlrCal := nVlrTot / nFatMOD
                else
                    nVlrCal := nVlrTot
                endif
                nTotMOD_Acum += nVlrCal // Acumula Mão de Obra Direta
                ConOut(">>> fPrcEst2 - ITEM MOD: " + cCodProd + " | Qtd: " + cValToChar(nQtdPrd) + " | Valor: " + cValToChar(nVlrCal) + " | MOD Acum: " + cValToChar(nTotMOD_Acum))
                
            elseif  cTpPrd $ "MP"
                CONOUT(">>> fPrcEst2 - Calculo Frete")
                nVlrCal :=  nVlrTot + (nVlrTot * nVlrFre)
                CONOUT(">>> fPrcEst2 - Calculo descontando os impostos")
                nVlrCal :=   ( 1-(nAliqICM)) *nVlrCal
                nVlrCal :=   ( 1-(nPisCof)) *nVlrCal
                
                IF nFatMP > 0
                    nVlrCal :=  (nVlrCal*(1+nFatMP))
                ENDIF
                
                nTotMP_Acum += nVlrCal // Acumula Matéria Prima
                ConOut(">>> fPrcEst2 - ITEM MP: " + cCodProd + " | Qtd: " + cValToChar(nQtdPrd) + " | Valor: " + cValToChar(nVlrCal) + " | MP Acum: " + cValToChar(nTotMP_Acum))
                
            elseif cTpPrd $ "FE|IN" // Ferramental/Investimento
                nVlrCal := nVlrTot // Valor integral do investimento
                nTotINV_Acum += nVlrCal // Acumula Investimento
                ConOut(">>> fPrcEst2 - ITEM FERRAMENTAL: " + cCodProd + " | Qtd: " + cValToChar(nQtdPrd) + " | Tipo: " + cTpPrd + " | Valor: " + cValToChar(nVlrCal) + " | INV Acum: " + cValToChar(nTotINV_Acum))
                
            elseif cTpPrd $ "GG|MC|II" // Gastos Gerais, Material de Consumo ou tipo II (ex: mini aplicador)
                nVlrCal := nVlrTot // Valor integral (SEM aplicar frete/impostos)
                nTotGG_Acum += nVlrCal // Acumula Gastos Gerais
                ConOut(">>> fPrcEst2 - ITEM GASTOS GERAIS/II: " + cCodProd + " | Qtd: " + cValToChar(nQtdPrd) + " | Tipo: " + cTpPrd + " | VlrBruto: " + cValToChar(nVlrTot) + " | VlrCalc: " + cValToChar(nVlrCal) + " | GG Acum: " + cValToChar(nTotGG_Acum))
                
            elseif cTpPrd $ "BE" // Beneficiamento
                nVlrCal :=  nVlrTot + (nVlrTot * nVlrFre)
                nVlrCal :=   ( 1-(nPisCof)) *nVlrCal
                nVlrCal :=   ( 1-(nAliqICM)) *nVlrCal
                nTotBen_Acum += nVlrCal // Acumula Beneficiamento
                ConOut(">>> fPrcEst2 - ITEM BENEFICIAMENTO: " + cCodProd + " | Qtd: " + cValToChar(nQtdPrd) + " | Valor: " + cValToChar(nVlrCal) + " | BEN Acum: " + cValToChar(nTotBen_Acum))
                
            ELSE
                CONOUT(">>> fPrcEst2 - Calculo Frete (OUTROS)")
                nVlrCal :=  nVlrTot + (nVlrTot * nVlrFre)
                CONOUT(">>> fPrcEst2 - Calculo descontando os impostos (OUTROS)")
                nVlrCal :=   ( 1-(nPisCof)) *nVlrCal
                nVlrCal :=   ( 1-(nAliqICM)) *nVlrCal
                ConOut(">>> fPrcEst2 - ITEM OUTROS: " + cCodProd + " | Qtd: " + cValToChar(nQtdPrd) + " | Tipo: " + cTpPrd + " | Valor: " + cValToChar(nVlrCal))
            ENDIF
            
            // Acumula no array de tipos
            nPos  :=  ascan(aTPPrd,{|x| Trim(x[1]) $ alltrim(cTpPrd) })
            if nPos == 0
                aadd(aTPPrd,{cTpPrd,nVlrTot,nVlrCal})
            else
                aTPPrd[nPos][2]+=nVlrTot
                aTPPrd[nPos][3]+=nVlrCal
            endif

            oModelSZ91:Setvalue("Z9_PRCLIQ", nVlrCal)
        endif
    next N1
    
    // LOG dos totais acumulados
    ConOut("=== fPrcEst2 - TOTAIS ACUMULADOS ===")
    ConOut(">>> Matéria Prima (000001): " + cValToChar(nTotMP_Acum))
    ConOut(">>> Mão de Obra Direta (000002): " + cValToChar(nTotMOD_Acum))
    ConOut(">>> Beneficiamento (000003): " + cValToChar(nTotBen_Acum))
    ConOut(">>> Gastos Gerais (000004): " + cValToChar(nTotGG_Acum))
    ConOut(">>> Investimento/Ferramental (000009): " + cValToChar(nTotINV_Acum))
    ConOut(">>> Quantidade Total: " + cValToChar(nQtdTotal))
    ConOut("=====================================")
    
    // Calcula o total geral para cálculo de percentuais
    nTotalGeral := nTotMP_Acum + nTotMOD_Acum + nTotBen_Acum + nTotGG_Acum + nTotINV_Acum
    
    // ATUALIZA A LINHA 1 (PRODUTO PRINCIPAL) COM OS TOTAIS INCLUINDO GASTOS GERAIS
    ConOut(">>> fPrcEst2 - ATUALIZANDO LINHA 1 (PRODUTO PRINCIPAL)")
    oModelSZ91:GoLine(1)
    
    // ? Calcula valores BRUTOS e LÍQUIDOS separadamente
    // Os valores em nTotXX_Acum JÁ são os valores LÍQUIDOS (com impostos/frete aplicados)
    // Portanto, nTotalBrutoLinha1 = soma dos líquidos (valores calculados)
    nTotalBrutoLinha1 := nTotMP_Acum + nTotMOD_Acum + nTotBen_Acum + nTotGG_Acum + nTotINV_Acum
    
    // ??? ATUALIZA OS TRÊS CAMPOS (Unit Bruto, Total Bruto e Preço Líquido)
    oModelSZ91:LoadValue("Z9_VUNIT", nTotalBrutoLinha1)   // Unit Bruto ?
    oModelSZ91:LoadValue("Z9_TOTAL", nTotalBrutoLinha1)   // Total Bruto ?
    oModelSZ91:LoadValue("Z9_PRCLIQ", nTotalBrutoLinha1)  // Preço Líquido ?
    
    ConOut(">>> fPrcEst2 - LINHA 1 (PRODUTO PRINCIPAL) ATUALIZADA:")
    ConOut("    - Z9_VUNIT (Unit Bruto): " + cValToChar(nTotalBrutoLinha1) + " ?")
    ConOut("    - Z9_TOTAL (Total Bruto): " + cValToChar(nTotalBrutoLinha1) + " ?")
    ConOut("    - Z9_PRCLIQ (Preço Líquido): " + cValToChar(nTotalBrutoLinha1) + " ?")
    ConOut("    - Incluindo MP: " + cValToChar(nTotMP_Acum))
    ConOut("    - Incluindo MOD: " + cValToChar(nTotMOD_Acum))
    ConOut("    - Incluindo BEN: " + cValToChar(nTotBen_Acum))
    ConOut("    - Incluindo GG (tipo II): " + cValToChar(nTotGG_Acum) + " ???")
    ConOut("    - Incluindo INV: " + cValToChar(nTotINV_Acum))
    
    // SEGUNDA PASSADA: Preencher linhas de totalização com valores acumulados
    For N1 := 1 To   oModelSZ91:Length()
        oModelSZ91:GOLINE(n1)
        cCodProd := AllTrim(oModelSZ91:getvalue("Z9_CDPROD"))
        
        // Processa apenas linhas de totalização
        If cCodProd == "000001" // Matéria Prima
            oModelSZ91:LoadValue("Z9_QUANT", 1.0000)
            oModelSZ91:LoadValue("Z9_TOTAL", nTotMP_Acum)
            oModelSZ91:LoadValue("Z9_PRCLIQ", nTotMP_Acum)
            If nTotalGeral > 0
                oModelSZ91:LoadValue("Z9_PERCENT", Round((nTotMP_Acum / nTotalGeral) * 100, 2))
            Else
                oModelSZ91:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> fPrcEst2 - TOTALIZADOR 000001 (MP) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotMP_Acum) + " | Total=" + cValToChar(nTotMP_Acum))
            
        ElseIf cCodProd == "000002" // Mão de Obra Direta
            oModelSZ91:LoadValue("Z9_QUANT", 1.0000)
            oModelSZ91:LoadValue("Z9_TOTAL", nTotMOD_Acum)
            oModelSZ91:LoadValue("Z9_PRCLIQ", nTotMOD_Acum)
            If nTotalGeral > 0
                oModelSZ91:LoadValue("Z9_PERCENT", Round((nTotMOD_Acum / nTotalGeral) * 100, 2))
            Else
                oModelSZ91:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> fPrcEst2 - TOTALIZADOR 000002 (MOD) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotMOD_Acum) + " | Total=" + cValToChar(nTotMOD_Acum))
            
        ElseIf cCodProd == "000003" // Beneficiamento
            oModelSZ91:LoadValue("Z9_QUANT", 1.0000)
            oModelSZ91:LoadValue("Z9_TOTAL", nTotBen_Acum)
            oModelSZ91:LoadValue("Z9_PRCLIQ", nTotBen_Acum)
            If nTotalGeral > 0
                oModelSZ91:LoadValue("Z9_PERCENT", Round((nTotBen_Acum / nTotalGeral) * 100, 2))
            Else
                oModelSZ91:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> fPrcEst2 - TOTALIZADOR 000003 (BEN) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotBen_Acum) + " | Total=" + cValToChar(nTotBen_Acum))
            
        ElseIf cCodProd == "000004" // Gastos Gerais
            oModelSZ91:LoadValue("Z9_QUANT", 1.0000)
            oModelSZ91:LoadValue("Z9_TOTAL", nTotGG_Acum)
            oModelSZ91:LoadValue("Z9_PRCLIQ", nTotGG_Acum)
            If nTotalGeral > 0
                oModelSZ91:LoadValue("Z9_PERCENT", Round((nTotGG_Acum / nTotalGeral) * 100, 2))
            Else
                oModelSZ91:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> fPrcEst2 - TOTALIZADOR 000004 (GG) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotGG_Acum) + " | Total=" + cValToChar(nTotGG_Acum))
            
        ElseIf cCodProd == "000009" // Investimento/Ferramental
            oModelSZ91:LoadValue("Z9_QUANT", 1.0000)
            oModelSZ91:LoadValue("Z9_TOTAL", nTotINV_Acum)
            oModelSZ91:LoadValue("Z9_PRCLIQ", nTotINV_Acum)
            If nTotalGeral > 0
                oModelSZ91:LoadValue("Z9_PERCENT", Round((nTotINV_Acum / nTotalGeral) * 100, 2))
            Else
                oModelSZ91:LoadValue("Z9_PERCENT", 0)
            EndIf
            ConOut(">>> fPrcEst2 - TOTALIZADOR 000009 (INV) PREENCHIDO: Qtd=1 | Unit=" + cValToChar(nTotINV_Acum) + " | Total=" + cValToChar(nTotINV_Acum))
        EndIf
    next N1

    oModelSZ91:GoLine(1)
    oModelSZ92:GoLine(1)
    oModelSZ93:GoLine(1)
    
    ConOut("=== fPrcEst2 - FIM DO PROCESSAMENTO ===")
    
    If ValType( oView ) != "U" .and. !lAuto
        oView:Refresh("SZ9DETAIL01")
        oView:Refresh("SZ9DETAIL02")
        oView:Refresh("SZ9DETAIL03")
    endif

Return

/*/{Protheus.doc} fRPrc01

    Soma as Aliquotas e Recalcula os Valores
    - Pendente Recalcular os Valores
    @author  Gabriel Araujo
    @since   17-05-2021
/*/

Static Function fRPrc01()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local nAliq      := 0.00
    Local nCoefAliq  := 0.00
    Local nSomaEstrutura := 0.00
    Local nVlrTotal  := 0.00
    Local n1         := 0
    Local n2         := 0
    Local n3         := 0
    Local cCodProd   := ""
    Local lIsDeleted := .F.

    ConOut("=== fRPrc01 - INICIO DO RECALCULO ===")

    // PASSO 1: Soma todos os valores Z9_TOTAL da grid ESTRUTURA (oModelSZ9)
    // IMPORTANTE: Soma TODOS os produtos REAIS (não linhas de totalização)
    nSomaEstrutura := 0.00
    For n1 := 1 To oModelSZ9:Length()
        oModelSZ9:GOLINE(n1)

        // PULA A LINHA 1 (produto principal)
        If n1 == 1
            ConOut(">>> fRPrc01 - ESTRUTURA Linha 1 - PULADA (produto principal)")
            Loop
        EndIf
        
        // Verifica se a linha está deletada
        lIsDeleted := oModelSZ9:IsDeleted()
        
        If !lIsDeleted
            cCodProd := AllTrim(oModelSZ9:GetValue("Z9_CDPROD"))
            
            // Soma apenas linhas de produtos reais (não linhas de totalização)
            // Exclui apenas os códigos reservados para totalização: 000001 a 000009
            If !(cCodProd $ "000001|000002|000003|000004|000005|000006|000007|000008|000009")
                nVlrTotal := oModelSZ9:GetValue("Z9_TOTAL")
                nSomaEstrutura += nVlrTotal
                ConOut(">>> fRPrc01 - ESTRUTURA Linha " + cValToChar(n1) + " [" + cCodProd + "]: " + cValToChar(nVlrTotal) + " | Acumulado: " + cValToChar(nSomaEstrutura))
            Else
                ConOut(">>> fRPrc01 - ESTRUTURA Linha " + cValToChar(n1) + " [" + cCodProd + "] - TOTALIZADOR (ignorado)")
            EndIf
        Else
            ConOut(">>> fRPrc01 - ESTRUTURA Linha " + cValToChar(n1) + " - DELETADA (ignorada)")
        EndIf
    next n1
    
    ConOut(">>> fRPrc01 - SOMA TOTAL da ESTRUTURA (produtos reais): " + cValToChar(nSomaEstrutura))

    // PASSO 2: Calcula a alíquota do COEFICIENTE (Mark-up Impostos)
    // Soma todas as alíquotas exceto a última linha (que é o coeficiente)
    nAliq := 0.00
    For n2 := 1 To oModelSZ92:Length()
        oModelSZ92:GOLINE(n2)

        if n2 == oModelSZ92:Length()
            // Última linha = COEFICIENTE (100 - soma das alíquotas anteriores)
            nCoefAliq := 100 - nAliq
            oModelSZ92:SetValue("Z9_ALIQ", nCoefAliq)
            ConOut(">>> fRPrc01 - Mark-up Impostos - Alíquota COEFICIENTE: " + cValToChar(nCoefAliq) + "%")
        else
            nAliq += oModelSZ92:GetValue("Z9_ALIQ")
            ConOut(">>> fRPrc01 - Mark-up Impostos Linha " + cValToChar(n2) + " - Alíquota: " + cValToChar(oModelSZ92:GetValue("Z9_ALIQ")) + "% | Soma Parcial: " + cValToChar(nAliq) + "%")
        endif
    next n2

    // PASSO 3: Calcula a alíquota do COEFICIENTE (Mark-up Operacional)
    nAliq := 0.00
    For n3 := 1 To oModelSZ93:Length()
        oModelSZ93:GOLINE(n3)

        if n3 == oModelSZ93:Length()
            // Última linha = COEFICIENTE
            oModelSZ93:SetValue("Z9_ALIQ", 100 - nAliq)
            ConOut(">>> fRPrc01 - Mark-up Operacional - Alíquota COEFICIENTE: " + cValToChar(100 - nAliq) + "%")
        else
            nAliq += oModelSZ93:GetValue("Z9_ALIQ")
            ConOut(">>> fRPrc01 - Mark-up Operacional Linha " + cValToChar(n3) + " - Alíquota: " + cValToChar(oModelSZ93:GetValue("Z9_ALIQ")) + "% | Soma Parcial: " + cValToChar(nAliq) + "%")
        endif
    next n3

    // PASSO 4: ATUALIZA OS TRÊS PONTOS COM O SOMATÓRIO DA ESTRUTURA
    ConOut(">>> fRPrc01 - ATUALIZANDO OS TRÊS PONTOS COM SOMA DA ESTRUTURA: " + cValToChar(nSomaEstrutura))
    
    // 1. Atualiza Z9_TOTAL na última linha da grid Mark-up Impostos
    oModelSZ92:GOLINE(oModelSZ92:Length())
    oModelSZ92:SetValue("Z9_TOTAL", nSomaEstrutura)
    ConOut(">>> fRPrc01 - [1/2] Mark-up Impostos linha " + cValToChar(oModelSZ92:Length()) + " (Z9_TOTAL) = " + cValToChar(nSomaEstrutura))
    
    // 2. Atualiza Z9_TOTAL na última linha da grid Mark-up Operacional
    oModelSZ93:GOLINE(oModelSZ93:Length())
    oModelSZ93:SetValue("Z9_TOTAL", nSomaEstrutura)
    ConOut(">>> fRPrc01 - [2/2] Mark-up Operacional linha " + cValToChar(oModelSZ93:Length()) + " (Z9_TOTAL) = " + cValToChar(nSomaEstrutura))
    
    // NOTA: NÃO atualiza Z8_PVSUGER aqui pois o COEFICIENTE do Mark-up Impostos
    // ainda não foi calculado (será calculado em fPrcRecal). 
    // O Z8_PVSUGER será definido em fSetPVen() após fPrcRecal() completar.
    ConOut(">>> fRPrc01 - Z8_PVSUGER NÃO atualizado aqui (será feito em fSetPVen após fPrcRecal)")

    // Retorna para primeira linha de cada grid
    oModelSZ9:GoLine(1)
    oModelSZ92:GoLine(1)
    oModelSZ93:GoLine(1)
    
    ConOut("=== fRPrc01 - FIM DO RECALCULO - ALÍQUOTAS E BASES ATUALIZADAS ===")
    
    // Refresh das views
    If ValType( oView ) != "U" .and. !lAuto
        oView:Refresh("SZ9DETAIL01")
        oView:Refresh("SZ9DETAIL02")
        oView:Refresh("SZ9DETAIL03")
        ConOut(">>> fRPrc01 - Views atualizadas")
    endif
Return
Static Function fRPrc02()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    Local nSomaEstrutura := 0.00
    Local nVlrTotal  := 0.00
    Local n1         := 0
    Local cCodProd   := ""
    Local lIsDeleted := .F.
    Local nTZ9DESC  := getsx3cache("Z9_DESC","X3_TAMANHO")

    ConOut("=== fRPrc02 - INICIO DO RECALCULO ===")

    // PASSO 1: Soma todos os valores Z9_TOTAL da grid ESTRUTURA (oModelSZ9)
    // IMPORTANTE: Soma TODOS os produtos REAIS (não linhas de totalização)
    nSomaEstrutura := 0.00
    For n1 := 1 To oModelSZ9:Length()
        oModelSZ9:GOLINE(n1)

        // PULA A LINHA 1 (produto principal)
        If n1 == 1
            ConOut(">>> fRPrc02 - ESTRUTURA Linha 1 - PULADA (produto principal)")
            Loop
        EndIf
        
        // Verifica se a linha está deletada
        lIsDeleted := oModelSZ9:IsDeleted()
        
        If !lIsDeleted
            cCodProd := AllTrim(oModelSZ9:GetValue("Z9_CDPROD"))
            
            // Soma apenas linhas de produtos reais (não linhas de totalização)
            // Exclui apenas os códigos reservados para totalização: 000001 a 000009
            If !(cCodProd $ "000001|000002|000003|000004|000005|000006|000007|000008|000009")
                nVlrTotal := oModelSZ9:GetValue("Z9_TOTAL")
                nSomaEstrutura += nVlrTotal
                ConOut(">>> fRPrc02 - ESTRUTURA Linha " + cValToChar(n1) + " [" + cCodProd + "]: " + cValToChar(nVlrTotal) + " | Acumulado: " + cValToChar(nSomaEstrutura))
            Else
                ConOut(">>> fRPrc02 - ESTRUTURA Linha " + cValToChar(n1) + " [" + cCodProd + "] - TOTALIZADOR (ignorado)")
            EndIf
        Else
            ConOut(">>> fRPrc02 - ESTRUTURA Linha " + cValToChar(n1) + " - DELETADA (ignorada)")
        EndIf
    next n1
    
    ConOut(">>> fRPrc02 - SOMA TOTAL da ESTRUTURA (produtos reais): " + cValToChar(nSomaEstrutura))

    // PASSO 2: ATUALIZA AS BASES COM O SOMATÓRIO DA ESTRUTURA
    ConOut(">>> fRPrc02 - ATUALIZANDO BASES COM SOMA DA ESTRUTURA: " + cValToChar(nSomaEstrutura))
    
    // 1. Atualiza Z9_TOTAL na última linha da grid Mark-up Impostos
    oModelSZ92:GOLINE(oModelSZ92:Length())
    oModelSZ92:SetValue("Z9_TOTAL", nSomaEstrutura)
    ConOut(">>> fRPrc02 - [1/2] Mark-up Impostos linha " + cValToChar(oModelSZ92:Length()) + " (Z9_TOTAL) = " + cValToChar(nSomaEstrutura))
    
    // 2. Atualiza Z9_TOTAL na última linha da grid Mark-up Operacional
    oModelSZ93:GOLINE(oModelSZ93:Length())
    oModelSZ93:SetValue("Z9_TOTAL", nSomaEstrutura)
    ConOut(">>> fRPrc02 - [2/2] Mark-up Operacional linha " + cValToChar(oModelSZ93:Length()) + " (Z9_TOTAL) = " + cValToChar(nSomaEstrutura))
    
    // NOTA: NÃO atualiza Z8_PVSUGER aqui pois o COEFICIENTE do Mark-up Impostos
    // ainda não foi calculado (será calculado em fPrcRecal). 
    // O Z8_PVSUGER será definido em fSetPVen() após fPrcRecal() completar.
    ConOut(">>> fRPrc02 - Z8_PVSUGER NÃO atualizado aqui (será feito em fSetPVen após fPrcRecal)")

    // Retorna para primeira linha de cada grid
    oModelSZ9:GoLine(1)
    oModelSZ92:GoLine(1)
    oModelSZ93:GoLine(1)
    
    ConOut("=== fRPrc02 - FIM DO RECALCULO - BASES ATUALIZADAS ===")
    
    // Refresh das views
    If ValType( oView ) != "U" .and. !lAuto
        oView:Refresh("SZ9DETAIL01")
        oView:Refresh("SZ9DETAIL02")
        oView:Refresh("SZ9DETAIL03")
        ConOut(">>> fRPrc02 - Views atualizadas")
    endif
REturn

Static Function fPrcEst3()
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ9  := oModel:GetModel("SZ9DETAIL01")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
    lOCAL cIdSZ8 := oModelSZ8:GETVALUE("Z8_ID")
    lOCAL cIdSZ7 := oModelSZ8:GETVALUE("Z8_IDSZ7")
    Local nTZ9CDPRD  := getsx3cache("Z9_CDPROD","X3_TAMANHO")
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local nTot1 := 0.00
    Local nTot2 := 0.00
    cSql :="SELECT * FROM dbo." + retsqlname("SZ7") + " SZ7 " + cEol
    cSql +="WHERE D_E_L_E_T_='' AND Z7_ID = " + VALTOSQL(cIdSZ7) + " AND Z7_FOLDER='1PRD01' " + cEol
    cSql +="ORDER BY Z7_ITEM "

    // aTPPrd := {}
    If Select('TMPEST') <> 0
        TMPEST->(dbCloseArea())
    Endif

    TCQuery cSql Alias TMPEST New
    While TMPEST->(!eof())

        cSeek1 :=  TMPEST->Z7_CAMPO
        cSeek2 :=  PADR(ALLTRIM(TMPEST->Z7_DESCCMP),nTZ9DESC)
        cTpPrd :=  TMPEST->Z7_FORMULA

        nPos  :=  ascan(aTPPrd,{|x| Trim(x[1]) $ alltrim(cTpPrd) })
        if nPos > 0
            if  oModelSZ9:SeekLine({{"Z9_CDPROD",cSeek1},{"Z9_DESC",cSeek2}})

                oModelSZ9:SETvalue("Z9_TOTAL",aTPPrd[nPos][2])
                oModelSZ9:SETvalue("Z9_PRCLIQ",aTPPrd[nPos][3])
                nTot1 += aTPPrd[nPos][2]
                nTot2 += aTPPrd[nPos][3]

            endif

        endif
        TMPEST->(dbskip())

    Enddo
    TMPEST->(dbCloseArea())

    oModelSZ9:GoLine(1)
    oModelSZ9:SETvalue("Z9_TOTAL" ,nTot1)
    oModelSZ9:SETvalue("Z9_PRCLIQ",nTot2)
    oModelSZ92:GoLine(1)
    oModelSZ93:GoLine(1)
    // If Type( 'oView' ) != "U"
    If ValType( oView ) != "U" .and. !lAuto
        oView:Refresh("SZ9DETAIL01")
        oView:Refresh("SZ9DETAIL02")
        oView:Refresh("SZ9DETAIL03")
    endif
rETURN


Static Function D02F02G()
    Local aArea     := getarea()
    Local lRet      := .t.
    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
    Local nVUnit     := 0
    Local nVTot      := 0
    Local nQtd       := 0
    //Z9_TABPRCC
    //Z9_PRCLIQ
    //Z9_PERCENT
    //Z9_VUNIT
    cProd    :=  oModelSZ91:GETVALUE("Z9_CDPROD")
    cTab     :=  oModelSZ91:GETVALUE("Z9_TABPRCC")
    cObs     :=  oModelSZ91:GETVALUE("Z9_OBS")
    cCodFor  :=  Substr(cObs,1,6)+ Substr(cObs,8,2)
    //  cLojFor := Substr(cObs,8,2)
    //AIB_FILIAL, AIB_CODFOR, AIB_LOJFOR, AIB_CODTAB, AIB_CODPRO, R_E_C_N_O_, D_E_L_E_T_
    nVUnit   := POSICIONE("AIB",2,XFILIAL("AIB")+cCodFor+cTab+cProd,"AIB_PRCCOM")
    RESTAREA(aArea)

Return nVUnit


Static Function D02F02H()
    Local aArea     := getarea()
    Local lRet      := .t.
    Local oModel    := FWMODELACTIVE()
    Local oView     := Nil //FWViewActive()

    Local oModelSZ8 := Nil // oModel:GetModel("SZ8MASTER")
    //  Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
    Local nVUnit := 0
    Local nVTot := 0
    Local nQtd := 0

    If oModel != Nil .AND. oModel:IsActive()

        oModelSZ8 := oModel:GetModel("SZ8MASTER")
        //   //Z9_TABPRCC
        //   //Z9_PRCLIQ
        //   //Z9_PERCENT
        //   // DA0_FILIAL, DA0_CODTAB, R_E_C_N_O_, D_E_L_E_T_
        cTab    :=  oModelSZ8:GETVALUE("Z8_CDTABVN")
        cPrd    :=  oModelSZ8:GETVALUE("Z8_COD")
        DBSELECTAREA("DA0")
        DA0->(dbSetOrder(1))
        IF DA0->(DBSeek(xFilial("DA0")+cTab))
            Desc  := DA0->DA0_DESCRI
        ELSE
            lRet := .f.
            MsgInfo("Tabela de Preco Invalida","Delpi")
        endif
        if lRet
            DBSELECTAREA("DA1")
            DA1->(dbSetOrder(1))
            IF DA1->(DBSeek(xFilial("DA1")+cTab+cPrd))
                nVlr    :=   DA1->DA1_PRCVEN
            ELSE
                lRet := .f.
                MsgInfo("Tabela de Preco Invalida","Delpi")
            endif
        endif

        if lRet
            lCanAlt := .T.
            oModelSZ8:SETVALUE("Z8_PVTAB",nVlr)
            oModelSZ8:SETVALUE("Z8_DSCTAB",Desc)
            lCanAlt := .F.
        ENDIF

    endif
    RESTAREA(aArea)
Return lRet


/*/{Protheus.doc} fSetPVen

    Responsvel por calcular a Margem e o Preco de venda da rotina

    @author  Name
    @example Example
    @param   [Parameter_Name],Parameter_type,Parameter_Description
    @return  Return
    @table   Tables
    @since   03-12-2021
/*/


Static Function fSetPVen()

    Local oModel    := FWMODELACTIVE()
    Local oView     := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
    Local nTZ9DESC   := getsx3cache("Z9_DESC","X3_TAMANHO")
    Local nI         := 0
    Local lAchou     := .F.

    ConOut("=== fSetPVen - INICIO ===")

    // =====================================================================
    // CORREÇÃO: Buscar o valor do COEFICIENTE pela descrição "COEFICIENTE"
    // ao invés de usar a última linha da grid (que pode ser LUCRO, IR, etc.)
    // O COEFICIENTE (linha 003) contém o PV Sugerido calculado sequencialmente
    // =====================================================================
    nPv := 0
    For nI := 1 To oModelSZ92:Length()
        oModelSZ92:GoLine(nI)
        If AllTrim(oModelSZ92:GetValue("Z9_DESC")) $ "COEFICIENTE"
            nPv := oModelSZ92:GetValue("Z9_TOTAL")
            lAchou := .T.
            ConOut(">>> fSetPVen - COEFICIENTE encontrado na linha " + cValToChar(nI) + " | Z9_TOTAL = " + cValToChar(nPv))
            Exit
        EndIf
    Next nI
    
    // Fallback: se não encontrou COEFICIENTE, tenta a última linha (comportamento antigo)
    If !lAchou
        oModelSZ92:GoLine(oModelSZ92:Length())
        nPv := oModelSZ92:GetValue("Z9_TOTAL")
        ConOut(">>> fSetPVen - COEFICIENTE não encontrado, usando última linha " + cValToChar(oModelSZ92:Length()) + " | Z9_TOTAL = " + cValToChar(nPv))
    EndIf

    nPVTab   := oModelSZ8:getvalue("Z8_PVTAB")
    lCanAlt  := .t.
    oModelSZ8:setvalue("Z8_PVSUGER",nPv)
    ConOut(">>> fSetPVen - Z8_PVSUGER ATUALIZADO = " + cValToChar(nPv))

    /*TRATATIVA PARA MARCAR O PRODUTO COMO PENDENTE VALIDA O PRECO SUGERIDO X PRECO TABELA COM BASE NOS PARAMTROS*/
    if lAuto
        if lVldPrcVd
            if  ROUND(nPv,4) !=  nPVTab
                oModelSZ8:setvalue("Z8_SITUA","P")
            ELSE
                oModelSZ8:setvalue("Z8_SITUA","A")
            endif
        endif
    endif

    if nPv  == 0.00

        nMargem := 0.00

    elseif  nPVTab == 0.00

        nMargem := 100.00

    else

        //   nMargem   := round( ((( nPVTab/nPv)-1)*100),4)
        nMargem   := round( (((nPv/nPVTab)-1)*100),4)

    endif
    nMargem>100
    oModelSZ8:setvalue("Z8_MARGEM",iif(nMargem>100,100.00,nMargem))
    ConOut(">>> fSetPVen - Margem = " + cValToChar(iif(nMargem>100,100.00,nMargem)) + "% | PV Sugerido = " + cValToChar(nPv) + " | PV Tabela = " + cValToChar(nPVTab))
    lCanAlt := .f.
    oModelSZ92:GoLine(1)
    // If Type( 'oView' ) != "U"
    If ValType( oView ) != "U" .and. !lAuto
        oView:Refresh("SZ9DETAIL01")
        oView:Refresh("SZ9DETAIL02")
        oView:Refresh("SZ8MASTER")
    endif
    ConOut("=== fSetPVen - FIM ===")
Return

/*/{Protheus.doc} Print
    Função responsavel para gerar o objeto de impressao da formação de preco
    @type  Function
    @author Gabriel Araujo
    @since 03/12/2021

/*/
Static Function Print(oView)
    Local oModel := oView:GetModel()
    Local oReport

    oReport := oModel:ReportDef()
    oReport:PrintDialog()

Return


/*/{Protheus.doc} fLegend
Função para legenda do Browse
/*/
Static Function fLegend()
    /* Local oLegend  :=  FWLegend():New()
    oLegend:Add("","BR_BRANCO", STR0040 ) // Carga Não Gerada
    oLegend:Add("","BR_AZUL", STR0041 ) // Carga Gerada
    oLegend:Add("","BR_VERDE", STR0042 ) // Carga Faturada
    oLegend:Add("","BR_AMARELO", STR0043 ) // Carga Monitorada
    oLegend:Activate()
    oLegend:View()
    oLegend:DeActivate()*/
Return
//oBrowse:AddStatusColumns({||StatusCarg((cAliasTMP)->TMP_SITCAR)}, {||LegendCarg()})


/*/{Protheus.doc} fStatusCal
Status da viagem
@author amanda.vieira
@since 12/09/2019
@version 1.0
/*/
Static Function fStatusCal(cStatus)
    Local cRetorno := "BR_LARANJA"
    Default cStatus := "0"
    /* If cStatus == "0" //Recebida
        cRetorno := "BR_LARANJA"
    ElseIf cStatus == "1" // Aguardando Liberação
        cRetorno := "BR_CINZA"
    ElseIf cStatus == "2" // Liberada
        cRetorno := "BR_VERDE"
    ElseIf cStatus == "3" // Falha Liberação
        cRetorno := "BR_VERMELHO"
    ElseIf cStatus = "4" // Reprogramada
        cRetorno := "BR_MARROM"
    ElseIf cStatus == "5" // Cancelada
        cRetorno := "BR_PRETO"
    ElseIf cStatus == "6" // Rejeitada
        cRetorno := "BR_AMARELO"
    Else
        cRetorno := "BR_BRANCO" //Sem viagem
    EndIf*/
Return cRetorno



user  Function DLPD2FOP(nOpc)

    Local oModel        := FwLoadModel("DLP02F02")
    Local oModel        := FwLoadModel("DLP02F02")
    Local cFiltSZ9      := ""

    IF nOpc == 2
        cFiltSZ9 := fD02FltSZ9(SZ8->Z8_ID, SZ8->Z8_FILIAL, SZ8->Z8_COD)
        oModel:GetModel('SZ9DETAIL01'):SetLoadFilter(, cFiltSZ9)
        oModel:GetModel('SZ9DETAIL02'):SetLoadFilter(, cFiltSZ9)
        oModel:GetModel('SZ9DETAIL03'):SetLoadFilter(, cFiltSZ9)
        nRet := FWExecView("", "DLP02F02", 1, /*oDlg*/, {|| .T. }, /*bOk*/ , /*nPercReducao*/, /*aEnableButtons*/, /*bCancel*/ , /*cOperatId*/, /*cToolBar*/, oModel)
    ELSEIF nOpc == 3
        aFltSZ9   := {}
        aadd(aFltSZ9, {"Z9_FILMOV","'"+XFILIAL("SZ8")+"'" })
        oModel:GetModel('SZ9DETAIL01'):SetLoadFilter(aFltSZ9)
        oModel:GetModel('SZ9DETAIL02'):SetLoadFilter(aFltSZ9)
        oModel:GetModel('SZ9DETAIL03'):SetLoadFilter(aFltSZ9)
        nRet := FWExecView("", "DLP02F02", OP_INCLUIR, /*oDlg*/, {|| .T. }, /*bOk*/ , /*nPercReducao*/, /*aEnableButtons*/, /*bCancel*/ , /*cOperatId*/, /*cToolBar*/, oModel)
    ELSEIF nOpc == 4

        cFiltSZ9 := fD02FltSZ9(SZ8->Z8_ID, SZ8->Z8_FILIAL, SZ8->Z8_COD)
        oModel:GetModel('SZ9DETAIL01'):SetLoadFilter(, cFiltSZ9)
        oModel:GetModel('SZ9DETAIL02'):SetLoadFilter(, cFiltSZ9)
        oModel:GetModel('SZ9DETAIL03'):SetLoadFilter(, cFiltSZ9)
        nRet := FWExecView("", "DLP02F02", OP_ALTERAR, /*oDlg*/, {|| .T. }, /*bOk*/ , /*nPercReducao*/, /*aEnableButtons*/, /*bCancel*/ , /*cOperatId*/, /*cToolBar*/, oModel)
    ELSEIF nOpc == 5
        cFiltSZ9 := fD02FltSZ9(SZ8->Z8_ID, SZ8->Z8_FILIAL, SZ8->Z8_COD)
        oModel:GetModel('SZ9DETAIL01'):SetLoadFilter(, cFiltSZ9)
        oModel:GetModel('SZ9DETAIL02'):SetLoadFilter(, cFiltSZ9)
        oModel:GetModel('SZ9DETAIL03'):SetLoadFilter(, cFiltSZ9)
        nRet := FWExecView("", "DLP02F02", OP_EXCLUIR, /*oDlg*/, {|| .T. }, /*bOk*/ , /*nPercReducao*/, /*aEnableButtons*/, /*bCancel*/ , /*cOperatId*/, /*cToolBar*/, oModel)
    ENDIF


/*/{Protheus.doc} zCopyMVC
    Função de cópia de registros MVC - Formação de Preço
    Copia o registro posicionado (cabeçalho e todas as 3 grids) gerando um novo ID
    
    @type function
    @author Pedro Koerich
    @since 26/01/2026
    @version 1.0
    
    @return object, Modelo MVC carregado
    
    @obs Grid 1 (SZ9DETAIL01 - 1PRD01): Estrutura - Copia todos os campos
    @obs Grid 2 (SZ9DETAIL02 - 3IMP01): Impostos - Copia apenas Z9_DESC, Z9_ALIQ, Z9_TOTAL
    @obs Grid 3 (SZ9DETAIL03 - 2OPE01): Operacional - Copia apenas Z9_DESC, Z9_ALIQ, Z9_TOTAL
    
    @example
    U_zCopyMVC()
/*/
User Function zCopyMVC()
    Local aArea        := GetArea()
    Local aAreaSZ8     := SZ8->(GetArea())
    Local aAreaSZ9     := SZ9->(GetArea())
    Local cTitulo      := "Cópia - Formação de Preço"
    Local cPrograma    := "DLP02F02"
    Local nOperation   := MODEL_OPERATION_INSERT
    Local nLin         := 0
    Local nCol         := 0
    Local cIdOrig      := ""
    Local cNovoId      := ""
    Local nRet         := 0
    Local oModel       := Nil
    Local oModelSZ8    := Nil
    Local oModelSZ91   := Nil
    Local oModelSZ92   := Nil
    Local oModelSZ93   := Nil
    Local oStruct      := Nil
    Local aCampos      := {}
    Local aDadosSZ8    := {}
    Local aDadosSZ91   := {}
    Local aDadosSZ92   := {}
    Local aDadosSZ93   := {}
    Local cCampo       := ""
    Local xValor       := Nil
    Local lContinua    := .T.
    Local cFilOrig     := ""

    // Valida se há registro posicionado
    If SZ8->(Eof()) .Or. SZ8->(Bof())
        MsgInfo("Posicione em um registro válido para realizar a cópia!", "Atenção")
        RestArea(aAreaSZ9)
        RestArea(aAreaSZ8)
        RestArea(aArea)
        Return Nil
    EndIf
    
    // Guarda o ID original
    cIdOrig := SZ8->Z8_ID
    cFilOrig := SZ8->Z8_FILIAL

    // ========================================
    // COLETA OS DADOS DO REGISTRO POSICIONADO
    // ========================================
    
    // Coleta dados do cabeçalho (SZ8)
    DbSelectArea("SZ8")
    DbSetOrder(1) // Z8_FILIAL + Z8_ID
    If SZ8->(MsSeek(cFilOrig + cIdOrig))
        oStruct := FWFormStruct(1, 'SZ8')
        aCampos := oStruct:GetFields()
        
        For nCol := 1 To Len(aCampos)
            cCampo := AllTrim(aCampos[nCol][3])
            
            // Ignora campos de controle e chave
            If !(cCampo $ "Z8_ID|Z8_FILIAL|Z8_DTAPROV|Z8_IDAPROV|Z8_ULTPV|Z8_DTULTPV|Z8_SITUA|Z8_PVTMP|Z8_DTEMISS")
                xValor := SZ8->&(cCampo)
                aAdd(aDadosSZ8, {cCampo, xValor})
                // Log para rastrear campos copiados com valor
                If cCampo == "Z8_PVSUGER"
                    ConOut(">>> CÓPIA: Z8_PVSUGER coletado = " + cValToChar(xValor))
                EndIf
            EndIf
        Next nCol
    Else
        MsgInfo("Erro ao localizar o registro para cópia!", "Atenção")
        lContinua := .F.
    EndIf
    
    // Coleta dados dos itens - Grid 1 (Estrutura - 1PRD01)
    // Grid 1 copia TODOS os campos da estrutura
    If lContinua
        DbSelectArea("SZ9")
        DbSetOrder(1) // Z9_FILIAL + Z9_IDZ8 + Z9_IDFLD + Z9_ITEM
        If SZ9->(MsSeek(cFilOrig + cIdOrig + "1PRD01"))
            While SZ9->(!Eof()) .And. SZ9->Z9_FILIAL == cFilOrig .And. SZ9->Z9_IDZ8 == cIdOrig .And. SZ9->Z9_IDFLD == "1PRD01"
                aLinha  := {}
                
                // Verifica se é linha de totalização (códigos 000001, 000002, 000003, 000004, 000009)
                lLinhaTotal := AllTrim(SZ9->Z9_CDPROD) $ "000001|000002|000003|000004|000009"
                
                // Grid 1 - Estrutura - Copia TODOS os campos necessários
                If !Empty(SZ9->Z9_CDPROD)
                    aAdd(aLinha, {"Z9_CDPROD", SZ9->Z9_CDPROD})
                EndIf
                If !Empty(SZ9->Z9_DESC)
                    aAdd(aLinha, {"Z9_DESC", SZ9->Z9_DESC})
                EndIf
                
                // Para linhas de totalização, zera os valores numéricos
                If lLinhaTotal
                    ConOut(">>> CÓPIA: Zerando valores da linha totalizadora: " + AllTrim(SZ9->Z9_CDPROD))
                    aAdd(aLinha, {"Z9_QUANT", 0})
                    aAdd(aLinha, {"Z9_VUNIT", 0})
                    aAdd(aLinha, {"Z9_TOTAL", 0})
                    aAdd(aLinha, {"Z9_ALIQ", 0})
                    aAdd(aLinha, {"Z9_PERCENT", 0})
                    aAdd(aLinha, {"Z9_PRCLIQ", 0})
                Else
                    // Para linhas normais, copia os valores originais
                    aAdd(aLinha, {"Z9_QUANT", SZ9->Z9_QUANT})
                    aAdd(aLinha, {"Z9_VUNIT", SZ9->Z9_VUNIT})
                    aAdd(aLinha, {"Z9_TOTAL", SZ9->Z9_TOTAL})
                    aAdd(aLinha, {"Z9_ALIQ", SZ9->Z9_ALIQ})
                    aAdd(aLinha, {"Z9_PERCENT", SZ9->Z9_PERCENT})
                    aAdd(aLinha, {"Z9_PRCLIQ", SZ9->Z9_PRCLIQ})
                EndIf
                
                // Campos opcionais
                If !Empty(SZ9->Z9_TABPRCC)
                    aAdd(aLinha, {"Z9_TABPRCC", SZ9->Z9_TABPRCC})
                EndIf
                If !Empty(SZ9->Z9_OBS)
                    aAdd(aLinha, {"Z9_OBS", SZ9->Z9_OBS})
                EndIf
                
                If Len(aLinha) > 0
                    aAdd(aDadosSZ91, aLinha)
                EndIf
                SZ9->(DbSkip())
            EndDo
        EndIf
    EndIf
    
    // Coleta dados dos itens - Grid 2 (Impostos - 3IMP01)
    // Campos REMOVIDOS do modelo SZ9DETAIL02: Z9_OBS, Z9_QUANT, Z9_VUNIT, Z9_PERCENT, Z9_CDPROD, Z9_PRCLIQ, Z9_TABPRCC
    If lContinua
        DbSelectArea("SZ9")
        DbSetOrder(1)
        If SZ9->(MsSeek(cFilOrig + cIdOrig + "3IMP01"))
            While SZ9->(!Eof()) .And. SZ9->Z9_FILIAL == cFilOrig .And. SZ9->Z9_IDZ8 == cIdOrig .And. SZ9->Z9_IDFLD == "3IMP01"
                aLinha  := {}
                
                // Grid 2 - Impostos - Copia TODAS as linhas com campos: Z9_DESC, Z9_ALIQ, Z9_TOTAL
                If !Empty(SZ9->Z9_DESC)
                    aAdd(aLinha, {"Z9_DESC", SZ9->Z9_DESC})
                EndIf
                // Sempre adiciona ALIQ e TOTAL, mesmo se zerados
                aAdd(aLinha, {"Z9_ALIQ", SZ9->Z9_ALIQ})
                aAdd(aLinha, {"Z9_TOTAL", SZ9->Z9_TOTAL})
                
                If Len(aLinha) > 0
                    aAdd(aDadosSZ92, aLinha)
                EndIf
                SZ9->(DbSkip())
            EndDo
        EndIf
    EndIf
    
    // Coleta dados dos itens - Grid 3 (Operacional - 2OPE01)
    // Campos REMOVIDOS do modelo SZ9DETAIL03: Z9_OBS, Z9_QUANT, Z9_VUNIT, Z9_PERCENT, Z9_CDPROD, Z9_PRCLIQ, Z9_TABPRCC
    If lContinua
        DbSelectArea("SZ9")
        DbSetOrder(1)
        If SZ9->(MsSeek(cFilOrig + cIdOrig + "2OPE01"))
            While SZ9->(!Eof()) .And. SZ9->Z9_FILIAL == cFilOrig .And. SZ9->Z9_IDZ8 == cIdOrig .And. SZ9->Z9_IDFLD == "2OPE01"
                aLinha  := {}
                
                // Grid 3 - Operacional - Copia TODAS as linhas com campos: Z9_DESC, Z9_ALIQ, Z9_TOTAL
                If !Empty(SZ9->Z9_DESC)
                    aAdd(aLinha, {"Z9_DESC", SZ9->Z9_DESC})
                EndIf
                // Sempre adiciona ALIQ e TOTAL, mesmo se zerados
                aAdd(aLinha, {"Z9_ALIQ", SZ9->Z9_ALIQ})
                aAdd(aLinha, {"Z9_TOTAL", SZ9->Z9_TOTAL})
                
                If Len(aLinha) > 0
                    aAdd(aDadosSZ93, aLinha)
                EndIf
                SZ9->(DbSkip())
            EndDo
        EndIf
    EndIf
    
    // ========================================
    // CRIA O NOVO REGISTRO COM OS DADOS COPIADOS
    // ========================================
    
    If lContinua
        // Caso precise testar em algum lugar
        __lCopia := .T.
        
        // Ativa flag para permitir edição de campos protegidos durante a cópia
        lCanAlt := .T.
        
        // Carrega o modelo de dados
        oModel := FWLoadModel(cPrograma)
        oModel:SetOperation(nOperation) // Inclusão
        oModel:Activate()
        
        // Gera novo ID
        cNovoId := GetSXENum("SZ8", "Z8_ID")
        ConfirmSX8()
        
        // Pega os modelos
        oModelSZ8  := oModel:GetModel("SZ8MASTER")
        oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
        oModelSZ92 := oModel:GetModel("SZ9DETAIL02")
        oModelSZ93 := oModel:GetModel("SZ9DETAIL03")
        
        // Seta o novo ID
        oModelSZ8:LoadValue("Z8_ID", cNovoId)
        
        // Preenche os campos do cabeçalho
        For nLin := 1 To Len(aDadosSZ8)
            cCampo := aDadosSZ8[nLin][1]
            xValor := aDadosSZ8[nLin][2]
            
            // Adiciona prefixo "COP - " na descrição do produto
            If cCampo == "Z8_DSCPRD"
                xValor := "COP - " + AllTrim(xValor)
            EndIf
            
            oModelSZ8:LoadValue(cCampo, xValor)
        Next nLin
        
        // Preenche Grid 1 - Estrutura (SZ9DETAIL01)
        For nLin := 1 To Len(aDadosSZ91)
            If nLin > 1
                oModelSZ91:AddLine()
            EndIf
            
            oModelSZ91:GoLine(nLin)
            
            // Preenche campos de controle obrigatï¿½rios usando SetValue
            oModelSZ91:LoadValue("Z9_FILMOV", cFilAnt)
            oModelSZ91:LoadValue("Z9_IDZ8", cNovoId)
            oModelSZ91:LoadValue("Z9_IDFLD", "1PRD01")
            
            // Preenche os demais campos da linha
            For nCol := 1 To Len(aDadosSZ91[nLin])
                cCampo := aDadosSZ91[nLin][nCol][1]
                xValor := aDadosSZ91[nLin][nCol][2]
                
                // Ignora campos de controle (já preenchidos acima)
                If !(cCampo $ "Z9_FILMOV|Z9_IDZ8|Z9_IDFLD")
                    oModelSZ91:LoadValue(cCampo, xValor)
                EndIf
            Next nCol
        Next nLin
        
        // Preenche Grid 2 - Impostos (SZ9DETAIL02)
        // IMPORTANTE: Usa LoadValue para não disparar triggers que possam zerar Z9_TOTAL
        For nLin := 1 To Len(aDadosSZ92)
            If nLin > 1
                oModelSZ92:AddLine()
            EndIf
            
            oModelSZ92:GoLine(nLin)
            
            // Preenche campos de controle obrigatï¿½rios usando LoadValue
            oModelSZ92:LoadValue("Z9_FILMOV", cFilAnt)
            oModelSZ92:LoadValue("Z9_IDZ8", cNovoId)
            oModelSZ92:LoadValue("Z9_IDFLD", "3IMP01")
            
            // Preenche os demais campos da linha
            For nCol := 1 To Len(aDadosSZ92[nLin])
                cCampo := aDadosSZ92[nLin][nCol][1]
                xValor := aDadosSZ92[nLin][nCol][2]
                
                // Apenas campos permitidos no modelo: Z9_DESC, Z9_ALIQ, Z9_TOTAL
                If cCampo $ "Z9_DESC|Z9_ALIQ|Z9_TOTAL"
                    oModelSZ92:LoadValue(cCampo, xValor)
                EndIf
            Next nCol
        Next nLin
        
        // Preenche Grid 3 - Operacional (SZ9DETAIL03)
        // IMPORTANTE: Usa LoadValue para não disparar triggers que possam zerar Z9_TOTAL
        For nLin := 1 To Len(aDadosSZ93)
            If nLin > 1
                oModelSZ93:AddLine()
            EndIf
            
            oModelSZ93:GoLine(nLin)
            
            // Preenche campos de controle obrigatï¿½rios usando LoadValue
            oModelSZ93:LoadValue("Z9_FILMOV", cFilAnt)
            oModelSZ93:LoadValue("Z9_IDZ8", cNovoId)
            oModelSZ93:LoadValue("Z9_IDFLD", "2OPE01")
            
            // Preenche os demais campos da linha
            For nCol := 1 To Len(aDadosSZ93[nLin])
                cCampo := aDadosSZ93[nLin][nCol][1]
                xValor := aDadosSZ93[nLin][nCol][2]
                
                // Apenas campos permitidos no modelo: Z9_DESC, Z9_ALIQ, Z9_TOTAL
                If cCampo $ "Z9_DESC|Z9_ALIQ|Z9_TOTAL"
                    oModelSZ93:LoadValue(cCampo, xValor)
                EndIf
            Next nCol
        Next nLin
        
        // Volta para a primeira linha de cada grid
        If Len(aDadosSZ91) > 0
            oModelSZ91:GoLine(1)
        EndIf
        If Len(aDadosSZ92) > 0
            oModelSZ92:GoLine(1)
        EndIf
        If Len(aDadosSZ93) > 0
            oModelSZ93:GoLine(1)
        EndIf
        
        // ? AJUSTE CÓPIA: Seta Z8_PVSUGER com o valor da última linha (COEFICIENTE) da grid Mark-up Impostos
        // Pois esse valor é o PV Sugerido e precisa ser trazido na cópia
        nPvCopia := 0
        
        // Tenta ler do modelo (grid já preenchida)
        If Len(aDadosSZ92) > 0
            oModelSZ92:GoLine(oModelSZ92:Length())
            nPvCopia := oModelSZ92:GetValue("Z9_TOTAL")
            ConOut(">>> CÓPIA: Z9_TOTAL da última linha Mark-up Impostos (do modelo): " + cValToChar(nPvCopia))
        EndIf
        
        // Fallback: busca diretamente do array coletado (última linha, campo Z9_TOTAL)
        If nPvCopia == 0 .And. Len(aDadosSZ92) > 0
            For nCol := 1 To Len(aDadosSZ92[Len(aDadosSZ92)])
                If aDadosSZ92[Len(aDadosSZ92)][nCol][1] == "Z9_TOTAL"
                    nPvCopia := aDadosSZ92[Len(aDadosSZ92)][nCol][2]
                    ConOut(">>> CÓPIA: Z9_TOTAL da última linha Mark-up Impostos (do array): " + cValToChar(nPvCopia))
                    Exit
                EndIf
            Next nCol
        EndIf
        
        // Fallback final: busca o Z8_PVSUGER coletado do cabeçalho original
        If nPvCopia == 0
            For nCol := 1 To Len(aDadosSZ8)
                If aDadosSZ8[nCol][1] == "Z8_PVSUGER"
                    nPvCopia := aDadosSZ8[nCol][2]
                    ConOut(">>> CÓPIA: Z8_PVSUGER do cabeçalho original: " + cValToChar(nPvCopia))
                    Exit
                EndIf
            Next nCol
        EndIf
        
        // Atualiza Z8_PVSUGER com o valor encontrado
        lCanAlt := .T.
        oModelSZ8:LoadValue("Z8_PVSUGER", nPvCopia)
        lCanAlt := .F.
        ConOut(">>> CÓPIA: Z8_PVSUGER FINAL = " + cValToChar(nPvCopia))
        
        If Len(aDadosSZ92) > 0
            oModelSZ92:GoLine(1)
        EndIf
        
        // Desativa flag de edição
        lCanAlt := .F.
        
        // Abre a tela para o usuário validar e salvar
        nRet := FWExecView(cTitulo, cPrograma, nOperation, /*oDlg*/, {|| .T.}, /*bOk*/, /*nPercReducao*/, /*aEnableButtons*/, /*bCancel*/, /*cOperatId*/, /*cToolBar*/, oModel)
        
        __lCopia := .F.
        lCanAlt  := .F.
        oModel:DeActivate()
        
        // Se a cópia foi confirmada
        If nRet == 0
            MsgInfo("Registro copiado com sucesso!" + CRLF + "Novo ID: " + cNovoId, "Cópia Confirmada")
        EndIf
    EndIf
    
    RestArea(aAreaSZ9)
    RestArea(aAreaSZ8)
    RestArea(aArea)
    
Return oModel

//===========================================================================
  // fD02FltSZ9 - localiza a filial fisica da SZ9 pelo produto principal
  // e monta filtro Z9_FILMOV correspondente.
  //
  // Disambigua casos onde duas SZ8 com mesmo Z8_ID coexistem (na mesma ou em
  // filiais diferentes), usando Z8_COD como ancora: a SZ9 correta e a que tem
  // item 001 do folder 1PRD01 com Z9_CDPROD = Z8_COD.
  //
  // Parametros:
  //   cIdSZ8  - Z8_ID do cabecalho
  //   cFilSZ8 - Filial atual da SZ8 (fallback se nada localizado)
  //   cZ8COD  - Z8_COD do cabecalho (produto principal)
  //===========================================================================
  Static Function fD02FltSZ9(cIdSZ8, cFilSZ8, cZ8COD)
      Local cFiltro := ""
      Local cSqlChk := ""
      Local cTbSZ9  := RetSqlName("SZ9")
      Local cFilFnd := ""
      Local nTamCOD := TamSX3("Z9_CDPROD")[1]

      Default cFilSZ8 := xFilial("SZ8")
      Default cZ8COD  := ""

      If !Empty(cIdSZ8) .And. !Empty(cZ8COD)
          cSqlChk := "SELECT TOP 1 Z9_FILIAL FROM " + cTbSZ9 + ;
                     " WHERE Z9_IDZ8    = '" + cIdSZ8 + "'" + ;
                     "   AND Z9_IDFLD   = '1PRD01'" + ;
                     "   AND Z9_ITEM    = '001'" + ;
                     "   AND Z9_CDPROD  = '" + PadR(AllTrim(cZ8COD), nTamCOD) + "'" + ;
                     "   AND D_E_L_E_T_ = ' '" + ;
                     " ORDER BY CASE WHEN Z9_FILIAL = '" + cFilSZ8 + "' THEN 1 ELSE 2 END"
          If Select("TMPCHKSZ9") > 0
              TMPCHKSZ9->(DbCloseArea())
          EndIf
          TCQuery cSqlChk Alias TMPCHKSZ9 New
          If !TMPCHKSZ9->(Eof())
              cFilFnd := AllTrim(TMPCHKSZ9->Z9_FILIAL)
          EndIf
          TMPCHKSZ9->(DbCloseArea())
      EndIf

      If Empty(cFilFnd)
          cFiltro := "Z9_FILMOV = '" + cFilSZ8 + "'"
          ConOut(">>> fD02FltSZ9: nao localizou SZ9 pelo produto - estrito (" + cFilSZ8 + ")")
      Else
          cFiltro := "Z9_FILMOV = '" + cFilFnd + "'"
          ConOut(">>> fD02FltSZ9: SZ9 desta SZ8 (cod=" + AllTrim(cZ8COD) + ") localizada em filial " + cFilFnd)
      EndIf
  Return cFiltro
