# Materiais de Terceiros — plugin Minha DELPI

Microfrontend (Module Federation) para acompanhar remessas de materiais de
clientes em beneficiamento e os retornos vinculados (`SB6` / view
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
- Filtros: produto, ref. cliente (`SB1.B1_REFEREN`), cliente/loja, NF recebimento, NF retorno, período, status, somente saldo, produtos de teste
- KPIs sobre **remessas únicas** (não soma saldo repetido nas linhas de retorno)
- Grade paginada de remessas; detalhe em `HostContainedDialog`
- URL compartilhável (`branch`, `product`, `customerReference`, `status`, `onlyWithBalance`, `shipment`)
- Exportação CSV/XLSX via endpoint (todas as linhas do recorte, com aviso de saldo repetido)
- PDF da remessa no detalhe (layout certificado DELPI: logo, recebimento e devoluções)

Não carrega a base sem critério: exige **filial + (produto, ref. cliente, NF, período ou somente saldo)**.

---

## API (gateway)

Base: **`/apps/api-delpi/supplies/third-party-materials`**

| Método | Rota | Uso |
|--------|------|-----|
| GET | `/summary` | KPIs |
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
