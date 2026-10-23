#INCLUDE "MATA010.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "APWIZARD.CH"
#INCLUDE "FWADAPTEREAI.CH"
#INCLUDE 'FWMVCDEF.CH'

#DEFINE ACCESS_VIZUALIZAR 1
#DEFINE ACCESS_INCLUIR 2
#DEFINE ACCESS_ALTERAR 3
#DEFINE ACCESS_EXCLUIR 4
#DEFINE ACCESS_COPIA 5

//Controle de Rotinas Relacionadas
Static lMATA019		:= NIL
Static lMATA036		:= NIL
Static aMATA061Access	:= {}
Static aMATA019Access	:= {}
Static aMATA180Access	:= {}
Static aMATA036Access	:= {}

//Controle de Pontos de Entrada
Static lMT010VCP := ExistBlock("MT010VCP")
Static lMT010COR := ExistBlock("MT010COR")
Static lMA010FIL := ExistBlock("MA010FIL")
Static lM010FILB := ExistBlock("M010FILB")
Static lMA010MEM := ExistBlock( "MT010MEM" )
Static lMTA010NC := ExistBlock( "MTA010NC" )
Static lMA010BUT := ExistBlock( "MA010BUT" )
Static lMTA010MNU := ExistBlock("MTA010MNU")
Static lMT010BRW := ExistBlock("MT010BRW")
Static lMT010CAN := ExistBlock("MT010CAN")
Static lMT010VLD := ExistBlock("MT010VLD")

//Outros
Static cFieldsVCP := NIL

/*/{Protheus.doc} MATA010
Cadastro de produto.

Esse fonte é usado por todos os paises, por esse motivo tudo que existir aqui deve ser referente ao
padrão. Se alguma regra se aplica somente a um pais ou a alguns paises, a regra deve ser escrita
no fonte correspondente ao pais(es).

As validações e integrações realizadas após/durante a gravação estão definidas nos eventos do modelo,
na classe MATA010EVDEF.

As rotinas abaixo estão associadas ao produto, de acordo com parametros e acessos do usuario:
	- MATA180 (Complemento de Produto)
	- MATA019 (Cadastro de Indicadores)
	- MATA061 (Produto x Fornecedor)
	- MATA036 ( Complementar do Produto )

@author Juliane Venteu
@since 27/03/2017
@version P12.1.17

/*/
USER Function MATA010M(xRotAuto,nOpcAuto)
    Local oBrowse
    Private l010Auto := ( xRotAuto <> NIL )
    Private lCopia := .F.
    Private lMnuCRM
    Private aRotina		:= MenuDef()
    Default nOpcAuto := 3


    aAdd(aRotina, { OemtoAnsi("Consulta") ,"A010Consul"		, 0 , 2, 0, .F.} )		//"Consulta"
    Set Key VK_F4 TO MT010F4()
    Set Key VK_F6 TO U_MT010F6()

    If ValType(xRotAuto) == "A"
        A010Auto(nOpcAuto, xRotAuto)
    Else
        oBrowse := BrowseDef()
        oBrowse:Activate()

        MT010EndShortcut()
    EndIf

Return .T.

/*/{Protheus.doc} BrowseDef
Definição do browse referente aos produtos

@author Juliane Venteu
@since 27/03/2017
@version P12.1.17

/*/
Static Function BrowseDef()
    Local oMBrowse
    Local aCores 		:= {}
    Local uFilPE		:= Nil
    Local cFiltro       := ""
    Local cFilPE 		:= ""
    Local nX
    Local lCoresPE      := .F.

    Set Key VK_F4 TO MT010F4()

    If lMA010FIL
        // Ponto de Entrada para Expressao em ADVPL.
        uFilPE := ExecBlock("MA010FIL",.F.,.F.)
        If ValType(uFilPE) == "C"
            cFiltro := AllTrim(uFilPE)
        EndIf

    ElseIf lM010FILB
        // Ponto de Entrada para Expressao em SQL ANSI.
        cFilPE := ExecBlock("M010FILB",.F.,.F.)
        If Valtype(cFilPE) == "C"
            cFiltro := "@"+AllTrim(cFilPE)
        EndIf
    EndIf

    // MT010COR - Ponto de Entrada para customizar o array aCores
    If lMT010COR
        lCoresPE := .F.
        aCores := ExecBlock("MT010COR",.F.,.F.)
        If (Valtype(aCores) == "A" .And. Len(aCores) > 0)
            lCoresPE := .T.
        EndIf
    EndIf

    oMBrowse := FWMBrowse():New()
    oMBrowse:SetAlias("SB1")
    oMBrowse:SetDescription(STR0008)
    oMBrowse:SetAttach(.T.)
    oMBrowse:SetCacheView(.F.)



    oMBrowse:SetTotalDefault("B1_FILIAL","COUNT",STR0092)//"Total de Registros"

    If lCoresPE
        // Adiciona as legendas no browse.
        For nX := 1 To Len(aCores)
            /*Condição,Legenda,Descrição*/
            oMBrowse:AddLegend(aCores[nX][1],aCores[nX][2],aCores[nX][3])
        Next nX
    EndIf

    If !Empty(cFiltro)
        oMBrowse:SetFilterDefault(cFiltro)
    EndIf
    oMBrowse:SetCanSaveArea(.T.)
    oMBrowse:SetChgAll(.F.)
    oMBrowse:SetSeeAll(.F.)
    oMBrowse:DisableDetails(.F.)
    oMBrowse:SetDescription("Produto")
    oMBrowse:SetMenuDef("MATA010")
    oMBrowse:SetMainProc("FMATA010")
Return oMBrowse



Static Function MTA010VldActivate(oModel)
    Local lRet 		:= .T.
    Local nOpc 		:= oModel:GetOperation()
    Local aVerify

    //Verifica o acesso do usuario as rotinas relacionadas
    If Type("lMATA061") == "U" .Or. Type("lMATA019") == "U" .Or. Type("lMATA180") == "U"  .Or. Type("lM010Alter") == "U"  .Or. Type("lDcl") == "U"  .Or. Type( "lMATA036" ) == "U" .Or. Type( "lSVK" ) == "U"
        //Controle de Rotinas Relacionadas
        aVerify	:= VerifyAccess() //{lMATA061,lMATA019,lMATA180,lDCL,lM010Alter}
        lMATA061	:= aVerify[1]
        lMATA019	:= aVerify[2]
        lMATA180	:= aVerify[3]
        lDCL		:= aVerify[4]
        lM010Alter	:= aVerify[5]
        lMATA036	:= aVerify[6]
        lSVK        := aVerify[7]
    EndIf

    Model180(oModel, nOpc)
    Model019(oModel, nOpc)
    Model061(oModel, nOpc)
    ModelSGI(oModel)
    ModelDCL(oModel)
    ModelSVK(oModel)

Return lRet

//---------------------------------------------------------
/*/{Protheus.doc} ModelSGI
Função para complementar os submodelos do Model.
É necessario obter a operação do modelo, para verificar
se o usuario tem acesso a rotina nessa operação.

Foi definido para ser executado antes do activate, pois
no momento da execução da função ModelDef, não existe operação
ainda.
@author José Eulálio
@since 18/04/2018
@version 1.0
/*/
//---------------------------------------------------------
Static Function ModelSGI(oModel)
Return MdlSGIPCP(oModel)

//---------------------------------------------------------
/*/{Protheus.doc} ModelDCL
Função para complementar os submodelos do Model.
É necessario obter a operação do modelo, para verificar
se o usuario tem acesso a rotina nessa operação.

Foi definido para ser executado antes do activate, pois
no momento da execução da função ModelDef, não existe operação
ainda.
@author José Eulálio
@since 18/04/2018
@version 1.0
/*/
//---------------------------------------------------------
Static Function ModelDCL(oModel)
    Local oStruDH5	:= NIL

    //Complemento DCL
    If lDCL
        oStruDH5 := FWFormStruct(1, 'DH5', {|cField| !(AllTrim(Upper(cField)) $ "DH5_COD") })

        oModel:AddFields("DH5DETAIL","SB1MASTER",oStruDH5)
        oModel:SetRelation('DH5DETAIL', { { 'DH5_FILIAL', 'xFilial("DH5")' }, { 'DH5_COD', 'B1_COD' } }, DH5->(IndexKey(1)) )
        oModel:GetModel('DH5DETAIL'):SetOptional(.T.)
    EndIf

Return

/*/{Protheus.doc} Model061
Função para complementar os submodelos do Model.
É necessario obter a operação do modelo, para verificar
se o usuario tem acesso a rotina nessa operação.

Foi definido para ser executado antes do activate, pois
no momento da execução da função ModelDef, não existe operação
ainda.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function Model061(oModel, nOpc)
    Local oStruSA5
    Local aAux

    //ProdxFornecedor
    If lMATA061 .and. IsAccessByOperation(nOpc, aMATA061Access)
        oStruSA5 := MA061MldStruct(.T.)

        aAux :=	FwStruTrigger("A5_FORNECE","A5_LOJA","MTA010Proc()")

        oStruSA5:AddTrigger( ;
            aAux[1]  , ;  // [01] Id do campo de origem
            aAux[2]  , ;  // [02] Id do campo de destino
            aAux[3]  , ;  // [03] Bloco de codigo de validação da execução do gatilho
            aAux[4]  )    // [04] Bloco de codigo de execução do gatilho

        //--------------------------------------------------------------------------
        // HACK: Não mudar o id 'MdGridSA5' pois o fonte MATA060 faz diversas
        // validações usando esse id de grid
        //--------------------------------------------------------------------------
        oModel:AddGrid("MdGridSA5","SB1MASTER",oStruSA5)
        oModel:SetRelation('MdGridSA5', { { 'A5_FILIAL', 'xFilial("SA5")' }, { 'A5_PRODUTO', 'B1_COD' } }, SA5->(IndexKey(1)) )
        oModel:getModel('MdGridSA5'):SetOptional(.T.)
        oModel:GetModel("MdGridSA5"):SetDelAllLine(.T.)
        oModel:GetModel("MdGridSA5"):SetUniqueLine({'A5_FORNECE','A5_LOJA','A5_FABR','A5_FALOJA'})
        oModel:GetModel("MdGridSA5"):SetDelAllLine(.T.)
        oModel:InstallEvent("FORNECE",,MATA010Fornecedores():New())
    EndIf
Return

/*/{Protheus.doc} Model180
Função para complementar os submodelos do Model.
É necessario obter a operação do modelo, para verificar
se o usuario tem acesso a rotina nessa operação.

Foi definido para ser executado antes do activate, pois
no momento da execução da função ModelDef, não existe operação
ainda.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function Model180(oModel, nOpc)
    Local oStruSB5
    Local aAux
    Local nPos := aScan(oModel:aAllSubModels, {|x| x:CID == "SB5DETAIL" })

    //Complemento de Produto
    If lMATA180 .and. IsAccessByOperation(nOpc, aMATA180Access) .and. nPos == 0
        oStruSB5 := FWFormStruct(1, 'SB5')
        oStruSB5:setProperty('B5_COD', MODEL_FIELD_OBRIGAT, .F.)

        oModel:AddFields("SB5DETAIL","SB1MASTER",oStruSB5)
        oModel:SetRelation('SB5DETAIL', { { 'B5_FILIAL', 'xFilial("SB5")' }, { 'B5_COD', 'B1_COD' } }, SB5->(IndexKey(1)) )
        oModel:getModel('SB5DETAIL'):SetOptional(.T.)
        oModel:InstallEvent("COMPL.",,MATA180EVDEF():New("SB5DETAIL"))

        If SuperGetMV("MV_LJECOMM",.F.,.F.)
            oModel:InstallEvent("INT.ECOMMERCE",,MATA180ECOMMERCE():New('SB5DETAIL'))
        EndIf

    EndIf

Return

/*/{Protheus.doc} Model019
Função para complementar os submodelos do Model.
É necessario obter a operação do modelo, para verificar
se o usuario tem acesso a rotina nessa operação.

Foi definido para ser executado antes do activate, pois
no momento da execução da função ModelDef, não existe operação
ainda.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function Model019(oModel, nOpc)
    Local oStruSBZ

    If lMATA019 .and. IsAccessByOperation(nOpc, aMATA019Access)
        //Indicadores
        oStruSBZ := MTA019MdlStruct()
        oModel:AddGrid("SBZDETAIL","SB1MASTER",oStruSBZ)
        oModel:SetRelation('SBZDETAIL', { { 'BZ_COD', 'B1_COD' } }, SBZ->(IndexKey(1)) )
        oModel:getModel('SBZDETAIL'):SetOptional(.T.)

        oModel:GetModel("SBZDETAIL"):SetUseOldGrid(.T.)
        oModel:GetModel("SBZDETAIL"):SetUniqueLine({"BZ_FILIAL"})

        oModel:InstallEvent("PAD.",,MATA019EVDEF():New("SBZDETAIL"))
        oModel:InstallEvent("PE.",,MATA019EVPE():New("SBZDETAIL"))

        oModel:AddRules( 'SBZDETAIL', 'BZ_LOCPAD', 'SBZDETAIL', 'BZ_FILIAL', 3)
    EndIf
Return

//---------------------------------------------------------
/*/{Protheus.doc} ModelSVK
Função para complementar os submodelos do Model.
É necessario obter a operação do modelo, para verificar
se o usuario tem acesso a rotina nessa operação.

Foi definido para ser executado antes do activate, pois
no momento da execução da função ModelDef, não existe operação
ainda.
@author Renan Roeder
@since 24/09/2018
@version 1.0
/*/
//---------------------------------------------------------
Static Function ModelSVK(oModel)
    Local oStruSVK
    Local nPos := aScan(oModel:aAllSubModels, {|x| x:CID == "SVKDETAIL" })

    //Complemento de Produto PCP
    If lSVK .And. nPos == 0
        oStruSVK := FWFormStruct(1, 'SVK')
        oStruSVK:setProperty('VK_COD', MODEL_FIELD_OBRIGAT, .F.)

        oModel:AddFields("SVKDETAIL","SB1MASTER",oStruSVK)
        oModel:SetRelation('SVKDETAIL', { { 'VK_FILIAL', 'xFilial("SVK")' }, { 'VK_COD', 'B1_COD' } }, SVK->(IndexKey(1)) )
        oModel:getModel('SVKDETAIL'):SetOptional(.T.)
    EndIf

Return

/*/{Protheus.doc} A010CanActivate
Função executada antes de realizar a ativação do objeto de view.
Se retonar FALSO cancela a exibição da janela, se retornar VERDADEIRO
executa a ativação normalmente.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
static Function A010CanActivate(oView)
    Local nPercent	:= 0
    Local oStruDH5	:= NIL
    Local oStruSGI	:= NIL
    Local oEvFISA180 As Object
    Local oEvMATA036 As Object
    Local aVerify

    RemoveFields(oView)
    AddButtons(oView)

    //Controle de Rotinas Relacionadas
    If Type("lMATA061") == "U" .Or. Type("lMATA019") == "U" .Or. Type("lMATA180") == "U" .Or. Type("lM010Alter") == "U" .Or. Type("lDCL") == "U" .Or. Type( "lMATA036" ) == "U" .Or. Type( "lSVK" ) == "U"
        aVerify	:= VerifyAccess()//{lMATA061,lMATA019,lMATA180,lDCL,lM010Alter}
        lMATA061	:= aVerify[1]
        lMATA019	:= aVerify[2]
        lMATA180	:= aVerify[3]
        lDCL		:= aVerify[4]
        lM010Alter	:= aVerify[5]
        lMATA036	:= aVerify[6]
        lSVK		:= aVerify[7]
    EndIf


    If lMATA036
        // Ativa o Complemento de Produto no formulario do produto
        oEvMATA036:= MATA010MATA036():New("SB1MASTER")
        oEvMATA036:A036CanActivate(oView)
        oEvMATA036:Destroy()
        oEvMATA036 := NIL
    EndIf
    If lMATA180
        View180(oView)
    Endif

    If lMATA019
        View019(oView)
    Endif

    If lMATA061
        View061(oView)
    Endif

    If lM010Alter
        ViewALT(oView)
    EndIf

    If lDCL
        ViewDCL(oView)
    EndIf

    If lSVK
        ViewSVK(oView)
    EndIf

    // Ativa o Complemento de Produto no formulario do produto
    oEvFISA180:= MATA010FISA180():New("SB1MASTER")
    oEvFISA180:A010CanActivate(oView)
    oEvFISA180:Destroy()
    oEvFISA180 := NIL

    //-------------------------------------------------------------------------
    // Tratamento para corrigir percentuais dos boxes. A soma de todos os boxes
    // deve ser igual a 100, caso contrario sobram espaços em branco no formulario
    // do SB1. como os formularios sao condicionais é feita uma correção caso
    // falte algum valor para chegar até o total de 100
    //-------------------------------------------------------------------------
    aEval(oView:aUserBoxs, {|x| nPercent += x:nPercetual} )
    If nPercent < 100
        oView:aUserBoxs[1]:nPercetual += (100 - nPercent)
    EndIf

Return .T.

/*/{Protheus.doc} View180
Função para complementar os formulários da View.
Se o submodelo foi carregado para o model, então cria
o formulário na View.

Esse formulário não é criado na ViewDef, pois no momento
que a ViewDef é executada, não há como saber se o modelo
foi criado, uma vez que a criação desse modelo depende da
operação.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function View180(oView)
    Local oStruSB5
    Local nPos

    If oView:GetModel():GetModel("SB5DETAIL") <> NIL
        oView:CreateHorizontalBox( 'BOXFORMSB5', 10)

        oView:SetOwnerView('FORMSB5','BOXFORMSB5')
        oView:EnableTitleView("FORMSB5", FwX2Nome("SB5"))
    Else
        nPos := aScan(oView:aViews, {|x| x[VIEWS_VIEW_ID] == "FORMSB5" })

        aDel(oView:aViews, nPos)
        aSize(oView:aViews, Len(oView:aViews)-1)
    EndIf

Return

/*/{Protheus.doc} View019
Função para complementar os formulários da View.
Se o submodelo foi carregado para o model, então cria
o formulário na View.

Esse formulário não é criado na ViewDef, pois no momento
que a ViewDef é executada, não há como saber se o modelo
foi criado, uma vez que a criação desse modelo depende da
operação.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function View019(oView)
    Local oStruSBZ
    Local nPos := aScan(oView:aViews, {|x| x[VIEWS_VIEW_ID] == "FORMSBZ" })

    If oView:GetModel():GetModel("SBZDETAIL") <> NIL .and. nPos == 0
        oStruSBZ := MTA019ViewStruct()
        oView:CreateHorizontalBox( 'BOXFORMSBZ', 10)
        oView:AddGrid('FORMSBZ' , oStruSBZ,'SBZDETAIL')
        oView:SetOwnerView('FORMSBZ','BOXFORMSBZ')
        oView:EnableTitleView("FORMSBZ", FwX2Nome("SBZ"))
    EndIf

Return

//---------------------------------------------------------
/*/{Protheus.doc} ViewDCL
Função para complementar os formulários da View.

@author José Eulálio
@since 04/06/2018
@version 1.0
/*/
//---------------------------------------------------------
static Function ViewDCL(oView)

    oView:CreateHorizontalBox( 'BOXFORMDH5', 10)
    oView:SetOwnerView('FORMDH5','BOXFORMDH5')
    oView:EnableTitleView("FORMDH5", FwX2Nome("DH5"))

Return

/*/{Protheus.doc} ViewSVK
Função para complementar os formulários da View.
Se o submodelo foi carregado para o model, então cria
o formulário na View.

Esse formulário não é criado na ViewDef, pois no momento
que a ViewDef é executada, não há como saber se o modelo
foi criado, uma vez que a criação desse modelo depende da
operação.

@author Renan Roeder
@since 27/09/2018
@version P12.1.17

/*/
Static Function ViewSVK(oView)
    Local nPos

    If oView:GetModel():GetModel("SVKDETAIL") <> NIL
        oView:CreateHorizontalBox( 'BOXFORMSVK', 10)

        oView:SetOwnerView('FORMSVK','BOXFORMSVK')
        oView:EnableTitleView("FORMSVK", FwX2Nome("SVK"))
    Else
        nPos := aScan(oView:aViews, {|x| x[VIEWS_VIEW_ID] == "FORMSVK" })

        aDel(oView:aViews, nPos)
        aSize(oView:aViews, Len(oView:aViews)-1)
    EndIf

Return

/*/{Protheus.doc} View061
Função para complementar os formulários da View.
Se o submodelo foi carregado para o model, então cria
o formulário na View.

Esse formulário não é criado na ViewDef, pois no momento
que a ViewDef é executada, não há como saber se o modelo
foi criado, uma vez que a criação desse modelo depende da
operação.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function View061(oView)
    Local oStruSA5
    Local nPos := aScan(oView:aViews, {|x| x[VIEWS_VIEW_ID] == "FORMSA5" })

    If oView:GetModel():GetModel("MdGridSA5") <> NIL .and. nPos == 0
        oStruSA5:= MA061ViewStruct()
        oView:CreateHorizontalBox( 'BOXFORMSA5', 10)
        oView:AddGrid('FORMSA5' , oStruSA5,'MdGridSA5')
        oView:SetOwnerView('FORMSA5','BOXFORMSA5')
        oView:EnableTitleView("FORMSA5", FwX2Nome("SA5"))
    EndIf

Return

/*/{Protheus.doc} ViewALT
Função para complementar os formulários da View.
Se o submodelo foi carregado para o model, então cria
o formulário na View.

Esse formulário não é criado na ViewDef, pois no momento
que a ViewDef é executada, não há como saber se o modelo
foi criado, uma vez que a criação desse modelo depende da
operação.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function ViewALT(oView)
Return ViewSGIPCP(oView)

/*/{Protheus.doc} MT010F4
Exibe tela de saldos do produto.

@author Juliane Venteu
@since 23/02/2017
@version P12.1.17

/*/
Static Function MT010F4()
    Local cFilBkp := cFilAnt
    Set Key VK_F4 TO
    If FWModeAccess("SB1")=="E"
        cFilAnt := SB1->B1_FILIAL
    EndIf
    MaViewSB2(SB1->B1_COD)
    cFilAnt := cFilBkp
    Set Key VK_F4 TO MT010F4()
Return Nil

static Function MT010EndShortcut()
    SET KEY VK_F4 TO
Return

Static Function A010Deleta(cAlias,nReg,nOpc)
    Local nOK

    DEFAULT cAlias	:= Alias()
    DEFAULT nReg 	:= SB1->(Recno())
    DEFAULT nOpc	:= 5

    nOK := (FWExecView (STR0007, "MATA010",  MODEL_OPERATION_DELETE,,{||.T.},,,,,,,))

    If lMT010CAN
        nOk := NMt010Can(nOk,nOpc)
        ExecBlock("MT010CAN",.F.,.F.,{nOK})
    EndIf

Return NIL

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Funcao criada porque no FINA010 tambem existe A010Deleta     ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
static Function MMata010De(cAlias,nReg,nOpc)
Return (A010Deleta(cAlias,nReg,nOpc))

//RETIRAR STATIC
static Function A010Visul(cAlias,nReg,nOpc)
Return ExecMVC(MODEL_OPERATION_VIEW)

static Function MA010Inclu(cAlias,nReg,nOpc)
    Local nOK

    Default nOpc := MODEL_OPERATION_INSERT

    //Desabilita o F4
    SET KEY VK_F4 TO

    nOK := (FWExecView (STR0005, "MATA010",  MODEL_OPERATION_INSERT,,,,,,,,,))

    If lMT010CAN
        nOk := NMt010Can(nOk,nOpc)
        ExecBlock("MT010CAN",.F.,.F.,{nOK})
    EndIf

    //Habilita o F4
    Set Key VK_F4 TO MT010F4()

Return

static Function MA010Alter(cAlias,nReg,nOpc)
    Local nOK

    //Desabilita o F4
    SET KEY VK_F4 TO
    nOK := (FWExecView (STR0006, "MATA010",  MODEL_OPERATION_UPDATE,,{||.T.},,,,,,,))

    If lMT010CAN
        nOk := NMt010Can(nOk,nOpc)
        ExecBlock("MT010CAN",.F.,.F.,{nOK})
    EndIf

    //Habilita o F4
    Set Key VK_F4 TO MT010F4()

Return

//RETIRAR STATIC
Static Function A010Copia()
    Local lRetPE := .T.

    lCopia := .T. //Private legado

    If lMT010VLD
        lRetPE:=ExecBlock("MT010VLD",.F.,.F.)
        If VALTYPE(lRetPE)<>"L"
            lRetPE := .T.
        EndIF
    EndIf

    If lRetPE
        A010Inclui(,,OP_COPIA)
    EndIf
Return .T.

Static Function ExecMVC(nOpc)
    Local nOK

    lMnuCRM := (nOpc == 2 .or. nOpc==4)
    nOK := FWExecView(,"MATA010",nOpc)

    //----------------------------------------------------------------
    // Compatibilização do retorno
    //----------------------------------------------------------------
    If nOK == 0 // OK do MVC
        nOK := 1 //OK da rotina antiga
    ElseIf nOK == 1 //Cancelou do MVC
        nOK := 3 //Cancelou da rotina antiga
    EndIf

Return nOK

/*/{Protheus.doc} VerifyAccess
Verifica se o usuario tem acesso as operações de
visualização, inclusão, alteração e exclusão das rotinas
MATA061, MATA019 e MATA180, se o o usuario possuir acesso,
então essas rotinas são acopladas a tela do cadastro de
produto.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
static Function VerifyAccess()
    Local cRot

    If Type("lMATA061") == "U" .Or. Type("lMATA019") == "U" .Or. Type("lMATA180") == "U" .Or. Type("lM010Alter")== "U" .Or. Type("lDcl")== "U" .Or. Type( "lMATA036" ) == "U" .Or. Type("lSVK") == "U"

        cRot := SuperGetMv("MV_CADPROD",,"|SBZ|SB5|SGI|D3E|")

        If "SA5" $ cRot .And. FwAliasInDic( 'SA5' )
            lMATA061 := .T.
            If Empty(aMATA061Access)
                aAdd(aMATA061Access, {OP_PESQUISAR	, MPUserHasAccess("MATA061", OP_PESQUISAR)} )
                aAdd(aMATA061Access, {OP_VISUALIZAR	, MPUserHasAccess("MATA061", OP_VISUALIZAR)} )
                aAdd(aMATA061Access, {OP_INCLUIR	, MPUserHasAccess("MATA061", OP_INCLUIR)} )
                aAdd(aMATA061Access, {OP_ALTERAR	, MPUserHasAccess("MATA061", OP_ALTERAR)} )
                aAdd(aMATA061Access, {OP_EXCLUIR	, MPUserHasAccess("MATA061", OP_EXCLUIR)} )
                aAdd(aMATA061Access, {OP_COPIA		, MPUserHasAccess("MATA061", OP_COPIA)} )
            Endif
        Else
            lMATA061 := .F.
        EndIf

        //-------------------------------------------------------------------------------------
        // Para o submodelo de indicadores, além de estar configurado no parametro é necessario
        // que a tabela de produtos esteja configurada como compartilhada, pois se o produto
        // for exclusivo para cada filial, não existe a necessidade de habilitar os indicadores
        // para cada filial do sistema
        //-------------------------------------------------------------------------------------
        If "SBZ" $ cRot .And. FWModeAccess("SB1",3) == "C"
            lMATA019 := .T.
            If Empty(aMATA019Access)
                aAdd(aMATA019Access, {OP_VISUALIZAR	, MPUserHasAccess("MATA019", OP_VISUALIZAR)} )
                aAdd(aMATA019Access, {OP_INCLUIR	, MPUserHasAccess("MATA019", OP_INCLUIR)} )
                aAdd(aMATA019Access, {OP_ALTERAR	, MPUserHasAccess("MATA019", OP_ALTERAR)} )
                aAdd(aMATA019Access, {OP_EXCLUIR	, MPUserHasAccess("MATA019", OP_EXCLUIR)} )
                aAdd(aMATA019Access, {OP_COPIA		, MPUserHasAccess("MATA019", OP_COPIA)} )
            Endif
        Else
            lMATA019 := .F.
        EndIf

        If "SB5" $ cRot .And. FwAliasInDic( 'SB5' )
            lMATA180 := .T.
            If Empty(aMATA180Access)
                aAdd(aMATA180Access, {OP_VISUALIZAR, MPUserHasAccess("MATA180", OP_VISUALIZAR)} )
                aAdd(aMATA180Access, {OP_INCLUIR	, MPUserHasAccess("MATA180", OP_INCLUIR)} )
                aAdd(aMATA180Access, {OP_ALTERAR	, MPUserHasAccess("MATA180", OP_ALTERAR)} )
                aAdd(aMATA180Access, {OP_EXCLUIR	, MPUserHasAccess("MATA180", OP_EXCLUIR)} )
                aAdd(aMATA180Access, {OP_COPIA		, MPUserHasAccess("MATA180", OP_COPIA)} )
            Endif
        Else
            lMATA180 := .F.
        EndIf

        If "DH5" $ cRot .And. FwAliasInDic( 'DH5' )
            lDCL := SuperGetMV("MV_DCLNEW",.F.,.F.)
        Else
            lDCL := .F.
        EndIf

        // produtos Alternativos
        If "SGI" $ cRot .And. FwAliasInDic( 'SGI' )
            lM010Alter := .T.
        Else
            lM010Alter := .F.
        EndIf

        If "D3E" $ cRot .And. FwAliasInDic( 'D3E' )
            lMATA036 := .T.
            If Empty(aMATA036Access)
                aAdd(aMATA036Access, {OP_VISUALIZAR	, MPUserHasAccess("MATA036", OP_VISUALIZAR 	)} )
                aAdd(aMATA036Access, {OP_INCLUIR	, MPUserHasAccess("MATA036", OP_INCLUIR 	)} )
                aAdd(aMATA036Access, {OP_ALTERAR	, MPUserHasAccess("MATA036", OP_ALTERAR 	)} )
                aAdd(aMATA036Access, {OP_EXCLUIR	, MPUserHasAccess("MATA036", OP_EXCLUIR 	)} )
                aAdd(aMATA036Access, {OP_COPIA		, MPUserHasAccess("MATA036", OP_COPIA		)} )
            Endif
        Else
            lMATA036 := .F.
        EndIf

        //complemento do produto PCP
        lSVK := ( "SVK" $ cRot .And. FwAliasInDic( 'SVK' ) )

    EndIf

Return { lMATA061, lMATA019, lMATA180, lDCL, lM010Alter, lMATA036, lSVK }

/*/{Protheus.doc} IsAccessByOperation
Analisa o array que guarda os acessos por operação da rotina
e retorna se o usuario tem acesso a determinada operação ou não.

@param nOpc número da operação
@param aAccess array que já possui os controles de acordo com usuario e rotinas

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function IsAccessByOperation(nOpc, aAccess)
    Local lRet

    Do Case
        Case nOpc == OP_VISUALIZAR
            lRet  := aAccess[ACCESS_VIZUALIZAR][2]

        Case nOpc == OP_INCLUIR
            lRet  := aAccess[ACCESS_INCLUIR][2]

        Case nOpc == OP_ALTERAR
            lRet  := aAccess[ACCESS_ALTERAR][2]

        Case nOpc == OP_EXCLUIR
            lRet  := aAccess[ACCESS_EXCLUIR][2]

        Case nOpc == OP_COPIA
            lRet  := aAccess[ACCESS_COPIA][2]

        Otherwise
            lRet := .T.
    EndCase

Return lRet

/*/{Protheus.doc} RemoveFields
Função criada para encapsular a chamada do ponto de entrada MT010VCP.
O ponto de entrada permite escolher quais campos serão exibidos na tela quando a
operação é VISUALIZAÇÃO.

Como quando a view é criada ainda não existe operação definida, usei o momento
antes do Activate para excluir os campos que não devem ser exibidos, se o ponto
de entrada existir.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function RemoveFields(oView)
    Local nOpc := oView:GetOperation()
    Local aAux
    Local oStruct
    Local aFields
    Local nX

    If nOpc == OP_VISUALIZAR .Or. nOpc == OP_PESQUISAR
        If lMT010VCP
            If cFieldsVCP == NIL
                cFieldsVCP := ""
                aAux := ExecBlock("MT010VCP",.F.,.F.)
                If ValType(aAux) == "A"
                    For nX:=1 to Len(aAux)
                        cFieldsVCP += AllTrim(Upper(aAux[nX])) + "|"
                    Next nX
                EndIf
            EndIf

            If !Empty(cFieldsVCP)
                oStruct := oView:GetViewStruct("FORMSB1")
                aFields := aClone(oStruct:GetFields())

                For nX:=1 to Len(aFields)
                    If !(AllTrim(Upper(aFields[nX][MVC_VIEW_IDFIELD])) $ cFieldsVCP)
                        oStruct:RemoveField(aFields[nX][MVC_VIEW_IDFIELD])
                    EndIf
                Next nX
            EndIf
        EndIf
    EndIf

Return .T.

/*/{Protheus.doc} AddButtons
Função criada para criar botões na view baseado em uma operação e se
existe o produto na tabela SG1

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function AddButtons(oView)
    Local aArea := SG1->(GetArea())

    //inclusao dinamica do botao para poder selecionar os opcionais, no minimo quando houver estrutura.
    SG1->(DbSetOrder(1))
    If SG1->(DbSeek(xFilial('SG1')+SB1->B1_COD))
        oView:AddUserButton(STR0029,'PRODUTO', {|| A010SeleOpc(oView) }) //"Opcionais Default"
        If oView:GetModel():GetOperation() == MODEL_OPERATION_UPDATE
            oView:AddUserButton(STR0112,'PRODOPC', {|| A010LimpOp(oView) })	//"Limpa os opcionais"
        EndIf
    EndIf

    RestArea(aArea)
Return

/*/{Protheus.doc} A010IntSFC
Na conversão para MVC essa função se tornou uma classe de integração
baseada em MVC. Para manter a compatibilidade da função, foi desviado
a execução da função para dentro da classe, usando o metodo Exec.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
//RETIRAR STATIC
Static Function A010IntSFC(nOpc,cError,cNome,oModel)
    Local lRet
    Local oEvent

    Default oModel  := FWLoadModel("SFCC101")		// Objeto de modelo de dados

    oEvent := MATA010DPR():New(oModel, cNome, cError)
    lRet := oEvent:Exec(nOpc)

Return lRet

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³A010SFCErrºAutor  ³ Andre Anjos  		 º Data ³  30/05/11   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Tratamento de erro da integracao com Chao de Fabrica.      º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Integracao SFC                                             º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010SFCErr(oModel,cError,nItErro,cNome,cChave)
    Local aErro  := {}
    Local lCarga := ValType(cError) == "C"

    aErro := oModel:GetErrorMessage()

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Estrutura do vetor com erro ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    //[1] Id do formulário de origem
    //[2] Id do campo de origem
    //[3] Id do formulário de erro
    //[4] Id do campo de erro
    //[5] Id do erro
    //[6] mensagem do erro
    //[7] mensagem da solução
    //[8] Valor atribuido
    //[9] Valor anterior

    If lCarga
        cError += cNome +" " +AllTrim(cChave) +": " +AllToChar(aErro[6]) +CRLF
    Else
        AutoGrLog(STR0131 +'[' +AllToChar(aErro[1]) +']') //"Id do formulário de origem: "
        AutoGrLog(STR0132 +'[' +AllToChar(aErro[2]) +']') //"Id do campo de origem:      "
        AutoGrLog(STR0133 +'[' +AllToChar(aErro[3]) +']') //"Id do formulário de erro:   "
        AutoGrLog(STR0134 +'[' +AllToChar(aErro[4]) +']') //"Id do campo de erro:        "
        AutoGrLog(STR0135 +'[' +AllToChar(aErro[5]) +']') //"Id do erro:                 "
        AutoGrLog(STR0136 +'[' +AllToChar(aErro[6]) +']') //"Mensagem do erro:           "
        AutoGrLog(STR0137 +'[' +AllToChar(aErro[7]) +']') //"Mensagem da solução:        "
        AutoGrLog(STR0138 +'[' +AllToChar(aErro[8]) +']') //"Valor atribuido:            "
        AutoGrLog(STR0139 +'[' +AllToChar(aErro[9]) +']') //"Valor anterior:             "

        HELP(" ",1,STR0140,,AllToChar(aErro[6]),1,1) //"Integração"

        If !Empty(nItErro)
            AutoGrLog(STR0141 +'[' +AllTrim(AllToChar(nItErro)) +']') //"Erro no Item:               "
        EndIf

        MostraErro()
    EndIf

Return

/*/{Protheus.doc} A010FDCANAL
//TODO Programa de Alteracao de Produtos
Função original A010FDC. foi renomeada para melhor hierarquia de chamadas
entre os fontes MATA010, MATA10M e MATA010EVDEF
@author Marcelo B. Abe
@since 20/04/1994
@version 1.0
@return logico, retorno sempre falso

@type function
/*/
static Function A010FDCANAL(void)
    LOCAL lExiste  :=.F.
    LOCAL nCont    := 0
    LOCAL aAreaAnt := GetArea()

    dbSelectArea("SA5")
    dbSetOrder(2)
    dbSeek(xFilial("SA5")+SB1->B1_COD)
    While !Eof() .And. (A5_FILIAL+A5_PRODUTO == xFilial("SA5")+SB1->B1_COD)

        If A5_FORNECE == SB1->B1_PROC   //Se ja Existe
            lExiste:=.T.
        Else
            RecLock("SA5",.F.,.T.)           //Eliminar outros Fornecedores
            dbDelete()
            MsUnLock()
            nCont += 1
        Endif
        dbSkip()
    End

    If !lExiste .And. !Empty(SB1->B1_PROC)   //Caso nao Haja,crie.
        dbSelectArea("SA2")
        dbSeek(xFilial("SA2")+SB1->B1_PROC)
        dbSelectArea("SB1")
        dbSeek(xFilial("SB1")+SB1->B1_COD)
        dbSelectArea("SA5")
        RecLock("SA5",.T.)
        Replace         A5_FILIAL  With xFilial("SA5"),;
            A5_FORNECE With SB1->B1_PROC,;
            A5_LOJA    With SA2->A2_LOJA,;
            A5_NOMEFOR With SA2->A2_NOME,;
            A5_PRODUTO With SB1->B1_COD ,;
            A5_NOMPROD With SB1->B1_DESC
    EndIf

    RestArea(aAreaAnt)
Return(.F.)

//-------------------------------------------------------------------------------------------------
/*/{Protheus.doc} MATA010PPI

Realiza a integração com o PC-Factory - PPI Multitask

@param cXml      - XML que será enviado. Caso não seja passado esse parametro, será realizada
                   a chamada do Adapter para criação do XML.
                   Se for passado esse parâmetro, não será exibida a mensagem de erro caso exista,
                   nem será considerado o filtro da tabela SOE.
@param cProd     - Obrigatório quando utilizado o parâmetro cXml. Contém o código do produto
@param lExclusao - Indica se está chamando para rotina de exclusão de produto.
@param lFiltra   - Identifica se será realizado ou não o filtro do registro.
@param lPendAut  - Indica se será gerada a pendência sem realizar a pergunta para o usuário, caso ocorra algum erro.

@author  Lucas Konrad França
@version P12
@since   13/08/2015
@return  lRet  - Indica se a integração com o PC-Factory foi realizada.
           .T. -> Integração Realizada
           .F. -> Integração não realizada.

@Obs Na conversão para MVC essa integração foi transformada em uma classe, para manter a compatibilidade
com a função, a execução é desviada para o metodo Execute da classe
/*/
//-------------------------------------------------------------------------------------------------
//RETIRAR STATIC
Static Function MATA010PPI(cXml, cProd, lExclusao, lFiltra, lPendAut)
    Local oEvent := MATA010PPI():New(cXml, cProd, lExclusao, lFiltra, lPendAut)
    Local lRet

    lRet := oEvent:Execute()

    //Tratativa para retornar .F. mesmo quando é pendência automática;
    //Utilizado apenas para o programa de sincronização.
    If lRet .And. AllTrim(FunName()) == "PCPA111"
        lRet := .F.
    EndIf

Return lRet

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010SeleOpc³ Autor ³Alex Sandro Valario   ³ Data ³04/05/2005³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Funcao p/ selecao de Opcionais                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ Nenhum 	                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA010                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
Static Function A010SeleOpc(oView)
    Local cRet := ""
    Local oModel := oView:GetModel()
    Local lVisual := !(oModel:GetOperation() == MODEL_OPERATION_UPDATE)
    Local lOpcPadrao := GetNewPar("MV_REPGOPC","N") == "N"
    Local nQtdMax := Val(Replicate('9',TamSX3("C2_QUANT")[1]))
    Local lPCPREVATU	:= FindFunction('PCPREVATU')
    Local cRevisao		:= ''

    cRevisao :=	IIF(lPCPREVATU , PCPREVATU(oModel:GetValue("SB1MASTER","B1_COD")), oModel:GetValue("SB1MASTER","B1_REVATU") )

    If SeleOpc(1,"MATA010",oModel:GetValue("SB1MASTER","B1_COD"),Nil,@cRet,oModel:GetValue("SB1MASTER",IIf(lOpcPadrao,"B1_OPC","B1_MOPC")),,lVisual,nQtdMax,dDataBase,cRevisao )
        oView:SetModified(.T.)
    EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} A010LimpOp
Funcao p/ Limpar o campo de Opcionais
@author		Andre Maximo
@since		17/12/2015
@version	1.0
/*/
//-------------------------------------------------------------------

Static Function A010LimpOp(oView)
    Local oModel := oView:GetModel()

    oModel:LoadValue("SB1MASTER","B1_OPC"," ")
    oModel:LoadValue("SB1MASTER","B1_MOPC"," ")

    oView:SetModified(.T.)

Return Nil

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ MTA010E  ³ Autor ³ AVERAGE               ³ Data ³ 28/07/00 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Grava campo memo     do EIC                          	  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ Nenhum 	                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³                                                   		  ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function Mta010e()

    If nModulo == 17			//SIGAEIC
        MSMM(SB1->B1_DESC_I,,,,2)
        MSMM(SB1->B1_DESC_GI,,,,2)
        MSMM(SB1->B1_DESC_P,,,,2)
    Endif
Return Nil

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ A010Tipo ³ Autor ³ Jose Lucas            ³ Data ³ 12.11.93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Verifica a existencia do Tipo na Tabela de Parametros.     ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A010Tipo()                                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MatA010                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Tipo()

    LOCAL cVar, cSavAlias := Alias(), lRet := .T.

    cVar := &(ReadVar())

    dbSelectArea("SX5")
    dbSeek(xFilial("SX5")+"02"+cVar)
    If !Found()
        Help(" ",1,"MA01002")
        lRet := .F.
    EndIf
    dbSelectArea(cSavAlias)
Return(lRet)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ A010Grupo³ Autor ³ Jose Lucas            ³ Data ³ 12.11.93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Verifica a existencia do Grupo na Tabela de Parametros.    ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A010Grupo()                                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MatA010                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Grupo()

    LOCAL cVar, cSavAlias := Alias(), lRet := .T.

    cVar := &(ReadVar())

    dbSelectArea("SBM")
    dbSetOrder(1)
    dbSeek(xFilial("SBM")+cVar)

    If !Found()
        Help(" ",1,"MA01002")
        lRet := .F.
    EndIf


    dbSelectArea(cSavAlias)
Return(lRet)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ A010Mult ³ Autor ³ Jose Lucas            ³ Data ³ 26.11.93 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Comsistir se B1_LE e B1_QE sao multiplos.                  ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A010Mult()                                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MatA010                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Mult()

    LOCAL cVar, cCampo, lRet := .T.

    cCampo := ReadVar()
    cVar := &(ReadVar())

    If AllTrim(cCampo) == "B1_LE"
        If !Empty(M->B1_QE) .And. !Empty(M->B1_LE)
            If QtdComp(Mod( M->B1_LE,M->B1_QE )) > QtdComp(0)
                Help(" ",1,"MA01003")
                lRet := .F.
            EndIf
        EndIf
    Else
        If !Empty(M->B1_LE) .And. !Empty(M->B1_QE)
            If QtdComp(Mod( M->B1_LE,M->B1_QE )) > QtdComp(0)
                Help(" ",1,"MA01003")
                lRet := .F.
            EndIf
        EndIf
    EndIf
Return(lRet)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ A010MONO ³ Autor ³ Marcelo B. Abe        ³ Data ³ 04/04/94 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Programa de Validacao de Fornecedor de Dominio do Canal    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ Void A010MONO(void)                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ SX3->X3_VALID(B1_MONO)                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010MONO()
    Local lRet := .T.
    Local oModel
    Local oView
    Local oGrid

    If EMPTY(M->B1_PROC) .And. M->B1_MONO=="S"
        HELP(" ",1,"A010MONO")
        lRet := .F.
    ElseIf M->B1_MONO == "S" .And. !Empty(M->B1_PROC)
        oModel := FWModelActive()
        oGrid := oModel:GetModel("MdGridSA5")
        oView := FWViewActive()

        If oGrid <> NIL .And. !oGrid:IsEmpty() .And. oGrid:Length(.T.) > 1 .And. oView <> NIL .And. oView:GetModel():GetID() == "ITEM"
            If !MsgYesNo(STR0142) //"Existem outros fornecedores relacionados a esse produto, tem certeza que deseja alterar a distribuição para um fornecedor único?
                lRet := .F.
                HELP(" ",1,"MT010NOFORALT") //"Fornecedor não alterado"
            EndIf
        EndIf
    ElseIf M->B1_MONO <> "S"
        // Habilita a edição do grid SA5
        editGridSA5(.T.)
    EndIf

Return(lRet)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³ A010PROC ³ Autor ³ Marcelo B. Abe        ³ Data ³ 04/04/94 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Programa de Validacao do Fornecedor Padrao.                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ Void A010PROC(void)                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T.                                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ SX3->X3_VALID(B1_PROC)                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010PROC()

    Local lRet  := .T.

    If Empty(M->B1_PROC)
        M->B1_MONO:= Space(TamSX3("B1_MONO")[1])
        M->B1_LOJPROC :=Space(TamSX3("B1_LOJPROC")[1])

        // Habilita a edição do grid SA5
        editGridSA5(.T.)
    Else
        If !Empty(M->B1_LOJPROC)
            lRet := ExistCpo("SA2",M->B1_PROC+M->B1_LOJPROC)
        Else
            SA2->(DbSetOrder(1))
            If !SA2->(DbSeek(xFilial("SA2")+M->B1_PROC))
                Help("  ",1,"REGNOIS")
                lRet := .F.
            EndIf
        EndIf
    Endif

Return(lRet)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010Preco ³ Autor ³ Marcos Bregantim      ³ Data ³ 17.05.94 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Validar Data de Referencia do Preco                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A010Preco()                                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T.                                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ Generico                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static FUNCTION A010Preco()

    LOCAL cPer := Substr(ReadVar(),10,1), cVar
    If "B1_"$ReadVar()
        cVar := "B1_DTREFP" + cPer
    Elseif "B5_"$ReadVar()
        cVar := "B5_DTREFP" + cPer
    Endif

    If &(ReadVar()) > 0
        M->&cVar := dDataBase
    Endif
Return(.T.)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010Grade ³ Autor ³ Rosane Luciane Chene  ³ Data ³ 23.10.95 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Verifica se o produto nao foi cadastrado como referencia   ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³ A010Grade()                                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T./.F.                                                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ Generico                                                   ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Grade()

    Local aArea
    Local cProduto	  :=&(ReadVar())
    Local cMascara    := SuperGetMv("MV_MASCGRD")
    Local lRet		  :=.T.
    Local nTamRef     := Val(Substr(cMascara,1,2))

    lGrade	  := GetMV("MV_GRADE")


    If lGrade
        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³So salva ambiente se o parametro MV_GRADE estiver habilitado            ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
        aArea := GetArea()

        cProduto := Substr(cProduto,1,nTamRef)

        dbSelectArea("SB4")
        dbSetOrder(1)
        If ( MsSeek(xFilial("SB4")+cProduto,.F.) .And. !Empty(cProduto) .And. ;
                AllTrim(SubStr(cProduto,nTamRef+1)) == "" )
            Help(" ",1,"A010GRADE")
            lRet := .F.
        Endif

        //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
        //³Restaura a entrada da Rotina                                            ³
        //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
        RestArea(aArea)
    Endif
    if lRet
        lRet := A010VlStr ()
    EndIf
Return(lRet)

/*/{Protheus.doc} A010Mod
//TODO Verifica se o centro de custos cadastrado p/ a MOD existe
@author Rodrigo de A. Sartorio
@since 15/07/97
@version 1.0
@return logico, Verdadeiro se o produto infomarmado é valido

@type function
/*/
//RETIRAR STATIC
Static Function A010Mod()
    Local cCC		:= ""
    Local cAliasCC	:= "CTT"
    Local nTamCCust	:= 0
    Local lRet		:= .T.

    nTamCCust := TamSX3("CTT_CUSTO")[1]

    cCC := PadR(Substr(&(ReadVar()),4),nTamCCust," ")

    dbSelectArea(cAliasCC)
    If dbSeek(xFilial(cAliasCC)+cCC)
        lRet := CTB105CC(cCC)
    Else
        Help(" ",1,"A010MOD")
        lRet := .F.
    EndIf

Return(lRet)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010Contr ³ Autor ³ Cristina Ogura        ³ Data ³ 18/07/97 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Verifica a existencia de contratos para o produto           ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³A010Contr()                                                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA010                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Contr()

    Local cSavAlias := Alias()
    Local nSavOrd
    Local lRet		:= .T.

    dbSelectArea("SC3")
    nSavOrd := IndexOrd()
    dbSetOrder(3)

    If Altera .And. M->B1_CONTRAT == "N"
        If dbSeek(xFilial("SC3")+M->B1_COD)
            While !Eof() .And. SC3->C3_FILIAL+SC3->C3_PRODUTO == xFilial("SC3")+M->B1_COD
                If SC3->C3_ENCER != "E"
                    Help(" ",1,"A010AE")
                    lRet := .F.
                    Exit
                EndIf
                dbSkip()
            EndDo
        EndIf
    EndIf

    dbSelectArea("SC3")
    dbSetOrder(nSavOrd)
    dbSelectArea(cSavAlias)

Return(lRet)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010Import³ Autor ³ MICROSIGA/AVERAGE     ³ Data ³ 20/08/97 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Consiste campos relativos a Importacao (SIGAEIC)            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³A010Import()                                                ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³MATA010                                                     ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Import()

    Local lRet:=.T.

    If M->B1_IMPORT == "S" .And. Empty(M->B1_UNI)
        Help("",1,"A010UNI")
        lRet:=.F.
    Endif
Return(lRet)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡„o    ³ A010Potenci³ Autor ³Rodrigo de A. Sartorio ³ Data ³ 31.07.02 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡„o ³ Valida potencia padrao digitada                              ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                    	³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                 	³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³ SIGAEST                                                      ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
*/
//RETIRAR STATIC
Static Function A010Potenci()

    LOCAL lRet := .T.
    If !Empty(&(ReadVar()))
        HELP(" ",1,"MA010NAOP")
        lRet:=.F.
    EndIf
Return(lRet)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010LotQlt³ Autor ³Paulo Emidio de Barros ³ Data ³29/08/2001³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Sugere o tipo de Rastreaabilidade, quando o produto estiver³±±
±±³ 		 ³ com opcao de envio para Inspecao no Quality				  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ .T. / .F.                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA010                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function a010LotQlt()

    Local lRet := .T.
Return(lRet)

/*
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡…o    ³A010Consul ³ Autor ³Alexandre Inacio Lemes³ Data ³31/03/2005³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³Excuta a chamada da funcao MC050con para consulta do produto³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³ Nenhum                                                     ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³ Nenhum 	                                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Uso      ³ MATA010                                                    ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Consul()

    Local aArea    := GetArea()

    SetKey( VK_F12, { || pergunte("MTC050",.T.) } )
    If Pergunte("MTC050",.T.)
        MC050Con()
    EndIf
    Set Key VK_F4 TO MT010F4()
    SetKey( VK_F12, { || pergunte("MTA010",.T.) } )
    Pergunte("MTA010",.F.)

    RestArea(aArea)
Return Nil

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Programa  ³A010WizFac³ Autor ³ Gustavo G. Rueda      ³ Data ³27/11/2007³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡…o ³ Chamada da rotina que permite uma manutencao facil no      ³±±
±±³          ³ cadastro.                                                  ³±±
±±³          ³                                                            ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Retorno   ³.T.                                                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³Nenhum                                                      ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³   DATA   ³ Programador   ³Manutencao efetuada                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³          ³               ³                                            ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/
//RETIRAR STATIC
Static Function A010WizFac()

    Local	cCmps		:=	""
    Local	aPar 		:=	{}
    Local	cMVA010FAC	:=	GetNewPar("MV_A010FAC","")

    cCmps	:=	"B1_TIPO/B1_CODITE/B1_UM/B1_LOCPAD/B1_GRUPO/B1_PICM/B1_IPI/B1_ESPECIE/B1_ALIQISS/B1_MSBLQL/"
    cCmps	+=	"B1_CODISS/B1_TE/B1_TS/B1_PICMRET/B1_PICMENT/B1_IMPZFRC/B1_SEGUM/B1_CONV/B1_TIPCONV/B1_CONTA/B1_CC/B1_ITEMCC/B1_ORIGEM/"
    cCmps	+=	"B1_CLASFIS/B1_GRTRIB/B1_CONTSOC/B1_IRRF/B1_IMPORT/B1_CODOBS/B1_OBS/B1_SITPROD/B1_INSS/B1_REDINSS/B1_REDIRRF/B1_TAB_IPI/"
    cCmps	+=	"B1_REDPIS/B1_REDCOF/B1_PCSLL/B1_PCOFINS/B1_PPIS/B1_VLR_IPI/B1_CLVL/B1_ATIVO/B1_VLR_ICM/B1_INT_ICM/B1_VLRSELO/B1_SELO/B1_PIS/"
    cCmps	+=	"B1_CLASSE/B1_VLR_PIS/B1_COFINS/B1_CSLL/B1_FRETISS/B1_CALCFET/B1_PAUTFET/B1_VLR_COF/B1_PRFDSUL/B1_RETOPER/B1_CNAE/B1_CRDEST/"
    cCmps	+=	cMVA010FAC

    aAdd(aPar,{"SB1","B1_COD+' - '+B1_DESC", cCmps,""})

    MATA984(aPar[1,1],aPar[1,2],aPar[1,3],,aPar[1,4])

Return .T.

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³MATA010   ºAutor  ³Andre Anjos         º Data ³  27/02/09   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³Valida o campo B1_ESTRORI                                   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ MATA010                                                    º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010EstOri()
    Local aArea := GetArea()
    Local lRet := .T.

    dbSelectArea("SG1")
    dbSetOrder(1)
    If !Empty(M->B1_ESTRORI) .And. !dbSeek(xFilial("SG1")+M->B1_ESTRORI+M->B1_COD) .Or. G1_QUANT > 0
        Help(" ",1,"REGNOIS")
        lRet := .F.
    EndIf

    RestArea(aArea)
Return lRet

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÚÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄ¿±±
±±³Fun‡ao    ³MA10VerAV  ³ Autor ³ Marco Aurelio - Mano    ³ Data ³19/05/11  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡ao ³Verifica se existe vinculo do produto que esta sendo excluido  ³±±
±±³          ³no cadastro de Apontamento de Visitas.                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Sintaxe   ³MA10VerAV()                                                    ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Parametros³                                                               ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Uso       ³MATA010                                                        ³±±
±±ÀÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
static Function MA10VerAV()
    Local cAliasTRB := GetNextAlias()	// Nome do arquivo temporario
    Local cQuery    := ""				// Auxiliar para execucao de query
    Local aArea     := GetArea()		// Salva area atual para posterior restauracao
    Local lRet      := .F.				// Conteudo de retorno

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Query para pesquisar o produto na tabela de Apontamento de Visitas(AD6) ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    cQuery := "SELECT * "

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Tabela base do filtro ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    cQuery += "FROM "
    cQuery += RetSqlName("AD6")+" AD6 "

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Condicoes de filtro ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    cQuery += "WHERE "
    cQuery += "AD6_FILIAL = '"+ xFilial("AD6")+"' AND "
    cQuery += "AD6_CODPRO = '"+ SB1->B1_COD   +"' AND "
    cQuery += "AD6.D_E_L_E_T_  <> '*'"

    cQuery := ChangeQuery(cQuery)

    DbUseArea(.T.,'TOPCONN',TCGENQRY(,,cQuery),cAliasTRB,.T.,.T.)

    If !(cAliasTRB)->(Eof())

        Help(" ",1,"APTNODEL") // Exclusao nao permitida deste produto pois existe vinculo do mesmo no cadastro Apontamento de Visitas.
        lRet := .T.

    EndIf

    (cAliasTRB)->(DbCloseArea())

    RestArea(aArea)

Return(lRet)

// -----------------------------------------------------------
/*/{Protheus.doc} A010VlStr
(long_description)
@type function
@author nilton.koyanagui
@since 22/04/2016
@version 1.0
@return ${return}, Possui (T) ou não (F) caracter especial
/*/
// -----------------------------------------------------------
//RETIRAR STATIC
Static Function A010VlStr ()

    Local lRet       	:= .T.
    Local cCaracter		:= "!@#$%¨&*()+{}^~´`][;.>,<=/¢¬§ªº'?*"
    Local cConteudo		:= Alltrim(&(ReadVar()))
    Local cCaracPip		:= "|'"
    Local nCont			:= 0

    For nCont := 1 to len(cConteudo)
        If substr(cConteudo,nCont,1) $ cCaracPip
            lret := .F.
        EndiF
    next nCont

    If !lRet
        Alert (STR0113)
    EndIf

Return lRet

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ A010CodBar   ºAutor  ³TOTVS S/A             º Data ³ 29/05/15 º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Validacao do tamanho do campo B1_CODBAR                       º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºRetorno   ³ .T. ou .F.                                                    º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010CodBar(cCodBar)
    Local lRet       := .T.
    Local nTamB1CBar := TamSX3("B1_CODBAR")[1]
    Local lVldCodBar := SuperGetMV("MV_ACDVLBA",.F.,.T.)

    If lVldCodBar
        If Len(AllTrim(cCodBar)) > nTamB1CBar - 1
            // "B1_CODBAR" ### "Digite no maximo " ### 15 ## "caracteres, pois o ultimo digito do campo de codigo de barras"
            //                                            "deve ser preenchido automaticamente pelo gatilho do campo B1_CODBAR."
            Aviso(STR0103,STR0104 + AllTrim(STR(nTamB1CBar - 1)) + STR0105 + STR0106,{STR0031})
            lRet := .F.
        EndIf
    EndIf

Return lRet

/*
| Programa : A010VLoc  			 Autor : TOTVS           Data : 26/11/2013
| Descricao: Valida local padrão diferente de MV_CQ
| Retorno  : .T. ou .F.
| Aplicacao: Chamada no valid do B1_LOCAL
*/
//RETIRAR STATIC
Static Function A010VLoc()
    Local lret:= .T.

    If M->B1_LOCPAD == GetMvNNR('MV_CQ','98')
        Help(" ",1,"A240LOCCQ")
        lRet := .F.
    Endif
Return lret

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ A010Hist     ºAutor  ³Wemerson Randolfo     º Data ³ 03/09/12 º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Visualizacao do historico das alteracoes                      º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºParametros³ Nao ha                                                        º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºRetorno   ³ .T. ou .F.                                                    º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºAplicacao ³ Funcao chamada pelo menu                                      º±±
±±º          ³                                                               º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function A010Hist()
    Local lRet

    lRet := HistOperFis("SS4",SB1->B1_COD,SB1->B1_DESC,"S4_COD")
Return lRet

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³IntegraSFCºAutor  ³ Aecio Ferreira Gomes º Data ³  29/09/11   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Valida Integração com SFC								    º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Integracao SFC                                            	º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function IntegraSFC()
    Local lRet		:= .F.
    Local xIntSFC	:= GetMV("MV_INTSFC",.F.,0)

    If ValType(xIntSFC) # "N"
        lRet := xIntSFC
    Else
        lRet := xIntSFC == 1
    EndIf

Return(lRet)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³IntegraDPRºAutor  ³ Leonardo Quintania   º Data ³  06/11/12   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ Valida Integração com o DPR(Desenvolvedor de Produtos)	    º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ Integracao DPR                                               º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
//RETIRAR STATIC
Static Function IntegraDPR()
    Local lRet		:= .F.

    lRet := SuperGetMv("MV_INTDPR",.F.,0) == 1

Return lRet

/*/{Protheus.doc} MTA010Mono
Gatilho para excluir do grid de fornecedores todos os fornecedores que não forem o fornecedor padrão do produto.

@author Juliane Venteu
@since 14/03/2017
@version P12.1.17

/*/
static Function MTA010Mono()
    Local oModel := FWModelActive()
    Local oGrid := oModel:GetModel("MdGridSA5")
    Local nX
    Local lFind := .F.
    Local nFind := 0
    Local oView := FWViewActive()

    If M->B1_MONO == "S" .And. !Empty(M->B1_PROC) .And. oGrid <> NIL
        // Desabilita a edição do grid SA5
        editGridSA5(.T.)

        For nX:=1 to oGrid:Length()
            oGrid:GoLine(nX)

            If oGrid:IsEmpty()
                oGrid:LoadValue("A5_FORNECE",M->B1_PROC)
                oGrid:LoadValue("A5_LOJA",M->B1_LOJPROC)
                oGrid:LoadValue("A5_NOMEFOR",Posicione("SA2",1,xFilial("SA2")+M->B1_PROC+M->B1_LOJPROC,"A2_NOME"))
            Else
                If oGrid:GetValue("A5_FORNECE") == M->B1_PROC .And. oGrid:GetValue("A5_LOJA") == M->B1_LOJPROC
                    If oGrid:IsDeleted()
                        oGrid:UnDeleteLine()
                    EndIf

                    lFind := .T.
                    nFind :=nX
                Else
                    If !oGrid:IsDeleted()
                        oGrid:DeleteLine()
                    EndIf
                EndIf

                If !lFind
                    oGrid:AddLine()
                    oGrid:LoadValue("A5_FORNECE",M->B1_PROC)
                    oGrid:LoadValue("A5_LOJA",M->B1_LOJPROC)
                    oGrid:LoadValue("A5_NOMEFOR",Posicione("SA2",1,xFilial("SA2")+M->B1_PROC+M->B1_LOJPROC,"A2_NOME"))
                Else
                    oGrid:GoLine(nFind)
                EndIf

                If oView <> NIL
                    oView:Refresh()
                EndIf
            EndIf
        Next nX

        // Desabilita a edição do grid SA5
        editGridSA5(.F.)
    EndIf

Return M->B1_PROC

/*/{Protheus.doc} MTAEanDig
Gatilho para B1_CODBAR
/*/
static Function MTAEanDig()
    Local oModel := FWModelActive()
    Local j
    Local nMultiplicador
    Local nSoma := 0
    Local nResultado := 0
    Local nDigito
    Local nTam := 0
    Local cCodigo:=''
    Local oField := oModel:GetModel("SB1MASTER")

    If !Empty(M->B1_CODBAR)
        cCodigo := AllTrim( M->B1_CODBAR )
        nTam := len(cCodigo)
        //-----------------------------------------------------------------//
        //Alterado função para utilizar modulo 10 de Calculo do EAN			//
        //-----------------------------------------------------------------//

        For j:= 1 To nTam    // Somatoria do conteudo do campo
            nMultiplicador := Iif( ( j % 2) == 0 , 1, 3 ) // varia entre 3 e 1
            nSoma += Int(Val(SubStr(cCodigo,(nTam+1)-j,1))) * nMultiplicador
        Next j

        nResultado := Int(nSoma / 10 ) + Iif(( nSoma % 10 ) > 0, 1 , 0 )  // Prox Multiplo 10
        nDigito   := nResultado * 10 - nSoma
        oField:LoadValue("B1_CODBAR",trim(m->B1_CODBAR)+Str( nDigito , 1 ))
    EndiF

Return
/*/{Protheus.doc} MTA010Proc
Gatilho para alterar o fornecedor padrão no SB1, se for um produto com distribuição por um unico fornecedor

@author Juliane Venteu
@since 14/03/2017
@version P12.1.17

/*/
static Function MTA010Proc()
    Local oModel := FWModelActive()
    Local oField := oModel:GetModel("SB1MASTER")
    Local cLoja := oModel:GetValue("MdGridSA5","A5_LOJA")

    If M->B1_MONO == "S"
        oField:LoadValue("B1_PROC", M->A5_FORNECE)
        oField:LoadValue("B1_LOJPROC", cLoja)
    EndIf

Return cLoja

/*/{Protheus.doc} editGridSA5
Essa função habilita/desabilita a inclusão e exclusão de linhas do gri de fornecedores,
se ele existir no modelo de dados.

Essa necessidade existe porque quando o produto é distribuido apenas por um fornecedor,
o usuario não deve conseguir adicionar e nem excluir novos fornecedores, deve existir apenas um
e se for necessario ele altera essa linha que já existe.

@param lEnable Se verdadeiro, habilita a inclusão/deleção de linha do grid de fornecedores

@author Juliane Venteu
@since 14/03/2017
@version P12.1.17

/*/
Static Function editGridSA5(lEnable)
    Local oModel := FWModelActive()
    Local oGrid := oModel:GetModel("MdGridSA5")

    If oGrid <> NIL
        oGrid:SetNoDeleteLine(!lEnable)
        oGrid:SetNoInsertLine(!lEnable)
    EndIf

Return

//------------------------------------------------------------------------------
/*/{Protheus.doc} A010ComPrd()

Abre o formulario do Complemento do Produto.

@sample 	A010ComPrd(cCodProd,nOpc)

@param		ExpC1 - Código do Produto
			ExpN3 - Numero da Operação

@return	Nenhum

@author	Anderson Silva
@since		11/07/2014
@version	12.0
/*/
//---------------------------------------------------------------------
//RETIRAR STATIC
Static Function A010ComPrd(cCodProd,nOpc)
    Local aArea 		:= GetArea()
    Local aAreaSB5	:= SB5->(GetArea())

    cCodProd := IIf(Empty(cCodProd),SB5->B5_COD,cCodProd)

    DbSelectArea("SB5")
    SB5->(DbSetOrder(1))

    If DbSeek(xFilial("SB5")+cCodProd)
        FWExecView(STR0093,"MATA180M",nOpc,,{|| .T.})
    Else
        MsgAlert(STR0094) // "Este produto não possui dados complementares."
    EndIf

    RestArea(aAreaSB5)
    RestArea(aArea)

Return Nil

/*/{Protheus.doc} A010Auto
Função criada para manter compatibilidade com a MSExecAuto.

@author Juliane Venteu
@since 02/03/2017
@version P12.1.17

/*/
Static Function A010Auto(nOpcAuto, xRotAuto)
    Local nOk
    Local oModel	:= FWLoadModel("MATA010")

    If FWMVCRotAuto(oModel,"SB1",nOpcAuto,{{"SB1MASTER",xRotAuto}},,.T.)
        // Realizado com sucesso
        If nOpcAuto == MODEL_OPERATION_DELETE
            nOk := 2
        Else
            nOk := 1
        EndIf
    Else
        // Erro
        If nOpcAuto == MODEL_OPERATION_DELETE
            nOk := 1
        Else
            nOk := 3
        EndIf
    EndIf

    // ---------------------------------------------------------------
    // Conteudo da variavel nOK mantido conforme documentado no TDN
    // http://tdn.totvs.com.br/pages/releaseview.action?pageId=6087683
    // ---------------------------------------------------------------
    If lMT010CAN
        nOk := NMt010Can(nOk,nOpcAuto)
        ExecBlock("MT010CAN",.F.,.F.,{nOK})
    EndIf

    oModel:DeActivate()
    oModel:Destroy()

Return

static Function Mta010Ceme()
    Local oModel	:= FWModelActive()
    Local oModSb5	:= oModel:GetModel("SB5DETAIL")
    Local cCeme	:= M->B1_DESC

    If oModSb5 <> NIL
        oModSb5:LoadValue("B5_CEME",cCeme)
    EndIf

Return cCeme

//---------------------------------------------------------
/*/{Protheus.doc} M010IniQtdSer
Inicializador do campo virtural B1_VRQTDSER
@author José Eulálio
@since 07/03/2018
@version 1.0
/*/
//---------------------------------------------------------
static Function M010IniQtdSer()
    Local cRet		:= "2"

    If INCLUI
        cRet := "1"
    Else
        cRet := IIf(ValType(SB1->B1_QTDSER) == "N",AllTrim(Str(SB1->B1_QTDSER)),SB1->B1_QTDSER)
    EndIf

Return cRet

//---------------------------------------------------------
/*/{Protheus.doc} Ma010QtdSer
Gatilho para atualizar o campo B1_QTDSER
@author José Eulálio
@since 07/03/2018
@version 1.0
/*/
//---------------------------------------------------------
static Function Ma010QtdSer()
    Local oModel		:= FWModelActive()
    Local oModSb1		:= oModel:GetModel("SB1MASTER")
    Local cVrQtdSer		:= oModSb1:GetValue("B1_VRQTDSER")
    Local xRet			:= IIf(ValType(oModSb1:GetValue('B1_QTDSER')) == "N",Val(cVrQtdSer),cVrQtdSer)

Return xRet

//---------------------------------------------------------
/*/{Protheus.doc} A010IntSFX
Função de Compatibilidade para que o MATA010 possa enxergar A static function A010IntSFC
@author José Eulálio
@since 05/03/2018
@version 1.0
/*/
//---------------------------------------------------------
static Function A010IntSFX(nOpc,cError,cNome,oModel)
Return A010IntSFC(nOpc,cError,cNome,oModel)

//---------------------------------------------------------
/*/{Protheus.doc} MATA010PPX
Função de Compatibilidade para que o MATA010 possa enxergar A static function MATA010PPI
@author José Eulálio
@since 05/03/2018
@version 1.0
/*/
//---------------------------------------------------------
static Function MATA010PPX(cXml, cProd, lExclusao, lFiltra, lPendAut)
Return MATA010PPI(cXml, cProd, lExclusao, lFiltra, lPendAut)

//---------------------------------------------------------
/*/{Protheus.doc} A010MONOX
Função de Compatibilidade para que o MATA010 possa enxergar A static function A010MONO
@author José Eulálio
@since 05/03/2018
@version 1.0
/*/
//---------------------------------------------------------
static Function A010MONOX()
Return A010MONO()

static Function A010Integ( cXML, nTypeTrans, cTypeMessage, cVersion, cTransac, lEAIObj )
    Default cXML 		:= ""
    Default nTypeTrans	:= ""
    Default cTypeMessage:= ""
    Default cVersion 	:= ""
    Default cTransac 	:= ""
    Default lEAIObj 	:= .F.

Return IntegDef( cXML, nTypeTrans, cTypeMessage, cVersion, cTransac, lEAIObj )

Static Function IntegDef( cXML, nTypeTrans, cTypeMessage, cVersion, cTransac, lEAIObj )
    Default cXML 		:= ""
    Default nTypeTrans	:= ""
    Default cTypeMessage:= ""
    Default cVersion 	:= ""
    Default cTransac 	:= ""
    Default lEAIObj 	:= .F.

Return MATI010(xEnt,nTypeTrans,cTypeMessage, cVersion, cTransac, lEAIObj )



//---------------------------------------------------------
/*/{Protheus.doc} A010B1Class
Valid para o campo B1_CLASSE
@author José Eulálio
@since 23/03/2018
@version 1.0
/*/
//---------------------------------------------------------
static Function A010B1Class()
    Local lRet			:= .T.
    Local cVar			:= &(ReadVar())
    Local cSavAlias	:= Alias()
    Local aAreaSX5	:= SX5->(GetArea())

    DbSelectArea("SX5")
    DbSeek(xFilial("SX5")+"A9"+cVar)

    If !Found()
        Help("  ",1,"REGNOIS")
        lRet := .F.
    EndIf

    dbSelectArea(cSavAlias)
    RestArea(aAreaSX5)

Return lRet

//---------------------------------------------------------
/*/{Protheus.doc} NMt010Can
Realiza compatibilidade entre o Retorno da Operação realizada
em MVC para o esperado pelo Ponto de Entrada MT010CAN
Documentações
MT010CAN - http://tdn.totvs.com/pages/viewpage.action?pageId=6087683
FwExecView - http://tdn.totvs.com/display/public/mp/FWExecView
@author José Eulálio
@since 23/03/2018
@version 1.0
/*/
//---------------------------------------------------------
Static Function NMt010Can(nOk,nOpc)
    Local nMt010Can	:= 0
    Local lDeleta	:= nOpc == MODEL_OPERATION_DELETE

    If nOk == 0
        If lDeleta
            nMt010Can := 2
        Else
            nMt010Can := 1
        EndIf
    ElseIf nOk == 1
        If lDeleta
            nMt010Can := 1
        Else
            nMt010Can := 3
        EndIf
    EndIf

Return nMt010Can



//--------------------------------------------------------------------------------------------------------------------
/*/{Protheus.doc} MenuDef
Definição do MenuDef

@return ExpO, Array, aRotina

@author luiz.jesus
@since 18/03/2014
@version 12
/*/
//--------------------------------------------------------------------------------------------------------------------
Static Function MenuDef()

    Local aRotina 	:= {}
    Local nPos		:= 0
    Local aAtiv		:= {}
    Local aAnotac	:= {}
    Local aEntRelac	:= {}

    ADD OPTION aRotina TITLE  "Consulta"    ACTION  "A010Consul" OPERATION 2 ACCESS 0 // "Visualizar"
    ADD OPTION aRotina TITLE  "Visualizar"    ACTION  "VIEWDEF.MATA010" OPERATION 2 ACCESS 0 // "Visualizar"
    ADD OPTION aRotina TITLE  "Incluir"       ACTION  "VIEWDEF.MATA010" OPERATION 3 ACCESS 0 // "Incluir"
    ADD OPTION aRotina TITLE  "Alterar"       ACTION  "VIEWDEF.MATA010" OPERATION 4 ACCESS 0 // "Alterar"
    ADD OPTION aRotina TITLE  "Excluir"       ACTION  "VIEWDEF.MATA010" OPERATION 5 ACCESS 0 // "Excluir"
    ADD OPTION aRotina TITLE  "Copiar"       ACTION  "VIEWDEF.MATA010" OPERATION 9 ACCESS 0 // "Copiar"

Return aRotina
