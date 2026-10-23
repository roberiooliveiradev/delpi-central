#INCLUDE 'Protheus.CH'
#INCLUDE 'fwMVCDEF.CH'
#include 'parmtype.ch'
#INCLUDE "FILEIO.CH"
#INCLUDE 'TOPCONN.CH'
#INCLUDE "TBICONN.CH"

User Function DLP10F08()
    Local oBrowse

    oBrowse:=FWMBrowse():New()
    //oBrowse:AddLegend( "ZA1_STATUS=='1'", "CARGA", "Ativo" )
    //oBrowse:AddLegend( "ZA1_STATUS=='2'", "EMPILHADEIRA" , "Inativo" )
    oBrowse:SetAlias("SZ6")
    oBrowse:SetDescription("Desc Operação")

    oBrowse:Activate()
RETURN

Static Function ModelDef()
    Local oModel
    Local oStrSZ6:= FWFormStruct(1,"SZ6")

    oModel:=MPFormModel():New("SZ6MASTER",,{||.T.})
    oModel:SetDescription("Castro de Operacoes") // setando a descrição do modelo

    oModel:addFields("MASTERSZ6",/*Caso tivesse um owner(pai)*/,oStrSZ6)
    oModel:SetPrimaryKey({"Z6_CODIGO"})

    //oStrSZ6:SetProperty('Z6_CODIGO'		    ,MODEL_FIELD_INIT,  {||  GetSxeNum("SZ6","Z6_CODIGO")	})
    oStrSZ6:SetProperty('Z6_CODIGO'		    ,MODEL_FIELD_INIT,  {||  fGetCod()	})
    oStrSZ6:SetProperty('Z6_CODIGO'		    ,MODEL_FIELD_WHEN,  {|| .f.})
    oModel:getModel("MASTERSZ6"):SetDescription("Operações") // setando a descrição do field MASTERZA1

return oModel //ModelDef sempre retorna o oModel(objeto de modelo)

Static Function MenuDef()
    Local aRotina := {}
    Local cUserId   := RetCodUsr()
    ADD OPTION aRotina TITLE "Pesquisar"  ACTION 'PesqBrw'       OPERATION 1 ACCESS 0
    ADD OPTION aRotina TITLE "Visualizar" ACTION "VIEWDEF.DLP10F08" OPERATION 2 ACCESS 0
    ADD OPTION aRotina TITLE "Incluir"    ACTION "VIEWDEF.DLP10F08" OPERATION 3 ACCESS 0
    ADD OPTION aRotina TITLE "Alterar"    ACTION "VIEWDEF.DLP10F08" OPERATION 4 ACCESS 0

    if cUserId $"000000_000000"
        ADD OPTION aRotina TITLE "Excluir"    ACTION "VIEWDEF.DLP10F08" OPERATION 5 ACCESS 0
    endif
    //   ADD OPTION aRotina TITLE "Imprimir"   ACTION "VIEWDEF.DLP10F08" OPERATION 8 ACCESS 0
    // ADD OPTION aRotina TITLE "***teste"   ACTION  'MsgAlert(ZA1->ZA1_NOME, "teste")' OPERATION 8 ACCESS 0
    ADD OPTION aRotina TITLE "Copiar"     ACTION "VIEWDEF.DLP10F08" OPERATION 9 ACCESS 0

return aRotina

Static Function ViewDef()
    Local oModel:=ModelDef()
    Local oView
    Local oStrSZ6:=FWFormStruct(2, "SZ6")

    oView:=FWFormView():New()
    oView:SetModel(oModel)

    oView:AddField("FORM_SZ6", oStrSZ6, "MASTERSZ6")

    oView:CreateHorizontalBox("BOX_FORM_SZ6", 100)
    oView:SetOwnerView("FORM_SZ6", "BOX_FORM_SZ6")
return oView



Static Function fGetCod()

    Local cRetCod := "001"

    lOCAL cEol := chr(10)
    If (Select("TSZ6") <> 0)

        dbSelectArea("TSZ6")
        dbCloseArea()

    Endif
    cSql := "SELECT  MAX(Z6_CODIGO) Z6_CODIGO  FROM  dbo." + retsqlname("SZ6") + " SZ6 (nolock) " + cEol
    cSql += "   WHERE  SZ6.D_E_L_E_T_ = ' ' " + cEol
    cSql += "    AND Z6_FILIAL = "+valtosql(xfilial("SZ6"))  + cEol
    // cSql += "    AND Z6_CODIGO NOT IN ('999')" + cEol

    TCQuery cSql NEW ALIAS "TSZ6"

    if  TSZ6->(!Eof())
        cRetCod := soma1(TSZ6->Z6_CODIGO,3)
    endif

return  cRetCod
