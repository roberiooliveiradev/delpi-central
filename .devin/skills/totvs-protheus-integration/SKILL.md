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
3. Superfície api-delpi: gate OFF por default, pin de ambiente, `codusr` via Core
   **e propagado upstream** (obrigatório — ver auditoria do ator abaixo),
   tracker antes da escrita, zero retry em timeout.
4. Contrato ExecAuto: campo confirmado (fonte/TDN) ou marcado `VALIDAR NO TST01`.
5. Escrita live: snapshot → TST01 → verify → PROD intacta → restore → ledger versionado.
6. Em revisão: rodar o checklist da regra sobre o diff; violação = «⚠ Desvio de integração TOTVS».

Saída esperada: `OPERAÇÃO | ROTINA OFICIAL | CONTRATO | GATE+PIN | IDENTIDADE | RASTREIO | EVIDÊNCIA`.

## Padrões de projeto DELPI (design patterns comprovados)

**Base de decisão obrigatória**: toda rota/customização nova deve compor
estes padrões — e **toda lição comprovada em runtime deve ser registrada
aqui antes de encerrar a sessão** (o especialista cresce a cada iteração;
conhecimento que fica só na conversa se perde). Nomear o padrão no código
e no handoff ajuda o revisor a conferir aplicação correta.

| Padrão | Regra | Referência viva |
|---|---|---|
| **PAD-AUDITORIA-ATOR** | Toda escrita carrega `codusr` (meta-campo, resolvido via Core — nunca do cliente) e persiste em `AIF_ZCDUSR` pós-commit oficial. **Obrigatório** — proibido rota sem previsão; mecanismo ausente ⇒ `TO_INVENTORY`/escalar | DLP04I01/DLP04I02 v-codusr; `MA020TDOK`/API fornecedores (Gabriel) |
| **PAD-JANELA-TEMPO-AIF** | Capturar `Left(Time(),5)` **antes** da rotina oficial; patch casa `AIF_DATA=hoje AND AIF_HORA>=início`. `Time()` traz `HH:MM:SS` (8) mas `AIF_HORA` grava `HH:MM` (5) — sem truncar, a janela `>=` nunca casa a linha da própria execução (prefixo menor < string ⇒ 0 rows silencioso — prova TST01 2026-11-19) | bugfix dlp-v056/0.5.1-codusr |
| **PAD-META-CAMPO** | Campos de controle (`codusr`, futuros) viajam no mesmo body fora do catálogo de campos de negócio — excluídos da validação/ExecAuto; quem consome extrai antes da rotina | `lPrepSB1` loop codusr; `lPrepSA5` (itera só ident/attrs) |
| **PAD-REPR-COMPLETA** | Update cadastral = representação completa (read-merge-write); omissão zera coluna no ExecAuto | `delpiproduto` 283 campos |
| **PAD-TAG-VERSAO** | `id` do envelope identifica o build no RPO — bumpar a cada mudança e conferir no probe | `dlp-v05x-*`, `dlp04i02-x.y.z-*` |
| **PAD-PATCH-NAO-FATAL** | Pós-commit oficial: anotações auxiliares (auditoria, complementos) nunca negam o write — falha ⇒ `ConOut`, não erro de resposta | bloco `AIF_ZCDUSR` nos 2 PRWs |
| **PAD-GETCONTENT-FIRST** | `GetContent()` antes de `SetContentType()`, ambos dentro do `Begin Sequence` — ordem errada = body vazio | regressão comprovada TST01 |
| **PAD-VALIDA-CONTEUDO** | Validar parse pelo conteúdo (`Len(GetNames())==0`), nunca pelo retorno de `FromJson` (NIL=ok / string=erro, não lógico) | semântica TDN comprovada |

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
- **URI inclui o nome do serviço WSRESTFUL**:
  `/rest/<NomeDoServico>/<path do WSMETHOD>` — ex.:
  `WSRESTFUL DelpiProduto ... PATH '/v1/IncProduto/alterar'` →
  `PUT /rest/delpiproduto/v1/IncProduto/alterar`. Sem o prefixo do
  serviço = 404 mesmo com objeto compilado (lição TST01 2026-11-19).
- Auth nativo: `/rest/api/oauth2/v1/token` quando oauth2 configurado —
  **form-urlencoded** (`grant_type=password&username&password`); o
  endpoint rejeita JSON ("Está faltando grant_type").
- **Alvos canônicos (drift resolvido 2026-11-19):**
  - TST01 = `192.168.1.233:8701` (`/rest`, ambiente `api`, TDS `233:2002`,
    serviço `dev_rest_minha_delpi`, RPO `apo\debug\api\Rest\custom.rpo` —
    DB-backed via `RepositInDataBase=1`);
  - daemon `:8061`/`/restall` do TST01 (TDS `233:2001`) **descontinuado** —
    não entrega body ao WSRESTFUL nem carrega os objetos Delpi;
  - produção = `192.168.1.231:8061/restall` — **API `delpi` viva**
    (deploy Gabriel 26/10; prova 19/11: `GET suppliers/00000101` → 200).
    `URL_REST@1`=`231:8061` + `BASE_PATH`=`/restall`; pin casa; writes
    OFF por gates até autorização. A API de fornecedores é **TLPP REST**
    (`@Post("/delpi/api/v1/suppliers")` + `oRest:`), não WSRESTFUL;
  - `PARAMETROS_MINHADELPI.AMBIENTE=2` carrega `URL_REST=…:8701/rest`
    (o `/rest` vai **dentro** da URL_REST; `BASE_PATH` vazio);
    `AMBIENTE=1` usa origem pura + `BASE_PATH=/restall`;
  - TLPP REST responde `501` em path sem método anotado (ex.: GET na
    coleção `/suppliers` — só `@Post` existe) — não confundir com
    "objeto ausente" (404).
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

### ADVPL — armadilhas e boas práticas comprovadas

- `=` em comparação de strings é **fuzzy** (prefixo); `==` é exata — em
  `dbSeek`/validação use `==` ou `AllTrim`.
- Chaves de busca são **padded**: `dbSeek(xFilial("SB1") + PadR(cCod, 15))`
  — espaço à direita faz parte da chave física.
- `Empty()` detecta vazio em C/N/D/L — preferir a `== ""`/`== 0` por tipo.
- Literais **ASCII puro** — binário em CP1252; acento em string literal =
  mojibake na resposta HTTP.
- `MSMM(cCampo)` lê campos memo; campo memo sem coluna física NÃO é
  selecionável por SQL nem aceito pelo form.
- `GetMv("MV_XXX")` lê parâmetro SX6; `PutSx1/PutSx3` criam dicionário em
  atualizadores.
- Arrays são 1-based; `aAdd`, `aScan`, `aSort`, `ASize`; hashes por nome
  via `JsonObject` (não há map nativo clássico).
- `dbSelectArea`/`dbSeek`/`While !Eof()`/`Skip` — navegação legada;
  `SetDeleteme(.F./.T.)` filtra registros deletados manualmente;
  `RestArea(aArea)` obrigatório ao sair.
- `user function` para entry points; `static function` para helpers;
  função pública inexistente no RPO = runtime error "function not found".

### Dicionário SX3 em profundidade

| Atributo | Papel |
|---|---|
| `X3_VALID` | expressão ADVPL avaliada na validação do campo (modelo/UI) |
| `X3_RELACAO` | código retornado após validação (lookup/integridade) |
| `X3_CBOX` | combo de valores válidos (`1=Sim;2=Nao`) — o modelo só aceita os valores listados |
| `X3_F3` | consulta padrão SXB associada (lookup F3) |
| `X3_PICTURE` | máscara de formato (`@!`, `999.99`) — afeta validação de estrutura |
| `X3_WHEN` | expressão que habilita/desabilita edição do campo |
| `X3_VISUAL` | campo editável na tela da rotina (S=sim) |
| `X3_CONTEXT` | contexto de exibição do campo no browse |
| `X3_PROPRI` | S=sistema (não alterar), U=usuário (editável), R=somente leitura |
| `X3_RESERV`/`X3_BROWSE` | tamanho reservado/exibição em browse |

Regra prática: campo `X3_VISUAL`/`X3_PROPRI=R` ou com `X3_CBOX` restrita
pode existir no form mas falhar na gravação — classificar por
comportamento do modelo, não por SX3 sozinho.

### SXB (consultas padrão F3)

`SXB` define consultas de lookup por alias (ex.: `SB1` → produto).
`X3_F3` aponta o campo para a consulta certa — em integração, a FK do
payload deve respeitar a mesma consulta (código existente na tabela
relacionada) ou a validação oficial rejeita.

### ExecAuto `aRotina` e contexto

- `PRIVATE aRotina := {}` ou com entradas `{{"NOMEDOBRW",opcao,nivel}}`
  quando a rotina consulta opções de menu — validar por rotina.
- Terceiro elemento da tripla `{CAMPO,valor,NIL}` = slot reservado da
  validação do ExecAuto (manter NIL).
- Rotinas podem depender de `PREPARE ENVIRONMENT` (empresa/filial/módulo)
  — ExecAuto herda o ambiente do processo; em REST o ambiente é o do
  serviço (section `environment` do ini).

### TLPP vs ADVPL (`.tlpp` vs `.prw`)

- `.prw` = ADVPL clássico (funções, `user function`, pseudo-OO via
  `#xcommand`) — todo o ecossistema DELPI existente.
- `.tlpp` = TLPP moderno (classes reais, namespaces, tipagem) — compila
  no mesmo RPO; REST/MVC funcionam igual.
- Escolha: manter `.prw` enquanto o ecossistema e os includes do projeto
  forem ADVPL — coerência com legado e com os guias.

### Jobs e processamento assíncrono

- `StartJob("u_Funcao", cEnv, .T., params)` — thread assíncrona com
  ambiente próprio; `FWExecJob` = agendador de jobs no menu.
- Job/thread não herda área nem transação do caller — abrir ambiente e
  áreas próprias; `RestArea`/`ErrorBlock` por thread.

### Atualizador (compatibilizador)

- Mudanças de dicionário (campo SX3 novo, SXB, parâmetro SX6, gatilho
  SX7) são entregues via **fonte de update** (`u_<nome>` executado pelo
  compatibilizador no login) — `PutSx1`, `PutSx3`, `PutSx6`, `PutSx7`.
- Nunca criar coluna física via SQL direto — dicionário e físico
  dessincronizam (origem do caso B1_VM_* no TST01).

### Triggers, gatilhos e user exits

- `SX7` = gatilhos de campo/tabela (disparam em qualquer escrita — ExecAuto
  incluso); modelo MVC chama `bVldPre`/`bVldPos`/`bCommit`/`bCancel` do
  ModelDef.
- User exits legados: `MTA*`/`M010*`/`A<VLD>` — pontos de customização que
  podem interferir na gravação; investigar quando validação oficial
  falhar sem causa aparente.

### HTTP client outbound (Protheus → externo)

- `FWRest():New(url)`/`RestClient` para callbacks/webhooks do ERP para
  api-delpi; timeout obrigatório; secrets nunca em fonte (SX6 ou serviço
  de configuração).

### Segurança e contexto de execução

- REST executa como **usuário de sistema do serviço** — não há usuário
  final no Protheus; a identidade de negócio (`codusr`) é dado do
  contrato/ledger, não autenticação ERP.
- **Auditoria do ator real — REGRA OBRIGATÓRIA (diretriz do PO
  2026-11-19):** toda rota DELPI de escrita no Protheus **deve** carregar
  o código Protheus do usuário (`codusr`/`protheus_user_id`) e persisti-lo
  para auditoria. **É proibido entregar rota sem essa previsão** — se o
  mecanismo não existir no ambiente (sem `AIF_ZCDUSR`, entidade sem linha
  AIF), inventariar/escalar, nunca silenciar: rota sem capacidade de
  auditoria do ator é rota incompleta.
- **`codusr` → `AIF_ZCDUSR` (padrão Gabriel/MATA020, adotado em DLP04I01/
  DLP04I02)**: meta-campo no body upstream, ignorado pela validação de
  campos do catálogo; após commit oficial bem-sucedido,
  `UPDATE AIF SET AIF_ZCDUSR=<codusr>` nas linhas recém-criadas
  (`AIF_TABELA` + `AIF_CODPRO`/`AIF_CODIGO` + `AIF_DATA=hoje` +
  `AIF_HORA>=início`). Não-fatal por desenho — falha do patch não nega
  o write. api-delpi injeta `codusr` resolvido via Core; cliente nunca
  informa (`_FORBIDDEN_KEYS`). SB1 usa `AIF_CODPRO`; SA2 usa
  `AIF_CODIGO`+`AIF_LOJA`. Inventário TST01 2026-11-19: AIF010 só tinha
  linhas SA2/SB1 — SA5 pode não gerar histórico (`VALIDAR NO TST01`).
- `TTALK "v1"` no WSMETHOD versiona o verbo — nova versão = PATH `/v2/`,
  nunca quebrar `/v1/` em uso.
- `SetRestFault(code, msg)` = erro HTTP nativo; envelope RETOBJ para o
  contrato DELPI.

### Ferramentas de desenvolvimento

- **TDS VS Code**: compilação (RPO token), debug com breakpoints,
  Inspetor de Objetos (diff/cópia entre RPOs), monitor de conexões.
- **SIGAADV**: utilitários de dictionary (SDU/SDF), visualizador de
  dados, Schedule, License Server.
- **console.log** do serviço = saída de `ConOut`; `FWFileWriter`/`LogFile`
  para arquivos de log.
- Diagnóstico remoto: `tools/DLPDBG01.PRW` — padrão reutilizável: criar
  `u_<nome>` + compilar + executar via TDS/smartclient + ler ConOut.

### Catálogo de erros comprovados (modelo/runtime)

| Erro | Origem | Significado/correção |
|---|---|---|
| `FWNOSTRUCT` | FWFormFieldsModel | valor difere do tipo do campo — tipar com `StoD`/`Val` antes da tripla/`SetValue` |
| `O id de formulario 'X' nao e valido` | FWFormFieldsModel | campo fora do form do modelo — remover do contrato (SX3 ∩ form) |
| `VLDDATA_POST` | VldData/CommitData | validação de negócio pós-carga (X3_VALID/bVldPos/PE) — investigar a regra, não o transporte. Opaco quando o PE retorna `.F.` sem mensagem útil |
| `FWNOLIST` | FWFormFieldsModel | valor fora do `X3_CBOX` — enviar chave da combo (`'1'/'2'`), não rótulo/legado (`'N'`) |
| `A<rot>TOK` / PE de permissão | user exit | `RetCodUsr()`/`SuperGetMV("MV_*US*")` falham em REST: o usuário é o técnico do serviço (SYS_USR), não o operador — ex.: `A010TOK`+`MV_ZUSMPLB` bloqueia MP no TST01 |
| `SB5010_UNQ` e afins | InTTS/commit | flush de complemento multi-filial (SB1 compartilhada × SB5/SBZ exclusivas) — diagnosticar PEs `MT010ALT`-style antes de culpar o contrato |
| `Erro -->` no `GetAutoGrLog` | ExecAuto | bloco de erro fica no FIM do log — ler a cauda, não a cabeça |
| `AIF_ZCDUSR` vazio pós-patch | janela `AIF_HORA` | `Time()` retorna `HH:MM:SS` mas `AIF_HORA` é `HH:MM` — truncar `Left(Time(),5)` (PAD-JANELA-TEMPO-AIF) |
| `THREAD ERROR` | console appserver | exceção não tratada; corpo do erro no `console.log`/`error.log` |
| `variable does not exist`/`function not found` | runtime | PRIVATE errado / função ausente no RPO (compilação ≠ carga) |
| `array out of bounds` | runtime | array é 1-based; tripla `{CAMPO,val,NIL}` mal formada |
| `type mismatch` | runtime | atribuição de tipo errado (`""` em N/D) |
| `Cannot find method` | runtime | objeto NIL ou método ausente no build |

### MVC — anatomia de ModelDef/ViewDef (fonte: `Dmata061.prx`, `MATA632_DLP`, `MATA010M_DLP`)

- `ModelDef()` retorna `oModel := MPFormModel():New(<id>, bVldPre, bVldPos,
  bCommit, bCancel)`; submodelos: `AddFields('ID',NIL,oStru)` (fields) /
  `AddGrid('GRID','PAI',oStru,,{|o|bLinhaOk(o)})` (grid Model-2);
  `SetRelation('GRID', {{'FIL','xFilial("SA5")'},{'CAMPO','CAMPO'}},
  ALIAS->(IndexKey(n)))`; `SetPrimaryKey({...})`.
- `ViewDef()` retorna `FWFormView():New()`; `AddField('VIEW_X',oStru,'MOD_ID')`
  / `AddGrid('GRID_X',oStru,'MOD_ID')` mapeiam struct → id de model.
- Delegação oficial: `ModelDef()`/`ViewDef()` custom podem devolver
  `FWLoadModel("ROTINA")`/`FWLoadView("ROTINA")` (MATA632_DLP).
- ExecAuto MVC: `FWMVCRotAuto(oModel,"ALIAS",nOp,{{"FORM_ID",aCampos}},,.T.)`
  — caminho oficial dentro de `A010Auto`; retorna lógico, erros via
  `GetErrorMessage`.
- Em evento/hook do modelo: `FWModelActive()` = modelo corrente
  (ex.: `Mta010Ceme` acessa `SB5DETAIL` via `oModel:GetModel`).
- Eventos oficiais de MATA010 vivem na classe `MATA010EVDEF` — customizações
  seguem o mesmo formato (`<ROTINA>EVDEF`).

### User exits e pontos de entrada oficiais

- Convenção: a rotina chama `ExistBlock("NOME")` + `ExecBlock("NOME",...)`
  ou função fixa (`MT010CAN`, `NMt010Can`, `MT061MN`, `MTA010MNU`,
  `MA650BUT`) — existem só se compilados no RPO.
- Menu: `MT<rot>MNU`/`MT061MN` injetam opções em `aRotina`; o menu MVC é
  montado por `MenuDef()` com `ADD OPTION`.
- Eventos MVC customizáveis: `bVldPre/bVldPos/bCommit/bCancel` +
  `bLinePre/bLinePost` nas grids do ModelDef.
- Gatilhos SX7 e `X3_RELACAO` disparam também sob ExecAuto — investigá-los
  quando a validação oficial falhar sem causa no contrato.
- Descoberta: `grep "ExistBlock"` no fonte oficial da rotina + página TDN
  "pontos de entrada <rotina>".

### aRotina — os dois formatos

- **Clássico**: `{"Titulo","FUNCAO",nReserv,nOperacao,nAcesso,lBmp}`.
- **MVC**: `ADD OPTION aRotina TITLE "X" ACTION "VIEWDEF.ROTINA" OPERATION n
  ACCESS n` — construído em `MenuDef()`; códigos de operação vistos no
  espelho: 2=visualizar, 3=incluir, 4=alterar, 5=excluir, 9=copiar.
- **MVC**: `ADD OPTION aRotina TITLE "X" ACTION "VIEWDEF.ROTINA" OPERATION n
  ACCESS n` — construído em `MenuDef()`.
- ExecAuto pode herdar `aRotina` do caller (`PRIVATE aRotina`) — rotinas com
  dependência de menu precisam do array correto.

### EAI — mensagem única TOTVS (adapter oficial alternativo)

- `Dmata061.prx` expõe `IntegDef(cXML,nTypeTrans,cTypeMessage,cVersion)`
  chamando `MATI060(...)` — o **adapter EAI do SA5**: integração por
  mensagem única (XML) em vez de escrita direta no form.
- Exige EAI configurado no ambiente (canais/schedule) — TST01 não tinha;
  classificar `TO_INVENTORY` antes de eleger como mecanismo.
- Descobrir adapters de outras rotinas por `IntegDef`/`MATI*` no fonte
  oficial — presença no fonte ≠ configurado no ambiente.

### SOAP — WSSERVICE (servidor) e WSCLIENT (cliente)

- Servidor: `WSSERVICE <Nome> DESCRIPTION ".." NAMESPACE ".."` + `WSDATA
  <campo> AS <Tipo>` + `WSMETHOD <Metodo>` + `END WSSERVICE` — publica WSDL
  no endpoint SOAP do appserver; hoje o padrão DELPI novo é REST.
- Cliente: bloco gerado `WSCLIENT <Nome>`/`ENDWSCLIENT` + `WSMETHOD <M>
  WSCLIENT <Nome>` (ver `10. PCP/apsws/MTPURCHASESREQUEST.PRW`) — o ERP
  consome WSDL externo.
- Checagem de dependência de build: `FindFunction("XMLCHILDEX")`,
  `Type("FUNCAO")`, `ExistBlock("NOME")` — evitar runtime error por
  função inexistente no RPO.

### Compatibilizador — dicionário via fonte (nunca DDL)

- Mudança de dicionário entra por fonte `u_<nome>` executado no updater:
  `PutSx1` (perguntas SX1), `PutSx2` (tabelas), `PutSx3` (campos), `PutSx6`
  (parâmetros), `PutSx7` (gatilhos), `PutSXB` (consultas) — assinatura
  posicional longa; ver `10. PCP/DIGR850.prw` e `BoletoActvs.prw`.
- Idempotente: checar existência antes de gravar; registrar no cabeçalho
  release/parâmetros afetados. Coluna física criada por SQL fora do
  dicionário dessincroniza SX3×físico (origem do caso B1_VM_* no TST01).

### SQL embutida — somente leitura

- `TCGenQry`/`TCQuery`/`TopConn` + `dbUseArea(.T.,"TOPCONN",cQry,"TRB")`
  aparecem no espelho para **consulta** (relatórios/buscas) — aceitável como
  leitura auxiliar dentro do PRW; **nunca** INSERT/UPDATE/DELETE e nunca
  como substituto de rotina oficial (regra mandatória do projeto).
- Alias de trabalho: `CriaTrab()`/`Select("TRB")`; fechar com `dbCloseArea`.

### Transações, locks e escrita custom

- `Begin Transaction`/`End Transaction`/`DisarmTransaction` envolvem
  operação composta; o modelo MVC já controla TTS própria — transação
  externa só quando múltiplas rotinas precisam de atomicidade.
- `RecLock`/`MsUnLock`/`SoftLock`/`MsAppend`: **proibidos em `S*`** no
  padrão DELPI; válidos apenas em tabela custom `Z*` ou dentro de user
  exit oficial.

### Parâmetros SX1/SX6 e `mv_par`

- Rotinas com parâmetros de execução leem SX1 (`Pergunte(cPerg,.T.)`) —
  em ExecAuto/job, definir `mv_par01..mv_parNN` (PRIVATE) antes da chamada
  em vez de abrir pergunta.
- `PutSx1` cria grupo de perguntas; `GetMv("MV_*")`/`PutMV`/`SuperGetMV`
  para parâmetros SX6 por filial.

### Funções clássicas — referência rápida

| Domínio | Funções |
|---|---|
| String | `AllTrim/At/RAt/SubStr/Left/Right/StrTran/PadR/PadL/Space/Replicate/Asc/Chr/Len` |
| Data | `Date()/dDataBase/DtoS/StoD/CtoD/Day/Month/Year/ElapTime` |
| Número | `Val/Str/cValToChar/Round/Int/Abs/Max/Min/Mod` |
| Array/hash | `aAdd/aSize/aScan/aSort/aClone/aEval/Array` ; hash por nome = `JsonObject` |
| Tipo/nil | `ValType/Type/Empty/Iif/IsNil` |
| DB navegação | `dbSelectArea/dbSetOrder/dbSeek/dbFound/Eof/Bof/Skip/RecNo/LastRec/dbGoTop` |
| DB estrutura | `dbStruct/FieldName/FieldPos/FieldGet/FieldPut`; meta `SX3->(dbSeek)` |
| Índices | `IndexKey(n)/OrdSetFocus/IndRegua/dbSetIndex` |
| Arquivo/temp | `CriaTrab/Select("TRB")/File()/fErase/FT_FUse/FT_FReadLn/MemoWrit/MemoRead` |
| Ambiente | `GetEnv/GetEnvServer/GetSrvProfString/RetCodUsr/__cUserId` |
| Parâmetro | `GetMv/PutMV/SuperGetMV/Pergunte` |
| Introspecção | `ExecBlock/ExistBlock/FindFunction/Type/FunName/ProcName/IsInCallStack` |
| Job/agenda | `StartJob/FWExecJob/CheckSched` |
| HTTP out | `FWRest():New()/HttpGet/HttpPost` |
| JSON | `JsonObject/FWJsonSerialize/FWJsonDeserialize` |
| Encoding | `FwCutOff/OemToAnsi/EncodeUTF8/DecodeUTF8/Encode64/Decode64` |
| Log/diag | `ConOut/FWFileWriter/VarInfo/GetCodeBlock/MsgStop` |
| Tempo | `Seconds()/Time()/Sleep` |
| Erro | `ErrorBlock/Break` + `oError:Description` |

### Contexto de execução e flags MVC

- `INCLUI`/`ALTERA`/`EXCLUI` = flags do fluxo dentro de validações de campo
  (ex.: `M010IniQtdSer` em `MATA010M_DLP` ramifica por `INCLUI`).
- `M->CAMPO` = valor da linha corrente em validação/gatilho; na API do
  modelo usar `oSubModel:LoadValue("CAMPO",valor)`.
- `PREPARE ENVIRONMENT EMPRESA e FILIAL f MODULO "FAT" [TABLES "SA1"]` +
  `RESET ENVIRONMENT` — jobs/processos sem login (DLP02J01/J02, DLP73F03);
  em REST o ambiente vem da `environment=` do ini do serviço.

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
