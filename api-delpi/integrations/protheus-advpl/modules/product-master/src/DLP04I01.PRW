/* ========================================================================
   DLP04I01.PRW — Api REST para cadastro de Produtos (SB1) via MATA010
   -----------------------------------------------------------------------
   ESTADO: SOURCE_CANDIDATE — aguardando revisão e compilação pela equipe ERP.

   PROVENIENCIA:
     upstream : Delpi-ti/protheus-erp @ master — "04. Estoque/DLP04I01.PRW"
     espelho  : docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW
                blob cdb68b0487222823a96162c0e493e442648e21f7 (commit be614649b7)
     upstream_sha: INCONCLUSIVE (repo privado nao revalidado nesta sessao)

   ALTERACOES vs fonte original (minimas, justificadas):
     1. Validacao explicita de JSON (FromJson falha => HTTP 400 "JSON invalido").
     2. Contrato de representacao completa explicitado: os 22 campos do
        contrato sao obrigatorios em POST e PUT; campo ausente/nulo =>
        400 com lista de campos faltantes (antes: quebra generica
        "expected C->U, function val" ou gravacao destrutiva).
     3. Campos numericos (B1_PICMRET, B1_CONV): N nativo do JSON ou C
        estritamente numerica (regra lIsNumStr: sinal opcional na 1a
        posicao, digitos, no maximo um ponto decimal, sem separador de
        milhar/espaco); qualquer outra string rejeitada antes do ExecAuto
        — sem conversao silenciosa. Zero ("0" ou 0) e valor valido.
     4. Campos caractere: somente ValType "C"; N/L/A/O rejeitados — sem
        conversao automatica de tipo.
     5. ErrorBlock restaurado em todos os caminhos (sucesso, rejeicao,
        excecao): fluxo unico de finalizacao, sem retorno antecipado.
     6. Removido codigo morto e artefatos de ambiente: rotina de log em
        disco com path fixo de unidade do servidor, helper de normalizacao
        de JSON sem chamada ativa, logs de depuracao e blocos comentados.
     7. Arrays ExecAuto montados por helper interno lPrepSB1() — mesma
        lista de 22 campos e mesma ordem do fonte original.

   CONTRATO REST PRESERVADO:
     POST /v1/IncProduto/incluir  -> MSExecAuto MATA010 op 3 (inclusao)
     PUT  /v1/IncProduto/alterar  -> MSExecAuto MATA010 op 4 (alteracao)
     Resposta: RETOBJ {code,message,detailedMessage,id} + HTTP 200/400.

   LIMITES CONHECIDOS (nao comprovados neste fonte):
     - Compilacao/homologacao: pendente (TST01, equipe ERP).
     - Atualizacao parcial: NAO SUPORTADA por contrato — PUT exige os
       22 campos (politica fail-closed contra perda por omissao).
     - ValType de null JSON e indistinguivel de campo ausente no
       JsonObject: ambos sao rejeitados (documentado).
     - Pontos de entrada ativos na MATA010 do ambiente nao inspecionados
       (inventario RPO pendente — playbook-inventario-rpo-smartclient).
   ======================================================================== */

#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#INCLUDE "FWMVCDef.ch"

WSRESTFUL DelpiProduto DESCRIPTION "Api REST para Tratativa de produtos" FORMAT "application/json"

    WSMETHOD POST incProd  DESCRIPTION 'Insere Produto'  PATH '/v1/IncProduto/incluir'  WSSYNTAX '/v1/IncProduto/incluir'  TTALK "v1"
    WSMETHOD PUT  incProd  DESCRIPTION 'Altera Produto'  PATH '/v1/IncProduto/alterar'  WSSYNTAX '/v1/IncProduto/alterar'  TTALK "v1"

END WSRESTFUL

/* -----------------------------------------------------------------------
   Lista oficial de campos do contrato (ordem preservada do fonte original).
   Campos posicionados com .T. sao numericos (B1_PICMRET, B1_CONV).
   ----------------------------------------------------------------------- */
static function aB1Fields()

Return { ;
    {"B1_GRUPO"  , .F.}, {"B1_COD"    , .F.}, {"B1_DESC"   , .F.}, ;
    {"B1_REFEREN", .F.}, {"B1_REFCANT", .F.}, {"B1_CODDES" , .F.}, ;
    {"B1_TIPO"   , .F.}, {"B1_YHOHS"  , .F.}, {"B1_POSIPI" , .F.}, ;
    {"B1_LOCPAD" , .F.}, {"B1_UM"     , .F.}, {"B1_SEGUM"  , .F.}, ;
    {"B1_TE"     , .F.}, {"B1_TS"     , .F.}, {"B1_PICMRET", .T.}, ;
    {"B1_CONV"   , .T.}, {"B1_TIPCONV", .F.}, {"B1_TPMAT"  , .F.}, ;
    {"B1_ESPECIE", .F.}, {"B1_EX_NCM" , .F.}, {"B1_EX_NBM" , .F.}, ;
    {"B1_ORIGEM" , .F.}  ;
}

/* -----------------------------------------------------------------------
   lPrepSB1 — valida o payload contra o contrato de representacao completa
   e monta o array ExecAuto da SB1.

   Retorna .T. com aSB1 preenchido, ou .F. com cErro listando os campos
   ausentes/nulos/invalidos. Nao inventa valores nem consulta o ERP.
   ----------------------------------------------------------------------- */
static function lPrepSB1(oDados, aSB1, cErro)

    local aFields := aB1Fields()
    local aMiss   := {}
    local cField  := ""
    local xVal    := NIL
    local nI      := 0
    local lOk     := .T.

    for nI := 1 to len(aFields)
        cField := aFields[nI][1]
        xVal   := oDados:GetJSonObject(cField)

        if ValType(xVal) == "U"
            // ausente ou null explicito — indistinguiveis no JsonObject
            aadd(aMiss, cField)
            lOk := .F.
            loop
        endif

        if aFields[nI][2]
            // campo numerico: N nativo ou C no formato lIsNumStr
            if ValType(xVal) == "N"
                aadd(aSB1, {cField, xVal, NIL})
            elseif ValType(xVal) == "C" .and. lIsNumStr(xVal)
                aadd(aSB1, {cField, Val(xVal), NIL})
            else
                aadd(aMiss, cField + "(numerico)")
                lOk := .F.
            endif
        elseif ValType(xVal) == "C"
            aadd(aSB1, {cField, xVal, NIL})
        else
            // caractere exige ValType "C" — sem conversao de tipo
            aadd(aMiss, cField + "(tipo " + ValType(xVal) + ")")
            lOk := .F.
        endif
    next nI

    if !lOk
        cErro := "Payload incompleto — campos ausentes/nulos/invalidos: " + ;
                 lJoin(aMiss, ", ") + ". O contrato exige representacao completa (22 campos)."
    endif

Return lOk

/* -----------------------------------------------------------------------
   lIsNumStr — validacao estrita de string numerica (regra documentada):
   sinal opcional SOMENTE na primeira posicao, ao menos um digito, no
   maximo um ponto decimal ".", sem separador de milhar, sem espacos.
   Rejeita: "abc", "12x", "", " ", "1,2,3", ".", "-".
   Aceita: "0", "12", "-3", "+4", "1.5", ".5".
   ----------------------------------------------------------------------- */
static function lIsNumStr(cVal)

    local nI      := 0
    local nLen    := len(cVal)
    local nDots   := 0
    local nDigits := 0
    local cCh     := ""

    if Empty(cVal)
        return .F.
    endif

    for nI := 1 to nLen
        cCh := SubStr(cVal, nI, 1)
        if cCh $ "0123456789"
            nDigits++
        elseif cCh == "."
            nDots++
            if nDots > 1
                return .F.
            endif
        elseif cCh $ "+-" .and. nI == 1
            // sinal permitido apenas na primeira posicao
        else
            return .F.
        endif
    next nI

Return nDigits > 0

static function lJoin(aItens, cSep)

    local cRet := ""
    local nI   := 0

    for nI := 1 to len(aItens)
        cRet += aItens[nI] + iif(nI < len(aItens), cSep, "")
    next nI

Return cRet

/* -----------------------------------------------------------------------
   lExecSB1 — corpo comum dos metodos: parse, validacao, ExecAuto, retorno.
   nOp = 3 (inclusao) | 4 (alteracao) — operacoes oficiais da MATA010.
   ----------------------------------------------------------------------- */
static function lExecSB1(oSelf, nOp)

    Local aArea      := GetArea()
    Local lRet       := .T.
    Local cErro      := ""
    Local cJSON      := oSelf:GetContent()
    Local cErroBlk   := ""
    Local aSB1       := {}
    Local nY         := 0
    Local oJsonRet   := JsonObject():New()
    Local oDados     := JsonObject():New()
    Local oException := ErrorBlock({|e| cErroBlk := e:Description + e:ErrorStack, Break(e) })

    PRIVATE lMsErroAuto    := .F.
    PRIVATE lMsHelpAuto    := .T.
    PRIVATE lAutoErrNoFile := .T.

    oSelf:SetContentType("application/json")

    Begin Sequence

        if !oDados:FromJson(cJSON)
            // JsonObject():FromJson retorna .F. em JSON malformado;
            // se lancar erro, o Recover abaixo cobre o mesmo caminho
            lRet := .F.
            oJsonRet := RETOBJ(oJsonRet, "400", "Erro", ;
                "Corpo da requisicao nao e um JSON valido", "dlp")
        elseif !lPrepSB1(oDados, @aSB1, @cErro)
            lRet := .F.
            oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErro, "dlp")
        else
            MSExecAuto({|x,y| Mata010(x,y)}, aSB1, nOp)

            if lMsErroAuto
                lRet    := .F.
                aLogAuto := GetAutoGrLog()
                for nY := 1 to len(aLogAuto)
                    cErro += aLogAuto[nY] + CRLF
                next nY
                oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErro, "dlp")
            else
                oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
                    "Registro integrado com sucesso!", "dlp")
            endif
        endif

    Recover
        ErrorBlock(oException)
        lRet := .F.
        oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErroBlk, "dlp")
    End sequence

    // finalizacao unica: restaura o handler anterior em TODO caminho
    // normal (sucesso, rejeicao ou excecao absorvida pela Sequence)
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

/*/{Protheus.doc} incProd (POST)
    Inclusao de produto SB1 via rotina oficial MATA010 (ExecAuto op 3).
    Contrato: representacao completa dos 22 campos B1_*.
/*/
WSMETHOD POST incProd WSRECEIVE WSRESTFUL DelpiProduto
Return lExecSB1(self, 3)

/*/{Protheus.doc} incProd (PUT)
    Alteracao de produto SB1 via rotina oficial MATA010 (ExecAuto op 4).
    PUT parcial NAO e suportado: os 22 campos sao obrigatorios
    (politica fail-closed contra perda de dados por omissao).
/*/
WSMETHOD PUT incProd WSRECEIVE WSRESTFUL DelpiProduto
Return lExecSB1(self, 4)

/*/{Protheus.doc} RETOBJ
    Padroniza o retorno JSON da API.
/*/
Static Function RETOBJ(oObj, cCode, cMsg, cDetMsg, cIdToken)

    Default cCode   := ""
    Default cMsg    := ""
    Default cDetMsg := ""
    Default cIdToken := ""

    oObj['code']            := cCode
    oObj['message']         := FwCutOff(cMsg, .T.)
    oObj['detailedMessage'] := FwCutOff(cDetMsg, .T.)
    oObj['id']              := cIdToken

Return oObj
