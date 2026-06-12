# Plugin — Manutenção (MFE)

Microfrontend React do módulo **Manutenção** (`id`: `maintenance`) — Module Federation + Vite.

**Estado:** Fases 0–2 concluídas; submódulos com RBAC por filial, filial no início, CRUD completo, tabelas paginadas server-side e UX de reposição (jun/2026).

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/12-roadmap-e-evolucao/maintenance/README.md](../../docs/12-roadmap-e-evolucao/maintenance/README.md) | Produto, roadmap, playbook |
| [maintenance-api/docs/README.md](../../maintenance-api/docs/README.md) | API dedicada |

## Nomenclatura

| Campo | Valor |
|-------|-------|
| **Id técnico** (inglês) | `maintenance` |
| **Nome no portal** (português) | Manutenção |

## Resumo

| Item | Valor |
|------|-------|
| Manifesto | `maintenance.manifest.json` (v0.2.1) |
| `id` | `maintenance` |
| `name` | Manutenção |
| `basePath` | `/apps/maintenance` |
| API | `/apps/maintenance-api/maintenance` |
| Container (alvo) | `delpi-maintenance` |

## Primeira funcionalidade

**Mini-aplicadores** (ferramentaria) — reposição de peças, golpes e alertas preventivos. Migração do legado WinForms `MiniAplicadores`.

## Componentes de UI (canônicos)

| Módulo | Caminho | Uso |
|--------|---------|-----|
| `DataTableSection` | `src/components/data/DataTableSection.tsx` | Título, toolbar, tabela, paginação e ordenação |
| `DataTable` | `src/components/data/DataTable.tsx` | Cabeçalhos ordenáveis (↕ / ↑ / ↓) |
| `Pagination` | `src/components/data/Pagination.tsx` | Anterior · Página **N** de M · Próxima |
| `useServerTable` | `src/hooks/useServerTable.ts` | Estado de `page`, `page_size`, `sort_by`, `sort_dir` para API |
| `appendListQuery` | `src/utils/listQuery.ts` | Monta query string de listagem paginada (suporta arrays repetidos) |
| `MultiSelectField` | `src/components/data/MultiSelectField.tsx` | Filtro multi-valor (peça, motivo, status) |
| `BrDateInput` | `src/components/data/BrDateInput.tsx` | Data em pt-BR (`dd/mm/aaaa`); valor interno `YYYY-MM-DD` |
| `BrDatetimeInput` | `src/components/data/BrDatetimeInput.tsx` | Data/hora em pt-BR (`dd/mm/aaaa HH:mm`, 24h); valor interno `YYYY-MM-DDTHH:mm` |
| `datetimeLocal` | `src/utils/datetimeLocal.ts` | Conversão exibição pt-BR ↔ ISO para API |
| `ReposicoesGolpesChart` | `src/components/ReposicoesGolpesChart.tsx` | Gráfico de linha (golpes por reposição) no detalhe da ferramenta |
| `FerramentaReposicaoIndicadores` | `src/components/FerramentaReposicaoIndicadores.tsx` | KPIs de reposição ao lado do gráfico |
| `PreventivaDetailPanel` | `src/components/PreventivaDetailPanel.tsx` | Detalhe preventivo + gráficos Recharts |
| `pecaOptions` | `src/utils/pecaOptions.ts` | Rótulos de peça; prefixo canônico `3019` |

**Paginação server-side:** todas as tabelas do MFE usam `serverTable` + `DataTableSection.serverTable` (`page`, `page_size`, `sort_by`, `sort_dir` + filtros na API). Ao paginar ou ordenar, só a tabela entra em loading — a página não recarrega.

**Reposição (detalhe da ferramenta):**

- Formulário **colapsável** — botão **Nova reposição** no cabeçalho do histórico; edição de linha abre o formulário.
- Select de peça via `componentesToPecaOptions(estrutura)` — mesma árvore vigente de **Componentes e estoque**, filtrada para **`3019*`**.
- Tabela **Componentes e estoque** usa `GET .../componentes` — todos os itens amarrados à ferramenta (sem filtro 3019).
- Gráfico **Golpes por reposição** + indicadores (`FerramentaReposicaoIndicadores`) acima do histórico quando existir ao menos um cadastro.
- Datas do formulário em **pt-BR** (`BrDatetimeInput`); envio à API em ISO.

**Filtros (histórico e relatório):**

| Tela | Filtro | API |
|------|--------|-----|
| Histórico reposições | Peça, motivo (multi), De/Até | `codigo_peca`, `motivo_id`, `data_inicial`, `data_final` |
| Relatório preventivo | Status (multi) | `status` (repetido na query) |

**Datas pt-BR:** todos os campos de data/hora usam `BrDateInput` / `BrDatetimeInput` — exibição `dd/mm/aaaa` e `dd/mm/aaaa HH:mm` (24h); estado interno e query params permanecem em ISO (`YYYY-MM-DD` / `YYYY-MM-DDTHH:mm`).

**Erros HTTP:** `maintenanceApiBase.ts` propaga `message` ou `detail` do envelope FastAPI (ex.: 401/403 legíveis), em vez de «Falha na requisição» genérico.

**Filial na UI:** nome exibido vem do catálogo Postgres (`resolveFilialDisplayName`), não só o código `01`/`02`.

## Registro no portal

```bash
export TOKEN="<jwt com apps.manage>"
export BASE_URL="http://localhost"
chmod +x scripts/register-manifest.sh
./scripts/register-manifest.sh
```

Permissões canônicas (manifesto v0.2.1 — ver matriz completa em [OPERATIONS.md](../../docs/12-roadmap-e-evolucao/maintenance/OPERATIONS.md)):

| Permissão | Uso |
|-----------|-----|
| `maintenance.view` | Abrir o módulo |
| `maintenance.manage` | Cadastro de filiais (`/filiais`) |
| `maintenance.mini-applicators.view.filial-XX` | Ler mini-aplicadores na filial |
| `maintenance.mini-applicators.manage.filial-XX` | Reposições, motivos e status na filial |
| `maintenance.manutencao-geral.view.filial-01` | Submódulo manutenção geral (filial 01) |

## Desenvolvimento

```bash
npm install
npm run dev
npm run build
```

Variável opcional: `VITE_MAINTENANCE_API_BASE` (default: `/apps/maintenance-api/maintenance`).

## Integração HTTP

- **CRUD operacional** → API dedicada (JWT).
- **TOTVS** → **não** chamar api-delpi no browser; a API dedicada usa gateways (`DelpiApiClient`).

Ver [PLAYBOOK-01](../../docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md).

## Design

Seguir [plugins-visual-design-system](../../.cursor/rules/plugins-visual-design-system.mdc) — padrão de tabelas alinhado ao Transformômetro (`DataTableSection`, paginação, ordenação).
