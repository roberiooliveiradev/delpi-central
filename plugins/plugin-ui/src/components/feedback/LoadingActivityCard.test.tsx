import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  LoadingActivityCard,
  loadingActivityBemClasses,
  type LoadingActivityCardLabels,
} from "./LoadingActivityCard";

const LABELS: LoadingActivityCardLabels = {
  progressRemaining: (p) => `${p}% left`,
  progressAriaDeterminate: (p) => `Loading: ${p}% remaining`,
  progressAriaIndeterminate: "Loading",
};

afterEach(() => {
  cleanup();
});

describe("LoadingActivityCard", () => {
  it("renderiza título e descrição", () => {
    render(
      <LoadingActivityCard
        title="Fetching data"
        description="Please wait"
        classNames={loadingActivityBemClasses("dp")}
        labels={LABELS}
      />,
    );
    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.getByText("Fetching data")).toBeTruthy();
    expect(screen.getByText("Please wait")).toBeTruthy();
  });

  it("exibe progresso determinado", () => {
    render(
      <LoadingActivityCard
        title="Loading"
        progressPercent={70}
        classNames={loadingActivityBemClasses("ds")}
        labels={LABELS}
      />,
    );
    expect(screen.getByText("30% left")).toBeTruthy();
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("70");
  });

  it("suporta rótulo Iniciando quando progresso = 0", () => {
    render(
      <LoadingActivityCard
        title="Loading"
        progressPercent={0}
        classNames={loadingActivityBemClasses("si", { block: "loading-activity-inline" })}
        labels={{
          progressRemaining: (p) => `Faltam ${p}%`,
          progressStarting: "Iniciando…",
          progressRemainingOnlyAfterStart: true,
          progressAriaDeterminate: (p) => `Carregamento: ${p}%`,
          progressAriaStarting: "Carregamento: Iniciando…",
          progressAriaIndeterminate: "Carregamento em andamento",
        }}
      />,
    );

    expect(screen.getByText("Iniciando…")).toBeTruthy();
  });
});
