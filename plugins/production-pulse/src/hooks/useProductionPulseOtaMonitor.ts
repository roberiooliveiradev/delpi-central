import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  fetchFirmwareUpdateTargets,
  type FirmwareUpdateJob,
  type FirmwareUpdateTarget,
} from "../api/productionPulseApi";
import { PP_HELP } from "../content/helpTooltips";
import { isOtaStatusActive, isOtaStatusTerminal } from "../utils/otaStatusLabels";
import {
  otaJobCreatedNoticeId,
  otaTargetFailedNoticeId,
  otaTargetUpdatedNoticeId,
  pushOtaTargetFailureNotice,
} from "../utils/pushResolvedNotice";

type NoticePush = (
  notice:
    | {
        id?: string;
        variant?: "error" | "warning" | "info" | "success";
        title?: string;
        message: string;
        action?: { label: string; onClick: () => void };
      }
    | string,
) => string;

type UseProductionPulseOtaMonitorArgs = {
  jobs: FirmwareUpdateJob[];
  /** Soft-reload jobs list after terminal transitions. */
  reloadJobs?: () => void | Promise<void>;
  /** Soft-reload canvas graph after terminal OTA transitions. */
  reloadGraph?: () => void | Promise<void>;
  pushNotice: NoticePush;
  deviceNameById?: Map<string, string>;
  pollMs?: number;
  enabled?: boolean;
  /** When WebSocket is healthy, skip interval poll (hint-driven refresh instead). */
  realtimeConnected?: boolean;
  /** Imperative refresh for WS ota.target hints. */
  refreshSignal?: number;
};

export type ProductionPulseOtaMonitor = {
  targetsByDeviceId: Map<string, FirmwareUpdateTarget>;
  targetsByJobId: Map<string, FirmwareUpdateTarget[]>;
  activeTargetCount: number;
  awaitingCount: number;
  downloadingCount: number;
  applyingCount: number;
  failedOpenCount: number;
  getTargetForDevice: (deviceId: string) => FirmwareUpdateTarget | undefined;
};

const DEFAULT_POLL_MS = 3000;

function jobIsActive(job: FirmwareUpdateJob): boolean {
  const s = (job.status || "").toLowerCase();
  return s === "running" || s === "scheduled";
}

/**
 * Hub OTA monitor: poll targets for active jobs only, index by device, notify on transitions.
 * Does not invent lifecycle — API remains authority.
 */
export function useProductionPulseOtaMonitor(
  args: UseProductionPulseOtaMonitorArgs,
): ProductionPulseOtaMonitor {
  const {
    jobs,
    reloadJobs,
    reloadGraph,
    pushNotice,
    deviceNameById,
    pollMs = DEFAULT_POLL_MS,
    enabled = true,
    realtimeConnected = false,
    refreshSignal = 0,
  } = args;

  const [targets, setTargets] = useState<FirmwareUpdateTarget[]>([]);
  const prevStatusRef = useRef<Map<string, string>>(new Map());
  const seenJobCreatedRef = useRef<Set<string>>(new Set());

  const activeJobs = useMemo(() => jobs.filter(jobIsActive), [jobs]);
  const activeJobIds = useMemo(
    () => activeJobs.map((j) => j.id).sort().join(","),
    [activeJobs],
  );

  const refreshTargets = useCallback(async () => {
    if (!enabled || activeJobs.length === 0) {
      setTargets([]);
      return;
    }
    const batches = await Promise.all(
      activeJobs.map(async (job) => {
        try {
          return await fetchFirmwareUpdateTargets(job.id);
        } catch {
          return [] as FirmwareUpdateTarget[];
        }
      }),
    );
    setTargets(batches.flat());
  }, [activeJobs, enabled]);

  useEffect(() => {
    void refreshTargets();
  }, [refreshTargets, activeJobIds, refreshSignal]);

  useEffect(() => {
    if (!enabled || activeJobs.length === 0) return;
    // D-11: poll curto só com WS down (ou sem realtime).
    if (realtimeConnected) return;
    const id = window.setInterval(() => {
      void refreshTargets();
    }, pollMs);
    return () => window.clearInterval(id);
  }, [activeJobs.length, enabled, pollMs, realtimeConnected, refreshTargets]);

  // Transition notices
  useEffect(() => {
    const prev = prevStatusRef.current;
    const next = new Map<string, string>();
    let shouldReloadJobs = false;

    for (const target of targets) {
      const status = (target.status || "").toLowerCase();
      next.set(target.id, status);
      const prior = prev.get(target.id);

      if (!prior && target.jobId && !seenJobCreatedRef.current.has(target.jobId)) {
        // First sight of targets for a job — optional; create notice is owned by runFirmwareJob.
        seenJobCreatedRef.current.add(target.jobId);
      }

      if (prior && prior !== status) {
        if (status === "updated") {
          const name = deviceNameById?.get(target.deviceId) || "IoT";
          pushNotice({
            id: otaTargetUpdatedNoticeId(target.id),
            variant: "success",
            title: PP_HELP.ota.updateCompletedTitle,
            message: PP_HELP.ota.updateCompletedMessage
              .replace("{name}", name)
              .replace("{version}", target.toVersion || "—"),
          });
          shouldReloadJobs = true;
        } else if (status === "failed") {
          pushOtaTargetFailureNotice(pushNotice, {
            targetId: target.id,
            errorCode: target.errorCode,
            deviceName: deviceNameById?.get(target.deviceId),
          });
          shouldReloadJobs = true;
        }
      }

      // First observation already failed/stale (e.g. after refresh) — notify once
      if (!prior && status === "failed" && target.errorCode === "ota_target_stale") {
        pushOtaTargetFailureNotice(pushNotice, {
          targetId: target.id,
          errorCode: target.errorCode,
          deviceName: deviceNameById?.get(target.deviceId),
        });
      }
    }

    prevStatusRef.current = next;
    if (shouldReloadJobs) {
      if (reloadJobs) void reloadJobs();
      if (reloadGraph) void reloadGraph();
    }
  }, [targets, pushNotice, deviceNameById, reloadJobs, reloadGraph]);

  // Clear seen jobs that disappeared
  useEffect(() => {
    const live = new Set(jobs.map((j) => j.id));
    for (const id of [...seenJobCreatedRef.current]) {
      if (!live.has(id)) seenJobCreatedRef.current.delete(id);
    }
  }, [jobs]);

  return useMemo(() => {
    const targetsByDeviceId = new Map<string, FirmwareUpdateTarget>();
    const targetsByJobId = new Map<string, FirmwareUpdateTarget[]>();
    let awaitingCount = 0;
    let downloadingCount = 0;
    let applyingCount = 0;
    let failedOpenCount = 0;
    let activeTargetCount = 0;

    for (const target of targets) {
      const status = (target.status || "").toLowerCase();
      if (isOtaStatusActive(status) || status === "failed" || status === "updated") {
        // Prefer active over terminal when indexing by device
        const existing = targetsByDeviceId.get(target.deviceId);
        if (
          !existing ||
          isOtaStatusActive(status) ||
          (!isOtaStatusActive(existing.status) && isOtaStatusTerminal(existing.status))
        ) {
          targetsByDeviceId.set(target.deviceId, target);
        }
      }
      const list = targetsByJobId.get(target.jobId) || [];
      list.push(target);
      targetsByJobId.set(target.jobId, list);

      if (isOtaStatusActive(status)) {
        activeTargetCount += 1;
        if (status === "pending" || status === "authorized") awaitingCount += 1;
        if (status === "downloading") downloadingCount += 1;
        if (status === "applying") applyingCount += 1;
      }
      if (status === "failed") failedOpenCount += 1;
    }

    return {
      targetsByDeviceId,
      targetsByJobId,
      activeTargetCount,
      awaitingCount,
      downloadingCount,
      applyingCount,
      failedOpenCount,
      getTargetForDevice: (deviceId: string) => targetsByDeviceId.get(deviceId),
    };
  }, [targets]);
}

/** Suppress unused import warning if tree-shaken oddly */
void otaJobCreatedNoticeId;
void otaTargetFailedNoticeId;
