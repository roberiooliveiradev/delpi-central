import { ArrowDown, ArrowUp, Ban, CircleDot } from "lucide-react";

import type { FirmwareListItem } from "../../api/productionPulseApi";
import { PP_HELP } from "../../content/helpTooltips";
import {
  formatFirmwareVersionMenuLabel,
  resolveFirmwareVersionRowRoles,
} from "../../utils/firmwareVersionLabels";
import { isPublishedFirmware } from "../../utils/hubOtaKpis";
import {
  resolveFirmwareChangeDirection,
  type FirmwareChangeDirection,
} from "../../utils/firmwareVersionDirection";

export type FirmwareVersionPickerProps = {
  versions: FirmwareListItem[];
  /** Version currently running / installed on the IoT (or null for family scope). */
  installedVersion?: string | null;
  selectedId?: string | null;
  /** When true, same-as-installed rows are disabled (no force reinstall). */
  disableSameAsInstalled?: boolean;
  onSelect: (firmwareId: string) => void;
};

function rowDisabledReason(
  item: FirmwareListItem,
  installedVersion: string | null | undefined,
  disableSameAsInstalled: boolean,
): string | null {
  if (item.archivedAt || item.lifecycle === "archived") {
    return PP_HELP.ota.versionPickerArchivedHint;
  }
  if (!isPublishedFirmware(item) || !item.hasArtifact) {
    return PP_HELP.ota.versionPickerDraftHint;
  }
  if (
    disableSameAsInstalled &&
    installedVersion &&
    item.version === installedVersion
  ) {
    return PP_HELP.ota.versionPickerSameHint;
  }
  return null;
}

function DirectionIcon({
  direction,
}: {
  direction: FirmwareChangeDirection;
}) {
  if (direction === "upgrade") return <ArrowUp size={14} aria-hidden />;
  if (direction === "downgrade") return <ArrowDown size={14} aria-hidden />;
  if (direction === "same") return <CircleDot size={14} aria-hidden />;
  return <Ban size={14} aria-hidden />;
}

/**
 * Presentational version list — emits `firmwareId` only; never starts jobs.
 * Uses button radiogroup (no raw &lt;input&gt;) to satisfy kit structural gates.
 */
export function FirmwareVersionPicker({
  versions,
  installedVersion = null,
  selectedId = null,
  disableSameAsInstalled = true,
  onSelect,
}: FirmwareVersionPickerProps) {
  return (
    <div
      className="pp-firmware-version-picker"
      role="radiogroup"
      aria-label={PP_HELP.ota.versionPickerAria}
    >
      {versions.map((item) => {
        const disabledReason = rowDisabledReason(
          item,
          installedVersion,
          disableSameAsInstalled,
        );
        const disabled = Boolean(disabledReason);
        const roles = resolveFirmwareVersionRowRoles({
          item,
          familyItems: versions,
          installedVersion,
          selectedId,
        });
        const direction = resolveFirmwareChangeDirection(
          installedVersion,
          item.version,
        );
        const checked = selectedId === item.id;
        return (
          <button
            key={item.id}
            type="button"
            role="radio"
            aria-checked={checked}
            disabled={disabled}
            title={disabledReason ?? undefined}
            className={[
              "pp-firmware-version-picker__row",
              checked ? "pp-firmware-version-picker__row--selected" : "",
              disabled ? "pp-firmware-version-picker__row--disabled" : "",
              direction === "upgrade"
                ? "pp-firmware-version-picker__row--upgrade"
                : "",
              direction === "downgrade"
                ? "pp-firmware-version-picker__row--downgrade"
                : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => {
              if (!disabled) onSelect(item.id);
            }}
          >
            <span className="pp-firmware-version-picker__icon" aria-hidden>
              <DirectionIcon direction={disabled ? "same" : direction} />
            </span>
            <span className="pp-firmware-version-picker__text">
              <span className="pp-firmware-version-picker__label">
                {formatFirmwareVersionMenuLabel(item, roles)}
              </span>
              {disabledReason ? (
                <span className="pp-muted pp-firmware-version-picker__hint">
                  {disabledReason}
                </span>
              ) : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}
