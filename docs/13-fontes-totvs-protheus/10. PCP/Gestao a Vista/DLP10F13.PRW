#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

//-------------------------------------------------------------------
/*/{Protheus.doc} COMP011_MVC
Exemplo de montagem da modelo e interface para um tabela em MVC

@author Ernani Forastieri e Rodrigo Antonio Godinho
@since 05/10/2009
@version P10
/*/
//-------------------------------------------------------------------
User Function DLP10F13()
    Local oBrowse

    chkfile("SZC")

    oBrowse := FWMBrowse():New()
    oBrowse:SetAlias('SZC')
    oBrowse:SetDescription('Cadastro de Metas Faturamento')
    oBrowse:SetMenuDef("DLP10F13")
    //oBrowse:AddLegend( "ZA0_TIPO=='1'", "YELLOW", "Autor"      )
    //oBrowse:AddLegend( "ZA0_TIPO=='2'", "BLUE"  , "Interprete" )
    //oBrowse:SetFilterDefault( "ZA0_TIPO=='1'" )
    //oBrowse:SetFilterDefault( "Empty(ZA0_DTAFAL)" )
    //oBrowse:DisableDetails()
    //oBrowse:SetCacheView( .F. )
    oBrowse:SetCanSaveArea(.T.)

    oBrowse:Activate()

Return NIL

//-------------------------------------------------------------------
Static Function MenuDef()
    Local aRotina := {}

    ADD OPTION aRotina TITLE 'Visualizar' ACTION 'VIEWDEF.DLP10F13' OPERATION 2 ACCESS 0
    ADD OPTION aRotina TITLE 'Incluir'    ACTION 'VIEWDEF.DLP10F13' OPERATION 3 ACCESS 0
    ADD OPTION aRotina TITLE 'Alterar'    ACTION 'VIEWDEF.DLP10F13' OPERATION 4 ACCESS 0
    ADD OPTION aRotina TITLE 'Excluir'    ACTION 'VIEWDEF.DLP10F13' OPERATION 5 ACCESS 0
    ADD OPTION aRotina TITLE 'Imprimir'   ACTION 'VIEWDEF.DLP10F13' OPERATION 8 ACCESS 0
    ADD OPTION aRotina TITLE 'Copiar'     ACTION 'VIEWDEF.DLP10F13' OPERATION 9 ACCESS 0
Return aRotina


//-------------------------------------------------------------------
Static Function ModelDef()
    // Cria a estrutura a ser usada no Modelo de Dados
    Local oStruSZC := FWFormStruct( 1, 'SZC', /*bAvalCampo*/,/*lViewUsado*/ )
    Local oModel

    //ZC_LJCLI	ZC_NMCLI //20

    // Cria o objeto do Modelo de Dados
    oModel := MPFormModel():New('DLPF13M', /*bPreValidacao*/, /*bPosValidacao*/, /*bCommit*/, /*bCancel*/ )
    //oModel := MPFormModel():New('COMP011MODEL', /*bPreValidacao*/, { |oMdl| COMP011POS( oMdl ) }, /*bCommit*/, /*bCancel*/ )

    // Adiciona ao modelo uma estrutura de formulário de edição por campo
    oModel:AddFields( 'SZCMASTER', /*cOwner*/, oStruSZC, /*bPreValidacao*/, /*bPosValidacao*/, /*bCarga*/ )
    // Adiciona a descricao do Modelo de Dados
    //oModel:SetDescription( 'Modelo de Dados de Metas' )
    oModel:SetPrimaryKey({'ZC_FILIAL','ZC_FIL' ,'ZC_EMP','ZC_ANOMES'})

    //oStruSZC:AddTrigger('ZC_LJCLI',"ZC_NMCLI"    ,{|| .T.}, {|| D02F02C()	} )
    // Adiciona a descricao do Componente do Modelo de Dados


    // Liga a validação da ativacao do Modelo de Dados
    //oModel:SetVldActivate( { |oModel| COMP011ACT( oModel ) } )

Return oModel

//-------------------------------------------------------------------
Static Function ViewDef()
    // Cria um objeto de Modelo de Dados baseado no ModelDef do fonte informado
    Local oModel   := FWLoadModel( 'DLP10F13' )
    // Cria a estrutura a ser usada na View
    Local oStruSZC := FWFormStruct( 2, 'SZC' )
    //Local oStruZA0 := FWFormStruct( 2, 'ZA0', { |cCampo| COMP11STRU(cCampo) } )
    Local oView
    Local cCampos := {}


    // Cria o objeto de View
    oView := FWFormView():New()

    // Define qual o Modelo de dados será utilizado
    oView:SetModel( oModel )

    //Adiciona no nosso View um controle do tipo FormFields(antiga enchoice)
    oView:AddField( 'VIEW_SZC', oStruSZC, 'SZCMASTER' )

    // Criar um "box" horizontal para receber algum elemento da view
    oView:CreateHorizontalBox( 'TELA' , 100 )

    // Relaciona o ID da View com o "box" para exibicao
    oView:SetOwnerView( 'VIEW_SZC', 'TELA' )

    //oView:SetViewAction( 'BUTTONOK'    , { |o| Help(,,'HELP',,'Ação de Confirmar ' + o:ClassName(),1,0) } )
    //oView:SetViewAction( 'BUTTONCANCEL', { |o| Help(,,'HELP',,'Ação de Cancelar '  + o:ClassName(),1,0) } )
Return oView


//-------------------------------------------------------------------
Static Function COMP011POS( oModel )
    Local nOperation := oModel:GetOperation()
    Local lRet       := .T.

    If nOperation == MODEL_OPERATION_UPDATE
        If Empty( oModel:GetValue( 'SZCMASTER', 'ZC_ANOMES' ) )
            Help( ,, 'HELP',, 'Informe a data', 1, 0)
            lRet := .F.
        EndIf
        If Empty( oModel:GetValue( 'SZCMASTER', 'ZC_EMP' ) )
            Help( ,, 'HELP',, 'Informe a data', 1, 0)
            lRet := .F.
        EndIf
        If Empty( oModel:GetValue( 'SZCMASTER', 'ZC_FIL' ) )
            Help( ,, 'HELP',, 'Informe a data', 1, 0)
            lRet := .F.
        EndIf
        If Empty( oModel:GetValue( 'SZCMASTER', 'ZC_ANOMES' ) )
            Help( ,, 'HELP',, 'Informe a data', 1, 0)
            lRet := .F.
        EndIf
        If Empty( oModel:GetValue( 'SZCMASTER', 'ZC_ORCFAT' ) )
            Help( ,, 'HELP',, 'Informe a data', 1, 0)
            lRet := .F.
        EndIf
    EndIf



Return lRet

//-------------------------------------------------------------------
Static Function COMP011ACT( oModel )  // Passa o model sem dados
    Local aArea      := GetArea()
    Local cQuery     := ''
    Local cTmp       := ''
    Local lRet       := .T.
    Local nOperation := oModel:GetOperation()

    If nOperation == MODEL_OPERATION_DELETE .AND. lRet

        cTmp    := GetNextAlias()

        cQuery  := ""
        cQuery  += "SELECT ZA0_CODIGO FROM " + RetSqlName( 'ZA0' ) + " ZA0 "
        cQuery  += " WHERE EXISTS ( "
        cQuery  += "       SELECT 1 FROM " + RetSqlName( 'ZA2' ) + " ZA2 "
        cQuery  += "        WHERE ZA2_AUTOR = ZA0_CODIGO"
        cQuery  += "          AND ZA2.D_E_L_E_T_ = ' ' ) "
        cQuery  += "   AND ZA0_CODIGO = '" + ZA0->ZA0_CODIGO  + "' "
        cQuery  += "   AND ZA0.D_E_L_E_T_ = ' ' "

        dbUseArea( .T., "TOPCONN", TcGenQry( ,, cQuery ) , cTmp, .F., .T. )

        lRet := (cTmp)->( EOF() )

        (cTmp)->( dbCloseArea() )

        If lRet
            cQuery  := ""
            cQuery  += "SELECT ZA0_CODIGO FROM " + RetSqlName( 'ZA0' ) + " ZA0 "
            cQuery  += " WHERE EXISTS ( "
            cQuery  += "       SELECT 1 FROM " + RetSqlName( 'ZA5' ) + " ZA5 "
            cQuery  += "        WHERE ZA5_INTER = ZA0_CODIGO"
            cQuery  += "          AND ZA5.D_E_L_E_T_ = ' ' ) "
            cQuery  += "   AND ZA0_CODIGO = '" + ZA0->ZA0_CODIGO  + "' "
            cQuery  += "   AND ZA0.D_E_L_E_T_ = ' ' "

            dbUseArea( .T., "TOPCONN", TcGenQry( ,, cQuery ) , cTmp, .F., .T. )

            lRet := (cTmp)->( EOF() )

            (cTmp)->( dbCloseArea() )

        EndIf

        If !lRet
            Help( ,, 'HELP',, 'Este Autor/interprete nao pode ser excluido.', 1, 0)
        EndIf

    EndIf

    RestArea( aArea )

Return lRet


//-------------------------------------------------------------------
Static Function COMP11STRU( cCampo )
    Local lRet := .T.

    If cCampo == 'ZA0_QTDMUS'
        lRet := .F.
    EndIf

Return lRet
