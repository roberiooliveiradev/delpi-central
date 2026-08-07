import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  HorizontalTimeline,
  horizontalTimelineBemClasses,
  horizontalTimelinePositionPercent,
} from "./HorizontalTimeline";

const classNames = horizontalTimelineBemClasses("test");

describe("horizontalTimelinePositionPercent", () => {
  const start = Date.UTC(2026, 7, 4);
  const end = Date.UTC(2026, 7, 7);

  it("coloca o início e o fim nas bordas com padding", () => {
    expect(horizontalTimelinePositionPercent("2026-08-04", start, end, 6)).toBeCloseTo(6, 5);
    expect(horizontalTimelinePositionPercent("2026-08-07", start, end, 6)).toBeCloseTo(94, 5);
  });

  it("posiciona data intermediária proporcionalmente no eixo útil", () => {
    // 05/08 está a 1/3 do intervalo 04→07
    expect(horizontalTimelinePositionPercent("2026-08-05", start, end, 6)).toBeCloseTo(
      6 + (1 / 3) * 88,
      5,
    );
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

  it("renderiza «Agora» acima do trilho, sem marco peer today", () => {
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
    expect(screen.getByText("Atual")).toBeTruthy();
    expect(screen.getByText("Agora")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__now")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__flag")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__stem")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__pin")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__item--today")).toBeNull();
    expect(container.querySelector(".delpi-ui-htimeline__item--current")).toBeTruthy();
    expect(container.querySelectorAll(".delpi-ui-htimeline__item")).toHaveLength(1);
  });

  it("posiciona «Agora» pela data, mesmo com vários marcos no mesmo dia", () => {
    const start = Date.UTC(2026, 7, 4);
    const end = Date.UTC(2026, 7, 7);
    const expected = `${horizontalTimelinePositionPercent("2026-08-07", start, end, 6)}%`;

    const { container } = render(
      <HorizontalTimeline
        classNames={classNames}
        points={[
          {
            id: "emit",
            label: "Emissão",
            dateIso: "2026-08-04",
            dateLabel: "04/08/2026",
            tone: "neutral",
            kind: "event",
          },
          {
            id: "delivery",
            label: "Entrega do pedido",
            dateIso: "2026-08-07",
            dateLabel: "07/08/2026",
            tone: "neutral",
            kind: "event",
          },
          {
            id: "end",
            label: "Fim previsto",
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

    const now = container.querySelector(".delpi-ui-htimeline__now") as HTMLElement;
    expect(now.style.left).toBe(expected);
    // Marcos de evento ficam abaixo; «Agora» é overlay separado.
    expect(container.querySelectorAll(".delpi-ui-htimeline__item")).toHaveLength(3);
  });
});
