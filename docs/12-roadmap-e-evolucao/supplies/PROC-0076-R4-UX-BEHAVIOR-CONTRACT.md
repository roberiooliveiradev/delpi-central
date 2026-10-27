# PROC-0076.R4 — Contrato de comportamento UX: Inteligência de Mercado

> **Status:** SPEC — congela interações, estados, URL, acessibilidade e regras de dados para a implementação R4. Documental; nenhum runtime alterado.
> **Baseline verificada:** HEAD `8b9003f438`; contrato URL R3 vigente em `plugins/supplies/src/features/market-intelligence/marketIntelligenceUrl.ts`.

## 1. Interações

### 1.1 Alternador de perspectiva (Metais | Câmbio | Indicadores)

- Troca sem reload: atualiza estado + `history.replaceState` (param `view`), re-renderiza somente a subárvore da perspectiva.
- Sem fetch das perspectivas inativas; aborta requisições pendentes da perspectiva anterior (corrida de requisições: última seleção vence, respostas atrasadas são descartadas).
- Opção indisponível pode permanecer clicável apenas para abrir painel de diagnóstico compacto — nunca fingir dados.
- Teclado: setas/espaço conforme padrão toggle do kit; `aria-pressed`/equivalente na opção ativa.

### 1.2 Cards de metais (seleção múltipla)

- Toggle por click/toque/Enter/Espaço; estado `selected` persistido na URL (`metals=cu,al,…`).
- Card de metal sem fonte homologada: **permanece selecionável** com nota secundária `Fonte pendente` (R4.1; D-04 — `selectable_in_ui` ≠ `data_access_allowed`); entra na URL como seleção visual e o fetch retorna `availability` sem pontos — nunca valores.
- Mudança de seleção refaz KPIs + painel; Comparação reabilita quando ≥2 séries compatíveis.
- Nenhum metal selecionado → painel orientador, sem chamada à API.

### 1.3 Frequência (Dia | Semana | Mês | Ano)

- Opção sem suporte para a série ativa → `disabled` + tooltip (ex.: IPP é mensal → `Dia`/`Semana` disabled).
- Mudança → nova consulta BFF + atualização de URL (`freq`/`granularity` — nomenclatura final na Doc D).
- Nunca fabricar observações diárias de série mensal; lacunas aparecem como `null`.

### 1.4 Modo de visualização (Gráfico | Tabela | Comparação)

- Persistido na URL (`mode`); um modo ativo por vez.
- Comparação `disabled` quando não houver contrato de comparação ou séries compatíveis — tooltip explica.
- Exportações seguem o modo e os filtros ativos.

### 1.5 Filtros contextuais

- Metais: seleção de metais (cards), frequência, período.
- Câmbio: tipo de boletim (fechamento), compra/venda, período, frequência.
- Indicadores: indicador/série (IPP índice, IPP M/M-1, NCM Comex quando homologada), período.
- Filtro sem efeito na métrica ativa não é renderizado (ex.: nunca seletor de moeda BRL sob IPP).

## 2. Estados visuais — mensagens PT-BR, ações, aparência

| Estado | Quando | Mensagem (PT-BR, diretriz) | Ações | Visual |
|---|---|---|---|---|
| `loading` | fetch em andamento | "Carregando…" | — | `SuppliesLoadingCard`/skeleton da aba ativa; conteúdo anterior persiste enquanto a troca não completa |
| `empty_no_selection` | metais sem seleção | "Selecione ao menos um metal para visualizar." | — | `SuppliesInlineEmptyState` compacto |
| `no_data` | fonte ok, zero observações na janela | "Nenhuma observação no período selecionado." + períodos faltantes | Ajustar período | `SuppliesEmptyState` no painel |
| `partial` | janela com lacunas | "Dados parciais: X de Y competências. Períodos sem dado: …" | — | `SuppliesStateBanner` default + gráfico com lacunas (sem ligar pontos) |
| `source_unavailable` | feed OFF/falha de provedor (ex.: PTAX 403 egress) | "Integração temporariamente indisponível — não é erro de filtro." | Recarregar | Painel compacto + `unavailable_reason` do BFF |
| `source_not_configured` | Comex sem NCM homologada | "NCMs de referência não homologadas para este Portal." | Entenda o indicador | Estado de configuração, sem gráfico vazio |
| `source_rights_pending` | metal sem `display_allowed` (quarentena LME) | "Aguardando observações de fonte homologada." | Sobre a fonte | Card **selecionável** (D-04) com nota secundária `Fonte pendente` (R4.1); painel explica sem inventar preço |
| `source_delayed` | `freshness.status` atrasado vs cadência | "Publicação oficial atrasada — última competência: …" | — | Banner warning + dados até a última competência real |
| `error` | falha HTTP/inesperada | "Não foi possível carregar a fonte." | Tentar novamente | `SuppliesStateBanner` variant `error` |
| `unauthorized` (401/403 Core) | sessão/permissão | "Sem autorização para usar Inteligência de Mercado." | — | Estado de acesso; nenhum dado |
| `timeout` (504) | upstream lento | "Tempo esgotado ao consultar a fonte." | Tentar novamente | Banner error + retry |
| `stale` | dados dentro da janela mas freshness degradado | "Última atualização: … (há N dias)" | — | Banner default + dados |
| `selected` | card/toggle ativo | — | — | `--active` BEM + accent token |
| `disabled` | opção inaplicável | tooltip com motivo | — | opacidade/disabled do kit |

Regras: nunca `—` sem causa exibida; `partial` só quando a métrica ativa depende da parte faltante (ausência de PTAX não degrada IPP); sem dados simulados em produção — em ambiente algum.

## 3. URL e navegação

Base inalterada: `/apps/supplies/market-intelligence`.

| Param | Valores | Evolução R3→R4 |
|---|---|---|
| `view` | `metals` \| `fx` \| `indicators` | Novos valores (R3 usava `ipp`/`comex`/`fx`); compat: `ipp`→`indicators`(+série), `comex`→`indicators`(+ncm), `fx`→`fx`; `instrument=usd-brl` → `fx` (legado já mapeado) |
| `metals` | lista CSV de instrument codes selecionados | Novo — códigos fora do catálogo são descartados na leitura; códigos sem `data_access_allowed` persistem como seleção visual (D-04) |
| `mode` | `chart` \| `table` \| `compare` | `compare` novo; inválido → fallback `chart` |
| `freq` (ou `granularity`) | `day` \| `week` \| `month` \| `year` | `week` depende do contrato BFF (gap Doc D) |
| `from`, `to` | ISO `YYYY-MM-DD` | Inalterado |
| `fx_kind` | `ptax_closing_sell` \| `ptax_closing_buy` | Inalterado |
| `ncm`, `ipp_series` | códigos do catálogo | Inalterado; `ipp_series` fica sob `indicators` |

Comportamentos: leitura **allowlist-validada** — parâmetro fora do contrato é ignorado (nunca repassado upstream); F5/back-forward restauram visão completa; favoritos funcionam pelo deep link; seleção de metal quarentenado na URL persiste como seleção visual (D-04) e o painel exibe `source_rights_pending` — códigos desconhecidos são descartados na validação de catálogo; links R2/R3 seguem resolvendo pela tabela de compat acima.

## 4. Acessibilidade

- Todos os alternadores: `ariaLabel` de grupo (obrigatório no kit) + opção ativa anunciada; navegação por teclado nativa do `SegmentToggle`.
- Cards de metais: `aria-pressed` + `ariaLabel` completo ("Cobre, US$/t, selecionado"/"sem fonte homologada"); foco visível; ≥44px touch target.
- KPIs: `role="group"`/`aria-label` via `MetricStrip` ou grid; valores nulos anunciados com motivo textual.
- Estados: `role="status"` nos banners; mudança de perspectiva anuncia região (aria-live discreto no painel).
- Tabela: cabeçalhos com `scope`, ordenação anunciada, foco navegável; modo mobile = cards (kit).
- Gráfico: resumo textual acessível (tabela alternativa já cobre leitores); tooltip também por foco/teclado quando o kit expuser.
- Contraste: tokens oficiais garantem ≥4.5:1 em texto e ≥3:1 em indicadores; sem cor como único canal de seleção (check + borda + aria).
- `prefers-reduced-motion`: o kit já respeita; nenhuma animação custom.
- Modo escuro: tokens `--sp-*`/`--delpi-ui-*` já possuem par dark oficial (ver §tokens).

## 5. Regras de dados (MFE render-only)

- Todo valor exibido vem do BFF: `value`, `unit`, `reference_period`, `metric_kind`, `data_status`, `coverage`, `freshness`, `unavailable_reason`, `source_id`, `method_version`.
- Frontend não calcula médias, variações, conversões nem agregações — nunca.
- Ausência = `null` + motivo; zero artificial é proibido.
- `observation_timestamp` (data da observação) ≠ `retrieved_at` (coleta) ≠ `reference_period` (competência) — o footer exibe `last_successful_at` e a competência real.
- Independência de provedor: a UI consome catálogo BFF; nenhum nome de provider hardcoded como fonte de verdade de disponibilidade.

## 6. Tokens (fonte canônica)

Definidos em `plugins/supplies/src/index.css` (escopo `.dashboard-supplies-portal`), encadeando `--delpi-ui-*` → `--sp-*` → tokens globais do Portal:

| Papel | Claro | Escuro |
|---|---|---|
| Canvas | `--bg`/`--app-canvas` + gradiente accent 5% | idem (globals dark) |
| Superfície | `--surface` (#fff) → `--sp-surface` | `color-mix(--surface-2 #1b2030 82%, black)` |
| Superfície elevada/soft/muted | `--sp-surface-elevated/soft/muted` (`--surface-muted #f6f8fa`) | mixes dark oficiais |
| Acento/ação | `--primary` (#089bdb) → `--sp-accent`/`--delpi-ui-accent` | `--primary` (inalterado) |
| Título/brand | `--secundary` (#003866) → `--sp-brand` | `--primary` (navy não é tinta no dark) |
| Valor de KPI | `--delpi-ui-title` = brand (claro) | `--delpi-ui-title` = texto branco |
| Texto/muted | `--text` / `--text-muted` | rgba branco .94/.78 |
| Borda | `--border` (#e6e6e6) | rgba branco .14 |
| Danger/success/warning | `--danger #b42318`, `--success #067647`, `--sp-warning #b54708` | `#f87171`, `#4ade80`, `#fdba74` |
| Espaçamento | `--sp-page-padding 24px`, `--sp-section-gap 24px`, `--sp-grid-gap 16px` | idem |

Selecionado/hover/focus/disabled vem dos componentes (`--delpi-ui-*`): estado ativo = `--active` com accent; qualquer cor ilustrativa do protótipo deve ser substituída por esses tokens — **proibido hex arbitrário no código da feature**.

## 7. Responsividade

Breakpoints reais do kit (não inventar): `max-width: 480/640/720/768/900/1024/1100px` em `plugin-ui/src/styles/*.css` — predominância `768px` (mobile) e `~900–1100px` (tablet/densidade).

| Faixa | Adaptação |
|---|---|
| Desktop (>1024) | grade metais 3×2; alternadores horizontais; 3 KPIs; painel amplo |
| Tablet (641–1024) | grade wrap 3→2 colunas; filtros em `FiltersRow` wrap; KPIs mantêm 3 ou wrap 2+1 |
| Mobile (≤640) | grade 2×N; alternadores com labels abreviadas + `ariaLabel` completo; KPIs compactos; tabela vira cards (kit); export em menu; sem overflow horizontal |

## 8. Dados — separação de semântica (inviolável)

- Índice IPP ≠ variação % ≠ USD/t ≠ R$/US$ — nunca na mesma série nem comparados sem metodologia.
- Comex FOB/t é valor médio de importação — disclaimer permanente no footer.
- Metais exibem unidade real da fonte homologada; sem fonte = sem preço, sem estimativa.
