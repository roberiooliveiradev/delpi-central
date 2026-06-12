# Plugin — Manutenção (MFE)

Microfrontend React do módulo **Manutenção** (`id`: `maintenance`) — Module Federation + Vite.

**Estado:** Fase 0 — manifesto rascunho e documentação; scaffold Vite na próxima entrega.

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
| Manifesto | `maintenance.manifest.json` |
| `id` | `maintenance` |
| `name` | Manutenção |
| `basePath` | `/apps/maintenance` |
| API | `/apps/maintenance-api/maintenance` |
| Container (alvo) | `delpi-maintenance` |

## Primeira funcionalidade

**Mini-aplicadores** (ferramentaria) — reposição de peças, golpes e alertas preventivos. Migração do legado WinForms `MiniAplicadores`.

## Desenvolvimento (quando scaffold existir)

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

Seguir [plugins-visual-design-system](../../.cursor/rules/plugins-visual-design-system.mdc) — copiar esqueleto de `plugins/dashboard-production` ou `plugins/transformometro`.
