import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
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
import {
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
import { resolveProductionPulseError } from "../utils/apiErrors";
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
  }, [branch, dispatch]);

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
    },
    [dispatch],
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
      if (isSingleDevice) {
        const deviceId = deviceIds![0];
        try {
          const status = await fetchDeviceFirmwareUpdateStatus(deviceId);
          if (status.active) {
            pushNotice({
              id: `ota-active-${deviceId}`,
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
            variant: "success",
            title: PP_HELP.ota.updateStartedTitle,
            message: PP_HELP.ota.updateStartedMessage.replace(
              "{count}",
              String(filterDeviceIds.length),
            ),
          });
        } else {
          pushNotice({
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
        const resolved = resolveProductionPulseError(err);
        pushNotice({
          variant: resolved.variant,
          title: resolved.title,
          message: resolved.message,
          action: resolved.actionLabel
            ? {
                label: resolved.actionLabel,
                onClick: () => openPanel("jobs"),
              }
            : undefined,
        });
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
        kpis={kpis}
        loading={loading}
        activeJobs={activeJobCount}
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
            linkMode={linkMode}
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

        <AdminSidePanel
          open={ui.openLayer === "panel" && ui.panel === "firmwares"}
          title="Firmwares"
          onClose={() => dispatch({ type: "closePanel" })}
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
          onClose={() => dispatch({ type: "closePanel" })}
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
          size="wide"
          onClose={() => dispatch({ type: "closePanel" })}
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
