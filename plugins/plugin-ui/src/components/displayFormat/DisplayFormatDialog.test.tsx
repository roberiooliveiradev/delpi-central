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
});
