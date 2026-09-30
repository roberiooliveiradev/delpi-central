import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { MesPerformance, MonitoringItem } from "../../types/mes";
import { PerformanceStrip, RunPerformancePanel } from "./Performance";
import { WorkCenterCard } from "./WorkCenterCard";

afterEach(() => cleanup());

const perf = (changes: Partial<MesPerformance> = {}): MesPerformance => ({
  idealCycleSeconds: 1.8, producedPieces: 1000, producingSeconds: 2100,
  performancePercent: 85.71, actualAverageCycleSeconds: 2.1,
  actualThroughputPerHour: 1714.285714, expectedThroughputPerHour: 2000,
  dataQuality: "complete", standardTimeSource: "shy_tempad",
  standardTimeDataQuality: "complete", ...changes,
});
const item = (changes: Partial<MonitoringItem> = {}): MonitoringItem => ({
  branch: "01", workCenter: "CT-35", runId: "run-1", runStatus: "running",
  operationalState: "producing", stateStartedAt: "2026-01-01T10:00:00Z",
  stateSource: "operator", integrityStatus: "complete", productionOrder: "123",
  operationCode: "20", operatorCode: "1", operatorName: "Ana", piecesTotal: 1000,
  targetPieces: 2500, lastCountActivityAt: null, downtime: null, ...changes,
});

describe("PerformanceStrip (monitoring card)", () => {
  it("shows the backend percent, cycles and throughput without computing", () => {
    render(<PerformanceStrip performance={perf()} />);
    expect(screen.getByText("Performance")).toBeTruthy();
    expect(screen.getByText("85,7%")).toBeTruthy();
    expect(screen.getByText("Abaixo do ritmo padrão")).toBeTruthy();
    expect(screen.getByText(/1,80 s padrão/)).toBeTruthy();
    expect(screen.getByText(/2,10 s real/)).toBeTruthy();
    expect(screen.getByText(/1\.714 pç\/h/)).toBeTruthy();
    expect(screen.getByText(/2\.000 pç\/h/)).toBeTruthy();
  });
  it("renders values above 100% without clamping", () => {
    render(<PerformanceStrip performance={perf({ performancePercent: 111.11 })} />);
    expect(screen.getByText("111,1%")).toBeTruthy();
    expect(screen.getByText("Acima do ritmo padrão")).toBeTruthy();
  });
  it("renders null percent as waiting, never 0%", () => {
    render(<PerformanceStrip performance={perf({ performancePercent: null, dataQuality: "insufficient_count_data" })} />);
    expect(screen.getByText("—")).toBeTruthy();
    expect(screen.getByText("Aguardando produção")).toBeTruthy();
    expect(screen.queryByText("0,0%")).toBeNull();
  });
  it("explains missing standard time without technical codes", () => {
    render(<PerformanceStrip performance={perf({ performancePercent: null, dataQuality: "standard_time_unavailable" })} />);
    expect(screen.getByText("Indisponível")).toBeTruthy();
    expect(document.body.textContent).not.toContain("standard_time_unavailable");
  });
  it("renders nothing when the run carries no performance block", () => {
    const { container } = render(<PerformanceStrip performance={null} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("WorkCenterCard performance tile", () => {
  it("shows real Performance instead of order progress", () => {
    render(<WorkCenterCard item={item({ performance: perf() })} nowMs={0} onOpen={vi.fn()} />);
    // tile + faixa de Performance exibem o valor do backend; a barra de
    // progresso da OP (40%) nao se confunde com Performance
    expect(screen.getAllByText("85,7%").length).toBeGreaterThanOrEqual(1);
    // progresso da OP (40%) segue na barra de producao, nao no tile de Performance
    expect(screen.getByText(/1\.714 pç\/h/)).toBeTruthy();
  });
});

describe("RunPerformancePanel (detail)", () => {
  it("shows the full run metrics with friendly labels", () => {
    render(<RunPerformancePanel performance={perf({ idealProductionSeconds: 1800 })} idealProductionSeconds={1800} />);
    expect(screen.getByText("Performance do run atual")).toBeTruthy();
    expect(screen.getByText("85,7%")).toBeTruthy();
    expect(screen.getByText("Ciclo padrão")).toBeTruthy();
    expect(screen.getByText("Ciclo médio real")).toBeTruthy();
    expect(screen.getByText("Ritmo real")).toBeTruthy();
    expect(screen.getByText("Ritmo esperado")).toBeTruthy();
    expect(screen.getByText("Tempo produzindo")).toBeTruthy();
    expect(screen.getByText("Tempo ideal previsto")).toBeTruthy();
    expect(screen.getByText("Peças produzidas")).toBeTruthy();
    expect(screen.getByText("Origem do tempo padrão")).toBeTruthy();
    expect(screen.getByText("Padrão da ordem de produção")).toBeTruthy();
  });
  it("keeps the panel alive and explains quality when percent is null", () => {
    render(<RunPerformancePanel performance={perf({ performancePercent: null, dataQuality: "invalid_standard_time_snapshot" })} />);
    expect(screen.getByText(/Performance indisponível/)).toBeTruthy();
    expect(screen.getByText(/tempo padrão registrado.*inválido/i)).toBeTruthy();
  });
  it("shows a localized error with retry without hiding other sections", () => {
    const onRetry = vi.fn();
    render(<RunPerformancePanel performance={perf()} error="boom" onRetry={onRetry} />);
    screen.getByRole("button", { name: "Tentar novamente" }).click();
    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(screen.getByText("85,7%")).toBeTruthy();
  });
  it("shows only the error state when performance data is absent", () => {
    render(<RunPerformancePanel performance={null} error="boom" />);
    expect(screen.getByText(/Não foi possível carregar os dados de Performance/)).toBeTruthy();
  });
});
