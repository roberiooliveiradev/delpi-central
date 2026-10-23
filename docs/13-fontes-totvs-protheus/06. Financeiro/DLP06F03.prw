#INCLUDE 'TOTVS.CH'
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE "RWMAKE.CH"

STATIC cNumBord := ""

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 02/07/2024
/*/
User Function DLP06F03()

	Local lRet := .T.

	private aEnableButtons := {{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.T.,"Salvar"},{.T.,"Fechar"},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil},{.f.,Nil}} //###"Fechar"

	FWExecView("Pix a Fornecedor","VIEWDEF.DLP06F03", 3, /*oDlg*/, {|| .T. } ,/*bOk*/{|| .T. }, /*nPercReducao50*/, aEnableButtons , /*bCancel*/ {|| lRet := .F.,fCanOpe() }, /*cNumBoreratId*/, /*cToolBar*/, /*oModel*/ )

Return lRet

Static Function ModelDef()

	Local oModel 	:= Nil
	Local oStrCab   := GETSTCAB(1)
	Local oStrBody2 := GETSTB2(1)

	oModel := MPFormModel():New('MVCDLP06F03')

	oModel:AddFields('MASTER',/*cOwner*/,oStrCab)
	oModel:AddGrid('BODY2','MASTER',oStrBody2)
	oModel:SetPrimaryKey({})

	oModel:SetDescription('Liberar Borderô')
	oModel:GetModel('MASTER'):SetDescription('Cabeçalho')
	oModel:GetModel('BODY2'):SetDescription('Corpo2')

	// oStrCab:SetProperty( 'NUMBOR' , MODEL_FIELD_VALID, FwBuildFeature(STRUCT_FEATURE_VALID, 'U_cFilFlds(oModel)'))

	oModel:GetModel('MASTER'):SetOnlyQuery(.T.)
	oModel:GetModel('BODY2'):SetOnlyQuery(.T.)

	oModel:setActivate({ |oModel| U_cFilFlds(oModel)})

Return oModel

Static Function ViewDef()
	Local oView			:= Nil
	Local oModel    := ModelDef()
	Local oStCab    := GETSTCAB(2)
	Local oStrBody2 := GETSTB2(2)

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

	oView:SetViewProperty("VIEW_BODY2", "GRIDDOUBLECLICK", {{ |oFormulario,cFieldName,nLineGrid,nLineModel| fSeaDouble(oFormulario,cFieldName,nLineGrid,nLineModel)}})

	oStCab:SetProperty('NUMBOR'       	  ,MVC_VIEW_CANCHANGE,.T.)
	oStCab:SetProperty('USUARIO'       	  ,MVC_VIEW_CANCHANGE,.F.)

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
	Local aCampos   := {{'Num.Borderô'        		, 'Num.Borderô'        		    , 'NUMBOR'	    , 'C'	, 6 	,0	,'@!'	,''	},;
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

	aCampos :={{ 'Filial' , 'Filial' , 'EA_FILIAL' , 'C' , 2 ,0 , '@!' , ''},;
		{'Num.Borderô'                                               , 'Num.Borderô' , 'EA_NUMBOR' , 'C', 6 , 0, '@!', ''},;
		{'Data.Borderô'                                              , 'Data.Borderô', 'EA_DATABOR', 'D', 8 , 0, ''  , ''},;
		{'Fornecedor'                                                , 'Fornecedor'  , 'EA_FORNECE', 'C', 6 , 0, '@!', ''},;
		{'Loja'                                                      , 'Loja'        , 'EA_LOJA'   , 'C', 2 , 0, '@!', ''},;
		{'Num.Conta'                                                 , 'Num.Conta'   , 'EA_NUMCON' , 'C', 10, 0, '@!', '' }}

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
User Function cFilFlds(oModel)
	Default oModel := FWModelActive()
	Local oModelFdls := oModel:GetModel("MASTER")

	// oModelFdls:SetValue("NUMBOR" , cNumBor)
	oModelFdls:SetValue("USUARIO", cUserName)

	fFeedTbe()

Return

/*/{Protheus.doc} nomeStaticFunction
	Funcao responsável por preencher a Grid
	@type  Static Function
	@author Pedro Lindenberg
	@since 12/06/2024
/*/
Static Function fFeedTbe()
	Local oModel := FWModelActive()
	Local oDadosBody := oModel:GetModel("BODY2")
	Local aSea := SEA->(GetArea())
	Local cAlias := GetNextAlias()

	BEGINSQL ALIAS cAlias
		SELECT
			SEA.EA_FILIAL,
			SEA.EA_NUMBOR,
			SEA.EA_DATABOR,
			SEA.EA_FORNECE,
			SEA.EA_LOJA,
			SEA.EA_NUMCON
		FROM
			%Table:SEA% SEA
		WHERE
			SEA.%NotDel%
			AND SEA.EA_YBLQPIX = 'N'
	ENDSQL


	oDadosBody:SetMaxLine(9999999)
	oDadosBody:SetNoInsertLine(.F.)
	oDadosBody:SetNoDeleteLine(.F.)
	oDadosBody:ClearData()
	oDadosBody:InitLine()
	oDadosBody:GoLine(1)

	(cAlias)->(dbGoTop())

	while (cAlias)->(!Eof())

		oDadosBody:SetValue("EA_FILIAL"   , (cAlias)->EA_FILIAL         )
		oDadosBody:SetValue("EA_NUMBOR"   , (cAlias)->EA_NUMBOR         )
		oDadosBody:SetValue("EA_DATABOR"  , StoD((cAlias)->EA_DATABOR)  )
		oDadosBody:SetValue("EA_FORNECE"  , (cAlias)->EA_FORNECE        )
		oDadosBody:SetValue("EA_LOJA"     , (cAlias)->EA_LOJA           )
		oDadosBody:SetValue("EA_NUMCON"   , (cAlias)->EA_NUMCON         )

		(cAlias)->(DbSkip())

		if (cAlias)->(!Eof())
			oDadosBody:AddLine()
		ENDIF

	end

	oDadosBody:goline(1)
	oDadosBody:SetNoInsertLine( .F. )
	oDadosBody:SetNoDeleteLine( .F. )

	(cAlias)->(DbCloseArea())

	RestArea(aSea)

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

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author user
@since 03/07/2024
/*/
User Function fltrBorMvc(cNumbor)
	Local oModel := FWModelActive()
	Local oView  := FWViewActive()
	Local oDadosBody := oModel:GetModel("BODY2")

	oDadosBody:DeActivate()

	oDadosBody:SetLoadFilter( { { 'EA_NUMBOR', cNumbor } } )

	oDadosBody:Activate()

	oDadosBody:GOLINE(1)
	oDadosBody:GOLINE(1)
	oDadosBody:GOLINE(1)
	oView:Refresh()

Return .T.


/*/{Protheus.doc} nomeStaticFunction
  (long_description)
  @type  Static Function
  @author Pedro Lindenberg
  @since 02/07/2024
  @version version
/*/
Static Function fSeaDouble(oFormulario,cFieldName,nLineGrid,nLineModel)
	Local nLinAtu := nLineGrid
	Local oModel := FWModelActive()
	Local oFields := oModel:GetModel("BODY2")

	cNumBord := OFIELDS:ADATAMODEL[nLinAtu][1][1][2]

	DLP06F02C(cNumBord)

Return .T.


//--------------------------------------------------------------
/*/{Protheus.doc} MyFunction
Description

@param xParam Parameter Description
@return xRet Return Description
@author Pedro Lindenberg - pedro.silveira@totvs.com.br
@since 02/07/2024
/*/
//--------------------------------------------------------------
Static Function DLP06F02C(cNumBord)
	Local oNumBor
	Local cNumBor := cNumBord //Space(6)
	Local oToken
	Local cToken := Space(6)
	Local oButton1
	Local oSay1
	Local oSay2
	Static oDlg

	DEFINE MSDIALOG oDlg TITLE "Token para confirmação, envio de Borderô" FROM 000, 000  TO 200, 500 COLORS 0, 16777215 PIXEL

	@ 032, 020 SAY oSay1 PROMPT "Numero do Borderô:" SIZE 052, 007 OF oDlg COLORS 0, 16777215 PIXEL
	@ 031, 075 MSGET oNumBor VAR cNumBor SIZE 090, 010 OF oDlg COLORS 0, 16777215 PIXEL
	@ 050, 020 SAY oSay2 PROMPT "Insira aqui o Token:" SIZE 052, 009 OF oDlg COLORS 0, 16777215 PIXEL
	@ 049, 075 MSGET oToken VAR cToken SIZE 090, 010 OF oDlg COLORS 0, 16777215 PIXEL
	@ 076, 197 BUTTON oButton1 PROMPT "Enviar" SIZE 044, 015 OF oDlg ACTION fSendtkn(cToken,cNumBor) PIXEL

	ACTIVATE MSDIALOG oDlg CENTERED

Return

/*/{Protheus.doc} fsndtkn
  (long_description)
  @type  Static Function
  @author Pedro Lindenberg
  @since 23/06/2024
/*/
Static Function fSendtkn(cToken,cNumBor)
	Local cAlias := GetNextAlias()
	Local cLockName := ""
	Local cRealTkn := ""
	Local lVldTkn := .T.
	Local aSeaArea := SEA->(GetArea())
	cLibTk :="N"
	IF lVldTkn

		If Select(cAlias) <> 0
			(cAlias)->(DbCloseArea())
		EndIf

		BeginSql alias cAlias
			%noparser%

			Select
				SEA.EA_YTOKEN,
				SEA.EA_NUMBOR
			from
				%Table:SEA% SEA
			Where
				SEA.EA_NUMBOR = %EXP:cNumBor%
				and SEA.EA_YBLQPIX = %EXP:cLibTk%
				and SEA.%notDel%
		EndSql

		If (cAlias)->(!EOF())
			cRealTkn := (cAlias)->EA_YTOKEN
		EndIf
		IF ALLTRIM(cToken) == ALLTRIM((cRealTkn))

			FWAlertSuccess("Token enviado com sucesso!", "Sucesso")
			cLockName := cEmpAnt + ' - FINA717'

			SEA->(DbSetOrder(1))
			If SEA->(DbSeek(xFilial('SEA')+(cAlias)->EA_NUMBOR))
				while SEA->(!EOF())
					If RecLock('SEA',.F.)
						SEA->EA_YBLQPIX := 'S'
						SEA->(MsUnlock())
						SEA->(DBSKIP())
					EndIf
				END
			EndIf

			lRet := .T.
			oDlg:End()
			fFeedTbe()

		ELSE

			FWAlertError("Token inválido, verifique", "ERRO")
			lRet := .F.
			oDlg:End()
			DLP06F02C()

		ENDIF

		(cAlias)->(DbCloseArea())

	ENDIF

	RESTAREA(aSeaArea)

Return Nil


/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author user
@since 02/07/2024
@version version
/*/
User Function DLP06F2F()
	RPCSETENV('01','01')

	Local cLockName As Character
	Private lRet := .F.

	cLockName := cEmpAnt + ' - FINA717'

	If F717VldUso()
		If LockByName(cLockName, .T., .F. ) // uma execução por vez
			F717Pagar()
			UnLockByName(cLockName, .T., .F. )
		EndIf
	EndIf

Return Nil

// If F717VldUso()
// 	If LockByName(cLockName, .T., .F. ) /s/ uma execução por vez
// 		F717Pagar()
// 		UnLockByName(cLockName, .T., .F. )
// 	EndIf
// EndIf

/*/{Protheus.doc} nomeStaticFunction
	Adiciona botao em tela.
	@type  Static Function
	@author Pedro Lindenberg
	@since 31/10/2023
	@version version
/*/
Static Function CreateBtn(oPanel)
	Local cCSSBtn1 := " "
	Local cFont := "Arial"
	Local oFontBtn := TFont():New(cFont,,-12,,.F.)

	oBtnT:= TButton():New( 010, 55, "Pesquisar",oPanel,{||fLineOpts()}, 56,15,,oFontBtn,.F.,.T.,.F.,,.F.,,,.F. )

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
	(long_description)
	@type  Static Function
	@author user
	@since 03/07/2024
/*/
Static Function fLineOpts()
	Local oModel := FWModelActive()
	Local oView  := FWViewActive()
	Local oDadosMast := oModel:GetModel("MASTER")
	Local oDadosBody := oModel:GetModel("BODY2")
	Local aSea := SEA->(GetArea())
	Local cAlias := GetNextAlias()
	Local cNumBord

	cNumBord := oDadosMast:GetValue("NUMBOR")

	oView:Refresh()

	IF !EMPTY(cNumBord)

		BEGINSQL ALIAS cAlias
			SELECT
				SEA.EA_FILIAL,
				SEA.EA_NUMBOR,
				SEA.EA_DATABOR,
				SEA.EA_FORNECE,
				SEA.EA_LOJA,
				SEA.EA_NUMCON
			FROM
				%Table:SEA% SEA
			WHERE
				SEA.%NotDel%
				AND SEA.EA_NUMBOR = %EXP:cNumBord%
				AND SEA.EA_YBLQPIX = 'N'
		ENDSQL

	ELSE

		BEGINSQL ALIAS cAlias
			SELECT
				SEA.EA_FILIAL,
				SEA.EA_NUMBOR,
				SEA.EA_DATABOR,
				SEA.EA_FORNECE,
				SEA.EA_LOJA,
				SEA.EA_NUMCON
			FROM
				%Table:SEA% SEA
			WHERE
				SEA.%NotDel%
				AND SEA.EA_YBLQPIX = 'N'
		ENDSQL

	ENDIF

	oDadosBody:SetMaxLine(9999999)
	oDadosBody:SetNoInsertLine(.F.)
	oDadosBody:SetNoDeleteLine(.F.)
	oDadosBody:ClearData()
	oDadosBody:InitLine()
	oDadosBody:GoLine(1)

	(cAlias)->(dbGoTop())

	while (cAlias)->(!Eof())

		oDadosBody:SetValue("EA_FILIAL"   , (cAlias)->EA_FILIAL         )
		oDadosBody:SetValue("EA_NUMBOR"   , (cAlias)->EA_NUMBOR         )
		oDadosBody:SetValue("EA_DATABOR"  , StoD((cAlias)->EA_DATABOR)  )
		oDadosBody:SetValue("EA_FORNECE"  , (cAlias)->EA_FORNECE        )
		oDadosBody:SetValue("EA_LOJA"     , (cAlias)->EA_LOJA           )
		oDadosBody:SetValue("EA_NUMCON"   , (cAlias)->EA_NUMCON         )

		(cAlias)->(DbSkip())

		if (cAlias)->(!Eof())
			oDadosBody:AddLine()
		ENDIF

	end

	oDadosBody:goline(1)
	oDadosBody:SetNoInsertLine( .F. )
	oDadosBody:SetNoDeleteLine( .F. )

	(cAlias)->(DbCloseArea())

	oView:Refresh()
	RestArea(aSea)

Return
