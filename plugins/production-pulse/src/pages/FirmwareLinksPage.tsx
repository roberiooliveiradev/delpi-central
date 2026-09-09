import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveFirmware,
  cancelFirmwareUpdateJob,
  createFirmwareUpdateJob,
  fetchDevice,
  fetchDevices,
  fetchFirmwareUpdateJobs,
  fetchFirmwareUpdateSummary,
  fetchFirmwareUpdateTargets,
  fetchFirmwares,
  putDeviceFirmwareLink,
  replaceDevice,
  type FirmwareListItem,
  type FirmwareUpdateJob,
  type FirmwareUpdateSummary,
  type FirmwareUpdateTarget,
} from "../api/productionPulseApi";
import { AdminSidePanel } from "../components/AdminSidePanel";
import { DeviceCatalogPanel } from "../components/DeviceCatalogPanel";
import {
  EntityActionMenu,
  EntitySummaryPopover,
} from "../components/EntityContextLayers";
import {
  FirmwareDeviceLinkCanvas,
  type CanvasEntitySelection,
} from "../components/FirmwareDeviceLinkCanvas";
import { HubOtaKpiChips } from "../components/HubOtaKpiChips";
import {
  ConfirmDisableDialog,
  MiniInspectorPanel,
  RenameDeviceDialog,
} from "../components/MiniInspectorPanel";
import {
  PpActionButton,
  PpCatalogSearchBar,
  PpDataTable,
  PpHintAction,
  PpHostContainedDialog,
  PpHostContainedDrawer,
  PpNativeTextField,
  PpSegmentToggle,
  PpStateBox,
  type DataTableColumn,
} from "../app/productionPulseUi";
import { resolveBranchOptions } from "../constants/branches";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  productionPulseFirmwareLinksPath,
  type HubFocus,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { DeviceFormPage } from "../pages/DeviceFormPage";
import { FirmwareCreatePage } from "../pages/FirmwareCreatePage";
import { FirmwareDetailPage } from "../pages/FirmwareDetailPage";
import type { DeviceListItem } from "../types/device";
import {
  formatAdminEntity,
  hubFocusToPanel,
  parseAdminDrawer,
  parseAdminEntity,
  parseAdminPanel,
  type AdminEntityRef,
  type AdminHubDrawer,
  type AdminHubOpenLayer,
  type AdminHubPanel,
  type AdminHubUiState,
  INITIAL_ADMIN_HUB_UI,
} from "../utils/adminHubUiState";
import { uniqueFirmwareFamilies } from "../utils/firmwareLinkGraph";
import {
  computeHubOtaKpis,
  EMPTY_HUB_OTA_KPIS,
  isPublishedFirmware,
} from "../utils/hubOtaKpis";
import { replaceProductionPulse } from "../utils/navigation";
import {
  formatOtaBytes,
  formatOtaProgressDisplay,
  otaStatusLabel,
} from "../utils/otaStatusLabels";

type FirmwareLinksPageProps = {
  branch: string;
  highlightFirmwareKey?: string;
  focus?: HubFocus;
  entityParam?: string;
  panelParam?: string;
  drawerParam?: string;
  permissions: ProductionPulsePermissionFlags;
};

const JOBS_POLL_MS = 3000;

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
  entityParam,
  panelParam,
  drawerParam,
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
  const [cancelJobId, setCancelJobId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(
    highlightFirmwareKey
      ? `Firmware ${highlightFirmwareKey} publicado — ligue os IoTs no canvas.`
      : null,
  );
  const [ui, setUi] = useState<AdminHubUiState>(() => {
    const entity = parseAdminEntity(entityParam);
    const panel =
      parseAdminPanel(panelParam) ?? hubFocusToPanel(focus) ?? null;
    const drawer = parseAdminDrawer(drawerParam);
    let openLayer: AdminHubOpenLayer = "none";
    if (drawer) openLayer = "drawer";
    else if (panel) openLayer = "panel";
    else if (entity) openLayer = "summary";
    return {
      ...INITIAL_ADMIN_HUB_UI,
      selectedEntity: entity,
      panel,
      drawer,
      openLayer,
      popoverAnchorId: entity
        ? entity.type === "device"
          ? `dev:${entity.id}`
          : entity.type === "firmware"
            ? null
            : null
        : null,
    };
  });
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [renameDevice, setRenameDevice] = useState<DeviceListItem | null>(null);
  const [disableDeviceRow, setDisableDeviceRow] = useState<DeviceListItem | null>(null);
  const [scheduleContext, setScheduleContext] = useState<{
    firmwareId: string;
    deviceIds?: string[];
  } | null>(null);
  const [scheduledAt, setScheduledAt] = useState("");

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
  const activeJobCount = jobs.filter(
    (job) => job.status === "running" || job.status === "scheduled",
  ).length;

  const selectedDevice =
    ui.selectedEntity?.type === "device"
      ? devices.find((item) => item.id === ui.selectedEntity!.id) ?? null
      : null;

  const selectedFirmware =
    ui.selectedEntity?.type === "firmware"
      ? firmwareById.get(ui.selectedEntity.id) ??
        firmwares.find((item) => item.firmwareKey === ui.selectedEntity!.id) ??
        null
      : null;

  const selectedFamily = useMemo(() => {
    if (!ui.selectedEntity) return null;
    if (ui.selectedEntity.type === "firmware") {
      const fw = selectedFirmware;
      const key = fw?.firmwareKey ?? ui.selectedEntity.id;
      return families.find((family) => family.firmwareKey === key) ?? null;
    }
    if (ui.selectedEntity.type === "device" && selectedDevice) {
      const key =
        selectedDevice.assignedFirmwareKey ||
        selectedDevice.firmwareKey ||
        selectedDevice.driverKey;
      return families.find((family) => family.firmwareKey === key) ?? null;
    }
    return null;
  }, [families, selectedDevice, selectedFirmware, ui.selectedEntity]);

  const setLayer = useCallback(
    (patch: Partial<AdminHubUiState>, sync = true) => {
      setUi((current) => {
        const next = { ...current, ...patch };
        if (sync) {
          queueMicrotask(() => {
            replaceProductionPulse(
              productionPulseFirmwareLinksPath({
                branch,
                firmwareKey: highlightFirmwareKey,
                entity: formatAdminEntity(next.selectedEntity) ?? undefined,
                panel: next.panel ?? undefined,
                drawer: next.drawer ?? undefined,
                focus:
                  next.panel === "firmwares"
                    ? "catalog"
                    : next.panel === "jobs"
                      ? "jobs"
                      : undefined,
              }),
            );
          });
        }
        return next;
      });
    },
    [branch, highlightFirmwareKey],
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar o Admin.");
    } finally {
      setLoading(false);
    }
  }, [branch]);

  const reloadJobs = useCallback(
    async (opts?: { soft?: boolean }) => {
      const soft = Boolean(opts?.soft);
      if (!soft) setJobsLoading(true);
      try {
        setJobs(await fetchFirmwareUpdateJobs(branch));
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

  useEffect(() => {
    const entity = parseAdminEntity(entityParam);
    const panel = parseAdminPanel(panelParam) ?? hubFocusToPanel(focus);
    const drawer = parseAdminDrawer(drawerParam);
    setUi((current) => ({
      ...current,
      selectedEntity: entity,
      panel,
      drawer,
      openLayer: drawer
        ? "drawer"
        : panel
          ? "panel"
          : entity
            ? current.openLayer === "inspector"
              ? "inspector"
              : "summary"
            : "none",
    }));
  }, [drawerParam, entityParam, focus, panelParam]);

  const changeBranch = (nextBranch: string) => {
    replaceProductionPulse(
      productionPulseFirmwareLinksPath({
        branch: nextBranch,
        firmwareKey: highlightFirmwareKey,
        panel: ui.panel ?? undefined,
        drawer: ui.drawer ?? undefined,
        entity: formatAdminEntity(ui.selectedEntity) ?? undefined,
      }),
    );
  };

  const handleUnlink = useCallback(
    async (deviceId: string) => {
      await putDeviceFirmwareLink(deviceId, null);
      await reloadGraph();
    },
    [reloadGraph],
  );

  const runFamilyJob = useCallback(
    async (
      firmwareKey: string,
      deviceIds?: string[],
      opts?: { scheduledAt?: string },
    ) => {
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
          trigger: opts?.scheduledAt ? "scheduled" : "manual",
          scheduledAt: opts?.scheduledAt,
          filter,
        });
        await reloadJobs({ soft: true });
        await openJobDetails(job.id);
        setLayer({ panel: "jobs", openLayer: "panel", drawer: null });
      } catch (err) {
        setError(err instanceof Error ? err.message : PP_HELP.ota.deviceJobFailed);
      } finally {
        setBusy(false);
      }
    },
    [branch, openJobDetails, publishedFirmwares, reloadJobs, setLayer],
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
      /* soft refresh */
    }
    await reloadJobs({ soft: true });
    if (detailJobId === jobId) await loadTargets(jobId);
  };

  const resolveAnchor = (nodeId: string | null) => {
    if (!nodeId || typeof document === "undefined") return null;
    return (
      document.querySelector<HTMLElement>(`.react-flow__node[data-id="${nodeId}"]`) ??
      null
    );
  };

  const onSelectEntity = (selection: CanvasEntitySelection) => {
    const entity: AdminEntityRef =
      selection.type === "device"
        ? { type: "device", id: selection.id }
        : { type: "firmware", id: selection.id };
    const el = resolveAnchor(selection.nodeId);
    setAnchorEl(el);
    setLayer({
      selectedEntity: entity,
      openLayer: "summary",
      popoverAnchorId: selection.nodeId,
      panel: null,
      drawer: null,
    });
  };

  const onOpenDeviceMenu = (payload: { deviceId: string; nodeId: string }) => {
    setAnchorEl(resolveAnchor(payload.nodeId));
    setLayer({
      selectedEntity: { type: "device", id: payload.deviceId },
      openLayer: "menu",
      popoverAnchorId: payload.nodeId,
    });
  };

  const onOpenFirmwareMenu = (payload: {
    firmwareKey: string;
    firmwareId?: string | null;
    nodeId: string;
  }) => {
    setAnchorEl(resolveAnchor(payload.nodeId));
    setLayer({
      selectedEntity: {
        type: "firmware",
        id: payload.firmwareId || payload.firmwareKey,
      },
      openLayer: "menu",
      popoverAnchorId: payload.nodeId,
    });
  };

  const openPanel = (panel: AdminHubPanel) => {
    setLayer({ panel, openLayer: "panel", drawer: null });
  };

  const openDrawer = (drawer: AdminHubDrawer, entity?: AdminEntityRef | null) => {
    setLayer({
      drawer,
      openLayer: "drawer",
      panel: null,
      selectedEntity: entity === undefined ? ui.selectedEntity : entity,
    });
  };

  const closeLayers = () => {
    setAnchorEl(null);
    setLayer({
      openLayer: "none",
      panel: null,
      drawer: null,
      selectedEntity: null,
      popoverAnchorId: null,
    });
  };

  const onEntityAction = async (action: string) => {
    if (!ui.selectedEntity) return;
    if (ui.selectedEntity.type === "device") {
      const device = devices.find((item) => item.id === ui.selectedEntity!.id);
      if (!device) return;
      if (action === "edit") {
        openDrawer("device-edit", { type: "device", id: device.id });
        return;
      }
      if (action === "rename") {
        setRenameDevice(device);
        return;
      }
      if (action === "ota-now") {
        await handleUpdateDevice(device.id);
        return;
      }
      if (action === "ota-schedule") {
        const key = device.assignedFirmwareKey || device.firmwareKey || device.driverKey;
        const match = publishedFirmwares.find((item) => item.firmwareKey === key);
        if (!match) {
          setError(PP_HELP.ota.noPublishedFirmware);
          return;
        }
        setScheduleContext({ firmwareId: match.id, deviceIds: [device.id] });
        openDrawer("ota-schedule", { type: "device", id: device.id });
        return;
      }
      if (action === "unlink") {
        await handleUnlink(device.id);
        return;
      }
      if (action === "disable") {
        setDisableDeviceRow(device);
        return;
      }
      if (action === "enable") {
        const full = await fetchDevice(device.id);
        await replaceDevice(device.id, {
          name: full.name,
          branch: full.branch,
          ipAddress: full.ipAddress,
          controllerCode: full.controllerCode ?? "",
          firmwareSource: full.firmwareSource ?? "",
          wifiSsid: full.wifiSsid ?? "",
          wifiPassword: "",
          debounceMs: full.debounceMs != null ? String(full.debounceMs) : "",
          apiToken: "",
          apiTokenSet: Boolean(full.apiTokenSet),
          driverKey: full.driverKey,
          pollIntervalMs: full.pollIntervalMs,
          enabled: true,
        });
        await reloadGraph();
      }
      return;
    }
    if (ui.selectedEntity.type === "firmware") {
      const fw =
        firmwareById.get(ui.selectedEntity.id) ||
        firmwares.find((item) => item.firmwareKey === ui.selectedEntity!.id);
      if (!fw) return;
      if (action === "edit") {
        openDrawer("firmware-edit", { type: "firmware", id: fw.id });
        return;
      }
      if (action === "new-version") {
        openDrawer("firmware-create", { type: "firmware", id: fw.id });
        return;
      }
      if (action === "ota-now") {
        await handleUpdateFamily(fw.firmwareKey);
        return;
      }
      if (action === "ota-schedule") {
        setScheduleContext({ firmwareId: fw.id });
        openDrawer("ota-schedule", { type: "firmware", id: fw.id });
        return;
      }
      if (action === "archive") {
        await archiveFirmware(fw.id);
        await reloadGraph();
      }
    }
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
      {
        key: "actions",
        header: "",
        render: (row) => (
          <div className="pp-inline-actions">
            <PpActionButton
              variant="ghost"
              onClick={() => openDrawer("firmware-edit", { type: "firmware", id: row.id })}
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
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar dispositivos."
        />
      </div>
    );
  }

  const overlayTopLeft = (
    <div className="pp-map-overlay-stack">
      <div className="pp-map-overlay-title">
        <strong>Admin · OTA</strong>
        <span className="pp-muted">Mapa Firmware ↔ IoT</span>
      </div>
      <PpCatalogSearchBar
        value={ui.filters.q}
        onChange={(q) => setUi((current) => ({ ...current, filters: { ...current.filters, q } }))}
        placeholder="Buscar no mapa…"
      />
      <PpSegmentToggle
        ariaLabel="Filtro de status"
        size="sm"
        widthMode="content"
        value={ui.filters.status || "all"}
        onChange={(value) =>
          setUi((current) => ({
            ...current,
            filters: { ...current.filters, status: value === "all" ? "" : value },
          }))
        }
        options={[
          { value: "all", label: "Todos" },
          { value: "online", label: "Online" },
          { value: "offline", label: "Offline" },
          { value: "disabled", label: "Inativos" },
        ]}
      />
      <HubOtaKpiChips
        kpis={kpis}
        loading={loading}
        activeJobs={activeJobCount}
        onOpenJobs={() => openPanel("jobs")}
      />
      <p className="pp-hub-legend pp-hub-legend--compact">
        <span className="pp-hub-legend__item pp-hub-legend__item--solid">sólida = vínculo</span>
        <span className="pp-hub-legend__item pp-hub-legend__item--dashed">
          tracejada = driver
        </span>
      </p>
    </div>
  );

  const overlayTopRight = (
    <div className="pp-map-overlay-actions">
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
      <PpActionButton variant="ghost" onClick={() => openPanel("devices")}>
        IoTs
      </PpActionButton>
      <PpActionButton variant="ghost" onClick={() => openPanel("firmwares")}>
        Firmwares
      </PpActionButton>
      {canManage ? (
        <PpHintAction hint={PP_HELP.hub.newDevice} ariaLabel="Ajuda: Novo IoT">
          <PpActionButton onClick={() => openDrawer("device-create", null)}>+ IoT</PpActionButton>
        </PpHintAction>
      ) : null}
      {canManage ? (
        <PpHintAction hint={PP_HELP.hub.newFirmware} ariaLabel="Ajuda: Novo firmware">
          <PpActionButton onClick={() => openDrawer("firmware-create", null)}>+ FW</PpActionButton>
        </PpHintAction>
      ) : null}
      <PpHintAction hint={PP_HELP.hub.refresh} ariaLabel="Ajuda: Atualizar">
        <PpActionButton
          variant="primary"
          disabled={loading}
          onClick={() => {
            void reloadGraph();
            void reloadJobs({ soft: true });
          }}
        >
          ↻
        </PpActionButton>
      </PpHintAction>
    </div>
  );

  return (
    <div className="pp-admin-hub">
      {notice ? (
        <div className="pp-admin-hub__notice">
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
        </div>
      ) : null}
      {error ? (
        <div className="pp-admin-hub__notice">
          <PpStateBox variant="error" title="Erro" message={error} />
        </div>
      ) : null}

      <div className="pp-admin-viewport">
        {loading ? (
          <PpStateBox variant="loading" title="Carregando mapa Admin…" />
        ) : (
          <FirmwareDeviceLinkCanvas
            families={families}
            devices={devices}
            canManage={canManage}
            filterQuery={ui.filters.q}
            filterStatus={ui.filters.status}
            onLinked={() => void reloadGraph()}
            onUnlink={handleUnlink}
            onUpdateDevice={handleUpdateDevice}
            onUpdateFamily={handleUpdateFamily}
            onSelectEntity={onSelectEntity}
            onOpenDeviceMenu={onOpenDeviceMenu}
            onOpenFirmwareMenu={onOpenFirmwareMenu}
            onNodeDragStart={() => {
              if (ui.openLayer === "summary" || ui.openLayer === "menu") {
                setLayer({ openLayer: "none", popoverAnchorId: null }, false);
                setAnchorEl(null);
              }
            }}
            overlayTopLeft={overlayTopLeft}
            overlayTopRight={overlayTopRight}
          />
        )}

        <MiniInspectorPanel
          open={ui.openLayer === "inspector"}
          entity={ui.selectedEntity}
          device={selectedDevice}
          firmware={selectedFirmware}
          onClose={() => setLayer({ openLayer: "none" })}
          onEdit={() => {
            if (ui.selectedEntity?.type === "device") {
              openDrawer("device-edit", ui.selectedEntity);
            } else if (ui.selectedEntity?.type === "firmware") {
              openDrawer("firmware-edit", ui.selectedEntity);
            }
          }}
        />

        <AdminSidePanel
          open={ui.openLayer === "panel" && ui.panel === "firmwares"}
          title="Firmwares"
          onClose={() => setLayer({ panel: null, openLayer: "none" })}
        >
          <PpCatalogSearchBar
            value={catalogSearch}
            onChange={setCatalogSearch}
            placeholder="Buscar família, versão…"
          />
          {canManage ? (
            <PpActionButton
              className="pp-mb-sm"
              onClick={() => openDrawer("firmware-create", null)}
            >
              Novo firmware
            </PpActionButton>
          ) : null}
          <PpDataTable
            columns={firmwareColumns}
            rows={filteredFirmwares}
            rowKey={(row) => row.id}
            emptyMessage={PP_HELP.ota.catalogEmpty}
          />
        </AdminSidePanel>

        <AdminSidePanel
          open={ui.openLayer === "panel" && ui.panel === "jobs"}
          title="Jobs OTA"
          onClose={() => setLayer({ panel: null, openLayer: "none" })}
        >
          {jobsLoading && jobs.length === 0 ? (
            <PpStateBox variant="loading" title="Carregando atualizações" />
          ) : (
            <PpDataTable
              columns={jobColumns}
              rows={jobs}
              rowKey={(row) => row.id}
              emptyMessage={PP_HELP.ota.jobsEmpty}
            />
          )}
        </AdminSidePanel>

        <AdminSidePanel
          open={ui.openLayer === "panel" && ui.panel === "devices"}
          title="IoTs"
          onClose={() => setLayer({ panel: null, openLayer: "none" })}
        >
          <DeviceCatalogPanel
            search={`?branch=${encodeURIComponent(branch)}`}
            permissions={permissions}
          />
        </AdminSidePanel>
      </div>

      <EntitySummaryPopover
        open={ui.openLayer === "summary"}
        anchorEl={anchorEl}
        entity={ui.selectedEntity}
        device={selectedDevice}
        firmware={selectedFirmware}
        firmwareMeta={
          selectedFamily
            ? {
                displayName: selectedFamily.displayName,
                firmwareKey: selectedFamily.firmwareKey,
                version: selectedFamily.latestVersion,
                linkedCount: selectedFamily.linkedCount,
                outdatedCount: selectedFamily.outdatedCount,
              }
            : null
        }
        canManage={canManage}
        onClose={() => setLayer({ openLayer: "none" }, false)}
        onInspect={() => setLayer({ openLayer: "inspector" })}
        onOpenMenu={() => setLayer({ openLayer: "menu" }, false)}
        onPrimary={() => {
          if (ui.selectedEntity?.type === "device") {
            void handleUpdateDevice(ui.selectedEntity.id);
          } else if (selectedFamily) {
            void handleUpdateFamily(selectedFamily.firmwareKey);
          }
        }}
      />

      <EntityActionMenu
        open={ui.openLayer === "menu"}
        anchorEl={anchorEl}
        entity={ui.selectedEntity}
        device={selectedDevice}
        firmware={selectedFirmware}
        canManage={canManage}
        onClose={() => setLayer({ openLayer: "none" }, false)}
        onAction={(action) => void onEntityAction(action)}
      />

      <PpHostContainedDrawer
        open={ui.openLayer === "drawer" && ui.drawer === "device-create"}
        title="Novo IoT"
        onClose={closeLayers}
      >
        <DeviceFormPage
          mode="create"
          initialBranch={branch}
          permissions={permissions}
          embedded
          onCancel={closeLayers}
          onDone={() => {
            closeLayers();
            void reloadGraph();
          }}
        />
      </PpHostContainedDrawer>

      <PpHostContainedDrawer
        open={ui.openLayer === "drawer" && ui.drawer === "device-edit"}
        title="Editar IoT"
        onClose={closeLayers}
      >
        {ui.selectedEntity?.type === "device" ? (
          <DeviceFormPage
            mode="edit"
            deviceId={ui.selectedEntity.id}
            permissions={permissions}
            embedded
            onCancel={closeLayers}
            onDone={() => {
              closeLayers();
              void reloadGraph();
            }}
          />
        ) : null}
      </PpHostContainedDrawer>

      <PpHostContainedDrawer
        open={
          ui.openLayer === "drawer" &&
          (ui.drawer === "firmware-create" || ui.drawer === "firmware-version")
        }
        title="Novo firmware"
        onClose={closeLayers}
      >
        <FirmwareCreatePage
          branch={branch}
          permissions={permissions}
          embedded
          onCancel={closeLayers}
          onDone={() => {
            closeLayers();
            void reloadGraph();
            openPanel("firmwares");
          }}
        />
      </PpHostContainedDrawer>

      <PpHostContainedDrawer
        open={ui.openLayer === "drawer" && ui.drawer === "firmware-edit"}
        title="Firmware"
        onClose={closeLayers}
      >
        {ui.selectedEntity?.type === "firmware" ? (
          <FirmwareDetailPage
            firmwareId={
              firmwareById.get(ui.selectedEntity.id)?.id || ui.selectedEntity.id
            }
            permissions={permissions}
            embedded
            onCancel={closeLayers}
            onDone={() => {
              closeLayers();
              void reloadGraph();
            }}
          />
        ) : null}
      </PpHostContainedDrawer>

      <PpHostContainedDrawer
        open={ui.openLayer === "drawer" && ui.drawer === "ota-schedule"}
        title="Agendar atualização"
        onClose={closeLayers}
      >
        <PpNativeTextField
          id="ota-schedule-at"
          label="Agendar para"
          hint={PP_HELP.ota.jobScheduledAt}
          type="datetime-local"
          value={scheduledAt}
          onChange={setScheduledAt}
        />
        <div className="pp-inline-actions">
          <PpActionButton variant="ghost" onClick={closeLayers}>
            Cancelar
          </PpActionButton>
          <PpActionButton
            disabled={!scheduledAt || !scheduleContext}
            onClick={() => {
              if (!scheduleContext) return;
              const fw = firmwareById.get(scheduleContext.firmwareId);
              if (!fw) return;
              void runFamilyJob(fw.firmwareKey, scheduleContext.deviceIds, {
                scheduledAt,
              }).then(() => {
                setScheduleContext(null);
                setScheduledAt("");
                closeLayers();
              });
            }}
          >
            Agendar
          </PpActionButton>
        </div>
      </PpHostContainedDrawer>

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

      <RenameDeviceDialog
        open={Boolean(renameDevice)}
        device={renameDevice}
        onClose={() => setRenameDevice(null)}
        onRenamed={() => void reloadGraph()}
      />
      <ConfirmDisableDialog
        open={Boolean(disableDeviceRow)}
        device={disableDeviceRow}
        onClose={() => setDisableDeviceRow(null)}
        onDone={() => void reloadGraph()}
      />
    </div>
  );
}
