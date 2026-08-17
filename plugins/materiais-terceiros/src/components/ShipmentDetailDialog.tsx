import {
  createDashboardDetailFieldGrid,
  createHostContainedModalShell,
  documentExportActionsBemClasses,
  TabularExportButtons,
} from "@delpi/plugin-ui/index";

import { HELP_TOOLTIPS } from "../content/helpTooltips";
import type { Shipment, ShipmentReturn } from "../types/thirdPartyMaterials";
import { exportShipmentPdf } from "../utils/exportShipmentPdf";
import { formatDatePtBr, formatQuantity, formatStatus } from "../utils/formatters";
import { DataTable, type DataTableColumn } from "./dataTableUi";

const exportActions = documentExportActionsBemClasses("mt");

const Modal = createHostContainedModalShell({
  prefix: "mt",
  variant: "page",
  portalScopeClassName: "dashboard-materiais-terceiros",
  containedLayout: "fill",
  closeAriaLabel: "Fechar detalhe da remessa",
});

const DetailFields = createDashboardDetailFieldGrid({
  prefix: "mt",
  labels: {
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
});

type ShipmentDetailDialogProps = {
  shipment: Shipment | null;
  onClose: () => void;
};

const returnColumns: DataTableColumn<ShipmentReturn>[] = [
  {
    key: "number",
    header: "NF retorno",
    render: (row: ShipmentReturn) => row.number || "—",
  },
  {
    key: "series",
    header: "Série",
    render: (row: ShipmentReturn) => row.series || "—",
  },
  {
    key: "issued",
    header: "Emissão",
    render: (row: ShipmentReturn) => formatDatePtBr(row.issued_on),
  },
  {
    key: "tes",
    header: "TES",
    render: (row: ShipmentReturn) => row.tes || "—",
  },
  {
    key: "qty",
    header: "Quantidade",
    align: "right",
    render: (row: ShipmentReturn) => formatQuantity(row.quantity),
  },
  {
    key: "after",
    header: "Saldo após retorno",
    headerHint: "Saldo da remessa depois deste retorno. Não some nas linhas.",
    align: "right",
    render: (row: ShipmentReturn) => formatQuantity(row.balance_after_return),
  },
  {
    key: "partnerType",
    header: "Tipo parceiro",
    render: (row: ShipmentReturn) => row.partner_type || "—",
  },
];

export function ShipmentDetailDialog({ shipment, onClose }: ShipmentDetailDialogProps) {
  return (
    <Modal
      open={Boolean(shipment)}
      title={
        shipment
          ? `Remessa ${shipment.receipt_invoice.number || shipment.shipment_id}`
          : "Remessa"
      }
      description={
        shipment
          ? `${shipment.product.code} · ${shipment.partner.name || shipment.partner.code || "—"}`
          : undefined
      }
      headerActions={
        shipment ? (
          <TabularExportButtons
            actions={[{ format: "pdf", label: "PDF", title: HELP_TOOLTIPS.detailPdf }]}
            className={exportActions.root}
            buttonClassName={exportActions.button}
            groupAriaLabel="Exportar remessa"
            onExport={() => {
              exportShipmentPdf(shipment);
            }}
          />
        ) : null
      }
      onClose={onClose}
    >
      {shipment ? (
        <div className="mt-detail">
          <DetailFields
            fields={[
              { label: "Filial", value: shipment.branch },
              { label: "Identidade", value: shipment.shipment_id },
              { label: "Produto", value: shipment.product.code },
              { label: "Ref. cliente", value: shipment.product.customer_reference },
              { label: "Descrição", value: shipment.product.description },
              { label: "Status", value: formatStatus(String(shipment.status)) },
              { label: "TES entrada", value: shipment.receipt_invoice.tes },
              {
                label: "Qtd. recebida",
                value: formatQuantity(shipment.received_quantity, shipment.product.unit),
              },
              {
                label: "Qtd. devolvida",
                value: formatQuantity(shipment.returned_quantity, shipment.product.unit),
              },
              {
                label: "Saldo pendente",
                value: formatQuantity(shipment.pending_balance, shipment.product.unit),
              },
              {
                label: "Diferença de controle",
                value: formatQuantity(shipment.control_difference),
              },
            ]}
          />
          <DataTable
            columns={returnColumns}
            rows={shipment.returns}
            rowKey={(row: ShipmentReturn) => String(row.return_recno)}
            emptyMessage="Esta remessa ainda não possui retornos."
          />
        </div>
      ) : null}
    </Modal>
  );
}
