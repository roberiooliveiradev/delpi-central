# Propostas Comerciais — plugin Minha DELPI

Consulta **read-only** de propostas comerciais **ativas** no Protheus/TOTVS, com detalhe operacional, emissão de PDF e revisão editável antes da exportação.

**Status:** MVP em produção (2026-06) — listagem, detalhe, PDF e fallback de **prospect** (`SUS010`) quando não há cliente em `SA1010`.

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
| Plugin MFE | `plugins/propostas-comerciais/` |
| README operacional | [plugins/propostas-comerciais/README.md](../../../plugins/propostas-comerciais/README.md) |
| Controller HTTP | `api-delpi/app/interface/http/propostas_comerciais_controller.py` |
| Queries TOTVS | `api-delpi/app/infrastructure/totvs/propostas_comerciais/queries.py` |
| Formatter canônico | `api-delpi/app/domain/propostas_comerciais/services/proposta_comercial_formatter.py` |
| PDF (ReportLab) | `api-delpi/app/infrastructure/pdf/propostas_comerciais/proposta_comercial_pdf_renderer.py` |
| Testes | `api-delpi/tests/test_propostas_comerciais.py` |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |
| Manifesto (contrato) | [manifesto-plugin.md](../../05-plugin-system/manifesto-plugin.md) |

---

## Acesso rápido (após implantação)

```text
http://localhost/apps/propostas-comerciais/
```

Smoke de assets:

```bash
curl -sI http://localhost/apps/propostas-comerciais/assets/remoteEntry.js | head -5
```
