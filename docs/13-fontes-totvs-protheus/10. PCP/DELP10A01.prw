#INCLUDE 'TOTVS.CH'
#Include "RWMAKE.CH"
#include 'fileio.ch'
#Include "TopConn.ch"

#DEFINE POS_CENARIO        01
#DEFINE POS_ITEM      02  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A NUMERO DA NOTA
#DEFINE POS_REFERENCIA    03 // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A SERIE  DA NOTA
#DEFINE POS_TIPDEM      04  // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A DATA DE DIGITAÇÃO
#DEFINE POS_DTENT    05 // POSIÇÃO  DA COLUNA NA ABA CTE REFERENTE A DATA DE EMISSÃO
#DEFINE POS_QUANT        06
#DEFINE POS_PEDCLI     07
#DEFINE POS_NOMEABV     08
#DEFINE POS_SEQITM       09
#DEFINE POS_PRIORI   10
#DEFINE POS_GRPENT       11
#DEFINE POS_NRENTRE          12
#DEFINE POS_ESTABE    13

//Constantes
#Define STR_PULA    Chr(13)+Chr(10)

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 13/01/2025
/*/
User Function DLP10A01()

	// rpcsetenv("01")

	Private cArquivo 	:= Space(200)
	Private cDiretorio := Space(200)
	Private bSelArq		:= {|| cArquivo:= cGetFile('Arquivo CSV (.csv) | *.CSV',OemToAnsi('Arquivos CSV'),,'',.T.,,.F.)}
	Private bSelDir		:= {|| cDiretorio:= fSelDir()}

	//Declaração de Variaveis Private dos Objetos
	SetPrvt("oDlg1","oSay1","oSay2","oSay3","oSay4","oSay5","oGet1","oGet2","oGet3","oGet4","oGet5","oBtn1","oBtn2","oBtn3","oBtn4")

	//Definicao do Dialog e todos os seus componentes.
	oDlg1      := MSDialog():New( 118,280,280,584,"Importação Pedidos APS",,,.F.,,,,,,.T.,,,.T. )

	oSay4      := TSay():New( 010,018,{||"Arquivo:"},oDlg1,,,.F.,.F.,.F.,.T.,CLR_BLACK,CLR_WHITE,032,008)
	oGet4      := TGet():New( 010,058,{|u| If(PCount()>0,cArquivo:=u,cArquivo)},oDlg1,050,008,'',{|| len(cArquivo) > 0 },CLR_BLACK,CLR_WHITE,,,,.T.,"",,,.F.,.F.,,.F.,.F.,"","",,)
	oBtn3      := TButton():New( 010,108,"...",oDlg1,bSelArq,10,10,,,,.T.,,"",,,,.F. )

	oSay5      := TSay():New( 030,018,{||"Diretório:"},oDlg1,,,.F.,.F.,.F.,.T.,CLR_BLACK,CLR_WHITE,032,008)
	oGet5      := TGet():New( 030,058,{|u| If(PCount()>0,cDiretorio:=u,cDiretorio)},oDlg1,050,008,'',{|| len(cDiretorio) > 0 },CLR_BLACK,CLR_WHITE,,,,.T.,"",,,.F.,.F.,,.F.,.F.,"","",,)
	oBtn4      := TButton():New( 030,108,"...",oDlg1,bSelDir,10,10,,,,.T.,,"",,,,.F. )

	oBtn1      := TButton():New( 050,081,"Confirmar",oDlg1,{|| Processa({ || lerCSV(),OemToAnsi('Lendo o Arquivo.')}, OemToAnsi('Aguarde...')),oDlg1:End()  },037,012,,,,.T.,,"",,,,.F. )
	oBtn2      := TButton():New( 050,036,"Fechar",oDlg1,{|| oDlg1:End()},037,012,,,,.T.,,"",,,,.F. )

	oDlg1:Activate(,,,.T.)

	// rpcclearenv()

Return

/*/{Protheus.doc} nomeStaticFunction
  (long_description)
  @type  Static Function
  @author Pedro Lindenberg
  @since 13/01/2025
/*/
Static Function lerCSV()
	local x1 := 0
	local cLinha  	:= ""
	local lPrim   	:= .T.
	Local aCampos 	:= {}
	Local aData  	:= {}
	Local nTotal		:= 0
	Local cCol1 		:= ""
	// Local oPrtXlsx:= Nil
	Local oExcel := Nil
	// Local oFileW := Nil
	Local cTit := "Pedidos_APS_"+DTOS(DATE())+FWTimeStamp(1)+""
	Local cNewArq := GetTempPath()+cTit+".rel"
	Local cArq3 := GetTempPath()+cTit+".xlsx"
	Local nRow    := 1 // Linha Atual
	Local nColMax := 13 //Quantidade de Colunas
	Local lRet := .T.
	Local nRow := 0
	PRIVATE nRotation      := 0
	Private cCLRWhite      := "ffffff" // branco
	Private cCLRGray       := "C0C0C0" // cinza
	Private cCLRGray1      := "d1d1d1" // cinza
	Private cCLRDelpi      := "003867" // azul
	Private cCLRBlk        := "0d0c0c" //preto
	Private oFileW := FwFileWriter():New(cNewArq)
	//Criando o objeto que irá gerar o conteúdo do Excel
	Private oPrtXlsx := FwPrinterXlsx():New() //FwPrinterXlsx()
	Private oCellHorAlign  := FwXlsxCellAlignment():Horizontal()
	Private oCellVertAlign := FwXlsxCellAlignment():Vertical()
	Private cHorAlignment  := oCellHorAlign:Center()
	Private cHorAlignLeft  := oCellHorAlign:Left()
	Private cVertAlignment := oCellVertAlign:Center()
	Private cStyleBord     := FwXlsxBorderStyle():Thin() // estilo da borda fino
	//parametros da planilha
	cFont       := FwPrinterFont():Calibri()
	nSize       := 12
	lItalic     := .t.
	lBold       := .T.
	lUnderlined := .f.

	if empty(cArquivo)
		msgStop("Arquivo não selecionado.")
		return
	endif

	//Alimenta Array com os dados a importar
	FT_FUSE(cArquivo)
	ProcRegua(FT_FLASTREC())
	FT_FGOTOP()
	While !FT_FEOF()

		cLinha := FT_FREADLN()

		If lPrim
			aCampos := Separa(cLinha,";",.T.)
			lPrim := .F.
		Else
			AADD(aData,Separa(cLinha,";",.T.))
		EndIf

		FT_FSKIP()

	EndDo

	lRet := oPrtXlsx:Activate(cNewArq, oFileW)

	nWidth := 15
	oPrtXlsx:SetColumnsWidth(1, nColMax, nWidth)

  /*Adiciona Aba no Excel*/
	oPrtXlsx:AddSheet("TOTVS APS")
	//seta a fonte da planilha
	lRet := oPrtXlsx:SetFont(cFont, nSize, lItalic, lBold, lUnderlined)

	//lRet := oPrtXlsx:MergeCells( nRow/*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, 5/*nColTo*/)
	oPrtXlsx:MergeCells( nRow/*nRowFrom*/, 1/*nColFrom*/,nRow /*nRowTo*/, nColMax/*nColTo*/)
	// Comando 'Formato de Célula' com cor de texto e fundo personalizada
	oPrtXlsx:SetCellsFormat(cHorAlignment, cVertAlignment, .t. /*lWrapText*/, nRotation, cCLRDelpi /*Cor do Texto*/,cCLRGray/*Cor de Fundo*/, "" )
	// define a borda da celula
	oPrtXlsx:SetBorder(.t./*lLeft*/, .t./*lTop*/, .t./*lRight*/, .t./*lBottom*/, cStyleBord, cCLRBlk)
	oPrtXlsx:SetText(nRow /*Linha*/, 1/*Coluna*/, "Layout planilha Excel de Importação pedidos e previsões APS")

	nRow++ // pula linha

	//setar o nome das colunas
	oPrtXlsx:SetText(nRow /*Linha*/, POS_CENARIO /*Coluna*/, "Cenário")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_ITEM /*Coluna*/, "Item")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_REFERENCIA /*Coluna*/, "Referência")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_TIPDEM /*Coluna*/, "Tipo Demanda")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_DTENT /*Coluna*/, "Data Entrega")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_QUANT /*Coluna*/, "Quantidade")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_PEDCLI /*Coluna*/, "Pedido Cliente")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_NOMEABV /*Coluna*/, "Nome Abreviado")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_SEQITM /*Coluna*/, "Seq Item Ped")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_PRIORI /*Coluna*/, "Prioridade")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_GRPENT /*Coluna*/, "Grupo Entrega")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_NRENTRE /*Coluna*/, "Nr Entrega")
	oPrtXlsx:SetText(nRow /*Linha*/, POS_ESTABE /*Coluna*/, "Estabelecimento")

	nRow++ // pula linha

	For x1 := 1 to 10//Len(aData)

		IF DateDiffDay(DATE(),cToD(aData[x1][6])) <= 7

			cCol1 := "001"

		ELSE

			cCol1 := "002"

		ENDIF

		IncProc("Montando lista de registros. Lendo linha "+cValToChar(nRow)+".")

		oPrtXlsx:SetText(nRow /*Linha*/, POS_CENARIO/*Coluna*/ , cCol1 )
		oPrtXlsx:SetText(nRow /*Linha*/, POS_ITEM/*Coluna*/ , aData[x1][3] )
		oPrtXlsx:SetText(nRow /*Linha*/, POS_REFERENCIA/*Coluna*/ , "" )
		oPrtXlsx:SetText(nRow /*Linha*/, POS_TIPDEM/*Coluna*/ , "2" )
		oPrtXlsx:SetText(nRow /*Linha*/, POS_DTENT/*Coluna*/ , aData[x1][6])
		oPrtXlsx:SetValue(nRow /*Linha*/, POS_QUANT/*Coluna*/ , ((GetDToVal(aData[x1][5])/1000)))
		oPrtXlsx:SetText(nRow /*Linha*/, POS_PEDCLI/*Coluna*/ , "")
		oPrtXlsx:SetText(nRow /*Linha*/, POS_NOMEABV/*Coluna*/ , "")
		oPrtXlsx:SetText(nRow /*Linha*/, POS_SEQITM/*Coluna*/ , "")
		oPrtXlsx:SetText(nRow /*Linha*/, POS_PRIORI/*Coluna*/ , "")
		oPrtXlsx:SetText(nRow /*Linha*/, POS_GRPENT/*Coluna*/ , "")
		oPrtXlsx:SetText(nRow /*Linha*/, POS_NRENTRE/*Coluna*/ , "")
		oPrtXlsx:SetText(nRow /*Linha*/, POS_ESTABE/*Coluna*/ , "")

		nRow++

	Next x1

	lRet := oPrtXlsx:ApplyAutoFilter(2/*nRowFrom*/,1 /*nColFrom*/,nRow-1/*nRowTo*/,nColMax/*nColTo*/)

	oPrtXlsx:DeActivate()

	lRet := oPrtXlsx:Activate(cNewArq)
	oPrtXlsx:toXlsx()

	//Ativando o arquivo e gerando o xml
	oExcel := MsExcel():New()             //Abre uma nova conexão com Excel
	oExcel:WorkBooks:Open(cArq3)     //Abre uma planilha
	oExcel:SetVisible(.T.)                 //Visualiza a planilha
	// oExcel:Destroy()

Return

Static Function fSelDir()
	Local aArea   := GetArea()
	Local cDirIni := GetTempPath()
	Local cTipArq := ""
	Local cTitulo := "Seleção de Pasta para Salvar arquivo"
	Local lSalvar := .F.
	Local cPasta  := ""

	//Se não estiver sendo executado via job
	If ! IsBlind()

		//Chama a função para buscar arquivos
		cPasta := tFileDialog(;
			cTipArq,;                  // Filtragem de tipos de arquivos que serão selecionados
		cTitulo,;                  // Título da Janela para seleção dos arquivos
		,;                         // Compatibilidade
		cDirIni,;                  // Diretório inicial da busca de arquivos
		lSalvar,;                  // Se for .T., será uma Save Dialog, senão será Open Dialog
		GETF_RETDIRECTORY;         // Se não passar parâmetro, irá pegar apenas 1 arquivo; Se for informado GETF_MULTISELECT será possível pegar mais de 1 arquivo; Se for informado GETF_RETDIRECTORY será possível selecionar o diretório
		)

		If Empty(cPasta)
			MsgInfo("Selecione um diretório", "Atenção")
		EndIf
	EndIf

	RestArea(aArea)

Return cPasta
