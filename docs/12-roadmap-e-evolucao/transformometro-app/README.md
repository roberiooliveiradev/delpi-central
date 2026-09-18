# Transformômetro — aplicação Minha Delpi

Documentação de arquitetura e plano de entrega do **Transformômetro** como produto independente no monorepo Delpi Central (API dedicada + plugin microfrontend), no mesmo padrão do [Strategic Indicators](../../../strategic-indicators-api/docs/README.md).

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| **[TUTORIAL-USUARIO.md](./TUTORIAL-USUARIO.md)** | **Guia prático de uso** — cadastro, workspaces Processos/Configurações, diagramas, mapeamento WBS, revisões, matriz, dashboard, UI |
| [OVERVIEW.md](./OVERVIEW.md) | Visão geral, objetivo, componentes, URLs, permissões |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Camadas, domínio, cálculo, banco, integração portal |
| [PLAYBOOK-MODELAGEM.md](./PLAYBOOK-MODELAGEM.md) | Contrato vivo de modelagem, vigência, atividade, investimentos, recursos e cálculo |
| [PLAYBOOK-18-instancias-filial-setor-escopo.md](./PLAYBOOK-18-instancias-filial-setor-escopo.md) | Refatoração: instâncias operacionais, filiais/setores UUID, escopo híbrido de recursos, visões consolidado/filial/dept |
| [PLAYBOOK-19-diagramas-processo-revisao-escopo.md](./PLAYBOOK-19-diagramas-processo-revisao-escopo.md) | Diagramas macro, escopo por instância, overlay por revisão (Playbook 19) |
| [PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md](./PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md) | Árvore de decomposição, export planilha, vínculo com fluxo (Playbook 20) |
| [PLAYBOOK-21-matriz-impacto-esforco-revisao.md](./PLAYBOOK-21-matriz-impacto-esforco-revisao.md) | Matriz impacto × esforço por revisão (Playbook 21) |
| [PLAYBOOK-23-decomposicao-composicao-macro-data.md](./PLAYBOOK-23-decomposicao-composicao-macro-data.md) | Macro composto por vigência, delta estrutural, âncora na referência, limites multi-melhoria |
| [playbook-21-implementation-status.md](../../../transformometro-api/docs/archive/playbooks/playbook-21-implementation-status.md) | Status técnico Playbook 21 (S0–S4) |
| [playbook-19-implementation-status.md](../../../transformometro-api/docs/archive/playbooks/playbook-19-implementation-status.md) | Status técnico S0–S6 (API + MFE) |
| [playbook-20-implementation-status.md](../../../transformometro-api/docs/archive/playbooks/playbook-20-implementation-status.md) | Status técnico Playbook 20 (S0–S6) |
| [adr-diagramas-processo.md](../../../transformometro-api/docs/architecture/adr-diagramas-processo.md) | ADR diagramas — decisões e endpoints |
| [playbook-18-implementation-status.md](../../../transformometro-api/docs/archive/playbooks/playbook-18-implementation-status.md) | Status técnico S1–S12 + MFE §9 (API) |
| [regras-de-calculo.md](../../../transformometro-api/docs/domain/regras-de-calculo.md) | Fórmulas oficiais + escopo de recurso e visões |
| [status-atual.md](./status-atual.md) | Snapshot jul/2026. Não cobre Portal Transforma+ nem contagens atuais de MCP/Actions |
| [ATAS-TRANSFORMA-MAIS.md](./ATAS-TRANSFORMA-MAIS.md) | Atas Transforma+ — fluxo, RBAC, status (incl. Kimi) |
| [meeting-minutes.md (MFE)](../../../plugins/transformometro/docs/meeting-minutes.md) | UI das atas no plugin |
| [kimi.md (API)](../../../transformometro-api/docs/meeting-minutes/kimi.md) | Endpoints + configuração OpenRouter/Kimi |
| [gpt-actions/](../../../transformometro-api/docs/gpt-actions/) | Custom GPT OpenAI (Actions + especialista) |
| [docs API (índice)](../../../transformometro-api/docs/README.md) | Índice da documentação da transformometro-api |
| [ROADMAP.md](./ROADMAP.md) | Fases de entrega e Playbook 18 |
| **[CICLO-INTELIGENCIA-DE-PROCESSO.md](./CICLO-INTELIGENCIA-DE-PROCESSO.md)** | **Alvo de produto** — ciclo mapeamento → diagnóstico → TO-BE → medição → aprendizado. Não é runtime. |
| **[PORTAL-TRANSFORMA-PLUS.md](./PORTAL-TRANSFORMA-PLUS.md)** | **Portal Transforma+** — experiência e IA sobre o domínio Transformômetro. Comercial é referência de UX, não fonte de regra. Não é runtime. |
| **[ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md)** | **Ordem de implementação** — decisões caras, waves, DoR/DoD e pacote. Única fonte de sequência. Não autoriza código. |
| **[WAVE-1-IMPLEMENTATION-PACKET.md](./WAVE-1-IMPLEMENTATION-PACKET.md)** | Pacote da Wave 1. IMPLEMENTED_NOT_RUNTIME_PROVEN. Browser smoke ainda TEST_NOT_RUN. |
| **[AUTHZ-SIMPLIFICATION.md](./AUTHZ-SIMPLIFICATION.md)** | Inventário de permissões e alvo multiunidade. AUTHZ_MIGRATION = NOT_READY. Não autoriza código. |
| **[AUTHZ-FINAL-DESIGN.md](./AUTHZ-FINAL-DESIGN.md)** | Desenho final. Core autoriza. Unidade é objeto do Portal. READY_FOR_ARCH_REVIEW. |
| **[CORE-APP-UNIT-SCOPE-PACKET.md](./CORE-APP-UNIT-SCOPE-PACKET.md)** | Pacote da fase 1 no Core. Não autoriza código. |
| **[PLAYBOOK-PORTAL-TRANSFORMA.md](./PLAYBOOK-PORTAL-TRANSFORMA.md)** | Inventário de portal (2026-09-17). A sequência vigente está no runway, não nas fases 0–6 deste playbook. |
| [ESPECIFICACAO.md](./ESPECIFICACAO.md) | Especificação funcional (planilha + Apps Script) |
| [OPERATIONS.md](./OPERATIONS.md) | Runbook operacional e deploy Playbook 18 |
| [DEPLOYMENT.md](../../../transformometro-api/docs/operations/DEPLOYMENT.md) | Docker, compose, migrations, checklist |

## Estado atual no monorepo (jul/2026)

**Fonte de verdade:** schema `transformometro` no Postgres (`postgres-plugins`). Cadastro, cálculo e cache materializado vivem em `transformometro-api` + plugin `plugins/transformometro`.

| Peça | Situação |
|------|----------|
| **transformometro-api** | API canônica — CRUD, dashboard, diagramas (V026–V028), mapeamento WBS (V030–V033), melhorias V034, **referência de revisão V035**, **matriz V038**, **duplicar revisão**, integração S2S, migrations **V001–V038** |
| **plugins/transformometro** | UI oficial — **workspaces** Processos + Configurações, dashboard (3 visões), diagramas BPMN-lite + Mermaid bidirecional, matriz impacto×esforço, mapeamento WBS, backup JSON, **SelectField**, **modal de confirmação**, aliases PT-BR de cenários |
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
