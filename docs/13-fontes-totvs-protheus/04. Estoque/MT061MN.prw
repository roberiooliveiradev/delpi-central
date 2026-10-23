

#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

User Function MT061MN()

	//aadd(aRotina,{"Filtro","U_DLPX061A()",0,3,0,Nil,Nil,Nil,Nil})  //Adiciona Botões
	aadd(aRotina,{"Filtro (F4)","U_DLPX061C()",0,3,0,Nil,Nil,Nil,Nil})  //Adiciona Botões
	aadd(aRotina,{"Limpa Filtro (F6)","U_DLPX061B()",0,3,0,Nil,Nil,Nil,Nil})  //Adiciona Botões
	aAdd(aRotina, { "Consulta" ,"U_DlpConPrd()"		, 0 , 2, 0, .F.} )

	//    SetKey( VK_F5 , { || U_DLPX061A() } )
	SetKey( VK_F6 , { || U_DLPX061B() } )
	SetKey( VK_F4 , { || U_DLPX061C() } )

Return

User Function DLPX061B()

	fCleanFlt()

RETURN

User Function DLPX061A()
	Local oGet1
	Local cFiltro := space(20)
	Local cSay1 := "Digite o Filtro desejado"
	Local oSay1
	Static oDlg

	DEFINE MSDIALOG oDlg TITLE "Filtro Produto x Fornecedor" FROM 000, 000  TO 150, 300 COLORS 0, 16777215 PIXEL STYLE DS_MODALFRAME
    /*Linha / coluna*/
	@036, 003 SAY oSay1 PROMPT cSay1 SIZE 055, 010 OF oDlg COLORS 0, 16777215 PIXEL

	@050, 003 MSGET oGet1 VAR cFiltro SIZE 081, 010 OF oDlg COLORS 0, 16777215 PIXEL;
		VALID fProcFil(alltrim(UPPER(cFiltro)),1)

	bCancel := { || fCleanFlt() ,oDlg:End() }
	//bOK     := { || (  FWMsgRun(, {||   fProcXML(cFolder)}, "WCT", cMsgRun) ,oDlg:End() )}
	bOK     := { || (  fProcFil(alltrim(UPPER(cFiltro)),0) ,oDlg:End() )}
	ACTIVATE MSDIALOG oDlg ON INIT EnchoiceBar(oDlg, bOk , bCancel) CENTERED
	// ACTIVATE MSDIALOG oDlg CENTERED

Return
static function fCleanFlt()

	oBrowse := FWmBrwActive()
	oBrowse:CleanFilter()
	oBrowse:SetFilterDefault("")
	//   oBrowse:CleanExFilter()
	//  oBrowse:ExecuteFilter(.t.)
	oBrowse:GoTop(.t.)
	oBrowse:Refresh()
Return

static function fProcFil(cFiltro,nOpc)
	default nOpc := 0
	lRet := .t.
	if !Empty(cFiltro)
		cCondicao :=  valtosql(cFiltro) +" $ alltrim(SA5->A5_FORNECE)  "
		cCondicao += ".or. "+valtosql(cFiltro) + "$ alltrim(SA5->A5_NOMEFOR) "
		cCondicao += ".or. "+valtosql(cFiltro) + "$ alltrim(SA5->A5_PRODUTO) "
		cCondicao += ".or. "+valtosql(cFiltro) + "$ alltrim(SA5->A5_NOMPROD) "
		cCondicao += ".or. "+valtosql(cFiltro) + "$ alltrim(SA5->A5_CODPRF)  "
		cCondicao += ".or. "+valtosql(cFiltro) + "$ alltrim(SA5->A5_CODPRCA)  "
		//Intercepta o FWMBrowse e executa o filtro
		oBrowse := FWmBrwActive()
		oBrowse:SetFilterDefault(cCondicao)
		oBrowse:Refresh()
		if nOpc ==1
			oModal:DeActivate()
		endif
	else
		FWAlertError("Gentileza Preencher com algum filtro", "Produto x Fornecedor")

		lRet := .f.
	endif
rETURN lRet


//aAdd(aRotina, { "Consulta" ,"A010Consul"		, 0 , 2, 0, .F.} )

//aAdd(aRotina, { "Consulta" ,"U_Dlp()"		, 0 , 2, 0, .F.} )
//
//return aRotina

USER Function DlpConPrd()
	Local aArea:= GetArea()

	dbSelectArea("SB1")
	SB1->(dbSetOrder(1))
	(dbseek(xFilial("SB1")+SA5->A5_PRODUTO))
	A010Consul()

	RestArea(aArea)
Return Nil



/*/{Protheus.doc} TelaApontamentodePerda
    (long_description)
    @type  Static Function
    @author user
    @since 24/08/2022
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
USER Function DLPX061C()

	// Local oModal as Object
	Local  oFont := TFont():New('Courier new',,-18,.T.)
	cFiltro := SPACE(20)
	//bOK     := { || (  FWMsgRun(, {||   fProcXML(cFolder)}, "WCT", cMsgRun) ,oDlg:End() )}
	bOK     := { || (  fProcFil(alltrim(UPPER(cFiltro)),0) ,oDlg:End() )}
	STATIC oModal as Object


	//B2_FILIAL + B2_LOCAL + B2_COD || Armazem + Produto
	//nQuantEstoque := Posicione("SB2",2,XFILIAL("SB2")+"01"+cProduto,"B2_QATU")

	oModal  := FWDialogModal():New()
	oModal:SetBackground(.F.)
	oModal:SetEscClose(.F.)
	// oModal:setTitle("Apontamento de Retrabalho OP - " + cOrdemProducao )
	oModal:setTitle("Produto X Fornecedor " )
	oModal:setSize(130, 240)
	oModal:createDialog()
	oModal:createFormBar()
	oModal:EnableFormBar( .T. )
	oModal:addCloseButton(nil, "Sair")
	// oModal:AddButton( 'Confirmar' , {|| fProcOdl(),oModal:DeActivate() }, 'Confirmar1', , .T., .F., .T., )	//"Ok"
	oModal:AddButton( 'Confirmar' , {|| iif(fProcFil(alltrim(UPPER(cFiltro)),0) ,oModal:DeActivate(), .f.) }, 'Confirmar1', , .T., .F., .T., )	//"Ok"
	oSay1:= TSay():New(20,20,{||'Digite o Filtro Desejado: '},oModal:getPanelMain(),,oFont,,,,.T.,CLR_BLACK,CLR_WHITE,200,50)
	@ 040,020 MSGET oGet1 VAR cFiltro SIZE 150,11 OF oModal:getPanelMain() PIXEL PICTURE GetSx3Cache("B1_COD","X3_PICTURE") ;
		VALID fProcFil(alltrim(UPPER(cFiltro)),1) // When .F.

	// oSay1:= TSay():New(45,20,{||'Quantidade Produzido: '},oModal:getPanelMain(),,oFont,,,,.T.,CLR_BLACK,CLR_WHITE,200,50)
	// @ 040,150 MSGET oGet1 VAR nGetQuantidaProduzido SIZE 55,11 OF oModal:getPanelMain() PIXEL PICTURE GetSx3Cache("H6_QTDPROD","X3_PICTURE") VALID  Positivo() .and. ValidaoGetApontamento("1")

	//oSay2:= TSay():New(60,20,{||'Quantidade de Perda:'},oModal:getPanelMain(),,oFont,,,,.T.,CLR_BLACK,CLR_WHITE,200,50)
	//@ 060,150 MSGET oGet2 VAR nGetQuantidaPerda  SIZE 55,11 OF oModal:getPanelMain() PIXEL PICTURE GetSx3Cache("H6_QTDPERD","X3_PICTURE")  VALID Positivo() .and. Naovazio() .and. ValidaoGetApontamento("2")

	//oSay3:= TSay():New(100,20,{||'Motivo:'},oModal:getPanelMain(),,oFont,,,,.T.,CLR_BLACK,CLR_WHITE,200,50)
	//oGet03  := TGet():New( 100,150,{|u| If(PCount()>0,cMotivoDaPerda:=u,cMotivoDaPerda)},oModal:getPanelMain(),080,017,'',{||Naovazio() .AND. ValidaoGetApontamento("3")},CLR_HBLUE,CLR_WHITE,oFont,,,.T.,"",,,.F.,.F.,,.F.,.F.,"CYO003","cMotivoDaPerda",,)
	//oGet04  := TGet():New( 100,20,{|u| If(PCount()>0,cDescDoMotivoPerda:=u,cDescDoMotivoPerda)},oModal:getPanelMain(),200,017,'',               ,CLR_HBLUE,CLR_WHITE,oFont,,,.T.,"",,,.F.,.F.,,.T.,.F.,"","cDescDoMotivoPerda",,)

	oModal:Activate()
Return
