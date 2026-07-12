import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NativeSlideView } from "./NativeScreens";
import { usePresentationEngine } from "./usePresentationEngine";
import { resolveSlideTransitionStyle } from "./presentationTransition";
import type { PresentationPayloadLike } from "./types";

const publicPayload: PresentationPayloadLike = {
  playlist: {
    id: "6e2d24be-051f-49fd-861b-07f1f4f64087",
    name: "teste",
    viewportProfile: "1080p",
    transitionStyle: "fade",
    globalRefreshSec: 300,
    defaultDurationSec: 30,
  },
  presentationMeta: {
    nativeErrorAdvanceSec: 10,
    heartbeatIntervalSec: 60,
  },
  slides: [
    {
      id: "55e5c1b1-c432-42ed-b32d-47660c1f8b51",
      sortOrder: 0,
      slideType: "native",
      durationSec: 30,
      title: "Produção — OEE visão geral",
      native: {
        screenKey: "production_oee_overview",
        config: { periodDays: 30 },
        data: {
          branch: null,
          periodDays: 30,
          startDate: "2026-06-05",
          endDate: "2026-07-05",
          oeePct: null,
          targetPct: null,
          status: null,
          label: "OEE",
        },
      },
    },
    {
      id: "32676cdc-03ae-4fb3-b29e-738ad3f58fff",
      sortOrder: 1,
      slideType: "native",
      durationSec: 40,
      title: "Produção — OTD",
      native: {
        screenKey: "production_otd_summary",
        config: { periodDays: 30 },
        data: {
          branch: null,
          periodDays: 30,
          startDate: "2026-06-05",
          endDate: "2026-07-05",
          otdPct: null,
          targetPct: null,
          label: "OTD Produção",
        },
      },
    },
  ],
};

function PublicStagePreview({ payload }: { payload: PresentationPayloadLike }) {
  const { index, slides, viewport } = usePresentationEngine({
    initialPayload: payload,
    enableHiddenPause: false,
  });

  return (
    <div className="tdp-stage tdp-stage--kiosk" data-viewport={viewport}>
      {slides.map((slide, slideIndex) => {
        const active = slideIndex === index;
        const slideTransition = resolveSlideTransitionStyle(slide, payload.playlist);
        return (
          <div
            key={slide.id}
            className={`tdp-slide tdp-slide--${slideTransition}${active ? " tdp-slide--active" : ""}`}
          >
            {slide.slideType === "native" && slide.native ? (
              <NativeSlideView native={slide.native} />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

describe("NativeScreens public payload", () => {
  it("renders OEE overview with null KPI values", () => {
    render(
      <NativeSlideView
        native={{
          screenKey: "production_oee_overview",
          config: { periodDays: 30 },
          data: publicPayload.slides[0].native!.data,
        }}
      />,
    );
    expect(screen.getAllByText("OEE").length).toBeGreaterThan(0);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders OEE with series chart when seriesPoints exist", () => {
    const { container } = render(
      <NativeSlideView
        native={{
          screenKey: "production_oee_overview",
          config: { periodDays: 7 },
          data: {
            label: "OEE",
            oeePct: 75,
            targetPct: 80,
            seriesPoints: [
              { label: "01/07", value: 70 },
              { label: "02/07", value: 75 },
            ],
          },
        }}
      />,
    );
    expect(container.querySelector(".tdp-oee--with-series")).toBeTruthy();
    expect(container.querySelector(".tdp-oee__series-chart")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart")).toBeTruthy();
  });

  it("renders public stage with active slide", () => {
    render(<PublicStagePreview payload={publicPayload} />);
    expect(document.querySelector(".tdp-slide--active")).toBeTruthy();
    expect(screen.getAllByText("OEE").length).toBeGreaterThan(0);
  });

  it("comunicado stage preenche o slide (prévia/filmstrip) sem position relative inline", () => {
    const { container } = render(
      <NativeSlideView
        native={{
          screenKey: "custom_message",
          config: {},
          data: {
            version: 4,
            background: { type: "color", value: "#ffffff" },
            blocks: [
              {
                id: "chart-1",
                type: "chart_view",
                chartType: "line",
                frame: { x: 5, y: 5, w: 90, h: 80 },
                style: {},
                chartOptions: { title: "OTD — série temporal", showDataTable: true },
                resolved: {
                  label: "OTD — série temporal",
                  chart: {
                    points: [
                      { label: "11/06/26", value: 66.7 },
                      { label: "10/07/26", value: 100 },
                    ],
                  },
                },
              },
            ],
          },
        }}
      />,
    );
    const root = container.querySelector(".tdp-native-screen.tdp-comunicado");
    const stage = container.querySelector(".tdp-comunicado__stage") as HTMLElement | null;
    expect(root).toBeTruthy();
    expect(stage).toBeTruthy();
    expect(stage?.style.position).toBe("");
    expect(screen.getAllByText("OTD — série temporal").length).toBeGreaterThan(0);
    expect(container.querySelector(".delpi-ui-series-chart")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-chart__series-line")).toBeTruthy();
  });

  it("tela vazia (blocks []) usa layout rico com fundo do slide — não o legado tdp-message", () => {
    const { container } = render(
      <NativeSlideView
        native={{
          screenKey: "custom_message",
          config: {},
          data: {
            version: 4,
            background: { type: "color", value: "#ffffff" },
            blocks: [],
          },
        }}
      />,
    );
    const rich = container.querySelector(".tdp-native-screen.tdp-comunicado") as HTMLElement | null;
    expect(rich).toBeTruthy();
    expect(rich?.style.backgroundColor).toBe("rgb(255, 255, 255)");
    expect(container.querySelector(".tdp-message")).toBeNull();
  });
});
