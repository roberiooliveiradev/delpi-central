import { CalendarClock, FileCode } from "lucide-react";

import type { FirmwareUpdateJob, FirmwareUpdateTarget } from "../../api/productionPulseApi";
import { PpActionButton, PpOtaProgressBar } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";
import { formatRelativeTime } from "../../utils/deviceDisplay";
import { resolveFirmwareChangeDirection } from "../../utils/firmwareVersionDirection";
import {
  jobStatusToOtaPhase,
  summarizeOtaJobTargets,
} from "../../utils/otaJobSummary";
import { OtaStatusIndicator } from "./OtaStatusIndicator";

type OtaJobListItemProps = {
  job: FirmwareUpdateJob;
  firmwareLabel: string;
  targets?: FirmwareUpdateTarget[];
  canManage: boolean;
  onOpenDetails: () => void;
  onCancel?: () => void;
};

export function OtaJobListItem({
  job,
  firmwareLabel,
  targets = [],
  canManage,
  onOpenDetails,
  onCancel,
}: OtaJobListItemProps) {
  const summary = targets.length > 0 ? summarizeOtaJobTargets(targets) : null;
  const phaseStatus = summary?.phaseStatus ?? jobStatusToOtaPhase(job.status);
  const triggerLabel = job.trigger === "manual" ? "Agora" : "Agendado";
  const TriggerIcon = job.trigger === "scheduled" ? CalendarClock : FileCode;
  const canCancel =
    canManage && ["draft", "scheduled", "running"].includes((job.status || "").toLowerCase());

  const sample = targets.find((t) => t.fromVersion || t.toVersion);
  const direction = sample
    ? resolveFirmwareChangeDirection(sample.fromVersion, sample.toVersion)
    : "unknown";
  const directionBadge =
    direction === "upgrade"
      ? PP_HELP.ota.directionUpgrade
      : direction === "downgrade"
        ? PP_HELP.ota.directionDowngrade
        : null;

  const metaParts: string[] = [triggerLabel];
  if (job.createdAt) metaParts.push(formatRelativeTime(job.createdAt));
  if (summary && summary.total > 0) {
    metaParts.push(`${summary.terminal} de ${summary.total} processados`);
  }
  if (sample?.fromVersion || sample?.toVersion) {
    metaParts.push(`${sample.fromVersion ?? "—"} → ${sample.toVersion ?? "—"}`);
  }

  return (
    <article className="pp-ota-job-row" aria-label={`Atualização ${firmwareLabel}`}>
      <div className="pp-ota-job-row__main">
        <div className="pp-ota-job-row__firmware">
          <FileCode size={16} aria-hidden className="pp-ota-job-row__fw-icon" />
          <div className="pp-ota-job-row__fw-text">
            <span className="pp-ota-job-row__fw-label">
              {firmwareLabel}
              {directionBadge ? (
                <span
                  className={
                    direction === "downgrade"
                      ? "pp-ota-direction-badge pp-ota-direction-badge--downgrade"
                      : "pp-ota-direction-badge pp-ota-direction-badge--upgrade"
                  }
                >
                  {directionBadge}
                </span>
              ) : null}
            </span>
            <span className="pp-ota-job-row__fw-meta">
              <TriggerIcon size={12} aria-hidden />
              {metaParts.join(" · ")}
            </span>
          </div>
        </div>
        <OtaStatusIndicator status={phaseStatus} density="comfortable" />
        {summary && summary.total > 0 && (job.status || "").toLowerCase() === "running" ? (
          <div className="pp-ota-job-row__progress">
            <PpOtaProgressBar
              value={summary.processedPercent}
              summary={`${summary.terminal} de ${summary.total} processados`}
              ariaLabel="Progresso agregado do job"
            />
            <ul className="pp-job-summary__counts">
              <li>{summary.updated} concluídos</li>
              <li>{summary.downloading} baixando</li>
              <li>{summary.awaiting} aguardando</li>
              <li>{summary.failed} falhas</li>
            </ul>
          </div>
        ) : null}
      </div>
      <div className="pp-ota-job-row__actions pp-inline-actions">
        <PpActionButton variant="ghost" onClick={onOpenDetails}>
          {PP_HELP.hub.jobDetails}
        </PpActionButton>
        {canCancel && onCancel ? (
          <PpActionButton variant="ghost" onClick={onCancel}>
            Cancelar
          </PpActionButton>
        ) : null}
      </div>
    </article>
  );
}
