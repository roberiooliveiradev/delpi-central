# Lançamento de Notas Fiscais — índice do módulo

Controle do **recebimento físico → solicitação → atendimento → lançamento** (confirmação Protheus `SF1` ou **Já lançada** manual) no ecossistema Minha DELPI.

**Status (2026-07):** MVP entregue — MFE + rotas api-delpi + migrations V001–V003 + conciliação sob demanda (refresh/run).

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [PLAYBOOK.md](./PLAYBOOK.md) | **Playbook operacional** — north star, papéis, fluxo, deploy, ondas |
| [especificacao-funcional-tecnica.md](./especificacao-funcional-tecnica.md) | Contrato de domínio (chave fiscal, estados, modelo) |
| [ROADMAP.md](./ROADMAP.md) | Etapas de implementação e status |
| [Plugin README](../../../plugins/lancamento-notas-fiscais/README.md) | Dev, smoke, permissões, estrutura MFE |
| [API lancamento-notas-fiscais.md](../../../api-delpi/docs/api/lancamento-notas-fiscais.md) | Contrato HTTP completo |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Plugin MFE | `plugins/lancamento-notas-fiscais/` |
| Rotas HTTP | `api-delpi/app/interface/http/routes/lancamento_notas_fiscais/` |
| Use cases | `api-delpi/app/application/use_cases/lancamento_notas_fiscais/` |
| Migrations | `api-delpi/migrations/plugins/lancamento-notas-fiscais/` |
| Inventário plugins | [08-plugins/README.md](../../08-plugins/README.md) |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |

---

## Identificação

| Campo | Valor |
|-------|--------|
| `id` | `lancamento-notas-fiscais` |
| `basePath` | `/apps/lancamento-notas-fiscais` |
| Container Docker | `delpi-lancamento-notas-fiscais` |
| API | `/apps/api-delpi/lancamento-notas-fiscais/*` |
| Caller header | `X-Delpi-Caller-App: lancamento-notas-fiscais` |
| Schema Postgres | `lancamento_notas_fiscais` |
| Menu | Financeiro |
| Permissões | `.access`, `.create`, `.view`, `.process`, `.manage` |
| ERP | SA2 (fornecedores), SF1/SD1 (match) |

---

## Acesso rápido (dev)

```text
http://localhost/apps/lancamento-notas-fiscais
```
