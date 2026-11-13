# PRC-TRACK-IMPLEMENTATION-PACKAGE — Plano integrado de execução governada

> **REGRA FINAL DO PO — ADR-04 (2026-11-13; substitui todas as interpretações anteriores):** a bandeira é única por produto/alvo e propaga-se às revisões enquanto **OPEN**. Se **RESOLVED durante V4**, aparece em **V4 como RESOLVED** (verde), mas **não aparece em V5 em diante**. Se **REMOVED durante V4**, **não aparece nem em V4 nem nas posteriores**. V3 preserva OPEN nos dois cenários. O evento registra `revisionContext=V4`, instante, autor e operação; resolução/remoção não cria versão técnica. A ficha corrente da V4 reflete imediatamente resolução/remoção; versões anteriores preservam seu estado. Histórico de eventos continua auditável, inclusive após desaparecimento da bandeira. **A revisão de resolução é a revisão vigente quando ocorre a ação, e não uma revisão nova.** Se houver reabertura, definir contrato separado, não supor comportamento retroativo. Especificação de persistência/projeção ainda depende de Coordination.

> **AMENDMENT G1/PO — 2026-11-13:** As escolhas documentadas em [Deliberações G1 do PO](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md) prevalecem sobre referências anteriores incompatíveis neste plano: **campos registrados pela Engineering API, não necessariamente snapshot TOTVS completo**; **somente diferenças técnicas reais geram nova Vn**; flags são únicas por produto/alvo e projetadas nas revisões; endpoints de diff no backend; HML API funcional + aceite completo Plugin UI antes do frontend. Fases/AC B1–B3 devem ser reespecificadas após ratificação; **não iniciar implementação com os AC antigos conflitantes**.

> **Data:** 2026-11-13 · **Natureza:** pacote de planejamento para implementação futura; **nenhum código, schema ou deploy autorizado por este documento**.  
> **Status do pacote:** `PLANNED / GATED`. UX das três páginas: `UX_APPROVED`. Contratos de produto acompanhado e flags: `TO_INVENTORY / ARCHITECTURE_DECISION_REQUIRED`. Evidência de execução global: `TEST_NOT_RUN`.  
> **Princípio:** inteligência ampla, autoridade estreita, explícita e governada. Contrato e autorização antes de frontend.  
> **Fontes vinculantes:** [regras de negócio](./PRC-PRODUCT-TRACKING-VERSIONS-TRANSVERSAL-FLAGS-DECISIONS.md), [UX aprovada páginas 1–3](./PRC-PRODUCT-TRACKING-FRONTEND-VISUAL-SPEC.md), [inventário + wireframes](./PRC-TRACKED-PRODUCTS-UI-COMPONENT-INVENTORY-RESPONSIVE-WIREFRAMES.md), [migração Plugin UI](./PRC-PLUGIN-UI-COMPONENT-EXTRACTION-MIGRATION-PLAN.md).

## 0. Resumo executivo e ordem obrigatória

Objetivo: introduzir o contexto **Produtos acompanhados** na ferramenta existente **Controle e Cadastro de Produtos**, ficha técnica por snapshot V1…Vn, flags transversais por produto/alvo e comparação entre quaisquer duas versões — sem substituir Catálogo TOTVS, sem converter drafts em dados oficiais e sem criar componentes visuais exclusivos do MFE.

**Ordem técnica:** (G0) reancorar/inventariar e aceitar migração Plugin UI → (G1) ratificar ownership e contratos → (B1) validar/corrigir materialização de snapshot oficial e versionamento → (B2) flags persistentes transversais e histórico temporal → (B3) queries/paginação/diff read-only → (U1) segmento e lista → (U2) ficha e flags → (U3) versões/comparação → (Q) testes e aceitação no SHA → (D) deployment governado, quando autorizado.

**Proibição:** não desenvolver U1–U3 com mocks tratados como backend pronto. Não fazer migrations antes de inventário de tabelas/grants. Não inferir permissão da UI, de provider scopes ou do JWT isolado.

## 1. Evidência GitHub consultada (default branch em 2026-11-13)

| Item | Fonte de código | Classificação e consequência |
|---|---|---|
| Registro/revisões existentes | `api-delpi/migrations/plugins/engineering/V012__product_registration_core.sql`; `engineering-api/engineering_app/infrastructure/persistence/product_registration/postgres_repository.py` | **PROVEN no código:** records/revisions, `current_revision_number`, transação de conclusão com verification e revision. **Não criar tabelas redundantes.** Runtime/migration aplicada neste ambiente: TO_INVENTORY. |
| Endpoints de registro/revisão | `engineering-api/engineering_app/interface/http/routes/product_registration_routes.py` (`technical-records/{record_id}`, `.../revisions`, `.../revisions/{revision_number}`); service `get_record/list_revisions/get_revision` | **PROVEN no código:** leituras por `recordId` para analistas. Não é prova de listagem paginada de produtos acompanhados, flags temporais ou diff arbitrário. |
| **Gap crítico de snapshot** | `engineering-api/engineering_app/application/use_cases/product_registration/service.py`, `_complete_with_official_verification` chama `_build_snapshot(request, data)`; `_build_snapshot` copia `draft_data` | **PROVEN no código e incompatibilidade com regra TARGET:** `revision_snapshot` é construído do **draft**, apesar da verificação de campos observados no TOTVS. O valor salvo **não pode ser chamado de snapshot oficial completo** sem mudança de contrato, leitura/cobertura e testes. **GATE B1 bloqueante.** |
| Diff vigente | `_revision_changes` em `service.py` usa `changed_paths` do draft e snapshot anterior; CREATE marca campos iniciais | **PROVEN no código:** diff da solicitação, não comparação confiável entre snapshots oficiais arbitrários. Não atribuir mudanças externas ao PRC. |
| Concorrência | `postgres_repository.complete_request` usa lock, `base_revision`, revisões sequenciais e operação transacional | **PROVEN no código:** há CAS/lock; testar conclusão concorrente, primeiro acompanhamento UPDATE e retry idempotente; não assumir cobertura runtime. |
| Flags atuais | service `list_flags`, `list_flags_cross_case`, `create_flag`, `resolve_flag`, `reopen_flag`; rotas D16 | **PROVEN no código:** consulta transversal/cross-case; **não equivale** a identidade de flag por produto, estado em corte histórico ou unicidade por produto/alvo. Inventariar tabelas, permissões e soft-delete. |
| Componentes PRC atuais | `plugins/plugin-ui/src/index.ts` exporta `PrcTechnicalSheetView`; `plugins/engineering/src/ui/engineeringUi.ts` expõe façade do kit; `PrcQueuePage.tsx` usa tabela/cards/kanban | **PROVEN no código:** base de apresentação; `PrcTechnicalSheetView` tem contrato orientado a draft CREATE/UPDATE. Snapshot precisa contrato próprio/mode explícito. |
| Extração de flags PRC-UI-EXTRACT-01 | Relatório do executor (conversa): 4 componentes extraídos, builds/testes reportados, worktree sem commit e visual bloqueado por entitlement | **REPORTED / PENDING_ACCEPTANCE**, não `PASS` confirmado. No `plugins/plugin-ui/src/index.ts` retornado pela consulta GitHub **não aparecem os novos exports**, e a busca por `PrcFlags.tsx` não encontrou arquivo publicado. **Verificar branch/HEAD/worktree e publicar/validar antes do frontend.** |
| Rotas frontend | `plugins/engineering/src/features/product-registration/ProductRegistrationFeature.tsx`, `prcNavigate.ts`; catálogo independente `features/products` | **PROVEN no código:** PRC queue/detalhe/criação; novas subrotas de acompanhados são TARGET, sem alterar `/apps/engineering/products/:code`. |

### 1.1 Drift que deve ser resolvido antes de construir UI

**Não confundir três conceitos:**
1. `technicalDraft` da solicitação = candidato que o PRC tenta confirmar.
2. `observed.product/suppliers` do leitor TOTVS = leitura oficial com cobertura/proveniência.
3. `technical_snapshot` atualmente persistido = cópia de `draft_data` na rotina de conclusão observada.

A regra de negócio aprovada exige **snapshot do estado oficial efetivamente observado após conclusão validada**, não preenchimento por draft. O agente de B1 deve verificar o contrato real da leitura oficial (campos presentes, ausência e fornecedor), projetar normalização com provenance, corrigir materialização se autorizado e tratar registros legados sem reescrever revisões imutáveis. Revisões antigas com evidência insuficiente devem ser rotuladas honestamente (ex.: `legacy_draft_derived`), **não convertidas retroativamente em oficiais por inferência**. Uma revisão V1 não comprova criação nativa no ERP.

## 2. Ownership e fronteiras

| Responsabilidade | Owner |
|---|---|
| Autenticação/SSO | Keycloak |
| App, rotas de plataforma, RBAC/governança | Core |
| Host, contexto e navegação global | Portal |
| Leitura oficial de cadastro e regras técnicas TOTVS | sistemas oficiais/Domain APIs de Engenharia |
| Registro de acompanhamento PRC, versões, flags, auditoria e autorização por objeto | **Engineering API / domínio PRC — owner proposto a ratificar** |
| Páginas, filtros, navegação e adapters de consumo | `plugins/engineering` (Portal Engenharia) |
| Primitivos e componentes visuais reutilizáveis, tokens, acessibilidade | `@delpi/plugin-ui` |
| Geração assistida/análise, se futuramente integrada | EVA (sem source of truth ou publicação automática) |

**ARCHITECTURE_DECISION_REQUIRED — Coordination:** ratificar a evolução das flags hoje centradas na solicitação para identidade por produto/alvo, fonte temporal/histórico, owner e contratos; política de cortes históricos e alvo removido; compatibilidade D16; publicação/recuperação de snapshots oficiais. Sem ratificação, execução limitada a inventário, testes e design de contrato, não writes/schema.

## 3. Matriz de páginas → componentes do Plugin UI → contratos

| UI aprovada | Componentes do kit / façade e provenance | Contrato necessário | Regras/limites |
|---|---|---|---|
| P1: Hero único, seletor `Solicitações | Produtos acompanhados` | `EngineeringPagePath`, `EngineeringPageHero`, `EngineeringSegmentToggle` (factories Plugin UI) | Nenhum novo dado para navegação; URL state | Um top bar do host; Solicitações permanece default |
| P1: fila existente | `EngineeringFiltersRow/Input/Select`, `EngineeringActionButton`, `DataTableSection`, `EngineeringDataCardsGrid`, `EngineeringKanbanBoard`, `EngineeringStateBanner` | PRC fila vigente `GET /requests` | Preservar layouts, filtros, ações e realtime; `DataTableSection` é wrapper do MFE, kit-first; inventariar abstração antes de novo wrapper |
| P1: listagem acompanhados | mesmos filtros/action/table do kit, `EngineeringEmptyState`, `EngineeringLoadingActivityCard` | **TARGET** `GET /technical-records?page&pageSize&search&flags&sort` (nome final a ratificar) | Uma linha por produto; 5 colunas código, descrição, Vn, flags abertas, última evolução; sem catálogo geral |
| P2: hero do detalhe + abas | `EngineeringPageHero`, `EngineeringPagePath`, `EngineeringTabs`, select do kit | `GET /technical-records/{id}` PROVEN + summary/snapshot adequados; `GET .../revisions` PROVEN | Só Ficha técnica e Versões; versão selecionada na ficha e URL |
| P2: cards de ficha e fornecedores | `PrcTechnicalSheetView`, `FieldLabel`, `createDashboardDetailCard`, estilos `delpi-prc` | `GET .../revisions/{n}` PROVEN **com esquema oficial a corrigir/validar** | Read-only, grupos PRC e fornecedores tabela; criar modo snapshot somente após contrato, sem quebrar CREATE/UPDATE |
| P2: flags nos campos e fornecedor | `FlagFieldAction`, `FlagLegend`, `FlagSummaryView`, `FlagEditorDialog` **REPORTED / NOT_PROVEN_ON_DEFAULT_BRANCH** | Flags atuais por produto e flags `asOfRevision`; writes governados por produto/alvo | Não implementar componentes locais; primeiro aceite PRC-UI-EXTRACT-01; adaptação de D16 sem import de API para kit |
| P3: timeline Vn→V1 | `EngineeringTimeline`, `EngineeringDetailCard`, `EngineeringTabs`, `EngineeringActionButton` | Índice revisões PROVEN, mas metadados/cobertura podem requerer DTO | Seções verticais, expansão e navegação para ficha Vn |
| P3: comparação arbitrária Vx × Vy | selects/forms, `EngineeringDetailCard`/`EngineeringDetailFieldGrid`, `EngineeringStateBanner` | **TARGET** query de comparação ou fetch de ambos snapshots + comparador puro governado; decisão contratual | Apenas diferenças comparáveis, fornecedor por vínculo estável; flags em seção separada; sem componente visual local |

**Import rules:** `@delpi/plugin-ui/index` (direto ou façade `engineeringUi.ts`). O MFE pode ter adapters, mapeadores, rotas e containers de página; nunca novo primitivo/card/modal personalizado de uso transversal. Não importar `portal/src/ui-kit` no MFE.

## 4. Contratos da Engineering API — spec-first, não endpoints afirmados

Os paths com `TARGET` são **propostas**, sujeitos a owner, políticas de autorização e compatibilidade; não chamar em frontend antes de ratificação/implementação.

| ID | Operação / path | Estado | Request/response mínimos | AuthZ/erros |
|---|---|---|---|---|
| C00 | `GET /v1/product-registration/requests` | PROVEN code | filtros/queue paginada atual | read por escopo; preservar |
| C01 | `GET /v1/product-registration/technical-records/{recordId}` | PROVEN code | id, fonte/código, revisão atual, verificação | analista; 403/404 |
| C02 | `GET /v1/product-registration/technical-records/{recordId}/revisions` | PROVEN code | items revisionNumber/requestId/approvedAt/changedPaths | analista; 403/404 |
| C03 | `GET /v1/product-registration/technical-records/{recordId}/revisions/{n}` | PROVEN code | technical_snapshot/changes/evidence; **proveniência e cobertura do snapshot não suficientes para UX TARGET sem B1** | analista; 403/404 |
| C04 | `GET /v1/product-registration/technical-records` | TARGET | `page,pageSize,search,flagState,sort` → `items` `{recordId,officialSource,officialCode,description,latestRevisionNumber,openFlagCount,lastEvolutionAt}`, `total`, allowed sort/filter; ordenação determinística | `read` e object-level filter; 400/403/503, páginas estáveis |
| C05 | enriquecimento de `C01/C03` ou DTO de snapshot | TARGET | snapshot versionado, `officialCoverage`/present, suppliers por vínculo, `source/evidence`, `snapshotKind` (confirmed vs legacy), `asOf` | fail-closed; não inventar valor ausente |
| C06 | `GET /technical-records/{recordId}/flags` | TARGET | `mode=current|asOfRevision`, `revisionNumber` validado, lista com id, status, alvo FIELD ou SUPPLIER_LINK, timestamps e eventos/estado histórico | auth por produto e alvo; 403/404; corte temporal estável |
| C07 | `POST/PATCH/actions /technical-records/{recordId}/flags...` | TARGET | `target`, título/descrição, estado, version/expectedVersion, `Idempotency-Key`, actor/audit | permissão live, 403/409/422; unicidade OPEN por produto/alvo |
| C08 | `GET /technical-records/{recordId}/comparisons?from=1&to=5` **ou** comparador puro sobre C03 | TARGET/TO_DECIDE | `from/to`, `fieldChanges`, `supplierLinkChanges`, coverage, `flagEvents` em coleção separada, valores tipados/formatáveis | sem invenção/causalidade; escopo; 403/404/422 |
| C09 | links request↔record/revision, invalidação realtime | TARGET por compatibilidade | `requestId`, `recordId`, `revisionNumber`, `updatedAt` / evento leve | nunca expor snapshot/flags completos via socket |

### 4.1 Regras de contrato transversais

- Definir owner, consumer, esquema versionado, paginação/limites, ordenação determinística, erros com `operation_id`, tracing/correlation, timezone UTC e envelope compatível.
- **Read:** somente produtos/revisões/flags no escopo autorizado; endpoint de listagem não pode revelar existência de produtos negados.
- **Write:** AuthZ live backend, autoria e auditoria, idempotência, transações, CAS/row version e prevenção de duplicata concorrente.
- **Corte de flags:** imutável para versão histórica; alterações atuais não mudam V3 retrospectivamente; distinguir data de publicação da versão e data de eventos. Campos removidos/fornecedores removidos não permitem nova flag no alvo histórico. Reabertura governada.
- **Snapshot:** preservar campos observáveis, fornecedor e provenance, distinguir `present:false`, não copiar draft como verdade oficial; conteúdo ERP diferente de PRC não vira causalidade da PRC.
- **Diff:** comparar snapshots selecionados (V1↔V5 arbitrário), não apenas `changes` da última solicitação; distinguir adicionado/removido/alterado e desconhecido/incomparável. Se servidor faz diff, contrato canônico; se cliente faz diff puro, exigir esquema/coverage completo, mesmo resultado em testes e sem autoridade de verificação no cliente.
- **No-op:** política de produzir ou não revisão quando conclusão não muda dados é `TO_DECIDE`.
- **Flags D16:** inventariar schema e client atuais; sua cross-case listagem não comprova unicidade por produto nem histórico.
- **Rollback/retry:** snapshot oficial indisponível após conclusão não pode ser fabricado; definir transação/pendência recuperável com owner. Não destruir versões já publicadas.

## 5. Fases, dependências, entregáveis e aceite

| Fase | Objetivo | Dependência | Entregável/evidência de saída |
|---|---|---|---|
| G0 — Baseline e kit | Revalidar HEAD/status; inventariar código, schema, SQL grants, docs; fechar PRC-UI-EXTRACT-01 | nenhuma | exports Plugin UI realmente publicados, testes e QA visual ou `TEST_NOT_RUN` assumido; `READY` só com gate aceito |
| G1 — Coordination | Ratificar ownership, flags por produto, histórico, cutoff, no-op, concorrência e snapshot oficial | G0 | ADR/decisões `READY_CONFIRMED` ou `READY_BOUNDED`; bloqueios explícitos |
| B1 — Snapshot confirmado | Modelar cobertura e provenance; corrigir transição `draft_data → observed_official_snapshot`; revisar política legado | G1 | contratos, migration mínima só se necessária, unit/integration, evidência matched/mismatch/unavailable e V1 de UPDATE |
| B2 — Flags produto/alvo | Adaptar persistência D16 e lifecycle; histórico temporal e associação PRC→produto | G1+B1 identidade | AuthZ, transições, unicidade, auditoria, migração/backfill seguro e E2E backend |
| B3 — Read models e comparação | Página/listagem paginada, revisão estruturada, flags as-of, comparação ou specs de comparador | B1+B2 | contracts C04–C09, testes com V1/V5, fornecedores, cobertura, filtro, 403 |
| U1 — Página 1 | Hero único e switch/filtros/lista acompanhados | G0+B3 C04 | UX-01..UX-03 e P1; PRC fila sem regressão |
| U2 — Página 2 | Ficha snapshot Vn, flags atuais/históricas, fornecedores tabela | G0+B1+B2+B3 | UX-04..UX-09 e P2; ações por Backend, teclado/toque |
| U3 — Página 3 | Timeline, links, comparação Vx×Vy, eventos de flags separados | G0+B3 | UX-10..UX-11 e P3; diff tipado, sem falsa atribuição |
| Q — Validação integrada | Contratos/AuthZ, semântica, regressão e QA visual | B1–U3 | matriz de aceite por SHA, evidência desktop/mobile e estados; bugs e residuais |
| D — Deploy controlado | Preparar e executar rollout **somente após autorização** | Q PASS | migração/grants, kit remote, Engineering API, MFE em ordem, rollback/revoke, smoke e audit trail |

**Pacote não deve ser executado como um único grande diff.** Cada fase aprovada deve gerar RQ/AC, diff mínimo, tests no SHA e evidência. Não misturar migração de flags, gravação de snapshot e CSS em um só merge.

## 6. Casos de aceite E2E obrigatórios (traceability)

| AC | Cenário | Evidência requerida |
|---|---|---|
| AC-01 | Fila PRC preservada, contexto default Solicitações, switches com URL/F5/back | visual + contrato |
| AC-02 | Lista contém **somente** records acompanhados, 5 colunas, busca/filtros/paginação; 403 sem vazamento | API+visual, usuário autorizado/negado |
| AC-03 | CREATE concluída verificada gera V1 com código e **snapshot oficial observado**; reenvio idempotente não duplica | integração DB/API + provenance |
| AC-04 | UPDATE concluída sem acompanhamento anterior gera V1; UPDATE seguinte gera V2; divergência não publica | integração DB/API |
| AC-05 | Revisões são imutáveis; duas conclusões concorrentes não perdem dados; no-op conforme política ratificada | testes concorrência |
| AC-06 | Ficha V5 usa 100% do snapshot V5; ao escolher V3 todos campos/fornecedores mudam para V3 sem mistura | testes de componente e browser |
| AC-07 | Campos não observados e revisões legacy não são mostrados como confirmação TOTVS | fixtures de coverage, browser |
| AC-08 | Flag FIELD/SUPPLIER_LINK OPEN atravessa V3→V5 com mesmo id; consulta `asOf V3` não muda com resolução futura | testes domain+API+UI |
| AC-09 | Flag fornecedor ligada a code+store+attribute; exclusão de vínculo preserva histórico sem permitir criar em alvo ausente | testes backend + UI |
| AC-10 | Autorizar criação/resolução/reabertura no produto atual; impedir duplicata OPEN por alvo em corrida; 403/409 previsíveis | integração auth+concurrency |
| AC-11 | Comparar V1×V5 mostra só diferenças entre snapshots; campos desconhecidos incomparáveis; PN/fornecedor adicionado/removido/alterado | diff property tests+visual |
| AC-12 | Eventos de flag apresentados fora do diff oficial; flag não aumenta revisão | API+browser |
| AC-13 | Mobile 320/360/390/430/768, desktop 1024/1280/1440/1920; tema claro/escuro; modal e tabela fornecedor sem overflow | screenshots e teclado/toque |
| AC-14 | Plugin UI remoto exporta todos componentes novos, sem imports de Engineering API; My Requests não regressa | builds MF + consumer tests |
| AC-15 | URLs do Catálogo TOTVS e PRC existente preservadas; login/entitlement não burlado | roteamento e auth negativo |
| AC-16 | Realtime apenas invalidação e refetch autorizado, sem campos privados no payload, sem pisar em modais em edição | WS + AuthZ tests |

Execução: `PASS / FAIL / PENDING / INCONCLUSIVE / TEST_NOT_RUN / STALE_EVIDENCE`; nunca reportar `PASS` de UX apenas com teste de render isolado.

## 7. Matriz de QA visual e dimensional

Fonte de wireframes e valores CSS `PROVEN`: [inventário responsivo](./PRC-TRACKED-PRODUCTS-UI-COMPONENT-INVENTORY-RESPONSIVE-WIREFRAMES.md). Propostas de margens externas `TARGET`: desktop >=1440: 24px; 1024–1439: 20px; tablet 768–1023: 16px; mobile 320–767: 12px. **Paddings internos pertencem ao kit; não fixar arbitrariamente.**

Resoluções para **cada** P1/P2/P3: `1920×1080`, `1440×900`, `1280×800`, `1024×768`, `768×1024`, `430×932`, `390×844`, `360×800`, `320×640`.

Verificar: uma top bar/hero; dimensões/tokens Plugin UI; busca/filters; grid técnico 2 colunas (CSS confirmado) → 1 coluna em 640px; flags hover+focus+touch; modal host-contained; fornecedores com scroll interno; comparação Antes/Depois lado a lado desktop e empilhada mobile; estados de loading/empty/partial/403/409; contraste e dark mode; URL/back/F5; ausência de overflow do documento.

## 8. Operação de entrega, segurança e rollback

- **Pré-diff:** ler authorities, HEAD e `git status`, inventariar equivalentes, validar RQ/AC e local vs branch. Não tocar alterações de terceiros.
- **Backend-first:** migrations pela autoridade de schema existente, grants mínimos, nenhuma consulta ao banco de outro contexto e nenhuma autorização em frontend.
- **Observabilidade:** log de requestId/recordId/revisionNumber, correlationId, resultado de validação e transição de flag; sem tokens, snapshots sensíveis ou payload ERP completo em log.
- **Ordem de liberação:** contratos/schema compatíveis → Plugin UI remoto (exports confirmados) → Engineering API → Engenharia MFE e eventuais consumers; decidir ordem exata com pipeline real; rollout reversível.
- **Rollback:** frontend/kit podem retornar versão anterior; schema deve ser backward compatible; evitar rollback destrutivo de revisões/flags já confirmadas; se houver incompatibilidade, feature flag em camada correta, revogação de rotas e plano de compensação.
- **Ambientes:** testar dados/entitlement no ambiente autorizado; ausência de entitlement é bloqueio de teste, não justificativa para bypass. Produção somente com autorização explícita.
- **Critério final:** registros, revisões, flags e visual passam pela autoridade real e evidências no SHA; `Q PASS` antes do deploy.

## 9. Decisões pendentes, priorizadas (Coordination)

**D01 (bloqueante):** ratificar owner e persistência/compatibilidade de flags transversais por produto/alvo vs D16 por solicitação; unicidade, eventos e vínculo pré-código.  
**D02 (bloqueante):** contrato de snapshot oficial completo/cobertura/proveniência, tratamento do `_build_snapshot` atual e versões legadas, incluindo falha pós-conclusão.  
**D03 (bloqueante):** leitura/AuthZ por produto e semântica da listagem paginada; supplier identity e estados temporais.  
**D04:** política no-op e concorrência de duas PRCs com base revision ausente.  
**D05:** diff servidor vs comparador puro no consumer, sem autoridade/causalidade delegada.  
**D06:** confirmação de commit/export/QA da migração PRC-UI-EXTRACT-01.  
**D07:** política de criação/reabertura de flag em ficha histórica (sugestão: criação só na última, histórico read-only).

### Definition of Ready para iniciar B1/B2/U1–U3

- G0 e G1 concluídos com decisões registradas.
- Contratos API e dados com status `READY_CONFIRMED` ou `READY_BOUNDED`.
- PRC-UI-EXTRACT-01 com SHA publicado e imports MF testados; resultado visual explicitado.
- Fixtures e casos de teste cobrindo produto já existente, primeira V1 via UPDATE, supplier link e flags.
- Escopo/RQ/AC e rollback definidos por fase.

**Este documento entrega planejamento e rastreabilidade, não autoriza implementation prompt, alteração de código ou publicação.**


### Emenda de aceite B2 — FLAG-RESOLVE-REMOVE-REVISION (PO, 2026-11-13)

- **B2-FLAG-01:** aberta em V3, sem evento de encerramento → OPEN nas V3/V4/V5.
- **B2-FLAG-02:** criada V3, **resolvida enquanto V4 vigente** → OPEN em V3, **RESOLVED visível em V4**, **ausente em V5**.
- **B2-FLAG-03:** criada V3, **removida enquanto V4 vigente** → OPEN em V3, **ausente em V4/V5**.
- **B2-FLAG-04:** transição não cria Vn nem modifica snapshot técnico; gravar revisão vigente no evento, com ator/data/CAS.
- **B2-FLAG-05:** uma identidade lógica por produto+alvo, projeção temporal sem clones, histórico disponível com AuthZ.

Prevalece sobre AC textuais antigos que tratem RESOLVED e REMOVED como estados de exibição equivalentes. `ARCHITECTURE_DECISION_REQUIRED` para contrato físico da projeção, sem alterar a intenção do PO.

## Complemento CR-02 — decisão do PO em 13/11/2026

**CR-02 APPROVED BY PO:** opção **A — Ficha consolidada por versão** (sem comentário). Cada Vn representa o estado consolidado dos campos PRC acompanhados pela Engineering API; delta e eventos de solicitação são separados. O backend compara Vx×Vy como estados consolidados, incluindo vínculos por supplierCode+store. UPDATE parcial combina dados confirmados com base válida, preservando cobertura/proveniência e sem inventar desconhecidos. Essa escolha **não ratifica** contratos, AuthZ, migration, source-of-truth adicional, nem autoriza implementação. Remanescentes: definição de valores registrados vs verificados, semântica de null/omissão/remoção, campos parciais, legado e primeira V1 sem baseline. [Decisão registrada](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md) · [Proposta à Coordination](./PRC-TRACK-G1-CONTRACT-RATIFICATION-PROPOSAL.md).

## Complemento CR-03 — exceção inicial à política de no-op (PO, 13/11/2026)

**Decisão aprovada pelo PO:** `CR-03 A — V1 baseline inicial mesmo sem mudança técnica`, sem comentário. **Compatível** com ADR-05 B quando interpretada em duas fases:
- **Sem versão anterior + primeira PRC concluída e matched:** gerar V1 com ficha consolidada CR-02, mesmo sem delta técnico, rotulada `primeiro acompanhamento`.
- **Já existe Vn + PRC matched:** gerar Vn+1 **somente** com diferença técnica real; conclusão sem diferença permanece auditada na versão vigente, sem nova revisão.
- **Não matched / não concluída:** nenhuma revisão.
- **Idempotência/concurrency:** não duplicar V1 ou Vn, exigir locks/CAS/testes e tratamento de vínculo da solicitação que não gerou revisão.

**Emenda aos gates B1/AC:** primeira UPDATE sem diferença gerando V1, segunda conclusão no-op sem incremento, alteração posterior gerando V2, conflito/rollback, snapshot consolidado/provenance, histórico V1 sem afirmar criação TOTVS. Critério anterior que bloqueava V1 por no-op está **superado pela decisão do PO**. [Registro PO](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md) · [Ratificação Coordination](./PRC-TRACK-G1-CONTRACT-RATIFICATION-PROPOSAL.md). `ARCHITECTURE_DECISION_REQUIRED` permanece para contratos/execução.

## Complemento CR-04 — Proveniência de campos acompanhados (PO, 13/11/2026)

**CR-04 APPROVED BY PO:** **A — Preservar valores e identificar sua confirmação**, sem comentário. `PO_APPROVED / COORDINATION_RATIFICATION_PENDING`.

**Atualização do contrato alvo B1:** ficha consolidada CR-02 mantém valores de campos PRC acompanhados e associa metadados de proveniência, cobertura, evidência e status individual (`official_verified`, `inherited_confirmed`, `registered_unverified`, `unknown` — nomes ilustrativos sujeitos a contrato). Valores herdados não são rotulados como novamente confirmados; registrados não verificados não recebem falsa autoridade; ausência não é substituída por suposição. Conclusão continua exigindo gate de verificação `matched` e AuthZ. **CR-03** cria V1 inicial com cobertura real; para V2+ apenas diff técnico em valores/vínculos gera versão. Mudança de metadados de verificação sem alteração técnica não incrementa versão, mas deve ter ledger/auditoria. O backend B3 apresenta proveniência e sinaliza valores incomparáveis. Testar em HML acesso positivo/negativo, UPDATE parcial, V1, no-op, missing/unknown e mismatch.

**Pendente de Coordination:** enums, DTO, regras null/ausência, cobertura, merge, contrato de evidência, versionamento e retrocompatibilidade. Sem autorização de implementação. [Registro PO](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md) · [Proposta Coordination](./PRC-TRACK-G1-CONTRACT-RATIFICATION-PROPOSAL.md).
