/* ========================================================================
   DLP04I01.PRW — Api REST para cadastro de Produtos (SB1) via MATA010
   -----------------------------------------------------------------------
   ESTADO: SOURCE_CANDIDATE — aguardando revisão e compilação pela equipe ERP.

   VERSAO 2 — CRUD com cobertura integral de campos (EVA-TOTVS-SB1-FULL-FIELD-CRUD)

   PROVENIENCIA:
     upstream : Delpi-ti/protheus-erp @ master — "04. Estoque/DLP04I01.PRW"
     espelho  : docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW
                blob cdb68b0487222823a96162c0e493e442648e21f7 (commit be614649b7)
     upstream_sha: INCONCLUSIVE (repo privado nao revalidado nesta sessao)
     dicionario: SX3010 DELPI_TST01 == DELPI (319 campos, paridade integral
                 verificada 2026-11-18) — contracts/sb1-field-matrix.json

   EVOLUCAO vs v1 (22 campos fixos):
     1. Catalogo completo de campos elegiveis: 291 campos B1_* gravaveis
        (285 READ_WRITE_ELIGIBLE + 5 CONDITIONAL-memo + B1_COD identidade),
        derivados do SX3 real — contracts/sb1-field-matrix.json e a fonte.
     2. Validacao dinamica por nome: campos fora do catalogo sao rejeitados
        (desconhecido) e campos protegidos/imutaveis/sistema sao rejeitados
        com 400 client_error — nada e ignorado silenciosamente.
     3. Tipos por especie SX3: C=string; N=numero ou string lIsNumStr;
        D=data "AAAAMMDD"; M=memo como string (VALIDAR NO TST01).
     4. POST incluir: B1_COD obrigatorio + campos elegiveis informados;
        obrigatoriedade de negocio fica com a MATA010 oficial.
     5. PUT alterar: representacao completa obrigatoria — TODOS os 291
        campos do catalogo (politica fail-closed anti-zeramento; a
        api-delpi faz merge read-modify-write para o cliente mandar so
        o delta).
     6. DELETE excluir: metodo publicado e BLOQUEADO (501 not_homologated)
        — semantica oficial de exclusao da MATA010/ExecAuto nao comprovada
        neste ambiente; nenhum ExecAuto op 5 e chamado.
     7. GET metadados: devolve o proprio catalogo da integracao
        (campo/tipo/tamanho) — autodescricao do contrato, sem leitura
        de dados do ERP.
     8. Erros diferenciados: errorType = client_error |
        official_validation | server_error | not_homologated;
        o stack de erro NUNCA e exposto na resposta
        HTTP (somente Description sanitizada); GetAutoGrLog() sanitizado e truncado.
     9. ErrorBlock restaurado em todos os caminhos; fluxo unico de
        finalizacao; FreeObj em todos os JsonObject; RestArea.

   CONTRATO REST:
     POST   /v1/IncProduto/incluir    -> MSExecAuto MATA010 op 3 (inclusao)
     PUT    /v1/IncProduto/alterar    -> MSExecAuto MATA010 op 4 (alteracao)
     DELETE /v1/IncProduto/excluir    -> bloqueado por contrato (501)
     GET    /v1/IncProduto/metadados  -> catalogo da integracao (JSON)

   LIMITES CONHECIDOS:
     - Compilacao/homologacao TST01: pendente (equipe ERP).
     - JsonObject:GetNames() — metodo assumido do padrao TOTVS;
       VALIDAR NA COMPILACAO.
     - Campos memo (5) trafegam como string; semantica ExecAuto de memo
       VALIDAR NO TST01.
     - Exclusao oficial (op 5) sem prova documental neste ambiente —
       metodo bloqueado ate comprovacao.
     - Pontos de entrada ativos (A010TOK/MT010ALT) inspecionados no
       espelho; campos gerenciados por PE estao fora do catalogo.
   ======================================================================== */

#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#INCLUDE "FWMVCDef.ch"

WSRESTFUL DelpiProduto DESCRIPTION "Api REST para Tratativa de produtos" FORMAT "application/json"

    WSMETHOD POST   incProd  DESCRIPTION 'Insere Produto'      PATH '/v1/IncProduto/incluir'    WSSYNTAX '/v1/IncProduto/incluir'    TTALK "v1"
    WSMETHOD PUT    incProd  DESCRIPTION 'Altera Produto'      PATH '/v1/IncProduto/alterar'    WSSYNTAX '/v1/IncProduto/alterar'    TTALK "v1"
    WSMETHOD DELETE excProd  DESCRIPTION 'Exclui Produto'      PATH '/v1/IncProduto/excluir'    WSSYNTAX '/v1/IncProduto/excluir'    TTALK "v1"
    WSMETHOD GET    metaProd DESCRIPTION 'Metadados Produto'   PATH '/v1/IncProduto/metadados'  WSSYNTAX '/v1/IncProduto/metadados'  TTALK "v1"

END WSRESTFUL

/* -----------------------------------------------------------------------
   Catalogo oficial de campos gravaveis (gerado do SX3 — 291 entradas).
   {CAMPO, especie} — especie: C=caractere, N=numerico, D=data, M=memo.
   Campos fora desta lista (imutaveis, sistema, espelhos de movimento,
   B1_FILIAL, B1_CODITE) sao rejeitados como protegidos.
   ----------------------------------------------------------------------- */
static function aB1Fields()

Return { ;
    {"B1_GRUPO","C"}, {"B1_COD","C"}, {"B1_DESC","C"}, {"B1_REFEREN","C"}, ;
    {"B1_CODDES","C"}, {"B1_REFCANT","C"}, {"B1_TIPO","C"}, {"B1_YHOHS","C"}, ;
    {"B1_POSIPI","C"}, {"B1_ESPECIE","C"}, {"B1_EX_NCM","C"}, {"B1_EX_NBM","C"}, ;
    {"B1_LOCPAD","C"}, {"B1_UM","C"}, {"B1_LINHA","C"}, {"B1_SUBGRUP","C"}, ;
    {"B1_TPMAT","C"}, {"B1_PICM","N"}, {"B1_BITMAP","C"}, {"B1_SEGUM","C"}, ;
    {"B1_IPI","N"}, {"B1_ALIQISS","N"}, {"B1_CODISS","C"}, {"B1_TE","C"}, ;
    {"B1_TS","C"}, {"B1_PICMRET","N"}, {"B1_PICMENT","N"}, {"B1_IMPZFRC","C"}, ;
    {"B1_CONV","N"}, {"B1_TIPCONV","C"}, {"B1_ALTER","C"}, {"B1_QE","N"}, ;
    {"B1_ESTFOR","C"}, {"B1_PRV1","N"}, {"B1_EMIN","N"}, {"B1_CUSTD","N"}, ;
    {"B1_MCUSTD","C"}, {"B1_PESO","N"}, {"B1_ESTSEG","N"}, {"B1_FORPRZ","C"}, ;
    {"B1_PE","N"}, {"B1_TIPE","C"}, {"B1_LE","N"}, {"B1_LOJPROC","C"}, ;
    {"B1_LM","N"}, {"B1_CONTA","C"}, {"B1_TOLER","N"}, {"B1_CC","C"}, ;
    {"B1_ITEMCC","C"}, {"B1_FAMILIA","C"}, {"B1_PROC","C"}, {"B1_QB","N"}, ;
    {"B1_TIPODEC","C"}, {"B1_DTREFP1","D"}, {"B1_ORIGEM","C"}, {"B1_CLASFIS","C"}, ;
    {"B1_FANTASM","C"}, {"B1_RASTRO","C"}, {"B1_FORAEST","C"}, {"B1_CONINI","D"}, ;
    {"B1_CONTSOC","C"}, {"B1_COMIS","N"}, {"B1_CODBAR","C"}, {"B1_GRADE","C"}, ;
    {"B1_FORMLOT","C"}, {"B1_MONO","C"}, {"B1_FPCOD","C"}, {"B1_PERINV","N"}, ;
    {"B1_CONTRAT","C"}, {"B1_DESC_P","C"}, {"B1_DESC_GI","C"}, {"B1_DESC_I","C"}, ;
    {"B1_GRTRIB","C"}, {"B1_MRP","C"}, {"B1_VM_I","M"}, {"B1_VM_GI","M"}, ;
    {"B1_VM_P","M"}, {"B1_ANUENTE","C"}, {"B1_CODOBS","C"}, {"B1_NOTAMIN","N"}, ;
    {"B1_PRVALID","N"}, {"B1_FABRIC","C"}, {"B1_NUMCOP","N"}, {"B1_IRRF","C"}, ;
    {"B1_LOCALIZ","C"}, {"B1_OPERPAD","C"}, {"B1_PRODPAI","C"}, {"B1_VLREFUS","N"}, ;
    {"B1_IMPORT","C"}, {"B1_OBS","M"}, {"B1_SITPROD","C"}, {"B1_MODELO","C"}, ;
    {"B1_SETOR","C"}, {"B1_BALANCA","C"}, {"B1_TECLA","C"}, {"B1_TIPOCQ","C"}, ;
    {"B1_SOLICIT","C"}, {"B1_GRUPCOM","C"}, {"B1_NALNCCA","C"}, {"B1_NUMCQPR","N"}, ;
    {"B1_NALSH","C"}, {"B1_CONTCQP","N"}, {"B1_REVATU","C"}, {"B1_INSS","C"}, ;
    {"B1_CODEMB","C"}, {"B1_ESPECIF","C"}, {"B1_DATASUB","D"}, {"B1_MAT_PRI","C"}, ;
    {"B1_REDINSS","N"}, {"B1_ALADI","C"}, {"B1_REDIRRF","N"}, {"B1_TAB_IPI","C"}, ;
    {"B1_GRUDES","C"}, {"B1_REDPIS","N"}, {"B1_REDCOF","N"}, {"B1_PCSLL","N"}, ;
    {"B1_PCOFINS","N"}, {"B1_PPIS","N"}, {"B1_QTDSER","C"}, {"B1_FLAGSUG","C"}, ;
    {"B1_CLASSVE","C"}, {"B1_MIDIA","C"}, {"B1_VLR_IPI","N"}, {"B1_QTMIDIA","N"}, ;
    {"B1_ENVOBR","C"}, {"B1_SERIE","C"}, {"B1_FAIXAS","N"}, {"B1_NROPAG","N"}, ;
    {"B1_ISBN","C"}, {"B1_TITORIG","C"}, {"B1_LINGUA","C"}, {"B1_EDICAO","C"}, ;
    {"B1_CORPRI","C"}, {"B1_CORSEC","C"}, {"B1_NICONE","C"}, {"B1_ATRIB1","C"}, ;
    {"B1_ATRIB2","C"}, {"B1_ATRIB3","C"}, {"B1_REGSEQ","C"}, {"B1_OBSISBN","C"}, ;
    {"B1_CLVL","C"}, {"B1_ATIVO","C"}, {"B1_PESBRU","N"}, {"B1_REQUIS","C"}, ;
    {"B1_SELO","C"}, {"B1_TIPCAR","C"}, {"B1_VLR_ICM","N"}, {"B1_VLRSELO","N"}, ;
    {"B1_CODNOR","C"}, {"B1_LOTVEN","N"}, {"B1_OK","C"}, {"B1_CPOTENC","C"}, ;
    {"B1_MSBLQL","C"}, {"B1_POTENCI","N"}, {"B1_QTDACUM","N"}, {"B1_EMAX","N"}, ;
    {"B1_PIS","C"}, {"B1_COFINS","C"}, {"B1_FRETISS","C"}, {"B1_TPREG","C"}, ;
    {"B1_CSLL","C"}, {"B1_CNAE","C"}, {"B1_VLR_PIS","N"}, {"B1_VLR_COF","N"}, ;
    {"B1_CALCFET","C"}, {"B1_PAUTFET","N"}, {"B1_LMP","N"}, {"B1_DESPIMP","C"}, ;
    {"B1_PARCEI","C"}, {"B1_USAFEFO","C"}, {"B1_AGREGCU","C"}, {"B1_FRACPER","N"}, ;
    {"B1_CLASSE","C"}, {"B1_INT_ICM","N"}, {"B1_GCCUSTO","C"}, {"B1_CCCUSTO","C"}, ;
    {"B1_PMACNUT","N"}, {"B1_PMICNUT","N"}, {"B1_CODPROC","C"}, {"B1_CODQAD","C"}, ;
    {"B1_VM_PROC","M"}, {"B1_QBP","N"}, {"B1_VLCIF","N"}, {"B1_RETOPER","C"}, ;
    {"B1_CRDEST","N"}, {"B1_PRFDSUL","N"}, {"B1_CODANT","C"}, {"B1_FETHAB","C"}, ;
    {"B1_FECP","N"}, {"B1_IVAAJU","C"}, {"B1_ESCRIPI","C"}, {"B1_FUSTF","C"}, ;
    {"B1_CRICMS","C"}, {"B1_SELOEN","C"}, {"B1_ALFECOP","N"}, {"B1_REGRISS","C"}, ;
    {"B1_ALFECST","N"}, {"B1_PRODREC","C"}, {"B1_FECOP","C"}, {"B1_VIGENC","D"}, ;
    {"B1_EMBDELP","N"}, {"B1_CRDPRES","N"}, {"B1_AFETHAB","N"}, {"B1_AFACS","N"}, ;
    {"B1_AFABOV","N"}, {"B1_REFBAS","C"}, {"B1_TFETHAB","C"}, {"B1_VEREAN","C"}, ;
    {"B1_RPRODEP","C"}, {"B1_RICM65","C"}, {"B1_PRDORI","C"}, {"B1_CFEM","C"}, ;
    {"B1_CFEMS","C"}, {"B1_CFEMA","N"}, {"B1_DTCORTE","D"}, {"B1_TRIBMUN","C"}, ;
    {"B1_TNATREC","C"}, {"B1_TPPROD","C"}, {"B1_CODLAN","C"}, {"B1_PR43080","N"}, ;
    {"B1_DCI","C"}, {"B1_DCRE","C"}, {"B1_ALFUMAC","N"}, {"B1_DCR","C"}, ;
    {"B1_PRN944I","C"}, {"B1_DCRII","N"}, {"B1_COEFDCR","N"}, {"B1_CHASSI","C"}, ;
    {"B1_DIFCNAE","C"}, {"B1_REGESIM","C"}, {"B1_RSATIVO","C"}, {"B1_FECPBA","N"}, ;
    {"B1_PRINCMG","N"}, {"B1_CRICMST","C"}, {"B1_ALFECRN","N"}, {"B1_AJUDIF","C"}, ;
    {"B1_SITTRIB","C"}, {"B1_DESBSE3","C"}, {"B1_BASE3","C"}, {"B1_IAT","C"}, ;
    {"B1_IPPT","C"}, {"B1_TALLA","C"}, {"B1_GDODIF","C"}, {"B1_MARKUP","N"}, ;
    {"B1_PRODSBP","C"}, {"B1_CARGAE","C"}, {"B1_VALEPRE","C"}, {"B1_LOTESBP","N"}, ;
    {"B1_TIPOBN","C"}, {"B1_DESBSE2","C"}, {"B1_ADMIN","C"}, {"B1_BASE2","C"}, ;
    {"B1_GARANT","C"}, {"B1_TIPVEC","C"}, {"B1_BASE","C"}, {"B1_TPDP","C"}, ;
    {"B1_PERGART","N"}, {"B1_MEPLES","C"}, {"B1_PAFMD5","C"}, {"B1_PORCPRL","C"}, ;
    {"B1_ESTRORI","C"}, {"B1_AFAMAD","N"}, {"B1_GRPTI","C"}, {"B1_GRPCST","C"}, ;
    {"B1_CEST","C"}, {"B1_AFASEMT","N"}, {"B1_AIMAMT","N"}, {"B1_AFUNDES","N"}, ;
    {"B1_COLOR","C"}, {"B1_IMPNCM","N"}, {"B1_CODGTIN","C"}, {"B1_YDESP","C"}, ;
    {"B1_YSC","C"}, {"B1_YPC","C"}, {"B1_YPV","C"}, {"B1_YMI","C"}, ;
    {"B1_YNFE","C"}, {"B1_YPDESD","N"}, {"B1_YPDESF","N"}, {"B1_YVLPC","C"}, ;
    {"B1_XLEWEG","C"}, {"B1_CONV3","N"}, {"B1_UM3","C"}, {"B1_NF3UM","C"}, ;
    {"B1_APOPRO","C"}, {"B1_ITEMWEG","C"}, {"B1_YCAT","C"}, {"B1_ZDLPSEG","C"}, ;
    {"B1_ZINVDLP","C"}, {"B1_ZDESREV","C"}, {"B1_XBLQCOM","C"} ;}

/* -----------------------------------------------------------------------
   lFieldSpec — retorna a especie do campo no catalogo, ou "" se ausente.
   ----------------------------------------------------------------------- */
static function cFieldKind(cField)

    local aFields := aB1Fields()
    local nI      := 0
    local cKind   := ""

    for nI := 1 to len(aFields)
        if aFields[nI][1] == cField
            cKind := aFields[nI][2]
            exit
        endif
    next nI

Return cKind

/* -----------------------------------------------------------------------
   lIsNumStr — validacao estrita de string numerica:
   sinal opcional SOMENTE na primeira posicao, ao menos um digito, no
   maximo um ponto decimal ".", sem separador de milhar, sem espacos.
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

/* -----------------------------------------------------------------------
   lIsDateStr — data no formato AAAAMMDD (8 digitos).
   ----------------------------------------------------------------------- */
static function lIsDateStr(cVal)

    local nI := 0

    if ValType(cVal) <> "C" .or. len(cVal) <> 8
        return .F.
    endif

    for nI := 1 to 8
        if !(SubStr(cVal, nI, 1) $ "0123456789")
            return .F.
        endif
    next nI

Return .T.

static function lJoin(aItens, cSep)

    local cRet := ""
    local nI   := 0

    for nI := 1 to len(aItens)
        cRet += aItens[nI] + iif(nI < len(aItens), cSep, "")
    next nI

Return cRet

/* -----------------------------------------------------------------------
   lPrepSB1 — valida o payload pelo catalogo e monta o array ExecAuto.

   nOp = 3: exige B1_COD + campos informados validos (inclusao — demais
            recebem default oficial da MATA010).
   nOp = 4: exige TODOS os campos do catalogo (representacao completa —
            politica fail-closed contra zeramento por omissao).

   Retorna .T. com aSB1 preenchido, ou .F. com cErro descritivo.
   ----------------------------------------------------------------------- */
static function lPrepSB1(oDados, nOp, aSB1, cErro)

    local aNames  := oDados:GetNames()
    local aMiss   := {}
    local aBad    := {}
    local cField  := ""
    local cKind   := ""
    local xVal    := NIL
    local nI      := 0
    local aFields := aB1Fields()

    // 1) rejeita campo desconhecido/protegido e valida tipos informados
    for nI := 1 to len(aNames)
        cField := aNames[nI]
        cKind  := cFieldKind(cField)

        if Empty(cKind)
            aadd(aBad, cField)
            loop
        endif

        xVal := oDados:GetJSonObject(cField)

        if cKind == "N"
            if ValType(xVal) == "N"
                aadd(aSB1, {cField, xVal, NIL})
            elseif ValType(xVal) == "C" .and. lIsNumStr(xVal)
                aadd(aSB1, {cField, Val(xVal), NIL})
            else
                aadd(aBad, cField + "(numerico)")
            endif
        elseif cKind == "D"
            if ValType(xVal) == "C" .and. lIsDateStr(xVal)
                aadd(aSB1, {cField, xVal, NIL})
            else
                aadd(aBad, cField + "(data AAAAMMDD)")
            endif
        else
            // C e M: somente string — sem conversao de tipo
            if ValType(xVal) == "C"
                aadd(aSB1, {cField, xVal, NIL})
            else
                aadd(aBad, cField + "(tipo " + ValType(xVal) + ")")
            endif
        endif
    next nI

    // 2) politica de cobertura por operacao
    if nOp == 4
        // representacao completa: todo campo do catalogo deve estar presente
        for nI := 1 to len(aFields)
            cField := aFields[nI][1]
            if ValType(oDados:GetJSonObject(cField)) == "U"
                aadd(aMiss, cField)
            endif
        next nI
    elseif nOp == 3
        // inclusao: somente a identidade e estruturalmente obrigatoria
        if ValType(oDados:GetJSonObject("B1_COD")) == "U"
            aadd(aMiss, "B1_COD")
        endif
    endif

    if len(aBad) > 0
        cErro := "Campos desconhecidos, protegidos ou invalidos: " + ;
                 lJoin(aBad, ", ") + ;
                 ". Consulte GET /v1/IncProduto/metadados para o catalogo elegivel."
        return .F.
    endif

    if len(aMiss) > 0
        if nOp == 4
            cErro := "Alteracao exige representacao completa — campos ausentes (" + ;
                     AllTrim(Str(len(aMiss))) + "): " + ;
                     lJoin(aMiss, ", ") + "."
        else
            cErro := "Campos obrigatorios ausentes: " + lJoin(aMiss, ", ") + "."
        endif
        return .F.
    endif

Return .T.

/* -----------------------------------------------------------------------
   lSanitLog — sanitiza linhas do GetAutoGrLog: trim, remove CR/LF
   internos e limita o texto total (erro oficial legivel, sem vazar
   internals nem estourar o envelope).
   ----------------------------------------------------------------------- */
static function cSanitLog(aLogAuto)

    local cTxt := ""
    local nI   := 0
    local cLin := ""

    for nI := 1 to len(aLogAuto)
        cLin := StrTran(StrTran(AllTrim(aLogAuto[nI]), Chr(13), " "), Chr(10), " ")
        if !Empty(cLin)
            cTxt += cLin + iif(nI < len(aLogAuto), " | ", "")
        endif
    next nI

Return SubStr(cTxt, 1, 2000)

/* -----------------------------------------------------------------------
   lExecSB1 — corpo comum de POST/PUT: parse, validacao, ExecAuto, retorno.
   nOp = 3 (inclusao) | 4 (alteracao) — operacoes oficiais da MATA010.
   ----------------------------------------------------------------------- */
static function lExecSB1(oSelf, nOp)

    Local aArea      := GetArea()
    Local lRet       := .T.
    Local cErro      := ""
    Local cJSON      := oSelf:GetContent()
    Local cErroBlk   := ""
    Local cErrType   := "server_error"
    Local aSB1       := {}
    Local aLogAuto   := {}
    Local nY         := 0
    Local nStatus    := 400
    Local oJsonRet   := JsonObject():New()
    Local oDados     := JsonObject():New()
    Local oException := ErrorBlock({|e| cErroBlk := e:Description, Break(e) })

    PRIVATE lMsErroAuto    := .F.
    PRIVATE lMsHelpAuto    := .T.
    PRIVATE lAutoErrNoFile := .T.

    oSelf:SetContentType("application/json")

    Begin Sequence

        if !oDados:FromJson(cJSON)
            lRet     := .F.
            cErrType := "client_error"
            oJsonRet := RETOBJ(oJsonRet, "400", "Erro", ;
                "Corpo da requisicao nao e um JSON valido", "dlp", cErrType)
        elseif !lPrepSB1(oDados, nOp, @aSB1, @cErro)
            lRet     := .F.
            cErrType := "client_error"
            oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErro, "dlp", cErrType)
        else
            MSExecAuto({|x,y| Mata010(x,y)}, aSB1, nOp)

            if lMsErroAuto
                lRet     := .F.
                cErrType := "official_validation"
                aLogAuto := GetAutoGrLog()
                oJsonRet := RETOBJ(oJsonRet, "400", "Erro", ;
                    cSanitLog(aLogAuto), "dlp", cErrType)
            else
                cErrType := ""
                oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
                    "Registro integrado com sucesso!", "dlp", "")
            endif
        endif

    Recover
        ErrorBlock(oException)
        lRet     := .F.
        cErrType := "server_error"
        nStatus  := 500
        oJsonRet := RETOBJ(oJsonRet, "500", "Erro interno", ;
            iif(Empty(cErroBlk), "Falha nao tratada na integracao", ;
                SubStr(cErroBlk, 1, 400)), "dlp", cErrType)
    End sequence

    // finalizacao unica: restaura o handler anterior em TODO caminho
    ErrorBlock(oException)

    if lRet
        oSelf:setStatus(200)
    else
        oSelf:setStatus(nStatus)
    endif
    oSelf:setResponse(oJsonRet:toJson())

    FreeObj(oJsonRet)
    FreeObj(oDados)
    RestArea(aArea)

Return .T.

/* -----------------------------------------------------------------------
   lExcBlocked — DELETE bloqueado por contrato.
   A semantica oficial de exclusao de produto via MATA010/MSExecAuto
   (op 5) nao esta comprovada neste ambiente (sem fonte upstream da
   rotina no repositorio). Nenhum ExecAuto e chamado.
   ----------------------------------------------------------------------- */
static function lExcBlocked(oSelf)

    Local aArea    := GetArea()
    Local oJsonRet := JsonObject():New()

    oSelf:SetContentType("application/json")

    oJsonRet := RETOBJ(oJsonRet, "501", "Nao homologado", ;
        "Exclusao de produto nao habilitada: semantica oficial de " + ;
        "exclusao da MATA010 pendente de comprovacao (TO_INVENTORY). " + ;
        "Nenhuma operacao foi executada no ERP.", "dlp", "not_homologated")

    oSelf:setStatus(501)
    oSelf:setResponse(oJsonRet:toJson())

    FreeObj(oJsonRet)
    RestArea(aArea)

Return .T.

/* -----------------------------------------------------------------------
   lMetaProd — GET metadados: devolve o catalogo elegivel da integracao
   (campo, especie). Autodescricao do contrato; nao le dados do ERP.
   ----------------------------------------------------------------------- */
static function lMetaProd(oSelf)

    Local aArea    := GetArea()
    Local oJsonRet := JsonObject():New()
    Local aFields  := aB1Fields()
    Local aCatalog := {}
    Local oField   := NIL
    Local nI       := 0

    oSelf:SetContentType("application/json")

    for nI := 1 to len(aFields)
        oField := JsonObject():New()
        oField["field"] := aFields[nI][1]
        oField["kind"]  := aFields[nI][2]
        aadd(aCatalog, oField)
    next nI

    oJsonRet["entity"] := "SB1"
    oJsonRet["routine"] := "MATA010"
    oJsonRet["mechanism"] := "MSExecAuto"
    oJsonRet["fields"] := aCatalog
    oJsonRet["fields_count"] := len(aCatalog)
    oJsonRet["matrix_ref"] := "contracts/sb1-field-matrix.json"

    oSelf:setStatus(200)
    oSelf:setResponse(oJsonRet:toJson())

    FreeObj(oJsonRet)
    for nI := 1 to len(aCatalog)
        FreeObj(aCatalog[nI])
    next nI
    RestArea(aArea)

Return .T.

/*/{Protheus.doc} incProd (POST)
    Inclusao de produto SB1 via rotina oficial MATA010 (ExecAuto op 3).
    B1_COD obrigatorio; campos elegiveis informados sao validados pelo
    catalogo SX3; demais recebem os defaults oficiais da rotina.
/*/
WSMETHOD POST incProd WSRECEIVE WSRESTFUL DelpiProduto
Return lExecSB1(self, 3)

/*/{Protheus.doc} incProd (PUT)
    Alteracao de produto SB1 via rotina oficial MATA010 (ExecAuto op 4).
    Representacao completa obrigatoria: todos os 291 campos do catalogo
    (politica fail-closed contra perda por omissao).
/*/
WSMETHOD PUT incProd WSRECEIVE WSRESTFUL DelpiProduto
Return lExecSB1(self, 4)

/*/{Protheus.doc} excProd (DELETE)
    Exclusao BLOQUEADA por contrato — semantica oficial pendente.
    Responde 501 sem executar nenhuma operacao no ERP.
/*/
WSMETHOD DELETE excProd WSRECEIVE WSRESTFUL DelpiProduto
Return lExcBlocked(self)

/*/{Protheus.doc} metaProd (GET)
    Metadados da integracao: catalogo de campos elegiveis.
/*/
WSMETHOD GET metaProd WSRECEIVE WSRESTFUL DelpiProduto
Return lMetaProd(self)

/*/{Protheus.doc} RETOBJ
    Padroniza o retorno JSON da API (v2: +errorType).
/*/
Static Function RETOBJ(oObj, cCode, cMsg, cDetMsg, cIdToken, cErrType)

    Default cCode    := ""
    Default cMsg     := ""
    Default cDetMsg  := ""
    Default cIdToken := ""
    Default cErrType := ""

    oObj['code']            := cCode
    oObj['message']         := FwCutOff(cMsg, .T.)
    oObj['detailedMessage'] := FwCutOff(cDetMsg, .T.)
    oObj['id']              := cIdToken
    oObj['errorType']       := cErrType

Return oObj
