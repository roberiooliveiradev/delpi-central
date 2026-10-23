//Bibliotecas
#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"
#INCLUDE "TBICONN.CH"

/*/{Protheus.doc} User Function zVid0040
Função que realiza a leitura de um XLS convertendo ele para CSV para importar os dados (como se fosse um CSV)
@type  Function
@author Atilio
@since 01/09/2022
@obs Pessoal, essa função é um paliativo de exemplo, para ler um XLS transformando ele em CSV
    Caso você queira se aprofundar, ou ver uma classe que vai além, com opção de leitura e
    escrita, eu recomendo que você conheça a YExcel, que é um projeto excelente do Saulo Martins

    + Link para download: https://github.com/saulogm/advpl-excel/blob/master/src/YEXCEL.prw
    + Link de exemplo:    https://github.com/saulogm/advpl-excel/blob/master/exemplo/tstyexcel.prw
    + Documentação:       https://github.com/saulogm/advpl-excel
/*/

User Function DLP02F24()
	Local aArea     := FWGetArea()
	Local cDirIni   :=  GetTempPath(.t.,.f.)//"C:\Users\Gabriel\OneDrive\Totvs\Delpi\ImpExcel" //GetTempPath()
	Local cTipArq   := 'Arquivos Excel (*.xlsx) | Arquivos Excel 97-2003 (*.xls)'
	Local cTitulo   := 'XLSX|XLS'
	Local lSalvar   := .F.
	Local cArqSel   := ''
	Local n1 := 0

	Local cCodTab := Space(3)
	Local cDscCod := Space(getsx3cache("AIA_DESCRI","X3_TAMANHO"))
	Local cCodFor := Space(getsx3cache("A2_COD","X3_TAMANHO"))
	Local cLjFor := Space(getsx3cache("A2_LOJA","X3_TAMANHO"))
	Local cMasc :="Excel XLS|*.XLS|Excel XLSX|*.XLSX"
	PRIVATE cDscFor := Space(getsx3cache("A2_NOME","X3_TAMANHO"))
	PRIVATE  aPergs := {}

	//Se não estiver sendo executado via job
	If ! IsBlind()

		//Chama a função para buscar arquivos

		cArqSel := cGetFile(cMasc,; //Máscara
		cTitulo,; //Título
		1,; //Número da máscara
		,; //Diretório Inicial
		.T.,; //.F. == Abrir; .T. == Salvar
		GETF_LOCALHARD,; //Diretório full. Ex.: 'C:\TOTVS\arquivo.docx'
		.F.) //Não exibe diretório do servidor

		//  cArqSel := tFileDialog(;
			//      cTipArq,;  // Filtragem de tipos de arquivos que serão selecionados
		//      cTitulo,;  // Título da Janela para seleção dos arquivos
		//      ,;         // Compatibilidade
		//      cDirIni,;  // Diretório inicial da busca de arquivos
		//      lSalvar,;  // Se for .T., será uma Save Dialog, senão será Open Dialog
		//      ;          // Se não passar parâmetro, irá pegar apenas 1 arquivo; Se for informado GETF_MULTISELECT será possível pegar mais de 1 arquivo; Se for informado GETF_RETDIRECTORY será possível selecionar o diretório
		//      )

		if Empty(cArqSel)

			FWAlertError("Nenhum arquivo Selecionado. Gentileza escolher um arquivo", "Delpi")
		else
			//   nTmArq := Len(aFileTXT)
			//   For n1 := 1 to Len(aFileTXT)
			nPosArq := n1
			nPosDir := RAt("\",cArqSel)
			cFolder := SUBSTR(cArqSel,1,nPosDir-1) // folder
			cArq  := SUBSTR(cArqSel,nPosDir+1) // Arquivo

			//aAdd(aPergs, {2, "Tipo Importação",               nTipo, {"1=Pré Nota",              "2=Classificação em Documento de Entrada"},     122, ".T.", .F.})

			//Box de Perguntas
			aAdd(aPergs, {2, "Tabela de Preço Existe?","2",;
				{"1=Sim","2=Não"},122, ".T.", .F.})
			aAdd(aPergs,{01,"Fornecedor" ,cCodFor 	,"","Vazio().Or.ExistCpo('SA2',MV_PAR02) ","SA2"	,"", 60,.t.})	// MV_PAR01
			aAdd(aPergs,{01,"Loja" ,cLjFor 	,"","U_D02F24A('3')",""	,"", 30,.t.})	// MV_PAR01
			aAdd( aPergs ,{01,"Desc For",cDscFor,"",".T.",""	,".F.", 80,.f.})

			aAdd(aPergs, {1, "Codigo Tabela" ,cCodTab,getsx3cache("AIA_CODTAB","X3_PICTURE" ),;
				"U_D02F24A('5')", "AIA", "U_D02F24A('1')", 40,  .F.})
			aAdd(aPergs, {1, "Desc Tabela" ,cDscCod,getsx3cache("AIA_DESCRI","X3_PICTURE" ),;
				'', "", "U_D02F24A('2')", 120,  .F.})
			aRetBox := ARRAY(LEN(aPergs))

			If ParamBox(aPergs, "Informe os parâmetros",@aRetBox)

				//GUARDA AS OPCOES ESCOLHIDAS
				lInc := iif(MV_PAR01=="2",.T.,.F.)
				cCodTab  := MV_PAR05
				cDscCod  := MV_PAR06
				FwMsgRun(NIL, {|| fImpExc(cArq,cFolder)}, "Delpi", "Processando")
			endif


		Endif

	EndIf

	FWRestArea(aArea)
Return
/*/{Protheus.doc} fVldPerg
@Description
@Type
@Author 	 TSC - Gabriel Araujo
@Since  	 14/01/2026
/*/
USER Function D02F24A(cOpc)
	Local lRet := .f. // iif(MV_PAR01=="1",.T.,.F.)
	lOCAL cCodF :=""
	lOCAL cLjF :=""

	if cOpc =='1'
		lRet :=  iif(MV_PAR01=="1",.T.,.F.)
	elseif cOpc =='2'
		lRet :=  iif(MV_PAR01=="1",.F.,.T.)
	elseif cOpc =='3'
		cCodF := MV_PAR02
		cLjF  := MV_PAR03
		if Empty(cLjF) .or. ExistCpo('SA2', cCodF+cLjF)
			dbSelectArea("SA2")
			SA2->(DbSetOrder(1))

			if  SA2->(DbSeek(xFilial("SA2")+cCodF+cLjF ))

				lRet := .t.
				cDscFor := SA2->A2_NOME
				aPergs[4][3] :=  SA2->A2_NOME
				MV_PAR04:=  alltrim(SA2->A2_NOME)
			endif
		endif
	elseif cOpc == '5'
		// Valida se AIA existe para fornecedor+loja+codigo informados
		If Empty(AllTrim(MV_PAR05))
			lRet := .T.
		Else
			dbSelectArea("AIA")
			AIA->(dbSetOrder(1))
			lRet := AIA->(dbSeek(xFilial("AIA") + PadR(MV_PAR02, TamSX3("AIA_CODFOR")[1]) + PadR(MV_PAR03, TamSX3("AIA_LOJFOR")[1]) + PadR(MV_PAR05, TamSX3("AIA_CODTAB")[1])))
		EndIf
	endif

	conout("stop")
Return lRet
static function fImpExc(cArq,cFolder)
	Local cFullFile := cFolder+"\"+cArq
	Local aTamLin
	Local nCont,nCont2
	Local xValor
	Local oExcel	:= YExcel():new(,cFullFile)
	Local nOpc := 4
	Local nPCPN := 0'
	Local nPMat := 0 //Material
	Local nPPrc := 0 //Gross Prc
	Local aProd := {}
	Local aProdImp := {}
	Local aItem := {}
	Local aItens := {}
	Local aLog := {}
	lOCAL cOpcPar :=""
	local cItem :=  StrZero(1,TamSx3("AIB_ITEM")[1])
	lOCAL lInc := .F.
	lOCAL cMaxIt :=fGetIt()
	PRIVATE lMsErroAuto := .F.
	//  oExcel:Pos(1,1):SetValue(oExcel:GetValue(1,1)+" - editado")
	aTamLin	:= oExcel:LinTam()
	//aTamLin[1]:=2
	//aTamLin[2]:=184
	If ValType(MV_PAR01)=="N"
		cOpcPar := cvaltochar(MV_PAR01)
	ELSE
		cOpcPar :=MV_PAR01
	ENDIF
	IF cOpcPar=="2"
		lInc := .T.
		nOpc := 3
	ENDIF
	For nCont:=aTamLin[1] to aTamLin[2]
		if nCont ==1
			aTamCol	:= oExcel:ColTam(nCont)
			If aTamCol[1]>0

				For nCont2:=aTamCol[1] to aTamCol[2]
					xValor	:=upper(alltrim( oExcel:GetValue(nCont,nCont2)))

					if xValor == "MATERIAL"
						nPMat := nCont2
					ENDIF

					if xValor == "CPN"
						nPCPN := nCont2
					ENDIF

					if xValor == "GROSS PRC"
						nPPrc := nCont2
					ENDIF
					// xValor	:= oExcel:GetValue(nCont,nCont2)
					// If ValType(xValor)=="O"
					//     VarInfo(oExcel:Ref(nCont,nCont2),xValor,,.F.)
					// Else
					//     ConOut(oExcel:Ref(nCont,nCont2)+"["+cValToChar(xValor)+"]")
					// EndIf
				Next nCont2
			EndIf
		ELSE
			xValor :=oExcel:GetValue(nCont,nPCPN)
			If ValType(xValor)=="N"
				cProd := padr(alltrim(cValtoChar(xValor)),getsx3cache("B1_COD","X3_TAMANHO"))
			ELSEIf ValType(xValor)=="C"
				cProd := padr(alltrim(xValor),getsx3cache("B1_COD","X3_TAMANHO"))
			endif

			xValor :=oExcel:GetValue(nCont,nPMat)
			If ValType(xValor)=="N"
				cMat := padr(alltrim(cValtoChar(xValor)),getsx3cache("B1_REFEREN","X3_TAMANHO"))
			ELSEIf ValType(xValor)=="C"
				cMat := padr(alltrim(xValor),getsx3cache("B1_REFEREN","X3_TAMANHO"))
			endif

			DBSELECTAREA("SB1")
			IF !EMPTY(cProd)
				SB1->(dbSetOrder(1))
				SB1->(DbSeek(xFilial('SB1')+cProd))
			ELSEIF !EMPTY(cMat)
				SB1->(dbSetOrder(18))
				SB1->(DbSeek(xFilial('SB1')+cMat))
			ENDIF
			nPrc := 0
			If	SB1->(Found())

				cProd := SB1->B1_COD
				cNomeProd:= SB1->B1_DESC
				xValor := oExcel:GetValue(nCont,nPPrc)
				If ValType(xValor)=="C"
					xValor := Replace(xValor,",",".")
					nPrc := VAL(xValor)
				ELSE
					nPrc := xValor
				ENDIF

				If nPrc <= 0
					Alert("Preço inválido para o produto "+cProd+" na linha "+cValToChar(nCont)+". Verifique o arquivo e tente novamente.")
					Return
				EndIf

				//CASO SEJA UMA NOVA TABELA BASTA FORMAR O ARRAY CONFORME PLANILHA
				IF lInc
					aItem :={}
					aadd(aItem,{"AIB_ITEM"  ,cItem      ,NIL})
					aAdd(aItem,{'AIB_CODPRO',cProd      ,NIL})
					aAdd(aItem,{'AIB_DESCRI',cNomeProd  ,NIL})
					aAdd(aItem,{'AIB_PRCCOM',nPrc         ,NIL})
					aAdd(aItem,{'AIB_DATVIG',dDataBase  ,NIL})
					//CONTROLE PARA NAO EXIBIR ITENS REPETIDOS
					IF ascan(aProd, cProd) ==0
						aAdd(aItens,aItem)
						cItem:=Soma1(cItem)
						aadd(aProd,cProd)
						aAdd(aProdImp, {cProd, nPrc})
					ELSE
						aadd(aLog,cProd+"/ Codigo Duplicado")
					ENDIF



				ELSE
					cFornec := MV_PAR02
					cLoja   := MV_PAR03
					cCodTab   := MV_PAR05
					DBSELECTAREA("AIB")
					AIB->(dbSetOrder(2))
					AIB->(DbSeek(xFilial('AIB')+cFornec+cLoja+cCodTab+cProd))

					If	AIB->(Found())
						//AIB_FILIAL, AIB_CODFOR, AIB_LOJFOR, AIB_CODTAB, AIB_ITEM, R_E_C_N_O_, D_E_L_E_T_
						aItem:={}
						aAdd(aItem,{"LINPOS","AIB_ITEM" ,AIB->AIB_ITEM})
						aAdd(aItem,{"AUTDELETA","N" ,Nil})

						aAdd(aItem,{'AIB_CODPRO',cProd,NIL})
						aAdd(aItem,{'AIB_DESCRI',cNomeProd,NIL})
						aAdd(aItem,{'AIB_DATVIG',dDataBase,NIL})
						aAdd(aItem,{'AIB_PRCCOM',nPrc,NIL})

						aAdd(aItens,aItem)
						aadd(aProd,cProd)
						aAdd(aProdImp, {cProd, nPrc})
					ELSE
						aItem:={}
						cMaxIt := soma1(cMaxIt)

						// aAdd(aItem,{"LINPOS","AIB_ITEM" ,cMaxIt})
						// aAdd(aItem,{"AUTDELETA","N" ,Nil})
						aAdd(aItem,{'AIB_ITEM',cMaxIt,NIL})
						aAdd(aItem,{'AIB_CODPRO',cProd,NIL})
						aAdd(aItem,{'AIB_DESCRI',cNomeProd,NIL})
						aAdd(aItem,{'AIB_DATVIG',dDataBase,NIL})
						aAdd(aItem,{'AIB_PRCCOM',nPrc,NIL})

						IF ascan(aProd, cProd) ==0
							aAdd(aItens,aItem)
							aadd(aProd,cProd)
							aAdd(aProdImp, {cProd, nPrc})
						ELSE
							aadd(aLog,cProd+"/ Codigo Duplicado")
						ENDIF

					ENDIF

				ENDIF

			ELSE
				aadd(aLog,cProd+"Não Encontrado")
			EndIf

		EndIf
	Next nCont
	aCab:= fGetCab()
	if len(aItens)>0
		MSExecAuto({|x,y,z| coma010(x,y,z)},nOpc,aCab,aItens)
		if  lMsErroAuto
			MostraErro()
		endif
		// -- Ticket 00009665: Atualizacao de precos em pedidos de compra em aberto
		If !lMsErroAuto .And. Len(aProdImp) > 0
			If MsgYesNo("Deseja atualizar precos nos pedidos de compra em aberto?", "Delpi")
				fAtuPedidos(MV_PAR02, MV_PAR03, MV_PAR05, aProdImp)
			EndIf
		EndIf
	endif


Return


static function fGetCab()
	Local aRetCab := {}
	Local cFornec := MV_PAR02
	Local cLoja   := MV_PAR03
	Local cCodTab := iif(empty(MV_PAR05),"001",MV_PAR05)
	lOCAL cDesc := padr(MV_PAR03,getsx3cache("AIB_DESCRI","X3_TAMANHO"))

	aRetCab := {}
	aadd(aRetCab,{"AIA_CODFOR",cFornec,NIL})
	aadd(aRetCab,{"AIA_LOJFOR",cLoja,NIL})
	aadd(aRetCab,{"AIA_CODTAB",cCodTab,NIL})
	aadd(aRetCab,{"AIA_DESCRI","TABELA DE PRECO BRASIL",NIL})
	aadd(aRetCab,{"AIA_DATDE",DDATABASE,NIL})
	aadd(aRetCab,{"AIA_DATATE",STOD("20491231"),NIL})



Return aRetCab

/*/{Protheus.doc} fGetIt
@Description
@Type
@Author 	 TSC - Gabriel Araujo
@Since  	 16/01/2026
/*/
Static Function fGetIt()
	lOCAL cEol := CHR(10)
	lOCAL cSql :=" "

	cSql +="SELECT ISNULL(MAX(AIB_ITEM),'0000') AIB_ITEM "  +cEol
	cSql +="    FROM  dbo."+ RetSqlName("AIB") + "  (NOLOCK) AIB "  +cEol
	cSql +="WHERE AIB.D_E_L_E_T_   = '' "  +cEol
	cSql +="    AND AIB.AIB_CODFOR = "+valtosql(MV_PAR02)+cEol
	cSql +="    AND AIB.AIB_LOJFOR = "+valtosql(MV_PAR03)+cEol
	cSql +="    AND AIB.AIB_CODTAB = "+valtosql(MV_PAR05)+cEol

	If Select('TMPQRY') <> 0
		TMPQRY->(dbCloseArea())
	Endif
	TCQuery cSql Alias TMPQRY New
	cNum := TMPQRY->AIB_ITEM
Return cNum
/*/{Protheus.doc} fImporta
Função que processa o arquivo e realiza a importação para o sistema
@author Daniel Atilio
@since 16/07/2022
@version 1.0
@type function
@obs Codigo gerado automaticamente pelo Autumn Code Maker
@see http://autumncodemaker.com
/*/

Static Function fImporta(cArqSel)
	Local cDirTmp    := GetTempPath()
	Local cArqLog    := 'importacao_' + dToS(Date()) + '_' + StrTran(Time(), ':', '-') + '.log'
	Local nTotLinhas := 0
	Local cLinAtu    := ''
	Local nLinhaAtu  := 0
	Local aLinha     := {}
	Local oArquivo
	Local cPastaErro := '\x_logs\'
	Local cNomeErro  := ''
	Local cTextoErro := ''
	Local aLogErro   := {}
	Local nLinhaErro := 0
	Local cLog       := ''
	Local nPCod      := 0
	Local nPPrc01    :=  0
	Local nPPrc02    := 0
	//Variáveis do ExecAuto
	Private aDados         := {}
	Private lMSHelpAuto    := .T.
	Private lAutoErrNoFile := .T.
	Private lMsErroAuto    := .F.
	//Variáveis da Importação
	Private cAliasImp  := 'SBM'
	Private cSeparador := ','
	//Item Delpi	Código Tramar	Descrição 	Preço Net (R$)	Preço EXW (Na Tramar) 	PrcFl01	Preço EXW (Na Tramar)	PrcFl02

	//Abre as tabelas que serão usadas
	DbSelectArea(cAliasImp)
	(cAliasImp)->(DbSetOrder(1))
	(cAliasImp)->(DbGoTop())

	//Definindo o arquivo a ser lido
	oArquivo := FWFileReader():New(cArqSel)

	//Se o arquivo pode ser aberto
	If (oArquivo:Open())

		//Se não for fim do arquivo
		If ! (oArquivo:EoF())

			//Definindo o tamanho da régua
			aLinhas := oArquivo:GetAllLines()
			nTotLinhas := Len(aLinhas)
			ProcRegua(nTotLinhas)

			//Método GoTop não funciona (dependendo da versão da LIB), deve fechar e abrir novamente o arquivo
			oArquivo:Close()
			oArquivo := FWFileReader():New(cArqSel)
			oArquivo:Open()

			//Iniciando controle de transação
			Begin Transaction

				//Enquanto tiver linhas
				While (oArquivo:HasLine())

					//Incrementa na tela a mensagem
					nLinhaAtu++
					IncProc('Analisando linha ' + cValToChar(nLinhaAtu) + ' de ' + cValToChar(nTotLinhas) + '...')

					//Pegando a linha atual e transformando em array
					cLinAtu := oArquivo:GetLine()
					aLinha  := Separa(cLinAtu, cSeparador)

					//Se houver posições no array
					If Len(aLinha) > 0




						//Se houve erro, gera o log
						If lMsErroAuto
							cPastaErro := '\x_logs\'
							cNomeErro  := 'erro_' + cAliasImp + '_' + dToS(Date()) + '_' + StrTran(Time(), ':', '-') + '.txt'

							//Se a pasta de erro não existir, cria ela
							If ! ExistDir(cPastaErro)
								MakeDir(cPastaErro)
							EndIf

							//Pegando log do ExecAuto, percorrendo e incrementando o texto
							aLogErro := GetAutoGRLog()
							For nLinhaErro := 1 To Len(aLogErro)
								cTextoErro += aLogErro[nLinhaErro] + CRLF
							Next

							//Criando o arquivo txt e incrementa o log
							MemoWrite(cPastaErro + cNomeErro, cTextoErro)
							cLog += '- Falha ao incluir registro, linha [' + cValToChar(nLinhaAtu) + '], arquivo de log em ' + cPastaErro + cNomeErro + CRLF
						Else
							cLog += '+ Sucesso no Execauto na linha ' + cValToChar(nLinhaAtu) + ';' + CRLF
						EndIf

					EndIf

				EndDo
			End Transaction

			//Se tiver log, mostra ele
			If ! Empty(cLog)
				MemoWrite(cDirTmp + cArqLog, cLog)
				ShellExecute('OPEN', cArqLog, '', cDirTmp, 1)
			EndIf

		Else
			MsgStop('Arquivo não tem conteúdo!', 'Atenção')
		EndIf

		//Fecha o arquivo
		oArquivo:Close()
	Else
		MsgStop('Arquivo não pode ser aberto!', 'Atenção')
	EndIf

Return

/*/{Protheus.doc} fAtuPedidos
Exibe MarkBrowse com pedidos de compra em aberto do fornecedor
para atualizacao de precos apos importacao de tabela
@type Static Function
@author TSC
@since 07/04/2026
@param cFornec, Character, Codigo do fornecedor
@param cLoja, Character, Loja do fornecedor
@param cCodTab, Character, Codigo da tabela de precos
@param aProdImp, Array, Produtos importados {{cProd, nPrc}, ...}
/*/
Static Function fAtuPedidos(cFornec, cLoja, cCodTab, aProdImp)
	Local aTamanho   := MsAdvSize()
	Local nJanLarg   := aTamanho[5]
	Local nJanAltu   := aTamanho[6]
	Local oFontGrid  := TFont():New(,,-14)
	Local aCampos    := {}
	Local aColunas   := {}
	Local aSeek      := {}
	Local oDlgMark, oPanGrid, oMarkBrowse, oTempTable
	Local cAliasTmp  := GetNextAlias()
	Local cAliasQry  := GetNextAlias()
	Local cQuery     := ""
	Local cAliasAIB  := RetSqlName("AIB")
	Local nRegs      := 0

	cCodTab := iif(empty(cCodTab), "001", cCodTab)

	nJanLarg := nJanLarg * 0.8
	nJanAltu := nJanAltu * 0.8

	// 1. Montar query: pedidos em aberto com preco divergente da tabela
	cQuery := " SELECT SC7.C7_FILIAL, " + CRLF
	cQuery += "        SC7.C7_NUM, " + CRLF
	cQuery += "        SC7.C7_ITEM, " + CRLF
	cQuery += "        SC7.C7_SEQUEN, " + CRLF
	cQuery += "        SC7.C7_FORNECE, " + CRLF
	cQuery += "        SC7.C7_LOJA, " + CRLF
	cQuery += "        SC7.C7_PRODUTO, " + CRLF
	cQuery += "        SC7.C7_DESCRI, " + CRLF
	cQuery += "        SC7.C7_CODTAB, " + CRLF
	cQuery += "        SC7.C7_DATPRF AS DTENTREGA, " + CRLF
	cQuery += "        SC7.C7_QUANT, " + CRLF
	cQuery += "        SC7.C7_PRECO, " + CRLF
	cQuery += "        SC7.C7_EMISSAO AS DTEMIS, " + CRLF
	cQuery += "        SC7.C7_COND, " + CRLF
	cQuery += "        SC7.C7_CONTATO, " + CRLF
	cQuery += "        SC7.C7_FILENT, " + CRLF
	cQuery += "        AIB.AIB_PRCCOM " + CRLF
	cQuery += " FROM " + RetSqlName("SC7") + " SC7 (NOLOCK) " + CRLF
	cQuery += " JOIN " + cAliasAIB + " AIB (NOLOCK) " + CRLF
	cQuery += "   ON AIB.D_E_L_E_T_ = ' ' " + CRLF
	cQuery += "   AND AIB.AIB_FILIAL = SC7.C7_FILIAL " + CRLF
	cQuery += "   AND AIB.AIB_CODFOR = SC7.C7_FORNECE " + CRLF
	cQuery += "   AND AIB.AIB_LOJFOR = SC7.C7_LOJA " + CRLF
	cQuery += "   AND AIB.AIB_CODTAB = '" + PadR(cCodTab, TamSX3("AIB_CODTAB")[1]) + "' " + CRLF
	cQuery += "   AND AIB.AIB_CODPRO = SC7.C7_PRODUTO " + CRLF
	// Garante 1 registro AIB por produto - pega o ultimo cadastrado (R_E_C_N_O_ maior)
	// para evitar duplicacao de linhas no MarkBrowse quando ha multiplos AIB com
	// a mesma chave (importacoes anteriores que acumularam registros)
	cQuery += "   AND AIB.R_E_C_N_O_ = ( " + CRLF
	cQuery += "        SELECT MAX(AIB2.R_E_C_N_O_) " + CRLF
	cQuery += "          FROM " + cAliasAIB + " AIB2 " + CRLF
	cQuery += "         WHERE AIB2.D_E_L_E_T_ = ' ' " + CRLF
	cQuery += "           AND AIB2.AIB_FILIAL = AIB.AIB_FILIAL " + CRLF
	cQuery += "           AND AIB2.AIB_CODFOR = AIB.AIB_CODFOR " + CRLF
	cQuery += "           AND AIB2.AIB_LOJFOR = AIB.AIB_LOJFOR " + CRLF
	cQuery += "           AND AIB2.AIB_CODTAB = AIB.AIB_CODTAB " + CRLF
	cQuery += "           AND AIB2.AIB_CODPRO = AIB.AIB_CODPRO ) " + CRLF
	cQuery += " WHERE SC7.D_E_L_E_T_ = ' ' " + CRLF
	cQuery += "   AND SC7.C7_FILIAL = '" + xFilial("SC7") + "' " + CRLF
	cQuery += "   AND SC7.C7_FORNECE = '" + PadR(cFornec, TamSX3("C7_FORNECE")[1]) + "' " + CRLF
	cQuery += "   AND SC7.C7_LOJA = '" + PadR(cLoja, TamSX3("C7_LOJA")[1]) + "' " + CRLF
	cQuery += "   AND SC7.C7_RESIDUO = ' ' " + CRLF
	cQuery += "   AND SC7.C7_QUANT > SC7.C7_QUJE " + CRLF
	cQuery += "   AND ROUND(AIB.AIB_PRCCOM, 5) != ROUND(SC7.C7_PRECO, 5) " + CRLF
	cQuery += " ORDER BY SC7.C7_NUM, SC7.C7_ITEM " + CRLF

	// 2. Criar tabela temporaria
	aAdd(aCampos, {"FLAG_OK",      "C",   2,  0})
	aAdd(aCampos, {"C7_NUM",       "C",  TamSX3("C7_NUM")[1],      0})
	aAdd(aCampos, {"C7_ITEM",      "C",  TamSX3("C7_ITEM")[1],     0})
	aAdd(aCampos, {"C7_PRODUTO",   "C",  TamSX3("C7_PRODUTO")[1],  0})
	aAdd(aCampos, {"C7_DESCRI",    "C",  TamSX3("C7_DESCRI")[1],   0})
	aAdd(aCampos, {"C7_CODTAB",    "C",  TamSX3("C7_CODTAB")[1],   0})
	aAdd(aCampos, {"DTENTREGA",    "D",   8,  0})
	aAdd(aCampos, {"C7_QUANT",     "N",  TamSX3("C7_QUANT")[1],  TamSX3("C7_QUANT")[2]})
	aAdd(aCampos, {"PRCATUAL",     "N",  TamSX3("C7_PRECO")[1],  TamSX3("C7_PRECO")[2]})
	aAdd(aCampos, {"PRCNOVO",      "N",  TamSX3("C7_PRECO")[1],  TamSX3("C7_PRECO")[2]})
	aAdd(aCampos, {"PERCDIF",      "N",   8,  2})
	aAdd(aCampos, {"STATUS",       "C",   1,  0})
	aAdd(aCampos, {"FILIAL",       "C",  TamSX3("C7_FILIAL")[1],   0})
	aAdd(aCampos, {"C7_SEQUEN",    "C",  TamSX3("C7_SEQUEN")[1],   0})
	aAdd(aCampos, {"C7_FORNECE",   "C",  TamSX3("C7_FORNECE")[1],  0})
	aAdd(aCampos, {"LOJA",         "C",  TamSX3("C7_LOJA")[1],     0})
	aAdd(aCampos, {"DTEMIS",       "C",   8,  0})
	aAdd(aCampos, {"C7_COND",      "C",  TamSX3("C7_COND")[1],     0})
	aAdd(aCampos, {"C7_CONTATO",   "C",  TamSX3("C7_CONTATO")[1],  0})
	aAdd(aCampos, {"C7_FILENT",    "C",  TamSX3("C7_FILENT")[1],   0})
	aAdd(aCampos, {"MSGERRO",      "C", 254,  0})
	aAdd(aCampos, {"MSGCOMP",      "M",  10,  0})


	oTempTable := FWTemporaryTable():New(cAliasTmp)
	oTempTable:SetFields(aCampos)
	oTempTable:AddIndex("1", {"C7_NUM", "C7_ITEM"})
	oTempTable:AddIndex("2", {"C7_PRODUTO"})
	oTempTable:Create()

	// 3. Carregar dados com feedback visual (query + populate dentro de Processa)
	Processa({|| fCarregaDados(cQuery, cAliasQry, cAliasTmp, @nRegs)}, "Carregando pedidos de compra...")

	If nRegs == 0
		oTempTable:Delete()
		MsgInfo("Nenhum pedido de compra em aberto com preco divergente encontrado.", "Delpi")
		Return
	EndIf

	// 4. Montar colunas e pesquisa
	aColunas := fCriaColsPed(cAliasTmp)
	// Pesquisa por Produto
	aAdd(aSeek, {"Produto", {{"" , "C", 15, 0, "C7_PRODUTO", "@!"}}})

	// 5. Dialog + MarkBrowse (protegido por Begin Sequence para garantir cleanup)
	Begin Sequence

		oDlgMark := TDialog():New(0, 0, nJanAltu, nJanLarg, "Atualizacao de Precos - Pedidos de Compra", , , , , , , , , .T.)

		oPanGrid := tPanel():New(001, 001, '', oDlgMark, , , , RGB(0,0,0), RGB(254,254,254), (nJanLarg/2)-5, (nJanAltu/2)-25)

		oMarkBrowse := FWMarkBrowse():New()
		oMarkBrowse:SetAlias(cAliasTmp)
		oMarkBrowse:SetTemporary(.T.)
		oMarkBrowse:SetDescription("Pedidos de Compra - Atualizacao de Precos")
		oMarkBrowse:AddLegend(cAliasTmp + "->STATUS == '1'", "GREEN",  "Pendente")
		oMarkBrowse:AddLegend(cAliasTmp + "->STATUS == '2'", "BLUE",   "Atualizado")
		oMarkBrowse:AddLegend(cAliasTmp + "->STATUS == '3'", "RED",    "Erro")
		oMarkBrowse:SetFieldMark('FLAG_OK')
		oMarkBrowse:SetColumns(aColunas)
		oMarkBrowse:SetFontBrowse(oFontGrid)
		oMarkBrowse:SetOwner(oPanGrid)
		oMarkBrowse:Activate()

		// Botoes ao pe do dialog
		TButton():New((nJanAltu/2)-18, 8, "&Atualizar Selecionados", oDlgMark, ;
			{|| fProcessaMark(oMarkBrowse, cAliasTmp, cCodTab)}, 110, 14,,,,.T.)
		TButton():New((nJanAltu/2)-18, 130, "&Ver Erro", oDlgMark, ;
			{|| fDupClique(cAliasTmp)}, 60, 14,,,,.T.)
		TButton():New((nJanAltu/2)-18, 200, "&Fechar", oDlgMark, ;
			{|| oDlgMark:End()}, 60, 14,,,,.T.)

		ACTIVATE MSDIALOG oDlgMark CENTERED

		Recover
		ConOut("DLP02F24 - Erro em fAtuPedidos")
	End Sequence

	// 6. Cleanup (sempre executa, mesmo apos erro)
	FWFreeObj(oFontGrid)
	oTempTable:Delete()
Return

/*/{Protheus.doc} fCarregaDados
Executa a query de pedidos e popula tabela temporaria com feedback visual.
Deve ser chamada via Processa() para que ProcRegua/IncProc tenham janela onde renderizar.
Reseta a regua entre as fases (busca, contagem, populacao), padrao usado em DAN010A01.
@type Static Function
@author TSC
@since 16/04/2026
@param cQuery, Character, Query SQL a executar
@param cAliasQry, Character, Alias de saida da query
@param cAliasTmp, Character, Alias da tabela temporaria a popular
@param nRegs, Numeric, Por referencia - quantidade de registros carregados
/*/
Static Function fCarregaDados(cQuery, cAliasQry, cAliasTmp, nRegs)
	Local nCount := 0

	nRegs := 0

	// Fase 1: Executar query (regua de 1 passo, mensagem unica)
	ProcRegua(1)
	IncProc("Buscando pedidos de compra na base de dados...")
	MpSysOpenQuery(ChangeQuery(cQuery), cAliasQry)

	If (cAliasQry)->(Eof())
		(cAliasQry)->(DbCloseArea())
		Return
	EndIf

	// Fase 2: Contar registros para dimensionar a regua da fase seguinte
	IncProc("Contando registros...")
	(cAliasQry)->(DbGoTop())
	While !(cAliasQry)->(Eof())
		nCount := nCount + 1
		(cAliasQry)->(DbSkip())
	EndDo
	(cAliasQry)->(DbGoTop())

	// Fase 3: Popular tabela temporaria (regua reseta com o total real)
	ProcRegua(nCount)
	nRegs := fPopulaTmp(cAliasTmp, cAliasQry)
	(cAliasQry)->(DbCloseArea())
Return

/*/{Protheus.doc} fPopulaTmp
Popula tabela temporaria com dados da query de pedidos
@type Static Function
@author TSC
@since 07/04/2026
@param cAliasTmp, Character, Alias da tabela temporaria
@param cAliasQry, Character, Alias da query
@return nRegs, Numeric, Quantidade de registros populados
/*/
Static Function fPopulaTmp(cAliasTmp, cAliasQry)
	Local nRegs    := 0
	Local nPrcAtu  := 0
	Local nPrcNov  := 0
	Local nPercDif := 0

	(cAliasQry)->(DbGoTop())
	While !(cAliasQry)->(Eof())
		IncProc("Carregando pedido " + AllTrim((cAliasQry)->C7_NUM) + " item " + AllTrim((cAliasQry)->C7_ITEM))

		nPrcAtu := (cAliasQry)->C7_PRECO
		nPrcNov := (cAliasQry)->AIB_PRCCOM
		nPercDif := 0
		If nPrcAtu > 0
			nPercDif := ((nPrcNov - nPrcAtu) / nPrcAtu) * 100
		EndIf

		If RecLock(cAliasTmp, .T.)
			(cAliasTmp)->FLAG_OK        := Space(2)
			(cAliasTmp)->C7_NUM     := (cAliasQry)->C7_NUM
			(cAliasTmp)->C7_ITEM    := (cAliasQry)->C7_ITEM
			(cAliasTmp)->C7_PRODUTO   := (cAliasQry)->C7_PRODUTO
			(cAliasTmp)->C7_DESCRI  := (cAliasQry)->C7_DESCRI
			(cAliasTmp)->C7_CODTAB    := (cAliasQry)->C7_CODTAB
			(cAliasTmp)->DTENTREGA := STOD((cAliasQry)->DTENTREGA)
			(cAliasTmp)->C7_QUANT     := (cAliasQry)->C7_QUANT
			(cAliasTmp)->PRCATUAL  := nPrcAtu
			(cAliasTmp)->PRCNOVO   := nPrcNov
			(cAliasTmp)->PERCDIF   := nPercDif
			(cAliasTmp)->STATUS    := "1"
			(cAliasTmp)->FILIAL    := (cAliasQry)->C7_FILIAL
			(cAliasTmp)->C7_SEQUEN    := (cAliasQry)->C7_SEQUEN
			(cAliasTmp)->C7_FORNECE   := (cAliasQry)->C7_FORNECE
			(cAliasTmp)->LOJA      := (cAliasQry)->C7_LOJA
			(cAliasTmp)->DTEMIS    := (cAliasQry)->DTEMIS
			(cAliasTmp)->C7_COND   := (cAliasQry)->C7_COND
			(cAliasTmp)->C7_CONTATO   := (cAliasQry)->C7_CONTATO
			(cAliasTmp)->C7_FILENT    := (cAliasQry)->C7_FILENT
			(cAliasTmp)->MSGERRO   := Space(254)
			(cAliasTmp)->(MsUnlock())
		EndIf

		nRegs := nRegs + 1
		(cAliasQry)->(DbSkip())
	EndDo
Return nRegs

/*/{Protheus.doc} fCriaColsPed
Cria colunas do FWMarkBrowse de pedidos
@type Static Function
@author TSC
@since 07/04/2026
@param cAliasTmp, Character, Alias da tabela temporaria
@return aColunas, Array, Array de FWBrwColumn
/*/
Static Function fCriaColsPed(cAliasTmp)
	Local aColunas := {}
	Local oColumn

	// Numero PC
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->C7_NUM}"))
	oColumn:SetTitle("Num.PC")
	oColumn:SetType("C")
	oColumn:SetSize(6)
	aAdd(aColunas, oColumn)

	// Item
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->C7_ITEM}"))
	oColumn:SetTitle("Item")
	oColumn:SetType("C")
	oColumn:SetSize(4)
	aAdd(aColunas, oColumn)

	// Produto
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->C7_PRODUTO}"))
	oColumn:SetTitle("Produto")
	oColumn:SetType("C")
	oColumn:SetSize(12)
	aAdd(aColunas, oColumn)

	// Descricao
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->C7_DESCRI}"))
	oColumn:SetTitle("Descricao")
	oColumn:SetType("C")
	oColumn:SetSize(35)
	aAdd(aColunas, oColumn)

	// Tab Preco
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->C7_CODTAB}"))
	oColumn:SetTitle("Tab.Preco")
	oColumn:SetType("C")
	oColumn:SetSize(4)
	aAdd(aColunas, oColumn)

	// Dt Entrega
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->DTENTREGA}"))
	oColumn:SetTitle("Dt.Entrega")
	oColumn:SetType("D")
	oColumn:SetSize(10)
	aAdd(aColunas, oColumn)

	// Quantidade
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->C7_QUANT}"))
	oColumn:SetTitle("Quantidade")
	oColumn:SetType("N")
	oColumn:SetSize(10)
	oColumn:SetDecimal(2)
	aAdd(aColunas, oColumn)

	// Preco Atual
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->PRCATUAL}"))
	oColumn:SetTitle("Preco Atual")
	oColumn:SetType("N")
	oColumn:SetSize(10)
	oColumn:SetDecimal(2)
	aAdd(aColunas, oColumn)

	// Preco Novo
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->PRCNOVO}"))
	oColumn:SetTitle("Preco Novo")
	oColumn:SetType("N")
	oColumn:SetSize(10)
	oColumn:SetDecimal(2)
	aAdd(aColunas, oColumn)

	// % Diferenca
	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->PERCDIF}"))
	oColumn:SetTitle("% Dif.")
	oColumn:SetType("N")
	oColumn:SetSize(8)
	oColumn:SetDecimal(2)
	oColumn:SetPicture("@E 9999.99")
	aAdd(aColunas, oColumn)

	oColumn := FWBrwColumn():New()
	oColumn:SetData(&("{|| " + cAliasTmp + "->MSGERRO}"))
	oColumn:SetTitle("Mgs. Erro")
	oColumn:SetType("C")
	oColumn:SetSize(40)
	oColumn:SetDecimal(0)
	aAdd(aColunas, oColumn)


Return aColunas

Static Function fDupClique(cAliasTmp)

	If (cAliasTmp)->STATUS == "3" .And. !Empty((cAliasTmp)->MSGCOMP)
		ShowLog((cAliasTmp)->MSGCOMP)
	EndIf

Return

/*/{Protheus.doc} fProcessaMark
Processa itens marcados atualizando precos via ExecAuto MATA120
@type Static Function
@author TSC
@since 07/04/2026
@param oMarkBrowse, Object, Objeto FWMarkBrowse
@param cAliasTmp, Character, Alias da tabela temporaria
/*/
Static Function fProcessaMark(oMarkBrowse, cAliasTmp, cCodTab)
	Local aArea    := FWGetArea()
	Local nTotal   := 0
	Local aResult  := {0, 0}  // {nOk, nErro}
	Private lMsErroAuto    := .F.
	Private lMsHelpAuto    := .T.
	Private lAutoErrNoFile := .T.

	// Contar marcados pendentes
	(cAliasTmp)->(DbGoTop())
	While !(cAliasTmp)->(Eof())
		If !Empty((cAliasTmp)->FLAG_OK) .And. (cAliasTmp)->STATUS == "1"
			nTotal := nTotal + 1
		EndIf
		(cAliasTmp)->(DbSkip())
	EndDo

	If nTotal == 0
		MsgAlert("Nenhum registro pendente selecionado!", "Delpi")
		FWRestArea(aArea)
		Return
	EndIf

	If !MsgYesNo("Confirma a atualizacao de " + cValToChar(nTotal) + " item(ns)?", "Delpi")
		FWRestArea(aArea)
		Return
	EndIf

	// Processa() cria a janela de regua/progresso onde ProcRegua/IncProc desenham
	Processa({|| fLoopAtu(cAliasTmp, nTotal, @aResult, cCodTab)}, "Atualizando precos em pedidos de compra...")

	// Refresh apos Processa(): FWMarkBrowse tem bug historico de duplicacao de
	// linhas ao dar Refresh (TDN DFRM1-30551). Padrao End+Home via :oBrowse
	// (FWMBrowse interno) resolve em LIBs sem a correcao oficial.
	// Ref: TEC10A08 (TECNOPERFIL)
	(cAliasTmp)->(DbGoTop())
	oMarkBrowse:oBrowse:GoBottom(.T.)
	oMarkBrowse:oBrowse:Refresh(.T.)
	oMarkBrowse:oBrowse:GoTop(.T.)
	oMarkBrowse:oBrowse:Refresh(.T.)
	MsgInfo(cValToChar(aResult[1]) + " item(ns) atualizado(s), " + cValToChar(aResult[2]) + " erro(s).", "Delpi")
	FWRestArea(aArea)
Return

/*/{Protheus.doc} fLoopAtu
Loop de atualizacao de precos via ExecAuto MATA120, executado dentro de Processa()
para que ProcRegua/IncProc tenham janela de progresso onde renderizar.
@type Static Function
@author TSC
@since 16/04/2026
@param cAliasTmp, Character, Alias da tabela temporaria
@param nTotal, Numeric, Total de registros a processar (para a regua)
@param aResult, Array, Array {nOk, nErro} preenchido por referencia
/*/
Static Function fLoopAtu(cAliasTmp, nTotal, aResult, cCodTab)
	Local aCabec     := {}
	Local aItens     := {}
	Local aLinha     := {}
	Local aLogAuto   := {}
	Local cErro      := ""
	Local nI         := 0
	Local nOk        := 0
	Local nErro      := 0
	Local aAreaAIA   := AIA->(GetArea())
	Local dDatdeOrig := CTOD("")
	Local cFornAIA   := ""
	Local cLojaAIA   := ""
	Local dEmisMin   := CTOD("")
	Local lAjusteAIA := .F.

	// 1a varredura: descobrir menor data de emissao entre os marcados
	// e identificar fornecedor/loja para localizar a AIA da tabela importada
	(cAliasTmp)->(DbGoTop())
	While !(cAliasTmp)->(Eof())
		If !Empty((cAliasTmp)->FLAG_OK) .And. (cAliasTmp)->STATUS == "1"
			If Empty(dEmisMin) .Or. SToD((cAliasTmp)->DTEMIS) < dEmisMin
				dEmisMin := SToD((cAliasTmp)->DTEMIS)
			EndIf
			If Empty(cFornAIA)
				cFornAIA := (cAliasTmp)->C7_FORNECE
				cLojaAIA := (cAliasTmp)->LOJA
			EndIf
		EndIf
		(cAliasTmp)->(DbSkip())
	EndDo

	// Recua AIA_DATDE temporariamente para abranger pedidos com emissao
	// anterior a vigencia atual da tabela. Sem esse ajuste, MaVldTabCom
	// (chamado por MATA120) bloqueia a alteracao com a mensagem:
	// "A data de emissao do pedido nao encontra-se dentro da data de
	//  validade desta tabela de precos".
	If !Empty(dEmisMin) .And. !Empty(cCodTab)
		DbSelectArea("AIA")
		AIA->(DbSetOrder(1))
		If AIA->(DbSeek(xFilial("AIA") + cFornAIA + cLojaAIA + cCodTab))
			If dEmisMin < AIA->AIA_DATDE
				dDatdeOrig := AIA->AIA_DATDE
				RecLock("AIA", .F.)
				AIA->AIA_DATDE := dEmisMin
				AIA->(MsUnlock())
				lAjusteAIA := .T.
			EndIf
		EndIf
	EndIf

	ProcRegua(nTotal)

	(cAliasTmp)->(DbGoTop())
	While !(cAliasTmp)->(Eof())
		If !Empty((cAliasTmp)->FLAG_OK) .And. (cAliasTmp)->STATUS == "1"

			IncProc("Atualizando PC " + AllTrim((cAliasTmp)->C7_NUM) + " Item " + AllTrim((cAliasTmp)->C7_ITEM))

			// Montar cabecalho (campos obrigatorios TDN MATA120)
			aCabec := {}
			aAdd(aCabec, {"C7_NUM",     (cAliasTmp)->C7_NUM})
			aAdd(aCabec, {"C7_EMISSAO", SToD((cAliasTmp)->DTEMIS)})
			aAdd(aCabec, {"C7_FORNECE", (cAliasTmp)->C7_FORNECE})
			aAdd(aCabec, {"C7_LOJA",    (cAliasTmp)->LOJA})
			aAdd(aCabec, {"C7_COND",    (cAliasTmp)->C7_COND})
			aAdd(aCabec, {"C7_CONTATO", (cAliasTmp)->C7_CONTATO})
			aAdd(aCabec, {"C7_FILENT",  (cAliasTmp)->C7_FILENT})

			// Montar item (1 item por ExecAuto)
			aItens := {}
			aLinha := {}
			aAdd(aLinha, {"C7_ITEM",    (cAliasTmp)->C7_ITEM,                              Nil})
			aAdd(aLinha, {"C7_PRODUTO", (cAliasTmp)->C7_PRODUTO,                             Nil})
			aAdd(aLinha, {"C7_QUANT",   (cAliasTmp)->C7_QUANT,                               Nil})
			aAdd(aLinha, {"C7_PRECO",   (cAliasTmp)->PRCNOVO,                             Nil})
			aAdd(aLinha, {"C7_TOTAL",   (cAliasTmp)->C7_QUANT * (cAliasTmp)->PRCNOVO,        Nil})
			aAdd(aLinha, {"LINPOS",     "C7_ITEM", (cAliasTmp)->C7_ITEM})
			aAdd(aLinha, {"AUTDELETA",  "N",       Nil})
			aAdd(aItens, aLinha)

			// Posicionar SC7 antes do ExecAuto (obrigatorio para alteracao nOpc=4)
			DbSelectArea("SC7")
			SC7->(DbSetOrder(1))

			// Executar ExecAuto MATA120 (operacao 4 = alteracao)
			lMsErroAuto := .F.
			cErro       := ""
			If SC7->(DbSeek((cAliasTmp)->FILIAL + (cAliasTmp)->C7_NUM + (cAliasTmp)->C7_ITEM + (cAliasTmp)->C7_SEQUEN))
				// TDN MATA120: C7_REC_WT obrigatorio para alteracao (SC7 recno do registro)
				aAdd(aCabec, {"C7_REC_WT", SC7->(Recno())})
				MSExecAuto({|a,b,c,d,e| MATA120(a,b,c,d,e)}, 1, aCabec, aItens, 4, .F.)
			Else
				lMsErroAuto := .T.
				cErro := "Registro SC7 nao localizado: Filial=" + AllTrim((cAliasTmp)->FILIAL) + ;
					" Num=" + AllTrim((cAliasTmp)->C7_NUM) + ;
					" Item=" + AllTrim((cAliasTmp)->C7_ITEM) + ;
					" Sequen=" + AllTrim((cAliasTmp)->C7_SEQUEN) + CRLF
			EndIf

			// Atualizar status na temporaria
			If RecLock(cAliasTmp, .F.)
				If lMsErroAuto
					If Empty(cErro)
						// Erro veio do MATA120, coletar mensagens do log
						aLogAuto := GetAutoGRLog()
						For nI := 1 To Len(aLogAuto)
							cErro += AllTrim(aLogAuto[nI]) + CRLF
						Next nI
					EndIf
					(cAliasTmp)->STATUS  := "3"
					(cAliasTmp)->MSGERRO := Left(cErro, 254)
					(cAliasTmp)->MSGCOMP := cErro
					nErro := nErro + 1
					ConOut("DLP02F24 - Erro MATA120 PC " + AllTrim((cAliasTmp)->C7_NUM) + " Item " + AllTrim((cAliasTmp)->C7_ITEM) + ": " + cErro)
				Else
					(cAliasTmp)->STATUS  := "2"
					(cAliasTmp)->MSGERRO := Space(254)
					nOk := nOk + 1
				EndIf
				(cAliasTmp)->FLAG_OK := Space(2)
				(cAliasTmp)->(MsUnlock())
			EndIf

		EndIf
		(cAliasTmp)->(DbSkip())
	EndDo

	// Restaura AIA_DATDE original apos a atualizacao dos pedidos
	If lAjusteAIA
		DbSelectArea("AIA")
		AIA->(DbSetOrder(1))
		If AIA->(DbSeek(xFilial("AIA") + cFornAIA + cLojaAIA + cCodTab))
			RecLock("AIA", .F.)
			AIA->AIA_DATDE := dDatdeOrig
			AIA->(MsUnlock())
		EndIf
	EndIf

	RestArea(aAreaAIA)

	aResult[1] := nOk
	aResult[2] := nErro
Return
