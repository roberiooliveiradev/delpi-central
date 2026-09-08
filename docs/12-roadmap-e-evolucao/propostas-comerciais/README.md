# Propostas Comerciais — documentação histórica

Consulta **read-only** de propostas comerciais **ativas** no Protheus/TOTVS (ADY), com detalhe e PDF.

> **Status (set/2026):** MFE **removido** do monorepo (F2c). UX canônica = Portal Comercial `/apps/commercial/proposals`. Paths api-delpi `/propostas-comerciais/*` **permanecem** via BFF. Redirects: [F2C-CUTOVER-RUNBOOK.md](../commercial/F2C-CUTOVER-RUNBOOK.md).

Os documentos abaixo são **arquivo histórico** da especificação do plugin antigo.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md) | Comportamento funcional, API, UI, PDF, permissões e deploy |
| [ESPECIFICACAO-DADOS-TOTVS.md](./ESPECIFICACAO-DADOS-TOTVS.md) | Tabelas Protheus, joins SQL e mapeamento de campos |

---

## Identificação do plugin

| Campo | Valor |
|-------|--------|
| `id` | `propostas-comerciais` |
| Nome exibido | Propostas Comerciais |
| Versão manifesto | `0.1.0` |
| `basePath` | `/apps/propostas-comerciais` |
| Container Docker | `delpi-propostas-comerciais` |
| Permissão Portal / API | `propostas-comerciais.view` (e legado `api-delpi.access`, `dashboard-commercial.view`) |
| Fonte de dados | SQL Server / Protheus — tabelas `ADY010`, `AD1010`, `ADZ010`, `SA1010`, `SUS010`, … |
| Backend | `api-delpi` — módulo `propostas_comerciais` |

---

## Endpoints API (gateway)

| Método | Caminho | Uso |
|--------|---------|-----|
| `GET` | `/apps/api-delpi/propostas-comerciais` | Listagem das propostas ativas recentes |
| `GET` | `/apps/api-delpi/propostas-comerciais/{proposta_interna}` | Detalhe completo (cabeçalho, cliente, itens, …) |
| `GET` | `/apps/api-delpi/propostas-comerciais/{proposta_interna}/pdf` | PDF com dados do Protheus |
| `POST` | `/apps/api-delpi/propostas-comerciais/{proposta_interna}/pdf` | PDF com overrides editáveis (revisão antes de exportar) |

Envelope padrão (JSON): `{ success, message, data, meta }`. PDF retorna `application/pdf` inline.

---

## Rotas do Portal

| Rota | Finalidade |
|------|------------|
| `/apps/propostas-comerciais` | Listagem com busca local |
| `/apps/propostas-comerciais/{proposta_interna}` | Detalhe + emissão de PDF |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| MFE (removido F2c) | — · UX: `/apps/commercial/proposals` |
| Docs históricos | esta pasta |
| Controller HTTP | `api-delpi/app/interface/http/propostas_comerciais_controller.py` |
| Queries TOTVS | `api-delpi/app/infrastructure/totvs/propostas_comerciais/queries.py` |
| Formatter canônico | `api-delpi/app/domain/propostas_comerciais/services/proposta_comercial_formatter.py` |
| PDF (ReportLab) | `api-delpi/app/infrastructure/pdf/propostas_comerciais/proposta_comercial_pdf_renderer.py` |
| Testes | `api-delpi/tests/test_propostas_comerciais.py` |
| Cutover | [F2C-CUTOVER-RUNBOOK.md](../commercial/F2C-CUTOVER-RUNBOOK.md) |

---

## Acesso rápido (pós-F2c)

```text
http://localhost/apps/commercial/proposals
# deep link legado redireciona:
# http://localhost/apps/propostas-comerciais/ → Portal
```