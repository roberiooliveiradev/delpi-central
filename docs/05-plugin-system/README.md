# Plugin System — documentação

> **Contrato vigente:** `schemaVersion: "1.0.0"`  
> **Evolução planejada:** `schemaVersion: "1.1.0"` (plugin vs módulo)  
> **Registro:** `POST /core-api/admin/apps/register`

---

## Visão e evolução (jun/2026)

| Arquivo | Conteúdo |
|---|---|
| [plugin-vs-module.md](./plugin-vs-module.md) | Taxonomia plugin/módulo, SI, Manutenção, decisões em aberto |
| [manifest-schema-1.1.0.md](./manifest-schema-1.1.0.md) | Contrato JSON 1.1.0 (`target`, `ui.module`, exemplos) |
| [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md) | Fases 0–6 — ordem de implementação |
| [core-api-alteracoes.md](./core-api-alteracoes.md) | Arquivos e endpoints Core API |
| [portal-alteracoes.md](./portal-alteracoes.md) | RouteDelegate, tipos, AppHost, admin |
| [module-runtime.md](./module-runtime.md) | Pacote `@delpi/module-runtime` compartilhado |

---

## Contrato atual (1.0.0)

| Arquivo | Conteúdo |
|---|---|
| [manifesto-plugin.md](./manifesto-plugin.md) | Schema JSON, tipos, validação |
| [registro-de-plugin.md](./registro-de-plugin.md) | Fluxo técnico de register |
| [atualizacao-de-manifesto.md](./atualizacao-de-manifesto.md) | PUT manifesto não estrutural |
| [versionamento-e-rollback.md](./versionamento-e-rollback.md) | Versões, rollback |
| [microfrontends.md](./microfrontends.md) | Module Federation |
| [iframe.md](./iframe.md) | Plugins iframe (ex.: `dash-lmps`) |
| [backend-only.md](./backend-only.md) | Sem UI |
| [visao-geral-plugin-system.md](./visao-geral-plugin-system.md) | Visão geral do sistema |

---

## Operação

- Runbook: [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md)
- Inventário: [../08-plugins/README.md](../08-plugins/README.md)
- Modelo de dados: [../09-banco-de-dados/modelo-plugin-system.md](../09-banco-de-dados/modelo-plugin-system.md)
- Portal (consumo): [../06-portal-frontend/consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md)

**Nota:** plugin LMPs no repositório usa `id` **`dash-lmps`** (iframe, `basePath` `/dash-lmps`), não `dashboard-lmps`.
