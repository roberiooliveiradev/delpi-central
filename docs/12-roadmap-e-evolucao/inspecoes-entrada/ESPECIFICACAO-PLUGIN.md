# Especificação funcional — Plugin Inspeções de Entrada (estado atual)

> **Versão do plugin:** `0.1.0` (manifesto)  
> **Última revisão:** 2026-06-18  
> **Escopo:** comportamento implementado em `plugins/inspecoes-entrada` + rotas `api-delpi/inspecoes-entrada/*`.

---

## 1. Visão geral

Painel no Portal (**Minha DELPI**) para acompanhamento de inspeções de **entrada de materiais** (recebimento), separado por filial:

- **Visão geral:** KPIs, gargalos por fornecedor, produtos rejeitados, tabela de pendências;
- **Histórico:** consulta auditável com filtros, paginação e detalhe de ensaios;
- **Certificado:** impressão a partir do detalhe de inspeções concluídas.

**URLs:**

| Filial | Path |
|--------|------|
| 01 (SC) | `/apps/inspecoes-entrada/filial-01` |
| 02 (ES) | `/apps/inspecoes-entrada/filial-02` |

**Permissões:** `inspecoes-entrada.view.filial-01|02`, `inspecoes-entrada.view` ou legado `api-delpi.access`.

---

## 2. Arquitetura de dados no frontend

```text
Abertura / Atualizar (header)
  → Promise.all([
       GET .../resumo,
       GET .../pendentes?page=1&page_size=200,
       GET .../pendentes-fornecedor,
       GET .../rejeitadas-produto?limit=50
     ])

Aba Histórico
  → GET .../historico?branch&filtros&page&page_size
  → clique linha → GET .../historico/detalhe?inspection_id
```

Cada bloco do dashboard mantém estado independente (`loading` / `error` / `data`) — falha em um bloco não impede os demais.

---

## 3. Abas e navegação

| Aba | URL | Comportamento |
|-----|-----|---------------|
| Visão geral | path base | KPIs + analíticos + pendências |
| Histórico | `?tab=historico` | Filtros + tabela |

Troca de aba atualiza URL via `history.replaceState` (`syncTabInUrl`). Filial derivada do path (`filial-01` → `branch=01`).

---

## 4. Visão geral — componentes

### 4.1 Cards KPI (`SummaryCards`)

| Card | Campo API | Formato |
|------|-----------|---------|
| Pendentes | `pending_inspections` | Inteiro |
| Inspecionados | `inspected` | Inteiro |
| Taxa aprovação | `approval_rate` | Percentual |
| Tempo médio | `average_time_days` / `average_time_hours` | Dias (primário) |

### 4.2 Gargalos por fornecedor (`SupplierPendingList`)

Lista `items[]` de `/pendentes-fornecedor` com `supplier_name` e `pending_count`. Exibe total agregado `total_pending`.

### 4.3 Produtos rejeitados (`RejectedProductsList`)

Top N (`limit=50`) de `/rejeitadas-produto`: produto, fornecedor, NF, data laudo, lote.

### 4.4 Pendências (`PendingInspectionsTable`)

Primeira página com até **200** registros de `/pendentes`. Colunas: recebimento, NF, fornecedor, produto, quantidade, status inspeção.

Badge de status via `inspectionStatusBadge.ts`.

---

## 5. Histórico

### 5.1 Filtros (`HistoricoFilterBar`)

| Filtro | Param API | Observação |
|--------|-----------|------------|
| Filial | `branch` | Bloqueada quando rota `/filial-XX` |
| Resultado | `result` | `APROVADA`, `REJEITADA` ou todos |
| Data laudo (de/até) | `date_from`, `date_to` | ISO date |
| Fornecedor | `supplier` | Parcial |
| Código produto | `product_code` | Exato |
| Ensaiador | `inspector` | Parcial |
| Nota fiscal | `invoice_number` | Exato |
| Lote | `lot` | Exato |

Alteração de filtro reseta página para 1.

### 5.2 Tabela (`HistoricoTable`)

Colunas principais: datas recebimento/laudo, NF, fornecedor, produto, resultado, ensaiador, ações (ver detalhe).

Badge de resultado via `resultBadge.ts`.

### 5.3 Paginação

Opções de `page_size` configuradas no hook (`pageSizeOptions`). Controles em `Pagination.tsx`.

---

## 6. Detalhe da inspeção (`HistoricoDetailModal`)

Carregamento lazy ao abrir modal.

**Seções:**

1. **Resumo** — cabeçalho laudo (NF, fornecedor, produto, quantidades aprovada/rejeitada, ensaiador, justificativa)
2. **Ensaios** — cards por teste (`InspecaoTestCard`): especificação, medição, resultado, amostra
3. **Totais** — contagem aprovados/reprovados nos ensaios

**Ações:**

- Fechar (Esc ou overlay)
- **Imprimir certificado** — `printQualityCertificate()` (HTML print-friendly)

---

## 7. Header (`AppHeader`)

- Título com filial
- Abas Visão geral / Histórico
- Botão **Atualizar** (dispara reload da aba ativa)
- Timestamp última atualização (Visão geral)

---

## 8. Regras de negócio (UI)

| Regra | Detalhe |
|-------|---------|
| Filial na rota | Path `/filial-XX` fixa filial; histórico embedded não permite trocar filial |
| Resultado histórico | Valores canônicos `APROVADA` / `REJEITADA` (validados na API) |
| Medição ensaio | Exibição usa `measured_value` consolidado pela API (QES > QEQ) |
| Certificado | Disponível quando detalhe carregado; erro amigável se popup bloqueado |
| Quantidade pendente | Parse decimal com vírgula normalizado no use case backend |

---

## 9. Fora de escopo v0.1

- Painel de rejeitadas por ensaiador (rota API existe)
- Edição de laudo / ensaio
- Filtro por período na visão geral (apenas histórico)
- Gráficos temporais (Recharts)
- Notificações

---

## 10. Referências de código

| Área | Caminho |
|------|---------|
| Shell | `src/pages/FilialAppPage.tsx` |
| Dashboard | `src/pages/DashboardPage.tsx` |
| Histórico | `src/pages/HistoricoPage.tsx` |
| API client | `src/api/inspecoesEntradaApi.ts` |
| Estilos | `src/index.css` |
