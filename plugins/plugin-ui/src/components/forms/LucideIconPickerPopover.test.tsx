import { fireEvent, render, screen } from "@testing-library/react";
import { useRef, useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { LucideIconPickerPopover } from "./LucideIconPickerPopover";

function Harness({
  onChange = vi.fn(),
}: {
  onChange?: (name: string | null) => void;
}) {
  const anchorRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(true);

  return (
    <>
      <button type="button" ref={anchorRef}>
        Abrir
      </button>
      <LucideIconPickerPopover
        open={open}
        onOpenChange={setOpen}
        anchorRef={anchorRef}
        value="Factory"
        nameFormat="pascal"
        curatedOnly={false}
        title="Ícones"
        onChange={onChange}
      />
    </>
  );
}

describe("LucideIconPickerPopover", () => {
  it("abre o catálogo completo com busca no portal", () => {
    render(<Harness />);

    expect(screen.getByRole("dialog", { name: "Ícones" })).toBeTruthy();
    expect(screen.getByPlaceholderText(/buscar/i)).toBeTruthy();
    expect(screen.getByText(/ícones Lucide/i)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Fechar" })).toBeNull();
  });

  it("seleciona ícone e fecha", () => {
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Fábrica" }));

    expect(onChange).toHaveBeenCalledWith("Factory");
    expect(screen.queryByRole("dialog", { name: "Ícones" })).toBeNull();
  });
});
