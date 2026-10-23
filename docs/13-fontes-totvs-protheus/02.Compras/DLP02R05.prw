#INCLUDE 'TOTVS.CH'
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE "RWMAKE.CH"

Static aItens := {}

/*/{Protheus.doc} nomeFunction
Rotina - Selecao/Impressao Rel. Grupo x Produto
@type user function
@author Pedro Lindenberg
@since 02/07/2024
/*/
User Function DLP02R05()

	Local lRet := .T.

	private aEnableButtons := {{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.T.,"Salvar"},{.T.,"Fechar"},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil}} //###"Fechar"

	FWExecView("Relatório Produto x Custo","VIEWDEF.DLP02R05", 3, /*oDlg*/, {|| .T. } ,/*bOk*/{|| fImpRel() }, /*nPercReducao50*/, aEnableButtons , /*bCancel*/ {|| lRet := .F.,fCanOpe() }, /*cNumBoreratId*/, /*cToolBar*/, /*oModel*/ )

Return lRet

Static Function ModelDef()

	Local oModel 	:= Nil
	Local oStrCab   := GETSTCAB(1)
	Local oStrBody2 := GETSTB2(1)

	oModel := MPFormModel():New('MVCDLP02R05')

	oModel:AddFields('MASTER',/*cOwner*/,oStrCab)
	oModel:AddGrid('BODY2','MASTER',oStrBody2)
	oModel:SetPrimaryKey({})

	oModel:SetDescription('Delpi')
	oModel:GetModel('MASTER'):SetDescription('Cabeçalho')
	oModel:GetModel('BODY2'):SetDescription('Corpo2')

	oModel:GetModel('MASTER'):SetOnlyQuery(.T.)

Return oModel

Static Function ViewDef()
	Local oView			:= Nil
	Local oModel    := ModelDef()
	Local oStCab    := GETSTCAB(2)
	Local oStrBody2 := GETSTB2(2)

	oStrBody2:RemoveField("xSTATUS2")

	oView := FWFormView():New()
	oView:SetModel(oModel)

	oView:AddField('VIEW_MASTER',oStCab,'MASTER')
	oView:AddGrid('VIEW_BODY2',oStrBody2,'BODY2')

	//Setando o dimensionamento de tamanho
	oView:CreateVerticalBox('TELA',100)
	oView:CreateHorizontalBox('CABEC',16,'TELA')
	oView:CreateHorizontalBox('BODY2',84,'TELA')
	oView:CreateVerticalBox('LFTSCRN',60,'CABEC')
	oView:CreateVerticalBox('RGTSCRN',40,'CABEC')

	oView:SetViewProperty("BODY2", "ENABLENEWGRID")

	oStCab:SetProperty('CODPROD'       	  ,MVC_VIEW_CANCHANGE,.T.)
	oStCab:SetProperty('USUARIO'       	  ,MVC_VIEW_CANCHANGE,.F.)

	oView:SetViewProperty("VIEW_BODY2", "GRIDDOUBLECLICK", {{ |oFormulario,cFieldName,nLineGrid,nLineModel| fSeaDouble(oFormulario,cFieldName,nLineGrid,nLineModel)}})

	oStCab:RemoveField('USUARIO')

	oStrBody2:SetProperty('*',MVC_VIEW_CANCHANGE,.F.)

	oView:AddOtherObject("VIEW_BTN", {|oPanel| CreateBtn(oPanel)})

	oView:SetOwnerView('VIEW_BTN','LFTSCRN')

	//Amarrando a view com as box
	oView:SetOwnerView('VIEW_MASTER','LFTSCRN')
	oView:SetOwnerView('VIEW_BODY2','BODY2')

	oView:SetCloseOnOk({||.T.})

Return oView

/*/{Protheus.doc}
	Funcao responsável por montar o Cabeçalho
	@type  Static Function
	@author Pedro Lindenberg
/*/
Static function GETSTCAB(nTipo)
	Local oStruct   := NIL
	Local bValid    := NIl
	Local nI        := 0
	Local bInic     := NIL
	Local bWhen     := NIL
	Local aLista    := NIL
	Local cLista    := ""
	Local cTipCampo := ""
	Local aCampos   := {{'Cod.Produto'        		, 'Cod.Produto'        		    , 'CODPROD'	    , 'C'	, 15 	,0	,'@!'	,''	},;
		{'Usuario'        		, 'Usuario'        		    , 'USUARIO'	    , 'C'	, 20 	,0	,'@!'	,''	    }}

	If nTipo == 1	// Model
		oStruct := FWFormModelStruct():New()
		oStruct:AddTable('',,'TMP',{||''})

		For nI := 1 to len(aCampos)
			bValid := ""
			bInic  := ""
			bWhen	:= Nil
			aLista := NIL

			bValid := FwBuildFeature(1,bValid)

			If !Empty(bWhen)
				bWhen	:= FwBuildFeature(2,bWhen)
			EndIf

			bInic  := FwBuildFeature(3,bInic)

			oStruct:AddField(          ;
				aCampos[nI,1]		     , ;              // [01] Titulo do campo
				aCampos[nI,2]		     , ;              // [02] ToolTip do campo
				aCampos[nI,3]            , ;              // [03] Id do Field
				aCampos[nI,4]            , ;              // [04] Tipo do campo
				aCampos[nI,5]	         , ;              // [05] Tamanho do campo
				aCampos[nI,6]            , ;              // [06] Decimal do campo
				bValid                   , ;              // [07] Code-block de validação do campo
				bWhen		             , ;              // [08] Code-block de validação When do campo
				aLista                   , ;              // [09] Lista de valores permitido do campo
				NIL						 , ;              // [10] Indica se o campo tem preenchimento obrigatório
				bInic              		 , ;              // [11] Code-block de inicializacao do campo
				NIL                      , ;              // [12] Indica se trata-se de um campo chave
				.F.                      , ;              // [13] Indica se o campo pode receber valor em uma operação de update.
				.T.  )                                    // [14] Indica se o campo é virtual

		NEXT nI
	ELSE //view
		oStruct := FWFormViewStruct():New()

		For nI := 1 to len(aCampos)

			IF(aCampos[nI,3]$cLista)
				cTipCampo := 'COMBO'
			else
				cTipCampo :='GET'
			ENDIF

			aLista := NIL

			oStruct:AddField( 			   ;
				aCampos[nI,3]  				 , ;                // [01] Campo
				STRZERO(nI,2)    			 , ;                // [02] Ordem
				aCampos[nI,1]				 , ;                // [03] Titulo
				aCampos[nI,2]			     , ;                // [04] Descricao
				NIL                          , ;                // [05] Help
				cTipCampo                    , ;      			// [06] Tipo do campo   COMBO, Get ou CHECK
				aCampos[nI,7]                , ;                // [07] Picture
				NIL                          , ;                // [08] PictVar
				aCampos[nI,8]                , ;                // [09] F3
				.T.	                         , ;                // [10] Editavel
				NIL               			 , ;                // [11] Folder
				NIL               			 , ;                // [12] Group
				aLista                       , ;                // [13] Lista Combo
				NIL                    		 , ;                // [14] Tam Max Combo
				NIL                			 , ;                // [15] Inic. Browse
				.T.                		    	)               // [16] Virtual
		Next nI

	ENDIF

return oStruct

/*/{Protheus.doc} GETSTB2
	Funcao responsável por montar a Grid
	@type  Static Function
	@author Pedro Lindenberg
/*/
Static function GETSTB2(nTipo,oModel)
	Local oStruct := NIL
	Local bValid  := NIl
	Local nI      := 0
	Local bInic   := NIL
	Local bWhen   := NIL
	Local aLista  := NIL
	Local cLista  := ""
	Local lEdita  := .f.

	aCampos :={{''          	       ,''                   ,'SELREG'      ,'L' ,1   ,0 , ,''} ,;
		{ 'Filial' , 'Filial' , 'Z8_FILIAL' , 'C' , 2 ,0 , '@!' , ''},;
		{'Cod.Produto'                                               , 'Cod.Produto' , 'Z8_COD' , 'C', 15 , 0, '@!', ''},;
		{'Id.Produto'                                              , 'Id.Produto', 'Z8_ID', 'C', 6 , 0, '@!'  , ''},;
		{'Desc.Produto'                                                , 'Desc.Produto'  , 'Z8_DSCPRD', 'C', 100, 0, '@!', ''},;
		{'Tab.Venda'                                                      , 'Tab.Venda'        , 'Z8_PVTAB'   , 'N', 16 , 4, '@E 99,999,999,999.9999', ''},;
		{'Val.Sugerido'                                                 , 'Val.Sugerido'   , 'Z8_PVSUGER' , 'N', 16, 4, '@E 99,999,999,999.9999', '' },;
		{'STATUS2'      	   ,'STATUS2'            ,"xSTATUS2"    ,'C' ,1   ,0 , ,''}}

	If nTipo == 1	// Model
		oStruct := FWFormModelStruct():New()

		oStruct:AddTable('TMP_CAMPO',,'TMP_CAMPO')
		oStruct:AddIndex( 0, 'REG', '', '', '', '', .F. )

		For nI := 1 to len(aCampos)
			bValid := ""
			bInic  := ""
			bWhen  :=  Nil
			aLista := NIL

			bValid := FwBuildFeature(1,bValid)

			If !Empty(bWhen)
				bWhen	:= FwBuildFeature(2,bWhen)
			EndIf

			bInic  := FwBuildFeature(3,bInic)

			oStruct:AddField(;
				aCampos[nI,1]		     , ;          // [01] Titulo do campo
				aCampos[nI,2]		     , ;              // [02] ToolTip do campo
				aCampos[nI,3]            , ;              // [03] Id do Field
				aCampos[nI,4]            , ;              // [04] Tipo do campo
				aCampos[nI,5]	         , ;              // [05] Tamanho do campo
				aCampos[nI,6]            , ;              // [06] Decimal do campo
				bValid                   , ;              // [07] Code-block de validação do campo
				bWhen		             , ;              // [08] Code-block de validação When do campo
				aLista                   , ;              // [09] Lista de valores permitido do campo
				NIL						 , ;              // [10] Indica se o campo tem preenchimento obrigatório
				bInic              		 , ;              // [11] Code-block de inicializacao do campo
				NIL                      , ;              // [12] Indica se trata-se de um campo chave
				.F.                      , ;              // [13] Indica se o campo pode receber valor em uma operação de update.
				.T.  )                                    // [14] Indica se o campo é virtual

		NEXT nI
	ELSE

		oStruct := FWFormViewStruct():New()

		For nI := 1 to len(aCampos)

			aLista := NIL

			IF aCampos[nI,3] == "SELREG"
				oStruct:AddField( 			   ;
					aCampos[nI,3]  			      , ;               // [01] Campo
					STRZERO(nI,2)    			 , ;                // [02] Ordem
					aCampos[nI,1]				 , ;                // [03] Titulo
					aCampos[nI,2]			     , ;                // [04] Descricao
					NIL                          , ;                // [05] Help
					Iif(aCampos[nI,3]$cLista,'COMBO','GET'), ;      // [06] Tipo do campo   COMBO, Get ou CHECK
					aCampos[nI,7]                , ;                // [07] Picture
					NIL                          , ;                // [08] PictVar
					aCampos[nI,8]                , ;                // [09] F3
					.T.                       , ;                // [10] Editavel
					NIL               			 , ;                // [11] Folder
					NIL               			 , ;                // [12] Group
					aLista                       , ;                // [13] Lista Combo
					NIL                    		 , ;                // [14] Tam Max Combo
					NIL                			 , ;                // [15] Inic. Browse
					.T.                		    	)               // [16] Virtual

			else
				oStruct:AddField( 			   ;
					aCampos[nI,3]  			      , ;               // [01] Campo
					STRZERO(nI,2)    			 , ;                // [02] Ordem
					aCampos[nI,1]				 , ;                // [03] Titulo
					aCampos[nI,2]			     , ;                // [04] Descricao
					NIL                          , ;                // [05] Help
					Iif(aCampos[nI,3]$cLista,'COMBO','GET'), ;      // [06] Tipo do campo   COMBO, Get ou CHECK
					aCampos[nI,7]                , ;                // [07] Picture
					NIL                          , ;                // [08] PictVar
					aCampos[nI,8]                , ;                // [09] F3
					lEdita                       , ;                // [10] Editavel
					NIL               			 , ;                // [11] Folder
					NIL               			 , ;                // [12] Group
					aLista                       , ;                // [13] Lista Combo
					NIL                    		 , ;                // [14] Tam Max Combo
					NIL                			 , ;                // [15] Inic. Browse
					.T.                		    	)               // [16] Virtual
			ENDIF

		Next nI

	ENDIF

return oStruct

/*/{Protheus.doc} nomeStaticFunction
	Funcao responsável por preencher o Cabeçalho
	@type  Static Function
	@author Pedro Lindenberg
	@since 02/07/2024
/*/
User Function fFilsz8()
	Default oModel := FWModelActive()
	Local oModelFdls := oModel:GetModel("MASTER")
	Local cCodPrd := ""

	cCodPrd := oModelFdls:GetValue("CODPROD")
	oModelFdls:SetValue("USUARIO", cUserName)

	IF EMPTY(cCodPrd)
		FWAlertError("Campo de Código de Produto está vazio","Erro")
		Return .F.
	ELSE
		fFeedTbe(cCodPrd)
	ENDIF

Return

/*/{Protheus.doc} nomeStaticFunction
	Funcao responsável por preencher a Grid
	@type  Static Function
	@author Pedro Lindenberg
	@since 12/06/2024
/*/
Static Function fFeedTbe(cCodPrd)
	Local oModel := FWModelActive()
	Local oDadosBody := oModel:GetModel("BODY2")
	Local oView  := FWViewActive()
	Local aSz8 := SZ8->(GetArea())
	Local cAlias := GetNextAlias()

	BEGINSQL ALIAS cAlias
		SELECT
			SZ8.Z8_FILIAL,
			SZ8.Z8_COD,
			SZ8.Z8_ID,
			SZ8.Z8_DSCPRD,
			SZ8.Z8_PVTAB,
			SZ8.Z8_PVSUGER
		FROM
			%Table:SZ8% SZ8
		WHERE
			SZ8.%NotDel%
			AND SZ8.Z8_COD = %EXP:cCodPrd%
			AND SZ8.Z8_FILIAL = %EXP:XFILIAL("SZ8")%
	ENDSQL


	oDadosBody:SetMaxLine(9999999)
	oDadosBody:SetNoInsertLine(.F.)
	oDadosBody:SetNoDeleteLine(.F.)
	oDadosBody:ClearData()
	oDadosBody:InitLine()
	oDadosBody:GoLine(1)

	(cAlias)->(dbGoTop())

	While (cAlias)->(!Eof())

		if (cAlias)->(!Eof())
			oDadosBody:AddLine()
		ENDIF

		oDadosBody:SetValue("SELREG" 		, .F.					 				)
		oDadosBody:SetValue("Z8_FILIAL" , (cAlias)->Z8_FILIAL )
		oDadosBody:SetValue("Z8_COD" 		, (cAlias)->Z8_COD 		)
		oDadosBody:SetValue("Z8_ID" 		, (cAlias)->Z8_ID 		)
		oDadosBody:SetValue("Z8_DSCPRD" , (cAlias)->Z8_DSCPRD )
		oDadosBody:SetValue("Z8_PVTAB" 	, (cAlias)->Z8_PVTAB 	)
		oDadosBody:SetValue("Z8_PVSUGER", (cAlias)->Z8_PVSUGER 	)

		(cAlias)->(DbSkip())

	ENDDO

	oDadosBody:goline(1)
	(cAlias)->(DbCloseArea())

	oDadosBody:goline(1)
	oView:Refresh("BODY2")

	RestArea(aSz8)

Return

/*/{Protheus.doc} nomeStaticFunction
	Funcao para informar cancelamento da Gravação da Tabela Customizada
	@type  Static Function
	@author Pedro Lindenberg
	@since 19/06/2024
/*/
Static Function fCanOpe()
	Local oViewActive  := FWViewActive()

	oViewActive:oOwner:End()

Return


/*/{Protheus.doc} nomeStaticFunction
	Adiciona botao em tela.
	@type  Static Function
	@author Pedro Lindenberg
	@since 31/10/2023
	@version version
/*/
Static Function CreateBtn(oPanel)
	Default oModel := FWModelActive()
	Local cCSSBtn1 := " "
	Local cFont := "Arial"
	Local oFontBtn := TFont():New(cFont,,-12,,.F.)

	oBtnT:= TButton():New( 010,125, "Pesquisar",oPanel,{||u_fFilsz8()}, 56,15,,oFontBtn,.F.,.T.,.F.,,.F.,,,.F. )

	cCSSBtn1 := " TButton { "
	cCSSBtn1 += " font: bold; "
	cCSSBtn1 += " background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #3DAFCC, stop: 1 #0D9CBF); "
	cCSSBtn1 += " color: #FFFFFF; "
	cCSSBtn1 += " border-width: 1px; "
	cCSSBtn1 += " border-style: solid; "
	cCSSBtn1 += " border-radius: 3px; "
	cCSSBtn1 += " border-color: #369CB5; "
	cCSSBtn1 += " } "
	cCSSBtn1 += " TButton:focus { "
	cCSSBtn1 += " padding:0px; "
	cCSSBtn1 += " outline-width:1px; "
	cCSSBtn1 += " outline-style:solid; "
	cCSSBtn1 += " outline-color: #51DAFC; "
	cCSSBtn1 += " outline-radius:3px; "
	cCSSBtn1 += " border-color:#369CB5; "
	cCSSBtn1 += " } "
	cCSSBtn1 += " TButton:hover { "
	cCSSBtn1 += " color: #FFFFFF; "
	cCSSBtn1 += " background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #3DAFCC, stop: 1 #1188A6); "
	cCSSBtn1 += " border-width: 1px; "
	cCSSBtn1 += " border-style: solid; "
	cCSSBtn1 += " border-radius: 3px; "
	cCSSBtn1 += " border-color: #C69CB5; "
	cCSSBtn1 += " } "
	cCSSBtn1 += " TButton:pressed { "
	cCSSBtn1 += " color: #FFF; "
	cCSSBtn1 += " background-color : qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #1188A6, stop: 1 #3DAFCC); "
	cCSSBtn1 += " border-width: 1px; "
	cCSSBtn1 += " border-style: solid; "
	cCSSBtn1 += " border-radius: 3px; "
	cCSSBtn1 += " border-color: #369CB5; "
	cCSSBtn1 += " } "
	cCSSBtn1 += " TButton:disabled { "
	cCSSBtn1 += " color: #FFFFFF; "
	cCSSBtn1 += " background-color: #4CA0B5; "
	cCSSBtn1 += " } "

	oBtnT:setCSS(cCSSBtn1)
	oBtnT:Refresh()

Return

/*/{Protheus.doc} nomeStaticFunction
  Função para marcar a Checkbox
  @type  Static Function
  @author Pedro Lindenberg
  @since 02/07/2024
  @version version
/*/
Static Function fSeaDouble(oFormulario,cFieldName,nLineGrid,nLineModel)
	Local nLinAtu := nLineGrid
	Local oModel := FWModelActive()
	Local oFields := oModel:GetModel("BODY2")
	Local oView  := FWViewActive()

	IF OFIELDS:ADATAMODEL[nLinAtu][1][1][1] == .F.

		OFIELDS:ADATAMODEL[nLinAtu][1][1][1] := .T.
		AADD(aItens,OFIELDS:ADATAMODEL[nLinAtu][1][1][4])

	ELSE

		OFIELDS:ADATAMODEL[nLinAtu][1][1][1] := .F.
		aDel(aItens,nLinAtu)

	ENDIF

	oView:Refresh("BODY2")

Return .T.


/*/{Protheus.doc} nomeStaticFunction
	Envia os dados para imprimir o relatório DLP02R04
	@type  Static Function
	@author Pedro Lindenberg
	@since 10/07/2024
/*/
Static Function fImpRel()
	Local oModel := FWModelActive()
	Local oFields := oModel:GetModel("BODY2")
	Local x := 0
	Local aPrdItens := {}
	Local cCodProd := ""
	Local nOpc := 0

	for x := 1 to len(OFIELDS:ADATAMODEL)

		IF OFIELDS:ADATAMODEL[x][1][1][1] := .T.

			// AADD(aItens,OFIELDS:ADATAMODEL[x][1][1][4])
			cCodProd := OFIELDS:ADATAMODEL[x][1][1][3]

		ENDIF

	next
	if len(aItens)!=2
		FWAlertWarning("Gentileza selecionar Duas formações para serem comparadas."+chr(10)+"Relatorio não será gerado.", "Delpi - Formação de Preço")

	endif
	AADD(aPrdItens,aItens[len(aItens)])
	AADD(aPrdItens,aItens[len(aItens)-1])

	nOpc := U_ImpGtOpc()

	U_DLP02R04(cCodProd,aPrdItens,nOpc)

Return Nil

//--------------------------------------------------------------
/*/{Protheus.doc} MyFunction
Selecao de opcao para impressao do relatorio
@author Pedro Lindenberg - pedro.silveira@totvs.com.br
@since 10/07/2024
/*/
//--------------------------------------------------------------
User Function ImpGtOpc()
	Local oButton1
	Local oButton2
	Local oSay1
	Local nNewOpc := 0
	Static oDlg

	DEFINE MSDIALOG oDlg TITLE "Impressao Rel. Grupo x Produto" FROM 000, 000  TO 130, 420 COLORS 0, 16777215 PIXEL

	@ 038, 016 BUTTON oButton1 PROMPT "Grupo" SIZE 070, 016 OF oDlg ACTION nNewOpc := fSelOpc(1) PIXEL
	@ 038, 119 BUTTON oButton2 PROMPT "Produto" SIZE 070, 016 OF oDlg ACTION nNewOpc := fSelOpc(2) PIXEL
	@ 020, 015 SAY oSay1 PROMPT "Deseja realizar a impressão do relatório, por Grupo ou Produto?" SIZE 170, 008 OF oDlg COLORS 0, 16777215 PIXEL

	ACTIVATE MSDIALOG oDlg CENTERED

Return nNewOpc

/*/{Protheus.doc} nomeStaticFunction
	Valida a opcao de relatorio selecionada
	@type  Static Function
	@author Pedro Lindenberg
	@since 10/07/2024
/*/
Static Function fSelOpc(nOpc)
	Local nSelect := 0

	IF nOpc == 1

		nSelect := 1

	else

		nSelect := 2

	ENDIF

	oDlg:End()

Return nSelect
