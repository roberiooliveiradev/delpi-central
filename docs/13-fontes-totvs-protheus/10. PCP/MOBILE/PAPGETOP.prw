#Include "TOTVS.CH"
#Include "TopConn.CH"

/*/{Protheus.doc} PApGetOP
Manipula o JSON retornado para o app Minha Producao.
1. Envia campos customizados (CCCA)
2. Busca e preenche a Ferramenta Padrao (SHY)
/*/
User Function PApGetOP()
    Local cTipo      := PARAMIXB[1] // Tipo de Apontamento (1, 3 ou 4)
    Local cJsRet     := PARAMIXB[2] // String JSON original da TOTVS
    Local cReqSource := ""
    
    // Variaveis para a regra da ferramenta
    Local cOP        := ""
    Local cOperac    := ""
    Local cFerra     := ""
    Local cQuery     := ""
    Local cAliasQ    := GetNextAlias()
    
    Local oJsRet     := JsonObject():New()

    // Protecao: Garante que PARAMIXB tem tamanho suficiente antes de ler a posicao 4
    If Len(PARAMIXB) >= 4
        cReqSource := PARAMIXB[4]
    EndIf

    // Converte a string JSON para objeto JSON
    oJsRet:FromJson(cJsRet)

    IF cTipo == "3" // Apontamento Modelo 2 (MATA681)

        // ====================================================================
        // 1. REGRA ORIGINAL: Campos Customizados (com protecao de Type)
        // O Type("M->...") evita que o sistema quebre caso a variavel de 
        // memoria nao exista durante a chamada da API REST.
        // ====================================================================
        If Type("M->H6_CCCA01") != "U" // "U" = Undefined (Nao existe)
            oJsRet["CustomFieldCharacter01"] := M->H6_CCCA01
        EndIf
        
        If Type("M->H6_CCCA02") != "U"
            oJsRet["CustomFieldCharacter02"] := ALLTRIM(M->H6_CCCA02)
        EndIf
        
        If Type("M->H6_CCCA03") != "U"
            oJsRet["CustomFieldCharacter03"] := ALLTRIM(M->H6_CCCA03)
        EndIf


        // ====================================================================
        // 2. NOVA REGRA: Busca a Ferramenta Padrao na SHY e injeta no App
        // ====================================================================
        If cReqSource == "QU" .Or. cReqSource == "AV" .Or. Empty(cReqSource)
            
            // Extrai a OP e Operacao do proprio JSON que o Protheus gerou
            If ValType(oJsRet["ProductionOrderNumber"]) == "C"
                cOP := oJsRet["ProductionOrderNumber"]
            EndIf
            
            If ValType(oJsRet["ActivityCode"]) == "C"
                cOperac := oJsRet["ActivityCode"]
            EndIf

            // Busca na SHY apenas se tiver OP e Operacao
            If !Empty(cOP) .And. !Empty(cOperac)
                cQuery := " SELECT HY_FERRAM FROM " + RetSqlName("SHY") + " SHY "
                cQuery += " WHERE SHY.HY_FILIAL = '" + xFilial("SHY") + "' "
                cQuery += " AND SHY.HY_OP = '" + cOP + "' "
                cQuery += " AND SHY.HY_OPERAC = '" + cOperac + "' "
                cQuery += " AND SHY.D_E_L_E_T_ = ' ' "

                cQuery := ChangeQuery(cQuery)
                dbUseArea( .T., "TOPCONN", TcGenQry( ,, cQuery ), cAliasQ, .F., .T. )

                If !(cAliasQ)->(Eof())
                    cFerra := (cAliasQ)->HY_FERRAM
                EndIf
                (cAliasQ)->(dbCloseArea())

                // Injeta a ferramenta encontrada na tag oficial do aplicativo
                If !Empty(cFerra)
                    oJsRet["ToolCode"] := cFerra
                EndIf
            EndIf
        EndIf

    ENDIF

    // Converte o objeto Json com as informacoes manipuladas em uma String Json
    cJsRet := oJsRet:ToJson()

    // Limpa da memoria o objeto Json utilizado
    FreeObj(oJsRet)

Return cJsRet
