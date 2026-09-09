import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveFirmware,
  cancelFirmwareUpdateJob,
  createFirmwareUpdateJob,
  disableDevice,
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
import { HubCanvasLegend } from "../components/HubCanvasLegend";
import {
  MiniInspectorPanel,
  RenameDeviceDialog,
} from "../components/MiniInspectorPanel";
import {
  PpActionButton,
  PpCatalogSearchBar,
  PpConfirmDialog,
  PpDataTable,
  PpDetailDialog,
  PpFloatingNotices,
  PpHintAction,
  PpHostContainedDialog,
  PpIconButton,
  PpNativeTextField,
  PpOtaProgressBar,
  PpSegmentToggle,
  PpStateBox,
  PpWorkbenchDialog,
  useFloatingNotices,
  type DataTableColumn,
} from "../app/productionPulseUi";
import {
  Cpu,
  FileCode,
  ListTodo,
  Lock,
  LockOpen,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  RefreshCw,
} from "lucide-react";
import { resolveBranchOptions } from "../constants/branches";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  productionPulseFirmwareLinksPath,
  type HubFocus,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { DeviceDetailPage } from "../pages/DeviceDetailPage";
import { DeviceFormPage } from "../pages/DeviceFormPage";
import { FirmwareCreatePage } from "../pages/FirmwareCreatePage";
import { FirmwareDetailPage } from "../pages/FirmwareDetailPage";
import type { DeviceListItem } from "../types/device";
import {
  formatAdminEntity,
  hubFocusToPanel,
  parseAdminEntity,
  parseAdminPanel,
  resolveAdminModalFromQuery,
  type AdminEntityRef,
  type AdminHubConfirmKind,
  type AdminHubModal,
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
  /** Canonical URL `modal=`. */
  modalParam?: string;
  /** @deprecated Prefer `modalParam`. Legacy `drawer=` still resolved. */
  drawerParam?: string;
  permissions: ProductionPulsePermissionFlags;
};

const JOBS_POLL_MS = 3000;

function lifecycleLabel(row: FirmwareListItem): string {
  if (row.lifecycle === "draft") return PP_HELP.ota.status.draft;
  if (row.lifecycle === "archived") return PP_HELP.ota.statusArchived;
  return PP_HELP.ota.statusPublished;
}

export function FirmwareLinksPage({
  branch,
  highlightFirmwareKey,
  focus,
  entityParam,
  panelParam,
  modalParam,
  drawerParam,
  permissions,
}: FirmwareLinksPageProps) {
  const canManage = permissions.canManageDevices;
  const branchOptions = useMemo(
    () => resolveBranchOptions(permissions.allowedBranches),
    [permissions.allowedBranches],
  );
  const {
    items: floatingNotices,
    push: pushNotice,
    dismiss: dismissNotice,
  } = useFloatingNotices();

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
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [ui, setUi] = useState<AdminHubUiState>(() => {
    const entity = parseAdminEntity(entityParam);
    const panel =
      parseAdminPanel(panelParam) ?? hubFocusToPanel(focus) ?? null;
    const modal = resolveAdminModalFromQuery({
      modal: modalParam,
      drawer: drawerParam,
    });
    let openLayer: AdminHubOpenLayer = "none";
    if (modal) openLayer = "modal";
    else if (panel) openLayer = "panel";
    else if (entity) openLayer = "summary";
    return {
      ...INITIAL_ADMIN_HUB_UI,
      selectedEntity: entity,
      panel,
      modal,
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
  const [scheduleContext, setScheduleContext] = useState<{
    firmwareId: string;
    deviceIds?: string[];
  } | null>(null);
  const [scheduledAt, setScheduledAt] = useState("");
  const [leftChromeCollapsed, setLeftChromeCollapsed] = useState(false);
  const [nodesLocked, setNodesLocked] = useState(false);

  useEffect(() => {
    if (!highlightFirmwareKey) return;
    pushNotice({
      id: "publish-highlight",
      variant: "success",
      title: "Publicação",
      message: `Firmware ${highlightFirmwareKey} publicado — ligue os IoTs no canvas.`,
    });
  }, [highlightFirmwareKey, pushNotice]);

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
                modal: next.modal ?? undefined,
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
      setLayer({
        modal: "job-detail",
        openLayer: "modal",
        panel: null,
        selectedEntity: { type: "job", id: jobId },
        confirm: null,
      });
      await loadTargets(jobId);
    },
    [loadTargets, setLayer],
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
    const modal = resolveAdminModalFromQuery({
      modal: modalParam,
      drawer: drawerParam,
    });
    setUi((current) => ({
      ...current,
      selectedEntity: entity,
      panel,
      modal,
      openLayer: modal
        ? "modal"
        : panel
          ? "panel"
          : entity
            ? current.openLayer === "inspector"
              ? "inspector"
              : "summary"
            : "none",
    }));
    if (modal === "job-detail" && entity?.type === "job") {
      setDetailJobId(entity.id);
      void loadTargets(entity.id);
    }
  }, [drawerParam, entityParam, focus, loadTargets, modalParam, panelParam]);

  const changeBranch = (nextBranch: string) => {
    replaceProductionPulse(
      productionPulseFirmwareLinksPath({
        branch: nextBranch,
        firmwareKey: highlightFirmwareKey,
        panel: ui.panel ?? undefined,
        modal: ui.modal ?? undefined,
        entity: formatAdminEntity(ui.selectedEntity) ?? undefined,
      }),
    );
  };

  const handleUnlink = useCallback(
    async (deviceId: string) => {
      await putDeviceFirmwareLink(deviceId, null);
      await reloadGraph();
      pushNotice({
        variant: "success",
        message: "Vínculo firmware ↔ IoT removido.",
      });
    },
    [pushNotice, reloadGraph],
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
      if (hasActiveJob) {
        pushNotice({
          id: "ota-active-job-warning",
          variant: "warning",
          title: "Job OTA em andamento",
          message: "Já existe uma atualização ativa. Você pode acompanhar os jobs em paralelo.",
          autoDismissMs: 7500,
          action: {
            label: "Ver Jobs",
            onClick: () => {
              setLayer({ panel: "jobs", openLayer: "panel", modal: null });
            },
          },
        });
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
        pushNotice({
          variant: "success",
          message: "Atualização OTA iniciada.",
        });
        await openJobDetails(job.id);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : PP_HELP.ota.deviceJobFailed;
        setError(message);
        pushNotice({
          variant: "error",
          title: "Falha OTA",
          message,
        });
      } finally {
        setBusy(false);
      }
    },
    [
      branch,
      hasActiveJob,
      openJobDetails,
      publishedFirmwares,
      pushNotice,
      reloadJobs,
      setLayer,
    ],
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
    if (!ui.confirm || ui.confirm.kind !== "cancel-job" || !canManage) return;
    const jobId = ui.confirm.id;
    setConfirmBusy(true);
    try {
      await cancelFirmwareUpdateJob(jobId);
      pushNotice({ variant: "success", message: "Atualização cancelada." });
    } catch {
      pushNotice({
        variant: "warning",
        message: "Não foi possível cancelar; a lista será atualizada.",
      });
    } finally {
      setConfirmBusy(false);
      setLayer({ confirm: null, openLayer: ui.modal ? "modal" : ui.panel ? "panel" : "none" });
    }
    await reloadJobs({ soft: true });
    if (detailJobId === jobId) await loadTargets(jobId);
  };

  const openConfirm = (kind: AdminHubConfirmKind, id: string) => {
    setLayer({ confirm: { kind, id }, openLayer: "confirm" }, false);
  };

  const closeConfirm = () => {
    setLayer(
      {
        confirm: null,
        openLayer: ui.modal ? "modal" : ui.panel ? "panel" : "none",
      },
      false,
    );
  };

  const runConfirmAction = async () => {
    if (!ui.confirm || !canManage) return;
    const { kind, id } = ui.confirm;
    if (kind === "cancel-job") {
      await confirmCancelJob();
      return;
    }
    setConfirmBusy(true);
    try {
      if (kind === "disable-device") {
        await disableDevice(id);
        pushNotice({
          variant: "success",
          message: "IoT desativado (soft delete). Use o filtro Inativos ou Reativar no menu ⋯.",
        });
        await reloadGraph();
      } else if (kind === "archive-firmware") {
        await archiveFirmware(id);
        pushNotice({
          variant: "success",
          message: "Versão arquivada (soft delete). Não entra em novos disparos OTA.",
        });
        await reloadGraph();
      } else if (kind === "unlink") {
        await handleUnlink(id);
        pushNotice({
          variant: "info",
          message:
            "Vínculo explícito removido. Se permanecer uma linha tracejada, é herança pelo driver (só leitura).",
          autoDismissMs: 8000,
        });
      }
      closeConfirm();
    } catch (err) {
      pushNotice({
        variant: "error",
        message: err instanceof Error ? err.message : "Falha ao confirmar a ação.",
      });
    } finally {
      setConfirmBusy(false);
    }
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
      modal: null,
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
    setLayer({ panel, openLayer: "panel", modal: null });
  };

  const openModal = (modal: AdminHubModal, entity?: AdminEntityRef | null) => {
    setLayer({
      modal,
      openLayer: "modal",
      panel: null,
      confirm: null,
      selectedEntity: entity === undefined ? ui.selectedEntity : entity,
    });
  };

  const closeLayers = () => {
    setAnchorEl(null);
    setDetailJobId(null);
    setTargets([]);
    setLayer({
      openLayer: "none",
      panel: null,
      modal: null,
      confirm: null,
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
        openModal("device-edit", { type: "device", id: device.id });
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
        openModal("ota-schedule", { type: "device", id: device.id });
        return;
      }
      if (action === "unlink") {
        openConfirm("unlink", device.id);
        return;
      }
      if (action === "disable") {
        openConfirm("disable-device", device.id);
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
        pushNotice({ variant: "success", message: "IoT reativado." });
      }
      return;
    }
    if (ui.selectedEntity.type === "firmware") {
      const fw =
        firmwareById.get(ui.selectedEntity.id) ||
        firmwares.find((item) => item.firmwareKey === ui.selectedEntity!.id);
      if (!fw) return;
      if (action === "edit") {
        openModal("firmware-detail", { type: "firmware", id: fw.id });
        return;
      }
      if (action === "new-version") {
        openModal("firmware-version", { type: "firmware", id: fw.id });
        return;
      }
      if (action === "ota-now") {
        await handleUpdateFamily(fw.firmwareKey);
        return;
      }
      if (action === "ota-schedule") {
        setScheduleContext({ firmwareId: fw.id });
        openModal("ota-schedule", { type: "firmware", id: fw.id });
        return;
      }
      if (action === "archive") {
        openConfirm("archive-firmware", fw.id);
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
              onClick={() => openModal("firmware-detail", { type: "firmware", id: row.id })}
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
              <PpActionButton
                variant="ghost"
                onClick={() => openConfirm("cancel-job", row.id)}
              >
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

  const overlayTopLeft = leftChromeCollapsed ? (
    <div className="pp-map-overlay-stack pp-map-overlay-stack--collapsed">
      <PpHintAction hint={PP_HELP.hub.collapseFilters} ariaLabel="Ajuda: Expandir filtros">
        <PpIconButton
          aria-label="Expandir filtros do mapa"
          aria-expanded={false}
          onClick={() => setLeftChromeCollapsed(false)}
        >
          <PanelLeftOpen size={18} />
        </PpIconButton>
      </PpHintAction>
    </div>
  ) : (
    <div className="pp-map-overlay-stack">
      <div className="pp-map-overlay-title">
        <div className="pp-map-overlay-title__row">
          <strong>Admin · OTA</strong>
          <PpHintAction hint={PP_HELP.hub.collapseFilters} ariaLabel="Ajuda: Recolher filtros">
            <PpIconButton
              aria-label="Recolher filtros do mapa"
              aria-expanded={true}
              onClick={() => setLeftChromeCollapsed(true)}
            >
              <PanelLeftClose size={16} />
            </PpIconButton>
          </PpHintAction>
        </div>
        <span className="pp-muted">Mapa Firmware ↔ IoT</span>
      </div>
      <PpHintAction hint={PP_HELP.hub.mapSearch} ariaLabel="Ajuda: Buscar no mapa">
        <div>
          <PpCatalogSearchBar
            value={ui.filters.q}
            onChange={(q) =>
              setUi((current) => ({ ...current, filters: { ...current.filters, q } }))
            }
            placeholder="Buscar no mapa…"
          />
        </div>
      </PpHintAction>
      <PpHintAction hint={PP_HELP.hub.statusFilter} ariaLabel="Ajuda: Filtro de status">
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
      </PpHintAction>
      <HubOtaKpiChips
        kpis={kpis}
        loading={loading}
        activeJobs={activeJobCount}
        onOpenJobs={() => openPanel("jobs")}
      />
      <HubCanvasLegend />
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
      <PpHintAction hint={PP_HELP.hub.panelDevices} ariaLabel="Ajuda: Painel IoTs">
        <PpActionButton variant="ghost" onClick={() => openPanel("devices")}>
          <Cpu size={14} aria-hidden="true" /> IoTs
        </PpActionButton>
      </PpHintAction>
      <PpHintAction hint={PP_HELP.hub.panelFirmwares} ariaLabel="Ajuda: Painel Firmwares">
        <PpActionButton variant="ghost" onClick={() => openPanel("firmwares")}>
          <FileCode size={14} aria-hidden="true" /> Firmwares
        </PpActionButton>
      </PpHintAction>
      <PpHintAction hint={PP_HELP.hub.panelJobs} ariaLabel="Ajuda: Painel Jobs">
        <PpActionButton variant="ghost" onClick={() => openPanel("jobs")}>
          <ListTodo size={14} aria-hidden="true" />
          Jobs{activeJobCount > 0 ? ` · ${activeJobCount}` : ""}
        </PpActionButton>
      </PpHintAction>
      {canManage ? (
        <PpHintAction hint={PP_HELP.hub.newDevice} ariaLabel="Ajuda: Novo IoT">
          <PpActionButton onClick={() => openModal("device-create", null)}>
            <Plus size={14} aria-hidden="true" /> IoT
          </PpActionButton>
        </PpHintAction>
      ) : null}
      {canManage ? (
        <PpHintAction hint={PP_HELP.hub.newFirmware} ariaLabel="Ajuda: Novo firmware">
          <PpActionButton onClick={() => openModal("firmware-create", null)}>
            <Plus size={14} aria-hidden="true" /> FW
          </PpActionButton>
        </PpHintAction>
      ) : null}
      <PpHintAction hint={PP_HELP.hub.refresh} ariaLabel="Ajuda: Atualizar">
        <PpIconButton
          aria-label="Atualizar mapa"
          disabled={loading}
          onClick={() => {
            void reloadGraph();
            void reloadJobs({ soft: true });
          }}
        >
          <RefreshCw size={16} />
        </PpIconButton>
      </PpHintAction>
    </div>
  );

  const overlayBottom = (
    <div className="pp-admin-bottom-bar" role="status" aria-label="Resumo do mapa">
      <PpHintAction hint={PP_HELP.hub.bottomBar} ariaLabel="Ajuda: Resumo do mapa">
        <span>
          {families.length} firmware{families.length === 1 ? "" : "s"} · {devices.length} IoT
          {devices.length === 1 ? "" : "s"}
        </span>
      </PpHintAction>
      {activeJobCount > 0 ? (
        <PpHintAction hint={PP_HELP.hub.kpiJobsChip} ariaLabel="Ajuda: Jobs ativos">
          <button type="button" className="pp-admin-bottom-bar__link" onClick={() => openPanel("jobs")}>
            Job●{activeJobCount}
          </button>
        </PpHintAction>
      ) : (
        <span className="pp-muted">Sem jobs ativos</span>
      )}
      <PpHintAction hint={PP_HELP.hub.lockNodes} ariaLabel="Ajuda: Bloquear nós">
        <PpIconButton
          aria-label={nodesLocked ? "Desbloquear nós" : "Bloquear nós"}
          onClick={() => setNodesLocked((value) => !value)}
        >
          {nodesLocked ? <Lock size={16} /> : <LockOpen size={16} />}
        </PpIconButton>
      </PpHintAction>
      <PpHintAction hint={PP_HELP.hub.refresh} ariaLabel="Ajuda: Atualizar">
        <PpIconButton
          aria-label="Atualizar"
          disabled={loading}
          onClick={() => {
            void reloadGraph();
            void reloadJobs({ soft: true });
          }}
        >
          <RefreshCw size={16} />
        </PpIconButton>
      </PpHintAction>
    </div>
  );

  return (
    <div className="pp-admin-hub">
      <PpFloatingNotices items={floatingNotices} onDismiss={dismissNotice} />
      {error ? (
        <div className="pp-admin-hub__notice">
          <PpStateBox
            variant="error"
            title="Erro"
            message={error}
            action={
              <PpActionButton variant="ghost" onClick={() => setError(null)}>
                Fechar
              </PpActionButton>
            }
          />
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
            overlayBottom={overlayBottom}
            nodesLocked={nodesLocked}
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
              openModal("device-edit", ui.selectedEntity);
            } else if (ui.selectedEntity?.type === "firmware") {
              openModal("firmware-detail", ui.selectedEntity);
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
              onClick={() => openModal("firmware-create", null)}
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
        onInspect={() => {
          if (ui.selectedEntity?.type === "device") {
            openModal("device-detail", ui.selectedEntity);
            return;
          }
          if (ui.selectedEntity?.type === "firmware") {
            openModal("firmware-detail", ui.selectedEntity);
            return;
          }
          setLayer({ openLayer: "inspector" });
        }}
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

      <PpWorkbenchDialog
        open={ui.openLayer === "modal" && ui.modal === "device-create"}
        title="Novo IoT"
        onClose={closeLayers}
      >
        <DeviceFormPage
          mode="create"
          initialBranch={branch}
          permissions={permissions}
          embedded
          onProbeNotice={(message, variant) =>
            pushNotice({ message, variant: variant ?? "info" })
          }
          onCancel={closeLayers}
          onDone={() => {
            closeLayers();
            void reloadGraph();
            pushNotice({ variant: "success", message: "IoT criado." });
          }}
        />
      </PpWorkbenchDialog>

      <PpWorkbenchDialog
        open={ui.openLayer === "modal" && ui.modal === "device-edit"}
        title="Editar IoT"
        onClose={closeLayers}
      >
        {ui.selectedEntity?.type === "device" ? (
          <DeviceFormPage
            mode="edit"
            deviceId={ui.selectedEntity.id}
            permissions={permissions}
            embedded
            onProbeNotice={(message, variant) =>
              pushNotice({ message, variant: variant ?? "info" })
            }
            onCancel={closeLayers}
            onDone={() => {
              closeLayers();
              void reloadGraph();
              pushNotice({ variant: "success", message: "IoT atualizado." });
            }}
          />
        ) : null}
      </PpWorkbenchDialog>

      <PpWorkbenchDialog
        open={
          ui.openLayer === "modal" &&
          (ui.modal === "firmware-create" || ui.modal === "firmware-version")
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
            pushNotice({ variant: "success", message: "Firmware criado." });
          }}
        />
      </PpWorkbenchDialog>

      <PpDetailDialog
        open={ui.openLayer === "modal" && ui.modal === "firmware-detail"}
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
      </PpDetailDialog>

      <PpDetailDialog
        open={ui.openLayer === "modal" && ui.modal === "device-detail"}
        title="Detalhe do IoT"
        onClose={closeLayers}
      >
        {ui.selectedEntity?.type === "device" ? (
          <DeviceDetailPage
            deviceId={ui.selectedEntity.id}
            tab="overview"
            search={`?branch=${encodeURIComponent(branch)}`}
            permissions={permissions}
            embedded
            onClose={closeLayers}
          />
        ) : null}
      </PpDetailDialog>

      <PpHostContainedDialog
        open={ui.openLayer === "modal" && ui.modal === "ota-schedule"}
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
              });
            }}
          >
            Agendar
          </PpActionButton>
        </div>
      </PpHostContainedDialog>

      <PpDetailDialog
        open={
          (ui.openLayer === "modal" && ui.modal === "job-detail") ||
          Boolean(detailJobId && ui.modal === "job-detail")
        }
        title={PP_HELP.hub.targetsDialogTitle}
        onClose={() => {
          setDetailJobId(null);
          setTargets([]);
          setLayer({
            modal: null,
            openLayer: ui.panel ? "panel" : "none",
            selectedEntity:
              ui.selectedEntity?.type === "job" ? null : ui.selectedEntity,
          });
        }}
      >
        <p className="pp-muted">{PP_HELP.ota.targetsList}</p>
        {targets.length === 0 ? (
          <PpStateBox variant="empty" title="Sem targets" />
        ) : (
          <>
            {targets.some(
              (row) =>
                typeof row.progressPercent === "number" &&
                Number.isFinite(row.progressPercent),
            ) ? (
              <div className="pp-mb-sm">
                <PpOtaProgressBar
                  value={Math.round(
                    targets.reduce(
                      (sum, row) => sum + (row.progressPercent ?? 0),
                      0,
                    ) / Math.max(1, targets.length),
                  )}
                  ariaLabel="Progresso médio do job OTA"
                />
              </div>
            ) : null}
            <PpDataTable
              columns={targetColumns}
              rows={targets}
              rowKey={(row) => row.id}
              emptyMessage="Sem targets"
            />
          </>
        )}
      </PpDetailDialog>

      <PpConfirmDialog
        open={ui.openLayer === "confirm" && ui.confirm?.kind === "cancel-job"}
        title={PP_HELP.ota.cancelConfirmTitle}
        message={PP_HELP.ota.cancelConfirmBody}
        confirmLabel="Cancelar atualização"
        cancelLabel="Voltar"
        variant="danger"
        confirmBusy={confirmBusy}
        onConfirm={() => void runConfirmAction()}
        onCancel={closeConfirm}
      />

      <PpConfirmDialog
        open={ui.openLayer === "confirm" && ui.confirm?.kind === "disable-device"}
        title={PP_HELP.hub.softDeleteDeviceConfirmTitle}
        message={
          selectedDevice || devices.find((d) => d.id === ui.confirm?.id)
            ? `${PP_HELP.hub.softDeleteDeviceConfirmBody} (${
                selectedDevice?.name ??
                devices.find((d) => d.id === ui.confirm?.id)?.name ??
                "IoT"
              })`
            : PP_HELP.hub.softDeleteDeviceConfirmBody
        }
        confirmLabel={PP_HELP.hub.softDeleteDeviceConfirmLabel}
        cancelLabel="Voltar"
        variant="danger"
        confirmBusy={confirmBusy}
        onConfirm={() => void runConfirmAction()}
        onCancel={closeConfirm}
      />

      <PpConfirmDialog
        open={ui.openLayer === "confirm" && ui.confirm?.kind === "archive-firmware"}
        title={PP_HELP.hub.softDeleteFirmwareConfirmTitle}
        message={PP_HELP.hub.softDeleteFirmwareConfirmBody}
        confirmLabel={PP_HELP.hub.softDeleteFirmwareConfirmLabel}
        cancelLabel="Voltar"
        variant="danger"
        confirmBusy={confirmBusy}
        onConfirm={() => void runConfirmAction()}
        onCancel={closeConfirm}
      />

      <PpConfirmDialog
        open={ui.openLayer === "confirm" && ui.confirm?.kind === "unlink"}
        title="Remover vínculo"
        message="Remover o vínculo firmware ↔ IoT deste dispositivo?"
        confirmLabel="Remover vínculo"
        cancelLabel="Voltar"
        variant="danger"
        confirmBusy={confirmBusy}
        onConfirm={() => void runConfirmAction()}
        onCancel={closeConfirm}
      />

      <RenameDeviceDialog
        open={Boolean(renameDevice)}
        device={renameDevice}
        onClose={() => setRenameDevice(null)}
        onRenamed={() => void reloadGraph()}
      />
    </div>
  );
}
