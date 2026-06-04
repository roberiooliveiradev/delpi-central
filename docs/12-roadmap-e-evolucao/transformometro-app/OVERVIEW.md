# Visão geral — Transformômetro App

**Última atualização:** 2026-05-27 (duplicar processo; URLs processo/revisão; ativar revisão sem workflow)

## O que é

O **Transformômetro** registra melhorias de processos (baseline vs melhoria/automação/correção), medições operacionais, investimentos e recursos compartilhados, e responde:

> Quanto a melhoria economizou, quanto custou implantar/manter e em quanto tempo o investimento se paga?

Hoje isso vive em **Google Sheets + Apps Script**. A meta é uma aplicação web na **Minha Delpi**:

- **API própria** (`transformometro-api`)
- **Plugin MFE** (`plugins/transformometro`)
- **PostgreSQL** como fonte de verdade
- **Autenticação e permissões** via Core API / Keycloak (mesmo modelo do SI)

## Componentes

| Peça | Pasta | URL (gateway) |
|------|-------|---------------|
| API | `transformometro-api/` (`tm_app`) | `/apps/transformometro-api/` |
| Rotas de negócio | prefixo `/transformometro` | `/apps/transformometro-api/transformometro/*` |
| MFE (UI) | `plugins/transformometro/` | `/apps/transformometro/` |
| Banco | schema `transformometro` em `postgres-plugins` | `PLUGINS_DB_*` |
| Cadastro de dados | CRUD na API + telas do MFE | Postgres como fonte de verdade |

### Rotas do MFE (menu e abas superiores)

| Rota | Função |
|------|--------|
| `/apps/transformometro/dashboard` | KPIs, alertas, export CSV/Excel, recalcular |
| `/apps/transformometro/processos` | Lista de processos (ação **Duplicar** na lista) |
| `/apps/transformometro/processos/{id}` | Detalhe do processo |
| `/apps/transformometro/processos/{id}/revisoes/{revisaoId}` | Detalhe com revisão selecionada |
| `/apps/transformometro/recursos` | Catálogo global de recursos compartilhados |

No detalhe da revisão: abas **Vigência**, **Medição**, **Investimentos**, **Recursos** (vínculos) e botão **Definir como ativa** (como na planilha legado — sem etapa de aprovação).

## Fluxo do usuário

```text
Portal MinhaDelpi
  → Core API (apps, permissões, menu)
  → Carrega MFE transformometro (Module Federation)
  → JWT no Authorization
  → CRUD processos / revisões / medições / investimentos / recursos
  → POST /dashboard/recalcular (ou recálculo automático em background)
  → GET /dashboard, /dashboard/resumo, detalhe por processo
  → UI: cadastro + dashboard com filtros (filial, setor, período)
```

## Unidade central de análise

Tudo gira em torno de **`revisao_id`**:

- `processos` = cadastro mestre
- `revisoes` = cenários (baseline, melhoria, automacao, correcao); uma pode estar **ativa** por processo
- `medicoes`, `investimentos`, vínculos de recurso = dados da revisão
- `dashboard_calculos` = tabela **derivada** (nunca editada manualmente)

## O que não é

- **Não** é extensão do painel Strategic Indicators — o SI e o `api-delpi` consomem dados via HTTP na `transformometro-api` (rotas `/integrations/engineering/transforma-mais/*`).
- O `dashboard-engineering` (TRANSFORMA+) usa as mesmas rotas `/engineering/transforma-mais/*`, agora alimentadas pelo banco.
- **Não** usa planilha como fonte de dados (cadastro somente no app).

## Permissões (manifesto — proposta)

| Código | Uso |
|--------|-----|
| `transformometro.view` | Dashboard e listagens |
| `transformometro.processes.manage` | CRUD processos |
| `transformometro.revisions.manage` | CRUD revisões, ativar revisão |
| `transformometro.measurements.manage` | Medições |
| `transformometro.investments.manage` | Investimentos |
| `transformometro.shared-resources.manage` | Recursos e vínculos |
| `transformometro.dashboard.recalculate` | Disparar recálculo mensal |
| `transformometro.data.transfer` | Exportar / importar backup JSON |

## Stack alinhada ao monorepo

| Camada | Escolha |
|--------|---------|
| API | **Python 3.11 + FastAPI** (igual `strategic-indicators-api`) |
| Domínio | Pacote `tm_app` (entities, use cases, ports, services) |
| ORM / SQL | SQLAlchemy 2 ou repositórios SQL + migrations SQL versionadas |
| MFE | **Vite + React 19 + Module Federation** |
| UI | Design system Delpi / padrão dos plugins existentes |
| Auth | JWT middleware `delpi_auth` / shared FastAPI |

A especificação original sugere NestJS; no Delpi Central o padrão consolidado é **FastAPI** para APIs de plugin.

## Reaproveitamento imediato

Código e regras já validados:

- `strategic-indicators-api/si_app/domain/services/transforma_mais/process_summary_calculator.py`
- DTOs e entidades `transforma_mais` em `si_app` / `api-delpi`
- Documentação de modelagem em `documentos/documentacao_modelagem_transformometro.md`

Na extração, o calculador vira pacote compartilhado ou cópia em `tm_app/domain/services/` com testes de regressão contra casos da planilha.

## Diferença importante: spec vs API Transforma+ atual

A [especificação](./ESPECIFICACAO.md) define:

```text
economia_liquida_mes = economia_bruta - custo_recorrente_mes
```

(com investimento único no ROI/payback acumulado)

A rota legada `transforma-mais` na listagem usa, para **economia/dia**:

```text
líquido ≈ economia_operacional - custo_recorrente - custo_compartilhado_atual
```

O app novo deve seguir a **especificação** (incluindo `economia_recursos_compartilhados` como delta baseline↔atual na economia bruta) e documentar breaking changes para quem migrar do dashboard engineering.

## Documentação relacionada

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ROADMAP.md](./ROADMAP.md)
- [ESPECIFICACAO.md](./ESPECIFICACAO.md)
