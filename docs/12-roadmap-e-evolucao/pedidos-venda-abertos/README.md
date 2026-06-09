# Pedidos de Venda em Aberto — plugin Minha DELPI

Consulta operacional read-only de pedidos de venda em aberto para vendedores, consumindo a view TOTVS `dbo.VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES` via **api-delpi**.

**Status:** Fase 3 concluída (2026-06-09) — dashboard operacional MVP; **pronto para Fase 4**.

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

## Acesso rápido (após implantação)

```text
http://localhost/apps/pedidos-venda-abertos/
```
