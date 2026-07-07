import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { KpiCard, kpiCardBemClasses } from "./KpiCard";

const LABELS = {
  goalPrefix: "Goal",
  iddScorePrefix: "IDD",
  badgesStatus: "Goal performance",
};

afterEach(() => {
  cleanup();
});

describe("KpiCard", () => {
  it("renderiza título, valor e ícone", () => {
    render(
      <KpiCard
        title="OEE"
        value="82%"
        icon={<span data-testid="icon" />}
        classNames={kpiCardBemClasses("dp")}
        labels={LABELS}
      />,
    );
    expect(screen.getByText("OEE")).toBeTruthy();
    expect(screen.getByText("82%")).toBeTruthy();
    expect(screen.getByTestId("icon")).toBeTruthy();
  });

  it("exibe meta e badges quando informados", () => {
    render(
      <KpiCard
        title="OTD"
        value="95%"
        goalLabel="90%"
        goalScopeBadge={{ label: "Consolidated" }}
        goalPerformanceBadge={{
          tone: "success",
          statusLabel: "On track",
          directionLabel: "Higher is better",
        }}
        icon={<span />}
        classNames={kpiCardBemClasses("ds")}
        labels={LABELS}
      />,
    );
    expect(screen.getByText("Goal")).toBeTruthy();
    expect(screen.getByText("90%")).toBeTruthy();
    expect(screen.getByText("Consolidated")).toBeTruthy();
    expect(screen.getByText("On track")).toBeTruthy();
  });

  it("mostra placeholder quando loading", () => {
    render(
      <KpiCard
        title="OEE"
        value="82%"
        loading={true}
        icon={<span />}
        classNames={kpiCardBemClasses("dc")}
        labels={LABELS}
      />,
    );
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("…");
  });
});
