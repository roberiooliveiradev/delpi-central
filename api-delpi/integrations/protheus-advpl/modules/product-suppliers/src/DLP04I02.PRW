/* ========================================================================
   DLP04I02.PRW — Api REST para Produto x Fornecedor (SA5) via modelo MVC
   oficial DMATA061 (MATA061 — cadastro Produto x Fornecedor, Model-2).
   -----------------------------------------------------------------------
   ESTADO: SOURCE_CANDIDATE — aguardando revisao e compilacao pela equipe ERP.

   PROVENIENCIA:
     modelo oficial: Delpi-ti/protheus-erp @ master — "73. CRM/Dmata061.prx"
     espelho: docs/13-fontes-totvs-protheus/73. CRM/Dmata061.prx
              blob b45cc9333c410a58d5836f78b79a140c6056c9c6 (commit be614649b7)
     comparacao : "73. CRM/MATA010M_DLP.PRW" (blob a56c2a5079991742a544c39dd…)
     upstream_sha: INCONCLUSIVE (repo privado nao revalidado nesta sessao)
     inventario : contracts/official-model-inventory.md (G2-B)

   MECANISMO: fachada WSRESTFUL instanciando o MODELO MVC oficial
   'DMATA061' — nunca RecLock, SQL ou DbWrite sobre SA5. As validacoes,
   triggers e pontos de entrada do cadastro oficial (a060LinOk,
   a060VldGrv, MT061MN, SX3) executam no ciclo do modelo.

   CLASSIFICACAO POR OPERACAO (sem fingimento de contrato):
     CREATE (POST)  = SOURCE_IMPLEMENTED — ciclo MPFormModel documentado
                      + ids/chave comprovados no fonte do modelo.
     UPDATE (PUT)   = CONTRACT_CANDIDATE — inclui chamada de carga da
                      linha existente cuja assinatura exata depende de
                      confirmacao (VALIDAR NO TST01).
     READ (GET)     = TO_INVENTORY — sem rotina oficial de leitura REST;
                      retorna 501 explicito. Leitura segue na superficie
                      SQL governada da api-delpi (evidencia auxiliar,
                      separada desta fachada).
     DELETE         = BLOCKED — a060VldGrv oficial rejeita salvar modelo
                      com todas as linhas excluidas (ultimo vinculo);
                      o mesmo callback tambem rejeita GRID VAZIO
                      (Length()==0): inclusao exige sempre uma linha e
                      UPDATE falha fechado se a linha nao carregar.
                      Semantica de exclusao pendente de ratificacao.
                      Retorna 501 explicito — nunca RecLock/DbDelete.

   IDENTIDADE SA5 (PK oficial do modelo — imutavel em UPDATE):
     A5_FILIAL(ctx xFilial) + A5_FORNECE + A5_LOJA + A5_PRODUTO +
     A5_FABR + A5_FALOJA + A5_REFGRD
     A5_FILIAL NAO vem do body — derivada por xFilial("SA5") no relation
     oficial do modelo (contexto empresa/filial da sessao REST).

   LIMITES / VALIDAR NO TST01:
     - Assinatura exata de Load() do MPFormModel para carga da linha
       existente (UPDATE) — parametros marcados VALIDAR NO TST01.
     - a060LinOk executa o dup-check apenas em isInserted() e le
       M->A5_PRODUTO/M->A5_REFGRD (contexto de tela): em REST sem view,
       M-> e indefinido — dup-check pode validar chave incompleta ou
       falhar. Sem preencher memvars artificialmente (proibido pela
       task); comportamento exato = VALIDAR NO TST01.
     - a060VldGrv chama Help() (UI): comportamento fora de tela =
       VALIDAR NO TST01.
     - API de erro do modelo (GetErrorMessage) = VALIDAR NO TST01.
     - Presenca compilada do modelo 'DMATA061' e PEs ativos no RPO.
     - Compilacao/homologacao: pendente (TST01, equipe ERP).
   ======================================================================== */

#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.ch"

WSRESTFUL DelpiProdForn DESCRIPTION "Api REST Produto x Fornecedor (SA5)" FORMAT "application/json"

    WSMETHOD POST   sa5Prod  DESCRIPTION 'Inclui vinculo Produto x Fornecedor'   PATH '/v1/ProdForn/incluir'   WSSYNTAX '/v1/ProdForn/incluir'   TTALK "v1"
    WSMETHOD PUT    sa5Prod  DESCRIPTION 'Altera vinculo Produto x Fornecedor'   PATH '/v1/ProdForn/alterar'   WSSYNTAX '/v1/ProdForn/alterar'   TTALK "v1"
    WSMETHOD GET    sa5Prod  DESCRIPTION 'Consulta vinculo (nao implementado)'   PATH '/v1/ProdForn/consultar' WSSYNTAX '/v1/ProdForn/consultar' TTALK "v1"
    WSMETHOD DELETE sa5Prod  DESCRIPTION 'Exclui vinculo (bloqueado — semantica pendente)' PATH '/v1/ProdForn/excluir' WSSYNTAX '/v1/ProdForn/excluir' TTALK "v1"

END WSRESTFUL

/* -----------------------------------------------------------------------
   Campos de identidade recebidos no body (A5_FILIAL derivada por xFilial
   na relation oficial do modelo — nunca informada pelo consumidor).
   ----------------------------------------------------------------------- */
static function aSA5Ident()

Return {"A5_PRODUTO", "A5_FORNECE", "A5_LOJA", "A5_FABR", "A5_FALOJA", "A5_REFGRD"}

// atributos editaveis do vinculo (restante e derivado pelo ERP/validacao)
static function aSA5Attrs()

Return {"A5_NOMEFOR", "A5_CODPRF", "A5_DESCPRF"}

/* -----------------------------------------------------------------------
   lPrepSA5 — valida presenca/tipo da identidade completa e dos atributos.
   Retorna .T. ou .F. com cErro listando campos ausentes/nulos/invalidos.
   Sem conversao de tipo, sem default inventado, sem consulta SQL.
   ----------------------------------------------------------------------- */
static function lPrepSA5(oDados, aMiss, cErro)

    local aReq  := aSA5Ident()
    local aAttr := aSA5Attrs()
    local nI    := 0
    local lOk   := .T.
    local xVal  := NIL

    for nI := 1 to len(aReq)
        xVal := oDados:GetJSonObject(aReq[nI])
        if ValType(xVal) == "U" .or. ValType(xVal) <> "C" .or. Empty(xVal)
            aadd(aMiss, aReq[nI] + iif(ValType(xVal) <> "U" .and. ValType(xVal) <> "C", "(tipo " + ValType(xVal) + ")", ""))
            lOk := .F.
        endif
    next nI

    for nI := 1 to len(aAttr)
        xVal := oDados:GetJSonObject(aAttr[nI])
        if ValType(xVal) == "U" .or. ValType(xVal) <> "C"
            aadd(aMiss, aAttr[nI] + iif(ValType(xVal) <> "U" .and. ValType(xVal) <> "C", "(tipo " + ValType(xVal) + ")", ""))
            lOk := .F.
        endif
    next nI

    if !lOk
        cErro := "Payload incompleto — campos ausentes/nulos/invalidos: " + ;
                 lJoin(aMiss, ", ") + ". Identidade completa (6 campos + filial por contexto) e atributos exigidos."
    endif

Return lOk

static function lJoin(aItens, cSep)

    local cRet := ""
    local nI   := 0

    for nI := 1 to len(aItens)
        cRet += aItens[nI] + iif(nI < len(aItens), cSep, "")
    next nI

Return cRet

/* -----------------------------------------------------------------------
   lModelErr — extrai mensagens de erro do modelo quando disponivel.
   VALIDAR NO TST01: API exata de erro do MPFormModel no ambiente.
   ----------------------------------------------------------------------- */
static function lModelErr(oModel, cErro)

    local xErr := NIL
    local nI   := 0

    xErr := oModel:GetErrorMessage()
    if ValType(xErr) == "A"
        for nI := 1 to len(xErr)
            cErro += cValToChar(xErr[nI]) + CRLF
        next nI
    elseif ValType(xErr) <> "U"
        cErro += cValToChar(xErr) + CRLF
    else
        cErro += "Validacao do modelo DMATA061 rejeitada (detalhe indisponivel)." + CRLF
    endif

Return cErro

/* -----------------------------------------------------------------------
   lExecSA5 — corpo comum das operacoes de escrita via modelo oficial.
   nOp = MODEL_OPERATION_INSERT | MODEL_OPERATION_UPDATE
   ----------------------------------------------------------------------- */
static function lExecSA5(oSelf, nOp)

    Local aArea      := GetArea()
    Local lRet       := .T.
    Local cErro      := ""
    Local cErroBlk   := ""
    Local aMiss      := {}
    Local aIdent     := aSA5Ident()
    Local aAttr      := aSA5Attrs()
    Local nI         := 0
    Local oModel     := NIL
    Local oGrid      := NIL
    Local oJsonRet   := JsonObject():New()
    Local oDados     := JsonObject():New()
    Local oException := ErrorBlock({|e| cErroBlk := e:Description + e:ErrorStack, Break(e) })

    oSelf:SetContentType("application/json")

    Begin Sequence

        if !oDados:FromJson(oSelf:GetContent())
            lRet := .F.
            oJsonRet := RETOBJ(oJsonRet, "400", "Erro", ;
                "Corpo da requisicao nao e um JSON valido", "dlp")
        elseif !lPrepSA5(oDados, @aMiss, @cErro)
            lRet := .F.
            oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErro, "dlp")
        else
            // Ciclo MVC oficial — modelo Model-2 'DMATA061'
            // (FWLoadModel comprovado na ViewDef do fonte oficial;
            //  GetModel/GetValue/Length/GoLine usados pelos callbacks)
            oModel := FWLoadModel("DMATA061")
            oModel:SetOperation(nOp)
            oModel:Activate()

            // header: produto (+ref. grade) — relation oficial aplica
            // xFilial("SA5") e propaga A5_PRODUTO/A5_REFGRD ao grid
            oModel:GetModel("DMdFieldSA5"):SetValue("A5_PRODUTO", oDados["A5_PRODUTO"])
            oModel:GetModel("DMdFieldSA5"):SetValue("A5_REFGRD",  oDados["A5_REFGRD"])

            oGrid := oModel:GetModel("DMdGridSA5")

            if nOp == MODEL_OPERATION_UPDATE
                // VALIDAR NO TST01 — carga da linha existente pela
                // relacao oficial (IndexKey(2)): filial via contexto.
                // A PK integral e imposta pelo SetPrimaryKey do modelo;
                // aqui localizamos a linha do vinculo informado.
                if !lLoadSa5Line(oModel, oGrid, oDados)
                    lRet := .F.
                    cErro := "Vinculo SA5 nao localizado pela identidade completa (ou assinatura Load pendente — VALIDAR NO TST01)."
                endif
            endif

            if lRet
                if nOp == MODEL_OPERATION_INSERT
                    oGrid:AddLine()
                endif

                // linha corrente: identidade + atributos
                for nI := 2 to len(aIdent)   // A5_PRODUTO vem do header
                    oGrid:SetValue(aIdent[nI], oDados[aIdent[nI]])
                next nI
                for nI := 1 to len(aAttr)
                    oGrid:SetValue(aAttr[nI], oDados[aAttr[nI]])
                next nI

                if !oModel:VldData()
                    lRet := .F.
                    cErro := lModelErr(oModel, cErro)
                else
                    oModel:CommitData()
                endif
            endif

            oModel:DeActivate()

            if lRet
                oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
                    "Vinculo integrado com sucesso!", "dlp")
            else
                oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErro, "dlp")
            endif
        endif

    Recover
        ErrorBlock(oException)
        lRet := .F.
        oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErroBlk, "dlp")
    End sequence

    // finalizacao unica: restaura o handler anterior em todo caminho
    ErrorBlock(oException)

    if lRet
        oSelf:setStatus(200)
    else
        oSelf:setStatus(400)
    endif
    oSelf:setResponse(oJsonRet:toJson())

    FreeObj(oJsonRet)
    FreeObj(oDados)
    RestArea(aArea)

Return .T.

/* -----------------------------------------------------------------------
   lLoadSa5Line — posiciona o grid na linha do vinculo informado.
   VALIDAR NO TST01: assinatura/semantica exata de carga de linhas do
   MPFormModel Model-2 por chave de relacao no ambiente instalado.
   Estrategia documentada: percorrer as linhas carregadas pelo modelo
   e comparar a identidade; se o modelo nao pre-carregar as linhas na
   ativacao UPDATE, a carga por Load/Seek oficial precisa ser definida
   com a equipe ERP antes de compilar.
   ----------------------------------------------------------------------- */
static function lLoadSa5Line(oModel, oGrid, oDados)

    local lFound := .F.
    local nI     := 0

    for nI := 1 to oGrid:Length()
        oGrid:GoLine(nI)
        if !oGrid:IsDeleted() .and. ;
           oGrid:GetValue("A5_FORNECE") == oDados["A5_FORNECE"] .and. ;
           oGrid:GetValue("A5_LOJA")    == oDados["A5_LOJA"]    .and. ;
           oGrid:GetValue("A5_FABR")    == oDados["A5_FABR"]    .and. ;
           oGrid:GetValue("A5_FALOJA")  == oDados["A5_FALOJA"]  .and. ;
           oGrid:GetValue("A5_REFGRD")  == oDados["A5_REFGRD"]
            lFound := .T.
            exit
        endif
    next nI

Return lFound

/*/{Protheus.doc} sa5Prod (POST)
    Inclusao de vinculo SA5 via modelo oficial DMATA061.
/*/
WSMETHOD POST sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn
Return lExecSA5(self, MODEL_OPERATION_INSERT)

/*/{Protheus.doc} sa5Prod (PUT)
    Alteracao de atributos do vinculo SA5 via modelo oficial DMATA061.
    Identidade imutavel; representacao completa exigida.
/*/
WSMETHOD PUT sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn
Return lExecSA5(self, MODEL_OPERATION_UPDATE)

/*/{Protheus.doc} sa5Prod (GET)
    TO_INVENTORY — sem rotina oficial de leitura REST comprovada.
    Nao implementar com SQL: leitura permanece na superficie governada
    da api-delpi (separada desta fachada).
/*/
WSMETHOD GET sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn

    Local oJsonRet := JsonObject():New()

    Self:SetContentType("application/json")
    Self:setStatus(501)
    Self:setResponse(RETOBJ(oJsonRet, "501", "Nao implementado", ;
        "READ via modelo oficial = TO_INVENTORY; usar a superficie de leitura governada da api-delpi", "dlp"):toJson())
    FreeObj(oJsonRet)

Return .T.

/*/{Protheus.doc} sa5Prod (DELETE)
    BLOCKED — a060VldGrv oficial rejeita salvar modelo sem linhas ativas;
    semantica de exclusao (ultimo vinculo) pendente de ratificacao.
    Jamais RecLock/DbDelete/SQL.
/*/
WSMETHOD DELETE sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn

    Local oJsonRet := JsonObject():New()

    Self:SetContentType("application/json")
    Self:setStatus(501)
    Self:setResponse(RETOBJ(oJsonRet, "501", "Bloqueado", ;
        "DELETE bloqueado: semantica oficial de exclusao SA5 pendente de ratificacao (a060VldGrv)", "dlp"):toJson())
    FreeObj(oJsonRet)

Return .T.

/*/{Protheus.doc} RETOBJ
    Padroniza o retorno JSON da API (mesmo contrato do product-master).
/*/
Static Function RETOBJ(oObj, cCode, cMsg, cDetMsg, cIdToken)

    Default cCode    := ""
    Default cMsg     := ""
    Default cDetMsg  := ""
    Default cIdToken := ""

    oObj['code']            := cCode
    oObj['message']         := FwCutOff(cMsg, .T.)
    oObj['detailedMessage'] := FwCutOff(cDetMsg, .T.)
    oObj['id']              := cIdToken

Return oObj
