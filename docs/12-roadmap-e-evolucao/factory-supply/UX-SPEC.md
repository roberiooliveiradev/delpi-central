# Factory Supply — UX Specification (Documentation 3/5)

> **Status:** frontend + UX + screens + Kanban + plugin-ui — Documentation 3/5
> **Escopo:** especificação de experiência. **Não** cria React, CSS, rotas, manifest, endpoints ou permissões.
> **Baseline:** `README.md` (Doc 1/5) + `DOMAIN-MODEL.md` (Doc 2/5, com correção de grain aplicada).
> **Natureza:** documentação canônica. Nada aqui autoriza implementação.

---

## 1. Purpose / status

Define a experiência completa do Factory Supply antes de API e código: arquitetura de informação, jornadas por ator, telas, projeções Kanban, tabelas, cards, filtros, detalhe, workspaces por papel, responsividade, estados de loading/empty/error/forbidden, reuso do `@delpi/plugin-ui`, acessibilidade e a fronteira "UX derivada vs estado autoritativo".

Todo o conteúdo é `TARGET` salvo marcação explícita `PROVEN` (evidência de plugin-ui / Line Feeder / regras canônicas) ou `TO_DESIGN` / `TO_INVENTORY`.

## 2. UX principles

1. **Frontend é projeção + intenção** — nunca autoridade: estoque, empenho, transferência, consumo, fórmula de devolução, validade de transição, permissão, prioridade e reconciliação ERP são do backend. A UI apresenta dimensões e estágios derivados computados pelo backend e dispara comandos válidos; não re-decide regra.
2. **Ação semântica, não arrasto** — transição de coluna é evento operacional (comando + AuthZ + idempotência + auditoria).
3. **Duas verdades visíveis** — estado operacional e evidência ERP são visualmente distintos sempre que coabitam (§ 17).
4. **Desconhecido ≠ zero** — dado indisponível renderiza "Indisponível" / "Não informado" / "—", nunca `0` (`PROVEN`: padrão `unknown` e `optionalQty → "—"` do Line Feeder).
5. **Chão de fábrica primeiro** — execução otimizada para mobile e toque; densidade analítica vive no desktop.
6. **Kit antes de local** — todo chrome vem de `@delpi/plugin-ui`; zero CSS de componente do kit no MFE (`plugins-reusable-components.mdc`).

## 3. Actor journeys

### Production Operator (`TARGET` — integração futura)

Jornada no Cockpit do Operador, não necessariamente no MFE Factory Supply: "preciso de material" → solicitação semântica → acompanha status do pedido. No Factory Supply, o pedido aparece como `DemandSignal kind=operator_request` visível em Necessidades e na missão correlacionada (§ 29). Nenhuma tela do cockpit é desenhada aqui.

### Warehouse Operator

```text
Almoxarifado (fila de preparo)
→ filtrar por janela/destino/material
→ ver item: local de retirada, quantidade a preparar, prazo, missão
→ Iniciar preparação / Registrar preparado (parcial permitido)
→ item vira "Pronto para retirada"
→ handoff ao alimentador registrado na coleta
→ exceções visíveis (sem local, saldo insuficiente, remanejado)
```

### Factory Feeder

```text
Abastecimento → Kanban (o que está pronto / em coleta / próximo do prazo)
→ Minha coleta (execução: missão → item → local → quantidade → confirmar)
→ registrar coleta → handoff → entrega no CT (parcial por item)
→ Devoluções: o que precisa voltar
→ Histórico: rastro quando algo diverge
```

### PCP

Somente contexto — lê necessidades planejadas e status de atendimento nas superfícies de leitura; **não** recebe workspace genérico dentro do Factory Supply.

## 4. Information architecture

**Decisão: aceita com um refinamento** — "Minha coleta" é sub-modo de execução de "Abastecimento" (mesma audiência e dados; superfície dedicada por densidade cognitiva diferente), não workspace paralelo.

```text
Abastecimento Fabril
├── Visão geral              — resumo do que exige atenção agora
├── Abastecimento
│     ├── Kanban             — quadro operacional por missão
│     ├── Necessidades       — tabela analítica densa (needs + sinais)
│     ├── Minha coleta       — modo de execução do alimentador (mobile-first)
│     └── Próximos períodos  — necessidades futuras (próximo turno/dia)
├── Almoxarifado             — fila/workspace de preparo
├── Devoluções               — fila de retornos
└── Histórico                — rastreabilidade investigável
```

Cada superfície mapeia a uma query conceitual do Doc 2/5 § 26 (`GetOverviewSummary`, `GetSupplyBoard`, `GetSupplyNeeds`, `GetWarehousePreparationQueue`, `GetReturnQueue`, `GetOperationalHistory`, `GetMissionDetail`) — coerência com o modelo verificada.

## 5. Navigation

Nav interna via `UnderlineNav` ou rail próprio do app (padrão `PpcRail` `PROVEN` na referência). Seções = nível 1; subviews de Abastecimento = `SegmentToggle` (`PROVEN` no catálogo) ou tabs de nível 2. Filtros **read-only** persistem em URL (compartilhável); estado de escrita nunca em URL.

## 6. Visão geral

Responde "o que exige atenção agora?" — não é dashboard de vaidade. Cards são **contagens derivadas do backend** e navegáveis (clique abre a superfície já filtrada):

| Card | Derivação (backend) | Destino ao clicar |
|---|---|---|
| A preparar | itens `preparation=not_started` em missões open | Almoxarifado filtrado |
| Pronto p/ retirada | itens `prepared ∧ not_collected` | Kanban / Almoxarifado |
| Em coleta | itens `collected ∧ not_delivered` | Kanban |
| Próximos do prazo | `need_window` dentro do limiar (metadado backend) | Kanban filtrado |
| Em atraso | `now > need_window` e não entregue | Kanban filtrado |
| Devoluções pendentes | `return ∈ {requested, in_return}` | Devoluções |
| Exceções | itens com exceção ativa | Necessidades filtrado |

Limiar de "próximo do prazo" é política de backend (`TO_DESIGN`), não constante de UI. Métrica indisponível mostra estado, não `0`.

## 7. Supply Kanban

**`KANBAN = YES` · `KANBAN_CARD_GRAIN = MISSION`** — card = missão (destino × janela × contexto); itens aparecem como progresso, nunca como cards separados (preserva o grain corrigido e a execução multi-material).

Colunas são **projeção derivada** das dimensões (Doc 2/5 § 11) computada pelo backend — a UI não deriva nem persiste estágio:

| Coluna (PT-BR) | Derivação | Significa | Não significa |
|---|---|---|---|
| **A preparar** | `open` ∧ nenhum item com custódia iniciada | Trabalho decidido, separação pendente | Reserva ERP |
| **Em preparo** | ∃ item `preparation=in_progress` | Almoxarifado separando | Tudo separado |
| **Pronto p/ retirada** | ∃ item `prepared ∧ not_collected` | Há custódia a transferir | Toda a missão separada |
| **Em coleta** | ∃ item `collected ∧ not_delivered` | Em trânsito com o alimentador | Entregue; movimento ERP |
| **Entregue** | todo item `delivered` ∧ sem `return` ativo | Chegada operacional completa | Consumo; movimento ERP |

`closed`/`cancelled` saem do quadro por padrão (filtro "incluir encerradas" leva ao Histórico). Missão com itens em estágios diferentes posiciona-se no estágio **mais atrasado** ainda aberto (regra de derivação a congelar com o backend na Doc 4/5); o card mostra progresso por item para não esconder a mistura. Itens com `return` ativo aparecem com badge "com devolução" no card — não viram coluna do fluxo direto (devoluções vivem na superfície própria).

**Ações por card** (semânticas — menu/botões, nunca arrasto): Iniciar preparação · Registrar preparado · Registrar coleta · Registrar entrega · Solicitar devolução · Cancelar · Encerrar — apenas quando válidas e autorizadas pelo backend; caso contrário ausentes ou desabilitadas com razão.

**No card:** exceção (badge danger), evidência ERP (badge neutro distinto — § 17), progresso "n/n itens", saldo não medido (badge `unknown`).

## 8. Supply Mission card

Otimizado para leitura rápida no chão de fábrica:

```text
┌──────────────────────────────────────┐
│ CT-10                     janela 10:00│  ← destino + janela
│ MP-A · MP-B · MP-C          (3 itens) │  ← materiais (sem somar unidades)
│ ████░░      2/3 itens entregues       │  ← progresso por item
│ OP 12345 · op 10 · alimentador: J.R.  │  ← contexto + atribuição
│ ⚠ 1 exceção     evidência ERP: —      │  ← exceções + evidência separada
└──────────────────────────────────────┘
```

Nunca soma quantidades de unidades diferentes — progresso é **por item** ("2/3 itens"), não por quantidade. Urgência vem de metadado backend (§ 22). Mobile: mesmo card em largura total, sem ações dependentes de hover.

## 9. Supply Mission detail

**`MISSION_DETAIL = DRAWER`** — `DrawerShell` do kit (`PROVEN`): preserva o contexto do quadro, adequado a detalhe operacional denso e vira sheet em mobile. Deep-link (`?mission=<id>`) reabre o drawer — página cheia seria pesada; modal simples insuficiente para o volume.

Conteúdo (progressive disclosure):

```text
Cabeçalho: destino, janela, contexto (OP/op), atribuição, lifecycle
Itens:        cada SupplyMissionItem → § 10
Evidência ERP: correlações por item (localizada / não localizada / divergente)
Handoffs:     eventos de custódia (ator→ator, quando, quantidade)
Sinais:       demand signals correlacionados (planejado × pedido × antecipação — fatos separados)
Histórico:    trilha resumida + link para Histórico completo
Ações:        apenas as válidas+autorizadas pelo backend
```

## 10. Item presentation

Cada item expõe: código, descrição, unidade, local de retirada, contexto de estoque autoritativo quando disponível, e o ledger de quantidades:

```text
MP-A · Aço carbono 1020                        un: kg
Requerido 100 · Pedido 100 · A entregar 100
Preparado 80 · Coletado 70 · Entregue 60
[preparo: concluído] [coleta: concluída] [entrega: concluída]
[evidência ERP: não localizada]      [devolução: —]
Local de retirada: A-03-02
```

Regras: quantidade ausente → "—" / "Não informado"; saldo não medido → "Indisponível"; unidade sempre ao lado do número; exceções do item inline. `required` (autoritativo-derivado) e `requested` (sinal humano) são **rótulos distintos** quando ambos existem — um nunca substitui o outro.

## 11. Necessidades (tabela)

`DataTableSection` (`PROVEN`, padrão do Line Feeder). Tabela analítica densa — **não** é o Kanban:

| Papel | Colunas |
|---|---|
| Default | estágio derivado · janela · CT destino · material+descrição · unidade · requerido · preparado · entregue · sinal fonte · exceção |
| Opcionais | local de retirada · coletado · evidência ERP · OP · operação · atribuído a · devolução |
| Interações | busca por material/CT/OP; ordenação; `TableColumnVisibilityMenu` (`PROVEN`); row → drawer da missão; `Pagination`/`CompactPagination` (`PROVEN`) |
| Mobile | fallback card via `InteractiveDataCard` (`PROVEN` no Line Feeder) |

## 12. Minha coleta (execution mode)

**`MY_COLLECTION = SEPARATE_SURFACE`** — execução focada, mobile-first. Modelo mental: "o que eu pego agora, onde, quanto, para onde".

```text
Passo 1: escolher missão atribuída (lista curta: destino, janela, n itens)
Passo 2: fila de itens em ordem sugerida (backend)
   ┌──────────────────────────────────┐
   │ MP-B · Granalha 6mm              │
   │ Retirar em: A-01-14              │
   │ Quantidade: 50 un                │
   │ [ Registrar coleta ]             │  ← comando semântico, 44px+
   └──────────────────────────────────┘
Passo 3: progresso (itens coletados/total) → próximo item
Passo 4: entrega — Registrar entrega por item ou subconjunto
```

Pausa/retomada = reentrada natural (estado é do backend). Coleta multi-missão não é bloqueada pela UX, mas `collection_round` permanece **conceito de sessão UX** — não vira entidade persistida por causa desta tela (`TO_DESIGN` se a Doc 4/5 exigir contrato). Exceção no item aparece inline com ação orientada.

## 13. Próximos períodos

Visão de antecipação: necessidades planejadas da próxima janela/turno/dia — mesma tabela de Necessidades com filtro temporal ou seção dedicada. Distinção visual **obrigatória** entre sinais: badge `Planejado` (autoritativo/sistema) vs `Pedido do operador` vs `Antecipação do alimentador` — fatos diferentes, rótulos diferentes, nunca fundidos. Ações: apenas criar **intenção operacional** (sinal) se o contrato permitir; **nunca** muta planejamento ERP.

## 14. Almoxarifado workspace

**`WAREHOUSE_WORKSPACE = HYBRID`** — fila de trabalho (tabela) como visão primária + toggle para quadro por estágio derivado.

- **Fila (default):** `DataTableSection` de itens a preparar — material, local de retirada, quantidade a preparar, destino/CT, janela, missão, progresso, exceção. Ordenação default por janela (política backend).
- **Quadro (toggle):** `KanbanBoard` por estágio derivado de preparo — A preparar / Em separação / Pronto para retirada / Entregue ao alimentador. Aqui o grain do card é **item** (a execução do almoxarifado é por material), diferente do Kanban de abastecimento (missão).
- **Preparo em lote:** quando várias missões pedem o mesmo material, a fila agrupa por material **como view** — linha por item de missão dentro do grupo; a alocação por item permanece explícita (nunca funde quantidades perdendo rastreabilidade nem unidade).
- Escopo estrito: preparo para abastecimento fabril — **não** é WMS genérico.

## 15. Devoluções workspace

**`RETURNS_WORKSPACE = HYBRID`** — tabela default + quadro opcional por dimensão `return` (A recolher / Em retorno / Recebimento / Concluído — derivados).

Como `RETURN_QUANTITY_RULE = TO_INVENTORY`, a UI suporta ambos os casos sem inventar cálculo:

- quantidade esperada fornecida pelo backend → "Esperado: N";
- não estabelecida → "Quantidade a devolver: não estabelecida" (badge neutro), aceita registrar `returned_qty` factual;
- reconciliação rotulada como manual/declarativa enquanto a regra não existe.

Campos: CT origem, material, unidade, esperado?, devolvido, destino de retorno, estado de coleta/recebimento, evidência ERP. Destino não resolvido = exceção visível.

## 16. Histórico

Superfície de investigação com progressive disclosure (sem ruído técnico por default):

```text
Busca/filtros: missão · material · CT · OP · operação · ator · período · tipo de evento
Resultado: missões/eventos → timeline da missão
Timeline: necessidade (sinais, com origem) → decisão → preparo → coleta →
          handoffs → entrega → evidência ERP → devolução → encerramento
```

Cada entrada: ator autenticado + timestamp + transição + quantidade + reason (Doc 2/5 § 20). Detalhe técnico (ids, correlation refs) atrás de "ver detalhes".

## 17. ERP evidence semantics

Separação visual permanente: **verdade operacional** vs **evidência ERP**.

- Operacional: "Preparado", "Coletado", "Entregue" (verbos operacionais).
- ERP: "Movimento ERP localizado", "Movimento ERP não localizado", "Movimento ERP divergente" — badge variante `meta`/neutro + `HelpTooltip` explicando "evidência registrada no ERP; o sistema não executa a transferência".
- Status operacional **nunca** se apresenta como verdade ERP; ausência de movimento não é erro — é `not_found` factual.

## 18. Partial quantities

Representação por item como **sequência de valores rotulados**, nunca percentual único enganoso:

```text
Requerido 100 kg → Preparado 80 → Coletado 70 → Entregue 60   [faltam 40]
```

`InlineMeter` / `JourneyProgressBar` (`PROVEN` no catálogo) como reforço visual **por etapa**, sempre com números ao lado — nunca "60%" solto. Déficit residual = badge "pendente 40 kg"; fechamento parcial exige `reason` no comando com aviso; exceções visíveis no card e na tabela.

## 19. Exceptions

Exceção de negócio ≠ erro técnico — são estados com badge + texto + ação:

| Exceção | Renderização |
|---|---|
| Estoque insuficiente | badge warning "saldo insuficiente" + disponível visto |
| Saldo desconhecido | badge neutro "saldo não medido" (`unknown` ≠ 0) |
| Local ausente | badge "sem local de retirada" |
| Empenho indisponível | `StateBanner` "não foi possível calcular a necessidade" (degradação honesta, `PROVEN`) |
| Remanejado | badge "replanejado" + janela nova vs anterior |
| Parciais (preparo/coleta/entrega) | números + badge "parcial" |
| Movimento ERP não correlacionado | badge neutro — § 17 |
| Devolução: qty desconhecida / destino não resolvido | badges dedicados (§ 15) |
| Permissão negada | § 28 |
| Conflito de concorrência | § 20 |

Erro técnico (5xx/rede) usa `StateBanner`/`InfoStatePanel` com retry; exceção de negócio nunca vira banner genérico de erro.

## 20. Concurrency / stale UX

Conflito de `expected_version` retornado pelo backend → a UI:

1. explica que o trabalho mudou ("esta missão foi atualizada por outra pessoa");
2. recarrega e reapresenta o estado autoritativo;
3. preserva input local não enviado quando seguro, sem reaplicá-lo cegamente;
4. exige reavaliação humana da ação;
5. **não** faz retry automático de transições materiais — só o que a semântica de idempotência permitir.

## 21. Filters

Por superfície, sem barra universal:

| Superfície | Filtros |
|---|---|
| Kanban | filial · janela · CT · atribuído · exceção · sinal |
| Necessidades | filial · estágio · janela · CT · material · sinal · evidência ERP |
| Minha coleta | missões atribuídas a mim (implícito) |
| Almoxarifado | filial · janela · material · CT · estágio de preparo |
| Devoluções | filial · estado de retorno · CT · material |
| Histórico | filial · material · CT · OP · ator · período · tipo de evento |

Componentes: `FiltersRow`/`FilterBarShell` + `MultiSelectField`/`SelectField`/`DateField` (`PROVEN`).

## 22. Priority presentation

`PRIORITY_POLICY = TO_DESIGN` — o frontend **não** computa score. Backend fornece ordenação + banda opcional (`Atrasado` / `Agora` / `Próximo` / `Depois` derivados de `need_window` vs `now`). A UI renderiza a banda como badge e respeita a ordenação recebida; ordenação manual de cards nunca é prioridade.

## 23. plugin-ui reuse matrix

Catálogo inspecionado em `plugins/plugin-ui/src/components/**` (`PROVEN` — todos os itens existem no pacote):

| Necessidade UX | Componente | Classificação |
|---|---|---|
| Quadro Kanban | `KanbanBoard` / `createDashboardKanbanBoard` — **read-only, sem drag-and-drop** (docblock explícito) | `PLUGIN_UI_REUSE` |
| Card de missão / item / fallback mobile | `InteractiveDataCard` / `createDashboardInteractiveDataCard` | `PLUGIN_UI_REUSE` (conteúdo de domínio nos campos) |
| Tabela densa | `DataTableSection` + `TableColumnVisibilityMenu` + `Pagination` / `CompactPagination` | `PLUGIN_UI_REUSE` |
| KPIs da visão geral | `DelpiKpiCard` / `SimpleKpiCard` / `createDashboardKpiCard` | `PLUGIN_UI_REUSE` |
| Badges estado/sinal/ERP | `StatusBadge` / `createDashboardStatusBadge` (labels do backend) | `PLUGIN_UI_REUSE` |
| Loading | `LoadingActivityCard` / `createDashboardLoadingActivityCard`, `ScreenLoading`, `InlineLoadingProgress` | `PLUGIN_UI_REUSE` |
| Vazio / estado | `EmptyState`, `EmptyGuidance`, `SoftEmptyState`, `StateBanner`, `InfoStatePanel`, `StateBox` | `PLUGIN_UI_REUSE` |
| Filtros | `FiltersRow`, `FilterBarShell`, `MultiSelectField`, `SelectField`, `DateField`, `RangeField`, `FilterCheckboxField` | `PLUGIN_UI_REUSE` |
| Drawer de detalhe | `DrawerShell` | `PLUGIN_UI_REUSE` |
| Confirmação / reason | `ConfirmModalPanel`, `ModalShell`, `ModalFrame` | `PLUGIN_UI_REUSE` |
| Detalhe de campos | `DetailFieldGrid`, `DetailCard` | `PLUGIN_UI_REUSE` |
| Progresso por etapa | `InlineMeter`, `JourneyProgressBar`, `ProgressTracker` | `PLUGIN_UI_REUSE` |
| Timeline de histórico | `Timeline` (layouts `linear` vertical + `tree`, tones, timestamps) | `PLUGIN_UI_REUSE` |
| Seletor de estágio (mobile Kanban) | `SegmentToggle` | `PLUGIN_UI_REUSE` |
| Fila de trabalho | `WorklistItem`, `TaskWorklistSection` (candidato Almoxarifado/Minha coleta) | `PLUGIN_UI_REUSE` |
| Entrada de quantidade | `NumberStepperControl`, `ComboboxNumberControl`, `NativeFormFields`, `FormFieldShell` | `PLUGIN_UI_REUSE` |
| Ajuda contextual | `HelpTooltip`, `KeyTip`, `FieldLabel`, `TabHintCell`, `HintAction` | `PLUGIN_UI_REUSE` |
| Navegação | `UnderlineNav`, `InlineNavLink`, `BackLink` | `PLUGIN_UI_REUSE` |
| Chrome de página | `PageHero`/`TopBar*`, `SectionCard`, `ContentCard`, `SectionBlock` | `PLUGIN_UI_REUSE` |
| Card de missão (composição completa) | composição de `InteractiveDataCard` + badges + meter | `DOMAIN_SPECIFIC_LOCAL_UI` só no conteúdo de domínio |

## 24. plugin-ui extension gaps

**`PLUGIN_UI_EXTENSION_REQUIRED = NO`** — a inspeção do catálogo cobriu todos os chrome necessários, inclusive os dois candidatos esperados (timeline vertical → `Timeline`; seletor de estágio → `SegmentToggle`).

Um candidato permanece `TO_DESIGN` (não bloqueia): trilho de quantidades encadeadas (requerido→preparado→coletado→entregue+residual) — provável composição de `InlineMeter`+rótulos; se virar padrão em 2+ plugins, extrai-se ao kit conforme o gate de `plugins-reusable-components.mdc`. **Nenhuma** cópia local de chrome do kit será criada.

## 25. Responsive behavior

Breakpoints canônicos (`plugins-visual-design-system.mdc`): `>1100px` completo · `≤1100px` colunas reduzidas · `≤768px` mobile coluna única.

| Superfície | Desktop | Tablet | Mobile |
|---|---|---|---|
| Visão geral | grid de KPIs | 2 colunas | 1 coluna |
| Kanban | board multi-coluna | colunas reduzidas/scroll horizontal intencional | **`SegmentToggle` por estágio + lista vertical de cards** (`MOBILE_KANBAN = STAGE_SELECTOR`) |
| Necessidades | `DataTableSection` | colunas essenciais | `InteractiveDataCard` fallback |
| Minha coleta | 2 colunas (fila + atual) | 1 coluna | fluxo em passos, botões 44px+ — superfície **mobile-first** |
| Almoxarifado | fila + quadro toggle | fila | fila→cards |
| Devoluções | tabela + quadro toggle | tabela | cards |
| Histórico | filtros + tabela + timeline | tabela | cards + timeline vertical |
| Detalhe missão | `DrawerShell` lateral | drawer | sheet full-width |

Kanban mobile **não** encolhe o board — estágio selecionado + cards verticais. Nenhuma ação crítica depende de hover.

## 26. Accessibility

- Navegação por teclado completa; ordem de foco segue a hierarquia visual.
- `aria-label` no board (`KanbanBoard` já emite `role="region"` + `aria-labelledby` por coluna — `PROVEN`).
- Estado nunca só por cor: badge sempre com texto (`PROVEN`: dot de inventário no card de referência é `aria-hidden` com texto ao lado).
- Ações rotuladas por verbo ("Registrar coleta", não "OK").
- Tabela com semântica real (`DataTableSection` do kit); cards como alternativa declaram `ariaLabel`.
- Drawer/modal com focus trap, `Esc` fecha, foco restaurado ao gatilho (`DrawerShell`/`ModalShell`).
- Alvos de toque ≥44×44px; `prefers-reduced-motion` respeitado (transições opcionais).
- Ícones `lucide-react` com `aria-hidden` quando decorativos.

## 27. Loading / empty / error / forbidden

| Estado | Componente / comportamento |
|---|---|
| Loading inicial | `LoadingActivityCard`/`ScreenLoading` por seção |
| Refresh | `InlineLoadingProgress`/`LoadingActivityBadge`; dado anterior permanece (sem flash) |
| Vazio | `EmptyGuidance`/`SoftEmptyState` com orientação ("nenhuma missão nesta janela") |
| Filtrado-vazio | empty state com reset de filtros |
| Downstream parcial | `StateBanner` degradado honesto ("saldos indisponíveis — necessidades sem cobertura calculada"), dados válidos permanecem (`PROVEN` padrão do Line Feeder) |
| Erro técnico | `StateBanner`/`InfoStatePanel` + retry explícito |
| Forbidden | § 28 |

Nunca tela em branco; nunca spinner sem contexto.

## 28. Authorization UX

- Frontend pode esconder/desabilitar ações para UX — **backend é a autoridade final**.
- Ação não autorizada: ausente ou desabilitada com razão legível; nenhum fallback perigoso; sem vazar dados não autorizados (filial que o usuário não vê simplesmente não aparece — `PROVEN`: repositório filtra tudo por `branch`).
- Nomes de permissão: **não inventados** — `AUTHZ_TO_DESIGN` (Doc 4/5). A UI consome capabilities declaradas pelo backend (`can_*`/lista de ações elegíveis no payload) em vez de hardcodar perfis.

## 29. Operator Cockpit future interaction

Conceito apenas. Ação do operador: **"Solicitar matéria-prima"** — usando o contexto corrente do cockpit (OP/operação/CT pré-preenchidos de fonte autoritativa), quantidade pedida + unidade + janela, mínimo de digitação. O pedido renderiza para o operador como status do sinal (`pendente → em atendimento → atendido`), distinguindo **quantidade pedida** de **quantidade planejada**. No Factory Supply: sinais `operator_request` aparecem na Necessidades e no detalhe da missão com origem "Operador". Integração é semântica (contrato), nunca acoplamento a internals do cockpit.

## 30. Wireframes

### 30.1 Visão geral

```text
┌ Abastecimento Fabril ───────────────────────────────────────────────┐
│ [Visão geral][Abastecimento][Almoxarifado][Devoluções][Histórico]      │
├──────────────────────────────────────────────────────────────────────┤
│ [A preparar: 8] [Pronto p/ retirada: 5] [Em coleta: 3]                 │
│ [Próximos do prazo: 4] [Em atraso: 2] [Devoluções: 2] [Exceções: 3]    │
│ ── Atenção agora ────────────────────────────────────────────────     │
│ ▸ CT-10 missão das 10:00 · 1 item sem local de retirada     [abrir]    │
│ ▸ CT-04 entrega parcial · faltam 20 kg de MP-C              [abrir]    │
│ ▸ 2 devoluções aguardando destino                           [abrir]    │
└──────────────────────────────────────────────────────────────────────┘
mobile: cards empilhados → "atenção agora" em lista única
```

### 30.2 Abastecimento — Kanban

```text
┌ Abastecimento ─ Kanban ──────────────────────────────────────────────┐
│ [Kanban][Necessidades][Minha coleta][Próximos períodos]  [filtros ▾]   │
├──────────────┬──────────────┬──────────────┬───────────┬──────────────┤
│ A preparar 3 │ Em preparo 2 │ Pronto p/    │ Em coleta │ Entregue hoje  │
│              │              │ retirada 4   │ 3         │ 6              │
│ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │ ┌───────┐ │ ┌───────────┐ │
│ │CT-10     │ │ │CT-04     │ │ │CT-07     │ │ │CT-10  │ │ │CT-02      │ │
│ │10:00     │ │ │10:30     │ │ │11:00     │ │ │10:00  │ │ │09:00      │ │
│ │3 itens   │ │ │2 itens   │ │ │4 itens   │ │ │3 itens│ │ │2 itens    │ │
│ │⚠1 exc.   │ │ │░░░ 1/2   │ │ │⚠1 exc.   │ │ │░ 2/3  │ │ │✓ completa │ │
│ └──────────┘ │ └──────────┘ │ └──────────┘ │ └───────┘ │ └───────────┘ │
│ ┌──────────┐ │              │ ┌──────────┐ │           │               │
│ │CT-12     │ │              │ │CT-09     │ │           │               │
│ └──────────┘ │              │ └──────────┘ │           │               │
└──────────────┴──────────────┴──────────────┴───────────┴──────────────┘
mobile: [A preparar ▾] → lista vertical de cards
```

### 30.3 Abastecimento — Necessidades

```text
┌ Necessidades ─────────────────────────────────────────────────────────┐
│ 🔍 buscar…   filial▾ estágio▾ janela▾ CT▾ sinal▾ ERP▾   colunas⚙        │
├────────────────────────────────────────────────────────────────────────┤
│ estágio    │ janela │ CT   │ material        │ un │ req. │ prep.│ entreg│
│ A preparar │ 10:00  │ CT-10│ MP-A aço 1020   │ kg │ 100  │ 0    │ 0     │
│ Em preparo │ 10:30  │ CT-04│ MP-C granalha   │ un │ 50   │ 30   │ 0     │
│ …          │        │      │                 │    │      │      │       │
│ sinal: 🗓 planejado · 🙋 operador · ⏩ antecipação  (legenda de origem)   │
├────────────────────────────────────────────────────────────────────────┤
│ ◀ 1 2 3 … ▹                                            50 por página    │
└────────────────────────────────────────────────────────────────────────┘
vazio: "nenhuma necessidade neste corte" + reset de filtros
mobile: cards (InteractiveDataCard)
```

### 30.4 Minha coleta

```text
┌ Minha coleta ──────────────────────────────────────────────────────────┐
│ Missão: CT-10 · janela 10:00 · 3 itens        progresso ▓▓░ 1/3         │
├────────────────────────────────────────────────────────────────────────┤
│ ✔ MP-A · aço 1020        coletado 100 kg  · A-03-02                     │
│ ▸ MP-B · granalha 6mm                                                   │
│   Retirar em: A-01-14                                                   │
│   Quantidade: [ 50 ] un                [ Registrar coleta ]             │
│   ⚠ local de retirada não cadastrado → ver alternativas                 │
│ ○ MP-C · óleo lub.        aguardando preparo (bloqueado)                │
├────────────────────────────────────────────────────────────────────────┤
│ Entrega: quando coletado → [ Registrar entrega no CT-10 ]               │
└────────────────────────────────────────────────────────────────────────┘
mobile-first: um item por tela, alvos 44px+, sem hover
```

### 30.5 Próximos períodos

```text
┌ Próximos períodos ─────────────────────────────────────────────────────┐
│ período: ( ) próximo turno ( ) amanhã ( ) próximos 7 dias    filial▾     │
├────────────────────────────────────────────────────────────────────────┤
│ janela │ CT   │ material      │ sinal        │ req. │ ação               │
│ 14:00  │ CT-03│ MP-X …        │ 🗓 planejado │ 200  │ [antecipar preparo]│
│ 14:00  │ CT-03│ MP-Y …        │ 🗓 planejado │  40  │ [antecipar preparo]│
│ 16:30  │ CT-11│ MP-Z …        │ ⏩ alimentador│ 15  │                    │
│ nota: antecipação cria intenção operacional — não altera o ERP          │
└────────────────────────────────────────────────────────────────────────┘
```

### 30.6 Almoxarifado

```text
┌ Almoxarifado ───────────────────────────────────────────────────────────┐
│ [Fila][Quadro]   filial▾ janela▾ material▾ CT▾ estágio▾                  │
├────────────────────────────────────────────────────────────────────────┤
│ FILA — agrupada por material ▾                                          │
│ ▾ MP-A aço 1020 (3 missões)                                             │
│   → CT-10 10:00 · preparar 100 kg · local A-03-02 · missão #…  [iniciar] │
│   → CT-04 10:30 · preparar  60 kg · local A-03-02 · missão #…  [iniciar] │
│ ▸ MP-C granalha (1 missão)                                              │
├─ QUADRO (toggle) ───────────────────────────────────────────────────────┤
│ A preparar │ Em separação │ Pronto p/ retirada │ Entregue ao alimentador │
│ (cards por ITEM de missão, mesma ação semântica)                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 30.7 Devoluções

```text
┌ Devoluções ─────────────────────────────────────────────────────────────┐
│ filial▾ estado▾ CT▾ material▾                                           │
├────────────────────────────────────────────────────────────────────────┤
│ CT origem│ material   │ un │ esperado  │ devolvido│ estado   │ destino  │
│ CT-10    │ MP-A aço   │ kg │ não estabel│ 20      │ a recolher│ pendente│
│ CT-07    │ MP-C granal│ un │ 15        │ 15      │ recebido  │ A-01-14 │
│ ⚠ "não estabelecido" = regra de quantidade ainda não definida (backend) │
└────────────────────────────────────────────────────────────────────────┘
```

### 30.8 Histórico

```text
┌ Histórico ──────────────────────────────────────────────────────────────┐
│ 🔍 missão/material/CT/OP   ator▾ período▾ evento▾                        │
├────────────────────────────────────────────────────────────────────────┤
│ Missão CT-10 10:00 · MP-A/MP-B/MP-C                            [timeline]│
│   08:30 🙋 operador pediu MP-A 100 kg (sinal)                            │
│   08:35 🗓 necessidade planejada 10:00 registrada (sinal)                │
│   08:40 missão criada por sistema/ator — 3 itens                         │
│   08:55 preparo iniciado (M.S.) → 09:20 preparado 80 kg parcial          │
│   09:42 coleta registrada (J.R.) handoff almox→alimentador               │
│   09:58 entrega operacional CT-10 (J.R.) 60 kg — pendente 40             │
│   10:15 evidência ERP: não localizada                                    │
│ ▸ detalhes técnicos (ids, correlações)                                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 30.9 Supply Mission detail (drawer)

```text
┌─ Drawer (direita) ─────────────────────────────────────────────────────┐
│ Missão · CT-10 · janela 10:00                lifecycle: open           │
│ OP 12345 op 10 · alimentador J.R. · filial 01                          │
│ ações elegíveis: [Registrar entrega] [Encerrar c/ motivo]              │
├────────────────────────────────────────────────────────────────────────┤
│ Itens (3)                                                              │
│  MP-A aço 1020 — kg                                                    │
│   req 100 · pedido 100 · prep 80 · colet 70 · entregue 60   [parcial]  │
│   preparo✓ coleta✓ entrega✓  ERP: não localizada  devolução: —         │
│  MP-B …  MP-C …                                                        │
│ Sinais: 🗓 planejado 10:00 · 🙋 operador 08:30 · ⏩ antecipação         │
│ Handoffs: almox→alim 09:42 (M.S.→J.R.) 70kg · alim→CT 09:58 (J.R.)60kg │
│ Histórico (resumo) → abrir no Histórico                                │
└────────────────────────────────────────────────────────────────────────┘
```

### 30.10 Item detail / operational trace

Coberto dentro do drawer da missão (seção por item + trilha filtrada do item). Não exige tela própria — `TO_DESIGN` se a densidade futura justificar página dedicada.

## 31. Route concepts

`ROUTE_CONCEPT` — não são rotas de runtime; Doc 4/5 reconcilia com API e manifest:

```text
/apps/factory-supply                 → Visão geral
/apps/factory-supply/supply          → Abastecimento (Kanban default; ?view=needs|collection|upcoming)
/apps/factory-supply/supply/needs    → Necessidades
/apps/factory-supply/supply/collection → Minha coleta
/apps/factory-supply/supply/upcoming → Próximos períodos
/apps/factory-supply/warehouse       → Almoxarifado
/apps/factory-supply/returns         → Devoluções
/apps/factory-supply/history         → Histórico
/apps/factory-supply?mission=<id>    → deep-link abre drawer (ou ?mission= em qualquer superfície)
```

Base path segue convenção de manifest existente (`/apps/{plugin}` — `PROVEN` no production-control).

## 32. UX vocabulary

| Termo PT-BR | Uso |
|---|---|
| Abastecimento Fabril | nome do produto |
| Missão | unidade de trabalho (SupplyMission) |
| Material | item/materia-prima |
| Necessidade | demanda calculada/sinalizada |
| Preparação | separação no almoxarifado |
| Pronto para retirada | preparado aguardando coleta |
| Coleta | retirada pelo alimentador |
| Entrega | chegada operacional no CT |
| Devolução | retorno produção→almoxarifado |
| Evidência ERP | observação de movimento oficial (nunca "transferência feita pelo sistema") |
| Exceção | estado de negócio que exige atenção (não erro técnico) |
| Sinal | origem da necessidade (planejado/operador/antecipação/PCP) |

Evita jargão ERP cru ("SD4", "empenho") em labels de operação — "necessidade" e "saldo" em vez de nomes de tabela; conceitos autoritativos mantêm nome correto quando citados ("movimento ERP").

## 33. Decisions frozen

| Decisão | Valor |
|---|---|
| Information architecture | Visão geral · Abastecimento (Kanban/Necessidades/Minha coleta/Próximos períodos) · Almoxarifado · Devoluções · Histórico |
| `KANBAN` | YES |
| `KANBAN_CARD_GRAIN` | MISSION (itens = progresso; Almoxarifado usa cards por item na sua fila/quadro) |
| `DRAG_AND_DROP` | DISABLED — `KanbanBoard` é read-only (`PROVEN`); transições são comandos semânticos |
| `MY_COLLECTION` | SEPARATE_SURFACE (execução, mobile-first) |
| `WAREHOUSE_WORKSPACE` | HYBRID (fila default + quadro toggle) |
| `RETURNS_WORKSPACE` | HYBRID (tabela default + quadro toggle) |
| `MISSION_DETAIL` | DRAWER (`DrawerShell`) + deep-link `?mission=` |
| `MOBILE_KANBAN` | STAGE_SELECTOR (`SegmentToggle` + lista vertical) |
| `TABLE_VIEW` | YES (Necessidades/Almoxarifado/Devoluções/Histórico) |
| `PLUGIN_UI_EXTENSION_REQUIRED` | NO — catálogo cobre tudo; trilho de quantidades encadeadas fica `TO_DESIGN` |
| Estágio Kanban | derivado pelo backend, nunca estado persistido nem derivado no MFE |
| Desconhecido | "Indisponível"/"Não informado" — nunca `0` |
| Prioridade | banda/ordem do backend; UI não inventa score |

## 34. Decisions NOT frozen

- Derivação exata do estágio da missão com itens mistos (regra "mais atrasado aberto" é candidata — congelar com o backend na Doc 4/5).
- `collection_round` como contrato persistido (hoje: conceito de sessão UX).
- Limiar "próximo do prazo" e bandas de prioridade finais (`PRIORITY_POLICY`).
- Se devolução avulsa (sem item/missão) terá superfície dedicada.
- Página de item/trace dedicada se a densidade crescer (hoje: dentro do drawer).
- Nomes de rotas finais (conceitos § 31; manifest na fase de implementação).
- Catálogo de permissões → visibilidade de ações (`AUTHZ_TO_DESIGN`).

## 35. TO_INVENTORY

| Item | Bloqueia |
|---|---|
| `RETURN_QUANTITY_RULE` | rótulo/validação da quantidade esperada de devolução |
| `PRIORITY_POLICY` + limiares | bandas de urgência e ordenação default |
| Catálogo de permissões por ator | quais ações cada superfície mostra |
| API de `Timeline`/`InlineMeter`/`JourneyProgressBar` (props exatas) | seleção final do componente de progresso/histórico |
| Contrato de capabilities no payload (`can_*`) | como a UI decide exibir/esconder ações |
| Exposição backend do estágio derivado por missão | posição da coluna Kanban |

## 36. Inputs for Documentation 4/5

- Catálogo de comandos/ações por superfície (§ 7–15) → endpoints + métodos.
- Payloads esperados por query (`GetSupplyBoard` com estágio derivado + progresso por item; `GetMissionDetail` completo com sinais/handoffs/evidência; `GetWarehousePreparationQueue` com agrupamento por material preservando itens).
- Campo `version`/expected-state em payloads de leitura para suportar § 20.
- Capabilities/ações elegíveis no payload (`can_*`) para autorização declarativa (§ 28).
- `Idempotency-Key` ou equivalente nos comandos de mutação (Doc 2/5 § 19) + dedup keys.
- Bandas/ordenação de prioridade fornecidas pelo backend (§ 22).
- Labels PT-BR servidos por content/backend (padrão `setting_map` `PROVEN` do Line Feeder) — MFE não hardcode semântica de estado.
- Rotas frontend (§ 31) a reconciliar com manifest na implementação.

---

## Referências

- Doc 1/5: `docs/12-roadmap-e-evolucao/factory-supply/README.md`
- Doc 2/5: `docs/12-roadmap-e-evolucao/factory-supply/DOMAIN-MODEL.md`
- Catálogo plugin-ui inspecionado: `plugins/plugin-ui/src/components/` (`data/KanbanBoard.tsx`, `data/Timeline.tsx`, `data/DataTableSection.tsx`, `data/InlineMeter.tsx`, `feedback/*`, `forms/SegmentToggle.tsx`, `forms/MultiSelectField.tsx`, `layout/FiltersRow.tsx`, `layout/DetailFieldGrid.tsx`, `layout/SimpleKpiCard.tsx`, `feedback/DrawerShell.tsx`, `feedback/ModalShell.tsx`…)
- Referência UX: `plugins/production-control/src/pages/LineFeederPage.tsx`, `src/components/LineFeederRequirementCard.tsx`, `src/components/LineFeederPickPlanPanel.tsx`, `src/components/LineFeederProductDetailModal.tsx`
- Regras canônicas: `platform-frontend-mfe-experience`, `plugins-reusable-components`, `plugins-visual-design-system`, `plugins-overlay-positioning`, `platform-security-identity-authorization`, `mfe-own-api-no-direct-api-delpi`, `application-bounded-context-decoupling`, `evidence-driven-execution`
