# Emissão de Notas Fiscais — plugin Minha DELPI

Microfrontend federado para **solicitar, acompanhar e concluir** a emissão de notas fiscais de saída: wizard guiado (destinatário TOTVS, itens, tipo, transporte e observação) e fila de atendimento do Faturamento.

## Deprecação (soft cutover E12)

O fluxo **canônico** é **[Minhas Solicitações](/apps/my-requests)** (`plugins/my-requests` + `requests-api`).

- Novas solicitações: `/apps/my-requests/new?type=invoice-issuance`
- **Menu oculto** (`showInMenu: false`) — tile canônico = Minhas Solicitações
- URL direta `/apps/invoice-issuance/*` ainda sobe o MFE (banner de aviso) até o hard descomission (E13)
- Schema `invoice_issuance` e rotas api-delpi de **lookup** **não** foram removidos (adapter do requests-api)
- Guia de procedimentos: `emissao-nota-fiscal` aponta para my-requests
- Runbook de migração: [`MIGRATION-RUNBOOK.md`](../../docs/12-roadmap-e-evolucao/my-requests/MIGRATION-RUNBOOK.md)
- Gate prod: [`PARITY-P0.md`](../../docs/12-roadmap-e-evolucao/my-requests/PARITY-P0.md) § Gate soft cutover

Documentação de roadmap: [docs/12-roadmap-e-evolucao/invoice-issuance/](../../docs/12-roadmap-e-evolucao/invoice-issuance/) · API: [invoice-issuance.md](../../api-delpi/docs/api/invoice-issuance.md).

Este plugin é **separado** do [Lançamento de Notas Fiscais](../lancamento-notas-fiscais/README.md) (entrada / SF1). Aqui **não** há conciliação Protheus (SF2) nesta versão.

---

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `invoice-issuance` | Wizard de 6 etapas, fila, detalhe (ficha única com destinatário, transporte SA4 e itens) |
| **api-delpi** `/invoice-issuance/*` | CRUD operacional + lookups TOTVS + RBAC por filial |
| **postgres-plugins** | Schema `invoice_issuance` (solicitações, itens, histórico) |
| **TOTVS** | Destinatário `SA1`/`SA2`; itens `SB1`; saldo informativo `SB2` local `01`; PV em aberto do cliente; transportadora `SA4` (nome de uso, razão, CNPJ, endereço, telefone) |

```text
Portal → /apps/invoice-issuance/filial-0x
           ↓ Module Federation (remoteEntry.js)
         MFE invoice-issuance
           ↓ JWT + X-Delpi-Caller-App: invoice-issuance
Gateway → /apps/api-delpi/invoice-issuance/*
           ↓
         api-delpi → Postgres (plugins) + SQL Server (SA1/SA2/SB1/SB2/SA4)
```

**Sem API própria:** o MFE chama a api-delpi (exceção legítima do checklist MFE + BFF).

---

## Funcionalidades

- Wizard: destinatário cadastrado (cliente ou fornecedor), tipo de NF (venda/devolução já marcam baixa de estoque), itens a partir de **pedido de venda em aberto** (cliente) ou busca SB1, CIF/FOB, transportadora SA4 opcional, peso/volumes, observação opcional e conferência automática
- Fila por filial (`01` SC / `02` ES), primeiro nome do solicitante, filtros de status/tipo/destinatário e deep link `?requestId=`
- Atendimento: iniciar, devolver (motivo), marcar emitida, cancelar
- Notificação no sino: criação/reenvio para `invoice-issuance.process`; devolução/emissão/cancelamento para o solicitante

---

## Rotas da UI

| View | Conteúdo |
|------|----------|
| Fila | Lista + filtros |
| Nova / Corrigir | Wizard de 6 etapas |
| Detalhe | Um card compacto (destinatário, tipo/PV, frete + contato da transportadora, peso/volumes, itens) + ações no topo; histórico recolhido |

| Rota | Permissão de menu |
|------|-------------------|
| `/apps/invoice-issuance/filial-01` | `invoice-issuance.view.filial-01` |
| `/apps/invoice-issuance/filial-02` | `invoice-issuance.view.filial-02` |

---

## API (gateway)

Base HTTP: **`/apps/api-delpi/invoice-issuance`**

Ver [invoice-issuance.md](../../api-delpi/docs/api/invoice-issuance.md).

---

## Permissões

| Código | Uso |
|--------|-----|
| `invoice-issuance.access` | Abrir o plugin |
| `invoice-issuance.create` | Solicitar, corrigir devolvida, cancelar própria `pending` |
| `invoice-issuance.view` | Consultar ambas as filiais |
| `invoice-issuance.view.filial-01` / `.filial-02` | Menu + gate de filial |
| `invoice-issuance.process` | Atender (start/return/issue/cancel em atendimento) |
| `invoice-issuance.manage` | Administrar |

---

## Dev / smoke

```bash
cd plugins/invoice-issuance
npm install
npm test
npm run build

docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin invoice-issuance
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin invoice-issuance

./infra/scripts/up-dev-sequential.sh --fase mfe --build invoice-issuance
```

**Nunca** `reset --plugin invoice-issuance` em ambiente com dados reais.

Registro na Core API (depois do manifesto no Compose):

```bash
curl -s -X POST http://localhost/core-api/admin/apps/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @plugins/invoice-issuance/invoice-issuance.manifest.json
```

RBAC no Portal é passo seguinte — ver [registrar-plugin.md](../../docs/10-guias-operacionais/registrar-plugin.md).
