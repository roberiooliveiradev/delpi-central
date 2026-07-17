import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DataPrepareQualityPanel } from "./DataPrepareQualityPanel";

afterEach(cleanup);

describe("DataPrepareQualityPanel", () => {
  it("mantém profiling opt-in e apresenta métricas sem depender de hover", () => {
    const onToggle = vi.fn();
    render(
      <DataPrepareQualityPanel
        profilingEnabled
        profilingRequested={false}
        loading={false}
        onToggleProfiling={onToggle}
        preview={{
          columns: [],
          rows: [],
          returnedRows: 0,
          availableRows: 0,
          truncated: false,
          isSample: false,
          selectedStepName: "Final",
          diagnostics: [],
          executionMs: 12,
          profilingStatus: "completed",
          columnProfile: {
            sampled: true,
            sampleRows: 2,
            availableRows: 10,
            columns: [
              {
                key: "valor",
                quality: { valid: 1, empty: 1, error: 0 },
                distribution: { distinct: 1, repeated: 0, distinctRatio: 1 },
                min: 2,
                max: 2,
                minMaxAvailable: true,
              },
            ],
          },
          explainPlan: {
            version: 1,
            output: "Final",
            warnings: [],
            steps: [
              {
                index: 0,
                name: "Final",
                input: "Fonte",
                operation: "Table.Sort",
                cost: "potentially_expensive",
                cancelable: true,
              },
            ],
          },
          stepMetrics: [
            {
              stepName: "Final",
              operation: "Table.Sort",
              durationMs: 12,
              inputRows: 2,
              outputRows: 2,
              inputColumns: 1,
              outputColumns: 1,
              runtimeErrors: 0,
            },
          ],
        }}
      />,
    );
    const toggle = screen.getByRole("button", { name: "Analisar perfil" });
    expect(toggle.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(toggle);
    expect(onToggle).toHaveBeenCalledWith(true);
    expect(screen.getByText(/Válidos 1 · Vazios 1 · Erros 0/)).toBeTruthy();
    expect(screen.getByText("Plano de execução (1 etapas)")).toBeTruthy();
  });

  it("mantém controle desabilitado quando rollout não liberou profiling", () => {
    render(
      <DataPrepareQualityPanel
        preview={null}
        profilingEnabled={false}
        profilingRequested={false}
        loading={false}
        onToggleProfiling={vi.fn()}
      />,
    );
    expect(
      (screen.getByRole("button", { name: "Analisar perfil" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(screen.getByText(/indisponível pelas capabilities/)).toBeTruthy();
  });
});
