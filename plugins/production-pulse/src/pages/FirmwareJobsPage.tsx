import { useCallback, useEffect, useMemo, useState } from "react";

import {
  cancelFirmwareUpdateJob,
  createFirmwareUpdateJob,
  fetchFirmwareUpdateJobs,
  fetchFirmwareUpdateTargets,
  fetchFirmwares,
  type FirmwareCatalogItem,
  type FirmwareUpdateJob,
  type FirmwareUpdateTarget,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpHintAction,
  PpNativeSelectField,
  PpNativeTextField,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwaresPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareJobsPageProps = {
  branch: string;
  permissions: ProductionPulsePermissionFlags;
};

export function FirmwareJobsPage({ branch, permissions }: FirmwareJobsPageProps) {
  const [jobs, setJobs] = useState<FirmwareUpdateJob[]>([]);
  const [firmwares, setFirmwares] = useState<FirmwareCatalogItem[]>([]);
  const [targets, setTargets] = useState<FirmwareUpdateTarget[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [firmwareId, setFirmwareId] = useState("");
  const [trigger, setTrigger] = useState<"manual" | "scheduled">("manual");
  const [scheduledAt, setScheduledAt] = useState("");

  const firmwareOptions = useMemo(
    () =>
      firmwares.map((item) => ({
        value: item.id,
        label: `${item.firmwareKey} · ${item.version}`,
      })),
    [firmwares],
  );

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [jobItems, firmwareItems] = await Promise.all([
        fetchFirmwareUpdateJobs(branch),
        fetchFirmwares(),
      ]);
      setJobs(jobItems);
      const published = firmwareItems.filter((item) => item.publishedAt);
      setFirmwares(published);
      if (!firmwareId && published[0]) setFirmwareId(published[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar campanhas.");
    } finally {
      setLoading(false);
    }
  }, [branch, firmwareId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const openTargets = async (jobId: string) => {
    setSelectedJobId(jobId);
    try {
      setTargets(await fetchFirmwareUpdateTargets(jobId));
    } catch {
      setTargets([]);
    }
  };

  const onCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!permissions.canManageDevices || !firmwareId) return;
    setBusy(true);
    setError(null);
    try {
      const job = await createFirmwareUpdateJob({
        firmwareId,
        branch,
        trigger,
        scheduledAt: trigger === "scheduled" ? scheduledAt : undefined,
        filter: { onlyOutdated: true },
      });
      await reload();
      await openTargets(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar campanha.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Campanhas OTA"
        badge={ppShellIcon}
        description={PP_HELP.ota.jobsHero}
        actions={
          <>
            <PpHintAction hint={PP_HELP.shell.backToPanel} ariaLabel="Ajuda: Painel">
              <PpActionButton
                variant="ghost"
                title={PP_HELP.shell.backToPanel}
                onClick={() => navigateProductionPulse(PRODUCTION_PULSE_BASE_PATH)}
              >
                Painel
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.ota.openCatalog} ariaLabel="Ajuda: Firmwares">
              <PpActionButton
                variant="secondary"
                title={PP_HELP.ota.openCatalog}
                onClick={() => navigateProductionPulse(productionPulseFirmwaresPath())}
              >
                Firmwares
              </PpActionButton>
            </PpHintAction>
          </>
        }
      />

      {permissions.canManageDevices ? (
        <PpSectionCard title="Nova campanha" hint={PP_HELP.ota.jobCreate}>
          <form className="pp-form-grid" onSubmit={(e) => void onCreate(e)}>
            <PpNativeSelectField
              id="ota-job-firmware"
              label="Firmware"
              hint={PP_HELP.ota.jobFirmware}
              value={firmwareId}
              onChange={setFirmwareId}
              options={firmwareOptions}
              placeholderOption="Selecione…"
              span
            />
            <PpNativeSelectField
              id="ota-job-trigger"
              label="Disparo"
              hint={PP_HELP.ota.jobTrigger}
              value={trigger}
              onChange={(value) => setTrigger(value as "manual" | "scheduled")}
              options={[
                { value: "manual", label: "Agora" },
                { value: "scheduled", label: "Agendado" },
              ]}
              searchable={false}
            />
            <PpNativeTextField
              id="ota-job-scheduled"
              label="Agendar para"
              hint={PP_HELP.ota.jobScheduledAt}
              type="datetime-local"
              value={scheduledAt}
              onChange={setScheduledAt}
            />
            <PpActionButton type="submit" disabled={busy || firmwares.length === 0 || !firmwareId}>
              {busy ? "Criando…" : "Disparar campanha"}
            </PpActionButton>
          </form>
        </PpSectionCard>
      ) : null}

      <PpSectionCard title={`Campanhas · filial ${branch}`} hint={PP_HELP.ota.jobsList}>
        {loading ? (
          <PpStateBox variant="loading" title="Carregando campanhas" />
        ) : error ? (
          <PpStateBox variant="error" title="Erro" message={error} />
        ) : jobs.length === 0 ? (
          <PpStateBox variant="empty" title="Sem campanhas" message={PP_HELP.ota.jobsEmpty} />
        ) : (
          <ul className="pp-list">
            {jobs.map((job) => (
              <li key={job.id} className="pp-list__item">
                <div>
                  <strong>{job.trigger}</strong> · {job.status}
                  {job.scheduledAt ? ` · ${new Date(job.scheduledAt).toLocaleString()}` : null}
                </div>
                <div className="pp-inline-actions">
                  <PpActionButton variant="ghost" onClick={() => void openTargets(job.id)}>
                    Targets
                  </PpActionButton>
                  {permissions.canManageDevices &&
                  ["draft", "scheduled", "running"].includes(job.status) ? (
                    <PpActionButton
                      variant="ghost"
                      onClick={() =>
                        void cancelFirmwareUpdateJob(job.id).then(() => reload())
                      }
                    >
                      Cancelar
                    </PpActionButton>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </PpSectionCard>

      {selectedJobId ? (
        <PpSectionCard title="Targets da campanha" hint={PP_HELP.ota.targetsList}>
          {targets.length === 0 ? (
            <PpStateBox variant="empty" title="Sem targets" />
          ) : (
            <div className="pp-table-wrap">
              <table className="pp-table">
                <thead>
                  <tr>
                    <th>Device</th>
                    <th>De</th>
                    <th>Para</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {targets.map((target) => (
                    <tr key={target.id}>
                      <td>
                        <code>{target.deviceId.slice(0, 8)}</code>
                      </td>
                      <td>{target.fromVersion ?? "—"}</td>
                      <td>{target.toVersion}</td>
                      <td>{target.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </PpSectionCard>
      ) : null}
    </div>
  );
}
