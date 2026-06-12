# Manutenção — aplicação Minha Delpi

Documentação de arquitetura e plano de entrega do módulo **Manutenção** como produto independente no monorepo Delpi Central (API dedicada + plugin microfrontend), no mesmo padrão do [Transformômetro](../transformometro-app/README.md) e do [Strategic Indicators](../../../strategic-indicators-api/docs/README.md).

A **primeira entrega** cobre **ferramentaria — mini-aplicadores** (reposição de peças, golpes, alertas preventivos), migrando o legado WinForms [`MiniAplicadores`](../../../../MiniAplicadores). O id `maintenance` permite escalar depois para outros domínios de manutenção (predial, equipamentos, calendário, etc.) no mesmo plugin.

## Convenção de nomenclatura

| Artefato | Idioma | Exemplo |
|----------|--------|---------|
| **Id do plugin** (manifest, pastas, URLs técnicas, permissões, schema) | **Inglês** kebab-case / snake_case | `maintenance` |
| **Nome exibido ao usuário** (menu, título, manifest `name`, labels de rota) | **Português** | «Manutenção», «Mini-aplicadores» |
| **Rotas de menu no MFE** | Português (UX) | `/apps/maintenance/relatorio` |
| **Rotas api-delpi (TOTVS)** | Inglês | `/engineering/mini-applicators/*` |

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [OVERVIEW.md](./OVERVIEW.md) | Visão geral, objetivo, componentes, URLs, permissões |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Camadas, domínio, banco, integração portal e api-delpi |
| [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md) | Contrato vivo: o que fica na API do plugin vs. rotas TOTVS na api-delpi |
| [ROADMAP.md](./ROADMAP.md) | Fases de entrega |
| [ESPECIFICACAO.md](./ESPECIFICACAO.md) | Especificação funcional (mini-aplicadores + escopo futuro) |
| [status-atual.md](./status-atual.md) | Snapshot do que existe no repo |
| [OPERATIONS.md](./OPERATIONS.md) | Runbook deploy, RBAC, import Access |
| [ARCHITECTURE.md (API)](../../../maintenance-api/docs/ARCHITECTURE.md) | Detalhe técnico da API dedicada |
| [integration-contracts.md (API)](../../../maintenance-api/docs/integration-contracts.md) | Contratos HTTP com api-delpi |

## Princípios arquiteturais

| Regra | Aplicação |
|-------|-----------|
| **CRUD operacional** | Postgres na `maintenance-api` (reposições, motivos, status, parâmetros preventivos) |
| **Leitura TOTVS** | Somente via **api-delpi** — gateways HTTP (`shared/delpi_api_client`), **sem** SQL Protheus duplicado na API do plugin |
| **Contrato público TOTVS** | Novas rotas registradas na api-delpi (`route_contract_registry`, OpenAPI, Playbook 10) |
| **UI** | MFE federado `plugins/maintenance` — JWT → API dedicada; nunca TOTVS direto no browser |

## Estado atual no monorepo

Ver [status-atual.md](./status-atual.md). **Fases 0–2 concluídas**; Fase 3 (migração Access + go-live) em curso.

## Legado de referência

| Peça | Situação |
|------|----------|
| `MiniAplicadores` (WinForms + Access) | Fonte funcional e de regras de negócio; **não** é runtime da Minha Delpi |
| Access `MiniAplicadoresBD` | Modelo lógico a migrar para Postgres (`TabReposicoes`, `TabMotivo`, `TabStatusPeca`) |
| TOTVS (SB1010, SG1010, SD4/SHY/SH4/SH6) | Consultas legadas → **novas rotas api-delpi**, consumidas por gateways na API do plugin |

## Referências

- Legado: repositório `MiniAplicadores` / `InstructionsGPT.md`
- Contrato envelope api-delpi: [playbook-10-contrato-respostas-api-delpi.md](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md)
- Padrão integração (Transformômetro): [integration-contracts.md](../../../transformometro-api/docs/integration-contracts.md)
- Registrar plugin no portal: [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md)
