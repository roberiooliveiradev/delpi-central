import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ScopeChipBar,
  createDashboardScopeChipBar,
  scopeChipBarBemClasses,
} from "./ScopeChipBar";

afterEach(() => {
  cleanup();
});

/**
 * Characterization of the CURRENT behavior (before additive evolution).
 * These cases must keep passing unchanged when the new optional props are absent.
 */
describe("ScopeChipBar — characterization (no new props)", () => {
  const classNames = scopeChipBarBemClasses("itp");

  it("emits dual-class names for every slot", () => {
    for (const slot of ["root", "label", "chips", "chip"] as const) {
      expect(classNames[slot]).toContain("delpi-ui-scope-chip-bar");
      expect(classNames[slot]).toContain("itp-scope-chip-bar");
    }
  });

  it("renders nothing when chips is empty", () => {
    const { container } = render(<ScopeChipBar classNames={classNames} chips={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a group with default aria-label and optional label", () => {
    const { container } = render(
      <ScopeChipBar
        classNames={classNames}
        label="Escopo atual"
        chips={[{ id: "a", label: "Alpha" }]}
      />,
    );
    const group = screen.getByRole("group");
    expect(group.getAttribute("aria-label")).toBe("Escopo");
    expect(container.querySelector(".delpi-ui-scope-chip-bar__label")?.textContent).toBe(
      "Escopo atual",
    );
  });

  it("honors custom aria-label and className", () => {
    render(
      <ScopeChipBar
        classNames={classNames}
        className="extra"
        aria-label="Meu escopo"
        chips={[{ id: "a", label: "Alpha" }]}
      />,
    );
    const group = screen.getByRole("group");
    expect(group.getAttribute("aria-label")).toBe("Meu escopo");
    expect(group.className).toContain("extra");
  });

  it("renders each chip as a toggle button with aria-pressed and active modifier", () => {
    render(
      <ScopeChipBar
        classNames={classNames}
        chips={[
          { id: "a", label: "Alpha", active: true },
          { id: "b", label: "Beta" },
        ]}
      />,
    );
    const alpha = screen.getByRole("button", { name: "Alpha" });
    const beta = screen.getByRole("button", { name: "Beta" });
    expect(alpha.getAttribute("aria-pressed")).toBe("true");
    expect(beta.getAttribute("aria-pressed")).toBe("false");
    expect(alpha.className).toContain("delpi-ui-scope-chip-bar__chip--active");
    expect(alpha.className).toContain("itp-scope-chip-bar__chip--active");
    expect(beta.className).not.toContain("--active");
    expect(alpha.getAttribute("type")).toBe("button");
  });

  it("invokes onSelect on click and renders exactly one button per chip", () => {
    const onSelect = vi.fn();
    render(
      <ScopeChipBar
        classNames={classNames}
        chips={[
          { id: "a", label: "Alpha", onSelect },
          { id: "b", label: "Beta" },
        ]}
      />,
    );
    expect(screen.getAllByRole("button")).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "Alpha" }));
    expect(onSelect).toHaveBeenCalledOnce();
  });

  it("does not render a clear-all button nor a remove control without new props", () => {
    const { container } = render(
      <ScopeChipBar classNames={classNames} chips={[{ id: "a", label: "Alpha" }]} />,
    );
    expect(screen.queryByText("Limpar tudo")).toBeNull();
    expect(container.querySelectorAll("button")).toHaveLength(1);
  });

  it("factory binds prefix classNames", () => {
    const Bar = createDashboardScopeChipBar({ prefix: "fx" });
    const { container } = render(<Bar chips={[{ id: "a", label: "Alpha" }]} />);
    expect(container.querySelector(".fx-scope-chip-bar.delpi-ui-scope-chip-bar")).toBeTruthy();
  });
});

describe("ScopeChipBar — additive evolution (remove / clear all / empty hint)", () => {
  const classNames = scopeChipBarBemClasses("itp");

  it("onRemove renders a × control with default PT-BR aria-label and fires only onRemove", () => {
    const onRemove = vi.fn();
    const onSelect = vi.fn();
    render(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: "Severidade: Alta", onRemove, onSelect }]}
      />,
    );
    const remove = screen.getByRole("button", { name: "Remover filtro Severidade: Alta" });
    expect(remove.className).toContain("delpi-ui-scope-chip-bar__chip-remove");
    fireEvent.click(remove);
    expect(onRemove).toHaveBeenCalledOnce();
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("removeAriaLabel overrides the default name", () => {
    render(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: "Alta", onRemove: () => undefined, removeAriaLabel: "Tirar Alta" }]}
      />,
    );
    expect(screen.getByRole("button", { name: "Tirar Alta" })).toBeTruthy();
  });

  it("non-text label falls back to a generic remove name", () => {
    render(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: <b>Alta</b>, onRemove: () => undefined }]}
      />,
    );
    expect(screen.getByRole("button", { name: "Remover filtro" })).toBeTruthy();
  });

  it("removable chip without onSelect renders the label as text, not a toggle button", () => {
    render(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: "Alta", onRemove: () => undefined }]}
      />,
    );
    expect(screen.queryByRole("button", { name: "Alta" })).toBeNull();
    expect(screen.getByText("Alta")).toBeTruthy();
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("removable chip with onSelect keeps its toggle button and aria-pressed", () => {
    render(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: "Alta", active: true, onSelect: () => undefined, onRemove: () => undefined }]}
      />,
    );
    expect(screen.getByRole("button", { name: "Alta" }).getAttribute("aria-pressed")).toBe("true");
  });

  it("sibling chips without onRemove stay as plain buttons next to removable ones", () => {
    const { container } = render(
      <ScopeChipBar
        classNames={classNames}
        chips={[
          { id: "a", label: "Alta", onRemove: () => undefined },
          { id: "b", label: "Baixa" },
        ]}
      />,
    );
    expect(container.querySelectorAll(".delpi-ui-scope-chip-bar__chip-group")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Baixa" }).getAttribute("aria-pressed")).toBe("false");
  });

  it("onClearAll shows 'Limpar tudo' at the end and fires; label is overridable", () => {
    const onClearAll = vi.fn();
    const { rerender, container } = render(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: "Alta" }, { id: "b", label: "Baixa" }]}
        onClearAll={onClearAll}
      />,
    );
    const buttons = container.querySelectorAll("button");
    expect(buttons[buttons.length - 1]?.textContent).toBe("Limpar tudo");
    fireEvent.click(screen.getByRole("button", { name: "Limpar tudo" }));
    expect(onClearAll).toHaveBeenCalledOnce();

    rerender(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: "Alta" }]}
        onClearAll={onClearAll}
        clearAllLabel="Remover todos"
      />,
    );
    expect(screen.getByRole("button", { name: "Remover todos" })).toBeTruthy();
  });

  it("onClearAll is not shown with zero chips", () => {
    const { container } = render(
      <ScopeChipBar classNames={classNames} chips={[]} onClearAll={() => undefined} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("emptyHint renders only when chips is empty", () => {
    const { container, rerender } = render(
      <ScopeChipBar classNames={classNames} chips={[]} emptyHint="Nenhum filtro ativo" />,
    );
    expect(container.querySelector(".delpi-ui-scope-chip-bar__empty")?.textContent).toBe(
      "Nenhum filtro ativo",
    );
    expect(screen.queryByRole("button")).toBeNull();
    rerender(
      <ScopeChipBar
        classNames={classNames}
        chips={[{ id: "a", label: "Alta" }]}
        emptyHint="Nenhum filtro ativo"
      />,
    );
    expect(screen.queryByText("Nenhum filtro ativo")).toBeNull();
  });

  it("legacy four-slot classNames objects keep working (new slots fall back to canonical)", () => {
    const legacy = {
      root: "x-root",
      label: "x-label",
      chips: "x-chips",
      chip: "x-chip",
    };
    const { container } = render(
      <ScopeChipBar
        classNames={legacy}
        chips={[{ id: "a", label: "Alta", onRemove: () => undefined }]}
        onClearAll={() => undefined}
      />,
    );
    expect(container.querySelector(".x-root")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-scope-chip-bar__chip-remove")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-scope-chip-bar__clear-all")).toBeTruthy();
  });
});
