---
name: totvs-protheus-integration
description: Especialista TOTVS/Protheus para análise e integração ADVPL/TLPP, fonte versionada no Delpi-ti/protheus-erp, RESTALL, RPO, MATA010, MATA061, SB1/SA5 e api-delpi. USAR SEMPRE que a tarefa envolver integração TOTVS/Protheus — inventário de rotinas, CRUD, contratos, desenvolvimento de .PRW/.TLPP, revisão e handoff de compilação ERP.
---

# Especialista — Integração TOTVS/Protheus (escrita)

Aplique o protocolo canônico completo definido em:

- **Regra operacional**: `.cursor/rules/totvs-protheus-write-integration.mdc`
  (auto-carrega por globs; esta skill é o ponto de invocação explícita)
- **Guia ADVPL**: `api-delpi/docs/integrations/protheus-advpl-route-development-guide.md`
- **Playbook de superfície**: `api-delpi/docs/integrations/protheus-write-integration-playbook.md`
- **Evidência live**: `api-delpi/docs/integrations/evidence/protheus-rest-product-update-ledger.md`
- **Negócio TOTVS/DELPI**: `api-delpi/docs/api/padroes-totvs/`; **fontes primários**: `Delpi-ti/protheus-erp` (`master`@SHA); **espelho**: `docs/13-fontes-totvs-protheus/`

## Resumo operacional

1. Rotina oficial primeiro (`Delpi-ti/protheus-erp` master@SHA → espelho DELPI → TDN/SX3 → RESTALL vigente → POC TST01).
2. Escrita = REST governado + **rotina oficial compatível**: `MSExecAuto` para MATA010 quando suportado; MVC oficial para MATA061/SA5 após contrato e homologação. **Nunca** SQL/RecLock direto em `S*`.
3. Superfície api-delpi: gate OFF por default, pin de ambiente, `codusr` via Core,
   tracker antes da escrita, zero retry em timeout.
4. Contrato ExecAuto: campo confirmado (fonte/TDN) ou marcado `VALIDAR NO TST01`.
5. Escrita live: snapshot → TST01 → verify → PROD intacta → restore → ledger versionado.
6. Em revisão: rodar o checklist da regra sobre o diff; violação = «⚠ Desvio de integração TOTVS».

Saída esperada: `OPERAÇÃO | ROTINA OFICIAL | CONTRATO | GATE+PIN | IDENTIDADE | RASTREIO | EVIDÊNCIA`.

## Lições de runtime comprovadas — TST01 (2026-11-19)

Depuração live do `delpiproduto`/`delpiprodforn` — tratar como conhecimento de
primeira classe ao escrever QUALQUER handler de body:

- **Body request**: `cJSON := oSelf:GetContent()` **antes** de
  `oSelf:SetContentType("application/json")`, ambos dentro do `Begin Sequence`.
  `SetContentType` consome o buffer do request no HTTPREST; `GetContent` no init
  de `Local` gera throw não-recuperável. Ordem errada = body sempre vazio.
- **Parse**: `oDados:FromJson(cJSON)` retorna `.F.` mesmo em sucesso no build
  `7.00.240223P` — o legado do espelho (`04. Estoque/DLP04I01.PRW`,
  `05. Faturamento/DLP05W01.PRW`) ignora o retorno. Validar pelo conteúdo:
  `Len(oDados:GetNames()) == 0` ⇒ inválido. Nunca `!oDados:FromJson(...)` como gate.
- **Topologia TST01**: `:2001`/`:2002` compilam em `env_teste`; `:72002` em `api`.
  REST `:8061` (`/restall`) e `:8701` (`/rest`) são serviços/RPOs diferentes.
  Build "success" no TDS não prova objeto carregado — restart do serviço certo
  + probe por marcadores (`metadados` count, `id` de versão, `errorType`).
- **Tag de versão no envelope**: `id` único por build (ex.: `"dlp-v053-fj"`)
  torna a versão carregada auto-evidente na resposta — dispensando console.
- **Referência viva**: implementação de referência do padrão legado =
  `docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW` (WSRESTFUL,
  aadd triple `{CAMPO,valor,Nil}`, RETOBJ, FreeObj trio, RestArea).

## Corpo de conhecimento ADVPL — ecossistema DELPI + TDN

### Convenções do espelho (docs/13-fontes-totvs-protheus)

- **Nomenclatura**: `DLP<modulo><tipo><seq>` — módulo = código do módulo
  Protheus (02 Compras, 04 Estoque, 05 Faturamento, 06 Financeiro, 09 Fiscal,
  10 PCP, 34 Contábil, 36 Qualidade, 73 CRM); tipo = I (integração REST),
  W (webservice), F/J/P (processos/rotinas); legado usa prefixo `DEL*`
  (DEL04P01). Customizações de modelos: `<ROTINA>_DLP` (MATA010M_DLP).
- **Includes REST**: `#Include "TOTVS.CH"` + `#Include "RESTFUL.CH"`
  (+ `"FWMVCDEF.CH"` quando MVC).
- **Anatomia WSRESTFUL**: `WSRESTFUL <Nome> DESCRIPTION "..." FORMAT
  "application/json"` → `WSMETHOD <VERBO> <id> DESCRIPTION PATH '/v1/x'
  WSSYNTAX '/v1/x' TTALK "v1"` → `END WSRESTFUL`; implementação:
  `WSMETHOD <VERBO> <id> WSRECEIVE <parms> WSRESTFUL <Nome>`.
  Versão no PATH (`/v1/`) e no TTALK — evolução de contrato = `/v2/` novo.
- **Envelope canônico**: `RETOBJ(oObj, cCode, cMsg, cDetMsg, cIdToken)` →
  `{code, message, detailedMessage, id}` com `FwCutOff()` sanitizando
  (remove chars de controle — CP1252; literais não-ASCII = mojibake).
- **Higiene**: `Local aArea := GetArea()`/`RestArea(aArea)`; `FreeObj` em
  todo `JsonObject` criado; `Return .T.`/`SetRestFault` para erro HTTP.
- **Contexto cross-empresa**: `PREPARE ENVIRONMENT EMPRESA ".." FILIAL ".."
  MODULO ".."` quando a rotina exige (ver `DLP02J05`, `DLP05F03`).

### Semântica real das APIs (TDN + prova live TST01)

| API | Semântica comprovada |
|---|---|
| `oSelf:GetContent()` | retorna body como string; chamar ANTES de `SetContentType`, dentro do `Begin Sequence` |
| `SetContentType()` | consome o buffer do request no HTTPREST — depois dele `GetContent` vê vazio |
| `oJson:FromJson(c)` | retorna **NIL** em sucesso / **string de erro** na falha — NÃO lógico; `!FromJson()` inverte o sentido. Validar por `ValType(ret)=="U"` ou `Len(o:GetNames())==0` |
| `oJson["campo"]` / `GetJSonObject` | acesso a propriedade; ausente ⇒ `U` (NIL) — testar com `ValType()` |
| `GetNames()` | lista de chaves parseadas — prova de conteúdo populado |
| `FWJsonDeserialize` | alternativa documentada (retorna objeto/NIL); NÃO usada no ecossistema DELPI — preferir padrão provado |
| `SetResponse`/`SetStatus`/`SetRestFault` | resposta, código HTTP, falha REST nativa |

### Rotinas oficiais e mecanismos de escrita

- **MATA010 (SB1)** = MVC desde 12.1.17: form `SB1MASTER` + submodelos
  injetados por `MATA010M` (DH5, SB5, SVK, MdGridSA5, SBZ). ExecAuto oficial:
  `FWMVCRotAuto(oModel,"SB1",nOp,{{"SB1MASTER",aFields}})` ou `MSExecAuto`
  com triplas `{CAMPO,valor,Nil}`. **O modelo exige o tipo do campo**:
  `D`→date (`StoD`), `N`→numérico — string `""` em data = `FWNOSTRUCT`.
  O form **não expõe todo SX3**: `FWFormFieldsModel` rejeita ids ausentes
  (ex.: `B1_GRADE`) — catálogo elegível = SX3 ∩ form (dump `DLPDBG01.PRW`).
- **Ciclo MVC manual**: `FWLoadModel`→`SetOperation`→`Activate`→
  `SetValue("FORM",campo,val)`→`VldData`→`CommitData`→`GetErrorMessage`
  →`DeActivate`/`Destroy`. UPDATE exige `dbSeek` prévio no registro.
- **MSExecAuto clássico**: `PRIVATE lMsErroAuto := .F.` +
  `lMsHelpAuto`/`lAutoErrNoFile`; erro em `GetAutoGrLog()` — **o erro real
  está no FIM do log** (manter cauda, não cabeça).
- **MATA061 (SA5)** = MVC Model-2 (`DMATA061`), chave composta
  FILIAL+FORNECE+LOJA+PRODUTO+FABR+FALOJA+REFGRD — `MSExecAuto` NÃO se
  aplica; estratégia = modelo oficial (`DLP04I02` implementa).
- **Erros do modelo**: `oModel:GetErrorMessage()` devolve array com
  [form-origem, campo-origem, form-erro, campo-erro, id-erro, mensagem,
  solução, valor, valor-anterior] — `FWNOSTRUCT` = tipo errado,
  `VLDDATA_POST` = validação de negócio.

### Diagnostics e iteração TST01

- Tag de versão no `id` do envelope (ex.: `"dlp-v053-fj"`) — a resposta
  autodeclara o build carregado no RPO.
- `ConOut` para o console do AppServer — acessível via `console.log` do
  serviço. Diagnóstico remoto: `tools/DLPDBG01.PRW` (dump de campos do
  modelo — `u_DLPDBG01` via TDS/smartclient).
- Nunca logar conteúdo de body (segurança) — só `ValType`/`Len`.

### Modelo de dados Protheus (essencial p/ qualquer integração)

- **`D_E_L_E_T_`** = soft-delete: `'*'` excluído, `' '` ativo. Protheus
  **nunca hard-deleta** — DELETE oficial vira flag; qualquer leitura deve
  filtrar `D_E_L_E_T_ = ' '`. `R_E_C_N_O_`/`R_E_C_D_E_L_` são ids internos —
  nunca expor como chave de contrato.
- **Tabela física** `<alias><empresa><filial>` (SB1010, SB1020 — sufixo por
  filial); `xFilial("SB1")` resolve a filial corrente; relations oficiais do
  modelo aplicam `xFilial` sozinhos.
- **Campos memo (SX3 `M`)**: conteúdo fora da tabela física — leitura só via
  `MSMM()`; se a coluna não existir no físico (caso B1_VM_*/B1_OBS do TST01),
  o campo sai do contrato até materialização.
- **SX3 = dicionário declarativo, não contrato**: `X3_VALID` (expressão de
  validação), `X3_RELACAO` (código de validação), `X3_CBOX` (combo),
  `X3_F3` (consulta padrão), `X3_PICTURE` (máscara), `X3_VISUAL` (editável na
  tela), `X3_WHEN`. SX3 declara; o **modelo da rotina** decide o que é
  aceito — por isso SX3 ∩ form é o catálogo real.
- **Parâmetros `SX6`/`MV_*`** alteram comportamento do modelo — ex.:
  `MV_CADPROD` habilita submodelos/grade. Validar params do ambiente antes
  de assumir presença de campos/submodelos.
- **Campos custom**: faixa alfabética reservada por cliente (Delpi usa
  Z/Y/X em muitos); são campos SX3 normais — mesmas regras.

### Mapa de rotinas oficiais × mecanismo

| Rotina | Domínio | Mecanismo comprovado/referência |
|---|---|---|
| MATA010 | SB1 produtos | MVC `SB1MASTER`; `FWMVCRotAuto`/`MSExecAuto` (DLP04I01) |
| MATA020 | SA1 clientes | ExecAuto suportado (historicamente) |
| MATA030 | SA2 fornecedores | ExecAuto suportado (historicamente) |
| MATA061 | SA5 prod×fornecedor | MVC Model-2 `DMATA061` — sem MSExecAuto (DLP04I02) |
| MATA120/160 | SC5/SC6 pedidos | ExecAuto parcial — validar por release |
| MATA650/250 | SC4 OP/apontamento | ExecAuto |
| FINA070/080 | SE1/SE2 títulos | ExecAuto histórico |

Mecanismo e campos do form variam por release/parâmetro — **VALIDAR NO
TST01 por ambiente** antes de promover contrato.

### ExecAuto/MVC em profundidade

- Triplas `{CAMPO, valor, Nil}` com **valor tipado** (D=`StoD`, N=numérico,
  C=string) — o modelo valida estrutura (`FWNOSTRUCT` = tipo errado).
- `GetAutoGrLog()` = dump sequencial de campos processados + blocos
  `"Erro -->"` no **final** — ao truncar para resposta, manter a cauda.
- `PRIVATE lMsErroAuto := .F.` (não LOCAL — a rotina interna a enxerga),
  `lMsHelpAuto := .T.`, `lAutoErrNoFile := .T.`.
- `oModel:GetErrorMessage()` = array [form-origem, campo-origem, form-erro,
  campo-erro, id-erro, msg, solução, valor, valor-anterior].
- UPDATE via modelo manual exige `dbSeek` prévio posicionando o registro.

### Runtimes REST e appserver

- `/rest` = HTTPREST clássico; `/restall` = REST 2.0 — **mesmo WSRESTFUL,
  daemon diferente** (pool, entrega de body, reciclagem pós-build).
- Auth nativo: `/rest/api/oauth2/v1/token` quando oauth2 configurado.
- Serviço REST = processo/appserver próprio com RPO/ini próprios:
  `[HTTPREST]`, `[HTTPV11]` (URI `/rest`), pool de threads,
  `MAXSTRINGSIZE`. Compilar ≠ carregar — restart relê o RPO.
- TDS compila no RPO da **conexão ativa**: porta × ambiente × serviço.

### ADVPL essencial (referência rápida)

- `ValType`: C N D L A O J U B M — ausente/indefinido = `"U"`.
- Escopo: `LOCAL` (função), `STATIC` (arquivo), `PRIVATE` (visível na
  cadeia de chamada — por isso `lMsErroAuto` exige PRIVATE), `PUBLIC`.
- `ErrorBlock` + `Begin Sequence`/`Recover` = try/catch; `Break(e)` entrega
  o erro ao Recover; restaurar com `ErrorBlock(oAnterior)` no fim.
- Conversões: `StoD/DtoS/CtoD`, `Val/Str/cValToChar`, `AllTrim/RTrim`.
- `WSMETHOD`/`WSRESTFUL` são `#xcommand`/`#xtranslate` do `RESTFUL.CH` —
  viram `Function ___REST_*` na compilação.
- `user function X()` = pública/invocável (u_X); `static function` =
  privada ao arquivo (helpers internos).
- `JsonObject`: `o["k"]`, `GetJSonObject`, `GetNames`, `ToJson`; array de
  objetos vira array ADVPL; `FreeObj` obrigatório.

## Atualização de autoridade de fontes (2026-11)

- **Fonte versionada primária ADVPL/TLPP:** repositório privado `Delpi-ti/protheus-erp`, branch `master`, consultado no HEAD vigente via GitHub autorizado. Registrar `SOURCE_REPO/BRANCH/SHA/PATH/BLOB_SHA` em cada análise.
- `docs/13-fontes-totvs-protheus/` do `delpi-central` é espelho/cópia de referência; comparar SHA do blob com o repositório ERP, não tratá-lo como versão automaticamente atual.
- Código no GitHub prova **fonte versionado**, não prova compilação, publicação no RPO ou execução em PRD/TST01. Para runtime exigir inspeção autorizada do RPO/versão e/ou evidência da equipe ERP. RESTALL demonstra superfície publicada, não equivalência binária nem sucesso da escrita.
- Em SB1, `DLP04I01.PRW` usa MATA010/`MSExecAuto` para CREATE/UPDATE com 22 campos na fonte inspecionada. Em SA5, `Dmata061.prx` define modelo MVC Model-2 e chave `FILIAL+FORNECE+LOJA+PRODUTO+FABR+FALOJA+REFGRD`; **não** assumir que `MSExecAuto` com arrays de MATA010 se aplica a MATA061.
- `MATA010M_DLP.PRW` contém submodelo `Model061` (grid SA5) condicionado a `MV_CADPROD` e permissões. Investigar essa alternativa de reuso antes de criar integração separada, sem inferir runtime.
- Não há prova de rota REST de escrita SA5 publicada no último inventário; MATI060/EAI não estava configurado. Revalidar se houve mudança. Operações CRUD requerem contracts oficiais, autorização do owner e read-back pela chave completa.
- Só escrever por rotina oficial validada: ExecAuto quando suportado; modelo MVC se aprovado e homologado. Jamais `RecLock` ou SQL de escrita direta. Separar `PROVEN_SOURCE`, `PROVEN_RUNTIME`, `TO_INVENTORY` e `TEST_NOT_RUN`.

## Workspace de desenvolvimento — decisão PO

Para os novos fontes ADVPL DELPI, **escrever e versionar somente em** `api-delpi/integrations/protheus-advpl/modules/<capability>/src/` no repositório `delpi-central`; contratos/testes junto do módulo; pacote gerado via `packaging/` e manifesto em `handoffs/` conforme `api-delpi/integrations/protheus-advpl/README.md`. `Delpi-ti/protheus-erp` permanece referência de leitura para upstream@SHA **sem push, alteração ou PR** neste ciclo. `docs/13-fontes-totvs-protheus/` é espelho referencial, não workspace editável. Não gerar ZIP de cópias manuais nem compilar/deploy por commit.

## Regra vinculante — SQL e rotas de leitura NAO definem implementacao ADVPL

- Para desenvolver, ampliar ou revisar qualquer `.PRW`/`.TLPP`, exigir rastreio `operacao → rotina oficial TOTVS ou customizacao comprovada → contrato suportado (ExecAuto/MVC/outro documentado) → fonte ERP repo@SHA → teste TST01 autorizado`. A ausencia de contrato oficial bloqueia o metodo candidato; nao preencher lacunas por inferencia SQL.
- Consultas SQL/ODBC, SX3, `api-delpi/app` repositories e endpoints READ da API DELPI sao **evidencia auxiliar de schema, valores, consistencia e diagnostico**, nao contrato funcional de operacao ADVPL, nao fonte de regras de cadastro/persistencia e nao modelo para implementar `READ/CREATE/UPDATE/DELETE` de fachada Protheus. 
- **Proibido** transplantar `SELECT`/joins/filtros/queries de repositories ou payloads das rotas SQL para os handlers `.PRW`; completar campos faltantes via consultas SQL; reproduzir validacoes, triggers ou efeitos colaterais por DML direto; usar `RecLock` como bypass das rotinas de negocio. Mesmo `READ` novo do lado Protheus exige mecanismo oficial validado, nunca copia de rota SQL.
- Auditoria de consistencia por SELECT autorizado pode ocorrer **fora do fluxo ADVPL**, em superficie de leitura governada, explicitamente separada do contrato de escrita e sem promover resultado a postcondition suficiente. Preservar os endpoints existentes de leitura; esta regra nao proibe seu uso legitimo por outros consumers.
- Revisao obrigatoria: `SQL_USED_AS_GROUNDING=YES|NO`, `OFFICIAL_ROUTINE`, `SOURCE_PATH+SHA`, `WRITE_MECHANISM`, `UNPROVEN_ASSUMPTIONS`. Falta de rota oficial: `TO_INVENTORY`, jamais fallback SQL.
