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
     CREATE (POST)  = SOURCE_CANDIDATE — ciclo MPFormModel documentado +
                      ids/chave comprovados no fonte do modelo; commit so
                      aceito com retorno logico .T. de CommitData().
     UPDATE (PUT)   = BLOCKED — carga inequivoca do vinculo pela PK
                      integral sem view nao esta comprovada; o handler
                      retorna 501 explicito e NUNCA executa CommitData.
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
     - Carregamento do vinculo pela PK integral sem view (UPDATE) —
       metodo oficial nao comprovado; PUT permanece bloqueado.
     - Retorno de CommitData() exigido logico .T.; retorno nao-logico
       e tratado como resultado AMBIGUO (erro, nao sucesso).
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
        // A5_REFGRD: presenca e tipo exigidos, mas valor vazio e aceito —
        // produtos sem grade nao possuem referencia (conservador;
        // regra efetiva do modelo/SX3 = VALIDAR NO TST01).
        if ValType(xVal) == "U" .or. ValType(xVal) <> "C" .or. ;
           (aReq[nI] <> "A5_REFGRD" .and. Empty(xVal))
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
   lExecSA5 — CREATE do vinculo via modelo oficial DMATA061.
   Semantica de sucesso: COMMIT_ACKNOWLEDGED pelo modelo — nunca
   PERSISTENCE_CONFIRMED (confirmacao exige read-back governado).
   Nenhum caminho retorna 200 sem CommitData() explicitamente .T.;
   retorno nao-logico do commit = resultado AMBIGUO (erro, nao sucesso).
   ----------------------------------------------------------------------- */
static function lExecSA5(oSelf)

    Local aArea      := GetArea()
    Local lRet       := .T.
    Local lActivated := .F.
    Local cErro      := ""
    Local cErroBlk   := ""
    Local aMiss      := {}
    Local aIdent     := aSA5Ident()
    Local aAttr      := aSA5Attrs()
    Local nI         := 0
    Local xCommit    := NIL
    Local oModel     := NIL
    Local oGrid      := NIL
    Local oJsonRet   := JsonObject():New()
    Local oDados     := JsonObject():New()
    Local oException := ErrorBlock({|e| cErroBlk := e:Description, Break(e) })

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
            oModel:SetOperation(MODEL_OPERATION_INSERT)
            oModel:Activate()
            lActivated := .T.

            // header: produto (+ref. grade) — relation oficial aplica
            // xFilial("SA5") e propaga A5_PRODUTO/A5_REFGRD ao grid
            oModel:GetModel("DMdFieldSA5"):SetValue("A5_PRODUTO", oDados["A5_PRODUTO"])
            oModel:GetModel("DMdFieldSA5"):SetValue("A5_REFGRD",  oDados["A5_REFGRD"])

            oGrid := oModel:GetModel("DMdGridSA5")
            oGrid:AddLine()

            // linha corrente: identidade restante + atributos
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
                // MODEL_VALIDATED != COMMIT_ACKNOWLEDGED !=
                // PERSISTENCE_CONFIRMED — exige retorno logico .T.
                xCommit := oModel:CommitData()
                if ValType(xCommit) <> "L"
                    lRet := .F.
                    cErro := "Resultado ambiguo do commit do modelo " + ;
                        "DMATA061 — integracao nao confirmada; verificar " + ;
                        "o vinculo antes de repetir (VALIDAR NO TST01)."
                elseif !xCommit
                    lRet := .F.
                    cErro := lModelErr(oModel, cErro)
                endif
            endif
        endif

    Recover
        ErrorBlock(oException)
        lRet := .F.
        oJsonRet := RETOBJ(oJsonRet, "400", "Erro", ;
            "Falha interna na integracao Produto x Fornecedor.", "dlp")
    End sequence

    // finalizacao unica: restaura o handler anterior em todo caminho;
    // detalhe tecnico (cErroBlk) fica no log do app server, nunca no body
    ErrorBlock(oException)
    if lActivated .and. ValType(oModel) == "O"
        Begin Sequence
            oModel:DeActivate()
        Recover
            // falha de cleanup nao pode sobrescrever o resultado real
        End sequence
    endif
    if !Empty(cErroBlk)
        ConOut("DLP04I02 error: " + cErroBlk)
    endif

    if lRet
        oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
            "Vinculo aceito pelo modelo oficial DMATA061 " + ;
            "(commit reconhecido; confirmacao final via read-back governado).", "dlp")
        oSelf:setStatus(200)
    else
        if Empty(cErro)
            cErro := "Operacao rejeitada pela integracao Produto x Fornecedor."
        endif
        oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErro, "dlp")
        oSelf:setStatus(400)
    endif
    oSelf:setResponse(oJsonRet:toJson())

    FreeObj(oJsonRet)
    FreeObj(oDados)
    RestArea(aArea)

Return .T.

/*/{Protheus.doc} sa5Prod (POST)
    Inclusao de vinculo SA5 via modelo oficial DMATA061.
/*/
WSMETHOD POST sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn
Return lExecSA5(self)

/*/{Protheus.doc} sa5Prod (PUT)
    CONTRACT_CANDIDATE — alteracao de atributos do vinculo via modelo
    oficial. A carga inequivoca do vinculo pela PK integral no contexto
    REST (sem view) nao esta comprovada; ate a evidencia TST01, o PUT
    nao executa o ciclo do modelo nem CommitData — indisponibilidade
    explicita, nunca sucesso ficticio nem update parcial inseguro.
/*/
WSMETHOD PUT sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn

    Local oJsonRet := JsonObject():New()

    Self:SetContentType("application/json")
    Self:setStatus(501)
    Self:setResponse(RETOBJ(oJsonRet, "501", "Nao implementado", ;
        "Alteracao SA5 = CONTRACT_CANDIDATE: carga oficial do vinculo pela " + ;
        "chave integral pendente de comprovacao (VALIDAR NO TST01)", "dlp"):toJson())
    FreeObj(oJsonRet)

Return .T.

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
