# Emissão de Notas Fiscais — índice do módulo

Wizard de **solicitação de emissão** de NF (saída) + fila do Faturamento no ecossistema Minha DELPI.

**Status (2026-08):** MVP v1 — MFE federado + rotas api-delpi + migration V001. Sem conciliação SF2.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [PLAYBOOK.md](./PLAYBOOK.md) | Playbook operacional — papéis, fluxo, deploy |
| [ROADMAP.md](./ROADMAP.md) | Etapas e status do MVP |
| [Plugin README](../../../plugins/invoice-issuance/README.md) | Dev, smoke, permissões, estrutura MFE |
| [API invoice-issuance.md](../../../api-delpi/docs/api/invoice-issuance.md) | Contrato HTTP |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Plugin MFE | `plugins/invoice-issuance/` |
| Rotas HTTP | `api-delpi/app/interface/http/routes/invoice_issuance/` |
| Use cases | `api-delpi/app/application/use_cases/invoice_issuance/` |
| Migrations | `api-delpi/migrations/plugins/invoice-issuance/` |
| Inventário plugins | [08-plugins/README.md](../../08-plugins/README.md) |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |

---

## Identificação

| Campo | Valor |
|-------|--------|
| `id` | `invoice-issuance` |
| `basePath` | `/apps/invoice-issuance` |
| Container Docker | `delpi-invoice-issuance` |
| API | `/apps/api-delpi/invoice-issuance/*` |
| Caller header | `X-Delpi-Caller-App: invoice-issuance` |
| Schema Postgres | `invoice_issuance` |
| Menu | Financeiro |
| Permissões | `.access`, `.create`, `.view`, `.view.filial-01/02`, `.process`, `.manage` |
| ERP | SA1/SA2 (destinatário), SB1 (itens), SB2 local 01 (saldo informativo) |

---

## Acesso rápido (dev)

```text
http://localhost/apps/invoice-issuance/filial-01
```
