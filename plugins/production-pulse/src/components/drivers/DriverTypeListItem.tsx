import { CircuitBoard, Gauge, Hash } from "lucide-react";

import type { DriverListItem } from "../../api/productionPulseApi";
import { PpActionButton } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";
import { summarizeDriverCatalogItem } from "../../utils/driverCatalogDisplay";

type DriverTypeListItemProps = {
  driver: DriverListItem;
  canManage: boolean;
  busy?: boolean;
  onOpenDetails: () => void;
  onArchive?: () => void;
  onUnarchive?: () => void;
};

function ProtocolIcon({ protocolKind }: { protocolKind: string }) {
  if (protocolKind === "http_gauge") {
    return <Gauge size={16} aria-hidden className="pp-driver-type-row__icon" />;
  }
  if (protocolKind === "http_counter") {
    return <Hash size={16} aria-hidden className="pp-driver-type-row__icon" />;
  }
  return <CircuitBoard size={16} aria-hidden className="pp-driver-type-row__icon" />;
}

export function DriverTypeListItem({
  driver,
  canManage,
  busy = false,
  onOpenDetails,
  onArchive,
  onUnarchive,
}: DriverTypeListItemProps) {
  const summary = summarizeDriverCatalogItem(driver);
  const title = driver.labelPt?.trim() || driver.key;
  const metaParts: string[] = [
    summary.protocol.shortLabel,
    driver.roleKey,
    `${summary.metricCount} métrica${summary.metricCount === 1 ? "" : "s"}`,
  ];
  if (summary.commandCount > 0) {
    metaParts.push(
      `${summary.commandCount} comando${summary.commandCount === 1 ? "" : "s"}`,
    );
  }
  if (!summary.eligible) {
    metaParts.push("fora do operador");
  }

  return (
    <article
      className={
        summary.archived
          ? "pp-driver-type-row pp-driver-type-row--archived"
          : "pp-driver-type-row"
      }
      aria-label={`Tipo de driver ${title}`}
    >
      <div className="pp-driver-type-row__main">
        <div className="pp-driver-type-row__identity">
          <ProtocolIcon protocolKind={summary.protocol.kind} />
          <div className="pp-driver-type-row__text">
            <span className="pp-driver-type-row__label">{title}</span>
            <code className="pp-driver-type-row__key">{driver.key}</code>
            <span className="pp-driver-type-row__meta">{metaParts.join(" · ")}</span>
          </div>
        </div>
        <span
          className={
            summary.archived
              ? "pp-driver-type-row__badge pp-driver-type-row__badge--archived"
              : "pp-driver-type-row__badge pp-driver-type-row__badge--active"
          }
        >
          {summary.archived
            ? PP_HELP.drivers.statusArchived
            : PP_HELP.drivers.statusActive}
        </span>
      </div>
      <div className="pp-driver-type-row__actions pp-inline-actions">
        <PpActionButton variant="ghost" onClick={onOpenDetails}>
          Detalhe
        </PpActionButton>
        {canManage && !summary.archived && onArchive ? (
          <PpActionButton variant="ghost" disabled={busy} onClick={onArchive}>
            Arquivar
          </PpActionButton>
        ) : null}
        {canManage && summary.archived && onUnarchive ? (
          <PpActionButton variant="ghost" disabled={busy} onClick={onUnarchive}>
            Reativar
          </PpActionButton>
        ) : null}
      </div>
    </article>
  );
}
