#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"

User Function DLP02F12()
	RpcSetEnv('01')

	Local aPergs    := {} // array para montar as perguntas na função ParamBox
	Local cAlias 		:= GetNextAlias()
	Local cForDe    := Space(getsx3cache("A2_COD","X3_TAMANHO"))                 /*01*/
	Local cForAte   := REPLICATE("Z",getsx3cache("A2_COD","X3_TAMANHO"))         /*02*/
	Local cForLjDe  := Space(getsx3cache("C7_LOJA","X3_TAMANHO"))                /*03*/
	Local cForLjAte := REPLICATE("Z",getsx3cache("C7_LOJA","X3_TAMANHO"))        /*04*/
	Local cProdDe   := Space(getsx3cache("C7_PRODUTO","X3_TAMANHO"))             /*05*/
	Local cProdAte  := REPLICATE("Z",getsx3cache("C7_PRODUTO","X3_TAMANHO"))     /*06*/
	Local cTabDe    := Space(getsx3cache("C7_CODTAB","X3_TAMANHO"))              /*07*/
	Local cTabAte   := REPLICATE("Z",getsx3cache("C7_CODTAB","X3_TAMANHO"))      /*08*/
	Local cFilDe    := Space(getsx3cache("C7_FILIAL","X3_TAMANHO"))              /*09*/
	Local cFilAte   := REPLICATE("Z",getsx3cache("C7_FILIAL","X3_TAMANHO"))      /*10*/
	Local dDtEntrDe := CToD("")                                                  /*11*/
	Local dDtEntrAte:= CToD("")                                                  /*12*/
	Local dDtEmiDe  := CToD("")                                                  /*13*/
	Local dDtEmiAte := CToD("")                                                  /*14*/                                              /*14*/
	Local aCabec := {}
	Local aLinha := {}
	Local aItens := {}
	Local cQry 	 := ""

	Private lMsErroAuto			:= .f. as logical
	Private lMsHelpAuto         := .T. as logical
	Private lAutoErrNoFile      := .T. as logical

	// /* 1*/	aAdd(aPergs,{2,"Quebra",nQuebra,aOpcQbr,100,"",.F.})
	/* 2*/	aAdd(aPergs, {1, 'Filial De',  cFilDe      , "@!", ".T.", "SM0", ".T.", 80,  .F.})
	/* 3*/	aAdd(aPergs, {1, 'Filial Ate', cFilAte    , "@!", ".T.", "SM0", ".T.", 80,  .F.})
	/* 4*/	aAdd(aPergs, {1, 'Do Fornecedor'   , cForDe     , "@!", ".T.", "SA2", ".T.", 80,  .F.})
	/* 5*/	aAdd(aPergs, {1, 'Da Loja ', cForLjDe       , "@!", ".T.", "", ".T.", 40,  .F.})
	/* 6*/	aAdd(aPergs, {1, 'Ate o Fornecedor', cForAte   , "@!", ".T.", "SA2", ".T.", 80,  .F.})
	/* 7*/	aAdd(aPergs, {1, 'Ate Loja ', cForLjAte       , "@!", ".T.", "", ".T.", 40,  .F.})
	/* 8*/	aAdd(aPergs, {1, 'Do  Produto ', cProdDe    , "@!", ".T.", "SB1", ".T.", 40,  .F.})
	/* 9*/	aAdd(aPergs, {1, 'Ate Produto ', cProdAte   , "@!", ".T.", "SB1", ".T.", 40,  .F.})
	/*10*/	aAdd(aPergs, {1, 'Da Tabela ', cTabDe      , "@!", ".T.", "AIB", ".T.", 80,  .F.})
	/*11*/	aAdd(aPergs, {1, 'Ate Tabela ', cTabAte    , "@!", ".T.", "AIB", ".T.", 80,  .F.})
	/*12*/	aAdd(aPergs, {1, 'Data de Emissao De ', dDtEmiDe    , "@!", ".T.", "", ".T.", 80,  .F.})
	/*13*/	aAdd(aPergs, {1, 'Data de Emissao Ate', dDtEmiAte   , "@!", ".T.", "", ".T.", 80,  .F.})
	/*14*/	aAdd(aPergs, {1, 'Data de Entrega De', dDtEntrDe      , "@!", ".T.", "", ".T.", 80,  .F.})
	/*15 */	aAdd(aPergs, {1, 'Data de Entrega Ate', dDtEntrAte    , "@!", ".T.", "", ".T.", 80,  .F.})

	// Filial De/Ate
	// Tabela De/Ate
	// Fornecedor De/Ate
	// Loja De/Ate
	// Produto De/Ate
	// Data Emissao De/Ate
	// Data Entrega De/Ate

	aRet := {}
	IF !ParamBox(aPergs, "Parâmetros Pedido de Compra",@aRet)

		return
		FWAlertWarning("Cancelado pelo Usuario","Delpi Compras")

	Else

		cQry := "SELECT TBL1.C7_FILIAL,"+CRLF
		cQry += "TBL1.C7_NUM,"+CRLF
		cQry += "TBL1.C7_ITEM,"+CRLF
		cQry += "TBL1.C7_FORNECE,"+CRLF
		cQry += "TBL1.C7_LOJA,"+CRLF
		cQry += "TBL1.C7_PRODUTO,"+CRLF
		cQry += "TBL1.C7_EMISSAO,"+CRLF
		cQry += "TBL1.C7_DATPRF,"+CRLF
		cQry += "TBL1.C7_CODTAB,"+CRLF
		cQry += "AIB.AIB_PRCCOM"+CRLF
		cQry += "FROM " + RetSqlName("SC7") + "(NOLOCK) TBL1"+CRLF
		cQry += "JOIN " + RetSqlName("AIB") + " (NOLOCK) AIB"+CRLF
		cQry += "ON AIB.D_E_L_E_T_ = ''"+CRLF
		cQry += "AND AIB_FILIAL = C7_FILIAL"+CRLF
		cQry += "AND AIB_CODFOR = C7_FORNECE"+CRLF
		cQry += "AND AIB_LOJFOR = C7_LOJA"+CRLF
		cQry += "AND AIB_CODPRO = C7_PRODUTO"+CRLF
		cQry += "WHERE"+CRLF
		cQry += "TBL1.D_E_L_E_T_ = ''"+CRLF
		cQry += "AND C7_RESIDUO = ''"+CRLF
		cQry += "AND C7_QUJE < C7_QUANT"+CRLF
		cQry += "AND C7_CODTAB != ''"+CRLF
		cQry += "AND ROUND(AIB_PRCCOM,5) != ROUND(C7_PRECO,5)"+CRLF
		cQry += "AND C7_FILIAL BETWEEN '" + aRet[1]+ "' AND '" + aRet[2]+ "'"+CRLF
		cQry += "AND C7_FORNECE BETWEEN '" + aRet[3]+ "' AND '" + aRet[5]+ "'"+CRLF
		cQry += "AND C7_LOJA BETWEEN '" + aRet[4]+ "' AND '" + aRet[6]+ "'"+CRLF
		cQry += "AND C7_PRODUTO BETWEEN '" + aRet[7]+ "' AND '" + aRet[8]+ "'"+CRLF
		cQry += "AND C7_CODTAB BETWEEN '" + aRet[9]+ "' AND '" + aRet[10]+ "'"+CRLF
		cQry += "AND C7_EMISSAO BETWEEN '" + dtos(aRet[11])+ "' AND '" + dtos(aRet[12])+ "'"+CRLF
		cQry += "AND C7_DATPRF BETWEEN '" + dtos(aRet[13])+ "' AND '" + dtos(aRet[14])+ "'"+CRLF
		cQry += "ORDER BY 1
		dbUseArea(.T., "TOPCONN", TCGENQRY(,,cQry),cAlias, .F., .T.)

		dbSelectArea("SC7")

		While (cAlias)->(!EOF())

			aCabec := {}
			aItens := {}

			SC7->(DbSetOrder(1))
			If SC7->(DbSeek((cAlias)->C7_FILIAL+(cAlias)->C7_NUM+(cAlias)->C7_ITEM+(cAlias)->C7_SEQUEN))

				aadd(aCabec,{"C7_NUM" ,SC7->C7_NUM})
				aadd(aCabec,{"C7_EMISSAO" ,SC7->C7_EMISSAO})
				aadd(aCabec,{"C7_FORNECE" ,SC7->C7_FORNECE})
				aadd(aCabec,{"C7_LOJA" ,SC7->C7_LOJA})
				aadd(aCabec,{"C7_COND" ,SC7->C7_COND}) // Condição de pagamento que permite adiantamento
				aadd(aCabec,{"C7_CONTATO" ,SC7->C7_CONTATO})
				aadd(aCabec,{"C7_FILENT" ,SC7->C7_FILENT})

				aLinha := {}

				// Alterar item existente
				aadd(aLinha,{"C7_ITEM" ,SC7->C7_ITEM,Nil})
				aadd(aLinha,{"C7_PRODUTO" ,SC7->C7_PRODUTO,Nil})
				aadd(aLinha,{"C7_QUANT" ,SC7->C7_QUANT,Nil})
				aadd(aLinha,{"C7_PRECO" ,(cAlias)->AIB_PRCCOM,Nil})
				aAdd(aLinha,{"LINPOS","C7_ITEM" ,SC7->C7_ITEM})
				aAdd(aLinha,{"AUTDELETA","N" ,Nil})
				aadd(aItens,aLinha)

				MSExecAuto({|a,b,c,d,e| MATA120(a,b,c,d,e)},1,aCabec,aItens,4,.F.)

				If lMsErroAuto
					MOSTRAERRO()
				EndIf

			EndIf

			(cAlias)->(DbSkip())

		EndDo

		(cAlias)->(DbCloseArea())

	endif

	RpcClearEnv()

Return
