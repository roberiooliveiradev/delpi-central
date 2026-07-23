# Estoque de Segurança — plugin Minha DELPI

Microfrontend (Module Federation) para monitoramento de matérias-primas versus estoque de segurança e **simulação gerencial do ESTSEG sugerido** com base no consumo real (baixas SD3) e lead time `BZ_PE`.

API: [api-delpi/docs/api/estoque-seguranca.md](../../api-delpi/docs/api/estoque-seguranca.md).

---

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `estoque-seguranca` | Monitoramento + análise de consumo |
| **api-delpi** `/supplies/safety-stock/*` | SB1/SBZ/SB2 + SC7 + SD4 + SD3 + SA5/SA2/SD1 |
| **plugin-ui** | Modal, DataTable, KPI e gráficos |

```text
Portal → /apps/estoque-seguranca[/analise-consumo]
           ↓ Module Federation
         MFE estoque-seguranca
           ↓ JWT + X-Delpi-Caller-App: estoque-seguranca
Gateway → /apps/api-delpi/supplies/safety-stock/*
```

---

## Funcionalidades

### Monitoramento (`/apps/estoque-seguranca`)

- Filtros por filial, grupo, unidade, situação e busca
- KPIs e déficit por unidade
- Modal com projeção SC7/SD4, extrato e fornecedores

### Análise de consumo (`/apps/estoque-seguranca/analise-consumo`)

- Produtos com `BZ_ESTSEG <> 0` e baixas elegíveis nos últimos 12 meses
- Consumo médio diário útil (SD3 local 99, TM 999, OP preenchida)
- ESTSEG sugerido = consumo médio × dias úteis do lead time (`BZ_PE`)
- KPIs, distribuição, tabela comparativa e detalhe com série mensal / comparativo anual
- Simulação **somente leitura** (não grava no Protheus)

---

## Rotas da UI

| Path | Descrição |
|------|-----------|
| `/apps/estoque-seguranca` | Monitoramento (saldo × ESTSEG) |
| `/apps/estoque-seguranca/analise-consumo` | Análise/simulação por consumo e lead time |

---

## API (gateway)

Base: **`/apps/api-delpi/supplies/safety-stock`**

| Método | Rota | Uso |
|--------|------|-----|
| GET | `/filters` | Opções de filtro + filiais autorizadas |
| GET | `/summary` | KPIs do monitoramento |
| GET | `/items` | Tabela paginada do monitoramento |
| GET | `/items/{code}/details` | Modal de detalhe + extrato |
| GET | `/items/{code}/suppliers` | Fornecedores vinculados + última compra |
| GET | `/items/{code}/suppliers/{supplierCode}/purchase-price-history` | Histórico de preço (12 meses) |
| GET | `/consumption-analysis/summary` | KPIs da simulação |
| GET | `/consumption-analysis/items` | Tabela da simulação |
| GET | `/consumption-analysis/items/{code}` | Série mensal + memória de cálculo |

### Semântica do detalhe (monitoramento)

- Déficit físico: só saldo 01+98+99 × ESTSEG
- Empenho: `D4_QUANT` (saldo atual aberto); data no extrato = `C2_DATPRI` da OP do empenho (`D4_OP`)
- Extrato: saldo inicial hoje → saídas SD4 → entradas SC7, acumulado por data
- Fornecedores: amarração SA5; última compra por `D1_DTDIGIT`

### Semântica da análise de consumo

- Janela: 365 dias corridos inclusivos (SQL e denominador alinhados)
- Dias úteis: segunda–sexta, sem feriados
- Lead time: `BZ_PE` em dias corridos, convertido para dias úteis na janela futura
- Cobertura: saldo disponível ÷ consumo médio diário útil

---

## Permissões

| Código | Escopo |
|--------|--------|
| `estoque-seguranca.access` | Acesso |
| `estoque-seguranca.view.filial-sc` | Filial 01 |
| `estoque-seguranca.view.filial-es` | Filial 02 |

---

## Desenvolvimento

```bash
cd plugins/estoque-seguranca
npm install
npm test
npm run build
```

Rebuild federado (dev):

```bash
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build estoque-seguranca
```

---

## Estrutura `src/`

| Pasta | Conteúdo |
|-------|----------|
| `pages/` | `SafetyStockPage` |
| `components/` | Tabela, filtros, `SafetyStockDetailModal` |
| `api/` | Cliente HTTP |
| `hooks/` | Listagem, summary, detalhe abortável |
| `types/` | Contrato do detalhe composto |
