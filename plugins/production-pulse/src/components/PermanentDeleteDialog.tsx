import { Ban, Cpu, FileCode, TriangleAlert } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import type { DeletionImpact } from "../api/productionPulseApi";
import {
  PpActionButton,
  PpHostContainedDialog,
  PpNativeTextField,
} from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";

export type PermanentDeleteDialogProps = {
  open: boolean;
  title: string;
  entityLabel: string;
  confirmPhrase: string;
  impact: DeletionImpact | null;
  loadingImpact?: boolean;
  confirmBusy?: boolean;
  impactSummary?: ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
};

function normalizeConfirmText(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function blockerLabel(code: string, count?: number): string {
  const n = count ?? 0;
  switch (code) {
    case "deviceHasActiveOta":
      return PP_HELP.hub.permanentDeleteBlockerActiveOta;
    case "firmwareHasUpdateHistory":
      return PP_HELP.hub.permanentDeleteBlockerFirmwareHistory.replace("{count}", String(n));
    case "firmwareHasActiveTargets":
      return PP_HELP.hub.permanentDeleteBlockerFirmwareActive.replace("{count}", String(n));
    case "firmwareInstalledOnDevices":
      return PP_HELP.hub.permanentDeleteBlockerFirmwareInstalled.replace("{count}", String(n));
    case "driverHasDevices":
      return PP_HELP.hub.permanentDeleteBlockerDriverDevices.replace("{count}", String(n));
    case "driverHasFirmwares":
      return PP_HELP.hub.permanentDeleteBlockerDriverFirmwares.replace("{count}", String(n));
    default:
      return code;
  }
}

/**
 * Presentational strong-confirm dialog for hard delete.
 * Receives preflight impact via props — does not call the API.
 */
export function PermanentDeleteDialog({
  open,
  title,
  entityLabel,
  confirmPhrase,
  impact,
  loadingImpact = false,
  confirmBusy = false,
  impactSummary,
  onConfirm,
  onCancel,
}: PermanentDeleteDialogProps) {
  const [typed, setTyped] = useState("");

  useEffect(() => {
    if (!open) setTyped("");
  }, [open]);

  const canDelete = Boolean(impact?.canDelete);
  const phraseOk =
    normalizeConfirmText(typed) === normalizeConfirmText(confirmPhrase);
  const confirmEnabled = canDelete && phraseOk && !confirmBusy && !loadingImpact;

  const dependencyLines = useMemo(() => {
    if (!impact?.dependencies) return [];
    const lines: { icon: ReactNode; text: string }[] = [];
    const deps = impact.dependencies;
    if (typeof deps.bindings === "number" && deps.bindings > 0) {
      lines.push({
        icon: <Cpu size={14} aria-hidden />,
        text: `${deps.bindings} amarração(ões)`,
      });
    }
    if (typeof deps.readings === "number" && deps.readings > 0) {
      lines.push({
        icon: <TriangleAlert size={14} aria-hidden />,
        text: `${deps.readings} leituras`,
      });
    }
    if (typeof deps.rollups === "number" && deps.rollups > 0) {
      lines.push({
        icon: <TriangleAlert size={14} aria-hidden />,
        text: `${deps.rollups} agregações`,
      });
    }
    if (typeof deps.commands === "number" && deps.commands > 0) {
      lines.push({
        icon: <TriangleAlert size={14} aria-hidden />,
        text: `${deps.commands} comandos`,
      });
    }
    if (typeof deps.otaTargets === "number" && deps.otaTargets > 0) {
      lines.push({
        icon: <FileCode size={14} aria-hidden />,
        text: `${deps.otaTargets} registro(s) OTA`,
      });
    }
    if (deps.hasArtifact === true) {
      lines.push({
        icon: <FileCode size={14} aria-hidden />,
        text: "Arquivo OTA .bin",
      });
    }
    if (deps.hasSource === true) {
      lines.push({
        icon: <FileCode size={14} aria-hidden />,
        text: "Source/sketch armazenado",
      });
    }
    return lines;
  }, [impact]);

  return (
    <PpHostContainedDialog open={open} title={title} onClose={onCancel}>
      <div className="pp-permanent-delete">
        <p className="pp-permanent-delete__entity">
          <strong>{entityLabel}</strong>
        </p>

        {loadingImpact || !impact ? (
          <p className="pp-muted">{PP_HELP.hub.permanentDeleteLoading}</p>
        ) : !canDelete ? (
          <div className="pp-permanent-delete__blocked">
            <p className="pp-permanent-delete__blocked-title">
              <Ban size={16} aria-hidden />
              {PP_HELP.hub.permanentDeleteBlockedTitle}
            </p>
            <ul className="pp-permanent-delete__blockers">
              {impact.blockers.map((blocker) => (
                <li key={blocker.code}>
                  {blockerLabel(blocker.code, blocker.count)}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <>
            {impactSummary}
            {dependencyLines.length > 0 ? (
              <ul className="pp-permanent-delete__deps">
                {dependencyLines.map((line) => (
                  <li key={line.text}>
                    {line.icon}
                    <span>{line.text}</span>
                  </li>
                ))}
              </ul>
            ) : null}
            <p className="pp-muted">{PP_HELP.hub.permanentDeleteIrreversible}</p>
            <PpNativeTextField
              id="pp-permanent-delete-confirm"
              label={PP_HELP.hub.permanentDeleteTypeLabel.replace(
                "{phrase}",
                confirmPhrase,
              )}
              value={typed}
              onChange={setTyped}
              autoComplete="off"
            />
          </>
        )}

        <div className="pp-inline-actions">
          <PpActionButton variant="ghost" onClick={onCancel} disabled={confirmBusy}>
            Cancelar
          </PpActionButton>
          {canDelete ? (
            <PpActionButton
              className="pp-permanent-delete__confirm"
              disabled={!confirmEnabled}
              onClick={onConfirm}
            >
              {confirmBusy
                ? PP_HELP.hub.permanentDeleteBusy
                : PP_HELP.hub.permanentDeleteConfirmLabel}
            </PpActionButton>
          ) : null}
        </div>
      </div>
    </PpHostContainedDialog>
  );
}
