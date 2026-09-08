import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ProgressTracker,
  progressTrackerBemClasses,
  type ProgressTrackerStep,
} from "./ProgressTracker";

const cn = progressTrackerBemClasses("demo");

const STEPS: ProgressTrackerStep[] = [
  { id: "a", label: "Destinatário", state: "complete" },
  { id: "b", label: "Tipo de NF", state: "current" },
  { id: "c", label: "Itens", state: "locked" },
];

afterEach(() => {
  cleanup();
});

describe("ProgressTracker", () => {
  it("marca etapa atual com aria-current=step", () => {
    const { container } = render(
      <ProgressTracker
        classNames={cn}
        steps={STEPS}
        currentStepId="b"
        interactive
        ariaLabel="Etapas do wizard"
      />,
    );
    const current = container.querySelector(
      ".delpi-ui-progress-tracker__item--current button",
    ) as HTMLButtonElement;
    expect(current.getAttribute("aria-current")).toBe("step");
  });

  it("não dispara onStepChange para etapa locked", () => {
    const onStepChange = vi.fn();
    const { container } = render(
      <ProgressTracker
        classNames={cn}
        steps={STEPS}
        currentStepId="b"
        interactive
        onStepChange={onStepChange}
      />,
    );
    const locked = container.querySelector(
      ".delpi-ui-progress-tracker__item--locked button",
    ) as HTMLButtonElement;
    fireEvent.click(locked);
    expect(onStepChange).not.toHaveBeenCalled();
  });

  it("permite clique em etapa complete", () => {
    const onStepChange = vi.fn();
    const { container } = render(
      <ProgressTracker
        classNames={cn}
        steps={STEPS}
        currentStepId="b"
        interactive
        onStepChange={onStepChange}
      />,
    );
    const complete = container.querySelector(
      ".delpi-ui-progress-tracker__item--complete button",
    ) as HTMLButtonElement;
    fireEvent.click(complete);
    expect(onStepChange).toHaveBeenCalledWith("a");
  });

  it("modo compact abre lista de etapas", () => {
    render(
      <ProgressTracker
        classNames={cn}
        steps={STEPS}
        currentStepId="b"
        density="compact"
        interactive
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Ver etapas" }));
    expect(screen.getByText(/bloqueada/i)).toBeTruthy();
  });
});
