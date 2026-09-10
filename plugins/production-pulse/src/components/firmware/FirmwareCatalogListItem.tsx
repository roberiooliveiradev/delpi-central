import { FileCode } from "lucide-react";

import type { FirmwareListItem } from "../../api/productionPulseApi";
import { PpActionButton } from "../../app/productionPulseUi";
import { isPublishedFirmware } from "../../utils/hubOtaKpis";
import {
  firmwareLifecycleBadgeClass,
  summarizeFirmwareCatalogItem,
} from "../../utils/firmwareCatalogDisplay";

type FirmwareCatalogListItemProps = {
  firmware: FirmwareListItem;
  canManage: boolean;
  busy?: boolean;
  onOpenDetails: () => void;
  onUpdateLinked?: () => void;
};

export function FirmwareCatalogListItem({
  firmware,
  canManage,
  busy = false,
  onOpenDetails,
  onUpdateLinked,
}: FirmwareCatalogListItemProps) {
  const summary = summarizeFirmwareCatalogItem(firmware);
  const metaParts: string[] = [
    `v${summary.version}`,
    summary.familyKey,
    summary.driverKey,
  ];
  if (summary.hasArtifact) {
    metaParts.push(
      summary.artifactSizeLabel ? `bin ${summary.artifactSizeLabel}` : "com binário",
    );
  } else {
    metaParts.push("sem binário");
  }
  if (summary.hasSource) {
    metaParts.push("com sketch");
  }

  return (
    <article
      className={
        summary.lifecycle === "archived"
          ? "pp-firmware-catalog-row pp-firmware-catalog-row--archived"
          : "pp-firmware-catalog-row"
      }
      aria-label={`Firmware ${summary.title} ${summary.version}`}
    >
      <div className="pp-firmware-catalog-row__main">
        <div className="pp-firmware-catalog-row__identity">
          <FileCode size={16} aria-hidden className="pp-firmware-catalog-row__icon" />
          <div className="pp-firmware-catalog-row__text">
            <span className="pp-firmware-catalog-row__label">{summary.title}</span>
            <span className="pp-firmware-catalog-row__meta">{metaParts.join(" · ")}</span>
          </div>
        </div>
        <span className={firmwareLifecycleBadgeClass(summary.lifecycle)}>
          {summary.lifecycleLabel}
        </span>
      </div>
      <div className="pp-firmware-catalog-row__actions pp-inline-actions">
        <PpActionButton variant="ghost" onClick={onOpenDetails}>
          Detalhe
        </PpActionButton>
        {canManage && isPublishedFirmware(firmware) && onUpdateLinked ? (
          <PpActionButton variant="ghost" disabled={busy} onClick={onUpdateLinked}>
            Atualizar ligados
          </PpActionButton>
        ) : null}
      </div>
    </article>
  );
}
