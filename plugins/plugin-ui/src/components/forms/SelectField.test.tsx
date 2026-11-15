import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  SelectControl,
  selectControlBemClasses,
} from "./SelectField";

const LABELS = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (label?: string) => (label ? `Buscar ${label}` : "Buscar opções"),
};

afterEach(() => {
  cleanup();
});

describe("SelectControl", () => {
  it("emite prefix + delpi-ui-select nas classNames", () => {
    const cn = selectControlBemClasses("ds");
    expect(cn.root).toBe("ds-select delpi-ui-select");
    expect(cn.trigger).toContain("delpi-ui-select__trigger");
    expect(cn.panel).toContain("delpi-ui-select__panel");
  });

  it("não duplica quando o prefixo já é delpi-ui", () => {
    const cn = selectControlBemClasses("delpi-ui");
    expect(cn.root).toBe("delpi-ui-select");
    expect(cn.trigger).toBe("delpi-ui-select__trigger");
  });

  it("renderiza trigger com placeholder", () => {
    render(
      <SelectControl
        options={[{ value: "a", label: "Opção A" }]}
        value=""
        onChange={vi.fn()}
        placeholder="Selecione…"
        ariaLabel="Status"
        classNames={selectControlBemClasses("ds")}
        labels={LABELS}
      />,
    );

    expect(screen.getByRole("button", { name: "Status" })).toBeTruthy();
    expect(screen.getByText("Selecione…")).toBeTruthy();
  });

  const OPTIONS = [
    { value: "a", label: "Opção A" },
    { value: "b", label: "Opção B" },
    { value: "c", label: "Opção C" },
  ];

  function renderControl(onChange = vi.fn()) {
    render(
      <SelectControl
        options={OPTIONS}
        value=""
        onChange={onChange}
        ariaLabel="Status"
        classNames={selectControlBemClasses("ds")}
        labels={LABELS}
      />,
    );
    return screen.getByRole("button", { name: "Status" });
  }

  it("ArrowDown no trigger abre o painel e foca a primeira opção", () => {
    const trigger = renderControl();
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    const listbox = screen.getByRole("listbox");
    const first = within(listbox).getByRole("button", { name: "Opção A" });
    expect(document.activeElement).toBe(first);
  });

  it("ArrowUp no trigger abre o painel e foca a última opção", () => {
    const trigger = renderControl();
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowUp" });
    const listbox = screen.getByRole("listbox");
    const last = within(listbox).getByRole("button", { name: "Opção C" });
    expect(document.activeElement).toBe(last);
  });

  it("setas/Home/End navegam entre as opções do painel", () => {
    const trigger = renderControl();
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    const listbox = screen.getByRole("listbox");
    const optionA = within(listbox).getByRole("button", { name: "Opção A" });
    const optionB = within(listbox).getByRole("button", { name: "Opção B" });
    const optionC = within(listbox).getByRole("button", { name: "Opção C" });

    fireEvent.keyDown(optionA, { key: "ArrowDown" });
    expect(document.activeElement).toBe(optionB);
    fireEvent.keyDown(optionB, { key: "End" });
    expect(document.activeElement).toBe(optionC);
    fireEvent.keyDown(optionC, { key: "Home" });
    expect(document.activeElement).toBe(optionA);
    fireEvent.keyDown(optionA, { key: "ArrowUp" });
    expect(document.activeElement).toBe(optionA);
  });

  it("clique na opção emite onChange, fecha e devolve foco ao trigger", () => {
    const onChange = vi.fn();
    const trigger = renderControl(onChange);
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    const listbox = screen.getByRole("listbox");
    fireEvent.click(within(listbox).getByRole("button", { name: "Opção B" }));
    expect(onChange).toHaveBeenCalledWith("b");
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("Escape na opção fecha o painel e devolve foco ao trigger", () => {
    const trigger = renderControl();
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    const listbox = screen.getByRole("listbox");
    const optionB = within(listbox).getByRole("button", { name: "Opção B" });
    fireEvent.keyDown(optionB, { key: "Escape" });
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("Tab na opção fecha o painel e devolve foco ao trigger", () => {
    const trigger = renderControl();
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    const listbox = screen.getByRole("listbox");
    const optionA = within(listbox).getByRole("button", { name: "Opção A" });
    fireEvent.keyDown(optionA, { key: "Tab" });
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });
});
