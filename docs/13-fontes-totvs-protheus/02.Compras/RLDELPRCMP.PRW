#INCLUDE "PROTHEUS.CH"
#INCLUDE "REPORT.CH"
#INCLUDE "TOPCONN.ch"

/*
------------------------------------------------------------------------------------------------------------
Delpi
------------------------------------------------------------------------------------------------------------
Nome do Módulo............: Estoque/Compras
Nome das Tabelas Acessadas: SB1/SB2
Nome do Programa..........: DPRLPRCMP
Parâmetros de Entrada.....:
Parâmetros de Saída.......:
------------------------------------------------------------------------------------------------------------
Objetivo do Programa......: Relatorio de Produto MP - Quantidade x Ultimo Preço de Compra
------------------------------------------------------------------------------------------------------------
Histórico                                                        |    Data      |  Executado por   | Chamado
------------------------------------------------------------------------------------------------------------
- Criação                                                            15/07/2010    ROBERTA LIMA

------------------------------------------------------------------------------------------------------------
*/

User Function DPRLPRCMP()

  Local oReport
  Local TRepInUse := .T.

  If FindFunction("TRepInUse")
    If TRepInUse()
      // Interface de impressao
      DBSELECTAREA("SB2")
      oReport := ReportDef()
      oReport:PrintDialog()
    Else
      // Interface de impressao - relatório anterior ao modo personalizavel - quando houver
      DBSELECTAREA("SB2")
      oReport := ReportDef()
      oReport:PrintDialog()
    Endif
  EndIf

Return


/*
-----------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------
 Função ReportDef()
 Definicao do objeto do relatorio personalizavel e das secoes que serao
 utilizadas
-----------------------------------------------------------------------------------------------------------
*/

Static Function ReportDef()

  Local oReport
  Local oSection1										// Sessao
  Local cReport 	:= "DPRLVLR"     					// Nome para geracao do relatorio
  Local cTitulo 	:= "Relação de Qtde x Preço" 	// Titulo
  Local cDescri   := "Relação de Qtde x Preço"  // Descricao na tela de impressao
  Local oBreak    									// Totalizador

  Private aOrdem  := {}  								// Ordens de impressao
  Private cPERG := "DMPRC"							// Cria Grupo de Perguntas

  ValidPerg()
  Pergunte(cPERG,.F.)

  // TReport():New(cReport,cTitle,uParam,{|bAction},cDescription,lLandscape,uTotalText,lTotalInLine,;
  //               cPageTText,lPageTInLine,lTPageBreak,nColSpace)
  oReport := TReport():New(cReport,cTitulo,cPerg,{|oReport| PrintReport(oReport)},cDescri)

  oReport:SetLandscape()								// Orientacao da pagina
  //oReport:lParamPage := .T.						    // Imprime página de parametros

  aOrdem := {"Produto"}



  /*---------------------------------------------------------
| Define a secao Dados do relatorio					       |
  ----------------------------------------------------------*/

  // TRSection():New(oParent,cTitle,uTable,aOrder,lLoadCells,lLoadOrder,uTotalText,lTotalInLine, lHeaderPage,;
  //                 lHeaderBreak,lPageBreak,lLineBreak,nLeftMargin)
  oSection1 := TRSection():New(oReport,"Produtos",{"SB2","SB1"}, aOrdem)

  //TRCEll():New( oParent   , cName     , cAlias    , cTitle     , cPicture  , nSize     , lPixel   ,{|| bBlock };
  //               cAlign , lLineBreak , cHeaderAlign , lCellBreak,nColSpace,lAutoSize,nClrBack,nClrFore,lBold)
  TRCell():New( oSection1, "B2_COD"		, "SB2", "Cód.Prod."			,/*cPicture*/,10,/*lPixel*/,/*bBlock*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,3,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/,/*lBold*/	)
  TRCell():New( oSection1, "B1_DESC"	, "SB1", "Descrição " 		,/*cPicture*/,20,/*lPixel*/,/*bBlock*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,5,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/,/*lBold*/	)
  TRCell():New( oSection1, "B2_LOCAL"	, "SB2", "Local"					,/*cPicture*/,5,/*lPixel*/,/*bBlock*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/,/*lBold*/	)
  TRCell():New( oSection1, "B1_UCOM"	, "SB1", "Dt.Ult.Com."    ,/*cPicture*/,12,/*lPixel*/,/*bBlock*/,/*cAlign*/,/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/,/*lBold*/	)
  TRCell():New( oSection1, "B2_QATU"	, "SB2", "Qtd.Atu"				,/*cPicture*/,12,/*lPixel*/,/*bBlock*/,"LEFT",/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,3,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/,/*lBold*/	)
  TRCell():New( oSection1, "B1_UPRC"	, "SB1", "Ult.Preço.Comp.","@E 999,999,999.99",15,/*lPixel*/,/*bBlock*/,"LEFT",/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/,/*lBold*/	)
  TRCell():New( oSection1, "TOTAL"		, "SB2"	, "TOTAL"					,"@E 999,999,999.99",15,/*lPixel*/,,"LEFT",/*lLineBreak*/,/*cHeaderAlign*/,/*lCellBreak*/,,/*lAutoSize*/,/*nClrBack*/,/*nClrFore*/,/*lBold*/	)


  // TRBreak(): New(oParent,uBreak,uTitle,lTotalInLine,cName,lPageBreak)
  //oBreak := TRBreak():New(oSection1,oSection1:Cell("SALDO"),"Sub Total")

  // TRFunction(): New(oCell,cName,cFunction,oBreak,cTitle,cPicture,uFormula,lEndSection,lEndReport,lEndPage,;
  // 				     oParent, {|bCondition},lDisable,bCanPrint)
  //TRFunction():New(oSection1:Cell(""),NIL,"SUM",,"")
  //TRFunction():New(oSection1:Cell(""),NIL,"SUM",,"")

  //TRFunction():New(oSection1:Cell(""),NIL,"SUM",oBreak,"Total")
  // TRFunction():New(oSection1:Cell(""),NIL,"COUNT",oBreak )

Return oReport


/*
-----------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------
 Função PrintReport()
 Impressão de relatório R4
-----------------------------------------------------------------------------------------------------------
*/

Static Function PrintReport(oReport)

  Local oSection1 := oReport:Section(1)
  //Local oBreak   	:= oReport:Section(1):ABREAK[1]
  Local cPerg		:= "DMPRC"
  Local cOrdem  := "% B2_COD, B2_LOCAL %"
  Local cFiltro
  Local cPart
  local mv01 := ALLTRIM(MV_PAR01)
  local mv02 := ALLTRIM(MV_PAR02)
  local mv03 := ALLTRIM(MV_PAR03)
  local mv04 := ALLTRIM(MV_PAR04)

  Pergunte(cPerg,.F.)


  cPart  := "% SB1.B1_TIPO = 'MP' %"
  //#IFDEF TOP

  BEGIN REPORT QUERY oSection1

    BeginSql Alias "QRYSB2"

	SELECT SB2.B2_COD,SB2.B2_LOCAL,SB2.B2_QATU, SB1.B1_COD, SB1.B1_DESC, SB1.B1_UPRC, TOTAL = (B2_QATU *  B1_UPRC)
    FROM %table:SB2% SB2, %table:SB1% SB1
	 WHERE SB2.B2_FILIAL = %xfilial:SB2% AND
	 	   SB2.B2_COD BETWEEN %Exp:mv01% AND %Exp:mv02% AND
	 	   SB2.B2_LOCAL BETWEEN %Exp:mv03% AND %Exp:mv04% AND
	 	   SB1.B1_COD = SB2.B2_COD AND
	 	   SB2.%notDel% AND %exp:cPart%
	 ORDER BY %Exp:cOrdem%

    EndSql
  END REPORT QUERY oSection1


  //#ENDIF

  oSection1:Print()

Return

/*------------------------------------------------------------
| ValidPerg									                  |
-------------------------------------------------------------*/

Static Function ValidPerg
  _sAlias := Alias()
  dbSelectArea("SX1")
  dbSetOrder(1)
  cPerg := PADR(cPerg,LEN(SX1->X1_GRUPO))
  aRegs:={}
  // Grupo/Ordem/Pergunta                                                                                                /Variavel/Tipo/Tamanho/Decimal/Presel/GSC/Valid/Var01/Def01/Cnt01/Var02/Def02/Cnt02/Var03/Def03/Cnt03/Var04/Def04/Cnt04/Var05/Def05/Cnt05
  AADD(aRegs,{cPerg,"01","Produto De","Produto De ","Produto De "	,"mv_ch1","C",15,0,0,"G","","mv_par01","","","","","","","","","","","","","","","","","","","","","","","","","SB1","","","","",""})
  AADD(aRegs,{cPerg,"02","Produto Ate ","Produto De","Produto De  ","mv_ch2","C",15,0,0,"G","","mv_par02","","","","","","","","","","","","","","","","","","","","","","","","","SB1","","","","",""})
  AADD(aRegs,{cPerg,"03","Local De ","Local De","Local De"			,"mv_ch3","C",02,0,0,"G","","mv_par03","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})
  AADD(aRegs,{cPerg,"04","Local Ate ","Local Ate ","Local De"		,"mv_ch4","C",02,0,0,"G","","mv_par04","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""})

  For i:=1 to Len(aRegs)
    If !dbSeek(cPerg+aRegs[i,2])
      RecLock("SX1",.T.)
      For j:=1 to FCount()
        FieldPut(j,aRegs[i,j])
      Next
      MsUnlock()
      dbCommit()
    Endif
  Next
  dbSelectArea(_sAlias)
Return




