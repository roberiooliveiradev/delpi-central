import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GovernedConfirmation } from "./GovernedConfirmation";

afterEach(cleanup);

describe("GovernedConfirmation", () => {
  it("renders title and both actions in a named group", () => {
    render(
      <GovernedConfirmation onConfirm={() => {}} onCancel={() => {}} />,
    );
    const group = screen.getByRole("group", { name: "Confirmação necessária" });
    expect(group).toBeTruthy();
    expect(screen.getByRole("button", { name: "Confirmar" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeTruthy();
  });

  it("fires onConfirm/onCancel", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(<GovernedConfirmation onConfirm={onConfirm} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables both actions while loading (double-submit guard)", () => {
    const onConfirm = vi.fn();
    render(
      <GovernedConfirmation onConfirm={onConfirm} onCancel={() => {}} loading />,
    );
    const confirm = screen.getByRole("button", { name: "Confirmar" });
    const cancel = screen.getByRole("button", { name: "Cancelar" });
    expect(confirm.hasAttribute("disabled")).toBe(true);
    expect(cancel.hasAttribute("disabled")).toBe(true);
    fireEvent.click(confirm);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("supports description, preview, compact and className", () => {
    const { container } = render(
      <GovernedConfirmation
        title="Revisar"
        description="ctx"
        preview={<span>pv</span>}
        density="compact"
        className="mine"
        onConfirm={() => {}}
        onCancel={() => {}}
      />,
    );
    const root = container.querySelector(".delpi-ui-governed-confirmation")!;
    expect(root.classList.contains("delpi-ui-governed-confirmation--compact")).toBe(true);
    expect(root.classList.contains("mine")).toBe(true);
    expect(
      container.querySelector(".delpi-ui-governed-confirmation__description"),
    ).toBeTruthy();
    expect(
      container.querySelector(".delpi-ui-governed-confirmation__preview"),
    ).toBeTruthy();
  });

  it("omits description/preview blocks when not provided", () => {
    const { container } = render(
      <GovernedConfirmation onConfirm={() => {}} onCancel={() => {}} />,
    );
    expect(
      container.querySelector(".delpi-ui-governed-confirmation__description"),
    ).toBeNull();
    expect(
      container.querySelector(".delpi-ui-governed-confirmation__preview"),
    ).toBeNull();
  });

  it("keeps presentation-only: no digest/fingerprint/session props", () => {
    // Component API has no slots for technical fields — the DOM must
    // never leak them even if a consumer had them in scope.
    const { container } = render(
      <GovernedConfirmation onConfirm={() => {}} onCancel={() => {}} />,
    );
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/digest|fingerprint|session/i);
  });
});
