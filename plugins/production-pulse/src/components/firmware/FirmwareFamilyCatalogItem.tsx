import { ChevronDown, ChevronRight, FileCode } from "lucide-react";
import { useEffect, useId, useState } from "react";

import { PpActionButton } from "../../app/productionPulseUi";
import type { FirmwareCatalogFamilyGroup } from "../../utils/firmwareCatalogGrouping";
import {
  firmwareLifecycleBadgeClass,
  firmwareLifecycleLabel,
} from "../../utils/firmwareCatalogDisplay";
import { FirmwareCatalogListItem } from "./FirmwareCatalogListItem";

type FirmwareFamilyCatalogItemProps = {
  family: FirmwareCatalogFamilyGroup;
  canManage: boolean;
  busy?: boolean;
  onOpenVersionDetails: (firmwareId: string) => void;
  onNewVersion?: () => void;
  onUpdateLinked?: () => void;
};

export function FirmwareFamilyCatalogItem({
  family,
  canManage,
  busy = false,
  onOpenVersionDetails,
  onNewVersion,
  onUpdateLinked,
}: FirmwareFamilyCatalogItemProps) {
  const panelId = useId();
  const [expanded, setExpanded] = useState(family.defaultExpanded);

  useEffect(() => {
    setExpanded(family.defaultExpanded);
  }, [family.defaultExpanded, family.firmwareKey]);

  const lifecycle = family.latest.lifecycle;
  const metaParts = [
    `v${family.latest.version}`,
    family.firmwareKey,
    family.driverKey,
    `${family.versionCount} versão${family.versionCount === 1 ? "" : "ões"}`,
  ];

  return (
    <article
      className="pp-firmware-family"
      aria-label={`Família OTA ${family.displayName}`}
    >
      <div className="pp-firmware-family__header">
        <button
          type="button"
          className="pp-firmware-family__toggle"
          aria-expanded={expanded}
          aria-controls={panelId}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? (
            <ChevronDown size={18} aria-hidden="true" />
          ) : (
            <ChevronRight size={18} aria-hidden="true" />
          )}
          <FileCode size={16} aria-hidden className="pp-firmware-family__icon" />
          <span className="pp-firmware-family__text">
            <span className="pp-firmware-family__label">{family.displayName}</span>
            <span className="pp-firmware-family__meta">{metaParts.join(" · ")}</span>
          </span>
          <span className={firmwareLifecycleBadgeClass(lifecycle)}>
            {firmwareLifecycleLabel(lifecycle)}
          </span>
        </button>
        <div className="pp-firmware-family__actions pp-inline-actions">
          {canManage && onNewVersion ? (
            <PpActionButton variant="ghost" onClick={onNewVersion}>
              Nova versão
            </PpActionButton>
          ) : null}
          {canManage && family.latestPublished && onUpdateLinked ? (
            <PpActionButton variant="ghost" disabled={busy} onClick={onUpdateLinked}>
              Atualizar ligados
            </PpActionButton>
          ) : null}
        </div>
      </div>

      {expanded ? (
        <div id={panelId} className="pp-firmware-family__versions" role="list">
          {family.versions.map((firmware) => (
            <div key={firmware.id} role="listitem">
              <FirmwareCatalogListItem
                firmware={firmware}
                canManage={canManage}
                onOpenDetails={() => onOpenVersionDetails(firmware.id)}
              />
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}
