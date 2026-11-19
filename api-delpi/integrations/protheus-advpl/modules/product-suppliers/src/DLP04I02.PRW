/* ========================================================================
   DLP04I02.PRW — Api REST para Produto x Fornecedor (SA5) via modelo MVC
   oficial MATA061 (cadastro Produto x Fornecedor, Model-2).
   -----------------------------------------------------------------------
   VERSAO: 0.7.1 — identificavel em runtime pelo campo 'id' das respostas
          ("dlp04i02-0.8.3"); comparar com o objeto compilado no RPO.
          0.7.0 = CRUD completo: PUT/GET/DELETE passam de 501 para o
          ciclo MVC oficial (mesma cadeia headless provada no POST).
          0.7.0 = PROVEN_RUNTIME TST01: GET 200 (data{}), PUT 200
          (A5_NOMEFOR alterado, read-back), DELETE 200 (vinculo
          removido), GET pos-delete 404 correto.
          0.8.3 = fix runtime GET 500 (causa real, log TST01): o error
                  block chamava __ObjHasData — funcao INEXISTENTE neste
                  build (familia __Obj* fora do AppMap); qualquer throw
                  dentro do error handler aborta a thread sem recover.
                  ErrorBlock reduzido a e:Description+Break; aSA5Form-
                  Fields passa a enumerar por GetStruct():GetFields()
                  AScan da guarda com == (match exato — '=' casa
                  prefixo A5_PE/A5_PESO e recriaria o crash).
                  (prova DLPDBG01 — id no elemento 3), nunca oGrid:
                  aFields (propriedade invalida no submodelo).
          0.8.2 = fix runtime GET 500: GetValue/SetValue em campo fora
                  do form aborta a thread sem recover (begin sequence
                  aninhado nao protege). Guarda trocada por intersecao
                  com oGrid:aFields — aSA5FormFields enumera os ids do
                  form (probe cIdField/GetID/cID, padrao DLPDBG01) e
                  GET devolve "" / PUT+POST rejeitam campo-a-campo
                  (official_validation). Sem aFields exposto, baseline
                  provado 0.7.x (3 attrs) como fail-safe.
          0.8.1 = fix runtime 0.8.0: catalogo montado com aadd
                  multi-arg so gravava o 1o item por chamada (catalogo
                  efetivo ~14 campos — PUT 400 indevido); aadd unitario
                  por elemento (padrao DLP04I01). GET: GetValue devolve
                  D/N — normalizado por xSA5JsonSafe antes do
                  JsonObject (Date crua derrubava a serializacao fora
                  do Begin Sequence => 500 cru do HTTPREST).
          0.8.0 = catalogo SA5 completo: 113 atributos SX3 editaveis
                  (matriz sa5-field-matrix.json); validadores aceitam
                  subconjuntos (PUT >= 1 campo; POST exige so o trio
                  SX3-obrigatorio + identidade); SetValue/GetValue por
                  campo com guarda — campo fora do form MdGridSA5 e
                  rejeitado nominalmente (official_validation no write,
                  "" no read); conversao tipada N=Val()/D=StoD().
                  VALIDAR NO TST01: intersecao real catalogo x formulario
                  (dump DLPDBG01 pendente) e tipos N/D na saida do GET.
          0.7.1 = identidade: A5_FABR/A5_FALOJA aceitam vazio — vinculos
          reais sem fabricante proprio guardam '' (regressao do teste
          negativo: GET em vinculo FABR='' retornava 400 indevido).
   ESTADO: PROVEN_RUNTIME TST01 (2026-11-19, REST :8701, build diag) —
          POST /incluir gravou SA5 10080010 x 999999/01 via modelo
          oficial MATA061 headless; read-back SQL confirmou.
   CADEIA CAUSAL RESOLVIDA (TST01 2026-11-19):
     - modelo 'DMATA061' (wrapper browse CRM) -> Activate() ExecBlock-ava
       U_DMATA061 -> FWMBrowse -> "JOB threads doesn't support
       remote/visual components" (srvobject.cpp) — THREAD ERROR provado;
     - modelo oficial 'MATA061' (TDN PCOM10001, rotina automatica)
       ativa headless — primario; DMATA061 fica fallback;
     - SetVldActivate({||.T.}) substitui a vld-activate que chamava a
       user function de browse (ponto de extensao documentado MPFormModel);
     - A5_REFGRD tem X3_WHEN que rejeita ate "": SetValue omitido em
       campo vazio (init/default do modelo);
     - AIF nao gera linha p/ SA5 nesta rotina (provado): patch
       AIF_ZCDUSR vira no-op; auditoria do ator fica no ledger api-delpi
       (decisao PO 2026-11-19).
   EVIDENCIA TST01 (2026-11-19, ambiente auxiliar REST :8061):
     - 4 URNs registradas; PUT/GET/DELETE responderam 501 do contrato
       (prova de publicacao da classe);
     - POST retornou mensagem generica para QUALQUER body — inclusive
       JSON valido — porque a resposta final sobrescrevia a mensagem
       especifica de cada ramo (corrigido nesta versao);
     - o sibling SB1 no MESMO ambiente tambem rejeitou JSON valido como
       "nao e um JSON valido" => CAUSA RAIZ CONFIRMADA no TST01
       (2026-11-19): FromJson retorna NIL em sucesso (semantica TDN) —
       !FromJson() inverte e rejeita JSON valido. O legado ignora o
       retorno; validamos pelo conteudo (GetNames() vazio).
   MUDANCAS 0.4.1 (diagnostico fail-closed, sem alterar contrato):
     - distincao "body vazio/indisponivel" x "JSON invalido" (evidencia se
       o corpo chega ao handler — a falha do ambiente auxiliar);
     - mensagem especifica de cada rejeicao preservada ate a resposta
       (fim do overwrite generico);
     - status 500 em excecao interna e em commit ambiguo (4xx = rejeicao
       deterministica; 5xx = resultado indeterminado);
     - campo errorType na resposta (paridade com o contrato do sibling);
     - ConOut com valtype/len do body na falha de parse (sem conteudo).

   PROVENIENCIA:
     modelo oficial: Delpi-ti/protheus-erp @ master — "73. CRM/Dmata061.prx"
     espelho: docs/13-fontes-totvs-protheus/73. CRM/Dmata061.prx
              blob b45cc9333c410a58d5836f78b79a140c6056c9c6 (commit be614649b7)
     comparacao : "73. CRM/MATA010M_DLP.PRW" (blob a56c2a5079991742a544c39dd…)
     upstream_sha: INCONCLUSIVE (repo privado nao revalidado nesta sessao)
     inventario : contracts/official-model-inventory.md (G2-B)

   MECANISMO: fachada WSRESTFUL instanciando o MODELO MVC oficial
   'MATA061' (fallback 'DMATA061') — nunca RecLock, SQL ou DbWrite
   sobre SA5. As validacoes,
   triggers e pontos de entrada do cadastro oficial (a060LinOk,
   a060VldGrv, MT061MN, SX3) executam no ciclo do modelo.

   CLASSIFICACAO POR OPERACAO (sem fingimento de contrato):
     CREATE (POST)  = PROVEN_RUNTIME TST01 (2026-11-19) — SA5 gravada
                      via modelo MATA061 headless + read-back SQL.
     UPDATE (PUT)   = SOURCE_CANDIDATE — posiciona SA5 no documento do
                      produto (indice 2), Activate em UPDATE, localiza a
                      linha na grade pela identidade e SetValue so nos
                      atributos editaveis (A5_NOMEFOR/A5_CODPRF/A5_DESCPRF).
                      Carga por posicao de alias = VALIDAR NO TST01.
     READ (GET)     = SOURCE_CANDIDATE — mesma carga em operacao VIEW,
                      GetValue nos campos da linha localizada; resposta
                      em data{}. Metodos GetValue/GoLine/IsDeleted do
                      FWFormModel = VALIDAR NO TST01.
     DELETE         = SOURCE_CANDIDATE — mesma carga em UPDATE +
                      DeleteLine() na linha localizada. SEMANTICA
                      OFICIAL: a060VldGrv rejeita salvar modelo com
                      todas as linhas excluidas — o ultimo vinculo do
                      produto nao pode ser removido por esta rota
                      (rejeicao oficial, fail-closed; remover o ultimo
                      vinculo exige a tela do MATA061/semantica de
                      exclusao do documento — TO_INVENTORY).

   IDENTIDADE SA5 (PK oficial do modelo — imutavel em UPDATE):
     A5_FILIAL(ctx xFilial) + A5_FORNECE + A5_LOJA + A5_PRODUTO +
     A5_FABR + A5_FALOJA + A5_REFGRD
     A5_FILIAL NAO vem do body — derivada por xFilial("SA5") no relation
     oficial do modelo (contexto empresa/filial da sessao REST).

   LIMITES / VALIDAR NO TST01:
     - Carga por posicao de alias (dbSetOrder(2)+MsSeek produto) como
       ancoragem do documento em UPDATE/VIEW = hipotese padrao MVC,
       nao comprovada; GoLine/IsDeleted/DeleteLine/GetValue = ids do
       padrao FWFormModel, nao comprovados neste RPO.
     - Produtos com grade (A5_REFGRD != ""): o documento e ancorado
       pelo registro posicionado — multiplos REFGRD do mesmo produto
       = VALIDAR NO TST01 (pode 404 legitimo).
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
     - Presenca compilada do modelo 'MATA061' e PEs ativos no RPO.
     - Compilacao/homologacao: pendente (TST01, equipe ERP).
   ======================================================================== */

#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.ch"

WSRESTFUL DelpiProdForn DESCRIPTION "Api REST Produto x Fornecedor (SA5)" FORMAT "application/json"

    WSMETHOD POST   sa5Prod  DESCRIPTION 'Inclui vinculo Produto x Fornecedor'   PATH '/v1/ProdForn/incluir'   WSSYNTAX '/v1/ProdForn/incluir'   TTALK "v1"
    WSMETHOD PUT    sa5Prod  DESCRIPTION 'Altera vinculo Produto x Fornecedor'   PATH '/v1/ProdForn/alterar'   WSSYNTAX '/v1/ProdForn/alterar'   TTALK "v1"
    WSMETHOD GET    sa5Prod  DESCRIPTION 'Consulta vinculo Produto x Fornecedor' PATH '/v1/ProdForn/consultar' WSSYNTAX '/v1/ProdForn/consultar' TTALK "v1"
    WSMETHOD DELETE sa5Prod  DESCRIPTION 'Exclui vinculo Produto x Fornecedor'   PATH '/v1/ProdForn/excluir'   WSSYNTAX '/v1/ProdForn/excluir'   TTALK "v1"

END WSRESTFUL

/* -----------------------------------------------------------------------
   Campos de identidade recebidos no body (A5_FILIAL derivada por xFilial
   na relation oficial do modelo — nunca informada pelo consumidor).
   ----------------------------------------------------------------------- */
static function aSA5Ident()

Return {"A5_PRODUTO", "A5_FORNECE", "A5_LOJA", "A5_FABR", "A5_FALOJA", "A5_REFGRD"}

// atributos editaveis do vinculo — catalogo SX3 SA5 completo menos
// identidade/protegidos (113 campos; sa5-field-matrix.json). A
// intersecao com o formulario MdGridSA5 e validada em runtime:
// SetValue/GetValue fora do form lanca e e capturado por campo.
static function aSA5Attrs()

    local aR := {}
    aadd(aR, "A5_NOMEFOR")
    aadd(aR, "A5_NOMERED")
    aadd(aR, "A5_CODPRF")
    aadd(aR, "A5_CODPRCA")
    aadd(aR, "A5_SITU")
    aadd(aR, "A5_FABREV")
    aadd(aR, "A5_PE")
    aadd(aR, "A5_TIPE")
    aadd(aR, "A5_EMBAL")
    aadd(aR, "A5_FABRRED")
    aadd(aR, "A5_MOE_US")
    aadd(aR, "A5_VLCOTUS")
    aadd(aR, "A5_ULT_ENT")
    aadd(aR, "A5_QT_COT")
    aadd(aR, "A5_ULT_FOB")
    aadd(aR, "A5_PARTOPC")
    aadd(aR, "A5_UNID")
    aadd(aR, "A5_SKPLOT")
    aadd(aR, "A5_RIAI")
    aadd(aR, "A5_DTRIAI")
    aadd(aR, "A5_VALRIAI")
    aadd(aR, "A5_INCOTER")
    aadd(aR, "A5_TR_COST")
    aadd(aR, "A5_CODGRP")
    aadd(aR, "A5_CODITE")
    aadd(aR, "A5_CODBAR")
    aadd(aR, "A5_TIPOCOT")
    aadd(aR, "A5_SKIPLOT")
    aadd(aR, "A5_DTCOM02")
    aadd(aR, "A5_DTCOM03")
    aadd(aR, "A5_DTCOM04")
    aadd(aR, "A5_DTCOM05")
    aadd(aR, "A5_DTCOM06")
    aadd(aR, "A5_DTCOM07")
    aadd(aR, "A5_DTCOM08")
    aadd(aR, "A5_DTCOM09")
    aadd(aR, "A5_DTCOM10")
    aadd(aR, "A5_DTCOM11")
    aadd(aR, "A5_DTCOM12")
    aadd(aR, "A5_ENTREGA")
    aadd(aR, "A5_QUANT01")
    aadd(aR, "A5_QUANT02")
    aadd(aR, "A5_QUANT03")
    aadd(aR, "A5_QUANT04")
    aadd(aR, "A5_QUANT05")
    aadd(aR, "A5_QUANT06")
    aadd(aR, "A5_QUANT07")
    aadd(aR, "A5_QUANT08")
    aadd(aR, "A5_QUANT09")
    aadd(aR, "A5_QUANT10")
    aadd(aR, "A5_QUANT11")
    aadd(aR, "A5_QUANT12")
    aadd(aR, "A5_PRECO01")
    aadd(aR, "A5_PRECO02")
    aadd(aR, "A5_PRECO03")
    aadd(aR, "A5_LEAD_T")
    aadd(aR, "A5_PRECO04")
    aadd(aR, "A5_PRECO05")
    aadd(aR, "A5_TIPATU")
    aadd(aR, "A5_LOTEMIN")
    aadd(aR, "A5_LOTEMUL")
    aadd(aR, "A5_PRECO06")
    aadd(aR, "A5_PRECO07")
    aadd(aR, "A5_MSBLQL")
    aadd(aR, "A5_PRECO08")
    aadd(aR, "A5_PRECO09")
    aadd(aR, "A5_PRECO10")
    aadd(aR, "A5_PRECO11")
    aadd(aR, "A5_PRECO12")
    aadd(aR, "A5_PLAM1")
    aadd(aR, "A5_NIVEL1")
    aadd(aR, "A5_NQA1")
    aadd(aR, "A5_PLAM2")
    aadd(aR, "A5_NIVEL2")
    aadd(aR, "A5_NQA2")
    aadd(aR, "A5_COND01")
    aadd(aR, "A5_COND02")
    aadd(aR, "A5_COND03")
    aadd(aR, "A5_COND04")
    aadd(aR, "A5_COND05")
    aadd(aR, "A5_TEMPLIM")
    aadd(aR, "A5_NOTA")
    aadd(aR, "A5_COND06")
    aadd(aR, "A5_COND07")
    aadd(aR, "A5_COND08")
    aadd(aR, "A5_COND09")
    aadd(aR, "A5_COND10")
    aadd(aR, "A5_COND11")
    aadd(aR, "A5_COND12")
    aadd(aR, "A5_DTCOM01")
    aadd(aR, "A5_TEMPTRA")
    aadd(aR, "A5_PESO")
    aadd(aR, "A5_ENTSIT")
    aadd(aR, "A5_CCUSTO")
    aadd(aR, "A5_DIASSIT")
    aadd(aR, "A5_TESBP")
    aadd(aR, "A5_CODFIS")
    aadd(aR, "A5_CONV")
    aadd(aR, "A5_TPCONV")
    aadd(aR, "A5_CODTAB")
    aadd(aR, "A5_DSCTAB")
    aadd(aR, "A5_LEADT")
    aadd(aR, "A5_QTDMN")
    aadd(aR, "A5_UMNFE")
    aadd(aR, "A5_NCMPRF")
    aadd(aR, "A5_DESCPRF")
    aadd(aR, "A5_TESCP")
    aadd(aR, "A5_ECFLAG")
    aadd(aR, "A5_ECDTEX")
    aadd(aR, "A5_ECSEQ")
    aadd(aR, "A5_CNO")
    aadd(aR, "A5_TOLEDIF")
    aadd(aR, "A5_VOLMAX")

Return aR

// campos numericos do catalogo (X3_TIPO=N) — SetValue recebe Val(x)
static function aSA5AttrNum()

    local aR := {}
    aadd(aR, "A5_PE")
    aadd(aR, "A5_EMBAL")
    aadd(aR, "A5_VLCOTUS")
    aadd(aR, "A5_QT_COT")
    aadd(aR, "A5_ULT_FOB")
    aadd(aR, "A5_TR_COST")
    aadd(aR, "A5_SKIPLOT")
    aadd(aR, "A5_ENTREGA")
    aadd(aR, "A5_QUANT01")
    aadd(aR, "A5_QUANT02")
    aadd(aR, "A5_QUANT03")
    aadd(aR, "A5_QUANT04")
    aadd(aR, "A5_QUANT05")
    aadd(aR, "A5_QUANT06")
    aadd(aR, "A5_QUANT07")
    aadd(aR, "A5_QUANT08")
    aadd(aR, "A5_QUANT09")
    aadd(aR, "A5_QUANT10")
    aadd(aR, "A5_QUANT11")
    aadd(aR, "A5_QUANT12")
    aadd(aR, "A5_PRECO01")
    aadd(aR, "A5_PRECO02")
    aadd(aR, "A5_PRECO03")
    aadd(aR, "A5_LEAD_T")
    aadd(aR, "A5_PRECO04")
    aadd(aR, "A5_PRECO05")
    aadd(aR, "A5_LOTEMIN")
    aadd(aR, "A5_LOTEMUL")
    aadd(aR, "A5_PRECO06")
    aadd(aR, "A5_PRECO07")
    aadd(aR, "A5_PRECO08")
    aadd(aR, "A5_PRECO09")
    aadd(aR, "A5_PRECO10")
    aadd(aR, "A5_PRECO11")
    aadd(aR, "A5_PRECO12")
    aadd(aR, "A5_TEMPLIM")
    aadd(aR, "A5_NOTA")
    aadd(aR, "A5_TEMPTRA")
    aadd(aR, "A5_PESO")
    aadd(aR, "A5_ENTSIT")
    aadd(aR, "A5_DIASSIT")
    aadd(aR, "A5_CONV")
    aadd(aR, "A5_LEADT")
    aadd(aR, "A5_QTDMN")
    aadd(aR, "A5_TOLEDIF")
    aadd(aR, "A5_VOLMAX")

Return aR

// campos data do catalogo (X3_TIPO=D, formato AAAAMMDD) — StoD(x)
static function aSA5AttrDat()

    local aR := {}
    aadd(aR, "A5_ULT_ENT")
    aadd(aR, "A5_DTRIAI")
    aadd(aR, "A5_VALRIAI")
    aadd(aR, "A5_DTCOM02")
    aadd(aR, "A5_DTCOM03")
    aadd(aR, "A5_DTCOM04")
    aadd(aR, "A5_DTCOM05")
    aadd(aR, "A5_DTCOM06")
    aadd(aR, "A5_DTCOM07")
    aadd(aR, "A5_DTCOM08")
    aadd(aR, "A5_DTCOM09")
    aadd(aR, "A5_DTCOM10")
    aadd(aR, "A5_DTCOM11")
    aadd(aR, "A5_DTCOM12")
    aadd(aR, "A5_DTCOM01")

Return aR

// obrigatorios SX3 para CREATE (X3_OBRIGAT comprovado — G0-C)
static function aSA5Required()

Return {"A5_NOMEFOR", "A5_CODPRF", "A5_DESCPRF"}

// converte o valor texto do JSON para o tipo do campo no modelo
static function xSA5Typed(cField, xVal, aNum, aDat)

    if aScan(aNum, cField) > 0
        return Val(xVal)
    elseif aScan(aDat, cField) > 0
        return StoD(xVal)
    endif

Return xVal

// normaliza valor do modelo p/ JSON — Date vira DtoS (AAAAMMDD),
// demais tipos nao-C/N/L viram texto; evita throw na serializacao
// do JsonObject fora do Begin Sequence (regressao GET 500 TST01)
static function xSA5JsonSafe(xVal)

    if ValType(xVal) == "D"
        return DtoS(xVal)
    elseif ValType(xVal) <> "C" .and. ValType(xVal) <> "N" .and. ;
           ValType(xVal) <> "L"
        return cValToChar(xVal)
    endif

Return xVal

/* ---------------------------------------------------------------------
   aSA5FormFields — ids dos campos expostos pelo submodelo de grade
   (FWFormFieldsModel:aFields — mesmo probe do DLPDBG01). GetValue/
   SetValue em campo fora do form aborta a thread sem recover (GET 500
   cru TST01 0.8.0/0.8.1) — intersecao deterministica ANTES da chamada,
   sem begin sequence aninhado. Enumeracao vazia = form desconhecido:
   caller decide fail-closed.
   --------------------------------------------------------------------- */
static function aSA5FormFields(oGrid)

    local aOut := {}
    local aF   := {}
    local nI   := 0

    // caminho provado DLPDBG01 (SB1MASTER): struct do modelo —
    // GetFields() devolve array de ARR com o id no elemento 3.
    // oGrid:aFields NAO existe neste build (propriedade invalida),
    // e a familia __Obj* esta fora do AppMap — sem probe de dados.
    begin sequence
        aF := oGrid:GetStruct():GetFields()
        for nI := 1 to len(aF)
            if ValType(aF[nI]) == "A" .and. len(aF[nI]) >= 3 .and. ;
               ValType(aF[nI][3]) == "C" .and. !Empty(aF[nI][3])
                aadd(aOut, Upper(AllTrim(aF[nI][3])))
            endif
        next nI
    recover
        aOut := {}
    end sequence

Return aOut

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
        // A5_REFGRD/A5_FABR/A5_FALOJA: presenca e tipo exigidos, mas
        // valor vazio e aceito — produtos sem grade nao possuem REFGRD
        // e vinculos reais sem fabricante proprio guardam FABR/FALOJA
        // vazios (provado TST01 2026-11-19: 6/6 vinculos do produto
        // 10080010 com FABR=FALOJA=''). FORNECE/LOJA/PRODUTO exigem valor.
        if ValType(xVal) == "U" .or. ValType(xVal) <> "C" .or. ;
           (aReq[nI] <> "A5_REFGRD" .and. aReq[nI] <> "A5_FABR" .and. ;
            aReq[nI] <> "A5_FALOJA" .and. Empty(xVal))
            aadd(aMiss, aReq[nI] + iif(ValType(xVal) <> "U" .and. ValType(xVal) <> "C", "(tipo " + ValType(xVal) + ")", ""))
            lOk := .F.
        endif
    next nI

    // atributos: catalogo completo — valida tipo dos presentes;
    // ausentes seguem omitidos (defaults do modelo oficial)
    for nI := 1 to len(aAttr)
        xVal := oDados:GetJSonObject(aAttr[nI])
        if ValType(xVal) <> "U" .and. ValType(xVal) <> "C"
            aadd(aMiss, aAttr[nI] + "(tipo " + ValType(xVal) + ")")
            lOk := .F.
        endif
    next nI

    // obrigatorios SX3 para CREATE
    for nI := 1 to len(aSA5Required())
        xVal := oDados:GetJSonObject(aSA5Required()[nI])
        if ValType(xVal) <> "C" .or. Empty(xVal)
            aadd(aMiss, aSA5Required()[nI])
            lOk := .F.
        endif
    next nI

    if !lOk
        cErro := "Payload incompleto — campos ausentes/nulos/invalidos: " + ;
                 lJoin(aMiss, ", ") + ". Identidade completa (6 campos + filial por contexto), " + ;
                 "obrigatorios SX3 (NOMEFOR/CODPRF/DESCPRF) e tipos corretos exigidos."
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
        cErro += "Validacao do modelo oficial rejeitada (detalhe indisponivel)." + CRLF
    endif

Return cErro

/* -----------------------------------------------------------------------
   lExecSA5 — CREATE do vinculo via modelo oficial MATA061.
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
    Local cErroEnv   := ""
    Local cMdlId     := ""
    Local cFldId     := ""
    Local cGrdId     := ""
    Local cErroLog   := ""
    Local cErrType   := "client_error"
    Local nStatus    := 400
    Local cJSON      := ""
    Local aMiss      := {}
    Local aIdent     := aSA5Ident()
    Local aAttr      := aSA5Attrs()
    Local nI         := 0
    Local xCommit    := NIL
    Local cCodUsr    := ""
    Local cHoraIni   := ""
    Local cQryUpd    := ""
    Local nQry       := 0
    Local oModel     := NIL
    Local oGrid      := NIL
    Local xVal       := NIL
    Local aLoad      := {}
    Local aRej       := {}
    Local aForm      := {}
    Local oJsonRet   := JsonObject():New()
    Local oDados     := JsonObject():New()
    Local oException := ErrorBlock({|e| cErroBlk := e:Description, Break(e) })

    Begin Sequence

        // GetContent SEMPRE antes de SetContentType — este consome o
        // buffer do request no HTTPREST (regressao comprovada TST01
        // 2026-11-19). "vazio/indisponivel" e "JSON invalido" sao
        // diagnosticos diferentes — o primeiro prova que o runtime nao
        // entregou o corpo (falha de ambiente), o segundo que chegou.
        cJSON := oSelf:GetContent()
        oSelf:SetContentType("application/json")

        // Semantica real do FromJson (TDN): retorna NIL em sucesso ou
        // string de erro na falha — nunca logico. !FromJson() inverte
        // o sentido. O legado ignora o retorno (DLP04I01/DLP05W01 no
        // espelho). Valida-se o parse pelo conteudo: GetNames() vazio.
        if ValType(cJSON) == "C" .and. !Empty(cJSON)
            oDados:FromJson(cJSON)
        endif

        if ValType(cJSON) <> "C" .or. Empty(cJSON)
            lRet := .F.
            cErro := "Corpo da requisicao vazio ou indisponivel no handler."
            ConOut("DLP04I02 body: valtype=" + ValType(cJSON) + ;
                " len=" + cValToChar(iif(ValType(cJSON) == "C", Len(cJSON), -1)))
        elseif Len(oDados:GetNames()) == 0
            lRet := .F.
            cErro := "Corpo da requisicao nao e um JSON valido"
            ConOut("DLP04I02 body: parse falhou; len=" + cValToChar(Len(cJSON)))
        elseif !lPrepSA5(oDados, @aMiss, @cErro)
            lRet := .F.
        else
            // ator real (auditoria AIF_ZCDUSR — padrao Gabriel/MATA020):
            // REST roda como usuario tecnico; sem isto a AIF fica cega.
            // codusr e meta-campo: lPrepSA5 ignora chaves fora de
            // aSA5Ident/aSA5Attrs, entao nao precisa de exclusao.
            if ValType(oDados:GetJSonObject("codusr")) == "C"
                cCodUsr := oDados:GetJSonObject("codusr")
            endif
            // Time() retorna HH:MM:SS (8) mas AIF_HORA grava HH:MM (5) —
            // truncar, senao a janela >= nunca casa na mesma execucao
            // (bug comprovado TST01 2026-11-19: 0 rows patcheados)
            cHoraIni := Left(Time(), 5)

            // Ciclo MVC oficial — modelo 'MATA061' = rotina automatica
            // documentada no TDN (EXECAUTO; componentes MdFieldSA5/
            // MdGridSA5), headless comprovado em TST01 2026-11-19.
            // Fallback 'DMATA061' (componentes DMd* — wrapper CRM).
            // SetVldActivate({||.T.}) substitui a validacao de ativacao:
            // o default ExecBlock-ava a user function de browse
            // (U_DMATA061 -> FWMBrowse -> "JOB threads doesn't support
            // remote/visual components", causa raiz provada por
            // THREAD ERROR TST01).
            aLoad := lLoadSA5Model()
            oModel := aLoad[1]
            cMdlId := aLoad[2]
            cFldId := aLoad[3]
            cGrdId := aLoad[4]
            if ValType(oModel) <> "O"
                lRet     := .F.
                cErrType := "server_error"
                nStatus  := 500
                cErro := "Nenhum modelo oficial MATA061/DMATA061 " + ;
                    "disponivel no RPO — integracao indisponivel."
            else
                oModel:SetOperation(MODEL_OPERATION_INSERT)
                oModel:SetVldActivate({|| .T.})
                oModel:Activate()
                lActivated := .T.

            // header: produto (+ref. grade) — relation oficial aplica
            // xFilial("SA5") e propaga A5_PRODUTO/A5_REFGRD ao grid.
            // A5_REFGRD tem X3_WHEN ("Ref Grd Cfg") que rejeita ate
            // atribuicao vazia — omitir o SetValue quando vazio e deixar
            // o modelo derivar (regressao TST01: FWWHEN
            // "Modo edicao nao respeitado").
            oModel:GetModel(cFldId):SetValue("A5_PRODUTO", oDados:GetJSonObject("A5_PRODUTO"))
            if !Empty(oDados:GetJSonObject("A5_REFGRD"))
                oModel:GetModel(cFldId):SetValue("A5_REFGRD", oDados:GetJSonObject("A5_REFGRD"))
            endif

            oGrid := oModel:GetModel(cGrdId)
            aForm := aSA5FormFields(oGrid)
            if len(aForm) == 0
                ConOut("DLP04I02 aFields do grid indisponivel — " + ;
                    "baseline provado 0.7.x como guarda")
                aForm := {"A5_NOMEFOR", "A5_CODPRF", "A5_DESCPRF"}
            endif
            oGrid:AddLine()

            // linha corrente: identidade restante + atributos; vazio =
            // omitir (init do modelo) — WHEN de campo calculado/protegido
            // rejeita atribuicao mesmo de "" (mesma classe do A5_REFGRD)
            for nI := 2 to len(aIdent)   // A5_PRODUTO vem do header
                xVal := oDados:GetJSonObject(aIdent[nI])
                if !Empty(xVal)
                    oGrid:SetValue(aIdent[nI], xVal)
                endif
            next nI
            // atributos: catalogo completo — so os presentes e nao
            // vazios; conversao por tipo SX3; campo fora do form do
            // modelo e detectado por intersecao com aFields do grid
            // (fail-closed: rejeicao nominal -> official_validation)
            for nI := 1 to len(aAttr)
                xVal := oDados:GetJSonObject(aAttr[nI])
                if ValType(xVal) == "C" .and. !Empty(xVal)
                    if aScan(aForm, {|x| x == aAttr[nI]}) > 0
                        oGrid:SetValue(aAttr[nI], ;
                            xSA5Typed(aAttr[nI], xVal, aSA5AttrNum(), aSA5AttrDat()))
                    else
                        aadd(aRej, aAttr[nI])
                        ConOut("DLP04I02 campo fora do form: " + aAttr[nI])
                    endif
                endif
            next nI

            if len(aRej) > 0
                lRet     := .F.
                cErrType := "official_validation"
                cErro := "Campos rejeitados pelo modelo " + cMdlId + ": " + ;
                    lJoin(aRej, ", ") + "."
            elseif !oModel:VldData()
                lRet     := .F.
                cErrType := "official_validation"
                // detalhe oficial do modelo NAO vai ao consumidor —
                // conteudo nao comprovado como seguro; fica no log
                cErroLog := lModelErr(oModel, cErroLog)
                cErro := "Rejeitado pela validacao oficial do modelo " + ;
                    cMdlId + " (detalhe tecnico no log do AppServer)."
            else
                // MODEL_VALIDATED != COMMIT_ACKNOWLEDGED !=
                // PERSISTENCE_CONFIRMED — exige retorno logico .T.
                xCommit := oModel:CommitData()
                if ValType(xCommit) <> "L"
                    lRet     := .F.
                    cErrType := "server_error"
                    nStatus  := 500
                    cErro := "Resultado ambiguo do commit do modelo " + ;
                        cMdlId + " — integracao nao confirmada; verificar " + ;
                        "o vinculo antes de repetir (VALIDAR NO TST01)."
                elseif !xCommit
                    lRet     := .F.
                    cErrType := "official_validation"
                    cErroLog := lModelErr(oModel, cErroLog)
                    cErro := "Persistencia rejeitada pelo modelo oficial " + ;
                        cMdlId + " (detalhe tecnico no log do AppServer)."
                else
                    // commit ok — patch do ator real no historico AIF.
                    // Nao-fatal por desenho: falha aqui nao nega o write
                    // ja commitado — so registra no console.
                    // DECISAO PO 2026-11-19: SA5 nao gera linha AIF nesta
                    // rotina (provado — AIF010 sem registros SA5); o
                    // UPDATE toca 0 linhas (no-op seguro) e a auditoria
                    // do ator fica no ledger da api-delpi.
                    if !Empty(cCodUsr)
                        cQryUpd := "UPDATE " + RetSqlName("AIF") + ;
                            " SET AIF_ZCDUSR = " + ValToSql(cCodUsr) + ;
                            " WHERE D_E_L_E_T_ = ' '" + ;
                            " AND AIF_TABELA = 'SA5'" + ;
                            " AND AIF_CODPRO = " + ;
                            ValToSql(AllTrim(oDados:GetJSonObject("A5_PRODUTO"))) + ;
                            " AND AIF_DATA = " + ValToSql(Date()) + ;
                            " AND AIF_HORA >= " + ValToSql(cHoraIni)
                        nQry := TCSQLExec(cQryUpd)
                        if nQry < 0
                            ConOut("DLP04I02 codusr: AIF_ZCDUSR nao gravado (rc=" + ;
                                cValToChar(nQry) + ")")
                        else
                            ConOut("DLP04I02 codusr=" + cCodUsr + ;
                                " -> AIF_ZCDUSR gravado")
                        endif
                    endif
                endif
            endif
            endif
        endif

    Recover
        ErrorBlock(oException)
        lRet     := .F.
        cErrType := "server_error"
        nStatus  := 500
        cErro    := "Falha interna na integracao Produto x Fornecedor."
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
    if !Empty(cErroEnv)
        ConOut("DLP04I02 err-env: " + cErroEnv)
    endif
    if !Empty(cErroLog)
        ConOut("DLP04I02 model: " + cErroLog)
    endif

    // resposta unica no fim — a mensagem especifica de cada ramo chega
    // ao consumidor; a generica so cobre o caso sem cErro preenchido
    if lRet
        oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
            "Vinculo aceito pelo modelo oficial " + cMdlId + " " + ;
            "(commit reconhecido; confirmacao final via read-back governado).", cVerTag(), "")
        oSelf:setStatus(200)
    else
        if Empty(cErro)
            cErro := "Operacao rejeitada pela integracao Produto x Fornecedor."
        endif
        oJsonRet := RETOBJ(oJsonRet, cValToChar(nStatus), "Erro", cErro, cVerTag(), cErrType)
        oSelf:setStatus(nStatus)
    endif
    oSelf:setResponse(oJsonRet:toJson())

    FreeObj(oJsonRet)
    FreeObj(oDados)
    RestArea(aArea)

Return .T.

/*/{Protheus.doc} sa5Prod (POST)
    Inclusao de vinculo SA5 via modelo oficial MATA061.
/*/
WSMETHOD POST sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn
Return lExecSA5(self)

/* -----------------------------------------------------------------------
   lFindSA5Line — localiza na grid do modelo a linha do vinculo pela
   identidade FORNECE+LOJA+FABR+FALOJA (4 campos definitivos da grid).
   REFGRD e validado contra o header do documento carregado.
   Retorna o numero da linha (>0) ou 0.
   VALIDAR NO TST01: nomes dos metodos da grid do modelo 'MATA061'
   (GetValue/IsDeleted) presumidos pelo padrao FWFormModel.
   ----------------------------------------------------------------------- */
static function lFindSA5Line(oGrid, oDados)

    local nI    := 0
    local nAlvo := 0

    for nI := 1 to oGrid:Length()
        oGrid:GoLine(nI)
        if !oGrid:IsDeleted() .and. ;
            AllTrim(cValToChar(oGrid:GetValue("A5_FORNECE"))) == AllTrim(oDados:GetJSonObject("A5_FORNECE")) .and. ;
            AllTrim(cValToChar(oGrid:GetValue("A5_LOJA")))    == AllTrim(oDados:GetJSonObject("A5_LOJA"))    .and. ;
            AllTrim(cValToChar(oGrid:GetValue("A5_FABR")))    == AllTrim(oDados:GetJSonObject("A5_FABR"))    .and. ;
            AllTrim(cValToChar(oGrid:GetValue("A5_FALOJA")))  == AllTrim(oDados:GetJSonObject("A5_FALOJA"))
            nAlvo := nI
            exit
        endif
    next nI

Return nAlvo

/* -----------------------------------------------------------------------
   lLoadSA5Model — carrega o modelo oficial (MATA061, fallback DMATA061)
   e devolve {oModel, cMdlId, cFldId, cGrdId}. Mesmo contrato do CREATE:
   rotina automatica TDN + bypass de vld-activate (browse).
   ----------------------------------------------------------------------- */
static function lLoadSA5Model()

    local oModel := NIL
    local cMdlId := ""
    local cFldId := ""
    local cGrdId := ""

    oModel := FWLoadModel("MATA061")
    if ValType(oModel) == "O"
        cMdlId := "MATA061"
        cFldId := "MdFieldSA5"
        cGrdId := "MdGridSA5"
    else
        oModel := FWLoadModel("DMATA061")
        cMdlId := "DMATA061"
        cFldId := "DMdFieldSA5"
        cGrdId := "DMdGridSA5"
    endif

Return {oModel, cMdlId, cFldId, cGrdId}

/* -----------------------------------------------------------------------
   lExecSA5Op — GET consultar / PUT alterar / DELETE excluir.
   Contrato uniforme: body JSON com identidade completa (6 campos);
   PUT exige tambem os atributos editaveis (A5_NOMEFOR/A5_CODPRF/A5_DESCPRF);
   codusr meta-campo (mesma regra do POST — ignorado pelo lPrep).
   Mecanismo oficial: posiciona SA5 no documento do produto (indice 2:
   FILIAL+PRODUTO+...), ativa o modelo na operacao correspondente e
   navega a grade ate a linha do vinculo. Sem RecLock/SQL/DbWrite.
   VALIDAR NO TST01: carga por posicao de alias + GoLine/DeleteLine/
   GetValue do FWFormModel — assinaturas presumidas do padrao MVC.
   DELETE: a060VldGrv oficial rejeita modelo com todas as linhas
   excluidas — ultimo vinculo do produto nao pode ser removido por esta
   rota (rejeicao oficial, fail-closed — semantica da rotina).
   ----------------------------------------------------------------------- */
static function lExecSA5Op(oSelf, cOp)

    Local aArea      := GetArea()
    Local lRet       := .F.
    Local lActivated := .F.
    Local cErro      := ""
    Local cErroBlk   := ""
    Local cErroEnv   := ""
    Local cMdlId     := ""
    Local cFldId     := ""
    Local cGrdId     := ""
    Local cErroLog   := ""
    Local cErrType   := "client_error"
    Local nStatus    := 400
    Local cJSON      := ""
    Local aMiss      := {}
    Local aIdent     := aSA5Ident()
    Local aAttr      := aSA5Attrs()
    Local nI         := 0
    Local nAlvo      := 0
    Local xCommit    := NIL
    Local xVal       := NIL
    Local cCodUsr    := ""
    Local cHoraIni   := ""
    Local cQryUpd    := ""
    Local nQry       := 0
    Local cProd      := ""
    Local oModel     := NIL
    Local oGrid      := NIL
    Local aLoad      := {}
    Local aRej       := {}
    Local aForm      := {}
    Local aFora      := {}
    Local oJsonRet   := JsonObject():New()
    Local oItem      := JsonObject():New()
    Local oDados     := JsonObject():New()
    Local oException := ErrorBlock({|e| cErroBlk := e:Description, Break(e) })

    Begin Sequence

        // GetContent SEMPRE antes de SetContentType (regressao TST01)
        cJSON := oSelf:GetContent()
        oSelf:SetContentType("application/json")

        if ValType(cJSON) == "C" .and. !Empty(cJSON)
            oDados:FromJson(cJSON)
        endif

        if ValType(cJSON) <> "C" .or. Empty(cJSON)
            lRet := .F.
            cErro := "Corpo da requisicao vazio ou indisponivel no handler."
        elseif Len(oDados:GetNames()) == 0
            lRet := .F.
            cErro := "Corpo da requisicao nao e um JSON valido"
        elseif !lPrepSA5Ident(oDados, @aMiss, @cErro)
            lRet := .F.
        elseif cOp == "PUT" .and. !lPrepSA5Attr(oDados, @aMiss, @cErro)
            lRet := .F.
        else
            if ValType(oDados:GetJSonObject("codusr")) == "C"
                cCodUsr := oDados:GetJSonObject("codusr")
            endif
            cHoraIni := Left(Time(), 5)
            cProd    := AllTrim(oDados:GetJSonObject("A5_PRODUTO"))

            // posiciona no documento do produto — indice 2 =
            // A5_FILIAL+A5_PRODUTO+A5_FORNECE+A5_LOJA (relation oficial).
            // dbSelectArea abre o alias se fechado (sem isso o SetOrder
            // lanca em area nao aberta).
            dbSelectArea("SA5")
            SA5->(dbSetOrder(2))
            if !SA5->(MsSeek(xFilial("SA5") + PadR(cProd, TamSx3("A5_PRODUTO")[1])))
                lRet     := .F.
                cErrType := "not_found"
                nStatus  := 404
                cErro := "Nenhum vinculo do produto " + cProd + ;
                    " encontrado na SA5 (filial do contexto)."
            else
                aLoad := lLoadSA5Model()
                oModel := aLoad[1]
                cMdlId := aLoad[2]
                cFldId := aLoad[3]
                cGrdId := aLoad[4]
                if ValType(oModel) <> "O"
                    lRet     := .F.
                    cErrType := "server_error"
                    nStatus  := 500
                    cErro := "Nenhum modelo oficial MATA061/DMATA061 " + ;
                        "disponivel no RPO — integracao indisponivel."
                else
                    oModel:SetOperation(iif(cOp == "GET", ;
                        MODEL_OPERATION_VIEW, MODEL_OPERATION_UPDATE))
                    oModel:SetVldActivate({|| .T.})
                    oModel:Activate()
                    lActivated := .T.
                    oGrid := oModel:GetModel(cGrdId)
                    aForm := aSA5FormFields(oGrid)
                    if len(aForm) == 0
                        ConOut("DLP04I02 aFields do grid indisponivel — " + ;
                            "baseline provado 0.7.x como guarda")
                        aForm := {"A5_NOMEFOR", "A5_CODPRF", "A5_DESCPRF"}
                    endif
                    nAlvo := lFindSA5Line(oGrid, oDados)
                    // REFGRD e campo do header do documento — linhas da
                    // grade compartilham o valor; compara-se no header.
                    if nAlvo > 0 .and. ;
                       AllTrim(cValToChar(oModel:GetModel(cFldId):GetValue("A5_REFGRD"))) <> ;
                           AllTrim(oDados:GetJSonObject("A5_REFGRD"))
                        nAlvo := 0
                    endif
                    if nAlvo == 0
                        lRet     := .F.
                        cErrType := "not_found"
                        nStatus  := 404
                        cErro := "Vinculo nao localizado na grade do " + ;
                            "modelo (identidade FORNECE/LOJA/FABR/FALOJA/REFGRD)."
                    else
                        oGrid:GoLine(nAlvo)
                        do case
                            case cOp == "GET"
                                // leitura via modelo — campos do vinculo;
                                // A5_PRODUTO/A5_REFGRD sao do header
                                // (campo fora do componente -> throw;
                                // chamada direta no componente certo)
                                for nI := 1 to len(aIdent)
                                    if aIdent[nI] == "A5_PRODUTO" .or. ;
                                       aIdent[nI] == "A5_REFGRD"
                                        xVal := oModel:GetModel(cFldId):GetValue(aIdent[nI])
                                    else
                                        xVal := oGrid:GetValue(aIdent[nI])
                                    endif
                                    oItem[aIdent[nI]] := iif(ValType(xVal) == "U", "", xSA5JsonSafe(xVal))
                                next nI
                                // atributos: catalogo completo — campo
                                // fora do form lanca no GetValue; a
                                // guarda por campo devolve "" sem derrubar
                                // a leitura do vinculo
                                for nI := 1 to len(aAttr)
                                    if aScan(aForm, {|x| x == aAttr[nI]}) > 0
                                        xVal := oGrid:GetValue(aAttr[nI])
                                        oItem[aAttr[nI]] := iif(ValType(xVal) == "U", "", xSA5JsonSafe(xVal))
                                    else
                                        aadd(aFora, aAttr[nI])
                                        oItem[aAttr[nI]] := ""
                                    endif
                                next nI
                                if len(aFora) > 0
                                    ConOut("DLP04I02 GET fora do form (" + ;
                                        cValToChar(len(aFora)) + "): " + ;
                                        lJoin(aFora, ", "))
                                endif
                                lRet    := .T.
                                nStatus := 200
                            case cOp == "PUT"
                                // subconjunto do catalogo — so presentes
                                // e nao vazios; conversao por tipo SX3;
                                // campo fora do form -> rejeicao por campo
                                for nI := 1 to len(aAttr)
                                    xVal := oDados:GetJSonObject(aAttr[nI])
                                    if ValType(xVal) == "C" .and. !Empty(xVal)
                                        if aScan(aForm, {|x| x == aAttr[nI]}) > 0
                                            oGrid:SetValue(aAttr[nI], ;
                                                xSA5Typed(aAttr[nI], xVal, aSA5AttrNum(), aSA5AttrDat()))
                                        else
                                            aadd(aRej, aAttr[nI])
                                            ConOut("DLP04I02 PUT campo fora do form: " + aAttr[nI])
                                        endif
                                    endif
                                next nI
                                if len(aRej) > 0
                                    lRet     := .F.
                                    cErrType := "official_validation"
                                    cErro := "Campos rejeitados pelo modelo " + cMdlId + ": " + ;
                                        lJoin(aRej, ", ") + "."
                                elseif !oModel:VldData()
                                    lRet     := .F.
                                    cErrType := "official_validation"
                                    cErroLog := lModelErr(oModel, cErroLog)
                                    cErro := "Rejeitado pela validacao oficial do modelo " + ;
                                        cMdlId + " (detalhe tecnico no log do AppServer)."
                                else
                                    xCommit := oModel:CommitData()
                                    if ValType(xCommit) <> "L"
                                        lRet     := .F.
                                        cErrType := "server_error"
                                        nStatus  := 500
                                        cErro := "Resultado ambiguo do commit do modelo " + ;
                                            cMdlId + " — integracao nao confirmada."
                                    elseif !xCommit
                                        lRet     := .F.
                                        cErrType := "official_validation"
                                        cErroLog := lModelErr(oModel, cErroLog)
                                        cErro := "Persistencia rejeitada pelo modelo oficial " + ;
                                            cMdlId + " (detalhe tecnico no log do AppServer)."
                                    else
                                        lRet := .T.
                                    endif
                                endif
                            otherwise  // DELETE
                                oGrid:DeleteLine()
                                if !oModel:VldData()
                                    lRet     := .F.
                                    cErrType := "official_validation"
                                    cErroLog := lModelErr(oModel, cErroLog)
                                    cErro := "Exclusao rejeitada pela validacao oficial do modelo " + ;
                                        cMdlId + " (detalhe tecnico no log do AppServer)."
                                else
                                    xCommit := oModel:CommitData()
                                    if ValType(xCommit) <> "L"
                                        lRet     := .F.
                                        cErrType := "server_error"
                                        nStatus  := 500
                                        cErro := "Resultado ambiguo do commit do modelo " + ;
                                            cMdlId + " — exclusao nao confirmada."
                                    elseif !xCommit
                                        lRet     := .F.
                                        cErrType := "official_validation"
                                        cErroLog := lModelErr(oModel, cErroLog)
                                        cErro := "Exclusao rejeitada pelo modelo oficial " + ;
                                            cMdlId + " (detalhe tecnico no log do AppServer)."
                                    else
                                        lRet := .T.
                                    endif
                                endif
                        endcase
                        // patch AIF_ZCDUSR pos-commit (no-op seguro p/
                        // SA5 — rotina nao gera AIF; decisao PO 2026-11-19:
                        // auditoria do ator permanece no ledger api-delpi)
                        if lRet .and. cOp <> "GET" .and. !Empty(cCodUsr)
                            cQryUpd := "UPDATE " + RetSqlName("AIF") + ;
                                " SET AIF_ZCDUSR = " + ValToSql(cCodUsr) + ;
                                " WHERE D_E_L_E_T_ = ' '" + ;
                                " AND AIF_TABELA = 'SA5'" + ;
                                " AND AIF_CODPRO = " + ;
                                ValToSql(AllTrim(oDados:GetJSonObject("A5_PRODUTO"))) + ;
                                " AND AIF_DATA = " + ValToSql(Date()) + ;
                                " AND AIF_HORA >= " + ValToSql(cHoraIni)
                            nQry := TCSQLExec(cQryUpd)
                            if nQry < 0
                                ConOut("DLP04I02 codusr: AIF_ZCDUSR nao gravado (rc=" + ;
                                    cValToChar(nQry) + ")")
                            endif
                        endif
                    endif
                endif
            endif
        endif

    Recover
        ErrorBlock(oException)
        lRet     := .F.
        cErrType := "server_error"
        nStatus  := 500
        cErro    := "Falha interna na integracao Produto x Fornecedor."
    End sequence

    // finalizacao unica
    ErrorBlock(oException)
    if lActivated .and. ValType(oModel) == "O"
        Begin Sequence
            oModel:DeActivate()
        Recover
        End sequence
    endif
    if !Empty(cErroBlk)
        ConOut("DLP04I02 error: " + cErroBlk)
    endif
    if !Empty(cErroEnv)
        ConOut("DLP04I02 err-env: " + cErroEnv)
    endif
    if !Empty(cErroLog)
        ConOut("DLP04I02 model: " + cErroLog)
    endif

    if lRet
        if cOp == "GET"
            oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
                "Vinculo localizado pelo modelo oficial " + cMdlId + ".", cVerTag(), "")
            oJsonRet["data"] := oItem
        elseif cOp == "PUT"
            oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
                "Alteracao aceita pelo modelo oficial " + cMdlId + " " + ;
                "(commit reconhecido; confirmacao final via read-back governado).", cVerTag(), "")
        else
            oJsonRet := RETOBJ(oJsonRet, "200", "OK", ;
                "Exclusao aceita pelo modelo oficial " + cMdlId + " " + ;
                "(commit reconhecido; confirmacao final via read-back governado).", cVerTag(), "")
        endif
        oSelf:setStatus(200)
    else
        if Empty(cErro)
            cErro := "Operacao rejeitada pela integracao Produto x Fornecedor."
        endif
        oJsonRet := RETOBJ(oJsonRet, cValToChar(nStatus), "Erro", cErro, cVerTag(), cErrType)
        oSelf:setStatus(nStatus)
    endif
    oSelf:setResponse(oJsonRet:toJson())

    FreeObj(oItem)
    FreeObj(oJsonRet)
    FreeObj(oDados)
    RestArea(aArea)

Return .T.

/* -----------------------------------------------------------------------
   lPrepSA5Ident — valida apenas a identidade completa (6 campos).
   Reuso para GET/PUT/DELETE (PUT valida attrs a parte).
   ----------------------------------------------------------------------- */
static function lPrepSA5Ident(oDados, aMiss, cErro)

    local aReq  := aSA5Ident()
    local nI    := 0
    local lOk   := .T.
    local xVal  := NIL

    for nI := 1 to len(aReq)
        xVal := oDados:GetJSonObject(aReq[nI])
        // mesma regra de opcionais do lPrepSA5: REFGRD/FABR/FALOJA
        // aceitam vazio (presenca+tipo exigidos)
        if ValType(xVal) == "U" .or. ValType(xVal) <> "C" .or. ;
           (aReq[nI] <> "A5_REFGRD" .and. aReq[nI] <> "A5_FABR" .and. ;
            aReq[nI] <> "A5_FALOJA" .and. Empty(xVal))
            aadd(aMiss, aReq[nI] + iif(ValType(xVal) <> "U" .and. ValType(xVal) <> "C", "(tipo " + ValType(xVal) + ")", ""))
            lOk := .F.
        endif
    next nI

    if !lOk
        cErro := "Payload incompleto — identidade ausente/nula/invalida: " + ;
            lJoin(aMiss, ", ")
    endif

Return lOk

/* -----------------------------------------------------------------------
   lPrepSA5Attr — valida os atributos editaveis (PUT).
   ----------------------------------------------------------------------- */
static function lPrepSA5Attr(oDados, aMiss, cErro)

    local aAttr := aSA5Attrs()
    local nI    := 0
    local lOk   := .T.
    local lAny  := .F.
    local xVal  := NIL

    // PUT = subconjunto do catalogo: ao menos um campo presente;
    // presentes devem ser texto (mesma normalizacao da api-delpi)
    for nI := 1 to len(aAttr)
        xVal := oDados:GetJSonObject(aAttr[nI])
        if ValType(xVal) == "C"
            lAny := .T.
        elseif ValType(xVal) <> "U"
            aadd(aMiss, aAttr[nI] + "(tipo " + ValType(xVal) + ")")
            lOk := .F.
        endif
    next nI

    if lOk .and. !lAny
        lOk := .F.
        cErro := "Informe ao menos um campo do catalogo SA5 para alterar."
    elseif !lOk
        cErro := "Payload invalido — atributos com tipo indevido: " + ;
            lJoin(aMiss, ", ")
    endif

Return lOk

/*/{Protheus.doc} sa5Prod (PUT)
    Alteracao de atributos do vinculo via modelo oficial (UPDATE op).
/*/
WSMETHOD PUT sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn
Return lExecSA5Op(self, "PUT")

/*/{Protheus.doc} sa5Prod (GET)
    Consulta do vinculo via modelo oficial (VIEW op) — nao-SQL.
/*/
WSMETHOD GET sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn
Return lExecSA5Op(self, "GET")

/*/{Protheus.doc} sa5Prod (DELETE)
    Exclusao da linha do vinculo via modelo oficial (DeleteLine).
/*/
WSMETHOD DELETE sa5Prod WSRECEIVE WSRESTFUL DelpiProdForn
Return lExecSA5Op(self, "DELETE")

/*/{Protheus.doc} cVerTag
    Tag de versao do fonte — devolvida no campo 'id' de toda resposta
    para identificacao unambiguous do objeto compilado no RPO.
/*/
static function cVerTag()

Return "dlp04i02-0.8.3"

/*/{Protheus.doc} RETOBJ
    Padroniza o retorno JSON da API (mesmo contrato do product-master:
    code/message/detailedMessage/id/errorType).
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
