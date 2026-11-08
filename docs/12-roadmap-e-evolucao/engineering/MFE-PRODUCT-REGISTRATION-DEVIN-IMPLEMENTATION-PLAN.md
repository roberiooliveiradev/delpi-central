# Portal Engenharia MFE — Plano executável Devin: refatoração completa do Product Registration

> **Status:** `TARGET / IMPLEMENTATION_AUTHORIZED_FOR_DEV / NOT_IMPLEMENTED_BY_THIS_DOCUMENT / PRODUCTION_DEPLOY_SUSPENDED` — 2026-11-07.
>
> **Executor-alvo:** Devin (agente de desenvolvimento). **Owner do produto/MFE:** Portal Engenharia. **Owners preservados:** Core/Keycloak (AuthZ), Engineering API (workflows/persistência), api-delpi (leitura oficial TOTVS), TOTVS (SoT), EVA (ação semântica governada).
>
> **Decisão PO:** a UI local atual é visualmente inadequada, usa HTML básico no PRC e não recebe aceite para deploy. Refatorar toda a experiência com o `@delpi/plugin-ui` real e a façade `plugins/engineering/src/ui/engineeringUi.ts`; **não fazer deploy em produção**. A autorização de deploy discutida anteriormente foi expressamente suspensa pela decisão mais recente do PO.
>
> **Inputs vinculantes:** [Wireframes sete áreas](./MFE-PRODUCT-REGISTRATION-UX-WIREFRAMES.md) · [Matriz componentes/QA](./MFE-PRODUCT-REGISTRATION-COMPONENTS-AND-ACCEPTANCE.md) · [Contrato MVP](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md) · [Decisões PO](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md) · [Integração EVA](./PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md).
>
> **Escopo de entrega:** MFE completo + integração somente com REST existente, testes e screenshots reais DEV/HML. Contratos do backend não devem mudar por conveniência de UI; lacuna real exige registro e owner.

## A. Inventário de implementação verificado no GitHub (base da trilha)

1. `plugins/engineering/src/features/product-registration/ProductRegistrationFeature.tsx`: roteador PRC atual aceita `queue` e `detail`; não há wizard de intake nessa árvore.
2. `pages/PrcQueuePage.tsx`: ~6 KB; lista/filtros nativos, `fetchPrcQueue`, filtros `status,type,search,page,pageSize`, paginação `total` do servidor. Sem uso confirmado de `engineeringUi`.
3. `pages/PrcDetailPage.tsx`: ~17 KB; `fetchPrcRequest`, `fetchPrcTimeline`, `fetchPrcVerifications`, `fetchPrcRevisions`, `prcAction` e `prcUpdateDraft`. Mistura todos os conteúdos em uma página. `allowedActions` governa operações. Respeitar esta semântica.
4. `api/productRegistrationApi.ts`: `BASE=/apps/engineering-api/v1/product-registration`. Exports CONFIRMADOS: `fetchPrcQueue`, `fetchPrcRequest`, `fetchPrcTimeline`, `fetchPrcVerifications`, `fetchPrcRecord`, `fetchPrcRevisions`, `fetchPrcReferenceData`, `prcAction`, `prcUpdateDraft`. **Não possui helper intake no cliente**, mas a Engineering API expõe `POST /v1/product-registration/intake/requests` (`IntakeBody`, idempotency key). Criar SOMENTE helper tipado para esse endpoint existente, através de `postJson`/httpClient oficial (verificar suporte a cabeçalhos idempotency e acrescentar na camada correta se exigido).
5. `engineering-api/engineering_app/interface/http/routes/product_registration_routes.py`: `IntakeBody` confirmado com `source,externalRequestId,externalItemId,requestType,productType,schemaVersion,requestedData,officialProductCode,baseRevision,changes`; mutações têm `expectedVersion`, motivos e checks de estado. **Não inventar field names, route, schema ou novos endpoints.**
6. `engineeringUi.ts`: façade real sobre `@delpi/plugin-ui/index`; `EngineeringPagePath`, `EngineeringPageHero`, `EngineeringSectionCard`, `EngineeringDetailCard`, `EngineeringDetailFieldGrid`, `EngineeringStatusBadge`, `EngineeringActionButton`, `EngineeringStateBanner`, `EngineeringEmptyState`, `EngineeringLoadingActivityCard`, `EngineeringFiltersRow`, `EngineeringFilterInput`, `EngineeringFilterSelect`, `EngineeringFieldLabel`, `EngineeringTimeline`, `EngineeringMetricStrip`, `EngineeringKpiCard`, `EngineeringMultiSelectField`, `EngineeringDateField`, demais exports conforme matriz. Verificar as **props reais** antes de usar.
7. `features/lmps/components/DataTableSection.tsx`: componente existente (não importá-lo do plugin-ui inexistente) com props reais `title,columns,rows,rowKey,loading,refreshing,emptyMessage,serverPagination,hideSearch,onRowClick,fillHeight,toolbarActions,...`. Use `serverPagination={page,pageSize,total,onPageChange}` e `hideSearch` quando barra externa já existir, evitando dupla busca/filtro client-side.
8. `features/products/pages/ProductsListPage.tsx` e `ProductDetailPage.tsx`: referência real de layout, cards, hero, tabs baseadas em URL, tabela e estados. Reutilizar padrões sem copiar lógica de produto oficial.
9. `features/product-registration/productRegistration.test.ts`: cobertura atual focada em rota e cliente. Expandir testes de componentes/jornada e a11y.
10. Capturas DEV fornecidas pelo PO: home nova mostra PRC; fila com colunas coladas e UUID bruto; detalhe com conteúdo estreito e alto, sem organização. Estas são as baseline screenshots, não QA aprovado.

**Fase obrigatória de verificação:** localizar internamente no repo os exports disponíveis para Tabs, Dialog/Modal, Form, Textarea, Checkbox, Radio, Stepper, Combobox/Lookup, Tooltip, Toast, Skeleton; registrar import e props realmente existentes. Caso algum não exista, compor **somente estrutura/semântica mínima local** com components oficiais, sem nova biblioteca/kit e sem criar nome de export fictício. Escolher tokens responsivos do kit em vez de breakpoints novos arbitrários.

## B. Deliverable structure e limites de arquivos

```text
plugins/engineering/src/features/product-registration/
  ProductRegistrationFeature.tsx    # resolver queue, create/target, detail; back-forward/F5
  prcNavigate.ts                    # preservar owner da navegação
  api/productRegistrationApi.ts     # tipos + helper intake sobre REST existente
  components/                      # novos componentes de apresentação PRC APENAS
    PrcPageHeader.tsx              # opcional se composição de PageHero repetida
    PrcStatusBadge.tsx             # composição do EngineeringStatusBadge, estado real
    PrcRequestTable.tsx            # DataTableSection + colunas + responsivo
    PrcRequestFilters.tsx          # filtros oficiais com estado/URL
    PrcWorkflowProgress.tsx        # estados DOMÍNIO, incluindo exceções
    PrcActionBar.tsx               # allowedActions + prioridade + confirmação
    PrcTechnicalFields.tsx         # cards em grupos semânticos
    PrcSuppliersSection.tsx        # vínculos code/store, PN opcional
    PrcFieldDiff.tsx               # leitura de field_results do backend
    PrcTimelineSection.tsx         # EngineeringTimeline
    PrcRevisionsSection.tsx        # tabela/read-only snapshot
    PrcErrorState.tsx              # OPCIONAL só se wrappers insuficientes
  pages/
    PrcQueuePage.tsx               # 01 fila
    PrcCreatePage.tsx              # 02 wizard CREATE/UPDATE (nova view se rota adequada)
    PrcDetailPage.tsx              # 03 shell do detalhe e abas
  ... test files colocados segundo padrão existente
```

A lista é um **mapa de responsabilidades sugerido**, não obrigação de criar 10 abstrações. Aplicar *Abstraction Gate*: componentes pequenos apenas se reutilizados ou com responsabilidade/owner claros. Se composição simples na page bastar, reduzir arquivos. **Não** introduzir módulo de aplicação ou contexto de dados paralelo. Não tocar `features/products`, `VAL-01`, `DAVI` ou outros arquivos sem motivo técnico comprovado.

## C. Design-to-component contract — sem interpretação livre

| UI target | Primeira escolha OBRIGATÓRIA | Complemento / limite |
|---|---|---|
| Breadcrumb | `EngineeringPagePath` | seguir API de `products` |
| Header título, subtítulo, ação | `EngineeringPageHero` + `EngineeringActionButton` | variant/density herdada; sem header artesanal |
| Cards de informação | `EngineeringDetailCard` / `EngineeringSectionCard` | separação por assunto |
| Campos leitura | `EngineeringDetailFieldGrid` | datas/unidades formatadas, sem JSON cru |
| Status | `EngineeringStatusBadge` | `submitted,in_progress,needs_information,under_review,completed,rejected` em pt-BR |
| Tabela fila e revisões | `DataTableSection` existente + `DataTableColumn` | rows acessíveis + serverPagination; mobile adaptado |
| Filtros | `EngineeringFiltersRow`, `EngineeringFilterInput`, `EngineeringFilterSelect` | busca API real, debounce/submit consciente |
| Indicadores | `EngineeringMetricStrip`, `EngineeringKpiCard` | **somente** se totais por status confiáveis existirem; senão OMITIR KPI |
| Mensagens de erro | `EngineeringStateBanner` | distinguir 401/403/404/409/422/5xx e sem conexão |
| Loading | `EngineeringLoadingActivityCard` | não usar spinner deslocado em página vazia |
| Zero resultados | `EngineeringEmptyState` | filtro vazio ≠ dataset vazio |
| Timeline | `EngineeringTimeline` | mapear eventos para props oficiais; sem inventar autor |
| Form label | `EngineeringFieldLabel` | controle associado `htmlFor`/id |
| Campos avançados | `EngineeringMultiSelectField`, `EngineeringDateField` se contrato exigir | não usar apenas para ornamentação |
| Tabs | plugin-ui se export real; senão padrão acessível `products` | aria/tablist, URL, back/forward, `?tab=` |
| Confirmação | plugin-ui dialog se export real; senão padrão oficial do host | confirmar rejeição/conclusão conforme risco |
| Wizard | component kit existente; senão composição local acessível | 3 etapas; sem nova dependência |
| Inputs, select, textarea, checkbox | imports CONFIRMADOS no kit a inventariar no UX0 | proibido CSS de botão/campo paralelo ao DS |
| Avatar/nome | `EngineeringInitialsAvatar` quando identidade de exibição autorizada | `assignedTo` pode ser subject UUID: exibir `Responsável não identificado` se sem display, não `Não atribuído` quando existe subject |
| Tooltips/ajuda | kit oficial após confirmação | textos técnicos curtos, sem exposição de campos internos |

**Não criar** `<EngineeringModal>` ou outros imports fictícios. Não usar `@delpi/plugin-ui` direto se façade já possui equivalente. CSS permitido só grid, placement, responsividade e composição específica; não sobrescrever `.delpi-ui-*` globalmente, não hardcode tema.

## D. Sequência bloqueante e AC por incremento

### MFE-PRC-UX0 — Baseline, Props Map e contratos (não adiar)

**Mudanças:** inspecionar `AGENTS.md`, políticas repo, HEAD/status, screenshots; mapear `plugin-ui` e sua origem real; registrar exports/props para components listados; mapear `productRegistrationApi.ts`, REST `IntakeBody`, `PrcRequestDetail` e requisitos dos campos. Comparar `products` e `lmps`. Definir RQ-UX01..RQ-UX07 e AC abaixo. Escolher padrão routing para create e tabs. Identificar schemas para supplier/changedPaths, labels de statuses/actions e tratamento de erros.

**Saída:** tabela real `componente -> import -> props -> consumidor` e lacunas do kit. Não inventar contract a partir deste plano. Evidência commit/SHA. **Gate:** UX0 não pode ser PASS sem inspeção real do `plugin-ui`.

### MFE-PRC-UX1 — Central de solicitações (RQ-UX01)

**Wireframe:** seção 2 do documento de UX.

**Arquivos:** `PrcQueuePage.tsx`, `PrcRequestTable`/Filters se necessários, `prcNavigate.ts`, testes.

**Tela:** breadcrumbs, hero, CTA nova solicitação, filtros reais, tabela com colunas: número curto, tipo, solicitante, origem/código se houver, abertura, status, responsável, ação. Mostrar `assignedTo` como display *somente quando houver fonte de display autorizada*; caso exista subject sem display, rótulo honesto `Responsável não identificado`, nunca inventar nome nem mostrar GUID bruto. Distinção de sem-atriuição `Não atribuído`. Mostrar código oficial ausente como `Aguardando cadastro`.

**Server paging:** usar `DataTableSection` com `serverPagination`; a busca de filtro externa controla `fetchPrcQueue`, evitar filtro client-side duplicado. Preservar estado URL (se aprovar padrão existente); controle de concorrência de responses. Sem KPI falso. Card mobile de solicitações; nenhuma coluna sobreposta.

**AC:** filtro/limpar/retry/paginar/navegar e F5 funcionam; estado vazio/error/403; desktop/tablet/mobile screenshot; tabela visualmente alinhada; não há UUIDs brutos; toda origem de dado ancorada.

### MFE-PRC-UX2 — Detalhe, abas e workflow (RQ-UX03)

**Arquivos:** `PrcDetailPage.tsx`, composições status/workflow/actions, testes.

**Tela:** header com número curto, tipo, status, solicitante, responsável, código TOTVS, action primária; cards `Identificação` + `Próximas ações`; andamento com `submitted -> in_progress -> under_review -> completed` como caminho principal, mas `needs_information`/rejected não forçados em progress linear; tabs `Visão geral | Ficha técnica | Verificação TOTVS | Histórico | Revisões`. Aba pode ser `?tab=` respeitando navegação existente. Não renderizar seções monolíticas.

**Authority:** apenas `allowedActions` e estado do servidor determinam ações; nenhuma suposição por superadmin; `expectedVersion` atualizado. Guardar `reason` por comando quando requerido. Conclusão não otimista. 409 com reload/reconciliação.

**AC:** actions disponíveis por estado correto, back/forward/foco, telas e tabs por teclado, erro 403/404/409, sem quebra deep link, status e version retratados corretamente.

### MFE-PRC-UX3 — Intake CREATE/UPDATE + ficha técnica (RQ-UX02 + RQ-UX04)

**Arquivos:** `PrcCreatePage.tsx` (se houver escolha de rota), `ProductRegistrationFeature.tsx`, API helper intake, editor técnico e fornecedores, testes.

**Fluxo de 3 etapas:** (1) Identificação e escolha criação/alteração; (2) ficha técnica e fornecedor; (3) resumo, validação e envio. O `IntakeBody` do backend é a autoridade de payload, não o wireframe. Para criação, `requestedData`; alteração usa `officialProductCode`, `baseRevision` e `changes` conforme contrato. Não forjar `requesterSubject`. `source` deve vir de valor canônico permitido pelo backend, não string improvisada. Se faltar contrato de lookup oficial, aceitar código digitado com validação via BFF existente, sem simular autocomplete.

**Campos:** agrupar identificação, classificação, estoque/contabilidade, fornecedores. Ler `reference-data` para required/allowed; enumValues, maxLength e `supplierKeys`. PN vazio/null/omitido normalizado conforme contrato PO e backend; `catalogNumber` diferente. Validation client ajuda, mas backend decide. Fornecedor por `(supplierCode,store)`; chave ambígua/dado oficial ausente bloqueia no backend, UI apresenta resultado.

**Editor detalhado:** modo visualização vs modo edição. `prcUpdateDraft` PATCH com `expectedVersion`, `changes[{path,proposedValue,reason}]` e alterações seletivas (sem full replacement). `under_review` não editável salvo `allowedActions`. Para UPDATE, selecionar path explicitamente, inclusive alteração para `""`, sem truthiness. Não perder mudança em navegação/aba. Preview de before/after se contrato existir.

**AC:** formulário real com create+update; validações visíveis; envio idempotente (quando supported) com duplicate-safe; erro preserva valores; conclusão do wizard cria caso real via REST, navega ao detalhe; editar salva apenas selected paths; 409 e reason; testes PN vazio/preenchido.

### MFE-PRC-UX4 — Verificação, timeline e revisões (RQ-UX05 + RQ-UX06 + RQ-UX07)

**Arquivos:** `PrcFieldDiff`, `PrcTimelineSection`, `PrcRevisionsSection`, `PrcDetailPage`, testes.

**Verificação:** mostrar `officialCode`, `verificationSummary`, `PrcVerification.field_results` do backend, com expected/observed/status por path quando payload suportar. Nunca inventar comparação frontend nem apresentar matched antes de backend. Mismatch, unverifiable, 403 upstream, timeout e faltas claramente bloqueiam. Botão `Verificar e concluir` só com `allowedActions`, confirmação explícita e status de mutação; explicar que reconsulta fonte oficial e publica revision se match.

**Histórico:** `EngineeringTimeline` com eventos `PrcTimelineEvent`: sequence, actor, data, reason, metadata; timeline ordenada pelo ledger e paginada se contrato exigir, sem inferir campo inexistente.

**Revisões:** `PrcRevision` lista número, timestamp, autor, read-only technical_snapshot, changes; `fetchPrcRevisions` só quando `completedRecordId` existe (ou conforme actual API). Comparação entre versões somente se snapshots permitirem no client. `Acompanhamento` = apresentação simplificada na aba Visão geral, não novo RBAC nem endpoint.

**AC:** positivo, negativo, unverifiable, API offline, revisão imutável, timeline completa, ID por caso; não usar contagem global de DB como prova local; screenshots das abas em diferentes estados.

### MFE-PRC-UX5 — Qualidade total / regressão / aceite PO (RQ-UX07 QA)

**Testes no SHA final:**
- TypeScript typecheck, build Vite, Vitest inteiro do MFE; preservar PRODUCTS/LMPs/NC/home.
- Testes de fila: filtro, server pagination, 401/403/404/5xx, loading/empty, resposta obsoleta, label ID e responsável.
- Intake create/update: reference-data, error fields, submit idempotente/erro, auth, navegação.
- Detalhe: tabs URL, keyboard, allowedActions, state/reason, CAS 409, draft PATCH, PN.
- Verificação: match/mismatch/unverifiable, falha API, confirmação, revision read-only.
- Timeline/revisions e mobile/tab state.
- Browser real DEV/HML com usuário autorizado, screenshots nos breakpoints OFICIAIS; teclado, foco, contraste/tema, labels, aria-live, zero overflow/collision.
- Smoke REST com Engineering API e PostgreSQL/TOTVS em ambiente autorizado; não refazer fixtures que geram dados produtivos.
- Auditoria visual comparando wireframes e Home/Produtos do Portal, com screenshots antes/depois; review PO.

**Sem browser disponível:** `TEST_NOT_RUN`, `VISUAL_ACCEPTANCE_PENDING` e reprodução do roteiro. Não alegar PASS de screenshots por inspeção de build. Todos os comandos de teste devem ser descobertos no `package.json`; não inventar scripts.

## E. Regras transversais não negociáveis

1. Design system primeiro: `@delpi/plugin-ui` via `engineeringUi.ts`; sem CSS paralelo/global, sem layouts puramente HTML quando equivalente oficial disponível. Evitar 15 novas abstrações sem consumer.
2. Backend unchanged: mesmos contratos REST e use cases, `engineering.access` para CRUD operacional, `engineering.manager` administrativo, `allowedActions` autoritativo.
3. Totvs: `Portal/EVA -> Engineering API -> api-delpi -> TOTVS`; sem ERP write. `B1_CONTA` e SA5/PN oficial. Part Number opcional vazio mas **nunca wildcard**; ausente no payload oficial = `unverifiable`.
4. Auditoria e concorrência: expectedVersion, CAS, idempotência e justificativa preservados. MFE não decide sucesso de verificação/publicação.
5. Estado DEV/HML não equivale PROD. `PRODUCTION_DEPLOY_SUSPENDED` até aceite visual PO e gates funcionais/operacionais.
6. Dados exibidos: não expor GUID de usuário como nome; não inventar KPI ou nomes/roles. `Não atribuído` só se `assignedTo` ausente, `Responsável não identificado` se subject existe sem nome; buscar display via API autorizada apenas se já houver contrato.
7. Responsividade e acessibilidade: testar views desktop/tablet/mobile e teclado. No desktop ocupar largura útil, sem vazios enormes; não esmagar tabela no mobile.
8. Sem alteração em bounded contexts alheios; se algum backend contract realmente insuficiente, documentar `ARCHITECTURE_DECISION_REQUIRED` com owner/consumers e seguir nas áreas independentes. Não criar endpoints fictícios para concluir UX.
9. Multiagente: HEAD/status antes de mudar; diffs mínimos; não perder FOREIGN_DIFF; testar no SHA; residual search; commits idempotentes segundo `AGENTS.md`.
10. Sem deploy de produção, alteração de Core/Keycloak, migrations ou TOTVS nesta tarefa.

## F. Critério de entrega: matriz de aceite por área

| RQ | Entrega | Critérios mínimos |
|---|---|---|
| RQ-UX01 | Fila | PageHero + DataTableSection + filters + status + paginação real + empty/erro + sem UUID |
| RQ-UX02 | Intake | wizard create/update + fonte/auth correta + validação + envio real + navigate |
| RQ-UX03 | Detalhe | cards, progress, actions from allowedActions, tabs URL, CAS |
| RQ-UX04 | Ficha | leitura/edição, grupos, suppliers PN opcional, PATCH seletivo + motivo |
| RQ-UX05 | Verificação | diff oficial, matched/mismatch/unverifiable, confirmação e read-back |
| RQ-UX06 | Histórico | timeline, revisions read-only, compare quando contratos permitirem |
| RQ-UX07 | Qualidade | responsive, a11y, kit-first, testes e screenshot visual PO |

**Não marcar UX completo se RQ-UX02 (intake) não tiver sido construído ou se screenshot/QA/browser não existir.**

## G. Formato de entregas Devin

Cada incremento deve ter `BASE_SHA,FINAL_SHA,FILES_CHANGED,COMPONENTS_REUSED,COMPONENTS_MISSING,CONTRACTS_VERIFIED,TYPECHECK,BUILD,TESTS,VISUAL_SCREENSHOTS,ACCEPTANCE_STATUS,REGRESSIONS,FOREIGN_DIFF_PRESERVED,BLOCKERS,NEXT_STEP`.

Relatório final obrigatório:
```text
TASK_ID: ENG-PRC-MFE-FULL-REDESIGN
BASE_SHA:
FINAL_SHA:
BRANCH:
FOREIGN_DIFF_PRESERVED:
DESIGN_SYSTEM_EXPORTS_VERIFIED:
COMPONENT_PROPS_VERIFIED:
UX0_COMPONENT_INVENTORY:
UX1_QUEUE:
UX2_DETAIL:
UX3_INTAKE_AND_DRAFT:
UX4_VERIFICATION_HISTORY_REVISIONS:
UX5_VISUAL_QA:
ROUTES_AND_DEEP_LINKS:
CREATE_FORM_REAL_SUBMISSION:
UPDATE_FORM_REAL_SUBMISSION:
SERVER_PAGINATION:
AUTHZ_ALLOWED_ACTIONS:
CAS_AND_IDEMPOTENCY:
PART_NUMBER_OPTIONAL:
B1_CONTA_DISPLAY:
TESTS_RUN_ON_SHA:
TYPECHECK:
BUILD:
VITEST:
BROWSER_DESKTOP:
BROWSER_TABLET:
BROWSER_MOBILE:
A11Y_KEYBOARD:
SCREENSHOTS:
BFF_ONLY_VALIDATION:
COMMITS:
PUSH_STATUS:
DEPLOY_STATUS:
VISUAL_PO_ACCEPTANCE:
HML_FUNCTIONAL_ACCEPTANCE:
PRODUCTION_DEPLOY:
RESIDUALS:
EXECUTION_DRIFT:
NEXT_SAFE_INCREMENT:
```

**Final target:** `UI_CODE_COMPLETE` só após todas RQ funcionais, `VISUAL_QA_PASS` só com screenshots de browser real, `PO_VISUAL_ACCEPTANCE` só após aceite explícito do PO. `PRODUCTION_DEPLOY_SUSPENDED` permanece.


## Refinamentos posteriores ao redesign — decisões PO 2026-11-07

O redesign foi implementado e já recebeu primeiras capturas em localhost; **ainda não houve aceite visual final nem autorização de produção**. As novas decisões e ajustes aprovados serão acumulados em [MFE-PRODUCT-REGISTRATION-POST-REDESIGN-REFINEMENT-PLAN.md](./MFE-PRODUCT-REGISTRATION-POST-REDESIGN-REFINEMENT-PLAN.md). Primeiro item: **PRC-REF-001 — em solicitações UPDATE, o usuário não informa revisão-base; Engineering API resolve a revisão técnica atual de forma governada, preservando CAS, concorrência e auditoria**. O plano original UX0–UX5 fica como histórico de execução; este refinamento tem precedência para UX de alteração. Implementação pendente. Não fazer deploy produtivo.
