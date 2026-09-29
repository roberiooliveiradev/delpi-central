import { describe, expect, it } from "vitest";
import type { MonitoringItem } from "../types/mes";
import { elapsedSeconds, formatDuration, serverOffsetMs } from "./duration";
import { filterMonitoringItems } from "./monitoringFilters";
import { isPendingReason, presentMonitoringState, progressPercent } from "./monitoringPresentation";

const item = (changes: Partial<MonitoringItem> = {}): MonitoringItem => ({ branch: "01", workCenter: "CT-35", runId: "run", runStatus: "running", operationalState: "producing", stateStartedAt: "2026-01-01T10:00:00Z", stateSource: "operator", integrityStatus: "complete", productionOrder: "123", operationCode: "20", operatorCode: "1", operatorName: "Ana", piecesTotal: 50, targetPieces: 100, lastCountActivityAt: null, downtime: null, ...changes });

describe("monitoring presentation", () => {
  it("uses server clock offset and never returns negative duration", () => { expect(serverOffsetMs("2026-01-01T10:00:10Z", Date.parse("2026-01-01T10:00:00Z"))).toBe(10000); expect(elapsedSeconds("2026-01-01T11:00:00Z", Date.parse("2026-01-01T10:00:00Z"))).toBe(0); expect(formatDuration(3661)).toBe("01:01:01"); });
  it("presents producing, stopped, paused and incomplete without invention", () => { expect(presentMonitoringState(item()).label).toBe("Produzindo"); expect(presentMonitoringState(item({ operationalState: "stopped" })).label).toBe("Parada"); expect(presentMonitoringState(item({ runStatus: "paused", operationalState: "stopped" })).label).toBe("Pausa manual"); expect(presentMonitoringState(item({ integrityStatus: "incomplete", operationalState: null })).label).toBe("Dados incompletos"); });
  it("protects progress and pending reasons", () => { expect(progressPercent(item())).toBe(50); expect(progressPercent(item({ targetPieces: 0 }))).toBeNull(); expect(progressPercent(item({ targetPieces: null }))).toBeNull(); expect(isPendingReason(item({ operationalState: "stopped", downtime: { id: "d", startedAt: null, source: "system", reasonCode: null, reasonLabel: null, category: null, confirmed: false, note: null } }))).toBe(true); });
  it("filters search, status and reason locally", () => { const rows = [item(), item({ runId: "2", workCenter: "CT-41", operationalState: "stopped", operatorName: "Beto", downtime: { id: "d", startedAt: null, source: "system", reasonCode: "material", reasonLabel: "Falta de material", category: "material", confirmed: true, note: null } })]; expect(filterMonitoringItems(rows, { search: "41", status: "all", reason: "", sort: "attention" }, Date.now())).toHaveLength(1); expect(filterMonitoringItems(rows, { search: "", status: "stopped", reason: "Falta de material", sort: "attention" }, Date.now())).toHaveLength(1); });
});
