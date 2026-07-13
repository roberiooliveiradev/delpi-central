# Inspeções de Processo — plugin Minha DELPI

Microfrontend federado para **acompanhamento operacional** de inspeções em processo (QIP), com dados do **TOTVS Protheus** via **api-delpi**.

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `inspecoes-processo` | Dashboard por filial: Visão Geral, Histórico e Auditoria |
| **api-delpi** `/inspecoes-processo/*` | Leitura TOTVS (views `vw_minha_delpi_inspecoes_processo_*` + auditoria em EF/QP*/QPR) |
| **TOTVS** | Views de inspeção; apontamentos `vw_Apontamentos_Eficiencia`; QP7/QP8/QPR |

```text
Portal → /apps/inspecoes-processo/filial-01|02
           ↓ Module Federation (remoteEntry.js)
         MFE inspecoes-processo
           ↓ JWT + X-Delpi-Caller-App: inspecoes-processo
Gateway → /apps/api-delpi/inspecoes-processo/*
           ↓
         api-delpi → SQL Server
```

## Rotas da UI

| Path | Tela |
|------|------|
| `/apps/inspecoes-processo/filial-01` | Painel filial 01 (SC) |
| `/apps/inspecoes-processo/filial-02` | Painel filial 02 (ES) |

Abas (query):

| Aba | URL |
|-----|-----|
| Visão Geral | (sem `?tab`) |
| Histórico | `?tab=historico` |
| Auditoria | `?tab=auditoria` |

### Auditoria

Lista **todos** os apontamentos produtivos do dia e confronta se o **mesmo operador** inspecionou a mesma OP+operação no QIP (`QPR_ENSR` → login via ranking por ensaiador).

- Filtro de data (default: hoje)
- KPIs: total no dia, pendentes, operadores pendentes, OK
- Status: inspecionou / pendente (outra pessoa) / pendente (sem inspeção)

Regra detalhada: [ESPECIFICACAO-AUDITORIA-APONTAMENTOS.md](../../docs/12-roadmap-e-evolucao/inspecoes-processo/ESPECIFICACAO-AUDITORIA-APONTAMENTOS.md).

## API (gateway)

Base HTTP: **`/apps/api-delpi/inspecoes-processo`**

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/resumo` | KPIs da filial |
| GET | `/por-produto` | Ranking por produto |
| GET | `/por-ensaiador` | Ranking por ensaiador |
| GET | `/por-operacao` | Ranking por operação (API) |
| GET | `/ranking-ensaio` | Ranking por ensaio (API) |
| GET | `/historico` | Histórico paginado por OP (últimos 12 meses; exige OP ou produto) |
| GET | `/historico/detalhe` | Medições da OP |
| GET | `/auditoria-apontamentos` | Pendências apontamento × inspeção |

Todas exigem `branch=01|02`. Respostas no envelope padrão api-delpi.

Documentação: [api-delpi/docs/api/inspecoes-processo.md](../../api-delpi/docs/api/inspecoes-processo.md).

### Exemplo — auditoria

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-processo" \
     "http://localhost/apps/api-delpi/inspecoes-processo/auditoria-apontamentos?branch=01&data=$(date +%F)" \
  | jq '.success, .meta.operationId, .data.summary'
```

## Permissões

| Código | Uso |
|--------|-----|
| `inspecoes-processo.view.filial-01` | Menu e dados da filial 01 (SC) |
| `inspecoes-processo.view.filial-02` | Menu e dados da filial 02 (ES) |
| `inspecoes-processo.view` | Acesso amplo (ambas filiais) |

Na api-delpi, rotas de leitura aceitam também `api-delpi.access`. Escopo por filial é validado no router (`403` se o usuário não tiver permissão da filial solicitada).

## Estrutura do código (MFE)

```text
src/
  api/inspecoesProcessoApi.ts
  pages/
    FilialAppPage.tsx
    DashboardPage.tsx
    HistoricoPage.tsx
    AuditoriaPage.tsx
  hooks/useInspecoesProcessoAuditoria.ts
  components/AuditoriaTable.tsx
  utils/tabs.ts
```

## Build / smoke

```bash
# build local (Node 20+)
cd plugins/inspecoes-processo && npm ci && npm run build

# rebuild container (dev)
./infra/scripts/up-dev-sequential.sh --fase mfe --build inspecoes-processo
```

Após alteração na API, o serviço `delpi-api-delpi` precisa estar com o código atualizado (volume ou recreate).
