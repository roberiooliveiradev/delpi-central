# Plugin — Manutenção (MFE)

Microfrontend React do módulo **Manutenção** (`id`: `maintenance`) — Module Federation + Vite.

**Estado:** Fases 0–2 concluídas; submódulos com RBAC por filial, filial no início, CRUD completo e tabelas paginadas/ordenáveis (jun/2026).

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
| `useClientPagination` | `src/hooks/useClientPagination.ts` | Paginação client-side (default 20 linhas) |
| `sortRows` | `src/utils/dataTableSort.ts` | Ordenação por coluna (`sortValue` ou texto renderizado) |
| `PreventivaDetailPanel` | `src/components/PreventivaDetailPanel.tsx` | Detalhe preventivo + gráficos Recharts |

**Paginação server-side:** lista de ferramentas (`fetchFerramentas` com `page` / `page_size`). Demais tabelas usam paginação client-side sobre o conjunto já carregado.

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
