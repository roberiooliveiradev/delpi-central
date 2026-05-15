# Plugin System — documentação

> **Contrato:** `schemaVersion: "1.0.0"` · **Registro:** `POST /core-api/admin/apps/register`

---

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [manifesto-plugin.md](./manifesto-plugin.md) | Schema JSON, tipos, validação |
| [registro-de-plugin.md](./registro-de-plugin.md) | Fluxo técnico de register |
| [atualizacao-de-manifesto.md](./atualizacao-de-manifesto.md) | PUT manifesto não estrutural |
| [versionamento-e-rollback.md](./versionamento-e-rollback.md) | Versões, rollback |
| [microfrontends.md](./microfrontends.md) | Module Federation |
| [iframe.md](./iframe.md) | Plugins iframe (ex.: `dash-lmps`) |
| [backend-only.md](./backend-only.md) | Sem UI |

---

## Operação

- Runbook: [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md)
- Inventário: [../08-plugins/README.md](../08-plugins/README.md)
- Modelo de dados: [../09-banco-de-dados/modelo-plugin-system.md](../09-banco-de-dados/modelo-plugin-system.md)

**Nota:** plugin LMPs no repositório usa `id` **`dash-lmps`** (iframe, `basePath` `/dash-lmps`), não `dashboard-lmps`.
