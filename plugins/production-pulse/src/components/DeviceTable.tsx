import { RefreshCw } from "lucide-react";

import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import {
  formatCounterPeriodDelta,
  formatPrimaryMetric,
  formatRelativeTime,
  roleLabel,
} from "../utils/deviceDisplay";
import { PpDataTable, type DataTableColumn } from "../app/productionPulseUi";
import { PlacementObjectDisplay } from "./PlacementObjectDisplay";
import { DeviceStatusBadge } from "./DeviceStatusBadge";

type DeviceTableProps = {
  devices: DeviceListItem[];
  loading: boolean;
  pollingDeviceId: string | null;
  onPoll: (deviceId: string) => void;
  onOpenDevice?: (deviceId: string) => void;
};

export function DeviceTable({
  devices,
  loading,
  pollingDeviceId,
  onPoll,
  onOpenDevice,
}: DeviceTableProps) {
  const columns: DataTableColumn<DeviceListItem>[] = [
    {
      key: "name",
      header: "Nome",
      render: (row) => (
        <button type="button" className="pp-device-link" onClick={() => onOpenDevice?.(row.id)}>
          {row.name}
        </button>
      ),
    },
    {
      key: "placement",
      header: "Objeto",
      render: (row) => <PlacementObjectDisplay device={row} />,
    },
    {
      key: "role",
      header: "Papel",
      className: "pp-device-table__col-role",
      render: (row) => roleLabel(row.roleKey),
    },
    {
      key: "metric",
      header: "Métrica",
      render: (row) => {
        const dayDelta = formatCounterPeriodDelta(row, "day");
        return (
          <span className="pp-device-metric">
            <span className="pp-tabular-nums">{formatPrimaryMetric(row)}</span>
            {dayDelta ? <span className="pp-device-metric__delta">{dayDelta} hoje</span> : null}
          </span>
        );
      },
    },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <span title={formatRelativeTime(row.lastSeenAt)}>
          <DeviceStatusBadge status={row.status} />
        </span>
      ),
    },
    {
      key: "lastSeen",
      header: "Última leitura",
      className: "pp-device-table__col-last-seen",
      render: (row) => (
        <span className="pp-tabular-nums" title={row.lastSeenAt ?? undefined}>
          {formatRelativeTime(row.lastSeenAt)}
        </span>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (row) => (
        <button
          type="button"
          className="pp-row-action"
          aria-label={`Atualizar ${row.name}`}
          title={PP_HELP.panel.rowPoll}
          disabled={pollingDeviceId === row.id}
          onClick={() => onPoll(row.id)}
        >
          <RefreshCw size={16} className={pollingDeviceId === row.id ? "pp-spin" : undefined} aria-hidden="true" />
        </button>
      ),
    },
  ];

  return (
    <section className="pp-device-table pp-device-table--desktop" aria-label="Dispositivos">
      <header className="pp-device-table__header">
        <h2 className="pp-device-table__title">Dispositivos</h2>
        <span className="pp-device-table__count">{devices.length} dispositivo(s)</span>
      </header>
      <PpDataTable
        rows={devices}
        columns={columns}
        rowKey={(row) => row.id}
        loading={loading}
        emptyMessage="Nenhum dispositivo encontrado."
      />
    </section>
  );
}
