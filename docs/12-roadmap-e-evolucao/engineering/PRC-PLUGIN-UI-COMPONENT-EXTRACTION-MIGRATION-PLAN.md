# PRC-UI-EXTRACT-01 — Migração de componentes visuais para Plugin UI (pré-requisito frontend)

> **FONTE CANÔNICA ATUAL — 2026-11-13:** [Regras de produto, inconsistências e plano central PRC-TRACK](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md). Este documento é referência histórica/setorial: em caso de divergência sobre no-op, V1, snapshot PRC, REOPEN, RESOLVED/REMOVED, flags durante solicitação, conclusão, permissões ou critérios de aceite, **o plano central prevalece**. Trechos legados contraditórios estão **SUPERSEDED**, não são perguntas abertas nem instruções para implementar. Regras UX não conflitantes continuam válidas. `G1_ARCHITECTURE_DECISION_REQUIRED / TEST_NOT_RUN`.


> **Estado:** `PLANNED / EXECUTION_NOT_RUN` · **Data:** 2026-11-12 · **Owner de apresentação compartilhada:** `plugins/plugin-ui` · **Consumers:** `plugins/engineering` e, onde pertinente, `plugins/my-requests`.  
> **Gate:** nenhuma implementação de frontend de Produtos acompanhados/Versões/Comparação antes de `PRC-UI-EXTRACT-01` alcançar `PASS` com evidência no SHA.  
> [Inventário e wireframes](./PRC-TRACKED-PRODUCTS-UI-COMPONENT-INVENTORY-RESPONSIVE-WIREFRAMES.md) · [Especificação visual](./PRC-PRODUCT-TRACKING-FRONTEND-VISUAL-SPEC.md) · [Regras de negócio](./PRC-PRODUCT-TRACKING-VERSIONS-TRANSVERSAL-FLAGS-DECISIONS.md).

## 1. Decisão de arquitetura

**Regra:** nenhum componente visual primitivo ou personalizado reutilizável deve ser criado ou mantido como implementação exclusiva do Portal Engenharia. O kit `@delpi/plugin-ui/index` é a biblioteca central. O MFE Engenharia pode manter **somente** containers de página, adapters, hooks de dados/estado, autorização recebida do backend, mapeadores e CSS de composição de layout (sem copiar estilos do kit).

A migração **não** altera owner de dados: Engineering API continua source of truth das flags PRC; Keycloak/Core seguem identidade e RBAC; Plugin UI não executa HTTP de domínio, não conhece `requestId`, JWT, `HomeApiError`, idempotência, endpoints, `allowedActions`, status workflow ou políticas de versão.

**Abstraction Gate:** promover apenas componentes com responsabilidade de apresentação reutilizável e API neutra, consumíveis por pelo menos uma superfície atual e uma superfície-alvo legítima. Não extrair helpers de domínio apenas para eliminar arquivos locais. Não criar design system paralelo.

## 2. Inventário de código efetivamente encontrado no GitHub

| Fonte atual | Constatação | Migração |
|---|---|---|
| `plugins/engineering/src/features/product-registration/components/PrcFieldFlagTrigger.tsx` | UI `PrcFieldFlagTrigger` e funções `findOpenFieldFlag`, `findResolvedFieldFlags`, equivalentes de fornecedor, `resolveFlagVisualState`; importa `PrcAttendanceFlag` da API | **Extrair UI neutra** para `plugin-ui` (ex.: `FlagFieldAction`) com props de estado `add/open/resolved`, label, disabled, onActivate, tooltip; **manter** seleção de flags por campo/vínculo e precedência de domínio no adapter PRC |
| `.../PrcFlagModal.tsx` | Modal ~474 linhas, usa `EngineeringHostDialog`, form fields do kit, mas também `createPrcFlag/delete/reopen/resolve/update`, `HomeApiError`, idempotência e target PRC | **Extrair modal/form/legenda/ações visuais** com callbacks e props neutras; **manter** operações, validação de domínio, mapeamento de erros, idempotência e permissão no MFE/Engineering API |
| `.../PrcAttendanceFlags.tsx` | Provider React, `fetchPrcFlags`, contadores, abertura do modal, resumo visual | **Extrair somente** `FlagSummary` e legenda/botões visuais, se houver reuso; **manter** provider/hook de orquestração e busca como adapter local, sem JSX visual próprio |
| `.../PrcTechnicalSheet.tsx` | Já consome `PrcTechnicalSheetView` do Plugin UI; contém edição seletiva, flags e regras de PRC | Manter container/adapter e edição de domínio; substituir UI própria por componentes neutros existentes/extraídos; evitar duplicação |
| `plugins/plugin-ui/src/components/prc/PrcTechnicalSheetView.tsx` | Composição render-only compartilhada entre Engenharia e Minhas Solicitações, exportada em `src/index.ts`; usa `createDashboardDetailCard`, `FieldLabel`, `PRC_FIELD_GROUPS` | **Preservar API e regressão**; quando necessário criar suporte visual neutro para snapshots sem reclassificar snapshot como draft |
| `plugins/engineering/src/ui/engineeringUi.ts` | Façade de exports `@delpi/plugin-ui/index`, inclui `EngineeringHostDialog`, `EngineeringTabs`, `EngineeringDetailCard`, `EngineeringActionButton` | Reusar fábricas do kit; façade de configuração/tema pode permanecer; não implementar primitivos |
| `plugins/plugin-ui/vite.config.ts` | Federation expõe `./index` via `src/index.ts` | Exportar novos símbolos públicos em `index.ts` e provar que sobrevivem ao build MF |
| `plugins/plugin-ui/src/styles/delpi-prc.css` | Fonte CSS neutra compartilhada para ficha/fornecedores, 2 colunas e breakpoint 640px | Estilos genéricos de flags/modal/trigger no kit; CSS de página permanece no MFE |

**Nota:** nomes sugeridos (`FlagFieldAction`, `FlagSummary`, `FlagEditorDialog`) são `TARGET`, **não exports existentes**. Confirmar catálogo antes de criar. Não migrar helpers que dependem de `PrcAttendanceFlag` para Plugin UI como dependência da Engineering API.

## 3. Contratos-alvo de apresentação (TARGET)

### 3.1 `FlagFieldAction` (ou equivalente existente)

- Input: `state: "add" | "open" | "resolved"`, `label`, `disabled?`, `onActivate`, `ariaLabel?`, `helpText?`; sem entidade PRC.
- Output: controle acessível por mouse, teclado e toque; azul/adicionar, vermelho/aberta, verde/resolvida; visual de precedência é calculado **pelo adapter**, não pelo componente.
- Comportamento: visível no foco e toque, hover como aprimoramento; `aria-label`, foco e área clicável adequados; sem mutação automática.

### 3.2 `FlagSummary` / `FlagLegend` (ou equivalentes)

- Input: contagens, rótulos e ações por callback; zero/open/resolved; nenhum `requestId`.
- Output: resumo compacto e legenda consistente; estados vazios explícitos; nenhuma regra de permissão implícita.

### 3.3 `FlagEditorDialog` (ou composição de ModalShell/form kit)

- Input: `open`, `mode`, `title`, `description`, `targetLabel`, `currentValue`, `busy`, `errors`, `availableActions`, callbacks `onSubmit/onResolve/onReopen/onDelete/onClose`.
- Output: apresentação de CRUD, sem `fetch`, sem gerar idempotency key, sem AuthZ; host injeta handlers e controla ações.
- Modal deve respeitar escopo do host/Portal (não cobrir sidebar), focus trap, Escape, tab order, scroll de conteúdo, layout mobile e preservação de texto em erro.
- Preferir composição das fábricas atuais `createHostContainedModalShell`, form fields, `ActionButton`, `StateBanner`; não duplicar shell.

### 3.4 `FlaggedValue` / `FlaggedSupplierCell` (apenas se comprovado necessário)

- Compor label/valor/ação visual neutros, aceitando `ReactNode` e callbacks; **sem** conhecimento de `supplierCode+store`, SA5, `targetPath` ou atributos PRC.
- Identidade do vínculo, seleção da flag e autorização ficam no adapter; preservar tabela de fornecedores como tabela.

## 4. Plano de migração em fases

| Fase | Ação | Critério de saída |
|---|---|---|
| F0 — Reancoragem | HEAD/git status, docs authorities, inventário global do kit e consumidores, testes baseline | Lista de componentes duplicados/equivalentes e RQ/AC fechados |
| F1 — Contratos | Props neutras, ownership, callbacks, acessibilidade, compatibilidade com consumers | Sem imports de Engineering API, hooks de negócio ou endpoints no Plugin UI |
| F2 — Kit | Extrair/aproveitar componentes visuais e CSS/tokens; exports em `plugin-ui/src/index.ts`; tipos | Unit/component tests, build e federation exports PASS |
| F3 — Adaptar PRC existente | Trocar JSX local por imports do kit; manter providers/HTTP/idempotência no MFE; preservar UX e comportamento | PRC flags campo/fornecedor/modal/resumo sem regressão |
| F4 — Verificar outros consumers | Garantir `PrcTechnicalSheetView` e Minhas Solicitações sem regressão, sem dependência nova de Engenharia | Tests/build de plugin-ui, engineering, my-requests PASS |
| F5 — Visual/QA | Desktop, tablet, mobile, teclado/toque, dark/light, host sidebar, errors 403/409, flags | Evidência screenshot e checklist PASS ou pendências explícitas |
| F6 — Fechamento | Residual search, docs, commit SHA, relatório, plano de rollback | `PRC-UI-EXTRACT-01 PASS` somente com evidência; liberar novo frontend |

**Escopo excluído:** novas páginas de produtos acompanhados, endpoints/DB, snapshots, novas regras de negócio, deploy automático, refatoração geral do kit.

## 5. RQ / AC

- **RQ01:** apresentação de flags reutilizável exclusivamente pelo Plugin UI; **AC01:** imports no MFE apontam para `@delpi/plugin-ui/index` ou façade de configuração do kit, sem implementações visuais duplicadas.
- **RQ02:** nenhuma autoridade de domínio no kit; **AC02:** busca residual negativa por `productRegistrationApi`, `HomeApiError`, `fetchPrcFlags`, `requestId`/endpoints PRC nos novos módulos neutros.
- **RQ03:** preservar UX existente; **AC03:** azul/aberta/resolvida, prioridade OPEN, campo/fornecedor, criação/edição/resolução/reabertura/remoção e estados de erro sem regressão.
- **RQ04:** compatibilidade MF; **AC04:** `src/index.ts` exporta símbolos e build remoto/consumidores comprova import real.
- **RQ05:** acessibilidade e responsividade; **AC05:** teclado/foco/toque, modal host-contained, 320–1920px sem overflow indevido, sem hover obrigatório.
- **RQ06:** segurança; **AC06:** AuthZ live/backend-first; nenhuma permissão inferida pelo componente; `403/409` visíveis, não há mutation otimista.
- **RQ07:** rollback; **AC07:** commit reversível e retorno do MFE sem divergência de contratos; registrar ordem de deploy `plugin-ui` antes dos consumidores.
- **RQ08:** preservação de trabalho alheio; **AC08:** diff limitado, nenhuma alteração não relacionada, nenhuma mudança de owner.

## 6. Testes e evidências exigidas

1. Tests unitários do novo kit (state, callbacks, foco, aria, desabilitado, render); testes PRC de integração com providers e API mockada.
2. Build `plugin-ui`, `engineering`, `my-requests`, typecheck; confirmar exports em `remoteEntry`/consumo runtime.
3. Regressão CREATE/UPDATE PRC e campo/fornecedor; não apagar falhas baseline sem evidência.
4. Screenshot/browser no host autenticado: 1920, 1440, 1024, 768, 430, 390, 360, 320; modal não cobre sidebar, scroll e foco corretos.
5. Relatório: HEAD inicial/final, `git status`, arquivos, testes com contagens, PASS/FAIL/TEST_NOT_RUN, SHA, residual search e riscos.
6. Se o ambiente não permitir E2E visual, declarar `TEST_NOT_RUN` e **não** declarar aceite visual.

## 7. Riscos e decisões

- **R1:** extração indiscriminada de `PrcFlagModal` traz HTTP/segurança ao kit → extrair apenas view, injetar callbacks.
- **R2:** `PrcAttendanceFlagsProvider` usa `requestId` e API PRC → permanecer adapter local, sem duplicar apresentação.
- **R3:** CSS `engineering-prc__*` em componente neutro → migrar estilos de componente ao Plugin UI com tokens e classes neutras; CSS de layout local permitido.
- **R4:** `PrcTechnicalSheetView` já compartilhado → preservar contratos e não fazer redesign oportunista.
- **R5:** rollout de kit antes de consumidores → versionar/testar exports, planejar rollback coordenado.
- **R6:** migração exigir novo owner/source of truth → `ARCHITECTURE_DECISION_REQUIRED` e voltar à Coordination.

**Conclusão:** o próximo trabalho autorizado é **somente a extração/migração de apresentação para Plugin UI**. A implementação de Produtos acompanhados permanece bloqueada até aceite desta etapa.
