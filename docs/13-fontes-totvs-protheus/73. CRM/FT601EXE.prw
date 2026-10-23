#INCLUDE "PROTHEUS.CH"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออปฑฑ
ฑฑบPrograma  ณFt601Exe  บAutor  ณVendas CRM			 บ Data ณ  27/12/10 บฑฑ
ฑฑฬออออออออออุออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออนฑฑ
ฑฑบDesc.     ณExemplo para preenchimento de variaveis da proposta       บฑฑ
ฑฑบ          ณcomercial usando a integracao com o WORD.                 บฑฑ
ฑฑฬออออออออออุออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณ Ft601Exe                                                 บฑฑ
ฑฑศออออออออออฯออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑบ			Especํfico Energia Solar                                    บฑฑ
ฑฑศออออออออออฯออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/

User Function Ft601Exe()

	Local aArea			:= GetArea()						//Armazena area atual
	Local cUnCons 	    :=  SPACE(10) //Unidade consumidora campo criado na proposta - ADY_ZUNCON
	Local hWord 		:= ParamIXB[1]						//Objeto usado para preenchimento
	Local cProposta		:= Space(TamSX3("CJ_PROPOST")[1])	//Numero da proposta comercial
	Local cRevisao		:= Space(TamSX3("ADY_PREVIS")[1])   //Controla a revisao do documento
	Local cDtEmissao	:= Space(TamSX3("CJ_EMISSAO")[1])	//Data de emissao
	Local cRede			:= Space(10)						//Tipo de rede eletrica
	Local cCodigo		:= Space(TamSX3("A1_COD")[1])		//Codigo da entidade (cliente ou prospect)
	Local cLoja			:= Space(TamSX3("A1_LOJA")[1])		//Loja
	Local cNome 		:= Space(TamSX3("A1_NOME")[1])		//Nome
	Local cEndereco		:= Space(TamSX3("A1_END")[1])   	//Endereco
	Local cBairro		:= Space(TamSX3("A1_BAIRRO")[1])    //Bairro
	Local cCidade		:= Space(TamSX3("A1_MUN")[1])  	    //Cidade
	Local cUF			:= Space(TamSX3("A1_ESTADO")[1])  	//Estado (UF)
	Local cCEP			:= Space(TamSX3("A1_CEP")[1])		//CEP
	Local cDDD			:= Space(TamSX3("A1_DDD")[1])		//DDD
	Local cTel			:= Space(TamSX3("A1_TEL")[1])		//Telefone
	Local lMsDocument	:= SuperGetMv("MV_FTMSDOC",,.F.)    //Define se a proposta comercial sera vinculada ao banco de conhecimento
	Local cPRevisa		:= ' '                              //Revisao dos itens da proposta comercial gravado na tabela ADZ
	Local aTipo09		:= {}								//Array que armazena o tipo de pagamento 9
	Local aCronoFin		:= {}								//Array que armazena o cronograma financeiro
	Local nTotProsp		:= 0								//Total da proposta comercial
	Local nI			:= 0                               	//Usado no laco do While
	Local nX            := 0                                //Usado no laco do For
	Local nY			:= 0								//Usado no laco do While
	Local nCount		:= 0								//Incremento para utilizar no itens de cond. pagto.
	Local cTelFil		:= Space(12)						//Telefone da Filial
	Local cEndFil		:= Space(70)						//Endereco da Filial


	//cProposta	:= ADY->ADY_PROPOS
	cProposta	:= "OV"+TRIM(ADY->ADY_OPORTU)
	cPRevisa	:= ADY->ADY_PREVIS
	cRevisao	:= ADY->ADY_PREVIS
	cDescEnt	:= Space(30)
	cDtEmissao	:= Dtoc(ADY->ADY_DATA)
	aTipo09		:= Ft601Tip09(cProposta,cPRevisa)
	aCronoFin	:= Ft601CroFin(cProposta,cPRevisa,aTipo09)

	IF !EMPTY(ADY->ADY_ZUNCON)
		cUnCons   := "Unidade Consumidora: " + Alltrim(ADY->ADY_ZUNCON)
	ENDIF

	If ADY->ADY_ENTIDA == "1"
		dbSelectArea("SA1")
		dbSetOrder(1)
		If	dbSeek(xFilial("SA1")+ADY->ADY_CODIGO+ADY->ADY_LOJA)
			cCodigo		:= ADY->ADY_CODIGO
			cLoja		:= ADY->ADY_LOJA
			cNome 		:= SA1->A1_NOME
			cDescEnt	:= SA1->A1_NREDUZ
			cEndereco	:= SA1->A1_END
			cBairro		:= SA1->A1_BAIRRO
			cCidade		:= SA1->A1_MUN
			cUF			:= SA1->A1_EST
			cCEP		:= SA1->A1_CEP
			cDDD		:= SA1->A1_DDD
			cTel		:= SA1->A1_TEL
		Endif
	Else
		dbSelectArea("SUS")
		dbSetOrder(1)
		If	dbSeek(xFilial("SUS")+ADY->ADY_CODIGO+ADY->ADY_LOJA)
			cCodigo		:= ADY->ADY_CODIGO
			cLoja		:= ADY->ADY_LOJA
			cNome 		:= SUS->US_NOME
			cDescEnt	:= SUS->US_NREDUZ
			cEndereco	:= SUS->US_END
			cBairro		:= SUS->US_BAIRRO
			cCidade		:= SUS->US_MUN
			cUF			:= SUS->US_EST
			cCEP		:= SUS->US_CEP
			cDDD		:= SUS->US_DDD
			cTel		:= SUS->US_TEL
		Endif
	Endif

	cNomeWord	:=	''
	cNomeWord	:= 'P'+cProposta


	//If lMsDocument
	//
	//	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//	//ณ Faz revisao do documento pelo banco de conhecimento. ณ
	//	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
	//
	//	OLE_SetDocumentVar(hWord,'cRevisao'	,Ft601Rev(cProposta))
	//
	//Else
	//
	//	OLE_SetDocumentVar(hWord,'cRevisao'	,cRevisao)
	//
	//EndIf

	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Descricao da Oportunidade de Venda         ณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
	OLE_SetDocumentVar(hWord,'cDesOport',Capital(POSICIONE("AD1",1,xFilial("AD1")+ADY->ADY_OPORTU,"AD1_DESCRI")))


	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Atualiza variaveis do cabecalho - Variaveisณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
	//OLE_SetDocumentVar(hWord,'cProposta'	,cProposta)
	OLE_SetDocumentVar(hWord,'cProposta'	,ADY->ADY_OPORTU)
	OLE_SetDocumentVar(hWord,'cRevisao'		,cRevisao)
	OLE_SetDocumentVar(hWord,'cDtEmissao'	,cDtEmissao)
	OLE_SetDocumentVar(hWord,'cCodigo'		,cCodigo)
	OLE_SetDocumentVar(hWord,'cNome'		,cNome)
	OLE_SetDocumentVar(hWord,'cUnCons'		,cUnCons)
	OLE_SetDocumentVar(hWord,'cEndereco'	,cEndereco)
	OLE_SetDocumentVar(hWord,'cBairro'		,cBairro)
	OLE_SetDocumentVar(hWord,'cCidade'		,cCidade)
	OLE_SetDocumentVar(hWord,'cUF'			,cUF)
	OLE_SetDocumentVar(hWord,'cCEP'			,cCEP)
	OLE_SetDocumentVar(hWord,'cDDD'			,cDDD)
	OLE_SetDocumentVar(hWord,'cTel'			,cTel)

	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Atualiza variaveis da energia solar - Camposณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู

	If  ADY->ADY_ZREDE == "1"
		cRede	:= 'Monofแsica'
	Else
		If ADY->ADY_ZREDE == "2"
			cRede	:= 'Bifแsica'
		Else
			cRede	:= 'Trifแsica'
		EndIf
	EndIf

	OLE_SetDocumentVar(hWord,'nKwhm'	,Alltrim(Transform(ADY->ADY_ZKWHM,"9,999.9")))
	OLE_SetDocumentVar(hWord,'cRede'	,cRede)
	OLE_SetDocumentVar(hWord,'nTxmin'	,Alltrim(Transform(ADY->ADY_ZTXMIN,"9,999.9")))
	OLE_SetDocumentVar(hWord,'nConsu'	,Alltrim(Transform(ADY->ADY_ZCONSU,"9,999.9")))
	OLE_SetDocumentVar(hWord,'nCpins'	,Alltrim(Transform(ADY->ADY_ZCPINS,"9,999.9")))
	OLE_SetDocumentVar(hWord,'nCpest'	,Alltrim(Transform(ADY->ADY_ZCPEST,"9,999.9")))
	OLE_SetDocumentVar(hWord,'cTelha'	,AllTrim(ADY->ADY_ZTELHA))


	DbSelectArea("SA3")
	DbSetOrder(1)
	If dbSeek(xFilial("SA3")+ADY->ADY_VEND)

		OLE_SetDocumentVar(hWord,'cNomVen'  ,Alltrim(SA3->A3_NOME))
		OLE_SetDocumentVar(hWord,'cDDDVen'  ,Alltrim(SA3->A3_DDDTEL))
		OLE_SetDocumentVar(hWord,'cTelVen'  ,Alltrim(SA3->A3_TEL))
		OLE_SetDocumentVar(hWord,'cCelVen'  ,Alltrim(SA3->A3_CEL))

	Endif

	If ADY->ADY_FILIAL = '01'
		cTelFil := '47 3017-9575'
		cEndFil	:= 'Rua Max Wilhelm, 840 - Bairro Baependi - Jaraguแ do Sul - SC'
	Else
		cTelFil := '27 3265-1904'
		cEndFil	:= 'Rua Eduardo Malavasi, 165 - Bairro Sใo Sebasiใo - Rio Bananal - ES'
	Endif

	OLE_SetDocumentVar(hWord,'cTelFil'  ,cTelFil)
	OLE_SetDocumentVar(hWord,'cEndfil'	,cEndFil)

	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Atualiza variaveis do item - Tabelaณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู

	DbSelectArea("ADZ")
	DbSetOrder(3)
	If dbSeek(xFilial("ADZ")+cProposta+cPRevisa)

		While ADZ->(!Eof()) .and. xFilial("ADZ") == ADZ->ADZ_FILIAL .AND. cProposta == ADZ->ADZ_PROPOS

			nI++

			OLE_SetDocumentVar(hWord,'cProd'+Alltrim(str(nI))  ,Alltrim( Posicione("SB1",1,xFilial("SB1")+ADZ->ADZ_PRODUT,"B1_DESC") ) )
			OLE_SetDocumentVar(hWord,'nQuant'+Alltrim(str(nI)) ,Transform(ADZ->ADZ_QTDVEN,"999,999,999.99"))
			OLE_SetDocumentVar(hWord,'nValUni'+Alltrim(str(nI)),Transform(ADZ->ADZ_PRCVEN,"@E 999,999,999.99"))
			OLE_SetDocumentVar(hWord,'nTotal'+Alltrim(str(nI)) ,Transform(ADZ->ADZ_TOTAL,"@E 999,999,999.99"))

			nTotProsp += ADZ->ADZ_TOTAL

			ADZ->(dbSkip())

		Enddo

		OLE_SetDocumentVar(hWord,'nTotProsp',Transform(nTotProsp,"@E 999,999,999.99"))

	Endif

	If nI > 0

		OLE_SetDocumentVar(hWord,'nItens_Proposta',alltrim(Str(nI)))
		OLE_ExecuteMacro(hWord,"Itens_Proposta")

	Endif


	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Proposta de Servicos               ณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู

	DbSelectArea("AF1")
	DbSetOrder(4)

	If DbSeek(xFilial("AF1")+cProposta)

		DbSelectArea("AF5")
		DbSetOrder(1)

		If DbSeek(xFilial("AF5")+AF1->AF1_ORCAME)
			OLE_SetDocumentVar(hWord,"cLine",AllTrim(AF5->AF5_DESCRI))
			While AF5->(!EOF()) .AND.  xFilial("AF5")+ AF1->AF1_ORCAME == AF5_FILIAL + AF5_ORCAME

				nY++

				If AF5->AF5_STATUS <> '2'

					If Len(AF5_EDT) == 2
						OLE_SetDocumentVar(hWord,"cLine"+Alltrim(str(nY)),AllTrim(AF5->AF5_DESCRI))
					End
					If Len(AF5_EDT) > 2
						OLE_SetDocumentVar(hWord,"cLine"+Alltrim(str(nY)),AllTrim(AF5->AF5_DESCRI))
						DbSelectArea("AF2")
						DbSetOrder(2)
						If  DbSeek(xFilial("AF2")+AF5->AF5_ORCAME+AF5->AF5_EDT)
							While AF2->(!EOF()) .AND. xFilial("AF2")+ AF5->AF5_ORCAME + AF5->AF5_EDT == AF2_FILIAL + AF2_ORCAME + AF2_EDTPAI
								nY++

								OLE_SetDocumentVar(hWord,"cLine"+Alltrim(str(nY)),Space(2)+AllTrim(AF2->AF2_DESCRI))
								AF2->(DbSkip())
							End
						EndIf
					EndIf
				EndIf
				AF5->(DbSkip())
			End

		EndIf

	EndIf


	If nY > 0

		OLE_SetDocumentVar(hWord,'nItens_PServico',alltrim(Str(nY)))
		OLE_ExecuteMacro(hWord,"Itens_PServico")

	Endif


	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Atualiza a condicoes de pagamento  ณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู

	For nX := 1 To Len(aCronoFin)

		OLE_SetDocumentVar(hWord,'cParcela'+Alltrim(str(nX)),aCronoFin[nX][1])
		OLE_SetDocumentVar(hWord,'dVencto'+Alltrim(str(nX)) ,aCronoFin[nX][2])
		OLE_SetDocumentVar(hWord,'nValor'+Alltrim(str(nX)) ,Transform(aCronoFin[nX][3],"@E 999,999,999.99"))

		nCount++

	Next nX

	If nCount > 0

		OLE_SetDocumentVar(hWord,'nItens_Cond_Pgto',alltrim(Str(nCount)))
		OLE_ExecuteMacro(hWord,"Cond_Pgto")

	Endif

	RestArea(aARea)

Return

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออออปฑฑ
ฑฑบPrograma  ณFt601Rev  บAutor  ณVendas CRM			 บ Data ณ  29/12/10   บฑฑ
ฑฑฬออออออออออุออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออออนฑฑ
ฑฑบDesc.     ณCria revisao do documento.                                  บฑฑ
ฑฑฬออออออออออุออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณ Ft601Exe                                                   บฑฑ
ฑฑศออออออออออฯออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/

Static Function Ft601Rev(cProposta)

	Local cLocRev		:= '' 	   				//Localiza a se existe docs de revisao no servidor
	Local cRevisao 		:= '' 					//Revisao do documento
	Local cNomeWord		:= "P"+cProposta   		//P+Numero da Proposta
	Local nCount 		:= 1  					//Incremento


	DbSelectArea("ACB")
	DbSetOrder(2)

	If !DbSeek(xFilial("ACB")+Upper(cNomeWord+'.doc'))
		cRevisao := cNomeWord
		Return(cRevisao)
	Else
		While ACB->(!Eof())
			cLocRev := ' - R'+cValToChar(nCount)
			If !DbSeek(xFilial("ACB")+Upper(cNomeWord+cLocRev+'.doc'))
				cRevisao := cNomeWord+cLocRev
				Exit
			EndIf
			nCount++
			ACB->(DbSkip())
		End
	EndIf

Return(cRevisao)

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัอออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออออปฑฑ
ฑฑบPrograma  ณFt601Tip09 บAutor  ณVendas CRM          บ Data ณ  12/01/11   บฑฑ
ฑฑฬออออออออออุอออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออออนฑฑ
ฑฑบDesc.     ณInicializa o vetor aTipo09 com as parcelas previamente       บฑฑ
ฑฑบ          ณsalvas.                                                      บฑฑ
ฑฑฬออออออออออุอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณFt601Exe                                                     บฑฑ
ฑฑศออออออออออฯอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/
Static Function Ft601Tip09(cProposta,cPRevisa)

	Local aArea		:= GetArea()
	Local aAreaSCJ	:= SCJ->(GetArea())
	Local aAreaSCK	:= SCK->(GetArea())
	Local aProdutos := {}
	Local aTipo09	:= {}
	Local nIt		:= 0
	Local nNumParc	:= SuperGetMv("MV_NUMPARC")
	Local cProxParc	:= ""
	Local dDtVenc	:= Nil
	Local nVlParc	:= 0
	Local nPc		:= 0


	dbSelectArea("SE4")
	dbSetOrder(1)

	DbSelectarea("SCJ")
	DbSetOrder(1)

	DbSelectArea("SCK")
	DbSetOrder(1)


	DbSelectArea("ADZ")
	DbSetOrder(3)

	If dbSeek(xFilial("ADZ")+cProposta+cPRevisa)

		While ADZ->(!EOF()) .AND. ADZ_FILIAL == xFilial("ADZ")  .AND. ADZ_PROPOS == cProposta
			aAdd(aProdutos,{ADZ_PRODUT,ADZ_ORCAME,ADZ_ITEMOR,ADZ_ITEM})
			ADZ->(DbSkip())
		End

	EndIf

	For nIt := 1 to Len(aProdutos)

		If  SCK->(DbSeek(xFilial("SCK") + aProdutos[nIt][02] + aProdutos[nIt][03] + aProdutos[nIt][01]))

			SCJ->(DbSeek(xFilial("SCJ") + SCK->CK_NUM + SCK->CK_CLIENTE + SCK->CK_LOJA ))

			SE4->(DbSeek(xFilial("SE4") + SCJ->CJ_CONDPAG))

			If	SE4->E4_TIPO == "9"

				cProxParc := "0"

				For nPc:=1 To nNumParc

					cProxParc := Soma1(cProxParc)

					dDtVenc := &("SCJ->CJ_DATA"+cProxParc)
					nVlParc	:= &("SCJ->CJ_PARC"+cProxParc)

					If	nVlParc > 0
						aadd( aTipo09,{SCK->CK_PRODUTO, dDtVenc , nVlParc ,SCJ->CJ_CONDPAG, aProdutos[nIt][04] } )
					Endif

				Next

			Endif

		EndIf

	Next nIt

	RestArea(aAreaSCJ)
	RestArea(aAreaSCK)
	RestArea(aArea)

Return(aTipo09)




/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัออออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออออปฑฑ
ฑฑบPrograma  ณFt601CroFin บAutor  ณVendas CRM          บ Data ณ  12/01/11   บฑฑ
ฑฑฬออออออออออุออออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออออนฑฑ
ฑฑบDesc.     ณMonta o Cronograma Financeiro.								บฑฑ
ฑฑฬออออออออออุออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณFt601Exe                                                      บฑฑ
ฑฑศออออออออออฯออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/
Static Function  Ft601CroFin(cProposta,cPRevisa,aTipo09)

	Local aArea			:= GetArea()
	Local aVencto 		:= {}
	Local aCronoAtu		:= {}
	Local nC			:= 0
	Local nA			:= 0
	Local nI			:= 0
	Local nPosData		:= 0
	Local cTipoPar		:= SuperGetMv("MV_1DUP")
	Local cSequencia    := " "
	Local aProdutos		:= {}
	Local aCronoFin		:= {}


	DbSelectArea("ADZ")
	DbSetOrder(3)

	If dbSeek(xFilial("ADZ")+cProposta+cPRevisa)

		While ADZ->(!EOF()) .AND. ADZ_FILIAL == xFilial("ADZ")  .AND. ADZ_PROPOS == cProposta
			aAdd(aProdutos,{ADZ_PRODUT,ADZ_TOTAL,ADZ_CONDPG,ADZ_DT1VEN})
			ADZ->(DbSkip())
		End

	EndIf


	For nI:=1 To Len(aProdutos)

		dbSelectArea("SE4")
		dbSetOrder(1)
		IF	dbSeek(xFilial("SE4")+aProdutos[nI][03])

			If	E4_TIPO <> "9"

				//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
				//ณ Atualiza cronograma financeiro para condicao diferente do tipo 9ณ
				//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
				aVencto := Condicao(aProdutos[nI][02],aProdutos[nI][03],0,dDatabase,0)

				For nA:=1 To Len(aVencto)

					If	!Empty(aProdutos[nI][04]) .AND. aProdutos[nI][04] <> dDataBase .AND. nA == 1
						aVencto[nA,1] := aProdutos[nI][04]
					Endif

					nPosData := aScan( aCronoAtu, { |x| x[1] == aVencto[nA,1] } )

					If	nPosData == 0
						aadd(aCronoAtu,{aVencto[nA,1],aVencto[nA,2]})
					Else
						aCronoAtu[nPosData,2] += aVencto[nA,2]
					Endif

				Next nA

			Endif

		Endif

	Next nI

	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Atualiza cronograma financeiro para condicao de pagamento tipo 9ณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
	If	Len(aTipo09)>0

		For nA:=1 To Len(aTipo09)

			If	Len(aCronoAtu)>0
				nPosData := aScan( aCronoAtu, { |x| x[1] == aTipo09[nA,2] } )
			Else
				nPosData := 0
			Endif

			If	nPosData == 0
				aadd(aCronoAtu,{aTipo09[nA,2],aTipo09[nA,3]})
			Else
				aCronoAtu[nPosData,2] += aTipo09[nA,3]
			Endif

		Next nA

	Endif

	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Trata o iniciador da parcela inicial ณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
	If	cTipoPar == "A"
		cSequencia	:= "9"
	Else
		cSequencia	:= "0"
	Endif

	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Ordena as parcelas pela data de vencimento ณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
	aCronoAtu := ASort(aCronoAtu,,,{|parc1,parc2|parc1[1]<parc2[1]})

	//ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
	//ณ Atualiza cronograma financeiro ณ
	//ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
	For nC:=1 To Len(aCronoAtu)

		cSequencia := Soma1(cSequencia)

		If	nC == 1
			aadd(aCronoFin,{"",CtoD(Space(8)),0})
			aCronoFin[nC,1] := cSequencia
			aCronoFin[nC,2] := aCronoAtu[nC,1]
			aCronoFin[nC,3] := aCronoAtu[nC,2]
		Else
			AAdd(aCronoFin,{cSequencia,aCronoAtu[nC,1],aCronoAtu[nC,2] })
		Endif

	Next nC

	RestArea(aArea)

Return(aCronoFin)
