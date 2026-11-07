# MFE Controle e Cadastro de Produtos — matriz plugin-ui, contratos UI e aceite visual

> **Estado:** `TARGET / COMPONENT_INVENTORY_PARTIAL / VISUAL_QA_NOT_RUN` · **Fonte:** inspeção GitHub de `plugins/engineering/src/ui/engineeringUi.ts`, `features/product-registration/pages/PrcQueuePage.tsx`, `PrcDetailPage.tsx`, `ProductRegistrationFeature.tsx` e referência `features/products/pages/ProductsListPage.tsx` + capturas DEV apresentadas pelo PO em 2026-11-07.
>
> **Wireframes de sete áreas:** [MFE-PRODUCT-REGISTRATION-UX-WIREFRAMES.md](./MFE-PRODUCT-REGISTRATION-UX-WIREFRAMES.md).
>
> **Gate:** `PRODUCTION_DEPLOY_SUSPENDED` até redesign implementado e validação visual. Documento **não** é evidência de implementação.

## 1. Fonte canônica dos componentes

Façade MFE: `plugins/engineering/src/ui/engineeringUi.ts` (importa `@delpi/plugin-ui/index`; prefixo visual `engineering`); conferir export/props diretamente em HEAD antes de implementar.

| Recurso UX | Nome confirmado na façade | Origem / observação | Situação |
|---|---|---|---|
| Breadcrumb/back | `EngineeringPagePath` | factory `createDashboardPagePath` do kit | PROVEN_EXPORT |
| Hero/título/subtítulo | `EngineeringPageHero` | `createDashboardPageHero`, density compact wrapper | PROVEN_EXPORT |
| Cards de seção | `EngineeringSectionCard` | `createDashboardSectionCard` | PROVEN_EXPORT |
| Cards de detalhe | `EngineeringDetailCard` | `createDashboardDetailCard` | PROVEN_EXPORT |
| Campos leitura | `EngineeringDetailFieldGrid` | `createDashboardDetailFieldGrid` | PROVEN_EXPORT |
| Badge de estado | `EngineeringStatusBadge` | `createDashboardStatusBadge` | PROVEN_EXPORT |
| Ação padronizada | `EngineeringActionButton` | alias `ActionButton` do plugin-ui | PROVEN_EXPORT |
| Banner de feedback/erro | `EngineeringStateBanner` | `createDashboardStateBanner` | PROVEN_EXPORT |
| Empty | `EngineeringEmptyState` | `createDashboardEmptyState` | PROVEN_EXPORT |
| Carregamento | `EngineeringLoadingActivityCard` | `createDashboardLoadingActivityCard` | PROVEN_EXPORT |
| Filtros em linha | `EngineeringFiltersRow` | façade filters kit | PROVEN_EXPORT |
| Campo de busca | `EngineeringFilterInput` | façade filters kit | PROVEN_EXPORT |
| Select filtrável | `EngineeringFilterSelect` | façade filters kit | PROVEN_EXPORT |
| Rótulo de formulário | `EngineeringFieldLabel` | alias `FieldLabel` do plugin-ui | PROVEN_EXPORT |
| Multi-select | `EngineeringMultiSelectField` | `createDashboardMultiSelectField` | PROVEN_EXPORT |
| Datas | `EngineeringDateField` | `createDashboardDateField` | PROVEN_EXPORT |
| Indicadores (com dados oficiais) | `EngineeringMetricStrip`, `EngineeringKpiCard` | factories correspondentes | PROVEN_EXPORT |
| Timeline de eventos | `EngineeringTimeline` | `createTimeline` do kit | PROVEN_EXPORT |
| Avatar iniciais | `EngineeringInitialsAvatar` | factory kit; usar só display autorizado | PROVEN_EXPORT |
| Tabela | `DataTableSection` | componente já usado em `products`, `features/lmps/components/DataTableSection`; classes `ENGINEERING_DATA_TABLE_*` na façade | PROVEN_REFERENCE |
| Tabs acessíveis | **A inventariar** | usar padrão já implantado em `products` (`?tab=`) se consistente com kit | TO_INVENTORY |
| Modal/confirmação | **A inventariar** | não inventar `EngineeringModal` ou export inexistente | TO_INVENTORY |
| Wizard/stepper | **A inventariar** | possivelmente composição simples local de componentes reais | TO_INVENTORY |
| Form / textarea / radio / checkbox | **A inventariar** | procurar no kit e outros MFEs; não assumir imports | TO_INVENTORY |
| Toast, drawer, skeleton, tooltips | **A inventariar** | preferir kit ou padrão oficial, evitar nova dependência | TO_INVENTORY |
| Lookup produto/fornecedor | **A inventariar** | não criar consulta TOTVS direta pelo MFE; API Engenharia BFF apenas | TO_INVENTORY |

`PROVEN_EXPORT` quer dizer **export de componente verificado em fonte**, não que a tela PRC o utilize ou que props/tema tenham sido testados. Verificar compatibilidade de props, theme e render antes do diff.

## 2. Matriz página → componente → contrato

| Área de experiência | Composição obrigatória/primeira escolha | Fonte de dados/ação | Regras / lacunas |
|---|---|---|---|
| 01 Fila | `PagePath`, `PageHero`, `ActionButton`, `FiltersRow`, `FilterInput`, `FilterSelect`, `DataTableSection`, `StatusBadge`, `EmptyState`, `StateBanner`, `LoadingActivityCard` | `fetchPrcQueue` | Busca/filters/page/total somente do contrato; KPI condicional; responsável sem GUID bruto |
| 02 Nova solicitação | `PagePath`, `PageHero`, `SectionCard`, `FieldLabel`, `ActionButton`, `StateBanner` | intake REST existente, identity do auth context | wizard/stepper e inputs a inventariar; página `TARGET`, sem rota nova automática |
| 03 Detalhe / resumo | `PagePath`, `PageHero`, `StatusBadge`, `DetailCard`, `DetailFieldGrid`, `ActionButton`, `StateBanner` | `fetchPrcRequest` / `allowedActions` | tab/stepper a inventariar; fluxo e estados válidos não vêm do MFE |
| 04 Ficha técnica | `DetailCard`, `DetailFieldGrid`, `SectionCard`, `FieldLabel`, `ActionButton`, `DataTableSection` | draft/detail, `prcUpdateDraft` | CAS, motivo, PATCH seletivo, PN opcional, 409 |
| 05 Verificação TOTVS | `SectionCard`, `DataTableSection`, `StatusBadge`, `StateBanner`, `ActionButton` | `prcAction` verify-and-complete, verifications | não calcular match; confirmação terminal, fonte/provenance, unavailable |
| 06 Histórico / revisões | `EngineeringTimeline`, `DetailCard`, `DataTableSection`, `StatusBadge`, `EmptyState` | `fetchPrcTimeline`, `fetchPrcRevisions`, `fetchPrcVerifications` | snapshots immutable, comparação entre versões apenas se dados permitirem |
| 07 Acompanhamento | `DetailCard`, `StatusBadge`, `DetailFieldGrid`, `Timeline`, `ActionButton` | mesma API/rota detalhe | modo de apresentação simples; não criar segundo RBAC nem owner |

**Regra de implementação:** preferir façade `engineeringUi.ts` sobre import direto do `@delpi/plugin-ui` em páginas PRC quando já houver equivalente. Se faltar um componente, documentar `NEEDS_COMPONENT`, consumer e owner; seguir Abstraction Gate. CSS novo apenas composição/layout local, sem cor/tipografia globais ou estilos de botão/tabela paralelos.

## 3. Comportamento por estado

| Situação | Apresentação desejada | Controle de negócio |
|---|---|---|
| Loading inicial | `EngineeringLoadingActivityCard` ou skeleton oficial | requests abortáveis, evitar stale response |
| Lista vazia | `EngineeringEmptyState` com contexto e ação apenas se disponível | diferencia zero global e zero por filtros |
| Erro de rede / 5xx | `EngineeringStateBanner` e retry | não reexecutar writes automaticamente |
| 401 / sessão | mensagem coerente com host SSO | sem exposição de dados |
| 403 | sem acesso, retorno à home | Core/Engineering API decide |
| 404 | solicitação inexistente | não exibir conteúdo residual |
| 409 (CAS) | banner conflito e recarregar/conciliar | não sobrescrever |
| 422 / validação | erro junto aos campos e resumo | backend autoritativo |
| Mutação pendente | loading/disabled, prevenir duplo clique | idempotência, expectedVersion |
| Sucesso | feedback e read-back do caso atualizado | nenhuma conclusão otimista |
| TOTVS mismatch | tabela com diferenças por path, status negativo | bloqueia publicar |
| TOTVS unverifiable / 403 / timeout | alerta explícito e bloqueio | não confundir ausente e vazio |
| Publicação concluída | badge + snapshot / revisão de leitura | imutabilidade |
| Part Number vazio na SA5 | `Não informado no TOTVS`/valor vazio fiel | pode corresponder se expected também vazio |
| Assignee não conhecido | `Não atribuído`/display resolvido | nunca UUID bruto exposto como nome |

## 4. Matriz de telas de QA visual (evidência exigida)

| View | Desktop >=1200 | Tablet 768–1199 | Mobile <=767 | Teclado/a11y | Smoke integrado |
|---|---|---|---|---|---|
| 01 Fila | PENDING | PENDING | PENDING | PENDING | PENDING |
| 02 Intake (target) | PENDING | PENDING | PENDING | PENDING | PENDING |
| 03 Detalhe | PENDING | PENDING | PENDING | PENDING | PENDING |
| 04 Ficha técnica | PENDING | PENDING | PENDING | PENDING | PENDING |
| 05 Verificação | PENDING | PENDING | PENDING | PENDING | PENDING |
| 06 Histórico/revisões | PENDING | PENDING | PENDING | PENDING | PENDING |
| 07 Acompanhamento | PENDING | PENDING | PENDING | PENDING | PENDING |

Faixas acima são alvo indicativo, não substituem breakpoints/token do kit. Cada evidência precisa conter versão/commit do bundle, ambiente DEV/HML, screenshot real, teste, responsável e issue residual. Para views condicionalmente inacessíveis, usar estado real de solicitação seed autorizada, não manipular DOM ou falsificar `allowedActions`.

### Checklist de aceitação

- [ ] Fila usa tabela/alinhamento/colunas/paginação padronizados; filtros funcionais; sem UUID bruto.
- [ ] Nova solicitação CREATE/UPDATE existe em UI se autorizada pelo endpoint atual e foi demonstrada com usuário real.
- [ ] Detalhe usa largura útil; informação segmentada; ações e status coerentes com backend; sem rolagem monolítica.
- [ ] Ficha agrupada; edição seletiva com motivo, CAS e estados não-editáveis.
- [ ] Fornecedores com código, loja, nome, PN opcional, catálogo; tratamento de duplicatas/ambiguidade.
- [ ] Verificação mostra expected/observed/resultado por campo, sem declarar sucesso antes de read-back.
- [ ] Revisões imutáveis e timeline clara com datas/atores.
- [ ] Home apresenta `Produtos` e `Controle e Cadastro de Produtos` como acessos distintos.
- [ ] Visual corresponde ao `@delpi/plugin-ui` e wrappers existentes — sem CSS paralelo global.
- [ ] Teclado, tab order, foco, aria-live, tema e contraste validados.
- [ ] Browser desktop/tablet/mobile com screenshots e interação real.
- [ ] Regressões TS/build/Vitest e REST/EVA/PG críticas sem falha.
- [ ] Owner PO aprovou evidências visuais; HML funcional e mudança de produção tratadas em gates SEPARADOS.

## 5. Gates / implementação

`MFE-PRC-UX0`: inventariar exports/props, design tokens e contratos API, produzir quadro de lacunas comprovadas.  
`MFE-PRC-UX1`: central de solicitações e filtros/tabela/status.  
`MFE-PRC-UX2`: detalhe, tabs, cabeçalho, workflow e estados.  
`MFE-PRC-UX3`: intake guiado + editor e fornecedores.  
`MFE-PRC-UX4`: verificação, histórico e revisões.  
`MFE-PRC-UX5`: QA visual completo, responsividade, a11y, screenshots e aprovação.

**Policy de implementação:** menor diff correto, sem produção, sem regressões de PRODUCTS/VAL-01/DAVI, sem troca de owner. Não alegar execução a partir de documentação.

**Estado de liberação:** `VISUAL_REDESIGN_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.
