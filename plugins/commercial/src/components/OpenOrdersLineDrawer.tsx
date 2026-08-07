import { ActionButton, DataTable, StatusBadge } from "@delpi/plugin-ui/index";

import {
  CommercialDetailFieldGrid,
  CommercialDrawerShell,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmStatusBadgeClassNames,
} from "../app/commercialUi";
import { navigateCustomerDetail } from "../app/pluginNavigation";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatDisplayDate, resolveOpVsPedidoPrazo } from "../utils/dates";
import { formatQuantity } from "../utils/format";
import { getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { getLineStatus } from "../utils/statusBadges";

type OpenOrdersLineDrawerProps = {
  item: OpenOrdersTotvsItem | null;
  open: boolean;
  onClose: () => void;
  basePath?: string;
};

function prazoVariant(
  status: ReturnType<typeof resolveOpVsPedidoPrazo>["status"],
): "success" | "danger" | "neutral" {
  if (status === "no_prazo") return "success";
  if (status === "atrasado") return "danger";
  return "neutral";
}

function badgeVariant(
  tone: ReturnType<typeof getLineStatus>["tone"],
): "neutral" | "info" | "success" | "warning" | "danger" {
  if (tone === "success") return "success";
  if (tone === "warning") return "warning";
  if (tone === "danger") return "danger";
  if (tone === "info") return "info";
  return "neutral";
}

export function OpenOrdersLineDrawer({
  item,
  open,
  onClose,
  basePath,
}: OpenOrdersLineDrawerProps) {
  if (!item) return null;

  const previsao = getLineOpForecast(item);
  const lineStatus = getLineStatus(item);
  const description = `${item.nome_cliente || "Cliente"} · Pedido ${item.pedido || "—"} · Linha ${item.linha || "—"} · Produto ${item.produto || "—"}`;

  const copyPedido = async () => {
    const text = item.pedido?.trim();
    if (!text || typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      /* ignore */
    }
  };

  const openAccount = () => {
    const code = item.codigo_cadastro?.trim();
    const store = item.loja_cadastro?.trim();
    if (!code || !store) return;
    navigateCustomerDetail(code, store, { basePath });
    onClose();
  };

  return (
    <CommercialDrawerShell
      open={open}
      onClose={onClose}
      title="Detalhe da linha"
      description={description}
      footer={
        <div className="cm-drawer-footer-actions">
          <ActionButton variant="ghost" onClick={copyPedido}>
            Copiar pedido
          </ActionButton>
          <ActionButton
            variant="primary"
            onClick={openAccount}
            disabled={!item.codigo_cadastro?.trim() || !item.loja_cadastro?.trim()}
          >
            Abrir conta
          </ActionButton>
        </div>
      }
    >
      <div className="cm-open-orders-drawer">
        <CommercialDetailFieldGrid
          valueFallback="—"
          wrapLabels
          fields={[
            { label: "Saldo do pedido", value: formatQuantity(item.saldo) },
            {
              label: "Estoque alocado",
              value: formatQuantity(getAllocatedStock(item)),
            },
            {
              label: "Saldo a produzir",
              value: formatQuantity(previsao.saldoNecessarioProducao),
            },
            {
              label: "Entrega pedido",
              value: formatDisplayDate(item.data_entrega),
            },
            {
              label: "Previsão de entrega",
              value: previsao.previsaoLabel,
            },
            {
              label: "Pode faturar?",
              value: (
                <StatusBadge
                  classNames={cmStatusBadgeClassNames}
                  label={lineStatus.label}
                  variant={badgeVariant(lineStatus.tone)}
                />
              ),
            },
            ...(previsao.saldoFaltanteProducao > 0
              ? [
                  {
                    label: "Ainda falta produzir",
                    value: formatQuantity(previsao.saldoFaltanteProducao),
                  },
                ]
              : []),
          ]}
        />

        <p className="cm-open-orders-drawer__note">
          OPs compartilhadas por produto/filial, alocadas por ordem de entrega do pedido. Indicação
          operacional — não reserva formal ao cliente.
        </p>

        {previsao.opsUtilizadas.length > 0 ? (
          <DataTable
            rows={previsao.opsUtilizadas}
            rowKey={(row) => row.numero_op}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
            columns={[
              { key: "op", header: "Número OP", render: (row) => row.numero_op || "—" },
              {
                key: "saldo",
                header: "Saldo OP",
                align: "right",
                render: (row) => formatQuantity(row.saldo_op_total),
              },
              {
                key: "alocado",
                header: "Alocado p/ o pedido",
                align: "right",
                render: (row) => formatQuantity(row.saldo_alocado),
              },
              {
                key: "fim",
                header: "Fim previsto",
                render: (row) =>
                  row.data_fim_prevista_op
                    ? formatDisplayDate(row.data_fim_prevista_op)
                    : "Sem data prevista",
              },
              {
                key: "status",
                header: "Status",
                render: (row) => {
                  const prazo = resolveOpVsPedidoPrazo(
                    row.data_fim_prevista_op,
                    item.data_entrega,
                  );
                  if (prazo.status === "indeterminado") return "—";
                  return (
                    <StatusBadge
                      classNames={cmStatusBadgeClassNames}
                      label={prazo.label}
                      variant={prazoVariant(prazo.status)}
                  />
                  );
                },
              },
              {
                key: "obs",
                header: "Observação",
                render: (row) => row.observacao_op || "—",
              },
            ]}
          />
        ) : (
          <p className="cm-open-orders-drawer__empty">Nenhuma OP alocada para esta linha.</p>
        )}
      </div>
    </CommercialDrawerShell>
  );
}
