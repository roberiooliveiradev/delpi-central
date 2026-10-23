#INCLUDE 'PROTHEUS.CH'
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE 'FWEditPanel.CH'

Static cTitulo := "Formulário LMP"

/**/
User Function DLP73F07()

	Local aArea := GetArea()
	Local oBrowse As Object


	Private cDscEng1 := "Estrutura de Produto cadastrada ?"
	Private cDscEng2 := "Roteiro de Produto já cadastrado ?"
	Private cDscEng3 := "Desenho já está no Protheus ?"
	Private cDscVND1 := "Os dados de entrada estão corretos ?"
	Private cDscVND2 := "Existe desenho e/ou especificações técnicas?"
	Private cDscVND3 := "O material precisa de alguma certificação  ? (UL, Rohs, CSA etc.)"
	Private cDscVND4 := "É necessario fazer amostras ?"

	Private lVEngProd := fVldEngPrd()
	Private lVEngProc := fVldEngPrc()
	Private lVldPcp   := fVldPcp()
	Private lVldQual  := fVldQuali()
	Private lVldVnd   := fVldVnd()

	Private lVldSts := .F.
	Private lVldLmp := .F.

	// Instanciando FWMBrowse - Somente com dicionário de dados
	oBrowse := FWMBrowse():New()

	//Setando a tabela de cadastro, nesse caso a SZA
	oBrowse:SetAlias("SZA")

	//Setando a descrição da rotina
	oBrowse:SetDescription(cTitulo)

	oBrowse:SetMenuDef('DLP73F07')

	//Ativa o Browse
	oBrowse:Activate()

	RestArea(aArea)

Return Nil

/**/
Static Function MenuDef()
	Local aRotina := {}

	//Adicionando opções
	ADD OPTION aRotina TITLE 'Visualizar' ACTION 'VIEWDEF.DLP73F07' OPERATION 2/*MODEL_OPERATION_VIEW*/   ACCESS 0
	ADD OPTION aRotina TITLE 'Incluir'    ACTION 'VIEWDEF.DLP73F07' OPERATION 3/*MODEL_OPERATION_INSERT*/ ACCESS 0
	ADD OPTION aRotina TITLE 'Alterar'    ACTION 'VIEWDEF.DLP73F07' OPERATION 4/*MODEL_OPERATION_UPDATE*/ ACCESS 0
	ADD OPTION aRotina TITLE 'Excluir'    ACTION 'VIEWDEF.DLP73F07' OPERATION 5/*MODEL_OPERATION_DELETE*/ ACCESS 0

Return aRotina

/**/
User Function D73F7OK(oModel)

	Local lRet := .T.
	Local cCodUsr := RetCodUsr()
	Local cNomUsr := UsrRetName(cCodUsr)
	Local oMdlSza := oModel:GetModel("SZAMASTER")

	If (oModel:GetOperation() == 3) .or. (oModel:GetOperation() == 4 )
		If lVEngProd
			if 	!empty(oMdlSza:getvalue( 'ZA_EPRD01A')) .and. ;
					!empty(oMdlSza:getvalue( 'ZA_EPRD01D')) .and. ;
					!empty(oMdlSza:getvalue( 'ZA_EPRD02A')) .and. ;
					!empty(oMdlSza:getvalue( 'ZA_EPRD02D')) .and. ;
					!empty(oMdlSza:getvalue( 'ZA_EPRD03A')) .and. ;
					!empty(oMdlSza:getvalue( 'ZA_EPRD03D'))

				lVldSts := .T.
				oMdlSza:Setvalue( 'ZA_STCODU1', cCodUsr)
				oMdlSza:Setvalue( 'ZA_STNOMU1', cNomUsr)
				oMdlSza:Setvalue( 'ZA_STDATA1', DATE())
				lVldSts := .F.
			EndIf
		EndIf

		//	If lVEngProc
		//		If  !Empty(oMdlSza:GetValue( 'ZA_EPRC01A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_EPRC01D' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_EPRC02A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_EPRC02D' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_EPRC03A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_EPRC03D' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_EPRC04A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_EPRC04D' ))
//
		//			lVldSts := .T.
		//			oMdlSza:SetValue( 'ZA_STCODU2', cCodUsr)
		//			oMdlSza:SetValue( 'ZA_STNOMU2', cNomUsr)
		//			oMdlSza:SetValue( 'ZA_STDATA2', Date())
//
		//			lVldSts := .F.
		//		EndIf
		//	EndIf

		//	If lVldPcp
		//		If  !Empty(oMdlSza:GetValue( 'ZA_PCP01A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_PCP01D' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_PCP02A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_PCP02D' ))
//
		//			lVldSts := .T.
		//			oMdlSza:SetValue( 'ZA_STCODU3', cCodUsr)
		//			oMdlSza:SetValue( 'ZA_STNOMU3', cNomUsr)
		//			oMdlSza:SetValue( 'ZA_STDATA3', Date())
//
		//			lVldSts := .F.
		//		EndIf
		//	EndIf

		//	If lVldQual
		//		If  !Empty(oMdlSza:GetValue( 'ZA_QLID01A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_QLID01D' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_QLID02A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_QLID02D' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_QLID03A' )) .and. ;
			//				!Empty(oMdlSza:GetValue( 'ZA_QLID03D' ))
//
		//			lVldSts := .T.
		//			oMdlSza:SetValue( 'ZA_STCODU4', cCodUsr)
		//			oMdlSza:SetValue( 'ZA_STNOMU4', cNomUsr)
		//			oMdlSza:SetValue( 'ZA_STDATA4', Date())
//
		//			lVldSts := .F.
		//		EndIf
		//	EndIf

		If lVldQual
			If      !Empty(oMdlSza:GetValue( 'ZA_VND01A' )) .and. ;
					!Empty(oMdlSza:GetValue( 'ZA_VND01D' )) .and. ;
					!Empty(oMdlSza:GetValue( 'ZA_VND02A' )) .and. ;
					!Empty(oMdlSza:GetValue( 'ZA_VND02D' )) .and. ;
					!Empty(oMdlSza:GetValue( 'ZA_VND03A' )) .and. ;
					!Empty(oMdlSza:GetValue( 'ZA_VND03D' )) .and. ;
					!Empty(oMdlSza:GetValue( 'ZA_VND04A' )) .and. ;
					!Empty(oMdlSza:GetValue( 'ZA_VND04D' ))

				lVldSts := .T.
				oMdlSza:SetValue( 'ZA_STCODU5', cCodUsr)
				oMdlSza:SetValue( 'ZA_STNOMU5', cNomUsr)
				oMdlSza:SetValue( 'ZA_STDATA5', Date())

				lVldSts := .F.
			EndIf
		EndIf
	EndIf

Return lRet

/**/
Static Function ModelDef()
	//Criação do objeto do modelo de dados
	Local oModel As Object

	//Criação da estrutura de dados utilizada na interface
	Local oStSZAm := FWFormStruct(1, "SZA")

	//Instanciando o modelo, não é recomendado colocar o mesmo nome da user function (por causa do u_), respeitando 10 caracteres
	//oModel := MPFormModel():New("D73F7M", /*bPre*/, /*bPos*/, /*bCommit*/, /*bCancel*/)
	oModel := MPFormModel():New('D73F7M',/*bPre*/, {|oModel| U_D73F7OK(oModel)}/* bTudoOK*/,/* {|oModel| U_D73F7OK(oModel)} */)

	//Atribuindo formulários para o modelo
	oModel:AddFields("SZAMASTER", /*cOwner*/, oStSZAm)

	//Setando a chave primaria
	oModel:SetPrimaryKey({'ZA_FILIAL','ZA_NROPOR'})

	//Setando a descrição do formulário
	oModel:SetDescription("Delpi - "+cTitulo)

	// Aba Analise - Eng. Produtos
	oStSZAm:SetProperty( 'ZA_EPRD01A' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	oStSZAm:SetProperty( 'ZA_EPRD01D' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	oStSZAm:SetProperty( 'ZA_EPRD02A' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	oStSZAm:SetProperty( 'ZA_EPRD02D' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	oStSZAm:SetProperty( 'ZA_EPRD03A' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	oStSZAm:SetProperty( 'ZA_EPRD03D' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	//oStSZAm:SetProperty( 'ZA_EPRD04A' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	//oStSZAm:SetProperty( 'ZA_EPRD04D' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	//oStSZAm:SetProperty( 'ZA_EPRD05A' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	//oStSZAm:SetProperty( 'ZA_EPRD05D' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	//oStSZAm:SetProperty( 'ZA_EPRD06A' , MODEL_FIELD_WHEN , {|| lVEngProd } )
	//oStSZAm:SetProperty( 'ZA_EPRD06D' , MODEL_FIELD_WHEN , {|| lVEngProd } )

	// Aba Analise - Eng. Processos
	//oStSZAm:SetProperty( 'ZA_EPRC01A' , MODEL_FIELD_WHEN , {|| lVEngProc } )
	//oStSZAm:SetProperty( 'ZA_EPRC01D' , MODEL_FIELD_WHEN , {|| lVEngProc } )
	//oStSZAm:SetProperty( 'ZA_EPRC02A' , MODEL_FIELD_WHEN , {|| lVEngProc } )
	//oStSZAm:SetProperty( 'ZA_EPRC02D' , MODEL_FIELD_WHEN , {|| lVEngProc } )
	//oStSZAm:SetProperty( 'ZA_EPRC03A' , MODEL_FIELD_WHEN , {|| lVEngProc } )
	//oStSZAm:SetProperty( 'ZA_EPRC03D' , MODEL_FIELD_WHEN , {|| lVEngProc } )
	//oStSZAm:SetProperty( 'ZA_EPRC04A' , MODEL_FIELD_WHEN , {|| lVEngProc } )
	//oStSZAm:SetProperty( 'ZA_EPRC04D' , MODEL_FIELD_WHEN , {|| lVEngProc } )

	// Aba Analise - PCP
//oStSZAm:SetProperty( 'ZA_PCP01A' , MODEL_FIELD_WHEN , {|| lVldPcp } )
//oStSZAm:SetProperty( 'ZA_PCP01D' , MODEL_FIELD_WHEN , {|| lVldPcp } )
//oStSZAm:SetProperty( 'ZA_PCP02A' , MODEL_FIELD_WHEN , {|| lVldPcp } )
//oStSZAm:SetProperty( 'ZA_PCP02D' , MODEL_FIELD_WHEN , {|| lVldPcp } )

	// Aba Analise - Qualidade
//oStSZAm:SetProperty( 'ZA_QLID01A' , MODEL_FIELD_WHEN , {|| lVldQual } )
//oStSZAm:SetProperty( 'ZA_QLID01D' , MODEL_FIELD_WHEN , {|| lVldQual } )
//oStSZAm:SetProperty( 'ZA_QLID02A' , MODEL_FIELD_WHEN , {|| lVldQual } )
//oStSZAm:SetProperty( 'ZA_QLID02D' , MODEL_FIELD_WHEN , {|| lVldQual } )
//oStSZAm:SetProperty( 'ZA_QLID03A' , MODEL_FIELD_WHEN , {|| lVldQual } )
//oStSZAm:SetProperty( 'ZA_QLID03D' , MODEL_FIELD_WHEN , {|| lVldQual } )

	oStSZAm:SetProperty( 'ZA_VND01A' , MODEL_FIELD_WHEN , {|| lVldVnd } )
	oStSZAm:SetProperty( 'ZA_VND01D' , MODEL_FIELD_WHEN , {|| lVldVnd } )
	oStSZAm:SetProperty( 'ZA_VND02A' , MODEL_FIELD_WHEN , {|| lVldVnd } )
	oStSZAm:SetProperty( 'ZA_VND02D' , MODEL_FIELD_WHEN , {|| lVldVnd } )
	oStSZAm:SetProperty( 'ZA_VND03A' , MODEL_FIELD_WHEN , {|| lVldVnd } )
	oStSZAm:SetProperty( 'ZA_VND03D' , MODEL_FIELD_WHEN , {|| lVldVnd } )
	oStSZAm:SetProperty( 'ZA_VND04A' , MODEL_FIELD_WHEN , {|| lVldVnd } )
	oStSZAm:SetProperty( 'ZA_VND04D' , MODEL_FIELD_WHEN , {|| lVldVnd } )

	// Aba Status - Eng. Produtos
	oStSZAm:SetProperty( 'ZA_STCODU1' , MODEL_FIELD_WHEN , {|| lVldSts } )
	oStSZAm:SetProperty( 'ZA_STNOMU1' , MODEL_FIELD_WHEN , {|| lVldSts } )
	oStSZAm:SetProperty( 'ZA_STDATA1' , MODEL_FIELD_WHEN , {|| lVldSts } )

//	// Aba Status - Eng. Processos
//	oStSZAm:SetProperty( 'ZA_STCODU2' , MODEL_FIELD_WHEN , {|| lVldSts } )
//	oStSZAm:SetProperty( 'ZA_STNOMU2' , MODEL_FIELD_WHEN , {|| lVldSts } )
//	oStSZAm:SetProperty( 'ZA_STDATA2' , MODEL_FIELD_WHEN , {|| lVldSts } )
//
//	// Aba Status - PCP
//	oStSZAm:SetProperty( 'ZA_STCODU3' , MODEL_FIELD_WHEN , {|| lVldSts } )
//	oStSZAm:SetProperty( 'ZA_STNOMU3' , MODEL_FIELD_WHEN , {|| lVldSts } )
//	oStSZAm:SetProperty( 'ZA_STDATA3' , MODEL_FIELD_WHEN , {|| lVldSts } )

	// Aba Status - Qualidade
	oStSZAm:SetProperty( 'ZA_STCODU4' , MODEL_FIELD_WHEN , {|| lVldSts } )
	oStSZAm:SetProperty( 'ZA_STNOMU4' , MODEL_FIELD_WHEN , {|| lVldSts } )
	oStSZAm:SetProperty( 'ZA_STDATA4' , MODEL_FIELD_WHEN , {|| lVldSts } )
	// Aba Status - Venda
	oStSZAm:SetProperty( 'ZA_STCODU5' , MODEL_FIELD_WHEN , {|| lVldSts } )
	oStSZAm:SetProperty( 'ZA_STNOMU5' , MODEL_FIELD_WHEN , {|| lVldSts } )
	oStSZAm:SetProperty( 'ZA_STDATA5' , MODEL_FIELD_WHEN , {|| lVldSts } )

	// Aba LMP
	oStSZAm:SetProperty( 'ZA_NROPOR'  , MODEL_FIELD_VALID , {|oModel| fSetAba1(oModel) } )
	oStSZAm:SetProperty( 'ZA_NROPOR'  , MODEL_FIELD_OBRIGAT, .T. )

	oStSZAm:SetProperty( 'ZA_CODCLI'  , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_LOJACLI' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_EMAIL'   , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_NOMCONT' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_FONE'    , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_RAZSOCI' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_CODPRD' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_DSCPRD' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_ITECLI' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_DESENH' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_AMOSTR' , MODEL_FIELD_WHEN , {|| lVldLmp } )
	oStSZAm:SetProperty( 'ZA_QTDAMS' , MODEL_FIELD_WHEN , {|| lVldLmp } )

	oStSZAm:SetProperty("ZA_EPRD01A",MODEL_FIELD_TITULO,cDscEng1)
	oStSZAm:SetProperty("ZA_EPRD01D",MODEL_FIELD_TITULO,"")
	oStSZAm:SetProperty("ZA_EPRD02A",MODEL_FIELD_TITULO,cDscEng2)
	oStSZAm:SetProperty("ZA_EPRD02D",MODEL_FIELD_TITULO,"")
	oStSZAm:SetProperty("ZA_EPRD03A",MODEL_FIELD_TITULO,cDscEng3)
	oStSZAm:SetProperty("ZA_EPRD03D",MODEL_FIELD_TITULO,"")
//oStSZAm:SetProperty("ZA_EPRD04A",MODEL_FIELD_TITULO,"Existem componentes empregados no produto que são fornecidos pelo cliente?                        ")
//oStSZAm:SetProperty("ZA_EPRD04D",MODEL_FIELD_TITULO,"")
//oStSZAm:SetProperty("ZA_EPRD05A",MODEL_FIELD_TITULO,"Existe a necessidade de desenvolvimento de novos fornecedores?                                    ")
//oStSZAm:SetProperty("ZA_EPRD05D",MODEL_FIELD_TITULO,"")
//oStSZAm:SetProperty("ZA_EPRD06A",MODEL_FIELD_TITULO,"As características e tolerâncias dimensionais foram atendidas/respeitadas?                        ")
//oStSZAm:SetProperty("ZA_EPRD06D",MODEL_FIELD_TITULO,"")

	//Mudando os nomes de exibição dos campos Engenharia de Processos
//	oStSZAm:SetProperty("ZA_EPRC01A",MODEL_FIELD_TITULO,"A Empresa possui as máquinas, ferramentas e dispositivos necessários para produção do item?       ")
//	oStSZAm:SetProperty("ZA_EPRC01D",MODEL_FIELD_TITULO,"")
//	oStSZAm:SetProperty("ZA_EPRC02A",MODEL_FIELD_TITULO,"Requer algum serviço terceirizado?                                                                ")
//	oStSZAm:SetProperty("ZA_EPRC02D",MODEL_FIELD_TITULO,"")
//	oStSZAm:SetProperty("ZA_EPRC03A",MODEL_FIELD_TITULO,"Necessita de algum investimento adicional?                                                        ")
//	oStSZAm:SetProperty("ZA_EPRC03D",MODEL_FIELD_TITULO,"")
//	oStSZAm:SetProperty("ZA_EPRC04A",MODEL_FIELD_TITULO,"Tempo Hs/Mil                                                                                      ")
//	oStSZAm:SetProperty("ZA_EPRC04D",MODEL_FIELD_TITULO,"")

	//Mudando os nomes de exibição dos campos PCP
	//oStSZAm:SetProperty("ZA_PCP01A",MODEL_FIELD_TITULO,"A data de entrega está de acordo com Disponibilidade da Matéria prima e capacidade da Fábrica?     ")
	//oStSZAm:SetProperty("ZA_PCP01D",MODEL_FIELD_TITULO,"")
	//oStSZAm:SetProperty("ZA_PCP02A",MODEL_FIELD_TITULO,"Existe ordens de produção em processo para o item?                                                 ")
	//oStSZAm:SetProperty("ZA_PCP02D",MODEL_FIELD_TITULO,"")

	//Mudando os nomes de exibição dos campos Qualidade
//	oStSZAm:SetProperty("ZA_QLID01A",MODEL_FIELD_TITULO,"O material precisa de alguma certificação? (UL, Rohs, CSA etc.)                                   ")
//	oStSZAm:SetProperty("ZA_QLID01D",MODEL_FIELD_TITULO,"")
//	oStSZAm:SetProperty("ZA_QLID02A",MODEL_FIELD_TITULO,"A empresa possui equipamentos de medição para controlar as especificações do item?                ")
//	oStSZAm:SetProperty("ZA_QLID02D",MODEL_FIELD_TITULO,"")
//	oStSZAm:SetProperty("ZA_QLID03A",MODEL_FIELD_TITULO,"O produto requer verificações ou testes funcionais? (Passagem, tensão, tração etc.)               ")
//	oStSZAm:SetProperty("ZA_QLID03D",MODEL_FIELD_TITULO,"")

//Mudando os nomes de exibição dos campos VENDAS

	oStSZAm:SetProperty("ZA_VND01A",MODEL_FIELD_TITULO,cDscVND1)
	oStSZAm:SetProperty("ZA_VND01D",MODEL_FIELD_TITULO,"")
	oStSZAm:SetProperty("ZA_VND02A",MODEL_FIELD_TITULO,cDscVND2)
	oStSZAm:SetProperty("ZA_VND02D",MODEL_FIELD_TITULO,"")
	oStSZAm:SetProperty("ZA_VND03A",MODEL_FIELD_TITULO,cDscVND3)
	oStSZAm:SetProperty("ZA_VND03D",MODEL_FIELD_TITULO,"")
	oStSZAm:SetProperty("ZA_VND04A",MODEL_FIELD_TITULO,cDscVND4)
	oStSZAm:SetProperty("ZA_VND04D",MODEL_FIELD_TITULO,"")



	//Mudando os nomes de exibição dos campos Cadastro
	oStSZAm:SetProperty("ZA_NROPOR",MODEL_FIELD_TITULO,"OV")
	oStSZAm:SetProperty("ZA_CODCLI",MODEL_FIELD_TITULO,"Cliente")
	oStSZAm:SetProperty("ZA_LOJACLI",MODEL_FIELD_TITULO,"Loja")
	oStSZAm:SetProperty("ZA_EMAIL",MODEL_FIELD_TITULO,"Email")
	oStSZAm:SetProperty("ZA_NOMCONT",MODEL_FIELD_TITULO,"Contato")
	oStSZAm:SetProperty("ZA_FONE",MODEL_FIELD_TITULO,"Telefone")
	oStSZAm:SetProperty("ZA_RAZSOCI",MODEL_FIELD_TITULO,"Razão Social")
	oStSZAm:SetProperty("ZA_CODPRD",MODEL_FIELD_TITULO,"Codigo Produto")
	oStSZAm:SetProperty("ZA_DSCPRD",MODEL_FIELD_TITULO,"Desc Produto")
	oStSZAm:SetProperty("ZA_ITECLI",MODEL_FIELD_TITULO,"Item Cliente")
	oStSZAm:SetProperty("ZA_DESENH",MODEL_FIELD_TITULO,"Desenho")
	oStSZAm:SetProperty("ZA_AMOSTR",MODEL_FIELD_TITULO,"Amostra ?")
	oStSZAm:SetProperty("ZA_QTDAMS",MODEL_FIELD_TITULO,"Qtd Amostra")
	//	oStSZAm:SetProperty("ZA_DESCMOT",MODEL_FIELD_TITULO,"Descrição do Motivo")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAm:SetProperty("ZA_STCODU1",MODEL_FIELD_TITULO,"Resp. Engenharia")
	oStSZAm:SetProperty("ZA_STCODU5",MODEL_FIELD_TITULO,"Resp. Vendas")
	//oStSZAm:SetProperty("ZA_STCODU2",MODEL_FIELD_TITULO,"Resp. Eng.Processos")
	//oStSZAm:SetProperty("ZA_STCODU3",MODEL_FIELD_TITULO,"Resp. PCP")
	//oStSZAm:SetProperty("ZA_STCODU4",MODEL_FIELD_TITULO,"Resp. Qualidade")



	//oStSZAm:SetProperty( 'ZA_DESCMOT' , MODEL_FIELD_WHEN , {|| lVldLmp } )

Return oModel

/**/
Static Function ViewDef()
	//Criação do objeto do modelo de dados da interface
	Local oModel := FWLoadModel("DLP73F07")

	//Criação da estrutura de dados utilizada na interface
	Local oStSZAv := FWFormStruct(2, "SZA", {|cCampo| AllTrim(cCampo) $ "ZA_EPRD01A|ZA_EPRD01D|ZA_EPRD02A|ZA_EPRD02D|ZA_EPRD03A|ZA_EPRD03D|ZA_EPRD04A|ZA_EPRD04D|ZA_EPRD05A|ZA_EPRD05D|ZA_EPRD06A|ZA_EPRD06D|ZA_EPRC01A|ZA_EPRC01D|ZA_EPRC02A|ZA_EPRC02D|ZA_EPRC03A|ZA_EPRC03D|ZA_EPRC04A|ZA_EPRC04D|ZA_PCP01A|ZA_PCP01D|ZA_PCP02A|ZA_PCP02D|ZA_QLID01A|ZA_QLID01D|ZA_QLID02A|ZA_QLID02D|ZA_QLID03A|ZA_QLID03D"})
	// Local oStSZAx := FWFormStruct(2, "SZA", {|cCampo| AllTrim(cCampo) $ "ZA_NROPOR|ZA_CODCLI|ZA_LOJACLI|ZA_EMAIL|ZA_NOMCONT|ZA_FONE|ZA_RAZSOCI|ZA_DESCMOT"})
	Local oStSZAx := FWFormStruct(2, "SZA", {|cCampo| AllTrim(cCampo) $ "ZA_NROPOR|ZA_CODCLI|ZA_LOJACLI|ZA_EMAIL|ZA_NOMCONT|ZA_FONE|ZA_RAZSOCI"})
	Local oStSZAz := FWFormStruct(2, "SZA", {|cCampo| AllTrim(cCampo) $ "ZA_STCODU1|ZA_STNOMU1|ZA_STDATA1|ZA_STCODU2|ZA_STNOMU2|ZA_STDATA2|ZA_STCODU3|ZA_STNOMU3|ZA_STDATA3|ZA_STCODU4|ZA_STNOMU4|ZA_STDATA4"})

	//Criando o objeto oView
	Local oView As Object

	//Retira as abas padrões
	oStSZAv:SetNoFolder()
	oStSZAx:SetNoFolder()
	oStSZAz:SetNoFolder()

	//Criando a view que será o retorno da função e setando o modelo da rotina
	oView := FWFormView():New()
	oView:SetModel(oModel)

	//Atribuindo formulários para interface
	oView:AddField("VIEW_SZAv", oStSZAv, "SZAMASTER")
	oView:AddField("VIEW_SZAx", oStSZAx, "SZAMASTER")
	oView:AddField("VIEW_SZAz", oStSZAz, "SZAMASTER")

	oView:SetViewProperty("VIEW_SZAz", "SETLAYOUT", { FF_LAYOUT_VERT_DESCR_TOP, 3} )
	oView:SetViewProperty("VIEW_SZAz", "SETCOLUMNSEPARATOR", { 5 } )
	oView:SetViewProperty("VIEW_SZAz", "SETCOLUMNSEPARATOR", { 5 } )
	cDscVND1
	cDscEng1
	//Mudando os nomes de exibição dos campos Engenharia de Produtos
	oStSZAv:SetProperty("ZA_EPRD01A",MVC_VIEW_TITULO,cDscEng1)
	oStSZAv:SetProperty("ZA_EPRD01D",MVC_VIEW_TITULO,"")
	oStSZAv:SetProperty("ZA_EPRD02A",MVC_VIEW_TITULO,cDscEng2)
	oStSZAv:SetProperty("ZA_EPRD02D",MVC_VIEW_TITULO,"")
	oStSZAv:SetProperty("ZA_EPRD03A",MVC_VIEW_TITULO,cDscEng3)
	oStSZAv:SetProperty("ZA_EPRD03D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_EPRD04A",MVC_VIEW_TITULO,"Existem componentes empregados no produto que são fornecidos pelo cliente?                        ")
	//oStSZAv:SetProperty("ZA_EPRD04D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_EPRD05A",MVC_VIEW_TITULO,"Existe a necessidade de desenvolvimento de novos fornecedores?                                    ")
	//oStSZAv:SetProperty("ZA_EPRD05D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_EPRD06A",MVC_VIEW_TITULO,"As características e tolerâncias dimensionais foram atendidas/respeitadas?                        ")
	//oStSZAv:SetProperty("ZA_EPRD06D",MVC_VIEW_TITULO,"")

	//Mudando os nomes de exibição dos campos Engenharia de Processos
	//oStSZAv:SetProperty("ZA_EPRC01A",MVC_VIEW_TITULO,"A Empresa possui as máquinas, ferramentas e dispositivos necessários para produção do item?       ")
	//oStSZAv:SetProperty("ZA_EPRC01D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_EPRC02A",MVC_VIEW_TITULO,"Requer algum serviço terceirizado?                                                                ")
	//oStSZAv:SetProperty("ZA_EPRC02D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_EPRC03A",MVC_VIEW_TITULO,"Necessita de algum investimento adicional?                                                        ")
	//oStSZAv:SetProperty("ZA_EPRC03D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_EPRC04A",MVC_VIEW_TITULO,"Tempo Hs/Mil                                                                                      ")
	//oStSZAv:SetProperty("ZA_EPRC04D",MVC_VIEW_TITULO,"")
//
	////Mudando os nomes de exibição dos campos PCP
	//oStSZAv:SetProperty("ZA_PCP01A",MVC_VIEW_TITULO,"A data de entrega está de acordo com Disponibilidade da Matéria prima e capacidade da Fábrica?     ")
	//oStSZAv:SetProperty("ZA_PCP01D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_PCP02A",MVC_VIEW_TITULO,"Existe ordens de produção em processo para o item?                                                 ")
	//oStSZAv:SetProperty("ZA_PCP02D",MVC_VIEW_TITULO,"")
//
	////Mudando os nomes de exibição dos campos Qualidade
	//oStSZAv:SetProperty("ZA_QLID01A",MVC_VIEW_TITULO,"O material precisa de alguma certificação? (UL, Rohs, CSA etc.)                                   ")
	//oStSZAv:SetProperty("ZA_QLID01D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_QLID02A",MVC_VIEW_TITULO,"A empresa possui equipamentos de medição para controlar as especificações do item?                ")
	//oStSZAv:SetProperty("ZA_QLID02D",MVC_VIEW_TITULO,"")
	//oStSZAv:SetProperty("ZA_QLID03A",MVC_VIEW_TITULO,"O produto requer verificações ou testes funcionais? (Passagem, tensão, tração etc.)               ")
	//oStSZAv:SetProperty("ZA_QLID03D",MVC_VIEW_TITULO,"")


	//Mudando os nomes de exibição dos campos Engenharia de Processos
	oStSZAv:SetProperty("ZA_EPRC01A",MVC_VIEW_TITULO,"A Empresa possui as máquinas, ferramentas e dispositivos necessários para produção do item?       ")
	oStSZAv:SetProperty("ZA_EPRC01D",MVC_VIEW_TITULO,"")
	oStSZAv:SetProperty("ZA_EPRC02A",MVC_VIEW_TITULO,"Requer algum serviço terceirizado?                                                                ")
	oStSZAv:SetProperty("ZA_EPRC02D",MVC_VIEW_TITULO,"")
	oStSZAv:SetProperty("ZA_EPRC03A",MVC_VIEW_TITULO,"Necessita de algum investimento adicional?                                                        ")
	oStSZAv:SetProperty("ZA_EPRC03D",MVC_VIEW_TITULO,"")
	oStSZAv:SetProperty("ZA_EPRC04A",MVC_VIEW_TITULO,"Tempo Hs/Mil                                                                                      ")
	oStSZAv:SetProperty("ZA_EPRC04D",MVC_VIEW_TITULO,"")


	//Mudando os nomes de exibição dos campos Cadastro
	oStSZAx:SetProperty("ZA_NROPOR",MVC_VIEW_TITULO,"OV")
	oStSZAx:SetProperty("ZA_CODCLI",MVC_VIEW_TITULO,"Cliente")
	oStSZAx:SetProperty("ZA_LOJACLI",MVC_VIEW_TITULO,"Loja")
	oStSZAx:SetProperty("ZA_EMAIL",MVC_VIEW_TITULO,"Email")
	oStSZAx:SetProperty("ZA_NOMCONT",MVC_VIEW_TITULO,"Contato")
	oStSZAx:SetProperty("ZA_FONE",MVC_VIEW_TITULO,"Telefone")
	oStSZAx:SetProperty("ZA_RAZSOCI",MVC_VIEW_TITULO,"Razão Social")
	oStSZAx:SetProperty("ZA_CODPRD",MVC_VIEW_TITULO,"Codigo Produto")
	oStSZAx:SetProperty("ZA_DSCPRD",MVC_VIEW_TITULO,"Desc Produto")
	oStSZAx:SetProperty("ZA_ITECLI",MVC_VIEW_TITULO,"Item Cliente")
	oStSZAx:SetProperty("ZA_DESENH",MVC_VIEW_TITULO,"Desenho")
	oStSZAx:SetProperty("ZA_AMOSTR",MVC_VIEW_TITULO,"Amostra ?")
	oStSZAx:SetProperty("ZA_QTDAMS",MVC_VIEW_TITULO,"Qtd Amostra")
	//oStSZAx:SetProperty("ZA_DESCMOT",MVC_VIEW_TITULO,"Descrição do Motivo")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAz:SetProperty("ZA_STCODU1",MVC_VIEW_TITULO,"Resp. Eng.Produtos")
	oStSZAz:SetProperty("ZA_STCODU2",MVC_VIEW_TITULO,"Resp. Eng.Processos")
	oStSZAz:SetProperty("ZA_STCODU3",MVC_VIEW_TITULO,"Resp. PCP")
	oStSZAz:SetProperty("ZA_STCODU4",MVC_VIEW_TITULO,"Resp. Qualidade")


	////Mudando os nomes de exibição dos campos Engenharia de Produtos
	//oStSZAv:SetProperty("ZA_EPRD01A",MVC_VIEW_DESCR ,"O Cliente enviou todas especificações necessárias para o desenvolvimento e/ou modificação do item?")
	//oStSZAv:SetProperty("ZA_EPRD01D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_EPRD02A",MVC_VIEW_DESCR ,"A matéria prima empregada está de acordo com o especificado?                                      ")
	//oStSZAv:SetProperty("ZA_EPRD02D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_EPRD03A",MVC_VIEW_DESCR ,"O material precisa de alguma certificação? (UL, Rohs, CSA etc.)                                   ")
	//oStSZAv:SetProperty("ZA_EPRD03D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_EPRD04A",MVC_VIEW_DESCR ,"Existem componentes empregados no produto que são fornecidos pelo cliente?                        ")
	//oStSZAv:SetProperty("ZA_EPRD04D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_EPRD05A",MVC_VIEW_DESCR ,"Existe a necessidade de desenvolvimento de novos fornecedores?                                    ")
	//oStSZAv:SetProperty("ZA_EPRD05D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_EPRD06A",MVC_VIEW_DESCR ,"As características e tolerâncias dimensionais foram atendidas/respeitadas?                        ")
	//oStSZAv:SetProperty("ZA_EPRD06D",MVC_VIEW_DESCR ,"")

	//Mudando os nomes de exibição dos campos Engenharia de Processos
	oStSZAv:SetProperty("ZA_VND01A",MVC_VIEW_DESCR ,cDscVND1)
	oStSZAv:SetProperty("ZA_VND01D",MVC_VIEW_DESCR ,"")
	oStSZAv:SetProperty("ZA_VND02A",MVC_VIEW_DESCR ,cDscVND2)
	oStSZAv:SetProperty("ZA_VND02D",MVC_VIEW_DESCR ,"")
	oStSZAv:SetProperty("ZA_VND03A",MVC_VIEW_DESCR ,cDscVND3)
	oStSZAv:SetProperty("ZA_VND03D",MVC_VIEW_DESCR ,"")
	oStSZAv:SetProperty("ZA_VND04A",MVC_VIEW_DESCR ,cDscVND4)
	oStSZAv:SetProperty("ZA_VND04D",MVC_VIEW_DESCR ,"")

	//Mudando os nomes de exibição dos campos PCP
	//oStSZAv:SetProperty("ZA_PCP01A",MVC_VIEW_DESCR ,"A data de entrega está de acordo com Disponibilidade da Matéria prima e capacidade da Fábrica?     ")
	//oStSZAv:SetProperty("ZA_PCP01D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_PCP02A",MVC_VIEW_DESCR ,"Existe ordens de produção em processo para o item?                                                 ")
	//oStSZAv:SetProperty("ZA_PCP02D",MVC_VIEW_DESCR ,"")
//
	////Mudando os nomes de exibição dos campos Qualidade
	//oStSZAv:SetProperty("ZA_QLID01A",MVC_VIEW_DESCR ,"O material precisa de alguma certificação? (UL, Rohs, CSA etc.)                                   ")
	//oStSZAv:SetProperty("ZA_QLID01D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_QLID02A",MVC_VIEW_DESCR ,"A empresa possui equipamentos de medição para controlar as especificações do item?                ")
	//oStSZAv:SetProperty("ZA_QLID02D",MVC_VIEW_DESCR ,"")
	//oStSZAv:SetProperty("ZA_QLID03A",MVC_VIEW_DESCR ,"O produto requer verificações ou testes funcionais? (Passagem, tensão, tração etc.)               ")
	//oStSZAv:SetProperty("ZA_QLID03D",MVC_VIEW_DESCR ,"")

	//Mudando os nomes de exibição dos campos Cadastro
	oStSZAx:SetProperty("ZA_NROPOR",MVC_VIEW_DESCR ,"OV")
	oStSZAx:SetProperty("ZA_CODCLI",MVC_VIEW_DESCR ,"Cliente")
	oStSZAx:SetProperty("ZA_LOJACLI",MVC_VIEW_DESCR ,"Loja")
	oStSZAx:SetProperty("ZA_EMAIL",MVC_VIEW_DESCR ,"Email")
	oStSZAx:SetProperty("ZA_NOMCONT",MVC_VIEW_DESCR ,"Contato")
	oStSZAx:SetProperty("ZA_FONE",MVC_VIEW_DESCR ,"Telefone")
	oStSZAx:SetProperty("ZA_RAZSOCI",MVC_VIEW_DESCR ,"Razão Social")
	oStSZAx:SetProperty("ZA_CODPRD",MVC_VIEW_DESCR,"Codigo Produto")
	oStSZAx:SetProperty("ZA_DSCPRD",MVC_VIEW_DESCR,"Desc Produto")
	oStSZAx:SetProperty("ZA_ITECLI",MVC_VIEW_DESCR,"Item Cliente")
	oStSZAx:SetProperty("ZA_DESENH",MVC_VIEW_DESCR,"Desenho")
	oStSZAx:SetProperty("ZA_AMOSTR",MVC_VIEW_DESCR,"Amostra ?")
	oStSZAx:SetProperty("ZA_QTDAMS",MVC_VIEW_DESCR,"Qtd Amostra")

	//	oStSZAx:SetProperty("ZA_DESCMOT",MVC_VIEW_DESCR ,"Descrição do Motivo")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAz:SetProperty("ZA_STCODU1",MVC_VIEW_DESCR ,"Resp. Eng.Produtos")
	//oStSZAz:SetProperty("ZA_STCODU2",MVC_VIEW_DESCR ,"Resp. Eng.Processos")
	//oStSZAz:SetProperty("ZA_STCODU3",MVC_VIEW_DESCR ,"Resp. PCP")
	//oStSZAz:SetProperty("ZA_STCODU4",MVC_VIEW_DESCR ,"Resp. Qualidade")
	oStSZAz:SetProperty("ZA_STCODU5",MVC_VIEW_DESCR ,"Resp. Vendas")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAz:SetProperty("ZA_STNOMU1",MVC_VIEW_DESCR ,"Nm Resp. Eng.Produtos")
	//oStSZAz:SetProperty("ZA_STNOMU2",MVC_VIEW_DESCR ,"Nm Resp. Eng.Processos")
	//oStSZAz:SetProperty("ZA_STNOMU3",MVC_VIEW_DESCR ,"Nm Resp. PCP")
	//oStSZAz:SetProperty("ZA_STNOMU4",MVC_VIEW_DESCR ,"Nm Resp. Qualidade")
	oStSZAz:SetProperty("ZA_STNOMU5",MVC_VIEW_DESCR ,"Nm Resp. Vendas")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAz:SetProperty("ZA_STDATA1",MVC_VIEW_DESCR ,"Dt Ass Eng.Produtos")
	//oStSZAz:SetProperty("ZA_STDATA2",MVC_VIEW_DESCR ,"Dt Ass Eng.Processos")
	//oStSZAz:SetProperty("ZA_STDATA3",MVC_VIEW_DESCR ,"Dt Ass PCP")
	//oStSZAz:SetProperty("ZA_STDATA4",MVC_VIEW_DESCR ,"Dt Ass Qualidade")
	oStSZAz:SetProperty("ZA_STDATA4",MVC_VIEW_DESCR ,"Dt Ass Vendas")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAz:SetProperty("ZA_STCODU1",MVC_VIEW_TITULO ,"Resp. Eng.Produtos")
	//oStSZAz:SetProperty("ZA_STCODU2",MVC_VIEW_TITULO ,"Resp. Eng.Processos")
	//oStSZAz:SetProperty("ZA_STCODU3",MVC_VIEW_TITULO ,"Resp. PCP")
//	oStSZAz:SetProperty("ZA_STCODU4",MVC_VIEW_TITULO ,"Resp. Qualidade")
	oStSZAz:SetProperty("ZA_STCODU5",MVC_VIEW_TITULO ,"Resp. Vendas")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAz:SetProperty("ZA_STNOMU1",MVC_VIEW_TITULO ,"Nm Resp. Eng.Produtos")
	//oStSZAz:SetProperty("ZA_STNOMU2",MVC_VIEW_TITULO ,"Nm Resp. Eng.Processos")
	//oStSZAz:SetProperty("ZA_STNOMU3",MVC_VIEW_TITULO ,"Nm Resp. PCP")
	//oStSZAz:SetProperty("ZA_STNOMU4",MVC_VIEW_TITULO ,"Nm Resp. Qualidade")
	oStSZAz:SetProperty("ZA_STNOMU5",MVC_VIEW_TITULO ,"Nm Resp. Vendas")

	//Mudando os nomes de exibição dos campos Responsavel na aba status
	oStSZAz:SetProperty("ZA_STDATA1",MVC_VIEW_TITULO ,"Dt Ass Eng.Produtos")
//oStSZAz:SetProperty("ZA_STDATA2",MVC_VIEW_TITULO ,"Dt Ass Eng.Processos")
//oStSZAz:SetProperty("ZA_STDATA3",MVC_VIEW_TITULO ,"Dt Ass PCP")
	// oStSZAz:SetProperty("ZA_STDATA4",MVC_VIEW_TITULO ,"Dt Ass Qualidade")
	oStSZAz:SetProperty("ZA_STDATA5",MVC_VIEW_TITULO ,"Dt Ass Vendas")



	//Agrupando os campos
	oStSZAv:AddGroup( 'GRUPO01', 'Engenharia de Produtos'   , '', 2 )
	//oStSZAv:AddGroup( 'GRUPO02', 'Engenharia de Processos'  , '', 2 )
	//oStSZAv:AddGroup( 'GRUPO03', 'PCP'                      , '', 2 )
	// oStSZAv:AddGroup( 'GRUPO04', 'Qualidade'                , '', 2 )
	oStSZAv:AddGroup( 'GRUPO05', 'Vendas'                , '', 2 )

	oStSZAx:AddGroup( 'GRUPO06', 'Cadastro'                 , '', 2 )

	oStSZAv:SetProperty( 'ZA_EPRD01A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	oStSZAv:SetProperty( 'ZA_EPRD01D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	oStSZAv:SetProperty( 'ZA_EPRD02A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	oStSZAv:SetProperty( 'ZA_EPRD02D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	oStSZAv:SetProperty( 'ZA_EPRD03A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	oStSZAv:SetProperty( 'ZA_EPRD03D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	//oStSZAv:SetProperty( 'ZA_EPRD04A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	//oStSZAv:SetProperty( 'ZA_EPRD04D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	//oStSZAv:SetProperty( 'ZA_EPRD05A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	//oStSZAv:SetProperty( 'ZA_EPRD05D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	//oStSZAv:SetProperty( 'ZA_EPRD06A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	//oStSZAv:SetProperty( 'ZA_EPRD06D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO01' )
	oStSZAv:SetProperty( 'ZA_VND01A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )
	oStSZAv:SetProperty( 'ZA_VND01D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )
	oStSZAv:SetProperty( 'ZA_VND02A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )
	oStSZAv:SetProperty( 'ZA_VND02D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )
	oStSZAv:SetProperty( 'ZA_VND03A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )
	oStSZAv:SetProperty( 'ZA_VND03D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )
	oStSZAv:SetProperty( 'ZA_VND04A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )
	oStSZAv:SetProperty( 'ZA_VND04D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )


	// oStSZAv:SetProperty( 'ZA_EPRC01A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )
	// oStSZAv:SetProperty( 'ZA_EPRC01D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )
	// oStSZAv:SetProperty( 'ZA_EPRC02A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )
	// oStSZAv:SetProperty( 'ZA_EPRC02D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )
	// oStSZAv:SetProperty( 'ZA_EPRC03A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )
	// oStSZAv:SetProperty( 'ZA_EPRC03D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )
	// oStSZAv:SetProperty( 'ZA_EPRC04A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )
	// oStSZAv:SetProperty( 'ZA_EPRC04D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO02' )

	// oStSZAv:SetProperty( 'ZA_PCP01A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO03' )
	// oStSZAv:SetProperty( 'ZA_PCP01D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO03' )
	// oStSZAv:SetProperty( 'ZA_PCP02A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO03' )
	// oStSZAv:SetProperty( 'ZA_PCP02D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO03' )

	// oStSZAv:SetProperty( 'ZA_QLID01A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO04' )
	// oStSZAv:SetProperty( 'ZA_QLID01D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO04' )
	// oStSZAv:SetProperty( 'ZA_QLID02A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO04' )
	// oStSZAv:SetProperty( 'ZA_QLID02D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO04' )
	// oStSZAv:SetProperty( 'ZA_QLID03A' , MVC_VIEW_GROUP_NUMBER, 'GRUPO04' )
	// oStSZAv:SetProperty( 'ZA_QLID03D' , MVC_VIEW_GROUP_NUMBER, 'GRUPO04' )

	oStSZAx:SetProperty( 'ZA_NROPOR'  , MVC_VIEW_GROUP_NUMBER, 'GRUPO06' )
	oStSZAx:SetProperty( 'ZA_CODCLI'  , MVC_VIEW_GROUP_NUMBER, 'GRUPO06' )
	oStSZAx:SetProperty( 'ZA_LOJACLI' , MVC_VIEW_GROUP_NUMBER, 'GRUPO06' )
	oStSZAx:SetProperty( 'ZA_EMAIL'   , MVC_VIEW_GROUP_NUMBER, 'GRUPO06' )
	oStSZAx:SetProperty( 'ZA_NOMCONT' , MVC_VIEW_GROUP_NUMBER, 'GRUPO06' )
	oStSZAx:SetProperty( 'ZA_FONE'    , MVC_VIEW_GROUP_NUMBER, 'GRUPO06' )
	oStSZAx:SetProperty( 'ZA_RAZSOCI' , MVC_VIEW_GROUP_NUMBER, 'GRUPO06' )
	oStSZAx:SetProperty("ZA_CODPRD",MVC_VIEW_GROUP_NUMBER,"GRUPO06")
	oStSZAx:SetProperty("ZA_DSCPRD",MVC_VIEW_GROUP_NUMBER,"GRUPO06")
	oStSZAx:SetProperty("ZA_ITECLI",MVC_VIEW_GROUP_NUMBER,"GRUPO06")
	oStSZAx:SetProperty("ZA_DESENH",MVC_VIEW_GROUP_NUMBER,"GRUPO06")
	oStSZAx:SetProperty("ZA_AMOSTR",MVC_VIEW_GROUP_NUMBER,"GRUPO06")
	oStSZAx:SetProperty("ZA_QTDAMS",MVC_VIEW_GROUP_NUMBER,"GRUPO06")
	//oStSZAx:SetProperty( 'ZA_DESCMOT' , MVC_VIEW_GROUP_NUMBER, 'GRUPO05' )

	// Controle das abas
	oView:CreateFolder( 'FOLDER1' )

	oView:AddSheet( 'FOLDER1', 'ABA01', 'LMP' )
	oView:AddSheet( 'FOLDER1', 'ABA02', 'Analise' )
	oView:AddSheet( 'FOLDER1', 'ABA03', 'Status' )

	// Controle dos box vinculados as abas
	oView:CreateHorizontalBox( 'LMP', 		100, ,, 'FOLDER1', 'ABA01' )
	oView:CreateHorizontalBox( 'ANALISE', 	100, ,, 'FOLDER1', 'ABA02' )
	oView:CreateHorizontalBox( 'STATUS', 	100, ,, 'FOLDER1', 'ABA03' )

	// Amarração das Abas aos Views de Struct criados
	oView:SetOwnerView( 'VIEW_SZAx', 'LMP' )
	oView:SetOwnerView( 'VIEW_SZAv', 'ANALISE' )
	oView:SetOwnerView( 'VIEW_SZAz', 'STATUS' )

	//Forçar o fechamento da janela na confirmação
	oView:SetCloseOnOk({||.T.})

Return oView

/**/
Static Function fVldEngPrd()

	Local lRet := .F.
	Local cCodUsr := RetCodUsr()

	dbSelectArea("SZB")
	SZB->(dbSetOrder(1))
	If FWIsAdmin() .OR. SZB->(MsSeek( xFilial("SZB")+cCodUsr+"3" ))
		lRet := .T.
	EndIf

Return lRet

/**/
Static Function fVldEngPrc()

	Local lRet := .F.
	Local cCodUsr := RetCodUsr()

	dbSelectArea("SZB")
	SZB->(dbSetOrder(1))
	If FWIsAdmin() .OR. SZB->(MsSeek( xFilial("SZB")+cCodUsr+"1" ))
		lRet := .T.
	EndIf

Return lRet

/**/
Static Function fVldPcp()

	Local lRet := .F.
	Local cCodUsr := RetCodUsr()

	dbSelectArea("SZB")
	SZB->(dbSetOrder(1))
	If FWIsAdmin() .OR. SZB->(MsSeek( xFilial("SZB")+cCodUsr+"2" ))
		lRet := .T.
	EndIf

Return lRet

/**/
Static Function fVldQuali()

	Local lRet := .F.
	Local cCodUsr := RetCodUsr()

	dbSelectArea("SZB")
	SZB->(dbSetOrder(1))
	If FWIsAdmin() .OR. SZB->(MsSeek( xFilial("SZB")+cCodUsr+"4" ))
		lRet := .T.
	EndIf

Return lRet

/**/
Static Function fSetAba1(oModel)

	Local lRet 		:= .F.
	Local cCodCli   := ""  // AD1->AD1_CODCLI
	Local cCodLoja  := ""  // AD1->AD1_LOJCLI
	Local cRazSoc   := ""  // SA1-> A1_NOME
	Local cContato  := ""  // SA1-> A1_CONTATO
	Local cTelefone := ""  // SA1-> A1_TEL
	Local cEmail 	:= ""  // SA1-> A1_EMAIL
	Local cNumOV    := oModel:GetValue("ZA_NROPOR") // AD1->AD1_NROPOR

	If (oModel:GetOperation() == 3) .OR. (oModel:GetOperation() == 4)
		If !Empty(cNumOV)
			dbSelectArea("AD1")
			AD1->(dbSetOrder(1)) //1-AD1_FILIAL, AD1_NROPOR, AD1_REVISA, R_E_C_N_O_, D_E_L_E_T_
			If !AD1->(dbSeek(xFilial("AD1")+cNumOV)) //!AD1->(dbSeek(xFilial("AD1")+cNumOV))
				MsgStop("Oportunidade não localizada pelo Número: " +cNumOV," Atenção ")
				lRet  := .F.
				Return lRet
			Else
				cCodCli  := AD1->AD1_CODCLI
				cCodLoja := AD1->AD1_LOJCLI

				lVldLmp := .T.
				oModel:SetValue("ZA_CODCLI"	, cCodCli)
				oModel:SetValue("ZA_LOJACLI", cCodLoja)
				lVldLmp := .F.
				lRet := .T.
			EndIf
		EndIf

		if !Empty(cCodCli)
			dbSelectArea("SA1")
			SA1->(dbSetOrder(1))
			If !SA1->(dbSeek(xFilial("SA1")+cCodCli+cCodLoja)) //SA1->(dbSeek(xFilial("SA1")+AD1->AD1_CODCLI+AD1->AD1_LOJCLI))
				MsgStop("Cliente não localizado pelo Código: " +cCodCli," Atenção ")
				lRet  := .F.
				Return lRet
			Else
				cRazSoc   :=  SA1-> A1_NOME
				cContato  :=  SA1-> A1_CONTATO
				cTelefone :=  SA1-> A1_TEL
				cEmail 	  :=  SA1-> A1_EMAIL

				lVldLmp := .T.
				oModel:SetValue("ZA_EMAIL"	, cEmail)
				oModel:SetValue("ZA_NOMCONT", cContato)
				oModel:SetValue("ZA_FONE"	, cTelefone)
				oModel:SetValue("ZA_RAZSOCI", cRazSoc)
				lVldLmp := .F.

				lRet := .T.
			EndIf
		EndIf

		If Empty(cCodCli) .AND. Empty(cCodLoja)

			lVldLmp := .T.
			oModel:SetValue("ZA_EMAIL"	, "")
			oModel:SetValue("ZA_NOMCONT", "")
			oModel:SetValue("ZA_FONE"	, "")
			oModel:SetValue("ZA_RAZSOCI", "")
			lVldLmp := .F.
			lRet := .T.

		EndIf
	EndIf

Return lRet

