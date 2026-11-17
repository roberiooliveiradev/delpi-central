# PRC — Descrição obrigatória + Isolamento de «Minhas Solicitações»

**TASK_ID:** `PRC-DESCRIPTION-REQUIRED-AND-MY-REQUESTS-OWNERSHIP-ISOLATION-01`
**Commit:** `6116a5231a` (main) · **Status:** HML publicado, PRD pendente no momento da escrita

## 1. Causa-raiz

| Defeito | Causa |
|---|---|
| CREATE aceitava `description` vazia | `validate_create_payload` tratava `""` como valor válido para qualquer `kind="text"`; `customerReference` (B1_REFEREN) precisava continuar admitindo vazio — faltava distinção no spec. |
| Edição/update podia zerar a descrição | `validate_draft_change` normalizava `""` sem checar obrigatoriedade. |
| «Minhas Solicitações» mostrava casos de terceiros | A rota de listagem nunca expunha `own_scope` — analistas recebiam a fila global (assigned ∪ requester ∪ global_scope) na superfície pessoal. |
| Formulário não bloqueava | `validateStep` pulava validação de branco em `kind === "text"`. |

## 2. Contratos

### Antes → Depois

- `FieldSpec` + `allow_blank: bool = False`; `customerReference.allow_blank=True`
  (preserva o gate de owner — B1_REFEREN opcional no ERP).
- `GET /v1/product-registration/requests` + query `scope` ∈
  `mine|authorized` (ausente = comportamento vigente — retroativo).
- `GET /v1/product-registration/requests/{id}` + query `scope=mine` →
  caso alheio responde `not_found` (anti-enumeração, sem 403 que
  vaze a existência do id).
- `reference_data.fields[]` + `allowBlank` exposto ao frontend.
- EVA `product_registration.list`/`detail` + campo `scope` (mesmo
  service, mesmo `PrcActor`) — 6 tools preservadas.

### Regra de escopo

`scope=mine` → `requester_subject == actor.user_id`, sem exceção para
analistas/admins. Predicado no repositório **antes** de COUNT/LIMIT/
OFFSET (postgres `requester_only` + in-memory paridade). O frontend
nunca envia identidade — o backend deriva do principal autenticado.

## 3. Componentes afetados

| Componente | Mudança |
|---|---|
| `domain/product_registration/catalog.py` | `allow_blank`; missing cobre texto em branco; draft-change rejeita branco em obrigatório |
| `service.py` | `get_request_detail(own_scope)`; `reference_data` expõe `allowBlank` |
| `product_registration_routes.py` | `scope` em listagem e detalhe |
| `prc_semantic.py` + `semantic_registry.py` | `scope` em list/detail EVA |
| `PrcRequestForm.tsx` | obrigatório não-vazio (exceto `allowBlank`); edição não zera campo requerido; submit revalida a ficha |
| `prcApi.ts` / `PrcCasePage.tsx` | `scope=mine` na listagem e no detalhe do contexto pessoal |

Cobertura transitiva dos caminhos de escrita: `validate_draft_change`
é usado por PATCH /draft, `update` changes e `save_returned_fields`
(correções) — todos rejeitam descrição em branco pela mesma regra.

## 4. Matriz de autorização

| Ator | `scope=mine` | fila autorizada | detalhe `?scope=mine` alheio |
|---|---|---|---|
| Solicitante A | só casos de A | escopo pessoal vigente | 404 |
| Analista D (também solicitante) | só casos de D | fila global da Engenharia | 404 |
| Solicitante sem permissão | 403 (gate de rota) | 403 | 403/404 |

## 5. Testes

- `tests/test_prc_description_own_scope.py` — **27 testes**: domínio
  (blank/null/whitespace/max_length/customerReference), REST (intake
  422, update changes 422, draft 422 sem mutação), escopo mine
  (analista, solicitante, filtros, detalhe 404/200) e EVA (list
  scope=mine, submit vazio rejeitado).
- `PrcRequestForm.descriptionRequired.test.tsx` — 3 testes: bloqueio
  de Avançar, allowBlank não apontado, edição legítima avança.
- Regressão: **453 passed** PRC/EVA/home/requester (10 skips =
  Postgres sem DSN — adapter postgres exercido pelos mesmos predicados;
  integração real gated por `ENG_PRC_TEST_DSN`); plugin-ui **93/93**
  testes PRC; my-requests suite (2 falhas pré-existentes em
  `process-issue`, fora do escopo).
- Postgres adapter: `requester_only` já existente e coberto pelo mesmo
  contrato de repositório; DSN de teste não provisionado nesta estação
  (`TEST_NOT_RUN` para integração real).

## 6. HML

- SHA implantado: `2362f5866e` (checkout HML fast-forward).
- Digests: engineering-api `1af690082700`, plugin-ui
  `3255deb472ee`, my-requests `ccdb4e4ce444`, engineering
  `45853e077681`.
- Verificação de runtime: `allow_blank` e `own_scope=scope=="mine"`
  presentes no código ativo do container; 0 erros no log pós-start;
  containers healthy.
- Smoke autenticado (formulário/scope com identidades reais):
  `TEST_NOT_RUN` — validação visual pelo PO.

## 7. Rollback

Imagem anterior engineering-api HML: `24c99dc9de32` (fix Home). PRD:
digest vigente registrado no adendo de deploy. Sem migrations, sem
mudança de RBAC/Keycloak, `TOTVS_WRITES=0` — rollback = retag +
`up-*-sequential.sh` do serviço.

## 8. Riscos residuais

- Legado: solicitações históricas com descrição vazia seguem legíveis;
  a regra vale para escritas futuras (sem migração de dados).
- Detalhe por contexto: `?scope=mine` protege a superfície pessoal;
  o endpoint operacional continua permitindo analistas por design.
- Sub-recursos (timeline/anexos/comentários) mantêm a AuthZ vigente;
  a página pessoal só os consulta após o detalhe `scope=mine` passar.

## 9. PRD — evidência de publicação

- SHA: `f7a785ef94` (fast-forward; inclui `6116a5231a` + doc).
- Digests (antes → depois):
  - engineering-api `0386937783af` → `a31ac31e5fd5`
  - plugin-ui `ddbc29b04bfb` → `73ca7ad0e20d`
  - my-requests `9bf854d7e101` → `50c6f4805d9d`
- Rollback: retag dos digests anteriores + `up-prod-sequential.sh`.
- Runtime PRD: `allow_blank` e `own_scope=scope=="mine"` ativos no
  container; engineering-api healthy; 0 erros no log pós-start.
- MCP: 6 tools (`analyze, delete, execute, get_context, knowledge,
  read`), 56 capacidades PRC, `scope` presente em `list`/`detail`.
- engineering MFE não republicado — consome plugin-ui como remote de
  Module Federation (nova validação servida pelo container plugin-ui).
- `PRD_AUTHENTICATED_SMOKE = TEST_NOT_RUN` — validação visual e de
  identidades reais fica com o PO (nenhuma sessão legítima disponível
  ao agente; sem dados artificiais em produção).
- Verificador independente: `INCONCLUSIVE` (rodada 1 — motor 'devin'
  sem login; bloqueio persistente, não contornado).

## 10. FIX-02 — Obrigatoriedade visual nos frontends

Task: `PRC-DESCRIPTION-REQUIRED-FRONTENDS-FIX-02`
Implementação: `815f7a3094`

### Causa-raiz

`SelectField` (path antigo de selects) renderizava ` *` no próprio
label via `classNames.required`. Campos nativos
(`NativeTextField`/`NativeSelectField`/`NativeTextAreaField` via
`createDashboardNativeFormFields`) propagavam `required` apenas ao
controle HTML — `FormFieldShell`/`FieldLabel` não aceitavam a prop e
não renderizavam o marcador. Resultado: **Descrição** (kind=text)
sem ` *` enquanto selects mostravam. A validação de avanço/envio já
bloqueava vazio e o backend já rejeitava (contrato
`requiredCreateIntake=true, allowBlank=false, maxLength=200` intacto)
— o defeito era exclusivamente de indicação visual + `aria-required`.

### Arquivos modificados

- `plugins/plugin-ui/src/components/help/FieldLabel.tsx` —
  prop `required` + marcador compartilhado.
- `plugins/plugin-ui/src/components/forms/FormFieldShell.tsx` —
  prop `required` repassada ao `FieldLabel`.
- `plugins/plugin-ui/src/components/forms/NativeFormFields.tsx` —
  os três campos nativos propagam `required` ao shell e recebem
  `aria-required` (nativo `required` já existia).
- `plugins/plugin-ui/src/components/prc/PrcRequestForm.descriptionRequired.test.tsx` —
  novo teste: `Descrição *` + `required` + `aria-required` em CREATE.

`PrcRequestForm.tsx`, consumers (`PrcRequestPage`, `PrcCreatePage`) e
Engineering API: **inalterados** — `required` já derivava de
`requestType === "create" && spec.requiredCreateIntake`. Sem lógica
duplicada por portal; fonte de verdade permanece no contrato backend.

### Contrato oficial (verificado)

`{"path":"description","kind":"text","requiredCreateIntake":true,"allowBlank":false,"maxLength":200}`

### Testes

- plugin-ui: **315/315 PASS** (59 arquivos), incluindo novo caso e
  regressão `PrcRequestForm.editCase` (UPDATE preservado — indicador
  só em `requestType==="create"`).
- Typecheck do escopo: `tsc-scope-clean` (erros pré-existentes em
  charts/realtime fora do escopo, inalterados).
- Backend: sem alteração — validação de avanço/envio e rejeição de
  vazio já vigentes desde `6116a5231a`.

### HML

- SHA: `815f7a3094` · plugin-ui digest `e8edeba604739`.
- `aria-required` presente no bundle publicado
  (`__federation_expose_Index-*.js`); container healthy.
- `HML_VISUAL_*`/`HML_EMPTY_FIELD_TEST`: `TEST_NOT_RUN` — sem sessão
  autenticada legítima; validação visual pendente do PO.

### PRD

- plugin-ui digest `faa8c9dc46af` → `43952b6a7986`.
- `aria-required` verificado no bundle ativo; nginx servindo
  `remoteEntry.js`; 0 erros no log pós-start.
- my-requests/engineering MFEs não republicados — consomem o remote
  de Module Federation (artefato novo servido automaticamente).
- `PRD_VISUAL_SMOKE`: `TEST_NOT_RUN` — aceite visual pelo PO.

### Rollback

Retag plugin-ui PRD para `faa8c9dc46af` + `up-prod-sequential.sh`.
Sem migrations/RBAC/Keycloak/MCP/TOTVS.

### Limitações residuais

- Screenshots autenticadas pendentes (PO).
- Marcador ` *` agora uniforme em todos os campos nativos required
  (benefício transversal; sem regressão detectada nos 315 testes).
- Verificador independente: `INCONCLUSIVE` (rodada 1 — motor 'devin'
  sem login, mesmo bloqueio persistente já registrado).
