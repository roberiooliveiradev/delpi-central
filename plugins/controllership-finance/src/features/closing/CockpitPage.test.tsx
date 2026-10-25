import {
  cleanup,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const cockpitMock = vi.fn();

vi.mock("../../api/packagesApi", () => ({
  getClosingCockpit: (...args: unknown[]) => cockpitMock(...args),
}));

import { CockpitPage } from "./CockpitPage";

function cockpit(overrides: Record<string, unknown> = {}) {
  return {
    period: "2026-10",
    checklist: { EXPECTED: 8, ACCEPTED: 4, NOT_APPLICABLE: 1 },
    p3: {
      cutoff_confirmed: true,
      domains: [
        {
          domain: "AP",
          source_state: "AVAILABLE",
          provenance_kind: "OFFICIAL",
          divergence: "0.00",
        },
        {
          domain: "AR",
          source_state: "UNAVAILABLE",
          provenance_kind: null,
          divergence: null,
        },
      ],
    },
    p4_pendencies: { OPEN: 2, RESOLVED: 5 },
    closing: {
      period: "2026-10",
      state: "PENDING",
      blocking_reasons: ["Package FISCAL not submitted"],
      packages: [
        {
          package_id: "p1",
          recipient_area: "CONTABIL",
          state: "PACKAGE_SUBMITTED_FOR_REVIEW",
          review_state: "REVIEW_IN_PROGRESS",
          current_version: null,
          required_areas: [],
          area_decisions: {},
          open_clarifications: 0,
          assignments: [],
          revision: 1,
        },
      ],
      terminal_rejection: null,
    },
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("CockpitPage", () => {
  it("renderiza estados reais de P2/P3/P4/P5 sem falso sucesso", async () => {
    cockpitMock.mockResolvedValue(cockpit());
    render(<CockpitPage />);
    await waitFor(() =>
      expect(screen.getByText("Fechamento pendente")).toBeTruthy(),
    );
    expect(
      screen.getByText("Package FISCAL not submitted"),
    ).toBeTruthy();
    expect(screen.getByText("Aceitos: 4")).toBeTruthy();
    expect(screen.getByText("UNAVAILABLE")).toBeTruthy();
    expect(screen.getByText("oficial")).toBeTruthy();
    expect(screen.getByText("2 pendência(s) em aberto")).toBeTruthy();
    expect(
      screen.getByText("Enviado para análise"),
    ).toBeTruthy();
  });

  it("marca conciliação declarada como não-oficial", async () => {
    const data = cockpit();
    data.p3.domains = [
      {
        domain: "AR",
        source_state: "AVAILABLE",
        provenance_kind: "DECLARED",
        divergence: "0.00",
      },
    ];
    cockpitMock.mockResolvedValue(data);
    render(<CockpitPage />);
    await waitFor(() =>
      expect(screen.getByText("declarado")).toBeTruthy(),
    );
  });
});
