/*/{Protheus.doc} DLP02F03
TABELA COM FORMULAS
    Formacao de Preco Delpi
SetNoInsertLine
/*/

#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"


USER FUNCTION DLP02F03()
    Local aArea       := GetArea()
    Local cAliasCab   := "SZ7"

    Private cBox1 := "1PRD01"
    Private cBox2 := "2OPE01"
    Private  cBox3 := "3IMP01"
    Private  cDescPlan := ""
    Private lWhenTok := .f.
    oBrowse := FWMBrowse():New()

    // oBrowse:SetAttach(.T.)
    // oBrowse:SetCacheView(.F.)
    oBrowse:SetAlias(cAliasCab)
    oBrowse:SetDescription("Planilha Formacao de Preco")
    //oBrowse:SetCanSaveArea(.T.)
    //oBrowse:SetChgAll(.F.)
    //oBrowse:SetSeeAll(.F.)
    //oBrowse:DisableDetails(.F.)
    oBrowse:SetMenuDef("DLP02F03")
    oBrowse:AddLegend( "Z7_STACALC == 'I' ", "RED"		, " Inativo"	)
    oBrowse:AddLegend( "Z7_STACALC != 'I' ", "GREEN"		, "Ativo"	)
    oBrowse:Activate()

    RestArea(aArea)
RETURN

/*====================================*\
|| # Func:  MenuDef   MVC		    # ||
\*====================================*/
Static Function MenuDef()
    local aRotina := {}

    ADD OPTION aRotina TITLE 'Visualizar'     ACTION 'VIEWDEF.DLP02F03' OPERATION 2 ACCESS 0
    ADD OPTION aRotina TITLE 'Incluir'        ACTION 'VIEWDEF.DLP02F03' OPERATION 3 ACCESS 0
    ADD OPTION aRotina TITLE 'Alterar'        ACTION 'VIEWDEF.DLP02F03' OPERATION 4 ACCESS 0
    ADD OPTION aRotina TITLE 'Excluir'        ACTION 'VIEWDEF.DLP02F03' OPERATION 5 ACCESS 0
    ADD OPTION aRotina TITLE 'Copiar'         ACTION 'VIEWDEF.DLP02F03' OPERATION 9 ACCESS 0


Return aRotina


USer Function DF03TOK(nOpc, oModel)

    // Local oModel     := FWMODELACTIVE()
    // Local oView      := FWViewActive()
    Local oModelSZ7  := oModel:GetModel("SZ7MASTER")
    Local oModelSZ71 := oModel:GetModel("SZ7DETAIL01")
    Local oModelSZ72 := oModel:GetModel("SZ7DETAIL02")
    Local oModelSZ73 := oModel:GetModel("SZ7DETAIL03")
    // Local cDescPlan  := oModelSZ7:getvalue("Z7_DESCPLN")
    Local cID        := oModelSZ7:getvalue("Z7_ID")
    Local nTmLogAlt  := getsx3cache("Z7_LOGALT","X3_TAMANHO")
    Local cPisCof    := oModelSZ7:getvalue("Z7_PISCFMP")
    Local cICMS    := oModelSZ7:getvalue("Z7_ICMSMP")
    Local nFATMP    := oModelSZ7:getvalue("Z7_FATMP")
    Local cStaCalc    := oModelSZ7:getvalue("Z7_STACALC")
    // SZ7->Z7_PISCFMP
    // SZ7->Z7_ICMSMP
    Local nOperation := oModel:GetOperation()
    Local cLog       := ""
    Local n1         := 0
    Local n2         := 0
    Local n3         := 0
    //Private cBox1 := "1PRD01"
    //Private cBox2 := "2OPE01"
    //Private  cBox3 := "3IMP01"
    cLog:=padr( (retcodusr() +" - "+alltrim(UsrFullName())+" "+dtoc(date())+" "+time()),nTmLogAlt)
    lWhenTok := .t.

    if nOperation == MODEL_OPERATION_UPDATE  .or. nOperation == MODEL_OPERATION_INSERT

        IF    nOperation == MODEL_OPERATION_UPDATE
            lOper := .F.
        ELSEIF nOperation == MODEL_OPERATION_INSERT
            lOper := .T.
        ENDIF

        // OPER_COPIAR
        // lOper := iif()  /// tipo de operação para o reclock se for um update .f. se for insert .t.
        For n1 := 1 To oModelSZ71:Length()

            oModelSZ71:GoLine( n1 )


            IF    nOperation == MODEL_OPERATION_INSERT .AND. !oModelSZ71:IsDeleted(N1)
                RecLock("SZ7", lOper)
                SZ7->Z7_FILIAL  :=  xFilial("SZ7")
                SZ7->Z7_ID      :=  cID
                SZ7->Z7_ITEM    :=  oModelSZ71:Getvalue("Z7_ITEM"    )
                SZ7->Z7_DESCPLN :=  cDescPlan
                SZ7->Z7_LOGALT  :=  cLog
                SZ7->Z7_PISCFMP  :=  cPisCof
                SZ7->Z7_ICMSMP  :=  cICMS
                SZ7->Z7_FOLDER  :=  cBox1
                SZ7->Z7_FATMP  :=  nFATMP
                SZ7->Z7_STACALC  :=  cStaCalc
                // cStaCalc    := oModelSZ7:getvalue("Z7_STACALC")
                SZ7->Z7_CAMPO   :=  oModelSZ71:Getvalue("Z7_CAMPO "  )

                SZ7->Z7_DESCRG  :=  oModelSZ71:Getvalue("Z7_DESCRG"  )
                SZ7->Z7_DESCCMP :=  oModelSZ71:Getvalue("Z7_DESCCMP" )
                SZ7->Z7_FORMULA :=  oModelSZ71:Getvalue("Z7_FORMULA" )
                SZ7->Z7_TIPO    :=  oModelSZ71:Getvalue("Z7_TIPO"    )
                SZ7->Z7_VLRINI  :=  oModelSZ71:Getvalue("Z7_VLRINI"  )
                SZ7->(MsUnLock())

            elseif  nOperation == MODEL_OPERATION_UPDATE

                cChvSZ7 := cID+cBox1+ oModelSZ71:Getvalue("Z7_CAMPO "  )
                dbSelectArea("SZ7")
                SZ7->(dbSetOrder(2))

                If   SZ7->(dBSeek(xFilial("SZ7")+cChvSZ7))
                    RecLock("SZ7", lOper)

                    If  !oModelSZ71:IsDeleted(N1)
                        SZ7->Z7_PISCFMP  :=  cPisCof
                        SZ7->Z7_ICMSMP  :=  cICMS
                        SZ7->Z7_FATMP  :=  nFATMP
                        SZ7->Z7_STACALC  :=  cStaCalc
                        SZ7->Z7_DESCRG  :=  oModelSZ71:Getvalue("Z7_DESCRG"  )
                        SZ7->Z7_DESCCMP :=  oModelSZ71:Getvalue("Z7_DESCCMP" )
                        SZ7->Z7_FORMULA :=  oModelSZ71:Getvalue("Z7_FORMULA" )
                        SZ7->Z7_TIPO    :=  oModelSZ71:Getvalue("Z7_TIPO"    )
                        SZ7->Z7_VLRINI  :=  oModelSZ71:Getvalue("Z7_VLRINI"  )
                        SZ7->Z7_LOGALT  :=  cLog
                    ELSE
                        dbDelete()
                    ENDIF
                    SZ7->(MsUnLock())
                else
                    msgstop("Nao achou o Registro")
                endif
            endif


        NEXT n1

        For n2 := 1 To oModelSZ72:Length()

            oModelSZ72:GoLine( n2 )


            IF    nOperation == MODEL_OPERATION_INSERT .AND. !oModelSZ72:IsDeleted(n2)
                RecLock("SZ7", lOper)
                SZ7->Z7_FILIAL  :=  xFilial("SZ7")
                SZ7->Z7_ID      :=  cID
                SZ7->Z7_ITEM    :=  oModelSZ72:Getvalue("Z7_ITEM"    )
                SZ7->Z7_DESCPLN :=  cDescPlan
                SZ7->Z7_LOGALT  :=  cLog
                SZ7->Z7_FOLDER  :=  cBox3
                SZ7->Z7_PISCFMP  :=  cPisCof
                SZ7->Z7_ICMSMP  :=  cICMS
                SZ7->Z7_FATMP  :=  nFATMP
                SZ7->Z7_STACALC  :=  cStaCalc
                SZ7->Z7_DESCRG  :=  oModelSZ72:Getvalue("Z7_DESCRG"  )
                SZ7->Z7_CAMPO   :=  oModelSZ72:Getvalue("Z7_CAMPO "  )
                /*alter*/
                SZ7->Z7_DESCCMP :=  oModelSZ72:Getvalue("Z7_DESCCMP" )
                SZ7->Z7_FORMULA :=  oModelSZ72:Getvalue("Z7_FORMULA" )
                SZ7->Z7_TIPO    :=  oModelSZ72:Getvalue("Z7_TIPO"    )
                SZ7->Z7_VLRINI  :=  oModelSZ72:Getvalue("Z7_VLRINI"  )
                SZ7->(MsUnLock())
            elseif  nOperation == MODEL_OPERATION_UPDATE

                cChvSZ7 := cID+cBox3+ oModelSZ72:Getvalue("Z7_CAMPO "  )
                dbSelectArea("SZ7")
                SZ7->(dbSetOrder(2))

                If   SZ7->(dBSeek(xFilial("SZ7")+cChvSZ7))
                    RecLock("SZ7", lOper)
                    If  !oModelSZ72:IsDeleted(N2)
                        SZ7->Z7_DESCRG  :=  oModelSZ72:Getvalue("Z7_DESCRG"  )
                        SZ7->Z7_DESCCMP :=  oModelSZ72:Getvalue("Z7_DESCCMP" )
                        SZ7->Z7_FORMULA :=  oModelSZ72:Getvalue("Z7_FORMULA" )
                        SZ7->Z7_TIPO    :=  oModelSZ72:Getvalue("Z7_TIPO"    )
                        SZ7->Z7_VLRINI  :=  oModelSZ72:Getvalue("Z7_VLRINI"  )
                        SZ7->Z7_PISCFMP  :=  cPisCof
                        SZ7->Z7_ICMSMP  :=  cICMS
                        SZ7->Z7_FATMP  :=  nFATMP
                        SZ7->Z7_STACALC  :=  cStaCalc
                        SZ7->Z7_LOGALT  :=  cLog
                    ELSE
                        dbDelete()
                    ENDIF
                    SZ7->(MsUnLock())

                else
                    msgstop("Nao achou o Registro oModelSZ72")
                endif
            endif
            //  SZ7->Z7_FOLDER  :=  oModelSZ72:Getvalue("Z7_FOLDER"  )

        NEXT n2

        For n3 := 1 To oModelSZ73:Length()

            oModelSZ73:GoLine( n3 )

            IF    nOperation == MODEL_OPERATION_INSERT  .AND. !oModelSZ73:IsDeleted(n3)
                RecLock("SZ7", lOper)
                SZ7->Z7_FILIAL  :=  xFilial("SZ7")
                SZ7->Z7_ID      :=  cID
                SZ7->Z7_ITEM    :=  oModelSZ73:Getvalue("Z7_ITEM"    )
                SZ7->Z7_DESCPLN :=  cDescPlan
                SZ7->Z7_LOGALT  :=  cLog
                SZ7->Z7_FOLDER  :=  cBox2
                SZ7->Z7_DESCRG  :=  oModelSZ73:Getvalue("Z7_DESCRG"  )
                SZ7->Z7_CAMPO   :=  oModelSZ73:Getvalue("Z7_CAMPO "  )
                SZ7->Z7_PISCFMP  :=  cPisCof
                SZ7->Z7_ICMSMP  :=  cICMS
                SZ7->Z7_FATMP  :=  nFATMP
                SZ7->Z7_STACALC  :=  cStaCalc
                /*alter*/
                SZ7->Z7_DESCCMP :=  oModelSZ73:Getvalue("Z7_DESCCMP" )
                SZ7->Z7_FORMULA :=  oModelSZ73:Getvalue("Z7_FORMULA" )
                SZ7->Z7_TIPO    :=  oModelSZ73:Getvalue("Z7_TIPO"    )
                SZ7->Z7_VLRINI  :=  oModelSZ73:Getvalue("Z7_VLRINI"  )
                SZ7->(MsUnLock())
            elseif  nOperation == MODEL_OPERATION_UPDATE

                cChvSZ7 := cID+cBox2+ oModelSZ73:Getvalue("Z7_CAMPO "  )
                dbSelectArea("SZ7")
                SZ7->(dbSetOrder(2))

                If   SZ7->(dBSeek(xFilial("SZ7")+cChvSZ7))
                    RecLock("SZ7", lOper)
                    If  !oModelSZ73:IsDeleted(N3)
                        SZ7->Z7_PISCFMP  :=  cPisCof
                        SZ7->Z7_ICMSMP  :=  cICMS
                        SZ7->Z7_FATMP  :=  nFATMP
                        SZ7->Z7_STACALC  :=  cStaCalc
                        SZ7->Z7_DESCRG  :=  oModelSZ73:Getvalue("Z7_DESCRG"  )
                        SZ7->Z7_DESCCMP :=  oModelSZ73:Getvalue("Z7_DESCCMP" )
                        SZ7->Z7_FORMULA :=  oModelSZ73:Getvalue("Z7_FORMULA" )
                        SZ7->Z7_TIPO    :=  oModelSZ73:Getvalue("Z7_TIPO"    )
                        SZ7->Z7_VLRINI  :=  oModelSZ73:Getvalue("Z7_VLRINI"  )
                        SZ7->Z7_LOGALT  :=  cLog
                    ELSE
                        dbDelete()
                    ENDIF
                    SZ7->(MsUnLock())
                else
                    msgstop("Nao achou o Registro oModelSZ73")
                endif
            endif
            //  SZ7->Z7_FOLDER  :=  oModelSZ72:Getvalue("Z7_FOLDER"  )

        NEXT n3
        cSql1 := " UPDATE dbo.SZ7010 SET Z7_FATMP = "+valtosql(nFATMP)+" WHERE D_E_L_E_T_ ='' "
        cSql1 += "AND Z7_FILIAL = "+valtosql( xFilial("SZ7"))
        cSql1 += "AND Z7_ID = "+valtosql(cID)
        TCSQLExec(cSql1)
    elseif nOperation == MODEL_OPERATION_DELETE

        FWFormCommit(oModel )

    endif


Return .t.



/*====================================*\
|| # Func:  ModelDef   MVC		    # ||
\*====================================*/

Static Function ModelDef()
    Local oModel         := Nil
    Local oStSZ7	    := FWFormStruct(1, 'SZ7')
    Local oStSZ71	    := FWFormStruct(1, 'SZ7')
    Local oStSZ72	    := FWFormStruct(1, 'SZ7')
    Local oStSZ73	    := FWFormStruct(1, 'SZ7')

    //    oModel := MPFormModel():New('D02F02',/*bPreValidacao*/,  /*{|oModel| u_validtok(oModel)} /* bTudoOK*/ ,  {|oModel| U_DF02TOK( oModel:GetOperation(), oModel)})
    //oModel := MPFormModel():New('D02F03')
    oModel := MPFormModel():New('D02F03',/*bPreValidacao*/,  {|oModel| FVLDTOK(oModel)} /* bTudoOK*/ ,  {|oModel| U_DF03TOK( oModel:GetOperation(), oModel)} )
    oModel:AddFields( "SZ7MASTER", /*cOwner*/, oStSZ7,,,/*bLoad*/ )

    //oModel:SetPrimaryKey( {"Z7_FILIAL", "Z7_ID","Z7_FOLDER","Z7_ITEM","Z7_CAMPO","Z7_DESCCMP"} )
    oModel:SetPrimaryKey( {"Z7_FILIAL", "Z7_ID","Z7_DESCPLN"} )


    oModel:SetDescription("Delpi -Planilha Formacao de Preco")

    //oModel:AddGrid('ZA7DETAIL','ZA6MASTER',oStZA7,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    //oModel:SetRelation( "ZA7DETAIL", {	{"ZA7_FILIAL","xFilial('ZA7')"  },{"ZA7_IDZA6","ZA6_ID"}}, ZA7->( IndexKey( 2 ) ) )

    oModel:AddGrid('SZ7DETAIL01','SZ7MASTER',oStSZ71,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    oModel:SetRelation( "SZ7DETAIL01", {	{"Z7_FILIAL","xFilial('SZ7')"  },{"Z7_ID","Z7_ID"},{"Z7_DESCPLN","Z7_DESCPLN"}}, SZ7->( IndexKey( 1 ) ) )
    oModel:AddGrid('SZ7DETAIL02','SZ7MASTER',oStSZ72,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    oModel:SetRelation( "SZ7DETAIL02", {	{"Z7_FILIAL","xFilial('SZ7')"  },{"Z7_ID","Z7_ID"},{"Z7_DESCPLN","Z7_DESCPLN"}}, SZ7->( IndexKey( 1 ) ) )
    oModel:AddGrid('SZ7DETAIL03','SZ7MASTER',oStSZ73,/*bLinePre*/, /*bPosVld*/ ,/*bPre - Grid Inteiro*/,/*bPos - Grid Inteiro*/,/*bLoad - Carga do modelo manualmente*/)  //cOwner Ã© para quem pertence
    oModel:SetRelation( "SZ7DETAIL03", {	{"Z7_FILIAL","xFilial('SZ7')"  },{"Z7_ID","Z7_ID"},{"Z7_DESCPLN","Z7_DESCPLN"}}, SZ7->( IndexKey( 1 ) ) )

    oModel:GetModel( 'SZ7DETAIL01' ):SetUniqueLine( { 'Z7_FILIAL', 'Z7_ID','Z7_DESCPLN','Z7_ITEM','Z7_FOLDER','Z7_CAMPO' } )
    oModel:GetModel( 'SZ7DETAIL02' ):SetUniqueLine( { 'Z7_FILIAL', 'Z7_ID','Z7_DESCPLN','Z7_ITEM','Z7_FOLDER','Z7_CAMPO' } )
    oModel:GetModel( 'SZ7DETAIL03' ):SetUniqueLine( { 'Z7_FILIAL', 'Z7_ID','Z7_DESCPLN','Z7_ITEM','Z7_FOLDER','Z7_CAMPO' } )

    oModel:GetModel( 'SZ7DETAIL01' ):SetLoadFilter( , " Z7_FOLDER = '"+cBox1+"'" )
    oModel:GetModel( 'SZ7DETAIL02' ):SetLoadFilter( , " Z7_FOLDER = '"+cBox3+"'" )
    oModel:GetModel( 'SZ7DETAIL03' ):SetLoadFilter( , " Z7_FOLDER = '"+cBox2+"'" )
    //  oStSZ8:SetProperty('Z8_IDSZ7'		,MODEL_FIELD_VALID, {|| D02F02A({"Z8_IDSZ7","MODEL_FIELD_VALID"})	})
    //  oStSZ8:SetProperty('Z8_COD'		    ,MODEL_FIELD_VALID, {|| D02F02A({"Z8_COD","MODEL_FIELD_VALID"})	})
    //  //   oStSZ8:SetProperty('Z8_ID'		    ,MODEL_FIELD_INIT,  {|| D02F02A({"Z8_ID","MODEL_FIELD_INIT"})	})
    //  oStSZ8:SetProperty('Z8_ID'		    ,MODEL_FIELD_WHEN,  {|| .f.	})


    //oStruZA0:SetProperty( 'ZA0_QTDMUS' , MODEL_FIELD_WHEN,'INCLUI')
    //oStSZ7:SetProperty('Z7_DESCPLN'		,MODEL_FIELD_VALID, {|| D02F03A({"Z8_IDSZ7","MODEL_FIELD_VALID"})	})
    oStSZ7:SetProperty('Z7_DESCPLN'		,MODEL_FIELD_VALID, {|| D02F03A()	})
    oStSZ71:SetProperty('Z7_DESCPLN'		,MODEL_FIELD_VALID, {|| D02F03A()	})
    oStSZ72:SetProperty('Z7_DESCPLN'		,MODEL_FIELD_VALID, {|| D02F03A()	})
    oStSZ73:SetProperty('Z7_DESCPLN'		,MODEL_FIELD_VALID, {|| D02F03A()	})
    //Z7_DESCRG
    //Z7_DESCCMP
    //Z7_FORMULA
    oStSZ71:SetProperty('Z7_DESCRG'		,MODEL_FIELD_VALID, {|| D02F03B({"Z7_DESCRG",cBox1})	})
    oStSZ71:SetProperty('Z7_DESCCMP'		,MODEL_FIELD_VALID, {|| D02F03B({"Z7_DESCCMP",cBox1})	})
    oStSZ71:SetProperty('Z7_FORMULA'		,MODEL_FIELD_VALID, {|| D02F03B({"Z7_FORMULA",cBox1})	})

    oStSZ7:SetProperty('Z7_DESCPLN',MODEL_FIELD_WHEN,FWBuildFeature(STRUCT_FEATURE_WHEN," iif( ( EMPTY(FWFldGet('Z7_DESCPLN')) .AND. ALTERA) .OR. INCLUI .or. lWhenTok, .T.,.F.)"))
    oStSZ71:SetProperty('Z7_DESCCMP',MODEL_FIELD_WHEN,FWBuildFeature(STRUCT_FEATURE_WHEN,"iif( ( EMPTY(FWFldGet('Z7_DESCCMP')) .AND. ALTERA) .OR. INCLUI .or. lWhenTok, .T.,.F.)"))
    oStSZ72:SetProperty('Z7_DESCCMP',MODEL_FIELD_WHEN,FWBuildFeature(STRUCT_FEATURE_WHEN,"iif( ( EMPTY(FWFldGet('Z7_DESCCMP')) .AND. ALTERA) .OR. INCLUI .or. lWhenTok, .T.,.F.)"))
    oStSZ73:SetProperty('Z7_DESCCMP',MODEL_FIELD_WHEN,FWBuildFeature(STRUCT_FEATURE_WHEN,"iif( ( EMPTY(FWFldGet('Z7_DESCCMP')) .AND. ALTERA) .OR. INCLUI .or. lWhenTok, .T.,.F.)"))

    oModel:SetActivate( {|oModel| IniDados( oModel ) } )

Return oModel


/*---------------------------------------------------------------------*
| Func:  D02F02A                                                      |
| VALIDACOES GERAIS DE INICIALIZADOR E TRIGGER                        |
*---------------------------------------------------------------------*/

Static Function D02F03A()
    Local xRet   := .t.
    Local oModel := FWModelActive()
    Local oModelSZ7  := oModel:GetModel("SZ7MASTER")

    If oModel:isActive()
        cDescPlan :=  oModelSZ7:getvalue("Z7_DESCPLN")
        conout("teste")
    endif
    //Local nOperation := oModel:GetOperation()
    //Local oModelZA2 := oModel:GetModel( 'ZA2DETAIL' )
    //D02F02A //FUNCAO PARA PREENCHER OS CAMPOS
    /*if aPars[1] $"Z8_ID" .and. aPars[1] $ "MODEL_FIELD_INIT"

        //    xNum := GetSxeNum("SZ8","Z8_ID")
        //    ConfirmSx8()
        //    bInitDesc	:= FWBuildFeature( STRUCT_FEATURE_INIPAD, 'IIF(!INCLUI,Posicione("FKC",1, xFilial("FKC") + FKD->FKD_CODIGO,"FKC_DESC"),"")')
        //    //    oMdlSZ8:SetValue(  'Z8_ID', xNum )

    elseif  aPars[1] $"Z8_IDSZ7" .and. aPars[2] $ "MODEL_FIELD_VALID"
        xRet := .t.
    elseif  aPars[1] $"Z8_COD" .and. aPars[2] $ "MODEL_FIELD_VALID"

        If oModel:isActive()
            D02F02D()
        ENDIF

        xRet := .t.
    ENDIF*/

Return xRet
/*---------------------------------------------------------------------*
| Func:  ViewDef                                                      |
*---------------------------------------------------------------------*/

Static Function ViewDef()

    Local oView     := Nil
    Local oModel    := FWLoadModel('DLP02F03')
    Local oStSZ7	:= FWFormStruct(2, 'SZ7')
    Local oStSZ71	:= FWFormStruct(2, 'SZ7')
    Local oStSZ72	:= FWFormStruct(2, 'SZ7')
    Local oStSZ73	:= FWFormStruct(2, 'SZ7')

    //Criando a View
    oView := FWFormView():New()
    oView:SetModel(oModel)

    oView:AddField('Master_SZ7' , oStSZ7,'SZ7MASTER' )
    oView:AddGrid('Detail_SZ71' , oStSZ71,'SZ7DETAIL01')
    oView:AddGrid('Detail_SZ72' , oStSZ72,'SZ7DETAIL02')
    oView:AddGrid('Detail_SZ73' , oStSZ73,'SZ7DETAIL03')


    oView:CreateHorizontalBox( '01CAB', 15) //CABECALHO
    oView:CreateHorizontalBox( 'BOX01', 45)  //PRODUTOS
    oView:CreateHorizontalBox( 'BOX02', 40)  //IMPOSTO / IOPERACIONAL
    // Quebra em 2 "box" vertical para receber algum elemento da view
    oView:CreateVerticalBox( 'BOX02ESQ', 50, 'BOX02' )
    oView:CreateVerticalBox( 'BOX02DIR', 50, 'BOX02' )

    oView:SetOwnerView('Master_SZ7','01CAB')
    oView:SetOwnerView('Detail_SZ71','BOX01')
    oView:SetOwnerView('Detail_SZ72','BOX02ESQ')
    oView:SetOwnerView('Detail_SZ73','BOX02DIR')

    // oStSZ91:RemoveField( 'Z9_PERCENT' )  //VIEW E MODEL
    //oStSZ92:RemoveField( 'Z9_PERCENT' )  //VIEW E MODEL
    //oStSZ93:RemoveField( 'Z9_PERCENT' )  //VIEW E MODEL
    //oStSZ92:RemoveField( 'Z9_IDZ8' )  //VIEW E MODEL
    //oStSZ93:RemoveField( 'Z9_IDZ8' )  //VIEW E MODEL
    //oStSZ91:RemoveField( 'Z9_IDFLD' ) //VIEW E MODEL
    //oStSZ92:RemoveField( 'Z9_IDFLD' ) //VIEW E MODEL
    //oStSZ93:RemoveField( 'Z9_IDFLD' ) //VIEW E MODEL
    //oStSZ91:RemoveField( 'Z9_ALIQ' )  //VIEW E MODEL
    //oStSZ92:RemoveField( 'Z9_QUANT' ) //VIEW E MODEL
    //oStSZ93:RemoveField( 'Z9_QUANT' ) //VIEW E MODEL
    //oStSZ92:RemoveField( 'Z9_VUNIT' ) //VIEW E MODEL
    //oStSZ93:RemoveField( 'Z9_VUNIT' ) //VIEW E MODEL

    //oView:AddUserButton( 'Preenche dados', 'DADOS', {|oView| fPrcDados()} )

    /*REMOVE OS CAMPOS DO CABEÇALHO*/
    // oStSZ7:RemoveField( 'Z7_STACALC')
    oStSZ7:RemoveField( 'Z7_STAITEM')
    oStSZ7:RemoveField( 'Z7_FOLDER')
    oStSZ7:RemoveField( 'Z7_DESCRG')
    oStSZ7:RemoveField( 'Z7_CAMPO')
    oStSZ7:RemoveField( 'Z7_DESCCMP')
    oStSZ7:RemoveField( 'Z7_FORMULA')
    oStSZ7:RemoveField( 'Z7_LOGINC')
    oStSZ7:RemoveField( 'Z7_LOGALT')
    oStSZ7:RemoveField( 'Z7_TIPO')
    oStSZ7:RemoveField( 'Z7_VLRINI')

    oStSZ7:SetProperty("Z7_PISCFMP",MVC_VIEW_TITULO ,"Cons Pis/Cof MP?")
    oStSZ7:SetProperty("Z7_PISCFMP",MVC_VIEW_DESCR ,"Cons Pis/Cof MP?")

    oStSZ7:SetProperty("Z7_ICMSMP",MVC_VIEW_TITULO ,"Cons ICMS MP?")
    oStSZ7:SetProperty("Z7_ICMSMP",MVC_VIEW_DESCR  ,"Cons ICMS MP?")

    /*CAMPOS ESTRUTURA*/
    oStSZ71:RemoveField( 'Z7_ID')
    oStSZ71:RemoveField( 'Z7_STACALC')
    oStSZ71:RemoveField( 'Z7_STAITEM')
    oStSZ71:RemoveField( 'Z7_DESCPLN')
    oStSZ71:RemoveField( 'Z7_FOLDER')
    //oStSZ71:RemoveField( 'Z7_DESCRG')
    oStSZ71:RemoveField( 'Z7_LOGINC')
    oStSZ71:RemoveField( 'Z7_LOGALT')
    oStSZ71:RemoveField( 'Z7_TIPO')
    oStSZ71:RemoveField( 'Z7_VLRINI')
    oStSZ71:RemoveField( 'Z7_PISCFMP')
    oStSZ71:RemoveField( 'Z7_ICMSMP')
    oStSZ71:RemoveField( 'Z7_FATMP')

    nLargDesc := 200
    nLargTp := 60
    conout("gda - validar")
    oStSZ71:SetProperty("Z7_DESCRG",MVC_VIEW_WIDTH ,nLargDesc)
    oStSZ71:SetProperty("Z7_DESCCMP",MVC_VIEW_WIDTH ,nLargDesc)
    oStSZ71:SetProperty("Z7_FORMULA",MVC_VIEW_WIDTH ,nLargTp)
    oStSZ71:SetProperty("Z7_FORMULA",MVC_VIEW_TITULO ,"Tipo Produto")
    oStSZ71:SetProperty("Z7_FORMULA",MVC_VIEW_DESCR ,"Tipo Produto")

    /*MVC_VIEW_ORDEM C Ordem
    MVC_VIEW_TITULO C Titulo do campo
    MVC_VIEW_DESCR C Descrição do campo*/

    /*CAMPOS IMPOSTOS*/
    oStSZ72:RemoveField( 'Z7_ID')
    oStSZ72:RemoveField( 'Z7_STACALC')
    oStSZ72:RemoveField( 'Z7_STAITEM')
    oStSZ72:RemoveField( 'Z7_DESCPLN')
    oStSZ72:RemoveField( 'Z7_FOLDER')
    //oStSZ72:RemoveField( 'Z7_DESCRG')
    oStSZ72:RemoveField( 'Z7_LOGINC')
    oStSZ72:RemoveField( 'Z7_LOGALT')
    //  oStSZ72:RemoveField( 'Z7_TIPO')
    // oStSZ72:RemoveField( 'Z7_VLRINI')
    oStSZ72:RemoveField( 'Z7_FORMULA')
    oStSZ72:RemoveField( 'Z7_PISCFMP')
    oStSZ72:RemoveField( 'Z7_ICMSMP')
    oStSZ72:RemoveField( 'Z7_FATMP')

    /*CAMPOS OPERACIONAL*/
    oStSZ73:RemoveField( 'Z7_ID')
    oStSZ73:RemoveField( 'Z7_STACALC')
    oStSZ73:RemoveField( 'Z7_STAITEM')
    oStSZ73:RemoveField( 'Z7_DESCPLN')
    oStSZ73:RemoveField( 'Z7_FOLDER')
    oStSZ73:RemoveField( 'Z7_LOGINC')
    oStSZ73:RemoveField( 'Z7_LOGALT')
    //  oStSZ73:RemoveField( 'Z7_TIPO')
    // oStSZ73:RemoveField( 'Z7_VLRINI')
    oStSZ73:RemoveField( 'Z7_FORMULA')
    oStSZ73:RemoveField( 'Z7_PISCFMP')
    oStSZ73:RemoveField( 'Z7_ICMSMP')
    oStSZ73:RemoveField( 'Z7_FATMP')


    oStSZ72:SetProperty("Z7_CAMPO"  ,MVC_VIEW_ORDEM,'01')
    oStSZ72:SetProperty("Z7_TIPO"   ,MVC_VIEW_ORDEM,'02')
    oStSZ72:SetProperty("Z7_DESCCMP",MVC_VIEW_ORDEM,'03')
    oStSZ72:SetProperty("Z7_DESCRG" ,MVC_VIEW_ORDEM,'04')
    oStSZ72:SetProperty("Z7_VLRINI" ,MVC_VIEW_ORDEM,'05')

    oStSZ73:SetProperty("Z7_CAMPO"  ,MVC_VIEW_ORDEM,'01')
    oStSZ73:SetProperty("Z7_TIPO"   ,MVC_VIEW_ORDEM,'02')
    oStSZ73:SetProperty("Z7_DESCCMP",MVC_VIEW_ORDEM,'03')
    oStSZ73:SetProperty("Z7_DESCRG" ,MVC_VIEW_ORDEM,'04')
    oStSZ73:SetProperty("Z7_VLRINI" ,MVC_VIEW_ORDEM,'05')

    /*campos comum a todos*/
    nLargDesc := 150
    oStSZ72:SetProperty("Z7_DESCRG" ,MVC_VIEW_WIDTH ,nLargDesc)
    oStSZ73:SetProperty("Z7_DESCRG",MVC_VIEW_WIDTH ,nLargDesc)
    oStSZ72:SetProperty("Z7_DESCCMP",MVC_VIEW_WIDTH ,nLargDesc)
    oStSZ73:SetProperty("Z7_DESCCMP",MVC_VIEW_WIDTH ,nLargDesc)

    /*campo item*/
    oStSZ7:RemoveField( 'Z7_ITEM')
    oStSZ71:RemoveField( 'Z7_ITEM')
    oStSZ72:RemoveField( 'Z7_ITEM')
    oStSZ73:RemoveField( 'Z7_ITEM')


    /*    nLarg := 100
    oStSZ91:SetProperty("Z9_TOTAL",MVC_VIEW_WIDTH ,nLarg)
    oStSZ91:SetProperty("Z9_PRCLIQ",MVC_VIEW_WIDTH ,nLarg)
    oStSZ91:SetProperty("Z9_CDPROD",MVC_VIEW_WIDTH ,nLarg)
    */

    oView:EnableTitleView('Detail_SZ71','Estrutura')
    oView:EnableTitleView('Detail_SZ72','Mark-up Impostos')
    oView:EnableTitleView('Detail_SZ73','Mark-up Operacional')

    oView:AddIncrementField( 'SZ7DETAIL01', 'Z7_CAMPO' )
    oView:AddIncrementField( 'SZ7DETAIL02', 'Z7_CAMPO' )
    oView:AddIncrementField( 'SZ7DETAIL03', 'Z7_CAMPO' )
Return oView


sTAtIC FUNCTION D02F03B(aPars)
    local lRet := .t.

    conout("parada gabriel")

Return lREt


Static Function IniDados( oModel )
    Local lInclui		:= oModel:GetOperation() == MODEL_OPERATION_INSERT
    Local oView	     := FwViewActive()
    Local n1	     := 0
    //  Local oModelSZ7  := oModel:GetModel("SZ7MASTER")
    Local oModelSZ71 := oModel:GetModel("SZ7DETAIL01")
    Local aDados :={}

    aadd(aDados,{'ARMAZENA O VALOR (SOMATORIO) DO CUSTO DOS PRODUTO DO TIPO MP' , 'TOTAL DE MATERIA PRIMA' , 'MP'})
    aadd(aDados,{'ARMAZENA O VALOR (SOMATORIO) DO CUSTO DOS PRODUTO TIPO MOD' , 'TOTAL DE MAO DE OBRA' , 'MO'})
    aadd(aDados,{'ARMAZENA O VALOR DO BENEFICIAMENTO' , 'TOTAL DE BENEFICIAMENTO' , 'BE'})
    aadd(aDados,{'ARMAZENA O VALOR DOS GASTOS GERAIS' , 'TOTAL DE GASTOS GERAIS' , 'GG'})

    if lInclui
        IF oModelSZ71:Length() == 1

            oModelSZ71:ClearData(.T.)
            IF oView:ISACTIVE()
                oView:Refresh()
            ENDIF
            oModelSZ71:GOLINE(1)
            For n1 := 1 to Len(aDados)

                oModelSZ71:GOLINE(n1)
                oModelSZ71:LoadValue('Z7_DESCRG' ,padr(aDados[n1][1] ,getsx3cache('Z7_DESCRG' ,"X3_TAMANHO")))
                oModelSZ71:LoadValue('Z7_DESCCMP',padr(aDados[n1][2] ,getsx3cache('Z7_DESCCMP',"X3_TAMANHO")))
                oModelSZ71:LoadValue('Z7_FORMULA',padr(aDados[n1][3] ,getsx3cache('Z7_FORMULA',"X3_TAMANHO")))
                IF n1 !=  Len(aDados)
                    oModelSZ71:AddLine()
                ENDIF
            Next n1
        ENDIF
    ENDIF
    oModelSZ71:GOLINE(1)
    IF oView:ISACTIVE()
        oView:Refresh()
    ENDIF
Return



sTATIC FUNCTION FVLDTOK(oModel)

    Local lRet := .t.
    //Local oModelSZ71 := oModel:GetModel("SZ7DETAIL01")
    Local oModelSZ72 := oModel:GetModel("SZ7DETAIL02")
    Local oModelSZ73 := oModel:GetModel("SZ7DETAIL03")
    Local n2
    Local n3

    /*valido se o ultimo registro é coeficiente
    valido que coeficiente deve ser a ultima linha valida
    */
    /**/
    For n2 := 1 to oModelSZ72:Length()
        oModelSZ72:GOLINE(n2)
        if !oModelSZ72:IsDeleted()

            if (oModelSZ72:getvalue('Z7_TIPO') == '2' .and. n2 < oModelSZ72:Length()) .or.;
                    (oModelSZ72:getvalue('Z7_TIPO') != '2' .and. n2 == oModelSZ72:Length())
                lRet := .f.
                FWAlertError("Coeficiente deve Ser a ultima linha valida", "Atenção - Mark-up Impostos")

            endif

        endif
    Next n2

    IF lRet
        For n3 := 1 to oModelSZ73:Length()
            oModelSZ73:GOLINE(n3)
            if !oModelSZ73:IsDeleted()

                if (oModelSZ73:getvalue('Z7_TIPO') == '2' .and. n3 < oModelSZ73:Length()) .or.;
                        (oModelSZ73:getvalue('Z7_TIPO') != '2' .and. n3 == oModelSZ73:Length()  )
                    lRet := .f.
                    FWAlertError("Coeficiente deve Ser a ultima linha valida", "Atenção - Mark-up Operacional")

                endif

            endif
        Next n3
    endif

reTURN lRet
