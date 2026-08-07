import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  HorizontalTimeline,
  horizontalTimelineBemClasses,
  horizontalTimelinePositionPercent,
  layoutHorizontalTimeline,
} from "./HorizontalTimeline";

const classNames = horizontalTimelineBemClasses("test");

describe("horizontalTimelinePositionPercent", () => {
  const start = Date.UTC(2026, 7, 4);
  const end = Date.UTC(2026, 7, 7);

  it("coloca o início e o fim nas bordas com padding", () => {
    expect(horizontalTimelinePositionPercent("2026-08-04", start, end, 8)).toBeCloseTo(8, 5);
    expect(horizontalTimelinePositionPercent("2026-08-07", start, end, 8)).toBeCloseTo(92, 5);
  });
});

describe("layoutHorizontalTimeline", () => {
  it("agrupa eventos do mesmo dia e espaça os grupos", () => {
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
    expect(layout.clusters[0].leftPercent).toBe(8);
    expect(layout.clusters[1].leftPercent).toBe(50);
    expect(layout.clusters[2].leftPercent).toBe(92);
    expect(layout.clusters[2].entries.map((e) => e.label)).toEqual([
      "Entrega do pedido",
      "Fim previsto da OP",
    ]);
    expect(layout.clusters[2].isCurrent).toBe(true);
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

  it("renderiza «Agora» acima e um item por dia (sem peer today)", () => {
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
            isCurrent: true,
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
    expect(screen.getByText("Entrega do pedido")).toBeTruthy();
    expect(screen.getByText("Fim previsto da OP")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__now")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__item--today")).toBeNull();
    expect(container.querySelectorAll(".delpi-ui-htimeline__item")).toHaveLength(2);
    expect(container.querySelector(".delpi-ui-htimeline__item--stacked")).toBeTruthy();
  });
});
