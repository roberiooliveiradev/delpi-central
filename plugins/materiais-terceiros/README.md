# Materiais de Terceiros — plugin Minha DELPI

Microfrontend (Module Federation) para acompanhar remessas e pendências
de materiais de clientes/fornecedores, incluindo carretéis de fornecedores,
e os retornos vinculados (`SB6` / view
`dbo.VW_PD3_BENEF_RETORNOS`).

API: [api-delpi/docs/api/materiais-terceiros.md](../../api-delpi/docs/api/materiais-terceiros.md).  
Padrões TOTVS: [padroes-totvs/materiais-terceiros-sb6.md](../../api-delpi/docs/api/padroes-totvs/materiais-terceiros-sb6.md).

---

## Visão geral

```text
Portal → /apps/materiais-terceiros
           ↓ Module Federation
         MFE materiais-terceiros
           ↓ JWT + X-Delpi-Caller-App: materiais-terceiros
Gateway → /apps/api-delpi/supplies/third-party-materials/*
```

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** | Filtros, KPIs, grade de remessas, detalhe de retornos, exportação |
| **api-delpi** | Consulta somente leitura à view TOTVS, RBAC por filial |
| **plugin-ui** | FilterBar, DataTable, KPI, modal host-contained |

---

## Funcionalidades

- Seletor de filial (apenas filiais autorizadas no JWT)
- Visões **Consolidado de pendências** (aberta por padrão) e **Remessas e devoluções**.
- Filtros: produto, ref. cliente (`SB1.B1_REFEREN`), parceiro/loja (SA1 cliente ou SA2 fornecedor), NF recebimento, NF retorno, período, status, somente saldo, produtos de teste.
- No consolidado aparecem apenas os filtros realmente aplicados: filial, parceiro, loja, produto e produtos de teste (saldo aberto é obrigatório).
- Detalhes e exportação de remessas enriquecidos pelo cadastro SA2 para fornecedores, mantendo SA1 para clientes.
- KPIs sobre **remessas únicas** (não soma saldo repetido nas linhas de retorno)
- Grade paginada de remessas; detalhe em `HostContainedDialog`
- URL compartilhável (`branch`, `product`, `customerReference`, `status`, `onlyWithBalance`, `shipment`)
- Exportação CSV/XLSX via endpoint (todas as linhas do recorte, com aviso de saldo repetido)
- PDF da remessa no detalhe (layout certificado DELPI: logo, recebimento e devoluções)

A visão de **remessas** exige **filial + (produto, parceiro, ref. cliente, NF, período, status ou somente saldo)**. O consolidado é agregado no backend e consulta pendências abertas por filial, com filtro opcional de fornecedor/produto.

---

## API (gateway)

Base: **`/apps/api-delpi/supplies/third-party-materials`**

| Método | Rota | Uso |
|--------|------|-----|
| GET | `/summary` | KPIs |
| GET | `/pending-by-supplier` | Consolidado de saldos por fornecedor/loja/produto, paginado |
| GET | `/pending-by-supplier/export` | CSV/XLSX do consolidado (limite 20 mil registros, sem truncamento silencioso) |
| GET | `/shipments` | Lista paginada por remessa |
| GET | `/shipments/{shipment_recno}` | Detalhe + `returns[]` |
| GET | `/returns/export` | CSV/XLSX (`export_format`) |

Payload em `snake_case`. Status da API: `completed` \| `partial` \| `no_return`.

---

## Permissões

| Código | Uso |
|--------|-----|
| `materiais-terceiros.access` | Abrir o app + ambas filiais |
| `materiais-terceiros.view.filial-sc` | Filial 01 |
| `materiais-terceiros.view.filial-es` | Filial 02 |
| `materiais-terceiros.export` | Exportar CSV/XLSX |

---

## Execução standalone

```bash
cd plugins/plugin-ui && npm run dev

cd plugins/materiais-terceiros
VITE_PLUGIN_UI_DEV=1 \
VITE_DEV_ACCESS_TOKEN="$(bash ../../infra/scripts/get-dev-token.sh)" \
npm run dev
```

## Scripts

```bash
npm test          # vitest
npm run build     # tsc + vite
TOKEN=… ./scripts/register-manifest.sh
```

## Deploy

Após `plugin-ui`:

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build materiais-terceiros
```

Se a API mudou, rebuild `api-delpi` na fase core. A view TOTVS precisa estar aplicada em homologação **antes** do smoke live.

## Atualização em produção e conferência da versão visual

O frontend federado **não é atualizado** apenas por reconstruir `api-delpi`.
Depois do merge na `main`, com o checkout de produção atualizado e limpo:

```bash
cd /caminho/para/delpi-central
git switch main
git pull --ff-only origin main
./infra/scripts/up-prod-sequential.sh --build api-delpi
./infra/scripts/up-prod-sequential.sh --no-cache --fase mfe --build materiais-terceiros
```

O gateway publica `/apps/materiais-terceiros/assets/remoteEntry.js` com `Cache-Control: no-store`.
Valide o bundle dentro do container, sem alteração em produção:

```bash
docker exec delpi-materiais-terceiros sh -c 'grep -rl "Consolidado de pendências" /usr/share/nginx/html/assets/ | head -5'
```

O teste funcional é abrir `/apps/materiais-terceiros`, carregar a versão atual (Ctrl+F5 se havia aba aberta) e verificar as duas abas. Na filial 01, o fornecedor `001692`/loja `01` e produto `20050017` são o cenário de regressão dos carretéis. O saldo real pode mudar ao longo do dia.
