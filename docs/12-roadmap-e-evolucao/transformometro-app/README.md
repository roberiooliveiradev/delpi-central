# Transformômetro — aplicação Minha Delpi

Documentação de arquitetura e plano de entrega do **Transformômetro** como produto independente no monorepo Delpi Central (API dedicada + plugin microfrontend), no mesmo padrão do [Strategic Indicators](../../../strategic-indicators-api/docs/README.md).

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [OVERVIEW.md](./OVERVIEW.md) | Visão geral, objetivo, componentes, URLs, permissões |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Camadas, domínio, cálculo, banco, integração portal |
| [PLAYBOOK-MODELAGEM.md](./PLAYBOOK-MODELAGEM.md) | Contrato vivo de modelagem, vigência, atividade, investimentos, recursos e cálculo |
| [PLAYBOOK-18-instancias-filial-setor-escopo.md](./PLAYBOOK-18-instancias-filial-setor-escopo.md) | Refatoração: instâncias operacionais, filiais/setores UUID, escopo híbrido de recursos, visões consolidado/filial/dept |
| [PLAYBOOK-19-diagramas-processo-revisao-escopo.md](./PLAYBOOK-19-diagramas-processo-revisao-escopo.md) | Diagramas macro, escopo por instância, overlay por revisão (Playbook 19) |
| [playbook-19-implementation-status.md](../../../transformometro-api/docs/playbook-19-implementation-status.md) | Status técnico S0–S6 (API + MFE) |
| [adr-diagramas-processo.md](../../../transformometro-api/docs/adr-diagramas-processo.md) | ADR diagramas — decisões e endpoints |
| [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md) | Status técnico S1–S12 + MFE §9 (API) |
| [regras-de-calculo.md](../../../transformometro-api/docs/regras-de-calculo.md) | Fórmulas oficiais + escopo de recurso e visões |
| [status-atual.md](./status-atual.md) | Snapshot do que está em produção / deploy |
| [ROADMAP.md](./ROADMAP.md) | Fases de entrega e Playbook 18 |
| [ESPECIFICACAO.md](./ESPECIFICACAO.md) | Especificação funcional (planilha + Apps Script) |
| [OPERATIONS.md](./OPERATIONS.md) | Runbook operacional e deploy Playbook 18 |
| [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md) | Docker, compose, migrations, checklist |

## Estado atual no monorepo (jun/2026)

**Fonte de verdade:** schema `transformometro` no Postgres (`postgres-plugins`). Cadastro, cálculo e cache materializado vivem em `transformometro-api` + plugin `plugins/transformometro`.

| Peça | Situação |
|------|----------|
| **transformometro-api** | API canônica — CRUD, dashboard, diagramas (V026–V028), integração S2S, migrations **V001–V028** |
| **plugins/transformometro** | UI oficial — cadastro, dashboard (3 visões), filiais, diagramas BPMN-lite, backup JSON |
| **Cálculo** | `DashboardCalculatorService` em `tm_app/domain/services/` (+ testes golden) |
| **Integração Transforma+** | api-delpi `GET /engineering/transforma-mais/*` → `TransformometroTransformaMaisGateway` → Postgres |
| **Strategic Indicators** | KPI engenharia via `DelpiEngineeringGateway` → api-delpi (não lê Sheets nem SQL local) |
| **dashboard-engineering** | `TransformaPage` ativa — somente leitura; mesmas rotas api-delpi, dados do Postgres |

```text
plugins/transformometro ──JWT──► transformometro-api ──► Postgres
dashboard-engineering     ──JWT──► api-delpi ──S2S──► transformometro-api ──► Postgres
strategic-indicators-api  ──JWT──► api-delpi ──S2S──► transformometro-api ──► Postgres
```

## Legado remanescente (não usado em runtime)

| Peça | Situação |
|------|----------|
| Planilha Google Sheets | **Fora do pipeline** — pode existir como arquivo histórico; escrita ainda não desligada (ops) |
| `api-delpi/.../google_sheets/transforma_mais/process_repository.py` | Código morto — **não** ligado ao `engineering_composer` |
| `TRANSFORMA_MAIS_SHEET_*` em `infra/.env` | Variáveis órfãs — sem consumidor no código |
| `ProcessSummaryCalculator` (SI/api-delpi) | **Removido** — substituído por `DashboardCalculatorService` |
| Rotas `/engineering/transforma-mais/*` | Nomes de contrato **mantidos**; implementação já é Postgres via gateway |

Migração inicial de dados: backup JSON (`import_cadastro_json.py`), não importação contínua de planilha.

## Referências

- Modelagem e fórmulas: [documentos/documentacao_modelagem_transformometro.md](../../../documentos/documentacao_modelagem_transformometro.md)
- Rotas legado Transforma+: [documentos/Routes/documentacao_rota_transforma_mais.md](../../../documentos/Routes/documentacao_rota_transforma_mais.md)
