import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { EditableTableCell, editableTableCellBemClasses } from "./EditableTableCell";
import { NativeSelectControl } from "./NativeSelectControl";

describe("EditableTableCell", () => {
  it("emite BEM e dispara onChange no input", () => {
    const onChange = vi.fn();
    const { container } = render(
      <EditableTableCell
        classNames={editableTableCellBemClasses("dm")}
        value="abc"
        onChange={onChange}
        aria-label="Descrição"
        badge={<span data-testid="badge">dirty</span>}
      />,
    );

    expect(container.querySelector(".dm-editable-cell")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "xyz" } });
    expect(onChange).toHaveBeenCalledWith("xyz");
    expect(screen.getByTestId("badge")).toBeTruthy();
  });

  it("renderiza select com opções", () => {
    const onChange = vi.fn();
    render(
      <EditableTableCell
        as="select"
        classNames={editableTableCellBemClasses("dm")}
        value="a"
        onChange={onChange}
        options={[
          { value: "a", label: "A" },
          { value: "b", label: "B" },
        ]}
        aria-label="Operador"
      />,
    );

    fireEvent.change(screen.getByLabelText("Operador"), { target: { value: "b" } });
    expect(onChange).toHaveBeenCalledWith("b");
  });
});

describe("NativeSelectControl", () => {
  it("select compacto sem label", () => {
    const onChange = vi.fn();
    render(
      <NativeSelectControl
        className="pac-field__control"
        value=""
        onChange={onChange}
        options={[{ value: "u1", label: "Ana" }]}
        placeholderOption="Selecione…"
        aria-label="Membro"
      />,
    );

    const select = screen.getByLabelText("Membro");
    expect(select).toHaveProperty("className", "pac-field__control");
    fireEvent.change(select, { target: { value: "u1" } });
    expect(onChange).toHaveBeenCalledWith("u1");
  });
});
