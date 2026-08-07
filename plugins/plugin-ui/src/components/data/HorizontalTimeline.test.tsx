import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  HorizontalTimeline,
  horizontalTimelineBemClasses,
} from "./HorizontalTimeline";

const classNames = horizontalTimelineBemClasses("test");

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

  it("renderiza bandeira e tags no marco hoje/atual", () => {
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
    expect(container.querySelector(".delpi-ui-htimeline__flag")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__item--today")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-htimeline__item--current")).toBeTruthy();
  });
});
