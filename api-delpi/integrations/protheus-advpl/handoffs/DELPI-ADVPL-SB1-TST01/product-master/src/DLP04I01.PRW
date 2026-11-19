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
     1. Catalogo completo de campos elegiveis: 286 campos B1_* gravaveis
        (285 READ_WRITE_ELIGIBLE + B1_COD identidade (5 memo sem coluna fisica no TST01 removidos)),
        derivados do SX3 real — contracts/sb1-field-matrix.json e a fonte.
     2. Validacao dinamica por nome: campos fora do catalogo sao rejeitados
        (desconhecido) e campos protegidos/imutaveis/sistema sao rejeitados
        com 400 client_error — nada e ignorado silenciosamente.
     3. Tipos por especie SX3: C=string; N=numero ou string lIsNumStr;
        D=data "AAAAMMDD"; M=memo como string (VALIDAR NO TST01).
     4. POST incluir: B1_COD obrigatorio + campos elegiveis informados;
        obrigatoriedade de negocio fica com a MATA010 oficial.
     5. PUT alterar: representacao completa obrigatoria — TODOS os 286
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

   REVISAO v2.1 (EVA independent review):
     - campos D aceitam valor vazio (data em branco e legitima na SB1;
       sem isso o PUT completo falharia em qualquer produto com data
       vazia). Semantica do vazio no ExecAuto: VALIDAR NO TST01.
     - GetContent/SetContentType dentro do Begin Sequence (throw em
       init de Local nao e recuperavel fora dela); GetContent SEMPRE
       antes de SetContentType — este consome o buffer do request no
       HTTPREST (regressao comprovada em TST01 2026-11-19).
     - GetAutoGrLog sem separador pendente; consulta ao catalogo sem
       rebuild por campo; literais de resposta 100% ASCII.

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
   Catalogo oficial de campos gravaveis (gerado do SX3 — 286 entradas; 5 memo sem coluna fisica no TST01 removidos).
   {CAMPO, especie} — especie: C=caractere, N=numerico, D=data, M=memo.
   Campos fora desta lista (imutaveis, sistema, espelhos de movimento,
   B1_FILIAL, B1_CODITE) sao rejeitados como protegidos.
   ----------------------------------------------------------------------- */
static function aB1Fields()

    /* Catalogo montado com aAdd() — literal unico de 286 sub-arrays
       excedia o limite de array literal do compilador ADVPL (erro
       de compilacao no fechamento do literal). Pares {campo,
       especie} identicos ao catalogo anterior. */
    local aRet := {}

    aAdd(aRet, {"B1_GRUPO","C"})
    aAdd(aRet, {"B1_COD","C"})
    aAdd(aRet, {"B1_DESC","C"})
    aAdd(aRet, {"B1_REFEREN","C"})
    aAdd(aRet, {"B1_CODDES","C"})
    aAdd(aRet, {"B1_REFCANT","C"})
    aAdd(aRet, {"B1_TIPO","C"})
    aAdd(aRet, {"B1_YHOHS","C"})
    aAdd(aRet, {"B1_POSIPI","C"})
    aAdd(aRet, {"B1_ESPECIE","C"})
    aAdd(aRet, {"B1_EX_NCM","C"})
    aAdd(aRet, {"B1_EX_NBM","C"})
    aAdd(aRet, {"B1_LOCPAD","C"})
    aAdd(aRet, {"B1_UM","C"})
    aAdd(aRet, {"B1_LINHA","C"})
    aAdd(aRet, {"B1_SUBGRUP","C"})
    aAdd(aRet, {"B1_TPMAT","C"})
    aAdd(aRet, {"B1_PICM","N"})
    aAdd(aRet, {"B1_BITMAP","C"})
    aAdd(aRet, {"B1_SEGUM","C"})
    aAdd(aRet, {"B1_IPI","N"})
    aAdd(aRet, {"B1_ALIQISS","N"})
    aAdd(aRet, {"B1_CODISS","C"})
    aAdd(aRet, {"B1_TE","C"})
    aAdd(aRet, {"B1_TS","C"})
    aAdd(aRet, {"B1_PICMRET","N"})
    aAdd(aRet, {"B1_PICMENT","N"})
    aAdd(aRet, {"B1_IMPZFRC","C"})
    aAdd(aRet, {"B1_CONV","N"})
    aAdd(aRet, {"B1_TIPCONV","C"})
    aAdd(aRet, {"B1_ALTER","C"})
    aAdd(aRet, {"B1_QE","N"})
    aAdd(aRet, {"B1_ESTFOR","C"})
    aAdd(aRet, {"B1_PRV1","N"})
    aAdd(aRet, {"B1_EMIN","N"})
    aAdd(aRet, {"B1_CUSTD","N"})
    aAdd(aRet, {"B1_MCUSTD","C"})
    aAdd(aRet, {"B1_PESO","N"})
    aAdd(aRet, {"B1_ESTSEG","N"})
    aAdd(aRet, {"B1_FORPRZ","C"})
    aAdd(aRet, {"B1_PE","N"})
    aAdd(aRet, {"B1_TIPE","C"})
    aAdd(aRet, {"B1_LE","N"})
    aAdd(aRet, {"B1_LOJPROC","C"})
    aAdd(aRet, {"B1_LM","N"})
    aAdd(aRet, {"B1_CONTA","C"})
    aAdd(aRet, {"B1_TOLER","N"})
    aAdd(aRet, {"B1_CC","C"})
    aAdd(aRet, {"B1_ITEMCC","C"})
    aAdd(aRet, {"B1_FAMILIA","C"})
    aAdd(aRet, {"B1_PROC","C"})
    aAdd(aRet, {"B1_QB","N"})
    aAdd(aRet, {"B1_TIPODEC","C"})
    aAdd(aRet, {"B1_DTREFP1","D"})
    aAdd(aRet, {"B1_ORIGEM","C"})
    aAdd(aRet, {"B1_CLASFIS","C"})
    aAdd(aRet, {"B1_FANTASM","C"})
    aAdd(aRet, {"B1_RASTRO","C"})
    aAdd(aRet, {"B1_FORAEST","C"})
    aAdd(aRet, {"B1_CONINI","D"})
    aAdd(aRet, {"B1_CONTSOC","C"})
    aAdd(aRet, {"B1_COMIS","N"})
    aAdd(aRet, {"B1_CODBAR","C"})
    aAdd(aRet, {"B1_GRADE","C"})
    aAdd(aRet, {"B1_FORMLOT","C"})
    aAdd(aRet, {"B1_MONO","C"})
    aAdd(aRet, {"B1_FPCOD","C"})
    aAdd(aRet, {"B1_PERINV","N"})
    aAdd(aRet, {"B1_CONTRAT","C"})
    aAdd(aRet, {"B1_DESC_P","C"})
    aAdd(aRet, {"B1_DESC_GI","C"})
    aAdd(aRet, {"B1_DESC_I","C"})
    aAdd(aRet, {"B1_GRTRIB","C"})
    aAdd(aRet, {"B1_MRP","C"})
    aAdd(aRet, {"B1_ANUENTE","C"})
    aAdd(aRet, {"B1_CODOBS","C"})
    aAdd(aRet, {"B1_NOTAMIN","N"})
    aAdd(aRet, {"B1_PRVALID","N"})
    aAdd(aRet, {"B1_FABRIC","C"})
    aAdd(aRet, {"B1_NUMCOP","N"})
    aAdd(aRet, {"B1_IRRF","C"})
    aAdd(aRet, {"B1_LOCALIZ","C"})
    aAdd(aRet, {"B1_OPERPAD","C"})
    aAdd(aRet, {"B1_PRODPAI","C"})
    aAdd(aRet, {"B1_VLREFUS","N"})
    aAdd(aRet, {"B1_IMPORT","C"})
    aAdd(aRet, {"B1_SITPROD","C"})
    aAdd(aRet, {"B1_MODELO","C"})
    aAdd(aRet, {"B1_SETOR","C"})
    aAdd(aRet, {"B1_BALANCA","C"})
    aAdd(aRet, {"B1_TECLA","C"})
    aAdd(aRet, {"B1_TIPOCQ","C"})
    aAdd(aRet, {"B1_SOLICIT","C"})
    aAdd(aRet, {"B1_GRUPCOM","C"})
    aAdd(aRet, {"B1_NALNCCA","C"})
    aAdd(aRet, {"B1_NUMCQPR","N"})
    aAdd(aRet, {"B1_NALSH","C"})
    aAdd(aRet, {"B1_CONTCQP","N"})
    aAdd(aRet, {"B1_REVATU","C"})
    aAdd(aRet, {"B1_INSS","C"})
    aAdd(aRet, {"B1_CODEMB","C"})
    aAdd(aRet, {"B1_ESPECIF","C"})
    aAdd(aRet, {"B1_DATASUB","D"})
    aAdd(aRet, {"B1_MAT_PRI","C"})
    aAdd(aRet, {"B1_REDINSS","N"})
    aAdd(aRet, {"B1_ALADI","C"})
    aAdd(aRet, {"B1_REDIRRF","N"})
    aAdd(aRet, {"B1_TAB_IPI","C"})
    aAdd(aRet, {"B1_GRUDES","C"})
    aAdd(aRet, {"B1_REDPIS","N"})
    aAdd(aRet, {"B1_REDCOF","N"})
    aAdd(aRet, {"B1_PCSLL","N"})
    aAdd(aRet, {"B1_PCOFINS","N"})
    aAdd(aRet, {"B1_PPIS","N"})
    aAdd(aRet, {"B1_QTDSER","C"})
    aAdd(aRet, {"B1_FLAGSUG","C"})
    aAdd(aRet, {"B1_CLASSVE","C"})
    aAdd(aRet, {"B1_MIDIA","C"})
    aAdd(aRet, {"B1_VLR_IPI","N"})
    aAdd(aRet, {"B1_QTMIDIA","N"})
    aAdd(aRet, {"B1_ENVOBR","C"})
    aAdd(aRet, {"B1_SERIE","C"})
    aAdd(aRet, {"B1_FAIXAS","N"})
    aAdd(aRet, {"B1_NROPAG","N"})
    aAdd(aRet, {"B1_ISBN","C"})
    aAdd(aRet, {"B1_TITORIG","C"})
    aAdd(aRet, {"B1_LINGUA","C"})
    aAdd(aRet, {"B1_EDICAO","C"})
    aAdd(aRet, {"B1_CORPRI","C"})
    aAdd(aRet, {"B1_CORSEC","C"})
    aAdd(aRet, {"B1_NICONE","C"})
    aAdd(aRet, {"B1_ATRIB1","C"})
    aAdd(aRet, {"B1_ATRIB2","C"})
    aAdd(aRet, {"B1_ATRIB3","C"})
    aAdd(aRet, {"B1_REGSEQ","C"})
    aAdd(aRet, {"B1_OBSISBN","C"})
    aAdd(aRet, {"B1_CLVL","C"})
    aAdd(aRet, {"B1_ATIVO","C"})
    aAdd(aRet, {"B1_PESBRU","N"})
    aAdd(aRet, {"B1_REQUIS","C"})
    aAdd(aRet, {"B1_SELO","C"})
    aAdd(aRet, {"B1_TIPCAR","C"})
    aAdd(aRet, {"B1_VLR_ICM","N"})
    aAdd(aRet, {"B1_VLRSELO","N"})
    aAdd(aRet, {"B1_CODNOR","C"})
    aAdd(aRet, {"B1_LOTVEN","N"})
    aAdd(aRet, {"B1_OK","C"})
    aAdd(aRet, {"B1_CPOTENC","C"})
    aAdd(aRet, {"B1_MSBLQL","C"})
    aAdd(aRet, {"B1_POTENCI","N"})
    aAdd(aRet, {"B1_QTDACUM","N"})
    aAdd(aRet, {"B1_EMAX","N"})
    aAdd(aRet, {"B1_PIS","C"})
    aAdd(aRet, {"B1_COFINS","C"})
    aAdd(aRet, {"B1_FRETISS","C"})
    aAdd(aRet, {"B1_TPREG","C"})
    aAdd(aRet, {"B1_CSLL","C"})
    aAdd(aRet, {"B1_CNAE","C"})
    aAdd(aRet, {"B1_VLR_PIS","N"})
    aAdd(aRet, {"B1_VLR_COF","N"})
    aAdd(aRet, {"B1_CALCFET","C"})
    aAdd(aRet, {"B1_PAUTFET","N"})
    aAdd(aRet, {"B1_LMP","N"})
    aAdd(aRet, {"B1_DESPIMP","C"})
    aAdd(aRet, {"B1_PARCEI","C"})
    aAdd(aRet, {"B1_USAFEFO","C"})
    aAdd(aRet, {"B1_AGREGCU","C"})
    aAdd(aRet, {"B1_FRACPER","N"})
    aAdd(aRet, {"B1_CLASSE","C"})
    aAdd(aRet, {"B1_INT_ICM","N"})
    aAdd(aRet, {"B1_GCCUSTO","C"})
    aAdd(aRet, {"B1_CCCUSTO","C"})
    aAdd(aRet, {"B1_PMACNUT","N"})
    aAdd(aRet, {"B1_PMICNUT","N"})
    aAdd(aRet, {"B1_CODPROC","C"})
    aAdd(aRet, {"B1_CODQAD","C"})
    aAdd(aRet, {"B1_QBP","N"})
    aAdd(aRet, {"B1_VLCIF","N"})
    aAdd(aRet, {"B1_RETOPER","C"})
    aAdd(aRet, {"B1_CRDEST","N"})
    aAdd(aRet, {"B1_PRFDSUL","N"})
    aAdd(aRet, {"B1_CODANT","C"})
    aAdd(aRet, {"B1_FETHAB","C"})
    aAdd(aRet, {"B1_FECP","N"})
    aAdd(aRet, {"B1_IVAAJU","C"})
    aAdd(aRet, {"B1_ESCRIPI","C"})
    aAdd(aRet, {"B1_FUSTF","C"})
    aAdd(aRet, {"B1_CRICMS","C"})
    aAdd(aRet, {"B1_SELOEN","C"})
    aAdd(aRet, {"B1_ALFECOP","N"})
    aAdd(aRet, {"B1_REGRISS","C"})
    aAdd(aRet, {"B1_ALFECST","N"})
    aAdd(aRet, {"B1_PRODREC","C"})
    aAdd(aRet, {"B1_FECOP","C"})
    aAdd(aRet, {"B1_VIGENC","D"})
    aAdd(aRet, {"B1_EMBDELP","N"})
    aAdd(aRet, {"B1_CRDPRES","N"})
    aAdd(aRet, {"B1_AFETHAB","N"})
    aAdd(aRet, {"B1_AFACS","N"})
    aAdd(aRet, {"B1_AFABOV","N"})
    aAdd(aRet, {"B1_REFBAS","C"})
    aAdd(aRet, {"B1_TFETHAB","C"})
    aAdd(aRet, {"B1_VEREAN","C"})
    aAdd(aRet, {"B1_RPRODEP","C"})
    aAdd(aRet, {"B1_RICM65","C"})
    aAdd(aRet, {"B1_PRDORI","C"})
    aAdd(aRet, {"B1_CFEM","C"})
    aAdd(aRet, {"B1_CFEMS","C"})
    aAdd(aRet, {"B1_CFEMA","N"})
    aAdd(aRet, {"B1_DTCORTE","D"})
    aAdd(aRet, {"B1_TRIBMUN","C"})
    aAdd(aRet, {"B1_TNATREC","C"})
    aAdd(aRet, {"B1_TPPROD","C"})
    aAdd(aRet, {"B1_CODLAN","C"})
    aAdd(aRet, {"B1_PR43080","N"})
    aAdd(aRet, {"B1_DCI","C"})
    aAdd(aRet, {"B1_DCRE","C"})
    aAdd(aRet, {"B1_ALFUMAC","N"})
    aAdd(aRet, {"B1_DCR","C"})
    aAdd(aRet, {"B1_PRN944I","C"})
    aAdd(aRet, {"B1_DCRII","N"})
    aAdd(aRet, {"B1_COEFDCR","N"})
    aAdd(aRet, {"B1_CHASSI","C"})
    aAdd(aRet, {"B1_DIFCNAE","C"})
    aAdd(aRet, {"B1_REGESIM","C"})
    aAdd(aRet, {"B1_RSATIVO","C"})
    aAdd(aRet, {"B1_FECPBA","N"})
    aAdd(aRet, {"B1_PRINCMG","N"})
    aAdd(aRet, {"B1_CRICMST","C"})
    aAdd(aRet, {"B1_ALFECRN","N"})
    aAdd(aRet, {"B1_AJUDIF","C"})
    aAdd(aRet, {"B1_SITTRIB","C"})
    aAdd(aRet, {"B1_DESBSE3","C"})
    aAdd(aRet, {"B1_BASE3","C"})
    aAdd(aRet, {"B1_IAT","C"})
    aAdd(aRet, {"B1_IPPT","C"})
    aAdd(aRet, {"B1_TALLA","C"})
    aAdd(aRet, {"B1_GDODIF","C"})
    aAdd(aRet, {"B1_MARKUP","N"})
    aAdd(aRet, {"B1_PRODSBP","C"})
    aAdd(aRet, {"B1_CARGAE","C"})
    aAdd(aRet, {"B1_VALEPRE","C"})
    aAdd(aRet, {"B1_LOTESBP","N"})
    aAdd(aRet, {"B1_TIPOBN","C"})
    aAdd(aRet, {"B1_DESBSE2","C"})
    aAdd(aRet, {"B1_ADMIN","C"})
    aAdd(aRet, {"B1_BASE2","C"})
    aAdd(aRet, {"B1_GARANT","C"})
    aAdd(aRet, {"B1_TIPVEC","C"})
    aAdd(aRet, {"B1_BASE","C"})
    aAdd(aRet, {"B1_TPDP","C"})
    aAdd(aRet, {"B1_PERGART","N"})
    aAdd(aRet, {"B1_MEPLES","C"})
    aAdd(aRet, {"B1_PAFMD5","C"})
    aAdd(aRet, {"B1_PORCPRL","C"})
    aAdd(aRet, {"B1_ESTRORI","C"})
    aAdd(aRet, {"B1_AFAMAD","N"})
    aAdd(aRet, {"B1_GRPTI","C"})
    aAdd(aRet, {"B1_GRPCST","C"})
    aAdd(aRet, {"B1_CEST","C"})
    aAdd(aRet, {"B1_AFASEMT","N"})
    aAdd(aRet, {"B1_AIMAMT","N"})
    aAdd(aRet, {"B1_AFUNDES","N"})
    aAdd(aRet, {"B1_COLOR","C"})
    aAdd(aRet, {"B1_IMPNCM","N"})
    aAdd(aRet, {"B1_CODGTIN","C"})
    aAdd(aRet, {"B1_YDESP","C"})
    aAdd(aRet, {"B1_YSC","C"})
    aAdd(aRet, {"B1_YPC","C"})
    aAdd(aRet, {"B1_YPV","C"})
    aAdd(aRet, {"B1_YMI","C"})
    aAdd(aRet, {"B1_YNFE","C"})
    aAdd(aRet, {"B1_YPDESD","N"})
    aAdd(aRet, {"B1_YPDESF","N"})
    aAdd(aRet, {"B1_YVLPC","C"})
    aAdd(aRet, {"B1_XLEWEG","C"})
    aAdd(aRet, {"B1_CONV3","N"})
    aAdd(aRet, {"B1_UM3","C"})
    aAdd(aRet, {"B1_NF3UM","C"})
    aAdd(aRet, {"B1_APOPRO","C"})
    aAdd(aRet, {"B1_ITEMWEG","C"})
    aAdd(aRet, {"B1_YCAT","C"})
    aAdd(aRet, {"B1_ZDLPSEG","C"})
    aAdd(aRet, {"B1_ZINVDLP","C"})
    aAdd(aRet, {"B1_ZDESREV","C"})
    aAdd(aRet, {"B1_XBLQCOM","C"})

Return aRet

/* -----------------------------------------------------------------------
   cFieldKind — retorna a especie do campo no catalogo, ou "" se ausente.
   aFields vem materializado pelo caller (evita rebuild do catalogo a
   cada consulta).
   ----------------------------------------------------------------------- */
static function cFieldKind(cField, aFields)

    local nI    := 0
    local cKind := ""

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
        cKind  := cFieldKind(cField, aFields)

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
            if ValType(xVal) == "C" .and. (lIsDateStr(xVal) .or. Empty(xVal))
                // Empty(xVal): data vazia e legitima (SB1 grava blank) —
                // sem ela o PUT completo falharia em todo produto com
                // data em branco. Semantica do valor vazio no ExecAuto:
                // VALIDAR NO TST01.
                aadd(aSB1, {cField, xVal, NIL})
            else
                aadd(aBad, cField + "(data AAAAMMDD ou vazio)")
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
            cErro := "Alteracao exige representacao completa - campos ausentes (" + ;
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

    local aLin := {}
    local nI   := 0
    local cLin := ""

    for nI := 1 to len(aLogAuto)
        cLin := StrTran(StrTran(AllTrim(aLogAuto[nI]), Chr(13), " "), Chr(10), " ")
        if !Empty(cLin)
            aadd(aLin, cLin)
        endif
    next nI

Return SubStr(lJoin(aLin, " | "), 1, 2000)

/* -----------------------------------------------------------------------
   lExecSB1 — corpo comum de POST/PUT: parse, validacao, ExecAuto, retorno.
   nOp = 3 (inclusao) | 4 (alteracao) — operacoes oficiais da MATA010.
   ----------------------------------------------------------------------- */
static function lExecSB1(oSelf, nOp)

    Local aArea      := GetArea()
    Local lRet       := .T.
    Local cErro      := ""
    Local cJSON      := ""
    Local cErroBlk   := ""
    Local cErrType   := "server_error"
    Local aSB1       := {}
    Local aLogAuto   := {}
    Local nStatus    := 400
    Local oJsonRet   := JsonObject():New()
    Local oDados     := JsonObject():New()
    Local oException := ErrorBlock({|e| cErroBlk := e:Description, Break(e) })

    PRIVATE lMsErroAuto    := .F.
    PRIVATE lMsHelpAuto    := .T.
    PRIVATE lAutoErrNoFile := .T.

    Begin Sequence

        cJSON := oSelf:GetContent()
        oSelf:SetContentType("application/json")

        // FromJson retorna .F. mesmo populando o objeto neste build —
        // o legado ignora o retorno (DLP04I01/DLP05W01 no espelho
        // 13-fontes). Valida-se o parse pelo conteudo: GetNames()
        // vazio = falhou. Sem conteudo do body por seguranca.
        oDados:FromJson(cJSON)

        if Len(oDados:GetNames()) == 0
            lRet     := .F.
            cErrType := "client_error"
            ConOut("DLP04I01 body: parse falhou; valtype=" + ;
                ValType(cJSON) + " len=" + ;
                iif(ValType(cJSON) == "C", cValToChar(Len(cJSON)), "n/a"))
            oJsonRet := RETOBJ(oJsonRet, "400", "Erro", ;
                "Corpo da requisicao nao e um JSON valido (valtype=" + ;
                ValType(cJSON) + ",len=" + ;
                iif(ValType(cJSON) == "C", cValToChar(Len(cJSON)), "n/a") + ")", ;
                "dlp-v053-fj", cErrType)
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
    Representacao completa obrigatoria: todos os 286 campos do catalogo
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
