#INCLUDE 'PROTHEUS.CH'
#INCLUDE 'FWMVCDEF.CH'

Static cTitulo := "Usuários x Setores"

User Function DLP73F08()

	Local aArea := GetArea()
	Local oBrowse As Object

	Private cCodTec := Nil //oModel:GetValue("ZB_CODUSUA")

	Private lVldTec := .F.

	// Instanciando FWMBrowse - Somente com dicionário de dados
	oBrowse := FWMBrowse():New()

	//Setando a tabela de cadastro, nesse caso a SZB
	oBrowse:SetAlias("SZB")

	//Setando a descrição da rotina
	oBrowse:SetDescription(cTitulo)

	oBrowse:SetMenuDef('DLP73F08')

	//Ativa o Browse
	oBrowse:Activate()

	RestArea(aArea)

Return Nil


Static Function MenuDef()
	Local aRotina := {}

	//Adicionando opções
	ADD OPTION aRotina TITLE 'Visualizar' ACTION 'VIEWDEF.DLP73F08' OPERATION 2/*MODEL_OPERATION_VIEW*/   ACCESS 0
	ADD OPTION aRotina TITLE 'Incluir'    ACTION 'VIEWDEF.DLP73F08' OPERATION 3/*MODEL_OPERATION_INSERT*/ ACCESS 0
	ADD OPTION aRotina TITLE 'Alterar'    ACTION 'VIEWDEF.DLP73F08' OPERATION 4/*MODEL_OPERATION_UPDATE*/ ACCESS 0
	ADD OPTION aRotina TITLE 'Excluir'    ACTION 'VIEWDEF.DLP73F08' OPERATION 5/*MODEL_OPERATION_DELETE*/ ACCESS 0

Return aRotina


Static Function ModelDef()
	//Criação do objeto do modelo de dados
	Local oModel As Object

	//Criação da estrutura de dados utilizada na interface
	Local oStSZBm := FWFormStruct(1 /*1-Model | 2-View*/, "SZB" /*Alias da tabela*/)

	//Instanciando o modelo, não é recomendado colocar o mesmo nome da user function (por causa do u_), respeitando 10 caracteres
	oModel := MPFormModel():New("D73F8M", /*bPre*/, /*bPos*/, /*bCommit*/, /*bCancel*/)

	//Atribuindo formulários para o modelo
	oModel:AddFields("SZBMASTER", /*cOwner*/, oStSZBm)

	//Setando a chave primaria
	oModel:SetPrimaryKey({'ZB_FILIAL','ZB_CODUSUA'})

	oStSZBm:SetProperty( 'ZB_CODUSUA' , MODEL_FIELD_VALID, {|oModel| fVldCodCpo(oModel) } )
	oStSZBm:SetProperty( 'ZB_CODUSUA' , MODEL_FIELD_OBRIGAT, .T. )

	oStSZBm:SetProperty( 'ZB_NOMUSUA' , MODEL_FIELD_WHEN, {|| lVldTec } )
	oStSZBm:SetProperty( 'ZB_EMAIL'   , MODEL_FIELD_WHEN, {|| lVldTec } )

	oStSZBm:SetProperty( 'ZB_SETOROP' , MODEL_FIELD_OBRIGAT, .T. )

	//Setando a descrição do formulário
	oModel:GetModel("SZBMASTER"):SetDescription("Modelo de Teste "+cTitulo)

Return oModel


Static Function ViewDef()
	//Criação do objeto do modelo de dados da interface
	Local oModel := FWLoadModel("DLP73F08")

	//Criação da estrutura de dados utilizada na interface
	Local oStSZBv := FWFormStruct(2 /*1-Model | 2-View*/, "SZB"/*Alias da tabela*/)

	//Criando o objeto oView
	Local oView As Object

	//Criando a view que será o retorno da função e setando o modelo da rotina
	oView := FWFormView():New()
	oView:SetModel(oModel)

	//Atribuindo formulários para interface
	oView:AddField("VIEW_SZB", oStSZBv, "SZBMASTER")

	oStSZBv:SetProperty("ZB_CODUSUA" , MVC_VIEW_TITULO, "Código Usuário")
	oStSZBv:SetProperty("ZB_NOMUSUA" , MVC_VIEW_TITULO, "Nome")
	oStSZBv:SetProperty("ZB_EMAIL"   , MVC_VIEW_TITULO, "Email")
	oStSZBv:SetProperty("ZB_SETOROP" , MVC_VIEW_TITULO, "Setor")

	//Criando um container com nome tela 100%
	oView:CreateHorizontalBox("SUPERIOR", 100)

	//O formulario da interface será colocado dentro do container
	oView:SetOwnerView("VIEW_SZB", "SUPERIOR")

	//Forçar o fechamento da janela na confirmação
	oView:SetCloseOnOk({||.T.})

Return oView

Static Function fVldCodCpo(oModel)

	cCodTec := oModel:GetValue("ZB_CODUSUA")

	Local lRet := .F.

	If (oModel:GetOperation() == 3) .OR. (oModel:GetOperation() == 4)
		If !Empty(oModel:GetValue('ZB_CODUSUA'))
			If UsrExist( cCodTec )

				lVldTec := .t.
				oModel:setvalue("ZB_NOMUSUA", UsrRetName(cCodTec))
				oModel:setvalue("ZB_EMAIL"  , UsrRetMail(cCodTec))
				lVldTec := .f.

				lRet :=.T.
			else
				ALERT("Necessário informar um Técnico")
				lRet := .F.
			EndIf
		EndIf 
	EndIf 

Return lRet
