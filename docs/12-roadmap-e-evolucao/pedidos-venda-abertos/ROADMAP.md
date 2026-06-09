# Roadmap — Plugin Pedidos de Venda em Aberto

> **Arquivo:** `docs/12-roadmap-e-evolucao/pedidos-venda-abertos/ROADMAP.md`  
> **Status:** Fase 3 concluída (2026-06-09) — dashboard operacional com KPIs, filtros e tabela  
> **Produto:** Minha DELPI  
> **Escopo:** plugin `pedidos-venda-abertos` + endpoint read-only em `api-delpi`

---

## 1. Objetivo

Disponibilizar no Portal uma **tela operacional de consulta** para vendedores e equipes comerciais acompanharem rapidamente:

- pedidos de venda **em aberto** (linha a linha);
- **saldo** pendente de entrega e **valor em aberto**;
- disponibilidade de **estoque** por linha;
- **datas de entrega** e **despacho** (quando existir);
- filtros por cliente, pedido, produto, filial e status de estoque.

**Escopo explícito:** somente leitura — sem baixa, edição ou gravação no Protheus.

**Fonte de dados:** view TOTVS `dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES`.

---

## 2. Decisões de arquitetura

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Tipo de plugin | `microfrontend` + `renderMode: federated` | Padrão operacional no monorepo |
| API dedicada (`*-api`) | **Não** | Dados TOTVS pertencem à **api-delpi** |
| Rota backend | `GET /apps/api-delpi/pedidos-venda-abertos` | Router dedicado; alinhado ao requisito funcional |
| Persistência própria | **Não** | Leitura direta da view; sem PostgreSQL |
| Referência de UI | `plugins/dashboard-commercial` + `plugins/eficiencia-fabril` | Tabela/filtros + KPI + reload operacional |
| Referência de backend | `otd_query_repository` + `eficiencia_fabril_query_repository` | View TOTVS + summary/items |
| Filtros na UI | **Client-side** sobre dataset completo | KPIs devem bater com tabela filtrada (critério de aceite) |
| Paginação | **Client-side** (50 linhas/página) | Volume moderado esperado; evita complexidade inicial |
| Conexão SQL | Variáveis `TOTVS_DB_*` existentes | Sem credenciais novas ou hardcode |

Fluxo:

```text
Portal → MFE pedidos-venda-abertos
  → GET /apps/api-delpi/pedidos-venda-abertos  (Bearer JWT)
  → PedidosVendaAbertosQueryRepository
  → dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES
```

---

## 3. Permissões

| Camada | Código | Observação |
|--------|--------|------------|
| Manifesto (Core API) | `pedidos-venda-abertos.access` | Entrada no menu do Portal |
| api-delpi | `pedidos-venda-abertos.access` | Decorator `@require_any_permission` |
| Compatibilidade | `api-delpi.access` | Perfis com acesso amplo à api-delpi |

Registro: `POST /core-api/admin/apps/register` com JWT `apps.manage` ou superadmin.

RBAC pós-registro: associar `pedidos-venda-abertos.access` à role **Vendedores** (ou equivalente) no `/admin`.

---

## 4. Contrato de resposta (alvo)

Envelope padrão api-delpi (`success`, `message`, `data`, `meta`):

```json
{
  "success": true,
  "message": "Pedidos de venda em aberto carregados com sucesso.",
  "data": {
    "items": [
      {
        "nome_cliente": "string",
        "tipo_entidade": "CLIENTE",
        "tipo_pedido": "N",
        "pedido_cliente": "string",
        "filial": "string",
        "pedido": "string",
        "linha": "string",
        "produto": "string",
        "codigo_cliente": "string",
        "quantidade": 0,
        "entregue": 0,
        "saldo": 0,
        "data_despacho": null,
        "data_entrega": "2026-06-09",
        "no_estoque": 0,
        "preco_venda": 0,
        "valor_aberto": 0
      }
    ],
    "summary": {
      "total_linhas": 0,
      "valor_total_aberto": 0,
      "saldo_total": 0,
      "itens_com_estoque": 0,
      "itens_estoque_parcial": 0,
      "itens_sem_estoque": 0
    }
  },
  "meta": {
    "operationId": "list_pedidos_venda_abertos",
    "entity": "open_sales_order",
    "shape": "composite_analysis"
  }
}
```

Detalhe dos campos da view: [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md).

---

## 5. Fases de entrega

### Fase 0 — Especificação e validação TOTVS (pré-código) ✅

**Objetivo:** confirmar que a view existe, que os nomes de colunas batem com o contrato e estimar volume antes de codificar o repository.

| # | Entrega | Detalhe | Status |
|---|---------|---------|--------|
| 0.1 | Validar existência da view | `SELECT TOP 10` no ambiente dev via `delpi-api-delpi` | ✅ |
| 0.2 | Confirmar colunas | 17/17 campos compatíveis com [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | ✅ |
| 0.3 | Literais de domínio | `CLIENTE` (151), `FORNECEDOR` (6); filiais `01` (126), `02` (31) | ✅ |
| 0.4 | Sanidade de datas | 70,06% sem `data_despacho`; normalizar `""` → `null` na Fase 1 | ✅ |
| 0.5 | Estimar volume | **157 linhas** → carga completa + filtros client-side (Fase 3) | ✅ |
| 0.6 | Query de referência | SQL documentado em [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | ✅ |
| 0.7 | Relatório Fase 0 | [FASE0-VALIDACAO-VIEW.md](./FASE0-VALIDACAO-VIEW.md) preenchido | ✅ |

**Resultados principais:**

| Métrica | Valor |
|---------|-------|
| Total de linhas | 157 |
| Valor total em aberto | R$ 2.348.421,81 |
| Saldo total | 4.453,58 |
| Itens com estoque / parcial / sem | 78 / 29 / 50 |
| Sem despacho | 110 linhas (70,06%) |

**Critério de pronto:** ✅ query de amostra retorna dados coerentes; colunas mapeadas; volume documentado; `ready_for_phase_1: true` no relatório Fase 0.

**Observação para Fase 1:** `data_despacho` nula chega como string vazia via `_normalize_row` — normalizar para `null` no use case antes da resposta HTTP.

---

### Fase 1 — Backend api-delpi (MVP leitura) ✅

**Objetivo:** endpoint agregado pronto para consumo pelo MFE, com RBAC e contrato padronizado.

| # | Entrega | Arquivo / local | Status |
|---|---------|-----------------|--------|
| 1.1 | Constantes RBAC | `api-delpi/app/application/security/api_delpi_permissions.py` | ✅ |
| 1.2 | Port | `app/domain/ports/pedidos_venda_abertos/pedidos_venda_abertos_query_repository_port.py` | ✅ |
| 1.3 | Repository TOTVS | `app/infrastructure/persistence/totvs/pedidos_venda_abertos/pedidos_venda_abertos_query_repository.py` | ✅ |
| 1.4 | DTO response | `app/application/dto/pedidos_venda_abertos/list_pedidos_venda_abertos_response.py` | ✅ |
| 1.5 | Use case | `app/application/use_cases/pedidos_venda_abertos/list_pedidos_venda_abertos_use_case.py` | ✅ |
| 1.6 | Composer | `app/composition/pedidos_venda_abertos_composer.py` | ✅ |
| 1.7 | Router | `app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py` | ✅ |
| 1.8 | Registro main | `api-delpi/app/main.py` | ✅ |
| 1.9 | Contrato meta | `app/interface/http/route_contract_registry.py` | ✅ |
| 1.10 | Testes unitários | `api-delpi/tests/test_list_pedidos_venda_abertos_use_case.py` | ✅ |
| 1.11 | Smoke meta | `api-delpi/tests/test_route_meta_smoke.py` | ✅ |
| 1.12 | Documentação API | `api-delpi/docs/api/10-referencia-rapida-endpoints.md` | ✅ |

**Validação live (2026-06-09):** 157 itens, summary coerente com Fase 0; 110 linhas com `data_despacho: null` após normalização.

**Critério de pronto:** ✅

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_list_pedidos_venda_abertos_use_case.py \
  tests/test_route_meta_smoke.py::test_pedidos_venda_abertos_returns_meta -q

TOKEN=<jwt_com_permissao> curl -s \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost/apps/api-delpi/pedidos-venda-abertos/ | jq '.success, .meta.operationId, .data.summary'
```

---

### Fase 2 — Plugin MFE (esqueleto deployável) ✅

**Objetivo:** plugin visível no Portal com página mínima consumindo a API.

| # | Entrega | Detalhe | Status |
|---|---------|---------|--------|
| 2.1 | Scaffold Vite + TS | `plugins/pedidos-venda-abertos/` | ✅ |
| 2.2 | Module Federation | `base: /apps/pedidos-venda-abertos/`, `remoteEntry.js` | ✅ |
| 2.3 | `bootstrap.tsx` | `mount` / `unmount` / `updateRoute` | ✅ |
| 2.4 | `httpClient.ts` | JWT + `X-Delpi-Caller-App: pedidos-venda-abertos` | ✅ |
| 2.5 | Cliente API | `src/api/pedidosVendaAbertosApi.ts` | ✅ |
| 2.6 | Manifesto | `pedidos-venda-abertos.manifest.json` v `1.0.0` | ✅ |
| 2.7 | Dockerfile | Node build → nginx | ✅ |
| 2.8 | Compose dev/prod | `delpi-pedidos-venda-abertos` | ✅ |
| 2.9 | Script registro | `scripts/register-manifest.sh` | ✅ |
| 2.10 | Página mínima | Resumo + amostra JSON da API | ✅ |

**Critério de pronto:** ✅

```bash
cd plugins/pedidos-venda-abertos && npm run ci
docker compose -f infra/docker-compose.dev.yml up -d --build pedidos-venda-abertos
curl -sI http://localhost/apps/pedidos-venda-abertos/assets/remoteEntry.js   # → 200
TOKEN=<jwt_admin> ./plugins/pedidos-venda-abertos/scripts/register-manifest.sh
```

---

### Fase 3 — Dashboard operacional (UI completa MVP) ✅

**Objetivo:** experiência de consulta rápida para vendedores — KPIs, filtros, tabela, badges e reload.

| # | Entrega | Detalhe | Status |
|---|---------|---------|--------|
| 3.1 | PageHeader | Título, ícone, botão **Atualizar** | ✅ |
| 3.2 | KPI cards | 6 cards recalculados sobre linhas filtradas | ✅ |
| 3.3 | FilterBar | busca, filial, entidade, estoque, datas entrega | ✅ |
| 3.4 | Hook de dados | `usePedidosVendaAbertosDashboard` | ✅ |
| 3.5 | Filtros locais | `filterItems.ts` + summary derivado | ✅ |
| 3.6 | Tabela | colunas operacionais + ordenação client-side | ✅ |
| 3.7 | Paginação | 50 linhas/página | ✅ |
| 3.8 | Badges | `statusBadges.ts` (entrega, estoque, despacho) | ✅ |
| 3.9 | Formatação | `format.ts` + `dates.ts` (BRL, dd/MM/yyyy) | ✅ |
| 3.10 | Estados UX | loading, erro, vazio, filtro sem resultado | ✅ |
| 3.11 | Responsividade | breakpoints 1100px / 768px, tabela card mobile | ✅ |
| 3.12 | Design system | prefixo `pva-`, tokens do portal | ✅ |

**Critério de pronto:** ✅ `npm run ci` passa; KPIs batem com tabela filtrada; despacho nulo → "Não informado".

---

### Fase 4 — RBAC, CI e homologação

**Objetivo:** entrega segura para usuários não superadmin e pipeline mínimo de qualidade.

| # | Entrega | Detalhe | Status |
|---|---------|---------|--------|
| 4.1 | Role Vendedores | `pedidos-venda-abertos.access` associada no RBAC | Pendente |
| 4.2 | Teste usuário piloto | Usuário sem superadmin acessa menu + API | Pendente |
| 4.3 | Script CI | `scripts/ci/build-pedidos-venda-abertos.sh` | Pendente |
| 4.4 | Smoke homologação | `scripts/homologacao/check-pedidos-venda-abertos.sh` | Pendente |
| 4.5 | README plugin | `plugins/pedidos-venda-abertos/README.md` | Pendente |
| 4.6 | Inventário docs | Entrada em `docs/08-plugins/README.md` | Pendente |
| 4.7 | Teste 403 | JWT sem permissão → 403 na API; plugin ausente em `/me/apps` | Pendente |

**Critério de pronto:** PR com CI verde; usuário piloto (role Vendedores) acessa dashboard; smoke script passa com `TOKEN`.

---

### Fase 5 — Produção

**Objetivo:** deploy na VM de produção sem regressão.

| # | Entrega | Detalhe | Status |
|---|---------|---------|--------|
| 5.1 | Build imagens | `pedidos-venda-abertos` + `api-delpi` com nova rota | Pendente |
| 5.2 | Gateway prod | `depends_on: pedidos-venda-abertos` no compose prod | Pendente |
| 5.3 | Registro manifesto prod | `POST /core-api/admin/apps/register` no ambiente prod | Pendente |
| 5.4 | RBAC produção | Role Vendedores com permissão | Pendente |
| 5.5 | Validação VPN/TOTVS | Endpoint responde no servidor prod | Pendente |
| 5.6 | Amostra manual | Conferir 5–10 linhas API vs SQL direto na view | Pendente |

**Critério de pronto:** vendedores em produção acessam via Portal; números de summary conferem com amostra SQL.

---

### Fase 6 — Evoluções (pós-MVP)

| Entrega | Prioridade | Detalhe |
|---------|------------|---------|
| Paginação server-side | Alta (se volume > ~5k linhas) | Query params `page`, `page_size`; summary filtrado no SQL |
| Cache TTL curto | Média | Evitar hammering na view TOTVS |
| Export CSV/Excel | Média | Dados filtrados em memória (padrão eficiência fabril) |
| Filtro por vendedor/comprador | Média | Se a view expuser campo |
| Drill-down por pedido | Baixa | Agrupar linhas do mesmo `pedido` |
| Integração chat/IA | Baixa | OpenAPI agent metadata + rota chat-critical |
| Alertas de atraso | Baixa | Linhas com `data_entrega` vencida |

---

## 6. Dependências e riscos

| Dependência | Impacto |
|-------------|---------|
| VPN / rede TOTVS | api-delpi falha sem SQL Server |
| View `VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES` em homolog/prod | repository vazio ou erro |
| Keycloak + audience JWT | login Portal e chamadas API |
| `TOTVS_DB_*` no `.env` | mesma config dos demais módulos TOTVS |
| Schema da view | colunas divergentes bloqueiam Fase 1 |

| Risco | Mitigação |
|-------|-----------|
| Volume alto de linhas | Fase 0 estima volume; Fase 6 paginação server-side |
| KPIs desalinhados com tabela | summary recalculado no frontend sobre linhas filtradas |
| `data_despacho` nula tratada como erro | regra explícita: null → "Não informado" |
| Permissão só no frontend | API com `@require_any_permission` independente do menu |
| Performance na carga inicial | botão Atualizar; cache opcional na Fase 6 |

---

## 7. Checklist de implantação (dev)

- [x] **Fase 0:** view validada — [FASE0-VALIDACAO-VIEW.md](./FASE0-VALIDACAO-VIEW.md) preenchido (2026-06-09)
- [x] **Fase 1:** endpoint `GET /pedidos-venda-abertos` na api-delpi + testes (2026-06-09)
- [x] **Fase 2:** plugin no compose + manifesto + `remoteEntry.js` 200 (2026-06-09)
- [x] **Fase 3:** UI dashboard completa (KPIs, filtros, tabela, badges) (2026-06-09)
- [ ] **Fase 4:** RBAC piloto + CI + smoke homologação
- [ ] **Fase 5:** produção validada

---

## 8. O que reaproveitar do monorepo

| Peça existente | Uso |
|----------------|-----|
| `plugins/eficiencia-fabril/` | Esqueleto MFE, httpClient, hook com filtros locais |
| `plugins/dashboard-commercial/` | DataTable, Pagination, KpiCard, FilterBar |
| `api-delpi/.../otd_query_repository.py` | Padrão SELECT em view TOTVS |
| `api-delpi/.../eficiencia_fabril_query_repository.py` | Summary + items |
| `plugins/dashboard-commercial/scripts/register-manifest.sh` | Template script registro |
| `docs/10-guias-operacionais/registrar-plugin.md` | Runbook operacional |
| `.cursor/rules/plugins-visual-design-system.mdc` | Tokens, prefixo CSS, responsividade |
| `.cursor/rules/api-delpi-response-contract.mdc` | Envelope + meta |

---

## 9. Comandos de referência

| Escopo | Comando |
|--------|---------|
| Testes API | `cd api-delpi && pytest tests/test_list_pedidos_venda_abertos_use_case.py -q` |
| Build plugin | `cd plugins/pedidos-venda-abertos && npm run ci` |
| Subir dev | `docker compose -f infra/docker-compose.dev.yml up -d --build pedidos-venda-abertos api-delpi gateway` |
| Registrar | `TOKEN=<jwt> ./plugins/pedidos-venda-abertos/scripts/register-manifest.sh` |
| Smoke assets | `curl -sI http://localhost/apps/pedidos-venda-abertos/assets/remoteEntry.js` |
| Smoke API | `curl -s -H "Authorization: Bearer $TOKEN" http://localhost/apps/api-delpi/pedidos-venda-abertos` |

---

## 10. Documentos relacionados

- [README.md](./README.md) — índice do módulo
- [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) — contrato da view
- [FASE0-VALIDACAO-VIEW.md](./FASE0-VALIDACAO-VIEW.md) — relatório Fase 0
- [../../08-plugins/README.md](../../08-plugins/README.md) — inventário plugins
- [../../05-plugin-system/manifesto-plugin.md](../../05-plugin-system/manifesto-plugin.md) — contrato JSON
- [../../10-guias-operacionais/registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) — registro
- [../eficiencia-fabril/ROADMAP.md](../eficiencia-fabril/ROADMAP.md) — referência de roadmap por fases

---

## 11. Histórico

| Data | Nota |
|------|------|
| 2026-06-09 | Roadmap criado a partir do requisito funcional e alinhamento com padrões eficiencia-fabril / dashboard-commercial |
| 2026-06-09 | **Fase 0 concluída** — view validada (157 linhas, 17 colunas OK, `ready_for_phase_1: true`); relatório em FASE0-VALIDACAO-VIEW.md |
| 2026-06-09 | **Fase 1 concluída** — endpoint `GET /apps/api-delpi/pedidos-venda-abertos/` com RBAC, testes e validação live (157 itens) |
| 2026-06-09 | **Fase 2 concluída** — plugin MFE `plugins/pedidos-venda-abertos`, Docker, CI build, `remoteEntry.js` 200 |
| 2026-06-09 | **Fase 3 concluída** — dashboard operacional com KPIs, filtros client-side, tabela paginada e badges |
