# PRC-TRACK — Refinamento pós-HML U1/U2/U3: integridade, UX clean e Plugin UI

> **Decisão PO / Coordination — 14/11/2026.** `EXECUTED / HML_VALIDATED` — implementação `2310b0ed52`+`a472c1e33d` em `main`, deploy HML e E2E 28/28 PASS (ver §5). Documento de execução para Devin. Complementa [especificação visual](./PRC-PRODUCT-TRACKING-FRONTEND-VISUAL-SPEC.md), [wireframes responsivos](./PRC-TRACKED-PRODUCTS-UI-COMPONENT-INVENTORY-RESPONSIVE-WIREFRAMES.md), [regras canônicas R01–R18](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md), [diretriz UX §17](./WIREFRAMES.md) e [ledger §59](./PRC-TRACK-DEVIN-IMPLEMENTATION-COORDINATION-AND-PROMPTS.md). Em divergência de negócio, regras canônicas e autoridades prevalecem.

**Base de observação:** oito capturas HML fornecidas pelo PO: listagem Produtos Acompanhados com quatro registros, detalhe/ficha do produto 30190125 V1, timeline V1 e V1/V2 e comparação V1×V2 do produto 30190123. **Captura não prova payload, cobertura nem conteúdo oficial TOTVS**. Inspeção de código no GitHub confirmou componentes `PrcProductsPage.tsx`, `PrcProductDetailPage.tsx`, `PrcProductVersionsTab.tsx`, `prcSnapshot.ts`; estado runtime completo permanece sujeito à investigação.

## 1. Resultado de produto e princípios visuais

Manter a arquitetura U1 (Solicitações | Produtos acompanhados), U2 (ficha somente leitura) e U3 (Versões + comparar). Não reconstruir workflow PRC. Levar a UX ao padrão aprovado das Solicitações: **design limpo, moderno, direcional e contextual**, hero curto, poucos contêineres, dados no lugar certo, linguagem humana pt-BR, rótulos legíveis, contraste, design tokens, feedback e foco. **Plugin UI é o owner da apresentação reutilizável; Engenharia compõe/adapta dados; backend é autoridade de comparação/flags/proveniência.**

## 2. Inventário priorizado de refinamentos

| ID | Pri | Evidência nas capturas / código | Diagnóstico obrigatório | Aceite objetivo |
|---|---|---|---|---|
| UX-P0-01 | P0 | Descrição de 30190125 aparece como `#` na lista, hero e ficha. UI usa `row.description || "—"` e `detail.description || detail.officialCode`, logo `#` passa como string não vazia | Consultar JSON de lista/detalhe/snapshot autorizado + origem e coverage. Identificar se `#` é valor literal persistido, máscara/placeholder indevido ou bug de mapping. Não especular que TOTVS tem valor diferente | Código oficial é identidade principal do hero; descrição só como valor com origem/qualidade explícita; nunca substituir snapshot histórico por leitura TOTVS ao vivo, não “corrigir” dados históricos por CSS. Cobrir `#`, vazio, null, válido e legado |
| UX-P0-02 | P0 | Comparação V1×V2 mostra `Antes —` e `Depois valor` em vários campos. `PrcProductVersionsTab` usa `scalarText(null) => "—"`, mas só banneriza `result.comparable=false` global | Auditar `compute_technical_diff`, campo a campo `coverage/valueOrigin`, snapshots V1/V2, `fieldChanges`, `supplierLinkChanges`, `comparable`, flags. Distinguir **adição real** de lacuna/incomparabilidade | Campos não conhecidos não são “diferença técnica comprovada”; exibir Incomparável/Não disponível na versão de origem conforme DTO, sem diff inventado. Corrigir backend se defeito comprovado, consumidor se mapping incorreto, com teste memory/PG/API |
| UX-P1-01 | P1 | Hero da listagem muito alto, texto técnico longo, divisórias/áreas vazias | Inspecionar `EngineeringPageHero` e tokens | Título + seletor Solicitações/Produtos de fácil reconhecimento, frase curta, ajuda contextual “não é catálogo inteiro TOTVS”, busca/filtros organizados sem altura excessiva; preservar `?area=products` e `?view=pending` |
| UX-P1-02 | P1 | Tabela interna dentro de cartão externo, borda/padding em duplicidade | Ver wrappers e `EngineeringDataTableSection` do Plugin UI | Um único plano de listagem, cinco colunas, sort/paginação/busca server-side, estado vazio, loading, 403, foco/click de linha, sem CSS global override |
| UX-P1-03 | P1 | Hero do produto tem título `#`, código oficial subordinado | Ver `PrcProductDetailPage.tsx` e produto/snapshot atual | **Código oficial em destaque**; descrição legível e com qualidade, Vn “Atual acompanhada”, origem/data secundários, refresh discreto; não dar a entender versão TOTVS live |
| UX-P1-04 | P1 | Ficha técnica com cards grandes e bastante vazio | Inspecionar adapter `prcSnapshot.ts`, `PrcTechnicalSheetView` e CSS/tokens Plugin UI | Leitura densa e consistente com duas colunas quando couber e uma em 320/390px; grupos/fornecedores/flags preservados; read-only; ausente ≠ zero; evitar duplicação de campo/metadado |
| UX-P1-05 | P1 | Timeline expandida enumera 8–9 nomes de campos, muita altura | `PrcProductVersionsTab` usa `changedPaths` integral em lista | Cada versão exibe Vn, data, origem e resumo conciso: contagem por categoria **só quando derivável do payload**; detalhe expandido agrupado por seções/fornecedores; reduzir densidade e preservar `aria-expanded`, teclado/touch, link de origem e Ver ficha; V1 não significa cadastro criado no ERP |
| UX-P1-06 | P1 | Comparação em tabela bruta, `—` ambíguos, supplier path pode ser técnico | Inspecionar DTO, labels compartilhados, `EngineeringSelectField` e `compute_technical_diff` | Grupos iguais à ficha, Antes Vx/Depois Vy, legenda clara de origem/indisponibilidade, fornecedores `supplierCode+store`, flags em seção separada, same-version desabilitado; **diff somente backend** |
| UX-P1-07 | P1 | Dropdown de versão parece cobrir título; screenshots rolados cortam parte superior de hero | Reproduzir com Chrome/Zoom/teclado; inspecionar select portal, sticky shell e scroll restoration | Se comprovado, ajustar via componente do kit (overlay/focus/flip/clamp) e não hack CSS. Sem topbar cobrindo âncora/foco. F5/back e seleção por URL previsíveis |
| UX-P2-01 | P2 | Origem como UUID abreviado `#41413651` etc., pouca explicação | `prcShortId`, link, tooltip e permissão | ID curto consistente + tooltip/nome acessível ID completo, deep-link autorizado; não inventar número sequencial |
| UX-QA-01 | Gate | §59: dark, zoom200, teclado E2E e 403 não foram testados; bundle MFE relatado como anterior | Inspecionar SHA/digest realmente servido, remoteEntry, tema e usuário de teste negado disponível | E2E 1440/768/390/320, claro/escuro, 200%, teclado, 403 se massa autorizada; registrar `TEST_NOT_RUN` para indisponível, nunca PASS sem execução |

## 3. Sequência de execução — não começar por CSS

### G0 — Prova de dados e inventário
1. Reancorar `origin/main`, HEAD, status e contratos. Preservar WIP concorrente, sem branch.
2. Capturar amostra autorizada de `technical-records`, detalhe, revisão e `comparison` para 30190125 e 30190123, **apenas GET**, em HML; documentar resultado sem vazar token ou conteúdo sensível.
3. Tabela `campo → snapshot V1 → coverage/origem V1 → snapshot V2 → coverage/origem V2 → comparável? → diff real? → apresentação`.
4. Classificar P0 como `PROVEN_DEFECT`, `LEGITIMATE_DATA_WITH_UX_GAP` ou `INCONCLUSIVE`, com evidência. Não corrigir fato sem prova.

### G1 — Semântica e contrato
1. Revisar `compute_technical_diff` e interpretação de `comparable`; campos sem cobertura não podem ser classificados como mudança por `None→valor` sem regra e evidência.
2. Preservar R01 V1 baseline, R02 no-op, R03 diff técnico real, snapshots imutáveis, proveniência `request_id`, flags por intervalo e estado OPEN/RESOLVED/REMOVED.
3. Corrigir menor contrato/backend ou adapter se necessário, com testes de snapshots legacy/partial, supplier code+store, nulos, `#` literal, comparação normal/incomparable, autorização e regressão.
4. Backend/Engineering API continua autoridade, sem enrich de snapshot por TOTVS live, sem novo source of truth ou escrita ERP.

### G2 — UX Plugin UI-first
1. Inventariar exports e tokens reais: PageHero, SegmentToggle, ScopeChipBar, DataTableSection, DetailCard, Tabs, SelectField, PrcTechnicalSheetView e FlagFieldAction/Summary/Legend/Dialog; preferir composição do kit.
2. Implementar hero e tabela leves, identidade correta do produto, ficha mais compacta, timeline orientada à diferença, comparação sem valores ambíguos, origin links legíveis, select/scroll somente se defeito comprovado.
3. Antes de novo componente compartilhado aplicar **Abstraction Gate**: owner, consumers, duplicação real, contrato, boundary, menor solução. Não importar internals de outros MFEs. Não modificar CSS global, `.delpi-ui-*` ou estilos do host.
4. Linguagem humana pt-BR, progresso/detalhes contextuais, sem informação visual repetida ou ação sem autoridade.

### G3 — E2E e aceite
- HML Chromium com screenshot antes/depois e SHA de backend/MFE efetivamente servido; CSS light/dark, zoom 200%, desktop/tablet/mobile 390/320 e legibilidade. Verificar overlay, focus order, Escape/Enter, labels/ARIA, contrast, touch targets (~44px), overflow horizontal e cabeçalho fixo.
- Casos: U1 Solicitações preservado (inclusive filtros, Cards/Kanban, `?view=pending`), U1 Produtos com list/search/filter/sort/page, U2 versão atual e histórica, fornecedores, flags, U3 timeline, V1-only, V1×V2 comparável/incomparável, F5/back, 403 real se credencial apropriada, loading/empty/error.
- Testes unitários frontend, backend memory/Postgres se código backend mudar, typecheck e build. **Nenhum write TOTVS; nenhum deploy PRD.** Se dados não existirem, fixtures no teste isolado com evidência `SIMULATED`, sem alegar E2E real.

## 4. Done/relatório obrigatório

Entregar matriz `ID → diagnóstico → causa → fix → teste → resultado`. Priorizar P0 antes de mexer na aparência; P1/P2 depois. `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN` por caso, mencionar gap residual e drift sem mascarar. Manter traceability dos usuários/solicitações/revisões oficiais e controles de acesso; preservar rollback. Implementação e deploy só DEV/HML pelo Devin; **PRD_NOT_AUTHORIZED**.

**Gate final:** `DATA_SEMANTICS_PROVEN + UX_DESIGN_REFINED + HML_VISUAL_QA_PASS` (cada parte comprovada). Até então: `PO_REFINEMENT_APPROVED / IMPLEMENTATION_PENDING / TEST_NOT_RUN`.

## 5. Resultados de execução (14/11/2026 — implementado, testado e homologado em HML)

Implementação: `2310b0ed52` (P0–P2) + `a472c1e33d` (regressão de recolhimento + spec de refinamento). Deploy HML: `engineering-api` sha256:47b58ce877cb, `engineering` (MFE) sha256:6c8b9ae4f5af, `plugin-ui` sha256:c25898633d3e — 22/22 containers healthy. E2E Chromium real no host HML: **28/28 PASS** (4 viewports × 7 testes). Sem writes TOTVS; sem deploy PRD.

| ID | Evidência | Diagnóstico | Causa | Correção | Teste | Resultado |
|---|---|---|---|---|---|---|
| UX-P0-01 | Postgres HML: snapshot V1 schema-2 de `30190125` tem `fields.description.value="#"` com `coverageState=present`, `valueOrigin=inherited_confirmed` | `LEGITIMATE_DATA_WITH_UX_GAP` — `#` é valor literal persistido com proveniência; nenhuma evidência de valor alternativo no TOTVS | Hero usava `detail.description || officialCode` → `#` virava identidade da página | `PrcProductDetailPage`: `title=detail.officialCode`; descrição como subtítulo (`descUnavailable` quando ausente); snapshot histórico intacto, sem leitura TOTVS live | Unit `prcSnapshot.test.ts` (`#`, vazio, null, legado) + E2E P0-01 heading `30190125` | PASS |
| UX-P0-02 | `30190123` V1 = snapshot legado esparso (só `unit`+identidade); V2 = schema-2 populada; `changes` persistidos com `before:null` para todos os campos | `LEGITIMATE_DATA_WITH_UX_GAP` — diff server-side legível, mas `null→valor` não distinguia «não observado em V1» de «nulo registrado» | Contrato do diff não carregava presença por lado; UI imprimia `—` ambíguo | `compute_technical_diff` emite `beforePresent`/`afterPresent` (fields, link added/removed, supplier attrs); UI exibe «Sem dado nesta versão (Vx)» + legenda; diff segue server-side | `TestDiffPresenceSemantics` (3 casos) + suite 104/104 + E2E P0-02 texto+legenda+grupo Fornecedores | PASS |
| UX-P1-01 | Hero alto com descrição longa | — | Título duplicado com o nome da área; descrição verbosa | Título `Controle e Cadastro de Produtos` nas duas áreas; descrição curta «Versões técnicas confirmadas pela Engenharia — não representa o catálogo geral TOTVS»; seletor/busca/filtros/contagem preservados | E2E U1 (toggle, busca, chips) | PASS |
| UX-P1-02 | `section.delpi-ui-table-section` (card-shell) + `div.delpi-ui-table-wrap--section` (borda+fundo) = duplo contorno | — | Kit aplicava card-shell à seção E borda ao wrap interno | Composição no kit `data-table.css`: `.delpi-ui-table-section > .delpi-ui-table-wrap--section { border:none; border-radius:0 }` — superfície única para todos os consumers, zero CSS de kit no MFE | E2E U1 listagem + screenshot | PASS |
| UX-P1-03 | Hero `#` como título | mesma causa do P0-01 | idem | Código oficial como heading; chip `Vn · acompanhada`; metas «Última evolução técnica» e «Solicitação de origem»; refresh ghost | E2E P0-01 | PASS |
| UX-P1-04 | Cards altos/vazios na ficha consolidada | — | `PrcTechnicalSheetView` sem variação de densidade | Prop `density="compact"` no kit (tokens `--delpi-ui-card-padding`/`--card-padding-mobile`, gaps menores); consumer opt-in somente na ficha consolidada; edição de solicitações intacta | plugin-ui 2517/2517 + E2E U2 | PASS |
| UX-P1-05 | Timeline expandida listava campos crus | — | Resumo=detalhe; e bug real: `display:flex` anulava `[hidden]` — painel nunca recolhia visualmente | Resumo conciso (contagem + até 3 labels + «e mais N»), detalhe agrupado pelos grupos da ficha + fornecedores + origem + «Ver ficha desta versão»; guarda `[hidden]{display:none}`; V1 rotulada «Primeiro acompanhamento confirmado» | E2E U3 (hidden→visible, aria-expanded) | PASS |
| UX-P1-06 | Tabela bruta com `—` ambíguos e paths técnicos | — | sem agrupamento nem presença | Comparação agrupada pelos grupos canônicos (`PRC_FIELD_GROUP_BY_PATH`) + seção Fornecedores com identidade `code|store` legível e PN·Cat; células presença-cientes; bandeiras em seção própria; same-version bloqueada | E2E P0-02 | PASS |
| UX-P1-07 | Seletor cobria título nas capturas | `INCONCLUSIVE→SEM_DEFEITO` | `EngineeringSelectField` é `<select>` nativo — o popup é do SO, não overlay/z-index | Nenhuma alteração (não substituir controle por estética); teclado/foco verificados | E2E UX (Tab/Enter/Escape implícito nos seletores) | PASS (sem defeito comprovado) |
| UX-P2-01 | IDs abreviados sem contexto | — | só `prcShortId` visível | `prcShortId` + `title` com ID completo no hero e na timeline; navegação autorizada preservada | E2E P0-01 (origem visível) | PASS |
| UX-QA-01 | §59: dark/zoom/teclado/403 pendentes | — | cobertura E2E incompleta | Spec `prc-tracked-products-refinement.spec.ts`: `data-theme=dark` via `localStorage theme`, zoom 200% sem overflow horizontal, Tab/Enter | 28/28 (4 viewports) | PASS; **403 TEST_NOT_RUN** (sem identidade negada autorizada em HML) |

**Regressões:** fila Solicitações preservada (toggle + deep-link `?view=pending` intactos — nenhuma mudança funcional na fila); R01–R18 preservados (diff, imutabilidade, proveniência, flags por intervalo inalterados — mudança foi aditiva no contrato). **Suites:** backend 104/104 (`test_prc_snapshot_versioning`, `test_prc_record_flags`, `test_product_registration`); MFE 430/430 (+12 `prcSnapshot.test`); plugin-ui 2517/2517; typecheck PASS; build PASS (kit + MFE). **Residual:** falha preexistente `intake D16 422` na suíte backend ampla (não deste escopo); `beforePresent` ausente em `changes` persistidos de revisões antigas → consumidor cai no fallback `—` somente naquele histórico (compare sempre recalcula server-side, portanto correto).

## 6. Diretriz complementar do PO — Plugin UI obrigatório também para componentes primitivos (14/11/2026)

**Decisão superveniente para refinamentos futuros:** cada primitivo de interface (botão, campo, select, chip/badge, card, tabela, tooltip, popover, diálogo, abas, carregamento/estado, avatar e respectivos ícones/tokens) deve ser consumido do `@delpi/plugin-ui` quando houver equivalente público. Os componentes compostos de ficha, timeline e listagem também devem reutilizar o kit. **É proibido criar um segundo conjunto de primitivos visuais dentro do MFE Engenharia**; estrutura HTML semântica e composição local permanecem legítimas.

Ao executar ajuste pontual subsequente, fazer inventário de exports no HEAD, identificar elementos locais equivalentes, substituir apenas quando a compatibilidade e regressão forem demonstráveis, e fazer Abstraction Gate para uma eventual extensão genérica **no owner Plugin UI**. DOM/estilo interno do kit não deve ser copiado para uma implementação paralela; não confundir classes CSS utilitárias de layout com novo primitivo. Regra transversal em `WIREFRAMES.md` §17.1.

**Status:** `PO_DESIGN_PRIMITIVES_RULE_APPROVED / DOCUMENTED / NO_NEW_CODE_CHANGE / HML_TEST_NOT_RUN_FOR_THIS_RULE`. O aceite anterior de U1/U2/U3 não é automaticamente revogado; inspeção e ajustes futuros devem respeitar esta regra.

## 7. Refinamento final — Semântica da timeline e densidade da ficha técnica (14/11/2026 — implementado, testado e homologado em HML)

**TASK_ID:** `EVA-PRC-TRACK-FINAL-UX-TIMELINE-TECHNICAL-SHEET-HML-01` — implementação `0d489aaa98` em `main`. Deploy HML: `engineering-api` 46d81200aacf, `engineering` (MFE) cb96b92f4912, `plugin-ui` b4caa957d5f2 — 23/23 containers healthy. E2E Chromium real no host HML (`hml-tester`): **36/36 PASS** (4 viewports × 9 testes). Sem writes TOTVS; sem deploy PRD.

### Diagnóstico

- `list_revisions` expunha só `changedPaths` — a timeline rotulava «N mudanças técnicas» incluindo campos nunca observados na revisão anterior (V1 legada esparsa × V2 schema-2). Diferença de cobertura era apresentada como alteração.
- Ficha compacta ainda fixa em 2 colunas: campos curtos deixavam a metade direita do card vazia.
- Comparação repetia `<thead>` idêntico por grupo e «Sem dado» era visualmente igual a texto comum.

### Mudanças

| Item | Mudança | Owner |
|---|---|---|
| G1 contrato | `list_revisions` emite `diffSummary` aditivo por revisão (`comparable`, `total`, `fields{Modified,NewlyObserved,NoLongerObserved}`, `suppliers{Added,Removed,Modified,NewlyObserved,NoLongerObserved}`), classificado pelo mesmo `compute_technical_diff` entre snapshots consecutivos — recomputo read-side, snapshots imutáveis intocados; `null` na baseline | Engineering API |
| G1 timeline | Vn>1: «N diferenças registradas» + qualificadores («M alteração(ões) técnica(s) confirmada(s)», «K campo(s) sem informação comparável na versão anterior», «S fornecedor(es) vinculado(s)/desvinculado(s)», «J campo(s) deixaram de ser observados»); `comparable=false` → ressalva explícita; payload antigo sem `diffSummary` → resumo neutro por `changedPaths`; V1: «Primeiro acompanhamento confirmado» + «N campo(s) registrado(s) / M vínculo(s)» — sem afirmar criação no TOTVS | MFE (copy `prcCopy`, helper `revisionDiffBuckets` em `prcSnapshot.ts`) |
| G2 densidade | `.delpi-prc__sheet--compact .delpi-prc__sheet-grid` → `repeat(auto-fit, minmax(190px,1fr))` (3–4 col. em cards largos, 1 col. ≤640px). Escopo exclusivo `density="compact"` — formulários editáveis seguem 2 colunas | plugin-ui (token-grade, sem classe nova no MFE) |
| G3 comparação | Tabela única: um `<thead>` + um `<tbody>` por grupo canônico com `<th scope="rowgroup" colspan=3>`; «Sem dado nesta versão» com `engineering-prc__diff-missing` (itálico + sublinhado pontilhado + `title`) | MFE |

### Componentes e primitivos

Reutilizados, sem novo primitivo: `EngineeringPageHero`, `SegmentToggle`, `ScopeChipBar`, `DataTableSection(unframed)`, `DetailCard`, `Tabs`, `SelectField`, `PrcTechnicalSheetView(density="compact")`, `StateBanner`, `ActionButton`. HTML semântico: `<ol>` timeline, `<table>` comparação — não são primitivos duplicados (§17.1/§6). Abstraction Gate: nada a promover — `density` e a grade auto-fit são evolução interna do componente canônico.

### Testes e evidências

- Backend: `TestRevisionDiffSummary` ×6 (baseline null, motivador legado×schema-2 `fieldsModified=0`, mudança real `fieldsModified=1`, nulo registrado × não observado, atributos de vínculo, `comparable:false`, índice HTTP end-to-end) — suíte PRC 256/256.
- MFE: `revisionDiffBuckets` ×5 — 435/435 total; typecheck PASS; build kit+MFE PASS; plugin-ui 2630/2630.
- E2E novo: `G1` (textos «diferenças registradas», «sem informação comparável», ausência de «mudança(s) técnica(s)», baseline «registrado(s)»), `G2` (≥3 col. ≥1024px, 1 col. ≤640px, sem overflow); `P0-02` atualizado p/ `rowheader` dos grupos na tabela única.
- Screenshots inspecionados: timeline (semântica nova), ficha compacta (3 col. desktop/1 col. mobile), comparação, tema escuro.

### Resultado e limitações

`PASS` — linguagem da timeline passa a distinguir alteração confirmada de expansão de cobertura em todos os estados (legado×schema-2, comparáveis normais, baseline, incomparável). Limitações: `diffSummary` é recomputado na leitura (custo desprezível por registro); fornecedor «vinculado» descreve diferença registrada, não intenção do usuário; 403 permanece `TEST_NOT_RUN` (sem identidade negada autorizada em HML); E2E usou credencial `hml-tester` (`HML_TEST_*` do `.env.hml`) — a credencial `ti_delpi` não existe no realm HML.

## 8. UX-P1-08 — Refinamento do seletor de versões (14/11/2026 — implementado e homologado em HML)

**TASK_ID:** `EVA-PRC-TRACK-VERSION-SELECT-PLUGIN-UI-UX-HML-01` — commits `bf03396d48` (MFE+kit+specs) e `e0eafe0dbf` (fix de foco no kit). Deploy HML: `engineering` 5d931acf10d2, `plugin-ui` 3532cc3001a0 — 23/23 healthy. E2E: **40/40 PASS** (4 viewports × 10 testes).

### Causa identificada

Os seletores «Versão de origem/destino» usavam `EngineeringSelectField` — `<select>` nativo cujo popup é controlado pelo SO/navegador e podia abrir sobre o título «Comparar versões». Não era defeito de z-index; era o popup nativo.

### Escolha técnica (Abstraction Gate)

O kit já expõe o componente canônico para campos com opções reais: `EngineeringSearchableSelect` (`SelectControl` + `AnchoredPanelPortal` — painel ancorado com flip/clamp de viewport, tema via `useDelpiUiPortalTheme`, escopo MFE auto-resolvido), já consumido pelo `PrcRequestInformationModal`. **Nenhum primitivo novo** — substituição direta no `PrcProductVersionsTab`, com `placeholder`/`allowEmpty` substituindo a pseudo-opção «Selecione». A extensão necessária foi feita **no owner** (plugin-ui): navegação por teclado do `SelectControl` — ArrowDown/ArrowUp no trigger abre focando 1ª/última opção, setas/Home/End navegam, Escape/Tab fecham devolvendo foco ao trigger, seleção devolve foco. Beneficia todos os consumers do select rico.

### Defeito real encontrado e corrigido

`focus()` imediato no `useEffect` era ignorado pelo browser: o painel ancorado monta `visibility:hidden` até o layout de posicionamento — jsdom não aplica a regra, então o defeito só apareceu no Chromium real de HML. Fix: foco da 1ª/última opção deferido para `requestAnimationFrame` (commit `e0eafe0dbf`).

### Posicionamento (comportamento verificado)

`resolveAnchoredPanelCoords` abre abaixo quando `anchor.bottom + panelHeight` cabe; inverte para cima quando necessário. Medido em HML: trigger no fim da página (viewport 720) → panel 501–613 acima do campo (flip necessário, especificado); com espaço abaixo → abre abaixo sem cobrir o título. Sempre dentro da viewport, sem clipping por card (portal no body).

### Testes

- Kit: `SelectField.test.tsx` 9/9 (+6 de teclado: abertura por seta, navegação, clique/Escape/Tab com retorno de foco); suíte completa 2636/2636.
- MFE: 238/238 PRC; typecheck PASS; builds kit+MFE PASS.
- E2E novo `G4`: abre/clica, ancorado±flip, dentro da viewport, não cobre título quando há espaço, Escape, teclado completo (ArrowDown→opção focada→Enter→seleção V1), comparação server-side V1×V2 preservada — 4 viewports.
- Specs U1–U3 adaptadas ao seletor rico via helper `selectKitOption` (trigger+listbox).

### Limitações

- Flip acima do campo continua possível — e correto — quando não há espaço abaixo (comportamento especificado, não defeito).
- `EngineeringSelectField` (nativo) permanece para opções triviais sem busca em outros formulários — sem substituição indiscriminada, conforme escopo.
- `searchable` não habilitado nos seletores de versão (≤3 opções); disponível no componente quando fizer sentido.
