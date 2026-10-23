#Include "PROTHEUS.CH"
#Include "TOTVS.CH"
#Include "FWMVCDEF.CH"

/*/{Protheus.doc} TK260ROT
    Ponto de Entrada da rotina TMKA260 (Cadastro de Prospects)
    Adiciona opcao "Qualificar" ao menu de opcoes do browse

    @type  Function
    @author Delpi - MIT044
    @since 11/03/2026
    @version 12.1.2410
    @return aRet, Array, Array com opcoes adicionais para o menu
/*/
User Function TK260ROT()

	Local aRet := {}

	aAdd(aRet, {"Qualificar", "U_DLP73Q1", 0, 2})

Return aRet


/*/{Protheus.doc} DLP73Q1
    Funcao de qualificacao manual de Prospect (SUS) para Cliente (SA1)
    Replica os dados do prospect para o cadastro de clientes via ExecAuto CRMA980
    e atualiza o status do prospect apos a conversao

    @type  Function
    @author Delpi - MIT044
    @since 11/03/2026
    @version 12.1.2410
    @table SUS, SA1, AI0
/*/
User Function DLP73Q1()

	Local aArea     := GetArea()
	Local aAreaSUS  := SUS->(GetArea())
	Local aSA1Auto  := {}
	Local aAI0Auto  := {}
	Local cCodProsp := SUS->US_COD
	Local cLojProsp := SUS->US_LOJA
	Local cCodCli   := ""
	Local cLojCli   := "01"
	Local cCGC      := AllTrim(SUS->US_CGC)
	Local aPergs    := {}
	Local aParamRet := {}
	Local cConta    := Space(20)
	Local cCodPais  := PadR("01058", 5)
	Local cBlEmail  := "1"
	Local aMiss     := {}
	Local cMiss     := ""
	Local nI        := 0
	Local cFunBkp   := FunName()

	Private lMsErroAuto := .F.
	Private l030Auto    := .F.

	//-----------------------------------------------
	// Passo 1 - Validacoes
	//-----------------------------------------------
	If Empty(cCodProsp)
		FWAlertError("Nenhum prospect selecionado.", "Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	If SUS->US_STATUS == "6" .Or. !Empty(SUS->US_CODCLI)
		FWAlertWarning("Este prospect ja foi qualificado." + CRLF + ;
			"Cliente: " + AllTrim(SUS->US_CODCLI) + "/" + AllTrim(SUS->US_LOJACLI), ;
			"Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	// Verifica se prospect tem CNPJ/CPF (obrigatorio para localizar cliente apos inclusao)
	If Empty(cCGC)
		FWAlertError("O prospect nao possui CNPJ/CPF preenchido." + CRLF + ;
			"Preencha o campo CNPJ/CPF no prospect antes de qualificar.", ;
			"Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	// Verifica se ja existe cliente com mesmo CNPJ/CPF
	DbSelectArea("SA1")
	DbSetOrder(3) // A1_FILIAL + A1_CGC
	If DbSeek(xFilial("SA1") + cCGC)
		FWAlertWarning("Ja existe um cliente com este CNPJ/CPF." + CRLF + ;
			"Cliente: " + AllTrim(SA1->A1_COD) + "/" + AllTrim(SA1->A1_LOJA) + CRLF + ;
			"Nome: " + AllTrim(SA1->A1_NOME), ;
			"Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	//-----------------------------------------------
	// Passo 2 - Validar campos obrigatorios do prospect
	//-----------------------------------------------
	aMiss := f73VldObrig()

	If Len(aMiss) > 0
		cMiss := "Campos obrigatorios vazios no prospect:" + CRLF + CRLF
		For nI := 1 To Len(aMiss)
			cMiss += "- " + aMiss[nI] + CRLF
		Next
		cMiss += CRLF + "Preencha estes campos no prospect antes de qualificar."
		FWAlertError(cMiss, "Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	//-----------------------------------------------
	// Passo 3 - Confirmacao do usuario
	//-----------------------------------------------
	If !FWAlertYesNo("Deseja qualificar o prospect " + AllTrim(SUS->US_NOME) + ;
			" como cliente?", "Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	//-----------------------------------------------
	// Passo 4 - Solicitar dados complementares
	//-----------------------------------------------
	aAdd(aPergs, {1, "Conta Contabil", cConta, "@!", ".T.", "CT1", ".T.", 80, .T.})
	aAdd(aPergs, {1, "Pais Bacen", cCodPais, "@!", ".T.", "SYA", ".T.", 80, .T.})
	aAdd(aPergs, {2, "Boleto Email", cBlEmail, {"1=Sim", "2=Nao"}, 80, ".T.", .T.})

	If !ParamBox(aPergs, "Dados Complementares", @aParamRet,,,,,,, .F., .F.)
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	cConta   := aParamRet[1]
	cCodPais := aParamRet[2]
	cBlEmail := aParamRet[3]

	If Empty(cConta) .Or. Empty(cCodPais) .Or. Empty(cBlEmail)
		FWAlertError("Todos os campos complementares sao obrigatorios.", "Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	//-----------------------------------------------
	// Passo 5 - Montar array De-Para Prospect->Cliente
	//-----------------------------------------------
	aSA1Auto := f73MontSA1(cLojCli, cConta, cCodPais, cBlEmail)

	//-----------------------------------------------
	// Passo 6 - Inclusao do cliente via MSExecAuto CRMA980
	//-----------------------------------------------
	MSExecAuto({|a,b,c| CRMA980(a,b,c)}, aSA1Auto, MODEL_OPERATION_INSERT, aAI0Auto)

	If lMsErroAuto
		MostraErro()
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	//-----------------------------------------------
	// Passo 7 - Obter codigo do cliente gerado via CNPJ (indice 3)
	//-----------------------------------------------
	DbSelectArea("SA1")
	DbSetOrder(3) // A1_FILIAL + A1_CGC
	If DbSeek(xFilial("SA1") + cCGC)
		cCodCli := SA1->A1_COD
		cLojCli := SA1->A1_LOJA
	EndIf

	If Empty(cCodCli)
		FWAlertError("Nao foi possivel localizar o cliente gerado.", ;
			"Qualificacao de Prospect")
		RestArea(aAreaSUS)
		RestArea(aArea)
		Return
	EndIf

	//-----------------------------------------------
	// Passo 8 - Atualizar o prospect (SUS)
	//-----------------------------------------------
	If !f73AtuSUS(cCodProsp, cLojProsp, cCodCli, cLojCli)
		FWAlertWarning("Cliente gerado com sucesso, porem nao foi possivel " + ;
			"atualizar o prospect (registro bloqueado)." + CRLF + ;
			"Atualize manualmente o prospect " + AllTrim(cCodProsp) + ".", ;
			"Qualificacao de Prospect")
	EndIf

	FWAlertSuccess("Cliente gerado com sucesso!" + CRLF + CRLF + ;
		"Codigo: " + AllTrim(cCodCli) + CRLF + ;
		"Loja: " + cLojCli + CRLF + CRLF + ;
		"A tela de clientes sera aberta para complementar os dados.", ;
		"Qualificacao de Prospect")

	//-----------------------------------------------
	// Passo 9 - Abrir tela CRMA980 para complementar dados
	//-----------------------------------------------
	DbSelectArea("SA1")
	DbSetOrder(1)
	If DbSeek(xFilial("SA1") + cCodCli + cLojCli)
		SetFunName("CRMA980")
		FWExecView("Complementar Cliente", "CRMA980", MODEL_OPERATION_UPDATE, , {|| .T.})
		SetFunName(cFunBkp)
	EndIf

	RestArea(aAreaSUS)
	RestArea(aArea)

Return


/*/{Protheus.doc} f73MontSA1
    Monta o array de campos SA1 com os dados do prospect (SUS)
    para uso no ExecAuto do CRMA980

    @type  Static Function
    @author Delpi - MIT044
    @since 11/03/2026
    @version 12.1.2410
    @param cLojCli, Character, Loja do cliente a ser gerado
    @param cConta, Character, Conta contabil (A1_CONTA)
    @param cCodPais, Character, Codigo BACEN do pais (A1_CODPAIS)
    @param cBlEmail, Character, Email para boleto (A1_BLEMAIL)
    @return aSA1, Array, Array no formato {campo, valor, Nil}
/*/
Static Function f73MontSA1(cLojCli, cConta, cCodPais, cBlEmail)

	Local aSA1 := {}

	// Loja e Conta Contabil sao obrigatorias, sempre envia
	aAdd(aSA1, {"A1_LOJA", f73PadFld("A1_LOJA", cLojCli), Nil})
	aAdd(aSA1, {"A1_CONTA", f73PadFld("A1_CONTA", cConta), Nil})
	aAdd(aSA1, {"A1_CODPAIS", f73PadFld("A1_CODPAIS", cCodPais), Nil})
	aAdd(aSA1, {"A1_BLEMAIL", f73PadFld("A1_BLEMAIL", cBlEmail), Nil})

	// Campos texto - so adiciona se preenchido no prospect
	f73AddFld(aSA1, "A1_NOME"   , SUS->US_NOME)
	f73AddFld(aSA1, "A1_NREDUZ" , SUS->US_NREDUZ)
	f73AddFld(aSA1, "A1_TIPO"   , SUS->US_TIPO)

	// Pessoa: se vazio, infere pelo tamanho do CGC (CNPJ=14 -> J, CPF=11 -> F)
	If !Empty(SUS->US_PESSOA)
		f73AddFld(aSA1, "A1_PESSOA", SUS->US_PESSOA)
	ElseIf !Empty(SUS->US_CGC)
		If Len(AllTrim(SUS->US_CGC)) > 11
			aAdd(aSA1, {"A1_PESSOA", "J", Nil})
		Else
			aAdd(aSA1, {"A1_PESSOA", "F", Nil})
		EndIf
	EndIf

	f73AddFld(aSA1, "A1_CGC"    , SUS->US_CGC)
	f73AddFld(aSA1, "A1_DDI"    , SUS->US_DDI)
	f73AddFld(aSA1, "A1_DDD"    , SUS->US_DDD)
	f73AddFld(aSA1, "A1_TEL"    , SUS->US_TEL)
	f73AddFld(aSA1, "A1_FAX"    , SUS->US_FAX)
	f73AddFld(aSA1, "A1_EMAIL"  , SUS->US_EMAIL)
	f73AddFld(aSA1, "A1_HPAGE"  , SUS->US_URL)
	f73AddFld(aSA1, "A1_END"    , SUS->US_END)
	f73AddFld(aSA1, "A1_BAIRRO" , SUS->US_BAIRRO)
	f73AddFld(aSA1, "A1_CEP"    , SUS->US_CEP)
	f73AddFld(aSA1, "A1_EST"    , SUS->US_EST)
	f73AddFld(aSA1, "A1_COD_MUN", SUS->US_COD_MUN)
	f73AddFld(aSA1, "A1_MUN"    , SUS->US_MUN)
	f73AddFld(aSA1, "A1_REGIAO" , SUS->US_REGIAO)
	f73AddFld(aSA1, "A1_DSCREG" , SUS->US_DSCREG)
	f73AddFld(aSA1, "A1_PAIS"   , SUS->US_PAIS)
	f73AddFld(aSA1, "A1_CNAE"   , SUS->US_CNAE)
	f73AddFld(aSA1, "A1_VEND"   , SUS->US_VEND)
	f73AddFld(aSA1, "A1_INSCR"  , SUS->US_INSCR)
	f73AddFld(aSA1, "A1_GRPTRIB", SUS->US_GRPTRIB)
	f73AddFld(aSA1, "A1_NATUREZ", SUS->US_NATUREZ)
	f73AddFld(aSA1, "A1_SUFRAMA", SUS->US_SUFRAMA)
	f73AddFld(aSA1, "A1_TPESSOA", SUS->US_TPESSOA)
	f73AddFld(aSA1, "A1_CONTRIB", SUS->US_CONTRIB)
	f73AddFld(aSA1, "A1_OBSERV" , SUS->US_OBS)

	// Campos numericos/data - so adiciona se preenchido
	If SUS->US_LC > 0
		aAdd(aSA1, {"A1_LC", SUS->US_LC, Nil})
	EndIf
	If !Empty(SUS->US_VENCLC)
		aAdd(aSA1, {"A1_VENCLC", SUS->US_VENCLC, Nil})
	EndIf
	If SUS->US_MOEDALC > 0
		aAdd(aSA1, {"A1_MOEDALC", SUS->US_MOEDALC, Nil})
	EndIf

Return aSA1


/*/{Protheus.doc} f73AddFld
    Adiciona campo texto ao array do ExecAuto somente se o valor
    estiver preenchido, ajustando ao tamanho do campo destino

    @type  Static Function
    @author Delpi - MIT044
    @since 11/03/2026
    @version 12.1.2410
    @param aSA1, Array, Array de campos do ExecAuto (passado por referencia)
    @param cField, Character, Nome do campo destino (SA1)
    @param xValue, Character, Valor do campo origem (SUS)
/*/
Static Function f73AddFld(aSA1, cField, xValue)

	If !Empty(xValue)
		aAdd(aSA1, {cField, f73PadFld(cField, xValue), Nil})
	EndIf

Return


/*/{Protheus.doc} f73PadFld
    Ajusta valor texto ao tamanho do campo destino na SA1
    usando PadR com o tamanho definido no SX3

    @type  Static Function
    @author Delpi - MIT044
    @since 11/03/2026
    @version 12.1.2410
    @param cField, Character, Nome do campo destino (SA1)
    @param xValue, Character, Valor a ser ajustado
    @return cRet, Character, Valor ajustado ao tamanho do campo
/*/
Static Function f73PadFld(cField, xValue)

	Local nTam := GetSx3Cache(cField, "X3_TAMANHO")

Return PadR(xValue, nTam)


/*/{Protheus.doc} f73VldObrig
    Valida campos obrigatorios da SA1 que vem do prospect (SUS).
    Consulta X3_OBRIGAT no SX3 para cada campo mapeado e retorna
    a lista de campos obrigatorios que estao vazios no prospect.

    @type  Static Function
    @author Delpi - MIT044
    @since 15/03/2026
    @version 12.1.2410
    @return aMiss, Array, Lista de descricoes dos campos faltantes
/*/
Static Function f73VldObrig()

	Local aVld    := {}
	Local aMiss   := {}
	Local nI      := 0
	Local cTitulo := ""

	// Mapeamento: campo SA1 -> valor do prospect SUS
	aAdd(aVld, {"A1_NOME"   , SUS->US_NOME})
	aAdd(aVld, {"A1_NREDUZ" , SUS->US_NREDUZ})
	aAdd(aVld, {"A1_TIPO"   , SUS->US_TIPO})
	aAdd(aVld, {"A1_CGC"    , SUS->US_CGC})
	aAdd(aVld, {"A1_DDI"    , SUS->US_DDI})
	aAdd(aVld, {"A1_DDD"    , SUS->US_DDD})
	aAdd(aVld, {"A1_TEL"    , SUS->US_TEL})
	aAdd(aVld, {"A1_FAX"    , SUS->US_FAX})
	aAdd(aVld, {"A1_EMAIL"  , SUS->US_EMAIL})
	aAdd(aVld, {"A1_HPAGE"  , SUS->US_URL})
	aAdd(aVld, {"A1_END"    , SUS->US_END})
	aAdd(aVld, {"A1_BAIRRO" , SUS->US_BAIRRO})
	aAdd(aVld, {"A1_CEP"    , SUS->US_CEP})
	aAdd(aVld, {"A1_EST"    , SUS->US_EST})
	aAdd(aVld, {"A1_COD_MUN", SUS->US_COD_MUN})
	aAdd(aVld, {"A1_MUN"    , SUS->US_MUN})
	aAdd(aVld, {"A1_REGIAO" , SUS->US_REGIAO})
	aAdd(aVld, {"A1_PAIS"   , SUS->US_PAIS})
	aAdd(aVld, {"A1_CNAE"   , SUS->US_CNAE})
	aAdd(aVld, {"A1_VEND"   , SUS->US_VEND})
	aAdd(aVld, {"A1_INSCR"  , SUS->US_INSCR})
	aAdd(aVld, {"A1_GRPTRIB", SUS->US_GRPTRIB})
	aAdd(aVld, {"A1_NATUREZ", SUS->US_NATUREZ})
	aAdd(aVld, {"A1_SUFRAMA", SUS->US_SUFRAMA})
	aAdd(aVld, {"A1_TPESSOA", SUS->US_TPESSOA})
	aAdd(aVld, {"A1_CONTRIB", SUS->US_CONTRIB})

	For nI := 1 To Len(aVld)
		If X3Obrigat(aVld[nI][1]) .And. Empty(aVld[nI][2])
			cTitulo := AllTrim(GetSx3Cache(aVld[nI][1], "X3_TITULO"))
			aAdd(aMiss, cTitulo + " (" + aVld[nI][1] + ")")
		EndIf
	Next

Return aMiss


/*/{Protheus.doc} f73AtuSUS
    Atualiza o registro do prospect (SUS) apos a qualificacao
    com os dados do cliente gerado

    @type  Static Function
    @author Delpi - MIT044
    @since 11/03/2026
    @version 12.1.2410
    @param cCodProsp, Character, Codigo do prospect
    @param cLojProsp, Character, Loja do prospect
    @param cCodCli, Character, Codigo do cliente gerado
    @param cLojCli, Character, Loja do cliente gerado
    @return lRet, Logical, .T. se atualizou com sucesso, .F. se falhou
/*/
Static Function f73AtuSUS(cCodProsp, cLojProsp, cCodCli, cLojCli)

	Local lRet := .F.

	DbSelectArea("SUS")
	DbSetOrder(1)
	If DbSeek(xFilial("SUS") + cCodProsp + cLojProsp)
		If RecLock("SUS", .F.)
			SUS->US_CODCLI  := cCodCli
			SUS->US_LOJACLI := cLojCli
			SUS->US_STATUS  := "6"
			SUS->US_DTCONV  := dDataBase
			SUS->US_HRCONV  := Time()
			SUS->US_MSBLQL  := "1" // Inativo
			MsUnlock()
			lRet := .T.
		EndIf
	EndIf

Return lRet
