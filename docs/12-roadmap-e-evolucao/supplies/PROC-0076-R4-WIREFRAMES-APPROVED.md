# PROC-0076.R4 — Wireframes aprovados: Inteligência de Mercado

> **Status:** SPEC / APPROVED (direção visual aprovada pelo PO). Documental — nenhuma alteração de código, contrato ou runtime nesta execução.
> **Rota alvo:** `/apps/supplies/market-intelligence` (inalterada).
> **Baseline:** HEAD `8b9003f438` em 2026-10-26; página R3 já em produção (`feeea8e1b9`).
> **Hierarquia:** este wireframe prevalece como baseline funcional/visual aprovado, **subordinado** a segurança, acessibilidade, arquitetura, source rights e design tokens oficiais. Não aprova uso de dados LME nem libera feed não homologado.
> **Boundary inalterado:** `plugins/supplies` (render-only) → `supplies-api` (BFF) → `external-data-api` (dados/proveniência). CSS root `.dashboard-supplies-portal`.

## 0. Reconciliação R3 → R4

| Conceito | R3 (em produção) | R4 (wireframe aprovado) |
|---|---|---|
| Perspectivas | `ipp` · `comex` · `fx` | **Metais** · **Câmbio** · **Indicadores** |
| Seleção de série | um seletor por perspectiva | Metais = grade 3×2 de cards multi-seleção; demais perspectivas mantêm controles contextuais |
| Indicadores IPP/Comex | perspectivas próprias | agrupados sob **Indicadores** |
| Modos | Gráfico/Tabela | Gráfico · Tabela · **Comparação** |
| Frequência | granularity por série (day/month/year) | **Dia · Semana · Mês · Ano** (kit já tipa `week`; contrato BFF `MarketGranularity` não inclui `week` → gap registrado, Doc D) |

O restante da arquitetura R3 (URL state, default-deny, quarentena LME, resumos contextuais, estados honestos) é preservado.

## 1. Wireframe macro — desktop (~1440px)

```text
┌──────────────────────────────────────────────────────────────────┐
│ PORTAL SUPRIMENTOS                                               │
│                                                                  │
│ Inteligência de Mercado                                          │
│ Cotações, tendências e indicadores para Compras e Vendas         │
│                                                                  │
│ [        METAIS       |       CÂMBIO      |     INDICADORES     ] │
│                                                                  │
│ [ Cobre          ✓ ] [ Alumínio       ✓ ] [ Zinco             ] │
│ [ US$/t            ] [ US$/t           ] [ US$/t             ] │
│                                                                  │
│ [ Níquel           ] [ Chumbo           ] [ Estanho           ] │
│ [ US$/t            ] [ US$/t            ] [ US$/t             ] │
│                                                                  │
│ Frequência dos dados              [ Dia | Semana | Mês | Ano ]    │
│                                                                  │
│ [ Última referência ] [ Média do período ] [ Variação         ] │
│ [ valor / estado   ] [ valor / estado    ] [ valor / estado   ] │
│                                                                  │
│ [           Gráfico      |      Tabela      |    Comparação    ] │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Histórico de metais                                          │ │
│ │ Instrumentos selecionados: Cobre, Alumínio                   │ │
│ │                                                              │ │
│ │           GRÁFICO / TABELA / COMPARAÇÃO                       │ │
│ │                                                              │ │
│ │   Ou estado vazio sem observações autorizadas               │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Fonte • Metodologia • Cobertura • Última atualização • Ajuda    │
└──────────────────────────────────────────────────────────────────┘
```

Cadeia de composição (topo → rodapé):

```text
PagePath
  ↓
PageHero (título + descrição + ações + ajuda)
  ↓
PerspectiveSwitcher — Metais | Câmbio | Indicadores
  ↓
ContextControls (grade de metais OU controles de câmbio OU controles de indicadores)
  ↓
FrequencySwitcher — Dia | Semana | Mês | Ano
  ↓
KpiStrip — Última referência | Média do período | Variação (contextuais)
  ↓
ViewSwitcher — Gráfico | Tabela | Comparação
  ↓
AnalysisPanel — uma única superfície de visualização
  ↓
SourceFooter — Fonte • Metodologia • Cobertura • Última atualização • Ajuda
```

Regras de composição:

- **Uma perspectiva ativa por vez** — alternância no hero, sem reload de página.
- **Um único painel de análise** — Gráfico e Tabela são modos exclusivos; Comparação só quando houver contrato de comparação e séries compatíveis.
- **Sem empilhamento de módulos de fonte** — nada de três seções grandes sequenciais.
- **KPIs contextuais** — cada perspectiva/métrica tem sua própria faixa; nunca resumo de USD/BRL sob IPP, nunca KPI de índice sob metais.
- **Estados honestos** — indisponível/configuração pendente/sem dados são estados compactos explícitos, nunca gráfico vazio sem explicação.
- Nenhuma perspectiva renderiza "apenas escondida" (`display:none` com fetch ativo é proibido).

## 2. Perspectiva Metais

```text
┌────────────────────────────────────────────────────────┐
│ METAIS  (seleção múltipla)                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │ Cobre      [✓]│ │ Alumínio  [✓]│ │ Zinco       │    │
│ │ US$/t        │ │ US$/t        │ │ US$/t       │    │
│ │ (disponível) │ │ (disponível) │ │ (sem fonte) │    │
│ └──────────────┘ └──────────────┘ └──────────────┘    │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │ Níquel       │ │ Chumbo       │ │ Estanho     │    │
│ │ US$/t        │ │ US$/t        │ │ US$/t       │    │
│ └──────────────┘ └──────────────┘ └──────────────┘    │
└────────────────────────────────────────────────────────┘
```

Anatomia de cada card:

- **Nome do metal** (rótulo principal).
- **Unidade real da fonte homologada** (ex.: `US$/t`) — nunca unidade inventada.
- **Estado de seleção** — indicador visual (check/marca) + `aria-pressed`; operável por mouse, toque e teclado.
- **Estado de disponibilidade** — disponível / sem observações / fonte pendente (nota secundária `Fonte pendente` — refinamento R4.1: mantém o card selecionável com menor peso visual; o card **permanece selecionável** — D-04).
- **Fonte** quando comprovada (tooltip/rodapé do card).

**Gate de direitos (imutável, refinado por D-04):** o catálogo separa `selectable_in_ui` (presença do instrumento) de `data_access_allowed` (`display_allowed` da fonte). Cards listam todos os instrumentos do catálogo e **permanecem selecionáveis** mesmo sem fonte homologada — a seleção prepara a visualização e persiste na URL, mas nunca autoriza leitura de valores: o BFF responde `availability.unavailable_reason = "source_use_pending"` e nenhum ponto é retornado. Metais LME permanecem em quarentena — sem fonte homologada, a grade exibe os cards selecionáveis com nota secundária `Fonte pendente` (R4.1) e o painel mostra «Aguardando observações de fonte homologada». **Este documento não aprova LME.**

Comportamento por cardinalidade da seleção:

| Seleção | Painel |
|---|---|
| 0 metais | Estado vazio orientador ("selecione ao menos um metal"), sem fetch |
| 1 metal | Série única; KPIs do metal; Comparação habilitada em potencial (precisa de 2ª série compatível) |
| 2 metais | Multi-série no mesmo gráfico (mesma unidade/granularidade); Comparação habilitada |
| 3+ metais | Idem; legenda com rolagem/overflow do kit; densidade de cores respeitando paleta acessível |
| 6 metais | Idem; sem limite artificial além do catálogo |
| Metal sem dados | Permanece selecionável se fonte homologada; série contribui lacunas `null` e KPI indica `no_data` com motivo |
| Metal com série parcial | Gráfico mostra pontos reais + lacunas explícitas; cobertura indicada |
| Metal sem fonte homologada | Card **selecionável** com nota secundária `Fonte pendente` (R4.1; D-04); entra na URL como seleção visual; o fetch retorna `availability` sem pontos — nunca valores |

## 3. Perspectiva Câmbio

Mesma grade de composição; a área de cards de metais é substituída por controles contextuais:

```text
[ Par USD/BRL ]  [ Boletim: Fechamento | (tipos do contrato) ]
[ Cotação: Venda | Compra ]   Período […]   Frequência [Dia|Semana|Mês|Ano]
[ Última taxa ] [ Média do período ] [ Variação ]
[ Gráfico | Tabela | Comparação ]
```

- Par fixo `USD/BRL` enquanto for o único instrumento cambial do catálogo; outros pares entram como opção do mesmo controle quando homologados.
- Tipo de boletim e compra/venda conforme contrato vigente (`ptax_closing_sell`/`ptax_closing_buy`).
- Feed indisponível (WAF/egress) → estado `source_unavailable` compacto no lugar do painel, com `unavailable_reason` do BFF. Sem área em branco grande, sem sugestão de "ajustar filtros".

## 4. Perspectiva Indicadores

Agrupa os indicadores aprovados; cada indicador mantém unidade e metodologia próprias:

```text
[ Indicador: IPP Metalurgia — número-índice ▾ | IPP variação M/M-1 | Comex (NCM) ]
  IPP → série/variável + período
  Comex → NCM homologada + dimensões (país/UF quando houver) + período
[ Último índice | Variação no mês | Cobertura ]   (contextual ao indicador)
[ Gráfico | Tabela | Comparação ]
```

Separação semântica (obrigatória):

- IPP número-índice: **índice (dez/2018=100)**, nunca `%` nem moeda.
- IPP M/M-1: **%**, nunca misturado com o índice na mesma série.
- Comex: **FOB total, massa líquida, US$/t ponderado** — valor médio de importação, não preço internacional de metal.
- PTAX: **R$/US$** (vive na perspectiva Câmbio).
- Metais: **US$/t** (ou unidade real da fonte homologada futura).

"Outros indicadores" só entram quando aprovados — o seletor de indicador é alimentado pelo catálogo do BFF, nunca por lista fixa.

## 5. Frequência

Alternador `Dia | Semana | Mês | Ano`:

- Estado ativo: variante `--active` do segment toggle (accent).
- Hover/focus: ring/hover do kit (`delpi-ui` BEM).
- Disabled: opção sem suporte para a série (ex.: `day` para série mensal IPP) → opção desabilitada com tooltip explicando o motivo — **nunca fabricar observações diárias a partir de série mensal**.
- Unavailable: frequência teoricamente suportada mas sem dados na janela → selecionável, painel mostra `no_data` honesto.
- Mudança de frequência dispara nova consulta ao BFF e atualiza URL.
- Agregações semana/anual são responsabilidade do owner de dados (external-data-api/BFF) — o frontend não agrega.
- Granularidade diária é requisito mínimo para futuras fontes de metais; intradiário previsto na arquitetura, sem botão nesta versão.

## 6. KPIs

Faixa compacta com até 3–4 cards contextuais. Por perspectiva:

| Perspectiva | KPIs válidos | Proibido |
|---|---|---|
| Metais | Última referência (por metal selecionado ou do 1º selecionado com indicação), Média do período (metodologia do owner), Variação (início→fim), Cobertura | Valor sem fonte, média improvisada no React |
| Câmbio | Última taxa (tipo+data), Média do período, Variação, Cobertura | Números sem PTAX coletada |
| Indicadores — IPP índice | Último número-índice, Variação do período, Cobertura, Frescor | PTAX, "cotação de metal" |
| Indicadores — IPP M/M-1 | Última variação %, amplitude/média (se aprovada), Cobertura | Unidade BRL/US$ |
| Indicadores — Comex | Último FOB/t ponderado, FOB total, massa, Cobertura | Spot LME |

Cada KPI exibe: valor real **ou** estado explícito com motivo (`unavailable_reason`), unidade, competência/período de referência, proveniência e ajuda contextual. Sem `—` sem causa. O frontend nunca é autoridade de cálculo — todo valor vem de read model do BFF.

## 7. Modos de visualização

Alternador `Gráfico | Tabela | Comparação` sobre o painel único.

**Gráfico:** séries dos instrumentos selecionados; eixo Y com unidade explícita; legenda; tooltip com período+valor+unidade; lacunas como `null` (sem interpolar); cores da paleta acessível do kit; `incompleteBucketMode` para buckets parciais; exportação da série; responsivo (largura fluida, scroll horizontal mínimo em tabela, não em gráfico).

**Tabela:** mesma série do gráfico — colunas: período, valor, unidade, cobertura/qualidade, fonte/timestamp quando exposto; ordenação e paginação do kit; exportação coerente com filtro ativo.

**Comparação:** habilitado somente quando existirem ≥2 séries compatíveis (mesma unidade **e** granularidade) com contrato aprovado; caso contrário a opção fica `disabled` com explicação. Nunca normalizar índice vs % vs USD/t vs R$/US$ na mesma série sem metodologia.

## 8. Wireframe — tablet (~768px)

```text
┌────────────────────────────────────────┐
│ ‹ Inteligência de Mercado        [?]   │
│ [ Metais | Câmbio | Indicadores ]      │
│ [ Cobre ✓ ] [ Alumínio ✓ ] [ Zinco ]   │
│ [ Níquel  ] [ Chumbo    ] [ Estanho]   │   ← grade 3×1+3×1 (wrap do kit)
│ Freq [Dia|Sem|Mês|Ano]  Período […]    │
│ [Última] [Média] [Variação]            │
│ [Gráfico|Tabela|Compar.] [Exportar]    │
│        painel responsivo               │
└────────────────────────────────────────┘
```

- Grade de metais mantém 3 colunas enquanto couber; abaixo disso, wrap natural do grid.
- Alternadores permanecem horizontais (wrap de opção em `direction="row"`); se não couber, `size="sm"`.

## 9. Wireframe — mobile (~375px)

```text
┌──────────────────────────┐
│ ‹ Inteligência    [?]   │
│ [Metais|Câmbio|Indic.]   │
│ [Cobre ✓] [Alumínio ✓]  │   ← grade 2×N (grid auto-fit do kit)
│ [Zinco  ] [Níquel     ] │
│ [Chumbo ] [Estanho    ] │
│ Freq [Dia|Sem|Mês|Ano]   │
│ [Última] [Média][Var.]   │
│ [Gráfico|Tabela|Compar.] │
│      painel              │
│ [Estados/lacunas]        │
│ [Exportar ▾]             │
└──────────────────────────┘
```

- Touch targets ≥ 44px; foco visível; ordem de tabulação = ordem visual.
- Segment toggles com `direction="row"` e labels abreviáveis sem perder `ariaLabel` completo.
- Tabela usa modo de cards mobile do `DataTable` do kit (já existe — ver Doc B).
- Sem overflow horizontal indevido; gráfico usa `StableResponsiveContainer`.

## 10. Rodapé de fonte

Sempre visível no fim do painel:

```text
Fonte: <source_id oficial> • Metodologia: <method_version> • Cobertura: n/m períodos • Última atualização: <last_successful_at> • [Ajuda]
```

Comex inclui disclaimer: "valor médio FOB de importação ≠ preço internacional do metal".

## 11. Restrições permanentes (carregadas da R3)

- Nenhum preço artificial; ausência = `null` + motivo.
- `display_allowed === true` é a única condição de seleção; indisponível ≠ oculto (estado explicado).
- Sem permission nova; Core decide `supplies.access`; S2S BFF→producer inalterado.
- Sem escolha de provedor externo nesta versão — cards de metais são estrutura alimentada por catálogo.
