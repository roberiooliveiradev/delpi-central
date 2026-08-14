import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CopyableValue } from "./CopyableValue";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("CopyableValue", () => {
  it("copia com botão de ícone, sem o texto Copiar", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    render(
      <CopyableValue value="000256" label="Código">
        000256
      </CopyableValue>,
    );

    expect(screen.queryByText("Copiar")).toBeNull();
    const button = screen.getByRole("button", { name: "Copiar Código" });
    fireEvent.click(button);
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("000256"));
    expect(screen.getByRole("button", { name: "Copiado: Código" })).toBeTruthy();
  });
});
