# Pedidos de Venda em Aberto — documentação histórica

Consulta operacional read-only de pedidos de venda em aberto (view TOTVS via **api-delpi**).

> **Status (set/2026):** MFE **removido** do monorepo (F2c). UX canônica = [Portal Comercial](../commercial/README.md). Paths TOTVS `/pedidos-venda-abertos/*` na api-delpi **permanecem** (BFF commercial-api). Redirects: [F2C-CUTOVER-RUNBOOK.md](../commercial/F2C-CUTOVER-RUNBOOK.md) · [ADR-002](../commercial/adr/ADR-002-deprecar-pedidos-venda-abertos.md).

Os documentos abaixo são **arquivo histórico** da especificação e do roadmap do plugin antigo.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ROADMAP.md](./ROADMAP.md) | **Plano de implementação por fases** — entregas, critérios de pronto, riscos |
| [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | Contrato da view TOTVS e campos da API |
| [FASE0-VALIDACAO-VIEW.md](./FASE0-VALIDACAO-VIEW.md) | Template do relatório de validação TOTVS (Fase 0) |

---

## Identificação do plugin

| Campo | Valor |
|-------|--------|
| `id` | `pedidos-venda-abertos` |
| Nome exibido | Pedidos de Venda em Aberto |
| `basePath` | `/apps/pedidos-venda-abertos` |
| Container Docker | `delpi-pedidos-venda-abertos` |
| Permissão Portal / API | `pedidos-venda-abertos.access` |
| Fonte de dados | `dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES` (SQL Server / Protheus) |

---

## Endpoint API (gateway)

| Método | Caminho | Uso |
|--------|---------|-----|
| `GET` | `/apps/api-delpi/pedidos-venda-abertos` | Lista de linhas em aberto + summary agregado |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Plugin MFE (a criar) | `plugins/pedidos-venda-abertos/` |
| Padrão plugin operacional | `plugins/eficiencia-fabril/` |
| Padrão tabela/filtros | `plugins/dashboard-commercial/` |
| Repository TOTVS (referência) | `api-delpi/app/infrastructure/persistence/totvs/supplies_repositories/otd_query_repository.py` |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |
| Inventário plugins | [08-plugins/README.md](../../08-plugins/README.md) |
| Manifesto (contrato) | [manifesto-plugin.md](../../05-plugin-system/manifesto-plugin.md) |

---

## Acesso rápido (pós-F2c)

```text
http://localhost/apps/commercial/open-orders
# deep link legado redireciona:
# http://localhost/apps/pedidos-venda-abertos/ → Portal
```