# Visão geral — Transformômetro App

**Última atualização:** jun/2026 (Playbook 18 — instâncias, visões dashboard, RBAC filial)

## O que é

O **Transformômetro** registra melhorias de processos (baseline vs melhoria/automação/correção), medições operacionais, investimentos e recursos compartilhados, e responde:

> Quanto a melhoria economizou, quanto custou implantar/manter e em quanto tempo o investimento se paga?

Origem histórica: **Google Sheets + Apps Script**. Hoje a aplicação web na **Minha Delpi** já está entregue no monorepo:

- **API própria** (`transformometro-api`) — fonte de verdade no **PostgreSQL**
- **Plugin MFE** (`plugins/transformometro`) — cadastro e dashboard oficiais
- **Autenticação e permissões** via Core API / Keycloak (mesmo modelo do SI)
- Consumidores legados (SI, `dashboard-engineering`) leem o **mesmo Postgres** via rotas `transforma-mais` na api-delpi (proxy S2S)

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
| `/apps/transformometro/dashboard` | KPIs, toggle Consolidado/Filial/Departamento, alertas, export, recalcular |
| `/apps/transformometro/processos` | Lista; create com primeira instância |
| `/apps/transformometro/processos/{id}` | Mestre + painel instâncias + revisões |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}/revisoes/{revisaoId}` | URL canônica da revisão |
| `/apps/transformometro/processos/{id}/revisoes/{revisaoId}` | Legado (redirect automático) |
| `/apps/transformometro/filiais` | CRUD de filiais |
| `/apps/transformometro/setores` | Catálogo de setores |
| `/apps/transformometro/recursos` | Catálogo global (`escopo_recurso`) |
| `/apps/transformometro/dados` | Export/import backup JSON |

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
  → UI: cadastro + dashboard com filtros (visão, filial, setor, período)
```

## Unidade central de análise

Tudo gira em torno de **`revisao_id`**, sempre vinculada a uma **`instancia_id`** (processo × filial ou `todas_filiais_ativas`, com N setores):

- `processos` = cadastro **mestre** (sem filial/setor na tabela)
- `processo_instancias` = unidade operacional do mestre (filial + `todas_filiais_ativas`)
- `processo_instancia_setores` = N setores por instância (junction V019)
- `revisoes` = cenários por instância (baseline, melhoria, automacao, correcao)
- `medicoes`, `investimentos`, vínculos de recurso = dados da revisão
- `dashboard_calculos` = tabela **derivada** (nunca editada manualmente)

Integração Transforma+: **`id` na listagem = `instancia_id`** (uma linha por instância operacional).

## O que não é

- **Não** é extensão do painel Strategic Indicators — o SI e o `dashboard-engineering` consomem Transforma+ via **api-delpi** (`GET /engineering/transforma-mais/*`). A transformometro-api expõe rotas S2S internas (`/integrations/engineering/transforma-mais/*`) só para o gateway api-delpi. Ver [`transformometro-api/docs/integration-contracts.md`](../../../transformometro-api/docs/integration-contracts.md).
- O `dashboard-engineering` (TRANSFORMA+) continua ativo como painel **somente leitura**; usa `/engineering/transforma-mais/*` na api-delpi, que faz proxy para o Postgres.
- **Não** usa planilha Google como fonte de dados em runtime (cadastro somente no app / API).

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
| `transformometro.view.filial-01` / `filial-02` | Leitura filtrada à filial (RBAC S10) |
| `transformometro.view.consolidated` | Visão consolidada com escopo filial ativo |
| `transformometro.manage.filial-01` / `filial-02` | CRUD na filial |

Usuários só com permissões globais legadas **não** têm restrição de filial até receberem escopos no Keycloak. Ver manifesto `plugins/transformometro/transformometro.manifest.json`.

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

## Reaproveitamento (concluído)

| Origem legada | Destino atual |
|---------------|---------------|
| Regras da planilha / Apps Script | `DashboardCalculatorService` + `regras-de-calculo.md` |
| `ProcessSummaryCalculator` (SI/api-delpi) | **Removido** do SI; lógica em `tm_app/domain/services/dashboard_calculator.py` |
| DTOs `transforma_mais` na api-delpi | **Mantidos** — contrato HTTP estável; gateway `TransformometroTransformaMaisGateway` mapeia resposta do Postgres |
| Modelagem | `documentos/documentacao_modelagem_transformometro.md` (referência histórica + regras) |

Testes de regressão: `tests/test_dashboard_calculator.py`, fixtures JSON, `scripts/ci-transformometro-api.sh`.

## Diferença histórica: spec vs calculador Sheets

A [especificação](./ESPECIFICACAO.md) e o **app atual** usam:

```text
economia_liquida_mes = economia_bruta - custo_recorrente_mes
```

(com delta de recursos na economia bruta; investimento único no ROI/payback)

O calculador antigo da planilha, na listagem, subtraía o **custo compartilhado inteiro** na economia diária. Quem compara números com a planilha antiga deve esperar divergência documentada — o Postgres segue a spec. Rotas `transforma-mais` na api-delpi já refletem o calculador da transformometro-api.

## Documentação relacionada

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ROADMAP.md](./ROADMAP.md)
- [ESPECIFICACAO.md](./ESPECIFICACAO.md)
