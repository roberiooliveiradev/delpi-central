# Inteligência do chat — Onda 9: Apresentação Rica de Dados

**Status:** planejado (maio/2026)  
**Pré-requisitos:** [Onda 8](./inteligencia-chat-onda-8.md)

## Objetivo

Transformar as respostas do chat em **visualizações interativas e exportáveis** — tabelas, gráficos, cards, canvas — no estilo ChatGPT/Claude, permitindo que o usuário explore, baixe e compartilhe os dados retornados.

---

## Visão geral da arquitetura

```text
Backend (minha-delpi-ai-api)
  └─ Resposta com metadata.presentation
       { type: "table" | "chart" | "card" | "kpi" | "json",
         title, columns, rows, chartConfig, actions }

Frontend (minha-delpi-chat)
  └─ ChatMessageList detecta presentation e renderiza:
       ├─ ChatRichTable (tabela interativa + sort + filtro)
       ├─ ChatRichChart (gráfico via Recharts)
       ├─ ChatRichCard (card resumo / KPI)
       ├─ ChatRichCanvas (canvas expandível tipo ChatGPT)
       └─ ChatExportToolbar (download CSV/XLSX/PDF/PNG, copiar, imprimir)
```

---

## Fases de entrega

### Fase 1 — Tabelas Ricas (alta prioridade, impacto imediato)

| # | Entrega | Descrição |
|---|---------|-----------|
| 9.1.1 | `ChatRichTable` component | Tabela interativa com sort por coluna, highlight de linhas, scroll horizontal |
| 9.1.2 | Backend: formatar como `presentation.table` | Adaptar `ExternalActionResultPresenter` para emitir `ChatPresentation` nos tool calls de produto, estoque, LMP, OVs, SQL |
| 9.1.3 | Export CSV/XLSX | Botão de download que serializa os dados da tabela |
| 9.1.4 | Copiar tabela | Copiar como texto formatado ou markdown para clipboard |
| 9.1.5 | Conectar `chatPresentation.ts` | Ativar o extrator já existente na renderização de mensagens |

**Resultado esperado:**  
Perguntas como "estoque do 10080001" ou "lista as LMPs da semana" renderizam tabela interativa com botão de download.

---

### Fase 2 — Gráficos e Visualizações (médio prazo)

| # | Entrega | Descrição |
|---|---------|-----------|
| 9.2.1 | Instalar Recharts | Adicionar `recharts` ao plugin (leve, React-native, composable) |
| 9.2.2 | `ChatRichChart` component | Renderiza bar, line, pie, area charts a partir de `presentation.chart` |
| 9.2.3 | Backend: heurística de chart | Detectar quando dados tabulares fazem sentido como gráfico (séries temporais, comparações, distribuições) |
| 9.2.4 | Toggle tabela ↔ gráfico | Usuário alterna entre visualização tabular e gráfica |
| 9.2.5 | Export PNG/SVG | Download do gráfico como imagem |

**Resultado esperado:**  
"Giro de estoque dos últimos 6 meses" renderiza gráfico de barras + tabela alternável.

---

### Fase 3 — Cards e KPIs (médio prazo)

| # | Entrega | Descrição |
|---|---------|-----------|
| 9.3.1 | `ChatRichCard` component | Card compacto para indicadores (valor, label, tendência, ícone) |
| 9.3.2 | Layout multi-card | Grid de 2-4 cards lado a lado para dashboards inline |
| 9.3.3 | Backend: formato `kpi` | Presenter detecta respostas de indicadores e emite formato card |
| 9.3.4 | Sparklines em cards | Mini-gráficos de tendência dentro dos cards |

**Resultado esperado:**  
"Qual o CPV e OTD deste mês?" renderiza 2 cards lado a lado com valores e tendência.

---

### Fase 4 — Canvas Expandível (estilo ChatGPT)

| # | Entrega | Descrição |
|---|---------|-----------|
| 9.4.1 | Evoluir `ChatCanvas` existente | Expandir para suportar tabelas, gráficos e texto rico (não só markdown) |
| 9.4.2 | Canvas automático para dados grandes | Se a resposta tem > 10 linhas ou é multi-seção, abrir automaticamente em canvas lateral |
| 9.4.3 | Edição no canvas | Permitir filtrar/reordenar dados diretamente no canvas |
| 9.4.4 | Salvar como artifact | Persistir visualização como artifact da sessão |
| 9.4.5 | Compartilhar artifact | Gerar link público (read-only) para o artifact |

**Resultado esperado:**  
Respostas complexas (estrutura de produto, relatório SQL) abrem em painel lateral editável e exportável.

---

### Fase 5 — Export & Download (transversal a todas as fases)

| # | Entrega | Descrição |
|---|---------|-----------|
| 9.5.1 | `ChatExportToolbar` component | Toolbar unificada de export abaixo de cada visualização rica |
| 9.5.2 | Export CSV | Serializar tabela para CSV com BOM UTF-8 |
| 9.5.3 | Export XLSX | Gerar planilha Excel via `xlsx` (SheetJS) |
| 9.5.4 | Export PDF | Gerar PDF do conteúdo via `jsPDF` + `html2canvas` |
| 9.5.5 | Export PNG | Screenshot do gráfico/tabela |
| 9.5.6 | Copiar para clipboard | Markdown formatado ou texto plano |
| 9.5.7 | Imprimir | CSS de impressão otimizado (@media print) |
| 9.5.8 | Export conversa completa | Baixar toda a sessão como PDF ou markdown |

---

### Fase 6 — Sugestões adicionais (não mencionadas pelo usuário)

| # | Entrega | Descrição | Justificativa |
|---|---------|-----------|---------------|
| 9.6.1 | **Drill-down interativo** | Clicar em linha da tabela dispara follow-up automático ("detalhe do produto X") | Reduz fricção para explorar dados |
| 9.6.2 | **Formatação contextual** | Detectar tipos de dados (moeda, data, %, quantidade) e formatar automaticamente (R$ 1.234,56, 25/05/2026) | Legibilidade profissional |
| 9.6.3 | **Comparação lado a lado** | "Compare estoque do produto A e B" → tabela/gráfico comparativo | Cenário real de operação |
| 9.6.4 | **Favoritar respostas** | Pin/bookmark de respostas úteis para acesso rápido | Produtividade |
| 9.6.5 | **Templates de relatório** | Relatórios recorrentes pré-configurados ("resumo de estoque semanal") | Automação |
| 9.6.6 | **Dark mode para gráficos** | Respeitar tema do sistema nos charts | UX |
| 9.6.7 | **Acessibilidade (a11y)** | Descrições alt em gráficos, navegação por teclado em tabelas | Compliance |
| 9.6.8 | **Notificação de atualização** | "Os dados de estoque mudaram desde sua última consulta" | Dados sempre frescos |
| 9.6.9 | **Histórico de exports** | Lista de downloads recentes acessível pelo usuário | Rastreabilidade |
| 9.6.10 | **Resposta em linguagem natural + dados** | Combinar parágrafo explicativo + tabela/gráfico na mesma resposta | Melhor compreensão |

---

## Dependências técnicas

| Biblioteca | Uso | Peso estimado |
|---|---|---|
| `recharts` | Gráficos (bar, line, pie, area) | ~150 KB gzipped |
| `xlsx` (SheetJS) | Export Excel | ~90 KB gzipped |
| `jspdf` + `html2canvas` | Export PDF | ~200 KB gzipped |
| `file-saver` | Trigger de download | ~2 KB |

**Estratégia:** lazy import (code splitting) para não impactar o bundle inicial.

---

## Priorização sugerida

```text
Sprint 1 (1-2 semanas): Fase 1 (tabelas ricas) + 9.5.1/9.5.2/9.5.6 (export CSV + copiar)
Sprint 2 (1-2 semanas): Fase 2 (gráficos) + 9.5.5 (export PNG) + 9.6.2 (formatação)
Sprint 3 (1 semana):    Fase 3 (cards/KPIs) + 9.6.10 (texto + dados)
Sprint 4 (1-2 semanas): Fase 4 (canvas) + 9.5.3/9.5.4 (XLSX/PDF)
Sprint 5 (1 semana):    Fase 5 restante + 9.6.1 (drill-down) + 9.6.4 (favoritos)
Sprint 6 (contínuo):    Fase 6 demais itens (a11y, dark mode, templates)
```

---

## Estrutura de `ChatPresentation` (proposta expandida)

```typescript
type ChatPresentation =
  | { type: "table"; title: string; columns: Column[]; rows: Row[]; meta?: TableMeta }
  | { type: "chart"; title: string; chartType: "bar"|"line"|"pie"|"area"; data: ChartData[]; config?: ChartConfig }
  | { type: "kpi"; title: string; cards: KpiCard[] }
  | { type: "json"; title: string; data: unknown }
  | { type: "report"; title: string; sections: ReportSection[] };

type Column = { key: string; label: string; type?: "text"|"number"|"currency"|"date"|"percent"; align?: "left"|"center"|"right" };
type Row = Record<string, unknown>;
type TableMeta = { sortable?: boolean; filterable?: boolean; pageSize?: number; totalRows?: number };
type KpiCard = { label: string; value: string | number; unit?: string; trend?: "up"|"down"|"stable"; delta?: string };
type ChartData = Record<string, unknown>;
type ChartConfig = { xAxis?: string; yAxis?: string; colors?: string[]; legend?: boolean };
type ReportSection = { title?: string; content: string; presentation?: ChatPresentation };
```

---

## Critérios de aceite (Fase 1)

- [ ] Pergunta "estoque do 10080001" renderiza tabela com colunas (Filial, Armazém, Quantidade, Disponível)
- [ ] Tabela possui sort ao clicar no header
- [ ] Botão "Baixar CSV" gera arquivo `.csv` correto (UTF-8 BOM)
- [ ] Botão "Copiar" coloca tabela formatada no clipboard
- [ ] Respostas de "lista LMPs" e "ordens de venda" também renderizam tabela
- [ ] Dados JSON brutos ainda acessíveis em modo expandido (collapse)
- [ ] Performance: renderização < 100ms para tabelas de até 100 linhas
- [ ] Mobile: tabela com scroll horizontal e headers fixos

---

## Referências

- [ChatPresentation types](../../plugins/minha-delpi-chat/src/data/api/chatTypes.ts)
- [chatPresentation.ts (extrator)](../../plugins/minha-delpi-chat/src/ui/components/chatPresentation.ts)
- [ChatCanvas existente](../../plugins/minha-delpi-chat/src/ui/components/ChatCanvas.tsx)
- [ChatMarkdown](../../plugins/minha-delpi-chat/src/ui/components/ChatMarkdown.tsx)
- [Recharts docs](https://recharts.org/)
- [SheetJS docs](https://docs.sheetjs.com/)
