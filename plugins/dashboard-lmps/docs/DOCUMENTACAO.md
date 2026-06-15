# Documentação — Dashboard LMPs

Plugin **microfrontend** (Module Federation) da Minha DELPI para acompanhamento de **LMPs** (propostas/ordens de engenharia), com dados do **TOTVS Protheus** via **api-delpi** (módulo Engenharia).

---

## 1. Visão geral

| Item | Valor |
|------|--------|
| ID do plugin | `dashboard-lmps` |
| URL base | `/apps/dashboard-lmps` |
| Container Docker | `delpi-dashboard-lmps` |
| API backend | `/apps/api-delpi/engineering/lmps/*` |
| Federation name | `dashboard-lmps` |
| `remoteEntry` | `/apps/dashboard-lmps/assets/remoteEntry.js` |

O Portal carrega o MFE, injeta o JWT Keycloak em `configureHttpClient` e renderiza uma **única página** analítica (`DashboardLmpsPage`).

### O que o dashboard exibe

- **KPIs:** % LMP dentro do prazo, lead time médio útil, total de propostas no período
- **Gráficos:** contagem por nível (1–3), por status (Pontual, Atrasado, Andamento, Retornada), média de lead time por nível, evolução temporal de lead time e quantidade de propostas
- **Tabela:** listagem detalhada das LMPs filtradas (filial, proposta, datas, SLA, classificação) — clique abre **detalhe da OV**

### Detalhe da OV (`/apps/dashboard-lmps/ov/{sale_number}`)

- KPIs da proposta, cards Proposta / Engenharia / Cliente
- Tabela de produtos + BOM por item (`ProductStructureTree`)
- **Histórico da OV** (`list_history`): linha do tempo vertical com toggle para tabela, filtros, mini-Gantt e tooltips em colunas

### Fora de escopo deste plugin

- Módulo **Transforma Mais** (`/engineering/transforma-mais/*`) — painel em **`dashboard-engineering`**
- Cadastro ou edição de LMPs no Protheus
- Gantt global multi-revisão em escala única

### Legado na plataforma

Documentos antigos citam `dash-lmps` como plugin **iframe**. No repositório atual o manifesto oficial é **`dashboard-lmps`** com `renderMode: "federated"`. Use o arquivo `dash-lmps-microfrontend.manifest.json` ao registrar na Core API.

---

## 2. Arquitetura

```text
Portal (AppHost)
  └─ import remoteEntry.js (dashboard-lmps)
       └─ bootstrap.tsx → mount(App)
            ├─ DashboardLmpsPage (lista + KPIs + gráficos)
            └─ LmpDetailPage (/ov/{sale_number})
                 ├─ useLmpDetail → GET .../lmps/{sale_number}
                 ├─ LmpHistorySection (timeline + tabela + filtros)
                 └─ LmpProductStructuresSection (BOM)
```

| Camada | Responsabilidade |
|--------|------------------|
| `src/api/httpClient.ts` | `fetch` com `Authorization: Bearer` |
| `src/api/lmpApi.ts` | `getLmpsDashboard`, `listLmps` |
| `src/hooks/useLmpsDashboard.ts` | Carga, erro, refresh automático |
| `src/pages/DashboardLmpsPage.tsx` | UI, gráficos e fallback client-side |

---

## 3. Permissões

O usuário precisa de **uma** das permissões na api-delpi:

| Permissão | Uso |
|-----------|-----|
| `dashboard-lmps.view` | Plugin (manifesto) |
| `api-delpi.access` | Acesso amplo à api-delpi (legado) |

Registro: `POST /core-api/admin/apps/register` com o JSON do manifesto (ver [TESTING.md](./TESTING.md)).

---

## 4. Filtros

Filtros são **estado React** sincronizado com a **URL** (`date_start`, `date_end`, `branch`, `listing_type`, `status`).

| Campo | UI | Query API / URL | Observação |
|-------|-----|-----------------|------------|
| Data inicial | `input[type=date]` | `date_start` (YYYY-MM-DD) | Default: primeiro dia do mês |
| Data final | `input[type=date]` | `date_end` | Default: hoje |
| Filial | multi-select | `branch` (CSV) | Vazio = todas |
| Tipo | multi-select | `listing_type` (CSV) | LMP, Amostra, Outro |
| Status | multi-select | `status` (CSV) | Pontual, Atrasado, … |

`syncLmpsFiltersToUrl()` atualiza a query via `history.replaceState` ao alterar filtros — links compartilháveis e retorno do detalhe preservam o recorte.

Botão **Atualizar** dispara `reload()` no hook (nova requisição ao dashboard).

### Atualização automática

`useLmpsDashboard` aceita `autoRefreshMs`. A página usa **2 minutos** (`120_000` ms), apenas com a aba visível (`document.visibilityState === "visible"`).

### Resiliência a erros

Se já existem dados e uma atualização falha, a UI mantém a **última carga válida** e exibe aviso de erro (não limpa KPIs/gráficos).

---

## 5. API consumida

### Endpoint principal (dashboard)

```http
GET /apps/api-delpi/engineering/lmps/dashboard
```

**Query:** `date_start`, `date_end`, `branch`, `status` (default `Todos`), `page`, `page_size` (opcionais).

**Envelope:**

```json
{
  "success": true,
  "message": "...",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 50,
    "summary": {
      "total_lmps": 0,
      "percent_dentro_prazo": 0,
      "avg_lead_time": 0
    },
    "charts": {
      "levelData": [{ "name": "Nível 1", "value": 3 }],
      "statusData": [],
      "leadByLevel": [{ "nivel": "Nível 1", "valor": 12.5 }],
      "evolutionData": [{ "periodo": "jan/26", "mediaLead": 10, "propostas": 5 }]
    }
  }
}
```

### Endpoint auxiliar (listagem paginada)

```http
GET /apps/api-delpi/engineering/lmps
```

Implementado em `listLmps()` — disponível para extensões; a tela atual usa apenas o dashboard agregado.

Detalhamento: [API_MAPPING.md](./API_MAPPING.md).

### Formato de datas nos itens

Campos como `start_date`, `end_date`, `data_limite` vêm da API em **`YYYYMMDD`**. O front formata para exibição `DD/MM/YYYY` e converte para `input[type=date]` quando necessário.

---

## 6. Gráficos e fallback

Quando `data.charts` vem vazio ou incompleto, `DashboardLmpsPage` recalcula agregações no **cliente** a partir de `items` (`fallbackCharts`):

- Contagem por nível e status
- Média de `lead_time_util` por nível
- Evolução por mês a partir de `start_date`

Isso garante gráficos mesmo se o backend não enviar `charts`, com possível divergência se a API passar a agregar de forma diferente.

---

## 7. KPIs e classificação

| KPI | Campo `summary` | Descrição |
|-----|-----------------|-----------|
| % LMP dentro do prazo | `percent_dentro_prazo` | Percentual consolidado no período |
| Lead time médio útil | `avg_lead_time` | Média em dias úteis |
| Total de propostas | `total_lmps` | Quantidade no filtro |

Cada linha da tabela inclui `nivel` (Nível 1–3), `status` (classificação de prazo), `dias_uteis_sla`, `data_limite`, `lead_time_util`, entre outros campos de `LmpDashboardItem`.

---

## 8. Desenvolvimento

### Pré-requisitos

- Node.js 20.19+ (ou 22.12+)
- npm

### Comandos

```bash
cd plugins/dashboard-lmps
npm install
npm run dev      # Vite standalone (index.html)
npm run build    # tsc + vite build
npm run lint
```

Build de produção: `dist/assets/remoteEntry.js`.

### Stack local com Docker

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build \
  gateway core-api dashboard-lmps
```

UI: `http://localhost/apps/dashboard-lmps`

Guia de testes: [TESTING.md](./TESTING.md).

---

## 9. Deploy em produção

1. Build da imagem `dashboard-lmps` (Dockerfile multi-stage: Node + nginx estático).
2. Subir/recriar `delpi-dashboard-lmps`.
3. Gateway já roteia `/apps/dashboard-lmps/assets/*` → container `delpi-dashboard-lmps` (padrão genérico de MFE).
4. Após recreate da **api-delpi**, reiniciar o **gateway** se houver 502 (mesmo padrão dos demais plugins).

```bash
docker compose up -d --build dashboard-lmps
```

Variáveis de ambiente do plugin: nenhuma obrigatória no front (dados vêm da api-delpi / TOTVS).

---

## 10. Estrutura do código

Ver [STRUCTURE.md](./STRUCTURE.md).

---

## 11. Documentos relacionados

| Arquivo | Conteúdo |
|---------|----------|
| [API_MAPPING.md](./API_MAPPING.md) | Endpoints e tipos |
| [TESTING.md](./TESTING.md) | Checklist e curl |
| [STRUCTURE.md](./STRUCTURE.md) | Pastas e convenções |
| `api-delpi/docs/api/06-modulos-departamentais.md` | Engenharia / LMP no backend |
| `plugins/dashboard-quality/docs/DOCUMENTACAO.md` | Plugin irmão (referência de padrão MFE) |

---

## 12. Evoluções sugeridas

Melhorias ainda não implementadas:

- Filiais dinâmicas via API (hoje opções fixas `01`/`02`)
- Script `register-manifest.sh` e CI dedicado no monorepo

**Já entregue (jun/2026):** detalhe OV, timeline, filtros do histórico, mini-Gantt por evento, Gantt global, preferências `localStorage`, filtros na URL, tooltips em ações/paginação/BOM, impressão básica (`@media print`).
