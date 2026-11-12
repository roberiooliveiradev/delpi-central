# PRC — Inventário GitHub + wireframes responsivos + especificação dimensional

> **2026-11-12 · PROVEN_SOURCE / TARGET_LAYOUT / VISUAL_TEST_NOT_RUN**  
> Complementa [especificação visual](./PRC-PRODUCT-TRACKING-FRONTEND-VISUAL-SPEC.md) e [regras de domínio](./PRC-PRODUCT-TRACKING-VERSIONS-TRANSVERSAL-FLAGS-DECISIONS.md).  
> Inspeção de fontes no GitHub (default branch, revisão consultada com resultados de busca em `287a53422099b4eb76b2ba94aab4ab30dd4d1be5`). **Sem execução local/browser.**  
> Diagramas são wireframes textuais **não** screenshots nem pixels de implementação. Dimensões não encontradas no CSS são **propostas TARGET**, não tokens oficiais.

## 1. Princípio de implementação: Plugin UI como origem

**Consumir exports do `@delpi/plugin-ui/index` através da façade** `plugins/engineering/src/ui/engineeringUi.ts`, mantendo prefixo `engineering`, tokens oficiais e Module Federation. Não importar `portal/src/ui-kit` diretamente no MFE nem copiar CSS/JSX de kit para features. A top bar global é do Portal; **não** instanciar outra top bar nas páginas.

### 1.1 Matriz rastreável de componentes

| Ref | Componente/factory comprovado | Origem GitHub | Uso no novo fluxo | Estado |
|---|---|---|---|---|
| C01 | `EngineeringPagePath` ← `createDashboardPagePath` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Breadcrumb nas listas/detalhe | PROVEN_EXPORT |
| C02 | `EngineeringPageHero` ← `createDashboardPageHero`, `density="compact"` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Hero único da lista, hero de produto | PROVEN_EXPORT |
| C03 | `EngineeringSegmentToggle` ← `createDashboardSegmentToggle` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Solicitações / Produtos acompanhados | PROVEN_EXPORT; props a verificar |
| C04 | `EngineeringFiltersRow`, `EngineeringFilterInput`, `EngineeringFilterSelect` ← `createDashboardFiltersKit` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Filtros de cada segmento | PROVEN_EXPORT |
| C05 | `EngineeringActionButton` ← `ActionButton` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Nova solicitação, comparar, limpar filtros | PROVEN_EXPORT |
| C06 | `DataTableSection` (wrapper de feature) + `ENGINEERING_DATA_TABLE_*` | [DataTableSection.tsx](../../../plugins/engineering/src/features/lmps/components/DataTableSection.tsx) e [ProductsListPage.tsx](../../../plugins/engineering/src/features/products/pages/ProductsListPage.tsx) | Tabela acompanhados, referências da fila | PROVEN_REFERENCE; **wrapper não é export direto do Plugin UI** |
| C07 | `EngineeringStatusBadge` ← `createDashboardStatusBadge` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Versão/estado quando houver contrato | PROVEN_EXPORT |
| C08 | `EngineeringTabs` ← `createDashboardUnderlineNav` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Ficha técnica / Versões | PROVEN_EXPORT; mode=tabs |
| C09 | `PrcTechnicalSheetView` | [PrcTechnicalSheetView.tsx](../../../plugins/plugin-ui/src/components/prc/PrcTechnicalSheetView.tsx), [index.ts](../../../plugins/plugin-ui/src/index.ts) | Base visual de cards e fornecedores | PROVEN_EXPORT; **props hoje são de solicitação**, adaptação a snapshot TO_DESIGN |
| C10 | `createDashboardDetailCard`, `FieldLabel`, `PRC_FIELD_GROUPS` | [PrcTechnicalSheetView.tsx](../../../plugins/plugin-ui/src/components/prc/PrcTechnicalSheetView.tsx) | Cards, labels, grupos técnicos | PROVEN_SOURCE |
| C11 | `EngineeringDetailCard`, `EngineeringDetailFieldGrid` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Detalhes complementares sem duplicar C09 | PROVEN_EXPORT |
| C12 | `PrcFieldFlagTrigger` | [PrcFieldFlagTrigger.tsx](../../../plugins/engineering/src/features/product-registration/components/PrcFieldFlagTrigger.tsx) | Bandeira no campo/fornecedor | PROVEN_LOCAL; **ainda não export Plugin UI** |
| C13 | `PrcAttendanceFlagsProvider`, `PrcAttendanceFlags` | [PrcAttendanceFlags.tsx](../../../plugins/engineering/src/features/product-registration/components/PrcAttendanceFlags.tsx) | Estado/resumo de flags | PROVEN_LOCAL; requestId-centric, **não reutilizar como product provider sem contrato** |
| C14 | `PrcFlagModal` + `EngineeringHostDialog` | [PrcFlagModal.tsx](../../../plugins/engineering/src/features/product-registration/components/PrcFlagModal.tsx), [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Criar/tratar flag | PROVEN_LOCAL + kit shell; requestId-centric |
| C15 | `EngineeringStateBanner`, `EngineeringEmptyState`, `EngineeringLoadingActivityCard` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Erro, vazio, loading | PROVEN_EXPORT |
| C16 | `EngineeringTimeline` ← `createTimeline` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) | Histórico de versões/eventos | PROVEN_EXPORT; contrato de itens a verificar |
| C17 | `EngineeringSectionCard`, `EngineeringFieldLabel`, `EngineeringTextField`, `EngineeringTextAreaField`, `EngineeringFormActions` | [engineeringUi.ts](../../../plugins/engineering/src/ui/engineeringUi.ts) e [PrcFlagModal.tsx](../../../plugins/engineering/src/features/product-registration/components/PrcFlagModal.tsx) | Filtros, modal, estados | PROVEN_EXPORT/USAGE |
| C18 | `EngineeringDataCardsGrid`, `EngineeringInteractiveDataCard`, `EngineeringKanbanBoard` | [PrcQueuePage.tsx](../../../plugins/engineering/src/features/product-registration/pages/PrcQueuePage.tsx) | **Preservar** visões existentes em Solicitações | PROVEN_USAGE |

**Boundary de reuso:** C09 é composição render-only compartilhada entre Engenharia e Minhas Solicitações; atualmente `draft`/`requestType`/`changedPaths`/`supplierLinkChanges` são de caso PRC. Não passar snapshot histórico como `draft` sem contrato/adaptação explícita. C12–C14 residem no MFE Engenharia, não no Plugin UI: antes de exigir import direto do kit, aplicar Abstraction Gate (owner, consumers, props neutras, testes, export MF) e extrair somente a apresentação reutilizável se necessário. Não criar falsos exports.

## 2. Dimensões: fonte comprovada versus proposta

### 2.1 Valores **PROVEN** em CSS consultado

Fonte: [`plugins/plugin-ui/src/styles/delpi-prc.css`](../../../plugins/plugin-ui/src/styles/delpi-prc.css).

| Alvo CSS | Valor comprovado |
|---|---|
| Pilha `.delpi-prc` | `gap: var(--delpi-ui-section-gap, 16px)` |
| Grade ficha `.delpi-prc__sheet-grid` | 2 colunas iguais; `gap: 12px 16px` |
| Grade ficha em `max-width:640px` | 1 coluna |
| Label da ficha | `font-size: .85rem`, `font-weight:600`, ícone/label `gap:6px` |
| Valor da ficha | `margin-top:4px`; quebra de palavras |
| Tabela fornecedores | `width:100%`, `font-size:.85rem`; `th/td padding:6px 8px` |
| Célula de fornecedor sinalizável | `gap:6px`; `min-height:28px` |
| Nota de alteração | `font-size:.82rem`; margem superior `var(--delpi-ui-grid-gap,12px)` |

Fonte: [`plugins/engineering/src/features/product-registration/prc.css`](../../../plugins/engineering/src/features/product-registration/prc.css).

| Alvo | Valor comprovado |
|---|---|
| Root PRC | `gap:var(--en-section-gap)` |
| Grid detalhe PRC | colunas `3fr 2fr`, `gap:var(--en-grid-gap)` |
| Grid detalhe PRC em `max-width:1100px` | 1 coluna |
| Ações PRC | `display:flex; flex-wrap:wrap; gap:8px` |
| Confirm body | `gap:12px` |

**Importante:** paddings internos do `PageHero`, `DetailCard`, `DataTableSection`, `ModalShell` e top bar **não foram medidos neste inventário**. Não sobrescrever o kit com valores inventados.

### 2.2 Envelope responsivo **TARGET** (proposta para revisão com tokens reais)

Os números abaixo definem **layout da página e áreas de composição**, não substituem dimensões intrínsecas do Plugin UI. Usar `box-sizing:border-box`, `min-width:0`, `width:100%` nos filhos flex/grid.

| Viewport (CSS px) | Margem lateral da área MFE | Espaço entre blocos | Hero / filtros | Ficha técnica | Tabela |
|---|---:|---:|---|---|---|
| Desktop largo `>=1440` | 24px TARGET | 24px TARGET | filtros em até 3 colunas; segmentado em linha própria no hero | **2 colunas de campos** (C09); cards 100% | ocupa largura; scroll interno apenas se necessário |
| Desktop `1024–1439` | 20px TARGET | 20px TARGET | filtros 2–3 colunas conforme espaço | 2 colunas | reduzir colunas opcionais; não cortar conteúdo |
| Tablet `768–1023` | 16px TARGET | 16px TARGET | filtros 2 colunas; ações podem quebrar | 2 colunas até breakpoint real C09 (640px) | overflow-x contido e sinalizado |
| Mobile `390–767` | 12px TARGET | 16px TARGET | filtros 1 coluna; segmentado 100% | 1 coluna em `<=640px`; 2 colunas em 641–767 se couber | scroll horizontal no container, primeira coluna identificadora visível quando viável |
| Mobile estreito `320–389` | 12px TARGET | 12px TARGET | 1 coluna; botões podem ocupar largura | 1 coluna | scroll horizontal com indicação, sem truncar identificadores |

**Breakpoint de 640px para a grade da ficha é PROVEN; os demais intervalos são alvos de teste**, não breakpoints existentes do kit. **Alvo de toque mínimo 44×44px TARGET** para botões de ícone/flags, sem ampliar artificialmente a linha da tabela; usar hit area acessível. Largura máxima da página deve respeitar o container já aplicado pelo Portal, não definir `max-width` novo sem inspeção.

## 3. Wireframes textuais versionados (legíveis no GitHub)

Legenda: `[Cnn]` = componente da matriz; `[T]` = comportamento TARGET; medidas em px são envelopes de layout propostos; `[P]` = CSS confirmado.

### WF-01 — Entrada Solicitações, desktop 1440+

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR GLOBAL DO PORTAL (HOST — NÃO DUPLICAR)                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ [C01] Início / Controle e Cadastro de Produtos                               │
│ ┌────────────────────── [C02] HERO ÚNICO ──────────────────────────────────┐ │
│ │ CONTROLE E CADASTRO DE PRODUTOS                  [C05 Nova solicitação] │ │
│ │ Acompanhe solicitações e produtos sob gestão da Engenharia              │ │
│ │ [C03  SOLICITAÇÕES  |  PRODUTOS ACOMPANHADOS]                            │ │
│ │ [C04 Busca nº/código/descrição] [Status] [Tipo]                          │ │
│ │ [Campos sinalizados]                                                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ [C03 Tabela | Cards | Kanban]                                  [Atualizar] │
│ ┌───────────────────────── FILA EXISTENTE ────────────────────────────────┐ │
│ │ [C06] Nº | Tipo | Solicitante | Código | Abertura | Status | Responsável │ │
│ │  ... [C07 badge] ...                                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
Envelope MFE: 24px laterais e 24px entre seções [T]; padding do hero = kit.
```

### WF-02 — Produtos acompanhados, desktop 1440+

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR GLOBAL (HOST)                                                        │
│ [C01] Início / Controle e Cadastro de Produtos                               │
│ ┌──────────────────────── [C02] HERO ÚNICO ───────────────────────────────┐ │
│ │ CONTROLE E CADASTRO DE PRODUTOS                                        │ │
│ │ [C03 Solicitações | ● PRODUTOS ACOMPANHADOS]                           │ │
│ │ [C04 Código/descrição] [Flags: todas/abertas] [Ordenar: última evolução]│ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────── PRODUTOS ACOMPANHADOS ──────────────────────────────┐ │
│ │ [C06] Código | Descrição | Versão | Flags abertas | Última evolução     │ │
│ │ 10080025 | TERM. OLHAL... | V5 | 2 | 12/11/2026                      > │ │
│ │ 10080022 | TERM. OLHAL... | V1 | 0 | 11/11/2026                      > │ │
│ │ [paginação conforme contrato; sem produtos do catálogo geral]          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
Uma linha por produto acompanhado. C06 é wrapper do MFE sobre classes do kit.
```

### WF-03 — Detalhe acompanhado / Ficha técnica, desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR GLOBAL (HOST)                                                        │
│ [C01] Produtos acompanhados / 10080025                                       │
│ ┌────────────────────── [C02] HERO PRODUTO ───────────────────────────────┐ │
│ │ 10080025 — TERM. OLHAL M6...          [Versão acompanhada: V5]          │ │
│ │ Última conclusão PRC: 12/11/2026   [Ver solicitação de origem]          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ [C08 ● Ficha técnica] [C08 Versões]            [Selecionar versão: V5 ▾]   │
│ [faixa leve acompanhamento/legenda existente — sem card de flags]             │
│ ┌────────────── [C09/C10] Identificação e classificação ──────────────────┐ │
│ │ Código oficial                  Descrição [C12 ⚑]                       │ │
│ │ 10080025                        TERM. OLHAL...                           │ │
│ │ Grupo                           Tipo [C12 ⚑]                            │ │
│ │ 1008                            Matéria-prima                           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────── [C09/C10] Estoque e contabilidade ──────────────────┐ │
│ │ Armazém padrão                  Conta contábil [C12 ⚑]                  │ │
│ │ 01                              11401002                                │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ ┌────────────────────── [C09] Fornecedores ───────────────────────────────┐ │
│ │ Código | Loja | Razão social | Part Number [⚑] | Catálogo [⚑]         │ │
│ │ 000001 | 01   | FORN X       | PN-RT-1         | —                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
Cards largura 100%; grade interna 2 colunas [P]; gaps 12×16px [P].
Flag OPEN vermelha, RESOLVED verde, adicionar azul: [C12] fonte comprovada.
```

### WF-04 — Aba Versões + comparação, desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [C02] 10080025 — TERM. OLHAL...  [V5]                                       │
│ [C08 Ficha técnica] [C08 ● Versões]                                          │
│ ┌──────────────────────────── HISTÓRICO [C16] ────────────────────────────┐ │
│ │ V5 · 12/11 · Alteração · Solicitação #... · 2 campos alterados          │ │
│ │ [Ver ficha V5]                                                         │ │
│ │ V4 · 08/11 · Alteração · Solicitação #... · fornecedor atualizado       │ │
│ │ [Ver ficha V4]                                                         │ │
│ │ V3 · 03/11 · Alteração · Solicitação #... · descrição alterada          │ │
│ │ [Ver ficha V3]                                                         │ │
│ │ V2 · ...  V1 · primeiro acompanhamento (não implica criação TOTVS)      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────── COMPARAR VERSÕES ───────────────────────────────┐ │
│ │ [Versão de origem: V1 ▾] [Versão de destino: V5 ▾] [C05 Comparar]      │ │
│ │ Campo / vínculo        | ANTES (V1)         | DEPOIS (V5)              │ │
│ │ Descrição              | TERM. ...          | TERM. ... REV           │ │
│ │ Fornecedor 000001/01   | Não vinculado      | PN-RT-1                 │ │
│ │ ─── Eventos de flags (separados de alterações TOTVS) ────────────────  │ │
│ │ [C12] Flag criada em V3; resolvida após V4                            │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
Comparação entre quaisquer duas versões, não apenas adjacentes. Sem V2, botão
comparar desabilitado com explicação; não comparar contra TOTVS atual.
```

### WF-05 — Mobile 390px: entrada, lista e detalhe

```text
┌─────────────────────────── 390px ───────────────────────────┐
│ TOP BAR DO HOST (responsividade do Portal)                 │
│ [C01] Início / Controle...                                 │
│ ┌──────────────────── HERO [C02] ────────────────────────┐  │
│ │ CONTROLE E CADASTRO DE PRODUTOS                        │  │
│ │ [ SOLICITAÇÕES | PRODUTOS ] [C03]                      │  │
│ │ [Busca código/descrição                 ] [C04]        │  │
│ │ [Flags ▾] [Ordenação ▾]                               │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌────────────────── LISTA [C06] ─────────────────────────┐  │
│ │ 10080025 | TERM. OLHAL... | V5 | ⚑ 2                > │  │
│ │ 10080022 | TERM. OLHAL... | V1 | 0                  > │  │
│ │ (tabela scroll-x ou adaptação autorizada após teste)   │  │
│ └────────────────────────────────────────────────────────┘  │
├──────────────────── DETALHE MOBILE ─────────────────────────┤
│ [C02] 10080025 — TERM. OLHAL...                            │
│ [C08 Ficha técnica | Versões]                              │
│ [Versão: V5 ▾]                                             │
│ ┌───────────── IDENTIFICAÇÃO [C09] ─────────────────────┐   │
│ │ Código oficial                                       │   │
│ │ 10080025                                             │   │
│ │ Descrição [⚑]                                        │   │
│ │ TERM. OLHAL...                                       │   │
│ │ Tipo [⚑]                                             │   │
│ │ Matéria-prima                                        │   │
│ └───────────────────────────────────────────────────────┘   │
│ ┌──────────── FORNECEDORES [C09] ───────────────────────┐   │
│ │ ← rolar tabela horizontal →                          │   │
│ │ Código | Loja | Razão | Part Number | ...             │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
12px de margem externa [T]; grade ficha vira 1 coluna em <=640px [P].
```

### WF-06 — Modal de flag, desktop e celular

```text
DESKTOP: diálogo contido no host (C14; não cobre sidebar)
        ┌────────────── [C14] NOVA BANDEIRA ──────────────┐
        │ ⚑ Adicionar acompanhamento                       │
        │ ⚑ Aberto · ⚑ Resolvido (legenda)                │
        │ Campo: Conta contábil                            │
        │ Valor atual (contexto): 11401002                 │
        │ [Título                                    ]     │
        │ [Descrição                                ]     │
        │ [                                         ]     │
        │                            [Fechar] [Criar]      │
        └──────────────────────────────────────────────────┘

MOBILE 320–390px: modal limitado ao container host/viewport;
        ┌──────────── NOVA BANDEIRA ────────────┐
        │ Campo: Conta contábil                 │
        │ Valor: 11401002                       │
        │ [Título                              ] │
        │ [Descrição                           ] │
        │ [                                    ] │
        │ [Fechar]                   [Criar]     │
        └───────────────────────────────────────┘
Largura/altura e paddings internos = EngineeringHostDialog / Plugin UI;
não fixar números sem inspecionar ModalShell e testar no host.
```

### WF-07 — Tablet 768px: Versões e comparação

```text
┌────────────────────────────── 768px ──────────────────────────────┐
│ [C02] Produto 10080025 · V5                                       │
│ [C08 Ficha técnica | ● Versões]                                   │
│ ┌──────────────────────── HISTÓRICO ────────────────────────────┐ │
│ │ V5 · 12/11 · Alteração · [Ver ficha]                          │ │
│ │ V4 · 08/11 · Alteração · [Ver ficha]                          │ │
│ └───────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────── COMPARAÇÃO ───────────────────────────┐ │
│ │ [Origem V2 ▾] [Destino V5 ▾] [Comparar]                     │ │
│ │ Descrição                                                  │ │
│ │ Antes (V2): ...                                            │ │
│ │ Depois (V5): ...                                           │ │
│ │ Fornecedor 000001/01                                       │ │
│ │ Antes: ...                                                 │ │
│ │ Depois: ...                                                │ │
│ └───────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
Comparação em blocos empilhados no tablet/mobile [T], sem 3 colunas estreitas.
```

## 4. Especificação de estados e interações

| Área | Interação / estado | Componente e regra |
|---|---|---|
| Segmento principal | Clique/teclado alterna contexto; URL persistida, back/F5 | C03; não renderizar top bar extra |
| Busca | Debounce e filtros pelo contrato, limpar filtros | C04/C05; não misturar estado de solicitações com acompanhados |
| Tabela | Linha inteira clicável com teclado; loading/empty/error | C06/C15; somente acompanhados |
| Versão | Seletor atualiza snapshot completo e corte de flags | C08 + select do kit; histórico não é TOTVS live |
| Flag sem registro | Hover/foco/toque revela ação azul | C12; hit area 44×44 [T] |
| Flag OPEN | Vermelho e abrir registro existente | C12/C14; não duplicar |
| Flag RESOLVED | Verde; histórico e reabrir conforme autorização | C12/C14 |
| Fornecedor | Flag em atributo do vínculo `supplierCode+store` | C09/C12; não usar índice da linha |
| Flag histórica | Mostrar corte temporal; consulta atual em ação separada | C12/C14; mutação somente versão atual [TARGET a ratificar] |
| Modal | Fechar/Escape, foco preso, erros 403/409, preservar texto | C14/C15; AuthZ backend-first |
| Comparação | Selecionar Vx e Vy, diff só campos/vínculos alterados | C16/C11; não atribuir flags a mudança TOTVS |
| Mobile | Sem hover obrigatório; rolagem de tabela controlada | C06/C09/C12; teclado/toque testados |

## 5. Matriz de QA visual obrigatória para implementação futura

| Viewport | Lista solicitações | Lista acompanhados | Ficha | Versões | Modal |
|---|---|---|---|---|---|
| 1920×1080 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 1440×900 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 1280×800 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 1024×768 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 768×1024 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 430×932 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 390×844 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 360×800 | PENDING | PENDING | PENDING | PENDING | PENDING |
| 320×640 | PENDING | PENDING | PENDING | PENDING | PENDING |

Para cada viewport: screenshot desktop/mobile, light/dark, sem overflow do documento, foco/teclado/toque, flags OPEN/RESOLVED/ausentes, tabela fornecedor extensa, modal com texto longo, V1 isolada, V3 histórica, comparação V1×V5, erro 403/409, carregamento, F5/back. **PENDING = não testado**, não PASS.

## 6. Gates antes do desenvolvimento

1. Revalidar HEAD e exports remotos do Plugin UI e props reais de C01–C18; confirmar componentes em build Module Federation.
2. Inspecionar CSS fonte de PageHero, SegmentToggle, DetailCard, DataTableSection, UnderlineNav, HostDialog e tokens de spacing/radius/font; substituir dimensões TARGET por tokens PROVEN quando possível.
3. Confirmar contratos Engineering API para produtos acompanhados, snapshots, comparação e flags transversais; não adaptar provider `requestId` por suposição.
4. Fazer Abstraction Gate para apresentação de flags e supplier cell; se necessário, mover **somente componentes neutros** para Plugin UI e manter autorização/HTTP nos adapters de Engenharia.
5. Validar política de flags em versão histórica com owner; alterações de autoridade exigem `ARCHITECTURE_DECISION_REQUIRED`.
6. Executar matriz visual com navegador autenticado e evidência no SHA. Até lá: `TARGET_LAYOUT / TEST_NOT_RUN`.

**Não criar PR, migration, API ou deploy como parte deste documento.**
