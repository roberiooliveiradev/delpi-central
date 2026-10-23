
#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMBROWSE.CH"
#INCLUDE "FWMVCDEF.CH"

#INCLUDE "FWADAPTEREAI.CH"

//---------------------------------------------------------------------
/*/{Protheus.doc} MATA632()
Roteiro de Operações
@author Leonardo Quintania
@since 05/10/2012
@version 1.0
@return NIL
/*/
//---------------------------------------------------------------------
USER Function DLPM632()
    Local oBrowse := FWMBrowse():New()
    Private lBrowse := .T.
    Private aRotina		:= MenuDef()
    oBrowse:SetAttach(.T.)
    oBrowse:SetCacheView(.F.)
    oBrowse:SetAlias("SG2")
    oBrowse:SetDescription("ROTEIRO DE OPERACOES") //Roteiro de Operações
    oBrowse:SetCanSaveArea(.T.)
    oBrowse:SetChgAll(.F.)
    oBrowse:SetSeeAll(.F.)
    oBrowse:DisableDetails(.F.)
    //   oBrowse:SetMenuDef("MATA632")

    oBrowse:Activate()

Return NIL

//---------------------------------------------------------------------
/*/{Protheus.doc} ModelDef()
Definicao do Modelo
@author Leonardo Quintania
@since 05/10/2012
@version 1.0
@return oModel
/*/
//---------------------------------------------------------------------
Static Function ModelDef()
    //  Local oModel	    := FWLoadModel("MATA632")

Return FWLoadModel("MATA632")


//----------------------------------------------------------------------
/*/{Protheus.doc} ViewDef()
Definicao da View
@author Leonardo Quintania
@since 05/10/2012
@version 1.0
@return oView
/*/
//----------------------------------------------------------------------
Static Function ViewDef()
    //Local oView := FWLoadView("MATA632")

Return FWLoadView("MATA632")


Static Function MenuDef()

    Local aRotina 	:= {}
    Local nPos		:= 0
    Local aAtiv		:= {}
    Local aAnotac	:= {}
    Local aEntRelac	:= {}

    ADD OPTION aRotina TITLE  "Visualizar"    ACTION  "VIEWDEF.MATA632" OPERATION 2 ACCESS 0 // "Visualizar"
    ADD OPTION aRotina TITLE  "Incluir"       ACTION  "VIEWDEF.MATA632" OPERATION 3 ACCESS 0 // "Incluir"
    ADD OPTION aRotina TITLE  "Alterar"       ACTION  "VIEWDEF.MATA632" OPERATION 4 ACCESS 0 // "Alterar"
    ADD OPTION aRotina TITLE  "Excluir"       ACTION  "VIEWDEF.MATA632" OPERATION 5 ACCESS 0 // "Excluir"
    ADD OPTION aRotina TITLE  "Copiar"       ACTION   "VIEWDEF.MATA632" OPERATION 9 ACCESS 0 // "Copiar"

Return aRotina