# Documentação — Dashboard Qualidade

Plugin **microfrontend** (Module Federation) da Minha DELPI para indicadores de qualidade vindos do **TOTVS Protheus**, via **api-delpi**.

---

## 1. Visão geral

| Item | Valor |
|------|--------|
| ID do plugin | `dashboard-quality` |
| URL base | `/apps/dashboard-quality` |
| Container Docker | `delpi-dashboard-quality` |
| API backend | `/apps/api-delpi/quality/*` |
| Dados | TOTVS (PPM, NC analítica, Kaizen, auditoria 5S) |

O Portal carrega o `remoteEntry.js` e injeta o token Keycloak no cliente HTTP do plugin. O plugin **não** implementa login próprio.

### Escopo incluído

- Visão geral executiva (KPIs PPM, resumos Kaizen/5S, sparklines)
- PPM interno/externo (gráfico, tabela, comparativo, metas de referência)
- Não conformidades analíticas do Protheus
- Kaizens (gráficos e listagem)
- Auditoria 5S (gráficos e listagem)

### Fora de escopo

- Workflow de NC em PostgreSQL — módulo removido da api-delpi (jun/2026)
- Indicadores estratégicos (API `strategic-indicators-api`)

---

## 2. Rotas do plugin

| Rota | Página | Descrição |
|------|--------|-----------|
| `/apps/dashboard-quality` | `DashboardQualityPage` | Home com KPIs e atalhos |
| `/apps/dashboard-quality/ppm` | `PpmPage` | PPM detalhado, gráfico e export CSV |
| `/apps/dashboard-quality/nonconformities` | `NonconformitiesPage` | NC TOTVS, gráfico de devoluções |
| `/apps/dashboard-quality/perdas` | `PerdasPage` | Custo refugo/retrabalho × ROL + atalhos |
| `/apps/dashboard-quality/kaizen` | `KaizenPage` | Kaizens por período, status e setor |
| `/apps/dashboard-quality/audit-5s` | `Audit5sPage` | Notas 5S por período e área |

Rotas internas são resolvidas em `src/App.tsx` a partir do `pathname` recebido do Portal.

---

## 3. Permissões

O usuário precisa de **uma** das permissões:

| Permissão | Onde |
|-----------|------|
| `dashboard-quality.view` | Plugin (RBAC Core API) |
| `api-delpi.quality.access` | API legada (compatibilidade) |

Registro do manifesto: `scripts/register-manifest.sh`  
Homologação: conceder `dashboard-quality.view` ao perfil de Qualidade no admin RBAC.

---

## 4. Filtros globais

Filtros compartilhados entre todas as abas:

| Campo | Query URL | API |
|-------|-----------|-----|
| Data inicial | `date_start` (YYYY-MM-DD) | `date_start` |
| Data final | `date_end` | `date_end` |
| Filial | `branch` | `branch` |

### Persistência

1. **URL** — `writeFiltersToUrl` atualiza a query string (`replaceState`).
2. **sessionStorage** — chave `delpi.dashboard-quality.filters`; usada quando o Portal troca de rota sem repassar a query.
3. **Navegação entre abas** — `QualityNav` e `ModuleShortcut` preservam filtros via `appendFiltersToPath` / `navigateQuality`.

Implementação: `src/utils/filterUrl.ts`, `src/hooks/useQualityFilters.ts`, `src/utils/navigation.ts`.

### Filiais dinâmicas

`GET /quality/branches?date_start=&date_end=` popula o combo de filial conforme o período.

---

## 5. Impressão

Botão **Imprimir** em todas as páginas (header compartilhado).

### Comportamento

- `PrintReportButton` dispara `resize` e aplica a classe `dq-printing` no `<html>` antes de `window.print()`, para o Recharts recalcular dimensões.
- Na impressão aparece apenas `PrintReportSummary` (título, período, filial, data de emissão).
- O header da tela (nav, ícone, ações) fica oculto (`dq-screen-only`).

### CSS (`src/index.css`)

- `@media print` isola `.dq-print-root` (não imprime sidebar do Portal).
- Oculta filtros, paginação, toolbars, banners e estados de erro/carregamento.
- Gráficos com altura fixa (~220px) e cores preservadas (`print-color-adjust: exact`).

### Classes úteis

| Classe | Uso |
|--------|-----|
| `dq-print-root` | Raiz do conteúdo imprimível (em cada página) |
| `dq-print-only` | Visível só na impressão |
| `dq-screen-only` | Visível só na tela |
| `dq-no-print` | Oculto na impressão |

---

## 6. API consumida

Base no browser:

```text
/apps/api-delpi/quality
```

Envelope padrão:

```json
{ "success": true, "message": "...", "data": { } }
```

Detalhamento endpoint a endpoint: [API_MAPPING.md](./API_MAPPING.md).

Cliente tipado: `src/api/qualityApi.ts`  
Validação leve: `src/api/validateQualityResponse.ts`  
Erros amigáveis: `src/utils/formatQualityApiError.ts`

---

## 7. Variáveis de ambiente (build)

| Variável | Efeito |
|----------|--------|
| `VITE_DQ_PPM_TARGET` | Linha de meta no gráfico PPM |
| `VITE_DQ_PPM_LIMIT` | Linha de limite no gráfico PPM |

Valores padrão em `src/constants/ppmReferenceLines.ts`.

---

## 8. Estrutura do código

```text
src/
├── App.tsx                 # Roteamento interno por pathname
├── api/                    # HTTP e qualityApi
├── components/             # UI reutilizável (filtros, gráficos, impressão)
├── constants/              # rotas, cores, metas PPM
├── hooks/                  # filtros, dashboard, séries, queries
├── pages/                  # uma página por módulo
├── types/                  # DTOs TypeScript
└── utils/                  # datas, URL, agregação de gráficos, CSV
```

Árvore detalhada: [STRUCTURE.md](./STRUCTURE.md).

---

## 9. Desenvolvimento

### Pré-requisitos

- Node.js 20.19+ (ou 22.12+)
- npm

### Comandos

```bash
cd plugins/dashboard-quality
npm install
npm run dev          # standalone em dev
npm run ci           # lint + build
```

Na raiz do monorepo:

```bash
./scripts/ci/build-dashboard-quality.sh
```

### Stack local com Docker

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build \
  gateway core-api api-delpi dashboard-quality
```

UI: `http://localhost/apps/dashboard-quality`

Guia completo de testes: [TESTING.md](./TESTING.md).

---

## 10. Deploy em produção

1. Build da imagem `dashboard-quality` (ou CI do monorepo).
2. Subir/recriar o container `delpi-dashboard-quality`.
3. Se a **api-delpi** for recriada, reiniciar o **gateway** (Nginx re-resolve o upstream).
4. Garantir variáveis TOTVS/`QUALITY_*` no `.env` da api-delpi.

```bash
docker compose up -d --build dashboard-quality
docker compose restart gateway   # após recreate da api-delpi
```

Smoke test:

```bash
export TOKEN="<jwt>"
./scripts/homologacao/check-dashboard-quality.sh
```

---

## 11. Documentos relacionados

| Arquivo | Conteúdo |
|---------|----------|
| [API_MAPPING.md](./API_MAPPING.md) | Endpoints e parâmetros |
| [TESTING.md](./TESTING.md) | Checklist manual e homologação |
| [ROADMAP.md](./ROADMAP.md) | Fases 0–6 do produto |
| [IMPROVEMENTS_ROADMAP.md](./IMPROVEMENTS_ROADMAP.md) | Ondas de melhorias (UX, performance) |
| [STRUCTURE.md](./STRUCTURE.md) | Convenções de pastas |
| `api-delpi/docs/api/06-modulos-departamentais.md` | API Qualidade no backend |

---

## 12. Referências no monorepo

- Plugin espelho: `plugins/dashboard-lmps`
- Gateway: `gateway/nginx.conf` (`/apps/api-delpi/`, `/apps/dashboard-quality/`)
- Router backend: `api-delpi/app/interface/http/routes/quality/quality_router.py`
- Docs portal: `docs/05-plugin-system/microfrontends.md`
