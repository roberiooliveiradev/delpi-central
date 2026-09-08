import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  clampJourneyProgressValue,
  JourneyProgressBar,
  journeyProgressBarBemClasses,
} from "./JourneyProgressBar";

describe("JourneyProgressBar", () => {
  it("clampJourneyProgressValue limita 0–100", () => {
    expect(clampJourneyProgressValue(-1)).toBe(0);
    expect(clampJourneyProgressValue(33.4)).toBe(33);
    expect(clampJourneyProgressValue(200)).toBe(100);
  });

  it("expõe progressbar de jornada com summary", () => {
    render(
      <JourneyProgressBar
        value={33}
        label="Progresso da solicitação"
        summary="2 de 6 etapas concluídas"
      />,
    );
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("33");
    expect(screen.getByText("2 de 6 etapas concluídas")).toBeTruthy();
    expect(screen.getByText("33%")).toBeTruthy();
  });

  it("aplica dual-class com prefixo", () => {
    const cn = journeyProgressBarBemClasses("mr");
    const { container } = render(
      <JourneyProgressBar value={10} classNames={cn} label="Progresso" />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("mr-journey-progress");
    expect(root.className).toContain("delpi-ui-journey-progress");
  });
});
