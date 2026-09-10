import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  archiveDriver,
  archiveFirmware,
  cancelFirmwareUpdateJob,
  createFirmwareUpdateJob,
  disableDevice,
  fetchDevice,
  fetchDeviceFirmwareUpdateStatus,
  fetchDevices,
  fetchFirmwareUpdateJobs,
  fetchFirmwareUpdateSummary,
  fetchFirmwareUpdateTargets,
  fetchFirmwares,
  listDrivers,
  putDeviceFirmwareLink,
  replaceDevice,
  unarchiveDriver,
  type DriverListItem,
  type FirmwareListItem,
  type FirmwareUpdateJob,
  type FirmwareUpdateSummary,
  type FirmwareUpdateTarget,
} from "../api/productionPulseApi";
import { DeviceCatalogPanel } from "../components/DeviceCatalogPanel";
import {
  EntityActionMenu,
  EntitySummaryPopover,
} from "../components/EntityContextLayers";
import {
  FirmwareDeviceLinkCanvas,
  type CanvasEntitySelection,
  type LinkCandidateRequest,
} from "../components/FirmwareDeviceLinkCanvas";
import { HubOtaKpiChips } from "../components/HubOtaKpiChips";
import { HubCanvasLegend } from "../components/HubCanvasLegend";
import {
  MiniInspectorPanel,
  RenameDeviceDialog,
} from "../components/MiniInspectorPanel";
import { ProductionPulseRequestError } from "../api/httpClient";
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
import { DriverTypeListItem } from "../components/drivers/DriverTypeListItem";
import { FirmwareCatalogListItem } from "../components/firmware/FirmwareCatalogListItem";
import { OtaStatusIndicator } from "../components/ota/OtaStatusIndicator";
import { OtaJobListItem } from "../components/ota/OtaJobListItem";
import { OtaTargetProgress } from "../components/ota/OtaTargetProgress";
import { useProductionPulseOtaMonitor } from "../hooks/useProductionPulseOtaMonitor";
import {
  CircuitBoard,
  Cpu,
  FileCode,
  Link2,
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
import { DriverDetailPage } from "../pages/DriverDetailPage";
import { DriverFormPage } from "../pages/DriverFormPage";
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
import {
  transitionAdminHub,
  type AdminHubAction,
} from "../utils/adminHubLayerTransitions";
import {
  isOperationalNoticeOnly,
  resolveProductionPulseError,
} from "../utils/apiErrors";
import {
  uniqueFirmwareFamilies,
  type LinkMode,
} from "../utils/firmwareLinkGraph";
import {
  computeHubOtaKpis,
  EMPTY_HUB_OTA_KPIS,
  isPublishedFirmware,
} from "../utils/hubOtaKpis";
import { replaceProductionPulse } from "../utils/navigation";
import { summarizeOtaJobTargets } from "../utils/otaJobSummary";
import {
  otaActiveNoticeId,
  otaJobCreatedNoticeId,
  pushResolvedProductionPulseNotice,
} from "../utils/pushResolvedNotice";

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
  const [drivers, setDrivers] = useState<DriverListItem[]>([]);
  const [devices, setDevices] = useState<DeviceListItem[]>([]);
  const [updateSummary, setUpdateSummary] = useState<FirmwareUpdateSummary | null>(null);
  const [jobs, setJobs] = useState<FirmwareUpdateJob[]>([]);
  const [targets, setTargets] = useState<FirmwareUpdateTarget[]>([]);
  const [detailJobId, setDetailJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [driversLoading, setDriversLoading] = useState(false);
  const [structuralError, setStructuralError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [driversSearch, setDriversSearch] = useState("");
  const [linkMode, setLinkMode] = useState<LinkMode | null>(null);
  const [pendingReplaceLink, setPendingReplaceLink] = useState<{
    deviceId: string;
    firmwareKey: string;
  } | null>(null);
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
    // Never force summary from entity alone (H2) — hydrateFromUrl owns URL restore.
    return {
      ...INITIAL_ADMIN_HUB_UI,
      selectedEntity: modal ? entity : null,
      panel,
      modal,
      openLayer,
      popoverAnchorId: null,
    };
  });
  const uiRef = useRef(ui);
  useEffect(() => {
    uiRef.current = ui;
  }, [ui]);
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

  const kpis = useMemo(() => {
    if (loading) return EMPTY_HUB_OTA_KPIS;
    return computeHubOtaKpis({ firmwares, devices, updateSummary });
  }, [devices, firmwares, loading, updateSummary]);

  const deviceNameById = useMemo(
    () => new Map(devices.map((device) => [device.id, device.name])),
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

  const filteredDrivers = useMemo(() => {
    const query = driversSearch.trim().toLowerCase();
    if (!query) return drivers;
    return drivers.filter((item) =>
      [
        item.key,
        item.labelPt,
        item.protocolKind,
        item.roleKey,
        item.archivedAt ? "archived" : "active",
      ]
        .join(" ")
        .toLowerCase()
        .includes(query),
    );
  }, [drivers, driversSearch]);

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

  const resolveAnchor = useCallback((nodeId: string | null) => {
    if (!nodeId || typeof document === "undefined") return null;
    return (
      document.querySelector<HTMLElement>(`.react-flow__node[data-id="${nodeId}"]`) ??
      null
    );
  }, []);

  const dispatch = useCallback(
    (action: AdminHubAction) => {
      const result = transitionAdminHub(uiRef.current, action);
      uiRef.current = result.state;
      setUi(result.state);
      if (result.clearAnchor) {
        setAnchorEl(null);
      } else if (result.popoverNodeId) {
        setAnchorEl(resolveAnchor(result.popoverNodeId));
      }
      if (result.syncUrl) {
        replaceProductionPulse(
          productionPulseFirmwareLinksPath({
            branch,
            firmwareKey: highlightFirmwareKey,
            entity: result.urlSlice.entity ?? undefined,
            panel: result.urlSlice.panel ?? undefined,
            modal: result.urlSlice.modal ?? undefined,
            focus:
              result.urlSlice.panel === "firmwares"
                ? "catalog"
                : result.urlSlice.panel === "jobs"
                  ? "jobs"
                  : undefined,
          }),
        );
      }
    },
    [branch, highlightFirmwareKey, resolveAnchor],
  );

  const reloadGraph = useCallback(async () => {
    dispatch({ type: "graphReloading" });
    setLoading(true);
    setStructuralError(null);
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
      setStructuralError(
        err instanceof Error ? err.message : "Falha ao carregar o Admin.",
      );
    } finally {
      setLoading(false);
    }
  }, [branch, dispatch]);

  const reloadJobs = useCallback(
    async (opts?: { soft?: boolean }) => {
      const soft = Boolean(opts?.soft);
      if (!soft) setJobsLoading(true);
      try {
        setJobs(await fetchFirmwareUpdateJobs(branch));
      } catch (err) {
        if (!soft) {
          setStructuralError(
            err instanceof Error
              ? err.message
              : "Falha ao carregar atualizações OTA.",
          );
        }
      } finally {
        if (!soft) setJobsLoading(false);
      }
    },
    [branch],
  );

  const softReloadJobs = useCallback(() => {
    void reloadJobs({ soft: true });
  }, [reloadJobs]);

  const otaMonitor = useProductionPulseOtaMonitor({
    jobs,
    reloadJobs: softReloadJobs,
    pushNotice,
    deviceNameById,
  });

  const hubKpis = useMemo(
    () => ({
      ...kpis,
      updatingDevices:
        otaMonitor.activeTargetCount > 0
          ? otaMonitor.activeTargetCount
          : kpis.updatingDevices,
      failedDevices:
        otaMonitor.failedOpenCount > 0
          ? otaMonitor.failedOpenCount
          : kpis.failedDevices,
    }),
    [kpis, otaMonitor.activeTargetCount, otaMonitor.failedOpenCount],
  );

  const reloadDrivers = useCallback(async () => {
    setDriversLoading(true);
    try {
      setDrivers(await listDrivers({ includeArchived: true }));
    } catch (err) {
      pushNotice({
        variant: "error",
        message: err instanceof Error ? err.message : "Falha ao carregar tipos de driver.",
      });
    } finally {
      setDriversLoading(false);
    }
  }, [pushNotice]);

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
      dispatch({
        type: "openModal",
        modal: "job-detail",
        entity: { type: "job", id: jobId },
      });
      await loadTargets(jobId);
    },
    [dispatch, loadTargets],
  );

  useEffect(() => {
    void reloadGraph();
  }, [reloadGraph]);

  useEffect(() => {
    void reloadJobs();
  }, [reloadJobs]);

  useEffect(() => {
    if (ui.openLayer === "panel" && ui.panel === "drivers") {
      void reloadDrivers();
    }
  }, [reloadDrivers, ui.openLayer, ui.panel]);

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
    const panel = parseAdminPanel(panelParam) ?? hubFocusToPanel(focus) ?? null;
    const modal = resolveAdminModalFromQuery({
      modal: modalParam,
      drawer: drawerParam,
    });
    dispatch({
      type: "hydrateFromUrl",
      entity,
      panel,
      modal,
    });
    if (modal === "job-detail" && entity?.type === "job") {
      setDetailJobId(entity.id);
      void loadTargets(entity.id);
    }
  }, [dispatch, drawerParam, entityParam, focus, loadTargets, modalParam, panelParam]);

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

  const applyFirmwareLink = useCallback(
    async (deviceId: string, firmwareKey: string) => {
      const device = devices.find((item) => item.id === deviceId);
      try {
        await putDeviceFirmwareLink(deviceId, firmwareKey);
        setLinkMode(null);
        setPendingReplaceLink(null);
        await reloadGraph();
        pushNotice({
          variant: "success",
          title: PP_HELP.hub.linkSuccess,
          message: device
            ? `${device.name} agora está vinculado a ${firmwareKey}.`
            : PP_HELP.hub.linkSuccessBody,
        });
      } catch (err) {
        const code = err instanceof ProductionPulseRequestError ? err.code : undefined;
        pushNotice({
          variant: "warning",
          title: "Vínculo indisponível",
          message:
            code === "firmwareLinkIncompatible"
              ? PP_HELP.hub.linkIncompatible
              : err instanceof Error
                ? err.message
                : "Falha ao criar vínculo.",
        });
      }
    },
    [devices, pushNotice, reloadGraph],
  );

  const onRequestLink = useCallback(
    (request: LinkCandidateRequest) => {
      if (!canManage) return;
      if (request.state === "incompatible") {
        pushNotice({
          variant: "warning",
          title: "Vínculo indisponível",
          message:
            linkMode?.origin === "device"
              ? PP_HELP.hub.linkIncompatibleFirmware
              : PP_HELP.hub.linkIncompatible,
          autoDismissMs: 5000,
        });
        return;
      }
      if (request.state === "already-linked") {
        pushNotice({
          variant: "info",
          message: PP_HELP.hub.linkAlreadyAssigned,
          autoDismissMs: 4000,
        });
        return;
      }
      if (request.state === "replace-link") {
        setPendingReplaceLink({
          deviceId: request.deviceId,
          firmwareKey: request.firmwareKey,
        });
        return;
      }
      if (request.state === "compatible") {
        void applyFirmwareLink(request.deviceId, request.firmwareKey);
      }
    },
    [applyFirmwareLink, canManage, linkMode?.origin, pushNotice],
  );

  const openPanel = useCallback(
    (panel: AdminHubPanel) => {
      dispatch({ type: "openPanel", panel });
      if (panel === "drivers") {
        void reloadDrivers();
      }
    },
    [dispatch, reloadDrivers],
  );

  const runFamilyJob = useCallback(
    async (
      firmwareKey: string,
      deviceIds?: string[],
      opts?: { scheduledAt?: string },
    ) => {
      const match = publishedFirmwares.find((item) => item.firmwareKey === firmwareKey);
      if (!match) {
        pushNotice({
          variant: "warning",
          title: PP_HELP.ota.noEligibleTitle,
          message: PP_HELP.ota.noPublishedFirmware,
        });
        return;
      }

      const isSingleDevice = deviceIds?.length === 1;
      const singleDeviceId = isSingleDevice ? deviceIds![0] : undefined;
      if (isSingleDevice && singleDeviceId) {
        try {
          const status = await fetchDeviceFirmwareUpdateStatus(singleDeviceId);
          if (status.active) {
            pushNotice({
              id: otaActiveNoticeId(singleDeviceId),
              variant: "warning",
              title: PP_HELP.ota.alreadyInProgressTitle,
              message: PP_HELP.ota.alreadyInProgressMessage,
              action: {
                label: PP_HELP.ota.alreadyInProgressAction,
                onClick: () => {
                  if (status.jobId) void openJobDetails(status.jobId);
                  else openPanel("jobs");
                },
              },
            });
            return;
          }
        } catch {
          /* status probe failed — proceed and let create surface the error */
        }
      }

      let filterDeviceIds = deviceIds;
      let skippedActive = 0;
      if (!isSingleDevice) {
        const family = families.find((item) => item.firmwareKey === firmwareKey);
        const candidates =
          deviceIds ??
          devices
            .filter((device) => device.assignedFirmwareKey === firmwareKey)
            .filter((device) => {
              const installed = device.installedFirmwareVersion?.trim() || null;
              return installed !== (family?.latestVersion ?? null);
            })
            .map((device) => device.id);

        if (candidates.length > 0) {
          const checks = await Promise.all(
            candidates.map(async (id) => {
              try {
                const status = await fetchDeviceFirmwareUpdateStatus(id);
                return { id, active: Boolean(status.active) };
              } catch {
                return { id, active: false };
              }
            }),
          );
          const freeIds = checks.filter((item) => !item.active).map((item) => item.id);
          skippedActive = checks.length - freeIds.length;
          if (freeIds.length === 0) {
            pushNotice({
              id: "ota-target-active:family",
              variant: "warning",
              title: PP_HELP.ota.alreadyInProgressTitle,
              message: PP_HELP.ota.alreadyInProgressMessage,
              action: {
                label: PP_HELP.ota.alreadyInProgressAction,
                onClick: () => openPanel("jobs"),
              },
            });
            return;
          }
          if (skippedActive > 0 || deviceIds) {
            filterDeviceIds = freeIds;
          }
        }
      }

      setBusy(true);
      try {
        const filter: Record<string, unknown> = {
          firmwareKey: match.firmwareKey,
          onlyOutdated: true,
        };
        if (filterDeviceIds?.length) filter.deviceIds = filterDeviceIds;
        const job = await createFirmwareUpdateJob({
          firmwareId: match.id,
          branch,
          trigger: opts?.scheduledAt ? "scheduled" : "manual",
          scheduledAt: opts?.scheduledAt,
          filter,
        });
        await reloadJobs({ soft: true });
        if (filterDeviceIds?.length) {
          pushNotice({
            id: otaJobCreatedNoticeId(job.id),
            variant: "success",
            title: PP_HELP.ota.updateStartedTitle,
            message: PP_HELP.ota.updateStartedMessage.replace(
              "{count}",
              String(filterDeviceIds.length),
            ),
          });
        } else {
          pushNotice({
            id: otaJobCreatedNoticeId(job.id),
            variant: "success",
            title: PP_HELP.ota.updateStartedTitle,
            message: PP_HELP.ota.deviceJobCreated,
          });
        }
        if (skippedActive > 0) {
          pushNotice({
            variant: "warning",
            message: PP_HELP.ota.familyPartialSkipped
              .replace("{skipped}", String(skippedActive))
              .replace("{started}", String(filterDeviceIds?.length ?? 0)),
          });
        }
        await openJobDetails(job.id);
      } catch (err) {
        const openTargetExists =
          err instanceof ProductionPulseRequestError &&
          err.code === "openTargetExists";
        const noticeId = openTargetExists
          ? singleDeviceId
            ? otaActiveNoticeId(singleDeviceId)
            : "ota-target-active:family"
          : undefined;
        const resolved = pushResolvedProductionPulseNotice(pushNotice, err, {
          id: noticeId,
          onAction: () => openPanel("jobs"),
        });
        if (resolved && !isOperationalNoticeOnly(resolved)) {
          setStructuralError(resolved.message);
        }
      } finally {
        setBusy(false);
      }
    },
    [
      branch,
      devices,
      families,
      openJobDetails,
      openPanel,
      publishedFirmwares,
      pushNotice,
      reloadJobs,
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
        pushNotice({
          variant: "warning",
          title: PP_HELP.ota.noEligibleTitle,
          message: PP_HELP.ota.noPublishedFirmware,
        });
        return;
      }
      await runFamilyJob(match.firmwareKey, [deviceId]);
    },
    [canManage, devices, publishedFirmwares, pushNotice, runFamilyJob],
  );

  const handleUpdateFamily = useCallback(
    async (firmwareKey: string) => {
      if (!canManage) return;
      await runFamilyJob(firmwareKey);
    },
    [canManage, runFamilyJob],
  );

  const openConfirm = useCallback(
    (kind: AdminHubConfirmKind, id: string) => {
      dispatch({ type: "openConfirm", kind, id });
    },
    [dispatch],
  );

  const closeConfirm = useCallback(() => {
    dispatch({ type: "closeConfirm" });
  }, [dispatch]);

  const confirmCancelJob = async () => {
    if (!ui.confirm || ui.confirm.kind !== "cancel-job" || !canManage) return;
    const jobId = ui.confirm.id;
    setConfirmBusy(true);
    try {
      await cancelFirmwareUpdateJob(jobId);
      pushNotice({ variant: "success", message: "Atualização cancelada." });
    } catch (err) {
      const resolved = resolveProductionPulseError(err, {
        fallbackMessage: "Não foi possível cancelar; a lista será atualizada.",
      });
      pushNotice({
        variant: resolved.variant,
        title: resolved.title,
        message: resolved.message,
      });
    } finally {
      setConfirmBusy(false);
      dispatch({ type: "closeConfirm" });
    }
    await reloadJobs({ soft: true });
    if (detailJobId === jobId) await loadTargets(jobId);
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
      } else if (kind === "archive-driver") {
        await archiveDriver(id);
        pushNotice({
          variant: "success",
          message: PP_HELP.drivers.archiveSuccess,
        });
        await reloadDrivers();
      } else if (kind === "unlink") {
        await handleUnlink(id);
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

  const onSelectEntity = (selection: CanvasEntitySelection) => {
    const entity: AdminEntityRef =
      selection.type === "device"
        ? { type: "device", id: selection.id }
        : { type: "firmware", id: selection.id };
    dispatch({
      type: "openSummary",
      entity,
      popoverNodeId: selection.nodeId,
    });
  };

  const onOpenDeviceMenu = (payload: { deviceId: string; nodeId: string }) => {
    dispatch({
      type: "openEntityMenu",
      entity: { type: "device", id: payload.deviceId },
      popoverNodeId: payload.nodeId,
    });
  };

  const onOpenFirmwareMenu = (payload: {
    firmwareKey: string;
    firmwareId?: string | null;
    nodeId: string;
  }) => {
    dispatch({
      type: "openEntityMenu",
      entity: {
        type: "firmware",
        id: payload.firmwareId || payload.firmwareKey,
      },
      popoverNodeId: payload.nodeId,
    });
  };

  const openModal = (modal: AdminHubModal, entity?: AdminEntityRef | null) => {
    dispatch({
      type: "openModal",
      modal,
      entity: entity === undefined ? undefined : entity,
    });
  };

  const closeLayers = () => {
    setDetailJobId(null);
    setTargets([]);
    dispatch({ type: "closeAll" });
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
          pushNotice({
            variant: "warning",
            title: PP_HELP.ota.noEligibleTitle,
            message: PP_HELP.ota.noPublishedFirmware,
          });
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
      if (action === "link") {
        dispatch({ type: "closeTransient" });
        setLinkMode({ origin: "device", deviceId: device.id });
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
        return;
      }
      if (action === "link") {
        dispatch({ type: "closeTransient" });
        setLinkMode({ origin: "firmware", firmwareKey: fw.firmwareKey });
      }
    }
  };

  const handleUnarchiveDriver = useCallback(
    (driverKey: string) => {
      void unarchiveDriver(driverKey)
        .then(() => {
          pushNotice({
            variant: "success",
            message: PP_HELP.drivers.unarchiveSuccess,
          });
          return reloadDrivers();
        })
        .catch((err) => {
          pushNotice({
            variant: "error",
            message: err instanceof Error ? err.message : "Falha ao reativar driver.",
          });
        });
    },
    [pushNotice, reloadDrivers],
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
      {
        key: "progress",
        header: "Atualização",
        render: (row) => {
          const device = devices.find((item) => item.id === row.deviceId);
          return (
            <div className="pp-ota-target-row">
              <OtaTargetProgress
                status={row.status}
                errorCode={row.errorCode}
                deviceOnline={device?.online ?? device?.status === "online"}
                progressPercent={row.progressPercent}
                bytesReceived={row.bytesReceived}
                bytesTotal={row.bytesTotal}
                updatedAt={row.updatedAt}
              />
            </div>
          );
        },
      },
    ],
    [devices],
  );

  const bottomOtaPriority = useMemo(() => {
    if (otaMonitor.failedOpenCount > 0) {
      return { status: "failed" as const, count: otaMonitor.failedOpenCount };
    }
    if (otaMonitor.applyingCount > 0) {
      return { status: "applying" as const, count: otaMonitor.applyingCount };
    }
    if (otaMonitor.downloadingCount > 0) {
      return {
        status: "downloading" as const,
        count: otaMonitor.downloadingCount,
      };
    }
    if (otaMonitor.awaitingCount > 0) {
      return { status: "authorized" as const, count: otaMonitor.awaitingCount };
    }
    return null;
  }, [
    otaMonitor.applyingCount,
    otaMonitor.awaitingCount,
    otaMonitor.downloadingCount,
    otaMonitor.failedOpenCount,
  ]);

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
              dispatch({
                type: "setFilters",
                filters: { ...ui.filters, q },
              })
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
            dispatch({
              type: "setFilters",
              filters: {
                ...ui.filters,
                status: value === "all" ? "" : value,
              },
            })
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
        kpis={hubKpis}
        loading={loading}
        activeJobs={activeJobCount}
        awaitingCount={otaMonitor.awaitingCount}
        downloadingCount={otaMonitor.downloadingCount}
        onOpenJobs={() => openPanel("jobs")}
      />
      <HubCanvasLegend linkModeActive={Boolean(linkMode)} />
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
      <PpHintAction hint={PP_HELP.hub.panelDrivers} ariaLabel="Ajuda: Painel Drivers">
        <PpActionButton variant="ghost" onClick={() => openPanel("drivers")}>
          <CircuitBoard size={14} aria-hidden="true" /> Drivers
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

  const overlayBottom = linkMode ? (
    <div className="pp-admin-bottom-bar pp-admin-bottom-bar--link-mode" role="status" aria-live="polite">
      <span className="pp-admin-bottom-bar__link-mode">
        <Link2 size={16} aria-hidden="true" />
        {linkMode.origin === "firmware" ? (
          <>
            <strong>Vinculando {linkMode.firmwareKey}</strong>
            <span className="pp-muted">{PP_HELP.hub.linkModeFirmwareHint}</span>
          </>
        ) : (
          <>
            <strong>
              Vinculando{" "}
              {devices.find((item) => item.id === linkMode.deviceId)?.name ?? "IoT"}
            </strong>
            <span className="pp-muted">{PP_HELP.hub.linkModeDeviceHint}</span>
          </>
        )}
      </span>
      <PpHintAction hint={PP_HELP.hub.cancelLinkMode} ariaLabel="Ajuda: Cancelar vínculo">
        <PpActionButton variant="ghost" onClick={() => setLinkMode(null)}>
          Esc · Cancelar
        </PpActionButton>
      </PpHintAction>
    </div>
  ) : (
    <div className="pp-admin-bottom-bar" role="status" aria-label="Resumo do mapa">
      <PpHintAction hint={PP_HELP.hub.bottomBar} ariaLabel="Ajuda: Resumo do mapa">
        <span>
          {families.length} firmware{families.length === 1 ? "" : "s"} · {devices.length} IoT
          {devices.length === 1 ? "" : "s"}
        </span>
      </PpHintAction>
      {bottomOtaPriority ? (
        <PpHintAction hint={PP_HELP.hub.kpiJobsChip} ariaLabel="Ajuda: Atividade OTA">
          <button
            type="button"
            className="pp-admin-bottom-bar__link pp-job-summary"
            onClick={() => openPanel("jobs")}
          >
            <OtaStatusIndicator
              status={bottomOtaPriority.status}
              density="compact"
              meta={
                bottomOtaPriority.count > 1
                  ? `${bottomOtaPriority.count} IoTs`
                  : undefined
              }
            />
          </button>
        </PpHintAction>
      ) : activeJobCount > 0 ? (
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
      {structuralError ? (
        <div className="pp-admin-hub__notice">
          <PpStateBox
            variant="error"
            title="Erro"
            message={structuralError}
            action={
              <PpActionButton variant="ghost" onClick={() => setStructuralError(null)}>
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
            linkMode={linkMode}
            otaByDeviceId={otaMonitor.targetsByDeviceId}
            onLinkModeChange={setLinkMode}
            onRequestLink={onRequestLink}
            onLinked={() => void reloadGraph()}
            onUnlink={handleUnlink}
            onUpdateDevice={handleUpdateDevice}
            onUpdateFamily={handleUpdateFamily}
            onSelectEntity={onSelectEntity}
            onOpenDeviceMenu={onOpenDeviceMenu}
            onOpenFirmwareMenu={onOpenFirmwareMenu}
            onNodeDragStart={() => {
              if (ui.openLayer === "summary" || ui.openLayer === "menu") {
                dispatch({ type: "closeTransient" });
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
          onClose={() => dispatch({ type: "closeTransient" })}
          onEdit={() => {
            if (ui.selectedEntity?.type === "device") {
              openModal("device-edit", ui.selectedEntity);
            } else if (ui.selectedEntity?.type === "firmware") {
              openModal("firmware-detail", ui.selectedEntity);
            }
          }}
        />
      </div>

      <EntitySummaryPopover
        open={ui.openLayer === "summary"}
        anchorEl={anchorEl}
        entity={ui.selectedEntity}
        device={selectedDevice}
        otaTarget={
          selectedDevice
            ? otaMonitor.getTargetForDevice(selectedDevice.id)
            : undefined
        }
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
        onClose={() => dispatch({ type: "closeTransient" })}
        onInspect={() => {
          if (ui.selectedEntity?.type === "device") {
            openModal("device-detail", ui.selectedEntity);
            return;
          }
          if (ui.selectedEntity?.type === "firmware") {
            openModal("firmware-detail", ui.selectedEntity);
            return;
          }
          // Fallback raro: entity sem detalhe modal — inspector layer.
          dispatch({ type: "openInspector" });
        }}
        onOpenMenu={() => {
          if (!ui.selectedEntity || !ui.popoverAnchorId) return;
          dispatch({
            type: "openEntityMenu",
            entity: ui.selectedEntity,
            popoverNodeId: ui.popoverAnchorId,
          });
        }}
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
        onClose={() => {
          // Não sobrescrever confirm/modal abertos pela ação do menu (ex.: Desvincular).
          if (uiRef.current.openLayer !== "menu") return;
          dispatch({ type: "closeEntityMenu" });
        }}
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
          onOpenDriverCreate={() => openModal("driver-create", null)}
          onCancel={closeLayers}
          onDone={() => {
            closeLayers();
            void reloadGraph();
            openPanel("firmwares");
            pushNotice({ variant: "success", message: "Firmware criado." });
          }}
        />
      </PpWorkbenchDialog>

      <PpWorkbenchDialog
        open={ui.openLayer === "modal" && ui.modal === "driver-create"}
        title={PP_HELP.drivers.breadcrumbCreate}
        onClose={closeLayers}
      >
        <DriverFormPage
          mode="create"
          permissions={permissions}
          embedded
          onCancel={closeLayers}
          onDone={() => {
            closeLayers();
            void reloadDrivers();
            openPanel("drivers");
            pushNotice({
              variant: "success",
              message: PP_HELP.drivers.createSuccess,
            });
          }}
        />
      </PpWorkbenchDialog>

      <PpDetailDialog
        open={ui.openLayer === "modal" && ui.modal === "driver-detail"}
        title={PP_HELP.drivers.breadcrumbDetail}
        onClose={closeLayers}
      >
        {ui.selectedEntity?.type === "driver" ? (
          <DriverDetailPage
            driverKey={ui.selectedEntity.id}
            permissions={permissions}
            embedded
            onCancel={closeLayers}
            onDone={() => {
              void reloadDrivers();
            }}
            onRequestArchive={(key) => openConfirm("archive-driver", key)}
          />
        ) : null}
      </PpDetailDialog>

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
            hubOtaTarget={otaMonitor.getTargetForDevice(ui.selectedEntity.id)}
            suppressLocalOtaPoll
            onOperationalNotice={(notice) => {
              pushNotice({
                message: notice.message,
                variant: notice.variant ?? "info",
                title: notice.title,
                id: notice.id,
              });
              if (notice.id?.startsWith("ota-job-created:")) {
                void reloadJobs({ soft: true });
              }
            }}
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
        open={ui.openLayer === "panel" && ui.panel === "firmwares"}
        title={PP_HELP.hub.firmwaresDialogTitle}
        onClose={() => dispatch({ type: "closePanel" })}
      >
        <PpCatalogSearchBar
          value={catalogSearch}
          onChange={setCatalogSearch}
          placeholder={PP_HELP.hub.firmwaresCatalogSearch}
        />
        <p className="pp-muted">{PP_HELP.hub.firmwaresCatalogList}</p>
        {canManage ? (
          <PpActionButton
            className="pp-mb-sm"
            onClick={() => openModal("firmware-create", null)}
          >
            Novo firmware
          </PpActionButton>
        ) : null}
        {filteredFirmwares.length === 0 ? (
          <PpStateBox variant="empty" title={PP_HELP.ota.catalogEmpty} />
        ) : (
          <div className="pp-firmware-catalog-list" role="list">
            {filteredFirmwares.map((firmware) => (
              <div key={firmware.id} role="listitem">
                <FirmwareCatalogListItem
                  firmware={firmware}
                  canManage={canManage}
                  busy={busy}
                  onOpenDetails={() =>
                    openModal("firmware-detail", { type: "firmware", id: firmware.id })
                  }
                  onUpdateLinked={() => void handleUpdateFamily(firmware.firmwareKey)}
                />
              </div>
            ))}
          </div>
        )}
      </PpDetailDialog>

      <PpDetailDialog
        open={ui.openLayer === "panel" && ui.panel === "drivers"}
        title={PP_HELP.hub.driversDialogTitle}
        onClose={() => dispatch({ type: "closePanel" })}
      >
        <PpCatalogSearchBar
          value={driversSearch}
          onChange={setDriversSearch}
          placeholder={PP_HELP.hub.driversCatalogSearch}
        />
        <p className="pp-muted">{PP_HELP.hub.driversCatalogList}</p>
        {canManage ? (
          <PpActionButton
            className="pp-mb-sm"
            onClick={() => openModal("driver-create", null)}
          >
            Novo tipo de driver
          </PpActionButton>
        ) : null}
        {driversLoading && drivers.length === 0 ? (
          <PpStateBox variant="loading" title="Carregando drivers…" />
        ) : filteredDrivers.length === 0 ? (
          <PpStateBox variant="empty" title={PP_HELP.hub.driversCatalogEmpty} />
        ) : (
          <div className="pp-driver-type-list" role="list">
            {filteredDrivers.map((driver) => (
              <div key={driver.key} role="listitem">
                <DriverTypeListItem
                  driver={driver}
                  canManage={canManage}
                  busy={busy}
                  onOpenDetails={() =>
                    openModal("driver-detail", { type: "driver", id: driver.key })
                  }
                  onArchive={() => openConfirm("archive-driver", driver.key)}
                  onUnarchive={() => handleUnarchiveDriver(driver.key)}
                />
              </div>
            ))}
          </div>
        )}
      </PpDetailDialog>

      <PpDetailDialog
        open={ui.openLayer === "panel" && ui.panel === "devices"}
        title={PP_HELP.hub.devicesDialogTitle}
        onClose={() => dispatch({ type: "closePanel" })}
      >
        <p className="pp-muted">{PP_HELP.hub.devicesCatalogList}</p>
        <DeviceCatalogPanel
          search={`?branch=${encodeURIComponent(branch)}`}
          permissions={permissions}
        />
      </PpDetailDialog>

      <PpDetailDialog
        open={ui.openLayer === "panel" && ui.panel === "jobs"}
        title={PP_HELP.hub.jobsDialogTitle}
        onClose={() => dispatch({ type: "closePanel" })}
      >
        <p className="pp-muted">{PP_HELP.ota.jobsList}</p>
        {jobsLoading && jobs.length === 0 ? (
          <PpStateBox variant="loading" title="Carregando atualizações" />
        ) : jobs.length === 0 ? (
          <PpStateBox variant="empty" title={PP_HELP.ota.jobsEmpty} />
        ) : (
          <div className="pp-ota-job-list" role="list">
            {jobs.map((job) => {
              const item = firmwareById.get(job.firmwareId);
              const label = item
                ? `${item.firmwareKey} · ${item.version}`
                : PP_HELP.hub.jobsUnknownFirmware;
              const jobTargets = otaMonitor.targetsByJobId.get(job.id) ?? [];
              return (
                <div key={job.id} role="listitem">
                  <OtaJobListItem
                    job={job}
                    firmwareLabel={label}
                    targets={jobTargets}
                    canManage={canManage}
                    onOpenDetails={() => void openJobDetails(job.id)}
                    onCancel={() => openConfirm("cancel-job", job.id)}
                  />
                </div>
              );
            })}
          </div>
        )}
      </PpDetailDialog>

      <PpDetailDialog
        open={ui.openLayer === "modal" && ui.modal === "job-detail"}
        title={PP_HELP.hub.targetsDialogTitle}
        onClose={() => {
          setDetailJobId(null);
          setTargets([]);
          dispatch({ type: "closeModal" });
        }}
      >
        <p className="pp-muted">{PP_HELP.ota.targetsList}</p>
        {targets.length === 0 ? (
          <PpStateBox variant="empty" title="Sem targets" />
        ) : (
          <>
            {(() => {
              const summary = summarizeOtaJobTargets(targets);
              return (
                <div className="pp-job-summary" aria-label="Resumo da atualização OTA">
                  <OtaStatusIndicator
                    status={summary.phaseStatus}
                    density="comfortable"
                    meta={`${summary.terminal} de ${summary.total} dispositivos processados`}
                  />
                  <PpOtaProgressBar
                    value={summary.processedPercent}
                    summary={`${summary.terminal} de ${summary.total} processados`}
                    ariaLabel="Progresso agregado do job (targets terminais)"
                  />
                  <ul className="pp-job-summary__counts">
                    <li>{summary.updated} concluídos</li>
                    <li>{summary.downloading} baixando</li>
                    <li>{summary.awaiting} aguardando</li>
                    <li>{summary.failed} falhas</li>
                  </ul>
                </div>
              );
            })()}
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
        open={ui.openLayer === "confirm" && ui.confirm?.kind === "archive-driver"}
        title={PP_HELP.hub.softDeleteDriverConfirmTitle}
        message={PP_HELP.hub.softDeleteDriverConfirmBody}
        confirmLabel={PP_HELP.hub.softDeleteDriverConfirmLabel}
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

      <PpConfirmDialog
        open={Boolean(pendingReplaceLink)}
        title={PP_HELP.hub.linkReplaceTitle}
        message={PP_HELP.hub.linkReplaceBody}
        confirmLabel={PP_HELP.hub.linkReplaceConfirm}
        cancelLabel="Voltar"
        variant="danger"
        confirmBusy={confirmBusy}
        onConfirm={() => {
          if (!pendingReplaceLink) return;
          setConfirmBusy(true);
          void applyFirmwareLink(pendingReplaceLink.deviceId, pendingReplaceLink.firmwareKey).finally(
            () => setConfirmBusy(false),
          );
        }}
        onCancel={() => setPendingReplaceLink(null)}
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
