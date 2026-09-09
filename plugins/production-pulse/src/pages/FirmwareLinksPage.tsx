import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  cancelFirmwareUpdateJob,
  createFirmwareUpdateJob,
  fetchDevices,
  fetchFirmwareUpdateJobs,
  fetchFirmwareUpdateSummary,
  fetchFirmwareUpdateTargets,
  fetchFirmwares,
  putDeviceFirmwareLink,
  type FirmwareListItem,
  type FirmwareUpdateJob,
  type FirmwareUpdateSummary,
  type FirmwareUpdateTarget,
} from "../api/productionPulseApi";
import { FirmwareDeviceLinkCanvas } from "../components/FirmwareDeviceLinkCanvas";
import { HubOtaKpiStrip } from "../components/HubOtaKpiStrip";
import {
  PpActionButton,
  PpCatalogSearchBar,
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
import { resolveBranchOptions } from "../constants/branches";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  productionPulseDeviceDetailPath,
  productionPulseDeviceNewPath,
  productionPulseFirmwareDetailPath,
  productionPulseFirmwareLinksPath,
  productionPulseFirmwareNewPath,
  type HubFocus,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import { uniqueFirmwareFamilies } from "../utils/firmwareLinkGraph";
import {
  computeHubOtaKpis,
  EMPTY_HUB_OTA_KPIS,
  isPublishedFirmware,
} from "../utils/hubOtaKpis";
import { navigateProductionPulse, replaceProductionPulse } from "../utils/navigation";
import {
  formatOtaBytes,
  formatOtaProgressDisplay,
  otaStatusLabel,
} from "../utils/otaStatusLabels";

type FirmwareLinksPageProps = {
  branch: string;
  highlightFirmwareKey?: string;
  focus?: HubFocus;
  permissions: ProductionPulsePermissionFlags;
};

const JOBS_POLL_MS = 3000;

const HUB_SECTION_ID: Record<HubFocus, string> = {
  canvas: "pp-hub-canvas",
  catalog: "pp-hub-catalog",
  jobs: "pp-hub-jobs",
};

function lifecycleLabel(row: FirmwareListItem): string {
  if (row.lifecycle === "draft") return PP_HELP.ota.status.draft;
  if (row.lifecycle === "archived") return PP_HELP.ota.statusArchived;
  return PP_HELP.ota.statusPublished;
}

function formatTimestamp(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : "—";
}

export function FirmwareLinksPage({
  branch,
  highlightFirmwareKey,
  focus,
  permissions,
}: FirmwareLinksPageProps) {
  const canManage = permissions.canManageDevices;
  const branchOptions = useMemo(
    () => resolveBranchOptions(permissions.allowedBranches),
    [permissions.allowedBranches],
  );

  const [firmwares, setFirmwares] = useState<FirmwareListItem[]>([]);
  const [devices, setDevices] = useState<DeviceListItem[]>([]);
  const [updateSummary, setUpdateSummary] = useState<FirmwareUpdateSummary | null>(null);
  const [jobs, setJobs] = useState<FirmwareUpdateJob[]>([]);
  const [targets, setTargets] = useState<FirmwareUpdateTarget[]>([]);
  const [detailJobId, setDetailJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState("");
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

  const publishedFirmwares = useMemo(
    () => firmwares.filter(isPublishedFirmware),
    [firmwares],
  );

  const families = useMemo(
    () => uniqueFirmwareFamilies(firmwares, devices),
    [firmwares, devices],
  );

  const kpis = useMemo(
    () =>
      loading
        ? EMPTY_HUB_OTA_KPIS
        : computeHubOtaKpis({ firmwares, devices, updateSummary }),
    [devices, firmwares, loading, updateSummary],
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

  const firmwareById = useMemo(
    () => new Map(firmwares.map((item) => [item.id, item])),
    [firmwares],
  );

  const filteredFirmwares = useMemo(() => {
    const query = catalogSearch.trim().toLowerCase();
    if (!query) return firmwares;
    return firmwares.filter((item) =>
      [
        item.firmwareKey,
        item.driverKey,
        item.version,
        item.displayName,
        item.lifecycle,
        item.artifactSha256 ?? "",
      ]
        .join(" ")
        .toLowerCase()
        .includes(query),
    );
  }, [catalogSearch, firmwares]);

  const hasActiveJob = jobs.some(
    (job) => job.status === "running" || job.status === "scheduled",
  );

  const reloadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [catalog, devs, summary] = await Promise.all([
        fetchFirmwares({ includeArchived: true }),
        fetchDevices({ branch }),
        fetchFirmwareUpdateSummary(branch).catch(() => null),
      ]);
      setFirmwares(catalog);
      setDevices(devs);
      setUpdateSummary(summary);
      const published = catalog.filter(isPublishedFirmware);
      setFirmwareId((current) =>
        current && published.some((item) => item.id === current)
          ? current
          : published[0]?.id || "",
      );
      setScopeDeviceId((current) =>
        current && devs.some((item) => item.id === current) ? current : devs[0]?.id || "",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar o hub OTA.");
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
      } catch (err) {
        if (!soft) {
          setError(err instanceof Error ? err.message : "Falha ao carregar atualizações OTA.");
        }
      } finally {
        if (!soft) setJobsLoading(false);
      }
    },
    [branch],
  );

  const loadTargets = useCallback(async (jobId: string) => {
    try {
      setTargets(await fetchFirmwareUpdateTargets(jobId));
    } catch {
      setTargets([]);
    }
  }, []);

  const openJobDetails = useCallback(
    async (jobId: string) => {
      setDetailJobId(jobId);
      await loadTargets(jobId);
    },
    [loadTargets],
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
      if (detailJobId) void loadTargets(detailJobId);
    }, JOBS_POLL_MS);
    return () => window.clearInterval(timer);
  }, [detailJobId, hasActiveJob, loadTargets, reloadJobs]);

  const focusHandledRef = useRef(false);
  useEffect(() => {
    if (loading || focusHandledRef.current) return;
    if (focus !== "catalog" && focus !== "jobs") return;
    const target = document.getElementById(HUB_SECTION_ID[focus]);
    if (!target) return;
    focusHandledRef.current = true;
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [focus, loading]);

  const changeBranch = (nextBranch: string) => {
    replaceProductionPulse(
      productionPulseFirmwareLinksPath({
        branch: nextBranch,
        firmwareKey: highlightFirmwareKey,
        focus,
      }),
    );
  };

  const onCreateJob = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canManage || !firmwareId) return;
    if (scope === "device" && !scopeDeviceId) return;
    setBusy(true);
    setError(null);
    try {
      const selected = publishedFirmwares.find((item) => item.id === firmwareId);
      const filter: Record<string, unknown> = { onlyOutdated: true };
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
      await openJobDetails(job.id);
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

  const runFamilyJob = useCallback(
    async (firmwareKey: string, deviceIds?: string[]) => {
      const match = publishedFirmwares.find((item) => item.firmwareKey === firmwareKey);
      if (!match) {
        setError(PP_HELP.ota.noPublishedFirmware);
        return;
      }
      setBusy(true);
      try {
        const filter: Record<string, unknown> = {
          firmwareKey: match.firmwareKey,
          onlyOutdated: true,
        };
        if (deviceIds?.length) filter.deviceIds = deviceIds;
        const job = await createFirmwareUpdateJob({
          firmwareId: match.id,
          branch,
          trigger: "manual",
          filter,
        });
        await reloadJobs({ soft: true });
        await openJobDetails(job.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : PP_HELP.ota.deviceJobFailed);
      } finally {
        setBusy(false);
      }
    },
    [branch, openJobDetails, publishedFirmwares, reloadJobs],
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
      await runFamilyJob(match.firmwareKey, [deviceId]);
    },
    [canManage, devices, publishedFirmwares, runFamilyJob],
  );

  const handleUpdateFamily = useCallback(
    async (firmwareKey: string) => {
      if (!canManage) return;
      await runFamilyJob(firmwareKey);
    },
    [canManage, runFamilyJob],
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
    if (detailJobId === jobId) await loadTargets(jobId);
  };

  const firmwareColumns: DataTableColumn<FirmwareListItem>[] = useMemo(
    () => [
      {
        key: "family",
        header: "Família",
        render: (row) => <code>{row.firmwareKey}</code>,
      },
      { key: "version", header: "Versão", render: (row) => row.version },
      { key: "displayName", header: "Nome", render: (row) => row.displayName || "—" },
      { key: "lifecycle", header: "Estado", render: (row) => lifecycleLabel(row) },
      { key: "source", header: "Sketch", render: (row) => (row.hasSource ? "Sim" : "—") },
      {
        key: "artifact",
        header: "Bin",
        render: (row) =>
          row.hasArtifact && row.artifactSha256 ? (
            <code>{row.artifactSha256.slice(0, 10)}…</code>
          ) : (
            "—"
          ),
      },
      {
        key: "published",
        header: "Publicado",
        render: (row) => formatTimestamp(row.publishedAt),
      },
      {
        key: "actions",
        header: "",
        render: (row) => (
          <div className="pp-inline-actions">
            <PpActionButton
              variant="ghost"
              onClick={() =>
                navigateProductionPulse(productionPulseFirmwareDetailPath(row.id))
              }
            >
              Detalhe
            </PpActionButton>
            {canManage && isPublishedFirmware(row) ? (
              <PpActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => void handleUpdateFamily(row.firmwareKey)}
              >
                Atualizar ligados
              </PpActionButton>
            ) : null}
          </div>
        ),
      },
    ],
    [busy, canManage, handleUpdateFamily],
  );

  const jobColumns: DataTableColumn<FirmwareUpdateJob>[] = useMemo(
    () => [
      {
        key: "firmware",
        header: "Firmware",
        render: (row) => {
          const item = firmwareById.get(row.firmwareId);
          return item ? `${item.firmwareKey} · ${item.version}` : "—";
        },
      },
      {
        key: "trigger",
        header: "Disparo",
        render: (row) => (row.trigger === "manual" ? "Agora" : "Agendado"),
      },
      { key: "status", header: "Status", render: (row) => otaStatusLabel(row.status) },
      {
        key: "scheduled",
        header: "Agenda",
        render: (row) => formatTimestamp(row.scheduledAt),
      },
      { key: "created", header: "Criado", render: (row) => formatTimestamp(row.createdAt) },
      {
        key: "actions",
        header: "",
        render: (row) => (
          <div className="pp-inline-actions">
            <PpActionButton variant="ghost" onClick={() => void openJobDetails(row.id)}>
              {PP_HELP.hub.jobDetails}
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
    [canManage, firmwareById, openJobDetails],
  );

  const targetColumns: DataTableColumn<FirmwareUpdateTarget>[] = useMemo(
    () => [
      {
        key: "device",
        header: "Dispositivo",
        render: (row) =>
          devices.find((device) => device.id === row.deviceId)?.name ?? (
            <code>{row.deviceId.slice(0, 8)}</code>
          ),
      },
      { key: "from", header: "De", render: (row) => row.fromVersion ?? "—" },
      { key: "to", header: "Para", render: (row) => row.toVersion ?? "—" },
      { key: "status", header: "Status", render: (row) => otaStatusLabel(row.status) },
      {
        key: "progress",
        header: "Progresso",
        render: (row) => {
          const display = formatOtaProgressDisplay({
            status: row.status,
            progressPercent: row.progressPercent,
          });
          const bytes = formatOtaBytes(row.bytesReceived, row.bytesTotal);
          return <span>{bytes ? `${display} · ${bytes}` : display}</span>;
        },
      },
    ],
    [devices],
  );

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Hub OTA" badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar dispositivos."
        />
      </div>
    );
  }

  return (
    <div className="pp-page-stack pp-hub-page">
      <PpPageHero
        title="Hub OTA"
        badge={ppShellIcon}
        description={PP_HELP.hub.hero}
        actions={
          <div className="pp-hub-hero-actions">
            {branchOptions.length > 1 ? (
              <PpHintAction hint={PP_HELP.hub.branch} ariaLabel="Ajuda: Filial">
                <PpSegmentToggle
                  ariaLabel="Filial"
                  size="sm"
                  widthMode="content"
                  value={branch}
                  onChange={changeBranch}
                  options={branchOptions.map((item) => ({
                    value: item.id,
                    label: item.label,
                  }))}
                />
              </PpHintAction>
            ) : null}
            {canManage ? (
              <PpHintAction hint={PP_HELP.hub.newDevice} ariaLabel="Ajuda: Novo dispositivo">
                <PpActionButton
                  variant="ghost"
                  className="pp-hero-brand-btn"
                  onClick={() =>
                    navigateProductionPulse(productionPulseDeviceNewPath(branch))
                  }
                >
                  + Novo dispositivo
                </PpActionButton>
              </PpHintAction>
            ) : null}
            {canManage ? (
              <PpHintAction hint={PP_HELP.hub.newFirmware} ariaLabel="Ajuda: Novo firmware">
                <PpActionButton
                  variant="ghost"
                  className="pp-hero-brand-btn"
                  onClick={() =>
                    navigateProductionPulse(productionPulseFirmwareNewPath())
                  }
                >
                  + Novo firmware
                </PpActionButton>
              </PpHintAction>
            ) : null}
            <PpHintAction hint={PP_HELP.hub.refresh} ariaLabel="Ajuda: Atualizar hub">
              <PpActionButton
                variant="primary"
                className="pp-hero-brand-btn"
                onClick={() => {
                  void reloadGraph();
                  void reloadJobs({ soft: true });
                }}
                disabled={loading}
              >
                Atualizar
              </PpActionButton>
            </PpHintAction>
          </div>
        }
      />

      <HubOtaKpiStrip kpis={kpis} loading={loading} />

      {notice ? (
        <PpStateBox
          variant="empty"
          title="Publicação"
          message={notice}
          action={
            <PpActionButton variant="ghost" onClick={() => setNotice(null)}>
              Fechar
            </PpActionButton>
          }
        />
      ) : null}

      {error ? <PpStateBox variant="error" title="Erro" message={error} /> : null}

      <div id={HUB_SECTION_ID.canvas}>
        {loading ? (
          <PpStateBox variant="loading" title="Carregando firmwares e IoTs" />
        ) : (
          <PpSectionCard
            title={`Canvas · ${families.length} firmwares · ${devices.length} IoTs`}
            hint={PP_HELP.otaLinks.canvas}
          >
            <p className="pp-hub-legend">
              <span className="pp-hub-legend__item pp-hub-legend__item--solid">
                sólida = vínculo direto
              </span>
              <span className="pp-hub-legend__item pp-hub-legend__item--dashed">
                tracejada = via driver
              </span>
            </p>
            <FirmwareDeviceLinkCanvas
              families={families}
              devices={devices}
              canManage={canManage}
              onLinked={() => void reloadGraph()}
              onUnlink={handleUnlink}
              onUpdateDevice={handleUpdateDevice}
              onUpdateFamily={handleUpdateFamily}
              onSelectDevice={(deviceId) =>
                navigateProductionPulse(
                  productionPulseDeviceDetailPath(deviceId, "firmware"),
                )
              }
            />
          </PpSectionCard>
        )}
      </div>

      <div id={HUB_SECTION_ID.catalog}>
        <PpSectionCard
          title="Firmwares"
          hint={PP_HELP.hub.catalog}
          actions={
            canManage ? (
              <PpActionButton
                variant="ghost"
                onClick={() => navigateProductionPulse(productionPulseFirmwareNewPath())}
              >
                Novo firmware
              </PpActionButton>
            ) : undefined
          }
        >
          <PpCatalogSearchBar
            value={catalogSearch}
            onChange={setCatalogSearch}
            placeholder="Buscar família, versão, driver…"
          />
          {loading ? (
            <PpStateBox variant="loading" title="Carregando firmwares" />
          ) : filteredFirmwares.length === 0 ? (
            <PpStateBox
              variant="empty"
              title="Nenhum firmware"
              message={PP_HELP.ota.catalogEmpty}
            />
          ) : (
            <PpDataTable
              columns={firmwareColumns}
              rows={filteredFirmwares}
              rowKey={(row) => row.id}
              emptyMessage={PP_HELP.ota.catalogEmpty}
            />
          )}
        </PpSectionCard>
      </div>

      {canManage ? (
        <PpSectionCard title="Disparar atualização" hint={PP_HELP.ota.jobCreate}>
          <form className="pp-form-grid pp-hub-ota-form" onSubmit={(e) => void onCreateJob(e)}>
            <PpNativeSelectField
              id="ota-hub-firmware"
              label="Firmware"
              hint={PP_HELP.ota.jobFirmware}
              value={firmwareId}
              onChange={setFirmwareId}
              options={firmwareOptions}
              placeholderOption="Selecione…"
            />
            <PpNativeSelectField
              id="ota-hub-scope"
              label="Escopo"
              hint={PP_HELP.ota.jobScope}
              value={scope}
              onChange={(value) => setScope(value as "branch" | "device")}
              options={[
                { value: "branch", label: "Filial inteira" },
                { value: "device", label: "Dispositivo" },
              ]}
              searchable={false}
            />
            {scope === "device" ? (
              <PpNativeSelectField
                id="ota-hub-device"
                label="Dispositivo"
                hint={PP_HELP.ota.jobScopeDevice}
                value={scopeDeviceId}
                onChange={setScopeDeviceId}
                options={deviceOptions}
                placeholderOption="Selecione…"
              />
            ) : null}
            <div className="pp-hub-ota-form__trigger">
              <PpSegmentToggle
                ariaLabel={PP_HELP.ota.jobTrigger}
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
            <div className="pp-hub-ota-form__submit">
              <PpActionButton
                type="submit"
                disabled={
                  busy ||
                  publishedFirmwares.length === 0 ||
                  !firmwareId ||
                  (scope === "device" && !scopeDeviceId) ||
                  (trigger === "scheduled" && !scheduledAt)
                }
              >
                {busy ? "Disparando…" : "Disparar"}
              </PpActionButton>
            </div>
          </form>
        </PpSectionCard>
      ) : null}

      <div id={HUB_SECTION_ID.jobs}>
        <PpSectionCard title="Atualizações OTA" hint={PP_HELP.hub.jobs}>
          {jobsLoading && jobs.length === 0 ? (
            <PpStateBox variant="loading" title="Carregando atualizações" />
          ) : jobs.length === 0 ? (
            <PpStateBox
              variant="empty"
              title="Sem atualizações"
              message={PP_HELP.ota.jobsEmpty}
            />
          ) : (
            <PpDataTable
              columns={jobColumns}
              rows={jobs}
              rowKey={(row) => row.id}
              emptyMessage={PP_HELP.ota.jobsEmpty}
            />
          )}
        </PpSectionCard>
      </div>

      <PpHostContainedDialog
        open={Boolean(detailJobId)}
        title={PP_HELP.hub.targetsDialogTitle}
        onClose={() => {
          setDetailJobId(null);
          setTargets([]);
        }}
      >
        <p className="pp-muted">{PP_HELP.ota.targetsList}</p>
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
      </PpHostContainedDialog>

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
          <PpActionButton onClick={() => void confirmCancelJob()}>
            Cancelar atualização
          </PpActionButton>
        </div>
      </PpHostContainedDialog>
    </div>
  );
}
