//Bibliotecas
#Include 'Protheus.ch'
#Include 'FWMVCDef.ch'

//Variáveis Estáticas
Static cTitulo := ""

/*/{Protheus.doc} CPARPOR
Cadastro de parametros PORTAIS - tabelas SX5 - CHAVE

@version 1.0
/*/
//User Function CPARPOR()
User Function DLP09F01()
    Local aArea   := GetArea()
    Local oBrowse
    Local cFunBkp := FunName()
    Default cTitRot := "Grupo Tributação"
    Default cTabela := "21"
    Private cTabX := cTabela

    //Senão tiver chave, finaliza
    If Empty(cTabela)
        Return
    EndIf

    DbSelectArea('SX5')
    SX5->(DbSetOrder(1)) // X5_FILIAL+X5_TABELA+X5_CHAVE
    SX5->(DbGoTop())

    //Se vier título por parâmetro
    If !Empty(cTitRot)
        cTitulo := cTitRot
    EndIf

    //Se ainda tiver em branco, pega o da própria tabela
    If Empty(cTitulo)
        //Se conseguir posicionar
        If SX5->(DbSeek(FWxFilial("SX5") + "00" + cTabela))
            cTitulo := SX5->X5_DESCRI
        Else
            MsgAlert("Tabela não encontrada!", "Atenção")
            Return
        EndIf
    EndIf

    //Instânciando FWMBrowse - Somente com dicionário de dados
    // SetFunName("DLP09F01")
    oBrowse := FWMBrowse():New()

    //Setando a tabela de cadastro de Autor/Interprete
    oBrowse:SetAlias("SX5")

    //Setando a descrição da rotina
    oBrowse:SetDescription(cTitulo)

    //Filtrando
    oBrowse:SetFilterDefault("SX5->X5_TABELA = '"+cTabela+"'")

    //Ativa a Browse
    oBrowse:Activate()

    SetFunName(cFunBkp)
    RestArea(aArea)
Return


Static Function MenuDef()
    Local aRot := {}

    //Adicionando opções
    ADD OPTION aRot TITLE 'Visualizar' ACTION 'VIEWDEF.DLP09F01' OPERATION MODEL_OPERATION_VIEW   ACCESS 0 //OPERATION 1
    ADD OPTION aRot TITLE 'Incluir'    ACTION 'VIEWDEF.DLP09F01' OPERATION MODEL_OPERATION_INSERT ACCESS 0 //OPERATION 3
    ADD OPTION aRot TITLE 'Alterar'    ACTION 'VIEWDEF.DLP09F01' OPERATION MODEL_OPERATION_UPDATE ACCESS 0 //OPERATION 4
    // ADD OPTION aRot TITLE 'Excluir'    ACTION 'VIEWDEF.DLP09F01' OPERATION MODEL_OPERATION_DELETE ACCESS 0 //OPERATION 5

Return aRot

Static Function ModelDef()
    //Criação do objeto do modelo de dados
    Local oModel := Nil

    //Criação da estrutura de dados utilizada na interface
    Local oStSX5 := FWFormStruct(1, "SX5")

    //Editando características do dicionário
    oStSX5:SetProperty('X5_TABELA',   MODEL_FIELD_INIT,    {|| "21"	} )                   //Ini Padrão
    oStSX5:SetProperty('X5_TABELA',   MODEL_FIELD_WHEN,    FwBuildFeature(STRUCT_FEATURE_WHEN,    '.F.'))                       //Modo de Edição
    //oStSX5:SetProperty('X5_TABELA',   MODEL_FIELD_INIT,    FwBuildFeature(STRUCT_FEATURE_INIPAD,  'cTabX'))                     //Ini Padrão

    oStSX5:SetProperty('X5_CHAVE',    MODEL_FIELD_WHEN,    FwBuildFeature(STRUCT_FEATURE_WHEN,    '.T.'))     //Modo de Edição
    oStSX5:SetProperty('X5_CHAVE',    MODEL_FIELD_VALID,   FwBuildFeature(STRUCT_FEATURE_VALID,   'u_zSX5Chv()'))               //Validação de Campo
    oStSX5:SetProperty('X5_CHAVE',    MODEL_FIELD_OBRIGAT, .T. )                                                                //Campo Obrigatório
    oStSX5:SetProperty('X5_DESCRI',   MODEL_FIELD_OBRIGAT, .T. )                                                                //Campo Obrigatório

    //Instanciando o modelo, não é recomendado colocar nome da user function (por causa do u_), respeitando 10 caracteres
    oModel := MPFormModel():New("DLP09F01M",/*bPre*/,/*bPos*/,/*bCommit*/,/*bCancel*/)

    //Atribuindo formulários para o modelo
    oModel:AddFields("FORMSX5",/*cOwner*/,oStSX5)

    //Setando a chave primária da rotina
    oModel:SetPrimaryKey({'X5_FILIAL', 'X5_TABELA', 'X5_CHAVE'})

    //Adicionando descrição ao modelo
    oModel:SetDescription("Modelo de Dados do Cadastro "+cTitulo)

    //Setando a descrição do formulário
    oModel:GetModel("FORMSX5"):SetDescription("Formulário do Cadastro "+cTitulo)
Return oModel


Static Function ViewDef()
    //Criação do objeto do modelo de dados da Interface do Cadastro de Autor/Interprete
    Local oModel := FWLoadModel("DLP09F01")

    //Criação da estrutura de dados utilizada na interface do cadastro de Autor
    Local oStSX5 := FWFormStruct(2, "SX5")  //pode se usar um terceiro parâmetro para filtrar os campos exibidos { |cCampo| cCampo $ 'SX5_NOME|SX5_DTAFAL|'}

    //Criando oView como nulo
    Local oView := Nil

    //Criando a view que será o retorno da função e setando o modelo da rotina
    oView := FWFormView():New()
    oView:SetModel(oModel)

    //Atribuindo formulários para interface
    oView:AddField("VIEW_SX5", oStSX5, "FORMSX5")

    //Criando um container com nome tela com 100%
    oView:CreateHorizontalBox("TELA",100)

    //Colocando título do formulário
    oView:EnableTitleView('VIEW_SX5', 'Dados - '+cTitulo )

    //Força o fechamento da janela na confirmação
    oView:SetCloseOnOk({||.T.})

    //O formulário da interface será colocado dentro do container
    oView:SetOwnerView("VIEW_SX5","TELA")

    //Retira o campo de tabela da visualização
    oStSX5:RemoveField("X5_TABELA")
Return oView



User Function zSX5Chv()
    Local aArea    := GetArea()
    Local lRet     := .T.
    Local cX5Chave := M->X5_CHAVE

    DbSelectArea('SX5')
    SX5->(DbSetOrder(1)) // X5_FILIAL+X5_TABELA+X5_CHAVE
    SX5->(DbGoTop())

    //Se conseguir posicionar, já existe
    If SX5->(DbSeek(FWxFilial('SX5') + cTabX + cX5Chave))
        MsgAlert("Já existe chave com esse código (<b>"+cX5Chave+"</b>)!", "Atenção")
        lRet := .F.
    EndIf

    RestArea(aArea)
Return lRet
