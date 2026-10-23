#Include 'Protheus.ch'
#Include 'FWEditPanel.ch'
#INCLUDE "FWMVCDEF.CH"
#INCLUDE "TOPCONN.CH"
#Include "TOTVS.ch"
#DEFINE SIMPLES Char( 39 )
#DEFINE DUPLAS  Char( 34 )

#DEFINE CSSBOTAO	"QPushButton { color: #024670; "+;
    "    border-image: url(rpo:fwstd_btn_nml.png) 3 3 3 3 stretch; "+;
    "    border-top-width: 3px; "+;
    "    border-left-width: 3px; "+;
    "    border-right-width: 3px; "+;
    "    border-bottom-width: 3px }"+;
    "QPushButton:pressed {	color: #FFFFFF; "+;
    "    border-image: url(rpo:fwstd_btn_prd.png) 3 3 3 3 stretch; "+;
    "    border-top-width: 3px; "+;
    "    border-left-width: 3px; "+;
    "    border-right-width: 3px; "+;
    "    border-bottom-width: 3px }"

/**/

user function DLP04F03()

    Local aButtons := {{.F.,Nil},{.F.,Nil},{.F.,Nil},{.T.,Nil},{.F.,Nil},{.F.,Nil},{.T.,Nil },{.T.,Nil },{.F.,Nil},{.F.,Nil},{.F.,Nil},{.F.,Nil},{.F.,Nil},{.F.,Nil}}

    Private aCPOBase := {'B1_GRUPO','B1_COD','B1_DESC','B1_REFEREN','B1_REFCANT','B1_CODDES';
        ,'B1_TIPO','B1_YHOHS','B1_POSIPI','B1_LOCPAD','B1_UM','B1_SEGUM','B1_TE','B1_TS','B1_PICMRET';
        ,'B1_CONV','B1_TIPCONV','B1_TPMAT','B1_ESPECIE','B1_EX_NCM','B1_EX_NBM','B1_ORIGEM'    }

    FWExecView("Delpi - Cadastro Produto","VIEWDEF.DLP04F03",3,,{|| .T.},/*bOk*/ ,65  /*nPercReducao*/,aButtons)

Return

Static Function ModelDef()
    Local oModel
    Local oStrCab := GETSTCAB(1)
    oModel := MPFormModel():New('MDDLP04F03',/*bPreValidacao*/,  /*{|oModel| u_validtok(oModel)} /* bTudoOK*/ ,  {|oModel| U_D04F3TOK( oModel:GetOperation(), oModel)})

    oModel:SetDescription('Delpi')

    oModel:addFields('MASTER',,oStrCab)

    oModel:getModel("MASTER"):SetDescription("DELPI")
    //oModel:getModel("MASTER"):SetDescription("Grid")

    //oModel:SetDescription("Consulta Missing Parts")

    oModel:SetActivate( {|oModel| IniDados( oModel ) } )
    oModel:SetPrimaryKey({})



Return oModel


Static Function ViewDef()
    Local oView
    Local oModel  := ModelDef()
    Local oStrCab := GETSTCAB(2)
    // Local oStrTab := GETSTGRD(2) // Grid Tabela


    //  Local oStrCAD := GETSTCAD(2) // Grid Cadastros

    oView        := FWFormView():New()
    oView:SetModel(oModel)

    oView:AddField('FORMCAB' , oStrCab,'MASTER' )
    //  oView:AddGrid('FORMTAB'  , oStrTab,'GRID1')
    //oView:AddGrid('FORMCAD'  , oStrCAD,'GRID2')

    oView:CreateHorizontalBox( 'BOXFORMCAB', 100) //Cabeçalho
    oView:SetOwnerView('FORMCAB','BOXFORMCAB')



Return oView


/*/{Protheus.doc} GETSTCAB

    Gera a estrutura de cabeçalho dos campos. para  a View e Model
    @author  Gabriel
    @since   25-08-2021
/*/

Static function GETSTCAB(nTipo)
    Local aAux      := {}
    Local oStruct   := NIL
    Local bValid    := NIl
    Local nI        := 0
    Local bInic     := NIL
    Local bWhen     := NIL
    Local aLista    := NIL
    Local cLista    := ""
    Local cTipCampo := ""
    Local aCampos   := {}
    Local n1

    For n1 := 1 to Len(aCPOBase)

        AADD(aCampos,{trim(GETSX3CACHE(aCPOBase[n1],'X3_TITULO')  ),;
            trim(GETSX3CACHE(aCPOBase[n1],'X3_TITULO') ) ,;
            trim( GETSX3CACHE(aCPOBase[n1],'X3_CAMPO') ),;
            GETSX3CACHE(aCPOBase[n1],'X3_TIPO')     ,GETSX3CACHE(aCPOBase[n1],'X3_TAMANHO')       ,GETSX3CACHE(aCPOBase[n1],'X3_DECIMAL')  ,,''})

    Next n1

    //AADD(aCampos,{'OP' ,'Ordem de Producao' ,'OP' ,GETSX3CACHE('ZZI_OP','X3_TIPO')     ,GETSX3CACHE('ZZI_OP','X3_TAMANHO')       ,GETSX3CACHE('ZZI_OP','X3_DECIMAL')  ,,''})
    //AADD(aCampos,{'OP' ,'Ordem de Producao' ,'OP' ,GETSX3CACHE('ZZI_OP','X3_TIPO')     ,GETSX3CACHE('ZZI_OP','X3_TAMANHO')       ,GETSX3CACHE('ZZI_OP','X3_DECIMAL')  ,,''})
    //AADD(aCampos,{'YPR','YPR - Pedido Venda','YPR',GETSX3CACHE('C5_NUM','X3_TIPO')     ,GETSX3CACHE('C5_NUM','X3_TAMANHO')       ,GETSX3CACHE('','X3_DECIMAL')  ,,''})
    //AADD(aCampos,{'ID' ,'Codigo do Produto' ,'ID' ,GETSX3CACHE('ZZI_PRODUT','X3_TIPO') ,GETSX3CACHE('ZZI_PRODUT','X3_TAMANHO')   ,GETSX3CACHE('ZZI_PRODUT','X3_DECIMAL')  ,,''})
    //AADD(aCampos,{'Produto' ,'Codigo do Produto 02 ' ,'PRODUTO' ,GETSX3CACHE('ZZI_PRODUT','X3_TIPO') ,GETSX3CACHE('ZZI_PRODUT','X3_TAMANHO')   ,GETSX3CACHE('ZZI_PRODUT','X3_DECIMAL')  ,,''})

    If nTipo == 1	// Model

        oStruct := FWFormModelStruct():New()
        oStruct:AddTable('TMP',,'TMP')
        //   oStruct:AddIndex( 1 , '' , 'OP', '' , '' , '', .F. )

        For nI := 1 to len(aCampos)
            bValid  := ""
            bInic   := ""
            bWhen   := Nil
            aLista  := NIL

            //IF aCampos[nI,3] == "LOAD" // Campo - Botao carregar
            //    bValid := "U_LOADTAB()"
            //    aCampos[nI,4] := 'BT'
            //ENDIF

            bValid := FwBuildFeature(1,bValid)

            If !Empty(bWhen)
                bWhen	:= FwBuildFeature(2,bWhen)
            EndIf

            bInic  := FwBuildFeature(3,bInic)

            oStruct:AddField(              ;
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
    ELSE

        oStruct := FWFormViewStruct():New()

        For nI := 1 to len(aCampos)

            IF(aCampos[nI,3]$cLista)
                cTipCampo := 'COMBO'
            else
                cTipCampo :='GET'
            ENDIF

            //IF aCampos[nI,3] == "LOAD"
            //    cTipCampo := 'BT' // Quando o campo for do tipo Btn.
            //ENDIF

            aLista := NIL

            oStruct:AddField( 			   ;
                aCampos[nI,3]  				 , ;                // [01] Campo
                STRZERO(nI,2)    			 , ;                // [02] Ordem
                aCampos[nI,1]				 , ;                // [03] Titulo
                aCampos[nI,2]			     , ;                // [04] Descricao
                NIL                          , ;                // [05] Help
                cTipCampo                    , ;      // [06] Tipo do campo   COMBO, Get ou CHECK
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



Static Function DLP04F03A()

    Local  aMarcadas := {}//  EscEmpresa()


    /*Seleciona as Empresas*/
    aMarcadas :=   EscEmpresa()

Return





//--------------------------------------------------------------------
/*/{Protheus.doc} EscEmpresa
Função genérica para escolha de Empresa, montada pelo SM0

@return aRet Vetor contendo as seleções feitas.
             Se não for marcada nenhuma o vetor volta vazio

@author Ernani Forastieri
@since  27/09/2004
@version 1.0
/*/
//--------------------------------------------------------------------
Static Function EscEmpresa()

    //---------------------------------------------
    // Parâmetro  nTipo
    // 1 - Monta com Todas Empresas/Filiais
    // 2 - Monta só com Empresas
    // 3 - Monta só com Filiais de uma Empresa
    //
    // Parâmetro  aMarcadas
    // Vetor com Empresas/Filiais pré marcadas
    //
    // Parâmetro  cEmpSel
    // Empresa que será usada para montar seleção
    //---------------------------------------------
    Local   aRet      := {}
    Local   aSalvAmb  := GetArea()
    Local   aSalvSM0  := {}
    Local   aVetor    := {}
    Local   cMascEmp  := "??"
    Local   cVar      := ""
    Local   lChk      := .F.
    Local   lOk       := .F.
    Local   lTeveMarc := .F.
    Local   oNo       := LoadBitmap( GetResources(), "LBNO" )
    Local   oOk       := LoadBitmap( GetResources(), "LBOK" )
    Local   oDlg, oChkMar, oLbx, oMascEmp, oSay
    Local   oButDMar, oButInv, oButMarc, oButOk, oButCanc
    Local nx
    Local   aMarcadas := {}


    /*If !MyOpenSm0(.F.)
        Return aRet
    EndIf*/



    aAllGroup := FWAllGrpCompany()

    For nx := 1 to Len(aAllGroup)
        IF aAllGroup[NX] != cEmpAnt
            aAdd(  aVetor, { .F.,aAllGroup[NX],"01",;
                FWFilName ( aAllGroup[NX],"01"),FWFilName ( aAllGroup[NX],"01")            })
        ENDIF
    Next nx

    Define MSDialog  oDlg Title "" From 0, 0 To 280, 395 Pixel

    oDlg:cToolTip := "Tela para Múltiplas Seleções de Empresas/Filiais"

    oDlg:cTitle   := "Selecione a(s) Empresa(s) para Atualização"

    @ 10, 10 Listbox  oLbx Var  cVar Fields Header " ", " ", "Empresa" Size 178, 095 Of oDlg Pixel
    oLbx:SetArray(  aVetor )
    oLbx:bLine := {|| {IIf( aVetor[oLbx:nAt, 1], oOk, oNo ), ;
        aVetor[oLbx:nAt, 2], ;
        aVetor[oLbx:nAt, 4]}}
    oLbx:BlDblClick := { || aVetor[oLbx:nAt, 1] := !aVetor[oLbx:nAt, 1], VerTodos( aVetor, @lChk, oChkMar ), oChkMar:Refresh(), oLbx:Refresh()}
    oLbx:cToolTip   :=  oDlg:cTitle
    oLbx:lHScroll   := .F. // NoScroll

    @ 112, 10 CheckBox oChkMar Var  lChk Prompt "Todos" Message "Marca / Desmarca"+ CRLF + "Todos" Size 40, 007 Pixel Of oDlg;
        on Click MarcaTodos( lChk, @aVetor, oLbx )

    // Marca/Desmarca por mascara
    @ 113, 51 Say   oSay Prompt "Empresa" Size  40, 08 Of oDlg Pixel
    @ 112, 80 MSGet oMascEmp Var  cMascEmp Size  05, 05 Pixel Picture "@!"  Valid (  cMascEmp := StrTran( cMascEmp, " ", "?" ), oMascEmp:Refresh(), .T. ) ;
        Message "Máscara Empresa ( ?? )"  Of oDlg
    oSay:cToolTip := oMascEmp:cToolTip

    @ 128, 10 Button oButInv    Prompt "&Inverter"  Size 32, 12 Pixel Action ( InvSelecao( @aVetor, oLbx, @lChk, oChkMar ), VerTodos( aVetor, @lChk, oChkMar ) ) ;
        Message "Inverter Seleção" Of oDlg
    oButInv:SetCss( CSSBOTAO )
    @ 128, 50 Button oButMarc   Prompt "&Marcar"    Size 32, 12 Pixel Action ( MarcaMas( oLbx, aVetor, cMascEmp, .T. ), VerTodos( aVetor, @lChk, oChkMar ) ) ;
        Message "Marcar usando" + CRLF + "máscara ( ?? )"    Of oDlg
    oButMarc:SetCss( CSSBOTAO )
    @ 128, 80 Button oButDMar   Prompt "&Desmarcar" Size 32, 12 Pixel Action ( MarcaMas( oLbx, aVetor, cMascEmp, .F. ), VerTodos( aVetor, @lChk, oChkMar ) ) ;
        Message "Desmarcar usando" + CRLF + "máscara ( ?? )" Of oDlg
    oButDMar:SetCss( CSSBOTAO )
    @ 112, 157  Button oButOk   Prompt "Processar"  Size 32, 12 Pixel Action (  RetSelecao( @aRet, aVetor ), IIf( Len( aRet ) > 0, oDlg:End(), MsgStop( "Ao menos um grupo deve ser selecionado", "UPDDLP01" ) ) ) ;
        Message "Confirma a seleção e efetua" + CRLF + "o processamento" Of oDlg
    oButOk:SetCss( CSSBOTAO )
    @ 128, 157  Button oButCanc Prompt "Cancelar"   Size 32, 12 Pixel Action ( IIf( lTeveMarc, aRet :=  aMarcadas, .T. ), oDlg:End() ) ;
        Message "Cancela o processamento" + CRLF + "e abandona a aplicação" Of oDlg
    oButCanc:SetCss( CSSBOTAO )

    Activate MSDialog  oDlg Center

    //  RestArea( aSalvAmb )
    //  dbSelectArea( "SM0" )
    //  dbCloseArea()

Return  aRet


//--------------------------------------------------------------------
/*/{Protheus.doc} MarcaTodos
Função auxiliar para marcar/desmarcar todos os ítens do ListBox ativo

@param lMarca  Contéudo para marca .T./.F.
@param aVetor  Vetor do ListBox
@param oLbx    Objeto do ListBox

@author Ernani Forastieri
@since  27/09/2004
@version 1.0
/*/
//--------------------------------------------------------------------
Static Function MarcaTodos( lMarca, aVetor, oLbx )
    Local  nI := 0

    For nI := 1 To Len( aVetor )
        aVetor[nI][1] := lMarca
    Next nI

    oLbx:Refresh()

Return NIL


//--------------------------------------------------------------------
/*/{Protheus.doc} InvSelecao
Função auxiliar para inverter a seleção do ListBox ativo

@param aVetor  Vetor do ListBox
@param oLbx    Objeto do ListBox

@author Ernani Forastieri
@since  27/09/2004
@version 1.0
/*/
//--------------------------------------------------------------------
Static Function InvSelecao( aVetor, oLbx )
    Local  nI := 0

    For nI := 1 To Len( aVetor )
        aVetor[nI][1] := !aVetor[nI][1]
    Next nI

    oLbx:Refresh()

Return NIL


//--------------------------------------------------------------------
/*/{Protheus.doc} RetSelecao
Função auxiliar que monta o retorno com as seleções

@param aRet    Array que terá o retorno das seleções (é alterado internamente)
@param aVetor  Vetor do ListBox

@author Ernani Forastieri
@since  27/09/2004
@version 1.0
/*/
//--------------------------------------------------------------------
Static Function RetSelecao( aRet, aVetor )
    Local  nI    := 0

    aRet := {}
    For nI := 1 To Len( aVetor )
        If aVetor[nI][1]
            aAdd( aRet, { aVetor[nI][2] , aVetor[nI][3], aVetor[nI][2] +  aVetor[nI][3] } )
        EndIf
    Next nI

Return NIL


//--------------------------------------------------------------------
/*/{Protheus.doc} MarcaMas
Função para marcar/desmarcar usando máscaras

@param oLbx     Objeto do ListBox
@param aVetor   Vetor do ListBox
@param cMascEmp Campo com a máscara (???)
@param lMarDes  Marca a ser atribuída .T./.F.

@author Ernani Forastieri
@since  27/09/2004
@version 1.0
/*/
//--------------------------------------------------------------------
Static Function MarcaMas( oLbx, aVetor, cMascEmp, lMarDes )
    Local cPos1 := SubStr( cMascEmp, 1, 1 )
    Local cPos2 := SubStr( cMascEmp, 2, 1 )
    Local nPos  := oLbx:nAt
    Local nZ    := 0

    For nZ := 1 To Len( aVetor )
        If cPos1 == "?" .or. SubStr( aVetor[nZ][2], 1, 1 ) == cPos1
            If cPos2 == "?" .or. SubStr( aVetor[nZ][2], 2, 1 ) == cPos2
                aVetor[nZ][1] := lMarDes
            EndIf
        EndIf
    Next

    oLbx:nAt := nPos
    oLbx:Refresh()

Return NIL


//--------------------------------------------------------------------
/*/{Protheus.doc} VerTodos
Função auxiliar para verificar se estão todos marcados ou não

@param aVetor   Vetor do ListBox
@param lChk     Marca do CheckBox do marca todos (referncia)
@param oChkMar  Objeto de CheckBox do marca todos

@author Ernani Forastieri
@since  27/09/2004
@version 1.0
/*/
//--------------------------------------------------------------------
Static Function VerTodos( aVetor, lChk, oChkMar )
    Local lTTrue := .T.
    Local nI     := 0

    For nI := 1 To Len( aVetor )
        lTTrue := IIf( !aVetor[nI][1], .F., lTTrue )
    Next nI

    lChk := IIf( lTTrue, .T., .F. )
    oChkMar:Refresh()

Return NIL

/*Função para confirmar e inserir os dados nas demais empresas*/
USER FUNCTION D04F3TOK(nOper, oModel)
    Local lRet := .t.
    Local lCont :=  .t. //FWAlertNoYes("Deseja replicar o Produto para as demais Empresas?","01 - Delpi")
    Local aMarcadas := {}
    Local oModel     := FWMODELACTIVE()
    //  Local oView      := FWViewActive()
    Local oModelTmp  := oModel:GetModel("MASTER")
    Local aSB1 := {}
    lOCAL n2
    lOCAL n1
    if !lCont
        lRet := .f.

    else
        aMarcadas :=   EscEmpresa()
    endif

    if len(aMarcadas) >0

        For n2 := 1 to Len(aCPOBase)
            aTMP := {aCPOBase[n2],oModelTmp:getvalue(aCPOBase[n2]),nil}


            aadd(aSB1,aTMP)

        Next n2


        For n1 := 1 to Len(aMarcadas)

            cEmpMrk := aMarcadas[n1][1]
            FWMsgRun(, {|| fProcSB1(cEmpMrk,aSB1) } , "03 - Delpi", "Processando...")

        Next n1

    else
        FWAlertWarning("Nenhuma Empresa Selecionada", "02 - Delpi")
        lRet := .f.
    Endif

    conout("fim")
Return lRet


Static Function fProcSB1(cEmpMrk,aSB1)
    //Local aSB1 := {}
    //Default cEmpMrk := "05"
    Local n1
    Local jBody := JsonObject():New()
    Local cUrl := "http://192.168.1.8:8060/rest/"+cEmpMrk+"/delpiproduto/v1/"
    Local cPatch := ""
    Local cEol := chr(10)+chr(13)
    Local aHeader   := {}
    Local nPosCod :=  ascan(aSB1,{|x| Trim(x[1]) == "B1_COD"})

    // CABEÇALHO DA REQUISIÇÃO


    /* If Select("TMP1") > 1
        TMP1->(DbCloseArea())
    EndIf
    stp_Protheus_GetOPerSB1
    cQuery :="EXEC dbo.stp_Protheus_GetOPerSB1  "
    cQuery +="  @CODPROD =    " +  valtosql( aSb1[nPosCod][2])
    cQuery +=" ,@EMP    =    " +  valtosql( cEmpMrk)*/

    aResult := TCSPExec("stp_Protheus_GetOPerSB1",  TRIM(aSb1[nPosCod][2]), cEmpMrk)

    cRet := ""

    IF Empty(aResult)

        Conout('Erro na execução da Consulta de Codigo de Produto Disponivel : '+TcSqlError())
        Alert('Erro na execução da Consulta de Codigo de Produto Disponivel : '+TcSqlError())

    ElseIf	ValType(aResult) == 'A'
        cRet := alltrim(aResult[1])
    EndIf

    CONOUT("teste")

    //  TcQuery cQuery New Alias "TMP1"


    // PREENCHE CABEÇALHO DA REQUISIÇÃO
    AAdd(aHeader, "Content-Type: application/json; charset=UTF-8")
    AAdd(aHeader, "Accept: application/json")
    AAdd(aHeader, "User-Agent: Chrome/65.0 (compatible; Protheus " + GetBuild() + ")")
    For n1 := 1 to Len(aSB1)
        jBody[aSB1[n1][1]] := cvaltochar(aSB1[n1][2])
    Next n1
    oRestClient := FWRest():New(cUrl)


    IF "ALTERAR" $ cRet
        cPatch := "IncProduto/alterar"
        oRestClient:setPath(cPatch)
        // REALIZA O MÉTODO PUT, ENVIA O JSON NO CORPO (BODY) E VALIDA O RETORNO
        If (oRestClient:Put(aHeader,jBody:toJson()))
            ConOut("PUT: " + oRestClient:GetResult()) //SUCESSO
            cTitulo := "DELPI - INTEGRACAO PRODUTOS"
            cTxt := "Produto Alterado com Sucesso"+ cEol
            cTxt += "Empresa "+ cEmpMrk + " | Produto" +   TRIM(aSb1[nPosCod][2])  + cEol

            EEcView(cTxt,cTitulo)
        Else
            ConOut("PUT: " + oRestClient:GetLastError()) // ERRO
            cTitulo := "DELPI - INTEGRACAO PRODUTOS"
            cTxt := "Erro ao tentar Alterar o Produto"+ cEol
            cTxt += "Empresa "+ cEmpMrk + " | Produto" +   TRIM(aSb1[nPosCod][2])  + cEol
            cTxt += "Erro Integração"  + cEol
            cTxt += oRestClient:getLastError() + cEol
            cTxt += "Erro Rotina Automatica"  + cEol
            cTxt += oRestClient:getResult()  + cEol
            EEcView(cTxt,cTitulo)
        EndIf

    ELSEIF  "INCLUIR" $ cRet
        cPatch := "IncProduto/incluir"
        oRestClient:setPath(cPatch)
        oRestClient:SetPostParams(jBody:toJson())

        If oRestClient:Post(aHeader)
            cError := ""
            nStatus := HTTPGetStatus(@cError)

            if nStatus >= 200 .And. nStatus <= 299
                if Empty(oRestClient:getResult())
                    MsgInfo(nStatus,"01")
                else
                    //  MsgInfo(oRestClient:getResult(),"02") //AJUSTAR AQUI - SUCESSO
                    ConOut("POST: " + oRestClient:GetResult()) //SUCESSO
                    cTitulo := "DELPI - INTEGRACAO PRODUTOS"
                    cTxt := "Produto Incluido com Sucesso"+ cEol
                    cTxt += "Empresa "+ cEmpMrk + " | Produto" +   TRIM(aSb1[nPosCod][2])  + cEol
                    //cTxt += "Erro Integração"  + cEol
                    //cTxt += oRestClient:getLastError() + cEol
                    //cTxt += "Erro Rotina Automatica"  + cEol
                    //cTxt += oRestClient:getResult()  + cEol
                    EEcView(cTxt,cTitulo)
                endif
            else
                MsgStop(cError)
            endif
        else
            cTitulo := "DELPI - INTEGRACAO PRODUTOS"
            cTxt := "Erro ao tentar Incluir o Produto"+ cEol
            cTxt += "Empresa "+ cEmpMrk + " | Produto" +   TRIM(aSb1[nPosCod][2])  + cEol
            cTxt += "Erro Integração"  + cEol
            cTxt += oRestClient:getLastError() + cEol
            cTxt += "Erro Rotina Automatica"  + cEol
            cTxt += oRestClient:getResult()  + cEol
            EEcView(cTxt,cTitulo)
            // MsgStop(oRestClient:getLastError() + CRLF + oRestClient:getResult(),"03") //- AJUSTAR AQUI ERRO 	EEcView(cTxt,cTitulo)
        endif
    ENDIF


Return
/*/{Protheus.doc} nomeFunction
(long_description)
@type  Function
@author user
@since 15/10/2021
@version version
@param param_name, param_type, param_descr
@return return_var, return_type, return_description
@example
(examples)
@see (links_or_references)
/*/

Static Function IniDados (oModel )

    Local oDados     := oModel:GetModel("MASTER")
    Local oModelStr     := oModel:GetModel("MASTER"):GetStruct()
    Private lInclui		:= oModel:GetOperation() == MODEL_OPERATION_INSERT
    Private lAltera		:= oModel:GetOperation() == MODEL_OPERATION_UPDATE

    if !oModel:IsActive()
        oModel:Activate()
    endif
    oDados:SETValue('B1_GRUPO  ',   SB1->B1_GRUPO)
    oDados:SETValue('B1_COD',SB1->B1_COD)
    oDados:SETValue('B1_DESC',SB1->B1_DESC)
    oDados:SETValue('B1_REFEREN',SB1->B1_REFEREN)
    oDados:SETValue('B1_REFCANT',SB1->B1_REFCANT)
    oDados:SETValue('B1_CODDES',SB1->B1_CODDES)
    oDados:SETValue('B1_TIPO',SB1->B1_TIPO)
    oDados:SETValue('B1_YHOHS',SB1->B1_YHOHS)
    oDados:SETValue('B1_POSIPI',SB1->B1_POSIPI)
    oDados:SETValue('B1_LOCPAD',SB1->B1_LOCPAD)
    oDados:SETValue('B1_UM',SB1->B1_UM)
    oDados:SETValue('B1_SEGUM',SB1->B1_SEGUM)
    oDados:SETValue('B1_TE',SB1->B1_TE)
    oDados:SETValue('B1_TS',SB1->B1_TS)
    oDados:SETValue('B1_PICMRET',SB1->B1_PICMRET)
    oDados:SETValue('B1_CONV',SB1->B1_CONV)
    oDados:SETValue('B1_TIPCONV',SB1->B1_TIPCONV)
    oDados:SETValue('B1_TPMAT',SB1->B1_TPMAT)
    oDados:SETValue('B1_ESPECIE',SB1->B1_ESPECIE)
    oDados:SETValue('B1_EX_NCM',SB1->B1_EX_NCM)
    oDados:SETValue('B1_EX_NBM',SB1->B1_EX_NBM)
    oDados:SETValue('B1_ORIGEM',SB1->B1_ORIGEM)

    bWhen	:= FwBuildFeature(2,".F.")

    oModelStr:SetProperty('*',MODEL_FIELD_WHEN,bWhen)


    bWhen	:= FwBuildFeature(2,".T.")

    oModelStr:SetProperty('B1_DESC',MODEL_FIELD_WHEN,bWhen)


Return

