import { useCallback, useEffect, useMemo, useState } from "react";

import {
  cancelFirmwareUpdateJob,
  createFirmwareUpdateJob,
  fetchDevices,
  fetchFirmwareUpdateJobs,
  fetchFirmwareUpdateTargets,
  fetchFirmwares,
  putDeviceFirmwareLink,
  type FirmwareCatalogItem,
  type FirmwareUpdateJob,
  type FirmwareUpdateTarget,
} from "../api/productionPulseApi";
import { FirmwareDeviceLinkCanvas } from "../components/FirmwareDeviceLinkCanvas";
import {
  PpActionButton,
  PpDataTable,
  PpHintAction,
  PpHostContainedDialog,
  PpNativeSelectField,
  PpNativeTextField,
  PpPageHero,
  PpSectionCard,
  PpSegmentToggle,
  PpStateBox,
  ppShellIcon,
  type DataTableColumn,
} from "../app/productionPulseUi";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseDeviceDetailPath,
  productionPulseFirmwaresPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import { uniqueFirmwareFamilies } from "../utils/firmwareLinkGraph";
import { navigateProductionPulse } from "../utils/navigation";
import {
  formatOtaBytes,
  formatOtaProgressDisplay,
  otaStatusLabel,
} from "../utils/otaStatusLabels";

type FirmwareLinksPageProps = {
  branch: string;
  highlightFirmwareKey?: string;
  permissions: ProductionPulsePermissionFlags;
};

const JOBS_POLL_MS = 3000;

export function FirmwareLinksPage({
  branch: initialBranch,
  highlightFirmwareKey,
  permissions,
}: FirmwareLinksPageProps) {
  const canManage = permissions.canManageDevices;
  const [branch, setBranch] = useState(initialBranch || "01");
  const [firmwaresRaw, setFirmwaresRaw] = useState<FirmwareCatalogItem[]>([]);
  const [publishedFirmwares, setPublishedFirmwares] = useState<FirmwareCatalogItem[]>([]);
  const [devices, setDevices] = useState<DeviceListItem[]>([]);
  const [jobs, setJobs] = useState<FirmwareUpdateJob[]>([]);
  const [targets, setTargets] = useState<FirmwareUpdateTarget[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [firmwareId, setFirmwareId] = useState("");
  const [trigger, setTrigger] = useState<"manual" | "scheduled">("manual");
  const [scheduledAt, setScheduledAt] = useState("");
  const [scope, setScope] = useState<"branch" | "device">("branch");
  const [scopeDeviceId, setScopeDeviceId] = useState("");
  const [cancelJobId, setCancelJobId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(
    highlightFirmwareKey
      ? `Firmware ${highlightFirmwareKey} publicado — ligue os IoTs no canvas.`
      : null,
  );

  const families = useMemo(
    () => uniqueFirmwareFamilies(firmwaresRaw, devices),
    [firmwaresRaw, devices],
  );

  const firmwareOptions = useMemo(
    () =>
      publishedFirmwares.map((item) => ({
        value: item.id,
        label: `${item.firmwareKey} · ${item.version}`,
      })),
    [publishedFirmwares],
  );

  const deviceOptions = useMemo(
    () =>
      devices.map((device) => ({
        value: device.id,
        label: `${device.name} (${device.ipAddress})`,
      })),
    [devices],
  );

  const hasActiveJob = jobs.some(
    (job) => job.status === "running" || job.status === "scheduled",
  );

  const reloadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [fw, published, devs] = await Promise.all([
        fetchFirmwares({ includeArchived: false }),
        fetchFirmwares({ includeArchived: false, publishedOnly: true }),
        fetchDevices({ branch }),
      ]);
      setFirmwaresRaw(fw);
      setPublishedFirmwares(published);
      setDevices(devs);
      setFirmwareId((current) => current || published[0]?.id || "");
      setScopeDeviceId((current) => current || devs[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar conexões.");
    } finally {
      setLoading(false);
    }
  }, [branch]);

  const reloadJobs = useCallback(
    async (opts?: { soft?: boolean }) => {
      const soft = Boolean(opts?.soft);
      if (!soft) setJobsLoading(true);
      try {
        const jobItems = await fetchFirmwareUpdateJobs(branch);
        setJobs(jobItems);
        if (selectedJobId) {
          try {
            setTargets(await fetchFirmwareUpdateTargets(selectedJobId));
          } catch {
            setTargets([]);
          }
        }
      } catch (err) {
        if (!soft) {
          setError(err instanceof Error ? err.message : "Falha ao carregar atualizações OTA.");
        }
      } finally {
        if (!soft) setJobsLoading(false);
      }
    },
    [branch, selectedJobId],
  );

  useEffect(() => {
    void reloadGraph();
  }, [reloadGraph]);

  useEffect(() => {
    void reloadJobs();
  }, [reloadJobs]);

  useEffect(() => {
    if (!hasActiveJob) return;
    const timer = window.setInterval(() => {
      void reloadJobs({ soft: true });
    }, JOBS_POLL_MS);
    return () => window.clearInterval(timer);
  }, [hasActiveJob, reloadJobs]);

  const openTargets = useCallback(async (jobId: string) => {
    setSelectedJobId(jobId);
    try {
      setTargets(await fetchFirmwareUpdateTargets(jobId));
    } catch {
      setTargets([]);
    }
  }, []);

  const onCreateJob = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canManage || !firmwareId) return;
    if (scope === "device" && !scopeDeviceId) return;
    setBusy(true);
    setError(null);
    try {
      const selected = publishedFirmwares.find((item) => item.id === firmwareId);
      const filter: Record<string, unknown> = {
        onlyOutdated: true,
      };
      if (selected?.firmwareKey) filter.firmwareKey = selected.firmwareKey;
      if (scope === "device") filter.deviceIds = [scopeDeviceId];
      const job = await createFirmwareUpdateJob({
        firmwareId,
        branch,
        trigger,
        scheduledAt: trigger === "scheduled" ? scheduledAt : undefined,
        filter,
      });
      await reloadJobs({ soft: true });
      await openTargets(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao disparar atualização OTA.");
    } finally {
      setBusy(false);
    }
  };

  const handleUnlink = useCallback(
    async (deviceId: string) => {
      await putDeviceFirmwareLink(deviceId, null);
      await reloadGraph();
    },
    [reloadGraph],
  );

  const handleUpdateDevice = useCallback(
    async (deviceId: string) => {
      if (!canManage) return;
      const device = devices.find((item) => item.id === deviceId);
      if (!device) return;
      const key = device.firmwareKey || device.assignedFirmwareKey || device.driverKey;
      const match =
        publishedFirmwares.find((item) => item.firmwareKey === key) ||
        publishedFirmwares.find((item) => item.driverKey === device.driverKey);
      if (!match) {
        setError(PP_HELP.ota.noPublishedFirmware);
        return;
      }
      setBusy(true);
      try {
        const job = await createFirmwareUpdateJob({
          firmwareId: match.id,
          branch,
          trigger: "manual",
          filter: {
            firmwareKey: match.firmwareKey,
            onlyOutdated: true,
            deviceIds: [deviceId],
          },
        });
        await reloadJobs({ soft: true });
        await openTargets(job.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : PP_HELP.ota.deviceJobFailed);
      } finally {
        setBusy(false);
      }
    },
    [branch, canManage, devices, openTargets, publishedFirmwares, reloadJobs],
  );

  const handleUpdateFamily = useCallback(
    async (firmwareKey: string) => {
      if (!canManage) return;
      const match = publishedFirmwares.find((item) => item.firmwareKey === firmwareKey);
      if (!match) {
        setError(PP_HELP.ota.noPublishedFirmware);
        return;
      }
      setBusy(true);
      try {
        const job = await createFirmwareUpdateJob({
          firmwareId: match.id,
          branch,
          trigger: "manual",
          filter: {
            firmwareKey: match.firmwareKey,
            onlyOutdated: true,
          },
        });
        await reloadJobs({ soft: true });
        await openTargets(job.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : PP_HELP.ota.deviceJobFailed);
      } finally {
        setBusy(false);
      }
    },
    [branch, canManage, openTargets, publishedFirmwares, reloadJobs],
  );

  const confirmCancelJob = async () => {
    if (!cancelJobId || !canManage) return;
    const jobId = cancelJobId;
    setCancelJobId(null);
    try {
      await cancelFirmwareUpdateJob(jobId);
    } catch {
      /* soft refresh anyway */
    }
    await reloadJobs({ soft: true });
    if (selectedJobId === jobId) {
      try {
        setTargets(await fetchFirmwareUpdateTargets(jobId));
      } catch {
        setTargets([]);
      }
    }
  };

  const jobColumns: DataTableColumn<FirmwareUpdateJob>[] = useMemo(
    () => [
      {
        key: "trigger",
        header: "Disparo",
        render: (row) => (row.trigger === "manual" ? "Agora" : "Agendado"),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => otaStatusLabel(row.status),
      },
      {
        key: "scheduled",
        header: "Agenda",
        render: (row) =>
          row.scheduledAt ? new Date(row.scheduledAt).toLocaleString() : "—",
      },
      {
        key: "created",
        header: "Criado",
        render: (row) => (row.createdAt ? new Date(row.createdAt).toLocaleString() : "—"),
      },
      {
        key: "actions",
        header: "",
        render: (row) => (
          <div className="pp-inline-actions">
            <PpActionButton variant="ghost" onClick={() => void openTargets(row.id)}>
              Targets
            </PpActionButton>
            {canManage && ["draft", "scheduled", "running"].includes(row.status) ? (
              <PpActionButton variant="ghost" onClick={() => setCancelJobId(row.id)}>
                Cancelar
              </PpActionButton>
            ) : null}
          </div>
        ),
      },
    ],
    [canManage, openTargets],
  );

  const targetColumns: DataTableColumn<FirmwareUpdateTarget>[] = useMemo(
    () => [
      {
        key: "device",
        header: "Device",
        render: (row) => <code>{row.deviceId.slice(0, 8)}</code>,
      },
      {
        key: "from",
        header: "De",
        render: (row) => row.fromVersion ?? "—",
      },
      {
        key: "to",
        header: "Para",
        render: (row) => row.toVersion ?? "—",
      },
      {
        key: "status",
        header: "Status",
        render: (row) => otaStatusLabel(row.status),
      },
      {
        key: "progress",
        header: "Progresso",
        render: (row) => {
          const display = formatOtaProgressDisplay({
            status: row.status,
            progressPercent: row.progressPercent,
          });
          const bytes = formatOtaBytes(row.bytesReceived, row.bytesTotal);
          return (
            <span>
              {display}
              {bytes ? ` · ${bytes}` : null}
            </span>
          );
        },
      },
    ],
    [],
  );

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Hub OTA · Amarração" badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar dispositivos."
        />
      </div>
    );
  }

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Hub OTA · Amarração"
        badge={ppShellIcon}
        description={PP_HELP.otaLinks.hero}
        actions={
          <>
            <PpHintAction hint={PP_HELP.shell.backToPanel} ariaLabel="Ajuda: Painel">
              <PpActionButton
                variant="ghost"
                onClick={() => navigateProductionPulse(PRODUCTION_PULSE_BASE_PATH)}
              >
                Painel
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.ota.openCatalog} ariaLabel="Ajuda: Firmwares">
              <PpActionButton
                variant="ghost"
                onClick={() => navigateProductionPulse(productionPulseFirmwaresPath())}
              >
                Firmwares
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.otaLinks.refresh} ariaLabel="Ajuda: Atualizar conexões">
              <PpActionButton
                variant="primary"
                onClick={() => {
                  void reloadGraph();
                  void reloadJobs({ soft: true });
                }}
                disabled={loading}
              >
                Atualizar
              </PpActionButton>
            </PpHintAction>
          </>
        }
      />

      <PpSectionCard title="Filial" hint={PP_HELP.otaLinks.branch}>
        <PpNativeSelectField
          id="ota-links-branch"
          label="Filial"
          hint={PP_HELP.otaLinks.branch}
          value={branch}
          onChange={setBranch}
          options={[
            { value: "01", label: "Filial 01" },
            { value: "02", label: "Filial 02" },
          ]}
          searchable={false}
        />
      </PpSectionCard>

      {notice ? (
        <PpStateBox
          variant="empty"
          title="Publicação"
          message={notice || PP_HELP.otaLinks.afterPublish}
          action={
            <PpActionButton variant="ghost" onClick={() => setNotice(null)}>
              Fechar
            </PpActionButton>
          }
        />
      ) : null}

      {canManage ? (
        <PpSectionCard title="Atualização OTA" hint={PP_HELP.ota.jobCreate}>
          <form className="pp-form-grid" onSubmit={(e) => void onCreateJob(e)}>
            <PpNativeSelectField
              id="ota-hub-firmware"
              label="Firmware"
              hint={PP_HELP.ota.jobFirmware}
              value={firmwareId}
              onChange={setFirmwareId}
              options={firmwareOptions}
              placeholderOption="Selecione…"
              span
            />
            <div className="pp-form-field-span">
              <PpSegmentToggle
                ariaLabel="Disparo"
                size="sm"
                widthMode="content"
                value={trigger}
                onChange={(value) => setTrigger(value as "manual" | "scheduled")}
                options={[
                  { value: "manual", label: "Agora" },
                  { value: "scheduled", label: "Agendar" },
                ]}
              />
            </div>
            {trigger === "scheduled" ? (
              <PpNativeTextField
                id="ota-hub-scheduled"
                label="Agendar para"
                hint={PP_HELP.ota.jobScheduledAt}
                type="datetime-local"
                value={scheduledAt}
                onChange={setScheduledAt}
              />
            ) : null}
            <PpSegmentToggle
              ariaLabel="Escopo"
              size="sm"
              widthMode="content"
              value={scope}
              onChange={(value) => setScope(value as "branch" | "device")}
              options={[
                { value: "branch", label: "Filial" },
                { value: "device", label: "Device selecionado" },
              ]}
            />
            {scope === "device" ? (
              <PpNativeSelectField
                id="ota-hub-device"
                label="Device"
                hint={PP_HELP.ota.jobScopeDevice}
                value={scopeDeviceId}
                onChange={setScopeDeviceId}
                options={deviceOptions}
                placeholderOption="Selecione…"
                span
              />
            ) : null}
            <PpActionButton
              type="submit"
              disabled={
                busy ||
                publishedFirmwares.length === 0 ||
                !firmwareId ||
                (scope === "device" && !scopeDeviceId)
              }
            >
              {busy ? "Disparando…" : "Disparar"}
            </PpActionButton>
          </form>
        </PpSectionCard>
      ) : null}

      <PpSectionCard title={`Atualizações · filial ${branch}`} hint={PP_HELP.ota.jobsList}>
        {jobsLoading && jobs.length === 0 ? (
          <PpStateBox variant="loading" title="Carregando atualizações" />
        ) : error && jobs.length === 0 ? (
          <PpStateBox variant="error" title="Erro" message={error} />
        ) : jobs.length === 0 ? (
          <PpStateBox variant="empty" title="Sem atualizações" message={PP_HELP.ota.jobsEmpty} />
        ) : (
          <PpDataTable
            columns={jobColumns}
            rows={jobs}
            rowKey={(row) => row.id}
            emptyMessage={PP_HELP.ota.jobsEmpty}
          />
        )}
      </PpSectionCard>

      {selectedJobId ? (
        <PpSectionCard title="Targets da atualização" hint={PP_HELP.ota.targetsList}>
          {targets.length === 0 ? (
            <PpStateBox variant="empty" title="Sem targets" />
          ) : (
            <PpDataTable
              columns={targetColumns}
              rows={targets}
              rowKey={(row) => row.id}
              emptyMessage="Sem targets"
            />
          )}
        </PpSectionCard>
      ) : null}

      {loading ? (
        <PpStateBox variant="loading" title="Carregando firmwares e IoTs" />
      ) : error && families.length === 0 ? (
        <PpStateBox variant="error" title="Erro" message={error} />
      ) : (
        <PpSectionCard
          title={`Canvas · ${families.length} firmwares · ${devices.length} IoTs`}
          hint={PP_HELP.otaLinks.canvas}
        >
          <p className="pp-muted">{PP_HELP.otaLinks.oneFirmwarePerDevice}</p>
          <p className="pp-muted">{PP_HELP.otaLinks.legend}</p>
          <FirmwareDeviceLinkCanvas
            families={families}
            devices={devices}
            canManage={canManage}
            onLinked={() => void reloadGraph()}
            onUnlink={handleUnlink}
            onUpdateDevice={handleUpdateDevice}
            onUpdateFamily={handleUpdateFamily}
            onSelectDevice={(deviceId) =>
              navigateProductionPulse(productionPulseDeviceDetailPath(deviceId, "firmware"))
            }
          />
        </PpSectionCard>
      )}

      <PpHostContainedDialog
        open={Boolean(cancelJobId)}
        title={PP_HELP.ota.cancelConfirmTitle}
        onClose={() => setCancelJobId(null)}
      >
        <p>{PP_HELP.ota.cancelConfirmBody}</p>
        <div className="pp-inline-actions">
          <PpActionButton variant="ghost" onClick={() => setCancelJobId(null)}>
            Voltar
          </PpActionButton>
          <PpActionButton onClick={() => void confirmCancelJob()}>Cancelar atualização</PpActionButton>
        </div>
      </PpHostContainedDialog>
    </div>
  );
}
