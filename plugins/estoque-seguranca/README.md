# Estoque de Segurança — plugin Minha DELPI

Microfrontend (Module Federation) para análise de matérias-primas versus estoque de segurança, com detalhe em **modal central** contendo cobertura de compras, empenhos, extrato projetado de saldo e fornecedores vinculados.

API: [api-delpi/docs/api/estoque-seguranca.md](../../api-delpi/docs/api/estoque-seguranca.md).

---

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `estoque-seguranca` | Listagem, KPIs, modal de detalhe com extrato |
| **api-delpi** `/supplies/safety-stock/*` | SB1/SBZ/SB2 + SC7 + SD4 + SA5/SA2/SD1 (empresa 01) |
| **plugin-ui** | Modal de página (`createModalShell` variante `page`) + DataTable |

```text
Portal → /apps/estoque-seguranca
           ↓ Module Federation
         MFE estoque-seguranca
           ↓ JWT + X-Delpi-Caller-App: estoque-seguranca
Gateway → /apps/api-delpi/supplies/safety-stock/*
```

---

## Funcionalidades

- Filtros por filial, grupo, unidade, situação e busca
- KPIs e déficit por unidade (sem somar UMs distintas)
- Tabela paginada de MPs
- Clique na linha abre **modal central** (não drawer lateral) com:
  - identificação e saldos físicos
  - projeção (físico + compras − empenhos)
  - cobertura por pedidos SC7
  - extrato cronológico consolidado (01+98+99) — única tabela de movimentos:
    empenhos (SD4) como saída e pedidos (SC7) como entrada, com referência
    `pedido/item - fornecedor` para compras e cores por sinal
  - fornecedores vinculados (SA5) com última compra (SD1), em carga independente
  - ao clicar no fornecedor: gráfico de oscilação do preço unitário nos últimos 12 meses

---

## Rotas da UI

| Path | Descrição |
|------|-----------|
| `/apps/estoque-seguranca` | Página principal |

---

## API (gateway)

Base: **`/apps/api-delpi/supplies/safety-stock`**

| Método | Rota | Uso |
|--------|------|-----|
| GET | `/filters` | Opções de filtro + filiais autorizadas |
| GET | `/summary` | KPIs |
| GET | `/items` | Tabela paginada |
| GET | `/items/{code}/details` | Modal de detalhe + extrato |
| GET | `/items/{code}/suppliers` | Fornecedores vinculados + última compra |
| GET | `/items/{code}/suppliers/{supplierCode}/purchase-price-history` | Histórico de preço (12 meses) ao clicar no fornecedor |

### Semântica do detalhe

- Déficit físico: só saldo 01+98+99 × ESTSEG
- Empenho: `D4_QUANT` (saldo atual aberto); `D4_DATA` = data do empenho
- Extrato: saldo inicial hoje → saídas SD4 → entradas SC7, acumulado por data
- Fornecedores: amarração SA5; última compra por `D1_DTDIGIT` (campos de compra nulos se sem NF)

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
