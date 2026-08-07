import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  formatClusterCaptionText,
  HorizontalTimeline,
  horizontalTimelineBemClasses,
  horizontalTimelinePositionPercent,
  layoutHorizontalTimeline,
  normalizeTimelineDayKey,
} from "./HorizontalTimeline";

const classNames = horizontalTimelineBemClasses("test");

describe("normalizeTimelineDayKey", () => {
  it("unifica ISO, Protheus e BR", () => {
    expect(normalizeTimelineDayKey("2026-09-08")).toBe("2026-09-08");
    expect(normalizeTimelineDayKey("20260908")).toBe("2026-09-08");
    expect(normalizeTimelineDayKey("08/09/2026")).toBe("2026-09-08");
  });
});

describe("formatClusterCaptionText", () => {
  it("funde início e fim previstos numa legenda", () => {
    expect(
      formatClusterCaptionText([
        { label: "Início previsto" },
        { label: "Fim previsto da OP" },
      ]),
    ).toBe("Início e fim previstos");
  });

  it("empilha demais legendas com quebra de linha", () => {
    expect(
      formatClusterCaptionText([
        { label: "Entrega do pedido" },
        { label: "Fim previsto da OP" },
      ]),
    ).toBe("Entrega do pedido\nFim previsto da OP");
  });
});

describe("horizontalTimelinePositionPercent", () => {
  const start = Date.UTC(2026, 7, 4);
  const end = Date.UTC(2026, 7, 7);

  it("coloca o início e o fim nas bordas com padding", () => {
    expect(horizontalTimelinePositionPercent("2026-08-04", start, end, 8)).toBeCloseTo(8, 5);
    expect(horizontalTimelinePositionPercent("2026-08-07", start, end, 8)).toBeCloseTo(92, 5);
  });
});

describe("layoutHorizontalTimeline", () => {
  it("agrupa mesmo dia mesmo com formatos mistos e funde início/fim", () => {
    const layout = layoutHorizontalTimeline([
      {
        id: "a",
        label: "Emissão",
        dateIso: "2026-08-04",
        dateLabel: "04/08/2026",
        tone: "neutral",
        kind: "event",
      },
      {
        id: "b",
        label: "Início previsto",
        dateIso: "20260908",
        dateLabel: "08/09/2026",
        tone: "info",
        kind: "event",
      },
      {
        id: "c",
        label: "Fim previsto da OP",
        dateIso: "08/09/2026",
        dateLabel: "08/09/2026",
        tone: "danger",
        kind: "event",
        isCurrent: true,
      },
    ]);

    expect(layout.clusters).toHaveLength(2);
    expect(layout.clusters[1].captionText).toBe("Início e fim previstos");
    expect(layout.clusters[1].entries).toHaveLength(2);
  });

  it("agrupa entrega + fim e espaça os grupos", () => {
    const layout = layoutHorizontalTimeline([
      {
        id: "a",
        label: "Emissão",
        dateIso: "2026-08-04",
        dateLabel: "04/08/2026",
        tone: "neutral",
        kind: "event",
      },
      {
        id: "b",
        label: "Início",
        dateIso: "2026-08-06",
        dateLabel: "06/08/2026",
        tone: "info",
        kind: "event",
      },
      {
        id: "c",
        label: "Entrega do pedido",
        dateIso: "2026-08-07",
        dateLabel: "07/08/2026",
        tone: "neutral",
        kind: "event",
      },
      {
        id: "d",
        label: "Fim previsto da OP",
        dateIso: "2026-08-07",
        dateLabel: "07/08/2026",
        tone: "success",
        kind: "event",
        isCurrent: true,
      },
      {
        id: "today",
        label: "Hoje",
        dateIso: "2026-08-07",
        dateLabel: "07/08/2026",
        tone: "info",
        kind: "today",
      },
    ]);

    expect(layout.clusters).toHaveLength(3);
    expect(layout.clusters[2].captionText).toBe(
      "Entrega do pedido\nFim previsto da OP",
    );
    expect(layout.today?.leftPercent).toBe(92);
  });
});

describe("HorizontalTimeline", () => {
  it("mostra emptyMessage quando não há pontos", () => {
    render(
      <HorizontalTimeline
        classNames={classNames}
        points={[]}
        labels={{ emptyMessage: "Sem marcos." }}
      />,
    );
    expect(screen.getByText("Sem marcos.")).toBeTruthy();
  });

  it("renderiza legenda multilinha num único nó (sem spans empilhados)", () => {
    const { container } = render(
      <HorizontalTimeline
        classNames={classNames}
        points={[
          {
            id: "a",
            label: "Emissão",
            dateIso: "2026-08-01",
            dateLabel: "01/08/2026",
            tone: "neutral",
            kind: "event",
          },
          {
            id: "b",
            label: "Entrega do pedido",
            dateIso: "2026-08-07",
            dateLabel: "07/08/2026",
            tone: "neutral",
            kind: "event",
          },
          {
            id: "c",
            label: "Fim previsto da OP",
            dateIso: "2026-08-07",
            dateLabel: "07/08/2026",
            tone: "success",
            kind: "event",
            isCurrent: true,
          },
          {
            id: "today",
            label: "Hoje",
            dateIso: "2026-08-07",
            dateLabel: "07/08/2026",
            tone: "info",
            kind: "today",
          },
        ]}
      />,
    );
    expect(screen.getByText("Agora")).toBeTruthy();
    const labels = container.querySelectorAll(".delpi-ui-htimeline__label");
    const stacked = Array.from(labels).find((el) =>
      (el.textContent || "").includes("Entrega do pedido"),
    );
    expect(stacked?.textContent).toContain("Entrega do pedido");
    expect(stacked?.textContent).toContain("Fim previsto da OP");
    expect(container.querySelectorAll(".delpi-ui-htimeline__item")).toHaveLength(2);
    expect(container.querySelector(".delpi-ui-htimeline__now--coincident")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__pin")).toBeNull();
  });
});
