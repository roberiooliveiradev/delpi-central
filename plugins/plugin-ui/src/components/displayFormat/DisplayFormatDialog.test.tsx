import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { DisplayFormatDialog } from "./DisplayFormatDialog";

describe("DisplayFormatDialog", () => {
  it("preview personalizado aplica máscara e confirma spec", () => {
    const onApply = vi.fn();
    const host = document.createElement("main");
    host.className = "delpi-ui";
    document.body.appendChild(host);

    render(
      <DisplayFormatDialog
        open
        onClose={() => undefined}
        spec={{ category: "general" }}
        onApply={onApply}
        sampleValue={30}
        target="chartValue"
        portalScopeClassName="delpi-ui"
      />,
      { container: host },
    );

    fireEvent.click(screen.getByRole("option", { name: "Personalizado" }));
    const mask = screen.getByPlaceholderText('"R$" #.##0,00');
    fireEvent.change(mask, { target: { value: '"R$" #.##0,00' } });
    expect(screen.getByText(/R\$\s*30,00/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));
    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({ category: "custom", pattern: '"R$" #.##0,00' }),
    );
    host.remove();
  });

  it("clicar em categoria/tipo não fecha o modal", () => {
    const onClose = vi.fn();
    const onApply = vi.fn();
    const host = document.createElement("main");
    host.className = "delpi-ui dashboard-tv-dashboard";
    document.body.appendChild(host);

    render(
      <DisplayFormatDialog
        open
        onClose={onClose}
        spec={{ category: "general", presetId: "general" }}
        onApply={onApply}
        sampleValue={0.2}
        target="tableColumn"
        targetHint='Coluna "Qtd"'
        portalScopeClassName="delpi-ui"
      />,
      { container: host },
    );

    expect(screen.getByText(/Formatando: Coluna/)).toBeTruthy();
    fireEvent.pointerDown(screen.getByRole("option", { name: "Número" }));
    fireEvent.click(screen.getByRole("option", { name: "Número" }));
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog")).toBeTruthy();

    const typeOptions = screen.getAllByRole("option", { name: /0,00|Compacto|^0$/ });
    const numberType = typeOptions.find((el) => el.textContent?.includes("0,00")) ?? typeOptions[0];
    fireEvent.pointerDown(numberType);
    fireEvent.click(numberType);
    expect(onClose).not.toHaveBeenCalled();
    expect(onApply).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog")).toBeTruthy();

    host.remove();
  });
});
